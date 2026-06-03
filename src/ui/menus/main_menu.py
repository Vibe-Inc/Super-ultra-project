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


def _ease_out_back(t):
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


def _ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def _ease_out_elastic(t):
    if t == 0 or t == 1:
        return t
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1


class FloatingOrb:
    """A large, soft glowing orb that drifts slowly across the screen."""
    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        self._reset(True)

    def _reset(self, init=False):
        self.x = random.uniform(0, self.sw)
        self.y = random.uniform(0, self.sh) if init else random.uniform(self.sh, self.sh + 100)
        self.vx = random.uniform(-15, 15)
        self.vy = random.uniform(-40, -10)
        self.radius = random.randint(30, 80)
        self.hue_shift = random.uniform(-20, 20)
        self.phase = random.uniform(0, 6.28)
        self.freq = random.uniform(0.3, 1.0)
        self.alpha_base = random.randint(8, 25)

    def update(self, dt, t):
        self.x += self.vx * dt + math.sin(t * 0.3 + self.phase) * 8 * dt
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
            c = (max(0, min(255, 210 + int(self.hue_shift))),
                 max(0, min(255, 175 + int(self.hue_shift * 0.5))),
                 max(0, min(255, 55 + int(self.hue_shift * 0.3))),
                 ca)
            pygame.draw.circle(s, c, (r, r), ri)
        surf.blit(s, (px - r, py - r))


class LaunchBurst:
    """A single burst particle for the launch animation."""
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
    """Gold shimmer text with caching."""
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


