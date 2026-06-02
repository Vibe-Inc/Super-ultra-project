import math
import random

import pygame
from src.core.logger import logger
from src.entities.projectile import Fireball, GlacialCascade, FrostNova, ChainLightning, Thunderstrike, EntanglingRoots, NatureBolt
from src.entities.nature_spirit import NatureSpirit

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

        # Flame Shield skill
        self.flame_shield_duration = 6.0       # seconds active
        self.flame_shield_cooldown = 14000      # ms cooldown
        self.flame_shield_last_used = -14000    # ms timestamp
        self.flame_shield_active = False
        self.flame_shield_active_time = 0.0     # remaining active time
        self.flame_shield_damage_per_sec = 8.0
        self.flame_shield_radius = 110.0        # pixels
        self.flame_shield_particles = []        # visual particles
        self.flame_shield_damage_acc = 0.0      # fractional damage accumulator

        # Frost Nova skill
        self.frost_nova_radius = 150.0
        self.frost_nova_freeze_duration = 3.0
        self.frost_nova_damage = 0
        self.frost_nova_cooldown = 8000
        self.frost_nova_last_used = -self.frost_nova_cooldown

        # Ice Armor skill
        self.ice_armor_duration = 8.0
        self.ice_armor_cooldown = 16000
        self.ice_armor_last_used = -self.ice_armor_cooldown
        self.ice_armor_active = False
        self.ice_armor_active_time = 0.0
        self.ice_armor_remaining_absorption = 30.0
        self.ice_armor_max_absorption = 30.0
        self.ice_armor_slow_radius = 80.0
        self.ice_armor_slow_factor = 0.5
        self.ice_armor_particles = []

        # Glacial Cascade skill
        self.glacial_cascade_speed = 400.0
        self.glacial_cascade_range = 500.0
        self.glacial_cascade_damage = 35
        self.glacial_cascade_freeze_duration = 2.0
        self.glacial_cascade_cooldown = 3000
        self.glacial_cascade_last_used = -self.glacial_cascade_cooldown
        self.glacial_cascade_width = 80.0

        # Chain Lightning skill
        self.chain_lightning_speed = 500.0
        self.chain_lightning_range = 550.0
        self.chain_lightning_damage = 22
        self.chain_lightning_chain_range = 180.0
        self.chain_lightning_max_targets = 5
        self.chain_lightning_cooldown = 2500
        self.chain_lightning_last_used = -self.chain_lightning_cooldown

        # Thunderstrike skill
        self.thunderstrike_damage = 55
        self.thunderstrike_radius = 100.0
        self.thunderstrike_range = 600.0
        self.thunderstrike_cooldown = 4000
        self.thunderstrike_last_used = -self.thunderstrike_cooldown

        # Passive: Static Field
        self.static_field = False
        self.static_field_proc_chance = 0.12
        self.static_field_damage = 20

        # Entangling Roots skill
        self.entangling_roots_speed = 380.0
        self.entangling_roots_range = 500.0
        self.entangling_roots_radius = 140.0
        self.entangling_roots_root_duration = 4.0
        self.entangling_roots_damage = 0
        self.entangling_roots_cooldown = 7000
        self.entangling_roots_last_used = -self.entangling_roots_cooldown

        # Summon Spirit skill
        self.summon_spirit_damage = 15
        self.summon_spirit_duration = 10.0
        self.summon_spirit_cooldown = 12000
        self.summon_spirit_last_used = -self.summon_spirit_cooldown

        # Passive: Regeneration
        self.regeneration = False
        self.regeneration_hp_per_sec = 3.0
        self.regeneration_acc = 0.0

        # Passive: Pyromancer's Fury
        self.pyromancers_fury = False
        self.pyromancers_fury_damage_mult = 1.25   # +25% fire damage
        self.pyromancers_fury_area_mult = 1.15     # +15% fire area
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
            "description": "Launch an explosive fireball dealing 28 damage with area effect and knockback.",
            "color": (188, 82, 35),
            "accent": (255, 214, 120),
        })
        logger.info("Player learned Fireball!")

    def learn_flame_shield(self):
        """Add the Flame Shield skill to the skillbook if not already present."""
        for skill in self.skillbook:
            if skill.get("skill_id") == "flame_shield":
                return  # already learned
        self.skillbook.append({
            "skill_id": "flame_shield",
            "name": "Flame Shield",
            "description": "Surrounds you with flames, dealing 8 damage/sec to nearby enemies.",
            "color": (220, 80, 20),
            "accent": (255, 180, 60),
        })
        logger.info("Player learned Flame Shield!")

    def learn_pyromancers_fury(self):
        """Activate the Pyromancer's Fury passive: fire skills deal 25% more damage and have 15% larger area."""
        self.pyromancers_fury = True
        logger.info("Player unlocked Pyromancer's Fury (passive)!")

    def learn_frost_nova(self):
        """Add the Frost Nova skill to the skillbook if not already present."""
        for skill in self.skillbook:
            if skill.get("skill_id") == "frost_nova":
                return
        self.skillbook.append({
            "skill_id": "frost_nova",
            "name": "Frost Nova",
            "description": "Freeze all enemies within radius for 3 seconds.",
            "color": (60, 140, 255),
            "accent": (180, 220, 255),
        })
        logger.info("Player learned Frost Nova!")

    def learn_ice_armor(self):
        """Add the Ice Armor skill to the skillbook if not already present."""
        for skill in self.skillbook:
            if skill.get("skill_id") == "ice_armor":
                return
        self.skillbook.append({
            "skill_id": "ice_armor",
            "name": "Ice Armor",
            "description": "Grants a shield of ice absorbing 30 damage and slowing attackers.",
            "color": (40, 100, 220),
            "accent": (140, 200, 255),
        })
        logger.info("Player learned Ice Armor!")

    def learn_glacial_cascade(self):
        """Add the Glacial Cascade skill to the skillbook if not already present."""
        for skill in self.skillbook:
            if skill.get("skill_id") == "glacial_cascade":
                return
        self.skillbook.append({
            "skill_id": "glacial_cascade",
            "name": "Glacial Cascade",
            "description": "Ice shards cascade outward dealing 35 damage and freezing enemies.",
            "color": (80, 160, 240),
            "accent": (200, 230, 255),
        })
        logger.info("Player learned Glacial Cascade!")

    def learn_chain_lightning(self):
        for skill in self.skillbook:
            if skill.get("skill_id") == "chain_lightning":
                return
        self.skillbook.append({
            "skill_id": "chain_lightning",
            "name": "Chain Lightning",
            "description": "Fires a lightning bolt that jumps between up to 5 enemies.",
            "color": (255, 220, 50),
            "accent": (255, 255, 180),
        })
        logger.info("Player learned Chain Lightning!")

    def learn_static_field(self):
        self.static_field = True
        logger.info("Player unlocked Static Field (passive)!")

    def learn_thunderstrike(self):
        for skill in self.skillbook:
            if skill.get("skill_id") == "thunderstrike":
                return
        self.skillbook.append({
            "skill_id": "thunderstrike",
            "name": "Thunderstrike",
            "description": "Call down lightning from above for 55 damage in a column.",
            "color": (200, 180, 255),
            "accent": (255, 230, 255),
        })
        logger.info("Player learned Thunderstrike!")

    def learn_entangling_roots(self):
        for skill in self.skillbook:
            if skill.get("skill_id") == "entangling_roots":
                return
        self.skillbook.append({
            "skill_id": "entangling_roots",
            "name": "Entangling Roots",
            "description": "Unleash roots that immobilize enemies for 4 seconds.",
            "color": (60, 180, 60),
            "accent": (160, 255, 140),
        })
        logger.info("Player learned Entangling Roots!")

    def learn_regeneration(self):
        self.regeneration = True
        logger.info("Player unlocked Regeneration (passive)!")

    def learn_summon_spirit(self):
        for skill in self.skillbook:
            if skill.get("skill_id") == "summon_spirit":
                return
        self.skillbook.append({
            "skill_id": "summon_spirit",
            "name": "Summon Spirit",
            "description": "Summon a nature spirit that attacks for 15 damage.",
            "color": (100, 220, 120),
            "accent": (200, 255, 200),
        })
        logger.info("Player learned Summon Spirit!")

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
            # Apply Pyromancer's Fury passive: +25% fire damage, +15% area
            fb_damage = self.fireball_damage
            fb_radius = self.fireball_blast_radius
            if self.pyromancers_fury:
                fb_damage = int(fb_damage * self.pyromancers_fury_damage_mult)
                fb_radius = fb_radius * self.pyromancers_fury_area_mult
            game_state.projectiles.append(
                Fireball(
                    spawn_pos,
                    direction,
                    self.fireball_speed,
                    self.fireball_range,
                    fb_damage,
                    fb_radius,
                    self.fireball_fuse_time,
                    knockback_force=self.fireball_knockback,
                )
            )
            self.fireball_last_used = current_time
            logger.info("Player used Fireball.")
            return True

        if skill_id == "flame_shield":
            if self.flame_shield_active:
                return False  # already active
            if current_time - self.flame_shield_last_used < self.flame_shield_cooldown:
                return False  # on cooldown

            self.flame_shield_active = True
            self.flame_shield_active_time = self.flame_shield_duration
            self.flame_shield_last_used = current_time
            logger.info("Player activated Flame Shield.")
            return True

        if skill_id == "frost_nova":
            if current_time - getattr(self, "frost_nova_last_used", -self.frost_nova_cooldown) < self.frost_nova_cooldown:
                return False

            game_state = getattr(self, "game_state", None)
            if game_state is None:
                logger.warning("Frost Nova skill used without an attached game state.")
                return False

            from src.entities.projectile import FrostNova
            center = self.get_center()
            game_state.projectiles.append(
                FrostNova(
                    center,
                    self.frost_nova_radius,
                    self.frost_nova_freeze_duration,
                    self.frost_nova_damage,
                )
            )
            self.frost_nova_last_used = current_time
            logger.info("Player used Frost Nova.")
            return True

        if skill_id == "ice_armor":
            if self.ice_armor_active:
                return False
            if current_time - self.ice_armor_last_used < self.ice_armor_cooldown:
                return False

            self.ice_armor_active = True
            self.ice_armor_active_time = self.ice_armor_duration
            self.ice_armor_remaining_absorption = self.ice_armor_max_absorption
            self.ice_armor_last_used = current_time
            logger.info("Player activated Ice Armor.")
            return True

        if skill_id == "glacial_cascade":
            if current_time - getattr(self, "glacial_cascade_last_used", -self.glacial_cascade_cooldown) < self.glacial_cascade_cooldown:
                return False

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
                logger.warning("Glacial Cascade skill used without an attached game state.")
                return False

            spawn_pos = self.get_melee_anchor() + direction * 22
            game_state.projectiles.append(
                GlacialCascade(
                    spawn_pos,
                    direction,
                    self.glacial_cascade_speed,
                    self.glacial_cascade_range,
                    self.glacial_cascade_damage,
                    self.glacial_cascade_freeze_duration,
                    cascade_width=self.glacial_cascade_width,
                )
            )
            self.glacial_cascade_last_used = current_time
            logger.info("Player used Glacial Cascade.")
            return True

        if skill_id == "chain_lightning":
            if current_time - getattr(self, "chain_lightning_last_used", -self.chain_lightning_cooldown) < self.chain_lightning_cooldown:
                return False

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
                logger.warning("Chain Lightning skill used without an attached game state.")
                return False

            spawn_pos = self.get_melee_anchor() + direction * 18
            game_state.projectiles.append(
                ChainLightning(
                    spawn_pos,
                    direction,
                    self.chain_lightning_speed,
                    self.chain_lightning_range,
                    self.chain_lightning_damage,
                    self.chain_lightning_chain_range,
                    self.chain_lightning_max_targets,
                )
            )
            self.chain_lightning_last_used = current_time
            logger.info("Player used Chain Lightning.")
            return True

        if skill_id == "thunderstrike":
            if current_time - getattr(self, "thunderstrike_last_used", -self.thunderstrike_cooldown) < self.thunderstrike_cooldown:
                return False

            game_state = getattr(self, "game_state", None)
            if game_state is None:
                logger.warning("Thunderstrike skill used without an attached game state.")
                return False

            target_pos = self.get_melee_anchor()
            if aim_direction is not None:
                aim_vec = pygame.Vector2(aim_direction)
                if aim_vec.length_squared() > 0:
                    target_pos = target_pos + aim_vec.normalize() * self.thunderstrike_range

            game_state.projectiles.append(
                Thunderstrike(
                    target_pos,
                    self.thunderstrike_damage,
                    self.thunderstrike_radius,
                )
            )
            self.thunderstrike_last_used = current_time
            logger.info("Player used Thunderstrike.")
            return True

        if skill_id == "entangling_roots":
            if current_time - getattr(self, "entangling_roots_last_used", -self.entangling_roots_cooldown) < self.entangling_roots_cooldown:
                return False

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
                logger.warning("Entangling Roots skill used without an attached game state.")
                return False

            spawn_pos = self.get_melee_anchor() + direction * 18
            game_state.projectiles.append(
                EntanglingRoots(
                    spawn_pos,
                    direction,
                    self.entangling_roots_speed,
                    self.entangling_roots_range,
                    self.entangling_roots_radius,
                    self.entangling_roots_root_duration,
                    self.entangling_roots_damage,
                )
            )
            self.entangling_roots_last_used = current_time
            logger.info("Player used Entangling Roots.")
            return True

        if skill_id == "summon_spirit":
            if current_time - getattr(self, "summon_spirit_last_used", -self.summon_spirit_cooldown) < self.summon_spirit_cooldown:
                return False

            game_state = getattr(self, "game_state", None)
            if game_state is None:
                logger.warning("Summon Spirit skill used without an attached game state.")
                return False

            spawn_pos = self.get_melee_anchor()
            spirit = NatureSpirit(
                spawn_pos,
                self,
                damage=self.summon_spirit_damage,
                duration=self.summon_spirit_duration,
            )
            if not hasattr(game_state, "spirits"):
                game_state.spirits = []
            game_state.spirits.append(spirit)
            self.summon_spirit_last_used = current_time
            logger.info("Player used Summon Spirit.")
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

        # Update Flame Shield active timer
        if self.flame_shield_active:
            self.flame_shield_active_time -= dt
            if self.flame_shield_active_time <= 0:
                self.flame_shield_active = False
                self.flame_shield_active_time = 0.0
                self.flame_shield_particles.clear()
                logger.info("Flame Shield expired.")

        # Update Flame Shield particles
        self._update_flame_shield_particles(dt)

        # Update Ice Armor active timer
        if self.ice_armor_active:
            self.ice_armor_active_time -= dt
            if self.ice_armor_active_time <= 0 or self.ice_armor_remaining_absorption <= 0:
                self.ice_armor_active = False
                self.ice_armor_active_time = 0.0
                self.ice_armor_particles.clear()
                if self.ice_armor_remaining_absorption <= 0:
                    logger.info("Ice Armor shattered!")
                else:
                    logger.info("Ice Armor expired.")

        # Update Ice Armor particles
        self._update_ice_armor_particles(dt)

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

        # Ice Armor absorbs damage
        if self.ice_armor_active and self.ice_armor_remaining_absorption > 0 and amount > 0:
            absorbed = min(self.ice_armor_remaining_absorption, float(amount))
            self.ice_armor_remaining_absorption -= absorbed
            amount -= int(absorbed)
            logger.info(f"Ice Armor absorbed {int(absorbed)} damage. Remaining: {int(self.ice_armor_remaining_absorption)}")
            if amount <= 0:
                return

        self.hp -= amount

        # Static Field: 12% chance to shock all nearby enemies when hit
        if self.static_field and amount > 0:
            if random.random() < self.static_field_proc_chance:
                game_state = getattr(self, "game_state", None)
                if game_state is not None and hasattr(game_state, "enemies"):
                    player_center = self.get_center()
                    for enemy in list(game_state.enemies):
                        enemy_center = enemy.get_center()
                        distance = player_center.distance_to(enemy_center)
                        if distance < 200:
                            enemy.take_damage(self.static_field_damage)
                            logger.info(f"Static Field shocked {enemy.__class__.__name__} for {self.static_field_damage} damage!")

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

        # Draw Flame Shield visual effect
        if self.flame_shield_active:
            self._draw_flame_shield(screen, camera_offset)

        # Draw Ice Armor visual effect
        if self.ice_armor_active:
            self._draw_ice_armor(screen, camera_offset)

    # ─── Flame Shield helpers ───────────────────────────────────────────

    def _update_flame_shield_particles(self, dt):
        """Spawn, move, and cull flame particles around the character."""
        import random

        # Spawn new particles while active
        if self.flame_shield_active:
            spawn_count = max(1, int(18 * dt))  # particles per frame
            for _ in range(spawn_count):
                effective_radius = self.flame_shield_radius
                if self.pyromancers_fury:
                    effective_radius *= self.pyromancers_fury_area_mult
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(effective_radius * 0.45, effective_radius)
                speed = random.uniform(25, 70)  # upward drift speed
                self.flame_shield_particles.append({
                    "angle": angle,
                    "dist": dist,
                    "life": random.uniform(0.3, 0.7),
                    "max_life": random.uniform(0.3, 0.7),
                    "size": random.uniform(2.5, 6.0),
                    "drift": random.uniform(-15, 15),
                    "vertical_speed": -speed,
                    "color": random.choice([
                        (255, 120, 20),   # orange
                        (255, 80, 10),    # deep orange
                        (255, 180, 40),   # bright yellow
                        (255, 60, 10),    # red-orange
                        (255, 200, 80),   # bright yellow
                    ]),
                })

        # Update existing particles
        for p in self.flame_shield_particles[:]:
            p["life"] -= dt
            if p["life"] <= 0:
                self.flame_shield_particles.remove(p)
                continue
            # Slowly spiral inward and drift upward
            p["angle"] += p["drift"] * dt
            p["dist"] = max(0, p["dist"] - 8 * dt)
            p["vertical_speed"] -= 120 * dt  # accelerate upward (negative)

    def _draw_flame_shield(self, screen, camera_offset):
        """Draw the flame shield aura and particles."""
        center = self.get_center()
        cx = center.x - camera_offset.x
        cy = center.y - camera_offset.y
        t = pygame.time.get_ticks() / 1000.0

        # Apply Pyromancer's Fury area buff to visual radius
        visual_radius = self.flame_shield_radius
        if self.pyromancers_fury:
            visual_radius *= self.pyromancers_fury_area_mult

        # ── Inner pulsing glow ring ──
        pulse = 0.6 + 0.4 * math.sin(t * 6.0)
        glow_radius = visual_radius * (0.85 + 0.15 * pulse)
        glow_surf = pygame.Surface((int(glow_radius * 2) + 4, int(glow_radius * 2) + 4), pygame.SRCALPHA)
        glow_a = int(35 + 25 * pulse)
        pygame.draw.circle(glow_surf, (255, 100, 20, glow_a),
                           (int(glow_radius) + 2, int(glow_radius) + 2),
                           int(glow_radius))
        # brighter inner core
        inner_r = int(glow_radius * 0.55)
        inner_a = int(25 + 20 * pulse)
        pygame.draw.circle(glow_surf, (255, 160, 40, inner_a),
                           (int(glow_radius) + 2, int(glow_radius) + 2),
                           inner_r)
        screen.blit(glow_surf, (int(cx - glow_radius - 2), int(cy - glow_radius - 2)))

        # ── Outer flickering ring ──
        ring_r = visual_radius
        ring_a = int(70 + 40 * math.sin(t * 9.0))
        ring_surf = pygame.Surface((int(ring_r * 2) + 4, int(ring_r * 2) + 4), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (255, 90, 10, ring_a),
                           (int(ring_r) + 2, int(ring_r) + 2),
                           int(ring_r), max(1, int(3 * pulse)))
        screen.blit(ring_surf, (int(cx - ring_r - 2), int(cy - ring_r - 2)))

        # ── Flame particles ──
        for p in self.flame_shield_particles:
            life_ratio = p["life"] / p["max_life"] if p["max_life"] > 0 else 0
            if life_ratio <= 0:
                continue

            # World position from polar around center
            px = cx + math.cos(p["angle"]) * p["dist"]
            py = cy + math.sin(p["angle"]) * p["dist"] + p["vertical_speed"] * (1 - life_ratio) * 0.3

            alpha = int(255 * life_ratio)
            size = max(1, int(p["size"] * life_ratio))
            r, g, b = p["color"]

            # Glow layer
            glow_sz = size * 3
            glow = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (r, g, b, alpha // 3),
                               (glow_sz, glow_sz), glow_sz)
            screen.blit(glow, (int(px - glow_sz), int(py - glow_sz)))

            # Core
            if alpha > 20:
                pygame.draw.circle(screen, (min(255, r + 40), min(255, g + 30), b),
                                   (int(px), int(py)), size)

        # ── Rising ember sparkles ──
        if self.flame_shield_active:
            import random
            for _ in range(2):
                em_angle = random.uniform(0, math.pi * 2)
                em_dist = random.uniform(0, visual_radius * 0.3)
                em_x = cx + math.cos(em_angle) * em_dist
                em_y = cy + random.uniform(-20, 20)
                em_size = random.randint(1, 3)
                em_color = random.choice([(255, 220, 100), (255, 180, 60), (255, 255, 140)])
                pygame.draw.circle(screen, em_color, (int(em_x), int(em_y)), em_size)

    # ─── Ice Armor helpers ───────────────────────────────────────────

    def _update_ice_armor_particles(self, dt):
        """Spawn, move, and cull ice particles around the character."""
        import random

        if self.ice_armor_active:
            spawn_count = max(1, int(15 * dt))
            for _ in range(spawn_count):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(self.ice_armor_slow_radius * 0.3, self.ice_armor_slow_radius)
                speed = random.uniform(20, 50)
                self.ice_armor_particles.append({
                    "angle": angle,
                    "dist": dist,
                    "life": random.uniform(0.4, 0.8),
                    "max_life": random.uniform(0.4, 0.8),
                    "size": random.uniform(2.0, 5.0),
                    "drift": random.uniform(-10, 10),
                    "vertical_speed": -speed,
                    "color": random.choice([
                        (180, 220, 255),
                        (200, 235, 255),
                        (160, 200, 255),
                        (220, 240, 255),
                        (140, 190, 255),
                    ]),
                })

        for p in self.ice_armor_particles[:]:
            p["life"] -= dt
            if p["life"] <= 0:
                self.ice_armor_particles.remove(p)
                continue
            p["angle"] += p["drift"] * dt
            p["dist"] = max(0, p["dist"] - 6 * dt)
            p["vertical_speed"] -= 80 * dt

    def _draw_ice_armor(self, screen, camera_offset):
        """Draw the ice armor aura and particles."""
        import random
        center = self.get_center()
        cx = center.x - camera_offset.x
        cy = center.y - camera_offset.y
        t = pygame.time.get_ticks() / 1000.0

        visual_radius = self.ice_armor_slow_radius

        # ── Inner frost glow ring ──
        pulse = 0.5 + 0.5 * math.sin(t * 4.0)
        glow_radius = visual_radius * (0.8 + 0.2 * pulse)
        glow_surf = pygame.Surface((int(glow_radius * 2) + 4, int(glow_radius * 2) + 4), pygame.SRCALPHA)
        glow_a = int(30 + 20 * pulse)
        pygame.draw.circle(glow_surf, (60, 140, 255, glow_a),
                           (int(glow_radius) + 2, int(glow_radius) + 2),
                           int(glow_radius))
        inner_r = int(glow_radius * 0.5)
        inner_a = int(20 + 15 * pulse)
        pygame.draw.circle(glow_surf, (140, 200, 255, inner_a),
                           (int(glow_radius) + 2, int(glow_radius) + 2),
                           inner_r)
        screen.blit(glow_surf, (int(cx - glow_radius - 2), int(cy - glow_radius - 2)))

        # ── Outer frost ring ──
        ring_r = visual_radius
        ring_a = int(60 + 40 * math.sin(t * 7.0))
        ring_surf = pygame.Surface((int(ring_r * 2) + 4, int(ring_r * 2) + 4), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (100, 180, 255, ring_a),
                           (int(ring_r) + 2, int(ring_r) + 2),
                           int(ring_r), max(1, int(2 * pulse)))
        screen.blit(ring_surf, (int(cx - ring_r - 2), int(cy - ring_r - 2)))

        # ── Ice crystal shield overlay ──
        shard_count = 8
        for i in range(shard_count):
            shard_angle = t * 0.5 + i * (math.pi * 2 / shard_count)
            shard_dist = visual_radius * 0.7 + 10 * math.sin(t * 3.0 + i)
            sx = cx + math.cos(shard_angle) * shard_dist
            sy = cy + math.sin(shard_angle) * shard_dist
            shard_size = max(2, int(4 + 2 * math.sin(t * 2.0 + i * 1.5)))
            shard_alpha = int(100 + 80 * math.sin(t * 5.0 + i * 2.0))
            shard_color = (180, 220, 255, shard_alpha)
            # Draw shard as small diamond
            pts = [
                (sx, sy - shard_size),
                (sx + shard_size * 0.6, sy),
                (sx, sy + shard_size),
                (sx - shard_size * 0.6, sy),
            ]
            pygame.draw.polygon(screen, shard_color[:3], pts)
            pygame.draw.polygon(screen, (220, 240, 255), pts, 1)

        # ── Ice particles ──
        for p in self.ice_armor_particles:
            life_ratio = p["life"] / p["max_life"] if p["max_life"] > 0 else 0
            if life_ratio <= 0:
                continue

            px = cx + math.cos(p["angle"]) * p["dist"]
            py = cy + math.sin(p["angle"]) * p["dist"] + p["vertical_speed"] * (1 - life_ratio) * 0.3

            alpha = int(200 * life_ratio)
            size = max(1, int(p["size"] * life_ratio))
            r, g, b = p["color"]

            glow_sz = size * 3
            glow = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (r, g, b, alpha // 3),
                               (glow_sz, glow_sz), glow_sz)
            screen.blit(glow, (int(px - glow_sz), int(py - glow_sz)))

            if alpha > 20:
                pygame.draw.circle(screen, (min(255, r + 40), min(255, g + 30), min(255, b + 10)),
                                   (int(px), int(py)), size)

        # ── Shield health indicator (frost cracks at edges) ──
        absorb_ratio = self.ice_armor_remaining_absorption / self.ice_armor_max_absorption
        if absorb_ratio < 0.5:
            crack_alpha = int(150 * (1.0 - absorb_ratio * 2))
            for _ in range(3):
                crack_angle = random.uniform(0, math.pi * 2)
                crack_dist = visual_radius
                cpx = cx + math.cos(crack_angle) * crack_dist
                cpy = cy + math.sin(crack_angle) * crack_dist
                pygame.draw.line(screen, (200, 220, 255, crack_alpha),
                                 (cpx - 3, cpy - 3), (cpx + 3, cpy + 3), 2)

        # ── Frost sparkles ──
        if self.ice_armor_active:
            for _ in range(2):
                sp_angle = random.uniform(0, math.pi * 2)
                sp_dist = random.uniform(0, visual_radius * 0.4)
                sp_x = cx + math.cos(sp_angle) * sp_dist
                sp_y = cy + random.uniform(-15, 15)
                sp_size = random.randint(1, 2)
                sp_color = random.choice([(200, 240, 255), (160, 210, 255), (220, 250, 255)])
                pygame.draw.circle(screen, sp_color, (int(sp_x), int(sp_y)), sp_size)
