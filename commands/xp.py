import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from utils.xp import calculate_level, xp_for_next_level

class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_user_stats(self, server_id: str, user_id: str):
        """Get user's XP and coins in a single query"""
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute('''
                    SELECT ux.xp, uc.coins
                    FROM user_xp ux
                    LEFT JOIN user_coins uc ON ux.user_id = uc.user_id
                    WHERE ux.server_id = ? AND ux.user_id = ?
                ''', (server_id, user_id))
                result = await cur.fetchone()
                
                if not result:
                    # Initialize user if not found
                    await cur.execute('''
                        INSERT INTO user_xp (server_id, user_id, xp)
                        VALUES (?, ?, 0)
                    ''', (server_id, user_id))
                    await cur.execute('''
                        INSERT OR IGNORE INTO user_coins (user_id, coins)
                        VALUES (?, 0)
                    ''', (user_id,))
                    await conn.commit()
                    return (0, 0)
                
                return (result[0], result[1] if result[1] is not None else 0)

    @commands.hybrid_command(name="xp", description="Check your XP and level")
    @app_commands.describe(user="The user to check (optional)")
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
        embed.add_field(name="Nova Coins", value=f"{coins} 💰")
        embed.set_thumbnail(url=target.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(XP(bot))