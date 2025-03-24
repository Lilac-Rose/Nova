import os
import json
import discord
import sys
from discord.ext import commands
from dotenv import load_dotenv
from config import pronouns, status
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
load_dotenv()

SPARKLES_FILE = Path("json/sparkles.json")
XP_FILE = Path("json/xp.json")
COINS_FILE = Path("json/coins.json")

def load_json_data(file_path):
    try:
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("\nInitializing data storage...")
        self.sparkles = load_json_data(SPARKLES_FILE)
        self.xp_data = load_json_data(XP_FILE)
        self.coins_data = load_json_data(COINS_FILE)
        print(f"Loaded {len(self.xp_data)} servers and {len(self.coins_data)} users")

    def save_data(self, data, file_path):
        print(f"\nAttempting to save to {file_path}")
        try:
            file_path.parent.mkdir(exist_ok=True)
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
            print(f"Successfully saved data to {file_path}")
            print(f"Sample data: {dict(list(data.items())[:2])}")
        except Exception as e:
            print(f"ERROR saving {file_path}: {e}")

    async def close(self):
        self.save_data(self.sparkles, SPARKLES_FILE)
        self.save_data(self.xp_data, XP_FILE)
        self.save_data(self.coins_data, COINS_FILE)
        await super().close()

bot = MyBot(command_prefix="!", intents=intents)

async def load_extensions(bot, folder):
    print(f"\nLoading extensions from {folder}:")
    for filename in os.listdir(f"./{folder}"):
        if filename.endswith(".py") and filename != "__init__.py":
            ext_name = f"{folder}.{filename[:-3]}"
            try:
                print(f"Loading extension: {ext_name}")
                await bot.load_extension(ext_name)
                print(f"✓ Successfully loaded {ext_name}")
            except Exception as e:
                print(f"✗ Failed to load {ext_name}: {type(e).__name__}: {e}")

@bot.event
async def on_ready():
    print(f'\nLogged in as {bot.user.name} (ID: {bot.user.id})')
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
    
    print("\nSyncing commands...")
    try:
        synced = await bot.tree.sync()
        print(f"✓ Synced {len(synced)} commands:")
        for cmd in synced:
            print(f"- {cmd.name}")
    except Exception as e:
        print(f"✗ Command sync failed: {type(e).__name__}: {e}")

token = os.getenv('TOKEN')
if not token:
    print("Error: The 'TOKEN' environment variable is not set.")
    sys.exit(1)

bot.run(token)