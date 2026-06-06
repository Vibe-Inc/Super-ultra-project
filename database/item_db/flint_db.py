"""
Flint-based item seed data for the smeltery workbench.

Adds three Minecraft-style items that are missing from the base game:

* ``sharpen_stone``  -- a small whetstone, wielded like a dagger.
* ``flint_axe``      -- a tier-1 axe (flint head, stick handle).
* ``flint_pickaxe``  -- a tier-1 pickaxe (flint head, stick handle).

If any of the expected PNG files are missing, ``_ensure_placeholder_image``
writes a small labeled square so ``create_item`` can load the asset without
raising ``FileNotFoundError``.
"""

import os
import sys
import pygame

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


def _ensure_placeholder_image(image_path, base_color, label, size=32):
    """
    Make sure ``image_path`` exists on disk. If not, write a small labeled
    PNG so ``create_item`` does not crash on a missing asset. The
    placeholder is a solid colour with a thin dark border, a subtle
    highlight on the top edge, and a single-letter label in the centre
    so the new items remain visually distinguishable in the workbench.
    """
    if not pygame.get_init():
        pygame.init()

    abs_path = os.path.join(PROJECT_ROOT, image_path) if not os.path.isabs(image_path) else image_path
    if os.path.exists(abs_path):
        return

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    surf.fill(base_color)
    pygame.draw.rect(surf, (0, 0, 0, 230), surf.get_rect(), width=2)
    pygame.draw.line(
        surf,
        (min(base_color[0] + 60, 255), min(base_color[1] + 60, 255), min(base_color[2] + 60, 255), 200),
        (2, 2),
        (size - 3, 2),
        1,
    )
    pygame.draw.line(
        surf,
        (max(base_color[0] - 60, 0), max(base_color[1] - 60, 0), max(base_color[2] - 60, 0), 200),
        (2, size - 3),
        (size - 3, size - 3),
        1,
    )
    if label:
        try:
            font = pygame.font.SysFont("arial", max(10, size // 2), bold=True)
            text = font.render(label, True, (0, 0, 0, 235))
            text_rect = text.get_rect(center=(size // 2, size // 2))
            surf.blit(text, text_rect)
        except Exception:
            pass
    try:
        pygame.image.save(surf, abs_path)
    except Exception:
        pass


def seed_flint_items(db):
    """
    Seed the three flint-based items into the database.

    The same PNG placeholder routine that ``smeltery_db.seed_smeltery``
    uses is reused here so the new tools/weapons load even when no
    pre-existing art has been added.
    """
    # ----- flint_axe (tool) -----
    axe_path = "assets/items/tools/flint_axe.png"
    _ensure_placeholder_image(axe_path, (75, 75, 80), "A")
    db.add_tool(
        item_id="flint_axe",
        name="Flint Axe",
        image_path=axe_path,
        tool_type="axe",
        durability=45,
        power=2,
        price=55,
        max_stack=1,
        description="An axe with a chipped flint head lashed to a stick. Better than wood, weaker than stone.",
        gather_type="wood",
        gather_yield_min=1,
        gather_yield_max=2,
    )

    # ----- flint_pickaxe (tool) -----
    pick_path = "assets/items/tools/flint_pickaxe.png"
    _ensure_placeholder_image(pick_path, (75, 75, 80), "P")
    db.add_tool(
        item_id="flint_pickaxe",
        name="Flint Pickaxe",
        image_path=pick_path,
        tool_type="pickaxe",
        durability=45,
        power=2,
        price=55,
        max_stack=1,
        description="A pickaxe tipped with sharp flint. Mines stone and ore faster than a wooden one.",
        gather_type="stone",
        gather_yield_min=1,
        gather_yield_max=2,
    )

    # ----- sharpen_stone (weapon) -----
    stone_path = "assets/items/weapons/sharpen_stone.png"
    _ensure_placeholder_image(stone_path, (130, 130, 135), "W")
    db.add_weapon(
        item_id="sharpen_stone",
        name="Sharpen Stone",
        image_path=stone_path,
        weapon_class="melee",
        damage=10,
        durability=40,
        range_val=50,
        cone_degrees=80.0,
        cooldown=280,
        price=25,
        description="A flat whetstone of fine-grained flint. Crude but razor-sharp - quick, light jabs.",
        combat_style="dagger",
    )


if __name__ == "__main__":
    from database.GP_database import Gp_database
    db = Gp_database()
    seed_flint_items(db)
    db.close()
