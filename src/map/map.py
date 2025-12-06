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

    def draw(self, screen):
        if self.game_map is None:
            try:
                logger.info(f"Loading map: {self.map_file}")
                self.game_map = pytmx.load_pygame(self.map_file)
                self.pixel_width = self.game_map.width * self.game_map.tilewidth
                self.pixel_height = self.game_map.height * self.game_map.tileheight
                logger.info(f"Map loaded successfully: {self.map_file} ({self.pixel_width}x{self.pixel_height})")
            except Exception as e:
                logger.error(f"Failed to load map {self.map_file}: {e}")
                return

        for layer in self.game_map.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = self.game_map.get_tile_image_by_gid(gid)
                    if tile:
                        screen.blit(tile, (x * self.game_map.tilewidth,
                                           y * self.game_map.tileheight))


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

    def draw(self, screen):
        self.current_map.draw(screen)

    def update(self, player):
        """
        Updates map logic and handles transitions based on player position.
        Returns: string (path to new map) if switch happened, else None.
        """
        if self.current_map.game_map is None:
            self.current_map.game_map = pytmx.load_pygame(self.current_map.map_file)

        tmx_data = self.current_map.game_map
        map_width = tmx_data.width * tmx_data.tilewidth

        if hasattr(player, 'rect'):
            w = player.rect.width
        else:
            w = player.image.get_width()
        x = player.pos.x

        spawn_offset = self.transition_buffer + 30 
        new_map = None

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

        return new_map

    def switch_map(self, new_map_path):
        print(f"Switching map to: {new_map_path}")
        self.current_map = Map(new_map_path)
        self.current_map_path = new_map_path