import requests
import time
import json
from datetime import datetime, timezone
import threading
import subprocess
import random
import math

import _state
import parsers
import commun
import tnt
import bot as discordBot
import backup
import mapping
import fencing
import sleep


def appendJSONL(event):
    now = datetime.now(timezone.utc)
    isoYear, isoWeek, _ = now.isocalendar()
    fileName = f"server_{isoYear}-W{isoWeek:02d}.jsonl"
    with open(f"joindb/{fileName}", "a") as dbFile:
        dbFile.write(event + "\n")


# _/‾\_#_/‾\_#_/‾\_#_/‾\_ #


def dailyServerRestart():
    while True:
        time.sleep(60)
        if datetime.now(timezone.utc).hour == 11:
            if datetime.now(timezone.utc).minute == 15:
                while _state.players or _state.isBackingUp:
                    time.sleep(30)
                commun.sendTmuxCommand("mcserver", "stop")
                time.sleep(30)
                commun.sendTmuxCommand(
                    "mcserver",
                    "./bedrock_server 2>&1 | tee -a server.log",
                )
                commun.sendWebhook("daily server restart", _state.consoleLoggerUrl)
                _state.players.clear()


# _/‾\_#_/‾\_#_/‾\_#_/‾\_ #


def playerListHookUpdate():
    if _state.players:
        commun.editHookMessage(
            _state.playerListUrl,
            "1527080499200262314",
            str(_state.players)
            .replace("[", "")
            .replace("]", "")
            .replace("', ", "\n")
            .replace("'", ""),
        )
    else:
        commun.editHookMessage(
            _state.playerListUrl, "1527080499200262314", "There is no one online."
        )


# _/‾\_#_/‾\_#_/‾\_#_/‾\_ #


def statWebhook():
    while True:
        if _state.mainConfig["statWebhookSettings"]["doStatWebhook"]:
            result_cpu = subprocess.run(
                ["tmux", "capture-pane", "-t", "htopx36", "-p"],
                capture_output=True,
                text=True,
            )
            commun.editHookMessage(
                _state.statInfoUrl,
                _state.mainConfig["statWebhookSettings"]["webHookMessageID"],
                f"# CPU Usage\n```{result_cpu.stdout[:141]}```\n# Backup Info\nLast Backup was <t:{str(_state.lastBackupStamp)}:R>\nThere are currently {_state.extraBackupStats["size"]}GB of backups",
            )
        time.sleep(1)


# _/‾\_#_/‾\_#_/‾\_#_/‾\_ #


def backupWatcher():
    while True:
        time.sleep(60)
        if (
            datetime.now(timezone.utc).minute == 0
            or datetime.now(timezone.utc).minute == 30
        ):
            if _state.players or _state.lastBackupStamp < _state.lastPlayerStamp:
                backup.backupScript()


# _/‾\_#_/‾\_#_/‾\_#_/‾\_ #


def playerPolling():
    while True:
        if _state.mainConfig["playerTrackingSettings"]["doPlayerTracking"]:
            try:
                fencing.checkGeofences()  # I should make this randomly fail less but with the multithreaded-ness idk how without great complexity
            except:
                pass
            for player in _state.players:
                commun.sendTmuxCommand(
                    "mcserver",
                    f'execute at @a[name="{player}"] run summon shulker "pospoll.{player}" ~ ~-10000 ~\nexecute at @e[name="pospoll.{player}"] run tp @e[name="pospoll.{player}"] ~ ~ ~\nkill @e[name="pospoll.{player}"]\nexecute at @a[name="{player}"] run execute if block ~ -64 ~ bedrock run tag @a[name="{player}"] add dim_overworld\nexecute at @a[name="{player}"] run execute if block ~ 127 ~ bedrock run tag @a[name="{player}"] add dim_nether\ntag @a[name="{player}"] remove dim_overworld\ntag @a[name="{player}"] remove dim_nether',
                )
            if _state.players:
                time.sleep(len(_state.players) * 5)
            else:
                time.sleep(30)
        else:
            time.sleep(30)


