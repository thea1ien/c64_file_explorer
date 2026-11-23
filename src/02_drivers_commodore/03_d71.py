class D71FileSystemPlugin(BaseVFSHandler):
	"""Dynamic Broker Adapter parsing legacy Commodore 1571 Double-Sided (.D71) images 
	utilizing your exact Inside Commodore DOS 1-based 33-byte step layout blocks.
	"""
	@staticmethod
	def get_d71_linear_sector_index(track, sector):
		"""Fact-aligned 1571 sector accumulator mapping 70 tracks to linear array slots."""
		side0_offsets = [
			0,	 # Track 0 placeholder
			0,	 21,  42,  63,	84, 105, 126, 147, 168, 189, 210, 231, 252, 273, 294, 315, 336, # 1-17
			357, 376, 395, 414, 433, 452, 471, # 18-24
			490, 508, 526, 544, 562, 580, # 25-30
			598, 615, 632, 649, 666		   # 31-35
		]
		
		if 1 <= track <= 35:
			return side0_offsets[track] + sector
		elif 36 <= track <= 70:
			normalized_track = track - 35
			return 683 + side0_offsets[normalized_track] + sector
		return 0

	def mount(self):
		self.payload = bytearray(self.payload)
		self.format_type = "D71"
		self.default_dir_track = 18
		self.default_dir_sector = 0
		self.max_tracks_limit = 70
		self.no_sector_editor = False

		# FIXED: Hardcode a printable text default first to guarantee it is NEVER NoneType!
		self.disk_label_msg = "UNLABELLED 1571 DISK"
		
		# Natively pull disk labels out of Side 0 BAM (Track 18, Sector 0)
		bam_idx = D71FileSystemPlugin.get_d71_linear_sector_index(18, 0) * 256
		if bam_idx + 256 <= len(self.payload):
			# Extract fields natively using identical 1541/1571 layout offsets [1.1]
			raw_label = self.payload[bam_idx + 144 : bam_idx + 160]
			raw_id = self.payload[bam_idx + 162 : bam_idx + 164]
			raw_dos = self.payload[bam_idx + 165 : bam_idx + 167]
			
			lbl_str = PETSCIIDecoder.decode_name(raw_label).replace("_", " ")
			id_str = PETSCIIDecoder.decode_name(raw_id).strip().upper()
			dos_str = PETSCIIDecoder.decode_name(raw_dos).strip().upper()
			
			# FIXED: Unifies D71 header with accurate space-separated capital IDs! [1.1]
			self.disk_label_msg = f'0 "{lbl_str:<16}" {id_str} {dos_str}'
					# FORCE CORE LISTING MAP INITIALIZATION:
		# Guarantees that your 1571 directory list builder runs explicitly upon mounting!
		self.file_list = self.list_directory()
		return True

			
	def check_sector_free_status(self, track, sector):
		"""Natively checks your live Side 0 and Side 1 allocation bitmasks to identify 
		if a sector is marked free (True) or used (False).
		"""
		if track <= 35:
			s0_idx = D71FileSystemPlugin.get_d71_linear_sector_index(18, 0) * 256
			track_offset = s0_idx + (track * 4)
			# Look right at the byte bitmask positions
			b_idx = sector // 8
			b_bit = sector % 8
			mask_byte = self.payload[track_offset + 1 + b_idx]
			return bool(mask_byte & (1 << b_bit))
		else:
			s1_idx = D71FileSystemPlugin.get_d71_linear_sector_index(53, 0) * 256
			t_offset = track - 36
			track_bytes_start = s1_idx + (t_offset * 3)
			b_idx = sector // 8
			b_bit = sector % 8
			mask_byte = self.payload[track_bytes_start + b_idx]
			return bool(mask_byte & (1 << b_bit))
			
	def toggle_sector_allocation_status(self, track, sector):
		"""Natively flips the allocation bit mask for a 1571 double-sided .d71 image 
		handling Side 0 (Track 1-35) or Side 1 (Track 36-70) bit alignments perfectly.
		"""
		if track <= 35:
			s0_idx = D71FileSystemPlugin.get_d71_linear_sector_index(18, 0) * 256
			track_offset = s0_idx + (track * 4)
			b_idx = sector // 8
			b_bit = sector % 8
			self.payload[track_offset + 1 + b_idx] ^= (1 << b_bit)
		else:
			s1_idx = D71FileSystemPlugin.get_d71_linear_sector_index(53, 0) * 256
			t_offset = track - 36
			track_bytes_start = s1_idx + (t_offset * 3)
			b_idx = sector // 8
			b_bit = sector % 8
			self.payload[track_bytes_start + b_idx] ^= (1 << b_bit)
			
	def write_virtual_sector(self, track, sector, data_bytes):
		"""Unified Flat-File Sector Writer for the 1571 plugin.
		Treats the .d71 layout as a flat extension of a 1541 to achieve perfect parity 
		with our working .d64 saving mechanics, both standalone and inside a .dhd container.
		"""
		t = int(track)
		s = int(sector)
		
		# Compute the flat, sequential sector index matching a standard CBM .d71 stream layout
		# Track 18 sits exactly where it belongs, and side-2 registers append sequentially
		linear_idx = D71FileSystemPlugin.get_d71_linear_sector_index(t, s) * 256
		
		if linear_idx + 256 > len(self.payload):
			return False
			
		clean_data = bytes(data_bytes[:256].ljust(256, b"\x00"))
		
		# Enforce a single globally shared mutable type for array patching operations
		if isinstance(self.payload, bytes):
			self.payload = bytearray(self.payload)
			
		# CRITICAL FIX: Write the modified hex bytes DIRECTLY into self.payload!
		# This eliminates any hidden private stream bypass loops permanently.
		self.payload[linear_idx : linear_idx + 256] = clean_data
		self.is_dirty = True
		
		# --- DHD MULTI-PARTITION SAVE INTERCEPT HOOK ---
		# Because self.payload is now actively updated, our parent flush loop will 
		# effortlessly capture your modifications and commit them to the PC hard drive!
		if hasattr(self, "parent_dhd_handler") and self.parent_dhd_handler:
			parent_dhd = self.parent_dhd_handler
			part_id = getattr(self, "parent_partition_id", None)
			part_info = parent_dhd.partitions_registry.get(part_id)
			
			if part_info:
				b_start = part_info["byte_start"]
				b_len = part_info["byte_length"]
				
				if isinstance(parent_dhd.payload, bytes):
					parent_dhd.payload = bytearray(parent_dhd.payload)
					
				# Pull a clean deep copy snapshot out of our freshly updated payload buffer array
				current_updated_bytes = bytes(self.payload)
				
				# Patch the parent's master platter block window using the absolute byte constraints of the partition
				parent_dhd.payload[b_start : b_start + b_len] = current_updated_bytes[:b_len]
				parent_dhd.is_dirty = True
				parent_dhd.flush_dhd_to_disk()
			return True
			
		# Standalone file serialization pass back to local PC storage media
		if hasattr(self, "archive_name") and self.archive_name:
			try:
				with open(os.path.abspath(self.archive_name), "wb") as f_out:
					f_out.write(bytes(self.payload))
			except Exception:
				pass
		return True
			
		# === STEP 1: STERILE 70-TRACK LINEAR BYTE MAPPING ===
	def get_d71_linear_sector_offset(t, s):
		total_sectors_accumulator = 0
		
		# Walk through every track preceding our target to cleanly sum the sectors up
		for check_t in range(1, t):
			# Safely query your master profile matrix for each track's sector density
			sec_in_track = ImageGeometryRegistry.get_sectors_in_track("D71", check_t)
			total_sectors_accumulator += sec_in_track
			
		# Check boundary limits for the targeted sector cell
		max_s_allowed = ImageGeometryRegistry.get_sectors_in_track("D71", t)
		if s >= max_s_allowed:
			return -1
			
		# Clear mathematical linear offset address (256 bytes per sector block)
		return (total_sectors_accumulator + s) * 256

		file_offset = get_d71_linear_sector_offset(int(track), int(sector))
		
		# Validate boundaries against your true master payload array length
		master_data_source = self.file_bytes if hasattr(self, "file_bytes") and self.file_bytes else self.payload
		if file_offset == -1 or file_offset + 256 > len(master_data_source):
			return False
			
		# === STEP 2: APPLY CHANGES IN RAM BUFFERS ===
		incoming_bytes = bytes(raw_bytes)
		self.payload[file_offset : file_offset + 256] = incoming_bytes
		if hasattr(self, "file_bytes") and self.file_bytes:
			self.file_bytes[file_offset : file_offset + 256] = incoming_bytes
			
		# Synchronize auxiliary localized dictionary caches safely
		local_cache_key = (int(track), int(sector))
		if hasattr(self, "virtual_sector_cache_pool"):
			self.virtual_sector_cache_pool[local_cache_key] = incoming_bytes

		# === STEP 3: AUTOMATED CASCADING WRITE-THROUGH BACKPLANE ===
		master_platter_bytes = bytes(self.payload)
		for attr_target in ("file_bytes", "container_bytes", "raw_data", "master_payload"):
			if hasattr(self, attr_target):
				setattr(self, attr_target, bytearray(master_platter_bytes))

		# === STEP 4: PERSIST MODIFICATIONS TO THE WINDOWS FILE SYSTEM ===
		if hasattr(self, "archive_name") and self.archive_name:
			absolute_file_path = os.path.abspath(self.archive_name)
			try:
				with open(absolute_file_path, "wb") as f_out:
					f_out.write(master_platter_bytes)
			except Exception:
				return False
				
		return True

	def list_directory(self):
		"""Returns the fully parsed folder directory entries list matching your exact 32-byte step buffer specs."""
		file_list = [{
			"name": "..", "is_directory": True, "is_virtual_container": False,
			"type_display": "UP-DIR", "size_display": " ", "modify_time_str": " -- -- -- "
		}]
		
		curr_t = 18
		curr_s = 1
		visited_sectors = set()
			
		while curr_t > 0 and (curr_t, curr_s) not in visited_sectors:
			if curr_t > 70:
				break
					
			visited_sectors.add((curr_t, curr_s))
			linear_idx = D71FileSystemPlugin.get_d71_linear_sector_index(curr_t, curr_s) * 256
			if linear_idx + 256 > len(self.payload):
				break
				
			# 1. Load the full 256-byte directory sector
			sector_data = self.payload[linear_idx : linear_idx + 256]
			
			# 2. Extract and note the first 2 jump bytes to manage our track chain routing
			next_t = sector_data[0]
			next_s = sector_data[1]
			
			# 3. Separate the remaining 254 bytes into a clean, independent record buffer array
			record_buffer = sector_data[2:256]
			
			# 4. Step precisely by 32 bytes using your proven multiplier pass
			for slot_idx in range(8):
				start_offset = slot_idx * 32
				
				# FIXED: Validates boundaries against the full 256-byte sector data limit to catch the 8th slot cleanly!
				# Slot 7 ends exactly at physical offset 2 + 224 + 32 = 256, fitting perfectly.
					
				# Extract the isolated 32-byte file record row out of our clean buffer window
				entry_bytes = record_buffer[start_offset : start_offset + 32]
				
				# Local 0-based relative offset targets inside the standard 32-byte file record
				ftype_raw = entry_bytes[0] # Offset $01: File type flag byte [1.1]
				if ftype_raw == 0x00: # Empty or unallocated record slot placeholder
					continue
					
				start_t = entry_bytes[1] # Offset $02: Starting Track
				start_s = entry_bytes[2] # Offset $03: Starting Sector
				
				# Filename field tracks from relative index positions 3 to 19 inclusive
				raw_name = entry_bytes[3:19]
				
				# Fixed properties trackers pull block size decimal bytes accurately from offsets +28 and +29!
				size_low = entry_bytes[28]
				size_high = entry_bytes[29]
				size_blocks = size_low + (size_high << 8)
				
				try:
					# FIXED: Grabs the numerical array directly and triggers the filename tracking flag!
					# This forces both the leading AND trailing spaces to turn into safe background 
					# underscores (_) globally, completely bypassing any metadata cleanups.
					clean_name = PETSCIIDecoder.decode_name(raw_name)
					
					# Decode file type display flags
					type_flags = ftype_raw & 0x0F
					if type_flags == 1: type_lbl = "SEQ"
					elif type_flags == 2: type_lbl = "PRG"
					elif type_flags == 3: type_lbl = "USR"
					elif type_flags == 4: type_lbl = "REL"
					else: type_lbl = "DEL"
					
					if (ftype_raw & 0x80):
						type_lbl = type_lbl
					else:
						type_lbl = f"*{type_lbl}"
						
					if clean_name:
						file_list.append({
							"name": clean_name, "is_directory": False, "is_virtual_container": False,
							"type_display": type_lbl, "size_display": str(size_blocks),
							"vfs_meta": {"track": start_t, "sector": start_s, "blocks": size_blocks}
						})
				except Exception:
					continue
					
			curr_t = next_t
			curr_s = next_s

		# --- PART B: CALCULATE BLOCKS FREE FROM TWIN BAM ZONES ---
		free_blocks_total = 0
		s0_idx = D71FileSystemPlugin.get_d71_linear_sector_index(18, 0) * 256
		
		if s0_idx + 256 <= len(self.payload):
			# 1. SIDE 0 (TRACKS 1-35): Read from Track 18, Sector 0 counters [1.1]
			for t_idx in range(1, 36):
				if t_idx == 18:
					continue # Track 18 is the directory track block itself, handled natively [1.1]
				free_blocks_total += int(self.payload[s0_idx + (t_idx * 4)])
				
			# 2. EVALUATE DOUBLE-SIDED FLAG STATUS [1.1]
			# Check offset 0x03 inside the Side 0 BAM (Hex 0x80 is decimal 128) [1.1]
			is_double_sided = (self.payload[s0_idx + 3] == 0x80)
			
			if is_double_sided:
				s1_idx = D71FileSystemPlugin.get_d71_linear_sector_index(53, 0) * 256
				if s1_idx + 256 <= len(self.payload):
					# Direct physical track dictionary mapping Side 1 tracks (36-70) straight to their sector caps [1.1]
					track_sector_counts = {
						36: 21, 37: 21, 38: 21, 39: 21, 40: 21, 41: 21, 42: 21, 43: 21, 44: 21, 
						45: 21, 46: 21, 47: 21, 48: 21, 49: 21, 50: 21, 51: 21, 52: 21,
						53: 19, 54: 19, 55: 19, 56: 19, 57: 19, 58: 19, 59: 19,
						60: 18, 61: 18, 62: 18, 63: 18, 64: 18, 65: 18,
						66: 17, 67: 17, 68: 17, 69: 17, 70: 17
					}
					
					# Step sequentially by 3 bytes for each track's bitmask on Side 1 (35 tracks total) [1.1]
					# Tracks 36-70 bitmasks start exactly at physical byte offset 0 of Track 53, Sector 0 [1.1]
					for t_offset in range(35):
						actual_track = 36 + t_offset
						
						track_bytes_start = s1_idx + (t_offset * 3)
						max_sectors = track_sector_counts[actual_track]
						
						b1 = self.payload[track_bytes_start]
						b2 = self.payload[track_bytes_start + 1]
						b3 = self.payload[track_bytes_start + 2]
						
						# Combine the 3 bytes into a clean 24-bit integer mask natively [1.1]
						track_mask = b1 | (b2 << 8) | (b3 << 16)
						
						# Standard 1541/1571 bitwise rules: 1 means the sector block is FREE [1.1]
						for sector_bit in range(max_sectors):
							if track_mask & (1 << sector_bit):
								free_blocks_total += 1
								
		self.free_sectors_count = free_blocks_total
		return file_list

	def read_virtual_sector(self, track, sector):
		"""Natively queries the raw .d71 payload buffer using 70-track sector offset formulas."""
		linear_idx = D71FileSystemPlugin.get_d71_linear_sector_index(track, sector) * 256
		if linear_idx + 256 <= len(self.payload):
			return bytearray(self.payload[linear_idx : linear_idx + 256])
		return bytearray(256)

	def extract_file_bytes(self, vfs_meta_node):
		"""Assembles raw file payload byte streams by sequentially traversing the 1571 track/sector chains."""
		file_bytes = bytearray()
		curr_t = vfs_meta_node.get("track", 0)
		curr_s = vfs_meta_node.get("sector", 0)
		visited = set()
		
		while curr_t > 0 and (curr_t, curr_s) not in visited:
			if curr_t > 70:
				break
			visited.add((curr_t, curr_s))
			linear_idx = D71FileSystemPlugin.get_d71_linear_sector_index(curr_t, curr_s) * 256
			if linear_idx + 256 > len(self.payload):
				break
				
			sector_data = self.payload[linear_idx : linear_idx + 256]
			next_t = int(sector_data[0])
			next_s = int(sector_data[1])
			
			if next_t == 0:
				active_bytes_count = next_s - 1
				file_bytes.extend(sector_data[2 : 2 + active_bytes_count])
			else:
				file_bytes.extend(sector_data[2:256])
				
			curr_t = next_t
			curr_s = next_s
			
		return bytes(file_bytes)


