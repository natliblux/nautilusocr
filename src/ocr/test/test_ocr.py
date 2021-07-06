from numpy.core.shape_base import block
from ocr.pipe.models import Models
from ocr.pipe.block import Block
from ocr.pipe.pipe import ocr
from ocr.test.visualize_ocr import visualize_test
from ocr.test.scoring import Scoring
from lxml import etree
from tqdm import tqdm
import cv2
import json
import os

# tests ocr on a test set defined through a json file
def test_on_set(test_set, visual, confidence):
	if not os.path.isfile(test_set):
		print("cannot find " + test_set)
		exit()

	models = Models()
	models.load_final_models(False)

	# Scoring objects to store results
	new_ocr_scoring = Scoring()
	original_ocr_scoring = Scoring()

	# open test set json file
	total = 0
	with open(test_set, 'r', encoding='utf-8') as lines:
		lines = [line for line in lines]
		for line in tqdm(lines):
			info = json.loads(line)
			if not 'image' in info or not 'gt' in info or not 'id' in info:
				print("json line does not include required 'image', 'gt' and 'id' properties")
				continue
			image = cv2.imread(info['image'])

			block = Block(image)

			# get gt text and run ocr
			gt_block_id = None
			if 'gt-block-id' in info:
				gt_block_id = info['gt-block-id']

			block.name = info['id']

			block.ocr_gt = get_alto_text(info['gt'], gt_block_id)
			block = ocr(block, models)
			block.score = new_ocr_scoring.get_score(block, new_ocr=True, average=False)
			
			# compare to original ocr output
			if 'ori' in info:
				# ori_block = Block(image)
				if 'ori-block-id' in info:
					ori_block_id = info['ori-block-id']
				block.ocr_ori = get_alto_text(info['ori'], ori_block_id)
				block.score_ori = original_ocr_scoring.get_score(block, new_ocr=False, average=False)

			# render image
			if visual:
				visualize_test(block=block, confidence=confidence)

	# print results
	print("ocr test completed with average results:")
	print("new ocr score:\t" + str(round(new_ocr_scoring.get_set_score(), 3)))
	if original_ocr_scoring.get_set_score() != None:
		print("ori ocr score:\t" + str(round(original_ocr_scoring.get_set_score(), 3)))
				

# retrieves text of TextBlock from an alto xml file at alto_path (no block_id sugggest file contains only one block)
def get_alto_text(alto_path, block_id=None):
	tree = None
	try:
		tree = etree.parse(alto_path)
	except:
		print('problem opening alto at path ' + alto_path)
	block_text = list()
	line_text = ""
	correct_block = False
	if tree != None:
		for e in tree.iter():
			if e.tag.endswith("TextBlock"):
				if e.get('ID') == block_id:
					correct_block = True
				elif block_id == None:
					correct_block = True
				else:
					correct_block = False
			elif e.tag.endswith("String"):
				word = e.get("CONTENT")
				if word != None and correct_block:
					line_text += word
			elif e.tag.endswith('SP'):
				if correct_block:
					line_text += " "
			elif e.tag.endswith('TextLine'):
				if correct_block:
					if line_text != "":
						block_text.append(line_text)
						line_text = ""
		if line_text != "":
			block_text.append(line_text)
	return '\n'.join(block_text)