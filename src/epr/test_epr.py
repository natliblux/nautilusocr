import json
from ocr.pipe.models import Models
from epr.apply_epr import predict
import constants.constants as ct
import os
from tqdm import tqdm

def test_epr_model(model_name):

	models = Models()
	model_path = models.load_epr_model(model_name)
	
	X = models.epr['x']
	Y = models.epr['y']
	chars = models.epr['chars']

	best_loss = None
	best_k = None

	n_test_ks = int(len(X)**(1/2))
	
	for k in tqdm([i for i in range(1, min(len(X), n_test_ks*2), 2)]):
		total_loss = 0
		total_chars = 0
		for i in range(0, len(X)):
			
			x_test = X[i]
			gt = Y[i]
			prediction = predict(models.epr, x_test, k, i)
			delta = prediction-gt
			diff = abs(delta)
			total_loss += diff*chars[i]
			total_chars += chars[i]

		loss = total_loss/total_chars

		if best_loss == None or loss < best_loss:
			best_loss = loss
			best_k = k

	# copy lines of model file
	with open(model_path, 'r') as model_file:
		lines = model_file.readlines()

	# remove last line if necessary
	if 'k' in json.loads(lines[-1]):
		with open(model_path, 'w') as model_file:
			model_file.writelines(lines[:-1])

	# add k and mae infos as last line
	with open(model_path, 'a') as model_file:
		info = {
			'k': best_k,
			'mae': best_loss
		}
		model_file.write(json.dumps(info))

	print("enhancement prediction test using " + model_name + " completed with results:")
	print("mean absolute error:\t" + str(best_loss))