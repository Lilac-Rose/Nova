import asqlite
from pathlib import Path

async def init_db(db_path: str):
    """Initialize database with clean tables"""
    db = await asqlite.create_pool(db_path)
    
    async with db.acquire() as conn:
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
                    level INTEGER DEFAULT 1,
                    last_message_time REAL,
                    PRIMARY KEY (server_id, user_id)
                )
            """)
            
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS user_coins (
                    user_id TEXT PRIMARY KEY,
                    coins INTEGER DEFAULT 0
                )
            """)
            
            await conn.commit()
    
    return db