# Eldrith Realms Idle

A keyboard-driven, terminal-based idle RPG in the spirit of *Your Chronicle*.
Build a fantasy realm of dwarves, elves, and stranger things; gather
resources; research arcane technologies; prestige to grow stronger across
cycles.

Built with [Textual](https://textual.textualize.io/) — runs anywhere there's a
terminal.

## Install

Requires Python 3.10–3.13.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

The game autosaves to `~/.eldrith_realms_idle/autosave.zsave` on quit and
loads it on startup. Offline progress accrues at a reduced rate while the
game is closed.

## Controls

All keyboard. The footer shows the live binding list.

| Key        | Action                                        |
|------------|-----------------------------------------------|
| `1`–`5`    | Switch between Races / Buildings / Research / Prestige / Achievements |
| `↑` `↓`    | Move selection in the current tab             |
| `b`        | Buy 1 of the selected row                     |
| `B`        | Buy 10                                        |
| `M`        | Buy max affordable                            |
| `u`        | Upgrade selected (1 level)                    |
| `U`        | Upgrade as many levels as you can afford      |
| `p`        | Prestige (resets progression for prestige points) |
| `t`        | Activate Time Warp (once unlocked via prestige) |
| `s`        | Save now                                      |
| `ctrl+q`   | Save and quit                                 |

## Game Mechanics

- **Races** produce resources passively; level them up for bigger bonuses.
- **Buildings** boost production directly or via global multipliers.
- **Research** spends ancient knowledge for permanent multipliers.
- **Prestige** resets your run in exchange for prestige points and permanent
  bonuses. Unlocks higher-tier races, buildings, and research.
- **Achievements** trigger automatically and grant passive bonuses.

## Project structure

```
main.py                       # Textual app entry point
game/
  game_state.py               # Pure game logic — no UI dependency
  constants.py                # Tunables + re-exports of data tables
  constants_data/             # Per-domain data tables
    races_data.py
    buildings_data.py
    research_data.py
    prestige_upgrades_data.py
    achievements_data.py
  logic/                      # Achievements + race-ability rules
  tui/                        # Textual UI layer
    app.py                    # App + StatusBar + bindings
    tabs.py                   # One widget per tab
    format.py                 # Number/cost formatting helpers
    styles.tcss               # Textual CSS
tests/
  test_game_state.py          # Headless pytest suite
```

## Development

Run the test suite:

```bash
pytest
```

Tests cover resource generation, cost scaling, prestige reset, time-warp
gating, and save/load round-trip. The game logic in `game/game_state.py`
has no Textual or pygame dependency — it can be driven by any UI.

## License

MIT — see [LICENSE](LICENSE).
