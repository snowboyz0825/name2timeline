import requests
import subprocess
import _state
import json

def sendWebhook(content, url, get_response=False):
    if get_response:
        url += "?wait=true"
    response = requests.post(url, json={"content": content})
    print(f"Sent webhook: {content}")
    if get_response:
        return response.json()

def editHookMessage(url, message_id, content, filepath=None):
    edit_url = f"{url}/messages/{message_id}"
    if filepath:
        with open(filepath, "rb") as f:
            files = {"files[0]": (filepath.split("/")[-1], f)}
            payload = {"payload_json": json.dumps({"content": content})}
            response = requests.patch(edit_url, data=payload, files=files)
    else:
        response = requests.patch(edit_url, json={"content": content})
    return response
        
def sendTmuxCommand(session_name, command):
    try:
        subprocess.run(
            ["tmux", "send-keys", "-t", session_name, command, "ENTER"], check=True
        )
        if _state.mainConfig["tmuxCommandSettings"]["printTmuxCommands"]:
            NotprintOutput = False
            for item in _state.mainConfig["tmuxCommandSettings"]["filterTmuxStrings"]:
                if item in command:
                    NotprintOutput = True
            if not NotprintOutput:
                print(session_name + " was sent " + command)
    except subprocess.CalledProcessError:
        print(
            f"Error: Could not send command to tmux session '{session_name}'. Is it running?"
        )

