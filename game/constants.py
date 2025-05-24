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
BASE_INCOME_RATE = 5.0
UPGRADE_MULTIPLIER = 1.5
BASE_UPGRADE_COST = 10
COST_INCREASE_RATE = 1.2

# Long-term progression constants
PRESTIGE_REQUIREMENT_BASE = 1000000
PRESTIGE_SCALING = 5.0
PRESTIGE_BONUS_BASE = 0.15
RESEARCH_POINT_BASE_COST = 5000
RESEARCH_POINT_COST_SCALING = 1.5

# Time-based mechanics
OFFLINE_PROGRESS_RATE = 0.5
TIME_WARP_DURATION = 3600
TIME_WARP_COOLDOWN = 86400

# Resource types
RESOURCE_TYPES = ["gold", "wood", "stone", "food", "mana", "crystal", "ancient_knowledge", "prestige_points"]

# Race definitions
RACES = {
    "dwarf": {
        "name": "Dwarves",
        "description": "Masters of mining and crafting. Generate more stone and gold.",
        "base_cost": 50,
        "resource_bonuses": {"gold": 1.2, "stone": 1.5},
        "unlock_level": 1,
        "special_abilities": {
            "mountain_heart": {
                "name": "Mountain Heart",
                "description": "Dwarves can mine the core of mountains, doubling stone production and adding a 10% chance to find crystals when mining.",
                "effects": {"stone_multiplier": 2.0, "crystal_chance": 0.1},
                "unlock_requirements": {"race_level": 50, "prestige_level": 1, "resources": {"gold": 1000000, "stone": 500000}}
            },
            "master_smiths": {
                "name": "Master Smiths",
                "description": "Dwarven smiths can forge powerful artifacts, increasing the efficiency of all buildings by 25%.",
                "effects": {"building_efficiency": 1.25},
                "unlock_requirements": {"race_level": 100, "prestige_level": 3, "resources": {"gold": 10000000, "crystal": 10000}}
            }
        }
    },
    "elf": {
        "name": "Elves",
        "description": "Forest dwellers with nature affinity. Generate more wood and mana.",
        "base_cost": 50,
        "resource_bonuses": {"wood": 1.5, "mana": 1.2},
        "unlock_level": 1,
        "special_abilities": {
            "ancient_grove": {
                "name": "Ancient Grove",
                "description": "Elves can cultivate ancient groves, tripling wood production and increasing mana regeneration by 50%.",
                "effects": {"wood_multiplier": 3.0, "mana_multiplier": 1.5},
                "unlock_requirements": {"race_level": 50, "prestige_level": 1, "resources": {"wood": 500000, "mana": 100000}}
            },
            "nature_harmony": {
                "name": "Nature's Harmony",
                "description": "Elves achieve perfect harmony with nature, allowing all resources to regenerate over time even without buildings.",
                "effects": {"passive_generation": 0.01},
                "unlock_requirements": {"race_level": 100, "prestige_level": 3, "resources": {"mana": 5000000, "crystal": 8000}}
            }
        }
    },
    "human": {
        "name": "Humans",
        "description": "Adaptable and industrious. Balanced resource generation.",
        "base_cost": 30,
        "resource_bonuses": {"food": 1.3},
        "unlock_level": 1,
        "special_abilities": {
            "adaptability": {
                "name": "Adaptability",
                "description": "Humans can adapt to any environment, gaining a 40% bonus to all resource production.",
                "effects": {"all_resources_multiplier": 1.4},
                "unlock_requirements": {"race_level": 50, "prestige_level": 1, "resources": {"gold": 750000, "food": 750000}}
            },
            "technological_mastery": {
                "name": "Technological Mastery",
                "description": "Human innovation leads to technological breakthroughs, reducing all research costs by 50% and increasing research effects by 25%.",
                "effects": {"research_cost_reduction": 0.5, "research_effect_bonus": 1.25},
                "unlock_requirements": {"race_level": 100, "prestige_level": 2, "resources": {"ancient_knowledge": 100000, "crystal": 5000}}
            }
        }
    },
    "goblin": {
        "name": "Goblins",
        "description": "Crafty and numerous. Cheaper to recruit but less efficient.",
        "base_cost": 20,
        "resource_bonuses": {"gold": 1.05},
        "unlock_level": 2,
        "special_abilities": {
            "horde_tactics": {
                "name": "Horde Tactics",
                "description": "Goblins organize into efficient hordes, gaining a stacking 0.5% bonus per goblin owned.",
                "effects": {"per_unit_bonus": 0.005},
                "unlock_requirements": {"race_level": 40, "prestige_level": 1, "resources": {"gold": 500000}}
            },
            "scavenger_economy": {
                "name": "Scavenger Economy",
                "description": "Goblins develop a complex scavenging economy, generating 1% of your highest resource production for all other resources.",
                "effects": {"resource_conversion": 0.01},
                "unlock_requirements": {"race_level": 80, "prestige_level": 2, "resources": {"gold": 2000000, "food": 1000000}}
            }
        }
    },
    "troll": {
        "name": "Trolls",
        "description": "Strong but slow. Generate significant stone but consume more food.",
        "base_cost": 100,
        "resource_bonuses": {"stone": 2.0},
        "resource_costs": {"food": 1.5},
        "unlock_level": 3,
        "special_abilities": {
            "regeneration": {
                "name": "Regeneration",
                "description": "Trolls develop powerful regenerative abilities, reducing their food consumption by 75% and doubling their stone production.",
                "effects": {"food_cost_reduction": 0.75, "stone_multiplier": 2.0},
                "unlock_requirements": {"race_level": 40, "prestige_level": 1, "resources": {"food": 1000000, "stone": 500000}}
            },
            "mountain_shapers": {
                "name": "Mountain Shapers",
                "description": "Trolls learn to reshape mountains with their bare hands, providing a 100% chance to find crystals when producing stone and increasing all building durability.",
                "effects": {"crystal_chance": 1.0, "building_durability": 2.0},
                "unlock_requirements": {"race_level": 80, "prestige_level": 2, "resources": {"stone": 5000000, "crystal": 7500}}
            }
        }
    },
    "shade": {
        "name": "Shades",
        "description": "Eldritch beings from beyond. Generate mana but are unstable.",
        "base_cost": 150,
        "resource_bonuses": {"mana": 2.0},
        "unlock_level": 5,
        "special_abilities": {
            "void_channeling": {
                "name": "Void Channeling",
                "description": "Shades learn to channel energy directly from the void, tripling mana production but occasionally causing dimensional instabilities.",
                "effects": {"mana_multiplier": 3.0, "random_resource_bonus": 0.2},
                "unlock_requirements": {"race_level": 45, "prestige_level": 1, "resources": {"mana": 750000}}
            },
            "reality_warping": {
                "name": "Reality Warping",
                "description": "Shades can temporarily warp reality, giving a 5% chance to double all resource production for short periods.",
                "effects": {"production_doubling_chance": 0.05},
                "unlock_requirements": {"race_level": 90, "prestige_level": 3, "resources": {"mana": 3000000, "crystal": 15000, "ancient_knowledge": 50000}}
            }
        }
    },
    "deepling": {
        "name": "Deeplings",
        "description": "Ancient race from the depths. Powerful mana generation.",
        "base_cost": 200,
        "resource_bonuses": {"mana": 2.5, "stone": 1.2},
        "unlock_level": 8,
        "special_abilities": {
            "abyssal_knowledge": {
                "name": "Abyssal Knowledge",
                "description": "Deeplings share ancient knowledge from the abyss, increasing ancient knowledge generation by 300% and mana by 100%.",
                "effects": {"ancient_knowledge_multiplier": 4.0, "mana_multiplier": 2.0},
                "unlock_requirements": {"race_level": 50, "prestige_level": 2, "resources": {"mana": 1000000, "ancient_knowledge": 25000}}
            },
            "pressure_manipulation": {
                "name": "Pressure Manipulation",
                "description": "Deeplings can manipulate immense pressures, creating crystals from stone with 50% efficiency and doubling all stone-based production.",
                "effects": {"stone_to_crystal_conversion": 0.5, "stone_production_multiplier": 2.0},
                "unlock_requirements": {"race_level": 90, "prestige_level": 3, "resources": {"stone": 4000000, "crystal": 20000}}
            }
        }
    },
    "fae": {
        "name": "Fae",
        "description": "Mystical beings with strong connections to nature and magic.",
        "base_cost": 180,
        "resource_bonuses": {"mana": 1.8, "wood": 1.8},
        "unlock_level": 6,
        "special_abilities": {
            "glamour": {
                "name": "Glamour",
                "description": "Fae can cast powerful glamours, making resources appear from nothing at random intervals.",
                "effects": {"random_resource_generation": 0.05},
                "unlock_requirements": {"race_level": 45, "prestige_level": 1, "resources": {"mana": 800000, "wood": 800000}}
            },
            "wild_magic": {
                "name": "Wild Magic",
                "description": "Fae unleash wild magic that enhances all magical effects by 100% and occasionally creates time distortions that speed up production.",
                "effects": {"magic_effect_multiplier": 2.0, "time_distortion_chance": 0.02},
                "unlock_requirements": {"race_level": 85, "prestige_level": 2, "resources": {"mana": 2500000, "crystal": 12000}}
            }
        }
    },
    "dragon": {
        "name": "Dragons",
        "description": "Ancient and powerful beings with mastery over fire and treasure.",
        "base_cost": 1000,
        "resource_bonuses": {"gold": 3.0, "mana": 2.0},
        "unlock_level": 15,
        "special_abilities": {
            "hoard_mastery": {
                "name": "Hoard Mastery",
                "description": "Dragons' hoards grow exponentially, gaining a 0.01% bonus to gold production for each 1000 gold in storage.",
                "effects": {"gold_storage_bonus": 0.0001},
                "unlock_requirements": {"race_level": 40, "prestige_level": 1, "resources": {"gold": 5000000}}
            },
            "dragon_fire": {
                "name": "Dragon Fire",
                "description": "Dragons unleash their legendary fire, which can transmute any resource into another at a 75% conversion rate.",
                "effects": {"resource_transmutation": 0.75},
                "unlock_requirements": {"race_level": 80, "prestige_level": 3, "resources": {"mana": 3000000, "crystal": 25000}}
            }
        }
    },
    "titan": {
        "name": "Titans",
        "description": "Primordial giants with immense strength and ancient knowledge.",
        "base_cost": 2000,
        "resource_bonuses": {"stone": 4.0, "ancient_knowledge": 1.5},
        "unlock_level": 20,
        "special_abilities": {
            "world_shaping": {
                "name": "World Shaping",
                "description": "Titans can reshape the world itself, quadrupling all stone and crystal production.",
                "effects": {"stone_multiplier": 4.0, "crystal_multiplier": 4.0},
                "unlock_requirements": {"race_level": 50, "prestige_level": 2, "resources": {"stone": 10000000, "ancient_knowledge": 50000}}
            },
            "primordial_wisdom": {
                "name": "Primordial Wisdom",
                "description": "Titans share their primordial wisdom, making all research instant and increasing all knowledge effects by 200%.",
                "effects": {"instant_research": True, "knowledge_effect_multiplier": 3.0},
                "unlock_requirements": {"race_level": 100, "prestige_level": 4, "resources": {"ancient_knowledge": 200000, "crystal": 50000}}
            }
        }
    },
    "celestial": {
        "name": "Celestials",
        "description": "Beings of pure energy from beyond the stars.",
        "base_cost": 5000,
        "resource_bonuses": {"crystal": 2.0, "mana": 3.0, "ancient_knowledge": 2.0},
        "unlock_level": 30,
        "requires_prestige": 1,
        "special_abilities": {
            "stellar_alignment": {
                "name": "Stellar Alignment",
                "description": "Celestials align with the stars, providing a 200% bonus to all resource production during specific time intervals.",
                "effects": {"timed_production_bonus": 3.0, "alignment_duration": 300},
                "unlock_requirements": {"race_level": 60, "prestige_level": 3, "resources": {"crystal": 30000, "mana": 5000000}}
            },
            "cosmic_manipulation": {
                "name": "Cosmic Manipulation",
                "description": "Celestials can manipulate cosmic forces, generating prestige points without resetting and increasing all production by 100%.",
                "effects": {"passive_prestige_generation": 0.001, "all_production_multiplier": 2.0},
                "unlock_requirements": {"race_level": 120, "prestige_level": 5, "resources": {"crystal": 100000, "ancient_knowledge": 300000}}
            }
        }
    },
    "void_walker": {
        "name": "Void Walkers",
        "description": "Enigmatic entities that exist between dimensions.",
        "base_cost": 10000,
        "resource_bonuses": {"crystal": 3.0, "ancient_knowledge": 3.0},
        "unlock_level": 40,
        "requires_prestige": 2,
        "special_abilities": {
            "dimensional_phasing": {
                "name": "Dimensional Phasing",
                "description": "Void Walkers phase between dimensions, gaining resources from parallel realities equal to 10% of your production.",
                "effects": {"parallel_production": 0.1},
                "unlock_requirements": {"race_level": 70, "prestige_level": 4, "resources": {"crystal": 50000, "ancient_knowledge": 100000}}
            },
            "entropy_manipulation": {
                "name": "Entropy Manipulation",
                "description": "Void Walkers can manipulate entropy itself, allowing them to reverse time and recover spent resources with 50% efficiency.",
                "effects": {"resource_recovery": 0.5, "time_reversal": True},
                "unlock_requirements": {"race_level": 150, "prestige_level": 7, "resources": {"crystal": 200000, "ancient_knowledge": 500000, "prestige_points": 100}}
            }
        }
    }
}

