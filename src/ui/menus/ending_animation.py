import math
import random
import pygame
from typing import TYPE_CHECKING

import src.config as cfg
from src.ui.effects import ease_out_cubic, ease_in_quart
from src.core.logger import logger

if TYPE_CHECKING:
    from src.app import App

# Palette
GOLD_TEXT  = (255, 100, 50)
MYSTIC     = (180, 20, 50)
WHITE_GLOW = (255, 220, 220)
BLOOD_RED  = (200, 10, 10)
DARK_RED   = (80, 0, 0)
PALE_RED   = (255, 120, 100)

class _Vignette:
    """Radial vignette overlay that pulses with intensity."""
    def __init__(self):
        self._cache = {}
        self._last_sw = 0
        self._last_sh = 0
        self._base_surf = None

    def _ensure_base(self, sw, sh):
        if sw == self._last_sw and sh == self._last_sh and self._base_surf is not None:
            return
        self._last_sw, self._last_sh = sw, sh
        r = int(math.hypot(sw, sh) / 2)
        cx, cy = sw // 2, sh // 2
        self._base_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for radius in range(r, 0, -max(1, r // 40)):
            ratio = radius / r
            a = int(200 * ratio ** 2)
            if a < 1:
                continue
            pygame.draw.circle(self._base_surf, (0, 0, 0, min(255, a)),
                               (cx, cy), radius)

    def draw(self, screen, sw, sh, intensity):
        if intensity <= 0:
            return
        self._ensure_base(sw, sh)
        v = self._base_surf.copy()
        v.set_alpha(min(255, int(255 * min(1.0, intensity))))
        screen.blit(v, (0, 0))


class _GlowRing:
    """Expanding ring of light for dramatic flashes."""
    def __init__(self, cx, cy, max_radius, color, duration):
        self.cx = cx
        self.cy = cy
        self.max_radius = max_radius
        self.color = color
        self.duration = duration
        self.t = 0.0

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        if self.t >= self.duration:
            return
        progress = self.t / self.duration
        r = int(self.max_radius * ease_out_cubic(progress))
        a = int(60 * (1 - progress))
        if r < 2 or a < 2:
            return
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for ri in range(r, max(0, r - 12), -1):
            ratio = ri / r
            ca = int(a * (1 - ratio))
            pygame.draw.circle(s, (*self.color, ca), (r, r), ri)
        surf.blit(s, (self.cx - r, self.cy - r))


class _LightningStreak:
    """A jagged red lightning bolt with glow."""
    def __init__(self, cx, cy, sw, sh):
        self.cx = cx
        self.cy = cy
        self.sw = sw
        self.sh = sh
        self.life = random.uniform(0.15, 0.4)
        self.max_life = self.life
        self.points = self._generate()
        self.alpha = random.randint(80, 200)

    def _generate(self):
        pts = []
        x = random.uniform(0, self.sw)
        y = 0
        pts.append((x, y))
        segments = random.randint(5, 12)
        for _ in range(segments):
            x += random.uniform(-50, 50)
            y += self.sh / segments + random.uniform(-25, 25)
            pts.append((x, y))
        return pts

    def update(self, dt):
        self.life -= dt

    def draw(self, surf):
        if self.life <= 0:
            return
        ratio = self.life / self.max_life
        a = int(self.alpha * ratio)
        w = max(1, int(4 * ratio))
        if a < 3:
            return
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            for thickness, offset, alpha_factor in [(w + 2, 0, 0.3), (w, -1, 0.6), (w, 1, 0.6), (max(1, w - 1), 0, 1.0)]:
                ca = int(a * alpha_factor)
                if ca < 2:
                    continue
                pygame.draw.line(surf, (255, 50, 50, ca),
                                 (p1[0] + offset, p1[1] + offset),
                                 (p2[0] + offset, p2[1] + offset),
                                 thickness)


class _BloodParticle:
    def __init__(self, x, y, speed_mult=1.0):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(80, 350) * speed_mult
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.uniform(0.8, 3.0)
        self.max_life = self.life
        self.size = random.uniform(2, 8)
        self.color = random.choice([
            (180, 0, 0), (220, 20, 20), (120, 0, 0),
            (200, 50, 30), (160, 10, 10)
        ])
        self.trail: list[tuple[float, float, float]] = []

    def update(self, dt):
        self.trail.append((self.x, self.y, self.size))
        if len(self.trail) > 4:
            self.trail.pop(0)
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 60 * dt
        self.vx *= 0.97
        self.life -= dt

    def draw(self, surf):
        if self.life <= 0:
            return
        ratio = self.life / self.max_life
        a = int(200 * ratio)
        sz = max(1, int(self.size * (0.3 + 0.7 * ratio)))
        for i, (tx, ty, ts) in enumerate(self.trail):
            ta = int(a * 0.3 * (i / len(self.trail)))
            tsz = max(1, int(ts * 0.5 * (i / len(self.trail))))
            pygame.draw.circle(surf, (*self.color, ta),
                               (int(tx), int(ty)), tsz)
        pygame.draw.circle(surf, (*self.color, a),
                           (int(self.x), int(self.y)), sz)
        glow_sz = sz + 3
        if glow_sz > sz:
            pygame.draw.circle(surf, (*self.color, int(a * 0.2)),
                               (int(self.x), int(self.y)), glow_sz)


class _EmberParticle:
    """Slowly rising ember with warm glow."""
    def __init__(self, sw, sh):
        self.x = random.uniform(0, sw)
        self.y = random.uniform(sh * 0.5, sh + 20)
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-30, -10)
        self.life = random.uniform(2.0, 5.0)
        self.max_life = self.life
        self.size = random.uniform(1.5, 4.0)
        self.color = random.choice([
            (255, 180, 80), (255, 120, 40), (200, 80, 20),
            (255, 200, 100), (180, 60, 20)
        ])
        self._phase = random.uniform(0, 2 * math.pi)

    def update(self, dt, t):
        self.x += self.vx * dt + math.sin(t * 0.5 + self._phase) * 8 * dt
        self.y += self.vy * dt
        self.life -= dt
        if self.life <= 0 or self.y < -20:
            self.life = random.uniform(2.0, 5.0)
            self.max_life = self.life
            self.x = random.uniform(0, 1920)
            self.y = random.uniform(500, 1100)
            self.vy = random.uniform(-30, -10)

    def draw(self, surf, t):
        if self.life <= 0:
            return
        ratio = self.life / self.max_life
        a = int(100 * ratio * (0.6 + 0.4 * math.sin(t * 2 + self._phase)))
        sz = max(0.5, self.size * ratio)
        glow_sz = int(sz * 3)
        s = pygame.Surface((glow_sz * 2 + 1, glow_sz * 2 + 1), pygame.SRCALPHA)
        for r in range(glow_sz, 0, -1):
            ca = int(a * (1 - r / glow_sz) * 0.5)
            if ca > 0:
                pygame.draw.circle(s, (*self.color, ca),
                                   (glow_sz, glow_sz), r)
        pygame.draw.circle(s, (*self.color, a),
                           (glow_sz, glow_sz), max(1, int(sz)))
        surf.blit(s, (int(self.x) - glow_sz, int(self.y) - glow_sz))


class EndingAnimation:
    def __init__(self, app: "App"):
        self.app = app
        self._phase = 0
        self._phase_t = 0.0
        self._t = 0.0
        self._done = False
        self._skip_requested = False

        self._blood_parts: list[_BloodParticle] = []
        self._lightnings: list[_LightningStreak] = []
        self._embers: list[_EmberParticle] = []
        self._glow_rings: list[_GlowRing] = []

        self._tw_chars = [0.0, 0.0]
        self._tw_speed = 25.0
        self._tw_hold = [0.0, 0.0]

        self._font_voice = cfg.get_font(max(24, int(44 * cfg.ui_scale())))
        self._font_skip = cfg.get_font(max(10, int(16 * cfg.ui_scale())))

        self._flash_alpha = 0.0
        self._shake_intensity = 0.0
        self._shake_offset_x = 0.0
        self._shake_offset_y = 0.0
        self._shake_phase = 0.0

        self._bg_pulse_phase = 0.0
        self._cached_sw = 0
        self._cached_sh = 0
        self._bg_glow_surf = None
        self._bp_surf = None
        self._lt_surf = None
        self._em_surf = None
        self._gr_surf = None
        self._flash_surf = None
        self._ov_surf = None

        self._vignette = _Vignette()

        self._voice_lines = [
            '"HAHAHAHA, FINALLY. I\'M FREE."',
            '"To be continued...?"'
        ]
        self._phase_dur = [
            2.0,
            4.0,
            5.0,
            4.0,
            3.0
        ]

    def on_enter(self):
        self._phase = 0
        self._phase_t = 0.0
        self._t = 0.0
        self._done = False
        self._skip_requested = False
        self._flash_alpha = 0.0
        self._shake_intensity = 0.0
        self._shake_offset_x = 0.0
        self._shake_offset_y = 0.0
        self._shake_phase = 0.0
        self._bg_pulse_phase = 0.0
        self._blood_parts.clear()
        self._lightnings.clear()
        self._embers.clear()
        self._glow_rings.clear()
        self._tw_chars = [0.0, 0.0]
        self._tw_hold = [0.0, 0.0]

        sw, sh = self.app.screen.get_width(), self.app.screen.get_height()
        self._embers = [_EmberParticle(sw, sh) for _ in range(30)]

        self._skip_surf = self._font_skip.render(
            "SPACE / ENTER \u2014 skip", True, (200, 50, 50))
        logger.info("[EndingAnimation] Sequence started.")

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                self._skip_requested = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._skip_requested = True

    def _update_shake(self, dt):
        self._shake_phase += dt * 8.0
        intensity = self._shake_intensity
        if intensity < 0.5:
            self._shake_offset_x = 0.0
            self._shake_offset_y = 0.0
            return
        t = self._shake_phase
        self._shake_offset_x = math.sin(t) * intensity * 0.7 + math.sin(t * 2.3) * intensity * 0.3
        self._shake_offset_y = math.cos(t * 1.7) * intensity * 0.7 + math.sin(t * 2.9) * intensity * 0.3

    def update(self, dt):
        self._t += dt
        self._phase_t += dt
        self._bg_pulse_phase += dt

        sw, sh = self.app.screen.get_width(), self.app.screen.get_height()
        cx, cy = sw // 2, sh // 2

        for em in self._embers:
            em.update(dt, self._t)

        if self._skip_requested and self._phase < 4:
            self._phase = 4
            self._phase_t = 0.0
            self._skip_requested = False

        if self._phase == 4 and self._phase_t >= self._phase_dur[4]:
            if not self._done:
                self._done = True
                logger.info("[EndingAnimation] Sequence complete \u2192 switching to main menu.")
                self.app.manager.set_state("main")
            return

        if self._phase in (2, 3):
            vp = self._phase - 2
            line_len = len(self._voice_lines[vp])
            self._tw_chars[vp] = min(line_len, self._tw_chars[vp] + self._tw_speed * dt)
            if self._tw_chars[vp] >= line_len:
                self._tw_hold[vp] += dt

        ready_to_advance = False
        if self._phase in (2, 3):
            vp = self._phase - 2
            ready_to_advance = (self._tw_chars[vp] >= len(self._voice_lines[vp])) and (self._tw_hold[vp] >= 1.5)
        else:
            ready_to_advance = self._phase_t >= self._phase_dur[self._phase]

        if ready_to_advance:
            self._phase_t = 0.0
            self._phase += 1
            if self._phase == 2:
                self._flash_alpha = 255.0
                self._glow_rings.append(_GlowRing(cx, cy, max(sw, sh) * 0.8, (255, 80, 50), 1.0))
                for _ in range(80):
                    self._blood_parts.append(_BloodParticle(cx, cy, 2.5))
                logger.info("[EndingAnimation] First voice line triggered.")
            if self._phase == 3:
                self._flash_alpha = 120.0
                self._glow_rings.append(_GlowRing(cx, cy, max(sw, sh) * 0.5, (200, 180, 180), 0.8))
                for _ in range(30):
                    self._blood_parts.append(_BloodParticle(cx, cy, 1.5))

        # Chaotic elements
        if self._phase >= 1 and self._phase < 4:
            spawn_rate = 0.25 if self._phase == 1 else (0.35 if self._phase == 2 else 0.15)
            if random.random() < spawn_rate:
                self._lightnings.append(_LightningStreak(cx, cy, sw, sh))
            blood_rate = 0.4 if self._phase == 1 else (0.5 if self._phase == 2 else 0.2)
            if random.random() < blood_rate:
                self._blood_parts.append(
                    _BloodParticle(
                        cx + random.uniform(-300, 300),
                        cy + random.uniform(-300, 300),
                        random.uniform(0.5, 1.5)
                    )
                )
            if self._phase == 1 and random.random() < 0.1:
                self._glow_rings.append(
                    _GlowRing(
                        random.uniform(0, sw), random.uniform(0, sh),
                        random.uniform(80, 200), random.choice([(180, 20, 20), (100, 0, 0)]),
                        random.uniform(0.3, 0.8)
                    )
                )

        # Phase 0 subtle buildup
        if self._phase == 0 and random.random() < 0.3:
            self._blood_parts.append(
                _BloodParticle(
                    cx + random.uniform(-400, 400),
                    cy + random.uniform(-200, 200),
                    random.uniform(0.3, 0.8)
                )
            )

        self._lightnings = [l for l in self._lightnings if l.life > 0]
        for l in self._lightnings:
            l.update(dt)

        self._blood_parts = [bp for bp in self._blood_parts if bp.life > 0]
        for bp in self._blood_parts:
            bp.update(dt)

        self._glow_rings = [gr for gr in self._glow_rings if gr.t < gr.duration]
        for gr in self._glow_rings:
            gr.update(dt)

        if self._flash_alpha > 0:
            self._flash_alpha = max(0.0, self._flash_alpha - dt * 120)

        # Shake intensity with easing
        if self._phase == 0:
            self._shake_intensity = 0.0
        elif self._phase == 1:
            progress = self._phase_t / self._phase_dur[1]
            self._shake_intensity = 15.0 * ease_in_quart(progress)
        elif self._phase == 2:
            hold_t = min(self._phase_t, 2.0)
            self._shake_intensity = 35.0 * (1.0 - 0.3 * (hold_t / 2.0))
        elif self._phase == 3:
            self._shake_intensity = max(0.0, 12.0 * (1.0 - ease_out_cubic(self._phase_t / self._phase_dur[3])))
        elif self._phase == 4:
            self._shake_intensity = max(0.0, 8.0 * (1.0 - ease_out_cubic(self._phase_t / self._phase_dur[4])))
        else:
            self._shake_intensity = 0.0

        self._update_shake(dt)

    def _ensure_surfaces(self, sw, sh):
        if sw == self._cached_sw and sh == self._cached_sh:
            return
        self._cached_sw, self._cached_sh = sw, sh
        self._bg_glow_surf = pygame.Surface((sw, sh))
        self._bp_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._lt_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._em_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._gr_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
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

        # Deep dark red background
        if phase == 0:
            screen.fill((0, 0, 0))
        else:
            r_val = int(5 + 20 * (phase / 4))
            screen.fill((min(25, r_val), 0, 0))

        # Background pulse glow
        if phase >= 1:
            pulse = math.sin(self._bg_pulse_phase * 6) * 0.5 + 0.5
            pulse = ease_out_cubic(pulse)
            if phase == 2:
                glow_color = (60, 15, 10)
                glow_alpha = int(140 * pulse)
            elif phase == 3:
                glow_color = (40, 10, 15)
                glow_alpha = int(80 * pulse)
            else:
                glow_color = (30, 5, 0)
                glow_alpha = int(60 * pulse)
            self._bg_glow_surf.fill(glow_color)
            self._bg_glow_surf.set_alpha(glow_alpha)
            screen.blit(self._bg_glow_surf, (0, 0))

        # Draw embers (behind everything)
        if self._embers:
            self._em_surf.fill((0, 0, 0, 0))
            for em in self._embers:
                orig_x, orig_y = em.x, em.y
                em.x += sx
                em.y += sy
                em.draw(self._em_surf, t)
                em.x, em.y = orig_x, orig_y
            screen.blit(self._em_surf, (0, 0))

        # Draw glow rings (behind blood)
        if self._glow_rings:
            self._gr_surf.fill((0, 0, 0, 0))
            for gr in self._glow_rings:
                gr.draw(self._gr_surf)
            screen.blit(self._gr_surf, (0, 0))

        # Draw blood particles
        if self._blood_parts:
            self._bp_surf.fill((0, 0, 0, 0))
            for bp in self._blood_parts:
                orig_x, orig_y = bp.x, bp.y
                bp.x += sx
                bp.y += sy
                bp.draw(self._bp_surf)
                bp.x, bp.y = orig_x, orig_y
            screen.blit(self._bp_surf, (0, 0))

        # Draw lightning
        if self._lightnings:
            self._lt_surf.fill((0, 0, 0, 0))
            for l in self._lightnings:
                l.draw(self._lt_surf)
            screen.blit(self._lt_surf, (0, 0))

        # Draw voice lines
        if phase in (2, 3):
            line_idx = phase - 2
            self._draw_voice_line(screen, sw, sh, cx, cy, line_idx, t, pt, sx, sy)

        # Flash overlay
        if self._flash_alpha > 0:
            flash_ratio = self._flash_alpha / 255.0
            r = int(255 * flash_ratio)
            g = int(80 * flash_ratio * flash_ratio)
            b = int(50 * flash_ratio * flash_ratio * flash_ratio)
            self._flash_surf.fill((r, g, b))
            self._flash_surf.set_alpha(min(255, int(self._flash_alpha)))
            screen.blit(self._flash_surf, (0, 0))

        # Vignette
        vignette_intensity = 0.0
        if phase == 1:
            vignette_intensity = 0.3 + 0.4 * (pt / self._phase_dur[1])
        elif phase == 2:
            vignette_intensity = 0.7
        elif phase == 3:
            vignette_intensity = 0.5
        elif phase == 4:
            vignette_intensity = 0.2 * (1.0 - pt / self._phase_dur[4])
        self._vignette.draw(screen, sw, sh, vignette_intensity)

        # Phase 0 overlay
        if phase == 0:
            progress = pt / self._phase_dur[0]
            fade_in = ease_in_quart(progress)
            self._ov_surf.fill((0, 0, 0))
            self._ov_surf.set_alpha(int(255 * (1.0 - fade_in)))
            screen.blit(self._ov_surf, (0, 0))

        # Phase 4 fade to black
        if phase == 4:
            fade_a = int(255 * ease_out_cubic(pt / self._phase_dur[4]))
            fade_a = max(0, min(255, fade_a))
            self._ov_surf.fill((0, 0, 0))
            self._ov_surf.set_alpha(fade_a)
            screen.blit(self._ov_surf, (0, 0))

        # Skip text
        if self._skip_surf and 1 <= phase <= 3:
            skip_a = int(130 * (0.5 + 0.5 * math.sin(t * 4.0)))
            self._skip_surf.set_alpha(max(0, min(200, skip_a)))
            screen.blit(
                self._skip_surf,
                (sw - self._skip_surf.get_width() - 20,
                 sh - self._skip_surf.get_height() - 16)
            )

    def _draw_voice_line(self, screen, sw, sh, cx, cy, line_idx, t, pt, sx, sy):
        full_text = self._voice_lines[line_idx]
        shown_chars = int(self._tw_chars[line_idx])
        display = full_text[:shown_chars]

        if line_idx == 0:
            color = (255, 30, 30)
            glow_color = (255, 80, 50)
        else:
            color = (220, 220, 220)
            glow_color = (200, 200, 255)

        t_surf = self._font_voice.render(display, True, color)
        t_w = t_surf.get_width()
        t_h = t_surf.get_height()

        px = cx - t_w // 2 + sx
        py = cy - t_h // 2 + sy

        text_complete = shown_chars >= len(full_text)

        # Text glow aura (render once, blit at offsets)
        if text_complete:
            glow_text = self._font_voice.render(display, True, glow_color)
            glow_surf = pygame.Surface((t_w + 20, t_h + 20), pygame.SRCALPHA)
            for r in range(8, 0, -1):
                ga = int(20 * (1 - r / 8) * (0.7 + 0.3 * math.sin(t * 3)))
                gs = glow_text.copy()
                gs.set_alpha(ga)
                glow_surf.blit(gs, (10 + r, 10 + r))
                glow_surf.blit(gs, (10 - r, 10 - r))
                glow_surf.blit(gs, (10, 10 + r))
                glow_surf.blit(gs, (10, 10 - r))
            screen.blit(glow_surf, (px - 10, py - 10))

        # Glitch effect when fully revealed
        if text_complete:
            glitch_count = 4 if line_idx == 0 else 2
            for _ in range(glitch_count):
                g_x = px + random.randint(-6, 6)
                g_y = py + random.randint(-6, 6)
                g_col = random.choice([
                    (255, 0, 0), (100, 0, 0), (50, 0, 0),
                    (200, 50, 50), (255, 100, 80)
                ]) if line_idx == 0 else random.choice([
                    (200, 200, 200), (100, 100, 100), (50, 50, 50)
                ])
                g_surf = self._font_voice.render(display, True, g_col)
                g_surf.set_alpha(random.randint(30, 100))
                screen.blit(g_surf, (g_x, g_y))

        # Main text
        screen.blit(t_surf, (px, py))

        # Cursor blink during typing
        if not text_complete:
            cursor_visible = int(t * 8) % 2 == 0
            if cursor_visible:
                cursor_x = px + t_surf.get_width() + 2
                cursor_y = py
                cursor_h = t_h
                cursor_surf = pygame.Surface((3, cursor_h), pygame.SRCALPHA)
                cursor_surf.fill((*color[:3], 200))
                screen.blit(cursor_surf, (cursor_x, cursor_y))
