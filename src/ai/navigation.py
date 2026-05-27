from __future__ import annotations

import heapq
import math
import random
from typing import Iterable

import pygame


class NavGrid:
    def __init__(
        self,
        cols: int,
        rows: int,
        tile_width: int,
        tile_height: int,
        walkable: list[list[bool]],
        walkable_cells: list[tuple[int, int]],
        allow_diagonal: bool = True,
    ):
        self.cols = cols
        self.rows = rows
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.walkable = walkable
        self.walkable_cells = walkable_cells
        self.allow_diagonal = allow_diagonal

        self.world_width = cols * tile_width
        self.world_height = rows * tile_height
        self.world_rect = pygame.Rect(0, 0, self.world_width, self.world_height)

    @classmethod
    def from_tmx(cls, tmx_data, obstacles: list[pygame.Rect]) -> "NavGrid":
        tile_width = int(getattr(tmx_data, "tilewidth", 0))
        tile_height = int(getattr(tmx_data, "tileheight", 0))
        cols = int(getattr(tmx_data, "width", 0))
        rows = int(getattr(tmx_data, "height", 0))

        walkable = [[True for _ in range(cols)] for _ in range(rows)]
        walkable_cells: list[tuple[int, int]] = []

        for y in range(rows):
            for x in range(cols):
                cell_rect = pygame.Rect(x * tile_width, y * tile_height, tile_width, tile_height)
                blocked = False
                for wall in obstacles:
                    if cell_rect.colliderect(wall):
                        blocked = True
                        break
                walkable[y][x] = not blocked
                if not blocked:
                    walkable_cells.append((x, y))

        return cls(cols, rows, tile_width, tile_height, walkable, walkable_cells)

    def clamp_world(self, pos: pygame.Vector2) -> pygame.Vector2:
        x = min(max(pos.x, 0), self.world_width - 1)
        y = min(max(pos.y, 0), self.world_height - 1)
        return pygame.Vector2(x, y)

    def world_to_cell(self, pos: pygame.Vector2 | tuple[float, float]) -> tuple[int, int]:
        if not isinstance(pos, pygame.Vector2):
            pos = pygame.Vector2(pos)
        x = int(pos.x // self.tile_width)
        y = int(pos.y // self.tile_height)
        x = max(0, min(self.cols - 1, x))
        y = max(0, min(self.rows - 1, y))
        return x, y

    def cell_to_world(self, cell: tuple[int, int]) -> pygame.Vector2:
        x, y = cell
        return pygame.Vector2((x + 0.5) * self.tile_width, (y + 0.5) * self.tile_height)

    def in_bounds(self, cell: tuple[int, int]) -> bool:
        x, y = cell
        return 0 <= x < self.cols and 0 <= y < self.rows

    def is_walkable(self, cell: tuple[int, int]) -> bool:
        if not self.in_bounds(cell):
            return False
        x, y = cell
        return self.walkable[y][x]

    def random_world_position(self) -> pygame.Vector2 | None:
        if not self.walkable_cells:
            return None
        cell = random.choice(self.walkable_cells)
        return self.cell_to_world(cell)

    def find_path(
        self,
        start_world: pygame.Vector2 | tuple[float, float],
        goal_world: pygame.Vector2 | tuple[float, float],
    ) -> list[pygame.Vector2]:
        start_cell = self.world_to_cell(start_world)
        goal_cell = self.world_to_cell(goal_world)

        if start_cell == goal_cell:
            return []
        if not self.is_walkable(start_cell) or not self.is_walkable(goal_cell):
            return []

        open_heap: list[tuple[float, float, tuple[int, int]]] = []
        heapq.heappush(open_heap, (0.0, 0.0, start_cell))

        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start_cell: 0.0}

        while open_heap:
            _, current_g, current = heapq.heappop(open_heap)
            if current == goal_cell:
                break
            if current_g > g_score.get(current, math.inf):
                continue

            for neighbor, cost in self._neighbors(current):
                tentative = current_g + cost
                if tentative < g_score.get(neighbor, math.inf):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative
                    f_score = tentative + self._heuristic(neighbor, goal_cell)
                    heapq.heappush(open_heap, (f_score, tentative, neighbor))

        if goal_cell not in came_from:
            return []

        path: list[pygame.Vector2] = []
        current = goal_cell
        while current != start_cell:
            path.append(self.cell_to_world(current))
            current = came_from[current]
        path.reverse()
        return path

    def _neighbors(self, cell: tuple[int, int]) -> Iterable[tuple[tuple[int, int], float]]:
        x, y = cell
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        diag = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
        sqrt2 = 1.41421356237

        for dx, dy in directions:
            neighbor = (x + dx, y + dy)
            if self.is_walkable(neighbor):
                yield neighbor, 1.0

        if not self.allow_diagonal:
            return

        for dx, dy in diag:
            neighbor = (x + dx, y + dy)
            if not self.is_walkable(neighbor):
                continue
            if not (self.is_walkable((x + dx, y)) and self.is_walkable((x, y + dy))):
                continue
            yield neighbor, sqrt2

    @staticmethod
    def _heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        sqrt2 = 1.41421356237
        return (dx + dy) + (sqrt2 - 2.0) * min(dx, dy)
