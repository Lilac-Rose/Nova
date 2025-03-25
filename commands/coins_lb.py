import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import escape_markdown

class CoinsLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="coinsleaderboard", aliases=["coinslb"], description="Show server Nova Coins leaderboard")
    @app_commands.describe(limit="Number of users to show (max 20)")
    async def coins_leaderboard(self, ctx: commands.Context, limit: int = 10):
        limit = max(1, min(20, limit))
        
        guild_member_ids = {str(member.id) for member in ctx.guild.members}
        
        if not guild_member_ids:
            await ctx.send("This server has no members to display.", ephemeral=True)
            return
            
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"SELECT user_id, coins FROM user_coins "
                    f"WHERE user_id IN ({','.join(['?']*len(guild_member_ids))}) "
                    "ORDER BY coins DESC LIMIT ?",
                    (*guild_member_ids, limit)
                )
                results = await cur.fetchall()
                
                if not results:
                    await ctx.send("No coins data available for members of this server.", ephemeral=True)
                    return
                
                safe_server_name = escape_markdown(ctx.guild.name)
                embed = discord.Embed(
                    title=f"💰 {safe_server_name} Nova Coins Leaderboard",
                    color=discord.Color.green()
                )
                
                for rank, (user_id, coins) in enumerate(results, 1):
                    user = ctx.guild.get_member(int(user_id))
                    if user:
                        safe_name = escape_markdown(user.display_name)
                        avatar = user.display_avatar.url
                    else:
                        safe_name = f"Unknown User ({user_id})"
                        avatar = None
                    
                    embed.add_field(
                        name=f"{rank}. {safe_name}",
                        value=f"{coins:,} Nova Coins",
                        inline=False
                    )
                    if avatar and rank == 1:  # Only set thumbnail for top user
                        embed.set_thumbnail(url=avatar)
                
                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CoinsLeaderboard(bot))