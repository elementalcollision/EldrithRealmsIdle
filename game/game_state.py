import copy
import time
import json
import math
import os
import zlib
import base64

from game.constants import (RESOURCE_TYPES, RACES, BUILDINGS, RESEARCH,
                           PRESTIGE_UPGRADES, ACHIEVEMENTS, BASE_INCOME_RATE,
                           PRESTIGE_REQUIREMENT_BASE, PRESTIGE_SCALING, PRESTIGE_BONUS_BASE,
                           OFFLINE_PROGRESS_RATE, OFFLINE_PROGRESS_MAX_RATE, OFFLINE_PROGRESS_CAP,
                           TIME_WARP_DURATION, TIME_WARP_COOLDOWN)

from game import constants as C  # pacing knobs read at call time, so they can be overridden
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
                        "active": False,
                        "available_notified": False,
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
        
        # Time tracking. Time Warp duration and cooldown are countdowns in
        # seconds of game time (advanced by update() and by offline time on
        # load), never wall-clock timestamps, so moving the clock does nothing.
        self.last_save_time = time.time()
        self.total_play_time = 0
        self.time_warp_active = False
        self.time_warp_remaining = 0.0
        self.time_warp_cooldown_remaining = 0.0

        # Notifications
        self.notifications = []

        # Set by load_game / import_save_string when offline progress accrued;
        # the UI consumes and clears it on startup.
        self.pending_offline_summary = None
    
    # ---------- Prestige points ----------
    # One counter only (errata E1): the spendable balance lives in
    # resources["prestige_points"], and this attribute is a view onto it.
    # Before, spending deducted from the resource but not from a separate
    # counter, and every prestige restored the counter — refunding the spend.
    @property
    def prestige_points(self):
        return self.resources.get("prestige_points", 0)

    @prestige_points.setter
    def prestige_points(self, value):
        self.resources["prestige_points"] = value

    def update(self, elapsed_time):
        """Advance the game by ``elapsed_time`` seconds of real play."""
        elapsed_time = max(0.0, float(elapsed_time))
        effective_time = self._advance_time_warp(elapsed_time)
        self.total_play_time += elapsed_time
        self.generate_resources(effective_time)
        self.check_unlocks()
        achievement_logic.check_achievements(self)

    def _advance_time_warp(self, elapsed_time):
        """Count Time Warp timers down by ``elapsed_time`` and return the
        production time that interval is worth (the warped part runs at the
        warp multiplier)."""
        self.time_warp_cooldown_remaining = max(0.0, self.time_warp_cooldown_remaining - elapsed_time)
        if not self.time_warp_active:
            return elapsed_time
        warped = min(elapsed_time, max(0.0, self.time_warp_remaining))
        self.time_warp_remaining -= warped
        effective = warped * self.get_time_warp_multiplier() + (elapsed_time - warped)
        if self.time_warp_remaining <= 0:
            self.time_warp_active = False
            self.time_warp_remaining = 0.0
            self.add_notification("Time Warp has ended!", notification_type="info")
        return effective

    def generate_resources(self, elapsed_time):
        ability_logic.apply_special_resource_generation(self, elapsed_time)
        # Chance-based abilities pay their expected value every tick, so
        # production is deterministic (no RNG, no wall clock).
        doubling = ability_logic.get_production_doubling_multiplier(self)

        for resource in RESOURCE_TYPES:
            if resource == "prestige_points": continue

            generation_rate = self.calculate_resource_generation_rate(resource)
            amount_generated = generation_rate * elapsed_time
            global_multiplier = self.calculate_global_multiplier(resource)
            amount_generated *= global_multiplier
            time_modifier = ability_logic.get_time_based_modifier(self, resource)
            amount_generated *= time_modifier
            amount_generated *= doubling

            self.resources[resource] = self.resources.get(resource, 0) + amount_generated
            
            if resource == "gold": self.total_earnings += amount_generated
            achievement_logic.track_race_resource_generation(self, resource, amount_generated)
                
        ability_logic.generate_passive_prestige_points(self, elapsed_time)
    
    def calculate_resource_generation_rate(self, resource):
        base_rate = 0
        base_rate += ability_logic.get_passive_generation_rate(self, resource)
        
        race_bonus_mult = self.get_race_bonus_multiplier()
        for race_id in self.races:
            base_rate += self.get_race_contribution(race_id, resource, race_bonus_mult)
        base_rate += ability_logic.get_ability_byproduct_rate(self, resource, race_bonus_mult)

        building_eff = ability_logic.get_building_efficiency(self)
        for b_id, b_data in self.buildings.items():
            if b_data["unlocked"] and b_data["count"] > 0:
                b_info = BUILDINGS[b_id]
                if "resource_production" in b_info and resource in b_info["resource_production"]:
                    lvl_scale = b_info.get("level_scaling", 1.0)
                    base_rate += (b_info["resource_production"][resource] * b_data["count"]
                                  * (lvl_scale ** (b_data["level"] - 1)) * building_eff)

        base_rate += self.get_research_flat_bonus(resource)
        return base_rate

    def get_race_contribution(self, race_id, resource, race_bonus_mult=None):
        """Base production of ``resource`` per second from one race, before
        global multipliers.

        A race produces only the resources listed in its ``resource_bonuses``
        (errata E10). Before, every race produced every resource at the base
        rate, which made research currency and crystal free from the start.
        """
        race_data = self.races.get(race_id)
        if not race_data or not race_data["unlocked"] or race_data["count"] <= 0:
            return 0.0
        bonuses = RACES[race_id].get("resource_bonuses", {})
        if resource not in bonuses:
            return 0.0
        if race_bonus_mult is None:
            race_bonus_mult = self.get_race_bonus_multiplier()
        bonus_cfg = bonuses[resource]
        bonus_val = bonus_cfg.get("base", 1.0) if isinstance(bonus_cfg, dict) else bonus_cfg
        contrib = BASE_INCOME_RATE * race_data["count"] * race_data["level"] * bonus_val * race_bonus_mult
        contrib *= ability_logic.get_race_specific_ability_bonus(self, race_id, resource)
        contrib *= self.get_race_skill_multiplier(race_id, resource)
        return contrib
    
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
            if count > self.building_room(building_id):
                return False  # would exceed max_count (errata E6)
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
    
    @staticmethod
    def earnings_for_level(level):
        """Total earnings (this run) needed to reach player ``level``."""
        return C.LEVEL_EARNINGS_BASE * max(0, level - 1) ** C.LEVEL_EARNINGS_EXPONENT

    @staticmethod
    def _level_for_earnings(total_earnings):
        ratio = min(max(0.0, total_earnings) / C.LEVEL_EARNINGS_BASE, 1e300)  # finite even for edited saves
        steps = ratio ** (1.0 / C.LEVEL_EARNINGS_EXPONENT)
        return 1 + int(steps + 1e-9)  # epsilon: exact thresholds must not round down

    def check_unlocks(self):
        new_level = self._level_for_earnings(self.total_earnings)
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

    # Cost functions use closed-form totals (arithmetic series for counts,
    # geometric series for levels), so buying N at once costs the same as N
    # single purchases and "buy max" can search large N cheaply (errata E9).
    # The *_override parameters let callers price from a hypothetical
    # starting count or level (errata E8: races and buildings lacked them).
    @staticmethod
    def _arith_units(count, start):
        """Sum of (1 + step*(start+i)) for i < count, returned as (n, n*start + n(n-1)/2)."""
        return count, count * start + count * (count - 1) / 2

    @staticmethod
    def _geom_sum(ratio, start, count):
        """Sum of ratio**(start+i) for i < count."""
        if ratio == 1.0:
            return float(count)
        return (ratio ** start) * (ratio ** count - 1.0) / (ratio - 1.0)

    def get_race_purchase_cost(self, race_id, count=1, current_count_override=None):
        if race_id not in RACES or count <= 0: return {}
        cur_c = current_count_override if current_count_override is not None else self.races[race_id]["count"]
        return {"gold": RACES[race_id]["base_cost"] * self._geom_sum(C.RACE_COST_GROWTH, cur_c, count)}

    def get_race_upgrade_cost(self, race_id, count=1, current_level_override=None):
        if race_id not in RACES or count <= 0: return {}
        cur_l = current_level_override if current_level_override is not None else self.races[race_id]["level"]
        return {"gold": RACES[race_id]["base_cost"] * C.RACE_UPGRADE_COST_MULT
                * self._geom_sum(C.RACE_UPGRADE_COST_GROWTH, cur_l - 1, count)}

    def _building_cost_reduction(self):
        # Errata E15: read from every building_cost_reduction reward, not a
        # hardcoded 0.95 for first_building.
        return ability_logic.get_building_cost_factor(self)

    def get_building_purchase_cost(self, building_id, count=1, current_count_override=None):
        if building_id not in BUILDINGS or count <= 0: return {}
        cur_c = current_count_override if current_count_override is not None else self.buildings[building_id]["count"]
        n, s = self._arith_units(count, cur_c)
        reduct = self._building_cost_reduction()
        return {r: a * (n + 0.2 * s) * reduct for r, a in BUILDINGS[building_id]["base_cost"].items()}

    def get_building_upgrade_cost(self, building_id, count=1, current_level_override=None):
        if building_id not in BUILDINGS or count <= 0: return {}
        cur_l = current_level_override if current_level_override is not None else self.buildings[building_id]["level"]
        reduct, up_mult = self._building_cost_reduction(), 2.0
        geo = self._geom_sum(2.0, cur_l - 1, count)
        return {r: a * geo * reduct * up_mult for r, a in BUILDINGS[building_id]["base_cost"].items()}

    def get_research_cost(self, research_id, count=1, current_level_override=None):
        if research_id not in RESEARCH: return {}
        info = RESEARCH[research_id]
        start_lvl = current_level_override if current_level_override is not None else self.research[research_id]["level"]
        actual_cnt = int(count) if count!=-1 else 1
        if actual_cnt <= 0: return {}
        geo = self._geom_sum(info["cost_scaling"], start_lvl, actual_cnt)
        factor = ability_logic.get_research_cost_factor(self)
        return {r: a * geo * factor for r, a in info["cost"].items()}

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

    # ---------- Purchases ----------
    # Every buy_* method checks all preconditions (unlocked, owned, level and
    # count caps, affordability) before spending, then charges and applies in
    # one step, so a refused purchase never costs anything (errata E7).
    # count=-1 means "as many as affordable" (errata E8, E9).
    def max_affordable_count(self, total_cost_fn, cap=math.inf):
        """Largest n <= cap whose total cost ``total_cost_fn(n)`` is affordable.

        Costs must rise with n. Uses exponential then binary search, so it is
        cheap even for very large n.
        """
        def affordable(n):
            try:
                cost = total_cost_fn(n)
            except OverflowError:
                return False
            return bool(cost) and all(math.isfinite(a) for a in cost.values()) and self.can_afford(cost)

        if cap < 1 or not affordable(1):
            return 0
        lo, hi = 1, 2
        while hi <= cap and hi < (1 << 62) and affordable(hi):
            lo, hi = hi, hi * 2
        hi = int(min(hi, cap + 1))  # first n known to be unaffordable or over the cap
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if affordable(mid):
                lo = mid
            else:
                hi = mid
        return lo

    def _resolve_count(self, count, cap, total_cost_fn):
        """Turn a requested count (-1 = max) into one that fits the cap and
        is affordable, or 0 if nothing can be bought."""
        if count == -1:
            return self.max_affordable_count(total_cost_fn, cap)
        count = int(min(int(count), cap))  # clamp to the cap before pricing
        if count < 1:
            return 0
        try:
            cost = total_cost_fn(count)
        except OverflowError:
            return 0
        return count if cost and self.can_afford(cost) else 0

    def _charge(self, cost, apply):
        """Spend ``cost`` and run ``apply``; refund if ``apply`` refuses."""
        if not self.spend_resources(cost):
            return False
        if apply():
            return True
        for r, a in cost.items():  # defensive: preconditions were checked
            self.resources[r] += a
        return False

    def building_room(self, building_id):
        """How many more of this building may be built (inf if uncapped)."""
        cap = BUILDINGS[building_id].get("max_count", math.inf)
        return max(0, cap - self.buildings[building_id]["count"])

    def buy_race(self, race_id, count=1):
        if race_id not in self.races or not self.races[race_id]["unlocked"]:
            return False
        n = self._resolve_count(count, math.inf, lambda k: self.get_race_purchase_cost(race_id, k))
        if n <= 0:
            return False
        return self._charge(self.get_race_purchase_cost(race_id, n), lambda: self.add_race(race_id, n))

    def buy_race_upgrade(self, race_id, count=1):
        data = self.races.get(race_id)
        if not data or not data["unlocked"] or data["count"] <= 0:
            return False
        room = RACES[race_id].get("max_level", math.inf) - data["level"]
        n = self._resolve_count(count, room, lambda k: self.get_race_upgrade_cost(race_id, k))
        if n <= 0:
            return False
        return self._charge(self.get_race_upgrade_cost(race_id, n), lambda: self.upgrade_race(race_id, n))

    def buy_building(self, building_id, count=1):
        if building_id not in self.buildings or not self.buildings[building_id]["unlocked"]:
            return False
        n = self._resolve_count(count, self.building_room(building_id),
                                lambda k: self.get_building_purchase_cost(building_id, k))
        if n <= 0:
            return False
        return self._charge(self.get_building_purchase_cost(building_id, n),
                            lambda: self.add_building(building_id, n))

    def buy_building_upgrade(self, building_id, count=1):
        data = self.buildings.get(building_id)
        if not data or not data["unlocked"] or data["count"] <= 0:
            return False
        room = BUILDINGS[building_id]["max_level"] - data["level"]
        n = self._resolve_count(count, room, lambda k: self.get_building_upgrade_cost(building_id, k))
        if n <= 0:
            return False
        return self._charge(self.get_building_upgrade_cost(building_id, n),
                            lambda: self.upgrade_building(building_id, n))

    def buy_research(self, research_id, count=1):
        data = self.research.get(research_id)
        if not data or not data["unlocked"]:
            return False
        room = RESEARCH[research_id]["max_level"] - data["level"]
        n = self._resolve_count(count, room, lambda k: self.get_research_cost(research_id, k))
        if n <= 0:
            return False

        def apply():
            for _ in range(n):
                if not self.research_technology(research_id):
                    return False
            return True
        return self._charge(self.get_research_cost(research_id, n), apply)

    def buy_prestige_upgrade(self, upgrade_id):
        data = self.prestige_upgrades.get(upgrade_id)
        if not data or data["level"] >= PRESTIGE_UPGRADES[upgrade_id]["max_level"]:
            return False
        cost = self.get_prestige_upgrade_cost(upgrade_id, 1)
        if not cost or not self.can_afford(cost):
            return False
        return self._charge(cost, lambda: self.purchase_prestige_upgrade(upgrade_id))

    def buy_race_ability(self, race_id, ability_id):
        return ability_logic.purchase_race_ability(self, race_id, ability_id)

    def toggle_race_ability(self, race_id, ability_id):
        return ability_logic.activate_race_ability(self, race_id, ability_id)
        
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
        eff_s *= ability_logic.get_research_effect_bonus(self)
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
        # Errata E15: {race}_{res}_bonus and {race}_efficiency now apply from
        # any achievement category, through the shared reward reader.
        return ability_logic.get_race_reward_multiplier(self, race_id, resource)

    def get_race_bonus_multiplier(self):
        mult = 1.0
        if "racial_harmony" in self.research and self.research["racial_harmony"]["unlocked"] and self.research["racial_harmony"]["level"]>0:
            info=RESEARCH["racial_harmony"]
            mult *= (1.0+((info["effect"]["race_bonus_multiplier"]-1.0)*self.research["racial_harmony"]["level"]*info.get("effect_scaling",1.0)
                          *ability_logic.get_research_effect_bonus(self)))
        for cat_key in ["race_milestones","race_skill_milestones"]:
            for m in ACHIEVEMENTS.get(cat_key,[]):
                if self.achievements.get(cat_key,{}).get(m["id"]) and "all_race_efficiency" in m["reward"]:
                    mult *= m["reward"]["all_race_efficiency"]
        return mult

    def get_research_multiplier(self, resource):
        mult = 1.0
        effect_bonus = ability_logic.get_research_effect_bonus(self)
        for id, data_v in self.research.items():
            if data_v["unlocked"] and data_v["level"]>0:
                info=RESEARCH[id]
                if "effect" in info:
                    eff,sc,lvl=info["effect"],info.get("effect_scaling",1.0)*effect_bonus,data_v["level"]
                    if "resource_multiplier" in eff and resource in eff["resource_multiplier"]:
                        mult *= (1.0+((eff["resource_multiplier"][resource]-1.0)*lvl*sc))
                    if "global_multiplier" in eff:
                        mult *= (1.0+((eff["global_multiplier"]-1.0)*lvl*sc))
        return mult

    def get_research_flat_bonus(self, resource):
        bonus = 0.0
        if "reality_manipulation" in self.research and self.research["reality_manipulation"]["unlocked"]:
            lvl=self.research["reality_manipulation"]["level"]
            if lvl>0:
                info=RESEARCH["reality_manipulation"]
                bonus+=(info["effect"]["idle_resource_generation"]*(info.get("effect_scaling",1.0)**(lvl-1))
                        *ability_logic.get_research_effect_bonus(self))
        return bonus

    # ---------- Prestige ----------
    def get_prestige_requirement(self):
        """Total-earnings threshold required to gain at least one prestige point."""
        return C.PRESTIGE_REQUIREMENT_BASE * (C.PRESTIGE_SCALING ** self.prestige_count)

    def calculate_prestige_points(self):
        """Prestige points the player would gain if they prestiged right now."""
        req = self.get_prestige_requirement()
        if self.total_earnings < req:
            return 0
        # Sqrt curve so doubling earnings ~= 1.4x points; classic idle pacing.
        base = int((self.total_earnings / req) ** 0.5)
        # Achievement bonuses
        # (errata E15: from any category, not only prestige_milestones)
        bonus_mult, bonus_flat = ability_logic.get_prestige_point_modifiers(self)
        return max(0, int(base * bonus_mult) + bonus_flat)

    def perform_prestige(self):
        """Reset progression in exchange for prestige points and permanent bonuses."""
        gained = self.calculate_prestige_points()
        if gained <= 0:
            return False

        # Compute retention from prestige upgrades before reset.
        kn_ret = 0.0
        if self.prestige_upgrades.get("eternal_knowledge", {}).get("level", 0) > 0:
            lvl = self.prestige_upgrades["eternal_knowledge"]["level"]
            kn_ret = PRESTIGE_UPGRADES["eternal_knowledge"]["effect"]["knowledge_retention"] * lvl
        res_ret = 0.0
        if self.prestige_upgrades.get("resource_memory", {}).get("level", 0) > 0:
            lvl = self.prestige_upgrades["resource_memory"]["level"]
            res_ret = PRESTIGE_UPGRADES["resource_memory"]["effect"]["resource_retention"] * lvl
        starting_gold = 100
        if self.prestige_upgrades.get("faster_start", {}).get("level", 0) > 0:
            lvl = self.prestige_upgrades["faster_start"]["level"]
            starting_gold += int(PRESTIGE_UPGRADES["faster_start"]["effect"]["starting_gold"] * lvl)

        retained_knowledge = self.resources.get("ancient_knowledge", 0) * kn_ret
        retained_basic = {
            r: self.resources.get(r, 0) * res_ret
            for r in ("wood", "stone", "food", "mana", "crystal")
        }

        # Award points and bump counter. The balance is the unspent points
        # plus the new ones; spent points stay spent (errata E1).
        balance = self.prestige_points + gained
        self.prestige_count += 1
        self.total_prestige_points += gained

        # Reset resources.
        self.resources = {r: 0 for r in RESOURCE_TYPES}
        self.resources["gold"] = starting_gold
        self.resources["ancient_knowledge"] = retained_knowledge
        for r, amt in retained_basic.items():
            self.resources[r] = amt
        self.prestige_points = balance

        # Reset progression-affected state.
        self.total_earnings = 0
        self.player_level = 1

        for race_id, race_data_const in RACES.items():
            self.races[race_id]["count"] = 0
            self.races[race_id]["level"] = 1
            self.races[race_id]["unlocked"] = race_data_const["unlock_level"] == 1 \
                and self.prestige_count >= race_data_const.get("requires_prestige", 0)
            self.races[race_id]["skills"] = {res: 0 for res in RESOURCE_TYPES}
            for ab in self.races[race_id].get("abilities", {}).values():
                ab["unlocked"] = False
                ab["active"] = False
                ab["available_notified"] = False

        for b_id, b_const in BUILDINGS.items():
            self.buildings[b_id]["count"] = 0
            self.buildings[b_id]["level"] = 1
            self.buildings[b_id]["unlocked"] = b_const["unlock_level"] <= 1 \
                and self.prestige_count >= b_const.get("requires_prestige", 0)

        for r_id, r_const in RESEARCH.items():
            self.research[r_id]["level"] = 0
            self.research[r_id]["unlocked"] = r_const["unlock_level"] <= 1 \
                and self.prestige_count >= r_const.get("requires_prestige", 0)

        self.time_warp_active = False
        self.time_warp_remaining = 0.0
        self.add_notification(
            f"Prestiged! Gained {gained} prestige points.",
            notification_type="achievement",
        )
        return True

    # ---------- Time Warp ----------
    def has_time_warp_unlocked(self):
        return self.prestige_upgrades.get("time_warp", {}).get("level", 0) > 0

    def get_time_warp_multiplier(self):
        lvl = self.prestige_upgrades.get("time_warp", {}).get("level", 0)
        if lvl <= 0:
            return 1.0
        info = PRESTIGE_UPGRADES["time_warp"]
        base = info["effect"]["time_warp_multiplier"]
        scaling = info.get("effect_scaling", 1.0)
        return base * (scaling ** (lvl - 1))

    def activate_time_warp(self):
        if not self.has_time_warp_unlocked():
            self.add_notification("Time Warp not yet unlocked (prestige upgrade).", notification_type="error")
            return False
        if self.time_warp_active:
            self.add_notification("Time Warp already active.", notification_type="error")
            return False
        if self.time_warp_cooldown_remaining > 0:
            remaining = int(math.ceil(self.time_warp_cooldown_remaining))
            self.add_notification(f"Time Warp cooling down ({remaining}s left).", notification_type="error")
            return False
        self.time_warp_active = True
        self.time_warp_remaining = float(TIME_WARP_DURATION)
        self.time_warp_cooldown_remaining = float(TIME_WARP_COOLDOWN)
        self.add_notification(
            f"Time Warp active! {self.get_time_warp_multiplier():.1f}x for {TIME_WARP_DURATION//60} min.",
            notification_type="achievement",
        )
        return True

    def add_notification(self, message, details=None, notification_type="info"):
        self.notifications.append({"text":message,"message":message,"time":int(time.time()*1000),"type":notification_type,"details":details or message,"id":len(self.notifications)+1})
        if len(self.notifications)>20: self.notifications=self.notifications[-20:]
    
    def get_notifications(self, clear=False):
        n_copy = self.notifications.copy()
        if clear:
            self.notifications = []
        return n_copy  # type: ignore
    
    # Fields written to a save. prestige_points duplicates
    # resources["prestige_points"] and is kept so older builds can read the file.
    SAVE_FIELDS = ["resources","races","buildings","research","prestige_upgrades","achievements",
                   "player_level","total_earnings","prestige_count","prestige_points","total_prestige_points",
                   "permanent_multipliers","total_play_time","time_warp_active","time_warp_remaining",
                   "time_warp_cooldown_remaining"]
    SAVE_VERSION = "1.2.0"  # 1.1.0: errata E1-E14 fixes; 1.2.0: E11 level curve

    def _save_data(self):
        data = {k: getattr(self, k) for k in self.SAVE_FIELDS}
        data.update({"save_time": time.time(), "version": self.SAVE_VERSION})
        return data

    def save_game(self, filename="save.json", compressed=True):
        data = self._save_data()
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
            return base64.b64encode(zlib.compress(json.dumps(self._save_data()).encode('utf-8'),level=9)).decode('utf-8')
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

    @staticmethod
    def _version_tuple(version):
        try:
            return tuple(int(p) for p in str(version).split("."))
        except ValueError:
            return (0,)

    def get_offline_rate(self):
        """Share of normal production earned while the game is closed.

        Automatic Production adds to the base rate (errata E14: it used to
        replace it, so level 1 cut the rate from 50% to 20%).
        """
        lvl = self.prestige_upgrades.get("automatic_production", {}).get("level", 0)
        bonus = PRESTIGE_UPGRADES["automatic_production"]["effect"]["offline_progress"] * lvl
        # Errata E15: offline_progress_bonus achievement rewards add to the rate.
        bonus += ability_logic.get_offline_progress_bonus(self)
        return min(OFFLINE_PROGRESS_MAX_RATE, OFFLINE_PROGRESS_RATE + bonus)

    def _apply_save_data(self, data):
        """Load ``data`` into this state, all or nothing: if anything in it
        is unusable the state is left exactly as it was and the error is
        re-raised (load_game / import_save_string then return False)."""
        snapshot = copy.deepcopy(self.__dict__)
        try:
            self._apply_save_data_unchecked(data)
        except Exception:
            self.__dict__.clear()
            self.__dict__.update(snapshot)
            raise

    def _apply_save_data_unchecked(self, data):
        if not isinstance(data, dict):
            raise ValueError("save data must be a JSON object")
        for k in ["resources","races","buildings","research","prestige_upgrades","player_level","total_earnings","prestige_count","total_prestige_points","permanent_multipliers","total_play_time","time_warp_active"]:
            setattr(self,k,data.get(k,getattr(self,k)))
        for k in ("resources", "races", "buildings", "research", "prestige_upgrades"):
            if not isinstance(getattr(self, k), dict):
                raise ValueError(f"save field {k!r} must be an object")

        # Prestige balance (errata E1): resources["prestige_points"] is the
        # spendable balance. Older saves also carry a separate counter that
        # spending never reduced; use it only if the balance is missing.
        if "prestige_points" not in self.resources:
            self.resources["prestige_points"] = data.get("prestige_points", 0)

        save_time = data.get("save_time")
        if not (isinstance(save_time, (int, float)) and math.isfinite(save_time)):
            save_time = None
        version = self._version_tuple(data.get("version", "0"))
        # Before 1.1.0, abilities were auto-bought and could never be switched on.
        pre_abilities = version < (1, 1, 0)
        # Before 1.2.0, player level was linear in earnings (E11), so the same
        # earnings meant a higher level and more unlocks.
        pre_level_curve = version < (1, 2, 0)

        # Time Warp countdowns (errata E3). Saves before 1.1.0 stored
        # wall-clock deadlines; convert them as of the save's own time.
        if "time_warp_remaining" in data or "time_warp_cooldown_remaining" in data:
            self.time_warp_remaining = data.get("time_warp_remaining", 0.0)
            self.time_warp_cooldown_remaining = data.get("time_warp_cooldown_remaining", 0.0)
        else:
            ref = save_time if save_time is not None else time.time()
            def _deadline(key):
                v = data.get(key, 0)
                return v - ref if isinstance(v, (int, float)) and math.isfinite(v) else 0.0
            self.time_warp_remaining = _deadline("time_warp_end_time")
            self.time_warp_cooldown_remaining = _deadline("time_warp_cooldown_end")

        # Missing, unknown or out-of-range entries (saves from older or newer
        # versions, or edited saves) are rebuilt by _sanitize_loaded_state.
        def_ach_struct={c_k:{ach["id"]:False for ach in ach_l} for c_k,ach_l in ACHIEVEMENTS.items()}
        loaded_ach=data.get("achievements",{}); self.achievements=def_ach_struct.copy()
        if not isinstance(loaded_ach, dict): loaded_ach = {}
        for cat,mstones in loaded_ach.items():
            if cat in self.achievements and isinstance(mstones, dict):
                for m_id,m_stat in mstones.items():
                    if m_id in self.achievements[cat]: self.achievements[cat][m_id]=m_stat
        
        self._sanitize_loaded_state(pre_abilities=pre_abilities, keep_unlocks=pre_level_curve)

        # Offline progress (errata E2): never negative (a save dated in the
        # future earns nothing) and capped at OFFLINE_PROGRESS_CAP, so moving
        # the clock or editing save_time gains at most one cap's worth.
        away = (time.time() - save_time) if save_time is not None else 0.0
        off_time = min(max(0.0, away), OFFLINE_PROGRESS_CAP)
        off_rate = self.get_offline_rate()
        if off_time > 0:
            # Time Warp timers keep running while away; the warp itself
            # doesn't boost offline gains.
            self._advance_time_warp(off_time)

        # Snapshot resources, apply offline gains, then diff so the UI can
        # show a "welcome back" summary. Skipped for very short gaps.
        if off_time > 5 and off_rate > 0:
            before = dict(self.resources)
            self.generate_resources(off_time * off_rate)
            gained = {
                r: self.resources[r] - before.get(r, 0)
                for r in self.resources
                if self.resources[r] - before.get(r, 0) > 0
            }
            self.pending_offline_summary = {
                "elapsed_seconds": off_time,
                "away_seconds": away,
                "capped": away > OFFLINE_PROGRESS_CAP,
                "rate": off_rate,
                "gained": gained,
            }

    def _unlock_requirement_met(self, const):
        return (const["unlock_level"] <= self.player_level
                and self.prestige_count >= const.get("requires_prestige", 0))

    def _sanitize_loaded_state(self, pre_abilities=False, keep_unlocks=False):
        """Reject impossible values from a save file or import string (errata E4).

        Numbers must be finite and non-negative; levels and counts are clamped
        to their caps; values that follow from others (player level, unlocks,
        permanent multipliers) are recomputed instead of trusted; unknown
        entries are dropped. Amounts that normal play could reach are still
        accepted: editing your own single-player save is not prevented.
        """
        def num(v, lo=0.0, hi=math.inf, default=0.0):
            try:
                v = float(v)
            except (TypeError, ValueError, OverflowError):
                return default
            if math.isnan(v):
                return default
            return min(max(v, lo), hi)

        def whole(v, lo=0, hi=math.inf, default=0):
            x = num(v, lo, hi, default)
            return int(x) if math.isfinite(x) else default

        def entry(table, key):
            v = table.get(key)
            return v if isinstance(v, dict) else {}

        def unlocked_flag(old, const):
            """Derived from level and prestige; a save from before the E11
            level curve also keeps what it had unlocked (prestige gates still
            apply), so owned content doesn't stop producing."""
            if self._unlock_requirement_met(const):
                return True
            return (keep_unlocks and old.get("unlocked") is True
                    and self.prestige_count >= const.get("requires_prestige", 0))

        def finite(v):
            x = num(v)
            return x if math.isfinite(x) else 0.0

        self.resources = {r: finite(self.resources.get(r, 0)) for r in RESOURCE_TYPES}
        self.total_earnings = finite(self.total_earnings)
        self.total_play_time = finite(self.total_play_time)
        self.prestige_count = whole(self.prestige_count)
        self.total_prestige_points = max(finite(self.total_prestige_points), self.prestige_points)
        self.player_level = self._level_for_earnings(self.total_earnings)

        races = {}
        for race_id, const in RACES.items():
            old = entry(self.races, race_id)
            data = {
                "count": whole(old.get("count", 0)),
                "level": whole(old.get("level", 1), 1, const.get("max_level", math.inf), 1),
                "unlocked": unlocked_flag(old, const),
                "skills": {res: finite(entry(old, "skills").get(res, 0)) for res in RESOURCE_TYPES},
                "abilities": {},
            }
            old_abilities = entry(old, "abilities")
            for ab_id, ab_const in const.get("special_abilities", {}).items():
                st = entry(old_abilities, ab_id)
                req = ab_const.get("unlock_requirements", {})
                unlocked = (bool(st.get("unlocked", False))
                            and data["level"] >= req.get("race_level", 0)
                            and self.prestige_count >= req.get("prestige_level", 0))
                # Abilities bought under the old auto-unlock (errata E5) could
                # never be switched on; switch them on now.
                active = unlocked and (pre_abilities or bool(st.get("active", False)))
                data["abilities"][ab_id] = {
                    "unlocked": unlocked,
                    "active": active,
                    "available_notified": bool(st.get("available_notified", unlocked)),
                }
            races[race_id] = data
        self.races = races

        buildings = {}
        for b_id, const in BUILDINGS.items():
            old = entry(self.buildings, b_id)
            buildings[b_id] = {
                "count": whole(old.get("count", 0), 0, const.get("max_count", math.inf)),
                "level": whole(old.get("level", 1), 1, const["max_level"], 1),
                "unlocked": unlocked_flag(old, const),
            }
        self.buildings = buildings

        research = {}
        for r_id, const in RESEARCH.items():
            old = entry(self.research, r_id)
            research[r_id] = {
                "level": whole(old.get("level", 0), 0, const["max_level"]),
                "unlocked": unlocked_flag(old, const),
            }
        self.research = research

        self.prestige_upgrades = {
            u_id: {"level": whole(entry(self.prestige_upgrades, u_id).get("level", 0), 0, const["max_level"])}
            for u_id, const in PRESTIGE_UPGRADES.items()
        }
        # Cosmic Insight is the only source of permanent multipliers.
        insight = PRESTIGE_UPGRADES["cosmic_insight"]["effect"]["permanent_multiplier"]
        self.permanent_multipliers = {"all": insight ** self.prestige_upgrades["cosmic_insight"]["level"]}

        for cat in self.achievements:
            for m_id, done in self.achievements[cat].items():
                self.achievements[cat][m_id] = done is True

        self.time_warp_remaining = num(self.time_warp_remaining, 0.0, TIME_WARP_DURATION)
        self.time_warp_cooldown_remaining = num(self.time_warp_cooldown_remaining, 0.0, TIME_WARP_COOLDOWN)
        self.time_warp_active = (bool(self.time_warp_active) and self.time_warp_remaining > 0
                                 and self.has_time_warp_unlocked())
        if not self.time_warp_active:
            self.time_warp_remaining = 0.0

    def calculate_max_affordable(self, cost):
        if not cost: return 0
        max_c = float('inf')
        for r,a in cost.items():
            if a<=0: continue
            max_c = min(max_c, self.resources.get(r,0)//a)
        return int(max_c) if max_c!=float('inf') else 0
