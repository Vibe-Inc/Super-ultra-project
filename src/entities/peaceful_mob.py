"""
Peaceful majestic mobs that roam the world, adding ambient life and wonder.

These creatures are non-aggressive and feature unique behaviors:
  - Wandering / idling with gentle animations
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

CAT_SOUNDS = ["nyaa", "purrr", "meow", "mrrrow", "prrr", "mew", "nya~"]

PEACEFUL_MOB_REGISTRY: dict[str, dict] = {
    "grove_titan": {
        "name": "Grove Titan",
        "description": "A small, gentle tree creature that waddles and hums.",
        "hp": 80,
        "speed": 25,
        "animation_size": (80, 90),
        "animation_speed": 3,
        "curiosity_range": 180.0,
        "shyness_range": 60.0,
        "wander_radius": 150.0,
        "wander_pause": 5.0,
        "idle_behavior": "sway",
        "drop_chance": [{"item_id": "stick", "chance": 0.5}],
    },
    "singing_stone": {
        "name": "Singing Stone",
        "description": "A gentle living rock that hums melodically, with glowing runes.",
        "hp": 60,
        "speed": 15,
        "animation_size": (72, 80),
        "animation_speed": 2,
        "curiosity_range": 150.0,
        "shyness_range": 40.0,
        "wander_radius": 80.0,
        "wander_pause": 6.0,
        "idle_behavior": "hum",
        "drop_chance": [{"item_id": "stone", "chance": 0.5}],
    },
    "ember_phoenix": {
        "name": "Ember Phoenix",
        "description": "A radiant bird of gentle flame that radiates warmth and healing light.",
        "hp": 50,
        "speed": 50,
        "animation_size": (84, 90),
        "animation_speed": 6,
        "curiosity_range": 250.0,
        "shyness_range": 90.0,
        "wander_radius": 220.0,
        "wander_pause": 3.0,
        "idle_behavior": "hover",
        "drop_chance": [{"item_id": "potion_of_shield", "chance": 0.3}],
    },
    "coral_golem": {
        "name": "Coral Golem",
        "description": "A living coral formation that pulses with deep ocean energy.",
        "hp": 70,
        "speed": 18,
        "animation_size": (76, 80),
        "animation_speed": 2,
        "curiosity_range": 160.0,
        "shyness_range": 50.0,
        "wander_radius": 90.0,
        "wander_pause": 5.5,
        "idle_behavior": "hum",
    },
    "void_butterfly": {
        "name": "Void Butterfly",
        "description": "A massive butterfly whose wings reveal glimpses of the distant cosmos.",
        "hp": 40,
        "speed": 30,
        "animation_size": (92, 84),
        "animation_speed": 4,
        "curiosity_range": 280.0,
        "shyness_range": 120.0,
        "wander_radius": 200.0,
        "wander_pause": 4.0,
        "idle_behavior": "flutter",
        "drop_chance": [{"item_id": "coal", "chance": 0.5}],
    },
    "moss_rabbit": {
        "name": "Moss Rabbit",
        "description": "A fluffy rabbit with moss and tiny flowers growing on its back.",
        "hp": 30,
        "speed": 65,
        "animation_size": (72, 68),
        "animation_speed": 8,
        "curiosity_range": 260.0,
        "shyness_range": 110.0,
        "wander_radius": 300.0,
        "wander_pause": 2.0,
        "idle_behavior": "flutter",
        "drop_chance": [{"item_id": "moldy_bread", "chance": 0.5}],
    },
    "crystal_fox": {
        "name": "Crystal Fox",
        "description": "A sleek fox whose fur shimmers like cut gemstones in the sunlight.",
        "hp": 45,
        "speed": 55,
        "animation_size": (80, 78),
        "animation_speed": 6,
        "curiosity_range": 240.0,
        "shyness_range": 90.0,
        "wander_radius": 260.0,
        "wander_pause": 2.8,
        "idle_behavior": "prowl",
    },
    "fairy_cat": {
        "name": "Fairy Cat",
        "description": "A graceful feline with iridescent wings and eyes like tiny moons.",
        "hp": 35,
        "speed": 58,
        "animation_size": (78, 80),
        "animation_speed": 7,
        "curiosity_range": 250.0,
        "shyness_range": 95.0,
        "wander_radius": 270.0,
        "wander_pause": 2.2,
        "idle_behavior": "prowl",
    },
    "tavern_cat": {
        "name": "Tavern Cat",
        "description": "A plump orange tabby cat that prowls the tavern in search of handouts and warm hearths.",
        "hp": 25,
        "speed": 52,
        "animation_size": (70, 66),
        "animation_speed": 7,
        "curiosity_range": 180.0,
        "shyness_range": 50.0,
        "wander_radius": 320.0,
        "wander_pause": 1.6,
        "idle_behavior": "prowl",
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

    Attributes:
        mob_type (str): Registry key identifying this mob's species.
        name (str): Display name.
        pos (pygame.Vector2): World position.
        spawn_pos (pygame.Vector2): Original spawn position.
        speed (float): Movement speed in px/s.
        hp (int): Current HP.
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
        curiosity_range (float): Distance at which mob notices player.
        shyness_range (float): Distance at which mob retreats.
        wander_radius (float): Max distance from spawn to wander.
        wander_pause (float): Seconds to idle between wander moves.
        wander_target (pygame.Vector2 | None): Current wander destination.
        wander_timer (float): Timer for wander pauses.
        idle_behavior (str): Species-specific idle animation key.
        mood (str): Current behavioral mood: "idle", "wander", "curious", "shy".
        player_ref (Character | None): Reference to nearby player.
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

        # Floating texts
        self.floating_texts: list[dict] = []

        # Bubble speech
        self.bubble_text: str | None = None
        self.bubble_timer: float = 0.0
        self.bubble_display_timer: float = 0.0
        self.bubble_interval: float = random.uniform(4.0, 8.0)
        self.bubble_duration: float = 2.5

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
    # HEART SURFACE
    # ----------------------------------------------------------

    @staticmethod
    def _create_heart_surface(size: int, color: tuple) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = size // 2
        cy = size // 2
        r = max(size // 5, 2)
        lobe_off = r // 2
        pygame.draw.circle(surf, color, (cx - lobe_off, cy - r // 3), r)
        pygame.draw.circle(surf, color, (cx + lobe_off, cy - r // 3), r)
        pts = [
            (cx - r, cy - r // 3),
            (cx + r, cy - r // 3),
            (cx, cy + r),
        ]
        pygame.draw.polygon(surf, color, pts)
        return surf

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

    def _spawn_floating_heart(self, size: int, color: tuple):
        self.floating_texts.append({
            "type": "heart",
            "size": size,
            "heart_surf": self._create_heart_surface(size, color),
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
            if ft.get("type") == "heart":
                heart = ft["heart_surf"].copy()
                heart.set_alpha(alpha)
                screen.blit(heart, (sx - ft["size"] // 2, sy))
            else:
                try:
                    font = pygame.font.Font(None, 18)
                    surf = font.render(ft["text"], True, ft["color"])
                    surf.set_alpha(alpha)
                    screen.blit(surf, (sx - surf.get_width() // 2, sy))
                except Exception:
                    pass

    # ----------------------------------------------------------
    # SPEECH BUBBLE (tavern cat only)
    # ----------------------------------------------------------

    def _update_bubble(self, dt: float):
        if self.mob_type != "tavern_cat":
            self.bubble_text = None
            return

        self.bubble_timer += dt
        self.bubble_display_timer = max(0, self.bubble_display_timer - dt)

        if self.bubble_display_timer > 0:
            return
        if self.bubble_text is not None:
            self.bubble_text = None
            self.bubble_timer = 0.0
            self.bubble_interval = random.uniform(4.0, 8.0)
            return

        if self.bubble_timer >= self.bubble_interval:
            self.bubble_text = random.choice(CAT_SOUNDS)
            self.bubble_display_timer = self.bubble_duration
            self.bubble_timer = 0.0

    def _draw_bubble(self, screen: pygame.Surface, cam: pygame.Vector2):
        if not self.bubble_text:
            return
        font = pygame.font.Font(None, 20)
        text_surf = font.render(self.bubble_text, True, (30, 30, 30))
        padding = 8
        bubble_w = text_surf.get_width() + padding * 2
        bubble_h = text_surf.get_height() + padding * 2

        sx = int(self.pos.x - cam.x) + self.image.get_width() // 2 - bubble_w // 2
        sy = int(self.pos.y - cam.y) - bubble_h - 12

        bubble_rect = pygame.Rect(sx, sy, bubble_w, bubble_h)
        # Tail triangle pointing down
        tail_points = [
            (sx + bubble_w // 2 - 5, sy + bubble_h),
            (sx + bubble_w // 2 + 5, sy + bubble_h),
            (sx + bubble_w // 2, sy + bubble_h + 8),
        ]

        pygame.draw.rect(screen, (255, 255, 255), bubble_rect, border_radius=6)
        pygame.draw.rect(screen, (60, 60, 60), bubble_rect, 2, border_radius=6)
        pygame.draw.polygon(screen, (255, 255, 255), tail_points)
        pygame.draw.polygon(screen, (60, 60, 60), tail_points, 2)
        screen.blit(text_surf, (sx + padding, sy + padding))

    # ----------------------------------------------------------
    # PET
    # ----------------------------------------------------------

    def pet(self):
        """Pet this mob — spawns a heart floating text."""
        self.interaction_cooldown = 2.0
        self._spawn_floating_heart(22, (255, 60, 100))
        self._spawn_floating_heart(16, (255, 130, 160))

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
            "tavern_cat": "The Tavern Cat purrs loudly and weaves between your ankles. You can hear it meowing for scraps.",

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
            player: The player character (for behavior).
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
                self._update_floating_texts(dt)
                return

        # Behavior
        self._update_behavior(dt)

        # Apply collision-aware movement after behavior sets velocity
        self._apply_movement(dt, collision_system, obstacles)

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

        # Speech bubble
        self._update_bubble(dt)

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

        # Speech bubble
        self._draw_bubble(screen, camera_offset)

        # Floating texts (hearts, etc.)
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