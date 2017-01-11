outpath = "..\\dep\\"

svnFile = open("a.txt")

import os
from shutil import copyfile
from shutil import copytree

for l in svnFile:
	l = l[8:]
	l = l[:-1]
	
	if os.path.isdir(l):
		if  not os.path.isdir(outpath + l):
			print "coyp dir:" + l
			copytree(l, outpath + l)
		continue
	
	if os.path.isfile(l) and os.path.isfile(outpath + l):
		continue
	
	dir = os.path.dirname(l)
	outdir = outpath + dir
	print outdir
	if not os.path.isdir(outdir):
		os.makedirs(outdir)
	print dir
	
	
	if os.path.isfile(l):
		print "coyp file:" + l
		copyfile(l, outpath + l)
	
	
	#print l