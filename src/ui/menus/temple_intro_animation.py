"""
Temple Intro Animation State — "The Approach"

A more dynamic multi-phase full-screen cinematic that plays once when the player
first travels to the temple location.

Phases
------
0  BLACK   — 0.5 s  — short black hold
1  RUMBLE  — 2.0 s  — screen shake, red/dark aura fading in
2  VOICE1  — 1.5 s  — "You're almost there." typewriter
3  VOICE2  — 1.5 s  — "Just a little further." typewriter
4  INTENSE — 1.5 s  — faster particle gathering, lightning
5  VOICE3  — 1.0 s  — "GO." huge text, fast
6  BURST   — 2.0 s  — explosive burst
7  FADE    — 1.5 s  — fade to gameplay
"""

import math
import random
import pygame
from typing import TYPE_CHECKING

import src.config as cfg
from src.ui.effects import (
    GOLD, GOLD_BRIGHT, GOLD_DARK,
    ease_out_cubic, ease_out_elastic, ease_out_back, ease_in_quart,
    Star, AmbientEmber, LaunchBurst,
)
from src.core.logger import logger

if TYPE_CHECKING:
    from src.app import App


# ─── Palette ──────────────────────────────────────────────────────────────────
VOID       = (10, 2, 4)
DEEP_RED   = (25, 4, 8)
MYSTIC     = (180, 20, 50)
VOICE_CLR  = (255, 180, 180)   # reddish-white
GOLD_TEXT  = (255, 100, 50)
WHITE_GLOW = (255, 220, 220)

_PHASE_DUR = [
    0.5,   # 0: black hold
    2.0,   # 1: rumble, red aura
    1.5,   # 2: voice line 1 (min)
    1.5,   # 3: voice line 2 (min)
    1.5,   # 4: intense gather
    1.0,   # 5: "GO." voice line
    2.0,   # 6: burst
    1.5,   # 7: fade out
]

_VOICE_HOLD = 1.0

_VOICE_LINES = [
    '"You\'re almost there."',
    '"Just a little further. The awakening is near."',
    '"GO."',
]

class _RuneSymbol:
    _CHARS = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"
    def __init__(self, sw, sh, font):
        self.char  = random.choice(self._CHARS)
        self.x     = random.uniform(sw * 0.05, sw * 0.95)
        self.y     = random.uniform(sh * 0.05, sh * 0.95)
        self.size  = random.uniform(0.8, 1.8)
        self.phase = random.uniform(0, 6.28)
        self.speed = random.uniform(1.0, 3.0)
        self.base_alpha = random.randint(50, 220)
        self.color = random.choice([GOLD_TEXT, MYSTIC[:3], WHITE_GLOW])
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

class _EnergyParticle:
    def __init__(self, sw, sh, gather=False):
        self.gather = gather
        self.sw = sw
        self.sh = sh
        angle  = random.uniform(0, 2 * math.pi)
        
        if gather:
            dist = random.uniform(150, max(sw, sh))
            self.x = sw / 2 + math.cos(angle) * dist
            self.y = sh / 2 + math.sin(angle) * dist
            self.speed = random.uniform(300, 800)
            self.vx = 0
            self.vy = 0
        else:
            speed  = random.uniform(40, 180)
            self.x = sw / 2 + random.uniform(-40, 40)
            self.y = sh / 2 + random.uniform(-40, 40)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed - random.uniform(20, 80)
            
        self.life = random.uniform(1.0, 3.0)
        if gather: self.life = random.uniform(0.3, 1.2)
        self.max_life = self.life
        self.size = random.uniform(2.0, 7.0)
        self.color = random.choice([GOLD_TEXT, MYSTIC[:3], WHITE_GLOW, (255, 50, 50), (255, 100, 0)])

    def update(self, dt, cx, cy):
        if self.gather:
            dx = cx - self.x
            dy = cy - self.y
            dist = math.hypot(dx, dy)
            if dist > 5:
                self.x += (dx / dist) * self.speed * dt
                self.y += (dy / dist) * self.speed * dt
            else:
                self.life = 0
        else:
            self.x  += self.vx * dt
            self.vx *= (1 - 1.2 * dt)
            self.y  += self.vy * dt
            self.vy *= (1 - 1.2 * dt)
            self.life -= dt

    def draw(self, screen):
        if self.life <= 0:
            return
        ratio = self.life / self.max_life
        a  = int(255 * ratio * ratio)
        sz = max(1, int(self.size * ratio))
        pygame.draw.circle(screen, (*self.color, a),
                           (int(self.x), int(self.y)), sz)

