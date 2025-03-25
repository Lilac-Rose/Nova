import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List, Optional, Tuple
from utils.database import get_connection

class RankSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Level-based ranks
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
        
        # Purchasable ranks and their prices
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
        """Calculate level based on XP using progressive scaling"""
        level = 0
        xp_needed = 100
        while xp >= xp_needed:
            xp -= xp_needed
            level += 1
            xp_needed = int(xp_needed * 1.2)
        return level

    def get_all_achieved_level_ranks(self, level: int) -> List[str]:
        """Get all level ranks achieved up to current level"""
        return [rank for lvl, rank in sorted(self.level_ranks.items()) if lvl <= level]

    def get_current_level_rank(self, level: int) -> str:
        """Get the highest rank achieved for current level"""
        achieved = self.get_all_achieved_level_ranks(level)
        return achieved[-1] if achieved else "Nova Seed"

    def get_next_level_rank(self, level: int) -> Optional[Tuple[int, str]]:
        """Get the next rank to achieve (level threshold and name)"""
        for lvl, rank in sorted(self.level_ranks.items()):
            if lvl > level:
                return (lvl, rank)
        return None

    async def _ensure_level_ranks(self, user_id: str, xp: int):
        """Ensure user has all appropriate level ranks in database"""
        level = self._calculate_level_from_xp(xp)
        achieved_ranks = self.get_all_achieved_level_ranks(level)
        
        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                # Insert missing level ranks
                for rank_name in achieved_ranks:
                    await cur.execute('''
                        INSERT OR IGNORE INTO user_ranks 
                        (user_id, rank_name, rank_type)
                        VALUES (?, ?, 'level')
                    ''', (str(user_id), rank_name))
                await conn.commit()

    @commands.hybrid_command(name="myranks", description="View your complete rank progression")
    async def show_my_ranks(self, ctx: commands.Context):
        """Display all earned and purchased ranks"""
        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                # Get user's XP and level
                await cur.execute(
                    "SELECT xp FROM user_xp WHERE server_id = ? AND user_id = ?",
                    (str(ctx.guild.id), str(ctx.author.id))
                )
                xp_result = await cur.fetchone()
                xp = xp_result[0] if xp_result else 0
                level = self._calculate_level_from_xp(xp)
                
                # Get all owned ranks
                await cur.execute('''
                    SELECT rank_name, is_equipped, rank_type FROM user_ranks
                    WHERE user_id = ?
                    ORDER BY
                        CASE rank_type
                            WHEN 'level' THEN 0
                            ELSE 1
                        END,
                        rank_name
                ''', (str(ctx.author.id),))
                all_ranks = await cur.fetchall()
                
        # Get rank information
        earned_ranks = self.get_all_achieved_level_ranks(level)
        current_rank = self.get_current_level_rank(level)
        next_rank_info = self.get_next_level_rank(level)
        
        # Create embed
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Ranks",
            color=discord.Color.purple()
        )
        
        # Current Rank
        embed.add_field(
            name="🌟 Current Rank",
            value=f"{current_rank} (Level {level})",
            inline=False
        )
        
        # Earned Level Ranks
        if len(earned_ranks) > 1:
            embed.add_field(
                name="✨ Rank Journey",
                value="\n".join(f"• {rank}" for rank in earned_ranks[:-1]),
                inline=False
            )
        
        # Next Rank
        if next_rank_info:
            next_lvl, next_rank = next_rank_info
            embed.add_field(
                name="🔜 Next Rank",
                value=f"{next_rank} at level {next_lvl}",
                inline=False
            )
        
        # Purchased Ranks
        purchased_ranks = [r for r in all_ranks if r[2] == 'purchased']
        if purchased_ranks:
            ranks_list = []
            for rank_name, is_equipped, _ in purchased_ranks:
                prefix = "⭐ " if is_equipped else ""
                ranks_list.append(f"{prefix}{rank_name.title()}")
            
            embed.add_field(
                name="🛍️ Purchased Ranks",
                value="\n".join(ranks_list),
                inline=False
            )
        else:
            embed.add_field(
                name="🛍️ Purchased Ranks",
                value="Use `/shop` to buy special ranks!",
                inline=False
            )
        
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="shop", description="View available purchasable ranks")
    async def rank_shop(self, ctx: commands.Context):
        """Display the rank shop"""
        embed = discord.Embed(
            title="🛍️ Rank Shop",
            description="Purchase these special ranks with your coins!",
            color=discord.Color.gold()
        )
        
        shop_items = []
        for rank, price in sorted(self.shop_ranks.items(), key=lambda x: x[1]):
            shop_items.append(f"• {rank.title()}: {price:,} coins")
        
        embed.add_field(
            name="Available Ranks",
            value="\n".join(shop_items),
            inline=False
        )
        
        embed.set_footer(text="Use /buyrank [name] to purchase")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="buyrank", description="Purchase a special rank")
    @app_commands.describe(rank_name="Name of the rank to purchase (see /shop for exact names)")
    async def buy_rank(self, ctx: commands.Context, rank_name: str):
        """Purchase a rank from the shop"""
        rank_name = rank_name.lower()
        
        if rank_name not in self.shop_ranks:
            available = ", ".join(f"`{r}`" for r in self.shop_ranks.keys())
            return await ctx.send(
                f"That rank doesn't exist! Available ranks: {available}",
                ephemeral=True
            )
        
        price = self.shop_ranks[rank_name]
        
        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                # Check if user already owns the rank
                await cur.execute(
                    "SELECT 1 FROM user_ranks WHERE user_id = ? AND rank_name = ?",
                    (str(ctx.author.id), rank_name)
                )
                if await cur.fetchone():
                    return await ctx.send(
                        f"You already own the `{rank_name}` rank!",
                        ephemeral=True
                    )
                
                # Verify and deduct coins
                await cur.execute(
                    "SELECT coins FROM user_coins WHERE user_id = ?",
                    (str(ctx.author.id),)
                )
                result = await cur.fetchone()
                
                if not result:
                    return await ctx.send(
                        "You don't have a coin balance yet!",
                        ephemeral=True
                    )
                
                if result[0] < price:
                    return await ctx.send(
                        f"Not enough coins! You need {price:,} but have {result[0]:,}.",
                        ephemeral=True
                    )
                
                # Perform the transaction
                try:
                    await cur.execute(
                        "UPDATE user_coins SET coins = coins - ? WHERE user_id = ?",
                        (price, str(ctx.author.id))
                    )
                    
                    await cur.execute(
                        """INSERT INTO user_ranks (user_id, rank_name, rank_type, is_equipped)
                        VALUES (?, ?, 'purchased', 0)""",
                        (str(ctx.author.id), rank_name)
                    )
                    
                    await conn.commit()
                except Exception as e:
                    await conn.rollback()
                    await ctx.send(
                        "❌ Transaction failed! Your coins were not deducted.",
                        ephemeral=True
                    )
                    raise e
        
        await ctx.send(
            f"🎉 Successfully purchased `{rank_name}` rank for {price:,} coins!",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(RankSystem(bot))