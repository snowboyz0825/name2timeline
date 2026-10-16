import math
import _state
import commun

def update_sleep_per():
    orig_per = _state.mainConfig.get("playerSleepingPercentage", 100)
    total_players = len(_state.players)
    afk = len([p for p in _state.afk_players if p in _state.players])
    active = total_players - afk
    if total_players == 0 or afk == 0 or active <= 0:
        adj_per = orig_per
    else:
        adj_per = (math.ceil(active * orig_per / 100) * 100) // total_players
    if adj_per != _state.lastSleepPct:
        _state.lastSleepPct = adj_per
        commun.sendTmuxCommand("mcserver", f"gamerule playersSleepingPercentage {adj_per}")
        commun.sendWebhook(f"slpcentage set {adj_per}", _state.consoleLoggerUrl)

        