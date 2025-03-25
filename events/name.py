import discord
import random
from discord.ext import commands
from typing import Optional

async def on_mention(message: discord.Message) -> Optional[discord.Message]:
    """
    Responds when the bot is mentioned
    Returns the sent message if successful, None otherwise
    """
    if message.author.bot:
        return None
    
    if message.guild and any(mention.id == message.guild.me.id for mention in message.mentions):
        try:
            responses = [
                "You called?",
                "At your service!",
                "How can I help?",
                "Yes?",
                "I'm listening..."
            ]
            return await message.reply(random.choice(responses), 
                mention_author=False)
        except discord.HTTPException as e:
            print(f"Failed to respond to mention: {e}")
            return None
    return None

async def setup(bot: commands.Bot) -> None:
    """Add the mention listener to the bot"""
    bot.add_listener(on_mention, "on_message")