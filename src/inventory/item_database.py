Weapon_database = {
    "dull_sword": {
        "id": "dull_sword",
        "type": "weapon",
        "name": "Dull Sword",
        "image_path": "assets/items/weapons/swords/dull_sword.png",
        "damage": 5,
        "durability": 50,
        "description": "A worn-out sword with a dull blade. Thats about it."
    }
}

Consumable_database = {
    "apple": {
        "id": "apple",
        "type": "food",
        "name": "Apple",
        "image_path": "assets/items/consumables/food/apple.png",
        "heal_amount": 10,
        "max_stack": 64,
        "description": "An apple."
    }
}

Item_database = {
    **Weapon_database,
    **Consumable_database
}