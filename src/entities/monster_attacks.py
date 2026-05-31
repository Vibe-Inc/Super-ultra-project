from __future__ import annotations

from dataclasses import dataclass
import math
import random
import pygame

from src.entities.projectile import ArcaneBolt, Bomb
from database.effects import ConfusionEffect, DizzinessEffect, PoisonEffect, SlowEffect


@dataclass
class AttackContext:
    """
    Context object passed into monster attack controllers.

    Attributes:
        dt (float):
            Delta time in seconds for the current update.
        player (object | None):
            Current player entity or None when unavailable.
        obstacles (list[pygame.Rect]):
            Solid world obstacles used for line-of-sight and collision tests.
        projectiles (list):
            Shared projectile list that attacks can append to.
        now_ms (int):
            Current game time in milliseconds.

    Methods:
        None.
    """
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


def _rect_for_enemy(enemy: object, pos: pygame.Vector2) -> pygame.Rect:
    hitbox_width = 40
    hitbox_height = 20
    sprite_width = enemy.image.get_width()
    sprite_height = enemy.image.get_height()
    offset_x = (sprite_width - hitbox_width) // 2
    offset_y = sprite_height - hitbox_height
    return pygame.Rect(int(pos.x + offset_x), int(pos.y + offset_y), hitbox_width, hitbox_height)


def _is_clear(enemy: object, pos: pygame.Vector2, obstacles: list[pygame.Rect]) -> bool:
    rect = _rect_for_enemy(enemy, pos)
    for wall in obstacles:
        if rect.colliderect(wall):
            return False
    return True


class BaseAttack:
    """
    Base behavior controller for enemy attack patterns.

    Attributes:
        config (dict):
            Attack tuning values.
        cooldown_ms (int):
            Minimum delay between attacks.
        last_attack_time (int):
            Timestamp of the most recent attack.

    Methods:
        __init__(config=None):
            Initialize the attack controller.
        ready(now_ms):
            Return whether the attack may fire now.
        update(enemy, context):
            Default no-op attack update.
    """
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.cooldown_ms = int(self.config.get("cooldown_ms", 1000))
        self.last_attack_time = -self.cooldown_ms

    def ready(self, now_ms: int) -> bool:
        return now_ms - self.last_attack_time >= self.cooldown_ms

    def update(self, enemy: object, context: AttackContext):
        return


class BruteAttack(BaseAttack):
    """
    Heavy melee attack pattern that charges and slams the player.

    Attributes:
        charge_cooldown_ms (int):
            Delay between charge attempts.
        charge_duration (float):
            Duration of an active charge.
        charge_speed_mult (float):
            Speed multiplier while charging.
        charge_distance (float):
            Distance the charge tries to cover.
        charge_trigger_range (float):
            Distance within which charging can begin.
        slam_damage_mult (float):
            Multiplier applied to base damage for the slam.
        knockback_force (float):
            Knockback distance applied to the player.
        slow_duration (float):
            Duration of the slow effect applied by the slam.
        slow_factor (float):
            Slow multiplier applied to the player.
        last_charge_time (int):
            Timestamp of the last charge start.
        charge_timer (float):
            Remaining time in the current charge.
        charge_direction (pygame.Vector2):
            Direction used while charging.

    Methods:
        __init__(config=None):
            Initialize brute-specific tuning values.
        update(enemy, context):
            Drive charge and slam behavior.
        _charge_ready(now_ms):
            Check whether a new charge may start.
        _slam(enemy, player, enemy_pos, player_pos, now_ms):
            Apply slam damage, knockback, and slow.
    """
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
        diff = player_pos - enemy_pos
        distance_sq = diff.length_squared()

        if self.charge_timer > 0:
            self.charge_timer -= context.dt
            enemy.speed_multiplier = self.charge_speed_mult
            enemy.ai_state = "charge"
            enemy.target = enemy.pos + self.charge_direction * self.charge_distance
            if distance_sq <= (enemy.attack_range * 1.1) * (enemy.attack_range * 1.1) and self.ready(context.now_ms):
                self._slam(enemy, player, enemy_pos, player_pos, context.now_ms)
                self.charge_timer = 0.0
            if self.charge_timer <= 0:
                enemy.speed_multiplier = 1.0
            return

        enemy.speed_multiplier = 1.0

        if distance_sq <= (enemy.attack_range * enemy.attack_range) and self.ready(context.now_ms):
            self._slam(enemy, player, enemy_pos, player_pos, context.now_ms)
            return

        if distance_sq <= (self.charge_trigger_range * self.charge_trigger_range) and self._charge_ready(context.now_ms):
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
    """
    Melee attack pattern that applies poison to the player.

    Attributes:
        poison_duration (float):
            Duration of the poison effect.
        poison_dps (float):
            Damage per second applied by poison.
        strike_damage_mult (float):
            Damage multiplier for the strike.
        strike_range (float):
            Optional custom strike range.

    Methods:
        __init__(config=None):
            Initialize venomous-specific tuning values.
        update(enemy, context):
            Apply poison if the player is in range and cooldown allows it.
    """
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
        diff = player_pos - enemy_pos
        distance_sq = diff.length_squared()

        effective_range = self.strike_range or float(enemy.attack_range)
        if distance_sq > (effective_range * effective_range):
            return

        if not self.ready(context.now_ms):
            return

        damage = int(enemy.damage * self.strike_damage_mult)
        if damage > 0:
            player.take_damage(damage)
        player.add_effect(PoisonEffect(self.poison_duration, self.poison_dps))
        self.last_attack_time = context.now_ms


