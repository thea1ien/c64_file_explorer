class PreloadedBufferBlockStream(VFSBlockStream):
	def __init__(self, raw_byte_buffer): 
		self.buffer = raw_byte_buffer
		self.total_blocks = len(raw_byte_buffer) // 256
	def read_block(self, block_index):
		if block_index >= self.total_blocks: 
			raise IndexError(f" BUFFER VFS EXCEPTION: Block request {block_index} overflows buffer bounds.")
		start_offset = block_index * 256
		return self.buffer[start_offset : start_offset + 256]
	def get_total_blocks(self): 
		return self.total_blocks


