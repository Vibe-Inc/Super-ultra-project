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


ATTACK_PHASE_IDLE = 0
ATTACK_PHASE_WIND_UP = 1
ATTACK_PHASE_TELEGRAPH = 2
ATTACK_PHASE_STRIKE = 3


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
        self.speed = self.base_speed
        self.hp = hp
        self.max_hp = hp
        self.spawn_pos = self.pos.copy()

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

        # Attack animation state (procedural close-range strike VFX)
        self.attack_anim_type: str = ""
        self.attack_anim_elapsed: float = 0.0
        self.attack_anim_duration: float = 0.0
        self.attack_anim_dir: pygame.Vector2 = pygame.Vector2(1, 0)
        self.attack_anim_origin: pygame.Vector2 = pygame.Vector2(0, 0)
        self.attack_anim_strength: float = 1.0
        # Delayed hit for non-3-phase attacks – stores damage to apply after wind-up phase
        self.attack_anim_hit_pending: dict | None = None

        # Three-phase attack system
        self.attack_phase: int = ATTACK_PHASE_IDLE
        self.attack_phase_timer: float = 0.0
        self.wind_up_duration: float = 0.25
        self.telegraph_duration: float = 0.30
        self.attack_telegraph_range: float = 0.0
        self.attack_telegraph_angle: float = 130.0
        self.attack_telegraph_color: tuple = (255, 100, 100, 80)
        self.attack_damage_pending: int = 0
        self.attack_knockback_pending: float = 0.0
        self.attack_effect_pending = None

        # Stun state
        self.stun_timer: float = 0.0
        # Strike consumption flag — prevents applying damage multiple times in STRIKE phase
        self.attack_strike_consumed: bool = False

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

    def trigger_attack_anim(
        self,
        anim_type: str,
        duration: float,
        direction: pygame.Vector2 | None = None,
        origin: pygame.Vector2 | None = None,
        strength: float = 1.0,
    ):
        """
        Start a close-range attack animation overlay.

        Args:
            anim_type: Visual style key (e.g. 'brute_slam', 'stalker_slash').
            duration: Total length of the animation in seconds.
            direction: Facing direction of the strike; defaults to current facing.
            origin: World position the effect is anchored to; defaults to enemy center.
            strength: Multiplier for visual intensity (size, particle count, alpha).
        """
        self.attack_anim_type = anim_type or ""
        self.attack_anim_duration = max(0.05, float(duration))
        self.attack_anim_elapsed = 0.0
        self.attack_anim_strength = max(0.1, float(strength))
        if direction is None or direction.length_squared() == 0:
            direction = self._facing_vector()
        self.attack_anim_dir = pygame.Vector2(direction).normalize()
        if origin is None:
            rect = self.get_rect()
            origin = pygame.Vector2(rect.centerx, rect.centery)
        self.attack_anim_origin = pygame.Vector2(origin)

    def _facing_vector(self) -> pygame.Vector2:
        if self.direction == "up":
            return pygame.Vector2(0, -1)
        if self.direction == "down":
            return pygame.Vector2(0, 1)
        if self.direction == "side":
            return pygame.Vector2(-1, 0) if self.flip else pygame.Vector2(1, 0)
        return pygame.Vector2(1, 0)

    def _tick_attack_anim(self, dt: float):
        if not self.attack_anim_type:
            return
        self.attack_anim_elapsed += dt
        anim_done = False
        if self.attack_anim_elapsed >= self.attack_anim_duration:
            self.attack_anim_type = ""
            self.attack_anim_elapsed = 0.0
            self.attack_anim_duration = 0.0
            anim_done = True

        # Consume delayed hit after wind-up phase (progress > 0.55)
        if self.attack_anim_hit_pending is not None:
            duration = max(0.0001, self.attack_anim_duration or 0.0001)
            progress = self.attack_anim_elapsed / duration
            if progress > 0.55 or anim_done:
                hit = self.attack_anim_hit_pending
                self.attack_anim_hit_pending = None
                player = getattr(self, 'target_entity', None)
                if player is not None:
                    dmg = hit.get('damage', 0)
                    if dmg > 0:
                        player.take_damage(dmg)
                    kb = hit.get('knockback', 0.0)
                    if kb > 0:
                        player.pos += self.attack_anim_dir * kb
                    for effect in hit.get('effects', []):
                        player.add_effect(effect)
                    heal = hit.get('heal', 0)
                    if heal > 0 and hasattr(self, 'hp') and hasattr(self, 'max_hp'):
                        self.hp = min(self.max_hp, self.hp + heal)

    def _tick_attack_phase(self, dt: float):
        if self.attack_phase == ATTACK_PHASE_IDLE:
            return
        self.attack_phase_timer -= dt

        # Continuously update telegraph direction toward player during active phases
        if self.attack_phase in (ATTACK_PHASE_WIND_UP, ATTACK_PHASE_TELEGRAPH):
            player = getattr(self, 'target_entity', None)
            if player is not None and hasattr(player, 'get_rect'):
                try:
                    p_pos = pygame.Vector2(player.get_rect().center)
                    e_pos = pygame.Vector2(self.get_rect().center)
                    direction = p_pos - e_pos
                    if direction.length_squared() > 0:
                        self.attack_anim_dir = direction.normalize()
                except Exception:
                    pass

        if self.attack_phase_timer <= 0:
            if self.attack_phase == ATTACK_PHASE_WIND_UP:
                self.attack_phase = ATTACK_PHASE_TELEGRAPH
                self.attack_phase_timer = self.telegraph_duration
                self.attack_strike_consumed = False
            elif self.attack_phase == ATTACK_PHASE_TELEGRAPH:
                self.attack_phase = ATTACK_PHASE_STRIKE
                self.attack_phase_timer = 0.05
                self.attack_strike_consumed = False
            elif self.attack_phase == ATTACK_PHASE_STRIKE:
                self.attack_phase = ATTACK_PHASE_IDLE
                self.attack_phase_timer = 0.0
                self.attack_strike_consumed = False

    def start_attack_phase(self, wind_up: float = 0.25, telegraph: float = 0.30,
                           telegraph_range: float = 0.0, telegraph_angle: float = 130.0,
                           telegraph_color: tuple = (255, 100, 100, 80),
                           damage: int = 0, knockback: float = 0.0, effect=None):
        # Clear any lingering strike animation so it doesn't overlap new wind-up
        self.attack_anim_type = ""
        self.attack_anim_elapsed = 0.0
        self.attack_anim_duration = 0.0
        self.attack_phase = ATTACK_PHASE_WIND_UP
        self.attack_phase_timer = wind_up
        self.wind_up_duration = wind_up
        self.telegraph_duration = telegraph
        self.attack_telegraph_range = telegraph_range
        self.attack_telegraph_angle = telegraph_angle
        self.attack_telegraph_color = telegraph_color
        self.attack_damage_pending = damage
        self.attack_knockback_pending = knockback
        self.attack_effect_pending = effect

    def is_attack_telegraphing(self) -> bool:
        return self.attack_phase == ATTACK_PHASE_TELEGRAPH

    def is_attack_wind_up(self) -> bool:
        return self.attack_phase == ATTACK_PHASE_WIND_UP

    def is_attack_striking(self) -> bool:
        return self.attack_phase == ATTACK_PHASE_STRIKE

    def consume_strike(self) -> bool:
        if self.attack_phase == ATTACK_PHASE_STRIKE and not self.attack_strike_consumed:
            self.attack_strike_consumed = True
            return True
        return False

    def is_in_attack(self) -> bool:
        return self.attack_phase != ATTACK_PHASE_IDLE

    def stun(self, duration: float = 1.0):
        self.stun_timer = max(self.stun_timer, duration)
        self.attack_phase = ATTACK_PHASE_IDLE
        self.attack_phase_timer = 0.0

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

        # Advance any active close-range attack animation overlay.
        self._tick_attack_anim(dt)
        # Advance three-phase attack system
        self._tick_attack_phase(dt)

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

        # Skip AI and attacks while frozen (speed_multiplier == 0) or during attack wind-up/telegraph
        in_attack_anim = self.is_in_attack()
        move_blocked = self.speed_multiplier <= 0 or (in_attack_anim and self.attack_phase != ATTACK_PHASE_STRIKE)

        if not move_blocked:
            self._ai_context.dt = dt
            self._ai_context.nav_grid = nav_grid
            self._ai_context.obstacles = obstacles
            self._ai_context.player = self.target_entity

            if self.brain:
                self.brain.update(self, self._ai_context)

            if self.attack_controller and attack_context:
                self.attack_controller.update(self, attack_context)

            self.speed = self.base_speed * self.speed_multiplier
            self._move(dt)
        else:
            # Still allow brain/attack updates even when movement is blocked by attack phase
            if self.attack_controller and attack_context and self.attack_phase == ATTACK_PHASE_IDLE:
                self.attack_controller.update(self, attack_context)
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
        # hit flash overlay removed

        # Procedural close-range attack animation overlay
        if self.attack_anim_type:
            draw_attack_animation(screen, self, camera_offset)

        # Telegraph visualization during WIND_UP and TELEGRAPH phases
        if self.attack_phase in (ATTACK_PHASE_WIND_UP, ATTACK_PHASE_TELEGRAPH) and self.attack_telegraph_range > 0:
            center = self.get_rect().center
            sx = int(center[0] - camera_offset.x)
            sy = int(center[1] - camera_offset.y)
            direction = self._facing_vector()
            if self.attack_anim_dir.length_squared() > 0:
                direction = self.attack_anim_dir
            fwd_angle = math.degrees(math.atan2(direction.y, direction.x))
            half_angle = self.attack_telegraph_angle * 0.5
            is_telegraph = self.attack_phase == ATTACK_PHASE_TELEGRAPH
            alpha_mult = 0.5 if self.attack_phase == ATTACK_PHASE_WIND_UP else 1.0
            col = self.attack_telegraph_color
            base_a = int(col[3] * alpha_mult) if len(col) > 3 else 80
            r = self.attack_telegraph_range
            surf_size = int(r * 2 + 30)
            surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            # Outer glow layer (wider, dimmer)
            glw = max(3, int(r * 0.16))
            outer_col = (col[0], col[1], col[2], base_a // 3)
            pygame.draw.arc(surf, outer_col,
                            pygame.Rect(5, 5, surf_size - 10, surf_size - 10),
                            math.radians(fwd_angle - half_angle - 2),
                            math.radians(fwd_angle + half_angle + 2),
                            glw)
            # Main telegraph arc
            main_col = (min(255, col[0] + 30), min(255, col[1] + 30), min(255, col[2] + 30), base_a)
            pygame.draw.arc(surf, main_col,
                            pygame.Rect(10, 10, surf_size - 20, surf_size - 20),
                            math.radians(fwd_angle - half_angle),
                            math.radians(fwd_angle + half_angle),
                            max(2, int(r * 0.08)))
            # Inner bright core arc (thinner, brighter)
            inner_col = (min(255, col[0] + 80), min(255, col[1] + 80), min(255, col[2] + 80), base_a)
            pygame.draw.arc(surf, inner_col,
                            pygame.Rect(12, 12, surf_size - 24, surf_size - 24),
                            math.radians(fwd_angle - half_angle + 1),
                            math.radians(fwd_angle + half_angle - 1),
                            max(1, int(r * 0.04)))
            # Pulsing dots along the arc edge during telegraph
            if is_telegraph:
                pulse = abs(math.sin(pygame.time.get_ticks() * 0.006))
                for i in range(6):
                    t = i / 6.0
                    ang = math.radians(fwd_angle - half_angle + t * half_angle * 2)
                    dx = int(math.cos(ang) * (r + 4))
                    dy = int(math.sin(ang) * (r + 4))
                    da = int(200 * pulse * (0.5 + 0.5 * math.sin(t * math.pi)))
                    dot_col = (min(255, col[0] + 100), min(255, col[1] + 100), min(255, col[2] + 100), da)
                    pygame.draw.circle(surf, dot_col, (surf_size // 2 + dx, surf_size // 2 + dy), 3)
            screen.blit(surf, (sx - surf_size // 2, sy - surf_size // 2),
                        special_flags=pygame.BLEND_ALPHA_SDL2)

        self.draw_hp_bar(screen, camera_offset)

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

    def draw_hp_bar(self, screen: pygame.Surface, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)
        bar_width = 40
        bar_height = 5
        bar_x = self.pos.x - camera_offset.x + (85 - bar_width) // 2
        bar_y = self.pos.y - camera_offset.y - 10

        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))

        if self.max_hp > 0:
            health_width = int(bar_width * (self.hp / self.max_hp))
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, health_width, bar_height))
