class TUIDropDownMenu:
	"""Renders action column overlays, drop-down cards, and setting windows."""
	@staticmethod
	def draw_menu_card(stdscr, menu_idx, active_item_idx, panel_state, global_tui_state=None):
		menu_columns = {0: 2, 1: 10, 2: 18, 3: 29, 4: 40}
		start_x = menu_columns[menu_idx]
		start_y = 1
		
		# FIXED: Determine which underlying panel data array matches this specific menu column card index
		current_view_side = "left" if menu_idx == 0 else "right" if menu_idx == 4 else global_tui_state.get("active_side", "left") if global_tui_state else "left"
		true_panel = global_tui_state[current_view_side] if global_tui_state else panel_state
		
		is_virtual = true_panel.get("is_in_container", False)
		no_editor_flag = true_panel.get("no_sector_editor", False)
		show_sector_editor = is_virtual and not no_editor_flag

		menu_items = []
		if menu_idx == 0 or menu_idx == 4:
			if show_sector_editor:
				# 1. RESOLVE THE ACTIVE FILE SYSTEM FORMAT LAYER
				handler = true_panel.get("vfs_handler")
				fmt = getattr(handler, "format_type", "HOST") if handler else "HOST"
				
				# 2. BUILD CONTEXT-AWARE DROP-DOWN MENU ARRAYS
				# Start with your universal base options available for all configurations
				menu_items = [" Rescan Directory ", " View Sector Editor ", " View BAM Editor "]
				
				# EXCLUSIVE GUARD: Show 'GCR Stream Viewer' ONLY if a true G64 image is mounted! [1.1]
				if fmt == "G64":
					menu_items.append(" View GCR Stream ")
					
				# EXCLUSIVE GUARD: Show 'Create 1581 Partition' ONLY if a D81 image is mounted! [1.13]
				if fmt == "D81":
					menu_items.append(" Create 1581 Partition ")
			else:
				menu_items = [" Rescan Directory "]
		elif menu_idx == 1:
			menu_items = [" View File ", " Copy File Out ", " Delete Node "]
		elif menu_idx == 2:
			menu_items = [" Mount Archive ", " Run Script Macro "]
		elif menu_idx == 3:
			menu_items = [" Settings ", " ───────────────── ", " Credits Info "]

		# FIXED: Guard check and geometry dimension variables restored cleanly! [1.26]
		if not menu_items: 
			return None
			
		card_width = max(len(x) for x in menu_items) + 2
		card_height = len(menu_items) + 2

		stdscr.attron(curses.color_pair(4))
		for r in range(card_height):
			curr_y = start_y + r
			if r == 0: 
				stdscr.addstr(curr_y, start_x, "┌" + "─" * (card_width - 2) + "┐")
			elif r == card_height - 1: 
				stdscr.addstr(curr_y, start_x, "└" + "─" * (card_width - 2) + "┘")
			else:
				stdscr.addstr(curr_y, start_x, "│" + " " * (card_width - 2) + "│")
				item_text = menu_items[r - 1]
				display_text = f"{item_text:<{card_width - 2}}"
				if (r - 1) == active_item_idx:
					stdscr.attron(curses.color_pair(3))
					stdscr.addstr(curr_y, start_x + 1, display_text)
					stdscr.attroff(curses.color_pair(3))
					stdscr.attron(curses.color_pair(4))
				else:
					if "───" in item_text: 
						stdscr.addstr(curr_y, start_x + 1, "─" * (card_width - 2))
					else: 
						stdscr.addstr(curr_y, start_x + 1, display_text)
		stdscr.attroff(curses.color_pair(4))
		stdscr.refresh()
		return menu_items

	@staticmethod
	def show_settings_popup(stdscr, global_tui_state):
		max_rows, max_cols = stdscr.getmaxyx()
		# FIXED: Expanded height constraint from 18 to 20 to give our new informational help text ample space!
		box_w, box_h = 68, 20
		start_x = (max_cols - box_w) // 2
		start_y = (max_rows - box_h) // 2

		# Load current persistent profiles dynamically from v1.9.0 configuration schema
		config = ConfigurationManager.load_application_settings()
		curr_mode = config.get("visual_mode", "STANDARD")
		curr_ext = config.get("respect_cbm_extensions", True)
		curr_type = config.get("default_cbm_filetype", "PRG")
		curr_override = config.get("override_cmd_hd_max_size", False)
		
		# Load our human-readable string token field definition string parameter
		orig_size_str = str(config.get("custom_cmd_hd_size_str", "8G")).strip().upper()
		
		# Store text input characters in a mutable list buffer layer to support fluid user interactions
		size_input_buffer = list(orig_size_str)
		active_row_idx = 0 

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

			# Title bar renderer layout pass
			stdscr.addstr(start_y + 1, start_x + 4, f" GLOBAL EXPLORER CONFIGURATION INTERFACE (v{ConfigurationManager.VERSION})", curses.A_BOLD)
			stdscr.addstr(start_y + 2, start_x + 2, "─" * (box_w - 4))

			# Row 0: Visual Style Toggle
			t0 = "[X]" if curr_mode == "PETSCII" else "[ ]"
			r0 = f" {t0} Switch visual mode to PETSCII "
			s0 = curses.color_pair(3) if active_row_idx == 0 else curses.color_pair(4)
			stdscr.addstr(start_y + 4, start_x + 4, f"{r0:<{box_w - 8}}", s0)

			# Row 1: Extension Verification Toggle
			t1 = "[X]" if curr_ext else "[ ]"
			r1 = f" {t1} Respect CBM file name extensions (.prg/.seq) "
			s1 = curses.color_pair(3) if active_row_idx == 1 else curses.color_pair(4)
			stdscr.addstr(start_y + 6, start_x + 4, f"{r1:<{box_w - 8}}", s1)

			# Row 2: Default Format Type Selector
			r2 = f" [ ] Default Fallback Filetype Selector: < {curr_type} > "
			s2 = curses.color_pair(3) if active_row_idx == 2 else curses.color_pair(4)
			stdscr.addstr(start_y + 8, start_x + 4, f"{r2:<{box_w - 8}}", s2)

			# Row 3: CMD-HD Maximum Size Override Toggle
			t3 = "[X]" if curr_override else "[ ]"
			r3 = f" {t3} Override CMD-HD Max Size Setting "
			s3 = curses.color_pair(3) if active_row_idx == 3 else curses.color_pair(4)
			stdscr.addstr(start_y + 10, start_x + 4, f"{r3:<{box_w - 8}}", s3)

			# Row 4: Prompts explicitly for the human-readable disk image size parameters
			curr_buffer_str = "".join(size_input_buffer)
			cursor_prompt = "_" if active_row_idx == 4 else " "
			r4 = f"		↳ Target Disk Image Max Size: [ {curr_buffer_str}{cursor_prompt} ] "
			s4 = curses.color_pair(3) if active_row_idx == 4 else curses.color_pair(4)
			
			if not curr_override:
				stdscr.addstr(start_y + 11, start_x + 4, f"{r4:<{box_w - 8}}", curses.A_DIM | (curses.color_pair(3) if active_row_idx == 4 else curses.color_pair(4)))
			else:
				stdscr.addstr(start_y + 11, start_x + 4, f"{r4:<{box_w - 8}}", s4)

			# --- FIXED: ADDED INFORMATIONAL SETTINGS USER EXPLANATION LINE ---
			# Renders an explicit help text string directly under the input row to guide user input formats!
			help_text = "Accepts 'G' or 'GB' for gigabytes and 'MB' for megabytes."
			stdscr.addstr(start_y + 13, start_x + 4, f"{help_text:<{box_w - 8}}", curses.color_pair(4) | curses.A_DIM)

			# Bottom Toolbar Options (Shifted layout down symmetrically matching box_h = 20 constraints)
			footer_text = " [UP/DN] Move │ [ENTER/SPACE] Toggle/Edit │ [Q/ESC] Save & Exit "
			footer_x = start_x + ((box_w - len(footer_text)) // 2)
			stdscr.attron(curses.color_pair(4))
			stdscr.addstr(start_y + 16, footer_x, footer_text, curses.A_REVERSE)
			stdscr.attroff(curses.color_pair(4))
			stdscr.refresh()

			popup_key = stdscr.getch()
			if popup_key in [27, ord('q'), ord('Q')]:  # Safe commit sequence exit
				global_tui_state["visual_mode"] = curr_mode
				
				# Sanitize and compile string tokens text maps back to raw blocks integers
				raw_final_str = "".join(size_input_buffer).strip().upper()
				if not raw_final_str:
					raw_final_str = "8G"
					
				# --- HIGH-PRECISION TEXT PARSER CONVERSION SUB-ROUTINE ---
				digit_chars = [c for c in raw_final_str if c.isdigit()]
				unit_chars = [c for c in raw_final_str if not c.isdigit() and c in ['M', 'G', 'B']]
				
				try:
					scalar_val = int("".join(digit_chars)) if digit_chars else 8
				except ValueError:
					scalar_val = 8
					
				# Determine geometry scales matching documented SCSI 512-byte parameters [1.13]
				computed_blocks = 16777216 
				if 'M' in unit_chars:
					computed_blocks = (scalar_val * 1048576) // 512
				else:
					computed_blocks = (scalar_val * 1073741824) // 512
					
				# HARDWARE FLOOR BARRIER LOCKOUT: Enforce the absolute 20 MB minimum mechanical limit! [1.13]
				if computed_blocks < 40960:
					computed_blocks = 40960
					raw_final_str = "20MB"
					
				# ARCHITECTURAL CEILING LIMIT LOCKOUT: Clamp to maximum 8 GB filesystem capacities [1.13]
				if computed_blocks > 16777216:
					computed_blocks = 16777216
					raw_final_str = "8G"

				saved_payload = {
					"version": ConfigurationManager.VERSION,
					"visual_mode": curr_mode,
					"respect_cbm_extensions": curr_ext,
					"default_cbm_filetype": curr_type,
					"override_cmd_hd_max_size": curr_override,
					"custom_cmd_hd_size_str": raw_final_str,			  
					"custom_cmd_hd_blocks_value": computed_blocks		  
				}
				ConfigurationManager.save_application_settings(saved_payload)
				break
				
			elif popup_key in [curses.KEY_UP, ord('w'), ord('W')]:
				active_row_idx = (active_row_idx - 1) % 5
			elif popup_key in [curses.KEY_DOWN, ord('s'), ord('S')]:
				active_row_idx = (active_row_idx + 1) % 5
				
			# FIXED: Expanded the backspace intercept gate to capture all possible terminal key-code variants simultaneously!
			elif active_row_idx == 4 and curr_override and (popup_key in [8, 127, 263, curses.KEY_BACKSPACE] or chr(popup_key) in ['\x08', '\x7f']):
				if size_input_buffer:
					size_input_buffer.pop()
				
			# EXTENDED ALPHANUMERIC CAPTURE GATEWAY: Accepts numbers AND scale indicator characters (M, G, B)
			elif active_row_idx == 4 and curr_override:
				# Map valid key code sets dynamically: 0-9 codes, case-shifted alphabetical letters
				is_digit = (48 <= popup_key <= 57)
				is_valid_alpha = (popup_key in [ord('m'), ord('M'), ord('g'), ord('G'), ord('b'), ord('B')])
				
				if (is_digit or is_valid_alpha) and len(size_input_buffer) < 8:
					size_input_buffer.append(chr(popup_key).upper())
				
			elif popup_key == 10 or popup_key == 13 or popup_key == 32:
				if active_row_idx == 0:
					curr_mode = "PETSCII" if curr_mode == "STANDARD" else "STANDARD"
				elif active_row_idx == 1:
					curr_ext = not curr_ext
				elif active_row_idx == 2:
					curr_type = "SEQ" if curr_type == "PRG" else "PRG"
				elif active_row_idx == 3:
					curr_override = not curr_override


	@staticmethod
	def show_credits_popup(stdscr):
		max_rows, max_cols = stdscr.getmaxyx()
		box_w, box_h = 58, 10
		start_x = (max_cols - box_w) // 2
		start_y = (max_rows - box_h) // 2

		stdscr.attron(curses.color_pair(4))
		for r in range(box_h):
			curr_y = start_y + r
			if r == 0: 
				stdscr.addstr(curr_y, start_x, "┌" + "─" * (box_w - 2) + "┐")
			elif r == box_h - 1: 
				stdscr.addstr(curr_y, start_x, "└" + "─" * (box_w - 2) + "┘")
			else: 
				stdscr.addstr(curr_y, start_x, "│" + " " * (box_w - 2) + "│")
		stdscr.addstr(start_y + 2, start_x + 4, " SYSTEM PLATFORM ARCHITECTURE ACKNOWLEDGEMENTS", curses.A_BOLD)
		stdscr.addstr(start_y + 4, start_x + 6, "Designed by The Alien & The Explorer AI", curses.color_pair(5) | curses.A_BOLD)
		stdscr.addstr(start_y + 5, start_x + 18, "System Node: LV-426 BBS", curses.A_UNDERLINE)
		stdscr.addstr(start_y + 8, start_x + (box_w - 30) // 2, " Press ANY KEY to return safely...", curses.A_BLINK)
		stdscr.attroff(curses.color_pair(4))
		stdscr.refresh()
		stdscr.getch()


