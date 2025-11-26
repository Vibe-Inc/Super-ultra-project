import pytmx

class Map:
    """
    Represents a tile-based game map loaded from a Tiled map file.
    Attributes:
        map_file (str): Path to the Tiled map file (.tmx).
        game_map (pytmx.TiledMap): The loaded Tiled map object.
    Methods:
        __init__(map_file: str):
            Initializes the Map instance with the given map file path.
        draw(screen):
            Draws the visible layers of the map onto the provided Pygame screen surface.
            Loads the map file if it hasn't been loaded yet.
    """

    def __init__(self, map_file: str):
        self.map_file = map_file
        self.game_map: pytmx.TiledMap = None

    def draw(self, screen):
        if self.game_map is None:
            self.game_map = pytmx.load_pygame(self.map_file)

        for layer in self.game_map.visible_layers:
            for x, y, gid in layer:
                tile = self.game_map.get_tile_image_by_gid(gid)
                if tile:
                    screen.blit(tile, (x * self.game_map.tilewidth,
                                       y * self.game_map.tileheight))
