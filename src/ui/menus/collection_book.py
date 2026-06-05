"""Fishing Field Journal — ornate empty book with an ocean theme.

A visual-only collection book that the player opens by talking to the
fishing NPC.  All fish entries and logic will be added in later steps;
right now the book shows empty parchment pages with water-themed
decorations, particles, and animations.
"""

import pygame
import math
import random
from src.ui.menus.base import Menu
from src.ui.widgets import Button
import src.config as cfg


# ---------------------------------------------------------------------------
# Particle
# ---------------------------------------------------------------------------

class _Particle:
    """A single particle for page-flip and ambient effects."""

    def __init__(self, x, y, vx, vy, lifetime, color, size, star=False):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.size = size
        self.star = star
        self.phase = random.uniform(0, math.pi * 2)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        self.vy += 40 * dt

    def draw(self, surf, offset=(0, 0)):
        if self.lifetime <= 0:
            return
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        progress = 1.0 - (self.lifetime / self.max_lifetime)
        sz = max(1, int(self.size * (1.0 - progress * 0.3)))
        px = int(self.x + offset[0])
        py = int(self.y + offset[1])

        if self.star:
            clr = (self.color[0], self.color[1], self.color[2], alpha)
            s = pygame.Surface((sz * 4, sz * 4), pygame.SRCALPHA)
            pts1 = [(sz * 2, 0), (sz * 2 + sz, sz * 2), (sz * 2, sz * 4 - 1), (sz * 2 - sz, sz * 2)]
            pts2 = [(0, sz * 2), (sz * 2, sz * 2 - sz), (sz * 4 - 1, sz * 2), (sz * 2, sz * 2 + sz)]
            pygame.draw.polygon(s, clr, pts1)
            pygame.draw.polygon(s, clr, pts2)
            surf.blit(s, (px - sz * 2, py - sz * 2))
        else:
            clr = tuple(int(c * (self.lifetime / self.max_lifetime)) for c in self.color[:3])
            if sz > 2:
                pygame.draw.circle(surf, clr, (px, py), sz, 1)
                hl = (min(255, clr[0] + 60), min(255, clr[1] + 60), min(255, clr[2] + 60))
                pygame.draw.circle(surf, hl, (px - sz // 3, py - sz // 3), max(1, sz // 4))
            else:
                pygame.draw.circle(surf, clr, (px, py), sz)


# ---------------------------------------------------------------------------
# Easing
# ---------------------------------------------------------------------------

def _ease_out_cubic(t):
    return 1.0 - math.pow(1.0 - t, 3)


# ---------------------------------------------------------------------------
# Collection Book Menu
# ---------------------------------------------------------------------------

class CollectionBookMenu(Menu):
    """An ornate ocean-themed field journal (empty for now).

    The book opens with an animation, shows blank parchment pages with
    water-themed decorations and bubble particles.  Fish entries will be
    added in a later step.
    """

    def __init__(self, app):
        super().__init__(app)
        self.book_magnifier = 1.35

        self.anim_start_time = pygame.time.get_ticks()
        self.anim_duration = 600
        self.is_opening = True

        self.flip_start_time = 0
        self.flip_duration = 300
        self.is_flipping = False

        self.current_spread = 0
        self.max_spreads = 3  # several empty spreads to flip through

        self.ambient_particles = []
        self.page_particles = []
        self.shine_phase = random.uniform(0, math.pi * 2)

        self.buttons = []
        self._setup_buttons()

    # -- Buttons --

    def _setup_buttons(self):
        self.buttons.clear()
        scale = cfg.ui_scale() * self.book_magnifier
        cx, cy = cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2
        book_w, book_h = int(860 * scale), int(600 * scale)
        btn_w, btn_h = int(120 * scale), int(36 * scale)

        # Position in the right-bottom corner of the right page
        back_x = cx + book_w // 2 - btn_w - int(30 * scale)
        back_y = cy + book_h // 2 - btn_h - int(30 * scale)
        back_rect = pygame.Rect(back_x, back_y, btn_w, btn_h)
        self.buttons.append(Button(
            back_rect, _("CLOSE"), cfg.button_color_EXIT, cfg.button_hover_color_EXIT,
            cfg.button_font, cfg.text_color, cfg.corner_radius, on_click=self.close_menu
        ))

        # Prev page button (left side of bottom)
        if self.current_spread > 0:
            prev_x = cx - book_w // 2 + int(30 * scale)
            prev_y = cy + book_h // 2 - btn_h - int(30 * scale)
            prev_rect = pygame.Rect(prev_x, prev_y, btn_w, btn_h)
            self.buttons.append(Button(
                prev_rect, _("<- PREV"), (30, 60, 90), (50, 90, 120),
                cfg.button_font, cfg.text_color, cfg.corner_radius, on_click=self.prev_page
            ))

        # Next page button (middle-right area)
        if self.current_spread < self.max_spreads - 1:
            next_x = cx + book_w // 2 - btn_w * 2 - int(40 * scale)
            next_y = cy + book_h // 2 - btn_h - int(30 * scale)
            next_rect = pygame.Rect(next_x, next_y, btn_w, btn_h)
            self.buttons.append(Button(
                next_rect, _("NEXT ->"), (30, 60, 90), (50, 90, 120),
                cfg.button_font, cfg.text_color, cfg.corner_radius, on_click=self.next_page
            ))

    def prev_page(self):
        if self.current_spread > 0 and not self.is_flipping:
            self.current_spread -= 1
            self._start_flip()

    def next_page(self):
        if self.current_spread < self.max_spreads - 1 and not self.is_flipping:
            self.current_spread += 1
            self._start_flip()

    def _start_flip(self):
        self.is_flipping = True
        self.flip_start_time = pygame.time.get_ticks()
        self._setup_buttons()
        self._emit_page_particles()

    def close_menu(self):
        self.app.manager.set_state("gameplay")

    # -- Particles --

    def _spawn_ambient_bubbles(self, dt):
        if random.random() < 0.18:
            scale = cfg.ui_scale() * self.book_magnifier
            cx, cy = cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2
            book_w, book_h = int(860 * scale), int(600 * scale)
            x = cx + random.randint(-book_w // 2, book_w // 2)
            y = cy + book_h // 2 + random.randint(0, int(40 * scale))
            vx = random.uniform(-12, 12)
            vy = random.uniform(-60, -20)
            lifetime = random.uniform(2.0, 4.5)
            colors = [(100, 180, 220, 90), (130, 200, 230, 70), (180, 220, 240, 50)]
            color = random.choice(colors)
            size = random.randint(2, 5)
            self.ambient_particles.append(_Particle(x, y, vx, vy, lifetime, color, size))

    def _emit_page_particles(self):
        scale = cfg.ui_scale() * self.book_magnifier
        cx, cy = cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2
        book_w, book_h = int(860 * scale), int(600 * scale)
        for _ in range(25):
            x = cx + random.randint(-book_w // 2, book_w // 2)
            y = cy + random.randint(-book_h // 2, book_h // 2)
            vx = random.uniform(-200, 200)
            vy = random.uniform(-350, -80)
            lifetime = random.uniform(0.4, 1.0)
            colors = [(100, 180, 220), (150, 200, 230), (80, 150, 190)]
            color = random.choice(colors)
            size = random.randint(2, 5)
            star = random.random() < 0.2
            self.page_particles.append(_Particle(x, y, vx, vy, lifetime, color, size, star=star))

    # -- Update --

    def update(self, dt=1 / 60):
        self._spawn_ambient_bubbles(dt)
        self.shine_phase += dt * 1.5
        self.ambient_particles = [p for p in self.ambient_particles if p.lifetime > 0]
        self.page_particles = [p for p in self.page_particles if p.lifetime > 0]
        for p in self.ambient_particles + self.page_particles:
            p.update(dt)

    # -- Events --

    def handle_event(self, event):
        if self.is_opening or self.is_flipping:
            return
        super().handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close_menu()
            elif event.key == pygame.K_LEFT:
                self.prev_page()
            elif event.key == pygame.K_RIGHT:
                self.next_page()

    # -- Drawing --

    def draw(self, screen):
        self.update()
        current_time = pygame.time.get_ticks()

        open_progress = 1.0
        if self.is_opening:
            t = (current_time - self.anim_start_time) / self.anim_duration
            if t >= 1.0:
                self.is_opening = False
                open_progress = 1.0
            else:
                open_progress = _ease_out_cubic(t)

        # Flip animation — fade content in/out
        content_alpha = 255
        if self.is_flipping:
            t = (current_time - self.flip_start_time) / self.flip_duration
            if t >= 1.0:
                self.is_flipping = False
                content_alpha = 255
            else:
                if t < 0.5:
                    content_alpha = int(255 * (1.0 - t * 2))
                else:
                    content_alpha = int(255 * ((t - 0.5) * 2))

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((5, 10, 20, int(180 * open_progress)))
        screen.blit(overlay, (0, 0))

        scale = cfg.ui_scale() * self.book_magnifier
        cx, cy = cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2
        book_w = int(860 * scale)
        book_h = int(600 * scale)
        y_offset = int((1.0 - open_progress) * 150 * scale)

        # Blue glow
        glow_size = max(book_w, book_h) + int(80 * scale)
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        pulse = (math.sin(current_time * 0.002) + 1) / 2
        glow_alpha = int(30 + pulse * 25)
        for r in range(glow_size // 2, 0, -1):
            a = int(glow_alpha * (1.0 - r / (glow_size // 2)))
            if a > 0:
                pygame.draw.circle(glow_surf, (80, 140, 180, a),
                                   (glow_size // 2, glow_size // 2), r)
        screen.blit(glow_surf, (cx - glow_size // 2, cy + y_offset - glow_size // 2))

        # Shadow
        shadow_surf = pygame.Surface(
            (book_w + int(40 * scale), book_h + int(20 * scale)), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 80),
                         (int(20 * scale), 0, book_w, book_h + int(10 * scale)),
                         border_radius=int(20 * scale))
        screen.blit(shadow_surf,
                    (cx - (book_w + int(40 * scale)) // 2,
                     cy + y_offset - book_h // 2 + int(8 * scale)))

        # Book
        book_surf = pygame.Surface((book_w, book_h), pygame.SRCALPHA)
        self._draw_book_background(book_surf, book_w, book_h, scale, current_time)
        self._draw_empty_pages(book_surf, book_w, book_h, scale, content_alpha)

        book_rect = book_surf.get_rect(center=(cx, cy + y_offset))
        if self.is_opening:
            book_surf.set_alpha(int(255 * open_progress))
        screen.blit(book_surf, book_rect.topleft)

        # Silver shine sweep
        shine_t = (current_time * 0.00025) % 1.0
        shine_x = int((shine_t - 0.3) * book_w * 1.4)
        if 0 < shine_x < book_w:
            shine_surf = pygame.Surface((int(100 * scale), book_h), pygame.SRCALPHA)
            for sx in range(shine_surf.get_width()):
                a = int(25 * (1.0 - abs(sx - shine_surf.get_width() / 2)
                              / (shine_surf.get_width() / 2)))
                if a > 0:
                    pygame.draw.line(shine_surf, (200, 220, 240, a), (sx, 0), (sx, book_h))
            screen.blit(shine_surf, (book_rect.x + shine_x, book_rect.y))

        # Particles
        for particle in self.ambient_particles:
            px = int(particle.x - cx + book_rect.centerx)
            py = int(particle.y - cy + book_rect.centery)
            if len(particle.color) == 4:
                a = int(particle.color[3] * (particle.lifetime / particle.max_lifetime))
                c = (particle.color[0], particle.color[1], particle.color[2])
                s = pygame.Surface((particle.size * 4, particle.size * 4), pygame.SRCALPHA)
                pygame.draw.circle(s, (*c, a),
                                   (particle.size * 2, particle.size * 2), particle.size)
                screen.blit(s, (px - particle.size * 2, py - particle.size * 2))
            else:
                particle.draw(screen, offset=(-cx + book_rect.centerx,
                                              -cy + book_rect.centery))

        for particle in self.page_particles:
            particle.draw(screen, offset=(-cx + book_rect.centerx,
                                          -cy + book_rect.centery))

        if not self.is_opening and not self.is_flipping:
            for button in self.buttons:
                button.draw(screen)

    # ------------------------------------------------------------------
    # Book background — deep ocean blue leather, silver borders
    # ------------------------------------------------------------------

    def _draw_book_background(self, surf, w, h, scale, current_time):
        cover_color = (15, 30, 55)
        pygame.draw.rect(surf, cover_color, (0, 0, w, h), border_radius=int(20 * scale))

        # Blue leather texture
        tex = pygame.Surface((w, h), pygame.SRCALPHA)
        for _ in range(1200):
            tx = random.randint(0, w - 1)
            ty = random.randint(0, h - 1)
            a = random.randint(3, 12)
            c = (10, 22, 45) if random.randint(0, 1) else (5, 15, 35)
            tex.set_at((tx, ty), (*c, a))
        surf.blit(tex, (0, 0))

        # Silver pulsing border
        pulse = (math.sin(current_time * 0.003) + 1) / 2
        silver_pulse = int(170 + pulse * 50)
        margin = int(7 * scale)
        silver_colors = [
            (silver_pulse, silver_pulse + 10, silver_pulse + 20),
            (180, 195, 210),
            (silver_pulse - 20, silver_pulse - 10, silver_pulse),
        ]
        for i, gc in enumerate(silver_colors):
            gc = tuple(max(0, min(255, c)) for c in gc)
            inset = margin + i * int(3 * scale)
            wd = 1 if i < 2 else max(1, int(2 * scale))
            pygame.draw.rect(surf, gc, (inset, inset, w - inset * 2, h - inset * 2),
                             width=wd, border_radius=int(18 * scale - i))

        # Wave corner ornaments
        corner_size = int(60 * scale)
        corners = [
            (margin + int(2 * scale), margin + int(2 * scale)),
            (w - margin - int(2 * scale) - corner_size, margin + int(2 * scale)),
            (margin + int(2 * scale), h - margin - int(2 * scale) - corner_size),
            (w - margin - int(2 * scale) - corner_size,
             h - margin - int(2 * scale) - corner_size),
        ]
        for x, y in corners:
            self._draw_wave_corner(surf, x, y, corner_size, scale, current_time)

        # Spine
        spine_w = int(48 * scale)
        spine_x = w // 2 - spine_w // 2
        spine_top = int(10 * scale)
        spine_bot = h - int(10 * scale)
        spine_shadow = pygame.Surface((spine_w, spine_bot - spine_top), pygame.SRCALPHA)
        for i in range(spine_w // 2):
            a = int(130 * (1.0 - (i / (spine_w // 2))))
            pygame.draw.line(spine_shadow, (0, 0, 0, a),
                             (i, 0), (i, spine_bot - spine_top), 1)
            pygame.draw.line(spine_shadow, (0, 0, 0, a),
                             (spine_w - i - 1, 0), (spine_w - i - 1, spine_bot - spine_top), 1)
        surf.blit(spine_shadow, (spine_x, spine_top))

        # Silver spine bands
        band_positions = [
            spine_top + int(25 * scale), spine_top + int(75 * scale),
            spine_bot - int(75 * scale), spine_bot - int(25 * scale),
        ]
        for by in band_positions:
            for bw in range(int(5 * scale)):
                band_color = (180, 195, 210) if bw % 2 == 0 else (140, 155, 175)
                if pulse > 0.5 and bw == 2:
                    band_color = (210, 225, 240)
                pygame.draw.line(surf, band_color,
                                 (spine_x + int(7 * scale), by + bw),
                                 (spine_x + spine_w - int(7 * scale), by + bw), 1)

        # Spine divider
        pygame.draw.line(surf, (100, 130, 160),
                         (w // 2, int(16 * scale)),
                         (w // 2, h - int(16 * scale)),
                         max(1, int(2 * scale)))

        # Spine gems — aquamarine + sea-green
        gem_y = (spine_top + spine_bot) // 2
        for gi, gcol in enumerate([(80, 200, 220), (40, 160, 120)]):
            gx = spine_x + int(spine_w * (0.25 + gi * 0.5))
            self._draw_gem(surf, gx,
                           gem_y + int((gi - 0.5) * 22 * scale),
                           int(6 * scale), gcol, scale)

        # Left page
        page_color = (235, 240, 250)
        page_margin = int(18 * scale)
        left_page = pygame.Rect(page_margin, page_margin,
                                w // 2 - page_margin, h - page_margin * 2)
        pygame.draw.rect(surf, page_color, left_page,
                         border_top_left_radius=int(14 * scale),
                         border_bottom_left_radius=int(14 * scale))
        gild = pygame.Surface((left_page.width, left_page.height), pygame.SRCALPHA)
        for x in range(left_page.width):
            a = int(8 * (x / left_page.width))
            pygame.draw.line(gild, (60, 80, 120, a), (x, 0), (x, left_page.height))
        surf.blit(gild, (left_page.x, left_page.y))

        # Right page
        right_page = pygame.Rect(w // 2, page_margin,
                                 w // 2 - page_margin, h - page_margin * 2)
        pygame.draw.rect(surf, page_color, right_page,
                         border_top_right_radius=int(14 * scale),
                         border_bottom_right_radius=int(14 * scale))
        gild_r = pygame.Surface((right_page.width, right_page.height), pygame.SRCALPHA)
        for x in range(right_page.width):
            a = int(8 * (1.0 - x / right_page.width))
            pygame.draw.line(gild_r, (60, 80, 120, a), (x, 0), (x, right_page.height))
        surf.blit(gild_r, (right_page.x, right_page.y))

        # Page borders — triple line
        border_color = (140, 160, 185)
        border_light = (160, 180, 205)
        for side in ['left', 'right']:
            bx = (page_margin + int(6 * scale) if side == 'left'
                  else w // 2 + int(6 * scale))
            by = page_margin + int(6 * scale)
            bw = w // 2 - page_margin - int(12 * scale)
            bh = h - page_margin * 2 - int(12 * scale)
            pygame.draw.rect(surf, border_color, (bx, by, bw, bh),
                             width=1, border_radius=int(8 * scale))
            inn = int(3 * scale)
            pygame.draw.rect(surf, border_light,
                             (bx + inn, by + inn, bw - inn * 2, bh - inn * 2),
                             width=1, border_radius=int(6 * scale))
            inn2 = int(6 * scale)
            pygame.draw.rect(surf, border_color,
                             (bx + inn2, by + inn2, bw - inn2 * 2, bh - inn2 * 2),
                             width=1, border_radius=int(4 * scale))
            for cxx, cyy in [(bx, by), (bx + bw, by), (bx, by + bh), (bx + bw, by + bh)]:
                self._draw_wave_flourish(surf, cxx, cyy, int(14 * scale), border_color)

        # Ribbon — ocean teal
        ribbon_x = w // 2 + int(30 * scale)
        ribbon_top = h - page_margin - int(4 * scale)
        ribbon_h = int(55 * scale)
        ribbon_w = int(16 * scale)
        r_pts = [
            (ribbon_x, ribbon_top),
            (ribbon_x + ribbon_w, ribbon_top),
            (ribbon_x + ribbon_w, ribbon_top + ribbon_h),
            (ribbon_x + ribbon_w // 2, ribbon_top + ribbon_h + int(8 * scale)),
            (ribbon_x, ribbon_top + ribbon_h),
        ]
        pygame.draw.polygon(surf, (40, 120, 140), r_pts)
        pygame.draw.polygon(surf, (60, 150, 170), r_pts, width=1)
        tassel_y = ribbon_top + ribbon_h + int(8 * scale)
        for ti in range(5):
            tx = ribbon_x + int(ribbon_w * (ti + 1) / 6)
            pygame.draw.line(surf, (120, 180, 200), (tx, tassel_y),
                             (tx, tassel_y + int(6 * scale)), 1)

        # Crests at top of each page
        for crect_x in [w // 4, w * 3 // 4]:
            self._draw_water_crest(surf, crect_x,
                                   page_margin + int(16 * scale),
                                   int(18 * scale), (120, 150, 180))

    # ------------------------------------------------------------------
    # Empty pages content
    # ------------------------------------------------------------------

    def _draw_empty_pages(self, surf, w, h, scale, alpha=255):
        """Draw page titles and page numbers on the blank spread."""
        content = pygame.Surface((w, h), pygame.SRCALPHA)

        # Title on first spread
        if self.current_spread == 0:
            title = self._render_text(cfg.button_font, _("FIELD JOURNAL"), (25, 50, 80))
            tx = w // 4 - title.get_width() // 2
            ty = int(30 * scale)
            content.blit(title, (tx, ty))

            # Frame around title
            frame_pad = int(10 * scale)
            frame_rect = pygame.Rect(tx - frame_pad, ty - frame_pad,
                                     title.get_width() + frame_pad * 2,
                                     title.get_height() + frame_pad * 2)
            ornate_color = (120, 150, 180)
            pygame.draw.rect(content, ornate_color, frame_rect,
                             width=1, border_radius=int(4 * scale))
            pygame.draw.rect(content, (160, 180, 205),
                             frame_rect.inflate(-int(3 * scale), -int(3 * scale)),
                             width=1, border_radius=int(3 * scale))

            # Subtitle
            sub_y = ty + title.get_height() + int(12 * scale)
            sub = self._render_text(cfg.INV_nums_font,
                                    _("\u2014 Fish Collection \u2014"),
                                    (100, 130, 160))
            content.blit(sub, (w // 4 - sub.get_width() // 2, sub_y))

        # Page numbers
        num_color = (120, 145, 175)
        page_left = self.current_spread * 2 + 1
        page_right = self.current_spread * 2 + 2

        left_num = self._render_text(cfg.INV_nums_font, str(page_left), num_color)
        lx = int(32 * scale)
        ly = h - int(35 * scale)
        content.blit(left_num, (lx, ly))

        right_num = self._render_text(cfg.INV_nums_font, str(page_right), num_color)
        rx = w - int(40 * scale) - right_num.get_width()
        ry = h - int(35 * scale)
        content.blit(right_num, (rx, ry))

        # Header flourish
        header_y = int(62 * scale)
        dot_color = (160, 180, 205)
        for side in ['left', 'right']:
            hx = int(28 * scale) if side == 'left' else w // 2 + int(28 * scale)
            hw = w // 2 - int(56 * scale)
            for li in range(hw):
                a = int(70 * (1.0 - abs(li - hw / 2) / (hw / 2)))
                content.set_at((hx + li, header_y), (*dot_color, a))
            for cxx in [hx, hx + hw // 2, hx + hw]:
                pts = [(cxx, header_y - int(4 * scale)),
                       (cxx + int(3 * scale), header_y),
                       (cxx, header_y + int(4 * scale)),
                       (cxx - int(3 * scale), header_y)]
                pygame.draw.polygon(content, dot_color, pts)

        content.set_alpha(alpha)
        surf.blit(content, (0, 0))

    # ------------------------------------------------------------------
    # Decorative helpers
    # ------------------------------------------------------------------

    def _render_text(self, font, text, color):
        s = font.render(text, True, color)
        if self.book_magnifier != 1.0:
            w, h = s.get_size()
            s = pygame.transform.smoothscale(s,
                     (int(w * self.book_magnifier), int(h * self.book_magnifier)))
        return s

    def _draw_wave_corner(self, surf, x, y, size, scale, current_time):
        silver = (180, 195, 210)
        silver_light = (210, 225, 240)
        silver_dark = (120, 140, 165)
        pulse = (math.sin(current_time * 0.003 + x * 0.01) + 1) / 2
        cx = x + size // 2
        cy = y + size // 2

        # Outer arc
        pts = []
        for i in range(12):
            a = math.pi * 0.5 * (i / 11)
            wobble = math.sin(i * 1.2 + current_time * 0.002) * size * 0.03
            r = size * 0.47 + wobble
            pts.append((int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)))
        pygame.draw.lines(surf, silver, False, pts, max(1, int(2 * scale)))

        # Middle arc
        pts2 = []
        for i in range(10):
            a = math.pi * 0.5 * (i / 9)
            r = size * 0.34
            pts2.append((int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)))
        pulse_s = tuple(min(255, int(c + 20 * pulse)) for c in silver_light)
        pygame.draw.lines(surf, pulse_s, False, pts2, max(1, int(1.5 * scale)))

        # Inner arc
        pts3 = []
        for i in range(8):
            a = math.pi * 0.5 * (i / 7)
            r = size * 0.22
            pts3.append((int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)))
        pygame.draw.lines(surf, silver_dark, False, pts3, 1)

        # Gem cluster
        gem_colors = [(80, 200, 220), (40, 160, 120), (60, 130, 190)]
        for gi, gc in enumerate(gem_colors):
            angle = math.pi * 0.5 * (gi / 3)
            g_dist = size * 0.08
            gx = cx + int(math.cos(angle) * g_dist)
            gy = cy + int(math.sin(angle) * g_dist)
            self._draw_gem(surf, gx, gy, max(1, int(size * 0.08)), gc, scale)

        # Silver dots
        for i in range(7):
            a = math.pi * 0.5 * (i / 6)
            r = size * 0.41
            dx = cx + int(math.cos(a) * r)
            dy = cy + int(math.sin(a) * r)
            sz = max(1, int(2 * scale + pulse))
            pygame.draw.circle(surf, silver_light, (dx, dy), sz)

    def _draw_wave_flourish(self, surf, x, y, size, color):
        s = max(4, size)
        pts_outer = [(x, y), (x + s, y), (x, y + s)]
        pygame.draw.lines(surf, color, False, pts_outer, 1)
        pts_inner = [(x + s // 4, y + s // 4),
                     (x + s * 3 // 4, y + s // 4),
                     (x + s // 4, y + s * 3 // 4)]
        pygame.draw.lines(surf, color, False, pts_inner, 1)
        pygame.draw.circle(surf, color, (x + s // 2, y + s // 2), max(1, s // 6))

    def _draw_gem(self, surf, cx, cy, size, color, scale):
        s = max(2, int(size * scale))
        lighter = tuple(min(255, c + 70) for c in color)
        darker = tuple(max(0, c - 50) for c in color)
        pts_top = [(cx, cy - s), (cx - s // 2, cy), (cx + s // 2, cy)]
        pts_bot = [(cx - s // 2, cy), (cx + s // 2, cy), (cx, cy + s)]
        pygame.draw.polygon(surf, lighter, pts_top)
        pygame.draw.polygon(surf, darker, pts_bot)
        highlight = tuple(min(255, c + 140) for c in color)
        pygame.draw.circle(surf, highlight, (cx - s // 3, cy - s // 3), max(1, s // 3))

    def _draw_water_crest(self, surf, cx, cy, size, color):
        s = max(4, size)
        points = []
        for i in range(8):
            a = i * math.pi / 4
            r = s * (0.5 if i % 2 == 0 else 1.0)
            points.append((int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)))
        pygame.draw.polygon(surf, color, points)
        pygame.draw.circle(surf, (180, 210, 230), (cx, cy), max(1, s // 4))
        pygame.draw.circle(surf, color, (cx, cy), max(1, s // 3), 1)