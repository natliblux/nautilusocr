import constants.constants as ct
import sys
import cv2
import numpy as np
import collections

'''
schneipiseg algorithm explanation:

1) apply a couple of morpholgy operations, such as opening, dilation, substraction, addition and inversion, on the image
2) after the final operations, search for connectedcomponents, representing the text lines
3) for each component analyze the horizontal histogram (projection) and possibly split the text line into multiple ones
4) we then adjust the boxes so that they are increased in height, so they do not go out of bounds, and so that they have PAD
5) a final algorithm looks at the boxes and possibly merges some, in case they are overlapping too much or are contained inside each other

'''

# x1 and y1 cant be below 0
# x2 and y2 cant be so that x2>image_w or y2>image_h
# also: we extend the height of the line in both directions using P8
# also: we readjust the coordinates so they consider LINE_IMG_PAD
def adjust_boxes(boxes, im_w, im_h):

	new_boxes = list()
	for box in boxes:
		x1 = max(0, int(box[0]-ct.LINE_IMG_PAD))
		y1 = max(0, int(box[1] - ct.P8))
		x2 = min(im_w, int(box[2]+ct.LINE_IMG_PAD))
		y2 = min(im_h, int(box[3] + ct.P8))
		new_boxes.append((x1, y1, x2, y2))
	return combine_boxes(new_boxes)

# combines boxes that overlap vertically
def combine_boxes(boxes):

	'''
	algorithm idea:
	- combine boxes that have similar vertical coordinates, so that they represent the same text line
	- sort list of boxes using increasing y
	- iterate over sorted list:
		- if new box is contained in previous one (new_y1 > prev_y1 and new_y2 < prev_y2), it is the same line
		- else if OVERLAP_THRESH_SEG and OVERLAP2_THRESH_SEG determine whether they overlap enough to represent the same line
		- else it is a new line
		- only in last two cases we update the current/new box to be the previous box in the next iteration  
	'''
	
	# sort using y
	boxes.sort(key=lambda pair: pair[1])
	
	correct_boxes = []
	# iterate over all boxes
	last_y1 = 0
	last_y2 = 0
	for box in boxes:
		y1 = box[1]
		y2 = box[3]
		
		# current box is contained in last box in terms of height -> same line
		if y2 < last_y2:
			correct_boxes[-1].append(box) 
		else:
			two_line_height = max(1,y2-last_y1)
			last_line_height = max(1,last_y2-last_y1)
			new_line_height = max(1,y2-y1)
			two_line_overlap = last_y2-y1


			# overlap between current box and last box is more than 50% of combined height -> same line
			if two_line_overlap/two_line_height>ct.OVERLAP_THRESH_SEG or two_line_overlap/last_line_height>ct.OVERLAP2_THRESH_SEG or two_line_overlap/new_line_height>ct.OVERLAP2_THRESH_SEG:
				correct_boxes[-1].append(box)
			
			# current box is a new line
			else:
				correct_boxes.append([box])
			last_y1 = y1
			last_y2 = y2
	
	merged_correct_boxes = []
	for correct_box in correct_boxes:
		new_x1 = correct_box[0][0]
		new_y1 = correct_box[0][1]
		new_x2 = correct_box[0][2]
		new_y2 = correct_box[0][3]
		if len(correct_box) > 1:
			for block in correct_box:
				if block[0] < new_x1:
					new_x1 = block[0]
				if block[1] < new_y1:
					new_y1 = block[1]
				if block[2] > new_x2:
					new_x2 = block[2]
				if block[3] > new_y2:
					new_y2 = block[3]
		merged_correct_boxes.append([int(new_x1), int(new_y1), int(new_x2), int(new_y2)])
	return merged_correct_boxes

# segmentation algorithm that returns a set of line bounding boxes for a given text block binar input image_b
def combiseg(image_b):

	im_width = image_b.shape[1]
	im_height = image_b.shape[0]

	image_p = morph(image_b)
	boxes = comp(image_p, im_width, im_height)
	boxes_u = hist(image_b, boxes)
	boxes = adjust_boxes(boxes, im_width, im_height)
	boxes = combine_boxes(boxes)

	return adjust_boxes(boxes_u, im_width, im_height)

