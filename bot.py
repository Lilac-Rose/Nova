import os
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv
import sys
from config import pronouns, status

load_dotenv()

SPARKLES_FILE = "sparkles.json"

# Function to load sparkles data
def load_sparkles():
    try:
        with open(SPARKLES_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sparkles = load_sparkles()  # Load sparkles data on startup

    def save_sparkles(self, sparkles):
        """Save the sparkles data to a JSON file."""
        with open(SPARKLES_FILE, "w") as f:
            json.dump(sparkles, f, indent=4)

    async def close(self):
        self.save_sparkles(self.sparkles)  # Save sparkles data on shutdown
        await super().close()

bot = MyBot(command_prefix="!", intents=intents)

async def load_extensions(bot, folder):
    for filename in os.listdir(f"./{folder}"):
        if filename.endswith(".py") and filename != "__init__.py":
            try:
                await bot.load_extension(f"{folder}.{filename[:-3]}")
                print(f"Successfully loaded {folder}.{filename[:-3]}")
            except Exception as e:
                print(f"Failed to load {folder}.{filename[:-3]}: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await load_extensions(bot, "commands")
    await load_extensions(bot, "events")
    await load_extensions(bot, "tasks")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{status} | Pronouns: {pronouns}"
        ),
        status=discord.Status.online
    )
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

token = os.getenv('TOKEN')
if not token:
    print("Error: The 'TOKEN' environment variable is not set.")
    sys.exit(1)

bot.run(token)