"""Headless tests for the core game state — no pygame, no UI."""
import os
import time

import pytest

from game.game_state import GameState
from game.constants import (
    PRESTIGE_REQUIREMENT_BASE,
    BASE_INCOME_RATE,
    RACES,
    BUILDINGS,
)


def fresh_state():
    return GameState()


# ---------- Initialization ----------
def test_starts_with_starting_gold():
    g = fresh_state()
    assert g.resources["gold"] == 100
    for r in ("wood", "stone", "food", "mana", "crystal", "ancient_knowledge"):
        assert g.resources[r] == 0
    assert g.player_level == 1
    assert g.prestige_count == 0


def test_initial_unlocks_match_unlock_level_1():
    g = fresh_state()
    for race_id, info in RACES.items():
        assert g.races[race_id]["unlocked"] == (info["unlock_level"] == 1)
    for b_id, info in BUILDINGS.items():
        assert g.buildings[b_id]["unlocked"] == (info["unlock_level"] <= 1)


# ---------- Resource generation ----------
def test_idle_with_no_units_produces_nothing():
    g = fresh_state()
    g.update(60.0)
    assert g.resources["gold"] == 100  # starting gold, no production


def test_dwarves_produce_gold_and_stone():
    g = fresh_state()
    g.add_race("dwarf", 5)
    g.update(10.0)
    assert g.resources["gold"] > 100
    assert g.resources["stone"] > 0


def test_total_earnings_tracks_gold_only():
    g = fresh_state()
    g.add_race("dwarf", 1)
    before = g.total_earnings
    g.update(5.0)
    # total_earnings should accumulate gold gained
    assert g.total_earnings > before
    # And approximately equal gold gained from 0
    assert g.total_earnings == pytest.approx(g.resources["gold"] - 100, rel=0.01)


# ---------- Costs ----------
def test_race_purchase_cost_scales_with_count():
    g = fresh_state()
    c1 = g.get_race_purchase_cost("dwarf", 1)["gold"]
    g.races["dwarf"]["count"] = 10
    c2 = g.get_race_purchase_cost("dwarf", 1)["gold"]
    assert c2 > c1


def test_calculate_max_affordable_returns_zero_when_broke():
    g = fresh_state()
    g.resources["gold"] = 0
    cost = {"gold": 1000}
    assert g.calculate_max_affordable(cost) == 0


def test_calculate_max_affordable_with_enough_resources():
    g = fresh_state()
    g.resources["gold"] = 1000
    assert g.calculate_max_affordable({"gold": 100}) == 10


# ---------- Affordability / spending ----------
def test_can_afford_and_spend_resources():
    g = fresh_state()
    assert g.can_afford({"gold": 50})
    assert not g.can_afford({"gold": 999_999})
    assert g.spend_resources({"gold": 50})
    assert g.resources["gold"] == 50
    assert not g.spend_resources({"gold": 999_999})


# ---------- Prestige ----------
def test_calculate_prestige_points_below_threshold():
    g = fresh_state()
    g.total_earnings = PRESTIGE_REQUIREMENT_BASE - 1
    assert g.calculate_prestige_points() == 0


def test_calculate_prestige_points_at_threshold():
    g = fresh_state()
    g.total_earnings = PRESTIGE_REQUIREMENT_BASE
    assert g.calculate_prestige_points() >= 1


def test_perform_prestige_resets_progression_and_awards_points():
    g = fresh_state()
    g.add_race("dwarf", 10)
    g.add_building("mine", 1)
    g.research["efficient_mining"]["level"] = 5
    g.research["efficient_mining"]["unlocked"] = True
    g.player_level = 25
    g.total_earnings = 4_000_000
    expected = g.calculate_prestige_points()
    assert expected > 0

    assert g.perform_prestige() is True

    assert g.prestige_count == 1
    assert g.prestige_points == expected
    assert g.total_prestige_points == expected
    assert g.resources["gold"] == 100  # default starting gold
    assert g.total_earnings == 0
    assert g.player_level == 1
    assert g.races["dwarf"]["count"] == 0
    assert g.buildings["mine"]["count"] == 0
    assert g.research["efficient_mining"]["level"] == 0


def test_perform_prestige_fails_below_threshold():
    g = fresh_state()
    g.total_earnings = 1000
    assert g.perform_prestige() is False
    assert g.prestige_count == 0


def test_prestige_bonus_applies_to_production():
    g = fresh_state()
    g.add_race("dwarf", 5)
    rate_before = g.calculate_global_multiplier("gold")
    g.prestige_count = 3
    rate_after = g.calculate_global_multiplier("gold")
    assert rate_after > rate_before


# ---------- Time Warp ----------
def test_time_warp_locked_by_default():
    g = fresh_state()
    assert g.has_time_warp_unlocked() is False
    assert g.activate_time_warp() is False


def test_time_warp_activates_when_unlocked():
    g = fresh_state()
    g.prestige_upgrades["time_warp"]["level"] = 1
    assert g.has_time_warp_unlocked() is True
    assert g.activate_time_warp() is True
    assert g.time_warp_active is True
    assert g.get_time_warp_multiplier() == pytest.approx(2.0)


def test_time_warp_blocks_on_cooldown():
    g = fresh_state()
    g.prestige_upgrades["time_warp"]["level"] = 1
    g.time_warp_cooldown_end = time.time() + 3600
    assert g.activate_time_warp() is False