# first step of algorihtm: morphological operations
# image parameter is white text on black background
def morph(image):

	# dilation - dilate text areas to be wider
	kernel = np.ones((1, ct.P2), np.uint8)
	dilated_image = cv2.dilate(image, kernel, iterations=1)

	# invert - we want a white background
	inverted_image = cv2.bitwise_not(dilated_image)

	# open morhp - search for vertical white background bars (to exclude them from nackground dilate)
	kernel = np.ones((ct.P3, 1), dtype=np.uint8)
	bars = cv2.morphologyEx(inverted_image, cv2.MORPH_OPEN, kernel)

	# substraction - substract vertical white background bars from background
	background = cv2.subtract(inverted_image, bars)

	# open morph - search for horizontal white background bars which should seperate the text lines
	kernel = np.ones((1, ct.P4), dtype=np.uint8)
	background_seperators_image = cv2.morphologyEx(background, cv2.MORPH_OPEN, kernel)

	# dilation - dilate background seperators so they are wider and seperate text lines
	kernel = np.ones((1, ct.P5), np.uint8)
	dilated_background_image = cv2.dilate(background_seperators_image, kernel, iterations=1)

	# addition - add inverted image with the dilated horizontal background bars
	added_image = cv2.bitwise_or(inverted_image, dilated_background_image)
	
	# invert - we invert again so that the text is white again
	final_image = cv2.bitwise_not(added_image)

	return final_image

# search for connected components which should represent the text lines and determine the coordinates of our bounding boxes
def comp(image, image_width, image_height):
	_, _, stats, _ = cv2.connectedComponentsWithStats(image, connectivity=4)		
	boxes = list()
	for i, comp in enumerate(stats):
		if i == 0: # this is the background component which we ignore
			continue
		if comp[3] > ct.P6:
			boxes.append((comp[0], comp[1], comp[0]+comp[2], comp[1]+comp[3]))
	if len(boxes) == 0:
		boxes = [[0, 0, image_width, image_height]]

	return boxes

# uses horizontal histogram projections to eventually split bounding boxes
def hist(image, boxes):

	new_boxes = list()
	image = image / 255
	projection = np.sum(image, 1)

	for box in boxes:
		x1 = box[0]
		y1 = box[1]
		x2 = box[2]
		y2 = box[3]
		subprojection = projection[y1:y2+1]
		seperators = histogram_algo(subprojection, y1, y2)
		if len(seperators) > 0:
			last_seperator = y1
			seperators.append(y2)
			for seperator in seperators:
				if seperator-last_seperator > ct.P6:
					new_boxes.append([x1, last_seperator, x2, seperator])
				last_seperator = seperator
		else:
			new_boxes.append(box)
	return new_boxes

# finds the lowest splitting point between two peaks
def find_seperator(x1, x2, hist):

	lowest = sys.maxsize
	seperator = x1
	for x in range(x1, x2+1):
		if hist[x] < lowest:
			lowest = hist[x]
			seperator = x
	return seperator

# algorithm taken from the literature: R. Ptak, B. Ygadlo and O. Unold - 2017 - Projection-based text line segmentation with a variable threshold
def histogram_algo(projection, y1, y2):
	hist = dict(enumerate(projection.flatten(), y1))
	hist = collections.OrderedDict(reversed(sorted(hist.items(), key=lambda kv: kv[1])))

	n = len(hist)
	alpha = 0.1
	t = ct.P7 # relativ threshold - this has been tuned based on all gt blocks
	A = set() # checked points
	B = list() # peak widths
	MAX_HEIGHT = None
	
	for x in hist:
		height = hist[x]
		if MAX_HEIGHT == None:
			MAX_HEIGHT = height
		if height <= alpha*MAX_HEIGHT:
			break
		if x not in A:
			ta = t*height
			
			left_x = x
			right_x = x
			new_h = ta
			
			# search to the left
			while True and left_x > y1:
				new_h = hist[left_x-1]
				if new_h > ta:
					left_x -= 1
				else:
					break
				
			# search to the right
			while True and right_x < y2-1:
				new_h = hist[right_x+1]
				if new_h > ta:
					right_x += 1
				else:
					break
				
			R = set(range(left_x, right_x+1))
			
			if R.isdisjoint(A) and x != left_x and x != right_x:
				B.append(left_x)
				B.append(right_x)

			A = A | R

	B.sort()
	x1 = None
	seperators = list()
	for i, x in enumerate(B):
		if i == 0:
			continue
		if i%2 == 1:
			x1 = x
		else:
			x2 = x
			seperators.append(find_seperator(x1, x2, hist))
	return seperators