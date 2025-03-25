import discord
from discord.ext import commands

async def on_message(message: discord.Message):
    if message.author.bot:
        return
    
    if message.guild and any(
        mention.id == message.guild.me.id
        for mention in message.mentions
    ):
        await message.reply("You called?")  # Don't bother her fuckface

async def setup(bot):
    bot.add_listener(on_message, "on_message")