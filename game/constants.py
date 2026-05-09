"""Game-wide constants and tunables.

UI/rendering constants live here; data tables live in constants_data/.
"""

GAME_TITLE = "Eldrith Realms Idle"

# Notification prefixes (UI-agnostic)
NOTIFICATION_PREFIXES = {
    "achievement": "[A] ",
    "unlock": "[U] ",
    "error": "[!] ",
    "info": "[i] ",
    "save": "[S] ",
    "default": "",
}

# --- Game balance ---
BASE_INCOME_RATE = 5.0
UPGRADE_MULTIPLIER = 1.5
BASE_UPGRADE_COST = 10
COST_INCREASE_RATE = 1.2

# --- Long-term progression ---
PRESTIGE_REQUIREMENT_BASE = 1_000_000
PRESTIGE_SCALING = 5.0
PRESTIGE_BONUS_BASE = 0.15
RESEARCH_POINT_BASE_COST = 5000
RESEARCH_POINT_COST_SCALING = 1.5

# --- Time-based mechanics ---
OFFLINE_PROGRESS_RATE = 0.5
TIME_WARP_DURATION = 3600       # seconds
TIME_WARP_COOLDOWN = 86400      # seconds

# --- Resource types ---
RESOURCE_TYPES = [
    "gold", "wood", "stone", "food", "mana",
    "crystal", "ancient_knowledge", "prestige_points",
]

# --- Data tables (re-exported from constants_data/) ---
from .constants_data.races_data import RACES
from .constants_data.buildings_data import BUILDINGS
from .constants_data.research_data import RESEARCH
from .constants_data.prestige_upgrades_data import PRESTIGE_UPGRADES
from .constants_data.achievements_data import ACHIEVEMENTS

__all__ = [
    "GAME_TITLE", "NOTIFICATION_PREFIXES",
    "BASE_INCOME_RATE", "UPGRADE_MULTIPLIER", "BASE_UPGRADE_COST", "COST_INCREASE_RATE",
    "PRESTIGE_REQUIREMENT_BASE", "PRESTIGE_SCALING", "PRESTIGE_BONUS_BASE",
    "RESEARCH_POINT_BASE_COST", "RESEARCH_POINT_COST_SCALING",
    "OFFLINE_PROGRESS_RATE", "TIME_WARP_DURATION", "TIME_WARP_COOLDOWN",
    "RESOURCE_TYPES",
    "RACES", "BUILDINGS", "RESEARCH", "PRESTIGE_UPGRADES", "ACHIEVEMENTS",
]