class _ShockwaveRing:
    def __init__(self, cx, cy, color, speed, max_radius, width=4, delay=0.0):
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

    def draw(self, screen, offset_x=0, offset_y=0):
        if self.delay > 0:
            return
        ratio = 1.0 - self.radius / self.max_r
        a = int(255 * ratio * ratio)
        r = int(self.radius)
        if r < 2 or a < 4:
            return
        pygame.draw.circle(screen, (*self.color, a),
                           (int(self.cx + offset_x), int(self.cy + offset_y)),
                           r, self.width)


class _LightningStreak:
    """A jagged red lightning bolt."""
    def __init__(self, cx, cy, sw, sh):
        self.cx = cx
        self.cy = cy
        self.sw = sw
        self.sh = sh
        self.life = random.uniform(0.1, 0.3)
        self.max_life = self.life
        self.points = self._generate()
        self.alpha = random.randint(60, 150)

    def _generate(self):
        pts = []
        x = random.uniform(0, self.sw)
        y = 0
        pts.append((x, y))
        segments = random.randint(4, 9)
        for _ in range(segments):
            x += random.uniform(-40, 40)
            y += self.sh / segments + random.uniform(-20, 20)
            pts.append((x, y))
        return pts

    def update(self, dt):
        self.life -= dt

    def draw(self, surf):
        if self.life <= 0:
            return
        a = int(self.alpha * (self.life / self.max_life))
        if a < 3:
            return
        for i in range(len(self.points) - 1):
            pygame.draw.line(surf, (255, 50, 50, max(0, min(255, a))),
                             self.points[i], self.points[i + 1],
                             max(1, int(3 * (self.life / self.max_life))))


class _BloodParticle:
    """A small red particle that bursts outward."""
    def __init__(self, x, y):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(50, 200)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.uniform(0.5, 1.5)
        self.max_life = self.life
        self.size = random.uniform(1, 3)
        self.color = random.choice([(180, 20, 20), (200, 30, 30), (150, 10, 10)])

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 30 * dt
        self.vx *= 0.98
        self.life -= dt

    def draw(self, surf):
        if self.life <= 0:
            return
        ratio = self.life / self.max_life
        a = int(200 * ratio)
        sz = max(1, int(self.size * ratio))
        pygame.draw.circle(surf, (*self.color, max(0, min(255, a))),
                           (int(self.x), int(self.y)), sz)


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
        r = int(40 * (1.0 - self.life))
        for ri in range(r * 4, 0, -r):
            ratio = ri / (r * 4)
            ca = int(a * (1 - ratio) * 0.3)
            if ca < 2:
                continue
            pygame.draw.circle(surf, (255, 180, 150, max(0, min(180, ca))),
                               (int(self.cx), int(self.cy)), ri)
        for angle in [0, math.pi / 4, math.pi / 2, 3 * math.pi / 4]:
            length = int(r * 2.5 * self.life)
            ex = self.cx + int(math.cos(angle) * length)
            ey = self.cy + int(math.sin(angle) * length)
            pygame.draw.line(surf, (255, 180, 150, max(0, min(180, a))),
                             (self.cx, self.cy), (ex, ey), max(1, int(2 * self.life)))


