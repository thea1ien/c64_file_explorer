def verify_and_bootstrap_dependencies():
	"""Natively inspects the workstation environment for mandatory external drivers."""
	for module_name, pip_package_name in MANDATORY_LIBS.items():
		if pip_package_name is None:
			continue
		try:
			__import__(module_name)
		except ImportError:
			print(f"\n SYSTEM CONFIGURATION WARNING: The '{module_name}' library is required.")
			is_interactive = hasattr(sys.stdin, "isatty") and sys.stdin.isatty() and hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
			if not is_interactive:
				print(" Automatic installation is unavailable because this session is not running in an interactive terminal.")
				sys.exit(1)
			user_choice = input(f" Install '{pip_package_name}' via pip right now? (y/n): ").strip().lower()
			if user_choice == 'y':
				try:
					subprocess.check_call([sys.executable, "-m", "pip", "install", pip_package_name])
					__import__(module_name)
				except Exception as err:
					print(f"\n AUTOMATED INSTALLATION ROUTINE FAILED: {str(err)}")
					sys.exit(1)
			else:
				sys.exit(1)


def main_orchestration_loop(stdscr):
	"""Main baseline launch controller coordinating curses events or handing off to Pygame."""
	curses.curs_set(0)
	stdscr.timeout(100)
	TUIRenderer.initialize_colors()

	initial_path = os.getcwd()
	app_state = {
		"visual_mode": "STANDARD",
		"menu_mode": "PANELS",
		"active_side": "left",
		"command_buffer": "System Bootstrapped. Press [F2/F9/M] for Actions.",
		"left": {
			"current_path": initial_path, "backed_host_path": initial_path,
			"archive_root": "", "is_in_container": False, "vfs_handler": None, "disk_label_msg": None,
			"file_list": HostSystemScanner.scan_directory(initial_path),
			"free_space_msg": TUIController.get_host_free_space_string(initial_path),
			"highlight_index": 0, "top_visible_row": 0
		},
		"right": {
			"current_path": initial_path, "backed_host_path": initial_path,
			"archive_root": "", "is_in_container": False, "vfs_handler": None, "disk_label_msg": None,
			"file_list": HostSystemScanner.scan_directory(initial_path),
			"free_space_msg": TUIController.get_host_free_space_string(initial_path),
			"highlight_index": 0, "top_visible_row": 0
		}
	}

	# Initialize dynamic system settings matrix states persistently from disk config maps
	saved_profile = ConfigurationManager.load_application_settings()
	app_state["visual_mode"] = saved_profile.get("visual_mode", "STANDARD")

	while True:
		# --- NATIVE TUI TEXT FILE CONTENT PAGER CONTROLLER (AUTHENTIC ORIGINAL EXTRACTION) ---
		if app_state.get("menu_mode") == "VIEWER":
			v_ctx = app_state.get("viewer_runtime_context", {})
			raw_payload = v_ctx.get("payload", b"")
			disp_m = v_ctx.get("display_mode", "PROMPT")
			stdscr.erase(); h, w = stdscr.getmaxyx()
			
			# --- VIEW DESIGN LAYER A: REPRODUCE CHOSEN TRANSLATION PROMPT ---
			if disp_m == "PROMPT":
				stdscr.attron(curses.A_REVERSE)
				stdscr.addstr(0, 0, f" 📂 VFS UNIFIED VIEW: '{v_ctx.get('file_name','').upper()}' ".ljust(w - 1)[:w-1])
				stdscr.attroff(curses.A_REVERSE)
				stdscr.addstr(3, 4, "SELECT VIEWING DISPLAY LAYOUT REPRESENTATION MODE:")
				stdscr.addstr(5, 6, "1. Modern Standard ASCII format representation")
				stdscr.addstr(7, 6, "2. Authentic Commodore PETSCII to ANSI/Unicode Translation")
				stdscr.addstr(9, 6, "3. Pure Style C64 Pro Mono TTF PUA Quadrant Mapping")
				stdscr.addstr(11, 6, "4. Advanced 16-Byte Hexadecimal & ASCII Buffer Code Dump")
				stdscr.addstr(14, 4, "Select mode (1-4) or press [ESC] to abort: ")
				stdscr.refresh()
				
				t_key = stdscr.getch()
				if t_key == 27: 
					app_state["menu_mode"] = "PANELS"
				elif t_key == ord('1'): v_ctx["display_mode"] = "ASCII"; v_ctx["lowercase_toggle"] = True
				elif t_key == ord('2'): v_ctx["display_mode"] = "ANSI_PETSCII"; v_ctx["lowercase_toggle"] = True
				elif t_key == ord('3'): v_ctx["display_mode"] = "PUA_PETSCII"; v_ctx["lowercase_toggle"] = True
				elif t_key == ord('4'): v_ctx["display_mode"] = "HEX_DUMP"; v_ctx["scroll_row"] = 0
				continue
				
			# --- VIEW DESIGN LAYER B: AUTHENTIC 40-COLUMN STREAM RASTER ---
			C64_ANSI_COLOR_MAP = {
				144: "0", 5: "15", 28: "124", 159: "87", 156: "127", 30: "34", 31: "19", 158: "220",
				129: "130", 149: "94", 150: "210", 151: "240", 152: "245", 153: "121", 154: "117", 155: "250"
			}
			# FIXED HIGH-RESOLUTION GLYPHS: Replaced thin corner wires with dense geometric blocks!
			# This closes the padding gaps, wiping away the lowercase 'r' visual artifacts completely.
			C64_UNICODE_FALLBACK_ROM = {
				0x20: " ", 0xa0: "█", 0x60: "▄", 0x7c: "▌", 0x7b: "█", 0xbd: "▗", 0xbe: "▘", 0xb1: "▘", 
				0xad: "▖", 0xae: "▝", 0xb2: "▄", 0xb3: "▀", 0xb4: "▐", 0xab: "▌", 0xbf: "▄", 0x7d: "▌",
				0xa1: "▌", 0xa2: "▄", 0xa3: "▔", 0xa5: "▏", 0xa6: "▒", 0xa7: "▕", 0xb5: "▎", 0xb6: "▍",
				0xb9: "▃", 0xba: "▄", 0xbb: "▅", 0x61: "♠", 0x6b: "♥", 0x70: "♣", 0x74: "♦", 0x62: "▞"
			}
			
			rendered_rows = []
			current_line_text = ""
			col_counter = 0
			current_fg = "15"
			reverse_mode = False
			lowercase_mode = v_ctx.get("lowercase_toggle", True)
			quote_mode_active = False
			
			def local_ansi_seq(fg, bg="0"):
				return f"\x1b[0;48;5;{bg};38;5;{fg}m"
				
			current_line_text += local_ansi_seq(current_fg)
			idx = 2 if len(raw_payload) > 2 and raw_payload == 0x01 and raw_payload == 0x08 else 0
			
			while idx < len(raw_payload):
				# FIXED THREE-WAY ROUTER: Decouples hex compilation from standard text streams
				if disp_m == "HEX_DUMP":
					break

				b = raw_payload[idx]; idx += 1
				
				if disp_m == "ASCII":
					if b in (10, 13):
						rendered_rows.append(current_line_text.ljust(40) + "\033[0m")
						current_line_text = local_ansi_seq(current_fg); col_counter = 0
						if b == 13 and idx < len(raw_payload) and raw_payload[idx] == 10: idx += 1
						continue
					# FIXED TWO-WAY CASING: Shifts native uppercase capital text bytes down to standard lowercase words!
					if lowercase_mode and 65 <= b <= 90:
						char_str = chr(b + 32) # Shift capital letters down to lowercase slots
					elif not lowercase_mode and 97 <= b <= 122:
						char_str = chr(b - 32) # Shift lowercase letters up to capital slots
					else:
						char_str = chr(b) if 32 <= b <= 126 else "."
					current_line_text += char_str
					col_counter += 1
					if col_counter == 40:
						rendered_rows.append(current_line_text + "\033[0m")
						current_line_text = local_ansi_seq(current_fg); col_counter = 0
				else:
					if quote_mode_active:
						if b == 0x22: quote_mode_active = False
						if disp_m == "PUA_PETSCII":
							q_base = 0xE100 if lowercase_mode else 0xE000
							if reverse_mode: q_base += 0x0200
							char_glyph = chr(q_base + b)
						else:
							char_glyph = C64_UNICODE_FALLBACK_ROM.get(b, chr(b) if 32<=b<=126 else " ")
						current_line_text += char_glyph; col_counter += 1
						if col_counter == 40:
							rendered_rows.append(current_line_text + "\033[0m")
							current_line_text = local_ansi_seq(current_fg); col_counter = 0
						continue
						
					if b == 0x22:
						quote_mode_active = True
						if disp_m == "PUA_PETSCII":
							q_base = 0xE100 if lowercase_mode else 0xE000
							if reverse_mode: q_base += 0x0200
							char_glyph = chr(q_base + b)
						else: char_glyph = '"'
						current_line_text += char_glyph; col_counter += 1
						if col_counter == 40:
							rendered_rows.append(current_line_text + "\033[0m")
							current_line_text = local_ansi_seq(current_fg); col_counter = 0
						continue

					# === [MODULE: TUIController] Part 5 (Authentic ANSI Engine - 2 of 2) ===
					if b in C64_ANSI_COLOR_MAP:
						current_fg = C64_ANSI_COLOR_MAP[b]
						current_line_text += local_ansi_seq(current_fg, "0" if disp_m == "PUA_PETSCII" else current_fg)
						continue
					elif b == 18: reverse_mode = True; continue
					elif b == 146: reverse_mode = False; continue
					elif b == 14: lowercase_mode = True; continue
					elif b == 142: lowercase_mode = False; continue
					elif b == 13:
						reverse_mode = False
						needed_padding = 40 - col_counter
						rendered_rows.append(current_line_text + (" " * needed_padding) + "\033[0m")
						current_line_text = local_ansi_seq(current_fg); col_counter = 0; continue
						
					if disp_m == "PUA_PETSCII":
						# FIXED GLOBAL BLANK SYMBOLS SUPPRESSION: Converts ALL uninitialized zero bytes 
						# uniformly into clear space cells across the entire file stream to wipe out gold artifacts!
						if b == 0x00:
							current_line_text += " "
						else:
							sc = b
							q_base = 0xE100 if lowercase_mode else 0xE000
							if reverse_mode: q_base += 0x0200
							current_line_text += chr(q_base + sc)

					else:
						# FIXED HIGH-RESOLUTION UNICODE TRANSPILER: Removes trailing space distortion entirely!
						if 0x40 <= b <= 0x5F: char_glyph = chr(b).upper() if lowercase_mode else chr(b).lower()
						elif 0xC0 <= b <= 0xDF: char_glyph = chr(b - 0x40).upper() if lowercase_mode else chr(b - 0x40).lower()
						else: char_glyph = C64_UNICODE_FALLBACK_ROM.get(b, chr(b) if 32 <= b <= 126 else " ")
						
						# Advanced solid cell bounding block injection for structural graphics stability
						if b == 0x20 and reverse_mode:
							current_line_text += f"\x1b[0;48;5;{current_fg};38;5;{current_fg}m█"
						else:
							# FIXED INDENTATION: Aligned at level 32 spaces to clear the indentation error!
							if reverse_mode:
								current_line_text += f"\x1b[0;48;5;{current_fg};38;5;0m" + char_glyph
							else:
								current_line_text += f"\x1b[0;48;5;0;38;5;{current_fg}m" + char_glyph
								
					col_counter += 1
					if col_counter == 40:
						rendered_rows.append(current_line_text + "\033[0m")
						current_line_text = local_ansi_seq(current_fg); col_counter = 0
						
			# FIXED LOCATION: Compiles your raw file data blocks cleanly into a 16-byte hex structure
			if disp_m == "HEX_DUMP":
				rendered_rows = []
				for base_offset in range(0, len(raw_payload), 16):
					chunk = raw_payload[base_offset : base_offset + 16]
					hex_str = " ".join(f"{b:02X}" for b in chunk).ljust(47)
					ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
					row_line = f"\x1b[0;38;5;3m${base_offset:04X}:	\x1b[0;38;5;15m{hex_str}  \x1b[0;38;5;14m{ascii_str}"
					rendered_rows.append(row_line)
			elif current_line_text:
				rendered_rows.append(current_line_text + "\033[0m")
				
			if not rendered_rows: rendered_rows = ["--- EMPTY ---"]
			
			# --- VIEW DESIGN LAYER C: NATIVE CONSOLE INTERACTION BLITTING ---
			curses.def_prog_mode(); curses.endwin()
			os.system('cls' if os.name == 'nt' else 'clear')
			
			total_rows = len(rendered_rows)
			current_top_row = v_ctx.get("scroll_row", 0)
			
			# FIXED HEADER TELEMETRY: Dynamically adjusts display panel string text descriptions
			if disp_m == "HEX_DUMP":
				status_str = "HEXADECIMAL: BINARY"
				mode_lbl = "HEX BUF VIEW"
			else:
				status_str = "LOWERCASE: TEXT" if lowercase_mode else "UPPERCASE: GRAPHICS"
				mode_lbl = disp_m
				
			filename = v_ctx.get("file_name", "UNKNOWN")
		
			# FIXED: Dynamic column scaling adapts cleanly to wide monitor environments to prevent label wrapping
			line1 = f" Casing Status: {status_str:<20} | Total Rows: {total_rows:<5}".ljust(w - 1)
			
			if disp_m == "HEX_DUMP":
				line2 = f" [Q] or [ESC] : Return to Menu Layout panes ".ljust(w - 1)
			else:
				line2 = f" [C]: Toggle Active Casing Mode  │  [Q] or [ESC] : Return to Menu Panels ".ljust(w - 1)
				
			line3 = f" [ARROWS]: Scroll View Up/Down  │	 Viewing Virtual File: '{filename.upper()}' ({mode_lbl})".ljust(w - 1)
			
			# FIXED: Synchronize direct console outputs to cleanly flush dashboard text headers
			sys.stdout.write("\033[H\033[7m" + line1 + "\033[0m\n")
			sys.stdout.write("\033[7m" + line2 + "\033[0m\n")
			sys.stdout.write("\033[7m" + line3 + "\033[0m\n")
			
			display_end = min(current_top_row + 20, total_rows)
			for r in range(current_top_row, display_end):
				sys.stdout.write(f" {rendered_rows[r]}\n")
			if (display_end - current_top_row) < 20:
				for _ in range(20 - (display_end - current_top_row)):
					sys.stdout.write(" " * 45 + "\n")
			# FIXED: Dynamically match the terminal window width to prevent NameError template crashes
			sys.stdout.write("-" * (w - 1) + "\n")
			sys.stdout.flush()
			
			import msvcrt
			ch = msvcrt.getch()
			if ch in (b'\x00', b'\xe0'):
				ch2 = msvcrt.getch()
				if ch2 == b'H' and current_top_row > 0: v_ctx["scroll_row"] = current_top_row - 1
				elif ch2 == b'P' and current_top_row + 20 < total_rows: v_ctx["scroll_row"] = current_top_row + 1
			else:
				# FIXED: Unified Windows msvcrt capture layer to accept both 'q' or the ESC byte (b'\x1b')
				if ch == b'\x1b':
					key_char = 'q'
				else:
					key_char = ch.decode('latin-1', errors='ignore').lower()

				if key_char == 'q':
					stdscr.refresh()
					curses.reset_prog_mode()
					app_state["menu_mode"] = "PANELS"
				elif key_char == 'c':
					# FIXED: Invert the live toggle key state directly inside the context dictionary!
					v_ctx["lowercase_toggle"] = not v_ctx.get("lowercase_toggle", True)
			continue


		
		# --- IF NOT IN VIEWER, THE STANDARD CODES RESUME DOWN BELOW ---


		# FIXED: Enforce a strict boundary preventing Pygame from hijacking 
		# or overwriting native text viewports while an active file view track is running!
		if app_state["visual_mode"] == "PETSCII" and app_state.get("menu_mode") not in ["VIEWER", "EDITOR", "PYGAME_VIEWER"]:
			app_state["menu_mode"] = "PYGAME_PANELS"
			PygameVisualEngine.launch_graphical_mirror(app_state, stdscr)
			app_state["visual_mode"] = "STANDARD"
			app_state["menu_mode"] = "PANELS"
			stdscr.clear()
			curses.curs_set(0)



		# Standard Curses painting matrix loops
		# --- UNIFIED NATIVE CURSES VIEWPORT ROUTER MATRIX ---
		current_tui_view = app_state.get("menu_mode")
		if current_tui_view == "EDITOR":
			TUISectorEditorRenderer.paint_editor_workspace(stdscr, app_state["editor_state"])
				# --- UNIFIED NATIVE CURSES VIEWPORT ROUTER MATRIX ---
		current_tui_view = app_state.get("menu_mode")
		if current_tui_view == "EDITOR":
			TUISectorEditorRenderer.paint_editor_workspace(stdscr, app_state["editor_state"])
		elif current_tui_view == "BAM_EDITOR":
			TUIBAMEditorRenderer.paint_bam_editor_workspace(stdscr, app_state.get("bam_editor_state", {}))
		elif current_tui_view == "GCR_VIEWER":
			# FIXED: Hook up our low-level diagnostic tool straight into your rendering core!
			TUIRendererGCRViewer = app_state.get("gcr_viewer_state", {})
			TUIGCRViewerRenderer.paint_gcr_viewer_workspace(stdscr, TUIRendererGCRViewer)
		elif current_tui_view == "VIEWER":
			v_ctx = app_state.get("viewer_runtime_context", {})
		elif current_tui_view == "VIEWER":
			v_ctx = app_state.get("viewer_runtime_context", {})
			payload = v_ctx.get("payload", b"")
			start_r = v_ctx.get("scroll_row", 0)
			
			# Safe assignment tracking configurations
			disp_m = v_ctx.get("display_mode", "PROMPT")
			
			stdscr.erase()
			stdscr.attron(curses.color_pair(2))


			
			# If the user is looking at the initial picker prompt, bypass text drawing maps
			if disp_m == "PROMPT":
				pass
			else:
				# Calculate active casing indicators dynamically straight from your layout context keys
				is_lowercase = v_ctx.get("lowercase_toggle", True)
				status_text = "LOWERCASE: TEXT" if is_lowercase else "UPPERCASE: GRAPHICS"
				
				# Render a crisp, custom header bar tailored exclusively for active file pagers
				stdscr.addstr(1, 2, f"TUI FILE VIEW ACTIVE: {v_ctx.get('file_name', 'UNKNOWN').upper()} │ Casing Status: {status_text}", curses.A_BOLD)
				stdscr.addstr(2, 2, f"Translation Mode: {disp_m} │ [ARROWS] Scroll │ [C] Toggle Casing │ [ESC] Exit View", curses.A_NORMAL)
				stdscr.addstr(3, 2, "─" * 76)
			
			text_lines = []
			if disp_m == "TUI_ASCII":
				try: text_lines = payload.decode('utf-8', errors='replace').splitlines()
				except Exception: text_lines = ["[! ERROR: File stream unreadable via text drivers ]"]
			elif disp_m == "TUI_PETSCII_ANSI":
				for chunk_off in range(0, len(payload), 40):
					raw_chunk = payload[chunk_off : chunk_off + 40]
					cleaned_bytes = bytearray([b for b in raw_chunk if b >= 32 and not (128 <= b <= 159)])
					text_lines.append(PETSCIIDecoder.decode_name(cleaned_bytes))
					
			elif disp_m == "PUA_PETSCII": # Match your authentic original layout engine strings perfectly
				is_lowercase = v_ctx.get("lowercase_toggle", True)
				for chunk_off in range(0, len(payload), 40):
					raw_chunk = payload[chunk_off : chunk_off + 40]
					decoded_chars = []
					for b in raw_chunk:
						if b == 0x20 or b == 0xA0:
							decoded_chars.append(" ")
							continue
						if b < 32 or (128 <= b <= 159):
							continue
						
						# Apply your original character sets bitwise shifts dynamically
						if is_lowercase:
							if 65 <= b <= 90: decoded_chars.append(chr(0xEE00 + b - 64))
							elif 97 <= b <= 122: decoded_chars.append(chr(0xEE00 + b - 96))
							elif 193 <= b <= 218: decoded_chars.append(chr(0xEE00 + b - 128))
							else: decoded_chars.append(chr(0xEE00 + b))
						else:
							if 65 <= b <= 90: decoded_chars.append(chr(0xEE00 + b))
							elif 97 <= b <= 122: decoded_chars.append(chr(0xEE00 + b - 32))
							elif 193 <= b <= 218: decoded_chars.append(chr(0xEE00 + b - 64))
							else: decoded_chars.append(chr(0xEE00 + b))
					
					# FIXED: Indent string collection cleanly inside your parent loop boundaries
					text_lines.append("".join(decoded_chars))

					
			elif disp_m == "TUI_HEX":
				for chunk_off in range(0, len(payload), 16):
					row_bytes = payload[chunk_off : chunk_off + 16]
					hex_part = " ".join(f"{b:02X}" for b in row_bytes)
					ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in row_bytes)
					text_lines.append(f"${chunk_off:04X}: {hex_part:<48} │ {ascii_part}")

			# Print your compiled rows safely offset below your custom header panel
			content_row_offset = 4 if disp_m != "PROMPT" else 3
			for l_idx in range(min(20, len(text_lines) - start_r)):
				stdscr.addstr(content_row_offset + l_idx, 2, text_lines[start_r + l_idx][:76])
				
			stdscr.refresh()
			
			# Isolated input listeners for scrolling and keyboard hotkeys
			stdscr.timeout(100)
			try:
				v_key = stdscr.getch()
				if v_key == 27 or v_key == ord('q') or v_key == ord('Q'):
					app_state["menu_mode"] = "PANELS"
				elif v_key == curses.KEY_DOWN and start_r < len(text_lines) - 20:
					v_ctx["scroll_row"] = start_r + 1
				elif v_key == curses.KEY_UP and start_r > 0:
					v_ctx["scroll_row"] = start_r - 1
				elif v_key == ord('c') or v_key == ord('C'):
					# Capture character toggles to shift your active text layers instantly
					v_ctx["lowercase_toggle"] = not v_ctx.get("lowercase_toggle", True)
			except KeyboardInterrupt:
				app_state["menu_mode"] = "PANELS"
		else:
			# Default: draw standard dual sidebar dashboards
			TUIRenderer.paint_complete_screen(stdscr, app_state)
		
		# --- FIXED STEP 1: NATIVE CURSES DROPDOWN MENUS OVERLAY CONTROLLER ---
		if app_state["menu_mode"] == "MENU":
			active_side_key = app_state["active_side"]
			panel_dict = app_state[active_side_key]
			m_header_idx = app_state.get("active_menu_header_idx", 0)
			m_item_idx = app_state.get("active_menu_item_idx", 0)
			TUIDropDownMenu.draw_menu_card(stdscr, m_header_idx, m_item_idx, panel_dict, app_state)
			
			# Commit the menu pixels over the panels layer and pause the 100ms stutter loop
			stdscr.refresh()
			stdscr.timeout(-1)
		else:
			# Maintain highly responsive backgrounds when just browsing lists
			stdscr.timeout(100)
		
		try:
			key_stroke = stdscr.getch()
		except KeyboardInterrupt:
			break
		# --- NATIVE FULLSCREEN CURSES SECTOR EDITOR INTERCEPT ROUTINE ---
		if app_state.get("menu_mode") == "EDITOR":
			# FIXED: Pulled tracking context uniformly out of our synchronized data register state
			ctx = app_state.get("editor_state", {})
			c_off = ctx.get("cursor_offset", 0)
			active_p_key = app_state["active_side"]
			panel_obj = app_state[active_p_key]
			active_handler = ctx.get("vfs_handler")

			if key_stroke == ord('q') or key_stroke == ord('Q') or key_stroke == 27:
				app_state["menu_mode"] = "PANELS"
				app_state["command_buffer"] = "Returned cleanly from Sector Editor."
				continue
			elif key_stroke == curses.KEY_LEFT:
				ctx["cursor_offset"] = (c_off - 1) % 256; continue
			elif key_stroke == curses.KEY_RIGHT:
				ctx["cursor_offset"] = (c_off + 1) % 256; continue
			elif key_stroke == curses.KEY_UP:
				ctx["cursor_offset"] = (c_off - 16) % 256; continue
			elif key_stroke == curses.KEY_DOWN:
				ctx["cursor_offset"] = (c_off + 16) % 256; continue
			elif key_stroke in [ord('+'), ord('=')]:
				if active_handler:
					try:
						fmt = ctx.get("format_type", "D64")
						ct, cs = ctx["track"], ctx["sector"]
						
						# Compute sector limits for the current track index natively
						total_sectors = ImageGeometryRegistry.get_sectors_in_track(fmt, ct)
						
						ns = cs + 1
						nt = ct
						if ns >= total_sectors:
							ns = 0
							nt += 1
						
						# Enforce the hard ceiling boundaries of the active drive chassis profile
						if nt <= ctx["max_track"]:
							ctx["track"], ctx["sector"] = nt, ns
							ctx["buffer"] = bytearray(active_handler.read_virtual_sector(nt, ns))
							ctx["cursor_offset"] = 0
							ctx["status_msg"] = f"SUCCESS: Stepped forward to Track {nt} Sector {ns}."
						else:
							ctx["status_msg"] = "ALERT: Upper partition threshold boundary reached. Cannot step forward."
					except Exception as e:
						ctx["status_msg"] = f"NAV FAULT: {str(e)}"
				else:
					ctx["status_msg"] = "DRV ERROR: Active Virtual Filesystem driver profile not initialized."
				continue

			elif key_stroke == ord('-'):
				if active_handler:
					try:
						fmt = ctx.get("format_type", "D64")
						ct, cs = ctx["track"], ctx["sector"]
						
						ps = cs - 1
						nt = ct
						if ps < 0:
							nt -= 1
							if nt >= 1:
								# Dynamically determine the maximum sector envelope for the new track
								ps = ImageGeometryRegistry.get_sectors_in_track(fmt, nt) - 1
						
						# Enforce the absolute lower boundary floor (Track 1, Sector 0)
						if nt >= 1 and ps >= 0:
							ctx["track"], ctx["sector"] = nt, ps
							ctx["buffer"] = bytearray(active_handler.read_virtual_sector(nt, ps))
							ctx["cursor_offset"] = 0
							ctx["status_msg"] = f"SUCCESS: Stepped backward to Track {nt} Sector {ps}."
						else:
							ctx["status_msg"] = "ALERT: Lower hardware track boundary reached. Cannot step backward."
					except Exception as e:
						ctx["status_msg"] = f"NAV FAULT: {str(e)}"
				else:
					ctx["status_msg"] = "DRV ERROR: Active Virtual Filesystem driver profile not initialized."
				continue
			elif key_stroke == ord('j') or key_stroke == ord('J'):
				if active_handler:
					try:
						# FIXED: Natively resolve bounds relative to the current image file format type (D64, DNP, etc.)
						fmt = ctx.get("format_type", "D64")
						
						tgt_track = ctx["buffer"][ctx["cursor_offset"]]
						tgt_sector = ctx["buffer"][(ctx["cursor_offset"] + 1) % 256]
						
						# Dynamically calculate sector limits for this track using the current format profile
						max_sectors_limit = ImageGeometryRegistry.get_sectors_in_track(fmt, tgt_track)
						
						if 1 <= tgt_track <= ctx["max_track"] and 0 <= tgt_sector < max_sectors_limit:
							ctx["buffer"] = bytearray(active_handler.read_virtual_sector(tgt_track, tgt_sector))
							ctx["track"], ctx["sector"] = tgt_track, tgt_sector
							ctx["cursor_offset"] = 0
							ctx["status_msg"] = f"SUCCESS: Followed sector pointer warp link to Track {tgt_track} Sector {tgt_sector}."
						else:
							ctx["status_msg"] = f"ALERT: Byte pointer T:{tgt_track} S:{tgt_sector} references out-of-bounds sectors."
					except Exception as e:
						ctx["status_msg"] = f"NAV FAULT: Pointer chase action failed. {str(e)}"
				else:
					ctx["status_msg"] = "DRV ERROR: Active Virtual Filesystem driver profile not initialized."
				continue

			elif key_stroke == ord('r') or key_stroke == ord('R'):
				live_rows, live_cols = stdscr.getmaxyx()
				
				curses.flushinp()
				curses.echo()
				stdscr.timeout(-1)
				
				prompt_msg = "FORCE MANUALLY READ TARGET COORDINATES (Track,Sector): "
				stdscr.addstr(live_rows - 2, 2, prompt_msg.ljust(live_cols - 4), curses.color_pair(3))
				stdscr.refresh()
				
				input_bytes = stdscr.getstr(live_rows - 2, 2 + len(prompt_msg), 12)
				
				curses.noecho()
				stdscr.timeout(100)
				
				if active_handler:
					try:
						# FIXED: Parse parameters using dynamic format types (D64 vs DNP)
						fmt = ctx.get("format_type", "D64")
						
						raw_input_str = input_bytes.decode('utf-8', errors='ignore').strip()
						t_str, s_str = raw_input_str.split(",")
						nt, ns = int(t_str.strip()), int(s_str.strip())
						
						# Dynamically compute geometry parameters directly from your mounted chassis specifications
						if 1 <= nt <= ctx["max_track"] and 0 <= ns < ImageGeometryRegistry.get_sectors_in_track(fmt, nt):
							ctx["track"], ctx["sector"] = nt, ns
							ctx["buffer"] = bytearray(active_handler.read_virtual_sector(nt, ns))
							ctx["cursor_offset"] = 0
							ctx["status_msg"] = f"READ REKICK SUCCESS: Loaded Sector T:{nt} S:{ns}."
						else:
							ctx["status_msg"] = f"ALERT: Coordinates T:{nt} S:{ns} invalid for {fmt} geometry profile."
					except Exception:
						ctx["status_msg"] = "FAIL: Invalid entry formatting parameters. Try format: 18,1"
				else:
					ctx["status_msg"] = "DRV ERROR: Active Virtual Filesystem driver profile not initialized."
				
				stdscr.clear()
				continue

			elif key_stroke == ord('t') or key_stroke == ord('T'):
				stdscr.timeout(-1); curses.echo(); curses.flushinp()
				stdscr.addstr(29, 2, " " * 75, curses.color_pair(5))
				stdscr.addstr(29, 2, "INJECT STRING DATA CHARACTERS: ", curses.color_pair(5))
				try:
					inp = stdscr.getstr(29, 33, 30).decode('utf-8')
					for i, char in enumerate(inp): ctx["buffer"][(c_off + i) % 256] = ord(char) & 0xFF
					ctx["status_msg"] = "SUCCESS: String bytes written to block memory buffer."
				except Exception: pass
				curses.noecho(); stdscr.timeout(100); continue
			elif key_stroke == ord('@'):
				stdscr.timeout(-1); curses.echo(); curses.flushinp()
				stdscr.addstr(29, 2, " " * 75, curses.color_pair(5))
				stdscr.addstr(29, 2, "OVERWRITE CELL HEX BYTE (e.g. A0): ", curses.color_pair(5))
				try:
					inp = stdscr.getstr(29, 37, 2).decode('utf-8').strip()
					ctx["buffer"][c_off] = int(inp, 16) & 0xFF
					ctx["status_msg"] = f"SUCCESS: Offset ${c_off:02X} updated to ${inp.upper()}."
				except Exception: ctx["status_msg"] = "FAIL: Invalid hex byte execution parameters."
				curses.noecho(); stdscr.timeout(100); continue
			elif key_stroke == ord('w') or key_stroke == ord('W'):
				# Grab the active disk panel workspace currently targeted by the cursor
				active_panel_side = app_state.get("active_panel", "left")
				active_disk_plugin = app_state[active_panel_side].get("vfs_handler")

				if active_disk_plugin is not None:
					# FIXED: Pull everything directly from the true live 'ctx' object already in scope!
					current_t = ctx.get("track", 18)
					current_s = ctx.get("sector", 0)
					modified_buffer = ctx.get("buffer")

						
					if modified_buffer and len(modified_buffer) == 256:

						# Execute direct virtual sector commit pass!
						success = active_disk_plugin.write_virtual_sector(current_t, current_s, modified_buffer)
						
						if success:
							if success == "NO_CHANGE":
								# Guard matched! Display a warning message reporting that no changes were detected
								ctx["status_msg"] = f"NOTICE: Sector T:{current_t} S:{current_s} is unchanged. File save skipped."
							else:
								# True change committed!
								ctx["status_msg"] = f"SUCCESS: Sector T:{current_t} S:{current_s} modified and saved permanently!"
							app_state["command_buffer"] = ctx["status_msg"]
						else:
							ctx["status_msg"] = f"ERROR: VFS handler rejected the write pass for Track {current_t} Sector {current_s}."
							app_state["command_buffer"] = ctx["status_msg"]

					else:
						# Diagnostic ticker update to report if buffer variables are missing or size-mismatched
						buf_len = len(modified_buffer) if modified_buffer else "None"
						app_state["command_buffer"] = f"FAULT: Write aborted. Buffer key mismatch or invalid size ({buf_len} bytes)."
				else:
					app_state["command_buffer"] = "FAULT: No active virtual disk container mounted to modify."
				continue

		# --- NATIVE FULLSCREEN CURSES BAM EDITOR INTERCEPT ROUTINE ---
		if app_state.get("menu_mode") == "BAM_EDITOR":
			ctx = app_state.get("bam_editor_state", {})
			if not ctx:
				app_state["menu_mode"] = "PANELS"
				continue

			active_handler = ctx.get("vfs_handler")
			cur_t = ctx.get("cursor_track", 1)
			cur_s = ctx.get("cursor_sector", 0)
			max_t = ctx.get("max_track", 35)
			view_height = 16

			# Handle integer and string keystrokes cleanly from your main loop architecture
			try:
				key_char = chr(key_stroke) if isinstance(key_stroke, int) and 32 <= key_stroke <= 126 else ""
			except Exception:
				key_char = ""

			# Q or ESC returns to the dual-pane workspace panels view
			if key_stroke == ord('q') or key_stroke == ord('Q') or key_stroke == 27:
				app_state["menu_mode"] = "PANELS"
				app_state["command_buffer"] = "Returned cleanly from BAM Editor."
				continue

			elif key_stroke == curses.KEY_UP:
				if cur_s > 0:
					ctx["cursor_sector"] -= 1
					if ctx["cursor_sector"] < ctx["top_visible_sector"]:
						ctx["top_visible_sector"] = ctx["cursor_sector"]
				continue

			elif key_stroke == curses.KEY_DOWN:
				current_track_max = ctx["sector_map"].get(cur_t, 21)
				if cur_s < current_track_max - 1:
					ctx["cursor_sector"] += 1
					if ctx["cursor_sector"] >= ctx["top_visible_sector"] + view_height:
						ctx["top_visible_sector"] = ctx["cursor_sector"] - view_height + 1
				continue

			elif key_stroke == curses.KEY_LEFT:
				if cur_t > 1:
					ctx["cursor_track"] -= 1
					# HARDWARE AUTO-ADJUST: Prevent cursor out-of-bounds when shifting onto shorter track boundaries!
					target_track_max = ctx["sector_map"].get(ctx["cursor_track"], 21)
					if ctx["cursor_sector"] >= target_track_max:
						ctx["cursor_sector"] = target_track_max - 1
					if ctx["cursor_track"] < ctx["left_visible_track"]:
						ctx["left_visible_track"] = ctx["cursor_track"]
				continue

			elif key_stroke == curses.KEY_RIGHT:
				if cur_t < max_t:
					ctx["cursor_track"] += 1
					# HARDWARE AUTO-ADJUST: Same horizontal clamp safety check
					target_track_max = ctx["sector_map"].get(ctx["cursor_track"], 21)
					if ctx["cursor_sector"] >= target_track_max:
						ctx["cursor_sector"] = target_track_max - 1
					if ctx["cursor_track"] >= ctx["left_visible_track"] + 8:
						ctx["left_visible_track"] = ctx["cursor_track"] - 8 + 1
				continue

			elif key_stroke == ord(' ') or key_char == ' ':
				# SPACE BAR: Target the abstract manager state object to toggle bits natively!
				bam_mgr = ctx.get("bam_manager")
				if bam_mgr:
					bam_mgr.toggle_sector(cur_t, cur_s)
					ctx["dirty"] = True
				continue

			elif key_stroke == ord('w') or key_char == 'w' or key_char == 'W':
				# INTERCEPT THE W KEY COMMIT WRITE PASS ACTION ROUTINE!
				bam_mgr = ctx.get("bam_manager")
				if bam_mgr:
					max_y, max_x = stdscr.getmaxyx()
					prompt_y = max_y // 2
					prompt_x = max_x // 2 - 25
					
					stdscr.attron(curses.A_BOLD)
					stdscr.addstr(prompt_y - 2, prompt_x, "+" + "-" * 50 + "+")
					stdscr.addstr(prompt_y - 1, prompt_x, "| WRITE CHANGES TO DISK IMAGE CANVASES?			  |")
					stdscr.addstr(prompt_y,		prompt_x, "| Are you sure you want to write BAM updates? (Y/N)|")
					stdscr.addstr(prompt_y + 1, prompt_x, "+" + "-" * 50 + "+")
					stdscr.attroff(curses.A_BOLD)
					stdscr.refresh()
					
					conf_key = ""
					while conf_key not in ('y', 'Y', 'n', 'N', chr(27)):
						try:
							c_stroke = stdscr.getch()
							conf_key = chr(c_stroke) if 32 <= c_stroke <= 126 else ""
						except Exception:
							continue
							
					if conf_key in ('y', 'Y'):
						# User confirmed! Tell BAM manager to pack the bit arrays and write back to disk!
						bam_mgr.flush_bam_changes_to_media()
						
						# Dynamically synchronize your master driver's listing stats in real-time
						active_handler = bam_mgr.driver
						if active_handler and hasattr(active_handler, "list_directory"):
							active_handler.list_directory()
							
						ctx["dirty"] = False
						app_state["command_buffer"] = "SUCCESS: BAM maps written securely to disk container files metadata."
					else:
						app_state["command_buffer"] = "Write operation aborted cleanly by user selection."
						
					stdscr.clear()
				continue
				
		# --- NATIVE FULLSCREEN CURSES GCR TRACK STREAM VIEWER INTERCEPT ---
		if app_state.get("menu_mode") == "GCR_VIEWER":
			ctx = app_state.get("gcr_viewer_state", {})
			if not ctx:
				app_state["menu_mode"] = "PANELS"
				continue

			active_handler = ctx.get("vfs_handler")
			cur_track = ctx.get("track", 18)
			scroll_offset = ctx.get("scroll_offset", 0)
			raw_gcr_len = len(ctx.get("raw_stream", b""))

			try:
				key_char = chr(key_stroke) if isinstance(key_stroke, int) and 32 <= key_stroke <= 126 else ""
			except Exception:
				key_char = ""

			# Q or ESC returns to the dual-pane workspace panels view
			if key_stroke == ord('q') or key_stroke == ord('Q') or key_stroke == 27:
				app_state["menu_mode"] = "PANELS"
				app_state["command_buffer"] = "Returned cleanly from Low-Level GCR Bitstream Viewer."
				continue

			# Page Down / Arrow Down - Scroll text stream forward
			elif key_stroke == curses.KEY_DOWN or key_stroke == ord('s') or key_stroke == ord('S'):
				if scroll_offset + 16 < raw_gcr_len:
					ctx["scroll_offset"] += 16
				continue
				
			# Page Up / Arrow Up - Scroll text stream backward
			elif key_stroke == curses.KEY_UP or key_stroke == ord('w') or key_stroke == ord('W'):
				if scroll_offset - 16 >= 0:
					ctx["scroll_offset"] -= 16
				continue	
				
			# Page Down keys - Skip forward by a full expanded screen block
			elif key_stroke == curses.KEY_NPAGE:
				# 32 rows * 16 bytes per row = 512 bytes per screen jump block pass
				if scroll_offset + 512 < raw_gcr_len:
					ctx["scroll_offset"] += 512
				continue

			# Page Up keys - Skip backward by a full expanded screen block
			elif key_stroke == curses.KEY_PPAGE:
				if scroll_offset - 512 >= 0:
					ctx["scroll_offset"] -= 512
				else:
					ctx["scroll_offset"] = 0
				continue

			# Plus Key (+) - Increment target position by a 0.5 physical half-track step
			elif key_stroke in (ord('+'), ord('=')):
				if cur_track < 42.5:
					ctx["track"] = cur_track + 0.5
					if active_handler and hasattr(active_handler, "get_raw_gcr_track_stream"):
						ctx["raw_stream"] = bytearray(active_handler.get_raw_gcr_track_stream(ctx["track"]))
					ctx["scroll_offset"] = 0
				continue

			# Minus Key (-) - Decrement target position by a 0.5 physical half-track step
			elif key_stroke in (ord('-'), ord('_')):
				if cur_track > 1.0:
					ctx["track"] = cur_track - 0.5
					if active_handler and hasattr(active_handler, "get_raw_gcr_track_stream"):
						ctx["raw_stream"] = bytearray(active_handler.get_raw_gcr_track_stream(ctx["track"]))
					ctx["scroll_offset"] = 0
				continue

		# FIXED: Core Event Router — Handles ESC for menus/directories, passes Q/F10 to native code rows
		if key_stroke == ord('q') or key_stroke == ord('Q') or key_stroke == 27:
			if app_state.get("menu_mode") == "MENU":
				app_state["menu_mode"] = "PANELS"  # Safe close dropdown overlay layers cleanly
			else:
				active_side = app_state.get("active_side", "left")
				active_panel = app_state[active_side]
				
				# Natively step out of active virtual containers back to host OS filesystem paths safely
				if active_panel.get("is_in_container"):
					active_panel["current_path"] = active_panel.get("backed_host_path", os.getcwd())
					active_panel["file_list"] = HostSystemScanner.scan_directory(active_panel["current_path"])
					active_panel["free_space_msg"] = TUIController.get_host_free_space_string(active_panel["current_path"])
					active_panel["is_in_container"] = False
					active_panel["vfs_handler"] = None
					active_panel["disk_label_msg"] = None
					active_panel["highlight_index"] = 0
					active_panel["top_visible_row"] = 0
					app_state["command_buffer"] = "VFS Dropped: Returned cleanly to host filesystem views."
			continue  # Block handled safely, re-kick the orchestration loop refresh cycle

		# Exit routine passes (Enforces	 F10 breaking gates)
		if key_stroke == (curses.KEY_F0 + 10):
			# If a menu card is open, Escape closes the menu instead of killing the program!
			if app_state["menu_mode"] == "MENU":
				app_state["menu_mode"] = "PANELS"
				continue
			break

		active_side = app_state["active_side"]
		panel = app_state[active_side]

		# --- FIXED STEP 1: RESTORE STABLE MENU CHOICE ROUTING MATRIX ---
		if app_state["menu_mode"] == "MENU":
			# FIXED: Dynamically capture the true live active panel context state natively right on input loop pass!
			# This stops stale .lnx metadata profile properties from locking out your C64 features.
			active_p_side = app_state.get("active_side", "left")
			m_idx = app_state.get("active_menu_header_idx", 0)
			i_idx = app_state.get("active_menu_item_idx", 0)
			menu_side = "left" if m_idx == 0 else "right" if m_idx == 4 else active_p_side
			live_panel_state = app_state[menu_side]
			menu_handler = live_panel_state.get("vfs_handler")
			
			# Evaluate current menu target panel parameters cleanly
			show_editor = live_panel_state.get("is_in_container", False) and menu_handler is not None and not live_panel_state.get("no_sector_editor", False)
			
			if m_idx == 0 or m_idx == 4:
				if show_editor:
					fmt = getattr(menu_handler, "format_type", "HOST")
					items = [" Rescan Directory ", " View Sector Editor ", " View BAM Editor "]
					if fmt == "G64":
						items.append(" View GCR Stream ")
					if fmt == "D81":
						items.append(" Create 1581 Partition ")
				else:
					items = [" Rescan Directory "]

			elif m_idx == 1:
				items = [" View File ", " Copy File Out ", " Delete Node "]
			elif m_idx == 2:
				items = [" Mount Archive ", " Run Script Macro "]
			elif m_idx == 3:
				items = [" Settings ", " Dev Mode ", " ───────────────── ", " Credits Info "]
			else:
				items = [" Close Sub-Menu "]

			if key_stroke == curses.KEY_LEFT:
				app_state["active_menu_header_idx"] = (m_idx - 1) % 5
				app_state["active_menu_item_idx"] = 0
				continue
			elif key_stroke == curses.KEY_RIGHT:
				app_state["active_menu_header_idx"] = (m_idx + 1) % 5
				app_state["active_menu_item_idx"] = 0
				continue
			elif key_stroke == curses.KEY_UP:
				app_state["active_menu_item_idx"] = (i_idx - 1) % len(items)
				continue
			elif key_stroke == curses.KEY_DOWN:
				app_state["active_menu_item_idx"] = (i_idx + 1) % len(items)
				continue
			elif key_stroke == 10 or key_stroke == 13 or key_stroke == 343:	 # Enter pressed inside dropdown menu card
				if "─────" in items[i_idx]:
					continue
				# Close the menu overlay since an action choice has been made
				
				# FIXED: Standardized variable name assignment to 'app_state' to eliminate the NameError crash
				if app_state.get("visual_mode") != "PETSCII":
					if m_idx == 3 and i_idx == 0:
						TUIDropDownMenu.show_settings_popup(stdscr, app_state)
						continue
					elif m_idx == 3 and i_idx == 1:
						TUIDropDownMenu.show_dev_mode_popup(stdscr, app_state)
						continue
					elif m_idx == 3 and i_idx == 3:
						TUIDropDownMenu.show_credits_popup(stdscr)
						continue
					elif (m_idx == 0 or m_idx == 4) and i_idx == 1:	 # View Sector Editor action chosen
						# FIXED: Explicitly target the configuration dictionary matching the chosen menu index
						target_side = "left" if m_idx == 0 else "right"
						menu_panel = app_state[target_side]
						# Strictly verify that THIS specific panel actually contains an active mounted image container
						if menu_panel.get("is_in_container") and not menu_panel.get("no_sector_editor", False):
							handler_instance = menu_panel.get("vfs_handler")
							driver_class_name = handler_instance.__class__.__name__.upper()
							# FIXED: Queries the active panel's VFS handler directly for its encapsulated format type!
							fmt_type = getattr(panel.get("vfs_handler"), "format_type", "D64")
							start_t = handler_instance.default_dir_track
							start_s = handler_instance.default_dir_sector
							max_t = handler_instance.max_tracks_limit
							
							# FIXED: Names the storage state dictionary exactly what your Curses engine looks up to paint the screen panels!
							app_state["editor_state"] = {
								"archive_name": menu_panel["current_path"].split("//")[-1], 
								"format_type": fmt_type,
								"track": start_t, 
								"sector": start_s, 
								"max_track": max_t,
								"cursor_offset": 0, 
								"edit_mode": "NAV", 
								"status_msg": f"Sector Editor Active. Viewing {fmt_type} Hardware Canvas Profile Map.",
								"vfs_handler": handler_instance,
								"buffer": bytearray(handler_instance.read_virtual_sector(start_t, start_s))
							}
							app_state["menu_mode"] = "EDITOR"
							continue
					# =========================================================================
					# 🎯 CONTEXT INTERCEPT: CHOSEN DROP-DOWN ACTION IS PARTITION CREATION 🎯
					# This checks if the text string of the selected row index equals our wizard token.
					# =========================================================================
					# FIXED: Targets row index 3 directly, removing the undefined menu_items variable dependency!
					if i_idx == 3:
						# FIXED: Safely resolve and bind the active target side panel before pulling the handler!
						target_side = "left" if m_idx == 0 else "right"
						menu_panel = app_state[target_side]
						
						handler_instance = menu_panel.get("vfs_handler")
						if handler_instance and getattr(handler_instance, "format_type", "") == "D81":
							
							curses.curs_set(1) # Restore cursor visibility for field text entry fields
							
							# STAGE A: QUERY DYNAMIC DRIVE ACCESSIBLE GEOMETRY MATRIX
							eligible_tracks_matrix = handler_instance.get_partition_creation_track_matrix()
							
							active_track_cursor = 1
							for t in range(1, 81):
								if eligible_tracks_matrix.get(t) == ".":
									active_track_cursor = t
									break

							# --- PHASE 1 BOARD LOOP: ACQUIRE VALID STARTING TRACK ---
							start_track_selection = None
							while True:
								stdscr.erase()
								max_y, max_x = stdscr.getmaxyx()
								stdscr.box()
								stdscr.addstr(1, 2, "🔨 COMMODORE 1581 VIRTUAL PARTITION ARCHITECT ENGINE", curses.A_BOLD)
								stdscr.addstr(2, 2, "─" * (max_x - 4))
								stdscr.addstr(4, 2, "👉 STEP 1: Select Your Partition Starting Track Coordinate Boundary")
								stdscr.addstr(5, 2, "	(Use LEFT/RIGHT arrow keys, press [ENTER] to confirm selection lock-in)")

								window_start_t = max(1, min(69, active_track_cursor - 6))
								
								# FIXED: Standardized 7-character left-flush headers [1.26]
								track_num_line = "Track: "
								state_map_line = "State: "
								cursor_ptr_line = "	  "
								
								for t in range(window_start_t, window_start_t + 12):
									# Force every track component block to occupy exactly 4 horizontal columns [1.26]
									track_num_line += f" T{t:02d}"
									state_marker = eligible_tracks_matrix.get(t, "X")
									state_map_line += f"  {state_marker} "
									
									if t == active_track_cursor:
										cursor_ptr_line += " ▲ "
									else:
										# FIXED: Changed from 5 spaces to EXACTLY 4 spaces to match the header stride! [1.26]
										cursor_ptr_line += "	"
										
								stdscr.attrset(curses.A_NORMAL)
								stdscr.addstr(7, 2, " " * (max_x - 4))
								stdscr.addstr(8, 2, " " * (max_x - 4))
								stdscr.addstr(9, 2, " " * (max_x - 4))
								
								stdscr.addstr(7, 2, track_num_line, curses.A_BOLD)
								stdscr.addstr(8, 2, state_map_line) 
								stdscr.addstr(9, 2, cursor_ptr_line, curses.A_BLINK | curses.A_BOLD)

								stdscr.addstr(12, 2, "[.] = Free Track Available   [X] = Allocated / Fails 3-Track Look-Ahead Limit", curses.A_DIM)
								stdscr.addstr(14, 2, f"💡 Active Track Focus: Track {active_track_cursor} | Eligible: {'YES' if eligible_tracks_matrix.get(active_track_cursor) == '.' else 'NO'}")
								stdscr.refresh()
								
								ch = stdscr.getch()
							
								if ch == curses.KEY_LEFT and active_track_cursor > 1:
									active_track_cursor -= 1
								elif ch == curses.KEY_RIGHT and active_track_cursor < 80:
									active_track_cursor += 1
								elif ch in [10, 13, curses.KEY_ENTER]:
									if eligible_tracks_matrix.get(active_track_cursor) == ".":
										start_track_selection = active_track_cursor
										break
									else:
										stdscr.addstr(16, 2, "❌ ERROR: Target track is locked or lacks 3 sequential tracks look-ahead depth!", curses.color_pair(2) | curses.A_BOLD)
										stdscr.refresh()
										curses.napms(1200)
								elif ch == 27: # ESC key pressed [1.26]
									# FIXED: Erase menu overlays and return True immediately to escape!
									curses.curs_set(0)
									app_state["menu_mode"] = "NORMAL"
									return True

							# --- PHASE 2 BOARD LOOP: ACQUIRE VALID ENDING TRACK CEILING ---
							min_end_t = start_track_selection + 2
							active_end_cursor = min_end_t
							
							# === FIXED STEP 2: RAW ALLOCATION ENDING BOUNDARY CEILING PROBER === [1.13]
							end_eligible_matrix = {t: "X" for t in range(1, 81)}
							
							# Query the pure sector allocation matrix from the plugin (stripping the look-ahead rules)
							active_t_ctx = getattr(handler_instance, "current_dir_track", 40)
							max_parent_ceiling = 80 if active_t_ctx == 40 else getattr(handler_instance, "current_partition_end_track", 12)
							
							for t in range(min_end_t, max_parent_ceiling + 1):
								if t == 40:
									break # Track 40 is a hard physical wall for any partition spans
									
								# Inspect raw sub-BAM block allocation counters for this track [1.13]
								bam_sec = 1 if t <= 40 else 2
								log_t = t if t <= 40 else (t - 40)
								bam_data = handler_instance.read_virtual_sector(active_t_ctx, bam_sec)
								
								if not bam_data or len(bam_data) < 256:
									break
									
								t_offset = 16 + ((log_t - 1) * 6)
								free_sectors_count = int(bam_data[t_offset])
								
								# If we hit an un-cleared track that has data, the ceiling drops here [1.13]
								if free_sectors_count < 40:
									break
									
								end_eligible_matrix[t] = "."
									
							while True:
								stdscr.erase()
								stdscr.box()
								stdscr.addstr(1, 2, "🔨 COMMODORE 1581 VIRTUAL PARTITION ARCHITECT ENGINE", curses.A_BOLD)
								stdscr.addstr(2, 2, "─" * (max_x - 4))
								stdscr.addstr(4, 2, f"👉 STEP 2: Select Your Partition Ending Track Ceiling (Starting Track: {start_track_selection})")
								stdscr.addstr(5, 2, "	(Use LEFT/RIGHT arrow keys, press [ENTER] to confirm layout lock-in)")

								window_end_t = max(1, min(69, active_end_cursor - 6))
								
								# FIXED: Synchronized to matching 7-character headers for alignment
								track_num_line = "Track: "
								state_map_line = "State: "
								cursor_ptr_line = "	  "
								
								for t in range(window_end_t, window_end_t + 12):
									track_num_line += f" T{t:02d}"
									state_marker = end_eligible_matrix.get(t, "X")
									state_map_line += f"  {state_marker} "
									
									if t == active_end_cursor:
										cursor_ptr_line += " ▲ "
									else:
										cursor_ptr_line += "	"
										
								stdscr.attrset(curses.A_NORMAL)
								stdscr.addstr(7, 2, " " * (max_x - 4))
								stdscr.addstr(8, 2, " " * (max_x - 4))
								stdscr.addstr(9, 2, " " * (max_x - 4))
								
								stdscr.addstr(7, 2, track_num_line, curses.A_BOLD)
								stdscr.addstr(8, 2, state_map_line) 
								stdscr.addstr(9, 2, cursor_ptr_line, curses.A_BLINK | curses.A_BOLD)
								
								total_span_tracks = (active_end_cursor - start_track_selection) + 1
								calculated_blocks_size = (total_span_tracks - 1) * 40
								
								stdscr.addstr(12, 2, f"📊 Footprint Span: Tracks {start_track_selection} to {active_end_cursor} ({total_span_tracks} Total Tracks)")
								stdscr.addstr(13, 2, f"📊 Estimated Capacity Yield: {calculated_blocks_size} Blocks Free data space.")
								stdscr.refresh()
								
								ch = stdscr.getch()

								if ch == curses.KEY_LEFT and active_end_cursor > min_end_t:
									active_end_cursor -= 1
								elif ch == curses.KEY_RIGHT and end_eligible_matrix.get(active_end_cursor + 1) == ".":
									active_end_cursor += 1
								elif ch in [10, 13, curses.KEY_ENTER]:
									if end_eligible_matrix.get(active_end_cursor) == ".":
										end_track_selection = active_end_cursor
										break
								elif ch == 27: # ESC key pressed [1.26]
									# FIXED: Return True immediately to abort partition creation!
									curses.curs_set(0)
									app_state["menu_mode"] = "NORMAL"
									return True

							# --- PHASE 3 BOARD LOOP: METADATA DATA TEXT PROMPTS ---
							p_filename, p_label, p_id = "PARTITION", "PART TITLE", "82"
							
							def capture_text_field(prompt_str, max_len, default_val):
								stdscr.clear()
								stdscr.box()
								stdscr.addstr(2, 2, "📝 STEP 3: Enter Your Partition Configuration Descriptors Metadata", curses.A_BOLD)
								stdscr.addstr(4, 2, prompt_str)
								stdscr.addstr(5, 4, f"(Press [ENTER] to lock string value. Default: '{default_val}')")
								stdscr.move(4, len(prompt_str) + 3)
								stdscr.refresh()
								
								curses.echo()
								input_bytes = stdscr.getstr(4, len(prompt_str) + 3, max_len)
								curses.noecho()
								
								decoded_str = input_bytes.decode('utf-8', 'ignore').strip()
								return decoded_str if decoded_str else default_val

							p_filename = capture_text_field("↳ Enter Partition Filename (16 chars max): ", 16, p_filename)
							p_label	   = capture_text_field("↳ Enter Partition Volume Disk Label (16 chars max): ", 16, p_label)
							p_id	   = capture_text_field("↳ Enter 2-Character Disk Partition ID (2 chars max): ", 2, p_id)

							# --- PHASE 4 EXECUTION BLOCK: COMMIT TRACK BYTES ---
							stdscr.clear()
							stdscr.box()
							stdscr.addstr(3, 2, "🚀 INITIALIZING PHYSICAL HARDWARE FORMAT OPERATIONS...", curses.A_BLINK | curses.A_BOLD)
							stdscr.refresh()
							
							success = handler_instance.create_1581_partition_sectors(start_track_selection, end_track_selection, p_filename, p_label, p_id)
							
							if success:
								stdscr.addstr(5, 2, "🏆 SUCCESS: 1581 Partition formed and linked cleanly into directory files!", curses.color_pair(5) | curses.A_BOLD)
							else:
								stdscr.addstr(5, 2, "❌ CRITICAL ERROR: Hardware allocation compilation block processing loop failed!", curses.color_pair(2) | curses.A_BOLD)
								
							stdscr.refresh()
							curses.napms(2000)
							curses.curs_set(0)
							
							# Reset menu context flags and force-refresh active file listings
							handler_instance.list_directory()
							menu_panel["file_list"] = handler_instance.file_list
							app_state["menu_mode"] = "NORMAL"
							continue
				# =========================================================================

						else:
							app_state["command_buffer"] = f"CRITICAL: Cannot open editor. The {target_side.upper()} panel has no disk mounted."
							continue
					elif (m_idx == 0 or m_idx == 4) and i_idx == 2:	 # View BAM Editor action chosen
						target_side = "left" if m_idx == 0 else "right"
						menu_panel = app_state[target_side]
						
						if menu_panel.get("is_in_container") and not menu_panel.get("no_sector_editor", False):
							handler_instance = menu_panel.get("vfs_handler")
							
							# FIXED: Resolve the active directory track to dynamically load sub-BAM sectors! [1.13]
							active_bam_track = 40
							if handler_instance and getattr(handler_instance, "format_type", "") == "D81":
								active_bam_track = getattr(handler_instance, "current_dir_track", 40)
							
							# Instantiating our updated manager subsystem engine passing the localized target track
							bam_mgr = BAMManager(handler_instance, bam_track=active_bam_track)
							fmt_type = bam_mgr.params["format_type"]
							
							# FIXED: Assign the dynamic max track limit straight from our bounded manager instance!
							max_t = bam_mgr.params["max_tracks"]
							
							app_state["bam_editor_state"] = {
								"archive_name": menu_panel["current_path"].split("//")[-1],
								"format_type": fmt_type,
								"cursor_track": 1,
								"cursor_sector": 0,
								"top_visible_sector": 0,
								"left_visible_track": 1,
								"max_track": max_t,	 # Secure boundary clamp mapping lock
								"sector_map": bam_mgr.params["sector_map"],
								"bam_manager": bam_mgr,
								"status_msg": f"BAM Editor Active. Viewing partition T{active_bam_track} Grid buffer." if active_bam_track != 40 else f"BAM Editor Active. Viewing unified {fmt_type} Grid buffer.",
								"dirty": False
							}
							app_state["menu_mode"] = "BAM_EDITOR"
							continue
						else:
							app_state["command_buffer"] = f"CRITICAL: Cannot open BAM editor. The {target_side.upper()} panel has no disk mounted."
							continue
					elif (m_idx == 0 or m_idx == 4) and i_idx == 3:	 # View GCR Stream Viewer chosen
						target_side = "left" if m_idx == 0 else "right"
						menu_panel = app_state[target_side]
						handler_instance = menu_panel.get("vfs_handler")
						
						if menu_panel.get("is_in_container") and getattr(handler_instance, "format_type", "") == "G64":
							# Capture raw binary track 18 data stream immediately upon entry
							start_track = 18
							if hasattr(handler_instance, "get_raw_gcr_track_stream"):
								track_data, _ = handler_instance.get_raw_gcr_track_stream(start_track)
								raw_bytes = bytearray(track_data)
							else:
								raw_bytes = bytearray()
							
							app_state["gcr_viewer_state"] = {
								"archive_name": menu_panel["current_path"].split("//")[-1],
								"track": start_track,
								"scroll_offset": 0,
								"raw_stream": raw_bytes,
								"vfs_handler": handler_instance
							}
							app_state["menu_mode"] = "GCR_VIEWER"
							continue

					# COLUMN SELECTION MATRIX PASS 2: File Operations (View File Viewer HUD)
					elif m_idx == 1:
						target_side = "left" if app_state["active_side"] == "left" else "right"
						panel_obj = app_state[target_side]
						ledger = panel_obj.get("file_list", [])
						h_index = panel_obj.get("highlight_index", 0)
						
						if ledger and h_index < len(ledger):
							sel_file = ledger[h_index]
							
							# FIXED: Allows opening the dropdown list box whether you are browsing a virtual image OR a local host drive file!
							if i_idx == 0: # "View File" selection executed
								try:
									if panel_obj.get("is_in_container") and panel_obj.get("vfs_handler"):
										vfs_node = sel_file["vfs_meta"]
										payload = panel_obj["vfs_handler"].extract_file_bytes(vfs_node)
									else:
										# Stream straight off your local hard drive file!
										full_host_file_path = os.path.join(panel_obj["current_path"], sel_file["name"])
										with open(full_host_file_path, 'rb') as host_file_stream:
											payload = host_file_stream.read()
											
									app_state["viewer_runtime_context"] = {
										"file_name": sel_file["name"], 
										"payload": payload, 
										"display_mode": "PROMPT", 
										"scroll_row": 0, 
										"lowercase_toggle": True
									}
									app_state["menu_mode"] = "VIEWER"
									continue
								except Exception as err:
									app_state["command_buffer"] = f"LOAD FAULT: {str(err)}"
							app_state["menu_mode"] = "PANELS"
							continue

			app_state["menu_mode"] = "PANELS"



		# --- NATIVE TUI TEXT FILE CONTENT PAGER CONTROLLER ---

		# --- FIXED STEP 2: STABLE DUAL SIDEPANELS BROWSING KEYMAPS ---
		if key_stroke == 9: # TAB Key swaps active focus tracks
			app_state["active_side"] = "right" if active_side == "left" else "left"
		elif key_stroke == curses.KEY_UP:
			TUIController.process_scrolling_movement(panel, "UP", stdscr.getmaxyx())
		elif key_stroke == curses.KEY_DOWN:
			TUIController.process_scrolling_movement(panel, "DOWN", stdscr.getmaxyx())
		elif key_stroke == 10 or key_stroke == 13 or key_stroke == 343: # Enter pressed on directory panels rows
			# FIXED: All old duplicated code sections are swept out to run off our pristine, unified driver center core!
			active_side_key = app_state["active_side"]
			SharedVFSController.execute_file_activation(app_state, active_side_key)
			continue
		elif key_stroke == ord('m') or key_stroke == ord('M') or key_stroke == (curses.KEY_F0 + 2) or key_stroke == (curses.KEY_F0 + 9):
			# If we are already running in standard TUI mode, open the native Curses action dropdown overlays!
			if app_state["visual_mode"] == "STANDARD":
				app_state["menu_mode"] = "MENU"
				app_state["active_menu_header_idx"] = 0
				app_state["active_menu_item_idx"] = 0
			else:
				# Fallback: flag an instant video track handoff if PETSCII mode is active
				app_state["visual_mode"] = "PETSCII"


