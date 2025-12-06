import pygame
from src.core.logger import logger

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
        
        # New attributes for CollisionSystem
        rect (pygame.Rect): Collision and drawing rectangle (for integer coordinates).
        velocity (pygame.Vector2): Normalized vector representing the desired movement direction.

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
        get_rect():
            Returns the collision rectangle, updated to the current float position.

        update(dt, collision_system, obstacles):
            Update the character's position and animation based on keyboard input.
            Args:
                dt (float): Time elapsed since the last frame in seconds.
                collision_system (CollisionSystem): The external collision handler instance.
                obstacles (list[pygame.Rect]): List of static collision boxes (walls).
        
        _set_velocity():
            Calculates the desired movement vector (velocity) based on keyboard input.

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
            "down":  [pygame.transform.scale(pygame.image.load(f"assets/characters/WomanHuman1(Recolor)/FrontWalk/FrontWalk{i}.png"), (85, 85)) for i in range(1, 5)],
            "up":    [pygame.transform.scale(pygame.image.load(f"assets/characters/WomanHuman1(Recolor)/BackWalk/BackWalk{i}.png"), (85, 85)) for i in range(1, 5)],
            "side":  [pygame.transform.scale(pygame.image.load(f"assets/characters/WomanHuman1(Recolor)/SideWalk/SideWalk{i}.png"), (85, 85)) for i in range(1, 5)],
        }

        self.direction = "down"
        self.image = self.animations[self.direction][0]
        self.pos = pygame.Vector2(960, 540)
        self.spawn_point = self.pos.copy()
        self.speed = 200
        self.sprint_multiplier = 1.8 
        
        # New attributes for collision
        self.rect = self.image.get_rect(topleft=(self.pos.x, self.pos.y))
        self.velocity = pygame.Vector2(0, 0) # Used to store desired movement

        self.frame_index = 0
        self.animation_speed = 10
        self.time_accumulator = 0
        self.flip = False
        self.moving = False

        self.max_hp = 100
        self.hp = self.max_hp
        self.death_count = 0
        self.death_sound = pygame.mixer.Sound("sounds/death.mp3")
        
        # Invulnerability
        self.invulnerable = False
        self.invulnerability_timer = 0.0
        self.invulnerability_duration = 1.0 # seconds

        # Level system
        self.xp = 0
        self.level = 1
        self.xp_to_next_level = 100

        # Stamina system
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.stamina_drain_rate = 35  
        self.stamina_regen_rate = 25  
        self.is_sprinting = False
        self.can_sprint = True

        # Effects
        self.effects = []
        self.confused = False
        self.dizzy = False

        # Combat stats
        self.base_attack_damage = 15
        self.attack_damage = self.base_attack_damage
        self.attack_range = 65
        self.attack_cooldown = 500  # ms
        self.last_attack_time = 0
        self.is_attacking = False

    def add_effect(self, effect):
        for e in self.effects:
            if type(e) == type(effect):
                self.effects.remove(e)
                self.effects.append(effect)
                return
        self.effects.append(effect)

    def gain_xp(self, amount):
        self.xp += amount
        logger.info(f"Gained {amount} XP. Current XP: {self.xp}/{self.xp_to_next_level}")
        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level_up()

    def level_up(self):
        self.level += 1
        self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
        self.max_hp += 20
        self.hp = self.max_hp 
        logger.info(f"Level Up! Level: {self.level}, Max HP: {self.max_hp}")
        print(f"Level Up! Level: {self.level}, Max HP: {self.max_hp}")

    def attack(self, enemies):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time < self.attack_cooldown:
            return

        self.last_attack_time = current_time
        self.is_attacking = True
        logger.info("Player attacks!")

        # Simple hitbox logic based on direction
        attack_rect = self.get_rect().copy()
        if self.direction == "up":
            attack_rect.y -= self.attack_range
            attack_rect.height = self.attack_range
        elif self.direction == "down":
            attack_rect.y += self.rect.height
            attack_rect.height = self.attack_range
        elif self.direction == "side":
            if self.flip: # Left
                attack_rect.x -= self.attack_range
                attack_rect.width = self.attack_range
            else: # Right
                attack_rect.x += self.rect.width
                attack_rect.width = self.attack_range

        # Check for hits
        for enemy in enemies:
            if attack_rect.colliderect(enemy.get_rect()):
                logger.info(f"Hit enemy for {self.attack_damage} damage!")
                enemy.take_damage(self.attack_damage)
                # Knockback
                knockback_force = 20
                direction = pygame.Vector2(0, 0)
                if self.direction == "up": direction.y = -1
                elif self.direction == "down": direction.y = 1
                elif self.direction == "side": direction.x = -1 if self.flip else 1
                
                enemy.pos += direction * knockback_force

    def get_rect(self):
        """Returns the collision rectangle (hitbox), updated to the current float position."""
        # Define a smaller hitbox for the feet (e.g., 40x20 pixels)
        hitbox_width = 40
        hitbox_height = 20
        
        # Center the hitbox horizontally, place it at the bottom vertically
        offset_x = (85 - hitbox_width) // 2
        offset_y = 85 - hitbox_height
        
        self.rect = pygame.Rect(int(self.pos.x + offset_x), int(self.pos.y + offset_y), hitbox_width, hitbox_height)
        return self.rect
    
    def _set_velocity(self):
        """Calculates the desired movement vector (self.velocity) based on keyboard input."""
        keys = pygame.key.get_pressed()
        self.velocity.x = 0
        self.velocity.y = 0
        self.moving = False
        self.is_sprinting = False

        wants_to_sprint = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        if wants_to_sprint and self.stamina > 0 and self.can_sprint:
            self.is_sprinting = True

        current_speed = self.speed * self.sprint_multiplier if self.is_sprinting else self.speed
        self.speed = current_speed 

        # Movement logic with confusion support
        up_key = pygame.K_w
        down_key = pygame.K_s
        left_key = pygame.K_a
        right_key = pygame.K_d

        if self.confused:
            up_key, down_key = down_key, up_key
            left_key, right_key = right_key, left_key

        if keys[up_key]:
            self.velocity.y = -1
            self.direction = "up"
        elif keys[down_key]:
            self.velocity.y = 1
            self.direction = "down"
        
        if keys[left_key]:
            self.velocity.x = -1
            self.direction = "side"
            self.flip = True
        elif keys[right_key]:
            self.velocity.x = 1
            self.direction = "side"
            self.flip = False
            
        if self.velocity.length_squared() > 0:
            self.velocity = self.velocity.normalize()
            self.moving = True
            
            if abs(self.velocity.x) > abs(self.velocity.y):
                self.direction = "side"
                self.flip = self.velocity.x < 0
            else:
                self.direction = "down" if self.velocity.y > 0 else "up"

    def update(self, dt, collision_system, obstacles):
        """
        Updates the character's state, sets desired movement, and applies movement
        using the external collision system.
        """
        # Reset attacking flag after short duration
        if self.is_attacking and pygame.time.get_ticks() - self.last_attack_time > 200:
            self.is_attacking = False

        # Update invulnerability
        if self.invulnerable:
            self.invulnerability_timer -= dt
            if self.invulnerability_timer <= 0:
                self.invulnerable = False

        # Update effects
        for effect in self.effects[:]:
            effect.update(dt, self)
            if effect.is_finished:
                self.effects.remove(effect)

        self._set_velocity()
        
        # Stamina management (logic from your update method)
        if self.moving and self.is_sprinting:
            self.stamina -= self.stamina_drain_rate * dt
            if self.stamina <= 0:
                self.stamina = 0
                self.can_sprint = False  
        elif not self.moving:
            self.stamina += self.stamina_regen_rate * dt
            if self.stamina >= self.max_stamina:
                self.stamina = self.max_stamina
                self.can_sprint = True  

        # KEY IMPLEMENTATION STEP: Single function call for collision-aware movement
        collision_system.handle_movement_and_collision(self, dt, obstacles)
        
        # Reset speed to base speed for next frame logic (if needed elsewhere)
        # Though _set_velocity will overwrite it again next frame.
        self.speed = 200 

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
        if self.invulnerable:
            return
            
        self.hp -= amount
        self.invulnerable = True
        self.invulnerability_timer = self.invulnerability_duration
        
        logger.info(f"Player took {amount} damage. HP: {self.hp}/{self.max_hp}")
        if self.hp <= 0:
            self.die()

    def die(self):
        logger.warning("Player died!")
        self.death_sound.play()
        self.death_count += 1
        self.hp = self.max_hp  # reset health
        self.pos = self.spawn_point.copy()  # teleport to spawn
        logger.info(f"Player respawned at {self.pos}. Death count: {self.death_count}")

    def draw(self, screen):
        # Blink if invulnerable
        if self.invulnerable and int(pygame.time.get_ticks() / 100) % 2 == 0:
            pass # Skip drawing for blinking effect
        else:
            # Draw relative to self.pos (top-left of sprite), NOT self.get_rect() (hitbox)
            draw_pos = (int(self.pos.x), int(self.pos.y))
            if self.direction == "side":
                screen.blit(pygame.transform.flip(self.image, self.flip, False), draw_pos)
            else:
                screen.blit(self.image, draw_pos)
        
        # Draw attack visual
        if self.is_attacking:
            attack_rect = self.get_rect().copy()
            
            # Create a surface for the slash
            slash_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
            
            # Draw a nice arc/slash
            color = (255, 255, 255, 200)
            width = 5
            
            if self.direction == "up":
                # Arc above
                rect = pygame.Rect(10, 50, 80, 80)
                pygame.draw.arc(slash_surface, color, rect, 0.1, 3.0, width)
                screen.blit(slash_surface, (self.pos.x - 10, self.pos.y - 60))
                
            elif self.direction == "down":
                # Arc below
                rect = pygame.Rect(10, -30, 80, 80)
                pygame.draw.arc(slash_surface, color, rect, 3.2, 6.2, width)
                screen.blit(slash_surface, (self.pos.x - 10, self.pos.y + 60))
                
            elif self.direction == "side":
                if self.flip: # Left
                    rect = pygame.Rect(30, 10, 80, 80)
                    pygame.draw.arc(slash_surface, color, rect, 1.6, 4.6, width)
                    screen.blit(slash_surface, (self.pos.x - 60, self.pos.y))
                else: # Right
                    rect = pygame.Rect(-10, 10, 80, 80)
                    pygame.draw.arc(slash_surface, color, rect, 4.8, 1.4 + 6.28, width) # Wrap around angle
                    screen.blit(slash_surface, (self.pos.x + 40, self.pos.y))