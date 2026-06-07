import os
import pytmx
import pygame
from src.core.logger import logger
import src.config as cfg
from src.map.locations import get_location_id, get_location, LOCATION_DEFS

class Map:
    FRINGE_LAYER_NAME = "details fringe layer"
    FRINGE_LAYER_FADE_ALPHA = 110

    # Layers to skip when building collision obstacles.
    # These are purely decorative wall layers that should not block movement.
    COLLISION_SKIP_LAYER_NAMES = {"back walls", "another walls"}

    ANIMATION_SPEED = 0.2

    TILESET_ANIMATIONS = {
        "smoke": {
            "frame_step": 6,
            "frame_count": 6,
        },
        "Water + terrain": {
            "frame_step": 1,
            "frame_count": 8,
            "seq_start": 29,
        },
    }

    """
    Represents a tile-based game map loaded from a Tiled map file.

    This class handles loading, caching, and drawing of the map using pytmx and pygame.

    Attributes:
        FRINGE_LAYER_NAME (str): Name of the fringe tile layer.
        FRINGE_LAYER_FADE_ALPHA (int): Alpha value for fading fringe tiles.
        map_file (str):
            Path to the Tiled map (.tmx) file.
        game_map (pytmx.TiledMap | None):
            The loaded Tiled map object.
        pixel_width (int):
            Width of the map in pixels.
        pixel_height (int):
            Height of the map in pixels.
        _base_render_cache (pygame.Surface | None):
            Cached composite surface for base layers.
        _fringe_components (list[dict]):
            Cached fringe layer components with surfaces and tile rects.

    Methods:
        __init__(map_file):
            Initialize the map with the given file path.
        ensure_loaded():
            Load the map file if not already loaded.
        _is_fringe_layer(layer):
            Check if a layer is the fringe overlay layer.
        _build_fringe_components(layer):
            Build grouped fringe surfaces for efficient drawing.
        _build_render_cache():
            Pre-render all non-fringe layers into a cached surface.
        get_tmx_data():
            Return the loaded TMX data, loading if needed.
        draw(screen, camera_offset=None):
            Draw the base map layers onto the given Pygame surface.
        draw_fringe_overlay(screen, camera_offset=None, player=None):
            Draw the fringe overlay with optional player fade.
        _should_fade_component(player_rect, tile_rects):
            Determine whether a fringe component should fade.
        get_obstacles():
            Collect all collidable rects from the map.
    """

    WINDOW_LOCAL_IDS = (
        382, 383, 384, 385, 386,
        416, 417, 418, 419, 420,
        515, 516, 518, 519, 520, 522, 523,
        549, 550, 552, 553, 554, 556, 557,
    )

    WINDOW_GLOW_RADIUS = 96
    WINDOW_GLOW_COLOR = (255, 170, 60)
    WINDOW_GLOW_MAX_ALPHA = 55

    def __init__(self, map_file: str):
        self.map_file = map_file
        self.game_map = None
        self.pixel_width = 0
        self.pixel_height = 0
        self._base_render_cache = None
        self._fringe_components = []
        self._animated_tiles = {"base": [], "fringe": []}
        self._anim_firstgid_map = {}
        self._anim_elapsed = 0.0
        self._window_glow = None

    def _has_valid_tile_property(self, props, gid):
        """Verify a tile property entry belongs to the correct tile.

        pytmx's gid renumbering can cause tile_properties from one tileset
        to be stored at gids that happen to collide with renumbered gids
        from a different tileset. Use tiledgidmap to detect this mismatch.
        """
        if self.game_map is None:
            return True
        tile_id = props.get("id")
        if tile_id is None:
            return True
        original_gid = self.game_map.tiledgidmap.get(gid)
        if original_gid is None:
            return True
        for ts in self.game_map.tilesets:
            if ts.firstgid <= original_gid < ts.firstgid + ts.tilecount:
                expected_gid = ts.firstgid + tile_id
                if original_gid != expected_gid:
                    return False
                break
        return True

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

    def _get_anim_config_for_gid(self, gid):
        if not self._anim_firstgid_map:
            return None
        tiled_gid = self.game_map.tiledgidmap.get(gid, gid)
        for firstgid, config in self._anim_firstgid_map.items():
            if firstgid <= tiled_gid < firstgid + config["tilecount"]:
                return (firstgid, config, tiled_gid)
        return None

    def _register_animated_tiles(self):
        for ts in self.game_map.tilesets:
            config = self.TILESET_ANIMATIONS.get(ts.name)
            if config is None:
                continue
            path = os.path.join(os.path.dirname(self.map_file), ts.source)
            if not os.path.exists(path):
                logger.warning(f"Tileset image not found: {path}")
                continue
            colorkey = getattr(ts, "trans", None)
            if colorkey:
                colorkey = pygame.Color(f"#{colorkey}")
            full_image = pygame.image.load(path)
            for local_id in range(ts.tilecount):
                tiled_gid = ts.firstgid + local_id
                gid_entries = self.game_map.gidmap.get(tiled_gid)
                if not gid_entries:
                    pytmx_gid = self.game_map.register_gid(tiled_gid)
                    col = local_id % ts.columns
                    row = local_id // ts.columns
                    x = ts.margin + col * (ts.tilewidth + ts.spacing)
                    y = ts.margin + row * (ts.tileheight + ts.spacing)
                    rect = (x, y, ts.tilewidth, ts.tileheight)
                    from pytmx.util_pygame import smart_convert
                    tile = full_image.subsurface(rect)
                    tile = smart_convert(tile, colorkey, pixelalpha=True)
                    if pytmx_gid >= len(self.game_map.images):
                        self.game_map.images.extend([None] * (pytmx_gid - len(self.game_map.images) + 1))
                    self.game_map.images[pytmx_gid] = tile
            full_image = None

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
                anim_info = self._get_anim_config_for_gid(gid)
                if anim_info:
                    firstgid, config, tiled_gid = anim_info
                    local_id = tiled_gid - firstgid
                    if "seq_start" in config:
                        if not (config["seq_start"] <= local_id < config["seq_start"] + config["frame_count"]):
                            # not in the animation sequence — render as static
                            pass
                        else:
                            anim_base = local_id - config["seq_start"]
                            extra = {"seq_start": config["seq_start"]}
                            self._animated_tiles["fringe"].append({
                                "x": cell_x,
                                "y": cell_y,
                                "firstgid": firstgid,
                                "anim_base": anim_base,
                                "frame_count": config["frame_count"],
                                "frame_step": config["frame_step"],
                                **extra,
                            })
                            continue
                    else:
                        stride = config["frame_step"] * config["frame_count"]
                        anim_base = (local_id // stride) * stride + (local_id % config["frame_step"])
                        self._animated_tiles["fringe"].append({
                            "x": cell_x,
                            "y": cell_y,
                            "firstgid": firstgid,
                            "anim_base": anim_base,
                            "frame_count": config["frame_count"],
                            "frame_step": config["frame_step"],
                        })
                        continue
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

            if not tile_rects:
                continue

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
            self._window_overlay = None
            self._window_positions = []
            return

        self._anim_firstgid_map = {}
        for ts in self.game_map.tilesets:
            config = self.TILESET_ANIMATIONS.get(ts.name)
            if config:
                self._anim_firstgid_map[ts.firstgid] = {
                    **config,
                    "tilecount": ts.tilecount,
                    "_tileset": ts,
                }
        self._register_animated_tiles()

        self._animated_tiles = {"base": [], "fringe": []}

        surface = pygame.Surface((self.pixel_width, self.pixel_height), pygame.SRCALPHA)
        fringe_components = []
        tilewidth = self.game_map.tilewidth
        tileheight = self.game_map.tileheight
        window_surf = pygame.Surface((self.pixel_width, self.pixel_height), pygame.SRCALPHA)
        orange_cache = {}
        window_positions = []
        for layer in self.game_map.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                if self._is_fringe_layer(layer):
                    fringe_components.extend(self._build_fringe_components(layer))
                    continue
                for x, y, gid in layer:
                    anim_info = self._get_anim_config_for_gid(gid)
                    if anim_info:
                        firstgid, config, tiled_gid = anim_info
                        local_id = tiled_gid - firstgid
                        if "seq_start" in config:
                            if not (config["seq_start"] <= local_id < config["seq_start"] + config["frame_count"]):
                                pass
                            else:
                                anim_base = local_id - config["seq_start"]
                                extra = {"seq_start": config["seq_start"]}
                                self._animated_tiles["base"].append({
                                    "x": x,
                                    "y": y,
                                    "firstgid": firstgid,
                                    "anim_base": anim_base,
                                    "frame_count": config["frame_count"],
                                    "frame_step": config["frame_step"],
                                    **extra,
                                })
                                continue
                        else:
                            stride = config["frame_step"] * config["frame_count"]
                            anim_base = (local_id // stride) * stride + (local_id % config["frame_step"])
                            self._animated_tiles["base"].append({
                                "x": x,
                                "y": y,
                                "firstgid": firstgid,
                                "anim_base": anim_base,
                                "frame_count": config["frame_count"],
                                "frame_step": config["frame_step"],
                            })
                            continue
                    tile = self.game_map.get_tile_image_by_gid(gid)
                    if tile:
                        surface.blit(tile, (x * tilewidth, y * tileheight))
                    if not gid:
                        continue
                    props = self.game_map.get_tile_properties_by_gid(gid)
                    if props and props.get("id") in self.WINDOW_LOCAL_IDS:
                        window_positions.append((x * tilewidth + tilewidth // 2, y * tileheight + tileheight // 2))
                        if gid not in orange_cache and tile:
                            orange = tile.copy()
                            px = pygame.PixelArray(orange)
                            px.replace((99, 96, 159), (180, 100, 40))
                            px.replace((123, 133, 195), (210, 145, 65))
                            px.replace((138, 177, 219), (235, 185, 100))
                            del px
                            orange_cache[gid] = orange
                        if gid in orange_cache:
                            window_surf.blit(orange_cache[gid], (x * tilewidth, y * tileheight))
        self._base_render_cache = surface
        self._fringe_components = fringe_components
        self._window_overlay = window_surf if orange_cache else None
        self._window_positions = window_positions

        # Pre-bake a warm radial glow around each window so it appears
        # on the map layer (below entities) rather than in the post-FX overlay.
        if window_positions:
            glow = pygame.Surface((self.pixel_width, self.pixel_height), pygame.SRCALPHA)
            r = self.WINDOW_GLOW_RADIUS
            cr, cg, cb = self.WINDOW_GLOW_COLOR
            for wx, wy in window_positions:
                for i in range(r, 0, -2):
                    frac = i / r
                    a = int((1.0 - frac) * self.WINDOW_GLOW_MAX_ALPHA)
                    pygame.draw.circle(glow, (cr, cg, cb, a), (wx, wy), i)
            self._window_glow = glow
        else:
            self._window_glow = None

    def get_tmx_data(self):
        if self.ensure_loaded():
            return self.game_map
        return None

    def _get_animated_gid(self, info, frame_index):
        if "seq_start" in info:
            offset = (info["anim_base"] + frame_index * info["frame_step"]) % info["frame_count"]
            return info["firstgid"] + info["seq_start"] + offset
        return info["firstgid"] + info["anim_base"] + frame_index * info["frame_step"]

    def _draw_animated_tiles(self, screen, camera_offset, tile_list, fade_alpha=None):
        if not tile_list:
            return
        frame_index = int(self._anim_elapsed / self.ANIMATION_SPEED) % max(
            (info["frame_count"] for info in tile_list), default=1
        )
        tilewidth = self.game_map.tilewidth
        tileheight = self.game_map.tileheight
        for info in tile_list:
            tiled_gid = self._get_animated_gid(info, frame_index % info["frame_count"])
            gid_entries = self.game_map.gidmap.get(tiled_gid)
            if not gid_entries:
                continue
            pytmx_gid = gid_entries[0][0]
            tile = self.game_map.get_tile_image_by_gid(pytmx_gid)
            if tile:
                px = info["x"] * tilewidth
                py = info["y"] * tileheight
                if camera_offset is None:
                    draw_pos = (px, py)
                else:
                    draw_pos = (px - int(camera_offset.x), py - int(camera_offset.y))

                if fade_alpha is not None:
                    tile_copy = tile.copy()
                    tile_copy.set_alpha(fade_alpha)
                    screen.blit(tile_copy, draw_pos)
                else:
                    screen.blit(tile, draw_pos)

    def update_animation(self, dt):
        self._anim_elapsed += dt

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
        self._draw_animated_tiles(screen, camera_offset, self._animated_tiles["base"])

        if self._window_glow is not None and cfg.ENVIRONMENT_BRIGHTNESS < 0.6:
            if camera_offset is None:
                screen.blit(self._window_glow, (0, 0))
            else:
                screen.blit(self._window_glow, (-int(camera_offset.x), -int(camera_offset.y)))

        if self._window_overlay is not None and cfg.ENVIRONMENT_BRIGHTNESS < 0.6:
            if camera_offset is None:
                screen.blit(self._window_overlay, (0, 0))
            else:
                screen.blit(self._window_overlay, (-int(camera_offset.x), -int(camera_offset.y)))

    def draw_fringe_overlay(self, screen, camera_offset=None, player=None):
        if not self.ensure_loaded():
            return

        if self._base_render_cache is None:
            self._build_render_cache()

        player_rect = None
        if player is not None:
            player_rect = pygame.Rect(int(player.pos.x), int(player.pos.y), player.image.get_width(), player.image.get_height())

        fringe_should_fade = False
        for component in self._fringe_components:
            surface = component["surface"]
            alpha = 255
            if player_rect is not None and self._should_fade_component(player_rect, component["tile_rects"]):
                alpha = self.FRINGE_LAYER_FADE_ALPHA
                fringe_should_fade = True

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

        if fringe_should_fade:
            self._draw_animated_tiles(screen, camera_offset, self._animated_tiles["fringe"], fade_alpha=self.FRINGE_LAYER_FADE_ALPHA)
        else:
            self._draw_animated_tiles(screen, camera_offset, self._animated_tiles["fringe"])

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

    def get_window_positions(self):
        """Return list of (world_x, world_y) center positions for all window tiles."""
        if not self.ensure_loaded():
            return []
        if self._base_render_cache is None:
            self._build_render_cache()
        return list(self._window_positions)

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

                if layer.name.strip().lower() in self.COLLISION_SKIP_LAYER_NAMES:
                    continue

                for x, y, gid in layer:
                    if not gid:
                        continue

                    tile_properties = self.game_map.get_tile_properties_by_gid(gid)
                    if not tile_properties:
                        continue

                    if not tile_properties.get("collidable"):
                        continue

                    if not self._has_valid_tile_property(tile_properties, gid):
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
        map_transitions (dict):
            Dictionary mapping source map paths to directional transitions.

    Methods:
        __init__(name, map_file):
            Initialize the local map manager with a name and starting map file.
        draw(screen, camera_offset=None):
            Draw the current map onto the given Pygame surface.
        draw_fringe_overlay(screen, camera_offset=None, player=None):
            Draw the current map's fringe overlay.
        get_obstacles():
            Return the current map's obstacle rects.
        update(player):
            Update map logic and handle transitions based on player position.
        switch_map(new_map_path):
            Switch to a new map by file path.
        _player_overlaps_any_tile(player_rect, tile_width, tile_height, tile_positions):
            Check if the player overlaps any of the given tile positions.
        _teleport_player_to_tile(player, tile_x, tile_y, tile_width, tile_height):
            Teleport the player to a specific tile position.
    """
    def __init__(self, name: str, map_file: str):
        self.name = name
        self.current_map = Map(map_file)
        self.current_map_path = map_file
        self.current_location_id = get_location_id(map_file)

        self.transition_buffer = 80
        self.transit_exit_positions = {}
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
                "up": {"map": "maps/test-map-3.tmx", "spawn": {"type": "side", "side": "bottom_center"}},
            },
            "maps/test-map-3.tmx": {
                "down": {"map": "maps/test-map-2.tmx", "spawn": {"type": "return"}},
            },
        }

    def draw(self, screen, camera_offset=None):
        self.current_map.draw(screen, camera_offset)

    def draw_fringe_overlay(self, screen, camera_offset=None, player=None):
        self.current_map.draw_fringe_overlay(screen, camera_offset, player)

    def get_obstacles(self):
        return self.current_map.get_obstacles()

    def get_window_positions(self):
        """Return list of (world_x, world_y) center positions for all window tiles."""
        if self.current_map is None:
            return []
        return self.current_map.get_window_positions()

    def update_animation(self, dt):
        if self.current_map:
            self.current_map.update_animation(dt)

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

        # Map 3 (Temple) → Map 4 (Cave) at tile (4, 5) — triggers location travel menu
        if self.current_map_path == "maps/test-map-3.tmx":
            col = int((player.pos.x + sprite_w / 2) // tile_width)
            feet_y = player.pos.y + sprite_h
            if col == 4 and feet_y >= 5 * tile_height - self.transition_buffer:
                target_map = "maps/test-map-4.tmx"
                target_loc = get_location_id(target_map)
                if target_loc is not None and target_loc != self.current_location_id:
                    if not hasattr(self, "location_exits"):
                        self.location_exits = {}
                    self.location_exits[self.current_location_id] = {
                        "map_path": self.current_map_path,
                        "pos": (player.pos.x, player.pos.y),
                    }
                    self.location_exits[target_loc] = {
                        "map_path": target_map,
                        "pos": (15 * tile_width, 36 * tile_height),
                    }
                    new_map = ("location_transition", target_loc)
                    return new_map

        # Map 4 (Cave) → Map 3 (Temple) at bottom centre — triggers location travel menu
        if self.current_map_path == "maps/test-map-4.tmx":
            cave_exit_tiles = [(x, 39) for x in range(13, 18)]
            if self._player_overlaps_any_tile(player_rect, tile_width, tile_height, cave_exit_tiles):
                target_map = "maps/test-map-3.tmx"
                target_loc = get_location_id(target_map)
                if target_loc is not None and target_loc != self.current_location_id:
                    if not hasattr(self, "location_exits"):
                        self.location_exits = {}
                    self.location_exits[self.current_location_id] = {
                        "map_path": self.current_map_path,
                        "pos": (player.pos.x, player.pos.y),
                    }
                    self.location_exits[target_loc] = {
                        "map_path": target_map,
                        "pos": (4 * tile_width, 5 * tile_height),
                    }
                    new_map = ("location_transition", target_loc)
                    return new_map

        # Directional edge checks (right/left/up/down)
        # Determine player's height for vertical checks
        if hasattr(player_rect, 'height'):
            h = player_rect.height
        else:
            h = player.image.get_height()

        direction = None
        if (self.current_map_path == "maps/test-map-2.tmx"
                and player.pos.y <= 10):
            zone_width = map_width / 12.0
            player_center_x = x + w / 2
            if 7 * zone_width <= player_center_x < 9 * zone_width:
                direction = "up"
        if direction is None:
            if x + w >= map_width - self.transition_buffer:
                direction = "right"
            elif x <= self.transition_buffer:
                direction = "left"
            elif player.pos.y + h >= (tmx_data.height * tile_height) - self.transition_buffer:
                direction = "down"
            elif (player.pos.y <= self.transition_buffer
                  and self.current_map_path != "maps/test-map-2.tmx"):
                direction = "up"

        if direction is not None:
            transitions = self.map_transitions.get(self.current_map_path, {})
            trans = transitions.get(direction)
            if trans:
                target_map = trans["map"]
                target_loc = get_location_id(target_map)
                if target_loc is not None and target_loc != self.current_location_id:
                    if not hasattr(self, "location_exits"):
                        self.location_exits = {}
                    self.location_exits[self.current_location_id] = {
                        "map_path": self.current_map_path,
                        "pos": (player.pos.x, player.pos.y),
                    }
                    return ("location_transition", target_loc)

                # remember previous position to pick nearest corner if needed
                old_x = player.pos.x
                old_y = player.pos.y
                self.transit_exit_positions[self.current_map_path] = (old_x, old_y)

                new_map = target_map
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
                        elif side == "center":
                            player.pos.x = (allowed_x_min + allowed_x_max) / 2
                            player.pos.y = (allowed_y_min + allowed_y_max) / 2
                        elif side == "bottom_center":
                            player.pos.x = (allowed_x_min + allowed_x_max) / 2
                            player.pos.y = bottom_y
                    elif spawn.get("type") == "return":
                        saved = self.transit_exit_positions.get(new_map)
                        if saved:
                            saved_x, saved_y = saved
                            player.pos.x = max(allowed_x_min, min(saved_x, allowed_x_max))
                            player.pos.y = max(allowed_y_min, min(saved_y, allowed_y_max))
                        else:
                            player.pos.x = (allowed_x_min + allowed_x_max) / 2
                            player.pos.y = (allowed_y_min + allowed_y_max) / 2
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
        new_loc = get_location_id(new_map_path)
        if new_loc is not None:
            self.current_location_id = new_loc

    def switch_to_location(self, location_id):
        loc = get_location(location_id)
        if not loc or not loc["maps"]:
            logger.warning(f"Cannot switch to location '{location_id}': no maps available")
            return None
        entry_map = loc.get("entry_map") or loc["maps"][0]
        self.current_location_id = location_id
        self.switch_map(entry_map)
        return entry_map

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