# Building definitions
BUILDINGS = {
    "mine": {
        "name": "Mine",
        "description": "Extracts stone and gold from the earth.",
        "base_cost": {"gold": 100, "wood": 50},
        "resource_production": {"stone": 2.0, "gold": 0.5},
        "unlock_level": 2,
        "max_level": 100,
        "level_scaling": 1.2  # Production multiplier per level
    },
    "lumber_camp": {
        "name": "Lumber Camp",
        "description": "Harvests wood from the forest.",
        "base_cost": {"gold": 80, "food": 30},
        "resource_production": {"wood": 2.5},
        "unlock_level": 2,
        "max_level": 100,
        "level_scaling": 1.2
    },
    "farm": {
        "name": "Farm",
        "description": "Grows food for your population.",
        "base_cost": {"gold": 60, "wood": 40},
        "resource_production": {"food": 3.0},
        "unlock_level": 2,
        "max_level": 100,
        "level_scaling": 1.2
    },
    "mana_well": {
        "name": "Mana Well",
        "description": "Draws magical energy from the earth.",
        "base_cost": {"gold": 150, "stone": 50},
        "resource_production": {"mana": 1.5},
        "unlock_level": 3,
        "max_level": 100,
        "level_scaling": 1.25
    },
    "marketplace": {
        "name": "Marketplace",
        "description": "Increases gold production from all sources.",
        "base_cost": {"gold": 200, "wood": 100, "stone": 50},
        "global_multipliers": {"gold": 1.1},  # 10% increase to all gold production
        "unlock_level": 5,
        "max_level": 50,
        "level_scaling": 1.05  # Each level adds another 5% to the multiplier
    },
    "library": {
        "name": "Library",
        "description": "Generates ancient knowledge and improves research.",
        "base_cost": {"gold": 500, "wood": 200, "stone": 100},
        "resource_production": {"ancient_knowledge": 0.5},
        "research_speed_bonus": 0.05,  # 5% faster research per level
        "unlock_level": 10,
        "max_level": 50,
        "level_scaling": 1.15
    },
    "crystal_mine": {
        "name": "Crystal Mine",
        "description": "Extracts rare crystals with magical properties.",
        "base_cost": {"gold": 1000, "stone": 500, "mana": 200},
        "resource_production": {"crystal": 0.2},
        "unlock_level": 15,
        "max_level": 50,
        "level_scaling": 1.3
    },
    "portal": {
        "name": "Dimensional Portal",
        "description": "Opens gateways to other realms, generating exotic resources.",
        "base_cost": {"gold": 5000, "crystal": 100, "mana": 1000},
        "resource_production": {"crystal": 0.5, "ancient_knowledge": 1.0},
        "unlock_level": 25,
        "requires_prestige": 1,
        "max_level": 30,
        "level_scaling": 1.4
    },
    "time_chamber": {
        "name": "Time Dilation Chamber",
        "description": "Manipulates time to increase all resource production.",
        "base_cost": {"gold": 50000, "crystal": 500, "ancient_knowledge": 200},
        "global_multipliers": {"all": 1.2},  # 20% to all production
        "unlock_level": 35,
        "requires_prestige": 2,
        "max_level": 20,
        "level_scaling": 1.1
    },
    "cosmic_forge": {
        "name": "Cosmic Forge",
        "description": "Ancient artifact that can create resources from pure energy.",
        "base_cost": {"gold": 1000000, "crystal": 2000, "ancient_knowledge": 1000},
        "resource_production": {"gold": 100, "wood": 100, "stone": 100, "food": 100, "mana": 50, "crystal": 5, "ancient_knowledge": 2},
        "unlock_level": 50,
        "requires_prestige": 3,
        "max_level": 10,
        "level_scaling": 2.0
    }
}

