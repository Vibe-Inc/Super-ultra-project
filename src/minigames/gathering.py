"""Gathering minigame for the player.

Lets the player chop trees, mine rocks and crack ore veins when they
have a suitable tool (an axe for wood, a pickaxe for stone, a hammer
for ore) selected in the hotbar's active slot. The player must be
within reach of a gatherable object and press **G** to begin
gathering; **K** cancels an in-progress gather.

Two kinds of gatherables are supported simultaneously:

* **Tile properties** -- a Tiled tile with the custom property
  ``choppable`` or ``minable`` set to a truthy value. The historical
  behaviour, kept for backwards compatibility with existing maps.
* **Coordinate-based nodes** -- :class:`GatherableNode` objects
  registered in the active :class:`GatherableNodeRegistry` (see
  :mod:`src.world.gatherable_nodes`). These let designers place
  trees/rocks/ore veins at exact pixel coordinates without touching
  the ``.tmx`` files.

The mechanic is a small timed progress bar rather than a full
Stardew-style fishing minigame: the bar fills at a rate that depends
on the tool's ``power`` stat, and the bar simply has to fill to
complete the gather. On success the configured
``gather_yield_min``..``gather_yield_max`` resource items are spawned
as world drops and the tool's durability ticks down by one.

States:

* ``idle``   -- the player can start a gather.
* ``active`` -- the bar is filling; **K** cancels.
* ``result`` -- a brief "Got X!" or "Cancelled" overlay is shown.

The controller exposes :py:meth:`update` for the per-frame tick,
:py:meth:`draw` for the render hook, and :py:meth:`handle_event` for
pygame event dispatch.
"""

import math
import random
import pytmx
import pygame
from typing import Optional

try:
    from src.items.items import create_item
except Exception:
    def create_item(_id):
        return None


GATHER_TILE_PROPERTY = {
    "wood":   "choppable",
    "stone":  "minable",
    "ore":    "minable",
}

# Default per-gather-type yield item id when the tool doesn't override it.
GATHER_DEFAULT_YIELD = {
    "wood":  "wood",
    "stone": "stone",
    "ore":   "iron_ore",
}

# How far (in pixels) the controller will search for a coordinate-based
# gatherable node around the player. Equivalent to roughly 2 tiles for
# a 32-pixel tileset.
NODE_SEARCH_RADIUS = 96.0

# How far (in tiles) the controller will search around the player for
# a gatherable tile property. Kept the same as the historical value of
# 1 (so 8 adjacent tiles).
TILE_SEARCH_RANGE = 1

# UI labels for the per-gather-type action verb.
GATHER_LABELS = {
    "wood":  "Chopping",
    "stone": "Mining",
    "ore":   "Mining",
}


class GatheringResult:
    """Lightweight transient UI message shown after a gather attempt."""

    def __init__(self, message: str, success: bool, duration: float = 1.8):
        self.message = message
        self.success = success
        self.duration = duration
        self.timer = duration

    def update(self, dt: float) -> None:
        self.timer = max(0.0, self.timer - dt)

    @property
    def alive(self) -> bool:
        return self.timer > 0.0


