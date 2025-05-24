# Game window settings
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60
GAME_TITLE = "Eldrith Realms Idle"

# Colors
BACKGROUND_COLOR = (30, 30, 50)  # Dark blue-ish background
TEXT_COLOR = (255, 255, 255)  # White text
BUTTON_COLOR = (70, 70, 100)  # Lighter blue for buttons
BUTTON_HOVER_COLOR = (90, 90, 120)  # Even lighter blue for button hover
PANEL_COLOR = (40, 40, 60)  # Medium blue for panels
GOLD_COLOR = (255, 215, 0)  # Gold for currency
GREEN_COLOR = (0, 200, 0)  # Green for positive effects
RED_COLOR = (200, 0, 0)  # Red for negative effects
PURPLE_COLOR = (128, 0, 128)  # Purple for prestige/special items
BLUE_COLOR = (0, 128, 255)  # Blue for research

# Notification Colors & Prefixes
NOTIFICATION_COLOR_ACHIEVEMENT = GOLD_COLOR
NOTIFICATION_COLOR_UNLOCK = (0, 200, 200)  # Teal
NOTIFICATION_COLOR_ERROR = RED_COLOR
NOTIFICATION_COLOR_INFO = (200, 200, 200)  # Light Gray
NOTIFICATION_COLOR_SAVE = GREEN_COLOR
DEFAULT_NOTIFICATION_COLOR = NOTIFICATION_COLOR_INFO

NOTIFICATION_PREFIXES = {
    "achievement": "[A] ",
    "unlock": "[U] ",
    "error": "[!] ",
    "info": "[i] ",
    "save": "[S] ",
    "default": "" 
}

# Disabled Button Colors
DISABLED_BUTTON_COLOR = (50, 50, 50)
DISABLED_TEXT_COLOR = (150, 150, 150)
DISABLED_BUTTON_BORDER_COLOR = (80, 80, 80)


# Game balance constants
BASE_INCOME_RATE = 1.0
UPGRADE_MULTIPLIER = 1.5
BASE_UPGRADE_COST = 10
COST_INCREASE_RATE = 1.2

# Long-term progression constants
PRESTIGE_REQUIREMENT_BASE = 1000000
PRESTIGE_SCALING = 5.0
PRESTIGE_BONUS_BASE = 0.1
RESEARCH_POINT_BASE_COST = 5000
RESEARCH_POINT_COST_SCALING = 1.5

# Time-based mechanics
OFFLINE_PROGRESS_RATE = 0.5
TIME_WARP_DURATION = 3600
TIME_WARP_COOLDOWN = 86400

# Resource types
RESOURCE_TYPES = ["gold", "wood", "stone", "food", "mana", "crystal", "ancient_knowledge", "prestige_points"]

# Import data from constants_data subdirectory
from .constants_data.races_data import RACES
from .constants_data.buildings_data import BUILDINGS
from .constants_data.research_data import RESEARCH
from .constants_data.prestige_upgrades_data import PRESTIGE_UPGRADES
from .constants_data.achievements_data import ACHIEVEMENTS
