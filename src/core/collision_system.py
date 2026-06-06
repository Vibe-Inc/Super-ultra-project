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
        resolve_static_collision(entity, obstacles):
            Push an entity out of all overlapping walls iteratively.
        check_interactions(player, enemies, items):
            Process player collisions with enemies and loose items.
    """

    def __init__(self):
        self._obstacle_cache_key = None
        self._obstacle_spatial_index: dict[tuple[int, int], list[pygame.Rect]] = {}
        self._obstacle_cell_size = 192

    def rect_of(self, entity: object) -> pygame.Rect:
        """Return the collision rectangle for an entity.

        Args:
            entity (object): An object that provides a ``get_rect()`` method.

        Returns:
            pygame.Rect: The collision rectangle of the entity.

        Raises:
            AttributeError: If the entity does not have a ``get_rect()`` method.
        """
        if hasattr(entity, "get_rect"):
            return entity.get_rect()
        raise AttributeError("Entity must have get_rect()")

    def _build_obstacle_index(self, obstacles: list[pygame.Rect]):
        """Build the spatial index from a list of obstacle rects.

        Populates a dictionary mapping cell coordinates to the obstacle
        rectangles that overlap those cells.

        Args:
            obstacles (list[pygame.Rect]): List of wall/obstacle rectangles.
        """
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
        """Get obstacles near a given rect using the spatial index.

        Rebuilds the spatial index if the obstacle list reference has changed.

        Args:
            rect (pygame.Rect): The query rectangle.
            obstacles (list[pygame.Rect]): The full list of obstacles.

        Returns:
            list[pygame.Rect]: Obstacles whose cells overlap the query rectangle.
        """
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
        """Move an entity and resolve wall collisions.

        Separates X and Y movement so the entity can slide along walls
        when only one axis is blocked.

        Args:
            entity (object): The moving entity (must have ``pos``, ``velocity``, ``speed``, ``get_rect()``).
            dt (float): Delta time in seconds.
            obstacles (list[pygame.Rect]): List of wall rectangles.
        """
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

        self.resolve_static_collision(entity, obstacles)

    def resolve_teleport_collision(self, entity: object, obstacles: list[pygame.Rect], direction: pygame.Vector2):
        """Push an entity out of overlapping walls after a teleport.

        Moves the entity iteratively in the given direction until it no
        longer overlaps any obstacle, up to 500 steps.

        Args:
            entity (object): The teleported entity.
            obstacles (list[pygame.Rect]): List of wall rectangles.
            direction (pygame.Vector2): Direction to push the entity.
        """
        rect = self.rect_of(entity)
        nearby = self._get_nearby_obstacles(rect, obstacles)

        if not any(rect.colliderect(w) for w in nearby):
            return

        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        direction = direction.normalize()

        for _ in range(500):
            entity.pos += direction
            rect = self.rect_of(entity)
            nearby = self._get_nearby_obstacles(rect, obstacles)
            if not any(rect.colliderect(w) for w in nearby):
                break

    def resolve_static_collision(self, entity: object, obstacles: list[pygame.Rect]):
        """Push an entity out of all overlapping walls iteratively.

        Uses up to 10 iterations to resolve overlaps by finding the
        smallest overlap axis on each pass.

        Args:
            entity (object): The entity to resolve.
            obstacles (list[pygame.Rect]): List of wall rectangles.
        """
        rect = self.rect_of(entity)
        nearby_obstacles = self._get_nearby_obstacles(rect, obstacles)

        for _ in range(10):
            resolved_any = False
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
                    nearby_obstacles = self._get_nearby_obstacles(rect, obstacles)
                    resolved_any = True
                    break
            if not resolved_any:
                break

    def check_interactions(self, player: object, enemies: list, items: list):
        """Process player collisions with enemies and loose items.

        Handles item pickup (calling ``on_pickup``) and contact damage
        from enemies (calling ``take_damage`` on the player).

        Args:
            player (object): The player character.
            enemies (list): List of enemy entities.
            items (list): List of dropped items (modified in-place).
        """
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