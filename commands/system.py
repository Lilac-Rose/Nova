import discord
import random
import logging
from discord.ext import commands
from discord import app_commands
from typing import Optional
from utils.database import init_db, close_pool


log = logging.getLogger('nova')

class SystemCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = 252130669919076352

    async def is_owner(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.owner_id

    @commands.hybrid_command(name="sync_commands")
    @app_commands.check(is_owner)
    async def sync(self, ctx: commands.Context):
        await ctx.bot.tree.sync()
        await ctx.send("Slash commands synced!")

    @commands.hybrid_command(name="reload_commands")
    @app_commands.check(is_owner)
    async def reload_commands(self, ctx: commands.Context):
        """Reload ALL extensions (commands + events + tasks) safely"""
        try:
            await close_pool()
            
            extensions = list(self.bot.extensions.keys())
            success = []
            failed = []
            
            for ext in extensions:
                try:
                    await self.bot.reload_extension(ext)
                    success.append(ext.split('.')[0])
                except Exception as e:
                    failed.append(f"{ext}: {str(e)}")
            
            self.bot.db_pool = await init_db("data/nova.db")
            
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
            
            try:
                self.bot.db_pool = await init_db("data/nova.db")
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

    @commands.hybrid_command(name="blacklist")
    @app_commands.check(is_owner)
    async def blacklist_user(self, ctx, user: discord.User, *, reason: Optional[str] = None):
        """Add a user to the bot blacklist"""
        try:
            await self.bot.add_to_blacklist(user.id)
            
            async with self.bot.db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """INSERT INTO blacklist (user_id, reason, created_at) 
                        VALUES (?, ?, datetime('now'))""",
                        (str(user.id), reason or "No reason provided")
                    )
                    await conn.commit()
            
            log_msg = f"Blacklisted {user} ({user.id})"
            if reason:
                log_msg += f" | Reason: {reason}"
                
            await ctx.send(f"✅ Successfully blacklisted {user.mention}", ephemeral=True)
            await self.bot.logger.log(log_msg, level="moderation")
            
        except Exception as e:
            await ctx.send(f"❌ Failed to blacklist: {str(e)}", ephemeral=True)
            log.error(f"Blacklist error: {e}", exc_info=True)

    @commands.hybrid_command(name="unblacklist")
    @app_commands.check(is_owner)
    async def unblacklist_user(self, ctx, user: discord.User):
        """Remove a user from the blacklist"""
        try:
            await self.bot.remove_from_blacklist(user.id)
            
            async with self.bot.db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "DELETE FROM blacklist WHERE user_id = ?",
                        (str(user.id),)
                    )
                    await conn.commit()
            
            await ctx.send(f"✅ Successfully unblacklisted {user.mention}", ephemeral=True)
            await self.bot.logger.log(
                f"Unblacklisted {user} ({user.id})", 
                level="moderation"
            )
                
        except Exception as e:
            await ctx.send(f"❌ Failed to unblacklist: {str(e)}", ephemeral=True)
            log.error(f"Unblacklist error: {e}", exc_info=True)

    @commands.hybrid_command(name="blacklist_info")
    @app_commands.check(is_owner)
    async def blacklist_info(self, ctx, user: Optional[discord.User] = None):
        """View blacklist information"""
        try:
            async with self.bot.db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    if user:
                        await cur.execute(
                            """SELECT reason, created_at 
                            FROM blacklist 
                            WHERE user_id = ?""",
                            (str(user.id),)
                        )
                        row = await cur.fetchone()
                        
                        if row:
                            reason, created_at = row
                            embed = discord.Embed(
                                title=f"Blacklist Info for {user}",
                                color=discord.Color.red()
                            )
                            embed.add_field(name="User ID", value=user.id, inline=False)
                            embed.add_field(name="Reason", value=reason or "Not specified", inline=False)
                            embed.add_field(name="Blacklisted Since", value=created_at, inline=False)
                        else:
                            embed = discord.Embed(
                                title="Not Blacklisted",
                                description=f"{user} is not in the blacklist",
                                color=discord.Color.green()
                            )
                        await ctx.send(embed=embed, ephemeral=True)
                    else:
                        await cur.execute(
                            """SELECT user_id, reason, created_at 
                            FROM blacklist 
                            ORDER BY created_at DESC"""
                        )
                        rows = await cur.fetchall()
                        
                        if not rows:
                            return await ctx.send("No users are currently blacklisted", ephemeral=True)
                        
                        embed = discord.Embed(
                            title=f"Blacklisted Users ({len(rows)})",
                            color=discord.Color.orange()
                        )
                        
                        for user_id, reason, created_at in rows:
                            user = self.bot.get_user(int(user_id))
                            embed.add_field(
                                name=f"{user or 'Unknown User'} ({user_id})",
                                value=f"**Reason:** {reason or 'Not specified'}\n"
                                      f"**Since:** {created_at}",
                                inline=False
                            )
                        
                        await ctx.send(embed=embed, ephemeral=True)
                        
        except Exception as e:
            await ctx.send(f"❌ Error retrieving blacklist info: {str(e)}", ephemeral=True)
            log.error(f"Blacklist info error: {e}", exc_info=True)

async def setup(bot):
    await bot.add_cog(SystemCommands(bot))