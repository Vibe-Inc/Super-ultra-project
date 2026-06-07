import pygame
import math
import random
from src.ui.menus.base import Menu
from src.ui.widgets import Button
import src.config as cfg
from database.GP_database import Gp_database
from src.items.items import create_item


class Particle:
    """A single particle used for book page-flip and hover effects.

    Attributes:
        x (float): Current X position.
        y (float): Current Y position.
        vx (float): Horizontal velocity.
        vy (float): Vertical velocity.
        lifetime (float): Remaining lifetime in seconds.
        max_lifetime (float): Initial lifetime in seconds.
        color (tuple): RGB or RGBA color tuple.
        size (float): Radius of the particle.
        star (bool): Whether to draw a star shape instead of a circle.
        phase (float): Random phase offset for animations.

    Methods:
        update(dt): Update position, gravity, and lifetime.
        draw(surf, offset=(0, 0)): Draw the particle onto a surface.
    """
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
        self.vy += 120 * dt

    def draw(self, surf, offset=(0, 0)):
        if self.lifetime <= 0:
            return
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        progress = 1.0 - (self.lifetime / self.max_lifetime)
        sz = max(1, int(self.size * (1.0 - progress * 0.5)))
        px = int(self.x + offset[0])
        py = int(self.y + offset[1])

        if self.star:
            clr = (self.color[0], self.color[1], self.color[2], alpha)
            s = pygame.Surface((sz * 4, sz * 4), pygame.SRCALPHA)
            points = [
                (sz * 2, 0), (sz * 2 + sz, sz * 2),
                (sz * 2, sz * 4 - 1), (sz * 2 - sz, sz * 2),
            ]
            pygame.draw.polygon(s, clr, points)
            pygame.draw.polygon(s, clr, [
                (0, sz * 2), (sz * 2, sz * 2 - sz),
                (sz * 4 - 1, sz * 2), (sz * 2, sz * 2 + sz),
            ])
            surf.blit(s, (px - sz * 2, py - sz * 2))
        else:
            clr = tuple(int(c * (self.lifetime / self.max_lifetime)) for c in self.color[:3])
            pygame.draw.circle(surf, clr, (px, py), sz)


def ease_out_cubic(t):
    return 1.0 - math.pow(1.0 - t, 3)

def ease_in_out_quad(t):
    if t < 0.5:
        return 2 * t * t
    return 1 - math.pow(-2 * t + 2, 2) / 2

def ease_in_out_cubic(t):
    if t < 0.5:
        return 4 * t * t * t
    return 1 - math.pow(-2 * t + 2, 3) / 2


