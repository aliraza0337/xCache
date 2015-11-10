import time
import thread
import copy
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.proxy import *
import selenium.webdriver.firefox.webdriver as fwb
import socket as dummysocket
import cPickle
import Queue as Q
import logging
import controller
import constants 
global ALL_WEBSITES, PREFETCHING_QUEUE, PREFETCHING_LIST 
logging.basicConfig(filename='prefetching.log',level=logging.INFO)
PREFETCHING_LIST = []
PREFETCHING_QUEUE = Q.PriorityQueue()

MAX_BOOTSTRAP  = constants.MAX_BOOTSTRAP
BOOTSTRAPSITES  = {}
ALL_WEBSITES = {}
TIME =  constants.INTERVAL_PREFETCHING


def startPrefetching(num):
	thread.start_new_thread(receiveLogs, (1,))
	thread.start_new_thread(bootstrap, (1,))
	thread.start_new_thread(sitesPrefetching, (1,))



def openPage (webpage):

	myProxy = "127.0.0.1:9999"
	proxy = Proxy ({
		'proxyType':ProxyType.MANUAL,
		'httpProxy': myProxy,
		'ftpProxy': myProxy,
		'sslProxy': myProxy,
		'noProxy': ''
		})

	binary = fwb.FirefoxBinary(firefox_path='/usr/bin/firefox')
	profile = webdriver.FirefoxProfile()
	profile.set_preference('datareporting.healthreport.uploadEnabled', False)
	profile.set_preference('datareporting.healthreport.service.enabled', False)
	profile.set_preference('datareporting.healthreport.service.firstRun', False)
	profile.set_preference('app.update.auto', False)
	profile.set_preference('app.update.enabled', False)
	profile.set_preference('browser.cache.disk.enable', False)
	profile.set_preference('browser.cache.memory.enable', False)
	profile.set_preference('browser.cache.offline.enable', False)
	profile.set_preference('network.http.use-cache', False)
	profile.set_preference('network.dns.disablePrefetch', True)
	profile.set_preference('network.http.accept-encoding', '')

	#for modifying header
	profile.add_extension( 'modify_headers-0.7.1.1-fx.xpi')
	profile.set_preference('modifyheaders.headers.count', 1)
	profile.set_preference('modifyheaders.headers.action0', "Add")
	profile.set_preference('modifyheaders.headers.name0', 'webpage')
	profile.set_preference('modifyheaders.headers.value0', webpage)
	profile.set_preference('modifyheaders.headers.enabled0', True)
	profile.set_preference('modifyheaders.config.active', True)
	profile.set_preference('modifyheaders.config.alwaysOn', True)
	#

	profile.update_preferences()

	browser = webdriver.Firefox(firefox_profile=profile, firefox_binary=binary, proxy=proxy)
	browser.implicitly_wait(50)
	browser.set_page_load_timeout(100)
	browser.set_window_size(1920, 1080)
	
	browser.get (webpage)

	while browser.title == "Problem loading page":
		browser.get (webpage)
		time.sleep(0.001)

	del profile
	print "-- Finished loading ", browser.title
	browser.quit()
	del browser



def bootstrap(a):
	global BOOTSTRAPSITES 
	print "Bootstraping thread started\n"

	while True:
		if len (BOOTSTRAPSITES ) > 0:

			for item in BOOTSTRAPSITES :
				
				if BOOTSTRAPSITES[item][0] <= 0:
					continue

				if BOOTSTRAPSITES [item][1] <= time.time():
					display = Display(visible=0, size=(1920,1080))
					display.start()

					print ('Requesting: ', item, 'for: ',BOOTSTRAPSITES[item][0] )
					
					log_string = 'BOOTSTRAP: '+str(time.time()) +' :'+item 
					logging.info(log_string)
					
					openPage(item)
					
					BOOTSTRAPSITES [item][0]-=1
					BOOTSTRAPSITES [item][1]=time.time()+constants.INTERVAL_BOOTSTRAP
					print BOOTSTRAPSITES [item][1]
					if BOOTSTRAPSITES [item][0] <=0 :

						print 'Added to PREFETCHING_LIST'
						log_string = 'BOOTSTRAP: ADDED_TO_PREFETCHING_LIST: '+item 
						logging.info(log_string)
						
						PREFETCHING_LIST.append(item)
					display.stop()
		time.sleep(1)










def sitesPrefetching (number):
	PREFETCHING_BOOL = False
	while True:

		global PREFETCHING_QUEUE , TIME, PREFETCHING_LIST
		currentTime = time.time()
		if len(PREFETCHING_LIST) > 0:
			calculateUtilities()
		
		while not PREFETCHING_QUEUE.empty():
			PREFETCHING_BOOL = True 

			w = PREFETCHING_QUEUE.get()
			display = Display(visible=0, size=(1920,1080))
			display.start()
			
			log_string = 'PREFETCHING: '+str(time.time()) +' :'+w[1] 
			logging.info(log_string)

			openPage(w[1])
			currentTime = time.time()
			display.stop()

		if PREFETCHING_BOOL:
			time_elapsed =  time.time() - currentTime
			if time_elapsed < TIME:
				time.sleep(TIME - time_elapsed)






def receiveLogs(num):
	global ALL_WEBSITES

	tmp = [('http://www.cnn.com/', 10),('http://www.bbc.com/', 10), ('http://www.apple.com/', 10)]

	for siteInfo in tmp:
		if siteInfo[0] in ALL_WEBSITES:
			ALL_WEBSITES[siteInfo[0]].N = 0.7*ALL_WEBSITES[siteInfo[0]].N + 0.3*siteInfo[1] # TODO: fix the ewma alpha parameter (at the moment random number is given)
		else:
			BOOTSTRAPSITES [siteInfo[0]]=[MAX_BOOTSTRAP , 0]
			ALL_WEBSITES[siteInfo[0]]=controller.WebPage(siteInfo[1])

	return




def calculateUtilities():
	global ALL_WEBSITES, PREFETCHING_QUEUE, PREFETCHING_LIST
	PREFETCHING_QUEUE =  Q.PriorityQueue()
	for webpage in PREFETCHING_LIST:
		print 'calculateUtilities'
		n_t = float(0.000)
		d_t = float(0.000)
		n_b = float(0.000)
		d_b = float(0.000)
		webPageObjects = ALL_WEBSITES[webpage].objects
		for o in webPageObjects.keys():
			x1, x2, x3, x4 = webPageObjects[o].calculateUtilities()
			n_t = n_t + x1 
			d_t = d_t + x2 
			n_b = n_b + x3  
			d_b = d_b + x4
		t = float(float(n_t/d_t) + float(n_b/d_b))
		PREFETCHING_QUEUE.put((t, webpage))



	# CONTROLLER_IP = '10.225.3.124'
	# CONTROLLER_PORT = 7007

	# s = dummysocket.socket(dummysocket.AF_INET, dummysocket.SOCK_STREAM)
	# s.setsockopt(dummysocket.SOL_SOCKET, dummysocket.SO_REUSEADDR, 1)

	# s.bind((CONTROLLER_IP, CONTROLLER_PORT))

	# while 1:

	# 	s.listen(1)
	# 	conn, addr = s.accept()
	# 	MESSAGE= ""
	# 	data = conn.recv(1024)

	# 	while data:
	# 		MESSAGE += data
	# 		data = conn.recv(1024)

	# 	websites = cPickle.loads(MESSAGE)

	# 	for web in websites:
	# 		if not (web in ALL_WEBSITES):
	# 			ALL_WEBSITES[web] = ''
	# 			PREFETCHING_QUEUE.put(( time.time() + 1800 ,web))
