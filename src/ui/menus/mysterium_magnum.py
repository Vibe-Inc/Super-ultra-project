"""
Mysterium Magnum – Tarot deck menu with majestic cosmic visuals.

Optimised for smooth 60 fps: heavy textures (nebula, aurora, mandala) are
pre-rendered once and cached; only lightweight per-frame draws remain.
"""

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

# ── colour palette (module-level to avoid per-frame allocation) ────────
_PURPLE_GOLD = [
    (120, 50, 180), (180, 100, 220), (80, 30, 140),
    (212, 175, 55), (240, 210, 100), (150, 120, 50),
    (100, 200, 220), (160, 80, 200),
]
_STAR_COLORS = [
    (255, 215, 100), (212, 175, 55), (200, 130, 255),
    (140, 80, 220), (140, 220, 255), (255, 200, 180),
    (200, 180, 255), (180, 255, 230),
]
_RUNE_SYMBOLS = [
    "ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ", "ᚷ", "ᚹ",
    "ᚺ", "ᚾ", "ᛁ", "ᛃ", "ᛇ", "ᛈ", "ᛉ", "ᛊ",
    "ᛏ", "ᛒ", "ᛖ", "ᛗ", "ᛚ", "ᛝ", "ᛟ", "ᛞ",
]
_RING_DEF = [(120, 6), (200, 5), (280, 5), (370, 6)]


