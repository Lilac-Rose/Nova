import discord
from discord.ext import commands

class ForceSparkle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="forcesparkle", description="Force a sparkle reaction on a message.")
    async def forcesparkle(self, ctx, message_id: str, reaction_type: str):
        """
        Force a sparkle reaction on a message.
        """
        # Ignore messages from the bot itself and other bots
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

        # Fetch the message by ID
        try:
            message = await ctx.channel.fetch_message(int(message_id))
        except discord.NotFound:
            await ctx.send("Message not found. Make sure the message ID is correct and the message is in this channel.", ephemeral=True)
            return
        except discord.Forbidden:
            await ctx.send("I don't have permission to access that message.", ephemeral=True)
            return
        except ValueError:
            await ctx.send("Invalid message ID. Please provide a valid message ID.", ephemeral=True)
            return

        # Add the reaction
        emoji = valid_reactions[reaction_type.lower()]
        await message.add_reaction(emoji)

        # Update the leaderboard
        server_id = str(ctx.guild.id)
        user_id = str(message.author.id)

        # Initialize server data if it doesn't exist
        if server_id not in self.bot.sparkles:
            self.bot.sparkles[server_id] = {}
        if user_id not in self.bot.sparkles[server_id]:
            self.bot.sparkles[server_id][user_id] = {"epic": 0, "rare": 0, "regular": 0}

        # Increment the sparkle count
        self.bot.sparkles[server_id][user_id][reaction_type.lower()] += 1
        self.bot.save_sparkles(self.bot.sparkles)  # Save the updated data

        await ctx.send(f"Added {emoji} reaction")

async def setup(bot):
    await bot.add_cog(ForceSparkle(bot))