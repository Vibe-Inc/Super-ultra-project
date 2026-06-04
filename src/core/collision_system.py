import pygame

from src.core.logger import logger


class CollisionSystem:
    """
    Collision helper for movement resolution and interaction checks.

    Attributes:
        _obstacle_cache_key (int | None):
            Cache key for the obstacle spatial index.
        _obstacle_spatial_index (dict):
            Spatial hash mapping cell coordinates to obstacle rects.
        _obstacle_cell_size (int):
            Cell size in pixels used for spatial indexing.

    Methods:
        rect_of(entity):
            Return the collision rectangle for an entity.
        handle_movement_and_collision(entity, dt, obstacles):
            Move an entity and resolve wall collisions.
        _build_obstacle_index(obstacles):
            Build the spatial index from a list of obstacle rects.
        _get_nearby_obstacles(rect, obstacles):
            Get obstacles near a given rect using the spatial index.
        _resolve_static_collision(entity, obstacles):
            Push an entity out of any remaining overlaps.
        check_interactions(player, enemies, items):
            Process player collisions with enemies and loose items.
    """

    def __init__(self):
        self._obstacle_cache_key = None
        self._obstacle_spatial_index: dict[tuple[int, int], list[pygame.Rect]] = {}
        self._obstacle_cell_size = 192

    def rect_of(self, entity: object) -> pygame.Rect:
        if hasattr(entity, "get_rect"):
            return entity.get_rect()
        raise AttributeError("Entity must have get_rect()")

    def _build_obstacle_index(self, obstacles: list[pygame.Rect]):
        self._obstacle_spatial_index = {}
        for obstacle in obstacles:
            min_cell_x = obstacle.left // self._obstacle_cell_size
            max_cell_x = obstacle.right // self._obstacle_cell_size
            min_cell_y = obstacle.top // self._obstacle_cell_size
            max_cell_y = obstacle.bottom // self._obstacle_cell_size

            for cell_x in range(min_cell_x, max_cell_x + 1):
                for cell_y in range(min_cell_y, max_cell_y + 1):
                    self._obstacle_spatial_index.setdefault((cell_x, cell_y), []).append(obstacle)

    def _get_nearby_obstacles(self, rect: pygame.Rect, obstacles: list[pygame.Rect]) -> list[pygame.Rect]:
        cache_key = id(obstacles)
        if cache_key != self._obstacle_cache_key:
            self._obstacle_cache_key = cache_key
            self._build_obstacle_index(obstacles)

        min_cell_x = rect.left // self._obstacle_cell_size
        max_cell_x = rect.right // self._obstacle_cell_size
        min_cell_y = rect.top // self._obstacle_cell_size
        max_cell_y = rect.bottom // self._obstacle_cell_size

        nearby: list[pygame.Rect] = []
        seen: set[int] = set()

        for cell_x in range(min_cell_x, max_cell_x + 1):
            for cell_y in range(min_cell_y, max_cell_y + 1):
                for obstacle in self._obstacle_spatial_index.get((cell_x, cell_y), []):
                    obstacle_id = id(obstacle)
                    if obstacle_id not in seen:
                        seen.add(obstacle_id)
                        nearby.append(obstacle)

        return nearby

    def handle_movement_and_collision(self, entity: object, dt: float, obstacles: list[pygame.Rect]):
        movement = entity.velocity * entity.speed * dt

        if movement.x != 0:
            entity.pos.x += movement.x
            rect = self.rect_of(entity)
            offset_x = rect.x - entity.pos.x
            query_rect = rect.inflate(abs(movement.x), 0)
            nearby_obstacles = self._get_nearby_obstacles(query_rect, obstacles)

            for wall in nearby_obstacles:
                if rect.colliderect(wall):
                    if movement.x > 0:
                        entity.pos.x = (wall.left - rect.width) - offset_x
                    else:
                        entity.pos.x = wall.right - offset_x
                    logger.debug(f"Resolved X collision for {getattr(entity, 'id', type(entity))} against wall {wall}")
                    rect = self.rect_of(entity)
                    break

        if movement.y != 0:
            entity.pos.y += movement.y
            rect = self.rect_of(entity)
            offset_y = rect.y - entity.pos.y
            query_rect = rect.inflate(0, abs(movement.y))
            nearby_obstacles = self._get_nearby_obstacles(query_rect, obstacles)

            for wall in nearby_obstacles:
                if rect.colliderect(wall):
                    if movement.y > 0:
                        entity.pos.y = (wall.top - rect.height) - offset_y
                    else:
                        entity.pos.y = wall.bottom - offset_y
                    logger.debug(f"Resolved Y collision for {getattr(entity, 'id', type(entity))} against wall {wall}")
                    rect = self.rect_of(entity)
                    break

        self._resolve_static_collision(entity, obstacles)

    def _resolve_static_collision(self, entity: object, obstacles: list[pygame.Rect]):
        rect = self.rect_of(entity)
        nearby_obstacles = self._get_nearby_obstacles(rect, obstacles)

        for wall in nearby_obstacles:
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
                rect = self.rect_of(entity)
                break

    def check_interactions(self, player: object, enemies: list, items: list):
        player_rect = self.rect_of(player)

        for item in items[:]:
            item_rect = self.rect_of(item)
            if player_rect.colliderect(item_rect):
                if hasattr(item, "on_pickup"):
                    logger.info(f"Player attempted to pick up item {getattr(item, 'id', type(item))}")
                    picked_up = item.on_pickup(player)
                    if picked_up is not False:
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