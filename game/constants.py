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
BASE_INCOME_RATE = 0.4  # per unit per race level per second (was 5.0; errata E11)
UPGRADE_MULTIPLIER = 1.5
BASE_UPGRADE_COST = 10
COST_INCREASE_RATE = 1.2

# --- Pacing (errata E11) ---
# Tuned with tools/balance_sim.py (which overrides these by name). With the
# probe's greedy player: level 10 at ~7 min, first prestige at ~35 min,
# first race ability at ~2 h, four prestiges in ~5.5 h. Content is gated so
# that run N (after N-1 prestiges) tops out around the next unlock tier.
RACE_COST_GROWTH = 1.15          # each extra unit of a race costs this much more
RACE_UPGRADE_COST_MULT = 5       # a race's first level-up costs base_cost x this
RACE_UPGRADE_COST_GROWTH = 2.0   # each further level-up costs this much more
# Player level L needs BASE * (L-1) ** EXPONENT total earnings this run.
# Level 25 (the first prestige-gated unlocks) lands at the first prestige
# requirement, and level 50 around the fourth (was linear: 1000 per level).
LEVEL_EARNINGS_EXPONENT = 7
LEVEL_EARNINGS_BASE = 1_000_000 / 24 ** LEVEL_EARNINGS_EXPONENT
# Gold per second paid only while nothing you own produces gold (errata E16):
# without it, a player holding only non-gold races and too little gold for a
# gold race could never earn again. Normal play never sees it.
SUBSISTENCE_GOLD_RATE = 0.25

# --- Long-term progression ---
PRESTIGE_REQUIREMENT_BASE = 1_000_000
PRESTIGE_SCALING = 5.0
PRESTIGE_BONUS_BASE = 0.15
RESEARCH_POINT_BASE_COST = 5000
RESEARCH_POINT_COST_SCALING = 1.5

# --- Time-based mechanics ---
OFFLINE_PROGRESS_RATE = 0.5     # base share of production earned while away
OFFLINE_PROGRESS_MAX_RATE = 1.0 # ceiling after Automatic Production upgrades
OFFLINE_PROGRESS_CAP = 86400    # seconds; longer absences earn no more
TIME_WARP_DURATION = 3600       # seconds of play
TIME_WARP_COOLDOWN = 86400      # seconds of play (offline time counts, up to the cap)

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
    "RACE_COST_GROWTH", "RACE_UPGRADE_COST_MULT", "RACE_UPGRADE_COST_GROWTH",
    "LEVEL_EARNINGS_BASE", "LEVEL_EARNINGS_EXPONENT", "SUBSISTENCE_GOLD_RATE",
    "PRESTIGE_REQUIREMENT_BASE", "PRESTIGE_SCALING", "PRESTIGE_BONUS_BASE",
    "RESEARCH_POINT_BASE_COST", "RESEARCH_POINT_COST_SCALING",
    "OFFLINE_PROGRESS_RATE", "OFFLINE_PROGRESS_MAX_RATE", "OFFLINE_PROGRESS_CAP",
    "TIME_WARP_DURATION", "TIME_WARP_COOLDOWN",
    "RESOURCE_TYPES",
    "RACES", "BUILDINGS", "RESEARCH", "PRESTIGE_UPGRADES", "ACHIEVEMENTS",
]
