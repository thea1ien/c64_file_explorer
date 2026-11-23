class TUIGCRViewerRenderer:
	"""Centralized full-screen TUI rendering helper module that displays raw, unaligned 
	GCR stream bytes with dynamic highlighting for hardware SYNC marks ($FF $FF).
	Expanded to double the visible data density on screen.
	"""
	@staticmethod
	def paint_gcr_viewer_workspace(stdscr, ctx):
		if not ctx:
			return
			
		stdscr.erase()
		max_y, max_x = stdscr.getmaxyx()
		
		archive_name = ctx.get("archive_name", "UNKNOWN CONTAINER")
		track_num = ctx.get("track", 18)
		scroll_off = ctx.get("scroll_offset", 0)
		raw_stream = ctx.get("raw_stream", b"")
		stream_len = len(raw_stream)

		# 1. Paint Top Dashboard Control Rows
		stdscr.addstr(1, 2, f"LOW-LEVEL MAGNETIC GCR TRACK STREAM VIEWER  |	 CONTAINER: {archive_name[:35]}", curses.A_BOLD)
		
		# FIXED: Formats track_num safely as a float string layout property to cleanly showcase .5 entries!
		track_str = f"{track_num:.1f}"
		stdscr.addstr(2, 2, f"PHYSICAL TRACK: {track_str:>4}   |   STREAM SIZE: {stream_len:<5} Bytes	|	VIEW OFFSET: ${scroll_off:04X} / {scroll_off}", curses.A_NORMAL)
		stdscr.addstr(3, 2, "=" * (max_x - 4))
		
		# Column index guide layout line
		stdscr.addstr(4, 2, "Addr	00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F	  ASCII", curses.A_UNDERLINE)

		# empty data stream guard display check
		if stream_len == 0:
			stdscr.addstr(6, 4, f"NOTICE: No GCR magnetic track data exists for Track {track_str} inside this image.", curses.A_BOLD | curses.A_DIM)
			stdscr.addstr(max_y - 2, 4, "CONTROLS: ARROWS/WASD = Scroll | +/- = Shift Tracks | Q/ESC = Exit", curses.A_DIM)
			stdscr.refresh()
			return
		# FIXED: Expanded view height boundaries calculation! 
		# Instead of capping strictly at 16 rows, this dynamically calculates available 
		# canvas lines up to 32 rows or more, maximizing visual density on large monitors.
		view_height = min(36, max_y - 8)
		
		for row in range(view_height):
			row_addr = scroll_off + (row * 16)
			if row_addr >= stream_len:
				break

			# Print absolute address label column
			stdscr.addstr(5 + row, 2, f"{row_addr:04X}: ")
			
			# Build 16-byte layout records row-by-row
			for col in range(16):
				byte_idx = row_addr + col
				if byte_idx < stream_len:
					b_val = raw_stream[byte_idx]
					curr_x = 9 + (col * 3)
					
					# Highlighting logic flags 0xFF as a hardware magnetic SYNC block
					is_sync = (b_val == 0xFF)
					attr = curses.A_REVERSE if is_sync else curses.A_NORMAL
					
					stdscr.addstr(5 + row, curr_x, f"{b_val:02X}", attr)
					stdscr.addstr(5 + row, curr_x + 2, " ")
					
					# Build ASCII translation character cell
					if 32 <= b_val <= 126:
						ascii_char = chr(b_val)
					else:
						ascii_char = "."
					stdscr.addstr(5 + row, 59 + col, ascii_char)
				else:
					# Pad empty spacing trails
					stdscr.addstr(5 + row, 9 + (col * 3), "	  ")
					stdscr.addstr(5 + row, 59 + col, " ")

		# 3. Print Help Instructions Footer Line
		stdscr.addstr(max_y - 2, 2, "CONTROLS: ARROWS/WASD = Scroll | PGUP/PGDN = Quick Jump | +/- = Shift Tracks | Q/ESC = Exit", curses.A_DIM)
		stdscr.refresh()


