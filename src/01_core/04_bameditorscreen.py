class BAMEditorScreen:
	"""Standalone Dedicated Screen Interface managing interactive Block Availability Map 
	editing with track-by-track sector boundary clipping across all CBM drivers.
	"""
	@staticmethod
	def get_disk_geometry(driver_instance):
		"""Fact-aligned hardware layout analyzer returning total tracks 
		and exact sector capacities per track matching your filesystem profile.
		"""
		geom = {"max_tracks": 35, "sector_map": {}}
		if not driver_instance:
			return geom
			
		geom["max_tracks"] = getattr(driver_instance, "max_tracks_limit", 35)
		class_name = driver_instance.__class__.__name__
		
		if "D64" in class_name:
			for t in range(1, geom["max_tracks"] + 1):
				if t <= 17: geom["sector_map"][t] = 21
				elif t <= 24: geom["sector_map"][t] = 19
				elif t <= 30: geom["sector_map"][t] = 18
				else: geom["sector_map"][t] = 17
		elif "D71" in class_name:
			for t in range(1, geom["max_tracks"] + 1):
				normalized_t = t if t <= 35 else (t - 35)
				if normalized_t <= 17: geom["sector_map"][t] = 21
				elif normalized_t <= 24: geom["sector_map"][t] = 19
				elif normalized_t <= 30: geom["sector_map"][t] = 18
				else: geom["sector_map"][t] = 17
		elif "DNP" in class_name:
			for t in range(1, geom["max_tracks"] + 1):
				geom["sector_map"][t] = 256
		else:
			for t in range(1, geom["max_tracks"] + 1):
				geom["sector_map"][t] = 21
				
		return geom

	@staticmethod
	def calculate_live_free_blocks(driver_instance, geom):
		"""Scans the live driver array bitmasks in real-time to compute the exact free blocks."""
		free_count = 0
		if not driver_instance:
			return 0
			
		for t in range(1, geom["max_tracks"] + 1):
			# Skip the directory track sectors based on drive format layout rules
			if "D71" in driver_instance.__class__.__name__ and t == 18:
				continue
			if "D64" in driver_instance.__class__.__name__ and t == 18:
				continue
				
			max_s = geom["sector_map"].get(t, 0)
			for s in range(max_s):
				try:
					if driver_instance.check_sector_free_status(t, s):
						free_count += 1
				except Exception:
					pass
		return free_count

	@staticmethod
	def run_editor(stdscr, driver_instance, archive_name):
		"""Main independent orchestration loop rendering the standalone BAM layout screen."""
		if not driver_instance:
			return
			
		geom = BAMEditorScreen.get_disk_geometry(driver_instance)
		
		# Initialize local viewport and cursor parameters
		state = {
			"cursor_track": 1,
			"cursor_sector": 0,
			"top_visible_sector": 0,
			"left_visible_track": 1,
			"max_tracks": geom["max_tracks"],
			"sector_map": geom["sector_map"],
			"dirty": False
		}
		
		# Force a baseline free sectors tally calculation matching the driver's state
		if hasattr(driver_instance, "free_sectors_count"):
			live_free_blocks = driver_instance.free_sectors_count
		else:
			live_free_blocks = BAMEditorScreen.calculate_live_free_blocks(driver_instance, geom)

		stdscr.clear()
		stdscr.keypad(True)
		curses.curs_set(0)

		while True:
			max_y, max_x = stdscr.getmaxyx()
			
			# 1. RENDER TOP HEADER DASHBOARD
			stdscr.addstr(1, 2, f"BAM EDITOR - IMAGE: {archive_name[:40]}", curses.A_BOLD)
			stdscr.addstr(2, 2, f"POSITION: Track {state['cursor_track']:>3} / Sector {state['cursor_sector']:>3}	|	FREE BLOCKS: {live_free_blocks:<4}")
			stdscr.addstr(3, 2, "=" * (max_x - 4))
			
			# 2. RENDER THE SCROLLABLE GRID CORES
			# Draw Track Column Label Headers (Up to 8 viewable columns fits perfectly inside TUI layouts)
			header_row = "Sec  "
			for col_idx in range(8):
				t_num = state["left_visible_track"] + col_idx
				if t_num <= state["max_tracks"]:
					header_row += f" T{t_num:<3}"
			stdscr.addstr(5, 2, header_row[:max_x-4], curses.A_UNDERLINE)

			# Determine vertical display ceiling limits based on console size bounds
			view_height = min(16, max_y - 9)
			
			for v_row in range(view_height):
				s_num = state["top_visible_sector"] + v_row
				
				# Identify if at least one track in the current viewport contains this sector number
				has_sector_data = False
				for c_idx in range(8):
					t_num = state["left_visible_track"] + c_idx
					if t_num <= state["max_tracks"] and s_num < state["sector_map"].get(t_num, 0):
						has_sector_data = True
						break
						
				if not has_sector_data:
					# Clean the trailing rows nicely if we slide beyond max capacities
					stdscr.addstr(6 + v_row, 2, " " * (max_x - 4))
					continue

				# Print Sector Row Title Label
				stdscr.addstr(6 + v_row, 2, f"S{s_num:<3} ")

				# Render data columns row by row
				for v_col in range(8):
					t_num = state["left_visible_track"] + v_col
					if t_num > state["max_tracks"]:
						continue
						
					max_sectors_on_track = state["sector_map"].get(t_num, 0)
					x_pos = 7 + (v_col * 5)
					
					# Print dots to indicate unmapped hardware geometry
					if s_num >= max_sectors_on_track:
						stdscr.addstr(6 + v_row, x_pos, "  .  ", curses.A_DIM)
						continue

					# Pull actual live byte allocation state out of our format drivers
					is_free = driver_instance.check_sector_free_status(t_num, s_num)
					token = "-" if is_free else "*"
					display_string = f"	 {token}  "

					# Highlight cell token under cursor focus coordinates
					is_selected = (t_num == state["cursor_track"] and s_num == state["cursor_sector"])
					attr = curses.A_REVERSE if is_selected else curses.A_NORMAL
					
					stdscr.addstr(6 + v_row, x_pos, display_string, attr)

			# 3. RENDER FOOTER HELBLINE STATUS
			stdscr.addstr(max_y - 2, 2, "CONTROLS: ARROWS = Move | SPACE = Toggle Allocation | ENTER/ESC = Save & Return", curses.A_DIM)
			stdscr.refresh()

			# 4. CAPTURE KEYBOARD INTERCEPTS
			try:
				key = stdscr.getkey()
			except Exception:
				continue

			cur_t = state["cursor_track"]
			cur_s = state["cursor_sector"]

			if key in ("KEY_UP", "w", "W"):
				if cur_s > 0:
					state["cursor_sector"] -= 1
					if state["cursor_sector"] < state["top_visible_sector"]:
						state["top_visible_sector"] = state["cursor_sector"]
						
			elif key in ("KEY_DOWN", "s", "S"):
				# HARDWARE CLIP: Fetch the current track's absolute ceiling sector capacity limit!
				current_track_max = state["sector_map"].get(cur_t, 0)
				if cur_s < current_track_max - 1:
					state["cursor_sector"] += 1
					if state["cursor_sector"] >= state["top_visible_sector"] + view_height:
						state["top_visible_sector"] = state["cursor_sector"] - view_height + 1
						
			elif key in ("KEY_LEFT", "a", "A"):
				if cur_t > 1:
					state["cursor_track"] -= 1
					# HARDWARE AUTO-ADJUST: Clamps sector value smoothly when jumping horizontally onto shorter tracks!
					target_track_max = state["sector_map"].get(state["cursor_track"], 0)
					if state["cursor_sector"] >= target_track_max:
						state["cursor_sector"] = target_track_max - 1
						
					if state["cursor_track"] < state["left_visible_track"]:
						state["left_visible_track"] = state["cursor_track"]
						
			elif key in ("KEY_RIGHT", "d", "D"):
				if cur_t < state["max_tracks"]:
					state["cursor_track"] += 1
					# HARDWARE AUTO-ADJUST: Same horizontal clamp safety check
					target_track_max = state["sector_map"].get(state["cursor_track"], 0)
					if state["cursor_sector"] >= target_track_max:
						state["cursor_sector"] = target_track_max - 1
						
					if state["cursor_track"] >= state["left_visible_track"] + 8:
						state["left_visible_track"] = state["cursor_track"] - 8 + 1
						
			elif key == " ":
				# SPACE BAR: Toggles the allocation bit mask inside your plugin driver natively!
				if hasattr(driver_instance, "toggle_sector_allocation_status"):
					driver_instance.toggle_sector_allocation_status(cur_t, cur_s)
					state["dirty"] = True
					# Recalculate live total to update the metrics panel instantly
					live_free_blocks = BAMEditorScreen.calculate_live_free_blocks(driver_instance, geom)
					if hasattr(driver_instance, "free_sectors_count"):
						driver_instance.free_sectors_count = live_free_blocks
						
			elif key in ("\n", "KEY_ENTER", chr(27)): # Enter or Escape terminates execution
				if state["dirty"]:
					# If the user made structural changes, sync parameters with the driver's base data structures
					if hasattr(driver_instance, "free_sectors_count"):
						driver_instance.free_sectors_count = live_free_blocks
				break

		# Reset the terminal window parameters safely before diving back into the dual-panes
		stdscr.clear()


