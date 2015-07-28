__author__ = 'hugh'
bl_info = {
	"name": "Creat Caffe solution",
	"category": "Object",
}

import bpy
import random
import time
import os

def getFillerString(node, ftype):
	if ftype == 'none':
		if node.type == 'constant':
			fillerString = 'value: %f\n' % (node.value)
		elif node.type == 'xavier' or node.type == 'msra':
			fillerString = 'variance_norm: %s\n' % (node.variance_norm)
		elif node.type == 'gaussian':
			fillerString = 'mean: %f\nstd: %f\n' % (node.mean, node.std)	
			if node.sparsity:
				fillerString = fillerString + 'sparse: %i\n' % (node.sparse)	
		elif node.type == 'uniform':
			fillerString = 'min: %f\nmax: %f\n' % (node.min, node.max)
	elif ftype == 'weight':
		if node.w_type == 'constant':
			fillerString = 'value: %f\n' % (node.w_value)
		elif node.w_type == 'xavier' or node.w_type == 'msra':
			fillerString = 'variance_norm: %s\n' % (node.w_variance_norm)
		elif node.w_type == 'gaussian':
			fillerString = 'mean: %f\nstd: %f\n' % (node.w_mean, node.w_std)	
			if node.w_sparsity:
				fillerString = fillerString + 'sparse: %i\n' % (node.w_sparse)	
		elif node.w_type == 'uniform':
			fillerString = 'min: %f\nmax: %f\n' % (node.w_min, node.w_max)
	elif ftype == 'bias':
		if node.b_type == 'constant':
			fillerString = 'value: %f\n' % (node.b_value)
		elif node.b_type == 'xavier' or node.b_type == 'msra':
			fillerString = 'variance_norm: %s\n' % (node.b_variance_norm)
		elif node.b_type == 'gaussian':
			fillerString = 'mean: %f\nstd: %f\n' % (node.b_mean, node.b_std)	
			if node.b_sparsity:
				fillerString = fillerString + 'sparse: %i\n' % (node.b_sparse)	
		elif node.b_type == 'uniform':
			fillerString = 'min: %f\nmax: %f\n' % (node.b_min, node.b_max)
	
	fillerString = 'type: "%s"\n%s' % (node.type, fillerString)
	return fillerString
	
def convtemplate(node,name, OutputLs, Padding, kernelsize, Stride, bottom, bfv, flr, blr, fdr, bdr, std, weight_filler,nonsquare=0,x=0,y=0):
	w_fillerString = getFillerString(node, 'weight')
	b_fillerString = getFillerString(node, 'bias')
	
	if not nonsquare:
		kernelstring = 'kernel_size: %i'%kernelsize
	else:
		kernelstring = 'kernel_h: %i\nkernel_w: %i' %(y,x)
	string = \
		'layer {\n\
		name: "%s"\n\
		type: "Convolution"\n\
		param {\n\
		lr_mult: %i\n\
		decay_mult: %i\n\
		}\n\
		param {\n\
		lr_mult: %i\n\
		decay_mult: %i\n\
		}\n\
		convolution_param {\n\
		num_output: %i\n\
		pad: %i\n\
		%s\n\
		stride: %i\n\
		weight_filler {\n\
		%s\
		}\n\
		bias_filler {\n\
		%s\
		}\n\
		}\n\
		bottom: "%s"\n\
		top: "%s"\n\
		}\n' \
		% (name, flr, fdr, blr, bdr, OutputLs, Padding, kernelstring, Stride, w_fillerString,b_fillerString, bottom, name)
	tb = [name, bottom]
	return string


