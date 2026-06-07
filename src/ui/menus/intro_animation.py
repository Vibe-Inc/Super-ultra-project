"""
Intro Animation State — "The Awakening"

A multi-phase full-screen cinematic that plays once when the player starts
a new game.  After the sequence finishes (or is skipped), the state
transitions to the gameplay state.

Phases
------
0  BLACK  — 1.0 s  — pure black hold
1  RUNES  — 2.5 s  — ancient rune symbols fade in from darkness, pulse
2  VOICE1 — 3.0 s  — "Arise, Chosen One." typewriter + Voice echo effect
3  VOICE2 — 3.5 s  — "I sense the latent magic…" typewriter
4  VOICE3 — 4.0 s  — "Far to the east…" typewriter
5  BURST  — 2.0 s  — full golden shockwave / particle eruption
6  FADE   — 1.5 s  — fade to black → switch to gameplay
"""

import math
import random
import pygame
from typing import TYPE_CHECKING

import src.config as cfg
from src.ui.effects import (
    GOLD, GOLD_BRIGHT, GOLD_DARK,
    ease_out_cubic, ease_out_elastic, ease_out_back,
    Star, AmbientEmber, LaunchBurst,
)
from src.core.logger import logger

if TYPE_CHECKING:
    from src.app import App


# ─── Palette ──────────────────────────────────────────────────────────────────
VOID       = (4,  3,  10)
DEEP_BLUE  = (8,  10, 28)
MYSTIC     = (100, 60, 220)
VOICE_CLR  = (210, 195, 255)   # soft lavender — the entity's text
GOLD_TEXT  = (255, 215, 80)
WHITE_GLOW = (220, 230, 255)

# Phase durations (seconds) — voice phases are minimum durations;
# they extend until typewriter is done + a hold period.
_PHASE_DUR = [
    1.0,   # 0: black hold
    2.5,   # 1: runes fade in
    2.0,   # 2: voice line 1 (min; extends until typed + hold)
    2.0,   # 3: voice line 2 (min; extends until typed + hold)
    2.0,   # 4: voice line 3 (min; extends until typed + hold)
    3.0,   # 5: burst
    1.8,   # 6: fade out
]

# After the typewriter finishes, hold for this many seconds before advancing.
_VOICE_HOLD = 1.5

_VOICE_LINES = [
    '"Arise, Chosen One."',
    '"I sense the latent magic humming in your blood.\nYou have been selected for a sacred mission."',
    '"Far to the east, a Chronos slumbers in \na mountain cave. You must slay it, or the realm will collapse."',
]

# ─── Helper particle classes ───────────────────────────────────────────────────

class _RuneSymbol:
    """One glowing rune character drawn at a random screen position."""
    _CHARS = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"

    def __init__(self, sw, sh, font):
        self.char  = random.choice(self._CHARS)
        self.x     = random.uniform(sw * 0.05, sw * 0.95)
        self.y     = random.uniform(sh * 0.05, sh * 0.95)
        self.size  = random.uniform(0.5, 1.4)   # scale multiplier for pulse
        self.phase = random.uniform(0, 6.28)
        self.speed = random.uniform(0.4, 1.2)
        self.base_alpha = random.randint(30, 160)
        self.color = random.choice([GOLD, MYSTIC[:3], WHITE_GLOW])
        self._surf = font.render(self.char, True, self.color)

    def draw(self, screen, t, global_alpha):
        pulse = 0.5 + 0.5 * math.sin(t * self.speed + self.phase)
        a = int(self.base_alpha * pulse * global_alpha / 255)
        a = max(0, min(255, a))
        if a < 4:
            return
        scale = self.size * (0.85 + 0.15 * pulse)
        w, h  = self._surf.get_size()
        nw    = max(1, int(w * scale))
        nh    = max(1, int(h * scale))
        scaled = pygame.transform.scale(self._surf, (nw, nh))
        scaled.set_alpha(a)
        screen.blit(scaled, (int(self.x - nw / 2), int(self.y - nh / 2)))


class _VoiceParticle:
    """A single drifting particle emitted from the screen centre during voice phases."""
    def __init__(self, sw, sh):
        angle  = random.uniform(0, 2 * math.pi)
        speed  = random.uniform(20, 110)
        self.x = sw / 2 + random.uniform(-30, 30)
        self.y = sh / 2 + random.uniform(-30, 30)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(10, 50)
        self.life = random.uniform(0.8, 2.5)
        self.max_life = self.life
        self.size = random.uniform(1.5, 4.5)
        self.color = random.choice([GOLD_BRIGHT, MYSTIC[:3], WHITE_GLOW, (180, 140, 255)])

    def update(self, dt):
        self.x  += self.vx * dt
        self.vx *= (1 - 1.5 * dt)
        self.y  += self.vy * dt
        self.vy *= (1 - 1.5 * dt)
        self.life -= dt

    def draw(self, screen):
        if self.life <= 0:
            return
        ratio = self.life / self.max_life
        a  = int(220 * ratio * ratio)
        sz = max(1, int(self.size * ratio))
        pygame.draw.circle(screen, (*self.color, a),
                           (int(self.x), int(self.y)), sz)


