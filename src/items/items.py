import pygame
from src.core.logger import logger
from database.effects import create_effect

class Item:
    """
    Base class for all game items.

    Attributes:
        id (str): Unique identifier for the item.
        name_key (str): Translation key for the item name.
        type (str): Category of the item.
        max_stack (int): Maximum stack size in the inventory.
        price (int): Monetary value of the item.
        desc_key (str): Translation key for the description.
        image (pygame.Surface): The loaded item sprite.

    Methods:
        __init__(row: dict): Initialize item properties from a dictionary.
        name(): Property returning the translated item name.
        description(): Property returning the translated item description.
        resize(size: int): Return a cached resized surface of the item.
        get_tooltip_text(): Return formatted tooltip text.
        use(target): Abstract method for item usage logic.
    """
    def __init__(self, row: dict):
        self.id = row["id"]
        self.name_key = row["name"]
        self.type = row["type"]
        self.max_stack = row["max_stack"]
        self.price = row["price"]
        self.desc_key = row["description"] if row["description"] is not None else ""
        self.image = pygame.image.load(row["image_path"]).convert_alpha()

        self._cached_image = None
        self._cached_size = 0

    @property
    def name(self):
        return _(self.name_key)

    @property
    def description(self):
        return _(self.desc_key)

    def resize(self, size: int):
        if self._cached_size != size:
            self._cached_image = pygame.transform.scale(self.image, (size, size))
            self._cached_size = size
        return self._cached_image
    
    def get_tooltip_text(self):
        return f"{self.name}\n{self.description}"

    def use(self, target):
        pass


class Weapon(Item):
    """
    Base class for weapon items, providing shared combat statistics.

    Attributes:
        damage (int): Base damage dealt by the weapon.
        durability (int): Current weapon durability points.
        cooldown (int): Attack cooldown in milliseconds.
        weapon_class (str): Classification (e.g., melee, ranged).
        on_hit_effects (list): Optional list of effect dicts applied to a
            target each time the weapon lands a hit (e.g. Flaming Sword ->
            BurnEffect).
    """
    def __init__(self, row: dict):
        super().__init__(row)
        self.damage = row["damage"]
        self.durability = row["durability"]
        self.cooldown = row["cooldown"]
        self.weapon_class = row["weapon_class"]
        # Per-weapon on-hit effects (list of effect dicts).
        # We keep it as a plain attribute even if the column is missing so
        # that existing items (with no on-hit effects) keep working.
        self.on_hit_effects = []
        raw_on_hit = row.get("on_hit_effects")
        if raw_on_hit:
            if isinstance(raw_on_hit, str):
                import ast
                try:
                    self.on_hit_effects = ast.literal_eval(raw_on_hit)
                except (ValueError, SyntaxError, TypeError):
                    self.on_hit_effects = []
            elif isinstance(raw_on_hit, list):
                self.on_hit_effects = list(raw_on_hit)

    def _get_base_stats_text(self):
        weapon_label = f"{_('Weapon')} ({self.weapon_class.capitalize()})"
        return (
            f"{_('Type')}: {weapon_label}\n"
            f"{_('Damage')}: {self.damage}\n"
            f"{_('Durability')}: {self.durability}\n"
        )


class MeleeWeapon(Weapon):
    """
    Represents a melee combat weapon.
    """
    def __init__(self, row: dict):
        super().__init__(row)
        self.range = row["range"]

    def get_tooltip_text(self):
        base_stats = self._get_base_stats_text()
        stats = (
            f"{base_stats}"
            f"{_('Range')}: {self.range}\n"
            f"Price: ${self.price}"
        )
        return f"{self.name}\n{stats}\n{self.description}"    


class RangedWeapon(Weapon):
    """
    Represents a ranged combat weapon.
    """
    def __init__(self, row: dict):
        super().__init__(row)
        self.range = row["range"]
        self.projectile_speed = row["projectile_speed"]
        self.cone_degrees = row["cone_degrees"]
        self.spread_degrees = row["spread_degrees"]

    def get_tooltip_text(self):
        base_stats = self._get_base_stats_text()
        stats = (
            f"{base_stats}"
            f"{_('Range')}: {self.range}\n"
            f"{_('Proj. Speed')}: {self.projectile_speed}\n"
            f"Price: ${self.price}"
        )
        return f"{self.name}\n{stats}\n{self.description}"


class Consumable(Item):
    """
    Represents an item that can be used to restore health
    or apply temporary effects to the target.

    Attributes:
        heal_amount (int): Points of HP restored or lost.
        effects_list (list): Configuration for applying dynamic effects.
    """
    def __init__(self, row: dict):
        super().__init__(row)
        self.heal_amount = row.get("heal_amount", 0)
        self.effects_list = row.get("effects", [])

    def get_tooltip_text(self):
        stats = f"{_('Type')}: {_('Consumable')}"
        if self.heal_amount > 0:
            stats += f"\n{_('Heal')}: +{self.heal_amount} {_('HP')}"
        elif self.heal_amount < 0:
            stats += f"\n{_('Damage')}: {self.heal_amount} {_('HP')}"
        if self.effects_list:
            stats += f"\n{_('Effects')}:"
            for effect_data in self.effects_list:
                etype = effect_data.get("type", "unknown")
                dur = effect_data.get("duration", 0)
                stats += f"\n - {etype.capitalize()} ({dur}s)"

        stats += f"\nPrice: ${self.price}"
        return f"{self.name}\n{stats}\n{self.description}"

    def use(self, target):
        """
        Apply the consumable's effects to the target.

        Returns True when at least one effect was applied (HP, mana, or
        a status effect), False otherwise.
        """
        used = False
        if self.heal_amount != 0:
            new_hp = min(target.max_hp, max(0, target.hp + self.heal_amount))
            # Special case: very large heal_amount (e.g. Elixir of Life) acts
            # as a full restore, no matter the current missing HP.
            if self.heal_amount >= target.max_hp:
                target.hp = target.max_hp
            else:
                target.hp = new_hp
            used = True

        if self.effects_list:
            used = True
            for effect_data in self.effects_list:
                effect_obj = create_effect(effect_data)
                if effect_obj:
                    target.add_effect(effect_obj)
        return used


class Armor(Item):
    """
    Represents an armor item.
    """
    def __init__(self, row: dict):
        super().__init__(row)


def create_item(item_id: str):
    """
    Factory function to instantiate the appropriate item class.

    Args:
        item_id (str): The identifier to look up in the database.

    Returns:
        Item | None: An instance of a specific item class or None.
    """
    from database.GP_database import Gp_database 
    
    db = Gp_database()
    row = db.get_item(item_id)
    db.close()

    if not row:
        logger.error(f"Предмет '{item_id}' не знайдено в базі даних!")
        return None

    item_type = row.get("type")
    
    if item_type == "weapon":
        w_class = row.get("weapon_class")
        if w_class == "ranged":
            return RangedWeapon(row)
        else:
            return MeleeWeapon(row)
    elif item_type in ("food", "potion"):
        return Consumable(row)
    elif item_type == "armor":
        return Armor(row)
    else:
        logger.warning(f"Unknown item type '{item_type}' for '{item_id}'. Defaulting to generic Item.")
        return Item(row)