# Research definitions
RESEARCH = {
    "efficient_mining": {
        "name": "Efficient Mining",
        "description": "Improves stone and gold production from all sources.",
        "cost": {"ancient_knowledge": 10},
        "effect": {"resource_multiplier": {"stone": 1.1, "gold": 1.1}},
        "max_level": 100,
        "cost_scaling": 1.5,
        "effect_scaling": 1.1,
        "unlock_level": 10
    },
    "advanced_forestry": {
        "name": "Advanced Forestry",
        "description": "Improves wood production from all sources.",
        "cost": {"ancient_knowledge": 10},
        "effect": {"resource_multiplier": {"wood": 1.2}},
        "max_level": 100,
        "cost_scaling": 1.5,
        "effect_scaling": 1.1,
        "unlock_level": 10
    },
    "magical_attunement": {
        "name": "Magical Attunement",
        "description": "Improves mana production from all sources.",
        "cost": {"ancient_knowledge": 15},
        "effect": {"resource_multiplier": {"mana": 1.2}},
        "max_level": 100,
        "cost_scaling": 1.6,
        "effect_scaling": 1.1,
        "unlock_level": 12
    },
    "crystal_resonance": {
        "name": "Crystal Resonance",
        "description": "Improves crystal production and mana efficiency.",
        "cost": {"ancient_knowledge": 30, "crystal": 5},
        "effect": {"resource_multiplier": {"crystal": 1.3, "mana": 1.1}},
        "max_level": 50,
        "cost_scaling": 1.7,
        "effect_scaling": 1.1,
        "unlock_level": 18
    },
    "racial_harmony": {
        "name": "Racial Harmony",
        "description": "Improves production bonuses from all races.",
        "cost": {"ancient_knowledge": 50},
        "effect": {"race_bonus_multiplier": 1.1},
        "max_level": 50,
        "cost_scaling": 1.8,
        "effect_scaling": 1.05,
        "unlock_level": 20
    },
    "dimensional_studies": {
        "name": "Dimensional Studies",
        "description": "Unlocks the secrets of other dimensions, improving exotic resource production.",
        "cost": {"ancient_knowledge": 100, "crystal": 20},
        "effect": {"resource_multiplier": {"crystal": 1.2, "ancient_knowledge": 1.2}},
        "max_level": 30,
        "cost_scaling": 2.0,
        "effect_scaling": 1.1,
        "unlock_level": 25,
        "requires_prestige": 1
    },
    "time_manipulation": {
        "name": "Time Manipulation",
        "description": "Bends the laws of time to increase all production.",
        "cost": {"ancient_knowledge": 200, "crystal": 50},
        "effect": {"global_multiplier": 1.05},
        "max_level": 20,
        "cost_scaling": 2.5,
        "effect_scaling": 1.05,
        "unlock_level": 30,
        "requires_prestige": 1
    },
    "cosmic_awareness": {
        "name": "Cosmic Awareness",
        "description": "Expands consciousness to understand the universe, massively boosting all production.",
        "cost": {"ancient_knowledge": 1000, "crystal": 200},
        "effect": {"global_multiplier": 1.2},
        "max_level": 10,
        "cost_scaling": 3.0,
        "effect_scaling": 1.2,
        "unlock_level": 40,
        "requires_prestige": 2
    },
    "reality_manipulation": {
        "name": "Reality Manipulation",
        "description": "Allows direct manipulation of reality itself, creating resources from nothing.",
        "cost": {"ancient_knowledge": 5000, "crystal": 1000},
        "effect": {"idle_resource_generation": 10.0},
        "max_level": 5,
        "cost_scaling": 5.0,
        "effect_scaling": 2.0,
        "unlock_level": 50,
        "requires_prestige": 3
    }
}

