from xml.dom.minidom import parse
from lxml import etree
import constants.constants as ct
import numpy as np
from epr.apply_epr import predict

# adds text and image coordinate information to the text block objects
def get_block_data(alto_path, blocks_dict, features, required_epr, models):

	correct_block = False
	counter = 0
	block_id = None
	tree = None

	try:
		parser = etree.XMLParser(remove_blank_text=True, encoding='utf-8')
		tree = etree.parse(alto_path, parser).getroot()
	except:
		print('could not parse ALTO file at ' + alto_path)
	if tree != None:
		etree.indent(tree, space="	")
		for e in tree.iter():
			if e.tag.endswith('TextBlock') or e.tag.endswith('ComposedBlock'):
				block_id = e.get("ID")
				if block_id != None and block_id in blocks_dict:
					blocks_dict[block_id].ocr_ori = ""
					correct_block = True
					coords = [e.get("HPOS"), e.get("VPOS"), e.get("WIDTH"), e.get("HEIGHT")]
					for c in coords:
						try:
							val = int(c)
							if val < 0:
								print('negative integer coordinate detected in ' + alto_path)
								return None
						except ValueError:
							print('non integer coordinate detected in ' + alto_path)
							return None
					x = int(round(300.0/254.0*float(coords[0])))
					y = int(round(300.0/254.0*float(coords[1])))
					w = int(round(300.0/254.0*float(coords[2])))
					h = int(round(300.0/254.0*float(coords[3])))
					coordinates = (x, y, w, h)
					blocks_dict[block_id].coordinates = coordinates
					blocks_dict[block_id].offset_alto = (int(coords[0]), int(coords[1]))
					if e.tag == 'ComposedBlock':
						blocks_dict[block_id].composed = True
					rotated = e.get('ROTATION')
					if rotated != None:
						blocks_dict[block_id].rotated = True
					counter += 1
				else:
					correct_block = False
			elif e.tag.endswith('TextLine'):
				if correct_block:
					if blocks_dict[block_id].ocr_ori != "":
						blocks_dict[block_id].ocr_ori += '\n'
			elif e.tag.endswith('SP'):
				if correct_block:
						blocks_dict[block_id].ocr_ori += ' '
			elif e.tag.endswith('String'):
				if correct_block:
					new_text = e.get('CONTENT')
					if isinstance(new_text, str):
						blocks_dict[block_id].ocr_ori += new_text
					else:
						print('CONTENT missing in ' + alto_path)
	if counter != len(blocks_dict):
		print('could not find all blocks in ' + alto_path)
		return (None, None)

	if required_epr > -1 and features != None:
		for block_id in blocks_dict:
			block = blocks_dict[block_id]
			block.tokens_ori = features.get_tokens(block.ocr_ori)
			lang_ori, trigrams_ori = features.get_ngrams(block.tokens_ori, block.ocr_ori)
			block.lang_ori = lang_ori
			if block.lang_ori in ct.SUPPORTED_LANGS and block.lang_ori in models.epr['trigrams']:
				block = features.compute_features_ori(block)
				n_gram_score = features.get_ngram_score(trigrams_ori, models.epr['trigrams'][block.lang_ori])
				x = np.array([block.dict_ori, n_gram_score, block.garbage_ori, features.scale_year(block.year)])
				block.enhance = predict(models.epr, x, models.epr['k'])

	return (blocks_dict, tree)