class GatheringUI:
    """Renderer for the gathering minigame progress bar and result popup."""

    BAR_WIDTH = 140
    BAR_HEIGHT = 12

    def __init__(self, controller):
        self.ctrl = controller
        self.font = pygame.font.SysFont(None, 24)
        self.hint_font = pygame.font.SysFont(None, 20)

    def draw(self, screen: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        if self.ctrl.state == "active":
            self._draw_progress_bar(screen)
        if self.ctrl.result and self.ctrl.result.alive:
            self._draw_result_popup(screen)
        self._draw_hint(screen)

    def _draw_progress_bar(self, screen: pygame.Surface) -> None:
        player_screen = self.ctrl.game.character.get_center() - self.ctrl.game._get_camera_offset()
        bar_x = int(player_screen.x - self.BAR_WIDTH // 2)
        bar_y = int(player_screen.y - 70)
        bg = pygame.Rect(bar_x - 3, bar_y - 3, self.BAR_WIDTH + 6, self.BAR_HEIGHT + 6)
        pygame.draw.rect(screen, (15, 15, 20), bg, border_radius=3)
        pygame.draw.rect(screen, (40, 35, 50),
                         (bar_x, bar_y, self.BAR_WIDTH, self.BAR_HEIGHT),
                         border_radius=2)
        fill_w = int(self.ctrl.fill * self.BAR_WIDTH)
        if fill_w > 0:
            t = self.ctrl.fill
            r = int(220 - 160 * t)
            g = int(180 + 40 * t)
            b = 60
            pygame.draw.rect(screen, (r, g, b),
                             (bar_x, bar_y, fill_w, self.BAR_HEIGHT),
                             border_radius=2)
        label = self.hint_font.render(
            f"{self.ctrl.gather_label}...", True, (240, 240, 240)
        )
        screen.blit(label,
                    (bar_x + self.BAR_WIDTH // 2 - label.get_width() // 2,
                     bar_y - 22))
        hint = self.hint_font.render("K to cancel", True, (200, 200, 200))
        screen.blit(hint,
                    (bar_x + self.BAR_WIDTH // 2 - hint.get_width() // 2,
                     bar_y + self.BAR_HEIGHT + 4))

    def _draw_result_popup(self, screen: pygame.Surface) -> None:
        r = self.ctrl.result
        color = (90, 220, 90) if r.success else (220, 110, 110)
        txt = self.font.render(r.message, True, color)
        screen.blit(txt, (screen.get_width() // 2 - txt.get_width() // 2,
                          screen.get_height() // 2 - 120))

    def _draw_hint(self, screen: pygame.Surface) -> None:
        """Show a floating 'Press G to ...' prompt above the nearest
        gatherable when the player has the right tool equipped but
        isn't currently gathering.
        """
        if self.ctrl.state != "idle":
            return
        info = self.ctrl.get_nearest_gatherable()
        if not info:
            return
        node, gather_type = info
        label = GATHER_LABELS.get(gather_type, "Gathering")
        verb = {
            "wood":  "chop",
            "stone": "mine",
            "ore":   "crack",
        }.get(gather_type, "gather")
        msg = f"Press G to {verb}"
        screen_pos = node.pos - self.ctrl.game._get_camera_offset()
        text = self.hint_font.render(msg, True, (245, 245, 220))
        bg_rect = text.get_rect(
            center=(int(screen_pos.x), int(screen_pos.y - 50))
        )
        bg_rect.inflate_ip(12, 6)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 160))
        screen.blit(bg_surf, bg_rect.topleft)
        screen.blit(text, text.get_rect(center=bg_rect.center))


class GatheringController:
    """State machine that drives chopping / mining.

    Attributes:
        game: Owning :class:`src.core.game.Game` instance.
        state (str): One of ``"idle"``, ``"active"``, ``"result"``.
        target_kind (str | None):
            ``"tile"`` if the current target is a Tiled tile property,
            ``"node"`` if it's a coordinate-based
            :class:`GatherableNode`, or ``None`` when idle.
        target_tile (tuple | None): ``(tile_x, tile_y)`` of the
            gatherable tile being targeted, or ``None`` when idle.
        target_node (GatherableNode | None):
            The coordinate-based node being targeted, or ``None``.
        target_gather_type (str | None): The resource type the
            targeted object produces (``"wood"``, ``"stone"``,
            ``"ore"``).
        target_yield_item_id (str | None): The ``items.id`` of the
            resource dropped on a successful gather.
        target_yield_min (int): Minimum resource items per success.
        target_yield_max (int): Maximum resource items per success.
        fill (float): Normalized progress (``0.0``..``1.0``) of the
            gathering minigame.
        gather_time (float): Seconds the bar takes to fill at full
            power for the current tool.
        power (int): Cached power of the active gathering tool.
        gather_label (str): UI label for the current action
            (``"Chopping"`` / ``"Mining"``).
        result (GatheringResult | None): Active result popup, or
            ``None``.
        ui (GatheringUI): UI renderer for this controller.
    """

    def __init__(self, game):
        self.game = game
        self.state = "idle"
        self.target_kind: Optional[str] = None
        self.target_node = None
        self.target_tile: Optional[tuple[int, int]] = None
        self.target_gather_type: Optional[str] = None
        self.target_yield_item_id: Optional[str] = None
        self.target_yield_min: int = 1
        self.target_yield_max: int = 1
        self.fill: float = 0.0
        self.gather_time: float = 2.5
        self.power: int = 0
        self.gather_label: str = "Gathering"
        self.result: Optional[GatheringResult] = None
        self.ui = GatheringUI(self)

    # ------------------------------------------------------------------
    # Tool detection
    # ------------------------------------------------------------------
    def _get_active_tool(self):
        """Return the ``Tool`` instance in the hotbar's active slot, or
        ``None`` if the slot is empty or holds a non-tool item.
        """
        try:
            inv_manager = getattr(self.game.app, "INV_manager", None)
            if not inv_manager:
                return None
            hotbar = getattr(inv_manager, "hotbar", None)
            if not hotbar:
                return None
            active = getattr(hotbar, "active_slot_index", None)
            if active is None:
                return None
            if not (0 <= active < len(hotbar.items)):
                return None
            slot = hotbar.items[active][0]
            if not slot:
                return None
            item = slot[0]
            gather_type = getattr(item, "gather_type", None)
            if not gather_type:
                return None
            return item
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Tile-property detection
    # ------------------------------------------------------------------
    def _tile_property_at(self, world_pos: pygame.Vector2, prop_name: str) -> bool:
        """Return ``True`` if the tile at ``world_pos`` has the given custom
        property set to a truthy value.
        """
        try:
            tmx_map = self.game.map.current_map
            tmx = getattr(tmx_map, "tmxdata", None) or getattr(tmx_map, "get_tmx_data", lambda: None)()
            if not tmx:
                return False
            tx = int(world_pos.x // tmx.tilewidth)
            ty = int(world_pos.y // tmx.tileheight)
            for layer in tmx.layers:
                if not isinstance(layer, pytmx.TiledTileLayer):
                    continue
                try:
                    gid = layer.data[ty][tx]
                except (IndexError, TypeError):
                    continue
                if not gid:
                    continue
                tile_props = tmx.get_tile_properties_by_gid(gid)
                if tile_props and tile_props.get(prop_name):
                    return True
        except Exception:
            return False
        return False

    def _find_target_tile(self, gather_type: str, range_tiles: int = TILE_SEARCH_RANGE):
        """Scan the tiles in a small square around the player for one
        whose tile property matches the tool's gather type. Returns
        ``(tile_x, tile_y, property_name, yield_item_id)`` or ``None``.

        The yield item id is derived from the gather type (``wood`` ->
        ``"wood"``, ``stone`` -> ``"stone"``, ``ore`` -> ``"iron_ore"``).
        """
        prop_name = GATHER_TILE_PROPERTY.get(gather_type)
        if not prop_name:
            return None
        try:
            tmx_map = self.game.map.current_map
            tmx = getattr(tmx_map, "tmxdata", None) or getattr(tmx_map, "get_tmx_data", lambda: None)()
            if not tmx:
                return None
            center = self.game.character.get_center()
            cx = int(center.x // tmx.tilewidth)
            cy = int(center.y // tmx.tileheight)
            best = None
            best_dist = None
            for dy in range(-range_tiles, range_tiles + 1):
                for dx in range(-range_tiles, range_tiles + 1):
                    if dx == 0 and dy == 0:
                        continue
                    tx, ty = cx + dx, cy + dy
                    world_pos = pygame.Vector2(tx * tmx.tilewidth + tmx.tilewidth // 2,
                                                ty * tmx.tileheight + tmx.tileheight // 2)
                    if self._tile_property_at(world_pos, prop_name):
                        dist = (dx * dx + dy * dy) ** 0.5
                        if best_dist is None or dist < best_dist:
                            best_dist = dist
                            best = (tx, ty, world_pos)
            if best is None:
                return None
            yield_id = GATHER_DEFAULT_YIELD.get(gather_type, "wood")
            return best[0], best[1], yield_id
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Coordinate-based node detection
    # ------------------------------------------------------------------
    def _get_active_node_registry(self):
        """Return the :class:`GatherableNodeRegistry` for the current
        map, or ``None`` if the map has no registered nodes.
        """
        try:
            gatherables = getattr(self.game, "gatherables", None)
            if gatherables is None:
                return None
            return gatherables.get(self.game.current_map_path)
        except Exception:
            return None

    def _find_target_node(self, gather_type: str):
        """Return the nearest :class:`GatherableNode` matching
        ``gather_type`` within :data:`NODE_SEARCH_RADIUS` of the
        player, or ``None`` if no node is in range.
        """
        registry = self._get_active_node_registry()
        if registry is None:
            return None
        return registry.find_nearest(
            self.game.character.get_center(),
            gather_type,
            max_radius=NODE_SEARCH_RADIUS,
        )

    def get_nearest_gatherable(self):
        """Public helper used by the UI to render the press-G prompt.

        Returns either:

        * ``(GatherableNode, gather_type)`` if a coordinate-based node
          is in range and the active tool matches its gather type;
        * ``(tile_target_tuple, gather_type)`` for a Tiled tile
          property target;
        * ``None`` when no tool is equipped or nothing is in range.
        """
        tool = self._get_active_tool()
        if not tool:
            return None
        gather_type = tool.gather_type
        node = self._find_target_node(gather_type)
        if node is not None:
            return (node, gather_type)
        tile = self._find_target_tile(gather_type)
        if tile is not None:
            return (tile, gather_type)
        return None

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------
    def start(self) -> bool:
        """Try to begin gathering with the active hotbar tool.

        Returns ``True`` if a gather started, ``False`` otherwise (no
        gather tool, no matching tile, or a minigame already running).
        """
        if self.state != "idle":
            return False
        tool = self._get_active_tool()
        if not tool:
            return False
        gather_type = tool.gather_type

        node = self._find_target_node(gather_type)
        tile = None
        if node is None:
            tile = self._find_target_tile(gather_type)
        if node is None and tile is None:
            return False

        self.target_gather_type = gather_type
        self.target_yield_min = max(1, int(getattr(tool, "gather_yield_min", 1) or 1))
        self.target_yield_max = max(self.target_yield_min,
                                    int(getattr(tool, "gather_yield_max", self.target_yield_min) or self.target_yield_min))
        self.power = max(0, int(getattr(tool, "power", 1) or 1))
        self.fill = 0.0
        base = 2.8
        self.gather_time = max(0.6, base - self.power * 0.18)
        self.gather_label = GATHER_LABELS.get(gather_type, "Gathering")

        if node is not None:
            self.target_kind = "node"
            self.target_node = node
            self.target_tile = None
            self.target_yield_item_id = node.yield_item_id or GATHER_DEFAULT_YIELD.get(gather_type, "wood")
        else:
            self.target_kind = "tile"
            self.target_node = None
            tx, ty, yield_id = tile
            self.target_tile = (tx, ty)
            self.target_yield_item_id = yield_id

        self.state = "active"
        return True

    def cancel(self) -> None:
        """Abort an active gathering attempt."""
        if self.state == "active":
            self.state = "idle"
            self.target_kind = None
            self.target_node = None
            self.target_tile = None
            self.target_gather_type = None
            self.target_yield_item_id = None
            self.fill = 0.0
            self.result = GatheringResult("Cancelled", success=False, duration=1.0)

    def _finish_success(self) -> None:
        """Award the gathered resources, deplete the node (if any),
        wear down the tool, and reset.
        """
        yield_id = self.target_yield_item_id
        lo = self.target_yield_min
        hi = self.target_yield_max
        amount = random.randint(lo, hi) if hi > lo else lo
        spawned = 0
        if amount > 0 and yield_id:
            try:
                item_obj = create_item(yield_id)
            except Exception:
                item_obj = None
            if item_obj is not None:
                try:
                    from src.entities.dropped_item import DroppedItem
                    base_x, base_y = self.game.character.get_rect().center
                    drop = DroppedItem(base_x + random.randint(-12, 12),
                                       base_y + random.randint(-6, 6),
                                       item_obj, amount)
                    self.game.items.append(drop)
                    spawned = amount
                except Exception:
                    spawned = 0
        if spawned > 0:
            nice_name = yield_id.replace("_", " ").title()
            self.result = GatheringResult(f"+{spawned} {nice_name}", success=True, duration=1.8)
        else:
            self.result = GatheringResult("Got nothing...", success=False, duration=1.2)

        # Deplete coordinate-based nodes so they can respawn later.
        if self.target_kind == "node" and self.target_node is not None:
            try:
                self.target_node.deplete()
            except Exception:
                pass

        self._damage_tool()
        self._reset_target()

    def _damage_tool(self) -> None:
        """Reduce the active tool's durability by one and remove it
        from the hotbar if it broke.
        """
        try:
            inv_manager = getattr(self.game.app, "INV_manager", None)
            if not inv_manager:
                return
            hotbar = getattr(inv_manager, "hotbar", None)
            if not hotbar:
                return
            active = getattr(hotbar, "active_slot_index", None)
            if active is None or not (0 <= active < len(hotbar.items)):
                return
            slot = hotbar.items[active][0]
            if not slot:
                return
            tool = slot[0]
            if hasattr(tool, "durability"):
                tool.durability = max(0, int(tool.durability) - 1)
                if tool.durability <= 0:
                    hotbar.items[active][0] = None
                    self.result = GatheringResult("Tool broke!", success=False, duration=2.0)
        except Exception:
            pass

    def _reset_target(self) -> None:
        self.state = "idle"
        self.target_kind = None
        self.target_node = None
        self.target_tile = None
        self.target_gather_type = None
        self.target_yield_item_id = None
        self.fill = 0.0
        self.power = 0

    # ------------------------------------------------------------------
    # Per-frame update / event / draw
    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        if self.result and self.result.alive:
            self.result.update(dt)

        if self.state != "active":
            return

        # Abort if the tool is no longer active.
        tool = self._get_active_tool()
        if not tool or tool.gather_type != self.target_gather_type:
            self.cancel()
            return

        # Validate the target each frame; cancel if it disappeared.
        if self.target_kind == "node":
            if self.target_node is None or self.target_node.depleted:
                self.cancel()
                return
        elif self.target_kind == "tile":
            prop = GATHER_TILE_PROPERTY.get(self.target_gather_type or "")
            tx, ty = self.target_tile or (-1, -1)
            tmx = getattr(self.game.map.current_map, "tmxdata", None)
            world_pos = None
            if tmx:
                world_pos = pygame.Vector2(
                    tx * tmx.tilewidth + tmx.tilewidth // 2,
                    ty * tmx.tileheight + tmx.tileheight // 2,
                )
            if not prop or not world_pos or not self._tile_property_at(world_pos, prop):
                self.cancel()
                return

        rate = 1.0 / max(0.001, self.gather_time)
        self.fill = min(1.0, self.fill + rate * dt)
        if self.fill >= 1.0:
            self._finish_success()

    def draw(self, screen: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        try:
            self.ui.draw(screen, camera_offset)
        except Exception:
            pass

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Dispatch a pygame event to the gathering state machine.

        Recognises:
          * ``G`` (KEYDOWN) -- start gathering if idle.
          * ``K`` (KEYDOWN) -- cancel an in-progress gather.

        Returns:
            bool: ``True`` if the event was consumed, ``False`` otherwise.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g and self.state == "idle":
                return self.start()
            if event.key == pygame.K_k and self.state == "active":
                self.cancel()
                return True
        return False