# Prestige system upgrades
PRESTIGE_UPGRADES = {
    "eternal_knowledge": {
        "name": "Eternal Knowledge",
        "description": "Retain 10% of your ancient knowledge after prestige.",
        "cost": {"prestige_points": 1},
        "effect": {"knowledge_retention": 0.1},
        "max_level": 5,
        "effect_scaling": 1.0
    },
    "faster_start": {
        "name": "Faster Start",
        "description": "Begin with additional gold after each prestige.",
        "cost": {"prestige_points": 1},
        "effect": {"starting_gold": 1000},
        "max_level": 10,
        "effect_scaling": 2.0
    },
    "resource_memory": {
        "name": "Resource Memory",
        "description": "Retain 5% of your basic resources after prestige.",
        "cost": {"prestige_points": 2},
        "effect": {"resource_retention": 0.08},
        "max_level": 5,
        "effect_scaling": 1.0
    },
    "automatic_production": {
        "name": "Automatic Production",
        "description": "Automatically generate resources even when game is closed.",
        "cost": {"prestige_points": 3},
        "effect": {"offline_progress": 0.2},
        "max_level": 5,
        "effect_scaling": 1.0
    },
    "time_warp": {
        "name": "Time Warp",
        "description": "Ability to accelerate time for 1 hour, once per day.",
        "cost": {"prestige_points": 5},
        "effect": {"time_warp_multiplier": 2.0},
        "max_level": 5,
        "effect_scaling": 1.5
    },
    "cosmic_insight": {
        "name": "Cosmic Insight",
        "description": "Permanent boost to all production that stacks across prestiges.",
        "cost": {"prestige_points": 10},
        "effect": {"permanent_multiplier": 1.1},
        "max_level": 10,
        "effect_scaling": 1.0
    }
}

