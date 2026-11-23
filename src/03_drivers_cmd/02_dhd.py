class DHDFileSystemPlugin(BaseVFSHandler):
	"""Dynamic Broker Adapter bridging low-level CMD SCSI Hard Drive container architectures.
	Decodes the 32 master directory track blocks, parses 32-byte partition slot vectors, 
	and dynamically routes targeted sector offsets straight to sub-emulation handlers.
	"""
	def mount(self):
		self.format_type = "DHD"
		self.default_dir_track = 1
		self.default_dir_sector = 1
		self.max_tracks_limit = 255
		self.is_dirty = False
		self.current_path = "ROOT"
		
		# Core operational maps for the master controller framework
		self.partitions_registry = {} 
		self.file_list = []
		
		total_bytes = len(self.payload)
		raw_bytes = bytes(self.payload)
		
		# Compute total hardware block ceiling based on 512-byte sectors
		total_hardware_blocks = total_bytes // 512
		
		# PREPEND HOST OS BACK-OUT BREADCRUMB: Allows the user to unmount the DHD entirely and go back to PC files!
		self.file_list.append({
			"name": "..",
			"type": "UP-DIR",
			"type_display": "UP-DIR",
			"subtype": "UP-DIR",
			"size": 0,
			"size_display": "0",
			"track": 0,
			"sector": 99,  # Flag 99 maps specifically to host-unmount triggers
			"is_dir": True,
			"is_directory": True,
			"is_virtual_container": False,
			"raw_meta": None,
			"vfs_meta": None
		})

		# --- PHASE 1: BULLETPROOF RAW HEX SEQUENCE LOOKAHEAD SWEEP ---
		config_found = False
		config_base_offset = 0
		active_config_block = None
		
		for offset_step in range(0, min(total_bytes - 512, 256 * 1024)):
			if (raw_bytes[offset_step] == 0x43 and		 # 'C'
				raw_bytes[offset_step + 1] == 0x4D and	 # 'M'
				raw_bytes[offset_step + 2] == 0x44 and	 # 'D'
				raw_bytes[offset_step + 3] == 0x20 and	 # ' '
				raw_bytes[offset_step + 4] == 0x48 and	 # 'H'
				raw_bytes[offset_step + 5] == 0x44):	 # 'D'
				
				if (raw_bytes[offset_step + 8] == 0x8D and
					raw_bytes[offset_step + 9] == 0x03 and
					raw_bytes[offset_step + 10] == 0x88 and
					raw_bytes[offset_step + 11] == 0x8E and
					raw_bytes[offset_step + 12] == 0x02 and
					raw_bytes[offset_step + 13] == 0x88 and
					raw_bytes[offset_step + 14] == 0xEA and
					raw_bytes[offset_step + 15] == 0x60):
					
					config_base_offset = offset_step - 0x1F0
					if config_base_offset >= 0 and config_base_offset + 512 <= total_bytes:
						active_config_block = raw_bytes[config_base_offset : config_base_offset + 512]
						config_found = True
						break
						
		if not config_found or active_config_block is None:
			self.disk_label_msg = '0 "sterile container?"'
			return False

		# --- PHASE 2: EXTRACT TRUE HARDWARE SIZE LIMITS FROM THE MASTER PARAMETERS ---
		part_table_lba_offset = struct.unpack(">H", active_config_block[0x1E6 : 0x1E8])[0]
		dev_address_flag = active_config_block[0x1E1]
		
		# Pull the raw 24-bit split address registers from Zone 2 (For Master Slot d=0) [1.13]
		max_platter_msb = active_config_block[0x138]
		max_platter_mid = active_config_block[0x170]
		max_platter_lsb = active_config_block[0x1A8]
		
		# Stitch the bytes together into a clean 24-bit logical block capacity integer
		parsed_device_blocks = (max_platter_msb << 16) | (max_platter_mid << 8) | max_platter_lsb
		
		# --- GLOBAL CONFIGURATION RESOLUTION ENGINE ---
		# Check your global settings payload structures for the custom override configuration toggles
		global_settings = app_state.get("settings", {}) if 'app_state' in locals() else {}
		is_override_enabled = global_settings.get("override_cmd_hd_max_size", False)
		custom_override_blocks = global_settings.get("custom_cmd_hd_blocks_value", 16777216)
		
		if is_override_enabled:
			# CRITICAL PATH OVERRIDE: User setting takes supreme authority over all disk metadata rules!
			total_hardware_blocks = int(custom_override_blocks)
		else:
			# Check if the hardware device table has an explicitly mapped platter configuration [1.13]
			if parsed_device_blocks == 0 or parsed_device_blocks == 0xFFFFFF:
				# THE EMPTY DEFAULT: Hard drive map is sterile, enforce the absolute 8 GB maximum filesystem architecture ceiling! [1.13]
				# 8 GB = 8,589,934,592 Bytes / 512 Bytes Per SCSI Block = Exactly 16,777,216 Blocks [1.13]
				total_hardware_blocks = 16777216
			else:
				# THE SAFE HARDWARE ENFORCEMENT: Honor the exact raw physical LBA sector boundaries from your real drive dump! [1.13]
				total_hardware_blocks = parsed_device_blocks

		self.disk_label_msg = f'12 "cmd hd dev {dev_address_flag}"'
		
		# --- PHASE 3: SWEEP THE 32 CONTIGUOUS MASTER PARTITION SECTORS ---
		p_count = 0 
		total_allocated_blocks = 0	
		
		TYPE_LABELS = {
			0x01: "NAT", 0x02: "41", 0x03: "71", 0x04: "81",
			0x05: "C81", 0x06: "PRN", 0x07: "FOR", 0xFF: "SYS"
		}
		
		for sec_step in range(32):
			current_sector_offset = part_table_lba_offset + sec_step
			lba_offset = (config_base_offset - 0x400) + (current_sector_offset * 256)
			
			if lba_offset + 256 > total_bytes:
				break
				
			sec_bytes = raw_bytes[lba_offset : lba_offset + 256]
			
			for slot_idx in range(8):
				off = slot_idx * 32
				p_type = sec_bytes[off + 2]
				
				if sec_step == 0 and slot_idx == 0:
					p_type = 0xFF
					p_name = "SYSTEM"
					start_lba = (config_base_offset - 0x400) // 512
					total_blocks = 0x90		 
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
					
					start_lba = (sec_bytes[off+0x15] << 16) | (sec_bytes[off+0x16] << 8) | sec_bytes[off+0x17]
					total_blocks = (sec_bytes[off+0x1E] << 8) | sec_bytes[off+0x1F]
				
				type_str = TYPE_LABELS.get(p_type, "FOR")
				
				# --- FIXED FORMAT-AWARE CAPACITY ACCUMULATION ---
				# Standardize how partition blocks accumulate based on hardware format rules
				if p_type != 0x00:
					if p_type == 0x01: # Native Partition (NAT)
						# If a native partition size field exceeds the theoretical boundaries of 
						# the file size, it indicates the layout is tracking raw 256-byte sectors!
						if total_blocks > total_hardware_blocks:
							# Scale it down to match our file's 512-byte block metrics accurately
							total_allocated_blocks += (total_blocks // 2)
						else:
							total_allocated_blocks += total_blocks
					else:
						# Emulated structures (41, 71, 81) are strictly counted in 512-byte blocks
						total_allocated_blocks += total_blocks
				
				part_node = {
					"index": p_count, "name": p_name, "type_flag": p_type, "type_string": type_str,
					"start_lba": start_lba, "blocks_count": total_blocks,
					"byte_start": start_lba * 512, "byte_length": total_blocks * 512
				}
				
				self.partitions_registry[p_count] = part_node
				
				self.file_list.append({
					"name": p_name, "type": type_str, "type_display": type_str, "subtype": type_str,
					"size": total_blocks, "size_display": str(total_blocks),
					"track": start_lba, "sector": p_count,
					"is_dir": False, "is_directory": False, "is_virtual_container": True,		
					"raw_meta": part_node, "vfs_meta": part_node
				})
				p_count += 1
				
		# --- DHD CAPACITY ALLOCATION FORENSIC LOGGER ---
		# We dump the raw parameters to an external text file to catch any value drift or index clamping!
		try:
			with open("dhd_capacity_trace.txt", "w") as diag_file:
				diag_file.write("=== CMD DHD DRIVE PLATTER CAPACITY AUDIT PASS ===\n")
				diag_file.write(f"Raw len(self.payload) Size : {len(self.payload)} Bytes\n")
				diag_file.write(f"Fallback File Blocks Count  : {len(self.payload) // 512} Blocks\n\n")
				
				diag_file.write("--- Zone 2 Platter Size Registers Extracted ---\n")
				diag_file.write(f"Raw MSB Byte	(Offset 0x138): {max_platter_msb} (0x{max_platter_msb:02X})\n")
				diag_file.write(f"Raw Middle Byte (Offset 0x170): {max_platter_mid} (0x{max_platter_mid:02X})\n")
				diag_file.write(f"Raw LSB Byte	(Offset 0x1A8): {max_platter_lsb} (0x{max_platter_lsb:02X})\n")
				diag_file.write(f"Calculated 24-Bit Max Blocks: {total_hardware_blocks}\n\n")
				
				diag_file.write("--- Accumulator Results ---\n")
				diag_file.write(f"Total Allocated Blocks Sum  : {total_allocated_blocks}\n")
				diag_file.write(f"Raw Theoretical Difference  : {total_hardware_blocks - total_allocated_blocks}\n")
		except Exception as trace_err:
			pass

		# --- REALLOCATION CAPACITY POOL FLUSH ---
		free_blocks_pool = max(0, total_hardware_blocks - total_allocated_blocks)
		self.free_sectors_count = free_blocks_pool	
		
		return True
		
	def flush_dhd_to_disk(self):
		"""Safely serializes the entire master platter memory payload array back onto the 
		PC hard drive, committing all sub-partition sector edits permanently in a single pass.
		"""
		if hasattr(self, "archive_name") and self.archive_name:
			try:
				with open(os.path.abspath(self.archive_name), "wb") as f_out:
					f_out.write(bytes(self.payload))
				self.is_dirty = False
				return True
			except Exception as err:
				# Log the save exception flag to the panel text notifications buffer if active
				return False
		return False
	
	def navigate_forward(self, track, sector, name):
		"""Intercepts active [ENTER] cursor actions on partition folder rows.
		Explicitly binds 'default_dir_track' and 'default_dir_sector' directly onto the 
		instantiated sub-plugin objects to lock down the directory parsing boundaries.
		"""
		part_id = int(sector)
		part_info = self.partitions_registry.get(part_id)
		
		if not part_info:
			return None
			
		t_str = part_info["type_string"]
		t_flag = part_info["type_flag"]
		
		if t_str in ["SYS", "PRN", "FOR"] or t_flag in [0x00, 0x06, 0x07, 0xFF]:
			return f"LOCKOUT: Partition '{name}' [{t_str}] is an unmountable hardware structure format."
			
		b_start = part_info["byte_start"]
		b_len = part_info["byte_length"]
		total_payload_bytes = len(self.payload)
		
		# Resolve precise standalone byte footprints to prevent format rejections
		target_size = b_len
		if t_str == "41":
			target_size = 174848  
		elif t_str == "71":
			target_size = 349696  
		elif t_str == "81" or t_str == "C81":
			target_size = 819200  
			
		if b_start >= total_payload_bytes:
			sub_partition_payload = bytearray(target_size)
		else:
			end_pos = min(b_start + target_size, total_payload_bytes)
			sub_partition_payload = bytearray(self.payload[b_start : end_pos])
			if len(sub_partition_payload) < target_size:
				sub_partition_payload.extend(b"\x00" * (target_size - len(sub_partition_payload)))
				
		# Polymorphic Driver Factory Instantiation Pass
		nested_handler = None
		if t_str == "41":
			nested_handler = D64FileSystemPlugin(bytes(sub_partition_payload))
		elif t_str == "71":
			nested_handler = D71FileSystemPlugin(bytes(sub_partition_payload))
		elif t_str == "81" or t_str == "C81":
			nested_handler = D81FileSystemPlugin(bytes(sub_partition_payload))
		elif t_str == "NAT":
			nested_handler = DNPFileSystemPlugin(bytes(sub_partition_payload))
			
		if nested_handler:
			# FIXED: Moved format type and directory track assignments strictly inside their 
			# respective type scopes to prevent cross-contaminating 1581 parameters!
			if t_str == "71":
				nested_handler.format_type = "D71"
				nested_handler.total_tracks = 70
				nested_handler.max_tracks_limit = 70
				nested_handler.default_dir_track = 18
				nested_handler.default_dir_sector = 0
			elif t_str == "41":
				nested_handler.format_type = "D64"
				nested_handler.total_tracks = 35
				nested_handler.max_tracks_limit = 35
				nested_handler.default_dir_track = 18
				nested_handler.default_dir_sector = 0
			elif t_str in ["81", "C81"]:
				nested_handler.format_type = "D81"
				nested_handler.total_tracks = 80
				nested_handler.max_tracks_limit = 80
				nested_handler.default_dir_track = 40  # FIXED: Locks 1581 onto center Track 40 natively!
				nested_handler.default_dir_sector = 0
			elif t_str == "NAT":
				nested_handler.format_type = "DNP"
				nested_handler.default_dir_track = 1
				nested_handler.default_dir_sector = 1
				
			# Invoke the native initialization mount sequence to parse file entries
			success = nested_handler.mount()
			if success or success is None:
				nested_handler.parent_dhd_handler = self
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
				
		return f"CRITICAL: Sub-VFS engine compilation error inside selected partition block frame."

	def read_virtual_sector(self, track, sector):
		"""Redirects absolute block extractions directly into target sub-partition streams."""
		# Standard fallback route back to configuration pages if un-routed
		idx = ((int(track) - 1) * 256) + int(sector)
		offset = idx * 256
		if offset + 256 <= len(self.payload):
			return bytes(self.payload[offset : offset + 256])
		return b"\x00" * 256

	def toggle_sector_allocation_status(self, track, sector):
		"""Bypasses master track allocations for direct inner partition private management passes."""
		pass


