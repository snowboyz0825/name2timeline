import discord
import asyncio
from discord import app_commands
import random
import json
import time
from typing import Optional
import requests
import mapping
import subprocess

import commun
import _state
import backup
import fencing
import sleep

# _/‾\_#_/‾\_#_/‾\_#_/‾\_#

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
bot_loop = None
verifyCodes = {}

# _/‾\_#_/‾\_#_/‾\_#_/‾\_#


def writeSettingsData():
    with open("data/userSettings.json", "w") as settingsFile:
        json.dump(_state.userSettings, settingsFile, indent=2)


def writeFriendData():
    with open("data/friends.json", "w") as friendFile:
        json.dump(_state.friends, friendFile, indent=2)


def catchMissingFriendData(id):
    if not id in _state.friends:
        _state.friends[id] = {
            "friends": [],
            "outgoing": [],
            "incoming": [],
            "settings": {},
        }


async def admin_only(interaction):
    if not (
        interaction.user.guild_permissions.administrator
        or any(role.id == 1457323549986521088 for role in interaction.user.roles)
    ):
        await interaction.response.send_message(
            "You must be <@&1240133433045286974> or <@&1457323549986521088> for that command."
        )
        return False
    else:
        return True


# _/‾\_#_/‾\_#_/‾\_#_/‾\_#


def on_player_join(playerName, playerXuid, playerPfid, unix):
    if bot_loop:
        asyncio.run_coroutine_threadsafe(
            _on_player_join(playerName, playerXuid, playerPfid, unix), bot_loop
        )


async def _on_player_join(playerName, playerXuid, playerPfid, unix):
    channel = client.get_channel(1515072853022736456)
    if channel:
        if playerXuid not in _state.verifyData:
            return
        discord_id = _state.verifyData[playerXuid]
        catchMissingFriendData(discord_id)
        if _state.friends[discord_id]["friends"]:
            friendListRaw = _state.friends[discord_id]["friends"]
            friendPings = ""
            allowedPings = []
            for i in friendListRaw:
                cooldowns = _state.friends[i]["settings"].get("ping_cooldowns", {})
                cooldown = cooldowns.get(discord_id)
                if cooldown:
                    if (
                        int(time.time())
                        - _state.friends[discord_id].get("last_join", 0)
                        > cooldown
                    ):
                        friendPings += f"<@{i}>\n"
                        allowedPings.append(discord.Object(int(i)))
                else:
                    friendPings += f"<@{i}>\n"
                    allowedPings.append(discord.Object(int(i)))

            if friendPings:
                await channel.send(
                    f"<@{discord_id}> is online!\n" + friendPings,
                    allowed_mentions=discord.AllowedMentions(users=allowedPings),
                )
            _state.friends[discord_id]["last_join"] = int(time.time())


# _/‾\_#_/‾\_#_/‾\_#_/‾\_#


@client.event
async def on_ready():
    global bot_loop
    bot_loop = asyncio.get_running_loop()
    synced = await tree.sync(guild=discord.Object(id=1240097763480309840))

    print(f"Logged in as {client.user}")


# _/‾\_#_/‾\_#_/‾\_#_/‾\_# basic commands


@tree.command(
    name="players",
    description="List online players",
    guild=discord.Object(id=1240097763480309840),
)
async def players(interaction: discord.Interaction):
    modifiedPlayerList = _state.players.copy()
    if _state.mainConfig["HerobrineSettings"]["doHerobrinePlayers"]:
        if (
            random.randint(1, _state.mainConfig["HerobrineSettings"]["HerobrineChance"])
            == 1
        ):
            modifiedPlayerList.append("Herobrine")
    modifiedPlayerList2 = []
    for playerName in modifiedPlayerList:
        if playerName in _state.afk_players:
            modifiedPlayerList2.append(f"{playerName} (afk)")
        else:
            modifiedPlayerList2.append(playerName)
    if modifiedPlayerList2:
        await interaction.response.send_message(
            "**Online:** " + ", ".join(modifiedPlayerList2)
        )
    else:
        await interaction.response.send_message("No players online.")


