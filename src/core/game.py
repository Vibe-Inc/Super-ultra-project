import math
import pygame
import pytmx
import os
import sys
# Ensure project root is on sys.path if this module is executed directly
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from typing import TYPE_CHECKING
import random

from src.core.logger import logger
import src.config as cfg
from src.core.day_night import DayNightVisuals
from src.core.state import State
from src.core.save_manager import SaveManager
from src.entities.character import Character
from src.map.map import LocalMap
from src.inventory.system import MAIN_player_inventory, MAIN_player_inventory_equipment, ShopInventory, MAIN_player_hotbar
from src.items.items import create_item, LightRing
from database.effects import RegenerationEffect, PoisonEffect, ConfusionEffect, DizzinessEffect, SlowEffect
from src.entities.enemy import Enemy
from src.entities.boss import Boss
from src.entities.npc import NPC
from src.entities.mage_npc import MageNPC
from src.entities.projectile import Arrow
from src.ui.hud import HUD
from src.ui.widgets import Dialog
from src.ui.debug_menu import SpawnMenu, EffectsMenu
from src.core.collision_system import CollisionSystem
from src.ai.navigation import NavGrid
from src.entities.monster_visuals import build_monster_animations
from src.entities.monster_attacks import build_attack_controller, AttackContext
from src.entities.boss_visuals import build_boss_animations
from src.entities.boss_attacks import build_boss_attack_controller
from src.combat.base_player_combat import PlayerCombatController
from src.minigames.blackjack import BlackjackGame
from src.minigames.roulette import RouletteGame
from src.minigames.poker import PokerGame
from src.minigames.crafting import CraftingMinigame
from src.minigames.fishing import FishingController
from src.minigames.gathering import GatheringController
from src.world.gatherable_nodes import GatherableNodeRegistry
from src.ui.menus.smeltery import SmelteryMenu
import inspect
import database.effects as effects_db

if TYPE_CHECKING:
    from src.app import App

