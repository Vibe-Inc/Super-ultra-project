"""
Arcane Quest Menu - A magical quest interface with gold and purple accents on black.

Features:
- Gold & purple magical style on a black base
- Quest list with a template: "Kill X mobs in Y"
- A 'Completed' button when the objective is met
- A gray 'Claim Reward' button that lights up (turns colorful & magical) when the quest is finished
- Plenty of space for future expansion (multiple quest slots, scrolling, etc.)
- Beautiful "WOW" effects: ambient sparkles, shimmer, breathing glow, particle bursts, runes
"""

import math
import random
import time
import pygame
from typing import TYPE_CHECKING

from src.ui.menus.base import Menu
from src.ui.widgets import Button
import src.config as cfg
from src.core.logger import logger

# Ensure _ is available for gettext translations
try:
    _  # type: ignore[used-before-def]
except NameError:
    from gettext import gettext as _

if TYPE_CHECKING:
    from src.app import App


# ── Magical palette ──────────────────────────────────────────────────────
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


class _Particle:
    """Lightweight particle used for ambient sparkles and burst effects."""

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
    """A single quest definition (template) tracked in the menu."""

    def __init__(self, quest_id, title, description, target_type, target_count, location_label, reward):
        self.id = quest_id
        self.title = title
        self.description = description
        self.target_type = target_type  # e.g., "mobs"
        self.target_count = int(target_count)
        self.location_label = location_label  # e.g., "the Dark Forest"
        self.reward = reward  # dict like {"xp": 100, "gold": 50}

        # Mutable progress
        self.progress = 0
        self.completed = False
        self.claimed = False

    @property
    def is_finished(self):
        return self.completed or self.progress >= self.target_count

    def progress_fraction(self):
        return min(1.0, self.progress / max(1, self.target_count))

    def description_with_progress(self):
        return f"{self.description}  ({self.progress}/{self.target_count})"

    def mark_complete(self):
        self.completed = True
        self.progress = self.target_count


