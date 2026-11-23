class TUISectorEditorRenderer:
	"""UI Paint Controller for the full-screen interactive low-level Sector Editor."""
	@staticmethod
	def paint_editor_workspace(stdscr, editor_state):
		max_rows, max_cols = stdscr.getmaxyx()
		stdscr.erase()
		if max_cols < 80 or max_rows < 32:
			stdscr.clear()
			stdscr.addstr(0, 0, " RESOLUTION WARNING: Terminal size must be at least 80x32 characters for the editor.")
			stdscr.refresh()
			return

		stdscr.attron(curses.color_pair(2))
		stdscr.addstr(0, 0, "┌" + "─" * (max_cols - 2) + "┐")
		stdscr.addstr(1, 2, "COMMODORE 64 INTERACTIVE SECTOR EDITOR Toolkit")
		title_str = f"Container Layer Targets: [{editor_state['archive_name'].upper()}] ({editor_state['format_type']}) "
		stdscr.addstr(1, max_cols - len(title_str) - 3, title_str, curses.A_BOLD)
		stdscr.addstr(2, 0, "├" + "─" * (max_cols - 2) + "┤")

		coord_line = f"VIEWING LOCATIONS -> TRACK: {editor_state['track']:02d} │ SECTOR: {editor_state['sector']:02d} │ BLOCK LIMITS: 1-{editor_state['max_track']}"
		stdscr.addstr(3, 2, coord_line, curses.A_BOLD)
		stdscr.addstr(4, 0, "├" + "─" * (max_cols - 2) + "┤")
		stdscr.addstr(5, 7, "00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F │ ASCII / PETSCII CHARACTER VIEW")
		stdscr.addstr(6, 2, "── ─────────────────────────────────────────────── ┼ ────────────────────────────────")

		buffer_data = editor_state["buffer"]
		cursor_offset = editor_state["cursor_offset"]
		edit_mode = editor_state["edit_mode"]

		for row_idx in range(16):
			display_y = 7 + row_idx
			row_start_offset = row_idx * 16
			stdscr.addstr(display_y, 2, f"${row_start_offset:02X}:", curses.A_BOLD)

			# Hex Canvas Grid View
			for col_idx in range(16):
				cell_offset = row_start_offset + col_idx
				byte_val = buffer_data[cell_offset]
				display_x = 7 + (col_idx * 3)
				if cell_offset == cursor_offset:
					attr = curses.color_pair(3) if edit_mode != "NAV" else curses.A_REVERSE
					stdscr.addstr(display_y, display_x, f"{byte_val:02X}", attr)
				else:
					stdscr.addstr(display_y, display_x, f"{byte_val:02X}")

			stdscr.addstr(display_y, 55, "│")

			# Decoded Char Matrix Column View
			for col_idx in range(16):
				cell_offset = row_start_offset + col_idx
				byte_val = buffer_data[cell_offset]
				display_x = 58 + col_idx
				if 32 <= byte_val <= 126:
					char_repr = chr(byte_val)
				elif 65 <= (byte_val & 0x7F) <= 90:
					char_repr = chr((byte_val & 0x7F) + 32)
				else:
					char_repr = "·"

				if cell_offset == cursor_offset:
					attr = curses.color_pair(3) if edit_mode != "NAV" else curses.A_REVERSE
					stdscr.addstr(display_y, display_x, char_repr, attr)
				else:
					stdscr.addstr(display_y, display_x, char_repr)

		stdscr.addstr(23, 0, "├" + "─" * (max_cols - 2) + "┤")
		stdscr.attron(curses.A_BOLD)
		current_byte = buffer_data[cursor_offset]
		stdscr.addstr(24, 4, f" CURSOR TARGET STATUS -> POSITION: ${cursor_offset:02X} │ BYTE: ${current_byte:02X} │ DEC: {current_byte:<3}")
		stdscr.attroff(curses.A_BOLD)
		stdscr.addstr(25, 0, "├" + "─" * (max_cols - 2) + "┤")

		stdscr.addstr(26, 2, " COMMAND MENU ACTIONS: ", curses.A_BOLD)
		stdscr.addstr(26, 26, "[R] Read Sector │ [W] Write Sector │ [J] Context Jump (T/S vectors)")
		stdscr.addstr(27, 4, "[+] Forward Next │ [-] Backward Prev │ [T] Type Text │ [@] Change Hex Byte")
		stdscr.addstr(28, 4, "[Q] Quit (Exit Editor / Return cleanly to dual explorer panel dashboard panes)")

		stdscr.attron(curses.color_pair(5))
		status_line = f" STATUS Ticker> {editor_state['status_msg']}"
		stdscr.addstr(29, 2, status_line[:max_cols - 3])
		stdscr.clrtoeol()
		stdscr.attroff(curses.color_pair(5))
		stdscr.addstr(30, 0, "└" + "─" * (max_cols - 3) + "┘")
		stdscr.attroff(curses.color_pair(2))
		stdscr.refresh()


