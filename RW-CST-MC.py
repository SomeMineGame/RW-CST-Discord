import discord, typing, random, requests, os, asyncrcon
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

# MINECRAFT
    
@bot.command(description="Lists the current Minecraft day")
async def day(i: di):
    output = await rcon.command(f"time query day")
    command = output.split(' ')
    day = command[-1]
    await i.response.send_message(f"The current day is {day}")
    
@bot.command(description="Get the IP of the server")
async def ip(i:di, platform: typing.Literal['Java', "Bedrock"]):
    if platform == "Java":
        await i.response.send_message("The IP is `rw-cst.someminegame.net`.", ephemeral=True)
    else:
        await i.response.send_message("The IP is `br-rw-cst.someminegame.net` with port `19135`.", ephemeral=True)
        
# MINECRAFT EXTRAS
    
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

# BOT

@bot.command(description="Tests the Discord bot's response")
async def test(i: di):
    await i.response.send_message(f"The bot is operational!")

@bot.command(description="Syncs the bot's command tree to Discord")
@commands.has_role("Bot Developer")
async def update_command_tree(i: di):
    await bot.sync()
    await i.response.send_message("Updated the command tree.", ephemeral=True)

# MISC
@bot.command(description="Flips a coim")
@commands.cooldown(1, 30, commands.cooldowns.BucketType.member)
async def coinflip(i:di):
    side = random.randint(1, 2)
    if side == 1:
        await i.response.send_message("You got heads!")
    else:
        await i.response.send_message("You got tails!")
        
@bot.command(description="Get the answer to a yes or no question")
async def magic8ball(i: di, message:str):
    responses = ['Maybe so, maybe not', 'I think so!', "I think not!", "Oh no! Not ***THAT** question!", 'Lol! What kind of question was that?', "Shut up! I'm tired.", "Joke's on you, it won't happen.", "Always", "Never", "Yeah", "IDK, YOU TELL *ME*", "No way!", 'Totally bro', 'Sorry but, no.', 'Absolutely', 'I hate my job because of that question', 'Repeat and try again in simpler terms', 'Error, response not clear.', 'You are a dimwit for asking that.', 'Why not', 'Sure', 'Uhhhh, no?', 'Uhhhh, yes?', 'How **DARE** you ask the beast of magic!', "Yes", "No", "Certainly", "That is uncertain", "It can happen", 'It can happen... NOT', 'Probably', 'Probably not', 'Repeat', "Goodbye, that response was stupid", '0% Chance', "25% Chance", '50% Chance', '75% Chance', '100% Chance', 'Absolutely not', 'You think ***I*** know the answer to that?']
    response = random.choice(responses)
    await i.response.send_message(response)
    
@bot.command(description="Rock Paper Scissors against the bot")
async def rps(i: di, choice: typing.Literal['Rock', 'Paper', 'Scissors']):
    botchoices = ["Rock", "Paper", "Scissors"]
    botoption = random.choice(botchoices)
    outcomes = ["Rock Scissors", "Paper Rock", "Scissors Paper"]
    if choice == botoption:
        await i.response.send_message(f"You both chose {choice}. Nobody won.")
    elif f"{botoption} {choice}" in outcomes:
        await i.response.send_message(f"You chose {choice} and the bot chose {botoption}. You lose.")
    elif f"{choice} {botoption}" in outcomes:
        await i.response.send_message(f"You chose {choice} and the bot chose {botoption}. You win!")
    else:
        await i.response.send_message(f'Developer error debug:\nPlayer={choice} Bot={botoption}')
      
@bot.command(description="Rock Paper Scissors Lizard Spock against the bot")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@commands.has_any_role("Sub $10")
async def rpsls(i: di, choice: typing.Literal["Rock", "Paper", "Scissors", "Lizard", "Spock"]):
    botoptions = ["Rock", "Paper", "Scissors", "Lizard", "Spock"]
    botoption = random.choice(botoptions)
    outcomes = ["Rock Scissors", "Rock Lizard", "Paper Rock", "Paper Spock", "Scissors Paper", "Scissors Lizard", "Lizard Paper", "Lizard Spock", "Spock Rock", "Spock Scissors"]
    if choice == botoption:
        await i.response.send_message(f"You both chose {choice}. Nobody won.")
    elif f"{botoption} {choice}" in outcomes:
        await i.response.send_message(f"You chose {choice} and the bot chose {botoption}. You lose.")
    elif f"{choice} {botoption}" in outcomes:
        await i.response.send_message(f"You chose {choice} and the bot chose {botoption}. You win!")
    else:
        await i.response.send_message(f'Developer error debug:\nPlayer={choice} Bot={botoption}')
    
client.run(bt.token)