def _(x): return x

Weapon_database = {
    "dull_sword": {
        "id": "dull_sword",
        "type": "weapon",
        "name": _("Dull Sword"),
        "image_path": "assets/items/weapons/swords/dull_sword.png",
        "damage": 5,
        "durability": 50,
        "price": 50,
        "description": _("A worn-out sword with a dull blade. Thats about it.")
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
    }
}
#Potion_database = {}

Consumable_database = {
**Food_database
#**Potion_database
}

Item_database = {
    **Weapon_database,
    **Consumable_database
}