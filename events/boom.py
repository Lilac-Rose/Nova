import discord
import re

async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if re.search(r"\bb[o]{2,}m\b", message.content, re.IGNORECASE):
        await message.add_reaction("💥")

async def setup(bot):
    bot.add_listener(on_message, "on_message")