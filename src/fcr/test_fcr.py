import os
import json
import cv2
from seg.apply_seg import combiseg
from fcr.apply_fcr import predict_font
from ocr.pipe.bin import bin_otsu
from ocr.pipe.models import Models
from ocr.pipe.block import Block
from tqdm import tqdm

# test fcr on a given test set
def test_model_fcr(test_set, model_name):

	models = Models()
	models.load_fcr_model(model_name)

	correct = 0
	wrong = 0

	with open(test_set, "r") as lines:
		lines = [line for line in lines]
		for line in tqdm(lines):
			info = json.loads(line)
			image_path = info["image"]
			gt_label = info["font"]
			img = cv2.imread(image_path)
			block = Block(img)
			_, inverted_image = bin_otsu(img)
			block.inv_image = inverted_image
			block.lines = combiseg(block.inv_image)
			pred = predict_font(block, models)
			if pred == gt_label:
				correct += 1
			else:
				wrong += 1
				
	print("font recognition test using " + model_name + " completed with results:")
	print("accuracy:\t" + str(correct/(correct+wrong)))