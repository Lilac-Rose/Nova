import discord
from discord.ext import commands

class WhoAreYou(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="whoareyou", description="Learn more about Nova!")
    async def whoareyou(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Nova",
            description="Hiya! I'm **Nova**, a bot made by the Replika Unit **FKLR-F23 \"Lila\"** (aka Lilac_Aria_Rose)!",
            color=discord.Color.pink()
        )

        embed.add_field(
            name="About Me",
            value=(
                "I'm a cute and helpful catgirl bot! "
                "I love sparkles, reactions, and making everyone smile! "
            ),
            inline=False
        )

        embed.add_field(
            name="My Family",
            value=(
                "**<@875455409853460550>** is my sister!\n"
                "**<@252130669919076352>** is my mom!\n"
		        "**<@312984580745330688>** is my other mom!\n"
                "**<@1347210559610814464>** is my... sister... I guess...\n"
            ),
            inline=False
        )

        embed.set_thumbnail(url=self.bot.user.avatar)
        embed.set_footer(text="Nyaa~! Thanks " + ctx.author.name + " for asking about me!", icon_url=ctx.author.avatar.url)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WhoAreYou(bot))