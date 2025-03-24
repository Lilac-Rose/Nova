import os
import json
import logging
import discord
import sys
import asqlite
import time
from pathlib import Path
from discord.ext import commands
from dotenv import load_dotenv
from config import pronouns, status
from logging.handlers import RotatingFileHandler
from datetime import datetime
import shutil

# Configure basic logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        RotatingFileHandler(LOG_DIR/'bot.log', maxBytes=5*1024*1024, backupCount=3),
        logging.StreamHandler()
    ]
)

# Add project root to Python path
sys.path.append(str(Path(__file__).parent))
load_dotenv()

# Paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "nova.db"

# Old JSON files
OLD_JSON_FILES = [
    Path("json/sparkles.json"),
    Path("json/xp.json"),
    Path("json/coins.json")
]

# Channel IDs
LOG_CHANNEL_ID = 1353840766694457454

class BotLogger:
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = LOG_CHANNEL_ID
        self.file_logger = logging.getLogger('nova')
    
    async def log(self, message: str, level: str = "info", alert: bool = False):
        """Log to both file and Discord channel"""
        # File logging
        getattr(self.file_logger, level.lower())(message)
        
        # Discord logging
        try:
            channel = self.bot.get_channel(self.log_channel_id)
            if channel:
                formats = {
                    'info': "📝 **Info**",
                    'warning': "⚠️ **Warning**",
                    'error': "❌ **Error**",
                    'debug': "🐛 **Debug**",
                    'critical': "🚨 **Critical**"
                }
                
                header = formats.get(level.lower(), "📌 **Log**")
                timestamp = f"<t:{int(time.time())}:T>"
                
                discord_msg = (
                    f"{header} {timestamp}\n"
                    f"```{message[:1800]}```"
                )
                
                if alert:
                    discord_msg = f"@here {discord_msg}"
                
                await channel.send(discord_msg)
        except Exception as e:
            self.file_logger.error(f"Failed to send log to Discord: {e}")

async def backup_old_json():
    """Backup old JSON files before migration"""
    backup_dir = Path("json/backups")
    backup_dir.mkdir(exist_ok=True)
    
    for json_file in OLD_JSON_FILES:
        if json_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"{timestamp}_{json_file.name}"
            shutil.copy2(json_file, backup_path)
            logging.info(f"Created backup of {json_file} at {backup_path}")

async def init_db(bot):
    """Initialize database with migration"""
    await backup_old_json()
    
    bot.db = await asqlite.create_pool(DB_PATH)
    
    async with bot.db.acquire() as conn:
        async with conn.cursor() as cur:
            # Create tables
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS sparkles (
                    server_id TEXT,
                    user_id TEXT,
                    epic INTEGER DEFAULT 0,
                    rare INTEGER DEFAULT 0,
                    regular INTEGER DEFAULT 0,
                    PRIMARY KEY (server_id, user_id)
                )
            """)
            
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS user_xp (
                    server_id TEXT,
                    user_id TEXT,
                    xp INTEGER DEFAULT 0,
                    PRIMARY KEY (server_id, user_id)
                )
            """)
            
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS user_coins (
                    user_id TEXT PRIMARY KEY,
                    coins INTEGER DEFAULT 0
                )
            """)
            
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS cooldowns (
                    user_id TEXT PRIMARY KEY,
                    last_message_time REAL
                )
            """)
            
            # Migration from JSON files
            if Path("json/sparkles.json").exists():
                with open("json/sparkles.json", "r") as f:
                    sparkles = json.load(f)
                    for server_id, users in sparkles.items():
                        for user_id, counts in users.items():
                            await cur.execute(
                                """INSERT INTO sparkles VALUES (?, ?, ?, ?, ?)
                                ON CONFLICT(server_id, user_id) DO UPDATE SET
                                epic = excluded.epic,
                                rare = excluded.rare,
                                regular = excluded.regular""",
                                (server_id, user_id, counts["epic"], counts["rare"], counts["regular"])
                            )
            
            if Path("json/xp.json").exists() and Path("json/coins.json").exists():
                with open("json/xp.json", "r") as f:
                    xp_data = json.load(f)
                with open("json/coins.json", "r") as f:
                    coins_data = json.load(f)
                
                for server_id, users in xp_data.items():
                    for user_id, xp in users.items():
                        await cur.execute(
                            """INSERT INTO user_xp VALUES (?, ?, ?)
                            ON CONFLICT(server_id, user_id) DO UPDATE SET
                            xp = excluded.xp""",
                            (server_id, user_id, xp)
                        )
                
                for user_id, coins in coins_data.items():
                    await cur.execute(
                        """INSERT INTO user_coins VALUES (?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET
                        coins = excluded.coins""",
                        (user_id, coins)
                    )
            
            await conn.commit()
    
    await bot.logger.log("✅ Database initialized successfully")

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_initialized = False
        self.db = None
        self.logger = None

    async def setup_hook(self):
        """Initialize bot components"""
        self.logger = BotLogger(self)
        await self.logger.log("🔄 Starting bot initialization...")
        
        try:
            # Initialize database
            await init_db(self)
            self.db_initialized = True
            
            # Load command logger first
            await self.load_extension("events.command_logger")
            
            # Load other extensions
            await self.load_extensions()
            
            await self.logger.log("🚀 Bot initialization complete!")
            
        except Exception as e:
            await self.logger.log(f"❌ Initialization failed: {str(e)}", level="error", alert=True)
            raise

    async def load_extensions(self):
        """Load all bot extensions"""
        for folder in ["commands", "events", "tasks"]:
            for filename in os.listdir(f"./{folder}"):
                if filename.endswith(".py") and filename != "__init__.py" and filename != "command_logger.py":
                    ext_name = f"{folder}.{filename[:-3]}"
                    try:
                        await self.load_extension(ext_name)
                        await self.logger.log(f"✓ Loaded {ext_name}", level="debug")
                    except Exception as e:
                        await self.logger.log(
                            f"✗ Failed to load {ext_name}: {type(e).__name__}: {e}", 
                            level="warning"
                        )

    async def close(self):
        """Cleanup when bot closes"""
        await self.logger.log("🛑 Bot shutting down...")
        if self.db:
            await self.db.close()
        await super().close()

# Configure intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.guilds = True

bot = MyBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Called when bot connects to Discord"""
    await bot.logger.log(f"👋 Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.logger.log(f"🌐 Connected to {len(bot.guilds)} guilds")
    
    # Update presence
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{status} | Pronouns: {pronouns}"
        ),
        status=discord.Status.online
    )

token = os.getenv('TOKEN')
if not token:
    logging.error("The 'TOKEN' environment variable is not set.")
    sys.exit(1)

if __name__ == "__main__":
    bot.run(token)