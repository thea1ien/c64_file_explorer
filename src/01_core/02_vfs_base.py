class SharedVFSController:
	"""Master Operations Engine: Houses the definitive, bug-free disk handling 
	and path manipulation routines shared equally by both TUI and Pygame frontends.
	"""
	@staticmethod
	def execute_file_activation(app_state, side_key):
		"""Unified router handling Enter/Return operations across all interface modes."""
		panel = app_state[side_key]
		files = panel.get("file_list", [])
		if not files:
			return False
			
		highlighted_idx = panel.get("highlight_index", 0)
		if highlighted_idx >= len(files):
			return False
			
		sel_item = files[highlighted_idx]
		# === INTERCEPT GATEWAY: DETECT MASTER CMD STORAGE CONTAINER (.DHD/.D2M/.D4M) PARTITIONS ===
		handler = panel.get("vfs_handler")
		if handler and getattr(handler, "format_type", "") in ["DHD", "D2M", "D4M"]:
			
			# SCENARIO A: BACK OUT OF A NESTED PARTITION TO RETURN TO THE MASTER TABLE VIEW
			if sel_item["name"] == "..":
				if hasattr(handler, "parent_dhd_handler") and handler.parent_dhd_handler:
					parent_container = handler.parent_dhd_handler
					
					panel["vfs_handler"] = parent_container
					panel["file_list"] = parent_container.file_list
					panel["disk_label_msg"] = getattr(parent_container, "disk_label_msg", f"12 \"{parent_container.format_type} SYSTEM\"")
					panel["free_sectors_count"] = getattr(parent_container, "free_sectors_count", 0)
					
					if "active_panel" in app_state and app_state["active_panel"] in app_state:
						target_panel_state = app_state[app_state["active_panel"]]
						target_panel_state["vfs_handler"] = parent_container
						target_panel_state["file_list"] = parent_container.file_list
						target_panel_state["disk_label_msg"] = panel["disk_label_msg"]
						target_panel_state["free_sectors_count"] = panel["free_sectors_count"]
						
					panel["highlight_index"] = 0
					panel["top_visible_row"] = 0
					return True
					
			# SCENARIO B: DIVE FORWARD INTO A VALID PARTITION SLOT (NAT, 41, 71, 81, C81)
			else:
				nested_res = handler.navigate_forward(sel_item["track"], sel_item["sector"], sel_item["name"])
				
				if isinstance(nested_res, str):
					# An explicit lockout warning banner or error string was returned from our gatekeeper bounds rules
					app_state["command_buffer"] = nested_res
					return True
				elif nested_res is not None:
					# SUCCESS: Swap out the panel's active virtual file system driver object with the nested handler
					panel["vfs_handler"] = nested_res
					panel["file_list"] = nested_res.file_list
					panel["disk_label_msg"] = getattr(nested_res, "disk_label_msg", panel.get("disk_label_msg", ""))
					panel["free_sectors_count"] = getattr(nested_res, "free_sectors_count", 0)
					
					if "active_panel" in app_state and app_state["active_panel"] in app_state:
						target_panel_state = app_state[app_state["active_panel"]]
						target_panel_state["vfs_handler"] = nested_res
						target_panel_state["file_list"] = nested_res.file_list
						target_panel_state["disk_label_msg"] = panel["disk_label_msg"]
						target_panel_state["free_sectors_count"] = panel["free_sectors_count"]
						
					panel["highlight_index"] = 0
					panel["top_visible_row"] = 0
					return True

		# === INTERCEPT GATEWAY: DETECT 1581 SUBDIRECTORY PARTITIONS ===
		vfs_meta = sel_item.get("vfs_meta", {})
		# FIXED: Added a NoneType guard to shield against root unmounting rows!
		if (vfs_meta and vfs_meta.get("is_1581_partition")) or sel_item.get("type_display") == "UP-DIR":
			handler = panel.get("vfs_handler")
			if handler and getattr(handler, "format_type", "") == "D81":
				
				# SCENARIO A: User selected the back-out UP-DIR entry hook
				if sel_item["name"] == "..":
					if hasattr(handler, "directory_history_stack") and handler.directory_history_stack:
						# Pop the previous directory track state out of the breadcrumb pool
						previous_t = handler.directory_history_stack.pop()
						handler.current_dir_track = previous_t
						
						# Run directory listing to dynamically compute the parent's file list, labels, and BAM!
						new_file_list = handler.list_directory()
						
						# FORCE SYNCHRONIZATION: Force-feed the fresh data directly into the global UI panel arrays!
						panel["file_list"] = new_file_list
						panel["disk_label_msg"] = getattr(handler, "disk_label_msg", panel.get("disk_label_msg", ""))
						panel["free_sectors_count"] = getattr(handler, "free_sectors_count", 0)
						
						# Sync the mirror tracking keys inside app_state to prevent refresh overrides
						if "active_panel" in app_state and app_state["active_panel"] in app_state:
							target_panel = app_state[app_state["active_panel"]]
							target_panel["file_list"] = new_file_list
							target_panel["disk_label_msg"] = panel["disk_label_msg"]
							target_panel["free_sectors_count"] = panel["free_sectors_count"]
						
						panel["highlight_index"] = 0
						panel["top_visible_row"] = 0
						return True
						
				# SCENARIO B: User selected a nested folder directory entry to jump inside
				else:
					target_t = int(vfs_meta.get("track", 40))
					
					if not hasattr(handler, "directory_history_stack"):
						handler.directory_history_stack = []
						
					# Freeze our current track onto the stack before diving into the subfolder
					handler.directory_history_stack.append(handler.current_dir_track)
					
					# Focus the driver on the partition's starting directory track layout block
					handler.current_dir_track = target_t
					
					# Run directory listing to dynamically compute the partition's file list, labels, and BAM!
					new_file_list = handler.list_directory()
					
					# FORCE SYNCHRONIZATION: Overwrite the static panel states completely with the partition's metrics!
					panel["file_list"] = new_file_list
					panel["disk_label_msg"] = getattr(handler, "disk_label_msg", panel.get("disk_label_msg", ""))
					panel["free_sectors_count"] = getattr(handler, "free_sectors_count", 0)
					
					# Sync the mirror tracking keys inside app_state to protect against background refresh loops
					if "active_panel" in app_state and app_state["active_panel"] in app_state:
						target_panel = app_state[app_state["active_panel"]]
						target_panel["file_list"] = new_file_list
						target_panel["disk_label_msg"] = panel["disk_label_msg"]
						target_panel["free_sectors_count"] = panel["free_sectors_count"]
					
					panel["highlight_index"] = 0
					panel["top_visible_row"] = 0
					return True

		# --- ROUTINE 1: UP-DIRECTORY ("..") NAVIGATION CONTROLLER ---
		if sel_item["name"] == "..":
			if panel.get("is_in_container"):
				vfs_obj = panel["vfs_handler"]
				
				# Format-aware verification splits .d64 flat sectors from complex nested .dnp partitions
				if "DNP" in vfs_obj.__class__.__name__ or hasattr(vfs_obj, "dnp_h"):
					inner_h = getattr(vfs_obj, "dnp_h", vfs_obj)
					
					# FIXED: If we are already at the top layer of the archive, back out completely into the local computer!
					if inner_h.current_track == 1 and inner_h.current_sector == 1 or inner_h.current_path == "":
						panel["current_path"] = panel["backed_host_path"]
						panel["file_list"] = HostSystemScanner.scan_directory(panel["backed_host_path"])
						panel["free_space_msg"] = TUIController.get_host_free_space_string(panel["backed_host_path"])
						panel["is_in_container"] = False
						panel["vfs_handler"] = None
						panel["disk_label_msg"] = None
						panel["highlight_index"] = 0
						panel["top_visible_row"] = 0
						return True
						
					current_blk = inner_h.read_virtual_sector(inner_h.current_track, inner_h.current_sector)
					
					parent_track = int(current_blk[34])
					parent_sector = int(current_blk[35])
					grandparent_track = int(current_blk[36])
					grandparent_sector = int(current_blk[37])
					
					if parent_track == grandparent_track and parent_sector == grandparent_sector:
						inner_h.current_track = 1
						inner_h.current_sector = 1
						inner_h.current_path = ""
					else:
						inner_h.current_track = parent_track
						inner_h.current_sector = parent_sector
						path_segments = inner_h.current_path.split("\\")
						# FIXED: Drops "ROOT" placeholder completely to prevent path array bloat
						inner_h.current_path = "\\".join(path_segments[:-1]) if len(path_segments) > 1 else ""
						
					# FIXED: Enforces clear single-backslash separators and strips out rogue duplicate empty nodes completely
					if inner_h.current_path == "" or inner_h.current_path == "\\":
						panel["current_path"] = f"VFS://{panel['archive_root']}"
					else:
						# Strip off any accidental double backslashes gracefully during generation sweeps
						clean_sub_path = inner_h.current_path.lstrip("\\")
						panel["current_path"] = f"VFS://{panel['archive_root']}\\{clean_sub_path}"
						
					panel["file_list"] = TUIController.mine_dnp_entries(inner_h, inner_h.current_track, inner_h.current_sector)
				else:
					# Clean .d64 exit strategy: drop back directly into the physical host path location
					panel["current_path"] = panel["backed_host_path"]
					panel["file_list"] = HostSystemScanner.scan_directory(panel["backed_host_path"])
					panel["free_space_msg"] = TUIController.get_host_free_space_string(panel["backed_host_path"])
					panel["is_in_container"] = False
					panel["vfs_handler"] = None
					panel["disk_label_msg"] = None
			else:
				# Native workstation local host upward trajectory
				parent_path = os.path.dirname(os.path.abspath(panel["current_path"]))
				panel["current_path"] = parent_path
				panel["file_list"] = HostSystemScanner.scan_directory(parent_path)
				panel["free_space_msg"] = TUIController.get_host_free_space_string(parent_path)
				
			panel["highlight_index"] = 0
			panel["top_visible_row"] = 0
			return True

		# --- ROUTINE 2: FORWARD SUB-DIRECTORY ENTRY EXPANSION ---
		elif sel_item.get("is_directory"):
			if panel.get("is_in_container"):
				vfs_obj = panel["vfs_handler"]
				v_meta = sel_item["vfs_meta"]
				
				# FIXED: Catch baseline ROOT paths natively and clear them out before diving forward
				inner_h = getattr(vfs_obj, "dnp_h", vfs_obj)
				if inner_h.current_path == "ROOT":
					inner_h.current_path = ""
					
				if vfs_obj.navigate_forward(v_meta["track"], v_meta["sector"], sel_item["name"]):
					# FIXED: If the path variable accidentally retains a leading slash or ROOT marker, normalize it cleanly
					sanitized_path = inner_h.current_path.replace("ROOT\\", "").replace("ROOT", "")
					inner_h.current_path = sanitized_path
					
					# FIXED: Enforces clear single-backslash separators and strips out rogue duplicate empty nodes completely
					if inner_h.current_path == "" or inner_h.current_path == "\\":
						panel["current_path"] = f"VFS://{panel['archive_root']}"
					else:
						# Strip off any accidental double backslashes gracefully during generation sweeps
						clean_sub_path = inner_h.current_path.lstrip("\\")
						panel["current_path"] = f"VFS://{panel['archive_root']}\\{clean_sub_path}"
						
					panel["file_list"] = TUIController.mine_dnp_entries(inner_h, inner_h.current_track, inner_h.current_sector)
			else:
				# Native workstation folder dive forward 
				target_folder_path = os.path.join(panel["current_path"], sel_item["name"])
				panel["current_path"] = target_folder_path
				panel["file_list"] = HostSystemScanner.scan_directory(target_folder_path)
				panel["free_space_msg"] = TUIController.get_host_free_space_string(target_folder_path)
				
			panel["highlight_index"] = 0
			panel["top_visible_row"] = 0
			return True

		# --- ROUTINE 3: UNIFIED CONTAINER AUTOMATED MOUNT BROKER ---
		elif VFSDriverRegistry.is_supported(sel_item["name"]):
			full_img_path = os.path.join(panel["current_path"], sel_item["name"])
			try:
				# Track if the parent workspace panel layout is already nested inside a read-only archive
				parent_was_read_only = panel.get("read_only_container", False)
				
				if panel.get("is_in_container") and panel.get("vfs_handler"):
					container_payload_bytes = panel["vfs_handler"].extract_file_bytes(sel_item.get("vfs_meta", {}))
				else:
					with open(full_img_path, 'rb') as host_f:
						container_payload_bytes = host_f.read()
						
							# FIXED: Combines your panel's current navigation folder string with the item name to preserve absolute paths!
				# FIXED: Uses 'panel' to match the true local variable namespace of this function!
				full_host_folder_path = panel.get("current_path", "")
				
				if full_host_folder_path.startswith("VFS://"):
					full_host_folder_path = panel.get("backed_host_path", "")
					
				absolute_source_file_path = os.path.join(full_host_folder_path, sel_item["name"])
				
				# Pass the absolute path into the handler factory registration loop cleanly!
				driver_instance = VFSDriverRegistry.instantiate_handler(absolute_source_file_path, container_payload_bytes)
				if driver_instance:
					if not panel.get("is_in_container"):
						panel["backed_host_path"] = panel["current_path"]
						
					# RECURSIVE SAFETY PASS: If the parent archive was read-only, or this new driver requires it, lock write abilities!
					if parent_was_read_only or getattr(driver_instance, "read_only", False):
						driver_instance.read_only = True
						panel["read_only_container"] = True
						panel["no_sector_editor"] = True # Protect sectors by hiding the full-screen interactive sector editor gate
					else:
						panel["read_only_container"] = False
						panel["no_sector_editor"] = getattr(driver_instance, "no_sector_editor", False)

					panel["archive_root"] = sel_item["name"]
					panel["current_path"] = f"VFS://{sel_item['name']}"
					panel["file_list"] = driver_instance.list_directory()				
					# =========================================================================
					# 🚨 GLOBAL CONTAINER SPACE-TO-UNDERLINE TRANSLATION SHIELD 🚨
					# Intercepts the generated directory lists across all virtual CBM drivers
					# (.d64, .d71, .dnp, .lnx). If a filename features true leading space columns, 
					# it swaps them to safe underscores (_) to ensure the host OS can manage, 
					# export, and track them without modern file allocation naming lockouts.
					# =========================================================================
					if panel["file_list"]:
						for file_node in panel["file_list"]:
							node_name = file_node.get("name", "")
							
							# If a file item name contains authentic leading spaces from a CBM disk
							if node_name.startswith(" "):
								# Count the spaces and replace them cleanly with safe underscores
								leading_space_count = len(node_name) - len(node_name.lstrip(' '))
								file_node["name"] = "_" * leading_space_count + node_name.lstrip(' ')
					# =========================================================================

					panel["disk_label_msg"] = driver_instance.disk_label_msg
					panel["free_sectors_count"] = getattr(driver_instance, "free_sectors_count", 664)
					panel["vfs_handler"] = driver_instance
					panel["is_in_container"] = True
					panel["highlight_index"] = 0
					panel["top_visible_row"] = 0
					app_state["command_buffer"] = f"SUCCESS: Unified Core Mounted '{sel_item['name']}'"
					return True
			except Exception as mount_err:
				app_state["command_buffer"] = f"VFS CONTROLLER ERROR: {str(mount_err)}"
				return False


