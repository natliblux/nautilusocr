import constants.constants as ct
import subprocess
import os

# trains an ocr model using the ketos command line utility that comes with kraken
def train_ocr_model(train_set_name, font, model_name):

	# check if images dir exists
	images_dir = ct.TRAIN_SETS_PATH + train_set_name + '/' + font + '/'
	if not os.path.isdir(images_dir):
		print(train_set_name + " in combination with " + font + " does not exist in " + ct.TRAIN_SETS_PATH)
		exit()

	# create paths file
	paths = list()
	for root, _, files in os.walk(images_dir):
		for f in files:
			if f.endswith('.png'):
				paths.append(root + '/' + f)
	path_to_paths = ct.TRAIN_SETS_PATH + train_set_name + '/' + font + '-paths.txt'
	with open(path_to_paths, 'a', encoding='utf-8') as paths_file:
		for p in paths:
			paths_file.write(p + '\n')

	model_name = model_name + "-" + font

	command = "ketos train --device " + ct.DEVICE + " --training-files " + path_to_paths + " -o " + ct.MODELS_PATH + model_name + " -N 3"
	subprocess.call(command, shell=True)
	for root, _, files in os.walk(ct.MODELS_PATH):
		for f in files:
			if f == model_name + '_best.mlmodel':
				os.rename(ct.MODELS_PATH + model_name + '_best.mlmodel', ct.MODELS_PATH + model_name + '.mlmodel')
			elif f.startswith(model_name) and f.endswith('.mlmodel'):
				os.remove(root + '/' + f)
	os.remove(path_to_paths)

	print('\n' + ct.MODELS_PATH.split('/')[-2] + '/' +  model_name + ' has been created')