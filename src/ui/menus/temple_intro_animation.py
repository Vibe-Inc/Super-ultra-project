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
4  INTENSE — 1.5 s  — faster particle gathering
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
        scaled = pygame.transform.smoothscale(self._surf, (nw, nh))
        scaled.set_alpha(a)
        screen.blit(scaled, (int(self.x - nw / 2), int(self.y - nh / 2)))

class _EnergyParticle:
    def __init__(self, sw, sh, gather=False):
        self.gather = gather
        self.sw = sw
        self.sh = sh
        angle  = random.uniform(0, 2 * math.pi)
        
        if gather:
            dist = random.uniform(200, max(sw, sh))
            self.x = sw / 2 + math.cos(angle) * dist
            self.y = sh / 2 + math.sin(angle) * dist
            self.speed = random.uniform(300, 700)
            self.vx = 0
            self.vy = 0
        else:
            speed  = random.uniform(40, 180)
            self.x = sw / 2 + random.uniform(-40, 40)
            self.y = sh / 2 + random.uniform(-40, 40)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed - random.uniform(20, 80)
            
        self.life = random.uniform(1.0, 3.0)
        if gather: self.life = random.uniform(0.5, 1.5)
        self.max_life = self.life
        self.size = random.uniform(2.0, 6.0)
        self.color = random.choice([GOLD_TEXT, MYSTIC[:3], WHITE_GLOW, (255, 50, 50)])

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
        s  = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, a), (sz, sz), sz)
        screen.blit(s, (int(self.x) - sz, int(self.y) - sz))

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
        s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, a), (r + 2, r + 2), r, self.width)
        screen.blit(s, (self.cx - r - 2 + offset_x, self.cy - r - 2 + offset_y))


