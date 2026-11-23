class HostSystemScanner:
	"""Natively scans the local host operating system directory path structure."""
	@staticmethod
	def get_formatted_size(byte_count, is_dir):
		if is_dir:
			return "SUB-DIR"
		if byte_count < 1024:
			return f"{byte_count}B"
		elif byte_count < 1024 * 1024:
			return f"{byte_count // 1024}K"
		else:
			return f"{byte_count / (1024 * 1024):.1f}M"

	@staticmethod
	def scan_directory(target_path):
		raw_list = []
		if not os.path.exists(target_path) or not os.path.isdir(target_path):
			target_path = os.getcwd()
		try:
			parent_dir = os.path.dirname(os.path.abspath(target_path))
			if parent_dir != os.path.abspath(target_path):
				raw_list.append({
					"name": "..",
					"is_directory": True,
					"is_virtual_container": False,
					"size_display": "UP-DIR",
					"modify_time_str": " -- -- -- "
				})
			for item in os.listdir(target_path):
				full_item_path = os.path.join(target_path, item)
				try:
					stats = os.stat(full_item_path)
					is_directory = os.path.isdir(full_item_path)
					dt_object = datetime.fromtimestamp(stats.st_mtime)
					time_str = dt_object.strftime("%b %d %H:%M")
					_, file_extension = os.path.splitext(item.lower())
					is_virtual_container = file_extension in [".d64", ".dnp", ".d71", ".d81", ".g64", ".lnx"]
					raw_list.append({
						"name": item,
						"is_directory": is_directory,
						"is_virtual_container": is_virtual_container,
						"size_display": HostSystemScanner.get_formatted_size(stats.st_size, is_directory),
						"modify_time_str": time_str
					})
				except (PermissionError, FileNotFoundError):
					continue
		except Exception as err:
			pass

		directories_sorted = sorted([x for x in raw_list if x["name"] != ".." and x["is_directory"]], key=lambda k: k["name"].lower())
		files_sorted = sorted([x for x in raw_list if not x["is_directory"]], key=lambda k: k["name"].lower())
		return [x for x in raw_list if x["name"] == ".."] + directories_sorted + files_sorted


