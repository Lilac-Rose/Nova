import random
import re
import discord
import json
from pathlib import Path

SPARKLES_FILE = Path("json/sparkles.json")

def load_sparkles():
    """Load the sparkles data from the JSON file."""
    if SPARKLES_FILE.exists():
        with open(SPARKLES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_sparkles(sparkles):
    """Save the sparkles data to the JSON file."""
    # Ensure the "json" directory exists
    SPARKLES_FILE.parent.mkdir(exist_ok=True)
    with open(SPARKLES_FILE, "w") as f:
        json.dump(sparkles, f, indent=4)

async def on_message(message: discord.Message):
    """
    Handles the on_message event for sparkle reactions and :boom: reactions
    """
    # Ignore messages from the bot itself and other bots
    if message.author.bot:
        return

    # Load sparkles data from the JSON file
    sparkles = load_sparkles()

    # Initialize server data if it doesn't exist
    server_id = str(message.guild.id)
    if server_id not in sparkles:
        sparkles[server_id] = {}
    if str(message.author.id) not in sparkles[server_id]:
        sparkles[server_id][str(message.author.id)] = {"epic": 0, "rare": 0, "regular": 0}

    if re.search("Nova", message.content, re.IGNORECASE):
        await message.reply(f"You called?") #Don't bother her fuckface

    # Check for "b" + 2 or more "o"s + "m" (case-insensitive)
    if re.search(r"\bb[o]{2,}m\b", message.content, re.IGNORECASE):
        await message.add_reaction("💥")

    chance = random.randint(1, 100000)

    # Check for epic sparkle reaction (1/100,000 chance)
    if chance == 1:
        await message.add_reaction("✨")
        await message.reply(f"**{message.author.name}** got an **epic sparkle**! ✨", mention_author=False)
        sparkles[server_id][str(message.author.id)]["epic"] += 1
        save_sparkles(sparkles)  # Save the updated data

    # Check for rare sparkle reaction (1/10,000 chance)
    elif chance <= 10:
        await message.add_reaction("🌟")
        await message.reply(f"**{message.author.name}** got a **rare sparkle**! 🌟", mention_author=False)
        sparkles[server_id][str(message.author.id)]["rare"] += 1
        save_sparkles(sparkles)  # Save the updated data

    # Check for regular sparkle reaction (1/1,000 chance)
    elif chance <= 100:
        await message.add_reaction("⭐")
        await message.reply(f"**{message.author.name}** got a **sparkle**! ⭐", mention_author=False)
        sparkles[server_id][str(message.author.id)]["regular"] += 1
        save_sparkles(sparkles)  # Save the updated data

async def setup(bot):
    """
    Registers the on_message event with the bot.
    """
    bot.add_listener(on_message, "on_message")