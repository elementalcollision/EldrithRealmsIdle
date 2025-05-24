import random
import time # Make sure time is imported if used (e.g. in get_time_based_modifier)
from game.constants import RACES, RESOURCE_TYPES, BUILDINGS # BUILDINGS needed for one ability effect

# --- Race Ability Logic ---

def check_race_ability_unlocks(game_state):
    """Check if any race abilities can be unlocked"""
    for race_id, race_data in game_state.races.items():
        if race_data["unlocked"] and race_data["count"] > 0:
            race_info = RACES[race_id]
            
            if "special_abilities" not in race_info:
                continue
                
            if "abilities" not in race_data: 
                race_data["abilities"] = {}
                for ability_id_key in race_info["special_abilities"]:
                    race_data["abilities"][ability_id_key] = {"unlocked": False, "active": False}
                    
            for ability_id, ability_info in race_info["special_abilities"].items():
                if ability_id not in race_data["abilities"]: 
                     race_data["abilities"][ability_id] = {"unlocked": False, "active": False}

                if race_data["abilities"][ability_id]["unlocked"]:
                    continue
                    
                req = ability_info["unlock_requirements"]
                
                if race_data["level"] < req["race_level"]:
                    continue
                if game_state.prestige_count < req["prestige_level"]:
                    continue
                    
                can_afford_resources = True
                for resource, amount in req["resources"].items():
                    if game_state.resources.get(resource, 0) < amount:
                        can_afford_resources = False
                        break
                if not can_afford_resources:
                    continue
                    
                race_data["abilities"][ability_id]["unlocked"] = True
                for resource, amount in req["resources"].items():
                    game_state.resources[resource] -= amount
                
                game_state.add_notification(f"New race ability unlocked: {race_info['name']} - {ability_info['name']}!", notification_type="unlock")

def activate_race_ability(game_state, race_id, ability_id):
    """Activate a race ability"""
    if race_id not in game_state.races:
        return False
        
    race_data = game_state.races[race_id]
    
    if "abilities" not in race_data or ability_id not in race_data["abilities"]:
        return False
        
    ability_data = race_data["abilities"][ability_id]
    if not ability_data["unlocked"]:
        return False
        
    ability_data["active"] = not ability_data["active"]
    
    race_info = RACES[race_id]
    ability_info = race_info["special_abilities"][ability_id]
    status = "activated" if ability_data["active"] else "deactivated"
    game_state.add_notification(f"{race_info['name']} ability {ability_info['name']} {status}!", notification_type="info")
    
    return True

def get_race_ability_multiplier(game_state, resource):
    """Get the multiplier for a resource from race abilities"""
    multiplier = 1.0
    
    for race_id, race_data in game_state.races.items():
        if not race_data["unlocked"] or race_data["count"] <= 0:
            continue
            
        race_info = RACES[race_id]
        if "special_abilities" not in race_info or "abilities" not in race_data:
            continue
            
        for ability_id, ability_state in race_data["abilities"].items():
            if not ability_state["unlocked"] or not ability_state["active"]:
                continue
                
            ability_info = race_info["special_abilities"][ability_id]
            effects = ability_info["effects"]
            
            if f"{resource}_multiplier" in effects:
                multiplier *= effects[f"{resource}_multiplier"]
            if "all_resources_multiplier" in effects:
                multiplier *= effects["all_resources_multiplier"]
            if "building_efficiency" in effects:
                for building_id_iter, building_data_iter in game_state.buildings.items():
                    if building_data_iter["count"] > 0 and "resource_production" in BUILDINGS[building_id_iter]:
                        if resource in BUILDINGS[building_id_iter]["resource_production"]:
                            multiplier *= effects["building_efficiency"]
                            break 
    return multiplier

def get_race_specific_ability_bonus(game_state, race_id, resource):
    """Get race-specific ability bonus for a resource"""
    bonus = 1.0
    
    if race_id not in game_state.races or not game_state.races[race_id]["unlocked"]:
        return bonus
        
    race_data = game_state.races[race_id]
    race_info = RACES[race_id]
    
    if "special_abilities" not in race_info or "abilities" not in race_data:
        return bonus
            
    for ability_id, ability_state in race_data["abilities"].items():
        if not ability_state["unlocked"] or not ability_state["active"]:
            continue
            
        ability_info = race_info["special_abilities"][ability_id]
        effects = ability_info["effects"]
        
        if "per_unit_bonus" in effects: # This is usually a flat bonus per unit, not a multiplier
            bonus += effects["per_unit_bonus"] * race_data["count"]
        if "gold_storage_bonus" in effects and resource == "gold": # This is also additive based on gold
            bonus += (game_state.resources.get("gold",0) / 1000) * effects["gold_storage_bonus"] # Use .get for safety
            
    return bonus

def get_passive_generation_rate(game_state, resource):
    """Get passive generation rate for a resource from race abilities"""
    rate = 0.0
    
    for race_id, race_data in game_state.races.items():
        if not race_data["unlocked"] or race_data["count"] <= 0:
            continue
            
        race_info = RACES[race_id]
        if "special_abilities" not in race_info or "abilities" not in race_data:
            continue
            
        for ability_id, ability_state in race_data["abilities"].items():
            if not ability_state["unlocked"] or not ability_state["active"]:
                continue
                
            ability_info = race_info["special_abilities"][ability_id]
            effects = ability_info["effects"]
            
            if "passive_generation" in effects:
                rate += effects["passive_generation"] * game_state.player_level
    return rate

