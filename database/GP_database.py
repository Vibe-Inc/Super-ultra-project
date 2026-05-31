import sqlite3
import os
import inspect

from database.effects import Effect_list

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "GP_database.db")

class Gp_database:
    """
    Manages the SQLite database for game items, weapons, and consumables.

    This class handles the creation of tables, insertion of different item types 
    with their specific properties, and dynamic extraction of item parameters for the game.

    Attributes:
        conn (sqlite3.Connection):
            The connection object to the SQLite database.
        cursor (sqlite3.Cursor):
            The cursor object used to execute database queries.

    Methods:
        __init__(db_name):
            Initialize the database connection and configuration.
        setup_tables():
            Create the necessary relational tables if they do not exist.
        add_generic_item(item_id, item_type, name, image_path, price, max_stack, description):
            Insert a basic item into the database.
        add_weapon(item_id, name, image_path, weapon_class, damage, durability, range_val, projectile_speed, cooldown, spread_degrees, cone_degrees, price, description):
            Insert a weapon with combat statistics into the database.
        add_consumable(item_id, item_type, name, image_path, heal_amount, effects, price, max_stack, description):
            Insert a consumable item and dynamically parse its effects into the database.
        get_item(item_id):
            Retrieve a complete dictionary of item stats and effects by its ID.
        close():
            Close the SQLite database connection.
    """

    def __init__(self, db_name=DB_PATH):
        """
        Initialize the database object.

        Args:
            db_name (str): The file path to the SQLite database.
        """
        self.conn = sqlite3.connect(db_name)
        self.conn.row_factory = sqlite3.Row 
        self.cursor = self.conn.cursor()
        self.setup_tables()

    def setup_tables(self):
        """
        Create all database tables required for the inventory system.
        """
        self.cursor.execute('PRAGMA foreign_keys = ON')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                image_path TEXT,
                price INTEGER DEFAULT 0,
                max_stack INTEGER DEFAULT 64,
                description TEXT
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS weapons (
                item_id TEXT PRIMARY KEY,
                weapon_class TEXT,       
                damage INT DEFAULT 1,    
                durability INT DEFAULT 100,
                range INT,            
                projectile_speed INT DEFAULT 0, 
                cooldown INT DEFAULT 500,
                spread_degrees REAL DEFAULT 0.0,
                cone_degrees REAL DEFAULT 0.0,     
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS consumables (
                item_id TEXT PRIMARY KEY,
                heal_amount INT DEFAULT 0,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS consumable_effects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT,
                effect_type TEXT NOT NULL,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS effect_params (
                effect_id INTEGER,
                param_name TEXT NOT NULL,
                param_value REAL NOT NULL,
                FOREIGN KEY (effect_id) REFERENCES consumable_effects(id) ON DELETE CASCADE
            )
        ''')
        self.conn.commit()

    def add_generic_item(self, item_id: str, item_type: str, name: str, image_path: str, price: int = 0, max_stack: int = 64, description: str = "") -> bool:
        """
        Add a generic item to the database.

        Args:
            item_id (str): Unique identifier for the item.
            item_type (str): Type category of the item.
            name (str): Display name or translation key.
            image_path (str): File path to the item's texture.
            price (int): Monetary value of the item.
            max_stack (int): Maximum items allowed in a single slot.
            description (str): Description text or translation key.

        Returns:
            bool: True if insertion was successful, False if it failed or exists.
        """
        try:
            self.cursor.execute('''
                INSERT INTO items (id, type, name, image_path, price, max_stack, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (item_id, item_type, name, image_path, price, max_stack, description))
            self.conn.commit()
            print(f"Item '{item_id}' added successfully.")
            return True
        except sqlite3.IntegrityError:
            print(f"Item '{item_id}' already exists (skipping).")
            return False

    def add_weapon(self, item_id: str, name: str, image_path: str, weapon_class: str, 
                   damage: int = 1, durability: int = 100, range_val: int = 65, 
                   projectile_speed: int = 0, cooldown: int = 500, 
                   spread_degrees: float = 0.0, cone_degrees: float = 0.0,
                   price: int = 0, description: str = "") -> bool:
        """
        Add a weapon item to the database along with its combat stats.

        Args:
            item_id (str): Unique identifier for the weapon.
            name (str): Display name or translation key.
            image_path (str): File path to the weapon's texture.
            weapon_class (str): Sub-category of the weapon (e.g., melee, ranged).
            damage (int): Base damage dealt by the weapon.
            durability (int): Maximum durability points.
            range_val (int): Effective attack range.
            projectile_speed (int): Speed of the projectile if ranged.
            cooldown (int): Attack cooldown in milliseconds.
            spread_degrees (float): Spread angle for projectiles.
            cone_degrees (float): Attack arc angle for melee.
            price (int): Monetary value of the weapon.
            description (str): Description text or translation key.

        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        try:
            self.conn.execute("BEGIN TRANSACTION")

            self.cursor.execute('''
                INSERT INTO items (id, type, name, image_path, price, max_stack, description)
                VALUES (?, 'weapon', ?, ?, ?, 1, ?)
            ''', (item_id, name, image_path, price, description))

            self.cursor.execute('''
                INSERT INTO weapons (item_id, weapon_class, damage, durability, range, 
                                    projectile_speed, cooldown, spread_degrees, cone_degrees)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item_id, weapon_class, damage, durability, range_val, 
                  projectile_speed, cooldown, spread_degrees, cone_degrees))

            self.conn.commit()
            print(f"Weapon '{item_id}' added successfully.")
            return True
        except sqlite3.IntegrityError:
            self.conn.rollback()
            return False
        except sqlite3.Error as e:
            self.conn.rollback()
            return False

    def add_consumable(self, item_id: str, item_type: str, name: str, image_path: str, 
                       heal_amount: int = 0, effects: list = None, 
                       price: int = 0, max_stack: int = 64, description: str = "") -> bool:
        """
        Add a consumable item to the database and dynamically map its effects.

        Args:
            item_id (str): Unique identifier for the consumable.
            item_type (str): Type category (e.g., food, potion).
            name (str): Display name or translation key.
            image_path (str): File path to the consumable's texture.
            heal_amount (int): Immediate health restored or damaged.
            effects (list): List of dictionaries containing effect properties.
            price (int): Monetary value of the consumable.
            max_stack (int): Maximum items allowed in a single slot.
            description (str): Description text or translation key.

        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        if effects is None:
            effects = []
            
        try:
            self.conn.execute("BEGIN TRANSACTION")
            
            self.cursor.execute('''
                INSERT INTO items (id, type, name, image_path, price, max_stack, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (item_id, item_type, name, image_path, price, max_stack, description))

            self.cursor.execute('''
                INSERT INTO consumables (item_id, heal_amount)
                VALUES (?, ?)
            ''', (item_id, heal_amount))

            for effect in effects:
                e_type = effect.get("type")
                if not e_type: continue
                
                self.cursor.execute('''
                    INSERT INTO consumable_effects (item_id, effect_type)
                    VALUES (?, ?)
                ''', (item_id, e_type))
                
                effect_id = self.cursor.lastrowid
                
                effect_class = Effect_list.get(e_type)
                if effect_class:
                    sig = inspect.signature(effect_class.__init__)
                    for param_name in sig.parameters.keys():
                        if param_name != 'self' and param_name in effect:
                            self.cursor.execute('''
                                INSERT INTO effect_params (effect_id, param_name, param_value)
                                VALUES (?, ?, ?)
                            ''', (effect_id, param_name, effect[param_name]))

            self.conn.commit()
            print(f"Consumable '{item_id}' added successfully.")
            return True
        except sqlite3.IntegrityError:
            self.conn.rollback()
            return False
        except sqlite3.Error:
            self.conn.rollback()
            return False

    def get_item(self, item_id: str) -> dict:
        """
        Retrieve an item and compile its parameters into a dictionary.

        Args:
            item_id (str): The unique identifier of the item to fetch.

        Returns:
            dict | None: A dictionary mapping item attributes to their values, or None if not found.
        """
        self.cursor.execute('''
            SELECT items.*, 
                   weapons.weapon_class, weapons.damage, weapons.durability, weapons.range, 
                   weapons.projectile_speed, weapons.cooldown, weapons.spread_degrees, weapons.cone_degrees,
                   consumables.heal_amount
            FROM items
            LEFT JOIN weapons ON items.id = weapons.item_id
            LEFT JOIN consumables ON items.id = consumables.item_id
            WHERE items.id = ?
        ''', (item_id,))
        
        row = self.cursor.fetchone()
        if not row:
            return None
            
        item_data = dict(row)
        item_data["effects"] = []
        
        if item_data["type"] in ("food", "potion"):
            self.cursor.execute('SELECT id, effect_type FROM consumable_effects WHERE item_id = ?', (item_id,))
            effects_rows = self.cursor.fetchall()
            
            for e_row in effects_rows:
                e_id = e_row["id"]
                effect_dict = {"type": e_row["effect_type"]}
                
                self.cursor.execute('SELECT param_name, param_value FROM effect_params WHERE effect_id = ?', (e_id,))
                params_rows = self.cursor.fetchall()
                
                for p_row in params_rows:
                    val = p_row["param_value"]
                    if val.is_integer(): 
                        val = int(val)
                    effect_dict[p_row["param_name"]] = val
                    
                item_data["effects"].append(effect_dict)
                
        return item_data

    def close(self):
        """
        Close the database connection safely.
        """
        self.conn.close()