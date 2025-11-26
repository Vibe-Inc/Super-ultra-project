import pygame


class Character:
    """
        class entity needed might do it later

        Represents the player character with animated movement in four directions.
    
        Attributes:
            animations (dict): Dictionary containing lists of Pygame surfaces for each direction ("up", "down", "side").
            direction (str): Current movement direction of the character ("up", "down", "side").
            image (pygame.Surface): Current frame of the character to be drawn.
            pos (pygame.Vector2): Position of the character on the screen.
            speed (float): Movement speed of the character in pixels per second.

            frame_index (int): Current frame index for animation.
            animation_speed (float): Number of frames per second for animation.
            time_accumulator (float): Accumulates time to control animation frame switching.
            flip (bool): Whether to flip the character horizontally (used for left/right movement).
            moving (bool): Whether the character is currently moving.

        Methods:
            update(dt):
                Updates the characters position and animation based on keyboard input.
                Args:
                    dt (float): Time elapsed since the last frame in seconds.
            draw(screen):
                Draws the characters current frame to the given Pygame surface.
                Args:
                    screen (pygame.Surface): The surface to draw the character on.
        """
    def __init__(self):
        self.animations = {
            "down":  [pygame.transform.scale(pygame.image.load(f"assets/characters/WomanHuman1(Recolor)/FrontWalk/FrontWalk{i}.png"), (85, 85)) for i in range(1, 5)],
            "up":    [pygame.transform.scale(pygame.image.load(f"assets/characters/WomanHuman1(Recolor)/BackWalk/BackWalk{i}.png"), (85, 85)) for i in range(1, 5)],
            "side":  [pygame.transform.scale(pygame.image.load(f"assets/characters/WomanHuman1(Recolor)/SideWalk/SideWalk{i}.png"), (85, 85)) for i in range(1, 5)],
        }

        self.direction = "down"
        self.image = self.animations[self.direction][0]
        self.pos = pygame.Vector2(960, 540)
        self.spawn_point = self.pos.copy()
        self.speed = 200  

        self.frame_index = 0
        self.animation_speed = 10
        self.time_accumulator = 0
        self.flip = False
        self.moving = False

        self.hp = 100
        self.death_count = 0
        self.death_sound = pygame.mixer.Sound("sounds/death.mp3")

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.moving = False 

        if keys[pygame.K_w]:
            self.pos.y -= self.speed * dt
            self.direction = "up"
            self.moving = True
        elif keys[pygame.K_s]:
            self.pos.y += self.speed * dt
            self.direction = "down"
            self.moving = True
        elif keys[pygame.K_a]:
            self.pos.x -= self.speed * dt
            self.direction = "side"
            self.flip = True
            self.moving = True
        elif keys[pygame.K_d]:
            self.pos.x += self.speed * dt
            self.direction = "side"
            self.flip = False
            self.moving = True
        
        #if keys[pygame.K_SPACE]:  # press SPACE to take 100 damage (temporary cuz button can be held down insted of pressed once)
        #    self.take_damage(100) 

        if self.moving:
            self.time_accumulator += dt
            if self.time_accumulator > 1 / self.animation_speed:
                self.time_accumulator = 0
                self.frame_index = (self.frame_index + 1) % len(self.animations[self.direction])
            self.image = self.animations[self.direction][self.frame_index]
        else:
            self.frame_index = 0
            self.image = self.animations[self.direction][0]

        if self.hp <= 0:
            self.die()

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.die()

    def die(self):
        self.death_sound.play()
        self.death_count += 1
        self.hp = 100  # reset health
        self.pos = self.spawn_point.copy()  # teleport to spawn

    def draw(self, screen):
        if self.direction == "side":
            screen.blit(pygame.transform.flip(self.image, self.flip, False), self.pos)
        else:
            screen.blit(self.image, self.pos)