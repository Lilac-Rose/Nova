import os
import time
import signal
import random
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
        self.db_pool = None
        self.logger = None
        self._restart_requested = False
        self._blacklisted_users = set()
        signal.signal(signal.SIGTERM, self.handle_signal)

    @property
    def blacklisted_users(self):
        return self._blacklisted_users.copy()

    async def add_to_blacklist(self, user_id: int):
        self._blacklisted_users.add(user_id)

    async def remove_from_blacklist(self, user_id: int):
        self._blacklisted_users.discard(user_id)

    async def is_not_blacklisted(self, ctx):
        if ctx.author.id in self._blacklisted_users:
            fake_errors = [
                "Command timed out. Please try again later.",
                "An error occurred while processing your command.",
                "This command is currently unavailable.",
                "Rate limited. Please wait before using this command again."
            ]
            await ctx.send(random.choice(fake_errors), ephemeral=True)
            return False
        return True

    def handle_signal(self, signum, frame):
        self._restart_requested = True
        if self.logger:
            self.logger.set_restart(True)

    async def setup_hook(self):
        self.add_check(self.is_not_blacklisted)
        self.logger = BotLogger(self, log_channel_id=1353840766694457454)
        
        try:
            self.db_pool = await init_db("data/nova.db")
            
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT user_id FROM blacklist")
                    rows = await cur.fetchall()
                    self._blacklisted_users.update(int(row[0]) for row in rows)
            
            await self.logger.log(
                f"Loaded {len(self._blacklisted_users)} blacklisted users", 
                level="info"
            )
            
            folders = ["commands", "events", "tasks"]
            for folder in folders:
                for filename in os.listdir(folder):
                    if filename.endswith(".py") and not filename.startswith("_"):
                        try:
                            await self.load_extension(f"{folder}.{filename[:-3]}")
                        except Exception as e:
                            await self.logger.log(
                                f"Failed to load {folder}.{filename[:-3]}: {e}",
                                level="error"
                            )

            startup_msg = (
                f"**Bot {'restarted' if self._restart_requested else 'started'}**\n"
                f"• User: {self.user}\n"
                f"• Guilds: {len(self.guilds)}\n"
                f"• Blacklisted users: {len(self._blacklisted_users)}"
            )
            await self.logger.log(startup_msg, level="startup")
            self._restart_requested = False

        except Exception as e:
            await self.logger.log(
                f"Startup failed: {e}", 
                level="error", 
                alert=True
            )
            raise

    async def close(self):
        if not self._restart_requested:
            uptime = time.time() - self.logger.start_time
            await self.logger.log(
                f"**Shutting down**\nUptime: {uptime:.2f} seconds",
                level="shutdown"
            )
        await close_pool()
        await super().close()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = MyBot(
    command_prefix="++",
    intents=intents,
    activity=discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{status} | Pronouns: {pronouns}"
    )
)

if __name__ == "__main__":
    bot.run(os.getenv('TOKEN'))