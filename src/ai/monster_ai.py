from __future__ import annotations

from dataclasses import dataclass
import math
import random

import pygame

from src.ai.navigation import NavGrid


@dataclass
class AIContext:
    dt: float
    nav_grid: NavGrid | None
    obstacles: list[pygame.Rect]
    player: object | None


def _entity_center(entity: object) -> pygame.Vector2:
    if hasattr(entity, "get_rect"):
        rect = entity.get_rect()
        return pygame.Vector2(rect.centerx, rect.centery)
    return pygame.Vector2(getattr(entity, "pos", (0, 0)))


def has_line_of_sight(start: pygame.Vector2, end: pygame.Vector2, obstacles: list[pygame.Rect]) -> bool:
    for wall in obstacles:
        if wall.clipline(start, end):
            return False
    return True


class BaseBrain:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.path: list[pygame.Vector2] = []
        self.path_index = 0
        self.path_target_cell: tuple[int, int] | None = None
        self.repath_timer = 0.0
        self.repath_interval = float(self.config.get("repath_interval", 0.6))
        self.path_node_radius = float(self.config.get("path_node_radius", 10.0))

        self.roam_target: pygame.Vector2 | None = None
        self.roam_timer = 0.0

    def update(self, enemy: object, context: AIContext):
        enemy.ai_state = "idle"
        enemy.target = None
        self._clear_path()

    def _nav_offset(self, enemy: object) -> pygame.Vector2:
        rect = enemy.get_rect()
        return pygame.Vector2(rect.centerx, rect.centery) - enemy.pos

    def _set_direct_target(self, enemy: object, world_pos: pygame.Vector2):
        offset = self._nav_offset(enemy)
        enemy.target = pygame.Vector2(world_pos) - offset

    def _clear_path(self):
        self.path = []
        self.path_index = 0
        self.path_target_cell = None

    def _move_to(self, enemy: object, context: AIContext, world_pos: pygame.Vector2, force_repath: bool = False):
        if context.nav_grid:
            world_pos = context.nav_grid.clamp_world(world_pos)

        if context.nav_grid is None:
            self._clear_path()
            self._set_direct_target(enemy, world_pos)
            return

        self.repath_timer -= context.dt
        target_cell = context.nav_grid.world_to_cell(world_pos)

        if force_repath or self.repath_timer <= 0 or target_cell != self.path_target_cell:
            start_pos = _entity_center(enemy)
            self.path = context.nav_grid.find_path(start_pos, world_pos)
            self.path_index = 0
            self.path_target_cell = target_cell
            self.repath_timer = self.repath_interval

        if not self.path:
            self._set_direct_target(enemy, world_pos)
            return

        current = _entity_center(enemy)
        while self.path_index < len(self.path) and current.distance_to(self.path[self.path_index]) <= self.path_node_radius:
            self.path_index += 1

        if self.path_index >= len(self.path):
            self._clear_path()
            self._set_direct_target(enemy, world_pos)
            return

        self._set_direct_target(enemy, self.path[self.path_index])

    def _random_point_near(
        self,
        center: pygame.Vector2,
        radius: float,
        nav_grid: NavGrid | None,
    ) -> pygame.Vector2 | None:
        for _ in range(8):
            angle = random.random() * (2.0 * math.pi)
            dist = random.uniform(radius * 0.4, radius)
            candidate = pygame.Vector2(center) + pygame.Vector2(math.cos(angle), math.sin(angle)) * dist
            if nav_grid is None:
                return candidate
            candidate = nav_grid.clamp_world(candidate)
            if nav_grid.is_walkable(nav_grid.world_to_cell(candidate)):
                return candidate

        if nav_grid:
            return nav_grid.random_world_position()
        return pygame.Vector2(center)

    def _roam(self, enemy: object, context: AIContext, center: pygame.Vector2, radius: float, interval: float):
        self.roam_timer -= context.dt
        current = _entity_center(enemy)

        if (
            self.roam_target is None
            or self.roam_timer <= 0
            or current.distance_to(self.roam_target) <= self.path_node_radius * 2
        ):
            self.roam_timer = interval
            self.roam_target = self._random_point_near(center, radius, context.nav_grid)

        if self.roam_target is None:
            enemy.target = None
            self._clear_path()
            return

        self._move_to(enemy, context, self.roam_target)


