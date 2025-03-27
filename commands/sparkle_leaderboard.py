import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import escape_markdown
from typing import Optional

class SparkleLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sparkle_emojis = {
            "epic": "✨",  # Epic sparkle
            "rare": "🌟",  # Rare sparkle
            "regular": "⭐"  # Regular sparkle
        }

    @commands.hybrid_command(name="sparkleleaderboard", aliases=["sparklelb"], description="Show server Sparkle leaderboard")
    @app_commands.describe(limit="Number of users to show (max 20)")
    async def sparkle_leaderboard(self, ctx: commands.Context, limit: int = 10):
        """Show the sparkle leaderboard with all sparkle types"""
        limit = max(1, min(20, limit))
        
        # Get current server members
        guild_member_ids = {str(member.id) for member in ctx.guild.members}
        
        if not guild_member_ids:
            await ctx.send("This server has no members to display.", ephemeral=True)
            return
            
        async with await self.bot.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """SELECT user_id, epic, rare, regular, 
                          (epic + rare + regular) as total
                       FROM sparkles
                       WHERE server_id = ? AND user_id IN ({})
                       ORDER BY total DESC LIMIT ?"""
                       .format(','.join(['?']*len(guild_member_ids))),
                    (str(ctx.guild.id), *guild_member_ids, limit)
                )
                results = await cur.fetchall()
                
                if not results:
                    await ctx.send("No sparkle data available for members of this server.", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title=f"{escape_markdown(ctx.guild.name)} Sparkle Leaderboard",
                    color=discord.Color.gold())
                
                for rank, (user_id, epic, rare, regular, total) in enumerate(results, 1):
                    user = ctx.guild.get_member(int(user_id))
                    display_name = escape_markdown(user.display_name) if user else f"Unknown User ({user_id})"
                    
                    # Format sparkle counts with the correct emojis
                    sparkles = (
                        f"{self.sparkle_emojis['epic']} {epic} (Epic) | "
                        f"{self.sparkle_emojis['rare']} {rare} (Rare) | "
                        f"{self.sparkle_emojis['regular']} {regular} (Regular) | "
                        f"**Total:** {total}"
                    )
                    
                    embed.add_field(
                        name=f"{rank}. {display_name}",
                        value=sparkles,
                        inline=False)
                    
                    # Set thumbnail to top user's avatar
                    if rank == 1 and user:
                        embed.set_thumbnail(url=user.display_avatar.url)
                
                # Add footer with sparkle types
                embed.set_footer(text="✨ Epic | 🌟 Rare | ⭐ Regular")
                
                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SparkleLeaderboard(bot))