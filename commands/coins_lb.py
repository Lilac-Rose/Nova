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
        
        if not self.bot.coins_data:
            await ctx.send("No coins data available yet.", ephemeral=True)
            return
        
        sorted_users = sorted(self.bot.coins_data.items(), key=lambda item: item[1], reverse=True)[:limit]
        
        embed = discord.Embed(
            title="Global Nova Coins Leaderboard",
            color=discord.Color.green()
        )
        
        for rank, (user_id, coins) in enumerate(sorted_users, 1):
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

async def setup(bot):
    await bot.add_cog(CoinsLeaderboard(bot))