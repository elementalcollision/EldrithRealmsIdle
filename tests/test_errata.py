"""Regression tests for errata E1–E14: exploits, traps and bugs in the game core,
found by code reading and automated play-testing.

Each test is named after its errata ID. All but three fail on the code at
3143a42; those three (future-dated save, non-object import, every resource
has a source) guard behaviour the fixes must keep.
"""
import base64
import copy
import json
import time
import zlib

import pytest

from game.constants import (
    BUILDINGS, OFFLINE_PROGRESS_CAP, PRESTIGE_REQUIREMENT_BASE, RACES, RESEARCH,
    TIME_WARP_COOLDOWN, TIME_WARP_DURATION,
)
from game.game_state import GameState
from game.logic import race_abilities as ab


def _encode(data):
    return base64.b64encode(zlib.compress(json.dumps(data).encode())).decode()


def _decode(blob):
    return json.loads(zlib.decompress(base64.b64decode(blob)).decode())


def _prestige_ready(g, earnings=4 * PRESTIGE_REQUIREMENT_BASE):
    g.total_earnings = earnings
    return g


# ---------- E1: spent prestige points come back ----------
def test_e1_spent_prestige_points_stay_spent():
    g = _prestige_ready(GameState())
    assert g.perform_prestige()
    first = g.prestige_points
    assert g.buy_prestige_upgrade("eternal_knowledge")
    assert g.prestige_points == first - 1

    _prestige_ready(g, 4 * PRESTIGE_REQUIREMENT_BASE * 5)  # requirement scales ×5
    gained = g.calculate_prestige_points()
    assert g.perform_prestige()
    assert g.prestige_points == first - 1 + gained  # the spent point is not refunded
    assert g.total_prestige_points == first + gained


def test_e1_prestige_points_is_one_counter():
    g = GameState()
    g.prestige_points = 7
    assert g.resources["prestige_points"] == 7
    g.resources["prestige_points"] -= 2
    assert g.prestige_points == 5


def test_e1_old_save_uses_spendable_balance():
    """Saves from before the fix keep a counter spending never reduced."""
    g = GameState()
    data = _decode(g.export_save_string())
    data["prestige_points"] = 10            # stale counter
    data["resources"]["prestige_points"] = 4  # what the player could spend
    g2 = GameState()
    assert g2.import_save_string(_encode(data))
    assert g2.prestige_points == 4


# ---------- E2: offline progress trusts the clock and save file ----------
def _save_dated(g, seconds_ago, tmp_path):
    path = str(tmp_path / "s.zsave")
    g.save_game(path)
    with open(path, "rb") as f:
        data = json.loads(zlib.decompress(f.read()).decode())
    data["save_time"] = time.time() - seconds_ago
    with open(path, "wb") as f:
        f.write(zlib.compress(json.dumps(data).encode()))
    return path


def test_e2_offline_progress_is_capped(tmp_path):
    g = GameState()
    g.add_race("dwarf", 5)
    g2 = GameState()
    assert g2.load_game(_save_dated(g, 30 * 86400, tmp_path))
    summary = g2.pending_offline_summary
    assert summary["elapsed_seconds"] == pytest.approx(OFFLINE_PROGRESS_CAP)
    assert summary["capped"] is True

    g3 = GameState()
    assert g3.load_game(_save_dated(g, OFFLINE_PROGRESS_CAP, tmp_path))
    assert g2.resources["gold"] == pytest.approx(g3.resources["gold"], rel=1e-3)


def test_e2_future_dated_save_earns_nothing(tmp_path):
    g = GameState()
    g.add_race("dwarf", 5)
    gold = g.resources["gold"]
    g2 = GameState()
    assert g2.load_game(_save_dated(g, -86400, tmp_path))
    assert g2.pending_offline_summary is None
    assert g2.resources["gold"] == pytest.approx(gold)


# ---------- E14: Automatic Production lowered the offline rate ----------
def test_e14_automatic_production_only_raises_offline_rate():
    g = GameState()
    base = g.get_offline_rate()
    rates = []
    for lvl in range(1, 6):
        g.prestige_upgrades["automatic_production"]["level"] = lvl
        rates.append(g.get_offline_rate())
    assert rates[0] > base
    assert rates == sorted(rates) and len(set(rates)) == 5  # every level helps
    assert rates[-1] == pytest.approx(1.0)


