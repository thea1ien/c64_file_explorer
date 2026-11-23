class PETSCIIDecoder:
	"""Handles translation from Commodore PETSCII byte streams to clean ASCII."""
	@staticmethod
	def decode_name(byte_array):
		"""Fact-aligned global character translation mapping PETSCII blocks to safe string layouts.
		Natively auto-detects 16-byte filename blocks to enforce space-to-underline tracking 
		uniformly across ALL virtual CBM filesystems (.d64, .d71, .d81, .lnx).
		"""
		# Host OS Immunity Shield: If a modern path string slips in, pass it back untouched!
		if isinstance(byte_array, str):
			return byte_array
			
		# Convert incoming data to a clean, mutable numeric array (bytearray) natively
		numeric_array = bytearray(byte_array)
		
		# =========================================================================
		# 🚨 UNIFIED PLATFORM AUTODETECT: CORE SPACE-TO-UNDERLINE SHIELD 🚨
		# Instead of forcing individual drivers to pass a toggle flag, this checks 
		# if the incoming raw byte stream matches the standard fixed 16-byte width 
		# of a Commodore filename record slot. If it matches, it pre-scans all slots 
		# natively and transforms EVERY true $20 space byte directly into an underscore 
		# (0x5F) before conversion. This protects ALL CBM filesystems globally!
		# =========================================================================
		if len(numeric_array) == 16:
			for i in range(len(numeric_array)):
				if numeric_array[i] == 0x20:
					numeric_array[i] = 0x5F	 # Hex 0x5F is the ASCII/PETSCII underscore symbol
		# =========================================================================

		chars = []
		for b in numeric_array:
			# If we encounter an unallocated CBM padding block ($A0 or $00), we drop it cleanly
			if b == 0xA0 or b == 0x00:
				continue
			elif b == 0x5F:
				chars.append("_")
			elif 65 <= b <= 90:
				chars.append(chr(b + 32))
			elif 193 <= b <= 218:
				chars.append(chr(b - 128))
			elif 32 <= b <= 126:
				chars.append(chr(b))
			else:
				chars.append("_")
				
		return "".join(chars)


