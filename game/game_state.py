import time
import json
import os
import zlib
import base64
import pygame 

from game.constants import (RESOURCE_TYPES, RACES, BUILDINGS, RESEARCH, 
                           PRESTIGE_UPGRADES, ACHIEVEMENTS, BASE_INCOME_RATE, 
                           PRESTIGE_REQUIREMENT_BASE, PRESTIGE_SCALING, PRESTIGE_BONUS_BASE,
                           OFFLINE_PROGRESS_RATE, TIME_WARP_DURATION, TIME_WARP_COOLDOWN)

from game.logic import achievements as achievement_logic
from game.logic import race_abilities as ability_logic

class GameState:
    def __init__(self):
        # Initialize resources
        self.resources = {resource: 0 for resource in RESOURCE_TYPES}
        self.resources["gold"] = 100  # Starting gold
        
        # Initialize races
        self.races = {}
        for race_id, race_data_const in RACES.items(): 
            race_abilities = {}
            if "special_abilities" in race_data_const:
                for ability_id_key in race_data_const["special_abilities"]:
                    race_abilities[ability_id_key] = {
                        "unlocked": False,
                        "active": False
                    }
            
            race_skills = {}
            for resource in RESOURCE_TYPES:
                race_skills[resource] = 0
                    
            self.races[race_id] = {
                "count": 0,
                "level": 1,
                "unlocked": race_data_const["unlock_level"] == 1,
                "abilities": race_abilities,
                "skills": race_skills
            }
        
        # Initialize buildings
        self.buildings = {}
        for building_id, building_data_const in BUILDINGS.items(): 
            self.buildings[building_id] = {
                "count": 0,
                "level": 1,
                "unlocked": building_data_const["unlock_level"] <= 1
            }
            
        # Initialize research
        self.research = {}
        for research_id, research_data_const in RESEARCH.items(): 
            self.research[research_id] = {
                "level": 0,
                "unlocked": research_data_const["unlock_level"] <= 1
            }
            
        # Initialize prestige upgrades
        self.prestige_upgrades = {}
        for upgrade_id, _ in PRESTIGE_UPGRADES.items(): 
            self.prestige_upgrades[upgrade_id] = {
                "level": 0
            }
            
        # Initialize achievements (ensure all categories are present)
        self.achievements = {}
        for category_key, achievement_list in ACHIEVEMENTS.items():
            self.achievements[category_key] = {milestone["id"]: False for milestone in achievement_list}

        # Game progression
        self.player_level = 1
        self.total_earnings = 0
        self.prestige_count = 0
        self.prestige_points = 0
        self.total_prestige_points = 0
        self.permanent_multipliers = {"all": 1.0}
        
        # Time tracking
        self.last_save_time = time.time()
        self.total_play_time = 0
        self.time_warp_active = False
        self.time_warp_end_time = 0
        self.time_warp_cooldown_end = 0
        
        # Notifications
        self.notifications = []
    
    def update(self, elapsed_time):
        if self.time_warp_active:
            current_time = time.time()
            if current_time >= self.time_warp_end_time:
                self.time_warp_active = False
                self.add_notification("Time Warp has ended!", notification_type="info")
            else:
                time_warp_multiplier = self.get_time_warp_multiplier()
                elapsed_time *= time_warp_multiplier
        
        self.total_play_time += elapsed_time
        self.generate_resources(elapsed_time)
        self.check_unlocks()
        achievement_logic.check_achievements(self)
    
    def generate_resources(self, elapsed_time):
        ability_logic.apply_special_resource_generation(self, elapsed_time)
        
        for resource in RESOURCE_TYPES:
            if resource == "prestige_points": continue
                
            generation_rate = self.calculate_resource_generation_rate(resource)
            amount_generated = generation_rate * elapsed_time
            global_multiplier = self.calculate_global_multiplier(resource)
            amount_generated *= global_multiplier
            time_modifier = ability_logic.get_time_based_modifier(self, resource)
            amount_generated *= time_modifier
            
            if ability_logic.check_production_doubling_chance(self):
                amount_generated *= 2
                
            self.resources[resource] = self.resources.get(resource, 0) + amount_generated
            
            if resource == "gold": self.total_earnings += amount_generated
            achievement_logic.track_race_resource_generation(self, resource, amount_generated)
                
        ability_logic.generate_passive_prestige_points(self, elapsed_time)
    
    def calculate_resource_generation_rate(self, resource):
        base_rate = 0
        base_rate += ability_logic.get_passive_generation_rate(self, resource)
        
        race_bonus_mult = self.get_race_bonus_multiplier()
        for race_id, race_data in self.races.items():
            if race_data["unlocked"] and race_data["count"] > 0:
                race_info = RACES[race_id]
                race_contrib = BASE_INCOME_RATE * race_data["count"] * race_data["level"]
                if "resource_bonuses" in race_info and resource in race_info["resource_bonuses"]:
                    bonus_cfg = race_info["resource_bonuses"][resource]
                    bonus_val = bonus_cfg.get("base", bonus_cfg) if isinstance(bonus_cfg, dict) else bonus_cfg
                    race_contrib *= (bonus_val * race_bonus_mult)
                race_contrib *= ability_logic.get_race_specific_ability_bonus(self, race_id, resource)
                race_contrib *= self.get_race_skill_multiplier(race_id, resource) 
                base_rate += race_contrib
        
        for b_id, b_data in self.buildings.items():
            if b_data["unlocked"] and b_data["count"] > 0:
                b_info = BUILDINGS[b_id]
                if "resource_production" in b_info and resource in b_info["resource_production"]:
                    lvl_scale = b_info.get("level_scaling", 1.0)
                    base_rate += b_info["resource_production"][resource] * b_data["count"] * (lvl_scale ** (b_data["level"] - 1))
        
        base_rate += self.get_research_flat_bonus(resource) 
        return base_rate
    
    def calculate_global_multiplier(self, resource):
        multiplier = 1.0
        for b_id, b_data in self.buildings.items():
            if b_data["unlocked"] and b_data["count"] > 0:
                b_info = BUILDINGS[b_id]
                if "global_multipliers" in b_info:
                    lvl_scale_key = b_info.get("level_scaling_multiplier_key", "level_scaling") # Use specific or default
                    lvl_bonus_factor = b_info.get(lvl_scale_key, 1.0)
                    lvl_bonus = (lvl_bonus_factor - 1.0) * (b_data["level"] - 1) if b_data['level'] > 1 else 0.0

                    if resource in b_info["global_multipliers"]:
                        base_mult = b_info["global_multipliers"][resource]
                        multiplier *= (base_mult + lvl_bonus if base_mult >= 1.0 else base_mult * (1.0 + lvl_bonus))
                    if "all" in b_info["global_multipliers"]:
                        all_mult_base = b_info["global_multipliers"]["all"]
                        multiplier *= (all_mult_base + lvl_bonus if all_mult_base >= 1.0 else all_mult_base * (1.0 + lvl_bonus))
        
        multiplier *= ability_logic.get_race_ability_multiplier(self, resource)
        multiplier *= achievement_logic.get_achievement_multiplier(self, resource)
        multiplier *= self.get_research_multiplier(resource)
        
        multiplier *= (1.0 + (self.prestige_count * PRESTIGE_BONUS_BASE))
        if resource in self.permanent_multipliers: multiplier *= self.permanent_multipliers[resource]
        if "all" in self.permanent_multipliers: multiplier *= self.permanent_multipliers["all"]
        return multiplier
    
    def can_afford(self, costs):
        return all(self.resources.get(r,0) >= a for r,a in costs.items())
    
    def spend_resources(self, costs):
        if not self.can_afford(costs): return False
        for r,a in costs.items(): self.resources[r] -= a
        return True
    
    def add_race(self, race_id, count=1):
        if race_id in self.races and self.races[race_id]["unlocked"]:
            self.races[race_id]["count"] += count; return True
        return False
    
    def upgrade_race(self, race_id, count=1):
        if race_id in self.races and self.races[race_id]["unlocked"] and self.races[race_id]["count"] > 0:
            info, data = RACES[race_id], self.races[race_id]
            max_lvl = info.get("max_level", float('inf'))
            upgrades = min(count, max_lvl - data["level"] if max_lvl != float('inf') else count)
            if upgrades <= 0: return False
            data["level"] += upgrades; return True
        return False
    
    def add_building(self, building_id, count=1):
        if building_id in self.buildings and self.buildings[building_id]["unlocked"]:
            self.buildings[building_id]["count"] += count
            if count > 0 and self.buildings[building_id]["count"] == count: # Check for first build of this type
                 achievement_logic.check_building_achievements(self) 
            return True
        return False
    
    def upgrade_building(self, building_id, count=1):
        if building_id in self.buildings and self.buildings[building_id]["unlocked"] and self.buildings[building_id]["count"] > 0:
            info, data = BUILDINGS[building_id], self.buildings[building_id]
            upgrades = min(count, info["max_level"] - data["level"])
            if upgrades <= 0: return False
            data["level"] += upgrades
            achievement_logic.check_building_achievements(self)
            return True
        return False
    
    def research_technology(self, research_id):
        if research_id in self.research and self.research[research_id]["unlocked"]:
            info, data = RESEARCH[research_id], self.research[research_id]
            if data["level"] >= info["max_level"]: return False
            data["level"] += 1; return True
        return False
    
    def purchase_prestige_upgrade(self, upgrade_id):
        if upgrade_id in self.prestige_upgrades:
            info, data = PRESTIGE_UPGRADES[upgrade_id], self.prestige_upgrades[upgrade_id]
            if data["level"] >= info["max_level"]: return False
            data["level"] += 1
            if upgrade_id=="cosmic_insight": self.permanent_multipliers["all"] *= info["effect"]["permanent_multiplier"]
            return True
        return False
    
    def check_unlocks(self):
        new_level = 1 + int(self.total_earnings / 1000)
        if new_level > self.player_level:
            self.player_level = new_level
            self.add_notification(f"Level up! You are now level {self.player_level}", notification_type="unlock")
            for r_id, r_const in RACES.items():
                if not self.races[r_id]["unlocked"] and r_const["unlock_level"]<=self.player_level and self.prestige_count>=r_const.get("requires_prestige",0):
                    self.races[r_id]["unlocked"]=True; self.add_notification(f"New race unlocked: {r_const['name']}!",notification_type="unlock")
        
        ability_logic.check_race_ability_unlocks(self)
        
        for b_id, b_const in BUILDINGS.items():
            if not self.buildings[b_id]["unlocked"] and b_const["unlock_level"]<=self.player_level and self.prestige_count>=b_const.get("requires_prestige",0):
                self.buildings[b_id]["unlocked"]=True; self.add_notification(f"New building unlocked: {b_const['name']}!",notification_type="unlock")
        for res_id, res_const in RESEARCH.items():
            if not self.research[res_id]["unlocked"] and res_const["unlock_level"]<=self.player_level and self.prestige_count>=res_const.get("requires_prestige",0):
                self.research[res_id]["unlocked"]=True; self.add_notification(f"New research unlocked: {res_const['name']}!",notification_type="unlock")

    def get_race_purchase_cost(self, race_id, count=1):
        if race_id not in RACES: return {}
        info, data = RACES[race_id], self.races[race_id]
        cost, cur_c = info["base_cost"], data["count"]
        if count==1: return {"gold":cost*(1.0+(0.15*cur_c))}
        return {"gold":sum(cost*(1.0+(0.15*(cur_c+i))) for i in range(count))}

    def get_race_upgrade_cost(self, race_id, count=1):
        if race_id not in RACES: return {}
        info, data = RACES[race_id], self.races[race_id]
        cost, cur_l = info["base_cost"]*5, data["level"]
        if count==1: return {"gold":cost*(2.0**(cur_l-1))}
        return {"gold":sum(cost*(2.0**(cur_l+i-1)) for i in range(count))}

    def get_building_purchase_cost(self, building_id, count=1):
        if building_id not in BUILDINGS: return {}
        info, data = BUILDINGS[building_id], self.buildings[building_id]
        b_costs, cur_c = info["base_cost"], data["count"]
        costs={}
        reduct=0.95 if achievement_logic.has_achievement(self,"first_building") else 1.0
        if count==1:
            for r,a in b_costs.items():costs[r]=a*(1.0+(0.2*cur_c))*reduct
        else:
            for r,b_a in b_costs.items():costs[r]=sum(b_a*(1.0+(0.2*(cur_c+i)))*reduct for i in range(count))
        return costs

    def get_building_upgrade_cost(self, building_id, count=1):
        if building_id not in BUILDINGS: return {}
        info, data = BUILDINGS[building_id], self.buildings[building_id]
        b_costs, cur_l = info["base_cost"], data["level"]
        costs={}
        reduct=0.95 if achievement_logic.has_achievement(self,"first_building") else 1.0
        up_mult=2.0
        if count==1:
            for r,a in b_costs.items():costs[r]=a*(2.0**(cur_l-1))*reduct*up_mult
        else:
            for r,b_a in b_costs.items():costs[r]=sum(b_a*(2.0**(cur_l+i-1))*reduct*up_mult for i in range(count))
        return costs

    def get_research_cost(self, research_id, count=1, current_level_override=None):
        if research_id not in RESEARCH: return {}
        info = RESEARCH[research_id]
        start_lvl = current_level_override if current_level_override is not None else self.research[research_id]["level"]
        actual_cnt = int(count) if count!=-1 else 1
        costs,b_costs,scale={},info["cost"],info["cost_scaling"]
        if actual_cnt==1:
            for r,a in b_costs.items():costs[r]=a*(scale**start_lvl)
        else:
            for r,b_a in b_costs.items():costs[r]=sum(b_a*(scale**(start_lvl+i)) for i in range(actual_cnt))
        return costs

    def get_prestige_upgrade_cost(self, upgrade_id, count=1, current_level_override=None):
        if upgrade_id not in PRESTIGE_UPGRADES: return {}
        info = PRESTIGE_UPGRADES[upgrade_id]
        start_lvl = current_level_override if current_level_override is not None else self.prestige_upgrades[upgrade_id]["level"]
        actual_cnt = int(count) if count!=-1 else 1
        costs,b_costs,scale={},info["cost"],info.get("cost_scaling",1.0)
        if actual_cnt==1:
            mult = scale**start_lvl if start_lvl>0 and scale !=1.0 else 1.0 # Avoid 1.0 ** large_number if scale is 1
            if start_lvl == 0 and info.get("cost_scaling") : cost_multiplier = 1.0 # First level generally doesn't apply scaling unless base cost is for level 0
            else: cost_multiplier = scale ** start_lvl if scale != 1.0 else 1.0

            for r,a in b_costs.items():costs[r]=a*cost_multiplier
        else:
            for r,b_a in b_costs.items():
                total_c = 0
                for i in range(actual_cnt):
                    lvl_to_calc = start_lvl + i
                    cost_multiplier_lvl = scale ** lvl_to_calc if lvl_to_calc > 0 and scale != 1.0 else 1.0
                    if lvl_to_calc == 0 and info.get("cost_scaling"): cost_multiplier_lvl = 1.0
                    total_c += b_a * cost_multiplier_lvl
                costs[r] = total_c
        return costs

    def calculate_max_affordable_levels(self, item_id, cost_func_name, current_lvl, max_cap):
        cost_func = getattr(self, cost_func_name)
        affordable_lvls = 0
        sim_res = self.resources.copy()
        if current_lvl >= max_cap: return 0
        for i in range(max_cap - current_lvl):
            cost = cost_func(item_id, 1, current_lvl + i)
            if not cost or not self.can_afford_with_simulated(sim_res, cost): break
            for r,a in cost.items(): sim_res[r] -= a
            affordable_lvls += 1
        return affordable_lvls
    
    def can_afford_with_simulated(self, sim_res, costs): # Helper for calculate_max_affordable_levels
        return all(sim_res.get(r,0) >= a for r,a in costs.items())
        
    def get_race_upgrade_benefits(self, race_id):
        if race_id not in self.races or not self.races[race_id]["unlocked"]: return None
        info, data = RACES[race_id], self.races[race_id]
        curr_lvl, next_lvl = data["level"], data["level"]+1; curr_b, next_b = {}, {}
        if "resource_bonuses" in info:
            for r, cfg in info["resource_bonuses"].items():
                base=cfg.get("base",1.0) if isinstance(cfg,dict) else cfg; growth=cfg.get("growth",0.1) if isinstance(cfg,dict) else 0.1
                curr_b[f"{r.capitalize()} Bonus"]=f"{base+(curr_lvl-1)*growth:.2f}x"; next_b[f"{r.capitalize()} Bonus"]=f"{base+(next_lvl-1)*growth:.2f}x"
        if "special_abilities" in info:
            for ab_id, ab_info in info["special_abilities"].items():
                req_lvl=ab_info.get("unlock_requirements",{}).get("race_level",0); name=ab_info.get("name",ab_id)
                unlocked=data["abilities"].get(ab_id,{}).get("unlocked")
                curr_b[name]="Unlocked" if unlocked else ("Unlockable" if curr_lvl>=req_lvl else f"Lv{req_lvl}")
                next_b[name]="Unlocked" if unlocked else ("Unlockable" if next_lvl>=req_lvl else f"Lv{req_lvl}")
        return {"current_level":curr_lvl,"next_level":next_lvl,"current_benefits":curr_b,"next_level_benefits":next_b,"upgrade_cost":self.get_race_upgrade_cost(race_id,1)}

    def get_building_upgrade_benefits(self, building_id):
        if building_id not in self.buildings or not self.buildings[building_id]["unlocked"]: return None
        info,data=BUILDINGS[building_id],self.buildings[building_id]
        curr_lvl,next_lvl,max_lvl=data["level"],data["level"]+1,info["max_level"]; curr_b,next_b={},{}
        prod_s=info.get("level_scaling",1.0); mult_s=info.get("level_scaling_multiplier", prod_s) # Use prod_s if mult_s not defined
        if "resource_production" in info:
            for r,a in info["resource_production"].items():
                curr_b[f"{r.capitalize()} Prod."]=f"+{a*(prod_s**(curr_lvl-1))*data['count']:.1f}/s"
                if next_lvl<=max_lvl: next_b[f"{r.capitalize()} Prod."]=f"+{a*(prod_s**(next_lvl-1))*data['count']:.1f}/s"
                else: next_b[f"{r.capitalize()} Prod."]="Max"
        if "global_multipliers" in info:
            for t,m in info["global_multipliers"].items():
                name=t.capitalize() if t!="all" else "All Res."
                curr_b[f"{name} Mult."]=f"x{m*(mult_s**(curr_lvl-1)):.2f}"
                if next_lvl<=max_lvl: next_b[f"{name} Mult."]=f"x{m*(mult_s**(next_lvl-1)):.2f}"
                else: next_b[f"{name} Mult."]="Max"
        if not curr_b: curr_b["Effect"]="Special"
        if not next_b and next_lvl<=max_lvl: next_b["Effect"]="Special"
        return {"current_level":curr_lvl,"next_level":next_lvl,"max_level":max_lvl,"current_benefits":curr_b,"next_level_benefits":next_b,
                "upgrade_cost":self.get_building_upgrade_cost(building_id,1) if curr_lvl<max_lvl else {}}

    def get_research_upgrade_benefits(self, research_id):
        if research_id not in self.research or not self.research[research_id]["unlocked"]: return None
        info,data=RESEARCH[research_id],self.research[research_id]
        curr_lvl,next_lvl,max_lvl=data["level"],data["level"]+1,info["max_level"]; curr_e,next_e={},{}
        effects,eff_s=info.get("effect",{}),info.get("effect_scaling",1.0)
        for type,val in effects.items():
            if type=="resource_multiplier":
                for r,b_m in val.items():
                    c_eff=1+(b_m-1)*curr_lvl*eff_s;n_eff=1+(b_m-1)*next_lvl*eff_s
                    curr_e[f"{r.capitalize()} Mult."]=f"x{c_eff:.2f}"
                    if next_lvl<=max_lvl: next_e[f"{r.capitalize()} Mult."]=f"x{n_eff:.2f}"
                    else: next_e[f"{r.capitalize()} Mult."]="Max"
            elif type=="global_multiplier":
                c_eff=1+(val-1)*curr_lvl*eff_s;n_eff=1+(val-1)*next_lvl*eff_s
                curr_e["Global Prod."]=f"x{c_eff:.2f}"
                if next_lvl<=max_lvl: next_e["Global Prod."]=f"x{n_eff:.2f}"
                else: next_e["Global Prod."]="Max"
        desc=info.get("description","Special"); shrt_desc=(desc[:27]+"...") if len(desc)>30 else desc
        if not curr_e: curr_e["Effect"]=shrt_desc
        if not next_e and next_lvl<=max_lvl: next_e["Effect"]=shrt_desc
        return {"current_level":curr_lvl,"next_level":next_lvl,"max_level":max_lvl,"current_effects":curr_e,"next_level_effects":next_e,"research_cost":self.get_research_cost(research_id,1) if curr_lvl<max_lvl else {}}
        
    def get_production_multiplier(self, resource):
        return self.calculate_global_multiplier(resource)
    
    def get_race_skill_multiplier(self, race_id, resource):
        mult = 1.0
        for m in ACHIEVEMENTS.get("race_skill_milestones",[]):
            if self.achievements.get("race_skill_milestones",{}).get(m["id"]) and m["requirement"].get("race_skill")==race_id:
                if f"{race_id}_{resource}_bonus" in m["reward"]: mult *= m["reward"][f"{race_id}_{resource}_bonus"]
                if f"{race_id}_efficiency" in m["reward"]: mult *= m["reward"][f"{race_id}_efficiency"]
        return mult

    def get_race_bonus_multiplier(self):
        mult = 1.0
        if "racial_harmony" in self.research and self.research["racial_harmony"]["unlocked"] and self.research["racial_harmony"]["level"]>0:
            info=RESEARCH["racial_harmony"]
            mult *= (1.0+((info["effect"]["race_bonus_multiplier"]-1.0)*self.research["racial_harmony"]["level"]*info.get("effect_scaling",1.0)))
        for cat_key in ["race_milestones","race_skill_milestones"]:
            for m in ACHIEVEMENTS.get(cat_key,[]):
                if self.achievements.get(cat_key,{}).get(m["id"]) and "all_race_efficiency" in m["reward"]:
                    mult *= m["reward"]["all_race_efficiency"]
        return mult

    def get_research_multiplier(self, resource):
        mult = 1.0
        for id, data_v in self.research.items():
            if data_v["unlocked"] and data_v["level"]>0:
                info=RESEARCH[id]
                if "effect" in info:
                    eff,sc,lvl=info["effect"],info.get("effect_scaling",1.0),data_v["level"]
                    if "resource_multiplier" in eff and resource in eff["resource_multiplier"]:
                        mult *= (1.0+((eff["resource_multiplier"][resource]-1.0)*lvl*sc))
                    if "global_multiplier" in eff:
                        mult *= (1.0+((eff["global_multiplier"]-1.0)*lvl*sc))
        return mult

    def get_research_flat_bonus(self, resource):
        bonus = 0.0
        if "reality_manipulation" in self.research and self.research["reality_manipulation"]["unlocked"]:
            lvl=self.research["reality_manipulation"]["level"]
            if lvl>0: info=RESEARCH["reality_manipulation"]; bonus+=info["effect"]["idle_resource_generation"]*(info.get("effect_scaling",1.0)**(lvl-1))
        return bonus

    def add_notification(self, message, details=None, notification_type="info"):
        self.notifications.append({"text":message,"message":message,"time":pygame.time.get_ticks(),"type":notification_type,"details":details or message,"id":len(self.notifications)+1})
        if len(self.notifications)>20: self.notifications=self.notifications[-20:]
    
    def get_notifications(self,clear=False): n_copy=self.notifications.copy(); (self.notifications:=[] if clear else None); return n_copy # type: ignore
    
    def save_game(self, filename="save.json", compressed=True):
        data = {k:getattr(self,k) for k in ["resources","races","buildings","research","prestige_upgrades","achievements","player_level","total_earnings","prestige_count","prestige_points","total_prestige_points","permanent_multipliers","total_play_time","time_warp_active","time_warp_end_time","time_warp_cooldown_end"]}
        data.update({"save_time":time.time(),"version":"1.0.0"})
        try:
            d_name=os.path.dirname(filename); (os.makedirs(d_name) if d_name and not os.path.exists(d_name) else None)
            comp=compressed or filename.endswith(".zsave")
            if comp:
                f_name=filename.replace(".json",".zsave") if not filename.endswith(".zsave") else filename
                with open(f_name,'wb') as f: f.write(zlib.compress(json.dumps(data).encode('utf-8'),level=9))
            else:
                with open(filename,'w') as f: json.dump(data,f)
            self.last_save_time = time.time(); return True
        except Exception as e: print(f"Error saving game: {e}"); return False
    
    def export_save_string(self):
        try:
            data = {k:getattr(self,k) for k in ["resources","races","buildings","research","prestige_upgrades","achievements","player_level","total_earnings","prestige_count","prestige_points","total_prestige_points","permanent_multipliers","total_play_time","time_warp_active","time_warp_end_time","time_warp_cooldown_end"]}
            data.update({"save_time":time.time(),"version":"1.0.0"})
            return base64.b64encode(zlib.compress(json.dumps(data).encode('utf-8'),level=9)).decode('utf-8')
        except Exception as e: print(f"Error exporting save string: {e}"); return None
    
    def import_save_string(self, save_str):
        try:
            self._apply_save_data(json.loads(zlib.decompress(base64.b64decode(save_str)).decode('utf-8')))
            self.add_notification("Save imported successfully!",notification_type="save"); return True
        except Exception as e: print(f"Error importing save string: {e}"); self.add_notification("Failed to import save. Invalid save string.",notification_type="error"); return False
    
    def load_game(self, filename="save.json"):
        try:
            if not os.path.exists(filename): filename = filename.replace(".json",".zsave"); (False if not os.path.exists(filename) else None)
            with open(filename,'rb' if filename.endswith(".zsave") else 'r') as f: data=json.loads(zlib.decompress(f.read()).decode('utf-8') if filename.endswith(".zsave") else json.load(f))
            self._apply_save_data(data); return True
        except Exception as e: print(f"Error loading game: {e}"); return False
    
    def _apply_save_data(self, data):
        for k in ["resources","races","buildings","research","prestige_upgrades","player_level","total_earnings","prestige_count","prestige_points","total_prestige_points","permanent_multipliers","total_play_time","time_warp_active","time_warp_end_time","time_warp_cooldown_end"]:
            setattr(self,k,data.get(k,getattr(self,k)))
        for r_id,r_data in self.races.items():
            if "skills" not in r_data: r_data["skills"]={res_t:0 for res_t in RESOURCE_TYPES}
        
        def_ach_struct={c_k:{ach["id"]:False for ach in ach_l} for c_k,ach_l in ACHIEVEMENTS.items()}
        loaded_ach=data.get("achievements",{}); self.achievements=def_ach_struct.copy()
        for cat,mstones in loaded_ach.items():
            if cat in self.achievements:
                for m_id,m_stat in mstones.items():
                    if m_id in self.achievements[cat]: self.achievements[cat][m_id]=m_stat
        
        off_time=time.time()-data.get("save_time",time.time())
        if off_time>0:
            off_rate=OFFLINE_PROGRESS_RATE
            if "automatic_production" in self.prestige_upgrades and self.prestige_upgrades["automatic_production"]["level"]>0:
                lvl,info=self.prestige_upgrades["automatic_production"]["level"],PRESTIGE_UPGRADES["automatic_production"]
                off_rate=info["effect"]["offline_progress"]*lvl
            if off_rate>0:
                self.generate_resources(off_time*off_rate)
                t_str=f"{int(off_time)}s"; (f"{int(off_time/3600)}h {int((off_time%3600)/60)}m" if off_time>=3600 else (f"{int(off_time/60)}m {int(off_time%60)}s" if off_time>=60 else t_str))
                self.add_notification(f"Welcome back! Offline: {t_str} ({int(off_rate*100)}% rate).",notification_type="info")

    def calculate_max_affordable(self, cost):
        if not cost: return 0
        max_c = float('inf')
        for r,a in cost.items():
            if a<=0: continue
            max_c = min(max_c, self.resources.get(r,0)//a)
        return int(max_c) if max_c!=float('inf') else 0
