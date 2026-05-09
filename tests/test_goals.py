"""Tests for the Goals progress-tracker logic."""
from __future__ import annotations

from game.game_state import GameState
from game.tui.goals import (
    GoalsTab, achievement_progress, earnings_for_level, fmt_pct, progress_bar,
)


def _tab():
    gs = GameState()
    tab = GoalsTab.__new__(GoalsTab)
    tab.game_state = gs
    tab._content = None
    return tab, gs


# ---------- progress_bar ----------
def test_progress_bar_clamps_and_fills():
    assert progress_bar(0.0) == "░" * 12
    assert progress_bar(1.0) == "█" * 12
    assert progress_bar(0.5) == "█" * 6 + "░" * 6
    assert progress_bar(-0.3) == "░" * 12  # clamped
    assert progress_bar(1.5) == "█" * 12


def test_fmt_pct():
    assert fmt_pct(0.0) == "0%"
    assert fmt_pct(0.5) == "50%"
    assert fmt_pct(1.0) == "100%"
    assert fmt_pct(2.0) == "100%"  # clamped


def test_earnings_for_level():
    assert earnings_for_level(1) == 0
    assert earnings_for_level(2) == 1000
    assert earnings_for_level(5) == 4000


# ---------- achievement_progress ----------
def test_achievement_progress_resource_milestone():
    _, gs = _tab()
    gs.resources["gold"] = 500
    frac, status = achievement_progress(gs, {"gold": 1000})
    assert frac == 0.5
    assert "gold" in status


def test_achievement_progress_race_count():
    _, gs = _tab()
    gs.races["dwarf"]["count"] = 25
    frac, _ = achievement_progress(gs, {"race": "dwarf", "count": 100})
    assert frac == 0.25


def test_achievement_progress_prestige_count():
    _, gs = _tab()
    gs.prestige_count = 2
    frac, _ = achievement_progress(gs, {"prestige_count": 5})
    assert frac == 0.4


def test_achievement_progress_unknown_returns_zero():
    _, gs = _tab()
    frac, status = achievement_progress(gs, {"completely_made_up_key": 1})
    assert frac == 0.0
    assert status == "—"


def test_achievement_progress_clamps_at_one():
    _, gs = _tab()
    gs.resources["gold"] = 999_999
    frac, _ = achievement_progress(gs, {"gold": 1000})
    assert frac == 1.0


# ---------- end-to-end render ----------
def test_render_includes_unlock_section():
    tab, _ = _tab()
    text = tab._build_text()
    assert "Next Unlocks" in text
    # At level 1 with no progression, several races (goblin, troll, fae...) are locked.
    assert "Goblins" in text or "Trolls" in text


def test_render_includes_prestige_progress():
    tab, _ = _tab()
    text = tab._build_text()
    assert "Prestige Cycle" in text
    assert "0%" in text  # at start, prestige progress is 0


def test_render_shows_achievements_in_progress_when_partial():
    tab, gs = _tab()
    gs.resources["gold"] = 500  # halfway to gold_1
    text = tab._build_text()
    assert "Golden Beginnings" in text


def test_render_shows_race_abilities_only_for_recruited_races():
    tab, gs = _tab()
    text_before = tab._build_text()
    assert "Race Abilities" not in text_before  # no races recruited yet
    gs.add_race("dwarf", 1)
    text_after = tab._build_text()
    assert "Race Abilities" in text_after
    assert "Mountain Heart" in text_after
