from epr.features_epr import Features
from ocr.test.scoring import Scoring
from ocr.test.test_ocr import get_alto_text
from ocr.pipe.block import Block
from ocr.pipe.pipe import ocr
from ocr.pipe.models import Models
from ocr.test.scoring import Scoring
from tqdm import tqdm
import constants.constants as ct
import json
import cv2
import os

def train_epr_model(inventory, model_name):

	features = Features()
	scoring = Scoring()
	models = Models()
	models.load_final_models(require_enhance=False)

	X, Y, chars, trigrams, lang_trigrams = get_data(inventory, models, scoring, features)

	lang_ngrams = dict()
	for lang in lang_trigrams:
		lang_ngrams[lang] = sorted(lang_trigrams[lang].items(), key=lambda x:x[1], reverse=True)
		lang_ngrams[lang] = lang_ngrams[lang][:ct.AMOUNT_NGRAMS]
		lang_ngrams[lang] = [n[0] for n in lang_ngrams[lang]]
	
	# we replace x[1] from language information to trigram score
	for i, _ in enumerate(X):
		X[i][1] = features.get_ngram_score(trigrams[i], lang_ngrams[X[i][1]])

	if not os.path.isdir(ct.MODELS_PATH):
		os.makedirs(ct.MODELS_PATH)

	if not model_name.endswith('jsonl'):
		model_name += '.jsonl'

	open(ct.MODELS_PATH + model_name, 'w').close()
	store_ngrams(lang_ngrams, model_name)
	store_model(X, Y, chars, model_name)

# stores language ngram information as first line of jsonl
def store_ngrams(lang_ngrams, model_name):

	with open(ct.MODELS_PATH + model_name, 'a', encoding='utf-8') as f:
		json_string = json.dumps(lang_ngrams, ensure_ascii=False).encode('utf8')
		f.write(json_string.decode())
		f.write('\n')

# stores actual model values
def store_model(X, Y, chars, model_name):

	with open(ct.MODELS_PATH + model_name, 'a', encoding='utf-8') as f:
		for i in range(0, len(X)):
			entry = {
				'y': Y[i],
				'x': X[i],
				'chars': chars[i]
			}
			json_string = json.dumps(entry, ensure_ascii=False).encode('utf8')
			f.write(json_string.decode())
			f.write('\n')
		k_dict = {
			'k': min(ct.DEFAULT_K, len(X))
		}
		f.write(json.dumps(k_dict))

	print(ct.MODELS_PATH.split('/')[-2] + '/' + model_name + ' has been created')

def get_data(inventory, models, scoring, features):
	
	x_values = list()
	y_values = list()
	chars = list()
	trigrams = list()
	lang_trigrams = dict()

	for lang in ct.SUPPORTED_LANGS:
		lang_trigrams[lang] = dict()

	with open(inventory, 'r', encoding='utf-8') as lines:
		lines = [line for line in lines]

		for line in tqdm(lines):
			
			info = json.loads(line)

			# create block based on image
			if not 'image' in info or not 'gt' in info or not 'ori' in info or not 'year' in info:
				print("json line does not include required 'image', 'gt', 'ori' and 'year' properties")
			year = None
			try:
				year = features.scale_year(int(info['year']))
			except:
				print("'year' property is not of type integer")
				exit()

			image = cv2.imread(info['image'])
			block = Block(image)

			# set gt ocr
			gt_block_id = None
			if 'gt-block-id' in info:
				gt_block_id = info['gt-block-id']
			block.ocr_gt = get_alto_text(info['gt'], gt_block_id)

			# set ori ocr
			ori_block_id = None
			if 'ori-block-id' in info:
				ori_block_id = info['ori-block-id']
			block.ocr_ori = get_alto_text(info['ori'], ori_block_id)
			
			# set new ocr
			block = ocr(block, models)

			# get enhance score
			new_score = scoring.get_score(block, new_ocr=True)
			old_score = scoring.get_score(block, new_ocr=False)
			enhance = new_score-old_score

			# get gt trigrams
			block.tokens_gt = features.get_tokens(block.ocr_gt)
			lang_gt, trigrams_gt = features.get_ngrams(block.tokens_gt, block.ocr_gt)

			# get ori trigrams
			block.tokens_ori = features.get_tokens(block.ocr_ori)
			lang_ori, trigrams_ori = features.get_ngrams(block.tokens_ori, block.ocr_ori)
			block.lang_ori = lang_ori

			# get ori features	
			block = features.compute_features_ori(block)

			# collect all trigrams in the gt language
			if lang_gt in ct.SUPPORTED_LANGS:
				for tri in trigrams_gt:
					if tri not in lang_trigrams[lang_gt]:
						lang_trigrams[lang_gt][tri] = 1
					else:
						lang_trigrams[lang_gt][tri] += 1

			# collect model values
			if lang_ori in ct.SUPPORTED_LANGS:
				y_values.append(enhance)
				x_values.append([block.dict_ori, lang_ori, block.garbage_ori, year])
				chars.append(len(block.ocr_ori))
				trigrams.append(trigrams_ori)

	return (x_values, y_values, chars, trigrams, lang_trigrams)