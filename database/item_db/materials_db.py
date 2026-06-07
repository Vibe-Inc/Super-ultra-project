import os
import sys
import pygame

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


def _ensure_placeholder_image(image_path, base_color, label, size=32):
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


def seed_materials(db):
    _ensure_placeholder_image("assets/items/resources/fiber.png", (180, 160, 120), "F")
    db.add_generic_item(
        item_id="fiber",
        item_type="resource",
        name="Fiber",
        image_path="assets/items/resources/fiber.png",
        price=1,
        max_stack=64,
        description="Plant fibers gathered from fibrous undergrowth. Can be twisted into string."
    )

    _ensure_placeholder_image("assets/items/resources/leather.png", (140, 90, 50), "L")
    db.add_generic_item(
        item_id="leather",
        item_type="resource",
        name="Leather",
        image_path="assets/items/resources/leather.png",
        price=7,
        max_stack=64,
        description="Cured animal hide. Used for crafting light armor and accessories."
    )

    _ensure_placeholder_image("assets/items/resources/string.png", (210, 200, 180), "S")
    db.add_generic_item(
        item_id="string",
        item_type="resource",
        name="String",
        image_path="assets/items/resources/string.png",
        price=2,
        max_stack=64,
        description="A strong, twisted thread. Useful for bows and bindings."
    )

    _ensure_placeholder_image("assets/items/resources/silver_ore.png", (180, 185, 200), "SO")
    db.add_generic_item(
        item_id="silver_ore",
        item_type="resource",
        name="Silver Ore",
        image_path="assets/items/resources/silver_ore.png",
        price=12,
        max_stack=64,
        description="Raw silver ore, gleaming with a dull white sheen. Smelt it into ingots."
    )

    _ensure_placeholder_image("assets/items/resources/silver_ingot.png", (210, 215, 230), "SI")
    db.add_generic_item(
        item_id="silver_ingot",
        item_type="resource",
        name="Silver Ingot",
        image_path="assets/items/resources/silver_ingot.png",
        price=10,
        max_stack=64,
        description="A pure silver ingot, cool and bright. Used for enchanted accessories."
    )

    _ensure_placeholder_image("assets/items/lantern.png", (200, 160, 40), "LN")
    db.add_generic_item(
        item_id="lantern",
        item_type="misc",
        name="Lantern",
        image_path="assets/items/lantern.png",
        price=25,
        max_stack=1,
        description="A compact lantern that casts a warm glow around you when carried."
    )

    _ensure_placeholder_image("assets/items/accessories/Light_ring.png", (220, 220, 100), "LR")
    db.add_generic_item(
        item_id="light_ring",
        item_type="armor",
        name="Light Ring",
        image_path="assets/items/accessories/Light_ring.png",
        price=120,
        max_stack=1,
        description="An enchanted ring that emits a soft glow and amplifies any light source you carry."
    )

    _ensure_placeholder_image("assets/items/accessories/Gay_ring.png", (255, 100, 200), "GR")
    db.add_generic_item(
        item_id="gay_ring",
        item_type="armor",
        name="Gay Ring",
        image_path="assets/items/accessories/Gay_ring.png",
        price=67,
        max_stack=1,
        description="A fabulous rainbow ring! Creates a gloving rainbow aura around you when equipped."
    )

    _ensure_placeholder_image("assets/items/resources/fire_rune.png", (220, 50, 50), "FR")
    db.add_generic_item(
        item_id="fire_rune",
        item_type="resource",
        name="Fire Rune",
        image_path="assets/items/resources/fire_rune.png",
        price=150,
        max_stack=10,
        description="A glowing rune radiating intense heat. Can be socketed into a weapon by an Enchanter."
    )

    _ensure_placeholder_image("assets/items/resources/ice_rune.png", (50, 150, 220), "IR")
    db.add_generic_item(
        item_id="ice_rune",
        item_type="resource",
        name="Ice Rune",
        image_path="assets/items/resources/ice_rune.png",
        price=150,
        max_stack=10,
        description="A cold, crystalline rune. Can be socketed into a weapon by an Enchanter."
    )


if __name__ == "__main__":
    from database.GP_database import Gp_database
    db = Gp_database()
    seed_materials(db)
    db.close()
