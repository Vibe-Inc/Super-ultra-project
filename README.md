# Super-ultra-project

A comprehensive Pygame-based RPG game engine developed as an OOP study project by students of Shevchenko National University of Kyiv. The project demonstrates state management, inventory systems, tile-based map rendering, character progression, and multi-language support.

## Features

### Core Gameplay
- **State Management**: Seamless transitions between menu, game, pause, and settings states via `StateManager`
- **Character System**: Player character with health, XP/leveling system, movement, and status effects on tile-based maps
- **Combat & Progression**: XP-based leveling system - defeat enemies to gain XP (30-60 per kill) and money (5-20 gold)
- **Enemy System**: AI-driven enemies with detection range, attack range, pathfinding, and combat mechanics
- **NPC System**: Interactive NPCs for trading (NPC spawns only on first map)
- **Collision System**: Physics-based collision detection with map obstacles and entity interactions
- **Tile-based Maps**: Loads and renders `.tmx` Tiled maps with PyTMX, supports multiple maps with seamless transitions
- **Map Switching**: Dynamic map transitions with per-map enemy and NPC spawning
- **Inventory System**: Grid-based inventory with item management, equipment slots, drag-and-drop, and tooltips
- **Shop/Trading System**: Buy and sell items from NPCs with in-game currency
- **Item Database**: Consumable items (food, potions) and weapons (swords) with stackable support
- **Item Effects System**: Status effects including regeneration, poison, confusion, and dizziness with visual feedback
- **HUD**: In-game heads-up display showing player HP, lives, XP/level, money, and inventory button
- **Save/Load System**: Save and load game progress including character stats, inventory, equipment, and currency

### UI & Menus
- **Main Menu** with START, LOAD, EXIT, SETTINGS, and CREDITS buttons
- **Settings Menu** with audio toggle, fullscreen toggle, language selection, and back option
- **Credits Menu** with hover tooltips showing developer information
- **Pause Menu** with resume, save, settings, and exit options (accessible via ESC key)
- **Load Menu** for loading saved games
- **Reusable UI Widgets**: Button class, Menu system, Tooltip system, and inventory grids
- **Responsive Design**: 1920×1080 resolution (configurable)

### Localization
- **Multi-language Support**: English and Ukrainian
- **Babel Integration**: Translation management via `.pot` and `.po` files

## Requirements

- **Python 3.10+** (uses modern type hints)
- **pygame-ce** 2.5.5+ (Community Edition)
- **PyTMX** 3.32+ (for Tiled map support)
- **Babel** 2.17.0+ (for localization)

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Running the Game

From the project root:

```powershell
python main.py
```

The game launches with a 1920×1080 window displaying the main menu with background image and audio enabled by default.

## Controls

### Menu Navigation
- **Mouse hover**: Highlights buttons
- **Left click**: Activates buttons (START, LOAD, EXIT, SETTINGS, CREDITS, BACK)

### In-Game (Gameplay State)
- **WASD / Arrow Keys**: Move character in four directions
- **ESC**: Open pause menu
- **E**: Interact with NPC / Open trading interface (when near NPC)
- **I**: Toggle inventory panel
- **Mouse**: Click and drag items between inventory slots, equipment, and shop
- **Map Transitions**: Walk to map edges to switch between maps

### Inventory & Trading
- **Drag & Drop**: Click and drag items between slots
- **Item Tooltips**: Hover over items to see name, description, and effects
- **Stacking**: Compatible items automatically stack (up to stack limit)
- **Equipment Slots**: Dedicated slots for weapons and armor
- **Trading**: Click items in shop to buy, right-click inventory items to sell (when trading)
- **Item Consumption**: Use consumable items for effects (healing, buffs, debuffs)

### Settings
- **Audio Toggle**: Enable/disable background music
- **Fullscreen Toggle**: Switch between windowed and fullscreen modes
- **Language Toggle**: Switch between English and Ukrainian

## Project Structure

