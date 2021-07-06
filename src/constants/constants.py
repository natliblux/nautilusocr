from pathlib import Path

########### fonts ###########
FONTS = ['antiqua', 'fraktur']

########### other ###########
ZFILL = 6
DEVICE = 'cpu'

MODELS_PATH = str(Path(__file__).parent.parent.parent.absolute()) + '/models/'
TRAIN_SETS_PATH = str(Path(__file__).parent.parent.parent.absolute()) + '/trainsets/'
ART_FONTS_PATH = str(Path(__file__).parent.parent.parent.absolute()) + '/fonts/artificial/'
VIS_FONT_PATH = str(Path(__file__).parent.parent.parent.absolute()) + '/fonts/image/Everson_Mono.ttf'
VIS_FONT_BOLD_PATH = str(Path(__file__).parent.parent.parent.absolute()) + '/fonts/image/Everson_Mono_Bold.ttf'
OCR_OUTPUT_PATH = str(Path(__file__).parent.parent.parent.absolute()) + '/output/'
CONFIG_PATH = str(Path(__file__).parent.parent.parent.absolute()) + '/config.ini'
DICTS_PATH = str(Path(__file__).parent.parent.parent.absolute()) + '/dicts/'
########### bin ###########
LINE_IMG_PAD = 30

########### fcr ###########
N_CHARS_FCR = 15
MIN_CHAR_SIZE_FCR = 8
MAX_CHAR_SIZE_FCR = 50
TARGET_CHAR_SIZE_FCR = 32

LEARNING_RATE_FCR = 0.001
BATCH_SIZE_FCR = 16
MAX_EPOCHS_FCR = 1000
VALIDATION_PER_FCR = 0.2
PATIENCE_FCR = 10
ACTIVATION_FCR = 'relu'
MAX_POOL_FCR = (2, 2)
N_FILTERS_FCR = 16
N_DENSE_FCR = 128
DROPOUT_FCR = 0.25

########### seg ###########
# as defined in https://arxiv.org/pdf/2103.08922.pdf
P1 = 100
P2 = 90
P3 = 25
P4 = 35
P5 = 330
P6 = 14
P7 = 0.3
P8 = 5

OVERLAP_THRESH_SEG = 0.5
OVERLAP2_THRESH_SEG = 0.75

TEST_THRESH_SEG = 14.3

########### epr ###########
SUPPORTED_LANGS = ['de', 'fr', 'lb', 'it', 'es', 'en', 'nl']
STOP_WORDS_THRESH = 0.1
STOP_WORDS = dict()
EPR_RULE1 = 21
EPR_RULE2 = 3
EPR_RULE3 = 4
EPR_RULE4 = 6
EPR_RULE5 = 8
EPR_RULE9 = 2
NGRAM_LENGTH = 3
AMOUNT_NGRAMS = 1000
MIN_YEAR = 1840
MAX_YEAR = 1960
DEFAULT_K = 27

########### alto ###########
BLOCK_TYPES_ALTO = [
	["PARAGRAPH", "TEXT"]
]
IMG_CROP_TOLERANCE = 2

########### ocr ###########
ART_LINE_WORDS_MIN = 6
ART_LINE_WORDS_MAX = 13
HYPHENS = {'-','⸗','='}
WHITE_LIST = set()
VOWELS = set()
REPLACEMENTS = {
	"⅓": "1/3",
	"↉": "0/5",
	"⅒": "1/10", 
	"⅑": "1/9", 
	"⅛": "1/8", 
	"⅐": "1/7", 
	"⅙": "1/6",
	"⅕": "1/5",
	"¼": "1/4",
	"⅓": "1/5",
	"⅖": "2/5",
	"⅔": "2/3",
	"⅜": "3/8",
	"⅗": "3/6",
	"¾": "3/4",
	"⅘": "4/5",
	"⅝": "5/8",
	"⅚": "5/6",
	"⅞": "7/8",
	'<': '‹',
	'>': '›',
	'Ç': 'C',
	'‛': '‘',
	'—': '-',
	'ᵃ': 'a',
	'ᵇ': 'b',
	'ᶜ': 'c',
	'ᵈ': 'd',
	'ᵉ': 'e',
	'ᶠ': 'f',
	'ᵍ': 'g',
	'ʰ': 'h',
	'ⁱ': 'i',
	'ʲ': 'j',
	'ᵏ': 'k',
	'ˡ': 'l',
	'ᵐ': 'm',
	'ⁿ': 'n',
	'ᵒ': 'o',
	'ᵖ': 'p',
	'ʳ': 'r',
	'ˢ': 's',
	'ᵗ': 't',
	'ᵘ': 'u',
	'ᵛ': 'v',
	'ʷ': 'w',
	'ˣ': 'x',
	'ʸ': 'y',
	'ᶻ': 'z',
	'ᴬ': 'A',
	'ᴮ': 'B',
	'ᴰ': 'D',
	'ᴱ': 'E',
	'ᴳ': 'G',
	'ᴴ': 'H',
	'ᴵ': 'I',
	'ᴶ': 'J',
	'ᴷ': 'K',
	'ᴸ': 'L',
	'ᴹ': 'M',
	'ᴺ': 'N',
	'ᴼ': 'O',
	'ᴾ': 'P',
	'ᴿ': 'R',
	'ᵀ': 'T',
	'ᵁ': 'U',
	'ⱽ': 'V',
	'ᵂ': 'W',
	'⁰': '0',
	'¹': '1',
	'²': '2',
	'³': '3',
	'⁴': '4',
	'⁵': '5',
	'⁶': '6',
	'⁷': '7',
	'⁸': '8',
	'⁹': '9',
}