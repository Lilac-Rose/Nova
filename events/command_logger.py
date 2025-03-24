import discord
from discord.ext import commands
import logging
import time

class CommandLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger('nova.commands')

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Logs when any command is invoked"""
        try:
            # Get command arguments
            args = " ".join([str(arg) for arg in ctx.args[2:]])  # Skip self and ctx
            kwargs = " ".join([f"{k}={v}" for k,v in ctx.kwargs.items()])
            
            await self.bot.logger.log(
                f"⚡ Command executed: {ctx.command.qualified_name}\n"
                f"User: {ctx.author} (ID: {ctx.author.id})\n"
                f"Server: {ctx.guild.name if ctx.guild else 'DM'}\n"
                f"Channel: {ctx.channel.name if hasattr(ctx.channel, 'name') else 'DM'}\n"
                f"Arguments: {args} {kwargs}",
                level="info"
            )
        except Exception as e:
            await self.bot.logger.log(
                f"❌ Command logging failed: {str(e)}",
                level="error"
            )

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        """Logs when a command completes successfully"""
        try:
            await self.bot.logger.log(
                f"✅ Command completed: {ctx.command.qualified_name}\n"
                f"User: {ctx.author} (ID: {ctx.author.id})",
                level="debug"
            )
        except Exception as e:
            await self.bot.logger.log(
                f"❌ Completion logging failed: {str(e)}",
                level="error"
            )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Logs when a command fails"""
        try:
            await self.bot.logger.log(
                f"❌ Command failed: {ctx.command.qualified_name}\n"
                f"User: {ctx.author} (ID: {ctx.author.id})\n"
                f"Error: {str(error)}",
                level="error",
                alert=True
            )
        except Exception as e:
            await self.bot.logger.log(
                f"❌ Error logging failed: {str(e)}",
                level="error"
            )

async def setup(bot):
    await bot.add_cog(CommandLogger(bot))