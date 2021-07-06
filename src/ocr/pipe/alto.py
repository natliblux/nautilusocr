import sys
import xml.etree.ElementTree as ET
import constants.constants as ct
from xml.etree.ElementTree import tostring
from xml.dom import minidom

# remaps from kraken range to alto range
def remap(confidences):
	remapped_confidences = list()
	for conf in confidences:
		kraken_low = 0
		kraken_high = 1
		alto_low = 9
		alto_high = 0
		remapped_confidences.append(int(round(alto_low-((conf-kraken_low)*(alto_low-alto_high))/(kraken_high-kraken_low)+alto_high)))
	return remapped_confidences

# remap coordinate system
def convert(value):
	return int(round(254.0/300.0*float(value)))

# generates alto for ocr output
def generate_alto(block, addOffset):

	output = block.ocr_words

	offset_x = 0
	offset_y = 0
	if addOffset and block.offset_alto != None:
		offset_x = block.offset_alto[0]
		offset_y = block.offset_alto[1]

	counter = 0
	string_id = ""
	if block.block_id != None:
		string_id += block.block_id + '-'
	
	hyphen_part_1 = None

	block = ET.Element('TextBlock')
	for i, line in enumerate(output):
		line_element = ET.SubElement(block, 'TextLine')

		x1_line = sys.maxsize
		y1_line = sys.maxsize
		x2_line = 0
		y2_line = 0

		for j, word_info in enumerate(line):

			counter += 1
			word = ET.SubElement(line_element, 'String')

			conf_strings = map(str, remap(word_info[2]))

			x1_word = convert(word_info[1][0])
			x1_line = min(x1_word, x1_line)
			y1_word = convert(word_info[1][1])
			y1_line = min(y1_word, y1_line)
			x2_word = convert(word_info[1][2])
			x2_line = max(x2_word, x2_line)
			y2_word = convert(word_info[1][3])
			y2_line = max(y2_word, y2_line)

			# detected hyphen at end of previous line
			if hyphen_part_1 != None:
				word.set('CONTENT', word_info[0])
				word.set('SUBS_TYPE', 'HypPart2')
				word.set('SUBS_CONTENT', hyphen_part_1 + word_info[0])
				hyphen_part_1 = None

			# if its the last word of the line, contains hyphen at last index and isn't the last text line
			elif j == len(line)-1 and word_info[0][-1] in ct.HYPHENS and i != len(output)-1:
				word.set('CONTENT', word_info[0][:-1])
				word.set('SUBS_TYPE', 'HypPart1')
				word.set('SUBS_CONTENT', word_info[0][:-1] + output[i+1][0][0])
				hyphen = ET.SubElement(line_element, 'HYP')
				hyphen.set('CONTENT', word_info[0][-1])
				hyphen_part_1 = word_info[0][:-1]

			# regular case
			else:
				word.set('CONTENT', word_info[0])
				word.set('ID', string_id + str(counter).zfill(5))
				hyphen_part_1 = None

			word.set('CC', ''.join(conf_strings))
			word.set('HPOS', str(x1_word+offset_x))
			word.set('VPOS', str(y1_word+offset_y))
			word.set('WIDTH', str(x2_word-x1_word))
			word.set('HEIGHT', str(y2_word-y1_word))

			if j < len(line)-1:
				space = ET.SubElement(line_element, 'SP')

		line_element.set('HPOS', str(x1_line+offset_x))
		line_element.set('VPOS', str(y1_line+offset_y))
		line_element.set('WIDTH', str(x2_line-x1_line))
		line_element.set('HEIGHT', str(y2_line-y1_line))

	xmlstr = minidom.parseString(tostring(block, encoding='utf-8')).toprettyxml(indent='	').strip()
	return xmlstr