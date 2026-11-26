"""Headless greedy balance probe for Eldrith Realms Idle.

Usage (from the repo root, or pass another checkout's path to compare versions):

    .venv/bin/python tools/balance_sim.py [REPO] [--hours H] [--label TEXT]
        [--set NAME=VALUE ...] [--decision SECONDS] [--prestige] [--json PATH]
        [--check-clone]

--set overrides a pacing constant (int, else float) on game.constants, and on
game.game_state too when that module holds its own name for it; an unknown name
is an error. --check-clone runs 20 game-minutes twice, once with the light
candidate clone and once with copy.deepcopy, and asserts identical final states.

Policy (a simple greedy player, 5 s simulation steps):
  * Every --decision seconds (default 10), repeatedly buy the affordable action
    (race, race upgrade, building, building upgrade, research) with the best
    gain/cost ratio, where gain is the rise in total effective production
    (generation rate x global multiplier, summed over the seven non-prestige
    resources) and cost is the summed cost. Candidates are evaluated on a light
    clone of the state, not a deep copy.
  * After each round, buy every ability whose status is "available" and that is
    affordable, in data order.
  * With --prestige, after a round prestige when at least one point is
    available and the pending gain is at least the total points earned so far
    (so the first prestige is as soon as one point exists, later ones when the
    gain at least doubles the total). Then repeatedly buy the cheapest
    affordable non-maxed prestige upgrade (data order on ties). Time Warp is
    activated whenever it can be.

Metrics: lifetime earnings (banked at each prestige plus the current run's);
first game time of player level 10/18/25/35/50, each prestige, the first
ability, and any race at level 50/100. Checkpoint lines are printed at 10 min,
30 min, 1 h, 2 h, 4 h, 8 h, 12 h and 24 h (those within --hours).
"""
import argparse
import copy
import importlib
import json
import math
import sys
import time

DT = 5.0
MAX_BUYS_PER_DECISION = 25
CHECKPOINTS = [600, 1800, 3600, 7200, 14400, 28800, 43200, 86400]
LEVEL_MARKS = [10, 18, 25, 35, 50]
RACE_MARKS = [50, 100]


def parse_value(text):
    try:
        return int(text)
    except ValueError:
        return float(text)


def light_clone(gs):
    """Copy of gs with fresh copies of every container a purchase mutates."""
    c = copy.copy(gs)
    c.resources = dict(gs.resources)
    c.races = {k: {**v, "skills": dict(v["skills"]),
                   "abilities": {a: dict(s) for a, s in v.get("abilities", {}).items()}}
               for k, v in gs.races.items()}
    c.buildings = {k: dict(v) for k, v in gs.buildings.items()}
    c.research = {k: dict(v) for k, v in gs.research.items()}
    c.prestige_upgrades = {k: dict(v) for k, v in gs.prestige_upgrades.items()}
    c.permanent_multipliers = dict(gs.permanent_multipliers)
    c.achievements = {k: dict(v) for k, v in gs.achievements.items()}
    c.notifications = []
    return c


