"""Regression tests for errata E15: 53 achievement rewards were read by no code.

A reward key means the same thing in every achievement category, and the same
as the ability effect of that name. Each test unlocks one achievement and
checks that what it should change changes, and the obvious rest does not.
"""
import pytest

from game.constants import ACHIEVEMENTS, PRESTIGE_REQUIREMENT_BASE, RACES, OFFLINE_PROGRESS_RATE
from game.game_state import GameState
from game.logic import race_abilities as ab

PRODUCED = ab.PRODUCED_RESOURCES


def unlock(g, *ids):
    for achievement_id in ids:
        for cat, milestones in ACHIEVEMENTS.items():
            if any(m["id"] == achievement_id for m in milestones):
                g.achievements[cat][achievement_id] = True
                break
        else:
            raise KeyError(achievement_id)
    return g


def realm(*races):
    """A state with each named race owned (10 at level 5), ready to produce."""
    g = GameState()
    g.prestige_count = 0
    for race_id in races:
        g.races[race_id].update(unlocked=True, count=10, level=5)
    return g


def mults(g):
    return {r: g.calculate_global_multiplier(r) for r in PRODUCED}


def ratios(before, after):
    return {r: after[r] / before[r] for r in before}


def assert_ratios(got, **expected):
    """Resources named in ``expected`` changed by that ratio, all others by 1."""
    for res, ratio in got.items():
        assert ratio == pytest.approx(expected.get(res, 1.0)), res


# --- Registry ---

def test_every_reward_and_effect_key_is_read_or_inactive():
    keys = set()
    for milestones in ACHIEVEMENTS.values():
        for m in milestones:
            keys |= set(m["reward"])
    for info in RACES.values():
        for ability in (info.get("special_abilities") or {}).values():
            keys |= set(ability["effects"])
    unknown = keys - ab.IMPLEMENTED_EFFECTS - ab.INACTIVE_EFFECTS
    assert not unknown, f"keys nothing reads: {sorted(unknown)}"
    assert not (ab.IMPLEMENTED_EFFECTS & ab.INACTIVE_EFFECTS)
    assert ab.INACTIVE_EFFECTS == {"resource_transmutation_efficiency"}


def test_renamed_deepling_key_fits_the_race_resource_pattern():
    deepling = next(m for m in ACHIEVEMENTS["race_skill_milestones"] if m["id"] == "deepling_knowledge_1")
    assert "deepling_ancient_knowledge_bonus" in deepling["reward"]
    assert "deepling_knowledge_bonus" not in deepling["reward"]


# --- Production multipliers ---

def test_resource_multiplier_from_a_race_skill_milestone():
    # dwarf_mining_4's stone_multiplier used to be read only from resource_milestones.
    g = realm("dwarf")
    before = mults(g)
    unlock(g, "dwarf_mining_4")
    assert_ratios(ratios(before, mults(g)), stone=1.2)


def test_all_resources_multiplier_applies_to_everything():
    g = realm()
    before = mults(g)
    unlock(g, "celestial_alignment_2")
    assert_ratios(ratios(before, mults(g)), **{r: 1.2 for r in PRODUCED})


def test_all_production_still_applies_from_any_category():
    g = realm()
    before = mults(g)
    unlock(g, "time_skill_1")
    assert_ratios(ratios(before, mults(g)), **{r: 1.1 for r in PRODUCED})


def test_parallel_production_bonus_is_one_plus_v_on_everything():
    g = realm()
    before = mults(g)
    unlock(g, "void_walker_mastery_2")  # all_resources 1.25 and parallel 0.2
    assert_ratios(ratios(before, mults(g)), **{r: 1.25 * 1.2 for r in PRODUCED})


def test_parallel_realms_ability_is_still_plus_twenty_percent():
    g = realm("void_walker")
    g.prestige_count = 7
    g.races["void_walker"]["abilities"]["parallel_realms"].update(unlocked=True, active=True)
    assert_ratios({r: ab.get_race_ability_multiplier(g, r) for r in PRODUCED},
                  **{r: 1.2 for r in PRODUCED})


