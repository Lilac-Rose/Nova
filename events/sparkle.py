import random
import discord
from discord.ext import commands
from utils.database import get_connection

class Sparkle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chances = {
            "epic": (1, "✨", "an **epic sparkle**"),
            "rare": (10, "🌟", "a **rare sparkle**"),
            "regular": (100, "⭐", "a **sparkle**")
        }

    async def _add_sparkle(self, message, sparkle_type):
        emoji, description = self.chances[sparkle_type][1:]
        await message.add_reaction(emoji)
        await message.reply(
            f"**{message.author.name}** got {description}! {emoji}", 
            mention_author=False
        )

        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""INSERT INTO sparkles (server_id, user_id, {sparkle_type})
                    VALUES (?, ?, 1)
                    ON CONFLICT(server_id, user_id) DO UPDATE SET
                    {sparkle_type} = {sparkle_type} + 1""",
                    (str(message.guild.id), str(message.author.id))
                )
                await conn.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        chance = random.randint(1, 1000000)
        
        if chance == 1:
            await self._add_sparkle(message, "epic")
        elif chance <= 10:
            await self._add_sparkle(message, "rare")
        elif chance <= 100:
            await self._add_sparkle(message, "regular")

async def setup(bot):
    await bot.add_cog(Sparkle(bot))