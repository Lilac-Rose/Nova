import discord
from discord.ext import commands
from discord import app_commands
import logging
import os

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
        """Reload ALL bot extensions (commands + events + tasks) without restarting (Owner only)"""
        try:
            # Get current extensions
            extensions = list(self.bot.extensions.keys())
            success = []
            failed = []
            
            # Reload everything
            for ext in extensions:
                try:
                    await self.bot.reload_extension(ext)
                    category = ext.split('.')[0]  # Get folder name
                    success.append(category)
                except Exception as e:
                    failed.append(f"{ext}: {str(e)}")
            
            # Build result message
            message = "🔄 Reload Results:\n"
            if success:
                unique_categories = set(success)
                message += f"✅ Reloaded {len(success)} extensions across {len(unique_categories)} categories: {', '.join(unique_categories)}\n"
            if failed:
                message += f"❌ Failed {len(failed)}:\n```{'\n'.join(failed)}```"
            
            await ctx.send(message, ephemeral=True)
            log.info(f"Reloaded {len(success)} extensions, failed {len(failed)}")

        except Exception as e:
            await ctx.send(f"💥 Critical reload error: {str(e)}", ephemeral=True)
            log.error(f"Full reload failed: {e}")

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