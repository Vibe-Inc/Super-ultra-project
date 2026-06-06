import json
import os
import datetime
import pygame
from src.core.logger import logger
from src.items.items import create_item
import src.config as cfg

SAVES_DIR = "saves"
SETTINGS_FILE = os.path.join(SAVES_DIR, "settings.json")

def _skill_dicts_to_json(items):
    """Convert tuple RGB values to lists for JSON serialization."""
    result = []
    for item in items:
        if item is None:
            result.append(None)
            continue
        result.append({k: list(v) if isinstance(v, tuple) else v for k, v in item.items()})
    return result

def _skill_dicts_from_json(items):
    """Convert list RGB values back to tuples."""
    result = []
    for item in items:
        if item is None:
            result.append(None)
            continue
        result.append({k: tuple(v) if isinstance(v, list) else v for k, v in item.items()})
    return result

# All character fields to persist (excluding transient/computed/resource attributes)
CHARACTER_SCALAR_FIELDS = [
    "death_count",
    "max_stamina", "stamina", "stamina_drain_rate", "stamina_regen_rate",
    "can_sprint", "is_sprinting",
    "skill_tree_points",
    "cooldown_multiplier",
    "damage_bonus",
    "base_attack_damage", "attack_damage",
    "base_attack_range", "attack_range",
    "base_attack_cooldown", "attack_cooldown_mult",
    "speed_multiplier", "speed", "base_speed", "sprint_multiplier",
    "spawn_point_x", "spawn_point_y",
    # Passive booleans and scalars
    "static_field", "static_field_proc_chance", "static_field_damage",
    "regeneration", "regeneration_hp_per_sec",
    "pyromancers_fury", "pyromancers_fury_damage_mult", "pyromancers_fury_area_mult",
    "poison_blade", "poison_blade_damage_per_sec", "poison_blade_duration",
    "mana_flow",
    "eternal_fortress",
    "soul_harvest", "soul_harvest_duration", "soul_harvest_hp_per_kill", "soul_harvest_damage_per_stack",
    "void_walker", "void_walker_dodge_chance", "void_walker_teleport_range", "void_walker_afterimage_damage",
    "elemental_mastery", "elemental_damage_mult", "combo_window",
    # Fireball
    "fireball_damage", "fireball_blast_radius", "fireball_cooldown",
    "fireball_speed", "fireball_range", "fireball_knockback", "fireball_fuse_time",
    # Flame Shield
    "flame_shield_duration", "flame_shield_cooldown", "flame_shield_damage_per_sec", "flame_shield_radius",
    # Frost Nova
    "frost_nova_radius", "frost_nova_freeze_duration", "frost_nova_damage", "frost_nova_cooldown",
    # Ice Armor
    "ice_armor_duration", "ice_armor_cooldown", "ice_armor_remaining_absorption",
    "ice_armor_max_absorption", "ice_armor_slow_radius", "ice_armor_slow_factor",
    # Glacial Cascade
    "glacial_cascade_damage", "glacial_cascade_freeze_duration", "glacial_cascade_cooldown",
    "glacial_cascade_range", "glacial_cascade_speed", "glacial_cascade_width",
    # Chain Lightning
    "chain_lightning_damage", "chain_lightning_chain_range", "chain_lightning_max_targets",
    "chain_lightning_cooldown", "chain_lightning_range", "chain_lightning_speed",
    # Thunderstrike
    "thunderstrike_damage", "thunderstrike_radius", "thunderstrike_range", "thunderstrike_cooldown",
    # Entangling Roots
    "entangling_roots_cooldown", "entangling_roots_damage", "entangling_roots_range",
    "entangling_roots_radius", "entangling_roots_root_duration", "entangling_roots_speed",
    # Summon Spirit
    "summon_spirit_damage", "summon_spirit_duration", "summon_spirit_cooldown",
    # Shadow Step
    "shadow_step_cooldown", "shadow_step_range", "shadow_step_invuln_duration",
    # Dark Pact
    "dark_pact_damage", "dark_pact_radius", "dark_pact_cooldown", "dark_pact_hp_cost_percent",
    # Arcane Missiles
    "arcane_missiles_damage", "arcane_missiles_count", "arcane_missiles_cooldown",
    "arcane_missiles_range", "arcane_missiles_speed",
    # Mystic Barrier
    "mystic_barrier_duration", "mystic_barrier_cooldown", "mystic_barrier_reflect_pct",
    # Berserker's Rage
    "berserkers_rage_duration", "berserkers_rage_cooldown",
    # Chrono Shift
    "chrono_shift_duration", "chrono_shift_cooldown",
    # Dash
    "dash_speed_multiplier", "dash_duration", "dash_cooldown", "dash_last_used",
    # Cooldown timestamps
    "fireball_last_used", "flame_shield_last_used", "frost_nova_last_used",
    "ice_armor_last_used", "glacial_cascade_last_used", "chain_lightning_last_used",
    "thunderstrike_last_used", "entangling_roots_last_used", "summon_spirit_last_used",
    "shadow_step_last_used", "dark_pact_last_used", "arcane_missiles_last_used",
    "mystic_barrier_last_used", "berserkers_rage_last_used", "chrono_shift_last_used",
    # Active states
    "flame_shield_active", "flame_shield_active_time",
    "ice_armor_active", "ice_armor_active_time",
    "mystic_barrier_active", "mystic_barrier_active_time",
    "berserkers_rage_active", "berserkers_rage_active_time",
    "chrono_shift_active", "chrono_shift_active_time",
    # Elemental Mastery runtime
    "last_elemental_time",
]