class RecipeBookMenu(Menu):
    """An ornate recipe book interface showing craftable items.

    Attributes:
        book_magnifier (float): Scale multiplier for the book UI.
        recipes (list[dict]): All recipes loaded from the database.
        item_images (dict): Cached item images keyed by item ID.
        recipes_per_spread (int): Number of recipe cards per spread.
        current_spread (int): Zero-based index of the current spread.
        max_spreads (int): Total number of spreads.
        anim_start_time (int): Timestamp of the opening animation start.
        anim_duration (int): Duration of the opening animation in ms.
        is_opening (bool): Whether the book opening animation is active.
        flip_start_time (int): Timestamp of the page flip start.
        flip_duration (int): Duration of the flip animation in ms.
        is_flipping (bool): Whether a page flip animation is active.
        card_entry_start_time (int): Timestamp for card entry animation.
        card_entry_duration (int): Duration of card entry animation in ms.
        hovered_card_index (int): Index of the currently hovered card (-1 if none).
        card_hover_animations (dict): Per-card hover animation progress.
        particles (list[Particle]): Active card hover particles.
        page_particles (list[Particle]): Active page-flip particles.
        ambient_particles (list[Particle]): Active ambient sparkle particles.
        star_particles (list[Particle]): Active star-shaped particles.
        shine_phase (float): Random phase for the golden shine sweep.
        buttons (list[Button]): Interactive UI buttons (close, prev, next).

    Methods:
        _render_text(font, text, color):
            Render text with book magnifier scaling.
        _setup_buttons():
            Create or update close, prev, and next page buttons.
        prev_page():
            Go to the previous spread.
        next_page():
            Go to the next spread.
        _start_flip_anim():
            Start the page flip animation and emit particles.
        _emit_page_particles():
            Spawn particles for the page flip effect.
        _emit_golden_burst():
            Spawn a burst of golden particles.
        _emit_card_particles(x, y):
            Spawn particles at a card position on hover.
        _spawn_ambient_particles(dt):
            Spawn ambient golden sparkles over the book.
        _spawn_star_particles(dt):
            Spawn occasional star-shaped particles.
        close_menu():
            Return to the gameplay state.
        update(dt):
            Update all particles and hover animations.
        handle_event(event):
            Handle keyboard and mouse input.
        _update_hovered_card(mouse_pos):
            Determine which recipe card the mouse is over.
        draw(screen):
            Render the full recipe book overlay.
        _draw_book_background(surf, w, h, scale, current_time):
            Draw the ornate book cover, pages, spine, and decorations.
        _draw_arabesque(surf, x, y, size, color):
            Draw a small arabesque corner flourish.
        _draw_crest(surf, cx, cy, size, color):
            Draw a small decorative crest/emblem.
        _draw_gem(surf, cx, cy, size, color, scale):
            Draw a faceted gem decoration.
        _draw_elaborate_corner(surf, x, y, size, scale, current_time):
            Draw an elaborate corner ornament with gems and filigree.
        _draw_small_flourish(surf, x, y, size, color, angle):
            Draw a small ornamental flourish.
        _draw_recipes_for_current_spread(surf, w, h, scale, alpha, current_time):
            Draw the recipe cards, titles, and page decorations for the current spread.
        _draw_recipe_card(surf, x, y, w, h, recipe, scale, recipe_idx, current_time):
            Draw a single recipe card with grid, arrow, and result slot.
    """
    def __init__(self, app):
        super().__init__(app)
        self.book_magnifier = 1.35

        db = Gp_database()
        self.recipes = db.get_all_recipes()
        db.close()

        self.item_images = {}
        for recipe in self.recipes:
            res_id = recipe['result_id']
            if res_id not in self.item_images:
                try: self.item_images[res_id] = create_item(res_id).image
                except Exception: pass
            for col in range(3):
                for row in range(3):
                    ing_id = recipe["matrix"][col][row]
                    if ing_id and ing_id not in self.item_images:
                        try: self.item_images[ing_id] = create_item(ing_id).image
                        except Exception: pass

        self.recipes_per_spread = 4
        self.current_spread = 0
        self.max_spreads = max(1, math.ceil(len(self.recipes) / self.recipes_per_spread))

        self.anim_start_time = pygame.time.get_ticks()
        self.anim_duration = 600
        self.is_opening = True

        self.flip_start_time = 0
        self.flip_duration = 300
        self.is_flipping = False

        self.card_entry_start_time = pygame.time.get_ticks()
        self.card_entry_duration = 600
        self.hovered_card_index = -1
        self.card_hover_animations = {}
        self.particles = []
        self.page_particles = []
        self.ambient_particles = []
        self.star_particles = []
        self.shine_phase = random.uniform(0, math.pi * 2)

        self.buttons = []
        self._setup_buttons()

        # Caching
        self._cached_book_bg = None
        self._cached_glow_surf = None
        self._cached_shadow_surf = None
        self._cached_shine_surf = None
        self._card_bg_cache = {}
        self._pre_scaled_grid = {}
        self._pre_scaled_result = {}
        self._cached_texts = {}
        self._prev_book_w = 0
        self._prev_book_h = 0
        self._prev_scale = 0

        scale = cfg.ui_scale() * self.book_magnifier
        grid_slot_size = int(33 * scale)
        res_icon_size = int(58 * scale) - int(14 * scale)
        for ing_id, img_surf in self.item_images.items():
            try:
                self._pre_scaled_grid[ing_id] = pygame.transform.scale(img_surf, (grid_slot_size - int(6 * scale), grid_slot_size - int(6 * scale)))
                self._pre_scaled_result[ing_id] = pygame.transform.scale(img_surf, (res_icon_size, res_icon_size))
            except Exception:
                pass

    def _render_text(self, font, text, color):
        surf = font.render(text, True, color)
        if self.book_magnifier != 1.0:
            w, h = surf.get_size()
            surf = pygame.transform.smoothscale(surf, (int(w * self.book_magnifier), int(h * self.book_magnifier)))
        return surf

    def _setup_buttons(self):
        self.buttons.clear()
        scale = cfg.ui_scale() * self.book_magnifier
        cx, cy = cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2
        book_w = int(860 * scale)
        book_h = int(600 * scale)
        btn_w, btn_h = int(160 * scale), int(42 * scale)

        back_x = cx + book_w // 2 - btn_w - int(30 * scale)
        back_y = cy + book_h // 2 - btn_h - int(30 * scale)
        back_rect = pygame.Rect(back_x, back_y, btn_w, btn_h)
        self.buttons.append(Button(
            back_rect, _("CLOSE BOOK"), cfg.button_color_EXIT, cfg.button_hover_color_EXIT,
            cfg.button_font, cfg.text_color, cfg.corner_radius, on_click=self.close_menu
        ))

        if self.current_spread > 0:
            prev_x = cx - book_w // 2 + int(30 * scale)
            prev_y = cy + book_h // 2 - btn_h - int(30 * scale)
            prev_rect = pygame.Rect(prev_x, prev_y, btn_w, btn_h)
            self.buttons.append(Button(
                prev_rect, _("<- PREV"), (80, 60, 40), (120, 90, 60),
                cfg.button_font, cfg.text_color, cfg.corner_radius, on_click=self.prev_page
            ))
        if self.current_spread < self.max_spreads - 1:
            next_x = cx + book_w // 2 - btn_w * 2 - int(40 * scale)
            next_y = cy + book_h // 2 - btn_h - int(30 * scale)
            next_rect = pygame.Rect(next_x, next_y, btn_w, btn_h)
            self.buttons.append(Button(
                next_rect, _("NEXT ->"), (80, 60, 40), (120, 90, 60),
                cfg.button_font, cfg.text_color, cfg.corner_radius, on_click=self.next_page
            ))

    def prev_page(self):
        if self.current_spread > 0 and not self.is_flipping:
            self.current_spread -= 1
            self._start_flip_anim()

    def next_page(self):
        if self.current_spread < self.max_spreads - 1 and not self.is_flipping:
            self.current_spread += 1
            self._start_flip_anim()

    def _start_flip_anim(self):
        self.is_flipping = True
        self.flip_start_time = pygame.time.get_ticks()
        self.card_entry_start_time = pygame.time.get_ticks()
        self._setup_buttons()
        self._emit_page_particles()
        self._emit_golden_burst()

    def _emit_page_particles(self):
        scale = cfg.ui_scale() * self.book_magnifier
        cx, cy = cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2
        book_w = int(860 * scale)
        book_h = int(600 * scale)
        for _ in range(30):
            x = cx + random.randint(-book_w // 2, book_w // 2)
            y = cy + random.randint(-book_h // 2, book_h // 2)
            vx = random.uniform(-250, 250)
            vy = random.uniform(-400, -60)
            lifetime = random.uniform(0.4, 1.0)
            colors = [(245, 235, 210), (220, 200, 170), (212, 175, 55), (255, 215, 0)]
            color = random.choice(colors)
            size = random.randint(2, 6)
            star = random.random() < 0.3
            self.page_particles.append(Particle(x, y, vx, vy, lifetime, color, size, star=star))

    def _emit_golden_burst(self):
        cx, cy = cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(120, 350)
            x = cx + random.randint(-120, 120)
            y = cy + random.randint(-120, 120)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.3, 0.8)
            color = (212, 175, 55)
            size = random.randint(2, 5)
            star = random.random() < 0.4
            self.page_particles.append(Particle(x, y, vx, vy, lifetime, color, size, star=star))

    def _emit_card_particles(self, x, y):
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 200)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.3, 0.7)
            colors = [(212, 175, 55), (255, 215, 0), (255, 255, 200), (200, 150, 100)]
            color = random.choice(colors)
            size = random.randint(1, 4)
            star = random.random() < 0.3
            self.particles.append(Particle(x, y, vx, vy, lifetime, color, size, star=star))

    def _spawn_ambient_particles(self, dt):
        if random.random() < 0.25:
            scale = cfg.ui_scale() * self.book_magnifier
            cx, cy = cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2
            book_w = int(860 * scale)
            book_h = int(600 * scale)
            x = cx + random.randint(-book_w // 2 - 40, book_w // 2 + 40)
            y = cy + random.randint(-book_h // 2 - 40, book_h // 2 + 40)
            vx = random.uniform(-20, 20)
            vy = random.uniform(-50, -15)
            lifetime = random.uniform(1.5, 3.5)
            colors = [(212, 175, 55, 100), (255, 215, 0, 80), (255, 255, 200, 50), (200, 180, 120, 60)]
            color = random.choice(colors)
            size = random.randint(1, 3)
            self.ambient_particles.append(Particle(x, y, vx, vy, lifetime, color, size, star=False))

    def _spawn_star_particles(self, dt):
        self.shine_phase += dt * 2
        if random.random() < 0.08:
            scale = cfg.ui_scale() * self.book_magnifier
            cx, cy = cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2
            book_w = int(860 * scale)
            book_h = int(600 * scale)
            x = cx + random.randint(-book_w // 2, book_w // 2)
            y = cy + random.randint(-book_h // 2, book_h // 2)
            vx = random.uniform(-8, 8)
            vy = random.uniform(-20, -5)
            lifetime = random.uniform(0.8, 2.0)
            bright = random.randint(180, 255)
            color = (bright, bright, random.randint(150, 200))
            size = random.randint(2, 4)
            self.star_particles.append(Particle(x, y, vx, vy, lifetime, color, size, star=True))

    def on_enter(self):
        self._setup_buttons()

    def close_menu(self):
        self.app.manager.set_state("gameplay")

    def update(self, dt=1/60):
        self._spawn_ambient_particles(dt)
        self._spawn_star_particles(dt)
        self.particles = [p for p in self.particles if p.lifetime > 0]
        self.page_particles = [p for p in self.page_particles if p.lifetime > 0]
        self.ambient_particles = [p for p in self.ambient_particles if p.lifetime > 0]
        self.star_particles = [p for p in self.star_particles if p.lifetime > 0]
        for particle in self.particles + self.page_particles + self.ambient_particles + self.star_particles:
            particle.update(dt)
        for card_idx in list(self.card_hover_animations.keys()):
            if card_idx == self.hovered_card_index:
                self.card_hover_animations[card_idx] = min(1.0, self.card_hover_animations[card_idx] + 3 * dt)
            else:
                self.card_hover_animations[card_idx] -= 3 * dt
                if self.card_hover_animations[card_idx] <= 0:
                    del self.card_hover_animations[card_idx]

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
        elif event.type == pygame.MOUSEMOTION:
            self._update_hovered_card(event.pos)

    def _update_hovered_card(self, mouse_pos):
        scale = cfg.ui_scale() * self.book_magnifier
        cx, cy = cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2
        book_w = int(860 * scale)
        book_h = int(600 * scale)
        book_x = cx - book_w // 2
        book_y = cy - book_h // 2
        card_w = int(340 * scale)
        card_h = int(195 * scale)
        start_y = int(90 * scale)
        gap_y = int(22 * scale)
        start_idx = self.current_spread * self.recipes_per_spread
        end_idx = min(start_idx + self.recipes_per_spread, len(self.recipes))
        self.hovered_card_index = -1
        for i in range(start_idx, end_idx):
            local_idx = i - start_idx
            is_right_page = local_idx >= 2
            if not is_right_page:
                x = book_x + (book_w // 2 - card_w) // 2
            else:
                x = book_x + book_w // 2 + (book_w // 2 - card_w) // 2
            row = local_idx % 2
            y = book_y + start_y + row * (card_h + gap_y)
            card_rect = pygame.Rect(x, y, card_w, card_h)
            if card_rect.collidepoint(mouse_pos):
                self.hovered_card_index = i
                if i not in self.card_hover_animations:
                    self.card_hover_animations[i] = 0
                if self.card_hover_animations.get(i, 0) < 0.05:
                    self._emit_card_particles(x + card_w // 2, y + card_h // 2)
                break

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
                open_progress = ease_out_cubic(t)

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
        overlay.fill((10, 10, 10, int(180 * open_progress)))
        screen.blit(overlay, (0, 0))

        scale = cfg.ui_scale() * self.book_magnifier
        cx, cy = cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2
        book_w = int(860 * scale)
        book_h = int(600 * scale)
        y_offset = int((1.0 - open_progress) * 150 * scale)

        # Radiant golden glow behind the book (cached)
        glow_size = max(book_w, book_h) + int(80 * scale)
        if self._cached_glow_surf is None or self._cached_glow_surf.get_width() != glow_size:
            self._cached_glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pulse = (math.sin(current_time * 0.002) + 1) / 2
            glow_alpha = int(40 + pulse * 30)
            for r in range(glow_size // 2, 0, -1):
                a = int(glow_alpha * (1.0 - r / (glow_size // 2)))
                if a > 0:
                    pygame.draw.circle(self._cached_glow_surf, (212, 175, 55, a), (glow_size // 2, glow_size // 2), r)
        screen.blit(self._cached_glow_surf, (cx - glow_size // 2, cy + y_offset - glow_size // 2))

        # Book shadow (cached)
        shadow_w = book_w + int(40 * scale)
        shadow_h = book_h + int(20 * scale)
        if self._cached_shadow_surf is None or self._cached_shadow_surf.get_width() != shadow_w:
            self._cached_shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
            pygame.draw.rect(self._cached_shadow_surf, (0, 0, 0, 80), (int(20 * scale), 0, book_w, book_h + int(10 * scale)), border_radius=int(20 * scale))
        screen.blit(self._cached_shadow_surf, (cx - (book_w + int(40 * scale)) // 2, cy + y_offset - book_h // 2 + int(8 * scale)))

        # Cached book background (regenerate only on size/scale change)
        if (self._cached_book_bg is None or self._prev_book_w != book_w or self._prev_book_h != book_h or
                abs(self._prev_scale - scale) > 0.01):
            self._cached_book_bg = pygame.Surface((book_w, book_h), pygame.SRCALPHA)
            self._draw_book_background(self._cached_book_bg, book_w, book_h, scale, current_time)
            self._prev_book_w = book_w
            self._prev_book_h = book_h
            self._prev_scale = scale
            self._card_bg_cache.clear()

        book_surf = self._cached_book_bg.copy()
        self._draw_recipes_for_current_spread(book_surf, book_w, book_h, scale, content_alpha, current_time)

        book_rect = book_surf.get_rect(center=(cx, cy + y_offset))
        if self.is_opening:
            book_surf.set_alpha(int(255 * open_progress))
        screen.blit(book_surf, book_rect.topleft)

        # Star particles
        for particle in self.star_particles:
            px = int(particle.x - cx + book_rect.centerx)
            py = int(particle.y - cy + book_rect.centery)
            blink = (math.sin(particle.phase + current_time * 0.004) + 1) / 2
            alpha = int(particle.lifetime / particle.max_lifetime * 255 * blink)
            if alpha > 5:
                sz = particle.size
                clr = particle.color
                s = pygame.Surface((sz * 6, sz * 6), pygame.SRCALPHA)
                mid = sz * 3
                glow_clr = (clr[0], clr[1], clr[2], alpha // 3)
                pygame.draw.circle(s, glow_clr, (mid, mid), sz * 3)
                for k in range(4):
                    angle = k * math.pi / 2 + math.pi / 4 + current_time * 0.001
                    pts = []
                    for j in range(5):
                        a = angle + j * math.pi / 2
                        r = sz * 2 if j % 2 == 0 else sz
                        pts.append((mid + int(math.cos(a) * r), mid + int(math.sin(a) * r)))
                    pygame.draw.polygon(s, (clr[0], clr[1], clr[2], alpha), pts)
                screen.blit(s, (px - mid, py - mid))

        # Golden shine sweep across the book (cached)
        shine_t = (current_time * 0.0003) % 1.0
        shine_x = int((shine_t - 0.3) * book_w * 1.4)
        if 0 < shine_x < book_w:
            shine_w = int(100 * scale)
            if self._cached_shine_surf is None or self._cached_shine_surf.get_width() != shine_w or self._cached_shine_surf.get_height() != book_h:
                self._cached_shine_surf = pygame.Surface((shine_w, book_h), pygame.SRCALPHA)
                for sx in range(shine_w):
                    a = int(30 * (1.0 - abs(sx - shine_w / 2) / (shine_w / 2)))
                    if a > 0:
                        pygame.draw.line(self._cached_shine_surf, (255, 215, 0, a), (sx, 0), (sx, book_h))
            screen.blit(self._cached_shine_surf, (book_rect.x + shine_x, book_rect.y))

        # Ambient golden sparkles
        for particle in self.ambient_particles:
            px = int(particle.x - cx + book_rect.centerx)
            py = int(particle.y - cy + book_rect.centery)
            if len(particle.color) == 4:
                a = int(particle.color[3] * (particle.lifetime / particle.max_lifetime))
                clr = (particle.color[0], particle.color[1], particle.color[2], a)
                pygame.draw.circle(screen, clr, (px, py), particle.size)
            else:
                particle.draw(screen, offset=(-cx + book_rect.centerx, -cy + book_rect.centery))

        for particle in self.page_particles:
            particle.draw(screen, offset=(-cx + book_rect.centerx, -cy + book_rect.centery))
        for particle in self.particles:
            px = int(particle.x - cx + book_rect.centerx)
            py = int(particle.y - cy + book_rect.centery)
            if particle.star:
                sz = particle.size
                a = int(255 * (particle.lifetime / particle.max_lifetime))
                if a > 5:
                    s = pygame.Surface((sz * 6, sz * 6), pygame.SRCALPHA)
                    mid = sz * 3
                    for k in range(4):
                        angle = k * math.pi / 2 + math.pi / 4
                        pts = []
                        for j in range(5):
                            ang = angle + j * math.pi / 2
                            r = sz * 2 if j % 2 == 0 else sz
                            pts.append((mid + int(math.cos(ang) * r), mid + int(math.sin(ang) * r)))
                        pygame.draw.polygon(s, (*particle.color[:3], a), pts)
                    screen.blit(s, (px - mid, py - mid))
            else:
                particle.draw(screen, offset=(-cx + book_rect.centerx, -cy + book_rect.centery))

        if not self.is_opening and not self.is_flipping:
            for button in self.buttons:
                button.draw(screen)

    def _draw_book_background(self, surf, w, h, scale, current_time):
        cover_color = (50, 24, 8)
        pygame.draw.rect(surf, cover_color, (0, 0, w, h), border_radius=int(20 * scale))

        # Leather texture
        tex_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for _ in range(1200):
            tx = random.randint(0, w - 1)
            ty = random.randint(0, h - 1)
            a = random.randint(3, 12)
            shade = random.randint(0, 1)
            c = (35, 18, 6) if shade else (18, 10, 4)
            tex_surf.set_at((tx, ty), (*c, a))
        surf.blit(tex_surf, (0, 0))

        # Pulsing golden border
        pulse = (math.sin(current_time * 0.003) + 1) / 2
        gold_pulse = int(180 + pulse * 60)
        margin = int(7 * scale)
        gold_colors = [(gold_pulse, gold_pulse - 30, 60), (212, 175, 55), (gold_pulse - 20, gold_pulse - 50, 40)]
        for i, gc in enumerate(gold_colors):
            gc = tuple(max(0, min(255, c)) for c in gc)
            inset = margin + i * int(3 * scale)
            wd = 1 if i < 2 else max(1, int(2 * scale))
            pygame.draw.rect(surf, gc, (inset, inset, w - inset * 2, h - inset * 2), width=wd, border_radius=int(18 * scale - i))

        # Corner ornaments
        corner_size = int(60 * scale)
        corners = [
            (margin + int(2*scale), margin + int(2*scale)),
            (w - margin - int(2*scale) - corner_size, margin + int(2*scale)),
            (margin + int(2*scale), h - margin - int(2*scale) - corner_size),
            (w - margin - int(2*scale) - corner_size, h - margin - int(2*scale) - corner_size),
        ]
        for x, y in corners:
            self._draw_elaborate_corner(surf, x, y, corner_size, scale, current_time)

        # Spine
        spine_w = int(48 * scale)
        spine_x = w // 2 - spine_w // 2
        spine_top = int(10 * scale)
        spine_bot = h - int(10 * scale)
        spine_shadow = pygame.Surface((spine_w, spine_bot - spine_top), pygame.SRCALPHA)
        for i in range(spine_w // 2):
            a = int(130 * (1.0 - (i / (spine_w // 2))))
            pygame.draw.line(spine_shadow, (0, 0, 0, a), (i, 0), (i, spine_bot - spine_top), 1)
            pygame.draw.line(spine_shadow, (0, 0, 0, a), (spine_w - i - 1, 0), (spine_w - i - 1, spine_bot - spine_top), 1)
        surf.blit(spine_shadow, (spine_x, spine_top))

        # Golden bands on spine
        band_positions = [
            spine_top + int(25*scale), spine_top + int(75*scale),
            spine_bot - int(75*scale), spine_bot - int(25*scale)
        ]
        for by in band_positions:
            for bw in range(int(5 * scale)):
                band_color = (212, 175, 55) if bw % 2 == 0 else (180, 150, 80)
                if pulse > 0.5 and bw == 2:
                    band_color = (255, 220, 80)
                pygame.draw.line(surf, band_color, (spine_x + int(7*scale), by + bw),
                                 (spine_x + spine_w - int(7*scale), by + bw), 1)

        pygame.draw.line(surf, (160, 130, 80), (w // 2, int(16 * scale)), (w // 2, h - int(16 * scale)), max(1, int(2 * scale)))

        # Spine gems
        gem_y = (spine_top + spine_bot) // 2
        gem_colors = [(220, 40, 40), (40, 70, 220)]
        for gi, gcol in enumerate(gem_colors):
            gx = spine_x + int(spine_w * (0.25 + gi * 0.5))
            self._draw_gem(surf, gx, gem_y + int((gi - 0.5) * 22 * scale), int(6 * scale), gcol, scale)

        # Pages
        page_color = (250, 242, 218)
        page_margin = int(18 * scale)
        left_page = pygame.Rect(page_margin, page_margin, w // 2 - page_margin, h - page_margin * 2)
        pygame.draw.rect(surf, page_color, left_page, border_top_left_radius=int(14*scale), border_bottom_left_radius=int(14*scale))
        gild = pygame.Surface((left_page.width, left_page.height), pygame.SRCALPHA)
        for x in range(left_page.width):
            a = int(10 * (x / left_page.width))
            pygame.draw.line(gild, (0, 0, 0, a), (x, 0), (x, left_page.height))
        surf.blit(gild, (left_page.x, left_page.y))

        right_page = pygame.Rect(w // 2, page_margin, w // 2 - page_margin, h - page_margin * 2)
        pygame.draw.rect(surf, page_color, right_page, border_top_right_radius=int(14*scale), border_bottom_right_radius=int(14*scale))
        gild_r = pygame.Surface((right_page.width, right_page.height), pygame.SRCALPHA)
        for x in range(right_page.width):
            a = int(10 * (1.0 - x / right_page.width))
            pygame.draw.line(gild_r, (0, 0, 0, a), (x, 0), (x, right_page.height))
        surf.blit(gild_r, (right_page.x, right_page.y))

        # Ornate page borders - triple line with corner flourishes
        border_color = (200, 175, 120)
        border_color_light = (220, 195, 140)
        for side in ['left', 'right']:
            if side == 'left':
                bx = page_margin + int(6 * scale)
                by = page_margin + int(6 * scale)
                bw = w // 2 - page_margin - int(12 * scale)
                bh = h - page_margin * 2 - int(12 * scale)
            else:
                bx = w // 2 + int(6 * scale)
                by = page_margin + int(6 * scale)
                bw = w // 2 - page_margin - int(12 * scale)
                bh = h - page_margin * 2 - int(12 * scale)

            pygame.draw.rect(surf, border_color, (bx, by, bw, bh), width=1, border_radius=int(8*scale))
            inner = int(3 * scale)
            pygame.draw.rect(surf, border_color_light, (bx + inner, by + inner, bw - inner * 2, bh - inner * 2), width=1, border_radius=int(6*scale))
            inner2 = int(6 * scale)
            pygame.draw.rect(surf, border_color, (bx + inner2, by + inner2, bw - inner2 * 2, bh - inner2 * 2), width=1, border_radius=int(4*scale))

            # Corner arabesques
            for cx, cy in [(bx, by), (bx + bw, by), (bx, by + bh), (bx + bw, by + bh)]:
                self._draw_arabesque(surf, cx, cy, int(14 * scale), border_color)

        # Ribbon bookmark hanging from bottom
        ribbon_x = w // 2 + int(30 * scale)
        ribbon_top = h - page_margin - int(4 * scale)
        ribbon_h = int(55 * scale)
        ribbon_w = int(16 * scale)
        ribbon_color = (180, 40, 40)
        r_pts = [(ribbon_x, ribbon_top), (ribbon_x + ribbon_w, ribbon_top),
                 (ribbon_x + ribbon_w, ribbon_top + ribbon_h),
                 (ribbon_x + ribbon_w // 2, ribbon_top + ribbon_h + int(8 * scale)),
                 (ribbon_x, ribbon_top + ribbon_h)]
        pygame.draw.polygon(surf, ribbon_color, r_pts)
        pygame.draw.polygon(surf, (220, 60, 60), r_pts, width=1)
        # Tassel
        tassel_y = ribbon_top + ribbon_h + int(8 * scale)
        for ti in range(5):
            tx = ribbon_x + int(ribbon_w * (ti + 1) / 6)
            pygame.draw.line(surf, (200, 160, 80), (tx, tassel_y), (tx, tassel_y + int(6 * scale)), 1)

        # Ornate crest/emblem at the top center of each page
        crest_color = (180, 150, 80)
        for cx, cy in [(w // 4, page_margin + int(16 * scale)), (w * 3 // 4, page_margin + int(16 * scale))]:
            self._draw_crest(surf, cx, cy, int(18 * scale), crest_color)

    def _draw_arabesque(self, surf, x, y, size, color):
        """Draw a small arabesque corner flourish."""
        s = max(4, size)
        pts_outer = [(x, y), (x + s, y), (x, y + s)]
        pygame.draw.lines(surf, color, False, pts_outer, 1)
        pts_inner = [(x + s // 4, y + s // 4), (x + s * 3 // 4, y + s // 4), (x + s // 4, y + s * 3 // 4)]
        pygame.draw.lines(surf, color, False, pts_inner, 1)
        pygame.draw.circle(surf, color, (x + s // 2, y + s // 2), max(1, s // 6))

    def _draw_crest(self, surf, cx, cy, size, color):
        """Draw a small decorative crest/emblem."""
        s = max(4, size)
        points = []
        for i in range(8):
            a = i * math.pi / 4
            r = s * (0.5 if i % 2 == 0 else 1.0)
            points.append((int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)))
        pygame.draw.polygon(surf, color, points)
        pygame.draw.circle(surf, (240, 210, 100), (cx, cy), max(1, s // 4))
        pygame.draw.circle(surf, color, (cx, cy), max(1, s // 3), 1)

    def _draw_gem(self, surf, cx, cy, size, color, scale):
        s = max(2, int(size * scale))
        lighter = tuple(min(255, c + 70) for c in color)
        darker = tuple(max(0, c - 50) for c in color)
        points_top = [(cx, cy - s), (cx - s // 2, cy), (cx + s // 2, cy)]
        points_bot = [(cx - s // 2, cy), (cx + s // 2, cy), (cx, cy + s)]
        pygame.draw.polygon(surf, lighter, points_top)
        pygame.draw.polygon(surf, darker, points_bot)
        highlight = tuple(min(255, c + 140) for c in color)
        pygame.draw.circle(surf, highlight, (cx - s // 3, cy - s // 3), max(1, s // 3))

    def _draw_elaborate_corner(self, surf, x, y, size, scale, current_time):
        gold = (212, 175, 55)
        gold_light = (245, 215, 105)
        gold_dark = (155, 125, 55)
        pulse = (math.sin(current_time * 0.003 + x * 0.01) + 1) / 2

        cx = x + size // 2
        cy = y + size // 2

        # Outer arc
        pts = []
        for i in range(12):
            a = math.pi * 0.5 * (i / 11)
            r = size * 0.47
            pts.append((int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)))
        pygame.draw.lines(surf, gold, False, pts, max(1, int(2 * scale)))

        # Middle arc
        pts2 = []
        for i in range(10):
            a = math.pi * 0.5 * (i / 9)
            r = size * 0.34
            pts2.append((int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)))
        pulse_gold = tuple(min(255, int(c + 20 * pulse)) for c in gold_light)
        pygame.draw.lines(surf, pulse_gold, False, pts2, max(1, int(1.5 * scale)))

        # Inner arc
        pts3 = []
        for i in range(8):
            a = math.pi * 0.5 * (i / 7)
            r = size * 0.22
            pts3.append((int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)))
        pygame.draw.lines(surf, gold_dark, False, pts3, 1)

        # Central gem cluster
        gem_colors = [(220, 40, 40), (40, 70, 220), (40, 200, 40)]
        for gi, gc in enumerate(gem_colors):
            angle = math.pi * 0.5 * (gi / 3)
            g_dist = size * 0.08
            gx = cx + int(math.cos(angle) * g_dist)
            gy = cy + int(math.sin(angle) * g_dist)
            self._draw_gem(surf, gx, gy, max(1, int(size * 0.08)), gc, scale)

        # Gold dots
        for i in range(7):
            a = math.pi * 0.5 * (i / 6)
            r = size * 0.41
            dx = cx + int(math.cos(a) * r)
            dy = cy + int(math.sin(a) * r)
            sz = max(1, int(2 * scale + pulse))
            pygame.draw.circle(surf, gold_light, (dx, dy), sz)

        # Filigree swirls
        for i in range(4):
            a_start = math.pi * 0.5 * (i / 5)
            a_end = math.pi * 0.5 * (i / 5 + 0.18)
            r1 = size * (0.12 + i * 0.08)
            r2 = size * (0.22 + i * 0.08)
            sw_pts = []
            for j in range(8):
                t = j / 7
                aa = a_start + (a_end - a_start) * t
                rr = r1 + (r2 - r1) * t
                sw_pts.append((int(cx + math.cos(aa) * rr), int(cy + math.sin(aa) * rr)))
            pygame.draw.lines(surf, gold_dark, False, sw_pts, 1)

    def _draw_small_flourish(self, surf, x, y, size, color, angle):
        pts = [(x, y - size), (x + size // 2, y), (x, y + size), (x - size // 2, y)]
        pygame.draw.circle(surf, color, (x, y), size, 1)
        pygame.draw.line(surf, color, (x - size, y), (x + size, y), 1)
        pygame.draw.line(surf, color, (x, y - size), (x, y + size), 1)

    def _draw_recipes_for_current_spread(self, surf, w, h, scale, alpha, current_time):
        content_surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Chapter title on first page (cached)
        title_key = ("title_page", scale)
        if title_key not in self._card_bg_cache:
            ts = pygame.Surface((w, h), pygame.SRCALPHA)
            title_text = _("RECIPE BOOK")
            title = self._render_text(cfg.button_font, title_text, (70, 45, 18))
            tx = w // 4 - title.get_width() // 2
            ty = int(30 * scale)
            ts.blit(title, (tx, ty))

            ornate_color = (180, 150, 80)
            frame_pad = int(10 * scale)
            frame_rect = pygame.Rect(tx - frame_pad, ty - frame_pad,
                                     title.get_width() + frame_pad * 2, title.get_height() + frame_pad * 2)
            pygame.draw.rect(ts, ornate_color, frame_rect, width=1, border_radius=int(4 * scale))
            pygame.draw.rect(ts, (200, 175, 120), frame_rect.inflate(-int(3*scale), -int(3*scale)), width=1, border_radius=int(3*scale))

            fl_y = ty + title.get_height() // 2
            line_len = int(70 * scale)
            for side in [-1, 1]:
                if side == -1:
                    sx = tx - frame_pad - int(5 * scale)
                    for li in range(int(line_len)):
                        a = int(80 * (1.0 - li / line_len))
                        ts.set_at((int(sx - li), fl_y), (*ornate_color, a))
                else:
                    sx = tx + title.get_width() + frame_pad + int(5 * scale)
                    for li in range(int(line_len)):
                        a = int(80 * li / line_len)
                        ts.set_at((int(sx + li), fl_y), (*ornate_color, a))

            for fx in [tx - frame_pad - line_len, tx + title.get_width() + frame_pad + line_len]:
                pts = [(fx, fl_y - int(5*scale)), (fx + int(4*scale), fl_y), (fx, fl_y + int(5*scale)), (fx - int(4*scale), fl_y)]
                pygame.draw.polygon(ts, ornate_color, pts)

            sub_y = ty + title.get_height() + int(12 * scale)
            sub_text = _("— Crafting Compendium —")
            sub = self._render_text(cfg.INV_nums_font, sub_text, (140, 120, 80))
            ts.blit(sub, (w // 4 - sub.get_width() // 2, sub_y))
            self._card_bg_cache[title_key] = ts

        if self.current_spread == 0:
            content_surf.blit(self._card_bg_cache[title_key], (0, 0))

        # Ornate page numbers with decoration (cached per spread)
        num_color = (160, 130, 80)
        page_left = self.current_spread * 2 + 1
        page_right = self.current_spread * 2 + 2

        page_num_key = (page_left, page_right, scale)
        if page_num_key not in self._card_bg_cache:
            left_num = self._render_text(cfg.INV_nums_font, str(page_left), num_color)
            lx = int(32 * scale)
            ly = h - int(35 * scale)

            right_num = self._render_text(cfg.INV_nums_font, str(page_right), num_color)
            rx = w - int(40 * scale) - right_num.get_width()
            ry = h - int(35 * scale)

            pn_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pn_surf.blit(left_num, (lx, ly))
            for li in range(int(18 * scale)):
                a = int(70 * (1.0 - li / (18 * scale)))
                pn_surf.set_at((lx - int(18 * scale) + li, ly + left_num.get_height() // 2), (*num_color, a))
            pn_surf.blit(right_num, (rx, ry))
            for li in range(int(18 * scale)):
                a = int(70 * li / (18 * scale))
                pn_surf.set_at((rx + right_num.get_width() + li, ry + right_num.get_height() // 2), (*num_color, a))
            self._card_bg_cache[page_num_key] = pn_surf
        content_surf.blit(self._card_bg_cache[page_num_key], (0, 0))

        # Decorative header flourish (cached per scale)
        header_key = ("header", scale)
        if header_key not in self._card_bg_cache:
            hdr = pygame.Surface((w, h), pygame.SRCALPHA)
            header_y = int(62 * scale)
            dot_color = (200, 175, 120)
            for side in ['left', 'right']:
                if side == 'left':
                    hx = int(28 * scale)
                    hw = w // 2 - int(56 * scale)
                else:
                    hx = w // 2 + int(28 * scale)
                    hw = w // 2 - int(56 * scale)
                for li in range(hw):
                    a = int(70 * (1.0 - abs(li - hw / 2) / (hw / 2)))
                    hdr.set_at((hx + li, header_y), (*dot_color, a))
                for cxp in [hx, hx + hw // 2, hx + hw]:
                    pts = [(cxp, header_y - int(4*scale)), (cxp + int(3*scale), header_y), (cxp, header_y + int(4*scale)), (cxp - int(3*scale), header_y)]
                    pygame.draw.polygon(hdr, dot_color, pts)
            self._card_bg_cache[header_key] = hdr
        content_surf.blit(self._card_bg_cache[header_key], (0, 0))

        start_idx = self.current_spread * self.recipes_per_spread
        end_idx = min(start_idx + self.recipes_per_spread, len(self.recipes))

        card_w = int(340 * scale)
        card_h = int(195 * scale)
        start_y = int(90 * scale)
        gap_y = int(22 * scale)

        for i in range(start_idx, end_idx):
            local_idx = i - start_idx
            recipe = self.recipes[i]
            is_right_page = local_idx >= 2
            if not is_right_page:
                x = (w // 2 - card_w) // 2
            else:
                x = w // 2 + (w // 2 - card_w) // 2
            row = local_idx % 2
            y = start_y + row * (card_h + gap_y)
            self._draw_recipe_card(content_surf, x, y, card_w, card_h, recipe, scale, i, current_time)

        content_surf.set_alpha(alpha)
        surf.blit(content_surf, (0, 0))

    @staticmethod
    def _recipe_uses_smeltery_materials(recipe):
        for row in recipe["matrix"]:
            for ingredient in row:
                if ingredient in ("iron_ingot", "steel_ingot"):
                    return True
        return False

    def _draw_recipe_card(self, surf, x, y, w, h, recipe, scale, recipe_idx, current_time):
        card_rect = pygame.Rect(x, y, w, h)
        hover_amount = self.card_hover_animations.get(recipe_idx, 0.0)

        current_time_ms = pygame.time.get_ticks()
        if self.is_flipping:
            t = (current_time_ms - self.flip_start_time) / self.flip_duration
            if t < 0.5:
                return
            else:
                entry_progress = ease_in_out_quad((t - 0.5) * 2)
        else:
            entry_progress = 1.0

        scale_amount = 1.0 + hover_amount * 0.08
        offset_y = int(hover_amount * -12 * scale)
        scaled_rect = pygame.Rect(
            int(x + (w * (1 - scale_amount)) / 2),
            int(y + offset_y),
            int(w * scale_amount),
            int(h * scale_amount)
        )

        content_x = scaled_rect.x
        content_y = scaled_rect.y

        # Shadow (only one card hovered, draw directly)
        if hover_amount > 0.1:
            pad = int(16 * scale)
            sw = scaled_rect.width + pad * 2
            sh = scaled_rect.height + pad * 2
            shadow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            shadow_a = int(120 * hover_amount)
            pygame.draw.rect(shadow_surf, (0, 0, 0, shadow_a), shadow_surf.get_rect(), border_radius=int(12 * scale))
            surf.blit(shadow_surf, (scaled_rect.x - pad, scaled_rect.y + pad))

        # Cached card background (parchment + borders + corners)
        bg_key = (w, h, scale)
        if bg_key not in self._card_bg_cache:
            bg = pygame.Surface((int(w * (1 + 0.08)), int(h * (1 + 0.08))), pygame.SRCALPHA)
            bg_w, bg_h = bg.get_size()
            bg_rect = pygame.Rect(0, 0, bg_w, bg_h)
            card_base = (238, 225, 198)
            pygame.draw.rect(bg, card_base, bg_rect, border_radius=int(10 * scale))
            # Parchment grain
            for _ in range(200):
                tx = random.randint(0, bg_w - 1)
                ty = random.randint(0, bg_h - 1)
                shade = random.randint(0, 1)
                c = (175, 155, 115) if shade else (215, 195, 165)
                bg.set_at((tx, ty), (*c, random.randint(5, 18)))
            # Triple golden border
            outer_border_colors = [(212, 175, 55), (190, 160, 70), (160, 130, 60)]
            for bi, bc in enumerate(outer_border_colors):
                inset = bi * int(2 * scale)
                rect = pygame.Rect(inset, inset, bg_w - inset * 2, bg_h - inset * 2)
                pygame.draw.rect(bg, bc, rect, width=1, border_radius=int(10 * scale - bi * 2))
            # Corner decorations
            corner_off = int(6 * scale)
            corner_sz = int(12 * scale)
            gold_d = (212, 175, 55)
            for cx, cy in [(corner_off, corner_off), (bg_w - corner_off, corner_off),
                           (corner_off, bg_h - corner_off), (bg_w - corner_off, bg_h - corner_off)]:
                pts = [(cx, cy - corner_sz), (cx + corner_sz // 2, cy), (cx, cy + corner_sz), (cx - corner_sz // 2, cy)]
                pygame.draw.circle(bg, gold_d, (cx, cy), corner_sz, 1)
                pygame.draw.line(bg, gold_d, (cx - corner_sz, cy), (cx + corner_sz, cy), 1)
                pygame.draw.line(bg, gold_d, (cx, cy - corner_sz), (cx, cy + corner_sz), 1)
            self._card_bg_cache[bg_key] = bg

        surf.blit(self._card_bg_cache[bg_key], scaled_rect.topleft, area=(0, 0, scaled_rect.width, scaled_rect.height))

        # Glow on hover (only one card hovered at a time, draw directly)
        if hover_amount > 0.2:
            glow_surf = pygame.Surface((scaled_rect.width, scaled_rect.height), pygame.SRCALPHA)
            glow_a = int(100 * hover_amount)
            pygame.draw.rect(glow_surf, (255, 215, 0, glow_a), glow_surf.get_rect(), width=max(1, int(2.5 * scale)), border_radius=int(10 * scale))
            surf.blit(glow_surf, scaled_rect.topleft)

        # Title
        formatted_name = recipe['result_id'].replace("_", " ").title()
        title_text = self._render_text(cfg.INV_nums_font, formatted_name, (55, 35, 18))
        surf.blit(title_text, (content_x + int(15 * scale), content_y + int(10 * scale)))

        # "Smeltery only" badge for advanced recipes
        if self._recipe_uses_smeltery_materials(recipe):
            badge_text = "SMELTERY"
            badge_color = (200, 120, 40)
            badge_font_size = max(8, int(13 * scale))
            badge_font = cfg.get_font(badge_font_size)
            badge_surf = badge_font.render(badge_text, True, badge_color)
            badge_pad = int(4 * scale)
            badge_x = scaled_rect.right - badge_surf.get_width() - int(10 * scale)
            badge_y = content_y + int(12 * scale)
            badge_bg_rect = pygame.Rect(
                badge_x - badge_pad, badge_y - int(2 * scale),
                badge_surf.get_width() + badge_pad * 2,
                badge_surf.get_height() + int(4 * scale),
            )
            bg_surf = pygame.Surface(badge_bg_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(bg_surf, (60, 40, 20, 200), bg_surf.get_rect(), border_radius=int(3 * scale))
            surf.blit(bg_surf, badge_bg_rect.topleft)
            pygame.draw.rect(surf, badge_color, badge_bg_rect, width=1, border_radius=int(3 * scale))
            surf.blit(badge_surf, (badge_x, badge_y))

        # Golden underline
        ul_y = content_y + int(10 * scale) + title_text.get_height() + int(3 * scale)
        ul_x = content_x + int(15 * scale)
        ul_w = max(int(60 * scale), title_text.get_width())
        for ui in range(ul_w):
            a = int(100 * (1.0 - abs(ui - ul_w / 2) / (ul_w / 2)))
            surf.set_at((ul_x + ui, ul_y), (212, 175, 55, a))
            surf.set_at((ul_x + ui, ul_y + 1), (180, 150, 80, a // 2))

        # 3x3 grid
        grid_slot_size = int(33 * scale)
        grid_padding = int(4 * scale)
        grid_start_x = content_x + int(18 * scale)
        grid_start_y = content_y + int(42 * scale)

        # Grid frame
        grid_frame_w = 3 * (grid_slot_size + grid_padding) - grid_padding + int(10 * scale)
        grid_frame_h = 3 * (grid_slot_size + grid_padding) - grid_padding + int(10 * scale)
        grid_frame_rect = pygame.Rect(grid_start_x - int(5 * scale), grid_start_y - int(5 * scale),
                                       grid_frame_w, grid_frame_h)
        pygame.draw.rect(surf, (160, 140, 110), grid_frame_rect, width=1, border_radius=int(4 * scale))
        pygame.draw.rect(surf, (180, 160, 130), grid_frame_rect.inflate(-int(3*scale), -int(3*scale)), width=1, border_radius=int(3 * scale))

        matrix = recipe["matrix"]
        for row in range(3):
            for col in range(3):
                slot_x = grid_start_x + col * (grid_slot_size + grid_padding)
                slot_y = grid_start_y + row * (grid_slot_size + grid_padding)
                slot_rect = pygame.Rect(slot_x, slot_y, grid_slot_size, grid_slot_size)

                slot_bg = (215, 200, 170) if hover_amount < 0.3 else (228, 213, 183)
                pygame.draw.rect(surf, slot_bg, slot_rect, border_radius=int(3 * scale))
                pygame.draw.rect(surf, (150, 130, 100), slot_rect, width=1, border_radius=int(3 * scale))

                ingredient = matrix[col][row]
                if ingredient:
                    img = self._pre_scaled_grid.get(ingredient)
                    if img is None:
                        raw = self.item_images.get(ingredient)
                        if raw:
                            icon_size = grid_slot_size - int(6 * scale)
                            img = pygame.transform.scale(raw, (icon_size, icon_size))
                            self._pre_scaled_grid[ingredient] = img
                    if img:
                        img_rect = img.get_rect(center=slot_rect.center)
                        surf.blit(img, img_rect)
                    else:
                        ing_text = self._render_text(cfg.INV_nums_font, ingredient[:3].capitalize(), (80, 60, 40))
                        tx = slot_x + (grid_slot_size - ing_text.get_width()) // 2
                        ty = slot_y + (grid_slot_size - ing_text.get_height()) // 2
                        surf.blit(ing_text, (tx, ty))

        # Ornate arrow
        arrow_x = grid_start_x + 3 * (grid_slot_size + grid_padding) + int(12 * scale)
        arrow_y = grid_start_y + grid_slot_size + (grid_padding // 2) - int(5 * scale)

        arrow_color = (int(160 + hover_amount * 40), int(130 + hover_amount * 30), 50 + int(hover_amount * 30))
        line_w = max(2, int(3 * scale))
        shaft_len = int(34 * scale)
        pygame.draw.line(surf, arrow_color, (arrow_x, arrow_y), (arrow_x + shaft_len, arrow_y), line_w)

        head_size = int(10 * scale)
        pygame.draw.line(surf, arrow_color, (arrow_x + shaft_len - head_size, arrow_y - head_size // 2), (arrow_x + shaft_len, arrow_y), line_w)
        pygame.draw.line(surf, arrow_color, (arrow_x + shaft_len - head_size, arrow_y + head_size // 2), (arrow_x + shaft_len, arrow_y), line_w)

        for di in range(3):
            dx = arrow_x + int(shaft_len * (di + 1) / 4)
            pygame.draw.circle(surf, arrow_color, (dx, arrow_y), max(1, int(2 * scale)))

        # Result slot - ornate golden frame
        out_size = int(58 * scale)
        out_x = arrow_x + shaft_len + int(14 * scale)
        out_y = arrow_y - out_size // 2
        out_rect = pygame.Rect(out_x, out_y, out_size, out_size)

        for fi in range(3):
            frect = pygame.Rect(out_x - fi, out_y - fi, out_size + fi * 2, out_size + fi * 2)
            fc = [(212, 175, 55), (180, 150, 80), (150, 120, 50)][fi]
            pygame.draw.rect(surf, fc, frect, width=max(1, int(2.5 * scale - fi)), border_radius=int(9 * scale - fi * 2))

        result_bg = (int(215 - hover_amount * 10), int(200 - hover_amount * 5), int(165 - hover_amount * 10))
        inner_rect = pygame.Rect(out_x + int(4 * scale), out_y + int(4 * scale),
                                  out_size - int(8 * scale), out_size - int(8 * scale))
        pygame.draw.rect(surf, result_bg, inner_rect, border_radius=int(5 * scale))

        if hover_amount > 0.2:
            og_key = ("og", out_size, scale)
            if og_key not in self._card_bg_cache:
                og = pygame.Surface((out_size, out_size), pygame.SRCALPHA)
                pygame.draw.rect(og, (255, 215, 0, 80), og.get_rect(), border_radius=int(8 * scale))
                self._card_bg_cache[og_key] = og
            og_surf = self._card_bg_cache[og_key]
            og_copy = og_surf.copy()
            og_copy.set_alpha(int(255 * min(1.0, hover_amount)))
            surf.blit(og_copy, (out_x, out_y))

        res_id = recipe['result_id']
        img = self._pre_scaled_result.get(res_id)
        if img is None:
            raw = self.item_images.get(res_id)
            if raw:
                res_icon_size = out_size - int(14 * scale)
                img = pygame.transform.scale(raw, (res_icon_size, res_icon_size))
                self._pre_scaled_result[res_id] = img
        if img:
            img_rect = img.get_rect(center=out_rect.center)
            surf.blit(img, img_rect)
        else:
            res_short = self._render_text(cfg.INV_nums_font, res_id[:3].capitalize(), (60, 120, 60))
            rx = out_x + (out_size - res_short.get_width()) // 2
            ry = out_y + (out_size - res_short.get_height()) // 2
            surf.blit(res_short, (rx, ry))

        # Quantity badge
        if recipe['amount'] > 1:
            badge_size = int(20 * scale)
            badge_x = out_x + out_size - badge_size
            badge_y = out_y + out_size - badge_size
            badge_rect = pygame.Rect(badge_x, badge_y, badge_size, badge_size)
            pygame.draw.rect(surf, (180, 30, 30), badge_rect, border_radius=int(badge_size // 2))
            pygame.draw.rect(surf, (255, 80, 80), badge_rect, width=1, border_radius=int(badge_size // 2))
            # White outline ring
            pygame.draw.rect(surf, (255, 200, 200), badge_rect.inflate(-2, -2), width=1, border_radius=int(badge_size // 2))
            out_amt = self._render_text(cfg.INV_nums_font, f"x{recipe['amount']}", (255, 255, 255))
            amt_x = badge_x + (badge_size - out_amt.get_width()) // 2
            amt_y = badge_y + (badge_size - out_amt.get_height()) // 2
            surf.blit(out_amt, (amt_x, amt_y))

        # Entry animation
        if self.is_flipping:
            pass
