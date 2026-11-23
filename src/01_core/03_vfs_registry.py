class VFSDriverRegistry:
	"""Master Format Broker Matrix. Dynamically routes mounting and entry lookups."""
	_REGISTRY = {}

	@classmethod
	def register_format(cls, extension, handler_class):
		cls._REGISTRY[extension.lower()] = handler_class

	@classmethod
	def is_supported(cls, filename):
		_, ext = os.path.splitext(filename.lower())
		return ext in cls._REGISTRY

	@classmethod
	def instantiate_handler(cls, filename, payload_bytes):
		_, ext = os.path.splitext(filename.lower())
		driver_class = cls._REGISTRY.get(ext)
		if driver_class:
			instance = driver_class(payload_bytes, filename)
			instance.mount()
			return instance
		return None


class ImageGeometryRegistry:
	"""Tracks physical layout profiles and capacities for CBM container disk images."""
	PROFILES = {
		"D64": {"type": "1541", "directory_track": 18, "directory_sector": 0, "zones": [(17, 21), (24, 19), (30, 18), (35, 17)]},
		"G64": {"type": "GCR_Floppy", "directory_track": 18, "directory_sector": 0, "zones": [(17, 21), (24, 19), (30, 18), (42, 17)]},
		"D71": {"type": "1571", "directory_track": 18, "directory_sector": 0, "zones": [(17, 21), (24, 19), (30, 18), (35, 17), (52, 21), (59, 19), (65, 18), (70, 17)]},
		"D81": {"type": "1581", "directory_track": 40, "directory_sector": 0, "sectors_per_track": 40, "max_tracks": 80},
		"DNP": {"type": "Native", "directory_track": 1, "directory_sector": 1, "sectors_per_track": 256, "max_tracks": 255}
	}

	@staticmethod
	def get_sectors_in_track(profile_name, track, total_payload_blocks=None):
		prof = ImageGeometryRegistry.PROFILES[profile_name]
		if profile_name == "DNP" and total_payload_blocks is not None:
			# DNP ADAPTIVE SCALING CALCULATION: A native partition's track limits match 
			# the size of the container file directly. Map track structures cleanly.
			computed_max_tracks = total_payload_blocks // 256
			if computed_max_tracks == 0: computed_max_tracks = 1
			return 256 if track <= computed_max_tracks else 0
		if profile_name not in ImageGeometryRegistry.PROFILES:
			return 17 # Default
		if "sectors_per_track" in prof:
			return prof["sectors_per_track"]
		for max_track, sectors in prof["zones"]:
			if track <= max_track:
				return sectors
		return 17

	@staticmethod
	def translate_ts_to_block_index(profile_name, track, sector, total_payload_blocks=None):
		if profile_name in ["DNP"]:
			# Relative track indexing alignment: Track References start at 1, not 0
			return ((track - 1) * 256) + sector
		else:
			total_blocks = 0
			for t in range(1, track):
				total_blocks += ImageGeometryRegistry.get_sectors_in_track(profile_name, t)
			return total_blocks + sector


