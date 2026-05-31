import pytmx
import pygame
from src.core.logger import logger

class Map:
    FRINGE_LAYER_NAME = "details fringe layer"
    FRINGE_LAYER_FADE_ALPHA = 110

    """
    Represents a tile-based game map loaded from a Tiled map file.

    This class handles loading and drawing of the map using pytmx and pygame.

    Attributes:
        map_file (str):
            Path to the Tiled map (.tmx) file.
        game_map (pytmx.TiledMap | None):
            The loaded Tiled map object.
        pixel_width (int):
            Width of the map in pixels.
        pixel_height (int):
            Height of the map in pixels.

    Methods:
        __init__(map_file):
            Initialize the map with the given file path.
        draw(screen):
            Draw the map layers onto the given Pygame surface.
            Args:
                screen (pygame.Surface): The surface to draw the map on.
    """

    def __init__(self, map_file: str):
        self.map_file = map_file
        self.game_map = None
        self.pixel_width = 0
        self.pixel_height = 0
        self._base_render_cache = None
        self._fringe_components = []

    def ensure_loaded(self) -> bool:
        if self.game_map is None:
            try:
                logger.info(f"Loading map: {self.map_file}")
                self.game_map = pytmx.load_pygame(self.map_file)
                self.pixel_width = self.game_map.width * self.game_map.tilewidth
                self.pixel_height = self.game_map.height * self.game_map.tileheight
                self._build_render_cache()
                logger.info(f"Map loaded successfully: {self.map_file} ({self.pixel_width}x{self.pixel_height})")
            except Exception as e:
                logger.error(f"Failed to load map {self.map_file}: {e}")
                self.game_map = None
                return False
        return True

    def _is_fringe_layer(self, layer) -> bool:
        return isinstance(layer, pytmx.TiledTileLayer) and layer.name.strip().lower() == self.FRINGE_LAYER_NAME

    def _build_fringe_components(self, layer):
        tile_width = self.game_map.tilewidth
        tile_height = self.game_map.tileheight

        occupied_tiles = {}
        for x, y, gid in layer:
            if gid:
                occupied_tiles[(x, y)] = gid

        components = []
        visited = set()

        for start_cell in occupied_tiles:
            if start_cell in visited:
                continue

            stack = [start_cell]
            visited.add(start_cell)
            cells = []

            while stack:
                cell_x, cell_y = stack.pop()
                cells.append((cell_x, cell_y))

                for neighbor in ((cell_x - 1, cell_y), (cell_x + 1, cell_y), (cell_x, cell_y - 1), (cell_x, cell_y + 1)):
                    if neighbor in occupied_tiles and neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)

            min_x = min(x for x, _ in cells)
            max_x = max(x for x, _ in cells)
            min_y = min(y for _, y in cells)
            max_y = max(y for _, y in cells)

            surface_width = (max_x - min_x + 1) * tile_width
            surface_height = (max_y - min_y + 1) * tile_height
            surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)

            tile_rects = []
            for cell_x, cell_y in cells:
                gid = occupied_tiles[(cell_x, cell_y)]
                tile = self.game_map.get_tile_image_by_gid(gid)
                if tile:
                    surface.blit(
                        tile,
                        ((cell_x - min_x) * tile_width, (cell_y - min_y) * tile_height),
                    )
                tile_rects.append(
                    pygame.Rect(
                        cell_x * tile_width,
                        cell_y * tile_height,
                        tile_width,
                        tile_height,
                    )
                )

            components.append(
                {
                    "surface": surface,
                    "origin": pygame.Vector2(min_x * tile_width, min_y * tile_height),
                    "tile_rects": tile_rects,
                }
            )

        return components

    def _build_render_cache(self):
        if self.game_map is None:
            self._base_render_cache = None
            self._fringe_components = []
            return

        surface = pygame.Surface((self.pixel_width, self.pixel_height), pygame.SRCALPHA)
        fringe_components = []
        for layer in self.game_map.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                if self._is_fringe_layer(layer):
                    fringe_components.extend(self._build_fringe_components(layer))
                    continue
                for x, y, gid in layer:
                    tile = self.game_map.get_tile_image_by_gid(gid)
                    if tile:
                        surface.blit(tile, (x * self.game_map.tilewidth, y * self.game_map.tileheight))
        self._base_render_cache = surface
        self._fringe_components = fringe_components

    def get_tmx_data(self):
        if self.ensure_loaded():
            return self.game_map
        return None

    def draw(self, screen, camera_offset=None):
        if not self.ensure_loaded():
            return

        if self._base_render_cache is None:
            self._build_render_cache()
        if self._base_render_cache is not None:
            if camera_offset is None:
                screen.blit(self._base_render_cache, (0, 0))
            else:
                screen.blit(self._base_render_cache, (-int(camera_offset.x), -int(camera_offset.y)))

    def draw_fringe_overlay(self, screen, camera_offset=None, player=None):
        if not self.ensure_loaded():
            return

        if self._base_render_cache is None:
            self._build_render_cache()

        if not self._fringe_components:
            return

        player_rect = None
        if player is not None:
            player_rect = pygame.Rect(int(player.pos.x), int(player.pos.y), player.image.get_width(), player.image.get_height())

        for component in self._fringe_components:
            surface = component["surface"]
            alpha = 255
            if player_rect is not None and self._should_fade_component(player_rect, component["tile_rects"]):
                alpha = self.FRINGE_LAYER_FADE_ALPHA

            surface.set_alpha(alpha)
            origin_x = int(component["origin"].x)
            origin_y = int(component["origin"].y)
            if camera_offset is None:
                screen.blit(surface, (origin_x, origin_y))
            else:
                screen.blit(
                    surface,
                    (
                        origin_x - int(camera_offset.x),
                        origin_y - int(camera_offset.y),
                    ),
                )
            surface.set_alpha(None)

    def _should_fade_component(self, player_rect: pygame.Rect, tile_rects: list[pygame.Rect]) -> bool:
        if not tile_rects:
            return False

        tile_area = tile_rects[0].width * tile_rects[0].height
        if tile_area <= 0:
            return False

        fade_threshold = tile_area * 0.5
        for tile_rect in tile_rects:
            overlap_rect = player_rect.clip(tile_rect)
            if overlap_rect.width > 0 and overlap_rect.height > 0:
                if overlap_rect.width * overlap_rect.height > fade_threshold:
                    return True
        return False

    def get_obstacles(self):
        if not self.ensure_loaded():
            return []

        obstacles = []
        if self.game_map:
            for obj in self.game_map.objects:
                if obj.type == "Wall" or obj.name == "Wall": # Check for object type or name
                    obstacles.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

            seen_tile_cells = set()

            for layer in self.game_map.layers:
                if not isinstance(layer, pytmx.TiledTileLayer):
                    continue

                if self._is_fringe_layer(layer):
                    continue

                for x, y, gid in layer:
                    if not gid:
                        continue

                    tile_properties = self.game_map.get_tile_properties_by_gid(gid)
                    if not tile_properties:
                        continue

                    if not tile_properties.get("collidable"):
                        continue

                    tile_key = (x, y, layer.id)
                    if tile_key in seen_tile_cells:
                        continue
                    seen_tile_cells.add(tile_key)

                    obstacles.append(
                        pygame.Rect(
                            x * self.game_map.tilewidth,
                            y * self.game_map.tileheight,
                            self.game_map.tilewidth,
                            self.game_map.tileheight,
                        )
                    )
            
            # Also check for object layers named "Walls" or "Collisions"
            for layer in self.game_map.visible_layers:
                if isinstance(layer, pytmx.TiledObjectGroup):
                    if "wall" in layer.name.lower() or "collision" in layer.name.lower():
                        for obj in layer:
                            obstacles.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
        return obstacles