class _ShockwaveRing:
    """Expanding circle ring used in the burst phase."""
    def __init__(self, cx, cy, color, speed, max_radius, width=3, delay=0.0):
        self.cx = cx
        self.cy = cy
        self.color  = color
        self.speed  = speed
        self.radius = 0.0
        self.max_r  = max_radius
        self.width  = width
        self.delay  = delay
        self._alive = True

    @property
    def alive(self):
        return self._alive

    def update(self, dt):
        if self.delay > 0:
            self.delay -= dt
            return
        self.radius += self.speed * dt
        if self.radius >= self.max_r:
            self._alive = False

    def draw(self, screen):
        if self.delay > 0:
            return
        ratio = 1.0 - self.radius / self.max_r
        a = int(220 * ratio * ratio)
        r = int(self.radius)
        if r < 2 or a < 4:
            return
        pygame.draw.circle(screen, (*self.color, a),
                           (int(self.cx), int(self.cy)), r, self.width)


class _LightRay:
    """A drifting ray of warm light across the screen."""
    def __init__(self, sw, sh):
        self.sw = sw
        self.sh = sh
        self._reset()

    def _reset(self):
        self.y = random.uniform(0, self.sh)
        self.height = random.uniform(15, 50)
        self.speed = random.uniform(0.1, 0.3)
        self.phase = random.uniform(0, 6.28)
        self.amp = random.uniform(15, 40)
        self.alpha = random.randint(3, 10)
        self.width_factor = random.uniform(0.3, 0.7)

    def draw(self, surf, t):
        cy = self.y + math.sin(t * self.speed + self.phase) * self.amp
        h = self.height
        w = int(self.sw * self.width_factor)
        s = pygame.Surface((w, int(h)), pygame.SRCALPHA)
        for i in range(int(h)):
            ratio = 1.0 - abs(i - h / 2) / (h / 2)
            a = int(self.alpha * max(0, ratio) ** 2)
            if a < 1:
                continue
            c = (255, 230, 180, min(255, a))
            pygame.draw.line(s, c, (0, i), (w, i))
        sx = int(self.sw * (1 - self.width_factor) * 0.5)
        surf.blit(s, (sx, int(cy - h / 2)))


class _OrbGlowRing:
    """A glowing ring orbiting the centre orb."""
    def __init__(self, cx, cy, radius, speed, color, width=1):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.speed = speed
        self.color = color
        self.width = width
        self.angle = random.uniform(0, 2 * math.pi)
        self.throb = random.uniform(0, 6.28)

    def draw(self, surf, t):
        self.angle += self.speed * 0.02
        ox = self.cx + int(math.cos(self.angle) * self.radius)
        oy = self.cy + int(math.sin(self.angle) * self.radius)
        pulse = 0.7 + 0.3 * math.sin(t * 2.0 + self.throb)
        a = int(80 * pulse)
        r = max(1, int(2 * pulse))
        pygame.draw.circle(surf, (*self.color, max(0, min(150, a))),
                           (ox, oy), r)


class _LensFlare:
    """A simple lens flare effect for the burst."""
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.life = 1.0
        self.max_life = 0.6

    def update(self, dt):
        self.life -= dt / self.max_life

    def draw(self, surf):
        if self.life <= 0:
            return
        a = int(200 * self.life * self.life)
        r = int(50 * (1.0 - self.life))
        # Halo — draw directly on surf
        for ri in range(r * 4, 0, -r):
            ratio = ri / (r * 4)
            ca = int(a * (1 - ratio) * 0.3)
            if ca < 2:
                continue
            pygame.draw.circle(surf, (255, 220, 150, max(0, min(180, ca))),
                               (int(self.cx), int(self.cy)), ri)
        # Star flare lines
        for angle in [0, math.pi / 4, math.pi / 2, 3 * math.pi / 4]:
            length = int(r * 2.5 * self.life)
            ex = self.cx + int(math.cos(angle) * length)
            ey = self.cy + int(math.sin(angle) * length)
            pygame.draw.line(surf, (255, 220, 150, max(0, min(180, a))),
                             (self.cx, self.cy), (ex, ey), max(1, int(2 * self.life)))


