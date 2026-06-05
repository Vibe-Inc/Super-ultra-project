"""
Arcane Quest Menu - A magical quest interface with gold and purple accents on black.
Optimized with cached elements, gold dust particles, ornate decorations, and majestic visuals.
"""

import math
import random
import time
import pygame
from typing import TYPE_CHECKING

from src.ui.menus.base import Menu
from src.ui.widgets import Button, Tooltip
import src.config as cfg
from src.core.logger import logger

try:
    _
except NameError:
    from gettext import gettext as _

if TYPE_CHECKING:
    from src.app import App


GOLD_BRIGHT   = (255, 215, 100)
GOLD          = (212, 175, 55)
GOLD_DEEP     = (160, 130, 40)
GOLD_DARK     = (110, 85, 25)
PURPLE_BRIGHT = (200, 130, 255)
PURPLE        = (140, 80, 220)
PURPLE_DEEP   = (90, 40, 160)
PURPLE_DARK   = (45, 20, 80)
BLACK_BG      = (10, 6, 18)
BLACK_PANEL   = (18, 10, 28, 235)
WHITE_SOFT    = (235, 225, 255)
MAGIC_CYAN    = (140, 220, 255)

MOB_DISPLAY_NAMES = {
    "brute": "Brute",
    "venomous": "Venomous",
    "arcanist": "Arcanist",
    "trickster": "Trickster",
    "bomber": "Bomber",
    "stalker": "Stalker",
    "skirmisher": "Skirmisher",
    "guardian": "Guardian",
}


class _Particle:
    __slots__ = (
        "x", "y", "vx", "vy", "life", "max_life",
        "color", "size", "shape", "trail",
    )

    def __init__(self, x, y, vx, vy, life, color, size, shape="dot", trail=None):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.life = float(life)
        self.max_life = float(life)
        self.color = color
        self.size = float(size)
        self.shape = shape
        self.trail = trail if trail is not None else []

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        if self.trail is not None:
            self.trail.append((self.x, self.y))
            if len(self.trail) > 8:
                self.trail.pop(0)

    @property
    def alive(self):
        return self.life > 0

    @property
    def alpha(self):
        return max(0.0, min(1.0, self.life / self.max_life))


class ArcaneQuest:
    QUEST_COOLDOWN_SECONDS = 120.0

    def __init__(self, quest_id, title, description, target_type, target_count, location_label, reward):
        self.id = quest_id
        self.title = title
        self.description = description
        self.target_type = target_type
        self.target_count = int(target_count)
        self.location_label = location_label
        self.reward = reward
        self.progress = 0
        self.completed = False
        self.claimed = False
        self.cooldown_until = 0.0

    @property
    def is_finished(self):
        return self.completed or self.progress >= self.target_count

    @property
    def on_cooldown(self):
        return self.claimed and self.cooldown_until > time.time()

    @property
    def cooldown_remaining(self):
        return max(0.0, self.cooldown_until - time.time())

    def progress_fraction(self):
        return min(1.0, self.progress / max(1, self.target_count))


