from typing import Tuple

XP_PER_MESSAGE_MIN = 5
XP_PER_MESSAGE_MAX = 10
XP_NEEDED_BASE = 100
XP_NEEDED_MULTIPLIER = 1.2
LEVEL_UP_BONUS = 100

def calculate_level(xp: int) -> Tuple[int, int]:
    level = 0
    xp_needed = XP_NEEDED_BASE
    
    while xp >= xp_needed:
        xp -= xp_needed
        level += 1
        xp_needed = int(xp_needed * XP_NEEDED_MULTIPLIER)
    
    return (level, xp)

def xp_needed_for_level(level: int) -> int:
    if level == 0:
        return 0
    
    total = 0
    xp_needed = XP_NEEDED_BASE
    
    for _ in range(level):
        total += xp_needed
        xp_needed = int(xp_needed * XP_NEEDED_MULTIPLIER)
    
    return total