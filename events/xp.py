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
                    return True
                
                await cur.execute(
                    """INSERT OR REPLACE INTO cooldowns 
                    VALUES (?, ?)""",
                    (str(user_id), current_time))
                await conn.commit()
                return False

    async def _grant_level_up_rewards(self, conn, user_id: str, new_level: int):
        """Grant coins and update ranks when leveling up"""
        async with conn.cursor() as cur:
            # Grant bonus coins (100 per level)
            bonus = 100 * new_level
            await cur.execute(
                """INSERT INTO user_coins (user_id, coins)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                coins = coins + excluded.coins""",
                (user_id, bonus))
            
            # Update level ranks via RankSystem cog
            if rank_cog := self.bot.get_cog("RankSystem"):
                await cur.execute(
                    "SELECT xp FROM user_xp WHERE user_id = ?",
                    (user_id,))
                xp = (await cur.fetchone())[0]
                await rank_cog._ensure_level_ranks(user_id, xp)
            
            await conn.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        if await self.check_cooldown(message.author.id):
            return
            
        try:
            async with await get_connection() as conn:
                new_xp, leveled_up = await add_xp(
                    conn,
                    str(message.author.id),
                    str(message.guild.id))
                
                if leveled_up:
                    level = calculate_level(new_xp)[0]
                    await self._grant_level_up_rewards(conn, str(message.author.id), level)
                    
                    # Optional level up notification
                    channel = message.channel
                    try:
                        await channel.send(
                            f"🎉 {message.author.mention} leveled up to **level {level}**!",
                            delete_after=10)
                    except discord.Forbidden:
                        pass
                    
        except Exception as e:
            await self.bot.logger.log(
                f"XP error: {type(e).__name__}: {str(e)}",
                level="error")

async def setup(bot):
    await bot.add_cog(XPTracker(bot))