```
.
├── main.py                    # Entry point
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── babel.cfg                  # Babel configuration for translations
├── ideas.md                   # Project planning/ideas
│
├── src/
│   ├── app.py                # Main App class, game initialization, and currency management
│   ├── config.py             # Configuration (screen size, colors, fonts, UI settings)
│   ├── i18n.py               # Internationalization setup
│   │
│   ├── core/
│   │   ├── game.py           # Game state (gameplay logic, map switching, spawning)
│   │   ├── state.py          # Base State class
│   │   ├── state_manager.py  # State management system
│   │   ├── collision_system.py # Physics and collision handling
│   │   ├── save_manager.py   # Save and load game functionality
│   │   └── logger.py         # Logging system for debugging
│   │
│   ├── entities/
│   │   ├── character.py      # Player character class with XP, leveling, and effects
│   │   ├── enemy.py          # Enemy class with AI, combat, and pathfinding
│   │   └── npc.py            # NPC class for trading and interaction
│   │
│   ├── inventory/
│   │   └── system.py         # Inventory, equipment, shop, and trading systems
│   │
│   ├── items/
│   │   ├── items.py          # Item factory and definitions
│   │   ├── item_database.py  # Item data and properties
│   │   └── effects.py        # Status effects (regeneration, poison, confusion, dizziness)
│   │
│   ├── map/
│   │   └── map.py            # Tile-based map rendering and obstacle detection (PyTMX)
│   │
│   └── ui/
│       ├── hud.py            # Heads-up display (HP, XP, money, lives)
│       ├── menus.py          # Menu state classes (main, pause, settings, credits, load)
│       └── widgets.py        # UI widgets (buttons, tooltips)
│
├── assets/
│   ├── smug.png              # Window icon
│   ├── bg_menu.jpg           # Menu background image
│   ├── characters/           # Character sprite sets (walk cycles, portraits)
│   ├── items/                # Item sprites
│   │   ├── consumables/
│   │   └── weapons/
│   └── sounds/               # Audio files
│
├── fonts/                     # TTF font files
├── maps/                      # Tiled map files (.tmx) and tilesets (.tsx)
├── saves/                     # Saved game files (JSON format)
├── logs/                      # Game logs for debugging
├── locales/                   # Localization files (messages.po, messages.mo)
│   ├── en/LC_MESSAGES/
│   └── ua/LC_MESSAGES/
└── sounds/                    # Background music and sound effects
```

## Configuration

Key settings in `src/config.py`:
- **Screen Resolution**: `SCREEN_WIDTH = 1920`, `SCREEN_HEIGHT = 1080`
- **FPS**: 60
- **Language**: `LANGUAGE = 'en'` (or `'ua'` for Ukrainian)
- **Button Colors & Hover States**: Configurable per button type
- **Inventory Layout**: 8×4 main inventory, 2×4 equipment slots, 8×4 shop grid
- **Slot Size**: 70 pixels (configurable)
- **Starting Money**: 100 gold (in `app.py`)
- **Character Stats**: Starting HP, speed, animation settings
- **Enemy AI**: Detection range, attack range, damage, and HP
- **Map Spawns**: Per-map enemy and NPC spawn coordinates in `game.py`

## Troubleshooting

- **Missing assets errors**: Ensure `assets/`, `fonts/`, `maps/`, and `sounds/` folders exist with required files
- **ImportError or Module not found**: Run `python -m pip install -r requirements.txt` to install all dependencies
- **Font rendering issues**: The app falls back to Arial if custom fonts are unavailable
- **Map not loading**: Verify `.tmx` files are in `maps/` and tilesets are correctly referenced
- **Collision issues**: Check that maps have proper collision layers defined in Tiled
- **Save/Load errors**: The `saves/` directory is auto-created; ensure write permissions
- **Enemy not spawning**: Check `ENEMY_SPAWNS` dictionary in `game.py` for current map path
- **NPC not visible**: NPC only spawns on the first map (`test-map-1.tmx`)
- **Fullscreen behaves oddly**: Close and reopen the app to reset display settings
- **Translation not working**: Ensure `.mo` files are compiled in `locales/*/LC_MESSAGES/`
- **Performance issues**: Check logs in `logs/` directory for errors or warnings

## Development Notes

- **State Machine**: The game uses a state-based architecture (`StateManager`) for clean separation of menu, gameplay, pause, and settings logic
- **Type Hints**: All classes use Python 3.10+ type annotations for clarity
- **Collision System**: Centralized physics handling with AABB collision detection and obstacle resolution
- **Inventory Architecture**: Items support stacking, dragging, equipment slots, and shop trading with tooltip feedback
- **Effect System**: Base `Effect` class with subclasses for different status effects (regeneration, poison, confusion, dizziness)
- **AI System**: Enemies use state machines (idle, chase, attack) with pathfinding toward player
- **PyTMX Integration**: Maps are created in Tiled and loaded at runtime with obstacle layer parsing
- **Save System**: JSON-based serialization of game state including character stats, inventory, and equipment
- **Logging**: Comprehensive logging system for debugging (`logs/` directory)
- **i18n Support**: Uses GNU gettext standards via Babel for easy translations
- **Spawn Management**: Per-map dictionaries control enemy and NPC spawn positions

## Contributing

This is an educational project — contributions are welcome. Consider:

- **Code Quality**: Follow PEP 8, use type hints, add docstrings
- **Features**: Keep changes focused; coordinate for large additions
- **Testing**: Add tests for new systems where practical
- **Documentation**: Update README for new features or configuration options
- **Assets**: Organize art/audio by type in `assets/` subdirectories
- **Translations**: Update `.pot` file and generate `.po`/`.mo` files via Babel

## Documentation

Automatically generated documentation for this project is available at the following link:
[GitHub Pages Documentation](https://vibe-inc.github.io/Super-ultra-project/)

The documentation is generated after each code update using GitHub Actions and Sphinx.

## License

This repository does not include a license file.
