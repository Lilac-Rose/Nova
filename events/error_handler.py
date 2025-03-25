from discord.ext import commands
from discord import Embed

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return
            
        error = getattr(error, 'original', error)
        
        await self.bot.logger.log_command_error(ctx, error)
        
        user_message = "❌ An error occurred"
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            user_message = "❌ You don't have permission to use this command"
        elif isinstance(error, commands.BotMissingPermissions):
            user_message = "❌ I don't have permission to do that"
        elif isinstance(error, commands.CheckFailure):
            user_message = "❌ You can't use this command"
        
        await ctx.send(user_message, delete_after=10)

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))