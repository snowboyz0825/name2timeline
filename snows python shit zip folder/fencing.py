import _state
import commun

import time
import json


def checkGeofences():
    for id in _state.geoFences:
        for name in _state.posData:
            try:
                if _state.xuids[name] in _state.geoFences[id]["excluded"]:
                    continue
            except Exception as e:
                print(f"exclusion check failed: {e}")
            if _state.geoFences[id]["included"]:
                try:
                    if not _state.xuids[name] in _state.geoFences[id]["included"]: #the mixing of xuids and playernames for databases is getting tiresome, I need to pick one
                        continue #I should probably pick xuids, they do not change
                except KeyError:
                    continue
            if _state.geoFences[id]["inverted"]:
                geofence_change = ("exited", "returned")
            else:
                geofence_change = ("entered", "exited")
            if _state.posData[name]["dimension"] == _state.geoFences[id]["dimension"]:
                dx = _state.posData[name]["x"] - _state.geoFences[id]["x"]
                dz = _state.posData[name]["z"] - _state.geoFences[id]["z"]
                distance = (dx**2 + dz**2) ** 0.5  # pythagoras you dirty dog
                if (
                    distance < _state.geoFences[id]["distance"]
                    and not _state.geoFences[id]["inverted"]
                    or distance > _state.geoFences[id]["distance"]
                    and _state.geoFences[id]["inverted"]
                ):
                    if (
                        name,
                        id,
                    ) in _state.geofence_ids:  # if we've been in the geofence before
                        _state.geofence_ids[(name, id)]["last_time"] = int(time.time())
                        _state.geofence_ids[(name, id)]["count"] += 1
                        _state.geofence_ids[(name, id)][
                            "log"
                        ] += f"\n{name},{str(time.strftime("%H:%M:%S", time.localtime(_state.geofence_ids[(name, id)]["last_time"])))},{_state.posData[name]["x"]},{_state.posData[name]["y"]},{_state.posData[name]["z"]}"
                        commun.editHookMessage(
                            _state.consoleLoggerUrl,
                            _state.geofence_ids[(name, id)]["id"],
                            f"{name} {geofence_change[0]} geofence {id} at <t:{str(_state.geofence_ids[(name, id)]["first_time"])}:T> (x{str(_state.geofence_ids[(name, id)]["count"])})",
                        )
                    else:  # If they're in the geofence for the first time
                        first_time = int(time.time())
                        message = commun.sendWebhook(
                            f"{name} {geofence_change[0]} geofence {id} at <t:{str(first_time)}:T>",
                            _state.consoleLoggerUrl,
                            True,
                        )
                        logitem = "name,time,x,y,z"
                        logitem += f"\n{name},{str(time.strftime("%H:%M:%S", time.localtime(first_time)))},{_state.posData[name]["x"]},{_state.posData[name]["y"]},{_state.posData[name]["z"]}"
                        meta_snippet = {
                            "id": message["id"],
                            "first_time": first_time,
                            "last_time": first_time,
                            "count": 1,
                            "log": logitem,
                        }
                        _state.geofence_ids[(name, id)] = meta_snippet
                elif (
                    name,
                    id,
                ) in _state.geofence_ids:  # if they've returned to the geofence
                    log_path = f"logs/{name}_{id}_{_state.geofence_ids[(name, id)]["first_time"]}.csv"
                    with open(log_path, "w") as f:
                        f.write(_state.geofence_ids[(name, id)]["log"])
                    commun.editHookMessage(
                        _state.consoleLoggerUrl,
                        _state.geofence_ids[(name, id)]["id"],
                        f"{name} {geofence_change[0]} geofence {id} at <t:{str(_state.geofence_ids[(name, id)]["first_time"])}:T> (x{str(_state.geofence_ids[(name, id)]["count"])}). They {geofence_change[1]} at <t:{str(int(time.time()))}:T>",
                        log_path,
                    )

                    _state.geofence_ids.pop((name, id))
            elif (
                name,
                id,
            ) in _state.geofence_ids:  # If they leave to another dimension
                _state.geofence_ids[(name, id)][
                    "log"
                ] += f"\n{name},{str(time.strftime("%H:%M:%S", time.localtime(_state.geofence_ids[(name, id)]["last_time"])))},{_state.posData[name]["x"]},{_state.posData[name]["y"]},{_state.posData[name]["z"]}"
                log_path = f"logs/{name}_{_state.geofence_ids[(name, id)]["id"]}_{_state.geofence_ids[(name, id)]["first_time"]}.csv"
                with open(log_path, "w") as f:
                    f.write(_state.geofence_ids[(name, id)]["log"])
                commun.editHookMessage(
                    _state.consoleLoggerUrl,
                    _state.geofence_ids[(name, id)]["id"],
                    f"{name} exited geofence {id} at <t:{str(_state.geofence_ids[(name, id)]["first_time"])}:T> (x{str(_state.geofence_ids[(name, id)]["count"])}). They entered the {_state.posData[name]["dimension"]} at <t:{str(int(time.time()))}:T>",
                    log_path,
                )
                _state.geofence_ids.pop((name, id))


def write_geofences():
    with open("data/geoFences.json", "w") as geofences_file:
        json.dump(_state.geoFences, geofences_file, indent=2)
