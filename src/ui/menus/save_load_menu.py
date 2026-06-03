import math
import random
import pygame
from typing import TYPE_CHECKING
from gettext import gettext as _

from src.ui.menus.base import Menu
from src.ui.widgets import Button
from src.ui.effects import (
    GOLD, GOLD_BRIGHT, GOLD_DARK,
    ease_out_cubic, ease_out_elastic,
    Star, LightRay, AmbientEmber, FloatingOrb, LaunchBurst,
    TitleSparkle,
)
from src.core.save_manager import SaveManager
import src.config as cfg

if TYPE_CHECKING:
    from src.app import App

EMPTY_BTN = (55, 50, 70)
EMPTY_BTN_HOVER = (75, 68, 92)
USED_BTN = (130, 95, 25)
USED_BTN_HOVER = (160, 120, 40)
DEL_BTN = (130, 25, 25)
DEL_BTN_HOVER = (170, 35, 35)


class SaveLoadMenu(Menu):
    def __init__(self, app: "App"):
        super().__init__(app)
        self.mode = "save"
        self.slots = ["save1", "save2", "save3"]

        self.refresh_saves()

        self._panel_rect = pygame.Rect(0, 0, 0, 0)
        self._anim_time = 0.0
        self._launch_phase = 0.0
        self._surf_cache = {}
        self._particles = []
        self._stars = []
        self._light_rays = []
        self._embers = []
        self._bursts = []
        self._sparkles = []

    def refresh_saves(self):
        self.buttons = []
        scale = cfg.ui_scale()
        btn_w = max(1, int(360 * scale))
        btn_h = max(1, int(100 * scale))
        del_w = max(1, int(100 * scale))
        back_w = max(1, int(360 * scale))

        self._btn_w = btn_w
        self._btn_h = btn_h
        self._del_w = del_w
        self._back_w = back_w
        self._title_font = cfg.get_font(max(20, int(72 * scale)))
        self._hint_font = cfg.get_font(max(12, int(24 * scale)))

        self._slot_btn_indices = []
        self._del_btn_indices = []

        for i, slot in enumerate(self.slots):
            exists = slot + ".json" in SaveManager.get_save_files()
            label = f"{_('Slot')} {i+1}"
            if exists:
                label += f" ({_('Used')})"
            else:
                label += f" ({_('Empty')})"

            self._slot_btn_indices.append(len(self.buttons))
            self.buttons.append(Button(
                pygame.Rect(0, 0, btn_w, btn_h),
                label,
                USED_BTN if exists else EMPTY_BTN,
                USED_BTN_HOVER if exists else EMPTY_BTN_HOVER,
                cfg.button_font,
                GOLD_BRIGHT if exists else (180, 170, 200),
                cfg.corner_radius,
                on_click=lambda s=slot: self.on_slot_click(s),
                shape='shield',
            ))

            if exists:
                self._del_btn_indices.append(len(self.buttons))
                self.buttons.append(Button(
                    pygame.Rect(0, 0, del_w, btn_h),
                    _("DEL"),
                    DEL_BTN,
                    DEL_BTN_HOVER,
                    cfg.button_font,
                    (255, 200, 200),
                    cfg.corner_radius,
                    on_click=lambda s=slot: self.delete_slot(s),
                    shape='shield',
                ))
            else:
                self._del_btn_indices.append(None)

        self._back_idx = len(self.buttons)
        self.buttons.append(Button(
            pygame.Rect(0, 0, back_w, btn_h),
            _("BACK"),
            GOLD_DARK,
            GOLD,
            cfg.button_font,
            GOLD_BRIGHT,
            cfg.corner_radius,
            on_click=self.go_back,
            shape='shield',
        ))

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
        btn_w = self._btn_w
        btn_h = self._btn_h
        del_w = self._del_w
        back_w = self._back_w

        for btn_idx in self._slot_btn_indices:
            try:
                self.buttons[btn_idx]._update_text_surface()
            except Exception:
                pass
        for btn_idx in self._del_btn_indices:
            if btn_idx is not None:
                try:
                    self.buttons[btn_idx]._update_text_surface()
                except Exception:
                    pass
        try:
            self.buttons[self._back_idx]._update_text_surface()
        except Exception:
            pass

        panel_cx = sw // 2
        panel_cy = int(sh * 0.52)
        panel_w = int(880 * scale)
        pad_x = int(60 * scale)
        pad_y = int(50 * scale)
        gap = int(14 * scale)

        title_h = self._title_font.get_height()
        row_h = btn_h
        slot_count = len(self.slots)
        panel_h = pad_y * 2 + title_h + gap * 11 + row_h * slot_count + row_h

        box_x = panel_cx - panel_w // 2
        box_y = panel_cy - panel_h // 2
        self._panel_rect = pygame.Rect(box_x, box_y, panel_w, panel_h)

        left_col_x = box_x + pad_x
        right_col_x = box_x + panel_w - pad_x - del_w

        body_anchor = box_y + pad_y + title_h + gap + gap * 2

        for i in range(slot_count):
            row_y = body_anchor + i * (row_h + gap * 2)

            self.buttons[self._slot_btn_indices[i]].rect = (
                pygame.Rect(left_col_x, row_y, btn_w, row_h))

            del_idx = self._del_btn_indices[i]
            if del_idx is not None:
                self.buttons[del_idx].rect = (
                    pygame.Rect(right_col_x, row_y, del_w, row_h))

        back_y = (body_anchor + slot_count * (row_h + gap * 2)
                  + gap * 2)
        self.buttons[self._back_idx].rect = pygame.Rect(
            box_x + (panel_w - back_w) // 2, back_y, back_w, row_h)

    def on_slot_click(self, slot_name):
        if self.mode == "save":
            SaveManager.save_game(self.app, slot_name)
            self.refresh_saves()
        elif self.mode == "load":
            if SaveManager.load_game(self.app, slot_name):
                self.app.manager.set_state("gameplay")

    def delete_slot(self, slot_name):
        SaveManager.delete_save(slot_name)
        self.refresh_saves()

    def go_back(self):
        if self.mode == "save":
            self.app.manager.set_state("pause")
        else:
            self.app.manager.set_state("main")

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
        star_surf = self._get_surf("star", sw, sh)
        for star in self._stars:
            star.draw(star_surf, t)
        screen.blit(star_surf, (0, 0))

        ray_surf = self._get_surf("ray", sw, sh)
        for ray in self._light_rays:
            ray.draw(ray_surf, t)
        screen.blit(ray_surf, (0, 0))

        wash = self._get_surf("wash", sw, sh)
        wash_a = int(10 + 6 * math.sin(t * 0.35))
        wash_phase = t * 0.15
        wr = int(sw * 0.35)
        wg_cx = int(sw * 0.5 + math.cos(wash_phase) * sw * 0.12)
        wg_cy = int(sh * 0.4 + math.sin(wash_phase * 0.6) * sh * 0.08)
        wg = self._get_surf("wg", wr * 2, wr * 2)
        pygame.draw.circle(wg, (255, 200, 80, max(0, min(25, wash_a))), (wr, wr), wr)
        wash.blit(wg, (wg_cx - wr, wg_cy - wr))
        wg2 = self._get_surf("wg2", wr, wr)
        pygame.draw.circle(wg2, (140, 100, 255, max(0, min(15, wash_a - 3))),
                          (wr // 2, wr // 2), wr // 2)
        wash.blit(wg2, (int(sw * 0.6) - wr // 2, int(sh * 0.6) - wr // 2))
        screen.blit(wash, (0, 0))

        orb_surf = self._get_surf("orb", sw, sh)
        for p in self._particles:
            p.draw(orb_surf, t)
        screen.blit(orb_surf, (0, 0))

        ember_surf = self._get_surf("ember", sw, sh)
        for e in self._embers:
            e.draw(ember_surf, t)
        screen.blit(ember_surf, (0, 0))

        if lp < 1.0:
            burst_surf = self._get_surf("burst", sw, sh)
            for b in self._bursts:
                b.draw(burst_surf)
            screen.blit(burst_surf, (0, 0))

    def _draw_panel(self, screen, sw, sh, t, box_x, box_y, panel_w, panel_h):
        scale = cfg.ui_scale()
        gap = int(14 * scale)
        pad_x = int(60 * scale)
        pad_y = int(50 * scale)

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
        title_s = self._title_font.render(
            _("SAVE GAME") if self.mode == "save" else _("LOAD GAME"), True, GOLD_BRIGHT)
        title_s.set_alpha(box_alpha)
        screen.blit(title_s, (box_x + pad_x, title_y))

        div_y = title_y + self._title_font.get_height() + gap
        div_w = panel_w - pad_x * 2
        pygame.draw.line(screen, (*GOLD, max(0, min(100, box_alpha))),
                        (box_x + pad_x, div_y),
                        (box_x + pad_x + div_w, div_y),
                        max(1, int(1.5 * scale)))
        d_phase = t * 2.0
        d_cx = box_x + pad_x + div_w // 2
        d_ds = max(2, int(5 * scale * (0.8 + 0.2 * math.sin(d_phase))))
        d_pts = [(d_cx, div_y - d_ds), (d_cx + d_ds, div_y),
                 (d_cx, div_y + d_ds), (d_cx - d_ds, div_y)]
        pygame.draw.polygon(screen, (*GOLD_BRIGHT, max(0, min(180, box_alpha))), d_pts)

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
        self.update(1 / 60)
        sw, sh = self._screen_size(screen)
        t = self._anim_time

        self._draw_background(screen, sw, sh, t, self._launch_phase)

        if self._panel_rect.width > 0:
            self._draw_panel(
                screen, sw, sh, t,
                self._panel_rect.x, self._panel_rect.y,
                self._panel_rect.width, self._panel_rect.height)

        super().draw(screen)

        if random.random() < 0.15:
            self._sparkles.append(TitleSparkle(
                self._panel_rect.x + random.uniform(0, self._panel_rect.width),
                self._panel_rect.y + self._panel_rect.height))
        for s in self._sparkles[:]:
            s.update(1 / 60)
            if s.life <= 0:
                self._sparkles.remove(s)
        if self._sparkles:
            sparkle_surf = self._get_surf("sparkle", sw, sh)
            for s in self._sparkles:
                s.draw(sparkle_surf)
            screen.blit(sparkle_surf, (0, 0))