@tree.command(
    name="mccommand",
    description="Allows ADMINS to send commands to the server",
    guild=discord.Object(id=1240097763480309840),
)
async def sendcommand(interaction: discord.Interaction, message: str):
    if interaction.user.guild_permissions.administrator:
        with open(_state.logFile, "r") as file:
            commun.sendTmuxCommand("mcserver", message)
            file.seek(0, 2)
            await asyncio.sleep(0.1)
            line = file.readline()
            if line == "":
                await interaction.response.send_message(
                    "Sent without a response fron the server. Was probably fine."
                )
            else:
                await interaction.response.send_message(line)
    else:
        await interaction.response.send_message(
            "You're not an admin. Why would you even try?"
        )


# _/‾\_#_/‾\_#_/‾\_#_/‾\_# Verification


class verifyModal(discord.ui.Modal, title="Verification"):
    # This creates a single text field in the pop-up
    verifyCodeEntered = discord.ui.TextInput(
        label="Verification Code",
        placeholder="Put the verification code you recieved in minecraft here",
        required=True,
    )

    def __init__(self, minecraft_username: str):
        super().__init__()
        self.minecraft_username = minecraft_username
        verifyCodes[minecraft_username] = str(random.randint(100000, 999999))
        code = verifyCodes[minecraft_username]
        commun.sendTmuxCommand(
            "mcserver",
            f'tellraw "{minecraft_username}" {{"rawtext":[{{"text":"Your discord verification code is {code}"}}]}}',
        )

    async def on_submit(self, interaction: discord.Interaction):
        if verifyCodes[self.minecraft_username] == self.verifyCodeEntered.value:
            do_verify(
                str(interaction.user.id), str(_state.xuids[self.minecraft_username])
            )
            await interaction.response.send_message(
                f"Verification Succesful", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Verification Unsuccesful", ephemeral=True
            )


def do_verify(dcid, xuid):

    _state.verifyData[str(dcid)] = xuid
    _state.verifyData[xuid] = str(str(dcid))

    with open("data/verifyData.json", "w") as file:
        json.dump(_state.verifyData, file, indent=2)

    # form permissions.json
    _state.permissions = [p for p in _state.permissions if p["xuid"] != xuid]
    _state.permissions.append({"permission": "member", "xuid": xuid})
    with open("bedrock-server/permissions.json", "w") as permissionFile:
        json.dump(_state.permissions, permissionFile, indent=2)

    commun.sendTmuxCommand("mcserver", "permission reload")


class verifyButton(discord.ui.View):
    def __init__(self, minecraft_username: str):
        super().__init__()
        self.minecraft_username = minecraft_username

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.blurple)
    async def button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if str(interaction.user.id) in _state.verifyData:
            await interaction.response.send_message(
                f"You are already verified as {_state.xuid2players[_state.verifyData[str(interaction.user.id)]]}",
                ephemeral=True,
            )
        elif self.minecraft_username not in _state.players:
            await interaction.response.send_message(
                "Log into the server to verify", ephemeral=True
            )
        elif self.minecraft_username not in _state.xuids:
            await interaction.response.send_message(
                "Something went wrong - please leave the server and rejoin",
                ephemeral=True,
            )
        elif _state.xuids[self.minecraft_username] in _state.verifyData:
            await interaction.response.send_message(
                "That Minecraft account is already verified", ephemeral=True
            )
        else:
            await interaction.response.send_modal(verifyModal(self.minecraft_username))


@tree.command(
    name="verify",
    description="Link your discord account to your minecraft account and be verified",
    guild=discord.Object(id=1240097763480309840),
)
async def verify(interaction: discord.Interaction, minecraft_username: str):
    view = verifyButton(minecraft_username)
    if (
        minecraft_username in _state.xuids
        and _state.xuids[minecraft_username] in _state.verifyData
    ):
        await interaction.response.send_message("You are already verified")
    else:
        await interaction.response.send_message(
            f"Click to verify as {minecraft_username}\nMake sure you're in the minecraft server - it will send you a private chat with a code",
            view=view,
            ephemeral=True,
        )