def deconvtemplate(node,name, OutputLs, Padding, kernelsize, Stride, bottom, bfv, flr, blr, fdr, bdr, std, weight_filler,nonsquare=0,x=0,y=0):
	w_fillerString = getFillerString(node, 'weight')
	b_fillerString = getFillerString(node, 'bias')
	
	if not nonsquare:
		kernelstring = 'kernel_size: %i'%kernelsize
	else:
		kernelstring = 'kernel_h: %i\nkernel_w: %i' %(y,x)
	string = \
		'layer {\n\
		name: "%s"\n\
		type: "Deconvolution"\n\
		param {\n\
		lr_mult: %i\n\
		decay_mult: %i\n\
		}\n\
		param {\n\
		lr_mult: %i\n\
		decay_mult: %i\n\
		}\n\
		convolution_param {\n\
		num_output: %i\n\
		pad: %i\n\
		%s\n\
		stride: %i\n\
		weight_filler {\n\
		%s\
		}\n\
		bias_filler {\n\
		%s\
		}\n\
		}\n\
		bottom: "%s"\n\
		top: "%s"\n\
		}\n' \
		% (name, flr, fdr, blr, bdr, OutputLs, Padding, kernelstring, Stride, w_fillerString, b_fillerString, bottom, name)
	tb = [name, bottom]
	return string


def datatemplate(name, batchsize, trainpath, testpath, shuffle, supervised, dbtype, meanused, imsize, maxval=255, mirror=0,
				meanfile=0, silout=0, channels=3):
	sf = 1.0 / (maxval + 1)
	if channels == 1:
		iscolour = 'is_color: 1' ### When single channel
	else:
		iscolour = ''
	try:
		extralabel = str(int(name[-1])) ####In case of more than one data layer
	except ValueError:
		extralabel = ''
	if supervised == 0:
		lstring = ''
	else:
		lstring = 'top: "label%s"' % extralabel
	if silout and supervised:
		silencestring = \
			'layer {\n\
		bottom: "label%s"\n\
		name: "%s"\n\
		type: "Silence"\n\
		}\n' \
			% (extralabel, name + 'silence')
	else:
		silencestring = ''
	if meanused != 0:
		meanstring = 'mean_file: "%s"' % meanfile
	else:
		meanstring = ''
	if dbtype == 'LMDB':
		typestring = 'Data'
		paramstring = \
			'data_param {\n\
			source: "%s"\n\
			backend: LMDB\n\
			batch_size: %i\n\
			}\n\
			transform_param {\n\
			mirror: %i\n\
			scale: %f\n\
			%s\n\
			}\n' \
			% (trainpath, batchsize, mirror, sf, meanstring)
		testparamstring = \
			'data_param {\n\
			source: "%s"\n\
			backend: LMDB\n\
			batch_size: %i\n\
			}\n\
			transform_param {\n\
			mirror: %i\n\
			scale: %f\n\
			%s \n\
			}\n' \
			% (testpath, batchsize, mirror, sf, meanstring)
	elif dbtype == 'Image files':
		typestring = 'ImageData'
		paramstring = \
			'transform_param {\n\
			mirror: %i\n\
			scale: %f\n\
			%s\n\
			}\n\
			image_data_param {\n\
			%s\n\
			source: "%s"\n\
			batch_size: %i\n\
			new_height: %i\n\
			new_width: %i\n\
			shuffle: %i\n\
			}\n' \
			% (mirror, sf, meanstring, iscolour, trainpath, batchsize, imsize, imsize, shuffle)
		testparamstring = \
			'transform_param {\n\
			mirror: %i\n\
			scale: %f\n\
			%s\n\
			}\n\
			image_data_param {\n\
			%s\n\
			source: "%s"\n\
			batch_size: %i\n\
			new_height: %i\n\
			new_width: %i\n\
			shuffle: %i\n\
			}\n' \
			% (mirror, sf, meanstring, iscolour, testpath, batchsize, imsize, imsize, shuffle)
	elif dbtype == 'HDF5Data':
		typestring = 'HDF5Data'
		paramstring = \
			'hdf5_data_param {\n\
			source: "%s"\n\
			batch_size: %i\n\
			shuffle: %i\n\
			}\n\
			transform_param {\n\
			mirror: %i\n\
			scale: %f\n\
			%s\n\
			}\n' \
			% (trainpath, batchsize, shuffle, mirror, sf, meanstring)
		testparamstring = \
			'hdf5_data_param {\n\
			source: "%s"\n\
			batch_size: %i\n\
			shuffle: %i\n\
			}\n\
			transform_param {\n\
			mirror: %i\n\
			scale: %f\n\
			%s \n\
			}\n' \
			% (testpath, batchsize, shuffle, mirror, sf, meanstring)
	else:
		print (dbtype)
		raise EOFError
	string = \
		'layer {\n\
		name: "%s"\n\
		type: "%s"\n\
		top: "%s"\n\
		%s\n\
		%s \n\
		include { \n\
		phase: TRAIN \n\
		}\n\
		}\n\
		layer {\n\
		name: "%s"\n\
		type: "%s"\n\
		top: "%s"\n\
		%s\n\
		%s\n\
		include {\n\
		phase: TEST \n\
		}\n\
		}\n\
		%s\n' \
		% (
			name, typestring, name, lstring, paramstring, name, typestring, name, lstring, testparamstring,
			silencestring)
	return string