# ---------- E3: Time Warp trusts the wall clock ----------
def test_e3_time_warp_ignores_wall_clock(monkeypatch):
    g = GameState()
    g.prestige_upgrades["time_warp"]["level"] = 1
    assert g.activate_time_warp()
    real_time = time.time
    monkeypatch.setattr(time, "time", lambda: real_time() + 10 * 86400)
    g.update(1.0)
    assert g.time_warp_active  # clock jump didn't end the warp
    assert g.activate_time_warp() is False  # nor clear the cooldown


def test_e3_time_warp_runs_on_play_time():
    g = GameState()
    g.prestige_upgrades["time_warp"]["level"] = 1
    g.add_race("dwarf", 1)
    assert g.activate_time_warp()
    g.update(TIME_WARP_DURATION - 1)
    assert g.time_warp_active
    g.update(2)
    assert not g.time_warp_active
    assert g.total_play_time == pytest.approx(TIME_WARP_DURATION + 1)  # real seconds, not warped
    assert g.activate_time_warp() is False  # still cooling down
    g.update(TIME_WARP_COOLDOWN)
    assert g.activate_time_warp()


def test_e3_warp_boosts_only_the_warped_part_of_a_tick():
    plain, warped = GameState(), GameState()
    for g in (plain, warped):
        g.add_race("dwarf", 1)
    warped.prestige_upgrades["time_warp"]["level"] = 1
    warped.activate_time_warp()
    warped.time_warp_remaining = 5.0
    plain.update(10.0)
    warped.update(10.0)
    # 5 s at 2x + 5 s at 1x = 15 s of production vs 10 s.
    gain_plain = plain.resources["stone"]
    assert warped.resources["stone"] == pytest.approx(1.5 * gain_plain, rel=1e-6)


def test_e3_old_save_deadlines_convert_to_countdowns():
    g = GameState()
    g.prestige_upgrades["time_warp"]["level"] = 1
    data = _decode(g.export_save_string())
    for k in ("time_warp_remaining", "time_warp_cooldown_remaining"):
        data.pop(k)
    data["version"] = "1.0.0"
    data["time_warp_cooldown_end"] = data["save_time"] + 7200
    g2 = GameState()
    assert g2.import_save_string(_encode(data))
    assert g2.time_warp_cooldown_remaining == pytest.approx(7200, abs=5)


# ---------- E4: imports are unvalidated ----------
def test_e4_import_rejects_impossible_values():
    g = GameState()
    data = _decode(g.export_save_string())
    data["resources"]["gold"] = -1e9
    data["resources"]["mana"] = "lots"
    data["races"]["dwarf"]["count"] = -5
    data["buildings"]["mine"]["level"] = 10_000
    data["buildings"]["marketplace"]["count"] = 40
    data["research"]["efficient_mining"]["level"] = 999
    data["prestige_upgrades"]["cosmic_insight"]["level"] = 99
    data["permanent_multipliers"] = {"all": 1e12}
    data["player_level"] = 500
    data["races"]["dragon"]["unlocked"] = True
    data["races"]["no_such_race"] = {"count": 3, "level": 1, "unlocked": True}
    data["time_warp_cooldown_remaining"] = -50
    g2 = GameState()
    assert g2.import_save_string(_encode(data))
    assert g2.resources["gold"] == 0
    assert g2.resources["mana"] == 0
    assert g2.races["dwarf"]["count"] == 0
    assert g2.buildings["mine"]["level"] == BUILDINGS["mine"]["max_level"]
    assert g2.buildings["marketplace"]["count"] == 1
    assert g2.research["efficient_mining"]["level"] == RESEARCH["efficient_mining"]["max_level"]
    assert g2.prestige_upgrades["cosmic_insight"]["level"] == 10
    assert g2.permanent_multipliers["all"] == pytest.approx(1.1 ** 10)
    assert g2.player_level == 1  # derived from earnings
    assert g2.races["dragon"]["unlocked"] is False
    assert "no_such_race" not in g2.races
    assert g2.time_warp_cooldown_remaining == 0
    g2.update(1.0)  # and the state still runs


def test_e4_import_rejects_non_object():
    g = GameState()
    assert g.import_save_string(_encode([1, 2, 3])) is False


# ---------- E5: abilities ----------
def _ready_for_mountain_heart(g):
    g.prestige_count = 1
    g.races["dwarf"]["count"] = 10
    g.races["dwarf"]["level"] = 50
    g.resources["gold"] = 2_000_000
    g.resources["stone"] = 1_000_000
    return g


