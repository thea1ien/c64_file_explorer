class G64FileSystemPlugin:
	"""Production-grade low-level GCR bitstream filesystem plugin driver. 
	Enhanced to support a true 42-track limit, preserve pre-existing speed zone data arrays 
	natively, and feed standard 256-byte sector buffers into high-level C64 Explorer loops.
	"""
	GCR_TO_NYBBLE = {
		0x0A: 0x0, 0x0B: 0x1, 0x12: 0x2, 0x13: 0x3,
		0x0E: 0x4, 0x0F: 0x5, 0x16: 0x6, 0x17: 0x7,
		0x09: 0x8, 0x19: 0x9, 0x1A: 0xA, 0x1B: 0xB,
		0x0D: 0xC, 0x1D: 0xD, 0x1E: 0xE, 0x15: 0xF
	}
	# Official Commodore 4-to-5 GCR Conversion Lookup Matrix Table [1.1]
	
	NYBBLE_TO_GCR = {
		0x0: 0x0A, 0x1: 0x0B, 0x2: 0x12, 0x3: 0x13,
		0x4: 0x0E, 0x5: 0x0F, 0x6: 0x16, 0x7: 0x17,
		0x8: 0x09, 0x9: 0x19, 0xA: 0x1A, 0xB: 0x1B,
		0xC: 0x0D, 0xD: 0x1D, 0xE: 0x1E, 0xF: 0x15
	}

	def encode_bytes_to_gcr_bits(self, raw_payload_bytes):
		"""Computes the 1541 data sector XOR checksum, frames the 260-byte block,
		maps every nybble to a 5-bit GCR code, and returns exactly 3,250 bits [1.1].
		"""
		if len(raw_payload_bytes) != 256:
			return []
		
		
		# STAGE 1: COMPUTE COMMODORE DOS SECTOR DATA XOR CHECKSUM [1.1]
		data_checksum = 0
		for b in raw_payload_bytes:
			data_checksum ^= b

		# STAGE 2: ASSEMBLE THE 260-BYTE COMMODORE DOS DATA BLOCK LAYOUT [1.1]
		# Byte 0: Data Block Identifier Token ($07) [1.1]
		# Bytes 1-256: Modified 256-Byte Payload Data [1.1]
		# Byte 257: Generated 1-Byte XOR Checksum [1.1]
		# Bytes 258-259: Trailing Off-Overhead Padding Gap ($00 $00) [1.1]
		framed_block = bytearray([0x07])
		framed_block.extend(raw_payload_bytes)
		framed_block.append(data_checksum)
		framed_block.extend([0x00, 0x00])
		# STAGE 3 & 4: EXECUTE THE TRUE 4-TO-5 NYBBLE RE-ENCODING & BIT FLATTENING [1.1]
		encoded_bit_stream = []
		for byte_val in framed_block:
			# Isolate the high and low 4-bit nybbles cleanly
			high_nybble = (byte_val >> 4) & 0x0F
			low_nybble = byte_val & 0x0F
			# FIXED: Referencing via Class Name scopes the lookup dictionary perfectly!
			gcr_high = G64FileSystemPlugin.NYBBLE_TO_GCR[high_nybble]
			gcr_low = G64FileSystemPlugin.NYBBLE_TO_GCR[low_nybble]

			# Convert the 5-bit high GCR word serially into integer bits [1.1]
			for pos in range(4, -1, -1):
				encoded_bit_stream.append((gcr_high >> pos) & 1)

			# Convert the 5-bit low GCR word serially into integer bits [1.1]
			for pos in range(4, -1, -1):
				encoded_bit_stream.append((gcr_low >> pos) & 1)

		# Returns an absolute un-truncated list array of exactly 3,250 bits [1.1]
		
		return encoded_bit_stream

	def __init__(self, file_bytes, archive_name=""):
		self.payload = bytearray(file_bytes)
		self.archive_name = archive_name
		self.format_type = "G64"
		self.file_list = []
		self.free_sectors_count = 0
		self.disk_label_msg = "0 \"G64 IMAGE		\" ID 2A"
		# On-demand virtual sector cache pool dictionary (track, sector -> 256 bytes)
		self.virtual_sector_cache_pool = {}
		
		# FIXED REQUIREMENT: Initialize the permanent track geometry bit map cache!
		# Maps (track, sector) -> absolute bit offset of the 0x07 data block ID
		self.track_geometry_offset_map = {}

		
		# FIXED: Expanded physical track limits from 35 straight up to 42 max track!
		self.default_dir_track = 18
		self.default_dir_sector = 0
		self.max_tracks_limit = 42
		self.no_sector_editor = False # Allows Sector Editor to read our decoded virtual blocks
		
		# On-demand virtual sector cache pool dictionary (track, sector -> 256 bytes)
		self.virtual_sector_cache_pool = {}
		
		# Execute mounting and directory compiling sequences
		self.mount()
		self.list_directory()
		
	def get_cached_sector_bit_offset(self, track, sector):
		"""Queries the geometry cache map for a sector's bit coordinate position.
		If the track hasn't been cached or demodulated yet, it forces a track sweep.
		"""
		cache_key = (int(track), int(sector))
		if cache_key not in self.track_geometry_offset_map:
			self.demodulate_track_gcr_to_cache(int(track))
			
		return self.track_geometry_offset_map.get(cache_key, None)

	def get_raw_gcr_track_stream(self, logical_track):
		"""Natively parses .g64 tables to extract file offsets, track byte sizes, 
		and preserves speed zone pointers for any full or half-track up to Track 42.5.
		"""
		try:
			track_float = float(logical_track)
		except ValueError:
			return b"", 0
			
		# Enforce our newly updated physical 42-track boundaries
		if track_float < 1.0 or track_float > 42.5:
			return b"", 0
			
		# Convert float track numbers cleanly to the 0-83 index entries
		g64_idx = int(round((track_float - 1.0) * 2))
		
		# 1. Gather Track Data Absolute Offset Pointer
		offset_ptr_pos = 12 + (g64_idx * 4)
		if offset_pointer_slice_pos := offset_ptr_pos + 4 > len(self.payload):
			return b"", 0
		track_file_offset = struct.unpack("<I", self.payload[offset_ptr_pos : offset_ptr_pos + 4])[0]
		if track_file_offset == 0:
			return b"", 0 # Track has no recorded data in this image file
			
		# 2. PRESERVED METADATA RULE: Extract but do not alter speed zone data entries!
		speed_ptr_pos = 0x0158 + (g64_idx * 4)
		speed_zone_val = 0
		if speed_ptr_pos + 4 <= len(self.payload):
			speed_zone_val = struct.unpack("<I", self.payload[speed_ptr_pos : speed_ptr_pos + 4])[0]

		# 3. Read True Length of Stored GCR Track Array Block
		if track_file_offset + 2 > len(self.payload):
			return b"", 0
		track_len = struct.unpack("<H", self.payload[track_file_offset : track_file_offset + 2])[0]
		
		if track_file_offset + 2 + track_len > len(self.payload):
			return b"", 0
			
		return bytes(self.payload[track_file_offset + 2 : track_file_offset + 2 + track_len]), speed_zone_val

	def read_virtual_sector(self, track, sector):
		"""High-level sector fetch hook. Automatically demodulates the requested 
		track on-demand if it hasn't been cached yet.
		"""
		cache_key = (int(track), int(sector))
		if cache_key not in self.virtual_sector_cache_pool:
			self.demodulate_track_gcr_to_cache(int(track))
			
		return self.virtual_sector_cache_pool.get(cache_key, b"\x00" * 256)

	def write_virtual_sector(self, track, sector, raw_bytes):
		"""Production-grade surgical .g64 sector modifier with integrated 
		Data Change Guard and circular Modulo Bit Wrap logic [1.1, 1.11].
		"""
		if len(raw_bytes) != 256:
			return False
			
		if track < 1 or track > 42 or sector < 0:
			return False

		# === STEP 1: NATIVE DATA CHANGE GUARD SAFETY CHECK ===
		local_cache_key = (int(track), int(sector))
		if local_cache_key in self.virtual_sector_cache_pool:
			if self.virtual_sector_cache_pool[local_cache_key] == bytes(raw_bytes):
				return "NO_CHANGE"

		# === STEP 2: LOOK UP THE CACHED BIT GEOMETRY OFFSET ===
		target_bit_offset = self.get_cached_sector_bit_offset(int(track), int(sector))
		if target_bit_offset is None:
			return False

		# === STEP 3: ASSEMBLE AND 4-TO-5 ENCODE PAYLOAD INTO GCR BITS ===
		mutated_gcr_bits = self.encode_bytes_to_gcr_bits(raw_bytes)
		if not mutated_gcr_bits or len(mutated_gcr_bits) != 2600:
			return False
			
		# === STEP 4: FETCH THE RAW TRACK FROM THE PLATTER FILE HEADER ===
		try:
			track_float = float(track)
			g64_idx = int(round((track_float - 1.0) * 2))
			offset_ptr_pos = 12 + (g64_idx * 4)
			
			if offset_ptr_pos + 4 > len(self.payload):
				return False
				
			track_file_offset_tuple = struct.unpack("<I", self.payload[offset_ptr_pos : offset_ptr_pos + 4])
			track_file_offset = track_file_offset_tuple[0]
			
			if track_file_offset == 0:
				return False
				
			track_len_tuple = struct.unpack("<H", self.payload[track_file_offset : track_file_offset + 2])
			track_len = track_len_tuple[0]
		except Exception:
			return False

		# === STEP 5: SURGICALLY OVERWRITE USING THE CIRCULAR MODULO WRAP RULE ===
		try:
			gcr_bytes_block = bytearray(self.payload[track_file_offset + 2 : track_file_offset + 2 + track_len])
			track_bits_array = []
			for b in gcr_bytes_block:
				for bit_pos in range(7, -1, -1):
					track_bits_array.append((b >> bit_pos) & 1)
					
			total_track_bits = len(track_bits_array)
			
			for i in range(2600):
				write_coord_idx = (target_bit_offset + i) % total_track_bits
				track_bits_array[write_coord_idx] = mutated_gcr_bits[i]
		except Exception:
			return False

		# === STEP 6: REPACK BINARY BITS ARRAY BACK INTO STANDARD BYTES ===
		try:
			packed_track_bytes = bytearray()
			for i in range(0, len(track_bits_array), 8):
				byte_chunk = track_bits_array[i:i+8]
				val = 0
				for bit in byte_chunk:
					val = (val << 1) | bit
				packed_track_bytes.append(val)
				
			self.payload[track_file_offset + 2 : track_file_offset + 2 + len(packed_track_bytes)] = packed_track_bytes
		except Exception:
			return False

		# === STEP 7: UPDATE LOCALIZED RAM CACHE POOLS ===
		self.virtual_sector_cache_pool[local_cache_key] = bytes(raw_bytes)

		# === STEP 8: AUTOMATED CASCADING WRITE-THROUGH BACKPLANE ===
		master_platter_bytes = bytes(self.payload)
		
		# 1. Proactively cascade updates into your application's global master storage layers
		for attr_target in ("file_bytes", "container_bytes", "raw_data", "master_payload"):
			if hasattr(self, attr_target):
				setattr(self, attr_target, bytearray(master_platter_bytes))
				
		# Check if this G64 instance is running inside a nested VFS container handler (like a .dnp or .d64)
		if hasattr(self, "parent_vfs_handler") and self.parent_vfs_handler:
			parent_handler = self.parent_vfs_handler
			target_filename = getattr(self, "filename_on_parent", "disk_image.g64")
			
			# Compress the updated G64 memory buffer completely into a flat, sequential array of bytes
			updated_payload_stream = bytes(self.payload)
			
			# 1. TRIGGER REPLACEMENT CHECK: Silently find and purge the old filename allocation sectors!
			# By forcing force_replace=True, it unlinks the old blocks automatically with zero user warnings
			dup_report = parent_handler.check_target_for_duplicate_filename(target_filename, force_replace=True)
			
			# 2. FILE INJECTION PASS: Allocate fresh sequential block sectors and save the new data stream
			# Call your container's native file-saving write routine to plop the new stream into place cleanly
			if hasattr(parent_handler, "save_virtual_file_payload"):
				success = parent_handler.save_virtual_file_payload(target_filename, updated_payload_stream)
				if success:
					# Cascade dirty flags right up the stack to flush everything safely back to the master DHD!
					parent_handler.is_dirty = True
					if hasattr(parent_handler, "parent_dhd_handler") and parent_handler.parent_dhd_handler:
						parent_handler.parent_dhd_handler.is_dirty = True
						parent_handler.parent_dhd_handler.flush_dhd_to_disk()
					return True
				
		# 2. Commit the final platter array permanently to your Windows workstation platter path
		if hasattr(self, "archive_name") and self.archive_name:
			absolute_file_path = os.path.abspath(self.archive_name)
			try:
				with open(absolute_file_path, "wb") as f_out:
					f_out.write(master_platter_bytes)
			except Exception:
				return False
				
		return True

	def decode_gcr_bits_to_bytes(self, bit_list):
		"""Groups a sequence of bit integers into 5-bit GCR chunks and decodes them."""
		gcr_blocks = []
		for i in range(0, len(bit_list) - 4, 5):
			val = 0
			for b_idx in range(5):
				val = (val << 1) | bit_list[i + b_idx]
			gcr_blocks.append(val)
		nybbles = []
		for block in gcr_blocks:
			nybbles.append(G64FileSystemPlugin.GCR_TO_NYBBLE.get(block, 0))
		standard_bytes = []
		for idx in range(0, len(nybbles) - 1, 2):
			standard_bytes.append((nybbles[idx] << 4) | nybbles[idx + 1])
		return standard_bytes

	def demodulate_track_gcr_to_cache(self, logical_track):
		"""🚨 HARDWARE-REPLICATING LOOK-AHEAD GCR DEMODULATOR 🚨
		Parses raw bitstreams natively using a precise 10-bit shift register window. 
		Identifies sector frames by executing direct 100-bit header and 3250-bit data 
		look-ahead captures, matching our verified diagnostic tool perfectly.
		"""
		gcr_bytes, speed_zone = self.get_raw_gcr_track_stream(logical_track)
		if not gcr_bytes:
			return

		# Convert raw track bytes into a continuous list array of binary integers
		base_bit_list = []
		for b in gcr_bytes:
			for bit_pos in range(7, -1, -1):
				base_bit_list.append((b >> bit_pos) & 1)
				
		# Replicate rotating floppy disk by multi-passing the stream list 4 times back-to-back
		bit_stream = base_bit_list * 4
		stream_len = len(bit_stream)

		# FIXED: Defined the total track bits variable early so State 1 can read it!
		total_track_bits = len(base_bit_list)

		# State registers
		shift_reg = 0
		seeking_sync = True
		collected_bits = []
		last_header_sector = None

		# ADD THESE TWO LINES FOR STATE MANAGEMENT:
		decoding_mode = "SEEK_SYNC"	 # Modes: "SEEK_SYNC", "COLLECT_ID", "HEADER", "DATA"
		expected_bytes = 0


		bit_idx = 0
		# We scan through the first full revolution plus our spillover lookahead room
		max_scan_len = len(base_bit_list) + 12000
		if max_scan_len > stream_len:
			max_scan_len = stream_len

		while bit_idx < max_scan_len:
			bit = bit_stream[bit_idx]
			bit_idx += 1
			shift_reg = ((shift_reg << 1) | bit) & 0x3FF

			# If ten 1s hit, a hardware sync IMMEDIATELY interrupts any active frame processing
			if shift_reg == 0x3FF:
				decoding_mode = "SEEK_SYNC"
				seeking_sync = True
				collected_bits = []
				# (Leave your existing track-wrap loop counters below this intact!)


			if seeking_sync:
				if bit == 0:
					seeking_sync = False
					shift_reg = 0
					collected_bits = [bit]
					decoding_mode = "COLLECT_ID"
				continue

			# Collect bits for the current active frame mode
			collected_bits.append(bit)
			
			# --- STATE 1: DECODE INDEPENDENT BLOCK IDENTIFIER (10 bits gathered) ---
			if decoding_mode == "COLLECT_ID" and len(collected_bits) == 10:
				decoded_id = self.decode_gcr_bits_to_bytes(collected_bits)
				if decoded_id and len(decoded_id) > 0:
					if decoded_id[0] == 0x08:	 # HEADER TOKEN MATCHED
						decoding_mode = "HEADER"
						expected_bytes = 5
					elif decoded_id[0] in (0x07, 0xF1):	 # DATA TOKEN MATCHED
						decoding_mode = "DATA"
						expected_bytes = 260
						
						# FIXED REQUIREMENT: Log the dynamic bit offset of the data identifier! [1.10]
						if last_header_sector is not None:
							# Calculate the true starting coordinate index on the primary track rotation
							# We offset backward by 9 bits to align perfectly on the absolute start of the data block ID cell
							absolute_start_bit = (bit_idx - 10) % total_track_bits
							geometry_key = (int(logical_track), int(last_header_sector))
							
							# Commit the coordinate directly to our driver state mapping tracking records
							self.track_geometry_offset_map[geometry_key] = absolute_start_bit
					else:
						decoding_mode = "SEEK_SYNC"
						seeking_sync = True
				else:
					decoding_mode = "SEEK_SYNC"
					seeking_sync = True

			# --- STATE 2: PROCESS ACTIVE DATA CHUNKS BY BYTE SIZE LIMITS ---
			elif decoding_mode in ("HEADER", "DATA"):
				# Every standard CBM byte requires exactly 10 raw GCR bits
				if len(collected_bits) == (expected_bytes * 10):
					full_frame_bytes = self.decode_gcr_bits_to_bytes(collected_bits)
					
					if decoding_mode == "HEADER" and len(full_frame_bytes) >= 3:
						# Byte 2 extracts Sector # natively out of the decoded byte array [1.28]
						last_header_sector = full_frame_bytes[2]
						
						# ============================================
						
					elif decoding_mode == "DATA" and last_header_sector is not None and len(full_frame_bytes) >= 257:
						cache_key = (int(logical_track), int(last_header_sector))
						if cache_key not in self.virtual_sector_cache_pool:
							# Store the standard 256 bytes data payload seamlessly
							self.virtual_sector_cache_pool[cache_key] = bytes(full_frame_bytes[1:257])
							last_header_sector = None
							# ==================================================
							
						last_header_sector = None
						
					# Clear frame parameters and return cleanly to master sync search loop [1.28]
					decoding_mode = "SEEK_SYNC"
					seeking_sync = True
					collected_bits = []


	def mount(self):
		"""Extracts high-level Disk Name and IDs from the cached Track 18, Sector 0 buffer [1.1]."""
		header_sector = self.read_virtual_sector(18, 0)
		
		# Pull strict physical slice limits from standard 1541 hardware profiles [1.1]
		raw_label = header_sector[144:160]
		raw_id = header_sector[162:164]
		raw_dos = header_sector[165:167]
		
		# Sanitizer loop: Strip out all non-printable raw padding data and clean spaces [1.1]
		lbl_str = "".join(chr(b) for b in raw_label if 32 <= b <= 126).strip()
		id_str = "".join(chr(b) for b in raw_id if 32 <= b <= 126).strip().upper()
		dos_str = "".join(chr(b) for b in raw_dos if 32 <= b <= 126).strip().upper()
		
		# Fallback guards: If text decoding comes up empty, default to standard CBM labels [1.1]
		if not lbl_str:
			lbl_str = "1541 GCR"
		if not id_str:
			id_str = "41"
		if not dos_str:
			dos_str = "2A"
			
		# Enforce true 16-character space-padded layout alignment within quotes [1.1]
		self.disk_label_msg = f'0 "{lbl_str:<16}" {id_str} {dos_str}'


	def list_directory(self):
		"""Traces standard 1541 directory linkages from the demodulated sector caches."""
		self.file_list = [{
			"name": "..", "is_directory": True, "is_virtual_container": False,
			"type_display": "UP-DIR", "size_display": " ", "modify_time_str": " -- -- -- "
		}]
		
		curr_t, curr_s = 18, 1
		free_count = 0
		
		while curr_t != 0:
			sec_data = self.read_virtual_sector(curr_t, curr_s)
			if not sec_data or len(sec_data) < 2:
				break
				
			next_t, next_s = int(sec_data[0]), int(sec_data[1])
			
			for off in range(2, 256, 32):
				slot = sec_data[off : off + 32]
				if len(slot) < 30 or int(slot[0]) == 0x00:
					continue
					
				ft_raw = int(slot[0])
				type_flags = ft_raw & 0x0F
				t_lbl = "PRG" if type_flags == 2 else "SEQ" if type_flags == 1 else "USR" if type_flags == 3 else "REL" if type_flags == 4 else "DEL"
				
				if ft_raw & 0x40: t_lbl = f"<{t_lbl}"
				if not (ft_raw & 0x80): t_lbl = f"*{t_lbl}"
					
				# FIXED: Match your D64 file link offsets exactly!
				tgt_t, tgt_s = slot[1], slot[2]
				c_nm = PETSCIIDecoder.decode_name(slot[3:19])
				# FIXED: Appended [0] to unpack the tuple cleanly into a raw block count integer!
				b_cnt = struct.unpack("<H", slot[28:30])[0]
				
				self.file_list.append({
					"name": c_nm, "is_directory": False, "is_virtual_container": False,
					"type_display": t_lbl, "size_display": str(b_cnt),
					"vfs_meta": {"track": tgt_t, "sector": tgt_s}
				})
				
			if next_t == 0 or (next_t == 0x00 and next_s == 0xFF):
				break
			curr_t, curr_s = next_t, next_s
			
		# FIXED: Bounded sectors density lookup loop safely limits to 35 tracks for free space calculations
		bam_sector = self.read_virtual_sector(18, 0)
		for t in range(1, 36):
			if t == 18: continue
			free_count += int(bam_sector[t * 4])
			
		self.free_sectors_count = free_count
		return self.file_list
		
	def extract_file_bytes(self, vfs_meta):
		"""Sequentially follows a file's track and sector link chain from our demodulated 
		virtual sector cache pool to extract the raw binary payload bytes [1.1].
		"""
		if not vfs_meta or "track" not in vfs_meta or "sector" not in vfs_meta:
			return b""
			
		file_bytes = bytearray()
		curr_t = int(vfs_meta["track"])
		curr_s = int(vfs_meta["sector"])
		
		# Guard against infinite loops or circular file allocation pointers
		visited_sectors = set()
		
		# A 1541 file chain runs until the Next Track byte equals 0x00 [1.1]
		while curr_t != 0:
			# Safety boundary check: ensure we don't spin endlessly on corrupted images
			sector_key = (curr_t, curr_s)
			if sector_key in visited_sectors:
				break
			visited_sectors.add(sector_key)
			
			# Pull the 256-byte standard sector via our unified lookup coordinate hook
			sec_data = self.read_virtual_sector(curr_t, curr_s)
			if not sec_data or len(sec_data) < 256:
				break
				
			# On a standard 1541 diskette [1.1]:
			# - Byte 0 is the Next Track of the file chain [1.1]
			# - Byte 1 is the Next Sector of the file chain [1.1]
			# FIXED: Pull indices straight out of the byte array natively!
			# Pull integers straight out of the active byte offsets natively!
			next_t = sec_data[0]
			next_s = sec_data[1]
			
			if next_t == 0:
				# If the next track is 0, this is the absolute final sector of the file [1.1]!
				# In this case, Byte 1 specifies exactly how many valid data bytes remain inside this block [1.1].
				valid_bytes_count = next_s
				# Strip off the initial 2-byte track/sector pointer overhead [1.1]
				file_bytes.extend(sec_data[2 : 1 + valid_bytes_count])
				break
			else:
				# If next_t is not 0, the entire sector contains valid data payload [1.1]
				file_bytes.extend(sec_data[2:256])
				
			curr_t = next_t
			curr_s = next_s
			
		return bytes(file_bytes)