def pooltemplate(name, kernel, stride, mode, bottom):    
	string = \
		'layer {\n\
		name: "%s"\n\
		type: "Pooling"\n\
		bottom: "%s"\n\
		top: "%s"\n\
		pooling_param {\n\
		pool: %s\n\
		kernel_size: %i\n\
		stride: %i\n\
		}\n\
		}\n' \
		% (name, bottom, name, mode, kernel, stride)
	return string

def eltwisetemplate(name, bottomA, bottomB, operation, coeff, stable_prod_grad):    
	if operation == 'PROD':
		string = \
			'layer {\n\
			name: "%s"\n\
			type: "Eltwise"\n\
			bottom: "%s"\n\
			bottom: "%s"\n\
			top: "%s"\n\
			eltwise_param  {\n\
			operation: %s\n\
			stable_prod_grad: %s\n\
			}\n\
			}\n' \
			% (name, bottomA, bottomB, name, operation, stable_prod_grad)
	elif operation == 'SUM':
		string = \
			'layer {\n\
			name: "%s"\n\
			type: "Eltwise"\n\
			bottom: "%s"\n\
			bottom: "%s"\n\
			top: "%s"\n\
			eltwise_param  {\n\
			operation: %s\n\
			coeff: %f\n\
			}\n\
			}\n' \
			% (name, bottomA, bottomB, name, operation, coeff)
	elif operation == 'MAX':
		string = \
			'layer {\n\
			name: "%s"\n\
			type: "Eltwise"\n\
			bottom: "%s"\n\
			bottom: "%s"\n\
			top: "%s"\n\
			eltwise_param  {\n\
			operation: %s\n\
			}\n\
			}\n' \
			% (name, bottomA, bottomB, name, operation)
	return string

def exptemplate(name, bottom, base, scale, shift):
	string = \
		'layer {\n\
		name: "%s"\n\
		type: "Exp"\n\
		bottom: "%s"\n\
		top: "%s"\n\
		exp_param  {\n\
		base: %f\n\
		scale: %f\n\
		shift: %f\n\
		}\n\
		}\n' \
		% (name, bottom, name, base, scale, shift)
	return string

def mvntemplate(name, bottom, normalize_variance, across_channels, eps):
	string = \
		'layer {\n\
		name: "%s"\n\
		type: "MVN"\n\
		bottom: "%s"\n\
		top: "%s"\n\
		mvn_param  {\n\
		normalize_variance: %s\n\
		across_channels: %s\n\
		eps: %f\n\
		}\n\
		}\n' \
		% (name, bottom, name, normalize_variance, across_channels, eps)
	return string
	
def FCtemplate(node, name, outputs, bottom, sparse, weight_filler, bfv, flr, blr, fdr, bdr, std, sparsity):
	if sparsity == 1:
		sparsestring = 'sparse: %i' % sparse
	else:
		sparsestring = ''
	if weight_filler == 'gaussian':
		wfstring = 'weight_filler {\n\
		type: "gaussian"\n\
		std: %f\n\
		%s\n\
		}\n' % (std, sparsestring)
	else:
		wfstring = 'weight_filler {\n\
		type: "xavier"\n\
		std: %f\n\
		%s\n\
		}\n'%(std,sparsestring)
	string = \
		'layer {\n\
		name: "%s"\n\
		type: "InnerProduct"\n\
		param {\n\
		lr_mult: %i\n\
		decay_mult: %i\n\
		}\n\
		param {\n\
		lr_mult: %i\n\
		decay_mult: %i\n\
		}\n\
		inner_product_param {\n\
		num_output: %i\n\
		%s\n\
		bias_filler {\n\
		type: "constant"\n\
		value: %i\n\
		}\n\
		}\n\
		bottom: "%s"\n\
		top: "%s"\n\
		}\n' \
		% (name, flr, fdr, blr, bdr, outputs, wfstring, bfv, bottom, name)
	return string


