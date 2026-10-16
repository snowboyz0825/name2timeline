import math
from datetime import datetime, timezone


def parseJoin(joinLine):
    playerName = joinLine.split("Player Spawned: ")[1].split(" xuid: ")[0]
    playerXuid = joinLine.split(" xuid: ")[1].split(", pfid: ")[0]
    playerPfid = joinLine.split(" pfid: ")[1].rstrip()
    joinTime = joinLine.split("[")[1].split(" INFO]")[0]
    unix = math.trunc(datetime.strptime(joinTime, "%Y-%m-%d %H:%M:%S:%f").timestamp())
    return playerName, playerXuid, playerPfid, unix


def parseLeave(leaveLine):
    playerName = leaveLine.split("Player disconnected: ")[1].split(", xuid: ")[0]
    playerXuid = leaveLine.split(", xuid: ")[1].split(", pfid: ")[0]
    playerPfid = leaveLine.split(", pfid: ")[1].rstrip()
    leaveTime = leaveLine.split("[")[1].split(" INFO]")[0]
    unix = math.trunc(datetime.strptime(leaveTime, "%Y-%m-%d %H:%M:%S:%f").timestamp())
    return playerName, playerXuid, playerPfid, unix


def determineType(line):
    if "Player Spawned: " in line:
        return "join"
    elif "Player disconnected: " in line:
        return "leave"
    elif "Teleported TNTFound to " in line:
        return "tntpos"
    elif "Added tag 'nearestTNT' to " in line:
        return "tnttag"
    elif "Server stop requested" in line:
        return "stop"
    elif "Teleported pospoll" in line:
        return "pospoll"
    elif "Added tag 'dim_" in line:
        return "dimpoll"
    elif ".ldb" in line or "MANIFEST-" in line or ".log" in line:
        return "savequery"
    else:
        return "other"
