import discord, typing, requests, os, asyncrcon
from discord import app_commands
from asyncrcon import AsyncRCON
from discord import app_commands
from discord.ext import commands, tasks
from extras import bot as bt
from extras import xuid

di = discord.Interaction

intents = discord.Intents.all()
intents.members = True
intents.guilds = True

client = discord.Client(intents=intents, help_command=None)
bot = app_commands.CommandTree(client)

AsyncRCON.__init__(AsyncRCON, bt.MC.ip, bt.MC.password, max_command_retries=1)
rcon = AsyncRCON(bt.MC.ip, bt.MC.password)
                            
@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game(name="RW CST Games!"))
    await rcon.open_connection()
    print("Ridgewater CST bot online!")
    
@bot.command(description="Lists the current Minecraft day")
async def day(i: di):
    output = await rcon.command(f"time query day")
    command = output.split(' ')
    day = command[-1]
    await i.response.send_message(f"The current day is {day}")
    
@bot.command(description="Adds you to the whitelist")
async def register(i: di, username: str, platform: typing.Literal['Java', 'Bedrock']):
    await i.response.defer()
    for user in i.channel.members:
        if (user.nick or user.name).lower() == (username.lower() or f".{username.lower()}"):
            await i.followup.send("That username is already registered. Contact an admin for assistance if this is incorrect.")
            return
    if platform == 'Bedrock':
        for user in i.channel.members:
            if (user.nick or user.name).lower() == f".{username.lower()}":
                await i.followup.send("That username is already registered. Contact an admin for assistance if this is incorrect.")
                return
        try:
            uuid, gamertag = xuid.get(target_gamertag = username)
            if uuid == None:
                await i.followup.send("That gamertag doesn't exist. Check your spelling.")
                return
        except:
            await i.followup.send("That gamertag doesn't exist. Check your spelling.")
            return
        username = f".{gamertag}"
        output = await rcon.command(f"fwhitelist add 00000000-0000-0000-000{uuid[0]}-{uuid[1:]}")
        if "unable to find any" in output:
            await i.followup.send("There was an issue adding your name. Check your spelling and try again, or message a moderator to help.")
            return
        else:
            pass
    else:
        for user in i.channel.members:
            if (user.nick or user.name).lower() == username.lower():
                await i.followup.send("That username is already registered. Contact an admin for assistance if this is incorrect.")
                return
        output = await rcon.command(f"whitelist add {username}")
        if "not exist" in output:
            await i.followup.send(f"There was an issue adding your name. Check your spelling and try again, or message a moderator to help.")
            return
        else:
            username = output.split(" ")[1]
    await i.guild.get_channel(bt.IDs.whitelist).send(f"Added `{username}` to the whitelist. Old name: {i.user.nick}")
    try:
        if i.user.nick[0] == ".":
            await rcon.command(f"fwhitelist remove {i.user.nick}")
        else:
            await rcon.command(f"whitelist remove {i.user.nick}")
    except:
        pass
    await i.user.edit(nick=username)
    await i.followup.send(f"You have been whitelisted and your Discord server nickname updated to match.\n`Username: {username}`")
    
@bot.command(description="Tests the Discord bot's response")
async def test(i: di):
    await bot.sync()
    await i.response.send_message(f"The bot is operational!")
    
client.run(bt.token)