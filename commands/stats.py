import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from utils.database import get_connection
from utils.xp import calculate_level, xp_for_next_level

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.level_ranks = {
            0: "Nova Seed",
            5: "Blossoming Nova",
            10: "Starlight Sprite",
            15: "Celestial Bloom",
            20: "Luminous Petal",
            25: "Galactic Lily",
            30: "Cosmic Rose",
            35: "Nebula Orchid",
            40: "Supernova Dahlia",
            45: "Quasar Peony",
            50: "Pulsar Primrose",
            55: "Andromeda Azalea",
            60: "Infinity Iris",
            65: "Eternal Violet",
            70: "Paradise Magnolia",
            75: "Dreamweaver Lotus",
            80: "Mystic Marigold",
            85: "Enchanted Tulip",
            90: "Divine Daffodil",
            95: "Transcendent Camellia",
            100: "Ultimate Nova"
        }

    def get_level_rank(self, level: int) -> str:
        """Get the highest rank achieved for a given level"""
        achieved_ranks = [rank for lvl, rank in self.level_ranks.items() if lvl <= level]
        return achieved_ranks[-1] if achieved_ranks else "Newbie"

    def format_rank_name(self, rank: Optional[str]) -> str:
        """Format rank name with proper capitalization"""
        if not rank:
            return "None"
        return rank.title()

    async def get_user_stats(self, server_id: str, user_id: str):
        try:
            async with await get_connection() as conn:
                async with conn.cursor() as cur:
                    # Get XP, coins, and ranks
                    await cur.execute('''
                        SELECT 
                            ux.xp, 
                            uc.coins,
                            (SELECT rank_name FROM user_ranks 
                             WHERE user_id = ? AND is_equipped = 1 LIMIT 1) as equipped_rank
                        FROM user_xp ux
                        LEFT JOIN user_coins uc ON ux.user_id = uc.user_id
                        WHERE ux.server_id = ? AND ux.user_id = ?
                    ''', (user_id, server_id, user_id))
                    result = await cur.fetchone()
                    
                    if result is None:
                        # Initialize user if not found
                        await cur.execute('''
                            INSERT OR IGNORE INTO user_xp (server_id, user_id, xp)
                            VALUES (?, ?, 0)
                        ''', (server_id, user_id))
                        await cur.execute('''
                            INSERT OR IGNORE INTO user_coins (user_id, coins)
                            VALUES (?, 0)
                        ''', (user_id,))
                        await conn.commit()
                        return (0, 0, None)  # Default XP, coins, no equipped rank
                    
                    return (result[0], result[1] if result[1] is not None else 0, result[2])

        except Exception as e:
            await self.bot.logger.log(
                f"Stats query failed: {str(e)}",
                level="error"
            )
            return (0, 0, None)

    @commands.hybrid_command(name="stats", description="Check your stats! (Coins, XP, and level)")
    async def xp(self, ctx: commands.Context, user: Optional[discord.User] = None):
        target = user or ctx.author
        xp, coins, equipped_rank = await self.get_user_stats(str(ctx.guild.id), str(target.id))
        
        level, current_xp = calculate_level(xp)
        level_rank = self.get_level_rank(level)
        next_level_xp = xp_for_next_level(level)
        progress = min(100, int((current_xp / next_level_xp) * 100)) if next_level_xp > 0 else 100
        
        embed = discord.Embed(
            title=f"{target.display_name}'s Stats",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Level Rank",
            value=self.format_rank_name(level_rank),
            inline=True
        )
        
        if equipped_rank:
            embed.add_field(
                name="Equipped Rank",
                value=self.format_rank_name(equipped_rank),
                inline=True
            )
        
        embed.add_field(
            name="Level",
            value=str(level),
            inline=True
        )
        
        embed.add_field(
            name="XP Progress", 
            value=f"{current_xp}/{next_level_xp} ({progress}%)",
            inline=True
        )
        
        embed.add_field(
            name="Coins",
            value=f"{coins:,}",
            inline=True
        )
        
        next_rank = next(
            (lvl, rank) for lvl, rank in sorted(self.level_ranks.items()) 
            if lvl > level
        )
        if next_rank:
            embed.set_footer(text=f"Next level rank: {next_rank[1]} at level {next_rank[0]}")
        
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))