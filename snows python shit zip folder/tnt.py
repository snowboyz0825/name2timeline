import time
import commun
import _state


def TNTWatchdog():
    while True:
        if _state.players:
            _state.TNTData.clear()
            commun.sendTmuxCommand(
                "mcserver",
                "execute at @e[type=tnt] run summon armor_stand TNTFound ~ ~-10000 ~ \n execute at @e[name=TNTFound] run tp @e[name=TNTFound] ~ ~ ~ \n execute at @e[type=tnt] run tag @p add nearestTNT \n kill @e[name=TNTFound] \n tag @a remove nearestTNT",
            )
        time.sleep(3.5)



def TNTMessage():
    commun.sendWebhook(
        f"<@&1457323549986521088>, <@&1240133433045286974> - Primed TNT found near {_state.TNTData['playerName']} at {_state.TNTData['tntPos']}",
        _state.consoleLoggerUrl,
    )
    _state.TNTData.clear()