def flattentemplate(name, bottom):
	string = \
		'layer {\n\
		bottom: "%s"\n\
		top: "%s"\n\
		name: "%s"\n\
		type: "Flatten"\n\
		}\n' \
		% (bottom, name, name)
	return string


def silencetemplate(name, bottom):
	string = \
		'layer {\n\
		bottom: "%s"\n\
		name: "%s"\n\
		type: "Silence"\n\
		}\n' \
		% (bottom, name)
	return string


def dropouttemplate(name, bottom, dropout):
	string = \
		'layer {\n\
	name: "%s"\n\
	type: "Dropout"\n\
	bottom: "%s"\n\
	top: "%s"\n\
	dropout_param {\n\
	dropout_ratio: %f\n\
	}\n\
	}\n' % (name, bottom, bottom, dropout)
	return string


def LRNtemplate(name, bottom, alpha, beta, size, mode):
	string = \
		'layer {\n\
		name: "%s"\n\
		type: "LRN"\n\
		bottom: "%s"\n\
		top: "%s"\n\
		lrn_param {\n\
		local_size: %i\n\
		alpha: %f\n\
		beta: %f\n\
		norm_region: %s\n\
		}\n\
		}\n' \
		% (name, bottom, name, size, alpha, beta, mode)
	return string


def NLtemplate(name, bottom, mode):
	string = \
		'layer {\n\
		name: "%s"\n\
		bottom: "%s"\n\
		top: "%s"\n\
		type: %s\n\
		}\n' \
		% (name, bottom, name, mode)
	return string


def Relutemplate(bottom, name, Negativeg):
	string = \
		'layer {\n\
		name: "%s"\n\
		type: "ReLU"\n\
		bottom: "%s"\n\
		top: "%s"\n\
		}\n' \
		% (name, bottom, bottom)
	return string
	
def PRelutemplate(node, bottom):	
	fillerString = getFillerString(node,'none')	
	string = \
		'layer {\n\
		name: "%s"\n\
		type: "PReLU"\n\
		bottom: "%s"\n\
		top: "%s"\n\
		filler {\n\
		%s\
		}\n\
		}\n' \
		% (node.name, bottom, node.name, fillerString)
	return string

def SMtemplate(name, bottom, w):
	string = \
		'layer {\n\
		name: "loss"\n\
		type: "SoftmaxWithLoss"\n\
		bottom: "%s"\n\
		bottom: "label"\n\
		top: "%s"\n\
		loss_weight: %f\n\
		}\n' \
		% (bottom, name, w)
	return string

def SCEtemplate(name, bottom1, bottom2, w):
	string = \
		'layer {\n\
		name: "loss"\n\
		type: "SigmoidCrossEntropyLoss"\n\
		bottom: "%s"\n\
		bottom: "%s"\n\
		top: "%s"\n\
		loss_weight: %f\n\
		}\n' \
		% (bottom1, bottom2, name, w)
	return string


def EUtemplate(name, bottom1, bottom2, w):
	string = \
		'layer {\n\
		name: "loss"\n\
		type: "EuclideanLoss"\n\
		bottom: "%s"\n\
		bottom: "%s"\n\
		top: "%s"\n\
		loss_weight: %f\n\
		}\n' \
		% (bottom1, bottom2, name, w)
	return string


def Concattemplate(name, bottom1, bottom2, dim):
	string = \
		'layer {\n\
		name: "%s"\n\
		bottom: "%s"\n\
		bottom: "%s"\n\
		top: "%s"\n\
		type: "Concat"\n\
		concat_param {\n\
		concat_dim: %i\n\
		}\n\
		}\n' \
		% (name, bottom1, bottom2, name, dim)
	return string


