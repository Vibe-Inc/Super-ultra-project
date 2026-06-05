import math
import os
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

        self._card_back_tex = None
        self._card_back_scaled = None
        self._card_scaled_rings = []
        self._load_card_back()
        self.card_ring_offsets = [0.0, 0.0, 0.0, 0.0]

        self.tarot_cards = []
        self._load_tarot_cards()

        self.revealed_cards = []
        self._revealed_numbers = set()
        self.reveal_button = None
        reveal_w = max(160, int(220 * scale))
        reveal_h = max(40, int(48 * scale))
        self.reveal_button = Button(
            pygame.Rect(0, 0, reveal_w, reveal_h),
            _("⟐ Reveal Secret ⟐"),
            (80, 35, 110),
            (120, 55, 160),
            cfg.get_font(max(12, int(18 * scale))),
            (220, 200, 240),
            cfg.corner_radius,
            on_click=self._reveal_secret,
        )
        self.buttons.append(self.reveal_button)
        self._reveal_cost = 1

        self.card_effects = {
            0:  {"mana": 5,  "hp": 0,   "regen": 0.0, "desc": _("The Fool walks where angels fear to tread. A blank slate, full of potential.")},
            1:  {"mana": 10, "hp": 0,   "regen": 0.3, "desc": _("The Magician channels the elements. Your mana reganition quickens.")},
            2:  {"mana": 15, "hp": 10,  "regen": 0.0, "desc": _("The High Priestess guards the temple of inner wisdom. Vitality blooms within.")},
            3:  {"mana": 10, "hp": 0,   "regen": 0.0, "desc": _("The Empress nurtures all life. The veil between worlds grows thin.")},
            4:  {"mana": 10, "hp": 15,  "regen": 0.0, "desc": _("The Emperor imposes order upon chaos. Your constitution hardens.")},
            5:  {"mana": 10, "hp": 0,   "regen": 0.0, "desc": _("The Hierophant speaks in riddles and parables. Seek meaning in the mundane.")},
            6:  {"mana": 8,  "hp": 0,   "regen": 0.0, "desc": _("The Lovers bind fate to choice. Not all bonds are visible to the eye.")},
            7:  {"mana": 8,  "hp": 0,   "regen": 0.0, "desc": _("The Chariot triumphs through will alone. Forward, always forward.")},
            8:  {"mana": 12, "hp": 0,   "regen": 0.0, "desc": _("Justice weighs all deeds. The scales do not forget.")},
            9:  {"mana": 15, "hp": 0,   "regen": 0.5, "desc": _("The Hermit seeks truth in solitude. Light your own lantern.")},
            10: {"mana": 10, "hp": 0,   "regen": 0.0, "desc": _("The Wheel of Fortune turns endlessly. What goes around, comes around.")},
            11: {"mana": 8,  "hp": 20,  "regen": 0.0, "desc": _("Strength is not merely muscle — it is the courage to endure.")},
            12: {"mana": 15, "hp": 0,   "regen": 0.0, "desc": _("The Hanged Man sees the world upside down. Wisdom comes from surrender.")},
            13: {"mana": 20, "hp": 0,   "regen": 0.0, "desc": _("Death is not the end, but a transformation. Let the old self fall away.")},
            14: {"mana": 10, "hp": 10,  "regen": 0.0, "desc": _("Temperance blends opposites into harmony. Balance is the highest art.")},
            15: {"mana": 15, "hp": 0,   "regen": 0.0, "desc": _("The Devil binds with chains of illusion. Break them, or be consumed.")},
            16: {"mana": 12, "hp": 0,   "regen": 0.0, "desc": _("The Tower falls so that something new may rise. Destruction paves the way.")},
            17: {"mana": 20, "hp": 0,   "regen": 1.0, "desc": _("The Star shines in the darkest night. Hope is a compass that never fails.")},
            18: {"mana": 15, "hp": 25,  "regen": 0.0, "desc": _("The Moon reveals what lurks beneath. Not all shadows are enemies.")},
            19: {"mana": 20, "hp": 15,  "regen": 1.5, "desc": _("The Sun banishes all doubt. Warmth and clarity flood the soul.")},
            20: {"mana": 25, "hp": 0,   "regen": 0.0, "desc": _("Judgement calls all to account. Rise and be measured.")},
            21: {"mana": 30, "hp": 30,  "regen": 2.0, "desc": _("The World completes the great cycle. All paths converge here.")},
        }

        self._selected_card = None
        self._sel_progress = 0.0
        self._sel_card_front_large = None

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

    def _load_card_back(self):
        scale = cfg.ui_scale()
        path = "assets/tarot/_cardBack/_cardBack_5x.png"
        try:
            full = pygame.image.load(path).convert_alpha()
        except Exception:
            full = pygame.Surface((230, 405), pygame.SRCALPHA)
            full.fill((60, 30, 80))
        card_w = int(55 * scale)
        card_h = int(full.get_height() * card_w / full.get_width())
        self._card_back_tex = full
        self._card_back_scaled = pygame.transform.smoothscale(full, (card_w, card_h))
        ring_scales = [0.70, 0.85, 1.00, 1.15]
        self._card_scaled_rings = []
        for sf in ring_scales:
            sw = int(card_w * sf)
            sh = int(card_h * sf)
            self._card_scaled_rings.append(pygame.transform.smoothscale(full, (sw, sh)))

    def _load_tarot_cards(self):
        self.tarot_cards = []
        base = "assets/tarot"
        scale = cfg.ui_scale()
        try:
            entries = sorted(os.listdir(base))
        except Exception:
            return
        for entry in entries:
            folder = os.path.join(base, entry)
            if not os.path.isdir(folder) or entry == "_cardBack":
                continue
            parts = entry.split("_", 1)
            if not parts[0].isdigit():
                continue
            num = int(parts[0])
            name = parts[1] if len(parts) > 1 else entry
            img_path = None
            for f in os.listdir(folder):
                if f.lower().endswith("_5x.png") and "back" not in f.lower():
                    img_path = os.path.join(folder, f)
                    break
            if img_path is None:
                continue
            try:
                full = pygame.image.load(img_path).convert_alpha()
            except Exception:
                continue
            card_w = int(70 * scale)
            card_h = int(full.get_height() * card_w / full.get_width())
            scaled = pygame.transform.smoothscale(full, (card_w, card_h))
            self.tarot_cards.append({
                "num": num,
                "name": name,
                "front": scaled,
            })
        self.tarot_cards.sort(key=lambda c: c["num"])

    def _pick_weighted_card(self):
        available = [c for c in self.tarot_cards if c["num"] not in self._revealed_numbers]
        if not available:
            return None
        weights = [max(1, 22 - c["num"]) for c in available]
        total = sum(weights)
        r = random.uniform(0, total)
        acc = 0
        for i, w in enumerate(weights):
            acc += w
            if r <= acc:
                return available[i]
        return available[-1]

    def _reveal_secret(self):
        stars = getattr(self.app, "purple_stars", 0)
        if stars < self._reveal_cost:
            return
        card = self._pick_weighted_card()
        if card is None:
            return
        self.app.purple_stars = stars - self._reveal_cost
        self._revealed_numbers.add(card["num"])

        ring_slots = [8, 10, 14, 18]
        num = card["num"]
        if num >= 16:
            ring_idx = 0
        elif num >= 11:
            ring_idx = 1
        elif num >= 6:
            ring_idx = 2
        else:
            ring_idx = 3

        occupied = {(rc["ring_idx"], rc["slot_idx"]) for rc in self.revealed_cards}
        slot_idx = 0
        for s in range(ring_slots[ring_idx]):
            if (ring_idx, s) not in occupied:
                slot_idx = s
                break

        self.revealed_cards.append({
            "card": card,
            "ring_idx": ring_idx,
            "slot_idx": slot_idx,
            "progress": 0.0,
            "float_offset": random.uniform(0, math.pi * 2),
        })

        eff = self.card_effects.get(card["num"])
        if eff:
            try:
                gs = self.app.manager.states.get("gameplay")
                if gs and hasattr(gs, "character"):
                    ch = gs.character
                    if hasattr(ch, "mana_system"):
                        ch.mana_system.increase_max_mana(eff["mana"])
                    if eff["hp"]:
                        ch.max_hp += eff["hp"]
                        ch.hp = min(ch.max_hp, ch.hp + eff["hp"])
                    if eff["regen"] and hasattr(ch, "mana_system"):
                        ch.mana_system.mana_regen_rate += eff["regen"]
            except Exception:
                pass

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

        if self.reveal_button:
            rev_w = max(160, int(self.sidebar_rect.width * 0.8))
            rev_h = max(40, int(48 * scale))
            rev_y = self.exit_button.rect.top - rev_h - int(12 * scale)
            self.reveal_button.rect = pygame.Rect(
                self.sidebar_rect.centerx - rev_w // 2,
                rev_y,
                rev_w,
                rev_h,
            )
            try:
                self.reveal_button._update_text_surface()
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

        speed_mul = 0.0 if self._selected_card is not None else 1.0
        ring_speeds = [0.003, -0.005, 0.008, -0.010]
        for i, speed in enumerate(ring_speeds):
            self.card_ring_offsets[i] = (self.card_ring_offsets[i] + speed * speed_mul * dt * 60) % (math.pi * 2)

        for rc in self.revealed_cards:
            rc["progress"] = min(1.0, rc["progress"] + dt * 2.0)

        if self._selected_card is not None:
            self._sel_progress = min(1.0, self._sel_progress + dt * 3.0)
        else:
            self._sel_progress = max(0.0, self._sel_progress - dt * 4.0)

    def _get_reveal_card_rects(self):
        rects = []
        if not self.revealed_cards:
            return rects
        cx, cy = self.tree_rect.center
        rings = [(120, 8), (200, 10), (280, 14), (370, 18)]
        for rc in self.revealed_cards:
            prog = rc["progress"]
            ease = 1.0 - (1.0 - prog) ** 3
            if ease < 0.85:
                continue
            ri = rc["ring_idx"]
            radius, count = rings[ri]
            offset = self.card_ring_offsets[ri]
            angle = offset + rc["slot_idx"] * 2 * math.pi / count
            tx = cx + math.cos(angle) * radius
            ty = cy + math.sin(angle) * radius
            px = cx + (tx - cx) * ease
            py = cy + (ty - cy) * ease
            ring_card = self._card_scaled_rings[ri]
            w = ring_card.get_width()
            h = ring_card.get_height()
            r = pygame.Rect(0, 0, int(w * 1.5), int(h * 1.5))
            r.center = (int(px), int(py))
            rects.append((r, rc))
        return rects

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F8:
            self.app.purple_stars = getattr(self.app, "purple_stars", 0) + 10
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self._selected_card is not None:
                sw, sh = self.tree_rect.size
                panel_w = int(sw * 0.85)
                panel_h = int(sh * 0.85)
                panel_x = self.tree_rect.x + (sw - panel_w) // 2
                panel_y = self.tree_rect.y + (sh - panel_h) // 2
                panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
                close_r = pygame.Rect(panel_rect.right - 44, panel_rect.y + 10, 34, 34)
                if not panel_rect.collidepoint(pos) or close_r.collidepoint(pos):
                    self._selected_card = None
                    self._sel_card_front_large = None
                return
            for rect, rc in self._get_reveal_card_rects():
                if rect.collidepoint(pos):
                    card = rc["card"]
                    large = pygame.transform.smoothscale(
                        card["front"],
                        (int(card["front"].get_width() * 2.5),
                         int(card["front"].get_height() * 2.5))
                    )
                    self._selected_card = rc
                    self._sel_card_front_large = large
                    self._sel_progress = 0.0
                    break

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

    def _draw_card_rings(self, surface):
        if self._card_back_scaled is None:
            return
        t = self.animation_time
        cx, cy = self.tree_rect.center
        rings = [
            (120,  8,  0.80),
            (200, 10, 1.00),
            (280, 14, 1.15),
            (370, 18, 1.30),
        ]
        base_alpha = 55
        revealed_slots = {(rc["ring_idx"], rc["slot_idx"]) for rc in self.revealed_cards}
        for ri, (radius, count, scale_f) in enumerate(rings):
            offset = self.card_ring_offsets[ri]
            scaled = self._card_scaled_rings[ri]
            for i in range(count):
                if (ri, i) in revealed_slots:
                    continue
                angle = offset + i * 2 * math.pi / count
                px = cx + math.cos(angle) * radius
                py = cy + math.sin(angle) * radius
                rot_angle = math.degrees(angle) + 90
                rotated = pygame.transform.rotate(scaled, rot_angle)
                fade = 0.7 + 0.3 * math.sin(t * 0.3 + ri + i)
                rotated.set_alpha(int(base_alpha * scale_f * fade))
                rect = rotated.get_rect(center=(int(px), int(py)))
                surface.blit(rotated, rect)

    def _draw_revealed_cards(self, surface):
        if not self.revealed_cards:
            return
        t = self.animation_time
        cx, cy = self.tree_rect.center
        rings = [
            (120,  8,  0.80),
            (200, 10, 1.00),
            (280, 14, 1.15),
            (370, 18, 1.30),
        ]
        for rc in self.revealed_cards:
            card = rc["card"]
            prog = rc["progress"]
            ease = 1.0 - (1.0 - prog) ** 3
            if ease < 0.01:
                continue

            ri = rc["ring_idx"]
            radius, count, scale_f = rings[ri]
            offset = self.card_ring_offsets[ri]
            slot_angle = offset + rc["slot_idx"] * 2 * math.pi / count
            tx = cx + math.cos(slot_angle) * radius
            ty = cy + math.sin(slot_angle) * radius

            px = cx + (tx - cx) * ease
            py = cy + (ty - cy) * ease

            ring_card = self._card_scaled_rings[ri]
            target_w = ring_card.get_width()
            s = 0.1 + 0.9 * ease
            display_w = max(1, int(target_w * s))
            surf = card["front"]
            ar = surf.get_height() / max(1, surf.get_width())
            display_h = max(1, int(display_w * ar))

            rot_angle = math.degrees(slot_angle) + 90
            rot_angle += math.sin(t * 0.3 + rc["float_offset"]) * 2

            scaled = pygame.transform.smoothscale(surf, (display_w, display_h))
            rotated = pygame.transform.rotate(scaled, rot_angle)
            rotated.set_alpha(int(230 * (0.3 + 0.7 * ease)))

            glow_r = max(display_w, display_h)
            glow_surf = pygame.Surface((glow_r * 3, glow_r * 3), pygame.SRCALPHA)
            glow_a = int(30 * ease * (0.6 + 0.4 * math.sin(t * 1.2 + rc["float_offset"])))
            pygame.draw.circle(glow_surf, (160, 80, 240, glow_a),
                               (glow_r * 1.5, glow_r * 1.5), glow_r * 1.2)
            surface.blit(glow_surf, (px - glow_r * 1.5, py - glow_r * 1.5))

            rect = rotated.get_rect(center=(int(px), int(py)))
            surface.blit(rotated, rect)

            if ease > 0.85:
                name_font = cfg.get_font(max(10, int(13 * cfg.ui_scale())))
                label = f"#{card['num']} {card['name']}"
                ls = name_font.render(label, True, (212, 175, 55))
                ls.set_alpha(int(160 * ease))
                lr = ls.get_rect(midtop=(int(px), rect.bottom + 3))
                surface.blit(ls, lr)

    def _draw_card_info(self, screen):
        if self._selected_card is None or self._sel_progress < 0.01:
            return
        ease = 1.0 - (1.0 - self._sel_progress) ** 3
        card = self._selected_card["card"]

        sw, sh = self.tree_rect.size
        panel_w = int(sw * 0.85)
        panel_h = int(sh * 0.85)
        px = self.tree_rect.x + (sw - panel_w) // 2
        py = self.tree_rect.y + (sh - panel_h) // 2

        overlay = pygame.Surface((self.tree_rect.width, self.tree_rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(180 * ease)))
        screen.blit(overlay, self.tree_rect.topleft)

        panel_rect = pygame.Rect(px, py, panel_w, panel_h)
        self._draw_gradient_rect(screen, panel_rect, (25, 12, 40), (12, 5, 22), border_radius=20)
        bw = max(2, int(2 * cfg.ui_scale()))
        pygame.draw.rect(screen, (140, 90, 200, int(200 * ease)), panel_rect, bw, border_radius=20)
        inner = panel_rect.inflate(-8, -8)
        pygame.draw.rect(screen, (80, 50, 110, int(120 * ease)), inner, 1, border_radius=18)

        margin = int(30 * cfg.ui_scale())
        card_img = self._sel_card_front_large
        if card_img:
            max_ch = panel_h - margin * 2
            cw, ch = card_img.get_size()
            if ch > max_ch:
                cw = int(cw * max_ch / ch)
                ch = int(max_ch)
                card_img = pygame.transform.smoothscale(card_img, (cw, ch))
            img_x = px + margin
            img_y = py + (panel_h - ch) // 2
            img_rect = pygame.Rect(img_x, img_y, cw, ch)

            glow = pygame.Surface((cw + 40, ch + 40), pygame.SRCALPHA)
            glow_a = int(40 * ease * (0.6 + 0.4 * math.sin(self.animation_time * 0.8)))
            cgx, cgy = glow.get_size()
            pygame.draw.ellipse(glow, (160, 80, 240, glow_a), (10, 10, cgx - 20, cgy - 20))
            screen.blit(glow, (img_x - 20, img_y - 20))
            screen.blit(card_img, img_rect)

            gold = (212, 175, 55)
            pygame.draw.rect(screen, (*gold, int(60 * ease)), img_rect, 1, border_radius=4)

        text_x = px + margin
        if card_img:
            text_x = img_rect.right + margin
        text_w = panel_rect.right - text_x - margin

        sec_font = cfg.get_font(max(16, int(28 * cfg.ui_scale())))
        name_text = f"#{card['num']} — {card['name']}"
        name_surf = sec_font.render(name_text, True, (240, 220, 255))
        name_surf.set_alpha(int(255 * ease))
        screen.blit(name_surf, (text_x, py + margin + 10))

        div_y = py + margin + 10 + name_surf.get_height() + 10
        for i in range(min(text_w, panel_w - margin * 2)):
            dx = text_x + i
            da = int((1.0 - abs(i / max(1, text_w - 1) - 0.5) * 2) * 100 * ease)
            pygame.draw.line(screen, (140, 80, 220, da), (dx, div_y), (dx, div_y + 1))

        eff = self.card_effects.get(card["num"])
        if eff and eff["desc"]:
            body_font = cfg.get_font(max(12, int(18 * cfg.ui_scale())))
            desc_surf = body_font.render(eff["desc"], True, (200, 190, 220))
            desc_surf.set_alpha(int(220 * ease))
            desc_y = div_y + 20
            screen.blit(desc_surf, (text_x, desc_y))

            stats_font = cfg.get_font(max(11, int(16 * cfg.ui_scale())))
            stats_y = desc_y + desc_surf.get_height() + 16
            parts = []
            if eff["mana"]:
                parts.append(f"+{eff['mana']} Max Mana")
            if eff["hp"]:
                parts.append(f"+{eff['hp']} Max HP")
            if eff["regen"]:
                parts.append(f"+{eff['regen']}/s Mana Regen")
            if parts:
                stats_text = " | ".join(parts)
                stats_surf = stats_font.render(stats_text, True, (212, 175, 55))
                stats_surf.set_alpha(int(200 * ease))
                screen.blit(stats_surf, (text_x, stats_y))

        close_font = cfg.get_font(max(14, int(20 * cfg.ui_scale())))
        close_r = pygame.Rect(panel_rect.right - 44, panel_rect.y + 10, 34, 34)
        close_a = int(150 + 105 * (0.5 + 0.5 * math.sin(self.animation_time * 2)))
        close_color = (200, 150, 255, int(close_a * ease))
        pygame.draw.circle(screen, close_color[:3], close_r.center, close_r.width // 2)
        pygame.draw.circle(screen, (100, 60, 150, int(200 * ease)), close_r.center, close_r.width // 2, 2)
        cx_mark = close_font.render("✕", True, (50, 20, 80))
        cx_mark.set_alpha(int(200 * ease))
        cx_rect = cx_mark.get_rect(center=close_r.center)
        screen.blit(cx_mark, cx_rect)

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

        narrative_y = div_y + 10 + hint.get_height() + 6
        narr_lines = [
            _("The Mysterium Magnum is a deck of 22 arcana,"),
            _("each holding a fragment of forgotten power."),
            _("Reveal them, and their essence binds to you."),
        ]
        for nli, nl in enumerate(narr_lines):
            ns = self.small_font.render(nl, True, (130, 120, 155))
            ns.set_alpha(160)
            screen.blit(ns, (r.x + 18, narrative_y + nli * (self.small_font.get_height() + 2)))

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
        self._draw_card_rings(screen)
        self._draw_revealed_cards(screen)

        screen.set_clip(old_clip)

        self._draw_sidebar(screen)
        self._draw_card_info(screen)
        self.reveal_button.draw(screen)
        self.exit_button.draw(screen)