# ---------- Save / Load ----------
def test_export_import_save_roundtrip():
    g = fresh_state()
    g.add_race("dwarf", 7)
    g.buildings["mine"]["unlocked"] = True
    g.add_building("mine", 2)
    g.update(5.0)
    g.prestige_points = 42

    blob = g.export_save_string()
    assert blob

    g2 = GameState()
    assert g2.import_save_string(blob) is True
    assert g2.prestige_points == 42
    assert g2.races["dwarf"]["count"] == 7
    assert g2.buildings["mine"]["count"] == 2
    # Offline progress adds a small amount during load, so allow tolerance
    assert g2.resources["gold"] >= g.resources["gold"]
    assert g2.resources["gold"] == pytest.approx(g.resources["gold"], rel=0.05)


def test_save_file_roundtrip(tmp_path):
    g = fresh_state()
    g.add_race("elf", 3)
    g.update(10.0)
    elf_count = g.races["elf"]["count"]
    elf_gold = g.resources["gold"]

    save_path = str(tmp_path / "test.zsave")
    assert g.save_game(save_path) is True
    assert os.path.exists(save_path)

    g2 = GameState()
    assert g2.load_game(save_path) is True
    assert g2.races["elf"]["count"] == elf_count
    # Allow tiny offline progress added on load
    assert g2.resources["gold"] >= elf_gold


def test_import_invalid_save_returns_false():
    g = fresh_state()
    assert g.import_save_string("not a valid base64 zlib payload!!!") is False


# ---------- Player level / unlocks ----------
def test_check_unlocks_levels_up_with_earnings():
    g = fresh_state()
    g.total_earnings = 5000  # 1 + 5000//1000 = 6
    g.check_unlocks()
    assert g.player_level == 6


def test_check_unlocks_unlocks_higher_level_buildings():
    g = fresh_state()
    g.total_earnings = 5000
    g.check_unlocks()  # level 6, marketplace unlocks at 5
    assert g.buildings["marketplace"]["unlocked"] is True


# ---------- Race roster ----------
EXPECTED_RACES = {
    "dwarf", "elf", "human", "goblin", "troll", "shade",
    "fae", "celestial", "deepling", "dragon", "void_walker",
}


def test_all_expected_races_exist():
    from game.constants import RACES
    assert set(RACES) == EXPECTED_RACES


def test_late_races_require_prestige():
    from game.constants import RACES
    for late in ("celestial", "deepling", "dragon", "void_walker"):
        assert RACES[late].get("requires_prestige", 0) >= 1


def test_initial_state_has_all_races():
    g = fresh_state()
    assert set(g.races) == EXPECTED_RACES
    # Tier-1 races start unlocked, prestige-gated ones do not.
    assert g.races["dwarf"]["unlocked"] is True
    assert g.races["dragon"]["unlocked"] is False


# ---------- Offline progress summary ----------
def test_offline_summary_set_on_load(tmp_path):
    g = fresh_state()
    g.add_race("dwarf", 5)
    save_path = str(tmp_path / "test.zsave")
    g.save_game(save_path)

    # Backdate save_time so load detects "elapsed" offline time.
    import json, zlib
    with open(save_path, "rb") as f:
        data = json.loads(zlib.decompress(f.read()).decode())
    data["save_time"] = time.time() - 600  # 10 minutes ago
    with open(save_path, "wb") as f:
        f.write(zlib.compress(json.dumps(data).encode(), level=9))

    g2 = GameState()
    assert g2.load_game(save_path)
    assert g2.pending_offline_summary is not None
    summary = g2.pending_offline_summary
    assert summary["elapsed_seconds"] == pytest.approx(600, rel=0.1)
    assert summary["rate"] > 0
    assert any(amount > 0 for amount in summary["gained"].values())


def test_load_backfills_missing_races_from_old_save(tmp_path):
    """Saves from before new races were added must still load."""
    import json, zlib
    # Build an "old" save with only the original 3 races / fewer keys.
    old_data = {
        "resources": {"gold": 100, "wood": 0, "stone": 0, "food": 0,
                      "mana": 0, "crystal": 0, "ancient_knowledge": 0,
                      "prestige_points": 0},
        "races": {
            "dwarf": {"count": 0, "level": 1, "unlocked": True, "abilities": {}, "skills": {}},
            "elf":   {"count": 0, "level": 1, "unlocked": True, "abilities": {}, "skills": {}},
            "human": {"count": 0, "level": 1, "unlocked": True, "abilities": {}, "skills": {}},
        },
        "buildings": {"mine": {"count": 0, "level": 1, "unlocked": False}},
        "research": {},
        "prestige_upgrades": {},
        "achievements": {},
        "player_level": 1,
        "total_earnings": 0,
        "prestige_count": 0,
        "prestige_points": 0,
        "total_prestige_points": 0,
        "permanent_multipliers": {"all": 1.0},
        "total_play_time": 0,
        "time_warp_active": False,
        "time_warp_end_time": 0,
        "time_warp_cooldown_end": 0,
        "save_time": time.time(),
        "version": "0.0.0",
    }
    save_path = tmp_path / "old.zsave"
    save_path.write_bytes(zlib.compress(json.dumps(old_data).encode(), level=9))

    g = GameState()
    assert g.load_game(str(save_path)) is True
    # Every race in current RACES must now be present.
    for race_id in EXPECTED_RACES:
        assert race_id in g.races
    # And iterating + ticking must not KeyError.
    g.update(1.0)


def test_offline_summary_skipped_for_short_gaps():
    g = fresh_state()
    blob = g.export_save_string()
    g2 = GameState()
    g2.import_save_string(blob)
    # Roundtrip is sub-second; no welcome-back should fire.
    assert g2.pending_offline_summary is None
