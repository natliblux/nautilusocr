import constants.constants as ct
from lxml import etree
from ocr.pipe.block import Block

START = 'start'
END = 'end'

# couldn't properly establish pairs of alto and images files
def mapping_problem():
	print('could not establish mapping between alto and image files')

# returns all block types that are relevant to determine whether a block is a target or not
def get_target_blocks():

	blocks = dict()
	for pattern in ct.BLOCK_TYPES_ALTO:
		for block_type in pattern:
			blocks[block_type] = END
	return blocks

# ultimately determines whether the block at the current parsing stage is a target, based on events_dict
# if the block is relevant, the block type is returned instead of none
def relevant_block_type(events_dict):
	for pattern in ct.BLOCK_TYPES_ALTO:
		is_current_state = True
		for block_type in pattern:
			if events_dict[block_type] == END:
				is_current_state = False
				break
		if is_current_state:
			return pattern[-1]
	return None

# returns target blocks info split by alto id, ark, issue_date, and the total number of target blocks
def get_mets_infos(mets_path):

	target_blocks_events = get_target_blocks()

	# those 4 values are returned
	block_data = dict()
	ark = None
	issue_date = None
	n_blocks = 0

	alto_file_paths = dict()
	image_file_paths = dict()
	target_altos = list()
	target_block_ids = list()
	target_block_types = list()
	altos_ordered = list()
	images_ordered = list()

	struct_map_event = END
	img_grp_event = END
	alto_grp_event = END
	date_issued_event = END

	tree = None
	try:
		tree = etree.iterparse(mets_path, events=(START, END))
	except:
		print('could not parse mets file at ' + mets_path)

	if tree != None:
		for event, e in tree:

			# toggle events
			if e.tag.endswith('structMap') and e.get('LABEL') == 'Physical Structure':
				struct_map_event = event
			elif e.tag.endswith('fileGrp') and e.get('ID') == 'ALTOGRP':
				alto_grp_event = event
			elif e.tag.endswith('fileGrp') and e.get('ID') == 'IMGGRP':
				img_grp_event = event
			elif e.tag.endswith('dmdSec') and e.get('ID') == 'MODSMD_PRINT':
				date_issued_event = event
			elif e.tag.endswith('div') and e.get('TYPE') in target_blocks_events:
				target_blocks_events[e.get('TYPE')] = event

			elif event == START:
			
				# get ark
				if e.tag.endswith('mets'):
					objid = e.get('OBJID')
					if objid != None:
						ark = 'ark:' + objid.split("ark:", 1)[1]

				# get image and alto file paths
				elif e.tag.endswith('FLocat'):
					parent = e.getparent()
					file_path = e.get('{http://www.w3.org/1999/xlink}href')
					if parent != None and parent.tag.endswith('file'):
						file_id = parent.get("ID")
						if alto_grp_event == START:
							alto_file_paths[file_id] = file_path
						elif img_grp_event == START:
							image_file_paths[file_id] = file_path

				# get alto/image mapping
				elif e.tag.endswith('area') and struct_map_event == START:
					file_id = e.get("FILEID")
					if file_id != None:
						if file_id in alto_file_paths:
							altos_ordered.append(file_id)
						if file_id in image_file_paths:
							images_ordered.append(file_id)

				# append a relevant block
				if e.tag.endswith('area'):
					is_relevant = relevant_block_type(target_blocks_events)
					if is_relevant != None:
						file_id = e.get("FILEID")
						block_id = e.get("BEGIN")
						if file_id != None and block_id != None:
							target_altos.append(file_id)
							target_block_ids.append(block_id)
							target_block_types.append(is_relevant)
							n_blocks += 1

				# date
				if e.tag.endswith('dateIssued') and date_issued_event == START:
					issue_date = e.text

		# check whether we found the same amount of alto and image files
		if len(altos_ordered) != len(images_ordered) or len(images_ordered) != len(image_file_paths) or len(image_file_paths) !=  len(alto_file_paths):
			mapping_problem()
			return (None, None, 0)

		# check whether year was determined
		if issue_date == None:
			print("couldn't extract issue year from mets file")
			exit()

		# fill block_data
		for i, block_id in enumerate(target_block_ids):
			alto_id = target_altos[i]
			try:
				index_alto = altos_ordered.index(alto_id)
				image_id = images_ordered[index_alto]
				alto_file = alto_file_paths[alto_id]
				image_file = image_file_paths[image_id]
				block_type = target_block_types[i]
			except:
				mapping_problem()
				return (None, None, 0)

			if not alto_id in block_data:
				block_data[alto_id] = {
					'image': image_file,
					'alto': alto_file,
					'blocks': dict()
				}

			if not block_id in block_data[alto_id]['blocks']:

				b = Block(block_id)
				b.block_type = block_type
				b.alto_id = alto_id
				b.ark = ark
				try:
					b.year = int(issue_date[:4])
				except:
					b.year = ""
					middle_year = str(round((ct.MIN_YEAR+ct.MAX_YEAR)/2))
					for i, element in enumerate(issue_date[:4]):
						if element in ["0123456789"]:
							b.year += element
						else:
							b.year += middle_year[i]
					b.year = int(b.year)

				block_data[alto_id]['blocks'][block_id] = b

	return (block_data, ark, n_blocks)