class SaveManager:
    """
    Manages game saving and loading functionality.

    This class handles the serialization and deserialization of game state, including player stats, inventory, and equipment, to and from JSON files.

    Methods:
        ensure_saves_dir():
            Ensure the saves directory exists.
        get_save_files():
            Get a list of available save files.
        save_game(app, slot_name):
            Save the current game state to a file.
        load_game(app, slot_name):
            Load a game state from a file.
        delete_save(slot_name):
            Delete a specific save file.
    """
    @staticmethod
    def ensure_saves_dir():
        """
        Ensure that the directory for save files exists.
        """
        if not os.path.exists(SAVES_DIR):
            os.makedirs(SAVES_DIR)

    @staticmethod
    def get_save_files():
        """
        Retrieve a list of all available save files in the saves directory.

        Returns:
            list[str]: A list of filenames ending with '.json'.
        """
        SaveManager.ensure_saves_dir()
        files = [f for f in os.listdir(SAVES_DIR) if f.endswith('.json')]
        return files

    @staticmethod
    def save_game(app, slot_name):
        """
        Save the current game state to a JSON file.

        Args:
            app (App): The main application instance containing the game state.
            slot_name (str): The name of the save slot (filename without extension).
        """
        SaveManager.ensure_saves_dir()
        
        game_state = app.manager.states.get("gameplay")
        if not game_state:
            logger.error("Cannot save, gameplay state not found.")
            return

        # Serialize Inventory
        serialized_inv = []
        for col in range(len(app.MAIN_INV_items)):
            col_data = []
            for row in range(len(app.MAIN_INV_items[col])):
                slot = app.MAIN_INV_items[col][row]
                if slot:
                    item, count = slot
                    col_data.append({"id": item.id, "count": count})
                else:
                    col_data.append(None)
            serialized_inv.append(col_data)

        # Serialize Equipment (assuming it's stored similarly in game.PLAYER_inventory_equipment)
        # Note: PLAYER_inventory_equipment.items is the grid
        serialized_equip = []
        equip_inv = game_state.PLAYER_inventory_equipment
        for col in range(len(equip_inv.items)):
            col_data = []
            for row in range(len(equip_inv.items[col])):
                slot = equip_inv.items[col][row]
                if slot:
                    item, count = slot
                    col_data.append({"id": item.id, "count": count})
                else:
                    col_data.append(None)
            serialized_equip.append(col_data)

        # Serialize Items Hotbar (10×1 grid of [item, count] or None)
        serialized_hotbar = []
        for col in range(len(app.MAIN_HOTBAR_items)):
            col_data = []
            for row in range(len(app.MAIN_HOTBAR_items[col])):
                slot = app.MAIN_HOTBAR_items[col][row]
                if slot:
                    item, count = slot
                    col_data.append({"id": item.id, "count": count})
                else:
                    col_data.append(None)
            serialized_hotbar.append(col_data)

        # Serialize Quest Data
        quest_data = []
        quest_state = app.manager.states.get("arcane_quest")
        if quest_state and hasattr(quest_state, "get_quest_data"):
            quest_data = quest_state.get_quest_data()

        char = game_state.character

        # Build character state dict (raw __dict__ values to bypass __getattribute__ overrides)
        char_state = {}
        for field in CHARACTER_SCALAR_FIELDS:
            if field in ("spawn_point_x", "spawn_point_y"):
                continue
            try:
                char_state[field] = char.__dict__[field]
            except KeyError:
                pass
        char_state["skill_tree_unlocked"] = list(char.__dict__.get("skill_tree_unlocked", {"core"}))
        char_state["skillbook"] = _skill_dicts_to_json(char.__dict__.get("skillbook", []))
        char_state["skillbar"] = _skill_dicts_to_json(char.__dict__.get("skillbar", []))
        char_state["soul_harvest_stacks"] = char.__dict__.get("soul_harvest_stacks", [])
        char_state["last_elemental_skill"] = char.__dict__.get("last_elemental_skill", None)
        char_state["spawn_point_x"] = char.__dict__.get("spawn_point", char.pos).x if hasattr(char.__dict__.get("spawn_point", char.pos), "x") else char.pos.x
        char_state["spawn_point_y"] = char.__dict__.get("spawn_point", char.pos).y if hasattr(char.__dict__.get("spawn_point", char.pos), "y") else char.pos.y

        save_data = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "money": app.money,
            "purple_stars": app.purple_stars,
            "revealed_tarot_cards": list(app.revealed_tarot_cards),
            "arcane_quests_unlocked": getattr(app, 'arcane_quests_unlocked', False),
            "mysterium_magnum_unlocked": getattr(app, 'mysterium_magnum_unlocked', False),
            "seen_articles": app.article_tracker.serialize(),
            "player": {
                "pos_x": char.pos.x,
                "pos_y": char.pos.y,
                "hp": char.hp,
                "max_hp": char.max_hp,
                "xp": char.xp,
                "level": char.level,
                "xp_to_next_level": char.xp_to_next_level,
                "map_path": game_state.current_map_path if hasattr(game_state, "current_map_path") else "maps/test-map-1.tmx",
                "character_state": char_state,
            },
            "inventory": serialized_inv,
            "hotbar": serialized_hotbar,
            "hotbar_active_slot": getattr(game_state, "hotbar", None).active_slot_index if hasattr(game_state, "hotbar") and game_state.hotbar else 0,
            "equipment": serialized_equip,
            "game_time_seconds": int(getattr(game_state, "game_time_seconds", 6 * 3600)),
            "quests": quest_data,
        }
        
        if hasattr(game_state, "current_map_path"):
             save_data["player"]["map_path"] = game_state.current_map_path
        else:
             # Default fallback
             save_data["player"]["map_path"] = "maps/test-map-1.tmx"

        file_path = os.path.join(SAVES_DIR, f"{slot_name}.json")
        with open(file_path, 'w') as f:
            json.dump(save_data, f, indent=4)
        logger.info(f"Game saved to {file_path}")

    @staticmethod
    def load_game(app, slot_name):
        """
        Load the game state from a JSON file and restore it to the application.

        Args:
            app (App): The main application instance to restore the state into.
            slot_name (str): The name of the save slot to load.

        Returns:
            bool: True if the game was successfully loaded, False otherwise.
        """
        file_path = os.path.join(SAVES_DIR, f"{slot_name}.json")
        if not os.path.exists(file_path):
            logger.error(f"Save file {file_path} not found.")
            return False

        with open(file_path, 'r') as f:
            data = json.load(f)

        # Restore Money
        app.money = data.get("money", 0)
        app.purple_stars = data.get("purple_stars", 0)
        app.revealed_tarot_cards = set(data.get("revealed_tarot_cards", []))
        app.arcane_quests_unlocked = data.get("arcane_quests_unlocked", False)
        app.mysterium_magnum_unlocked = data.get("mysterium_magnum_unlocked", False)

        # Restore Inventory
        inv_data = data.get("inventory", [])
        for col in range(len(inv_data)):
            for row in range(len(inv_data[col])):
                slot_data = inv_data[col][row]
                if slot_data:
                    item = create_item(slot_data["id"])
                    count = slot_data["count"]
                    app.MAIN_INV_items[col][row] = [item, count]
                else:
                    app.MAIN_INV_items[col][row] = None

        app.manager.set_state("gameplay")
        game_state = app.manager.states["gameplay"]
        
        # Restore Map
        player_data = data.get("player", {})
        map_path = player_data.get("map_path", "maps/test-map-1.tmx")
        
        from src.map.map import LocalMap
        game_state.map = LocalMap("LoadedLevel", map_path)
        game_state.current_map_path = map_path # Store for next save
        game_state.obstacles = game_state.map.get_obstacles()
        if hasattr(game_state, "_rebuild_nav_grid"):
            game_state._rebuild_nav_grid()

        # Restore Player
        char = game_state.character
        char.pos.x = player_data.get("pos_x", 0)
        char.pos.y = player_data.get("pos_y", 0)
        char.hp = player_data.get("hp", 100)
        char.max_hp = player_data.get("max_hp", 100)
        char.xp = player_data.get("xp", 0)
        char.level = player_data.get("level", 1)
        char.xp_to_next_level = player_data.get("xp_to_next_level", 100)

        # Restore extended character state
        char_state = player_data.get("character_state", {})
        if char_state:
            for field in CHARACTER_SCALAR_FIELDS:
                if field in ("spawn_point_x", "spawn_point_y",):
                    continue
                if field in char_state:
                    setattr(char, field, char_state[field])
            if "skill_tree_unlocked" in char_state:
                char.skill_tree_unlocked = set(char_state["skill_tree_unlocked"])
            if "skillbook" in char_state:
                char.skillbook = _skill_dicts_from_json(char_state["skillbook"])
            if "skillbar" in char_state:
                char.skillbar = _skill_dicts_from_json(char_state["skillbar"])
            if "soul_harvest_stacks" in char_state:
                char.soul_harvest_stacks = list(char_state["soul_harvest_stacks"])
            if "last_elemental_skill" in char_state:
                char.last_elemental_skill = char_state["last_elemental_skill"]
            if "spawn_point_x" in char_state and "spawn_point_y" in char_state:
                char.spawn_point.x = char_state["spawn_point_x"]
                char.spawn_point.y = char_state["spawn_point_y"]
            # Recalculate derived stats
            char.speed = char.base_speed * char.speed_multiplier
            char.attack_damage = char.base_attack_damage
            char.attack_range = char.base_attack_range
            char.attack_cooldown = char.base_attack_cooldown
            if char.max_hp < char.hp:
                char.hp = char.max_hp
        
        # Restore Items Hotbar
        hotbar_data = data.get("hotbar", [])
        if hotbar_data and hasattr(game_state, "hotbar") and game_state.hotbar:
            active_slot = data.get("hotbar_active_slot", 0)
            game_state.hotbar.active_slot_index = active_slot
            for col in range(min(len(hotbar_data), len(app.MAIN_HOTBAR_items))):
                for row in range(min(len(hotbar_data[col]), len(app.MAIN_HOTBAR_items[col]))):
                    slot_data = hotbar_data[col][row]
                    if slot_data:
                        item = create_item(slot_data["id"])
                        count = slot_data["count"]
                        app.MAIN_HOTBAR_items[col][row] = [item, count]
                    else:
                        app.MAIN_HOTBAR_items[col][row] = None

        # Restore Equipment
        equip_data = data.get("equipment", [])
        equip_inv = game_state.PLAYER_inventory_equipment
        for col in range(len(equip_data)):
            for row in range(len(equip_data[col])):
                slot_data = equip_data[col][row]
                if slot_data:
                    item = create_item(slot_data["id"])
                    count = slot_data["count"]
                    equip_inv.items[col][row] = [item, count]
                else:
                    equip_inv.items[col][row] = None

        # Restore Quest Data
        quest_data = data.get("quests", [])
        if quest_data:
            quest_state = app.manager.states.get("arcane_quest")
            if quest_state and hasattr(quest_state, "set_quest_data"):
                quest_state.set_quest_data(quest_data)

        # Restore seen articles
        seen_articles = data.get("seen_articles", [])
        if seen_articles:
            app.article_tracker.deserialize(seen_articles)
            logger.info(f"Restored {len(seen_articles)} seen articles from save.")

        # Sync character defense from loaded equipment
        equip_inv.sync_character_defense(char)

        # Restore game time and visual state
        if "game_time_seconds" in data:
            game_state.game_time_seconds = int(data["game_time_seconds"])
        else:
            game_state.game_time_seconds = getattr(game_state, "game_time_seconds", 6 * 3600)
        game_state._update_game_time(0)

        logger.info(f"Game loaded from {file_path}")
        return True

    @staticmethod
    def delete_save(slot_name):
        """
        Delete a specific save file.

        Args:
            slot_name (str): The name of the save slot to delete.
        """
        file_path = os.path.join(SAVES_DIR, f"{slot_name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted save {file_path}")

    @staticmethod
    def save_settings(app):
        """
        Persist current user settings (language, display mode, brightness, volume)
        to a JSON file so they survive application restarts.

        Args:
            app (App): The main application instance.
        """
        SaveManager.ensure_saves_dir()
        data = {
            "language": cfg.LANGUAGE,
            "fullscreen": app.is_fullscreen,
            "windowed_width": app.windowed_size[0],
            "windowed_height": app.windowed_size[1],
            "brightness": cfg.USER_SCREEN_BRIGHTNESS,
            "music_volume": cfg.MUSIC_VOLUME,
            "profiler_enabled": cfg.PROFILER_ENABLED,
            "guide_intro_shown": app.guide_intro_shown,
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        logger.info(f"Settings saved to {SETTINGS_FILE}")

    @staticmethod
    def load_settings(app):
        """
        Restore previously persisted user settings into the application.

        Args:
            app (App): The main application instance.
        """
        if not os.path.exists(SETTINGS_FILE):
            logger.info("No saved settings found — using defaults.")
            return

        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)

        # Language
        lang = data.get("language", cfg.LANGUAGE)
        if lang in cfg.SUPPORTED_LANGUAGES and lang != cfg.LANGUAGE:
            app.update_language(lang)

        # Brightness
        cfg.USER_SCREEN_BRIGHTNESS = data.get("brightness", cfg.USER_SCREEN_BRIGHTNESS)
        cfg.update_brightness()

        # Music volume
        cfg.MUSIC_VOLUME = data.get("music_volume", 0.3)
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(cfg.MUSIC_VOLUME)

        # Profiler
        app.set_profiler_enabled(data.get("profiler_enabled", False))

        # Windowed size
        if "windowed_width" in data and "windowed_height" in data:
            app.windowed_size = (data["windowed_width"], data["windowed_height"])

        # Guide intro one-time flag
        app.guide_intro_shown = data.get("guide_intro_shown", False)

        # Fullscreen — apply after windowed_size is restored
        if data.get("fullscreen", False):
            app._apply_display_mode(True, update_windowed_size=False)

        logger.info(f"Settings loaded from {SETTINGS_FILE}")