class TempleIntroAnimation:
    def __init__(self, app: "App"):
        self.app = app
        self._phase   = 0
        self._phase_t = 0.0
        self._t       = 0.0
        self._done    = False
        self._skip_requested = False

        self._runes:      list[_RuneSymbol]    = []
        self._v_parts:    list[_EnergyParticle] = []
        self._bursts:     list[LaunchBurst]    = []
        self._shockwaves: list[_ShockwaveRing] = []
        self._embers:     list[AmbientEmber]   = []

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

    def on_enter(self):
        self._phase   = 0
        self._phase_t = 0.0
        self._t       = 0.0
        self._done    = False
        self._skip_requested = False
        self._flash_alpha = 0.0
        self._shake_intensity = 0.0

        sw, sh = self._sw(), self._sh()

        self._runes = [_RuneSymbol(sw, sh, self._font_rune) for _ in range(60)]
        self._embers = [AmbientEmber(sw, sh) for _ in range(40)]
        self._v_parts    = []
        self._bursts     = []
        self._shockwaves = []
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

        for e in self._embers:
            e.update(dt, self._t)
            
        self._v_parts = [p for p in self._v_parts if p.life > 0]
        for p in self._v_parts:
            p.update(dt, cx, cy)

        if 1 <= self._phase <= 3:
            for _ in range(5):
                self._v_parts.append(_EnergyParticle(sw, sh, gather=False))
        elif self._phase == 4: # Intense gather
            for _ in range(15):
                self._v_parts.append(_EnergyParticle(sw, sh, gather=True))
        elif self._phase == 5:
            for _ in range(30):
                self._v_parts.append(_EnergyParticle(sw, sh, gather=True))
                self._v_parts.append(_EnergyParticle(sw, sh, gather=False))

        self._bursts = [b for b in self._bursts if b.lt > 0]
        for b in self._bursts:
            b.update(dt)

        self._shockwaves = [w for w in self._shockwaves if w.alive]
        for w in self._shockwaves:
            w.update(dt)

        if self._flash_alpha > 0:
            self._flash_alpha = max(0.0, self._flash_alpha - dt * 150)
            
        if self._phase == 1:
            self._shake_intensity = 5.0 * (self._phase_t / _PHASE_DUR[1])
        elif self._phase == 4:
            self._shake_intensity = 15.0 * ease_in_quart(self._phase_t / _PHASE_DUR[4])
        elif self._phase == 5:
            self._shake_intensity = 25.0
        elif self._phase == 6:
            self._shake_intensity = 40.0 * max(0, 1.0 - (self._phase_t / 0.5))
        else:
            self._shake_intensity = max(0.0, self._shake_intensity - dt * 50)

    def _spawn_burst(self, cx, cy):
        self._flash_alpha = 255.0
        for i, (col, spd, wr) in enumerate([
            (WHITE_GLOW,   800, 1200),
            ((255, 100, 100), 600, 1000),
            (MYSTIC,       400, 800),
            (GOLD_TEXT,    250, 600),
        ]):
            self._shockwaves.append(_ShockwaveRing(cx, cy, col, spd, wr, width=max(3, 6 - i), delay=i * 0.08))

        for _ in range(300):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 800)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(0, 100)
            col = random.choice([WHITE_GLOW, (255, 120, 120), MYSTIC[:3], GOLD_TEXT])
            self._bursts.append(LaunchBurst(
                cx + random.uniform(-20, 20), cy + random.uniform(-20, 20),
                vx, vy, col, random.randint(3, 8), random.uniform(0.8, 3.0)
            ))

    def draw(self, screen):
        self.update(self.app.clock.get_time() / 1000.0)
        sw, sh = screen.get_width(), screen.get_height()
        cx, cy = sw // 2, sh // 2
        t = self._t
        phase = self._phase
        pt = self._phase_t
        
        shake_x = random.uniform(-self._shake_intensity, self._shake_intensity)
        shake_y = random.uniform(-self._shake_intensity, self._shake_intensity)
        cx += int(shake_x)
        cy += int(shake_y)

        screen.fill(VOID)
        self._draw_nebula(screen, sw, sh, t, cx, cy)

        if phase >= 1:
            rune_global = int(255 * min(1.0, pt / 1.0)) if phase == 1 else 255
            if phase == 7:
                rune_global = int(255 * max(0.0, 1.0 - pt / _PHASE_DUR[7]))
            if phase == 4 or phase == 5:
                rune_global = 255 # Keep fully lit
            for rune in self._runes:
                # Add offset for shake
                orig_x, orig_y = rune.x, rune.y
                rune.x += shake_x
                rune.y += shake_y
                rune.draw(screen, t * 2.0 if phase >= 4 else t, rune_global)
                rune.x, rune.y = orig_x, orig_y

        ember_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for e in self._embers:
            orig_x, orig_y = e.x, e.y
            e.x += shake_x
            e.y += shake_y
            e.draw(ember_surf, t * 2.0 if phase >= 4 else t)
            e.x, e.y = orig_x, orig_y
        if phase >= 1:
            screen.blit(ember_surf, (0, 0))

        if self._v_parts:
            vp_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for p in self._v_parts:
                orig_x, orig_y = p.x, p.y
                p.x += shake_x
                p.y += shake_y
                p.draw(vp_surf)
                p.x, p.y = orig_x, orig_y
            screen.blit(vp_surf, (0, 0))

        if phase >= 1:
            self._draw_centre_glow(screen, cx, cy, t, phase, pt)

        if phase in (2, 3):
            line_idx = phase - 2
            self._draw_voice_line(screen, sw, sh, cx, cy, line_idx, t, pt, phase)

        if phase == 5:
            self._draw_go_text(screen, sw, sh, cx, cy, pt)

        if self._shockwaves or self._bursts:
            fx_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for w in self._shockwaves:
                w.draw(fx_surf, shake_x, shake_y)
            for b in self._bursts:
                orig_x, orig_y = b.x, b.y
                b.x += shake_x
                b.y += shake_y
                b.draw(fx_surf)
                b.x, b.y = orig_x, orig_y
            screen.blit(fx_surf, (0, 0))

        if self._flash_alpha > 0:
            flash = pygame.Surface((sw, sh))
            flash.fill(WHITE_GLOW)
            flash.set_alpha(int(self._flash_alpha))
            screen.blit(flash, (0, 0))

        if phase == 0:
            screen.fill((0, 0, 0))
        elif phase == 7:
            fade_a = int(255 * ease_out_cubic(min(1.0, pt / _PHASE_DUR[7])))
            if fade_a > 0:
                ov = pygame.Surface((sw, sh))
                ov.fill((0, 0, 0))
                ov.set_alpha(fade_a)
                screen.blit(ov, (0, 0))

        if self._skip_surf and 1 <= phase <= 5:
            skip_a = int(130 * (0.5 + 0.5 * math.sin(t * 3.0)))
            self._skip_surf.set_alpha(max(0, min(200, skip_a)))
            screen.blit(
                self._skip_surf,
                (sw - self._skip_surf.get_width() - 20,
                 sh - self._skip_surf.get_height() - 16)
            )

    def _draw_nebula(self, screen, sw, sh, t, cx, cy):
        phase_shift = t * 0.15
        for (rx, ry_off, r, col, base_a) in [
            (0.35, -0.10, 0.40, (120, 20, 30), 25),
            (0.50,  0.15, 0.35, (80, 10, 20),  20),
            (-0.10, 0.05, 0.30, (160, 40, 50), 15),
        ]:
            ncx = int(cx + sw * rx * math.cos(phase_shift))
            ncy = int(cy + sh * ry_off + sh * 0.1 * math.sin(phase_shift * 2.0))
            nr  = int(min(sw, sh) * r)
            a   = int(base_a + 10 * math.sin(t * 0.8 + rx * 5))
            a   = max(0, min(50, a))
            ns  = pygame.Surface((nr * 2, nr * 2), pygame.SRCALPHA)
            pygame.draw.circle(ns, (*col, a), (nr, nr), nr)
            screen.blit(ns, (ncx - nr, ncy - nr))

    def _draw_centre_glow(self, screen, cx, cy, t, phase, pt):
        base_r = int(min(self._sw(), self._sh()) * 0.22)
        pulse  = 0.8 + 0.2 * math.sin(t * 3.0)
        
        if phase == 4:
            pulse += 0.3 * (pt / _PHASE_DUR[4]) # grows more intense
        elif phase == 5:
            pulse = 1.5 + 0.2 * math.sin(t * 15.0) # frantic
            
        r      = int(base_r * pulse)
        a_mult = min(1.0, pt / 1.0) if phase == 1 else 1.0
        if phase == 7:
            a_mult = max(0.0, 1.0 - pt / _PHASE_DUR[7])

        for ri in range(r, 0, -5):
            ratio = ri / r
            base_a = int(60 * (1.0 - ratio) * a_mult)
            col = (
                max(0, min(255, int(150 + 105 * (1 - ratio)))),
                max(0, min(255, int(20 +  60 * (1 - ratio)))),
                max(0, min(255, int(30 + 40 * (1 - ratio)))),
                max(0, min(80, base_a))
            )
            ns = pygame.Surface((ri * 2, ri * 2), pygame.SRCALPHA)
            pygame.draw.circle(ns, col, (ri, ri), ri)
            screen.blit(ns, (cx - ri, cy - ri))

    def _draw_voice_line(self, screen, sw, sh, cx, cy, line_idx, t, pt, phase):
        full_text = _VOICE_LINES[line_idx]
        shown_chars = int(self._tw_chars[line_idx])
        display = full_text[:shown_chars]

        lines = display.split("\n")
        lh = self._font_voice.get_height() + 4
        total_h = lh * len(lines)

        max_line_w = max((self._font_voice.size(ln)[0] for ln in full_text.split("\n")), default=1)
        pad_x, pad_y = int(50 * cfg.ui_scale()), int(30 * cfg.ui_scale())
        panel_w = min(max_line_w + pad_x * 2, sw - 80)
        panel_h = total_h + pad_y * 2 + int(40 * cfg.ui_scale())
        panel_x = cx - panel_w // 2
        panel_y = cy - panel_h // 2 + int(sh * 0.22)

        text_alpha = int(255 * min(1.0, pt / 0.3))

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (15, 2, 5, 210), (0, 0, panel_w, panel_h), border_radius=16)

        bord_a = int(180 + 75 * math.sin(t * 3.5))
        pygame.draw.rect(panel_surf, (*MYSTIC[:3], max(0, min(255, bord_a))),
                         (0, 0, panel_w, panel_h), max(2, int(3*cfg.ui_scale())), border_radius=16)

        tag_font = cfg.get_font(max(10, int(16 * cfg.ui_scale())))
        tag = tag_font.render("⟨ UNKNOWN ENTITY ⟩", True, (*GOLD_TEXT, 220))
        panel_surf.blit(tag, (panel_w // 2 - tag.get_width() // 2, 12))

        ty = pad_y + int(25 * cfg.ui_scale())
        for ln in lines:
            if not ln:
                ty += lh
                continue
            txt_surf = self._font_voice.render(ln, True, VOICE_CLR)
            
            # Glitch effect occasionally
            if random.random() < 0.05 and shown_chars >= len(full_text):
                glitch_surf = self._font_voice.render(ln, True, (255, 50, 50))
                panel_surf.blit(glitch_surf, (panel_w // 2 - txt_surf.get_width() // 2 + random.randint(-4, 4), ty + random.randint(-2, 2)))
            
            panel_surf.blit(txt_surf, (panel_w // 2 - txt_surf.get_width() // 2, ty))
            ty += lh

        panel_surf.set_alpha(text_alpha)
        screen.blit(panel_surf, (panel_x, panel_y))

        if shown_chars < len(full_text):
            if int(t * 6) % 2 == 0:
                cur_x = panel_x + panel_w // 2 + self._font_voice.size(lines[-1])[0] // 2 + 5
                cur_y = panel_y + pad_y + int(25 * cfg.ui_scale()) + (len(lines) - 1) * lh
                pygame.draw.rect(screen, (*GOLD_TEXT, 220),
                                 (cur_x, cur_y + 2, max(2, int(3 * cfg.ui_scale())), lh - 4))

    def _draw_go_text(self, screen, sw, sh, cx, cy, pt):
        text = _VOICE_LINES[2]
        shown_chars = int(self._tw_chars[2])
        display = text[:shown_chars]
        
        # huge, jittery text
        t_surf = self._font_go.render(display, True, (255, 50, 50))
        t_w = t_surf.get_width()
        t_h = t_surf.get_height()
        
        jitter_x = random.uniform(-5, 5)
        jitter_y = random.uniform(-5, 5)
        
        # Draw red shadow/glow
        glow = self._font_go.render(display, True, (200, 0, 0))
        glow.set_alpha(150)
        screen.blit(glow, (cx - t_w//2 + jitter_x * 2, cy - t_h//2 + jitter_y * 2))
        
        # Draw main text
        screen.blit(t_surf, (cx - t_w//2 + jitter_x, cy - t_h//2 + jitter_y))
