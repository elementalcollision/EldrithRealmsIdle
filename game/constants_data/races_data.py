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
    }
    # ... (add the rest of the races as needed) ...
}
