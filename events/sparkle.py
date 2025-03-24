import random
import discord
from discord.ext import commands
from utils.database import get_connection

class Sparkle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        chance = random.randint(1, 100000)
        reaction_type = None

        if chance == 1:
            reaction_type = ("✨", "epic", "an **epic sparkle**")
        elif chance <= 10:
            reaction_type = ("🌟", "rare", "a **rare sparkle**")
        elif chance <= 100:
            reaction_type = ("⭐", "regular", "a **sparkle**")

        if reaction_type:
            emoji, type_key, description = reaction_type
            await message.add_reaction(emoji)
            await message.reply(f"**{message.author.name}** got {description}! {emoji}", mention_author=False)

            async with await get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        f"""INSERT INTO sparkles (server_id, user_id, {type_key})
                        VALUES (?, ?, 1)
                        ON CONFLICT(server_id, user_id) DO UPDATE SET
                        {type_key} = {type_key} + 1""",
                        (str(message.guild.id), str(message.author.id)))
                    await conn.commit()

async def setup(bot):
    await bot.add_cog(Sparkle(bot))