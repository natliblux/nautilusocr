import operator
import numpy as np
import constants.constants as ct

from fcr.char_segmenter_fcr import char_seg
from ocr.pipe.models import Models
from ocr.pipe.block import Block

# converts integer based font class to descriptive font class label
def class_to_label(font_class):
	if font_class == -1:
		return 'unknown'
	return ct.FONTS[font_class]

# applies the font recognition model on a binarized image using detected line bounding boxes 
def font_recognition(block: Block, models: Models):

	if block.inv_image is None or block.lines is None:
		print("block properties 'inv_image' and/or 'lines' not defined, cannot make font prediction")
		return (class_to_label(-1), -1)
	
	images = char_seg(block.inv_image, block.lines, ct.N_CHARS_FCR)
	processed_imgs = []
	if len(images) > 0:
		for img in images:
			pix = img.reshape(32, 32, 1)
			pix = pix / 255.0
			processed_imgs.append(pix)
		nn_output = models.fcr.predict(np.array(processed_imgs))
		predictions = nn_output.argmax(axis=-1)
		n_predications = len(predictions)
		classes_dict = dict()
		for prediction in predictions:
			if prediction in classes_dict:
				classes_dict[prediction] = classes_dict[prediction] + 1
			else:
				classes_dict[prediction] = 1
		final_class = max(classes_dict.items(), key=operator.itemgetter(1))[0]
		confidence = classes_dict[final_class]/n_predications
	else:
		final_class = -1
		confidence = -1
	
	return (class_to_label(final_class), confidence)

# only returns the font class
def predict_font(block: Block, models: Models):
	font_class, _ = font_recognition(block, models)
	return font_class

# returns the class and the confidence
def predict_font_confidence(block: Block, models: Models):
	font_class, font_confidence = font_recognition(block, models)
	return font_class, font_confidence

