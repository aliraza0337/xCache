import os 
import cPickle
from threading import Thread 
import socket as dummysocket
import time 
import random 
import string as stringRandom 
import diff_match_patch
import reportLogs 
import edgeCacheObject 
import constants 
import logging 

global ALL_OBJECTS , PUSH_TO_CACHE, PREVIOUS_OBJECTS 

logger_1 = logging.getLogger('simple_logger')
logger_1.setLevel(logging.INFO)
hdlr_1 = logging.FileHandler('network.log')
logger_1.addHandler(hdlr_1)


ALL_OBJECTS = [] 
PUSH_TO_CACHE = []
PREVIOUS_OBJECTS = {}


def startfunc():	
	thread1 = Thread(target = listenFromController, args = (1, ))
	thread1.start()
	thread2 = Thread(target = processObjects, args = (1, ))
	thread2.start()
	thread3 = Thread(target = reportLogs.startFunc, args = (1, ))
	thread3.start()


def listenFromController(num):

	EdgeCache_IP = constants.EDGECACHE_IP
	EdgeCache_Port = constants.EDGECACHE_PORT_OBJECTS
	while 1:

		while 1:
			try:
				logger_1.info('connecting to CC\n')
				s = dummysocket.socket(dummysocket.AF_INET, dummysocket.SOCK_STREAM)
				s.connect((EdgeCache_IP, EdgeCache_Port))
				logger_1.info('connected...\n')
			except:
				time.sleep(30)


		MESSAGE = ''
		while 1:
			data = s.recv(1024)
			MESSAGE += data
				if '**EDGE_OBJECT**' in MESSAGE: 
					try:
						edgeObject = cPickle.loads(MESSAGE.split('**EDGE_OBJECT**')[0])
						ALL_OBJECTS.append(edgeObject)
					except:
						pass
					MESSAGE = MESSAGE.split('**EDGE_OBJECT**')[1]







def push_in_cache(edgeObject, mode):
	res = '%s %s %s\r\n' % (edgeObject.request_ver, edgeObject.status, edgeObject.reason)
	N = 15 
	file_name = ''.join(random.choice(stringRandom.ascii_uppercase + stringRandom.digits) for _ in range(N))
	print 'ready to push    :'+ file_name

	for header in edgeObject.headers:
		res += header[0] + ": " + header[1] +"\n"

	res = res+"\r\n"+edgeObject.content
	with open('cache/'+file_name+'.txt','wb') as f:
		f.write(res);
	f.close()

	path = 'cache/'+file_name+'.txt'
	command = 'sudo ./tspush -f cache/'+file_name+'.txt -u http://'+constants.APS_IP_PORT+' -s '+edgeObject.url
	#print command
	os.system(command)
	time.sleep(0.08)
	os.system('rm '+path)


def applyDiff(obj):

	global PREVIOUS_OBJECTS
	
	if obj.url in PREVIOUS_OBJECTS:
		newObject = PREVIOUS_OBJECTS[obj.url]
	else: 
		print 'Object not found!'

	old_content = newObject.content.decode('utf-8')
	diff = obj.content 

	var = diff_match_patch.diff_match_patch()
	patches = var.patch_fromText(diff)
	results = var.patch_apply(patches, old_content)

	
	newObject.content = results[0].encode('utf-8')
	newObject.headers = obj.headers
	newObject.status = obj.status
	newObject.reason = obj.reason

	del obj
	push_in_cache(newObject, 'diff')



def processObjects(num):	
	global ALL_OBJECTS, PUSH_TO_CACHE, PREVIOUS_OBJECTS
	while 1:
		if len(ALL_OBJECTS) > 0:
			edgeObject = ALL_OBJECTS.pop(0)
			
			if not edgeObject.diff:			
				push_in_cache(edgeObject, 'normal')
				PREVIOUS_OBJECTS[edgeObject.url] = edgeObject
			else:
				applyDiff(edgeObject)
			time.sleep(0.001)
		time.sleep(0.001)

startfunc()
