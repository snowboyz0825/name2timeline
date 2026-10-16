import _state
import commun
import subprocess
import time

def generateUnminedMap():
    commun.sendWebhook("unmined map generation started.", _state.consoleLoggerUrl)

    open("unmined.log", "w").close() #deletes the log beforehand to eliminate possible (extremely rare) race conditions

    subprocess.run(
        [
            "tmux",
            "new",
            "-d",
            "-s",
            "unmined"
        ],
    capture_output=True,
    text=True,
    )
    command = "unmined/unmined-cli web render "
    for item in _state.mainConfig["mapSettings"]["mapArgs"]:
        command += (" " + item)
    #send unmined command, filter redundant items for a tiny performance gain, pipes to log for parsing
    commun.sendTmuxCommand("unmined", command + " 2>&1 | grep --line-buffered -E -v \"(BedrockWorldIndex)|Found player data player_|(ConfigLoader)|(ConfigurationLoader)|Rendering tile |Looking for changed tiles at \" > unmined.log" + " && tmux kill-pane")
    with open("unmined.log", "r") as unminedLog:
        unminedLog.seek(0, 2)  
        while True:
            line = unminedLog.readline()
            if not line:
                time.sleep(0.1)
                continue
            if "Elapsed time total: " in line: #SHOULD be the final thing sent
                break 
            if _state.players:
                commun.sendTmuxCommand("unmined", "C-c") #kills tmux session if anyone joins for safety
                break
        commun.sendWebhook("unmined map generation completed.", _state.consoleLoggerUrl)