class Sim:
    def __init__(self, env, decision=10.0, prestige=False, clone="light"):
        self.env = env
        self.decision = decision
        self.prestige = prestige
        self.clone = light_clone if clone == "light" else copy.deepcopy
        self.res = [r for r in env.RESOURCE_TYPES if r != "prestige_points"]
        self.gs = env.GameState()
        self.banked = 0.0
        self.prestiges = []          # game times of each prestige
        self.level_marks = {}
        self.race_marks = {}
        self.first_ability = None
        self.t = 0.0
        names = ("_active_effects", "get_race_reward_multiplier", "get_race_ability_multiplier",
                 "get_research_effect_bonus", "get_building_efficiency")
        self._orig = {n: getattr(env.logic, n) for n in names}
        self._pure = {}

    # --- evaluation ---
    def total_rate(self, gs, memo=True):
        """Total effective production.

        The state is not mutated here, so the list of switched-on effects (the
        game rebuilds it from every unlocked achievement on each query) is
        built once per evaluation. Queries that depend only on that list are
        also cached across evaluations, keyed by the identity of the effect
        dicts it holds (constants, so the key is stable). Disable with
        memo=False to get the plain game calls; --check-clone compares both.
        """
        if not memo:
            return self._total_rate(gs)
        logic = self.env.logic
        eff_cache, sig = {}, []

        def active(g):
            if id(g) not in eff_cache:
                eff_cache[id(g)] = list(self._orig["_active_effects"](g))
                sig.append(tuple((r, id(e)) for r, e in eff_cache[id(g)]))
            return eff_cache[id(g)]

        def pure(name):
            fn = self._orig[name]

            def wrapper(g, *args):
                active(g)
                key = (name, sig[-1], args)
                if key not in self._pure:
                    self._pure[key] = fn(g, *args)
                return self._pure[key]
            return wrapper

        bonus_cache, orig_bonus = {}, self.env.GameState.get_race_bonus_multiplier

        def race_bonus(g):
            if id(g) not in bonus_cache:
                bonus_cache[id(g)] = orig_bonus(g)
            return bonus_cache[id(g)]

        self.env.GameState.get_race_bonus_multiplier = race_bonus
        logic._active_effects = active
        for name in ("get_race_reward_multiplier", "get_race_ability_multiplier",
                     "get_research_effect_bonus", "get_building_efficiency"):
            setattr(logic, name, pure(name))
        try:
            return self._total_rate(gs)
        finally:
            self.env.GameState.get_race_bonus_multiplier = orig_bonus
            for name, fn in self._orig.items():
                setattr(logic, name, fn)

    def _total_rate(self, gs):
        return sum(gs.calculate_resource_generation_rate(r) * gs.calculate_global_multiplier(r)
                   for r in self.res)

    def candidates(self, gs):
        env, out = self.env, []
        for rid in env.RACES:
            d = gs.races[rid]
            if not d["unlocked"]:
                continue
            out.append(("race", rid))
            if d["count"] > 0:
                out.append(("race_up", rid))
        for bid, info in env.BUILDINGS.items():
            d = gs.buildings[bid]
            if not d["unlocked"]:
                continue
            if d["count"] < info.get("max_count", math.inf):
                out.append(("bld", bid))
            if d["count"] > 0 and d["level"] < info["max_level"]:
                out.append(("bld_up", bid))
        for rid, info in env.RESEARCH.items():
            d = gs.research[rid]
            if d["unlocked"] and d["level"] < info["max_level"]:
                out.append(("res", rid))
        return out

    @staticmethod
    def cost_of(gs, act):
        kind, key = act
        return {
            "race": gs.get_race_purchase_cost, "race_up": gs.get_race_upgrade_cost,
            "bld": gs.get_building_purchase_cost, "bld_up": gs.get_building_upgrade_cost,
            "res": gs.get_research_cost,
        }[kind](key, 1)

    @staticmethod
    def apply(gs, act):
        kind, key = act
        return {
            "race": gs.buy_race, "race_up": gs.buy_race_upgrade, "bld": gs.buy_building,
            "bld_up": gs.buy_building_upgrade, "res": gs.buy_research,
        }[kind](key, 1)

    def decide(self):
        gs = self.gs
        for _ in range(MAX_BUYS_PER_DECISION):
            base = self.total_rate(gs)
            best, best_score = None, 0.0
            for act in self.candidates(gs):
                cost = self.cost_of(gs, act)
                if not cost or not gs.can_afford(cost):
                    continue
                trial = self.clone(gs)
                if not self.apply(trial, act):
                    continue
                score = (self.total_rate(trial) - base) / max(sum(cost.values()), 1e-9)
                if score > best_score:
                    best, best_score = act, score
            if best is None:
                break
            self.apply(gs, best)

    # --- policies ---
    def buy_abilities(self):
        gs = self.gs
        for rid, info in self.env.RACES.items():
            for aid in (info.get("special_abilities") or {}):
                if self.env.ability_status(gs, rid, aid) != "available":
                    continue
                if not gs.can_afford(self.env.ability_cost(rid, aid)):
                    continue
                if gs.buy_race_ability(rid, aid) and self.first_ability is None:
                    self.first_ability = self.t

    def maybe_prestige(self):
        gs = self.gs
        pending = gs.calculate_prestige_points()
        if pending < 1 or pending < gs.total_prestige_points:
            return
        earned = gs.total_earnings
        if not gs.perform_prestige():
            return
        self.banked += earned
        self.prestiges.append(self.t)
        while True:
            options = []
            for uid in self.env.PRESTIGE_UPGRADES:
                if gs.prestige_upgrades[uid]["level"] >= self.env.PRESTIGE_UPGRADES[uid]["max_level"]:
                    continue
                cost = gs.get_prestige_upgrade_cost(uid, 1)
                if cost and gs.can_afford(cost):
                    options.append((sum(cost.values()), uid))
            if not options:
                break
            _, uid = min(options, key=lambda o: o[0])  # min() keeps the first on ties
            if not gs.buy_prestige_upgrade(uid):
                break

    # --- metrics ---
    def record(self):
        gs = self.gs
        for m in LEVEL_MARKS:
            if gs.player_level >= m:
                self.level_marks.setdefault(m, self.t)
        top = max(d["level"] for d in gs.races.values())
        for m in RACE_MARKS:
            if top >= m:
                self.race_marks.setdefault(m, self.t)

    def snapshot(self, wall):
        gs = self.gs
        return {
            "t_min": self.t / 60,
            "run_earnings": gs.total_earnings,
            "lifetime_earnings": self.banked + gs.total_earnings,
            "player_level": gs.player_level,
            "prestige_count": gs.prestige_count,
            "prestige_points": gs.prestige_points,
            "max_race_level": max(d["level"] for d in gs.races.values()),
            "abilities": sum(1 for d in gs.races.values() for a in d.get("abilities", {}).values()
                             if a.get("unlocked")),
            "research_levels": sum(d["level"] for d in gs.research.values()),
            "achievements": sum(1 for cat in gs.achievements.values() for v in cat.values() if v),
            "wall_s": wall,
        }

    @staticmethod
    def line(s):
        return (f"t={s['t_min']:>5.0f}m  run={s['run_earnings']:.3g}  life={s['lifetime_earnings']:.3g}  "
                f"lvl={s['player_level']}  prestiges={s['prestige_count']}  pp={s['prestige_points']:.3g}  "
                f"maxrace={s['max_race_level']}  abil={s['abilities']}  research={s['research_levels']}  "
                f"ach={s['achievements']}  wall={s['wall_s']:.1f}s")

    def milestones(self):
        out = {f"level_{m}": self.level_marks.get(m) for m in LEVEL_MARKS}
        out["prestige_count"] = len(self.prestiges)
        out["prestige_times"] = list(self.prestiges)
        out["first_ability"] = self.first_ability
        out.update({f"race_level_{m}": self.race_marks.get(m) for m in RACE_MARKS})
        return out

    def run(self, hours, quiet=True):
        gs, end = self.gs, hours * 3600
        wall0 = time.time()
        next_decision, pending_cp, rows = 0.0, [c for c in CHECKPOINTS if c <= end], []
        while self.t < end:
            if self.t >= next_decision:
                self.decide()
                self.buy_abilities()
                if self.prestige:
                    self.maybe_prestige()
                    gs.activate_time_warp()
                gs.notifications.clear()
                next_decision += self.decision
            gs.update(DT)
            self.t += DT
            self.record()
            while pending_cp and self.t >= pending_cp[0]:
                pending_cp.pop(0)
                rows.append(self.snapshot(time.time() - wall0))
                if not quiet:
                    print(self.line(rows[-1]), flush=True)
        self.wall = time.time() - wall0
        return rows


