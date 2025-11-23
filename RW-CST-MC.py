import discord, typing, random, requests, os, json
from discord import app_commands
from asyncrcon import AsyncRCON
from discord import app_commands
from discord.ext import commands, tasks
from extras import bot as bt
from extras import xuid

# Alias used in command arguments 
di = discord.Interaction

# Sets the Required Intents
intents = discord.Intents.all()
intents.members = True
intents.guilds = True

# Sets up the bot user
client = discord.Client(intents=intents, help_command=None)
bot = app_commands.CommandTree(client)

# Sets up the Minecraft RCON connection
AsyncRCON.__init__(AsyncRCON, bt.MC.ip, bt.MC.password, max_command_retries=1)
rcon = AsyncRCON(bt.MC.ip, bt.MC.password)

# Runs on launch
@client.event
async def on_ready():
    # Change Bot's user status
    await client.change_presence(status=discord.Status.online, activity=discord.Game(name="RW CST Games!"))
    # Opens connection to Minecraft RCON
    await rcon.open_connection()
    print("Ridgewater CST bot online!")


# +------------------+
# |MINECRAFT COMMANDS|
# +------------------+

@bot.command(description="Lists the current Minecraft day")
async def day(i: di):
    output = await rcon.command(f"time query day")
    # Separate Words Into List
    command = output.split(' ')
    # Last List Item Is The Day
    day = command[-1]
    await i.response.send_message(f"The current day is {day}")
    
@bot.command(description="Get the IP of the server")
async def ip(i:di, platform: typing.Literal['Java', "Bedrock"]):
    if platform == "Java":
        await i.response.send_message("The IP is `rw-cst.someminegame.net`.", ephemeral=True)
    else:
        await i.response.send_message("The IP is `br-rw-cst.someminegame.net` with port `19135`.", ephemeral=True)


# +----------------+
# |MINECRAFT EXTRAS|
# +----------------+
    
@bot.command(description="Adds you to the whitelist")
async def register(i: di, username: str, platform: typing.Literal['Java', 'Bedrock']):
    # Deferred As Command Can Otherwise Timeout
    await i.response.defer()
    if platform == 'Bedrock':
        # Check If Username Already Added
        for user in i.channel.members:
            if (user.nick or user.name).lower() == f".{username.lower()}":
                await i.followup.send("That username is already registered. Contact an admin for assistance if this is incorrect.")
                return
        try:
            # Receives The XUID And Gamertag, Returns None If Nonexistent
            # This Gamertag Has Proper Capitalization
            uuid, gamertag = xuid.get(target_gamertag = username)
            if uuid == None:
                await i.followup.send("That gamertag doesn't exist. Check your spelling.")
                return
        except Exception:
            await i.followup.send(f"There was an error checking your name. Send this to a bot dev.\n`{Exception}`", ephemeral=True)
            return
        # Floodgate Uses A Period Prefix For Bedrock Users
        username = f".{gamertag}"
        # Whitelists The XUID
        # XUID Used As A Username Is Only Available If A Player Has Joined The Geyser Network Previously
        output = await rcon.command(f"fwhitelist add 00000000-0000-0000-000{uuid[0]}-{uuid[1:]}")
        # If The Player Can't Be Found By Floodgate (Would Be Very Rare)
        if "unable to find any" in output:
            await i.followup.send("There was an issue adding your name. Check your spelling and try again, or message a moderator to help.")
            return
    else: # Java Player
        # Check If Username Already Added
        for user in i.channel.members:
            if (user.nick or user.name).lower() == username.lower():
                await i.followup.send("That username is already registered. Contact an admin for assistance if this is incorrect.")
                return
        # Attempts To Whitelist Player
        output = await rcon.command(f"whitelist add {username}")
        # If Username Doesn't Exist
        if "not exist" in output:
            await i.followup.send(f"There was an issue adding your name. Check your spelling and try again, or message a moderator to help.")
            return
        # If Username Does Exist
        else:
            # Splits Output And Grabs Username
            # This Username Has Proper Capitalization
            username = output.split(" ")[1]
    await i.guild.get_channel(bt.IDs.whitelist).send(f"Added `{username}` to the whitelist. Old name: {i.user.nick}")
    # Removed Old Username From Whitelist If Present
    # Prevents Players From Adding Friends
    try:
        if i.user.nick[0] == ".":
            await rcon.command(f"fwhitelist remove {i.user.nick}")
        else:
            await rcon.command(f"whitelist remove {i.user.nick}")
    except:
        pass
    # Changes The Player's Discord Nickname To Their Minecraft Username For Cross-Platform Chatting
    await i.user.edit(nick=username)
    await i.followup.send(f"You have been whitelisted and your Discord server nickname updated to match.\n`Username: {username}`")


# +--------------+
# |BOT MANAGEMENT|
# +--------------+

@bot.command(description="Tests the Discord bot's response")
async def test(i: di):
    await i.response.send_message(f"The bot is operational!")

@bot.command(description="Syncs the bot's command tree to Discord")
@commands.has_role("Bot Developer")
async def update_command_tree(i: di):
    await bot.sync()
    await i.response.send_message("Updated the command tree.", ephemeral=True)


# +-------------+
# |MISC COMMANDS|
# +-------------+

