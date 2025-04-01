# Eldrith Realms Idle

An idle game featuring dwarves, elves, and other eldritch races. Players can build and manage their fantasy realm, gather resources, and unlock new races and abilities as they progress.

## Features
- Multiple fantasy races including dwarves, elves, and other eldritch beings
- Resource gathering and management
- Building construction and upgrades
- Research system to unlock new abilities
- Prestige system for long-term progression
- Bulk purchase options (x1, x10, x100, Max)
- Achievement system
- Save/load functionality including import/export

## Game Mechanics
- Each race produces different resources
- Buildings enhance resource production
- Research improves efficiency and unlocks new features
- Prestige resets progress but provides permanent bonuses

## Installation
1. Ensure you have Python 3.8+ installed
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the game:
   ```
   python main.py
   ```

## Controls
- Mouse: Click on elements to interact with them
- Tab buttons: Switch between different game sections (Races, Buildings, Research, etc.)
- Purchase buttons: Buy or upgrade game elements
- Bulk purchase panel: Select quantity for purchases (x1, x10, x100, Max)

## Development
This game is built using Python and Pygame. The code is organized as follows:

- `main.py`: Entry point and game loop
- `game/`: Core game modules
  - `game_state.py`: Game state management and logic
  - `constants.py`: Game constants and configuration
  - `ui/`: User interface components
    - `ui_manager.py`: UI management and rendering
    - `components.py`: Individual UI components (buttons, panels, etc.)
    - `notification_dialog.py`: Notification system

## License
MIT License
