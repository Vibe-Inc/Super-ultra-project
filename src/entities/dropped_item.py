import pygame
from src.core.logger import logger


class DroppedItem:
    """
    Represents an item lying on the ground in the world.

    Wraps an :class:`Item` together with its world position and a cached
    on-ground image. The visible icon and the physical hitbox are always
    kept in sync with :pyattr:`pos` so the player can pick the item up
    by walking onto it.

    Attributes:
        ON_GROUND_SIZE (int):
            Pixel size used when drawing the on-ground icon (square).
        pos (pygame.Vector2):
            World-space center of the dropped item.
        item (Item):
            The item instance this drop represents.
        count (int):
            Stack size of the item in this drop.
        image (pygame.Surface):
            Cached, resized icon used for rendering.
        rect (pygame.Rect):
            World-space bounding rect used for drawing and collisions.

    Methods:
        __init__(x, y, item, count):
            Create a drop at the given world position.
        update(dt, obstacles):
            Sync the bounding rect to the current world position.
        get_rect():
            Return a rect centered on :pyattr:`pos` for collision checks.
        draw(screen, camera_offset=None):
            Blit the on-ground icon at the rect, applying the camera offset.
        on_pickup(player):
            Try to add this drop's item/count to the player's inventory.
    """

    ON_GROUND_SIZE = 48

    def __init__(self, x, y, item, count):
        self.pos = pygame.Vector2(x, y)
        self.item = item
        self.count = count
        self.image = item.resize(self.ON_GROUND_SIZE)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, dt, obstacles):
        self.rect.center = (self.pos.x, self.pos.y)

    def get_rect(self):
        self.rect.center = (self.pos.x, self.pos.y)
        return self.rect

    def draw(self, screen, camera_offset=None):
        self.rect.center = (self.pos.x, self.pos.y)
        draw_rect = self.rect.copy()
        if camera_offset:
            draw_rect.x -= int(camera_offset.x)
            draw_rect.y -= int(camera_offset.y)
        screen.blit(self.image, draw_rect)

    def on_pickup(self, player):
        game_state = getattr(player, 'game_state', None)
        if game_state:
            from src.inventory.system import CraftingLogic
            added = CraftingLogic.add_crafted_item(game_state.MAIN_player_inv, self.item, self.count)
            if not added:
                logger.info("Inventory full, could not pick up item")
                return False
            return True
        return False
