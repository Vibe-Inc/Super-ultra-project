import pygame
from src.items.item_database import Item_database
from src.items.effects import create_effect

class Item:
    """
    Represents a generic inventory item.

    This class provides basic item properties, image loading, and translation support for name and description.

    Attributes:
        id (str):
            Unique identifier for the item.
        name_key (str):
            The original (untranslated) name string for translation lookup.
        type (str):
            The type/category of the item (e.g., 'weapon', 'food', 'armor').
        max_stack (int):
            Maximum number of items per inventory slot.
        desc_key (str):
            The original (untranslated) description string for translation lookup.
        image (pygame.Surface):
            The item's image surface.
        _cached_image (pygame.Surface | None):
            Cached resized image for performance.
        _cached_size (int):
            Size of the cached image.

    Properties:
        name (str):
            The translated name of the item.
        description (str):
            The translated description of the item.

    Methods:
        resize(size):
            Resize and cache the item's image.
            Args:
                size (int): The desired size in pixels.
            Returns:
                pygame.Surface: The resized image.
        get_tooltip_text():
            Get a tooltip string with the item's name and description.
            Returns:
                str: Tooltip text.
    """
    def __init__(self, data: dict):
        self.id = data["id"]
        self.name_key = data["name"]
        self.type = data["type"]
        self.max_stack = data.get("max_stack", 64)
        self.price = data.get("price", 0)
        self.desc_key = data.get("description", "")
        self.image = pygame.image.load(data["image_path"]).convert_alpha()

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
        """
        Use the item on the target character.
        """
        pass

class Weapon(Item):
    """
    Represents a weapon item with damage and durability.

    Attributes:
        damage (int):
            The amount of damage this weapon deals.
        durability (int):
            The remaining durability of the weapon.
        range (float):
            The attack range of the weapon.

    Methods:
        get_tooltip_text():
            Get a tooltip string with weapon stats and description.
            Returns:
                str: Tooltip text.
    """
    def __init__(self, data: dict):
        super().__init__(data)
        self.damage = data.get("damage", 1)
        self.durability = data.get("durability", 100)
        self.range = data.get("range", 1.0)

    def get_tooltip_text(self):
        stats = f"{_('Type')}: {_('Weapon')}\n{_('Damage')}: {self.damage}\n{_('Durability')}: {self.durability}\nPrice: ${self.price}"
        return f"{self.name}\n{stats}\n{self.description}"    

class Consumable(Item):
    """
    Represents a consumable item (e.g., food, potion).

    Attributes:
        heal_amount (int):
            The amount of HP restored by this item.
        effects_data (list[dict]):
            Configuration for effects to apply.

    Methods:
        get_tooltip_text():
            Get a tooltip string with consumable stats and description.
            Returns:
                str: Tooltip text.
        use(target):
            Apply healing and effects to the target.
    """

    def __init__(self, data: dict):
        super().__init__(data)
        self.heal_amount = data.get("heal_amount", 0)
        self.effects_list = data.get("effects", [])
        
    def get_tooltip_text(self):
        stats = f"{_('Type')}: {_('Consumable')}"
        if self.heal_amount > 0:
            stats += f"\n{_('Heal')}: +{self.heal_amount} {_('HP')}"
        
        if self.effects_list:
            stats += f"\n{_('Effects')}:"
            for effect_data in self.effects_list:
                etype = effect_data.get("type")
                dur = effect_data.get("duration")

                stats += f"\n - {etype.capitalize()} ({dur}s)"
        
        stats += f"\nPrice: ${self.price}"
        return f"{self.name}\n{stats}\n{self.description}"

    def use(self, target):
        if self.heal_amount > 0:
            target.hp = min(100, target.hp + self.heal_amount)
            used = True
        
        if self.effects_list:
            for effect_data in self.effects_list:
                effect_obj = create_effect(effect_data)
                
                if effect_obj:
                    target.add_effect(effect_obj)
        return used


class Armor(Item):
    """
    Represents an armor item. (Extend with armor-specific stats as needed.)
    """
    def __init__(self, data: dict):
        super().__init__(data)
        pass

def create_item(item_id: str):
    """
    Factory function to create an item instance by ID.

    Args:
        item_id (str): The unique identifier of the item in the item database.

    Returns:
        Item | Weapon | Consumable | Armor: The instantiated item object of the appropriate type.
    """
    data = Item_database.get(item_id)
    item_type = data.get("type")
    
    if item_type == "weapon":
        return Weapon(data)
    elif item_type == "food":
        return Consumable(data)
    elif item_type == "armor":
        return Armor(data)
    else:
        return Item(data)