def accuracytemplate(name, bottom, Testonly):
	if Testonly == 1:
		Testonly = 'include { \n\
			phase: TEST \n\
			}'
	else:
		Testonly = ''
	string = \
		'layer {\n\
		name: "%s"\n\
		type: "Accuracy"\n\
		bottom: "%s"\n\
		bottom: "label"\n\
		top: "%s"\n\
		%s\n\
		}\n' \
		% (name, bottom, name, Testonly)
	return string

def argmaxtemplate(name, bottom, OutMaxVal, TopK):
	string = \
		'layer {\n\
		name: "%s"\n\
		type: "ARGMAX"\n\
		bottom: "%s"\n\
		top: "%s"\n\
		out_max_val: %i\n\
		top_k: %i\n\
		}\n' \
		% (name, bottom, name, OutMaxVal, TopK)
	return string


def solvertemplate(type, learningrate, testinterval, testruns, maxiter, displayiter, snapshotiter, snapshotname,
				snapshotpath, configpath, solvername, itersize, solver='GPU'):
	snapshotprefix = snapshotpath + snapshotname
	netpath = configpath + '%s_train_test.prototxt' % solvername
	if type == 'ADAGRAD':
		tsstring = \
			'lr_policy: "step"\n\
			gamma: 0.1\n\
			stepsize: 10000\n\
			weight_decay: 0.0005\n\
			solver_type: ADAGRAD\n'
	elif type == 'NAG':
		tsstring = \
			'lr_policy: "step"\n\
			gamma: 0.1\n\
			stepsize: 10000\n\
			weight_decay: 0.0005\n\
			momentum: 0.95\n\
			solver_type: NESTEROV\n'
	elif type == 'SGD':
		tsstring = \
			'lr_policy: "step"\n\
			gamma: 0.1\n\
			stepsize: 10000\n\
			weight_decay: 0.0005\n\
			momentum: 0.95\n'
	else:
		print ('ERROR')
		time.sleep(1000000)
	genericstring = \
		'net: "%s"\n\
		test_iter: %i\n\
		test_interval: %i\n\
		base_lr: %f\n\
		display: %i\n\
		max_iter: %i\n\
		iter_size: %i\n\
		snapshot: %i\n\
		snapshot_prefix: "%s"\n\
		solver_mode: %s\n' \
		% (netpath, testruns, testinterval, learningrate, displayiter, maxiter, itersize, snapshotiter, snapshotprefix,
		solver)
	solverstring = genericstring + tsstring
	return solverstring


def deploytemplate(batch, channels, size, datain):
	deploystring = \
		'name: "Autogen"\n\
	input: "%s"\n\
	input_dim: %i\n\
	input_dim: %i\n\
	input_dim: %i\n\
	input_dim: %i\n' % (datain, batch, channels, size, size)
	return deploystring


def scripttemplate(caffepath, configpath, solvername, gpus, solver):
	gpustring = ''
	usedcount = 0
	for gpu, used in enumerate(gpus):
		if used:
			if usedcount != 0:
				gpustring += ',' + str(gpu)
			else:
				gpustring += str(gpu)
			usedcount += 1
	if solver == 'GPU':
		extrastring = '--gpu=%s' % gpustring
	else:
		extrastring = ''
	solverstring = configpath + '%s_solver.prototxt' % solvername
	caffestring = caffepath + 'caffe'
	string = '#!/usr/bin/env sh \n %s train --solver=%s %s' % (caffestring, solverstring, extrastring)
	return string


