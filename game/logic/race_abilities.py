"""Race special abilities.

An ability becomes *available* when its race reaches the required level and
the realm the required prestige count. The player then buys it explicitly
(its unlock_requirements["resources"] is the price), after which it can be
switched on and off. Buying switches it on. (Errata E5: abilities used to
unlock automatically, silently deducting the price, and nothing could ever
switch them on.)

Every effect is deterministic: chance-based effects pay their expected value,
and timed effects run on accumulated play time, not the wall clock (E12).
"""
from game.constants import RACES, RESOURCE_TYPES
from game.logic import achievements as achievement_logic

PRODUCED_RESOURCES = [r for r in RESOURCE_TYPES if r != "prestige_points"]
BASIC_RESOURCES = ("wood", "stone", "food", "mana", "crystal")

# Effect keys the engine applies. An ability with any other key would charge
# its price and do nothing, so it can't be bought until it is implemented.
# Achievement rewards use the same vocabulary, with the same meaning (errata
# E15: 53 achievement rewards used to be read by no code at all).
IMPLEMENTED_EFFECTS = {f"{r}_multiplier" for r in PRODUCED_RESOURCES} | {
    "all_resources_multiplier",
    "all_production",
    "global_multiplier",
    "parallel_production_bonus",  # all resources x (1 + v)
    "mana_regeneration",
    "building_efficiency",
    "building_cost_reduction",
    "research_speed",
    "food_consumption_reduction",
    "offline_progress_bonus",
    "passive_prestige_generation",
    "prestige_point_multiplier",
    "prestige_point_bonus",
    "all_race_efficiency",  # read by GameState.get_race_bonus_multiplier
    "passive_generation",
    "crystal_chance",
    "research_cost_reduction",
    "research_effect_bonus",
    "production_doubling_chance",
    "resource_conversion_rate",
    "timed_production_bonus",
    "per_unit_bonus",
    "gold_storage_bonus",
} | {f"{race}_efficiency" for race in RACES} | {
    f"{race}_{r}_bonus" for race in RACES for r in PRODUCED_RESOURCES
}

# Effects no system exists for yet. They are shown as inactive and any ability
# carrying one cannot be bought.
INACTIVE_EFFECTS = {
    "resource_transmutation_efficiency",  # no transmutation system yet
}


# --- Lookup helpers ---

def _ability_info(race_id, ability_id):
    return RACES.get(race_id, {}).get("special_abilities", {}).get(ability_id)


def _ability_state(game_state, race_id, ability_id):
    race_data = game_state.races.get(race_id)
    if race_data is None or _ability_info(race_id, ability_id) is None:
        return None
    abilities = race_data.setdefault("abilities", {})
    return abilities.setdefault(ability_id, {"unlocked": False, "active": False})


def _active_abilities(game_state):
    """Yield (race_id, race_data, effects) for owned, switched-on abilities of
    races the player currently has."""
    for race_id, race_data in game_state.races.items():
        if not race_data["unlocked"] or race_data["count"] <= 0:
            continue
        specials = RACES[race_id].get("special_abilities") or {}
        for ability_id, state in race_data.get("abilities", {}).items():
            if state.get("unlocked") and state.get("active") and ability_id in specials:
                yield race_id, race_data, specials[ability_id]["effects"]


def _active_effects(game_state):
    """Yield (race_id or None, effects) for every switched-on ability and
    every unlocked achievement reward (errata E15: one place reads both, so a
    key means the same thing whichever one carries it)."""
    for race_id, _, effects in _active_abilities(game_state):
        yield race_id, effects
    yield from achievement_logic.unlocked_rewards(game_state)


def ability_is_implemented(ability_info):
    return set(ability_info.get("effects", {})) <= IMPLEMENTED_EFFECTS


def ability_requirements_met(game_state, race_id, ability_id):
    """Race level and prestige requirements (not the price)."""
    info = _ability_info(race_id, ability_id)
    race_data = game_state.races.get(race_id)
    if info is None or race_data is None:
        return False
    if not race_data["unlocked"] or race_data["count"] <= 0:
        return False
    req = info.get("unlock_requirements", {})
    return (race_data["level"] >= req.get("race_level", 0)
            and game_state.prestige_count >= req.get("prestige_level", 0))


def ability_cost(race_id, ability_id):
    info = _ability_info(race_id, ability_id)
    return dict(info.get("unlock_requirements", {}).get("resources", {})) if info else {}


def ability_status(game_state, race_id, ability_id):
    """One of: "active", "inactive", "available", "locked", "unimplemented"."""
    info = _ability_info(race_id, ability_id)
    state = _ability_state(game_state, race_id, ability_id)
    if info is None or state is None:
        return "locked"
    if state.get("unlocked"):
        return "active" if state.get("active") else "inactive"
    if not ability_is_implemented(info):
        return "unimplemented"
    return "available" if ability_requirements_met(game_state, race_id, ability_id) else "locked"


