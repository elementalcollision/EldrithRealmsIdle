"""Tab widgets for each section of the game.

Each tab is a horizontal split: a DataTable on the left for selection,
and a markup-rich Static on the right showing the selected row's full
details (description, current bonuses, next-level preview, etc.).
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import DataTable, Static

from game.constants import (
    RACES, BUILDINGS, RESEARCH, PRESTIGE_UPGRADES, ACHIEVEMENTS,
)
from game.tui.format import short_num, format_cost


# ---------------- Base ----------------
class GameTab(Vertical):
    """Base for tabs backed by a DataTable + detail panel.

    Subclasses fill ``columns`` and implement ``rows()``, ``detail()``,
    optionally ``buy()`` and ``upgrade()``.
    """

    columns: tuple[str, ...] = ()
    help_text: str = ""
    empty_detail: str = "[dim](nothing selected)[/dim]"

    def __init__(self, game_state, **kwargs):
        super().__init__(**kwargs)
        self.game_state = game_state
        self._table: DataTable | None = None
        self._detail: Static | None = None

    def compose(self) -> ComposeResult:
        if self.help_text:
            yield Static(self.help_text, classes="tab-help")
        with Horizontal(classes="tab-body"):
            yield DataTable(cursor_type="row", zebra_stripes=True, classes="tab-table")
            with VerticalScroll(classes="tab-detail-scroll"):
                yield Static("", id=f"detail-{type(self).__name__}", classes="tab-detail", markup=True)

    def on_mount(self) -> None:
        self._table = self.query_one(DataTable)
        self._detail = self.query_one(".tab-detail", Static)
        for col in self.columns:
            self._table.add_column(col, key=col)
        self.refresh_rows()
        self.refresh_detail()

    # --- subclass hooks ---
    def rows(self) -> list[tuple]:
        """Return ``[(row_key, *cells), ...]``."""
        return []

    def detail(self, key: str) -> str:
        """Return a markup string describing the row identified by ``key``."""
        return self.empty_detail

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
        # Detail panel costs / next-level previews depend on resources, so
        # refresh it on every row tick too — not just on cursor changes.
        self.refresh_detail()

    def refresh_detail(self) -> None:
        if self._detail is None:
            return
        key = self.selected_key()
        text = self.detail(key) if key else self.empty_detail
        self._detail.update(text)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        # Cursor moved → update the side panel.
        self.refresh_detail()


# ---------------- Detail-rendering helpers ----------------
def _render_cost(label: str, cost: dict | None, can_afford: bool) -> str:
    if not cost:
        return f"[bold]{label}:[/bold] -"
    return f"[bold]{label}:[/bold] {format_cost(cost, can_afford)}"


def _render_kv_block(title: str, entries: dict) -> str:
    if not entries:
        return ""
    lines = [f"[bold]{title}[/bold]"]
    for k, v in entries.items():
        lines.append(f"  {k}: {v}")
    return "\n".join(lines)


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

    def detail(self, key):
        gs = self.game_state
        info = RACES.get(key)
        data = gs.races.get(key)
        if info is None or data is None:
            return self.empty_detail

        lines = [
            f"[bold cyan]{info['name']}[/bold cyan]  [dim](lv {data['level']}, ×{short_num(data['count'])})[/dim]",
            "",
            info["description"],
        ]

        # Resource bonuses (per-resource production multipliers).
        if "resource_bonuses" in info:
            bonuses = ", ".join(
                f"{res} ×{val:.2f}" for res, val in info["resource_bonuses"].items()
            )
            lines += ["", f"[bold]Bonuses:[/bold] {bonuses}"]

        # Special abilities and their unlock state.
        abilities = info.get("special_abilities") or {}
        if abilities:
            lines += ["", "[bold]Abilities[/bold]"]
            for ab_id, ab in abilities.items():
                state = data.get("abilities", {}).get(ab_id, {})
                if state.get("unlocked"):
                    status = "[green]unlocked[/green]"
                else:
                    req = ab.get("unlock_requirements", {})
                    parts = []
                    if "race_level" in req:
                        parts.append(f"lv {req['race_level']}")
                    if "prestige_level" in req and req["prestige_level"] > 0:
                        parts.append(f"prestige {req['prestige_level']}")
                    if "resources" in req:
                        parts.append(", ".join(f"{short_num(v)} {k}" for k, v in req["resources"].items()))
                    status = "[dim]locked[/dim]" + (f" ({'; '.join(parts)})" if parts else "")
                lines.append(f"  • [bold]{ab['name']}[/bold] — {status}")
                lines.append(f"    {ab['description']}")

        # Next-level preview (only meaningful with at least one of the race).
        if data["count"] > 0:
            preview = gs.get_race_upgrade_benefits(key)
            if preview:
                lines += [
                    "",
                    f"[bold]Next level → {preview['next_level']}[/bold]",
                    _render_cost("Upgrade cost", preview["upgrade_cost"],
                                 gs.can_afford(preview["upgrade_cost"])),
                ]
                cur_b = preview.get("current_benefits") or {}
                next_b = preview.get("next_level_benefits") or {}
                for name in dict.fromkeys(list(cur_b) + list(next_b)):
                    lines.append(f"  {name}: {cur_b.get(name, '-')} → {next_b.get(name, '-')}")

        # Purchase preview if not yet owned.
        cost = gs.get_race_purchase_cost(key, 1)
        lines += [
            "",
            _render_cost("Recruit cost", cost, gs.can_afford(cost)),
        ]
        return "\n".join(lines)

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

    def detail(self, key):
        gs = self.game_state
        info = BUILDINGS.get(key)
        data = gs.buildings.get(key)
        if info is None or data is None:
            return self.empty_detail

        lines = [
            f"[bold cyan]{info['name']}[/bold cyan]  [dim](lv {data['level']}/{info['max_level']}, ×{short_num(data['count'])})[/dim]",
            "",
            info["description"],
        ]

        # Production / multiplier description
        prod = info.get("resource_production") or {}
        if prod:
            base_lines = [f"{res}: +{short_num(amount)}/s/building" for res, amount in prod.items()]
            lines += ["", "[bold]Base production[/bold]"] + [f"  {b}" for b in base_lines]

        gmult = info.get("global_multipliers") or {}
        if gmult:
            mults = ", ".join(f"{k} ×{v:.2f}" for k, v in gmult.items())
            lines += ["", f"[bold]Global multiplier:[/bold] {mults}"]

        if data["count"] > 0:
            preview = gs.get_building_upgrade_benefits(key)
            if preview:
                at_max = data["level"] >= info["max_level"]
                lines += [
                    "",
                    f"[bold]Next level → {preview['next_level']}[/bold]"
                    if not at_max else "[bold]At max level[/bold]",
                ]
                if not at_max:
                    lines.append(_render_cost(
                        "Upgrade cost", preview["upgrade_cost"],
                        gs.can_afford(preview["upgrade_cost"]),
                    ))
                cur_b = preview.get("current_benefits") or {}
                next_b = preview.get("next_level_benefits") or {}
                for name in dict.fromkeys(list(cur_b) + list(next_b)):
                    lines.append(f"  {name}: {cur_b.get(name, '-')} → {next_b.get(name, '-')}")

        cost = gs.get_building_purchase_cost(key, 1)
        lines += [
            "",
            _render_cost("Build cost", cost, gs.can_afford(cost)),
        ]
        return "\n".join(lines)

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
    columns = ("Research", "Lv", "Cost")
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
            ))
        return out

    def detail(self, key):
        gs = self.game_state
        info = RESEARCH.get(key)
        data = gs.research.get(key)
        if info is None or data is None:
            return self.empty_detail

        lines = [
            f"[bold cyan]{info['name']}[/bold cyan]  [dim](lv {data['level']}/{info['max_level']})[/dim]",
            "",
            info["description"],
        ]

        preview = gs.get_research_upgrade_benefits(key)
        if preview:
            at_max = data["level"] >= info["max_level"]
            lines += ["", "[bold]At max level[/bold]" if at_max else f"[bold]Next level → {preview['next_level']}[/bold]"]
            if not at_max:
                lines.append(_render_cost(
                    "Cost", preview["research_cost"],
                    gs.can_afford(preview["research_cost"]),
                ))
            cur_e = preview.get("current_effects") or {}
            next_e = preview.get("next_level_effects") or {}
            for name in dict.fromkeys(list(cur_e) + list(next_e)):
                lines.append(f"  {name}: {cur_e.get(name, '-')} → {next_e.get(name, '-')}")
        return "\n".join(lines)

    def buy(self, key, count):
        return self.upgrade(key, count)

    def upgrade(self, key, count):
        gs = self.game_state
        cost = gs.get_research_cost(key, 1)
        if not gs.can_afford(cost):
            return False
        gs.spend_resources(cost)
        return gs.research_technology(key)


# ---------------- Prestige ----------------
class PrestigeTab(GameTab):
    columns = ("Upgrade", "Lv", "Cost")
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
            ))
        return out

    def detail(self, key):
        gs = self.game_state
        info = PRESTIGE_UPGRADES.get(key)
        data = gs.prestige_upgrades.get(key)
        if info is None or data is None:
            return self.empty_detail

        at_max = data["level"] >= info["max_level"]
        lines = [
            f"[bold magenta]{info['name']}[/bold magenta]  [dim](lv {data['level']}/{info['max_level']})[/dim]",
            "",
            info["description"],
        ]

        # Effect preview (one-level lift).
        eff = info.get("effect", {})
        if eff:
            current_text = ", ".join(
                f"{k}: ×{v ** data['level']:.2f}" if isinstance(v, (int, float)) and v > 1 and data["level"] > 0
                else f"{k}: {v * max(data['level'], 1)}"
                for k, v in eff.items()
            )
            lines += ["", f"[bold]Effect:[/bold] {current_text}"]

        if not at_max:
            cost = gs.get_prestige_upgrade_cost(key, 1)
            lines += ["", _render_cost("Next-level cost", cost, gs.can_afford(cost))]
        else:
            lines += ["", "[bold]At max level[/bold]"]
        return "\n".join(lines)

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
    columns = ("Category", "Achievement", "Status")
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
                    "[green]✓ done[/green]" if done else "[dim]·[/dim]",
                ))
        return out

    def detail(self, key):
        if key is None or ":" not in key:
            return self.empty_detail
        cat, m_id = key.split(":", 1)
        for m in ACHIEVEMENTS.get(cat, []):
            if m["id"] == m_id:
                gs = self.game_state
                done = gs.achievements.get(cat, {}).get(m_id, False)
                status = "[green]Unlocked[/green]" if done else "[dim]Locked[/dim]"
                lines = [
                    f"[bold gold1]{m['name']}[/bold gold1]  ({status})",
                    "",
                    m["description"],
                ]
                # Reward block.
                if m.get("reward"):
                    rewards = ", ".join(f"{k}={v}" for k, v in m["reward"].items())
                    lines += ["", f"[bold]Reward:[/bold] {rewards}"]
                # Requirement (terse).
                if m.get("requirement"):
                    parts = []
                    for k, v in m["requirement"].items():
                        parts.append(f"{k}={short_num(v) if isinstance(v, (int, float)) else v}")
                    lines += ["", f"[bold]Requirement:[/bold] {', '.join(parts)}"]
                return "\n".join(lines)
        return self.empty_detail
