import math
import random

import pygame
from database.effects import PoisonEffect
from src.core.logger import logger
from src.entities.projectile import Fireball, GlacialCascade, FrostNova, ChainLightning, Thunderstrike, EntanglingRoots, NatureBolt, DarkPact, ArcaneMissile
from src.entities.nature_spirit import NatureSpirit
from src.mana.mana_system import ManaSystem

class Character:
    """
    Represents the player character with animated movement, combat, skill system,
    resource management, and visual effects.

    Attributes grouped by category:

    --- Animations & Sprites ---
        sprite_set (str): Name of the character sprite set.
        animations (dict[str, list[pygame.Surface]]): Animation frames per direction.
        animations_flipped (dict[str, list[pygame.Surface]]): Horizontally flipped side frames.
        direction (str): Current direction ("up", "down", "side").
        image (pygame.Surface): Current animation frame to draw.
        frame_index (int): Current animation frame index.
        animation_speed (float): Frames per second for animation.
        time_accumulator (float): Accumulated time for frame switching.
        flip (bool): Whether to flip the sprite horizontally.
        moving (bool): Whether the character is currently in motion.

    --- Position & Movement ---
        pos (pygame.Vector2): World position.
        spawn_point (pygame.Vector2): Respawn point.
        rect (pygame.Rect): Collision/drawing rectangle.
        velocity (pygame.Vector2): Normalized movement direction.
        base_speed (float): Base movement speed in px/s.
        speed_multiplier (float): Multiplier applied to base speed.
        speed (float): Effective movement speed.
        sprint_multiplier (float): Speed multiplier while sprinting.
        is_sprinting (bool): Whether sprinting is active.
        can_sprint (bool): Whether the character can sprint.

    --- Health & Death ---
        max_hp (int): Maximum health points.
        hp (int): Current health points.
        death_count (int): Number of deaths.
        death_sound (pygame.mixer.Sound): Sound played on death.
        invulnerable (bool): Whether the character is temporarily invulnerable.
        invulnerability_timer (float): Elapsed invulnerability time.
        invulnerability_duration (float): Duration of invulnerability after hit.

    --- Resources ---
        max_stamina (int): Maximum stamina.
        stamina (int): Current stamina.
        stamina_drain_rate (int): Stamina drained per second while sprinting.
        stamina_regen_rate (int): Stamina regenerated per second.
        max_mana (int): Maximum mana.
        mana (int): Current mana.
        mana_drain_rate (float): Mana drained per second while casting.
        mana_regen_rate (float): Mana regenerated per second.
        energy (float): Alias for stamina for compatibility.

    --- Leveling & XP ---
        xp (int): Current experience points.
        level (int): Current level.
        xp_to_next_level (int): XP required for next level.

    --- Combat Stats ---
        base_attack_damage (int): Base melee damage.
        base_attack_range (int): Base melee range in pixels.
        base_attack_cooldown (int): Base melee cooldown in ms.
        attack_damage (int): Effective attack damage.
        attack_range (int): Effective attack range.
        attack_cooldown (int): Effective attack cooldown (modified by __getattribute__).
        attack_cooldown_mult (float): Cooldown multiplier (<1 = faster).
        last_attack_time (int): Timestamp of last attack.
        is_attacking (bool): Whether currently attacking.
        last_attack_dir (pygame.Vector2): Direction of last attack.
        melee_origin_offset (float): Offset from character center for melee origin.
        melee_slash_distance (float): Forward reach of melee attacks.
        damage_bonus (int): Flat bonus damage added to all attacks.
        cooldown_multiplier (float): Global skill cooldown multiplier.
        shield (float): Damage absorption before HP loss.
        defense (int): Flat damage reduction from armor.

    --- Skill System ---
        skillbook (list): Learned skills (dicts with skill_id, name, description, etc.).
        skillbar (list): 6-slot skill hotbar (skill dicts or None).
        skill_tree_points (int): Available skill tree points.
        skill_tree_unlocked (set): Unlocked skill tree node IDs.

    --- Status Effects ---
        effects (list): Active status effect instances.
        confused (bool): Whether movement is inverted.
        dizzy (bool): Whether the character is staggered.
        resistances (dict): Resistance values per effect name (0.0-1.0).
        floating_texts (list): Active damage/heal floating text popups.

    --- Passive / Keystone Attributes ---
        static_field (bool): Static Field passive active.
        static_field_proc_chance (float): Proc chance for Static Field.
        static_field_damage (int): Static Field damage.
        regeneration (bool): Regeneration passive active.
        regeneration_hp_per_sec (float): HP regenerated per second.
        regeneration_acc (float): Accumulator for regen tick.
        pyromancers_fury (bool): Pyromancer's Fury passive active.
        pyromancers_fury_damage_mult (float): Fire damage multiplier.
        pyromancers_fury_area_mult (float): Fire area multiplier.
        poison_blade (bool): Poison Blade passive active.
        poison_blade_damage_per_sec (float): Poison DPS.
        poison_blade_duration (float): Poison duration in seconds.
        mana_flow (bool): Mana Flow passive active.
        eternal_fortress (bool): Eternal Fortress keystone active.
        soul_harvest (bool): Soul Harvest keystone active.
        soul_harvest_stacks (list): Current Soul Harvest kill stacks.
        soul_harvest_duration (float): Stack duration.
        soul_harvest_hp_per_kill (int): HP restored per kill.
        soul_harvest_damage_per_stack (float): Damage bonus per stack.
        void_walker (bool): Void Walker keystone active.
        void_walker_dodge_chance (float): Dodge chance.
        void_walker_teleport_range (float): Teleport range.
        void_walker_afterimage_damage (int): Afterimage damage.
        elemental_mastery (bool): Elemental Mastery keystone active.
        elemental_damage_mult (float): Elemental damage multiplier.
        last_elemental_skill (str or None): ID of last used elemental skill.
        last_elemental_time (float): Timestamp of last elemental skill.
        combo_window (float): Window in seconds for element combo.
        elemental_damage_attrs (frozenset): Attribute names affected by elemental mastery.

    --- Skill Cooldowns & Config ---
        fireball_speed (float): Fireball projectile speed.
        fireball_range (float): Fireball max range.
        fireball_damage (int): Fireball damage.
        fireball_blast_radius (float): Fireball explosion radius.
        fireball_fuse_time (float): Fireball fuse duration.
        fireball_cooldown (int): Fireball cooldown in ms.
        fireball_last_used (int): Last fireball use timestamp.
        fireball_knockback (float): Fireball knockback force.
        game_state (object or None): Reference to game state.
        flame_shield_duration (float): Flame Shield active duration.
        flame_shield_cooldown (int): Flame Shield cooldown in ms.
        flame_shield_last_used (int): Last Flame Shield timestamp.
        flame_shield_active (bool): Whether Flame Shield is active.
        flame_shield_active_time (float): Remaining active time.
        flame_shield_damage_per_sec (float): Flame Shield DPS.
        flame_shield_radius (float): Flame Shield radius.
        flame_shield_particles (list): Flame Shield visual particles.
        flame_shield_damage_acc (float): Accumulated fractional damage.
        frost_nova_radius (float): Frost Nova radius.
        frost_nova_freeze_duration (float): Freeze duration.
        frost_nova_damage (int): Frost Nova damage.
        frost_nova_cooldown (int): Frost Nova cooldown.
        frost_nova_last_used (int): Last Frost Nova timestamp.
        ice_armor_duration (float): Ice Armor active duration.
        ice_armor_cooldown (int): Ice Armor cooldown.
        ice_armor_last_used (int): Last Ice Armor timestamp.
        ice_armor_active (bool): Whether Ice Armor is active.
        ice_armor_active_time (float): Remaining active time.
        ice_armor_remaining_absorption (float): Remaining damage absorption.
        ice_armor_max_absorption (float): Max absorption capacity.
        ice_armor_slow_radius (float): Slow aura radius.
        ice_armor_slow_factor (float): Slow movement multiplier.
        ice_armor_particles (list): Ice Armor visual particles.
        glacial_cascade_speed (float): Cascade projectile speed.
        glacial_cascade_range (float): Cascade max range.
        glacial_cascade_damage (int): Cascade damage.
        glacial_cascade_freeze_duration (float): Cascade freeze duration.
        glacial_cascade_cooldown (int): Cascade cooldown.
        glacial_cascade_last_used (int): Last Cascade timestamp.
        glacial_cascade_width (float): Cascade fan base width.
        chain_lightning_speed (float): Lightning bolt speed.
        chain_lightning_range (float): Lightning max range.
        chain_lightning_damage (int): Lightning damage per hit.
        chain_lightning_chain_range (float): Chain jump range.
        chain_lightning_max_targets (int): Max chain targets.
        chain_lightning_cooldown (int): Lightning cooldown.
        chain_lightning_last_used (int): Last Lightning timestamp.
        thunderstrike_damage (int): Thunderstrike damage.
        thunderstrike_radius (float): Thunderstrike radius.
        thunderstrike_range (float): Thunderstrike cast range.
        thunderstrike_cooldown (int): Thunderstrike cooldown.
        thunderstrike_last_used (int): Last Thunderstrike timestamp.
        entangling_roots_speed (float): Root projectile speed.
        entangling_roots_range (float): Root max range.
        entangling_roots_radius (float): Root burst radius.
        entangling_roots_root_duration (float): Root immobilize duration.
        entangling_roots_damage (int): Root burst damage.
        entangling_roots_cooldown (int): Roots cooldown.
        entangling_roots_last_used (int): Last Roots timestamp.
        summon_spirit_damage (int): Spirit attack damage.
        summon_spirit_duration (float): Spirit lifetime.
        summon_spirit_cooldown (int): Spirit summon cooldown.
        summon_spirit_last_used (int): Last summon timestamp.
        summon_spirit_particles (list): Summon visual particles.
        shadow_step_range (float): Shadow Step teleport range.
        shadow_step_cooldown (int): Shadow Step cooldown.
        shadow_step_last_used (int): Last Shadow Step timestamp.
        shadow_step_invuln_duration (float): Invulnerability after step.
        shadow_step_effect (object or None): Current shadow effect object.
        shadow_step_particles (list): Shadow Step visual particles.
        dark_pact_hp_cost_percent (float): HP cost as fraction of max HP.
        dark_pact_damage (int): Dark Pact damage.
        dark_pact_radius (float): Dark Pact radius.
        dark_pact_cooldown (int): Dark Pact cooldown.
        dark_pact_last_used (int): Last Dark Pact timestamp.
        arcane_missiles_speed (float): Missile speed.
        arcane_missiles_range (float): Missile max range.
        arcane_missiles_damage (int): Missile damage per bolt.
        arcane_missiles_count (int): Number of missiles per cast.
        arcane_missiles_cooldown (int): Missiles cooldown.
        arcane_missiles_last_used (int): Last Missiles timestamp.
        mystic_barrier_duration (float): Barrier active duration.
        mystic_barrier_cooldown (int): Barrier cooldown.
        mystic_barrier_last_used (int): Last Barrier timestamp.
        mystic_barrier_active (bool): Whether barrier is active.
        mystic_barrier_active_time (float): Remaining active time.
        mystic_barrier_reflect_pct (float): Damage reflect percentage.
        mystic_barrier_particles (list): Barrier visual particles.

    --- Keystone Skills ---
        berserkers_rage_active (bool): Whether Rage is active.
        berserkers_rage_duration (float): Rage duration.
        berserkers_rage_active_time (float): Remaining Rage time.
        berserkers_rage_cooldown (int): Rage cooldown.
        berserkers_rage_last_used (int): Last Rage timestamp.
        berserkers_rage_particles (list): Rage visual particles.
        chrono_shift_active (bool): Whether Chrono Shift is active.
        chrono_shift_duration (float): Chrono Shift duration.
        chrono_shift_active_time (float): Remaining active time.
        chrono_shift_cooldown (int): Chrono Shift cooldown.
        chrono_shift_last_used (int): Last Chrono Shift timestamp.
        chrono_shift_particles (list): Chrono Shift visual particles.

    --- Dash ---
        dash_speed_multiplier (float): Dash speed boost multiplier.
        dash_duration (float): Dash duration in seconds.
        dash_cooldown (int): Dash cooldown in ms.
        dash_active_time (float): Remaining dash time.
        dash_last_used (int): Last dash timestamp.
        dash_direction (pygame.Vector2): Dash direction.
        dash_trail (list): Dash visual trail points.
        _dash_trail_timer (float): Dash trail spawn accumulator.

    Methods:
        __init__():
            Initialize all character attributes, skills, and resources.
        __getattribute__(name):
            Apply dynamic modifiers to cooldown, damage, and attack_cooldown attributes.

        # Skill Learning
        _build_skillbook():
            Build and return the initial skillbook (includes dash).
        learn_fireball():
        learn_flame_shield():
        learn_pyromancers_fury():
        learn_frost_nova():
        learn_ice_armor():
        learn_glacial_cascade():
        learn_chain_lightning():
        learn_static_field():
        learn_thunderstrike():
        learn_entangling_roots():
        learn_regeneration():
        learn_summon_spirit():
        learn_shadow_step():
        learn_poison_blade():
        learn_dark_pact():
        learn_arcane_missiles():
        learn_mana_flow():
        learn_mystic_barrier():
        learn_berserkers_rage():
        learn_eternal_fortress():
        learn_soul_harvest():
        learn_void_walker():
        learn_elemental_mastery():
        learn_chrono_shift():
            Add the named skill/passive/keystone to the skillbook.

        # Skill Usage
        get_skill_in_slot(slot_index):
            Return the skill dict in the given hotbar slot.
        use_skill_from_slot(slot_index, aim_direction=None):
            Use the skill in the given hotbar slot.
        get_skill_cooldown_percent(skill):
            Return cooldown progress (0.0-1.0) for a skill.
        is_skill_ready(skill):
            Return True if the skill is off cooldown.
        use_skill(skill, aim_direction=None):
            Execute a skill by its dict, spawning the appropriate projectile/effect.

        # Combat
        can_attack(current_time=None):
            Return True if melee attack cooldown has elapsed.
        start_attack(current_time=None, show_slash=True):
            Begin a melee attack animation.
        get_effective_attack_damage():
            Return attack damage including bonuses.
        get_forward_direction():
            Return the forward Vector2 based on current direction.
        get_center():
            Return the center position as Vector2.
        get_melee_anchor():
            Return the origin point for melee slash.
        attack(enemies, aim_direction=None, cone_degrees=90.0):
            Perform a standard melee attack (sword style).
        _apply_weapon_enchantments(enemy):
            Apply on-hit weapon effects to the given enemy.
        attack_mace(enemies, aim_direction=None):
        attack_axe(enemies, aim_direction=None):
        attack_spear(enemies, aim_direction=None):
        attack_war_hammer(enemies, aim_direction=None):
            Perform weapon-class-specific melee attacks.

        # Resource Management
        consume_stamina(amount):
            Deduct stamina, clamped to 0.
        restore_stamina(amount):
            Restore stamina, clamped to max.
        consume_mana(amount):
            Deduct mana, clamped to 0.
        restore_mana(amount):
            Restore mana, clamped to max.
        heal(amount):
            Restore HP, clamped to max_hp.
        use_item(item):
            Use a consumable item from inventory.

        # Status Effects
        get_resistance(effect_name):
            Return resistance value (0.0-1.0) for the given effect.
        is_immune(effect_name):
            Return True if resistance >= 1.0 for the effect.
        add_effect(effect):
            Add a status effect to the character.
        strength_metric(x):
            Placeholder metric for sorting/filtering effects.

        # Core Loop
        get_rect():
            Return the collision rectangle at current position.
        _set_velocity():
            Calculate movement velocity from keyboard input.
        update(dt, collision_system, obstacles):
            Update movement, resources, cooldowns, effects, and skill particles.
        take_damage(amount, ignore_invulnerability=False):
            Apply damage, factoring invulnerability, shield, and armor.
        die():
            Handle death: play sound, reset HP and position.
        draw(screen, camera_offset=None):
            Render the character and all active skill/passive visual effects.
        gain_xp(amount):
            Add XP and trigger level-up if threshold reached.
        level_up():
            Increase level, update next XP threshold.

        # Floating Text
        add_floating_text(text, x, y, color, duration, size):
            Queue a floating damage/heal text popup.
        _update_floating_texts(dt):
            Update floating text lifetimes.
        _draw_floating_texts(screen, camera_offset):
            Render all active floating texts.

        # Skill Visual Effects
        _spawn_shadow_step_effect(start_pos, end_pos):
        _update_shadow_step_particles(dt):
        _draw_shadow_step(screen, camera_offset):
        _spawn_summon_effect(pos):
        _update_summon_spirit_particles(dt):
        _draw_summon_spirit(screen, camera_offset):
        _update_berserkers_rage_particles(dt):
        _draw_berserkers_rage(screen, camera_offset):
        _update_flame_shield_particles(dt):
        _draw_flame_shield(screen, camera_offset):
        _update_ice_armor_particles(dt):
        _draw_ice_armor(screen, camera_offset):
        _update_mystic_barrier_particles(dt):
        _draw_mystic_barrier(screen, camera_offset):
        _update_chrono_shift_particles(dt):
        _draw_chrono_shift(screen, camera_offset):
            Update and render skill/passive visual particle effects.

        # Visual Helpers (defined inside draw)
        swoosh(center, angle_deg, arc_total, radius, color, width, alpha, layers=3):
            Draw a melee swoosh arc.
        gust_line(start, end, color, alpha, width):
            Draw a single gust arc line.
        dot(center, color, alpha, radius):
            Draw a single dot for melee effects.
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

        # Mana system (using ManaSystem component)
        # Regen rate reduced 4x (10.0 -> 2.5) so mana regenerates much
        # more slowly and the magical crumble animation has time to play out.
        self.mana_system = ManaSystem(max_mana=100, mana_regen_rate=2.5)
        self.max_mana = self.mana_system.max_mana
        self.mana = self.mana_system.current_mana
        self.mana_drain_rate = 20.0
        self.mana_regen_rate = self.mana_system.mana_regen_rate
        # energy is an alias to support systems that use "energy"
        self.energy = self.stamina
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
        # Resistances: values 0.0..1.0 (1.0 = immune). Example: {"poison": 0.5, "slow": 0.2}
        self.resistances = {}

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

        # Charge attack system
        self.charge_start_time: int = 0
        self.is_charging: bool = False
        self.is_charged: bool = False
        self.charge_threshold: int = 500  # ms to hold for charged attack
        self.charge_indicator: float = 0.0  # 0..1 progress
        self.charge_mouse_pos: pygame.Vector2 | None = None

        # Fast attack
        self.fast_attack_damage_mult: float = 0.6
        self.fast_attack_knockback_mult: float = 2.0
        self.fast_attack_stun_duration: float = 0.5

        # Charged attack
        self.charged_attack_damage_mult: float = 1.8
        self.charged_attack_range_mult: float = 1.3
        self.normal_attack_stamina_cost: float = 6.0
        self.fast_attack_stamina_cost: float = 4.0
        self.charged_attack_stamina_cost: float = 30.0

        # Block / Parry system
        self.blocking: bool = False
        self.block_start_time: int = 0
        self.parry_window_ms: int = 200  # ms after block start where parry is possible
        self.block_damage_reduction: float = 0.6  # 60% reduction while blocking
        self.parry_active: bool = False
        self.parry_timer: float = 0.0
        self.parry_success: bool = False
        self.stamina_parry_cost: float = 25.0

        # Weapon throw
        self.throw_damage_mult: float = 1.5
        self.throw_cooldown_ms: int = 2000
        self.throw_last_time: int = -self.throw_cooldown_ms

        # Stun mechanic (for enemies hit by fast attack, parry)
        self.stun_applied: bool = False

        # Attack visual tint and scale for different attack types
        self.attack_visual_tint: tuple | None = None  # (r,g,b,a) or None
        self.attack_visual_scale: float = 1.0


        self.skillbook = self._build_skillbook()
        self.skillbar = [None for _ in range(6)]
        self.fireball_speed = 420.0
        self.fireball_range = 520.0
        self.fireball_damage = 28
        self.fireball_blast_radius = 110.0
        self.fireball_fuse_time = 0.9
        self.fireball_cooldown = 1300
        self.fireball_last_used = -self.fireball_cooldown
        self.fireball_knockback = 18.0
        self.game_state = None

        # Light/lamp support
        self.active_lamp = None

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
        self.summon_spirit_particles = []

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
        self.shadow_step_effect = None
        self.shadow_step_particles = []

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

        # Rainbow aura (Gay Ring)
        self.rainbow_aura_active = False
        self.rainbow_aura_particles = []

        self.dash_speed_multiplier = 3.0
        self.dash_duration = 0.14
        self.dash_cooldown = 900
        self.dash_active_time = 0.0
        self.dash_last_used = -self.dash_cooldown
        self.dash_direction = pygame.Vector2(1, 0)
        self.dash_trail = []
        self._dash_trail_timer = 0.0

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

    def _try_open_magic_article(self, title):
        gs = getattr(self, "game_state", None)
        if gs and hasattr(gs, "app") and hasattr(gs.app, "article_tracker"):
            gs.app.article_tracker.try_open(gs.app, "magic", title)

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
            "manaCost": 20,
        })
        logger.info("Player learned Fireball!")
        self._try_open_magic_article("Fireball")

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
            "manaCost": 15,
        })
        logger.info("Player learned Flame Shield!")
        self._try_open_magic_article("Flame Shield")

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
            "manaCost": 25,
        })
        logger.info("Player learned Frost Nova!")
        self._try_open_magic_article("Frost Nova")

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
            "manaCost": 30,
        })
        logger.info("Player learned Ice Armor!")
        self._try_open_magic_article("Ice Armor")

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
            "manaCost": 22,
        })
        logger.info("Player learned Glacial Cascade!")
        self._try_open_magic_article("Glacial Cascade")

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
            "manaCost": 18,
        })
        logger.info("Player learned Chain Lightning!")
        self._try_open_magic_article("Chain Lightning")

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
            "manaCost": 28,
        })
        logger.info("Player learned Thunderstrike!")
        self._try_open_magic_article("Thunderstrike")

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
            "manaCost": 22,
        })
        logger.info("Player learned Entangling Roots!")
        self._try_open_magic_article("Entangling Roots")

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
            "manaCost": 35,
        })
        logger.info("Player learned Summon Spirit!")
        self._try_open_magic_article("Summon Spirit")

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
            "manaCost": 20,
        })
        logger.info("Player learned Shadow Step!")
        self._try_open_magic_article("Shadow Step")

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
            "manaCost": 25,
        })
        logger.info("Player learned Dark Pact!")
        self._try_open_magic_article("Dark Pact")

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
            "manaCost": 24,
        })
        logger.info("Player learned Arcane Missiles!")
        self._try_open_magic_article("Arcane Missiles")

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
            "manaCost": 25,
        })
        logger.info("Player learned Mystic Barrier!")
        self._try_open_magic_article("Mystic Barrier")

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
            "manaCost": 30,
        })
        logger.info("Player learned Berserker's Rage!")
        self._try_open_magic_article("Berserker's Rage")

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
            "manaCost": 40,
        })
        logger.info("Player learned Chrono Shift!")
        self._try_open_magic_article("Chrono Shift")

    def get_skill_in_slot(self, slot_index):
        if 0 <= slot_index < len(self.skillbar):
            return self.skillbar[slot_index]
        return None

    def use_skill_from_slot(self, slot_index, aim_direction=None):
        skill = self.get_skill_in_slot(slot_index)
        if skill is None:
            return False
        return self.use_skill(skill, aim_direction=aim_direction)

    def get_skill_cooldown_percent(self, skill):
        """
        Get the cooldown progress for a skill (0.0 = ready, 1.0 = just used).
        
        Args:
            skill (dict): The skill dictionary with skill_id.
            
        Returns:
            float: Cooldown percentage (0.0 to 1.0), where 0.0 means ready.
        """
        if skill is None:
            return 0.0
        
        skill_id = skill.get("skill_id", "")
        if not skill_id:
            return 0.0
        
        current_time = pygame.time.get_ticks()
        
        last_used = getattr(self, f"{skill_id}_last_used", None)
        if last_used is None:
            return 0.0
        
        # Skills with dynamic cooldown (may include cooldown reduction bonuses)
        if skill_id == "berserkers_rage":
            cooldown = self.berserkers_rage_cooldown + getattr(self, "berserkers_rage_cooldown_bonus", 0)
        elif skill_id == "chrono_shift":
            cooldown = self.chrono_shift_cooldown + getattr(self, "chrono_shift_cooldown_bonus", 0)
        else:
            cooldown = getattr(self, f"{skill_id}_cooldown", 0)
        
        if cooldown <= 0:
            return 0.0
        
        elapsed = current_time - last_used
        if elapsed >= cooldown:
            return 0.0
        return 1.0 - (elapsed / cooldown)

    def is_skill_ready(self, skill):
        """
        Check if a skill is ready to use (cooldown expired).

        Args:
            skill (dict): The skill dictionary with skill_id.

        Returns:
            bool: True if skill is ready, False if on cooldown.
        """
        return self.get_skill_cooldown_percent(skill) == 0.0

    def _is_skill_on_cooldown(self, skill_id, current_time):
        """
        Internal cooldown gate that mirrors the per-skill cooldown logic
        in ``use_skill``. Returns True when the skill is still on cooldown.

        This lets us reject a cast *before* spending mana, so the player
        doesn't get penalised for trying to fire a skill they couldn't use.

        Args:
            skill_id (str): The skill identifier (e.g. "fireball").
            current_time (int): ``pygame.time.get_ticks()`` value in ms.

        Returns:
            bool: True if the skill is on cooldown, False if it's ready.
        """
        # Skills with dynamic cooldown (may include cooldown reduction bonuses)
        if skill_id == "berserkers_rage":
            cooldown = self.berserkers_rage_cooldown + getattr(self, "berserkers_rage_cooldown_bonus", 0)
        elif skill_id == "chrono_shift":
            cooldown = self.chrono_shift_cooldown + getattr(self, "chrono_shift_cooldown_bonus", 0)
        else:
            cooldown = getattr(self, f"{skill_id}_cooldown", 0)

        if cooldown is None or cooldown <= 0:
            return False

        last_used = getattr(self, f"{skill_id}_last_used", None)
        if last_used is None:
            return False
        return current_time - last_used < cooldown

    def _is_skill_state_blocked(self, skill_id):
        """
        Return True if the skill can't be used due to a non-cooldown state
        condition (e.g. toggle already active). Mirrors the early ``if ...:
        return False`` guards inside ``use_skill``.
        """
        if skill_id == "flame_shield" and getattr(self, "flame_shield_active", False):
            return True
        if skill_id == "ice_armor" and getattr(self, "ice_armor_active", False):
            return True
        if skill_id == "mystic_barrier" and getattr(self, "mystic_barrier_active", False):
            return True
        if skill_id == "berserkers_rage" and getattr(self, "berserkers_rage_active", False):
            return True
        if skill_id == "chrono_shift" and getattr(self, "chrono_shift_active", False):
            return True
        return False

    def get_skill_mana_cost(self, skill):
        """
        Return the mana cost of a skill (read from the skill dict's ``manaCost`` key).

        Falls back to 0 for skills that don't define one (e.g., passives, dash).

        Args:
            skill (dict): The skill dictionary with a ``manaCost`` field.

        Returns:
            int: Mana required to cast the skill (>= 0).
        """
        if skill is None:
            return 0
        try:
            return int(skill.get("manaCost", 0) or 0)
        except (TypeError, ValueError):
            return 0

    def use_skill(self, skill, aim_direction=None):
        if skill is None:
            return False

        skill_id = skill.get("skill_id", "")
        current_time = pygame.time.get_ticks()

        # ─── ManaSystem integration ────────────────────────────────────
        # Cast gating order (matches the inner skill branches' return-False
        # checks so mana is only spent on a *successful* cast):
        #   1. Cooldown   — don't penalise the player for trying a skill
        #                    they can't use yet.
        #   2. State      — e.g. an already-active Flame Shield / Ice Armor.
        #   3. Mana       — only checked once we know the cast can actually
        #                    happen, then deducted at the same time.
        # Anything that fails steps 1/2 returns ``False`` *without* touching
        # the player's mana pool.
        if self._is_skill_on_cooldown(skill_id, current_time):
            return False
        if self._is_skill_state_blocked(skill_id):
            return False

        mana_cost = self.get_skill_mana_cost(skill)
        if mana_cost > 0 and not self.mana_system.has_enough_mana(mana_cost):
            logger.info(
                f"Cannot cast '{skill_id}': not enough mana "
                f"(need {mana_cost}, have {int(self.mana_system.current_mana)})."
            )
            try:
                self.add_floating_text(
                    "Not enough mana!",
                    self.pos.x,
                    self.pos.y - 50,
                    (180, 120, 255),
                    1.2,
                    20,
                )
            except Exception:
                pass
            return False

        # Mana is sufficient (or the skill is free) and the cooldown/state
        # gates have passed — deduct it so the inner branch commits. If the
        # inner branch still bails (e.g. missing game_state, no projectiles
        # container) the cost is not refunded; this matches typical ARPG
        # design where paying mana and missing is a player mistake.
        if mana_cost > 0:
            self.consume_mana(mana_cost)
        # ───────────────────────────────────────────────────────────────

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
            # Dash magic article + guide: Skills & Hotbar (first use)
            gs = getattr(self, "game_state", None)
            if gs and hasattr(gs, "app") and hasattr(gs.app, "article_tracker"):
                tr = gs.app.article_tracker
                tr.try_open(gs.app, "magic", "Dash")
                if not gs._triggered_guide_skills:
                    gs._triggered_guide_skills = True
                    tr.try_open(gs.app, "guide", "3. Skills & Hotbar")
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

            start_pos = self.get_center()
            teleport_offset = direction.normalize() * self.shadow_step_range
            self.pos += teleport_offset
            if getattr(self, '_obstacles', None):
                self._collision_system.resolve_teleport_collision(self, self._obstacles, direction)
            end_pos = self.get_center()

            self.invulnerable = True
            self.invulnerability_timer = self.shadow_step_invuln_duration
            self.shadow_step_last_used = current_time

            self._spawn_shadow_step_effect(start_pos, end_pos)
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

            # Spawn summon visual effect
            self._spawn_summon_effect(spawn_pos)
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

    def get_resistance(self, effect_name: str) -> float:
        """
        Return resistance in range [0.0, 1.0] for given effect name.
        1.0 means immune.
        """
        return float(self.resistances.get(effect_name, 0.0))

    def is_immune(self, effect_name: str) -> bool:
        return self.get_resistance(effect_name) >= 1.0

    def add_effect(self, effect):
        """
        Add an effect, applying resistances and simple stacking rules:
        - Immunity (resistance >= 1.0) blocks the effect.
        - Partial resistance scales magnitude and duration.
        - If an existing effect of the same class exists, replace it only if the new one is stronger.
        """
        # Map class names to effect keys used in resistances
        name_map = {
            "RegenerationEffect": "regeneration",
            "PoisonEffect": "poison",
            "BurnEffect": "burn",
            "ConfusionEffect": "confusion",
            "DizzinessEffect": "dizziness",
            "SlowEffect": "slow",
        }
        cls_name = effect.__class__.__name__
        e_name = name_map.get(cls_name, cls_name.lower())
        r = self.get_resistance(e_name)

        if r >= 1.0:
            logger.info(f"Effect '{e_name}' blocked by immunity on {getattr(self, 'id', type(self))}")
            return

        # Apply resistance scaling
        if r > 0.0:
            # Scale damage-like fields
            if hasattr(effect, "damage_per_sec"):
                effect.damage_per_sec = effect.damage_per_sec * max(0.0, 1.0 - r)
            if hasattr(effect, "amount_per_sec"):
                effect.amount_per_sec = effect.amount_per_sec * max(0.0, 1.0 - r)
            # Scale duration
            if hasattr(effect, "duration"):
                effect.duration = effect.duration * max(0.0, 1.0 - r)
            # Scale slow's speed_multiplier (reduce slow strength)
            if hasattr(effect, "speed_multiplier") and effect.speed_multiplier < 1.0:
                reduction = 1.0 - effect.speed_multiplier
                reduced = reduction * max(0.0, 1.0 - r)
                effect.speed_multiplier = 1.0 - reduced

            logger.debug(f"Applied resistance {r:.2f} to effect '{e_name}' -> adjusted attrs: {effect.__dict__}")

        # Stacking: if same class exists, replace only if new is stronger
        def strength_metric(x):
            s = 0.0
            if hasattr(x, "damage_per_sec"):
                s += float(getattr(x, "damage_per_sec", 0.0))
            if hasattr(x, "amount_per_sec"):
                s += float(getattr(x, "amount_per_sec", 0.0))
            if hasattr(x, "duration"):
                s += float(getattr(x, "duration", 0.0)) * 0.1
            if hasattr(x, "speed_multiplier"):
                s += (1.0 - float(getattr(x, "speed_multiplier", 1.0))) * 10.0
            return s

        for i, e in enumerate(self.effects):
            if type(e) == type(effect):
                if strength_metric(effect) > strength_metric(e):
                    self.effects[i] = effect
                    logger.debug(f"Replaced weaker '{e_name}' effect with stronger one on {getattr(self, 'id', type(self))}")
                else:
                    logger.debug(f"Ignored incoming weaker or equal '{e_name}' effect on {getattr(self, 'id', type(self))}")
                return

        # Otherwise append new effect
        self.effects.append(effect)

        # Effects article: open on first application to the player
        _effect_article_map = {
            "RegenerationEffect": "Boon: Regeneration",
            "PoisonEffect": "Bane: Poison",
            "BurnEffect": "Bane: Burn",
            "ConfusionEffect": "Bane: Confusion",
            "DizzinessEffect": "Bane: Dizziness",
            "SlowEffect": "Bane: Slow",
            "FreezeEffect": "Bane: Freeze & Root",
            "RootEffect": "Bane: Freeze & Root",
        }
        art_title = _effect_article_map.get(cls_name)
        if art_title:
            gs = getattr(self, "game_state", None)
            if gs and hasattr(gs, "app") and hasattr(gs.app, "article_tracker"):
                gs.app.article_tracker.try_open(gs.app, "effects", art_title)

    def gain_xp(self, amount):
        self.xp += amount
        logger.info(f"Gained {amount} XP. Current XP: {self.xp}/{self.xp_to_next_level}")
        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level_up()

    def level_up(self):
        prev_level = self.level
        self.level += 1
        self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
        self.max_hp += 20
        self.hp = self.max_hp
        self.skill_tree_points += 1
        logger.info(f"Level Up! Level: {self.level}, Max HP: {self.max_hp}, Skill points: {self.skill_tree_points}")
        print(f"Level Up! Level: {self.level}, Max HP: {self.max_hp}, Skill points: {self.skill_tree_points}")
        # Article triggers
        gs = getattr(self, "game_state", None)
        if gs and hasattr(gs, "app") and hasattr(gs.app, "article_tracker"):
            tr = gs.app.article_tracker
            if not gs._triggered_guide_leveling:
                gs._triggered_guide_leveling = True
                tr.try_open(gs.app, "guide", "6. Leveling & Experience")
            if self.level >= 10 and not gs._triggered_guide_final:
                gs._triggered_guide_final = True
                tr.try_open(gs.app, "guide", "10. Final Words")

    def can_attack(self, current_time=None):
        if current_time is None:
            current_time = pygame.time.get_ticks()
        effective_cooldown = self.attack_cooldown * getattr(self, "cooldown_multiplier", 1.0)
        return current_time - self.last_attack_time >= effective_cooldown

    def start_attack(self, current_time=None, show_slash=True, visual_tint=None):
        if current_time is None:
            current_time = pygame.time.get_ticks()
        self.last_attack_time = current_time
        self.is_attacking = show_slash
        self.attack_visual_tint = visual_tint

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

        self.start_attack(current_time, show_slash=True, visual_tint=self.attack_visual_tint)
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
            if getattr(self, '_obstacles', None):
                self._collision_system.resolve_static_collision(enemy, self._obstacles)

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
            if getattr(self, '_obstacles', None):
                self._collision_system.resolve_static_collision(enemy, self._obstacles)

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
            if getattr(self, '_obstacles', None):
                self._collision_system.resolve_static_collision(enemy, self._obstacles)

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
            if getattr(self, '_obstacles', None):
                self._collision_system.resolve_static_collision(enemy, self._obstacles)

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
            if getattr(self, '_obstacles', None):
                self._collision_system.resolve_static_collision(enemy, self._obstacles)

    # ── Charge system ──
    def start_charge(self, mouse_pos=None):
        current_time = pygame.time.get_ticks()
        if not self.can_attack(current_time):
            return
        self.charge_start_time = current_time
        self.is_charging = True
        self.is_charged = False
        self.charge_indicator = 0.0
        self.charge_mouse_pos = mouse_pos

    def cancel_charge(self):
        self.is_charging = False
        self.is_charged = False
        self.charge_indicator = 0.0
        self.charge_start_time = 0

    def update_charge(self):
        if not self.is_charging:
            return
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.charge_start_time
        self.charge_indicator = min(1.0, elapsed / self.charge_threshold)
        if elapsed >= self.charge_threshold:
            self.is_charged = True

    def release_charge(self, enemies, aim_direction=None):
        if self.is_charged:
            self.attack_charged(enemies, aim_direction)
        elif self.is_charging:
            self.attack_visual_tint = None
            self.attack_visual_scale = 1.0
            if not self.consume_stamina(self.normal_attack_stamina_cost):
                self.cancel_charge()
                return
            self.attack(enemies, aim_direction=aim_direction)
        self.cancel_charge()

    # ── Charged attack ──
    def attack_charged(self, enemies, aim_direction=None):
        current_time = pygame.time.get_ticks()
        if not self.consume_stamina(self.charged_attack_stamina_cost):
            self.attack_visual_tint = None
            self.attack_visual_scale = 1.0
            if not self.consume_stamina(self.normal_attack_stamina_cost):
                return
            self.attack(enemies, aim_direction=aim_direction)
            return

        self.attack_visual_tint = (255, 60, 60, 120)  # Red tint for charged attack
        self.attack_visual_scale = 1.4

        effective_damage = self.attack_damage
        self.attack_damage = int(self.attack_damage * self.charged_attack_damage_mult)
        effective_range = self.attack_range
        self.attack_range = int(self.attack_range * self.charged_attack_range_mult)

        # Charged attack with red tint
        self.attack(enemies, aim_direction=aim_direction)

        self.attack_damage = effective_damage
        self.attack_range = effective_range

    # ── Fast attack ──
    def attack_fast(self, enemies, aim_direction=None):
        current_time = pygame.time.get_ticks()
        if not self.can_attack(current_time):
            return
        if not self.consume_stamina(self.fast_attack_stamina_cost):
            return

        self.attack_visual_tint = (180, 80, 255, 120)
        self.attack_visual_scale = 0.7
        self.start_attack(current_time, show_slash=True, visual_tint=self.attack_visual_tint)

        if aim_direction is None:
            aim_direction = self.get_forward_direction()
        aim_dir = pygame.Vector2(aim_direction)
        if aim_dir.length_squared() == 0:
            aim_dir = pygame.Vector2(1, 0)
        aim_dir = aim_dir.normalize()
        self.last_attack_dir = pygame.Vector2(aim_dir)

        range_sq = float(self.attack_range) * float(self.attack_range)
        origin = self.get_melee_anchor() + aim_dir * self.melee_origin_offset
        forward = self.get_forward_direction()
        if forward.length_squared() == 0:
            forward = pygame.Vector2(1, 0)
        cone_half_angle = 45.0
        cos_half_angle = math.cos(math.radians(cone_half_angle))

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

            final_damage = int(self.get_effective_attack_damage() * self.fast_attack_damage_mult)
            enemy.take_damage(max(1, final_damage))
            self._apply_weapon_enchantments(enemy)

            if self.poison_blade:
                enemy.add_effect(PoisonEffect(self.poison_blade_duration, self.poison_blade_damage_per_sec))

            knockback_force = 40 * self.fast_attack_knockback_mult
            enemy.pos += knock_dir * knockback_force
            if hasattr(enemy, "stun"):
                enemy.stun(self.fast_attack_stun_duration)
            if getattr(self, '_obstacles', None):
                self._collision_system.resolve_static_collision(enemy, self._obstacles)

    # ── Block / Parry system ──
    def start_block(self):
        self.blocking = True
        self.block_start_time = pygame.time.get_ticks()
        self.parry_success = False

    def stop_block(self):
        was_blocking = self.blocking
        hold_duration = pygame.time.get_ticks() - self.block_start_time
        self.blocking = False
        self.parry_active = False
        # If block was very brief (< 150ms), return False to signal it was a click, not a hold
        return not was_blocking or hold_duration < 150

    def is_in_parry_window(self) -> bool:
        if not self.blocking:
            return False
        return (pygame.time.get_ticks() - self.block_start_time) <= self.parry_window_ms

    def do_parry(self, enemy) -> bool:
        if not self.consume_stamina(self.stamina_parry_cost):
            return False
        self.parry_success = True
        self.parry_active = True
        if hasattr(enemy, "stun"):
            enemy.stun(1.5)
        damage = int(self.get_effective_attack_damage() * 0.5)
        enemy.take_damage(max(1, damage))
        return True

    def reflect_projectile(self, projectile) -> bool:
        if not self.consume_stamina(self.stamina_parry_cost):
            return False
        self.parry_success = True
        self.parry_active = True
        if hasattr(projectile, "direction"):
            projectile.direction *= -1
        if hasattr(projectile, "speed"):
            projectile.speed *= 1.5
        return True

    # ── Weapon throw ──
    def can_throw_weapon(self) -> bool:
        current_time = pygame.time.get_ticks()
        return current_time - self.throw_last_time >= self.throw_cooldown_ms

    def throw_weapon(self, enemies, aim_direction=None, game_state=None):
        current_time = pygame.time.get_ticks()
        if not self.can_throw_weapon():
            return
        if not game_state or not hasattr(game_state, 'INV_manager'):
            return

        # Take the weapon from the active hotbar slot
        inv_manager = game_state.INV_manager
        weapon_slot = inv_manager.take_active_hotbar_item()
        if weapon_slot is None:
            return
        weapon_item, count = weapon_slot
        if weapon_item is None or not hasattr(weapon_item, 'weapon_class'):
            return
        if getattr(weapon_item, 'weapon_class', None) != 'melee':
            return
        if hasattr(weapon_item, 'is_broken') and weapon_item.is_broken():
            return

        self.throw_last_time = current_time

        if aim_direction is None:
            aim_direction = self.get_forward_direction()
        aim_dir = pygame.Vector2(aim_direction)
        if aim_dir.length_squared() == 0:
            aim_dir = pygame.Vector2(1, 0)
        aim_dir = aim_dir.normalize()

        # Throw range is inversely proportional to weapon attack range
        weapon_range = getattr(weapon_item, 'range', 50)
        throw_range = max(80, min(250, 250 - weapon_range))
        speed = 300.0

        # If weapon has only 1 durability or less → no drop on landing
        will_drop = not (getattr(weapon_item, 'durability', 1) <= 1 or getattr(weapon_item, 'unbreakable', False))
        if will_drop:
            weapon_item.apply_durability_damage(1)

        # Create the thrown weapon projectile
        from src.entities.projectile import ThrownWeapon
        origin = self.get_center() + aim_dir * 20
        proj = ThrownWeapon(origin, aim_dir, speed, throw_range, weapon_item, will_drop)
        if hasattr(game_state, 'projectiles'):
            game_state.projectiles.append(proj)
            logger.info(f"Threw weapon {getattr(weapon_item, 'name', 'weapon')}")

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
        self._collision_system = collision_system
        self._obstacles = obstacles
        # Reset attacking flag after short duration
        if self.is_attacking and pygame.time.get_ticks() - self.last_attack_time > 200:
            self.is_attacking = False

        # Update charge state
        self.update_charge()

        # Blocking slowing is applied after _set_velocity (see below)

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

        # Update Shadow Step particles
        self._update_shadow_step_particles(dt)

        # Update Summon Spirit particles
        self._update_summon_spirit_particles(dt)

        # Update Rainbow Aura particles
        if self.rainbow_aura_active:
            self._update_rainbow_aura_particles(dt)

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
        if self.blocking:
            self.speed = min(self.speed, self.base_speed * 0.5)
        
        # Stamina management (logic from your update method)
        if self.moving and self.is_sprinting:
            self.stamina -= self.stamina_drain_rate * dt
            if self.stamina <= 0:
                self.stamina = 0
                self.can_sprint = False
        elif not self.blocking:
            regen = self.stamina_regen_rate
            if self.moving:
                regen *= 0.25
            self.stamina += regen * dt
            if self.stamina >= self.max_stamina:
                self.stamina = self.max_stamina
                self.can_sprint = True

        # Mana regeneration (using ManaSystem)
        if hasattr(self, "mana_system"):
            self.mana_system.update(dt)
            # Sync with legacy attributes for compatibility
            self.mana = self.mana_system.current_mana
            self.max_mana = self.mana_system.max_mana

        # KEY IMPLEMENTATION STEP: Single function call for collision-aware movement
        collision_system.handle_movement_and_collision(self, dt, obstacles)

        if self.dash_active_time > 0:
            self.dash_active_time = max(0.0, self.dash_active_time - dt)
            self._dash_trail_timer += dt
            # Record afterimage at intervals
            if self._dash_trail_timer >= 0.025:
                self._dash_trail_timer = 0.0
                img = self.image
                if self.direction == "side" and self.flip:
                    img = self.animations_flipped["side"][self.frame_index]
                self.dash_trail.append({
                    "pos": pygame.Vector2(self.pos),
                    "image": img,
                    "life": 0.35,
                })
        elif self.dash_trail:
            self.dash_trail.clear()

        # Update dash trail lifetimes
        for t in self.dash_trail[:]:
            t["life"] -= dt
            if t["life"] <= 0:
                self.dash_trail.remove(t)

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
            if random.random() < self.void_walker_dodge_chance:
                old_center = self.get_center()
                # Teleport in a random direction
                angle = random.uniform(0, math.pi * 2)
                direction = pygame.Vector2(math.cos(angle), math.sin(angle))
                self.pos += direction * self.void_walker_teleport_range
                if getattr(self, '_obstacles', None):
                    self._collision_system.resolve_teleport_collision(self, self._obstacles, direction)
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
                        enemy_center = enemy.get_rect().center
                        if player_center.distance_to(enemy_center) < reflect_radius:
                            enemy.take_damage(reflect_damage)
                            logger.info(f"Mystic Barrier reflected {reflect_damage} damage to {enemy.__class__.__name__}!")

        # Block reduces incoming damage
        if self.blocking and amount > 0:
            reduced = int(amount * (1.0 - self.block_damage_reduction))
            logger.info(f"Block reduced damage from {amount} to {reduced}")
            amount = max(1, reduced)

        self.hp -= amount

        # Static Field: 12% chance to shock all nearby enemies when hit
        if self.static_field and amount > 0:
            if random.random() < self.static_field_proc_chance:
                game_state = getattr(self, "game_state", None)
                if game_state is not None and hasattr(game_state, "enemies"):
                    player_center = self.get_center()
                    for enemy in list(game_state.enemies):
                        enemy_center = enemy.get_rect().center
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

        # ─── Armor durability damage ─────────────────────────────────
        # Every incoming hit chips a point off *each* equipped armor
        # piece so the player can see their gear take real wear over
        # the course of a fight.  We do this *after* HP is decremented
        # (and only when the hit actually connected) so dodges, full
        # blocks and pre-HP deaths don't burn durability for free.
        #
        # The damage is gated on:
        #   * amount > 0   -- ignore 0-damage "hits" (e.g. post-ice-armor
        #                     zero-damage echoes),
        #   * not ignore_invulnerability  -- mirror the rest of the
        #                     durability system: scripted "true damage"
        #                     hits still wear armor down (no cheat).
        if amount > 0 and not ignore_invulnerability:
            equip_inv = None
            game_state = getattr(self, "game_state", None)
            if game_state is not None:
                equip_inv = getattr(game_state, "PLAYER_inventory_equipment", None)
            if equip_inv is not None and hasattr(equip_inv, "damage_equipped_armor"):
                try:
                    broken_pieces = equip_inv.damage_equipped_armor(1, source="hit")
                except Exception:
                    broken_pieces = []
                for col, row, item, _broke in broken_pieces:
                    try:
                        self.add_floating_text(
                            f"{getattr(item, 'name', 'Armor')} broke!",
                            self.pos.x,
                            self.pos.y - 40,
                            (220, 90, 90),
                            1.6,
                            20,
                        )
                    except Exception:
                        pass
                    try:
                        logger.info(
                            f"Armor piece broke: id={getattr(item, 'id', '?')} "
                            f"slot=({col},{row}) defense={getattr(item, 'defense_value', 0)}"
                        )
                    except Exception:
                        pass
                # Re-sync the live defense so the *next* hit in the
                # same frame is reduced by the new (lower) armor
                # value rather than the stale pre-wear one.
                if broken_pieces and hasattr(equip_inv, "sync_character_defense"):
                    try:
                        equip_inv.sync_character_defense(self)
                    except Exception:
                        pass

        if not ignore_invulnerability:
            self.invulnerable = True
            self.invulnerability_timer = self.invulnerability_duration

        logger.info(f"Player took {amount} damage. HP: {self.hp}/{self.max_hp}")
        if self.hp <= 0:
            self.die()

    def heal(self, amount):
        """
        Restore HP by the specified amount, clamped to max_hp.
        """
        if amount <= 0:
            return
        prev_hp = self.hp
        self.hp = min(self.max_hp, self.hp + int(amount))
        healed = self.hp - prev_hp
        if healed > 0:
            logger.info(f"Player healed {healed} HP. HP: {self.hp}/{self.max_hp}")

    def consume_stamina(self, amount):
        """
        Attempt to consume stamina. Returns True if enough stamina was available.
        """
        if amount <= 0:
            return True
        if self.stamina >= amount:
            self.stamina -= amount
            # keep energy alias in sync
            self.energy = self.stamina
            logger.debug(f"Consumed {amount} stamina. Stamina: {int(self.stamina)}/{self.max_stamina}")
            return True
        logger.debug(f"Not enough stamina to consume {amount}. Current: {int(self.stamina)}")
        return False

    def restore_stamina(self, amount):
        """
        Restore stamina (clamped to max_stamina).
        """
        if amount <= 0:
            return
        prev = int(self.stamina)
        self.stamina = min(self.max_stamina, self.stamina + amount)
        self.energy = self.stamina
        logger.info(f"Player restored {int(self.stamina) - prev} stamina. Stamina: {int(self.stamina)}/{self.max_stamina}")

    def consume_mana(self, amount):
        """
        Attempt to consume mana. Returns True if enough mana was available.
        Uses the ManaSystem component if available.
        """
        if amount <= 0:
            return True
        if hasattr(self, "mana_system"):
            result = self.mana_system.consume_mana(amount)
            # Sync with legacy attributes
            self.mana = self.mana_system.current_mana
            return result
        # Fallback if mana_system not initialized
        if getattr(self, "mana", 0) >= amount:
            self.mana -= amount
            logger.debug(f"Consumed {amount} mana. Mana: {int(self.mana)}/{self.max_mana}")
            return True
        logger.debug(f"Not enough mana to consume {amount}. Current: {int(getattr(self,'mana',0))}")
        return False

    def restore_mana(self, amount):
        """
        Restore mana (clamped to max_mana).
        Uses the ManaSystem component if available.
        """
        if amount <= 0:
            return
        if hasattr(self, "mana_system"):
            self.mana_system.restore_mana(amount)
            # Sync with legacy attributes
            self.mana = self.mana_system.current_mana
            return
        # Fallback if mana_system not initialized
        prev = int(getattr(self, "mana", 0))
        self.mana = min(self.max_mana, self.mana + amount)
        logger.info(f"Player restored {int(self.mana) - prev} mana. Mana: {int(self.mana)}/{self.max_mana}")

    def use_item(self, item):
        """
        Use an Item instance on the player. Returns True if item was consumed/used.
        """
        try:
            used = item.use(self)
            if used:
                logger.info(f"Player used item {getattr(item, 'id', str(item))}")
            return bool(used)
        except Exception as e:
            logger.exception(f"Error using item: {e}")
            return False

    def die(self):
        logger.warning("Player died!")
        self.death_sound.play()
        self.death_count += 1
        self.hp = self.max_hp  # reset health
        self.pos = self.spawn_point.copy()  # teleport to spawn
        self.cancel_charge()
        self.stop_block()
        logger.info(f"Player respawned at {self.pos}. Death count: {self.death_count}")

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        # ── Dash motion trail ──
        for t in self.dash_trail:
            life_ratio = t["life"] / 0.35 if 0.35 > 0 else 0
            if life_ratio <= 0:
                continue
            alpha = int(180 * life_ratio)
            draw_pos = (int(t["pos"].x - camera_offset.x), int(t["pos"].y - camera_offset.y))
            trail_img = t["image"].copy()
            trail_img.set_alpha(alpha)
            # Blue-tinted afterimage
            tint = pygame.Surface(trail_img.get_size(), pygame.SRCALPHA)
            tint.fill((120, 180, 255, int(60 * life_ratio)))
            trail_img.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(trail_img, draw_pos)

        # ── Dash wind lines ──
        if self.dash_active_time > 0:
            center = self.get_center()
            cx = int(center.x - camera_offset.x)
            cy = int(center.y - camera_offset.y)
            dash_dir = self.dash_direction
            perp = pygame.Vector2(-dash_dir.y, dash_dir.x)
            for i in range(3):
                offset = perp * (8 + i * 12 - 24)
                start_pt = (cx + int(offset.x) - int(dash_dir.x * 20),
                            cy + int(offset.y) - int(dash_dir.y * 20))
                end_pt = (cx + int(offset.x) - int(dash_dir.x * 60),
                          cy + int(offset.y) - int(dash_dir.y * 60))
                wind_alpha = int(100 * (self.dash_active_time / self.dash_duration))
                pygame.draw.line(screen, (180, 220, 255, wind_alpha), start_pt, end_pt,
                                 max(1, int(2 - i * 0.5)))

        # Blink if invulnerable
        if self.invulnerable and int(pygame.time.get_ticks() / 100) % 2 == 0:
            pass # Skip drawing for blinking effect
        else:
            # Draw relative to self.pos (top-left of sprite), NOT self.get_rect() (hitbox)
            draw_pos = (int(self.pos.x - camera_offset.x), int(self.pos.y - camera_offset.y))
            img = self.image
            if self.direction == "side" and self.flip:
                img = self.animations_flipped["side"][self.frame_index]
            if self.rainbow_aura_active:
                from src.items.items import GayRing
                colors = GayRing.RAINBOW_COLORS
                t = pygame.time.get_ticks() / 1000.0
                n = len(colors)
                phase = (t * 3.0) % n
                ci = int(phase)
                frac = phase - ci
                c1 = colors[ci]
                c2 = colors[(ci + 1) % n]
                r = int(c1[0] + (c2[0] - c1[0]) * frac)
                g = int(c1[1] + (c2[1] - c1[1]) * frac)
                b = int(c1[2] + (c2[2] - c1[2]) * frac)
                tint = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                tint.fill((r, g, b, 140))
                img = img.copy()
                img.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(img, draw_pos)

        # ── Charge indicator ──
        if self.is_charging:
            center = self.get_center()
            cx = int(center.x - camera_offset.x)
            cy = int(center.y - camera_offset.y)
            charge_progress = self.charge_indicator
            radius = 10 + int(charge_progress * 15)
            alpha = int(100 + 155 * charge_progress)
            color = (255, int(100 * (1 - charge_progress)), int(100 * (1 - charge_progress)), alpha)
            pygame.draw.circle(screen, color[:3] + (alpha,), (cx, cy), radius, max(1, int(3 - charge_progress * 2)))
            if charge_progress > 0.5:
                outer_r = radius + 5 + int((charge_progress - 0.5) * 10)
                outer_a = int(80 * (charge_progress - 0.5) * 2)
                pygame.draw.circle(screen, (255, 50, 50, outer_a), (cx, cy), outer_r, 2)
            # Small particles rising during charge
            for i in range(3):
                p_offset = (pygame.time.get_ticks() * 0.003 + i * 2.1) % 3
                px = cx + int(math.sin(charge_progress * 10 + i * 2.1) * 12)
                py = cy - 15 - int(p_offset * 12)
                pa = int(180 * (1 - p_offset / 3) * charge_progress)
                if pa > 0:
                    pygame.draw.circle(screen, (255, 100, 100, pa), (px, py), 2)

        # ── Block circle (360°) ──
        if self.blocking:
            center = self.get_center()
            cx = int(center.x - camera_offset.x)
            cy = int(center.y - camera_offset.y)
            radius = self.attack_range + 10
            surf_size = int(radius * 2 + 20)
            surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            # Green block circle (full 360°)
            pygame.draw.circle(surf, (80, 220, 80, 80),
                               (surf_size // 2, surf_size // 2), radius,
                               max(2, int(radius * 0.06)))
            pygame.draw.circle(surf, (160, 255, 160, 50),
                               (surf_size // 2, surf_size // 2), radius - 3,
                               max(1, int(radius * 0.03)))
            screen.blit(surf, (cx - surf_size // 2, cy - surf_size // 2),
                        special_flags=pygame.BLEND_ALPHA_SDL2)
            # Parry window visual (pulsing yellow circle)
            if self.is_in_parry_window():
                p_alpha = int(80 + 80 * abs(math.sin(pygame.time.get_ticks() * 0.01)))
                pygame.draw.circle(surf, (255, 255, 100, p_alpha),
                                   (surf_size // 2, surf_size // 2), radius + 3,
                                   max(3, int(radius * 0.08)))
                screen.blit(surf, (cx - surf_size // 2, cy - surf_size // 2),
                            special_flags=pygame.BLEND_ALPHA_SDL2)
            # Parry success flash
            if self.parry_success:
                flash_alpha = int(180 * max(0, 1.0 - (pygame.time.get_ticks() - self.block_start_time) / 300))
                if flash_alpha > 0:
                    pygame.draw.circle(screen, (255, 255, 100, flash_alpha), (cx, cy),
                                       radius, max(2, int(radius * 0.06)))
                    pygame.draw.circle(screen, (255, 255, 200, flash_alpha // 2), (cx, cy),
                                       radius - 3, max(1, int(radius * 0.03)))

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

                # Pick colors based on attack type
                if self.attack_visual_tint is not None:
                    tr, tg, tb, _ = self.attack_visual_tint
                    if tr > 200 and tg < 100:
                        outer_c, mid_c, main_c, inner_c, edge_c = (140, 70, 70), (210, 110, 110), (255, 180, 180), (255, 220, 220), (255, 255, 255)
                        particle_c = (255, 200, 200)
                    elif tb > 200 and tr < 200:
                        outer_c, mid_c, main_c, inner_c, edge_c = (100, 70, 140), (160, 110, 210), (210, 180, 255), (235, 220, 255), (255, 255, 255)
                        particle_c = (200, 180, 255)
                    else:
                        outer_c, mid_c, main_c, inner_c, edge_c = (70, 80, 140), (110, 140, 210), (180, 210, 255), (220, 235, 255), (255, 255, 255)
                        particle_c = (160, 200, 255)
                else:
                    outer_c, mid_c, main_c, inner_c, edge_c = (70, 80, 140), (110, 140, 210), (180, 210, 255), (220, 235, 255), (255, 255, 255)
                    particle_c = (160, 200, 255)

                swing_total = 140
                start_offset = 65
                current_angle = base_angle - 90 + start_offset - swing_total * p

                fade = 1.0 - p * 0.45
                alpha = int(180 * fade)
                arc_radius = (60 + 10 * p) * self.attack_visual_scale
                arc_current = swing_total * p

                # ── Crescent slash trail (procedural, no sprite) ──
                # Dark outer glow
                swoosh(anchor_s, base_angle - 270, arc_current, arc_radius + 16, outer_c, 10, alpha // 5, 2)
                # Mid glow
                swoosh(anchor_s, base_angle - 270, arc_current, arc_radius + 8, mid_c, 7, alpha // 3, 2)
                # Main crescent body (light)
                swoosh(anchor_s, base_angle - 270, arc_current, arc_radius, main_c, 5, alpha, 3)
                # Bright inner core
                swoosh(anchor_s, base_angle - 270, arc_current * 0.7, arc_radius * 0.8, inner_c, 3, alpha, 2)
                # Hot cutting edge
                swoosh(anchor_s, base_angle - 270, arc_current * 0.4, arc_radius * 0.6, edge_c, 2, int(alpha * 0.8), 1)

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
                    dot(to_screen(pos), particle_c, int(100 * (1 - lp) * fade), 1 + int(3 * (1 - lp)))

            elif combat_style == "dagger":
                # A realistic dagger slash. The blade is a shaded steel polygon
                # sweeping the full 80° attack cone, with a 2-frame motion blur,
                # a single brief tip glint, a thin pale air-arc tracing the path,
                # and a few dust motes kicked up by the strike. No glow ribbons,
                # no laser core — just a fast piece of metal cutting air.
                half_cone = 40.0
                blade_len = float(self.attack_range)

                def _swing_angle(sp):
                    if sp < 0.15:
                        return -half_cone * 1.25
                    if sp < 0.70:
                        wp = (sp - 0.15) / 0.55
                        return -half_cone + 2.0 * half_cone * (wp * wp * (3.0 - 2.0 * wp))
                    wp = (sp - 0.70) / 0.30
                    return half_cone + 8.0 * wp

                def _draw_blade(swing_a, alpha):
                    if alpha <= 0.02:
                        return None
                    swing_dir = attack_dir.rotate(swing_a)
                    perp = pygame.Vector2(-swing_dir.y, swing_dir.x)

                    tip    = base_anchor + swing_dir * blade_len
                    mid    = base_anchor + swing_dir * (blade_len * 0.45)
                    hilt   = base_anchor + swing_dir * 5.0
                    top_m  = mid  + perp * 1.8
                    top_h  = hilt + perp * 2.5
                    bot_m  = mid  - perp * 1.3
                    bot_h  = hilt - perp * 2.0

                    tip_s   = to_screen(tip)
                    top_m_s = to_screen(top_m)
                    top_h_s = to_screen(top_h)
                    bot_m_s = to_screen(bot_m)
                    bot_h_s = to_screen(bot_h)

                    # Steel body fill.
                    pygame.draw.polygon(
                        screen,
                        (190, 200, 215, int(225 * alpha)),
                        [tip_s, top_m_s, top_h_s, bot_h_s, bot_m_s],
                        0,
                    )
                    # Lit (top) edge highlight.
                    pygame.draw.line(screen, (232, 238, 248, int(195 * alpha)),
                                     top_h_s, top_m_s, 1)
                    pygame.draw.line(screen, (242, 246, 252, int(155 * alpha)),
                                     top_m_s, tip_s, 1)
                    # Shadow (bottom) edge.
                    pygame.draw.line(screen, (100, 110, 130, int(160 * alpha)),
                                     bot_h_s, bot_m_s, 1)
                    # Thin bright cutting edge along the leading (top) edge.
                    pygame.draw.line(screen, (248, 250, 253, int(210 * alpha)),
                                     top_h_s, tip_s, 1)
                    return tip_s

                # 1. Motion blur: two ghost positions at older swing angles.
                _draw_blade(_swing_angle(max(0.15, p - 0.06)), 0.22)
                _draw_blade(_swing_angle(max(0.15, p - 0.03)), 0.40)

                # 2. Thin pale air-arc tracing the swing path (wake disturbance).
                if 0.18 < p < 0.95:
                    n_arc = 10
                    prev = None
                    for i in range(n_arc + 1):
                        sp = i / n_arc
                        if sp > p:
                            break
                        sa = _swing_angle(sp)
                        sdir = attack_dir.rotate(sa)
                        pt = to_screen(base_anchor + sdir * blade_len)
                        if prev is not None:
                            cd = abs(sp - 0.5) * 2
                            arc_alpha = int(38 * (1 - cd * 0.5) *
                                            (1.0 - max(0, p - 0.78) * 3))
                            if arc_alpha > 0:
                                pygame.draw.line(screen,
                                                 (170, 180, 195, arc_alpha),
                                                 prev, pt, 1)
                        prev = pt

                # 3. The main blade (full opacity).
                tip_s = _draw_blade(_swing_angle(p), 1.0)

                # 4. Brief tip glint — a quick reflection, not a sustained glow.
                glint = max(0.0, 1.0 - abs(p - 0.45) * 4.5)
                if glint > 0 and tip_s is not None:
                    pygame.draw.circle(screen,
                                       (255, 255, 255, int(220 * glint)),
                                       tip_s, max(1, int(2.5 * glint)))

                # 5. Dust motes kicked up by the strike (warm grey, not sparks).
                dust_specs = [
                    (0.28, -half_cone * 0.40, 3.0, 1.0),
                    (0.38, -half_cone * 0.10, 3.5, 0.9),
                    (0.45,  half_cone * 0.30, 3.0, 0.8),
                    (0.55,  half_cone * 0.65, 3.5, 0.9),
                    (0.62,  half_cone * 0.85, 4.0, 1.0),
                ]
                for start_p, ang_off, drift, base_size in dust_specs:
                    lifetime = 0.25
                    if p < start_p or p > start_p + lifetime:
                        continue
                    age = (p - start_p) / lifetime
                    sa = _swing_angle(start_p) + ang_off
                    sdir = attack_dir.rotate(sa)
                    base_pos = base_anchor + sdir * blade_len
                    drift_vec = sdir * (drift * age) + pygame.Vector2(0, -2.0 * age)
                    dust_pos = base_pos + drift_vec
                    d_alpha = int(150 * (1 - age))
                    d_size = max(1, int(base_size * (1 - age * 0.3)))
                    if d_alpha > 0:
                        dot(to_screen(dust_pos), (165, 155, 140),
                            d_alpha, d_size)

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
                perp = pygame.Vector2(-attack_dir.y, attack_dir.x)
                tail = base_anchor - attack_dir * 10
                tail_s = to_screen(tail)
                shaft_color = (130, 130, 135)
                shaft_alpha = int(180 * fade)
                shaft_width = max(2, int(5 - p * 2))
                shaft_end = tip - attack_dir * 10
                gust_line(tail_s, to_screen(shaft_end), shaft_color, shaft_alpha, shaft_width)
                head_width = 8
                head_len = 14
                base_p1 = tip - attack_dir * head_len + perp * head_width
                base_p2 = tip - attack_dir * head_len - perp * head_width
                head_pts = [tip_s, to_screen(base_p1), to_screen(base_p2)]
                if len(head_pts) >= 3:
                    pygame.draw.polygon(screen, (160, 160, 165, int(200 * fade)), head_pts, 0)
                    pygame.draw.polygon(screen, (180, 180, 185, int(220 * fade)), head_pts, 2)
                if p > 0.1 and p < 0.85:
                    for i in range(10):
                        part_p = (p - 0.1 - i * 0.06) / 0.6
                        if part_p < 0 or part_p > 1:
                            continue
                        spread = 4 + 18 * part_p
                        side = -1 if i % 2 == 0 else 1
                        offset = 3 + 10 * part_p
                        pp = tip - attack_dir * offset + perp * spread * side
                        a = int(90 * (1 - part_p) * fade)
                        dot(to_screen(pp), (210, 210, 220), a, 1 + int(2 * (1 - part_p)))
                        gust_line(to_screen(pp - attack_dir * 4), to_screen(pp), (200, 200, 210), int(a * 0.7), 1)
                    for i in range(8):
                        part_p = (p - 0.1 - i * 0.07) / 0.6
                        if part_p < 0 or part_p > 1:
                            continue
                        stem_t = part_p * 0.7 + 0.15
                        stem_pos = tail + attack_dir * (thrust * stem_t)
                        stem_side = -1 if i % 2 == 0 else 1
                        stem_off = perp * (3 + 8 * (1 - part_p)) * stem_side
                        sp = stem_pos + stem_off
                        sa = int(50 * (1 - part_p) * fade)
                        dot(to_screen(sp), (190, 190, 200), sa, 1 + int(1 * (1 - part_p)))

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

            # Color tint overlay for charged/fast attacks
            if self.attack_visual_tint is not None:
                tint_r, tint_g, tint_b, tint_a = self.attack_visual_tint
                tint_fade = int(tint_a * (1.0 - p * 0.7))
                if tint_fade > 0:
                    tint_radius = (60 + 10 * p) * self.attack_visual_scale
                    surf_size = int(tint_radius * 2 + 20)
                    tint_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
                    pygame.draw.arc(tint_surf, (tint_r, tint_g, tint_b, tint_fade),
                                    pygame.Rect(surf_size // 2 - tint_radius, surf_size // 2 - tint_radius,
                                                tint_radius * 2, tint_radius * 2),
                                    math.radians(270 - 70 * p), math.radians(270 + 70 * p),
                                    max(2, int(6 * (1 - p * 0.5))))
                    base_angle = -math.degrees(math.atan2(attack_dir.y, attack_dir.x))
                    rot = pygame.transform.rotate(tint_surf, base_angle - 270)
                    rot_rect = rot.get_rect(center=anchor_s)
                    screen.blit(rot, rot_rect.topleft)

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

        # Draw Shadow Step visual effect (always draw if active, even during other effects)
        self._draw_shadow_step(screen, camera_offset)

        # Draw Summon Spirit visual effect
        self._draw_summon_spirit(screen, camera_offset)

        # Draw Rainbow Aura (Gay Ring)
        if self.rainbow_aura_active:
            self._draw_rainbow_aura(screen, camera_offset)

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

    # ─── Shadow Step helpers ─────────────────────────────────────────

    def _spawn_shadow_step_effect(self, start_pos, end_pos):
        """Create vanish/appear particles and trail for Shadow Step teleport."""
        self.shadow_step_effect = {
            "start": pygame.Vector2(start_pos),
            "end": pygame.Vector2(end_pos),
            "life": 0.5,
            "max_life": 0.5,
        }
        # Vanish particles at start
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(40, 120)
            self.shadow_step_particles.append({
                "pos": pygame.Vector2(start_pos),
                "vel": pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                "max_life": (ml := random.uniform(0.2, 0.4)),
                "life": ml,
                "size": random.uniform(2.0, 5.0),
                "phase": "vanish",
                "color": random.choice([
                    (80, 40, 140),
                    (120, 60, 180),
                    (160, 100, 220),
                ]),
            })
        # Appear particles at end
        for _ in range(25):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(20, 80)
            self.shadow_step_particles.append({
                "pos": pygame.Vector2(end_pos),
                "vel": pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                "max_life": (ml := random.uniform(0.3, 0.5)),
                "life": ml,
                "size": random.uniform(3.0, 6.0),
                "phase": "appear",
                "color": random.choice([
                    (80, 40, 160),
                    (140, 80, 220),
                    (180, 120, 255),
                ]),
            })
        # Trail particles along the path
        steps = 10
        for i in range(steps):
            t = i / steps
            trail_pos = start_pos.lerp(end_pos, t)
            self.shadow_step_particles.append({
                "pos": pygame.Vector2(trail_pos),
                "vel": pygame.Vector2(random.uniform(-10, 10), random.uniform(-10, 10)),
                "max_life": (ml := random.uniform(0.15, 0.35)),
                "life": ml,
                "size": random.uniform(1.5, 3.5),
                "phase": "trail",
                "color": random.choice([
                    (60, 30, 120),
                    (100, 50, 160),
                    (140, 70, 200),
                ]),
            })

    def _update_shadow_step_particles(self, dt):
        if self.shadow_step_effect is not None:
            self.shadow_step_effect["life"] -= dt
            if self.shadow_step_effect["life"] <= 0:
                self.shadow_step_effect = None

        for p in self.shadow_step_particles[:]:
            p["pos"] += p["vel"] * dt
            p["vel"] *= 0.92
            p["life"] -= dt
            if p["life"] <= 0:
                self.shadow_step_particles.remove(p)

    def _draw_shadow_step(self, screen, camera_offset):
        if not self.shadow_step_particles:
            return

        # Draw shadow trail line between start and end
        if self.shadow_step_effect is not None:
            progress = 1.0 - self.shadow_step_effect["life"] / self.shadow_step_effect["max_life"]
            start_screen = self.shadow_step_effect["start"] - camera_offset
            end_screen = self.shadow_step_effect["end"] - camera_offset
            trail_alpha = int(100 * (1 - progress))
            # Draw shadowy path line
            line_surf = pygame.Surface((800, 600), pygame.SRCALPHA)
            for w in range(3):
                offset = pygame.Vector2(random.uniform(-3, 3), random.uniform(-3, 3))
                pygame.draw.line(line_surf, (60, 30, 120, trail_alpha // (w + 1)),
                                 (int(start_screen.x + offset.x), int(start_screen.y + offset.y)),
                                 (int(end_screen.x + offset.x), int(end_screen.y + offset.y)),
                                 max(1, 3 - w))
            screen.blit(line_surf, (0, 0))

        # Draw particles
        for p in self.shadow_step_particles:
            life_r = min(1.0, p["life"] / p["max_life"]) if p["max_life"] > 0 else 0
            if life_r <= 0:
                continue
            px = int(p["pos"].x - camera_offset.x)
            py = int(p["pos"].y - camera_offset.y)
            alpha = int(220 * life_r)
            size = max(1, int(p["size"] * life_r))
            r, g, b = p["color"]

            phase = p.get("phase", "vanish")
            if phase == "appear":
                # Diamond-like burst shape
                pts = [
                    (px, py - size * 2),
                    (px + size, py),
                    (px, py + size * 2),
                    (px - size, py),
                ]
                p_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
                soff = size * 2
                rel_pts = [(p[0] - px + soff, p[1] - py + soff) for p in pts]
                pygame.draw.polygon(p_surf, (r, g, b, alpha), rel_pts)
                pygame.draw.polygon(p_surf, (min(255, r + 60), min(255, g + 60), min(255, b + 60), alpha), rel_pts, 1)
                screen.blit(p_surf, (px - soff, py - soff))
            else:
                # Dark mist circle for vanish/trail
                g_sz = size * 2
                g_surf = pygame.Surface((g_sz * 2, g_sz * 2), pygame.SRCALPHA)
                pygame.draw.circle(g_surf, (r, g, b, alpha // 2), (g_sz, g_sz), g_sz)
                screen.blit(g_surf, (px - g_sz, py - g_sz))
                pygame.draw.circle(screen, (r, g, b, alpha), (px, py), size)

    # ─── Summon Spirit helpers ───────────────────────────────────────

    def _spawn_summon_effect(self, pos):
        """Create green energy particles for the summon circle."""
        for _ in range(30):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(40, 150)
            self.summon_spirit_particles.append({
                "pos": pygame.Vector2(pos),
                "vel": pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                "max_life": (ml := random.uniform(0.3, 0.7)),
                "life": ml,
                "size": random.uniform(2.0, 5.0),
                "color": random.choice([
                    (60, 220, 60), (100, 255, 100),
                    (160, 255, 140), (40, 180, 40),
                ]),
            })

    def _update_summon_spirit_particles(self, dt):
        for p in self.summon_spirit_particles[:]:
            p["pos"] += p["vel"] * dt
            p["vel"] *= 0.92
            p["life"] -= dt
            if p["life"] <= 0:
                self.summon_spirit_particles.remove(p)

    def _draw_summon_spirit(self, screen, camera_offset):
        for p in self.summon_spirit_particles:
            life_r = min(1.0, p["life"] / p["max_life"]) if p["max_life"] > 0 else 0
            if life_r <= 0:
                continue
            px = int(p["pos"].x - camera_offset.x)
            py = int(p["pos"].y - camera_offset.y)
            alpha = int(200 * life_r)
            size = max(1, int(p["size"] * life_r))
            r, g, b = p["color"]
            g_sz = size * 2
            g_surf = pygame.Surface((g_sz * 2, g_sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(g_surf, (r, g, b, alpha // 2), (g_sz, g_sz), g_sz)
            screen.blit(g_surf, (px - g_sz, py - g_sz))
            pygame.draw.circle(screen, (r, g, b, alpha), (px, py), size)

    # ─── Berserker's Rage helpers ─────────────────────────────────────

    def _update_berserkers_rage_particles(self, dt):
        if self.berserkers_rage_active:
            spawn_count = max(1, int(30 * dt))
            for _ in range(spawn_count):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(10, 80)
                ml = random.uniform(0.2, 0.6)
                self.berserkers_rage_particles.append({
                    "angle": angle,
                    "dist": dist,
                    "life": ml,
                    "max_life": ml,
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
        center = self.get_center()
        cx = center.x - camera_offset.x
        cy = center.y - camera_offset.y
        t = pygame.time.get_ticks() / 1000.0

        pulse = 0.5 + 0.5 * math.sin(t * 6.0)
        radius = 70.0

        # ── Outer rage aura ──
        aura_radius = radius * (0.9 + 0.15 * pulse)
        aura_surf = pygame.Surface((int(aura_radius * 2) + 8, int(aura_radius * 2) + 8), pygame.SRCALPHA)
        a_cx = int(aura_radius) + 4
        a_cy = int(aura_radius) + 4
        aura_a = int(50 + 40 * pulse)
        pygame.draw.circle(aura_surf, (220, 40, 10, aura_a), (a_cx, a_cy), int(aura_radius))
        inner_a = int(40 + 30 * pulse)
        pygame.draw.circle(aura_surf, (255, 80, 20, inner_a), (a_cx, a_cy), int(aura_radius * 0.6))
        core_a = int(25 + 20 * pulse)
        pygame.draw.circle(aura_surf, (255, 160, 40, core_a), (a_cx, a_cy), int(aura_radius * 0.3))
        screen.blit(aura_surf, (int(cx - aura_radius - 4), int(cy - aura_radius - 4)))

        # ── Ground rage rune (rotating star) ──
        rune_pts = []
        rune_outer = radius * 0.5
        rune_inner = radius * 0.2
        for ri in range(8):
            ra = t * 1.2 + ri * math.pi / 4
            rr = rune_outer if ri % 2 == 0 else rune_inner
            rune_pts.append((cx + math.cos(ra) * rr, cy + math.sin(ra) * rr))
        rune_alpha = int(30 + 20 * math.sin(t * 3))
        pygame.draw.polygon(screen, (200, 60, 20, rune_alpha), rune_pts, 2)

        # ── Rage ring ──
        ring_r = radius * 0.8
        ring_a = int(80 + 50 * math.sin(t * 9.0))
        ring_surf = pygame.Surface((int(ring_r * 2) + 8, int(ring_r * 2) + 8), pygame.SRCALPHA)
        rc_x = int(ring_r) + 4
        rc_y = int(ring_r) + 4
        for i in range(3):
            r = int(ring_r * (0.85 + 0.05 * (i + 1)))
            offset_phase = t * 4.0 + i * 1.0
            rr = r * (0.98 + 0.04 * math.sin(offset_phase))
            pygame.draw.circle(ring_surf,
                               (200, 60 + i * 30, 10 + i * 10, ring_a // (i + 1)),
                               (rc_x, rc_y), int(rr),
                               max(1, 3 - i))
        screen.blit(ring_surf, (int(cx - ring_r - 4), int(cy - ring_r - 4)))

        # ── Rage spikes ──
        spike_count = 14
        for i in range(spike_count):
            spike_angle = t * 2.5 + i * (math.pi * 2 / spike_count)
            spike_len = 15 + 15 * (0.3 + 0.7 * ((i % 3) / 2.0)) * (0.5 + 0.5 * math.sin(t * 7.0 + i * 2.0))
            inner_dist = radius * (0.7 + 0.1 * ((i % 3) / 2.0)) + 6 * math.sin(t * 5.0 + i * 1.5)
            sx1 = cx + math.cos(spike_angle) * inner_dist
            sy1 = cy + math.sin(spike_angle) * inner_dist
            sx2 = cx + math.cos(spike_angle) * (inner_dist + spike_len)
            sy2 = cy + math.sin(spike_angle) * (inner_dist + spike_len)
            spike_alpha = int(140 + 80 * math.sin(t * 8.0 + i * 1.7))
            sw = max(1, int(2 + 3 * (i % 3) / 2.0 * math.sin(t * 4.0 + i)))
            pygame.draw.line(screen, (220, 60 + i * 8, 10 + i * 4, spike_alpha),
                             (sx1, sy1), (sx2, sy2), sw)

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
            for _ in range(4):
                sp_angle = random.uniform(0, math.pi * 2)
                sp_dist = random.uniform(0, radius * 0.45)
                sp_x = cx + math.cos(sp_angle) * sp_dist + random.uniform(-3, 3)
                sp_y = cy + random.uniform(-30, 5)
                sp_size = random.randint(1, 3)
                sp_color = random.choice([(255, 200, 80), (255, 140, 40), (255, 255, 120)])
                pygame.draw.circle(screen, sp_color, (int(sp_x), int(sp_y)), sp_size)

        # ── Ground fire bursts ──
        if self.berserkers_rage_active:
            for fi in range(3):
                fa = t * 8.0 + fi * math.pi * 2 / 3
                fd = radius * 0.5 + 20 * math.sin(t * 6 + fi * 1.5)
                fx = cx + math.cos(fa) * fd
                fy = cy + math.sin(fa) * fd
                fh = 10 + 8 * math.sin(t * 10 + fi * 2.3)
                fw = max(1, int(3 + 2 * math.sin(t * 7 + fi * 1.8)))
                f_alpha = int(100 + 80 * math.sin(t * 9 + fi * 2.0))
                pygame.draw.line(screen, (255, 120 + fi * 20, 30, f_alpha),
                                 (fx, fy), (fx, fy - fh), fw)
                pygame.draw.line(screen, (255, 200, 80, f_alpha // 2),
                                 (fx, fy), (fx, fy - fh // 2), fw - 1)

    # ─── Flame Shield helpers ───────────────────────────────────────────

    def _update_flame_shield_particles(self, dt):
        """Spawn, move, and cull flame particles around the character."""
        import random

        # Spawn new particles while active
        if self.flame_shield_active:
            effective_radius = self.flame_shield_radius
            if self.pyromancers_fury:
                effective_radius *= self.pyromancers_fury_area_mult
            spawn_count = max(1, int(30 * dt))
            for _ in range(spawn_count):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(effective_radius * 0.3, effective_radius)
                speed = random.uniform(30, 90)
                is_flame_tongue = random.random() < 0.25
                max_life = random.uniform(0.3, 0.8)
                self.flame_shield_particles.append({
                    "angle": angle,
                    "dist": dist,
                    "life": max_life,
                    "max_life": max_life,
                    "size": random.uniform(3.0, 8.0),
                    "drift": random.uniform(-20, 20),
                    "vertical_speed": -speed,
                    "color": random.choice([
                        (255, 120, 20),
                        (255, 80, 10),
                        (255, 180, 40),
                        (255, 60, 10),
                        (255, 200, 80),
                    ]),
                    "flame_tongue": is_flame_tongue,
                    "tongue_len": random.uniform(8, 18) if is_flame_tongue else 0,
                    "tongue_phase": random.uniform(0, math.pi * 2),
                })

        # Update existing particles
        for p in self.flame_shield_particles[:]:
            p["life"] -= dt
            if p["life"] <= 0:
                self.flame_shield_particles.remove(p)
                continue
            p["angle"] += p["drift"] * dt
            p["dist"] = max(0, p["dist"] - 10 * dt)
            p["vertical_speed"] -= 140 * dt

    def _draw_flame_shield(self, screen, camera_offset):
        """Draw the flame shield aura and particles."""
        center = self.get_center()
        cx = center.x - camera_offset.x
        cy = center.y - camera_offset.y
        t = pygame.time.get_ticks() / 1000.0

        visual_radius = self.flame_shield_radius
        if self.pyromancers_fury:
            visual_radius *= self.pyromancers_fury_area_mult

        # ── Heat distortion shimmer (subtle wavy ring) ──
        shimmer_surf = pygame.Surface((int(visual_radius * 2) + 20, int(visual_radius * 2) + 20), pygame.SRCALPHA)
        shimmer_a = int(15 + 10 * math.sin(t * 5.0))
        for i in range(3):
            r = visual_radius + i * 6 + 4 * math.sin(t * 7.0 + i * 2.0)
            pygame.draw.circle(shimmer_surf, (255, 180, 80, shimmer_a // (i + 1)),
                               (int(r) + 10, int(r) + 10), int(r), 1)
        screen.blit(shimmer_surf, (int(cx - visual_radius - 10), int(cy - visual_radius - 10)))

        # ── Inner pulsing glow ring ──
        pulse_slow = 0.6 + 0.4 * math.sin(t * 4.5)
        pulse_fast = 0.5 + 0.5 * math.sin(t * 11.0)
        glow_radius = visual_radius * (0.82 + 0.18 * pulse_slow)
        glow_surf = pygame.Surface((int(glow_radius * 2) + 8, int(glow_radius * 2) + 8), pygame.SRCALPHA)
        glow_a = int(45 + 35 * pulse_slow)
        pygame.draw.circle(glow_surf, (255, 80, 10, glow_a),
                           (int(glow_radius) + 4, int(glow_radius) + 4),
                           int(glow_radius))
        mid_r = int(glow_radius * 0.65)
        mid_a = int(35 + 25 * pulse_slow)
        pygame.draw.circle(glow_surf, (255, 160, 40, mid_a),
                           (int(glow_radius) + 4, int(glow_radius) + 4),
                           mid_r)
        inner_r = int(glow_radius * 0.35)
        inner_a = int(25 + 20 * pulse_slow)
        pygame.draw.circle(glow_surf, (255, 220, 80, inner_a),
                           (int(glow_radius) + 4, int(glow_radius) + 4),
                           inner_r)
        screen.blit(glow_surf, (int(cx - glow_radius - 4), int(cy - glow_radius - 4)))

        # ── Flame tongue ring segments ──
        tongue_count = 12
        for i in range(tongue_count):
            angle = i * (math.pi * 2 / tongue_count) + t * 0.8
            flicker = 0.6 + 0.4 * math.sin(t * 14.0 + i * 1.7)
            tongue_len = visual_radius * 0.12 * flicker
            inner = visual_radius * (0.92 + 0.06 * pulse_fast)
            outer = inner + tongue_len
            sx = cx + int(math.cos(angle) * inner)
            sy = cy + int(math.sin(angle) * inner)
            ex = cx + int(math.cos(angle) * outer)
            ey = cy + int(math.sin(angle) * outer)
            t_alpha = int(120 + 100 * flicker * pulse_fast)
            if t_alpha > 10:
                tongue_color = (255, 140 + int(60 * flicker), 20 + int(40 * flicker), t_alpha)
                # Draw tongue as tapered line
                pygame.draw.line(screen, tongue_color, (sx, sy), (ex, ey), max(1, int(3 + 4 * flicker)))
                # Wider glow for tongue
                tg_sz = max(1, int(1 + flicker * 2))
                for glow_offset in range(3):
                    tg_x = sx + int((ex - sx) * glow_offset / 3)
                    tg_y = sy + int((ey - sy) * glow_offset / 3)
                    tg_r = int(tg_sz * (2 - glow_offset * 0.5))
                    tg_surf = pygame.Surface((tg_r * 2, tg_r * 2), pygame.SRCALPHA)
                    tg_a = int(t_alpha * 0.3 * (1 - glow_offset * 0.25))
                    pygame.draw.circle(tg_surf, (255, 200, 80, tg_a), (tg_r, tg_r), tg_r)
                    screen.blit(tg_surf, (tg_x - tg_r, tg_y - tg_r))

        # ── Outer flickering ring ──
        ring_r = visual_radius
        ring_a = int(80 + 50 * math.sin(t * 9.0))
        ring_surf = pygame.Surface((int(ring_r * 2) + 4, int(ring_r * 2) + 4), pygame.SRCALPHA)
        ring_width = max(1, int(2 + 2 * pulse_fast))
        pygame.draw.circle(ring_surf, (255, 80, 5, ring_a),
                           (int(ring_r) + 2, int(ring_r) + 2),
                           int(ring_r), ring_width)
        # Second ring layer
        if ring_width > 1:
            pygame.draw.circle(ring_surf, (255, 200, 60, ring_a // 2),
                               (int(ring_r) + 2, int(ring_r) + 2),
                               int(ring_r * 0.98), max(1, ring_width - 1))
        screen.blit(ring_surf, (int(cx - ring_r - 2), int(cy - ring_r - 2)))

        # ── Flame particles ──
        for p in self.flame_shield_particles:
            life_ratio = min(1.0, p["life"] / p["max_life"]) if p["max_life"] > 0 else 0
            if life_ratio <= 0:
                continue

            px = cx + math.cos(p["angle"]) * p["dist"]
            py = cy + math.sin(p["angle"]) * p["dist"] + p["vertical_speed"] * (1 - life_ratio) * 0.3

            alpha = int(255 * life_ratio)
            size = max(1, int(p["size"] * life_ratio))
            r, g, b = p["color"]

            # Flame tongue particles draw as elongated shapes
            if p.get("flame_tongue") and p["tongue_len"] > 0:
                tongue_phase = p.get("tongue_phase", 0)
                tongue_len = p["tongue_len"] * (0.5 + 0.5 * math.sin(t * 12 + tongue_phase))
                perp = pygame.Vector2(-math.sin(p["angle"]), math.cos(p["angle"]))
                base_pt = (px, py)
                tip_pt = (px + perp.x * tongue_len * 0.3,
                          py + perp.y * tongue_len * 0.3)
                t_alpha = int(alpha * 0.6)
                # Draw glow at midpoint
                glow_sz = size * 4
                glow = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow, (r, g, b, t_alpha // 3), (glow_sz, glow_sz), glow_sz)
                screen.blit(glow, (int((base_pt[0] + tip_pt[0]) / 2 - glow_sz),
                                   int((base_pt[1] + tip_pt[1]) / 2 - glow_sz)))
                # Draw tongue line on temp SRCALPHA surface
                min_x = min(base_pt[0], tip_pt[0])
                min_y = min(base_pt[1], tip_pt[1])
                surf_w = int(max(base_pt[0], tip_pt[0]) - min_x) + 10
                surf_h = int(max(base_pt[1], tip_pt[1]) - min_y) + 10
                if surf_w > 0 and surf_h > 0:
                    line_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
                    rel_b = (int(base_pt[0] - min_x + 5), int(base_pt[1] - min_y + 5))
                    rel_t = (int(tip_pt[0] - min_x + 5), int(tip_pt[1] - min_y + 5))
                    pygame.draw.line(line_surf, (r, g, b, t_alpha), rel_b, rel_t,
                                     max(1, int(size * 1.5)))
                    screen.blit(line_surf, (int(min_x - 5), int(min_y - 5)))
            else:
                # Standard circular particle
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
            for _ in range(3):
                em_angle = random.uniform(0, math.pi * 2)
                em_dist = random.uniform(0, visual_radius * 0.4)
                em_x = cx + math.cos(em_angle) * em_dist
                em_y = cy + random.uniform(-visual_radius * 0.2, visual_radius * 0.2)
                em_size = random.randint(1, 3)
                em_phase = random.uniform(0, math.pi * 2)
                drift_x = math.sin(em_phase + t) * 2
                em_color = random.choice([(255, 220, 100), (255, 180, 60), (255, 255, 140)])
                pygame.draw.circle(screen, em_color, (int(em_x + drift_x), int(em_y)), em_size)

    # ─── Ice Armor helpers ───────────────────────────────────────────

    def _update_ice_armor_particles(self, dt):
        """Spawn, move, and cull ice particles around the character."""
        if self.ice_armor_active:
            spawn_count = max(1, int(18 * dt))
            for _ in range(spawn_count):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(self.ice_armor_slow_radius * 0.3, self.ice_armor_slow_radius)
                speed = random.uniform(20, 50)
                is_snow = random.random() < 0.3
                self.ice_armor_particles.append({
                    "angle": angle,
                    "dist": dist,
                    "max_life": (ml := random.uniform(0.4, 0.8)),
                    "life": ml,
                    "size": random.uniform(2.0, 5.0),
                    "drift": random.uniform(-10, 10),
                    "vertical_speed": -speed,
                    "is_snow": is_snow,
                    "color": random.choice([
                        (180, 220, 255), (200, 235, 255),
                        (160, 200, 255), (220, 240, 255),
                        (140, 190, 255), (255, 255, 255),
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
        center = self.get_center()
        cx = center.x - camera_offset.x
        cy = center.y - camera_offset.y
        t = pygame.time.get_ticks() / 1000.0

        vr = self.ice_armor_slow_radius
        pulse = 0.5 + 0.5 * math.sin(t * 4.0)
        fast_pulse = 0.5 + 0.5 * math.sin(t * 10.0)

        # ── Hexagonal ice crystal shell ──
        hex_pts = []
        for i in range(6):
            ha = t * 0.3 + i * (math.pi * 2 / 6)
            hr = vr * (0.85 + 0.15 * pulse)
            hx = cx + math.cos(ha) * hr
            hy = cy + math.sin(ha) * hr
            hex_pts.append((hx, hy))

        hex_surf = pygame.Surface((int(vr * 2.2), int(vr * 2.2)), pygame.SRCALPHA)
        hoff = int(vr * 1.1)
        hex_glow_a = int(30 + 20 * pulse)
        rel_hex = [(p[0] - cx + hoff, p[1] - cy + hoff) for p in hex_pts]
        pygame.draw.polygon(hex_surf, (80, 160, 255, hex_glow_a), rel_hex)
        pygame.draw.polygon(hex_surf, (140, 200, 255, int(hex_glow_a * 1.5)), rel_hex,
                            max(1, int(2 + fast_pulse * 2)))
        screen.blit(hex_surf, (cx - hoff, cy - hoff))

        # ── Inner frost glow ring ──
        glow_radius = vr * (0.7 + 0.3 * pulse)
        glow_surf = pygame.Surface((int(glow_radius * 2) + 4, int(glow_radius * 2) + 4), pygame.SRCALPHA)
        glow_a = int(35 + 25 * pulse)
        pygame.draw.circle(glow_surf, (60, 140, 255, glow_a),
                           (int(glow_radius) + 2, int(glow_radius) + 2), int(glow_radius))
        inner_r = int(glow_radius * 0.5)
        inner_a = int(25 + 20 * pulse)
        pygame.draw.circle(glow_surf, (140, 200, 255, inner_a),
                           (int(glow_radius) + 2, int(glow_radius) + 2), inner_r)
        screen.blit(glow_surf, (int(cx - glow_radius - 2), int(cy - glow_radius - 2)))

        # ── Outer frost ring ──
        ring_r = vr
        ring_a = int(70 + 50 * math.sin(t * 7.0))
        ring_surf = pygame.Surface((int(ring_r * 2) + 4, int(ring_r * 2) + 4), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (100, 180, 255, ring_a),
                           (int(ring_r) + 2, int(ring_r) + 2),
                           int(ring_r), max(1, int(2 + fast_pulse)))
        screen.blit(ring_surf, (int(cx - ring_r - 2), int(cy - ring_r - 2)))

        # ── Connecting facet lines (center to hex vertices) ──
        for i in range(6):
            ha = t * 0.3 + i * (math.pi * 2 / 6)
            hr = vr * (0.85 + 0.15 * pulse)
            hx = cx + math.cos(ha) * hr
            hy = cy + math.sin(ha) * hr
            line_alpha = int(50 + 40 * math.sin(t * 3.0 + i * 1.2))
            pygame.draw.line(screen, (140, 200, 255, line_alpha), (cx, cy), (hx, hy),
                             max(1, int(1 + fast_pulse)))

        # ── Ice crystal shards orbiting ──
        shard_count = 10
        for i in range(shard_count):
            shard_angle = t * 0.6 + i * (math.pi * 2 / shard_count)
            shard_dist = vr * (0.5 + 0.2 * math.sin(t * 2.0 + i * 1.5))
            sx = cx + math.cos(shard_angle) * shard_dist
            sy = cy + math.sin(shard_angle) * shard_dist
            shard_size = max(2, int(4 + 2 * math.sin(t * 3.0 + i * 2.0)))
            shard_alpha = int(120 + 80 * math.sin(t * 5.0 + i * 2.5))
            shard_color = (180, 220, 255, shard_alpha)
            pts = [
                (sx, sy - shard_size),
                (sx + shard_size * 0.6, sy),
                (sx, sy + shard_size),
                (sx - shard_size * 0.6, sy),
            ]
            pygame.draw.polygon(screen, shard_color[:3], pts)
            pygame.draw.polygon(screen, (220, 240, 255), pts, 1)

        # ── Falling snow particles ──
        if self.ice_armor_active:
            for _ in range(2):
                sn_angle = random.uniform(0, math.pi * 2)
                sn_dist = random.uniform(0, vr * 0.6)
                sn_x = cx + math.cos(sn_angle) * sn_dist
                sn_y = cy - vr * 0.5 + random.uniform(0, vr)
                sn_size = random.randint(1, 2)
                sn_alpha = int(100 + 80 * random.random())
                pygame.draw.circle(screen, (220, 240, 255, sn_alpha), (int(sn_x), int(sn_y)), sn_size)

        # ── Ice particles ──
        for p in self.ice_armor_particles:
            life_ratio = min(1.0, p["life"] / p["max_life"]) if p["max_life"] > 0 else 0
            if life_ratio <= 0:
                continue
            px = cx + math.cos(p["angle"]) * p["dist"]
            py = cy + math.sin(p["angle"]) * p["dist"] + p["vertical_speed"] * (1 - life_ratio) * 0.3
            alpha = int(200 * life_ratio)
            size = max(1, int(p["size"] * life_ratio))
            r, g, b = p["color"]

            if p.get("is_snow"):
                # Snowflake (cross shape)
                pygame.draw.line(screen, (r, g, b, alpha), (px - size, py), (px + size, py), 1)
                pygame.draw.line(screen, (r, g, b, alpha), (px, py - size), (px, py + size), 1)
            else:
                # Frost particle (circular with glow)
                glow_sz = size * 3
                glow = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow, (r, g, b, alpha // 3), (glow_sz, glow_sz), glow_sz)
                screen.blit(glow, (int(px - glow_sz), int(py - glow_sz)))
                if alpha > 20:
                    pygame.draw.circle(screen, (min(255, r + 40), min(255, g + 30), min(255, b + 10)),
                                       (int(px), int(py)), size)

        # ── Shield health indicator (frost cracks at edges) ──
        absorb_ratio = self.ice_armor_remaining_absorption / self.ice_armor_max_absorption
        if absorb_ratio < 0.5:
            crack_alpha = int(150 * (1.0 - absorb_ratio * 2))
            for _ in range(int(3 + 3 * (1 - absorb_ratio * 2))):
                crack_angle = random.uniform(0, math.pi * 2)
                crack_dist = vr
                cpx = cx + math.cos(crack_angle) * crack_dist
                cpy = cy + math.sin(crack_angle) * crack_dist
                # Longer cracks when more damaged
                crack_len = 2 + 4 * (1 - absorb_ratio * 2)
                pygame.draw.line(screen, (200, 220, 255, crack_alpha),
                                 (cpx - crack_len, cpy - crack_len),
                                 (cpx + crack_len, cpy + crack_len),
                                 max(1, int(1 + (1 - absorb_ratio * 2) * 2)))

        # ── Frost sparkles ──
        if self.ice_armor_active:
            for _ in range(3):
                sp_angle = random.uniform(0, math.pi * 2)
                sp_dist = random.uniform(0, vr * 0.4)
                sp_x = cx + math.cos(sp_angle) * sp_dist
                sp_y = cy + random.uniform(-15, 15)
                sp_size = random.randint(1, 2)
                sp_color = random.choice([(200, 240, 255), (160, 210, 255), (220, 250, 255)])
                pygame.draw.circle(screen, sp_color, (int(sp_x), int(sp_y)), sp_size)

    # ─── Mystic Barrier helpers ──────────────────────────────────────

    def _update_mystic_barrier_particles(self, dt):
        import random

        if self.mystic_barrier_active:
            spawn_count = max(1, int(18 * dt))
            for _ in range(spawn_count):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(20, 90)
                max_life = random.uniform(0.3, 0.8)
                is_shard = random.random() < 0.4
                self.mystic_barrier_particles.append({
                    "angle": angle,
                    "dist": dist,
                    "life": max_life,
                    "max_life": max_life,
                    "size": random.uniform(2.0, 5.0),
                    "drift": random.uniform(-15, 15),
                    "radial_vel": random.uniform(15, 50),
                    "rotation": random.uniform(0, math.pi * 2),
                    "rot_speed": random.uniform(-3, 3),
                    "is_shard": is_shard,
                    "color": random.choice([
                        (180, 120, 255),
                        (120, 80, 240),
                        (220, 180, 255),
                        (100, 200, 255),
                        (160, 100, 220),
                    ]),
                })

        for p in self.mystic_barrier_particles[:]:
            p["life"] -= dt
            if p["life"] <= 0:
                self.mystic_barrier_particles.remove(p)
                continue
            p["angle"] += p["drift"] * dt
            p["dist"] += p["radial_vel"] * dt
            p["rotation"] += p["rot_speed"] * dt

    def _draw_mystic_barrier(self, screen, camera_offset):
        import random
        center = self.get_center()
        cx = center.x - camera_offset.x
        cy = center.y - camera_offset.y
        t = pygame.time.get_ticks() / 1000.0

        radius = 85.0
        pulse = 0.6 + 0.4 * math.sin(t * 4.0)
        fast_pulse = 0.5 + 0.5 * math.sin(t * 10.0)

        # ── Crystalline hexagon shell ──
        hex_pts = []
        for i in range(6):
            a = t * 0.4 + i * (math.pi * 2 / 6)
            hr = radius * (0.85 + 0.15 * pulse)
            hx = cx + math.cos(a) * hr
            hy = cy + math.sin(a) * hr
            hex_pts.append((hx, hy))

        # Outer hexagon glow
        hex_surf = pygame.Surface((int(radius * 2.4), int(radius * 2.4)), pygame.SRCALPHA)
        hex_off = int(radius * 1.2)
        hex_glow_a = int(30 + 20 * pulse)
        pygame.draw.polygon(hex_surf, (100, 60, 200, hex_glow_a),
                           [(p[0] - cx + hex_off, p[1] - cy + hex_off) for p in hex_pts])
        pygame.draw.polygon(hex_surf, (160, 100, 240, int(hex_glow_a * 1.5)),
                           [(p[0] - cx + hex_off, p[1] - cy + hex_off) for p in hex_pts],
                           max(1, int(2 + fast_pulse * 2)))
        screen.blit(hex_surf, (cx - hex_off, cy - hex_off))

        # ── Inner glow hexagon ──
        inner_hr = radius * 0.65 * (0.9 + 0.1 * pulse)
        inner_pts = []
        for i in range(6):
            a = -t * 0.3 + i * (math.pi * 2 / 6)
            ix = cx + math.cos(a) * inner_hr
            iy = cy + math.sin(a) * inner_hr
            inner_pts.append((ix, iy))
        inner_surf = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
        inner_off = int(radius)
        inner_a = int(25 + 20 * pulse)
        pygame.draw.polygon(inner_surf, (180, 140, 255, inner_a),
                           [(p[0] - cx + inner_off, p[1] - cy + inner_off) for p in inner_pts])
        screen.blit(inner_surf, (cx - inner_off, cy - inner_off))

        # ── Connecting facet lines (from center to each vertex) ──
        for i in range(6):
            a = t * 0.4 + i * (math.pi * 2 / 6)
            hr = radius * (0.85 + 0.15 * pulse)
            hx = cx + math.cos(a) * hr
            hy = cy + math.sin(a) * hr
            line_alpha = int(60 + 50 * math.sin(t * 3.0 + i * 1.2))
            pygame.draw.line(screen, (200, 160, 255, line_alpha), (cx, cy), (hx, hy),
                             max(1, int(1 + fast_pulse)))

        # ── Hexagon edge connector lines ──
        for i in range(6):
            a1 = t * 0.4 + i * (math.pi * 2 / 6)
            a2 = t * 0.4 + (i + 1) * (math.pi * 2 / 6)
            hr = radius * (0.85 + 0.15 * pulse)
            x1 = cx + math.cos(a1) * hr
            y1 = cy + math.sin(a1) * hr
            x2 = cx + math.cos(a2) * hr
            y2 = cy + math.sin(a2) * hr
            edge_alpha = int(100 + 80 * math.sin(t * 5.0 + i * 1.8))
            pygame.draw.line(screen, (180, 140, 255, edge_alpha), (x1, y1), (x2, y2),
                             max(1, int(2 + fast_pulse)))

        # ── Rotating arcane glyphs at hex vertices ──
        for i in range(6):
            a = -t * 0.6 + i * (math.pi * 2 / 6)
            glyph_dist = radius * 0.78 + 6 * math.sin(t * 3.0 + i * 1.5)
            gx = cx + math.cos(a) * glyph_dist
            gy = cy + math.sin(a) * glyph_dist
            g_size = max(2, int(4 + 3 * math.sin(t * 4.0 + i * 2.0)))
            g_alpha = int(130 + 100 * math.sin(t * 5.0 + i * 2.5))
            # Triangle glyph
            tri_pts = []
            for j in range(3):
                ta = a + j * (math.pi * 2 / 3)
                tx = gx + math.cos(ta) * g_size
                ty = gy + math.sin(ta) * g_size
                tri_pts.append((tx, ty))
            pygame.draw.polygon(screen, (100, 200, 255, g_alpha), tri_pts)
            pygame.draw.polygon(screen, (180, 230, 255, g_alpha), tri_pts, 1)
            # Center dot
            pygame.draw.circle(screen, (220, 240, 255, g_alpha), (int(gx), int(gy)), max(1, g_size // 3))

        # ── Shard particles ──
        for p in self.mystic_barrier_particles:
            life_ratio = min(1.0, p["life"] / p["max_life"]) if p["max_life"] > 0 else 0
            if life_ratio <= 0:
                continue
            px = cx + math.cos(p["angle"]) * p["dist"]
            py = cy + math.sin(p["angle"]) * p["dist"]
            alpha = int(220 * life_ratio)
            size = max(1, int(p["size"] * life_ratio))
            r, g, b = p["color"]
            rot = p.get("rotation", 0)

            if p.get("is_shard"):
                # Draw as diamond shard with rotation
                pts = []
                for j in range(4):
                    sa = rot + j * (math.pi * 2 / 4)
                    sd = size * (1.5 if j % 2 == 0 else 0.8)
                    sx = px + math.cos(sa) * sd
                    sy = py + math.sin(sa) * sd
                    pts.append((sx, sy))
                shard_surf = pygame.Surface((int(size * 4), int(size * 4)), pygame.SRCALPHA)
                soff = size * 2
                rel_pts = [(p[0] - px + soff, p[1] - py + soff) for p in pts]
                pygame.draw.polygon(shard_surf, (r, g, b, alpha), rel_pts)
                pygame.draw.polygon(shard_surf, (min(255, r + 60), min(255, g + 60), min(255, b + 60), alpha), rel_pts, 1)
                screen.blit(shard_surf, (int(px - soff), int(py - soff)))
                # Glow
                g_sz = int(size * 2)
                g_surf = pygame.Surface((g_sz * 2, g_sz * 2), pygame.SRCALPHA)
                pygame.draw.circle(g_surf, (r, g, b, alpha // 3), (g_sz, g_sz), g_sz)
                screen.blit(g_surf, (int(px - g_sz), int(py - g_sz)))
            else:
                # Standard circular particle
                glow_sz = size * 3
                glow = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow, (r, g, b, alpha // 3), (glow_sz, glow_sz), glow_sz)
                screen.blit(glow, (int(px - glow_sz), int(py - glow_sz)))
                if alpha > 20:
                    pygame.draw.circle(screen, (min(255, r + 40), min(255, g + 30), min(255, b + 10)),
                                       (int(px), int(py)), size)

        # ── Protective glyph flashes ──
        if self.mystic_barrier_active:
            for _ in range(2):
                flash_angle = random.uniform(0, math.pi * 2)
                flash_dist = radius * (0.5 + 0.4 * random.random())
                fx = cx + math.cos(flash_angle) * flash_dist
                fy = cy + math.sin(flash_angle) * flash_dist
                f_size = random.randint(2, 4)
                f_alpha = int(100 + 100 * random.random())
                f_color = random.choice([
                    (180, 230, 255, f_alpha),
                    (140, 200, 255, f_alpha),
                    (220, 240, 255, f_alpha),
                ])
                # Draw as cross glyph
                pygame.draw.line(screen, f_color, (fx - f_size, fy), (fx + f_size, fy), 1)
                pygame.draw.line(screen, f_color, (fx, fy - f_size), (fx, fy + f_size), 1)

    # ─── Rainbow Aura helpers (Gay Ring) ─────────────────────────────────

    def _update_rainbow_aura_particles(self, dt):
        import random
        from src.items.items import GayRing
        colors = GayRing.RAINBOW_COLORS
        if self.rainbow_aura_active:
            spawn_count = max(1, int(8 * dt))
            for _ in range(spawn_count):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(30, 80)
                speed = random.uniform(20, 50)
                max_life = random.uniform(0.5, 1.0)
                self.rainbow_aura_particles.append({
                    "angle": angle,
                    "dist": dist,
                    "life": max_life,
                    "max_life": max_life,
                    "size": random.uniform(2.0, 5.0),
                    "drift": random.uniform(-10, 10),
                    "vertical_speed": -speed,
                    "color": random.choice(colors),
                    "color_index": random.randint(0, len(colors) - 1),
                })
        for p in self.rainbow_aura_particles[:]:
            p["life"] -= dt
            if p["life"] <= 0:
                self.rainbow_aura_particles.remove(p)
                continue
            p["angle"] += p["drift"] * dt
            p["dist"] = max(0, p["dist"] - 4 * dt)
            p["vertical_speed"] -= 80 * dt

    def _draw_rainbow_aura(self, screen, camera_offset):
        import random
        from src.items.items import GayRing
        center = self.get_center()
        cx = center.x - camera_offset.x
        cy = center.y - camera_offset.y
        t = pygame.time.get_ticks() / 1000.0
        colors = GayRing.RAINBOW_COLORS
        n_colors = len(colors)

        n = n_colors
        phase = (t * 1.5) % n
        ci = int(phase)
        frac = phase - ci
        c1 = colors[ci]
        c2 = colors[(ci + 1) % n]
        cur_color = (
            int(c1[0] + (c2[0] - c1[0]) * frac),
            int(c1[1] + (c2[1] - c1[1]) * frac),
            int(c1[2] + (c2[2] - c1[2]) * frac),
        )

        visual_radius = 80.0
        pulse_slow = 0.6 + 0.4 * math.sin(t * 2.0)
        pulse_fast = 0.5 + 0.5 * math.sin(t * 5.0)

        # ── Shimmer ring ──
        shimmer_surf = pygame.Surface((int(visual_radius * 2) + 20, int(visual_radius * 2) + 20), pygame.SRCALPHA)
        shimmer_a = int(15 + 10 * math.sin(t * 3.0))
        for i in range(3):
            r = visual_radius + i * 6 + 4 * math.sin(t * 4.0 + i * 2.0)
            ci2 = (ci + i) % n_colors
            sc = colors[ci2]
            pygame.draw.circle(shimmer_surf, (*sc, shimmer_a // (i + 1)),
                               (int(r) + 10, int(r) + 10), int(r), 1)
        screen.blit(shimmer_surf, (int(cx - visual_radius - 10), int(cy - visual_radius - 10)))

        # ── Inner pulsing glow ──
        glow_radius = visual_radius * (0.7 + 0.3 * pulse_slow)
        glow_surf = pygame.Surface((int(glow_radius * 2) + 8, int(glow_radius * 2) + 8), pygame.SRCALPHA)
        gc = int(glow_radius) + 4
        glow_a = int(35 + 25 * pulse_slow)
        pygame.draw.circle(glow_surf, (*cur_color, glow_a), (gc, gc), int(glow_radius))
        mid_r = int(glow_radius * 0.65)
        mid_a = int(25 + 20 * pulse_slow)
        ci3 = (ci + 2) % n_colors
        mc = colors[ci3]
        pygame.draw.circle(glow_surf, (*mc, mid_a), (gc, gc), mid_r)
        inner_r = int(glow_radius * 0.35)
        inner_a = int(20 + 15 * pulse_slow)
        ci4 = (ci + 4) % n_colors
        ic = colors[ci4]
        pygame.draw.circle(glow_surf, (*ic, inner_a), (gc, gc), inner_r)
        screen.blit(glow_surf, (int(cx - glow_radius - 4), int(cy - glow_radius - 4)))

        # ── Outer ring ──
        ring_r = visual_radius
        ring_a = int(60 + 40 * math.sin(t * 5.0))
        ring_surf = pygame.Surface((int(ring_r * 2) + 4, int(ring_r * 2) + 4), pygame.SRCALPHA)
        ring_width = max(1, int(2 + pulse_fast))
        ci5 = int(t * 0.5) % n_colors
        rc = colors[ci5]
        pygame.draw.circle(ring_surf, (*rc, ring_a), (int(ring_r) + 2, int(ring_r) + 2), int(ring_r), ring_width)
        if ring_width > 1:
            ci6 = (ci5 + 3) % n_colors
            rc2 = colors[ci6]
            pygame.draw.circle(ring_surf, (*rc2, ring_a // 2), (int(ring_r) + 2, int(ring_r) + 2), int(ring_r * 0.98), max(1, ring_width - 1))
        screen.blit(ring_surf, (int(cx - ring_r - 2), int(cy - ring_r - 2)))

        # ── Particles ──
        for p in self.rainbow_aura_particles:
            life_ratio = min(1.0, p["life"] / p["max_life"]) if p["max_life"] > 0 else 0
            if life_ratio <= 0:
                continue
            px = cx + math.cos(p["angle"]) * p["dist"]
            py = cy + math.sin(p["angle"]) * p["dist"] + p["vertical_speed"] * (1 - life_ratio) * 0.3
            alpha = int(200 * life_ratio)
            size = max(1, int(p["size"] * life_ratio))
            r, g, b = p["color"]
            glow_sz = size * 3
            glow = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (r, g, b, alpha // 3), (glow_sz, glow_sz), glow_sz)
            screen.blit(glow, (int(px - glow_sz), int(py - glow_sz)))
            if alpha > 20:
                pygame.draw.circle(screen, (min(255, r + 60), min(255, g + 60), min(255, b + 60)), (int(px), int(py)), size)

        # ── Sparkles ──
        for _ in range(3):
            sp_angle = random.uniform(0, math.pi * 2)
            sp_dist = random.uniform(0, visual_radius * 0.5)
            sp_x = cx + math.cos(sp_angle) * sp_dist
            sp_y = cy + random.uniform(-15, 15)
            sp_size = random.randint(1, 3)
            sp_ci = random.randint(0, n_colors - 1)
            sp_color = colors[sp_ci]
            pygame.draw.circle(screen, sp_color, (int(sp_x), int(sp_y)), sp_size)

    # ─── Chrono Shift helpers ─────────────────────────────────────────

    def _update_chrono_shift_particles(self, dt):
        if self.chrono_shift_active:
            spawn_count = max(1, int(25 * dt))
            for _ in range(spawn_count):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(10, 75)
                ml = random.uniform(0.2, 0.5)
                ptype = random.choices(
                    ["orbit", "spark", "dust"],
                    weights=[0.5, 0.3, 0.2],
                )[0]
                self.chrono_shift_particles.append({
                    "angle": angle,
                    "dist": dist,
                    "life": ml,
                    "max_life": ml,
                    "size": random.uniform(1.5, 4.5),
                    "drift": random.uniform(-80, -15),
                    "type": ptype,
                    "base_alpha": random.randint(150, 255),
                    "color": random.choice([
                        (255, 215, 0),
                        (255, 230, 80),
                        (255, 200, 40),
                        (255, 245, 200),
                        (255, 180, 20),
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
        center = self.get_center()
        cx = center.x - camera_offset.x
        cy = center.y - camera_offset.y
        t = pygame.time.get_ticks() / 1000.0

        radius = 90.0
        pulse = 0.5 + 0.5 * math.sin(t * 5.0)

        # ── Radiant gold light beams ──
        for bi in range(8):
            ba = t * 0.3 + bi * math.pi / 4
            ba_a = int(8 + 6 * math.sin(t * 2 + bi * 1.3))
            for bj in range(3):
                bd = radius * (0.3 + bj * 0.3)
                bx = cx + math.cos(ba) * bd
                by = cy + math.sin(ba) * bd
                bs = 3 + bj * 3
                pygame.draw.circle(screen, (255, 220, 100, ba_a), (int(bx), int(by)), bs)

        # ── Golden time ripple waves ──
        for ri in range(3):
            rp = (t * 1.5 + ri * 1.2) % 1.8
            rr = rp * radius * 1.3
            ra = int(50 * (1 - rp / 1.8))
            if ra > 0:
                rs = pygame.Surface((int(rr * 2) + 4, int(rr * 2) + 4), pygame.SRCALPHA)
                rc = rs.get_width() // 2
                pygame.draw.circle(rs, (255, 200, 50, ra), (rc, rc), int(rr), 1)
                pygame.draw.circle(rs, (255, 230, 150, ra // 2), (rc, rc), int(rr * 0.7), 1)
                screen.blit(rs, (cx - rc, cy - rc))

        # ── Golden ground clock face ──
        face_surf = pygame.Surface((int(radius * 2.6), int(radius * 2.6)), pygame.SRCALPHA)
        fc = face_surf.get_width() // 2
        pygame.draw.circle(face_surf, (80, 60, 10, 20), (fc, fc), int(radius * 1.15))
        pygame.draw.circle(face_surf, (120, 90, 20, 15), (fc, fc), int(radius * 0.9))
        pygame.draw.circle(face_surf, (200, 160, 30, 8), (fc, fc), int(radius * 0.65))
        screen.blit(face_surf, (cx - fc, cy - fc))

        # ── 3 Concentric gold gear rings ──
        ring_data = [
            (radius * 0.95, t * 0.4, 120, 255, 200, 50),
            (radius * 0.70, t * -0.6, 100, 255, 220, 80),
            (radius * 0.45, t * 0.8, 80, 255, 230, 120),
        ]
        for rr, rspeed, ra, *rgb in ring_data:
            ring_a = int(ra + 50 * math.sin(t * 6.0 + rspeed * 10))
            if ring_a <= 0:
                continue
            rs = pygame.Surface((int(rr * 2) + 8, int(rr * 2) + 8), pygame.SRCALPHA)
            rcx = rs.get_width() // 2
            rcy = rs.get_height() // 2
            pygame.draw.circle(rs, (*rgb, ring_a), (rcx, rcy), int(rr), max(1, int(2 + pulse)))
            for gi in range(20):
                ga = rspeed + gi * math.pi / 10
                gd = rr
                gx = rcx + math.cos(ga) * gd
                gy = rcy + math.sin(ga) * gd
                gs = 2 + (gi % 4)
                pygame.draw.circle(rs, (*rgb, ring_a), (int(gx), int(gy)), gs)
            screen.blit(rs, (cx - rcx, cy - rcy))

        # ── Outer gold gear teeth ──
        gear_a = int(70 + 40 * math.sin(t * 7.0))
        for gi in range(30):
            ga = t * 0.5 + gi * math.pi / 15
            gd = radius * 1.05
            inner_d = radius * 0.90
            gx1 = cx + math.cos(ga) * inner_d
            gy1 = cy + math.sin(ga) * inner_d
            gx2 = cx + math.cos(ga) * gd
            gy2 = cy + math.sin(ga) * gd
            gx3 = cx + math.cos(ga + 0.06) * gd
            gy3 = cy + math.sin(ga + 0.06) * gd
            tw = 2 if gi % 4 == 0 else 1
            pygame.draw.line(screen, (255, 200, 50, gear_a), (gx1, gy1), (gx2, gy2), tw)
            if gi % 2 == 0:
                pygame.draw.line(screen, (255, 230, 120, gear_a), (gx2, gy2), (gx3, gy3), 1)

        # ── Golden clock hands with glow trail ──
        for hand_len, hand_width, hand_color, speed in [
            (radius * 0.55, 3, (255, 215, 0), 2.0),
            (radius * 0.80, 2, (255, 200, 60), 1.2),
            (radius * 0.35, 2, (255, 240, 150), 4.0),
        ]:
            ha = t * speed
            hx = cx + math.cos(ha) * hand_len
            hy = cy + math.sin(ha) * hand_len
            for ti in range(4):
                ta = ha - 0.015 * (ti + 1)
                tax = cx + math.cos(ta) * hand_len * 0.85
                tay = cy + math.sin(ta) * hand_len * 0.85
                ta_a = 70 - ti * 15
                pygame.draw.line(screen, (*hand_color, ta_a), (cx, cy), (tax, tay), hand_width)
            pygame.draw.line(screen, hand_color, (cx, cy), (hx, hy), hand_width + 1)
            cap_size = 5 + hand_width
            pygame.draw.circle(screen, (255, 215, 0), (int(cx), int(cy)), cap_size)
            pygame.draw.circle(screen, (255, 245, 200), (int(cx), int(cy)), cap_size - 2)

        # ── Golden clock markers (12 outer + inner) ──
        for i in range(12):
            ma = t * 0.3 + i * math.pi / 6
            outer_dist = radius * 0.88
            inner_dist = radius * 0.60
            mxo = cx + math.cos(ma) * outer_dist
            myo = cy + math.sin(ma) * outer_dist
            mxi = cx + math.cos(ma) * inner_dist
            myi = cy + math.sin(ma) * inner_dist
            ma_a = int(150 + 70 * math.sin(t * 3 + i * 0.5))
            mw = 3 if i % 3 == 0 else 1
            ml = 8 if i % 3 == 0 else 4
            mo = math.cos(ma)
            ms = math.sin(ma)
            pygame.draw.line(screen, (255, 215, 0, ma_a),
                             (mxo - mo * ml, myo - ms * ml),
                             (mxo + mo * ml, myo + ms * ml), mw)
            if i % 3 == 0:
                pygame.draw.line(screen, (255, 240, 150, ma_a // 2),
                                 (mxi - mo * 2, myi - ms * 2),
                                 (mxi + mo * 2, myi + ms * 2), 1)

        # ── Golden time particles ──
        for p in self.chrono_shift_particles:
            life_ratio = p["life"] / p["max_life"] if p["max_life"] > 0 else 0
            if life_ratio <= 0:
                continue
            px = cx + math.cos(p["angle"]) * p["dist"]
            py = cy + math.sin(p["angle"]) * p["dist"]
            alpha = int(p.get("base_alpha", 180) * life_ratio)
            size = max(1, int(p["size"] * life_ratio))
            r, g, b = p["color"]
            ptype = p.get("type", "orbit")

            if ptype == "spark":
                # Star-spark shape
                for spi in range(4):
                    sa = p["angle"] * 3 + spi * math.pi / 2
                    sd = size * 1.5
                    spx = px + math.cos(sa) * sd
                    spy = py + math.sin(sa) * sd
                    pygame.draw.line(screen, (r, g, b, alpha),
                                     (int(px), int(py)),
                                     (int(spx), int(spy)), 1)
                pygame.draw.circle(screen, (r, g, b, alpha), (int(px), int(py)), size)
            elif ptype == "dust":
                # Tiny golden dust mote
                pygame.draw.circle(screen, (r, g, b, alpha // 2), (int(px), int(py)), size)
                if size > 1:
                    pygame.draw.circle(screen, (255, 255, 200, alpha // 3),
                                       (int(px), int(py)), size * 2)
            else:
                # Orbit glow
                glow_sz = size * 3
                glow = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow, (r, g, b, alpha // 3),
                                   (glow_sz, glow_sz), glow_sz)
                screen.blit(glow, (int(px - glow_sz), int(py - glow_sz)))
                pygame.draw.circle(screen, (min(255, r + 40), min(255, g + 30), min(255, b + 10)),
                                   (int(px), int(py)), size)

        # ── Golden sparkles ──
        if self.chrono_shift_active:
            for _ in range(6):
                sp_angle = random.uniform(0, math.pi * 2)
                sp_dist = random.uniform(0, radius * 0.7)
                sp_x = cx + math.cos(sp_angle) * sp_dist + random.uniform(-3, 3)
                sp_y = cy + random.uniform(-25, 25)
                sp_size = random.randint(1, 3)
                sp_color = random.choice([(255, 215, 0), (255, 240, 150), (255, 200, 40)])
                pygame.draw.circle(screen, sp_color, (int(sp_x), int(sp_y)), sp_size)
                # Tiny glow
                if sp_size > 1:
                    pygame.draw.circle(screen, (255, 255, 200, 40),
                                       (int(sp_x), int(sp_y)), sp_size + 2)
