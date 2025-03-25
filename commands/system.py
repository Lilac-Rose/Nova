import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
import time

log = logging.getLogger('nova')

class SystemCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = 252130669919076352  # Your Discord ID

    async def is_owner(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.owner_id

    @commands.hybrid_command(name="reload_commands")
    @app_commands.check(is_owner)
    async def reload_commands(self, ctx: commands.Context):
        """Reload all bot commands without restarting (Owner only)"""
        try:
            extensions = list(self.bot.extensions.keys())
            success = []
            failed = []
            
            for ext in extensions:
                try:
                    await self.bot.reload_extension(ext)
                    success.append(ext)
                except Exception as e:
                    failed.append(f"{ext}: {str(e)}")
            
            message = "✅ Reload complete!\n"
            if success:
                message += f"• Reloaded: {len(success)} commands\n"
            if failed:
                message += f"• Failed: {', '.join(failed)}"
            
            await ctx.send(message, ephemeral=True)
            log.info(f"Commands reloaded: {len(success)} success, {len(failed)} failed")
        except Exception as e:
            await ctx.send(f"❌ Critical reload error: {str(e)}", ephemeral=True)
            log.error(f"Command reload failed: {e}")

    @commands.hybrid_command(name="announce")
    @commands.is_owner()
    async def make_announcement(self, ctx, *, message):
        """Send an announcement to the log channel (Owner only)"""
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