# --- Player actions ---

def check_race_ability_unlocks(game_state):
    """Announce, once, each ability that has become available to buy.

    Never spends anything: buying is an explicit player action.
    """
    for race_id, race_data in game_state.races.items():
        for ability_id, info in (RACES[race_id].get("special_abilities") or {}).items():
            state = _ability_state(game_state, race_id, ability_id)
            if state.get("unlocked") or state.get("available_notified"):
                continue
            if ability_is_implemented(info) and ability_requirements_met(game_state, race_id, ability_id):
                state["available_notified"] = True
                game_state.add_notification(
                    f"Race ability available: {RACES[race_id]['name']} - {info['name']} "
                    f"(buy it in the Races tab)",
                    notification_type="unlock",
                )


def purchase_race_ability(game_state, race_id, ability_id):
    """Buy an available ability and switch it on. Returns False, spending
    nothing, if it is owned, unimplemented, locked or unaffordable."""
    info = _ability_info(race_id, ability_id)
    state = _ability_state(game_state, race_id, ability_id)
    if info is None or state is None or state.get("unlocked"):
        return False
    if not ability_is_implemented(info):
        return False
    if not ability_requirements_met(game_state, race_id, ability_id):
        return False
    if not game_state.spend_resources(ability_cost(race_id, ability_id)):
        return False
    state["unlocked"] = True
    state["active"] = True
    state["available_notified"] = True
    game_state.add_notification(
        f"Race ability bought: {RACES[race_id]['name']} - {info['name']} (active)",
        notification_type="unlock",
    )
    return True


def activate_race_ability(game_state, race_id, ability_id):
    """Switch an owned ability on or off."""
    state = _ability_state(game_state, race_id, ability_id)
    if state is None or not state.get("unlocked"):
        return False
    state["active"] = not state.get("active", False)
    info = _ability_info(race_id, ability_id)
    status = "activated" if state["active"] else "deactivated"
    game_state.add_notification(f"{RACES[race_id]['name']} ability {info['name']} {status}!", notification_type="info")
    return True


# --- Effects ---

def get_race_ability_multiplier(game_state, resource):
    """Multiplier on ``resource`` from switched-on abilities."""
    multiplier = 1.0
    for _, effects in _active_effects(game_state):
        if f"{resource}_multiplier" in effects:
            multiplier *= effects[f"{resource}_multiplier"]
        for key in ("all_resources_multiplier", "global_multiplier", "all_production"):
            if key in effects:
                multiplier *= effects[key]
        if "parallel_production_bonus" in effects:
            multiplier *= 1.0 + effects["parallel_production_bonus"]
        if resource == "mana" and "mana_regeneration" in effects:
            multiplier *= effects["mana_regeneration"]
        # There is no food consumption, so a cut in it frees food for the realm.
        if resource == "food" and "food_consumption_reduction" in effects:
            multiplier /= max(1e-9, 1.0 - effects["food_consumption_reduction"])
    return multiplier


def get_race_reward_multiplier(game_state, race_id, resource):
    """Multiplier on one race's own output of ``resource`` from
    ``{race}_{resource}_bonus`` and ``{race}_efficiency`` effects."""
    mult = 1.0
    for _, effects in _active_effects(game_state):
        mult *= effects.get(f"{race_id}_{resource}_bonus", 1.0)
        mult *= effects.get(f"{race_id}_efficiency", 1.0)
    return mult


def get_race_specific_ability_bonus(game_state, race_id, resource):
    """Race-specific multiplier on one race's own output."""
    bonus = 1.0
    race_data = game_state.races.get(race_id)
    if race_data is None or not race_data["unlocked"]:
        return bonus
    specials = RACES[race_id].get("special_abilities") or {}
    for ability_id, state in race_data.get("abilities", {}).items():
        if not (state.get("unlocked") and state.get("active")) or ability_id not in specials:
            continue
        effects = specials[ability_id]["effects"]
        if "per_unit_bonus" in effects:
            bonus += effects["per_unit_bonus"] * race_data["count"]
        if "gold_storage_bonus" in effects and resource == "gold":
            bonus += (game_state.resources.get("gold", 0) / 1000) * effects["gold_storage_bonus"]
    return bonus


def get_passive_generation_rate(game_state, resource):
    """Flat production of every resource from abilities like Nature Harmony."""
    rate = 0.0
    for _, effects in _active_effects(game_state):
        if "passive_generation" in effects:
            rate += effects["passive_generation"] * game_state.player_level
    return rate


