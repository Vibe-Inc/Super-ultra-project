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


class AchievementsMenu(Menu):
    """
    Achievements screen displaying all global achievements and their unlock status.

    Features scrolling list of achievements and animated background effects.
    """

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

        self._title_font = cfg.get_font(max(20, int(70 * scale)))
        self._name_font = cfg.get_font(max(16, int(40 * scale)))
        self._desc_font = cfg.get_font(max(14, int(24 * scale)))
        self.font_small = cfg.get_font(max(12, int(18 * scale)))

        self._anim_time = 0.0
        self._launch_phase = 0.0
        self._particles = []
        self._stars = []
        self._light_rays = []
        self._embers = []
        self._bursts = []
        self._sparkles = []
        self._surf_cache = {}
        
        self.scroll_y = 0
        self.max_scroll = 0

    def on_enter(self):
        self._anim_time = 0.0
        self._launch_phase = 0.0
        self._bursts.clear()
        self._sparkles.clear()
        sw, sh = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT
        
        self.scroll_y = 0

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

    def _draw_badge(self, surface, cx, cy, size, alpha, t, is_unlocked):
        if not is_unlocked:
            # Draw locked lock
            pygame.draw.circle(surface, (50, 50, 50, alpha), (cx, cy), size // 2)
            pygame.draw.rect(surface, (80, 80, 80, alpha), (cx - size//6, cy - size//6, size//3, size//3), border_radius=2)
            pygame.draw.circle(surface, (80, 80, 80, alpha), (cx, cy - size//6), size//6, width=2)
            return

        # Animate the badge slightly
        bob = math.sin(t * 3.0 + cx) * 3
        cy += int(bob)

        # Draw ribbons
        ribbon_color = (220, 50, 50, alpha)
        ribbon_dark = (180, 30, 30, alpha)
        rw = size // 2.5
        rh = size // 1.2
        
        # left ribbon
        pygame.draw.polygon(surface, ribbon_color, [
            (cx - rw//1.5, cy), (cx - rw, cy + rh), (cx - rw//1.5, cy + rh - size//8), (cx - rw//3, cy + rh), (cx - rw//3, cy)
        ])
        # right ribbon
        pygame.draw.polygon(surface, ribbon_dark, [
            (cx + rw//3, cy), (cx + rw//1.5, cy + rh), (cx + rw//3, cy + rh - size//8), (cx + rw, cy + rh), (cx + rw//1.5, cy)
        ])
        
        # Draw gold sunburst seal
        gold_points = []
        rays = 16
        rot = t * 0.5  # slowly spin
        for i in range(rays * 2):
            r = size // 2 if i % 2 == 0 else size // 2.5
            angle = i * math.pi / rays + rot
            gold_points.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        
        pygame.draw.polygon(surface, (255, 215, 0, alpha), gold_points)
        pygame.draw.polygon(surface, (218, 165, 32, alpha), gold_points, max(1, int(size / 15)))
        
        # Inner circle
        pygame.draw.circle(surface, (255, 250, 220, alpha), (cx, cy), size // 3)
        pygame.draw.circle(surface, (255, 215, 0, alpha), (cx, cy), size // 3, max(1, int(size / 15)))
        
        # Cute star inside
        star_points = []
        star_rot = -t * 1.0
        for i in range(10):
            r = size // 4.5 if i % 2 == 0 else size // 10
            angle = i * math.pi / 5 - math.pi / 2 + star_rot
            star_points.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        pygame.draw.polygon(surface, (255, 140, 0, alpha), star_points)

    def _draw_achievements_box(self, screen, sw, sh, t, lp):
        scale = cfg.ui_scale()
        
        pad_x = int(60 * scale)
        pad_y = int(40 * scale)
        gap = int(20 * scale)
        item_h = int(130 * scale)

        box_w = min(sw - int(100 * scale), int(1000 * scale))
        
        achievements = self.app.achievement_manager.get_all()
        num_items = len(achievements)
        
        list_h = num_items * item_h + (num_items - 1) * gap
        
        title_h = self._title_font.get_height()
        box_h = int(sh * 0.7)
        
        self.max_scroll = max(0, list_h - (box_h - pad_y * 2 - title_h - gap * 3))

        cx = sw // 2
        cy = int(sh * 0.45)
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

        title_text = _("ACHIEVEMENTS")
        title_s = self._title_font.render(title_text, True, GOLD_BRIGHT)
        title_s.set_alpha(box_alpha)
        title_x = box_x + (box_w - title_s.get_width()) // 2
        title_y = box_y + pad_y
        screen.blit(title_s, (title_x, title_y))

        div_y = title_y + title_h + gap
        div_w = box_w - pad_x * 2
        pygame.draw.line(screen, (*GOLD, max(0, min(100, box_alpha))),
                        (box_x + pad_x, div_y), (box_x + pad_x + div_w, div_y),
                        max(1, int(1.5 * scale)))

        # Content area mask for scrolling
        content_rect = pygame.Rect(box_x + pad_x, div_y + gap, div_w, box_h - pad_y - title_h - gap * 2)
        
        prev_clip = screen.get_clip()
        screen.set_clip(content_rect)
        
        current_y = content_rect.y - self.scroll_y
        
        for i, ach in enumerate(achievements):
            if current_y + item_h < content_rect.top:
                current_y += item_h + gap
                continue
            if current_y > content_rect.bottom:
                break
                
            line_delay = 0.5 + i * 0.1
            line_t = max(0, min(1.0, (t - line_delay) / 0.4))
            
            line_eased = ease_out_cubic(line_t)
            line_alpha = int(255 * line_eased * (box_alpha / 255.0))
            line_offset = int((1.0 - line_eased) * 20)
            
            item_rect = pygame.Rect(content_rect.x, current_y + line_offset, content_rect.width, item_h)
            
            # Draw achievement item background
            bg_color = (30, 25, 45, max(0, min(180, line_alpha))) if ach.unlocked else (20, 15, 25, max(0, min(120, line_alpha)))
            border_color = (*GOLD_BRIGHT, max(0, min(200, line_alpha))) if ach.unlocked else (*GOLD_DARK, max(0, min(100, line_alpha)))
            
            item_surf = pygame.Surface((item_rect.width, item_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(item_surf, bg_color, (0, 0, item_rect.width, item_rect.height), border_radius=int(8*scale))
            pygame.draw.rect(item_surf, border_color, (0, 0, item_rect.width, item_rect.height), width=max(1, int(2*scale)), border_radius=int(8*scale))
            
            # Draw badge onto item_surf
            icon_size = int(70 * scale)
            icon_cx = int(60 * scale)
            icon_cy = item_h // 2
            
            self._draw_badge(item_surf, icon_cx, icon_cy, icon_size, line_alpha, t + i*0.2, ach.unlocked)
            
            # Draw text onto item_surf
            text_x = icon_cx + int(60 * scale)
            
            name_color = GOLD_BRIGHT if ach.unlocked else (150, 150, 150)
            name_s = self._name_font.render(ach.name if ach.unlocked or True else "???", True, name_color)
            name_s.set_alpha(line_alpha)
            item_surf.blit(name_s, (text_x, int(15 * scale)))
            
            desc_color = (210, 205, 195) if ach.unlocked else (100, 100, 100)
            desc_text = ach.description if ach.unlocked else _("Keep playing to reveal this achievement.")
            desc_s = self._desc_font.render(desc_text, True, desc_color)
            desc_s.set_alpha(line_alpha)
            item_surf.blit(desc_s, (text_x, int(50 * scale)))
            
            # Progress bar
            if ach.max_progress > 1:
                pb_w = item_rect.width - text_x - int(30 * scale)
                pb_h = int(14 * scale)
                pb_x = text_x
                pb_y = item_h - int(30 * scale)
                
                # Background
                pygame.draw.rect(item_surf, (40, 35, 50, line_alpha), (pb_x, pb_y, pb_w, pb_h), border_radius=pb_h//2)
                
                # Fill
                fill_pct = min(1.0, ach.progress / ach.max_progress)
                if fill_pct > 0:
                    fill_w = max(pb_h, int(pb_w * fill_pct))
                    fill_color = (100, 200, 100, line_alpha) if ach.unlocked else (200, 150, 50, line_alpha)
                    pygame.draw.rect(item_surf, fill_color, (pb_x, pb_y, fill_w, pb_h), border_radius=pb_h//2)
                
                # Text
                prog_str = f"{ach.progress} / {ach.max_progress}"
                prog_s = self.font_small.render(prog_str, True, (255, 255, 255, line_alpha))
                item_surf.blit(prog_s, (pb_x + pb_w // 2 - prog_s.get_width() // 2, pb_y - int(1 * scale)))
            
            # Blit the entire item surface
            screen.blit(item_surf, item_rect)
            
            current_y += item_h + gap

        screen.set_clip(prev_clip)

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
        self._draw_achievements_box(screen, sw, sh, t, lp)

        for i, button in enumerate(self.buttons):
            btn_delay = 1.0
            btn_t = max(0, min(1.0, (t - btn_delay) / 0.5))
            if btn_t > 0:
                btn_eased = ease_out_back(btn_t)
                saved_y = button.rect.y
                button.rect.y = int(saved_y + (1 - btn_eased) * 40)
                button.draw(screen)
                button.rect.y = saved_y

        if lp < 1.0:
            ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
            ov.fill((0, 0, 0, max(0, min(255, int(255 * (1.0 - lp))))))
            screen.blit(ov, (0, 0))
            
    def handle_event(self, event):
        super().handle_event(event)
        
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * 30
            self.scroll_y = max(0, min(self.max_scroll, self.scroll_y))
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.back_to_main()
            elif event.key == pygame.K_UP:
                self.scroll_y -= 40
                self.scroll_y = max(0, min(self.max_scroll, self.scroll_y))
            elif event.key == pygame.K_DOWN:
                self.scroll_y += 40
                self.scroll_y = max(0, min(self.max_scroll, self.scroll_y))

    def back_to_main(self):
        self.app.manager.set_state("main")
