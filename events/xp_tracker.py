import random
import time
import discord
from discord.ext import commands
from utils.database import get_connection
from utils.xp_utils import calculate_level, LEVEL_UP_BONUS, XP_PER_MESSAGE_MIN, XP_PER_MESSAGE_MAX

class XPTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_range = (XP_PER_MESSAGE_MIN, XP_PER_MESSAGE_MAX)  # Using your constants

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.content:
            return
        
        try:
            async with await get_connection() as conn:
                # Cooldown check
                async with conn.cursor() as cur:
                    await cur.execute(
                        "SELECT last_message_time FROM cooldowns WHERE user_id = ?",
                        (str(message.author.id),)
                    )
                    row = await cur.fetchone()
                    
                    current_time = time.time()
                    if row and current_time - row[0] < 10:
                        return
                    
                    await cur.execute(
                        "INSERT OR REPLACE INTO cooldowns VALUES (?, ?)",
                        (str(message.author.id), current_time)
                    )

                # XP and coins processing
                xp_gain = random.randint(*self.xp_range)
                server_id = str(message.guild.id)
                user_id = str(message.author.id)
                
                async with conn.cursor() as cur:
                    # Update XP
                    await cur.execute(
                        """INSERT INTO user_xp (server_id, user_id, xp)
                        VALUES (?, ?, ?)
                        ON CONFLICT(server_id, user_id) DO UPDATE SET
                        xp = xp + excluded.xp""",
                        (server_id, user_id, xp_gain)
                    )
                    
                    # Update coins
                    await cur.execute(
                        """INSERT INTO user_coins (user_id, coins)
                        VALUES (?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET
                        coins = coins + excluded.coins""",
                        (user_id, xp_gain)
                    )
                    
                    # Get new totals
                    await cur.execute(
                        "SELECT xp FROM user_xp WHERE server_id = ? AND user_id = ?",
                        (server_id, user_id)
                    )
                    new_xp = (await cur.fetchone())[0]
                
                # Check level up
                old_level = calculate_level(new_xp - xp_gain)[0]
                new_level = calculate_level(new_xp)[0]
                
                if new_level > old_level:
                    bonus = LEVEL_UP_BONUS * (new_level - old_level)  # Now using 100 per level
                    async with conn.cursor() as cur:
                        await cur.execute(
                            "UPDATE user_coins SET coins = coins + ? WHERE user_id = ?",
                            (bonus, user_id)
                        )
                    
                    await message.channel.send(
                        f"🎉 {message.author.mention} reached level {new_level}! (+{bonus} coins)",
                        delete_after=10
                    )
                
                await conn.commit()

        except Exception as e:
            await self.bot.logger.log(
                f"XP processing error: {str(e)}",
                level="error",
                alert=True
            )

async def setup(bot):
    await bot.add_cog(XPTracker(bot))