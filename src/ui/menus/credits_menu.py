import math
import random
import pygame
from typing import TYPE_CHECKING
from gettext import gettext as _

from src.ui.menus.base import Menu
from src.ui.widgets import Button
from src.ui.effects import (
    GOLD, GOLD_BRIGHT, GOLD_DARK,
    ease_out_back, ease_out_cubic,
    Star, LightRay, AmbientEmber, FloatingOrb, LaunchBurst,
    TitleSparkle,
)
import src.config as cfg

if TYPE_CHECKING:
    from src.app import App


class CreditsMenu(Menu):
    def __init__(self, app: "App"):
        super().__init__(app)
        scale = cfg.ui_scale()

        btn_w, btn_h = max(1, int(300 * scale)), max(1, int(95 * scale))
        back_rect = pygame.Rect(0, 0, btn_w, btn_h)
        self.buttons = [
            Button(back_rect,
                _("BACK"),
                cfg.button_color_SETTINGS_BACK,
                cfg.button_hover_color_SETTINGS_BACK,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.back_to_main,
                shape='shield',
            )
        ]

        self.credits_text = _("""CREDITS:
Vibe inc idea, production and execution
Art not by Vibe inc
Music not by Vibe inc
Main sponsor: Vibe inc
Special thanks to Vibe inc""")

        self._title_font = cfg.get_font(max(20, int(80 * scale)))
        self._line_font = cfg.get_font(max(16, int(52 * scale)))
        self.font_small = cfg.get_font(max(12, int(18 * scale)))

        self.credits_lines = self.credits_text.split('\n')

        self._anim_time = 0.0
        self._launch_phase = 0.0
        self._particles = []
        self._stars = []
        self._light_rays = []
        self._embers = []
        self._bursts = []
        self._sparkles = []
        self._surf_cache = {}

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
        btn_w, btn_h = max(1, int(300 * scale)), max(1, int(95 * scale))
        self.buttons[0].rect = pygame.Rect(
            (sw - btn_w) // 2, int(sh * 0.85), btn_w, btn_h)
        try:
            self.buttons[0]._update_text_surface()
        except Exception:
            pass

    def _get_surf(self, name, sw, sh):
        key = (name, sw, sh)
        if key in self._surf_cache:
            surf = self._surf_cache[key]
            surf.fill((0, 0, 0, 0))
            return surf
        surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._surf_cache[key] = surf
        return surf

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

    def _draw_credits_box(self, screen, sw, sh, t, lp):
        scale = cfg.ui_scale()
        num_lines = len(self.credits_lines)
        line_h = self._line_font.get_height()
        title_h = self._title_font.get_height()

        max_line_w = max(
            (self._line_font.size(line)[0] for line in self.credits_lines[1:]),
            default=0
        )
        title_w = self._title_font.size(self.credits_lines[0])[0]
        max_w = max(max_line_w, title_w)

        pad_x = int(80 * scale)
        pad_y = int(50 * scale)
        gap = int(14 * scale)

        box_w = max_w + pad_x * 2
        box_h = pad_y * 2 + title_h + gap * 3 + line_h * (num_lines - 1)

        cx = sw // 2
        cy = int(sh * 0.40)
        box_x = cx - box_w // 2
        box_y = cy - box_h // 2

        box_delay = 0.3
        box_t = max(0, min(1.0, (t - box_delay) / 0.6))
        box_eased = ease_out_back(box_t)
        box_y_offset = int((1.0 - box_eased) * 80)
        box_y += box_y_offset

        box_alpha = int(255 * ease_out_cubic(box_t))
        if box_alpha < 5:
            return

        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)

        border_r = max(6, int(16 * scale))
        pygame.draw.rect(box_surf, (*GOLD_DARK, max(0, min(200, box_alpha))),
                        (0, 0, box_w, box_h), border_radius=border_r)

        inner = max(2, int(4 * scale))
        inner_r = max(4, border_r - inner)
        dark_bg = (12, 10, 22, max(0, min(240, box_alpha)))
        pygame.draw.rect(box_surf, dark_bg,
                        (inner, inner, box_w - inner * 2, box_h - inner * 2),
                        border_radius=inner_r)

        pygame.draw.rect(box_surf, (*GOLD, max(0, min(120, box_alpha))),
                        (inner * 2, inner * 2, box_w - inner * 4, box_h - inner * 4),
                        max(1, int(1.5 * scale)), border_radius=max(2, inner_r - inner))

        d_sz = max(2, int(5 * scale))
        corners = [(inner, inner), (box_w - inner, inner),
                   (inner, box_h - inner), (box_w - inner, box_h - inner)]
        for cx2, cy2 in corners:
            d_pts = [(cx2, cy2 - d_sz), (cx2 + d_sz, cy2),
                     (cx2, cy2 + d_sz), (cx2 - d_sz, cy2)]
            pygame.draw.polygon(box_surf, (*GOLD_BRIGHT, max(0, min(180, box_alpha))), d_pts)

        screen.blit(box_surf, (box_x, box_y))

        title_x = box_x + pad_x
        title_y = box_y + pad_y
        title_s = self._title_font.render(self.credits_lines[0], True, GOLD_BRIGHT)
        title_s.set_alpha(box_alpha)
        screen.blit(title_s, (title_x, title_y))

        div_y = title_y + title_h + gap
        div_w = box_w - pad_x * 2
        pygame.draw.line(screen, (*GOLD, max(0, min(100, box_alpha))),
                        (box_x + pad_x, div_y), (box_x + pad_x + div_w, div_y),
                        max(1, int(1.5 * scale)))

        d_phase = t * 2.0
        d_cx = box_x + pad_x + div_w // 2
        d_ds = max(2, int(5 * scale * (0.8 + 0.2 * math.sin(d_phase))))
        d_pts = [(d_cx, div_y - d_ds), (d_cx + d_ds, div_y),
                 (d_cx, div_y + d_ds), (d_cx - d_ds, div_y)]
        pygame.draw.polygon(screen, (*GOLD_BRIGHT, max(0, min(180, box_alpha))), d_pts)

        body_y = div_y + gap * 2
        for i, line in enumerate(self.credits_lines[1:], start=1):
            line_delay = 1.0 + i * 0.15
            line_t = max(0, min(1.0, (t - line_delay) / 0.4))
            if line_t <= 0:
                continue

            line_eased = ease_out_cubic(line_t)
            line_alpha = int(255 * line_eased)
            line_offset = int((1.0 - line_eased) * 20)

            ly = body_y + (i - 1) * line_h + line_offset

            bullet_sz = max(1, int(3 * scale))
            bl = box_x + pad_x + 10
            bcy = ly + line_h // 2
            pygame.draw.polygon(screen, (*GOLD, max(0, min(120, line_alpha))), [
                (bl, bcy - bullet_sz), (bl + bullet_sz, bcy),
                (bl, bcy + bullet_sz), (bl - bullet_sz, bcy),
            ])

            line_s = self._line_font.render(line, True, (210, 205, 195))
            line_s.set_alpha(line_alpha)
            screen.blit(line_s, (box_x + pad_x + 24, ly))

        if random.random() < 0.15:
            self._sparkles.append(TitleSparkle(
                box_x + random.uniform(0, box_w), box_y + box_h))
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
        overlay.fill((8, 6, 18, 140))
        bg.blit(overlay, (0, 0))
        screen.blit(bg, (0, 0))

        self._draw_background(screen, sw, sh, t, lp)
        self._draw_credits_box(screen, sw, sh, t, lp)

        for i, button in enumerate(self.buttons):
            btn_delay = 2.5
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
            scale = cfg.ui_scale()
            screen.blit(ver_s, ((sw - ver_s.get_width()) // 2, sh - int(20 * scale)))

        if lp < 1.0:
            ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
            ov.fill((0, 0, 0, max(0, min(255, int(255 * (1.0 - lp))))))
            screen.blit(ov, (0, 0))

    def back_to_main(self):
        self.app.manager.set_state("main")
