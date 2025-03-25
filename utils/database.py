import asqlite
from pathlib import Path

_pool = None

async def get_connection():
    """Get a database connection from the pool"""
    global _pool
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db() first.")
    return await _pool.acquire()

async def init_db(db_path: str):
    """Initialize database with connection pool and tables"""
    global _pool
    _pool = await asqlite.create_pool(db_path)
    
    async with await get_connection() as conn:
        async with conn.cursor() as cur:
            # First check if old blacklist table exists without created_at
            await cur.execute("PRAGMA table_info(blacklist)")
            columns = [col[1] for col in await cur.fetchall()]
            
            # If table exists but is missing columns
            if columns and 'created_at' not in columns:
                # Create temporary backup
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS blacklist_backup AS 
                    SELECT * FROM blacklist
                """)
                # Drop old table
                await cur.execute("DROP TABLE IF EXISTS blacklist")
                await conn.commit()

            # Create all tables with current schema
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
            
            # Create blacklist table with all columns
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS blacklist (
                    user_id TEXT PRIMARY KEY,
                    reason TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    return _pool

async def close_pool():
    """Safely close all connections"""
    global _pool
    if _pool and not _pool._closed:
        await _pool.close()
    _pool = None