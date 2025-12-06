import json
import os
import datetime
from src.core.logger import logger
from src.items.items import create_item
import src.config as cfg

SAVES_DIR = "saves"

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

        save_data = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "money": app.money,
            "player": {
                "pos_x": game_state.character.pos.x,
                "pos_y": game_state.character.pos.y,
                "hp": game_state.character.hp,
                "max_hp": game_state.character.max_hp,
                "xp": game_state.character.xp,
                "level": game_state.character.level,
                "xp_to_next_level": game_state.character.xp_to_next_level,
                "map_path": game_state.current_map_path if hasattr(game_state, "current_map_path") else "maps/test-map-1.tmx",
            },
            "inventory": serialized_inv,
            "equipment": serialized_equip
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

        # Restore Player
        game_state.character.pos.x = player_data.get("pos_x", 0)
        game_state.character.pos.y = player_data.get("pos_y", 0)
        game_state.character.hp = player_data.get("hp", 100)
        game_state.character.max_hp = player_data.get("max_hp", 100)
        game_state.character.xp = player_data.get("xp", 0)
        game_state.character.level = player_data.get("level", 1)
        game_state.character.xp_to_next_level = player_data.get("xp_to_next_level", 100)
        
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
