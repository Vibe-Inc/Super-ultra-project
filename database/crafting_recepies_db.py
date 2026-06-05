import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from database.GP_database import Gp_database

def seed_recipes(db=None):
    if db is None:
        db = Gp_database()
        should_close = True
    else:
        should_close = False

    db.add_shaped_recipe(
        result_item_id="potion_of_confusion",
        result_amount=1,
        grid=[
            ["moldy_bread", "apple", None],
            [None,          None,    None],
            [None,          None,    None]
        ]
    )

    # ------------------ Minecraft-style stone & wood recipes ------------------

    # Sticks: 2 wood stacked vertically -> 4 sticks
    db.add_shaped_recipe(
        result_item_id="stick",
        result_amount=4,
        grid=[
            ["wood", None, None],
            ["wood", None, None],
            [None,  None, None]
        ]
    )

    # Wooden Pickaxe: 3 wood (top row) + 2 sticks (middle & bottom of centre column)
    db.add_shaped_recipe(
        result_item_id="wooden_pickaxe",
        result_amount=1,
        grid=[
            ["wood",  "wood", "wood"],
            [None,   "stick", None],
            [None,   "stick", None]
        ]
    )

    # Wooden Axe: 3 wood (V shape) + 2 sticks (middle & bottom of centre column)
    db.add_shaped_recipe(
        result_item_id="wooden_axe",
        result_amount=1,
        grid=[
            ["wood", "wood", None],
            [None,  "stick", None],
            [None,  "stick", None]
        ]
    )

    # Wooden Sword: 2 wood (top & middle) + 1 stick (bottom of centre column)
    db.add_shaped_recipe(
        result_item_id="wooden_sword",
        result_amount=1,
        grid=[
            ["wood", None,  None],
            ["wood", None,  None],
            [None,  "stick", None]
        ]
    )

    # Stone Pickaxe: 3 stone (top row) + 2 sticks (middle & bottom of centre column)
    db.add_shaped_recipe(
        result_item_id="stone_pickaxe",
        result_amount=1,
        grid=[
            ["stone", "stone", "stone"],
            [None,    "stick",  None],
            [None,    "stick",  None]
        ]
    )

    # Stone Axe: 3 stone (V shape) + 2 sticks (middle & bottom of centre column)
    db.add_shaped_recipe(
        result_item_id="stone_axe",
        result_amount=1,
        grid=[
            ["stone", "stone", None],
            [None,    "stick",  None],
            [None,    "stick",  None]
        ]
    )

    if should_close:
        db.close()

if __name__ == "__main__":
    seed_recipes()