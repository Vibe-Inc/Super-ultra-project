from __future__ import annotations

from functools import lru_cache

import pygame


def build_monster_animations(style: str, size: tuple[int, int]) -> dict[str, list[pygame.Surface]]:
    return _build_monster_animations_cached((style or "").lower(), tuple(size))


@lru_cache(maxsize=16)
def _build_monster_animations_cached(style: str, size: tuple[int, int]) -> dict[str, list[pygame.Surface]]:
    palette = _palette_for(style)
    offsets = [0, 1, 0, -1]

    animations: dict[str, list[pygame.Surface]] = {
        "down": [],
        "up": [],
        "side": [],
    }

    for offset in offsets:
        animations["down"].append(_make_frame(size, palette, "down", offset))
        animations["up"].append(_make_frame(size, palette, "up", offset))
        animations["side"].append(_make_frame(size, palette, "side", offset))

    return animations


def _palette_for(style: str) -> dict[str, tuple[int, int, int]]:
    palettes = {
        "brute": {
            "body": (120, 70, 45),
            "accent": (170, 110, 75),
            "eye": (240, 220, 180),
            "mark": (80, 40, 25),
        },
        "venomous": {
            "body": (45, 120, 70),
            "accent": (60, 170, 90),
            "eye": (230, 250, 140),
            "mark": (20, 70, 40),
        },
        "arcanist": {
            "body": (40, 80, 140),
            "accent": (100, 150, 210),
            "eye": (230, 240, 255),
            "mark": (25, 45, 85),
        },
        "trickster": {
            "body": (140, 50, 60),
            "accent": (210, 110, 120),
            "eye": (245, 230, 210),
            "mark": (70, 20, 30),
        },
        "bomber": {
            "body": (140, 95, 40),
            "accent": (210, 160, 90),
            "eye": (250, 230, 190),
            "mark": (80, 50, 20),
        },
    }
    return palettes.get(style, palettes["brute"])


def _make_frame(
    size: tuple[int, int],
    palette: dict[str, tuple[int, int, int]],
    direction: str,
    bob_offset: int,
) -> pygame.Surface:
    width, height = size
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    body_w = int(width * 0.62)
    body_h = int(height * 0.5)
    body_x = (width - body_w) // 2
    body_y = int(height * 0.33) + bob_offset

    head_r = int(width * 0.18)
    head_x = width // 2
    head_y = int(height * 0.25) + bob_offset

    pygame.draw.rect(surface, palette["body"], (body_x, body_y, body_w, body_h), border_radius=8)
    pygame.draw.circle(surface, palette["body"], (head_x, head_y), head_r)

    if direction == "side":
        horn = [(head_x + head_r - 2, head_y - 2), (head_x + head_r + 12, head_y - 8), (head_x + head_r, head_y + 6)]
        pygame.draw.polygon(surface, palette["accent"], horn)
    else:
        horn_left = [(head_x - head_r + 2, head_y - 2), (head_x - head_r - 10, head_y - 8), (head_x - head_r + 2, head_y + 6)]
        horn_right = [(head_x + head_r - 2, head_y - 2), (head_x + head_r + 10, head_y - 8), (head_x + head_r - 2, head_y + 6)]
        pygame.draw.polygon(surface, palette["accent"], horn_left)
        pygame.draw.polygon(surface, palette["accent"], horn_right)

    eye_offset = 6 if direction == "side" else 10
    pygame.draw.circle(surface, palette["eye"], (head_x + eye_offset, head_y + 2), 3)
    pygame.draw.circle(surface, palette["eye"], (head_x - eye_offset, head_y + 2), 3)

    mark_y = body_y + int(body_h * 0.55)
    pygame.draw.rect(surface, palette["mark"], (body_x + 6, mark_y, body_w - 12, 6), border_radius=3)

    return surface
