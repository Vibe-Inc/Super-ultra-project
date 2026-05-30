import pygame
from src.core.logger import logger

class CollisionSystem:
    """
    Collision helper for movement resolution and interaction checks.

    Attributes:
        None.

    Methods:
        rect_of(entity):
            Return the collision rectangle for an entity.
        handle_movement_and_collision(entity, dt, obstacles):
            Move an entity and resolve wall collisions.
        _resolve_static_collision(entity, obstacles):
            Push an entity out of any remaining overlaps.
        check_interactions(player, enemies, items):
            Process player collisions with enemies and loose items.
    """
    def rect_of(self, entity: object) -> pygame.Rect:
        if hasattr(entity, "get_rect"):
            return entity.get_rect()
        raise AttributeError("Entity must have get_rect()")

    def handle_movement_and_collision(self, entity: object, dt: float, obstacles: list[pygame.Rect]):
        movement = entity.velocity * entity.speed * dt

        # Move on X and check collisions; minimize repeated rect lookups
        if movement.x != 0:
            entity.pos.x += movement.x
            rect = self.rect_of(entity)
            offset_x = rect.x - entity.pos.x

            for wall in obstacles:
                if rect.colliderect(wall):
                    if movement.x > 0:
                        entity.pos.x = (wall.left - rect.width) - offset_x
                    else:
                        entity.pos.x = wall.right - offset_x
                    logger.debug(f"Resolved X collision for {getattr(entity, 'id', type(entity))} against wall {wall}")
                    # update rect after resolving and stop checking other walls
                    rect = self.rect_of(entity)
                    break

        # Move on Y and check collisions; minimize repeated rect lookups
        if movement.y != 0:
            entity.pos.y += movement.y
            rect = self.rect_of(entity)
            offset_y = rect.y - entity.pos.y

            for wall in obstacles:
                if rect.colliderect(wall):
                    if movement.y > 0:
                        entity.pos.y = (wall.top - rect.height) - offset_y
                    else:
                        entity.pos.y = wall.bottom - offset_y
                    logger.debug(f"Resolved Y collision for {getattr(entity, 'id', type(entity))} against wall {wall}")
                    rect = self.rect_of(entity)
                    break

        # Final pass to resolve any remaining static overlaps
        self._resolve_static_collision(entity, obstacles)

    def _resolve_static_collision(self, entity: object, obstacles: list[pygame.Rect]):
        rect = self.rect_of(entity)

        for wall in obstacles:
            if rect.colliderect(wall):
                overlap_left = rect.right - wall.left
                overlap_right = wall.right - rect.left
                overlap_top = rect.bottom - wall.top
                overlap_bottom = wall.bottom - rect.top

                min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

                if min_overlap == overlap_left:
                    entity.pos.x -= overlap_left
                elif min_overlap == overlap_right:
                    entity.pos.x += overlap_right
                elif min_overlap == overlap_top:
                    entity.pos.y -= overlap_top
                elif min_overlap == overlap_bottom:
                    entity.pos.y += overlap_bottom

                logger.debug(f"Resolved static overlap for {getattr(entity, 'id', type(entity))}; applied correction {min_overlap}")
                # Update rect after resolving and stop further checks
                rect = self.rect_of(entity)
                break

    def check_interactions(self, player: object, enemies: list, items: list):
        player_rect = self.rect_of(player)

        # Iterate over a shallow copy since we may remove items
        for item in items[:]:
            item_rect = self.rect_of(item)
            if player_rect.colliderect(item_rect):
                if hasattr(item, "on_pickup"):
                    logger.info(f"Player picked up item {getattr(item, 'id', type(item))}")
                    item.on_pickup(player)
                    items.remove(item)

        for enemy in enemies:
            enemy_rect = self.rect_of(enemy)
            if player_rect.colliderect(enemy_rect):
                if getattr(enemy, "contact_damage", True) and hasattr(enemy, "damage") and hasattr(player, "take_damage"):
                    logger.info(f"Player collided with enemy {getattr(enemy, 'id', type(enemy))}; applying {enemy.damage} damage")
                    player.take_damage(enemy.damage)

                if hasattr(player, "on_collision"):
                    player.on_collision(enemy)
                if hasattr(enemy, "on_collision"):
                    logger.debug(f"Enemy {getattr(enemy, 'id', type(enemy))} on_collision with player")
                    enemy.on_collision(player)