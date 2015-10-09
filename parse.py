#
strInputFilePath = "d:\\log.txt"
strOutputFilePath = "d:\\output.cpp"

######################################
file = open(strInputFilePath)


startStr = ">  <extern>"
nLenStart = len(startStr)

fOut = open(strOutputFilePath,"w")
fOut.write('#include "StdAfx.h"\n')
fOut.write('#ifndef IPHONE\n')
fOut.write('void LinkGlobalVars(){}\n')
fOut.write('#else\n')


extLines = []
for line in file:
	pos = line.find(startStr)
	if pos < 0:
		continue;
	line = line[pos + nLenStart:]	
	pos = line.find("__FACTORY_EXPORT___")
	if  pos< 0:
		continue
	fOut.write(line)
	extLines.append(line[pos:])
	
fOut.write("void LinkGlobalVars(){\n")

for line in extLines:
	fOut.write("\t"+line)
fOut.write("}\n")

fOut.write('#endif\n')