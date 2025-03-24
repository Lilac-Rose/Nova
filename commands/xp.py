import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from utils.xp_utils import calculate_level, xp_needed_for_level, LEVEL_UP_BONUS

class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="xp", description="Check your XP and level")
    @app_commands.describe(user="The user to check (optional)")
    async def xp(self, ctx: commands.Context, user: Optional[discord.User] = None):
        target = user or ctx.author
        server_id = str(ctx.guild.id)
        user_id = str(target.id)
        
        xp = self.bot.xp_data.get(server_id, {}).get(user_id, 0)
        level, remaining_xp = calculate_level(xp)
        next_level_xp = xp_needed_for_level(level + 1)
        xp_needed = next_level_xp - remaining_xp
        coins = self.bot.coins_data.get(user_id, 0)
        
        embed = discord.Embed(
            title=f"{target.display_name}'s Stats",
            color=discord.Color.blue()
        )
        embed.add_field(name="Level", value=level)
        embed.add_field(name="XP", value=f"{remaining_xp}/{next_level_xp} (need {xp_needed} more)")
        embed.add_field(name="Nova Coins", value=coins)
        embed.set_footer(text=f"Level up bonus: +{LEVEL_UP_BONUS} coins per level")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(XP(bot))