def test_mana_regeneration_multiplies_mana_only():
    g = realm()
    before = mults(g)
    unlock(g, "elf_woodcutting_4")  # wood_multiplier 1.2 and mana_regeneration 1.1
    assert_ratios(ratios(before, mults(g)), wood=1.2, mana=1.1)


def test_food_consumption_reduction_frees_food():
    g = realm()
    before = mults(g)
    unlock(g, "troll_strength_4")  # stone_multiplier 1.2 and food 1 / (1 - 0.2)
    assert_ratios(ratios(before, mults(g)), stone=1.2, food=1 / 0.8)


def test_iron_stomach_ability_is_now_buyable():
    g = realm("troll")
    g.prestige_count = 2
    g.races["troll"]["level"] = 100
    g.resources.update(stone=10_000_000, food=1_000_000)
    assert ab.ability_status(g, "troll", "iron_stomach") == "available"
    before = g.calculate_global_multiplier("food")
    assert g.buy_race_ability("troll", "iron_stomach")
    assert g.calculate_global_multiplier("food") == pytest.approx(before / 0.8)


# --- Race-specific output ---

def test_race_resource_bonus_multiplies_that_races_output_only():
    g = realm("dwarf", "elf")
    dwarf, elf = g.get_race_contribution("dwarf", "stone"), g.get_race_contribution("elf", "wood")
    unlock(g, "dwarf_mining_1")  # dwarf_stone_bonus
    bonus = next(m for m in ACHIEVEMENTS["race_skill_milestones"]
                 if m["id"] == "dwarf_mining_1")["reward"]["dwarf_stone_bonus"]
    assert g.get_race_contribution("dwarf", "stone") == pytest.approx(dwarf * bonus)
    assert g.get_race_contribution("elf", "wood") == pytest.approx(elf)


def test_race_efficiency_applies_from_race_milestones():
    g = realm("dwarf")
    stone = g.get_race_contribution("dwarf", "stone")
    gold = g.get_race_contribution("dwarf", "gold")
    unlock(g, "dwarf_1")  # category race_milestones, dwarf_efficiency 1.1
    assert g.get_race_contribution("dwarf", "stone") == pytest.approx(stone * 1.1)
    assert g.get_race_contribution("dwarf", "gold") == pytest.approx(gold * 1.1)


def test_deepling_ancient_knowledge_bonus_applies():
    g = realm("deepling")
    before = g.get_race_contribution("deepling", "ancient_knowledge")
    mana = g.get_race_contribution("deepling", "mana")
    unlock(g, "deepling_knowledge_1")
    assert g.get_race_contribution("deepling", "ancient_knowledge") == pytest.approx(before * 1.2)
    assert g.get_race_contribution("deepling", "mana") == pytest.approx(mana)


def test_all_race_efficiency_is_unchanged():
    g = realm("dwarf")
    before = g.get_race_contribution("dwarf", "stone")
    unlock(g, "all_races_1")
    assert g.get_race_contribution("dwarf", "stone") == pytest.approx(before * 1.05)


def test_crystal_chance_pays_a_share_of_the_milestone_races_stone():
    g = realm("dwarf", "troll")
    before = g.calculate_resource_generation_rate("crystal")
    unlock(g, "dwarf_mining_4")
    dwarf_stone = g.get_race_contribution("dwarf", "stone")
    assert g.calculate_resource_generation_rate("crystal") == pytest.approx(before + 0.05 * dwarf_stone)
    # The troll's stone does not count: the reward belongs to the dwarf.
    assert ab.get_ability_byproduct_rate(g, "crystal") == pytest.approx(0.05 * dwarf_stone)
    assert ab.get_ability_byproduct_rate(g, "stone") == 0.0


def test_mountain_heart_ability_still_works_the_same_way():
    g = realm("dwarf")
    g.races["dwarf"]["abilities"]["mountain_heart"].update(unlocked=True, active=True)
    effect = RACES["dwarf"]["special_abilities"]["mountain_heart"]["effects"]["crystal_chance"]
    assert ab.get_ability_byproduct_rate(g, "crystal") == pytest.approx(
        effect * g.get_race_contribution("dwarf", "stone"))


