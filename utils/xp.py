import random
from typing import Tuple

# Configuration
XP_PER_MESSAGE = (5, 15)  # min, max XP per message
BASE_XP_NEEDED = 100
XP_MULTIPLIER = 1.2
LEVEL_UP_BONUS = 100

def calculate_level(xp: int) -> Tuple[int, int]:
    """
    Calculate current level and XP progress to next level
    Returns: (current_level, xp_into_current_level)
    """
    level = 0
    xp_needed = BASE_XP_NEEDED
    while xp >= xp_needed:
        xp -= xp_needed
        level += 1
        xp_needed = int(xp_needed * XP_MULTIPLIER)
    return level, xp

def xp_for_next_level(level: int) -> int:
    """
    Calculate total XP needed to reach the next level
    Example: xp_for_next_level(0) -> 100 (base)
             xp_for_next_level(1) -> 120 (100 * 1.2)
             xp_for_next_level(2) -> 144 (120 * 1.2)
    """
    if level < 0:
        return BASE_XP_NEEDED
    return int(BASE_XP_NEEDED * (XP_MULTIPLIER ** level))

def xp_for_level(level: int) -> int:
    """
    Calculate total XP needed to reach a specific level
    (Sum of XP needed for all previous levels)
    """
    total = 0
    current_requirement = BASE_XP_NEEDED
    for _ in range(level):
        total += current_requirement
        current_requirement = int(current_requirement * XP_MULTIPLIER)
    return total

def calculate_level_progress(xp: int) -> Tuple[int, int, int]:
    """
    Calculate level information for display
    Returns: (current_level, progress_percentage, xp_needed_for_next_level)
    """
    level, xp_into_level = calculate_level(xp)
    next_level_xp = xp_for_next_level(level)
    progress = min(100, int((xp_into_level / next_level_xp) * 100)) if next_level_xp > 0 else 100
    return level, progress, next_level_xp

async def add_xp(conn, user_id: str, server_id: str) -> Tuple[int, bool]:
    """
    Add XP to user and check for level up
    Returns: (new_total_xp, leveled_up)
    """
    xp_gain = random.randint(*XP_PER_MESSAGE)
    
    async with conn.cursor() as cur:
        # Get current XP
        await cur.execute(
            "SELECT xp FROM user_xp WHERE server_id = ? AND user_id = ?",
            (server_id, user_id))
        row = await cur.fetchone()
        
        old_xp = row[0] if row else 0
        new_xp = old_xp + xp_gain
        old_level = calculate_level(old_xp)[0]
        new_level = calculate_level(new_xp)[0]
        
        # Update XP
        await cur.execute(
            """INSERT INTO user_xp (server_id, user_id, xp)
            VALUES (?, ?, ?)
            ON CONFLICT(server_id, user_id) DO UPDATE SET
            xp = xp + excluded.xp""",
            (server_id, user_id, xp_gain))
        
        # Update coins
        await cur.execute(
            """INSERT INTO user_coins (user_id, coins)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            coins = coins + excluded.coins""",
            (user_id, xp_gain))
        
        # Level up bonus
        if new_level > old_level:
            bonus = LEVEL_UP_BONUS * (new_level - old_level)
            await cur.execute(
                "UPDATE user_coins SET coins = coins + ? WHERE user_id = ?",
                (bonus, user_id))
        
        await conn.commit()
        return (new_xp, new_level > old_level)