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

    # String: 2 fiber stacked vertically -> 1 string
    db.add_shaped_recipe(
        result_item_id="string",
        result_amount=1,
        grid=[
            ["fiber", None, None],
            ["fiber", None, None],
            [None,   None, None]
        ]
    )

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

    # ------------------ Hammer tools ------------------

    # Stone Hammer: 4 stone (top row + center) + 2 sticks (centre column)
    db.add_shaped_recipe(
        result_item_id="stone_hammer",
        result_amount=1,
        grid=[
            ["stone", "stone", "stone"],
            ["stone", "stick",  None],
            [None,    "stick",  None]
        ]
    )

    # Iron Hammer: 4 iron_ingot (top row + center) + 2 sticks (centre column)
    db.add_shaped_recipe(
        result_item_id="iron_hammer",
        result_amount=1,
        grid=[
            ["iron_ingot", "iron_ingot", "iron_ingot"],
            ["iron_ingot", "stick",      None],
            [None,         "stick",      None]
        ]
    )

    # ------------------ Melee weapons ------------------

    # Dull Sword: 2 iron_ingot vertically (worn-down blade, no handle)
    db.add_shaped_recipe(
        result_item_id="dull_sword",
        result_amount=1,
        grid=[
            ["iron_ingot", None,  None],
            ["iron_ingot", None,  None],
            [None,         None,  None]
        ]
    )

    # Battle Axe: 3 steel_ingot in axe shape + 2 sticks
    db.add_shaped_recipe(
        result_item_id="battle_axe",
        result_amount=1,
        grid=[
            ["steel_ingot", "steel_ingot", None],
            ["steel_ingot", "stick",       None],
            [None,          "stick",       None]
        ]
    )

    # War Hammer: 4 steel_ingot (top row + center) + 2 sticks
    db.add_shaped_recipe(
        result_item_id="war_hammer",
        result_amount=1,
        grid=[
            ["steel_ingot", "steel_ingot", "steel_ingot"],
            ["steel_ingot", "stick",       None],
            [None,          "stick",       None]
        ]
    )

    # Mace: 3 iron_ingot on top row + 2 sticks
    db.add_shaped_recipe(
        result_item_id="mace",
        result_amount=1,
        grid=[
            ["iron_ingot", "iron_ingot", "iron_ingot"],
            [None,         "stick",      None],
            [None,         "stick",      None]
        ]
    )

    # Spear: 1 iron_ingot tip + 2 sticks shaft
    db.add_shaped_recipe(
        result_item_id="spear",
        result_amount=1,
        grid=[
            ["iron_ingot", None,  None],
            [None,         "stick", None],
            [None,         "stick", None]
        ]
    )

    # ------------------ Ranged weapons ------------------

    # Wooden Bow: 4 sticks in bow shape
    db.add_shaped_recipe(
        result_item_id="wooden_bow",
        result_amount=1,
        grid=[
            [None,  "stick", None],
            ["stick", None,  "stick"],
            [None,  "stick", None]
        ]
    )

    # Hunting Bow: reinforced with string
    db.add_shaped_recipe(
        result_item_id="hunting_bow",
        result_amount=1,
        grid=[
            [None,  "stick",  None],
            ["stick", "string", "stick"],
            [None,  "stick",  None]
        ]
    )

    # Longbow: 4 sticks + string + leather grip
    db.add_shaped_recipe(
        result_item_id="longbow",
        result_amount=1,
        grid=[
            [None,    "stick",  "string"],
            ["stick",  None,    "stick"],
            [None,    "stick",  None]
        ]
    )

    # Crossbow: mechanical - iron_ingot + sticks + string
    db.add_shaped_recipe(
        result_item_id="crossbow",
        result_amount=1,
        grid=[
            ["iron_ingot", None,    "string"],
            [None,         "stick",  None],
            [None,         "stick",  None]
        ]
    )

    # Throwing Dagger: 2 flint stacked vertically
    db.add_shaped_recipe(
        result_item_id="throwing_dagger",
        result_amount=1,
        grid=[
            ["flint", None, None],
            ["flint", None, None],
            [None,    None, None]
        ]
    )

    # ------------------ Leather armor ------------------

    # Leather Gloves: 2 leather in bottom row
    db.add_shaped_recipe(
        result_item_id="leather_gloves",
        result_amount=1,
        grid=[
            [None,     None,     None],
            [None,     None,     None],
            ["leather", "leather", None]
        ]
    )

    # Leather Belt: 3 leather in middle row
    db.add_shaped_recipe(
        result_item_id="leather_belt",
        result_amount=1,
        grid=[
            [None,     None,     None],
            ["leather", "leather", "leather"],
            [None,     None,     None]
        ]
    )

    # ------------------ Charms ------------------

    # Defense Charm: iron_ingot + flint (crude protective charm)
    db.add_shaped_recipe(
        result_item_id="defense_charm",
        result_amount=1,
        grid=[
            ["iron_ingot", "flint", None],
            [None,         None,    None],
            [None,         None,    None]
        ]
    )

    # Silver Charm: silver_ingot + flint (enchanted silver charm)
    db.add_shaped_recipe(
        result_item_id="silver_charm",
        result_amount=1,
        grid=[
            ["silver_ingot", "flint", None],
            [None,           None,    None],
            [None,           None,    None]
        ]
    )

    # Lantern: iron_ingot + 2 coal
    db.add_shaped_recipe(
        result_item_id="lantern",
        result_amount=1,
        grid=[
            ["iron_ingot", "coal", None],
            [None,         "coal",  None],
            [None,         None,   None]
        ]
    )

    # Light Ring: iron_ring + coal + flint (enchanted light source)
    db.add_shaped_recipe(
        result_item_id="light_ring",
        result_amount=1,
        grid=[
            ["iron_ring", "coal",  None],
            ["flint",     None,    None],
            [None,        None,    None]
        ]
    )

    # Gay Ring: steel_ring + coal + flint (rainbow magic)
    db.add_shaped_recipe(
        result_item_id="gay_ring",
        result_amount=1,
        grid=[
            ["steel_ring", "coal",  None],
            ["flint",      None,    None],
            [None,         None,    None]
        ]
    )

    if should_close:
        db.close()

if __name__ == "__main__":
    seed_recipes()
