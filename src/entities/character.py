import math
import random

import pygame
from database.effects import PoisonEffect
from src.core.logger import logger
from src.entities.projectile import Fireball, GlacialCascade, FrostNova, ChainLightning, Thunderstrike, EntanglingRoots, NatureBolt, DarkPact, ArcaneMissile
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

        # Armor / defense system (consumed by Armor items)
        self.defense = 0

        # Buff / debuff dynamic multipliers (touched by HasteEffect, LethargyEffect, ...)
        self.damage_bonus = 0         # flat damage added to every attack
        self.cooldown_multiplier = 1.0  # <1 = faster, >1 = slower
        self.shield = 0.0             # absorbs damage before HP is touched

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
        self.attack_cooldown_mult = 1.0
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

        # Shadow Step skill
        self.shadow_step_range = 300.0
        self.shadow_step_cooldown = 6000
        self.shadow_step_last_used = -self.shadow_step_cooldown
        self.shadow_step_invuln_duration = 0.5

        # Passive: Poison Blade
        self.poison_blade = False
        self.poison_blade_damage_per_sec = 6.0
        self.poison_blade_duration = 5.0

        # Dark Pact skill
        self.dark_pact_hp_cost_percent = 0.1
        self.dark_pact_damage = 60
        self.dark_pact_radius = 150.0
        self.dark_pact_cooldown = 8000
        self.dark_pact_last_used = -self.dark_pact_cooldown

        # Arcane Missiles skill
        self.arcane_missiles_speed = 420.0
        self.arcane_missiles_range = 500.0
        self.arcane_missiles_damage = 14
        self.arcane_missiles_count = 5
        self.arcane_missiles_cooldown = 4000
        self.arcane_missiles_last_used = -self.arcane_missiles_cooldown

        # Passive: Mana Flow
        self.mana_flow = False

        # Mystic Barrier skill
        self.mystic_barrier_duration = 5.0
        self.mystic_barrier_cooldown = 12000
        self.mystic_barrier_last_used = -self.mystic_barrier_cooldown
        self.mystic_barrier_active = False
        self.mystic_barrier_active_time = 0.0
        self.mystic_barrier_reflect_pct = 0.3
        self.mystic_barrier_particles = []

        # Eternal Fortress keystone (passive)
        self.eternal_fortress = False

        # Soul Harvest keystone (passive)
        self.soul_harvest = False
        self.soul_harvest_stacks = []
        self.soul_harvest_duration = 8.0
        self.soul_harvest_hp_per_kill = 5
        self.soul_harvest_damage_per_stack = 0.02

        # Void Walker keystone (passive)
        self.void_walker = False
        self.void_walker_dodge_chance = 0.3
        self.void_walker_teleport_range = 200.0
        self.void_walker_afterimage_damage = 18

        # Floating text popups
        self.floating_texts = []

        # Elemental Mastery keystone (passive)
        self.elemental_mastery = False
        self.elemental_damage_mult = 1.35
        self.last_elemental_skill = None
        self.last_elemental_time = 0.0
        self.combo_window = 3.0
        self.elemental_damage_attrs = frozenset({
            "fireball_damage", "frost_nova_damage", "glacial_cascade_damage",
            "chain_lightning_damage", "thunderstrike_damage", "static_field_damage",
        })

        # Berserker's Rage keystone
        self.berserkers_rage_active = False
        self.berserkers_rage_duration = 8.0
        self.berserkers_rage_active_time = 0.0
        self.berserkers_rage_cooldown = 20000
        self.berserkers_rage_last_used = -self.berserkers_rage_cooldown
        self.berserkers_rage_particles = []

        # Chrono Shift keystone
        self.chrono_shift_active = False
        self.chrono_shift_duration = 3.0
        self.chrono_shift_active_time = 0.0
        self.chrono_shift_cooldown = 30000
        self.chrono_shift_last_used = -self.chrono_shift_cooldown
        self.chrono_shift_particles = []

        self.dash_speed_multiplier = 3.0
        self.dash_duration = 0.14
        self.dash_cooldown = 900
        self.dash_active_time = 0.0
        self.dash_last_used = -self.dash_cooldown
        self.dash_direction = pygame.Vector2(1, 0)

    def __getattribute__(self, name):
        if name.endswith("_cooldown") and name not in ("attack_cooldown", "base_attack_cooldown"):
            try:
                mana_flow = object.__getattribute__(self, "mana_flow")
            except AttributeError:
                mana_flow = False
            try:
                cd_mult = object.__getattribute__(self, "skill_cooldown_mult")
            except AttributeError:
                cd_mult = 1.0
            if mana_flow or cd_mult != 1.0:
                actual = object.__getattribute__(self, name)
                if actual is not None:
                    mult = (0.8 if mana_flow else 1.0) * cd_mult
                    return int(actual * mult)
        if name.endswith("_damage"):
            try:
                rage = object.__getattribute__(self, "berserkers_rage_active")
            except AttributeError:
                rage = False
            try:
                soul_harvest = object.__getattribute__(self, "soul_harvest")
            except AttributeError:
                soul_harvest = False
            try:
                elem = object.__getattribute__(self, "elemental_mastery")
            except AttributeError:
                elem = False
            if rage or soul_harvest or elem:
                actual = object.__getattribute__(self, name)
                if actual is not None and isinstance(actual, (int, float)):
                    mult = 1.0
                    if rage:
                        mult *= 1.5
                    if soul_harvest:
                        stacks = object.__getattribute__(self, "soul_harvest_stacks")
                        mult *= 1.0 + len(stacks) * 0.02
                    if elem:
                        try:
                            elem_attrs = object.__getattribute__(self, "elemental_damage_attrs")
                            if name in elem_attrs:
                                mult *= object.__getattribute__(self, "elemental_damage_mult")
                        except AttributeError:
                            pass
                    return int(actual * mult)
        if name == "attack_cooldown":
            try:
                chrono = object.__getattribute__(self, "chrono_shift_active")
            except AttributeError:
                chrono = False
            if chrono:
                base = object.__getattribute__(self, "base_attack_cooldown")
                if base is not None:
                    return int(base * 0.75)
            try:
                cd_mult = object.__getattribute__(self, "attack_cooldown_mult")
            except AttributeError:
                cd_mult = 1.0
            if cd_mult != 1.0:
                base = object.__getattribute__(self, "base_attack_cooldown")
                if base is not None:
                    return int(base * cd_mult)
        return object.__getattribute__(self, name)

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

    def learn_shadow_step(self):
        for skill in self.skillbook:
            if skill.get("skill_id") == "shadow_step":
                return
        self.skillbook.append({
            "skill_id": "shadow_step",
            "name": "Shadow Step",
            "description": "Teleport through shadows, becoming invulnerable briefly.",
            "color": (100, 50, 140),
            "accent": (200, 160, 255),
        })
        logger.info("Player learned Shadow Step!")

    def learn_poison_blade(self):
        self.poison_blade = True
        logger.info("Player unlocked Poison Blade (passive)!")

    def learn_dark_pact(self):
        for skill in self.skillbook:
            if skill.get("skill_id") == "dark_pact":
                return
        self.skillbook.append({
            "skill_id": "dark_pact",
            "name": "Dark Pact",
            "description": "Sacrifice 10% HP to deal 60 shadow damage to all nearby enemies.",
            "color": (140, 60, 180),
            "accent": (220, 160, 255),
        })
        logger.info("Player learned Dark Pact!")

    def learn_arcane_missiles(self):
        for skill in self.skillbook:
            if skill.get("skill_id") == "arcane_missiles":
                return
        self.skillbook.append({
            "skill_id": "arcane_missiles",
            "name": "Arcane Missiles",
            "description": "Fire homing arcane missiles dealing 22 damage each.",
            "color": (140, 60, 120),
            "accent": (255, 180, 240),
        })
        logger.info("Player learned Arcane Missiles!")

    def learn_mana_flow(self):
        self.mana_flow = True
        logger.info("Player unlocked Mana Flow (passive)!")

    def learn_mystic_barrier(self):
        for skill in self.skillbook:
            if skill.get("skill_id") == "mystic_barrier":
                return
        self.skillbook.append({
            "skill_id": "mystic_barrier",
            "name": "Mystic Barrier",
            "description": "Creates a barrier that reflects 30% of incoming damage.",
            "color": (180, 80, 160),
            "accent": (255, 200, 240),
        })
        logger.info("Player learned Mystic Barrier!")

    def learn_berserkers_rage(self):
        for skill in self.skillbook:
            if skill.get("skill_id") == "berserkers_rage":
                return
        self.skillbook.append({
            "skill_id": "berserkers_rage",
            "name": "Berserker's Rage",
            "description": "+50% damage dealt, +20% damage taken. The fury consumes you.",
            "color": (200, 50, 30),
            "accent": (255, 160, 60),
        })
        logger.info("Player learned Berserker's Rage!")

    def learn_eternal_fortress(self):
        if self.eternal_fortress:
            return
        self.eternal_fortress = True
        self.max_hp += 40
        self.hp += 40
        self.speed_multiplier *= 0.85
        self.speed = self.base_speed * self.speed_multiplier
        logger.info("Player learned Eternal Fortress (passive)! (+40 HP, +80% defense, -15% speed)")

    def learn_soul_harvest(self):
        if self.soul_harvest:
            return
        self.soul_harvest = True
        logger.info("Player learned Soul Harvest (passive)! (5 HP/kill, +2% damage stack)")

    def learn_void_walker(self):
        if self.void_walker:
            return
        self.void_walker = True
        logger.info("Player learned Void Walker (passive)! (30% dodge, teleport, afterimage)")

    def learn_elemental_mastery(self):
        if self.elemental_mastery:
            return
        self.elemental_mastery = True
        logger.info("Player learned Elemental Mastery (passive)! (+35% elemental damage, dual-element combos)")

    def learn_chrono_shift(self):
        for skill in self.skillbook:
            if skill.get("skill_id") == "chrono_shift":
                return
        self.skillbook.append({
            "skill_id": "chrono_shift",
            "name": "Chrono Shift",
            "description": "Slow time for 3 seconds. +25% attack speed. Cooldown: 30s.",
            "color": (100, 160, 220),
            "accent": (200, 230, 255),
        })
        logger.info("Player learned Chrono Shift!")

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

        # Elemental Mastery: dual-element combo tracking
        if self.elemental_mastery:
            element_map = {
                "fireball": "fire", "frost_nova": "ice", "glacial_cascade": "ice",
                "chain_lightning": "lightning", "thunderstrike": "lightning",
            }
            elem = element_map.get(skill_id)
            if elem is not None:
                last_elem = getattr(self, "last_elemental_skill", None)
                last_time = getattr(self, "last_elemental_time", 0.0)
                combo_window_ms = int(self.combo_window * 1000)
                if (last_elem is not None and last_elem != elem
                        and current_time - last_time < combo_window_ms):
                    game_state = getattr(self, "game_state", None)
                    if game_state is not None and hasattr(game_state, "projectiles"):
                        from src.entities.projectile import ElementalBurst
                        combo_damage = int(self.elemental_damage_mult * 30) + getattr(self, "combo_damage_bonus", 0)
                        game_state.projectiles.append(
                            ElementalBurst(self.get_center(), combo_damage)
                        )
                    self.add_floating_text("Elemental Combo!", self.pos.x, self.pos.y - 40, (255, 200, 100), 1.5, 22)
                self.last_elemental_skill = elem
                self.last_elemental_time = current_time

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

            target_pos = self.get_center()
            if aim_direction is not None:
                aim_vec = pygame.Vector2(aim_direction)
                if aim_vec.length_squared() > 0:
                    max_range_sq = self.thunderstrike_range * self.thunderstrike_range
                    if aim_vec.length_squared() > max_range_sq:
                        aim_vec = aim_vec.normalize() * self.thunderstrike_range
                    target_pos = target_pos + aim_vec

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

        if skill_id == "shadow_step":
            if current_time - getattr(self, "shadow_step_last_used", -self.shadow_step_cooldown) < self.shadow_step_cooldown:
                return False

            direction = pygame.Vector2(aim_direction) if aim_direction is not None else pygame.Vector2(self.velocity)
            if direction.length_squared() == 0:
                direction = self.get_forward_direction()
            if direction.length_squared() == 0:
                direction = pygame.Vector2(1, 0)

            teleport_offset = direction.normalize() * self.shadow_step_range
            self.pos += teleport_offset
            self.invulnerable = True
            self.invulnerability_timer = self.shadow_step_invuln_duration
            self.shadow_step_last_used = current_time
            logger.info("Player used Shadow Step.")
            return True

        if skill_id == "dark_pact":
            if current_time - getattr(self, "dark_pact_last_used", -self.dark_pact_cooldown) < self.dark_pact_cooldown:
                return False

            hp_cost = int(self.max_hp * self.dark_pact_hp_cost_percent)
            self.hp = max(0, self.hp - hp_cost)

            game_state = getattr(self, "game_state", None)
            if game_state is not None:
                center = self.get_center()
                game_state.projectiles.append(
                    DarkPact(
                        center,
                        self.dark_pact_damage,
                        self.dark_pact_radius,
                    )
                )
            self.dark_pact_last_used = current_time
            logger.info("Player used Dark Pact.")
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

        if skill_id == "arcane_missiles":
            if current_time - getattr(self, "arcane_missiles_last_used", -self.arcane_missiles_cooldown) < self.arcane_missiles_cooldown:
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
                logger.warning("Arcane Missiles skill used without an attached game state.")
                return False

            spawn_pos = self.get_melee_anchor() + direction * 18
            missile_spread = 0.3
            for i in range(self.arcane_missiles_count):
                spread_angle = (i - (self.arcane_missiles_count - 1) / 2) * missile_spread
                spread_dir = pygame.Vector2(direction)
                if spread_angle != 0:
                    cos_a = math.cos(spread_angle)
                    sin_a = math.sin(spread_angle)
                    spread_dir = pygame.Vector2(
                        direction.x * cos_a - direction.y * sin_a,
                        direction.x * sin_a + direction.y * cos_a,
                    )
                game_state.projectiles.append(
                    ArcaneMissile(
                        pygame.Vector2(spawn_pos),
                        spread_dir,
                        self.arcane_missiles_speed,
                        self.arcane_missiles_range,
                        self.arcane_missiles_damage,
                    )
                )
            self.arcane_missiles_last_used = current_time
            logger.info("Player used Arcane Missiles.")
            return True

        if skill_id == "mystic_barrier":
            if self.mystic_barrier_active:
                return False
            if current_time - getattr(self, "mystic_barrier_last_used", -self.mystic_barrier_cooldown) < self.mystic_barrier_cooldown:
                return False

            self.mystic_barrier_active = True
            self.mystic_barrier_active_time = self.mystic_barrier_duration
            self.mystic_barrier_last_used = current_time
            logger.info("Player activated Mystic Barrier.")
            return True

        if skill_id == "berserkers_rage":
            if self.berserkers_rage_active:
                return False
            cd = self.berserkers_rage_cooldown + getattr(self, "berserkers_rage_cooldown_bonus", 0)
            if current_time - getattr(self, "berserkers_rage_last_used", -self.berserkers_rage_cooldown) < cd:
                return False

            self.berserkers_rage_active = True
            duration = self.berserkers_rage_duration + getattr(self, "berserkers_rage_duration_bonus", 0.0)
            self.berserkers_rage_active_time = duration
            self.berserkers_rage_last_used = current_time
            logger.info("Player activated Berserker's Rage!")
            return True

        if skill_id == "chrono_shift":
            if self.chrono_shift_active:
                return False
            cd = self.chrono_shift_cooldown + getattr(self, "chrono_shift_cooldown_bonus", 0)
            if current_time - getattr(self, "chrono_shift_last_used", -self.chrono_shift_cooldown) < cd:
                return False

            self.chrono_shift_active = True
            duration = self.chrono_shift_duration + getattr(self, "chrono_shift_duration_bonus", 0.0)
            self.chrono_shift_active_time = duration
            self.chrono_shift_last_used = current_time
            game_state = getattr(self, "game_state", None)
            if game_state is not None and hasattr(game_state, "enemies"):
                from database.effects import SlowEffect
                for enemy in list(game_state.enemies):
                    enemy.add_effect(SlowEffect(duration, 0.5))
            logger.info("Player activated Chrono Shift!")
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
        effective_cooldown = self.attack_cooldown * getattr(self, "cooldown_multiplier", 1.0)
        return current_time - self.last_attack_time >= effective_cooldown

    def start_attack(self, current_time=None, show_slash=True):
        if current_time is None:
            current_time = pygame.time.get_ticks()
        self.last_attack_time = current_time
        self.is_attacking = show_slash

    def get_effective_attack_damage(self):
        """Compute the final damage of an attack, factoring in weapon + damage_bonus buff."""
        return int(self.attack_damage) + int(getattr(self, "damage_bonus", 0))

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
            final_damage = self.get_effective_attack_damage()
            enemy.take_damage(final_damage)

            # Apply weapon on-hit enchantments (Flaming Sword, etc.) if enemy supports it.
            self._apply_weapon_enchantments(enemy)

            if self.poison_blade:
                enemy.add_effect(PoisonEffect(self.poison_blade_duration, self.poison_blade_damage_per_sec))

            knockback_force = 20
            enemy.pos += knock_dir * knockback_force

    def _apply_weapon_enchantments(self, enemy):
        """
        Apply on-hit effects from the currently equipped weapon (if any).

        New weapons can declare `on_hit_effects` as a list of effect dicts
        (the same shape used by consumable effects) and they will be applied
        to the struck enemy here.
        """
        weapon = getattr(self, "equipped_weapon", None)
        if weapon is None:
            return
        on_hit = getattr(weapon, "on_hit_effects", None)
        if not on_hit:
            return
        from database.effects import create_effect  # local import to avoid cycles
        for effect_data in on_hit:
            if not isinstance(effect_data, dict):
                continue
            effect_obj = create_effect(effect_data)
            if effect_obj is None:
                continue
            if hasattr(enemy, "add_effect"):
                enemy.add_effect(effect_obj)
            else:
                # Fallback: try to apply take_damage for DoT-style effects.
                pass

    def attack_mace(self, enemies, aim_direction=None):
        """Circle AoE centered at the impact point. Hits all enemies in a radius."""
        current_time = pygame.time.get_ticks()
        if not self.can_attack(current_time):
            return

        self.start_attack(current_time, show_slash=True)

        if aim_direction is None:
            aim_direction = self.get_forward_direction()
        aim_dir = pygame.Vector2(aim_direction)
        if aim_dir.length_squared() == 0:
            aim_dir = pygame.Vector2(1, 0)
        aim_dir = aim_dir.normalize()
        self.last_attack_dir = pygame.Vector2(aim_dir)

        origin = self.get_melee_anchor()
        impact_point = origin + aim_dir * self.attack_range
        blast_radius = 55.0
        blast_radius_sq = blast_radius * blast_radius
        knockback_force = 35

        for enemy in enemies:
            enemy_rect = enemy.get_rect()
            enemy_center = pygame.Vector2(enemy_rect.centerx, enemy_rect.centery)
            to_impact = enemy_center - impact_point
            dist_sq = to_impact.length_squared()
            if dist_sq > blast_radius_sq:
                continue

            logger.info(f"Mace hit enemy for {self.attack_damage} damage!")
            final_damage = self.get_effective_attack_damage()
            enemy.take_damage(final_damage)
            self._apply_weapon_enchantments(enemy)

            if self.poison_blade:
                enemy.add_effect(PoisonEffect(self.poison_blade_duration, self.poison_blade_damage_per_sec))

            knock_dir = to_impact.normalize() if dist_sq > 0 else pygame.Vector2(aim_dir)
            enemy.pos += knock_dir * knockback_force

    def attack_axe(self, enemies, aim_direction=None):
        """Full 360° spinning sweep. Hits all enemies within range regardless of direction."""
        current_time = pygame.time.get_ticks()
        if not self.can_attack(current_time):
            return

        self.start_attack(current_time, show_slash=True)

        if aim_direction is None:
            aim_direction = self.get_forward_direction()
        aim_dir = pygame.Vector2(aim_direction)
        if aim_dir.length_squared() == 0:
            aim_dir = pygame.Vector2(1, 0)
        aim_dir = aim_dir.normalize()
        self.last_attack_dir = pygame.Vector2(aim_dir)

        range_sq = float(self.attack_range) * float(self.attack_range)
        origin = self.get_melee_anchor()
        knockback_force = 30

        for enemy in enemies:
            enemy_rect = enemy.get_rect()
            enemy_center = pygame.Vector2(enemy_rect.centerx, enemy_rect.centery)
            to_enemy = enemy_center - origin
            dist_sq = to_enemy.length_squared()
            if dist_sq > range_sq:
                continue

            logger.info(f"Axe spin hit enemy for {self.attack_damage} damage!")
            final_damage = self.get_effective_attack_damage()
            enemy.take_damage(final_damage)
            self._apply_weapon_enchantments(enemy)

            if self.poison_blade:
                enemy.add_effect(PoisonEffect(self.poison_blade_duration, self.poison_blade_damage_per_sec))

            knock_dir = to_enemy.normalize() if dist_sq > 0 else pygame.Vector2(aim_dir)
            enemy.pos += knock_dir * knockback_force

    def attack_spear(self, enemies, aim_direction=None):
        """Long narrow piercing line. Hits enemies in a thin rectangle extending forward."""
        current_time = pygame.time.get_ticks()
        if not self.can_attack(current_time):
            return

        self.start_attack(current_time, show_slash=True)

        if aim_direction is None:
            aim_direction = self.get_forward_direction()
        aim_dir = pygame.Vector2(aim_direction)
        if aim_dir.length_squared() == 0:
            aim_dir = pygame.Vector2(1, 0)
        aim_dir = aim_dir.normalize()
        self.last_attack_dir = pygame.Vector2(aim_dir)

        origin = self.get_melee_anchor()
        half_width = 18.0
        perp = pygame.Vector2(-aim_dir.y, aim_dir.x)
        range_len = float(self.attack_range)
        knockback_force = 25

        for enemy in enemies:
            enemy_rect = enemy.get_rect()
            enemy_center = pygame.Vector2(enemy_rect.centerx, enemy_rect.centery)
            to_enemy = enemy_center - origin

            proj_len = to_enemy.dot(aim_dir)
            if proj_len < 0 or proj_len > range_len:
                continue

            perp_dist = abs(to_enemy.dot(perp))
            if perp_dist > half_width:
                continue

            logger.info(f"Spear pierced enemy for {self.attack_damage} damage!")
            final_damage = self.get_effective_attack_damage()
            enemy.take_damage(final_damage)
            self._apply_weapon_enchantments(enemy)

            if self.poison_blade:
                enemy.add_effect(PoisonEffect(self.poison_blade_duration, self.poison_blade_damage_per_sec))

            enemy.pos += aim_dir * knockback_force

    def attack_dagger(self, enemies, aim_direction=None):
        """Quick short-range double strike. Two rapid hits in a narrow cone."""
        current_time = pygame.time.get_ticks()
        if not self.can_attack(current_time):
            return

        self.start_attack(current_time, show_slash=True)

        if aim_direction is None:
            aim_direction = self.get_forward_direction()
        aim_dir = pygame.Vector2(aim_direction)
        if aim_dir.length_squared() == 0:
            aim_dir = pygame.Vector2(1, 0)
        aim_dir = aim_dir.normalize()
        self.last_attack_dir = pygame.Vector2(aim_dir)

        cone_half_angle = 35.0
        cos_half_angle = math.cos(math.radians(cone_half_angle))
        range_sq = float(self.attack_range) * float(self.attack_range)
        origin = self.get_melee_anchor() + aim_dir * self.melee_origin_offset
        strikes = 2
        knockback_force = 12

        for enemy in enemies:
            enemy_rect = enemy.get_rect()
            enemy_center = pygame.Vector2(enemy_rect.centerx, enemy_rect.centery)
            to_enemy = enemy_center - origin
            dist_sq = to_enemy.length_squared()
            if dist_sq > range_sq:
                continue

            if dist_sq == 0:
                hit = True
            else:
                to_enemy_dir = to_enemy.normalize()
                hit = aim_dir.dot(to_enemy_dir) >= cos_half_angle

            if not hit:
                continue

            final_damage = self.get_effective_attack_damage() * strikes
            logger.info(f"Dagger double-strike hit enemy for {final_damage} damage!")
            enemy.take_damage(final_damage)
            self._apply_weapon_enchantments(enemy)
            if self.poison_blade:
                enemy.add_effect(PoisonEffect(self.poison_blade_duration, self.poison_blade_damage_per_sec))

            if dist_sq > 0:
                enemy.pos += to_enemy.normalize() * knockback_force

    def attack_war_hammer(self, enemies, aim_direction=None):
        """Heavy slam with small AoE. Deals high damage and stuns enemies in a radius."""
        current_time = pygame.time.get_ticks()
        if not self.can_attack(current_time):
            return

        self.start_attack(current_time, show_slash=True)

        if aim_direction is None:
            aim_direction = self.get_forward_direction()
        aim_dir = pygame.Vector2(aim_direction)
        if aim_dir.length_squared() == 0:
            aim_dir = pygame.Vector2(1, 0)
        aim_dir = aim_dir.normalize()
        self.last_attack_dir = pygame.Vector2(aim_dir)

        origin = self.get_melee_anchor()
        impact_point = origin + aim_dir * self.attack_range
        blast_radius = 50.0
        blast_radius_sq = blast_radius * blast_radius
        knockback_force = 45

        for enemy in enemies:
            enemy_rect = enemy.get_rect()
            enemy_center = pygame.Vector2(enemy_rect.centerx, enemy_rect.centery)
            to_impact = enemy_center - impact_point
            dist_sq = to_impact.length_squared()
            if dist_sq > blast_radius_sq:
                continue

            logger.info(f"War Hammer crushed enemy for {self.attack_damage} damage!")
            final_damage = self.get_effective_attack_damage()
            enemy.take_damage(final_damage)
            self._apply_weapon_enchantments(enemy)

            if self.poison_blade:
                enemy.add_effect(PoisonEffect(self.poison_blade_duration, self.poison_blade_damage_per_sec))

            from database.effects import DizzinessEffect
            if hasattr(enemy, "add_effect"):
                enemy.add_effect(DizzinessEffect(duration=2.0))

            knock_dir = to_impact.normalize() if dist_sq > 0 else pygame.Vector2(aim_dir)
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

        # Update Mystic Barrier active timer
        if self.mystic_barrier_active:
            self.mystic_barrier_active_time -= dt
            if self.mystic_barrier_active_time <= 0:
                self.mystic_barrier_active = False
                self.mystic_barrier_active_time = 0.0
                self.mystic_barrier_particles.clear()
                logger.info("Mystic Barrier expired.")
            else:
                self._update_mystic_barrier_particles(dt)

        # Update Berserker's Rage active timer
        if self.berserkers_rage_active:
            self.berserkers_rage_active_time -= dt
            if self.berserkers_rage_active_time <= 0:
                self.berserkers_rage_active = False
                self.berserkers_rage_active_time = 0.0
                logger.info("Berserker's Rage faded.")
                self.berserkers_rage_particles.clear()
            else:
                self._update_berserkers_rage_particles(dt)

        # Update Chrono Shift active timer
        if self.chrono_shift_active:
            self.chrono_shift_active_time -= dt
            if self.chrono_shift_active_time <= 0:
                self.chrono_shift_active = False
                self.chrono_shift_active_time = 0.0
                self.chrono_shift_particles.clear()
                logger.info("Chrono Shift ended.")
            else:
                self._update_chrono_shift_particles(dt)

        # Update Soul Harvest stacks
        if self.soul_harvest and self.soul_harvest_stacks:
            self.soul_harvest_stacks = [t - dt for t in self.soul_harvest_stacks if t - dt > 0]

        # Update floating texts
        self._update_floating_texts(dt)

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

        # Void Walker: dodge chance
        if self.void_walker and amount > 0 and not ignore_invulnerability:
            import random
            if random.random() < self.void_walker_dodge_chance:
                old_center = self.get_center()
                # Teleport in a random direction
                angle = random.uniform(0, math.pi * 2)
                offset = pygame.Vector2(math.cos(angle), math.sin(angle)) * self.void_walker_teleport_range
                self.pos += offset
                # Spawn afterimage at old center position
                game_state = getattr(self, "game_state", None)
                if game_state is not None and hasattr(game_state, "projectiles"):
                    from src.entities.projectile import Afterimage
                    game_state.projectiles.append(
                        Afterimage(old_center, self.void_walker_afterimage_damage)
                    )
                # Floating "Dodged" text at the old position
                self.add_floating_text("Dodged!", old_center.x, old_center.y - 30, (120, 255, 120), 1.2, 24)
                logger.info("Void Walker dodged an attack!")
                return

        # Ice Armor absorbs damage
        if self.ice_armor_active and self.ice_armor_remaining_absorption > 0 and amount > 0:
            absorbed = min(self.ice_armor_remaining_absorption, float(amount))
            self.ice_armor_remaining_absorption -= absorbed
            amount -= int(absorbed)
            logger.info(f"Ice Armor absorbed {int(absorbed)} damage. Remaining: {int(self.ice_armor_remaining_absorption)}")
            if amount <= 0:
                return

        # Berserker's Rage: take 20% more damage
        if self.berserkers_rage_active and amount > 0:
            amount = int(amount * 1.2)

        # Eternal Fortress: 80% defense = 20% damage reduction
        if self.eternal_fortress and amount > 0:
            amount = int(amount * 0.8)
            if amount < 1:
                amount = 1

        # Mystic Barrier: reflect 30% of damage to all nearby enemies
        if self.mystic_barrier_active and amount > 0:
            reflect_damage = int(amount * self.mystic_barrier_reflect_pct)
            if reflect_damage > 0:
                game_state = getattr(self, "game_state", None)
                if game_state is not None and hasattr(game_state, "enemies"):
                    player_center = self.get_center()
                    reflect_radius = 200.0
                    for enemy in list(game_state.enemies):
                        enemy_center = enemy.get_center()
                        if player_center.distance_to(enemy_center) < reflect_radius:
                            enemy.take_damage(reflect_damage)
                            logger.info(f"Mystic Barrier reflected {reflect_damage} damage to {enemy.__class__.__name__}!")

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

        # Apply armor / defense reduction first
        defense = getattr(self, "defense", 0)
        if defense > 0 and not ignore_invulnerability:
            reduction = min(defense, int(amount * 0.6))
            amount = max(0, amount - reduction)
            self.defense = max(0, self.defense - reduction // 2)
            if amount == 0:
                logger.debug(f"Player attack fully absorbed by armor ({defense} def).")
                return

        # Shield absorbs next, before HP is touched
        shield = getattr(self, "shield", 0.0)
        if shield > 0.0 and not ignore_invulnerability:
            if amount <= shield:
                self.shield = shield - amount
                logger.debug(f"Player shield absorbed {amount} damage. Remaining shield: {self.shield:.1f}")
                return
            else:
                amount -= shield
                self.shield = 0.0
                logger.debug(f"Player shield depleted, remaining {amount} damage taken.")

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
        
        # Draw attack visual based on equipped weapon's combat style — wind-swoosh effects
        if self.is_attacking:
            attack_dir = pygame.Vector2(self.last_attack_dir)
            if attack_dir.length_squared() == 0:
                attack_dir = self.get_forward_direction()
            if attack_dir.length_squared() == 0:
                attack_dir = pygame.Vector2(1, 0)
            else:
                attack_dir = attack_dir.normalize()

            weapon = getattr(self, "equipped_weapon", None)
            combat_style = getattr(weapon, "combat_style", "sword") if weapon else "sword"

            now = pygame.time.get_ticks()
            elapsed = now - self.last_attack_time
            duration = 200
            p = min(elapsed / duration, 1.0)

            base_anchor = self.get_melee_anchor() + attack_dir * self.melee_origin_offset
            to_screen = lambda v: (int(v.x - camera_offset.x), int(v.y - camera_offset.y))
            anchor_s = to_screen(base_anchor)

            def swoosh(center, angle_deg, arc_total, radius, color, width, alpha, layers=3):
                surf_size = int(radius * 2 + 20)
                for layer in range(layers):
                    lf = 1.0 - layer * 0.25
                    r = radius * (1.0 - layer * 0.12)
                    w = max(1, int(width * lf * (layers - layer) / layers))
                    a = int(alpha * lf)
                    if a <= 0:
                        continue
                    s = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
                    half = arc_total * 0.5 * (1.0 - layer * 0.08)
                    off = layer * 4 - layers * 2
                    pygame.draw.arc(s, (*color, a),
                                    pygame.Rect(surf_size // 2 - r, surf_size // 2 - r, r * 2, r * 2),
                                    math.radians(270 - half + off), math.radians(270 + half + off), w)
                    rot = pygame.transform.rotate(s, angle_deg)
                    cr = rot.get_rect(center=center)
                    screen.blit(rot, cr.topleft)

            def gust_line(start, end, color, alpha, width):
                pygame.draw.line(screen, (*color, max(0, min(255, alpha))), start, end, max(1, width))

            def dot(center, color, alpha, radius):
                pygame.draw.circle(screen, (*color, max(0, min(255, alpha))), center, max(1, radius))

            if combat_style == "sword":
                base_angle = -math.degrees(math.atan2(attack_dir.y, attack_dir.x))

                swing_total = 140
                start_offset = 65
                current_angle = base_angle - 90 + start_offset - swing_total * p

                fade = 1.0 - p * 0.45
                alpha = int(180 * fade)
                arc_radius = 60 + 10 * p
                arc_current = swing_total * p

                # ── Crescent slash trail (procedural, no sprite) ──
                # Dark outer glow
                swoosh(anchor_s, base_angle - 270, arc_current, arc_radius + 16, (70, 80, 140), 10, alpha // 5, 2)
                # Mid glow
                swoosh(anchor_s, base_angle - 270, arc_current, arc_radius + 8, (110, 140, 210), 7, alpha // 3, 2)
                # Main crescent body (light)
                swoosh(anchor_s, base_angle - 270, arc_current, arc_radius, (180, 210, 255), 5, alpha, 3)
                # Bright inner core
                swoosh(anchor_s, base_angle - 270, arc_current * 0.7, arc_radius * 0.8, (220, 235, 255), 3, alpha, 2)
                # Hot cutting edge
                swoosh(anchor_s, base_angle - 270, arc_current * 0.4, arc_radius * 0.6, (255, 255, 255), 2, int(alpha * 0.8), 1)

                # Bright tip flare at the blade edge
                tip_angle = base_angle + arc_current * 0.5
                tip_dir = pygame.Vector2(1, 0).rotate(-tip_angle)
                tip_pos = base_anchor + tip_dir * (arc_radius + 5)
                dot(to_screen(tip_pos), (255, 255, 255), int(220 * (1 - p * 0.5)), 3 + int(5 * (1 - p)))

                # Particles scattered along the arc
                for i in range(8):
                    lp = (p - i * 0.09) / 0.8
                    if lp < 0 or lp > 1:
                        continue
                    dot_angle = base_angle - arc_current * 0.5 + lp * arc_current
                    d = pygame.Vector2(1, 0).rotate(-dot_angle)
                    pos = base_anchor + d * (30 + 40 * lp)
                    c = (160, 200, 255)
                    dot(to_screen(pos), c, int(100 * (1 - lp) * fade), 1 + int(3 * (1 - lp)))

            elif combat_style == "mace":
                ip = base_anchor + attack_dir * (self.attack_range * min(1.0, p * 1.5))
                ip_s = to_screen(ip)
                fade = max(0, 1.0 - p * 1.0)
                r = 20 + p * 50
                pygame.draw.circle(screen, (200, 210, 255, int(80 * fade)), ip_s, int(r), max(1, int(4 - p * 2)))
                pygame.draw.circle(screen, (180, 190, 255, int(40 * fade)), ip_s, int(r * 0.7), 1)
                for i in range(10):
                    a = math.radians(i * 36 + elapsed * 0.2)
                    length = 15 + p * 45 * (0.4 + 0.6 * abs(math.sin(a)))
                    end = (ip_s[0] + math.cos(a) * length, ip_s[1] + math.sin(a) * length)
                    gust_line(ip_s, end, (200, 215, 255), int(70 * fade * (0.3 + 0.7 * (1 - abs(math.sin(a))))), max(1, int(3 - p * 1.5)))
                for i in range(6):
                    lp = (p - i * 0.08) / 0.6
                    if lp < 0 or lp > 1:
                        continue
                    a = math.radians(i * 60 + elapsed * 0.5)
                    pos = ip + pygame.Vector2(math.cos(a), math.sin(a)) * (10 + lp * 40)
                    dot(to_screen(pos), (220, 230, 255), int(100 * (1 - lp) * fade), 2 + int(3 * (1 - lp)))

            elif combat_style == "axe":
                cx, cy = anchor_s

                # Slower spin (350ms duration vs default 200ms)
                p_axe = min(elapsed / 350.0, 1.0)

                sweep_start = 0
                sweep = 360 * p_axe
                fade = max(0, 1.0 - p_axe * 0.5)
                base_a = math.degrees(math.atan2(attack_dir.y, attack_dir.x))
                r = 60 + 15 * math.sin(p_axe * math.pi)

                # Gray metallic arc layers (spinning sweep trail)
                for layer in range(3):
                    lf = 1.0 - layer * 0.2
                    lr = r * (1.0 - layer * 0.08)
                    a_start = math.radians(base_a + sweep_start - layer * 6)
                    a_end = math.radians(base_a + sweep_start + sweep + layer * 6)
                    w = max(1, int(6 * lf))
                    c = int(140 + 40 * lf)
                    surf = pygame.Surface((int(lr * 2 + 30), int(lr * 2 + 30)), pygame.SRCALPHA)
                    pygame.draw.arc(surf, (c, c, c + 10, int(90 * fade * lf)),
                                    pygame.Rect(15, 15, lr * 2, lr * 2), a_start, a_end, w)
                    screen.blit(surf, (cx - lr - 15, cy - lr - 15),
                                special_flags=pygame.BLEND_ALPHA_SDL2)

                # Spinning stick (shaft) connecting two blades
                cur_a = base_a + sweep_start + sweep
                stick_angle = cur_a
                for side in range(2):
                    tip_offset = pygame.Vector2(1, 0).rotate(-(stick_angle + side * 180)) * r * 0.425
                    sx = cx + int(tip_offset.x)
                    sy = cy + int(tip_offset.y)
                    gust_line((cx, cy), (sx, sy), (150, 140, 130), int(180 * fade), max(1, int(4 - p_axe * 2)))

                # Labrys double-bladed axe head at the end of the stick
                ba = stick_angle
                tip_offset = pygame.Vector2(1, 0).rotate(-ba) * r * 0.425
                hx = cx + int(tip_offset.x)
                hy = cy + int(tip_offset.y)
                fwd = pygame.Vector2(1, 0).rotate(-ba)
                perp = pygame.Vector2(1, 0).rotate(-(ba + 90))
                blade_len = max(4, int(r * 0.35))
                blade_wid = max(2, int(r * 0.14))
                neck = max(1, int(r * 0.04))
                for sign in (-1, 1):
                    outer_top = (hx + int(perp.x * blade_len * sign + fwd.x * blade_wid),
                                 hy + int(perp.y * blade_len * sign + fwd.y * blade_wid))
                    outer_mid = (hx + int(perp.x * blade_len * sign * 0.95),
                                 hy + int(perp.y * blade_len * sign * 0.95))
                    outer_bot = (hx + int(perp.x * blade_len * sign - fwd.x * blade_wid),
                                 hy + int(perp.y * blade_len * sign - fwd.y * blade_wid))
                    inner_top = (hx + int(perp.x * neck * sign + fwd.x * blade_wid * 0.3),
                                 hy + int(perp.y * neck * sign + fwd.y * blade_wid * 0.3))
                    inner_bot = (hx + int(perp.x * neck * sign - fwd.x * blade_wid * 0.3),
                                 hy + int(perp.y * neck * sign - fwd.y * blade_wid * 0.3))
                    pts = [outer_top, outer_mid, outer_bot, inner_bot, inner_top]
                    if len(pts) >= 3:
                        pygame.draw.polygon(screen, (180, 180, 190, int(150 * fade)), pts, 0)
                        pygame.draw.polygon(screen, (210, 210, 220, int(200 * fade)), pts, max(1, int(2 - p_axe)))

            elif combat_style == "spear":
                thrust_p = p * 1.3
                if thrust_p < 0.2:
                    thrust = self.attack_range * (thrust_p / 0.2)
                elif thrust_p < 0.8:
                    thrust = self.attack_range + (thrust_p - 0.2) / 0.6 * 10
                else:
                    thrust = (self.attack_range + 10) * max(0, 1.0 - (thrust_p - 0.8) / 0.5)
                tip = base_anchor + attack_dir * max(5, thrust)
                tip_s = to_screen(tip)
                fade = max(0.0, min(1.0, 1.0 - (p - 0.3) * 1.4))
                shaft_color = (130, 130, 135)
                shaft_alpha = int(180 * fade)
                shaft_width = max(2, int(5 - p * 2))
                shaft_end = tip - attack_dir * 10
                gust_line(anchor_s, to_screen(shaft_end), shaft_color, shaft_alpha, shaft_width)
                perp = pygame.Vector2(-attack_dir.y, attack_dir.x)
                head_width = 8
                head_len = 14
                base_p1 = tip - attack_dir * head_len + perp * head_width
                base_p2 = tip - attack_dir * head_len - perp * head_width
                head_pts = [tip_s, to_screen(base_p1), to_screen(base_p2)]
                if len(head_pts) >= 3:
                    pygame.draw.polygon(screen, (160, 160, 165, int(200 * fade)), head_pts, 0)
                    pygame.draw.polygon(screen, (180, 180, 185, int(220 * fade)), head_pts, 2)

            elif combat_style == "dagger":
                for idx, side in enumerate((-1, 1)):
                    local_p = (p - idx * 0.35) / 0.65
                    if local_p < 0 or local_p > 1:
                        continue
                    lfade = 1.0 - local_p * 0.5
                    base_color = (230, 230, 255)
                    d = attack_dir.rotate(side * (15 + 25 * local_p))
                    mid = base_anchor + d * (30 + 40 * local_p)
                    mid_s = to_screen(mid)
                    gust_line(anchor_s, mid_s, base_color, int(160 * lfade), max(1, int(4 - local_p * 2)))
                    for j in range(3):
                        jitter = d.rotate(side * (5 + j * 8) * (1 - local_p * 0.5))
                        jp = base_anchor + jitter * (20 + 50 * local_p)
                        gust_line(anchor_s, to_screen(jp), (base_color[0], base_color[1], base_color[2]),
                                  int(60 * lfade * 1 - j * 0.25), 1)
                    dot(mid_s, (255, 255, 255), int(120 * lfade), 2)

            elif combat_style == "war_hammer":
                if p < 0.25:
                    windup = p / 0.25
                    fade = 1.0 - windup * 0.3
                    swing_dir = attack_dir.rotate(-40 + 80 * windup)
                    tip = base_anchor + swing_dir * (self.attack_range * 0.5 * windup)
                    tip_s = to_screen(tip)
                    gust_line(anchor_s, tip_s, (255, 195, 195), int(100 * windup), max(1, int(4 + windup * 4)))
                    for i in range(3):
                        d = swing_dir.rotate(-20 + 40 * (i / 2))
                        pos = base_anchor + d * (20 + 40 * windup)
                        dot(to_screen(pos), (255, 210, 210), int(80 * windup * (1 - i * 0.25)), 2 + int(3 * windup))
                else:
                    impact_p = (p - 0.25) / 0.75
                    impact_point = base_anchor + attack_dir * self.attack_range
                    ip_s = to_screen(impact_point)
                    fade = max(0, 1.0 - impact_p * 0.9)
                    r = 15 + impact_p * 55
                    pygame.draw.circle(screen, (255, 185, 185, int(100 * fade)), ip_s, int(r), max(1, int(5 - impact_p * 3)))
                    pygame.draw.circle(screen, (255, 155, 155, int(60 * fade)), ip_s, int(r * 0.6), 1)
                    for i in range(8):
                        a = math.radians(i * 45 + impact_p * 20)
                        length = 10 + impact_p * 50 * (0.5 + 0.5 * abs(math.cos(a)))
                        end = (ip_s[0] + math.cos(a) * length, ip_s[1] + math.sin(a) * length)
                        gust_line(ip_s, end, (255, 175, 175), int(80 * fade * (0.4 + 0.6 * (1 - abs(math.sin(a))))),
                                  max(1, int(3 - impact_p * 2)))
                    for i in range(5):
                        lp = (impact_p - i * 0.08) / 0.5
                        if lp < 0 or lp > 1:
                            continue
                        a = math.radians(i * 72 + impact_p * 40)
                        pos = impact_point + pygame.Vector2(math.cos(a), math.sin(a)) * (8 + lp * 35)
                        dot(to_screen(pos), (255, 210, 210), int(90 * (1 - lp) * fade), 2 + int(4 * (1 - lp)))

            else:
                base_angle = -math.degrees(math.atan2(attack_dir.y, attack_dir.x))
                sweep = 100 * p
                fade = 1.0 - p * 0.45
                alpha = int(180 * fade)
                swoosh(anchor_s, base_angle, sweep, 70 + 10 * p, (220, 220, 255), 4, alpha, 3)
                swoosh(anchor_s, base_angle, sweep * 0.7, 55 + 8 * p, (200, 200, 255), 6, int(alpha * 0.6), 2)
                for i in range(4):
                    lp = (p - i * 0.15) / 0.7
                    if lp < 0 or lp > 1:
                        continue
                    spread = 20 + 35 * lp
                    d = attack_dir.rotate(-20 + 40 * lp + i * 18)
                    pos = base_anchor + d * (45 + 30 * lp)
                    dot(to_screen(pos), (255, 255, 255), int(120 * (1 - lp) * fade), 2 + int(3 * (1 - lp)))

        # Draw Flame Shield visual effect
        if self.flame_shield_active:
            self._draw_flame_shield(screen, camera_offset)

        # Draw Ice Armor visual effect
        if self.ice_armor_active:
            self._draw_ice_armor(screen, camera_offset)

        # Draw Mystic Barrier visual effect
        if self.mystic_barrier_active:
            self._draw_mystic_barrier(screen, camera_offset)

        # Draw Chrono Shift visual effect
        if self.chrono_shift_active:
            self._draw_chrono_shift(screen, camera_offset)

        # Draw Berserker's Rage visual effect
        if self.berserkers_rage_active:
            self._draw_berserkers_rage(screen, camera_offset)

        # Draw floating texts
        self._draw_floating_texts(screen, camera_offset)

    # ─── Floating text helpers ─────────────────────────────────────────

    def add_floating_text(self, text, x, y, color=(255, 255, 255), duration=1.5, size=20):
        self.floating_texts.append({
            "text": text,
            "x": x,
            "y": y,
            "color": color,
            "life": duration,
            "max_life": duration,
            "speed_y": -40,
            "size": size,
        })

    def _update_floating_texts(self, dt):
        for ft in self.floating_texts[:]:
            ft["life"] -= dt
            ft["y"] += ft["speed_y"] * dt
            if ft["life"] <= 0:
                self.floating_texts.remove(ft)

    def _draw_floating_texts(self, screen, camera_offset):
        for ft in self.floating_texts:
            life_ratio = ft["life"] / ft["max_life"] if ft["max_life"] > 0 else 0
            if life_ratio <= 0:
                continue
            alpha = int(255 * life_ratio)
            sx = int(ft["x"] - camera_offset.x)
            sy = int(ft["y"] - camera_offset.y)
            font = pygame.font.Font(None, ft["size"])
            text_surf = font.render(ft["text"], True, ft["color"])
            text_surf.set_alpha(alpha)
            text_rect = text_surf.get_rect(center=(sx, sy))
            # Shadow
            shadow_surf = font.render(ft["text"], True, (0, 0, 0))
            shadow_surf.set_alpha(alpha // 2)
            screen.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
            screen.blit(text_surf, text_rect)

    # ─── Berserker's Rage helpers ─────────────────────────────────────

    def _update_berserkers_rage_particles(self, dt):
        import random
        if self.berserkers_rage_active:
            spawn_count = max(1, int(30 * dt))
            for _ in range(spawn_count):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(10, 80)
                self.berserkers_rage_particles.append({
                    "angle": angle,
                    "dist": dist,
                    "life": random.uniform(0.2, 0.6),
                    "max_life": random.uniform(0.2, 0.6),
                    "size": random.uniform(2.0, 5.0),
                    "drift": random.uniform(30, 90),
                    "color": random.choice([
                        (255, 60, 20),
                        (255, 120, 30),
                        (255, 200, 50),
                        (200, 40, 10),
                    ]),
                })
        for p in self.berserkers_rage_particles[:]:
            p["life"] -= dt
            if p["life"] <= 0:
                self.berserkers_rage_particles.remove(p)
                continue
            p["dist"] += p["drift"] * dt
            p["angle"] += 1.5 * dt

    def _draw_berserkers_rage(self, screen, camera_offset):
        import random
        center = self.get_center()
        cx = center.x - camera_offset.x
        cy = center.y - camera_offset.y
        t = pygame.time.get_ticks() / 1000.0

        pulse = 0.5 + 0.5 * math.sin(t * 6.0)
        radius = 70.0

        # ── Outer rage aura ──
        aura_radius = radius * (0.9 + 0.15 * pulse)
        aura_surf = pygame.Surface((int(aura_radius * 2) + 4, int(aura_radius * 2) + 4), pygame.SRCALPHA)
        aura_a = int(40 + 30 * pulse)
        pygame.draw.circle(aura_surf, (220, 50, 20, aura_a),
                           (int(aura_radius) + 2, int(aura_radius) + 2),
                           int(aura_radius))
        inner_a = int(30 + 20 * pulse)
        pygame.draw.circle(aura_surf, (255, 100, 30, inner_a),
                           (int(aura_radius) + 2, int(aura_radius) + 2),
                           int(aura_radius * 0.6))
        screen.blit(aura_surf, (int(cx - aura_radius - 2), int(cy - aura_radius - 2)))

        # ── Rage ring ──
        ring_r = radius * 0.8
        ring_a = int(80 + 50 * math.sin(t * 9.0))
        ring_surf = pygame.Surface((int(ring_r * 2) + 4, int(ring_r * 2) + 4), pygame.SRCALPHA)
        for i in range(3):
            r = int(ring_r * (0.85 + 0.05 * (i + 1)))
            offset_phase = t * 4.0 + i * 1.0
            rr = r * (0.98 + 0.04 * math.sin(offset_phase))
            pygame.draw.circle(ring_surf,
                               (200, 60 + i * 30, 10 + i * 10, ring_a // (i + 1)),
                               (int(ring_r) + 2, int(ring_r) + 2), int(rr),
                               max(1, 3 - i))
        screen.blit(ring_surf, (int(cx - ring_r - 2), int(cy - ring_r - 2)))

        # ── Rage spikes ──
        spike_count = 8
        for i in range(spike_count):
            spike_angle = t * 2.5 + i * (math.pi * 2 / spike_count)
            spike_len = 18 + 12 * math.sin(t * 7.0 + i * 2.0)
            inner_dist = radius * 0.75 + 8 * math.sin(t * 5.0 + i * 1.5)
            sx1 = cx + math.cos(spike_angle) * inner_dist
            sy1 = cy + math.sin(spike_angle) * inner_dist
            sx2 = cx + math.cos(spike_angle) * (inner_dist + spike_len)
            sy2 = cy + math.sin(spike_angle) * (inner_dist + spike_len)
            spike_alpha = int(140 + 80 * math.sin(t * 8.0 + i * 1.7))
            pygame.draw.line(screen, (220, 80 + i * 12, 10 + i * 5, spike_alpha),
                             (sx1, sy1), (sx2, sy2),
                             max(1, int(3 + 2 * math.sin(t * 4.0 + i))))

        # ── Rage particles ──
        for p in self.berserkers_rage_particles:
            life_ratio = p["life"] / p["max_life"] if p["max_life"] > 0 else 0
            if life_ratio <= 0:
                continue
            px = cx + math.cos(p["angle"]) * p["dist"]
            py = cy + math.sin(p["angle"]) * p["dist"]
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

        # ── Rising sparkles ──
        if self.berserkers_rage_active:
            for _ in range(3):
                sp_angle = random.uniform(0, math.pi * 2)
                sp_dist = random.uniform(0, radius * 0.4)
                sp_x = cx + math.cos(sp_angle) * sp_dist
                sp_y = cy + random.uniform(-25, 0)
                sp_size = random.randint(1, 2)
                sp_color = random.choice([(255, 200, 80), (255, 140, 40), (255, 255, 120)])
                pygame.draw.circle(screen, sp_color, (int(sp_x), int(sp_y)), sp_size)

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

    # ─── Mystic Barrier helpers ──────────────────────────────────────

    def _update_mystic_barrier_particles(self, dt):
        import random

        if self.mystic_barrier_active:
            spawn_count = max(1, int(12 * dt))
            for _ in range(spawn_count):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(30, 100)
                self.mystic_barrier_particles.append({
                    "angle": angle,
                    "dist": dist,
                    "life": random.uniform(0.3, 0.7),
                    "max_life": random.uniform(0.3, 0.7),
                    "size": random.uniform(2.0, 4.0),
                    "drift": random.uniform(-20, 20),
                    "color": random.choice([
                        (200, 140, 255),
                        (160, 80, 220),
                        (220, 180, 255),
                        (180, 100, 240),
                        (240, 200, 255),
                    ]),
                })

        for p in self.mystic_barrier_particles[:]:
            p["life"] -= dt
            if p["life"] <= 0:
                self.mystic_barrier_particles.remove(p)
                continue
            p["angle"] += p["drift"] * dt
            pulse = 1.0 + 0.3 * math.sin(p["life"] * 8.0)
            p["dist"] *= pulse

    def _draw_mystic_barrier(self, screen, camera_offset):
        import random
        center = self.get_center()
        cx = center.x - camera_offset.x
        cy = center.y - camera_offset.y
        t = pygame.time.get_ticks() / 1000.0

        radius = 85.0

        # ── Outer magenta barrier ring ──
        pulse = 0.6 + 0.4 * math.sin(t * 3.5)
        glow_radius = radius * (0.9 + 0.1 * pulse)
        glow_surf = pygame.Surface((int(glow_radius * 2) + 4, int(glow_radius * 2) + 4), pygame.SRCALPHA)
        glow_a = int(40 + 25 * pulse)
        pygame.draw.circle(glow_surf, (140, 60, 180, glow_a),
                           (int(glow_radius) + 2, int(glow_radius) + 2),
                           int(glow_radius))
        inner_r = int(glow_radius * 0.55)
        inner_a = int(25 + 20 * pulse)
        pygame.draw.circle(glow_surf, (200, 120, 240, inner_a),
                           (int(glow_radius) + 2, int(glow_radius) + 2),
                           inner_r)
        screen.blit(glow_surf, (int(cx - glow_radius - 2), int(cy - glow_radius - 2)))

        # ── Arcane rune ring ──
        ring_r = radius
        ring_a = int(80 + 60 * math.sin(t * 6.0))
        ring_surf = pygame.Surface((int(ring_r * 2) + 4, int(ring_r * 2) + 4), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (200, 140, 255, ring_a),
                           (int(ring_r) + 2, int(ring_r) + 2),
                           int(ring_r), max(1, int(2 * (0.5 + 0.5 * pulse))))
        screen.blit(ring_surf, (int(cx - ring_r - 2), int(cy - ring_r - 2)))

        # ── Rotating energy sigils ──
        sigil_count = 4
        for i in range(sigil_count):
            sigil_angle = t * 0.8 + i * (math.pi * 2 / sigil_count)
            sigil_dist = radius * 0.75 + 8 * math.sin(t * 4.0 + i * 1.2)
            sx = cx + math.cos(sigil_angle) * sigil_dist
            sy = cy + math.sin(sigil_angle) * sigil_dist
            sigil_size = max(2, int(5 + 3 * math.sin(t * 3.0 + i * 1.7)))
            sigil_alpha = int(120 + 80 * math.sin(t * 5.0 + i * 2.3))
            sigil_color = (220, 160, 255, sigil_alpha)
            pts = [
                (sx, sy - sigil_size),
                (sx + sigil_size * 0.7, sy),
                (sx, sy + sigil_size),
                (sx - sigil_size * 0.7, sy),
            ]
            pygame.draw.polygon(screen, sigil_color[:3], pts)
            pygame.draw.polygon(screen, (240, 210, 255), pts, 1)

        # ── Barrier particles ──
        for p in self.mystic_barrier_particles:
            life_ratio = p["life"] / p["max_life"] if p["max_life"] > 0 else 0
            if life_ratio <= 0:
                continue
            px = cx + math.cos(p["angle"]) * p["dist"]
            py = cy + math.sin(p["angle"]) * p["dist"]
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

        # ── Arcane sparkles ──
        if self.mystic_barrier_active:
            for _ in range(3):
                sp_angle = random.uniform(0, math.pi * 2)
                sp_dist = random.uniform(0, radius * 0.5)
                sp_x = cx + math.cos(sp_angle) * sp_dist
                sp_y = cy + random.uniform(-10, 10)
                sp_size = random.randint(1, 2)
                sp_color = random.choice([(220, 180, 255), (180, 120, 240), (255, 220, 255)])
                pygame.draw.circle(screen, sp_color, (int(sp_x), int(sp_y)), sp_size)

    # ─── Chrono Shift helpers ─────────────────────────────────────────

    def _update_chrono_shift_particles(self, dt):
        import random
        if self.chrono_shift_active:
            spawn_count = max(1, int(20 * dt))
            for _ in range(spawn_count):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(15, 70)
                self.chrono_shift_particles.append({
                    "angle": angle,
                    "dist": dist,
                    "life": random.uniform(0.15, 0.4),
                    "max_life": random.uniform(0.15, 0.4),
                    "size": random.uniform(1.5, 3.5),
                    "drift": random.uniform(-40, -10),
                    "color": random.choice([
                        (180, 220, 255),
                        (140, 200, 240),
                        (200, 235, 255),
                        (160, 210, 250),
                    ]),
                })
        for p in self.chrono_shift_particles[:]:
            p["life"] -= dt
            if p["life"] <= 0:
                self.chrono_shift_particles.remove(p)
                continue
            p["angle"] += p["drift"] * dt * 0.3
            p["dist"] += 20 * dt

    def _draw_chrono_shift(self, screen, camera_offset):
        import random
        center = self.get_center()
        cx = center.x - camera_offset.x
        cy = center.y - camera_offset.y
        t = pygame.time.get_ticks() / 1000.0

        radius = 90.0

        # ── Outer time distortion ring ──
        pulse = 0.5 + 0.5 * math.sin(t * 5.0)
        glow_radius = radius * (0.85 + 0.15 * pulse)
        glow_surf = pygame.Surface((int(glow_radius * 2) + 4, int(glow_radius * 2) + 4), pygame.SRCALPHA)
        glow_a = int(30 + 20 * pulse)
        pygame.draw.circle(glow_surf, (80, 160, 220, glow_a),
                           (int(glow_radius) + 2, int(glow_radius) + 2),
                           int(glow_radius))
        inner_r = int(glow_radius * 0.5)
        inner_a = int(20 + 15 * pulse)
        pygame.draw.circle(glow_surf, (140, 210, 255, inner_a),
                           (int(glow_radius) + 2, int(glow_radius) + 2),
                           inner_r)
        screen.blit(glow_surf, (int(cx - glow_radius - 2), int(cy - glow_radius - 2)))

        # ── Rotating clock hand ring ──
        ring_r = radius
        ring_a = int(60 + 40 * math.sin(t * 8.0))
        ring_surf = pygame.Surface((int(ring_r * 2) + 4, int(ring_r * 2) + 4), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (160, 210, 255, ring_a),
                           (int(ring_r) + 2, int(ring_r) + 2),
                           int(ring_r), max(1, int(2 * (0.5 + 0.5 * pulse))))
        screen.blit(ring_surf, (int(cx - ring_r - 2), int(cy - ring_r - 2)))

        # ── Clock ticks ──
        tick_count = 12
        for i in range(tick_count):
            tick_angle = t * 0.6 + i * (math.pi * 2 / tick_count)
            tick_dist = radius * 0.85
            tx = cx + math.cos(tick_angle) * tick_dist
            ty = cy + math.sin(tick_angle) * tick_dist
            tick_len = 4 + 3 * math.sin(t * 4.0 + i)
            tick_alpha = int(100 + 80 * math.sin(t * 6.0 + i * 1.3))
            pygame.draw.line(screen, (160, 210, 255, tick_alpha),
                             (tx - math.cos(tick_angle) * tick_len,
                              ty - math.sin(tick_angle) * tick_len),
                             (tx + math.cos(tick_angle) * tick_len,
                              ty + math.sin(tick_angle) * tick_len), 2)

        # ── Clock hands ──
        hand_angle = t * 2.0
        for hand_len, hand_width, hand_color in [
            (radius * 0.5, 3, (180, 220, 255)),
            (radius * 0.7, 2, (140, 200, 240)),
        ]:
            hx = cx + math.cos(hand_angle) * hand_len
            hy = cy + math.sin(hand_angle) * hand_len
            pygame.draw.line(screen, hand_color, (cx, cy), (hx, hy), hand_width)

        # ── Time particles ──
        for p in self.chrono_shift_particles:
            life_ratio = p["life"] / p["max_life"] if p["max_life"] > 0 else 0
            if life_ratio <= 0:
                continue
            px = cx + math.cos(p["angle"]) * p["dist"]
            py = cy + math.sin(p["angle"]) * p["dist"]
            alpha = int(180 * life_ratio)
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

        # ── Time sparkles ──
        if self.chrono_shift_active:
            for _ in range(4):
                sp_angle = random.uniform(0, math.pi * 2)
                sp_dist = random.uniform(0, radius * 0.6)
                sp_x = cx + math.cos(sp_angle) * sp_dist
                sp_y = cy + random.uniform(-15, 15)
                sp_size = random.randint(1, 2)
                sp_color = random.choice([(200, 235, 255), (160, 210, 255), (220, 240, 255)])
                pygame.draw.circle(screen, sp_color, (int(sp_x), int(sp_y)), sp_size)
