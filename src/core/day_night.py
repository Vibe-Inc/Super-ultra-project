"""
Day-night cycle visuals for the game.

Smooth multi-stop color/brightness gradient with a soft vignette.
"""

import math
import pygame
import src.config as cfg


def _lerp_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def _sample_gradient(stops: list[tuple[float, tuple[int, int, int]]], position: float) -> tuple[int, int, int]:
    position = max(0.0, min(1.0, position))
    if len(stops) == 0:
        return (255, 255, 255)
    if len(stops) == 1:
        return stops[0][1]
    if position <= stops[0][0]:
        return stops[0][1]
    if position >= stops[-1][0]:
        return stops[-1][1]
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        if p0 <= position <= p1:
            seg_len = p1 - p0
            if seg_len <= 0:
                return c0
            t = (position - p0) / seg_len
            t = t * t * (3.0 - 2.0 * t)
            t = t * t * (3.0 - 2.0 * t)
            return _lerp_color(c0, c1, t)
    return stops[-1][1]


def _sample_scalar_gradient(stops: list[tuple[float, float]], position: float) -> float:
    position = max(0.0, min(1.0, position))
    if len(stops) == 0:
        return 1.0
    if len(stops) == 1:
        return stops[0][1]
    if position <= stops[0][0]:
        return stops[0][1]
    if position >= stops[-1][0]:
        return stops[-1][1]
    for i in range(len(stops) - 1):
        p0, v0 = stops[i]
        p1, v1 = stops[i + 1]
        if p0 <= position <= p1:
            seg_len = p1 - p0
            if seg_len <= 0:
                return v0
            t = (position - p0) / seg_len
            t = t * t * (3.0 - 2.0 * t)
            t = t * t * (3.0 - 2.0 * t)
            return v0 + (v1 - v0) * t
    return stops[-1][1]


# ---------------------------------------------------------------------------
# Gradient data
# ---------------------------------------------------------------------------

TINT_GRADIENT: list[tuple[float, tuple[int, int, int]]] = [
    (0.00, (12, 18, 50)),
    (0.10, (14, 20, 55)),
    (0.17, (18, 22, 58)),
    (0.21, (30, 24, 52)),
    (0.24, (65, 40, 48)),
    (0.27, (110, 75, 65)),
    (0.30, (160, 120, 85)),
    (0.34, (200, 170, 120)),
    (0.38, (225, 210, 175)),
    (0.44, (245, 240, 225)),
    (0.50, (255, 255, 255)),
    (0.56, (255, 255, 255)),
    (0.62, (250, 248, 240)),
    (0.68, (240, 225, 195)),
    (0.73, (215, 180, 135)),
    (0.76, (190, 135, 90)),
    (0.79, (140, 90, 80)),
    (0.82, (80, 55, 65)),
    (0.85, (45, 35, 58)),
    (0.88, (25, 25, 52)),
    (0.92, (16, 20, 48)),
    (0.96, (13, 18, 45)),
    (1.00, (12, 18, 50)),
]

BRIGHTNESS_GRADIENT: list[tuple[float, float]] = [
    (0.00, 0.12), (0.10, 0.13), (0.17, 0.15), (0.21, 0.22),
    (0.24, 0.35), (0.27, 0.50), (0.30, 0.65), (0.34, 0.82),
    (0.38, 0.92), (0.44, 0.98), (0.50, 1.00), (0.56, 1.00),
    (0.62, 0.98), (0.68, 0.94), (0.73, 0.85), (0.76, 0.72),
    (0.79, 0.55), (0.82, 0.38), (0.85, 0.25), (0.88, 0.18),
    (0.92, 0.14), (0.96, 0.12), (1.00, 0.12),
]


# ---------------------------------------------------------------------------
# Vignette
# ---------------------------------------------------------------------------

class _Vignette:
    def __init__(self):
        self._cache: dict[tuple[int, int, int], pygame.Surface] = {}

    def draw(self, screen: pygame.Surface, strength: float):
        if strength <= 0.01:
            return
        sw, sh = screen.get_size()
        cw = (sw + 3) // 4 * 4
        ch = (sh + 3) // 4 * 4
        key = (cw, ch, int(strength * 20))
        surf = self._cache.get(key)
        if surf is None:
            surf = self._build(cw, ch, strength)
            self._cache[key] = surf
            if len(self._cache) > 12:
                del self._cache[next(iter(self._cache))]
        screen.blit(surf, (0, 0))

    @staticmethod
    def _build(w: int, h: int, strength: float) -> pygame.Surface:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        max_dist = math.sqrt(cx * cx + cy * cy)
        for i in range(24):
            frac = i / 24
            radius = int((1.0 - frac) * max_dist)
            if radius <= 0:
                continue
            a = max(0, min(255, int(frac * frac * 80 * strength)))
            pygame.draw.circle(surf, (0, 0, 0, a), (cx, cy), radius)
        small = pygame.transform.smoothscale(surf, (max(1, w // 4), max(1, h // 4)))
        return pygame.transform.smoothscale(small, (w, h))


# ---------------------------------------------------------------------------
# Main controller
# ---------------------------------------------------------------------------

class DayNightVisuals:
    def __init__(self):
        self._elapsed = 0.0
        self._vignette = _Vignette()
        self._cached_tint = (255, 255, 255)
        self._cached_brightness = 1.0
        self._cached_night_factor = 0.0

    @property
    def tint(self) -> tuple[int, int, int]:
        return self._cached_tint

    @property
    def brightness(self) -> float:
        return self._cached_brightness

    def update(self, dt: float, game_time_seconds: float, game_day_seconds: int):
        self._elapsed += dt

        t = (game_time_seconds % game_day_seconds) / game_day_seconds

        self._cached_tint = _sample_gradient(TINT_GRADIENT, t)
        self._cached_brightness = _sample_scalar_gradient(BRIGHTNESS_GRADIENT, t)

        b = self._cached_brightness
        if b <= 0.20:
            self._cached_night_factor = 1.0
        elif b >= 0.75:
            self._cached_night_factor = 0.0
        else:
            self._cached_night_factor = 1.0 - (b - 0.20) / (0.75 - 0.20)
            self._cached_night_factor = max(0.0, min(1.0, self._cached_night_factor))

        cfg.ENVIRONMENT_BRIGHTNESS = self._cached_brightness
        cfg.ENVIRONMENT_TINT = self._cached_tint

    def draw(self, screen: pygame.Surface):
        vignette_strength = 0.06 + 0.18 * self._cached_night_factor
        self._vignette.draw(screen, vignette_strength)