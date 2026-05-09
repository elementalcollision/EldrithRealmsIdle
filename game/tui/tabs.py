"""Tab widgets for each section of the game."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Static

from game.constants import (
    RACES, BUILDINGS, RESEARCH, PRESTIGE_UPGRADES, ACHIEVEMENTS,
    PRESTIGE_REQUIREMENT_BASE,
)
from game.tui.format import short_num, format_cost, format_rate


class GameTab(Vertical):
    """Base for tabs backed by a DataTable of game items.

    Subclasses fill ``columns`` and implement ``rows()``, ``buy()``, ``upgrade()``.
    Returning False from buy/upgrade signals "nothing happened".
    """

    columns: tuple[str, ...] = ()
    help_text: str = ""

    def __init__(self, game_state, **kwargs):
        super().__init__(**kwargs)
        self.game_state = game_state
        self._table: DataTable | None = None

    def compose(self) -> ComposeResult:
        if self.help_text:
            yield Static(self.help_text, id="tab-help")
        yield DataTable(cursor_type="row", zebra_stripes=True)

    def on_mount(self) -> None:
        self._table = self.query_one(DataTable)
        for col in self.columns:
            self._table.add_column(col, key=col)
        self.refresh_rows()

    # --- subclass hooks ---
    def rows(self) -> list[tuple]:
        """Return ``[(row_key, *cells), ...]``."""
        return []

    def buy(self, key: str, count: int) -> bool:
        return False

    def upgrade(self, key: str, count: int) -> bool:
        return False

    # --- helpers ---
    def selected_key(self) -> str | None:
        if self._table is None or self._table.row_count == 0:
            return None
        try:
            row_key, _ = self._table.coordinate_to_cell_key((self._table.cursor_row, 0))
            return row_key.value
        except Exception:
            return None

    def refresh_rows(self) -> None:
        if self._table is None:
            return
        cur = self._table.cursor_row
        self._table.clear()
        for row in self.rows():
            key, *cells = row
            self._table.add_row(*cells, key=key)
        if self._table.row_count > 0:
            self._table.move_cursor(row=min(cur, self._table.row_count - 1))


# ---------------- Races ----------------
class RacesTab(GameTab):
    columns = ("Race", "Count", "Lv", "Cost (Buy)", "Upgrade Cost")
    help_text = "(b) buy 1   (B) buy 10   (M) buy max   (u) upgrade   (U) upgrade max"

    def rows(self):
        gs = self.game_state
        out = []
        for race_id, info in RACES.items():
            data = gs.races[race_id]
            if not data["unlocked"]:
                continue
            cost = gs.get_race_purchase_cost(race_id, 1)
            up = gs.get_race_upgrade_cost(race_id, 1) if data["count"] > 0 else None
            out.append((
                race_id,
                info["name"],
                short_num(data["count"]),
                str(data["level"]),
                format_cost(cost, gs.can_afford(cost)),
                format_cost(up, gs.can_afford(up)) if up else "-",
            ))
        return out

    def buy(self, key, count):
        gs = self.game_state
        if count == -1:
            base = gs.get_race_purchase_cost(key, 1)
            count = gs.calculate_max_affordable(base)
            if count <= 0:
                return False
        cost = gs.get_race_purchase_cost(key, count)
        if not gs.can_afford(cost):
            return False
        gs.spend_resources(cost)
        return gs.add_race(key, count)

    def upgrade(self, key, count):
        gs = self.game_state
        if count == -1:
            count = gs.calculate_max_affordable_levels(
                key, "get_race_upgrade_cost",
                gs.races[key]["level"],
                int(RACES[key].get("max_level", 999)),
            )
            if count <= 0:
                return False
        cost = gs.get_race_upgrade_cost(key, count)
        if not gs.can_afford(cost):
            return False
        gs.spend_resources(cost)
        return gs.upgrade_race(key, count)


# ---------------- Buildings ----------------
class BuildingsTab(GameTab):
    columns = ("Building", "Count", "Lv", "Cost (Buy)", "Upgrade Cost")
    help_text = "(b) buy 1   (B) buy 10   (M) buy max   (u) upgrade   (U) upgrade max"

    def rows(self):
        gs = self.game_state
        out = []
        for b_id, info in BUILDINGS.items():
            data = gs.buildings[b_id]
            if not data["unlocked"]:
                continue
            cost = gs.get_building_purchase_cost(b_id, 1)
            at_max = data["level"] >= info["max_level"]
            up = gs.get_building_upgrade_cost(b_id, 1) if data["count"] > 0 and not at_max else None
            out.append((
                b_id,
                info["name"],
                short_num(data["count"]),
                f"{data['level']}/{info['max_level']}",
                format_cost(cost, gs.can_afford(cost)),
                "MAX" if at_max else (format_cost(up, gs.can_afford(up)) if up else "-"),
            ))
        return out

    def buy(self, key, count):
        gs = self.game_state
        if count == -1:
            base = gs.get_building_purchase_cost(key, 1)
            count = gs.calculate_max_affordable(base)
            if count <= 0:
                return False
        cost = gs.get_building_purchase_cost(key, count)
        if not gs.can_afford(cost):
            return False
        gs.spend_resources(cost)
        return gs.add_building(key, count)

    def upgrade(self, key, count):
        gs = self.game_state
        if count == -1:
            count = gs.calculate_max_affordable_levels(
                key, "get_building_upgrade_cost",
                gs.buildings[key]["level"],
                BUILDINGS[key]["max_level"],
            )
            if count <= 0:
                return False
        cost = gs.get_building_upgrade_cost(key, count)
        if not gs.can_afford(cost):
            return False
        gs.spend_resources(cost)
        return gs.upgrade_building(key, count)


# ---------------- Research ----------------
class ResearchTab(GameTab):
    columns = ("Research", "Lv", "Cost", "Description")
    help_text = "(u) research one level"

    def rows(self):
        gs = self.game_state
        out = []
        for r_id, info in RESEARCH.items():
            data = gs.research[r_id]
            if not data["unlocked"]:
                continue
            at_max = data["level"] >= info["max_level"]
            cost = gs.get_research_cost(r_id, 1) if not at_max else None
            out.append((
                r_id,
                info["name"],
                f"{data['level']}/{info['max_level']}",
                "MAX" if at_max else format_cost(cost, gs.can_afford(cost)),
                info["description"][:50],
            ))
        return out

    def buy(self, key, count):
        return self.upgrade(key, count)

    def upgrade(self, key, count):
        gs = self.game_state
        # Research increments one level per call; ignore count > 1 for now.
        cost = gs.get_research_cost(key, 1)
        if not gs.can_afford(cost):
            return False
        gs.spend_resources(cost)
        return gs.research_technology(key)


# ---------------- Prestige ----------------
class PrestigeTab(GameTab):
    columns = ("Upgrade", "Lv", "Cost", "Description")
    help_text = "(u) purchase upgrade   (p) perform prestige   (t) activate Time Warp"

    def rows(self):
        gs = self.game_state
        out = []
        for u_id, info in PRESTIGE_UPGRADES.items():
            data = gs.prestige_upgrades[u_id]
            at_max = data["level"] >= info["max_level"]
            cost = gs.get_prestige_upgrade_cost(u_id, 1) if not at_max else None
            out.append((
                u_id,
                info["name"],
                f"{data['level']}/{info['max_level']}",
                "MAX" if at_max else format_cost(cost, gs.can_afford(cost)),
                info["description"][:60],
            ))
        return out

    def buy(self, key, count):
        return self.upgrade(key, count)

    def upgrade(self, key, count):
        gs = self.game_state
        cost = gs.get_prestige_upgrade_cost(key, 1)
        if not gs.can_afford(cost):
            return False
        gs.spend_resources(cost)
        return gs.purchase_prestige_upgrade(key)


# ---------------- Achievements ----------------
class AchievementsTab(GameTab):
    columns = ("Category", "Achievement", "Status", "Description")
    help_text = "Read-only. Achievements unlock automatically as you meet requirements."

    def rows(self):
        gs = self.game_state
        out = []
        for cat, milestones in ACHIEVEMENTS.items():
            cat_label = cat.replace("_", " ").title()
            for m in milestones:
                done = gs.achievements.get(cat, {}).get(m["id"], False)
                out.append((
                    f"{cat}:{m['id']}",
                    cat_label,
                    m["name"],
                    "[green]✓[/green]" if done else "[dim]·[/dim]",
                    m["description"][:55],
                ))
        return out

    def buy(self, key, count):
        return False

    def upgrade(self, key, count):
        return False
