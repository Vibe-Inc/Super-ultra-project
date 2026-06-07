# Super-ultra-project

A comprehensive Pygame-based RPG game engine developed as an OOP study project by students of Shevchenko National University of Kyiv. The project demonstrates state management, inventory systems, tile-based map rendering, character progression, combat mechanics, magic skill trees, minigames, and multi-language support.

## Features

### Core Gameplay
- **State Management**: Seamless transitions between menu, game, pause, and settings states via `StateManager`
- **Character System**: Player character with health, mana, stamina, XP/leveling system, movement, and status effects on tile-based maps
- **Combat & Progression**: XP-based leveling system — defeat enemies to gain XP and money; multiple weapon types (swords, maces, axes, spears, war hammers) with unique attack animations
- **Melee Combat**: Cone-based melee attacks with charged attacks, fast attacks, blocking, parrying, and weapon throwing
- **Ranged Combat**: Projectile system with arrows and magic bolts; mouse-aimed with cone-direction clamping
- **Enemy System**: AI-driven enemies with detection range, attack range, pathfinding (A*), stun mechanics, and 16+ unique attack profiles (Brute, Venomous, Arcanist, Trickster, Bomber, Phantom, Titan, Cryomancer, Shadowmancer, Revenant, Molten, Stormcaller, Plaguebearer, etc.)
- **Boss System**: Multi-phase boss (Chronos) with cinematic intro, phase transitions (Time Fractures, Chronos Awakens, The Final Hour), and unique attacks (Temporal Nova, Time Shards, Chrono Cascade, Time Stop, Decay Aura, Time Reversal, etc.)
- **NPC System**: Interactive NPCs including Merchants, Archeologist, Gambler, and Mage — each with unique dialog and trading/minigame access
- **Peaceful Mob System**: 9 species of ambient creatures (Grove Titan, Singing Stone, Ember Phoenix, Coral Golem, Void Butterfly, Moss Rabbit, Crystal Fox, Fairy Cat, Tavern Cat) with behavior AI (wandering, curiosity, shyness, fleeing from enemies) and pettable interactions
- **Nature Spirits**: Summoned spirits that follow the player and attack nearby enemies
- **Collision System**: Physics-based collision detection with map obstacles, spatial indexing for performance, and entity interactions
- **Tile-based Maps**: Loads and renders `.tmx` Tiled maps with PyTMX, supports multiple maps with seamless transitions
- **Map Switching**: Dynamic map transitions with per-map enemy, NPC, and peaceful mob spawning
- **Inventory System**: Grid-based inventory with item management, equipment slots, drag-and-drop, tooltips, and scrollbar
- **Shop/Trading System**: Buy and sell items from NPCs with in-game currency
- **Item Database**: Consumables (food, potions), weapons (swords, maces, axes, spears, war hammers), armor, accessories, resources, and tools with stackable support
- **Item Effects System**: Status effects including regeneration, poison, confusion, dizziness, slow, freeze, and more with visual feedback
- **Dropped Items**: Physics-based item drops from defeated enemies and peaceful mobs
- **Projectile System**: Arrows, fireballs, frost novas, chain lightning, thunderstrikes, entangling roots, arcane missiles, thrown weapons, and boss-specific projectiles
- **HUD**: In-game heads-up display showing player HP, mana bar (with crumble animation), stamina, lives, XP/level, money, minimap, effect icons, skill hotbar, and achievement popups
- **Save/Load System**: Save and load game progress including character stats, inventory, equipment, currency, skills, and world state

