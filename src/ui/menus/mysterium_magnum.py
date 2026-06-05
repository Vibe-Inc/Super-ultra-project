import math
import random
import pygame
from typing import TYPE_CHECKING

from src.ui.menus.base import Menu
from src.ui.widgets import Button
import src.config as cfg

if TYPE_CHECKING:
    from src.app import App


class MysteriumMagnumMenu(Menu):
    def __init__(self, app: "App"):
        super().__init__(app)
        scale = cfg.ui_scale()
        self.title_font = cfg.get_font(max(16, int(40 * scale)))
        self.section_font = cfg.get_font(max(16, int(28 * scale)))
        self.small_font = cfg.get_font(max(14, int(20 * scale)))

        exit_width = max(120, int(200 * scale))
        exit_height = max(44, int(52 * scale))
        self.exit_button = Button(
            pygame.Rect(0, 0, exit_width, exit_height),
            _("BACK"),
            (110, 70, 70),
            (150, 95, 95),
            cfg.button_font,
            cfg.text_color,
            cfg.corner_radius,
            on_click=self.exit_menu,
        )
        self.buttons = [self.exit_button]

        self.tree_rect = pygame.Rect(0, 0, 0, 0)
        self.sidebar_rect = pygame.Rect(0, 0, 0, 0)
        self._layout_size = None

        self.animation_time = 0.0

        self.particles = []
        self._init_particles()

        self.pentagrams = []
        self._init_pentagrams()

        self.runes = []
        self._init_runes()

        self.magic_circles = []
        self._init_magic_circles()

        self._nebula_cache = None
        self._gradient_cache = {}

    def _init_particles(self):
        purple_gold = [
            (120, 50, 180), (180, 100, 220), (80, 30, 140),
            (212, 175, 55), (240, 210, 100), (150, 120, 50),
        ]
        for _ in range(80):
            self.particles.append({
                "x": random.uniform(-900, 900),
                "y": random.uniform(-700, 700),
                "size": random.uniform(1, 4),
                "speed_x": random.uniform(-0.2, 0.2),
                "speed_y": random.uniform(-0.4, -0.05),
                "alpha": random.uniform(0.15, 0.6),
                "pulse_speed": random.uniform(0.5, 2.5),
                "color": random.choice(purple_gold),
                "pulse_offset": random.uniform(0, math.pi * 2),
            })

    def _init_pentagrams(self):
        for _ in range(6):
            self.pentagrams.append({
                "x": random.uniform(-700, 700),
                "y": random.uniform(-600, 600),
                "size": random.uniform(30, 80),
                "rotation": random.uniform(0, math.pi * 2),
                "rot_speed": random.uniform(-0.15, 0.15),
                "alpha": random.uniform(0.08, 0.25),
                "pulse_speed": random.uniform(0.3, 0.8),
                "pulse_offset": random.uniform(0, math.pi * 2),
                "color": random.choice([(180, 120, 255), (212, 175, 55), (140, 60, 200)]),
            })

    def _init_runes(self):
        rune_symbols = [
            "ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ", "ᚷ", "ᚹ",
            "ᚺ", "ᚾ", "ᛁ", "ᛃ", "ᛇ", "ᛈ", "ᛉ", "ᛊ",
            "ᛏ", "ᛒ", "ᛖ", "ᛗ", "ᛚ", "ᛝ", "ᛟ", "ᛞ",
        ]
        for _ in range(20):
            self.runes.append({
                "x": random.uniform(-800, 800),
                "y": random.uniform(-650, 650),
                "symbol": random.choice(rune_symbols),
                "size": random.uniform(12, 28),
                "alpha": random.uniform(0.06, 0.2),
                "pulse_speed": random.uniform(0.3, 1.0),
                "pulse_offset": random.uniform(0, math.pi * 2),
                "color": random.choice([(200, 170, 255), (255, 215, 100), (180, 100, 240)]),
            })

    def _init_magic_circles(self):
        for _ in range(4):
            self.magic_circles.append({
                "x": random.uniform(-500, 500),
                "y": random.uniform(-400, 400),
                "radius": random.uniform(60, 150),
                "rotation": random.uniform(0, math.pi * 2),
                "rot_speed": random.uniform(-0.08, 0.08),
                "alpha": random.uniform(0.06, 0.15),
                "pulse_speed": random.uniform(0.2, 0.6),
                "pulse_offset": random.uniform(0, math.pi * 2),
                "color": random.choice([(140, 80, 220), (212, 175, 55), (80, 40, 160)]),
                "ring_count": random.randint(2, 4),
            })

    def exit_menu(self):
        try:
            self.app.INV_manager._return_held_item()
        except Exception:
            pass
        self.app.manager.set_state("gameplay")

    def layout(self, screen):
        sw, sh = screen.get_size()
        scale = cfg.ui_scale()
        margin = max(12, int(24 * scale))
        sidebar_width = min(max(240, int(360 * scale)), max(240, sw // 3))
        tree_width = max(240, sw - sidebar_width - margin * 3)
        self.sidebar_rect = pygame.Rect(sw - sidebar_width - margin, margin, sidebar_width, sh - margin * 2)
        self.tree_rect = pygame.Rect(margin, margin, tree_width, sh - margin * 2)

        exit_width = max(120, int(self.sidebar_rect.width * 0.6))
        exit_height = max(44, int(52 * scale))
        self.exit_button.rect = pygame.Rect(
            self.sidebar_rect.centerx - exit_width // 2,
            self.sidebar_rect.bottom - exit_height - margin,
            exit_width,
            exit_height,
        )
        try:
            self.exit_button._update_text_surface()
        except Exception:
            pass

        size = (sw, sh)
        if self._layout_size != size:
            self._layout_size = size
            self._nebula_cache = None
            self._gradient_cache.clear()

    def on_enter(self):
        pass

    def update(self, dt):
        dt = min(0.05, dt)
        self.animation_time += dt

        for p in self.particles:
            p["x"] += p["speed_x"] * dt * 60
            p["y"] += p["speed_y"] * dt * 60
            if p["y"] < -700:
                p["y"] = 700
                p["x"] = random.uniform(-900, 900)
            if p["x"] < -950:
                p["x"] = 950
            elif p["x"] > 950:
                p["x"] = -950

        for p in self.pentagrams:
            p["rotation"] += p["rot_speed"] * dt

        for c in self.magic_circles:
            c["rotation"] += c["rot_speed"] * dt

    def handle_event(self, event):
        super().handle_event(event)

    def _draw_gradient_rect(self, surface, rect, color_top, color_bottom, border_radius=0):
        cache_key = (rect.width, rect.height, color_top, color_bottom, border_radius)
        if cache_key in self._gradient_cache:
            temp = self._gradient_cache[cache_key]
        else:
            height = rect.height
            temp = pygame.Surface((rect.width, height), pygame.SRCALPHA)
            for y in range(height):
                t = y / max(1, height - 1)
                r = int(color_top[0] + (color_bottom[0] - color_top[0]) * t)
                g = int(color_top[1] + (color_bottom[1] - color_top[1]) * t)
                b = int(color_top[2] + (color_bottom[2] - color_top[2]) * t)
                pygame.draw.line(temp, (r, g, b), (0, y), (rect.width, y))
            if border_radius > 0:
                mask = pygame.Surface((rect.width, height), pygame.SRCALPHA)
                mask.fill((0, 0, 0, 0))
                pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, rect.width, height), border_radius=border_radius)
                temp.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            self._gradient_cache[cache_key] = temp
        surface.blit(temp, rect)

    def _draw_pentagram(self, surface, cx, cy, size, rotation, color, alpha):
        points = []
        for i in range(5):
            angle = rotation + i * 2 * math.pi / 5 - math.pi / 2
            points.append((cx + math.cos(angle) * size, cy + math.sin(angle) * size))
        for i in range(5):
            a = points[i]
            b = points[(i + 2) % 5]
            pygame.draw.line(surface, (*color, int(alpha * 255)), a, b, max(1, int(1.5)))
        outer_pts = points
        pygame.draw.polygon(surface, (*color, int(alpha * 150)), outer_pts, width=1)
        circle_r = size * 1.3
        pygame.draw.circle(surface, (*color, int(alpha * 120)), (cx, cy), int(circle_r), 1)

    def _draw_magic_circle(self, surface, cx, cy, radius, rotation, color, alpha, ring_count):
        for i in range(ring_count):
            r = int(radius * (1.0 - i * 0.25))
            a = int(alpha * 255 * (1.0 - i * 0.15))
            pygame.draw.circle(surface, (*color, a), (cx, cy), r, 1)
            dot_count = 8 + i * 4
            for j in range(dot_count):
                angle = rotation + j * 2 * math.pi / dot_count
                dx = cx + math.cos(angle) * r
                dy = cy + math.sin(angle) * r
                dot_a = int(a * (0.5 + 0.5 * math.sin(self.animation_time * 2 + j)))
                pygame.draw.circle(surface, (*color, dot_a), (int(dx), int(dy)), max(1, int(1.5)))

    def _draw_background(self, surface):
        origin = pygame.Vector2(self.tree_rect.center)
        bg_origin = pygame.Vector2(self.tree_rect.center)
        t = self.animation_time

        if self._nebula_cache is None:
            nebula_colors = [
                (18, 5, 30), (25, 8, 40), (15, 5, 25), (30, 10, 35),
                (20, 8, 28), (10, 5, 20), (28, 8, 38), (22, 6, 32),
            ]
            nebula_centers = [
                (0.3, 0.4), (0.7, 0.3), (0.5, 0.7), (0.2, 0.6),
                (0.8, 0.6), (0.4, 0.8), (0.6, 0.2), (0.3, 0.5),
            ]
            neb_w = self.tree_rect.width
            neb_h = self.tree_rect.height
            n_surf = pygame.Surface((neb_w, neb_h), pygame.SRCALPHA)
            for y in range(0, neb_h, 3):
                for x in range(0, neb_w, 3):
                    blend_r, blend_g, blend_b = 0, 0, 0
                    total = 0
                    for nc, (nx, ny) in zip(nebula_colors, nebula_centers):
                        dx2 = x / neb_w - nx
                        dy2 = y / neb_h - ny
                        dist = math.sqrt(dx2 * dx2 + dy2 * dy2) * 3.0
                        if dist < 1.5:
                            w = (1.0 - dist / 1.5) * 0.4
                            blend_r += nc[0] * w
                            blend_g += nc[1] * w
                            blend_b += nc[2] * w
                            total += w
                    if total > 0:
                        r2 = int(min(255, blend_r / total))
                        g2 = int(min(255, blend_g / total))
                        b2 = int(min(255, blend_b / total))
                        n_surf.set_at((x, y), (r2, g2, b2, 140))
            self._nebula_cache = n_surf

        surface.blit(self._nebula_cache, (self.tree_rect.x, self.tree_rect.y))

        for r in range(800, 0, -40):
            brightness = max(5, 16 - r // 80)
            pygame.draw.circle(surface, (brightness, brightness, brightness + 5), origin, r, 0)

        for pent in self.pentagrams:
            px = bg_origin.x + pent["x"]
            py = bg_origin.y + pent["y"]
            if self.tree_rect.collidepoint(px, py):
                pulse = (math.sin(t * pent["pulse_speed"] + pent["pulse_offset"]) + 1.0) * 0.5
                a = pent["alpha"] * (0.5 + 0.5 * pulse)
                sz = pent["size"] * (0.9 + 0.1 * pulse)
                self._draw_pentagram(surface, int(px), int(py), sz, pent["rotation"], pent["color"], a)

        for r_data in self.runes:
            rx = bg_origin.x + r_data["x"]
            ry = bg_origin.y + r_data["y"]
            if self.tree_rect.collidepoint(rx, ry):
                pulse = (math.sin(t * r_data["pulse_speed"] + r_data["pulse_offset"]) + 1.0) * 0.5
                a = r_data["alpha"] * (0.4 + 0.6 * pulse)
                if a > 0.02:
                    font = cfg.get_font(max(10, int(r_data["size"])))
                    glyph = font.render(r_data["symbol"], True, r_data["color"])
                    glyph.set_alpha(int(a * 255))
                    rect = glyph.get_rect(center=(int(rx), int(ry)))
                    surface.blit(glyph, rect)

        for c in self.magic_circles:
            cx = bg_origin.x + c["x"]
            cy = bg_origin.y + c["y"]
            if self.tree_rect.collidepoint(cx, cy):
                pulse = (math.sin(t * c["pulse_speed"] + c["pulse_offset"]) + 1.0) * 0.5
                a = c["alpha"] * (0.5 + 0.5 * pulse)
                r = c["radius"] * (0.9 + 0.1 * pulse)
                self._draw_magic_circle(surface, int(cx), int(cy), r, c["rotation"], c["color"], a, c["ring_count"])

        for p in self.particles:
            px = bg_origin.x + p["x"]
            py = bg_origin.y + p["y"]
            if self.tree_rect.collidepoint(px, py):
                pulse = (math.sin(t * p["pulse_speed"] + p["pulse_offset"]) + 1.0) * 0.5
                alpha = p["alpha"] * (0.4 + 0.6 * pulse)
                r, g, b = p["color"]
                pcolor = (int(r * alpha), int(g * alpha), int(b * alpha))
                sz = max(1, int(p["size"] * (0.8 + 0.4 * pulse)))
                if alpha > 0.05:
                    pygame.draw.circle(surface, pcolor, (int(px), int(py)), sz)

    def _draw_sidebar(self, screen):
        r = self.sidebar_rect
        t = self.animation_time

        self._draw_gradient_rect(screen, r, (22, 10, 35), (10, 5, 20), border_radius=18)
        pygame.draw.rect(screen, (80, 55, 110), r, 2, border_radius=18)
        inner_border = r.inflate(-4, -4)
        pygame.draw.rect(screen, (55, 40, 75), inner_border, 1, border_radius=16)

        orn_len = 20
        orn_color = (180, 130, 220)
        for corner in [(r.x, r.y), (r.right, r.y), (r.x, r.bottom), (r.right, r.bottom)]:
            cx, cy = corner
            hor_dir = 1 if corner[0] == r.x else -1
            ver_dir = 1 if corner[1] == r.y else -1
            pygame.draw.line(screen, orn_color, (cx, cy), (cx + hor_dir * orn_len, cy), 2)
            pygame.draw.line(screen, orn_color, (cx, cy), (cx, cy + ver_dir * orn_len), 2)

        title_text = _("⟐ Mysterium Magnum ⟐")
        glow_a = int((math.sin(t * 1.5) + 1.0) * 60 + 60)
        for i in range(4):
            glow_surf = self.title_font.render(title_text, True, (140, 80, 220))
            glow_surf.set_alpha(glow_a // (i + 1))
            screen.blit(glow_surf, (r.x + 18 + i, r.y + 18 + i))
        title = self.title_font.render(title_text, True, (240, 220, 255))
        screen.blit(title, (r.x + 18, r.y + 18))

        div_y = r.y + 18 + title.get_height() + 12
        for i in range(r.width - 36):
            x = r.x + 18 + i
            alpha = int((1.0 - abs(i / max(1, r.width - 36) - 0.5) * 2) * 120)
            pygame.draw.line(screen, (140, 80, 220, alpha), (x, div_y), (x, div_y + 1))

        hint_text = _("Secrets await within the cards...")
        hint = self.small_font.render(hint_text, True, (150, 140, 175))
        screen.blit(hint, (r.x + 18, div_y + 10))

        py = div_y + 10 + hint.get_height() + 24

        for i in range(r.width - 36):
            x = r.x + 18 + i
            alpha = int((1.0 - abs(i / max(1, r.width - 36) - 0.5) * 2) * 80)
            pygame.draw.line(screen, (70, 40, 100, alpha), (x, py), (x, py + 1))
        py += 12

        stars = getattr(self.app, "purple_stars", 0)
        t = self.animation_time

        panel_w = r.width - 36
        panel_h = max(60, int(80 * cfg.ui_scale()))
        panel_rect = pygame.Rect(r.x + 18, py, panel_w, panel_h)
        pygame.draw.rect(screen, (18, 8, 32), panel_rect, border_radius=10)
        pygame.draw.rect(screen, (100, 60, 140), panel_rect, 2, border_radius=10)
        inner_panel = panel_rect.inflate(-4, -4)
        pygame.draw.rect(screen, (55, 35, 80), inner_panel, 1, border_radius=8)

        star_cx = panel_rect.x + int(panel_rect.width * 0.25)
        star_cy = panel_rect.centery
        star_outer_r = max(8, int(18 * cfg.ui_scale()))
        star_inner_r = int(star_outer_r * 0.35)
        star_pulse = (math.sin(t * 2.0) + 1.0) * 0.5
        star_rot = t * 0.5

        star_pts = []
        for i in range(8):
            angle = star_rot + i * math.pi / 4 - math.pi / 2
            r2 = star_outer_r if i % 2 == 0 else star_inner_r
            star_pts.append((star_cx + math.cos(angle) * r2, star_cy + math.sin(angle) * r2))

        glow_r = int(star_outer_r * 2.5)
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        glow_a = int(60 + 60 * star_pulse)
        pygame.draw.circle(glow_surf, (180, 80, 255, glow_a), (glow_r, glow_r), glow_r)
        screen.blit(glow_surf, (star_cx - glow_r, star_cy - glow_r))

        star_color = (
            int(180 + 40 * star_pulse),
            int(80 + 40 * star_pulse),
            int(255 - 40 * star_pulse),
        )
        pygame.draw.polygon(screen, star_color, star_pts)
        pygame.draw.polygon(screen, (220, 180, 255), star_pts, width=max(1, int(1.5 * cfg.ui_scale())))

        label_x = panel_rect.x + int(panel_rect.width * 0.45)
        label_y = panel_rect.y + int(10 * cfg.ui_scale())
        label = self.small_font.render(_("Purple Stars"), True, (200, 180, 220))
        screen.blit(label, (label_x, label_y))

        count_color = (
            int(220 + 35 * star_pulse),
            int(140 + 60 * star_pulse),
            int(255),
        )
        count_text = str(stars)
        count_surf = self.section_font.render(count_text, True, count_color)
        count_shadow = self.section_font.render(count_text, True, (0, 0, 0))
        count_x = label_x
        count_y = label_y + label.get_height() + 4
        screen.blit(count_shadow, (count_x + 2, count_y + 2))
        screen.blit(count_surf, (count_x, count_y))

        decor_r = max(2, int(3 * cfg.ui_scale()))
        for i in range(3):
            da = t * 1.5 + i * 2.094
            dx = panel_rect.right - int(12 * cfg.ui_scale())
            dy = panel_rect.centery + math.sin(da) * (panel_h * 0.25)
            dc = (180, 130, 255, int(80 + 80 * (math.sin(da) + 1) * 0.5))
            pygame.draw.circle(screen, dc[:3], (dx, int(dy)), decor_r)

    def draw(self, screen):
        self.layout(screen)
        raw_dt = 0.016
        try:
            raw_dt = self.app.clock.get_time() / 1000.0 if hasattr(self.app, 'clock') else 0.016
        except Exception:
            pass
        raw_dt = min(0.05, raw_dt)
        if not hasattr(self, '_smooth_dt'):
            self._smooth_dt = raw_dt
        self._smooth_dt = self._smooth_dt * 0.85 + raw_dt * 0.15
        dt = self._smooth_dt
        self.update(dt)

        screen.fill((5, 3, 12))

        pygame.draw.rect(screen, (12, 8, 22), self.tree_rect, border_radius=18)
        outer_border = (70, 45, 100)
        pygame.draw.rect(screen, outer_border, self.tree_rect, 2, border_radius=18)
        inner_rect = self.tree_rect.inflate(-4, -4)
        inner_border = (45, 30, 65)
        pygame.draw.rect(screen, inner_border, inner_rect, 1, border_radius=16)
        orn_len = 16
        orn_color = (160, 100, 210)
        tr = self.tree_rect
        for cx, cy, hdx, hdy in [(tr.x, tr.y, 1, 1), (tr.right, tr.y, -1, 1),
                                  (tr.x, tr.bottom, 1, -1), (tr.right, tr.bottom, -1, -1)]:
            pygame.draw.line(screen, orn_color, (cx, cy), (cx + hdx * orn_len, cy), 2)
            pygame.draw.line(screen, orn_color, (cx, cy), (cx, cy + hdy * orn_len), 2)

        old_clip = screen.get_clip()
        screen.set_clip(self.tree_rect)

        self._draw_background(screen)

        screen.set_clip(old_clip)

        self._draw_sidebar(screen)
        self.exit_button.draw(screen)