# --- Costs, buildings, research ---

def test_building_cost_reduction_is_read_from_the_reward():
    g = realm()
    before = g.get_building_purchase_cost("farm"), g.get_building_upgrade_cost("farm")
    unlock(g, "first_building")
    after = g.get_building_purchase_cost("farm"), g.get_building_upgrade_cost("farm")
    for b, a in zip(before, after):
        for res in b:
            assert a[res] == pytest.approx(b[res] * 0.95)
    # Not hardcoded: a different reward value changes the price.
    for m in ACHIEVEMENTS["building_milestones"]:
        if m["id"] == "first_building":
            m["reward"]["building_cost_reduction"] = 0.5
            try:
                assert g.get_building_purchase_cost("farm")["gold"] == pytest.approx(before[0]["gold"] * 0.5)
            finally:
                m["reward"]["building_cost_reduction"] = 0.95


def test_building_efficiency_multiplies_building_output_and_combines():
    g = realm()
    g.buildings["farm"].update(unlocked=True, count=3)
    before = g.calculate_resource_generation_rate("food")
    assert before > 0
    unlock(g, "building_level_10")
    assert g.calculate_resource_generation_rate("food") == pytest.approx(before * 1.05)
    g.races["dwarf"].update(unlocked=True, count=1, level=1)
    g.races["dwarf"]["abilities"]["master_smiths"].update(unlocked=True, active=True)
    smiths = RACES["dwarf"]["special_abilities"]["master_smiths"]["effects"]["building_efficiency"]
    assert ab.get_building_efficiency(g) == pytest.approx(1.05 * smiths)


def test_research_speed_makes_research_cheaper_and_combines_with_abilities():
    g = realm()
    research_id = next(iter(g.research))
    before = g.get_research_cost(research_id)
    unlock(g, "knowledge_1")  # research_speed 1.1
    after = g.get_research_cost(research_id)
    for res in before:
        assert after[res] == pytest.approx(before[res] / 1.1)
    g.races["human"].update(unlocked=True, count=1, level=1)
    g.races["human"]["abilities"]["technological_mastery"].update(unlocked=True, active=True)
    assert ab.get_research_cost_factor(g) == pytest.approx(0.5 / 1.1)


# --- Prestige and offline ---

def test_prestige_point_multiplier_and_bonus_apply_from_any_category():
    g = realm()
    g.total_earnings = 100 * PRESTIGE_REQUIREMENT_BASE  # base = 10
    assert g.calculate_prestige_points() == 10
    unlock(g, "time_skill_4")
    assert g.calculate_prestige_points() == 12
    unlock(g, "first_prestige")  # prestige_point_bonus 1
    assert g.calculate_prestige_points() == 13


def test_offline_progress_bonus_adds_to_the_rate_and_is_capped():
    g = realm()
    assert g.get_offline_rate() == pytest.approx(OFFLINE_PROGRESS_RATE)
    unlock(g, "played_1_day")  # +0.1
    assert g.get_offline_rate() == pytest.approx(OFFLINE_PROGRESS_RATE + 0.1)
    unlock(g, "played_1_week")  # +0.2
    assert g.get_offline_rate() == pytest.approx(OFFLINE_PROGRESS_RATE + 0.3)
    g.prestige_upgrades["automatic_production"]["level"] = 1000
    assert g.get_offline_rate() == 1.0


def test_passive_prestige_generation_trickles_a_share_of_the_pending_gain():
    g = realm()
    g.total_earnings = 100 * PRESTIGE_REQUIREMENT_BASE
    pending = g.calculate_prestige_points()
    assert pending > 0
    before, total = g.prestige_points, g.total_prestige_points
    ab.generate_passive_prestige_points(g, 10.0)
    assert g.prestige_points == before and g.total_prestige_points == total
    unlock(g, "celestial_alignment_2")  # 0.0001
    ab.generate_passive_prestige_points(g, 10.0)
    assert g.prestige_points == pytest.approx(before + pending * 0.0001 * 10.0)
    assert g.total_prestige_points == pytest.approx(total + pending * 0.0001 * 10.0)
    assert g.prestige_count == 0  # nothing reset
    assert g.total_earnings == 100 * PRESTIGE_REQUIREMENT_BASE


