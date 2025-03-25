import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List, Optional
from utils.database import get_connection

class RankSystem(commands.Cog):
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
        
        # Purchasable ranks
        self.shop_ranks = {
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

    def _calculate_level_from_xp(self, xp: int) -> int:
        level = 0
        xp_needed = 100
        while xp >= xp_needed:
            xp -= xp_needed
            level += 1
            xp_needed = int(xp_needed * 1.2)
        return level

    def get_current_level_rank(self, level: int) -> str:
        return next((rank for lvl, rank in sorted(self.level_ranks.items(), reverse=True) if lvl <= level), "Newbie")

    async def _ensure_level_ranks(self, user_id: str, xp: int):
        """Ensure user has all appropriate level ranks"""
        level = self._calculate_level_from_xp(xp)
        current_rank_level = (level // 5) * 5
        
        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                # Get all achieved level thresholds
                achieved_thresholds = [lvl for lvl in self.level_ranks.keys() if lvl <= current_rank_level]
                
                # Add any missing level ranks
                for threshold in achieved_thresholds:
                    rank_name = self.level_ranks[threshold]
                    await cur.execute('''
                        INSERT OR IGNORE INTO user_ranks 
                        (user_id, rank_name, rank_type)
                        VALUES (?, ?, 'level')
                    ''', (str(user_id), rank_name))
                
                await conn.commit()

    @commands.hybrid_command(name="myranks", description="View all your owned ranks")
    async def show_my_ranks(self, ctx: commands.Context):
        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                # Get current level
                await cur.execute(
                    "SELECT xp FROM user_xp WHERE server_id = ? AND user_id = ?",
                    (str(ctx.guild.id), str(ctx.author.id)))
                xp_result = await cur.fetchone()
                xp = xp_result[0] if xp_result else 0
                level = self._calculate_level_from_xp(xp)
                current_rank = self.get_current_level_rank(level)
                
                # Get all owned ranks
                await cur.execute(
                    """SELECT rank_name, is_equipped, rank_type FROM user_ranks 
                    WHERE user_id = ? ORDER BY 
                    CASE rank_type
                        WHEN 'level' THEN 0
                        ELSE 1
                    END, rank_name""",
                    (str(ctx.author.id),))
                all_ranks = await cur.fetchall()
                
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Ranks",
            color=discord.Color.lighter_grey()
        )
        
        # Current level rank (shows first)
        embed.add_field(
            name="Current Level Rank",
            value=f"🌱 {current_rank} (Level {level})",
            inline=False
        )
        
        # Other level ranks
        level_ranks = [r for r in all_ranks if r[2] == 'level' and r[0] != current_rank]
        if level_ranks:
            embed.add_field(
                name="Other Level Ranks",
                value="\n".join(f"• {r[0]}" for r in level_ranks),
                inline=False
            )
        
        # Purchased ranks
        purchased_ranks = [r for r in all_ranks if r[2] == 'purchased']
        if purchased_ranks:
            ranks_list = []
            for rank_name, is_equipped, _ in purchased_ranks:
                star = "⭐ " if is_equipped else ""
                ranks_list.append(f"{star}{rank_name.capitalize()}")
            
            embed.add_field(
                name="Purchased Ranks",
                value="\n".join(ranks_list),
                inline=False
            )
            embed.set_footer(text="⭐ = Currently equipped")
        else:
            embed.add_field(
                name="Purchased Ranks",
                value="You haven't bought any ranks yet! Use !shop",
                inline=False
            )
        
        await ctx.send(embed=embed)

    # ... [keep all other commands unchanged] ...

async def setup(bot):
    await bot.add_cog(RankSystem(bot))