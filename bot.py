import os
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv  # Import the load_dotenv function
import sys

# Load environment variables from .env file
load_dotenv()

# Constants
SPARKLES_FILE = "sparkles.json"  # Path to your sparkles JSON file

# Function to load sparkles data
def load_sparkles():
    try:
        with open(SPARKLES_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Set up intents
intents = discord.Intents.default()
intents.message_content = True

# Set up the bot
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

# Function to load all extensions from a folder
async def load_extensions(bot, folder):
    for filename in os.listdir(f"./{folder}"):
        if filename.endswith(".py") and filename != "__init__.py":
            try:
                # Remove the .py extension and format the path for load_extension
                await bot.load_extension(f"{folder}.{filename[:-3]}")
                print(f"Successfully loaded {folder}.{filename[:-3]}")
            except Exception as e:
                print(f"Failed to load {folder}.{filename[:-3]}: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    # Load all commands, events, and tasks
    await load_extensions(bot, "commands")
    await load_extensions(bot, "events")
    await load_extensions(bot, "tasks")

    # Sync slash commands (if using discord.app_commands)
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

# Get the bot token from the environment variable
token = os.getenv('TOKEN')  # Use os.getenv to read the token
if not token:
    print("Error: The 'TOKEN' environment variable is not set.")
    sys.exit(1)  # Exit with a non-zero status code to indicate an error

# Run the bot
bot.run(token)