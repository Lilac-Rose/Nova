import discord
import re

async def on_message(message: discord.Message):
    if message.author.bot:
        return
    
    if re.search("Nova", message.content, re.IGNORECASE):
        await message.reply(f"You called?") #Don't bother her fuckface