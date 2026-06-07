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
    '"Far to the east, a great dragon slumbers in a\nmountain cave. You must slay it, or the realm will burn."',
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
        scaled = pygame.transform.smoothscale(self._surf, (nw, nh))
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
        s  = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, a), (sz, sz), sz)
        screen.blit(s, (int(self.x) - sz, int(self.y) - sz))


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
        s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, a), (r + 2, r + 2), r, self.width)
        screen.blit(s, (self.cx - r - 2, self.cy - r - 2))


# ─── Main state ───────────────────────────────────────────────────────────────

class IntroAnimation:
    """
    Full-screen cinematic intro that plays once when the player starts the game.

    Attributes:
        app (App): Main application reference.
        _phase (int): Current animation phase index.
        _phase_t (float): Time elapsed inside the current phase.
        _t (float): Global accumulated time.
        _done (bool): True once the sequence has completed.
        _skip_requested (bool): Set to True if the player presses SPACE/ENTER.

    Methods:
        on_enter(): Reset all state; called when the StateManager activates us.
        handle_event(event): Handle SPACE/ENTER skip.
        update(dt): Advance animation timers and particles.
        draw(screen): Render the current frame.
    """

    def __init__(self, app: "App"):
        self.app = app
        self._phase   = 0
        self._phase_t = 0.0
        self._t       = 0.0
        self._done    = False
        self._skip_requested = False

        # Particle lists
        self._runes:      list[_RuneSymbol]   = []
        self._v_parts:    list[_VoiceParticle] = []
        self._bursts:     list[LaunchBurst]   = []
        self._shockwaves: list[_ShockwaveRing] = []
        self._embers:     list[AmbientEmber]  = []
        self._stars:      list[Star]          = []

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

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self):
        """Reset everything so the intro is fresh each time."""
        self._phase   = 0
        self._phase_t = 0.0
        self._t       = 0.0
        self._done    = False
        self._skip_requested = False
        self._flash_alpha = 0.0

        sw, sh = self._sw(), self._sh()

        self._runes = [_RuneSymbol(sw, sh, self._font_rune) for _ in range(45)]
        self._embers = [AmbientEmber(sw, sh) for _ in range(20)]
        self._stars  = [Star(sw, sh) for _ in range(120)]
        self._v_parts    = []
        self._bursts     = []
        self._shockwaves = []
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

        # ── Particles ─────────────────────────────────────────────────────────
        for e in self._embers:
            e.update(dt, self._t)
        self._v_parts = [p for p in self._v_parts if p.life > 0]
        for p in self._v_parts:
            p.update(dt)

        # Spawn voice particles during voice & burst phases
        if 2 <= self._phase <= 5:
            rate = 3 if self._phase < 5 else 12
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

        # Flash alpha — always decays regardless of phase
        if self._flash_alpha > 0:
            self._flash_alpha = max(0.0, self._flash_alpha - dt * 220)

    def _spawn_burst(self, cx, cy):
        """Spawn the big particle eruption for phase 5."""
        self._flash_alpha = 180.0   # softer initial flash — not blinding white

        # Shockwave rings — gold and white only (no purple)
        for i, (col, spd, wr) in enumerate([
            (GOLD_BRIGHT,  520, 900),
            (WHITE_GLOW,   380, 700),
            (GOLD,         260, 550),
            ((255, 200, 80), 180, 400),
        ]):
            self._shockwaves.append(_ShockwaveRing(cx, cy, col, spd, wr,
                                                   width=max(2, 4 - i),
                                                   delay=i * 0.12))

        # Burst particles — warm gold and white only
        for _ in range(180):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 380)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(0, 60)
            col = random.choice([GOLD_BRIGHT, (255, 180, 60), WHITE_GLOW, (255, 220, 120)])
            self._bursts.append(
                LaunchBurst(
                    cx + random.uniform(-15, 15),
                    cy + random.uniform(-15, 15),
                    vx, vy, col,
                    random.randint(2, 6),
                    random.uniform(0.5, 2.2)
                )
            )

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, screen):
        self.update(self.app.clock.get_time() / 1000.0)
        sw, sh = screen.get_width(), screen.get_height()
        cx, cy = sw // 2, sh // 2
        t = self._t
        phase = self._phase
        pt = self._phase_t

        # 1. Background ───────────────────────────────────────────────────────
        screen.fill(VOID)

        # Subtle nebula gradient
        self._draw_nebula(screen, sw, sh, t)

        # Stars (visible from phase 1 onwards)
        if phase >= 1:
            star_a = int(255 * min(1.0, pt / 1.5)) if phase == 1 else 255
            star_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for star in self._stars:
                star.draw(star_surf, t)
            star_surf.set_alpha(star_a)
            screen.blit(star_surf, (0, 0))

        # 2. Runes ────────────────────────────────────────────────────────────
        if phase >= 1:
            rune_global = int(255 * min(1.0, pt / 1.0)) if phase == 1 else 255
            if phase == 6:
                rune_global = int(255 * max(0.0, 1.0 - pt / _PHASE_DUR[6]))
            for rune in self._runes:
                rune.draw(screen, t, rune_global)

        # 3. Embers ───────────────────────────────────────────────────────────
        ember_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for e in self._embers:
            e.draw(ember_surf, t)
        if phase >= 2:
            screen.blit(ember_surf, (0, 0))

        # 4. Voice particles ──────────────────────────────────────────────────
        if self._v_parts:
            vp_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for p in self._v_parts:
                p.draw(vp_surf)
            screen.blit(vp_surf, (0, 0))

        # 5. Centre glow / orb ────────────────────────────────────────────────
        if phase >= 2:
            self._draw_centre_glow(screen, cx, cy, t, phase, pt)

        # 6. Voice lines ──────────────────────────────────────────────────────
        if 2 <= phase <= 4:
            line_idx = phase - 2
            self._draw_voice_line(screen, sw, sh, cx, cy, line_idx, t, pt, phase)

        # 7. "Arise, Chosen One" grand title (burst phase) ────────────────────
        if phase == 5:
            self._draw_arise_title(screen, sw, sh, cx, cy, pt)

        # 8. Shockwaves & burst particles ─────────────────────────────────────
        if self._shockwaves or self._bursts:
            fx_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for w in self._shockwaves:
                w.draw(fx_surf)
            for b in self._bursts:
                b.draw(fx_surf)
            screen.blit(fx_surf, (0, 0))

        # 9. Flash (burst entry) ──────────────────────────────────────────────
        if self._flash_alpha > 0:
            flash = pygame.Surface((sw, sh))
            flash.fill(WHITE_GLOW)
            flash.set_alpha(int(self._flash_alpha))
            screen.blit(flash, (0, 0))

        # 10. Fade overlays ────────────────────────────────────────────────────
        if phase == 0:
            # Pure black — full opacity
            screen.fill((0, 0, 0))
        elif phase == 1:
            # Fade from black: alpha decreases as pt increases
            fade_a = max(0, int(255 * (1.0 - ease_out_cubic(min(1.0, pt / 1.5)))))
            if fade_a > 0:
                ov = pygame.Surface((sw, sh))
                ov.fill((0, 0, 0))
                ov.set_alpha(fade_a)
                screen.blit(ov, (0, 0))
        elif phase == 6:
            # Fade to black
            fade_a = int(255 * ease_out_cubic(min(1.0, pt / _PHASE_DUR[6])))
            if fade_a > 0:
                ov = pygame.Surface((sw, sh))
                ov.fill((0, 0, 0))
                ov.set_alpha(fade_a)
                screen.blit(ov, (0, 0))

        # 11. Skip hint ────────────────────────────────────────────────────────
        if self._skip_surf and 1 <= phase <= 4:
            skip_a = int(130 * (0.5 + 0.5 * math.sin(t * 1.8)))
            self._skip_surf.set_alpha(max(0, min(200, skip_a)))
            screen.blit(
                self._skip_surf,
                (sw - self._skip_surf.get_width() - 20,
                 sh - self._skip_surf.get_height() - 16)
            )

    # ── Sub-draw helpers ──────────────────────────────────────────────────────

    def _draw_nebula(self, screen, sw, sh, t):
        """Draw a gently pulsing coloured nebula in the background."""
        cx, cy = sw // 2, sh // 2
        phase_shift = t * 0.07
        for (rx, ry_off, r, col, base_a) in [
            (0.40, -0.12, 0.35, (40, 20, 100), 18),
            (0.60,  0.10, 0.30, (20, 40,  80), 14),
            (-0.05, 0.0,  0.25, (60, 30, 120), 10),
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
        base_r = int(min(self._sw(), self._sh()) * 0.18)
        pulse  = 0.85 + 0.15 * math.sin(t * 1.4)
        r      = int(base_r * pulse)
        a_mult = min(1.0, pt / 0.8) if phase == 2 else 1.0
        if phase == 6:
            a_mult = max(0.0, 1.0 - pt / _PHASE_DUR[6])

        for ri in range(r, 0, -4):
            ratio = ri / r
            # Inner: bright lavender → outer: dark purple
            base_a = int(40 * (1.0 - ratio) * a_mult)
            col = (
                max(0, min(255, int(80 + 140 * (1 - ratio)))),
                max(0, min(255, int(40 +  80 * (1 - ratio)))),
                max(0, min(255, int(180 + 60 * (1 - ratio)))),
                max(0, min(50, base_a))
            )
            ns = pygame.Surface((ri * 2, ri * 2), pygame.SRCALPHA)
            pygame.draw.circle(ns, col, (ri, ri), ri)
            screen.blit(ns, (cx - ri, cy - ri))

    def _draw_voice_line(self, screen, sw, sh, cx, cy, line_idx, t, pt, phase):
        """
        Draw a single voice line using a typewriter effect.
        The text is centred vertically around the middle of the screen with a
        panel and decorative border.
        """
        full_text = _VOICE_LINES[line_idx]
        shown_chars = int(self._tw_chars[line_idx])
        display = full_text[:shown_chars]

        # Split on actual newlines
        lines = display.split("\n")

        lh = self._font_voice.get_height() + 4
        total_h = lh * len(lines)

        # Panel bounds
        max_line_w = max((self._font_voice.size(ln)[0] for ln in full_text.split("\n")), default=1)
        pad_x, pad_y = int(40 * cfg.ui_scale()), int(20 * cfg.ui_scale())
        panel_w = min(max_line_w + pad_x * 2, sw - 80)
        panel_h = total_h + pad_y * 2 + int(30 * cfg.ui_scale())
        panel_x = cx - panel_w // 2
        panel_y = cy - panel_h // 2 + int(sh * 0.18)

        # Fade-in during first 0.4 s of this phase
        text_alpha = int(255 * min(1.0, pt / 0.4))
        if phase > line_idx + 2:   # next phase has begun → text should fade out
            pass   # we simply stop showing it (phase guard above)

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)

        # Dark glass background
        pygame.draw.rect(panel_surf, (8, 5, 20, 190), (0, 0, panel_w, panel_h), border_radius=12)

        # Gold border — animated glow
        bord_a = int(160 + 60 * math.sin(t * 1.5))
        pygame.draw.rect(panel_surf, (*GOLD, max(0, min(255, bord_a))),
                         (0, 0, panel_w, panel_h), 2, border_radius=12)

        # Top accent bar
        bar_w = panel_w - 40
        bar_surf = pygame.Surface((bar_w, 2), pygame.SRCALPHA)
        for bx in range(bar_w):
            ratio = 1.0 - abs(bx / bar_w - 0.5) * 2
            ba = int(200 * ratio * ratio)
            bar_surf.set_at((bx, 0), (*GOLD_BRIGHT, max(0, min(255, ba))))
        panel_surf.blit(bar_surf, (20, 4))

        # Entity tag
        tag_font = cfg.get_font(max(9, int(14 * cfg.ui_scale())))
        tag = tag_font.render("⟨ THE VOICE ⟩", True, (*GOLD, 180))
        panel_surf.blit(tag, (panel_w // 2 - tag.get_width() // 2, 8))

        # Text lines with shimmer
        ty = pad_y + int(20 * cfg.ui_scale())
        for ln in lines:
            if not ln:
                ty += lh
                continue
            txt_surf = self._font_voice.render(ln, True, VOICE_CLR)
            # Add a subtle shimmer
            shimmer_phase = (t * 80 + 0) % (txt_surf.get_width() + 40)
            sh_w = max(1, int(txt_surf.get_width() * 0.12))
            sh_band = pygame.Surface((sh_w, txt_surf.get_height()), pygame.SRCALPHA)
            for sx in range(sh_w):
                ratio = 1.0 - abs(sx - sh_w / 2) / (sh_w / 2 + 1)
                sa = int(60 * ratio)
                pygame.draw.line(sh_band, (*WHITE_GLOW, max(0, min(100, sa))), (sx, 0), (sx, txt_surf.get_height()))
            txt_surf.blit(sh_band, (int(shimmer_phase - sh_w), 0), special_flags=pygame.BLEND_RGBA_ADD)

            panel_surf.blit(txt_surf, (panel_w // 2 - txt_surf.get_width() // 2, ty))
            ty += lh

        panel_surf.set_alpha(text_alpha)
        screen.blit(panel_surf, (panel_x, panel_y))

        # Cursor blink
        if shown_chars < len(full_text):
            if int(t * 3) % 2 == 0:
                cur_x = panel_x + panel_w // 2 + self._font_voice.size(lines[-1])[0] // 2 + 3
                cur_y = panel_y + pad_y + int(20 * cfg.ui_scale()) + (len(lines) - 1) * lh
                pygame.draw.rect(screen, (*GOLD_BRIGHT, 200),
                                 (cur_x, cur_y + 2, max(1, int(2 * cfg.ui_scale())), lh - 4))

    def _draw_arise_title(self, screen, sw, sh, cx, cy, pt):
        """
        Render the grand 'ARISE, CHOSEN ONE.' text that dominates the burst phase.
        Each letter drops in elastically, then glows.
        """
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

                # Glow halo
                if c_eased > 0.5:
                    glow_a = int(80 * (c_eased - 0.5) * 2 * (0.7 + 0.3 * math.sin(self._t * 3 + i)))
                    glow_s = self._font_arise.render(c, True, (255, 200, 80))
                    glow_s.set_alpha(max(0, min(120, glow_a)))
                    screen.blit(glow_s, (sx - 1, base_y + c_off_y - 1))

                cs.set_alpha(c_alpha)
                screen.blit(cs, (sx, base_y + c_off_y))
                sx += cs.get_width()

        lh = self._font_arise.get_height()
        _render_word(text1, cy - lh - int(8 * cfg.ui_scale()), 0.0)
        _render_word(text2, cy + int(8 * cfg.ui_scale()), 0.2)

        # Decorative horizontal line beneath
        line_t = max(0.0, min(1.0, (pt - 0.8) / 0.4))
        if line_t > 0:
            lw = int(sw * 0.55 * ease_out_cubic(line_t))
            lx = cx - lw // 2
            ly = cy + lh + int(16 * cfg.ui_scale())
            la = int(200 * line_t)
            pygame.draw.line(screen, (*GOLD, max(0, min(255, la))), (lx, ly), (lx + lw, ly), max(2, int(3 * cfg.ui_scale())))
            pygame.draw.line(screen, (*GOLD_BRIGHT, max(0, min(255, la // 2))), (lx, ly - 2), (lx + lw, ly - 2), 1)
