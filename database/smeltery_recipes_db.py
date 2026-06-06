"""
Smeltery recipe definitions for the coke oven and blast furnace.

Each entry is a plain Python dict, kept in a module-level list so the
``SmelteryMenu`` can iterate them without any database I/O.

Schema
------
Coke oven (single-input furnace):
    {
        "input_id": str,             # item id required in the input slot
        "input_amount": int,         # how many of that item are consumed
        "primary_output_id": str,   # main product, appears in the output slot
        "primary_output_amount": int,
        "duration": float,           # seconds for one batch
        "heat_color": tuple,         # RGB used to tint the flame/progress
    }

Blast furnace (two-input furnace: material + fuel):
    {
        "input_item_id": str,        # primary material (e.g. iron_ore)
        "input_item_amount": int,
        "input_fuel_id": str,        # fuel consumed (e.g. coke)
        "input_fuel_amount": int,
        "primary_output_id": str,
        "primary_output_amount": int,
        "duration": float,
        "heat_color": tuple,
    }
"""

COKE_OVEN_RECIPES = [
    {
        "input_id": "coal",
        "input_amount": 1,
        "primary_output_id": "coke",
        "primary_output_amount": 1,
        "duration": 18.0,
        "heat_color": (220, 80, 30),
    },
    {
        "input_id": "wood",
        "input_amount": 1,
        "primary_output_id": "coal",
        "primary_output_amount": 1,
        "duration": 12.0,
        "heat_color": (220, 80, 30),
    },
]

BLAST_FURNACE_RECIPES = [
    {
        "input_item_id": "iron_ore",
        "input_item_amount": 1,
        "input_fuel_id": "coke",
        "input_fuel_amount": 1,
        "primary_output_id": "iron_ingot",
        "primary_output_amount": 1,
        "duration": 20.0,
        "heat_color": (255, 130, 40),
    },
    {
        "input_item_id": "iron_ingot",
        "input_item_amount": 1,
        "input_fuel_id": "coke",
        "input_fuel_amount": 1,
        "primary_output_id": "steel_ingot",
        "primary_output_amount": 1,
        "duration": 30.0,
        "heat_color": (255, 200, 90),
    },
]


def get_coke_recipe_for_input(item_id):
    """Return the first coke oven recipe that matches ``item_id`` or None."""
    for recipe in COKE_OVEN_RECIPES:
        if recipe["input_id"] == item_id:
            return recipe
    return None


def get_blast_recipe_for_inputs(item_id, fuel_id):
    """Return the first blast furnace recipe that matches the given pair or None."""
    for recipe in BLAST_FURNACE_RECIPES:
        if recipe["input_item_id"] == item_id and recipe["input_fuel_id"] == fuel_id:
            return recipe
    return None


# ---------------------------------------------------------------------------
# Anvil repair recipes
# ---------------------------------------------------------------------------
# The anvil tab of the smeltery is used to repair weapons, armor and tools
# that have lost durability.  The repair is driven by material ingots:
# iron_ingot restores 35% of max durability and steel_ingot restores 75%.
# The actual item-to-repair isn't named in the recipe -- the anvil accepts
# *any* damaged weapon/armor/tool in its item slot -- so the recipe only
# describes the material that fuels the repair.
#
# Schema
# ------
# Anvil material recipe:
#     {
#         "material_id": str,          # item id required in the material slot
#         "material_amount": int,      # how many of that item are consumed
#         "repair_fraction": float,    # 0.0..1.0, fraction of max durability restored
#         "duration": float,           # seconds for one repair job
#         "heat_color": tuple,         # RGB used to tint the flame/progress
#     }
#
# Material-less repairs (free of charge) are intentionally NOT supported:
# the anvil always requires a fuel material to fix anything.

ANVIL_RECIPES = [
    {
        "material_id": "iron_ingot",
        "material_amount": 1,
        "repair_fraction": 0.35,
        "duration": 4.0,
        "heat_color": (255, 150, 60),
    },
    {
        "material_id": "steel_ingot",
        "material_amount": 1,
        "repair_fraction": 0.75,
        "duration": 6.0,
        "heat_color": (255, 210, 100),
    },
]


def get_anvil_recipe_for_material(material_id):
    """Return the first anvil material recipe matching ``material_id`` or None."""
    for recipe in ANVIL_RECIPES:
        if recipe["material_id"] == material_id:
            return recipe
    return None


def find_coke_recipe_by_primary(output_id):
    for recipe in COKE_OVEN_RECIPES:
        if recipe["primary_output_id"] == output_id:
            return recipe
    return None


def find_blast_recipe_by_primary(output_id):
    for recipe in BLAST_FURNACE_RECIPES:
        if recipe["primary_output_id"] == output_id:
            return recipe
    return None
