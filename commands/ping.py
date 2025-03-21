import discord
from discord.ext import commands

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Ping the bot to get the delay")
    @commands.cooldown(1, 30, commands.BucketType.guild)  # 30-second cooldown per server
    async def ping(self, ctx: commands.Context):
        """
        Responds with the bot's latency in an embed.
        """
        latency = round(self.bot.latency * 1000)  # Convert to milliseconds

        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Delay: **{latency}ms**",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)

        await ctx.send(embed=embed)

    @ping.error
    async def ping_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Handles errors for the ping command, specifically cooldown errors.
        """
        if isinstance(error, commands.CommandOnCooldown):
            # Send a message when the command is on cooldown
            await ctx.send(
                f"Slow down! You can use this command again in **{error.retry_after:.1f} seconds**. 🕒",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Ping(bot))