class Game(State):
    """
    Main gameplay state for the application.

    Owns the player character, the current map, enemy spawning, the
    HUD, the merchant and card-game NPCs, the blackjack minigame, the
    debug spawn menu, and the day/night cycle. Drives the per-frame
    update + draw pipeline and dispatches pygame events to the right
    subsystems (HUD, inventory, combat, dialogs).

    Attributes:
        app (App):
            The main application reference.
        character (Character):
            The player character instance.
        map (LocalMap):
            The current game map.
        current_map_path (str):
            Path of the .tmx map currently loaded.
        collision_handler (CollisionSystem):
            Helper for movement resolution and interaction checks.
        obstacles (list):
            Current map's static collision rectangles.
        nav_grid (NavGrid):
            Navigation grid for pathfinding around the current map.
        MAIN_player_inv (MAIN_player_inventory):
            Main grid inventory of the player.
        PLAYER_inventory_equipment (MAIN_player_inventory_equipment):
            Equipment loadout inventory of the player.
        hotbar (MAIN_player_hotbar):
            Quick-access hotbar inventory.
        player_combat (PlayerCombatController):
            Player melee / ranged combat controller.
        projectiles (list):
            Active player projectiles.
        enemy_projectiles (list):
            Active enemy projectiles.
        equipped_weapon (object):
            Currently equipped weapon reference, or None.
        enemy_profiles (dict):
            Per-archetype enemy stat/AI profile definitions.
        enemy_profile_names (list):
            Names of all enemy profiles available for spawning.
        ENEMY_SPAWNS (dict):
            Map-path -> spawn info for default enemies.
        NPC_SPAWNS (dict):
            Map-path -> (x, y) for the merchant NPC.
        CARD_NPC_SPAWNS (dict):
            Map-path -> (x, y) for the blackjack NPC.
        NO_ENEMY_SPAWN_MAPS (set):
            Map paths where enemies are never spawned.
        hud (HUD):
            Heads-up display for the player.
        enemy (Enemy):
            The current main enemy instance, if any.
        enemies (list):
            All currently active enemies.
        items (list):
            All currently active dropped items.
        enemy_spawn_timer (float):
            Seconds elapsed since the last periodic spawn check.
        enemy_spawn_interval (float):
            Seconds between periodic enemy spawn attempts.
        npc (NPC):
            Merchant NPC instance for the current map.
        card_npc (NPC):
            Card-game NPC instance for the current map.
        card_npc_first_dialog (list):
            First-time dialog lines for the card NPC.
        card_npc_repeat_dialog (list):
            Repeat dialog lines for the card NPC.
        card_npc_post_game_dialog (list):
            Dialog lines shown after a blackjack round.
        shop_inv (ShopInventory):
            Merchant shop inventory used by the NPC.
        blackjack_game (BlackjackGame):
            Active blackjack instance, or None.
        roulette_game (RouletteGame):
            Active roulette instance, or None.
        poker_game (PokerGame):
            Active poker instance, or None.
        crafting_minigame (CraftingMinigame):
            Active "Tempering" minigame instance, or None.
        spawn_menu (SpawnMenu):
            Debug menu for spawning enemies on demand.
        game_time_seconds (float):
            In-game time in seconds since midnight.
        GAME_DAY_SECONDS (int):
            Number of in-game seconds in a full day.
        DAY_CYCLE_REAL_SECONDS (int):
            Number of real-world seconds for a full 24h in-game cycle.
        GAME_SECONDS_PER_REAL_SECOND (float):
            Conversion factor from real seconds to in-game seconds.
        DAY_START (int):
            In-game second at which day begins.
        DUSK_START (int):
            In-game second at which dusk begins.
        NIGHT_START (int):
            In-game second at which night begins.
        DAWN_START (int):
            In-game second at which dawn begins.
        NIGHT_BRIGHTNESS (float):
            Environment brightness multiplier at night.
        player_inventory_opened (bool):
            Whether the player inventory screen is currently shown.
        _dizzy_overlay (pygame.Surface):
            Cached white overlay surface used for the dizzy effect.

    Methods:
        __init__(app):
            Build the game state: character, map, HUD, NPCs, blackjack.
        reinit_ui():
            Recreate UI elements that depend on language/scale (HUD).
        toggle_player_inventory():
            Open or close the player's main inventory.
        open_shop():
            Toggle the merchant's trading interface.
        open_blackjack():
            Launch the blackjack minigame overlay.
        open_crafting_minigame(crafted_item, consume_callback, smelting_level=1):
            Launch the Tempering timing minigame for a workbench craft.
        _get_card_npc_dialog():
            Pick the right card-NPC dialog lines for the current state.
        use_skill_slot(slot_index):
            Activate the skill currently bound to the given hotbar slot.
        _update_projectiles(dt):
            Step all player projectiles and prune dead ones.
        _update_enemy_projectiles(dt):
            Step all enemy projectiles and prune dead ones.
        _rebuild_nav_grid():
            Rebuild the navigation grid for the current map.
        _format_game_time():
            Format the current in-game time as an HH:MM string.
        is_daytime():
            Return True if the in-game clock is currently daytime.
        _update_game_time(dt):
            Advance the in-game clock and update day/night brightness.
        _get_spawn_entries(map_path):
            Resolve the configured enemy spawn entries for a given map path
            as a list of {"pos": (x, y), "profile": "name"} dicts.
        _get_camera_offset():
            Compute the camera offset (in world space) for this frame.
        _make_patrol_points(center, radius):
            Build a square patrol loop around a center point.
        _create_enemy(x, y, profile=None):
            Construct an Enemy with a chosen profile at a given position.
        spawn_random_enemy():
            Try to spawn a random enemy somewhere on the current map.
        _debug_spawn_enemy(profile_name):
            Spawn an enemy of a given profile next to the player.
        _debug_apply_effect(effect_name, duration):
            Apply a debug effect to the player for testing.
        _get_drop_chance_for_enemy(enemy):
            Look up the drop table for a given enemy.
        _drop_enemy_loot(enemy):
            Roll and spawn drops for a defeated enemy (no JSON).
        _apply_ice_armor_slow(dt):
            Apply slowing effect to nearby enemies when Ice Armor is active.
        _apply_flame_shield_damage(dt):
            Apply fire damage to nearby enemies when Flame Shield is active.
        _apply_regeneration(dt):
            Apply passive health regeneration from effects.
        _update_spirits(dt):
            Update summoned spirit entities.
        update(dt):
            Per-frame state update (input, AI, physics, time, spawning).
        draw_scene(screen):
            Update + draw the world scene (map, entities, overlays).
        draw_ui(screen):
            Draw HUD, inventory, dialogs, blackjack, and debug menu.
        draw(screen):
            Draw the scene followed by the UI on top of it.
        handle_event(event):
            Dispatch a pygame event to the right subsystem.
    """
    def __init__(self, app: "App"):
        super().__init__(app)
        logger.info("Initializing Game State...")
        self.character = Character()
        self.character.game_state = self

        initial_map_path = "maps/test-map-1.tmx"
        self.current_map_path = initial_map_path
        self.intro_played = False
        self._intro_sequence_active = False
        self.map = LocalMap("Level1", initial_map_path)

        self.collision_handler = CollisionSystem()
        
        self.obstacles = self.map.get_obstacles()
        self.nav_grid = None
        self._rebuild_nav_grid()

        self.player_inventory_opened = app.INV_manager.player_inventory_opened

        self.MAIN_player_inv = MAIN_player_inventory(app)
        self.PLAYER_inventory_equipment = MAIN_player_inventory_equipment(app)
        self.PLAYER_inventory_equipment.sync_character_defense(self.character)
        self.hotbar = MAIN_player_hotbar(app)
        self.app.INV_manager.hotbar = self.hotbar
        self.app.INV_manager.add_active_inventory(self.hotbar)
        self.player_combat = PlayerCombatController(self)

        self.projectiles = []
        self.enemy_projectiles = []
        self.spirits = []
        self.equipped_weapon = None
        self._dizzy_overlay = None

        self.game_time_seconds = 6 * 3600  # Start at 06:00
        self.GAME_DAY_SECONDS = 24 * 3600
        self.DAY_CYCLE_REAL_SECONDS = 12 * 60  # 12 real-life minutes for full 24h cycle
        self.GAME_SECONDS_PER_REAL_SECOND = self.GAME_DAY_SECONDS / self.DAY_CYCLE_REAL_SECONDS
        self.DAY_START = 6 * 3600
        self.DUSK_START = 16 * 3600
        self.NIGHT_START = 18 * 3600
        self.DAWN_START = 4 * 3600
        self.NIGHT_BRIGHTNESS = 0.15

        # Majestic day-night visual controller
        self.day_night = DayNightVisuals()

        self.enemy_profiles = {
            "brute": {
                "visual_style": "brute",
                "sprite_set": "MenHuman1",
                "speed": 110.0,
                "hp": 160,
                "damage": 20,
                "animation_speed": 5.0,
                "detection_range": 240.0,
                "attack_range": 45.0,
                "ai_profile": "guardian",
                "attack_profile": "brute",
                "attack_config": {
                    "cooldown_ms": 1100,
                    "charge_cooldown_ms": 2400,
                    "charge_duration": 0.7,
                    "charge_speed_mult": 2.4,
                    "slam_damage_mult": 1.5,
                    "slow_duration": 1.5,
                    "slow_factor": 0.6,
                },
                "contact_damage": False,
                "drop_chance": [
                    {"item_id": "small_health_potion", "chance": 0.95},
                    {"item_id": "large_health_potion", "chance": 1.0},
                ],
            },
            "venomous": {
                "visual_style": "venomous",
                "sprite_set": "MenHuman1(Recolor)",
                "speed": 130.0,
                "hp": 95,
                "damage": 12,
                "animation_speed": 6.5,
                "detection_range": 260.0,
                "attack_range": 38.0,
                "ai_profile": "stalker",
                "attack_profile": "venomous",
                "attack_config": {
                    "cooldown_ms": 900,
                    "poison_duration": 4.0,
                    "poison_dps": 5.0,
                    "strike_damage_mult": 0.85,
                },
                "contact_damage": False,
                "drop_chance": [
                    {"item_id": "small_health_potion", "chance": 0.25},
                    {"item_id": "potion_of_confusion", "chance": 0.20},
                ],
            },
            "arcanist": {
                "visual_style": "arcanist",
                "sprite_set": "WomanHuman1",
                "speed": 115.0,
                "hp": 80,
                "damage": 14,
                "animation_speed": 6.2,
                "detection_range": 300.0,
                "attack_range": 40.0,
                "ai_profile": "stalker",
                "attack_profile": "arcanist",
                "attack_config": {
                    "cooldown_ms": 950,
                    "bolt_speed": 480.0,
                    "bolt_range": 560.0,
                    "bolt_damage_mult": 0.85,
                    "burn_duration": 3.2,
                    "burn_dps": 4.5,
                    "cast_range": 340.0,
                    "spread_degrees": 5.0,
                },
                "contact_damage": False,
                "drop_chance": [
                    {"item_id": "small_health_potion", "chance": 0.30},
                    {"item_id": "large_health_potion", "chance": 0.15},
                    {"item_id": "potion_of_confusion", "chance": 0.10},
                ],
            },
            "trickster": {
                "visual_style": "trickster",
                "sprite_set": "WomanHuman1(Recolor)",
                "speed": 150.0,
                "hp": 75,
                "damage": 10,
                "animation_speed": 7.5,
                "detection_range": 280.0,
                "attack_range": 35.0,
                "ai_profile": "skirmisher",
                "attack_profile": "trickster",
                "attack_config": {
                    "cooldown_ms": 1800,
                    "step_range": 240.0,
                    "step_distance": 55.0,
                    "step_attempts": 6,
                    "step_spread_degrees": 110.0,
                    "strike_range": 75.0,
                    "confuse_duration": 2.8,
                    "dizzy_duration": 2.2,
                    "damage_mult": 0.7,
                },
                "contact_damage": False,
                "drop_chance": [
                    {"item_id": "potion_of_confusion", "chance": 0.40},
                    {"item_id": "small_health_potion", "chance": 0.20},
                ],
            },
            "bomber": {
                "visual_style": "bomber",
                "sprite_set": "MenHuman1",
                "speed": 105.0,
                "hp": 125,
                "damage": 16,
                "animation_speed": 6.0,
                "detection_range": 320.0,
                "attack_range": 35.0,
                "ai_profile": "skirmisher",
                "ai_config": {
                    "preferred_min": 120.0,
                    "preferred_max": 220.0,
                    "orbit_radius": 180.0,
                },
                "attack_profile": "bomber",
                "attack_config": {
                    "cooldown_ms": 1400,
                    "throw_range": 320.0,
                    "min_range": 90.0,
                    "bomb_speed": 260.0,
                    "bomb_range": 420.0,
                    "blast_radius": 95.0,
                    "fuse_time": 0.9,
                    "damage_mult": 1.1,
                    "knockback_force": 80.0,
                    "spread_degrees": 12.0,
                },
                "contact_damage": False,
                "drop_chance": [
                    {"item_id": "large_health_potion", "chance": 0.20},
                    {"item_id": "small_health_potion", "chance": 0.30},
                ],
            },
            "stalker": {
                "visual_style": "stalker",
                "sprite_set": "MenHuman1(Recolor)",
                "speed": 120.0,
                "hp": 110,
                "damage": 15,
                "animation_speed": 6.0,
                "detection_range": 260.0,
                "attack_range": 40.0,
                "ai_config": {
                    "memory_duration": 3.0,
                    "repath_interval": 0.5,
                },
                "attack_profile": "melee",
                "attack_config": {
                    "cooldown_ms": 900,
                    "damage_mult": 1.0,
                    "strike_range": 55.0,
                },
                "contact_damage": False,
                "drop_chance": [
                    {"item_id": "small_health_potion", "chance": 0.20},
                ],
            },
            "skirmisher": {
                "visual_style": "skirmisher",
                "sprite_set": "WomanHuman1(Recolor)",
                "speed": 140.0,
                "hp": 85,
                "damage": 10,
                "animation_speed": 7.0,
                "detection_range": 300.0,
                "attack_range": 35.0,
                "ai_config": {
                    "preferred_min": 80.0,
                    "preferred_max": 170.0,
                    "orbit_radius": 130.0,
                },
                "attack_profile": "melee",
                "attack_config": {
                    "cooldown_ms": 800,
                    "damage_mult": 1.0,
                    "strike_range": 50.0,
                },
                "contact_damage": False,
                "drop_chance": [
                    {"item_id": "small_health_potion", "chance": 0.25},
                ],
            },
            "guardian": {
                "visual_style": "guardian",
                "sprite_set": "MenHuman1",
                "speed": 100.0,
                "hp": 140,
                "damage": 18,
                "animation_speed": 5.0,
                "detection_range": 220.0,
                "attack_range": 45.0,
                "patrol_radius": 120.0,
                "ai_config": {
                    "guard_radius": 320.0,
                    "leash_slack": 90.0,
                    "patrol_wait": 0.8,
                },
                "attack_profile": "melee",
                "attack_config": {
                    "cooldown_ms": 1100,
                    "damage_mult": 1.1,
                    "strike_range": 60.0,
                    "knockback_force": 25.0,
                },
                "contact_damage": False,
                "drop_chance": [
                    {"item_id": "small_health_potion", "chance": 0.30},
                    {"item_id": "large_health_potion", "chance": 0.10},
                ],
            },
            "phantom": {
                "visual_style": "phantom",
                "sprite_set": "MenHuman1(Recolor)",
                "speed": 105.0,
                "hp": 100,
                "damage": 14,
                "animation_speed": 5.5,
                "detection_range": 260.0,
                "attack_range": 40.0,
                "ai_profile": "stalker",
                "attack_profile": "phantom",
                "attack_config": {
                    "cooldown_ms": 1400,
                    "damage_mult": 0.8,
                    "strike_range": 45.0,
                    "drain_duration": 0.8,
                    "drain_speed": 280.0,
                    "drain_heal_fraction": 0.35,
                    "drain_range": 220.0,
                    "slow_duration": 1.5,
                    "slow_factor": 0.65,
                },
                "contact_damage": False,
                "drop_chance": [
                    {"item_id": "small_health_potion", "chance": 0.25},
                    {"item_id": "large_health_potion", "chance": 0.10},
                ],
            },
            "titan": {
                "visual_style": "titan",
                "sprite_set": "MenHuman1",
                "speed": 75.0,
                "hp": 220,
                "damage": 28,
                "animation_speed": 4.5,
                "detection_range": 220.0,
                "attack_range": 50.0,
                "ai_profile": "guardian",
                "attack_profile": "titan",
                "attack_config": {
                    "cooldown_ms": 1800,
                    "charge_cooldown_ms": 3200,
                    "charge_duration": 0.9,
                    "charge_speed_mult": 2.0,
                    "stomp_damage_mult": 1.8,
                    "root_duration": 2.5,
                    "knockback_force": 45.0,
                },
                "contact_damage": True,
                "drop_chance": [
                    {"item_id": "large_health_potion", "chance": 0.90},
                    {"item_id": "small_health_potion", "chance": 1.0},
                ],
            },
            "cryomancer": {
                "visual_style": "cryomancer",
                "sprite_set": "WomanHuman1",
                "speed": 110.0,
                "hp": 85,
                "damage": 15,
                "animation_speed": 6.5,
                "detection_range": 280.0,
                "attack_range": 40.0,
                "ai_profile": "stalker",
                "attack_profile": "cryomancer",
                "attack_config": {
                    "cooldown_ms": 1100,
                    "shard_speed": 420.0,
                    "shard_range": 500.0,
                    "shard_damage_mult": 0.80,
                    "freeze_duration": 2.0,
                    "close_range": 80.0,
                    "nova_damage_mult": 0.95,
                    "spread_degrees": 6.0,
                },
                "contact_damage": False,
                "drop_chance": [
                    {"item_id": "small_health_potion", "chance": 0.30},
                    {"item_id": "large_health_potion", "chance": 0.10},
                ],
            },
            "shadowmancer": {
                "visual_style": "shadowmancer",
                "sprite_set": "WomanHuman1(Recolor)",
                "speed": 125.0,
                "hp": 75,
                "damage": 13,
                "animation_speed": 7.0,
                "detection_range": 300.0,
                "attack_range": 35.0,
                "ai_profile": "skirmisher",
                "ai_config": {
                    "preferred_min": 80.0,
                    "preferred_max": 180.0,
                    "orbit_radius": 130.0,
                },
                "attack_profile": "shadowmancer",
                "attack_config": {
                    "cooldown_ms": 1500,
                    "step_range": 260.0,
                    "step_distance": 65.0,
                    "step_attempts": 5,
                    "step_spread_degrees": 100.0,
                    "bolt_speed": 450.0,
                    "bolt_range": 480.0,
                    "bolt_damage_mult": 0.85,
                    "confuse_duration": 3.0,
                    "spread_degrees": 4.0,
                },
                "contact_damage": False,
                "drop_chance": [
                    {"item_id": "potion_of_confusion", "chance": 0.35},
                    {"item_id": "small_health_potion", "chance": 0.20},
                ],
            },
            "revenant": {
                "visual_style": "revenant",
                "sprite_set": "MenHuman1(Recolor)",
                "speed": 110.0,
                "hp": 130,
                "damage": 18,
                "animation_speed": 5.5,
                "detection_range": 250.0,
                "attack_range": 42.0,
                "ai_profile": "stalker",
                "attack_profile": "revenant",
                "attack_config": {
                    "cooldown_ms": 1000,
                    "damage_mult": 1.05,
                    "strike_range": 55.0,
                    "lifesteal_fraction": 0.30,
                    "bleed_duration": 3.0,
                    "undying_threshold": 0.20,
                    "undying_heal_fraction": 0.35,
                    "undying_immunity_ms": 2500,
                    "undying_cooldown_ms": 15000,
                },
                "contact_damage": False,
                "drop_chance": [
                    {"item_id": "large_health_potion", "chance": 0.25},
                    {"item_id": "small_health_potion", "chance": 0.40},
                ],
            },
            "molten": {
                "visual_style": "molten",
                "sprite_set": "MenHuman1",
                "speed": 100.0,
                "hp": 150,
                "damage": 20,
                "animation_speed": 5.0,
                "detection_range": 240.0,
                "attack_range": 45.0,
                "ai_profile": "guardian",
                "attack_profile": "molten",
                "attack_config": {
                    "cooldown_ms": 1200,
                    "nova_cooldown_ms": 2800,
                    "nova_radius": 100.0,
                    "nova_damage_mult": 1.1,
                    "burn_duration": 3.5,
                    "burn_dps": 6.0,
                    "charge_cooldown_ms": 3500,
                    "charge_duration": 0.6,
                    "charge_speed_mult": 2.5,
                    "charge_damage_mult": 1.3,
                },
                "contact_damage": True,
                "drop_chance": [
                    {"item_id": "large_health_potion", "chance": 0.35},
                    {"item_id": "small_health_potion", "chance": 0.50},
                ],
            },
            "stormcaller": {
                "visual_style": "stormcaller",
                "sprite_set": "WomanHuman1",
                "speed": 115.0,
                "hp": 80,
                "damage": 14,
                "animation_speed": 6.5,
                "detection_range": 300.0,
                "attack_range": 38.0,
                "ai_profile": "stalker",
                "attack_profile": "stormcaller",
                "attack_config": {
                    "cooldown_ms": 1000,
                    "bolt_speed": 500.0,
                    "bolt_range": 520.0,
                    "bolt_damage_mult": 0.9,
                    "dizzy_duration": 1.8,
                    "cast_range": 360.0,
                    "spread_degrees": 4.0,
                    "field_cooldown_ms": 3000,
                    "field_radius": 90.0,
                    "field_damage_mult": 0.8,
                },
                "contact_damage": False,
                "drop_chance": [
                    {"item_id": "small_health_potion", "chance": 0.25},
                    {"item_id": "large_health_potion", "chance": 0.10},
                ],
            },
            "plaguebearer": {
                "visual_style": "plaguebearer",
                "sprite_set": "MenHuman1(Recolor)",
                "speed": 105.0,
                "hp": 110,
                "damage": 14,
                "animation_speed": 5.5,
                "detection_range": 280.0,
                "attack_range": 40.0,
                "ai_profile": "stalker",
                "ai_config": {
                    "preferred_min": 60.0,
                    "preferred_max": 160.0,
                    "orbit_radius": 110.0,
                },
                "attack_profile": "plaguebearer",
                "attack_config": {
                    "cooldown_ms": 1200,
                    "bolt_speed": 380.0,
                    "bolt_range": 460.0,
                    "bolt_damage_mult": 0.85,
                    "poison_duration": 4.0,
                    "poison_dps": 5.5,
                    "cast_range": 340.0,
                    "spread_degrees": 6.0,
                    "nova_cooldown_ms": 3200,
                    "nova_radius": 100.0,
                    "nova_damage_mult": 1.0,
                    "nova_slow_duration": 2.0,
                    "nova_slow_factor": 0.55,
                },
                "contact_damage": False,
                "drop_chance": [
                    {"item_id": "small_health_potion", "chance": 0.30},
                    {"item_id": "potion_of_confusion", "chance": 0.15},
                ],
            },
            "chronos": {
                "visual_style": "chronos",
                "sprite_set": "MenHuman1(Recolor)",
                "speed": 120.0,
                "hp": 600,
                "damage": 25,
                "animation_speed": 6.0,
                "animation_size": (160, 160),
                "detection_range": 500.0,
                "attack_range": 70.0,
                "ai_profile": "chronos",
                "ai_config": {
                    "preferred_min": 120.0,
                    "preferred_max": 250.0,
                    "orbit_radius": 180.0,
                    "orbit_interval": 2.5,
                    "drift_cooldown": 3.0,
                    "drift_distance": 80.0,
                    "rift_cooldown": 5.0,
                    "warp_cooldown": 4.0,
                    "warp_speed_mult": 2.5,
                    "warp_duration": 0.6,
                },
                "attack_profile": "chronos",
                "attack_config": {
                    "cooldown_ms": 1200,
                    "bolt_speed": 450.0,
                    "bolt_range": 500.0,
                    "bolt_damage_mult": 0.85,
                    "slow_duration": 2.0,
                    "slow_factor": 0.5,
                    "melee_damage_mult": 1.2,
                    "melee_range": 60.0,
                    "spread_degrees": 5.0,
                    "burst_cooldown_ms": 3500,
                    "burst_radius": 100.0,
                    "burst_damage_mult": 1.0,
                    "rift_cooldown_ms": 4000,
                    "rift_distance": 150.0,
                    "storm_cooldown_ms": 6000,
                    "storm_radius": 140.0,
                    "storm_damage_mult": 1.5,
                    "freeze_duration": 2.0,
                    "enrage_speed_mult": 1.6,
                    "nova_cooldown_ms": 5000,
                    "nova_bolt_count": 8,
                    "nova_bolt_speed": 350.0,
                    "nova_bolt_range": 300.0,
                    "nova_damage_mult": 0.7,
                    "shard_cooldown_ms": 4500,
                    "shard_count": 5,
                    "shard_spread_degrees": 25.0,
                    "shard_speed": 400.0,
                    "shard_range": 400.0,
                    "shard_damage_mult": 0.6,
                    "cascade_cooldown_ms": 7000,
                    "cascade_waves": 3,
                    "cascade_bolts_per_wave": 3,
                    "cascade_speed": 380.0,
                    "cascade_range": 450.0,
                    "cascade_damage_mult": 0.5,
                    "barrage_cooldown_ms": 8000,
                    "barrage_bolt_count": 12,
                    "barrage_speed": 320.0,
                    "barrage_range": 350.0,
                    "barrage_damage_mult": 0.45,
                    "timestop_cooldown_ms": 9000,
                    "timestop_radius": 120.0,
                    "timestop_freeze_duration": 1.5,
                    "timestop_damage_mult": 0.5,
                    "wave_cooldown_ms": 5500,
                    "wave_radius": 160.0,
                    "wave_damage_mult": 0.8,
                    "rift_cooldown2_ms": 7000,
                    "rift_duration": 4.0,
                    "rift_damage_mult": 0.35,
                    "decay_cooldown_ms": 6500,
                    "decay_radius": 80.0,
                    "decay_damage_mult": 0.3,
                    "reversal_cooldown_ms": 10000,
                    "reversal_heal": 40,
                    "reversal_damage_mult": 0.6,
                },
                "contact_damage": True,
                "is_boss": True,
                "boss_name": "Chronos the Chronicler of Time",
                "drop_chance": [
                    {"item_id": "large_health_potion", "chance": 1.0},
                ],
            },
        }
        self.enemy_profile_names = list(self.enemy_profiles.keys())

        self.ENEMY_SPAWNS = {
            # "maps/test-map-1.tmx": (400, 300), # Якщо закоментувати цей рядок, ворога на старті не буде
            # Each map can declare multiple distinct enemy spawns (pos + profile).
            # Both dict-of-one and list-of-many forms are supported; tuples fall
            # back to the "stalker" profile for backward compatibility.
            "maps/test-map-2.tmx": [
                {"pos": (600, 450),   "profile": "trickster"},
                {"pos": (1500, 1250), "profile": "stalker"},
                {"pos": (3000, 1800), "profile": "brute"},
                {"pos": (3200, 400),  "profile": "phantom"},
            ],
            "maps/test-map-3.tmx": [
                {"pos": (300, 200),  "profile": "skirmisher"},
                {"pos": (900, 500),  "profile": "bomber"},
                {"pos": (1400, 800), "profile": "phantom"},
                {"pos": (2200, 1200), "profile": "chronos", "is_boss": True},
            ],
        }

        # NPC spawn positions (pixels). Tavern NPC coordinates corrected to fit map bounds
        self.NPC_SPAWNS = {
            "maps/tavern.tmx": (576, 256),
        }

        # Card-game NPC spawn positions (pixels) — separate from the merchant NPC
        self.CARD_NPC_SPAWNS = {
            "maps/tavern.tmx": (320, 320),
        }

        # Fishing NPC spawn positions (pixels) — placed near the lake
        self.FISHING_NPC_SPAWNS = {
            "maps/test-map-1.tmx": (1120, 1024),
        }

        # Mage NPC spawn positions (pixels) — placed near trees on test-map-2
        # The center of the map (cols 50-64, rows 40-54) is the lake; this
        # position is on solid ground near the upper-right detail objects.
        self.MAGE_NPC_SPAWNS = {
            "maps/test-map-2.tmx": (2240, 640),
        }

        # Maps where enemy spawning (both default and random) is disabled
        self.NO_ENEMY_SPAWN_MAPS = {"maps/tavern.tmx", "maps/test-map-1.tmx"}

        spawn_entries = self._get_spawn_entries(initial_map_path)
        if initial_map_path in self.NO_ENEMY_SPAWN_MAPS:
            spawn_entries = []
        if spawn_entries:
            first = spawn_entries[0]
            start_x, start_y = first["pos"]
            default_profile = first.get("profile")
        else:
            start_x, start_y = -5000, -5000
            default_profile = None

        self.hud = HUD(self.character, app, self.toggle_player_inventory, self.use_skill_slot, open_shop_callback=self.open_shop)

        self.enemy = self._create_enemy(start_x, start_y, profile=default_profile)

        self.enemies = [self.enemy]
        # Spawn any additional configured enemies on the starting map.
        for extra in spawn_entries[1:]:
            ex, ey = extra["pos"]
            self.enemies.append(self._create_enemy(ex, ey, profile=extra.get("profile")))
        self.items = []
        
        # Enemy spawning system
        self.enemy_spawn_timer = 0.0
        self.enemy_spawn_interval = 30.0 # seconds

        if initial_map_path in self.NPC_SPAWNS:
            npc_x, npc_y = self.NPC_SPAWNS[initial_map_path]
        else:
            npc_x, npc_y = -5000, -5000

        # NPC: provide dialog and mark as merchant for this map
        default_dialog = [
            "Hey — good to see someone around.",
            "I run a small stall: got some gear and supplies for travelers.",
            "If you want, I can open the shop and you can take a look."
        ]
        self.npc = NPC(x=npc_x, y=npc_y, sprite_set="MenHuman1", dialog_lines=default_dialog, is_merchant=True, gender='male')

        # Clamp initial NPC position to current map bounds so NPC won't be placed off-map
        try:
            if initial_map_path in self.NPC_SPAWNS and self.map.current_map and self.map.current_map.pixel_width and self.map.current_map.pixel_height:
                map_w = self.map.current_map.pixel_width
                map_h = self.map.current_map.pixel_height
                npc_w = self.npc.image.get_width()
                npc_h = self.npc.image.get_height()
                clamped_x = max(0, min(npc_x, map_w - npc_w))
                clamped_y = max(0, min(npc_y, map_h - npc_h))
                self.npc.pos = pygame.Vector2(clamped_x, clamped_y)
        except Exception:
            pass
        
        shop_items = [
            create_item("dull_sword"),
            create_item("wooden_bow"),
            create_item("apple"),
            create_item("gay_ring"),
            create_item("hand_lamp"),
            create_item("lantern"),
            create_item("small_health_potion"),
            create_item("large_health_potion"),
            create_item("large_health_potion"),
            create_item("large_health_potion"),
            create_item("potion_of_confusion"),
            create_item("moldy_bread"),
            create_item("iron_helmet"),
            create_item("iron_chestplate"),
            create_item("iron_leggings"),
            create_item("iron_boots"),
            create_item("defense_charm"),
            create_item("leather_gloves"),
            create_item("fishing_rod"),
            create_item("stone_axe"),
            create_item("iron_axe"),
            create_item("stone_pickaxe"),
            create_item("iron_pickaxe"),
            create_item("stone_hammer"),
            create_item("iron_hammer"),
            ]

        self.shop_inv = ShopInventory(self.app, shop_items)

        # ---- Card-game NPC (tavern gambler) ----
        if initial_map_path in self.CARD_NPC_SPAWNS:
            cn_x, cn_y = self.CARD_NPC_SPAWNS[initial_map_path]
        else:
            cn_x, cn_y = -5000, -5000

        self.card_npc_first_dialog = [
            "Well, well — a fresh face in the tavern!",
            "Name's Ren. I pass the time with some casino games.",
            "Care for a round of Blackjack, Roulette, or Poker? I promise I don't cheat... much."
        ]
        self.card_npc_repeat_dialog = [
            "Back again? I knew you'd come around.",
            "The tables are waiting for you.",
            "Would you like to play Blackjack, Roulette, or Poker?"
        ]
        self.card_npc_post_game_dialog = [
            "Thanks for playing! That was a fine round.",
            "Come back anytime — the deck's always shuffled."
        ]

        self.card_npc = NPC(
            x=cn_x, y=cn_y,
            sprite_set="MenHuman1(Recolor)",
            dialog_lines=self.card_npc_first_dialog,
            is_merchant=False,
            gender='male',
        )

        # Clamp card NPC to map bounds
        try:
            if initial_map_path in self.CARD_NPC_SPAWNS and self.map.current_map and self.map.current_map.pixel_width and self.map.current_map.pixel_height:
                map_w = self.map.current_map.pixel_width
                map_h = self.map.current_map.pixel_height
                cn_w = self.card_npc.image.get_width()
                cn_h = self.card_npc.image.get_height()
                cn_x = max(0, min(cn_x, map_w - cn_w))
                cn_y = max(0, min(cn_y, map_h - cn_h))
                self.card_npc.pos = pygame.Vector2(cn_x, cn_y)
        except Exception:
            pass

        # ---- Fishing NPC (woman near the lake) ----
        fishing_npc_dialog = [
            "Hello there! I come here to fish every day.",
            "The lake is full of interesting catches — have you tried?",
            "Equip a fishing rod and press F near the water to cast your line."
        ]

        if initial_map_path in self.FISHING_NPC_SPAWNS:
            fn_x, fn_y = self.FISHING_NPC_SPAWNS[initial_map_path]
        else:
            fn_x, fn_y = -5000, -5000

        self.fishing_npc = NPC(
            x=fn_x, y=fn_y,
            sprite_set="WomanHuman1",
            dialog_lines=fishing_npc_dialog,
            is_merchant=False,
            gender='female',
        )

        # Clamp fishing NPC to map bounds
        try:
            if initial_map_path in self.FISHING_NPC_SPAWNS and self.map.current_map and self.map.current_map.pixel_width and self.map.current_map.pixel_height:
                map_w = self.map.current_map.pixel_width
                map_h = self.map.current_map.pixel_height
                fn_w = self.fishing_npc.image.get_width()
                fn_h = self.fishing_npc.image.get_height()
                fn_x = max(0, min(fn_x, map_w - fn_w))
                fn_y = max(0, min(fn_y, map_h - fn_h))
                self.fishing_npc.pos = pygame.Vector2(fn_x, fn_y)
        except Exception:
            pass

        # ---- Mage NPC (Arcane Quests / Mysterium Magnum gatekeeper) ----
        if initial_map_path in self.MAGE_NPC_SPAWNS:
            mg_x, mg_y = self.MAGE_NPC_SPAWNS[initial_map_path]
        else:
            mg_x, mg_y = -5000, -5000

        self.mage_npc_first_dialog = [
            "I sense a great power within you... something ancient, something waiting.",
            "You must collect the souls of the monsters you defeat.",
            "Bring them to me, and I shall unlock the Arcane Quests — a path to harness that power."
        ]
        self.mage_npc_repeat_dialog = [
            "The winds whisper of your progress.",
            "Keep collecting monster souls. The Arcane Quests await."
        ]
        self.mage_npc_post_unlock_dialog = [
            "You have gathered the souls. I can feel their energy resonating.",
            "Now you must tap into your inner world and transform these souls into a tarot deck.",
            "This is the Mysterium Magnum — a deck of power, fate, and transformation.",
            "I shall open the way for you."
        ]
        self.mage_npc_post_unlock_repeat_dialog = [
            "The Mysterium Magnum is now open to you.",
            "Transform your collected souls into cards of destiny."
        ]

        self.mage_npc = MageNPC(
            x=mg_x, y=mg_y,
            dialog_lines=self.mage_npc_first_dialog,
            gender='female',
        )

        # Clamp mage NPC to map bounds
        try:
            if initial_map_path in self.MAGE_NPC_SPAWNS and self.map.current_map and self.map.current_map.pixel_width and self.map.current_map.pixel_height:
                map_w = self.map.current_map.pixel_width
                map_h = self.map.current_map.pixel_height
                mg_w = self.mage_npc.image.get_width()
                mg_h = self.mage_npc.image.get_height()
                mg_x = max(0, min(mg_x, map_w - mg_w))
                mg_y = max(0, min(mg_y, map_h - mg_h))
                self.mage_npc.pos = pygame.Vector2(mg_x, mg_y)
        except Exception:
            pass

        # Blackjack, Roulette & Poker game state (None when not playing)
        self.blackjack_game = None
        self.roulette_game = None
        self.poker_game = None

        # Crafting "Tempering" minigame state (None when not playing)
        self.crafting_minigame = None

        # Debug menu for spawning mobs
        self.spawn_menu = SpawnMenu(
            self.enemy_profile_names,
            on_spawn=self._debug_spawn_enemy,
            on_close=lambda: None
        )

        # Debug menu for applying effects
        effect_names = [
            name for name, obj in inspect.getmembers(effects_db, inspect.isclass)
            if issubclass(obj, effects_db.Effect) and obj is not effects_db.Effect
        ]
        effect_names.sort()
        self.effects_menu = EffectsMenu(
            effect_names,
            on_apply=self._debug_apply_effect,
            on_close=lambda: None
        )
        # Fishing minigame controller
        try:
            self.fishing = FishingController(self)
        except Exception:
            self.fishing = None

        # Guide article one-shot trigger flags
        self._triggered_guide_combat = False
        self._triggered_guide_inventory = False
        self._triggered_guide_crafting = False
        self._triggered_guide_leveling = False
        self._triggered_guide_daynight = False
        self._triggered_guide_enemies = False
        self._triggered_guide_skills = False
        self._triggered_guide_respec = False
        self._triggered_guide_final = False
        self._bestiary_encountered = set()
        self._dusk_was_reached = False
        self._kill_count = 0

        # Gathering minigame controller (chop / mine)
        try:
            self.gathering = GatheringController(self)
        except Exception:
            self.gathering = None

        # Smeltery workstation overlay (workbench + coke oven + blast furnace)
        try:
            self.smeltery = SmelteryMenu(app)
        except Exception as exc:
            logger.warning(f"Failed to initialise SmelteryMenu: {exc}")
            self.smeltery = None

        # Per-map gatherable node registries
        self.gatherables: dict[str, GatherableNodeRegistry] = {}
        try:
            self._build_gatherable_registries()
        except Exception as exc:
            logger.warning(f"Failed to build gatherable node registries: {exc}")

    def _build_gatherable_registries(self) -> None:
        try:
            from data.gatherable_nodes import load_gatherable_node_defs
        except Exception as exc:
            logger.warning(f"Could not import data.gatherable_nodes: {exc}")
            return
        try:
            definitions = load_gatherable_node_defs()
        except Exception as exc:
            logger.warning(f"load_gatherable_node_defs() failed: {exc}")
            return
        for definition in definitions:
            registry = self.gatherables.get(definition.map_path)
            if registry is None:
                registry = GatherableNodeRegistry(definition.map_path)
                self.gatherables[definition.map_path] = registry
            registry.add_def(definition)
        total = sum(len(reg.nodes) for reg in self.gatherables.values())
        logger.info(f"Loaded {total} gatherable node(s) across {len(self.gatherables)} map(s)")

    def reinit_ui(self):
        self.hud = HUD(self.character, self.app, self.toggle_player_inventory, self.use_skill_slot, open_shop_callback=self.open_shop)

        scale = cfg.ui_scale()
        slot_size = int(cfg.BASE_INV_slot_size * scale)
        border = int(cfg.BASE_INV_border * scale)

        self.MAIN_player_inv.slot_size = slot_size
        self.MAIN_player_inv.border = border
        self.MAIN_player_inv.pos_x = cfg.MAIN_INV_pos_x
        self.MAIN_player_inv.pos_y = cfg.MAIN_INV_pos_y

        self.PLAYER_inventory_equipment.slot_size = slot_size
        self.PLAYER_inventory_equipment.border = border
        self.PLAYER_inventory_equipment.pos_x = cfg.MAIN_INV_equipment_pos_x
        self.PLAYER_inventory_equipment.pos_y = cfg.MAIN_INV_equipment_pos_y

        hotbar_scale = cfg.INV_HOTBAR_SCALE * scale
        self.hotbar.slot_size = int(cfg.BASE_INV_slot_size * hotbar_scale)
        self.hotbar.border = border

        self.app.INV_manager.crafting_system.rescale()
        self.shop_inv.rescale()

        if self.app.INV_manager.current_shop_inv:
            self.MAIN_player_inv.pos_x = cfg.SCREEN_WIDTH // 2 - int(500 * scale)
            self.app.INV_manager.current_shop_inv.pos_x = cfg.SCREEN_WIDTH // 2 + int(100 * scale)
            self.app.INV_manager.current_shop_inv.pos_y = self.MAIN_player_inv.pos_y

    def toggle_player_inventory(self):
        self.app.INV_manager.toggle_inventory(self.MAIN_player_inv, self.PLAYER_inventory_equipment)
        # Guide: Inventory & Items — first inventory open
        if not self._triggered_guide_inventory:
            self._triggered_guide_inventory = True
            self.app.article_tracker.try_open(self.app, "guide", "4. Inventory & Items")

    def open_shop(self):
        try:
            self.app.INV_manager.toggle_trade(self.MAIN_player_inv, self.shop_inv, self.PLAYER_inventory_equipment)
        except Exception:
            pass

    def open_blackjack(self):
        def on_close(outcome, net_change):
            self.blackjack_game = None
            self.app.money += net_change
            if self.app.money < 0:
                self.app.money = 0
            logger.info(f"Blackjack closed: outcome={outcome}, net_change={net_change}, money now={self.app.money}")
            if net_change > 0:
                post_lines = [
                    "Thanks for playing! That was a fine round.",
                    f"You walked away {net_change} gold richer!",
                    "Come back anytime — the deck's always shuffled."
                ]
            elif net_change < 0:
                post_lines = [
                    "Thanks for playing! That was a fine round.",
                    f"Tough luck — you lost {abs(net_change)} gold.",
                    "Come back anytime — the deck's always shuffled."
                ]
            else:
                post_lines = self.card_npc_post_game_dialog
            self.app.current_dialog = Dialog(
                self.app,
                post_lines,
                on_close=lambda: setattr(self.card_npc, 'was_talked', True),
            )
        self.blackjack_game = BlackjackGame(self.app, on_close=on_close, player_money=self.app.money)

    def open_roulette(self):
        def on_close(outcome, net_change):
            self.roulette_game = None
            self.app.money += net_change
            if self.app.money < 0:
                self.app.money = 0
            logger.info(f"Roulette closed: outcome={outcome}, net_change={net_change}, money now={self.app.money}")
            if net_change > 0:
                post_lines = [
                    "Thanks for playing! That was a fine round.",
                    f"You walked away {net_change} gold richer!",
                    "Come back anytime — the wheel is always spinning."
                ]
            elif net_change < 0:
                post_lines = [
                    "Thanks for playing! That was a fine round.",
                    f"Tough luck — you lost {abs(net_change)} gold.",
                    "Come back anytime — the wheel is always spinning."
                ]
            else:
                post_lines = [
                    "Thanks for playing! That was a fine round.",
                    "Come back anytime — the wheel is always spinning."
                ]
            self.app.current_dialog = Dialog(
                self.app,
                post_lines,
                on_close=lambda: setattr(self.card_npc, 'was_talked', True),
            )
        self.roulette_game = RouletteGame(self.app, on_close=on_close, player_money=self.app.money)

    def open_poker(self):
        def on_close(outcome, net_change):
            self.poker_game = None
            self.app.money += net_change
            if self.app.money < 0:
                self.app.money = 0
            logger.info(f"Poker closed: outcome={outcome}, net_change={net_change}, money now={self.app.money}")
            if net_change > 0:
                post_lines = [
                    "Thanks for playing! That was a fine round.",
                    f"You walked away {net_change} gold richer!",
                    "Come back anytime — the cards are always dealt."
                ]
            elif net_change < 0:
                post_lines = [
                    "Thanks for playing! That was a fine round.",
                    f"Tough luck — you lost {abs(net_change)} gold.",
                    "Come back anytime — the cards are always dealt."
                ]
            else:
                post_lines = [
                    "Thanks for playing! That was a fine round.",
                    "Come back anytime — the cards are always dealt."
                ]
            self.app.current_dialog = Dialog(
                self.app,
                post_lines,
                on_close=lambda: setattr(self.card_npc, 'was_talked', True),
            )
        self.poker_game = PokerGame(self.app, on_close=on_close, player_money=self.app.money)

    def open_crafting_minigame(self, crafted_item, consume_callback, smelting_level: int = 1):
        """Launch the Tempering timing minigame for a freshly crafted item.

        ``crafted_item`` is the already-tiered item produced by
        :meth:`src.inventory.system.CraftingGrid.check_recipes`.  The
        minigame may further bias the tier up or down based on the
        player's three hammer strikes.  On close, ``consume_callback``
        is invoked with the final item and the XP multiplier; it is
        expected to clear the crafting grid, place the item in the
        player's cursor, and award the (multiplied) smelting XP.
        """
        def on_close(final_item, xp_multiplier, outcome):
            self.crafting_minigame = None
            logger.info(
                f"Crafting minigame closed: outcome={outcome}, "
                f"final_tier={getattr(final_item, 'tier', 'fine')}, "
                f"xp_multiplier={xp_multiplier}"
            )
            try:
                consume_callback(final_item, xp_multiplier)
            except Exception as exc:
                logger.warning(f"crafting minigame consume callback failed: {exc}")
        self.crafting_minigame = CraftingMinigame(
            self.app,
            crafted_item,
            on_close=on_close,
            smelting_level=smelting_level,
        )

    def _get_card_npc_dialog(self):
        if not self.card_npc.was_talked:
            return self.card_npc_first_dialog
        return self.card_npc_repeat_dialog

    def _get_mage_npc_dialog(self):
        """Pick the right mage NPC dialog lines based on the current unlock state."""
        if not self.app.arcane_quests_unlocked:
            # First conversation: senses power, tells player to collect souls
            if not self.mage_npc.was_talked:
                return self.mage_npc_first_dialog
            return self.mage_npc_repeat_dialog
        elif not self.app.mysterium_magnum_unlocked:
            # Arcane quests unlocked, but Mysterium Magnum not yet
            # Check if player has at least 1 purple star
            if getattr(self.app, 'purple_stars', 0) >= 1:
                if not getattr(self, '_mage_mysterium_dialog_shown', False):
                    self._mage_mysterium_dialog_shown = True
                    return self.mage_npc_post_unlock_dialog
            return self.mage_npc_post_unlock_repeat_dialog if getattr(self, '_mage_mysterium_dialog_shown', False) else self.mage_npc_post_unlock_repeat_dialog
        else:
            # Both unlocked
            return self.mage_npc_post_unlock_repeat_dialog

    def use_skill_slot(self, slot_index):
        mouse_screen_pos = pygame.mouse.get_pos()
        camera_offset = self._get_camera_offset()
        mouse_world_pos = pygame.Vector2(mouse_screen_pos) + camera_offset
        player_center = self.character.get_center()
        aim_direction = mouse_world_pos - player_center
        if aim_direction.length_squared() == 0:
            aim_direction = self.character.get_forward_direction()
        return self.character.use_skill_from_slot(slot_index, aim_direction=aim_direction)

    # ------------------------------------------------------------------ #
    # Smeltery workstation helpers                                        #
    # ------------------------------------------------------------------ #

    SMELTERY_TILE_PROPERTY = "Is_smeltery_workstation"
    SMELTERY_INTERACT_RADIUS = 48.0

    def _is_smeltery_tile(self, world_pos):
        """Return True if the map tile at ``world_pos`` carries the
        smeltery-workstation custom property."""
        try:
            if not getattr(self, "map", None) or not getattr(self.map, "current_map", None):
                return False
            tmx_map = self.map.current_map
            tmx = getattr(tmx_map, "tmxdata", None) or getattr(tmx_map, "get_tmx_data", lambda: None)()
            if not tmx:
                return False
            tile_x = int(world_pos.x // tmx.tilewidth)
            tile_y = int(world_pos.y // tmx.tileheight)
            for layer in tmx.layers:
                if not isinstance(layer, pytmx.TiledTileLayer):
                    continue
                try:
                    gid = layer.data[tile_y][tile_x]
                except (IndexError, TypeError):
                    continue
                if not gid:
                    continue
                tile_properties = tmx.get_tile_properties_by_gid(gid)
                if not tile_properties:
                    continue
                val = tile_properties.get(self.SMELTERY_TILE_PROPERTY)
                if isinstance(val, str):
                    if val.strip().lower() in ("true", "1", "yes"):
                        return True
                elif val:
                    return True
        except Exception:
            pass
        return False

    def _find_nearby_smeltery_tile(self):
        """Return the world-space position of the closest smeltery
        tile within :pyattr:`SMELTERY_INTERACT_RADIUS`, or ``None`` if
        the player is not standing near one."""
        try:
            tmx_map = getattr(self.map, "current_map", None)
            if not tmx_map:
                return None
            tmx = getattr(tmx_map, "tmxdata", None) or tmx_map.get_tmx_data()
            if not tmx:
                return None
            tile_w = tmx.tilewidth
            tile_h = tmx.tileheight
            center = self.character.get_center()
            cx = int(center.x // tile_w)
            cy = int(center.y // tile_h)
            r = 2
            best_pos = None
            best_dist = None
            for ty in range(max(0, cy - r), cy + r + 1):
                for tx in range(max(0, cx - r), cx + r + 1):
                    world_x = tx * tile_w + tile_w // 2
                    world_y = ty * tile_h + tile_h // 2
                    if self._is_smeltery_tile(pygame.Vector2(world_x, world_y)):
                        d = (world_x - center.x) ** 2 + (world_y - center.y) ** 2
                        if best_dist is None or d < best_dist:
                            best_dist = d
                            best_pos = pygame.Vector2(world_x, world_y)
            if best_pos is None:
                return None
            if best_dist is not None and best_dist > (self.SMELTERY_INTERACT_RADIUS ** 2):
                return None
            return best_pos
        except Exception:
            return None

    def _draw_smeltery_hint(self, screen, camera_offset):
        """Show a floating 'Press E to use Smeltery' hint above the
        nearest smeltery tile when the player is in range."""
        if not getattr(self, "smeltery", None) or self.smeltery.is_open:
            return
        tile_pos = self._find_nearby_smeltery_tile()
        if tile_pos is None:
            return
        screen_x = int(tile_pos.x - camera_offset.x)
        screen_y = int(tile_pos.y - camera_offset.y)
        font = cfg.tooltip_font_CREDITS
        text = font.render(_("Press E to use Smeltery"), True, (255, 240, 200))
        shadow = font.render(_("Press E to use Smeltery"), True, (0, 0, 0))
        text_rect = text.get_rect(midbottom=(screen_x, screen_y - 8))
        # Soft backdrop pill for legibility.
        pad_x = int(8 * cfg.ui_scale())
        pad_y = int(4 * cfg.ui_scale())
        bg_rect = text_rect.inflate(pad_x * 2, pad_y * 2)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (0, 0, 0, 160), bg_surf.get_rect(), border_radius=6)
        screen.blit(bg_surf, bg_rect.topleft)
        screen.blit(shadow, (text_rect.x + 1, text_rect.y + 1))
        screen.blit(text, text_rect)

    def _update_projectiles(self, dt):
        if not self.projectiles:
            return

        for projectile in self.projectiles:
            projectile.update(dt, self.obstacles, self.enemies)

        self.projectiles = [projectile for projectile in self.projectiles if projectile.alive]

    def _update_enemy_projectiles(self, dt):
        if not self.enemy_projectiles:
            return

        for projectile in self.enemy_projectiles:
            projectile.update(dt, self.obstacles, self.character)

        self.enemy_projectiles = [projectile for projectile in self.enemy_projectiles if projectile.alive]

    def _rebuild_nav_grid(self):
        tmx_data = self.map.current_map.get_tmx_data()
        if not tmx_data:
            self.nav_grid = None
            return
        self.nav_grid = NavGrid.from_tmx(tmx_data, self.obstacles)

    def _format_game_time(self) -> str:
        hours = int(self.game_time_seconds // 3600) % 24
        minutes = int((self.game_time_seconds % 3600) // 60)
        return f"{hours:02d}:{minutes:02d}"

    def is_daytime(self) -> bool:
        return self.DAY_START <= self.game_time_seconds < self.NIGHT_START

    def _update_game_time(self, dt: float):
        was_day = self.is_daytime()
        self.game_time_seconds = (self.game_time_seconds + dt * self.GAME_SECONDS_PER_REAL_SECOND) % self.GAME_DAY_SECONDS
        # Guide: Day & Night Cycle — first time dusk/night is reached
        if not self._triggered_guide_daynight and not was_day and not self.is_daytime():
            self._triggered_guide_daynight = True
            self.app.article_tracker.try_open(self.app, "guide", "7. Day & Night Cycle")

        self.day_night.update(dt, self.game_time_seconds, self.GAME_DAY_SECONDS)

        self.app.profiler.set_gauge("game_time", self._format_game_time())

    def _get_spawn_entries(self, map_path: str) -> list[dict]:
        """
        Normalize the ENEMY_SPAWNS entry for a map into a list of
        {"pos": (x, y), "profile": "name"} dicts.

        Supports three legacy forms:
          - list of dicts: returned as-is
          - single dict: wrapped in a one-element list
          - (x, y) tuple: wrapped with the default "stalker" profile
        Returns an empty list if the map has no configured spawns.
        """
        spawn = self.ENEMY_SPAWNS.get(map_path)
        if not spawn:
            return []
        if isinstance(spawn, list):
            return [entry for entry in spawn if entry]
        if isinstance(spawn, dict):
            return [spawn]
        return [{"pos": spawn, "profile": "stalker"}]

    def _get_camera_offset(self) -> pygame.Vector2:
        viewport_width, viewport_height = self.app.screen.get_size()

        map_width = viewport_width
        map_height = viewport_height
        if self.map.current_map and self.map.current_map.pixel_width and self.map.current_map.pixel_height:
            map_width = self.map.current_map.pixel_width
            map_height = self.map.current_map.pixel_height

        camera_x = int(self.character.get_center().x - viewport_width / 2)
        camera_y = int(self.character.get_center().y - viewport_height / 2)

        # If the map is larger than the viewport, clamp camera within map bounds.
        # If the map is smaller than the viewport on an axis, center the map on that axis.
        if map_width >= viewport_width:
            max_x = map_width - viewport_width
            camera_x = max(0, min(camera_x, int(max_x)))
        else:
            # center map horizontally: negative camera offset will cause map to be drawn centered
            camera_x = int((map_width - viewport_width) / 2)

        if map_height >= viewport_height:
            max_y = map_height - viewport_height
            camera_y = max(0, min(camera_y, int(max_y)))
        else:
            # center map vertically
            camera_y = int((map_height - viewport_height) / 2)

        return pygame.Vector2(camera_x, camera_y)

    def _make_patrol_points(self, center: pygame.Vector2, radius: float) -> list[tuple[float, float]]:
        return [
            (center.x - radius, center.y - radius),
            (center.x + radius, center.y - radius),
            (center.x + radius, center.y + radius),
            (center.x - radius, center.y + radius),
        ]

    def get_light_sources(self) -> list:
        """Return a list of light sources in screen coordinates.

        Each source is a dict: { 'pos': (x,y), 'radius': int, 'intensity': float }
        The Game computes camera offset and converts world positions to screen space.
        Only returns lights during night/dusk/dawn — illumination turns on at night.
        """
        if self.is_daytime():
            return []
        lights = []
        try:
            camera = self._get_camera_offset()
            player_center = self.character.get_center()
            # Lantern: emit light when the lantern is in the active hotbar slot
            try:
                hb = getattr(self, 'hotbar', None)
                if hb:
                    slot_data = hb.items[hb.active_slot_index][0]
                    if slot_data:
                        held_item = slot_data[0] if isinstance(slot_data, (list, tuple)) else slot_data
                        if getattr(held_item, 'emits_light', False):
                            radius = getattr(held_item, 'light_radius', 160)
                            intensity = getattr(held_item, 'intensity', 0.9)

                            # Check if a LightRing is equipped in the ring slot
                            try:
                                eq = getattr(self, 'PLAYER_inventory_equipment', None)
                                if eq:
                                    for ex in range(eq.columns):
                                        for ey in range(eq.rows):
                                            eq_slot = eq.items[ex][ey]
                                            if eq_slot:
                                                eq_item = eq_slot[0] if isinstance(eq_slot, (list, tuple)) else eq_slot
                                                if isinstance(eq_item, LightRing):
                                                    radius += getattr(eq_item, 'light_radius_bonus', 0)
                                                    intensity += getattr(eq_item, 'light_intensity_bonus', 0)
                            except Exception:
                                pass

                            screen_pos = (int(player_center.x - camera.x), int(player_center.y - camera.y))
                            lights.append({
                                'pos': screen_pos,
                                'radius': int(radius),
                                'intensity': float(min(intensity, 2.0)),
                            })
            except Exception:
                pass

            # LightRing: emits its own light when equipped in ring slot
            try:
                eq = getattr(self, 'PLAYER_inventory_equipment', None)
                if eq:
                    for ex in range(eq.columns):
                        for ey in range(eq.rows):
                            eq_slot = eq.items[ex][ey]
                            if eq_slot:
                                eq_item = eq_slot[0] if isinstance(eq_slot, (list, tuple)) else eq_slot
                                if isinstance(eq_item, LightRing) and getattr(eq_item, 'emits_light', False):
                                    screen_pos = (int(player_center.x - camera.x), int(player_center.y - camera.y))
                                    lights.append({
                                        'pos': screen_pos,
                                        'radius': int(getattr(eq_item, 'light_radius', 160)),
                                        'intensity': float(getattr(eq_item, 'light_intensity', 0.6)),
                                    })
            except Exception:
                pass


            # GayRing: emits its own soft rainbow light when equipped in ring slot
            from src.items.items import GayRing
            try:
                eq = getattr(self, 'PLAYER_inventory_equipment', None)
                if eq:
                    for ex in range(eq.columns):
                        for ey in range(eq.rows):
                            eq_slot = eq.items[ex][ey]
                            if eq_slot:
                                eq_item = eq_slot[0] if isinstance(eq_slot, (list, tuple)) else eq_slot
                                if isinstance(eq_item, GayRing) and getattr(eq_item, 'emits_light', False):
                                    screen_pos = (int(player_center.x - camera.x), int(player_center.y - camera.y))
                                    lights.append({
                                        'pos': screen_pos,
                                        'radius': int(getattr(eq_item, 'light_radius', 130)),
                                        'intensity': float(getattr(eq_item, 'light_intensity', 1.6)),
                                        'full_360': True,
                                    })
            except Exception:
                pass

            # Optional: existing dropped items that emit light
            for it in getattr(self, 'items', []):
                try:
                    if getattr(it, 'emits_light', False):
                        world_pos = pygame.Vector2(getattr(it, 'pos', it.get('pos', pygame.Vector2(0,0))))
                        screen_pos = (int(world_pos.x - camera.x), int(world_pos.y - camera.y))
                        lights.append({'pos': screen_pos, 'radius': int(getattr(it, 'light_radius', 120)), 'intensity': float(getattr(it, 'intensity', 0.8))})
                except Exception:
                    pass

            # Window illumination: windows emit soft light at night.
            # The warm visual glow is pre-baked on the map layer (Map._window_glow);
            # these light sources only punch subtle holes in the night overlay.
            # Skip for interior maps (e.g. tavern) where windows are on internal walls.
            _NO_WINDOW_LIGHT_MAPS = {"maps/tavern.tmx"}
            try:
                game_map = getattr(self, 'map', None)
                if game_map and self.current_map_path not in _NO_WINDOW_LIGHT_MAPS:
                    window_positions = game_map.get_window_positions()
                    for wx, wy in window_positions:
                        screen_pos = (int(wx - camera.x), int(wy - camera.y))
                        lights.append({
                            'pos': screen_pos,
                            'radius': 100,
                            'intensity': 0.7,
                            'full_360': True,
                        })
            except Exception:
                pass
        except Exception:
            pass
        return lights

    def _create_enemy(self, x: float, y: float, profile: str | None = None) -> Enemy:
        profile_name = profile or random.choice(self.enemy_profile_names)
        if profile_name not in self.enemy_profiles:
            profile_name = "stalker"

        settings = self.enemy_profiles[profile_name]
        ai_profile = settings.get("ai_profile", profile_name)
        attack_profile = settings.get("attack_profile")
        attack_controller = None
        if attack_profile:
            attack_controller = build_attack_controller(attack_profile, settings.get("attack_config"))
        contact_damage = settings.get("contact_damage", True)
        visual_style = settings.get("visual_style")
        animations = None
        if visual_style:
            animations = build_monster_animations(visual_style, (85, 85))
        sprite_set = settings.get("sprite_set", "MenHuman1(Recolor)")
        patrol_points = settings.get("patrol_points")
        if patrol_points is None and profile_name == "guardian":
            radius = float(settings.get("patrol_radius", 120.0))
            patrol_points = self._make_patrol_points(pygame.Vector2(x, y), radius)

        is_boss = settings.get("is_boss", False)
        anim_size = settings.get("animation_size", (85, 85))
        if is_boss:
            boss_name = settings.get("boss_name", "Boss")
            if attack_profile:
                attack_controller = build_boss_attack_controller(attack_profile, settings.get("attack_config"))
            animations = None
            if visual_style:
                animations = build_boss_animations(visual_style, anim_size)
            enemy = Boss(
                x=x, y=y, sprite_set=sprite_set,
                speed=settings["speed"], hp=settings["hp"], damage=settings["damage"],
                animation_size=anim_size, animation_speed=settings.get("animation_speed", 6.0),
                detection_range=settings.get("detection_range", 250.0),
                attack_range=settings.get("attack_range", 40.0),
                boss_name=boss_name,
                patrol_points=patrol_points, ai_profile=ai_profile,
                ai_config=settings.get("ai_config"), animations=animations,
                attack_controller=attack_controller, contact_damage=contact_damage,
                visual_style=visual_style,
                intro_trigger_distance=450.0,
            )
        else:
            enemy = Enemy(
                x=x, y=y, sprite_set=sprite_set,
                speed=settings["speed"], hp=settings["hp"], damage=settings["damage"],
                animation_size=anim_size, animation_speed=settings.get("animation_speed", 6.0),
                detection_range=settings.get("detection_range", 250.0),
                attack_range=settings.get("attack_range", 40.0),
                patrol_points=patrol_points, ai_profile=ai_profile,
                ai_config=settings.get("ai_config"), animations=animations,
                attack_controller=attack_controller, contact_damage=contact_damage,
                visual_style=visual_style,
            )
        enemy.target_entity = self.character
        enemy.profile_name = profile_name
        if isinstance(enemy, Boss):
            try:
                screen_w, screen_h = pygame.display.get_surface().get_size()
                enemy.set_screen_size((screen_w, screen_h))
            except Exception:
                pass
        return enemy

    def spawn_random_enemy(self):
        if not self.map.current_map or self.map.current_map.pixel_width == 0:
            return

        map_w = self.map.current_map.pixel_width
        map_h = self.map.current_map.pixel_height
        
        # Try 10 times to find a valid position
        for _ in range(10):
            x = random.randint(50, map_w - 50)
            y = random.randint(50, map_h - 50)
            pos = pygame.Vector2(x, y)
            
            # Check distance to player (must be at least 400 pixels away)
            pdiff = pos - self.character.pos
            if pdiff.length_squared() < 400 * 400:
                continue
                
            # Check collision with walls
            # Using approximate size for enemy feet/hitbox
            rect = pygame.Rect(x, y, 40, 20) 
            collides = False
            for wall in self.obstacles:
                if rect.colliderect(wall):
                    collides = True
                    break

            if self.nav_grid and not self.nav_grid.is_walkable(self.nav_grid.world_to_cell(pos)):
                collides = True
            
            if not collides:
                # Spawn enemy
                new_enemy = self._create_enemy(x, y)
                self.enemies.append(new_enemy)
                logger.info(f"Spawned new enemy at ({x}, {y})")
                break

    def _debug_spawn_enemy(self, profile_name):
        offset_x = 100
        spawn_x = self.character.pos.x + offset_x
        spawn_y = self.character.pos.y
        new_enemy = self._create_enemy(spawn_x, spawn_y, profile=profile_name)
        self.enemies.append(new_enemy)
        logger.info(f"[DEBUG] Spawned {profile_name} at ({spawn_x}, {spawn_y})")

    def _debug_apply_effect(self, effect_name, duration):
        """
        Instantiate an effect by name and attach it to the player character.
        Uses simple fallbacks for constructors that require an extra numeric arg.
        """
        cls = getattr(effects_db, effect_name, None)
        if cls is None:
            logger.warning(f"[DEBUG] Unknown effect: {effect_name}")
            return
        try:
            eff = cls(duration)
        except TypeError:
            # Try common fallback: pass a single extra numeric parameter (1.0)
            try:
                eff = cls(duration, 1.0)
            except Exception as e:
                logger.exception(f"[DEBUG] Failed to instantiate effect {effect_name}: {e}")
                return

        # Attach to whichever list the Character uses for effects
        if hasattr(self.character, "active_effects"):
            self.character.active_effects.append(eff)
        elif hasattr(self.character, "effects"):
            self.character.effects.append(eff)
        else:
            # last resort: create active_effects container
            self.character.active_effects = [eff]

        logger.info(f"[DEBUG] Applied effect {effect_name} duration={duration}s to player")

    def _get_drop_chance_for_enemy(self, enemy: "Enemy") -> list[dict]:
        """
        Look up the drop table for a given enemy based on its AI profile.

        Returns a list of drop entries (``{"item_id": str, "chance": float}``).
        If the enemy has no profile or no ``drop_chance`` entry configured,
        returns an empty list (no drops).
        """
        if enemy is None:
            return []
        profile_name = getattr(enemy, "ai_profile", None)
        if not profile_name:
            return []
        settings = self.enemy_profiles.get(profile_name, {})
        return settings.get("drop_chance", []) or []

    def _drop_enemy_loot(self, enemy: "Enemy") -> None:
        """
        Roll each configured drop for the given enemy and spawn matching
        ``DroppedItem`` instances near the enemy's death position.

        Drops are configured per-archetype in :pyattr:`enemy_profiles` under
        the ``drop_chance`` key. Each entry has:
          - ``item_id`` (str): the item id to look up via ``create_item``.
          - ``chance``  (float): probability in [0, 1] of the drop firing.
          - ``amount``  (int, optional): stack size for the drop (defaults to 1).

        Multiple entries can fire independently in a single kill, so a single
        enemy can drop several different items at once.
        """
        from src.entities.dropped_item import DroppedItem

        drop_entries = self._get_drop_chance_for_enemy(enemy)
        if not drop_entries:
            return

        # Anchor the drops near the enemy's feet (centered on its hitbox bottom).
        base_x, base_y = enemy.get_rect().center

        placed = 0
        for entry in drop_entries:
            if not isinstance(entry, dict):
                continue
            item_id = entry.get("item_id")
            if not item_id:
                continue
            chance = float(entry.get("chance", 0.0))
            if chance <= 0.0:
                continue
            if random.random() > chance:
                continue
            amount = int(entry.get("amount", 1))
            if amount <= 0:
                amount = 1

            item_obj = create_item(item_id)
            if item_obj is None:
                logger.warning(f"Drop skipped: could not create item '{item_id}'")
                continue

            # Spread drops slightly so multiple items don't fully overlap.
            spread = 18
            offset_x = random.randint(-spread, spread)
            offset_y = random.randint(-spread // 2, spread // 2)
            drop = DroppedItem(base_x + offset_x, base_y + offset_y, item_obj, amount)
            self.items.append(drop)
            placed += 1
            logger.info(
                f"Enemy '{getattr(enemy, 'ai_profile', 'unknown')}' dropped "
                f"{amount}x {item_id} at ({base_x + offset_x}, {base_y + offset_y})"
            )

        if placed == 0:
            logger.debug(f"Enemy '{getattr(enemy, 'ai_profile', 'unknown')}' had drop_chance entries but none rolled.")

    def _finish_intro(self):
        """Callback to finish the intro sequence and unlock the game."""
        self.intro_played = True
        self._intro_sequence_active = False

    def update(self, dt):
        # Intro Sequence for test-map-1
        if self.current_map_path == "maps/test-map-1.tmx" and not getattr(self, "intro_played", False) and not getattr(self, "_intro_sequence_active", False):
            self._intro_sequence_active = True
            
            # Set player lying down (facing down, frame 0)
            self.character.direction = "down"
            self.character.frame_index = 0
            self.character.image = self.character.animations["down"][0]

            dialog_lines = [
                '"Arise, Chosen One."',
                '"I sense the latent magic humming in your blood. You have been selected for a sacred mission."',
                '"Far to the east, a great dragon slumbers in a mountain cave. You must slay it, or the realm will burn."'
            ]
            self.app.current_dialog = Dialog(self.app, dialog_lines, on_close=self._finish_intro)

        tr = self.app.article_tracker

        # Guide intro — only on the very first-ever game start
        if not self.app.guide_intro_shown:
            self.app.guide_intro_shown = True
            SaveManager.save_settings(self.app)
            tr.try_open(self.app, "guide", "1. Movement & Navigation")

        switched_map_path = self.map.update(self.character)

        if switched_map_path:
            self.current_map_path = switched_map_path
            logger.info(f"Map switched to {switched_map_path}. Respawning enemy...")
            self.obstacles = self.map.get_obstacles()
            self._rebuild_nav_grid()
            
            # Reset enemies list and spawn default one if needed
            self.enemies = []
            
            spawn_entries = self._get_spawn_entries(switched_map_path)
            if switched_map_path not in self.NO_ENEMY_SPAWN_MAPS and spawn_entries:
                for entry in spawn_entries:
                    new_x, new_y = entry["pos"]
                    profile = entry.get("profile")
                    self.enemies.append(self._create_enemy(new_x, new_y, profile=profile))

            if switched_map_path in self.NPC_SPAWNS:
                    npc_x, npc_y = self.NPC_SPAWNS[switched_map_path]
                    # Clamp NPC to the new map bounds so it is visible
                    try:
                        if self.map.current_map and self.map.current_map.pixel_width and self.map.current_map.pixel_height:
                            map_w = self.map.current_map.pixel_width
                            map_h = self.map.current_map.pixel_height
                            npc_w = self.npc.image.get_width()
                            npc_h = self.npc.image.get_height()
                            npc_x = max(0, min(npc_x, map_w - npc_w))
                            npc_y = max(0, min(npc_y, map_h - npc_h))
                    except Exception:
                        pass
                    self.npc.pos = pygame.Vector2(npc_x, npc_y)
                    logger.info(f"Placed NPC for map {switched_map_path} at ({npc_x},{npc_y})")
            else:
                self.npc.pos = pygame.Vector2(-5000, -5000)
                logger.info(f"No NPC spawn for map {switched_map_path}; hiding NPC")

            # Place card-game NPC on the new map (or hide if not present)
            if switched_map_path in self.CARD_NPC_SPAWNS:
                cn_x, cn_y = self.CARD_NPC_SPAWNS[switched_map_path]
                try:
                    if self.map.current_map and self.map.current_map.pixel_width and self.map.current_map.pixel_height:
                        map_w = self.map.current_map.pixel_width
                        map_h = self.map.current_map.pixel_height
                        cn_w = self.card_npc.image.get_width()
                        cn_h = self.card_npc.image.get_height()
                        cn_x = max(0, min(cn_x, map_w - cn_w))
                        cn_y = max(0, min(cn_y, map_h - cn_h))
                except Exception:
                    pass
                self.card_npc.pos = pygame.Vector2(cn_x, cn_y)
                logger.info(f"Placed card NPC for map {switched_map_path} at ({cn_x},{cn_y})")
            else:
                self.card_npc.pos = pygame.Vector2(-5000, -5000)
                logger.info(f"No card NPC spawn for map {switched_map_path}; hiding card NPC")

            # Place fishing NPC on the new map (or hide if not present)
            if switched_map_path in self.FISHING_NPC_SPAWNS:
                fn_x, fn_y = self.FISHING_NPC_SPAWNS[switched_map_path]
                try:
                    if self.map.current_map and self.map.current_map.pixel_width and self.map.current_map.pixel_height:
                        map_w = self.map.current_map.pixel_width
                        map_h = self.map.current_map.pixel_height
                        fn_w = self.fishing_npc.image.get_width()
                        fn_h = self.fishing_npc.image.get_height()
                        fn_x = max(0, min(fn_x, map_w - fn_w))
                        fn_y = max(0, min(fn_y, map_h - fn_h))
                except Exception:
                    pass
                self.fishing_npc.pos = pygame.Vector2(fn_x, fn_y)
                logger.info(f"Placed fishing NPC for map {switched_map_path} at ({fn_x},{fn_y})")
            else:
                self.fishing_npc.pos = pygame.Vector2(-5000, -5000)
                logger.info(f"No fishing NPC spawn for map {switched_map_path}; hiding fishing NPC")

            # Place mage NPC on the new map (or hide if not present)
            if switched_map_path in self.MAGE_NPC_SPAWNS:
                mg_x, mg_y = self.MAGE_NPC_SPAWNS[switched_map_path]
                try:
                    if self.map.current_map and self.map.current_map.pixel_width and self.map.current_map.pixel_height:
                        map_w = self.map.current_map.pixel_width
                        map_h = self.map.current_map.pixel_height
                        mg_w = self.mage_npc.image.get_width()
                        mg_h = self.mage_npc.image.get_height()
                        mg_x = max(0, min(mg_x, map_w - mg_w))
                        mg_y = max(0, min(mg_y, map_h - mg_h))
                except Exception:
                    pass
                self.mage_npc.pos = pygame.Vector2(mg_x, mg_y)
                logger.info(f"Placed mage NPC for map {switched_map_path} at ({mg_x},{mg_y})")
            else:
                self.mage_npc.pos = pygame.Vector2(-5000, -5000)
                logger.info(f"No mage NPC spawn for map {switched_map_path}; hiding mage NPC")

        self.map.update_animation(dt)

        # Enemy Spawning Logic
        self._update_game_time(dt)

        self.enemy_spawn_timer += dt
        if self.enemy_spawn_timer >= self.enemy_spawn_interval:
            self.enemy_spawn_timer = 0
            # Skip periodic/random spawns on maps where spawning is disabled
            if self.current_map_path not in self.NO_ENEMY_SPAWN_MAPS:
                self.spawn_random_enemy()

        self.player_combat.sync_weapon_stats()

        # Boss intro trigger check
        intro_active = False
        screen_size = getattr(self, '_screen_size', (1280, 720))
        for enemy in self.enemies:
            if isinstance(enemy, Boss) and not enemy.intro_triggered:
                enemy.check_intro_trigger(self.character.pos, screen_size)
            if isinstance(enemy, Boss) and enemy.is_intro_active():
                intro_active = True
                # Freeze player position during intro
                enemy.intro.update(dt)
                if enemy.intro.finished:
                    intro_active = False

        if not intro_active:
            self.character.update(dt, self.collision_handler, self.obstacles)

        mouse_pos = pygame.mouse.get_pos()
        camera_offset = self._get_camera_offset()
        mouse_world_pos = pygame.Vector2(mouse_pos) + camera_offset
        
        aim_dir = mouse_world_pos - self.character.get_center()
        
        if aim_dir.length_squared() > 0:
            if abs(aim_dir.x) > abs(aim_dir.y):
                self.character.direction = "side"
                self.character.flip = aim_dir.x < 0
            else:
                self.character.direction = "down" if aim_dir.y > 0 else "up"
            
            self.character.image = self.character.animations[self.character.direction][self.character.frame_index]
            
        now_ms = pygame.time.get_ticks()
        attack_context = AttackContext(
            dt=dt,
            player=self.character,
            obstacles=self.obstacles,
            projectiles=self.enemy_projectiles,
            now_ms=now_ms,
        )
        # Update enemies with LOD: skip heavy updates for distant enemies
        LOD_DISTANCE = 800.0
        lod_sq = LOD_DISTANCE * LOD_DISTANCE
        player_pos = self.character.pos
        for enemy in self.enemies:
            ediff = enemy.pos - player_pos
            active = ediff.length_squared() <= lod_sq
            enemy.update(dt, self.collision_handler, self.obstacles, self.nav_grid, attack_context, active=active)

        self._update_projectiles(dt)
        self._update_enemy_projectiles(dt)

        for item in self.items:
            if hasattr(item, "update"):
                item.update(dt, self.obstacles)
        # Flame Shield: deal damage to nearby enemies
        if self.character.flame_shield_active:
            self._apply_flame_shield_damage(dt)

        # Ice Armor: slow nearby enemies
        if self.character.ice_armor_active:
            self._apply_ice_armor_slow(dt)

        # GayRing: check if equipped in ring slot and toggle rainbow aura
        from src.items.items import GayRing
        try:
            eq = getattr(self, 'PLAYER_inventory_equipment', None)
            gay_ring_equipped = False
            if eq:
                for ex in range(eq.columns):
                    for ey in range(eq.rows):
                        eq_slot = eq.items[ex][ey]
                        if eq_slot:
                            eq_item = eq_slot[0] if isinstance(eq_slot, (list, tuple)) else eq_slot
                            if isinstance(eq_item, GayRing):
                                gay_ring_equipped = True
                                break
                    if gay_ring_equipped:
                        break
            self.character.rainbow_aura_active = gay_ring_equipped
        except Exception:
            pass

        # Regeneration passive
        if self.character.regeneration:
            self._apply_regeneration(dt)

        # Update summoned spirits
        self._update_spirits(dt)

        self.collision_handler.check_interactions(
            self.character, self.enemies, self.items
        )

        # Remove dead enemies
        for enemy in self.enemies[:]:
            if enemy.is_dead():
                logger.info("Enemy defeated!")
                self._kill_count += 1
                self.app.achievement_manager.unlock("first_blood")
                self.app.achievement_manager.add_progress("exterminator", 1, 50)
                self.app.achievement_manager.add_progress("monster_hunter", 1, 200)

                # Bestiary: open article for this enemy type
                vs = getattr(enemy, "visual_style", None) or getattr(enemy, "ai_profile", "")
                bestiary_title = {
                    "brute": "The Brute", "venomous": "The Venomous",
                    "arcanist": "The Arcanist", "trickster": "The Trickster",
                    "bomber": "The Bomber", "stalker": "The Stalker",
                    "skirmisher": "The Skirmisher", "guardian": "The Guardian",
                }.get(vs.lower() if vs else "")
                if bestiary_title:
                    tr.try_open(self.app, "bestiary", bestiary_title)

                # Guide: Combat Basics — first kill
                if not self._triggered_guide_combat:
                    self._triggered_guide_combat = True
                    tr.try_open(self.app, "guide", "2. Combat Basics")

                # Guide: Enemies & Threat Assessment — after 3+ different types encountered
                if vs:
                    self._bestiary_encountered.add(vs.lower())
                    if not self._triggered_guide_enemies and len(self._bestiary_encountered) >= 3:
                        self._triggered_guide_enemies = True
                        tr.try_open(self.app, "guide", "8. Enemies & Threat Assessment")

                # Reward scaling based on enemy difficulty (using max_hp as proxy)
                # Base reward ranges
                _base_xp_min, _base_xp_max = 30, 60
                _base_gold_min, _base_gold_max = 5, 20

                # Scaling factor: enemy's max HP relative to 100 (average)
                _scale = enemy.max_hp / 100.0

                xp_gain = int(random.randint(_base_xp_min, _base_xp_max) * _scale)
                # Soul Harvest: restore HP and add damage stack
                character = self.character
                if getattr(character, "soul_harvest", False):
                    character.hp = min(character.max_hp, character.hp + character.soul_harvest_hp_per_kill)
                    character.soul_harvest_stacks.append(character.soul_harvest_duration)
                self.character.gain_xp(xp_gain)

                gold_gain = int(random.randint(_base_gold_min, _base_gold_max) * _scale)
                self.app.money += gold_gain
                logger.info(f"Gained {gold_gain} gold. Total: {self.app.money}")

                # Update quest progress for the killed mob type
                mob_type = getattr(enemy, 'profile_name', None)
                if mob_type:
                    quest_state = self.app.manager.states.get("arcane_quest")
                    if quest_state and hasattr(quest_state, "quests"):
                        for q in quest_state.quests:
                            if q.claimed:
                                continue
                            if q.target_type == mob_type:
                                q.progress = min(q.target_count, q.progress + 1)
                                if q.progress >= q.target_count:
                                    q.completed = True

                # Spawn loot drops at the enemy's death location (Python-configured, no JSON)
                self._drop_enemy_loot(enemy)

                self.enemies.remove(enemy)

        self.npc.update(self.character.pos)
        self.card_npc.update(self.character.pos)
        self.fishing_npc.update(self.character.pos)
        self.mage_npc.update(self.character.pos)

        # Update fishing controller
        try:
            if getattr(self, 'fishing', None):
                self.fishing.update(dt)
        except Exception:
            pass

        # Update gathering controller
        try:
            if getattr(self, 'gathering', None):
                self.gathering.update(dt)
        except Exception:
            pass

        # Tick the crafting tempering minigame (sweeping cursor, timers).
        try:
            if getattr(self, 'crafting_minigame', None):
                self.crafting_minigame.update(dt)
        except Exception:
            pass

        # Tick the smeltery overlay so coke oven / blast furnace jobs
        # continue to advance even while the overlay is closed.
        try:
            if getattr(self, 'smeltery', None):
                self.smeltery.update(dt)
        except Exception:
            pass

        # Tick gatherable node respawn timers for the current map.
        try:
            active_registry = self.gatherables.get(self.current_map_path)
            if active_registry is not None:
                active_registry.update(dt)
        except Exception:
            pass

        # Safety: if current map defines an NPC spawn but NPC is far away (not placed), place it
        try:
            if self.current_map_path in self.NPC_SPAWNS and (self.npc.pos.x < -1000 or self.npc.pos.y < -1000):
                nx, ny = self.NPC_SPAWNS[self.current_map_path]
                self.npc.pos = pygame.Vector2(nx, ny)
                logger.info(f"Safety placed NPC on {self.current_map_path} at ({nx},{ny})")
        except Exception:
            pass

        # Safety: place card NPC if it should be on this map but is far away
        try:
            if self.current_map_path in self.CARD_NPC_SPAWNS and (self.card_npc.pos.x < -1000 or self.card_npc.pos.y < -1000):
                cnx, cny = self.CARD_NPC_SPAWNS[self.current_map_path]
                self.card_npc.pos = pygame.Vector2(cnx, cny)
                logger.info(f"Safety placed card NPC on {self.current_map_path} at ({cnx},{cny})")
        except Exception:
            pass

        # Safety: place fishing NPC if it should be on this map but is far away
        try:
            if self.current_map_path in self.FISHING_NPC_SPAWNS and (self.fishing_npc.pos.x < -1000 or self.fishing_npc.pos.y < -1000):
                fnx, fny = self.FISHING_NPC_SPAWNS[self.current_map_path]
                self.fishing_npc.pos = pygame.Vector2(fnx, fny)
                logger.info(f"Safety placed fishing NPC on {self.current_map_path} at ({fnx},{fny})")
        except Exception:
            pass

        # Safety: place mage NPC if it should be on this map but is far away
        try:
            if self.current_map_path in self.MAGE_NPC_SPAWNS and (self.mage_npc.pos.x < -1000 or self.mage_npc.pos.y < -1000):
                mgx, mgy = self.MAGE_NPC_SPAWNS[self.current_map_path]
                self.mage_npc.pos = pygame.Vector2(mgx, mgy)
                logger.info(f"Safety placed mage NPC on {self.current_map_path} at ({mgx},{mgy})")
        except Exception:
            pass

        self.app.profiler.set_gauge("enemies", len(self.enemies))
        self.app.profiler.set_gauge("projectiles", len(self.projectiles))
        self.app.profiler.set_gauge("enemy_projectiles", len(self.enemy_projectiles))
        self.app.profiler.set_gauge("spirits", len(self.spirits))

    def _apply_ice_armor_slow(self, dt):
        """Slow enemies near the player while Ice Armor is active."""
        center = self.character.get_center()
        radius = self.character.ice_armor_slow_radius
        slow_factor = self.character.ice_armor_slow_factor
        slow_duration = 1.0
        radius_sq = radius * radius
        for enemy in self.enemies:
            if enemy.is_dead():
                continue
            enemy_rect = enemy.get_rect()
            enemy_center = pygame.Vector2(enemy_rect.centerx, enemy_rect.centery)
            dist_sq = (enemy_center - center).length_squared()
            if dist_sq <= radius_sq:
                enemy.add_effect(SlowEffect(slow_duration, slow_factor))

    def _apply_flame_shield_damage(self, dt):
        """Deal flame shield damage to enemies within the flame shield radius."""
        center = self.character.get_center()
        radius = self.character.flame_shield_radius
        dmg_per_sec = self.character.flame_shield_damage_per_sec
        # Apply Pyromancer's Fury passive buff to flame shield (+25% damage, +15% area)
        if getattr(self.character, "pyromancers_fury", False):
            dmg_per_sec *= self.character.pyromancers_fury_damage_mult
            radius *= self.character.pyromancers_fury_area_mult
        radius_sq = radius * radius

        # Accumulate fractional damage
        acc = getattr(self.character, "flame_shield_damage_acc", 0.0)
        acc += dmg_per_sec * dt
        damage = int(acc)
        if damage < 1:
            self.character.flame_shield_damage_acc = acc
            return
        self.character.flame_shield_damage_acc = acc - damage

        for enemy in self.enemies:
            if enemy.is_dead():
                continue
            enemy_rect = enemy.get_rect()
            enemy_center = pygame.Vector2(enemy_rect.centerx, enemy_rect.centery)
            dist_sq = (enemy_center - center).length_squared()
            if dist_sq <= radius_sq:
                enemy.take_damage(damage)
                # Apply slight knockback pushing enemy away from player
                if dist_sq > 0:
                    push_dir = (enemy_center - center).normalize()
                    enemy.pos += push_dir * 8 * dt
                    self.collision_handler.resolve_static_collision(enemy, self.obstacles)

    def _apply_regeneration(self, dt):
        acc = getattr(self.character, "regeneration_acc", 0.0)
        acc += self.character.regeneration_hp_per_sec * dt
        heal = int(acc)
        if heal >= 1:
            old_hp = self.character.hp
            self.character.hp = min(self.character.max_hp, self.character.hp + heal)
            acc -= heal
            if self.character.hp > old_hp:
                logger.debug(f"Regeneration healed {heal} HP.")
        self.character.regeneration_acc = acc

    def _update_spirits(self, dt):
        for spirit in self.spirits[:]:
            spirit.update(dt, self.enemies)
        self.spirits = [s for s in self.spirits if s.alive]

    def draw_scene(self, screen):
        self._screen_size = screen.get_size()
        dt = self.app.clock.get_time() / 1000
        self.app.profiler.start_section("game.update")
        self.update(dt)
        self.app.profiler.end_section("game.update")

        self.app.profiler.start_section("game.draw")
        camera_offset = self._get_camera_offset()

        # Boss intro screen shake
        for enemy in self.enemies:
            if isinstance(enemy, Boss) and enemy.intro is not None and not enemy.intro.finished:
                shake = enemy.intro.get_shake_offset()
                camera_offset = camera_offset + shake
                break

        viewport_rect = pygame.Rect(0, 0, screen.get_width(), screen.get_height())

        def _is_visible(entity) -> bool:
            rect = entity.get_rect()
            rect.x -= int(camera_offset.x)
            rect.y -= int(camera_offset.y)
            return rect.colliderect(viewport_rect)

        self.map.draw(screen, camera_offset)

        # Draw enemies and projectiles
        for enemy in self.enemies:
            if _is_visible(enemy):
                enemy.draw(screen, camera_offset)

        for projectile in self.projectiles:
            if _is_visible(projectile):
                projectile.draw(screen, camera_offset)

        for projectile in self.enemy_projectiles:
            if _is_visible(projectile):
                projectile.draw(screen, camera_offset)

        # Draw NPCs, player, and dropped items with simple Y-ordering so
        # they overlap naturally (items at the player's feet won't be hidden
        # behind the player sprite).
        for spirit in self.spirits:
            if _is_visible(spirit):
                spirit.draw(screen, camera_offset)

        # Draw NPCs and player with simple Y-ordering so they overlap naturally
        try:
            npc_vis = _is_visible(self.npc)
        except Exception:
            npc_vis = False
        try:
            card_npc_vis = _is_visible(self.card_npc)
        except Exception:
            card_npc_vis = False
        try:
            fishing_npc_vis = _is_visible(self.fishing_npc)
        except Exception:
            fishing_npc_vis = False
        try:
            mage_npc_vis = _is_visible(self.mage_npc)
        except Exception:
            mage_npc_vis = False

        # Collect all visible entities with their y-position for sorting.
        draw_entities = []
        if npc_vis:
            draw_entities.append((self.npc.pos.y, 'npc'))
        if card_npc_vis:
            draw_entities.append((self.card_npc.pos.y, 'card_npc'))
        if fishing_npc_vis:
            draw_entities.append((self.fishing_npc.pos.y, 'fishing_npc'))
        if mage_npc_vis:
            draw_entities.append((self.mage_npc.pos.y, 'mage_npc'))
        draw_entities.append((self.character.pos.y, 'player'))
        for item in self.items:
            try:
                if _is_visible(item):
                    draw_entities.append((item.pos.y, 'item', item))
            except Exception:
                continue

        # Sort by y-position (lower y drawn first = further back)
        draw_entities.sort(key=lambda e: e[0])

        for entry in draw_entities:
            kind = entry[1]
            if kind == 'npc':
                self.npc.draw(screen, camera_offset)
            elif kind == 'card_npc':
                self.card_npc.draw(screen, camera_offset)
            elif kind == 'fishing_npc':
                self.fishing_npc.draw(screen, camera_offset)
            elif kind == 'mage_npc':
                self.mage_npc.draw(screen, camera_offset)
            elif kind == 'player':
                self.character.draw(screen, camera_offset)
            elif kind == 'item':
                entry[2].draw(screen, camera_offset)

        # Draw boss intro text OVER entities (name + title)
        for enemy in self.enemies:
            if isinstance(enemy, Boss):
                enemy.draw_intro_text(screen)

        try:
            if getattr(self, 'fishing', None):
                self.fishing.draw(screen, camera_offset)
        except Exception:
            pass

        # Draw coordinate-based gatherable nodes (trees/rocks/ore veins)
        # on the current map so they appear in the world.
        try:
            active_registry = self.gatherables.get(self.current_map_path)
            if active_registry is not None:
                active_registry.draw(screen, camera_offset)
        except Exception:
            pass

        # Draw the fringe (upper-details) overlay BEFORE the gathering
        # UI so the bar and "Press G to ..." hint sit on top of the
        # upper halves of trees / rocks and never get hidden behind
        # tall tile art.
        self.map.draw_fringe_overlay(screen, camera_offset, self.character)

        try:
            if getattr(self, 'gathering', None):
                self.gathering.draw(screen, camera_offset)
        except Exception:
            pass

        # "Press E to use Smeltery" hint above the nearest workstation tile.
        try:
            if getattr(self, 'smeltery', None) and not self.smeltery.is_open:
                self._draw_smeltery_hint(screen, camera_offset)
        except Exception:
            pass

        if not self.npc.is_interactable:
            if getattr(self.app.INV_manager, 'current_shop_inv', None) is not None:
                self.app.INV_manager.toggle_trade(self.MAIN_player_inv, self.shop_inv, self.PLAYER_inventory_equipment)

        # Dizziness effect (visual)
        if self.character.dizzy:
            alpha = int(100 + 50 * math.sin(pygame.time.get_ticks() * 0.005))
            if self._dizzy_overlay is None or self._dizzy_overlay.get_size() != screen.get_size():
                self._dizzy_overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            self._dizzy_overlay.fill((255, 255, 255, alpha))
            screen.blit(self._dizzy_overlay, (0, 0))

        self.app.profiler.end_section("game.draw")

    def draw_ui(self, screen):
        self.hud.draw(screen)
        self.app.INV_manager.draw(screen)
        if getattr(self.app, 'current_dialog', None):
            try:
                self.app.current_dialog.draw(screen)
            except Exception:
                pass
        # Draw blackjack, roulette, or poker overlay on top of everything
        if self.blackjack_game:
            try:
                self.blackjack_game.draw(screen)
            except Exception:
                pass
        if self.roulette_game:
            try:
                self.roulette_game.draw(screen)
            except Exception:
                pass
        if self.poker_game:
            try:
                self.poker_game.draw(screen)
            except Exception:
                pass
        # Smeltery workstation overlay (workbench / coke oven / blast furnace).
        # Must draw BEFORE the crafting minigame so the Tempering overlay
        # renders on top of the smeltery panel, not behind it.
        try:
            if getattr(self, 'smeltery', None) and self.smeltery.is_open:
                self.smeltery.draw(screen)
                # Re-draw the inventory's held item on top of the smeltery
                # panel so dragged items stay visible above the overlay.
                try:
                    self.app.INV_manager.draw_held_item(screen)
                except Exception:
                    pass
        except Exception:
            pass
        # Crafting "Tempering" minigame overlay (workbench tempering).
        if getattr(self, 'crafting_minigame', None):
            try:
                self.crafting_minigame.update(0.0)  # safety: no-op if not running
                self.crafting_minigame.draw(screen)
            except Exception:
                pass
        # Draw debug spawn / effects menus
        self.spawn_menu.draw(screen)
        try:
            self.effects_menu.draw(screen)
        except Exception:
            pass

    def draw(self, screen):
        self.draw_scene(screen)
        self.draw_ui(screen)

    def handle_event(self, event: pygame.event.Event):
        # Debug menu priority (support Spawn <-> Effects tab switching)
        if getattr(self, "spawn_menu", None) and getattr(self, "effects_menu", None) and (self.spawn_menu.visible or self.effects_menu.visible):
            # allow keyboard tab switching between menus
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and self.spawn_menu.visible:
                    self.spawn_menu.visible = False
                    self.effects_menu.toggle()
                    return
                if event.key == pygame.K_LEFT and self.effects_menu.visible:
                    self.effects_menu.visible = False
                    self.spawn_menu.toggle()
                    return
            # route events to the visible menu
            if self.spawn_menu.visible:
                self.spawn_menu.handle_event(event)
                return
            if self.effects_menu.visible:
                self.effects_menu.handle_event(event)
                return

        # If blackjack, roulette, or poker game is active, route all events to it
        if self.blackjack_game:
            try:
                self.blackjack_game.handle_event(event)
                return
            except Exception:
                pass
        if self.roulette_game:
            try:
                self.roulette_game.handle_event(event)
                return
            except Exception:
                pass
        if self.poker_game:
            try:
                self.poker_game.handle_event(event)
                return
            except Exception:
                pass

        # If the crafting tempering minigame is active, route all events to it
        if getattr(self, 'crafting_minigame', None):
            try:
                self.crafting_minigame.handle_event(event)
                return
            except Exception:
                pass

        if getattr(self.app, 'current_dialog', None):
            try:
                self.app.current_dialog.handle_event(event)
                return
            except Exception:
                pass

        self.hud.handle_event(event)
        # Route events to fishing controller (casting/reeling)
        if getattr(self, 'fishing', None):
            try:
                handled = self.fishing.handle_event(event)
                if handled:
                    return
            except Exception:
                pass

        # Route events to gathering controller (G to gather, K to cancel)
        if getattr(self, 'gathering', None):
            try:
                handled = self.gathering.handle_event(event)
                if handled:
                    return
            except Exception:
                pass

        # Route events to the smeltery overlay (workbench / coke oven / blast furnace).
        if getattr(self, 'smeltery', None) and self.smeltery.is_open:
            try:
                handled = self.smeltery.handle_event(event)
                if handled:
                    return
            except Exception:
                pass

        if event.type == pygame.MOUSEWHEEL:
            if getattr(self.app.INV_manager, 'hotbar', None):
                self.app.INV_manager.hotbar.scroll_active_slot(event.y)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.app.INV_manager.player_inventory_opened:
                    self.app.INV_manager.toggle_inventory(self.MAIN_player_inv, self.PLAYER_inventory_equipment)
                else:
                    self.app.manager.set_state("pause")
                
            if event.key == pygame.K_q:
                # Q-drop priority (no longer drops a held/dragged item):
                # 1. If the mouse is hovering over an inventory or hotbar slot
                #    that contains an item, drop that item.
                # 2. Otherwise, if the hotbar's active slot contains an item,
                #    drop that item.
                # 3. Otherwise, fall back to the hotbar's active-slot use
                #    behavior (the historical Q action).
                inv_manager = self.app.INV_manager
                dropped = False
                if inv_manager:
                    hovered = inv_manager.take_item_from_under_mouse()
                    if hovered:
                        dropped = inv_manager.drop_item_data(hovered)
                    if not dropped:
                        hotbar_item = inv_manager.take_active_hotbar_item()
                        if hotbar_item:
                            dropped = inv_manager.drop_item_data(hotbar_item)
                if not dropped:
                    if inv_manager and getattr(inv_manager, 'hotbar', None):
                        inv_manager.hotbar.use_active_slot()

            if event.key == pygame.K_1:
                self.use_skill_slot(0)
            if event.key == pygame.K_2:
                self.use_skill_slot(1)
            if event.key == pygame.K_3:
                self.use_skill_slot(2)
            if event.key == pygame.K_4:
                self.use_skill_slot(3)
            if event.key == pygame.K_5:
                self.use_skill_slot(4)
            if event.key == pygame.K_6:
                self.use_skill_slot(5)
            
            if event.key == pygame.K_e:
                # Mage NPC interaction (highest priority)
                if self.mage_npc.is_interactable:
                    dialog_lines = self._get_mage_npc_dialog()

                    def on_mage_close():
                        try:
                            self.mage_npc.was_talked = True
                            # On first talk: unlock Arcane Quests
                            if not self.app.arcane_quests_unlocked:
                                self.app.arcane_quests_unlocked = True
                                logger.info("Arcane Quests UNLOCKED by mage NPC!")
                            # If arcane quests already unlocked and player has purple star: unlock Mysterium Magnum
                            elif not self.app.mysterium_magnum_unlocked and getattr(self.app, 'purple_stars', 0) >= 1:
                                self.app.mysterium_magnum_unlocked = True
                                logger.info("Mysterium Magnum UNLOCKED by mage NPC!")
                        except Exception:
                            pass

                    self.app.current_dialog = Dialog(
                        self.app,
                        dialog_lines,
                        on_close=on_mage_close,
                    )
                # Card NPC interaction
                elif self.card_npc.is_interactable:
                    dialog_lines = self._get_card_npc_dialog()

                    def on_card_close():
                        try:
                            self.card_npc.was_talked = True
                        except Exception:
                            pass

                    self.app.current_dialog = Dialog(
                        self.app,
                        dialog_lines,
                        on_close=on_card_close,
                        on_play_cards=self.open_blackjack,
                        show_play_cards=True,
                        on_play_roulette=self.open_roulette,
                        show_play_roulette=True,
                        on_play_poker=self.open_poker,
                        show_play_poker=True,
                    )
                elif self.fishing_npc.is_interactable:
                    self.app.manager.set_state("collection_book")
                elif self.npc.is_interactable:
                    def on_close():
                        try:
                            self.app.last_talked_npc = self.npc
                            self.npc.was_talked = True
                        except Exception:
                            pass

                    # show shop button inside dialog only for merchant NPCs
                    self.app.current_dialog = Dialog(self.app, self.npc.dialog_lines, on_close=on_close, on_shop=self.open_shop, show_shop=self.npc.is_merchant)
                elif self._find_nearby_smeltery_tile() is not None and getattr(self, "smeltery", None):
                    self.smeltery.open()
                else:
                    # Otherwise toggle the player's inventory (open/close)
                    self.app.INV_manager.toggle_inventory(self.MAIN_player_inv, self.PLAYER_inventory_equipment)

            # Test keys
            if event.key == pygame.K_F5:
                self.character.take_damage(10)
            if event.key == pygame.K_F6:
                self.character.gain_xp(50)
            if event.key == pygame.K_F9:
                self.character.skill_tree_points += 1
                logger.info(f"[DEBUG] F9: +1 skill tree point. Total: {self.character.skill_tree_points}")
            if event.key == pygame.K_F10:
                self.spawn_menu.toggle()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if not self.app.INV_manager.player_inventory_opened:
                    hud_click = self.hud.inv_button.rect.collidepoint(event.pos) or (
                        not getattr(self.app.INV_manager, 'current_shop_inv', None) and any(slot.collidepoint(event.pos) for slot in self.hud.skill_slot_rects)
                    )
                    if not hud_click:
                        mouse_world_pos = pygame.Vector2(event.pos) + self._get_camera_offset()
                        self.player_combat.handle_player_attack(mouse_world_pos)
            
            elif event.button == 3:
                if not self.app.INV_manager.player_inventory_opened:
                    if getattr(self.app.INV_manager, 'hotbar', None):
                        self.app.INV_manager.hotbar.use_active_slot()

        self.app.INV_manager.PLAYER_inventory_open(event, self.MAIN_player_inv, self.PLAYER_inventory_equipment)