### Mana & Magic System
- **Mana Resource**: Regenerating mana with visual crumble animation on spend
- **Skill Tree**: 24+ learnable magic skills across 8 schools:
  - **Fire**: Fireball, Flame Shield, Pyromancer's Fury
  - **Ice**: Frost Nova, Ice Armor, Glacial Cascade
  - **Lightning**: Chain Lightning, Static Field, Thunderstrike
  - **Nature**: Entangling Roots, Regeneration, Summon Spirit
  - **Shadow**: Shadow Step, Poison Blade, Dark Pact
  - **Arcane**: Arcane Missiles, Mana Flow, Mystic Barrier
  - **Berserker**: Berserker's Rage, Eternal Fortress, Soul Harvest
  - **Chrono**: Void Walker, Elemental Mastery, Chrono Shift
- **Skillbar**: Active skill hotbar with cooldown indicators and mana cost display

### World Systems
- **Day/Night Cycle**: Smooth multi-stop color/brightness gradient with soft vignette
- **Weather System**: Rain (with puddles), fog (with floating clouds), and lightning — with gameplay effects
- **World Scale**: Progressive difficulty scaling system with XP, milestones, and stat modifiers for both player and enemies
- **Gatherable Nodes**: World resource nodes (trees, rocks, herbs, etc.) with cooldown timers and tool-based gathering
- **Smelting System**: Smeltery tiles with a full skill progression (SmeltingSkill) and recipe database

### Minigames
- **Blackjack**: Full card game with betting, hit/stand, dealer AI, and card art
- **Poker**: Card game with hand evaluation, betting rounds, and chip system
- **Roulette**: Casino roulette with wheel animation, bet zones, and chip placement
- **Archeologium**: Minesweeper-like excavation game with oracle ability and flagging
- **Fishing**: Cast-and-catch fishing with fish types, bobber physics, and UI feedback
- **Gathering**: Resource harvesting with tool progression, cooldowns, and cluster-based nodes
- **Crafting**: Item crafting with tier progression
- **Smeltery Minigames**: Multi-step smelting chain — Tending Fire, Forge (timing-based strikes), Quench (sweet-spot), Pattern (rhythm), Bellows (rhythm tap), Temper (color matching)
- **Rune Drawing**: Arcane rune tracing minigame with particle effects

### UI & Menus
- **Main Menu** with animated title (shimmer text, sparkles, floating orbs, light rays, ambient embers, clock widget)
- **Intro Animation** with cinematic launch sequence
- **Temple Intro Animation** for themed area transitions
- **Settings Menu** with audio toggle, fullscreen toggle, language selection, and back option
- **Credits Menu** with hover tooltips showing developer information
- **Pause Menu** with resume, save, settings, and exit options (accessible via ESC key)
- **Save/Load Menu** for managing saved games
- **Location Map Menu** for world navigation
- **Skill Tree Menu** for allocating skill points
- **Skillbar Menu** for managing active skills
- **Achievements Menu** for tracking unlocked achievements
- **Collection Book** for tracking discovered items/entities
- **Recipe Book** for browsing crafting and smelting recipes
- **Enchanting Menu** for weapon enchantment
- **Rune Selection Menu** for choosing rune types
- **Smeltery Menu** for smelting interface
- **Wiki Menu** for in-game documentation
- **Mysterium Magnum** — arcane knowledge compendium
- **Arcane Quest Menu** for quest tracking
- **World Scale Menu** for viewing difficulty progression
- **Debug Menu** for spawning enemies and applying effects (developer tool)
- **Reusable UI Widgets**: Button (with shield shape), Menu, Tooltip, Dialog (with particle effects), Slider, and inventory grids
- **Visual Effects System**: Stars, light rays, ambient embers, floating orbs, launch bursts, shimmer text, and title sparkles for menus
- **Responsive Design**: 1920×1080 resolution (configurable)

### Localization
- **Multi-language Support**: English and Ukrainian
- **Babel Integration**: Translation management via `.pot` and `.po` files

## Requirements

