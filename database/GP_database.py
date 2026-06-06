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

    def _ensure_column(self, table: str, column: str, definition: str):
        """
        Add a column to a table if it doesn't already exist (safe migration).

        Args:
            table (str): Table name.
            column (str): Column to add.
            definition (str): Full column definition (e.g. "INT DEFAULT 0").
        """
        try:
            self.cursor.execute(f"PRAGMA table_info({table})")
            existing = {row[1] for row in self.cursor.fetchall()}
            if column not in existing:
                self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                self.conn.commit()
        except sqlite3.Error as exc:
            print(f"_ensure_column({table}.{column}) failed: {exc}")

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
                max_durability INT DEFAULT 100,
                range INT,
                projectile_speed INT DEFAULT 0,
                cooldown INT DEFAULT 500,
                spread_degrees REAL DEFAULT 0.0,
                cone_degrees REAL DEFAULT 0.0,
                on_hit_effects TEXT DEFAULT NULL,
                combat_style TEXT DEFAULT 'sword',
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')

        # Backwards-compatible column adds for existing databases.
        self._ensure_column("weapons", "on_hit_effects", "TEXT DEFAULT NULL")
        self._ensure_column("weapons", "combat_style", "TEXT DEFAULT 'sword'")
        # max_durability lets us track the *original* durability of a weapon
        # even as the current `durability` ticks down. We seed it with the
        # existing `durability` value on first migration so legacy rows
        # behave the same as before.
        self._ensure_column("weapons", "max_durability", "INT DEFAULT NULL")
        try:
            self.cursor.execute(
                "UPDATE weapons SET max_durability = durability "
                "WHERE max_durability IS NULL"
            )
            self.conn.commit()
        except sqlite3.Error:
            self.conn.rollback()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS consumables (
                item_id TEXT PRIMARY KEY,
                heal_amount INT DEFAULT 0,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS armor (
                item_id TEXT PRIMARY KEY,
                slot_type TEXT NOT NULL DEFAULT 'helmet',
                defense_value INT DEFAULT 0,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tools (
                item_id TEXT PRIMARY KEY,
                tool_type TEXT NOT NULL DEFAULT 'generic',
                durability INT DEFAULT 100,
                max_durability INT DEFAULT 100,
                power INT DEFAULT 0,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS fish (
                item_id TEXT PRIMARY KEY,
                rarity TEXT NOT NULL DEFAULT 'common',
                difficulty REAL DEFAULT 0.3,
                speed REAL DEFAULT 1.0,
                spawn_weight INT DEFAULT 50,
                base_price INT DEFAULT 10,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')

        # Backwards-compatible column adds for gathering tools.
        self._ensure_column("tools", "gather_type", "TEXT DEFAULT NULL")
        self._ensure_column("tools", "gather_yield_min", "INT DEFAULT 1")
        self._ensure_column("tools", "gather_yield_max", "INT DEFAULT 1")
        # max_durability is the pristine reference value; the existing
        # `durability` column is the live (ticking-down) value.
        self._ensure_column("tools", "max_durability", "INT DEFAULT NULL")
        try:
            self.cursor.execute(
                "UPDATE tools SET max_durability = durability "
                "WHERE max_durability IS NULL"
            )
            self.conn.commit()
        except sqlite3.Error:
            self.conn.rollback()

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

        # Таблиця рецептів
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS crafting_recipes (
                recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_item_id TEXT NOT NULL,
                result_amount INTEGER DEFAULT 1,
                FOREIGN KEY (result_item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipe_ingredients (
                recipe_id INTEGER,
                ingredient_item_id TEXT NOT NULL,
                required_amount INTEGER DEFAULT 1,
                FOREIGN KEY (recipe_id) REFERENCES crafting_recipes(recipe_id) ON DELETE CASCADE,
                FOREIGN KEY (ingredient_item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')
        self.conn.commit()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS shaped_recipes (
                recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_item_id TEXT NOT NULL UNIQUE,
                result_amount INTEGER DEFAULT 1,
                FOREIGN KEY (result_item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipe_matrix (
                recipe_id INTEGER,
                ingredient_item_id TEXT NOT NULL,
                col INTEGER NOT NULL,
                row INTEGER NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES shaped_recipes(recipe_id) ON DELETE CASCADE,
                FOREIGN KEY (ingredient_item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')
        self.conn.commit()

        self._migrate_shaped_recipes_unique()

    def _migrate_shaped_recipes_unique(self):
        """
        Ensure shaped_recipes.result_item_id has a UNIQUE constraint and that
        no duplicate rows exist. Older databases may have been seeded multiple
        times, so collapse duplicates to a single row before adding the
        constraint.
        """
        try:
            self.cursor.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'index' AND tbl_name = 'shaped_recipes' "
                "AND sql LIKE '%result_item_id%'"
            )
            existing_indexes = {row[0] for row in self.cursor.fetchall()}

            has_unique = False
            for idx_name in existing_indexes:
                self.cursor.execute(f"PRAGMA index_info({idx_name})")
                cols = [row[2] for row in self.cursor.fetchall()]
                if cols == ["result_item_id"]:
                    self.cursor.execute(
                        "SELECT sql FROM sqlite_master "
                        "WHERE type = 'index' AND name = ?",
                        (idx_name,)
                    )
                    row = self.cursor.fetchone()
                    if row and row[0] and "UNIQUE" in row[0].upper():
                        has_unique = True
                        break

            if not has_unique:
                self.cursor.execute('''
                    DELETE FROM recipe_matrix
                    WHERE recipe_id NOT IN (
                        SELECT MIN(recipe_id) FROM shaped_recipes GROUP BY result_item_id
                    )
                ''')
                self.cursor.execute('''
                    DELETE FROM shaped_recipes
                    WHERE recipe_id NOT IN (
                        SELECT MIN(recipe_id) FROM shaped_recipes GROUP BY result_item_id
                    )
                ''')
                self.cursor.execute('''
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_shaped_recipes_result_item_id
                    ON shaped_recipes(result_item_id)
                ''')
                self.conn.commit()
        except sqlite3.Error as exc:
            print(f"_migrate_shaped_recipes_unique failed: {exc}")
            self.conn.rollback()

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
                   price: int = 0, description: str = "",
                   on_hit_effects: list | None = None,
                   combat_style: str = 'sword') -> bool:
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
            on_hit_effects (list | None): Optional list of effect dicts
                describing on-hit effects (e.g. burn on hit).
            combat_style (str): Attack pattern ('sword', 'mace', 'axe', 'spear',
                'dagger', 'war_hammer').

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
                INSERT INTO weapons (item_id, weapon_class, damage, durability, max_durability, range,
                                    projectile_speed, cooldown, spread_degrees, cone_degrees, on_hit_effects, combat_style)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item_id, weapon_class, damage, durability, durability, range_val,
                  projectile_speed, cooldown, spread_degrees, cone_degrees, None if on_hit_effects is None else repr(on_hit_effects), combat_style))

            self.conn.commit()
            print(f"Weapon '{item_id}' added successfully.")
            return True
        except sqlite3.IntegrityError:
            self.conn.rollback()
            return False
        except sqlite3.Error as e:
            self.conn.rollback()
            return False

    def add_armor(self, item_id: str, name: str, image_path: str,
                   slot_type: str = "helmet", defense_value: int = 0,
                   price: int = 0, max_stack: int = 1, description: str = "") -> bool:
        """
        Add an armor item to the database.

        Args:
            item_id (str): Unique identifier for the armor.
            name (str): Display name or translation key.
            image_path (str): File path to the armor's texture.
            slot_type (str): Equipment slot type (helmet, chestplate, leggings, boots,
                             charm, gloves, ring, belt).
            defense_value (int): Flat damage reduction provided.
            price (int): Monetary value.
            max_stack (int): Maximum stack size (usually 1).
            description (str): Description text.

        Returns:
            bool: True if successful.
        """
        try:
            self.conn.execute("BEGIN TRANSACTION")

            self.cursor.execute('''
                INSERT INTO items (id, type, name, image_path, price, max_stack, description)
                VALUES (?, 'armor', ?, ?, ?, ?, ?)
            ''', (item_id, name, image_path, price, max_stack, description))

            self.cursor.execute('''
                INSERT INTO armor (item_id, slot_type, defense_value)
                VALUES (?, ?, ?)
            ''', (item_id, slot_type, defense_value))

            self.conn.commit()
            print(f"Armor '{item_id}' added successfully.")
            return True
        except sqlite3.IntegrityError:
            self.conn.rollback()
            return False
        except sqlite3.Error:
            self.conn.rollback()
            return False

    def add_tool(self, item_id: str, name: str, image_path: str,
                 tool_type: str = "generic", durability: int = 100,
                 power: int = 0, price: int = 0, max_stack: int = 1,
                 description: str = "", gather_type: str = None,
                 gather_yield_min: int = 1, gather_yield_max: int = 1) -> bool:
        """
        Add a tool item to the database.

        Tools are non-combat, non-consumable items used to perform a specific
        in-world action (fishing, mining, woodcutting, etc.). They typically
        do not stack and have their own durability / power stats.

        Args:
            item_id (str): Unique identifier for the tool.
            name (str): Display name or translation key.
            image_path (str): File path to the tool's texture.
            tool_type (str): Sub-category of the tool
                (e.g. "fishing", "pickaxe", "axe").
            durability (int): Maximum durability points.
            power (int): Generic effectiveness multiplier (e.g. catch power
                bonus for a fishing rod, mining speed for a pickaxe).
            price (int): Monetary value.
            max_stack (int): Maximum stack size (usually 1).
            description (str): Description text.
            gather_type (str | None): If set, the resource type this tool
                gathers ("wood", "stone", "ore", etc.). The GatheringController
                uses this to match a tool against tile properties such as
                ``choppable`` (matched by "wood") or ``minable`` (matched by
                "stone" or "ore"). ``None`` means the tool does not gather
                (e.g. a fishing rod).
            gather_yield_min (int): Lower bound of resource items produced
                per successful gather.
            gather_yield_max (int): Upper bound of resource items produced
                per successful gather.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            self.conn.execute("BEGIN TRANSACTION")

            self.cursor.execute('''
                INSERT INTO items (id, type, name, image_path, price, max_stack, description)
                VALUES (?, 'tool', ?, ?, ?, ?, ?)
            ''', (item_id, name, image_path, price, max_stack, description))

            self.cursor.execute('''
                INSERT INTO tools (item_id, tool_type, durability, max_durability, power,
                                   gather_type, gather_yield_min, gather_yield_max)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item_id, tool_type, durability, durability, power,
                  gather_type, gather_yield_min, gather_yield_max))

            self.conn.commit()
            print(f"Tool '{item_id}' added successfully.")
            return True
        except sqlite3.IntegrityError:
            self.conn.rollback()
            return False
        except sqlite3.Error:
            self.conn.rollback()
            return False

    def add_fish(self, item_id: str, name: str, image_path: str,
                 rarity: str = "common", difficulty: float = 0.3,
                 speed: float = 1.0, spawn_weight: int = 50,
                 base_price: int = 10, description: str = "") -> bool:
        """
        Add a fish item to the database.

        Fish are caught via the fishing minigame and stored in the
        inventory.  Each fish carries stats that map directly to the
        ``FishType`` dataclass used by the fishing controller.

        Args:
            item_id (str): Unique identifier for the fish.
            name (str): Display name or translation key.
            image_path (str): File path to the fish's sprite.
            rarity (str): Rarity tier — ``common``, ``uncommon``,
                ``rare``, or ``legendary``.
            difficulty (float): ``0.0`` (very easy) to ``1.0`` (very
                hard). Controls speed, direction-change frequency,
                and catch tolerance in the minigame.
            speed (float): Multiplier applied to the fish's base
                vertical speed on the catching bar.
            spawn_weight (int): Relative spawn weight when selecting
                a fish on a bite. Higher = more common.
            base_price (int): Gold value when sold.
            description (str): Description text.

        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        try:
            self.conn.execute("BEGIN TRANSACTION")

            self.cursor.execute('''
                INSERT INTO items (id, type, name, image_path, price, max_stack, description)
                VALUES (?, 'fish', ?, ?, ?, 64, ?)
            ''', (item_id, name, image_path, base_price, description))

            self.cursor.execute('''
                INSERT INTO fish (item_id, rarity, difficulty, speed, spawn_weight, base_price)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (item_id, rarity, difficulty, speed, spawn_weight, base_price))

            self.conn.commit()
            print(f"Fish '{item_id}' added successfully.")
            return True
        except sqlite3.IntegrityError:
            self.conn.rollback()
            return False
        except sqlite3.Error:
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
                   weapons.weapon_class, weapons.damage, weapons.durability,
                   weapons.max_durability AS weapon_max_durability, weapons.range,
                   weapons.projectile_speed, weapons.cooldown, weapons.spread_degrees,
                   weapons.cone_degrees, weapons.on_hit_effects, weapons.combat_style,
                   consumables.heal_amount,
                   armor.slot_type, armor.defense_value,
                   "tools".tool_type, "tools".durability AS tool_durability,
                   "tools".max_durability AS tool_max_durability, "tools".power,
                   "tools".gather_type, "tools".gather_yield_min, "tools".gather_yield_max,
                   fish.rarity, fish.difficulty, fish.speed AS fish_speed,
                   fish.spawn_weight, fish.base_price AS fish_base_price
            FROM items
            LEFT JOIN weapons ON items.id = weapons.item_id
            LEFT JOIN consumables ON items.id = consumables.item_id
            LEFT JOIN armor ON items.id = armor.item_id
            LEFT JOIN "tools" ON items.id = "tools".item_id
            LEFT JOIN fish ON items.id = fish.item_id
            WHERE items.id = ?
        ''', (item_id,))

        row = self.cursor.fetchone()
        if not row:
            return None

        item_data = dict(row)
        item_data["effects"] = []

        # Decode on_hit_effects for weapons, if any.
        if item_data.get("on_hit_effects"):
            import ast
            try:
                item_data["on_hit_effects"] = ast.literal_eval(item_data["on_hit_effects"])
            except (ValueError, SyntaxError, TypeError):
                item_data["on_hit_effects"] = []
        else:
            item_data["on_hit_effects"] = []

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
    
    def add_recipe(self, result_item_id: str, result_amount: int, ingredients: dict) -> bool:
        try:
            self.conn.execute("BEGIN TRANSACTION")
            
            self.cursor.execute('''
                INSERT INTO crafting_recipes (result_item_id, result_amount)
                VALUES (?, ?)
            ''', (result_item_id, result_amount))
            
            recipe_id = self.cursor.lastrowid
            
            for ing_id, req_amount in ingredients.items():
                self.cursor.execute('''
                    INSERT INTO recipe_ingredients (recipe_id, ingredient_item_id, required_amount)
                    VALUES (?, ?, ?)
                ''', (recipe_id, ing_id, req_amount))
                
            self.conn.commit()
            print(f"Recipe for '{result_item_id}' added successfully.")
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Error adding recipe: {e}")
            return False
        
    def get_all_recipes(self) -> list:
        self.cursor.execute('SELECT * FROM shaped_recipes')
        recipes_rows = self.cursor.fetchall()
        
        all_recipes = []
        for r_row in recipes_rows:
            recipe_id = r_row["recipe_id"]
            
            self.cursor.execute('SELECT * FROM recipe_matrix WHERE recipe_id = ?', (recipe_id,))
            matrix_rows = self.cursor.fetchall()
            
            matrix = [[None for _ in range(3)] for _ in range(3)]
            for m_row in matrix_rows:
                matrix[m_row["col"]][m_row["row"]] = m_row["ingredient_item_id"]
                
            all_recipes.append({
                "recipe_id": recipe_id,
                "result_id": r_row["result_item_id"],
                "amount": r_row["result_amount"],
                "matrix": matrix
            })
        return all_recipes
    
    def add_shaped_recipe(self, result_item_id: str, result_amount: int, grid: list) -> bool:
        try:
            self.cursor.execute(
                'SELECT 1 FROM shaped_recipes WHERE result_item_id = ?',
                (result_item_id,)
            )
            if self.cursor.fetchone() is not None:
                return False

            self.conn.execute("BEGIN TRANSACTION")

            self.cursor.execute('''
                INSERT INTO shaped_recipes (result_item_id, result_amount)
                VALUES (?, ?)
            ''', (result_item_id, result_amount))

            recipe_id = self.cursor.lastrowid

            for row in range(3):
                for col in range(3):
                    ingredient_id = grid[row][col]
                    if ingredient_id:
                        self.cursor.execute('''
                            INSERT INTO recipe_matrix (recipe_id, ingredient_item_id, col, row)
                            VALUES (?, ?, ?, ?)
                        ''', (recipe_id, ingredient_id, col, row))

            self.conn.commit()
            print(f"Recipe for '{result_item_id}' added successfully.")
            return True

        except Exception as e:
            self.conn.rollback()
            print(f"Failed to add recipe for '{result_item_id}': {e}")
            return False

    def close(self):
        """
        Close the database connection safely.
        """
        self.conn.close()