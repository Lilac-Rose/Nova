import random
import discord
import json
from pathlib import Path

SPARKLES_FILE = Path("json/sparkles.json")

def load_sparkles():
    if SPARKLES_FILE.exists():
        with open(SPARKLES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_sparkles(sparkles):
    SPARKLES_FILE.parent.mkdir(exist_ok=True)
    with open(SPARKLES_FILE, "w") as f:
        json.dump(sparkles, f, indent=4)

async def on_message(message: discord.Message):
    if message.author.bot:
        return

    sparkles = load_sparkles()

    server_id = str(message.guild.id)
    if server_id not in sparkles:
        sparkles[server_id] = {}
    if str(message.author.id) not in sparkles[server_id]:
        sparkles[server_id][str(message.author.id)] = {"epic": 0, "rare": 0, "regular": 0}

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
    bot.add_listener(on_message, "on_message")