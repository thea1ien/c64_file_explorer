class TUIRenderer:
	"""Text User Interface (TUI) paint controller using curses."""
	@staticmethod
	def initialize_colors():
		"""Registers classic Midnight Commander style color palettes into terminal memory."""
		curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLUE)
		curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
		curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
		curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLUE)
		curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLUE)

	@staticmethod
	def draw_top_menubar(stdscr, max_cols):
		"""Paints the permanent drop-down menu anchor words across row 0."""
		stdscr.attron(curses.color_pair(3))
		stdscr.addstr(0, 0, " " * max_cols)
		stdscr.addstr(0, 2, " Left ")
		stdscr.addstr(0, 10, " File ")
		stdscr.addstr(0, 18, " Command ")
		stdscr.addstr(0, 29, " Options ")
		stdscr.addstr(0, 40, " Right ")
		stdscr.attroff(curses.color_pair(3))

	@staticmethod
	def draw_single_panel(stdscr, start_col, end_col, state_dict, is_active, max_rows):
		"""Draws one structural sidebar panel box container window framework."""
		panel_bottom_row = max_rows - 4
		width = end_col - start_col
		theme = curses.color_pair(4) if is_active else curses.color_pair(1)
		stdscr.attron(theme)

		# --- DRAW BORDER BOX OUTLINES ---
		for r in range(1, panel_bottom_row + 1):
			if r == 1:
				stdscr.addstr(r, start_col, "┌" + "─" * (width - 2) + "┐")
			elif r == panel_bottom_row:
				stdscr.addstr(r, start_col, "└" + "─" * (width - 2) + "┘")
			elif r == 3:
				stdscr.attron(theme)
				stdscr.addstr(r, start_col, "├" + "─" * (width - 2) + "┤")
			else:
				stdscr.addstr(r, start_col, "│")
				stdscr.addstr(r, start_col + width - 1, "│")
				stdscr.addstr(r, start_col + 1, " " * (width - 2))

		# --- DRAW PATH HEADER LABEL ROW ---
		path_label = f" {state_dict['current_path']} "
		if len(path_label) > (width - 4):
			path_label = "..." + path_label[-(width - 7):]
		stdscr.addstr(1, start_col + 2, path_label, curses.A_BOLD)

		# --- DRAW THE INTERNALS COLUMN HEADERS ---
		stdscr.addstr(2, start_col + 2, "Name", curses.A_REVERSE if is_active else curses.A_NORMAL)
		stdscr.addstr(2, start_col + int(width * 0.65), "Type")
		stdscr.addstr(2, start_col + (width - 10), "Size")

		is_container_path = state_dict['current_path'].startswith("VFS://")
		start_y_offset = 4

		if is_container_path and "disk_label_msg" in state_dict:
			stdscr.attron(curses.color_pair(5) if is_active else curses.color_pair(1))
			# =========================================================================
			# 🚨 FIXED HEADER DRAWING ENGINE: SINGLE PASS ALIGNMENT 🚨
			# Uses a single-pass draw to cleanly pad your label and position the
			# 'Blks' indicator without creating overlapping string artifacts [1.1].
			# =========================================================================
			header_string = state_dict.get("disk_label_msg", "")
			if header_string:
				# Pad out the label tightly to align 'Blks' perfectly over the size column
				# Subtracting the extra border padding guarantees crisp column alignment [1.1].
				target_padding_width = (width - 12)
				header_string = f"{header_string:<{target_padding_width}}Blks"
			
			# SINGLE PRINT PASS: Bypasses overlapping string collisions permanently!
			stdscr.addstr(4, start_col + 2, header_string)
			# =========================================================================
			stdscr.attroff(curses.color_pair(5) if is_active else curses.color_pair(1))
			stdscr.attron(theme)
			start_y_offset = 5


		# --- RENDER DIRECTORY FILE ROWS WITHIN VIEWPORT WINDOW ---
		files = state_dict["file_list"]
		idx_highlight = state_dict["highlight_index"]
		top_row = state_dict["top_visible_row"]
		max_visible_rows = panel_bottom_row - start_y_offset

		for v_row in range(max_visible_rows):
			file_idx = top_row + v_row
			if file_idx >= len(files):
				break
			item = files[file_idx]
			display_y = start_y_offset + v_row
			max_name_len = int(width * 0.60)
			clean_name = item["name"]
			if len(clean_name) > max_name_len:
				clean_name = clean_name[:max_name_len - 3] + "..."

			t_label = item.get("type_display", "CBM" if item["is_virtual_container"] else "FILE")
			if item["is_directory"]:
				t_label = "DIR"
			# =========================================================================
			# 🚨 UNIVERSAL VISUAL MASK: SIMPLE CBM QUOTE WRAPPER 🚨
			# This mask checks your active context parameters. If you are nested inside 
			# a virtual container disk, it wraps the clean filename string inside your 
			# double quotes, and then turns all underlines back into visual empty spaces!
			# =========================================================================
			if is_container_path:
				# 1. Directly wrap true CBM file entries inside authentic double quotes
				if not item["is_directory"] and clean_name != "..":
					clean_name = f'"{clean_name}"'
				
				# 2. Transform our background protection underscores (_) into visible spaces
				if "_" in clean_name:
					clean_name = clean_name.replace("_", " ")
			# =========================================================================


			if is_active and file_idx == idx_highlight:
				stdscr.attron(curses.color_pair(3))
				stdscr.addstr(display_y, start_col + 1, " " * (width - 2))
				stdscr.addstr(display_y, start_col + 2, f"{clean_name:<{max_name_len}}")
				stdscr.addstr(display_y, start_col + int(width * 0.65), f"{t_label:<4}")
				stdscr.addstr(display_y, start_col + (width - 10), f"{item['size_display']:>8}")
				stdscr.attroff(curses.color_pair(3))
				stdscr.attron(theme)
			else:
				stdscr.addstr(display_y, start_col + 2, f"{clean_name:<{max_name_len}}")
				stdscr.addstr(display_y, start_col + int(width * 0.65), f"{t_label:<4}")
				stdscr.addstr(display_y, start_col + (width - 10), f"{item['size_display']:>8}")

		stdscr.attron(theme)
		# FIXED: Safe inline dictionary verification prevents state variable blocking on initial system boots
		# FIXED: Direct object reference lookup bypasses frame refresh dictionary overwrites completely
		is_vfs = state_dict.get("is_in_container", False)
		handler = state_dict.get("vfs_handler")
		
		# FIXED: Dynamic object reference lookup routes parameters accurately across D64, D71, D81, or DNP formats
		if handler:
			free_sectors = getattr(handler, "free_sectors_count", 664)
		else:
			free_sectors = state_dict.get("free_sectors_count", 0)
			
		free_msg = f" {free_sectors} BLOCKS FREE " if is_vfs else f" {state_dict.get('free_space_msg', '0B FREE')} "


		if len(free_msg) < width - 4:
			stdscr.addstr(panel_bottom_row, start_col + width - len(free_msg) - 2, free_msg)
		stdscr.attroff(theme)
	@staticmethod
	def draw_footer_hotkeys(stdscr, max_rows, max_cols):
		"""Paints system command function buttons across the last screen row."""
		footer_y = max_rows - 1
		stdscr.move(footer_y, 0)
		stdscr.clrtoeol()
		hotkeys = [
			("1", "Help"), ("2", "Menu"), ("3", "View"), ("4", "Edit"),
			("5", "Copy"), ("6", "RenMov"), ("7", "Mkdir"), ("8", "Delete"),
			("9", "PullDn"), ("10", "Quit")
		]
		current_col = 0
		for num, label in hotkeys:
			stdscr.addstr(footer_y, current_col, f" {num} ", curses.A_REVERSE)
			current_col += len(num) + 2
			stdscr.addstr(footer_y, current_col, f"{label} ")
			current_col += len(label) + 1
			if current_col >= max_cols:
				break

	@staticmethod
	def paint_complete_screen(stdscr, tui_state):
		"""Redraws the complete twin explorer screen grid canvas cleanly."""
		max_rows, max_cols = stdscr.getmaxyx()
		if max_cols < 80 or max_rows < 24:
			stdscr.clear()
			stdscr.addstr(0, 0, " RESOLUTION WARNING: Terminal window size must be at least 80x24 characters.")
			stdscr.refresh()
			return

		stdscr.erase()
		TUIRenderer.draw_top_menubar(stdscr, max_cols)
		mid_split = max_cols // 2
		active_panel = tui_state["active_side"]

		TUIRenderer.draw_single_panel(stdscr, 0, mid_split, tui_state["left"], (active_panel == "left"), max_rows)
		TUIRenderer.draw_single_panel(stdscr, mid_split, max_cols, tui_state["right"], (active_panel == "right"), max_rows)

		stdscr.attron(curses.color_pair(2))
		raw_cmd_line = f"CBM-VFS Prompt> {tui_state['command_buffer']}"
		stdscr.addstr(max_rows - 2, 0, raw_cmd_line[:max_cols - 1])
		stdscr.clrtoeol()
		stdscr.attroff(curses.color_pair(2))

		TUIRenderer.draw_footer_hotkeys(stdscr, max_rows, max_cols)
		stdscr.refresh()


