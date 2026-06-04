import math
import random
import pygame
import sys
from gettext import gettext as _
from typing import TYPE_CHECKING

from src.ui.menus.base import Menu
from src.ui.widgets import Button, Tooltip
from src.ui.effects import (
    GOLD, GOLD_BRIGHT, GOLD_DARK,
    ease_out_back, ease_out_cubic, ease_out_elastic,
    Star, LightRay, AmbientEmber, FloatingOrb, LaunchBurst,
    render_shimmer_text, TitleSparkle, MenuClock,
)
import src.config as cfg
from src.core.logger import logger
from src.core.save_manager import SaveManager

if TYPE_CHECKING:
    from src.app import App


class MainMenu(Menu):
    """
    Main menu screen with start, load, settings, credits, and exit options.

    Features animated background effects, decorative particles, and shield-shaped buttons.

    Attributes:
        app (App):
            The main application instance.
        buttons (list[Button]):
            List of main menu buttons (START, LOAD, EXIT, SETTINGS, CREDITS).
        beta_logo_img (pygame.Surface):
            The beta logo image.
        _label_font (pygame.font.Font):
            Font for labels.
        _title_font (pygame.font.Font):
            Large font for the title.
        font_small (pygame.font.Font):
            Small font for captions.
        _anim_time (float):
            Accumulated animation time.
        _launch_phase (float):
            Phase of the launch animation.
        _particles (list):
            Decorative ambient particles.
        _stars (list):
            Background star effects.
        _light_rays (list):
            Light ray effects.
        _embers (list):
            Ambient ember particles.
        _bursts (list):
            Launch burst effects.
        _sparkles (list):
            Title sparkle effects.
        _panel_rect (pygame.Rect):
            Rectangle for the central panel.

    Methods:
        __init__(app):
            Initialize the main menu.
        start_game():
            Start a new game.
        exit_game():
            Exit the application.
        open_settings():
            Open the settings menu.
        open_load_menu():
            Open the save/load menu.
        open_credits():
            Open the credits menu.
        back_to_main():
            Return to the main menu screen (inherited).
        handle_event(event):
            Handle input events.
        update(dt):
            Update animations and effects.
        draw(screen):
            Render the main menu.
    """

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
        self.beta_logo_img = pygame.image.load("assets/ui/beta_logo.png")
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
        self._clock = MenuClock()
        self._surf_cache = {}
        self._cached_chars = {}
        self._cached_title_chars = {}
        self._orn_cache = None
        self._orn_key = None

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

    def _get_surf(self, name, sw, sh):
        key = (name, sw, sh)
        s = self._surf_cache.get(key)
        if s is None:
            s = pygame.Surface((sw, sh), pygame.SRCALPHA)
            self._surf_cache[key] = s
        else:
            s.fill((0, 0, 0, 0))
        return s

    def draw(self, screen):
        self.layout(screen)
        sw, sh = self._screen_size(screen)
        self.update(1 / 60)
        t = self._anim_time
        lp = ease_out_cubic(self._launch_phase)
        scale = cfg.ui_scale()

        bg = self._get_bg(sw, sh)
        screen.blit(bg, (0, 0))

        star_surf = self._get_surf('star', sw, sh)
        for star in self._stars:
            star.draw(star_surf, t)
        screen.blit(star_surf, (0, 0))

        ray_surf = self._get_surf('ray', sw, sh)
        for ray in self._light_rays:
            ray.draw(ray_surf, t)
        screen.blit(ray_surf, (0, 0))

        wash = self._get_surf('wash', sw, sh)
        wash_a = int(12 + 8 * math.sin(t * 0.4))
        wash_phase = t * 0.2
        wr = int(sw * 0.4)
        wg_cx = int(sw * 0.5 + math.cos(wash_phase) * sw * 0.15)
        wg_cy = int(sh * 0.3 + math.sin(wash_phase * 0.7) * sh * 0.1)
        wg = self._get_surf('wg', wr * 2, wr * 2)
        wg.fill((0, 0, 0, 0))
        pygame.draw.circle(wg, (255, 200, 80, max(0, min(30, wash_a))), (wr, wr), wr)
        wash.blit(wg, (wg_cx - wr, wg_cy - wr))
        wg2_cx = int(sw * 0.6 + math.sin(wash_phase * 1.3) * sw * 0.12)
        wg2_cy = int(sh * 0.6 + math.cos(wash_phase * 0.9) * sh * 0.08)
        wg2 = self._get_surf('wg2', wr, wr)
        wg2.fill((0, 0, 0, 0))
        pygame.draw.circle(wg2, (180, 140, 255, max(0, min(18, wash_a - 3))), (wr // 2, wr // 2), wr // 2)
        wash.blit(wg2, (wg2_cx - wr // 2, wg2_cy - wr // 2))
        screen.blit(wash, (0, 0))

        orb_surf = self._get_surf('orb', sw, sh)
        for p in self._particles:
            p.draw(orb_surf, t)
        screen.blit(orb_surf, (0, 0))

        ember_surf = self._get_surf('ember', sw, sh)
        for e in self._embers:
            e.draw(ember_surf, t)
        screen.blit(ember_surf, (0, 0))

        if self._bursts:
            burst_surf = self._get_surf('burst', sw, sh)
            for b in self._bursts:
                b.draw(burst_surf)
            screen.blit(burst_surf, (0, 0))

        astrolabe = self._make_astrolabe(sw, sh)
        astro_alpha = int(255 * lp)
        astrolabe.set_alpha(astro_alpha)
        screen.blit(astrolabe, (0, 0))

        self._clock.draw(screen, t, sw, sh, scale)

        logo_progress = min(1.0, max(0, (t - 0.2) / 0.8))
        logo_scale_eased = ease_out_back(logo_progress)
        logo_base_w = self.beta_logo_img.get_width()
        logo_base_h = self.beta_logo_img.get_height()
        logo_float = math.sin(t * 0.7) * 5 * scale
        lw = max(1, int(logo_base_w * logo_scale_eased))
        lh = max(1, int(logo_base_h * logo_scale_eased))
        logo_scaled = pygame.transform.smoothscale(self.beta_logo_img, (lw, lh))
        logo_cy = int(sh * 0.18) + int(logo_float)
        logo_rect = logo_scaled.get_rect(center=(sw // 2, logo_cy))

        if logo_progress > 0.05:
            glow_sz = max(lw, lh) + int(50 * scale * logo_scale_eased)
            glow = pygame.Surface((glow_sz, glow_sz), pygame.SRCALPHA)
            ga = int(35 + 20 * math.sin(t * 1.3)) if logo_progress > 0.5 else int(60 * logo_progress)
            pygame.draw.circle(glow, (*GOLD, max(0, min(60, ga))), (glow_sz // 2, glow_sz // 2), glow_sz // 2)
            screen.blit(glow, (logo_rect.centerx - glow_sz // 2, logo_rect.centery - glow_sz // 2))

        logo_scaled.set_alpha(int(255 * min(1.0, logo_progress * 2)))
        screen.blit(logo_scaled, logo_rect)

        title_text = "CODEX ARCANUM"
        title_y = int(sh * 0.35)
        title_chars = list(title_text)
        char_widths = []
        for c in title_chars:
            if c not in self._cached_title_chars:
                self._cached_title_chars[c] = self._title_font.render(c, True, GOLD_BRIGHT)
            if ('glow', c) not in self._cached_title_chars:
                self._cached_title_chars[('glow', c)] = self._title_font.render(c, True, (255, 200, 50))
            char_widths.append(self._cached_title_chars[c].get_width())
        total_title_w = sum(char_widths)
        title_start_x = (sw - total_title_w) // 2

        for i, char in enumerate(title_chars):
            char_delay = 0.5 + i * 0.03
            char_t = max(0, min(1.0, (t - char_delay) / 0.4))
            char_eased = ease_out_elastic(char_t)
            char_offset_y = int((1.0 - char_eased) * 60)
            char_alpha = int(255 * char_eased)

            char_x = title_start_x + sum(char_widths[:i])

            if char_eased > 0.3:
                glow_a = int(40 * (1 - char_eased * 0.5))
                gs = self._cached_title_chars[('glow', char)]
                gs.set_alpha(max(0, min(60, glow_a)))
                screen.blit(gs, (char_x, title_y + char_offset_y))

            char_s = self._cached_title_chars[char]
            char_s.set_alpha(char_alpha)
            screen.blit(char_s, (char_x, title_y + char_offset_y))

        sparkle_surf = self._get_surf('sparkle', sw, sh)
        for s in self._title_sparkles:
            s.draw(sparkle_surf)
        screen.blit(sparkle_surf, (0, 0))

        div_delay = 1.2
        div_t = max(0, min(1.0, (t - div_delay) / 0.5))
        if div_t > 0:
            div_eased = ease_out_cubic(div_t)
            div_w = int(sw * 0.55 * div_eased)
            div_x = (sw - div_w) // 2
            div_y = title_y + self._title_font.get_height() + int(12 * scale)
            thin = max(1, int(1.5 * scale))
            thick = max(2, int(3 * scale))
            div_a = int(220 * div_eased)
            pygame.draw.line(screen, (*GOLD_DARK, div_a), (div_x, div_y), (div_x + div_w, div_y), thick)
            pygame.draw.line(screen, (*GOLD_BRIGHT, div_a), (div_x, div_y - thin), (div_x + div_w, div_y - thin), thin)
            for j, cx in enumerate((div_x + div_w // 4, div_x + div_w // 2, div_x + 3 * div_w // 4)):
                phase = t * 2.0 + j * 1.2
                ds = max(3, int(7 * scale * (0.8 + 0.2 * math.sin(phase))))
                pts = [(cx, div_y - ds), (cx + ds, div_y), (cx, div_y + ds), (cx - ds, div_y)]
                pygame.draw.polygon(screen, (*GOLD_BRIGHT, div_a), pts)

        sub_delay = 1.5
        sub_t = max(0, min(1.0, (t - sub_delay) / 0.6))
        if sub_t > 0:
            sub_alpha = int((140 + 50 * math.sin(t * 0.8)) * ease_out_cubic(sub_t))
            sub_y = title_y + self._title_font.get_height() + int(30 * scale)
            sub_s = self._sub_font.render(_("An Epic Adventure Awaits"), True, (200, 185, 140))
            sub_s.set_alpha(sub_alpha)
            screen.blit(sub_s, ((sw - sub_s.get_width()) // 2, sub_y))

        for i, button in enumerate(self.buttons):
            btn_delay = 1.0 + i * 0.12
            btn_t = max(0, min(1.0, (t - btn_delay) / 0.5))
            if btn_t > 0:
                btn_eased = ease_out_back(btn_t)
                saved_y = button.rect.y
                button.rect.y = int(saved_y + (1 - btn_eased) * 40)
                button.draw(screen)
                button.rect.y = saved_y

        screen.blit(self.beta_logo_img, self.beta_logo_rect)

        corner_t = max(0, min(1.0, (t - 0.8) / 0.5))
        if corner_t > 0:
            ca = int(180 * ease_out_cubic(corner_t))
            if self._orn_key != (sw, sh) or self._orn_cache is None:
                ofs = max(20, int(40 * scale))
                self._orn_cache = pygame.Surface((sw, sh), pygame.SRCALPHA)
                for cx2, cy2 in [(ofs, ofs), (sw - ofs, ofs), (ofs, sh - ofs), (sw - ofs, sh - ofs)]:
                    outer_r = max(8, int(16 * scale))
                    inner_r = max(4, int(8 * scale))
                    s = pygame.Surface((outer_r * 2, outer_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*GOLD, 40), (outer_r, outer_r), outer_r)
                    pygame.draw.circle(s, (*GOLD_BRIGHT, 60), (outer_r, outer_r), inner_r)
                    for angle in range(0, 360, 30):
                        rad = math.radians(angle)
                        ex = outer_r + int(math.cos(rad) * (outer_r - 2))
                        ey = outer_r + int(math.sin(rad) * (outer_r - 2))
                        lw = max(1, outer_r // 6)
                        pygame.draw.line(s, (*GOLD, 30), (outer_r, outer_r), (ex, ey), lw)
                    self._orn_cache.blit(s, (cx2 - outer_r, cy2 - outer_r))
                self._orn_key = (sw, sh)
            self._orn_cache.set_alpha(ca)
            screen.blit(self._orn_cache, (0, 0))
            self._orn_cache.set_alpha(255)

        ver_t = max(0, min(1.0, (t - 2.0) / 0.5))
        if ver_t > 0:
            ver_s = self.font_small.render("v0.1.0 \u2014 Codex Arcanum", True, (150, 135, 105))
            ver_s.set_alpha(int(140 * ease_out_cubic(ver_t)))
            screen.blit(ver_s, ((sw - ver_s.get_width()) // 2, sh - int(30 * scale)))

        if lp < 1.0:
            ov = self._get_surf('overlay', sw, sh)
            ov.fill((0, 0, 0, max(0, min(255, int(255 * (1.0 - lp))))))
            screen.blit(ov, (0, 0))

    def start_game(self):
        logger.info("Start game requested from MainMenu")
        self.app.manager.set_state("gameplay")

    def exit_game(self):
        logger.info("Exit requested from MainMenu")
        SaveManager.save_settings(self.app)
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