class LocalMap:
    """
    Manages the current map and transitions between maps.

    This class tracks the active map, handles map switching logic, and manages player transitions between maps.

    Attributes:
        name (str):
            Name of the local map context.
        current_map (Map):
            The currently active Map object.
        current_map_path (str):
            Path to the currently active map file.
        transition_buffer (int):
            Distance from the map edge at which a transition is triggered.

    Methods:
        __init__(name, map_file):
            Initialize the local map manager with a name and starting map file.
        draw(screen):
            Draw the current map onto the given Pygame surface.
            Args:
                screen (pygame.Surface): The surface to draw the map on.
        update(player):
            Update map logic and handle transitions based on player position.
            Args:
                player: The player object (must have pos and image/rect attributes).
            Returns:
                str | None: Path to the new map if switched, else None.
        switch_map(new_map_path):
            Switch to a new map by file path.
            Args:
                new_map_path (str): Path to the new map file.
    """
    def __init__(self, name: str, map_file: str):
        self.name = name
        self.current_map = Map(map_file)
        self.current_map_path = map_file 

        self.transition_buffer = 150 
        # Define directional transitions for maps.
        # Each entry maps a direction ('left','right','up','down') to a dict with:
        #  - 'map': target map path
        #  - 'spawn': either {'type':'side','side':'left'|'right'|'top'|'bottom'} to place near that edge
        #             or {'type':'tile','x':tile_x,'y':tile_y} to teleport to a specific tile
        # This makes adding new directional transitions easy in future.
        self.map_transitions = {
            "maps/test-map-1.tmx": {
                "right": {"map": "maps/test-map-2.tmx", "spawn": {"type": "side", "side": "left"}},
            },
            "maps/test-map-2.tmx": {
                "left": {"map": "maps/test-map-1.tmx", "spawn": {"type": "side", "side": "right"}},
                "right": {"map": "maps/test-map-3.tmx", "spawn": {"type": "side", "side": "left"}},
            },
            "maps/test-map-3.tmx": {
                "left": {"map": "maps/test-map-2.tmx", "spawn": {"type": "side", "side": "right"}},
            },
        }

    def draw(self, screen, camera_offset=None):
        self.current_map.draw(screen, camera_offset)

    def draw_fringe_overlay(self, screen, camera_offset=None, player=None):
        self.current_map.draw_fringe_overlay(screen, camera_offset, player)

    def get_obstacles(self):
        return self.current_map.get_obstacles()

    def update(self, player):
        """
        Updates map logic and handles transitions based on player position.
        Returns: string (path to new map) if switch happened, else None.
        """
        if not self.current_map.ensure_loaded():
            return None

        tmx_data = self.current_map.game_map
        map_width = tmx_data.width * tmx_data.tilewidth
        tile_width = tmx_data.tilewidth
        tile_height = tmx_data.tileheight

        if hasattr(player, 'rect'):
            w = player.rect.width
        else:
            w = player.image.get_width()
        x = player.pos.x
        player_rect = player.get_rect() if hasattr(player, "get_rect") else player.rect

        # Prevent player from leaving map bounds: clamp position to map pixel dimensions
        sprite_w = player.image.get_width()
        sprite_h = player.image.get_height()
        max_x = max(0, map_width - sprite_w)
        max_y = max(0, tmx_data.height * tile_height - sprite_h)
        if player.pos.x < 0:
            player.pos.x = 0
        elif player.pos.x > max_x:
            player.pos.x = max_x
        if player.pos.y < 0:
            player.pos.y = 0
        elif player.pos.y > max_y:
            player.pos.y = max_y
        # refresh player rect after clamping
        player_rect = player.get_rect() if hasattr(player, "get_rect") else player.rect

        spawn_offset = self.transition_buffer + 30 
        new_map = None

        if self.current_map_path == "maps/test-map-1.tmx":
            if self._player_overlaps_any_tile(player_rect, tile_width, tile_height, [(36, 16), (37, 16)]):
                new_map = "maps/tavern.tmx"
                self.switch_map(new_map)
                self._teleport_player_to_tile(player, 14, 38, tile_width, tile_height)
                return new_map

        # Tavern exit handling: check first so tavern-specific teleports always take priority
        if self.current_map_path == "maps/tavern.tmx":
            tavern_exit_tiles = [(x, 39) for x in range(13, 17)]
            if self._player_overlaps_any_tile(player_rect, tile_width, tile_height, tavern_exit_tiles):
                new_map = "maps/test-map-1.tmx"
                self.switch_map(new_map)
                self._teleport_player_to_tile(player, 36, 17, tile_width, tile_height)
                return new_map

        # Directional edge checks (right/left/up/down)
        # Determine player's height for vertical checks
        if hasattr(player_rect, 'height'):
            h = player_rect.height
        else:
            h = player.image.get_height()

        direction = None
        if x + w >= map_width - self.transition_buffer:
            direction = "right"
        elif x <= self.transition_buffer:
            direction = "left"
        elif player.pos.y + h >= (tmx_data.height * tile_height) - self.transition_buffer:
            direction = "down"
        elif player.pos.y <= self.transition_buffer:
            direction = "up"

        if direction is not None:
            transitions = self.map_transitions.get(self.current_map_path, {})
            trans = transitions.get(direction)
            if trans:
                # remember previous position to pick nearest corner if needed
                old_x = player.pos.x
                old_y = player.pos.y

                new_map = trans["map"]
                self.switch_map(new_map)
                # handle spawn
                spawn = trans.get("spawn")
                if spawn:
                    # ensure new map data available
                    self.current_map.ensure_loaded()
                    new_map_tmx = self.current_map.game_map
                    new_map_width = new_map_tmx.width * new_map_tmx.tilewidth
                    new_map_height = new_map_tmx.height * new_map_tmx.tileheight

                    allowed_x_min = 0
                    allowed_x_max = max(0, new_map_width - w)
                    allowed_y_min = 0
                    allowed_y_max = max(0, new_map_height - h)

                    left_x = allowed_x_min + spawn_offset
                    right_x = allowed_x_max - spawn_offset
                    top_y = allowed_y_min + spawn_offset
                    bottom_y = allowed_y_max - spawn_offset

                    # helper to choose nearest corner to old position
                    def _nearest_corner():
                        candidates = [
                            (left_x, top_y),
                            (left_x, bottom_y),
                            (right_x, top_y),
                            (right_x, bottom_y),
                        ]
                        best = None
                        best_dist = None
                        for cx, cy in candidates:
                            # clamp candidates to allowed ranges
                            cx_clamped = max(allowed_x_min, min(cx, allowed_x_max))
                            cy_clamped = max(allowed_y_min, min(cy, allowed_y_max))
                            dx = cx_clamped - old_x
                            dy = cy_clamped - old_y
                            dist = dx * dx + dy * dy
                            if best is None or dist < best_dist:
                                best = (cx_clamped, cy_clamped)
                                best_dist = dist
                        return best

                    if spawn.get("type") == "side":
                        side = spawn.get("side")
                        if side == "left":
                            desired_x = left_x
                            # clamp desired_x to allowed range
                            if desired_x < allowed_x_min or desired_x > allowed_x_max:
                                px, py = _nearest_corner()
                                player.pos.x = px
                                player.pos.y = py
                            else:
                                player.pos.x = desired_x
                                # clamp y within allowed range
                                player.pos.y = max(allowed_y_min, min(player.pos.y, allowed_y_max))
                        elif side == "right":
                            desired_x = right_x
                            if desired_x < allowed_x_min or desired_x > allowed_x_max:
                                px, py = _nearest_corner()
                                player.pos.x = px
                                player.pos.y = py
                            else:
                                player.pos.x = desired_x
                                player.pos.y = max(allowed_y_min, min(player.pos.y, allowed_y_max))
                        elif side == "top":
                            desired_y = top_y
                            if desired_y < allowed_y_min or desired_y > allowed_y_max:
                                px, py = _nearest_corner()
                                player.pos.x = px
                                player.pos.y = py
                            else:
                                player.pos.y = desired_y
                                player.pos.x = max(allowed_x_min, min(player.pos.x, allowed_x_max))
                        elif side == "bottom":
                            desired_y = bottom_y
                            if desired_y < allowed_y_min or desired_y > allowed_y_max:
                                px, py = _nearest_corner()
                                player.pos.x = px
                                player.pos.y = py
                            else:
                                player.pos.y = desired_y
                                player.pos.x = max(allowed_x_min, min(player.pos.x, allowed_x_max))
                    elif spawn.get("type") == "tile":
                        sx = spawn.get("x")
                        sy = spawn.get("y")
                        # calculate target top-left based on tile and player offset
                        player_rect = player.get_rect() if hasattr(player, "get_rect") else player.rect
                        offset_x = player_rect.x - player.pos.x
                        offset_y = player_rect.y - player.pos.y
                        target_x = sx * tile_width - offset_x
                        target_y = sy * tile_height - offset_y
                        if target_x < allowed_x_min or target_x > allowed_x_max or target_y < allowed_y_min or target_y > allowed_y_max:
                            px, py = _nearest_corner()
                            player.pos.x = px
                            player.pos.y = py
                        else:
                            player.pos.x = target_x
                            player.pos.y = target_y

        

        return new_map

    def switch_map(self, new_map_path):
        logger.info(f"Switching map from {self.current_map_path} to {new_map_path}")
        self.current_map = Map(new_map_path)
        self.current_map_path = new_map_path

    def _player_overlaps_any_tile(self, player_rect, tile_width: int, tile_height: int, tile_positions: list[tuple[int, int]]) -> bool:
        for tile_x, tile_y in tile_positions:
            tile_rect = pygame.Rect(tile_x * tile_width, tile_y * tile_height, tile_width, tile_height)
            if player_rect.colliderect(tile_rect):
                return True
        return False

    def _teleport_player_to_tile(self, player, tile_x: int, tile_y: int, tile_width: int, tile_height: int):
        player_rect = player.get_rect() if hasattr(player, "get_rect") else player.rect
        offset_x = player_rect.x - player.pos.x
        offset_y = player_rect.y - player.pos.y

        player.pos.x = tile_x * tile_width - offset_x
        player.pos.y = tile_y * tile_height - offset_y