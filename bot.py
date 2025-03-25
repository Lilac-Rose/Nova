import os
import time
import signal
import discord
from discord.ext import commands
from dotenv import load_dotenv
from config import pronouns, status
from utils.logger import BotLogger
from utils.database import init_db, close_pool

load_dotenv()

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = None
        self.logger = None
        self._restart_requested = False
        signal.signal(signal.SIGTERM, self.handle_signal)

    def handle_signal(self, signum, frame):
        self._restart_requested = True
        if self.logger:
            self.logger.set_restart(True)

    async def load_extensions(self):
        """Auto-load all extensions from folders"""
        folders = ["commands", "events", "tasks"]
        for folder in folders:
            for filename in os.listdir(folder):
                if filename.endswith(".py") and not filename.startswith("_"):
                    try:
                        await self.load_extension(f"{folder}.{filename[:-3]}")
                    except Exception as e:
                        if self.logger:
                            await self.logger.log(
                                f"Failed to load {folder}.{filename[:-3]}: {e}",
                                level="error"
                            )

    async def setup_hook(self):
        self.logger = BotLogger(self, log_channel_id=1353840766694457454)
        
        # Initialize database first
        try:
            self.db = await init_db("data/nova.db")
            await self.logger.log("Database initialized", level="info")
        except Exception as e:
            await self.logger.log(f"Database failed: {e}", level="error", alert=True)
            raise

        # Load all extensions
        await self.load_extensions()
        
        # Startup message
        startup_msg = (
            f"**Bot {'restarted' if self._restart_requested else 'started'}**\n"
            f"• User: {self.user}\n"
            f"• Guilds: {len(self.guilds)}"
        )
        await self.logger.log(startup_msg, level="startup")
        self._restart_requested = False

    async def close(self):
        if not self._restart_requested:
            uptime = time.time() - self.logger.start_time
            hours, remainder = divmod(uptime, 3600)
            minutes, seconds = divmod(remainder, 60)
            await self.logger.log(
                f"**Shutting down**\nUptime: {int(hours)}h {int(minutes)}m {int(seconds)}s",
                level="shutdown"
            )
        
        await close_pool()
        await super().close()

# Configure intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.guilds = True

bot = MyBot(
    command_prefix="!",
    intents=intents,
    activity=discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{status} | Pronouns: {pronouns}"
    )
)

if __name__ == "__main__":
    bot.run(os.getenv('TOKEN'))