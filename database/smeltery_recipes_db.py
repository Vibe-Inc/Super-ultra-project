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
        "tier": str,                 # optional
        "minigame_chain": list,      # optional, list of minigame ids for
                                     # multi-stage challenges on high-tier
                                      # recipes (steel, etc.)
    }
"""

# ---------------------------------------------------------------------------
# Minigame registry
# ---------------------------------------------------------------------------
# Each id below maps to a callable in :mod:`src.minigames.smeltery_minigames`
# that launches a small skill challenge whenever the smelting batch that
# uses it finishes.  Iron and steel recipes use the "quench" / "tending"
# challenges so the high-end materials feel meaningfully harder than
# the easy charcoal / coal batches.

#: Minigame used by the wood -> coal conversion in the coke oven.
#: Kept on the "tending" minigame because the player will mostly be
#: running the oven for fuel -- the challenge is light and forgiving.
MINIGAME_NONE = "none"

#: Heat-bar hold challenge used by all coke oven recipes.  The player
#: must keep a moving "bellows" indicator inside a target zone for a
#: short period; success restores the coal/coke yield to 1, failure
#: loses a fraction of the output.
MINIGAME_TENDING = "tending"

#: Heat-bar hold + clicking "bellows" pulses for the iron-ore -> iron
#: ingot batch.  Faster cycle than the coke oven, narrower target.
MINIGAME_FORGE = "forge"

#: Quench-timing challenge for the iron -> steel upgrade batch.  This
#: is the toughest smelting minigame in the game: the player has to
#: click within a rapidly-narrowing timing window to seal the steel.
#: Failure burns a fraction of the ingot.
MINIGAME_QUENCH = "quench"

#: Bellows pumping challenge for the iron-ore + coal -> iron-ingot path.
#: Player must rhythmically pump (click / SPACE) to keep pressure in
#: a target zone; the fire dies if pressure drops too low for too long.
MINIGAME_BELLOWS = "bellows"

#: Colour-match tempering challenge for high-end steel.  An ingot cycles
#: through colours; the player clicks when it matches the target colour.
#: 5 stages, increasing speed.
MINIGAME_TEMPER = "temper"


MINIGAME_REGISTRY = {
    MINIGAME_NONE: None,
    MINIGAME_TENDING: "tending",
    MINIGAME_FORGE: "forge",
    MINIGAME_QUENCH: "quench",
    MINIGAME_BELLOWS: "bellows",
    MINIGAME_TEMPER: "temper",
}


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
        "tier": "iron",
    },
    {
        "input_item_id": "iron_ore",
        "input_item_amount": 1,
        "input_fuel_id": "coal",
        "input_fuel_amount": 2,
        "primary_output_id": "iron_ingot",
        "primary_output_amount": 1,
        "duration": 24.0,
        "heat_color": (220, 100, 40),
        "tier": "iron",
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
        "tier": "steel",
        "minigame_chain": ["forge", "quench"],
    },
    {
        "input_item_id": "iron_ingot",
        "input_item_amount": 1,
        "input_fuel_id": "coke",
        "input_fuel_amount": 2,
        "primary_output_id": "steel_ingot",
        "primary_output_amount": 1,
        "duration": 35.0,
        "heat_color": (255, 220, 150),
        "tier": "steel",
        "minigame_chain": ["bellows", "temper"],
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


def get_recipe_minigame_id(recipe):
    """Return the minigame id (one of :data:`MINIGAME_REGISTRY`) for
    ``recipe`` or :data:`MINIGAME_NONE` if the recipe doesn't trigger
    a minigame.
    """
    if not recipe:
        return MINIGAME_NONE
    return recipe.get("minigame", MINIGAME_NONE) or MINIGAME_NONE


def get_recipe_minigame_chain(recipe):
    """Return the minigame chain list for ``recipe`` or an empty list
    if the recipe doesn't have a multi-stage challenge.

    A chain is a list of minigame IDs that play in sequence.
    Each step must be completed before the next begins; the final
    bonus and XP multiplier are aggregated across all steps.
    """
    if not recipe:
        return []
    return recipe.get("minigame_chain", []) or []


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
        # Repairs are quick by design; speed unchanged from the
        # previous build.
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
