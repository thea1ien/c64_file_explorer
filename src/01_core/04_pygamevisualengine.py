class PygameVisualEngine:
	"""Hardware-accelerated graphical interface mirroring our workspace architecture."""
	C64_PALETTE = {
		0: (0, 0, 0), 1: (255, 255, 255), 2: (136, 0, 0), 3: (170, 255, 238),
		4: (204, 68, 204), 5: (0, 204, 85), 6: (0, 0, 170), 7: (238, 238, 119),
		8: (221, 136, 85), 9: (102, 68, 0), 10: (255, 119, 119), 11: (51, 51, 51),
		12: (119, 119, 119), 13: (170, 255, 102), 14: (0, 136, 255), 15: (187, 170, 187)
	}

	@staticmethod
	def ascii_to_c64_screencode(text_str):
		screencodes = []
		for char in text_str:
			ascii_val = ord(char)
			if 65 <= ascii_val <= 90: 
				screencodes.append(ascii_val - 64)
			elif 97 <= ascii_val <= 122: 
				screencodes.append(ascii_val - 96)
			elif 32 <= ascii_val <= 63: 
				screencodes.append(ascii_val)
			else: 
				screencodes.append(0x20)
		return screencodes
		
	@staticmethod
	def launch_graphical_mirror(global_tui_state, stdscr):
		"""Spawns an interactive mirror environment displaying dual panels natively inside Pygame."""
		global sys
		import base64
		import io
		
		# FIXED: Explicitly parse and bind persistent config profiles directly to your active Pygame loop states upon bootup!
		config = ConfigurationManager.load_application_settings()
		if "respect_cbm_extensions" not in global_tui_state:
			global_tui_state["respect_cbm_extensions"] = config.get("respect_cbm_extensions", True)
		if "default_cbm_filetype" not in global_tui_state:
			global_tui_state["default_cbm_filetype"] = config.get("default_cbm_filetype", "PRG")
			
		stdscr.erase()
		stdscr.refresh()
		os.environ["SDL_RENDER_SCALE_QUALITY"] = "nearest"
		pygame.display.init()
		pygame.font.init()
		pygame.key.set_repeat(300, 50)
		
		char_w, char_h = 10, 16
		screen_w, screen_h = 80 * char_w, 32 * char_h
		screen = pygame.display.set_mode((screen_w, screen_h), pygame.SCALED | pygame.RESIZABLE)
		pygame.display.set_caption("C64 Explorer VFS - Graphical Panel Surface (Pixel Sharp)")
		
		try:
			full_b64_data = "".join(FONT_STREAM_ROM)
			clean_font_bytes = base64.b64decode(full_b64_data)
			font_memory_stream = io.BytesIO(clean_font_bytes)
			c64_font_obj = pygame.font.Font(font_memory_stream, 16)
		except Exception as font_load_err:
			global_tui_state["command_buffer"] = f"C64 GRAPHICS FAULT: {str(font_load_err)}"
			c64_font_obj = pygame.font.SysFont("monospace", 14, bold=True)

		font_obj = pygame.font.SysFont("monospace", 14, bold=True)
		clock = pygame.time.Clock()
		running_mirror = True
		while running_mirror:
			clock.tick(30)
			screen.fill(PygameVisualEngine.C64_PALETTE.get(14))
			m_mode_track = global_tui_state.get("menu_mode")
			if m_mode_track == "PYGAME_VIEWER":
				bg_color_tuple = PygameVisualEngine.C64_PALETTE.get(0)
			else:
				bg_color_tuple = PygameVisualEngine.C64_PALETTE.get(6)
			inner_rect = pygame.Rect(char_w * 2, char_h * 2, screen_w - (char_w * 4), screen_h - (char_h * 4))
			pygame.draw.rect(screen, bg_color_tuple, inner_rect)

			
			# --- TOP HEADER MENUBAR WORDS RASTERIZER ---
			if global_tui_state.get("menu_mode") != "PYGAME_VIEWER":
				headers_map = {0: "Left", 1: "File", 2: "Command", 3: "Options", 4: "Right"}
				menu_cols = {0: 2, 1: 12, 2: 22, 3: 35, 4: 48}
				for h_idx, h_text in headers_map.items():
					col_char_pos = menu_cols[h_idx]
					screen.blit(font_obj.render(f" {h_text} ", True, PygameVisualEngine.C64_PALETTE.get(1)), ((col_char_pos + 1) * char_w, char_h * 2))
				screen.blit(font_obj.render("═" * 76, True, PygameVisualEngine.C64_PALETTE.get(3)), (char_w * 2, char_h * 3))

			if global_tui_state.get("menu_mode") not in ["PYGAME_EDITOR", "PYGAME_VIEWER"]:
				panel_width_chars = 37
				
				# --- LEFT COLUMN FILE PANEL SURFACES ---
				left_state = global_tui_state["left"]
				left_active = (global_tui_state["active_side"] == "left")
				left_x = 2 * char_w
				path_lbl_l = f" PATH: {left_state['current_path']} "
				if len(path_lbl_l) > panel_width_chars:
					path_lbl_l = "..." + path_lbl_l[-(panel_width_chars-3):]
				
				c_choice_l = PygameVisualEngine.C64_PALETTE.get(1) if left_active else PygameVisualEngine.C64_PALETTE.get(12)
				screen.blit(font_obj.render(f"[{path_lbl_l.center(panel_width_chars)}]", True, c_choice_l), (left_x, char_h * 5))
				screen.blit(font_obj.render(" Name │ Type │ Size ", True, PygameVisualEngine.C64_PALETTE.get(1)), (left_x, char_h * 6))
				screen.blit(font_obj.render("────────────────────┼──────┼──────", True, PygameVisualEngine.C64_PALETTE.get(1)), (left_x, char_h * 7))

				file_items_l = left_state["file_list"]
				top_visible_l = left_state.get("top_visible_row", 0)
				highlight_idx_l = left_state.get("highlight_index", 0)
				for r_idx in range(16):
					f_idx = top_visible_l + r_idx
					if f_idx >= len(file_items_l):
						break
					item = file_items_l[f_idx]
					px_y = (8 + r_idx) * char_h
					c_nm = f"{item['name']:<18}"[:18]
					t_lb = f"{item.get('type_display', 'PRG'):<4}"[:4]
					s_lb = f"{str(item.get('size_display', '0')):>4}"[:4]
					row_str = f" {c_nm} │ {t_lb} │ {s_lb} "
					if left_active and f_idx == highlight_idx_l:
						pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE.get(1), (left_x, px_y, panel_width_chars * char_w, char_h))
						screen.blit(font_obj.render(row_str, True, PygameVisualEngine.C64_PALETTE.get(0)), (left_x, px_y))
					else:
						screen.blit(font_obj.render(row_str, True, PygameVisualEngine.C64_PALETTE.get(1)), (left_x, px_y))
				if left_state.get("is_in_container"):
					free_lbl_l = f"{left_state.get('free_sectors_count', 0)} BLOCKS FREE"
				else:
					free_lbl_l = left_state.get("free_space_msg", "SCANNING HOST...")
				screen.blit(font_obj.render(f" {free_lbl_l:<35}", True, PygameVisualEngine.C64_PALETTE.get(3)), (left_x, 24 * char_h))

				# --- RIGHT COLUMN FILE PANEL SURFACES ---
				right_state = global_tui_state["right"]
				right_active = (global_tui_state["active_side"] == "right")
				right_x = (2 + panel_width_chars + 2) * char_w
				path_lbl_r = f" PATH: {right_state['current_path']} "
				if len(path_lbl_r) > panel_width_chars:
					path_lbl_r = "..." + path_lbl_r[-(panel_width_chars-3):]

				c_choice_r = PygameVisualEngine.C64_PALETTE.get(1) if right_active else PygameVisualEngine.C64_PALETTE.get(12)
				screen.blit(font_obj.render(f"[{path_lbl_r.center(panel_width_chars)}]", True, c_choice_r), (right_x, char_h * 5))
				screen.blit(font_obj.render(" Name │ Type │ Size ", True, PygameVisualEngine.C64_PALETTE.get(1)), (right_x, char_h * 6))
				screen.blit(font_obj.render("────────────────────┼──────┼──────", True, PygameVisualEngine.C64_PALETTE.get(1)), (right_x, char_h * 7))

				file_items_r = right_state["file_list"]
				top_visible_r = right_state.get("top_visible_row", 0)
				highlight_idx_r = right_state.get("highlight_index", 0)
				for r_idx in range(16):
					f_idx = top_visible_r + r_idx
					if f_idx >= len(file_items_r):
						break
					item = file_items_r[f_idx]
					px_y = (8 + r_idx) * char_h
					c_nm = f"{item['name']:<18}"[:18]
					t_lb = f"{item.get('type_display', 'PRG'):<4}"[:4]
					s_lb = f"{str(item.get('size_display', '0')):>4}"[:4]
					row_str = f" {c_nm} │ {t_lb} │ {s_lb} "
					if right_active and f_idx == highlight_idx_r:
						pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE.get(1), (right_x, px_y, panel_width_chars * char_w, char_h))
						screen.blit(font_obj.render(row_str, True, PygameVisualEngine.C64_PALETTE.get(0)), (right_x, px_y))
					else:
						screen.blit(font_obj.render(row_str, True, PygameVisualEngine.C64_PALETTE.get(1)), (right_x, px_y))

				if right_state.get("is_in_container"):
					free_lbl_r = f"{right_state.get('free_sectors_count', 0)} BLOCKS FREE"
				else:
					free_lbl_r = right_state.get("free_space_msg", "SCANNING HOST...")
				screen.blit(font_obj.render(f" {free_lbl_r:<35}", True, PygameVisualEngine.C64_PALETTE.get(3)), (right_x, 24 * char_h))

				# --- DUAL VECTOR CORE DRIVER DISK ROUTER MENU COUPLER ---
				# FIXED: Wrap the entire block inside a conditional state guard so the menu vanishes when menu_mode shifts back to PANELS
				if global_tui_state.get("menu_mode") == "MENU":
					m_idx = global_tui_state.get("active_menu_header_idx", 0)
					i_idx = global_tui_state.get("active_menu_item_idx", 0)
					menu_cols = {0: 2, 1: 12, 2: 22, 3: 35, 4: 48}
					mx = menu_cols.get(m_idx, 2) * char_w
					my = 4 * char_h
					active_p_dict = global_tui_state.get("left") if (m_idx == 0 or m_idx == 1 or m_idx == 2 or m_idx == 3) else global_tui_state.get("right")
					show_editor = active_p_dict.get("is_in_container", False) and not active_p_dict.get("no_sector_editor", False)
					
					if m_idx == 0 or m_idx == 4:
						items = [" Rescan Directory ", " View Sector Editor "] if show_editor else [" Rescan Directory "]
					elif m_idx == 1:
						items = [" View File ", " Copy File Out ", " Delete Node "]
					elif m_idx == 2:
						items = [" Mount Archive ", " Run Script Macro "]
					elif m_idx == 3:
						items = [" Settings ", " ───────────────── ", " Credits Info "]
					else:
						items = [" Close Sub-Menu "]
					
					mw = (max(len(x) for x in items) + 2) * char_w
					mh = (len(items) + 2) * char_h
					pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE.get(1), (mx, my, mw, mh)) # White Border
					pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE.get(0), (mx + 2, my + 2, mw - 4, mh - 4)) # Black Background
					for idx, text in enumerate(items):
						item_y = my + (char_h * (idx + 1))
						if idx == i_idx:
							pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE.get(6), (mx + 4, item_y, mw - 8, char_h)) # Blue Highlight Bar
							screen.blit(font_obj.render(text, True, PygameVisualEngine.C64_PALETTE.get(1)), (mx + 4, item_y)) # White Text
						else:
							c_flag = PygameVisualEngine.C64_PALETTE.get(1) if "───" not in text else PygameVisualEngine.C64_PALETTE.get(12)
							screen.blit(font_obj.render(text, True, c_flag), (mx + 4, item_y))
							
				# --- POPUP SETTINGS HUD MANAGER BAR ---

				# FIXED: Aligned target runtime context references cleanly to use the proper loop variable tracking name
				# --- POPUP SETTINGS HUD MANAGER BAR ---
				elif global_tui_state.get("menu_mode") == "PYGAME_SETTINGS":
					if "pygame_settings_row" not in global_tui_state:
						global_tui_state["pygame_settings_row"] = 0
						
					# Expand box height parameters dynamically to fit all three options safely
					px, py, pw, ph = 12 * char_w, 8 * char_h, 56 * char_w, 13 * char_h
					pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE.get(1), (px, py, pw, ph)) # White border line
					pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE.get(0), (px + 2, py + 2, pw - 4, ph - 4)) # Black interior
					
					# Render the main HUD title row header text asset
					screen.blit(font_obj.render(" GLOBAL EXPLORER CONFIGURATION PANELS", True, PygameVisualEngine.C64_PALETTE.get(1)), (px + 3 * char_w, py + 1 * char_h))
					screen.blit(font_obj.render("─" * 50, True, PygameVisualEngine.C64_PALETTE.get(12)), (px + 3 * char_w, py + 2 * char_h))
					
					active_row = global_tui_state["pygame_settings_row"]
					
					# Row 0: Visual Style Mode
					box0 = "[X]" if global_tui_state.get("visual_mode") == "PETSCII" else "[ ]"
					text0 = f" {box0} Switch visual mode to PETSCII "
					if active_row == 0:
						pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE.get(1), (px + 3 * char_w, py + 4 * char_h, 50 * char_w, char_h))
						screen.blit(font_obj.render(text0, True, PygameVisualEngine.C64_PALETTE.get(0)), (px + 3 * char_w, py + 4 * char_h))
					else:
						screen.blit(font_obj.render(text0, True, PygameVisualEngine.C64_PALETTE.get(1)), (px + 3 * char_w, py + 4 * char_h))
						
					# Row 1: Extension Verification Toggle
					box1 = "[X]" if global_tui_state.get("respect_cbm_extensions", True) else "[ ]"
					text1 = f" {box1} Respect CBM file name extensions (.prg/.seq) "
					if active_row == 1:
						pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE.get(1), (px + 3 * char_w, py + 6 * char_h, 50 * char_w, char_h))
						screen.blit(font_obj.render(text1, True, PygameVisualEngine.C64_PALETTE.get(0)), (px + 3 * char_w, py + 6 * char_h))
					else:
						screen.blit(font_obj.render(text1, True, PygameVisualEngine.C64_PALETTE.get(1)), (px + 3 * char_w, py + 6 * char_h))
						
					# Row 2: Default Fallback Filetype Selector
					fallback_type = global_tui_state.get("default_cbm_filetype", "PRG")
					text2 = f" [ ] Default Fallback Filetype Selector: < {fallback_type} > "
					if active_row == 2:
						pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE.get(1), (px + 3 * char_w, py + 8 * char_h, 50 * char_w, char_h))
						screen.blit(font_obj.render(text2, True, PygameVisualEngine.C64_PALETTE.get(0)), (px + 3 * char_w, py + 8 * char_h))
					else:
						screen.blit(font_obj.render(text2, True, PygameVisualEngine.C64_PALETTE.get(1)), (px + 3 * char_w, py + 8 * char_h))
						
					# Bottom Info Toolbar Text
					screen.blit(font_obj.render(" [W/S] Move │ [ENTER/SPACE] Toggle │ [ESC] Save & Exit", True, PygameVisualEngine.C64_PALETTE.get(1)), (px + 4 * char_w, py + 11 * char_h))


				# --- DESIGN ACKNOWLEDGEMENTS POPUP CREDIT CARDS ---
				elif global_tui_state.get("menu_mode") == "PYGAME_CREDITS":
					px, py, pw, ph = 12 * char_w, 10 * char_h, 56 * char_w, 9 * char_h
					
					# FIXED: Added correct static color mapping so the credits window container displays instantly on screen
					pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE.get(1), (px, py, pw, ph))
					pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE.get(0), (px + 2, py + 2, pw - 4, ph - 4))
					
					screen.blit(font_obj.render(" SYSTEM PLATFORM ARCHITECTURE ACKNOWLEDGEMENTS", True, PygameVisualEngine.C64_PALETTE.get(1)), (px + 2 * char_w, py + 1 * char_h))
					screen.blit(font_obj.render("Designed by The Alien & The Explorer AI", True, PygameVisualEngine.C64_PALETTE.get(1)), (px + 5 * char_w, py + 3 * char_h))
					screen.blit(font_obj.render("System Node: LV-426 BBS", True, PygameVisualEngine.C64_PALETTE.get(1)), (px + 14 * char_w, py + 5 * char_h))
					screen.blit(font_obj.render(" Press ANY KEY to return safely...", True, PygameVisualEngine.C64_PALETTE.get(1)), (px + 11 * char_w, py + 7 * char_h))



			# --- LOW LEVEL VECTOR DRIVER INTERACTIVE HEX EDITOR GRID CANVASES ---
			elif global_tui_state.get("menu_mode") == "PYGAME_EDITOR":
				ctx = global_tui_state.get("editor_runtime_context", {})
				raw_buf = ctx.get("buffer", bytearray(256))
				c_off = ctx.get("cursor_offset", 0)
				ed_hdr = f" DISK SECTOR EDITOR │ {ctx.get('format_type', 'D64')} MODE │ TRACK: {ctx.get('track', 1):<3} │ SECTOR: {ctx.get('sector', 0):<3}"
				screen.blit(font_obj.render(ed_hdr, True, PygameVisualEngine.C64_PALETTE[1]), (4 * char_w, 5 * char_h))
				screen.blit(font_obj.render("─" * 72, True, PygameVisualEngine.C64_PALETTE[3]), (4 * char_w, 6 * char_h))
				screen.blit(font_obj.render("Offset", True, PygameVisualEngine.C64_PALETTE[1]), (2 * char_w, 7 * char_h))
				for col_idx in range(16):
					screen.blit(font_obj.render(f"{col_idx:02X}", True, PygameVisualEngine.C64_PALETTE[1]), ((11 + (col_idx * 3)) * char_w, 7 * char_h))
				screen.blit(font_obj.render("ASCII View", True, PygameVisualEngine.C64_PALETTE[1]), (61 * char_w, 7 * char_h))

				for row_idx in range(16):
					row_base = row_idx * 16; px_y = (8 + row_idx) * char_h
					screen.blit(font_obj.render(f"${row_base:04X} ", True, PygameVisualEngine.C64_PALETTE[12]), (2 * char_w, px_y))
					for col_idx in range(16):
						curr_byte_offset = row_base + col_idx
						val = raw_buf[curr_byte_offset] if curr_byte_offset < len(raw_buf) else 0
						cx = (11 + (col_idx * 3)) * char_w; ax = (61 + col_idx) * char_w
						char_repr = chr(val) if 32 <= val <= 126 else "."
						if curr_byte_offset == c_off:
							pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE[1], (cx, px_y, 2 * char_w, char_h))
							screen.blit(font_obj.render(f"{val:02X}", True, PygameVisualEngine.C64_PALETTE[6]), (cx, px_y))
							pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE[1], (ax, px_y, char_w, char_h))
							screen.blit(font_obj.render(char_repr, True, PygameVisualEngine.C64_PALETTE[6]), (ax, px_y))
						else:
							screen.blit(font_obj.render(f"{val:02X}", True, PygameVisualEngine.C64_PALETTE[1]), (cx, px_y))
							screen.blit(font_obj.render(char_repr, True, PygameVisualEngine.C64_PALETTE[1]), (ax, px_y))

				if ctx.get("input_prompt_active"):
					px, py, pw, ph = 12 * char_w, 11 * char_h, 56 * char_w, 6 * char_h
					pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE[1], (px, py, pw, ph))
					pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE[0], (px + 2, py + 2, pw - 4, ph - 4))
					screen.blit(font_obj.render(ctx.get("prompt_title", "ENTER VALUE:"), True, PygameVisualEngine.C64_PALETTE[1]), (px + 2 * char_w, py + 1 * char_h))
					screen.blit(font_obj.render(f"> {ctx.get('user_input_buffer', '')}_", True, PygameVisualEngine.C64_PALETTE[3]), (px + 2 * char_w, py + 3 * char_h))

				screen.blit(font_obj.render(" [R] Read Sec │ [W] Write Sec │ [J] Context Jump │ [+/-] Next/Prev Sec ", True, PygameVisualEngine.C64_PALETTE[1]), (2 * char_w, 25 * char_h))
				screen.blit(font_obj.render(" [T] Type Text │ [@] Change Hex │ [Q/ESC] Exit Editor to Panels ", True, PygameVisualEngine.C64_PALETTE[1]), (2 * char_w, 26 * char_h))
				screen.blit(font_obj.render(f" STATUS: {ctx.get('status_msg', 'Active.')}"[:76], True, PygameVisualEngine.C64_PALETTE[1]), (2 * char_w, 28 * char_h))
			# --- NATIVE GRAPHICAL TEXT REPRESENTATION FILE VIEWING HUD ---
			elif global_tui_state.get("menu_mode") == "PYGAME_VIEWER":
				v_ctx = global_tui_state.get("viewer_runtime_context", {})
				raw_payload = v_ctx.get("payload", b"")
				disp_m = v_ctx.get("display_mode", "PROMPT")
				pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE[0], inner_rect)
				pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE[0], pygame.Rect(char_w * 2, char_h * 2, screen_w - (char_w * 4), char_h * 4))
				
				v_char_w, v_char_h = 16, 16
				start_row = v_ctx.get("scroll_row", 0)
				status_str = "LOWERCASE: TEXT" if v_ctx.get("lowercase_toggle", True) else "UPPERCASE: GRAPHICS"
				screen.blit(c64_font_obj.render(f"| Casing Status: {status_str:<45}|", True, PygameVisualEngine.C64_PALETTE[1], PygameVisualEngine.C64_PALETTE[0]), (2 * char_w, 2 * char_h))
				screen.blit(c64_font_obj.render(f"| [ARROWS]: Scroll View Up/Down │ Rows: {v_ctx.get('max_computed_rows', 1):<4} |", True, PygameVisualEngine.C64_PALETTE[1], PygameVisualEngine.C64_PALETTE[0]), (2 * char_w, 3 * char_h))
				screen.blit(c64_font_obj.render(f"| File: '{v_ctx.get('file_name', 'UNKNOWN').upper()}' ({disp_m:<6})	  |", True, PygameVisualEngine.C64_PALETTE[1], PygameVisualEngine.C64_PALETTE[0]), (2 * char_w, 4 * char_h))
				screen.blit(c64_font_obj.render("-" * 47, True, PygameVisualEngine.C64_PALETTE[1]), (2 * char_w, 5 * char_h))

				if disp_m == "PROMPT":
					px, py, pw, ph = 14 * char_w, 11 * char_h, 52 * char_w, 7 * char_h
					pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE[0], (px, py, pw, ph))
					pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE[1], (px, py, pw, ph), 2)
					screen.blit(font_obj.render(" SELECT TEXT TRANSLATION REPRESENTATION MODE: ", True, PygameVisualEngine.C64_PALETTE[1]), (px + 2 * char_w, py + 1 * char_h))
					screen.blit(font_obj.render(" [A] Standard ASCII │ [P] Commodore PETSCII ", True, PygameVisualEngine.C64_PALETTE[1]), (px + 3 * char_w, py + 3 * char_h))
				else:
					col_cnt, row_cnt = 0, 0
					curr_fg = 15
					reverse_mode = False
					lowercase_mode = v_ctx.get("lowercase_toggle", True)
					idx = 0
					while idx < len(raw_payload) and row_cnt < (start_row + 21):
						b = raw_payload[idx]
						idx += 1
						if b == 13:
							col_cnt = 0
							row_cnt += 1
							reverse_mode = False
							continue
						elif b == 18:
							reverse_mode = True
							continue
						elif b == 146:
							reverse_mode = False
							continue
						elif b == 14:
							lowercase_mode = True
							continue
						elif b == 142:
							lowercase_mode = False
							continue
						C64_CODES = {144:0, 5:1, 28:2, 159:3, 156:4, 30:5, 31:6, 158:7, 129:8, 149:9, 150:10, 151:11, 152:12, 153:13, 154:14, 155:15}
						if b in C64_CODES:
							curr_fg = C64_CODES[b]
							continue
						
						if row_cnt >= start_row:
							render_y = (6 * char_h) + ((row_cnt - start_row) * v_char_h)
							render_x = (2 * char_w) + (col_cnt * v_char_w)
							
							if disp_m == "ASCII":
								# FIXED: Use a clean, modern monospace system font for perfect readability
								char_str = chr(b) if 32 <= b <= 126 else "."
								if not lowercase_mode:
									char_str = char_str.upper()
									
								# FIXED: Explicitly force a static, single-tint color registry palette (White = Index 1) to eliminate color leaks!
								screen.blit(font_obj.render(char_str, True, PygameVisualEngine.C64_PALETTE[1]), (render_x, render_y))
							else:
								# Keep your beautiful PETSCII custom mapping and dynamic color variables perfectly running!
								if b == 0x00:
									screen.blit(c64_font_obj.render(" ", True, PygameVisualEngine.C64_PALETTE[curr_fg]), (render_x, render_y))
								else:
									q_base = 0xE100 if lowercase_mode else 0xE000
									if reverse_mode:
										q_base += 0x0200
									screen.blit(c64_font_obj.render(chr(q_base + b), True, PygameVisualEngine.C64_PALETTE[curr_fg]), (render_x, render_y))


						col_cnt += 1
						if col_cnt == 40:
							col_cnt = 0
							row_cnt += 1
					v_ctx["max_computed_rows"] = max(row_cnt, 1)

				pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE.get(0), (char_w * 2, char_h * 27, 76 * char_w, 4 * char_h))
				screen.blit(c64_font_obj.render("-" * 47, True, PygameVisualEngine.C64_PALETTE.get(1)), (2 * char_w, 27 * char_h))
				
				# Safe properties check: falls back smoothly to row 1 if the calculation engine hasn't initialized the key yet
				max_computed = v_ctx.get("max_computed_rows", 1)
				screen.blit(font_obj.render(f" LINE: {start_row}/{max_computed} │ STATUS: View Layer active. "[:76], True, PygameVisualEngine.C64_PALETTE.get(1)), (3 * char_w, 28 * char_h))
				
				screen.blit(font_obj.render(" [UP/DOWN] Scroll File │ [PAGE UP/DOWN] Large Leap │ [C] Toggle Casing ", True, PygameVisualEngine.C64_PALETTE.get(1)), (3 * char_w, 29 * char_h))
				screen.blit(font_obj.render(" [ESC] Exit Viewer File and Return cleanly to Dual Explorer Panel Dashboards ", True, PygameVisualEngine.C64_PALETTE.get(1)), (3 * char_w, 30 * char_h))

			if global_tui_state.get("menu_mode") != "PYGAME_VIEWER" and global_tui_state.get("menu_mode") != "PYGAME_EDITOR":
				screen.blit(font_obj.render(f" SYSTEM: {global_tui_state['command_buffer']}"[:76], True, PygameVisualEngine.C64_PALETTE.get(1)), (char_w * 3, char_h * 25))
				pygame.draw.rect(screen, PygameVisualEngine.C64_PALETTE.get(1), (char_w * 2, char_h * 27, 76 * char_w, char_h))
				screen.blit(font_obj.render(" 1 Help 2 Menu 3 View 4 Edit 5 Copy 6 RenMov 7 Mkdir 8 Delete 9 PullDn 10 Quit ", True, PygameVisualEngine.C64_PALETTE.get(0)), (char_w * 2, char_h * 27))
				screen.blit(font_obj.render(" [F2/F9/M] Dropdown Menu │ [TAB] Swap Panel │ [Arrows] Move Highlight ", True, PygameVisualEngine.C64_PALETTE.get(1)), (char_w * 3, char_h * 29))


			pygame.display.flip()
			# --- HARDWARE EVENT ROUTERS AND KEYBOARD MAPS INTERCEPT LOOP ---
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running_mirror = False
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_F10:
						pygame.quit()
						import sys
						sys.exit(0)
					mm_mode = global_tui_state.get("menu_mode")
					active_side_key = global_tui_state["active_side"]
					active_panel = global_tui_state[active_side_key]
					
					if mm_mode == "PYGAME_EDITOR":
						ctx = global_tui_state.get("editor_runtime_context", {})
						c_off = ctx.get("cursor_offset", 0)
						active_handler = left_state.get("vfs_handler") if (global_tui_state["active_side"] == "left") else right_state.get("vfs_handler")
						if ctx.get("input_prompt_active"):
							if event.key == pygame.K_ESCAPE:
								ctx["input_prompt_active"] = False
								ctx["user_input_buffer"] = ""
								ctx["status_msg"] = "Prompt aborted cleanly."
							elif event.key == pygame.K_BACKSPACE:
								ctx["user_input_buffer"] = ctx.get("user_input_buffer", "")[:-1]
							elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
								input_raw = ctx.get("user_input_buffer", "").strip()
								p_type = ctx.get("prompt_type", "")
								ctx["input_prompt_active"] = False
								ctx["user_input_buffer"] = ""
								if p_type == "READ":
									try:
										nt_str, ns_str = input_raw.split(",")
										nt, ns = int(nt_str.strip()), int(ns_str.strip())
										max_sectors_limit = 256 if ctx.get("format_type") == "DNP" else 21
										if 1 <= nt <= ctx["max_track"] and 0 <= ns < max_sectors_limit:

											ctx["buffer"] = bytearray(active_handler.read_virtual_sector(nt, ns))
											ctx["track"], ctx["sector"] = nt, ns
											ctx["cursor_offset"] = 0
											ctx["status_msg"] = f"SUCCESS: Read Sector Track {nt} Sector {ns}."
										else:
											ctx["status_msg"] = "ALERT: Invalid track/sector coordinate ranges."
									except:
										ctx["status_msg"] = "FAIL: Please use format: Track,Sector (e.g. 18,0)"
								elif p_type == "HEX":
									try:
										ctx["buffer"][c_off] = int(input_raw, 16) & 0xFF
										ctx["status_msg"] = f"SUCCESS: Byte offset ${c_off:02X} updated to ${input_raw.upper()}."
									except:
										ctx["status_msg"] = "FAIL: Invalid two-digit hex values rejected."
								elif p_type == "TEXT":
									for idx, char in enumerate(input_raw):
										ctx["buffer"][(c_off + idx) % 256] = ord(char) & 0xFF
									ctx["status_msg"] = f"SUCCESS: Encoded raw string value onto sector block."
							elif event.unicode and event.unicode.isprintable():
								p_type = ctx.get("prompt_type", "")
								current_buf = ctx.get("user_input_buffer", "")
								if p_type == "HEX" and len(current_buf) >= 2:
									continue
								elif p_type == "TEXT" and len(current_buf) >= (256 - c_off):
									continue
								ctx["user_input_buffer"] = current_buf + event.unicode
							continue
						
						if event.key in [pygame.K_ESCAPE, pygame.K_q]:
							global_tui_state["menu_mode"] = "PANELS"
						elif event.key == pygame.K_LEFT:
							ctx["cursor_offset"] = (c_off - 1) % 256
						elif event.key == pygame.K_RIGHT:
							ctx["cursor_offset"] = (c_off + 1) % 256
						elif event.key == pygame.K_UP:
							ctx["cursor_offset"] = (c_off - 16) % 256
						elif event.key == pygame.K_DOWN:
							ctx["cursor_offset"] = (c_off + 16) % 256
						elif event.key == pygame.K_w:
							try:
								active_handler.write_virtual_sector(ctx["track"], ctx["sector"], ctx["buffer"])
								ctx["status_msg"] = f"SUCCESS: Sector Track {ctx['track']} Sector {ctx['sector']} flushed to disk!"
							except Exception as e:
								ctx["status_msg"] = f"WRITE FAULT: {str(e)}"
						elif event.key in [pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS]:
							try:
								fmt = ctx.get("format_type", "D64")
								ct, cs = ctx["track"], ctx["sector"]
								
								total_sectors = ImageGeometryRegistry.get_sectors_in_track(fmt, ct)
								ns = cs + 1
								nt = ct
								if ns >= total_sectors:
									ns = 0
									nt += 1
									
								if nt <= ctx["max_track"]:
									ctx["track"], ctx["sector"] = nt, ns
									ctx["buffer"] = bytearray(active_handler.read_virtual_sector(nt, ns))
									ctx["cursor_offset"] = 0
									ctx["status_msg"] = f"SUCCESS: Stepped forward to Track {nt} Sector {ns}."
								else:
									ctx["status_msg"] = "ALERT: End of disk container space reached."
							except Exception as e:
								ctx["status_msg"] = f"NAV FAULT: {str(e)}"

						elif event.key in [pygame.K_MINUS, pygame.K_KP_MINUS]:
							try:
								fmt = ctx.get("format_type", "D64")
								ct, cs = ctx["track"], ctx["sector"]
								
								ps = cs - 1
								nt = ct
								if ps < 0:
									nt -= 1
									if nt >= 1:
										ps = ImageGeometryRegistry.get_sectors_in_track(fmt, nt) - 1
										
								if nt >= 1 and ps >= 0:
									ctx["track"], ctx["sector"] = nt, ps
									ctx["buffer"] = bytearray(active_handler.read_virtual_sector(nt, ps))
									ctx["cursor_offset"] = 0
									ctx["status_msg"] = f"SUCCESS: Stepped backward to Track {nt} Sector {ps}."
								else:
									ctx["status_msg"] = "ALERT: Beginning of disk container space reached."
							except Exception as e:
								ctx["status_msg"] = f"NAV FAULT: {str(e)}"

						elif event.key == pygame.K_j:
							try:
								tgt_track = ctx["buffer"][c_off]
								tgt_sector = ctx["buffer"][(c_off + 1) % 256]
								max_sectors_limit = 256 if ctx.get("format_type") == "DNP" else 21
								if 1 <= tgt_track <= ctx["max_track"] and 0 <= tgt_sector < max_sectors_limit:

									ctx["buffer"] = bytearray(active_handler.read_virtual_sector(tgt_track, tgt_sector))
									ctx["track"], ctx["sector"] = tgt_track, tgt_sector
									ctx["cursor_offset"] = 0
									ctx["status_msg"] = f"SUCCESS: Followed pointer warp to Track {tgt_track} Sector {tgt_sector}."
								else:
									ctx["status_msg"] = f"ALERT: Byte pointer T:{tgt_track} S:{tgt_sector} references out-of-bounds sectors."
							except Exception as e:
								ctx["status_msg"] = f"POINTER FAULT: {str(e)}"
						elif event.key == pygame.K_r:
							ctx["input_prompt_active"] = True
							ctx["prompt_type"] = "READ"
							ctx["user_input_buffer"] = ""
							ctx["prompt_title"] = "READ SECTOR COMMAND (Format: Track,Sector e.g. 18,1):"
						elif event.key == pygame.K_t:
							ctx["input_prompt_active"] = True
							ctx["prompt_type"] = "TEXT"
							ctx["user_input_buffer"] = ""
							ctx["prompt_title"] = f"STRING CHARACTER INJECTOR (Max room left: {256 - c_off} bytes):"
						elif event.key == pygame.K_2 and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
							ctx["input_prompt_active"] = True
							ctx["prompt_type"] = "HEX"
							ctx["user_input_buffer"] = ""
							ctx["prompt_title"] = f"CELL OVERWRITE OFFSET ${c_off:02X} (Type exactly 2 Hex characters):"
					elif mm_mode == "PYGAME_CREDITS":
						global_tui_state["menu_mode"] = "PANELS"
					elif mm_mode == "PYGAME_SETTINGS":
						# Initialize an internal tracking row state variable inside app_state if it doesn't exist yet
						if "pygame_settings_row" not in global_tui_state:
							global_tui_state["pygame_settings_row"] = 0
							
						if event.key == pygame.K_ESCAPE:
							current_visual_mode = global_tui_state.get("visual_mode", "STANDARD")
							
							# Commit all three dynamic configurations natively to your persistent configuration file
							ConfigurationManager.save_application_settings({
								"version": ConfigurationManager.VERSION,
								"visual_mode": current_visual_mode,
								"respect_cbm_extensions": global_tui_state.get("respect_cbm_extensions", True),
								"default_cbm_filetype": global_tui_state.get("default_cbm_filetype", "PRG")
							})
							
							if current_visual_mode == "STANDARD":
								pygame.quit()
								import sys
								sys.exit(0)
							else:
								global_tui_state["menu_mode"] = "PANELS"
								continue
								
						# FIXED: Row selection navigation engine handles scrolling through all three toggles cleanly!
						elif event.key == pygame.K_UP or event.key == pygame.K_w:
							global_tui_state["pygame_settings_row"] = (global_tui_state["pygame_settings_row"] - 1) % 3
							continue
						elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
							global_tui_state["pygame_settings_row"] = (global_tui_state["pygame_settings_row"] + 1) % 3
							continue
							
						elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE]:
							sel_row = global_tui_state["pygame_settings_row"]
							
							if sel_row == 0: # Row 0: Visual Style Toggle
								curr = global_tui_state.get("visual_mode", "STANDARD")
								global_tui_state["visual_mode"] = "STANDARD" if curr == "PETSCII" else "PETSCII"
							elif sel_row == 1: # Row 1: Extension Verification Toggle
								global_tui_state["respect_cbm_extensions"] = not global_tui_state.get("respect_cbm_extensions", True)
							elif sel_row == 2: # Row 2: Default Format Suffix Selector
								curr_type = global_tui_state.get("default_cbm_filetype", "PRG")
								global_tui_state["default_cbm_filetype"] = "SEQ" if curr_type == "PRG" else "PRG"
							continue



					
					elif event.key in [pygame.K_F2, pygame.K_F9, pygame.K_m]:
						global_tui_state["menu_mode"] = "MENU"
						global_tui_state["active_menu_header_idx"] = 0
						global_tui_state["active_menu_item_idx"] = 0
					elif mm_mode == "MENU":
						m_idx, i_idx = global_tui_state["active_menu_header_idx"], global_tui_state["active_menu_item_idx"]
						if event.key == pygame.K_ESCAPE:
							global_tui_state["menu_mode"] = "PANELS"
						elif event.key == pygame.K_LEFT:
							global_tui_state["active_menu_header_idx"] = (m_idx - 1) % 5
							global_tui_state["active_menu_item_idx"] = 0
						elif event.key == pygame.K_RIGHT:
							global_tui_state["active_menu_header_idx"] = (m_idx + 1) % 5
							global_tui_state["active_menu_item_idx"] = 0
						elif event.key == pygame.K_UP:
							global_tui_state["active_menu_item_idx"] = (i_idx - 1) % len(items)
						elif event.key == pygame.K_DOWN:
							global_tui_state["active_menu_item_idx"] = (i_idx + 1) % len(items)
						elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
							if "─────" in items[i_idx]:
								continue
							active_side_str = "left" if (m_idx == 0 or m_idx == 1 or m_idx == 2 or m_idx == 3) else "right"
							target_panel = global_tui_state[active_side_str]
							if m_idx == 3 and i_idx == 0:
								global_tui_state["menu_mode"] = "PYGAME_SETTINGS"
							elif m_idx == 3 and i_idx == 2:
								global_tui_state["menu_mode"] = "PYGAME_CREDITS"
								continue
							elif (m_idx == 0 or m_idx == 4) and i_idx == 1 and show_editor:
								# Safe properties check: inspects the underlying broker wrapper class name
								is_dnp = "DNP" in active_p_dict["vfs_handler"].__class__.__name__
								fmt_type = "DNP" if is_dnp else "D64"
								
								global_tui_state["editor_runtime_context"] = {
									"archive_name": active_p_dict["current_path"].split("//")[-1], 
									"format_type": fmt_type,
									"track": 1 if is_dnp else 18, 
									"sector": 34 if is_dnp else 0, 
									"max_track": 255 if is_dnp else 35,
									"cursor_offset": 0, 
									"edit_mode": "NAV", 
									"status_msg": "Sector Editor Active. Arrow keys navigation.",
									"buffer": bytearray(active_p_dict["vfs_handler"].read_virtual_sector(1 if is_dnp else 18, 34 if is_dnp else 0))
								}
								global_tui_state["menu_mode"] = "PYGAME_EDITOR"
							elif m_idx == 1 and i_idx == 0:
								ledger = target_panel.get("file_list", [])
								h_index = target_panel.get("highlight_index", 0)
								if ledger and h_index < len(ledger):
									sel_file = ledger[h_index]
									if "vfs_meta" in sel_file and not sel_file.get("is_directory") and not sel_file.get("is_virtual_container"):
										try:
											vfs_node = sel_file["vfs_meta"]
											payload = target_panel["vfs_handler"].extract_file_bytes(vfs_node)
											global_tui_state["viewer_runtime_context"] = {"file_name": sel_file["name"], "payload": payload, "display_mode": "PROMPT", "scroll_row": 0, "lowercase_toggle": True, "reverse_state": False}
											if global_tui_state.get("visual_mode") == "PETSCII":
												global_tui_state["menu_mode"] = "PYGAME_VIEWER"
											else:
												global_tui_state["menu_mode"] = "VIEWER"
												running_mirror = False
										except Exception as e:
											global_tui_state["command_buffer"] = f"LOAD FAULT: {str(e)}"
									else:
										global_tui_state["menu_mode"] = "PANELS"
					elif mm_mode == "PYGAME_VIEWER":
						v_ctx = global_tui_state.get("viewer_runtime_context", {})
						disp_m = v_ctx.get("display_mode", "PROMPT")
						if disp_m == "PROMPT":
							if event.key == pygame.K_ESCAPE:
								global_tui_state["menu_mode"] = "PANELS"
							elif event.key == pygame.K_a:
								v_ctx["display_mode"] = "ASCII"
							elif event.key == pygame.K_p:
								v_ctx["display_mode"] = "PETSCII"
						else:
							cur_scroll = v_ctx.get("scroll_row", 0)
							max_avail = v_ctx.get("max_computed_rows", 1)
							if event.key == pygame.K_ESCAPE:
								global_tui_state["menu_mode"] = "PANELS"
							elif event.key == pygame.K_c:
								v_ctx["lowercase_toggle"] = not v_ctx.get("lowercase_toggle", True)
							elif event.key == pygame.K_UP:
								v_ctx["scroll_row"] = max(0, cur_scroll - 1)
							elif event.key == pygame.K_DOWN:
								v_ctx["scroll_row"] = min(max(0, max_avail - 1), cur_scroll + 1)
							elif event.key == pygame.K_PAGEUP:
								v_ctx["scroll_row"] = max(0, cur_scroll - 10)
							elif event.key == pygame.K_PAGEDOWN:
								v_ctx["scroll_row"] = min(max(0, max_avail - 1), cur_scroll + 10)

					elif event.key == pygame.K_TAB:
						global_tui_state["active_side"] = "right" if (active_side_key == "left") else "left"
					elif event.key == pygame.K_UP:
						TUIController.process_scrolling_movement(active_panel, "UP", (24, 80))
					elif event.key == pygame.K_DOWN:
						TUIController.process_scrolling_movement(active_panel, "DOWN", (24, 80))
					elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
						# FIXED: Strip away all duplicated code and pass calculations directly to our shared, bug-free driver tracks!
						active_side_key = global_tui_state["active_side"]
						SharedVFSController.execute_file_activation(global_tui_state, active_side_key)
						continue

		# --- PROTECTED SHUTDOWN GATEWAY PASS ---
		pygame.display.quit()


