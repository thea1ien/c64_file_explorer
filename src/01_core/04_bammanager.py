class BAMManager:
	"""Centralized Abstract allocation manager that decodes, caches, modifies, and 
	re-encodes Block Availability Map (BAM) hex byte streams uniformly across 
	all Commodore virtual filesystems (.d64, .d71, .d81, .lnx, .dnp) [1.1].
	"""
	def __init__(self, driver_instance, bam_track=None):
		self.driver = driver_instance
		
		# FIXED: Streamlined fallback guard! If it's a D81, initialize our partition tracker.
		# Any other file system bypasses this completely and continues exactly as it did before! [1.13]
		if driver_instance and getattr(driver_instance, "format_type", "") == "D81":
			self.bam_track = getattr(driver_instance, "current_dir_track", 40) if bam_track is None else int(bam_track)
			
		self.params = self._generate_bam_parameters()
		
		# Core multi-tier tracking registers
		self.grid = {}			  # The active, live editable modifications buffer
		self.historical_copy = {} # An untouched backup snapshot of the raw disk state
		
		# Boot up and instantiate the data tables immediately on session creation
		self.load_bam_from_disk()
		

	def _generate_bam_parameters(self):
		"""Fact-aligned hardware layout profiles mapping exact byte limits 
		and track descriptor bounds across all platform formats natively.
		"""
		if not self.driver:
			return None
			
		class_name = self.driver.__class__.__name__.upper()
		
		# --- PROFILE A: CMD NATIVE PARTITIONS (.DNP) ---
		if "DNP" in class_name:
			payload_len = len(getattr(self.driver, "payload", b""))
			dnp_max_tracks = payload_len // 65536
			
			if dnp_max_tracks < 1:
				dnp_max_tracks = 1	# Minimum safety boundary fallback
				
			# Generate the track configuration index maps first
			track_configs = {}
			max_sec_idx_found = 0
			for t in range(1, dnp_max_tracks + 1):
				# Calculate the precise continuous byte offset starting past the 32-byte header overhead
				global_byte_offset = ((t - 1) * 32) + 32
				sec_idx = global_byte_offset // 256
				rel_byte = global_byte_offset % 256
				
				track_configs[t] = (sec_idx, rel_byte, 32, False)
				if sec_idx > max_sec_idx_found:
					max_sec_idx_found = sec_idx
					
			# FIXED: Dynamically build source_sectors by reading exactly how many sectors 
			# are required by the track configuration map, eliminating any boundary mismatch risks!
			num_sectors_needed = max_sec_idx_found + 1
			source_sectors = [(1, 2 + s) for s in range(num_sectors_needed)]
				
			return {
				"format_type": "DNP",
				"max_tracks": dnp_max_tracks,
				"sector_map": {t: 256 for t in range(1, dnp_max_tracks + 1)},
				"bam_layout_type": "PURE_MASK",
				"reverse_bit_direction": True,
				"source_sectors": source_sectors,
				"track_configs": track_configs
			}
			
		# --- PROFILE B: HIGH-DENSITY 1581 DRIVES (.D81) ---
		max_t = getattr(self.driver, "max_tracks_limit", 35)
		if "D81" in class_name or max_t == 80:
			# FIXED: Pulls the target BAM track dynamically from self.bam_track instead of hardcoded 40! [1.13]
			target_track = getattr(self, "bam_track", 40)
			
			return {
				"format_type": "D81",
				"max_tracks": 80,
				"sector_map": {t: 40 for t in range(1, 81)},
				"bam_layout_type": "COUNTER_MASK",
				"source_sectors": [(target_track, 1), (target_track, 2)], # Dynamically routes to the partition track [1.13]
				"track_configs": {
					**{t: (0, 16 + ((t - 1) * 6), 6, True) for t in range(1, 41)},
					**{t: (1, 16 + ((t - 41) * 6), 6, True) for t in range(41, 81)}
				}
			}
			
		# --- PROFILE C: DUAL-SIDED 1571 DRIVES (.D71) ---
		elif "D71" in class_name or max_t == 70:
			return {
				"format_type": "D71",
				"max_tracks": 70,
				"sector_map": {
					**{t: (21 if t<=17 else 19 if t<=24 else 18 if t<=30 else 17) for t in range(1, 36)},
					**{t: (21 if (t-35)<=17 else 19 if (t-35)<=24 else 18 if (t-35)<=30 else 17) for t in range(36, 71)}
				},
				"bam_layout_type": "SPLIT_1571",
				"source_sectors": [(18, 0), (53, 0)],
				"side1_summary_offset": 221,
				"track_configs": {
					**{t: (0, 4 + ((t - 1) * 4), 4, True) for t in range(1, 36)},
					**{t: (1, (t - 36) * 3, 3, False) for t in range(36, 71)}
				}
			}
			
		# --- DEFAULT PROFILE D: STANDARD 1541 DRIVES (.D64) ---
		else:
			return {
				"format_type": "D64",
				"max_tracks": 35,
				"sector_map": {t: (21 if t<=17 else 19 if t<=24 else 18 if t<=30 else 17) for t in range(1, 36)},
				"bam_layout_type": "COUNTER_MASK",
				"source_sectors": [(18, 0)],
				"track_configs": {
					t: (0, 4 + ((t - 1) * 4), 4, True) for t in range(1, 36)
				}
			}

	def load_bam_from_disk(self):
		"""Commands driver to read raw BAM sectors and decodes their allocation masks.
		Fully fault-tolerant with active index guards to handle any disk sector spillover.
		"""
		if not self.params or not self.driver:
			return
			
		self.sector_buffers = []
		for (t, s) in self.params["source_sectors"]:
			raw_data = self.driver.read_virtual_sector(t, s)
			if raw_data:
				self.sector_buffers.append(bytearray(raw_data))
			else:
				self.sector_buffers.append(bytearray(256))
			
		rev_direction = self.params.get("reverse_bit_direction", False)
			
		for t in range(1, self.params["max_tracks"] + 1):
			self.grid[t] = {}
			self.historical_copy[t] = {}
			
			max_s = self.params["sector_map"].get(t, 21)
			cfg = self.params["track_configs"].get(t)
			if not cfg:
				continue
				
			sec_idx, start_byte, total_bytes, has_counter = cfg
			
			# FIXED: Restored the structural index guard! Prevents list out of range crashes 
			# by routing empty or truncated track definitions to a safe fallback layout buffer.
			if sec_idx >= len(self.sector_buffers):
				buf = bytearray(256)
			else:
				buf = self.sector_buffers[sec_idx]
			
			mask_start_byte = start_byte + 1 if has_counter else start_byte
			
			for s in range(max_s):
				byte_offset = mask_start_byte + (s // 8)
				
				if rev_direction:
					bit_position = 7 - (s % 8)
				else:
					bit_position = s % 8
				
				if byte_offset < len(buf):
					is_free = bool(buf[byte_offset] & (1 << bit_position))
				else:
					is_free = True
					
				self.grid[t][s] = is_free
				self.historical_copy[t][s] = is_free

	def flush_bam_changes_to_media(self):
		"""Compiles the in-memory working bit grid maps back into accurate hardware hex 
		byte data payloads, preserving format-specific bit directions cleanly [1.1].
		"""
		if not self.params or not self.driver:
			return False
			
		fmt = self.params["format_type"]
		rev_direction = self.params.get("reverse_bit_direction", False)
		
		for t in range(1, self.params["max_tracks"] + 1):
			cfg = self.params["track_configs"].get(t)
			if not cfg:
				continue
				
			sec_idx, start_byte, total_bytes, has_counter = cfg
			buf = self.sector_buffers[sec_idx]
			max_s = self.params["sector_map"].get(t, 21)
			
			mask_start = start_byte + 1 if has_counter else start_byte
			mask_len = total_bytes - 1 if has_counter else total_bytes
			
			# Clear old byte values to prepare for re-packing
			for offset in range(mask_len):
				if (mask_start + offset) < len(buf):
					buf[mask_start + offset] = 0x00
				
			# Pack bits back down into bytes
			track_free_count = 0
			for s in range(max_s):
				is_free = self.grid[t][s]
				if is_free:
					track_free_count += 1
					byte_offset = mask_start + (s // 8)
					
					# FIXED: Apply identical directional packing logic when saving back to media! [1.1]
					if rev_direction:
						bit_pos = 7 - (s % 8)
					else:
						bit_pos = s % 8
						
					if byte_offset < len(buf):
						buf[byte_offset] |= (1 << bit_pos)
					
			if has_counter and start_byte < len(buf):
				buf[start_byte] = track_free_count

		if fmt == "D71" and "side1_summary_offset" in self.params:
			summary_start = self.params["side1_summary_offset"]
			buf_s0 = self.sector_buffers
			for t_side1 in range(36, 71):
				s1_track_free = sum(1 for s in range(self.params["sector_map"][t_side1]) if self.grid[t_side1][s])
				cache_byte_idx = summary_start + (t_side1 - 36)
				if cache_byte_idx < len(buf_s0):
					buf_s0[cache_byte_idx] = s1_track_free

		for idx, (t, s) in enumerate(self.params["source_sectors"]):
			self.driver.write_virtual_sector(t, s, bytes(self.sector_buffers[idx]))
			
		for t in range(1, self.params["max_tracks"] + 1):
			for s in range(self.params["sector_map"].get(t, 0)):
				self.historical_copy[t][s] = self.grid[t][s]
				
		return True

	def check_sector_status(self, track, sector):
		"""Returns the live buffered state of a sector cell: True = Free, False = Used."""
		return self.grid.get(track, {}).get(sector, True)

	def toggle_sector(self, track, sector):
		"""Flips the buffer allocation state of a specific coordinate cell natively."""
		if track in self.grid and sector in self.grid[track]:
			self.grid[track][sector] = not self.grid[track][sector]

	def allocate_sector(self, track, sector):
		"""Explicitly marks a block as used (False). Vital for future file save engines!"""
		if track in self.grid and sector in self.grid[track]:
			self.grid[track][sector] = False

	def free_sector(self, track, sector):
		"""Explicitly marks a block as free (True). Vital for future delete routines!"""
		if track in self.grid and sector in self.grid[track]:
			self.grid[track][sector] = True

	def count_free_blocks(self, use_historical=False):
		"""Natively scans the bit grid tables to calculate live or historical sector totals.
		Enforces strict hardware directory and system overhead exclusions across ALL drive 
		formats (.d64, .d71, .d81, .dnp) so editing system tracks never alters the block count.
		"""
		total = 0
		target_matrix = self.historical_copy if use_historical else self.grid
		fmt = self.params["format_type"]
		
		for t in range(1, self.params["max_tracks"] + 1):
			# --- HARDWARE CONSTRAINT: STANDARD CBM SYSTEM TRACK EXCLUSIONS ---
			# Track 18 is the directory track for 1541/1571 Side 0.
			# Track 53 is the directory/BAM continuation track for 1571 Side 1.
			# Track 40 is the exact center directory track for 1581 drives.
			# Skipping these guarantees that editing system maps won't fluctuate user free space!
			if fmt == "D64" and t == 18:
				continue
			if fmt == "D71" and t in (18, 53):
				continue
			if fmt == "D81" and t == 40:
				continue
				
			max_s = self.params["sector_map"].get(t, 0)
			for s in range(max_s):
				# --- HARDWARE CONSTRAINT: CMD NATIVE DISK DIRECTORY TAX ---
				# CMD Native partitions permanently reserve the first 64 sectors (S0-S63) of Track 1.
				if fmt == "DNP" and t == 1 and s < 64:
					continue
					
				if target_matrix.get(t, {}).get(s, True):
					total += 1
					
		return total

	def flush_bam_changes_to_media(self):
		"""Compiles the in-memory working bit grid maps back into accurate hardware hex 
		byte data payloads and instructs driver to write changes permanently to disk images [1.1].
		"""
		if not self.params or not self.driver:
			return False
			
		fmt = self.params["format_type"]
		
		# Step 1: Re-encode track allocations row-by-row based on configuration models
		for t in range(1, self.params["max_tracks"] + 1):
			cfg = self.params["track_configs"].get(t)
			if not cfg:
				continue
				
			sec_idx, start_byte, total_bytes, has_counter = cfg
			buf = self.sector_buffers[sec_idx]
			max_s = self.params["sector_map"].get(t, 21)
			
			# 1. Clear out the old bit fields to prepare for re-packing
			mask_start = start_byte + 1 if has_counter else start_byte
			mask_len = total_bytes - 1 if has_counter else total_bytes
			for offset in range(mask_len):
				buf[mask_start + offset] = 0x00
				
			# 2. Pack the ones and zeros back down into raw byte values [1.1]
			track_free_count = 0
			for s in range(max_s):
				is_free = self.grid[t][s]
				if is_free:
					track_free_count += 1
					byte_offset = mask_start + (s // 8)
					bit_pos = s % 8
					buf[byte_offset] |= (1 << bit_pos)
					
			# 3. If the profile uses a 1-byte counter overhead, encode it now [1.1]
			if has_counter:
				buf[start_byte] = track_free_count

		# Step 2: Handle the unique 1571 Side 1 Pre-Computed cache totals update check [1.1]
		if fmt == "D71" and "side1_summary_offset" in self.params:
			summary_start = self.params["side1_summary_offset"]
			buf_s0 = self.sector_buffers[0] # Side 0 BAM sector
			
			for t_side1 in range(36, 71):
				# Sum up the live bits for Side 1 tracks natively inside the manager loop
				s1_track_free = sum(1 for s in range(self.params["sector_map"][t_side1]) if self.grid[t_side1][s])
				
				# Write the counter value directly into offsets 221-255 of Sector 0 [1.1]
				cache_byte_idx = summary_start + (t_side1 - 36)
				buf_s0[cache_byte_idx] = s1_track_free

		# Step 3: Command the driver plugin to flush the modified raw byte arrays back to disk sectors [1.1]
		for idx, (t, s) in enumerate(self.params["source_sectors"]):
			self.driver.write_virtual_sector(t, s, bytes(self.sector_buffers[idx]))
			
		# Synchronize layout states: Copy working grid items straight to the historical cache mirror
		for t in range(1, self.params["max_tracks"] + 1):
			for s in range(self.params["sector_map"].get(t, 0)):
				self.historical_copy[t][s] = self.grid[t][s]
				
		return True


