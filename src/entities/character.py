import pygame


class Character:
    """
    Represents the player character with animated movement in four directions.

    This class handles player movement, animation, health, and respawn logic.

    Attributes:
        animations (dict[str, list[pygame.Surface]]):
            Dictionary containing lists of Pygame surfaces for each direction ("up", "down", "side").
        direction (str):
            Current movement direction of the character ("up", "down", "side").
        image (pygame.Surface):
            Current frame of the character to be drawn.
        pos (pygame.Vector2):
            Position of the character on the screen.
        spawn_point (pygame.Vector2):
            The respawn point for the character.
        speed (float):
            Movement speed of the character in pixels per second.
        frame_index (int):
            Current frame index for animation.
        animation_speed (float):
            Number of frames per second for animation.
        time_accumulator (float):
            Accumulates time to control animation frame switching.
        flip (bool):
            Whether to flip the character horizontally (used for left/right movement).
        moving (bool):
            Whether the character is currently moving.
        hp (int):
            Current health points of the character.
        death_count (int):
            Number of times the character has died.
        death_sound (pygame.mixer.Sound):
            Sound effect played on death.

    Methods:
        update(dt):
            Update the character's position and animation based on keyboard input.
            Args:
                dt (float): Time elapsed since the last frame in seconds.
        take_damage(amount):
            Reduce the character's health by the given amount and handle death.
            Args:
                amount (int): Amount of damage to take.
        die():
            Handle character death, play sound, increment death count, reset health and position.
        draw(screen):
            Draw the character's current frame to the given Pygame surface.
            Args:
                screen (pygame.Surface): The surface to draw the character on.
        """
    def __init__(self):
        self.animations = {
            "down": 	[pygame.transform.scale(pygame.image.load(f"assets/characters/WomanHuman1(Recolor)/FrontWalk/FrontWalk{i}.png"), (85, 85)) for i in range(1, 5)],
            "up": 	[pygame.transform.scale(pygame.image.load(f"assets/characters/WomanHuman1(Recolor)/BackWalk/BackWalk{i}.png"), (85, 85)) for i in range(1, 5)],
            "side": 	[pygame.transform.scale(pygame.image.load(f"assets/characters/WomanHuman1(Recolor)/SideWalk/SideWalk{i}.png"), (85, 85)) for i in range(1, 5)],
        }

        self.direction = "down"
        self.image = self.animations[self.direction][0]
        self.pos = pygame.Vector2(960, 540)
        self.spawn_point = self.pos.copy()
        self.speed = 200  
        
        self.rect = self.image.get_rect(topleft=(self.pos.x, self.pos.y))
        self.velocity = pygame.Vector2(0, 0)
        self.hit_cooldown = 0

        self.frame_index = 0
        self.animation_speed = 10
        self.time_accumulator = 0
        self.flip = False
        self.moving = False

        self.hp = 100
        self.death_count = 0
        self.death_sound = pygame.mixer.Sound("sounds/death.mp3")

    def get_rect(self):
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))
        return self.rect
    
    def _set_velocity(self):
        keys = pygame.key.get_pressed()
        self.velocity.x = 0
        self.velocity.y = 0
        self.moving = False

        if keys[pygame.K_w]:
            self.velocity.y -= 1
        if keys[pygame.K_s]:
            self.velocity.y += 1
        if keys[pygame.K_a]:
            self.velocity.x -= 1
        if keys[pygame.K_d]:
            self.velocity.x += 1
            
        if self.velocity.length_squared() > 0:
            self.velocity = self.velocity.normalize()
            self.moving = True
            
            if abs(self.velocity.x) > abs(self.velocity.y):
                self.direction = "side"
                self.flip = self.velocity.x < 0
            else:
                self.direction = "down" if self.velocity.y > 0 else "up"

    def update(self, dt, collision_system, obstacles):
        self._set_velocity()
        
        collision_system.handle_movement_and_collision(self, dt, obstacles)

        if self.moving:
            self.time_accumulator += dt
            if self.time_accumulator > 1 / self.animation_speed:
                self.time_accumulator = 0
                self.frame_index = (self.frame_index + 1) % len(self.animations[self.direction])
            self.image = self.animations[self.direction][self.frame_index]
        else:
            self.frame_index = 0
            self.image = self.animations[self.direction][0]

        if self.hit_cooldown > 0:
            self.hit_cooldown -= dt

        if self.hp <= 0:
            self.die()

    def take_damage(self, amount):
        if self.hit_cooldown <= 0:
            self.hp -= amount
            self.hit_cooldown = 1.0
            if self.hp <= 0:
                self.die()

    def die(self):
        self.death_sound.play()
        self.death_count += 1
        self.hp = 100  
        self.pos = self.spawn_point.copy()

    def draw(self, screen):
        if self.direction == "side":
            screen.blit(pygame.transform.flip(self.image, self.flip, False), self.get_rect())
        else:
            screen.blit(self.image, self.get_rect())