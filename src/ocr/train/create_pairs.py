from random import randrange
from trdg.generators import GeneratorFromStrings
from ocr.pipe.bin import bin_otsu
from ocr.pipe.models import Models
from ocr.pipe.block import Block
from fcr.apply_fcr import predict_font
from lxml import etree
from seg.apply_seg import combiseg
from tqdm import tqdm

import constants.constants as ct
import cv2
import numpy as np
import os
import re
import json
import math

char_count = 0
line_count = dict()
max_line_count = dict()
char_dict = dict()

# used to create char distribution within train set
def analyze_text(text, font):

	global char_count
	global char_dict

	if not font in char_dict:
		char_dict[font] = dict()

	for c in text:
		if c.isspace():
			continue
		char_count += 1
		code = hex(ord(c))
		entry = (c, code)
		if entry in char_dict[font]:
			char_dict[font][entry] = char_dict[font][entry] + 1
		else:
			char_dict[font][entry] = 1

# saves a given img/txt pair
def save_pair(img, set_name, font, text, line_type):

	global line_count

	line_number = line_count[font]['total']
	analyze_text(text, font)
	name = str(line_number).zfill(ct.ZFILL)
	dir_font = ct.TRAIN_SETS_PATH + set_name + "/" + font + '/'
	if not os.path.exists(dir_font):
		os.makedirs(dir_font)
	cv2.imwrite(dir_font + name + ".png", img)
	file2write=open(dir_font+ name + ".gt.txt",'w', encoding='utf-8')
	file2write.write(text.strip())
	file2write.close()
	line_count[font][line_type] += 1
	line_count[font]['total'] += 1

# walks through directory and searchs for existing img/txt couples
def add_existing_pairs(existing_dir, set_name):

	print("integrating existing lines...")
	for root, _, files in tqdm(list(os.walk(existing_dir))):
		for f in files:
			path = root+'/'+f
			if f.endswith('.png') or f.endswith('.tif'):
				label_file = open(path.replace('.png', '.gt.txt').replace('.tif', '.gt.txt'), 'r')
				label = label_file.read().strip()
				label = check_against_whitelist(label)
				if label != None:	
					for font in ct.FONTS:
						if font in path:
							img = bin_otsu(cv2.imread(path))[0]
							save_pair(img, set_name, font, label, 'existing')
							break

# returns None in case text contains non-whitelasted chars - also replaces some special chars
def check_against_whitelist(text):

	new_text = ""
	for c in text:
		if c in ct.REPLACEMENTS:
			new_text += ct.REPLACEMENTS[c]
		elif c not in ct.WHITE_LIST and c!= ' ':
			return None
		else:
			new_text += c
	return new_text

# uses a list of tokens and creates a set of n text lines
def generate_art_lines(n, tokens):

	text_lines = list()
	stop = False
	while not stop:
		length = randrange(ct.ART_LINE_WORDS_MAX-ct.ART_LINE_WORDS_MIN) + ct.ART_LINE_WORDS_MIN
		text = ""
		for _ in range(0, length):
			text += tokens[randrange(len(tokens))] + ' '
		text = re.sub(r'\s+', ' ', text)
		text = check_against_whitelist(text)
		if text != None:
			text_lines.append(text)
			if len(text_lines) == n:
				stop = True
	return text_lines

# creates artificial img/txt paris using the trdg library
def generate_artificial_data(dataset_dir, text_lines, font):
	
	print(font)
	fonts = list()
	for root, _, files in os.walk(ct.ART_FONTS_PATH):
		for f in files:
			if font in root and f.endswith('.ttf'):
				fonts.append(root + '/' + f)
	
	BATCH_SIZE = 10
	
	iterations = int(math.ceil(len(text_lines)/BATCH_SIZE))

	with tqdm(total=len(text_lines)) as pbar:
		for i in range(0, iterations):

			sub_lines = None
			if i == iterations-1:
				sub_lines = text_lines[-(len(text_lines)%BATCH_SIZE):]
			else:
				sub_lines = text_lines[i*BATCH_SIZE:(i+1)*BATCH_SIZE]
			skew = 0
			distortion = 0
			blur = 0
			size = 38 + (i%10)
			if i%4 == 0:
				skew = 1
			if i%10 == 0:
				distortion = 3
			if i%8 == 0:
				blur = 1
			generator = GeneratorFromStrings(
				sub_lines,
				count=len(sub_lines),
				blur=blur,
				size=size,
				fonts = fonts,
				skewing_angle=skew,
				random_skew=True,
				background_type=1,
				random_blur=True,
				distorsion_type=distortion,
				fit=False,
				margins=(2, ct.LINE_IMG_PAD, 2, ct.LINE_IMG_PAD)
			)
			for img, lbl in generator:
				img, _ = bin_otsu(np.array(img))
				save_pair(img, dataset_dir, font, lbl, 'artificial')
			pbar.update(BATCH_SIZE)

