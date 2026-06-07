import math
from typing import TYPE_CHECKING

import pygame

from src.ai.monster_ai import AIContext, build_brain
from src.core.logger import logger
from src.entities.monster_attack_visuals import draw_attack_animation

if TYPE_CHECKING:
    from src.entities.character import Character

_ANIMATION_CACHE: dict[tuple[str, tuple[int, int]], dict[str, list[pygame.Surface]]] = {}
_FLIPPED_CACHE: dict[tuple[str, tuple[int, int]], dict[str, list[pygame.Surface]]] = {}


def _load_sprite_animations(
    sprite_set: str,
    animation_size: tuple[int, int],
) -> tuple[dict[str, list[pygame.Surface]], dict[str, list[pygame.Surface]]]:
    key = (sprite_set, tuple(animation_size))
    cached = _ANIMATION_CACHE.get(key)
    if cached is not None:
        return cached, _FLIPPED_CACHE[key]

    def _load_series(folder: str, prefix: str) -> list[pygame.Surface]:
        frames: list[pygame.Surface] = []
        for i in range(1, 5):
            path = f"assets/characters/{sprite_set}/{folder}/{prefix}{i}.png"
            image = pygame.image.load(path).convert_alpha()
            if image.get_size() != animation_size:
                image = pygame.transform.scale(image, animation_size)
            frames.append(image)
        return frames

    animations = {
        "down": _load_series("FrontWalk", "FrontWalk"),
        "up": _load_series("BackWalk", "BackWalk"),
        "side": _load_series("SideWalk", "SideWalk"),
    }
    flipped = {"side": [pygame.transform.flip(frame, True, False) for frame in animations["side"]]}

    _ANIMATION_CACHE[key] = animations
    _FLIPPED_CACHE[key] = flipped
    return animations, flipped


