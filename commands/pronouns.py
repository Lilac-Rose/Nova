from discord.ext import commands
from discord import app_commands
from config import pronouns

class Pronouns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="pronouns", description="Display the bot's pronouns.")
    async def pronouns(self, ctx):
        await ctx.send(f"My pronouns are {pronouns}!")

async def setup(bot):
    await bot.add_cog(Pronouns(bot))