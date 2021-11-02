import re
import constants.constants as ct
from PIL import Image
from numpy.core.shape_base import block
from ocr.pipe.models import Models
from kraken.rpred import rpred
from ocr.pipe.block import Block

# character recognition class invoking kraken engine
# good place to (in the future) add additional engines to combine outputs or compare performance
class Predictor:

	def __init__(self, block: Block, models: Models):

		self.block = block
		self.models = models

	# removes padding
	def readjust_lines(self):
		new_boxes = list()
		for box in self.block.lines:
			box[0] = max(0, (box[0] - ct.LINE_IMG_PAD))
			box[2] = max(0, (box[2] - ct.LINE_IMG_PAD))
			new_boxes.append(box)
		block.lines = new_boxes

	def post_process(self, line_txt):
		return [(m.start(), m.end()-1) for m in re.finditer(r'\S+', line_txt)]

	# formats kraken ocr output so that:
	# - block.ocr holds the plain text of the ocr output
	# - block.ocr_words holds a list, equaling
	# [
	# [ ["word1_row1", [x1, y1, x2, y2], confidence_string], ["word2_row1", [x1, y1, x2, y2], confidence_string] ]
	# [ ["word1_row2", [x1, y1, x2, y2], confidence_string], ... ]
	# ...
	# ]
	def format_output(self, output):

		if self.block.ocr_words == None:
			self.block.ocr_words = list()

		if not len(self.block.lines) == len(output):
			print("number of lines in output doesn't correspond to number of line bounding boxes")
			return None
		
		self.readjust_lines()

		line_strings = list()

		for line in output:
			txt = str(line)
			if txt == '' or txt.isspace():
				continue
			self.block.ocr_words.append(list())
			indices = self.post_process(txt)
			line_words = list()
			for pair in indices:
				word = ""
				box = [None, None, None, None]
				confidences = list()
				for i in range(pair[0], pair[1]+1):
					word += line[i][0]
					x1 = line[i][1][0]-ct.LINE_IMG_PAD
					x2 = line[i][1][2]-ct.LINE_IMG_PAD
					y1 = line[i][1][1]
					y2 = line[i][1][3]
					if box[0] == None or x1 < box[0]:
						box[0] = x1
					if box[1] == None or y1 < box[1]:
						box[1] = y1
					if box[2] == None or x2 > box[2]:
						box[2] = x2
					if box[3] == None or y2 > box[3]:
						box[3] = y2
					confidences.append(line[i][2])
					word = word.replace("t;", "t:")
				self.block.ocr_words[-1].append([word, box, confidences])
				line_words.append(word)
			line_strings.append(' '.join(line_words))
		self.block.ocr = '\n'.join(line_strings)	

	# improves kraken character bounding boxes so that neighbouring boxes "touch" each other
	def improve_boxes(self):

		for j, line in enumerate(self.block.ocr_words):
			x1_values = [box[0] for box in [word_info[1] for word_info in line]]
			x2_values = [box[2] for box in [word_info[1] for word_info in line]]
			x_values = sorted(x1_values + x2_values)
			new_x_values = list()
			for i, x in enumerate(x_values):
				if i == 0:
					new_x_values.append(max(0, self.block.lines[j][0]))
				elif i == (len(x_values)-1):
					new_x_values.append(min(len(self.block.image[0]), self.block.lines[j][2]))
				elif i%2 == 1:
					new_x = (round((x+x_values[i+1])/2.0-1)) # we shift the point, where two bounding boxes meet, by 1 point to the left
					new_x_values.append(new_x)
					new_x_values.append(new_x)
			new_line = line
			for i, word in enumerate(new_line):
				word[1][0] = new_x_values[i*2]
				word[1][2] = new_x_values[i*2+1]

	# performs character recognition using kraken models
	def kraken(self):

		model = self.models.ocr[ct.FONTS[0]]
		if self.block.font != "unknown":
			model = self.models.ocr[self.block.font]
		result = rpred(
			model,
			Image.fromarray(self.block.bin_image),
			self.lines_to_kraken(), 
			pad = 0,
			bidi_reordering = True)
		self.format_output([x for x in result])
		self.improve_boxes()
		return self.block

	# converts the image line bounding boxes to the kraken format 
	def lines_to_kraken(self):
		kraken_format = {
			'text_direction': 'horizontal-lr',
			'boxes': self.block.lines,
			'script_detection': False
		}
		return kraken_format
