import discord
from discord.ext import commands
import logging

log = logging.getLogger('nova')

class SystemCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="announce")
    @commands.is_owner()
    async def make_announcement(self, ctx, *, message):
        """Send an announcement to the log channel"""
        try:
            channel = self.bot.get_channel(1353840766694457454)
            if channel:
                await channel.send(f"📣 **Announcement**: {message}")
                await ctx.send("✅ Announcement posted to log channel")
            else:
                await ctx.send("❌ Log channel not found")
        except Exception as e:
            await ctx.send(f"❌ Failed to send announcement: {e}")
            log.error(f"Announcement failed: {e}")

    @commands.hybrid_command(name="logs")
    @commands.is_owner()
    async def get_logs(self, ctx, lines: int = 20):
        """Get recent logs (Owner only)"""
        try:
            with open("logs/bot.log", "r") as f:
                log_lines = f.readlines()[-lines:]
            await ctx.send(f"```\n{''.join(log_lines)}\n```")
        except Exception as e:
            await ctx.send(f"❌ Error getting logs: {e}")
            log.error(f"Log retrieval failed: {e}")

async def setup(bot):
    await bot.add_cog(SystemCommands(bot))