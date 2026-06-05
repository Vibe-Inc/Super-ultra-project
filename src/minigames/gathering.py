"""Gathering minigame for the player.

Lets the player chop trees, mine rocks and crack ore veins when they
have a suitable tool (an axe for wood, a pickaxe for stone, a hammer
for ore) selected in the hotbar's active slot. The player must be
adjacent to a gatherable tile and press **G** to begin gathering;
**K** cancels an in-progress gather.

A Tiled tile is considered gatherable when one of these custom
properties is set to a truthy value on the tile:

* ``is_wood_gatherable``  -- trees (axe).
* ``is_stone_gatherable`` -- rock outcrops (pickaxe).
* ``is_ore_gatherable``   -- ore veins (hammer).

The legacy ``choppable`` / ``minable`` properties are still honoured
as fallbacks so older maps keep working.

The mechanic is a small timed progress bar rather than a full
Stardew-style fishing minigame: the bar fills at a rate that depends
on the tool's ``power`` stat, and the bar simply has to fill to
complete the gather. On success the configured
``gather_yield_min``..``gather_yield_max`` resource items are added
**directly to the player's inventory** (no world drop is spawned)
and the tool's durability ticks down by one.

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
    from src.core.logger import logger
except Exception:
    import logging
    logger = logging.getLogger("gathering")

try:
    from src.items.items import create_item
except Exception:
    def create_item(_id):
        return None


GATHER_TILE_PROPERTY = {
    "wood":   "is_wood_gatherable",
    "stone":  "is_stone_gatherable",
    "ore":    "is_ore_gatherable",
}

# Legacy tile properties still recognised for backwards compatibility
# with older maps that have not been updated to the is_*_gatherable
# naming scheme. A tile matches if it has *any* of the listed
# properties set to a truthy value.
GATHER_TILE_PROPERTY_FALLBACK = {
    "wood":   ("choppable",),
    "stone":  ("minable",),
    "ore":    ("minable",),
}

# Default per-gather-type yield item id when the tool doesn't override it.
GATHER_DEFAULT_YIELD = {
    "wood":  "wood",
    "stone": "stone",
    "ore":   "iron_ore",
}

# How far (in tiles) the controller will search around the player for
# a gatherable tile property. Kept the same as the historical value of
# 1 (so 8 adjacent tiles).
TILE_SEARCH_RANGE = 1

# Seconds a successfully-gathered tile stays "regrowing" before it
# can be gathered again. Tiles on cooldown still render in the world
# (they're map art, not nodes) but the "Press G to ..." hint is
# replaced with a "Regrowing (Xs)" countdown and the gatherable
# lookup ignores them.
#
# The cooldown is applied to the *cluster* that the targeted tile
# belongs to, so an entire tree/rock regrows at once rather than
# tile-by-tile.
GATHER_COOLDOWN_DURATION = 30.0

# Adjacency mode used when grouping connected gatherable tiles into
# a single cluster. ``4`` means orthogonal neighbours only (up/down/
# left/right), which is the natural fit for Tiled tile maps where a
# tree or rock outcrop is a stack of orthogonal tiles.
GATHER_CLUSTER_ADJACENCY = 4

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
        isn't currently gathering. Tiles on regrow cooldown get a
        "Regrowing (Xs)" prompt instead so the player understands
        why the usual hint isn't actionable.
        """
        if self.ctrl.state != "idle":
            return
        info = self.ctrl.get_nearest_gatherable()
        if not info:
            return
        target, gather_type = info
        world_pos = self._gatherable_world_pos(target)
        if world_pos is None:
            return

        # Cooldown hint: 6-tuple -> (tx, ty, world_pos, gather_type,
        # cluster_idx, remaining). Ready hint: 5-tuple -> (tx, ty,
        # world_pos, yield_id, cluster_idx). The trailing ``remaining``
        # field doubles as the ready/cooldown discriminator.
        if isinstance(target, (tuple, list)) and len(target) >= 6 and target[5] > 0.0:
            remaining = int(math.ceil(target[5]))
            msg = f"Regrowing ({remaining}s)"
            text_color = (200, 200, 210)
        else:
            verb = {
                "wood":  "chop",
                "stone": "mine",
                "ore":   "crack",
            }.get(gather_type, "gather")
            msg = f"Press G to {verb}"
            text_color = (245, 245, 220)

        screen_pos = world_pos - self.ctrl.game._get_camera_offset()
        text = self.hint_font.render(msg, True, text_color)
        bg_rect = text.get_rect(
            center=(int(screen_pos.x), int(screen_pos.y - 50))
        )
        bg_rect.inflate_ip(12, 6)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 160))
        screen.blit(bg_surf, bg_rect.topleft)
        screen.blit(text, text.get_rect(center=bg_rect.center))

    @staticmethod
    def _gatherable_world_pos(target) -> Optional[pygame.Vector2]:
        """Extract the world-space position from a ``get_nearest_gatherable``
        target, which is the ``(tx, ty, world_pos, yield_id, cluster_idx)``
        tuple returned by :meth:`GatheringController._find_target_tile` or
        the longer ``(tx, ty, world_pos, gather_type, cluster_idx, remaining)``
        tuple returned by :meth:`GatheringController._find_cooldown_tile`.
        In both cases the world position (cluster centroid) is the
        element at index 2.
        """
        if target is None:
            return None
        if isinstance(target, (tuple, list)) and len(target) >= 3:
            return target[2]
        return None


