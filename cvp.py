#!/usr/bin/python3.5

# https://github.com/phil294/FH-Rosenheim-Community-Downloader
#   .___.
#   {o,o}
#  /)___)
# ---"-"-
# Created 21.01.2017 by Phi

from pyquery import PyQuery
import requests
import tkinter.messagebox as msgbox

url_FHR = "https://www.fh-rosenheim.de"
url_FHR_idp = "https://idp.fh-rosenheim.de"



######### CONFIG ###########
USERNAME = 'sAAAzzzzzzz'
PASSWORD = '......'
COMMUNITY = 'inf-community'
############################



def eksit(s):
	msgbox.showwarning('FH Rosenheim Community Downloader', s+'. Exiting.')
	exit()

## returns session
def login(user, passw): 
	session = requests.Session()
	# Get action url incl. JSEISSIONID Cookie
	url_start = url_FHR + '/index.php?id=11378&deeplink=1'
	get = session.get(url_start)
	pq = PyQuery(get.text)
	form = pq.find("div.column.one form")
	# /idp/profile/SAML2/Redirect/SSO;jsessionid=....?execution=e1s1
	action = form.attr.action
	if 'jsessionid' not in action:
		eksit('Session error')

	# Login
	url_action = url_FHR_idp + action
	post_params = {
		'j_username': user,
		'j_password': passw,
		'_eventId_proceed': ''
	}
	post = session.post(url_action, post_params)
	
	# Forward ... (noscript)
	pq = PyQuery(post.text)
	div = pq.find("body>form>div")
	relayState = div.find('input[name="RelayState"]').attr.value
	samlResponse = div.find('input[name="SAMLResponse"]').attr.value
	url_shibbo = url_FHR + "/Shibboleth.sso/SAML2/POST"
	post_params = {
		"RelayState": relayState,
		"SAMLResponse": samlResponse
	}
	post = session.post(url_shibbo, post_params)
	if 'Abmelden' not in post.text: # todo internationlaliserien & exit in main
		exsit('Login error')
	return session

# returns int array
def getCourseIds(session):
	url_courses = url_FHR + "/community/" + COMMUNITY + "/lehrveranstaltungen/?m=1"
	get = session.get(url_courses)
	pq = PyQuery(get.text)
	ids = []
	# Extract LV IDs
	# <h3 class="lvTitle"><a name="lv-3027">
	pq.find("h3.lvTitle").each(lambda i,h3: ids.append( PyQuery(h3).find("a").attr.name[3:] ) )
	return ids

# returns array of file urls
def getNewFilesUrls(session, courseId):
	url_material = url_FHR + "/community/" + COMMUNITY + "/lehrveranstaltungen/details/?tx_fhalumni_pi1[uid]=" . courseId
	# todo
	return []

def downloadFile(session, url, dest):
	# todo
	return true



print(0)
session = login(USERNAME, PASSWORD)
print(1)
courseIds = getCourseIds(session)
print(2)
if(len(courseIds) < 1):
	eksit("Lehrveranstaltungen < 1")
for courseId in courseIds:
	# todo mkdir
	file_urls = getNewFilesUrls(session, courseId)
	for url in file_urls:
		# todo downloadFile(session, url, ?)
		pass
# todo update info
exit(0)