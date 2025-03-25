import time
import discord
from discord.ext import commands
from utils.database import get_connection
from utils.xp import add_xp, calculate_level

class XPTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown_seconds = 10  # 10 second cooldown

    async def check_cooldown(self, user_id: str) -> bool:
        """Check if user is on cooldown"""
        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT last_message_time FROM cooldowns WHERE user_id = ?",
                    (str(user_id),)
                )

                row = await cur.fetchone()
                current_time = time.time()
                
                if row and current_time - row[0] < self.cooldown_seconds:
                    return True  # On cooldown
                
                # Update cooldown
                await cur.execute(
                    """INSERT OR REPLACE INTO cooldowns 
                    VALUES (?, ?)""",
                    (str(user_id), current_time)
                )
                await conn.commit()
                return False  # Not on cooldown

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        # Check cooldown
        if await self.check_cooldown(message.author.id):
            return
            
        try:
            new_level, leveled_up = await add_xp(
                self.bot.db,
                str(message.author.id),
                str(message.guild.id)
            )
                
        except Exception as e:
            await self.bot.logger.log(
                f"XP error: {type(e).__name__}: {str(e)}",
                level="error"
            )

async def setup(bot):
    await bot.add_cog(XPTracker(bot))