class _TitleSparkle:
    """A sparkle particle emitted from the title text."""
    def __init__(self, x, y):
        self.x = x + random.uniform(-5, 5)
        self.y = y + random.uniform(-5, 5)
        self.vx = random.uniform(-10, 10)
        self.vy = random.uniform(-25, -5)
        self.life = 1.0
        self.max_life = random.uniform(0.3, 1.0)
        self.size = random.uniform(1, 3)
        angle = random.uniform(0, 6.28)
        self.color = (255, max(0, min(255, int(200 + 55 * math.sin(angle)))),
                      max(0, min(255, int(140 + 80 * math.cos(angle)))))

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 15 * dt
        self.life -= dt / self.max_life

    def draw(self, surf):
        if self.life <= 0:
            return
        a = int(255 * self.life)
        sz = max(0.5, self.size * self.life)
        pygame.draw.circle(surf, (*self.color, max(0, min(255, a))),
                           (int(self.x), int(self.y)), int(sz))


# ─── Main state ───────────────────────────────────────────────────────────────

class IntroAnimation:
    """
    Full-screen cinematic intro that plays once when the player starts the game.
    """

    def __init__(self, app: "App"):
        self.app = app
        self._phase   = 0
        self._phase_t = 0.0
        self._t       = 0.0
        self._done    = False
        self._skip_requested = False

        # Particle lists
        self._runes:      list[_RuneSymbol]    = []
        self._v_parts:    list[_VoiceParticle] = []
        self._bursts:     list[LaunchBurst]    = []
        self._shockwaves: list[_ShockwaveRing] = []
        self._embers:     list[AmbientEmber]   = []
        self._stars:      list[Star]           = []
        self._light_rays: list[_LightRay]      = []
        self._orb_rings:  list[_OrbGlowRing]   = []
        self._lens_flare: _LensFlare | None    = None
        self._title_sparkles: list[_TitleSparkle] = []

        # Typewriter state per voice line
        self._tw_chars   = [0.0, 0.0, 0.0]   # fractional char count shown
        self._tw_speed   = 22.0               # chars per second
        self._tw_hold    = [0.0, 0.0, 0.0]   # hold-timer after line finishes

        # Fonts
        self._font_voice = cfg.get_font(max(14, int(26 * cfg.ui_scale())))
        self._font_rune  = cfg.get_font(max(16, int(36 * cfg.ui_scale())))
        self._font_skip  = cfg.get_font(max(10, int(16 * cfg.ui_scale())))
        self._font_arise = cfg.get_font(max(22, int(52 * cfg.ui_scale())))

        # Cache
        self._bg = None
        self._skip_surf = None
        self._flash_alpha = 0.0
        self._vignette_alpha = 0.0
        self._burst_timer = 0.0
        self._cached_sw = 0
        self._cached_sh = 0
        self._star_surf = None
        self._ray_surf = None
        self._ember_surf = None
        self._vp_surf = None
        self._ring_surf = None
        self._fx_surf = None
        self._flare_surf = None
        self._sp_surf = None
        self._flash_surf = None
        self._vig_cache_sw = 0
        self._vig_cache_sh = 0
        self._vig_base = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self):
        """Reset everything so the intro is fresh each time."""
        self._phase   = 0
        self._phase_t = 0.0
        self._t       = 0.0
        self._done    = False
        self._skip_requested = False
        self._flash_alpha = 0.0
        self._vignette_alpha = 0.0
        self._burst_timer = 0.0
        self._lens_flare = None

        sw, sh = self._sw(), self._sh()

        self._runes = [_RuneSymbol(sw, sh, self._font_rune) for _ in range(70)]
        self._embers = [AmbientEmber(sw, sh) for _ in range(30)]
        self._stars  = [Star(sw, sh) for _ in range(200)]
        self._light_rays = [_LightRay(sw, sh) for _ in range(8)]
        self._orb_rings = [
            _OrbGlowRing(sw // 2, sh // 2, int(min(sw, sh) * 0.08 * f), 0.5 + i * 0.3,
                         random.choice([GOLD_BRIGHT, MYSTIC[:3], WHITE_GLOW]), max(1, 3 - i))
            for i, f in enumerate([1.0, 1.6, 2.3, 3.0])
        ]
        self._v_parts    = []
        self._bursts     = []
        self._shockwaves = []
        self._title_sparkles = []
        self._tw_chars   = [0.0, 0.0, 0.0]
        self._tw_hold    = [0.0, 0.0, 0.0]

        # Pre-render skip hint
        self._skip_surf = self._font_skip.render(
            "SPACE / ENTER — skip", True, (160, 150, 130))

        logger.info("[IntroAnimation] Sequence started.")

    def _sw(self): return self.app.screen.get_width()
    def _sh(self): return self.app.screen.get_height()

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                self._skip_requested = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._skip_requested = True

    # ── Update ─────────────────────────────────────────────────────────────────

    def update(self, dt):
        self._t       += dt
        self._phase_t += dt

        sw, sh = self._sw(), self._sh()
        cx, cy = sw // 2, sh // 2

        # Skip: jump straight to fade-out phase
        if self._skip_requested and self._phase < 6:
            self._phase   = 6
            self._phase_t = 0.0
            self._skip_requested = False

        # ── Done check BEFORE resetting phase_t ───────────────────────────────
        if self._phase == 6 and self._phase_t >= _PHASE_DUR[6]:
            if not self._done:
                self._done = True
                logger.info("[IntroAnimation] Sequence complete → switching to gameplay.")
                self.app.manager.set_state("gameplay")
            return

        # ── Typewriter update for current voice phase ─────────────────────────
        voice_phase = self._phase - 2   # 0,1,2 for phases 2,3,4
        if 0 <= voice_phase <= 2:
            line_len = len(_VOICE_LINES[voice_phase])
            self._tw_chars[voice_phase] = min(
                line_len,
                self._tw_chars[voice_phase] + self._tw_speed * dt
            )
            # Advance hold timer once the line is fully typed
            if self._tw_chars[voice_phase] >= line_len:
                self._tw_hold[voice_phase] += dt

        # ── Phase advancement ─────────────────────────────────────────────────
        ready_to_advance = False
        if self._phase in (2, 3, 4):   # voice phases: must type + hold
            vp = self._phase - 2
            typed_done = self._tw_chars[vp] >= len(_VOICE_LINES[vp])
            held_enough = self._tw_hold[vp] >= _VOICE_HOLD
            ready_to_advance = typed_done and held_enough
        else:
            ready_to_advance = self._phase_t >= _PHASE_DUR[self._phase]

        if ready_to_advance:
            self._phase_t = 0.0
            self._phase  += 1

            # Phase entry side-effects
            if self._phase == 5:   # burst eruption
                self._spawn_burst(cx, cy)

        # ── Vignette ─────────────────────────────────────────────────────────
        if 2 <= self._phase <= 4:
            self._vignette_alpha = min(80, self._vignette_alpha + dt * 15)
        elif self._phase == 5:
            self._vignette_alpha = 120
        else:
            self._vignette_alpha = max(0.0, self._vignette_alpha - dt * 30)

        # ── Particles ─────────────────────────────────────────────────────────
        for e in self._embers:
            e.update(dt, self._t)
        self._v_parts = [p for p in self._v_parts if p.life > 0]
        for p in self._v_parts:
            p.update(dt)

        # Spawn voice particles during voice & burst phases
        if 2 <= self._phase <= 5:
            rate = 4 if self._phase < 5 else 15
            for _ in range(rate):
                self._v_parts.append(_VoiceParticle(sw, sh))

        # Burst particles
        self._bursts = [b for b in self._bursts if b.lt > 0]
        for b in self._bursts:
            b.update(dt)

        # Shockwaves
        self._shockwaves = [w for w in self._shockwaves if w.alive]
        for w in self._shockwaves:
            w.update(dt)

        # Lens flare
        if self._lens_flare is not None:
            self._lens_flare.update(dt)
            if self._lens_flare.life <= 0:
                self._lens_flare = None

        # Title sparkles during burst
        if self._phase == 5:
            self._burst_timer += dt
            for _ in range(3):
                self._title_sparkles.append(
                    _TitleSparkle(cx + random.uniform(-200, 200),
                                  cy + random.uniform(-60, 60))
                )
        self._title_sparkles = [s for s in self._title_sparkles if s.life > 0]
        for s in self._title_sparkles:
            s.update(dt)

        # Flash alpha — always decays regardless of phase
        if self._flash_alpha > 0:
            self._flash_alpha = max(0.0, self._flash_alpha - dt * 220)

    def _spawn_burst(self, cx, cy):
        """Spawn the big particle eruption for phase 5."""
        self._flash_alpha = 200.0
        self._lens_flare = _LensFlare(cx, cy)

        # Shockwave rings — gold and white only (no purple)
        for i, (col, spd, wr) in enumerate([
            (WHITE_GLOW,     550, 1000),
            (GOLD_BRIGHT,   450, 850),
            (WHITE_GLOW,    350, 700),
            (GOLD,          280, 600),
            (GOLD_BRIGHT,   200, 480),
            ((255, 220, 120), 150, 380),
        ]):
            self._shockwaves.append(_ShockwaveRing(cx, cy, col, spd, wr,
                                                   width=max(2, 5 - i),
                                                   delay=i * 0.10))

        # Burst particles — warm gold and white only
        for _ in range(200):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 450)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(0, 80)
            col = random.choice([GOLD_BRIGHT, (255, 180, 60), WHITE_GLOW,
                                 (255, 220, 120), (255, 200, 80)])
            self._bursts.append(
                LaunchBurst(
                    cx + random.uniform(-20, 20),
                    cy + random.uniform(-20, 20),
                    vx, vy, col,
                    random.randint(2, 7),
                    random.uniform(0.5, 2.5)
                )
            )

    def _ensure_surfaces(self, sw, sh):
        if sw == self._cached_sw and sh == self._cached_sh:
            return
        self._cached_sw, self._cached_sh = sw, sh
        self._star_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._ray_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._ember_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._vp_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._ring_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._fx_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._flare_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._sp_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._flash_surf = pygame.Surface((sw, sh))
        self._ov_surf = pygame.Surface((sw, sh))

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, screen):
        self.update(self.app.clock.get_time() / 1000.0)
        sw, sh = screen.get_width(), screen.get_height()
        cx, cy = sw // 2, sh // 2
        t = self._t
        phase = self._phase
        pt = self._phase_t

        self._ensure_surfaces(sw, sh)

        # 1. Background ───────────────────────────────────────────────────────
        screen.fill(VOID)

        # Subtle nebula gradient
        self._draw_nebula(screen, sw, sh, t)

        # Stars (visible from phase 1 onwards)
        if phase >= 1:
            star_a = int(255 * min(1.0, pt / 1.5)) if phase == 1 else 255
            self._star_surf.fill((0, 0, 0, 0))
            for star in self._stars:
                star.draw(self._star_surf, t)
            self._star_surf.set_alpha(star_a)
            screen.blit(self._star_surf, (0, 0))

        # 2. Light rays (visible from phase 2 onwards) ────────────────────────
        if phase >= 2:
            self._ray_surf.fill((0, 0, 0, 0))
            for ray in self._light_rays:
                ray.draw(self._ray_surf, t)
            ray_a = 255
            if phase == 6:
                ray_a = int(255 * max(0.0, 1.0 - pt / _PHASE_DUR[6]))
            self._ray_surf.set_alpha(ray_a)
            screen.blit(self._ray_surf, (0, 0))

        # 3. Runes ────────────────────────────────────────────────────────────
        if phase >= 1:
            rune_global = int(255 * min(1.0, pt / 1.0)) if phase == 1 else 255
            if phase == 6:
                rune_global = int(255 * max(0.0, 1.0 - pt / _PHASE_DUR[6]))
            for rune in self._runes:
                rune.draw(screen, t, rune_global)

        # 4. Embers ───────────────────────────────────────────────────────────
        self._ember_surf.fill((0, 0, 0, 0))
        for e in self._embers:
            e.draw(self._ember_surf, t)
        if phase >= 2:
            screen.blit(self._ember_surf, (0, 0))

        # 5. Voice particles ──────────────────────────────────────────────────
        if self._v_parts:
            self._vp_surf.fill((0, 0, 0, 0))
            for p in self._v_parts:
                p.draw(self._vp_surf)
            screen.blit(self._vp_surf, (0, 0))

        # 6. Centre glow / orb ────────────────────────────────────────────────
        if phase >= 2:
            self._draw_centre_glow(screen, cx, cy, t, phase, pt)

        # 7. Orb glow rings ───────────────────────────────────────────────────
        if phase >= 2 and self._orb_rings:
            self._ring_surf.fill((0, 0, 0, 0))
            for ring in self._orb_rings:
                ring.draw(self._ring_surf, t)
            if phase == 6:
                ring_a = int(255 * max(0.0, 1.0 - pt / _PHASE_DUR[6]))
                self._ring_surf.set_alpha(ring_a)
            screen.blit(self._ring_surf, (0, 0))

        # 8. Voice lines ──────────────────────────────────────────────────────
        if 2 <= phase <= 4:
            line_idx = phase - 2
            self._draw_voice_line(screen, sw, sh, cx, cy, line_idx, t, pt, phase)

        # 9. "Arise, Chosen One" grand title (burst phase) ────────────────────
        if phase == 5:
            self._draw_arise_title(screen, sw, sh, cx, cy, pt)

        # 10. Title sparkles ──────────────────────────────────────────────────
        if self._title_sparkles:
            self._sp_surf.fill((0, 0, 0, 0))
            for s in self._title_sparkles:
                s.draw(self._sp_surf)
            screen.blit(self._sp_surf, (0, 0))

        # 11. Shockwaves & burst particles ─────────────────────────────────────
        if self._shockwaves or self._bursts:
            self._fx_surf.fill((0, 0, 0, 0))
            for w in self._shockwaves:
                w.draw(self._fx_surf)
            for b in self._bursts:
                b.draw(self._fx_surf)
            screen.blit(self._fx_surf, (0, 0))

        # 12. Lens flare ───────────────────────────────────────────────────────
        if self._lens_flare is not None:
            self._flare_surf.fill((0, 0, 0, 0))
            self._lens_flare.draw(self._flare_surf)
            screen.blit(self._flare_surf, (0, 0))

        # 13. Flash (burst entry) ──────────────────────────────────────────────
        if self._flash_alpha > 0:
            self._flash_surf.fill(WHITE_GLOW)
            self._flash_surf.set_alpha(int(self._flash_alpha))
            screen.blit(self._flash_surf, (0, 0))

        # 14. Vignette ─────────────────────────────────────────────────────────
        if self._vignette_alpha > 1:
            self._draw_vignette(screen, sw, sh)

        # 15. Fade overlays ────────────────────────────────────────────────────
        if phase == 0:
            screen.fill((0, 0, 0))
        elif phase == 1:
            fade_a = max(0, int(255 * (1.0 - ease_out_cubic(min(1.0, pt / 1.5)))))
            if fade_a > 0:
                self._ov_surf.fill((0, 0, 0))
                self._ov_surf.set_alpha(fade_a)
                screen.blit(self._ov_surf, (0, 0))
        elif phase == 6:
            fade_a = int(255 * ease_out_cubic(min(1.0, pt / _PHASE_DUR[6])))
            if fade_a > 0:
                self._ov_surf.fill((0, 0, 0))
                self._ov_surf.set_alpha(fade_a)
                screen.blit(self._ov_surf, (0, 0))

        # 16. Skip hint ────────────────────────────────────────────────────────
        if self._skip_surf and 1 <= phase <= 4:
            skip_a = int(130 * (0.5 + 0.5 * math.sin(t * 1.8)))
            self._skip_surf.set_alpha(max(0, min(200, skip_a)))
            screen.blit(
                self._skip_surf,
                (sw - self._skip_surf.get_width() - 20,
                 sh - self._skip_surf.get_height() - 16)
            )

    # ── Sub-draw helpers ──────────────────────────────────────────────────────

    def _draw_vignette(self, screen, sw, sh):
        """Darken the edges of the screen."""
        if not hasattr(self, '_vig_cache_sw') or self._vig_cache_sw != sw or self._vig_cache_sh != sh:
            self._vig_cache_sw, self._vig_cache_sh = sw, sh
            r = int(math.hypot(sw, sh) / 2)
            self._vig_base = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for radius in range(r, 0, -max(1, r // 30)):
                ratio = radius / r
                ca = int(200 * (1 - ratio) ** 2)
                if ca < 1:
                    continue
                pygame.draw.circle(self._vig_base, (0, 0, 0, max(0, min(255, ca))),
                                   (sw // 2, sh // 2), radius)
        v = self._vig_base.copy()
        v.set_alpha(min(255, int(self._vignette_alpha)))
        screen.blit(v, (0, 0))

    def _draw_nebula(self, screen, sw, sh, t):
        """Draw a gently pulsing coloured nebula in the background."""
        cx, cy = sw // 2, sh // 2
        phase_shift = t * 0.07
        for (rx, ry_off, r, col, base_a) in [
            (0.40, -0.12, 0.35, (40, 20, 100), 18),
            (0.60,  0.10, 0.30, (20, 40,  80), 14),
            (-0.05, 0.0,  0.25, (60, 30, 120), 10),
            (-0.25, 0.20, 0.20, (80, 40, 140), 8),
            (0.30, -0.25, 0.18, (30, 15, 90),  12),
        ]:
            ncx = int(cx + sw * rx * math.cos(phase_shift))
            ncy = int(cy + sh * ry_off + sh * 0.08 * math.sin(phase_shift * 1.3))
            nr  = int(min(sw, sh) * r)
            a   = int(base_a + 6 * math.sin(t * 0.3 + rx * 5))
            a   = max(0, min(30, a))
            ns  = pygame.Surface((nr * 2, nr * 2), pygame.SRCALPHA)
            pygame.draw.circle(ns, (*col, a), (nr, nr), nr)
            screen.blit(ns, (ncx - nr, ncy - nr))

    def _draw_centre_glow(self, screen, cx, cy, t, phase, pt):
        """Pulsing glow orb at the screen centre."""
        base_r = int(min(self._sw(), self._sh()) * 0.20)
        pulse  = 0.85 + 0.15 * math.sin(t * 1.4)
        if phase == 5:
            pulse = 1.2 + 0.3 * math.sin(t * 8.0)
        r      = int(base_r * pulse)
        a_mult = min(1.0, pt / 0.8) if phase == 2 else 1.0
        if phase == 6:
            a_mult = max(0.0, 1.0 - pt / _PHASE_DUR[6])

        ns = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for ri in range(r, 0, -3):
            ratio = ri / r
            base_a = int(50 * (1.0 - ratio) * a_mult)
            col = (
                max(0, min(255, int(80 + 160 * (1 - ratio)))),
                max(0, min(255, int(40 +  90 * (1 - ratio)))),
                max(0, min(255, int(180 + 70 * (1 - ratio)))),
                max(0, min(60, base_a))
            )
            pygame.draw.circle(ns, col, (r, r), ri)
        screen.blit(ns, (cx - r, cy - r))

    def _draw_voice_line(self, screen, sw, sh, cx, cy, line_idx, t, pt, phase):
        full_text = _VOICE_LINES[line_idx]
        shown_chars = int(self._tw_chars[line_idx])
        display = full_text[:shown_chars]

        lines = display.split("\n")

        lh = self._font_voice.get_height() + 4
        total_h = lh * len(lines)

        max_line_w = max((self._font_voice.size(ln)[0] for ln in full_text.split("\n")), default=1)
        pad_x, pad_y = int(50 * cfg.ui_scale()), int(24 * cfg.ui_scale())
        panel_w = min(max_line_w + pad_x * 2, sw - 80)
        panel_h = total_h + pad_y * 2 + int(40 * cfg.ui_scale())
        panel_x = cx - panel_w // 2
        panel_y = cy - panel_h // 2 + int(sh * 0.18)

        text_alpha = int(255 * min(1.0, pt / 0.4))

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)

        # Dark glass background with richer alpha
        pygame.draw.rect(panel_surf, (8, 5, 20, 200), (0, 0, panel_w, panel_h), border_radius=14)

        # Gold border — animated glow
        bord_a = int(170 + 70 * math.sin(t * 1.5))
        pygame.draw.rect(panel_surf, (*GOLD, max(0, min(255, bord_a))),
                         (0, 0, panel_w, panel_h), max(2, int(2 * cfg.ui_scale())), border_radius=14)

        # Inner glow border
        in_a = int(60 + 30 * math.sin(t * 2.0 + 1.0))
        pygame.draw.rect(panel_surf, (*GOLD_BRIGHT, max(0, min(80, in_a))),
                         (3, 3, panel_w - 6, panel_h - 6), 1, border_radius=12)

        # Corner ornaments
        corner_size = int(16 * cfg.ui_scale())
        for (cx_off, cy_off, flip_x, flip_y) in [
            (6, 6, 1, 1), (panel_w - 6 - corner_size, 6, -1, 1),
            (6, panel_h - 6 - corner_size, 1, -1),
            (panel_w - 6 - corner_size, panel_h - 6 - corner_size, -1, -1),
        ]:
            c_surf = pygame.Surface((corner_size, corner_size), pygame.SRCALPHA)
            pts = [(0, corner_size), (0, 0), (corner_size, 0)]
            ca = int(120 + 60 * math.sin(t * 1.2 + cx_off))
            pygame.draw.lines(c_surf, (*GOLD_BRIGHT, max(0, min(200, ca))), False, pts, 2)
            if flip_x < 0:
                c_surf = pygame.transform.flip(c_surf, True, False)
            if flip_y < 0:
                c_surf = pygame.transform.flip(c_surf, False, True)
            panel_surf.blit(c_surf, (cx_off, cy_off))

        # Top accent bar
        bar_w = panel_w - 40
        bar_surf = pygame.Surface((bar_w, 2), pygame.SRCALPHA)
        for bx in range(bar_w):
            ratio = 1.0 - abs(bx / bar_w - 0.5) * 2
            ba = int(220 * ratio * ratio)
            bar_surf.set_at((bx, 0), (*GOLD_BRIGHT, max(0, min(255, ba))))
        panel_surf.blit(bar_surf, (20, 6))

        # Entity tag
        tag_font = cfg.get_font(max(9, int(14 * cfg.ui_scale())))
        tag = tag_font.render("⟨ THE VOICE ⟩", True, (*GOLD, 200))
        panel_surf.blit(tag, (panel_w // 2 - tag.get_width() // 2, 10))

        # Text lines with shimmer
        ty = pad_y + int(22 * cfg.ui_scale())
        for ln in lines:
            if not ln:
                ty += lh
                continue
            txt_surf = self._font_voice.render(ln, True, VOICE_CLR)
            shimmer_phase = (t * 80 + 0) % (txt_surf.get_width() + 40)
            sh_w = max(1, int(txt_surf.get_width() * 0.12))
            sh_band = pygame.Surface((sh_w, txt_surf.get_height()), pygame.SRCALPHA)
            for sx in range(sh_w):
                ratio = 1.0 - abs(sx - sh_w / 2) / (sh_w / 2 + 1)
                sa = int(70 * ratio)
                pygame.draw.line(sh_band, (*WHITE_GLOW, max(0, min(120, sa))),
                                 (sx, 0), (sx, txt_surf.get_height()))
            txt_surf.blit(sh_band, (int(shimmer_phase - sh_w), 0),
                          special_flags=pygame.BLEND_RGBA_ADD)

            panel_surf.blit(txt_surf, (panel_w // 2 - txt_surf.get_width() // 2, ty))
            ty += lh

        panel_surf.set_alpha(text_alpha)
        screen.blit(panel_surf, (panel_x, panel_y))

        # Cursor blink
        if shown_chars < len(full_text):
            if int(t * 3) % 2 == 0:
                cur_x = panel_x + panel_w // 2 + self._font_voice.size(lines[-1])[0] // 2 + 3
                cur_y = panel_y + pad_y + int(22 * cfg.ui_scale()) + (len(lines) - 1) * lh
                pygame.draw.rect(screen, (*GOLD_BRIGHT, 220),
                                 (cur_x, cur_y + 2, max(1, int(2 * cfg.ui_scale())), lh - 4))

    def _draw_arise_title(self, screen, sw, sh, cx, cy, pt):
        dur = _PHASE_DUR[5]
        t_local = min(1.0, pt / (dur * 0.6))

        text1 = "ARISE,"
        text2 = "CHOSEN ONE."

        def _render_word(text, base_y, delay_mult):
            chars = list(text)
            char_surfs = [self._font_arise.render(c, True, GOLD_BRIGHT) for c in chars]
            total_w = sum(s.get_width() for s in char_surfs)
            sx = cx - total_w // 2
            for i, (c, cs) in enumerate(zip(chars, char_surfs)):
                c_delay = delay_mult + i * 0.06
                c_t = max(0.0, min(1.0, (pt - c_delay) / 0.35))
                c_eased = ease_out_elastic(c_t)
                c_off_y = int((1 - c_eased) * 80)
                c_alpha = int(255 * c_eased)
                if c_alpha < 4:
                    sx += cs.get_width()
                    continue

                # Glow halo — richer
                if c_eased > 0.3:
                    glow_a = int(120 * c_eased * (0.6 + 0.4 * math.sin(self._t * 4 + i * 2)))
                    for dx, dy in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1),
                                   (-1, -1), (1, -1), (-1, 1), (1, 1)]:
                        glow_s = self._font_arise.render(c, True, (255, 200, 80))
                        glow_s.set_alpha(max(0, min(80, int(glow_a * 0.4))))
                        screen.blit(glow_s, (sx + dx - 1, base_y + c_off_y + dy - 1))

                cs.set_alpha(c_alpha)
                screen.blit(cs, (sx, base_y + c_off_y))
                sx += cs.get_width()

        lh = self._font_arise.get_height()
        _render_word(text1, cy - lh - int(8 * cfg.ui_scale()), 0.0)
        _render_word(text2, cy + int(8 * cfg.ui_scale()), 0.2)

        # Decorative horizontal line beneath
        line_t = max(0.0, min(1.0, (pt - 0.8) / 0.4))
        if line_t > 0:
            lw = int(sw * 0.60 * ease_out_cubic(line_t))
            lx = cx - lw // 2
            ly = cy + lh + int(16 * cfg.ui_scale())
            la = int(220 * line_t)
            pygame.draw.line(screen, (*GOLD, max(0, min(255, la))),
                             (lx, ly), (lx + lw, ly), max(2, int(3 * cfg.ui_scale())))
            pygame.draw.line(screen, (*GOLD_BRIGHT, max(0, min(255, la // 2))),
                             (lx, ly - 2), (lx + lw, ly - 2), 1)
            # Decorative dots on ends
            for dx in [lx, lx + lw]:
                pygame.draw.circle(screen, (*GOLD_BRIGHT, max(0, min(200, la))),
                                   (dx, ly), max(2, int(3 * cfg.ui_scale())))
