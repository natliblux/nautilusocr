import tensorflow as tf
import numpy as np

def predict(model, x_test, k, leave_out_index=None):

	X = model['x']
	Y = model['y']
	chars = model['chars']

	if leave_out_index != None:
		X = np.delete(X, (leave_out_index), axis=0)
		Y = np.delete(Y, (leave_out_index), axis=0)
		chars = np.delete(chars, (leave_out_index), axis=0)

	total = 0
	total_weight = 0

	distances = tf.negative(tf.sqrt(tf.reduce_sum(tf.square(tf.subtract(X, x_test)), 1)))
	_, indx = tf.nn.top_k(distances, k)
	for index in indx.numpy():
		flag = Y[index]
		weight = chars[index]
		total += flag*weight
		total_weight += weight
	
	return total/total_weight