# _/‾\_#_/‾\_#_/‾\_#_/‾\_ #


def watcher():  # main processer
    with open(_state.logFile, "r") as file:
        file.seek(0, 2)  # jump to end of file
        while True:
            line = file.readline()
            if line:
                type = parsers.determineType(line)
                if type == "join":  # do all this when a player joins
                    playerName, playerXuid, playerPfid, unix = parsers.parseJoin(line)
                    event = {
                        "joinTime": unix,
                        "exitTime": None,
                        "playerName": playerName,
                        "playerXuid": playerXuid,
                        "playerPfid": playerPfid,
                        "timestamp": unix,
                    }
                    if (
                        not _state.players
                    ):  # do this before the player gets added to the list
                        commun.sendTmuxCommand(
                            "mcserver", "gamerule doDaylightCycle true"
                        )
                    _state.players.append(playerName)
                    _state.sessionDatas[playerXuid] = event
                    _state.xuids[playerName] = playerXuid
                    _state.xuid2players[playerXuid] = playerName
                    discordBot.on_player_join(playerName, playerXuid, playerPfid, unix)
                    # print(_state.xuids)
                    modifiedPlayerList = _state.players.copy()
                    if _state.mainConfig["HerobrineSettings"]["doHerobrinePlayers"]:
                        if (
                            random.randint(
                                1,
                                _state.mainConfig["HerobrineSettings"][
                                    "HerobrineChance"
                                ],
                            )
                            == 1
                        ):
                            modifiedPlayerList.append("Herobrine")
                    if len(modifiedPlayerList) == 1:
                        command = f'tellraw "{playerName}" {{"rawtext":[{{"text":"§l§eWelcome to Name II!§r§e\\nYou are alone."}}]}}'
                    else:
                        command = f'tellraw "{playerName}" {{"rawtext":[{{"text":"§l§eWelcome to Name II!§r§e Currently online players are\\n  - {"\\n  - ".join(modifiedPlayerList).replace("[", "").replace("]", "")}"}}]}}'  # why the hell did I code it this way
                    commun.sendTmuxCommand("mcserver", command)
                    commun.sendWebhook(
                        f"→ {playerName} joined the server at <t:{unix}:F>",
                        _state.consoleLoggerUrl,
                    )  # form permissions.json
                    if playerXuid not in _state.verifyData:
                        commun.sendTmuxCommand(
                            "mcserver",
                            f'tellraw "{playerName}" {{"rawtext":[{{"text":"(i) You are not verified. Run /verify on the discord server to become a member."}}]}}',
                        )
                        if not any(p["xuid"] == playerXuid for p in _state.permissions):
                            _state.permissions.append(
                                {
                                    "permission": "visitor",
                                    "xuid": playerXuid,
                                }
                            )
                            with open(
                                "bedrock-server/permissions.json", "w"
                            ) as permission_file:
                                json.dump(_state.permissions, permission_file, indent=2)
                            commun.sendTmuxCommand("mcserver", "permission reload")
                    if playerXuid in _state.verifyData:
                        discordBot.catchMissingSettingData(
                            _state.verifyData[playerXuid]
                        )
                        _state.userSettings[_state.verifyData[playerXuid]].setdefault(
                            "locatorbar", True
                        )
                        if not _state.userSettings[_state.verifyData[playerXuid]][
                            "locatorbar"
                        ]:
                            _state.playersWithoutBar.append(playerXuid)
                            commun.sendTmuxCommand(
                                "mcserver", "gamerule playerwaypoints off"
                            )
                    playerListHookUpdate()

                if type == "leave":
                    playerName, playerXuid, playerPfid, unix = parsers.parseLeave(line)
                    if playerXuid in _state.sessionDatas:
                        event = _state.sessionDatas[playerXuid]
                        event["exitTime"] = unix
                        jsonString = json.dumps(event, separators=(",", ":"))
                        appendJSONL(jsonString)
                        _state.sessionDatas.pop(playerXuid, None)
                    if playerName.rstrip() in _state.players:
                        _state.players.remove(playerName.rstrip())
                    if not _state.players:
                        commun.sendTmuxCommand(
                            "mcserver", "gamerule doDaylightCycle false"
                        )
                        _state.lastPlayerStamp = unix
                    for key in [k for k in _state.geofence_ids if k[0] == playerName]:
                        fence_id = key[1]
                        entry = _state.geofence_ids[key]
                        log_path = (
                            f"logs/{playerName}_{fence_id}_{entry["first_time"]}.csv"
                        )
                        with open(log_path, "w") as f:
                            f.write(entry["log"])
                        commun.editHookMessage(
                            _state.consoleLoggerUrl,
                            entry["id"],
                            f"{playerName} exited geofence {fence_id} at <t:{str(entry["first_time"])}:T> (x{str(entry["count"])}). They left before returning.",
                            log_path,
                        )
                        _state.geofence_ids.pop(key)
                    commun.sendWebhook(
                        f"← {playerName} left the server at <t:{unix}:F>",
                        _state.consoleLoggerUrl,
                    )
                    if playerXuid in _state.verifyData:
                        discordBot.catchMissingSettingData(
                            _state.verifyData[playerXuid]
                        )
                        _state.userSettings[_state.verifyData[playerXuid]].setdefault(
                            "locatorbar", True
                        )
                        if not _state.userSettings[_state.verifyData[playerXuid]][
                            "locatorbar"
                        ]:
                            _state.playersWithoutBar.remove(playerXuid)
                            if not _state.playersWithoutBar:
                                commun.sendTmuxCommand(
                                    "mcserver", "gamerule playerwaypoints everyone"
                                )
                    if playerName in _state.afk_players:
                        _state.afk_players.remove(playerName)
                    if _state.xuids[playerName] in _state.afk_players[0]["exdata"]["manually_toggled"]:
                        _state.afk_players[0]["exdata"]["manually_toggled"].remove(_state.xuids(playerName))
                    playerListHookUpdate()
                    sleep.update_sleep_per()
                    if _state.mainConfig["playerTrackingSettings"]["doPlayerTracking"]:
                        try:  # if a player leaves before their position is polled, they will not be on the list
                            _state.posData.pop(playerName)
                        except KeyError:
                            pass
                        if _state.mainConfig["playerTrackingSettings"][
                            "trackToFileSettings"
                        ]["doTrackToFile"]:
                            with open(
                                _state.mainConfig["playerTrackingSettings"][
                                    "trackToFileSettings"
                                ]["trackToFile"],
                                "w",
                            ) as posApiFile:
                                json.dump(_state.posData, posApiFile)

                if type == "tntpos":
                    # get tnt pos
                    _state.TNTData["tntPos"] = line.split(" Teleported TNTFound to ")[
                        1
                    ].rstrip()
                    if _state.TNTData.get("playerName") and _state.TNTData.get(
                        "tntPos"
                    ):
                        tnt.TNTMessage()

                if type == "tnttag":
                    # get player near tnt
                    # reacts like [2026-06-05 04:16:47:488 INFO] Added tag 'nearestTNT' to snowboyz0825
                    _state.TNTData["playerName"] = line.split(
                        " Added tag 'nearestTNT' to "
                    )[1].rstrip()
                    if _state.TNTData.get("playerName") and _state.TNTData.get(
                        "tntPos"
                    ):
                        tnt.TNTMessage()
                if not any(substring in line for substring in _state.excludeSubStrings):
                    requests.post(
                        _state.consoleLoggerUrl, json={"content": line.rstrip()}
                    )

                if type == "stop":
                    _state.players = []

                # I should probably throw all this in parsers.py but eh
                if type == "pospoll":
                    if not "0.00, -100.00, 0.00" in line:
                        username = line.split(".")[1].split(" to ")[0]
                        _state.posData.setdefault(username, {})
                        _state.posData[username]["dimension"] = "the_end"
                        x = float(
                            line.split("Teleported pospoll")[1]
                            .split(" to ")[1]
                            .split(", ")[0]
                        )
                        y = (
                            float(
                                line.split("Teleported pospoll")[1]
                                .split(" to ")[1]
                                .split(", ")[1]
                            )
                            + 10000
                        )
                        z = float(
                            line.split("Teleported pospoll")[1]
                            .split(" to ")[1]
                            .split(", ")[2]
                            .rstrip()
                        )
                        try:
                            player = _state.posData[username]
                            if player["x"] == x and player["y"] == y and player["z"] == z:
                                since = player.setdefault("afk_since", int(time.time()))
                                if int(time.time()) - since > _state.mainConfig["afkTime"] and username not in _state.afk_players:
                                    _state.afk_players.append(username)
                                    commun.sendTmuxCommand("mcserver", f"say §8§o{username} is AFK")
                                    commun.sendWebhook(f"{username} is afk", _state.consoleLoggerUrl)
                                    sleep.update_sleep_per()
                            else:
                                player.pop("afk_since", None)  
                                if username in _state.afk_players and _state.xuids[username] not in _state.afk_players[0]["exdata"]["manually_toggled"]:
                                    commun.sendTmuxCommand("mcserver", f"say §8§o{username} is no longer AFK")
                                    _state.afk_players.remove(username)
                                    sleep.update_sleep_per()  
                        except KeyError:
                            pass
                        _state.posData[username]["x"] = x
                        _state.posData[username]["y"] = y
                        _state.posData[username]["z"] = z
                if type == "dimpoll":
                    username = line.split("' to ")[1].rstrip()
                    if not username in _state.posData:
                        continue
                    _state.posData[username]["dimension"] = line.split("' to ")[
                        0
                    ].split("_")[1]
                    if len(_state.posData) == len(_state.players):
                        if _state.mainConfig["playerTrackingSettings"][
                            "trackToFileSettings"
                        ]["doTrackToFile"]:
                            with open(
                                _state.mainConfig["playerTrackingSettings"][
                                    "trackToFileSettings"
                                ]["trackToFile"],
                                "w",
                            ) as posApiFile:
                                json.dump(_state.posData, posApiFile)

                if (
                    type == "savequery"
                ):  # getting disapointed with how many types I've added
                    _state.saveQueryQuery = json.loads(
                        '{"'
                        + line.replace(", ", ',"').replace(":", '":').rstrip()
                        + "}"
                    )  # one day I'll learn regex. today is not that day

            time.sleep(0.05)


