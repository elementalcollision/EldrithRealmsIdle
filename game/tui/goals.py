"""Goals tab — a progress tracker showing what's coming next.

The point of an idle game is the next milestone. This tab surfaces:
  - the next race / building / research that's about to unlock,
  - progress toward the next prestige cycle,
  - the closest in-progress achievements,
  - per-race ability unlock progress for races you've recruited.

It's read-only; cursor lives elsewhere.
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static

from game.constants import (
    ACHIEVEMENTS, BUILDINGS, PRESTIGE_UPGRADES, RACES, RESEARCH, RESOURCE_TYPES,
)
from game.tui.format import format_seconds, short_num


# ---------- progress helpers ----------
def progress_bar(fraction: float, width: int = 12) -> str:
    fraction = max(0.0, min(1.0, fraction))
    filled = int(round(fraction * width))
    return "█" * filled + "░" * (width - filled)


def fmt_pct(fraction: float) -> str:
    return f"{int(round(max(0.0, min(1.0, fraction)) * 100))}%"


def earnings_for_level(level: int) -> int:
    """Inverse of the player_level formula in GameState.check_unlocks."""
    return max(0, (level - 1) * 1000)


def achievement_progress(gs, requirement: dict) -> tuple[float, str]:
    """Return (fraction in [0,1], short status string) for a requirement.

    Returns (0.0, "—") if the requirement isn't yet measurable here.
    """
    if not requirement:
        return 0.0, "—"
    req = requirement

    # Single-resource: {"gold": 1000}
    res_keys = [k for k in req if k in RESOURCE_TYPES]
    if len(res_keys) == 1 and len(req) == 1:
        r = res_keys[0]
        cur = gs.resources.get(r, 0)
        return min(cur / req[r], 1.0), f"{short_num(cur)}/{short_num(req[r])} {r}"

    if "race" in req and "count" in req:
        cur = gs.races.get(req["race"], {}).get("count", 0)
        return min(cur / req["count"], 1.0), f"{short_num(cur)}/{short_num(req['count'])} {req['race']}"

    if "all_races" in req:
        n = req["all_races"]
        counts = [d["count"] for d in gs.races.values() if d["unlocked"]]
        if not counts:
            return 0.0, "no races unlocked"
        m = min(counts)
        return min(m / n, 1.0), f"min count across races: {short_num(m)}/{short_num(n)}"

    if "any_building" in req:
        n = req["any_building"]
        counts = [d["count"] for d in gs.buildings.values() if d["unlocked"]]
        if not counts:
            return 0.0, "no buildings unlocked"
        m = max(counts)
        return min(m / n, 1.0), f"any building: {short_num(m)}/{short_num(n)}"

    if "any_building_level" in req:
        n = req["any_building_level"]
        levels = [d["level"] for d in gs.buildings.values() if d["unlocked"] and d["count"] > 0]
        if not levels:
            return 0.0, "no buildings yet"
        m = max(levels)
        return min(m / n, 1.0), f"highest building lv {m}/{n}"

    if "building" in req and "count" in req:
        cur = gs.buildings.get(req["building"], {}).get("count", 0)
        return min(cur / req["count"], 1.0), f"{cur}/{req['count']} {req['building']}"

    if "all_buildings" in req:
        n = req["all_buildings"]
        levels = [d["level"] for d in gs.buildings.values() if d["unlocked"]]
        if not levels:
            return 0.0, "no buildings unlocked"
        m = min(levels)
        return min(m / n, 1.0), f"all buildings lv {m}/{n}"

    if "prestige_count" in req:
        return min(gs.prestige_count / req["prestige_count"], 1.0), \
               f"{gs.prestige_count}/{req['prestige_count']} prestiges"

    if "play_time" in req:
        return min(gs.total_play_time / req["play_time"], 1.0), \
               f"{format_seconds(gs.total_play_time)}/{format_seconds(req['play_time'])}"

    if "player_level" in req and len(req) == 1:
        return min(gs.player_level / req["player_level"], 1.0), \
               f"lv {gs.player_level}/{req['player_level']}"

    if "race_skill" in req:
        race_id = req["race_skill"]
        skills = gs.races.get(race_id, {}).get("skills", {})
        if "resource" in req and "amount" in req:
            cur = skills.get(req["resource"], 0)
            return min(cur / req["amount"], 1.0), \
                   f"{short_num(cur)}/{short_num(req['amount'])} {req['resource']} via {race_id}"
        if "all_resources" in req and skills:
            n = req["all_resources"]
            m = min(skills.values())
            return min(m / n, 1.0), f"{short_num(m)}/{short_num(n)} all-res via {race_id}"

    return 0.0, "—"


# ---------- the tab ----------
class GoalsTab(Vertical):
    """Read-only goals tracker. Refreshed by the app's UI tick."""

    def __init__(self, game_state, **kwargs):
        super().__init__(**kwargs)
        self.game_state = game_state
        self._panel = None  # type: ignore[assignment]

    def compose(self) -> ComposeResult:
        yield Static(
            "[italic dim]Closest milestones — what's about to unlock and how close you are.[/italic dim]",
            classes="tab-help",
        )
        with VerticalScroll(id="goals-scroll"):
            # Pre-render so the widget never has empty content during mount.
            initial = self._build_text() if self.game_state else ""
            yield Static(initial, id="goals-content", markup=True)

    def on_mount(self) -> None:
        self._panel = self.query_one("#goals-content", Static)

    # Stubs so the app can treat this like a GameTab without crashing.
    def refresh_rows(self) -> None:
        self.refresh_goals()

    def refresh_detail(self) -> None:  # noqa: D401
        pass

    def selected_key(self):  # noqa: D401
        return None

    def buy(self, key, count):
        return False

    def upgrade(self, key, count):
        return False

    # ---------- rendering ----------
    def refresh_goals(self) -> None:
        if self._panel is None:
            return
        self._panel.update(self._build_text())

    def _build_text(self) -> str:
        gs = self.game_state
        sections: list[str] = []

        # ---- Next unlocks ----
        unlock_lines: list[tuple[float, str]] = []
        for race_id, info in RACES.items():
            data = gs.races.get(race_id, {})
            if data.get("unlocked"):
                continue
            need_lv = info["unlock_level"]
            need_prestige = info.get("requires_prestige", 0)
            line = self._unlock_line(
                kind="Race", name=info["name"], need_lv=need_lv,
                need_prestige=need_prestige,
            )
            if line is not None:
                unlock_lines.append(line)

        for b_id, info in BUILDINGS.items():
            data = gs.buildings.get(b_id, {})
            if data.get("unlocked"):
                continue
            line = self._unlock_line(
                kind="Building", name=info["name"], need_lv=info["unlock_level"],
                need_prestige=info.get("requires_prestige", 0),
            )
            if line is not None:
                unlock_lines.append(line)

        for r_id, info in RESEARCH.items():
            data = gs.research.get(r_id, {})
            if data.get("unlocked"):
                continue
            line = self._unlock_line(
                kind="Research", name=info["name"], need_lv=info["unlock_level"],
                need_prestige=info.get("requires_prestige", 0),
            )
            if line is not None:
                unlock_lines.append(line)

        # Sort by progress descending; show closest 8.
        unlock_lines.sort(key=lambda kv: -kv[0])
        if unlock_lines:
            sections.append("[bold cyan]Next Unlocks[/bold cyan]")
            sections.extend(line for _, line in unlock_lines[:8])
        else:
            sections.append("[bold cyan]Next Unlocks[/bold cyan]\n  [dim]Everything unlocked at this prestige tier![/dim]")

        # ---- Prestige progress ----
        req = gs.get_prestige_requirement()
        frac = min(gs.total_earnings / req, 1.0) if req > 0 else 0.0
        gain = gs.calculate_prestige_points()
        sections.append("")
        sections.append("[bold magenta]Prestige Cycle[/bold magenta]")
        sections.append(
            f"  {progress_bar(frac)} {fmt_pct(frac)}  "
            f"{short_num(gs.total_earnings)}/{short_num(req)} earnings  "
            f"→ +{gain} prestige pts"
        )

        # ---- Race ability progress for recruited races ----
        ability_lines: list[tuple[float, str]] = []
        for race_id, info in RACES.items():
            data = gs.races.get(race_id, {})
            if not data.get("unlocked") or data.get("count", 0) == 0:
                continue
            for ab_id, ab in (info.get("special_abilities") or {}).items():
                state = data.get("abilities", {}).get(ab_id, {})
                if state.get("unlocked"):
                    continue
                ureq = ab.get("unlock_requirements", {})
                need_lv = ureq.get("race_level", 1)
                need_prestige = ureq.get("prestige_level", 0)
                lv_frac = min(data["level"] / need_lv, 1.0) if need_lv else 1.0
                prestige_ok = gs.prestige_count >= need_prestige
                # Use level fraction as the headline progress.
                frac = lv_frac if prestige_ok else min(lv_frac, 0.99)
                gate = "" if prestige_ok else f"  [yellow](needs prestige {need_prestige})[/yellow]"
                ability_lines.append((
                    frac,
                    f"  {progress_bar(frac)} {fmt_pct(frac)}  "
                    f"[bold]{ab['name']}[/bold] ({info['name']})  "
                    f"lv {data['level']}/{need_lv}{gate}",
                ))
        ability_lines.sort(key=lambda kv: -kv[0])
        if ability_lines:
            sections.append("")
            sections.append("[bold yellow]Race Abilities In Progress[/bold yellow]")
            sections.extend(line for _, line in ability_lines[:6])

        # ---- Achievements in progress ----
        ach_lines: list[tuple[float, str]] = []
        for cat, milestones in ACHIEVEMENTS.items():
            for m in milestones:
                if gs.achievements.get(cat, {}).get(m["id"]):
                    continue
                frac, status = achievement_progress(gs, m.get("requirement", {}))
                if frac <= 0:
                    continue
                ach_lines.append((
                    frac,
                    f"  {progress_bar(frac)} {fmt_pct(frac)}  "
                    f"[bold]{m['name']}[/bold]  [dim]{status}[/dim]",
                ))
        ach_lines.sort(key=lambda kv: -kv[0])
        if ach_lines:
            sections.append("")
            sections.append("[bold green]Achievements In Progress[/bold green]")
            sections.extend(line for _, line in ach_lines[:8])

        return "\n".join(sections)

    def _unlock_line(self, *, kind: str, name: str, need_lv: int,
                      need_prestige: int) -> tuple[float, str] | None:
        gs = self.game_state
        cur_lv = gs.player_level
        cur_earn = gs.total_earnings
        need_earn = earnings_for_level(need_lv)
        prestige_ok = gs.prestige_count >= need_prestige

        if not prestige_ok:
            # Show stub but very low priority.
            return (
                -1.0,
                f"  [dim]░░░░░░░░░░░░  0%  [bold]{kind}: {name}[/bold]  "
                f"requires prestige {need_prestige}[/dim]",
            )

        if need_earn <= 0:
            frac = 1.0
        else:
            frac = min(cur_earn / need_earn, 1.0)

        eta_chunk = ""
        # Try to estimate ETA from current gold rate.
        rate = gs.calculate_resource_generation_rate("gold") * gs.calculate_global_multiplier("gold")
        deficit = max(0.0, need_earn - cur_earn)
        if rate > 0 and deficit > 0:
            eta_chunk = f"  ETA ≈ {format_seconds(deficit / rate)}"

        return (
            frac,
            f"  {progress_bar(frac)} {fmt_pct(frac)}  "
            f"[bold]{kind}: {name}[/bold]  "
            f"lv {need_lv} ({short_num(cur_earn)}/{short_num(need_earn)} earnings){eta_chunk}",
        )
