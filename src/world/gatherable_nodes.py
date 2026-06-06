"""Coordinate-based gatherable nodes (trees, rocks, ore veins).

The :mod:`src.minigames.gathering` controller historically only looked
for gatherable tiles via the ``choppable`` / ``minable`` custom
properties of Tiled map tiles. This module adds a complementary,
**Python-driven** registry so designers (and the project's main
``ideas.md`` roadmap) can place gatherable objects at exact world
coordinates without touching any ``.tmx`` file.

A :class:`GatherableNode` represents a single object in the world:

* a tree (produces ``wood``)
* a rock (produces ``stone``)
* an ore vein (produces ``iron_ore``)

Each node has a pixel position, a hit radius, a yield item, and a
respawn timer. When gathered successfully, the node is marked
"depleted" and disappears for ``respawn_time`` seconds before
reappearing, giving the world a natural "resource regen" feel.

Nodes are organised per-map by :class:`GatherableNodeRegistry`, which
the :class:`src.core.game.Game` owns. The :class:`GatheringController`
queries the active registry on ``G`` to find the nearest valid node.
"""

from __future__ import annotations

import math
import os
import pygame
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.core.logger import logger

# Default sprites for nodes. Loaded once and shared across all nodes of
# the same kind to keep memory use down. Designers can override per-node
# by setting ``image_path`` in the data file.
DEFAULT_SPRITE_PATHS: Dict[str, str] = {
    "wood":  "assets/world/tree.png",
    "stone": "assets/world/rock.png",
    "ore":   "assets/world/ore_vein.png",
}

# Fallback procedural sprite colors when an asset isn't present. Keeps
# the system working even if a particular PNG hasn't been drawn yet.
FALLBACK_COLORS: Dict[str, Tuple[int, int, int]] = {
    "wood":  (66, 130, 60),
    "stone": (140, 140, 150),
    "ore":   (200, 130, 60),
}

DEFAULT_HIT_RADIUS = 64.0
DEFAULT_RESPAWN_TIME = 12.0


@dataclass
class GatherableNodeDef:
    """Raw, JSON/Python-friendly description of a single node.

    Used by the data file the user edits (see
    ``data/gatherable_nodes.py``). At registry-build time each def is
    converted to a live :class:`GatherableNode`.
    """

    map_path: str
    gather_type: str
    x: float
    y: float
    yield_item_id: str = ""
    hit_radius: float = DEFAULT_HIT_RADIUS
    respawn_time: float = DEFAULT_RESPAWN_TIME
    image_path: str = ""


