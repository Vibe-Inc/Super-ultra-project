from __future__ import annotations

import math
import random

import pygame

from src.entities.enemy import Enemy
from src.core.logger import logger


class ChronosIntro:
    """
    Majestic cinematic intro that plays when the player first approaches Chronos.

    Phases:
        0  – Screen darkens, player frozen (0.0 – 1.0 s)
        1  – Camera pans to Chronos, cosmic particles burst (1.0 – 3.0 s)
        2  – Boss name + title appear with golden glow (3.0 – 5.0 s)
        3  – Chronos rises, aura expands, screen shakes (5.0 – 6.5 s)
        4  – Flash, fade back to normal, fight begins (6.5 – 8.0 s)
    """

    DURATION = 8.0

    def __init__(self, boss_pos: pygame.Vector2, screen_size: tuple[int, int]):
        self.boss_pos = boss_pos.copy()
        self.screen_w, self.screen_h = screen_size
        self.elapsed = 0.0
        self.finished = False
        self._overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
        self._shake_intensity = 0.0
        self._shake_offset = pygame.Vector2(0, 0)

    def update(self, dt: float):
        self.elapsed += dt
        if self.elapsed >= self.DURATION:
            self.finished = True
        if self.elapsed > 5.0:
            progress = min(1.0, (self.elapsed - 5.0) / 1.5)
            self._shake_intensity = 8.0 * (1.0 - progress)
        elif self.elapsed > 4.5:
            self._shake_intensity = 6.0 + (self.elapsed - 4.5) * 8.0

    def get_shake_offset(self) -> pygame.Vector2:
        if self._shake_intensity <= 0:
            return pygame.Vector2(0, 0)
        import random
        self._shake_offset = pygame.Vector2(
            random.uniform(-self._shake_intensity, self._shake_intensity),
            random.uniform(-self._shake_intensity, self._shake_intensity),
        )
        return self._shake_offset

    def draw_overlay(self, screen: pygame.Surface):
        """Draw dark backdrop, particles, effects (rendered behind entities)."""
        if self.finished:
            return
        t = self.elapsed
        w, h = self.screen_w, self.screen_h

        # --- Phase 0: darkening (0-1s) ---
        if t < 1.0:
            alpha = int(200 * t)
            self._overlay.fill((5, 2, 15, alpha))
            screen.blit(self._overlay, (0, 0))
            return

        # --- Phases 1-4: full darkness backdrop with effects ---
        self._overlay.fill((5, 2, 15, 210))
        screen.blit(self._overlay, (0, 0))

        cx, cy = w // 2, h // 2

        # --- Phase 1: cosmic particle burst + boss silhouette (1-3s) ---
        if t < 3.0:
            burst_progress = (t - 1.0) / 2.0
            # Expanding cosmic ring
            ring_r = int(50 + burst_progress * 250)
            ring_alpha = int(180 * (1.0 - burst_progress * 0.5))
            ring_surf = pygame.Surface((ring_r * 2, ring_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (180, 140, 60, ring_alpha // 2), (ring_r, ring_r), ring_r, 2)
            pygame.draw.circle(ring_surf, (220, 180, 80, ring_alpha // 3), (ring_r, ring_r), ring_r - 5, 1)
            screen.blit(ring_surf, (cx - ring_r, cy - ring_r), special_flags=pygame.BLEND_ALPHA_SDL2)

            # Burst particles
            for pi in range(12):
                angle = pi * (math.pi * 2 / 12) + burst_progress * 0.5
                dist = 30 + burst_progress * 180
                px = cx + int(math.cos(angle) * dist)
                py = cy + int(math.sin(angle) * dist)
                pa = int(200 * (1.0 - burst_progress * 0.6))
                ps = max(1, int(4 - burst_progress * 2))
                pygame.draw.circle(screen, (220, 180, 80, pa), (px, py), ps)

            # Boss silhouette (dark shape growing)
            sil_alpha = int(200 * min(1.0, burst_progress * 1.5))
            sil_size = int(30 + burst_progress * 50)
            sil_surf = pygame.Surface((sil_size * 2, sil_size * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(sil_surf, (25, 15, 50, sil_alpha), (0, 0, sil_size * 2, sil_size * 2))
            screen.blit(sil_surf, (cx - sil_size, cy - sil_size), special_flags=pygame.BLEND_ALPHA_SDL2)

        # --- Phase 3: Rise + aura expand (5-6.5s) ---
        elif t >= 5.0 and t < 6.5:
            rise_progress = (t - 5.0) / 1.5
            # Massive expanding aura
            aura_r = int(80 + rise_progress * 200)
            aura_alpha = int(150 * (1.0 - rise_progress * 0.3))
            aura_surf = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, (220, 180, 60, aura_alpha // 3), (aura_r, aura_r), aura_r)
            pygame.draw.circle(aura_surf, (180, 140, 50, aura_alpha // 2), (aura_r, aura_r), aura_r // 2)
            screen.blit(aura_surf, (cx - aura_r, cy - aura_r), special_flags=pygame.BLEND_ALPHA_SDL2)

            # Runes orbiting
            for ri in range(8):
                angle = rise_progress * math.pi * 2 + ri * (math.pi * 2 / 8)
                rr = 100 + int(rise_progress * 60)
                rx = cx + int(math.cos(angle) * rr)
                ry = cy + int(math.sin(angle) * rr)
                rs = 4
                pygame.draw.polygon(screen, (220, 180, 60, 200),
                    [(rx, ry - rs), (rx + rs, ry), (rx, ry + rs), (rx - rs, ry)])

        # --- Phase 4: Flash + fade (6.5-8s) ---
        elif t >= 6.5:
            flash_progress = (t - 6.5) / 1.5
            if flash_progress < 0.2:
                flash_alpha = int(255 * (1.0 - flash_progress / 0.2))
                flash_surf = pygame.Surface((w, h), pygame.SRCALPHA)
                flash_surf.fill((255, 230, 150, flash_alpha))
                screen.blit(flash_surf, (0, 0))
            else:
                fade_alpha = int(210 * (1.0 - (flash_progress - 0.2) / 0.8))
                self._overlay.fill((5, 2, 15, fade_alpha))
                screen.blit(self._overlay, (0, 0))

    def draw_text(self, screen: pygame.Surface):
        """Draw boss name + title (rendered over entities)."""
        if self.finished:
            return
        t = self.elapsed
        w, h = self.screen_w, self.screen_h
        cx, cy = w // 2, h // 2

        # --- Phase 2: Name + Title appear (3-5s) ---
        if 3.0 <= t < 5.0:
            name_progress = (t - 3.0) / 2.0
            self._draw_boss_title(screen, cx, cy, name_progress)
        # --- Phase 3: Name still visible (fading) ---
        elif 5.0 <= t < 6.5:
            self._draw_boss_title(screen, cx, cy, 1.0)

    def _draw_boss_title(self, screen, cx, cy, progress):
        # "CHRONOS" main title
        try:
            title_font = pygame.font.SysFont("arial", 36, bold=True)
            sub_font = pygame.font.SysFont("arial", 16, bold=True)
        except Exception:
            title_font = pygame.font.Font(None, 42)
            sub_font = pygame.font.Font(None, 20)

        alpha = int(255 * min(1.0, progress * 2))
        if progress > 0.8:
            alpha = int(255 * (1.0 - (progress - 0.8) / 0.2))

        # Title glow
        title_surf = title_font.render("CHRONOS", True, (255, 220, 100))
        title_surf.set_alpha(alpha)
        title_x = cx - title_surf.get_width() // 2
        title_y = cy - 40

        # Glow behind title
        glow_surf = title_font.render("CHRONOS", True, (200, 160, 50))
        glow_surf.set_alpha(alpha // 2)
        for gx, gy in [(-2, -1), (2, -1), (-1, 2), (1, -2)]:
            screen.blit(glow_surf, (title_x + gx, title_y + gy), special_flags=pygame.BLEND_ALPHA_SDL2)
        screen.blit(title_surf, (title_x, title_y))

        # Subtitle
        sub_surf = sub_font.render("The Chronicler of Time", True, (180, 150, 220))
        sub_surf.set_alpha(int(220 * min(1.0, max(0, progress * 2 - 1))))
        if progress > 0.8:
            sub_surf.set_alpha(int(220 * (1.0 - (progress - 0.8) / 0.2)))
        sub_x = cx - sub_surf.get_width() // 2
        sub_y = cy - 5
        screen.blit(sub_surf, (sub_x, sub_y))

        # Decorative lines
        line_alpha = int(180 * min(1.0, progress * 1.5))
        line_w = int(120 * min(1.0, progress * 1.5))
        line_y = cy + 18
        pygame.draw.line(screen, (200, 170, 60, line_alpha), (cx - line_w, line_y), (cx - 10, line_y), 1)
        pygame.draw.line(screen, (200, 170, 60, line_alpha), (cx + 10, line_y), (cx + line_w, line_y), 1)
        # Diamond center
        pygame.draw.polygon(screen, (220, 180, 60, line_alpha),
            [(cx, line_y - 4), (cx + 4, line_y), (cx, line_y + 4), (cx - 4, line_y)])


class BossPhaseTransition:
    """
    Majestic cinematic transition between boss phases.

    Each phase transition has a unique visual theme:
        Phase 2 (Time Fractures):   Clock shards burst outward, temporal distortion field,
                                    gold-to-amber color shift, shockwave ring.
        Phase 3 (Chronos Awakens):  Reality cracks, chains shatter, dark purple aura,
                                    inverted gravity particles, screen warps.
        Phase 4 (The Final Hour):   Crimson overload, massive temporal shockwave,
                                    all particles reverse, boss silhouette transforms.

    Phases of the transition animation:
        0  – Screen darkens, player frozen, boss pulses (0.0 – 0.8 s)
        1  – Main effect burst (shards / cracks / crimson surge) (0.8 – 2.2 s)
        2  – Aura transformation + color shift (2.2 – 3.0 s)
        3  – Flash + fade, new phase begins (3.0 – 3.8 s)
    """

    DURATION = 3.8

    PHASE_THEMES = {
        2: {
            "name": "TIME FRACTURES",
            "subtitle": "The clock shatters...",
            "darken_color": (15, 10, 30),
            "flash_color": (255, 210, 80),
            "aura_color_inner": (220, 180, 60),
            "aura_color_outer": (180, 140, 30),
            "particle_color": (255, 220, 90),
            "ring_color": (200, 170, 50),
        },
        3: {
            "name": "CHRONOS AWAKENS",
            "subtitle": "Reality fractures...",
            "darken_color": (10, 5, 25),
            "flash_color": (180, 120, 255),
            "aura_color_inner": (160, 80, 220),
            "aura_color_outer": (100, 40, 180),
            "particle_color": (200, 140, 255),
            "ring_color": (140, 80, 200),
        },
        4: {
            "name": "THE FINAL HOUR",
            "subtitle": "Time itself breaks...",
            "darken_color": (20, 2, 5),
            "flash_color": (255, 60, 40),
            "aura_color_inner": (220, 40, 30),
            "aura_color_outer": (160, 20, 15),
            "particle_color": (255, 80, 50),
            "ring_color": (200, 50, 30),
        },
    }

    def __init__(self, boss_pos: pygame.Vector2, screen_size: tuple[int, int], to_phase: int):
        self.boss_pos = boss_pos.copy()
        self.screen_w, self.screen_h = screen_size
        self.to_phase = to_phase
        self.elapsed = 0.0
        self.finished = False
        self._overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
        self._shake_intensity = 0.0
        self._shake_offset = pygame.Vector2(0, 0)
        self._shard_particles = []
        self._ring_particles = []
        self._warp_particles = []
        self._theme = self.PHASE_THEMES.get(to_phase, self.PHASE_THEMES[2])
        self._spawn_initial_particles()

    def _spawn_initial_particles(self):
        cx, cy = self.screen_w // 2, self.screen_h // 2
        for _ in range(24):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(80, 250)
            self._shard_particles.append({
                "x": float(cx), "y": float(cy),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "size": random.uniform(3, 8),
                "life": 1.0,
                "rotation": random.uniform(0, math.pi * 2),
                "rot_speed": random.uniform(-6, 6),
            })
        for _ in range(16):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(40, 120)
            self._ring_particles.append({
                "x": float(cx), "y": float(cy),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "size": random.uniform(2, 5),
                "life": 1.0,
                "delay": random.uniform(0.0, 0.4),
            })
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(20, 80)
            self._warp_particles.append({
                "x": cx + math.cos(angle) * dist,
                "y": cy + math.sin(angle) * dist,
                "base_angle": angle,
                "base_dist": dist,
                "size": random.uniform(1.5, 4),
                "life": 1.0,
                "speed": random.uniform(1.0, 3.0),
            })

    def update(self, dt: float):
        self.elapsed += dt
        if self.elapsed >= self.DURATION:
            self.finished = True
            return
        t = self.elapsed
        if t < 0.8:
            self._shake_intensity = 3.0 + t * 5.0
        elif t < 2.2:
            self._shake_intensity = 8.0 + math.sin((t - 0.8) * 8) * 4.0
        elif t < 3.0:
            progress = (t - 2.2) / 0.8
            self._shake_intensity = 8.0 * (1.0 - progress)
        else:
            self._shake_intensity = 0.0
        for p in self._shard_particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vx"] *= 0.97
            p["vy"] *= 0.97
            p["rotation"] += p["rot_speed"] * dt
            if t > 0.8:
                p["life"] -= dt * 1.5
        for p in self._ring_particles:
            if t > p["delay"]:
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["vx"] *= 0.92
                p["vy"] *= 0.92
                if t > 1.0:
                    p["life"] -= dt * 1.2
        for p in self._warp_particles:
            p["base_angle"] += p["speed"] * dt
            wobble = math.sin(t * 4 + p["base_angle"] * 2) * 15
            new_dist = p["base_dist"] + wobble
            cx, cy = self.screen_w // 2, self.screen_h // 2
            p["x"] = cx + math.cos(p["base_angle"]) * new_dist
            p["y"] = cy + math.sin(p["base_angle"]) * new_dist
            if t > 1.5:
                p["life"] -= dt * 0.8

    def get_shake_offset(self) -> pygame.Vector2:
        if self._shake_intensity <= 0:
            return pygame.Vector2(0, 0)
        self._shake_offset = pygame.Vector2(
            random.uniform(-self._shake_intensity, self._shake_intensity),
            random.uniform(-self._shake_intensity, self._shake_intensity),
        )
        return self._shake_offset

    def draw_overlay(self, screen: pygame.Surface):
        if self.finished:
            return
        t = self.elapsed
        w, h = self.screen_w, self.screen_h
        cx, cy = w // 2, h // 2
        theme = self._theme
        dc = theme["darken_color"]
        fc = theme["flash_color"]
        aci = theme["aura_color_inner"]
        aco = theme["aura_color_outer"]
        pc = theme["particle_color"]
        rc = theme["ring_color"]

        if t < 0.8:
            alpha = int(220 * (t / 0.8))
            self._overlay.fill((*dc, alpha))
            screen.blit(self._overlay, (0, 0))
            pulse_r = int(40 + t * 80)
            pulse_a = int(120 * (t / 0.8))
            ring_surf = pygame.Surface((pulse_r * 2, pulse_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (*aci, pulse_a // 2), (pulse_r, pulse_r), pulse_r, 2)
            pygame.draw.circle(ring_surf, (*aco, pulse_a // 3), (pulse_r, pulse_r), pulse_r - 4, 1)
            screen.blit(ring_surf, (cx - pulse_r, cy - pulse_r), special_flags=pygame.BLEND_ALPHA_SDL2)
            return

        self._overlay.fill((*dc, 220))
        screen.blit(self._overlay, (0, 0))

        if 0.8 <= t < 2.2:
            burst_t = (t - 0.8) / 1.4
            main_r = int(burst_t * 400)
            main_a = int(180 * (1.0 - burst_t * 0.6))
            ring_surf = pygame.Surface((main_r * 2, main_r * 2), pygame.SRCALPHA)
            ring_w = max(1, int(6 * (1.0 - burst_t)))
            pygame.draw.circle(ring_surf, (*rc, main_a), (main_r, main_r), main_r, ring_w)
            pygame.draw.circle(ring_surf, (*aci, main_a // 2), (main_r, main_r), main_r - 8, max(1, ring_w - 1))
            screen.blit(ring_surf, (cx - main_r, cy - main_r), special_flags=pygame.BLEND_ALPHA_SDL2)

            if burst_t < 0.4:
                flash_a = int(100 * (1.0 - burst_t / 0.4))
                flash_surf = pygame.Surface((w, h), pygame.SRCALPHA)
                flash_surf.fill((*fc, flash_a))
                screen.blit(flash_surf, (0, 0))

            for p in self._shard_particles:
                if p["life"] <= 0:
                    continue
                sa = int(220 * p["life"])
                sz = max(1, int(p["size"] * p["life"]))
                s_surf = pygame.Surface((sz * 2 + 4, sz * 2 + 4), pygame.SRCALPHA)
                angle = p["rotation"]
                pts = []
                for j in range(4):
                    pr = sz * (1.5 if j % 2 == 0 else 0.6)
                    pa2 = angle + j * (math.pi * 2 / 4)
                    pts.append((sz + 2 + math.cos(pa2) * pr, sz + 2 + math.sin(pa2) * pr))
                pygame.draw.polygon(s_surf, (*pc, sa), pts)
                pygame.draw.polygon(s_surf, (*fc, sa // 2), pts, 1)
                screen.blit(s_surf, (int(p["x"]) - sz - 2, int(p["y"]) - sz - 2))

            for p in self._ring_particles:
                if p["life"] <= 0:
                    continue
                ra = int(160 * p["life"])
                rs = max(1, int(p["size"] * p["life"]))
                r_surf = pygame.Surface((rs * 2, rs * 2), pygame.SRCALPHA)
                pygame.draw.circle(r_surf, (*pc, ra), (rs, rs), rs)
                screen.blit(r_surf, (int(p["x"]) - rs, int(p["y"]) - rs))

        if 0.8 <= t < 3.0:
            aura_t = min(1.0, (t - 0.8) / 1.5)
            for ring_i in range(6):
                ring_r = int(60 + aura_t * 180 + ring_i * 15)
                ring_a = max(5, int(50 * (1.0 - aura_t * 0.4) - ring_i * 6))
                aura_surf = pygame.Surface((ring_r * 2, ring_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(aura_surf, (*aci, ring_a), (ring_r, ring_r), ring_r, 1)
                screen.blit(aura_surf, (cx - ring_r, cy - ring_r), special_flags=pygame.BLEND_ALPHA_SDL2)

            for p in self._warp_particles:
                if p["life"] <= 0:
                    continue
                wa = int(140 * p["life"])
                ws = max(1, int(p["size"] * p["life"]))
                w_surf = pygame.Surface((ws * 2, ws * 2), pygame.SRCALPHA)
                pygame.draw.circle(w_surf, (*pc, wa), (ws, ws), ws)
                screen.blit(w_surf, (int(p["x"]) - ws, int(p["y"]) - ws))

        if t >= 3.0:
            fade_t = (t - 3.0) / 0.8
            if fade_t < 0.25:
                flash_a = int(255 * (1.0 - fade_t / 0.25))
                flash_surf = pygame.Surface((w, h), pygame.SRCALPHA)
                flash_surf.fill((*fc, flash_a))
                screen.blit(flash_surf, (0, 0))
            else:
                fade_alpha = int(220 * (1.0 - (fade_t - 0.25) / 0.75))
                self._overlay.fill((*dc, fade_alpha))
                screen.blit(self._overlay, (0, 0))

        if 2.2 <= t < 3.0:
            transform_t = (t - 2.2) / 0.8
            pulse = math.sin(transform_t * math.pi * 4) * 0.5 + 0.5
            for ring_i in range(3):
                tr = int(30 + ring_i * 25 + pulse * 20)
                ta = int(80 * (1.0 - transform_t) * (1.0 - ring_i * 0.25))
                tr_surf = pygame.Surface((tr * 2, tr * 2), pygame.SRCALPHA)
                pygame.draw.circle(tr_surf, (*fc, ta), (tr, tr), tr, 2)
                screen.blit(tr_surf, (cx - tr, cy - tr), special_flags=pygame.BLEND_ALPHA_SDL2)

    def draw_text(self, screen: pygame.Surface):
        if self.finished:
            return
        t = self.elapsed
        w, h = self.screen_w, self.screen_h
        cx, cy = w // 2, h // 2
        theme = self._theme
        fc = theme["flash_color"]

        if 1.2 <= t < 2.8:
            name_progress = (t - 1.2) / 1.6
            try:
                title_font = pygame.font.SysFont("arial", 32, bold=True)
                sub_font = pygame.font.SysFont("arial", 14, bold=True)
            except Exception:
                title_font = pygame.font.Font(None, 38)
                sub_font = pygame.font.Font(None, 18)

            alpha = int(255 * min(1.0, name_progress * 2.5))
            if name_progress > 0.75:
                alpha = int(255 * (1.0 - (name_progress - 0.75) / 0.25))

            title_surf = title_font.render(theme["name"], True, fc)
            title_surf.set_alpha(alpha)
            title_x = cx - title_surf.get_width() // 2
            title_y = cy - 35

            glow_surf = title_font.render(theme["name"], True, tuple(max(0, c - 40) for c in fc[:3]))
            glow_surf.set_alpha(alpha // 2)
            for gx, gy in [(-2, -1), (2, -1), (-1, 2), (1, -2)]:
                screen.blit(glow_surf, (title_x + gx, title_y + gy), special_flags=pygame.BLEND_ALPHA_SDL2)
            screen.blit(title_surf, (title_x, title_y))

            sub_surf = sub_font.render(theme["subtitle"], True, (200, 180, 220))
            sub_alpha = int(220 * min(1.0, max(0, name_progress * 2.5 - 1)))
            if name_progress > 0.75:
                sub_alpha = int(220 * (1.0 - (name_progress - 0.75) / 0.25))
            sub_surf.set_alpha(sub_alpha)
            sub_x = cx - sub_surf.get_width() // 2
            sub_y = cy - 5
            screen.blit(sub_surf, (sub_x, sub_y))

            line_alpha = int(180 * min(1.0, name_progress * 2))
            line_w = int(100 * min(1.0, name_progress * 2))
            line_y = cy + 16
            pygame.draw.line(screen, (*fc[:3], line_alpha), (cx - line_w, line_y), (cx - 8, line_y), 1)
            pygame.draw.line(screen, (*fc[:3], line_alpha), (cx + 8, line_y), (cx + line_w, line_y), 1)
            pygame.draw.polygon(screen, (*fc[:3], line_alpha),
                [(cx, line_y - 3), (cx + 3, line_y), (cx, line_y + 3), (cx - 3, line_y)])

        if 2.8 <= t < 3.8:
            fade_t = (t - 2.8) / 1.0
            alpha2 = int(255 * (1.0 - fade_t))
            if alpha2 > 0:
                try:
                    final_font = pygame.font.SysFont("arial", 20, bold=True)
                except Exception:
                    final_font = pygame.font.Font(None, 24)
                phase_text = f"PHASE {self.to_phase}"
                pf = final_font.render(phase_text, True, fc)
                pf.set_alpha(alpha2)
                screen.blit(pf, (cx - pf.get_width() // 2, cy - pf.get_height() // 2))


class Boss(Enemy):
    """
    Extended enemy class for boss encounters with phase tracking,
    a prominent boss HP bar, and optional intro cutscene.

    Attributes:
        phase (int): Current boss phase (1, 2, or 3).
        boss_name (str): Display name shown above the HP bar.
        max_phases (int): Total number of phases.
        intro (ChronosIntro | None): Active intro cutscene, or None.
        intro_triggered (bool): Whether the intro has been triggered.
        intro_trigger_distance (float): Distance at which the intro starts.
    """

    def __init__(
        self,
        x: float,
        y: float,
        sprite_set: str,
        speed: float,
        hp: int,
        damage: int,
        animation_size: tuple[int, int],
        animation_speed: float,
        detection_range: float,
        attack_range: float,
        boss_name: str = "Boss",
        patrol_points: list | None = None,
        ai_profile: str = "stalker",
        ai_config: dict | None = None,
        animations: dict[str, list[pygame.Surface]] | None = None,
        attack_controller=None,
        contact_damage: bool = True,
        visual_style: str | None = None,
        intro_trigger_distance: float = 450.0,
    ):
        super().__init__(
            x=x, y=y, sprite_set=sprite_set, speed=speed, hp=hp, damage=damage,
            animation_size=animation_size, animation_speed=animation_speed,
            detection_range=detection_range, attack_range=attack_range,
            patrol_points=patrol_points, ai_profile=ai_profile, ai_config=ai_config,
            animations=animations, attack_controller=attack_controller,
            contact_damage=contact_damage, visual_style=visual_style,
        )
        self.boss_name = boss_name
        self.phase = 1
        self.max_phases = 3
        self._phase_thresholds = [0.70, 0.40]
        self._phase_triggered = set()
        self.intro: ChronosIntro | None = None
        self.intro_triggered = False
        self.intro_trigger_distance = intro_trigger_distance
        self._player_frozen = False
        self._boss_activated = False
        self.phase_transition: BossPhaseTransition | None = None
        self._screen_size = (0, 0)
        self._phase_visual_tint = None
        logger.info(f"Boss '{boss_name}' spawned at ({x}, {y}) with {hp} HP")

    def check_intro_trigger(self, player_pos: pygame.Vector2, screen_size: tuple[int, int]):
        if self.intro_triggered or self.intro is not None:
            return
        diff = player_pos - self.pos
        if diff.length_squared() <= self.intro_trigger_distance ** 2:
            self.intro = ChronosIntro(self.pos.copy(), screen_size)
            self.intro_triggered = True
            self._player_frozen = True
            self._boss_activated = False
            logger.info(f"Boss intro triggered for '{self.boss_name}'")

    def is_intro_active(self) -> bool:
        return self.intro is not None and not self.intro.finished

    def is_player_frozen(self) -> bool:
        return self._player_frozen

    def _trigger_phase_transition(self, to_phase: int):
        if self._screen_size == (0, 0):
            self._screen_size = (1024, 768)
        self.phase_transition = BossPhaseTransition(
            self.pos.copy(), self._screen_size, to_phase,
        )
        self._player_frozen = True
        logger.info(f"Boss '{self.boss_name}' phase transition {to_phase} started")

    def set_screen_size(self, size: tuple[int, int]):
        self._screen_size = size

    def update(self, dt: float, collision_system, obstacles, nav_grid=None, attack_context=None, active: bool = True):
        if self.intro is not None and not self.intro.finished:
            self.intro.update(dt)
            if self.intro.finished:
                self._player_frozen = False
                self._boss_activated = True
                logger.info(f"Boss intro finished for '{self.boss_name}', fight begins")
            return
        if not self._boss_activated and not self.intro_triggered:
            return
        if self.phase_transition is not None and not self.phase_transition.finished:
            self.phase_transition.update(dt)
            if self.phase_transition.finished:
                self.phase_transition = None
                self._player_frozen = False
                logger.info(f"Boss phase transition finished for '{self.boss_name}'")
            return
        super().update(dt, collision_system, obstacles, nav_grid, attack_context, active)
        self._check_phase_transition()

    def _check_phase_transition(self):
        if self.max_hp <= 0:
            return
        ratio = self.hp / self.max_hp
        for i, threshold in enumerate(self._phase_thresholds):
            phase_num = i + 2
            if ratio <= threshold and phase_num not in self._phase_triggered:
                self.phase = phase_num
                self._phase_triggered.add(phase_num)
                logger.info(f"Boss '{self.boss_name}' entered phase {self.phase}")
                self._trigger_phase_transition(phase_num)

    def draw(self, screen: pygame.Surface, camera_offset=None):
        if self.intro is not None and not self.intro.finished:
            return
        if self.phase_transition is not None and not self.phase_transition.finished:
            return
        img = self.image
        if self.direction == "side" and self.flip:
            img = self.animations_flipped["side"][self.frame_index]
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)
        draw_pos = (int(self.pos.x - camera_offset.x), int(self.pos.y - camera_offset.y))
        screen.blit(img, draw_pos)
        self._draw_phase_aura(screen, camera_offset)

    def draw_overlay(self, screen: pygame.Surface):
        if self.intro is not None and not self.intro.finished:
            self.intro.draw_overlay(screen)
        if self.phase_transition is not None and not self.phase_transition.finished:
            self.phase_transition.draw_overlay(screen)

    def draw_hp_bar(self, screen: pygame.Surface, camera_offset=None):
        if self.intro is not None and not self.intro.finished:
            return
        if self.phase_transition is not None and not self.phase_transition.finished:
            return
        self._draw_boss_hp_bar(screen)

    def draw_intro_text(self, screen: pygame.Surface):
        if self.intro is not None and not self.intro.finished:
            self.intro.draw_text(screen)
        if self.phase_transition is not None and not self.phase_transition.finished:
            self.phase_transition.draw_text(screen)

    def _draw_phase_aura(self, screen: pygame.Surface, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)
        if self.phase < 2:
            return
        rect = self.get_rect()
        cx = rect.centerx - int(camera_offset.x)
        cy = rect.centery - int(camera_offset.y)
        t = pygame.time.get_ticks() / 1000.0
        if self.phase >= 4:
            colors = [(220, 40, 30), (180, 25, 15)]
            ring_count = 6
            base_alpha = 35
        elif self.phase >= 3:
            colors = [(160, 80, 220), (120, 50, 180)]
            ring_count = 5
            base_alpha = 30
        else:
            colors = [(220, 180, 60), (180, 140, 30)]
            ring_count = 4
            base_alpha = 25
        pulse = math.sin(t * 3.0) * 0.3 + 0.7
        for ring_i in range(ring_count):
            ring_r = int(50 + ring_i * 12 + pulse * 8)
            ring_a = max(3, int((base_alpha - ring_i * 5) * pulse))
            ring_surf = pygame.Surface((ring_r * 2, ring_r * 2), pygame.SRCALPHA)
            c = colors[0] if ring_i % 2 == 0 else colors[1]
            pygame.draw.circle(ring_surf, (*c, ring_a), (ring_r, ring_r), ring_r, 1)
            screen.blit(ring_surf, (cx - ring_r, cy - ring_r), special_flags=pygame.BLEND_ALPHA_SDL2)
        for orb_i in range(3):
            orb_angle = t * 0.8 + orb_i * (math.pi * 2 / 3)
            orb_r = 55 + orb_i * 8
            orb_x = cx + int(math.cos(orb_angle) * orb_r)
            orb_y = cy + int(math.sin(orb_angle) * orb_r * 0.6)
            orb_a = int(120 * pulse)
            orb_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(orb_surf, (*colors[0], orb_a), (5, 5), 5)
            pygame.draw.circle(orb_surf, (*colors[0], orb_a // 2), (5, 5), 7)
            screen.blit(orb_surf, (orb_x - 5, orb_y - 5), special_flags=pygame.BLEND_ALPHA_SDL2)

    def _draw_boss_hp_bar(self, screen: pygame.Surface):
        screen_w = screen.get_width()
        bar_w = min(600, screen_w - 100)
        bar_h = 20
        bar_x = (screen_w - bar_w) // 2
        bar_y = 30

        # Ornate background frame
        frame_color = (40, 25, 60)
        pygame.draw.rect(screen, (10, 5, 20), (bar_x - 6, bar_y - 6, bar_w + 12, bar_h + 12), border_radius=6)
        pygame.draw.rect(screen, frame_color, (bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 8), border_radius=5)
        pygame.draw.rect(screen, (60, 40, 85), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), border_radius=4)
        pygame.draw.rect(screen, (25, 15, 38), (bar_x, bar_y, bar_w, bar_h), border_radius=3)

        # HP fill
        if self.max_hp > 0:
            hp_ratio = max(0.0, self.hp / self.max_hp)
            fill_w = int(bar_w * hp_ratio)
            if self.phase >= 3:
                fill_color = (220, 40, 40)
                fill_light = (255, 80, 80)
            elif self.phase >= 2:
                fill_color = (220, 150, 30)
                fill_light = (255, 200, 60)
            else:
                fill_color = (40, 180, 100)
                fill_light = (80, 220, 140)
            if fill_w > 0:
                pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_w, bar_h), border_radius=3)
                highlight_h = max(1, bar_h // 3)
                pygame.draw.rect(screen, fill_light, (bar_x + 1, bar_y + 1, fill_w - 2, highlight_h), border_radius=2)

        # Phase tick marks
        for threshold in self._phase_thresholds:
            marker_x = bar_x + int(bar_w * threshold)
            pygame.draw.line(screen, (140, 120, 170), (marker_x, bar_y + 2), (marker_x, bar_y + bar_h - 2), 1)

        # Boss name
        try:
            name_font = pygame.font.SysFont("arial", 15, bold=True)
        except Exception:
            name_font = pygame.font.Font(None, 20)
        name_text = f"{self.boss_name}"
        name_surf = name_font.render(name_text, True, (220, 190, 255))
        name_x = (screen_w - name_surf.get_width()) // 2
        screen.blit(name_surf, (name_x, bar_y - 20))

        # HP numbers
        try:
            hp_font = pygame.font.SysFont("arial", 11, bold=True)
        except Exception:
            hp_font = pygame.font.Font(None, 14)
        hp_text = f"{self.hp} / {self.max_hp}"
        hp_surf = hp_font.render(hp_text, True, (200, 190, 220))
        hp_x = bar_x + (bar_w - hp_surf.get_width()) // 2
        screen.blit(hp_surf, (hp_x, bar_y + 4))

        # Corner ornaments
        orn_w = 8
        for ox, oy in [(bar_x - 6, bar_y - 6), (bar_x + bar_w - 2, bar_y - 6),
                       (bar_x - 6, bar_y + bar_h - 2), (bar_x + bar_w - 2, bar_y + bar_h - 2)]:
            pygame.draw.circle(screen, (200, 170, 60), (ox + orn_w // 2, oy + orn_w // 2), 3)
            pygame.draw.circle(screen, (140, 110, 30), (ox + orn_w // 2, oy + orn_w // 2), 3, 1)
