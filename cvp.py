#!/usr/bin/python3.5

# https://github.com/phil294/FH-Rosenheim-Community-Downloader
#   .___.
#   {o,o}
#  /)___)
# ---"-"-
# Created 21.01.2017 by Phi

from pyquery import PyQuery
import requests
#import tkinter.messagebox as msgbox
import os
import datetime

url_FHR = "https://www.fh-rosenheim.de"
url_FHR_idp = "https://idp.fh-rosenheim.de"



######### CONFIG ###########
USERNAME = ''
PASSWORD = ''
COMMUNITY = 'inf-community'
OUTPUT_FOLDER = 'community'
############################



def info(s):
	#msgbox.showwarning('FH Rosenheim Community Downloader', s)
	print(s)
def error(s):
	info(s)
	exit(1)

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
		info('Session error')

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
	if 'name="logintype" value="logout"' not in post.text:
		error('Login error')
	return session

## returns array of obj{id, name}
def getCourses(session):
	url_courses = url_FHR + "/community/" + COMMUNITY + "/lehrveranstaltungen/?m=1"
	get = session.get(url_courses)
	pq = PyQuery(get.text)
	courses = []
	def addToCourses(a):
		id = a.attr.name[3:]
		name = a.text()
		courses.append({
			'id': id,
			'name': name
		})
	# Extract LV IDs
	# <h3 class="lvTitle"><a name="lv-3027">course title</a>
	pq.find("h3.lvTitle").each(lambda i,h3: addToCourses(PyQuery(h3).find('a')) )
	return courses

## returns array of obj(categoryName, urls: array of obj(fileName,fileTitle,fileUrl,fileDate))
def getFilesUrlsByCourse(session, courseId, onlyNew=False):
	url_material = url_FHR + "/community/" + COMMUNITY + "/lehrveranstaltungen/details/?tx_fhalumni_pi1[uid]=" + courseId
	get = session.get(url_material)
	pq = PyQuery(get.text)
	files = [];
	# foreach category
	def addToFiles(h3):
		categoryName = h3.text() # Skript, Übungen, ..
		urls = []
		# foreach file detail
		def addToUrls(tr):
			fileName = tr.find('input.download-check').attr.value
			a = tr.find('a')
			fileTitle = a.attr.title
			fileUrl = a.attr.href
			fileDate = tr.find('td.multipow-date').text()
			urls.append({
				'fileName': fileName,
				'fileTitle': fileTitle,
				'fileUrl': fileUrl,
				'fileDate': fileDate
			})
		# find file details
		if onlyNew:
			filepattern = 'tr.multipow-file:not(.disabled)'
		else:
			filepattern = 'tr.multipow-file'
		h3.nextAll('table').eq(0).find(filepattern).each( lambda i,tr: addToUrls(PyQuery(tr)) )
		files.append({
			'categoryName': categoryName,
			'urls': urls
		})
	# find categories
	pq.find("h3.materialCategoryHeadline").each( lambda i,h3: addToFiles(PyQuery(h3)) )
	return files

def downloadFileIfNotExist(session, url, folder, fileName):
	if not os.path.exists(folder):
		os.makedirs(folder) # recursively
	dest = folder + "/" + fileName
	if not os.path.exists(dest):
		get = session.get(url, stream=True)
		with open(dest, 'wb') as file:
			for chunk in get:
				file.write(chunk)
		return True
	return False



session = login(USERNAME, PASSWORD)

courses = getCourses(session)
if(len(courses) < 1):
	error("Lehrveranstaltungen < 1")

updateInfo = "New files in community:\n\n"
for course in courses:
	# Fach Unterordner
	courseFolder = OUTPUT_FOLDER + "/" + course["name"]
	file_urls = getFilesUrlsByCourse(session, course["id"]) # todo onlyNew=True
	if len(file_urls) > 0:
		updateInfo +=  "##### "+ course["name"] +" ####:\n"
		for category in file_urls:
			# array of obj(categoryName, urls: array of obj(fileName,fileTitle,fileUrl,fileDate))

			# Kategorie Unterordner (Skripte, Übungen, ...)
			categoryFolder = courseFolder + "/" + category['categoryName']

			for url in category['urls']:
				fileUrl = url_FHR + url['fileUrl']
				fileDate = datetime.datetime.strptime(url['fileDate'], "%d.%m.%Y").strftime("%Y%m%d")
				fileTitle = url['fileTitle']
				fileName = url['fileName']
				# z.B. "community/DV-Anwendungen des Software-Engineering (DAS)/Skript/07.01.2017 09 Kanban - 09_PM_Kanban.pdf"
				fileDest = fileDate + " " + fileTitle + " - " + fileName
				downloaded = downloadFileIfNotExist(session, fileUrl, categoryFolder, fileDest)
				if downloaded:
					updateInfo += categoryFolder + "/" + fileDest + "\n"
		updateInfo += "\n"

info(updateInfo)
exit(0)