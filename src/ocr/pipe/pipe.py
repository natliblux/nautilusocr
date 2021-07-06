from ocr.pipe.bin import bin_otsu
from seg.apply_seg import combiseg
from fcr.apply_fcr import predict_font
from ocr.pipe.models import Models
from ocr.pipe.block import Block
from ocr.pipe.pred import Predictor
from ocr.pipe.alto import generate_alto

# ocr applied on image using models object, alto format can be requested 
def ocr(block: Block, models: Models, alto=False, addOffset=False):

	# binarization
	bin_image, inv_image = bin_otsu(block.image)
	block.bin_image = bin_image
	block.inv_image = inv_image

	# segmentation
	block.lines = combiseg(block.inv_image)

	# font recognition
	block.font = predict_font(block, models)

	# character recognition
	predictor = Predictor(block, models)
	block = predictor.kraken()

	# alto generation
	if alto:
		block.ocr_alto = generate_alto(block, addOffset)

	return block