# Achievements for long-term goals
ACHIEVEMENTS = {
    "resource_milestones": [
        {"id": "gold_1", "name": "Golden Beginnings", "description": "Accumulate 1,000 gold", "requirement": {"gold": 1000}, "reward": {"gold_multiplier": 1.05}},
        {"id": "gold_2", "name": "Treasure Hoard", "description": "Accumulate 1,000,000 gold", "requirement": {"gold": 1000000}, "reward": {"gold_multiplier": 1.1}},
        {"id": "gold_3", "name": "Dragon's Fortune", "description": "Accumulate 1,000,000,000 gold", "requirement": {"gold": 1000000000}, "reward": {"gold_multiplier": 1.2}},
        {"id": "crystal_1", "name": "Crystal Collector", "description": "Accumulate 100 crystals", "requirement": {"crystal": 100}, "reward": {"crystal_multiplier": 1.1}},
        {"id": "crystal_2", "name": "Crystal Mastery", "description": "Accumulate 10,000 crystals", "requirement": {"crystal": 10000}, "reward": {"crystal_multiplier": 1.2}},
        {"id": "knowledge_1", "name": "Scholar", "description": "Accumulate 1,000 ancient knowledge", "requirement": {"ancient_knowledge": 1000}, "reward": {"research_speed": 1.1}},
        {"id": "knowledge_2", "name": "Sage", "description": "Accumulate 100,000 ancient knowledge", "requirement": {"ancient_knowledge": 100000}, "reward": {"research_speed": 1.2}}
    ],
    "race_milestones": [
        {"id": "dwarf_1", "name": "Dwarf Friend", "description": "Recruit 100 dwarves", "requirement": {"race": "dwarf", "count": 100}, "reward": {"dwarf_efficiency": 1.1}},
        {"id": "elf_1", "name": "Elf Friend", "description": "Recruit 100 elves", "requirement": {"race": "elf", "count": 100}, "reward": {"elf_efficiency": 1.1}},
        {"id": "all_races_1", "name": "Diplomat", "description": "Recruit at least 10 of each basic race", "requirement": {"all_races": 10}, "reward": {"all_race_efficiency": 1.05}},
        {"id": "all_races_2", "name": "Master Diplomat", "description": "Recruit at least 100 of each race", "requirement": {"all_races": 100}, "reward": {"all_race_efficiency": 1.1}},
        {"id": "celestial_1", "name": "Star Touched", "description": "Recruit your first Celestial", "requirement": {"race": "celestial", "count": 1}, "reward": {"mana_multiplier": 1.2}}
    ],
    "race_skill_milestones": [
        {"id": "dwarf_mining_1", "name": "Novice Miner", "description": "Generate 10,000 stone with Dwarves", "requirement": {"race_skill": "dwarf", "resource": "stone", "amount": 10000}, "reward": {"stone_multiplier": 1.05, "dwarf_stone_bonus": 1.1}},
        {"id": "dwarf_mining_2", "name": "Adept Miner", "description": "Generate 1,000,000 stone with Dwarves", "requirement": {"race_skill": "dwarf", "resource": "stone", "amount": 1000000}, "reward": {"stone_multiplier": 1.1, "dwarf_stone_bonus": 1.2}},
        {"id": "dwarf_mining_3", "name": "Master Miner", "description": "Generate 100,000,000 stone with Dwarves", "requirement": {"race_skill": "dwarf", "resource": "stone", "amount": 100000000}, "reward": {"stone_multiplier": 1.15, "dwarf_stone_bonus": 1.3}},
        {"id": "dwarf_mining_4", "name": "Legendary Miner", "description": "Generate 10,000,000,000 stone with Dwarves", "requirement": {"race_skill": "dwarf", "resource": "stone", "amount": 10000000000, "player_level": 50}, "reward": {"stone_multiplier": 1.2, "dwarf_stone_bonus": 1.5, "crystal_chance": 0.05}},
        {"id": "elf_woodcutting_1", "name": "Novice Forester", "description": "Generate 10,000 wood with Elves", "requirement": {"race_skill": "elf", "resource": "wood", "amount": 10000}, "reward": {"wood_multiplier": 1.05, "elf_wood_bonus": 1.1}},
        {"id": "elf_woodcutting_2", "name": "Adept Forester", "description": "Generate 1,000,000 wood with Elves", "requirement": {"race_skill": "elf", "resource": "wood", "amount": 1000000}, "reward": {"wood_multiplier": 1.1, "elf_wood_bonus": 1.2}},
        {"id": "elf_woodcutting_3", "name": "Master Forester", "description": "Generate 100,000,000 wood with Elves", "requirement": {"race_skill": "elf", "resource": "wood", "amount": 100000000}, "reward": {"wood_multiplier": 1.15, "elf_wood_bonus": 1.3}},
        {"id": "elf_woodcutting_4", "name": "Legendary Forester", "description": "Generate 10,000,000,000 wood with Elves", "requirement": {"race_skill": "elf", "resource": "wood", "amount": 10000000000, "player_level": 50}, "reward": {"wood_multiplier": 1.2, "elf_wood_bonus": 1.5, "mana_regeneration": 1.1}},
        {"id": "human_trading_1", "name": "Novice Trader", "description": "Generate 50,000 gold with Humans", "requirement": {"race_skill": "human", "resource": "gold", "amount": 50000}, "reward": {"gold_multiplier": 1.05, "human_gold_bonus": 1.1}},
        {"id": "human_trading_2", "name": "Adept Trader", "description": "Generate 5,000,000 gold with Humans", "requirement": {"race_skill": "human", "resource": "gold", "amount": 5000000}, "reward": {"gold_multiplier": 1.1, "human_gold_bonus": 1.2}},
        {"id": "human_trading_3", "name": "Master Trader", "description": "Generate 500,000,000 gold with Humans", "requirement": {"race_skill": "human", "resource": "gold", "amount": 500000000}, "reward": {"gold_multiplier": 1.15, "human_gold_bonus": 1.3}},
        {"id": "human_trading_4", "name": "Legendary Trader", "description": "Generate 50,000,000,000 gold with Humans", "requirement": {"race_skill": "human", "resource": "gold", "amount": 50000000000, "player_level": 50}, "reward": {"gold_multiplier": 1.2, "human_gold_bonus": 1.5, "all_resources_multiplier": 1.05}},
        {"id": "goblin_scavenging_1", "name": "Novice Scavenger", "description": "Generate 20,000 food with Goblins", "requirement": {"race_skill": "goblin", "resource": "food", "amount": 20000}, "reward": {"food_multiplier": 1.05, "goblin_food_bonus": 1.1}},
        {"id": "goblin_scavenging_2", "name": "Adept Scavenger", "description": "Generate 2,000,000 food with Goblins", "requirement": {"race_skill": "goblin", "resource": "food", "amount": 2000000}, "reward": {"food_multiplier": 1.1, "goblin_food_bonus": 1.2}},
        {"id": "goblin_scavenging_3", "name": "Master Scavenger", "description": "Generate 200,000,000 food with Goblins", "requirement": {"race_skill": "goblin", "resource": "food", "amount": 200000000}, "reward": {"food_multiplier": 1.15, "goblin_food_bonus": 1.3}},
        {"id": "goblin_scavenging_4", "name": "Legendary Scavenger", "description": "Generate 20,000,000,000 food with Goblins", "requirement": {"race_skill": "goblin", "resource": "food", "amount": 20000000000, "player_level": 50}, "reward": {"food_multiplier": 1.2, "goblin_food_bonus": 1.5, "resource_conversion_rate": 1.1}},
        {"id": "troll_strength_1", "name": "Novice Crusher", "description": "Generate 30,000 stone with Trolls", "requirement": {"race_skill": "troll", "resource": "stone", "amount": 30000}, "reward": {"stone_multiplier": 1.05, "troll_stone_bonus": 1.1}},
        {"id": "troll_strength_2", "name": "Adept Crusher", "description": "Generate 3,000,000 stone with Trolls", "requirement": {"race_skill": "troll", "resource": "stone", "amount": 3000000}, "reward": {"stone_multiplier": 1.1, "troll_stone_bonus": 1.2}},
        {"id": "troll_strength_3", "name": "Master Crusher", "description": "Generate 300,000,000 stone with Trolls", "requirement": {"race_skill": "troll", "resource": "stone", "amount": 300000000}, "reward": {"stone_multiplier": 1.15, "troll_stone_bonus": 1.3}},
        {"id": "troll_strength_4", "name": "Legendary Crusher", "description": "Generate 30,000,000,000 stone with Trolls", "requirement": {"race_skill": "troll", "resource": "stone", "amount": 30000000000, "player_level": 50}, "reward": {"stone_multiplier": 1.2, "troll_stone_bonus": 1.5, "food_consumption_reduction": 0.2}},
        {"id": "shade_magic_1", "name": "Novice Channeler", "description": "Generate 10,000 mana with Shades", "requirement": {"race_skill": "shade", "resource": "mana", "amount": 10000}, "reward": {"mana_multiplier": 1.05, "shade_mana_bonus": 1.1}},
        {"id": "shade_magic_2", "name": "Adept Channeler", "description": "Generate 1,000,000 mana with Shades", "requirement": {"race_skill": "shade", "resource": "mana", "amount": 1000000}, "reward": {"mana_multiplier": 1.1, "shade_mana_bonus": 1.2}},
        {"id": "shade_magic_3", "name": "Master Channeler", "description": "Generate 100,000,000 mana with Shades", "requirement": {"race_skill": "shade", "resource": "mana", "amount": 100000000}, "reward": {"mana_multiplier": 1.15, "shade_mana_bonus": 1.3}},
        {"id": "shade_magic_4", "name": "Legendary Channeler", "description": "Generate 10,000,000,000 mana with Shades", "requirement": {"race_skill": "shade", "resource": "mana", "amount": 10000000000, "player_level": 50}, "reward": {"mana_multiplier": 1.2, "shade_mana_bonus": 1.5, "production_doubling_chance": 0.05}},
        {"id": "time_skill_1", "name": "Skill Novice", "description": "Reach player level 20 within 2 days of playtime", "requirement": {"player_level": 20, "max_play_time": 172800}, "reward": {"all_production": 1.1}},
        {"id": "time_skill_2", "name": "Skill Adept", "description": "Reach player level 50 within 5 days of playtime", "requirement": {"player_level": 50, "max_play_time": 432000}, "reward": {"all_production": 1.2}},
        {"id": "time_skill_3", "name": "Skill Master", "description": "Reach player level 100 within 10 days of playtime", "requirement": {"player_level": 100, "max_play_time": 864000}, "reward": {"all_production": 1.3}},
        {"id": "time_skill_4", "name": "Skill Grandmaster", "description": "Reach player level 200 within 20 days of playtime", "requirement": {"player_level": 200, "max_play_time": 1728000}, "reward": {"all_production": 1.5, "prestige_point_multiplier": 1.2}},
        {"id": "deepling_knowledge_1", "name": "Abyssal Scholar", "description": "Generate 50,000 ancient knowledge with Deeplings", "requirement": {"race_skill": "deepling", "resource": "ancient_knowledge", "amount": 50000, "prestige_level": 3}, "reward": {"ancient_knowledge_multiplier": 1.1, "deepling_knowledge_bonus": 1.2}},
        {"id": "deepling_knowledge_2", "name": "Abyssal Sage", "description": "Generate 5,000,000 ancient knowledge with Deeplings", "requirement": {"race_skill": "deepling", "resource": "ancient_knowledge", "amount": 5000000, "prestige_level": 5}, "reward": {"ancient_knowledge_multiplier": 1.2, "deepling_knowledge_bonus": 1.5, "research_speed": 1.2}},
        {"id": "dragon_hoard_1", "name": "Dragon Treasurer", "description": "Accumulate 1,000,000,000 gold with Dragons", "requirement": {"race_skill": "dragon", "resource": "gold", "amount": 1000000000, "prestige_level": 4}, "reward": {"gold_multiplier": 1.2, "dragon_gold_bonus": 1.3}},
        {"id": "dragon_hoard_2", "name": "Dragon Overlord", "description": "Accumulate 100,000,000,000 gold with Dragons", "requirement": {"race_skill": "dragon", "resource": "gold", "amount": 100000000000, "prestige_level": 6}, "reward": {"gold_multiplier": 1.3, "dragon_gold_bonus": 1.6, "resource_transmutation_efficiency": 1.5}},
        {"id": "celestial_alignment_1", "name": "Stellar Harmonizer", "description": "Generate 1,000,000 of each resource with Celestials", "requirement": {"race_skill": "celestial", "all_resources": 1000000, "prestige_level": 5}, "reward": {"all_resources_multiplier": 1.1, "celestial_efficiency": 1.3}},
        {"id": "celestial_alignment_2", "name": "Cosmic Harmonizer", "description": "Generate 100,000,000 of each resource with Celestials", "requirement": {"race_skill": "celestial", "all_resources": 100000000, "prestige_level": 7}, "reward": {"all_resources_multiplier": 1.2, "celestial_efficiency": 1.5, "passive_prestige_generation": 0.0001}},
        {"id": "void_walker_mastery_1", "name": "Dimensional Adept", "description": "Generate 10,000,000 of each resource with Void Walkers", "requirement": {"race_skill": "void_walker", "all_resources": 10000000, "prestige_level": 5}, "reward": {"all_resources_multiplier": 1.15, "void_walker_efficiency": 1.3}},
        {"id": "void_walker_mastery_2", "name": "Dimensional Master", "description": "Generate 1,000,000,000 of each resource with Void Walkers", "requirement": {"race_skill": "void_walker", "all_resources": 1000000000, "prestige_level": 7}, "reward": {"all_resources_multiplier": 1.25, "void_walker_efficiency": 1.6, "parallel_production_bonus": 0.2}}
    ],
    "building_milestones": [
        {"id": "first_building", "name": "Builder", "description": "Construct your first building", "requirement": {"any_building": 1}, "reward": {"building_cost_reduction": 0.95}},
        {"id": "building_level_10", "name": "Master Builder", "description": "Upgrade any building to level 10", "requirement": {"any_building_level": 10}, "reward": {"building_efficiency": 1.05}},
        {"id": "all_buildings_5", "name": "Empire Builder", "description": "Have all basic buildings at level 5", "requirement": {"all_buildings": 5}, "reward": {"all_production": 1.1}},
        {"id": "cosmic_forge_1", "name": "Reality Shaper", "description": "Build the Cosmic Forge", "requirement": {"building": "cosmic_forge", "count": 1}, "reward": {"all_production": 1.5}}
    ],
    "prestige_milestones": [
        {"id": "first_prestige", "name": "Rebirth", "description": "Perform your first prestige", "requirement": {"prestige_count": 1}, "reward": {"prestige_point_bonus": 1}},
        {"id": "prestige_5", "name": "Cycle Master", "description": "Perform 5 prestiges", "requirement": {"prestige_count": 5}, "reward": {"prestige_point_multiplier": 1.1}},
        {"id": "prestige_20", "name": "Eternal Cycle", "description": "Perform 20 prestiges", "requirement": {"prestige_count": 20}, "reward": {"prestige_point_multiplier": 1.2}}
    ],
    "time_milestones": [
        {"id": "played_1_day", "name": "Dedicated", "description": "Play for a total of 24 hours", "requirement": {"play_time": 86400}, "reward": {"offline_progress_bonus": 0.1}},
        {"id": "played_1_week", "name": "Committed", "description": "Play for a total of 1 week", "requirement": {"play_time": 604800}, "reward": {"offline_progress_bonus": 0.2}},
        {"id": "played_1_month", "name": "Devoted", "description": "Play for a total of 1 month", "requirement": {"play_time": 2592000}, "reward": {"all_production": 1.5}}
    ]
}