def load_env(repo):
    sys.path.insert(0, repo)
    consts = importlib.import_module("game.constants")
    gsm = importlib.import_module("game.game_state")
    logic = importlib.import_module("game.logic.race_abilities")

    class Env:
        pass
    env = Env()
    env.constants, env.gsmod = consts, gsm
    env.GameState = gsm.GameState
    for n in ("RACES", "BUILDINGS", "RESEARCH", "RESOURCE_TYPES", "PRESTIGE_UPGRADES"):
        setattr(env, n, getattr(consts, n))
    env.logic = logic
    env.ability_status, env.ability_cost = logic.ability_status, logic.ability_cost
    return env


def apply_settings(env, settings):
    for item in settings:
        name, _, raw = item.partition("=")
        if not raw:
            sys.exit(f"--set expects NAME=VALUE, got {item!r}")
        if not hasattr(env.constants, name):
            sys.exit(f"game.constants has no attribute {name!r}")
        value = parse_value(raw)
        setattr(env.constants, name, value)
        if hasattr(env.gsmod, name):
            setattr(env.gsmod, name, value)


def state_dict(gs):
    d = {k: v for k, v in vars(gs).items() if k not in ("notifications", "last_save_time")}
    return d


def check_clone(env, args):
    runs = {}
    for mode in ("light", "deepcopy"):
        sim = Sim(env, args.decision, args.prestige, clone=mode)
        sim.gs.last_save_time = 0
        sim.run(20 / 60)
        runs[mode] = (sim, sim.wall)
    a, b = state_dict(runs["light"][0].gs), state_dict(runs["deepcopy"][0].gs)
    assert abs(runs["light"][0].total_rate(runs["light"][0].gs)
               - runs["light"][0].total_rate(runs["light"][0].gs, memo=False)) < 1e-9 * max(1.0, a["total_earnings"]), \
        "memoised total_rate disagrees with the plain one"
    assert a == b, "light clone diverged from deepcopy: " + ", ".join(k for k in a if a[k] != b[k])
    bought = sum(r["level"] for r in runs["light"][0].gs.research.values()) + sum(
        r["count"] for r in runs["light"][0].gs.races.values())
    print(f"check-clone OK over 20 game-minutes: final states identical "
          f"(light {runs['light'][1]:.1f}s, deepcopy {runs['deepcopy'][1]:.1f}s, "
          f"{bought} race units + research levels bought, earnings {runs['light'][0].gs.total_earnings:.4g})")


