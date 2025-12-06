import pygame

class CollisionSystem:
    def rect_of(self, entity: object) -> pygame.Rect:
        if hasattr(entity, "get_rect"):
            return entity.get_rect()
        raise AttributeError("Entity must have get_rect()")

    def handle_movement_and_collision(self, entity: object, dt: float, obstacles: list[pygame.Rect]):
        movement = entity.velocity * entity.speed * dt
        
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
                    rect = self.rect_of(entity)

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
                    rect = self.rect_of(entity)

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
                
                break 

    def check_interactions(self, player: object, enemies: list, items: list):
        for item in items[:]:
            if self.rect_of(player).colliderect(self.rect_of(item)):
                if hasattr(item, "on_pickup"):
                    item.on_pickup(player)
                    items.remove(item)

        for enemy in enemies:
            if self.rect_of(player).colliderect(self.rect_of(enemy)):
                if hasattr(enemy, "damage") and hasattr(player, "take_damage"):
                    player.take_damage(enemy.damage)
                
                if hasattr(player, "on_collision"):
                    player.on_collision(enemy)
                if hasattr(enemy, "on_collision"):
                    enemy.on_collision(player)