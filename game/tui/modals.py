"""Modal screens for the Eldrith TUI."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from game.tui.format import format_seconds, short_num


class WelcomeBackModal(ModalScreen[None]):
    """Shown on startup when a save loaded with non-trivial offline time."""

    BINDINGS = [
        Binding("enter", "dismiss", "Dismiss", show=True),
        Binding("escape", "dismiss", "Dismiss", show=False),
    ]

    DEFAULT_CSS = """
    WelcomeBackModal {
        align: center middle;
    }
    WelcomeBackModal > Vertical {
        background: $panel;
        border: double $primary;
        padding: 1 2;
        width: 60;
        height: auto;
        max-height: 24;
    }
    WelcomeBackModal #title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 1;
    }
    WelcomeBackModal #body {
        margin-bottom: 1;
    }
    WelcomeBackModal Button {
        width: 100%;
    }
    """

    def __init__(self, summary: dict):
        super().__init__()
        self.summary = summary

    def compose(self) -> ComposeResult:
        elapsed = self.summary.get("elapsed_seconds", 0)
        rate = self.summary.get("rate", 0)
        gained = self.summary.get("gained", {})

        gained_lines = "\n".join(
            f"  • {res}: [green]+{short_num(amount)}[/green]"
            for res, amount in sorted(gained.items(), key=lambda kv: -kv[1])
            if amount > 0
        ) or "  (nothing accumulated)"

        body = (
            f"You were away for [bold]{format_seconds(elapsed)}[/bold] "
            f"at [bold]{int(rate*100)}%[/bold] offline rate.\n\n"
            f"While you were gone you gained:\n{gained_lines}"
        )

        with Vertical():
            yield Static("[Welcome Back]", id="title")
            yield Static(body, id="body", markup=True)
            yield Button("Continue (Enter)", id="ok", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def action_dismiss(self) -> None:  # type: ignore[override]
        self.dismiss(None)