def get_ability_byproduct_rate(game_state, resource, race_bonus_mult=None):
    """Production one resource yields as a by-product of another.

    crystal_chance (Mountain Heart): each unit of stone the race mines has
    that chance of turning up a crystal, paid as its expected value.
    """
    rate = 0.0
    if resource != "crystal":
        return rate
    for race_id, effects in _active_effects(game_state):
        if "crystal_chance" in effects and race_id is not None:
            stone = game_state.get_race_contribution(race_id, "stone", race_bonus_mult)
            rate += effects["crystal_chance"] * stone
    return rate


def get_building_efficiency(game_state):
    """Multiplier on all building production (Master Smiths)."""
    eff = 1.0
    for _, effects in _active_effects(game_state):
        if "building_efficiency" in effects:
            eff *= effects["building_efficiency"]
    return eff


def get_research_cost_factor(game_state):
    """Multiplier on research costs (Technological Mastery, Abyssal Gaze,
    research_speed). Research is bought instantly, so "speed" means cheaper."""
    factor = 1.0
    for _, effects in _active_effects(game_state):
        if "research_cost_reduction" in effects:
            factor *= max(0.0, 1.0 - effects["research_cost_reduction"])
        if "research_speed" in effects:
            factor /= effects["research_speed"]
    return factor


def get_building_cost_factor(game_state):
    """Multiplier on building purchase and upgrade costs."""
    factor = 1.0
    for _, effects in _active_effects(game_state):
        if "building_cost_reduction" in effects:
            factor *= effects["building_cost_reduction"]
    return factor


def get_offline_progress_bonus(game_state):
    """Extra share of production earned while away."""
    return sum(effects.get("offline_progress_bonus", 0.0) for _, effects in _active_effects(game_state))


def get_prestige_point_modifiers(game_state):
    """(multiplier, flat bonus) applied to a prestige's point gain."""
    mult, flat = 1.0, 0
    for _, effects in _active_effects(game_state):
        mult *= effects.get("prestige_point_multiplier", 1.0)
        flat += effects.get("prestige_point_bonus", 0)
    return mult, flat


def get_research_effect_bonus(game_state):
    """Multiplier on the strength of every research effect."""
    bonus = 1.0
    for _, effects in _active_effects(game_state):
        if "research_effect_bonus" in effects:
            bonus *= effects["research_effect_bonus"]
    return bonus


def get_production_doubling_multiplier(game_state):
    """Expected multiplier from "chance to fire twice" abilities.

    With chances p1, p2, ... a tick fires twice with probability
    1 - (1-p1)(1-p2)..., so production is multiplied by one plus that.
    """
    miss = 1.0
    for _, effects in _active_effects(game_state):
        if "production_doubling_chance" in effects:
            miss *= 1.0 - effects["production_doubling_chance"]
    return 1.0 + (1.0 - miss)


def get_time_based_modifier(game_state, resource):
    """Timed production bonus: active for the first ``alignment_duration``
    seconds of every hour of play (errata E12: it used the wall clock, so
    output depended on the minute of the real hour)."""
    modifier = 1.0
    for _, effects in _active_effects(game_state):
        if "timed_production_bonus" in effects:
            alignment_duration = effects.get("alignment_duration", 300)
            if (int(game_state.total_play_time) % 3600) < alignment_duration:
                modifier *= effects["timed_production_bonus"]
    return modifier


def apply_special_resource_generation(game_state, elapsed_time):
    """Conversions that move production between resources.

    resource_conversion_rate (Junk Alchemy, 1.1 = 10%): each other basic
    resource gains that share of food production, without using up food.
    """
    for _, effects in _active_effects(game_state):
        if "resource_conversion_rate" in effects:
            share = effects["resource_conversion_rate"] - 1.0
            food_rate = (game_state.calculate_resource_generation_rate("food")
                         * game_state.calculate_global_multiplier("food"))
            if share > 0 and food_rate > 0:
                for res in BASIC_RESOURCES:
                    if res != "food":
                        game_state.resources[res] = game_state.resources.get(res, 0) + food_rate * share * elapsed_time


def generate_passive_prestige_points(game_state, elapsed_time):
    """passive_prestige_generation v: prestige points trickle in at v times the
    pending gain per second of play, without resetting anything (errata E15:
    the old formula, total earnings x v x dt, was absurd)."""
    rate = sum(effects.get("passive_prestige_generation", 0.0) for _, effects in _active_effects(game_state))
    if rate <= 0:
        return
    points = game_state.calculate_prestige_points() * rate * elapsed_time
    game_state.prestige_points = game_state.prestige_points + points
    game_state.total_prestige_points += points
