import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import escape_markdown
from typing import Tuple  # Add this import

class NetWorthLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rank_values = {
            "cutie": 1000,
            "goddess": 10000,
            "uwu": 3000,
            "smol": 2000,
            "bean": 4000,
            "divine": 15000,
            "legendary": 20000,
            "potato": 1000,
            "angel": 5000,
            "bunny": 3500,
            "princess": 8000
        }

    async def calculate_net_worth(self, user_id: str, conn) -> Tuple[int, int, int]:
        """Calculate a user's total net worth and components"""
        async with conn.cursor() as cur:
            # Get coins balance
            await cur.execute(
                "SELECT coins FROM user_coins WHERE user_id = ?",
                (user_id,)
            )
            coins_result = await cur.fetchone()
            coins = coins_result[0] if coins_result else 0
            
            # Get purchased ranks and sum their values
            await cur.execute(
                "SELECT rank_name FROM user_ranks WHERE user_id = ? AND rank_type = 'purchased'",
                (user_id,)
            )
            ranks = await cur.fetchall()
            rank_value = sum(self.rank_values.get(rank[0].lower(), 0) for rank in ranks)
            
            return coins + rank_value, coins, rank_value

    @commands.hybrid_command(name="networthlb", aliases=["nwlb"], 
                            description="Show server net worth leaderboard (coins + rank values)")
    @app_commands.describe(limit="Number of users to show (max 20)")
    async def networth_leaderboard(self, ctx: commands.Context, limit: int = 10):
        limit = max(1, min(20, limit))
        
        guild_member_ids = {str(member.id) for member in ctx.guild.members}
        
        if not guild_member_ids:
            await ctx.send("This server has no members to display.", ephemeral=True)
            return
            
        async with self.bot.db_pool.acquire() as conn:
            # Calculate net worth for all members
            member_data = []
            for user_id in guild_member_ids:
                net_worth, coins, rank_value = await self.calculate_net_worth(user_id, conn)
                member_data.append((user_id, net_worth, coins, rank_value))
            
            # Sort by net worth (descending) and take top results
            member_data.sort(key=lambda x: x[1], reverse=True)
            top_results = member_data[:limit]
                
            if not top_results:
                await ctx.send("No net worth data available for members of this server.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"{escape_markdown(ctx.guild.name)} Net Worth Leaderboard",
                color=discord.Color.gold())
            
            # Add #1 with breakdown
            user_id, net_worth, coins, rank_value = top_results[0]
            user = ctx.guild.get_member(int(user_id))
            
            if user:
                embed.add_field(
                    name=f"#1 {escape_markdown(user.display_name)}",
                    value=(
                        f"**Coins:** {coins:,}\n"
                        f"**Rank Value:** {rank_value:,}\n"
                        f"**Total:** {net_worth:,}"
                    ),
                    inline=False
                )
                embed.set_thumbnail(url=user.display_avatar.url)
            
            # Add other entries with just total
            for rank, (user_id, net_worth, _, _) in enumerate(top_results[1:], 2):
                user = ctx.guild.get_member(int(user_id))
                display_name = escape_markdown(user.display_name) if user else f"Unknown User ({user_id})"
                
                embed.add_field(
                    name=f"{rank}. {display_name}",
                    value=f"{net_worth:,}",
                    inline=False)
            
            embed.set_footer(text="Net worth = coins + value of purchased ranks")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(NetWorthLeaderboard(bot))