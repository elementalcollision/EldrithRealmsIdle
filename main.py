"""Eldrith Realms Idle — Textual TUI entry point."""
from game.tui.app import EldrithApp


def main() -> None:
    EldrithApp().run()


if __name__ == "__main__":
    main()
