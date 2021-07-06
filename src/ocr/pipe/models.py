
import os
import json
import constants.constants as ct
import numpy as np
from kraken.lib.models import load_any
from tensorflow import keras

# class grouping all ml models that could be involved
class Models:

	def __init__(self):
		self.ocr = dict()
		self.fcr = None
		self.epr = None

	# loads all required models to apply ocr - they should be stored in /models/final/
	def load_final_models(self, require_enhance):
		for root, _, files in os.walk(ct.MODELS_PATH + 'final/'):
			for f in files:
				if f.endswith('.h5'):
					self.fcr = self.load_tensorflow_model(root + '/' + f)
					print("loaded " + f)
					continue
				for font in ct.FONTS:
					if font in f and f.endswith('.mlmodel'):
						self.ocr[font] = self.load_kraken_model(root + '/' + f)
						print("loaded " + f)
						break
				if f.endswith('.jsonl') and require_enhance:
					self.epr = self.load_json_model(root + '/' + f)
					print("loaded " + f)
		for font in ct.FONTS:
			if not font in self.ocr:
				self.missing_final_models()
		if self.fcr == None:
			self.missing_final_models()

	# at least one model is missing in /models/final/
	def missing_final_models(self):
		print("not all required models found in " + ct.MODELS_PATH + "final/, please consult " + ct.MODELS_PATH + "final/info.txt")
		exit()
					
	# load font recognition model named name
	def load_fcr_model(self, name):
		loaded = False
		for root, _, files in os.walk(ct.MODELS_PATH):
			for f in files:
				if f == name or f == name + '.h5':
					self.fcr = self.load_tensorflow_model(root + '/' + f)
					loaded = True
		if not loaded:
			self.model_not_loaded(name)

	# loads a kraken model at path
	def load_kraken_model(self, path):
		model = load_any(
			path,
			train = False,
			device = ct.DEVICE)
		return model

	# loads tensorflow model at path
	def load_tensorflow_model(self, path):
		return keras.models.load_model(path)

	# load enahncement prediction model named name
	def load_epr_model(self, name):
		path = None
		loaded = False
		for root, _, files in os.walk(ct.MODELS_PATH):
			for f in files:
				if f == name or f == name + '.jsonl':
					path = root + '/' + f
					self.epr = self.load_json_model(path)
					loaded = True
		if not loaded:
			self.model_not_loaded(name)

		return path

	# loads epr model at path
	def load_json_model(self, path):
		x_values = list()
		y_values = list()
		chars = list()
		trigrams = dict()
		k = None
		counter = 0
		with open(path, 'r', encoding='utf-8') as lines:
			for line in lines:
				counter += 1
				info = json.loads(line)

				# load language trigrams
				if counter == 1:
					trigrams = info
					model_langs = set([k for k in trigrams])
					target_langs = set(ct.SUPPORTED_LANGS)
					if not model_langs == target_langs:
						print("warning: epr model languages don't match supported languages in config.ini")
				# load models
				elif 'k' in info:
					k = info['k']
				else:
					x_values.append(info['x'])
					y_values.append(info['y'])
					chars.append(info['chars'])
		
		model = {
			'x': np.array(x_values),
			'y': np.array(y_values),
			'chars': np.array(chars),
			'trigrams': trigrams,
			'k': k
		}

		return model

	def model_not_loaded(self, name):
		print("couldn't find and load model named " + name)
		exit()