class Solve(bpy.types.Operator):
	"""Generate Caffe solver"""  # blender will use this as a tooltip for menu items and buttons.
	bl_idname = "nodes.make_solver"  # unique identifier for buttons and menu items to reference.
	bl_label = "Create Solution"  # display name in the interface.
	bl_options = {'REGISTER'}  # enable undo for the operator.

	def execute(self, context):  # execute() is called by blender when running the operator.
		gtops = []  # the top (I.E. name of) each layer
		gbottoms = []  # the first input of all nodes
		g2bottoms = []  # the second input of all nodes
		gcode = []  # the code slice of each layer
		dcode = []  # the 'deploy' code slice of each layer
		# Go through all nodes, and find nodes that need to 'skip' a node computed in place
		nodesafterinplacenode = []  # Holds the name of the node after an in place (which needs a fiddled bottom)
		# and the name of the bottom it needs to be fiddled to
		for node in context.selected_nodes:
			for number,input in enumerate(node.inputs):
				if input.is_linked == True:
					bottomnode = input.links[0].from_node
					# Nodes computed in place
					if bottomnode.bl_idname == 'DropoutNodeType' or bottomnode.bl_idname == 'ReluNodeType':  #Function just to skip placeholder nodes
						bottomnodein = bottomnode.inputs  #the inputs of the node before
						bottomnodein = bottomnodein[0]  #the first input of the node before
						bottombottomnode = bottomnodein.links[0].from_node  # the the node before the node before
						print('*#*')
						nodesafterinplacenode.extend([[node.name,bottombottomnode.name,number]])
						print(nodesafterinplacenode)
		# The original script
		########################################### Main loop
		for node in context.selected_nodes:
			#################### Which of the nodes inputs are after an in place node?
			afterinplace = [0,0]
			newbottoms = [0,0] # assumes node can have max two inputs
			if len(nodesafterinplacenode) != 0: #Check if inplace swap needed
				print(nodesafterinplacenode)
				for nodename,nbottom,number in nodesafterinplacenode:
					if node.name == nodename:
						afterinplace[number] = 1
						newbottoms[number] = nbottom

			###################### What are all the nodes inputs?
			bottoms = []
			nname = node.name
			string = 0
			for input in node.inputs:
				if input.is_linked == True:
					bottomnode = input.links[0].from_node
					while bottomnode.bl_idname == 'NodeReroute':  # Function just to skip placeholder nodes
						bottomnodein = bottomnode.inputs  #the inputs of the node before
						bottomnodein = bottomnodein[0]  #the first input of the node before
						bottomnode = bottomnodein.links[0].from_node  # the name of the node before the node before
					bottom = bottomnode.name
					print ('node %s has input %s' % (nname, bottomnode.name))
					bottoms.extend([bottom])  # Bottoms is the list of all the nodes attached behind the current node
			######################## Swap the nodes inputs that are in place
			print('afterinplace:')
			print(afterinplace)
			if len(bottoms) > 0:
				in1 = bottoms[0]
			if len(bottoms) > 1:
				in2 = bottoms[1]
			if afterinplace[0] == 1:
				in1 = newbottoms[0]
			if afterinplace[1] == 1:
				in2 = newbottoms[1]
			# We keep the list of bottoms, irrelevant of in-place-ness as it is needed for sorting the layers
			###########################
			if node.bl_idname == 'DataNodeType':
				if node.dbtype == 'LMDB':
					string = datatemplate(node.name, node.batchsize, node.trainpath, node.testpath, node.shuffle, node.supervised,
										node.dbtype, node.usemeanfile, node.imsize, node.maxval, node.mirror,
										node.meanfile, node.silout)
					dstring = deploytemplate(node.batchsize, node.channels, node.imsize, node.name)
				elif node.dbtype == 'Image files':
					string = datatemplate(node.name, node.batchsize, node.trainfile, node.testfile, node.shuffle, node.supervised,
										node.dbtype, node.usemeanfile, node.imsize, node.maxval, node.mirror,
										node.meanfile, node.silout, channels=node.channels)
					dstring = deploytemplate(node.batchsize, node.channels, node.imsize, node.name)
				elif node.dbtype == 'HDF5Data':
					string = datatemplate(node.name, node.batchsize, node.trainHDF5, node.trainHDF5, node.shuffle, node.supervised,
										node.dbtype, node.usemeanfile, node.imsize, node.maxval, node.mirror,
										node.meanfile, node.silout, channels=node.channels)
					dstring = deploytemplate(node.batchsize, node.channels, node.imsize, node.name)
			elif node.bl_idname == 'PoolNodeType':
				string = pooltemplate(node.name, node.kernel, node.stride, node.mode, in1)
				dstring = string
			elif node.bl_idname == 'EltwiseNodeType':
				string = eltwisetemplate(node.name, in1, in2, node.operation, node.coeff, node.stable_prod_grad)
				dstring = string
			elif node.bl_idname == 'ExpNodeType':
				string = exptemplate(node.name, in1, node.base, node.scale, node.shift)
				dstring = string
			elif node.bl_idname == 'MVNNodeType':
				string = mvntemplate(node.name, in1, node.normalize_variance, node.across_channels, node.eps)
				dstring = string				
			elif node.bl_idname == 'ConvNodeType':
				string = convtemplate(node,node.name, node.OutputLs, node.Padding, node.kernelsize, node.Stride, in1,
									node.biasfill, node.filterlr, node.biaslr, node.filterdecay, node.biasdecay,
									node.std, node.weights,nonsquare=node.nonsquare,x=node.kernelsizex,y=node.kernelsizey)
				dstring = string
			elif node.bl_idname == 'DeConvNodeType':
				string = deconvtemplate(node, node.name, node.OutputLs, node.Padding, node.kernelsize, node.Stride,
										in1,
										node.biasfill, node.filterlr, node.biaslr, node.filterdecay, node.biasdecay,
										node.std, node.weights,nonsquare=node.nonsquare,x=node.kernelsizex,y=node.kernelsizey)
				dstring = string
			elif node.bl_idname == 'FCNodeType':
				string = FCtemplate(node.name, node.outputnum, in1, node.sparse, node.weights, node.biasfill,
									node.filterlr, node.biaslr, node.filterdecay, node.biasdecay, node.std,
									node.sparsity)
				dstring = string
			elif node.bl_idname == 'FlattenNodeType':
				string = flattentemplate(node.name, in1)
				dstring = string
			elif node.bl_idname == 'SilenceNodeType':
				string = silencetemplate(node.name, in1)
				dstring = string
			elif node.bl_idname == 'LRNNodeType':
				string = LRNtemplate(node.name, in1, node.alpha, node.beta, node.size, node.mode)
				dstring = string
			elif node.bl_idname == 'AcNodeType':
				string = NLtemplate(node.name, in1, node.mode)
				dstring = string
			elif node.bl_idname == 'ReluNodeType':
				string = Relutemplate(in1, node.name, node.Negativeg)
				dstring = string
			elif node.bl_idname == 'PReluNodeType':
				string = PRelutemplate(node, in1)
				dstring = string	
			elif node.bl_idname == 'DropoutNodeType':
				string = dropouttemplate(node.name, in1, node.fac)
				dstring = string
			elif node.bl_idname == 'SMLossNodeType':
				string = SMtemplate(node.name, in1, node.w)
				dstring = ''
			elif node.bl_idname == 'SCELossNodeType':
				string = SCEtemplate(node.name, in1,in2, node.w)
				dstring = ''
			elif node.bl_idname == 'EULossNodeType':
				string = EUtemplate(node.name, in1, in2, node.w)
				dstring = ''
			elif node.bl_idname == 'ConcatNodeType':
				string = Concattemplate(node.name, in1, in2, node.dim)
				dstring = string
			elif node.bl_idname == 'AccuracyNodeType':
				string = accuracytemplate(node.name, in1, node.Testonly)
				dstring = ''
			elif node.bl_idname == 'ArgMaxNodeType':
				string = argmaxtemplate(node.name, in1, node.OutMaxVal, node.TopK)
				dstring = ''
			elif node.bl_idname == 'NodeReroute':
				string = ''
				dstring = ''
			elif node.bl_idname == 'SolverNodeType':
				solverstring = solvertemplate(node.solver, node.learningrate, node.testinterval, node.testruns,
											node.maxiter,
											node.displayiter, node.snapshotiter, node.solvername, node.snapshotpath,
											node.configpath, node.solvername, node.accumiters, solver=node.compmode)
				scriptstring = scripttemplate(node.caffexec, node.configpath, node.solvername, node.gpus,
											solver=node.compmode)
				configpath = node.configpath
				solvername = node.solvername
			elif string == 0:
				print (node.bl_idname)
			if node.bl_idname != 'SolverNodeType':
				gcode.extend([string])
				dcode.extend([dstring])
				gtops.extend([node.name])
				try:
					gbottoms.extend([bottoms[0]])  # first node attached to current
				except IndexError:
					gbottoms.extend([str(random.random())])
				try:
					g2bottoms.extend([bottoms[1]])  # Second node attached to current
				except IndexError:
					g2bottoms.extend([str(random.random())])
		for juggle in range(30):
			gtops, gbottoms, g2bottoms, gcode, dcode = self.juggleorder(gtops, gbottoms, g2bottoms, gcode, 0, dcode)
			# for chunk in gcode:
			# print (chunk)
			gtops, gbottoms, g2bottoms, gcode, dcode = self.juggleorder(gtops, gbottoms, g2bottoms, gcode, 1, dcode)
		solution = ''
		for chunk in gcode:
			solution = solution + chunk
		dsolution = ''
		for chunk in dcode:
			dsolution = dsolution + chunk
		# print (solution)
		os.chdir(configpath)
		ttfile = open('%s_train_test.prototxt' % solvername, mode='w')
		ttfile.write(solution)
		ttfile.close()
		depfile = open('%s_deploy.prototxt' % solvername, mode='w')
		depfile.write(dsolution)
		depfile.close()
		solvefile = open('%s_solver.prototxt' % solvername, mode='w')
		solvefile.write(solverstring)
		solvefile.close()
		scriptfile = open('train_%s.sh' % solvername, mode='w')
		scriptfile.write(scriptstring)
		scriptfile.close()
		print ('Finished solving tree')
		return {'FINISHED'}  # this lets blender know the operator finished successfully.

	def juggleorder(self, names, refs, refs2, code, prefsocket, dcode):

		'''Ever heard of a bubble sort? Meet the worlds most complicated function designed to do just that.
		It checks whether a node is dependent on the node below it, and orders all the laters in the prototxt
		by a reference number. For some reason it sort of does it twice. Best just not to touch this and hope it never
		breaks as no-one will ever EVER work out how fix it.'''
		# Names, in 1, in2, code chunk, ??, deploy code chunk
		goodorder = 0
		checks = [1] * len(names)  #make list of zeros, length names
		while sum(checks) > 0:
			for name in names:
				Referred1Socket = 0
				Bottomless = 0
				Referred2Socket = 0
				# Start of list is data layer
				# get location of bottom in top
				# print (name)
				#print (names)
				loc = names.index(name)
				try:
					ref = refs.index(name)  # find where the current node is referred to
					Referred1Socket = 1
				except ValueError:
					pass
				try:
					float(name)  #we used a float name for nodes that are bottomless
					print ('passing float')
					print (name)
					Bottomless = 1
				except ValueError:
					pass
				try:
					tmpref = refs2.index(name)  #check a node isnt reffered to as the second socket
					if Referred1Socket == 1 and prefsocket == 1:
						ref = tmpref  #only put before if on second socket pass, or does not connect to a first socket
					elif Referred1Socket == 0:  #(Will not be a bottomless node as connects to at least one socket)
						ref = tmpref
					Referred2Socket = 1
				except ValueError:
					pass
				if Referred1Socket + Bottomless + Referred2Socket == 0:
					# not referred to by anything, so can be as late as possible
					ref = 10000000000000000
					#time.sleep(10)
				#ref = 10000000
				if ref < loc:
					names, refs, refs2, code, dcode = self.swap(loc, ref, (names, refs, refs2, code, dcode))
					checks[loc] = 0
				else:
					checks[loc] = 0
		return names, refs, refs2, code, dcode

	def swap(self, orig, dest, lists):
		for list in lists:
			tmp = list[dest]
			list[dest] = list[orig]
			list[orig] = tmp
		return lists


def register():
	bpy.utils.register_class(Solve)


def unregister():
	bpy.utils.unregister_class(Solve)


# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
	register()
