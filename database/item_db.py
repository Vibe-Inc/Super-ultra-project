import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from GP_database import Gp_database

def seed_items():
    """
    Execute the database population process.

    This function connects to the Gp_database, calls insertion methods for various item
    categories, and closes the connection once complete. It handles weapons with
    combat statistics, food with minor healing or damage effects, and potions
    with complex dynamic effects.
    """
    print("Starting database population...")
    db = Gp_database()

    db.add_weapon(
        item_id="dull_sword",
        name="Dull Sword", 
        image_path="assets/items/weapons/swords/dull_sword.png",
        weapon_class="melee",
        damage=20, durability=50, cone_degrees=120.0, price=50,
        description="A worn-out sword with a dull blade. Thats about it."
    )

    db.add_weapon(
        item_id="wooden_bow",
        name="Wooden Bow",
        image_path="assets/items/weapons/bows/wooden_bow.png",
        weapon_class="ranged",
        damage=14, durability=40, range_val=520, projectile_speed=900, cooldown=650, spread_degrees=4.0, price=75,
        description="A simple bow made of wood. Lightweight but reliable."
    )

    db.add_consumable(
        item_id="apple",
        item_type="food",
        name="Apple",
        image_path="assets/items/consumables/food/apple.png",
        heal_amount=10,
        max_stack=64,
        price=5,
        description="An apple.",
        effects=[{"type": "regeneration", "duration": 5, "amount_per_sec": 2}]
    )

    db.add_consumable(
        item_id="moldy_bread",
        item_type="food",
        name="Moldy Bread",
        image_path="assets/items/consumables/food/moldy_bread.png",
        heal_amount=-5,
        max_stack=64,
        price=2,
        description="A piece of bread that has gone bad.",
        effects=[{"type": "poison", "duration": 5, "damage_per_sec": 2}]
    )

    db.add_consumable(
        item_id="small_health_potion",
        item_type="potion",
        name="Small Health Potion",
        image_path="assets/items/consumables/potion/small_health_potion.png",
        heal_amount=30,
        max_stack=1,
        price=30,
        description="A small potion that restores health.",
        effects=[{"type": "regeneration", "duration": 3, "amount_per_sec": 10}]
    )

    db.add_consumable(
        item_id="large_health_potion",
        item_type="potion",
        name="Large Health Potion",
        image_path="assets/items/consumables/potion/large_health_potion.png",
        heal_amount=70,
        max_stack=1,
        price=60,
        description="A large potion that restores a significant amount of health.",
        effects=[{"type": "regeneration", "duration": 5, "amount_per_sec": 14}]
    )

    db.add_consumable(
        item_id="potion_of_confusion",
        item_type="potion",
        name="Potion of Confusion",
        image_path="assets/items/consumables/potion/potion_of_confusion.png",
        heal_amount=0,
        max_stack=1,
        price=25,
        description="A mix oh herbs and spices that causes confusion.",
        effects=[
            {"type": "confusion", "duration": 30},
            {"type": "dizziness", "duration": 30}
        ]
    )

    db.close()
    print("Population complete!")

if __name__ == "__main__":
    seed_items()