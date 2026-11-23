class BaseCMDFloppyPlugin(BaseVFSHandler):
	"""Shared Base Engine providing low-level structural partition parsing,
	512-byte geometry scaling, and polymorphic routing for D2M and D4M floppy formats.
	"""
	def mount(self):
		self.default_dir_track = 1
		self.default_dir_sector = 1
		self.max_tracks_limit = 255
		self.is_dirty = False
		self.current_path = "ROOT"
		
		self.partitions_registry = {}
		self.file_list = []
		
		total_bytes = len(self.payload)
		raw_bytes = bytes(self.payload)
		
		# Compute total floppy hardware block ceiling based on 512-byte blocks
		total_hardware_blocks = total_bytes // 512
		
		# FIXED: PREPEND HOST OS BACK-OUT BREADCRUMB TO D2M AND D4M IMAGES!
		# This inserts a single safe ".." row to exit the floppy container entirely and go back to PC files!
		self.file_list.append({
			"name": "..",
			"type": "UP-DIR",
			"type_display": "UP-DIR",
			"subtype": "UP-DIR",
			"size": 0,
			"size_display": "0",
			"track": 0,
			"sector": 99,  # Flag 99 maps specifically to host-unmount triggers in your execute loop
			"is_dir": True,
			"is_directory": True,
			"is_virtual_container": False,
			"raw_meta": None,
			"vfs_meta": None
		})

		# --- PHASE 1: TARGET ACCURATE GEOMETRY ADDRESSES ---
		if self.format_type == "D2M":
			self.sys_part_offset = 0x190800	  # Track 26, Sector 8 (FD2000 Base)
			dev_block_ptr = 0x190500		  # Track 26, Sector 5 DevBlock
		else:
			self.sys_part_offset = 0x320800	  # Track 51, Sector 8 (FD4000 Base)
			dev_block_ptr = 0x320500		  # Track 51, Sector 5 DevBlock

		if self.sys_part_offset >= total_bytes:
			self.disk_label_msg = '0 "truncated image?"'
			return False

		# Extract the Device Identification settings safely
		if dev_block_ptr + 256 <= total_bytes:
			dev_address_flag = raw_bytes[dev_block_ptr + 0xE1]
			self.disk_label_msg = f'12 "cmd {self.format_type.lower()} dev {dev_address_flag}"'
		else:
			self.disk_label_msg = f'12 "cmd {self.format_type.lower()} system"'

		# --- PHASE 3: SWEEP THE 32 CONTIGUOUS MASTER PARTITION SECTORS ---
		p_count = 0 
		total_allocated_blocks = 0	
		
		TYPE_LABELS = {
			0x01: "NAT", 0x02: "41", 0x03: "71", 0x04: "81",
			0x05: "C81", 0x06: "PRN", 0x07: "FOR", 0xFF: "SYS"
		}
		
		# Iterate across the 4 partition table sectors sequentially (Sectors 8 to 11)
		for sec_step in range(4):
			current_sec_offset = self.sys_part_offset + (sec_step * 256)
			if current_sec_offset + 256 > total_bytes:
				break
				
			sec_bytes = raw_bytes[current_sec_offset : current_sec_offset + 256]
			
			for slot_idx in range(8):
				off = slot_idx * 32
				p_type = sec_bytes[off + 2]
				
				if sec_step == 0 and slot_idx == 0:
					p_type = 0xFF
					p_name = "SYSTEM"
					start_lba = self.sys_part_offset // 512
					total_blocks = 12  
				else:
					if p_type == 0x00 and all(b == 0 for b in sec_bytes[off+5:off+21]):
						continue 
						
					p_name_raw = sec_bytes[off + 5 : off + 21]
					p_name_chars = []
					for b in p_name_raw:
						if b == 0x00 or b == 0xA0:
							p_name_chars.append(' ')
						elif 32 <= b <= 126:
							p_name_chars.append(chr(b))
					p_name = "".join(p_name_chars).strip()
					if not p_name:
						p_name = f"PARTITION {p_count:02d}"
					
					# FIXED: Extract 24-bit Big-Endian Start LBA Block from offsets 21, 22, 23
					start_lba = (sec_bytes[off + 21] << 16) | (sec_bytes[off + 22] << 8) | sec_bytes[off + 23]
					
					# FIXED: Extract 24-bit Big-Endian Total Size Blocks Count from offsets 29, 30, 31
					total_blocks = (sec_bytes[off + 29] << 16) | (sec_bytes[off + 30] << 8) | sec_bytes[off + 31]
				
				type_str = TYPE_LABELS.get(p_type, "FOR")
				if p_type != 0x00:
					total_allocated_blocks += total_blocks
				
				# Scale parameters precisely to 512-byte hardware blocks to match verified signatures
				part_node = {
					"index": p_count,
					"name": p_name,
					"type_flag": p_type,
					"type_string": type_str,
					"start_lba": start_lba,
					"blocks_count": total_blocks,
					"byte_start": start_lba * 512,		# Points precisely to embedded VFS signature boundaries!
					"byte_length": total_blocks * 512	 # Extracts accurate standalone image sizes!
				}
				
				self.partitions_registry[p_count] = part_node
				
				self.file_list.append({
					"name": p_name,
					"type": type_str,					
					"type_display": type_str,
					"subtype": type_str,
					"size": total_blocks,
					"size_display": str(total_blocks),
					"track": start_lba,
					"sector": p_count,
					"is_dir": False,
					"is_directory": False,
					"is_virtual_container": True,		
					"raw_meta": part_node,
					"vfs_meta": part_node
				})
				p_count += 1
				
		return True

	def navigate_forward(self, track, sector, name):
		"""Polymorphically builds and boots inner child driver filesystems in-memory."""
		part_id = int(sector)
		part_info = self.partitions_registry.get(part_id)
		if not part_info:
			return None
			
		t_str = part_info["type_string"]
		t_flag = part_info["type_flag"]
		
		if t_str in ["SYS", "PRN", "FOR"] or t_flag in [0x00, 0x06, 0x07, 0xFF]:
			return f"LOCKOUT: Partition '{name}' [{t_str}] is an unmountable format structure."
			
		b_start = part_info["byte_start"]
		b_len = part_info["byte_length"]
		total_payload_bytes = len(self.payload)
		
		# Clamp and force-align raw footprints to guard standalone plugins against geometry initialization rejects
		target_size = b_len
		if t_str == "41":	target_size = 174848
		elif t_str == "71": target_size = 349696
		elif t_str == "81": target_size = 819200

		if b_start >= total_payload_bytes:
			sub_payload = bytearray(target_size)
		else:
			end_pos = min(b_start + target_size, total_payload_bytes)
			sub_payload = bytearray(self.payload[b_start : end_pos])
			if len(sub_payload) < target_size:
				sub_payload.extend(b"\x00" * (target_size - len(sub_payload)))

		nested_handler = None
		if t_str == "41":	nested_handler = D64FileSystemPlugin(bytes(sub_payload))
		elif t_str == "71": nested_handler = D71FileSystemPlugin(bytes(sub_payload))
		elif t_str == "81" or t_str == "C81": nested_handler = D81FileSystemPlugin(bytes(sub_payload))
		elif t_str == "NAT": nested_handler = DNPFileSystemPlugin(bytes(sub_payload))

		if nested_handler:
			# FIXED: Ensure format types and geometry metadata parameters are assigned explicitly 
			# so that the main Sector Editor views map standard CBM track rules instead of floppy parameters!
			if t_str in ["81", "C81"]:
				nested_handler.format_type = "D81"
				nested_handler.total_tracks = 80
				nested_handler.max_tracks_limit = 80
				nested_handler.default_dir_track = 40
				nested_handler.default_dir_sector = 0
			elif t_str == "71":
				nested_handler.format_type = "D71"
				nested_handler.total_tracks = 70
				nested_handler.max_tracks_limit = 70
				nested_handler.default_dir_track = 18
				nested_handler.default_dir_sector = 1
			elif t_str == "41":
				nested_handler.format_type = "D64"
				nested_handler.total_tracks = 35
				nested_handler.max_tracks_limit = 35
				nested_handler.default_dir_track = 18
				nested_handler.default_dir_sector = 0
			elif t_str == "NAT":
				nested_handler.format_type = "DNP"
				nested_handler.default_dir_track = 1
				nested_handler.default_dir_sector = 1

			success = nested_handler.mount()

			if success or success is None:
				nested_handler.parent_dhd_handler = self  # Re-use parent link keys for unified saving routing
				nested_handler.parent_partition_id = part_id
				nested_handler.archive_name = getattr(self, "archive_name", "")
				
				# FIXED: Check if a ".." entry already exists in the list to prevent duplicate rows!
				if hasattr(nested_handler, "file_list") and nested_handler.file_list:
					has_up_dir = any(item.get("name") == ".." for item in nested_handler.file_list)
					if not has_up_dir:
						nested_handler.file_list.insert(0, {
							"name": "..",
							"type": "UP-DIR",
							"type_display": "UP-DIR",
							"subtype": "UP-DIR",
							"size": 0,
							"size_display": "0",
							"track": 0,
							"sector": 0,
							"is_dir": True,
							"is_directory": True,
							"is_virtual_container": False
						})
						
				return nested_handler
		return "CRITICAL: Sub-VFS engine compilation error inside floppy partition frame."

	def write_virtual_sector(self, track, sector, data_bytes):
		"""Flat-File Sector Writer for the CMD floppy master system tracks.
		Allows direct hex modifications to be written cleanly into the master container payload.
		"""
		t = int(track)
		s = int(sector)
		
		# Compute flat linear index: 256 sectors per track mapping rules
		idx = ((t - 1) * 256) + s
		offset = idx * 256
		
		if offset + 256 > len(self.payload):
			return False
			
		clean_data = bytes(data_bytes[:256].ljust(256, b"\x00"))
		
		if isinstance(self.payload, bytes):
			self.payload = bytearray(self.payload)
			
		self.payload[offset : offset + 256] = clean_data
		self.is_dirty = True
		
		# Immediately serialize the updated platter memory buffer back down to your PC
		return self.flush_dhd_to_disk()

	def flush_dhd_to_disk(self):
		"""Polymorphic File Serialization Engine for CMD Floppy Containers.
		Acts as a mirror alias for 'flush_dhd_to_disk' so that all nested sub-partitions 
		can effortlessly write back to .d2m and .d4m files with zero code modifications!
		"""
		if hasattr(self, "archive_name") and self.archive_name:
			try:
				with open(os.path.abspath(self.archive_name), "wb") as f_out:
					f_out.write(bytes(self.payload))
				self.is_dirty = False
				return True
			except Exception:
				return False
		return False

	def read_virtual_sector(self, track, sector):
		idx = ((int(track) - 1) * 256) + int(sector)
		offset = idx * 256
		if offset + 256 <= len(self.payload):
			return bytes(self.payload[offset : offset + 256])
		return b"\x00" * 256