class TempleIntroAnimation:
    def __init__(self, app: "App"):
        self.app = app
        self._phase   = 0
        self._phase_t = 0.0
        self._t       = 0.0
        self._done    = False
        self._skip_requested = False

        self._runes:      list[_RuneSymbol]     = []
        self._v_parts:    list[_EnergyParticle] = []
        self._bursts:     list[LaunchBurst]     = []
        self._shockwaves: list[_ShockwaveRing]  = []
        self._embers:     list[AmbientEmber]    = []
        self._lightnings: list[_LightningStreak] = []
        self._blood_parts: list[_BloodParticle]  = []

        self._tw_chars   = [0.0, 0.0, 0.0]
        self._tw_speed   = 35.0  # Much faster typing
        self._tw_hold    = [0.0, 0.0, 0.0]

        self._font_voice = cfg.get_font(max(18, int(32 * cfg.ui_scale())))
        self._font_go    = cfg.get_font(max(40, int(100 * cfg.ui_scale())))
        self._font_rune  = cfg.get_font(max(20, int(46 * cfg.ui_scale())))
        self._font_skip  = cfg.get_font(max(10, int(16 * cfg.ui_scale())))

        self._bg = None
        self._skip_surf = None
        self._flash_alpha = 0.0
        self._shake_intensity = 0.0
        self._shake_offset_x = 0.0
        self._shake_offset_y = 0.0
        self._shake_phase = 0.0
        self._vignette_alpha = 0.0
        self._lens_flare: _LensFlare | None = None
        self._cached_sw = 0
        self._cached_sh = 0
        self._ember_surf = None
        self._vp_surf = None
        self._lt_surf = None
        self._bp_surf = None
        self._fx_surf = None
        self._flare_surf = None
        self._flash_surf = None
        self._ov_surf = None
        self._vig_cache_sw = 0
        self._vig_cache_sh = 0
        self._vig_base = None

    def on_enter(self):
        self._phase   = 0
        self._phase_t = 0.0
        self._t       = 0.0
        self._done    = False
        self._skip_requested = False
        self._flash_alpha = 0.0
        self._shake_intensity = 0.0
        self._vignette_alpha = 0.0
        self._lens_flare = None

        sw, sh = self._sw(), self._sh()

        self._runes = [_RuneSymbol(sw, sh, self._font_rune) for _ in range(80)]
        self._embers = [AmbientEmber(sw, sh) for _ in range(60)]
        self._v_parts    = []
        self._bursts     = []
        self._shockwaves = []
        self._lightnings = []
        self._blood_parts = []
        self._tw_chars   = [0.0, 0.0, 0.0]
        self._tw_hold    = [0.0, 0.0, 0.0]

        self._skip_surf = self._font_skip.render(
            "SPACE / ENTER — skip", True, (200, 100, 100))

        logger.info("[TempleIntroAnimation] Sequence started.")

    def _sw(self): return self.app.screen.get_width()
    def _sh(self): return self.app.screen.get_height()

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                self._skip_requested = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._skip_requested = True

    def update(self, dt):
        self._t       += dt
        self._phase_t += dt

        sw, sh = self._sw(), self._sh()
        cx, cy = sw // 2, sh // 2

        if self._skip_requested and self._phase < 7:
            self._phase   = 7
            self._phase_t = 0.0
            self._skip_requested = False

        if self._phase == 7 and self._phase_t >= _PHASE_DUR[7]:
            if not self._done:
                self._done = True
                logger.info("[TempleIntroAnimation] Sequence complete → switching to gameplay.")
                self.app.manager.set_state("gameplay")
            return

        # Typewriter update (Phase 2, 3)
        if self._phase in (2, 3):
            vp = self._phase - 2
            line_len = len(_VOICE_LINES[vp])
            self._tw_chars[vp] = min(line_len, self._tw_chars[vp] + self._tw_speed * dt)
            if self._tw_chars[vp] >= line_len:
                self._tw_hold[vp] += dt
                
        # Fast Typewriter update for "GO." (Phase 5)
        if self._phase == 5:
            vp = 2
            line_len = len(_VOICE_LINES[vp])
            self._tw_chars[vp] = min(line_len, self._tw_chars[vp] + self._tw_speed * 3 * dt)
            if self._tw_chars[vp] >= line_len:
                self._tw_hold[vp] += dt

        ready_to_advance = False
        if self._phase in (2, 3):
            vp = self._phase - 2
            ready_to_advance = (self._tw_chars[vp] >= len(_VOICE_LINES[vp])) and (self._tw_hold[vp] >= _VOICE_HOLD)
        elif self._phase == 5:
            vp = 2
            ready_to_advance = (self._tw_chars[vp] >= len(_VOICE_LINES[vp])) and (self._tw_hold[vp] >= _VOICE_HOLD * 0.5)
        else:
            ready_to_advance = self._phase_t >= _PHASE_DUR[self._phase]

        if ready_to_advance:
            self._phase_t = 0.0
            self._phase  += 1
            if self._phase == 6:
                self._spawn_burst(cx, cy)

        # Vignette
        if self._phase >= 4:
            self._vignette_alpha = min(160, self._vignette_alpha + dt * 40)
        elif self._phase >= 1:
            self._vignette_alpha = min(60, self._vignette_alpha + dt * 20)
        else:
            self._vignette_alpha = max(0.0, self._vignette_alpha - dt * 50)

        for e in self._embers:
            e.update(dt, self._t)
            
        self._v_parts = [p for p in self._v_parts if p.life > 0]
        for p in self._v_parts:
            p.update(dt, cx, cy)

        if 1 <= self._phase <= 3:
            for _ in range(6):
                self._v_parts.append(_EnergyParticle(sw, sh, gather=False))
        elif self._phase == 4:
            for _ in range(25):
                self._v_parts.append(_EnergyParticle(sw, sh, gather=True))
        elif self._phase == 5:
            for _ in range(40):
                self._v_parts.append(_EnergyParticle(sw, sh, gather=True))
                self._v_parts.append(_EnergyParticle(sw, sh, gather=False))

        # Lightning during intense / GO phases
        if self._phase in (4, 5):
            if random.random() < 0.08:
                self._lightnings.append(_LightningStreak(cx, cy, sw, sh))
        self._lightnings = [l for l in self._lightnings if l.life > 0]
        for l in self._lightnings:
            l.update(dt)

        # Blood particles during burst
        if self._phase == 6:
            for _ in range(5):
                self._blood_parts.append(
                    _BloodParticle(cx + random.uniform(-100, 100),
                                   cy + random.uniform(-100, 100))
                )
        self._blood_parts = [bp for bp in self._blood_parts if bp.life > 0]
        for bp in self._blood_parts:
            bp.update(dt)

        self._bursts = [b for b in self._bursts if b.lt > 0]
        for b in self._bursts:
            b.update(dt)

        self._shockwaves = [w for w in self._shockwaves if w.alive]
        for w in self._shockwaves:
            w.update(dt)

        if self._lens_flare is not None:
            self._lens_flare.update(dt)
            if self._lens_flare.life <= 0:
                self._lens_flare = None

        if self._flash_alpha > 0:
            self._flash_alpha = max(0.0, self._flash_alpha - dt * 150)

        if self._phase == 1:
            self._shake_intensity = 6.0 * (self._phase_t / _PHASE_DUR[1])
        elif self._phase == 4:
            self._shake_intensity = 18.0 * ease_in_quart(self._phase_t / _PHASE_DUR[4])
        elif self._phase == 5:
            self._shake_intensity = 30.0
        elif self._phase == 6:
            self._shake_intensity = 50.0 * max(0, 1.0 - (self._phase_t / 0.6))
        else:
            self._shake_intensity = max(0.0, self._shake_intensity - dt * 50)

        # Smooth shake update
        self._shake_phase += dt * 10.0
        intensity = self._shake_intensity
        if intensity > 0.5:
            sp = self._shake_phase
            self._shake_offset_x = math.sin(sp) * intensity * 0.7 + math.sin(sp * 2.3) * intensity * 0.3
            self._shake_offset_y = math.cos(sp * 1.7) * intensity * 0.7 + math.sin(sp * 2.9) * intensity * 0.3
        else:
            self._shake_offset_x = 0.0
            self._shake_offset_y = 0.0

    def _spawn_burst(self, cx, cy):
        self._flash_alpha = 255.0
        self._lens_flare = _LensFlare(cx, cy)
        for i, (col, spd, wr) in enumerate([
            (WHITE_GLOW,     900, 1400),
            (MYSTIC,         700, 1200),
            (WHITE_GLOW,     550, 1000),
            ((255, 100, 100), 400, 800),
            (GOLD_TEXT,      300, 650),
            (MYSTIC,         200, 500),
        ]):
            self._shockwaves.append(_ShockwaveRing(cx, cy, col, spd, wr,
                                                   width=max(2, 6 - i),
                                                   delay=i * 0.06))

        for _ in range(350):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 900)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(0, 120)
            col = random.choice([WHITE_GLOW, (255, 120, 120), MYSTIC[:3],
                                 GOLD_TEXT, (255, 80, 80), (200, 30, 30)])
            self._bursts.append(LaunchBurst(
                cx + random.uniform(-25, 25), cy + random.uniform(-25, 25),
                vx, vy, col, random.randint(3, 9), random.uniform(0.6, 3.0)
            ))

    def _ensure_surfaces(self, sw, sh):
        if sw == self._cached_sw and sh == self._cached_sh:
            return
        self._cached_sw, self._cached_sh = sw, sh
        self._ember_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._vp_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._lt_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._bp_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._fx_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._flare_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._flash_surf = pygame.Surface((sw, sh))
        self._ov_surf = pygame.Surface((sw, sh))

    def draw(self, screen):
        self.update(self.app.clock.get_time() / 1000.0)
        sw, sh = screen.get_width(), screen.get_height()
        cx, cy = sw // 2, sh // 2
        t = self._t
        phase = self._phase
        pt = self._phase_t

        self._ensure_surfaces(sw, sh)

        sx = int(self._shake_offset_x)
        sy = int(self._shake_offset_y)

        screen.fill(VOID)
        self._draw_nebula(screen, sw, sh, t, cx, cy)

        if phase >= 1:
            rune_global = int(255 * min(1.0, pt / 1.0)) if phase == 1 else 255
            if phase == 7:
                rune_global = int(255 * max(0.0, 1.0 - pt / _PHASE_DUR[7]))
            if phase == 4 or phase == 5:
                rune_global = 255
            for rune in self._runes:
                orig_x, orig_y = rune.x, rune.y
                rune.x += sx
                rune.y += sy
                rune.draw(screen, t * 2.5 if phase >= 4 else t, rune_global)
                rune.x, rune.y = orig_x, orig_y

        self._ember_surf.fill((0, 0, 0, 0))
        for e in self._embers:
            orig_x, orig_y = e.x, e.y
            e.x += sx
            e.y += sy
            e.draw(self._ember_surf, t * 2.0 if phase >= 4 else t)
            e.x, e.y = orig_x, orig_y
        if phase >= 1:
            screen.blit(self._ember_surf, (0, 0))

        if self._v_parts:
            self._vp_surf.fill((0, 0, 0, 0))
            for p in self._v_parts:
                orig_x, orig_y = p.x, p.y
                p.x += sx
                p.y += sy
                p.draw(self._vp_surf)
                p.x, p.y = orig_x, orig_y
            screen.blit(self._vp_surf, (0, 0))

        # Lightning
        if self._lightnings:
            self._lt_surf.fill((0, 0, 0, 0))
            for l in self._lightnings:
                l.draw(self._lt_surf)
            screen.blit(self._lt_surf, (0, 0))

        # Blood particles
        if self._blood_parts:
            self._bp_surf.fill((0, 0, 0, 0))
            for bp in self._blood_parts:
                bp.draw(self._bp_surf)
            screen.blit(self._bp_surf, (0, 0))

        if phase >= 1:
            self._draw_centre_glow(screen, cx + sx, cy + sy, t, phase, pt)

        if phase in (2, 3):
            line_idx = phase - 2
            self._draw_voice_line(screen, sw, sh, cx, cy, line_idx, t, pt, phase)

        if phase == 5:
            self._draw_go_text(screen, sw, sh, cx, cy, pt)

        if self._shockwaves or self._bursts:
            self._fx_surf.fill((0, 0, 0, 0))
            for w in self._shockwaves:
                w.draw(self._fx_surf, sx, sy)
            for b in self._bursts:
                orig_x, orig_y = b.x, b.y
                b.x += sx
                b.y += sy
                b.draw(self._fx_surf)
                b.x, b.y = orig_x, orig_y
            screen.blit(self._fx_surf, (0, 0))

        if self._lens_flare is not None:
            self._flare_surf.fill((0, 0, 0, 0))
            self._lens_flare.draw(self._flare_surf)
            screen.blit(self._flare_surf, (0, 0))

        # Vignette
        if self._vignette_alpha > 1:
            self._draw_vignette(screen, sw, sh)

        if self._flash_alpha > 0:
            self._flash_surf.fill(WHITE_GLOW)
            self._flash_surf.set_alpha(int(self._flash_alpha))
            screen.blit(self._flash_surf, (0, 0))

        if phase == 0:
            screen.fill((0, 0, 0))
        elif phase == 7:
            fade_a = int(255 * ease_out_cubic(min(1.0, pt / _PHASE_DUR[7])))
            if fade_a > 0:
                self._ov_surf.fill((0, 0, 0))
                self._ov_surf.set_alpha(fade_a)
                screen.blit(self._ov_surf, (0, 0))

        if self._skip_surf and 1 <= phase <= 5:
            skip_a = int(130 * (0.5 + 0.5 * math.sin(t * 3.0)))
            self._skip_surf.set_alpha(max(0, min(200, skip_a)))
            screen.blit(
                self._skip_surf,
                (sw - self._skip_surf.get_width() - 20,
                 sh - self._skip_surf.get_height() - 16)
            )

    def _draw_vignette(self, screen, sw, sh):
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

    def _draw_nebula(self, screen, sw, sh, t, cx, cy):
        phase_shift = t * 0.15
        for (rx, ry_off, r, col, base_a) in [
            (0.35, -0.10, 0.40, (120, 20, 30), 25),
            (0.50,  0.15, 0.35, (80, 10, 20),  20),
            (-0.10, 0.05, 0.30, (160, 40, 50), 15),
            (-0.30, 0.25, 0.22, (180, 30, 40), 12),
            (0.25, -0.22, 0.18, (90, 15, 25),  16),
        ]:
            ncx = int(cx + sw * rx * math.cos(phase_shift))
            ncy = int(cy + sh * ry_off + sh * 0.1 * math.sin(phase_shift * 2.0))
            nr  = int(min(sw, sh) * r)
            a   = int(base_a + 12 * math.sin(t * 0.8 + rx * 5))
            a   = max(0, min(55, a))
            ns  = pygame.Surface((nr * 2, nr * 2), pygame.SRCALPHA)
            pygame.draw.circle(ns, (*col, a), (nr, nr), nr)
            screen.blit(ns, (ncx - nr, ncy - nr))

    def _draw_centre_glow(self, screen, cx, cy, t, phase, pt):
        base_r = int(min(self._sw(), self._sh()) * 0.25)
        pulse  = 0.8 + 0.2 * math.sin(t * 3.0)
        
        if phase == 4:
            pulse += 0.4 * (pt / _PHASE_DUR[4])
        elif phase == 5:
            pulse = 1.8 + 0.3 * math.sin(t * 18.0)
        elif phase == 6:
            pulse = 1.5 + 0.2 * math.sin(t * 8.0)
            
        r      = int(base_r * pulse)
        a_mult = min(1.0, pt / 1.0) if phase == 1 else 1.0
        if phase == 7:
            a_mult = max(0.0, 1.0 - pt / _PHASE_DUR[7])

        ns = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for ri in range(r, 0, -4):
            ratio = ri / r
            base_a = int(80 * (1.0 - ratio) * a_mult)
            col = (
                max(0, min(255, int(160 + 95 * (1 - ratio)))),
                max(0, min(255, int(15 +  50 * (1 - ratio)))),
                max(0, min(255, int(20 + 35 * (1 - ratio)))),
                max(0, min(90, base_a))
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
        pad_x, pad_y = int(60 * cfg.ui_scale()), int(35 * cfg.ui_scale())
        panel_w = min(max_line_w + pad_x * 2, sw - 80)
        panel_h = total_h + pad_y * 2 + int(50 * cfg.ui_scale())
        panel_x = cx - panel_w // 2
        panel_y = cy - panel_h // 2 + int(sh * 0.22)

        text_alpha = int(255 * min(1.0, pt / 0.3))

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (15, 2, 5, 220), (0, 0, panel_w, panel_h), border_radius=16)

        bord_a = int(200 + 80 * math.sin(t * 3.5))
        pygame.draw.rect(panel_surf, (*MYSTIC[:3], max(0, min(255, bord_a))),
                         (0, 0, panel_w, panel_h), max(2, int(3*cfg.ui_scale())), border_radius=16)

        # Inner glow border
        in_a = int(70 + 40 * math.sin(t * 2.5 + 1.0))
        pygame.draw.rect(panel_surf, (*GOLD_TEXT, max(0, min(90, in_a))),
                         (3, 3, panel_w - 6, panel_h - 6), 1, border_radius=14)

        tag_font = cfg.get_font(max(10, int(16 * cfg.ui_scale())))
        tag = tag_font.render("⟨ UNKNOWN ENTITY ⟩", True, (*GOLD_TEXT, 220))
        panel_surf.blit(tag, (panel_w // 2 - tag.get_width() // 2, 12))

        ty = pad_y + int(28 * cfg.ui_scale())
        for ln in lines:
            if not ln:
                ty += lh
                continue
            txt_surf = self._font_voice.render(ln, True, VOICE_CLR)
            
            # Glitch effect — more aggressive
            if random.random() < 0.08 and shown_chars >= len(full_text):
                for _ in range(2):
                    glitch_surf = self._font_voice.render(ln, True, (255, 50, 50))
                    panel_surf.blit(glitch_surf,
                                    (panel_w // 2 - txt_surf.get_width() // 2 + random.randint(-6, 6),
                                     ty + random.randint(-3, 3)))
            
            panel_surf.blit(txt_surf, (panel_w // 2 - txt_surf.get_width() // 2, ty))
            ty += lh

        panel_surf.set_alpha(text_alpha)
        screen.blit(panel_surf, (panel_x, panel_y))

        if shown_chars < len(full_text):
            if int(t * 6) % 2 == 0:
                cur_x = panel_x + panel_w // 2 + self._font_voice.size(lines[-1])[0] // 2 + 5
                cur_y = panel_y + pad_y + int(28 * cfg.ui_scale()) + (len(lines) - 1) * lh
                pygame.draw.rect(screen, (*GOLD_TEXT, 220),
                                 (cur_x, cur_y + 2, max(2, int(3 * cfg.ui_scale())), lh - 4))

    def _draw_go_text(self, screen, sw, sh, cx, cy, pt):
        text = _VOICE_LINES[2]
        shown_chars = int(self._tw_chars[2])
        display = text[:shown_chars]
        
        t_surf = self._font_go.render(display, True, (255, 50, 50))
        t_w = t_surf.get_width()
        t_h = t_surf.get_height()
        
        jitter_x = random.uniform(-8, 8)
        jitter_y = random.uniform(-8, 8)
        
        # Multiple layered glows (render text once per glow layer)
        for scale_mult, col, max_a in [
            (3.0, (100, 0, 0), 60),
            (2.0, (200, 0, 0), 100),
            (1.5, (255, 50, 50), 140),
        ]:
            glow_size = int(max(t_w, t_h) * scale_mult * 0.08)
            base_text = self._font_go.render(display, True, col)
            glow_s = pygame.Surface((t_w + glow_size * 2, t_h + glow_size * 2), pygame.SRCALPHA)
            for ri in range(glow_size, 0, -2):
                ratio = ri / glow_size
                ca = int(max_a * (1 - ratio) ** 2 * (0.5 + 0.5 * math.sin(self._t * 10)))
                gs = base_text.copy()
                gs.set_alpha(max(0, min(180, ca)))
                glow_s.blit(gs, (glow_size - ri, glow_size - ri))
            screen.blit(glow_s,
                        (cx - t_w // 2 - glow_size + jitter_x * 2,
                         cy - t_h // 2 - glow_size + jitter_y * 2))
        
        # Draw main text
        screen.blit(t_surf, (cx - t_w // 2 + jitter_x, cy - t_h // 2 + jitter_y))
        
        # Red scanline overlay
        if random.random() < 0.15:
            scan_surf = pygame.Surface((t_w, t_h), pygame.SRCALPHA)
            for sy in range(0, t_h, 3):
                pygame.draw.line(scan_surf, (255, 0, 0, 60),
                                 (0, sy), (t_w, sy), 1)
            screen.blit(scan_surf, (cx - t_w // 2 + jitter_x, cy - t_h // 2 + jitter_y))
