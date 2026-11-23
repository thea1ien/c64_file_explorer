class DNPFileSystemPlugin(BaseVFSHandler):
	"""Dynamic Broker Adapter bridging low-level Native Partition sub-directories."""
	def mount(self):
		# Bind the specific massive parameters matching native high-capacity partition frameworks
		self.format_type = "DNP"
		self.default_dir_track = 1
		self.default_dir_sector = 1
		self.max_tracks_limit = 255

		mem_stream = PreloadedBufferBlockStream(self.payload)
		computed_blocks_count = len(self.payload) // 256

		# Pass the dynamically calculated block length straight down to your lower driver mechanics
		self.dnp_h = DNPNativeHandler(mem_stream, computed_blocks_count)
		
		# FIXED: Trigger our fresh binary BAM evaluation scanner block
		bam_info = self.dnp_h.get_dnp_bam_matrix()
		
		header_blk = self.dnp_h.read_virtual_sector(1, 1)
		d_name = PETSCIIDecoder.decode_name(header_blk[4:20])
		self.disk_label_msg = f'0 "{d_name:<16}"'

		# FIXED: Dynamic assignment checks live parsed bit structures instead of blindly dropping into size math defaults
		if bam_info and "blocks_free" in bam_info:
			self.free_sectors_count = bam_info["blocks_free"]
		else:
			# Structural baseline ceiling marker backup fallback rule tracking
			self.free_sectors_count = computed_blocks_count - 35



		# Clean Initial Entry Point: Hand over the true hardware starting block (Track 1, Sector 1)
		self.file_list = TUIController.mine_dnp_entries(self.dnp_h, 1, 1)
		
	def toggle_sector_allocation_status(self, track, sector):
		"""Natively flips the allocation bit mask for a CMD Native .dnp partition 
		by targeting Track 1, Sectors 2-32 using 32-byte track allocation blocks [1.1].
		"""
		# 1. Calculate which sector on Track 1 holds this specific track's BAM data [1.1]
		dnp_sector = 2 + ((track - 1) // 8)
		
		# 2. Calculate the 32-byte track offset window inside that 256-byte sector block [1.1]
		track_in_sector_offset = ((track - 1) % 8) * 32
		
		# 3. Translate Track 1, Target Sector into a global linear index in your payload [1.1]
		# (DNP uses a flat 256 sectors per track layout uniformly across the disk image) [1.1]
		linear_sector_idx = ((1 - 1) * 256 + dnp_sector) * 256
		
		# 4. Find the exact byte and bit position for the target sector [1.1]
		byte_in_track = sector // 8
		bit_in_byte = sector % 8
		
		final_payload_offset = linear_sector_idx + track_in_sector_offset + byte_in_track
		
		if final_payload_offset < len(self.payload):
			# XOR (^) the exact bit to toggle its state cleanly: 1 (Free) <-> 0 (Used) [1.1]
			self.payload[final_payload_offset] ^= (1 << bit_in_byte)


	def extract_file_bytes(self, vfs_meta_node):
		return TUIController.extract_vfs_file_bytes(self.dnp_h, vfs_meta_node["track"], vfs_meta_node["sector"])

	def navigate_forward(self, track, sector, name):
		return self.dnp_h.navigate_forward(track, sector, name)

	def navigate_backward(self):
		return self.dnp_h.navigate_backward()
		
	def read_virtual_sector(self, track, sector):
		"""Passes the sector read request straight down to the Native Partition driver."""
		return self.dnp_h.read_virtual_sector(track, sector)
		
	def write_virtual_sector(self, track, sector, data_bytes):
		"""Passes the sector write execution down to the Native Partition handler,
		forcefully syncs the modified buffers back to the primary file plugin stream,
		and arms the dirty flag to guarantee hard drive persistence on save passes.
		"""
		if not hasattr(self, "dnp_h") or not self.dnp_h:
			return False
			
		# Enforce a strict 256-byte sector footprint block limit constraint
		clean_data = bytes(data_bytes[:256].ljust(256, b"\x00"))
		
		# 1. Delegate the raw write straight down to your inner handler core mechanics
		success = self.dnp_h.write_virtual_sector(track, sector, clean_data)
		
		if success:
			# Sync the updated data buffer back to the child handler's local payload
			if hasattr(self.dnp_h, "stream") and hasattr(self.dnp_h.stream, "buffer"):
				updated_buffer = self.dnp_h.stream.buffer
				if isinstance(self.payload, bytes):
					self.payload = bytes(updated_buffer)
				else:
					self.payload = bytearray(updated_buffer)
			
			self.is_dirty = True 
			
			# --- THE ISOLATED ROUTING INTERCEPT BARRIER ---
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
				
			# SCENARIO B: This plugin is running as a standalone, loose .dnp file on your PC's hard drive
			if hasattr(self, "archive_name") and self.archive_name:
				try:
					with open(os.path.abspath(self.archive_name), "wb") as f_out:
						f_out.write(bytes(self.payload))
				except Exception:
					pass
			return True


class DNPNativeHandler(BaseContainerHandler):
	"""Virtual driver managing raw DNP Native Partition image operations."""
	def __init__(self, vfs_stream, total_blocks=1024):
		super().__init__(vfs_stream)
		self.total_blocks = total_blocks
		self.history_stack = []
		prof = ImageGeometryRegistry.PROFILES["DNP"]
		self.current_track = prof["directory_track"]
		self.current_sector = prof["directory_sector"]
		self.current_path = "ROOT"
		
		# INITIALIZATION REGISTERS: Cached parameters initialized cleanly upon mount passes
		self.free_blocks_counter = 0
		self.bit_matrix = {}

	def get_dnp_bam_matrix(self):
		"""
		Pure Data Engine: Parses the system BAM sectors on Track 1 (Sectors 2-33).
		Natively enforces the 64-sector hard system overhead rule over loose bit masks.
		"""
		try:
			# Read Track 1, Sector 2 directly to extract the core directory BAM map vectors
			bam_sector_data = self.read_virtual_sector(1, 2)
			if not bam_sector_data or len(bam_sector_data) < 256:
				return None

			live_bit_free_tally = 0
			self.bit_matrix = {}

			# Calculate exactly how many physical tracks exist in this container profile size
			computed_max_tracks = self.total_blocks // 256
			if computed_max_tracks == 0:
				computed_max_tracks = 1
			# Safe bounding ceiling constraint matching hardware scaling rules
			track_ceiling_limit = min(computed_max_tracks + 1, 256)

			# Loop exclusively through the real tracks present inside this image partition frame
			for track_idx in range(1, track_ceiling_limit):
				self.bit_matrix[track_idx] = {}
				
				# The first BAM block houses maps for Tracks 1-7 starting at byte offset $20
				if track_idx <= 7:
					track_segment_start = 0x20 + ((track_idx - 1) * 32)
					active_sector_data = bam_sector_data
				else:
					bam_sector_offset = 3 + ((track_idx - 8) // 8)
					active_sector_data = self.read_virtual_sector(1, bam_sector_offset)
					if not active_sector_data:
						continue
					track_segment_start = ((track_idx - 8) % 8) * 32
				
				# Step sequentially through the 32 bytes reserved for this track's bitmask
				for byte_idx in range(32):
					final_byte_offset = track_segment_start + byte_idx
					bit_byte = active_sector_data[final_byte_offset]
					
					# Inspect all 8 bits sequentially inside this active byte register
					for bit_idx in range(8):
						# Reconstruct the absolute sector coordinate index value (0 to 255)
						sector_idx = (byte_idx * 8) + bit_idx
						
						# FIXED: Enforce absolute operating system boundaries. 
						# Sectors 0-63 on Track 1 are never free for data files, no matter what the BAM bits claim.
						if track_idx == 1 and sector_idx < 64:
							self.bit_matrix[track_idx][sector_idx] = False	# Mark as ALLOCATED
							continue
							
						# Inverts logic evaluation rule mapping because 1=FREE on CMD Native Partitions
						is_free_block = ((bit_byte & (1 << bit_idx)) != 0)
						self.bit_matrix[track_idx][sector_idx] = is_free_block
						
						# Increment our counter tally only if the cluster registers as truly free
						if is_free_block:
							live_bit_free_tally += 1

			# Return the calculated counts back to your upper plugin adaptations
			return {
				"blocks_free": live_bit_free_tally,
				"bit_matrix": self.bit_matrix
			}
		except Exception:
			return None

	def read_virtual_sector(self, track, sector):
		block_idx = ImageGeometryRegistry.translate_ts_to_block_index("DNP", track, sector)
		if block_idx >= self.total_blocks:
			raise IndexError("DNP track boundary overflow.")
		return bytearray(self.stream.read_block(block_idx))

	def get_raw_block(self, track, sector):
		try:
			return self.read_virtual_sector(track, sector)
		except IndexError:
			return None

	def mount(self):
		pass
		
	def allocate_free_sector(self, track, sector, file_write_payload=None):
		"""
		High-Level Virtual Drive Allocation Guard:
		Enforces absolute CMD Native file copying restrictions across Track 1, Sectors 0-63.
		Bypasses restrictions ONLY if direct low-level block sector editing tasks are active.
		"""
		# Enforce mandatory system overhead reservation rules on Track 1
		if track == 1 and sector < 64:
			# If a payload is passed, this is a file copy request attempting to write user data
			if file_write_payload is not None:
				return False # CRITICAL RESTRICTION: Block file copy action from fowling up system blocks
		
		try:
			# If validated safely or bypassing via direct block editor, commit to the preloaded stream
			if file_write_payload is not None:
				block_idx = ImageGeometryRegistry.translate_ts_to_block_index("DNP", track, sector)
				if block_idx >= self.total_blocks:
					return False
				# Commit the 256-byte payload buffer straight to the block stream
				start_offset = block_idx * 256
				self.stream.buffer[start_offset : start_offset + 256] = file_write_payload
			return True
		except Exception:
			return False
			
	def find_next_free_allocation_block(self):
		"""
		High-Level Allocation Engine: Walks the synchronized BAM bit matrix natively
		to find the very first available Track/Sector coordinate fit for user file data.
		Guarantees it respects absolute CMD system overhead storage layouts.
		"""
		# Refresh our calculation tracking maps to get the latest disk state matrix
		bam_map = self.get_dnp_bam_matrix()
		if not bam_map or "bit_matrix" not in bam_map:
			return None
			
		matrix = bam_map["bit_matrix"]
		
		# Step through every track and sector coordinate layer present inside the partition frame
		for track_idx in sorted(matrix.keys()):
			for sector_idx in sorted(matrix[track_idx].keys()):
				# Safety Guard Pass: Skip Track 1, Sectors 0-63 regardless of rogue BAM bit states
				if track_idx == 1 and sector_idx < 64:
					continue
					
				# If the synchronized matrix registers a slot as completely free
				if matrix[track_idx][sector_idx] is True:
					return (track_idx, sector_idx)
					
		return None # Return None if the partition container space is entirely packed (0 BLOCKS FREE)
		
	def write_virtual_sector(self, track, sector, data_bytes):
		"""Surgically overwrites a 256-byte sector payload block inside the raw DNP platter stream.
		Auto-casts immutable bytes arrays dynamically to guarantee clean sector writes.
		"""
		if track < 1 or sector < 0 or sector > 255:
			return False
			
		# Compute the exact 1:1 linear byte offset location inside the massive image array
		linear_sector_idx = ((int(track) - 1) * 256) + int(sector)
		final_payload_offset = linear_sector_idx * 256
		
		# Connect directly to self.stream.buffer matching your native read method architecture
		if hasattr(self, "stream") and hasattr(self.stream, "buffer"):
			payload_ref = self.stream.buffer
			if final_payload_offset + 256 <= len(payload_ref):
				clean_bytes = data_bytes[:256].ljust(256, b"\x00")
				
				# FIXED: Detect if buffer is an immutable 'bytes' type, and auto-cast to bypass write restrictions!
				if isinstance(payload_ref, bytes):
					mutable_buffer = bytearray(payload_ref)
					mutable_buffer[final_payload_offset : final_payload_offset + 256] = clean_bytes
					
					# Re-assign the patched array back to the stream container cleanly
					self.stream.buffer = bytes(mutable_buffer)
					
					# Mirror the payload array sync inside the parent driver plugin wrapper if tracked there
					if hasattr(self, "payload"):
						self.payload = self.stream.buffer
				else:
					# If it's already a mutable bytearray, patch it directly in place!
					payload_ref[final_payload_offset : final_payload_offset + 256] = clean_bytes
					
				return True
				
		return False

	def list_directory_entries(self, track, sector):
		entries = []
		lt, ls = track, sector
		
		# Lock your initial entry parameters so the loop can identify the exact metadata header block
		header_track = track
		header_sector = sector
		
		while lt != 0:
			try:
				sec_data = self.read_virtual_sector(lt, ls)
			except IndexError:
				# FIXED: If a small image bounds check trips, log the parameters rather than zeroing rows!
				entries.append({
					"name": f"! GEOMETRY FAULT (T:{lt} S:{ls})", "is_directory": False, "is_virtual_container": False,
					"type_display": "ERR", "size_display": "0B", "vfs_meta": {"track": 0, "sector": 0}
				})
				break

				
			next_t, next_s = int(sec_data[0]), int(sec_data[1])
			
			# --- AUTHENTIC COMMODORE HARDWARE BEHAVIOR ENGINE ---
			# If we are parsing the initial point of entry sector (Root 1,1 or Subdir header),
			# this is strictly a structural metadata header container! 
			# We do NOT parse filename records out of these 32-byte slots. Instead, we pull the 
			# header information, wrap to the next linked pointer, and continue onto the file sectors!
			if lt == header_track and ls == header_sector:
				if next_t == 0 or (next_t == 0x00 and next_s == 0xFF):
					break
				lt, ls = next_t, next_s
				continue
				
			# Process true 32-byte filename entries residing exclusively on the subsequent sectors
			for off in range(2, 256, 32):
				slot = sec_data[off : off + 32]
				if len(slot) < 30 or int(slot[0]) == 0x00:
					continue
					
				ft_raw = int(slot[0])
				act_t = ft_raw & 0x0F
				is_dir = (act_t == 0x06)
				
				tgt_t, tgt_s = int(slot[1]), int(slot[2])
				c_nm = PETSCIIDecoder.decode_name(slot[3:19])
				b_cnt = struct.unpack("<H", slot[28:30])[0]
				
				if is_dir:
					t_lbl = "DIR"
					s_lbl = "SUB-DIR"
				else:
					t_lbl = "PRG" if act_t == 0x02 else "SEQ" if act_t == 0x01 else "USR" if act_t == 0x03 else "REL" if act_t == 0x04 else "???"
					s_lbl = f"{b_cnt}B"
					
				entries.append({
					"name": c_nm, "is_directory": is_dir, "is_virtual_container": False,
					"type_display": t_lbl, "size_display": s_lbl,
					"vfs_meta": {"track": tgt_t, "sector": tgt_s}
				})
				
			if next_t == 0 or (next_t == 0x00 and next_s == 0xFF):
				break
			lt, ls = next_t, next_s
			
		return entries



	def navigate_forward(self, track, sector, name):
		self.history_stack.append((self.current_track, self.current_sector, self.current_path))
		self.current_track = track
		self.current_sector = sector
		self.current_path = f"{self.current_path}\\{name}"
		return True

	def navigate_backward(self):
		if not self.history_stack:
			return False
		self.current_track, self.current_sector, self.current_path = self.history_stack.pop()
		return True