class GatherableNode:
    """A live gatherable object in the world.

    Attributes:
        gather_type (str):
            Resource category: ``"wood"``, ``"stone"`` or ``"ore"``.
        pos (pygame.Vector2):
            World-space pixel position of the node's center.
        hit_radius (float):
            Pixel radius within which the player can interact with the
            node. Default is 64 pixels (~2 tiles for a 32 px tileset).
        yield_item_id (str):
            Item id spawned on a successful gather (``"wood"``,
            ``"stone"``, ``"iron_ore"``, ...).
        respawn_time (float):
            Seconds the node stays depleted after a successful gather
            before it reappears.
        depleted (bool):
            ``True`` while the node is waiting to respawn. A depleted
            node is invisible, non-interactive, and ignored by
            targeting queries.
        respawn_timer (float):
            Seconds remaining until ``depleted`` flips back to
            ``False``.
        image (pygame.Surface | None):
            Cached sprite surface, lazily loaded on first draw.
        image_path (str):
            Asset path the sprite was loaded from, or empty when a
            procedural fallback is used.
    """

    def __init__(
        self,
        gather_type: str,
        x: float,
        y: float,
        yield_item_id: str = "",
        hit_radius: float = DEFAULT_HIT_RADIUS,
        respawn_time: float = DEFAULT_RESPAWN_TIME,
        image_path: str = "",
    ):
        self.gather_type = gather_type
        self.pos = pygame.Vector2(float(x), float(y))
        self.hit_radius = float(hit_radius)
        self.yield_item_id = yield_item_id or _default_yield_for(gather_type)
        self.respawn_time = float(respawn_time)
        self.depleted = False
        self.respawn_timer = 0.0
        self.image: Optional[pygame.Surface] = None
        self.image_path = image_path or DEFAULT_SPRITE_PATHS.get(gather_type, "")
        self._fallback_size = 48
        self._image_size = 0

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------
    def deplete(self) -> None:
        """Mark the node as just-gathered and start its respawn timer."""
        self.depleted = True
        self.respawn_timer = self.respawn_time

    def update(self, dt: float) -> None:
        if not self.depleted:
            return
        self.respawn_timer = max(0.0, self.respawn_timer - dt)
        if self.respawn_timer <= 0.0:
            self.depleted = False
            self.respawn_timer = 0.0

    # ------------------------------------------------------------------
    # Geometry / queries
    # ------------------------------------------------------------------
    def contains(self, world_pos: pygame.Vector2) -> bool:
        """Return ``True`` if ``world_pos`` is within ``hit_radius``."""
        if self.depleted:
            return False
        dx = world_pos.x - self.pos.x
        dy = world_pos.y - self.pos.y
        return (dx * dx + dy * dy) <= (self.hit_radius * self.hit_radius)

    def distance_to(self, world_pos: pygame.Vector2) -> float:
        dx = world_pos.x - self.pos.x
        dy = world_pos.y - self.pos.y
        return math.sqrt(dx * dx + dy * dy)

    def rect(self) -> pygame.Rect:
        """Return a square ``pygame.Rect`` centered on the node."""
        r = int(self.hit_radius)
        return pygame.Rect(int(self.pos.x) - r, int(self.pos.y) - r, r * 2, r * 2)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _ensure_image(self) -> None:
        if self.image is not None:
            return
        loaded = False
        if self.image_path:
            try:
                abs_path = self.image_path
                if not os.path.isabs(abs_path):
                    project_root = os.path.dirname(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    )
                    abs_path = os.path.join(project_root, self.image_path)
                if os.path.exists(abs_path):
                    self.image = pygame.image.load(abs_path).convert_alpha()
                    self._image_size = self.image.get_width()
                    loaded = True
            except Exception as exc:
                logger.warning(
                    f"Failed to load gatherable sprite '{self.image_path}': {exc}"
                )
        if not loaded:
            color = FALLBACK_COLORS.get(self.gather_type, (180, 180, 180))
            self.image = _make_fallback_sprite(self.gather_type, color, self._fallback_size)
            self._image_size = self._fallback_size

    def draw(self, screen: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        if self.depleted:
            return
        self._ensure_image()
        if self.image is None:
            return
        screen_pos = pygame.Vector2(
            self.pos.x - camera_offset.x,
            self.pos.y - camera_offset.y,
        )
        rect = self.image.get_rect(center=(int(screen_pos.x), int(screen_pos.y)))
        screen.blit(self.image, rect)


def _default_yield_for(gather_type: str) -> str:
    return {
        "wood":  "wood",
        "stone": "stone",
        "ore":   "iron_ore",
    }.get(gather_type, "wood")


def _make_fallback_sprite(gather_type: str, color: Tuple[int, int, int], size: int) -> pygame.Surface:
    """Procedurally draw a small tree/rock/ore-vein icon.

    Used when the corresponding asset PNG is missing so the gatherable
    system stays functional in development.
    """
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    if gather_type == "wood":
        trunk_color = (90, 60, 35)
        crown_color = color
        trunk_w = max(4, size // 6)
        trunk_h = size // 3
        trunk_rect = pygame.Rect(
            size // 2 - trunk_w // 2,
            size - trunk_h - 2,
            trunk_w,
            trunk_h,
        )
        pygame.draw.rect(surf, trunk_color, trunk_rect, border_radius=2)
        crown_radius = size // 2 - 2
        pygame.draw.circle(
            surf, crown_color,
            (size // 2, size // 2 - 2),
            crown_radius,
        )
        pygame.draw.circle(
            surf, (40, 90, 45),
            (size // 2, size // 2 - 2),
            crown_radius,
            max(1, size // 16),
        )
    elif gather_type == "ore":
        rock_color = (110, 110, 120)
        pygame.draw.polygon(
            surf, rock_color,
            [
                (size // 5, int(size * 0.7)),
                (size // 2, size // 5),
                (int(size * 0.85), int(size * 0.65)),
                (int(size * 0.75), int(size * 0.9)),
                (int(size * 0.2), int(size * 0.85)),
            ],
        )
        pygame.draw.polygon(
            surf, (60, 60, 70),
            [
                (size // 5, int(size * 0.7)),
                (size // 2, size // 3),
                (int(size * 0.85), int(size * 0.65)),
                (int(size * 0.75), int(size * 0.9)),
                (int(size * 0.2), int(size * 0.85)),
            ],
            max(1, size // 16),
        )
        for i, dot_pos in enumerate(
            [
                (int(size * 0.35), int(size * 0.55)),
                (int(size * 0.55), int(size * 0.45)),
                (int(size * 0.65), int(size * 0.6)),
                (int(size * 0.4), int(size * 0.7)),
            ]
        ):
            pygame.draw.circle(surf, color, dot_pos, max(2, size // 8))
    else:
        pygame.draw.circle(surf, color, (size // 2, size // 2), size // 2 - 2)
        pygame.draw.circle(
            surf, (90, 90, 100), (size // 2, size // 2), size // 2 - 2, max(1, size // 16)
        )
        pygame.draw.circle(surf, (170, 170, 180), (size // 2 - 4, size // 2 - 4), size // 8)
    return surf


class GatherableNodeRegistry:
    """Per-map container of :class:`GatherableNode` instances.

    The registry is owned by the :class:`src.core.game.Game` and is
    rebuilt when the active map changes, so each map's nodes live in
    their own container.

    Attributes:
        map_path (str):
            Path of the map this registry belongs to (e.g.
            ``"maps/test-map-1.tmx"``). Used as a lookup key.
        nodes (list[GatherableNode]):
            All live nodes on this map, in registration order.
    """

    def __init__(self, map_path: str):
        self.map_path = map_path
        self.nodes: List[GatherableNode] = []

    def add(self, node: GatherableNode) -> None:
        self.nodes.append(node)

    def add_def(self, definition: GatherableNodeDef) -> GatherableNode:
        node = GatherableNode(
            gather_type=definition.gather_type,
            x=definition.x,
            y=definition.y,
            yield_item_id=definition.yield_item_id,
            hit_radius=definition.hit_radius,
            respawn_time=definition.respawn_time,
            image_path=definition.image_path,
        )
        self.add(node)
        return node

    def update(self, dt: float) -> None:
        for node in self.nodes:
            node.update(dt)

    def find_nearest(
        self,
        world_pos: pygame.Vector2,
        gather_type: str,
        max_radius: Optional[float] = None,
    ) -> Optional[GatherableNode]:
        """Return the closest non-depleted node matching ``gather_type``,
        or ``None`` if nothing in range matches.
        """
        best: Optional[GatherableNode] = None
        best_dist = None
        max_sq = None if max_radius is None else max_radius * max_radius
        for node in self.nodes:
            if node.depleted:
                continue
            if node.gather_type != gather_type:
                continue
            if node.contains(world_pos):
                return node
            if max_sq is not None:
                dx = node.pos.x - world_pos.x
                dy = node.pos.y - world_pos.y
                if (dx * dx + dy * dy) > max_sq:
                    continue
            dist = node.distance_to(world_pos)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best = node
        return best

    def find_all_in_range(
        self,
        world_pos: pygame.Vector2,
        gather_type: str,
        max_radius: float,
    ) -> List[GatherableNode]:
        result: List[GatherableNode] = []
        max_sq = max_radius * max_radius
        for node in self.nodes:
            if node.depleted or node.gather_type != gather_type:
                continue
            dx = node.pos.x - world_pos.x
            dy = node.pos.y - world_pos.y
            if (dx * dx + dy * dy) <= max_sq:
                result.append(node)
        return result

    def draw(self, screen: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        for node in self.nodes:
            node.draw(screen, camera_offset)
