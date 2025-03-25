import discord
from discord.ext import commands
from discord import app_commands

class CoinsLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="coinsleaderboard", aliases=["coinslb"], description="Show global Nova Coins leaderboard")
    @app_commands.describe(limit="Number of users to show (max 20)")
    async def coins_leaderboard(self, ctx: commands.Context, limit: int = 10):
        limit = max(1, min(20, limit))
        
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT user_id, coins FROM user_coins 
                    ORDER BY coins DESC 
                    LIMIT ?
                """, (limit,))
                results = await cur.fetchall()
                
                if not results:
                    await ctx.send("No coins data available yet.", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="💰 Global Nova Coins Leaderboard",
                    color=discord.Color.green()
                )
                
                for rank, (user_id, coins) in enumerate(results, 1):
                    user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(int(user_id))
                    display_name = user.name if user else f"Unknown User ({user_id})"
                    embed.add_field(
                        name=f"{rank}. {display_name}",
                        value=f"{coins:,} Nova Coins",
                        inline=False
                    )
                
                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CoinsLeaderboard(bot))