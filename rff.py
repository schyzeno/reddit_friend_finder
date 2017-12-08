import requests
import requests.auth
from bs4 import BeautifulSoup
import ConfigParser
import time
import timeit
import pandas
import numpy as np

credentials = {'username':'df','password':'df','clientid':'df','clientsecret':'df','useragent':'df'}
headers = ''
authHeaders = ''
bearHeaders = ''
#Load user credentials
def loadConfig():	
	config = ConfigParser.ConfigParser()
	config.read('r.ini')
	global credentials
	credentials['username'] = config.get('OAUTH','username')
	credentials['password'] = config.get('OAUTH','password')
	credentials['clientid'] = config.get('OAUTH','clientid')
	credentials['clientsecret'] = config.get('OAUTH','clientsecret')
	credentials['useragent'] = config.get('OAUTH','useragent')+'/'+config.get('OAUTH','useragentversion')+' by '+credentials['username']

#Perform OAUTH fetch token
def genHeaders():
	global headers,authHeaders,bearHeaders
	client_auth = requests.auth.HTTPBasicAuth(credentials['clientid'], credentials['clientsecret'])
	post_data = {"grant_type": "password", "username": credentials['username'], "password": credentials['password']}
	headers = {"User-Agent": credentials['useragent']}
	response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
	token = response.json()['access_token'].encode("UTF-8")
	authHeaders = {"Authorization": token, "User-Agent": credentials['useragent']}
	bearHeaders = {"Authorization": ("bearer "+token), "User-Agent": credentials['useragent']}

#Get all subs
#TODO handle users with listings on more than one page
def getSubscriptions():		
	response = requests.get("https://oauth.reddit.com/subreddits/mine/subscriber",headers=bearHeaders)
	subs = []
	for listing in response.json()['data']['children']:		
		print listing['data']['url']
		subs.append("https://www.reddit.com"+listing['data']['url'])
	print 'Found ' + str(len(subs)) + ' subreddits'
	return subs
		
def getTrendingThreads(subreddit):
	response = requests.get(subreddit, headers=authHeaders)
	soup = BeautifulSoup(response.content,'html.parser')
	threads = []
	for link in soup.findAll('a'):
		if u'comment' in link.text:
			threads.append(link.get('href'))
	return threads

def getComments(thread):
	comments = []
	try:
		response = requests.get(thread, headers=headers)
		soup = BeautifulSoup(response.content, 'html.parser')
		sub = thread[thread.index('/r/'):]
		sub = sub[3:]
		sub = sub[:sub.index('/')]	
		title = thread[thread[0:len(thread)-2].rfind('/')+1:-1]
		print 'Processing Subreddit: '+ sub + ' Thread: ' + title
	except:
		print 'Error Unable to process thread'
		return []
	for comment in soup.findAll("a", class_='author'):
		author = comment.text
		comments.append((author,sub,title))	
	return comments

def findFriends():	
	startTime = time.time()	
	loadConfig()
	genHeaders()
	threads = []
	comments = []
	subs = getSubscriptions()
	print 'Retrieving comment threads...'
	for sub in subs:
		threads = threads + getTrendingThreads(sub)
	print 'All threads retrieved in ' + str(time.time() - startTime) + 's'
	for idx,thread in enumerate(threads):
		print ('('+str(idx)+'/'+str(len(threads))+')')
		comments = comments + getComments(thread)	
	print 'Found ' + str(len(comments)) + ' in ' + str(len(threads)) + ' threads across ' + str(len(subs)) + ' subreddits'
	analyzeComments(comments)

def analyzeComments(comments):	
	df = pandas.DataFrame(comments,columns=['user','subreddit','title'])
	top10Matches = df.groupby(['user']).subreddit.nunique().head(10)
	print top10Matches
	
def runTimedNoArg(methodName, method):
	print methodName + '()'
	startTime = time.time()
	method()
	print '-'+methodName + '() finished in ' + str(time.time() - startTime) + 's'	

runTimedNoArg('findFriends',findFriends)

