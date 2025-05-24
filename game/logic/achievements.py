from game.constants import ACHIEVEMENTS, RESOURCE_TYPES, RACES, BASE_INCOME_RATE

# --- Achievement Checking Logic ---
def check_achievements(game_state):
    """Check for achievement completion"""
    check_resource_achievements(game_state)
    check_race_achievements(game_state)
    check_building_achievements(game_state)
    check_prestige_achievements(game_state)
    check_time_achievements(game_state)
    check_race_skill_achievements(game_state)

def check_resource_achievements(game_state):
    """Check resource-based achievements"""
    for milestone in ACHIEVEMENTS["resource_milestones"]:
        milestone_id = milestone["id"]
        
        # Skip if already achieved
        if game_state.achievements["resource_milestones"].get(milestone_id):
            continue
            
        # Check requirement
        requirement = milestone["requirement"]
        met_all_reqs = True
        for resource, amount in requirement.items():
            if game_state.resources.get(resource, 0) < amount:
                met_all_reqs = False
                break
        if met_all_reqs:
            game_state.achievements["resource_milestones"][milestone_id] = True
            game_state.add_notification(f"Achievement unlocked: {milestone['name']}!", notification_type="achievement")

def check_race_achievements(game_state):
    """Check race-based achievements"""
    for milestone in ACHIEVEMENTS["race_milestones"]:
        milestone_id = milestone["id"]
        
        # Skip if already achieved
        if game_state.achievements["race_milestones"].get(milestone_id):
            continue
            
        # Check requirement
        requirement = milestone["requirement"]
        
        # Check for specific race count
        if "race" in requirement and "count" in requirement:
            race_id = requirement["race"]
            count = requirement["count"]
            
            if race_id in game_state.races and game_state.races[race_id]["count"] >= count:
                game_state.achievements["race_milestones"][milestone_id] = True
                game_state.add_notification(f"Achievement unlocked: {milestone['name']}!", notification_type="achievement")
        
        # Check for all races at a certain count
        elif "all_races" in requirement:
            min_count = requirement["all_races"]
            all_races_meet_requirement = True
            
            for race_id, race_data in game_state.races.items():
                if race_data["unlocked"] and race_data["count"] < min_count:
                    all_races_meet_requirement = False
                    break
            
            if all_races_meet_requirement:
                game_state.achievements["race_milestones"][milestone_id] = True
                game_state.add_notification(f"Achievement unlocked: {milestone['name']}!", notification_type="achievement")

def check_building_achievements(game_state):
    """Check building-based achievements"""
    for milestone in ACHIEVEMENTS["building_milestones"]:
        milestone_id = milestone["id"]
        
        # Skip if already achieved
        if game_state.achievements["building_milestones"].get(milestone_id):
            continue
            
        # Check requirement
        requirement = milestone["requirement"]
        
        # Check for any building
        if "any_building" in requirement:
            count = requirement["any_building"]
            any_building_meets_requirement = False
            
            for building_id, building_data in game_state.buildings.items():
                if building_data["count"] >= count:
                    any_building_meets_requirement = True
                    break
            
            if any_building_meets_requirement:
                game_state.achievements["building_milestones"][milestone_id] = True
                game_state.add_notification(f"Achievement unlocked: {milestone['name']}!", notification_type="achievement")
        
        # Check for any building level
        elif "any_building_level" in requirement:
            level = requirement["any_building_level"]
            any_building_meets_level = False
            
            for building_id, building_data in game_state.buildings.items():
                if building_data["count"] > 0 and building_data["level"] >= level:
                    any_building_meets_level = True
                    break
            
            if any_building_meets_level:
                game_state.achievements["building_milestones"][milestone_id] = True
                game_state.add_notification(f"Achievement unlocked: {milestone['name']}!", notification_type="achievement")
        
        # Check for all buildings at a certain level
        elif "all_buildings" in requirement:
            min_level = requirement["all_buildings"]
            all_buildings_meet_requirement = True
            any_buildings_exist = False
            
            for building_id, building_data in game_state.buildings.items():
                # Only consider unlocked buildings with at least one built
                if building_data["unlocked"] and building_data["count"] > 0:
                    any_buildings_exist = True # Ensure there's at least one building to check
                    if building_data["level"] < min_level:
                        all_buildings_meet_requirement = False
                        break
            
            if any_buildings_exist and all_buildings_meet_requirement: # Check if any buildings exist before granting
                game_state.achievements["building_milestones"][milestone_id] = True
                game_state.add_notification(f"Achievement unlocked: {milestone['name']}!", notification_type="achievement")
        
        # Check for specific building
        elif "building" in requirement and "count" in requirement:
            building_id = requirement["building"]
            count = requirement["count"]
            
            if building_id in game_state.buildings and game_state.buildings[building_id]["count"] >= count:
                game_state.achievements["building_milestones"][milestone_id] = True
                game_state.add_notification(f"Achievement unlocked: {milestone['name']}!", notification_type="achievement")

def check_prestige_achievements(game_state):
    """Check prestige-based achievements"""
    for milestone in ACHIEVEMENTS["prestige_milestones"]:
        milestone_id = milestone["id"]
        
        # Skip if already achieved
        if game_state.achievements["prestige_milestones"].get(milestone_id):
            continue
            
        # Check requirement
        requirement = milestone["requirement"]
        
        if "prestige_count" in requirement:
            count = requirement["prestige_count"]
            
            if game_state.prestige_count >= count:
                game_state.achievements["prestige_milestones"][milestone_id] = True
                game_state.add_notification(f"Achievement unlocked: {milestone['name']}!", notification_type="achievement")

