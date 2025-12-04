import pytmx
import pygame

class Map:
    """
    Represents a tile-based game map loaded from a Tiled map file.
    Only handles loading and drawing.
    """

    def __init__(self, map_file: str):
        self.map_file = map_file
        self.game_map = None
        self.pixel_width = 0
        self.pixel_height = 0

    def draw(self, screen):
        if self.game_map is None:
            self.game_map = pytmx.load_pygame(self.map_file)
            self.pixel_width = self.game_map.width * self.game_map.tilewidth
            self.pixel_height = self.game_map.height * self.game_map.tileheight

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
    """
    def __init__(self, name: str, map_file: str):
        self.name = name
        self.current_map = Map(map_file)
        self.current_map_path = map_file 
        
        # === ЗМІНА 1: Збільшили буфер ===
        # Це зона "тригера". Якщо гравець заходить у цю зону, стається перехід.
        self.transition_buffer = 150 

    def draw(self, screen):
        self.current_map.draw(screen)

    def update(self, player):
        # 1. Завантаження
        if self.current_map.game_map is None:
            self.current_map.game_map = pytmx.load_pygame(self.current_map.map_file)

        # 2. Розміри карти
        tmx_data = self.current_map.game_map
        map_width = tmx_data.width * tmx_data.tilewidth
        
        # 3. Гравець
        if hasattr(player, 'rect'):
            w = player.rect.width
        else:
            w = player.image.get_width()
            
        x = player.pos.x

        # === ЗМІНА 2: Безпечний відступ ===
        # Куди ставити гравця після переходу. 
        # Це має бути БІЛЬШЕ, ніж transition_buffer, інакше він одразу телепортується назад.
        spawn_offset = self.transition_buffer + 20 

        # 4. Логіка переходів
        
        if self.current_map_path == "maps/test-map-1.tmx":
            # Правий край
            if x + w >= map_width - self.transition_buffer:
                self.switch_map("maps/test-map-2.tmx")
                # Ставимо гравця зліва, але ЗА межами буфера тригера
                player.pos.x = spawn_offset  

        elif self.current_map_path == "maps/test-map-2.tmx":
            # Лівий край
            if x <= self.transition_buffer:
                self.switch_map("maps/test-map-1.tmx")
                # Ставимо гравця справа, ЗА межами буфера
                player.pos.x = map_width - w - spawn_offset 
            
            # Правий край
            elif x + w >= map_width - self.transition_buffer:
                self.switch_map("maps/test-map-3.tmx")
                player.pos.x = spawn_offset
                
        elif self.current_map_path == "maps/test-map-3.tmx":
            # Лівий край
            if x <= self.transition_buffer:
                self.switch_map("maps/test-map-2.tmx")
                player.pos.x = map_width - w - spawn_offset

    def switch_map(self, new_map_path):
        print(f"Switching map to: {new_map_path}")
        self.current_map = Map(new_map_path)
        self.current_map_path = new_map_path