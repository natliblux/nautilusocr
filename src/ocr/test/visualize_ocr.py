from PIL import Image, ImageDraw, ImageFont
from ocr.pipe.block import Block
import constants.constants as ct
import os

# determines font size and spacing between characters for drawing
def get_params(new_block: Block):

	total_height = 0
	for line in new_block.lines:
		total_height += line[3]-line[1]
	average_height = total_height / len(new_block.lines)

	font_size = int(average_height*0.8)
	font = ImageFont.truetype(ct.VIS_FONT_PATH, font_size)
	bold_font = ImageFont.truetype(ct.VIS_FONT_BOLD_PATH, int(font_size*1.15))
	step_size = int(float(font_size)*0.55)

	return font, bold_font, step_size

# draws a given ocr output (original or new) and optionally reflects ocr engine confidence through color
def draw_ocr_block(block: Block, new_ocr, draw, x, step_size, font, bold_font, confidence):

	title = "new ocr"
	if block.score != None:
		title += " - " + str(round(block.score, 3))
	if not new_ocr:
		title = "ori ocr"
		if block.score_ori != None:
			title += " - " + str(round(block.score_ori, 3))
	draw.text((x, ct.LINE_IMG_PAD), title, (255, 150, 50), font=bold_font)

	y = 0
	x_temp = x
	max_x = 0

	data = None
	if new_ocr:
		data = block.ocr
		if block.ocr_words != None:
			data = block.ocr_words
	else:
		data = block.ocr_ori

	y = None

	# plain text str, used for original ocr
	if isinstance(data, str):
		text_lines = data.split("\n")
		for i, text_line in enumerate(text_lines):
			if i < len(block.lines):
				y = ct.LINE_IMG_PAD*3+block.lines[i][1]+(block.lines[i][3]-block.lines[i][1])/4*3
			else:
				y += block.lines[-1][3]-block.lines[-1][1]
			draw.text((x_temp, y), str(i+1)+")", (0, 0, 0), font=font)
			x_temp += step_size*4
			for c in text_line:
				draw.text((x_temp, y), str(c), (0, 0, 0), font=font)
				x_temp += step_size
			if x_temp > max_x:
				max_x = x_temp
			x_temp = x

	# new ocr 
	else:
		for i, text_line in enumerate(data):
			if i < len(block.lines):
				y = ct.LINE_IMG_PAD*3+block.lines[i][1]+(block.lines[i][3]-block.lines[i][1])/4*3
			else:
				y += block.lines[-1][3]-block.lines[-1][1]
			draw.text((x_temp, y), str(i+1)+")", (0, 0, 0), font=font)
			x_temp += step_size*4
			for word in text_line:
				for j, c in enumerate(word[0] + ' '):
					color = (0, 0, 0)
					if confidence and c!= ' ':
						color = min(255, int((1-word[2][j])*2*255))
						color = (color, color, color)
					draw.text((x_temp, y), str(c), color, font=font)
					x_temp += step_size
			if x_temp > max_x:
				max_x = x_temp
			x_temp = x

	return max_x

# generates an image that compares ocr to source image and optionally to original ocr
def visualize_test(block: Block, confidence=False):

	# create new image
	image = Image.fromarray(block.image)
	width, height = image.size
	new_image_w	= width*10
	new_image_h = height+5*ct.LINE_IMG_PAD
	newImage = Image.new('RGB', (new_image_w, new_image_h), (255, 255, 255))
	draw = ImageDraw.Draw(newImage)

	# some params
	font, bold_font, step_size = get_params(block)
	x = ct.LINE_IMG_PAD

	# old ocr (optional)
	if block.ocr_ori != None:
		x = draw_ocr_block(block, False, draw, x, step_size, font, bold_font, confidence)
	
	# source image
	x += ct.LINE_IMG_PAD
	scan_x = x
	draw.text((x, ct.LINE_IMG_PAD), block.name+' - '+block.font, (255, 150, 50), font=bold_font)
	newImage.paste(image, (x, ct.LINE_IMG_PAD*4, width+x, height+ct.LINE_IMG_PAD*4))
	x += + ct.LINE_IMG_PAD + width

	# new ocr
	x = draw_ocr_block(block, True, draw, x, step_size, font, bold_font, confidence)

	# draw word boxes for new ocr
	newImage = draw_word_boxes(block, newImage, scan_x)

	# crop image to smallest size
	cropped_image = newImage.crop((0, 0, x+ct.LINE_IMG_PAD, height+5*ct.LINE_IMG_PAD))

	# save image
	if not os.path.isdir(ct.OCR_OUTPUT_PATH):
		os.makedirs(ct.OCR_OUTPUT_PATH)
	cropped_image.save(ct.OCR_OUTPUT_PATH + block.name.replace('.png', '').replace('.tif', '') + '.png')

# translucent word bounding boxes for every word in new ocr output
def draw_word_boxes(block: Block, newImage, scan_x):

	TRANSPARENCY = .6
	OPACITY = int(255 * TRANSPARENCY)
	color = (139, 196, 65)
	rect_w = 4

	for line in block.ocr_words:
		for word in line:
			left = word[1][0] + scan_x
			top = word[1][1] + ct.LINE_IMG_PAD*4
			right = word[1][2] + scan_x
			bottom = word[1][3] + ct.LINE_IMG_PAD*4
			draw_cords = (int(round(left-rect_w/2.0)), int(round(top-rect_w/2.0)), int(round(right+rect_w/2.0)), int(round(bottom+rect_w/2.0)))
			newImage = newImage.convert("RGBA")
			overlay = Image.new('RGBA', newImage.size, color+(0,))
			draw = ImageDraw.Draw(overlay)  # Create a context for drawing things on it.
			draw.rectangle(draw_cords, outline=color+(OPACITY,), width=int(round(rect_w)))
			newImage = Image.alpha_composite(newImage, overlay)
			newImage = newImage.convert("RGB")
			
	return newImage