def main():
    ap = argparse.ArgumentParser(description="Greedy balance probe (see module docstring).")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--hours", type=float, default=2.0)
    ap.add_argument("--label", default=None)
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE", dest="settings")
    ap.add_argument("--decision", type=float, default=10.0)
    ap.add_argument("--prestige", action="store_true")
    ap.add_argument("--json", metavar="PATH", default=None)
    ap.add_argument("--check-clone", action="store_true")
    args = ap.parse_args()

    env = load_env(args.repo)
    apply_settings(env, args.settings)
    if args.check_clone:
        check_clone(env, args)
        return

    label = args.label or args.repo
    print(f"== {label}  hours={args.hours}  prestige={args.prestige}  set={args.settings} ==")
    sim = Sim(env, args.decision, args.prestige)
    rows = sim.run(args.hours, quiet=False)
    ms = sim.milestones()
    print("milestones (game minutes):")
    for k, v in ms.items():
        if k == "prestige_times":
            print(f"  {k}: {[round(x / 60, 1) for x in v]}")
        elif k == "prestige_count":
            print(f"  {k}: {v}")
        else:
            print(f"  {k}: {'never' if v is None else round(v / 60, 1)}")
    print(f"(sim wall time {sim.wall:.1f}s)")
    if args.json:
        with open(args.json, "w") as f:
            json.dump({"label": label, "settings": args.settings, "checkpoints": rows,
                       "milestones": ms}, f, indent=2)


if __name__ == "__main__":
    main()