def test_e5_abilities_never_spend_on_their_own():
    g = _ready_for_mountain_heart(GameState())
    gold, stone = g.resources["gold"], g.resources["stone"]
    ab.check_race_ability_unlocks(g)
    assert g.resources["gold"] == gold and g.resources["stone"] == stone
    assert g.races["dwarf"]["abilities"]["mountain_heart"]["unlocked"] is False
    assert ab.ability_status(g, "dwarf", "mountain_heart") == "available"
    assert any("available" in n["text"] for n in g.notifications)


def test_e5_buying_an_ability_charges_once_and_switches_it_on():
    g = _ready_for_mountain_heart(GameState())
    stone_rate = g.calculate_resource_generation_rate("stone") * g.calculate_global_multiplier("stone")
    assert g.buy_race_ability("dwarf", "mountain_heart")
    assert g.resources["gold"] == pytest.approx(1_000_000)
    assert g.resources["stone"] == pytest.approx(500_000)
    assert ab.ability_status(g, "dwarf", "mountain_heart") == "active"
    new_rate = g.calculate_resource_generation_rate("stone") * g.calculate_global_multiplier("stone")
    assert new_rate == pytest.approx(2 * stone_rate)
    assert g.calculate_resource_generation_rate("crystal") > 0  # crystal_chance by-product
    assert g.buy_race_ability("dwarf", "mountain_heart") is False  # can't buy twice


def test_e5_abilities_can_be_switched_off_and_on():
    g = _ready_for_mountain_heart(GameState())
    g.buy_race_ability("dwarf", "mountain_heart")
    on = g.calculate_global_multiplier("stone")
    assert g.toggle_race_ability("dwarf", "mountain_heart")
    assert g.calculate_global_multiplier("stone") == pytest.approx(on / 2)
    assert g.toggle_race_ability("dwarf", "mountain_heart")
    assert g.calculate_global_multiplier("stone") == pytest.approx(on)


def test_e5_locked_or_unaffordable_ability_costs_nothing():
    g = _ready_for_mountain_heart(GameState())
    g.resources["gold"] = 10
    assert g.buy_race_ability("dwarf", "mountain_heart") is False
    assert g.resources["gold"] == 10
    g.prestige_count = 0
    g.resources["gold"] = 2_000_000
    assert g.buy_race_ability("dwarf", "mountain_heart") is False
    assert g.resources["gold"] == 2_000_000


def test_e5_every_buyable_ability_changes_something():
    """No ability may charge its price and do nothing (the E6 trap)."""
    for race_id, info in RACES.items():
        for ab_id, ab_info in info["special_abilities"].items():
            if not ab.ability_is_implemented(ab_info):
                continue
            g = GameState()
            g.prestige_count = 10
            for r in RACES:
                g.races[r].update(unlocked=True, count=5, level=100)
            for b in BUILDINGS:
                g.buildings[b].update(unlocked=True, count=1)
            g.research["efficient_mining"].update(unlocked=True, level=3)
            g.player_level = 100
            for res in g.resources:
                g.resources[res] = 1e12

            def snapshot():
                rates = {r: g.calculate_resource_generation_rate(r) * g.calculate_global_multiplier(r)
                         for r in ("gold", "wood", "stone", "food", "mana", "crystal", "ancient_knowledge")}
                return rates, g.get_research_cost("efficient_mining", 1), \
                    ab.get_production_doubling_multiplier(g)

            before = snapshot()
            trial = copy.deepcopy(g)
            assert g.buy_race_ability(race_id, ab_id), (race_id, ab_id)
            after = snapshot()
            # Junk Alchemy works by conversion during ticks, not via rates.
            g.update(1.0)
            trial.update(1.0)
            ticked = any(g.resources[r] - trial.resources[r] > 1.0
                         for r in ("wood", "stone", "mana", "crystal"))
            assert before != after or ticked, f"{race_id}.{ab_id} does nothing"


def test_e5_unimplemented_abilities_cannot_be_bought():
    g = GameState()
    g.prestige_count = 10
    g.races["dragon"].update(unlocked=True, count=5, level=100)
    for res in g.resources:
        g.resources[res] = 1e12
    assert ab.ability_status(g, "dragon", "elder_breath") == "unimplemented"
    assert g.buy_race_ability("dragon", "elder_breath") is False
    assert g.resources["stone"] == 1e12


