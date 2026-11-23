class D64FileSystemPlugin(BaseVFSHandler):
	"""Dynamic Broker Adapter bridging low-level 1541 DOS handler streams."""
	def mount(self):
		self.format_type = "D64"
		self.default_dir_track = 18
		self.default_dir_sector = 0
		self.max_tracks_limit = 35
		self.payload = bytearray(self.payload)
		mem_stream = PreloadedBufferBlockStream(self.payload)
		# ... (rest of your existing mount logic continues below safely)
		sub_h = D64FileSystemHandler(mem_stream, self.archive_name)
		b_info = sub_h.get_bam_state()
		
		self.file_list = [{
			"name": "..", "is_directory": True, "is_virtual_container": False,
			"type_display": "UP-DIR", "size_display": " ", "modify_time_str": " -- -- -- "
		}]
		if b_info:
			# Isolate and clean the raw 4-character ID tracking string from your b_info model
			raw_id_block = str(b_info.get("disk_id", "	  ")).strip().upper()
			
			# Slice the 4 characters cleanly: first 2 are the ID, last 2 are the DOS version code!
			# For example, if raw_id_block is "412A", this yields id_part="41" and dos_part="2A"
			id_part = raw_id_block[:2]
			dos_part = raw_id_block[2:] if len(raw_id_block) >= 4 else "2A"
			
			# FIXED: Formats header string tightly to include your space-separated capital IDs!
			# Yields -> 0 "copydisk		   " 41 2A
			self.disk_label_msg = f'0 "{b_info["disk_name"]:<16}" {id_part} {dos_part}'
			
			# FIXED: Natively expose the calculated free blocks from the BAM parser to the VFS container state matrix
			self.free_sectors_count = b_info.get("blocks_free", 0)
			
			lt, ls = b_info["next_track"], b_info["next_sector"]
			while lt != 0:
				sec_data = sub_h.read_virtual_sector(lt, ls)
				if not sec_data:
					break
				nt, ns = int(sec_data[0]), int(sec_data[1])
				for off in range(2, 256, 32):
					slot = sec_data[off : off + 32]
					if len(slot) < 30:
						continue
					ft_raw = int(slot[0])
					if ft_raw == 0x00:
						continue
					act_t = ft_raw & 0x0F
					tgt_t, tgt_s = int(slot[1]), int(slot[2])
					c_nm = PETSCIIDecoder.decode_name(slot[3:19])
					b_cnt = struct.unpack("<H", slot[28:30])[0]
					t_lbl = "PRG" if act_t == 0x02 else "SEQ" if act_t == 0x01 else "DEL" if act_t == 0x00 else "???"
					self.file_list.append({
						"name": c_nm, "is_directory": False, "is_virtual_container": False,
						"type_display": t_lbl, "size_display": f"{b_cnt}B",
						"vfs_meta": {"track": tgt_t, "sector": tgt_s}
					})
				if nt == 0 or (nt == 0x00 and ns == 0xFF):
					break
				lt, ls = nt, ns
		self.low_level_handler = sub_h
	
	def check_sector_free_status(self, track, sector):
		"""Natively checks the raw 1541 allocation bitmask inside Track 18, Sector 0 
		to identify if a target sector block is currently free (True) or used (False) [1.1].
		"""
		# Linear byte offset to the start of Track 18, Sector 0 (357 sectors precede it)
		bam_idx = 18 * 21 * 256
		if bam_idx + 256 <= len(self.payload):
			# Each track uses a strict 4-byte descriptor block layout: [Count, Bit0, Bit1, Bit2] [1.1]
			track_offset = bam_idx + (track * 4)
			
			# Identify which byte and specific bit inside that byte handles this sector index
			b_idx = sector // 8
			b_bit = sector % 8
			
			# Extract the target byte offset position (skipping the initial 1-byte track total count)
			mask_byte = self.payload[track_offset + 1 + b_idx]
			
			# Standard 1541 bitwise rules: 1 means the sector is FREE, 0 means it is USED [1.1]
			# If the bit is set to 1, return True (Free); otherwise return False (Used) [1.1]
			return bool(mask_byte & (1 << b_bit))
			
		# Safe fallback for freshly allocated empty streams
		return True	

		
	def toggle_sector_allocation_status(self, track, sector):
		"""Natively flips the allocation bit mask for a standard 1541 .d64 image 
		at Track 18, Sector 0. 1 (Free) <-> 0 (Used).
		"""
		# Linear offset to Track 18, Sector 0 (357 sectors precede it)
		bam_idx = 18 * 21 * 256
		if bam_idx + 256 <= len(self.payload):
			# Each track uses a 4-byte entry: [Count, Bit0, Bit1, Bit2]
			track_offset = bam_idx + (track * 4)
			
			b_idx = sector // 8
			b_bit = sector % 8
			
			# XOR (^) the exact bit to toggle its state cleanly inside the payload byte
			self.payload[track_offset + 1 + b_idx] ^= (1 << b_bit)

	def extract_file_bytes(self, vfs_meta_node):
		return TUIController.extract_vfs_file_bytes(self.low_level_handler, vfs_meta_node["track"], vfs_meta_node["sector"])
		
	def read_virtual_sector(self, track, sector):
		"""Passes the sector read request straight down to the 1541 DOS engine."""
		return self.low_level_handler.read_virtual_sector(track, sector)
		
	def write_virtual_sector(self, track, sector, raw_bytes):
		"""Production-grade sector modifier with integrated Data Change Guard.
		Calculates the raw linear interleaved offset, checks if changes actually 
		exist, and only flushes to the local file system on true modifications.
		"""
		if len(raw_bytes) != 256:
			return False
			
		if track < 1 or track > 40 or sector < 0:
			return False
			
		def get_d64_linear_sector_offset(t, s):
			if 1 <= t <= 17:   
				base_off = (t - 1) * 21
				max_s = 20
			elif 18 <= t <= 24: 
				base_off = (17 * 21) + (t - 18) * 19
				max_s = 18
			elif 25 <= t <= 30: 
				base_off = (17 * 21) + (7 * 19) + (t - 25) * 18
				max_s = 17
			elif 31 <= t <= 40: 
				base_off = (17 * 21) + (7 * 19) + (6 * 18) + (t - 31) * 17
				max_s = 16
			else: 
				return -1
			
			if s > max_s: 
				return -1
			return (base_off + s) * 256

		file_offset = get_d64_linear_sector_offset(int(track), int(sector))
		if file_offset == -1 or file_offset + 256 > len(self.payload):
			return False
			
		# === STEP 1: NATIVE DATA CHANGE GUARD SAFETY CHECK ===
		existing_sector_bytes = bytes(self.payload[file_offset : file_offset + 256])
		incoming_sector_bytes = bytes(raw_bytes)
		
		if existing_sector_bytes == incoming_sector_bytes:
			# The sector data is already identical! Skip the hard drive write process completely.
			# Returning a unique string keyword signal lets the parent UI know no save was needed
			return "NO_CHANGE"

		# === STEP 2: APPLY DATA MODIFICATIONS IN ACTIVE RAM ===
		self.payload[file_offset : file_offset + 256] = incoming_sector_bytes
		
		# Flush the modified bytes directly into the low-level handler's inner stream cache
		if hasattr(self, "low_level_handler") and self.low_level_handler:
			handler = self.low_level_handler
			active_stream = getattr(handler, "stream", getattr(handler, "_stream", getattr(handler, "payload", None)))
			if active_stream:
				if hasattr(active_stream, "payload"):
					active_stream.payload[file_offset : file_offset + 256] = incoming_sector_bytes
				elif hasattr(active_stream, "buffer"):
					active_stream.buffer[file_offset : file_offset + 256] = incoming_sector_bytes
				elif isinstance(active_stream, (bytearray, list)):
					active_stream[file_offset : file_offset + 256] = incoming_sector_bytes

		# Synchronize auxiliary localized dictionary caches
		cache_key = (int(track), int(sector))
		for attr_name in ("virtual_sector_cache_pool", "virtual_sectors", "sector_cache", "_cache"):
			if hasattr(self, attr_name):
				pool = getattr(self, attr_name)
				if isinstance(pool, dict):
					pool[cache_key] = incoming_sector_bytes
					
		# SCENARIO A: This plugin is running as a NESTED SUB-PARTITION inside a master .dhd container!
		if hasattr(self, "parent_dhd_handler") and self.parent_dhd_handler:
			parent_dhd = self.parent_dhd_handler
			part_id = getattr(self, "parent_partition_id", None)
			part_info = parent_dhd.partitions_registry.get(part_id)
			
			if part_info:
				b_start = part_info["byte_start"]
				b_len = part_info["byte_length"]
				
				# Enforce mutable type conformity on the parent payload container stream
				if isinstance(parent_dhd.payload, bytes):
					parent_dhd.payload = bytearray(parent_dhd.payload)
					
				# Safely patch our modified 16MB sub-image buffer right into the parent's layout window!
				parent_dhd.payload[b_start : b_start + b_len] = self.payload[:b_len]
				
				# Arm the parent handler's dirty flag and trigger its physical disk save sequence!
				parent_dhd.is_dirty = True
				parent_dhd.flush_dhd_to_disk()
			return True
				
		# === STEP 3: PERSIST MODIFICATIONS TO THE WINDOWS FILE SYSTEM ===
		if hasattr(self, "archive_name") and self.archive_name:
			if os.path.exists(self.archive_name) and os.path.isfile(self.archive_name):
				try:
					with open(self.archive_name, "wb") as f_out:
						f_out.write(bytes(self.payload))
				except Exception:
					pass
					
		# SINGLE EXPLICIT RETURN POINT AT THE END OF THE PASS
		return True


