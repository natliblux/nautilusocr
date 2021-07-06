import json
import cv2
import os
import constants.constants as ct
from fcr.char_segmenter_fcr import char_seg
from ocr.pipe.bin import bin_otsu
from seg.apply_seg import combiseg
from tqdm import tqdm

# creates train set by segmenting entire blocks into individual chars based on font
def create_train_set_fcr(json_set, max_chars, set_name):

	class_counters = dict()
	for font in ct.FONTS:
		class_counters[font] = 0

	with open(json_set, "r") as lines:
		lines = [line for line in lines]
		for line in tqdm(lines):
			info = json.loads(line)
			if 'font' in info and 'image' in info:
				font = info['font']
				if font in ct.FONTS:
					path = info['image']
					img = cv2.imread(path)
					_, inverted_image = bin_otsu(img)
					lines = combiseg(inverted_image)
					train_chars = char_seg(inverted_image, lines, max_chars)
					for train_char in train_chars:
						folder_name = ct.TRAIN_SETS_PATH + set_name + '/' + font
						if not os.path.isdir(folder_name):
							os.makedirs(folder_name)
						cv2.imwrite(folder_name + "/" + str(class_counters[font]).zfill(ct.ZFILL) + ".png", train_char)
						class_counters[font] = class_counters[font] + 1
			else:
				print("ignoring text block since 'font' and/or 'image' properties are missing")
	print(ct.TRAIN_SETS_PATH.split('/')[-2] + '/' + set_name + ' has been created and contains the following number of chars:')
	print(class_counters)