@tree.command(
    name="unverify",
    description="Unlinks your discord account from your Minecraft account and sets you to visitor",
    guild=discord.Object(id=1240097763480309840),
)
async def unverify(interaction: discord.Interaction):
    if str(interaction.user.id) not in _state.verifyData:
        await interaction.response.send_message("You are not verified.", ephemeral=True)
        return
    _state.permissions = [
        p
        for p in _state.permissions
        if p["xuid"] != _state.verifyData[str(interaction.user.id)]
    ]
    _state.permissions.append(
        {"permission": "visitor", "xuid": _state.verifyData[str(interaction.user.id)]}
    )
    with open("bedrock-server/permissions.json", "w") as permissionFile:
        json.dump(_state.permissions, permissionFile, indent=2)

    del _state.verifyData[_state.verifyData[str(interaction.user.id)]]
    del _state.verifyData[str(interaction.user.id)]
    await interaction.response.send_message(
        f"You are no longer verified as <@{interaction.user.id}>"
    )

    with open("data/verifyData.json", "w") as file:
        json.dump(_state.verifyData, file, indent=2)

    commun.sendTmuxCommand("mcserver", "permission reload")


# _/‾\_#_/‾\_#_/‾\_#_/‾\_# friends

friend_group = app_commands.Group(
    name="friend", description="Friend system - must be verified to use."
)


def catchMissingSettingData(id):
    if not id in _state.userSettings:
        _state.userSettings[id] = {}


@friend_group.command(name="ping", description="pings all of your friends")
async def invokableFriendPing(interaction: discord.Interaction):
    if str(interaction.user.id) in _state.verifyData:
        catchMissingFriendData(str(interaction.user.id))
        if _state.friends[str(interaction.user.id)]["friends"]:
            friendPings = ""
            for i in _state.friends[str(interaction.user.id)]["friends"]:
                friendPings += f"<@{i}>\n"
            await interaction.response.send_message(friendPings)
    else:
        await interaction.response.send_message("You must be verified to have friends.")


@friend_group.command(
    name="pingcooldown", description="changes the cooldown between friend pings"
)
async def ping_cooldown(
    interaction: discord.Interaction,
    target: discord.Member,
    hours: Optional[int],
    minutes: Optional[int],
    seconds: Optional[int],
):
    if not (hours or minutes or seconds):
        await interaction.response.send_message("You must specify a time")
        return
    else:
        catchMissingFriendData(str(interaction.user.id))
        catchMissingFriendData(str(target.id))
        _state.friends[str(interaction.user.id)]["settings"].setdefault(
            "ping_cooldowns", {}
        )
        _state.friends[str(interaction.user.id)]["settings"]["ping_cooldowns"][
            str(target.id)
        ] = (((hours or 0) * 3600) + ((minutes or 0) * 60) + (seconds or 0))
        await interaction.response.send_message(
            f"Set <@{target.id}>'s ping cooldown to {((hours or 0)*3600) + ((minutes or 0)*60) + (seconds or 0)} seconds",
            ephemeral=True,
        )
        writeFriendData()


@friend_group.command(
    name="request", description="Requests to add someone to your friends list"
)
async def friend_add(interaction: discord.Interaction, recipient: discord.Member):
    if str(recipient.id) in _state.verifyData:
        if str(interaction.user.id) in _state.verifyData:
            catchMissingFriendData(str(interaction.user.id))
            catchMissingFriendData(str(recipient.id))
            if str(interaction.user.id) == str(recipient.id):
                await interaction.response.send_message(
                    "You cannot friend yourself (anymore)"
                )
            else:
                if (
                    str(recipient.id)
                    in _state.friends[str(interaction.user.id)]["friends"]
                ):
                    await interaction.response.send_message("You are already friends")
                else:
                    _state.friends[str(interaction.user.id)]["outgoing"].append(
                        str(recipient.id)
                    )
                    _state.friends[str(recipient.id)]["incoming"].append(
                        str(interaction.user.id)
                    )
                    await interaction.response.send_message(
                        f"<@{str(recipient.id)}>, <@{str(interaction.user.id)}> would like to be your friend. Run `/friend accept` to accept it!"
                    )
                    writeFriendData()
        else:
            await interaction.response.send_message(
                "Please run `/verify` before sending friend requests."
            )
    else:
        await interaction.response.send_message(
            "User is not verified! Have them run `/verify` to add them as a friend."
        )


