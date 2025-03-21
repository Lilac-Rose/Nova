# commands/whoareyou.py
import discord
from discord.ext import commands

class WhoAreYou(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="whoareyou", description="Learn more about Nova!")
    async def whoareyou(self, ctx: commands.Context):
        # Create an embed
        embed = discord.Embed(
            title="Nyaa~!",
            description="Hiya! I'm **Nova**, a bot made by the Replika Unit **FKLR-F23 \"Lila\"** (aka Lilac_Aria_Rose)!",
            color=discord.Color.pink()
        )

        # Add fields for more information
        embed.add_field(
            name="About Me",
            value=(
                "I'm a cute and helpful catgirl bot! "
                "I love sparkles, reactions, and making everyone smile! "
                "Nyaa~!"
            ),
            inline=False
        )

        embed.add_field(
            name="My Family",
            value=(
                "**<@875455409853460550>** is my sister!\n"
                "**<@312984580745330688>** is my mom!\n"
		        "**<@252130669919076352>** is my other mom!\n"
                "We're a happy little family!"
            ),
            inline=False
        )

        # Set a footer
        embed.set_footer(text="Nyaa~! Thanks for asking about me! 🐾", icon_url=ctx.author.avatar.url)

        # Send the embed
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WhoAreYou(bot))
