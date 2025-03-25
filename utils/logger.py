import time
import discord
from discord import Embed
from discord.ext import commands

class BotLogger:
    def __init__(self, bot=None, log_channel_id=None):
        self.bot = bot
        self.log_channel_id = log_channel_id
        self.start_time = time.time()
        self._is_restart = False

    def set_restart(self, restarting: bool):
        self._is_restart = restarting

    async def log(self, message: str, level: str = "info", alert: bool = False, embed: Embed = None):
        if not self.bot or not self.log_channel_id:
            print(f"Would log: {message}")  # Fallback print
            return
            
        try:
            # Fetch the channel fresh each time to ensure we have permissions
            channel = await self.bot.fetch_channel(self.log_channel_id)
            if not channel:
                print(f"Channel {self.log_channel_id} not found")
                return

            formats = {
                'info': ("📝 Info", 0x3498db),
                'warning': ("⚠️ Warning", 0xf39c12),
                'error': ("❌ Error", 0xe74c3c),
                'debug': ("🐛 Debug", 0x9b59b6),
                'critical': ("🚨 Critical", 0xe74c3c),
                'startup': ("🟢 Online", 0x2ecc71),
                'shutdown': ("🔴 Offline", 0xe74c3c),
                'restart': ("🟡 Restarting", 0xf1c40f)
            }
            
            header, color = formats.get(level.lower(), ("📌 Log", 0x7289da))
            
            if embed is None:
                embed = Embed(
                    title=header,
                    description=f"```{message[:2000]}```",
                    color=color
                )
            else:
                embed.color = color
                embed.title = f"{header} | {embed.title}" if embed.title else header
            
            embed.timestamp = discord.utils.utcnow()
            
            try:
                if alert:
                    await channel.send("@here", embed=embed)
                else:
                    await channel.send(embed=embed)
            except discord.Forbidden:
                print(f"Missing permissions to send messages in logging channel {self.log_channel_id}")
            except discord.HTTPException as e:
                print(f"Failed to send log message: {e}")
                
        except Exception as e:
            print(f"Logging failed completely: {e}")

    async def log_command_error(self, ctx, error):
        embed = Embed(
            title="Command Failed",
            color=0xe74c3c,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="Command",
            value=f"`{ctx.command}`" if ctx.command else "Unknown",
            inline=False
        )
        
        embed.add_field(
            name="User",
            value=f"{ctx.author.mention} (`{ctx.author.id}`)",
            inline=True
        )
        
        embed.add_field(
            name="Channel",
            value=ctx.channel.mention if hasattr(ctx.channel, 'mention') else "DM",
            inline=True
        )
        
        error_msg = str(error)[:1000]
        if isinstance(error, commands.CommandInvokeError):
            error_msg = f"{type(error.original).__name__}: {error_msg}"
        
        embed.add_field(
            name="Error",
            value=f"```{error_msg}```",
            inline=False
        )
        
        if ctx.guild:
            embed.set_footer(text=f"Guild: {ctx.guild.name} (ID: {ctx.guild.id})")
        
        await self.log("Command error occurred", level="error", embed=embed)