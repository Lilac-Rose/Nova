import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from utils.database import get_connection
from utils.xp import calculate_level, xp_for_next_level

class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_user_data(self, server_id: str, user_id: str):
        """Safe database access with connection validation"""
        try:
            async with await get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute('''
                        SELECT xp FROM user_xp 
                        WHERE server_id = ? AND user_id = ?
                    ''', (server_id, user_id))
                    result = await cur.fetchone()
                    return result[0] if result else 0
        except Exception as e:
            await self.bot.logger.log(
                f"XP query failed: {str(e)}",
                level="error"
            )
            return 0

    @commands.hybrid_command(name="xp", description="Check your XP and level")
    @app_commands.describe(user="User to check (optional)")
    async def xp(self, ctx: commands.Context, user: Optional[discord.User] = None):
        target = user or ctx.author
        xp = await self.get_user_data(str(ctx.guild.id), str(target.id))
        
        level, current_xp = calculate_level(xp)
        next_level_xp = xp_for_next_level(level)
        progress = min(100, int((current_xp / next_level_xp) * 100)) if next_level_xp > 0 else 100
        
        embed = discord.Embed(
            title=f"{target.display_name}'s Stats",
            color=discord.Color.blue()
        )
        embed.add_field(name="Level", value=str(level))
        embed.add_field(name="XP Progress", value=f"{current_xp}/{next_level_xp} ({progress}%)")
        embed.set_thumbnail(url=target.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(XP(bot))