def test_e5_legacy_auto_unlocked_abilities_switch_on_at_load():
    g = _ready_for_mountain_heart(GameState())
    data = _decode(g.export_save_string())
    data["version"] = "1.0.0"
    data["races"]["dwarf"]["abilities"]["mountain_heart"] = {"unlocked": True, "active": False}
    g2 = GameState()
    assert g2.import_save_string(_encode(data))
    assert ab.ability_status(g2, "dwarf", "mountain_heart") == "active"


# ---------- E6: multiplier buildings ----------
def test_e6_multiplier_buildings_are_limited_to_one():
    g = GameState()
    g.buildings["marketplace"]["unlocked"] = True
    g.resources.update(gold=1e9, wood=1e9, stone=1e9)
    assert g.buy_building("marketplace", 1)
    gold = g.resources["gold"]
    assert g.buy_building("marketplace", 1) is False
    assert g.buy_building("marketplace", -1) is False
    assert g.resources["gold"] == gold
    assert g.buildings["marketplace"]["count"] == 1
    assert g.buy_building_upgrade("marketplace", 1)  # levels still improve it


# ---------- E7: charge before checking the cap ----------
@pytest.mark.parametrize("buy, setup", [
    ("buy_building_upgrade", lambda g: g.buildings["mine"].update(unlocked=True, count=1,
                                                                  level=BUILDINGS["mine"]["max_level"])),
    ("buy_research", lambda g: g.research["efficient_mining"].update(
        unlocked=True, level=RESEARCH["efficient_mining"]["max_level"])),
    ("buy_prestige_upgrade", lambda g: g.prestige_upgrades["eternal_knowledge"].update(level=5)),
    ("buy_race_upgrade", lambda g: g.races["dwarf"].update(count=0)),  # nothing to upgrade
])
def test_e7_refused_purchase_costs_nothing(buy, setup):
    g = GameState()
    for res in g.resources:
        g.resources[res] = 1e15
    setup(g)
    before = dict(g.resources)
    key = {"buy_building_upgrade": "mine", "buy_research": "efficient_mining",
           "buy_prestige_upgrade": "eternal_knowledge", "buy_race_upgrade": "dwarf"}[buy]
    assert getattr(g, buy)(key) is False
    assert g.resources == before


def test_e7_upgrade_count_is_clamped_before_pricing():
    g = GameState()
    g.buildings["mine"].update(unlocked=True, count=1, level=BUILDINGS["mine"]["max_level"] - 2)
    for res in g.resources:
        g.resources[res] = 1e40
    expected = g.get_building_upgrade_cost("mine", 2)
    before = dict(g.resources)
    assert g.buy_building_upgrade("mine", 10)
    assert g.buildings["mine"]["level"] == BUILDINGS["mine"]["max_level"]
    for r, a in expected.items():
        assert before[r] - g.resources[r] == pytest.approx(a)


# ---------- E8: "Upgrade Max" raised TypeError ----------
@pytest.mark.parametrize("fn", ["get_race_upgrade_cost", "get_building_upgrade_cost"])
def test_e8_upgrade_cost_accepts_level_override(fn):
    g = GameState()
    key = "dwarf" if "race" in fn else "mine"
    assert getattr(g, fn)(key, 1, 5) == getattr(g, fn)(key, 1, current_level_override=5)
    g.calculate_max_affordable_levels(key, fn, 1, 10)  # the old crash path


def test_e8_upgrade_max_buys_the_affordable_levels():
    g = GameState()
    g.races["dwarf"]["count"] = 1
    g.resources["gold"] = 250 * (2 ** 5 - 1)  # exactly levels 1→6
    assert g.buy_race_upgrade("dwarf", -1)
    assert g.races["dwarf"]["level"] == 6
    assert g.resources["gold"] == pytest.approx(0)


# ---------- E9: "Buy Max" usually failed ----------
def test_e9_buy_max_buys_the_largest_affordable_count():
    g = GameState()
    g.resources["gold"] = 10_000
    assert g.buy_race("dwarf", -1)
    n = g.races["dwarf"]["count"]
    assert n > 1
    assert not g.can_afford(g.get_race_purchase_cost("dwarf", 1))  # couldn't afford one more


