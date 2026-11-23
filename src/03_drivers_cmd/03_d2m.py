class D2MFileSystemPlugin(BaseCMDFloppyPlugin):
	def __init__(self, payload_data, archive_name="", *args, **kwargs):
		self.archive_name = archive_name # Fixed
		self.payload = bytearray(payload_data) if isinstance(payload_data, bytes) else payload_data
		self.format_type = "D2M"