class GatheringController:
    """State machine that drives chopping / mining.

    Attributes:
        game: Owning :class:`src.core.game.Game` instance.
        state (str): One of ``"idle"``, ``"active"``, ``"result"``.
        target_kind (str | None):
            ``"tile"`` if the current target is a Tiled tile property,
            or ``None`` when idle.
        target_tile (tuple | None): ``(tile_x, tile_y)`` of the
            gatherable tile being targeted, or ``None`` when idle.
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
        # Per-*cluster* regrow timers. Key is (cluster_idx, gather_type);
        # value is the seconds remaining until the cluster can be
        # gathered again. Decremented by :py:meth:`_tick_cooldowns`.
        # The whole cluster (a connected group of gatherable tiles)
        # regrows at once, not one tile at a time.
        self.gather_cooldowns: dict[tuple[int, str], float] = {}
        # Cluster cache. Built lazily by :py:meth:`_ensure_clusters_built`
        # when the controller first needs to look at cluster information
        # for a (map, gather_type) pair. Caches are invalidated when the
        # underlying :class:`pytmx.TiledMap` object changes (i.e. the
        # player moved to a different map).
        self._clusters_built_for: Optional[tuple] = None
        self.gatherable_tiles: set[tuple[int, int]] = set()
        self.tile_clusters: list[frozenset[tuple[int, int]]] = []
        self.tile_to_cluster: dict[tuple[int, int], int] = {}
        # The cluster_idx the current gather is targeting. ``None`` when
        # idle. Set by :py:meth:`start`, consumed by
        # :py:meth:`_finish_success` to mark the cluster on cooldown.
        self.target_cluster_idx: Optional[int] = None

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
    def _tile_property_at(self, world_pos: pygame.Vector2, prop_names) -> bool:
        """Return ``True`` if the tile at ``world_pos`` has any of the given
        custom tile properties set to a truthy value.

        ``prop_names`` may be a single string or a tuple of strings; all
        are checked (so legacy ``choppable`` / ``minable`` names still
        work alongside the newer ``is_*_gatherable`` ones).
        """
        if isinstance(prop_names, str):
            prop_names = (prop_names,)
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
                if not tile_props:
                    continue
                for prop_name in prop_names:
                    if tile_props.get(prop_name):
                        return True
        except Exception:
            return False
        return False

    def _gather_type_prop_names(self, gather_type: str):
        """Return all tile-property names (primary + fallbacks) that
        mark a tile as gatherable for ``gather_type``.
        """
        primary = GATHER_TILE_PROPERTY.get(gather_type)
        fallbacks = GATHER_TILE_PROPERTY_FALLBACK.get(gather_type, ())
        names = []
        if primary:
            names.append(primary)
        for name in fallbacks:
            if name not in names:
                names.append(name)
        return tuple(names)

    def _find_target_tile(self, gather_type: str, range_tiles: int = TILE_SEARCH_RANGE,
                           include_cooldown: bool = False):
        """Scan the tiles in a small square around the player for a
        gatherable *cluster* whose tile property matches the tool's
        gather type. Returns
        ``(tile_x, tile_y, world_pos, yield_item_id, cluster_idx)`` or
        ``None``.

        The return tuple is shaped as follows:

        * ``tile_x``, ``tile_y`` -- coordinates of the cluster's
          *representative* tile, i.e. the gatherable tile closest to
          the player in tile-space. Used for log messages and as a
          stable identifier within the cluster.
        * ``world_pos`` -- the cluster's *centroid* in world pixels
          (average of member tiles' world centres). UI code renders
          the "Press G to ..." prompt at this point so it sits over
          the visual centre of a multi-tile tree/rock rather than
          off to one side.
        * ``yield_item_id`` -- the resource id this gather type drops
          (e.g. ``"wood"`` -> ``"wood"``).
        * ``cluster_idx`` -- the index into
          :py:attr:`tile_clusters`. Persisted on the controller as
          :py:attr:`target_cluster_idx` and used to mark the entire
          cluster on cooldown on success.

        Clusters currently on regrow cooldown are skipped by default
        (so the player can't immediately re-gather the same tree).
        Pass ``include_cooldown=True`` to return them anyway -- the
        UI uses this to render a "Regrowing (Xs)" hint over the
        cluster.
        """
        prop_names = self._gather_type_prop_names(gather_type)
        if not prop_names:
            return None
        try:
            tmx_map = self.game.map.current_map
            tmx = getattr(tmx_map, "tmxdata", None) or getattr(tmx_map, "get_tmx_data", lambda: None)()
            if not tmx:
                return None
            self._ensure_clusters_built(gather_type)
            center = self.game.character.get_center()
            cx = int(center.x // tmx.tilewidth)
            cy = int(center.y // tmx.tileheight)
            best_dist = None
            best_cluster_idx: Optional[int] = None
            best_rep_tx: Optional[int] = None
            best_rep_ty: Optional[int] = None
            seen_clusters: set[int] = set()
            for dy in range(-range_tiles, range_tiles + 1):
                for dx in range(-range_tiles, range_tiles + 1):
                    if dx == 0 and dy == 0:
                        continue
                    tx, ty = cx + dx, cy + dy
                    cluster_idx = self.tile_to_cluster.get((tx, ty))
                    if cluster_idx is None or cluster_idx in seen_clusters:
                        continue
                    seen_clusters.add(cluster_idx)
                    if not include_cooldown and self._cluster_on_cooldown(cluster_idx, gather_type):
                        continue
                    dist = (dx * dx + dy * dy) ** 0.5
                    if best_dist is None or dist < best_dist:
                        best_dist = dist
                        best_cluster_idx = cluster_idx
                        best_rep_tx = tx
                        best_rep_ty = ty
            if best_cluster_idx is None or best_dist is None:
                return None
            centroid = self._cluster_center_world_pos(best_cluster_idx, gather_type)
            if centroid is None:
                # Fall back to the representative tile's centre if the
                # centroid can't be computed (e.g. map unloaded).
                centroid = pygame.Vector2(
                    (best_rep_tx or 0) * tmx.tilewidth + tmx.tilewidth // 2,
                    (best_rep_ty or 0) * tmx.tileheight + tmx.tileheight // 2,
                )
            yield_id = GATHER_DEFAULT_YIELD.get(gather_type, "wood")
            return best_rep_tx, best_rep_ty, centroid, yield_id, best_cluster_idx
        except Exception:
            return None

    def _find_cooldown_tile(self, gather_type: str, range_tiles: int = TILE_SEARCH_RANGE):
        """Return the closest gatherable *cluster* that is currently
        on regrow cooldown, used for the "Regrowing (Xs)" hint.

        Returns ``(tx, ty, world_pos, gather_type, cluster_idx, remaining)``
        or ``None``. ``tx``, ``ty`` is the cluster's representative
        tile (the gatherable tile closest to the player);
        ``world_pos`` is the cluster's centroid; ``cluster_idx`` is
        the cluster index; ``remaining`` is the seconds left on the
        regrow cooldown.
        """
        prop_names = self._gather_type_prop_names(gather_type)
        if not prop_names:
            return None
        try:
            tmx_map = self.game.map.current_map
            tmx = getattr(tmx_map, "tmxdata", None) or getattr(tmx_map, "get_tmx_data", lambda: None)()
            if not tmx:
                return None
            self._ensure_clusters_built(gather_type)
            center = self.game.character.get_center()
            cx = int(center.x // tmx.tilewidth)
            cy = int(center.y // tmx.tileheight)
            best_dist = None
            best_cluster_idx: Optional[int] = None
            best_rep_tx: Optional[int] = None
            best_rep_ty: Optional[int] = None
            best_remaining = 0.0
            seen_clusters: set[int] = set()
            for dy in range(-range_tiles, range_tiles + 1):
                for dx in range(-range_tiles, range_tiles + 1):
                    if dx == 0 and dy == 0:
                        continue
                    tx, ty = cx + dx, cy + dy
                    cluster_idx = self.tile_to_cluster.get((tx, ty))
                    if cluster_idx is None or cluster_idx in seen_clusters:
                        continue
                    seen_clusters.add(cluster_idx)
                    remaining = self._cluster_cooldown_remaining(cluster_idx, gather_type)
                    if remaining <= 0.0:
                        continue
                    dist = (dx * dx + dy * dy) ** 0.5
                    if best_dist is None or dist < best_dist:
                        best_dist = dist
                        best_cluster_idx = cluster_idx
                        best_rep_tx = tx
                        best_rep_ty = ty
                        best_remaining = remaining
            if best_cluster_idx is None or best_dist is None:
                return None
            centroid = self._cluster_center_world_pos(best_cluster_idx, gather_type)
            if centroid is None:
                centroid = pygame.Vector2(
                    (best_rep_tx or 0) * tmx.tilewidth + tmx.tilewidth // 2,
                    (best_rep_ty or 0) * tmx.tileheight + tmx.tileheight // 2,
                )
            return best_rep_tx, best_rep_ty, centroid, gather_type, best_cluster_idx, best_remaining
        except Exception:
            return None

    def get_nearest_gatherable(self):
        """Public helper used by the UI to render the press-G prompt.

        Returns either:

        * ``(tile_target_tuple, gather_type)`` for a Tiled tile
          property target that is **not** on regrow cooldown;
        * ``(cooldown_tuple, gather_type)`` -- where ``cooldown_tuple``
          is ``(tx, ty, world_pos, gather_type, seconds_remaining)``
          -- for the nearest gatherable tile that *is* currently on
          cooldown (the UI renders a "Regrowing (Xs)" prompt for
          these);
        * ``None`` when no tool is equipped, no gatherable tile is
          adjacent to the player, and no cooldown tiles are nearby.
        """
        tool = self._get_active_tool()
        if not tool:
            return None
        gather_type = tool.gather_type
        tile = self._find_target_tile(gather_type)
        if tile is not None:
            return (tile, gather_type)
        # No ready tile -- surface a "Regrowing" prompt instead so the
        # player understands why the hint isn't an actionable "Press G".
        cooldown_tile = self._find_cooldown_tile(gather_type)
        if cooldown_tile is not None:
            return (cooldown_tile, gather_type)
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
            logger.debug(f"gather.start: rejected, state={self.state}")
            return False
        tool = self._get_active_tool()
        if not tool:
            logger.debug("gather.start: rejected, no active tool")
            return False
        gather_type = tool.gather_type

        tile = self._find_target_tile(gather_type)
        if tile is None:
            logger.debug(f"gather.start: rejected, no {gather_type} tile adjacent")
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

        self.target_kind = "tile"
        tx, ty, _world_pos, yield_id, cluster_idx = tile
        self.target_tile = (tx, ty)
        self.target_cluster_idx = cluster_idx
        self.target_yield_item_id = yield_id

        self.state = "active"
        cluster_size = len(self.tile_clusters[cluster_idx]) if 0 <= cluster_idx < len(self.tile_clusters) else 1
        logger.info(
            f"Gather started: type={gather_type} tile=({tx},{ty}) "
            f"cluster={cluster_idx} size={cluster_size} "
            f"tool={getattr(tool, 'item_id', '?')} power={self.power} "
            f"time={self.gather_time:.2f}s"
        )
        return True

    def cancel(self) -> None:
        """Abort an active gathering attempt."""
        if self.state == "active":
            logger.debug(
                f"gather.cancel: was active for {getattr(self, 'target_gather_type', '?')}"
            )
            self.state = "idle"
            self.target_kind = None
            self.target_tile = None
            self.target_cluster_idx = None
            self.target_gather_type = None
            self.target_yield_item_id = None
            self.fill = 0.0
            self.result = GatheringResult("Cancelled", success=False, duration=1.0)

    def _finish_success(self) -> None:
        """Award the gathered resources, wear down the tool, and reset.

        Resources are added **directly to the player's inventory** via
        :class:`src.inventory.system.CraftingLogic.add_crafted_item` --
        no world drop is spawned.
        """
        yield_id = self.target_yield_item_id
        lo = self.target_yield_min
        hi = self.target_yield_max
        amount = random.randint(lo, hi) if hi > lo else lo
        added = 0
        if amount > 0 and yield_id:
            try:
                item_obj = create_item(yield_id)
            except Exception:
                item_obj = None
            if item_obj is not None:
                added = self._add_to_inventory(item_obj, amount)

        if added > 0:
            nice_name = yield_id.replace("_", " ").title()
            self.result = GatheringResult(f"+{added} {nice_name}", success=True, duration=1.8)
        else:
            self.result = GatheringResult("Got nothing...", success=False, duration=1.2)

        # Mark the just-gathered *cluster* as on regrow cooldown so the
        # same tree/rock can't be re-gathered for GATHER_COOLDOWN_DURATION.
        # The whole cluster regrows at once (every tile in it) so a 6-tile
        # tree behaves as one resource node rather than 6 independent ones.
        if self.target_cluster_idx is not None and self.target_gather_type is not None:
            self._mark_cluster_cooldown(self.target_cluster_idx, self.target_gather_type)
            cluster_size = (
                len(self.tile_clusters[self.target_cluster_idx])
                if 0 <= self.target_cluster_idx < len(self.tile_clusters)
                else 1
            )
            logger.info(
                f"Gather finished: cluster={self.target_cluster_idx} "
                f"size={cluster_size} type={self.target_gather_type} "
                f"cooldown={GATHER_COOLDOWN_DURATION:.0f}s"
            )

        self._damage_tool()
        self._reset_target()

    def _add_to_inventory(self, item_obj, amount: int) -> int:
        """Add ``amount`` of ``item_obj`` straight to the player's
        inventory. Returns the number of items actually stored.

        :class:`src.inventory.system.CraftingLogic.add_crafted_item`
        is an all-or-nothing helper, so when the inventory is full the
        full amount is spawned as a single :class:`DroppedItem` at the
        player's feet instead of being lost.
        """
        if amount <= 0 or item_obj is None:
            return 0
        try:
            from src.inventory.system import CraftingLogic
            player_inv = getattr(self.game, "MAIN_player_inv", None)
            if player_inv is None:
                raise RuntimeError("player inventory not available")
            if CraftingLogic.add_crafted_item(player_inv, item_obj, amount):
                return amount
        except Exception:
            pass

        try:
            base_x, base_y = self.game.character.get_rect().center
            from src.entities.dropped_item import DroppedItem
            drop = DroppedItem(base_x + random.randint(-12, 12),
                               base_y + random.randint(-6, 6),
                               item_obj, amount)
            self.game.items.append(drop)
            return amount
        except Exception:
            return 0

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
        self.target_tile = None
        self.target_cluster_idx = None
        self.target_gather_type = None
        self.target_yield_item_id = None
        self.fill = 0.0
        self.power = 0

    # ------------------------------------------------------------------
    # Cluster detection
    # ------------------------------------------------------------------
    def _ensure_clusters_built(self, gather_type: str) -> None:
        """Build (or rebuild) the cluster index for the current map and
        ``gather_type`` if it isn't already cached.

        A cluster is a set of gatherable tiles that are orthogonally
        connected (4-way BFS). Building is a single full-map scan; the
        result is cached by ``(id(tmx_map), gather_type)`` so it's only
        recomputed when the player moves to a different map.

        On exit:

        * :py:attr:`gatherable_tiles` is the set of all tiles on the
          current map that match the gather type's tile property.
        * :py:attr:`tile_clusters` is a list of
          ``frozenset[(tx, ty), ...]`` -- one entry per cluster, in
          discovery order. The integer index of a cluster is stable
          for the lifetime of the cache.
        * :py:attr:`tile_to_cluster` is a ``(tx, ty) -> cluster_idx``
          lookup built from the cluster list.
        """
        try:
            tmx_map = self.game.map.current_map
            tmx = getattr(tmx_map, "tmxdata", None) or getattr(tmx_map, "get_tmx_data", lambda: None)()
        except Exception:
            tmx = None
        cache_key = (id(tmx) if tmx is not None else None, gather_type)
        if self._clusters_built_for == cache_key:
            return

        self.gatherable_tiles = set()
        self.tile_clusters = []
        self.tile_to_cluster = {}

        if tmx is None:
            self._clusters_built_for = cache_key
            return

        prop_names = self._gather_type_prop_names(gather_type)
        if not prop_names:
            self._clusters_built_for = cache_key
            return

        # First pass: find every gatherable tile on the map.
        gatherable: set[tuple[int, int]] = set()
        for ty in range(tmx.height):
            for tx in range(tmx.width):
                world_pos = pygame.Vector2(
                    tx * tmx.tilewidth + tmx.tilewidth // 2,
                    ty * tmx.tileheight + tmx.tileheight // 2,
                )
                if self._tile_property_at(world_pos, prop_names):
                    gatherable.add((tx, ty))

        # Second pass: 4-way BFS flood fill, groups connected tiles
        # into clusters. Order of discovery is the order of iteration
        # over ``gatherable`` (which is sorted implicitly by the
        # nested loop above).
        if GATHER_CLUSTER_ADJACENCY == 4:
            neighbours = ((1, 0), (-1, 0), (0, 1), (0, -1))
        elif GATHER_CLUSTER_ADJACENCY == 8:
            neighbours = (
                (1, 0), (-1, 0), (0, 1), (0, -1),
                (1, 1), (1, -1), (-1, 1), (-1, -1),
            )
        else:
            neighbours = ((1, 0), (-1, 0), (0, 1), (0, -1))

        visited: set[tuple[int, int]] = set()
        clusters: list[frozenset[tuple[int, int]]] = []
        for start in sorted(gatherable):
            if start in visited:
                continue
            cluster: set[tuple[int, int]] = set()
            queue: list[tuple[int, int]] = [start]
            visited.add(start)
            cluster.add(start)
            while queue:
                cur = queue.pop()
                for dx, dy in neighbours:
                    n = (cur[0] + dx, cur[1] + dy)
                    if n in gatherable and n not in visited:
                        visited.add(n)
                        cluster.add(n)
                        queue.append(n)
            clusters.append(frozenset(cluster))

        tile_to_cluster: dict[tuple[int, int], int] = {}
        for idx, cluster in enumerate(clusters):
            for tile in cluster:
                tile_to_cluster[tile] = idx

        self.gatherable_tiles = gatherable
        self.tile_clusters = clusters
        self.tile_to_cluster = tile_to_cluster
        self._clusters_built_for = cache_key
        logger.info(
            f"Gather clusters built: type={gather_type} "
            f"tiles={len(gatherable)} clusters={len(clusters)}"
        )

    def _cluster_for_tile(self, tx: int, ty: int, gather_type: str) -> Optional[int]:
        """Return the cluster index containing ``(tx, ty)``, or ``None``."""
        self._ensure_clusters_built(gather_type)
        return self.tile_to_cluster.get((tx, ty))

    def _cluster_center_world_pos(self, cluster_idx: int, gather_type: str) -> Optional[pygame.Vector2]:
        """Return the world-space centroid of ``cluster_idx`` -- the
        average of the world-space centres of all its tiles. Used to
        anchor the press-G / regrowing hint over the visual centre of
        a multi-tile tree or rock.
        """
        self._ensure_clusters_built(gather_type)
        if cluster_idx < 0 or cluster_idx >= len(self.tile_clusters):
            return None
        cluster = self.tile_clusters[cluster_idx]
        if not cluster:
            return None
        try:
            tmx_map = self.game.map.current_map
            tmx = getattr(tmx_map, "tmxdata", None) or getattr(tmx_map, "get_tmx_data", lambda: None)()
        except Exception:
            tmx = None
        if tmx is None:
            return None
        tw, th = tmx.tilewidth, tmx.tileheight
        sum_x = 0.0
        sum_y = 0.0
        for tx, ty in cluster:
            sum_x += tx * tw + tw / 2.0
            sum_y += ty * th + th / 2.0
        n = len(cluster)
        return pygame.Vector2(sum_x / n, sum_y / n)

    # ------------------------------------------------------------------
    # Per-cluster gather cooldowns
    # ------------------------------------------------------------------
    def _cluster_on_cooldown(self, cluster_idx: int, gather_type: str) -> bool:
        return self.gather_cooldowns.get((cluster_idx, gather_type), 0.0) > 0.0

    def _cluster_cooldown_remaining(self, cluster_idx: int, gather_type: str) -> float:
        return max(0.0, self.gather_cooldowns.get((cluster_idx, gather_type), 0.0))

    def _mark_cluster_cooldown(self, cluster_idx: int, gather_type: str) -> None:
        self.gather_cooldowns[(cluster_idx, gather_type)] = GATHER_COOLDOWN_DURATION

    def _tick_cooldowns(self, dt: float) -> None:
        if not self.gather_cooldowns or dt <= 0.0:
            return
        expired = []
        for key, remaining in self.gather_cooldowns.items():
            new_remaining = remaining - dt
            if new_remaining <= 0.0:
                expired.append(key)
            else:
                self.gather_cooldowns[key] = new_remaining
        for key in expired:
            del self.gather_cooldowns[key]

    # ------------------------------------------------------------------
    # Per-frame update / event / draw
    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        if self.result and self.result.alive:
            self.result.update(dt)

        self._tick_cooldowns(dt)

        if self.state != "active":
            return

        # Abort if the tool is no longer active (e.g. player swapped
        # hotbar slots, or the tool's durability hit zero).
        tool = self._get_active_tool()
        if not tool or tool.gather_type != self.target_gather_type:
            self.cancel()
            return

        # Tick the progress bar.
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
