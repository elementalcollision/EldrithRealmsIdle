"""Eldrith Realms Idle — Textual TUI app."""
from __future__ import annotations

import os
import time
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Footer, Header, RichLog, Static, TabbedContent, TabPane

from game.constants import GAME_TITLE, RESOURCE_TYPES, PRESTIGE_REQUIREMENT_BASE
from game.game_state import GameState
from game.tui.format import short_num, format_seconds
from game.tui.modals import WelcomeBackModal
from game.tui.tabs import (
    AchievementsTab, BuildingsTab, GameTab, PrestigeTab, RacesTab, ResearchTab,
)

SAVE_PATH = str(Path.home() / ".eldrith_realms_idle" / "autosave.zsave")
TICK_SECONDS = 0.5
REFRESH_SECONDS = 0.5


class StatusBar(Static):
    """Top bar showing resources and progression."""

    def __init__(self, game_state: GameState, **kwargs):
        super().__init__(**kwargs)
        self.game_state = game_state

    def render_str(self) -> str:
        gs = self.game_state
        lines = []

        # Resource line(s)
        res_parts = []
        for r in RESOURCE_TYPES:
            if r == "prestige_points":
                continue
            amt = gs.resources.get(r, 0)
            rate = gs.calculate_resource_generation_rate(r) * gs.calculate_global_multiplier(r)
            if amt > 0 or rate > 0:
                rate_str = f" [dim](+{short_num(rate)}/s)[/dim]" if rate > 0 else ""
                res_parts.append(f"[bold]{r}[/bold]:{short_num(amt)}{rate_str}")
        lines.append(" │ ".join(res_parts) if res_parts else "(no resources yet)")

        # Progression line
        req = gs.get_prestige_requirement()
        prestige_pts = gs.calculate_prestige_points()
        twarp = ""
        if gs.time_warp_active:
            remaining = max(0, gs.time_warp_end_time - time.time())
            twarp = f" │ [yellow]⌛ Time Warp x{gs.get_time_warp_multiplier():.1f} ({format_seconds(remaining)} left)[/yellow]"
        elif gs.has_time_warp_unlocked():
            cd = gs.time_warp_cooldown_end - time.time()
            if cd > 0:
                twarp = f" │ Time Warp cooldown: {format_seconds(cd)}"
            else:
                twarp = " │ [green]Time Warp ready (t)[/green]"
        lines.append(
            f"Lv {gs.player_level} │ Total earnings: {short_num(gs.total_earnings)} / {short_num(req)} "
            f"│ Prestige #{gs.prestige_count} ({short_num(gs.prestige_points)} pts, +{prestige_pts} on prestige)"
            + twarp
        )
        return "\n".join(lines)

    def refresh_status(self) -> None:
        self.update(self.render_str())


