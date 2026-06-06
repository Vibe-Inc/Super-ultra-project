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

    # ------------------ Iron tier workbench recipes ------------------

    # Iron Pickaxe: 3 iron_ingot (top row) + 2 sticks (centre column)
    db.add_shaped_recipe(
        result_item_id="iron_pickaxe",
        result_amount=1,
        grid=[
            ["iron_ingot", "iron_ingot", "iron_ingot"],
            [None,         "stick",      None],
            [None,         "stick",      None]
        ]
    )

    # Iron Axe: 3 iron_ingot (V shape) + 2 sticks (centre column)
    db.add_shaped_recipe(
        result_item_id="iron_axe",
        result_amount=1,
        grid=[
            ["iron_ingot", "iron_ingot", None],
            [None,         "stick",      None],
            [None,         "stick",      None]
        ]
    )

    # Iron Sword: 2 iron_ingot (top & middle) + 1 stick (bottom of centre column)
    db.add_shaped_recipe(
        result_item_id="iron_sword",
        result_amount=1,
        grid=[
            ["iron_ingot", None,  None],
            ["iron_ingot", None,  None],
            [None,         "stick", None]
        ]
    )

    # Iron Helmet: 5 iron_ingot in helmet pattern
    db.add_shaped_recipe(
        result_item_id="iron_helmet",
        result_amount=1,
        grid=[
            ["iron_ingot", "iron_ingot", "iron_ingot"],
            ["iron_ingot", None,         "iron_ingot"],
            [None,         None,         None]
        ]
    )

    # Iron Chestplate: 8 iron_ingot in chestplate pattern
    db.add_shaped_recipe(
        result_item_id="iron_chestplate",
        result_amount=1,
        grid=[
            ["iron_ingot", None,         "iron_ingot"],
            ["iron_ingot", "iron_ingot", "iron_ingot"],
            ["iron_ingot", "iron_ingot", "iron_ingot"]
        ]
    )

    # Iron Leggings: 7 iron_ingot in leggings pattern
    db.add_shaped_recipe(
        result_item_id="iron_leggings",
        result_amount=1,
        grid=[
            ["iron_ingot", "iron_ingot", "iron_ingot"],
            ["iron_ingot", None,         "iron_ingot"],
            ["iron_ingot", None,         "iron_ingot"]
        ]
    )

    # Iron Boots: 4 iron_ingot in boots pattern
    db.add_shaped_recipe(
        result_item_id="iron_boots",
        result_amount=1,
        grid=[
            [None,         None,         None],
            ["iron_ingot", None,         "iron_ingot"],
            ["iron_ingot", None,         "iron_ingot"]
        ]
    )

    # ------------------ Steel tier workbench recipes ------------------

    # Steel Helmet: 5 steel_ingot in helmet pattern
    db.add_shaped_recipe(
        result_item_id="steel_helmet",
        result_amount=1,
        grid=[
            ["steel_ingot", "steel_ingot", "steel_ingot"],
            ["steel_ingot", None,          "steel_ingot"],
            [None,          None,          None]
        ]
    )

    # Steel Chestplate: 8 steel_ingot in chestplate pattern
    db.add_shaped_recipe(
        result_item_id="steel_chestplate",
        result_amount=1,
        grid=[
            ["steel_ingot", None,          "steel_ingot"],
            ["steel_ingot", "steel_ingot", "steel_ingot"],
            ["steel_ingot", "steel_ingot", "steel_ingot"]
        ]
    )

    # Steel Leggings: 7 steel_ingot in leggings pattern
    db.add_shaped_recipe(
        result_item_id="steel_leggings",
        result_amount=1,
        grid=[
            ["steel_ingot", "steel_ingot", "steel_ingot"],
            ["steel_ingot", None,          "steel_ingot"],
            ["steel_ingot", None,          "steel_ingot"]
        ]
    )

    # Steel Boots: 4 steel_ingot in boots pattern
    db.add_shaped_recipe(
        result_item_id="steel_boots",
        result_amount=1,
        grid=[
            [None,          None,          None],
            ["steel_ingot", None,          "steel_ingot"],
            ["steel_ingot", None,          "steel_ingot"]
        ]
    )

    # Steel Sword: 2 steel_ingot (top & middle) + 1 stick (bottom of centre column)
    db.add_shaped_recipe(
        result_item_id="steel_sword",
        result_amount=1,
        grid=[
            ["steel_ingot", None,   None],
            ["steel_ingot", None,   None],
            [None,          "stick", None]
        ]
    )

    # ------------------ Accessories & utility ------------------

    # Iron Ring: 1 iron_ingot in the centre -> 1 iron_ring
    db.add_shaped_recipe(
        result_item_id="iron_ring",
        result_amount=1,
        grid=[
            [None,         None, None],
            [None,         "iron_ingot", None],
            [None,         None, None]
        ]
    )

    # Steel Ring: 1 steel_ingot in the centre -> 1 steel_ring
    db.add_shaped_recipe(
        result_item_id="steel_ring",
        result_amount=1,
        grid=[
            [None,          None, None],
            [None,          "steel_ingot", None],
            [None,          None, None]
        ]
    )

    # Iron Gloves: 2 iron_ingot (one per hand row)
    db.add_shaped_recipe(
        result_item_id="iron_gloves",
        result_amount=1,
        grid=[
            [None,         None, None],
            [None,         None, None],
            ["iron_ingot", "iron_ingot", None]
        ]
    )

    # Fishing Rod: 3 sticks diagonally + 2 sticks (Minecraft uses string, we don't have that)
    db.add_shaped_recipe(
        result_item_id="fishing_rod",
        result_amount=1,
        grid=[
            [None,   None,   "stick"],
            [None,   "stick", None],
            ["stick", None,  None]
        ]
    )

    # ------------------ Flint tier workbench recipes ------------------

    # Sharpen Stone: 2 flint stacked in the left column
    db.add_shaped_recipe(
        result_item_id="sharpen_stone",
        result_amount=1,
        grid=[
            ["flint", None, None],
            ["flint", None, None],
            [None,   None, None]
        ]
    )

    # Flint Pickaxe: 3 flint (top row) + 2 sticks (centre column)
    db.add_shaped_recipe(
        result_item_id="flint_pickaxe",
        result_amount=1,
        grid=[
            ["flint", "flint", "flint"],
            [None,   "stick",  None],
            [None,   "stick",  None]
        ]
    )

    # Flint Axe: 3 flint (V shape) + 2 sticks (centre column)
    db.add_shaped_recipe(
        result_item_id="flint_axe",
        result_amount=1,
        grid=[
            ["flint", "flint", None],
            [None,   "stick",  None],
            [None,   "stick",  None]
        ]
    )

    if should_close:
        db.close()

if __name__ == "__main__":
    seed_recipes()