- **Python 3.10+** (uses modern type hints)
- **pygame-ce** 2.5.5+ (Community Edition)
- **PyTMX** 3.32+ (for Tiled map support)
- **Babel** 2.17.0+ (for localization)
- **Sphinx** + **sphinx_rtd_theme** (for documentation generation)

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
- **Left Click**: Melee attack (cone-based, direction from mouse aim)
- **Right Click**: Block / Parry (with timing window for parry)
- **Mouse**: Aim direction for attacks and ranged weapons
- **ESC**: Open pause menu
- **E**: Interact with NPC / Open trading interface (when near NPC); Pet peaceful mobs; Use smeltery; Open chests
- **I**: Toggle inventory panel
- **1-9**: Use skill from skillbar slot
- **Q**: Throw weapon (if available)
- **Shift**: Sprint (uses stamina)
- **R**: Charge attack (hold and release)
- **Map Transitions**: Walk to map edges to switch between maps

### Inventory & Trading
- **Drag & Drop**: Click and drag items between slots
- **Item Tooltips**: Hover over items to see name, description, effects, durability, and tier
- **Stacking**: Compatible items automatically stack (up to stack limit)
- **Equipment Slots**: Dedicated slots for weapons, armor, and accessories
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
├── glossary.md                # Game terminology glossary
│
├── src/
│   ├── app.py                # Main App class, game initialization, and currency management
│   ├── config.py             # Configuration (screen size, colors, fonts, UI settings)
│   ├── i18n.py               # Internationalization setup
│   │
│   ├── ai/
│   │   ├── monster_ai.py    # Enemy AI state machines (idle, chase, attack, patrol)
│   │   └── navigation.py    # A* pathfinding and navigation grid
│   │
│   ├── combat/
│   │   └── base_player_combat.py  # Player combat controller (melee, ranged, aiming)
│   │
│   ├── core/
│   │   ├── game.py           # Game state (gameplay logic, map switching, spawning)
│   │   ├── state.py          # Base State class
│   │   ├── state_manager.py  # State management system
│   │   ├── collision_system.py # Physics and collision handling with spatial indexing
│   │   ├── save_manager.py   # Save and load game functionality
│   │   ├── day_night.py      # Day/night cycle with gradient tinting and vignette
│   │   ├── weather.py        # Weather system (rain, fog, lightning) with gameplay effects
│   │   ├── achievements.py   # Achievement tracking and unlock system
│   │   ├── article_tracker.py # Wiki/article unlock tracking
│   │   ├── profiling.py      # Frame profiler and FPS counter for debugging
│   │   └── logger.py         # Logging system for debugging
│   │
│   ├── entities/
│   │   ├── character.py      # Player character (HP, mana, stamina, skills, combat, 24+ spells)
│   │   ├── enemy.py          # Enemy class with AI, combat, pathfinding, and 16+ attack profiles
│   │   ├── boss.py           # Boss (Chronos) with multi-phase combat and cinematic transitions
│   │   ├── boss_attacks.py   # Boss-specific attack patterns (temporal, chrono, chain attacks)
│   │   ├── boss_visuals.py   # Procedural boss sprite generation
│   │   ├── monster_attacks.py # Monster attack controllers (Brute, Venomous, Arcanist, etc.)
│   │   ├── monster_visuals.py # Procedural monster sprite generation for 16+ types
│   │   ├── monster_attack_visuals.py # Visual effects for monster attacks
│   │   ├── npc.py            # Base NPC class for trading and interaction
│   │   ├── archeologist_npc.py # Archeologist NPC with unique dialog
│   │   ├── gambler_npc.py    # Gambler NPC (access to card games)
│   │   ├── mage_npc.py       # Mage NPC (access to rune crafting/enchanting)
│   │   ├── peaceful_mob.py   # Peaceful ambient creatures with behavior AI
│   │   ├── peaceful_mob_visuals.py # Procedural peaceful mob sprite generation
│   │   ├── nature_spirit.py  # Summoned nature spirit follower
│   │   ├── dropped_item.py   # Physics-based item drops
│   │   └── projectile.py     # Projectiles (arrows, fireballs, frost, lightning, etc.)
│   │
│   ├── inventory/
│   │   ├── system.py         # Inventory, equipment, shop, and trading systems
│   │   ├── inventory_manager.py # Inventory logic and state management
│   │   └── inventory_renderer.py # Inventory UI rendering
│   │
│   ├── items/
│   │   ├── items.py          # Item factory and definitions
│   │   └── __init__.py
│   │
│   ├── mana/
│   │   └── mana_system.py   # Mana resource with regeneration and crumble animation
│   │
│   ├── map/
│   │   ├── map.py            # Tile-based map rendering and obstacle detection (PyTMX)
│   │   └── locations.py      # Map location definitions and transitions
│   │
│   ├── minigames/
│   │   ├── blackjack.py      # Blackjack card game with betting
│   │   ├── poker.py          # Poker card game with hand evaluation
│   │   ├── roulette.py       # Casino roulette with wheel and bet zones
│   │   ├── archeologium.py   # Minesweeper-like excavation game
│   │   ├── fishing.py        # Fishing minigame with casting and catching
│   │   ├── gathering.py      # Resource gathering with tool progression
│   │   ├── crafting.py       # Item crafting with tier progression
│   │   ├── smeltery_minigames.py # Smeltery chain (Fire, Forge, Quench, Pattern, Bellows, Temper)
│   │   └── rune_drawing.py   # Arcane rune tracing minigame
│   │
│   ├── systems/
│   │   ├── smelting_skill.py  # Smelting skill progression (XP, levels)
│   │   └── world_scale.py     # World difficulty scaling with milestones
│   │
│   ├── ui/
│   │   ├── hud.py            # Heads-up display (HP, mana, stamina, XP, money, minimap, skills, effects, achievements)
│   │   ├── widgets.py        # UI widgets (Button, Tooltip, Dialog, Slider)
│   │   ├── effects.py        # Visual effects (stars, light rays, embers, orbs, shimmer text, sparkles)
│   │   ├── debug_menu.py     # Debug menus (spawn, effects) for development
│   │   └── menus/
│   │       ├── main_menu.py          # Main menu with animated background
│   │       ├── pause_menu.py         # Pause menu
│   │       ├── settings_menu.py      # Settings menu
│   │       ├── credits_menu.py       # Credits with developer tooltips
│   │       ├── save_load_menu.py     # Save/Load management
│   │       ├── intro_animation.py    # Cinematic intro sequence
│   │       ├── temple_intro_animation.py # Temple area intro
│   │       ├── skilltree_menu.py     # Skill tree allocation
│   │       ├── skillbar_menu.py      # Skill hotbar management
│   │       ├── achievements_menu.py  # Achievement tracking
│   │       ├── collection_book.py    # Item/entity collection tracker
│   │       ├── recipe_book.py        # Crafting/smelting recipe browser
│   │       ├── enchanting_menu.py    # Weapon enchantment
│   │       ├── rune_selection_menu.py # Rune type selection
│   │       ├── smeltery.py           # Smeltery interface
│   │       ├── wiki_menu.py          # In-game wiki
│   │       ├── mysterium_magnum.py   # Arcane knowledge compendium
│   │       ├── arcane_quest_menu.py  # Quest tracking
│   │       ├── location_map_menu.py  # World location map
│   │       ├── world_scale_menu.py   # Difficulty progression view
│   │       └── base.py               # Base menu class
│   │
│   └── world/
│       └── gatherable_nodes.py # World resource nodes with cooldowns and clusters
│
├── database/
│   ├── GP_database.py        # Game parameter database
│   ├── GP_database.db        # SQLite game database
│   ├── crafting_recepies_db.py # Crafting recipe definitions
│   ├── crafting_tiers_db.py  # Crafting tier progression
│   ├── smeltery_recipes_db.py # Smeltery recipe definitions
│   ├── effects.py            # Status effect definitions
│   └── item_db/              # Item database files
│
├── data/
│   ├── __init__.py
│   └── gatherable_nodes.py   # Gatherable node definitions
│
├── assets/
│   ├── characters/           # Character sprite sets (walk cycles, portraits)
│   ├── items/                # Item sprites organized by type
│   │   ├── accessories/
│   │   ├── armor/
│   │   ├── consumables/
│   │   ├── resources/
│   │   ├── tools/
│   │   └── weapons/
│   ├── minigames/            # Minigame assets (cards, fishing)
│   ├── tarot/                # Tarot card art (22 major arcana)
│   ├── misc/                 # Miscellaneous assets
│   └── ui/                   # UI images (menu backgrounds, icons)
│
├── fonts/                    # TTF font files
├── maps/                     # Tiled map files (.tmx) and tilesets (.tsx)
├── sounds/                   # Background music and sound effects
├── locales/                  # Localization files (messages.po, messages.mo)
│   ├── en/LC_MESSAGES/
│   └── ua/LC_MESSAGES/
├── logs/                     # Game logs for debugging
└── docs/                     # Sphinx documentation source
```

## Configuration

Key settings in `src/config.py`:
- **Screen Resolution**: `SCREEN_WIDTH = 1920`, `SCREEN_HEIGHT = 1080`
- **FPS**: 60
- **Language**: `LANGUAGE = 'en'` (or `'ua'` for Ukrainian)
- **Button Colors & Hover States**: Configurable per button type
- **Inventory Layout**: 8×4 main inventory, equipment slots, 8×4 shop grid
- **Slot Size**: 70 pixels (configurable)
- **Starting Money**: 100 gold (in `app.py`)
- **Character Stats**: Starting HP, mana, stamina, speed, animation settings
- **Skill System**: 24+ skills with cooldowns, mana costs, and element types
- **Enemy AI**: Detection range, attack range, damage, HP, and attack profiles
- **Map Spawns**: Per-map enemy, NPC, and peaceful mob spawn coordinates in `game.py`
- **World Scale**: Progressive difficulty modifiers for player and enemy stats
- **Weather**: Rain, fog, lightning intervals and visual parameters
- **Day/Night**: Cycle timing and color gradient stops

## Development Notes

- **State Machine**: The game uses a state-based architecture (`StateManager`) for clean separation of menu, gameplay, pause, and settings logic
- **Type Hints**: All classes use Python 3.10+ type annotations for clarity
- **Collision System**: Centralized physics handling with AABB collision detection, spatial indexing, and obstacle resolution
- **Inventory Architecture**: Items support stacking, dragging, equipment slots, and shop trading with tooltip feedback
- **Effect System**: Base `Effect` class with subclasses for different status effects (regeneration, poison, confusion, dizziness, slow, freeze, etc.)
- **AI System**: Enemies use state machines (idle, chase, attack, patrol) with A* pathfinding toward player
- **Attack System**: Modular attack controllers per enemy type — each with unique patterns, cooldowns, and visual effects
- **Boss System**: Multi-phase boss with cinematic intro, phase transitions, and escalating attack patterns
- **Monster Visuals**: Procedural sprite generation for 16+ monster types and 9 peaceful mob species
- **PyTMX Integration**: Maps are created in Tiled and loaded at runtime with obstacle layer parsing
- **Save System**: JSON-based serialization of game state including character stats, inventory, equipment, skills, and world state
- **Logging**: Comprehensive logging system for debugging (`logs/` directory)
- **i18n Support**: Uses GNU gettext standards via Babel for easy translations
- **Spawn Management**: Per-map dictionaries control enemy, NPC, and peaceful mob spawn positions
- **Profiling**: Built-in frame profiler and FPS counter for performance debugging
- **Minigames**: Chain-based minigame system (e.g., smeltery steps) with shared UI patterns
- **World Scale**: Progressive difficulty system with milestone-based ability unlocks
- **Gatherable Nodes**: Cluster-based resource nodes with cooldown timers and tool requirements

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