class StalkerBrain(BaseBrain):
    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.memory_duration = float(self.config.get("memory_duration", 2.5))
        self.memory_timer = 0.0
        self.last_seen_pos: pygame.Vector2 | None = None
        self.patrol_wait = float(self.config.get("patrol_wait", 0.6))
        self.patrol_wait_timer = 0.0

    def update(self, enemy: object, context: AIContext):
        player = context.player
        if player is None:
            enemy.ai_state = "idle"
            enemy.target = None
            self._clear_path()
            return

        enemy_pos = _entity_center(enemy)
        player_pos = _entity_center(player)
        distance = enemy_pos.distance_to(player_pos)

        wants_melee = getattr(enemy, "contact_damage", True) and getattr(enemy, "attack_controller", None) is None
        if wants_melee:
            if distance <= enemy.attack_range:
                enemy.ai_state = "attack"
                self._move_to(enemy, context, player_pos)
                return
            enemy.ai_state = "chase"
            self._move_to(enemy, context, player_pos)
            return

        if distance <= enemy.attack_range:
            enemy.ai_state = "attack"
            if getattr(enemy, "contact_damage", True):
                self._move_to(enemy, context, player_pos)
            else:
                enemy.target = None
                self._clear_path()
            return

        if distance <= enemy.detection_range:
            self.memory_timer = self.memory_duration
            self.last_seen_pos = pygame.Vector2(player_pos)
            enemy.ai_state = "chase"
            if has_line_of_sight(enemy_pos, player_pos, context.obstacles):
                self._clear_path()
                self._set_direct_target(enemy, player_pos)
            else:
                self._move_to(enemy, context, player_pos)
            return

        if self.memory_timer > 0 and self.last_seen_pos is not None:
            self.memory_timer -= context.dt
            enemy.ai_state = "search"
            self._move_to(enemy, context, self.last_seen_pos)
            return

        if enemy.patrol_points:
            enemy.ai_state = "patrol"
            if self.patrol_wait_timer > 0:
                self.patrol_wait_timer -= context.dt
                enemy.target = None
                self._clear_path()
                return

            patrol_target = pygame.Vector2(enemy.patrol_points[enemy.patrol_index])
            if enemy_pos.distance_to(patrol_target) <= 12:
                enemy.patrol_index = (enemy.patrol_index + 1) % len(enemy.patrol_points)
                self.patrol_wait_timer = self.patrol_wait
                enemy.target = None
                self._clear_path()
                return

            self._move_to(enemy, context, patrol_target)
            return

        enemy.ai_state = "idle"
        enemy.target = None
        self._clear_path()


