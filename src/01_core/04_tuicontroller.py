class TUIController:
	"""Orchestration layout layer mapping raw data frames onto active viewport grids."""
	@staticmethod
	def get_host_free_space_string(target_path):
		try:
			if sys.platform.startswith("win"):
				import ctypes
				free_bytes = ctypes.c_ulonglong(0)
				ctypes.windll.kernel32.GetDiskFreeSpaceExW(target_path, None, None, ctypes.byref(free_bytes))
				total_free = free_bytes.value
			else:
				st = os.statvfs(target_path)
				total_free = st.f_bavail * st.f_frsize
			if total_free < 1024 * 1024 * 1024:
				return f"{total_free // (1024 * 1024)}M FREE"
			else:
				return f"{total_free / (1024 * 1024 * 1024):.1f}G FREE"
		except Exception:
			return "0B FREE"

	@staticmethod
	def extract_vfs_file_bytes(handler_instance, track, sector):
		payload_bytes = bytearray()
		lt, ls = track, sector
		while lt != 0:
			sec_data = handler_instance.read_virtual_sector(lt, ls)
			if not sec_data:
				break
			nt, ns = int(sec_data[0]), int(sec_data[1])
			if nt == 0:
				payload_bytes.extend(sec_data[2 : ns + 1])
				break
			else:
				payload_bytes.extend(sec_data[2:256])
			lt, ls = nt, ns
		return bytes(payload_bytes)
	@staticmethod
	
	def establish_bulk_copy_strategy(stdscr, selected_count):
		"""
		Acts precisely like a classic BASIC GOSUB block.
		Evaluates bulk selection queues and hooks confirmation popup overlays.
		"""
		# If only 1 file is selected, bypass the global warning prompt pass entirely
		if selected_count <= 1:
			return "ASK"

		max_rows, max_cols = stdscr.getmaxyx()
		box_w, box_h = 64, 8
		start_x = (max_cols - box_w) // 2
		start_y = (max_rows - box_h) // 2

		# Strategy Choice Loop Pass 1
		while True:
			stdscr.attron(curses.color_pair(4))
			for r in range(box_h):
				curr_y = start_y + r
				if r == 0:
					stdscr.addstr(curr_y, start_x, "┌" + "─" * (box_w - 2) + "┐")
				elif r == box_h - 1:
					stdscr.addstr(curr_y, start_x, "└" + "─" * (box_w - 2) + "┘")
				else:
					stdscr.addstr(curr_y, start_x, "│" + " " * (box_w - 2) + "│")

			stdscr.addstr(start_y + 1, start_x + 4, f" BATCH FILE TRANSFER INITIALIZATION GATEWAY ", curses.A_BOLD)
			stdscr.addstr(start_y + 2, start_x + 2, "─" * (box_w - 4))
			stdscr.addstr(start_y + 3, start_x + 4, f"Queue contains {selected_count} files. If duplicate names are found:")
			stdscr.addstr(start_y + 5, start_x + 8, "[O] Overwrite Automatically   │   [A] Ask Individually", curses.A_REVERSE)
			stdscr.attroff(curses.color_pair(4))
			stdscr.refresh()

			ch = stdscr.getch()
			if ch in [ord('a'), ord('A')]:
				return "ASK"
			
			elif ch in [ord('o'), ord('O')]:
				# Trigger Secondary Fatal Safety Warning Confirmation Layer (Pass 2)
				while True:
					stdscr.attron(curses.color_pair(3)) # Alternating highlight warning color mask
					for r in range(box_h - 2):
						stdscr.addstr(start_y + 1 + r, start_x + 1, " " * (box_w - 2))
					
					stdscr.addstr(start_y + 2, start_x + 4, "⚠️	 CRITICAL DESTRUCTION WARNING!	⚠️", curses.A_BOLD)
					stdscr.addstr(start_y + 4, start_x + 4, "Overwrite ALL mode eliminates downstream safety prompts.")
					stdscr.addstr(start_y + 5, start_x + 6, "Confirm permanent replacement action? (Y/N): ", curses.A_BOLD)
					stdscr.attroff(curses.color_pair(3))
					stdscr.refresh()

					warn_ch = stdscr.getch()
					if warn_ch in [ord('y'), ord('Y')]:
						return "AUTO_OVERWRITE"
					if warn_ch in [ord('n'), ord('N'), 27]:
						break # Break out of warning sub-loop, drop cleanly back to Pass 1 menu options!

	@staticmethod
	def mine_dnp_entries(dnp_handler, track, sector):
		entries = dnp_handler.list_directory_entries(track, sector)
		prefix = [{
			"name": "..", "is_directory": True, "is_virtual_container": False,
			"type_display": "UP-DIR", "size_display": " ", "modify_time_str": " -- -- -- "
		}]
		return prefix + entries

	@staticmethod
	def process_scrolling_movement(panel_dict, direction, viewport_limits):
		"""Fact-aligned view scrolling manager that ensures selection cursors 
		stay fully visible within viewport coordinate windows boundaries.
		"""
		max_rows = viewport_limits[0] - 8
		ledger_len = len(panel_dict["file_list"])
		if ledger_len == 0:
			return

		if direction == "UP":
			if panel_dict["highlight_index"] > 0:
				panel_dict["highlight_index"] -= 1
				if panel_dict["highlight_index"] < panel_dict["top_visible_row"]:
					panel_dict["top_visible_row"] = panel_dict["highlight_index"]
					
		elif direction == "DOWN":
			if panel_dict["highlight_index"] < ledger_len - 1:
				panel_dict["highlight_index"] += 1
				
				# FIXED: Subtracting 1 forces the container viewport to scroll upward 
				# one line earlier, keeping your highlighted selection completely visible!
				if panel_dict["highlight_index"] >= panel_dict["top_visible_row"] + (max_rows - 1):
					panel_dict["top_visible_row"] = panel_dict["highlight_index"] - (max_rows - 1) + 1

	@staticmethod
	def check_target_for_duplicate_filename(target_file_list, source_filename):
		"""Automated name collision gatekeeper scanning target directories and virtual container 
		disk images to intercept identical filename strings and prevent silent data overwrites.
		"""
		if not target_file_list:
			return False
			
		# Strip case sensitivity and padding variations to ensure matching accuracy
		sanitized_source = source_filename.strip().lower()
		
		for entry in target_file_list:
			# Skip checking parent directional link rows
			if entry.get("name") == "..":
				continue
				
			sanitized_target = entry.get("name", "").strip().lower()
			
			# Collision Intercepted: Match found!
			if sanitized_target == sanitized_source:
				return True
				
		return False