class ArcaneQuestMenu(Menu):
    QUEST_COUNT = 6

    def __init__(self, app: "App"):
        super().__init__(app)
        scale = cfg.ui_scale()

        self.title_font   = cfg.get_font(max(20, int(48 * scale)))
        self.section_font = cfg.get_font(max(16, int(30 * scale)))
        self.body_font    = cfg.get_font(max(14, int(24 * scale)))
        self.small_font   = cfg.get_font(max(12, int(20 * scale)))
        self.reward_font  = cfg.get_font(max(14, int(26 * scale)))
        self.mono_font    = cfg.get_font(max(12, int(20 * scale)))

        btn_w = max(140, int(200 * scale))
        btn_h = max(36, int(48 * scale))
        self.back_button = Button(
            pygame.Rect(0, 0, btn_w, btn_h),
            _("BACK"),
            (45, 25, 65),
            (80, 50, 110),
            cfg.button_font,
            GOLD_BRIGHT,
            max(2, int(10 * scale)),
            on_click=self.close_menu,
        )

        self.claim_buttons: list[Button] = []
        self.buttons = [self.back_button]
        self.quests: list[ArcaneQuest] = []
        self._init_quests()

        self.anim_time = 0.0
        self.particles: list[_Particle] = []
        self.burst_particles: list[_Particle] = []
        self.star_particles: list[_Particle] = []
        self.gold_dust: list[_Particle] = []
        self.energy_arcs: list[dict] = []
        self._init_particles()
        self._init_energy_arcs()

        self.entrance_progress = 0.0
        self.entrance_active = True
        self.entrance_start = time.time()
        self.flicker_t = 0.0
        self._layout_size: tuple[int, int] | None = None

        self.claim_flash_alpha = 0.0
        self.claim_flash_time = 0.0

        self.panel_rect = pygame.Rect(0, 0, 0, 0)
        self.title_rect = pygame.Rect(0, 0, 0, 0)
        self.slot_rects: list[pygame.Rect] = []

        self.rerolls_remaining = 1
        self.reroll_cooldown_until = 0.0
        self.reroll_icon_rect = pygame.Rect(0, 0, 0, 0)
        self.reroll_tooltip: Tooltip | None = None

        # ── Cached elements ──────────────────────────────────────────
        self._cached_stars: list[dict] = []
        self._cached_constellations: list[tuple] = []
        self._cached_runes: list[dict] = []
        self._orb_cache: dict[tuple, pygame.Surface] = {}
        self._nebula_cache: pygame.Surface | None = None
        self._nebula_cache_key: tuple | None = None
        self._sigil_cache: pygame.Surface | None = None
        self._sigil_cache_size: tuple = (0, 0)

    # ── Data persistence ──────────────────────────────────────────────
    def get_quest_data(self) -> dict:
        return {
            "quests": [
                {
                    "id": q.id, "title": q.title, "description": q.description,
                    "target_type": q.target_type, "target_count": q.target_count,
                    "location_label": q.location_label, "reward": q.reward,
                    "progress": q.progress, "completed": q.completed,
                    "claimed": q.claimed,
                    "cooldown_remaining": max(0.0, q.cooldown_until - time.time()),
                }
                for q in self.quests
            ],
            "rerolls_remaining": self.rerolls_remaining,
            "reroll_cooldown_remaining": max(0.0, self.reroll_cooldown_until - time.time()),
        }

    def set_quest_data(self, data: dict | list[dict]):
        if not data:
            return
        now = time.time()
        self.quests = []
        if isinstance(data, list):
            for d in data:
                q = ArcaneQuest(
                    d.get("id", ""), d.get("title", ""), d.get("description", ""),
                    d.get("target_type", "mobs"), d.get("target_count", 5),
                    d.get("location_label", ""), d.get("reward", {}),
                )
                q.progress = d.get("progress", 0)
                q.completed = d.get("completed", False)
                q.claimed = d.get("claimed", False)
                q.cooldown_until = now + d.get("cooldown_remaining", 0.0)
                self.quests.append(q)
            self.rerolls_remaining = 1
            self.reroll_cooldown_until = 0.0
        else:
            for d in data.get("quests", []):
                q = ArcaneQuest(
                    d.get("id", ""), d.get("title", ""), d.get("description", ""),
                    d.get("target_type", "mobs"), d.get("target_count", 5),
                    d.get("location_label", ""), d.get("reward", {}),
                )
                q.progress = d.get("progress", 0)
                q.completed = d.get("completed", False)
                q.claimed = d.get("claimed", False)
                q.cooldown_until = now + d.get("cooldown_remaining", 0.0)
                self.quests.append(q)
            self.rerolls_remaining = data.get("rerolls_remaining", 1)
            self.reroll_cooldown_until = now + data.get("reroll_cooldown_remaining", 0.0)
        self._layout_size = None

    def reset_quests(self):
        self.rerolls_remaining = 1
        self.reroll_cooldown_until = 0.0
        self.reroll_tooltip = None
        self._init_quests()
        self._layout_size = None

    def _init_quests(self):
        self.quests = []
        gs = self.app.manager.states.get("gameplay") if hasattr(self.app, "manager") else None
        mob_names = list(gs.enemy_profile_names) if gs and hasattr(gs, "enemy_profile_names") else ["brute", "venomous", "arcanist"]
        random.shuffle(mob_names)
        rng = random.Random()
        base_xp = [80, 120, 180, 250, 350, 500]
        base_gold = [20, 35, 55, 80, 120, 180]
        for i in range(self.QUEST_COUNT):
            mob_key = mob_names[i % len(mob_names)]
            kill_count = rng.randint(3, 8)
            mob_name = MOB_DISPLAY_NAMES.get(mob_key, mob_key.capitalize())
            idx = rng.randint(0, len(base_xp) - 1)
            reward = {"xp": base_xp[idx], "gold": base_gold[idx]}
            if rng.random() < 0.35:
                reward["item"] = rng.choice(["Arcane Token", "Crystal Shard", "Storm Core", "Abyss Essence"])
            self.quests.append(ArcaneQuest(
                f"q_{i}_{mob_key}",
                _("Hunt {n}").format(n=mob_name),
                _("Kill {c}x {n}").format(c=kill_count, n=mob_name),
                mob_key, kill_count, "", reward,
            ))
        self.claim_buttons.clear()

    def _process_quest_cooldowns(self):
        for i, q in enumerate(self.quests):
            if q.claimed and q.cooldown_until <= time.time():
                self._spawn_replacement_quest(i)

    def _spawn_replacement_quest(self, idx: int):
        gs = self.app.manager.states.get("gameplay") if hasattr(self.app, "manager") else None
        mob_names = list(gs.enemy_profile_names) if gs and hasattr(gs, "enemy_profile_names") else ["brute", "venomous", "arcanist"]
        rng = random.Random()
        mob_key = rng.choice(mob_names)
        kill_count = rng.randint(3, 8)
        mob_name = MOB_DISPLAY_NAMES.get(mob_key, mob_key.capitalize())
        base_xp = [80, 120, 180, 250, 350, 500]
        base_gold = [20, 35, 55, 80, 120, 180]
        idx2 = rng.randint(0, len(base_xp) - 1)
        reward = {"xp": base_xp[idx2], "gold": base_gold[idx2]}
        if rng.random() < 0.35:
            reward["item"] = rng.choice(["Arcane Token", "Crystal Shard", "Storm Core", "Abyss Essence"])
        q = self.quests[idx]
        q.id = f"n_{int(time.time())}_{mob_key}_{rng.randint(0, 999)}"
        q.title = _("Hunt {n}").format(n=mob_name)
        q.description = _("Kill {c}x {n}").format(c=kill_count, n=mob_name)
        q.target_type = mob_key
        q.target_count = kill_count
        q.location_label = ""
        q.reward = reward
        q.progress = 0
        q.completed = False
        q.claimed = False
        q.cooldown_until = 0.0
        base_cx = self.panel_rect.centerx if self.panel_rect.width > 0 else 400
        base_cy = self.panel_rect.centery if self.panel_rect.height > 0 else 300
        slot_rect = self.slot_rects[idx] if idx < len(self.slot_rects) else None
        if slot_rect:
            self._spawn_burst(slot_rect.centerx, slot_rect.centery, GOLD_BRIGHT, n=25)
            self._spawn_burst(slot_rect.centerx + 20, slot_rect.centery, PURPLE_BRIGHT, n=25)
        else:
            self._spawn_burst(base_cx, base_cy, GOLD_BRIGHT, n=25)
        self._rebuild_claim_buttons()

    def _reroll_quests(self):
        if self.rerolls_remaining <= 0:
            return
        if time.time() < self.reroll_cooldown_until:
            return
        unclaimed = [q for q in self.quests if not q.claimed]
        if not unclaimed:
            return
        gs = self.app.manager.states.get("gameplay") if hasattr(self.app, "manager") else None
        mob_names = list(gs.enemy_profile_names) if gs and hasattr(gs, "enemy_profile_names") else ["brute", "venomous", "arcanist"]
        rng = random.Random()
        base_xp = [80, 120, 180, 250, 350, 500]
        base_gold = [20, 35, 55, 80, 120, 180]
        for q in unclaimed:
            mob_key = rng.choice(mob_names)
            kill_count = rng.randint(3, 8)
            mob_name = MOB_DISPLAY_NAMES.get(mob_key, mob_key.capitalize())
            idx = rng.randint(0, len(base_xp) - 1)
            reward = {"xp": base_xp[idx], "gold": base_gold[idx]}
            if rng.random() < 0.35:
                reward["item"] = rng.choice(["Arcane Token", "Crystal Shard", "Storm Core", "Abyss Essence"])
            q.id = f"r_{int(time.time())}_{mob_key}_{rng.randint(0, 999)}"
            q.title = _("Hunt {n}").format(n=mob_name)
            q.description = _("Kill {c}x {n}").format(c=kill_count, n=mob_name)
            q.target_type = mob_key
            q.target_count = kill_count
            q.location_label = ""
            q.reward = reward
            q.progress = 0
            q.completed = False
        self.rerolls_remaining -= 1
        self.reroll_cooldown_until = time.time() + 600.0
        self._rebuild_claim_buttons()
        self._layout_size = None
        cx = self.panel_rect.centerx if self.panel_rect.width > 0 else 400
        cy = self.panel_rect.centery if self.panel_rect.height > 0 else 300
        self._spawn_burst(cx, cy, MAGIC_CYAN, n=40)

    # ── Particle initialization ───────────────────────────────────────
    def _init_particles(self):
        rng = random.Random(1337)
        self.particles.clear()
        self.star_particles.clear()
        self.gold_dust.clear()
        self.ambient_orbs = []

        for _ in range(150):
            x = rng.uniform(0, 1000)
            y = rng.uniform(0, 1000)
            vx = rng.uniform(-8, 8)
            vy = rng.uniform(-15, -3)
            life = rng.uniform(3.0, 7.0)
            color = rng.choice(
                [GOLD_BRIGHT, GOLD, PURPLE_BRIGHT, PURPLE, (180, 150, 255), (255, 230, 180)]
            )
            size = rng.uniform(1.0, 3.0)
            self.particles.append(
                _Particle(x, y, vx, vy, life, color, size, shape="dot")
            )

        for _ in range(60):
            x = rng.uniform(0, 1000)
            y = rng.uniform(0, 1000)
            vx = rng.uniform(-4, 4)
            vy = rng.uniform(-10, -2)
            life = rng.uniform(2.0, 5.0)
            color = rng.choice([GOLD_BRIGHT, PURPLE_BRIGHT, MAGIC_CYAN])
            size = rng.uniform(2.0, 5.0)
            self.star_particles.append(
                _Particle(x, y, vx, vy, life, color, size, shape="star")
            )

        # Gold dust particles that flow around panel edges
        for _ in range(40):
            x = rng.uniform(0, 1000)
            y = rng.uniform(0, 1000)
            ang = rng.uniform(0, math.pi * 2)
            speed = rng.uniform(4, 18)
            life = rng.uniform(4.0, 12.0)
            color = rng.choice([GOLD_BRIGHT, GOLD, (255, 230, 160)])
            size = rng.uniform(0.5, 2.0)
            self.gold_dust.append(
                _Particle(x, y, math.cos(ang) * speed, math.sin(ang) * speed, life, color, size, shape="dust")
            )

        for _ in range(8):
            self.ambient_orbs.append({
                "x": rng.uniform(0, 1000),
                "y": rng.uniform(0, 1000),
                "radius": rng.uniform(100, 280),
                "vx": rng.uniform(-3, 3),
                "vy": rng.uniform(-2, 2),
                "color": rng.choice([PURPLE_DEEP, PURPLE, GOLD_DARK, (30, 15, 50), (50, 20, 80)]),
                "alpha": rng.uniform(0.04, 0.10),
                "pulse_speed": rng.uniform(0.3, 0.8),
                "pulse_offset": rng.uniform(0, math.pi * 2),
            })

    def _init_energy_arcs(self):
        self.energy_arcs = []
        rng = random.Random(42)
        for i in range(12):
            angle = rng.uniform(0, math.pi * 2)
            radius = rng.uniform(100, min(600, 400))
            length = rng.uniform(80, 250)
            speed = rng.uniform(0.3, 1.0)
            color = rng.choice([GOLD_BRIGHT, PURPLE_BRIGHT, MAGIC_CYAN, GOLD])
            self.energy_arcs.append({
                "angle": angle, "radius": radius, "length": length, "speed": speed,
                "color": color, "alpha": rng.uniform(0.05, 0.12),
                "phase": rng.uniform(0, math.pi * 2), "width": rng.uniform(1.0, 2.5),
            })

    # ── Cached element generation ────────────────────────────────────
    def _build_cache(self, sw: int, sh: int):
        rng = random.Random(7)
        star_colors = [GOLD_BRIGHT, GOLD, PURPLE_BRIGHT, PURPLE, MAGIC_CYAN, (255, 200, 180), (200, 180, 255)]
        self._cached_stars = []
        for _ in range(300):
            sx = rng.randint(0, sw - 1)
            sy = rng.randint(0, sh - 1)
            ci = rng.randint(0, len(star_colors) - 1)
            phase = rng.uniform(0, math.pi * 2)
            speed = 1.5 + rng.random() * 2.0
            self._cached_stars.append({
                "x": sx, "y": sy, "color": star_colors[ci],
                "phase": phase, "speed": speed,
                "seed_a": sx * 0.08 + sy * 0.06,
            })

        rng2 = random.Random(13)
        const_points = [(rng2.randint(0, sw - 1), rng2.randint(0, sh - 1)) for _ in range(40)]
        self._cached_constellations = []
        for i, (x1, y1) in enumerate(const_points):
            for j, (x2, y2) in enumerate(const_points):
                if j <= i:
                    continue
                dx, dy = x2 - x1, y2 - y1
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < 90 and dist > 20:
                    self._cached_constellations.append((x1, y1, x2, y2, i))

        scale_runes = cfg.ui_scale()
        rune_positions = [
            (0.06, 0.08), (0.94, 0.08), (0.06, 0.92), (0.94, 0.92),
            (0.02, 0.25), (0.98, 0.25), (0.02, 0.75), (0.98, 0.75),
            (0.10, 0.02), (0.90, 0.02), (0.10, 0.98), (0.90, 0.98),
            (0.50, 0.02), (0.50, 0.98), (0.02, 0.50), (0.98, 0.50),
        ]
        rune_chars = ["ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ", "ᚷ", "ᚹ",
                      "ᚺ", "ᚾ", "ᛁ", "ᛃ", "ᛇ", "ᛈ", "ᛉ", "ᛊ"]
        rune_font = cfg.get_font(max(16, int(32 * scale_runes)))
        self._cached_runes = []
        for i, (rx, ry) in enumerate(rune_positions):
            px, py = int(sw * rx), int(sh * ry)
            r_color = GOLD if i % 3 == 0 else (PURPLE_BRIGHT if i % 3 == 1 else MAGIC_CYAN)
            surf = rune_font.render(rune_chars[i], True, r_color)
            self._cached_runes.append({"x": px, "y": py, "surf": surf, "idx": i})

    def _get_orb_surface(self, radius: int, color: tuple, base_alpha: int) -> pygame.Surface:
        key = (radius, color, base_alpha)
        if key in self._orb_cache:
            return self._orb_cache[key]
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for ri in range(radius, 0, -2):
            ta = base_alpha * (1.0 - ri / radius)
            pygame.draw.circle(surf, (color[0], color[1], color[2], ta), (radius, radius), ri)
        self._orb_cache[key] = surf
        return surf

    def _get_nebula(self, sw: int, sh: int) -> pygame.Surface:
        key = (sw, sh)
        if self._nebula_cache_key == key and self._nebula_cache is not None:
            return self._nebula_cache
        nebula = pygame.Surface((sw, sh), pygame.SRCALPHA)
        nebula_colors = [
            (18, 8, 38), (24, 10, 42), (16, 12, 36), (20, 14, 32),
            (14, 6, 28), (26, 12, 34), (32, 16, 28), (12, 14, 30),
            (36, 18, 44), (22, 8, 32), (28, 14, 38), (10, 10, 28),
        ]
        nebula_centers = [
            (0.3, 0.4), (0.7, 0.3), (0.5, 0.7), (0.2, 0.6),
            (0.8, 0.6), (0.4, 0.8), (0.6, 0.2), (0.3, 0.5),
            (0.15, 0.25), (0.85, 0.75), (0.45, 0.15), (0.55, 0.85),
        ]
        for y in range(0, sh, 4):
            for x in range(0, sw, 4):
                blend_r, blend_g, blend_b = 0, 0, 0
                total = 0
                for (nc, (nx, ny)) in zip(nebula_colors, nebula_centers):
                    dx = x / sw - nx
                    dy = y / sh - ny
                    dist = math.sqrt(dx*dx + dy*dy) * 3.2
                    if dist < 1.5:
                        w = (1.0 - dist / 1.5) * 0.35
                        blend_r += nc[0] * w
                        blend_g += nc[1] * w
                        blend_b += nc[2] * w
                        total += w
                if total > 0:
                    r2 = int(min(255, blend_r / total))
                    g2 = int(min(255, blend_g / total))
                    b2 = int(min(255, blend_b / total))
                    nebula.set_at((x, y), (r2, g2, b2, 180))
        self._nebula_cache = nebula
        self._nebula_cache_key = key
        return nebula

    def _get_sigil_surface(self, w: int, h: int) -> pygame.Surface:
        if self._sigil_cache is not None and self._sigil_cache_size == (w, h):
            return self._sigil_cache
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        r = min(w, h) // 2 - 10
        if r > 6:
            # Outer dashed circle
            segments = 20
            for i in range(segments):
                if i % 2 == 0:
                    ang1 = (i / segments) * math.pi * 2
                    ang2 = ((i + 1) / segments) * math.pi * 2
                    x1 = cx + math.cos(ang1) * r
                    y1 = cy + math.sin(ang1) * r
                    x2 = cx + math.cos(ang2) * r
                    y2 = cy + math.sin(ang2) * r
                    pygame.draw.line(surf, (*GOLD_DEEP, 60), (x1, y1), (x2, y2), 1)
            # Inner 4-pointed star
            inner_r = r * 0.6
            pts = []
            for i in range(4):
                ang = (i / 4) * math.pi * 2 - math.pi / 4
                pts.append((cx + math.cos(ang) * inner_r, cy + math.sin(ang) * inner_r))
                ang2 = ang + math.pi / 4
                pts.append((cx + math.cos(ang2) * inner_r * 0.4, cy + math.sin(ang2) * inner_r * 0.4))
            if len(pts) >= 3:
                pygame.draw.polygon(surf, (*PURPLE, 50), pts)
                pygame.draw.polygon(surf, (*GOLD_DEEP, 70), pts, width=1)
            # Center dot
            pygame.draw.circle(surf, (*GOLD, 80), (cx, cy), max(2, r // 8))
        self._sigil_cache = surf
        self._sigil_cache_size = (w, h)
        return surf

    # ── Layout ────────────────────────────────────────────────────────
    def _ensure_layout(self, screen_width: int, screen_height: int):
        if self._layout_size != (screen_width, screen_height):
            self._layout_size = (screen_width, screen_height)
            self._recalc_layout(screen_width, screen_height)
            self._build_cache(screen_width, screen_height)

    def _recalc_layout(self, screen_width: int, screen_height: int):
        scale = cfg.ui_scale()

        panel_w = min(960, max(680, int(780 * scale)))
        panel_h = min(700, max(560, int(620 * scale)))
        panel_x = (screen_width - panel_w) // 2
        panel_y = (screen_height - panel_h) // 2
        self.panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        self.title_rect = pygame.Rect(
            self.panel_rect.x,
            self.panel_rect.y + int(16 * scale),
            self.panel_rect.width,
            int(56 * scale),
        )

        slot_pad = int(24 * scale)
        slot_gap = int(6 * scale)
        slot_count = len(self.quests)
        title_bottom = self.title_rect.bottom + int(8 * scale)
        btn_area_height = max(44, int(54 * scale))
        available = (panel_h - (title_bottom - panel_y) - btn_area_height - int(20 * scale))
        slot_h = max(68, int(available / max(1, slot_count)) - slot_gap)

        self.slot_rects = []
        for i in range(slot_count):
            sy = title_bottom + i * (slot_h + slot_gap)
            sr = pygame.Rect(
                self.panel_rect.x + slot_pad,
                sy,
                self.panel_rect.width - slot_pad * 2,
                slot_h,
            )
            self.slot_rects.append(sr)

        back_h = self.back_button.rect.height
        bottom_y = self.panel_rect.bottom - back_h - int(14 * scale)
        self.back_button.rect.topleft = (
            self.panel_rect.x + int(14 * scale),
            bottom_y,
        )

        self._rebuild_claim_buttons()

        for btn in self.buttons:
            try:
                btn._update_text_surface()
            except Exception:
                pass

    # ── Lifecycle ────────────────────────────────────────────────────
    def on_enter(self):
        self.entrance_active = True
        self.entrance_start = time.time()
        self.entrance_progress = 0.0
        self.claim_flash_alpha = 0.0
        self._init_particles()
        self._init_energy_arcs()
        self._layout_size = None
        self._orb_cache.clear()
        sw, sh = (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        try:
            sw, sh = self.app.screen.get_size()
        except Exception:
            pass
        self._ensure_layout(sw, sh)
        px, py = self.panel_rect.x, self.panel_rect.y
        pw, ph = self.panel_rect.width, self.panel_rect.height
        for _ in range(30):
            sx = px + random.uniform(0, pw)
            sy = py + random.uniform(0, ph)
            ang = random.uniform(0, math.pi * 2)
            speed = random.uniform(20, 80)
            life = random.uniform(1.2, 2.5)
            sz = random.uniform(1.5, 4.0)
            color = random.choice([GOLD_BRIGHT, PURPLE_BRIGHT, MAGIC_CYAN])
            self.burst_particles.append(
                _Particle(sx, sy, math.cos(ang) * speed, math.sin(ang) * speed, life, color, sz)
            )

    def close_menu(self):
        self.app.manager.set_state("gameplay")

    def claim_reward(self, quest_idx: int):
        if quest_idx < 0 or quest_idx >= len(self.quests):
            return
        q = self.quests[quest_idx]
        if not q.is_finished or q.claimed:
            return
        q.claimed = True
        q.completed = True
        q.progress = q.target_count
        self.claim_flash_alpha = 1.0
        self.claim_flash_time = 0.0
        reward = q.reward
        try:
            if "gold" in reward and hasattr(self.app, "money"):
                self.app.money += int(reward["gold"])
        except Exception:
            pass
        try:
            if "xp" in reward and hasattr(self.app, "character"):
                gs = self.app.manager.states.get("gameplay")
                char = getattr(gs, "character", None) if gs else None
                if char and hasattr(char, "xp"):
                    char.xp += int(reward["xp"])
        except Exception:
            pass
        self.app.purple_stars = getattr(self.app, "purple_stars", 0) + 1
        logger.info(f"Player earned a Purple Star! Total: {self.app.purple_stars}")
        try:
            btn_rect = self.claim_buttons[quest_idx].rect if quest_idx < len(self.claim_buttons) else self.panel_rect
            self._spawn_burst(btn_rect.centerx, btn_rect.centery, GOLD_BRIGHT, n=50)
            self._spawn_burst(btn_rect.centerx + 30, btn_rect.centery, PURPLE_BRIGHT, n=50)
        except Exception:
            pass
        self._rebuild_claim_buttons()
        q.cooldown_until = time.time() + ArcaneQuest.QUEST_COOLDOWN_SECONDS

    def _rebuild_claim_buttons(self):
        scale = cfg.ui_scale()
        self.claim_buttons = []
        for i, q in enumerate(self.quests):
            if i >= len(self.slot_rects):
                break
            sr = self.slot_rects[i]
            cw = max(80, int(120 * scale))
            ch = max(28, int(36 * scale))
            cx = sr.right - cw - int(8 * scale)
            cy = sr.bottom - ch - int(6 * scale)
            text = _("CLAIM") if not q.claimed else _("DONE")
            btn = Button(
                pygame.Rect(cx, cy, cw, ch),
                text,
                (70, 30, 100) if not q.claimed else (50, 50, 55),
                (100, 50, 140) if not q.claimed else (70, 70, 75),
                cfg.button_font,
                GOLD_BRIGHT if not q.claimed else (140, 140, 150),
                max(2, int(6 * scale)),
                on_click=lambda idx=i: self.claim_reward(idx),
            )
            self.claim_buttons.append(btn)

    def _spawn_burst(self, x, y, color, n=40):
        for _ in range(n):
            ang = random.uniform(0, math.pi * 2)
            speed = random.uniform(60, 280)
            life = random.uniform(0.4, 1.2)
            sz = random.uniform(1.5, 3.5)
            self.burst_particles.append(
                _Particle(x, y, math.cos(ang) * speed, math.sin(ang) * speed, life, color, sz)
            )

    def _bump_page_progress(self, amount=1):
        for q in self.quests:
            if q.claimed:
                continue
            q.progress = min(q.target_count, q.progress + amount)
            if q.progress >= q.target_count:
                q.completed = True

    # ── Update ────────────────────────────────────────────────────────
    def update(self, dt=None):
        if dt is None:
            dt = 1.0 / 60.0
        self.anim_time += dt
        self.flicker_t += dt
        if self.entrance_active:
            t = (time.time() - self.entrance_start) / 1.8
            self.entrance_progress = max(0.0, min(1.0, t))
            if self.entrance_progress >= 1.0:
                self.entrance_active = False
        if self.claim_flash_alpha > 0.0:
            self.claim_flash_time += dt
            self.claim_flash_alpha = max(0.0, 1.0 - self.claim_flash_time / 1.0)
        sw, sh = (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        try:
            sw, sh = self.app.screen.get_size()
        except Exception:
            pass
        self._ensure_layout(sw, sh)
        self._process_quest_cooldowns()

        mouse_pos = pygame.mouse.get_pos()
        hovering_reroll = self.reroll_icon_rect and self.reroll_icon_rect.collidepoint(mouse_pos)
        if hovering_reroll:
            reroll_ready = self.rerolls_remaining > 0 and time.time() >= self.reroll_cooldown_until
            if reroll_ready:
                tip_text = _("Reroll Quests") + "\n" + _("Available: {n}/{m}").format(n=self.rerolls_remaining, m=1)
            elif self.rerolls_remaining <= 0:
                tip_text = _("Reroll Unavailable") + "\n" + _("No rerolls remaining")
            else:
                remaining = int(self.reroll_cooldown_until - time.time())
                mins, secs = divmod(remaining, 60)
                tip_text = _("Reroll Quests") + "\n" + _("Available: {n}/{m}").format(n=self.rerolls_remaining, m=1) + "\n" + _("Cooldown: {m}:{s:02d}").format(m=mins, s=secs)
            if self.reroll_tooltip is None:
                self.reroll_tooltip = Tooltip(
                    self.reroll_icon_rect, tip_text,
                    cfg.tooltip_bg_CREDITS, cfg.tooltip_border_CREDITS,
                    cfg.tooltip_font_CREDITS, cfg.text_color,
                    cfg.tooltip_appear, cfg.tooltip_padding,
                )
            elif self.reroll_tooltip.text != tip_text:
                self.reroll_tooltip.text = tip_text
                self.reroll_tooltip._cache_key = ""
                self.reroll_tooltip._cached_surface = None
        elif self.reroll_tooltip is not None:
            self.reroll_tooltip = None

        # Update ambient particles with wrap-around
        for lst in (self.particles, self.star_particles, self.gold_dust):
            alive = []
            for p in lst:
                p.update(dt)
                if p.x < 0: p.x = sw
                elif p.x > sw: p.x = 0
                if p.y < -10:
                    p.y = sh + 10
                    if hasattr(p, 'max_life') and p.max_life > 0:
                        p.life = p.max_life
                if p.alive:
                    alive.append(p)
                elif p.shape == "dust":
                    p.x = random.uniform(0, sw)
                    p.y = random.uniform(0, sh)
                    p.life = p.max_life
                    alive.append(p)
            lst.clear()
            lst.extend(alive)

        for orb in self.ambient_orbs:
            orb["x"] += orb["vx"] * dt
            orb["y"] += orb["vy"] * dt
            if orb["x"] < -200:
                orb["x"] = sw + 200
            elif orb["x"] > sw + 200:
                orb["x"] = -200
            if orb["y"] < -200:
                orb["y"] = sh + 200
            elif orb["y"] > sh + 200:
                orb["y"] = -200

        new_bursts = []
        for p in self.burst_particles:
            p.update(dt)
            if p.life > 0:
                new_bursts.append(p)
        self.burst_particles = new_bursts

        if self.reroll_tooltip:
            self.reroll_tooltip.hover_update(mouse_pos)

    # ── Event handling ────────────────────────────────────────────────
    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            for btn in self.claim_buttons:
                if btn.rect.collidepoint(event.pos) and btn.on_click:
                    btn.on_click()
            if self.reroll_icon_rect and self.reroll_icon_rect.collidepoint(event.pos):
                self._reroll_quests()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_b):
                self.close_menu()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._bump_page_progress(1)

    # ── Drawing ───────────────────────────────────────────────────────
    def draw(self, screen):
        sw, sh = screen.get_size()
        self._ensure_layout(sw, sh)
        self.update()
        self._draw_background(screen)

        t = self.entrance_progress
        ease = 1.0 - (1.0 - t) ** 3
        panel = self.panel_rect

        slide_dist = int((1.0 - ease) * sh * 0.18)
        s = 0.90 + 0.10 * ease
        scaled_w = int(panel.width * s)
        scaled_h = int(panel.height * s)
        scaled_rect = pygame.Rect(0, 0, scaled_w, scaled_h)
        scaled_rect.center = (panel.centerx, panel.centery - slide_dist)

        if t > 0.08 and t < 0.6:
            ring_progress = (t - 0.08) / 0.52
            self._draw_entrance_ring(screen, panel, ring_progress)

        self._draw_soft_shadow(screen, scaled_rect, offset=14, alpha=80)
        self._draw_panel(screen, scaled_rect)
        self._draw_title(screen, scaled_rect)
        self._draw_quest_slots(screen, scaled_rect)
        self._draw_back_button(screen, scaled_rect)
        self._draw_reroll_ui(screen, scaled_rect)
        self._draw_ambient_particles(screen)
        self._draw_burst_particles(screen)
        self._draw_star_particles(screen)
        self._draw_gold_dust(screen)

    # ── Background ────────────────────────────────────────────────────
    def _draw_background(self, screen):
        sw, sh = screen.get_size()
        t = self.anim_time

        screen.fill((6, 4, 14))
        screen.blit(self._get_nebula(sw, sh), (0, 0))

        # Ambient floating orbs (cached surfaces)
        for orb in self.ambient_orbs:
            px = orb["x"] % sw
            py = orb["y"] % sh
            pulse = (math.sin(t * orb["pulse_speed"] + orb["pulse_offset"]) + 1.0) * 0.5
            alpha = int(orb["alpha"] * 255 * (0.6 + 0.4 * pulse))
            r = int(orb["radius"])
            orb_surf = self._get_orb_surface(r, orb["color"], alpha)
            screen.blit(orb_surf, (int(px) - r, int(py) - r))

        # Animated magical circle (rotating rings + hexagram)
        cx, cy = sw // 2, sh // 2
        circle_rot = t * 0.15
        for ring_idx, radius in enumerate([min(sw, sh) * 0.35, min(sw, sh) * 0.30, min(sw, sh) * 0.25]):
            p = (math.sin(t * 0.5 + ring_idx * 1.2) + 1.0) * 0.5
            a = int(10 + 20 * p)
            color = (GOLD[0], GOLD[1], GOLD[2], a)
            dir = 1 if ring_idx % 2 == 0 else -1
            segments = 64
            for i in range(segments):
                ang1 = circle_rot * dir + (i / segments) * math.pi * 2
                ang2 = circle_rot * dir + ((i + 1) / segments) * math.pi * 2
                if i % 4 == 0:
                    continue
                x1 = cx + math.cos(ang1) * radius
                y1 = cy + math.sin(ang1) * radius
                x2 = cx + math.cos(ang2) * radius
                y2 = cy + math.sin(ang2) * radius
                pygame.draw.line(screen, color, (x1, y1), (x2, y2), max(1, int(1.5 - ring_idx * 0.3)))

        # Hexagram
        hex_radius = min(sw, sh) * 0.18
        hex_rot = t * 0.08
        hex_alpha = int(12 + 10 * math.sin(t * 0.7))
        hex_color = (*PURPLE_BRIGHT, hex_alpha)
        points = []
        for i in range(6):
            ang = hex_rot + (i / 6) * math.pi * 2 - math.pi / 2
            points.append((cx + math.cos(ang) * hex_radius, cy + math.sin(ang) * hex_radius))
        for i in range(6):
            p1 = points[i]
            p2 = points[(i + 2) % 6]
            pygame.draw.line(screen, hex_color, p1, p2, 1)
        for i in range(6):
            p1 = points[i]
            p2 = points[(i + 1) % 6]
            pygame.draw.line(screen, hex_color, p1, p2, 1)

        # Energy arcs
        for arc in self.energy_arcs:
            ang = arc["angle"] + t * arc["speed"]
            radius = arc["radius"]
            length = arc["length"]
            a = int(arc["alpha"] * 255 * (0.6 + 0.4 * math.sin(t * 0.5 + arc["phase"])))
            if a < 3:
                continue
            color = arc["color"]
            steps = 20
            for step in range(steps):
                frac = step / steps
                theta = ang + (frac - 0.5) * (length / radius)
                px = cx + math.cos(theta) * radius
                py = cy + math.sin(theta) * radius
                sa = int(a * (1.0 - abs(frac - 0.5) * 2))
                if sa > 2:
                    pygame.draw.circle(screen, (*color, sa), (int(px), int(py)), max(1, int(arc["width"])))

        # Cached twinkling stars
        for star in self._cached_stars:
            twinkle = (math.sin(t * star["speed"] + star["phase"] + star["seed_a"]) + 1.0) * 0.5
            a = int(25 + 100 * twinkle)
            size = 1 + twinkle * 0.7
            c = star["color"]
            sx, sy = star["x"], star["y"]
            star_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(star_surf, (*c, a), (3, 3), max(1, int(size)))
            screen.blit(star_surf, (sx - 3, sy - 3))
            if twinkle > 0.85 and size > 1.4:
                glow_r = 10
                glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                ga = int(40 * twinkle)
                pygame.draw.circle(glow_surf, (*c, ga), (glow_r, glow_r), glow_r)
                screen.blit(glow_surf, (sx - glow_r, sy - glow_r))

        # Cached constellation lines
        for (x1, y1, x2, y2, idx) in self._cached_constellations:
            twinkle = (math.sin(t * 0.6 + x1 * 0.01 + y1 * 0.01 + idx) + 1.0) * 0.5
            a = int(6 + 12 * twinkle)
            if a > 3:
                pygame.draw.line(screen, (PURPLE_BRIGHT[0], PURPLE_BRIGHT[1], PURPLE_BRIGHT[2], a),
                                 (x1, y1), (x2, y2), 1)

        # Cached rune ornaments around edges
        for rune in self._cached_runes:
            pulse = (math.sin(t * 0.7 + rune["idx"] * 0.8) + 1.0) * 0.5
            a = int(20 + 60 * pulse)
            rune_surf = rune["surf"].copy()
            rune_surf.set_alpha(a)
            rw, rh = rune_surf.get_size()
            screen.blit(rune_surf, (rune["x"] - rw // 2, rune["y"] - rh // 2))

        # Radial glow behind panel
        max_r = int(min(sw, sh) * 0.65)
        glow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for r in range(max_r, 0, -4):
            p = r / max_r
            a = int(18 * (1.0 - p) * (0.5 + 0.5 * math.sin(t * 0.8)))
            ci = (
                int(PURPLE[0] * (1 - p) + GOLD_BRIGHT[0] * p),
                int(PURPLE[1] * (1 - p) + GOLD_BRIGHT[1] * p),
                int(PURPLE[2] * (1 - p) + GOLD_BRIGHT[2] * p),
                max(0, a),
            )
            pygame.draw.circle(glow_surf, ci, (cx, cy), r)
        screen.blit(glow_surf, (0, 0))

        # Light rays from center
        for i in range(16):
            ang = (i / 16) * math.pi * 2 + t * 0.05
            a = max(0, int(3 + 5 * math.sin(t * 0.3 + i * 0.8)))
            ray_len = min(sw, sh) * 0.8
            ex = cx + math.cos(ang) * ray_len
            ey = cy + math.sin(ang) * ray_len
            pygame.draw.line(screen, (*GOLD, a), (cx, cy), (ex, ey), 1)

        # Vignette
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        screen.blit(overlay, (0, 0))

    # ── UI Drawing ──────────────────────────────────────────────────
    def _draw_soft_shadow(self, screen, rect, offset=10, alpha=70):
        for i in range(4, 0, -1):
            sh_rect = rect.inflate(i * 4, i * 4)
            sh_surf = pygame.Surface(sh_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(sh_surf, (0, 0, 0, max(0, alpha - i * 12)),
                             sh_surf.get_rect(), border_radius=22)
            screen.blit(sh_surf, (sh_rect.x - offset // 2, sh_rect.y + offset // 2))

    def _draw_panel(self, screen, rect):
        # Outer majestic border
        outer = rect.inflate(6, 6)
        pygame.draw.rect(screen, GOLD_DARK, outer, border_radius=22)
        pygame.draw.rect(screen, PURPLE, rect.inflate(3, 3), width=2, border_radius=20)

        # Panel fill
        pygame.draw.rect(screen, BLACK_PANEL, rect, border_radius=18)
        pygame.draw.rect(screen, GOLD_DEEP, rect.inflate(-6, -6), width=1, border_radius=14)

        # Gradient overlay (purple tint from top to bottom)
        grad = pygame.Surface(rect.size, pygame.SRCALPHA)
        for y in range(rect.height):
            tt = y / max(1, rect.height - 1)
            a = int(24 * tt)
            pygame.draw.line(grad, (PURPLE_DEEP[0], PURPLE_DEEP[1], PURPLE_DEEP[2], a),
                             (0, y), (rect.width, y))
        clip = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(clip, (255, 255, 255, 255), clip.get_rect(), border_radius=18)
        grad.blit(clip, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(grad, rect.topleft)

        # Arcane sigil watermark at panel center
        sigil_w = int(rect.width * 0.35)
        sigil_h = int(rect.height * 0.30)
        sigil = self._get_sigil_surface(sigil_w, sigil_h)
        pulse = (math.sin(self.anim_time * 1.5) + 1.0) * 0.5
        sigil.set_alpha(int(40 + 60 * pulse))
        sx = rect.x + (rect.width - sigil_w) // 2
        sy = rect.y + (rect.height - sigil_h) // 2
        screen.blit(sigil, (sx, sy))

        # Ornate corner gems
        gem_size = 10
        for gcx, gcy in [
            (rect.x + 14, rect.y + 14),
            (rect.right - 14, rect.y + 14),
            (rect.x + 14, rect.bottom - 14),
            (rect.right - 14, rect.bottom - 14),
        ]:
            lighter = tuple(min(255, c + 60) for c in PURPLE)
            darker = tuple(max(0, c - 40) for c in PURPLE)
            pts = [(gcx, gcy - gem_size), (gcx - gem_size, gcy), (gcx + gem_size, gcy)]
            pygame.draw.polygon(screen, lighter, pts)
            pts = [(gcx - gem_size, gcy), (gcx + gem_size, gcy), (gcx, gcy + gem_size)]
            pygame.draw.polygon(screen, darker, pts)
            gp = (math.sin(self.anim_time * 2.0 + gcx * 0.1) + 1.0) * 0.5
            glow_r = gem_size * 2
            gsurf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            ga = int(30 + 50 * gp)
            pygame.draw.circle(gsurf, (*GOLD_BRIGHT, ga), (glow_r, glow_r), glow_r)
            screen.blit(gsurf, (gcx - glow_r, gcy - glow_r))
            pygame.draw.circle(screen, GOLD_BRIGHT, (gcx - 2, gcy - 2), max(2, gem_size // 4))

        # Corner rune ornaments
        rune_orn = cfg.get_font(max(12, int(18 * cfg.ui_scale())))
        orn_chars = ["ᛟ", "ᛞ", "ᛝ", "ᛚ"]
        for idx, (gcx, gcy) in enumerate([
            (rect.x + 14, rect.y + 14),
            (rect.right - 14, rect.y + 14),
            (rect.x + 14, rect.bottom - 14),
            (rect.right - 14, rect.bottom - 14),
        ]):
            pulse = (math.sin(self.anim_time * 1.2 + idx * 1.5) + 1.0) * 0.5
            a = int(60 + 80 * pulse)
            o = rune_orn.render(orn_chars[idx], True, (*GOLD, a))
            screen.blit(o, (gcx - o.get_width() // 2, gcy - o.get_height() // 2 - 2))

        # Decorative border runes along top and bottom edges
        small_rune = cfg.get_font(max(8, int(12 * cfg.ui_scale())))
        border_runes = ["ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ", "ᚷ", "ᚹ", "ᚺ", "ᚾ", "ᛁ", "ᛃ"]
        for i, ch in enumerate(border_runes):
            frac = (i + 0.5) / len(border_runes)
            bp = (math.sin(self.anim_time * 1.5 + i * 0.9) + 1.0) * 0.5
            ba = int(30 + 50 * bp)
            rs = small_rune.render(ch, True, (*GOLD_DEEP, ba))
            # Top edge
            tx = rect.x + int(rect.width * frac)
            screen.blit(rs, (tx - rs.get_width() // 2, rect.y + 2))
            # Bottom edge
            screen.blit(rs, (tx - rs.get_width() // 2, rect.bottom - rs.get_height() - 2))

    def _draw_title(self, screen, panel_rect):
        cx = panel_rect.centerx
        title_y = panel_rect.y + 20
        title_text = _("ARCANE QUESTS")
        title_surf = self.title_font.render(title_text, True, GOLD_BRIGHT)
        shadow_surf = self.title_font.render(title_text, True, (0, 0, 0))

        t = self.entrance_progress
        if self.entrance_active:
            title_delay = 0.1
            title_dur = 0.4
            title_p = max(0.0, min(1.0, (t - title_delay) / title_dur))
            if title_p <= 0.0:
                return
            title_ease = 1.0 - (1.0 - title_p) ** 2
            title_scale = 0.6 + 0.4 * title_ease
            title_alpha = int(255 * title_ease)
            scaled_ts = pygame.transform.scale(
                title_surf,
                (int(title_surf.get_width() * title_scale), int(title_surf.get_height() * title_scale))
            )
            scaled_ts.set_alpha(title_alpha)
            ts = scaled_ts
        else:
            ts = title_surf

        # Purple glow behind title
        glow = pygame.Surface((ts.get_width() + 60, ts.get_height() + 30), pygame.SRCALPHA)
        pulse = (math.sin(self.anim_time * 2.0) + 1.0) * 0.5
        glow_alpha = int(70 + 60 * pulse)
        glow.fill((*PURPLE_BRIGHT, glow_alpha))
        inner = pygame.Rect(20, 10, ts.get_width() + 20, ts.get_height() + 10)
        pygame.draw.rect(glow, (0, 0, 0, 0), inner)
        screen.blit(glow, (cx - glow.get_width() // 2, title_y - 10))

        # Shadow
        if self.entrance_active:
            shadow_ts = pygame.transform.scale(
                shadow_surf,
                (int(shadow_surf.get_width() * title_scale), int(shadow_surf.get_height() * title_scale))
            )
            shadow_ts.set_alpha(title_alpha)
            screen.blit(shadow_ts, (cx - ts.get_width() // 2 + 2, title_y + 2))
        else:
            screen.blit(shadow_surf, (cx - ts.get_width() // 2 + 2, title_y + 2))
        screen.blit(ts, (cx - ts.get_width() // 2, title_y))

        # Decorative line under title with diamond endpoints
        line_y = title_y + ts.get_height() + 6
        line_w = int(panel_rect.width * 0.7)
        line_x = cx - line_w // 2
        for i in range(line_w):
            tt = abs(i - line_w / 2) / (line_w / 2)
            a = int(180 * (1.0 - tt))
            if i % 2 == 0:
                pygame.draw.line(screen, (*GOLD_BRIGHT, a), (line_x + i, line_y),
                                 (line_x + i, line_y), 1)
        for dx in [line_x - 4, line_x + line_w + 4]:
            dsz = 5
            dpts = [(dx, line_y - dsz), (dx + dsz, line_y),
                    (dx, line_y + dsz), (dx - dsz, line_y)]
            pygame.draw.polygon(screen, GOLD, dpts)

        # Decorative arcane swashes on both sides of title
        swash_font = cfg.get_font(max(14, int(22 * cfg.ui_scale())))
        left_swash = swash_font.render("⟐", True, (*GOLD_DEEP, 120))
        right_swash = swash_font.render("⟐", True, (*GOLD_DEEP, 120))
        swash_y = title_y + ts.get_height() // 2 - left_swash.get_height() // 2
        screen.blit(left_swash, (line_x - left_swash.get_width() - 10, swash_y))
        screen.blit(right_swash, (line_x + line_w + 10, swash_y))

    def _draw_entrance_ring(self, screen, panel_rect, progress):
        cx, cy = panel_rect.center
        max_radius = int(max(panel_rect.width, panel_rect.height) * 0.7)
        radius = int(max_radius * progress)
        alpha = int(80 * (1.0 - progress) * (1.0 + math.sin(self.anim_time * 8)))
        if alpha < 3:
            return
        ring_surf = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
        pulse = (math.sin(self.anim_time * 10 + progress * 5) + 1.0) * 0.5
        for w in range(2, 0, -1):
            a = int(alpha * (1.0 - w * 0.2))
            col = (
                int(GOLD_BRIGHT[0] * (0.7 + 0.3 * pulse)),
                int(GOLD_BRIGHT[1] * (0.7 + 0.3 * pulse)),
                int(GOLD_BRIGHT[2] * (0.5 + 0.5 * pulse)),
                a,
            )
            pygame.draw.circle(ring_surf, col, (radius + 5, radius + 5), radius + w * 2, width=max(1, int(2 + w)))
        screen.blit(ring_surf, (cx - radius - 5, cy - radius - 5))

    def _draw_quest_slots(self, screen, panel_rect):
        t = self.entrance_progress
        for i, q in enumerate(self.quests):
            if i >= len(self.slot_rects):
                break
            r = self.slot_rects[i].copy()
            r.clamp_ip(panel_rect)
            if r.width <= 0 or r.height <= 0:
                continue

            # Entrance stagger
            if self.entrance_active:
                slot_delay = 0.25 + i * 0.12
                slot_duration = 0.35
                slot_progress = max(0.0, min(1.0, (t - slot_delay) / slot_duration))
                if slot_progress <= 0.0:
                    continue
                slot_ease = 1.0 - (1.0 - slot_progress) ** 2
                slide_offset = int(r.width * 0.3 * (1.0 - slot_ease))
                slot_alpha = int(255 * slot_ease)
                r = r.move(slide_offset, 0)
            else:
                slot_alpha = 255

            completed_ready = q.is_finished and not q.claimed
            claimed = q.claimed

            # Outer glow when completable
            if completed_ready:
                pulse = (math.sin(self.anim_time * 3.0 + i * 0.7) + 1.0) * 0.5
                glow_surf = pygame.Surface((r.width + 8, r.height + 8), pygame.SRCALPHA)
                ga = int(40 + 50 * pulse)
                pygame.draw.rect(glow_surf, (*GOLD_BRIGHT, ga), glow_surf.get_rect(), border_radius=12)
                screen.blit(glow_surf, (r.x - 4, r.y - 4))

            # Slot border
            outer_col = GOLD_BRIGHT if completed_ready else (GOLD_DARK if not claimed else PURPLE_DARK)
            pygame.draw.rect(screen, outer_col, r.inflate(3, 3), border_radius=10)
            pygame.draw.rect(screen, PURPLE_DARK if not claimed else (45, 45, 55), r, border_radius=10)

            # Animated arcane border runes on unclaimed slots
            if not claimed:
                border_font = cfg.get_font(max(6, int(9 * cfg.ui_scale())))
                runes = ["ᚠ", "ᛟ", "ᚲ", "ᛉ"]
                for rune_idx, (rx_pos, ry_pos) in enumerate([
                    (r.x + 4, r.centery), (r.right - 4, r.centery),
                    (r.centerx, r.y + 4), (r.centerx, r.bottom - 4),
                ]):
                    rp = (math.sin(self.anim_time * 2.0 + i * 0.5 + rune_idx * 1.3) + 1.0) * 0.5
                    ra = int(30 + 60 * rp)
                    rs = border_font.render(runes[rune_idx % len(runes)], True, (*GOLD_DEEP, ra))
                    rsr = rs.get_rect(center=(rx_pos, ry_pos))
                    screen.blit(rs, rsr)

            # Slot background fill
            inner = r.inflate(-4, -4)
            bg_col = (20, 12, 32) if not claimed else (25, 25, 30)
            pygame.draw.rect(screen, bg_col, inner, border_radius=8)
            if not claimed:
                pygame.draw.rect(screen, GOLD_DEEP, inner.inflate(-2, -2), width=1, border_radius=6)

            # Subtle slot arcane sigil watermark
            sigil_w = min(inner.width, inner.height) // 3
            if sigil_w > 8 and not claimed:
                ss = pygame.Surface((sigil_w * 2, sigil_w * 2), pygame.SRCALPHA)
                scx, scy = sigil_w, sigil_w
                for ring in range(2, 0, -1):
                    ra = max(0, int(8 + 10 * math.sin(self.anim_time * 1.5 + i + ring)))
                    pygame.draw.circle(ss, (*PURPLE_DEEP, ra), (scx, scy), sigil_w * ring // 2, width=1)
                l_a = max(0, int(8 + 12 * math.sin(self.anim_time * 2 + i)))
                pygame.draw.line(ss, (*PURPLE_DEEP, l_a),
                                 (scx - sigil_w // 2, scy), (scx + sigil_w // 2, scy), 1)
                l_a2 = max(0, int(8 + 12 * math.sin(self.anim_time * 2 + i + 1)))
                pygame.draw.line(ss, (*PURPLE_DEEP, l_a2),
                                 (scx, scy - sigil_w // 2), (scx, scy + sigil_w // 2), 1)
                screen.blit(ss, (inner.right - sigil_w * 2 - 4, inner.centery - sigil_w))

            # Quest title
            title_surf = self.section_font.render(q.title, True, GOLD_BRIGHT if not claimed else (120, 120, 130))
            if slot_alpha < 255:
                title_surf.set_alpha(slot_alpha)
            screen.blit(title_surf, (r.x + 10, r.y + 6))

            # Mob description
            desc_surf = self.body_font.render(q.description, True, PURPLE_BRIGHT if not claimed else (100, 100, 110))
            if slot_alpha < 255:
                desc_surf.set_alpha(slot_alpha)
            screen.blit(desc_surf, (r.x + 10, r.y + 10 + title_surf.get_height()))

            # Reward text
            reward_parts = []
            if "xp" in q.reward:
                reward_parts.append(f"{q.reward['xp']}XP")
            if "gold" in q.reward:
                reward_parts.append(f"{q.reward['gold']}G")
            if "item" in q.reward:
                reward_parts.append(str(q.reward['item']))
            reward_text = " • ".join(reward_parts) if reward_parts else ""
            if reward_text:
                reward_surf = self.small_font.render(reward_text, True, GOLD if not claimed else (100, 100, 110))
                if slot_alpha < 255:
                    reward_surf.set_alpha(slot_alpha)
                screen.blit(reward_surf, (r.x + 10, r.y + 10 + title_surf.get_height() + desc_surf.get_height() + 2))

            # Progress bar
            bar_w = int(r.width * 0.5)
            bar_h = max(10, int(16 * cfg.ui_scale()))
            bar_x = r.x + 10
            bar_y = r.bottom - bar_h - int(6 * cfg.ui_scale())
            if claimed:
                bar_y = r.centery - bar_h // 2
            bar_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
            self._draw_progress_bar(screen, bar_rect, q.progress_fraction(),
                                    glowing=(completed_ready and not claimed))

            # Progress label
            if not claimed:
                prog_label = _("{cur}/{max}").format(cur=q.progress, max=q.target_count)
                prog_surf = self.small_font.render(prog_label, True, WHITE_SOFT)
                if slot_alpha < 255:
                    prog_surf.set_alpha(slot_alpha)
                screen.blit(prog_surf, (bar_rect.right + 6, bar_rect.y - 1))

            # Claim / Claimed button
            if i < len(self.claim_buttons) and not claimed:
                btn = self.claim_buttons[i]
                cw = btn.rect.width
                ch = btn.rect.height
                btn.rect.topleft = (r.right - cw - int(8 * cfg.ui_scale()),
                                    r.bottom - ch - int(6 * cfg.ui_scale()))
                if completed_ready:
                    self._draw_magical_claim_button(screen, btn, i)
                else:
                    self._draw_locked_button(screen, btn)
            elif claimed:
                if q.on_cooldown:
                    remaining = q.cooldown_remaining
                    total = ArcaneQuest.QUEST_COOLDOWN_SECONDS
                    frac = remaining / total
                    ring_radius = int(min(r.width, r.height) * 0.22)
                    ring_radius = max(14, ring_radius)
                    cx_slot, cy_slot = r.centerx + int(r.width * 0.08), r.centery
                    # Ring background
                    pygame.draw.circle(screen, (*PURPLE_DARK, 60), (cx_slot, cy_slot), ring_radius, width=3)
                    # Arcane progress arc
                    arc_steps = 30
                    for step in range(arc_steps):
                        if step / arc_steps > (1.0 - frac):
                            break
                        ang = -math.pi / 2 + (step / arc_steps) * math.pi * 2
                        next_ang = -math.pi / 2 + ((step + 1) / arc_steps) * math.pi * 2
                        x1 = cx_slot + math.cos(ang) * ring_radius
                        y1 = cy_slot + math.sin(ang) * ring_radius
                        x2 = cx_slot + math.cos(next_ang) * ring_radius
                        y2 = cy_slot + math.sin(next_ang) * ring_radius
                        ap = (math.sin(self.anim_time * 2.5 + step * 0.3) + 1.0) * 0.5
                        a = int(120 + 135 * ap)
                        pygame.draw.line(screen, (*GOLD_BRIGHT, a), (x1, y1), (x2, y2),
                                         max(1, int(2 + ap * 2)))
                    # Countdown text
                    mins, secs = divmod(int(remaining), 60)
                    cd_text = _("{m}:{s:02d}").format(m=mins, s=secs)
                    cd_surf = self.small_font.render(cd_text, True, GOLD)
                    screen.blit(cd_surf, cd_surf.get_rect(center=(cx_slot, cy_slot)))
                else:
                    # Ornate CLAIMED badge
                    badge_w = max(70, int(100 * cfg.ui_scale()))
                    badge_h = max(22, int(30 * cfg.ui_scale()))
                    badge_rect = pygame.Rect(r.right - badge_w - int(8 * cfg.ui_scale()),
                                             r.centery - badge_h // 2, badge_w, badge_h)
                    bg = pygame.Surface(badge_rect.size, pygame.SRCALPHA)
                    pygame.draw.rect(bg, (40, 40, 50, 200), bg.get_rect(), border_radius=6)
                    pygame.draw.rect(bg, (GOLD_DARK[0], GOLD_DARK[1], GOLD_DARK[2], 180),
                                     bg.get_rect(), 1, border_radius=6)
                    screen.blit(bg, badge_rect)
                    done_surf = self.small_font.render(_("CLAIMED"), True, GOLD)
                    done_surf.set_alpha(200)
                    screen.blit(done_surf, done_surf.get_rect(center=badge_rect.center))

    def _draw_magical_claim_button(self, screen, btn, idx):
        pulse = (math.sin(self.anim_time * 3.0 + idx * 1.1) + 1.0) * 0.5

        # Outer glow aura
        aura_size = int(btn.rect.width * 1.4)
        aura_surf = pygame.Surface((aura_size, aura_size), pygame.SRCALPHA)
        aa = int(60 + 70 * pulse)
        for r_ in range(aura_size // 2, 0, -4):
            t_ = r_ / (aura_size // 2)
            col = (
                int(GOLD_BRIGHT[0] * (1 - t_) + PURPLE_BRIGHT[0] * t_),
                int(GOLD_BRIGHT[1] * (1 - t_) + PURPLE_BRIGHT[1] * t_),
                int(GOLD_BRIGHT[2] * (1 - t_) + PURPLE_BRIGHT[2] * t_),
                max(0, int(aa * (1 - t_))),
            )
            pygame.draw.circle(aura_surf, col, (aura_size // 2, aura_size // 2), r_)
        screen.blit(aura_surf,
                    (btn.rect.centerx - aura_size // 2, btn.rect.centery - aura_size // 2))

        # Gradient background (gold → purple)
        grad = pygame.Surface(btn.rect.size, pygame.SRCALPHA)
        for x in range(btn.rect.width):
            tt = x / max(1, btn.rect.width - 1)
            cr = int(GOLD_BRIGHT[0] * (1 - tt) + PURPLE[0] * tt)
            cg = int(GOLD_BRIGHT[1] * (1 - tt) + PURPLE[1] * tt)
            cb = int(GOLD_BRIGHT[2] * (1 - tt) + PURPLE[2] * tt)
            pygame.draw.line(grad, (cr, cg, cb), (x, 0), (x, btn.rect.height))
        mask = pygame.Surface(btn.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=8)
        grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(grad, btn.rect.topleft)

        # Gold border
        pygame.draw.rect(screen, GOLD_BRIGHT, btn.rect, 2, border_radius=8)

        # Text with glow
        text_surf = btn.font.render(btn.text, True, (255, 255, 240))
        text_rect = text_surf.get_rect(center=btn.rect.center)
        shadow_surf = btn.font.render(btn.text, True, (80, 50, 20, 120))
        screen.blit(shadow_surf, (text_rect.x + 1, text_rect.y + 1))
        screen.blit(text_surf, text_rect)

        # Decorative stars
        self._draw_star(screen, btn.rect.x + 8, btn.rect.centery, 2.5, GOLD_BRIGHT,
                        self.anim_time + idx * 0.3)
        self._draw_star(screen, btn.rect.right - 8, btn.rect.centery, 2.5, PURPLE_BRIGHT,
                        self.anim_time + idx * 0.3 + 1.5)

    def _draw_locked_button(self, screen, btn):
        dim_grad = pygame.Surface(btn.rect.size, pygame.SRCALPHA)
        for x in range(btn.rect.width):
            tt = x / max(1, btn.rect.width - 1)
            cr = int(40 * (1 - tt) + 55 * tt)
            cg = int(28 * (1 - tt) + 32 * tt)
            cb = int(50 * (1 - tt) + 45 * tt)
            pygame.draw.line(dim_grad, (cr, cg, cb, 180), (x, 0), (x, btn.rect.height))
        dim_mask = pygame.Surface(btn.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(dim_mask, (255, 255, 255, 255), dim_mask.get_rect(), border_radius=8)
        dim_grad.blit(dim_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(dim_grad, btn.rect.topleft)
        pygame.draw.rect(screen, (GOLD_DARK[0], GOLD_DARK[1], GOLD_DARK[2]),
                         btn.rect, 1, border_radius=8)
        text_surf = btn.font.render(btn.text, True, (140, 135, 150))
        text_rect = text_surf.get_rect(center=btn.rect.center)
        screen.blit(text_surf, text_rect)

    def _draw_progress_bar(self, screen, rect, frac, glowing=False):
        # Background track
        pygame.draw.rect(screen, (8, 4, 18), rect, border_radius=rect.height // 2)
        inner = rect.inflate(-2, -2)
        pygame.draw.rect(screen, (20, 10, 32), inner, border_radius=inner.height // 2)

        # Gold→purple gradient fill
        fill_w = max(0, int(rect.width * frac))
        if fill_w > 0:
            for x in range(fill_w):
                tt = x / max(1, fill_w - 1)
                r = int(GOLD[0] * (1 - tt) + PURPLE_BRIGHT[0] * tt)
                g = int(GOLD[1] * (1 - tt) + PURPLE_BRIGHT[1] * tt)
                b = int(GOLD[2] * (1 - tt) + PURPLE_BRIGHT[2] * tt)
                pygame.draw.line(screen, (r, g, b), (rect.x + x, rect.y + 1),
                                 (rect.x + x, rect.bottom - 2))

            # Completion sparkle near end of bar
            if frac > 0.9 and glowing:
                sp = (math.sin(self.anim_time * 6.0) + 1.0) * 0.5
                sx_end = rect.x + fill_w - 2
                sa = int(80 + 175 * sp)
                sz = max(1, int(2 + sp * 2))
                pygame.draw.circle(screen, (*GOLD_BRIGHT, sa), (sx_end, rect.centery), sz)

        # Clip to rounded rect
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(),
                         border_radius=rect.height // 2)
        screen.blit(mask, rect.topleft, special_flags=pygame.BLEND_RGBA_MULT)
        pygame.draw.rect(screen, GOLD_DEEP, rect, width=1, border_radius=rect.height // 2)

        # Glow border when completable
        if glowing:
            pulse = (math.sin(self.anim_time * 4.0) + 1.0) * 0.5
            ga = int(80 + 80 * pulse)
            glow = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow, (*GOLD_BRIGHT, ga), glow.get_rect(),
                             width=2, border_radius=rect.height // 2)
            screen.blit(glow, rect.topleft)

    def _draw_reroll_ui(self, screen, panel_rect):
        bx = panel_rect.right - int(64 * cfg.ui_scale())
        by = panel_rect.bottom - int(48 * cfg.ui_scale())
        size = int(28 * cfg.ui_scale())
        self.reroll_icon_rect = pygame.Rect(bx - size // 2, by - size // 2, size, size)

        ready = self.rerolls_remaining > 0 and time.time() >= self.reroll_cooldown_until
        color = GOLD_BRIGHT if ready else (100, 90, 120)

        # Outer glow when ready
        if ready:
            pulse = (math.sin(self.anim_time * 3.0) + 1.0) * 0.5
            glow_surf = pygame.Surface((size + 16, size + 16), pygame.SRCALPHA)
            ga = int(60 + 70 * pulse)
            pygame.draw.circle(glow_surf, (*GOLD_BRIGHT, ga),
                               ((size + 16) // 2, (size + 16) // 2), (size + 16) // 2)
            screen.blit(glow_surf, (bx - (size + 16) // 2, by - (size + 16) // 2))

        # Cooldown ring
        on_cooldown = self.rerolls_remaining <= 0 and time.time() < self.reroll_cooldown_until
        if on_cooldown:
            ring_radius = int(size * 0.75)
            remaining = max(0.0, self.reroll_cooldown_until - time.time())
            total = 600.0
            frac = remaining / total
            pygame.draw.circle(screen, (*PURPLE_DARK, 80), (bx, by), ring_radius, width=2)
            arc_steps = 24
            for step in range(arc_steps):
                if step / arc_steps > (1.0 - frac):
                    break
                ang = -math.pi / 2 + (step / arc_steps) * math.pi * 2
                next_ang = -math.pi / 2 + ((step + 1) / arc_steps) * math.pi * 2
                x1 = bx + math.cos(ang) * ring_radius
                y1 = by + math.sin(ang) * ring_radius
                x2 = bx + math.cos(next_ang) * ring_radius
                y2 = by + math.sin(next_ang) * ring_radius
                ap = (math.sin(self.anim_time * 2.5 + step * 0.4) + 1.0) * 0.5
                a = int(100 + 155 * ap)
                pygame.draw.line(screen, (*GOLD, a), (x1, y1), (x2, y2), max(1, int(2 + ap * 2)))

        # Diamond background
        pts = [(bx, by - size // 2), (bx + size // 2, by),
               (bx, by + size // 2), (bx - size // 2, by)]
        pygame.draw.polygon(screen, (40, 25, 60) if not ready else (60, 35, 90), pts)
        pygame.draw.polygon(screen, color, pts, width=2)

        # ↻ refresh symbol
        if ready:
            rot = math.degrees(self.anim_time * 30) % 360
        else:
            rot = 0.0
        icon_text = "↻"
        icon_font = cfg.get_font(max(12, int(18 * cfg.ui_scale())))
        icon_surf = icon_font.render(icon_text, True, color)
        if ready:
            icon_surf = pygame.transform.rotate(icon_surf, rot)
        icon_rect = icon_surf.get_rect(center=(bx, by))
        screen.blit(icon_surf, icon_rect)

        if self.reroll_tooltip:
            self.reroll_tooltip.draw(screen)

    def _draw_back_button(self, screen, panel_rect):
        btn = self.back_button
        if not panel_rect.colliderect(btn.rect):
            return
        pulse = (math.sin(self.anim_time * 2.0) + 1.0) * 0.5
        border_rect = btn.rect.inflate(4, 4)
        bw = int(1 + pulse * 0.5)
        border_color = (
            int(GOLD[0] * (1 - pulse * 0.3)),
            int(GOLD[1] * (1 - pulse * 0.3)),
            int(GOLD[2] * (1 - pulse * 0.3)),
        )
        pygame.draw.rect(screen, border_color, border_rect, width=bw, border_radius=12)
        btn.draw(screen)

    def _draw_star(self, screen, x, y, size, color, t):
        pulse = (math.sin(t * 4.0) + 1.0) * 0.5
        s = max(1, int(size * (0.8 + 0.4 * pulse)))
        glow_size = s * 3
        glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, int(80 * (0.4 + 0.6 * pulse))),
                           (glow_size, glow_size), glow_size)
        screen.blit(glow, (x - glow_size, y - glow_size))
        pts = [(x, y - s), (x + s, y), (x, y + s), (x - s, y)]
        pygame.draw.polygon(screen, color, pts)
        core_color = tuple(min(255, c + 60) for c in color)
        pygame.draw.circle(screen, core_color, (x, y), max(1, s // 2))

    def _draw_ambient_particles(self, screen):
        for p in self.particles:
            if p.y > screen.get_height() + 10:
                continue
            sz = max(1, int(p.size))
            a = int(180 * p.alpha)
            if a <= 5:
                continue
            s = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p.color, a // 3), (sz, sz), sz)
            screen.blit(s, (int(p.x) - sz, int(p.y) - sz))
            pygame.draw.circle(screen, (*p.color, a), (int(p.x), int(p.y)), max(1, sz // 2))

    def _draw_burst_particles(self, screen):
        for p in self.burst_particles:
            sz = max(1, int(p.size * p.alpha))
            a = int(255 * p.alpha)
            if a <= 5:
                continue
            if p.shape == "star":
                self._draw_star(screen, int(p.x), int(p.y), int(p.size), p.color, self.anim_time)
            else:
                s = pygame.Surface((sz * 3, sz * 3), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p.color, a // 3), (sz, sz), sz)
                screen.blit(s, (int(p.x) - sz, int(p.y) - sz))
                pygame.draw.circle(screen, (*p.color, a), (int(p.x), int(p.y)), sz)

    def _draw_star_particles(self, screen):
        for p in self.star_particles:
            if p.y > screen.get_height() + 10:
                continue
            self._draw_star(screen, int(p.x), int(p.y), int(p.size), p.color, self.anim_time + p.x)

    def _draw_gold_dust(self, screen):
        for p in self.gold_dust:
            sz = max(1, int(p.size))
            a = int(200 * p.alpha)
            if a <= 3:
                continue
            pygame.draw.circle(screen, (*p.color, a), (int(p.x), int(p.y)), sz)
