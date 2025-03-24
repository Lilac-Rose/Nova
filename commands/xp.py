import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from utils.xp_utils import calculate_level, xp_needed_for_level, LEVEL_UP_BONUS

class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_user_data(self, server_id: str, user_id: str):
        try:
            async with self.bot.db.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute('''
                        SELECT xp 
                        FROM user_xp 
                        WHERE server_id = ? AND user_id = ?
                    ''', (server_id, user_id))
                    result = await cur.fetchone()
                    
                    if result is None:
                        await cur.execute('''
                            INSERT INTO user_xp (server_id, user_id, xp) 
                            VALUES (?, ?, 0)
                        ''', (server_id, user_id))
                        await conn.commit()
                        return 0
                    
                    return result[0]
        except Exception as e:
            await self.bot.logger.log(
                f"❌ Database error in get_user_data: {str(e)}",
                level="error"
            )
            return 0

    @commands.hybrid_command(name="xp", description="Check your XP and level")
    @app_commands.describe(user="The user to check (optional)")
    async def xp(self, ctx: commands.Context, user: Optional[discord.User] = None):
        target = user or ctx.author
        server_id = str(ctx.guild.id)
        user_id = str(target.id)
        
        xp = await self.get_user_data(server_id, user_id)
        level, remaining_xp = calculate_level(xp)
        next_level_xp = xp_needed_for_level(level + 1)
        xp_needed = next_level_xp - remaining_xp
        
        async with self.bot.db.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute('''
                    SELECT coins FROM user_coins WHERE user_id = ?
                ''', (user_id,))
                coins_result = await cur.fetchone()
                coins = coins_result[0] if coins_result else 0

        embed = discord.Embed(
            title=f"{target.display_name}'s Stats",
            color=discord.Color.blue()
        )
        embed.add_field(name="Level", value=str(level))
        embed.add_field(name="XP", value=f"{remaining_xp}/{next_level_xp} (need {xp_needed} more)")
        embed.add_field(name="Nova Coins", value=str(coins))
        embed.set_footer(text=f"Level up bonus: +{LEVEL_UP_BONUS} coins per level")  # Shows 100
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(XP(bot))