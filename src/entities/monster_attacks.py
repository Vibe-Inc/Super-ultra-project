from __future__ import annotations

from dataclasses import dataclass
import pygame

from src.items.effects import SlowEffect


@dataclass
class AttackContext:
    dt: float
    player: object | None
    obstacles: list[pygame.Rect]
    now_ms: int


def _entity_center(entity: object) -> pygame.Vector2:
    if hasattr(entity, "get_rect"):
        rect = entity.get_rect()
        return pygame.Vector2(rect.centerx, rect.centery)
    return pygame.Vector2(getattr(entity, "pos", (0, 0)))


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


def build_attack_controller(profile: str | None, config: dict | None = None) -> BaseAttack | None:
    name = (profile or "").lower()
    if name == "brute":
        return BruteAttack(config)
    return None
