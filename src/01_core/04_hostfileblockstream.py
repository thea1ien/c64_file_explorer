class HostFileBlockStream(VFSBlockStream):
	def __init__(self, filepath): 
		self.path = filepath
		self.file_size = os.path.getsize(filepath)
		self.total_blocks = self.file_size // 256
	def read_block(self, block_index):
		if block_index >= self.total_blocks: 
			raise IndexError(f" HOST VFS EXCEPTION: Block request {block_index} overflows host file limit.")
		with open(self.path, "rb") as f: 
			f.seek(block_index * 256)
			return f.read(256)
	def get_total_blocks(self): 
		return self.total_blocks