@friend_group.command(
    name="accept",
    description="Accepts someone's friend request, pinging you whenever they come online",
)
async def friend_accept(interaction: discord.Interaction, from_user: discord.Member):
    catchMissingFriendData(str(interaction.user.id))
    if str(from_user.id) in _state.friends[str(interaction.user.id)]["incoming"]:
        if str(interaction.user.id) in _state.verifyData:
            _state.friends[str(interaction.user.id)]["incoming"].remove(
                str(from_user.id)
            )
            _state.friends[str(from_user.id)]["outgoing"].remove(
                str(interaction.user.id)
            )
            _state.friends[str(from_user.id)]["friends"].append(
                str(interaction.user.id)
            )
            _state.friends[str(interaction.user.id)]["friends"].append(
                str(from_user.id)
            )
            await interaction.response.send_message(
                f"<@{from_user.id}>, <@{interaction.user.id}> has accepted your friend request."
            )
            writeFriendData()
        else:
            await interaction.response.send_message(
                "Somehow, you recieved a request while unverified. This should not happen."
            )
    else:
        await interaction.response.send_message(
            "That user has not sent you a friend request."
        )


@friend_group.command(name="list", description="Lists friends.")
async def friend_list(interaction: discord.Interaction):
    catchMissingFriendData(str(interaction.user.id))
    if str(interaction.user.id) in _state.verifyData:
        if _state.friends[str(interaction.user.id)]["friends"]:
            friendListRaw = _state.friends[str(interaction.user.id)]["friends"]
            friendList = "Your friends are\n"
            for friend_id in friendListRaw:
                friendList += f" - <@{friend_id}>\n"
            await interaction.response.send_message(
                friendList,
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        else:
            await interaction.response.send_message("You have no friends.")
    else:
        await interaction.response.send_message("You must be verified to have friends.")


@friend_group.command(name="remove", description="Unfriesnds someone.")
async def friend_remove(interaction: discord.Interaction, user: discord.Member):
    catchMissingFriendData(str(interaction.user.id))
    if _state.friends[str(interaction.user.id)]:
        if str(user.id) in _state.friends[str(interaction.user.id)]["friends"]:
            _state.friends[str(interaction.user.id)]["friends"].remove(str(user.id))
            _state.friends[str(user.id)]["friends"].remove(str(interaction.user.id))
            await interaction.response.send_message(
                "You are no longer friends.", ephemeral=True
            )
            writeFriendData()
        else:
            await interaction.response.send_message(
                "You are not friends with them. Why so hostile?"
            )
    else:
        await interaction.response.send_message("You have no friends.")


tree.add_command(friend_group, guild=discord.Object(id=1240097763480309840))

# _/‾\_#_/‾\_#_/‾\_#_/‾\_# admin-jun. mod commands (should prob be renamed)

force_group = app_commands.Group(name="force", description="admin commands")


@force_group.command(name="backup", description="Forces a restic backup")
async def force_backup(interaction: discord.Interaction):
    if admin_only(interaction):
        await interaction.response.send_message(
            "ran command. yes this is a lazy response. I do not care."
        )
        backup.backupScript()


@force_group.command(name="verify", description="Forcibly links two accounts")
async def force_verify(
    interaction: discord.Interaction, xuid: int, discord_user: discord.Member
):
    if not (
        interaction.user.guild_permissions.administrator
        or any(role.id == 1457323549986521088 for role in interaction.user.roles)
    ):
        await interaction.response.send_message(
            "You must be <@&1240133433045286974> or <@&1457323549986521088> for that command."
        )
    else:
        do_verify(str(discord_user.id), str(xuid))
        await interaction.response.send_message("verified")


@force_group.command(
    name="restart", description="Restarts the server. Takes 15 seconds."
)
async def restart(interaction: discord.Interaction):
    if not (
        interaction.user.guild_permissions.administrator
        or any(role.id == 1457323549986521088 for role in interaction.user.roles)
    ):
        await interaction.response.send_message(
            "You must be <@&1240133433045286974> or <@&1457323549986521088> for that command."
        )
    else:
        await interaction.response.send_message("restarting...")
        commun.sendTmuxCommand("mcserver", "stop")
        await asyncio.sleep(15)
        commun.sendTmuxCommand(
            "mcserver",
            "./bedrock_server 2>&1 | tee -a server.log",
        )


@force_group.command(name="test", description="Runs whatever test snow decide to setup")
async def test(interaction: discord.Interaction, addplayer: int):
    if await admin_only(interaction):
        await interaction.response.send_message("done", ephemeral=True)  # must respond within 3s
        r = subprocess.run(
        ["restic", "--json", "-r", _state.mainConfig["backupSettings"]["backupDir"],
         "--insecure-no-password", "stats", "--mode", "raw-data"],
        capture_output=True, text=True,
        )
        
        await interaction.channel.send(str(r.stdout))
        
    

@force_group.command(name="sleeppercentage", description="sets the player sleep percentage. Afk players will not count towards the sleep percentage")
async def sleeppercentage(interaction: discord.Interaction, percentage: int):
    if await admin_only(interaction):
        _state.mainConfig["playerSleepingPercentage"] = percentage
        _state.write_settings()
        commun.sendTmuxCommand("mcserver",f"gamerule playersSleepingPercentage {str(percentage)}")
        await interaction.response.send_message(
            f"Sleep Percentage set to {percentage}"
        )



tree.add_command(force_group, guild=discord.Object(id=1240097763480309840))

# _/‾\_#_/‾\_#_/‾\_#_/‾\_# geofencing

geofence_group = app_commands.Group(
    name="geofence", description="commands to notify when players go beyond limits"
)


@geofence_group.command(
    name="add", description="Allows you to opt in and out of the locator bar"
)
async def geofence_add(
    interaction: discord.Interaction,
    name: str,
    x: int,
    z: int,
    distance: int,
    dimension: str = "overworld",
    inverted: bool = False,
    include_players: str = None,  # feels cleaner than Optional[str]
    exclude_players: str = None,
):
    if await admin_only(interaction):
        if not _state.mainConfig["playerTrackingSettings"]["doPlayerTracking"]:
            await interaction.response.send_message(
                "You must have playerTrackingSettings.doPlayerTracking enabled in the config to use geofencing.",
                ephemeral=True,
            )

        else:
            response = "GeoFence added."
            geofence_snippet = {
                "x": x,
                "z": z,
                "distance": distance,
                "dimension": dimension,
                "inverted": inverted,
                "included": [],
                "excluded": [],
            }
            if include_players:
                modified_inclusion = (
                    include_players.strip().replace(" ", "").split("><")
                )
                for id in modified_inclusion:
                    modified_id = id.replace("<", "").replace(">", "").replace("@", "")
                    try:
                        geofence_snippet["included"].append(
                            _state.verifyData[modified_id]
                        )
                    except TypeError:
                        pass
                    except KeyError:
                        response += f"\n<@{modified_id}> is not verified. Geofence was created anyways."
                    except:
                        pass
            if exclude_players:
                modified_exclusion = (
                    exclude_players.strip().replace(" ", "").split("><")
                )
                for id in modified_exclusion:
                    modified_id = id.replace("<", "").replace(">", "").replace("@", "")
                    try:
                        geofence_snippet["excluded"].append(
                            _state.verifyData[modified_id]
                        )
                    except TypeError:
                        pass
                    except KeyError:
                        response += f"\n<@{modified_id}> is not verified. Geofence was created anyways."
                    except:
                        pass

            _state.geoFences[name] = geofence_snippet
            await interaction.response.send_message(
                response,
                ephemeral=True,
            )
            fencing.write_geofences()


@geofence_group.command(name="list", description="lists currently active geofences.")
async def geofence_list(
    interaction: discord.Interaction,
):
    if await admin_only(interaction):
        message = "Currently Active GeoFences:"
        for name in _state.geoFences:
            message += f"\n{name}"
        await interaction.response.send_message(
            message,
            ephemeral=True,
        )


@geofence_group.command(name="remove", description="removes a geofence.")
async def geofence_remove(
    interaction: discord.Interaction,
    name: str,
):
    if await admin_only(interaction):
        try:
            _state.geoFences.pop(name)
            fencing.write_geofences()
            await interaction.response.send_message(
                f"GeoFence {name} removed.",
                ephemeral=True,
            )

        except KeyError:
            await interaction.response.send_message(
                f"GeoFence {name} was not found. Run `geofence list` to see active geoFences.",
                ephemeral=True,
            )


@geofence_group.command(name="info", description="lists geofence settings")
async def geofence_info(
    interaction: discord.Interaction,
    name: str,
):
    try:
        response = f"Geofence {name}:"
        response += f"\nX: {_state.geoFences[name]["x"]}"
        response += f"\nZ: {_state.geoFences[name]["z"]}"
        response += f"\nDistance: {_state.geoFences[name]["distance"]}"
        response += f"\nDimension: {_state.geoFences[name]["dimension"]}"
        response += f"\nInverted?: {_state.geoFences[name]["inverted"]}"
        included = ""
        for player in _state.geoFences[name]["included"]:
            included += f"<@{_state.verifyData[player]}>"
        response += f"\nIncluded Players: {included}"
        excluded = ""
        for player in _state.geoFences[name]["excluded"]:
            excluded += f"<@{_state.verifyData[player]}>"
        response += f"\nExcluded Players: {excluded}"

        await interaction.response.send_message(
            response,
            ephemeral=True,
        )

    except KeyError:
        await interaction.response.send_message(
            f"GeoFence {name} was not found. Run `geofence list` to see active geoFences.",
            ephemeral=True,
        )


@geofence_group.command(
    name="include_players",
    description="adds a player to be tracked with geofences. Not required.",
)
async def geofence_player_add(
    interaction: discord.Interaction, name: str, include_players: str, remove: bool=False
):
    if _state.geoFences[name]:
        response = "Included players."
        modified_inclusion = include_players.strip().replace(" ", "").split("><")
        for id in modified_inclusion:
            modified_id = id.replace("<", "").replace(">", "").replace("@", "")
            try:
                if remove:
                    _state.geoFences[name]["included"].remove(
                                            _state.verifyData[modified_id]
                                        )
                else:
                    _state.geoFences[name]["included"].append(
                        _state.verifyData[modified_id]
                    )
            except TypeError:
                pass
            except KeyError:
                response += (
                    f"\n<@{modified_id}> is not verified. Everything else was added."
                )
            except:
                pass
        await interaction.response.send_message(
            response,
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            f"GeoFence {name} was not found. Run `geofence list` to see active geoFences.",
            ephemeral=True,
        )


@geofence_group.command(
    name="exclude_players",
    description="adds a player to be tracked with geofences. Not required.",
)
async def geofence_player_exclude(
    interaction: discord.Interaction, name: str, exclude_players: str, remove: bool=False
):
    if _state.geoFences[name]:
        response = "Added players."
        modified_inclusion = exclude_players.strip().replace(" ", "").split("><")
        for id in modified_inclusion:
            modified_id = id.replace("<", "").replace(">", "").replace("@", "")
            try:
                if remove:
                    _state.geoFences[name]["excluded"].remove(
                        _state.verifyData[modified_id]
                    )
                else:
                    _state.geoFences[name]["excluded"].append(
                        _state.verifyData[modified_id]
                    )
            except TypeError:
                pass
            except KeyError:
                response += (
                    f"\n<@{modified_id}> is not verified. Everything else was added."
                )
            except:
                pass
        await interaction.response.send_message(
            response,
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            f"GeoFence {name} was not found. Run `geofence list` to see active geoFences.",
            ephemeral=True,
        )


tree.add_command(geofence_group, guild=discord.Object(id=1240097763480309840))

# _/‾\_#_/‾\_#_/‾\_#_/‾\_# misc

toggle_group = app_commands.Group(name="toggle", description="toggles certain things on and off")

@toggle_group.command(
    name="afk", description="Allows you to set yourself as afk"
)
async def toggle_afk(interaction: discord.Interaction):
    discord_id = str(interaction.user.id)
    if discord_id not in _state.verifyData:
        await interaction.response.send_message("Not Verified. Run `/verify`", ephemeral=True)
        return
    xuid = _state.verifyData[discord_id]
    name = _state.xuid2players.get(xuid)
    if name not in _state.players:
        await interaction.response.send_message("You must be online.", ephemeral=True)
        return

    manual = _state.afk_players[0]["exdata"]["manually_toggled"]
    if xuid in manual:
        _state.posData.get(name, {}).pop("afk_since", None)
        manual.remove(xuid)
        if name in _state.afk_players:
            _state.afk_players.remove(name)
        msg = "You are no longer AFK."
    else:
        manual.append(xuid)
        if name not in _state.afk_players:
            _state.afk_players.append(name)
        msg = "You are now AFK."
    sleep.update_sleep_per()
    await interaction.response.send_message(msg, ephemeral=True)

vote_group = app_commands.Group(name="vote", description="vote for things")


@vote_group.command(name="kick_afk", description="vote to kick an afk player")
async def vote_kick_afk(interaction: discord.Interaction, player: discord.Member):
    voter = str(interaction.user.id)
    if voter not in _state.verifyData or str(player.id) not in _state.verifyData:
        await interaction.response.send_message("Both of you must be verified.", ephemeral=True)
        return
    name = _state.xuid2players[_state.verifyData[str(player.id)]]
    if name not in _state.players or name not in _state.afk_players:
        await interaction.response.send_message(f"{name} isn't afk.", ephemeral=True)
        return

    voters = _state.kick_data.setdefault(name, set())
    if voter in voters:
        await interaction.response.send_message("You already voted.", ephemeral=True)
        return
    voters.add(voter)

    afk = len([p for p in _state.afk_players if p in _state.players])
    total = max(len(_state.players) - afk, 1)
    votes = len(voters)

    if votes / total >= 0.5:
        commun.sendTmuxCommand("mcserver", f"kick {name}")
        _state.kick_data.pop(name, None)
        await interaction.response.send_message(f"{name} was kicked")
    else:
        msg = f"People are voting to kick {name}! {votes}/{total} so far!"
        commun.sendTmuxCommand("mcserver", f"say {msg}")
        await interaction.response.send_message(msg)

    

@toggle_group.command(
    name="locatorbar", description="Allows you to opt in and out of the locator bar"
)
async def locatorbar(interaction: discord.Interaction):
    if str(interaction.user.id) in _state.verifyData:
        catchMissingSettingData(str(interaction.user.id))
        _state.userSettings[str(interaction.user.id)].setdefault("locatorbar", True)
        if _state.userSettings[str(interaction.user.id)]["locatorbar"]:
            _state.userSettings[str(interaction.user.id)]["locatorbar"] = False
            await interaction.response.send_message(
                "Locator bar will be turn **off** when you're online."
            )
            if _state.isDcidOnline(str(interaction.user.id)):
                _state.playersWithoutBar.append(
                    _state.verifyData[str(interaction.user.id)]
                )
                commun.sendTmuxCommand("mcserver", "gamerule playerwaypoints off")
        else:
            _state.userSettings[str(interaction.user.id)]["locatorbar"] = True
            await interaction.response.send_message(
                "Locator bar will stay **on** when you're online."
            )
            if _state.isDcidOnline(str(interaction.user.id)):
                _state.playersWithoutBar.remove(
                    _state.verifyData[str(interaction.user.id)]
                )
                if not _state.playersWithoutBar:
                    commun.sendTmuxCommand(
                        "mcserver", "gamerule playerwaypoints everyone"
                    )
        writeSettingsData()

    else:
        await interaction.response.send_message("Not Verified. Run `/verify`")


tree.add_command(toggle_group, guild=discord.Object(id=1240097763480309840))
tree.add_command(vote_group, guild=discord.Object(id=1240097763480309840))



@tree.command(
    name="reloadconf",
    description="reload's the bot's config files, may cause bugs",
    guild=discord.Object(id=1240097763480309840),
)
async def reloadconf(interaction: discord.Interaction):
    if await admin_only(interaction):
        with open("config.json", "r") as config_file:
            _state.mainConfig = json.load(config_file)
        await interaction.response.send_message("config reloaded")


# _/‾\_#_/‾\_#_/‾\_#_/‾\_#


def post_message(channel_id, content):
    if bot_loop:
        channel = client.get_channel(channel_id)
        if channel:
            asyncio.run_coroutine_threadsafe(channel.send(content), bot_loop)


def run_bot():
    try:
        client.run(_state.env["discord_token"])
    except Exception as e:
        print(f"Discord bot failed to start: {e}")
