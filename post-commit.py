#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
import json
import re
import requests
import traceback
import os

# 设置环境变量以确保 UTF-8 编码
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

REDMINE_URL = "http://192.168.11.213:8080/redmine"
REDMINE_API_KEY = "983de8712b10c406b43c518f003f0a4977085e40"  ##对应redmine里的SVN账号

# 设置日志文件路径
LOG_FILE = '/tmp/post-commit.log'

def log(message):
	return
	with open(LOG_FILE, 'a') as f:
		f.write(f"{message}\n")

HTTP_headers = {
	'X-Redmine-API-Key': REDMINE_API_KEY,
	'Content-Type': 'application/json'
}

# svn名对应的 redmine名字
NameMap = {

}

def extract_info(s):
	"""
	从字符串列表中提取 # 号前后的字符。
	
	:param strings: 包含各种格式字符串的列表
	:return: 提取结果的列表，每个元素是一个字典，包含 'prefix' 和 'issue_id'
	"""
	pattern = re.compile(r'(?:(?P<prefix>[^\s#]+)#|(#))(?P<issue_id>\d+)')
	
	match = pattern.search(s)
	if match:
		prefix = match.group('prefix')
		issue_id = match.group('issue_id')
		if not prefix:
			prefix = ''  # 如果没有前缀，则设置为空字符串
		return prefix, issue_id

def get_commit_info(repo_path, revision):
	"""
	获取指定版本的提交详细信息。
	
	:param repo_path: SVN仓库路径
	:param revision: 提交的版本号
	:return: 包含提交详细信息的字典
	"""
	# 获取提交日志信息
	result = subprocess.run(['svnlook', 'log', '-r', revision, repo_path], 
							stdout=subprocess.PIPE, 
							stderr=subprocess.PIPE)
	log_message = result.stdout.decode('utf-8').strip()

	# 获取更改的目录列表
	result_dirs = subprocess.run(['svnlook', 'dirs-changed', '-r', revision, repo_path], 
								 stdout=subprocess.PIPE, 
								 stderr=subprocess.PIPE)
	dirs_changed = result_dirs.stdout.decode('utf-8').strip().splitlines()

	# 获取提交者信息
	result_author = subprocess.run(['svnlook', 'author', '-r', revision, repo_path], 
									stdout=subprocess.PIPE, 
									stderr=subprocess.PIPE)
	author = result_author.stdout.decode('utf-8').strip()

	# 获取提交日期
	result_date = subprocess.run(['svnlook', 'date', '-r', revision, repo_path], 
								 stdout=subprocess.PIPE, 
								 stderr=subprocess.PIPE)
	date = result_date.stdout.decode('utf-8').strip()

	# 获取修改的文件列表
	result_changed = subprocess.run(['svnlook', 'changed', '-r', revision, repo_path], 
									stdout=subprocess.PIPE, 
									stderr=subprocess.PIPE)
	changed_files = result_changed.stdout.decode('utf-8').strip().splitlines()
	
	# 解析修改的文件列表
	parsed_changes = []
	for line in changed_files:
		action = line[:1]  # 文件操作类型（A, D, U等）
		path = line[4:]	# 文件或目录路径
		parsed_changes.append({
			"action": action,
			"path": path
		})

	return {
		"log": log_message,
		"dirs_changed": dirs_changed,
		"revision": revision,
		"repository": repo_path,
		"author": author,
		"date": date,
		"changes": parsed_changes
	}

def query_issue_info(issue_id):
	"""
	获取指定ID的issue信息，并提取Issue状态和指派者。
	:param issue_id: 要查询的issue ID
	:return: 包含issue状态和指派者的信息字典
	"""
	url = f"{REDMINE_URL}/issues/{issue_id}.json"

	try:
		response = requests.get(url, headers=HTTP_headers)
		response.raise_for_status()  # 如果响应状态码不是200，抛出HTTPError
		
		data = response.json()
		issue = data['issue']
		
		# 提取所需信息
		status = issue.get('status', {}).get('name', 'N/A')
		assigned_to = issue.get('assigned_to', {}).get('name', 'Unassigned')
		
		return {
			'id': issue_id,
			'status': status,
			'assigned_to': assigned_to
		}
	
	except requests.exceptions.RequestException as e:
		log(f"请求错误: {e}")
		return None

def add_comment_to_redmine_issue(redmine_url, issue_id, comment, newIssueStatusId):
	"""
	将评论添加到Redmine中的指定issue。
	
	:param redmine_url: Redmine实例的基础URL
	:param issue_id: 要更新的issue ID
	:param comment: 要添加的评论内容
	"""
	url = f"{redmine_url}/issues/{issue_id}.json"

	data = {
		"issue": {
			"notes": comment
		}
	}

	if newIssueStatusId:
		data["issue"]["status_id"] = newIssueStatusId

	try:
		response = requests.put(url, headers=HTTP_headers, data=json.dumps(data))
		response.raise_for_status()  # 如果响应状态码不是200，抛出HTTPError
		
		#log(f"Comment added to issue {issue_id}")
	except requests.exceptions.RequestException as e:
		log(f"请求错误: {e}")

def tryGetNewStateId(commit_info, issueAction, issueId):
	redmineInfo = NameMap.get(commit_info['author'])
	if not redmineInfo:
		return None
	redmineName, redmineKey = redmineInfo[0], redmineInfo[1]

	issueSt = query_issue_info(issueId)
	#log(json.dumps(issueSt, indent=4))
	if not issueSt or redmineName != issueSt.get('assigned_to'):
		return None
	HTTP_headers['X-Redmine-API-Key'] = redmineKey

	redminestatus = issueSt.get('status')
	if redminestatus == "待处理":
		return issueAction == "fix" and 3 or 11
	
	if redminestatus == "进行中":
		return issueAction == "fix" and 3 or None
	
	if redminestatus == "主干测试通过":
		return issueAction == "merge" and 9 or None
	return None

if __name__ == '__main__':
	if len(sys.argv) < 3:
		log("Usage: {} <repo_path> <revision>".format(sys.argv[0]))
		sys.exit(1)

	try:
		repo_path = sys.argv[1] 
		revision = sys.argv[2]
		commit_info = get_commit_info(repo_path, revision)
		#log(json.dumps(commit_info, indent=4))

		# 从svn日志中提取  #issuId
		commit_log = commit_info['log']
		issueAction, issueId = extract_info(commit_log)

		if not issueId or str(issueId) == "0":
			log(f"can not get issueId by log {commit_log}")
			sys.exit(0)

		newStatusId = tryGetNewStateId(commit_info, issueAction, issueId)

		#log(f"newStatusId newStatusId={newStatusId} issueAction={issueAction} issueId={issueId}")
		# 构建要添加到Redmine issue的评论内容
		commit_author = commit_info.get('author')
		commit_date = commit_info.get('date')
		#log(f"commit {commit_author} {commit_date}")
		comment = (f"Commit #{commit_info['revision']} by {commit_author} on {commit_date}\n\n"
					f"Log: {commit_log}\n\n"
					f"Changes:\n")
		for change in commit_info['changes']:
			comment += f"- [{change['action']}] {change['path']}\n"

		add_comment_to_redmine_issue(REDMINE_URL, issueId, comment, newStatusId)
	except Exception as e:
		log(f"Exception {e}")
		traceback.print_exc()
		sys.exit(2)