# crops an individual text line from an image
def cut_text(x, y, width, height, image_file, text, font, set_name):

	text = check_against_whitelist(text)
	if text != None:
		cut_image = image_file[y: y+height, x: ct.LINE_IMG_PAD*2+x+width]
		save_pair(cut_image, set_name, font, text, 'new')

# extracts text line coordinate information and related text
def cut_lines(alto_path, block_id, block, min_confidence, set_name):
	tree = None
	try:
		tree = etree.parse(alto_path)
	except:
		pass
	if tree != None:
		x = None
		y = None
		width = None
		height = None
		text = ""
		correct_block = False
		for e in tree.iter():
			if e.tag.endswith('TextBlock') or e.tag.endswith('ComposedBlock'):
				b_id = e.get("ID")
				if block_id == None or block_id == b_id:
					correct_block = True
				else:
					correct_block = False
			elif e.tag.endswith("TextLine"):
				if correct_block:
					if text != "":
						if max_line_count[block.font]['total'] == -1 or max_line_count[block.font]['total'] > line_count[block.font]['total']:
							cut_text(x, y, width, height, block.bin_image, text, block.font, set_name)
					text = ""
					x = int(round(300.0/254.0*float(e.get("HPOS"))))
					y = int(round(300.0/254.0*float(e.get("VPOS"))))
					width = int(round(300.0/254.0*float(e.get("WIDTH"))))
					height = int(round(300.0/254.0*float(e.get("HEIGHT"))))
			elif e.tag.endswith("String"):
				if correct_block:
					confidences = e.get("CC")
					text += e.get("CONTENT")
					for c in confidences:
						if int(c) > min_confidence:
							text = ""
			elif e.tag.endswith("SP"):
				if correct_block:
					text += " "
		if text != "":
			if max_line_count[block.font]['total'] == -1 or max_line_count[block.font]['total'] > line_count[block.font]['total']:
				cut_text(x, y, width, height, block.bin_image, text, block.font, set_name)

# writes summary file that provides info on number of chars in train set
def add_fonts_info(info, font, dataset_dir):

	total_sum = sum([x[1] for x in info])
	with open(dataset_dir + '/'+ font + '-chars' + '.txt', 'w', encoding='utf-8') as f:
		for i in info:
			f.write(str(i[0][0]) + '\t' + str(i[0][1]) + '\t' + str(i[1]) + '\n')
		f.write('total: ' + str(total_sum))


# creates train img/txt pairs for ocr training purposes
def create_train_pairs(gt_set, confidence, set_name, existing_dir, n_lines, n_art_lines, art_text_file, fcr_model_name):
	
	global line_count
	global max_line_count

	for font in ct.FONTS:
		max_line_count[font] = {
			'artificial': n_art_lines,
			'total': n_lines
		}
		line_count[font] = {
			'existing': 0,
			'artificial': 0,
			'new': 0,
			'total': 0
		}

	# existing pairs that have been prepared beforehand
	if existing_dir != None:
		add_existing_pairs(existing_dir, set_name)

	# artificially created pairs
	if n_art_lines > 0:
		print('generating artificial lines...')
		for font in ct.FONTS:
			amount = max_line_count[font]['artificial']
			if amount > 0:
				art_tokens = list()
				with open(art_text_file, 'r', encoding='utf-8"') as text_file:
					for line in text_file:
						tokens = line.strip().split(" ")
						art_tokens = art_tokens + tokens
				art_lines = generate_art_lines(amount, art_tokens)
				generate_artificial_data(set_name, art_lines, font)

	# new pairs
	if gt_set != None:
		models = None
		print('creating new lines...')
		with open(gt_set, 'r', encoding='utf-8') as lines:
			lines = [line for line in lines]
			for line in tqdm(lines):
				if 'gt' not in line or 'image' not in line:
					print("json line does not include required 'image' and 'gt' properties")
					break
				info = json.loads(line)
				image = cv2.imread(info['image'])
				bin_img, inv_img = bin_otsu(image)
				block = Block(image)
				block.inv_image = inv_img
				block.bin_image = bin_img
				if 'font' in info and info['font'] in ct.FONTS:
					block.font = info['font']
				else:
					if models == None:
						models = Models()
						models.load_fcr_model(fcr_model_name)
					block.lines = combiseg(block.inv_image)
					block.font = predict_font(block, models)
					if block.font == 'unknown':
						print('could not predict font of block, skipping block...')
						continue
				gt_block_id = None
				if 'gt-block-id' in info:
					gt_block_id = info['gt-block-id']
				cut_lines(info['gt'], gt_block_id, block, confidence, set_name)

	# recap
	print(ct.TRAIN_SETS_PATH.split('/')[-2]+'/'+set_name + ' has been created and contains the following number of lines:')
	for font in ct.FONTS:
		if line_count[font]['total'] > 0:
			print(font + ': ' + str(line_count[font]))
			sorted_stats = sorted(char_dict[font].items(), key=lambda x:x[1], reverse=True)
			add_fonts_info(sorted_stats, font, ct.TRAIN_SETS_PATH+set_name)


