from ocr.pipe.block import Block
from langid.langid import LanguageIdentifier, model
import hunspell
import constants.constants as ct
import os

class Features:

	def __init__(self):

		self.identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
		self.dicts = dict()
		for lang in ct.SUPPORTED_LANGS:
			aff_path = None
			dic_path = None
			txt_path = None
			for root, _, files in os.walk(ct.DICTS_PATH):
				for f in files:
					if f == lang + '.txt':
						txt_path = root + '/' + f 
					elif f == lang + '.aff':
						aff_path = root + '/' + f
					elif f == lang + '.dic':
						dic_path = root + '/' + f

			if not (txt_path != None or (dic_path != None and aff_path != None)):
				print("dictionnary files not found for language " + lang)				
				exit()

			if aff_path != None and dic_path != None:
				self.dicts[lang] = hunspell.HunSpell(dic_path, aff_path)
			else:
				words_list = set()
				with open(txt_path, 'r', encoding='utf-8') as lines:
					for line in lines:
						words_list.add(line.lower().strip())
				self.dicts[lang] = words_list

	def compute_features_ori(self, block: Block):
		
		block.tokens_ori = self.get_tokens(block.ocr_ori)
		block.dict_ori = self.get_dict_score(block.tokens_ori, block.lang_ori)
		block.garbage_ori = self.get_garbage_score(block.tokens_ori)
		return block

	def scale_year(self, year):
		scaled_year = (year-ct.MIN_YEAR)/(ct.MAX_YEAR-ct.MIN_YEAR)
		scaled_year = max(min(1.0, scaled_year), 0.0)
		return scaled_year

	def get_ngram_score(self, ngrams, lang_ngrams):
		
		if len(ngrams) == 0:
			return 0
		
		score = 0
		for ngram in ngrams:
			for i in range(0, len(lang_ngrams)):
				if ngram == lang_ngrams[i]:
					score += 1-(1/len(lang_ngrams)*i)
					break
				
		score = score/len(ngrams)
		return score
		

	def get_ngrams(self, tokens, text):

		lang_gt = self.get_lang(tokens, text)
		n_grams = list()
		for token in tokens:
			token_list = list(token)
			for i in range(0,len(token_list)):
				if not token[i].isalpha():
					token_list[i] = " "
			modified_token = "".join(token_list)
			splits = modified_token.split(" ")
			for split in splits:
				if split != "":
					for i in range(0, len(split)-ct.NGRAM_LENGTH+1):
						n_grams.append(split[i:i+ct.NGRAM_LENGTH].lower())
		return (lang_gt, n_grams)

	def get_tokens(self, text):

		tokens = list()

		new_token = ''
		for c in text:
			if c == ' ' and len(new_token) > 0:
				tokens.append(new_token)
				new_token = ''
			elif c == '\n' and len(new_token) > 0:
				if new_token[-1] in ct.HYPHENS:
					new_token = new_token[:-1]
				else:
					tokens.append(new_token)
					new_token = ''
			else:
				new_token += c
		if len(new_token) > 0:
			tokens.append(new_token)

		for i, token in enumerate(tokens):
			if not token[-1].isalpha():
				tokens[i] = token[:-1]
			if not token[0].isalpha():
				tokens[i] = token[1:]

		return tokens

	def get_lang(self, tokens, text):

		if len(tokens) == 0:
			return 'unknown'
		for lang in ct.SUPPORTED_LANGS:
			matched = 0
			for token in tokens:
				if token.lower() in [sw.lower() for sw in ct.STOP_WORDS[lang]]:
					matched += 1
			if matched/len(tokens) >= ct.STOP_WORDS_THRESH:
				return lang
		try:
			lang, _ = self.identifier.classify(text.strip())
			return lang
		except:
			return 'unknown'

	def get_dict_score(self, tokens, lang):

		if lang not in ct.SUPPORTED_LANGS or len(tokens) == 0:
			return 0

		matched_count = 0
		total_count = 0

		for token in tokens:
			total_count += len(token)
			if isinstance(self.dicts[lang], set):
				if token.lower() in self.dicts[lang]:
					matched_count += len(token)
			else:
				if self.dicts[lang].spell(token):
					matched_count += len(token)
		return matched_count/total_count


	def get_garbage_score(self, tokens):

		issues = 0

		if len(tokens) == 0:
			return 0
						
		for token in tokens:
		
			# rule1
			if len(token) >= ct.EPR_RULE1:
				issues += 1
				continue
				
			vowel_count = 0
			consonant_count = 0
			lower_case_count = 0
			upper_case_count = 0
			special_char_count = 0
			non_outer_special_chars = set()
			alpha = True
			last_char = None
			repitition_streak = 0
			vowel_streak = 0
			consonant_streak = 0
			go_to_next_token = False
			for i in range(0, len(token)):
				go_to_next_token = False
				char = token[i]
				
				# collect token info
				if char.isalpha():
					if char.lower() in ct.VOWELS:
						vowel_count += 1
						vowel_streak += 1
						consonant_streak = 0
					else:
						consonant_count += 1
						consonant_streak += 1
						vowel_streak = 0
					if char.isupper():
						upper_case_count += 1
					else:
						lower_case_count += 1
				elif char.isalnum():
					alpha = False
					vowel_streak = 0
					consonant_streak = 0
				else:
					special_char_count += 1
					alpha = False
					vowel_streak = 0
					consonant_streak = 0
					if i != 0 and i != len(token)-1:
						non_outer_special_chars.add(char)

				# rule 3
				if vowel_streak >= ct.EPR_RULE3:
					issues += 1
					go_to_next_token = True
					break

				# rule 4
				if consonant_streak >= ct.EPR_RULE4:
					issues += 1
					go_to_next_token = True
					break
				
				if last_char != None and char == last_char:
					repitition_streak += 1

					# rule 2
					if repitition_streak >= ct.EPR_RULE2:
						issues += 1
						go_to_next_token = True
						break
				else:
					repitition_streak = 0
				last_char = char
			
			if go_to_next_token:
				continue
			
			if alpha and vowel_count>0 and consonant_count>0:
				# rule 5		
				if vowel_count*ct.EPR_RULE5 < consonant_count:
					issues += 1
					continue
				# rule 5
				if consonant_count*ct.EPR_RULE5 < vowel_count:
					issues += 1
					continue
			
			# rule 6
			if lower_case_count > 0 and upper_case_count > lower_case_count:
				issues += 1
				continue

			# rule 7
			if upper_case_count > 0 and token[0].islower() and token[len(token)-1].islower():
				issues += 1
				continue

			# rule 8
			regular_chars = len(token)-special_char_count
			if special_char_count >= regular_chars and regular_chars > 0:
				issues += 1
				continue
			
			# rule 9
			if len(non_outer_special_chars) >= ct.EPR_RULE9:
				issues += 1
				continue

		return issues/len(tokens)