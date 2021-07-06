from enum import Enum
import argparse
import os
import sys

class ParseMode(Enum):
    SINGLE      = 'single'
    PARALLEL    = 'parallel'

    def __str__(self):
        return self.value

def readable_file(x):
	if not os.path.isfile(x):
		raise argparse.ArgumentTypeError('{} does not exist'.format(x))
	return x

def readable_folder(x):
	if not os.path.isdir(x):
		raise argparse.ArgumentTypeError('{} does not exist'.format(x))
	return x

def print_kvp(dictionary):
	print('Parameters:')
	for k, v in dictionary.items():
		print(' > {:15} : {}'.format(k,v))

# defines the actions and options stated in the readme file
SUBPARSERS = {

	# args order: short name, long name, required, default, type, action, help

	# optical character recognition (ocr)
	'set-ocr': {
		'args': [
			['-j', "--jsonl", False, None, readable_file, 'store', 'Path to jsonl file referencing image and ALTO files'],
			['-c', "--confidence", False, 9, int, 'store', 'Highest tolerated confidence value for every char in line'],
			['-m', "--model", False, 'fcr-model', str, 'store', 'Name of fcr model to be used in absence of font class indication'],
			['-e', "--existing", False, None, readable_folder, 'store', 'Path to directory containing existing pairs'],
			['-g', "--generated", False, 0, int, 'store', 'Number of artificially generated pairs to be added per font class'],
			['-t', "--text", False, None, readable_file, 'store', 'Path to text file containing text for artificial pairs'],
			['-n', "--nlines", False, -1, int, 'store', 'Maximum number of pairs per font class'],
			['-s', "--set", False, 'ocr-train-set', str, 'store', 'Name of ocr train set']
		],
		'func': 'set_ocr',
	},
	'train-ocr': {
		'args': [
			['-s', "--set", True, None, str, 'store', 'Name of ocr train set to be used'],
			['-f', "--font", True, None, str, 'store', 'Name of font that ocr model should be trained on'],
			['-m', "--model", False, 'ocr-model', str, 'store', 'Name of ocr model to be created'],
		],

		'func': 'train_ocr',
	},
	'test-ocr': {
		'args': [
			['-j', "--jsonl", True, None, readable_file, 'store', 'Path to jsonl file referencing image and ground truth ALTO files'],
			['-i', "--image", False, False, bool, 'store_true', 'Generate output image comparing ocr output with source image'],
			['-c', "--confidence", False, False, bool, 'store_true', 'Add ocr confidence (through font greyscale level) to output image']
		],
		'func': 'test_ocr',
	},
	'enhance': {
		'args': [
			['-d', '--directory', True, None, readable_folder, 'store', 'Path to directory containing all orignal METS/ALTO packages'],
			['-r', '--required', False, 0.0, float, 'store', 'Value for minimum required enhancement prediction']
		],
		'func': 'enhance',
	},
	'ocr': {
		'args': [
			['-d', "--directory", True, None, readable_folder, 'store', 'Path to directory containing target ocr source images'],
			['-a', "--alto", False, False, bool, 'store_true', 'Output ocr in ALTO format'],
			['-i', "--image", False, False, bool, 'store_true', 'Generate output image comparing ocr with source image'],
			['-c', "--confidence", False, False, bool, 'store_true', 'Add ocr confidence (through font greyscale level) to output image']
		],
		'func': 'ocr'
	},

	# font class recognizer (fcr)
	'set-fcr': {
		'args': [
			['-j', "--jsonl", True, None, readable_file, 'store', 'Path to jsonl file referencing image files and the respective font classes'],
			['-n', "--nchars", False, sys.maxsize, int, 'store', 'Maximum number of characters extracted from every image'],
			['-s', "--set", False, 'fcr-train-set', str, 'store', 'Name of fcr train set']
		],
		'func': 'set_fcr',
	},
	'train-fcr': {
		'args': [
			['-s', "--set", True, None, str, 'store', 'Name of fcr train set'],
			['-m', "--model", False, 'fcr-model', str, 'store', 'Name of fcr model to be created']
		],
		'func': 'train_fcr',
	},
	'test-fcr': {
		'args': [
			['-j', "--jsonl", True, None, readable_file, 'store', 'Path to jsonl file referencing image files and the respective font classes'],
			['-m', "--model", False, 'fcr-model', str, 'store', 'Name of fcr model to be tested']
		],
		'func': 'test_fcr',
	},

	# segmenter (seg)
	'test-seg': {
		'args': [
			['-j', "--jsonl", True, None, readable_file, 'store', 'Path to jsonl file referencing image and ALTO files']
		],
		'func': 'test_seg',
	},

	# enhancement predictor (epr)
	'train-epr': {
		'args': [
			['-j', "--jsonl", True, None, readable_file, 'store', 'Path to jsonl file referencing image, ground truth ALTO and original ALTO files'],
			['-m', "--model", False, 'epr-model', str, 'store', 'Name of epr model to be created']
		],
		'func': 'train_epr',
	},
	'test-epr': {
		'args': [
			['-m', "--model", False, 'epr-model', str, 'store', 'Name of epr model to be tested']
		],
		'func': 'test_epr',
	}
}