import constants.constants as ct
import cv2
import numpy as np

# binarizes an image and returns it together with the inverted version
def bin_otsu(original):

	image = None

	# image to binary
	if not len(original.shape) == 2:
		image = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
	else:
		image = original
	_, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)


	# determine black on white or white on black
	total_pixels = len(image) * len(image[0])
	white_pixels = cv2.countNonZero(thresh)
	black_pixels = total_pixels - white_pixels
	if black_pixels < white_pixels:
		thresh = cv2.bitwise_not(thresh)

	# open - search for vertical white bars
	kernel = np.ones((ct.P1, 1), dtype=np.uint8)
	ver_bars = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
	
	# substraction - remove detected vertical bars from binarized image
	temp_image = cv2.subtract(thresh, ver_bars)

	# open - search for horizontal white bars
	kernel = np.ones((1, ct.P1), dtype=np.uint8)
	hor_bars = cv2.morphologyEx(temp_image, cv2.MORPH_OPEN, kernel)

	# substraction - remove detected horizontal bars from binarized image
	temp_image = cv2.subtract(temp_image, hor_bars)

	# dilate
	kernel = np.ones((2, 2), np.uint8)
	temp_image = cv2.dilate(temp_image, kernel, iterations=1)
	
	# pad image
	padded_image = cv2.copyMakeBorder(temp_image, 0, 0, ct.LINE_IMG_PAD, ct.LINE_IMG_PAD, cv2.BORDER_CONSTANT, value=(0, 0, 0))

	# invert image
	inv_padded_image = cv2.bitwise_not(padded_image)

	return (inv_padded_image, padded_image)