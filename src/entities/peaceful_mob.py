"""
Peaceful majestic mobs that roam the world, adding ambient life and wonder.

These creatures are non-aggressive and feature unique behaviors:
  - Wandering / idling with gentle animations
  - Passive aura effects (healing, speed boost, mana regen, etc.)
  - React to the player's proximity (curiosity, shyness, following)
  - Unique movement patterns per species

Each mob type is defined by a ``PEACEFUL_MOB_REGISTRY`` entry that
packages all the stats, visual style, and behavior parameters.
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame

from src.core.logger import logger
from src.entities.peaceful_mob_visuals import build_peaceful_mob_animations, DRAW_FUNCS

if TYPE_CHECKING:
    from src.entities.character import Character


# ============================================================
# MOB TYPE REGISTRY
# ============================================================

PEACEFUL_MOB_REGISTRY: dict[str, dict] = {
    "grove_titan": {
        "name": "Grove Titan",
        "description": "A small, gentle tree creature that waddles and hums.",
        "hp": 80,
        "speed": 25,
        "animation_size": (80, 90),
        "animation_speed": 3,
        "aura_color": (140, 200, 100),
        "aura_radius": 110.0,
        "aura_effect": "stamina_regen",
        "aura_magnitude": 3.0,
        "curiosity_range": 180.0,
        "shyness_range": 60.0,
        "wander_radius": 150.0,
        "wander_pause": 5.0,
        "idle_behavior": "sway",
        "xp_reward": 0,
    },
    "singing_stone": {
        "name": "Singing Stone",
        "description": "A gentle living rock that hums melodically, with glowing runes.",
        "hp": 60,
        "speed": 15,
        "animation_size": (72, 80),
        "animation_speed": 2,
        "aura_color": (200, 220, 160),
        "aura_radius": 100.0,
        "aura_effect": "xp_bonus",
        "aura_magnitude": 0.15,
        "curiosity_range": 150.0,
        "shyness_range": 40.0,
        "wander_radius": 80.0,
        "wander_pause": 6.0,
        "idle_behavior": "hum",
        "xp_reward": 0,
    },
    "ember_phoenix": {
        "name": "Ember Phoenix",
        "description": "A radiant bird of gentle flame that radiates warmth and healing light.",
        "hp": 50,
        "speed": 50,
        "animation_size": (84, 90),
        "animation_speed": 6,
        "aura_color": (255, 180, 100),
        "aura_radius": 120.0,
        "aura_effect": "heal",
        "aura_magnitude": 2.0,
        "curiosity_range": 250.0,
        "shyness_range": 90.0,
        "wander_radius": 220.0,
        "wander_pause": 3.0,
        "idle_behavior": "hover",
        "xp_reward": 0,
    },
    "coral_golem": {
        "name": "Coral Golem",
        "description": "A living coral formation that pulses with deep ocean energy.",
        "hp": 70,
        "speed": 18,
        "animation_size": (76, 80),
        "animation_speed": 2,
        "aura_color": (220, 140, 160),
        "aura_radius": 100.0,
        "aura_effect": "stamina_regen",
        "aura_magnitude": 4.0,
        "curiosity_range": 160.0,
        "shyness_range": 50.0,
        "wander_radius": 90.0,
        "wander_pause": 5.5,
        "idle_behavior": "hum",
        "xp_reward": 0,
    },
    "void_butterfly": {
        "name": "Void Butterfly",
        "description": "A massive butterfly whose wings reveal glimpses of the distant cosmos.",
        "hp": 40,
        "speed": 30,
        "animation_size": (92, 84),
        "animation_speed": 4,
        "aura_color": (150, 120, 220),
        "aura_radius": 130.0,
        "aura_effect": "mana_regen",
        "aura_magnitude": 2.5,
        "curiosity_range": 280.0,
        "shyness_range": 120.0,
        "wander_radius": 200.0,
        "wander_pause": 4.0,
        "idle_behavior": "flutter",
        "xp_reward": 0,
    },
    "moss_rabbit": {
        "name": "Moss Rabbit",
        "description": "A fluffy rabbit with moss and tiny flowers growing on its back.",
        "hp": 30,
        "speed": 65,
        "animation_size": (72, 68),
        "animation_speed": 8,
        "aura_color": (130, 200, 130),
        "aura_radius": 95.0,
        "aura_effect": "heal",
        "aura_magnitude": 1.0,
        "curiosity_range": 260.0,
        "shyness_range": 110.0,
        "wander_radius": 300.0,
        "wander_pause": 2.0,
        "idle_behavior": "flutter",
        "xp_reward": 0,
    },
    "crystal_fox": {
        "name": "Crystal Fox",
        "description": "A sleek fox whose fur shimmers like cut gemstones in the sunlight.",
        "hp": 45,
        "speed": 55,
        "animation_size": (80, 78),
        "animation_speed": 6,
        "aura_color": (160, 200, 255),
        "aura_radius": 110.0,
        "aura_effect": "speed_boost",
        "aura_magnitude": 0.15,
        "curiosity_range": 240.0,
        "shyness_range": 90.0,
        "wander_radius": 260.0,
        "wander_pause": 2.8,
        "idle_behavior": "prowl",
        "xp_reward": 0,
    },
    "fairy_cat": {
        "name": "Fairy Cat",
        "description": "A graceful feline with iridescent wings and eyes like tiny moons.",
        "hp": 35,
        "speed": 58,
        "animation_size": (78, 80),
        "animation_speed": 7,
        "aura_color": (220, 180, 255),
        "aura_radius": 115.0,
        "aura_effect": "stamina_regen",
        "aura_magnitude": 3.5,
        "curiosity_range": 250.0,
        "shyness_range": 95.0,
        "wander_radius": 270.0,
        "wander_pause": 2.2,
        "idle_behavior": "prowl",
        "xp_reward": 0,
    },

}


# ============================================================
# PEACEFUL MOB CLASS
# ============================================================

class PeacefulMob:
    """
    A non-aggressive majestic creature that roams the world.

    Behaviors:
      - Wander between random points within a radius of its spawn.
      - Idle with species-specific animations (hover, graze, float, etc.).
      - React to the player: curiosity (approach), shyness (retreat).
      - Emit a passive aura that provides a beneficial effect to the player.

    Attributes:
        mob_type (str): Registry key identifying this mob's species.
        name (str): Display name.
        pos (pygame.Vector2): World position.
        spawn_pos (pygame.Vector2): Original spawn position.
        speed (float): Movement speed in px/s.
        hp (int): Current HP (effectively infinite for peaceful mobs).
        max_hp (int): Maximum HP.
        animations (dict): Animation frames by direction.
        animations_flipped (dict): Flipped side frames.
        direction (str): Current facing direction.
        image (pygame.Surface): Current frame.
        frame_index (int): Current animation frame.
        animation_speed (float): Frames per second.
        time_accumulator (float): Frame timing.
        flip (bool): Horizontal flip.
        moving (bool): Whether currently moving.
        aura_color (tuple): RGB color for the aura glow.
        aura_radius (float): Radius of the passive aura.
        aura_effect (str): Type of passive effect.
        aura_magnitude (float): Strength of the passive effect.
        curiosity_range (float): Distance at which mob notices player.
        shyness_range (float): Distance at which mob retreats.
        wander_radius (float): Max distance from spawn to wander.
        wander_pause (float): Seconds to idle between wander moves.
        wander_target (pygame.Vector2 | None): Current wander destination.
        wander_timer (float): Timer for wander pauses.
        idle_behavior (str): Species-specific idle animation key.
        mood (str): Current behavioral mood: "idle", "wander", "curious", "shy".
        player_ref (Character | None): Reference to nearby player.
        particles (list): Ambient particle effects.
        _aura_timer (float): Timer for aura effect ticks.
    """

    def __init__(
        self,
        x: float,
        y: float,
        mob_type: str,
        custom_config: dict | None = None,
    ):
        config = PEACEFUL_MOB_REGISTRY.get(mob_type)
        if config is None:
            raise ValueError(f"Unknown peaceful mob type: {mob_type!r}")

        if custom_config:
            config = {**config, **custom_config}

        self.mob_type = mob_type
        self.name = config["name"]
        self.description = config["description"]

        # Position & movement
        self.pos = pygame.Vector2(x, y)
        self.spawn_pos = self.pos.copy()
        self.base_speed = config["speed"]
        self.speed = self.base_speed
        self.velocity = pygame.Vector2(0, 0)

        # Health
        self.hp = config["hp"]
        self.max_hp = config["hp"]
        self.shield = 0.0
        self.hit_flash_timer = 0.0
        self.effects: list = []

        # Animation
        anim_size = config["animation_size"]
        self.animations = build_peaceful_mob_animations(mob_type, anim_size)
        self.animations_flipped = {
            "side": [pygame.transform.flip(f, True, False) for f in self.animations["side"]]
        }
        self.direction = random.choice(["down", "side"])
        self.image = self.animations[self.direction][0]
        self.rect = self.image.get_rect(topleft=(int(x), int(y)))
        self.flip = False
        self.frame_index = 0
        self.animation_speed = config["animation_speed"]
        self.time_accumulator = 0.0
        self.moving = False
        self._animation_size = anim_size

        # Aura / passive effect
        self.aura_color = config["aura_color"]
        self.aura_radius = config["aura_radius"]
        self.aura_effect = config["aura_effect"]
        self.aura_magnitude = config["aura_magnitude"]

        # Behavior parameters
        self.curiosity_range = config["curiosity_range"]
        self.shyness_range = config["shyness_range"]
        self.wander_radius = config["wander_radius"]
        self.wander_pause = config["wander_pause"]
        self.idle_behavior = config["idle_behavior"]

        # Behavior state
        self.mood = "idle"  # idle | wander | curious | shy
        self.wander_target: pygame.Vector2 | None = None
        self.wander_timer: float = 0.0
        self.idle_timer: float = 0.0
        self.player_ref: Character | None = None

        # Aura effect accumulator
        self._aura_timer: float = 0.0

        # Ambient particles
        self.particles: list[dict] = []

        # Floating texts
        self.floating_texts: list[dict] = []

        # Interaction state
        self.interaction_cooldown: float = 0.0
        self.met_player: bool = False  # True once player has been nearby

        logger.info(f"Spawned peaceful mob {self.name} ({self.mob_type}) at ({x:.0f}, {y:.0f})")

    # ----------------------------------------------------------
    # COMBAT
    # ----------------------------------------------------------

    def take_damage(self, amount: int) -> bool:
        self.hp = max(0, self.hp - amount)
        self.hit_flash_timer = 0.15
        logger.info(f"Peaceful mob {self.name} took {amount} damage, HP: {self.hp}/{self.max_hp}")
        return self.hp <= 0

    def is_dead(self) -> bool:
        return self.hp <= 0

    def add_effect(self, effect):
        for e in self.effects:
            if type(e) == type(effect):
                self.effects.remove(e)
                self.effects.append(effect)
                return
        self.effects.append(effect)

    # ----------------------------------------------------------
    # COLLISION
    # ----------------------------------------------------------

    def get_rect(self) -> pygame.Rect:
        w = self.image.get_width()
        h = self.image.get_height()
        self.rect = pygame.Rect(int(self.pos.x), int(self.pos.y), w, h)
        return self.rect

    # ----------------------------------------------------------
    # MOVEMENT / WANDERING
    # ----------------------------------------------------------

    def _pick_wander_target(self):
        """Choose a random point within wander_radius of the spawn point."""
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, self.wander_radius)
        tx = self.spawn_pos.x + math.cos(angle) * dist
        ty = self.spawn_pos.y + math.sin(angle) * dist
        self.wander_target = pygame.Vector2(tx, ty)

    def _move_toward(self, target: pygame.Vector2, dt: float):
        """Set velocity to move toward a target position."""
        diff = target - self.pos
        if diff.length_squared() < 4.0:
            self.moving = False
            self.velocity = pygame.Vector2(0, 0)
            return True  # arrived
        self.velocity = diff.normalize()
        self.moving = True
        self._update_facing()
        return False

    def _apply_movement(self, dt: float, collision_system, obstacles: list | None):
        """Apply velocity-based movement with collision resolution, like enemies use."""
        if not obstacles:
            obstacles = []
        if self.moving and collision_system is not None:
            collision_system.handle_movement_and_collision(self, dt, obstacles)
        elif self.pos is not None and self.velocity.length_squared() > 0:
            self.pos += self.velocity * self.speed * dt

    def _update_facing(self):
        """Update direction and flip based on velocity."""
        if self.velocity.length_squared() < 0.01:
            return
        if abs(self.velocity.x) > abs(self.velocity.y):
            self.direction = "side"
            self.flip = self.velocity.x < 0
        else:
            self.direction = "down" if self.velocity.y > 0 else "up"

    # ----------------------------------------------------------
    # BEHAVIOR STATE MACHINE
    # ----------------------------------------------------------

    def _update_behavior(self, dt: float):
        """Core behavior state machine."""
        player_dist = self._player_distance()

        # --- Shy: retreat to spawn if player too close ---
        if player_dist is not None and player_dist < self.shyness_range:
            if self.mood != "shy":
                self.mood = "shy"
                self.wander_target = None
            dist_to_spawn = (self.pos - self.spawn_pos).length()
            if dist_to_spawn > 10:
                self._move_toward(self.spawn_pos, dt)
            else:
                self.moving = False
                self.velocity = pygame.Vector2(0, 0)
            return

        # --- Curious: approach player ---
        if player_dist is not None and player_dist < self.curiosity_range and player_dist > self.shyness_range * 2:
            if self.mood != "curious":
                self.mood = "curious"
                self.met_player = True
            # Move toward player, stopping at a comfortable distance
            stop_dist = self.shyness_range * 2
            if player_dist > stop_dist:
                target_pos = pygame.Vector2(self.player_ref.pos.x, self.player_ref.pos.y)
                self._move_toward(target_pos, dt)
            else:
                self.moving = False
                self.velocity = pygame.Vector2(0, 0)
                # Face the player
                if self.player_ref:
                    diff = self.player_ref.pos - self.pos
                    if diff.length_squared() > 1:
                        self._update_facing_from_vec(diff)
            return

        # --- Wander ---
        if self.mood == "wander" and self.wander_target is not None:
            arrived = self._move_toward(self.wander_target, dt)
            if arrived:
                self.mood = "idle"
                self.wander_target = None
                self.wander_timer = self.wander_pause
            return

        # --- Idle: count down then pick a new wander target ---
        if self.mood in ("idle", "curious", "shy"):
            self.mood = "idle"
            self.moving = False
            self.velocity = pygame.Vector2(0, 0)
            self.wander_timer -= dt
            if self.wander_timer <= 0:
                self._pick_wander_target()
                self.mood = "wander"

    def _update_facing_from_vec(self, vec: pygame.Vector2):
        """Set facing from an arbitrary direction vector."""
        if abs(vec.x) > abs(vec.y):
            self.direction = "side"
            self.flip = vec.x < 0
        else:
            self.direction = "down" if vec.y > 0 else "up"

    def _player_distance(self) -> float | None:
        """Return distance to player, or None if no player reference."""
        if self.player_ref is None:
            return None
        return self.pos.distance_to(pygame.Vector2(
            self.player_ref.pos.x + self.player_ref.image.get_width() // 2,
            self.player_ref.pos.y + self.player_ref.image.get_height() // 2,
        ))

    def _nearest_enemy_distance(self, enemies: list) -> float | None:
        """Return distance to the closest enemy, or None if enemies list is empty."""
        best: float | None = None
        my_center = pygame.Vector2(
            self.pos.x + self.image.get_width() // 2,
            self.pos.y + self.image.get_height() // 2,
        )
        for e in enemies:
            if getattr(e, "is_dead", lambda: False)():
                continue
            rect = e.get_rect()
            e_center = pygame.Vector2(rect.centerx, rect.centery)
            d = my_center.distance_to(e_center)
            if best is None or d < best:
                best = d
        return best

    # ----------------------------------------------------------
    # AURA EFFECT
    # ----------------------------------------------------------

    def _apply_aura(self, dt: float):
        """Apply the passive aura effect to the nearby player."""
        if self.player_ref is None:
            return
        dist = self._player_distance()
        if dist is None or dist > self.aura_radius:
            return

        self._aura_timer += dt
        if self._aura_timer < 1.0:
            return
        self._aura_timer -= 1.0

        player = self.player_ref
        effect = self.aura_effect
        magnitude = self.aura_magnitude

        if effect == "heal":
            if hasattr(player, "hp") and hasattr(player, "max_hp"):
                if player.hp < player.max_hp:
                    player.heal(int(magnitude))
                    self._spawn_floating_text(f"+{int(magnitude)}", (200, 255, 150))

        elif effect == "mana_regen":
            if hasattr(player, "restore_mana"):
                player.restore_mana(magnitude)
                self._spawn_floating_text(f"+{magnitude:.1f} mana", (150, 180, 255))

        elif effect == "stamina_regen":
            if hasattr(player, "restore_stamina"):
                player.restore_stamina(magnitude)
                self._spawn_floating_text(f"+{magnitude:.1f} stam", (180, 220, 140))

        elif effect == "shield":
            if hasattr(player, "shield"):
                player.shield = min(player.shield + magnitude, player.max_hp * 0.5)
                self._spawn_floating_text(f"+{magnitude:.1f} shield", (160, 220, 255))

        elif effect == "speed_boost":
            if hasattr(player, "speed_multiplier"):
                current = player.speed_multiplier
                target = 1.0 + magnitude
                # Smoothly approach the boost value
                if current < target:
                    player.speed_multiplier = min(current + 0.01, target)

        elif effect == "cooldown_reduce":
            if hasattr(player, "cooldown_multiplier"):
                target = 1.0 - magnitude
                if player.cooldown_multiplier > target:
                    player.cooldown_multiplier = max(target, player.cooldown_multiplier - 0.005)

        elif effect == "damage_boost":
            if hasattr(player, "damage_bonus"):
                if player.damage_bonus < magnitude:
                    player.damage_bonus += 0.1

        elif effect == "xp_bonus":
            pass  # Applied at XP gain time via a flag check

    def _remove_aura_on_leave(self):
        """Remove ongoing aura effects when the player leaves range."""
        if self.player_ref is None:
            return
        dist = self._player_distance()
        if dist is None or dist > self.aura_radius * 1.5:
            player = self.player_ref
            if self.aura_effect == "speed_boost" and hasattr(player, "speed_multiplier"):
                if player.speed_multiplier > 1.0:
                    player.speed_multiplier = max(1.0, player.speed_multiplier - 0.02)
            elif self.aura_effect == "cooldown_reduce" and hasattr(player, "cooldown_multiplier"):
                if player.cooldown_multiplier < 1.0:
                    player.cooldown_multiplier = min(1.0, player.cooldown_multiplier + 0.01)
            elif self.aura_effect == "damage_boost" and hasattr(player, "damage_bonus"):
                if player.damage_bonus > 0:
                    player.damage_bonus = max(0, player.damage_bonus - 0.1)

    # ----------------------------------------------------------
    # PARTICLES
    # ----------------------------------------------------------

    def _spawn_ambient_particles(self, dt: float):
        """Spawn ambient particles based on mob type."""
        if random.random() > dt * 2:
            return
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(10, self.aura_radius * 0.6)
        px = self.pos.x + math.cos(angle) * dist
        py = self.pos.y + math.sin(angle) * dist
        self.particles.append({
            "x": px, "y": py,
            "vx": random.uniform(-5, 5),
            "vy": random.uniform(-15, -5),
            "life": random.uniform(1.0, 2.5),
            "max_life": 2.5,
            "color": self.aura_color,
            "size": random.uniform(1.5, 3.5),
        })

    def _update_particles(self, dt: float):
        """Update ambient particles."""
        for p in self.particles[:]:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
            if p["life"] <= 0:
                self.particles.remove(p)

    def _draw_particles(self, screen: pygame.Surface, cam: pygame.Vector2):
        """Draw ambient particles."""
        for p in self.particles:
            alpha = max(0, min(255, int(255 * (p["life"] / p["max_life"]))))
            sx = int(p["x"] - cam.x)
            sy = int(p["y"] - cam.y)
            r = max(1, int(p["size"] * (p["life"] / p["max_life"])))
            color = (*p["color"][:3], alpha)
            if len(color) == 4 and color[3] < 255:
                overlay = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(overlay, color, (r, r), r)
                screen.blit(overlay, (sx - r, sy - r), special_flags=pygame.BLEND_ALPHA_SDL2)
            else:
                pygame.draw.circle(screen, p["color"], (sx, sy), r)

    # ----------------------------------------------------------
    # FLOATING TEXT
    # ----------------------------------------------------------

    def _spawn_floating_text(self, text: str, color: tuple):
        """Queue a floating text popup."""
        self.floating_texts.append({
            "text": text,
            "x": self.pos.x + self.image.get_width() // 2,
            "y": self.pos.y - 10,
            "color": color,
            "life": 1.5,
            "max_life": 1.5,
            "vy": -30,
        })

    def _update_floating_texts(self, dt: float):
        for ft in self.floating_texts[:]:
            ft["y"] += ft["vy"] * dt
            ft["life"] -= dt
            if ft["life"] <= 0:
                self.floating_texts.remove(ft)

    def _draw_floating_texts(self, screen: pygame.Surface, cam: pygame.Vector2):
        for ft in self.floating_texts:
            alpha = max(0, min(255, int(255 * (ft["life"] / ft["max_life"]))))
            sx = int(ft["x"] - cam.x)
            sy = int(ft["y"] - cam.y)
            try:
                font = pygame.font.Font(None, 18)
                surf = font.render(ft["text"], True, ft["color"])
                surf.set_alpha(alpha)
                screen.blit(surf, (sx - surf.get_width() // 2, sy))
            except Exception:
                pass

    # ----------------------------------------------------------
    # INTERACTION
    # ----------------------------------------------------------

    def on_player_interact(self, player: Character) -> str | None:
        """
        Called when the player interacts (e.g., presses action key) near this mob.
        Returns a description string or None if no interaction.
        """
        if self.interaction_cooldown > 0:
            return None

        self.interaction_cooldown = 2.0

        # Species-specific interactions
        interactions = {
            "grove_titan": "The Grove Titan pats your leg with its branch-like arm. It smells of fresh earth.",
            "singing_stone": "The Singing Stone hums louder. You feel a deep, resonant peace.",
            "ember_phoenix": "The Ember Phoenix ruffles its burning feathers. A wave of warmth envelops you.",
            "coral_golem": "The Coral Golem hums a deep oceanic melody. You feel refreshed and energized.",
            "void_butterfly": "The Void Butterfly lands on your shoulder. You glimpse distant galaxies in its wings.",
            "moss_rabbit": "The Moss Rabbit twitches its nose. Tiny flower petals fall from its furry back.",
            "crystal_fox": "The Crystal Fox flicks its tail. Shimmering prismatic light dances across its fur.",
            "fairy_cat": "The Fairy Cat purrs and rubs against your leg. The tiny bells on its collar chime softly.",

        }

        msg = interactions.get(self.mob_type, f"The {self.name} regards you serenely.")
        self._spawn_floating_text("♡", (255, 180, 200))
        return msg

    # ----------------------------------------------------------
    # UPDATE / DRAW
    # ----------------------------------------------------------

    def update(self, dt: float, player: Character | None = None, enemies: list | None = None,
               collision_system=None, obstacles: list | None = None):
        """
        Update the peaceful mob each frame.

        Args:
            dt: Delta time in seconds.
            player: The player character (for aura and behavior).
            enemies: List of enemy entities to flee from.
            collision_system: CollisionSystem for wall-aware movement (like enemies use).
            obstacles: List of wall/polygon collision rectangles.
        """
        self.player_ref = player
        self.interaction_cooldown = max(0, self.interaction_cooldown - dt)
        self.hit_flash_timer = max(0, self.hit_flash_timer - dt)

        # Enemy flee behavior (checked first — overrides player curiosity)
        if enemies and self.mood in ("idle", "wander", "curious"):
            nearest_enemy_dist = self._nearest_enemy_distance(enemies)
            if nearest_enemy_dist is not None and nearest_enemy_dist < self.shyness_range * 1.5:
                if self.mood != "shy":
                    self.mood = "shy"
                    self.wander_target = None
                dist_to_spawn = (self.pos - self.spawn_pos).length()
                if dist_to_spawn > 10:
                    self._move_toward(self.spawn_pos, dt)
                else:
                    self.moving = False
                    self.velocity = pygame.Vector2(0, 0)
                # Apply collision-aware movement (like enemies do)
                self._apply_movement(dt, collision_system, obstacles)
                # skip player-driven behavior when fleeing from enemies
                # Play animation while fleeing
                if self.moving:
                    self.time_accumulator += dt
                    if self.time_accumulator > 1 / self.animation_speed:
                        self.time_accumulator = 0
                        self.frame_index = (self.frame_index + 1) % len(self.animations[self.direction])
                    self.image = self.animations[self.direction][self.frame_index]
                else:
                    self.time_accumulator += dt * 0.3
                    if self.time_accumulator > 1 / self.animation_speed:
                        self.time_accumulator = 0
                        self.frame_index = (self.frame_index + 1) % len(self.animations[self.direction])
                    self.image = self.animations[self.direction][self.frame_index]
                self._spawn_ambient_particles(dt)
                self._update_particles(dt)
                self._update_floating_texts(dt)
                return

        # Behavior
        self._update_behavior(dt)

        # Apply collision-aware movement after behavior sets velocity
        self._apply_movement(dt, collision_system, obstacles)

        # Aura effect
        self._apply_aura(dt)
        self._remove_aura_on_leave()

        # Animation
        if self.moving:
            self.time_accumulator += dt
            if self.time_accumulator > 1 / self.animation_speed:
                self.time_accumulator = 0
                self.frame_index = (self.frame_index + 1) % len(self.animations[self.direction])
            self.image = self.animations[self.direction][self.frame_index]
        else:
            # Gentle idle animation (slower frame advance)
            self.time_accumulator += dt * 0.3
            if self.time_accumulator > 1 / self.animation_speed:
                self.time_accumulator = 0
                self.frame_index = (self.frame_index + 1) % len(self.animations[self.direction])
            self.image = self.animations[self.direction][self.frame_index]

        # Particles
        self._spawn_ambient_particles(dt)
        self._update_particles(dt)

        # Floating texts
        self._update_floating_texts(dt)

    def draw(self, screen: pygame.Surface, camera_offset: pygame.Vector2 | None = None):
        """
        Draw the peaceful mob with a health bar (like enemies), no aura/name tag.
        """
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        img = self.image
        if self.direction == "side" and self.flip:
            img = self.animations_flipped["side"][self.frame_index]

        draw_x = int(self.pos.x - camera_offset.x)
        draw_y = int(self.pos.y - camera_offset.y)
        screen.blit(img, (draw_x, draw_y))

        # Health bar (matching enemy style)
        bar_width = 40
        bar_height = 5
        bar_x = self.pos.x - camera_offset.x + (self.image.get_width() - bar_width) // 2
        bar_y = self.pos.y - camera_offset.y - 10

        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))

        if self.max_hp > 0:
            health_width = int(bar_width * (self.hp / self.max_hp))
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, health_width, bar_height))


# ============================================================
# FACTORY FUNCTION
# ============================================================

def create_peaceful_mob(
    x: float,
    y: float,
    mob_type: str,
    custom_config: dict | None = None,
) -> PeacefulMob:
    """
    Factory function to create a PeacefulMob instance.

    Args:
        x: Spawn X position.
        y: Spawn Y position.
        mob_type: One of the keys in PEACEFUL_MOB_REGISTRY.
        custom_config: Optional overrides for the mob's config.

    Returns:
        A configured PeacefulMob instance.
    """
    return PeacefulMob(x, y, mob_type, custom_config)


def create_all_peaceful_mobs(center_x: float, center_y: float, spread: float = 400.0) -> list[PeacefulMob]:
    """
    Create one of each peaceful mob type, scattered around a center point.
    Useful for initial world population.

    Args:
        center_x: Center X for spawning.
        center_y: Center Y for spawning.
        spread: How far from center each mob can be placed.

    Returns:
        List of PeacefulMob instances.
    """
    mobs = []
    for i, mob_type in enumerate(PEACEFUL_MOB_REGISTRY):
        angle = (2 * math.pi / len(PEACEFUL_MOB_REGISTRY)) * i + random.uniform(-0.3, 0.3)
        dist = random.uniform(spread * 0.4, spread)
        x = center_x + math.cos(angle) * dist
        y = center_y + math.sin(angle) * dist
        mobs.append(create_peaceful_mob(x, y, mob_type))
    return mobs