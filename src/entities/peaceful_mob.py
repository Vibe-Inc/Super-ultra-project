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
    "starwhale": {
        "name": "Starwhale",
        "description": "A celestial whale drifting through the cosmos, trailing stardust.",
        "hp": 9999,
        "speed": 30,
        "animation_size": (96, 80),
        "animation_speed": 4,
        "aura_color": (180, 200, 255),
        "aura_radius": 120.0,
        "aura_effect": "mana_regen",       # passive mana regeneration
        "aura_magnitude": 2.0,             # mana per second
        "curiosity_range": 300.0,
        "shyness_range": 80.0,
        "wander_radius": 200.0,
        "wander_pause": 3.0,               # seconds between wander moves
        "idle_behavior": "hover",           # slow up-down bobbing
        "xp_reward": 0,
    },
    "luminous_deer": {
        "name": "Luminous Deer",
        "description": "A forest deer whose antlers glow with crystallized light.",
        "hp": 9999,
        "speed": 55,
        "animation_size": (80, 90),
        "animation_speed": 6,
        "aura_color": (200, 255, 160),
        "aura_radius": 100.0,
        "aura_effect": "heal",             # passive HP regeneration
        "aura_magnitude": 1.5,
        "curiosity_range": 200.0,
        "shyness_range": 120.0,
        "wander_radius": 300.0,
        "wander_pause": 2.5,
        "idle_behavior": "graze",          # occasional head dip
        "xp_reward": 0,
    },
    "crystal_serpent": {
        "name": "Crystal Serpent",
        "description": "A gentle serpentine creature of living crystal that refracts light.",
        "hp": 9999,
        "speed": 40,
        "animation_size": (80, 96),
        "animation_speed": 5,
        "aura_color": (160, 220, 255),
        "aura_radius": 90.0,
        "aura_effect": "shield",           # temporary damage shield
        "aura_magnitude": 0.3,             # shield per second
        "curiosity_range": 250.0,
        "shyness_range": 100.0,
        "wander_radius": 180.0,
        "wander_pause": 4.0,
        "idle_behavior": "coil",           # gentle coiling motion
        "xp_reward": 0,
    },
    "aurora_moth": {
        "name": "Aurora Moth",
        "description": "An ethereal moth whose wings shimmer with aurora borealis colors.",
        "hp": 9999,
        "speed": 35,
        "animation_size": (96, 80),
        "animation_speed": 5,
        "aura_color": (120, 220, 180),
        "aura_radius": 130.0,
        "aura_effect": "speed_boost",      # movement speed bonus
        "aura_magnitude": 0.1,             # 10% speed boost
        "curiosity_range": 250.0,
        "shyness_range": 150.0,
        "wander_radius": 250.0,
        "wander_pause": 3.5,
        "idle_behavior": "flutter",        # figure-8 flight pattern
        "xp_reward": 0,
    },
    "grove_titan": {
        "name": "Grove Titan",
        "description": "A small, gentle tree creature that waddles and hums.",
        "hp": 9999,
        "speed": 25,
        "animation_size": (80, 90),
        "animation_speed": 3,
        "aura_color": (140, 200, 100),
        "aura_radius": 110.0,
        "aura_effect": "stamina_regen",    # passive stamina regeneration
        "aura_magnitude": 3.0,
        "curiosity_range": 180.0,
        "shyness_range": 60.0,
        "wander_radius": 150.0,
        "wander_pause": 5.0,
        "idle_behavior": "sway",           # gentle side-to-side sway
        "xp_reward": 0,
    },
    "moon_jelly": {
        "name": "Moon Jellyfish",
        "description": "An ethereal jellyfish that glows with soft moonlight.",
        "hp": 9999,
        "speed": 20,
        "animation_size": (80, 90),
        "animation_speed": 3,
        "aura_color": (180, 200, 255),
        "aura_radius": 140.0,
        "aura_effect": "cooldown_reduce",  # skill cooldown reduction
        "aura_magnitude": 0.05,            # 5% cooldown reduction
        "curiosity_range": 300.0,
        "shyness_range": 90.0,
        "wander_radius": 120.0,
        "wander_pause": 4.5,
        "idle_behavior": "float",          # slow drift up and down
        "xp_reward": 0,
    },
    "prism_fox": {
        "name": "Prism Fox",
        "description": "An elegant fox whose fur refracts light into rainbows.",
        "hp": 9999,
        "speed": 65,
        "animation_size": (80, 80),
        "animation_speed": 8,
        "aura_color": (220, 180, 255),
        "aura_radius": 95.0,
        "aura_effect": "damage_boost",     # flat damage bonus
        "aura_magnitude": 3,
        "curiosity_range": 220.0,
        "shyness_range": 100.0,
        "wander_radius": 280.0,
        "wander_pause": 2.0,
        "idle_behavior": "prowl",          # quick dart-and-pause
        "xp_reward": 0,
    },
    "singing_stone": {
        "name": "Singing Stone",
        "description": "A gentle living rock that hums melodically, with glowing runes.",
        "hp": 9999,
        "speed": 15,
        "animation_size": (72, 80),
        "animation_speed": 2,
        "aura_color": (200, 220, 160),
        "aura_radius": 100.0,
        "aura_effect": "xp_bonus",         # XP gain bonus
        "aura_magnitude": 0.15,            # 15% XP bonus
        "curiosity_range": 150.0,
        "shyness_range": 40.0,
        "wander_radius": 80.0,
        "wander_pause": 6.0,
        "idle_behavior": "hum",            # stays mostly still, pulsing
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

        # Health (effectively immortal)
        self.hp = config["hp"]
        self.max_hp = config["hp"]

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
        self.pos += self.velocity * self.speed * dt
        self._update_facing()
        return False

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
            "starwhale": "The Starwhale hums a cosmic melody. You feel your mind expand...",
            "luminous_deer": "The Luminous Deer nuzzles your hand. Its antlers glow brighter.",
            "crystal_serpent": "The Crystal Serpent coils around your arm gently, leaving tiny sparkles.",
            "aurora_moth": "The Aurora Moth brushes its wing against you. Colors dance before your eyes.",
            "grove_titan": "The Grove Titan pats your leg with its branch-like arm. It smells of fresh earth.",
            "moon_jelly": "The Moon Jellyfish pulses gently. A calming warmth washes over you.",
            "prism_fox": "The Prism Fox circles you playfully, leaving a trail of rainbow light.",
            "singing_stone": "The Singing Stone hums louder. You feel a deep, resonant peace.",
        }

        msg = interactions.get(self.mob_type, f"The {self.name} regards you serenely.")
        self._spawn_floating_text("♡", (255, 180, 200))
        return msg

    # ----------------------------------------------------------
    # UPDATE / DRAW
    # ----------------------------------------------------------

    def update(self, dt: float, player: Character | None = None, enemies: list | None = None):
        """
        Update the peaceful mob each frame.

        Args:
            dt: Delta time in seconds.
            player: The player character (for aura and behavior).
            enemies: List of enemy entities to flee from.
        """
        self.player_ref = player
        self.interaction_cooldown = max(0, self.interaction_cooldown - dt)

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
        Draw the peaceful mob, its aura, particles, and floating texts.
        """
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        # --- Aura glow ---
        dist_to_player = self._player_distance()
        if dist_to_player is not None and dist_to_player < self.aura_radius * 1.5:
            aura_surf = pygame.Surface(
                (int(self.aura_radius * 2), int(self.aura_radius * 2)), pygame.SRCALPHA
            )
            # Pulsing aura
            pulse = 1.0 + 0.1 * math.sin(pygame.time.get_ticks() * 0.003)
            r = int(self.aura_radius * pulse)
            color_a = (*self.aura_color[:3], 25)
            pygame.draw.circle(aura_surf, color_a, (r, r), r)
            color_b = (*self.aura_color[:3], 15)
            pygame.draw.circle(aura_surf, color_b, (r, r), r + 10, 3)
            ax = int(self.pos.x - r + self.image.get_width() // 2 - camera_offset.x)
            ay = int(self.pos.y - r + self.image.get_height() // 2 - camera_offset.y)
            screen.blit(aura_surf, (ax, ay), special_flags=pygame.BLEND_ALPHA_SDL2)

        # --- Ground shadow ---
        shadow_surf = pygame.Surface((40, 12), pygame.SRCALPHA)
        shadow_cx = 20
        shadow_color = (0, 0, 0, 40)
        pygame.draw.ellipse(shadow_surf, shadow_color, (0, 0, 40, 12))
        sx = int(self.pos.x + self.image.get_width() // 2 - 20 - camera_offset.x)
        sy = int(self.pos.y + self.image.get_height() - 10 - camera_offset.y)
        screen.blit(shadow_surf, (sx, sy))

        # --- Sprite ---
        img = self.image
        if self.direction == "side" and self.flip:
            img = self.animations_flipped["side"][self.frame_index]
        draw_x = int(self.pos.x - camera_offset.x)
        draw_y = int(self.pos.y - camera_offset.y)
        screen.blit(img, (draw_x, draw_y))

        # --- Name tag (when close) ---
        if dist_to_player is not None and dist_to_player < 200:
            name_surf = pygame.font.Font(None, 20).render(self.name, True, (220, 220, 200))
            name_surf.set_alpha(200)
            nx = draw_x + (self.image.get_width() - name_surf.get_width()) // 2
            ny = draw_y - 16
            screen.blit(name_surf, (nx, ny))

        # --- Particles ---
        self._draw_particles(screen, camera_offset)

        # --- Floating texts ---
        self._draw_floating_texts(screen, camera_offset)


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