import cv2
import sys
import constants.constants as ct

# resizes char images so that they have size TARGET_CHAR_SIZE_FCR x TARGET_CHAR_SIZE_FCR
def resize_chars(char_imgs):

	final_imgs = list()
	for char_img in char_imgs:
		old_size = (len(char_img[0]), len(char_img))
		ratio = float(ct.TARGET_CHAR_SIZE_FCR)/max(old_size)
		new_size = tuple([min(ct.TARGET_CHAR_SIZE_FCR, int(x*ratio)) for x in old_size])
		if new_size[0] > 0 and new_size[1] > 0:
			char_img = cv2.resize(char_img, new_size)
			hor_pad = ct.TARGET_CHAR_SIZE_FCR - new_size[0]
			left_pad = hor_pad/2
			right_pad = hor_pad/2
			if hor_pad%2 == 1:
				left_pad -= 0.5
				right_pad += 0.5
			ver_pad = ct.TARGET_CHAR_SIZE_FCR - new_size[1]
			top_pad = ver_pad/2
			bottom_pad = ver_pad/2
			if ver_pad%2 == 1:
				top_pad -= 0.5
				bottom_pad += 0.5
			char_img = cv2.copyMakeBorder(char_img, int(top_pad), int(bottom_pad), int(left_pad), int(right_pad), cv2.BORDER_CONSTANT, value=(0, 0, 0))
			final_imgs.append(char_img)

	return final_imgs

# crops a single char from the image
def crop_chars(chars, matrix, img):

	# crop char image
	char_imgs = list()
	for char in chars:
		label = char[0]
		x = char[1]
		y = char[2]
		w = char[3]
		h = char[4]
		char_img = img[y: y+h, x: x+w]

		# filter out every other component that might be in the image
		char_matrix = matrix[y: y+h, x: x+w]
		for i in range(0, h):
			for j in range(0, w):
				if char_matrix[i][j] != 0 and char_matrix[i][j] != label:
					char_img[i][j] = 0
		char_imgs.append(char_img)

	return char_imgs

# pick n_chars, to be fed to the nn later, in round robin fashion by iterating over lines 
def pick_chars(chars_per_lines, n_chars):

	chars_found = list()
	iteration = 0
	while len(chars_found) < n_chars:
		found_at_least_one = False
		for line in chars_per_lines:
			if len(line) > iteration:
				chars_found.append(line[iteration])
				found_at_least_one = True
				if len(chars_found) == n_chars:
					found_at_least_one = False
					break
		if not found_at_least_one:
			break
		iteration += 1

	# n_chars == sys.maxsize in case we want to create train samples
	# otherwise we want to avoid an even number of chars for the nn to make predictions
	if n_chars != sys.maxsize and len(chars_found) % 2 == 0 and len(chars_found) > 0:
		chars_found = chars_found[:-1]

	return chars_found

# detects individual chars within image using the already available line coordinates
def isolate_chars(img, lines):

	# run connectedcomponents and calculate middle of every text line
	comp_output = cv2.connectedComponentsWithStats(img, connectivity=8)
	matrix = comp_output[1]
	stats = comp_output[2]
	y1_values = [x[1] for x in lines]
	y2_values = [x[3] for x in lines]
	mid_lines = [int(round((y1+y2)/2)) for y1, y2 in zip(y1_values, y2_values)]	

	# assign every component (of bound size) to the closest line
	chars_per_line = dict()
	for label, comp in enumerate(stats):
		if label == 0:
			continue
		x = comp[0]
		y = comp[1]
		w = comp[2]
		h = comp[3]
		if w<ct.MIN_CHAR_SIZE_FCR or w>ct.MAX_CHAR_SIZE_FCR or h<ct.MIN_CHAR_SIZE_FCR or h>ct.MAX_CHAR_SIZE_FCR:
			continue
		mid = int(round(y+(h/2)))
		line_index = 0
		min_diff = sys.maxsize
		for index, mid_line in enumerate(mid_lines):
			diff = abs(mid-mid_line)
			if diff < min_diff:
				min_diff = diff
				line_index = index
		char_coords = (label, x, y, w, h)
		if line_index in chars_per_line:
			chars_per_line[line_index].append(char_coords)
		else:
			chars_per_line[line_index] = [char_coords]

	# for every line, for all components, sort them by distance to their left neighbour
	# component with lowest x value (left most component) is assigned default value sys.maxsize
	# idea: extract first letters of words since they typically contain more clues for the font class
	final_chars = list()
	for line_index in chars_per_line:
		chars_list = chars_per_line[line_index]
		chars_list.sort(key=lambda pair: pair[1])
		char_distances = list()
		lastx2 = 0
		for i, char_coord in enumerate(chars_list):
			label = char_coord[0]
			x = char_coord[1]
			y = char_coord[2]
			w = char_coord[3]
			h = char_coord[4]
			dist = None
			if i==0:
				if line_index == 0:
					dist = sys.maxsize # we want to pick the first letter in the first line
				else:
					dist = 0 # we do not want to pick the first letters of the other line (they sometimes represent digits (not meaningful for font class))
			else:
				dist = x-lastx2
			char_distances.append([label, x, y, w, h, dist])
			lastx2 = x+h
		char_distances.sort(key=lambda pair: pair[5])
		char_distances.reverse()
		final_chars.append(char_distances)

	return final_chars, matrix

# returns a set of individual char images, originating from a text block image
def char_seg(img, lines, n_chars=sys.maxsize):

	# n_chars=sys.maxsize i.e. "get them all" is used to generate training samples
	chars, matrix = isolate_chars(img, lines)
	picked_chars = pick_chars(chars, n_chars)
	cropped_chars = crop_chars(picked_chars, matrix, img)
	resized_chars = resize_chars(cropped_chars)
	return resized_chars