# _/‾\_#_/‾\_#_/‾\_#_/‾\_ #

# lists the players to add to the list as a sort of recovery
# that way you don't have to restart the mcserver every time you restart the script.
# leads to bugs occasionally but those SHOULD be properly guarded
# needs to run first to avoid log noise

with open(_state.logFile, "r") as file:
    file.seek(0, 2)
    commun.sendTmuxCommand("mcserver", "list")
    line = file.readline()
    while ("There are " in line and "players online:" in line) or line == "":
        if "There are 0/" in line:
            break
        line = file.readline()
        time.sleep(0.05)
    if "There are 0/" not in line:
        for playerName in line.split("INFO] ")[-1].strip().split(", "):
            _state.players.append(playerName.strip())

# _/‾\_#_/‾\_#_/‾\_#_/‾\_ #

TNTWatchdogThread = threading.Thread(target=tnt.TNTWatchdog, daemon=True)
TNTWatchdogThread.start()

backupThread = threading.Thread(target=backupWatcher, daemon=True)
backupThread.start()

serverRestartThread = threading.Thread(target=dailyServerRestart, daemon=True)
serverRestartThread.start()

statThread = threading.Thread(target=statWebhook, daemon=True)
statThread.start()

botThread = threading.Thread(target=discordBot.run_bot, daemon=True)
botThread.start()

positionPollingThread = threading.Thread(target=playerPolling, daemon=True)
positionPollingThread.start()

# _/‾\_#_/‾\_#_/‾\_#_/‾\_ #

watcher()
