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
loads it on startup. Offline progress accrues at a reduced rate (50%, up to
100% with Automatic Production) while the game is closed, for at most 24 hours.

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
| `a` / `A`  | Races tab: buy the race's first / second ability, or switch it on and off once owned |
| `p`        | Prestige (resets progression for prestige points) |
| `t`        | Activate Time Warp (once unlocked via prestige) |
| `s`        | Save now                                      |
| `ctrl+q`   | Save and quit                                 |

## Game Mechanics

- **Races** produce the resources they specialise in; level them up for bigger
  bonuses. Each race has two special abilities: once the race and your prestige
  count are high enough, buy one with `a`/`A`, then switch it on or off.
- **Buildings** boost production directly or via global multipliers. Multiplier
  buildings (Marketplace, Time Dilation Chamber) are limited to one each;
  upgrade them instead.
- **Research** spends ancient knowledge for permanent multipliers.
- **Prestige** resets your run in exchange for prestige points and permanent
  bonuses. Unlocks higher-tier races, buildings, and research. Time Warp runs
  for an hour of play and cools down for a day (offline time counts).
- **Achievements** trigger automatically and grant passive bonuses. Every
  listed reward applies, except dragon transmutation, which the Achievements
  tab marks inactive until the game has a transmutation system.
- **Pacing:** the first prestige takes roughly half an hour to an hour, and each
  prestige run opens the next tier of races, buildings and research
  (player levels 25, 35 and 50). If nothing you own produces gold, a small
  subsistence income pays out, so you can always afford a gold race again.

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
  test_errata.py              # Regression tests for errata E1–E14 (exploits, traps, bugs)
  test_rewards.py             # Every achievement reward and ability effect has a reader
tools/
  balance_sim.py              # Headless greedy balance probe (economy pacing)
```

## Development

Run the test suite:

```bash
pytest
```

Tests cover resource generation, cost scaling, prestige reset, time-warp
gating, and save/load round-trip.

Check economy pacing after changing costs or rewards (pacing knobs are in
`game/constants.py`; `--set` overrides them for a run):

```bash
python tools/balance_sim.py . --hours 8 --prestige --decision 30
python tools/balance_sim.py . --hours 2 --set BASE_INCOME_RATE=0.5
``` The game logic in `game/game_state.py`
has no Textual or pygame dependency — it can be driven by any UI.

## License

MIT — see [LICENSE](LICENSE).