class MainMenu(Menu):
    """Main menu screen with dramatic launch animation and majestic visuals."""

    def __init__(self, app: "App"):
        super().__init__(app)

        scale = cfg.ui_scale()
        button_width, button_height = max(1, int(360 * scale)), max(1, int(120 * scale))
        gap = max(4, int(60 * scale))
        tot_width = 2 * button_width + gap
        center_x = cfg.SCREEN_WIDTH // 2

        start_rect = pygame.Rect(center_x - tot_width // 2, int(650 * scale), button_width, button_height)
        exit_rect = pygame.Rect(center_x - tot_width // 2 + button_width + gap, int(650 * scale), button_width, button_height)
        settings_rect = pygame.Rect(center_x - tot_width // 2, int(800 * scale), button_width, button_height)
        credits_rect = pygame.Rect(center_x - tot_width // 2 + button_width + gap, int(800 * scale), button_width, button_height)
        load_rect = pygame.Rect(center_x - button_width // 2, int(520 * scale), button_width, button_height)

        self.buttons = [
            Button(start_rect, _("START"), cfg.button_color_START,
                   cfg.button_hover_color_START, cfg.button_font,
                   cfg.text_color, cfg.corner_radius, on_click=self.start_game),
            Button(load_rect, _("LOAD"), cfg.button_color_SETTINGS,
                   cfg.button_hover_color_SETTINGS, cfg.button_font,
                   cfg.text_color, cfg.corner_radius, on_click=self.open_load_menu),
            Button(exit_rect, _("EXIT"), cfg.button_color_EXIT,
                   cfg.button_hover_color_EXIT, cfg.button_font,
                   cfg.text_color, cfg.corner_radius, on_click=self.exit_game),
            Button(settings_rect, _("SETTINGS"), cfg.button_color_SETTINGS,
                   cfg.button_hover_color_SETTINGS, cfg.button_font,
                   cfg.text_color, cfg.corner_radius, on_click=self.open_settings),
            Button(credits_rect, _("CREDITS"), cfg.button_color_CREDITS,
                   cfg.button_hover_color_CREDITS, cfg.button_font,
                   cfg.text_color, cfg.corner_radius, on_click=self.open_credits),
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
        self._launch_phase = 0.0  # 0→1 controls the entire launch sequence
        self._particles = []
        self._orbs = []
        self._bursts = []
        self._title_font = cfg.get_font(max(20, int(80 * scale)))
        self._sub_font = cfg.get_font(max(12, int(28 * scale)))
        self._bg_surface = None  # cached game bg + overlay
        self._bg_key = None

    def on_enter(self):
        self._anim_time = 0.0
        self._launch_phase = 0.0
        self._bursts.clear()
        if not self._particles:
            sw, sh = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT
            for _ in range(35):
                self._particles.append(FloatingOrb(sw, sh))
        # Trigger initial burst
        sw, sh = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT
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

        # Use game background image as base
        bg_base = cfg.bg.copy()
        if bg_base.get_size() != (sw, sh):
            bg_base = pygame.transform.scale(bg_base, (sw, sh))

        # Create overlay with semi-transparent dark tint (keeps image visible)
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((10, 8, 18, 120))  # Much lighter — just a gentle tint

        # Radial vignette (darker at edges, clear in center)
        cx, cy = sw // 2, sh // 2
        max_r = int(math.sqrt(cx * cx + cy * cy))
        for rs in range(max_r, 0, max(30, int(30 * cfg.ui_scale()))):
            ratio = rs / max_r
            va = int(60 * ratio * ratio)  # stronger at edges
            vs = pygame.Surface((rs * 2, rs * 2), pygame.SRCALPHA)
            pygame.draw.circle(vs, (5, 3, 10, va), (rs, rs), rs)
            overlay.blit(vs, (cx - rs, cy - rs))

        bg_base.blit(overlay, (0, 0))
        self._bg_surface = bg_base
        self._bg_key = key
        return self._bg_surface

    def layout(self, screen: pygame.Surface):
        sw, sh = self._screen_size(screen)
        scale = cfg.ui_scale()
        button_width, button_height = max(1, int(360 * scale)), max(1, int(120 * scale))
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
        for p in self._particles:
            p.update(dt, self._anim_time)
        alive = []
        for b in self._bursts:
            b.update(dt)
            if b.lt > 0:
                alive.append(b)
        self._bursts = alive

    def draw(self, screen):
        self.layout(screen)
        sw, sh = self._screen_size(screen)
        scale = cfg.ui_scale()
        self.update(1 / 60)
        t = self._anim_time
        lp = _ease_out_cubic(self._launch_phase)

        # ── Background: game image with elegant tint ──
        bg = self._get_bg(sw, sh)
        screen.blit(bg, (0, 0))

        # ── Animated color-shifting light wash ──
        wash = pygame.Surface((sw, sh), pygame.SRCALPHA)
        wash_a = int(15 + 10 * math.sin(t * 0.4))
        wash_phase = t * 0.2
        wr = int(sw * 0.4)
        wg_cx = int(sw * 0.5 + math.cos(wash_phase) * sw * 0.15)
        wg_cy = int(sh * 0.3 + math.sin(wash_phase * 0.7) * sh * 0.1)
        wg = pygame.Surface((wr * 2, wr * 2), pygame.SRCALPHA)
        pygame.draw.circle(wg, (255, 200, 80, max(0, min(30, wash_a))), (wr, wr), wr)
        wash.blit(wg, (wg_cx - wr, wg_cy - wr))
        # Second orb
        wg2_cx = int(sw * 0.6 + math.sin(wash_phase * 1.3) * sw * 0.12)
        wg2_cy = int(sh * 0.6 + math.cos(wash_phase * 0.9) * sh * 0.08)
        wg2 = pygame.Surface((wr, wr), pygame.SRCALPHA)
        pygame.draw.circle(wg2, (200, 150, 255, max(0, min(20, wash_a - 5))), (wr // 2, wr // 2), wr // 2)
        wash.blit(wg2, (wg2_cx - wr // 2, wg2_cy - wr // 2))
        screen.blit(wash, (0, 0))

        # ── Floating orbs ──
        orb_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for p in self._particles:
            p.draw(orb_surf, t)
        screen.blit(orb_surf, (0, 0))

        # ── Burst particles ──
        if self._bursts:
            burst_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for b in self._bursts:
                b.draw(burst_surf)
            screen.blit(burst_surf, (0, 0))

        # ── Logo: dramatic entrance (scale up from 0 with bounce) ──
        logo_progress = min(1.0, max(0, (t - 0.2) / 0.8))
        logo_scale_eased = _ease_out_back(logo_progress)
        logo_base_w = self.beta_logo_img.get_width()
        logo_base_h = self.beta_logo_img.get_height()
        logo_float = math.sin(t * 0.7) * 5 * scale
        lw = max(1, int(logo_base_w * logo_scale_eased))
        lh = max(1, int(logo_base_h * logo_scale_eased))
        logo_scaled = pygame.transform.smoothscale(self.beta_logo_img, (lw, lh))
        logo_cy = int(sh * 0.18) + int(logo_float)
        logo_rect = logo_scaled.get_rect(center=(sw // 2, logo_cy))

        # Glow behind logo (grows with entrance)
        if logo_progress > 0.05:
            glow_sz = max(lw, lh) + int(50 * scale * logo_scale_eased)
            glow = pygame.Surface((glow_sz, glow_sz), pygame.SRCALPHA)
            ga = int(35 + 20 * math.sin(t * 1.3)) if logo_progress > 0.5 else int(60 * logo_progress)
            pygame.draw.circle(glow, (*GOLD, max(0, min(60, ga))), (glow_sz // 2, glow_sz // 2), glow_sz // 2)
            screen.blit(glow, (logo_rect.centerx - glow_sz // 2, logo_rect.centery - glow_sz // 2))

        logo_scaled.set_alpha(int(255 * min(1.0, logo_progress * 2)))
        screen.blit(logo_scaled, logo_rect)

        # ── Title: staggered letter entrance ──
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

            # Glow per character
            if char_eased > 0.3:
                glow_a = int(40 * (1 - char_eased * 0.5))
                gs = self._title_font.render(char, True, (255, 200, 50))
                gs.set_alpha(max(0, min(60, glow_a)))
                screen.blit(gs, (char_x, title_y + char_offset_y))

            screen.blit(char_s, (char_x, title_y + char_offset_y))

        # ── Gold divider (appears after title) ──
        div_delay = 1.2
        div_t = max(0, min(1.0, (t - div_delay) / 0.5))
        if div_t > 0:
            div_eased = _ease_out_cubic(div_t)
            div_w = int(sw * 0.5 * div_eased)
            div_x = (sw - div_w) // 2
            div_y = title_y + self._title_font.get_height() + int(12 * scale)
            thin = max(1, int(1.5 * scale))
            thick = max(2, int(3 * scale))
            div_a = int(220 * div_eased)
            pygame.draw.line(screen, (*GOLD_DARK, div_a), (div_x, div_y), (div_x + div_w, div_y), thick)
            pygame.draw.line(screen, (*GOLD_BRIGHT, div_a), (div_x, div_y - thin), (div_x + div_w, div_y - thin), thin)
            # Diamond ornaments
            for j, cx in enumerate((div_x + div_w // 4, div_x + div_w // 2, div_x + 3 * div_w // 4)):
                phase = t * 2.0 + j * 1.2
                ds = max(3, int(6 * scale * (0.8 + 0.2 * math.sin(phase))))
                pts = [(cx, div_y - ds), (cx + ds, div_y), (cx, div_y + ds), (cx - ds, div_y)]
                pygame.draw.polygon(screen, (*GOLD_BRIGHT, div_a), pts)

        # ── Subtitle (fades in after divider) ──
        sub_delay = 1.5
        sub_t = max(0, min(1.0, (t - sub_delay) / 0.6))
        if sub_t > 0:
            sub_alpha = int((140 + 50 * math.sin(t * 0.8)) * _ease_out_cubic(sub_t))
            sub_y = title_y + self._title_font.get_height() + int(30 * scale)
            sub_s = self._sub_font.render(_("An Epic Adventure Awaits"), True, (200, 185, 140))
            sub_s.set_alpha(sub_alpha)
            screen.blit(sub_s, ((sw - sub_s.get_width()) // 2, sub_y))

        # ── Buttons: staggered slide-up entrance ──
        for i, button in enumerate(self.buttons):
            btn_delay = 1.0 + i * 0.12
            btn_t = max(0, min(1.0, (t - btn_delay) / 0.5))
            if btn_t > 0:
                btn_eased = _ease_out_back(btn_t)
                saved_y = button.rect.y
                button.rect.y = int(saved_y + (1 - btn_eased) * 40)
                button.draw(screen)
                button.rect.y = saved_y

        # ── Logo overlay ──
        screen.blit(self.beta_logo_img, self.beta_logo_rect)

        # ── Corner ornaments (fade in) ──
        corner_t = max(0, min(1.0, (t - 0.8) / 0.5))
        if corner_t > 0:
            ca = int(140 * _ease_out_cubic(corner_t))
            cc = (*GOLD, ca)
            ofs = max(20, int(40 * scale))
            cr = max(4, int(8 * scale))
            for cx2, cy2 in [(ofs, ofs), (sw - ofs, ofs), (ofs, sh - ofs), (sw - ofs, sh - ofs)]:
                pygame.draw.circle(screen, cc, (cx2, cy2), cr)
                pygame.draw.circle(screen, (*GOLD_BRIGHT, ca), (cx2, cy2), max(1, cr - 2))
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    ex = cx2 + int(math.cos(rad) * (cr + 5))
                    ey = cy2 + int(math.sin(rad) * (cr + 5))
                    pygame.draw.line(screen, cc, (cx2, cy2), (ex, ey), 1)

        # ── Tooltips ──
        mouse_pos = pygame.mouse.get_pos()
        for tooltip in self.tooltips:
            tooltip.hover_update(mouse_pos)
            tooltip.draw(screen)

        # ── Version text ──
        ver_t = max(0, min(1.0, (t - 2.0) / 0.5))
        if ver_t > 0:
            ver_s = self.font_small.render("v0.1.0 \u2014 Codex Arcanum", True, (150, 135, 105))
            ver_s.set_alpha(int(140 * _ease_out_cubic(ver_t)))
            screen.blit(ver_s, ((sw - ver_s.get_width()) // 2, sh - int(30 * scale)))

        # ── Fade-in overlay ──
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