import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
from utils.database import close_pool, init_db

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
        """Reload ALL extensions (commands + events + tasks) safely"""
        try:
            # Close existing connections
            await close_pool()
            
            # Reload all extensions
            extensions = list(self.bot.extensions.keys())
            success = []
            failed = []
            
            for ext in extensions:
                try:
                    await self.bot.reload_extension(ext)
                    success.append(ext.split('.')[0])  # Get category name
                except Exception as e:
                    failed.append(f"{ext}: {str(e)}")
            
            # Reinitialize database
            self.bot.db = await init_db("data/nova.db")
            
            # Build response
            message = "🔄 Reload Results:\n"
            if success:
                message += f"✅ {len(success)} extensions in {len(set(success))} categories\n"
            if failed:
                message += f"❌ Failed: {len(failed)}\n```{'\n'.join(failed)}```"
            
            await ctx.send(message, ephemeral=True)
            log.info(f"Reloaded {len(success)} extensions")

        except Exception as e:
            await ctx.send(f"💥 Critical error: {str(e)}", ephemeral=True)
            log.error(f"Reload failed: {e}")
            
            # Emergency reconnect
            try:
                self.bot.db = await init_db("data/nova.db")
            except Exception as db_error:
                log.critical(f"Database reconnect failed: {db_error}")

    @commands.hybrid_command(name="announce")
    @commands.is_owner()
    async def make_announcement(self, ctx, *, message):
        """Send an announcement to the log channel"""
        try:
            channel = self.bot.get_channel(1353840766694457454)
            if channel:
                await channel.send(f"📣 **Announcement**: {message}")
                await ctx.send("✅ Announcement posted", ephemeral=True)
            else:
                await ctx.send("❌ Log channel not found", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Failed: {e}", ephemeral=True)
            log.error(f"Announcement failed: {e}")

    @commands.hybrid_command(name="logs")
    @commands.is_owner()
    async def get_logs(self, ctx, lines: int = 20):
        """Get recent logs"""
        try:
            with open("logs/bot.log", "r") as f:
                log_lines = f.readlines()[-lines:]
            await ctx.send(f"```\n{''.join(log_lines)}\n```", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Error: {e}", ephemeral=True)
            log.error(f"Log retrieval failed: {e}")

async def setup(bot):
    await bot.add_cog(SystemCommands(bot))