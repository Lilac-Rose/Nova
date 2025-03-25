import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import escape_markdown
from utils.xp import calculate_level

class XpLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="xpleaderboard", aliases=["xplb"], description="Show server XP leaderboard")
    @app_commands.describe(limit="Number of users to show (max 20)")
    async def xp_leaderboard(self, ctx: commands.Context, limit: int = 10):
        limit = max(1, min(20, limit))
        
        async with self.bot.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT user_id, xp FROM user_xp "
                    "WHERE server_id = ? "
                    "ORDER BY xp DESC LIMIT ?",
                    (str(ctx.guild.id), limit)
                )
                results = await cur.fetchall()
                
                if not results:
                    await ctx.send("No XP data available for this server yet.", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title=f"{escape_markdown(ctx.guild.name)} XP Leaderboard",
                    color=discord.Color.gold())
                
                for rank, (user_id, xp) in enumerate(results, 1):
                    user = ctx.guild.get_member(int(user_id))
                    level, _ = calculate_level(xp)
                    display_name = escape_markdown(user.display_name) if user else f"Unknown User ({user_id})"
                    
                    embed.add_field(
                        name=f"{rank}. {display_name}",
                        value=f"Level {level} | {xp:,} XP",
                        inline=False)
                    
                    if rank == 1 and user:
                        embed.set_thumbnail(url=user.display_avatar.url)
                
                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(XpLeaderboard(bot))