class ArcanistAttack(BaseAttack):
    """
    Ranged attack pattern that fires burning arcane bolts.

    Attributes:
        bolt_speed (float):
            Projectile speed.
        bolt_range (float):
            Maximum projectile travel distance.
        bolt_damage_mult (float):
            Damage multiplier for each bolt.
        burn_duration (float):
            Duration of the burn effect applied on hit.
        burn_dps (float):
            Damage per second of the burn effect.
        cast_range (float):
            Maximum distance at which the attack can be cast.
        spread_degrees (float):
            Random spread applied to each shot.

    Methods:
        __init__(config=None):
            Initialize arcanist-specific tuning values.
        update(enemy, context):
            Spawn an ArcaneBolt when the player is visible and in range.
    """
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
        diff = player_pos - enemy_pos
        distance_sq = diff.length_squared()

        if distance_sq > (self.cast_range * self.cast_range):
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


class TricksterAttack(BaseAttack):
    """
    Mobility attack pattern that teleports near the player and confuses them.

    Attributes:
        step_range (float):
            Maximum distance at which the teleport attack can trigger.
        step_distance (float):
            Distance used when repositioning around the player.
        step_attempts (int):
            Number of placement attempts before giving up.
        step_spread_degrees (float):
            Angular spread for candidate positions.
        strike_range (float):
            Distance within which the post-teleport strike lands.
        confuse_duration (float):
            Duration of the confusion effect.
        dizzy_duration (float):
            Duration of the dizziness effect.
        damage_mult (float):
            Damage multiplier for the strike.

    Methods:
        __init__(config=None):
            Initialize trickster-specific tuning values.
        update(enemy, context):
            Teleport, strike, and apply debuffs when possible.
    """
    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.step_range = float(self.config.get("step_range", 260.0))
        self.step_distance = float(self.config.get("step_distance", 80.0))
        self.step_attempts = int(self.config.get("step_attempts", 6))
        self.step_spread_degrees = float(self.config.get("step_spread_degrees", 140.0))
        self.strike_range = float(self.config.get("strike_range", 60.0))
        self.confuse_duration = float(self.config.get("confuse_duration", 3.0))
        self.dizzy_duration = float(self.config.get("dizzy_duration", 2.0))
        self.damage_mult = float(self.config.get("damage_mult", 0.7))

    def update(self, enemy: object, context: AttackContext):
        player = context.player
        if player is None:
            return

        enemy_center = _entity_center(enemy)
        player_center = _entity_center(player)
        diff = player_center - enemy_center
        distance_sq = diff.length_squared()

        if distance_sq > (self.step_range * self.step_range):
            return
        if not self.ready(context.now_ms):
            return

        direction = player_center - enemy_center
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        base_angle = math.atan2(direction.y, direction.x) + math.pi
        spread_rad = math.radians(self.step_spread_degrees)

        offset = enemy_center - enemy.pos
        new_pos = None
        for _ in range(self.step_attempts):
            angle = base_angle + random.uniform(-spread_rad, spread_rad)
            candidate_center = player_center + pygame.Vector2(math.cos(angle), math.sin(angle)) * self.step_distance
            candidate_pos = candidate_center - offset
            if _is_clear(enemy, candidate_pos, context.obstacles):
                new_pos = candidate_pos
                break

        if new_pos is None:
            return

        enemy.pos = new_pos
        enemy.ai_state = "blink"

        new_center = _entity_center(enemy)
        ndiff = new_center - player_center
        if ndiff.length_squared() <= (self.strike_range * self.strike_range):
            damage = int(enemy.damage * self.damage_mult)
            if damage > 0:
                player.take_damage(damage)
            player.add_effect(ConfusionEffect(self.confuse_duration))
            player.add_effect(DizzinessEffect(self.dizzy_duration))

        self.last_attack_time = context.now_ms


