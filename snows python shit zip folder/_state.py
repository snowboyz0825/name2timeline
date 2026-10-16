import json

posData = {}
sessionDatas = {}
players = []
xuid2players = {}
xuids = {}
TNTData = {}
isBackingUp = False
lastPlayerStamp = 0
lastBackupStamp = 0
saveQueryQuery = ""
extraBackupStats = {"size":100}
geofence_ids = {}
afk_players = [{"exdata":{"manually_toggled":[]}}]
lastSleepPct = None
kick_data = {}

logFile = "bedrock-server/server.log"

with open("data/verifyData.json", "r") as verifyFile:
    verifyData = json.load(verifyFile)
with open("bedrock-server/permissions.json", "r") as perms_file:
    permissions = json.load(perms_file)
with open("data/friends.json", "r") as friends_file:
    friends = json.load(friends_file)
with open("env.json", "r") as env_file:
    env = json.load(env_file)
    consoleLoggerUrl = env["consoleLogWebhook"]
    playerListUrl = env["playerListEditWebhook"]
    statInfoUrl = env["serverUSageEditWebhook"]
with open("config.json", "r") as config_file:
    mainConfig = json.load(config_file)
with open("data/geoFences.json", "r") as geoFences_file:
    geoFences = json.load(geoFences_file)
with open("data/userSettings.json", "r") as user_settings_file:
    userSettings = json.load(user_settings_file)


playersWithoutBar = []    

if mainConfig["filterLogs"]:
    excludeSubStrings = [
        "Running AutoCompaction...",
        "say §8§oSaving Paused",
        "save hold",
        "Saving...",
        "save resume",
        "say §8§oSaving Resumed",
        "Changes to the world are resumed.",
        "Player connected: ",
        "Player PartyIdUpdate:  ",
        "Player Spawned: ",
        "Player disconnected: ",
        "execute at @e[type=tnt] run summon armor_stand TNTFound ~ ~10000 ~",
        "execute at @e[name=TNTFound] run tp @e[name=TNTFound] ~ ~ ~",
        "execute at @e[type=tnt] run tag @p add nearestTNT",
        "tag @a remove nearestTNT",
        "kill @e[name=TNTFound]",
        "No targets matched selector",
        "Target does not have this tag",
        "§l§eWelcome to Name II!§r§e ",
        "Object successfully summoned",
        "Killed TNTFound",
        "Added tag 'nearestTNT' to ",
        "Removed tag 'nearestTNT' from ",
        "gamerule doDaylightCycle ",
        "Killed pospoll",
        "Teleported pospoll",
        "Failed to execute 'execute' as [Null]",
        "tag 'dim_overworld'",
        "tag 'dim_nether'",
        "tag 'dim_end'",
        "Execute subcommand if block test failed.",
        "Execute subcommand unless block test failed.",
        "Data saved. Files are now ready to be copied.",
        "A previous save has not been completed.",
        "Bedrock level/db/"
    ]
else:
    excludeSubStrings = []
excludeSubStrings += mainConfig["customLogFilters"]
    
def isDcidOnline(discord_id):
    xuid = verifyData.get(str(discord_id))
    if not xuid:
        return False
    name = xuid2players.get(xuid)
    return name in players

def write_settings():
    with open("config.json", "w") as config_file:
        json.dump(mainConfig, config_file, indent=3)