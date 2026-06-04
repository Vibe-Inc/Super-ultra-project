import math
import random
import pygame
from typing import TYPE_CHECKING
from gettext import gettext as _

from src.ui.menus.base import Menu
from src.ui.widgets import Button, Slider
from src.ui.effects import (
    GOLD, GOLD_BRIGHT, GOLD_DARK,
    ease_out_back, ease_out_cubic,
    Star, LightRay, AmbientEmber, FloatingOrb, LaunchBurst,
    TitleSparkle,
)
import src.config as cfg

if TYPE_CHECKING:
    from src.app import App


class SettingsMenu(Menu):
    """
    Settings screen for display mode, language, brightness, and audio volume.

    Features animated background effects and gold-styled sliders.

    Attributes:
        app (App):
            The main application instance.
        buttons (list[Button]):
            List of setting buttons (display mode, language, back).
        brightness_slider (Slider):
            Slider control for screen brightness.
        audio_slider (Slider):
            Slider control for audio volume.
        _label_font (pygame.font.Font):
            Font for setting labels.
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
            Initialize the settings menu.
        _display_mode_label():
            Get the label for the current display mode.
        toggle_display_mode():
            Toggle between fullscreen and windowed mode.
        toggle_language():
            Cycle through available languages.
        back_to_main():
            Return to the main menu.
        handle_event(event):
            Handle input events.
        update(dt):
            Update animations and effects.
        draw(screen):
            Render the settings menu.
    """

    def __init__(self, app: "App"):
        super().__init__(app)
        scale = cfg.ui_scale()

        btn_w, btn_h = max(1, int(360 * scale)), max(1, int(100 * scale))

        self.buttons = [
            Button(pygame.Rect(0, 0, btn_w, btn_h), self._display_mode_label(),
                   cfg.button_color_SETTINGS, cfg.button_hover_color_SETTINGS,
                   cfg.button_font, cfg.text_color, cfg.corner_radius,
                   on_click=self.toggle_display_mode, shape='shield'),
            Button(pygame.Rect(0, 0, btn_w, btn_h),
                   f"{_('LANG')}: {cfg.LANGUAGE.upper()}",
                   cfg.button_color_SETTINGS, cfg.button_hover_color_SETTINGS,
                   cfg.button_font, cfg.text_color, cfg.corner_radius,
                   on_click=self.toggle_language, shape='shield'),
            Button(pygame.Rect(0, 0, btn_w, btn_h), _("BACK"),
                   cfg.button_color_SETTINGS_BACK, cfg.button_hover_color_SETTINGS_BACK,
                   cfg.button_font, cfg.text_color, cfg.corner_radius,
                   on_click=self.back_to_main, shape='shield'),
        ]

        initial_volume = pygame.mixer.music.get_volume() if pygame.mixer.get_init() else 0.3

        def set_brightness(v):
            cfg.USER_SCREEN_BRIGHTNESS = max(0.3, v)
            cfg.update_brightness()

        track_len = max(50, int(340 * scale))
        sh2 = max(10, int(44 * scale))
        self.brightness_slider = Slider(
            0, 0, sh2, max(3, int(6 * scale)),
            (0, 0, 0), (255, 255, 255),
            max(10, int(22 * scale)), max(10, int(22 * scale)),
            track_len, value=cfg.USER_SCREEN_BRIGHTNESS,
            action=set_brightness, style='gold',
        )
        self.audio_slider = Slider(
            0, 0, sh2, max(3, int(6 * scale)),
            (0, 0, 0), (255, 255, 255),
            max(10, int(22 * scale)), max(10, int(22 * scale)),
            track_len, value=initial_volume,
            action=lambda v: pygame.mixer.music.set_volume(v), style='gold',
        )

        self._label_font = cfg.get_font(max(12, int(28 * scale)))
        self._title_font = cfg.get_font(max(20, int(72 * scale)))
        self.font_small = cfg.get_font(max(12, int(18 * scale)))

        self._anim_time = 0.0
        self._launch_phase = 0.0
        self._particles = []
        self._stars = []
        self._light_rays = []
        self._embers = []
        self._bursts = []
        self._sparkles = []

        self._panel_rect = pygame.Rect(0, 0, 0, 0)
        self._label_positions = [(0, 0), (0, 0)]
        self._surf_cache = {}

    def _get_surf(self, name, sw, sh):
        key = (name, sw, sh)
        if key in self._surf_cache:
            surf = self._surf_cache[key]
            surf.fill((0, 0, 0, 0))
            return surf
        surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._surf_cache[key] = surf
        return surf

    def _display_mode_label(self):
        return f"MODE: {'FULLSCREEN' if self.app.is_fullscreen else 'WINDOW'}"

    def on_enter(self):
        self._anim_time = 0.0
        self._launch_phase = 0.0
        self._bursts.clear()
        self._sparkles.clear()
        sw, sh = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT

        if not self._stars:
            for _ in range(150):
                self._stars.append(Star(sw, sh))
        if not self._light_rays:
            for _ in range(3):
                self._light_rays.append(LightRay(sw, sh))
        if not self._embers:
            for _ in range(25):
                self._embers.append(AmbientEmber(sw, sh))
        if not self._particles:
            for _ in range(25):
                self._particles.append(FloatingOrb(sw, sh))

        cx, cy = sw // 2, sh // 2
        for _ in range(40):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(60, 250)
            self._bursts.append(LaunchBurst(
                cx + random.uniform(-30, 30), cy + random.uniform(-30, 30),
                math.cos(angle) * speed, math.sin(angle) * speed - 40,
                GOLD_BRIGHT, random.randint(2, 4), random.uniform(0.5, 1.5)))

    def layout(self, screen):
        sw, sh = self._screen_size(screen)
        scale = cfg.ui_scale()
        btn_w, btn_h = max(1, int(360 * scale)), max(1, int(100 * scale))

        self.buttons[0].set_text(self._display_mode_label())
        self.buttons[1].set_text(f"{_('LANG')}: {cfg.LANGUAGE.upper()}")
        self.buttons[2].set_text(_("BACK"))

        for button in self.buttons:
            try:
                button._update_text_surface()
            except Exception:
                pass

        panel_cx = sw // 2
        panel_cy = int(sh * 0.44)
        panel_w = int(880 * scale)
        pad_x = int(50 * scale)
        pad_y = int(40 * scale)
        gap = int(10 * scale)

        label_h = self._label_font.get_height()
        title_h = self._title_font.get_height()
        sh2 = self.brightness_slider.height

        row_h = max(btn_h, label_h + gap + sh2)
        panel_h = pad_y * 2 + title_h + gap * 8 + row_h * 3

        box_x = panel_cx - panel_w // 2
        box_y = panel_cy - panel_h // 2
        self._panel_rect = pygame.Rect(box_x, box_y, panel_w, panel_h)

        div_y = box_y + pad_y + title_h + gap
        body_y = div_y + gap * 2

        left_col_x = box_x + pad_x
        right_col_x = box_x + panel_w - pad_x - btn_w

        body_anchor = body_y + gap
        row0_y = body_anchor
        row1_y = row0_y + row_h + gap * 2
        row2_y = row1_y + row_h + gap * 2

        content_h = label_h + gap + sh2
        row_off = (row_h - content_h) // 2

        label0_y = row0_y + row_off
        slider0_y = label0_y + label_h + gap
        self.brightness_slider.x = left_col_x
        self.brightness_slider.y = slider0_y

        label1_y = row1_y + row_off
        slider1_y = label1_y + label_h + gap
        self.audio_slider.x = left_col_x
        self.audio_slider.y = slider1_y

        self.buttons[0].rect = pygame.Rect(right_col_x, row0_y, btn_w, btn_h)
        self.buttons[1].rect = pygame.Rect(right_col_x, row1_y, btn_w, btn_h)
        self.buttons[2].rect = pygame.Rect(right_col_x, row2_y, btn_w, btn_h)

        self._label_positions = [(left_col_x, label0_y), (left_col_x, label1_y)]

        for button in self.buttons:
            try:
                button._update_text_surface()
            except Exception:
                pass

    def _draw_background(self, screen, sw, sh, t, lp):
        star_surf = self._get_surf('star', sw, sh)
        for star in self._stars:
            star.draw(star_surf, t)
        screen.blit(star_surf, (0, 0))

        ray_surf = self._get_surf('ray', sw, sh)
        for ray in self._light_rays:
            ray.draw(ray_surf, t)
        screen.blit(ray_surf, (0, 0))

        wash = self._get_surf('wash', sw, sh)
        wash_a = int(10 + 6 * math.sin(t * 0.35))
        wash_phase = t * 0.15
        wr = int(sw * 0.35)
        wg_cx = int(sw * 0.5 + math.cos(wash_phase) * sw * 0.12)
        wg_cy = int(sh * 0.4 + math.sin(wash_phase * 0.6) * sh * 0.08)
        wg = self._get_surf('wg', wr * 2, wr * 2)
        pygame.draw.circle(wg, (255, 200, 80, max(0, min(25, wash_a))), (wr, wr), wr)
        wash.blit(wg, (wg_cx - wr, wg_cy - wr))
        wg2 = self._get_surf('wg2', wr, wr)
        pygame.draw.circle(wg2, (140, 100, 255, max(0, min(15, wash_a - 3))),
                          (wr // 2, wr // 2), wr // 2)
        wash.blit(wg2, (int(sw * 0.6) - wr // 2, int(sh * 0.6) - wr // 2))
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

    def _draw_panel(self, screen, sw, sh, t, lp):
        scale = cfg.ui_scale()
        pr = self._panel_rect
        box_x, box_y, panel_w, panel_h = pr.x, pr.y, pr.w, pr.h
        pad_x = int(50 * scale)
        pad_y = int(40 * scale)
        gap = int(10 * scale)

        box_t = max(0, min(1.0, (t - 0.3) / 0.5))
        box_alpha = int(255 * ease_out_cubic(box_t))
        if box_alpha < 5:
            return

        box_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        border_r = max(6, int(16 * scale))
        pygame.draw.rect(box_surf, (*GOLD_DARK, max(0, min(200, box_alpha))),
                        (0, 0, panel_w, panel_h), border_radius=border_r)
        inner = max(2, int(4 * scale))
        inner_r = max(4, border_r - inner)
        dark_bg = (12, 10, 22, max(0, min(240, box_alpha)))
        pygame.draw.rect(box_surf, dark_bg,
                        (inner, inner, panel_w - inner * 2, panel_h - inner * 2),
                        border_radius=inner_r)
        pygame.draw.rect(box_surf, (*GOLD, max(0, min(120, box_alpha))),
                        (inner * 2, inner * 2, panel_w - inner * 4, panel_h - inner * 4),
                        max(1, int(1.5 * scale)), border_radius=max(2, inner_r - inner))
        d_sz = max(2, int(5 * scale))
        for cx2, cy2 in [(inner, inner), (panel_w - inner, inner),
                         (inner, panel_h - inner), (panel_w - inner, panel_h - inner)]:
            d_pts = [(cx2, cy2 - d_sz), (cx2 + d_sz, cy2),
                     (cx2, cy2 + d_sz), (cx2 - d_sz, cy2)]
            pygame.draw.polygon(box_surf, (*GOLD_BRIGHT, max(0, min(180, box_alpha))), d_pts)
        screen.blit(box_surf, (box_x, box_y))

        title_y = box_y + pad_y
        title_s = self._title_font.render(_("SETTINGS"), True, GOLD_BRIGHT)
        title_s.set_alpha(box_alpha)
        screen.blit(title_s, (box_x + pad_x, title_y))

        div_y = title_y + self._title_font.get_height() + gap
        div_w = panel_w - pad_x * 2
        pygame.draw.line(screen, (*GOLD, max(0, min(100, box_alpha))),
                        (box_x + pad_x, div_y), (box_x + pad_x + div_w, div_y),
                        max(1, int(1.5 * scale)))
        d_phase = t * 2.0
        d_cx = box_x + pad_x + div_w // 2
        d_ds = max(2, int(5 * scale * (0.8 + 0.2 * math.sin(d_phase))))
        d_pts = [(d_cx, div_y - d_ds), (d_cx + d_ds, div_y),
                 (d_cx, div_y + d_ds), (d_cx - d_ds, div_y)]
        pygame.draw.polygon(screen, (*GOLD_BRIGHT, max(0, min(180, box_alpha))), d_pts)

        sliders = [
            (self._label_font.render(_('Brightness'), True, GOLD_BRIGHT), self.brightness_slider),
            (self._label_font.render(_('Music volume'), True, GOLD_BRIGHT), self.audio_slider),
        ]

        for i, (label_surf, slider) in enumerate(sliders):
            lx, ly = self._label_positions[i]
            label_surf.set_alpha(box_alpha)
            screen.blit(label_surf, (lx, ly))
            slider.draw(screen)

        if random.random() < 0.15:
            self._sparkles.append(TitleSparkle(
                box_x + random.uniform(0, panel_w), box_y + panel_h))
        for s in self._sparkles[:]:
            s.update(1 / 60)
            if s.life <= 0:
                self._sparkles.remove(s)
        if self._sparkles:
            sparkle_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for s in self._sparkles:
                s.draw(sparkle_surf)
            screen.blit(sparkle_surf, (0, 0))

    def update(self, dt):
        self._anim_time += dt
        self._launch_phase = min(1.0, self._launch_phase + dt * 1.2)
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

    def draw(self, screen):
        self.layout(screen)
        sw, sh = self._screen_size(screen)
        self.update(1 / 60)
        t = self._anim_time
        lp = ease_out_cubic(self._launch_phase)

        bg = cfg.bg.copy()
        if bg.get_size() != (sw, sh):
            bg = pygame.transform.scale(bg, (sw, sh))
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, max(0, min(255, int(180 + 50 * (1 - lp))))))
        bg.blit(overlay, (0, 0))
        screen.blit(bg, (0, 0))

        self._draw_background(screen, sw, sh, t, lp)
        self._draw_panel(screen, sw, sh, t, lp)

        for i, button in enumerate(self.buttons):
            btn_delay = 1.0 + i * 0.15
            btn_t = max(0, min(1.0, (t - btn_delay) / 0.5))
            if btn_t > 0:
                btn_eased = ease_out_back(btn_t)
                saved_y = button.rect.y
                button.rect.y = int(saved_y + (1 - btn_eased) * 40)
                button.draw(screen)
                button.rect.y = saved_y

        ver_t = max(0, min(1.0, (t - 2.5) / 0.5))
        if ver_t > 0:
            ver_s = self.font_small.render("v0.1.0 \u2014 Codex Arcanum", True, (150, 135, 105))
            ver_s.set_alpha(int(120 * ease_out_cubic(ver_t)))
            vs = cfg.ui_scale()
            screen.blit(ver_s, ((sw - ver_s.get_width()) // 2, sh - int(20 * vs)))

        if lp < 1.0:
            ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
            ov.fill((0, 0, 0, max(0, min(255, int(255 * (1.0 - lp))))))
            screen.blit(ov, (0, 0))

    def handle_event(self, event):
        super().handle_event(event)
        self.audio_slider.handle_event(event)
        self.brightness_slider.handle_event(event)

    def back_to_main(self):
        self.app.manager.set_state("main")

    def toggle_display_mode(self):
        self.app.toggle_display_mode()
        self.buttons[0].set_text(self._display_mode_label())

    def toggle_language(self):
        new_lang = 'ua' if cfg.LANGUAGE == 'en' else 'en'
        self.app.update_language(new_lang)
