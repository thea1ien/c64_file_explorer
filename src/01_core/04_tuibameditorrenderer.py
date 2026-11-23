class TUIBAMEditorRenderer:
	"""Centralized full-screen TUI rendering helper module that builds the 8-track 
	scrollable BAM block allocation grid layout with clear visual dual-value metrics indicators.
	"""
	@staticmethod
	def paint_bam_editor_workspace(stdscr, ctx):
		if not ctx:
			return
			
		stdscr.erase()
		max_y, max_x = stdscr.getmaxyx()
		
		archive_name = ctx.get("archive_name", "UNKNOWN CONTAINER")
		fmt_type = ctx.get("format_type", "D64")
		cur_t = ctx.get("cursor_track", 1)
		cur_s = ctx.get("cursor_sector", 0)
		top_s = ctx.get("top_visible_sector", 0)
		left_t = ctx.get("left_visible_track", 1)
		max_t = ctx.get("max_track", 35)
		sector_map = ctx.get("sector_map", {})
		bam_mgr = ctx.get("bam_manager")
		
		if not bam_mgr:
			stdscr.addstr(2, 2, "ERROR: BAM Manager Object not initialized.")
			stdscr.refresh()
			return

		disk_free_blocks = bam_mgr.count_free_blocks(use_historical=True)
		editor_free_blocks = bam_mgr.count_free_blocks(use_historical=False)

		# 1. Top Header Rows
		stdscr.addstr(1, 2, f"CBM HARDWARE BAM EDITOR  |  FORMAT: {fmt_type}  |	 CONTAINER: {archive_name[:35]}", curses.A_BOLD)
		stdscr.addstr(2, 2, f"POSITION: Track {cur_t:>3} / Sector {cur_s:>3}", curses.A_NORMAL)
		
		disk_str = f"DISK FREE: {disk_free_blocks:<4}"
		edit_str = f"BUFFERED FREE: {editor_free_blocks:<4}"
		if ctx.get("dirty", False):
			edit_str += " (UNSAVED)"
			
		stdscr.addstr(3, 2, f"{disk_str}   |   ", curses.A_NORMAL)
		stdscr.addstr(3, len(disk_str) + 9, edit_str, curses.A_BOLD if ctx.get("dirty") else curses.A_NORMAL)
		stdscr.addstr(4, 2, "=" * (max_x - 4))
		
		# 2. Track Column Headers (Ensures absolute 5-character structural column blocks spacing!)
		header_row = "Sec	"
		for col_idx in range(8):
			t_num = left_t + col_idx
			if t_num <= max_t:
				header_row += f" T{t_num:<3}"
		stdscr.addstr(5, 4, header_row[:max_x-6], curses.A_UNDERLINE | curses.A_BOLD)

		# 3. Dynamic Vertical Row Loop
		view_height = min(16, max_y - 9)
		for v_row in range(view_height):
			s_num = top_s + v_row
			
			# Clean workspace line natively to remove historical artifacts
			stdscr.addstr(6 + v_row, 4, " " * (max_x - 6))
			stdscr.addstr(6 + v_row, 4, f"S{s_num:<3} ")

			for v_col in range(8):
				t_num = left_t + v_col
				if t_num > max_t:
					continue
					
				max_s_for_t = sector_map.get(t_num, 0)
				
				# FIXED: Mathematically perfect horizontal alignment!
				# Aligns cell characters exactly centered underneath the T1, T2 headers
				x_pos = 10 + (v_col * 5)
				
				if s_num >= max_s_for_t:
					stdscr.addstr(6 + v_row, x_pos, " . ", curses.A_DIM)
					continue

				is_block_free = bam_mgr.check_sector_status(t_num, s_num)
				token_char = "-" if is_block_free else "*"
				display_token = f" {token_char} "

				is_cursor = (t_num == cur_t and s_num == cur_s)
				attr = curses.A_REVERSE if is_cursor else curses.A_NORMAL
				
				stdscr.addstr(6 + v_row, x_pos, display_token, attr)

		stdscr.addstr(max_y - 2, 4, "CONTROLS: ARROWS/WASD = Move | SPACE = Toggle | W = Write Changes | Q/ESC = Exit", curses.A_DIM)
		stdscr.refresh()


