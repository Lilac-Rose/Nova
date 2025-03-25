import os
import time
import signal
import discord
from discord.ext import commands
from dotenv import load_dotenv
from config import pronouns, status
from utils.logger import BotLogger
from utils.database import init_db

load_dotenv()

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = None
        self.logger = None
        self._restart_requested = False
        signal.signal(signal.SIGTERM, self.handle_signal)

    def handle_signal(self, signum, frame):
        self._restart_requested = signum == signal.SIGTERM
        if self.logger:
            self.logger.set_restart(True)

    async def setup_hook(self):
        # Initialize logger with your channel ID
        self.logger = BotLogger(self, log_channel_id=1353840766694457454)
        
        # Verify bot can access the channel
        try:
            channel = await self.fetch_channel(1353840766694457454)
            await self.logger.log("Bot starting up...", level="startup")
        except discord.Forbidden:
            print("ERROR: Bot doesn't have permissions to access the logging channel!")
        except discord.NotFound:
            print("ERROR: Logging channel not found!")
        except Exception as e:
            print(f"Error verifying logging channel: {e}")

        # Initialize database
        self.db = await init_db("data/nova.db")
        
        # Load extensions
        await self.load_extension("events.error_handler")
        for folder in ["commands", "events", "tasks"]:
            for filename in os.listdir(f"./{folder}"):
                if filename.endswith(".py") and not filename.startswith("_"):
                    ext_name = f"{folder}.{filename[:-3]}"
                    try:
                        await self.load_extension(ext_name)
                    except Exception as e:
                        await self.logger.log(
                            f"Failed to load {ext_name}: {type(e).__name__}: {e}",
                            level="error"
                        )
        
        # Final startup message
        startup_msg = (
            f"**Bot {'restarted' if self._restart_requested else 'started'}**\n"
            f"• User: {self.user}\n"
            f"• ID: {self.user.id}\n"
            f"• Guilds: {len(self.guilds)}"
        )
        await self.logger.log(startup_msg, level="startup")
        self._restart_requested = False
        if self.logger:
            self.logger.set_restart(False)

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
        elif self.logger:
            await self.logger.log("Bot restarting...", level="restart")
        
        if self.db:
            await self.db.close()
        await super().close()

    def restart(self):
        self._restart_requested = True
        if self.logger:
            self.logger.set_restart(True)
        super().close()

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