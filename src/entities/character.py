import math
import pygame
from src.core.logger import logger
from src.entities.projectile import Fireball

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
        self.sprite_set = "WomanHuman1(Recolor)"
        self.animations = {
            "down":  [pygame.transform.scale(pygame.image.load(f"assets/characters/{self.sprite_set}/FrontWalk/FrontWalk{i}.png").convert_alpha(), (85, 85)) for i in range(1, 5)],
            "up":    [pygame.transform.scale(pygame.image.load(f"assets/characters/{self.sprite_set}/BackWalk/BackWalk{i}.png").convert_alpha(), (85, 85)) for i in range(1, 5)],
            "side":  [pygame.transform.scale(pygame.image.load(f"assets/characters/{self.sprite_set}/SideWalk/SideWalk{i}.png").convert_alpha(), (85, 85)) for i in range(1, 5)],
        }
        self.animations_flipped = {
            "side": [pygame.transform.flip(frame, True, False) for frame in self.animations["side"]]
        }

        self.direction = "down"
        self.image = self.animations[self.direction][0]
        self.pos = pygame.Vector2(960, 540)
        self.spawn_point = self.pos.copy()
        self.base_speed = 200
        self.speed_multiplier = 1.0
        self.speed = self.base_speed
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

        # Skill tree
        self.skill_tree_points = 0
        self.skill_tree_unlocked = {"core"}

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
        self.base_attack_range = 65
        self.base_attack_cooldown = 500  # ms
        self.attack_damage = self.base_attack_damage
        self.attack_range = self.base_attack_range
        self.attack_cooldown = self.base_attack_cooldown
        self.last_attack_time = 0
        self.is_attacking = False
        self.last_attack_dir = pygame.Vector2(1, 0)
        self.melee_origin_offset = 6.0
        self.melee_slash_distance = 50.0
        self.skillbook = self._build_skillbook()
        self.skillbar = [None for _ in range(6)]
        self.fireball_speed = 420.0
        self.fireball_range = 520.0
        self.fireball_damage = 28
        self.fireball_blast_radius = 110.0
        self.fireball_fuse_time = 0.9
        self.fireball_cooldown = 1300
        self.fireball_knockback = 18.0
        self.game_state = None
        self.dash_speed_multiplier = 3.0
        self.dash_duration = 0.14
        self.dash_cooldown = 900
        self.dash_active_time = 0.0
        self.dash_last_used = -self.dash_cooldown
        self.dash_direction = pygame.Vector2(1, 0)

    def _build_skillbook(self):
        return [
            {
                "skill_id": "dash",
                "name": "Dash",
                "description": "Quick burst of movement",
                "color": (86, 132, 186),
                "accent": (220, 235, 255),
            },
        ]

    def learn_fireball(self):
        """Add the fireball skill to the skillbook if not already present."""
        for skill in self.skillbook:
            if skill.get("skill_id") == "fireball":
                return  # already learned
        self.skillbook.append({
            "skill_id": "fireball",
            "name": "Fireball",
            "description": "Випускає вибуховий вогняний шар, що завдає 28 пошкоджень, має радіус вибуху 110 і відкидає ворогів.",
            "color": (188, 82, 35),
            "accent": (255, 214, 120),
        })
        logger.info("Player learned Fireball!")

    def get_skill_in_slot(self, slot_index):
        if 0 <= slot_index < len(self.skillbar):
            return self.skillbar[slot_index]
        return None

    def use_skill_from_slot(self, slot_index, aim_direction=None):
        skill = self.get_skill_in_slot(slot_index)
        if skill is None:
            return False
        return self.use_skill(skill, aim_direction=aim_direction)

    def use_skill(self, skill, aim_direction=None):
        if skill is None:
            return False

        skill_id = skill.get("skill_id", "")
        current_time = pygame.time.get_ticks()

        if skill_id == "dash":
            if current_time - self.dash_last_used < self.dash_cooldown:
                return False

            direction = pygame.Vector2(self.velocity)
            if direction.length_squared() == 0:
                direction = self.get_forward_direction()
            if direction.length_squared() == 0:
                direction = pygame.Vector2(1, 0)

            self.dash_direction = direction.normalize()
            self.dash_active_time = self.dash_duration
            self.dash_last_used = current_time
            logger.info("Player used Dash.")
            return True

        if skill_id == "fireball":
            if current_time - getattr(self, "fireball_last_used", -self.fireball_cooldown) < self.fireball_cooldown:
                return False

            # Use aim_direction (cursor direction) if provided, otherwise fall back to velocity/facing
            if aim_direction is not None:
                direction = pygame.Vector2(aim_direction)
            else:
                direction = pygame.Vector2(self.velocity)
            
            if direction.length_squared() == 0:
                direction = self.get_forward_direction()
            if direction.length_squared() == 0:
                direction = pygame.Vector2(1, 0)
            else:
                direction = direction.normalize()

            game_state = getattr(self, "game_state", None)
            if game_state is None:
                logger.warning("Fireball skill used without an attached game state.")
                return False

            spawn_pos = self.get_melee_anchor() + direction * 18
            game_state.projectiles.append(
                Fireball(
                    spawn_pos,
                    direction,
                    self.fireball_speed,
                    self.fireball_range,
                    self.fireball_damage,
                    self.fireball_blast_radius,
                    self.fireball_fuse_time,
                    knockback_force=self.fireball_knockback,
                )
            )
            self.fireball_last_used = current_time
            logger.info("Player used Fireball.")
            return True

        return False

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
        self.skill_tree_points += 1
        logger.info(f"Level Up! Level: {self.level}, Max HP: {self.max_hp}, Skill points: {self.skill_tree_points}")
        print(f"Level Up! Level: {self.level}, Max HP: {self.max_hp}, Skill points: {self.skill_tree_points}")

    def can_attack(self, current_time=None):
        if current_time is None:
            current_time = pygame.time.get_ticks()
        return current_time - self.last_attack_time >= self.attack_cooldown

    def start_attack(self, current_time=None, show_slash=True):
        if current_time is None:
            current_time = pygame.time.get_ticks()
        self.last_attack_time = current_time
        self.is_attacking = show_slash

    def get_forward_direction(self):
        if self.direction == "up":
            return pygame.Vector2(0, -1)
        if self.direction == "down":
            return pygame.Vector2(0, 1)
        if self.direction == "side":
            return pygame.Vector2(-1, 0) if self.flip else pygame.Vector2(1, 0)
        return pygame.Vector2(1, 0)

    def get_center(self):
        return pygame.Vector2(
            self.pos.x + self.image.get_width() / 2,
            self.pos.y + self.image.get_height() / 2,
        )

    def get_melee_anchor(self):
        return pygame.Vector2(
            self.pos.x + self.image.get_width() / 2,
            self.pos.y + self.image.get_height() * 0.55,
        )

    def attack(self, enemies, aim_direction=None, cone_degrees=90.0):
        current_time = pygame.time.get_ticks()
        if not self.can_attack(current_time):
            return

        self.start_attack(current_time, show_slash=True)
        logger.info("Player attacks!")

        forward = self.get_forward_direction()
        if forward.length_squared() == 0:
            forward = pygame.Vector2(1, 0)

        if aim_direction is None:
            aim_dir = pygame.Vector2(forward)
        else:
            aim_dir = pygame.Vector2(aim_direction)
            if aim_dir.length_squared() == 0:
                aim_dir = pygame.Vector2(forward)

        aim_dir = aim_dir.normalize()
        self.last_attack_dir = pygame.Vector2(aim_dir)

        cone_half_angle = max(0.0, float(cone_degrees) * 0.5)
        cos_half_angle = math.cos(math.radians(cone_half_angle))
        range_sq = float(self.attack_range) * float(self.attack_range)
        origin = self.get_melee_anchor() + aim_dir * self.melee_origin_offset

        for enemy in enemies:
            enemy_rect = enemy.get_rect()
            enemy_center = pygame.Vector2(enemy_rect.centerx, enemy_rect.centery)
            to_enemy = enemy_center - origin
            dist_sq = to_enemy.length_squared()
            if dist_sq > range_sq:
                continue

            if dist_sq == 0:
                hit = True
                knock_dir = pygame.Vector2(aim_dir)
            else:
                to_enemy_dir = to_enemy.normalize()
                hit = aim_dir.dot(to_enemy_dir) >= cos_half_angle
                knock_dir = to_enemy_dir

            if not hit:
                continue

            logger.info(f"Hit enemy for {self.attack_damage} damage!")
            enemy.take_damage(self.attack_damage)

            knockback_force = 20
            enemy.pos += knock_dir * knockback_force

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

        if self.dash_active_time > 0:
            self.velocity = pygame.Vector2(self.dash_direction)
            if self.velocity.length_squared() == 0:
                self.velocity = self.get_forward_direction()
            if self.velocity.length_squared() == 0:
                self.velocity = pygame.Vector2(1, 0)

            self.velocity = self.velocity.normalize()
            self.moving = True

            if abs(self.velocity.x) > abs(self.velocity.y):
                self.direction = "side"
                self.flip = self.velocity.x < 0
            else:
                self.direction = "down" if self.velocity.y > 0 else "up"

            self.speed = self.base_speed * self.dash_speed_multiplier
            return

        wants_to_sprint = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        if wants_to_sprint and self.stamina > 0 and self.can_sprint:
            self.is_sprinting = True

        current_speed = self.base_speed * self.speed_multiplier
        if self.is_sprinting:
            current_speed *= self.sprint_multiplier
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

        if self.dash_active_time > 0:
            self.dash_active_time = max(0.0, self.dash_active_time - dt)
        
        # Reset speed to base speed for next frame logic (if needed elsewhere)
        # Though _set_velocity will overwrite it again next frame.
        self.speed = self.base_speed 

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

    def take_damage(self, amount, ignore_invulnerability=False):
        if self.invulnerable and not ignore_invulnerability:
            return
            
        self.hp -= amount
        
        if not ignore_invulnerability:
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

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        # Blink if invulnerable
        if self.invulnerable and int(pygame.time.get_ticks() / 100) % 2 == 0:
            pass # Skip drawing for blinking effect
        else:
            # Draw relative to self.pos (top-left of sprite), NOT self.get_rect() (hitbox)
            draw_pos = (int(self.pos.x - camera_offset.x), int(self.pos.y - camera_offset.y))
            img = self.image
            if self.direction == "side" and self.flip:
                img = self.animations_flipped["side"][self.frame_index]
            screen.blit(img, draw_pos)
        
        # Draw attack visual
        if self.is_attacking:
            attack_dir = pygame.Vector2(self.last_attack_dir)
            if attack_dir.length_squared() == 0:
                attack_dir = self.get_forward_direction()
            if attack_dir.length_squared() == 0:
                attack_dir = pygame.Vector2(1, 0)
            else:
                attack_dir = attack_dir.normalize()

            slash_size = 120
            slash_surface = pygame.Surface((slash_size, slash_size), pygame.SRCALPHA)

            color = (255, 255, 255, 200)
            width = 5
            rect = pygame.Rect(10, 10, slash_size - 20, slash_size - 20)
            pygame.draw.arc(
                slash_surface,
                color,
                rect,
                math.radians(300),
                math.radians(420),
                width,
            )

            angle_deg = -math.degrees(math.atan2(attack_dir.y, attack_dir.x))
            rotated = pygame.transform.rotate(slash_surface, angle_deg)

            base_anchor = self.get_melee_anchor() + attack_dir * self.melee_origin_offset
            center = base_anchor + attack_dir * self.melee_slash_distance
            rotated_rect = rotated.get_rect(center=(int(center.x - camera_offset.x), int(center.y - camera_offset.y)))
            screen.blit(rotated, rotated_rect.topleft)