import discord
from discord.ext import commands
from discord import app_commands
from utils.database import get_connection

class CoinsLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="coinsleaderboard", aliases=["coinslb"], description="Show global Nova Coins leaderboard")
    @app_commands.describe(limit="Number of users to show (max 20)")
    async def coins_leaderboard(self, ctx: commands.Context, limit: int = 10):
        limit = max(1, min(20, limit))
        
        try:
            # Log command usage
            await self.bot.logger.log(
                f"Command executed: coinsleaderboard by {ctx.author}",
                level="info"
            )

            async with await get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT user_id, coins FROM user_coins 
                        ORDER BY coins DESC 
                        LIMIT ?
                    """, (limit,))
                    results = await cursor.fetchall()
                    
                    if not results:
                        await ctx.send("No coins data available yet.", ephemeral=True)
                        return
                    
                    embed = discord.Embed(
                        title="Global Nova Coins Leaderboard",
                        color=discord.Color.green()
                    )
                    
                    for rank, (user_id, coins) in enumerate(results, 1):
                        user = self.bot.get_user(int(user_id))
                        if user:
                            embed.add_field(
                                name=f"{rank}. {user.name}",
                                value=f"{coins} Nova Coins",
                                inline=False
                            )
                        else:
                            try:
                                user = await self.bot.fetch_user(int(user_id))
                                embed.add_field(
                                    name=f"{rank}. {user.name}",
                                    value=f"{coins} Nova Coins",
                                    inline=False
                                )
                            except:
                                embed.add_field(
                                    name=f"{rank}. Unknown User",
                                    value=f"{coins} Nova Coins",
                                    inline=False
                                )
                    
                    await ctx.send(embed=embed)
                    await self.bot.logger.log(
                        f"Successfully displayed coins leaderboard",
                        level="debug"
                    )

        except Exception as e:
            await self.bot.logger.log(
                f"Error in coins leaderboard: {str(e)}",
                level="error",
                alert=True
            )
            await ctx.send("An error occurred while fetching the leaderboard.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CoinsLeaderboard(bot))