# Runs On Every Message Sent
# Used For A Counting Game In A Dedicated Channel
@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        # Stops Command If Bot Sent The Message
        return
    # Detects If Message Is In Counting Channel
    elif message.channel.name == "count-to-great-heights":
        # Loads Score Data
        with open(f"{os.getcwd}/data.json", 'r+') as f:
            data = json.load(f)
            f.close
        # Valid Ways To Request The High Score
        hs = ['highscore', 'high score', 'hs']
        # Detects If High Score Was Requested And Sends It
        if message.content.lower().strip() in hs:
            await message.channel.send(f"The current high score is: **{data['Counting']['Highscore']:,}**")
            return
        # Makes A List Of Every Word
        # Also Removes Commas So Numbers Like '1,000' Are '1000'
        parts = message.content.strip().replace(',', '').split()
        number = None
        # Finds The First Instance Of A Number
        # This Will Be The User Input
        for part in parts:
            try:
                Number = int(part)
                break
            except:
                pass
        # Quits Command If There Is No Number In Message
        if number == None:
            return
        # Detects If The Same User Has Sent Two Messages Containing Numbers In A Row
        elif message.author.id == data['Counting']['LastUser']:
            # Sets The Current Number And Last User To 0
            # Last User As 0 Means The Person That Killed The Streak Can Still Start The New One
            data['Counting']['Current'], data['Counting']['LastUser'] = 0, 0
            with open(f"{os.getcwd}/data.json", 'r+') as f:
                f.seek(0)
                json.dump(data, f)
                f.close()
            await message.add_reaction("❌")
            await message.channel.send(f"{message.author.mention} sent a number twice in a row! The challenge has been reset to 0. The current high score is **{data['Counting']['HighScore']:,}")
        # Detects If The Same Number Was Sent Two Messages In A Row
        elif number != number + 1:
            # Sets The Current Number And Last User To 0
            # Last User As 0 Means The Person That Killed The Streak Can Still Start The New One
            data['Counting']['Current'], data['Counting']['LastUser'] = 0, 0
            with open(f"{os.getcwd}/data.json", 'r+') as f:
                f.seek(0)
                json.dump(data, f)
                f.close()
            await message.add_reaction("❌")
            await message.channel.send(f"{message.author.mention} sent the wrong number! The challenge has been reset to 0. The current high score is **{data['Counting']['HighScore']:,}")
        # Number Is Valid
        else:
            # Gets Current High Score
            HighScore = data['Counting']['HighScore']
            # Sets The New High Score If Current Is Larger
            if number > data['Counting']['HighScore']:
                HighScore = number
            # Saves The Data
            data['Counting'] = {"Current": number, "HighScore": HighScore, "LastUser": message.author.id}
            with open(f"{os.getcwd}/data.json", 'r+') as f:
                f.seek(0)
                json.dump(data, f)
                f.close()
            await message.add_reaction("✅")

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
    responses = ["Maybe so, maybe not", "I think so!", "I think not!", "Oh no! Not ***THAT** question!", "Lol! What kind of question was that?", "Shut up! I'm tired.", "Joke's on you, it won't happen.", "Always", "Never", "Yeah", "IDK, YOU TELL *ME*", "No way!", "Totally bro", "Sorry but, no.", "Absolutely", "I hate my job because of that question", "Repeat and try again in simpler terms", "Error, response not clear.", "You are a dimwit for asking that.", "Why not", "Sure", "Uhhhh, no?", "Uhhhh, yes?", "How **DARE** you ask the beast of magic!", "Yes", "No", "Certainly", "That is uncertain", "It can happen", "It can happen... NOT", "Probably", "Probably not", "Repeat", "Goodbye, that response was stupid", "0% Chance", "25% Chance", "50% Chance", "75% Chance", "100% Chance", "Absolutely not", "You think ***I*** know the answer to that?"]
    response = random.choice(responses)
    await i.response.send_message(response)
    
@bot.command(description="Rock Paper Scissors against the bot")
async def rps(i: di, choice: typing.Literal['Rock', 'Paper', 'Scissors']):
    botchoices = ["Rock", "Paper", "Scissors"]
    botoption = random.choice(botchoices)
    # All Possible Wins
    # Setup as ["Win Lose", "Win Lose", ect]
    outcomes = ["Rock Scissors", "Paper Rock", "Scissors Paper"]
    # Choices Match
    if choice == botoption:
        await i.response.send_message(f"You both chose {choice}. Nobody won.")
    # Bot Wins
    elif f"{botoption} {choice}" in outcomes:
        await i.response.send_message(f"You chose {choice} and the bot chose {botoption}. You lose.")
    # Player Wins
    elif f"{choice} {botoption}" in outcomes:
        await i.response.send_message(f"You chose {choice} and the bot chose {botoption}. You win!")
    else:
        await i.response.send_message(f'Developer error debug:\nPlayer={choice} Bot={botoption}')
      
@bot.command(description="Rock Paper Scissors Lizard Spock against the bot")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def rpsls(i: di, choice: typing.Literal["Rock", "Paper", "Scissors", "Lizard", "Spock"]):
    botoptions = ["Rock", "Paper", "Scissors", "Lizard", "Spock"]
    botoption = random.choice(botoptions)
    # All Possible Wins
    # Setup as ["Win Lose", "Win Lose", ect]
    outcomes = ["Rock Scissors", "Rock Lizard", "Paper Rock", "Paper Spock", "Scissors Paper", "Scissors Lizard", "Lizard Paper", "Lizard Spock", "Spock Rock", "Spock Scissors"]
    # Choices Match
    if choice == botoption:
        await i.response.send_message(f"You both chose {choice}. Nobody won.")
    # Bot Wins
    elif f"{botoption} {choice}" in outcomes:
        await i.response.send_message(f"You chose {choice} and the bot chose {botoption}. You lose.")
    # Player Wins
    elif f"{choice} {botoption}" in outcomes:
        await i.response.send_message(f"You chose {choice} and the bot chose {botoption}. You win!")
    else:
        await i.response.send_message(f'Developer error debug:\nPlayer={choice} Bot={botoption}')

# Runs The Bot
client.run(bt.token)