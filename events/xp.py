# events/xp.py
import discord
from discord.ext import commands
from utils.xp import add_xp, calculate_level

class XPTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        try:
            new_level, leveled_up = await add_xp(
                self.bot.db,
                str(message.author.id),
                str(message.guild.id)
            )
            
            if leveled_up:
                await message.channel.send(
                    f"🎉 {message.author.mention} reached level {new_level}!",
                    delete_after=10
                )
                
        except Exception as e:
            await self.bot.logger.log(
                f"XP error: {type(e).__name__}: {str(e)}",
                level="error"
            )

async def setup(bot):
    await bot.add_cog(XPTracker(bot))