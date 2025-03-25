import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from utils.database import get_connection
from utils.xp import calculate_level, xp_for_next_level

class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_user_stats(self, server_id: str, user_id: str):
        try:
            async with await get_connection() as conn:
                async with conn.cursor() as cur:
                    # First try to get existing stats
                    await cur.execute('''
                        SELECT ux.xp, uc.coins
                        FROM user_xp ux
                        LEFT JOIN user_coins uc ON ux.user_id = uc.user_id
                        WHERE ux.server_id = ? AND ux.user_id = ?
                    ''', (server_id, user_id))
                    result = await cur.fetchone()
                    
                    if result is None:
                        # Initialize user stats if not found (using INSERT OR IGNORE)
                        await cur.execute('''
                            INSERT OR IGNORE INTO user_xp (server_id, user_id, xp)
                            VALUES (?, ?, 0)
                        ''', (server_id, user_id))
                        await cur.execute('''
                            INSERT OR IGNORE INTO user_coins (user_id, coins)
                            VALUES (?, 0)
                        ''', (user_id,))
                        await conn.commit()
                        return (0, 0)  # Default XP and coins
                    
                    return (result[0], result[1] if result[1] is not None else 0)
        except Exception as e:
            await self.bot.logger.log(
                f"Stats query failed: {str(e)}",
                level="error"
            )
            return (0, 0)  # Fallback values

    @commands.hybrid_command(name="stats", description="Check your stats! (Coins, XP, and level)")
    async def xp(self, ctx: commands.Context, user: Optional[discord.User] = None):
        target = user or ctx.author
        xp, coins = await self.get_user_stats(str(ctx.guild.id), str(target.id))
        
        level, current_xp = calculate_level(xp)
        next_level_xp = xp_for_next_level(level)
        progress = min(100, int((current_xp / next_level_xp) * 100)) if next_level_xp > 0 else 100
        
        embed = discord.Embed(
            title=f"{target.display_name}'s Stats",
            color=discord.Color.blue()
        )
        embed.add_field(name="Level", value=str(level))
        embed.add_field(name="XP Progress", value=f"{current_xp}/{next_level_xp} ({progress}%)")
        embed.add_field(name="Coins", value=f"{coins:,}")  # Added comma formatting
        embed.set_thumbnail(url=target.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(XP(bot))