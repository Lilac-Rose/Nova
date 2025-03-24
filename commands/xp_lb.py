import discord
from discord.ext import commands
from discord import app_commands
from utils.database import get_connection
from utils.xp_utils import calculate_level

class XpLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="xpleaderboard", aliases=["xplb"], description="Show server XP leaderboard")
    @app_commands.describe(limit="Number of users to show (max 20)")
    async def xp_leaderboard(self, ctx: commands.Context, limit: int = 10):
        limit = max(1, min(20, limit))
        server_id = str(ctx.guild.id)
        
        async with await get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT user_id, xp FROM user_xp 
                    WHERE server_id = ? 
                    ORDER BY xp DESC 
                    LIMIT ?
                """, (server_id, limit))
                results = await cursor.fetchall()
                
                if not results:
                    await ctx.send("No XP data available for this server yet.", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title=f"{ctx.guild.name} XP Leaderboard",
                    color=discord.Color.gold()
                )
                
                for rank, (user_id, xp) in enumerate(results, 1):
                    user = ctx.guild.get_member(int(user_id))
                    if user:
                        level, _ = calculate_level(xp)
                        embed.add_field(
                            name=f"{rank}. {user.display_name}",
                            value=f"Level {level} | {xp} XP",
                            inline=False
                        )
                
                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(XpLeaderboard(bot))