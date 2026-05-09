"""Race definitions.

Each race entry:
    name, description, base_cost (gold to recruit), resource_bonuses
    (per-resource production multipliers), unlock_level (player level),
    requires_prestige (optional), max_level (optional, default unbounded),
    special_abilities (per-ability dict with effects + unlock_requirements).

Unlock progression aims for ~one new race every ~5–10 player levels in the
early game, with eldritch races gated behind prestige cycles.
"""

RACES = {
    # -------------------- Tier 1: starting races (level 1) --------------------
    "dwarf": {
        "name": "Dwarves",
        "description": "Masters of mining and crafting. Generate more stone and gold.",
        "base_cost": 50,
        "resource_bonuses": {"gold": 1.2, "stone": 1.5},
        "unlock_level": 1,
        "special_abilities": {
            "mountain_heart": {
                "name": "Mountain Heart",
                "description": "Dwarves mine the core of mountains, doubling stone production and adding a 10% chance to find crystals when mining.",
                "effects": {"stone_multiplier": 2.0, "crystal_chance": 0.1},
                "unlock_requirements": {"race_level": 50, "prestige_level": 1, "resources": {"gold": 1000000, "stone": 500000}},
            },
            "master_smiths": {
                "name": "Master Smiths",
                "description": "Dwarven smiths forge powerful artifacts, increasing the efficiency of all buildings by 25%.",
                "effects": {"building_efficiency": 1.25},
                "unlock_requirements": {"race_level": 100, "prestige_level": 3, "resources": {"gold": 10000000, "crystal": 10000}},
            },
        },
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
                "description": "Elves cultivate ancient groves, tripling wood production and increasing mana regeneration by 50%.",
                "effects": {"wood_multiplier": 3.0, "mana_multiplier": 1.5},
                "unlock_requirements": {"race_level": 50, "prestige_level": 1, "resources": {"wood": 500000, "mana": 100000}},
            },
            "nature_harmony": {
                "name": "Nature's Harmony",
                "description": "Elves achieve perfect harmony with nature, generating all resources passively even without buildings.",
                "effects": {"passive_generation": 0.01},
                "unlock_requirements": {"race_level": 100, "prestige_level": 3, "resources": {"mana": 5000000, "crystal": 8000}},
            },
        },
    },
    "human": {
        "name": "Humans",
        "description": "Adaptable and industrious. Balanced resource generation.",
        "base_cost": 30,
        "resource_bonuses": {"food": 1.3, "gold": 1.1},
        "unlock_level": 1,
        "special_abilities": {
            "adaptability": {
                "name": "Adaptability",
                "description": "Humans adapt to any environment, gaining 40% bonus to all resource production.",
                "effects": {"all_resources_multiplier": 1.4},
                "unlock_requirements": {"race_level": 50, "prestige_level": 1, "resources": {"gold": 750000, "food": 750000}},
            },
            "technological_mastery": {
                "name": "Technological Mastery",
                "description": "Human innovation reduces all research costs by 50% and increases research effects by 25%.",
                "effects": {"research_cost_reduction": 0.5, "research_effect_bonus": 1.25},
                "unlock_requirements": {"race_level": 100, "prestige_level": 2, "resources": {"ancient_knowledge": 100000, "crystal": 5000}},
            },
        },
    },

    # -------------------- Tier 2: early-game (level 5–15) --------------------
    "goblin": {
        "name": "Goblins",
        "description": "Scrappy scavengers who find food and gold where others see refuse.",
        "base_cost": 40,
        "resource_bonuses": {"food": 1.4, "gold": 1.1},
        "unlock_level": 5,
        "special_abilities": {
            "scavenger_swarm": {
                "name": "Scavenger Swarm",
                "description": "Goblin swarms double food output and grant a 20% bonus to gold from looting.",
                "effects": {"food_multiplier": 2.0, "gold_multiplier": 1.2},
                "unlock_requirements": {"race_level": 50, "prestige_level": 1, "resources": {"food": 200000, "gold": 200000}},
            },
            "junk_alchemy": {
                "name": "Junk Alchemy",
                "description": "Goblins transmute scrap into useful resources, granting 10% conversion of food into all basic resources.",
                "effects": {"resource_conversion_rate": 1.1},
                "unlock_requirements": {"race_level": 100, "prestige_level": 2, "resources": {"food": 5000000, "crystal": 2000}},
            },
        },
    },
    "troll": {
        "name": "Trolls",
        "description": "Hulking brutes who crush stone and weather any storm.",
        "base_cost": 75,
        "resource_bonuses": {"stone": 1.6, "food": 0.9},
        "unlock_level": 8,
        "special_abilities": {
            "stone_crusher": {
                "name": "Stone Crusher",
                "description": "Trolls smash through bedrock, tripling stone production.",
                "effects": {"stone_multiplier": 3.0},
                "unlock_requirements": {"race_level": 50, "prestige_level": 1, "resources": {"stone": 1000000}},
            },
            "iron_stomach": {
                "name": "Iron Stomach",
                "description": "Trolls require 20% less food, freeing it up for the rest of the realm.",
                "effects": {"food_consumption_reduction": 0.2},
                "unlock_requirements": {"race_level": 100, "prestige_level": 2, "resources": {"stone": 10000000, "food": 1000000}},
            },
        },
    },
    "shade": {
        "name": "Shades",
        "description": "Spectral channelers who weave mana out of the dark between stars.",
        "base_cost": 120,
        "resource_bonuses": {"mana": 1.7, "ancient_knowledge": 1.1},
        "unlock_level": 12,
        "special_abilities": {
            "mana_weave": {
                "name": "Mana Weave",
                "description": "Shades weave dense lattices of mana, doubling mana production.",
                "effects": {"mana_multiplier": 2.0},
                "unlock_requirements": {"race_level": 50, "prestige_level": 1, "resources": {"mana": 250000}},
            },
            "echo_of_the_dead": {
                "name": "Echo of the Dead",
                "description": "Each production tick has a 5% chance to fire twice.",
                "effects": {"production_doubling_chance": 0.05},
                "unlock_requirements": {"race_level": 100, "prestige_level": 3, "resources": {"mana": 5000000, "ancient_knowledge": 100000}},
            },
        },
    },

    # -------------------- Tier 3: mid-game (level 18–25, prestige optional) --------------------
    "fae": {
        "name": "Fae",
        "description": "Capricious tricksters whose touch sweetens every harvest.",
        "base_cost": 250,
        "resource_bonuses": {"food": 1.4, "wood": 1.3, "mana": 1.2},
        "unlock_level": 18,
        "special_abilities": {
            "wild_growth": {
                "name": "Wild Growth",
                "description": "The Fae bless the realm with fertility — wood and food production +50%.",
                "effects": {"wood_multiplier": 1.5, "food_multiplier": 1.5},
                "unlock_requirements": {"race_level": 50, "prestige_level": 1, "resources": {"wood": 1000000, "food": 1000000}},
            },
            "trickster_luck": {
                "name": "Trickster's Luck",
                "description": "All resource generation has a 7% chance to fire twice.",
                "effects": {"production_doubling_chance": 0.07},
                "unlock_requirements": {"race_level": 100, "prestige_level": 2, "resources": {"mana": 2000000, "crystal": 3000}},
            },
        },
    },

    # -------------------- Tier 4: late-game, prestige-gated --------------------
    "celestial": {
        "name": "Celestials",
        "description": "Star-touched beings whose mere presence raises the very tides of magic.",
        "base_cost": 1000,
        "resource_bonuses": {"mana": 2.0, "crystal": 1.3, "ancient_knowledge": 1.2},
        "unlock_level": 25,
        "requires_prestige": 1,
        "special_abilities": {
            "starlight_blessing": {
                "name": "Starlight Blessing",
                "description": "Celestial light bathes the realm, granting +25% to all resources.",
                "effects": {"all_resources_multiplier": 1.25},
                "unlock_requirements": {"race_level": 50, "prestige_level": 2, "resources": {"mana": 5000000, "crystal": 50000}},
            },
            "cosmic_alignment": {
                "name": "Cosmic Alignment",
                "description": "When the heavens align, time itself bends — global production doubled.",
                "effects": {"global_multiplier": 2.0},
                "unlock_requirements": {"race_level": 100, "prestige_level": 5, "resources": {"crystal": 1000000, "ancient_knowledge": 1000000}},
            },
        },
    },
    "deepling": {
        "name": "Deeplings",
        "description": "Things that swam in the Abyss before the world was named. They remember.",
        "base_cost": 5000,
        "resource_bonuses": {"ancient_knowledge": 2.0, "mana": 1.4},
        "unlock_level": 35,
        "requires_prestige": 2,
        "special_abilities": {
            "abyssal_lore": {
                "name": "Abyssal Lore",
                "description": "Deeplings whisper forgotten knowledge — ancient knowledge production tripled.",
                "effects": {"ancient_knowledge_multiplier": 3.0},
                "unlock_requirements": {"race_level": 50, "prestige_level": 3, "resources": {"ancient_knowledge": 500000}},
            },
            "abyssal_gaze": {
                "name": "Abyssal Gaze",
                "description": "All research costs reduced by 40%; research effects amplified by 30%.",
                "effects": {"research_cost_reduction": 0.4, "research_effect_bonus": 1.3},
                "unlock_requirements": {"race_level": 100, "prestige_level": 5, "resources": {"ancient_knowledge": 10000000, "crystal": 100000}},
            },
        },
    },
    "dragon": {
        "name": "Dragons",
        "description": "Hoarders without peer. Where dragons roost, gold falls like rain.",
        "base_cost": 25000,
        "resource_bonuses": {"gold": 3.0, "crystal": 1.4},
        "unlock_level": 40,
        "requires_prestige": 2,
        "special_abilities": {
            "dragon_hoard": {
                "name": "Dragon's Hoard",
                "description": "Gold production tripled and gold cap effectively removed.",
                "effects": {"gold_multiplier": 3.0},
                "unlock_requirements": {"race_level": 50, "prestige_level": 4, "resources": {"gold": 100000000}},
            },
            "elder_breath": {
                "name": "Elder Breath",
                "description": "Dragonfire transmutes gold into rarer resources at +50% efficiency.",
                "effects": {"resource_transmutation_efficiency": 1.5},
                "unlock_requirements": {"race_level": 100, "prestige_level": 6, "resources": {"gold": 1000000000, "crystal": 500000}},
            },
        },
    },
    "void_walker": {
        "name": "Void Walkers",
        "description": "Travelers who walk between dimensions, returning with what they find.",
        "base_cost": 100000,
        "resource_bonuses": {"crystal": 1.8, "ancient_knowledge": 1.5, "mana": 1.5},
        "unlock_level": 50,
        "requires_prestige": 3,
        "special_abilities": {
            "dimensional_step": {
                "name": "Dimensional Step",
                "description": "Void Walkers harvest from parallel realms, granting +30% to all resources.",
                "effects": {"all_resources_multiplier": 1.3},
                "unlock_requirements": {"race_level": 50, "prestige_level": 5, "resources": {"crystal": 1000000, "ancient_knowledge": 5000000}},
            },
            "parallel_realms": {
                "name": "Parallel Realms",
                "description": "Production occurs simultaneously across realms — global production +20%.",
                "effects": {"parallel_production_bonus": 0.2, "global_multiplier": 1.2},
                "unlock_requirements": {"race_level": 100, "prestige_level": 7, "resources": {"crystal": 100000000, "ancient_knowledge": 100000000}},
            },
        },
    },
}
