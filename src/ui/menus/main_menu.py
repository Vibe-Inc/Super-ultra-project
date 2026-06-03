import math
import random
import pygame
import sys
from gettext import gettext as _
from typing import TYPE_CHECKING

from src.ui.menus.base import Menu
from src.ui.widgets import Button, Tooltip
import src.config as cfg
from src.core.logger import logger

if TYPE_CHECKING:
    from src.app import App

GOLD = (212, 175, 55)
GOLD_BRIGHT = (255, 215, 0)
GOLD_DARK = (160, 120, 30)
DARK_BG = (8, 6, 18)


def _ease_out_back(t):
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


def _ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def _ease_out_elastic(t):
    if t == 0 or t == 1:
        return t
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1


def _ease_in_quart(t):
    return t * t * t * t


class Star:
    def __init__(self, sw, sh):
        self.x = random.uniform(0, sw)
        self.y = random.uniform(0, sh)
        self.size = random.uniform(0.5, 2.8)
        self.base_alpha = random.randint(20, 200)
        self.twinkle_speed = random.uniform(0.4, 3.0)
        self.phase = random.uniform(0, 6.28)
        self.color = random.choice([
            (255, 255, 255),
            (255, 240, 200),
            (200, 220, 255),
            (255, 200, 180),
        ])

    def draw(self, surf, t):
        alpha = int(self.base_alpha * (0.5 + 0.5 * math.sin(t * self.twinkle_speed + self.phase)))
        alpha = max(0, min(255, alpha))
        if alpha < 5:
            return
        px = int(self.x)
        py = int(self.y)
        sz = max(1, self.size)
        if sz <= 1.5:
            surf.set_at((px, py), (*self.color, alpha))
        else:
            s = pygame.Surface((int(sz * 2), int(sz * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (int(sz), int(sz)), int(sz))
            surf.blit(s, (px - int(sz), py - int(sz)))


class LightRay:
    def __init__(self, sw, sh):
        self.sw = sw
        self.sh = sh
        self._reset()

    def _reset(self):
        self.y = random.uniform(0, self.sh)
        self.height = random.uniform(20, 80)
        self.speed = random.uniform(0.15, 0.4)
        self.phase = random.uniform(0, 6.28)
        self.amp = random.uniform(20, 60)
        self.alpha = random.randint(3, 12)
        self.width_factor = random.uniform(0.3, 0.8)

    def draw(self, surf, t):
        cy = self.y + math.sin(t * self.speed + self.phase) * self.amp
        h = self.height
        s = pygame.Surface((int(self.sw * self.width_factor), int(h)), pygame.SRCALPHA)
        for i in range(int(h)):
            ratio = 1.0 - abs(i - h / 2) / (h / 2)
            a = int(self.alpha * max(0, ratio) ** 2)
            if a < 1:
                continue
            c = (255, 230, 180, min(255, a))
            pygame.draw.line(s, c, (0, i), (s.get_width(), i))
        sx = int(self.sw * (1 - self.width_factor) * 0.5)
        surf.blit(s, (sx, int(cy - h / 2)))


class AmbientEmber:
    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        self._reset()

    def _reset(self):
        self.x = random.uniform(0, self.sw)
        self.y = random.uniform(self.sh, self.sh + 50)
        self.speed = random.uniform(15, 50)
        self.sway_amp = random.uniform(10, 40)
        self.sway_freq = random.uniform(0.5, 2.0)
        self.phase = random.uniform(0, 6.28)
        self.size = random.uniform(1.0, 3.5)
        self.alpha = random.randint(30, 120)
        self.color = random.choice([
            (255, 200, 80),
            (255, 180, 60),
            (255, 220, 100),
            (255, 160, 40),
            (200, 150, 255),
        ])

    def update(self, dt, t):
        self.y -= self.speed * dt
        self.x += math.sin(t * self.sway_freq + self.phase) * self.sway_amp * dt
        if self.y < -20 or self.x < -50 or self.x > self.sw + 50:
            self._reset()

    def draw(self, surf, t):
        a = int(self.alpha * (0.6 + 0.4 * math.sin(t * 1.5 + self.phase)))
        a = max(0, min(255, a))
        sz = self.size
        s = pygame.Surface((int(sz * 2 + 2), int(sz * 2 + 2)), pygame.SRCALPHA)
        for ri in range(int(sz), 0, -1):
            ratio = ri / sz
            ca = int(a * (1 - ratio))
            pygame.draw.circle(s, (*self.color, max(0, min(255, ca))),
                               (int(sz + 1), int(sz + 1)), ri)
        surf.blit(s, (int(self.x - sz), int(self.y - sz)))


class FloatingOrb:
    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        self._reset(True)

    def _reset(self, init=False):
        self.x = random.uniform(0, self.sw)
        self.y = random.uniform(0, self.sh) if init else random.uniform(self.sh, self.sh + 100)
        self.vx = random.uniform(-15, 15)
        self.vy = random.uniform(-40, -10)
        self.radius = random.randint(30, 90)
        self.hue_shift = random.uniform(-30, 30)
        self.phase = random.uniform(0, 6.28)
        self.freq = random.uniform(0.3, 1.0)
        self.alpha_base = random.randint(6, 22)
        self.color_variant = random.choice(['gold', 'purple', 'teal', 'crimson'])

    def _get_color(self, ri, r, a):
        if self.color_variant == 'gold':
            return (max(0, min(255, 210 + int(self.hue_shift))),
                    max(0, min(255, 175 + int(self.hue_shift * 0.5))),
                    max(0, min(255, 55 + int(self.hue_shift * 0.3))), a)
        elif self.color_variant == 'purple':
            return (max(0, min(255, 180 + int(self.hue_shift))),
                    max(0, min(255, 120 + int(self.hue_shift * 0.3))),
                    max(0, min(255, 220 + int(self.hue_shift))), a)
        elif self.color_variant == 'teal':
            return (max(0, min(255, 80 + int(self.hue_shift * 0.3))),
                    max(0, min(255, 200 + int(self.hue_shift))),
                    max(0, min(255, 200 + int(self.hue_shift))), a)
        else:
            return (max(0, min(255, 200 + int(self.hue_shift))),
                    max(0, min(255, 80 + int(self.hue_shift * 0.3))),
                    max(0, min(255, 80 + int(self.hue_shift * 0.3))), a)

    def update(self, dt, t):
        self.x += self.vx * dt + math.sin(t * 0.3 + self.phase) * 10 * dt
        self.y += self.vy * dt
        if self.y < -self.radius * 2 or self.x < -self.radius * 2 or self.x > self.sw + self.radius * 2:
            self._reset()

    def draw(self, surf, t):
        a = int(self.alpha_base * (0.5 + 0.5 * math.sin(t * self.freq + self.phase)))
        a = max(0, min(40, a))
        px = int(self.x)
        py = int(self.y)
        r = self.radius
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for ri in range(r, 0, -2):
            ratio = ri / r
            ca = int(a * (1 - ratio) ** 1.5)
            c = self._get_color(ri, r, ca)
            pygame.draw.circle(s, c, (r, r), ri)
        surf.blit(s, (px - r, py - r))


class LaunchBurst:
    def __init__(self, x, y, vx, vy, color, size, lt):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.size = size
        self.lt = self.max_lt = lt

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 40 * dt
        self.lt -= dt

    def draw(self, surf):
        if self.lt <= 0:
            return
        a = int(255 * (self.lt / self.max_lt))
        sz = max(1, int(self.size * (self.lt / self.max_lt)))
        c = (*self.color[:3], a)
        s = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, c, (sz, sz), sz)
        surf.blit(s, (int(self.x) - sz, int(self.y) - sz))


def _render_shimmer_text(font, text, base_color, t, intensity=0.15):
    tb = int(t * 6)
    ck = (id(font), text, base_color, tb)
    if not hasattr(_render_shimmer_text, '_cache'):
        _render_shimmer_text._cache = {}
    if ck in _render_shimmer_text._cache:
        return _render_shimmer_text._cache[ck]
    result = font.render(text, True, base_color)
    if intensity <= 0:
        return result
    w, h = result.get_size()
    shimmer_w = max(1, int(w * 0.2))
    band = pygame.Surface((shimmer_w, h), pygame.SRCALPHA)
    for sx in range(shimmer_w):
        ratio = 1.0 - abs(sx - shimmer_w // 2) / (shimmer_w // 2 + 1)
        a = int(60 * ratio * intensity / 0.15)
        pygame.draw.line(band, (*GOLD_BRIGHT, max(0, min(140, a))), (sx, 0), (sx, h))
    band_x = int((t * 180) % (w + shimmer_w)) - shimmer_w
    result.blit(band, (band_x, 0), special_flags=pygame.BLEND_RGBA_ADD)
    if len(_render_shimmer_text._cache) > 30:
        _render_shimmer_text._cache.clear()
    _render_shimmer_text._cache[ck] = result
    return result


class TitleSparkle:
    def __init__(self, x, y):
        self.x = x + random.uniform(-4, 4)
        self.y = y + random.uniform(-4, 4)
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-20, -5)
        self.life = 1.0
        self.max_life = random.uniform(0.4, 1.0)
        self.size = random.uniform(1, 3)
        angle = random.uniform(0, 6.28)
        self.color = (
            max(0, min(255, int(255))),
            max(0, min(255, int(200 + 55 * math.sin(angle)))),
            max(0, min(255, int(140 + 80 * math.cos(angle)))),
        )

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 15 * dt
        self.life -= dt / self.max_life

    def draw(self, surf):
        if self.life <= 0:
            return
        a = int(255 * self.life)
        sz = max(0.5, self.size * self.life)
        s = pygame.Surface((int(sz * 2 + 2), int(sz * 2 + 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, max(0, min(255, a))), (int(sz + 1), int(sz + 1)), int(sz))
        surf.blit(s, (int(self.x - sz), int(self.y - sz)))


class MainMenu(Menu):
    def __init__(self, app: "App"):
        super().__init__(app)

        scale = cfg.ui_scale()
        button_width, button_height = max(1, int(380 * scale)), max(1, int(110 * scale))
        gap = max(4, int(60 * scale))
        tot_width = 2 * button_width + gap
        center_x = cfg.SCREEN_WIDTH // 2

        shield = 'shield'

        start_rect = pygame.Rect(center_x - tot_width // 2, int(650 * scale), button_width, button_height)
        exit_rect = pygame.Rect(center_x - tot_width // 2 + button_width + gap, int(650 * scale), button_width, button_height)
        settings_rect = pygame.Rect(center_x - tot_width // 2, int(800 * scale), button_width, button_height)
        credits_rect = pygame.Rect(center_x - tot_width // 2 + button_width + gap, int(800 * scale), button_width, button_height)
        load_rect = pygame.Rect(center_x - button_width // 2, int(520 * scale), button_width, button_height)

        self.buttons = [
            Button(start_rect, _("START"), cfg.button_color_START,
                   cfg.button_hover_color_START, cfg.button_font,
                   cfg.text_color, cfg.corner_radius, on_click=self.start_game, shape=shield),
            Button(load_rect, _("LOAD"), cfg.button_color_SETTINGS,
                   cfg.button_hover_color_SETTINGS, cfg.button_font,
                   cfg.text_color, cfg.corner_radius, on_click=self.open_load_menu, shape=shield),
            Button(exit_rect, _("EXIT"), cfg.button_color_EXIT,
                   cfg.button_hover_color_EXIT, cfg.button_font,
                   cfg.text_color, cfg.corner_radius, on_click=self.exit_game, shape=shield),
            Button(settings_rect, _("SETTINGS"), cfg.button_color_SETTINGS,
                   cfg.button_hover_color_SETTINGS, cfg.button_font,
                   cfg.text_color, cfg.corner_radius, on_click=self.open_settings, shape=shield),
            Button(credits_rect, _("CREDITS"), cfg.button_color_CREDITS,
                   cfg.button_hover_color_CREDITS, cfg.button_font,
                   cfg.text_color, cfg.corner_radius, on_click=self.open_credits, shape=shield),
        ]

        self.beta_logo_img = pygame.image.load("assets/beta_logo.png")
        logo_size = max(8, int(280 * cfg.ui_scale()))
        self.beta_logo_img = pygame.transform.scale(self.beta_logo_img, (logo_size, logo_size))
        self.beta_logo_rect = self.beta_logo_img.get_rect()

        self.tooltips = [
            Tooltip(
                self.beta_logo_rect,
                _("Our logo that we need to think of"),
                cfg.tooltip_bg_CREDITS, cfg.tooltip_border_CREDITS,
                cfg.tooltip_font_CREDITS, cfg.text_color,
                cfg.tooltip_appear, cfg.tooltip_padding
            )
        ]

        self.font_small = cfg.get_font(max(12, int(18 * scale)))
        self._anim_time = 0.0
        self._launch_phase = 0.0
        self._particles = []
        self._orbs = []
        self._bursts = []
        self._stars = []
        self._light_rays = []
        self._embers = []
        self._title_sparkles = []
        self._title_font = cfg.get_font(max(20, int(80 * scale)))
        self._sub_font = cfg.get_font(max(12, int(28 * scale)))
        self._bg_surface = None
        self._bg_key = None
        self._astrolabe_surf = None
        self._astrolabe_key = None

    def on_enter(self):
        self._anim_time = 0.0
        self._launch_phase = 0.0
        self._bursts.clear()
        self._title_sparkles.clear()
        sw, sh = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT

        if not self._stars:
            for _ in range(180):
                self._stars.append(Star(sw, sh))
        if not self._light_rays:
            for _ in range(4):
                self._light_rays.append(LightRay(sw, sh))
        if not self._embers:
            for _ in range(30):
                self._embers.append(AmbientEmber(sw, sh))
        if not self._particles:
            for _ in range(35):
                self._particles.append(FloatingOrb(sw, sh))

        cx, cy = sw // 2, int(sh * 0.18)
        for _ in range(60):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(80, 350)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 60
            self._bursts.append(LaunchBurst(
                cx + random.uniform(-20, 20), cy + random.uniform(-20, 20),
                vx, vy, GOLD_BRIGHT, random.randint(2, 5), random.uniform(0.6, 1.8)))
        for _ in range(30):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(50, 200)
            self._bursts.append(LaunchBurst(
                cx + random.uniform(-10, 10), cy + random.uniform(-10, 10),
                math.cos(angle) * speed, math.sin(angle) * speed - 30,
                (255, 180, 60), random.randint(1, 3), random.uniform(0.4, 1.2)))

    def _get_bg(self, sw, sh):
        key = (sw, sh)
        if self._bg_key == key and self._bg_surface is not None:
            return self._bg_surface

        bg_base = cfg.bg.copy()
        if bg_base.get_size() != (sw, sh):
            bg_base = pygame.transform.scale(bg_base, (sw, sh))

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((10, 8, 18, 130))

        cx, cy = sw // 2, sh // 2
        max_r = int(math.sqrt(cx * cx + cy * cy))
        for rs in range(max_r, 0, max(30, int(30 * cfg.ui_scale()))):
            ratio = rs / max_r
            va = int(70 * ratio * ratio)
            vs = pygame.Surface((rs * 2, rs * 2), pygame.SRCALPHA)
            pygame.draw.circle(vs, (5, 3, 10, va), (rs, rs), rs)
            overlay.blit(vs, (cx - rs, cy - rs))

        bg_base.blit(overlay, (0, 0))
        self._bg_surface = bg_base
        self._bg_key = key
        return self._bg_surface

    def _make_astrolabe(self, sw, sh):
        key = (sw, sh)
        if self._astrolabe_key == key and self._astrolabe_surf is not None:
            return self._astrolabe_surf

        cx, cy = sw // 2, int(sh * 0.35)
        base_r = min(sw, sh) // 4
        surf = pygame.Surface((sw, sh), pygame.SRCALPHA)

        for ring_r in [base_r, int(base_r * 0.78), int(base_r * 0.55)]:
            if ring_r < 10:
                continue
            s = pygame.Surface((ring_r * 2, ring_r * 2), pygame.SRCALPHA)
            a = 20 if ring_r == base_r else (30 if ring_r == int(base_r * 0.78) else 40)
            w = 1 if ring_r == base_r else (2 if ring_r == int(base_r * 0.78) else 2)
            pygame.draw.circle(s, (*GOLD, max(0, min(60, a))), (ring_r, ring_r), ring_r, w)
            surf.blit(s, (cx - ring_r, cy - ring_r))

        spoke_len = base_r
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            ex = cx + int(math.cos(rad) * spoke_len)
            ey = cy + int(math.sin(rad) * spoke_len)
            a = 15 if angle % 90 == 0 else 8
            pygame.draw.line(surf, (*GOLD, max(0, min(40, a))), (cx, cy), (ex, ey), 1)

        for ring_r in [int(base_r * 0.92), int(base_r * 0.65)]:
            if ring_r < 10:
                continue
            s = pygame.Surface((ring_r * 2, ring_r * 2), pygame.SRCALPHA)
            a = 8
            for a2 in range(0, 360, 10):
                rad = math.radians(a2)
                ex = ring_r + int(math.cos(rad) * ring_r)
                ey = ring_r + int(math.sin(rad) * ring_r)
                pygame.draw.circle(s, (*GOLD, max(0, min(25, a))), (ex, ey), 1)
            surf.blit(s, (cx - ring_r, cy - ring_r))

        inner_r = int(base_r * 0.08)
        if inner_r >= 2:
            s = pygame.Surface((inner_r * 2, inner_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*GOLD_BRIGHT, 40), (inner_r, inner_r), inner_r)
            surf.blit(s, (cx - inner_r, cy - inner_r))

        self._astrolabe_surf = surf
        self._astrolabe_key = key
        return self._astrolabe_surf

    def layout(self, screen: pygame.Surface):
        sw, sh = self._screen_size(screen)
        scale = cfg.ui_scale()
        button_width, button_height = max(1, int(380 * scale)), max(1, int(110 * scale))
        gap = max(4, int(60 * scale))
        tot_width = 2 * button_width + gap
        center_x = sw // 2

        positions = [
            pygame.Rect(center_x - tot_width // 2, int(sh * 0.60), button_width, button_height),
            pygame.Rect(center_x - button_width // 2, int(sh * 0.48), button_width, button_height),
            pygame.Rect(center_x - tot_width // 2 + button_width + gap, int(sh * 0.60), button_width, button_height),
            pygame.Rect(center_x - tot_width // 2, int(sh * 0.75), button_width, button_height),
            pygame.Rect(center_x - tot_width // 2 + button_width + gap, int(sh * 0.75), button_width, button_height),
        ]
        for button, rect in zip(self.buttons, positions):
            self._apply_button_size(button, rect)

        logo_off = max(20, int(180 * cfg.ui_scale()))
        self.beta_logo_rect = self.beta_logo_img.get_rect(center=(sw - logo_off, sh - logo_off))
        self.tooltips[0].update_target(self.beta_logo_rect, self.tooltips[0].text)

    def update(self, dt):
        self._anim_time += dt
        self._launch_phase = min(1.0, self._launch_phase + dt * 0.8)
        t = self._anim_time
        for p in self._particles:
            p.update(dt, t)
        for e in self._embers:
            e.update(dt, t)
        alive = []
        for b in self._bursts:
            b.update(dt)
            if b.lt > 0:
                alive.append(b)
        self._bursts = alive

        if random.random() < 0.3:
            title_y = int(cfg.SCREEN_HEIGHT * 0.35)
            title_h = self._title_font.get_height()
            spark_y = title_y + title_h // 2
            spark_x = random.uniform(cfg.SCREEN_WIDTH * 0.15, cfg.SCREEN_WIDTH * 0.85)
            self._title_sparkles.append(TitleSparkle(spark_x, spark_y))
        self._title_sparkles = [s for s in self._title_sparkles if s.life > 0]
        for s in self._title_sparkles:
            s.update(dt)

    def draw(self, screen):
        self.layout(screen)
        sw, sh = self._screen_size(screen)
        self.update(1 / 60)
        t = self._anim_time
        lp = _ease_out_cubic(self._launch_phase)

        bg = self._get_bg(sw, sh)
        screen.blit(bg, (0, 0))

        star_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for star in self._stars:
            star.draw(star_surf, t)
        screen.blit(star_surf, (0, 0))

        ray_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for ray in self._light_rays:
            ray.draw(ray_surf, t)
        screen.blit(ray_surf, (0, 0))

        wash = pygame.Surface((sw, sh), pygame.SRCALPHA)
        wash_a = int(12 + 8 * math.sin(t * 0.4))
        wash_phase = t * 0.2
        wr = int(sw * 0.4)
        wg_cx = int(sw * 0.5 + math.cos(wash_phase) * sw * 0.15)
        wg_cy = int(sh * 0.3 + math.sin(wash_phase * 0.7) * sh * 0.1)
        wg = pygame.Surface((wr * 2, wr * 2), pygame.SRCALPHA)
        pygame.draw.circle(wg, (255, 200, 80, max(0, min(30, wash_a))), (wr, wr), wr)
        wash.blit(wg, (wg_cx - wr, wg_cy - wr))
        wg2_cx = int(sw * 0.6 + math.sin(wash_phase * 1.3) * sw * 0.12)
        wg2_cy = int(sh * 0.6 + math.cos(wash_phase * 0.9) * sh * 0.08)
        wg2 = pygame.Surface((wr, wr), pygame.SRCALPHA)
        pygame.draw.circle(wg2, (180, 140, 255, max(0, min(18, wash_a - 3))), (wr // 2, wr // 2), wr // 2)
        wash.blit(wg2, (wg2_cx - wr // 2, wg2_cy - wr // 2))
        screen.blit(wash, (0, 0))

        orb_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for p in self._particles:
            p.draw(orb_surf, t)
        screen.blit(orb_surf, (0, 0))

        ember_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for e in self._embers:
            e.draw(ember_surf, t)
        screen.blit(ember_surf, (0, 0))

        if self._bursts:
            burst_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for b in self._bursts:
                b.draw(burst_surf)
            screen.blit(burst_surf, (0, 0))

        astrolabe = self._make_astrolabe(sw, sh)
        astro_alpha = int(255 * lp)
        astrolabe.set_alpha(astro_alpha)
        screen.blit(astrolabe, (0, 0))

        logo_progress = min(1.0, max(0, (t - 0.2) / 0.8))
        logo_scale_eased = _ease_out_back(logo_progress)
        logo_base_w = self.beta_logo_img.get_width()
        logo_base_h = self.beta_logo_img.get_height()
        logo_float = math.sin(t * 0.7) * 5 * cfg.ui_scale()
        lw = max(1, int(logo_base_w * logo_scale_eased))
        lh = max(1, int(logo_base_h * logo_scale_eased))
        logo_scaled = pygame.transform.smoothscale(self.beta_logo_img, (lw, lh))
        logo_cy = int(sh * 0.18) + int(logo_float)
        logo_rect = logo_scaled.get_rect(center=(sw // 2, logo_cy))

        if logo_progress > 0.05:
            glow_sz = max(lw, lh) + int(50 * cfg.ui_scale() * logo_scale_eased)
            glow = pygame.Surface((glow_sz, glow_sz), pygame.SRCALPHA)
            ga = int(35 + 20 * math.sin(t * 1.3)) if logo_progress > 0.5 else int(60 * logo_progress)
            pygame.draw.circle(glow, (*GOLD, max(0, min(60, ga))), (glow_sz // 2, glow_sz // 2), glow_sz // 2)
            screen.blit(glow, (logo_rect.centerx - glow_sz // 2, logo_rect.centery - glow_sz // 2))

        logo_scaled.set_alpha(int(255 * min(1.0, logo_progress * 2)))
        screen.blit(logo_scaled, logo_rect)

        title_text = "SUPER ULTRA PROJECT"
        title_y = int(sh * 0.35)
        title_chars = list(title_text)
        char_widths = [self._title_font.size(c)[0] for c in title_chars]
        total_title_w = sum(char_widths)
        title_start_x = (sw - total_title_w) // 2

        for i, char in enumerate(title_chars):
            char_delay = 0.5 + i * 0.03
            char_t = max(0, min(1.0, (t - char_delay) / 0.4))
            char_eased = _ease_out_elastic(char_t)
            char_offset_y = int((1.0 - char_eased) * 60)
            char_alpha = int(255 * char_eased)

            char_x = title_start_x + sum(char_widths[:i])
            char_s = self._title_font.render(char, True, GOLD_BRIGHT)
            char_s.set_alpha(char_alpha)

            if char_eased > 0.3:
                glow_a = int(40 * (1 - char_eased * 0.5))
                gs = self._title_font.render(char, True, (255, 200, 50))
                gs.set_alpha(max(0, min(60, glow_a)))
                screen.blit(gs, (char_x, title_y + char_offset_y))

            screen.blit(char_s, (char_x, title_y + char_offset_y))

        sparkle_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for s in self._title_sparkles:
            s.draw(sparkle_surf)
        screen.blit(sparkle_surf, (0, 0))

        div_delay = 1.2
        div_t = max(0, min(1.0, (t - div_delay) / 0.5))
        if div_t > 0:
            div_eased = _ease_out_cubic(div_t)
            div_w = int(sw * 0.55 * div_eased)
            div_x = (sw - div_w) // 2
            div_y = title_y + self._title_font.get_height() + int(12 * cfg.ui_scale())
            thin = max(1, int(1.5 * cfg.ui_scale()))
            thick = max(2, int(3 * cfg.ui_scale()))
            div_a = int(220 * div_eased)
            pygame.draw.line(screen, (*GOLD_DARK, div_a), (div_x, div_y), (div_x + div_w, div_y), thick)
            pygame.draw.line(screen, (*GOLD_BRIGHT, div_a), (div_x, div_y - thin), (div_x + div_w, div_y - thin), thin)
            for j, cx in enumerate((div_x + div_w // 4, div_x + div_w // 2, div_x + 3 * div_w // 4)):
                phase = t * 2.0 + j * 1.2
                ds = max(3, int(7 * cfg.ui_scale() * (0.8 + 0.2 * math.sin(phase))))
                pts = [(cx, div_y - ds), (cx + ds, div_y), (cx, div_y + ds), (cx - ds, div_y)]
                pygame.draw.polygon(screen, (*GOLD_BRIGHT, div_a), pts)

        sub_delay = 1.5
        sub_t = max(0, min(1.0, (t - sub_delay) / 0.6))
        if sub_t > 0:
            sub_alpha = int((140 + 50 * math.sin(t * 0.8)) * _ease_out_cubic(sub_t))
            sub_y = title_y + self._title_font.get_height() + int(30 * cfg.ui_scale())
            sub_s = self._sub_font.render(_("An Epic Adventure Awaits"), True, (200, 185, 140))
            sub_s.set_alpha(sub_alpha)
            screen.blit(sub_s, ((sw - sub_s.get_width()) // 2, sub_y))

        for i, button in enumerate(self.buttons):
            btn_delay = 1.0 + i * 0.12
            btn_t = max(0, min(1.0, (t - btn_delay) / 0.5))
            if btn_t > 0:
                btn_eased = _ease_out_back(btn_t)
                saved_y = button.rect.y
                button.rect.y = int(saved_y + (1 - btn_eased) * 40)
                button.draw(screen)
                button.rect.y = saved_y

        screen.blit(self.beta_logo_img, self.beta_logo_rect)

        corner_t = max(0, min(1.0, (t - 0.8) / 0.5))
        if corner_t > 0:
            ca = int(180 * _ease_out_cubic(corner_t))
            cc = (*GOLD, ca)
            ofs = max(20, int(40 * cfg.ui_scale()))
            cr = max(4, int(8 * cfg.ui_scale()))
            orn_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for cx2, cy2 in [(ofs, ofs), (sw - ofs, ofs), (ofs, sh - ofs), (sw - ofs, sh - ofs)]:
                outer_r = max(8, int(16 * cfg.ui_scale()))
                inner_r = max(4, int(8 * cfg.ui_scale()))
                s = pygame.Surface((outer_r * 2, outer_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*GOLD, max(0, min(40, ca // 3))), (outer_r, outer_r), outer_r)
                pygame.draw.circle(s, (*GOLD_BRIGHT, max(0, min(60, ca // 2))), (outer_r, outer_r), inner_r)
                for angle in range(0, 360, 30):
                    rad = math.radians(angle)
                    ex = outer_r + int(math.cos(rad) * (outer_r - 2))
                    ey = outer_r + int(math.sin(rad) * (outer_r - 2))
                    lw = max(1, outer_r // 6)
                    lc = (*GOLD, max(0, min(30, ca // 4)))
                    pygame.draw.line(s, lc, (outer_r, outer_r), (ex, ey), lw)
                orn_surf.blit(s, (cx2 - outer_r, cy2 - outer_r))
            screen.blit(orn_surf, (0, 0))

        ver_t = max(0, min(1.0, (t - 2.0) / 0.5))
        if ver_t > 0:
            ver_s = self.font_small.render("v0.1.0 \u2014 Codex Arcanum", True, (150, 135, 105))
            ver_s.set_alpha(int(140 * _ease_out_cubic(ver_t)))
            screen.blit(ver_s, ((sw - ver_s.get_width()) // 2, sh - int(30 * cfg.ui_scale())))

        if lp < 1.0:
            ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
            ov.fill((0, 0, 0, max(0, min(255, int(255 * (1.0 - lp))))))
            screen.blit(ov, (0, 0))

    def start_game(self):
        logger.info("Start game requested from MainMenu")
        self.app.manager.set_state("gameplay")

    def exit_game(self):
        logger.info("Exit requested from MainMenu")
        pygame.quit()
        sys.exit()

    def open_settings(self):
        logger.info("Open Settings from MainMenu")
        self.app.manager.set_state("settings")

    def open_credits(self):
        logger.info("Open Credits from MainMenu")
        self.app.manager.set_state("credits")

    def open_load_menu(self):
        logger.info("Open Load Menu from MainMenu")
        self.app.manager.states["save_load"].mode = "load"
        self.app.manager.states["save_load"].refresh_saves()
        self.app.manager.set_state("save_load")
