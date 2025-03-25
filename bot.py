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
        """Load all Python files in commands, events, and tasks folders"""
        folders = ["commands", "events", "tasks"]
        loaded = 0
        failed = 0
        
        for folder in folders:
            if not os.path.exists(folder):
                continue
                
            for filename in os.listdir(folder):
                if filename.endswith(".py") and not filename.startswith("_"):
                    ext_name = f"{folder}.{filename[:-3]}"
                    try:
                        await self.load_extension(ext_name)
                        loaded += 1
                    except Exception as e:
                        failed += 1
                        await self.logger.log(
                            f"Failed to load {ext_name}: {type(e).__name__}: {e}",
                            level="error"
                        )
        
        return loaded, failed

    async def setup_hook(self):
        # Initialize logger
        self.logger = BotLogger(self, log_channel_id=1353840766694457454)
        
        # Initialize database
        try:
            self.db = await init_db("data/nova.db")
            await self.logger.log("Database initialized", level="info")
        except Exception as e:
            await self.logger.log(f"Database init failed: {e}", level="error", alert=True)
            raise

        # Load extensions
        loaded, failed = await self.load_extensions()
        await self.logger.log(f"Loaded {loaded} extensions successfully", level="info")
        
        # Startup message
        startup_msg = (
            f"**Bot {'restarted' if self._restart_requested else 'started'}**\n"
            f"• User: {self.user}\n"
            f"• ID: {self.user.id}\n"
            f"• Guilds: {len(self.guilds)}"
        )
        await self.logger.log(startup_msg, level="startup")
        self._restart_requested = False

    async def close(self):
        if not self._restart_requested:
            uptime = time.time() - self.logger.start_time
            hours, remainder = divmod(uptime, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            shutdown_msg = (
                f"**Bot shutting down**\n"
                f"• Uptime: {int(hours)}h {int(minutes)}m {int(seconds)}s\n"
                f"• Guilds: {len(self.guilds)}"
            )
            await self.logger.log(shutdown_msg, level="shutdown")
        else:
            await self.logger.log("Bot restarting...", level="restart")
        
        await close_pool()
        await super().close()

# Configure intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.guilds = True
intents.reactions = True

bot = MyBot(
    command_prefix="!",
    intents=intents,
    activity=discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{status} | Pronouns: {pronouns}"
    )
)

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{status} | Pronouns: {pronouns}"
        )
    )

if __name__ == "__main__":
    bot.run(os.getenv('TOKEN'))