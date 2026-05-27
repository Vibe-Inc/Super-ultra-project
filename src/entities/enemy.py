import pygame

from src.ai.monster_ai import AIContext, build_brain


class Enemy:
    """
    Represents an enemy character that can patrol, detect, chase, and attack the player.

    This class handles enemy movement, animation, AI state transitions, health, and combat logic.

    Attributes:
        pos (pygame.Vector2):
            Current position of the enemy on the screen.
        speed (float):
            Movement speed of the enemy in pixels per second.
        
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

    Methods:
        get_rect():
            Returns the collision rectangle, updated to the current float position.
        update(dt, collision_system, obstacles, nav_grid=None):
            Update the enemy's AI state, set velocity, and apply movement via collision system.
            Args:
                dt (float): Time elapsed since the last frame in seconds.
                collision_system (CollisionSystem): The external collision handler.
                obstacles (list[pygame.Rect]): List of static walls.
                nav_grid (NavGrid | None): Optional navigation grid for pathfinding.
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
    ):
        self.pos = pygame.Vector2(x, y)
        self.speed = speed
        self.hp = hp
        self.max_hp = hp
        self.spawn_pos = self.pos.copy()

        self.animations = {
            "down":  [pygame.transform.scale(pygame.image.load(f"assets/characters/{sprite_set}/FrontWalk/FrontWalk{i}.png"), animation_size) for i in range(1, 5)],
            "up":    [pygame.transform.scale(pygame.image.load(f"assets/characters/{sprite_set}/BackWalk/BackWalk{i}.png"), animation_size) for i in range(1, 5)],
            "side":  [pygame.transform.scale(pygame.image.load(f"assets/characters/{sprite_set}/SideWalk/SideWalk{i}.png"), animation_size) for i in range(1, 5)],
        }

        self.direction = "down"
        self.image = self.animations[self.direction][0]
        
        # New attributes for collision
        self.rect = self.image.get_rect(topleft=(x, y))
        self.velocity = pygame.Vector2(0, 0)

        self.flip = False
        self.frame_index = 0
        self.animation_speed = animation_speed
        self.time_accumulator = 0.0
        self.moving = False

        self.damage = damage
        self.target = None
        self.hit_flash_timer = 0.0
        self.target_entity = None
        self.ai_profile = ai_profile
        self.ai_state = "idle"  # idle, patrol, chase, attack
        self.brain = build_brain(ai_profile, ai_config)
        self.patrol_points = patrol_points or []
        self.patrol_index = 0
        self.detection_range = detection_range
        self.attack_range = attack_range

    def get_rect(self):
        # Define a smaller hitbox for the feet
        hitbox_width = 40
        hitbox_height = 20
        
        # Assuming animation_size is (85, 85) or similar
        sprite_width = self.image.get_width()
        sprite_height = self.image.get_height()
        
        offset_x = (sprite_width - hitbox_width) // 2
        offset_y = sprite_height - hitbox_height
        
        self.rect = pygame.Rect(int(self.pos.x + offset_x), int(self.pos.y + offset_y), hitbox_width, hitbox_height)
        return self.rect

    def update(self, dt: float, collision_system, obstacles, nav_grid=None):
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= dt

        context = AIContext(dt=dt, nav_grid=nav_grid, obstacles=obstacles, player=self.target_entity)
        if self.brain:
            self.brain.update(self, context)

        self._move(dt)  # Sets self.velocity instead of moving directly
        
        # Collision system
        collision_system.handle_movement_and_collision(self, dt, obstacles)
        
        self._update_animation(dt)

    def _move(self, dt: float):
        self.velocity = pygame.Vector2(0, 0)
        self.moving = False

        if self.target:
            direction_vector = self.target - self.pos
            
            if direction_vector.length() > 1:
                # Calculate normalized direction
                self.velocity = direction_vector.normalize()
                self.moving = True

                # Determine animation direction
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

    def take_damage(self, amount: int) -> bool:
        self.hp = max(0, self.hp - amount)
        self.hit_flash_timer = 0.2
        return self.hp <= 0

    def is_dead(self) -> bool:
        return self.hp <= 0

    def draw(self, screen: pygame.Surface):
        img = self.image
        if self.hit_flash_timer > 0:
            img = img.copy()
            img.fill((255, 50, 50), special_flags=pygame.BLEND_ADD)
            
        draw_pos = (int(self.pos.x), int(self.pos.y))
        if self.direction == "side":
            screen.blit(pygame.transform.flip(img, self.flip, False), draw_pos)
        else:
            screen.blit(img, draw_pos)

        # Draw Health Bar
        bar_width = 40
        bar_height = 5
        # Center above sprite (assuming 85px width)
        bar_x = self.pos.x + (85 - bar_width) // 2
        bar_y = self.pos.y - 10
        
        # Background (Red)
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        # Health (Green)
        if self.max_hp > 0:
            health_width = int(bar_width * (self.hp / self.max_hp))
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, health_width, bar_height))