# --- Conversion, doubling, inactive ---

def test_resource_conversion_rate_matches_junk_alchemy():
    g = realm("goblin")
    g.resources.update({r: 0.0 for r in ab.BASIC_RESOURCES})
    ab.apply_special_resource_generation(g, 10.0)
    assert g.resources["wood"] == 0
    unlock(g, "goblin_scavenging_4")  # 1.1 -> 10% of food production
    food = g.calculate_resource_generation_rate("food") * g.calculate_global_multiplier("food")
    assert food > 0
    ab.apply_special_resource_generation(g, 10.0)
    assert g.resources["wood"] == pytest.approx(food * 0.1 * 10.0)
    assert g.resources["food"] == 0  # food itself is not used up


def test_production_doubling_chance_combines_with_the_ability():
    g = realm("shade")
    assert ab.get_production_doubling_multiplier(g) == 1.0
    unlock(g, "shade_magic_4")  # 0.05
    assert ab.get_production_doubling_multiplier(g) == pytest.approx(1.05)
    g.prestige_count = 3
    g.races["shade"]["abilities"]["echo_of_the_dead"].update(unlocked=True, active=True)
    assert ab.get_production_doubling_multiplier(g) == pytest.approx(1.0 + 1 - 0.95 * 0.95)


def test_transmutation_reward_stays_inactive_and_is_labelled():
    g = realm("dragon")
    before = mults(g)
    unlock(g, "dragon_hoard_2")  # gold_multiplier 1.3 only
    assert_ratios(ratios(before, mults(g)), gold=1.3)
    g.prestige_count = 10
    g.races["dragon"]["level"] = 100
    for res in g.resources:
        g.resources[res] = 1e12
    assert ab.ability_status(g, "dragon", "elder_breath") == "unimplemented"
    from game.tui.tabs import AchievementsTab
    text = AchievementsTab.detail(type("T", (), {"game_state": g, "empty_detail": ""})(),
                                  "race_skill_milestones:dragon_hoard_2")
    assert "resource_transmutation_efficiency=1.5 (inactive: no transmutation yet)" in text
    assert "dragon_gold_bonus=1.6" in text and "inactive" not in text.replace(
        "resource_transmutation_efficiency=1.5 (inactive: no transmutation yet)", "")


# --- Nothing applied twice, old rewards keep their values ---

def test_pre_existing_rewards_keep_their_values():
    g = realm()
    before = mults(g)
    unlock(g, "gold_1")
    assert_ratios(ratios(before, mults(g)), gold=1.05)  # not 1.05 twice
    before = mults(g)
    unlock(g, "time_skill_1")
    assert_ratios(ratios(before, mults(g)), **{r: 1.1 for r in PRODUCED})
    g2 = realm()
    g2.total_earnings = 100 * PRESTIGE_REQUIREMENT_BASE
    unlock(g2, "prestige_5")
    assert g2.calculate_prestige_points() == 11  # int(10 * 1.1)
    g3 = realm("dwarf")
    stone = g3.get_race_contribution("dwarf", "stone")
    unlock(g3, "dwarf_mining_4")
    bonus = ACHIEVEMENTS["race_skill_milestones"]
    reward = next(m for m in bonus if m["id"] == "dwarf_mining_4")["reward"]
    assert g3.get_race_contribution("dwarf", "stone") == pytest.approx(stone * reward["dwarf_stone_bonus"])


def test_a_save_round_trip_keeps_rewards_working(tmp_path):
    g = realm("dwarf")
    unlock(g, "dwarf_mining_4", "first_building")
    blob = g.export_save_string()
    h = GameState()
    assert h.import_save_string(blob)
    assert h.get_building_purchase_cost("farm")["gold"] == pytest.approx(g.get_building_purchase_cost("farm")["gold"])
    assert h.calculate_global_multiplier("stone") == pytest.approx(g.calculate_global_multiplier("stone"))
