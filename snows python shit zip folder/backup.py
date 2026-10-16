import subprocess
import _state
import time
import commun
from datetime import datetime, timezone
import os
import json
import mapping

def getSummaryLine(backupResult):
    for line in backupResult.stdout.splitlines():
        if '"message_type":"summary"' in line:
            return line
    return "No summary line found in restic output."


def createBackup():
    backupResult = subprocess.run(
        [
            "restic",
            "--json",
            "--compression", 
            "off",
            "-r",
            "backups/",
            "--insecure-no-password",
            "backup",
            "bedrock-server/worlds/cached",
        ],
        capture_output=True,
        text=True,
    )
    print(backupResult.stdout)
    commun.sendWebhook(str((json.loads(getSummaryLine(backupResult))["data_added"])/1000000) + " MB", _state.consoleLoggerUrl)
    _state.lastBackupStamp = int(time.time())
    return backupResult

def cacheWorldFiles():
    cahceResult = subprocess.run(
        [
            "rsync",
            "-ravPsc",
            "--delete",
            "bedrock-server/worlds/Bedrock level/",
            "bedrock-server/worlds/cached/"
        ],
        capture_output=True,
        text=True,
    )
    return cahceResult

def backupScript():
    _state.isBackingUp = True
    commun.sendTmuxCommand("mcserver", "say §8§oSaving Paused [Creating Backup]")
    commun.sendTmuxCommand("mcserver", "save hold")
    _state.saveQueryQuery = ""
    time.sleep(0.5)
    commun.sendTmuxCommand("mcserver", "save query")
    retrycounter = 0
    while not _state.saveQueryQuery:
        time.sleep(2)
        if _state.saveQueryQuery:
            break
        commun.sendTmuxCommand("mcserver", "save query")
        retrycounter += 1
        print (f"retried query {retrycounter} times")
    print (f"retried query {retrycounter} times")
    time.sleep(0.25)
    cacheResult = cacheWorldFiles()
    for fileName, length in _state.saveQueryQuery.items():
        #print(f"fileName: {"bedrock-server/worlds/" + fileName.replace("Bedrock level", "cached")}, byte-length: {length}")
        os.truncate("bedrock-server/worlds/" + fileName.replace("Bedrock level", "cached"), length)
    commun.sendTmuxCommand("mcserver", "save resume")
    commun.sendTmuxCommand("mcserver", "say §8§oSaving Resumed [Backup Complete]")
    backup_stdout = createBackup()
    _state.isBackingUp = False
    if not _state.players:
        subprocess.run(
    [
        "restic", "forget",
        "--group-by", "",
        "--keep-within", "3d",
        "--keep-hourly", "240",
        "--keep-daily", "90",
        "--keep-weekly", "26",
        "--keep-monthly", "120",
        "--prune",
        "-r", _state.mainConfig["backupSettings"]["backupDir"],
        "--insecure-no-password"
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
        
        result_backup_usage = subprocess.run(
                ["du", "-sb", f"{_state.mainConfig["backupSettings"]["backupDir"]}/"],
                capture_output=True,
                text=True,
            )
        try:
            _state.extraBackupStats["size"]=round(int((result_backup_usage.stdout).split()[0])/1073741824, 2)
        except:
            pass #I think that occasionally this fails and causes crashes, so I added a try. I am unsure if it does or not or why
        mapping.generateUnminedMap()
    return backup_stdout
