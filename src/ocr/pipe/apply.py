from ocr.pipe.models import Models
from ocr.pipe.pipe import ocr
from ocr.pipe.block import Block
from ocr.test.visualize_ocr import visualize_test
from tqdm import tqdm
import constants.constants as ct
import cv2
import os

# applies ocr on a set of images
def apply_on_images(images_dir, alto, visual, confidence):

	if not os.path.isdir(images_dir):
		print("cannot find directory " + images_dir)
		exit()

	models = Models()
	models.load_final_models(False)

	paths = list()

	for root, _, files in os.walk(images_dir):
		for f in files:
			if f.endswith('.png') or f.endswith('.tif'):
				paths.append(root + '/' + f)

	for path in tqdm(paths):
		img = cv2.imread(path)
		block = Block(img)
		block.name = path.split('/')[-1]
		block = ocr(block, models, alto=alto)

		# print in console and generate image
		if visual:
			visualize_test(block=block, confidence=confidence)
			print('\n\n' + str(block))
		
		# write text file
		output_dir = ct.OCR_OUTPUT_PATH + path.replace(images_dir, '').replace(block.name, '')
		if not os.path.isdir(output_dir):
			os.makedirs(output_dir)
		output_name = block.name.replace('.png','').replace('.tif','') + '.txt'
		if alto:
			output_name = output_name.replace('.txt', '.xml')
		with open(output_dir + output_name, 'w', encoding='utf-8') as out:
			if alto:
				out.write(block.ocr_alto)
			else:
				out.write(block.ocr)
	print('ocr completed and output can be viewed in ' + ct.OCR_OUTPUT_PATH.split('/')[-2] + '/')