def test_e9_closed_form_costs_match_unit_by_unit():
    g = GameState()
    g.races["dwarf"]["count"] = 3
    total = sum(g.get_race_purchase_cost("dwarf", 1, current_count_override=3 + i)["gold"] for i in range(7))
    assert g.get_race_purchase_cost("dwarf", 7)["gold"] == pytest.approx(total)
    g.buildings["mine"].update(count=2, level=4)
    for fn, kw in (("get_building_purchase_cost", "current_count_override"),
                   ("get_building_upgrade_cost", "current_level_override")):
        start = 2 if "purchase" in fn else 4
        parts = [getattr(g, fn)("mine", 1, **{kw: start + i}) for i in range(5)]
        whole = getattr(g, fn)("mine", 5)
        for r in whole:
            assert whole[r] == pytest.approx(sum(p[r] for p in parts))


def test_e9_buy_max_handles_huge_budgets_quickly():
    g = GameState()
    g.resources["gold"] = 1e20
    t0 = time.time()
    assert g.buy_race("dwarf", -1)
    assert time.time() - t0 < 0.5
    assert g.races["dwarf"]["count"] > 1
    assert not g.can_afford(g.get_race_purchase_cost("dwarf", 1))  # bought the maximum


# ---------- E10: races produce only their specialities ----------
def test_e10_races_produce_only_their_bonus_resources():
    g = GameState()
    g.add_race("dwarf", 1)
    g.update(10.0)
    assert g.resources["gold"] > 100 and g.resources["stone"] > 0
    for r in ("wood", "food", "mana", "crystal", "ancient_knowledge"):
        assert g.resources[r] == 0, r


def test_e10_every_resource_still_has_a_source():
    sources = set()
    for info in RACES.values():
        sources |= set(info["resource_bonuses"])
    for info in BUILDINGS.values():
        sources |= set(info.get("resource_production", {}))
    assert {"gold", "wood", "stone", "food", "mana", "crystal", "ancient_knowledge"} <= sources


# ---------- E12: production depends on the wall clock ----------
def test_e12_production_is_deterministic(monkeypatch):
    def run(clock_offset):
        real_time = time.time
        monkeypatch.setattr(time, "time", lambda: real_time() + clock_offset)
        g = GameState()
        g.prestige_count = 3
        for r in ("shade", "fae"):
            g.races[r].update(unlocked=True, count=5, level=100)
            for a in g.races[r]["abilities"].values():
                a.update(unlocked=True, active=True)
        for _ in range(20):
            g.update(0.5)
        monkeypatch.setattr(time, "time", real_time)
        return dict(g.resources)

    assert run(0) == run(1234)


# ---------- Found in review of the fixes ----------
def test_all_resources_skill_milestones_are_reachable():
    """E10 follow-up: "all resources" means the resources the race makes."""
    from game.logic import achievements as ach_logic
    g = GameState()
    g.prestige_count = 7
    g.races["celestial"].update(unlocked=True, count=1)
    for r in RACES["celestial"]["resource_bonuses"]:
        g.races["celestial"]["skills"][r] = 1e9
    ach_logic.check_race_skill_achievements(g)
    assert g.achievements["race_skill_milestones"]["celestial_alignment_1"] is True
    assert g.achievements["race_skill_milestones"]["celestial_alignment_2"] is True


def test_failed_import_leaves_state_untouched():
    g = GameState()
    g.add_race("dwarf", 3)
    before = copy.deepcopy(g.__dict__)
    data = _decode(g.export_save_string())
    data["resources"] = {"gold": 10 ** 400}   # float() overflows; must not raise out of load
    data["races"] = ["not", "a", "dict"]      # unusable: whole import is refused
    assert g.import_save_string(_encode(data)) is False
    after = copy.deepcopy(g.__dict__)
    after["notifications"] = before["notifications"]  # the failure notice is expected
    assert after == before


def test_huge_number_in_save_is_clamped_not_fatal():
    g = GameState()
    data = _decode(g.export_save_string())
    data["resources"]["gold"] = 10 ** 400
    g2 = GameState()
    assert g2.import_save_string(_encode(data))
    assert g2.resources["gold"] == 0


def test_explicit_huge_count_is_refused_not_raised():
    g = GameState()
    g.races["dwarf"]["count"] = 1
    g.resources["gold"] = 1e300
    assert g.buy_race_upgrade("dwarf", 5000) is False
