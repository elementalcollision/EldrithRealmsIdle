"""Headless greedy balance probe for Eldrith Realms Idle (E11 measurement).

Usage: python tools/balance_sim.py . [hours] [label]   (from the repo root; or pass
another checkout's path to compare versions)

Policy (a simple greedy): every DECISION seconds, repeatedly buy the affordable
action with the best gain/cost ratio, where gain is the rise in total effective
production summed over all seven resources and cost is the summed cost. No
prestige. Works on both the original API (spend + apply primitives) and the
patched API (buy_* methods).
"""
import copy
import math
import sys
import time

repo = sys.argv[1]
hours = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
label = sys.argv[3] if len(sys.argv) > 3 else repo
sys.path.insert(0, repo)

from game.game_state import GameState  # noqa: E402
from game.constants import RACES, BUILDINGS, RESEARCH, RESOURCE_TYPES  # noqa: E402

RES = [r for r in RESOURCE_TYPES if r != "prestige_points"]
DT = 5.0
DECISION = 10.0
MAX_BUYS_PER_DECISION = 25
PATCHED = hasattr(GameState, "buy_race")


def total_rate(gs):
    return sum(gs.calculate_resource_generation_rate(r) * gs.calculate_global_multiplier(r) for r in RES)


def candidates(gs):
    out = []
    for rid in RACES:
        d = gs.races[rid]
        if not d["unlocked"]:
            continue
        out.append(("race", rid))
        if d["count"] > 0:
            out.append(("race_up", rid))
    for bid, info in BUILDINGS.items():
        d = gs.buildings[bid]
        if not d["unlocked"]:
            continue
        if d["count"] < info.get("max_count", math.inf):
            out.append(("bld", bid))
        if d["count"] > 0 and d["level"] < info["max_level"]:
            out.append(("bld_up", bid))
    for rid, info in RESEARCH.items():
        d = gs.research[rid]
        if d["unlocked"] and d["level"] < info["max_level"]:
            out.append(("res", rid))
    return out


def cost_of(gs, act):
    kind, key = act
    return {
        "race": lambda: gs.get_race_purchase_cost(key, 1),
        "race_up": lambda: gs.get_race_upgrade_cost(key, 1),
        "bld": lambda: gs.get_building_purchase_cost(key, 1),
        "bld_up": lambda: gs.get_building_upgrade_cost(key, 1),
        "res": lambda: gs.get_research_cost(key, 1),
    }[kind]()


def apply(gs, act):
    kind, key = act
    if PATCHED:
        return {
            "race": gs.buy_race, "race_up": gs.buy_race_upgrade, "bld": gs.buy_building,
            "bld_up": gs.buy_building_upgrade, "res": gs.buy_research,
        }[kind](key, 1)
    cost = cost_of(gs, act)
    if not gs.can_afford(cost):
        return False
    gs.spend_resources(cost)
    return {
        "race": lambda: gs.add_race(key, 1), "race_up": lambda: gs.upgrade_race(key, 1),
        "bld": lambda: gs.add_building(key, 1), "bld_up": lambda: gs.upgrade_building(key, 1),
        "res": lambda: gs.research_technology(key),
    }[kind]()


def decide(gs):
    bought = 0
    while bought < MAX_BUYS_PER_DECISION:
        base = total_rate(gs)
        best, best_score = None, 0.0
        for act in candidates(gs):
            cost = cost_of(gs, act)
            if not cost or not gs.can_afford(cost):
                continue
            trial = copy.deepcopy(gs)
            if not apply(trial, act):
                continue
            gain = total_rate(trial) - base
            score = gain / max(sum(cost.values()), 1e-9)
            if score > best_score:
                best, best_score = act, score
        if best is None:
            return
        apply(gs, best)
        bought += 1


def main():
    gs = GameState()
    t, next_decision, wall0 = 0.0, 0.0, time.time()
    checkpoints = {600, 1800, 3600, 7200, 14400, 86400}
    print(f"== {label} (patched API: {PATCHED}) ==")
    while t < hours * 3600:
        if t >= next_decision:
            decide(gs)
            next_decision += DECISION
        gs.update(DT)
        t += DT
        if int(t) in checkpoints:
            print(f"t={int(t)/60:>6.0f} min  gold={gs.resources['gold']:.3g}  earnings={gs.total_earnings:.3g}  "
                  f"level={gs.player_level:.3g}  AK={gs.resources['ancient_knowledge']:.3g}  "
                  f"crystal={gs.resources['crystal']:.3g}  races={sum(r['count'] for r in gs.races.values())}  "
                  f"research_lv={sum(r['level'] for r in gs.research.values())}  "
                  f"prestige_pts_avail={gs.calculate_prestige_points()}")
    print(f"(sim wall time {time.time()-wall0:.1f}s)")


main()