class BomberAttack(BaseAttack):
    """
    Ranged attack pattern that throws timed bombs at the player.

    Attributes:
        throw_range (float):
            Maximum distance at which bombs may be thrown.
        min_range (float):
            Preferred minimum distance from the player.
        bomb_speed (float):
            Projectile speed.
        bomb_range (float):
            Maximum bomb travel distance.
        blast_radius (float):
            Explosion radius.
        fuse_time (float):
            Time before the bomb explodes.
        damage_mult (float):
            Damage multiplier for the bomb.
        knockback_force (float):
            Knockback applied by the explosion.
        spread_degrees (float):
            Random spread applied to the throw angle.

    Methods:
        __init__(config=None):
            Initialize bomber-specific tuning values.
        update(enemy, context):
            Throw a bomb when the player is in range and cooldown allows it.
    """
    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.throw_range = float(self.config.get("throw_range", 320.0))
        self.min_range = float(self.config.get("min_range", 80.0))
        self.bomb_speed = float(self.config.get("bomb_speed", 260.0))
        self.bomb_range = float(self.config.get("bomb_range", 420.0))
        self.blast_radius = float(self.config.get("blast_radius", 95.0))
        self.fuse_time = float(self.config.get("fuse_time", 0.9))
        self.damage_mult = float(self.config.get("damage_mult", 1.1))
        self.knockback_force = float(self.config.get("knockback_force", 80.0))
        self.spread_degrees = float(self.config.get("spread_degrees", 12.0))

    def update(self, enemy: object, context: AttackContext):
        player = context.player
        if player is None:
            return

        enemy_pos = _entity_center(enemy)
        player_pos = _entity_center(player)
        diff = player_pos - enemy_pos
        distance_sq = diff.length_squared()

        if distance_sq > (self.throw_range * self.throw_range):
            return
        if not self.ready(context.now_ms):
            return

        direction = player_pos - enemy_pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        else:
            direction = direction.normalize()

        # compare squared distance to avoid an unnecessary sqrt and fix NameError
        if distance_sq < (self.min_range * self.min_range):
            direction *= -1

        if self.spread_degrees:
            direction = direction.rotate(random.uniform(-self.spread_degrees, self.spread_degrees))

        damage = max(1, int(enemy.damage * self.damage_mult))
        bomb = Bomb(
            enemy_pos + direction * 20,
            direction,
            self.bomb_speed,
            self.bomb_range,
            damage,
            self.blast_radius,
            self.fuse_time,
            self.knockback_force,
        )
        context.projectiles.append(bomb)
        self.last_attack_time = context.now_ms


def build_attack_controller(profile: str | None, config: dict | None = None) -> BaseAttack | None:
    name = (profile or "").lower()
    if name == "brute":
        return BruteAttack(config)
    if name == "venomous":
        return VenomousAttack(config)
    if name == "arcanist":
        return ArcanistAttack(config)
    if name == "trickster":
        return TricksterAttack(config)
    if name == "bomber":
        return BomberAttack(config)
    return None
