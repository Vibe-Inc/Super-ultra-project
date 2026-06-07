from __future__ import annotations

import math
import random

import pygame

from src.entities.monster_attacks import BaseAttack, AttackContext, _entity_center, _has_line_of_sight, _is_clear
from src.entities.projectile import (
    TimeBolt, ChronoBurst, TemporalSiphon, EternalChains, ParadoxMirror,
    TemporalWave, ChronoRift, DecayZone, TimeStopField,
)
from database.effects import FreezeEffect, SlowEffect, RootEffect, LethargyEffect


class ChronosAttack(BaseAttack):
    """
    Four-phase boss attack controller for Chronos the Chronicler of Time.

    Phase 1 (100-70% HP): Temporal Bolt + Melee Strike + Siphon Bolt + Temporal Nova
    Phase 2 (70-40% HP): + Chrono Burst + Time Rift + Eternal Chains + Time Shards
    Phase 3 (40-15% HP): + Eternal Storm + Paradox Mirror + Chrono Cascade
    Phase 4 (15-0% HP):  + Rift Barrage + Triple Bolt + all abilities boosted + berserk
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
        # burst
        self.burst_cooldown_ms = int(self.config.get("burst_cooldown_ms", 3500))
        self.burst_radius = float(self.config.get("burst_radius", 100.0))
        self.burst_damage_mult = float(self.config.get("burst_damage_mult", 1.0))
        # rift
        self.rift_cooldown_ms = int(self.config.get("rift_cooldown_ms", 4000))
        self.rift_distance = float(self.config.get("rift_distance", 150.0))
        # storm
        self.storm_cooldown_ms = int(self.config.get("storm_cooldown_ms", 6000))
        self.storm_radius = float(self.config.get("storm_radius", 140.0))
        self.storm_damage_mult = float(self.config.get("storm_damage_mult", 1.5))
        self.freeze_duration = float(self.config.get("freeze_duration", 2.0))
        self.enrage_speed_mult = float(self.config.get("enrage_speed_mult", 1.6))
        self.strike_anim_duration = float(self.config.get("strike_anim_duration", 0.5))
        # siphon
        self.last_siphon_time = -4000
        self.siphon_cooldown_ms = 4000
        # chains
        self.last_chain_time = -5000
        self.chain_cooldown_ms = 5000
        # burst
        self.last_burst_time = -self.burst_cooldown_ms
        # storm
        self.last_storm_time = -self.storm_cooldown_ms
        # rift
        self.last_rift_time = -self.rift_cooldown_ms
        # mirror
        self.last_mirror_time = -8000
        self.mirror_cooldown_ms = 8000
        # ─── NEW SPLASH ATTACKS ───
        # temporal nova (8 bolts radial ring)
        self.nova_cooldown_ms = int(self.config.get("nova_cooldown_ms", 5000))
        self.nova_bolt_count = int(self.config.get("nova_bolt_count", 8))
        self.nova_bolt_speed = float(self.config.get("nova_bolt_speed", 350.0))
        self.nova_bolt_range = float(self.config.get("nova_bolt_range", 300.0))
        self.nova_damage_mult = float(self.config.get("nova_damage_mult", 0.7))
        self.last_nova_time = -self.nova_cooldown_ms
        # time shards (5 bolts fan)
        self.shard_cooldown_ms = int(self.config.get("shard_cooldown_ms", 4500))
        self.shard_count = int(self.config.get("shard_count", 5))
        self.shard_spread_degrees = float(self.config.get("shard_spread_degrees", 25.0))
        self.shard_speed = float(self.config.get("shard_speed", 400.0))
        self.shard_range = float(self.config.get("shard_range", 400.0))
        self.shard_damage_mult = float(self.config.get("shard_damage_mult", 0.6))
        self.last_shard_time = -self.shard_cooldown_ms
        # chrono cascade (waves of bolts)
        self.cascade_cooldown_ms = int(self.config.get("cascade_cooldown_ms", 7000))
        self.cascade_waves = int(self.config.get("cascade_waves", 3))
        self.cascade_bolts_per_wave = int(self.config.get("cascade_bolts_per_wave", 3))
        self.cascade_speed = float(self.config.get("cascade_speed", 380.0))
        self.cascade_range = float(self.config.get("cascade_range", 450.0))
        self.cascade_damage_mult = float(self.config.get("cascade_damage_mult", 0.5))
        self.last_cascade_time = -self.cascade_cooldown_ms
        self._cascade_pending = []
        # rift barrage (teleport + 12 bolts radial)
        self.barrage_cooldown_ms = int(self.config.get("barrage_cooldown_ms", 8000))
        self.barrage_bolt_count = int(self.config.get("barrage_bolt_count", 12))
        self.barrage_speed = float(self.config.get("barrage_speed", 320.0))
        self.barrage_range = float(self.config.get("barrage_range", 350.0))
        self.barrage_damage_mult = float(self.config.get("barrage_damage_mult", 0.45))
        self.last_barrage_time = -self.barrage_cooldown_ms
        # triple bolt (berserk fan)
        self.last_triple_time = -6000
        self.triple_cooldown_ms = 6000
        # ─── TIME-THEMED ABILITIES ───
        # time stop (freeze player)
        self.timestop_cooldown_ms = int(self.config.get("timestop_cooldown_ms", 9000))
        self.timestop_radius = float(self.config.get("timestop_radius", 120.0))
        self.timestop_freeze_duration = float(self.config.get("timestop_freeze_duration", 1.5))
        self.timestop_damage_mult = float(self.config.get("timestop_damage_mult", 0.5))
        self.last_timestop_time = -self.timestop_cooldown_ms
        # temporal wave (expanding ring)
        self.wave_cooldown_ms = int(self.config.get("wave_cooldown_ms", 5500))
        self.wave_radius = float(self.config.get("wave_radius", 160.0))
        self.wave_damage_mult = float(self.config.get("wave_damage_mult", 0.8))
        self.last_wave_time = -self.wave_cooldown_ms
        # chrono rift (stationary turret)
        self.rift_cooldown2_ms = int(self.config.get("rift_cooldown2_ms", 7000))
        self.rift_duration = float(self.config.get("rift_duration", 4.0))
        self.rift_damage_mult = float(self.config.get("rift_damage_mult", 0.35))
        self.last_rift2_time = -self.rift_cooldown2_ms
        # decay aura (lethargy zone)
        self.decay_cooldown_ms = int(self.config.get("decay_cooldown_ms", 6500))
        self.decay_radius = float(self.config.get("decay_radius", 80.0))
        self.decay_damage_mult = float(self.config.get("decay_damage_mult", 0.3))
        self.last_decay_time = -self.decay_cooldown_ms
        # time reversal (heal self, damage player)
        self.reversal_cooldown_ms = int(self.config.get("reversal_cooldown_ms", 10000))
        self.reversal_heal = int(self.config.get("reversal_heal", 40))
        self.reversal_damage_mult = float(self.config.get("reversal_damage_mult", 0.6))
        self.last_reversal_time = -self.reversal_cooldown_ms
        # 3-phase melee configuration (windup -> telegraph -> strike)
        self.melee_windup_duration = float(self.config.get("melee_windup_duration", 0.45))
        self.melee_telegraph_duration = float(self.config.get("melee_telegraph_duration", 0.30))
        self.melee_strike_duration = float(self.config.get("melee_strike_duration", 0.18))
        self.melee_arc_angle = float(self.config.get("melee_arc_angle", 140.0))
        # pending melee state — applied at the end of the 3-phase animation
        self._pending_melee = None

    def _get_phase(self, enemy) -> int:
        if hasattr(enemy, "hp") and hasattr(enemy, "max_hp") and enemy.max_hp > 0:
            ratio = enemy.hp / enemy.max_hp
            if ratio <= 0.15:
                return 4
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
        if phase == 4:
            return max(150, int(base * 0.35))
        return base

    def _fire_bolt(self, enemy, context, direction, damage_mult=None, speed=None, rng=None):
        if damage_mult is None:
            damage_mult = self.bolt_damage_mult
        if speed is None:
            speed = self.bolt_speed
        if rng is None:
            rng = self.bolt_range
        damage = max(1, int(enemy.damage * damage_mult))
        bolt = TimeBolt(
            _entity_center(enemy), direction, speed, rng,
            damage, self.slow_duration, self.slow_factor,
        )
        context.projectiles.append(bolt)

    def _fire_siphon(self, enemy, context, direction):
        damage = max(1, int(enemy.damage * 0.7))
        heal = int(enemy.damage * 0.4)
        siphon = TemporalSiphon(
            _entity_center(enemy), direction, self.bolt_speed * 0.85,
            self.bolt_range * 0.8, damage, heal,
            slow_duration=1.5, slow_factor=0.6,
        )
        context.projectiles.append(siphon)

    def _fire_chains(self, enemy, context, direction):
        damage = max(1, int(enemy.damage * 0.6))
        chains = EternalChains(
            _entity_center(enemy), direction, self.bolt_speed * 0.7,
            self.bolt_range * 0.7, damage,
            root_duration=1.5, slow_duration=2.0, slow_factor=0.4,
        )
        context.projectiles.append(chains)

    def _place_mirror(self, enemy, context, pos=None):
        if pos is None:
            pos = _entity_center(enemy)
        damage = max(1, int(enemy.damage * 0.3))
        mirror = ParadoxMirror(
            pos, damage, radius=90.0, duration=3.0,
            slow_duration=2.0, slow_factor=0.5,
        )
        context.projectiles.append(mirror)

    def _teleport_rift(self, enemy, context, direction):
        new_pos = enemy.pos + direction * self.rift_distance
        if _is_clear(enemy, new_pos, context.obstacles):
            enemy.pos = new_pos
            enemy.ai_state = "blink"
            return True
        return False

    def _begin_melee_phase(self, enemy, enemy_pos, player_pos, phase, direction):
        """Start a 3-phase melee attack (windup -> telegraph -> strike)."""
        damage = max(1, int(enemy.damage * self.melee_damage_mult))
        knockback = 40.0 if phase < 3 else 70.0
        self._pending_melee = {
            "damage": damage,
            "knockback": knockback,
            "direction": pygame.Vector2(direction),
            "phase": phase,
            "applied": False,
        }
        if hasattr(enemy, "start_attack_phase"):
            enemy.start_attack_phase(
                wind_up=self.melee_windup_duration,
                telegraph=self.melee_telegraph_duration,
                strike_duration=self.melee_strike_duration,
                telegraph_range=self.melee_range * 1.4,
                telegraph_angle=self.melee_arc_angle,
                damage=damage,
                knockback=knockback,
            )
            enemy.attack_windup_range = self.melee_range * 1.4
            enemy.attack_windup_angle = self.melee_arc_angle
            enemy.attack_windup_coverage = "arc"
        if hasattr(enemy, "trigger_attack_anim"):
            enemy.trigger_attack_anim(
                "chronos_strike",
                self.melee_windup_duration + self.melee_telegraph_duration + self.melee_strike_duration,
                direction=pygame.Vector2(direction),
                origin=enemy_pos,
                strength=1.1 + phase * 0.2,
            )

    def _apply_pending_melee(self, enemy, player):
        """Apply pending melee damage + knockback on the strike frame."""
        if not self._pending_melee:
            return False
        if not getattr(enemy, "_phase_strike_ready", False):
            return False
        if getattr(enemy, "_attack_phase", None) != "strike":
            return False
        pm = self._pending_melee
        if pm.get("applied"):
            return False
        if player is not None and pm.get("damage", 0) > 0:
            player.take_damage(pm["damage"])
            player.pos += pm["direction"] * pm.get("knockback", 0.0)
        pm["applied"] = True
        self._pending_melee = None
        enemy._phase_strike_ready = False
        return True

    # ─── SPLASH ATTACK: TEMPORAL NOVA ───
    def _do_temporal_nova(self, enemy, context, now_ms):
        """Fire N bolts in a perfect radial ring around Chronos."""
        enemy_pos = _entity_center(enemy)
        for i in range(self.nova_bolt_count):
            angle = (math.pi * 2 / self.nova_bolt_count) * i
            direction = pygame.Vector2(math.cos(angle), math.sin(angle))
            self._fire_bolt(enemy, context, direction,
                            damage_mult=self.nova_damage_mult,
                            speed=self.nova_bolt_speed, rng=self.nova_bolt_range)
        self.last_nova_time = now_ms
        if hasattr(enemy, "trigger_attack_anim"):
            enemy.trigger_attack_anim(
                "chronos_storm", 0.7,
                direction=pygame.Vector2(0, -1), origin=enemy_pos, strength=1.5,
            )

    # ─── SPLASH ATTACK: TIME SHARDS ───
    def _do_time_shards(self, enemy, context, now_ms, player_pos, enemy_pos):
        """Fire a fan of narrow bolts toward the player."""
        direction = player_pos - enemy_pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        else:
            direction = direction.normalize()
        total_spread = self.shard_spread_degrees * 2
        step = total_spread / max(1, self.shard_count - 1) if self.shard_count > 1 else 0
        base_angle = math.atan2(direction.y, direction.x)
        for i in range(self.shard_count):
            if self.shard_count == 1:
                shard_dir = direction
            else:
                angle = math.degrees(base_angle) - self.shard_spread_degrees + step * i
                rad = math.radians(angle)
                shard_dir = pygame.Vector2(math.cos(rad), math.sin(rad))
            self._fire_bolt(enemy, context, shard_dir,
                            damage_mult=self.shard_damage_mult,
                            speed=self.shard_speed, rng=self.shard_range)
        self.last_shard_time = now_ms
        if hasattr(enemy, "trigger_attack_anim"):
            enemy.trigger_attack_anim(
                "chronos_burst", 0.5,
                direction=direction, origin=enemy_pos, strength=1.3,
            )

    # ─── SPLASH ATTACK: CHRONO CASCADE ───
    def _do_chrono_cascade(self, enemy, context, now_ms, player_pos, enemy_pos):
        """Fire multiple waves of bolts with delays between each wave."""
        self._cascade_pending = []
        direction = player_pos - enemy_pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        else:
            direction = direction.normalize()
        base_angle = math.atan2(direction.y, direction.x)
        for wave in range(self.cascade_waves):
            wave_delay = wave * 0.3
            fan_spread = 15.0 + wave * 10.0
            wave_bolts = self.cascade_bolts_per_wave
            for bi in range(wave_bolts):
                if wave_bolts == 1:
                    bolt_dir = direction
                else:
                    angle_deg = math.degrees(base_angle) - fan_spread + (fan_spread * 2 / (wave_bolts - 1)) * bi
                    rad = math.radians(angle_deg)
                    bolt_dir = pygame.Vector2(math.cos(rad), math.sin(rad))
                self._cascade_pending.append({
                    "delay": wave_delay,
                    "direction": bolt_dir,
                    "fired": False,
                })
        self.last_cascade_time = now_ms
        if hasattr(enemy, "trigger_attack_anim"):
            enemy.trigger_attack_anim(
                "chronos_burst", 0.6,
                direction=direction, origin=enemy_pos, strength=1.4,
            )

    def _tick_cascade(self, enemy, context, dt):
        """Process pending cascade bolts."""
        if not self._cascade_pending:
            return
        for entry in self._cascade_pending:
            entry["delay"] -= dt
            if entry["delay"] <= 0 and not entry["fired"]:
                entry["fired"] = True
                self._fire_bolt(enemy, context, entry["direction"],
                                damage_mult=self.cascade_damage_mult,
                                speed=self.cascade_speed, rng=self.cascade_range)
        self._cascade_pending = [e for e in self._cascade_pending if not e["fired"]]

    # ─── SPLASH ATTACK: RIFT BARRAGE ───
    def _do_rift_barrage(self, enemy, context, now_ms, player_pos, enemy_pos):
        """Teleport behind the player, then fire bolts in all directions."""
        direction = player_pos - enemy_pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        else:
            direction = direction.normalize()
        behind_player = player_pos + direction * -80.0
        if _is_clear(enemy, behind_player, context.obstacles):
            old_pos = pygame.Vector2(enemy.pos)
            enemy.pos = behind_player
            enemy.ai_state = "blink"
            if hasattr(enemy, "trigger_attack_anim"):
                enemy.trigger_attack_anim(
                    "chronos_rift", 0.4,
                    direction=direction, origin=old_pos, strength=1.6,
                )
            new_enemy_pos = _entity_center(enemy)
            for i in range(self.barrage_bolt_count):
                angle = (math.pi * 2 / self.barrage_bolt_count) * i
                bolt_dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                self._fire_bolt(enemy, context, bolt_dir,
                                damage_mult=self.barrage_damage_mult,
                                speed=self.barrage_speed, rng=self.barrage_range)
            self.last_barrage_time = now_ms
        else:
            self.last_barrage_time = now_ms - self.barrage_cooldown_ms // 2

    # ─── TIME STOP ───
    def _do_time_stop(self, enemy, context, now_ms, player_pos, enemy_pos):
        """Create a time-stop field that freezes the player."""
        damage = max(1, int(enemy.damage * self.timestop_damage_mult))
        field = TimeStopField(
            player_pos, damage, self.timestop_radius,
            self.timestop_freeze_duration, duration=1.0,
        )
        context.projectiles.append(field)
        self.last_timestop_time = now_ms
        if hasattr(enemy, "trigger_attack_anim"):
            enemy.trigger_attack_anim(
                "chronos_storm", 0.6,
                direction=pygame.Vector2(0, -1), origin=enemy_pos, strength=1.6,
            )

    # ─── TEMPORAL WAVE ───
    def _do_temporal_wave(self, enemy, context, now_ms):
        """Emit an expanding ring of time energy."""
        enemy_pos = _entity_center(enemy)
        damage = max(1, int(enemy.damage * self.wave_damage_mult))
        wave = TemporalWave(
            enemy_pos, damage, self.wave_radius, duration=0.8,
            slow_duration=1.5, slow_factor=0.5,
        )
        context.projectiles.append(wave)
        self.last_wave_time = now_ms
        if hasattr(enemy, "trigger_attack_anim"):
            enemy.trigger_attack_anim(
                "chronos_storm", 0.5,
                direction=pygame.Vector2(0, -1), origin=enemy_pos, strength=1.3,
            )

    # ─── CHRONO RIFT (stationary turret) ───
    def _do_chrono_rift(self, enemy, context, now_ms, player_pos, enemy_pos):
        """Place a rift near the player that fires bolts periodically."""
        mid = pygame.Vector2(
            (enemy_pos.x + player_pos.x) / 2,
            (enemy_pos.y + player_pos.y) / 2,
        )
        damage = max(1, int(enemy.damage * self.rift_damage_mult))
        rift = ChronoRift(
            mid, damage, self.rift_duration, fire_interval=0.6,
            bolt_speed=300.0, bolt_range=350.0,
            slow_duration=1.0, slow_factor=0.7,
        )
        context.projectiles.append(rift)
        self.last_rift2_time = now_ms
        if hasattr(enemy, "trigger_attack_anim"):
            enemy.trigger_attack_anim(
                "chronos_rift", 0.4,
                direction=pygame.Vector2(0, -1), origin=enemy_pos, strength=1.1,
            )

    # ─── DECAY AURA ───
    def _do_decay_aura(self, enemy, context, now_ms, player_pos, enemy_pos):
        """Place a lingering decay zone that applies lethargy."""
        damage = max(1, int(enemy.damage * self.decay_damage_mult))
        zone = DecayZone(
            player_pos, damage, self.decay_radius, duration=3.5,
            tick_interval=0.8, lethargy_duration=2.0,
            slow_factor=0.6, cooldown_mult=1.4,
        )
        context.projectiles.append(zone)
        self.last_decay_time = now_ms
        if hasattr(enemy, "trigger_attack_anim"):
            enemy.trigger_attack_anim(
                "chronos_burst", 0.5,
                direction=pygame.Vector2(0, -1), origin=enemy_pos, strength=1.2,
            )

    # ─── TIME REVERSAL ───
    def _do_time_reversal(self, enemy, context, now_ms, player_pos, enemy_pos):
        """Reverse time flow — heal Chronos and damage the player."""
        player = context.player
        if player is None:
            return
        damage = max(1, int(enemy.damage * self.reversal_damage_mult))
        player.take_damage(damage)
        if hasattr(enemy, "hp") and hasattr(enemy, "max_hp"):
            old_hp = enemy.hp
            enemy.hp = min(enemy.max_hp, enemy.hp + self.reversal_heal)
        self.last_reversal_time = now_ms
        if hasattr(enemy, "trigger_attack_anim"):
            enemy.trigger_attack_anim(
                "chronos_storm", 0.7,
                direction=pygame.Vector2(0, -1), origin=enemy_pos, strength=1.5,
            )
        # visual burst
        burst = ChronoBurst(
            _entity_center(enemy), 0, self.wave_radius * 0.8, 0.4, 0.3,
        )
        context.projectiles.append(burst)

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
        now_ms = context.now_ms

        # tick cascade
        self._tick_cascade(enemy, context, context.dt)

        # speed management
        if phase >= 4:
            enemy.speed_multiplier = self.enrage_speed_mult * 1.3
        elif phase >= 3:
            enemy.speed_multiplier = self.enrage_speed_mult
        else:
            enemy.speed_multiplier = 1.0

        # If a 3-phase melee is in progress, apply the strike damage
        if self._pending_melee and self._apply_pending_melee(enemy, player):
            return

        # ─── PHASE 4: BERSERK ───
        if phase >= 4:
            # rift barrage
            barrage_ready = (now_ms - self.last_barrage_time) >= self.barrage_cooldown_ms
            if barrage_ready:
                self._do_rift_barrage(enemy, context, now_ms, player_pos, enemy_pos)
                return

            # time reversal (heal self)
            reversal_ready = (now_ms - self.last_reversal_time) >= self.reversal_cooldown_ms
            if reversal_ready and enemy.hp < enemy.max_hp * 0.6:
                self._do_time_reversal(enemy, context, now_ms, player_pos, enemy_pos)
                return

            # triple bolt fan
            triple_ready = (now_ms - self.last_triple_time) >= self.triple_cooldown_ms
            if triple_ready and distance_sq <= (self.bolt_range * self.bolt_range):
                direction = player_pos - enemy_pos
                if direction.length_squared() > 0:
                    direction = direction.normalize()
                for angle_offset in [-15.0, 0.0, 15.0]:
                    d = direction.rotate(angle_offset)
                    self._fire_bolt(enemy, context, d, self.bolt_damage_mult * 1.1)
                self.last_triple_time = now_ms
                if hasattr(enemy, "trigger_attack_anim"):
                    enemy.trigger_attack_anim(
                        "chronos_burst", 0.5,
                        direction=pygame.Vector2(0, -1), origin=enemy_pos, strength=1.5,
                    )
                return

        # ─── PHASE 3: STORM + MIRROR + CASCADE + DECAY + REVERSAL ───
        if phase >= 3:
            # time reversal (heal self, damage player)
            reversal_ready = (now_ms - self.last_reversal_time) >= self.reversal_cooldown_ms
            if reversal_ready and enemy.hp < enemy.max_hp * 0.5:
                self._do_time_reversal(enemy, context, now_ms, player_pos, enemy_pos)
                return

            # decay aura (lethargy zone on player)
            decay_ready = (now_ms - self.last_decay_time) >= self.decay_cooldown_ms
            if decay_ready and distance_sq <= (200.0 * 200.0):
                self._do_decay_aura(enemy, context, now_ms, player_pos, enemy_pos)
                return

            # chrono cascade
            cascade_ready = (now_ms - self.last_cascade_time) >= self.cascade_cooldown_ms
            if cascade_ready and distance_sq <= (self.cascade_range * self.cascade_range * 1.5):
                self._do_chrono_cascade(enemy, context, now_ms, player_pos, enemy_pos)
                return

            # eternal storm
            storm_ready = (now_ms - self.last_storm_time) >= self.storm_cooldown_ms
            if storm_ready and distance_sq <= (self.storm_radius * self.storm_radius * 1.5):
                damage = max(1, int(enemy.damage * self.storm_damage_mult))
                player.take_damage(damage)
                player.add_effect(FreezeEffect(self.freeze_duration))
                self.last_storm_time = now_ms
                if hasattr(enemy, "trigger_attack_anim"):
                    enemy.trigger_attack_anim(
                        "chronos_storm", 0.8,
                        direction=pygame.Vector2(0, -1), origin=enemy_pos, strength=1.8,
                    )
                burst = ChronoBurst(enemy_pos, damage, self.storm_radius, self.freeze_duration, 0.3)
                context.projectiles.append(burst)
                return

            # paradox mirror
            mirror_ready = (now_ms - self.last_mirror_time) >= self.mirror_cooldown_ms
            if mirror_ready and distance_sq <= (200.0 * 200.0):
                mid_pos = pygame.Vector2(
                    (enemy_pos.x + player_pos.x) / 2,
                    (enemy_pos.y + player_pos.y) / 2,
                )
                self._place_mirror(enemy, context, mid_pos)
                self.last_mirror_time = now_ms
                if hasattr(enemy, "trigger_attack_anim"):
                    enemy.trigger_attack_anim(
                        "chronos_rift", 0.4,
                        direction=pygame.Vector2(0, -1), origin=enemy_pos, strength=1.0,
                    )
                return

        # ─── PHASE 2: BURST + RIFT + CHAINS + SHARDS + TIME STOP + RIFT TURRET ───
        if phase >= 2:
            # time stop (freeze player)
            timestop_ready = (now_ms - self.last_timestop_time) >= self.timestop_cooldown_ms
            if timestop_ready and distance_sq <= (250.0 * 250.0):
                self._do_time_stop(enemy, context, now_ms, player_pos, enemy_pos)
                return

            # chrono rift (stationary turret near player)
            rift2_ready = (now_ms - self.last_rift2_time) >= self.rift_cooldown2_ms
            if rift2_ready and distance_sq <= (300.0 * 300.0):
                self._do_chrono_rift(enemy, context, now_ms, player_pos, enemy_pos)
                return

            # time shards (fan)
            shard_ready = (now_ms - self.last_shard_time) >= self.shard_cooldown_ms
            if shard_ready and distance_sq <= (self.shard_range * self.shard_range * 1.2):
                self._do_time_shards(enemy, context, now_ms, player_pos, enemy_pos)
                return

            # chrono burst
            burst_ready = (now_ms - self.last_burst_time) >= self.burst_cooldown_ms
            if burst_ready and distance_sq <= (self.burst_radius * self.burst_radius * 1.2):
                damage = max(1, int(enemy.damage * self.burst_damage_mult))
                player.take_damage(damage)
                player.add_effect(SlowEffect(self.slow_duration, self.slow_factor))
                self.last_burst_time = now_ms
                if hasattr(enemy, "trigger_attack_anim"):
                    enemy.trigger_attack_anim(
                        "chronos_burst", 0.6,
                        direction=pygame.Vector2(0, -1), origin=enemy_pos, strength=1.4,
                    )
                burst = ChronoBurst(enemy_pos, damage, self.burst_radius, self.slow_duration, self.slow_factor)
                context.projectiles.append(burst)
                return

            # eternal chains
            chain_ready = (now_ms - self.last_chain_time) >= self.chain_cooldown_ms
            if chain_ready and distance_sq <= (self.bolt_range * self.bolt_range):
                direction = player_pos - enemy_pos
                if direction.length_squared() > 0:
                    direction = direction.normalize()
                self._fire_chains(enemy, context, direction)
                self.last_chain_time = now_ms
                if hasattr(enemy, "trigger_attack_anim"):
                    enemy.trigger_attack_anim(
                        "chronos_burst", 0.5,
                        direction=direction, origin=enemy_pos, strength=1.2,
                    )
                return

            # time rift
            rift_ready = (now_ms - self.last_rift_time) >= self.rift_cooldown_ms
            if rift_ready and distance_sq > (120.0 * 120.0):
                direction = player_pos - enemy_pos
                if direction.length_squared() > 0:
                    direction = direction.normalize()
                if self._teleport_rift(enemy, context, direction):
                    self.last_rift_time = now_ms
                    if hasattr(enemy, "trigger_attack_anim"):
                        enemy.trigger_attack_anim(
                            "chronos_rift", 0.4,
                            direction=direction, origin=enemy_pos, strength=1.2,
                        )
                    return

        # ─── PHASE 1+: TEMPORAL NOVA + TEMPORAL WAVE ───
        wave_ready = (now_ms - self.last_wave_time) >= self.wave_cooldown_ms
        if wave_ready and distance_sq <= (200.0 * 200.0):
            self._do_temporal_wave(enemy, context, now_ms)
            return

        nova_ready = (now_ms - self.last_nova_time) >= self.nova_cooldown_ms
        if nova_ready and distance_sq <= (250.0 * 250.0):
            self._do_temporal_nova(enemy, context, now_ms)
            return

        # ─── MELEE STRIKE (3-phase, parryable) ───
        effective_range = self.melee_range
        in_melee_range = distance_sq <= (effective_range * effective_range)
        already_attacking = hasattr(enemy, "is_in_attack") and enemy.is_in_attack()
        if in_melee_range and self.ready(context.now_ms) and not already_attacking:
            direction = player_pos - enemy_pos
            if direction.length_squared() == 0:
                direction = pygame.Vector2(1, 0)
            else:
                direction = direction.normalize()
            self._begin_melee_phase(enemy, enemy_pos, player_pos, phase, direction)
            self.last_attack_time = now_ms
            return
        if self._pending_melee and self._apply_pending_melee(enemy, player):
            return

        # ─── RANGED ATTACKS ───
        cast_range = self.bolt_range
        if distance_sq > (cast_range * cast_range):
            return
        bolt_cd = self._get_bolt_cooldown(phase)
        if now_ms - self.last_attack_time < bolt_cd:
            return
        if not _has_line_of_sight(enemy_pos, player_pos, context.obstacles):
            return

        direction = player_pos - enemy_pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        else:
            direction = direction.normalize()

        # siphon bolt
        siphon_ready = (now_ms - self.last_siphon_time) >= self.siphon_cooldown_ms
        if siphon_ready and random.random() < 0.3:
            if self.spread_degrees:
                direction = direction.rotate(random.uniform(-self.spread_degrees, self.spread_degrees))
            self._fire_siphon(enemy, context, direction)
            self.last_siphon_time = now_ms
            self.last_attack_time = now_ms
            if hasattr(enemy, "trigger_attack_anim"):
                enemy.trigger_attack_anim(
                    "chronos_burst", 0.4,
                    direction=direction, origin=enemy_pos, strength=1.0,
                )
            return

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
