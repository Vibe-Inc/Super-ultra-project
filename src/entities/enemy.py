import pygame


class Enemy:
    """
    Represents an enemy character that can patrol, detect, chase, and attack the player.

    Attributes:
        animations (dict): Dictionary containing lists of Pygame surfaces for each direction ("up", "down", "side").
        direction (str): Current movement direction of the enemy ("up", "down", "side").
        image (pygame.Surface): Current frame of the enemy to be drawn.
        pos (pygame.Vector2): Current position of the enemy on the screen.
        spawn_pos (pygame.Vector2): Initial spawn position used for resetting or respawning.
        speed (float): Movement speed of the enemy in pixels per second.
        hp (int): Current health points of the enemy.
        max_hp (int): Maximum health points of the enemy.
        damage (int): Damage dealt to the player when attacking.
        frame_index (int): Current frame index for animation.
        animation_speed (float): Number of frames per second for animation.
        time_accumulator (float): Accumulates time to control animation frame switching.
        flip (bool): Whether to flip the enemy horizontally (used for left/right movement).
        moving (bool): Whether the enemy is currently moving.
        target (pygame.Vector2 or None): Position the enemy is currently moving toward.
        target_entity (Character or None): Reference to the player character being tracked.
        ai_state (str): Current AI behavior state ("idle", "patrol", "chase", "attack").
        patrol_points (list): List of (x, y) tuples representing patrol waypoints.
        patrol_index (int): Index of the current patrol target.
        detection_range (float): Distance within which the enemy detects the player.
        attack_range (float): Distance within which the enemy initiates an attack.

    Methods:
        update(dt):
            Updates the enemy's AI state, movement, and animation.
            Args:
                dt (float): Time elapsed since the last frame in seconds.

        take_damage(amount):
            Reduces the enemy's health by the given amount.
            Args:
                amount (int): Damage to apply.

        is_dead():
            Returns True if the enemy's health is zero or below.

        draw(screen):
            Draws the enemy's current frame to the given Pygame surface.
            Args:
                screen (pygame.Surface): The surface to draw the enemy on.
    """

    def __init__(self, x, y, sprite_set, speed, hp, damage, animation_size, animation_speed, detection_range, attack_range, patrol_points=None):
        self.pos = pygame.Vector2(x, y)
        self.speed = speed
        self.hp = hp
        self.spawn_pos = self.pos.copy()

        self.animations = {
            "down":  [pygame.transform.scale(pygame.image.load(f"assets/characters/{sprite_set}/FrontWalk/FrontWalk{i}.png"), animation_size) for i in range(1, 5)],
            "up":    [pygame.transform.scale(pygame.image.load(f"assets/characters/{sprite_set}/BackWalk/BackWalk{i}.png"), animation_size) for i in range(1, 5)],
            "side":  [pygame.transform.scale(pygame.image.load(f"assets/characters/{sprite_set}/SideWalk/SideWalk{i}.png"), animation_size) for i in range(1, 5)],
        }

        self.direction = "down"
        self.image = self.animations[self.direction][0]
        self.flip = False
        self.frame_index = 0
        self.animation_speed = animation_speed
        self.time_accumulator = 0.0
        self.moving = False

        self.damage = damage
        self.target = None
        self.target_entity = None
        self.ai_state = "idle" # idle, patrol, chase, attack
        self.patrol_points = patrol_points or []
        self.patrol_index = 0
        self.detection_range = detection_range
        self.attack_range = attack_range

    def update(self, dt: float):
        self._update_ai()
        self._move(dt)
        self._update_animation(dt)

    def _update_ai(self):
        if self.target_entity:
            distance = (self.target_entity.pos - self.pos).length()
            if distance <= self.attack_range:
                self.target = None
                self.ai_state = "attack"
            elif distance <= self.detection_range:
                self.target = self.target_entity.pos
                self.ai_state = "chase"
            else:
                self.target = None
                self.ai_state = "idle"
        elif self.patrol_points:
            self.ai_state = "patrol"
            patrol_target = pygame.Vector2(self.patrol_points[self.patrol_index])
            if (patrol_target - self.pos).length() < 5:
                self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
            self.target = patrol_target
        else:
            self.ai_state = "idle"
            self.target = None

    def _move(self, dt: float):
        self.moving = False
        if self.target:
            direction_vector = self.target - self.pos
            if direction_vector.length() > 1:
                direction_vector = direction_vector.normalize()
                self.pos += direction_vector * self.speed * dt
                self.moving = True

                if abs(direction_vector.x) > abs(direction_vector.y):
                    self.direction = "side"
                    self.flip = direction_vector.x < 0
                else:
                    self.direction = "down" if direction_vector.y > 0 else "up"

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
        return self.hp <= 0

    def is_dead(self) -> bool:
        return self.hp <= 0

    def draw(self, screen: pygame.Surface):
        if self.direction == "side":
            screen.blit(pygame.transform.flip(self.image, self.flip, False), self.pos)
        else:
            screen.blit(self.image, self.pos)
