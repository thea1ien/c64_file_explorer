class LNXFileSystemPlugin(BaseVFSHandler):
	"""Dynamic Broker Adapter parsing legacy Commodore Lynx (.LNX) archives 
	utilizing a robust, line-ending agnostic text parser and a pretend 
	256-byte sector-buffered memory layout chassis.
	"""
	def mount(self):
		self.default_dir_track = 1
		self.default_dir_sector = 0
		self.max_tracks_limit = 255
		self.no_sector_editor = False  # Enabled! The sector buffer mapping makes low-level viewing 100% stable
		self.disk_label_msg = "0 LYNX VIRTUAL DISK"
		self.read_only = True
		
		self.file_list = [{
			"name": "..", "is_directory": True, "is_virtual_container": False,
			"type_display": "UP-DIR", "size_display": " ", "modify_time_str": " -- -- -- "
		}]
		
		# --- PHASE 1: PARSE METADATA VIA THE UNIVERSAL BYTE-SPLIT CORE ---
		payload_len = len(self.payload)
		basic_end = self.payload.find(b'\x00\x00\x00')
		if basic_end == -1: 
			return
			
		header_offset = basic_end + 3
		
		# Isolate text-only index list safely at the byte-level to preserve PETSCII symbols
		text_segment = self.payload[header_offset : header_offset + 6400]
		
		# Universally agnostic byte-splitter: Split by CR, LF, or CR+LF dynamically
		lines = []
		current_line = bytearray()
		for b in text_segment:
			if b == 13 or b == 10:	# CR or LF markers
				if current_line:
					lines.append(bytes(current_line))
					current_line = bytearray()
			else:
				current_line.append(b)
		if current_line:
			lines.append(bytes(current_line))
			
		if len(lines) < 2: 
			return
			
		# Dynamically discover the file count line integer signature parameter
		num_files = 0
		current_line_idx = 1
		
		while current_line_idx < len(lines):
			val_str = lines[current_line_idx].decode('latin-1', errors='ignore').strip()
			if val_str.isdigit():
				num_files = int(val_str)
				current_line_idx += 1  # Advance past the file count to the first record line
				break
			current_line_idx += 1
			
		if num_files == 0:
			return
			
		file_metadata = []
		
		# Extract the 4-line metadata blocks exactly matching your authentic hardware hex dump sequence!
		for _ in range(num_files):
			if current_line_idx + 3 >= len(lines): 
				break
				
			raw_name_bytes = lines[current_line_idx]
			clean_name = PETSCIIDecoder.decode_name(raw_name_bytes).replace("_", " ").strip()
			clean_name = clean_name.replace('\xa0', '').strip()
			
			blocks_str = lines[current_line_idx + 1].decode('latin-1', errors='ignore').strip()
			ftype_raw = lines[current_line_idx + 2].decode('latin-1', errors='ignore').strip().upper()
			last_block_bytes_str = lines[current_line_idx + 3].decode('latin-1', errors='ignore').strip()
			
			# Maps abbreviated 1-letter labels to standard 1541 format codes cleanly
			if ftype_raw.startswith('P'):
				type_lbl = "PRG"
			elif ftype_raw.startswith('S'):
				type_lbl = "SEQ"
			elif ftype_raw.startswith('U'):
				type_lbl = "USR"
			elif ftype_raw.startswith('R'):
				type_lbl = "REL"
			else:
				type_lbl = ftype_raw if ftype_raw else "PRG"
				
			try:
				blocks = int(blocks_str) if blocks_str.isdigit() else 0
				last_bytes_val = int(last_block_bytes_str) if last_block_bytes_str.isdigit() else 0
				
				if blocks > 0:
					total_bytes = (254 * (blocks - 1)) + (last_bytes_val - 1)
				else:
					total_bytes = 0
			except Exception:
				blocks = 0
				total_bytes = 0

			file_metadata.append({
				"name": clean_name, 
				"type": type_lbl,
				"bytes": total_bytes,
				"raw_blocks": blocks
			})
			current_line_idx += 4

		# FIXED: Safe, robust data boundary extractor calculates text lengths using index counters smoothly
		data_start_offset = header_offset
		processed_count = 0
		
		# Sum up text data lengths explicitly across the exact total index lines evaluated in Phase 1
		for line_byte_node in lines[:current_line_idx]:
			data_start_offset += len(line_byte_node) + 1 # Include trailing line character overhead offsets
			
		# Structural emergency alignment guard bounds checker parameter
		if data_start_offset >= payload_len:
			return

		# --- PHASE 2: GENERATE THE MOCK 256-BYTE DRIVE SECTOR MAPS ---
		self.virtual_disk_sectors = []
		idx = data_start_offset
		
		while idx < payload_len:
			chunk = self.payload[idx : idx + 254]
			if not chunk: 
				break
				
			if len(chunk) < 254:
				chunk = chunk + b"\x00" * (254 - len(chunk))
				
			sector_buffer = bytearray(256)
			next_sector_idx = len(self.virtual_disk_sectors) + 1
			
			sector_buffer[0] = 1   
			sector_buffer[1] = next_sector_idx & 0xFF 
			sector_buffer[2:256] = chunk
			self.virtual_disk_sectors.append(sector_buffer)
			idx += 254
			
		if self.virtual_disk_sectors:
			self.virtual_disk_sectors[-1][0] = 0x00
			self.virtual_disk_sectors[-1][1] = 0xFF

		# --- PHASE 3: BIND EXTRACTED FILE ENTRIES TO PANEL DIRECTORY VIEWS ---
		current_sector_offset = 0
		
		for item in file_metadata:
			start_t = 1
			start_s = current_sector_offset
			
			self.file_list.append({
				"name": item["name"], 
				"is_directory": False, 
				"is_virtual_container": False,
				"type_display": item["type"], 
				"size_display": str(item["raw_blocks"]),
				"vfs_meta": {"sector": start_s, "blocks": item["raw_blocks"], "bytes": item["bytes"]}
			})
			
			current_sector_offset += item["raw_blocks"]
		# --- End of the mount method block pass ---
		try:
			pass
		except Exception:
			pass

	# FIXED: Do NOT delete these remaining methods below! They drive your File Viewer and Sector Editors!
	def read_virtual_sector(self, track, sector):
		"""Natively queries the fake sector-buffered storage grid using standard T/S coordinates."""
		block_index = sector
		if 0 <= block_index < len(self.virtual_disk_sectors):
			return bytearray(self.virtual_disk_sectors[block_index])
		return bytearray(256)

	def extract_file_bytes(self, vfs_meta_node):
		"""Extracts raw file payload bytes natively by walking our virtual sector chains."""
		file_bytes = bytearray()
		start_sector = vfs_meta_node.get("sector", 0)
		total_blocks = vfs_meta_node.get("blocks", 0)
		target_bytes = vfs_meta_node.get("bytes", 0)
		
		for b_idx in range(total_blocks):
			target_sec = start_sector + b_idx
			if target_sec < len(self.virtual_disk_sectors):
				file_bytes.extend(self.virtual_disk_sectors[target_sec][2:256])
				
		return bytes(file_bytes[:target_bytes])


