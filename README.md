# FH-Rosenheim-Community-Downloader
Python: Automatic file downloader for material of Fachhochschule Rosenheim courses. Downloads files (if not already done so) in format...

    "[output]/[course]/[category]/[date] [title] [name]"

USAGE:

	fhr.py -u <username> -p <password> -c <community> -o <output-folder> [-h]
	  -u, --username	Benutzerkennung [sXXXyyyyy]
	  -p, --password	Password
	  -c, --community	Community subpath in url (after "/community/"), e.g. "inf-community"')
	  -o, --output		Output folder. Default: "./community"
	  -h, --help
	  
Pls report errors. (Dependency install of modules like pyquery via pip. Windows: `python -m pip install [package-name]`)

Preview

![preview](http://i.imgur.com/77oF22P.png)

![preview](http://i.imgur.com/ZmaVuqQ.png)
