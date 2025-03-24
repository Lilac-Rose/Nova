import logging
from discord.ext import commands
from typing import Optional
from pathlib import Path

class BotLogger:
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1353840766694457454  # Your log channel ID
        self.file_logger = logging.getLogger('nova')
        
        # Configure file logging
        self._setup_file_logging()
    
    def _setup_file_logging(self):
        """Configure file-based logging"""
        LOG_DIR = Path("logs")
        LOG_DIR.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(LOG_DIR/'bot.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s'
        ))
        self.file_logger.addHandler(file_handler)

    async def log(self, message: str, level: str = "info", alert: bool = False):
        """
        Log messages to both file and Discord channel
        :param message: The message to log
        :param level: Log level (info, warning, error, debug)
        :param alert: Whether to @here in Discord for important messages
        """
        # Log to file
        getattr(self.file_logger, level.lower())(message)
        
        # Log to Discord channel
        try:
            channel = self.bot.get_channel(self.log_channel_id)
            if channel:
                prefix = {
                    'info': 'ℹ️',
                    'warning': '⚠️',
                    'error': '❌',
                    'debug': '🐛'
                }.get(level.lower(), '📝')
                
                discord_msg = f"{prefix} {message[:1900]}"  # Truncate to avoid overflow
                if alert:
                    discord_msg = f"@here {discord_msg}"
                
                await channel.send(discord_msg)
        except Exception as e:
            self.file_logger.error(f"Failed to send log to Discord: {e}")

def setup_activity_log():
    """Setup the activity logger"""
    activity_log = logging.getLogger('activity')
    activity_log.setLevel(logging.INFO)
    activity_log.propagate = False
    
    LOG_DIR = Path("logs")
    LOG_DIR.mkdir(exist_ok=True)
    
    handler = logging.FileHandler(LOG_DIR/'activity.log')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    activity_log.addHandler(handler)
    return activity_log

async def log_command(ctx: commands.Context):
    """Log command execution details"""
    activity_log = logging.getLogger('activity')
    guild_info = f"{ctx.guild.name} ({ctx.guild.id})" if ctx.guild else 'DM'
    activity_log.info(
        f"COMMAND: {ctx.command.qualified_name} | "
        f"User: {ctx.author} ({ctx.author.id}) | "
        f"Server: {guild_info} | "
        f"Args: {ctx.kwargs}"
    )

def log_xp_event(user: discord.User, xp_gain: int, new_xp: int, level_up: bool = False):
    """Log XP-related events"""
    activity_log = logging.getLogger('activity')
    activity_log.info(
        f"XP: {user} ({user.id}) | "
        f"Gained: +{xp_gain} XP | "
        f"Total: {new_xp} XP | "
        f"Level Up: {'Yes' if level_up else 'No'} | "
        f"Server: {user.guild.name if hasattr(user, 'guild') and user.guild else 'DM'}"
    )

def log_coins_event(user: discord.User, coins_change: int, new_balance: int, reason: str):
    """Log coins transactions"""
    activity_log = logging.getLogger('activity')
    activity_log.info(
        f"COINS: {user} ({user.id}) | "
        f"Change: {coins_change:+} coins | "
        f"New Balance: {new_balance} | "
        f"Reason: {reason}"
    )