from __future__ import annotations

import math
import random

import pygame

from src.entities.monster_attacks import BaseAttack, AttackContext, _entity_center, _has_line_of_sight, _is_clear
from src.entities.projectile import TimeBolt, ChronoBurst
from database.effects import FreezeEffect, SlowEffect


class ChronosAttack(BaseAttack):
    """
    Three-phase boss attack controller for Chronos the Chronicler of Time.

    Phase 1 (100-70% HP): Temporal Bolt + Temporal Slow + Melee Strike
    Phase 2 (70-40% HP): Chrono Burst (AoE) + Time Rift (teleport) + faster bolts
    Phase 3 (40-0% HP): Eternal Storm (big AoE) + Time Stop (freeze) + enraged speed
    """

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.bolt_speed = float(self.config.get("bolt_speed", 450.0))
        self.bolt_range = float(self.config.get("bolt_range", 500.0))
        self.bolt_damage_mult = float(self.config.get("bolt_damage_mult", 0.85))
        self.slow_duration = float(self.config.get("slow_duration", 2.0))
        self.slow_factor = float(self.config.get("slow_factor", 0.5))
        self.melee_damage_mult = float(self.config.get("melee_damage_mult", 1.2))
        self.melee_range = float(self.config.get("melee_range", 60.0))
        self.spread_degrees = float(self.config.get("spread_degrees", 5.0))
        self.burst_cooldown_ms = int(self.config.get("burst_cooldown_ms", 3500))
        self.burst_radius = float(self.config.get("burst_radius", 100.0))
        self.burst_damage_mult = float(self.config.get("burst_damage_mult", 1.0))
        self.rift_cooldown_ms = int(self.config.get("rift_cooldown_ms", 4000))
        self.rift_distance = float(self.config.get("rift_distance", 150.0))
        self.storm_cooldown_ms = int(self.config.get("storm_cooldown_ms", 6000))
        self.storm_radius = float(self.config.get("storm_radius", 140.0))
        self.storm_damage_mult = float(self.config.get("storm_damage_mult", 1.5))
        self.freeze_duration = float(self.config.get("freeze_duration", 2.0))
        self.enrage_speed_mult = float(self.config.get("enrage_speed_mult", 1.6))
        self.last_burst_time = -self.burst_cooldown_ms
        self.last_rift_time = -self.rift_cooldown_ms
        self.last_storm_time = -self.storm_cooldown_ms
        self.strike_anim_duration = float(self.config.get("strike_anim_duration", 0.5))

    def _get_phase(self, enemy) -> int:
        if hasattr(enemy, "hp") and hasattr(enemy, "max_hp") and enemy.max_hp > 0:
            ratio = enemy.hp / enemy.max_hp
            if ratio <= 0.40:
                return 3
            if ratio <= 0.70:
                return 2
        return 1

    def _get_bolt_cooldown(self, phase: int) -> int:
        base = self.cooldown_ms
        if phase == 2:
            return max(300, int(base * 0.7))
        if phase == 3:
            return max(200, int(base * 0.5))
        return base

    def update(self, enemy: object, context: AttackContext):
        player = context.player
        if player is None:
            enemy.speed_multiplier = 1.0
            return

        phase = self._get_phase(enemy)
        enemy_pos = _entity_center(enemy)
        player_pos = _entity_center(player)
        diff = player_pos - enemy_pos
        distance_sq = diff.length_squared()

        if phase == 3:
            enemy.speed_multiplier = self.enrage_speed_mult
        else:
            enemy.speed_multiplier = 1.0

        if phase >= 3:
            storm_ready = (context.now_ms - self.last_storm_time) >= self.storm_cooldown_ms
            if storm_ready and distance_sq <= (self.storm_radius * self.storm_radius):
                damage = max(1, int(enemy.damage * self.storm_damage_mult))
                player.take_damage(damage)
                player.add_effect(FreezeEffect(self.freeze_duration))
                self.last_storm_time = context.now_ms
                if hasattr(enemy, "trigger_attack_anim"):
                    enemy.trigger_attack_anim(
                        "chronos_storm", 0.8,
                        direction=pygame.Vector2(0, -1), origin=enemy_pos, strength=1.8,
                    )
                burst = ChronoBurst(enemy_pos, damage, self.storm_radius, self.freeze_duration, 0.3)
                context.projectiles.append(burst)
                return

        if phase >= 2:
            burst_ready = (context.now_ms - self.last_burst_time) >= self.burst_cooldown_ms
            if burst_ready and distance_sq <= (self.burst_radius * self.burst_radius):
                damage = max(1, int(enemy.damage * self.burst_damage_mult))
                player.take_damage(damage)
                player.add_effect(SlowEffect(self.slow_duration, self.slow_factor))
                self.last_burst_time = context.now_ms
                if hasattr(enemy, "trigger_attack_anim"):
                    enemy.trigger_attack_anim(
                        "chronos_burst", 0.6,
                        direction=pygame.Vector2(0, -1), origin=enemy_pos, strength=1.4,
                    )
                burst = ChronoBurst(enemy_pos, damage, self.burst_radius, self.slow_duration, self.slow_factor)
                context.projectiles.append(burst)
                return

            rift_ready = (context.now_ms - self.last_rift_time) >= self.rift_cooldown_ms
            if rift_ready and distance_sq > (120.0 * 120.0):
                direction = player_pos - enemy_pos
                if direction.length_squared() > 0:
                    direction = direction.normalize()
                new_pos = enemy.pos + direction * self.rift_distance
                if _is_clear(enemy, new_pos, context.obstacles):
                    enemy.pos = new_pos
                    enemy.ai_state = "blink"
                    self.last_rift_time = context.now_ms
                    if hasattr(enemy, "trigger_attack_anim"):
                        enemy.trigger_attack_anim(
                            "chronos_rift", 0.4,
                            direction=direction, origin=enemy_pos, strength=1.2,
                        )
                    return

        effective_range = self.melee_range
        if distance_sq <= (effective_range * effective_range) and self.ready(context.now_ms):
            direction = player_pos - enemy_pos
            if direction.length_squared() == 0:
                direction = pygame.Vector2(1, 0)
            else:
                direction = direction.normalize()
            damage = max(1, int(enemy.damage * self.melee_damage_mult))
            player.take_damage(damage)
            knockback = 40.0 if phase < 3 else 70.0
            player.pos += direction * knockback
            self.last_attack_time = context.now_ms
            if hasattr(enemy, "trigger_attack_anim"):
                enemy.trigger_attack_anim(
                    "chronos_strike", self.strike_anim_duration,
                    direction=direction, origin=enemy_pos, strength=1.1 + phase * 0.2,
                )
            return

        cast_range = self.bolt_range
        if distance_sq > (cast_range * cast_range):
            return
        bolt_cd = self._get_bolt_cooldown(phase)
        now_ms = context.now_ms
        if now_ms - self.last_attack_time < bolt_cd:
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
        bolt = TimeBolt(
            enemy_pos, direction, self.bolt_speed, self.bolt_range,
            damage, self.slow_duration, self.slow_factor,
        )
        context.projectiles.append(bolt)
        self.last_attack_time = now_ms


def build_boss_attack_controller(profile: str | None, config: dict | None = None) -> BaseAttack | None:
    name = (profile or "").lower()
    if name == "chronos":
        return ChronosAttack(config)
    return None
