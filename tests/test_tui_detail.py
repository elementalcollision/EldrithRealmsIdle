"""Tests for the per-tab detail-panel rendering.

These don't need an active Textual app — the detail() methods are pure
functions of (game_state, key). We instantiate the tab with a stub for
the missing widget plumbing and call detail() directly.
"""
from __future__ import annotations

from game.game_state import GameState
from game.tui.tabs import (
    AchievementsTab, BuildingsTab, PrestigeTab, RacesTab, ResearchTab,
)


def _tab(cls):
    """Build a tab with a real GameState but no mounted widgets."""
    gs = GameState()
    # Bypass Textual mount; we only call detail()/rows().
    tab = cls.__new__(cls)
    tab.game_state = gs
    tab._table = None
    tab._detail = None
    return tab, gs


def test_races_detail_includes_name_description_bonuses():
    tab, _ = _tab(RacesTab)
    text = tab.detail("dwarf")
    assert "Dwarves" in text
    assert "stone" in text
    assert "Recruit cost" in text


def test_races_detail_includes_abilities():
    tab, _ = _tab(RacesTab)
    text = tab.detail("dwarf")
    assert "Mountain Heart" in text
    assert "locked" in text  # not yet unlocked at level 1


def test_races_detail_shows_next_level_preview_only_after_recruit():
    tab, gs = _tab(RacesTab)
    text_before = tab.detail("dwarf")
    assert "Next level" not in text_before
    gs.add_race("dwarf", 1)
    text_after = tab.detail("dwarf")
    assert "Next level" in text_after


def test_races_detail_returns_placeholder_for_missing_key():
    tab, _ = _tab(RacesTab)
    assert "nothing selected" in tab.detail("does_not_exist").lower()


def test_buildings_detail_lists_production():
    tab, gs = _tab(BuildingsTab)
    text = tab.detail("mine")
    assert "Mine" in text
    assert "stone" in text
    assert "Build cost" in text


def test_research_detail_shows_effect_preview():
    tab, gs = _tab(ResearchTab)
    text = tab.detail("efficient_mining")
    assert "Efficient Mining" in text


def test_prestige_detail_shows_effect():
    tab, _ = _tab(PrestigeTab)
    text = tab.detail("eternal_knowledge")
    assert "Eternal Knowledge" in text
    assert "Effect" in text
    assert "Next-level cost" in text


def test_achievement_detail_includes_status_and_reward():
    tab, _ = _tab(AchievementsTab)
    text = tab.detail("resource_milestones:gold_1")
    assert "Golden Beginnings" in text
    assert "Locked" in text
    assert "Reward" in text


def test_achievement_detail_handles_bad_key():
    tab, _ = _tab(AchievementsTab)
    assert "nothing selected" in tab.detail("invalid").lower()