class EldrithApp(App):
    """Main application."""

    CSS_PATH = "styles.tcss"
    TITLE = GAME_TITLE
    SUB_TITLE = "An eldritch idle realm"

    BINDINGS = [
        Binding("1", "show_tab('races')", "Races", show=True),
        Binding("2", "show_tab('buildings')", "Buildings", show=True),
        Binding("3", "show_tab('research')", "Research", show=True),
        Binding("4", "show_tab('prestige')", "Prestige", show=True),
        Binding("5", "show_tab('achievements')", "Achievements", show=True),
        Binding("b", "buy(1)", "Buy 1", show=True),
        Binding("B", "buy(10)", "Buy 10", show=False),
        Binding("M", "buy(-1)", "Buy Max", show=True),
        Binding("u", "upgrade(1)", "Upgrade", show=True),
        Binding("U", "upgrade(-1)", "Upgrade Max", show=False),
        Binding("p", "prestige", "Prestige", show=True),
        Binding("t", "time_warp", "Time Warp", show=True),
        Binding("s", "save", "Save", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    def __init__(self, save_path: str = SAVE_PATH):
        super().__init__()
        self.save_path = save_path
        self.game_state = GameState()
        if os.path.exists(self.save_path):
            self.game_state.load_game(self.save_path)
        self._last_tick = time.time()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        self.status = StatusBar(self.game_state, id="status-bar")
        yield self.status
        with TabbedContent(initial="races"):
            with TabPane("[1] Races", id="races"):
                yield RacesTab(self.game_state)
            with TabPane("[2] Buildings", id="buildings"):
                yield BuildingsTab(self.game_state)
            with TabPane("[3] Research", id="research"):
                yield ResearchTab(self.game_state)
            with TabPane("[4] Prestige", id="prestige"):
                yield PrestigeTab(self.game_state)
            with TabPane("[5] Achievements", id="achievements"):
                yield AchievementsTab(self.game_state)
        self.log_widget = RichLog(
            id="log", highlight=True, markup=True, wrap=True, max_lines=100,
        )
        self.log_widget.can_focus = False
        yield self.log_widget
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(TICK_SECONDS, self._tick)
        self.set_interval(REFRESH_SECONDS, self._refresh_ui)
        self._drain_notifications()
        self.status.refresh_status()
        self.log_widget.write(
            f"[bold cyan]{GAME_TITLE}[/bold cyan] — keys shown in footer; "
            "ctrl+q to save & quit."
        )
        # Surface offline progress, if a save was just loaded.
        summary = getattr(self.game_state, "pending_offline_summary", None)
        if summary:
            self.game_state.pending_offline_summary = None
            self.push_screen(WelcomeBackModal(summary))
        # Default focus to the active tab's DataTable so arrows move rows.
        self.call_after_refresh(self._focus_active_table)

    def _focus_active_table(self) -> None:
        try:
            self._current_tab().query_one("DataTable").focus()
        except Exception:
            pass

    # ---------------- Game loop ----------------
    def _tick(self) -> None:
        now = time.time()
        elapsed = now - self._last_tick
        self._last_tick = now
        self.game_state.update(elapsed)

    def _refresh_ui(self) -> None:
        self.status.refresh_status()
        self._current_tab().refresh_rows()
        self._drain_notifications()

    def _drain_notifications(self) -> None:
        for n in self.game_state.get_notifications(clear=True):
            kind = n.get("type", "info")
            color = {
                "achievement": "gold1",
                "unlock": "cyan",
                "error": "red",
                "save": "green",
                "info": "white",
            }.get(kind, "white")
            self.log_widget.write(f"[{color}]{n['text']}[/{color}]")

    # ---------------- Tab navigation ----------------
    def _tabbed(self) -> TabbedContent:
        return self.query_one(TabbedContent)

    def _current_tab(self) -> GameTab:
        active = self._tabbed().active
        pane = self.query_one(f"TabPane#{active}")
        return pane.query_one(GameTab)

    def action_show_tab(self, tab_id: str) -> None:
        self._tabbed().active = tab_id
        # Focus the DataTable so arrow keys move the cursor instead of
        # scrolling the log.
        try:
            self._current_tab().query_one("DataTable").focus()
        except Exception:
            pass

    # ---------------- Buy / upgrade ----------------
    def action_buy(self, count: int) -> None:
        tab = self._current_tab()
        key = tab.selected_key()
        if key is None:
            self.log_widget.write("[dim]Nothing selected.[/dim]")
            return
        ok = tab.buy(key, count)
        if not ok:
            self.log_widget.write("[red]Cannot afford or no effect.[/red]")
        self._refresh_ui()

    def action_upgrade(self, count: int) -> None:
        tab = self._current_tab()
        key = tab.selected_key()
        if key is None:
            self.log_widget.write("[dim]Nothing selected.[/dim]")
            return
        ok = tab.upgrade(key, count)
        if not ok:
            self.log_widget.write("[red]Cannot afford, at max level, or no effect.[/red]")
        self._refresh_ui()

    # ---------------- Prestige / time warp ----------------
    def action_prestige(self) -> None:
        gs = self.game_state
        gain = gs.calculate_prestige_points()
        if gain <= 0:
            self.log_widget.write(
                f"[yellow]Need {short_num(gs.get_prestige_requirement())} total earnings to prestige "
                f"(have {short_num(gs.total_earnings)}).[/yellow]"
            )
            return
        if gs.perform_prestige():
            self._refresh_ui()

    def action_time_warp(self) -> None:
        self.game_state.activate_time_warp()
        self._refresh_ui()

    # ---------------- Save / quit ----------------
    def action_save(self) -> None:
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        if self.game_state.save_game(self.save_path):
            self.log_widget.write(f"[green]Saved → {self.save_path}[/green]")

    def action_quit(self) -> None:
        self.action_save()
        self.exit()