class Enemy:
    """
    Represents an enemy character that can patrol, detect, chase, and attack the player.

    This class handles enemy movement, AI state transitions, health, and combat logic.

    Attributes:
        pos (pygame.Vector2):
            Current position of the enemy on the screen.
        speed (float):
            Movement speed of the enemy in pixels per second.
        base_speed (float):
            Base movement speed before modifiers.
        speed_multiplier (float):
            Multiplier applied to base speed.

        # New attributes for CollisionSystem
        rect (pygame.Rect): Collision and drawing rectangle.
        velocity (pygame.Vector2): Normalized vector representing desired movement direction.

        hp (int):
            Current health points of the enemy.
        spawn_pos (pygame.Vector2):
            Initial spawn position used for resetting or respawning.
        animations (dict[str, list[pygame.Surface]]):
            Dictionary containing lists of Pygame surfaces for each direction ("up", "down", "side").
        direction (str):
            Current movement direction of the enemy ("up", "down", "side").
        image (pygame.Surface):
            Current frame of the enemy to be drawn.
        flip (bool):
            Whether to flip the enemy horizontally (used for left/right movement).
        frame_index (int):
            Current frame index for animation.
        animation_speed (float):
            Number of frames per second for animation.
        time_accumulator (float):
            Accumulates time to control animation frame switching.
        moving (bool):
            Whether the enemy is currently moving.
        damage (int):
            Damage dealt to the player when attacking.
        target (pygame.Vector2 | None):
            Position the enemy is currently moving toward.
        target_entity (Character | None):
            Reference to the player character being tracked.
        ai_profile (str):
            Name of the AI profile used by this enemy.
        brain (BaseBrain | None):
            AI brain instance that drives behavior and pathing.
        attack_controller (BaseAttack | None):
            Attack controller for special monster mechanics.
        contact_damage (bool):
            Whether touching the player should deal damage.
        ai_state (str):
            Current AI behavior state ("idle", "patrol", "chase", "attack").
        patrol_points (list[tuple[float, float]]):
            List of (x, y) tuples representing patrol waypoints.
        patrol_index (int):
            Index of the current patrol target.
        detection_range (float):
            Distance within which the enemy detects the player.
        attack_range (float):
            Distance within which the enemy initiates an attack.
        effects (list):
            Active status effects (burn, poison, etc.) on this enemy.
        max_hp (int):
            Maximum HP used for the HP bar.

    Methods:
        get_rect():
            Returns the collision rectangle, updated to the current float position.
        update(dt, collision_system, obstacles, nav_grid=None, attack_context=None):
            Update the enemy's AI state, set velocity, and apply movement via collision system.
        add_effect(effect):
            Attach a status effect (matches the player's API so weapons can apply burn, etc.).
        _tick_effects(dt):
            Update all active effects and remove finished ones.
        take_damage(amount):
            Reduce the enemy's health by the given amount.
        is_dead():
            Returns True if the enemy's health is zero or below.
        draw(screen):
            Draw the enemy's current frame to the given Pygame surface.
    """

    def __init__(
        self,
        x,
        y,
        sprite_set,
        speed,
        hp,
        damage,
        animation_size,
        animation_speed,
        detection_range,
        attack_range,
        patrol_points=None,
        ai_profile: str = "stalker",
        ai_config: dict | None = None,
        animations: dict[str, list[pygame.Surface]] | None = None,
        attack_controller=None,
        contact_damage: bool = True,
        visual_style: str | None = None,
    ):
        self.pos = pygame.Vector2(x, y)
        self.base_speed = speed
        self.speed_multiplier = 1.0
        self.speed_multiplier_world = 1.0
        self.speed = self.base_speed
        self.hp = hp
        self.max_hp = hp
        self.base_max_hp = hp
        self.base_damage = damage
        self.base_detection_range = detection_range
        self.base_attack_range = attack_range
        self.spawn_pos = self.pos.copy()
        self.is_boss = False

        if animations is not None:
            self.animations = animations
            self.animations_flipped = {
                "side": [pygame.transform.flip(frame, True, False) for frame in self.animations["side"]]
            }
        else:
            self.animations, self.animations_flipped = _load_sprite_animations(sprite_set, animation_size)

        self.direction = "down"
        self.image = self.animations[self.direction][0]

        self.rect = self.image.get_rect(topleft=(x, y))
        self.velocity = pygame.Vector2(0, 0)
        self.hitbox_width = 46
        self.hitbox_height = 34

        self.flip = False
        self.frame_index = 0
        self.animation_speed = animation_speed
        self.time_accumulator = 0.0
        self.moving = False

        self.damage = damage
        self.target = None
        self.hit_flash_timer = 0.0
        self.target_entity: Character | None = None
        self.ai_profile = ai_profile
        self.visual_style = (visual_style or ai_profile or "stalker").lower()
        self.ai_state = "idle"  # idle, patrol, chase, attack
        self.brain = build_brain(ai_profile, ai_config)
        self.attack_controller = attack_controller
        self.contact_damage = contact_damage
        self.patrol_points = patrol_points or []
        self.patrol_index = 0
        self.detection_range = detection_range
        self.attack_range = attack_range
        self._ai_context = AIContext(dt=0.0, nav_grid=None, obstacles=[], player=None)

        # Attack phase state (3-phase: windup → telegraph → strike)
        self._attack_phase: str = "idle"
        self._attack_phase_timer: float = 0.0
        self._windup_duration: float = 0.25
        self._telegraph_duration: float = 0.30
        self._strike_duration: float = 0.15
        self._phase_strike_ready: bool = False
        self._phase_damage: int = 0
        self._phase_knockback: float = 0.0
        self._phase_effect = None

        # Attack animation state (procedural close-range strike VFX)
        self.attack_anim_type: str = ""
        self.attack_anim_elapsed: float = 0.0
        self.attack_anim_duration: float = 0.35
        self.attack_anim_origin: pygame.Vector2 = pygame.Vector2(0, 0)
        self.attack_anim_dir: pygame.Vector2 = pygame.Vector2(1, 0)
        self.attack_anim_strength: float = 1.0
        self.attack_windup_range: float = attack_range
        self.attack_windup_angle: float = 130.0
        self.attack_windup_coverage: str = "arc"
        # Stun state
        self.stun_timer: float = 0.0
        # Instant strike consumption guard (kept for attack controllers that use the old pattern)
        self._strike_ready: bool = False

        self.effects = []
        # Status effect container (matches the player's API so weapons
        # can apply burn / poison / etc. by calling enemy.add_effect()).
        self.effects: list = []
        self.cooldown_multiplier = 1.0
        self.damage_bonus = 0
        self.shield = 0.0
        self.dizzy = False
        self.confused = False

        self._flash_overlay = pygame.Surface(animation_size, pygame.SRCALPHA)
        self._flash_overlay.fill((255, 50, 50, 100))
        self._animation_size = animation_size
        self._lod_distance = 800.0
        logger.info(f"Spawned enemy {getattr(self, 'ai_profile', 'unknown')} at ({x}, {y})")

    def add_effect(self, effect):
        """Attach a status effect to this enemy. Same contract as Character."""
        for e in self.effects:
            if type(e) == type(effect):
                self.effects.remove(e)
                self.effects.append(effect)
                return
        self.effects.append(effect)

    def _tick_effects(self, dt: float):
        if not self.effects:
            return
        for effect in self.effects[:]:
            effect.update(dt, self)
            if effect.is_finished:
                self.effects.remove(effect)

    def get_rect(self):
        sprite_width = self.image.get_width()
        sprite_height = self.image.get_height()

        self.rect = pygame.Rect(int(self.pos.x), int(self.pos.y), sprite_width, sprite_height)
        return self.rect

    def add_effect(self, effect):
        for e in self.effects:
            if type(e) == type(effect):
                self.effects.remove(e)
                self.effects.append(effect)
                return
        self.effects.append(effect)

    def start_attack_phase(self, wind_up: float = 0.25, telegraph: float = 0.30,
                           strike_duration: float = 0.15,
                           telegraph_range: float = 0.0, telegraph_angle: float = 130.0,
                           telegraph_color: tuple = (255, 100, 100, 80),
                           damage: int = 0, knockback: float = 0.0, effect=None):
        self._strike_ready = False
        self._attack_phase = "windup"
        self._attack_phase_timer = 0.0
        self._windup_duration = max(0.01, wind_up)
        self._telegraph_duration = max(0.01, telegraph)
        self._strike_duration = max(0.01, strike_duration)
        self._phase_strike_ready = False
        self._phase_damage = damage
        self._phase_knockback = knockback
        self._phase_effect = effect
        self.attack_windup_range = telegraph_range or self.attack_range
        self.attack_windup_angle = telegraph_angle

    def consume_strike(self) -> bool:
        if self._strike_ready:
            self._strike_ready = False
            self._attack_phase = "idle"
            return True
        return False

    def trigger_attack_anim(self, anim_type: str, duration: float, *,
                            direction=None, origin=None, strength=1.0):
        self.attack_anim_type = anim_type
        self.attack_anim_duration = max(0.05, duration)
        self.attack_anim_elapsed = 0.0
        if origin is not None:
            self.attack_anim_origin = pygame.Vector2(origin)
        else:
            self.attack_anim_origin = self.pos + pygame.Vector2(
                self.image.get_width() / 2, self.image.get_height() * 0.55)
        if direction is not None:
            self.attack_anim_dir = pygame.Vector2(direction).normalize()
        else:
            self.attack_anim_dir = pygame.Vector2(1, 0)
        self.attack_anim_strength = strength
        arc_types = {"brute_slam", "venomous_strike", "stalker_slash",
                     "skirmisher_claw", "guardian_smash", "revenant_slash",
                     "molten_slam", "bomber_strike", "phantom_drain", "generic_strike"}
        self.attack_windup_coverage = "arc" if anim_type in arc_types else "circle"
        if self.attack_windup_range <= 1:
            self.attack_windup_range = self.attack_range

    def is_in_attack(self) -> bool:
        return self._attack_phase != "idle"

    def stun(self, duration: float = 1.0):
        self.stun_timer = max(self.stun_timer, duration)

    def update(self, dt: float, collision_system, obstacles, nav_grid=None, attack_context=None, active: bool = True):
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= dt

        # Update effects
        for effect in self.effects[:]:
            effect.update(dt, self)
            if effect.is_finished:
                self.effects.remove(effect)
        # Tick status effects first so debuffs can modify speed_multiplier
        # before the movement code below consumes it.
        self._tick_effects(dt)

        # Tick attack animation elapsed
        if self.attack_anim_elapsed < self.attack_anim_duration:
            self.attack_anim_elapsed += dt

        # Tick attack phase progression
        if self._attack_phase != "idle":
            self._attack_phase_timer += dt
            if self._attack_phase == "windup" and self._attack_phase_timer >= self._windup_duration:
                self._attack_phase = "telegraph"
            if self._attack_phase == "telegraph" and self._attack_phase_timer >= self._windup_duration + self._telegraph_duration:
                self._attack_phase = "strike"
                self._phase_strike_ready = True
                self._strike_ready = True

        # Handle stun
        if self.stun_timer > 0:
            self.stun_timer -= dt
            self.speed_multiplier = 0.0
            self.velocity = pygame.Vector2(0, 0)
            self.moving = False
            self.speed = 0.0
            collision_system.handle_movement_and_collision(self, dt, obstacles)
            self._update_animation(dt)
            if self.stun_timer <= 0:
                self.speed_multiplier = 1.0
            return

        if not active:
            self.time_accumulator += dt * 0.2
            if self.time_accumulator > 1 / self.animation_speed:
                self.time_accumulator = 0
                self.frame_index = (self.frame_index + 1) % len(self.animations[self.direction])
            self.image = self.animations[self.direction][self.frame_index]
            return

        # Movement blocked only when frozen (speed_multiplier <= 0) or stunned
        if self.speed_multiplier > 0:
            self._ai_context.dt = dt
            self._ai_context.nav_grid = nav_grid
            self._ai_context.obstacles = obstacles
            self._ai_context.player = self.target_entity

            if self.brain:
                self.brain.update(self, self._ai_context)

            if self.attack_controller and attack_context:
                self.attack_controller.update(self, attack_context)

            self.speed = self.base_speed * self.speed_multiplier * self.speed_multiplier_world
            self._move(dt)
        else:
            self.speed = 0.0
            self.velocity = pygame.Vector2(0, 0)
            self.moving = False

        collision_system.handle_movement_and_collision(self, dt, obstacles)

        self._update_animation(dt)

    def _move(self, dt: float):
        self.velocity = pygame.Vector2(0, 0)
        self.moving = False

        if self.target:
            direction_vector = self.target - self.pos

            if direction_vector.length_squared() > 1.0:

                self.velocity = direction_vector.normalize()
                self.moving = True

                if abs(self.velocity.x) > abs(self.velocity.y):
                    self.direction = "side"
                    self.flip = self.velocity.x < 0
                else:
                    self.direction = "down" if self.velocity.y > 0 else "up"
            else:
                self.target = None

    def _update_animation(self, dt: float):
        if self.moving:
            self.time_accumulator += dt
            if self.time_accumulator > 1 / self.animation_speed:
                self.time_accumulator = 0
                self.frame_index = (self.frame_index + 1) % len(self.animations[self.direction])
            self.image = self.animations[self.direction][self.frame_index]
        else:
            self.frame_index = 0
            self.image = self.animations[self.direction][0]

    def apply_world_scale(self, scale_mult: dict):
        if self.is_boss:
            return
        old_max = self.max_hp
        self.max_hp = max(1, int(self.base_max_hp * scale_mult.get('hp', 1.0)))
        self.hp = max(1, int(self.hp * (self.max_hp / old_max))) if old_max > 0 else self.max_hp
        self.damage = max(1, int(self.base_damage * scale_mult.get('damage', 1.0)))
        self.speed_multiplier_world = scale_mult.get('speed', 1.0)
        self.speed = max(1, int(self.base_speed * self.speed_multiplier_world))
        self.detection_range = max(1, int(self.base_detection_range * scale_mult.get('range', 1.0)))
        self.attack_range = max(1, int(self.base_attack_range * scale_mult.get('range', 1.0)))

    def take_damage(self, amount: int, ignore_invulnerability=False) -> bool:
        prev = self.hp
        self.hp = max(0, self.hp - amount)
        logger.debug(f"Enemy {getattr(self, 'ai_profile', 'unknown')} took {amount} damage: {prev} -> {self.hp}")
        if self.hp <= 0:
            logger.info(f"Enemy {getattr(self, 'ai_profile', 'unknown')} died")
        # disabled hit flash overlay on damage
        return self.hp <= 0

    def is_dead(self) -> bool:
        return self.hp <= 0

    def draw(self, screen: pygame.Surface, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        img = self.image
        if self.direction == "side" and self.flip:
            img = self.animations_flipped["side"][self.frame_index]
        draw_pos = (int(self.pos.x - camera_offset.x), int(self.pos.y - camera_offset.y))
        screen.blit(img, draw_pos)

        bar_width = 40
        bar_height = 5
        bar_x = self.pos.x - camera_offset.x + (85 - bar_width) // 2
        bar_y = self.pos.y - camera_offset.y - 10

        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))

        if self.max_hp > 0:
            health_width = int(bar_width * (self.hp / self.max_hp))
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, health_width, bar_height))

        # Stun visual effect (spinning stars above enemy)
        if self.stun_timer > 0:
            sx = int(self.pos.x - camera_offset.x + self.image.get_width() // 2)
            sy = int(self.pos.y - camera_offset.y - 14)
            now = pygame.time.get_ticks()
            for i in range(4):
                angle = now * 0.004 + i * math.pi * 0.5
                star_r = 4 + int(3 * abs(math.sin(now * 0.005 + i)))
                sx2 = sx + int(math.cos(angle) * 9)
                sy2 = sy + int(math.sin(angle) * 6)
                star_alpha = int(180 + 75 * math.sin(now * 0.008 + i * 2.1))
                surf = pygame.Surface((star_r * 2 + 2, star_r * 2 + 2), pygame.SRCALPHA)
                pts = []
                for j in range(5):
                    a = math.pi * 2 * j / 5 - math.pi * 0.5
                    pts.append((star_r + int(math.cos(a) * star_r), star_r + int(math.sin(a) * star_r)))
                pygame.draw.polygon(surf, (255, 255, 100, star_alpha), pts)
                screen.blit(surf, (sx2 - star_r, sy2 - star_r),
                            special_flags=pygame.BLEND_ALPHA_SDL2)

        now_ms = pygame.time.get_ticks()
        enemy_cx = int(self.pos.x - camera_offset.x + self.image.get_width() // 2)
        enemy_cy = int(self.pos.y - camera_offset.y + self.image.get_height() * 0.5)

        # ── Wind-up danger zone during attack phase (before strike lands) ──
        if self._attack_phase in ("windup", "telegraph"):
            total_windup = self._windup_duration + self._telegraph_duration
            phase_prog = min(1.0, self._attack_phase_timer / total_windup) if total_windup > 0 else 1.0
            pulse = 0.6 + 0.4 * math.sin(now_ms * 0.006 + phase_prog * 8)
            fade = int(50 + 90 * phase_prog * pulse)
            w_rng = self.attack_windup_range * 1.4
            if self.attack_windup_coverage == "circle":
                for layer in range(2):
                    lr = int(w_rng * (0.9 + layer * 0.1))
                    pygame.draw.circle(
                        screen, (255, 100, 80, fade // (layer + 1)),
                        (enemy_cx, enemy_cy), max(2, lr), max(1, 3 - layer))
            else:
                # Direction: toward target_entity if available
                if self.target_entity:
                    tdir = pygame.Vector2(self.target_entity.pos) - self.pos
                    if tdir.length_squared() > 0:
                        tdir = tdir.normalize()
                else:
                    tdir = pygame.Vector2(1, 0)
                base_angle = -math.degrees(math.atan2(tdir.y, tdir.x))
                sweep = self.attack_windup_angle * 0.85
                for layer in range(2):
                    sr = int(w_rng * (0.8 + layer * 0.1))
                    sz = max(32, int(sr * 2 + 20))
                    surf2 = pygame.Surface((sz, sz), pygame.SRCALPHA)
                    a = fade // (layer + 1)
                    pygame.draw.arc(
                        surf2, (255, 100, 80, a),
                        pygame.Rect(sz // 2 - sr, sz // 2 - sr, sr * 2, sr * 2),
                        math.radians(270 - sweep * 0.5),
                        math.radians(270 + sweep * 0.5), max(1, 4 - layer))
                    rotated = pygame.transform.rotate(surf2, base_angle - 270)
                    screen.blit(rotated, rotated.get_rect(center=(enemy_cx, enemy_cy)))

        # ── Strike visual animation (triggers after consume_strike) ──
        if self.attack_anim_type and self.attack_anim_elapsed < self.attack_anim_duration:
            progress = self.attack_anim_elapsed / self.attack_anim_duration
            origin = self.attack_anim_origin
            direction = self.attack_anim_dir
            cx = int(origin.x - camera_offset.x)
            cy = int(origin.y - camera_offset.y)

            # ── Wind-up phase (0.0 to 0.25): afterimage danger zone ──
            if progress < 0.25:
                wp = progress / 0.25
                fade = int(100 * (1.0 - wp) * wp * 4)
                w_rng2 = self.attack_windup_range * 1.4
                if self.attack_windup_coverage == "circle":
                    for layer in range(2):
                        lr = int(w_rng2 * (1.0 + layer * 0.15) * self.attack_anim_strength)
                        pygame.draw.circle(
                            screen, (255, 80, 60, fade // (layer + 1)),
                            (cx, cy), max(2, lr), max(1, 3 - layer))
                else:
                    base_angle = -math.degrees(math.atan2(direction.y, direction.x))
                    sweep = self.attack_windup_angle * 0.85
                    for layer in range(2):
                        sr = int(w_rng2 * (0.8 + layer * 0.1) * self.attack_anim_strength)
                        sz = max(32, int(sr * 2 + 20))
                        surf3 = pygame.Surface((sz, sz), pygame.SRCALPHA)
                        a = fade // (layer + 1)
                        pygame.draw.arc(
                            surf3, (255, 100, 80, a),
                            pygame.Rect(sz // 2 - sr, sz // 2 - sr, sr * 2, sr * 2),
                            math.radians(270 - sweep * 0.5),
                            math.radians(270 + sweep * 0.5), max(1, 4 - layer))
                        rotated = pygame.transform.rotate(surf3, base_angle - 270)
                        screen.blit(rotated, rotated.get_rect(center=(cx, cy)))

            # ── Strike phase: dispatch to per-enemy unique visual ──
            draw_attack_animation(screen, self, camera_offset)
