class D81FileSystemPlugin:
	"""Production-grade filesystem driver plugin natively mounting, parsing, and mapping 
	high-density 1581 (.d81) virtual disk containers seamlessly [1.1].
	"""
	def __init__(self, payload_bytes, archive_name=""):
		# LINE 2384 CORRECTION: Enforces a clean, writable bytearray structure at instantiation
		self.payload = bytearray(payload_bytes)
		self.archive_name = archive_name
		self.file_list = []
		self.free_sectors_count = 0
		self.disk_label_msg = "0 \"UNLABELLED DISK \" ID 2A"
		
		# Bind the physical constraints matching high-density 1581 profiles [1.1]
		self.format_type = "D81"
		# FIXED: Essential tracking registers to drive fluid subdirectory navigation!
		# FIXED: Essential interface hooks to prevent dropdown menu/sector editor AttributeErrors!
		self.default_dir_track = 40
		self.default_dir_sector = 0		
		self.current_dir_track = 40
		self.current_dir_sector = 0
		self.directory_history_stack = []

		self.max_tracks_limit = 80
		self.no_sector_editor = False
		
		# Execute automatic mounting routines on instantiation
		self.mount()
		self.list_directory()

	@staticmethod
	def get_d81_linear_sector_index(track, sector):
		"""Translates physical 1581 1-based tracks and 0-based sectors into a flat, 
		linear offset tracking multiplier. Every single track holds exactly 40 sectors [1.1].
		"""
		if track < 1 or track > 80 or sector < 0 or sector > 39:
			return 0
		return ((track - 1) * 40) + sector

	def read_virtual_sector(self, track, sector):
		"""Extracts a raw 256-byte sector payload block natively from the image stream."""
		idx = D81FileSystemPlugin.get_d81_linear_sector_index(track, sector) * 256
		if idx + 256 <= len(self.payload):
			return bytes(self.payload[idx : idx + 256])
		return b"\x00" * 256

	def write_virtual_sector(self, track, sector, raw_bytes):
		"""Production-grade high-density 1581 .d81 sector modifier with integrated 
		Data Change Guard and sterile uniform track offset mapping [1.1, 1.13].
		"""
		if len(raw_bytes) != 256:
			return False
			
		# Enforce strict 1581 physical constraints (Tracks 1 to 80, Sectors 0 to 39) [1.13]
		if track < 1 or track > 80 or sector < 0 or sector > 39:
			return False

		# === STEP 1: NATIVE DATA CHANGE GUARD SAFETY CHECK ===
		local_cache_key = (int(track), int(sector))
		# FIXED: Looks for your class's existing cache dictionary dynamically
		active_cache = getattr(self, "sector_cache", getattr(self, "virtual_sector_cache_pool", {}))
		if local_cache_key in active_cache:
			if active_cache[local_cache_key] == bytes(raw_bytes):
				return "NO_CHANGE"

		# === STEP 2: UNIFORM 1581 LINEAR BYTE OFFSET MAPPING ===
		# Every single track holds exactly 40 sectors; no accumulator loops required! [1.13]
		file_offset = ((int(track) - 1) * 40 + int(sector)) * 256
		
		# Validate boundaries against your true master payload array length
		master_data_source = self.file_bytes if hasattr(self, "file_bytes") and self.file_bytes else self.payload
		if file_offset + 256 > len(master_data_source):
			return False
			
		# === STEP 3: APPLY CHANGES IN RAM BUFFERS ===
		incoming_bytes = bytes(raw_bytes)
		
		if not isinstance(self.payload, bytearray):
			self.payload = bytearray(self.payload)
			
		self.payload[file_offset : file_offset + 256] = incoming_bytes
		if hasattr(self, "file_bytes") and self.file_bytes:
			self.file_bytes[file_offset : file_offset + 256] = incoming_bytes
			
		# FIXED: Loops through common cache dictionaries to update whatever variable this plugin is using!
		for attr_name in ("sector_cache", "virtual_sector_cache_pool", "virtual_sectors"):
			if hasattr(self, attr_name) and isinstance(getattr(self, attr_name), dict):
				getattr(self, attr_name)[local_cache_key] = incoming_bytes

		# === STEP 4: AUTOMATED CASCADING WRITE-THROUGH BACKPLANE ===
		master_platter_bytes = bytes(self.payload)
		for attr_target in ("file_bytes", "container_bytes", "raw_data", "master_payload"):
			if hasattr(self, attr_target):
				setattr(self, attr_target, bytearray(master_platter_bytes))
				
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
				
		# === STEP 5: PERSIST MODIFICATIONS TO THE WINDOWS FILE SYSTEM ===
		if hasattr(self, "archive_name") and self.archive_name:
			absolute_file_path = os.path.abspath(self.archive_name)
			try:
				with open(absolute_file_path, "wb") as f_out:
					f_out.write(master_platter_bytes)
			except Exception:
				return False
				
		return True

	def mount(self):
		"""Natively isolates unique disk metadata, splits layout IDs, and builds headers [1.1]."""
		# Track 40, Sector 0 contains the central Disk Header block [1.1]
		header_bytes = self.read_virtual_sector(40, 0)
		
		# Offsets matching 1581 specs: Label at 4-19, ID at 22-23, DOS at 25-26 [1.1]
		raw_label = header_bytes[4:20]
		raw_id = header_bytes[22:24]
		raw_dos = header_bytes[25:27]
		
		lbl_str = PETSCIIDecoder.decode_name(raw_label).replace("_", " ")
		id_str = PETSCIIDecoder.decode_name(raw_id).strip().upper()
		dos_str = PETSCIIDecoder.decode_name(raw_dos).strip().upper()
		
		# Formats header string tightly to include your space-separated capital IDs! [1.1]
		self.disk_label_msg = f'0 "{lbl_str:<16}" {id_str} {dos_str}'
		
	def allocate_virtual_sector_in_bam(self, track, sector, bam_track=None):
		"""Hardware-accurate bitwise allocator for 1581 profiles.
		Flips the target sector's availability bit to 0 (USED) and decrements the track counter.
		Defaults to target Track 40 unless overridden by an explicit partition track [1.13].
		"""
		if track < 1 or track > 80 or sector < 0 or sector > 39:
			return False
		if track == 40:
			return False

		# Polymorphic Routing Target: Default to standard root track 40 unless told otherwise
		target_bam_root = 40 if bam_track is None else int(bam_track)

		bam_sector_num = 1 if track <= 40 else 2
		logical_track = track if track <= 40 else (track - 40)
		
		# Fetch from the dynamically requested BAM root platter coordinate location! [1.13]
		bam_data = bytearray(self.read_virtual_sector(target_bam_root, bam_sector_num))
		if len(bam_data) < 256:
			return False
			
		track_offset = 16 + ((logical_track - 1) * 6)
		byte_in_mask = 1 + (sector // 8)
		bit_position = sector % 8
		target_byte_idx = track_offset + byte_in_mask
		
		if not (bam_data[target_byte_idx] & (1 << bit_position)):
			return True # Already marked allocated
			
		bam_data[target_byte_idx] &= ~(1 << bit_position)
		if bam_data[track_offset] > 0:
			bam_data[track_offset] -= 1
			
		return self.write_virtual_sector(target_bam_root, bam_sector_num, bytes(bam_data))

	def deallocate_virtual_sector_in_bam(self, track, sector, bam_track=None):
		"""Hardware-accurate bitwise deallocator for 1581 profiles.
		Flips the target sector's availability bit to 1 (FREE) and increments the track counter.
		Defaults to target Track 40 unless overridden by an explicit partition track [1.13].
		"""
		if track < 1 or track > 80 or sector < 0 or sector > 39:
			return False
		if track == 40:
			return False

		target_bam_root = 40 if bam_track is None else int(bam_track)

		bam_sector_num = 1 if track <= 40 else 2
		logical_track = track if track <= 40 else (track - 40)
		
		bam_data = bytearray(self.read_virtual_sector(target_bam_root, bam_sector_num))
		if len(bam_data) < 256:
			return False
			
		track_offset = 16 + ((logical_track - 1) * 6)
		byte_in_mask = 1 + (sector // 8)
		bit_position = sector % 8
		target_byte_idx = track_offset + byte_in_mask
		
		if bam_data[target_byte_idx] & (1 << bit_position):
			return True # Already marked free
			
		bam_data[target_byte_idx] |= (1 << bit_position)
		if bam_data[track_offset] < 40:
			bam_data[track_offset] += 1
			
		return self.write_virtual_sector(target_bam_root, bam_sector_num, bytes(bam_data))

	def create_1581_partition_sectors(self, start_t, end_t, name, label, disk_id):
		"""Surgically compiles and injects standard 1581 partition sector containers.
		Writes the custom Partition Header, builds local sub-BAM sectors, allocates
		track availability blocks, and updates the parent directory table linkages [1.13].
		"""
		try:
			# 1. PARSE TOTAL SECTORS FOOTPRINT BOUNDS MATH
			total_tracks = (end_t - start_t) + 1
			# Track size block count yields exactly 40 sectors per track minus the local dir track [1.13]
			calculated_free_blocks = (total_tracks - 1) * 40
			
			# 2. WRITE THE PARTITION HEADER DESCRIPTORS TO SECTOR 0 OF START_TRACK [1.1, 1.13]
			header_block = bytearray(256)
			header_block[0:2] = [0x00, 0xFF] # Set structural sector link terminators
			
			# Encode string attributes tightly into standard PETSCII matching byte arrays [1.1]
			# FIXED: Forms a clean, raw bytearray padded with 0xA0 primitives to completely avoid UTF-8 expansion glitches! [1.1]
			# === FIXED: HIGH-ACCURACY BYTE CONVERTERS WITH HARDENED ASCII PADDING [1.1] ===
			petscii_label = bytearray(16)
			clean_label_str = str(label).strip()
			label_bytes = clean_label_str.encode('ascii', 'ignore')[:16]
			petscii_label[0:len(label_bytes)] = label_bytes
			for idx in range(len(label_bytes), 16):
				petscii_label[idx] = 0xA0 # Raw unshifted CBM space primitive [1.1]

			petscii_id = bytearray(2)
			clean_id_str = str(disk_id).strip()
			id_bytes = clean_id_str.encode('ascii', 'ignore')[:2]
			petscii_id[0:len(id_bytes)] = id_bytes
			for idx in range(len(id_bytes), 2):
				petscii_id[idx] = 0xA0

			# ─── YOUR PASTE STOP ANCHOR (LINES BELOW REMAIN COMPLETELY UNTOUCHED) ───
			petscii_dos = b"3D"
			
			header_block[4:20]	= petscii_label
			header_block[22:24] = petscii_id
			header_block[25:27] = petscii_dos
			
			# Encode the exact numeric free block value right at bytes 11-12 of the partition's BAM [1.13]
			struct.pack_into("<H", header_block, 11, calculated_free_blocks)
			
			# Patch Sector 0 directly onto the platter stream caches
			self.write_virtual_sector(start_t, 0, bytes(header_block))
			
			# 3. CONSTRUCT THE PARTITION SUB-BAM SECTORS (Sectors 1 and 2) [1.13]
			# To act like an authentic independent disk, we format local BAM maps
			# where tracks outside our partition footprint are pre-flagged as fully used! [1.13]
			bam1 = bytearray(256)
			bam2 = bytearray(256)
			bam1[0:2] = [0x00, 0xFF]
			bam2[0:2] = [0x00, 0xFF]
			
			# Build Sector 1 Track Map Loop (Tracks 1 to 40) [1.13]
			for t in range(1, 41):
				off = 16 + ((t - 1) * 6)
				if start_t <= t <= end_t and t != start_t:
					# This track resides inside our active partition! Mark all 40 sectors as FREE [1.13]
					bam1[off] = 40 # Set Free Sector Counter to 40
					bam1[off+1:off+6] = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF] # All availability bits set to 1
				else:
					# Out of partition bounds! Hard-flag track as FULLY USED [1.13]
					bam1[off] = 0
					bam1[off+1:off+6] = [0x00, 0x00, 0x00, 0x00, 0x00]
					
			# Build Sector 2 Track Map Loop (Tracks 41 to 80) [1.13]
			for t in range(41, 81):
				off = 16 + ((t - 41) * 6)
				if start_t <= t <= end_t and t != start_t:
					bam2[off] = 40
					bam2[off+1:off+6] = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
				else:
					bam2[0] = 0
					bam2[off+1:off+6] = [0x00, 0x00, 0x00, 0x00, 0x00]
					
			self.write_virtual_sector(start_t, 1, bytes(bam1))
			self.write_virtual_sector(start_t, 2, bytes(bam2))
			
			# 4. ZERO OUT THE FILES RECORD DATA TRACK CHUNKS IN THIS WINDOW RANGE [1.13]
			blank_sector_data = b"\x00" * 256
			for t in range(start_t + 1, end_t + 1):
				for s in range(40):
					self.write_virtual_sector(t, s, blank_sector_data)
					
			# 5. FIXED: STREAMLINED ALLOCATION DRIVES EXCLUSIVELY INTO THE ACTIVE WORKSPACE BAM [1.13]
			active_dir_t = getattr(self, "current_dir_track", 40)
			
			for t in range(start_t, end_t + 1):
				for s in range(40):
					# Pass the active directory track context so the block is claimed inside the proper sandbox layer! [1.13]
					self.allocate_virtual_sector_in_bam(t, s, bam_track=active_dir_t)
					
					# Pass B: If we are inside a subdirectory partition, copy the used mark into its local sub-BAM! [1.13]
					if active_dir_t != 40:
						self.allocate_virtual_sector_in_bam(t, s, bam_track=active_dir_t)
					
			# 6. INJECT A CLEAN "CBM" FILE SLOT RECORD ENTRY INTO THE CURRENT PARENT DIRECTORY LAYER [1.13]
			active_dir_t = getattr(self, "current_dir_track", 40)
			active_dir_s = 3
			
			slot_injected = False
			while active_dir_t != 0:
				dir_sector = bytearray(self.read_virtual_sector(active_dir_t, active_dir_s))
				if len(dir_sector) < 256:
					break
					
				# Look for an unallocated empty file slot row stub (First byte == 0x00)
				for off in range(2, 256, 32):
					if dir_sector[off] == 0x00:
						# Empty slot stub found! Package our partition details right here
						dir_sector[off] = 0x85 # File Type Number: Closed CBM Partition entry flag! [1.13]
						dir_sector[off+1] = start_t # Target Track Link Vector [1.13]
						dir_sector[off+2] = 0		# Target Sector Link Vector (Always 0 for partitions) [1.13]
						
						# Inject Filename text padded cleanly with PETSCII space marks [1.1]
						petscii_name = bytearray(16)
						name_enc = name.encode('utf-8', 'ignore')[:16]
						petscii_name[0:len(name_enc)] = name_enc
						for i in range(len(name_enc), 16):
							petscii_name[i] = 0xA0
							
						dir_sector[off+3:off+19] = petscii_name
						
						# Inject the 16-bit block size allocation count [1.1]
						struct.pack_into("<H", dir_sector, off + 28, calculated_free_blocks)
						
						self.write_virtual_sector(active_dir_t, active_dir_s, bytes(dir_sector))
						slot_injected = True
						break
						
				if slot_injected:
					break
					
				# Trace down to the next linked directory track sector block link in the chain
				next_t, next_s = int(dir_sector[0]), int(dir_sector[1])
				if next_t == 0:
					# If the directory is full, allocate an extended directory sector block link next!
					break
				active_dir_t, active_dir_s = next_t, next_s
				
			return True
		except Exception:
			return False
		
	def get_partition_creation_track_matrix(self):
		"""Computes a dictionary map of tracks 1-80 indicating selection eligibility
		based on active workspace scopes, BAM sector usage, and look-ahead depth thresholds [1.13].
		"""
		# DYNAMIC SOURCE LOGIC: Look at the folder track we are currently exploring!
		active_t = getattr(self, "current_dir_track", 40)
		
		# Set baseline playground boundaries
		min_bound = 1
		max_bound = 80
		
		# If we are nested inside a partition, the playground is bound strictly inside its scope
		if active_t != 40:
			min_bound = active_t
			# Extract the parent partition's absolute upper track limit
			max_bound = getattr(self, "current_partition_end_track", min_bound + 11) # Default to 12 tracks span fallback

		track_matrix = {}
		
		# Initialize all tracks across the platter
		for t in range(1, 81):
			if t < min_bound or t > max_bound or t == 40:
				track_matrix[t] = "X" # Hard lock out-of-scope regions
				continue
				
			# Inspect the sub-BAM sectors of our ACTIVE location track, not a hardcoded 40! [1.13]
			bam_sec = 1 if t <= 40 else 2
			log_t = t if t <= 40 else (t - 40)
			bam_data = self.read_virtual_sector(active_t, bam_sec)
			
			if not bam_data or len(bam_data) < 256:
				track_matrix[t] = "X"
				continue
				
			t_offset = 16 + ((log_t - 1) * 6)
			free_sectors_count = int(bam_data[t_offset])
			
			if free_sectors_count < 40:
				track_matrix[t] = "X" # Even one allocated sector locks out the entire track
			else:
				track_matrix[t] = "." # Clean unallocated track
				
		# PASS 2: COUPLER LOOK-AHEAD PASS CONSTRICTOR
		final_eligible_matrix = {}
		for t in range(1, 81):
			if track_matrix.get(t) == "X":
				final_eligible_matrix[t] = "X"
				continue
				
			can_fit = True
			# A partition requires a minimum footprint chunk size of 3 tracks sequential
			for look_ahead in range(t, t + 3):
				if look_ahead > max_bound:
					can_fit = False
					break
				if look_ahead == 40 or track_matrix.get(look_ahead) == "X":
					can_fit = False
					break
			if can_fit:
				final_eligible_matrix[t] = "."
			else:
				final_eligible_matrix[t] = "X"
				
		return final_eligible_matrix

	def list_directory(self):
		"""Traces standard 1581 directory linkages dynamically across subdirectories [1.13]."""
		# Forcefully pull our newly shifted dynamic directory track from the state matrix
		curr_t = getattr(self, "current_dir_track", 40)
		curr_s = 3
		
		self.file_list = []
		
		# Inject our back-out hook if we are operating inside a nested sub-partition space [1.13]
		if curr_t != 40:
			self.file_list.append({
				"name": "..", "is_directory": True, "is_virtual_container": False,
				"type_display": "UP-DIR", "size_display": " ", "modify_time_str": " -- -- -- "
			})
			
		while curr_t != 0:
				
			# DYNAMIC OVERRIDE: Force the sector reader to pull from curr_t instead of hardcoded track maps!
			sec_data = self.read_virtual_sector(curr_t, curr_s)
			if not sec_data or len(sec_data) < 2:
				break

				
			# If the low-level sector buffer returns empty or un-demodulated junk bytes, drop out
			next_t, next_s = int(sec_data[0]), int(sec_data[1])
			
			# Process the 8 standard 32-byte file entry rows inside this sector allocation window
			for off in range(2, 256, 32):
				slot = sec_data[off : off + 32]
				if len(slot) < 30:
					continue
					
				ft_raw = int(slot[0])
				if ft_raw == 0x00: 
					continue
					
				type_flags = ft_raw & 0x0F
				core_type = type_flags & 0x07
				
				is_sub_dir = False
				if core_type == 5:
					t_lbl = "CBM"
					is_sub_dir = True
				else:
					t_lbl = "PRG" if core_type == 2 else "SEQ" if core_type == 1 else "USR" if core_type == 3 else "REL" if core_type == 4 else "DEL"
					
				if ft_raw & 0x40: t_lbl = f"<{t_lbl}"
				if not (ft_raw & 0x80): t_lbl = f"*{t_lbl}"
					
				tgt_t, tgt_s = int(slot[1]), int(slot[2])
				raw_name = slot[3:19]
				c_nm = PETSCIIDecoder.decode_name(raw_name)
				b_cnt = struct.unpack("<H", slot[28:30])[0]
				
				self.file_list.append({
					"name": c_nm, "is_directory": is_sub_dir, "is_virtual_container": False,
					"type_display": t_lbl, "size_display": str(b_cnt),
					"vfs_meta": {"track": tgt_t, "sector": tgt_s, "is_1581_partition": is_sub_dir}
				})
				
			# Standard 1581 directory chain layout routing progression
			if next_t == 0:
				break
			curr_t, curr_s = next_t, next_s

		# =========================================================================
		# 🎯 CORE ENGINE FIX: 1581 HARDWARE-MANUAL ALIGNED BAM & HEADER 🎯
		# =========================================================================
		header_t = getattr(self, "current_dir_track", 40)
		free_count = 0

		# 1. FORCE MANDATORY UP-DIR (..) ENTRY HOOK AT THE TOP OF THE LIST ARRAY
		# Ensures a clean escape link always exists to back out of any mounted state!
		has_up_dir = any(item["name"] == ".." for item in self.file_list)
		if not has_up_dir:
			self.file_list.insert(0, {
				"name": "..", "is_directory": True, "is_virtual_container": False,
				"type_display": "UP-DIR" if header_t == 40 else "CBM-DIR", 
				"size_display": " ", "modify_time_str": " -- -- -- "
			})

		# 2. ACCURATE HARDWARE SCANNERS READ COUNTER BYTES FROM SECTOR 1 & 2 [1.13]
		try:
			# Your manual page proves BAM1 is Sector 1 and BAM2 is Sector 2! [1.13]
			bam_sector_1 = self.read_virtual_sector(header_t, 1)
			bam_sector_2 = self.read_virtual_sector(header_t, 2)

			if bam_sector_1 and len(bam_sector_1) >= 256 and bam_sector_2 and len(bam_sector_2) >= 256:
				# PASS A: Tracks 1 to 40 are stored on Sector 1, starting at byte 16 [1.13]
				for t in range(1, 41):
					if t == 40: 
						continue  # Skip directory track capacity counting [1.13]
					# Calculate the 6-byte stride block offset for this track [1.13]
					off = 16 + ((t - 1) * 6)
					if off < len(bam_sector_1):
						# Read the track's absolute free sector counter byte! [1.13]
						free_count += int(bam_sector_1[off])

				# PASS B: Tracks 41 to 80 are stored on Sector 2, starting at byte 16 [1.13]
				for t in range(41, 81):
					# Track 41 maps to relative index 0 inside Sector 2 [1.13]
					off = 16 + ((t - 41) * 6)
					if off < len(bam_sector_2):
						# Read the track's absolute free sector counter byte! [1.13]
						free_count += int(bam_sector_2[off])
		except Exception:
			free_count = 0

		# Synchronize the free capacity counters across the driver state properties
		self.free_sectors_count = free_count
		self.free_count = free_count

		# 3. EXTRACT DISK VOLUME METADATA NATIVELY FROM DIRECTORY HEADER SECTOR 0 [1.1]
		try:
			# Manual page verifies that the Name and IDs live exclusively on Sector 0 [1.1]
			header_sector = self.read_virtual_sector(header_t, 0)
			if header_sector and len(header_sector) >= 30:
				header_bytes = bytearray(header_sector)
				
				# Direct standard 1581 directory header layout offset ranges [1.1]
				raw_label = header_bytes[4:20]
				raw_id = header_bytes[22:24]
				raw_dos = header_bytes[25:27]
				
				# Convert bytes through your standard PETSCII Decoder module [1.1]
				lbl_str = PETSCIIDecoder.decode_name(raw_label).replace("_", " ").rstrip()
				id_str = PETSCIIDecoder.decode_name(raw_id).strip().upper()
				dos_str = PETSCIIDecoder.decode_name(raw_dos).strip().upper()
				
				if not lbl_str: 
					lbl_str = "1581 DISK" if header_t == 40 else f"PARTITION T{header_t}"
				if not id_str:	
					id_str = "81" if header_t == 40 else "82"
				if not dos_str: 
					dos_str = "3D"
				
				self.disk_label_msg = f'"{lbl_str:<16}" {id_str} {dos_str}'
		except Exception:
			pass

		return self.file_list
		
	def extract_file_bytes(self, vfs_meta):
		"""Sequentially extracts raw file data bytes from a 1581 filesystem structure.
		Traces the 1581 track/sector block allocation links to compile a pristine 
		payload buffer array ready for cross-filesystem file copies. [1.13, 1.26]
		"""
		if not vfs_meta:
			return b""
			
		# Extract starting track and sector markers from the 1581 directory entry [1.13]
		curr_t = int(vfs_meta.get("track", 0))
		curr_s = int(vfs_meta.get("sector", 0))
		
		if curr_t == 0:
			return b""
			
		file_bytes_accumulator = bytearray()
		visited_blocks = set()
		
		# Trace the 1581 linked-list sector allocation path block-by-block [1.13]
		while curr_t != 0 and (curr_t, curr_s) not in visited_blocks:
			visited_blocks.add((curr_t, curr_s))
			
			# Fetch the raw 256-byte 1581 sector straight out of memory
			sector_buffer = self.read_virtual_sector(curr_t, curr_s)
			if not sector_buffer or len(sector_buffer) < 256:
				break
				
			# Standard CBM architecture link bytes mapping [1.13]:
			# FIXED: Added explicit [0] and [1] brackets to read raw byte values as integer scalars!
			next_t = sector_buffer[0]
			next_s = sector_buffer[1]
			
			if next_t == 0:
				# Target block reached! Byte 1 acts as a length offset integer [1.13]
				valid_bytes_count = next_s
				if 2 <= valid_bytes_count <= 255:
					file_bytes_accumulator.extend(sector_buffer[2 : valid_bytes_count + 1])
				else:
					file_bytes_accumulator.extend(sector_buffer[2:])
				break
			else:
				# Middle data block payload: grab all 254 data bytes cleanly [1.13]
				file_bytes_accumulator.extend(sector_buffer[2:])
				
			curr_t = next_t
			curr_s = next_s
			
		return bytes(file_bytes_accumulator)
		
	def check_sector_free_status(self, track, sector):
		"""Natively checks the 1581 dual-BAM bitmasks to identify if a block is free (True) 
		or used (False), keeping your BAM Editor fully compatible with .d81 formats out of the box [1.1]!
		"""
		if track < 1 or track > 80 or sector < 0 or sector > 39:
			return False
			
		if track <= 40:
			bam_bytes = self.read_virtual_sector(40, 1)
			offset = 16 + ((track - 1) * 6)
		else:
			bam_bytes = self.read_virtual_sector(40, 2)
			offset = 16 + ((track - 41) * 6)
			
		# Skip past the 1-byte track total counter byte to find the 5-byte mask array start [1.1]
		mask_start = offset + 1
		b_idx = sector // 8
		b_bit = sector % 8
		
		mask_byte = bam_bytes[mask_start + b_idx]
		return bool(mask_byte & (1 << b_bit))


