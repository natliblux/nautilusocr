from numpy.lib.function_base import _parse_input_dimensions, append, copy
from enhance.mets_parser import get_mets_infos
from epr.features_epr import Features
from ocr.pipe.pipe import Models
from enhance.image_cropper import get_images
from enhance.alto_parser import get_block_data
from ocr.pipe.pipe import ocr
from tqdm import tqdm
from shutil import copytree
from lxml import etree
from enhance.mets_utils import adjust_ark_name, update_mets_file
import constants.constants as ct
import datetime
import os
import json
import time

def incomplete_mets(mets_path):
	print('mets not processed entirely: ' + mets_path)

# writes out completely processed mets issues
def add_to_json(blocks, path):
	if not os.path.exists(path):
		os.makedirs(path)
	with open(path+'data.jsonl', "a") as output:
		output.write(json.dumps(blocks) + "\n")

# pipeline for processing a single mets/alto package
def process_package(old_mets_path, models, output_path, features, required_epr):

	# start clock
	before = int(round(time.time() * 1000))

	# copy package to new destination
	old_package_dir = os.path.dirname(old_mets_path)
	new_package_dir = output_path + "/new-packages/" + old_package_dir.split('/')[-1]
	new_blocks_dir = output_path + "/new-blocks/"
	copytree(old_package_dir, new_package_dir)

	# xml parser
	parser = etree.XMLParser(remove_blank_text=True, encoding='utf-8')
	
	# get blocks
	blocks_info, ark, n_blocks = get_mets_infos(old_mets_path)
	processed_blocks = 0
	if ark == None:
		print("couldn't identify ark in " + old_mets_path)
		incomplete_mets(old_mets_path)
		return
	elif n_blocks == 0:
		print("found 0 blocks for requested types in " + old_mets_path)
		incomplete_mets(old_mets_path)
		return

	# create json dict for package
	json_dict = dict()
	json_dict[ark] = list()

	# loop over all alto files that contain at least 1 block
	for alto_id in tqdm(blocks_info):

		# working with blocks for this specific alto
		blocks_stuff = blocks_info[alto_id]['blocks']
		if blocks_stuff == None:
			incomplete_mets(old_mets_path)
			return

		# get coordinates for every blocks and alto xml tree
		alto_path = old_package_dir + blocks_info[alto_id]['alto'].replace("file://.", "")
		blocks_stuff, alto_tree = get_block_data(alto_path, blocks_stuff, features, required_epr, models)

		# for every alto image: crop the images for every block
		image_path = old_package_dir + blocks_info[alto_id]['image'].replace("file://.", "")
		blocks_stuff = get_images(image_path, blocks_stuff)
		if blocks_stuff == None:
			incomplete_mets(old_mets_path)
			return
		
		# for every block
		for block_id in blocks_stuff:

			ark = blocks_stuff[block_id].ark
			b_type = blocks_stuff[block_id].block_type
			composed = blocks_stuff[block_id].composed
			rotated = blocks_stuff[block_id].rotated
			text = blocks_stuff[block_id].ocr_ori
			lang = blocks_stuff[block_id].lang_ori
			enhance = blocks_stuff[block_id].enhance
			n_chars_ori = len(text)

			# check conditions for continuing with this block
			if rotated:
				print('ignoring rotated text block: ' + block_id + ' - alto: ' + alto_id + ' - ark: ' + ark + ' - mets: ' + old_mets_path)
				continue
			elif text == "":
				print('ignoring empty text block: ' + block_id + ' - alto: ' + alto_id + ' - ark: ' + ark + ' - mets: ' + old_mets_path)
				continue
			elif required_epr > -1:
				if lang not in ct.SUPPORTED_LANGS:
					print('ignoring ' + block_id + ' with unsupported lang (' + lang + ') belonging to ' + old_mets_path)
					continue
				elif lang not in models.epr['trigrams']:
					print('ignoring ' + block_id + ' since lang (' + lang + ') is not supported by epr model')
					continue

			# create block dict for data.jsonl
			block_dict = {
				'blockId': block_id,
				'altoId': alto_id,
				'epr': enhance,
				'processed': False,
				'altoPathOri': "./" + alto_path,
				'blockType': b_type,
				'composedBlock': composed,
				'charsOri': n_chars_ori
			}

			# block is not prcessed because there is no epr model or predicted enhancement is too low
			if enhance != None and enhance < required_epr:
				json_dict[ark].append(block_dict)
				continue

			# predicted enhancement is high enough: run ocr
			block = ocr(blocks_stuff[block_id], models, alto=True, addOffset=True)
			if block.ocr_alto == None or blocks_stuff[block_id].ocr_alto == None:
				incomplete_mets(old_mets_path)
				return

			# write new alto file to new blocks folder
			folder_path = new_blocks_dir+adjust_ark_name(ark)+'/'
			file_name = adjust_ark_name(ark)+'-'+alto_id+'-'+block_id+'.xml'
			file_path = folder_path+file_name
			if composed:
				file_name.replace('.xml', '-CB.xml')
			if not os.path.exists(folder_path):
				os.makedirs(folder_path)
			with open(file_path, 'w') as f:
				f.write(block.ocr_alto)
			
			# adjust dict for data.jsonl
			block_dict['processed'] = True
			block_dict['font'] = block.font
			splits = new_blocks_dir.split('/')
			alto_path_new = './'+splits[-3]+'/'+splits[-2]+'/'+splits[-1]+adjust_ark_name(ark)+'/'+file_name
			block_dict['altoPathNew'] = alto_path_new
			block_dict['langOri'] = lang
			block_dict['charsNew'] = len(block.ocr)
			json_dict[ark].append(block_dict)

			# increment counter
			processed_blocks += 1

		# removing old text lines of alto file
		for b_type in ['TextBlock', 'ComposedBlock']:
			for b in alto_tree.findall(".//{http://www.loc.gov/standards/alto/ns-v3#}" + b_type):
				if b.get("ID") in blocks_stuff and blocks_stuff[b.get("ID")].ocr_alto != None:
					for child in b.getchildren():
						child.getparent().remove(child)

		# adding new text lines to alto file
		for e in alto_tree.iter():
			if e.tag.endswith('TextBlock') or e.tag.endswith('ComposedBlock'):
				if e.get("ID") in blocks_stuff and blocks_stuff[e.get("ID")].ocr_alto != None:
					for e2 in etree.fromstring(blocks_stuff[e.get("ID")].ocr_alto):
						e2.tail = "\n"
						if e2.tag == 'TextLine':
							e.append(e2)
		etree.indent(alto_tree, space="	")

		# write new alto file
		alto_str = etree.tostring(alto_tree, pretty_print=True, xml_declaration=True, encoding="utf-8")
		mets_dir_small = old_package_dir.split('/')[-1]
		p = new_package_dir + alto_path.split(mets_dir_small)[-1]
		with open(p, 'wb') as f:
			f.write(alto_str)

	# adjust mets file
	update_mets_file(new_package_dir, old_mets_path, parser)

	time_needed = int(round(time.time() * 1000))-before
	print(ark + ' processed successfully in ' + str(time_needed) + ' ms (new ocr for ' + str(processed_blocks) + '/' + str(n_blocks) + ' target blocks)')

	return json_dict

# aims to enhance mets/alto by running ocr on a select subset of textblocks only
def improve_alto(mets_directory, required_epr):

	# save start date
	date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
	path = ct.OCR_OUTPUT_PATH + str(date)

	# create mets paths list
	mets_paths = list()
	for root, _, files in os.walk(mets_directory):
		for f in files:
			if f.endswith('-mets.xml'):
				mets_paths.append(root + '/' + f)
	print('identified all METS files within directory')

	# load models
	models = Models()
	models.load_final_models(True)
	if models.epr == None and required_epr > -1:
		required_epr = -1
		print('no enhancement prediction (epr) model found in models/final/ -> running ocr for all target blocks')

	features = None
	if required_epr > -1:
		features = Features()

	for mets_path in mets_paths:
		mets_path = mets_path.strip()
		result = process_package(mets_path, models, path, features, required_epr)
		if result != None:
			add_to_json(result, path+ "/new-blocks/")

	print("\nenhance completed - new METS/ALTO packages and blocks are located in " + path)