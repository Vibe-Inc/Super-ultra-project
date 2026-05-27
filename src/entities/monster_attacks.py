from __future__ import annotations

from dataclasses import dataclass
import random
import pygame

from src.entities.projectile import ArcaneBolt
from src.items.effects import PoisonEffect, SlowEffect


@dataclass
class AttackContext:
    dt: float
    player: object | None
    obstacles: list[pygame.Rect]
    projectiles: list
    now_ms: int


def _entity_center(entity: object) -> pygame.Vector2:
    if hasattr(entity, "get_rect"):
        rect = entity.get_rect()
        return pygame.Vector2(rect.centerx, rect.centery)
    return pygame.Vector2(getattr(entity, "pos", (0, 0)))


def _has_line_of_sight(start: pygame.Vector2, end: pygame.Vector2, obstacles: list[pygame.Rect]) -> bool:
    for wall in obstacles:
        if wall.clipline(start, end):
            return False
    return True


class BaseAttack:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.cooldown_ms = int(self.config.get("cooldown_ms", 1000))
        self.last_attack_time = -self.cooldown_ms

    def ready(self, now_ms: int) -> bool:
        return now_ms - self.last_attack_time >= self.cooldown_ms

    def update(self, enemy: object, context: AttackContext):
        return


class BruteAttack(BaseAttack):
    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.charge_cooldown_ms = int(self.config.get("charge_cooldown_ms", 2200))
        self.charge_duration = float(self.config.get("charge_duration", 0.6))
        self.charge_speed_mult = float(self.config.get("charge_speed_mult", 2.3))
        self.charge_distance = float(self.config.get("charge_distance", 220.0))
        self.charge_trigger_range = float(self.config.get("charge_trigger_range", 220.0))
        self.slam_damage_mult = float(self.config.get("slam_damage_mult", 1.4))
        self.knockback_force = float(self.config.get("knockback_force", 50.0))
        self.slow_duration = float(self.config.get("slow_duration", 1.3))
        self.slow_factor = float(self.config.get("slow_factor", 0.6))

        self.last_charge_time = -self.charge_cooldown_ms
        self.charge_timer = 0.0
        self.charge_direction = pygame.Vector2(1, 0)

    def update(self, enemy: object, context: AttackContext):
        player = context.player
        if player is None:
            enemy.speed_multiplier = 1.0
            return

        enemy_pos = _entity_center(enemy)
        player_pos = _entity_center(player)
        distance = enemy_pos.distance_to(player_pos)

        if self.charge_timer > 0:
            self.charge_timer -= context.dt
            enemy.speed_multiplier = self.charge_speed_mult
            enemy.ai_state = "charge"
            enemy.target = enemy.pos + self.charge_direction * self.charge_distance

            if distance <= enemy.attack_range * 1.1 and self.ready(context.now_ms):
                self._slam(enemy, player, enemy_pos, player_pos, context.now_ms)
                self.charge_timer = 0.0
            if self.charge_timer <= 0:
                enemy.speed_multiplier = 1.0
            return

        enemy.speed_multiplier = 1.0

        if distance <= enemy.attack_range and self.ready(context.now_ms):
            self._slam(enemy, player, enemy_pos, player_pos, context.now_ms)
            return

        if distance <= self.charge_trigger_range and self._charge_ready(context.now_ms):
            direction = player_pos - enemy_pos
            if direction.length_squared() == 0:
                direction = pygame.Vector2(1, 0)
            self.charge_direction = direction.normalize()
            self.charge_timer = self.charge_duration
            self.last_charge_time = context.now_ms

    def _charge_ready(self, now_ms: int) -> bool:
        return now_ms - self.last_charge_time >= self.charge_cooldown_ms

    def _slam(self, enemy: object, player: object, enemy_pos: pygame.Vector2, player_pos: pygame.Vector2, now_ms: int):
        direction = player_pos - enemy_pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        direction = direction.normalize()

        damage = int(enemy.damage * self.slam_damage_mult)
        player.take_damage(damage)
        player.add_effect(SlowEffect(self.slow_duration, self.slow_factor))
        player.pos += direction * self.knockback_force
        self.last_attack_time = now_ms


class VenomousAttack(BaseAttack):
    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.poison_duration = float(self.config.get("poison_duration", 3.5))
        self.poison_dps = float(self.config.get("poison_dps", 4.0))
        self.strike_damage_mult = float(self.config.get("strike_damage_mult", 0.9))
        self.strike_range = float(self.config.get("strike_range", 0.0))

    def update(self, enemy: object, context: AttackContext):
        player = context.player
        if player is None:
            return

        enemy_pos = _entity_center(enemy)
        player_pos = _entity_center(player)
        distance = enemy_pos.distance_to(player_pos)

        effective_range = self.strike_range or float(enemy.attack_range)
        if distance > effective_range:
            return

        if not self.ready(context.now_ms):
            return

        damage = int(enemy.damage * self.strike_damage_mult)
        if damage > 0:
            player.take_damage(damage)
        player.add_effect(PoisonEffect(self.poison_duration, self.poison_dps))
        self.last_attack_time = context.now_ms


class ArcanistAttack(BaseAttack):
    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.bolt_speed = float(self.config.get("bolt_speed", 420.0))
        self.bolt_range = float(self.config.get("bolt_range", 520.0))
        self.bolt_damage_mult = float(self.config.get("bolt_damage_mult", 0.8))
        self.burn_duration = float(self.config.get("burn_duration", 3.0))
        self.burn_dps = float(self.config.get("burn_dps", 4.0))
        self.cast_range = float(self.config.get("cast_range", 320.0))
        self.spread_degrees = float(self.config.get("spread_degrees", 6.0))

    def update(self, enemy: object, context: AttackContext):
        player = context.player
        if player is None:
            return

        enemy_pos = _entity_center(enemy)
        player_pos = _entity_center(player)
        distance = enemy_pos.distance_to(player_pos)

        if distance > self.cast_range:
            return
        if not self.ready(context.now_ms):
            return
        if not _has_line_of_sight(enemy_pos, player_pos, context.obstacles):
            return

        direction = player_pos - enemy_pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        else:
            direction = direction.normalize()

        if self.spread_degrees:
            direction = direction.rotate(random.uniform(-self.spread_degrees, self.spread_degrees))

        damage = max(1, int(enemy.damage * self.bolt_damage_mult))
        bolt = ArcaneBolt(
            enemy_pos,
            direction,
            self.bolt_speed,
            self.bolt_range,
            damage,
            self.burn_duration,
            self.burn_dps,
        )
        context.projectiles.append(bolt)
        self.last_attack_time = context.now_ms


def build_attack_controller(profile: str | None, config: dict | None = None) -> BaseAttack | None:
    name = (profile or "").lower()
    if name == "brute":
        return BruteAttack(config)
    if name == "venomous":
        return VenomousAttack(config)
    if name == "arcanist":
        return ArcanistAttack(config)
    return None
