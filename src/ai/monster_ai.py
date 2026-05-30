from __future__ import annotations

from dataclasses import dataclass
import math
import random

import pygame

from src.ai.navigation import NavGrid
from src.core.logger import logger


@dataclass
class AIContext:
    """
    Context object passed into monster AI updates.

    Attributes:
        dt (float):
            Delta time in seconds for the current update.
        nav_grid (NavGrid | None):
            Navigation grid used for pathfinding and world clamping.
        obstacles (list[pygame.Rect]):
            Solid world obstacles used for line-of-sight checks.
        player (object | None):
            Current player entity or None when no player is available.

    Methods:
        None.
    """
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
    """
    Base behavior controller for enemy AI.

    Attributes:
        config (dict):
            Behavior tuning values for the brain.
        path (list[pygame.Vector2]):
            Cached path nodes toward the current target.
        path_index (int):
            Index of the next node in the cached path.
        path_target_cell (tuple[int, int] | None):
            Cell used to detect when the path target has changed.
        repath_timer (float):
            Countdown before the next path recomputation.
        repath_interval (float):
            Minimum delay between path recomputations.
        path_node_radius (float):
            Radius used to consider a node reached.
        roam_target (pygame.Vector2 | None):
            Current roaming target position.
        roam_timer (float):
            Countdown before choosing a new roaming target.

    Methods:
        __init__(config=None):
            Initialize the brain with optional tuning values.
        update(enemy, context):
            Reset the enemy into an idle state.
        _nav_offset(enemy):
            Compute the offset from the enemy anchor to its center.
        _set_direct_target(enemy, world_pos):
            Set a direct movement target in world space.
        _clear_path():
            Clear any cached path data.
        _move_to(enemy, context, world_pos, force_repath=False):
            Move the enemy toward a world position using pathfinding.
        _random_point_near(center, radius, nav_grid):
            Pick a random nearby point that is walkable when possible.
        _roam(enemy, context, center, radius, interval):
            Move the enemy toward a wandering target.
    """
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
        logger.debug("AI cleared path cache")

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
            logger.debug(f"AI repath for {getattr(enemy, 'id', type(enemy))}: target_cell={target_cell} path_len={len(self.path)}")

        if not self.path:
            logger.debug(f"AI using direct target for {getattr(enemy, 'id', type(enemy))}")
            self._set_direct_target(enemy, world_pos)
            return

        current = _entity_center(enemy)
        while self.path_index < len(self.path):
            target_node = self.path[self.path_index]
            diff = target_node - current
            if diff.length_squared() <= (self.path_node_radius * self.path_node_radius):
                self.path_index += 1
                continue
            break

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
            or (self.roam_target is not None and (self.roam_target - current).length_squared() <= (self.path_node_radius * 2) * (self.path_node_radius * 2))
        ):
            self.roam_timer = interval
            self.roam_target = self._random_point_near(center, radius, context.nav_grid)

        if self.roam_target is None:
            enemy.target = None
            self._clear_path()
            return

        self._move_to(enemy, context, self.roam_target)


class StalkerBrain(BaseBrain):
    """
    AI brain that chases, searches, and patrols around the player.

    Attributes:
        memory_duration (float):
            Time to remember the player's last seen position.
        memory_timer (float):
            Remaining memory time before the enemy returns to idle.
        last_seen_pos (pygame.Vector2 | None):
            Last player position the enemy saw.
        patrol_wait (float):
            Delay between patrol point transitions.
        patrol_wait_timer (float):
            Countdown before resuming patrol movement.

    Methods:
        __init__(config=None):
            Initialize stalker-specific tuning values.
        update(enemy, context):
            Drive stalker chase, search, and patrol behavior.
    """
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
        diff = player_pos - enemy_pos
        distance_sq = diff.length_squared()

        wants_melee = getattr(enemy, "contact_damage", True) and getattr(enemy, "attack_controller", None) is None
        if wants_melee:
            if distance_sq <= (enemy.attack_range * enemy.attack_range):
                enemy.ai_state = "attack"
                logger.info(f"Enemy {getattr(enemy, 'id', type(enemy))} entering ATTACK (melee)")
                self._move_to(enemy, context, player_pos)
                return
            enemy.ai_state = "chase"
            logger.debug(f"Enemy {getattr(enemy, 'id', type(enemy))} entering CHASE (melee)")
            self._move_to(enemy, context, player_pos)
            return

        if distance_sq <= (enemy.attack_range * enemy.attack_range):
            enemy.ai_state = "attack"
            logger.info(f"Enemy {getattr(enemy, 'id', type(enemy))} entering ATTACK")
            if getattr(enemy, "contact_damage", True):
                self._move_to(enemy, context, player_pos)
            else:
                enemy.target = None
                self._clear_path()
            return

        if distance_sq <= (enemy.detection_range * enemy.detection_range):
            self.memory_timer = self.memory_duration
            self.last_seen_pos = pygame.Vector2(player_pos)
            enemy.ai_state = "chase"
            logger.info(f"Enemy {getattr(enemy, 'id', type(enemy))} detected player at {player_pos}")
            if has_line_of_sight(enemy_pos, player_pos, context.obstacles):
                self._clear_path()
                self._set_direct_target(enemy, player_pos)
            else:
                self._move_to(enemy, context, player_pos)
            return

        if self.memory_timer > 0 and self.last_seen_pos is not None:
            self.memory_timer -= context.dt
            enemy.ai_state = "search"
            logger.debug(f"Enemy {getattr(enemy, 'id', type(enemy))} searching last seen pos {self.last_seen_pos}")
            self._move_to(enemy, context, self.last_seen_pos)
            return

        if enemy.patrol_points:
            enemy.ai_state = "patrol"
            logger.debug(f"Enemy {getattr(enemy, 'id', type(enemy))} patrolling")
            if self.patrol_wait_timer > 0:
                self.patrol_wait_timer -= context.dt
                enemy.target = None
                self._clear_path()
                return

            patrol_target = pygame.Vector2(enemy.patrol_points[enemy.patrol_index])
            if (patrol_target - enemy_pos).length_squared() <= 12 * 12:
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
        logger.debug(f"Enemy {getattr(enemy, 'id', type(enemy))} idle")