class BaseVFSHandler:
	"""Abstract Base Contract for all C64 Virtual Filesystems."""
	def __init__(self, raw_payload, archive_name=""):
		self.payload = raw_payload
		self.archive_name = archive_name
		self.file_list = []
		self.disk_label_msg = ""
		self.no_sector_editor = False
		self.read_only = False # FIXED: Absolute baseline write protection flag register
		
		# ARCHITECTURE UPGRADE: Every driver class declares its own structural boundaries natively
		self.default_dir_track = 18
		self.default_dir_sector = 0
		self.max_tracks_limit = 35
	def mount(self):
		raise NotImplementedError

	def list_directory(self):
		return self.file_list
		
	def check_target_for_duplicate_filename(self, target_name, force_replace=False):
		"""Scans the active directory blocks for a matching filename.
		Supports automated save-with-replace mode (force_replace=True) for nested image 
		saving, and standard verification reporting flags for the file copier loops.
		"""
		# Clean the incoming target string name and force standard uppercase matching parity
		sanitized_target = str(target_name).strip().upper()
		
		# Guard boundary check: Ensure the current filesystem handler instance has a populated file array
		if not hasattr(self, "file_list") or not self.file_list:
			return {"exists": False, "meta": None, "cleared": False}
			
		# Loop across all compiled directory records inside the active browser workspace
		for item in self.file_list:
			if item.get("name") == "..":
				continue
				
			current_entry_name = str(item.get("name", "")).strip().upper()
			
			# Execute a clean text comparison pass
			if current_entry_name == sanitized_target:
				matched_meta = item.get("vfs_meta", item.get("raw_meta"))
				
				# --- MODE A: AUTOMATED SAVE WITH REPLACE OVERRIDE ---
				if force_replace:
					# Force-purge the entry from our local active listing tracking cache array immediately
					self.file_list.remove(item)
					
					# Invoke your filesystem's native unlinking or delete engine if built
					if hasattr(self, "delete_virtual_file_by_meta"):
						self.delete_virtual_file_by_meta(matched_meta)
					elif hasattr(self, "unlink_file") and callable(self.unlink_file):
						self.unlink_file(current_entry_name)
						
					self.is_dirty = True
					return {"exists": True, "meta": matched_meta, "cleared": True}
					
				# --- MODE B: STANDARD SAFE COPY PROMPT NOTIFICATION ---
				return {"exists": True, "meta": matched_meta, "cleared": False}
				
		return {"exists": False, "meta": None, "cleared": False}

	def extract_file_bytes(self, vfs_meta_node):
		raise NotImplementedError

	def navigate_forward(self, track, sector, name):
		return False

	def navigate_backward(self):
		return False


class VFSBlockStream:
	"""Abstract baseline interface for all 256-byte block storage providers."""
	def read_block(self, block_index): 
		raise NotImplementedError
	def get_total_blocks(self): 
		raise NotImplementedError


class BaseContainerHandler:
	def __init__(self, vfs_stream):
		self.stream = vfs_stream
	def mount(self):
		raise NotImplementedError
	def print_current_directory(self):
		raise NotImplementedError