class SkirmisherBrain(BaseBrain):
    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.orbit_interval = float(self.config.get("orbit_interval", 2.0))
        self.orbit_timer = 0.0
        self.orbit_clockwise = True
        self.roam_interval = float(self.config.get("roam_interval", 4.0))

    def update(self, enemy: object, context: AIContext):
        player = context.player
        if player is None:
            enemy.ai_state = "idle"
            enemy.target = None
            self._clear_path()
            return

        enemy_pos = _entity_center(enemy)
        player_pos = _entity_center(player)
        distance = enemy_pos.distance_to(player_pos)

        if distance > enemy.detection_range:
            enemy.ai_state = "roam"
            roam_radius = float(self.config.get("roam_radius", 220.0))
            self._roam(enemy, context, pygame.Vector2(enemy.spawn_pos), roam_radius, self.roam_interval)
            return

        if distance <= enemy.attack_range:
            enemy.ai_state = "attack"
            if getattr(enemy, "contact_damage", True):
                self._move_to(enemy, context, player_pos)
            else:
                enemy.target = None
                self._clear_path()
            return

        preferred_min = float(self.config.get("preferred_min", enemy.attack_range * 1.3))
        preferred_max = float(self.config.get("preferred_max", enemy.attack_range * 3.0))
        if getattr(enemy, "contact_damage", True):
            preferred_min = min(preferred_min, enemy.attack_range * 0.8)
            preferred_max = max(preferred_max, enemy.attack_range * 1.6)

        if distance < preferred_min:
            enemy.ai_state = "retreat"
            away = enemy_pos - player_pos
            if away.length_squared() == 0:
                away = pygame.Vector2(1, 0)
            target = enemy_pos + away.normalize() * preferred_min
            self._move_to(enemy, context, target)
            return

        if distance > preferred_max:
            enemy.ai_state = "chase"
            self._move_to(enemy, context, player_pos)
            return

        enemy.ai_state = "orbit"
        self.orbit_timer -= context.dt
        if self.orbit_timer <= 0:
            self.orbit_timer = self.orbit_interval
            self.orbit_clockwise = random.choice([True, False])

        direction = player_pos - enemy_pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)

        tangent = pygame.Vector2(-direction.y, direction.x)
        if not self.orbit_clockwise:
            tangent *= -1
        tangent = tangent.normalize()

        orbit_radius = float(self.config.get("orbit_radius", (preferred_min + preferred_max) * 0.5))
        target = player_pos + tangent * orbit_radius
        self._move_to(enemy, context, target)


class GuardianBrain(BaseBrain):
    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.guard_radius = float(self.config.get("guard_radius", 300.0))
        self.leash_slack = float(self.config.get("leash_slack", 80.0))
        self.alerted = False
        self.patrol_wait = float(self.config.get("patrol_wait", 0.6))
        self.patrol_wait_timer = 0.0
        self.roam_interval = float(self.config.get("roam_interval", 4.5))

    def update(self, enemy: object, context: AIContext):
        guard_center = pygame.Vector2(enemy.spawn_pos)
        enemy_pos = _entity_center(enemy)
        player = context.player

        if player is not None:
            player_pos = _entity_center(player)
            player_distance = enemy_pos.distance_to(player_pos)
            player_guard_distance = player_pos.distance_to(guard_center)

            if player_distance <= enemy.detection_range and player_guard_distance <= self.guard_radius:
                self.alerted = True

            if self.alerted:
                if player_guard_distance <= self.guard_radius + self.leash_slack:
                    if player_distance <= enemy.attack_range:
                        enemy.ai_state = "attack"
                        if getattr(enemy, "contact_damage", True):
                            self._move_to(enemy, context, player_pos)
                        else:
                            enemy.target = None
                            self._clear_path()
                        return
                    enemy.ai_state = "chase"
                    self._move_to(enemy, context, player_pos)
                    return
                self.alerted = False

        if enemy.patrol_points:
            enemy.ai_state = "patrol"
            if self.patrol_wait_timer > 0:
                self.patrol_wait_timer -= context.dt
                enemy.target = None
                self._clear_path()
                return

            patrol_target = pygame.Vector2(enemy.patrol_points[enemy.patrol_index])
            if enemy_pos.distance_to(patrol_target) <= 12:
                enemy.patrol_index = (enemy.patrol_index + 1) % len(enemy.patrol_points)
                self.patrol_wait_timer = self.patrol_wait
                enemy.target = None
                self._clear_path()
                return

            self._move_to(enemy, context, patrol_target)
            return

        if enemy_pos.distance_to(guard_center) > self.guard_radius * 0.6:
            enemy.ai_state = "return"
            self._move_to(enemy, context, guard_center)
            return

        enemy.ai_state = "guard"
        self._roam(enemy, context, guard_center, self.guard_radius * 0.5, self.roam_interval)


def build_brain(profile: str | None, config: dict | None = None) -> BaseBrain:
    name = (profile or "stalker").lower()
    if name == "skirmisher":
        return SkirmisherBrain(config)
    if name == "guardian":
        return GuardianBrain(config)
    return StalkerBrain(config)