class ArcaneQuestMenu(Menu):
    """
    The Arcane Quest menu — a magical interface for tracking quests.

    Attributes:
        app (App): The main application instance.
        title_font (pygame.font.Font): Font for the title.
        section_font (pygame.font.Font): Font for section headers.
        body_font (pygame.font.Font): Font for body text.
        small_font (pygame.font.Font): Font for small labels.
        back_button (Button): Button to return to the previous state.
        claim_button (Button): 'Claim Reward' button at the bottom.
        complete_button (Button): 'Completed' indicator (visible when quest is done).
        quest (ArcaneQuest | None): Currently displayed quest.
        particles (list): Active ambient particles.
        burst_particles (list): Burst particles spawned when claiming.
        anim_time (float): Accumulated time for animations.
        _layout_size (tuple | None): Cached screen size.

    Methods:
        __init__(app): Set up the menu, fonts, and the template quest.
        _init_quest(): Initialize the template quest ("Kill X mobs in Y").
        _init_particles(): Seed ambient magical particles.
        _ensure_layout(): Ensure UI positions are up to date.
        _recalc_layout(): Recompute UI positions for the current screen size.
        close_menu(): Return to gameplay.
        on_enter(): Reset animations and play entrance flash.
        update(dt): Animate particles and the breathing glow.
        handle_event(event): Forward to base + 'c' / 'space' to claim.
        draw(screen): Render the full magical UI.
        _draw_background(surf): Render the magical background (runes, stars, vignette).
        _draw_rune_circle(surf, cx, cy, radius, t): A slowly rotating magical circle.
        _draw_quest_panel(surf): Render the active quest card.
        _draw_claim_button(surf): Render the 'Claim Reward' button (gray → magical).
        _draw_complete_button(surf): Render the 'Completed' badge.
        _draw_progress_bar(surf, x, y, w, h, frac, color): Render a glowing progress bar.
        _draw_star(surf, x, y, size, color, t): Draw a 4-point sparkle star.
        _spawn_burst(x, y, color, n=40): Spawn burst particles at (x, y).
        _bump_quest_progress(amount): Helper to advance the quest (and emit particles).
        claim_reward(): Claim the reward (bursts + progress reset + brief flicker).
    """

    def __init__(self, app: "App"):
        super().__init__(app)
        scale = cfg.ui_scale()

        # ── Fonts ────────────────────────────────────────────────────
        self.title_font   = cfg.get_font(max(20, int(46 * scale)))
        self.section_font = cfg.get_font(max(16, int(28 * scale)))
        self.body_font    = cfg.get_font(max(14, int(20 * scale)))
        self.small_font   = cfg.get_font(max(12, int(16 * scale)))
        self.reward_font  = cfg.get_font(max(14, int(22 * scale)))

        # ── Buttons ──────────────────────────────────────────────────
        btn_w = max(160, int(280 * scale))
        btn_h = max(40, int(54 * scale))
        self.back_button = Button(
            pygame.Rect(0, 0, btn_w, btn_h),
            _("BACK"),
            (60, 35, 75),
            (90, 55, 115),
            cfg.button_font,
            GOLD_BRIGHT,
            max(2, int(10 * scale)),
            on_click=self.close_menu,
        )

        # Claim Reward button (gray when locked, magical gold/purple when ready)
        claim_w = max(220, int(360 * scale))
        claim_h = max(48, int(64 * scale))
        self.claim_button = Button(
            pygame.Rect(0, 0, claim_w, claim_h),
            _("CLAIM REWARD"),
            (75, 75, 80),       # neutral gray base
            (105, 105, 110),    # gray hover
            cfg.button_font,
            (220, 220, 225),
            max(2, int(12 * scale)),
            on_click=self.claim_reward,
        )

        # 'Completed' indicator — a small badge that appears when the quest is done
        complete_w = max(140, int(220 * scale))
        complete_h = max(34, int(46 * scale))
        self.complete_button = Button(
            pygame.Rect(0, 0, complete_w, complete_h),
            _("COMPLETED"),
            (35, 110, 70),
            (55, 150, 95),
            cfg.button_font,
            (220, 255, 230),
            max(2, int(10 * scale)),
            on_click=None,
        )

        self.buttons = [self.back_button, self.claim_button, self.complete_button]

        # ── Quest data ───────────────────────────────────────────────
        self.quests: list[ArcaneQuest] = []
        self._init_quest()

        # ── Animation state ──────────────────────────────────────────
        self.anim_time = 0.0
        self.particles: list[_Particle] = []
        self.burst_particles: list[_Particle] = []
        self.star_particles: list[_Particle] = []
        self._init_particles()

        self.entrance_progress = 0.0
        self.entrance_active = True
        self.entrance_start = time.time()

        # A tiny ambient flicker used to make the UI feel alive
        self.flicker_t = 0.0
        self._layout_size: tuple[int, int] | None = None

        # Reward banner flash (when claim is performed)
        self.claim_flash_alpha = 0.0
        self.claim_flash_time = 0.0

        # Layout rects (computed in _recalc_layout)
        self.panel_rect = pygame.Rect(0, 0, 0, 0)
        self.title_rect = pygame.Rect(0, 0, 0, 0)
        self.quest_card_rect = pygame.Rect(0, 0, 0, 0)
        self.reward_rect = pygame.Rect(0, 0, 0, 0)
        self.progress_rect = pygame.Rect(0, 0, 0, 0)

    # ── Quest setup ───────────────────────────────────────────────────
    def _init_quest(self):
        """Create the template quest: 'Kill X mobs in Y'.

        Leaves room for expansion by using a list (self.quests).
        """
        # ── Template quest ──
        template = ArcaneQuest(
            quest_id="kill_mobs_in_dark_forest",
            title=_("Whispers of the Dark Forest"),
            description=_("Kill {X} mobs in {Y}").format(X="10", Y="the Dark Forest"),
            target_type="mobs",
            target_count=10,
            location_label=_("the Dark Forest"),
            reward={"xp": 250, "gold": 75, "item": "Arcane Token"},
        )
        self.quests = [template]
        self.quest = template  # currently displayed (kept for backwards-compat lookups)

    def _init_particles(self):
        """Seed the ambient magical particles."""
        rng = random.Random(1337)
        self.particles.clear()
        self.star_particles.clear()

        for _ in range(60):
            x = rng.uniform(0, 1000)
            y = rng.uniform(0, 1000)
            vx = rng.uniform(-8, 8)
            vy = rng.uniform(-15, -3)
            life = rng.uniform(3.0, 7.0)
            color = rng.choice(
                [GOLD_BRIGHT, GOLD, PURPLE_BRIGHT, PURPLE, (180, 150, 255), (255, 230, 180)]
            )
            size = rng.uniform(1.0, 2.4)
            self.particles.append(
                _Particle(x, y, vx, vy, life, color, size, shape="dot")
            )

        for _ in range(20):
            x = rng.uniform(0, 1000)
            y = rng.uniform(0, 1000)
            vx = rng.uniform(-4, 4)
            vy = rng.uniform(-10, -2)
            life = rng.uniform(2.0, 5.0)
            color = rng.choice([GOLD_BRIGHT, PURPLE_BRIGHT, MAGIC_CYAN])
            size = rng.uniform(2.0, 3.5)
            self.star_particles.append(
                _Particle(x, y, vx, vy, life, color, size, shape="star")
            )

    # ── Layout ────────────────────────────────────────────────────────
    def _ensure_layout(self, screen_width: int, screen_height: int):
        if self._layout_size != (screen_width, screen_height):
            self._layout_size = (screen_width, screen_height)
            self._recalc_layout(screen_width, screen_height)

    def _recalc_layout(self, screen_width: int, screen_height: int):
        scale = cfg.ui_scale()

        # Main panel — centered, with size relative to the screen
        panel_w = min(960, max(640, int(720 * scale)))
        panel_h = min(640, max(440, int(520 * scale)))
        panel_x = (screen_width - panel_w) // 2
        panel_y = (screen_height - panel_h) // 2
        self.panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        # Title
        self.title_rect = pygame.Rect(
            self.panel_rect.x,
            self.panel_rect.y + int(18 * scale),
            self.panel_rect.width,
            int(60 * scale),
        )

        # Quest card (the main area for quest description / progress)
        card_pad = int(30 * scale)
        self.quest_card_rect = pygame.Rect(
            self.panel_rect.x + card_pad,
            self.title_rect.bottom + int(10 * scale),
            self.panel_rect.width - card_pad * 2,
            int(190 * scale),
        )

        # Progress bar
        self.progress_rect = pygame.Rect(
            self.quest_card_rect.x + int(20 * scale),
            self.quest_card_rect.bottom - int(46 * scale),
            self.quest_card_rect.width - int(40 * scale),
            int(22 * scale),
        )

        # Reward banner
        self.reward_rect = pygame.Rect(
            self.quest_card_rect.x,
            self.quest_card_rect.bottom + int(14 * scale),
            self.quest_card_rect.width,
            int(56 * scale),
        )

        # Buttons (bottom row of the panel)
        back_w = self.back_button.rect.width
        back_h = self.back_button.rect.height
        claim_w = self.claim_button.rect.width
        claim_h = self.claim_button.rect.height
        complete_w = self.complete_button.rect.width
        complete_h = self.complete_button.rect.height

        bottom_y = self.panel_rect.bottom - max(back_h, claim_h, complete_h) - int(18 * scale)

        # Back button: left
        self.back_button.rect.topleft = (
            self.panel_rect.x + int(18 * scale),
            bottom_y,
        )
        # Claim Reward: centered
        self.claim_button.rect.topleft = (
            self.panel_rect.centerx - claim_w // 2,
            bottom_y + (max(back_h, claim_h) - claim_h) // 2,
        )
        # Completed: right (visible only when quest is done)
        self.complete_button.rect.topleft = (
            self.panel_rect.right - complete_w - int(18 * scale),
            bottom_y + (max(back_h, complete_h) - complete_h) // 2,
        )

        # Re-render text surfaces for new sizes
        for btn in (self.back_button, self.claim_button, self.complete_button):
            try:
                btn._update_text_surface()
            except Exception:
                pass

    # ── State transitions ─────────────────────────────────────────────
    def on_enter(self):
        """Reset animations when the menu opens."""
        self.entrance_active = True
        self.entrance_start = time.time()
        self.entrance_progress = 0.0
        self.claim_flash_alpha = 0.0
        self._init_particles()

    def close_menu(self):
        self.app.manager.set_state("gameplay")

    # ── Quest interaction ─────────────────────────────────────────────
    def _current_quest(self) -> ArcaneQuest | None:
        return self.quest if self.quest else (self.quests[0] if self.quests else None)

    def claim_reward(self):
        """Player pressed 'Claim Reward' — give them their reward and reset the quest."""
        q = self._current_quest()
        if not q or not q.is_finished or q.claimed:
            return

        q.claimed = True
        q.completed = True
        q.progress = q.target_count

        # Reward banner flash
        self.claim_flash_alpha = 1.0
        self.claim_flash_time = 0.0

        # Give reward (best-effort, app may or may not have these)
        reward = q.reward
        try:
            if "gold" in reward and hasattr(self.app, "money"):
                self.app.money += int(reward["gold"])
        except Exception:
            pass
        try:
            if "xp" in reward and hasattr(self.app, "character"):
                # gameplay state owns the character
                gs = self.app.manager.states.get("gameplay")
                char = getattr(gs, "character", None) if gs else None
                if char and hasattr(char, "xp"):
                    char.xp += int(reward["xp"])
        except Exception:
            pass

        # Celebration bursts near the reward / claim button
        try:
            self._spawn_burst(self.claim_button.rect.centerx, self.claim_button.rect.centery, GOLD_BRIGHT, n=70)
            self._spawn_burst(self.reward_rect.centerx, self.reward_rect.centery, PURPLE_BRIGHT, n=70)
            # Big star burst
            for _ in range(30):
                ang = random.uniform(0, math.pi * 2)
                speed = random.uniform(80, 220)
                self.burst_particles.append(_Particle(
                    self.claim_button.rect.centerx, self.claim_button.rect.centery,
                    math.cos(ang) * speed, math.sin(ang) * speed,
                    random.uniform(0.6, 1.4), random.choice([GOLD_BRIGHT, PURPLE_BRIGHT, MAGIC_CYAN]),
                    random.uniform(2.0, 4.0), shape="star",
                ))
        except Exception:
            pass

    def _spawn_burst(self, x, y, color, n=40):
        for _ in range(n):
            ang = random.uniform(0, math.pi * 2)
            speed = random.uniform(60, 280)
            life = random.uniform(0.4, 1.2)
            sz = random.uniform(1.5, 3.5)
            self.burst_particles.append(
                _Particle(x, y, math.cos(ang) * speed, math.sin(ang) * speed, life, color, sz)
            )

    def _bump_quest_progress(self, amount=1):
        """Developer/test hook: increase quest progress (and maybe complete it)."""
        q = self._current_quest()
        if not q or q.claimed:
            return
        q.progress = min(q.target_count, q.progress + amount)
        if q.progress >= q.target_count:
            q.completed = True
            self._spawn_burst(
                self.progress_rect.centerx, self.progress_rect.centery, GOLD_BRIGHT, n=40
            )

    # ── Per-frame update ──────────────────────────────────────────────
    def update(self, dt=None):
        if dt is None:
            dt = 1.0 / 60.0
        self.anim_time += dt
        self.flicker_t += dt

        # Entrance progress (0..1 over ~0.6s)
        if self.entrance_active:
            t = (time.time() - self.entrance_start) / 0.6
            self.entrance_progress = max(0.0, min(1.0, t))
            if self.entrance_progress >= 1.0:
                self.entrance_active = False

        # Claim flash decay
        if self.claim_flash_alpha > 0.0:
            self.claim_flash_time += dt
            self.claim_flash_alpha = max(0.0, 1.0 - self.claim_flash_time / 1.0)

        sw, sh = (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        try:
            sw, sh = self.app.screen.get_size()
        except Exception:
            pass
        self._ensure_layout(sw, sh)

        # Update ambient particles (drift upward)
        alive = []
        for p in self.particles:
            p.update(dt)
            # Wrap around the visible area
            if p.x < 0: p.x = sw
            elif p.x > sw: p.x = 0
            if p.y < -10:
                p.y = sh + 10
                p.life = p.max_life  # respawn
            if p.alive:
                alive.append(p)
        self.particles = alive

        alive_stars = []
        for p in self.star_particles:
            p.update(dt)
            if p.x < 0: p.x = sw
            elif p.x > sw: p.x = 0
            if p.y < -10:
                p.y = sh + 10
                p.life = p.max_life
            if p.alive:
                alive_stars.append(p)
        self.star_particles = alive_stars

        # Burst particles
        self.burst_particles = [p for p in self.burst_particles if p.update(dt) is None and p.life > 0]
        # The comprehension above has a bug (update returns None); do an explicit loop:
        new_bursts = []
        for p in self.burst_particles:
            p.update(dt)
            if p.life > 0:
                new_bursts.append(p)
        self.burst_particles = new_bursts

    # ── Event handling ────────────────────────────────────────────────
    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_b):
                self.close_menu()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                # Dev hotkey: simulate killing one mob (advances progress)
                self._bump_quest_progress(1)

    # ── Drawing ───────────────────────────────────────────────────────
    def draw(self, screen):
        sw, sh = screen.get_size()
        self._ensure_layout(sw, sh)
        self.update()

        # Dim background (full screen) and draw magical backdrop
        self._draw_background(screen)

        # Entrance pop animation: panel scales 0.92 → 1.0 with a tiny slide
        t = self.entrance_progress
        ease = 1.0 - (1.0 - t) ** 3  # ease-out cubic

        panel = self.panel_rect
        # Panel scale (entrance)
        scale = 0.92 + 0.08 * ease
        scaled_w = int(panel.width * scale)
        scaled_h = int(panel.height * scale)
        scaled_rect = pygame.Rect(0, 0, scaled_w, scaled_h)
        scaled_rect.center = panel.center

        # Panel shadow (slightly offset, soft)
        self._draw_soft_shadow(screen, scaled_rect, offset=14, alpha=80)

        # Main panel
        self._draw_panel(screen, scaled_rect)

        # Title
        self._draw_title(screen, scaled_rect)

        # Quest card
        self._draw_quest_card(screen, scaled_rect)

        # Reward banner
        self._draw_reward_banner(screen, scaled_rect)

        # Buttons (positioned to the absolute layout, but only render inside the scaled panel)
        self._draw_claim_button(screen, scaled_rect)
        self._draw_complete_button(screen, scaled_rect)
        self._draw_back_button(screen, scaled_rect)

        # Ambient particles and bursts on top
        self._draw_ambient_particles(screen)
        self._draw_burst_particles(screen)
        self._draw_star_particles(screen)

    # ── Sub-draws ─────────────────────────────────────────────────────
    def _draw_background(self, screen):
        sw, sh = screen.get_size()
        # Full-screen dim layer
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        # Subtle radial glow behind the panel — gold/purple
        cx, cy = sw // 2, sh // 2
        max_r = int(min(sw, sh) * 0.7)
        for r in range(max_r, 0, -3):
            t = r / max_r
            a = int(20 * (1.0 - t) * (0.5 + 0.5 * math.sin(self.anim_time * 1.2)))
            c = (PURPLE[0], PURPLE[1], PURPLE[2], max(0, a))
            pygame.draw.circle(overlay, c, (cx, cy), r)
        screen.blit(overlay, (0, 0))

        # Faint background stars (subtle)
        rng = random.Random(7)
        for _ in range(80):
            x = rng.randint(0, sw - 1)
            y = rng.randint(0, sh - 1)
            tw = (math.sin(self.anim_time * 2.0 + x * 0.13) + 1.0) * 0.5
            a = int(40 + 60 * tw)
            color = random.choice([GOLD_BRIGHT, PURPLE_BRIGHT, MAGIC_CYAN, (200, 200, 255)])
            star_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(star_surf, (*color, a), (2, 2), 1)
            screen.blit(star_surf, (x, y))

    def _draw_soft_shadow(self, screen, rect, offset=10, alpha=70):
        # Layered offset rectangles for a soft shadow
        for i in range(4, 0, -1):
            sh_rect = rect.inflate(i * 4, i * 4)
            sh_surf = pygame.Surface(sh_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(sh_surf, (0, 0, 0, max(0, alpha - i * 12)),
                             sh_surf.get_rect(), border_radius=22)
            screen.blit(sh_surf, (sh_rect.x - offset // 2, sh_rect.y + offset // 2))

    def _draw_panel(self, screen, rect):
        # Outer gold border
        outer = rect.inflate(6, 6)
        pygame.draw.rect(screen, GOLD_DARK, outer, border_radius=22)
        # Inner purple border
        pygame.draw.rect(screen, PURPLE, rect.inflate(3, 3), width=2, border_radius=20)
        # Panel background (deep black-purple)
        pygame.draw.rect(screen, BLACK_PANEL, rect, border_radius=18)
        # Inner gold hairline
        pygame.draw.rect(screen, GOLD_DEEP, rect.inflate(-6, -6), width=1, border_radius=14)

        # Subtle vertical gradient inside
        grad = pygame.Surface(rect.size, pygame.SRCALPHA)
        for y in range(rect.height):
            t = y / max(1, rect.height - 1)
            a = int(20 * t)
            pygame.draw.line(grad, (PURPLE_DEEP[0], PURPLE_DEEP[1], PURPLE_DEEP[2], a),
                             (0, y), (rect.width, y))
        # Clip gradient to the panel
        clip = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(clip, (255, 255, 255, 255), clip.get_rect(), border_radius=18)
        grad.blit(clip, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(grad, rect.topleft)

        # Decorative corner gems
        gem_size = 8
        for cx, cy in [
            (rect.x + 14, rect.y + 14),
            (rect.right - 14, rect.y + 14),
            (rect.x + 14, rect.bottom - 14),
            (rect.right - 14, rect.bottom - 14),
        ]:
            lighter = tuple(min(255, c + 60) for c in PURPLE)
            darker = tuple(max(0, c - 40) for c in PURPLE)
            pts = [(cx, cy - gem_size), (cx - gem_size, cy), (cx + gem_size, cy)]
            pygame.draw.polygon(screen, lighter, pts)
            pts = [(cx - gem_size, cy), (cx + gem_size, cy), (cx, cy + gem_size)]
            pygame.draw.polygon(screen, darker, pts)
            pygame.draw.circle(screen, GOLD_BRIGHT, (cx - 2, cy - 2), 2)

    def _draw_title(self, screen, panel_rect):
        cx = panel_rect.centerx
        title_y = panel_rect.y + 22
        # Title text
        title_surf = self.title_font.render(_("ARCANE QUESTS"), True, GOLD_BRIGHT)
        shadow_surf = self.title_font.render(_("ARCANE QUESTS"), True, (0, 0, 0))
        # Glow under the text
        glow = pygame.Surface((title_surf.get_width() + 60, title_surf.get_height() + 30), pygame.SRCALPHA)
        pulse = (math.sin(self.anim_time * 2.0) + 1.0) * 0.5
        glow_alpha = int(60 + 50 * pulse)
        glow.fill((*PURPLE_BRIGHT, glow_alpha))
        # Soften center for a nicer falloff
        inner = pygame.Rect(20, 10, title_surf.get_width() + 20, title_surf.get_height() + 10)
        pygame.draw.rect(glow, (0, 0, 0, 0), inner)
        screen.blit(glow, (cx - glow.get_width() // 2, title_y - 10))
        screen.blit(shadow_surf, (cx - title_surf.get_width() // 2 + 2, title_y + 2))
        screen.blit(title_surf, (cx - title_surf.get_width() // 2, title_y))

        # Decorative line under the title
        line_y = title_y + title_surf.get_height() + 6
        line_w = int(panel_rect.width * 0.6)
        line_x = cx - line_w // 2
        for i in range(line_w):
            t = abs(i - line_w / 2) / (line_w / 2)
            a = int(200 * (1.0 - t))
            if i % 2 == 0:
                pygame.draw.line(screen, (*GOLD_BRIGHT, a), (line_x + i, line_y),
                                 (line_x + i, line_y), 1)
        # Diamond ends
        for dx in [line_x - 4, line_x + line_w + 4]:
            dsz = 5
            dpts = [(dx, line_y - dsz), (dx + dsz, line_y),
                    (dx, line_y + dsz), (dx - dsz, line_y)]
            pygame.draw.polygon(screen, GOLD, dpts)

    def _draw_quest_card(self, screen, panel_rect):
        q = self._current_quest()
        if not q:
            return

        r = self.quest_card_rect.copy()
        r.clamp_ip(panel_rect)
        # Outer purple border
        pygame.draw.rect(screen, PURPLE_DARK, r, border_radius=12)
        # Inner black panel
        inner = r.inflate(-4, -4)
        pygame.draw.rect(screen, (15, 8, 25, 240), inner, border_radius=10)
        # Gold hairline
        pygame.draw.rect(screen, GOLD_DEEP, inner.inflate(-3, -3), width=1, border_radius=8)

        # Quest title
        title_surf = self.section_font.render(q.title, True, GOLD_BRIGHT)
        screen.blit(title_surf, (r.x + 16, r.y + 12))

        # Description (uses the "Kill X mobs in Y" template)
        desc_surf = self.body_font.render(q.description, True, WHITE_SOFT)
        screen.blit(desc_surf, (r.x + 16, r.y + 12 + title_surf.get_height() + 6))

        # Progress label
        prog_label = _("Progress: {cur}/{max}").format(cur=q.progress, max=q.target_count)
        prog_label_surf = self.small_font.render(prog_label, True, PURPLE_BRIGHT)
        screen.blit(prog_label_surf, (r.x + 16, self.progress_rect.y - 22))

        # Progress bar
        frac = q.progress_fraction()
        self._draw_progress_bar(screen, self.progress_rect, frac, glowing=q.is_finished)

    def _draw_progress_bar(self, screen, rect, frac, glowing=False):
        # Background
        pygame.draw.rect(screen, (8, 4, 18), rect, border_radius=rect.height // 2)
        # Inner shadow
        inner = rect.inflate(-2, -2)
        pygame.draw.rect(screen, (20, 10, 32), inner, border_radius=inner.height // 2)
        # Fill
        fill_w = max(0, int(rect.width * frac))
        if fill_w > 0:
            fill_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
            # Gradient gold/purple
            for x in range(fill_w):
                t = x / max(1, fill_w - 1)
                r = int(GOLD[0] * (1 - t) + PURPLE_BRIGHT[0] * t)
                g = int(GOLD[1] * (1 - t) + PURPLE_BRIGHT[1] * t)
                b = int(GOLD[2] * (1 - t) + PURPLE_BRIGHT[2] * t)
                pygame.draw.line(screen, (r, g, b), (rect.x + x, rect.y + 2),
                                 (rect.x + x, rect.bottom - 3))
            # Shimmer band
            shimmer_x = int((self.anim_time * 60) % (fill_w + 60)) - 30
            for sx in range(max(0, shimmer_x), min(fill_w, shimmer_x + 30)):
                a = int(120 * (1 - abs(sx - shimmer_x - 15) / 15))
                if a > 0:
                    pygame.draw.line(screen, (255, 240, 200, a),
                                     (rect.x + sx, rect.y + 2),
                                     (rect.x + sx, rect.bottom - 3))

        # Rounded mask
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(),
                         border_radius=rect.height // 2)
        screen.blit(mask, rect.topleft, special_flags=pygame.BLEND_RGBA_MULT)
        # Outer hairline
        pygame.draw.rect(screen, GOLD_DEEP, rect, width=1, border_radius=rect.height // 2)
        # Glow when complete
        if glowing:
            pulse = (math.sin(self.anim_time * 4.0) + 1.0) * 0.5
            glow = pygame.Surface(rect.size, pygame.SRCALPHA)
            ga = int(80 + 80 * pulse)
            pygame.draw.rect(glow, (*GOLD_BRIGHT, ga), glow.get_rect(),
                             width=2, border_radius=rect.height // 2)
            screen.blit(glow, rect.topleft)

    def _draw_reward_banner(self, screen, panel_rect):
        q = self._current_quest()
        if not q:
            return
        r = self.reward_rect.copy()
        r.clamp_ip(panel_rect)
        # Backing
        pygame.draw.rect(screen, PURPLE_DARK, r, border_radius=10)
        inner = r.inflate(-3, -3)
        pygame.draw.rect(screen, (25, 12, 40, 240), inner, border_radius=8)
        pygame.draw.rect(screen, GOLD_DEEP, inner, width=1, border_radius=8)

        # Reward label
        reward_parts = []
        if "xp" in q.reward:
            reward_parts.append(f"{q.reward['xp']} XP")
        if "gold" in q.reward:
            reward_parts.append(f"{q.reward['gold']} G")
        if "item" in q.reward:
            reward_parts.append(str(q.reward['item']))
        reward_text = _("Reward: ") + ", ".join(reward_parts) if reward_parts else _("Reward: —")
        reward_surf = self.reward_font.render(reward_text, True, GOLD_BRIGHT)
        screen.blit(reward_surf, (r.x + 14, r.centery - reward_surf.get_height() // 2))

        # Sparkle next to the reward text (right side)
        for i in range(3):
            sx = r.right - 22 - i * 14
            sy = r.centery + int(math.sin(self.anim_time * 3.0 + i) * 4)
            self._draw_star(screen, sx, sy, 3 + (i % 2), PURPLE_BRIGHT, self.anim_time + i * 0.7)

        # Claim flash overlay
        if self.claim_flash_alpha > 0.0:
            flash = pygame.Surface(r.size, pygame.SRCALPHA)
            a = int(180 * self.claim_flash_alpha)
            pygame.draw.rect(flash, (*GOLD_BRIGHT, a), flash.get_rect(), border_radius=8)
            screen.blit(flash, r.topleft)

    def _draw_back_button(self, screen, panel_rect):
        btn = self.back_button
        if not panel_rect.colliderect(btn.rect):
            return
        btn.draw(screen)

    def _draw_complete_button(self, screen, panel_rect):
        q = self._current_quest()
        if not q or not q.is_finished:
            return
        btn = self.complete_button
        if not panel_rect.colliderect(btn.rect):
            return
        # Magical glow behind the completed button
        glow_surf = pygame.Surface((btn.rect.width + 30, btn.rect.height + 30), pygame.SRCALPHA)
        pulse = (math.sin(self.anim_time * 3.0) + 1.0) * 0.5
        a = int(60 + 60 * pulse)
        pygame.draw.rect(glow_surf, (*PURPLE_BRIGHT, a), glow_surf.get_rect(),
                         border_radius=14)
        screen.blit(glow_surf, (btn.rect.x - 15, btn.rect.y - 15))
        # Gold border
        border_rect = btn.rect.inflate(4, 4)
        pygame.draw.rect(screen, GOLD_BRIGHT, border_rect, width=2, border_radius=10)
        btn.draw(screen)

    def _draw_claim_button(self, screen, panel_rect):
        btn = self.claim_button
        if not panel_rect.colliderect(btn.rect):
            return
        q = self._current_quest()
        ready = bool(q and q.is_finished and not q.claimed)
        hover = btn.rect.collidepoint(pygame.mouse.get_pos())

        if ready:
            # Magical mode: gold/purple aura, breathing glow, animated border
            # Big radial aura behind
            aura_size = int(btn.rect.width * 1.5)
            aura_surf = pygame.Surface((aura_size, aura_size), pygame.SRCALPHA)
            pulse = (math.sin(self.anim_time * 3.0) + 1.0) * 0.5
            a = int(70 + 60 * pulse)
            for r in range(aura_size // 2, 0, -3):
                t = r / (aura_size // 2)
                col = (
                    int(GOLD_BRIGHT[0] * (1 - t) + PURPLE_BRIGHT[0] * t),
                    int(GOLD_BRIGHT[1] * (1 - t) + PURPLE_BRIGHT[1] * t),
                    int(GOLD_BRIGHT[2] * (1 - t) + PURPLE_BRIGHT[2] * t),
                    max(0, int(a * (1 - t))),
                )
                pygame.draw.circle(aura_surf, col, (aura_size // 2, aura_size // 2), r)
            screen.blit(
                aura_surf,
                (btn.rect.centerx - aura_size // 2, btn.rect.centery - aura_size // 2),
            )

            # Background (gradient gold→purple)
            grad = pygame.Surface(btn.rect.size, pygame.SRCALPHA)
            for x in range(btn.rect.width):
                t = x / max(1, btn.rect.width - 1)
                r = int(GOLD_DEEP[0] * (1 - t) + PURPLE_DEEP[0] * t)
                g = int(GOLD_DEEP[1] * (1 - t) + PURPLE_DEEP[1] * t)
                b = int(GOLD_DEEP[2] * (1 - t) + PURPLE_DEEP[2] * t)
                pygame.draw.line(grad, (r, g, b), (x, 0), (x, btn.rect.height))
            mask = pygame.Surface(btn.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=12)
            grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(grad, btn.rect.topleft)

            # Triple gold-purple border
            for fi in range(3):
                w = 2 - fi
                col = [GOLD_BRIGHT, GOLD, PURPLE][fi]
                br = btn.rect.inflate(fi * 2, fi * 2)
                pygame.draw.rect(screen, col, br, width=max(1, w), border_radius=12 + fi)

            # Animated shimmer sweep
            sweep_w = 60
            sweep_x = int((self.anim_time * 80) % (btn.rect.width + sweep_w)) - sweep_w
            if 0 < sweep_x < btn.rect.width:
                for sx in range(sweep_w):
                    t = sx / sweep_w
                    a = int(120 * math.sin(t * math.pi))
                    if a > 0:
                        px = btn.rect.x + sweep_x + sx
                        if 0 <= px < btn.rect.right:
                            pygame.draw.line(
                                screen, (*GOLD_BRIGHT, a),
                                (px, btn.rect.y + 2), (px, btn.rect.bottom - 3), 1,
                            )

            # Star sparkles
            for i in range(5):
                sx = btn.rect.x + int(btn.rect.width * (0.1 + 0.2 * i))
                sy = btn.rect.y + 8 + int(math.sin(self.anim_time * 2.0 + i * 1.3) * 3)
                self._draw_star(screen, sx, sy, 3, GOLD_BRIGHT, self.anim_time + i * 0.4)

            # Text (rendered over the gradient)
            text_surf = btn.font.render(btn.text, True, (255, 255, 240))
            shadow = btn.font.render(btn.text, True, (0, 0, 0))
            text_rect = text_surf.get_rect(center=btn.rect.center)
            shadow_rect = shadow.get_rect(center=(btn.rect.centerx + 1, btn.rect.centery + 1))
            # Subtle glow under the text
            tg = pygame.Surface((text_surf.get_width() + 16, text_surf.get_height() + 12), pygame.SRCALPHA)
            tg.fill((*PURPLE_BRIGHT, 80))
            inner = pygame.Rect(4, 4, text_surf.get_width() + 8, text_surf.get_height() + 4)
            pygame.draw.rect(tg, (0, 0, 0, 0), inner)
            screen.blit(tg, (text_rect.x - 8, text_rect.y - 6))
            screen.blit(shadow, shadow_rect)
            screen.blit(text_surf, text_rect)
        else:
            # Locked / not-yet-finished: gray and dimmed, but still drawn
            # Dim the existing button to make the difference clear
            saved_color = btn.color
            saved_hover = btn.hover_color
            btn.color = (55, 55, 60)
            btn.hover_color = (75, 75, 80)
            try:
                btn.draw(screen)
            except Exception:
                pass
            btn.color = saved_color
            btn.hover_color = saved_hover

            # Overlay a small lock icon
            lock_cx = btn.rect.x + 18
            lock_cy = btn.rect.centery
            pygame.draw.circle(screen, (150, 150, 160), (lock_cx, lock_cy - 2), 6)
            pygame.draw.rect(screen, (150, 150, 160),
                             (lock_cx - 7, lock_cy - 1, 14, 10), border_radius=2)
            pygame.draw.circle(screen, (90, 90, 100), (lock_cx, lock_cy + 2), 2)

    def _draw_star(self, screen, x, y, size, color, t):
        # 4-point sparkle star
        pulse = (math.sin(t * 4.0) + 1.0) * 0.5
        s = max(1, int(size * (0.8 + 0.4 * pulse)))
        glow_size = s * 3
        glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, int(80 * (0.4 + 0.6 * pulse))),
                           (glow_size, glow_size), glow_size)
        screen.blit(glow, (x - glow_size, y - glow_size))
        # 4-point star
        pts = [(x, y - s), (x + s, y), (x, y + s), (x - s, y)]
        pygame.draw.polygon(screen, color, pts)
        pts = [(x - s, y), (x, y - s), (x + s, y), (x, y + s)]
        # White core
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
