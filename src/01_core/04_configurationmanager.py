class ConfigurationManager:
	"""Handles robust JSON configuration file operations with version matrix matching."""
	VERSION = "1.9.0"  # Advanced chassis update version branch step
	FILE_NAME = "c64_file_explorer_config.json"
	DEFAULT_CONFIG = {
		"version": VERSION,
		"visual_mode": "STANDARD",
		"respect_cbm_extensions": True,
		"default_cbm_filetype": "PRG",
		"override_cmd_hd_max_size": False,
		"custom_cmd_hd_size_str": "8G"		 # FIXED: Changed from blocks integer to clean humand-readable string token!
	}

	@staticmethod
	def load_application_settings():
		if not os.path.exists(ConfigurationManager.FILE_NAME):
			return dict(ConfigurationManager.DEFAULT_CONFIG)
		try:
			with open(ConfigurationManager.FILE_NAME, "r") as file_stream:
				loaded_data = json.load(file_stream)
			file_version = loaded_data.get("version", "0.0.0")
			if ConfigurationManager.is_version_newer(file_version, ConfigurationManager.VERSION):
				return dict(ConfigurationManager.DEFAULT_CONFIG)
			runtime_config = dict(ConfigurationManager.DEFAULT_CONFIG)
			for key, value in loaded_data.items():
				if key in runtime_config:
					runtime_config[key] = value
			runtime_config["version"] = ConfigurationManager.VERSION
			return runtime_config
		except Exception:
			return dict(ConfigurationManager.DEFAULT_CONFIG)

	@staticmethod
	def save_application_settings(config_dict):
		try:
			config_dict["version"] = ConfigurationManager.VERSION
			with open(ConfigurationManager.FILE_NAME, "w") as file_stream:
				json.dump(config_dict, file_stream, indent=4)
			return True
		except Exception:
			return False

	@staticmethod
	def is_version_newer(version_v1, version_v2):
		try:
			v1_parts = [int(x) for x in version_v1.split(".")]
			v2_parts = [int(x) for x in version_v2.split(".")]
			return v1_parts > v2_parts
		except Exception:
			return False

	@staticmethod
	def trigger_program_reboot():
		current_config = ConfigurationManager.load_application_settings()
		target_visual_mode = current_config.get("visual_mode", "STANDARD")
		executable_path = sys.executable.lower().replace("python.exe", "pythonw.exe") if sys.platform.startswith("win") else sys.executable
		if sys.platform.startswith("win"):
			if target_visual_mode == "PETSCII":
				if "python.exe" in executable_path.lower():
					executable_path = executable_path.lower().replace("python.exe", "pythonw.exe")
			else:
				if "pythonw.exe" in executable_path.lower():
					executable_path = executable_path.lower().replace("pythonw.exe", "python.exe")
		subprocess.Popen([executable_path] + sys.argv)
		sys.exit(0)