class MysteriumMagnumMenu(Menu):
    """Tarot-arcana selection screen with a cosmic, mystical aesthetic."""

    def __init__(self, app: "App"):
        super().__init__(app)
        scale = cfg.ui_scale()
        self.title_font = cfg.get_font(max(16, int(40 * scale)))
        self.section_font = cfg.get_font(max(16, int(28 * scale)))
        self.small_font = cfg.get_font(max(14, int(20 * scale)))

        # ── Buttons ────────────────────────────────────────────────────
        exit_w = max(120, int(200 * scale))
        exit_h = max(44, int(52 * scale))
        self.exit_button = Button(
            pygame.Rect(0, 0, exit_w, exit_h),
            _("BACK"),
            (110, 70, 70),
            (150, 95, 95),
            cfg.button_font,
            cfg.text_color,
            cfg.corner_radius,
            on_click=self.exit_menu,
        )
        self.buttons = [self.exit_button]

        rev_w = max(160, int(220 * scale))
        rev_h = max(40, int(48 * scale))
        self.reveal_button = Button(
            pygame.Rect(0, 0, rev_w, rev_h),
            _("⟐ Reveal Secret ⟐"),
            (80, 35, 110),
            (120, 55, 160),
            cfg.get_font(max(14, int(24 * scale))),
            (220, 200, 240),
            cfg.corner_radius,
            on_click=self._reveal_secret,
        )
        self.buttons.append(self.reveal_button)
        self._reveal_cost = 1

        # ── Layout rects ───────────────────────────────────────────────
        self.tree_rect = pygame.Rect(0, 0, 0, 0)
        self.sidebar_rect = pygame.Rect(0, 0, 0, 0)
        self._layout_size = None

        # ── Animation state ────────────────────────────────────────────
        self.animation_time = 0.0

        # ── Particle systems ───────────────────────────────────────────
        self.particles = []
        self._init_particles()
        self.pentagrams = []
        self._init_pentagrams()
        self.runes = []
        self._init_runes()
        self.magic_circles = []
        self._init_magic_circles()
        self._rune_spirits = []
        self._init_rune_spirits()
        self._ember_particles = []
        self._init_embers()

        # ── Caches (heavy pre-rendered surfaces) ───────────────────────
        self._nebula_cache = None
        self._aurora_cache = None
        self._mandala_cache = None
        self._vignette_cache = None
        self._border_energy_cache = None
        self._gradient_cache = {}
        self._star_surface_pool = {}  # cached tiny star surf per (color_key, size_bucket)

        # ── Card back + rings ──────────────────────────────────────────
        self._card_back_tex = None
        self._card_back_scaled = None
        self._card_scaled_rings = []
        self._load_card_back()
        self.card_ring_offsets = [0.0, 0.0, 0.0, 0.0]

        # ── Tarot cards ────────────────────────────────────────────────
        self.tarot_cards = []
        self._load_tarot_cards()

        # ── Reveal state ───────────────────────────────────────────────
        self.revealed_cards = []
        self._revealed_numbers = set()
        self._reveal_bursts: list[dict] = []

        # ── Selection overlay ──────────────────────────────────────────
        self._selected_card = None
        self._sel_progress = 0.0
        self._sel_card_front_large = None

        # ── Cached background elements ─────────────────────────────────
        self._cached_stars: list[dict] = []
        self._cached_constellations: list[tuple] = []
        self._entrance_progress = 1.0
        self._entrance_active = False

        # ── Card effects (inside __init__ so _() is available) ─────────
        self.card_effects = {
            0:  {"mana": 5,  "regen": 0.0, "hp_regen": 0.0, "speed": 0.0, "cdr": 0.0, "atk_spd": 0.0, "dmg": 0, "stam": 0.0, "desc": _("The Fool walks where angels fear to tread. A blank slate, full of potential.")},
            1:  {"mana": 10, "regen": 0.3, "hp_regen": 0.0, "speed": 0.0, "cdr": 0.0, "atk_spd": 0.0, "dmg": 0, "stam": 0.0, "desc": _("The Magician channels the elements. Your mana reganition quickens.")},
            2:  {"mana": 15, "regen": 0.0, "hp_regen": 0.0, "speed": 0.0, "cdr": 0.0, "atk_spd": 0.0, "dmg": 0, "stam": 2.5, "desc": _("The High Priestess guards the temple of inner wisdom. Stamina flows abundantly.")},
            3:  {"mana": 10, "regen": 0.0, "hp_regen": 0.5, "speed": 0.0, "cdr": 0.0, "atk_spd": 0.0, "dmg": 0, "stam": 0.0, "desc": _("The Empress nurtures all life. Your wounds mend more swiftly.")},
            4:  {"mana": 10, "regen": 0.0, "hp_regen": 0.0, "speed": 0.03, "cdr": 0.0, "atk_spd": 0.0, "dmg": 0, "stam": 0.0, "desc": _("The Emperor imposes order upon chaos. Your steps grow swifter.")},
            5:  {"mana": 10, "regen": 0.0, "hp_regen": 0.0, "speed": 0.0, "cdr": 0.0, "atk_spd": 0.0, "dmg": 3, "stam": 0.0, "desc": _("The Hierophant speaks in riddles and parables. Your strikes carry more weight.")},
            6:  {"mana": 8,  "regen": 0.0, "hp_regen": 0.0, "speed": 0.0, "cdr": 0.0, "atk_spd": 0.03, "dmg": 0, "stam": 0.0, "desc": _("The Lovers bind fate to choice. Your reflexes sharpen.")},
            7:  {"mana": 8,  "regen": 0.0, "hp_regen": 0.0, "speed": 0.03, "cdr": 0.0, "atk_spd": 0.0, "dmg": 0, "stam": 0.0, "desc": _("The Chariot triumphs through will alone. Forward, always faster.")},
            8:  {"mana": 12, "regen": 0.0, "hp_regen": 0.0, "speed": 0.0, "cdr": 0.03, "atk_spd": 0.0, "dmg": 0, "stam": 0.0, "desc": _("Justice weighs all deeds. Your skills recover more swiftly.")},
            9:  {"mana": 15, "regen": 0.5, "hp_regen": 0.0, "speed": 0.0, "cdr": 0.0, "atk_spd": 0.0, "dmg": 0, "stam": 0.0, "desc": _("The Hermit seeks truth in solitude. Light your own lantern.")},
            10: {"mana": 10, "regen": 0.0, "hp_regen": 0.0, "speed": 0.02, "cdr": 0.0, "atk_spd": 0.0, "dmg": 0, "stam": 0.0, "desc": _("The Wheel of Fortune turns endlessly. Fortune favours the swift.")},
            11: {"mana": 8,  "regen": 0.0, "hp_regen": 0.0, "speed": 0.0, "cdr": 0.0, "atk_spd": 0.0, "dmg": 5, "stam": 0.0, "desc": _("Strength is not merely muscle — it is the courage to strike true.")},
            12: {"mana": 15, "regen": 0.0, "hp_regen": 0.0, "speed": 0.0, "cdr": 0.05, "atk_spd": 0.0, "dmg": 0, "stam": 0.0, "desc": _("The Hanged Man sees the world upside down. Patience hastens all things.")},
            13: {"mana": 20, "regen": 0.0, "hp_regen": 0.0, "speed": 0.0, "cdr": 0.0, "atk_spd": 0.0, "dmg": 8, "stam": 0.0, "desc": _("Death is not the end, but a transformation. Let the old self fall away.")},
            14: {"mana": 10, "regen": 0.0, "hp_regen": 1.0, "speed": 0.0, "cdr": 0.0, "atk_spd": 0.0, "dmg": 0, "stam": 0.0, "desc": _("Temperance blends opposites into harmony. Your body mends itself.")},
            15: {"mana": 15, "regen": 0.0, "hp_regen": 0.0, "speed": 0.0, "cdr": 0.0, "atk_spd": 0.05, "dmg": 0, "stam": 0.0, "desc": _("The Devil binds with chains of illusion. Break free — strike faster.")},
            16: {"mana": 12, "regen": 0.0, "hp_regen": 0.0, "speed": 0.0, "cdr": 0.0, "atk_spd": 0.0, "dmg": 5, "stam": 0.0, "desc": _("The Tower falls so that something new may rise. Destruction fuels your blows.")},
            17: {"mana": 20, "regen": 1.0, "hp_regen": 0.0, "speed": 0.0, "cdr": 0.0, "atk_spd": 0.0, "dmg": 0, "stam": 0.0, "desc": _("The Star shines in the darkest night. Hope is a compass that never fails.")},
            18: {"mana": 15, "regen": 0.0, "hp_regen": 2.0, "speed": 0.0, "cdr": 0.0, "atk_spd": 0.0, "dmg": 0, "stam": 0.0, "desc": _("The Moon reveals what lurks beneath. The dark grants you resilience.")},
            19: {"mana": 20, "regen": 1.5, "hp_regen": 0.0, "speed": 0.05, "cdr": 0.0, "atk_spd": 0.0, "dmg": 0, "stam": 0.0, "desc": _("The Sun banishes all doubt. Warmth and speed flood your veins.")},
            20: {"mana": 25, "regen": 0.0, "hp_regen": 0.0, "speed": 0.0, "cdr": 0.10, "atk_spd": 0.0, "dmg": 0, "stam": 0.0, "desc": _("Judgement calls all to account. Rise and be swift.")},
            21: {"mana": 30, "regen": 2.0, "hp_regen": 0.0, "speed": 0.10, "cdr": 0.10, "atk_spd": 0.0, "dmg": 0, "stam": 0.0, "desc": _("The World completes the great cycle. All paths converge in you.")},
        }

        # ── Hover state ────────────────────────────────────────────────
        self._hovered_card_idx = -1
        self._hover_sparkles: list[dict] = []

        # ── Orbital energy trails (cached paths) ───────────────────────
        self._orbital_trail_cache = None

    # ── Initialisation helpers ─────────────────────────────────────────

    def _init_particles(self):
        for _ in range(70):
            self.particles.append({
                "x": random.uniform(-900, 900),
                "y": random.uniform(-700, 700),
                "size": random.uniform(1, 4),
                "speed_x": random.uniform(-0.2, 0.2),
                "speed_y": random.uniform(-0.4, -0.05),
                "alpha": random.uniform(0.15, 0.6),
                "pulse_speed": random.uniform(0.5, 2.5),
                "color": random.choice(_PURPLE_GOLD),
                "pulse_offset": random.uniform(0, math.pi * 2),
            })

    def _init_embers(self):
        """Slowly rising golden ember particles – adds warmth."""
        for _ in range(30):
            self._ember_particles.append({
                "x": random.uniform(-400, 400),
                "y": random.uniform(-300, 300),
                "size": random.uniform(1, 3),
                "speed_x": random.uniform(-0.15, 0.15),
                "speed_y": random.uniform(-0.6, -0.15),
                "alpha": random.uniform(0.2, 0.7),
                "phase": random.uniform(0, math.pi * 2),
                "color": random.choice([(255, 200, 80), (255, 170, 60), (240, 220, 120)]),
            })

    def _init_pentagrams(self):
        pentagram_palette = [
            (180, 120, 255), (212, 175, 55), (140, 60, 200),
            (100, 200, 220), (255, 180, 100), (160, 80, 240),
            (200, 140, 255), (240, 200, 80),
        ]
        rng = random.Random(42)
        cols, rows = 2, 2
        cell_w = 1200 / cols
        cell_h = 1000 / rows
        positions = []
        for row in range(rows):
            for col in range(cols):
                x_min = -600 + col * cell_w
                x_max = x_min + cell_w
                y_min = -500 + row * cell_h
                y_max = y_min + cell_h
                margin = 80
                x = rng.uniform(x_min + margin, x_max - margin)
                y = rng.uniform(y_min + margin, y_max - margin)
                positions.append((x, y))
        for x, y in positions:
            base_color = rng.choice(pentagram_palette)
            glow_color = (
                min(255, base_color[0] + rng.randint(-20, 20)),
                min(255, base_color[1] + rng.randint(-20, 20)),
                min(255, base_color[2] + rng.randint(-15, 15)),
            )
            self.pentagrams.append({
                "x": x,
                "y": y,
                "size": rng.uniform(25, 60),
                "rotation": rng.uniform(0, math.pi * 2),
                "rot_speed": rng.uniform(-0.08, 0.08),
                "alpha": rng.uniform(0.03, 0.09),
                "pulse_speed": rng.uniform(0.2, 0.5),
                "pulse_offset": rng.uniform(0, math.pi * 2),
                "color": base_color,
                "glow_color": glow_color,
                "layer_count": 1,
                "ring_count": rng.randint(0, 1),
                "has_inner_pentagon": rng.random() > 0.5,
                "orbit_particles": 0,
                "orbit_speed": 0,
                "orbit_offset": 0,
                "orbit_radius_factor": 1.3,
                "color_shift_speed": rng.uniform(0.05, 0.15),
            })

    def _init_runes(self):
        for _ in range(18):
            self.runes.append({
                "x": random.uniform(-800, 800),
                "y": random.uniform(-650, 650),
                "symbol": random.choice(_RUNE_SYMBOLS),
                "size": random.uniform(12, 28),
                "alpha": random.uniform(0.05, 0.16),
                "pulse_speed": random.uniform(0.3, 1.0),
                "pulse_offset": random.uniform(0, math.pi * 2),
                "color": random.choice([(200, 170, 255), (255, 215, 100), (180, 100, 240)]),
            })

    def _init_magic_circles(self):
        for _ in range(3):
            self.magic_circles.append({
                "x": random.uniform(-500, 500),
                "y": random.uniform(-400, 400),
                "radius": random.uniform(60, 140),
                "rotation": random.uniform(0, math.pi * 2),
                "rot_speed": random.uniform(-0.06, 0.06),
                "alpha": random.uniform(0.05, 0.12),
                "pulse_speed": random.uniform(0.2, 0.6),
                "pulse_offset": random.uniform(0, math.pi * 2),
                "color": random.choice([(140, 80, 220), (212, 175, 55), (80, 40, 160)]),
                "ring_count": random.randint(2, 3),
            })

    def _init_rune_spirits(self):
        self._rune_spirits = []
        for _ in range(10):
            d = {
                "x": random.uniform(-500, 500),
                "y": random.uniform(-400, 400),
                "vx": random.uniform(-3, 3),
                "vy": random.uniform(-8, -3),
                "char": random.choice(_RUNE_SYMBOLS[:16]),
                "size": random.uniform(14, 26),
                "alpha": random.uniform(0.04, 0.12),
                "rot": random.uniform(0, math.pi * 2),
                "rot_speed": random.uniform(-0.3, 0.3),
                "phase": random.uniform(0, math.pi * 2),
                "life": random.uniform(3.0, 6.0),
            }
            d["max_life"] = d["life"]
            self._rune_spirits.append(d)

    # ── Asset loaders ──────────────────────────────────────────────────

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
        self._card_scaled_rings = []
        for sf in (0.70, 0.85, 1.00, 1.15):
            self._card_scaled_rings.append(
                pygame.transform.smoothscale(full, (int(card_w * sf), int(card_h * sf)))
            )

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
            self.tarot_cards.append({"num": num, "name": name, "front": scaled})
        self.tarot_cards.sort(key=lambda c: c["num"])

    # ── Card helpers ───────────────────────────────────────────────────

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

    def _spawn_burst(self, x, y, color, n=20):
        for _ in range(n):
            ang = random.uniform(0, math.pi * 2)
            speed = random.uniform(20, 120)
            self._reveal_bursts.append({
                "x": float(x), "y": float(y),
                "vx": math.cos(ang) * speed,
                "vy": math.sin(ang) * speed,
                "life": random.uniform(0.3, 1.2),
                "max_life": 1.2,
                "color": color,
                "size": random.uniform(2, 6),
            })

    def _reveal_secret(self):
        stars = getattr(self.app, "purple_stars", 0)
        if stars < self._reveal_cost:
            return
        card = self._pick_weighted_card()
        if card is None:
            return
        self.app.purple_stars = stars - self._reveal_cost
        self._revealed_numbers.add(card["num"])

        num = card["num"]
        if num >= 16:
            ring_idx, slot_idx = 0, num - 16
        elif num >= 11:
            ring_idx, slot_idx = 1, num - 11
        elif num >= 6:
            ring_idx, slot_idx = 2, num - 6
        else:
            ring_idx, slot_idx = 3, num

        self.revealed_cards.append({
            "card": card,
            "ring_idx": ring_idx,
            "slot_idx": slot_idx,
            "progress": 0.0,
            "float_offset": random.uniform(0, math.pi * 2),
        })

        cx, cy = self.tree_rect.center
        radius, count = _RING_DEF[ring_idx]
        angle = self.card_ring_offsets[ring_idx] + slot_idx * 2 * math.pi / count
        tx = cx + math.cos(angle) * radius
        ty = cy + math.sin(angle) * radius

        # Burst effects – two waves for dramatic reveal
        self._spawn_burst(cx, cy, (255, 215, 100), n=35)
        self._spawn_burst(int(tx), int(ty), (200, 130, 255), n=25)

        # Apply card gameplay effects
        eff = self.card_effects.get(card["num"])
        if eff:
            try:
                gs = self.app.manager.states.get("gameplay")
                if gs and hasattr(gs, "character"):
                    ch = gs.character
                    if hasattr(ch, "mana_system"):
                        ch.mana_system.increase_max_mana(eff["mana"])
                    if eff["regen"] and hasattr(ch, "mana_system"):
                        ch.mana_system.mana_regen_rate += eff["regen"]
                    if eff["hp_regen"]:
                        ch.regeneration = True
                        ch.regeneration_hp_per_sec += eff["hp_regen"]
                    if eff["speed"]:
                        ch.speed_multiplier *= (1.0 + eff["speed"])
                    if eff["cdr"]:
                        ch.cooldown_multiplier *= (1.0 - eff["cdr"])
                    if eff["atk_spd"]:
                        ch.attack_cooldown_mult *= (1.0 - eff["atk_spd"])
                    if eff["dmg"]:
                        ch.damage_bonus += eff["dmg"]
                    if eff["stam"]:
                        ch.stamina_regen_rate += eff["stam"]
            except Exception:
                pass

        # Extra explosion wave
        self._spawn_burst(cx, cy, (255, 255, 255), n=60)
        for _ in range(20):
            self._spawn_burst(
                cx + random.uniform(-100, 100),
                cy + random.uniform(-100, 100),
                random.choice([(255, 215, 100), (200, 130, 255), (140, 220, 255)]),
                n=8,
            )

    def _get_reveal_card_rects(self):
        rects = []
        if not self.revealed_cards:
            return rects
        cx, cy = self.tree_rect.center
        for rc in self.revealed_cards:
            prog = rc["progress"]
            ease = 1.0 - (1.0 - prog) ** 3
            if ease < 0.85:
                continue
            ri = rc["ring_idx"]
            radius, count = _RING_DEF[ri]
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

    # ── Navigation ─────────────────────────────────────────────────────

    def exit_menu(self):
        try:
            self.app.INV_manager._return_held_item()
        except Exception:
            pass
        self.app.manager.set_state("gameplay")

    # ── Layout ─────────────────────────────────────────────────────────

    def layout(self, screen):
        sw, sh = screen.get_size()
        scale = cfg.ui_scale()
        margin = max(12, int(24 * scale))
        sidebar_width = min(max(240, int(360 * scale)), max(240, sw // 3))
        tree_width = max(240, sw - sidebar_width - margin * 3)
        self.sidebar_rect = pygame.Rect(sw - sidebar_width - margin, margin, sidebar_width, sh - margin * 2)
        self.tree_rect = pygame.Rect(margin, margin, tree_width, sh - margin * 2)

        # Exit button
        exit_width = max(120, int(self.sidebar_rect.width * 0.6))
        exit_height = max(44, int(52 * scale))
        self.exit_button.rect = pygame.Rect(
            self.sidebar_rect.centerx - exit_width // 2,
            self.sidebar_rect.bottom - exit_height - margin,
            exit_width, exit_height,
        )
        try:
            self.exit_button._update_text_surface()
        except Exception:
            pass

        # Reveal button
        if self.reveal_button:
            rev_w = max(160, int(self.sidebar_rect.width * 0.8))
            rev_h = max(40, int(48 * scale))
            rev_y = self.exit_button.rect.top - rev_h - int(12 * scale)
            self.reveal_button.rect = pygame.Rect(
                self.sidebar_rect.centerx - rev_w // 2, rev_y, rev_w, rev_h,
            )
            try:
                self.reveal_button._update_text_surface()
            except Exception:
                pass

        size = (sw, sh)
        if self._layout_size != size:
            self._layout_size = size
            self._nebula_cache = None
            self._aurora_cache = None
            self._mandala_cache = None
            self._vignette_cache = None
            self._border_energy_cache = None
            self._orbital_trail_cache = None
            self._gradient_cache.clear()
            self._star_surface_pool.clear()
            self._build_cache(sw, sh)

    def on_enter(self):
        self._entrance_active = True
        self._entrance_progress = 0.0
        self._reveal_bursts.clear()

    # ── Heavy pre-render cache builders ─────────────────────────────────

    def _build_cache(self, sw: int, sh: int):
        tw, th = self.tree_rect.width, self.tree_rect.height
        cx, cy = tw // 2, th // 2

        # ── Star field (deep-space layer) ──────────────────────────────
        rng = random.Random(7)
        self._cached_stars = []
        for _ in range(180):
            sx = rng.randint(0, tw - 1)
            sy = rng.randint(0, th - 1)
            ci = rng.randint(0, len(_STAR_COLORS) - 1)
            self._cached_stars.append({
                "x": sx, "y": sy,
                "color": _STAR_COLORS[ci],
                "phase": rng.uniform(0, math.pi * 2),
                "speed": 1.5 + rng.random() * 2.0,
                "seed_a": sx * 0.08 + sy * 0.06,
            })

        # ── Constellation lines ────────────────────────────────────────
        rng2 = random.Random(13)
        pts = [(rng2.randint(0, tw - 1), rng2.randint(0, th - 1)) for _ in range(25)]
        self._cached_constellations = []
        for i, (x1, y1) in enumerate(pts):
            for j, (x2, y2) in enumerate(pts):
                if j <= i:
                    continue
                dx, dy = x2 - x1, y2 - y1
                dist = math.sqrt(dx * dx + dy * dy)
                if 20 < dist < 100:
                    self._cached_constellations.append((x1, y1, x2, y2, i))

        # ── Nebula (pre-rendered once per resize) ──────────────────────
        self._build_nebula(tw, th)

        # ── Aurora bands (pre-rendered) ────────────────────────────────
        self._build_aurora(tw, th)

        # ── Central mandala (pre-rendered) ─────────────────────────────
        self._build_mandala()

        # ── Vignette ───────────────────────────────────────────────────
        self._build_vignette(sw, sh)

        # ── Border energy texture ──────────────────────────────────────
        self._build_border_energy()

        # ── Orbital trail paths ────────────────────────────────────────
        self._build_orbital_trails()

    def _build_nebula(self, w, h):
        nebula_colors = [
            (18, 5, 30), (25, 8, 40), (15, 5, 25), (30, 10, 35),
            (20, 8, 28), (10, 5, 20), (28, 8, 38), (22, 6, 32),
        ]
        nebula_centers = [
            (0.3, 0.4), (0.7, 0.3), (0.5, 0.7), (0.2, 0.6),
            (0.8, 0.6), (0.4, 0.8), (0.6, 0.2), (0.3, 0.5),
        ]
        n_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        step = 4  # step 4 for speed – 4x faster than step 3
        for y in range(0, h, step):
            for x in range(0, w, step):
                br, bg, bb = 0, 0, 0
                total = 0
                for nc, (nx, ny) in zip(nebula_colors, nebula_centers):
                    dx2 = x / w - nx
                    dy2 = y / h - ny
                    dist = math.sqrt(dx2 * dx2 + dy2 * dy2) * 3.0
                    if dist < 1.5:
                        wt = (1.0 - dist / 1.5) * 0.4
                        br += nc[0] * wt
                        bg += nc[1] * wt
                        bb += nc[2] * wt
                        total += wt
                if total > 0:
                    r2 = int(min(255, br / total))
                    g2 = int(min(255, bg / total))
                    b2 = int(min(255, bb / total))
                    for dy in range(step):
                        for dx in range(step):
                            if x + dx < w and y + dy < h:
                                n_surf.set_at((x + dx, y + dy), (r2, g2, b2, 140))
        self._nebula_cache = n_surf

    def _build_aurora(self, w, h):
        """Pre-render two translucent aurora bands for the cosmic feel."""
        aurora = pygame.Surface((w, h), pygame.SRCALPHA)
        # Band 1 – purple-cyan sweep
        for y in range(0, h, 2):
            t = y / max(1, h - 1)
            # Gaussian-ish band shape centred at t=0.35 and t=0.65
            band1 = math.exp(-((t - 0.30) ** 2) / 0.008)
            band2 = math.exp(-((t - 0.65) ** 2) / 0.012)
            strength = max(band1 * 0.6, band2 * 0.35)
            if strength < 0.02:
                continue
            a = int(strength * 55)
            # Gradient hue from purple to teal across the band
            hue_mix = 0.5 + 0.5 * math.sin(t * 4.0)
            r = int(80 + 60 * (1 - hue_mix))
            g = int(40 + 100 * hue_mix)
            b = int(160 + 60 * hue_mix)
            pygame.draw.line(aurora, (r, g, b, a), (0, y), (w, y))
        self._aurora_cache = aurora

    def _build_mandala(self):
        """Pre-render a glowing sacred-geometry mandala at the centre."""
        if self._card_back_scaled is None:
            return
        # Compute radius from outermost ring
        max_r = _RING_DEF[-1][0] + 30
        size = max_r * 2 + 20
        surf = pygame.Surface((int(size), int(size)), pygame.SRCALPHA)
        mcx = mcy = int(size // 2)
        t = 0  # static at build time; animation done via alpha oscillation
        # Concentric energy rings
        for i, (radius, count) in enumerate(_RING_DEF):
            col = (140, 80, 220) if i % 2 == 0 else (212, 175, 55)
            a = int(12 + 8 * i)
            pygame.draw.circle(surf, (*col, a), (mcx, mcy), int(radius), 1)
        # Radiating spokes
        spoke_count = 22  # one per arcana
        for i in range(spoke_count):
            angle = i * 2 * math.pi / spoke_count
            ex = mcx + math.cos(angle) * max_r
            ey = mcy + math.sin(angle) * max_r
            a = 10 + 4 * (i % 3)
            pygame.draw.line(surf, (160, 120, 220, a), (mcx, mcy), (int(ex), int(ey)), 1)
        # Inner glow disc
        glow_r = _RING_DEF[0][0] - 10
        if glow_r > 5:
            pygame.draw.circle(surf, (100, 50, 180, 15), (mcx, mcy), int(glow_r))
        self._mandala_cache = surf

    def _build_vignette(self, sw, sh):
        """Dark-edge vignette for depth."""
        vig = pygame.Surface((sw, sh), pygame.SRCALPHA)
        max_dim = max(sw, sh)
        # Radial gradient from transparent centre to dark edges
        for r in range(int(max_dim * 0.7), int(max_dim * 0.52), -2):
            t = (r - max_dim * 0.52) / max(1, max_dim * 0.18)
            a = int(t * 120)
            pygame.draw.circle(vig, (3, 1, 8, a), (sw // 2, sh // 2), r)
        self._vignette_cache = vig

    def _build_border_energy(self):
        """Pre-compute the flowing energy line texture for panel borders."""
        # This is just a base – actual animation done per-frame with small overhead
        self._border_energy_cache = True  # flag: we've validated borders

    def _build_orbital_trails(self):
        """Pre-render faint orbital path circles for the card rings."""
        if self._card_back_scaled is None:
            return
        tw = self.tree_rect.width
        th = self.tree_rect.height
        surf = pygame.Surface((tw, th), pygame.SRCALPHA)
        mcx, mcy = tw // 2, th // 2
        for ri, (radius, count) in enumerate(_RING_DEF):
            col = (140, 80, 220) if ri % 2 == 0 else (212, 175, 55)
            # Dashed orbit effect: draw many small arcs
            segments = 60
            for s in range(segments):
                a1 = s * 2 * math.pi / segments
                a2 = a1 + math.pi / segments * 0.6
                alpha = int(10 + 4 * math.sin(s * 0.5))
                points = []
                for seg_t in range(6):
                    a = a1 + (a2 - a1) * seg_t / 5
                    points.append((mcx + math.cos(a) * radius, mcy + math.sin(a) * radius))
                if len(points) >= 2:
                    pygame.draw.lines(surf, (*col, alpha), False, points, 1)
        self._orbital_trail_cache = surf

    # ── Update loop ────────────────────────────────────────────────────

    def update(self, dt):
        dt = min(0.05, dt)
        self.animation_time += dt
        t = self.animation_time

        # Entrance
        if self._entrance_active:
            self._entrance_progress = min(1.0, self._entrance_progress + dt * 1.5)
            if self._entrance_progress >= 1.0:
                self._entrance_active = False

        # Floating particles
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

        # Ember particles
        for p in self._ember_particles:
            p["x"] += p["speed_x"] * dt * 60 + math.sin(t * 0.8 + p["phase"]) * 0.3
            p["y"] += p["speed_y"] * dt * 60
            if p["y"] < -350:
                p["y"] = 350
                p["x"] = random.uniform(-400, 400)

        # Rotations
        for p in self.pentagrams:
            p["rotation"] += p["rot_speed"] * dt
        for c in self.magic_circles:
            c["rotation"] += c["rot_speed"] * dt

        # Ring orbit offsets (pause when card selected)
        speed_mul = 0.0 if self._selected_card is not None else 1.0
        ring_speeds = [0.001, -0.002, 0.003, -0.004]
        for i, spd in enumerate(ring_speeds):
            self.card_ring_offsets[i] = (self.card_ring_offsets[i] + spd * speed_mul * dt * 60) % (math.pi * 2)

        # Revealed cards animation
        for rc in self.revealed_cards:
            rc["progress"] = min(1.0, rc["progress"] + dt * 2.0)

        # Selection overlay
        if self._selected_card is not None:
            self._sel_progress = min(1.0, self._sel_progress + dt * 3.0)
        else:
            self._sel_progress = max(0.0, self._sel_progress - dt * 4.0)

        # Burst particles
        for b in list(self._reveal_bursts):
            b["x"] += b["vx"] * dt
            b["y"] += b["vy"] * dt
            b["life"] -= dt
            if b["life"] <= 0:
                self._reveal_bursts.remove(b)

        # Rune spirits
        for s in list(self._rune_spirits):
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt
            s["rot"] += s["rot_speed"] * dt
            s["life"] -= dt
            if s["life"] <= 0:
                s["x"] = random.uniform(-600, 600)
                s["y"] = random.uniform(400, 600)
                s["life"] = s["max_life"]
                s["alpha"] = random.uniform(0.04, 0.12)

        # Hover sparkles
        mp = pygame.mouse.get_pos()
        hover_idx = -1
        for idx, (rect, rc) in enumerate(self._get_reveal_card_rects()):
            if rect.collidepoint(mp):
                hover_idx = idx
                if random.random() < 0.35:
                    self._hover_sparkles.append({
                        "x": rect.centerx + random.uniform(-rect.width // 2, rect.width // 2),
                        "y": rect.centery + random.uniform(-rect.height // 2, rect.height // 2),
                        "vx": random.uniform(-12, 12),
                        "vy": random.uniform(-18, -4),
                        "life": random.uniform(0.3, 0.7),
                        "max_life": 0.7,
                        "color": random.choice([(255, 215, 100), (200, 130, 255)]),
                        "size": random.uniform(1.5, 3.0),
                    })
                break
        self._hovered_card_idx = hover_idx
        for hs in list(self._hover_sparkles):
            hs["x"] += hs["vx"] * dt
            hs["y"] += hs["vy"] * dt
            hs["life"] -= dt
            if hs["life"] <= 0:
                self._hover_sparkles.remove(hs)

    # ── Event handling ─────────────────────────────────────────────────

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
                panel_rect = pygame.Rect(
                    self.tree_rect.x + (sw - panel_w) // 2,
                    self.tree_rect.y + (sh - panel_h) // 2,
                    panel_w, panel_h,
                )
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
                         int(card["front"].get_height() * 2.5)),
                    )
                    self._selected_card = rc
                    self._sel_card_front_large = large
                    self._sel_progress = 0.0
                    break

    # ── Drawing helpers ────────────────────────────────────────────────

    def _draw_gradient_rect(self, surface, rect, color_top, color_bottom, border_radius=0):
        key = (rect.width, rect.height, color_top, color_bottom, border_radius)
        cached = self._gradient_cache.get(key)
        if cached is not None:
            surface.blit(cached, rect)
            return
        h = rect.height
        temp = pygame.Surface((rect.width, h), pygame.SRCALPHA)
        for y in range(h):
            t = y / max(1, h - 1)
            r = int(color_top[0] + (color_bottom[0] - color_top[0]) * t)
            g = int(color_top[1] + (color_bottom[1] - color_top[1]) * t)
            b = int(color_top[2] + (color_bottom[2] - color_top[2]) * t)
            pygame.draw.line(temp, (r, g, b), (0, y), (rect.width, y))
        if border_radius > 0:
            mask = pygame.Surface((rect.width, h), pygame.SRCALPHA)
            mask.fill((0, 0, 0, 0))
            pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, rect.width, h), border_radius=border_radius)
            temp.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        self._gradient_cache[key] = temp
        surface.blit(temp, rect)

    def _draw_pentagram(self, surface, cx, cy, size, rotation, color, alpha,
                         glow_color=None, layer_count=2, ring_count=1,
                         has_inner_pentagon=True, orbit_particles=4,
                         orbit_speed=0.6, orbit_offset=0.0, orbit_radius_factor=1.3,
                         color_shift_speed=0.2):
        """Draw a richly layered mystical pentagram with glow, rings, orbiting
        particles, and colour-shifting energy lines."""
        t = self.animation_time
        a255 = int(alpha * 255)
        if a255 < 1:
            return

        if glow_color is None:
            glow_color = color

        # ── 1. Outer glow halo ─────────────────────────────────────────
        glow_r = int(size * 1.8)
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        # Soft radial glow that pulses
        pulse = (math.sin(t * 1.2 + rotation) + 1.0) * 0.5
        for ring in range(4, 0, -1):
            rr = int(glow_r * ring / 4)
            ga = int(a255 * 0.08 * (1.0 - ring / 5) * (0.6 + 0.4 * pulse))
            gc = glow_color
            pygame.draw.circle(glow_surf, (*gc, ga), (glow_r, glow_r), rr)
        surface.blit(glow_surf, (cx - glow_r, cy - glow_r))

        # ── 2. Outer decorative rings ──────────────────────────────────
        for ri in range(ring_count):
            ring_r = int(size * (1.35 + ri * 0.18))
            ring_a = int(a255 * (0.35 - ri * 0.08))
            # Dash effect: draw arcs with gaps
            segments = 20 + ri * 8
            for s in range(segments):
                a1 = rotation + s * 2 * math.pi / segments
                frac = s / segments
                seg_alpha = int(ring_a * (0.4 + 0.6 * math.sin(t * 0.8 + frac * 6 + ri)))
                if seg_alpha < 1:
                    continue
                a2 = a1 + math.pi / segments * 0.55
                pts = []
                for st in range(6):
                    ang = a1 + (a2 - a1) * st / 5
                    pts.append((cx + math.cos(ang) * ring_r, cy + math.sin(ang) * ring_r))
                if len(pts) >= 2:
                    # Colour shift along the ring
                    cs = (math.sin(t * color_shift_speed + frac * 4 + ri) + 1.0) * 0.5
                    rc = (
                        int(color[0] * (1 - cs) + glow_color[0] * cs),
                        int(color[1] * (1 - cs) + glow_color[1] * cs),
                        int(color[2] * (1 - cs) + glow_color[2] * cs),
                    )
                    pygame.draw.lines(surface, (*rc, seg_alpha), False, pts, max(1, int(1.2)))
            # Tiny rune dots on the ring
            if ring_r > 10:
                dot_count = 5 + ri * 3
                for d in range(dot_count):
                    da = rotation * (0.5 if ri % 2 else -0.5) + d * 2 * math.pi / dot_count
                    dx = cx + math.cos(da) * ring_r
                    dy = cy + math.sin(da) * ring_r
                    dot_pulse = (math.sin(t * 1.5 + d * 1.1 + ri) + 1.0) * 0.5
                    dot_a = int(ring_a * dot_pulse * 0.7)
                    if dot_a > 0:
                        pygame.draw.circle(surface, (*glow_color, dot_a), (int(dx), int(dy)), max(1, int(1.5)))

        # ── 3. Star points (outer) ────────────────────────────────────
        outer_pts = []
        for i in range(5):
            angle = rotation + i * 2 * math.pi / 5 - math.pi / 2
            outer_pts.append((cx + math.cos(angle) * size, cy + math.sin(angle) * size))

        # ── 4. Inner pentagon vertices ─────────────────────────────────
        inner_r = size * 0.38  # ratio for inner pentagon
        inner_pts = []
        for i in range(5):
            angle = rotation + i * 2 * math.pi / 5 - math.pi / 2 + math.pi / 5
            inner_pts.append((cx + math.cos(angle) * inner_r, cy + math.sin(angle) * inner_r))

        # ── 5. Multi-layered energy lines (star strokes) ───────────────
        for layer in range(layer_count):
            layer_offset = layer * 0.04 * size  # slight outward offset per layer
            layer_alpha_factor = 1.0 - layer * 0.2
            for i in range(5):
                p1 = outer_pts[i]
                p2 = outer_pts[(i + 2) % 5]
                # Colour shift per line segment
                seg_t = (math.sin(t * color_shift_speed * 1.5 + i * 1.3 + layer) + 1.0) * 0.5
                lc = (
                    int(color[0] * (1 - seg_t * 0.3) + glow_color[0] * seg_t * 0.3),
                    int(color[1] * (1 - seg_t * 0.3) + glow_color[1] * seg_t * 0.3),
                    int(color[2] * (1 - seg_t * 0.3) + glow_color[2] * seg_t * 0.3),
                )
                la = int(a255 * layer_alpha_factor * (0.6 + 0.4 * pulse))
                width = max(1, int(1.8 - layer * 0.4))
                pygame.draw.line(surface, (*lc, la), p1, p2, width)

            # Glow version (thicker, more transparent)
            glow_la = int(a255 * 0.12 * layer_alpha_factor)
            if glow_la > 0:
                for i in range(5):
                    p1 = outer_pts[i]
                    p2 = outer_pts[(i + 2) % 5]
                    pygame.draw.line(surface, (*glow_color, glow_la), p1, p2, max(2, int(3 - layer)))

        # ── 6. Inner pentagon fill ─────────────────────────────────────
        if has_inner_pentagon:
            inner_alpha = int(a255 * 0.12 * (0.5 + 0.5 * pulse))
            if inner_alpha > 0:
                pygame.draw.polygon(surface, (*glow_color, inner_alpha), inner_pts)
            # Inner pentagon outline
            inner_outline_a = int(a255 * 0.4 * (0.6 + 0.4 * pulse))
            if inner_outline_a > 0:
                pygame.draw.polygon(surface, (*color, inner_outline_a), inner_pts, width=max(1, int(1)))
                # Connect inner pentagon to outer star points
                for i in range(5):
                    conn_a = int(a255 * 0.15 * (0.5 + 0.5 * math.sin(t + i)))
                    if conn_a > 0:
                        pygame.draw.line(surface, (*color, conn_a), inner_pts[i], outer_pts[i], 1)

        # ── 7. Outer pentagon outline (connecting outer points) ────────
        pent_alpha = int(a255 * 0.25 * (0.5 + 0.5 * pulse))
        if pent_alpha > 0:
            pygame.draw.polygon(surface, (*color, pent_alpha), outer_pts, width=max(1, int(1)))

        # ── 8. Central glow disc ───────────────────────────────────────
        central_r = int(size * 0.25)
        if central_r > 2:
            for cr in range(central_r, 0, -2):
                ca = int(a255 * 0.06 * (cr / central_r) * (0.7 + 0.3 * pulse))
                pygame.draw.circle(surface, (*glow_color, ca), (cx, cy), cr)

        # ── 9. Orbiting energy particles ───────────────────────────────
        orbit_r = int(size * orbit_radius_factor)
        for pi_idx in range(orbit_particles):
            pa = orbit_offset + t * orbit_speed + pi_idx * 2 * math.pi / orbit_particles
            ppx = cx + math.cos(pa) * orbit_r
            ppy = cy + math.sin(pa) * orbit_r
            # Particle trail
            trail_len = 5
            for ti in range(trail_len):
                trail_a = orbit_r + ti * 2
                ta = pa - ti * 0.08
                tpx = cx + math.cos(ta) * trail_len * 2 + math.cos(pa) * orbit_r
                tpy = cy + math.sin(ta) * trail_len * 2 + math.sin(pa) * orbit_r
                tpa = int(a255 * 0.3 * (1.0 - ti / trail_len) * (0.5 + 0.5 * pulse))
                if tpa > 0:
                    pygame.draw.circle(surface, (*glow_color, tpa), (int(tpx), int(tpy)), max(1, int(2 - ti * 0.3)))
            # Main particle
            ppa = int(a255 * 0.5 * (0.6 + 0.4 * pulse))
            psize = max(1, int(2.5 + pulse))
            if ppa > 0:
                pygame.draw.circle(surface, (*color, ppa), (int(ppx), int(ppy)), psize)
                # Tiny glow around particle
                pg_a = int(a255 * 0.15)
                if pg_a > 0:
                    pygame.draw.circle(surface, (*glow_color, pg_a), (int(ppx), int(ppy)), psize + 2)

        # ── 10. Vertex sparkle nodes ───────────────────────────────────
        for i in range(5):
            sparkle_a = int(a255 * 0.4 * (0.5 + 0.5 * math.sin(t * 2.0 + i * 1.3)))
            if sparkle_a > 0:
                sx, sy = outer_pts[i]
                sparkle_sz = max(1, int(2.5 + pulse * 1.5))
                pygame.draw.circle(surface, (*glow_color, sparkle_a), (int(sx), int(sy)), sparkle_sz)
                # Cross sparkle
                cross_a = int(sparkle_a * 0.5)
                cross_len = sparkle_sz + 3
                pygame.draw.line(surface, (*glow_color, cross_a),
                                 (int(sx) - cross_len, int(sy)), (int(sx) + cross_len, int(sy)), 1)
                pygame.draw.line(surface, (*glow_color, cross_a),
                                 (int(sx), int(sy) - cross_len), (int(sx), int(sy) + cross_len), 1)

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

    # ── Major draw passes ──────────────────────────────────────────────

    def _draw_background(self, surface):
        """Cosmic background: nebula → aurora → deep glow → pentagrams →
        runes → magic circles → particles → embers → light rays →
        constellations → twinkling stars."""
        origin = pygame.Vector2(self.tree_rect.center)
        t = self.animation_time

        # Nebula base
        if self._nebula_cache is not None:
            surface.blit(self._nebula_cache, self.tree_rect.topleft)

        # Aurora overlay
        if self._aurora_cache is not None:
            # Animate alpha with a slow pulse
            aurora_a = int(120 + 40 * math.sin(t * 0.2))
            self._aurora_cache.set_alpha(aurora_a)
            surface.blit(self._aurora_cache, self.tree_rect.topleft)

        # Deep radial glow at centre
        for r in range(600, 0, -50):
            brightness = max(3, 12 - r // 80)
            pygame.draw.circle(surface, (brightness, brightness, brightness + 5), origin, r, 0)

        # Pentagrams
        for pent in self.pentagrams:
            px = origin.x + pent["x"]
            py = origin.y + pent["y"]
            if self.tree_rect.collidepoint(px, py):
                pulse = (math.sin(t * pent["pulse_speed"] + pent["pulse_offset"]) + 1.0) * 0.5
                a = pent["alpha"] * (0.5 + 0.5 * pulse)
                sz = pent["size"] * (0.9 + 0.1 * pulse)
                self._draw_pentagram(
                    surface, int(px), int(py), sz, pent["rotation"],
                    pent["color"], a,
                    glow_color=pent.get("glow_color"),
                    layer_count=pent.get("layer_count", 2),
                    ring_count=pent.get("ring_count", 1),
                    has_inner_pentagon=pent.get("has_inner_pentagon", True),
                    orbit_particles=pent.get("orbit_particles", 4),
                    orbit_speed=pent.get("orbit_speed", 0.6),
                    orbit_offset=pent.get("orbit_offset", 0.0),
                    orbit_radius_factor=pent.get("orbit_radius_factor", 1.3),
                    color_shift_speed=pent.get("color_shift_speed", 0.2),
                )

        # Runes
        for r_data in self.runes:
            rx = origin.x + r_data["x"]
            ry = origin.y + r_data["y"]
            if self.tree_rect.collidepoint(rx, ry):
                pulse = (math.sin(t * r_data["pulse_speed"] + r_data["pulse_offset"]) + 1.0) * 0.5
                a = r_data["alpha"] * (0.4 + 0.6 * pulse)
                if a > 0.02:
                    font = cfg.get_font(max(10, int(r_data["size"])))
                    glyph = font.render(r_data["symbol"], True, r_data["color"])
                    glyph.set_alpha(int(a * 255))
                    rect = glyph.get_rect(center=(int(rx), int(ry)))
                    surface.blit(glyph, rect)

        # Magic circles
        for c in self.magic_circles:
            cx = origin.x + c["x"]
            cy = origin.y + c["y"]
            if self.tree_rect.collidepoint(cx, cy):
                pulse = (math.sin(t * c["pulse_speed"] + c["pulse_offset"]) + 1.0) * 0.5
                a = c["alpha"] * (0.5 + 0.5 * pulse)
                rd = c["radius"] * (0.9 + 0.1 * pulse)
                self._draw_magic_circle(surface, int(cx), int(cy), rd, c["rotation"], c["color"], a, c["ring_count"])

        # Floating particles
        for p in self.particles:
            px = origin.x + p["x"]
            py = origin.y + p["y"]
            if self.tree_rect.collidepoint(px, py):
                pulse = (math.sin(t * p["pulse_speed"] + p["pulse_offset"]) + 1.0) * 0.5
                alpha = p["alpha"] * (0.4 + 0.6 * pulse)
                r, g, b = p["color"]
                pcolor = (int(r * alpha), int(g * alpha), int(b * alpha))
                sz = max(1, int(p["size"] * (0.8 + 0.4 * pulse)))
                if alpha > 0.05:
                    pygame.draw.circle(surface, pcolor, (int(px), int(py)), sz)

        # Ember particles (warm golden wisps)
        for p in self._ember_particles:
            px = origin.x + p["x"]
            py = origin.y + p["y"]
            if self.tree_rect.collidepoint(px, py):
                pulse = (math.sin(t * 1.5 + p["phase"]) + 1.0) * 0.5
                a = p["alpha"] * (0.3 + 0.7 * pulse)
                r, g, b = p["color"]
                pygame.draw.circle(surface, (int(r * a), int(g * a), int(b * a)), (int(px), int(py)), max(1, int(p["size"])))

        # Light rays from centre
        cx, cy = self.tree_rect.center
        for i in range(16):
            ang = (i / 16) * math.pi * 2 + t * 0.02
            a = max(0, int(3 + 5 * math.sin(t * 0.35 + i * 0.7)))
            ray_len = min(self.tree_rect.width, self.tree_rect.height) * 0.65
            ex = cx + math.cos(ang) * ray_len
            ey = cy + math.sin(ang) * ray_len
            pygame.draw.line(surface, (212, 175, 55, a), (cx, cy), (ex, ey), 1)

        # Constellation lines
        for (x1, y1, x2, y2, idx) in self._cached_constellations:
            twinkle = (math.sin(t * 0.5 + x1 * 0.01 + y1 * 0.01 + idx) + 1.0) * 0.5
            ca = int(4 + 8 * twinkle)
            if ca > 3:
                pygame.draw.line(surface, (140, 80, 220, ca), (x1, y1), (x2, y2), 1)

        # Twinkling stars
        for star in self._cached_stars:
            twinkle = (math.sin(t * star["speed"] + star["phase"] + star["seed_a"]) + 1.0) * 0.5
            a = int(15 + 80 * twinkle)
            size = 1 + twinkle * 0.8
            c = star["color"]
            sx, sy = star["x"], star["y"]
            # Pool tiny star surfaces by size bucket
            sb = int(size)
            pool_key = (c[0] >> 3, c[1] >> 3, c[2] >> 3, sb)
            star_surf = self._star_surface_pool.get(pool_key)
            if star_surf is None:
                star_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                self._star_surface_pool[pool_key] = star_surf
            # Draw onto a temp blit
            if self.tree_rect.collidepoint(sx, sy):
                pygame.draw.circle(star_surf, (*c, a), (3, 3), max(1, int(size)))
                surface.blit(star_surf, (sx - 3, sy - 3))
                # Bright glow for high-twinkle stars
                if twinkle > 0.88 and size > 1.3:
                    glow_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
                    ga = int(30 * twinkle)
                    pygame.draw.circle(glow_surf, (*c, ga), (8, 8), 8)
                    surface.blit(glow_surf, (sx - 8, sy - 8))

    def _draw_mandala(self, surface):
        """Draw the pre-rendered central mandala with pulsing alpha."""
        if self._mandala_cache is None:
            return
        t = self.animation_time
        alpha = int(80 + 30 * math.sin(t * 0.4))
        self._mandala_cache.set_alpha(alpha)
        mr = self._mandala_cache.get_rect(center=self.tree_rect.center)
        surface.blit(self._mandala_cache, mr)

    def _draw_orbital_trails(self, surface):
        """Draw pre-rendered orbital path dashes with pulsing alpha."""
        if self._orbital_trail_cache is None:
            return
        t = self.animation_time
        alpha = int(50 + 20 * math.sin(t * 0.3))
        self._orbital_trail_cache.set_alpha(alpha)
        surface.blit(self._orbital_trail_cache, self.tree_rect.topleft)

    def _draw_card_rings(self, surface):
        if self._card_back_scaled is None:
            return
        t = self.animation_time
        cx, cy = self.tree_rect.center
        ring_draw = [
            (120, 6, 0.80),
            (200, 5, 1.00),
            (280, 5, 1.15),
            (370, 6, 1.30),
        ]
        base_alpha = 140  # raised from 55 so face-down cards are clearly visible
        revealed_slots = {(rc["ring_idx"], rc["slot_idx"]) for rc in self.revealed_cards}

        # Ring glows
        for ri, (radius, count, scale_f) in enumerate(ring_draw):
            gp = (math.sin(t * 0.5 + ri * 1.2) + 1.0) * 0.5
            ga = int(12 + 20 * gp)
            glow_surf = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
            gcolor = (140, 80, 220, ga) if ri % 2 == 0 else (212, 175, 55, ga)
            pygame.draw.circle(glow_surf, gcolor, (radius + 10, radius + 10), radius + 10, width=max(1, int(2 - ri * 0.3)))
            surface.blit(glow_surf, (cx - radius - 10, cy - radius - 10))

        # Card slots
        for ri, (radius, count, scale_f) in enumerate(ring_draw):
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
                # Gentle pulse between 0.80 and 1.0 so cards breathe without disappearing
                fade = 0.88 + 0.12 * math.sin(t * 0.3 + ri + i)
                rotated.set_alpha(int(base_alpha * fade))
                rect = rotated.get_rect(center=(int(px), int(py)))
                surface.blit(rotated, rect)

    def _draw_revealed_cards(self, surface):
        if not self.revealed_cards:
            return
        t = self.animation_time
        cx, cy = self.tree_rect.center
        ring_draw = [
            (120, 6, 0.80), (200, 5, 1.00), (280, 5, 1.15), (370, 6, 1.30),
        ]
        hover_idx = self._hovered_card_idx
        for idx, rc in enumerate(self.revealed_cards):
            card = rc["card"]
            ease = 1.0 - (1.0 - rc["progress"]) ** 3
            if ease < 0.01:
                continue

            ri = rc["ring_idx"]
            radius, count, scale_f = ring_draw[ri]
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

            rot_angle = math.degrees(slot_angle) + 90 + math.sin(t * 0.3 + rc["float_offset"]) * 2

            scaled = pygame.transform.smoothscale(surf, (display_w, display_h))
            rotated = pygame.transform.rotate(scaled, rot_angle)
            rotated.set_alpha(int(230 * (0.3 + 0.7 * ease)))

            # Glow aura
            num = card["num"]
            glow_r = max(display_w, display_h)
            glow_surf = pygame.Surface((glow_r * 3, glow_r * 3), pygame.SRCALPHA)
            if num >= 16:
                gcolor = (200, 130, 255)
            elif num >= 11:
                gcolor = (255, 215, 100)
            elif num >= 6:
                gcolor = (140, 80, 220)
            else:
                gcolor = (160, 100, 255)
            glow_a = int(25 * ease * (0.6 + 0.4 * math.sin(t * 1.2 + rc["float_offset"])))
            pygame.draw.circle(glow_surf, (*gcolor, glow_a), (glow_r * 1.5, glow_r * 1.5), glow_r * 1.2)
            surface.blit(glow_surf, (px - glow_r * 1.5, py - glow_r * 1.5))

            rect = rotated.get_rect(center=(int(px), int(py)))
            surface.blit(rotated, rect)

            # Name label
            if ease > 0.85:
                name_font = cfg.get_font(max(10, int(13 * cfg.ui_scale())))
                label = f"#{card['num']} {card['name']}"
                ls = name_font.render(label, True, (212, 175, 55))
                ls.set_alpha(int(160 * ease))
                lr = ls.get_rect(midtop=(int(px), rect.bottom + 3))
                surface.blit(ls, lr)

            # Hover glow
            if idx == hover_idx:
                hg = pygame.Surface((display_w * 3, display_h * 3), pygame.SRCALPHA)
                ha = int(80 + 60 * math.sin(t * 3.0))
                hc = (255, 220, 140) if num >= 16 else (255, 215, 100)
                pygame.draw.circle(hg, (*hc, ha), (display_w * 1.5, display_h * 1.5), max(display_w, display_h))
                surface.blit(hg, (px - display_w * 1.5, py - display_h * 1.5))

    def _draw_rune_spirits(self, surface):
        t = self.animation_time
        cx, cy = self.tree_rect.center
        for s in self._rune_spirits:
            frac = s["life"] / s["max_life"]
            a = int(30 * frac * s["alpha"] * 200)
            if a < 2:
                continue
            sx = cx + s["x"]
            sy = cy + s["y"]
            sp = math.sin(t * 0.5 + s["phase"]) * 4
            font = cfg.get_font(int(s["size"]))
            rs = font.render(s["char"], True, (200, 160, 255))
            rs.set_alpha(a)
            rot = pygame.transform.rotate(rs, math.degrees(s["rot"]))
            rot.set_alpha(a)
            surface.blit(rot, (sx - rot.get_width() // 2 + sp, sy - rot.get_height() // 2))

    def _draw_hover_sparkles(self, surface):
        for hs in self._hover_sparkles:
            frac = hs["life"] / hs["max_life"]
            a = int(255 * frac)
            if a < 2:
                continue
            sz = max(1, int(hs["size"] * (0.3 + 0.7 * frac)))
            pygame.draw.circle(surface, (*hs["color"], a), (int(hs["x"]), int(hs["y"])), sz)

    def _draw_card_info(self, screen):
        if self._selected_card is None or self._sel_progress < 0.01:
            return
        ease = 1.0 - (1.0 - self._sel_progress) ** 3
        card = self._selected_card["card"]
        t = self.animation_time
        scale = cfg.ui_scale()
        num = card["num"]

        # Determine card rarity tier for colour theming
        if num >= 19:
            tier_color = (255, 215, 100)   # legendary gold
            tier_glow = (255, 180, 60)
        elif num >= 14:
            tier_color = (200, 130, 255)   # epic purple
            tier_glow = (160, 80, 240)
        elif num >= 8:
            tier_color = (100, 200, 220)   # rare cyan
            tier_glow = (60, 160, 200)
        else:
            tier_color = (180, 140, 255)   # common violet
            tier_glow = (140, 100, 220)

        sw, sh = self.tree_rect.size
        panel_w = int(sw * 0.85)
        panel_h = int(sh * 0.85)
        px = self.tree_rect.x + (sw - panel_w) // 2
        py = self.tree_rect.y + (sh - panel_h) // 2
        panel_rect = pygame.Rect(px, py, panel_w, panel_h)

        # ── Dimmed overlay with subtle colour tint ─────────────────────
        overlay = pygame.Surface((self.tree_rect.width, self.tree_rect.height), pygame.SRCALPHA)
        overlay.fill((5, 2, 12, int(200 * ease)))
        screen.blit(overlay, self.tree_rect.topleft)

        # ── Multi-layered ornate border ────────────────────────────────
        # Outermost halo
        outer_halo = panel_rect.inflate(14, 14)
        halo_a = int(60 * ease * (0.5 + 0.5 * math.sin(t * 0.8)))
        pygame.draw.rect(screen, (*tier_glow, halo_a), outer_halo, border_radius=24)
        # Gold accent border
        outer = panel_rect.inflate(6, 6)
        pygame.draw.rect(screen, (80, 50, 110, int(220 * ease)), outer, border_radius=22)
        gold_a = int(140 * ease * (0.6 + 0.4 * math.sin(t * 1.0)))
        pygame.draw.rect(screen, (*tier_color, gold_a), outer, width=max(1, int(1.5 * scale)), border_radius=22)

        # ── Panel body with richer gradient ────────────────────────────
        self._draw_gradient_rect(screen, panel_rect, (22, 10, 38), (10, 4, 20), border_radius=20)
        bw = max(2, int(2.5 * scale))
        border_pulse = int((160 + 60 * math.sin(t * 1.2)) * ease)
        pygame.draw.rect(screen, (*tier_color[:3], min(255, border_pulse)), panel_rect, bw, border_radius=20)
        # Inner decorative line
        inner = panel_rect.inflate(-8, -8)
        inner_a = int(80 * ease)
        pygame.draw.rect(screen, (*tier_glow, inner_a), inner, 1, border_radius=18)

        # ── Animated energy dots along panel border ────────────────────
        perim = 2 * (panel_rect.width + panel_rect.height) - 8
        dot_count = 20
        for di in range(dot_count):
            frac = (di / dot_count + t * 0.06) % 1.0
            dist = int(frac * perim)
            if dist < panel_rect.width:
                dx, dy = panel_rect.x + dist, panel_rect.y
            elif dist < panel_rect.width + panel_rect.height:
                dx, dy = panel_rect.right, panel_rect.y + (dist - panel_rect.width)
            elif dist < 2 * panel_rect.width + panel_rect.height:
                dx, dy = panel_rect.right - (dist - panel_rect.width - panel_rect.height), panel_rect.bottom
            else:
                dx, dy = panel_rect.x, panel_rect.bottom - (dist - 2 * panel_rect.width - panel_rect.height)
            dp = (math.sin(t * 2.5 + di * 1.4) + 1.0) * 0.5
            da = int(40 + 50 * dp)
            pygame.draw.circle(screen, (*tier_color, da), (dx, dy), max(1, int(1.5 * scale)))

        # ── Corner ornaments (elaborate) ───────────────────────────────
        orn_font = cfg.get_font(max(10, int(16 * scale)))
        orn_chars = ["ᛟ", "ᛞ", "ᛝ", "ᛚ"]
        corner_positions = [
            (panel_rect.x + 16, panel_rect.y + 16),
            (panel_rect.right - 16, panel_rect.y + 16),
            (panel_rect.x + 16, panel_rect.bottom - 16),
            (panel_rect.right - 16, panel_rect.bottom - 16),
        ]
        for idx, (gcx, gcy) in enumerate(corner_positions):
            op = (math.sin(t * 1.2 + idx * 1.5) + 1.0) * 0.5
            oa = int(90 + 130 * op)
            # Diamond ornament behind rune
            gem_sz = int(10 * scale)
            pygame.draw.polygon(screen, (*tier_color, int(oa * 0.3 * ease)),
                [(gcx, gcy - gem_sz), (gcx + gem_sz, gcy), (gcx, gcy + gem_sz), (gcx - gem_sz, gcy)])
            # Rune character
            o = orn_font.render(orn_chars[idx], True, tier_color)
            o.set_alpha(int(oa * ease))
            screen.blit(o, (gcx - o.get_width() // 2, gcy - o.get_height() // 2))

        # ── Arcane corner filigree lines ───────────────────────────────
        filig_len = int(30 * scale)
        for idx, (gcx, gcy) in enumerate(corner_positions):
            h_dir = 1 if gcx == panel_rect.x + 16 else -1
            v_dir = 1 if gcy == panel_rect.y + 16 else -1
            fa = int(60 * ease * (0.5 + 0.5 * math.sin(t + idx)))
            # Diagonal filigree
            end_x = gcx + h_dir * filig_len
            end_y = gcy + v_dir * filig_len
            mid_x = gcx + h_dir * filig_len * 0.5
            mid_y = gcy + v_dir * filig_len * 0.5
            pygame.draw.line(screen, (*tier_color, fa), (gcx, gcy), (end_x, gcy), 1)
            pygame.draw.line(screen, (*tier_color, fa), (gcx, gcy), (gcx, end_y), 1)
            pygame.draw.circle(screen, (*tier_color, int(fa * 0.6)), (int(end_x), int(end_y)), max(1, int(2 * scale)))

        margin = int(30 * scale)
        card_img = self._sel_card_front_large
        img_rect = None
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

            # ── Multi-layer card glow ──────────────────────────────────
            glow_w, glow_h = cw + 60, ch + 60
            glow = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
            # Outer diffuse glow
            ga1 = int(30 * ease * (0.5 + 0.5 * math.sin(t * 0.7)))
            pygame.draw.ellipse(glow, (*tier_glow, ga1), (0, 0, glow_w, glow_h))
            # Inner focused glow
            ga2 = int(50 * ease * (0.6 + 0.4 * math.sin(t * 1.1)))
            pygame.draw.ellipse(glow, (*tier_color, ga2), (15, 15, glow_w - 30, glow_h - 30))
            screen.blit(glow, (img_x - 30, img_y - 30))

            # ── Card frame (ornate gold border) ────────────────────────
            frame_inset = 3
            frame_rect = img_rect.inflate(6, 6)
            # Outer gold frame
            pygame.draw.rect(screen, (*tier_color, int(120 * ease)), frame_rect,
                             width=max(2, int(2.5 * scale)), border_radius=6)
            # Inner subtle line
            inner_frame = img_rect.inflate(-2, -2)
            pygame.draw.rect(screen, (255, 255, 255, int(30 * ease)), inner_frame, 1, border_radius=4)

            # ── Floating arcane particles around card ──────────────────
            card_cx, card_cy = img_rect.center
            for pi in range(6):
                pa = t * 0.4 + pi * math.pi * 2 / 6
                orbit_r_x = cw * 0.65
                orbit_r_y = ch * 0.65
                ppx = card_cx + math.cos(pa) * orbit_r_x
                ppy = card_cy + math.sin(pa) * orbit_r_y
                ppa = int(80 * ease * (0.4 + 0.6 * math.sin(t * 1.5 + pi * 2)))
                if ppa > 0:
                    pygame.draw.circle(screen, (*tier_color, ppa), (int(ppx), int(ppy)), max(1, int(2 * scale)))
                    # Tiny connecting line to card
                    line_a = int(ppa * 0.3)
                    pygame.draw.line(screen, (*tier_glow, line_a), (int(ppx), int(ppy)), img_rect.center, 1)

            screen.blit(card_img, img_rect)

            # ── Card number badge ──────────────────────────────────────
            badge_font = cfg.get_font(max(10, int(14 * scale)))
            badge_text = f"#{num}"
            badge_surf = badge_font.render(badge_text, True, tier_color)
            badge_w = badge_surf.get_width() + 12
            badge_h = badge_surf.get_height() + 6
            badge_rect = pygame.Rect(img_x + cw - badge_w - 4, img_y - badge_h // 2, badge_w, badge_h)
            pygame.draw.rect(screen, (15, 8, 25, int(200 * ease)), badge_rect, border_radius=8)
            pygame.draw.rect(screen, (*tier_color, int(120 * ease)), badge_rect, 1, border_radius=8)
            screen.blit(badge_surf, badge_rect.center)

        # ── Text column ────────────────────────────────────────────────
        text_x = px + margin
        if img_rect:
            text_x = img_rect.right + margin + int(10 * scale)
        text_w = panel_rect.right - text_x - margin

        # ── Card name with glow ────────────────────────────────────────
        sec_font = cfg.get_font(max(16, int(28 * scale)))
        name_text = card['name']
        # Glow layers for name
        for gi in range(3):
            name_glow = sec_font.render(name_text, True, tier_glow)
            name_glow.set_alpha(int(40 * ease * (0.5 + 0.5 * math.sin(t * 0.9 + gi))))
            screen.blit(name_glow, (text_x + gi * (1 if gi % 2 == 0 else -1),
                                     py + margin + 8 + gi * (1 if gi < 2 else -1)))
        name_surf = sec_font.render(name_text, True, (240, 225, 255))
        name_surf.set_alpha(int(255 * ease))
        name_y = py + margin + 8
        screen.blit(name_surf, (text_x, name_y))

        # ── Arcana number + ornamental subtitle ────────────────────────
        sub_font = cfg.get_font(max(11, int(15 * scale)))
        sub_text = f"— Arcana {num} of 22 —"
        sub_surf = sub_font.render(sub_text, True, tier_color)
        sub_surf.set_alpha(int(140 * ease))
        sub_y = name_y + name_surf.get_height() + 6
        screen.blit(sub_surf, (text_x, sub_y))

        # ── Animated ornamental divider ────────────────────────────────
        div_y = sub_y + sub_surf.get_height() + 10
        div_width = min(text_w, panel_w - margin * 2)
        # Centre diamond ornament
        div_cx = text_x + div_width // 2
        diamond_sz = int(4 * scale)
        diamond_pulse = (math.sin(t * 1.5) + 1.0) * 0.5
        d_a = int(150 * ease * (0.5 + 0.5 * diamond_pulse))
        pygame.draw.polygon(screen, (*tier_color, d_a), [
            (div_cx, div_y - diamond_sz), (div_cx + diamond_sz, div_y),
            (div_cx, div_y + diamond_sz), (div_cx - diamond_sz, div_y)])
        # Lines extending from diamond
        for side in (-1, 1):
            for i in range(div_width // 2 - diamond_sz):
                ix = div_cx + side * (diamond_sz + i + 1)
                if text_x <= ix < text_x + div_width:
                    wave = math.sin(t * 2.0 + i * 0.08) * 0.3 + 0.7
                    la = int((1.0 - i / max(1, div_width // 2)) * 120 * wave * ease)
                    pygame.draw.line(screen, (*tier_color, la), (ix, div_y), (ix, div_y + 1))

        # ── Description text ───────────────────────────────────────────
        eff = self.card_effects.get(num)
        if eff and eff["desc"]:
            body_font = cfg.get_font(max(12, int(18 * scale)))
            # Description background panel
            desc_panel_y = div_y + 16
            words = eff["desc"].split(" ")
            lines = []
            current_line = ""
            for w in words:
                test = f"{current_line} {w}".strip()
                if body_font.size(test)[0] <= text_w - 16:
                    current_line = test
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = w
            if current_line:
                lines.append(current_line)

            line_h = body_font.get_height() + 4
            desc_panel_h = len(lines) * line_h + 16
            desc_panel = pygame.Rect(text_x - 8, desc_panel_y - 6,
                                      min(text_w + 8, panel_w - margin * 2 + 8), desc_panel_h)
            # Subtle background for description
            pygame.draw.rect(screen, (15, 8, 25, int(80 * ease)), desc_panel, border_radius=8)
            pygame.draw.rect(screen, (*tier_glow, int(25 * ease)), desc_panel, 1, border_radius=8)

            desc_y = desc_panel_y + 4
            for li, line in enumerate(lines):
                desc_surf = body_font.render(line, True, (210, 200, 230))
                desc_surf.set_alpha(int(230 * ease))
                screen.blit(desc_surf, (text_x, desc_y))
                desc_y += line_h

            # ── Stats section with individual badges ───────────────────
            stats_y = desc_panel.bottom + 14
            stats_font = cfg.get_font(max(10, int(14 * scale)))
            stat_badge_h = int(22 * scale)

            stat_items = []
            if eff["mana"]:
                stat_items.append(("✧", f"+{eff['mana']} Max Mana", (100, 180, 255)))
            if eff["regen"]:
                stat_items.append(("↻", f"+{eff['regen']}/s Mana Regen", (120, 200, 255)))
            if eff["hp_regen"]:
                stat_items.append(("♥", f"+{eff['hp_regen']} HP/s", (100, 220, 120)))
            if eff["speed"]:
                stat_items.append(("»", f"+{int(eff['speed'] * 100)}% Move Speed", (200, 220, 100)))
            if eff["cdr"]:
                stat_items.append(("◈", f"+{int(eff['cdr'] * 100)}% Skill Haste", (180, 140, 255)))
            if eff["atk_spd"]:
                stat_items.append(("⚡", f"+{int(eff['atk_spd'] * 100)}% Atk Speed", (255, 200, 80)))
            if eff["dmg"]:
                stat_items.append(("⚔", f"+{eff['dmg']} Damage", (255, 100, 100)))
            if eff["stam"]:
                stat_items.append(("♦", f"+{eff['stam']}/s Stamina", (180, 220, 100)))

            if stat_items:
                badge_x = text_x
                badge_y = stats_y
                for icon, text, color in stat_items:
                    full_text = f" {icon} {text}"
                    tw_stat = stats_font.size(full_text)[0]
                    badge_w_stat = tw_stat + int(16 * scale)

                    # Check if badge fits on current line
                    if badge_x + badge_w_stat > panel_rect.right - margin:
                        badge_x = text_x
                        badge_y += stat_badge_h + int(4 * scale)

                    badge_rect = pygame.Rect(badge_x, badge_y, badge_w_stat, stat_badge_h)
                    # Badge background
                    badge_bg_a = int(100 * ease * (0.7 + 0.3 * math.sin(t * 0.8 + badge_x * 0.01)))
                    pygame.draw.rect(screen, (*color, int(badge_bg_a * 0.15)), badge_rect, border_radius=6)
                    pygame.draw.rect(screen, (*color, int(badge_bg_a * 0.4)), badge_rect, 1, border_radius=6)
                    # Badge text
                    badge_ts = stats_font.render(full_text, True, color)
                    badge_ts.set_alpha(int(220 * ease))
                    screen.blit(badge_ts, (badge_x + int(8 * scale),
                                           badge_y + (stat_badge_h - badge_ts.get_height()) // 2))
                    badge_x += badge_w_stat + int(6 * scale)

        # ── Close button (ornate) ──────────────────────────────────────
        close_r = pygame.Rect(panel_rect.right - 48, panel_rect.y + 12, 36, 36)
        # Animated ring around close button
        ring_a = int(120 * ease * (0.5 + 0.5 * math.sin(t * 2.0)))
        ring_r = close_r.width // 2 + 4
        pygame.draw.circle(screen, (*tier_color, ring_a), close_r.center, ring_r, max(1, int(1.5 * scale)))
        # Button body
        close_pulse = int(180 + 75 * (0.5 + 0.5 * math.sin(t * 1.5)))
        pygame.draw.circle(screen, (40, 20, 60, int(220 * ease)), close_r.center, close_r.width // 2)
        pygame.draw.circle(screen, (*tier_color, int(close_pulse * ease * 0.5)),
                           close_r.center, close_r.width // 2, 2)
        close_font = cfg.get_font(max(14, int(20 * scale)))
        cx_mark = close_font.render("✕", True, (200, 180, 220))
        cx_mark.set_alpha(int(200 * ease))
        screen.blit(cx_mark, cx_mark.get_rect(center=close_r.center))

    def _draw_sidebar(self, screen):
        r = self.sidebar_rect
        t = self.animation_time
        scale = cfg.ui_scale()

        # ── Panel background ───────────────────────────────────────────
        self._draw_gradient_rect(screen, r, (22, 10, 35), (10, 5, 20), border_radius=18)

        # Glass highlight
        highlight = r.inflate(-6, -6)
        hl_surf = pygame.Surface(highlight.size, pygame.SRCALPHA)
        hl_surf.fill((60, 40, 80, 12))
        screen.blit(hl_surf, highlight.topleft)

        # ── Animated energy border ─────────────────────────────────────
        pygame.draw.rect(screen, (80, 55, 110), r, 2, border_radius=18)
        inner_border = r.inflate(-4, -4)
        pygame.draw.rect(screen, (55, 40, 75), inner_border, 1, border_radius=16)

        # Flowing energy dots along border perimeter
        perimeter = 2 * (r.width + r.height) - 8  # approximate
        energy_dots = 24
        for i in range(energy_dots):
            frac = (i / energy_dots + t * 0.05) % 1.0
            dist = int(frac * perimeter)
            # Map perimeter distance to (x, y) on rect
            if dist < r.width:
                ex, ey = r.x + dist, r.y
            elif dist < r.width + r.height:
                ex, ey = r.right, r.y + (dist - r.width)
            elif dist < 2 * r.width + r.height:
                ex, ey = r.right - (dist - r.width - r.height), r.bottom
            else:
                ex, ey = r.x, r.bottom - (dist - 2 * r.width - r.height)
            pulse = (math.sin(t * 3.0 + i * 1.2) + 1.0) * 0.5
            ea = int(40 + 60 * pulse)
            pygame.draw.circle(screen, (160, 100, 240, ea), (ex, ey), max(1, int(2 * scale)))

        # Corner ornament lines
        orn_len = 20
        orn_color = (180, 130, 220)
        for corner in [(r.x, r.y), (r.right, r.y), (r.x, r.bottom), (r.right, r.bottom)]:
            cx, cy = corner
            hor_dir = 1 if corner[0] == r.x else -1
            ver_dir = 1 if corner[1] == r.y else -1
            pygame.draw.line(screen, orn_color, (cx, cy), (cx + hor_dir * orn_len, cy), 2)
            pygame.draw.line(screen, orn_color, (cx, cy), (cx, cy + ver_dir * orn_len), 2)

        # Corner gemstones
        gem_size = 6
        for gcx, gcy in [
            (r.x + 14, r.y + 14), (r.right - 14, r.y + 14),
            (r.x + 14, r.bottom - 14), (r.right - 14, r.bottom - 14),
        ]:
            gp = (math.sin(t * 1.5 + gcx * 0.1) + 1.0) * 0.5
            gcolor = (180, 100, 255)
            pts_top = [(gcx, gcy - gem_size), (gcx - gem_size, gcy), (gcx + gem_size, gcy)]
            pts_bot = [(gcx - gem_size, gcy), (gcx + gem_size, gcy), (gcx, gcy + gem_size)]
            pygame.draw.polygon(screen, tuple(min(255, c + 40) for c in gcolor), pts_top)
            pygame.draw.polygon(screen, tuple(max(0, c - 30) for c in gcolor), pts_bot)
            pygame.draw.circle(screen, (255, 215, 100), (gcx, gcy), max(1, gem_size // 3))

        # Corner rune ornaments
        rune_orn = cfg.get_font(max(10, int(16 * scale)))
        orn_chars = ["ᛟ", "ᛞ", "ᛝ", "ᛚ"]
        for idx, (gcx, gcy) in enumerate([
            (r.x + 14, r.y + 14), (r.right - 14, r.y + 14),
            (r.x + 14, r.bottom - 14), (r.right - 14, r.bottom - 14),
        ]):
            op = (math.sin(t * 1.2 + idx * 1.5) + 1.0) * 0.5
            oa = int(80 + 100 * op)
            o = rune_orn.render(orn_chars[idx], True, (212, 175, 55))
            o.set_alpha(oa)
            screen.blit(o, (gcx - o.get_width() // 2, gcy - o.get_height() // 2 - 2))

        # ── Title with cascading glow ──────────────────────────────────
        title_text = _("⟐ Mysterium Magnum ⟐")
        glow_a_pulse = int((math.sin(t * 1.5) + 1.0) * 60 + 60)
        # Multiple glow layers for depth
        for i in range(5):
            offset = i * (1 if i < 3 else -1)
            glow_surf = self.title_font.render(title_text, True, (140, 80, 220))
            glow_surf.set_alpha(glow_a_pulse // (i + 1))
            screen.blit(glow_surf, (r.x + 18 + offset, r.y + 18 + offset))
        title = self.title_font.render(title_text, True, (240, 220, 255))
        screen.blit(title, (r.x + 18, r.y + 18))

        # ── Title underline with flowing energy ────────────────────────
        div_y = r.y + 18 + title.get_height() + 12
        for i in range(r.width - 36):
            x = r.x + 18 + i
            # Wave pattern along the divider
            wave = math.sin(t * 2.0 + i * 0.08) * 0.3 + 0.7
            alpha = int((1.0 - abs(i / max(1, r.width - 36) - 0.5) * 2) * 120 * wave)
            pygame.draw.line(screen, (140, 80, 220, alpha), (x, div_y), (x, div_y + 1))

        # ── Hint text ──────────────────────────────────────────────────
        hint_text = _("Secrets await within the cards...")
        hint = self.small_font.render(hint_text, True, (150, 140, 175))
        screen.blit(hint, (r.x + 18, div_y + 10))

        # ── Narrative text ─────────────────────────────────────────────
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

        # ── Second divider ─────────────────────────────────────────────
        for i in range(r.width - 36):
            x = r.x + 18 + i
            alpha = int((1.0 - abs(i / max(1, r.width - 36) - 0.5) * 2) * 80)
            pygame.draw.line(screen, (70, 40, 100, alpha), (x, py), (x, py + 1))
        py += 12

        # ── Purple Stars panel ─────────────────────────────────────────
        stars = getattr(self.app, "purple_stars", 0)
        panel_w = r.width - 36
        panel_h = max(60, int(80 * scale))
        panel_rect = pygame.Rect(r.x + 18, py, panel_w, panel_h)
        pygame.draw.rect(screen, (18, 8, 32), panel_rect, border_radius=10)
        pygame.draw.rect(screen, (100, 60, 140), panel_rect, 2, border_radius=10)
        inner_panel = panel_rect.inflate(-4, -4)
        pygame.draw.rect(screen, (55, 35, 80), inner_panel, 1, border_radius=8)

        # Animated star icon
        star_cx = panel_rect.x + int(panel_rect.width * 0.25)
        star_cy = panel_rect.centery
        star_outer_r = max(8, int(18 * scale))
        star_inner_r = int(star_outer_r * 0.35)
        star_pulse = (math.sin(t * 2.0) + 1.0) * 0.5
        star_rot = t * 0.5

        star_pts = []
        for i in range(8):
            angle = star_rot + i * math.pi / 4 - math.pi / 2
            rd = star_outer_r if i % 2 == 0 else star_inner_r
            star_pts.append((star_cx + math.cos(angle) * rd, star_cy + math.sin(angle) * rd))

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
        pygame.draw.polygon(screen, (220, 180, 255), star_pts, width=max(1, int(1.5 * scale)))

        label_x = panel_rect.x + int(panel_rect.width * 0.45)
        label_y = panel_rect.y + int(10 * scale)
        label = self.small_font.render(_("Purple Stars"), True, (200, 180, 220))
        screen.blit(label, (label_x, label_y))

        count_color = (
            int(220 + 35 * star_pulse),
            int(140 + 60 * star_pulse),
            255,
        )
        count_text = str(stars)
        count_surf = self.section_font.render(count_text, True, count_color)
        count_shadow = self.section_font.render(count_text, True, (0, 0, 0))
        count_y = label_y + label.get_height() + 4
        screen.blit(count_shadow, (label_x + 2, count_y + 2))
        screen.blit(count_surf, (label_x, count_y))

        # Orbiting decorative dots around the star icon
        decor_r = max(2, int(3 * scale))
        for i in range(4):
            da = t * 1.2 + i * math.pi * 0.5
            orbit_r = star_outer_r + 10 + 3 * math.sin(t + i)
            dx = star_cx + math.cos(da) * orbit_r
            dy = star_cy + math.sin(da) * orbit_r
            pygame.draw.circle(screen, (180, 130, 255), (int(dx), int(dy)), decor_r)

    def _draw_vignette(self, screen):
        if self._vignette_cache is not None:
            screen.blit(self._vignette_cache, (0, 0))

    # ── Main draw entry point ──────────────────────────────────────────

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

        # ── Entrance animation ─────────────────────────────────────────
        ep = self._entrance_progress
        ee = 1.0 - (1.0 - ep) ** 2
        if self._entrance_active:
            tree_scale = 0.92 + 0.08 * ee
            tw = int(self.tree_rect.width * tree_scale)
            th = int(self.tree_rect.height * tree_scale)
            tree_draw = pygame.Rect(0, 0, tw, th)
            tree_draw.center = self.tree_rect.center
        else:
            tree_draw = self.tree_rect

        # ── Tree panel frame ───────────────────────────────────────────
        pygame.draw.rect(screen, (12, 8, 22), tree_draw, border_radius=18)
        pygame.draw.rect(screen, (70, 45, 100), tree_draw, 2, border_radius=18)
        inner_rect = tree_draw.inflate(-4, -4)
        pygame.draw.rect(screen, (45, 30, 65), inner_rect, 1, border_radius=16)

        # ── Animated border energy ─────────────────────────────────────
        tree_perimeter = 2 * (tree_draw.width + tree_draw.height) - 8
        border_dots = 30
        for i in range(border_dots):
            frac = (i / border_dots + self.animation_time * 0.04) % 1.0
            dist = int(frac * tree_perimeter)
            if dist < tree_draw.width:
                bx, by = tree_draw.x + dist, tree_draw.y
            elif dist < tree_draw.width + tree_draw.height:
                bx, by = tree_draw.right, tree_draw.y + (dist - tree_draw.width)
            elif dist < 2 * tree_draw.width + tree_draw.height:
                bx, by = tree_draw.right - (dist - tree_draw.width - tree_draw.height), tree_draw.bottom
            else:
                bx, by = tree_draw.x, tree_draw.bottom - (dist - 2 * tree_draw.width - tree_draw.height)
            bp = (math.sin(self.animation_time * 2.5 + i * 1.1) + 1.0) * 0.5
            ba = int(30 + 50 * bp)
            pygame.draw.circle(screen, (140, 90, 200, ba), (bx, by), max(1, int(1.5 * cfg.ui_scale())))

        # ── Corner ornaments ───────────────────────────────────────────
        orn_len = 16
        orn_color = (160, 100, 210)
        for cx, cy, hdx, hdy in [
            (tree_draw.x, tree_draw.y, 1, 1),
            (tree_draw.right, tree_draw.y, -1, 1),
            (tree_draw.x, tree_draw.bottom, 1, -1),
            (tree_draw.right, tree_draw.bottom, -1, -1),
        ]:
            pygame.draw.line(screen, orn_color, (cx, cy), (cx + hdx * orn_len, cy), 2)
            pygame.draw.line(screen, orn_color, (cx, cy), (cx, cy + hdy * orn_len), 2)
            gem_sz = 4
            gem_pts = [
                (cx + hdx * orn_len, cy + hdy * orn_len - gem_sz),
                (cx + hdx * orn_len - gem_sz, cy + hdy * orn_len),
                (cx + hdx * orn_len + gem_sz, cy + hdy * orn_len),
            ]
            pygame.draw.polygon(screen, (180, 100, 255), gem_pts)
            gem_pts2 = [
                (cx + hdx * orn_len - gem_sz, cy + hdy * orn_len),
                (cx + hdx * orn_len + gem_sz, cy + hdy * orn_len),
                (cx + hdx * orn_len, cy + hdy * orn_len + gem_sz),
            ]
            pygame.draw.polygon(screen, (120, 60, 200), gem_pts2)

        # ── Border runes ───────────────────────────────────────────────
        bf = cfg.get_font(max(6, int(10 * cfg.ui_scale())))
        border_rune_list = ["ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ", "ᚷ", "ᚹ", "ᚺ", "ᚾ", "ᛁ", "ᛃ"]
        for i, ch in enumerate(border_rune_list):
            frac = (i + 0.5) / len(border_rune_list)
            bp = (math.sin(self.animation_time * 1.5 + i * 0.9) + 1.0) * 0.5
            ba = int(30 + 50 * bp)
            rs = bf.render(ch, True, (160, 100, 210))
            rs.set_alpha(ba)
            if tree_draw.height > 100:
                ly = tree_draw.y + int(tree_draw.height * frac)
                screen.blit(rs, (tree_draw.x + 2, ly - rs.get_height() // 2))
                screen.blit(rs, (tree_draw.right - rs.get_width() - 2, ly - rs.get_height() // 2))

        # ── Clip to tree area ──────────────────────────────────────────
        old_clip = screen.get_clip()
        screen.set_clip(tree_draw)

        self._draw_background(screen)
        self._draw_orbital_trails(screen)
        self._draw_mandala(screen)
        self._draw_card_rings(screen)
        self._draw_revealed_cards(screen)
        self._draw_hover_sparkles(screen)
        self._draw_rune_spirits(screen)

        # Reveal burst particles
        for b in self._reveal_bursts:
            if self.tree_rect.collidepoint(b["x"], b["y"]):
                frac = b["life"] / b["max_life"]
                sz = max(1, int(b["size"] * frac))
                a = int(255 * frac)
                pygame.draw.circle(screen, (*b["color"], a), (int(b["x"]), int(b["y"])), sz)

        screen.set_clip(old_clip)

        # ── UI panels ──────────────────────────────────────────────────
        self._draw_sidebar(screen)
        self._draw_card_info(screen)
        self.reveal_button.draw(screen)
        self.exit_button.draw(screen)

        # ── Vignette (on top of everything) ───────────────────────────
        self._draw_vignette(screen)