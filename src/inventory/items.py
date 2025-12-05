import pygame
from src.inventory.item_database import Item_database
from typing import TYPE_CHECKING

class Item:
    def __init__(self, data: dict):
        self.id = data["id"]
        self.name = data["name"]
        self.type = data["type"]
        self.max_stack = data.get("max_stack", 64)
        self.description = data.get("description", "")
        self.image = pygame.image.load(data["image_path"]).convert_alpha()

        self._cached_image = None
        self._cached_size = 0

    def resize(self, size: int):
        if self._cached_size != size:
            self._cached_image = pygame.transform.scale(self.image, (size, size))
            self._cached_size = size
        return self._cached_image
    
    def get_tooltip_text(self):
        return f"{self.name}\n{self.description}"

class Weapon(Item):
    def __init__(self, data: dict):
        super().__init__(data)
        self.damage = data.get("damage", 1)
        self.durability = data.get("durability", 100)
        self.range = data.get("range", 1.0)

    def get_tooltip_text(self):
        stats = f"Type: Weapon\nDamage: {self.damage}\nDurability: {self.durability}"
        return f"{self.name}\n{stats}\n{self.description}"    

class Consumable(Item):
    def __init__(self, data: dict):
        super().__init__(data)
        self.heal_amount = data.get("heal_amount", 0)
        
    def get_tooltip_text(self):
        stats = f"Type: Consumable\nHeal: +{self.heal_amount} HP"
        return f"{self.name}\n{stats}\n{self.description}"


class Armor(Item):
    def __init__(self, data: dict):
        super().__init__(data)
        pass

def create_item(item_id: str):
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