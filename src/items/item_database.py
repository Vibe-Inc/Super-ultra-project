def _(x): return x

Weapon_database = {
    "dull_sword": {
        "id": "dull_sword",
        "type": "weapon",
        "name": _("Dull Sword"),
        "image_path": "assets/items/weapons/swords/dull_sword.png",
        "damage": 20,
        "durability": 50,
        "cone_degrees": 120,
        "price": 50,
        "description": _("A worn-out sword with a dull blade. Thats about it.")
    },
    "wooden_bow": {
        "id": "wooden_bow",
        "type": "weapon",
        "weapon_class": "bow",
        "name": _("Wooden Bow"),
        "image_path": "assets/items/weapons/bows/wooden_bow.png",
        "damage": 14,
        "durability": 40,
        "range": 520,
        "projectile_speed": 900,
        "cooldown": 650,
        "spread_degrees": 4,
        "price": 75,
        "description": _("A simple bow made of wood. Lightweight but reliable.")
    }
}



Food_database = {
"apple": {
        "id": "apple",
        "type": "food",
        "name": _("Apple"),
        "image_path": "assets/items/consumables/food/apple.png",
        "heal_amount": 10,
        "max_stack": 64,
        "price": 5,
        "description": _("An apple."),
        "effects": [
            {"type": "regeneration", "duration": 5, "amount_per_sec": 2}
        ]
    },
"moldy_bread": {
        "id": "moldy_bread",
        "type": "food",
        "name": _("Moldy Bread"),
        "image_path": "assets/items/consumables/food/moldy_bread.png",
        "heal_amount": -5,
        "max_stack": 64,
        "price": 2,
        "description": _("A piece of bread that has gone bad."),
        "effects": [
            {"type": "poison", "duration": 5, "damage_per_sec": 2}
        ]
    }
}

Potion_database = {
"small_health_potion": {
        "id": "small_health_potion",
        "type": "potion",
        "name": _("Small Health Potion"),
        "image_path": "assets/items/consumables/potion/small_health_potion.png",
        "heal_amount": 30,
        "max_stack": 1,
        "price": 30,
        "description": _("A small potion that restores health."),
        "effects": [
            {"type": "regeneration", "duration": 3, "amount_per_sec": 10}
        ]
    },
"large_health_potion": {
        "id": "large_health_potion",
        "type": "potion",
        "name": _("Large Health Potion"),
        "image_path": "assets/items/consumables/potion/large_health_potion.png",
        "heal_amount": 70,
        "max_stack": 1,
        "price": 60,
        "description": _("A large potion that restores a significant amount of health."),
        "effects": [
            {"type": "regeneration", "duration": 5, "amount_per_sec": 14}
        ]
    },
"potion_of_confusion": {
        "id": "potion_of_confusion",
        "type": "potion",
        "name": _("Potion of Confusion"),
        "image_path": "assets/items/consumables/potion/potion_of_confusion.png",
        "heal_amount": 0,
        "max_stack": 1,
        "price": 25,
        "description": _("A mix oh herbs and spices that causes confusion."),
        "effects": [
            {"type": "confusion", "duration": 30},
            {"type": "dizziness", "duration": 30}
        ]
    }
}

Consumable_database = {
**Food_database,
**Potion_database
}

Item_database = {
    **Weapon_database,
    **Consumable_database
}