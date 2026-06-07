from __future__ import annotations

import math

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

    def draw(self, screen: pygame.Surface, camera_offset=None):
        if self.intro is not None and not self.intro.finished:
            self.intro.draw_overlay(screen)
            return
        super().draw(screen, camera_offset)
        self._draw_boss_hp_bar(screen)

    def draw_intro_text(self, screen: pygame.Surface):
        if self.intro is not None and not self.intro.finished:
            self.intro.draw_text(screen)

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
