#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,re,sys
import os.path,string
import time
import PIL
from PIL import Image

##目前仅支持在Windows平台运行
##################################################
ConfList = [
	#（搜索目录,文件后缀,相似度）
	("..\\..\\Assets\\Res", ".png", 0.97),
	("..\\..\\Assets\\Res", ".tga", 0.97)
]
##################################################

#返回指定目录特定后缀的所有文件列表;
def SearchTextureFiles(rootDir, targetExt):
	ret = []
	extLen = len(targetExt)
	for root, _, files in os.walk(rootDir):
		for name in files:
			ext = name[-extLen:]
			if targetExt.lower() == ext:
				path=os.path.join(root, name)
				ret.append(path)
				#print(path)
	return ret

#将文件列表分组：文件大小+图片模式
def GroupBySize(fileList):
	ret = {}
	for f in fileList:
		img = Image.open(f,"r")
		key = str(img.size) + ":" + str(img.mode)
		img.close()
		if not ret.has_key(key):
			ret[key] = []
		ret[key].append(f)
	return ret

#计算单个文件的特征值：直方图
def calcFeature(f):
	ret = None
	img = Image.open(f,"r")
	ret = img.histogram()
	img.close()
	return ret

#比较两个特征是否相似
def compareFeature(f1, f2, ratio):
	assert(len(f1) == len(f2))
	sameCount = 0
	totalLen = len(f1)
	for i in range(0, totalLen - 1):
		if f1[i] == f2[i]:
			sameCount += 1
	ret = sameCount >= (ratio * totalLen )
	return ret

#比较文件列表中相似度高于ratio的所有文件组合;目前如果a约等于b,b约等于c时。认为a约等于c；
def CompareFiles(fileList, ratio=0.97):
	mapFileName2Feature = {}
	for f in fileList:
		mapFileName2Feature[f] = calcFeature(f)
	listLen = len(fileList)

	samePairList = []
	for i in range(0, listLen-1):
		for j in range(i+1, listLen -1 ):
			if compareFeature(mapFileName2Feature[fileList[i]], mapFileName2Feature[fileList[j]], ratio):
				samePairList.append( (i,j) )
	ret = []
	while len(samePairList) > 0:
		sel = samePairList[0]
		samePairList.pop(0)
		sameMap = {}
		sameMap[sel[0]] = True
		sameMap[sel[1]] = True

		sorted = []
		for ip in range(0, len(samePairList) - 1):
			pair = samePairList[ip]
			sorted.append(ip)
			if sameMap.has_key(pair[0]) or sameMap.has_key(pair[1]):
				sameMap[pair[0]] = True
				sameMap[pair[1]] = True
		sorted.reverse()
		for idx in sorted:
			samePairList.pop(idx)

		tret = []
		for k in sameMap.keys():
			tret.append(fileList[k])

		ret.append(tret)

	return ret

if __name__ == "__main__":
	for conf in ConfList:
		path, ext, ratio = conf[0], conf[1].lower(),  conf[2]
		print("PROCESS CONF: rootPath=%s ext=%s ratio=%.2f" % (path, ext, ratio))
		pngFiles = SearchTextureFiles(path, ext)

		gps = GroupBySize(pngFiles)

		for k in gps.keys():
			#print("PROCESS Key:", k)
			retList = CompareFiles(gps[k] , ratio)
			for ret in retList:
				print(ret)
	os.system("pause")