def check_time_achievements(game_state):
    """Check time-based achievements"""
    for milestone in ACHIEVEMENTS["time_milestones"]:
        milestone_id = milestone["id"]
        
        # Skip if already achieved
        if game_state.achievements["time_milestones"].get(milestone_id):
            continue
            
        # Check requirement
        requirement = milestone["requirement"]
        
        if "play_time" in requirement:
            seconds = requirement["play_time"]
            
            if game_state.total_play_time >= seconds:
                game_state.achievements["time_milestones"][milestone_id] = True
                game_state.add_notification(f"Achievement unlocked: {milestone['name']}!", notification_type="achievement")

def track_race_resource_generation(game_state, resource, amount):
    """Track resources generated by each race for skill achievements"""
    race_contributions = {}
    total_contribution = 0
    
    for race_id, race_data in game_state.races.items():
        if race_data["unlocked"] and race_data["count"] > 0:
            race_info = RACES[race_id]
            race_contribution = BASE_INCOME_RATE * race_data["count"] * race_data["level"]
            
            if "resource_bonuses" in race_info and resource in race_info["resource_bonuses"]:
                # Assuming get_race_bonus_multiplier is a method of game_state
                bonus = race_info["resource_bonuses"][resource] * game_state.get_race_bonus_multiplier()
                race_contribution *= bonus
            
            # Assuming get_race_specific_ability_bonus is a method of game_state
            ability_bonus = game_state.get_race_specific_ability_bonus(race_id, resource)
            race_contribution *= ability_bonus
            
            race_contributions[race_id] = race_contribution
            total_contribution += race_contribution
    
    if total_contribution <= 0:
        return
    
    for race_id, contribution in race_contributions.items():
        proportion = contribution / total_contribution
        race_amount = amount * proportion
        if resource in game_state.races[race_id]["skills"]:
            game_state.races[race_id]["skills"][resource] += race_amount
        else: # Should not happen if initialized correctly
            game_state.races[race_id]["skills"][resource] = race_amount


def check_race_skill_achievements(game_state):
    """Check race skill-based achievements"""
    for milestone in ACHIEVEMENTS["race_skill_milestones"]:
        milestone_id = milestone["id"]
        
        if game_state.achievements["race_skill_milestones"].get(milestone_id):
            continue
            
        requirement = milestone["requirement"]
        
        if "race_skill" in requirement and "resource" in requirement and "amount" in requirement:
            race_id = requirement["race_skill"]
            resource_key = requirement["resource"]
            required_amount = requirement["amount"]
            
            if race_id not in game_state.races or not game_state.races[race_id]["unlocked"]:
                continue
            if "player_level" in requirement and game_state.player_level < requirement["player_level"]:
                continue
            if "prestige_level" in requirement and game_state.prestige_count < requirement["prestige_level"]:
                continue
            
            if game_state.races[race_id]["skills"].get(resource_key, 0) >= required_amount:
                game_state.achievements["race_skill_milestones"][milestone_id] = True
                game_state.add_notification(f"Achievement unlocked: {milestone['name']}!", notification_type="achievement")
        
        elif "race_skill" in requirement and "all_resources" in requirement:
            race_id = requirement["race_skill"]
            min_amount = requirement["all_resources"]
            
            if race_id not in game_state.races or not game_state.races[race_id]["unlocked"]:
                continue
            if "player_level" in requirement and game_state.player_level < requirement["player_level"]:
                continue
            if "prestige_level" in requirement and game_state.prestige_count < requirement["prestige_level"]:
                continue
            
            all_resources_meet_requirement = True
            for resource_type in RESOURCE_TYPES:
                if resource_type == "prestige_points": continue
                if game_state.races[race_id]["skills"].get(resource_type, 0) < min_amount:
                    all_resources_meet_requirement = False
                    break
            
            if all_resources_meet_requirement:
                game_state.achievements["race_skill_milestones"][milestone_id] = True
                game_state.add_notification(f"Achievement unlocked: {milestone['name']}!", notification_type="achievement")
        
        elif "player_level" in requirement and "max_play_time" in requirement:
            player_level_req = requirement["player_level"]
            max_play_time_req = requirement["max_play_time"]
            
            if game_state.player_level >= player_level_req and game_state.total_play_time <= max_play_time_req:
                game_state.achievements["race_skill_milestones"][milestone_id] = True
                game_state.add_notification(f"Achievement unlocked: {milestone['name']}!", notification_type="achievement")

def get_achievement_multiplier(game_state, resource):
    """Get production multiplier from achievements"""
    multiplier = 1.0
    
    # Check resource-specific multipliers from resource_milestones
    for milestone_details in ACHIEVEMENTS["resource_milestones"]:
        milestone_id = milestone_details["id"]
        if game_state.achievements["resource_milestones"].get(milestone_id):
            reward = milestone_details["reward"]
            if f"{resource}_multiplier" in reward:
                multiplier *= reward[f"{resource}_multiplier"]
    
    # Check global production multipliers from all achievement categories
    for category_key, achievement_list in ACHIEVEMENTS.items():
        if category_key not in game_state.achievements: continue

        for achievement_details in achievement_list:
            achievement_id = achievement_details["id"]
            if game_state.achievements[category_key].get(achievement_id):
                reward = achievement_details["reward"]
                if "all_production" in reward:
                    multiplier *= reward["all_production"]
    return multiplier

def has_achievement(game_state, achievement_id):
    """Check if an achievement has been unlocked across all categories"""
    for category_key in game_state.achievements.keys():
        if game_state.achievements[category_key].get(achievement_id):
            return True
    return False
