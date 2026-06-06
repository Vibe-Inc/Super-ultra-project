import os
import sys
import pygame

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


def _ensure_placeholder_image(image_path, color, size=32):
    """
    Make sure ``image_path`` exists on disk. If not, create a small
    square placeholder PNG so the item factory does not crash on a
    missing asset. The placeholder is a solid colour with a thin
    dark border so it remains visible against any slot background.
    """
    if not pygame.get_init():
        pygame.init()

    abs_path = os.path.join(PROJECT_ROOT, image_path) if not os.path.isabs(image_path) else image_path
    if os.path.exists(abs_path):
        return

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    surf.fill(color)
    pygame.draw.rect(surf, (0, 0, 0, 220), surf.get_rect(), width=2)
    pygame.draw.line(
        surf,
        (min(color[0] + 60, 255), min(color[1] + 60, 255), min(color[2] + 60, 255), 200),
        (2, 2),
        (size - 3, 2),
        1,
    )
    pygame.draw.line(
        surf,
        (max(color[0] - 60, 0), max(color[1] - 60, 0), max(color[2] - 60, 0), 200),
        (2, size - 3),
        (size - 3, size - 3),
        1,
    )
    try:
        pygame.image.save(surf, abs_path)
    except Exception:
        pass


def seed_smeltery(db):
    """
    Seed the items used by the smeltery workstations (coke oven, blast
    furnace, workbench). Generates a placeholder PNG for any item that
    does not have a pre-existing asset so ``create_item`` can load it.
    """
    items = [
        ("coal",          (40, 40, 45),    "A chunk of coal, made by slowly baking wood. Burns hot and long."),
        ("coke",          (22, 22, 28),    "Coke, refined from coal. Burns even hotter."),
        ("iron_ingot",    (192, 200, 210), "A pure iron ingot, ready for smithing."),
        ("steel_ingot",   (210, 215, 220), "A steel ingot, stronger than iron."),
    ]

    for item_id, color, description in items:
        image_path = f"assets/items/resources/{item_id}.png"
        _ensure_placeholder_image(image_path, color)
        db.add_generic_item(
            item_id=item_id,
            item_type="resource",
            name=item_id.replace("_", " ").title(),
            image_path=image_path,
            price=5,
            max_stack=64,
            description=description,
        )


if __name__ == "__main__":
    from database.GP_database import Gp_database
    db = Gp_database()
    seed_smeltery(db)
    db.close()
