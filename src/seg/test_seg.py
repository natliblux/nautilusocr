from seg.apply_seg import combiseg
from ocr.pipe.bin import bin_otsu
from lxml import etree
from tqdm import tqdm
import constants.constants as ct
import os
import json
import cv2

# parses xml file and returns bounding boxes of textlines
def get_boxes(file):

	gt_boxes = []  
	try:
		tree = etree.parse(file)
	except:
		print('problems parsing ALTO file')
		return
	if tree != None:
		for e in tree.iter():
			if e.tag.endswith('TextLine'):
				coords = [e.get("HPOS"), e.get("VPOS"), e.get("WIDTH"), e.get("HEIGHT")]
				x = int(round(300.0/254.0*float(coords[0])))
				y = int(round(300.0/254.0*float(coords[1])))
				w = int(round(300.0/254.0*float(coords[2])))
				h = int(round(300.0/254.0*float(coords[3])))
				gt_boxes.append([x, y, x+w, y+h])
	return gt_boxes

# loss function for testing combiseg segmenter
def evaluate(algo, gt):
	
	loss = len(gt) + max(0, len(algo)-len(gt))
	middles = [(x[1]+x[3]/2.0) for x in algo]
	gt_middles = [(x[1]+x[3]/2.0) for x in gt]
	
	for gt_mid in gt_middles:
		for mid in middles:
			if abs(gt_mid-mid) <= ct.TEST_THRESH_SEG:
				loss -= 1
				break
			
	return min(len(gt), loss)

# test combiseg segmentation algorithm
def test_segmentation(test_set):

	combiseg_loss = 0
	block_counter = 0

	with open(test_set, "r") as lines:
		lines = [line for line in lines]
		for line in tqdm(lines):
			info = json.loads(line)
			if not 'gt' in info or not 'image' in info:
				print("json line does not include required 'image' and 'gt' properties")
				continue
			gt_boxes = get_boxes(info['gt'])
			if gt_boxes == None or len(gt_boxes) < 2:
				continue
			image = cv2.imread(info['image'])
			block_counter += 1
			_, inv = bin_otsu(image)
			combiseg_loss += evaluate(combiseg(inv), gt_boxes)

	print("line segmentation test using combiseg algorithm completed with results:")
	print("blocks tested:\t\t" + str(block_counter))
	print("total loss:\t\t" + str(combiseg_loss))
	if block_counter > 0:
		print("loss/block:\t\t" + str(combiseg_loss/block_counter))
		print("loss explanation:\tnumber of text lines that are not correctly matched with a bounding box, plus the number of bounding boxes that do not correctly match any text line")