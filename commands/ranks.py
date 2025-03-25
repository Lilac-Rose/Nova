import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List, Optional, Tuple
from utils.database import get_connection

class RankSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Gorgeous level progression ranks
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
        
        # Classic purchasable ranks
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
        """Calculate level from XP"""
        level = 0
        xp_needed = 100
        while xp >= xp_needed:
            xp -= xp_needed
            level += 1
            xp_needed = int(xp_needed * 1.2)
        return level

    async def _ensure_level_ranks(self, user_id: str, xp: int):
        """Ensure user has all appropriate level ranks"""
        async with await get_connection() as conn:
            level = self._calculate_level_from_xp(xp)
            current_rank_level = (level // 5) * 5
            
            async with conn.cursor() as cur:
                # Remove any existing level ranks below current level
                await cur.execute(
                    "DELETE FROM user_ranks WHERE user_id = ? AND rank_type = 'level'",
                    (str(user_id),))
                
                # Add all achieved level ranks
                for threshold in sorted(self.level_ranks.keys()):
                    if threshold <= current_rank_level:
                        await cur.execute(
                            """INSERT OR IGNORE INTO user_ranks 
                            (user_id, rank_name, rank_type)
                            VALUES (?, ?, 'level')""",
                            (str(user_id), self.level_ranks[threshold]))
                
                await conn.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Update ranks when users gain XP"""
        if message.author.bot:
            return
        
        # Call this from your XP system after granting XP
        # await self._ensure_level_ranks(str(message.author.id), new_xp)

    @commands.hybrid_command(name="ranks", description="View all rank types")
    async def show_ranks(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🌟 Nova Rank System",
            color=discord.Color.purple()
        )
        
        # Level ranks
        level_desc = "\n".join(
            f"Level {lvl}: {rank}" 
            for lvl, rank in sorted(self.level_ranks.items())
        )
        embed.add_field(
            name="🌠 Level Progression Ranks",
            value=level_desc,
            inline=False
        )
        
        # Purchasable ranks
        shop_desc = "\n".join(
            f"{rank.capitalize()}: {price:,} coins" 
            for rank, price in sorted(self.shop_ranks.items(),
                                    key=lambda x: x[1])
        )
        embed.add_field(
            name="💖 Purchasable Ranks (use !shop)",
            value=shop_desc,
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="xpsystem", description="How the XP and coins system works")
    async def explain_system(self, ctx: commands.Context):
        embed = discord.Embed(
            title="✨ Nova XP System",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="XP Gain",
            value="• Earn 5-15 XP per message (10s cooldown)\n"
                  "• Higher activity = more XP\n"
                  "• Level up every 100 XP (scaling)",
            inline=False
        )
        
        embed.add_field(
            name="Coins",
            value="• Earn 1 coin per XP gained\n"
                  "• Bonus coins when leveling up\n"
                  "• Use coins to buy special ranks in !shop",
            inline=False
        )
        
        embed.add_field(
            name="Ranks",
            value="• Automatic level ranks every 5 levels\n"
                  "• Purchasable cute ranks in !shop\n"
                  "• Equip your favorite with !equip_rank",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="shop", description="View purchasable ranks")
    async def show_shop(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🌸 Nova Rank Shop",
            color=discord.Color.pink()
        )
        
        shop_items = "\n".join(
            f"• {rank.capitalize()} - {price:,} coins" 
            for rank, price in sorted(self.shop_ranks.items(),
                                    key=lambda x: x[1])
        )
        
        embed.description = shop_items
        embed.set_footer(text="Use !buy [rank] to purchase a rank")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="buy", description="Purchase a rank")
    @app_commands.describe(rank_name="The rank you want to purchase")
    async def buy_rank(self, ctx: commands.Context, rank_name: str):
        rank_name = rank_name.lower()
        if rank_name not in self.shop_ranks:
            return await ctx.send(
                f"That rank doesn't exist! Use !shop to see available ranks.",
                ephemeral=True
            )
        
        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                # Check coins
                await cur.execute(
                    "SELECT coins FROM user_coins WHERE user_id = ?",
                    (str(ctx.author.id),))
                result = await cur.fetchone()
                coins = result[0] if result else 0
                
                if coins < self.shop_ranks[rank_name]:
                    return await ctx.send(
                        f"You need {self.shop_ranks[rank_name]:,} coins to buy this!",
                        ephemeral=True
                    )
                
                # Deduct coins and add rank
                await cur.execute(
                    "UPDATE user_coins SET coins = coins - ? WHERE user_id = ?",
                    (self.shop_ranks[rank_name], str(ctx.author.id)))
                
                await cur.execute(
                    """INSERT OR IGNORE INTO user_ranks 
                    (user_id, rank_name, rank_type) 
                    VALUES (?, ?, 'purchased')""",
                    (str(ctx.author.id), rank_name))
                
                await conn.commit()
        
        await ctx.send(
            f"✨ You bought the '{rank_name}' rank! Use !equip_rank {rank_name} to show it on your profile.",
            ephemeral=True
        )

    @commands.hybrid_command(name="equip_rank", description="Equip a rank to display on your profile")
    @app_commands.describe(rank_name="The rank to equip")
    async def equip_rank(self, ctx: commands.Context, rank_name: str):
        rank_name = rank_name.lower()
        
        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                # Check if user owns this rank
                await cur.execute(
                    """SELECT 1 FROM user_ranks 
                    WHERE user_id = ? AND rank_name = ?""",
                    (str(ctx.author.id), rank_name))
                
                if not await cur.fetchone():
                    return await ctx.send(
                        "You don't own this rank! Use !myranks to see your available ranks.",
                        ephemeral=True
                    )
                
                # Unequip all other ranks first
                await cur.execute(
                    """UPDATE user_ranks 
                    SET is_equipped = 0 
                    WHERE user_id = ?""",
                    (str(ctx.author.id),))
                
                # Equip selected rank
                await cur.execute(
                    """UPDATE user_ranks 
                    SET is_equipped = 1 
                    WHERE user_id = ? AND rank_name = ?""",
                    (str(ctx.author.id), rank_name))
                
                await conn.commit()
        
        await ctx.send(
            f"💖 You've equipped the '{rank_name}' rank! It will now show on your profile.",
            ephemeral=True
        )

    @commands.hybrid_command(name="myranks", description="View all your owned ranks")
    async def show_my_ranks(self, ctx: commands.Context):
        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                # Get level
                await cur.execute(
                    "SELECT xp FROM user_xp WHERE server_id = ? AND user_id = ?",
                    (str(ctx.guild.id), str(ctx.author.id)))
                xp_result = await cur.fetchone()
                xp = xp_result[0] if xp_result else 0
                level = self._calculate_level_from_xp(xp)
                current_rank = next(
                    rank for lvl, rank in sorted(self.level_ranks.items(), reverse=True) 
                    if lvl <= level
                )
                
                # Get purchased ranks
                await cur.execute(
                    """SELECT rank_name, is_equipped FROM user_ranks 
                    WHERE user_id = ? AND rank_type = 'purchased'""",
                    (str(ctx.author.id),))
                purchased_ranks = await cur.fetchall()
                
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Ranks",
            color=discord.Color.lighter_grey()
        )
        
        # Current level rank
        embed.add_field(
            name="🌱 Current Level Rank",
            value=f"{current_rank} (Level {level})",
            inline=False
        )
        
        # Purchased ranks
        if purchased_ranks:
            ranks_list = []
            for rank_name, is_equipped in purchased_ranks:
                star = "⭐ " if is_equipped else ""
                ranks_list.append(f"{star}{rank_name.capitalize()}")
            
            embed.add_field(
                name="💝 Purchased Ranks",
                value="\n".join(ranks_list),
                inline=False
            )
            embed.set_footer(text="⭐ = Currently equipped")
        else:
            embed.add_field(
                name="💝 Purchased Ranks",
                value="You haven't bought any ranks yet! Use !shop",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RankSystem(bot))