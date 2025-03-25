import discord
from discord.ext import commands
from discord import app_commands

class CoinsLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="coinsleaderboard", aliases=["coinslb"], description="Show server Nova Coins leaderboard")
    @app_commands.describe(limit="Number of users to show (max 20)")
    async def coins_leaderboard(self, ctx: commands.Context, limit: int = 10):
        limit = max(1, min(20, limit))
        
        # Get all member IDs in the current guild
        guild_member_ids = {str(member.id) for member in ctx.guild.members}
        
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT user_id, coins FROM user_coins 
                    WHERE user_id IN ({})
                    ORDER BY coins DESC 
                    LIMIT ?
                """.format(','.join(['?']*len(guild_member_ids))), (*guild_member_ids, limit))
                results = await cur.fetchall()
                
                if not results:
                    await ctx.send("No coins data available for members of this server.", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title=f"💰 {ctx.guild.name} Nova Coins Leaderboard",
                    color=discord.Color.green()
                )
                
                for rank, (user_id, coins) in enumerate(results, 1):
                    user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(int(user_id))
                    display_name = user.display_name if user else f"Unknown User ({user_id})"
                    embed.add_field(
                        name=f"{rank}. {display_name}",
                        value=f"{coins:,} Nova Coins",
                        inline=False
                    )
                
                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CoinsLeaderboard(bot))