def get_time_based_modifier(game_state, resource):
    """Get time-based modifier for resource generation"""
    modifier = 1.0
    
    for race_id, race_data in game_state.races.items():
        if not race_data["unlocked"] or race_data["count"] <= 0:
            continue
            
        race_info = RACES[race_id]
        if "special_abilities" not in race_info or "abilities" not in race_data:
            continue
            
        for ability_id, ability_state in race_data["abilities"].items():
            if not ability_state["unlocked"] or not ability_state["active"]:
                continue
                
            ability_info = race_info["special_abilities"][ability_id]
            effects = ability_info["effects"]
            
            if "timed_production_bonus" in effects:
                current_time_sec = int(time.time()) 
                alignment_duration = effects.get("alignment_duration", 300)
                if (current_time_sec % 3600) < alignment_duration:
                    modifier *= effects["timed_production_bonus"]
    return modifier

def check_production_doubling_chance(game_state):
    """Check if production should be doubled based on race abilities"""
    for race_id, race_data in game_state.races.items():
        if not race_data["unlocked"] or race_data["count"] <= 0:
            continue
            
        race_info = RACES[race_id]
        if "special_abilities" not in race_info or "abilities" not in race_data:
            continue
            
        for ability_id, ability_state in race_data["abilities"].items():
            if not ability_state["unlocked"] or not ability_state["active"]:
                continue
                
            ability_info = race_info["special_abilities"][ability_id]
            effects = ability_info["effects"]
            
            if "production_doubling_chance" in effects:
                if random.random() < effects["production_doubling_chance"]:
                    return True
    return False

def apply_special_resource_generation(game_state, elapsed_time):
    """Apply special resource generation from race abilities"""
    for race_id, race_data in game_state.races.items():
        if not race_data["unlocked"] or race_data["count"] <= 0:
            continue
            
        race_info = RACES[race_id]
        if "special_abilities" not in race_info or "abilities" not in race_data:
            continue
            
        for ability_id, ability_state in race_data["abilities"].items():
            if not ability_state["unlocked"] or not ability_state["active"]:
                continue
                
            ability_info = race_info["special_abilities"][ability_id]
            effects = ability_info["effects"]
            
            if "random_resource_generation" in effects:
                chance = effects["random_resource_generation"] * elapsed_time
                if random.random() < chance:
                    resource_choice = random.choice([r for r in RESOURCE_TYPES if r != "prestige_points"])
                    amount = game_state.player_level * 10 * (1 + game_state.prestige_count * 0.5)
                    game_state.resources[resource_choice] = game_state.resources.get(resource_choice, 0) + amount
                    game_state.add_notification(f"Fae glamour generated {amount:.0f} {resource_choice}!", notification_type="info")
            
            if "resource_conversion" in effects:
                max_rate = 0
                max_resource = None
                for res_key in RESOURCE_TYPES:
                    if res_key == "prestige_points": continue
                    rate = game_state.calculate_resource_generation_rate(res_key) 
                    if rate > max_rate:
                        max_rate = rate
                        max_resource = res_key
                
                if max_resource and max_rate > 0:
                    conversion_rate_eff = effects["resource_conversion"] * elapsed_time
                    for res_key_target in RESOURCE_TYPES:
                        if res_key_target == "prestige_points" or res_key_target == max_resource: continue
                        amount_converted = max_rate * conversion_rate_eff
                        game_state.resources[res_key_target] = game_state.resources.get(res_key_target, 0) + amount_converted
            
            if "resource_transmutation" in effects and hasattr(game_state, "transmutation_source") and hasattr(game_state, "transmutation_target"):
                source = game_state.transmutation_source
                target = game_state.transmutation_target
                if source in RESOURCE_TYPES and target in RESOURCE_TYPES and source != target and game_state.resources.get(source, 0) > 0:
                    amount_to_convert = min(game_state.resources.get(source,0) * 0.01 * elapsed_time, game_state.resources.get(source,0))
                    if amount_to_convert > 0:
                        game_state.resources[source] -= amount_to_convert
                        game_state.resources[target] = game_state.resources.get(target,0) + amount_to_convert * effects["resource_transmutation"]
            
            if "stone_to_crystal_conversion" in effects:
                stone_produced = game_state.calculate_resource_generation_rate("stone") * elapsed_time 
                if stone_produced > 0:
                    crystal_amount = stone_produced * effects["stone_to_crystal_conversion"]
                    game_state.resources["crystal"] = game_state.resources.get("crystal",0) + crystal_amount
            
            if "parallel_production" in effects:
                for res_key_parallel in RESOURCE_TYPES:
                    if res_key_parallel == "prestige_points": continue
                    rate = game_state.calculate_resource_generation_rate(res_key_parallel) 
                    amount_parallel = rate * elapsed_time * effects["parallel_production"]
                    game_state.resources[res_key_parallel] = game_state.resources.get(res_key_parallel, 0) + amount_parallel

def generate_passive_prestige_points(game_state, elapsed_time):
    """Generate passive prestige points from race abilities"""
    for race_id, race_data in game_state.races.items():
        if not race_data["unlocked"] or race_data["count"] <= 0:
            continue
            
        race_info = RACES[race_id]
        if "special_abilities" not in race_info or "abilities" not in race_data:
            continue
            
        for ability_id, ability_state in race_data["abilities"].items():
            if not ability_state["unlocked"] or not ability_state["active"]:
                continue
                
            ability_info = race_info["special_abilities"][ability_id]
            effects = ability_info["effects"]
            
            if "passive_prestige_generation" in effects:
                points = game_state.total_earnings * effects["passive_prestige_generation"] * elapsed_time
                game_state.resources["prestige_points"] = game_state.resources.get("prestige_points", 0) + points
                game_state.total_prestige_points += points
