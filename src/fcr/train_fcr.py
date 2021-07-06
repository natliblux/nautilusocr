import os
import numpy as np
import cv2
import constants.constants as ct
from numpy.core.numeric import full
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Conv2D, MaxPool2D, Flatten
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping


# loads train dataset
def get_data(set_name):

	full_path = ct.TRAIN_SETS_PATH + set_name

	if not os.path.isdir(full_path):
		print("train set with name " + set_name + " does not exist in directory " + ct.TRAIN_SETS_PATH)
		exit()

	paths = []
	labels = []
	images = []

	for i, font in enumerate(ct.FONTS):
		if os.path.isdir (full_path + '/' + font):
			for root, _, files in os.walk(full_path + '/' + font):
				for f in files:
					if f.endswith('.png'):
						paths.append(root + '/' + f)
						labels.append(i)

	for image in paths:
		pix = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
		pix = pix.reshape(ct.TARGET_CHAR_SIZE_FCR, ct.TARGET_CHAR_SIZE_FCR, 1)
		pix = pix / 255.0
		images.append(pix)
			
	return (np.array(images), np.array(labels))

# trains font recognition model and stores it at model_path
def train_model_fcr(set_name, model_name):

	N_CLASSES = len(ct.FONTS)

	model = Sequential()
	model.add(Conv2D(ct.N_FILTERS_FCR, (5, 5), activation=ct.ACTIVATION_FCR, input_shape=(ct.TARGET_CHAR_SIZE_FCR, ct.TARGET_CHAR_SIZE_FCR, 1)))
	model.add(MaxPool2D(ct.MAX_POOL_FCR))
	model.add(Conv2D(ct.N_FILTERS_FCR, (3, 3), activation=ct.ACTIVATION_FCR))
	model.add(MaxPool2D(ct.MAX_POOL_FCR))
	model.add(Flatten())
	model.add(Dense(ct.N_DENSE_FCR, activation=ct.ACTIVATION_FCR))
	model.add(Dropout(ct.DROPOUT_FCR))
	model.add(Dense(N_CLASSES, activation='softmax'))
	model.summary()

	X, Y = get_data(set_name)
	callback = EarlyStopping(monitor="val_loss", patience=ct.PATIENCE_FCR, restore_best_weights=True)
	model.compile(optimizer=Adam(ct.LEARNING_RATE_FCR), loss='sparse_categorical_crossentropy')
	model.fit(X, Y, batch_size=ct.BATCH_SIZE_FCR, epochs=ct.MAX_EPOCHS_FCR, validation_split=ct.VALIDATION_PER_FCR, shuffle=True, callbacks=[callback])
	if not os.path.isdir(ct.MODELS_PATH):
		os.makedirs(ct.MODELS_PATH)
	model.save(ct.MODELS_PATH + model_name)
	print(ct.MODELS_PATH.split('/')[-2] + '/' +  model_name + ' has been created')