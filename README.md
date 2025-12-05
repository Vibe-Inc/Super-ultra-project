# Super-ultra-project

A comprehensive Pygame-based RPG game engine developed as an OOP study project by students of Shevchenko National University of Kyiv. The project demonstrates state management, inventory systems, tile-based map rendering, character progression, and multi-language support.

## Features

### Core Gameplay
- **State Management**: Seamless transitions between menu, game, and settings states via `StateManager`
- **Character System**: Player character with attributes and movement on tile-based maps
- **Enemy System**: AI-driven enemies in the game world
- **Tile-based Maps**: Loads and renders `.tmx` Tiled maps with PyTMX
- **Inventory System**: Grid-based inventory with item management, equipment slots, drag-and-drop, and tooltips
- **Item Database**: Consumable items (food) and weapons (swords) with stackable support
- **HUD**: In-game heads-up display showing player status and inventory

### UI & Menus
- **Main Menu** with START, EXIT, SETTINGS, and CREDITS buttons
- **Settings Menu** with audio toggle, fullscreen toggle, and back option
- **Credits Menu** with hover tooltips
- **Reusable UI Widgets**: Button class, Menu system, and Tooltip system
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
- **Left click**: Activates buttons (START, EXIT, SETTINGS, CREDITS, BACK)

### In-Game (Gameplay State)
- Navigate and interact with the tile-based map
- **Inventory System**: Click and drag items between inventory slots, equipment, and the world
- **Item Tooltips**: Hover over items to see descriptions
- **Stacking**: Compatible items automatically stack
- **Equipment Slots**: Dedicated slots for weapons and armor

### Settings
- **Audio Toggle**: Enable/disable background music
- **Fullscreen Toggle**: Switch between windowed and fullscreen modes

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
│   ├── app.py                # Main App class and game initialization
│   ├── config.py             # Configuration (screen size, colors, fonts, UI settings)
│   ├── i18n.py               # Internationalization setup
│   │
│   ├── core/
│   │   ├── game.py           # Game state (gameplay logic)
│   │   ├── state.py          # Base State class
│   │   └── state_manager.py  # State management system
│   │
│   ├── entities/
│   │   ├── character.py      # Player character class
│   │   └── enemy.py          # Enemy class
│   │
│   ├── inventory/
│   │   ├── system.py         # Inventory and equipment classes
│   │   ├── items.py          # Item factory and definitions
│   │   └── item_database.py  # Item data and properties
│   │
│   ├── map/
│   │   └── map.py            # Tile-based map rendering (PyTMX)
│   │
│   └── ui/
│       ├── hud.py            # Heads-up display
│       ├── menus.py          # Menu state classes
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
├── locales/                   # Localization files (messages.po, messages.mo)
│   ├── en/LC_MESSAGES/
│   └── ua/LC_MESSAGES/
```

## Configuration

Key settings in `src/config.py`:
- **Screen Resolution**: `SCREEN_WIDTH = 1920`, `SCREEN_HEIGHT = 1080`
- **FPS**: 60
- **Language**: `LANGUAGE = 'en'` (or `'ua'` for Ukrainian)
- **Button Colors & Hover States**: Configurable per button type
- **Inventory Layout**: 8×4 main inventory, 2×4 equipment slots
- **Slot Size**: 70 pixels (configurable)

## Troubleshooting

- **Missing assets errors**: Ensure `assets/`, `fonts/`, and `maps/` folders exist with required files
- **ImportError or Module not found**: Run `python -m pip install -r requirements.txt` to install all dependencies
- **Font rendering issues**: The app falls back to Arial if custom fonts are unavailable
- **Map not loading**: Verify `.tmx` files are in `maps/` and tilesets are correctly referenced
- **Fullscreen behaves oddly**: Close and reopen the app to reset display settings
- **Translation not working**: Ensure `.mo` files are compiled in `locales/*/LC_MESSAGES/`

## Development Notes

- **State Machine**: The game uses a state-based architecture (`StateManager`) for clean separation of menu and gameplay logic
- **Type Hints**: All classes use Python 3.10+ type annotations for clarity
- **Inventory Architecture**: Items support stacking, dragging, and equipment slots with tooltip feedback
- **PyTMX Integration**: Maps are created in Tiled and loaded at runtime
- **i18n Support**: Uses GNU gettext standards via Babel for easy translations

## Contributing

This is an educational project — contributions are welcome. Consider:

- **Code Quality**: Follow PEP 8, use type hints, add docstrings
- **Features**: Keep changes focused; coordinate for large additions
- **Testing**: Add tests for new systems where practical
- **Documentation**: Update README for new features or configuration options
- **Assets**: Organize art/audio by type in `assets/` subdirectories
- **Translations**: Update `.pot` file and generate `.po`/`.mo` files via Babel

## License

This repository does not include a license file.
