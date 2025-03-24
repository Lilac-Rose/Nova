import discord
from discord.ext import commands
from utils.database import get_connection

class ForceSparkle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="forcesparkle", description="Force a sparkle reaction on a message.")
    async def forcesparkle(self, ctx, message_id: str, reaction_type: str):
        if ctx.author.bot:
            return

        valid_reactions = {
            "epic": "✨",
            "rare": "🌟",
            "regular": "⭐"
        }

        if reaction_type.lower() not in valid_reactions:
            await ctx.send("Invalid reaction type. Use `epic`, `rare`, or `regular`.", ephemeral=True)
            return

        try:
            message = await ctx.channel.fetch_message(int(message_id))
        except discord.NotFound:
            await ctx.send("Message not found.", ephemeral=True)
            return
        except discord.Forbidden:
            await ctx.send("No permission to access that message.", ephemeral=True)
            return
        except ValueError:
            await ctx.send("Invalid message ID.", ephemeral=True)
            return

        emoji = valid_reactions[reaction_type.lower()]
        await message.add_reaction(emoji)

        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """INSERT INTO sparkles (server_id, user_id, epic, rare, regular)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(server_id, user_id) DO UPDATE SET
                    epic = epic + excluded.epic,
                    rare = rare + excluded.rare,
                    regular = regular + excluded.regular""",
                    (str(ctx.guild.id), str(message.author.id),
                     *(1 if k == reaction_type.lower() else 0 for k in ["epic", "rare", "regular"]))
                )
                await conn.commit()

        await ctx.send(f"Added {emoji} reaction")

async def setup(bot):
    await bot.add_cog(ForceSparkle(bot))