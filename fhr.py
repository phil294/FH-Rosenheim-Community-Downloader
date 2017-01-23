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
import sys
import getopt
import re

url_FHR = "https://www.fh-rosenheim.de"
url_FHR_idp = "https://idp.fh-rosenheim.de"

def info(s):
	#msgbox.showwarning('FH Rosenheim Community Downloader', s)
	print(s)
def error(s):
	info(s)
	sys.exit(1)

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
def getCourses(session, community):
	url_courses = url_FHR + "/community/" + community + "/lehrveranstaltungen/?m=1"
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
# todo in unterfunktionen aufsplitten
def getFilesUrlsByCourse(session, community, courseId):
	url_material = url_FHR + "/community/" + community + "/lehrveranstaltungen/details/?tx_fhalumni_pi1[uid]=" + courseId
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
	fileName = re.sub('[^a-zA-Z0-9_\-. äöüÄÖÜß]', '_', fileName) # escape
	dest = folder + "/" + fileName
	if not os.path.exists(dest):
		get = session.get(url, stream=True)
		with open(dest, 'wb') as file:
			for chunk in get:
				file.write(chunk)
		return True
	return False

def usage():
	info('FH Rosenheim: Community Files Downloader')
	info('')
	info('Usage: fhr.py -u <username> -p <password> -c <community> -o <output-folder> [-h]')
	info('  -u, --username\tBenutzerkennung [sXXXyyyyy]')
	info('  -p, --password\tPassword')
	info('  -c, --community\tCommunity subpath in url (after "/community/"), e.g. "inf-community"')
	info('  -o, --output\t\tOutput folder. Default: "./community"')
	info('  -h, --help\t\tShow this help')

def main(argv):
	USERNAME = ""
	PASSWORD = ""
	COMMUNITY = ""
	OUTPUT_FOLDER = "community"
	try:
		opts, args = getopt.getopt(argv, "u:p:c:o:h", ["username=","password=","community=","output=","help"])
	except getopt.GetoptError:
		usage()
		error("")
	for opt, arg in opts:
		if opt in ('-h', '--help'):
			usage()
			sys.exit()
		elif opt in ('-u', '--username'):
			USERNAME = arg
		elif opt in ('-p', '--password'):
			PASSWORD = arg
		elif opt in ('-c', '--community'):
			COMMUNITY = arg
		elif opt in ('-o', '--output'):
			OUTPUT_FOLDER = arg
	if len(USERNAME) < 1 or len(PASSWORD) < 1 or len(COMMUNITY) < 1 or len(OUTPUT_FOLDER) < 1:
		usage()
		error("")

	session = login(USERNAME, PASSWORD)

	courses = getCourses(session, COMMUNITY)
	if(len(courses) < 1):
		error("No courses available in community "+COMMUNITY)

	updateInfo = "New files in community:\n\n"
	for course in courses:
		# Fach Unterordner
		courseFolder = OUTPUT_FOLDER + "/" + course["name"]
		file_urls = getFilesUrlsByCourse(session, COMMUNITY, course["id"])
		if len(file_urls) > 0:
			updateInfo +=  "##### "+ course["name"] +" ####:\n"
			for category in file_urls:
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

if __name__ == "__main__":
	main(sys.argv[1:])