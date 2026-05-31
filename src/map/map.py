import pytmx
import pygame
from src.core.logger import logger

class Map:
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
        self._render_cache = None

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

    def _build_render_cache(self):
        if self.game_map is None:
            self._render_cache = None
            return

        surface = pygame.Surface((self.pixel_width, self.pixel_height), pygame.SRCALPHA)
        for layer in self.game_map.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = self.game_map.get_tile_image_by_gid(gid)
                    if tile:
                        surface.blit(tile, (x * self.game_map.tilewidth, y * self.game_map.tileheight))
        self._render_cache = surface

    def get_tmx_data(self):
        if self.ensure_loaded():
            return self.game_map
        return None

    def draw(self, screen, camera_offset=None):
        if not self.ensure_loaded():
            return

        if self._render_cache is None:
            self._build_render_cache()
        if self._render_cache is not None:
            if camera_offset is None:
                screen.blit(self._render_cache, (0, 0))
            else:
                screen.blit(self._render_cache, (-int(camera_offset.x), -int(camera_offset.y)))

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

    def draw(self, screen, camera_offset=None):
        self.current_map.draw(screen, camera_offset)

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

        spawn_offset = self.transition_buffer + 30 
        new_map = None

        if self.current_map_path == "maps/test-map-1.tmx":
            if self._player_overlaps_any_tile(player_rect, tile_width, tile_height, [(36, 16), (37, 16)]):
                new_map = "maps/tavern.tmx"
                self.switch_map(new_map)
                self._teleport_player_to_tile(player, 14, 38, tile_width, tile_height)
                return new_map

        if self.current_map_path == "maps/test-map-1.tmx":
            if x + w >= map_width - self.transition_buffer:
                new_map = "maps/test-map-2.tmx"
                self.switch_map(new_map)
                player.pos.x = spawn_offset  

        elif self.current_map_path == "maps/test-map-2.tmx":
            if x <= self.transition_buffer:
                new_map = "maps/test-map-1.tmx"
                self.switch_map(new_map)
                player.pos.x = map_width - w - spawn_offset 
            
            elif x + w >= map_width - self.transition_buffer:
                new_map = "maps/test-map-3.tmx"
                self.switch_map(new_map)
                player.pos.x = spawn_offset
                
        elif self.current_map_path == "maps/test-map-3.tmx":
            if x <= self.transition_buffer:
                new_map = "maps/test-map-2.tmx"
                self.switch_map(new_map)
                player.pos.x = map_width - w - spawn_offset

        elif self.current_map_path == "maps/tavern.tmx":
            tavern_exit_tiles = [(x, 39) for x in range(13, 17)]
            if self._player_overlaps_any_tile(player_rect, tile_width, tile_height, tavern_exit_tiles):
                new_map = "maps/test-map-1.tmx"
                self.switch_map(new_map)
                self._teleport_player_to_tile(player, 36, 17, tile_width, tile_height)
                return new_map

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