class D64FileSystemHandler(BaseContainerHandler):
	"""Virtual 1541 DOS driver overlay."""
	def __init__(self, vfs_stream, archive_name):
		super().__init__(vfs_stream)
		self.archive_name = archive_name
		prof = ImageGeometryRegistry.PROFILES["D64"]
		self.start_track = prof["directory_track"]
		self.start_sector = prof["directory_sector"]

	def read_virtual_sector(self, track, sector):
		block_idx = ImageGeometryRegistry.translate_ts_to_block_index("D64", track, sector)
		raw_block_bytes = self.stream.read_block(block_idx)
		return bytearray(raw_block_bytes)

	def get_raw_block(self, track, sector):
		try:
			return self.read_virtual_sector(track, sector)
		except IndexError:
			return None

	def mount(self):
		pass

	def get_bam_state(self):
		"""Pure Data Engine: Computes the 1541 disk environment from the BAM bitmasks."""
		try:
			bam_sector_data = self.read_virtual_sector(self.start_track, self.start_sector)
		except IndexError:
			return None

		next_directory_track = int(bam_sector_data[0])
		next_directory_sector = int(bam_sector_data[1])
		raw_name = PETSCIIDecoder.decode_name(bam_sector_data[144:160])
		disk_name = raw_name.replace("_", " ")
		raw_id = PETSCIIDecoder.decode_name(bam_sector_data[162:167])
		disk_id = raw_id.replace("_", " ").strip()

		blocks_free_tally = 0
		matrix_bit_map = {}

		for track_idx in range(1, 36):
			matrix_bit_map[track_idx] = {}
			bam_offset = 4 + ((track_idx - 1) * 4)
			
			# FIXED: Read byte 0 of the track profile, which acts as the authentic 1541 sector count storage register
			if track_idx != 18:
				blocks_free_tally += int(bam_sector_data[bam_offset])
				
			total_sectors = ImageGeometryRegistry.get_sectors_in_track("D64", track_idx)
			mask_24 = bam_sector_data[bam_offset + 1] | (bam_sector_data[bam_offset + 2] << 8) | (bam_sector_data[bam_offset + 3] << 16)
			for s_idx in range(total_sectors):
				matrix_bit_map[track_idx][s_idx] = ((mask_24 & (1 << s_idx)) != 0)
		

		return {
			"disk_name": disk_name,
			"disk_id": disk_id,
			"blocks_free": blocks_free_tally,
			"next_track": next_directory_track,
			"next_sector": next_directory_sector,
			"bit_matrix": matrix_bit_map
		}


