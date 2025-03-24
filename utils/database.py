import asqlite
from pathlib import Path

DB_PATH = Path("data/nova.db")

async def init_db():
    async with asqlite.connect(DB_PATH) as conn:
        async with conn.cursor() as cur:
            # Sparkles table
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
            
            # Server-specific XP
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS user_xp (
                    server_id TEXT,
                    user_id TEXT,
                    xp INTEGER DEFAULT 0,
                    PRIMARY KEY (server_id, user_id)
                )
            """)
            
            # Global coins
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS user_coins (
                    user_id TEXT PRIMARY KEY,
                    coins INTEGER DEFAULT 0
                )
            """)
            
            # Cooldowns table
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS cooldowns (
                    user_id TEXT PRIMARY KEY,
                    last_message_time REAL
                )
            """)
        await conn.commit()

async def get_connection():
    return await asqlite.connect(DB_PATH)