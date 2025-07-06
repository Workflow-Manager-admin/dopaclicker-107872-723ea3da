"""
Core game mechanics calculations and progression systems.

This module defines the constants and functions that drive the game's
progression, rewards, and upgrade systems.
"""

from typing import Tuple, Dict, List

# Progression Constants
BASE_POINTS_PER_CLICK = 1
POINTS_MULTIPLIER_PER_LEVEL = 1.2
BASE_XP_PER_CLICK = 5
LEVEL_XP_MULTIPLIER = 1.5

# Level Up Requirements (XP needed for each level)
def calculate_xp_for_level(level: int) -> int:
    """Calculate XP needed for a given level."""
    return int(100 * (level ** 1.5))

def calculate_click_value(level: int, upgrades: List[Dict]) -> int:
    """Calculate points earned per click based on level and upgrades."""
    base = BASE_POINTS_PER_CLICK * (POINTS_MULTIPLIER_PER_LEVEL ** (level - 1))
    upgrade_multiplier = sum(upgrade.get("multiplier", 0) for upgrade in upgrades)
    return int(base * (1 + upgrade_multiplier))

def calculate_rewards_for_level(level: int) -> Dict[str, int]:
    """Calculate rewards for reaching a level."""
    return {
        "dopamine_points": int(50 * (level ** 1.2)),
        "bonus_multiplier": level * 0.1
    }

def check_for_achievements(
    clicks: int,
    level: int,
    dopamine_points: int
) -> List[Dict[str, any]]:
    """Check for any achievements unlocked based on stats."""
    achievements = []
    
    # Click-based achievements
    click_tiers = [100, 500, 1000, 5000, 10000]
    for tier in click_tiers:
        if clicks >= tier:
            achievements.append({
                "type": "clicks_milestone",
                "tier": tier,
                "reward": int(tier * 0.2),
                "title": f"Click Master {tier}"
            })
            
    # Level-based achievements
    level_tiers = [5, 10, 25, 50, 100]
    for tier in level_tiers:
        if level >= tier:
            achievements.append({
                "type": "level_milestone", 
                "tier": tier,
                "reward": tier * 100,
                "title": f"Level {tier} Master"
            })
            
    # Points-based achievements
    points_tiers = [1000, 5000, 10000, 50000, 100000]
    for tier in points_tiers:
        if dopamine_points >= tier:
            achievements.append({
                "type": "points_milestone",
                "tier": tier,
                "reward": int(tier * 0.1),
                "title": f"Points Master {tier}"
            })
            
    return achievements

def calculate_progression(
    current_xp: int,
    current_level: int,
    click_power: int
) -> Tuple[int, int, bool]:
    """
    Calculate progression after an action.
    Returns (new_xp, new_level, did_level_up)
    """
    xp_gained = BASE_XP_PER_CLICK * click_power
    new_xp = current_xp + xp_gained
    
    # Check for level up
    xp_needed = calculate_xp_for_level(current_level)
    if new_xp >= xp_needed:
        return new_xp, current_level + 1, True
        
    return new_xp, current_level, False

# Upgrade tiers and costs
UPGRADE_TIERS = {
    "click_power": [
        {"level": 1, "cost": 100, "multiplier": 0.2},
        {"level": 2, "cost": 250, "multiplier": 0.5},
        {"level": 5, "cost": 1000, "multiplier": 1.0},
        {"level": 10, "cost": 2500, "multiplier": 2.0},
        {"level": 25, "cost": 10000, "multiplier": 5.0}
    ],
    "auto_click": [
        {"level": 3, "cost": 500, "multiplier": 0.1},
        {"level": 8, "cost": 2000, "multiplier": 0.3},
        {"level": 15, "cost": 5000, "multiplier": 0.8},
        {"level": 30, "cost": 15000, "multiplier": 2.0}
    ],
    "bonus_multiplier": [
        {"level": 5, "cost": 1000, "multiplier": 0.3},
        {"level": 12, "cost": 3000, "multiplier": 0.8},
        {"level": 20, "cost": 8000, "multiplier": 1.5},
        {"level": 35, "cost": 20000, "multiplier": 3.0}
    ]
}
