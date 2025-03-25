import random
from typing import Tuple

# Configuration
XP_PER_MESSAGE = (5, 15)  # min, max
BASE_XP_NEEDED = 100
XP_MULTIPLIER = 1.2
LEVEL_UP_BONUS = 100

def calculate_level(xp: int) -> Tuple[int, int]:
    """Calculate current level and progress to next level"""
    level = 0
    xp_needed = BASE_XP_NEEDED
    while xp >= xp_needed:
        xp -= xp_needed
        level += 1
        xp_needed = int(xp_needed * XP_MULTIPLIER)
    return level, xp

def xp_for_next_level(level: int) -> int:
    """Calculate XP needed for the next level"""
    if level == 0:
        return BASE_XP_NEEDED
    return int(BASE_XP_NEEDED * (XP_MULTIPLIER ** level))

async def add_xp(db, user_id: str, server_id: str) -> Tuple[int, bool]:
    """
    Add XP to user and check for level up
    Returns: (new_level, leveled_up)
    """
    xp_gain = random.randint(*XP_PER_MESSAGE)
    
    async with db.acquire() as conn:
        async with conn.cursor() as cur:
            # Update XP
            await cur.execute(
                """INSERT INTO user_xp (server_id, user_id, xp)
                VALUES (?, ?, ?)
                ON CONFLICT(server_id, user_id) DO UPDATE SET
                xp = xp + excluded.xp
                RETURNING xp""",
                (server_id, user_id, xp_gain)
            )
            
            result = await cur.fetchone()
            new_xp = result[0]
            
            # Update coins
            await cur.execute(
                """INSERT INTO user_coins (user_id, coins)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                coins = coins + excluded.coins""",
                (user_id, xp_gain)
            )
            
            # Check level up
            old_level = calculate_level(new_xp - xp_gain)[0]
            new_level = calculate_level(new_xp)[0]
            
            if new_level > old_level:
                bonus = LEVEL_UP_BONUS * (new_level - old_level)
                await cur.execute(
                    "UPDATE user_coins SET coins = coins + ? WHERE user_id = ?",
                    (bonus, user_id)
                )
                await conn.commit()
                return (new_level, True)
            
            await conn.commit()
            return (new_level, False)