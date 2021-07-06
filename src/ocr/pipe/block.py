import numpy as np

# class grouping all properties related to a single text block
class Block:

	def __init__(self, arg):

		if isinstance(arg, np.ndarray):
			self.image = arg
		elif isinstance(arg, str):
			self.block_id = arg

		self.bin_image = None
		self.inv_image = None
		self.font = None
		self.lines = None
		self.ocr = None
		self.ocr_words = None
		self.ocr_alto = None
		self.ocr_ori = None
		self.ocr_gt = None
		self.name = None
		self.score = None
		self.score_ori = None
		self.block_type = None
		self.alto_id = None
		self.ark = None
		self.year = None
		self.lang_ori = None
		self.lang_gt = None
		self.composed = False
		self.rotated = False
		self.coordinates = None
		self.offset_alto = None
		self.tokens_ori = None
		self.tokens_gt = None
		self.dict_ori = None
		self.garbage_ori = None
		self.trigrams_gt = None
		self.trigrams_ori = None
		self.enhance = None

	# returns a string version of the ocr output of the block
	def __str__(self):
		return_str = ""
		if self.ocr != None:
			if self.name != None:
				return_str += self.name + ':\n'
			for i, line in enumerate(self.ocr.split('\n')):
				return_str += str(i+1) + ':\t' + line + '\n'
		return return_str