class SkirmisherBrain(BaseBrain):
    """
    AI brain that keeps distance and circles the player.

    Attributes:
        orbit_interval (float):
            Interval for changing orbit direction.
        orbit_timer (float):
            Countdown until the orbit direction may change.
        orbit_clockwise (bool):
            Current orbit direction flag.
        roam_interval (float):
            Interval used while wandering outside detection range.

    Methods:
        __init__(config=None):
            Initialize skirmisher-specific tuning values.
        update(enemy, context):
            Drive skirmisher orbit, retreat, chase, and roam behavior.
    """
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
        sd = player_pos - enemy_pos
        distance_sq = sd.length_squared()

        if distance_sq > (enemy.detection_range * enemy.detection_range):
            enemy.ai_state = "roam"
            roam_radius = float(self.config.get("roam_radius", 220.0))
            self._roam(enemy, context, pygame.Vector2(enemy.spawn_pos), roam_radius, self.roam_interval)
            return

        if distance_sq <= (enemy.attack_range * enemy.attack_range):
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

        if distance_sq < (preferred_min * preferred_min):
            enemy.ai_state = "retreat"
            away = enemy_pos - player_pos
            if away.length_squared() == 0:
                away = pygame.Vector2(1, 0)
            target = enemy_pos + away.normalize() * preferred_min
            self._move_to(enemy, context, target)
            return

        if distance_sq > (preferred_max * preferred_max):
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
    """
    AI brain that guards a spawn area and returns to post after pursuit.

    Attributes:
        guard_radius (float):
            Radius around the spawn point that the guardian protects.
        leash_slack (float):
            Extra distance allowed before the guardian disengages.
        alerted (bool):
            Whether the guardian is currently in an alerted state.
        patrol_wait (float):
            Delay between patrol point transitions.
        patrol_wait_timer (float):
            Countdown before the next patrol step.
        roam_interval (float):
            Interval used for idle roaming near the guard point.

    Methods:
        __init__(config=None):
            Initialize guardian-specific tuning values.
        update(enemy, context):
            Drive guardian patrol, chase, retreat, and guard behavior.
    """
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
            pdiff = player_pos - enemy_pos
            player_distance_sq = pdiff.length_squared()
            pgdiff = player_pos - guard_center
            player_guard_distance_sq = pgdiff.length_squared()

            if player_distance_sq <= (enemy.detection_range * enemy.detection_range) and player_guard_distance_sq <= (self.guard_radius * self.guard_radius):
                self.alerted = True

            if self.alerted:
                if player_guard_distance_sq <= (self.guard_radius + self.leash_slack) * (self.guard_radius + self.leash_slack):
                    if player_distance_sq <= (enemy.attack_range * enemy.attack_range):
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
            if (patrol_target - enemy_pos).length_squared() <= 12 * 12:
                enemy.patrol_index = (enemy.patrol_index + 1) % len(enemy.patrol_points)
                self.patrol_wait_timer = self.patrol_wait
                enemy.target = None
                self._clear_path()
                return

            self._move_to(enemy, context, patrol_target)
            return

        if (enemy_pos - guard_center).length_squared() > (self.guard_radius * 0.6) * (self.guard_radius * 0.6):
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
