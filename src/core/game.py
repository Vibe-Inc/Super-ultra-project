import math
import pygame
from typing import TYPE_CHECKING
import random

from src.core.logger import logger
import src.config as cfg
from src.core.state import State
from src.entities.character import Character
from src.map.map import LocalMap
from src.inventory.system import MAIN_player_inventory, MAIN_player_inventory_equipment, ShopInventory
from src.items.items import create_item
from src.items.effects import RegenerationEffect, PoisonEffect, ConfusionEffect, DizzinessEffect
from src.entities.enemy import Enemy
from src.entities.npc import NPC
from src.entities.projectile import Arrow
from src.ui.hud import HUD
from src.core.collision_system import CollisionSystem
from src.ai.navigation import NavGrid
from src.entities.monster_visuals import build_monster_animations
from src.entities.monster_attacks import build_attack_controller, AttackContext

if TYPE_CHECKING:
    from src.app import App

class Game(State):
    """
    Main gameplay state for the application.

    This class manages the core game loop, including the player character, map switching, enemy spawning, HUD, and inventory logic.

    Attributes:
        app (App): Reference to the main application instance.
        character (Character): The player character instance.
        map (LocalMap): The current game map.
        player_inventory_opened (bool): Whether the player's inventory is open.
        MAIN_player_inv: The main player inventory object.
        PLAYER_inventory_equipment: The player's equipment inventory object.
        ENEMY_SPAWNS (dict): Mapping of map paths to enemy spawn coordinates.
        hud (HUD): The heads-up display for the player.
        enemy (Enemy): The main enemy instance for the current map.

    Methods:
        __init__(app):
            Initialize the game state, character, map, HUD, and enemy.
        reinit_ui():
            Recreate the HUD (e.g., after language change).
        toggle_player_inventory():
            Toggle the player's inventory open/closed.
        draw(screen):
            Draw the game map, character, enemy, HUD, and inventory if open.
        handle_event(event):
            Handle Pygame events for HUD, inventory, and pause state.
    """
    def __init__(self, app: "App"):
        super().__init__(app)
        logger.info("Initializing Game State...")
        self.character = Character()

        initial_map_path = "maps/test-map-1.tmx"
        self.current_map_path = initial_map_path
        self.map = LocalMap("Level1", initial_map_path)

        self.collision_handler = CollisionSystem()
        
        self.obstacles = self.map.get_obstacles()
        self.nav_grid = None
        self._rebuild_nav_grid()

        self.player_inventory_opened = app.INV_manager.player_inventory_opened

        self.MAIN_player_inv = MAIN_player_inventory(app)
        self.PLAYER_inventory_equipment = MAIN_player_inventory_equipment(app)
        self.projectiles = []
        self.enemy_projectiles = []
        self.equipped_weapon = None
        self._dizzy_overlay = None

        self.game_time_seconds = 6 * 3600  # Start at 06:00
        self.GAME_DAY_SECONDS = 24 * 3600
        self.DAY_CYCLE_REAL_SECONDS = 12 * 60  # 12 real-life minutes for full 24h cycle
        self.GAME_SECONDS_PER_REAL_SECOND = self.GAME_DAY_SECONDS / self.DAY_CYCLE_REAL_SECONDS
        self.DAY_START = 6 * 3600
        self.DUSK_START = 16 * 3600
        self.NIGHT_START = 18 * 3600
        self.DAWN_START = 4 * 3600
        self.NIGHT_BRIGHTNESS = 0.4

        self.enemy_profiles = {
            "brute": {
                "visual_style": "brute",
                "sprite_set": "MenHuman1",
                "speed": 110.0,
                "hp": 160,
                "damage": 20,
                "animation_speed": 5.0,
                "detection_range": 240.0,
                "attack_range": 45.0,
                "ai_profile": "guardian",
                "attack_profile": "brute",
                "attack_config": {
                    "cooldown_ms": 1100,
                    "charge_cooldown_ms": 2400,
                    "charge_duration": 0.7,
                    "charge_speed_mult": 2.4,
                    "slam_damage_mult": 1.5,
                    "slow_duration": 1.5,
                    "slow_factor": 0.6,
                },
                "contact_damage": False,
            },
            "venomous": {
                "visual_style": "venomous",
                "sprite_set": "MenHuman1(Recolor)",
                "speed": 130.0,
                "hp": 95,
                "damage": 12,
                "animation_speed": 6.5,
                "detection_range": 260.0,
                "attack_range": 38.0,
                "ai_profile": "stalker",
                "attack_profile": "venomous",
                "attack_config": {
                    "cooldown_ms": 900,
                    "poison_duration": 4.0,
                    "poison_dps": 5.0,
                    "strike_damage_mult": 0.85,
                },
                "contact_damage": False,
            },
            "arcanist": {
                "visual_style": "arcanist",
                "sprite_set": "WomanHuman1",
                "speed": 115.0,
                "hp": 80,
                "damage": 14,
                "animation_speed": 6.2,
                "detection_range": 300.0,
                "attack_range": 40.0,
                "ai_profile": "stalker",
                "attack_profile": "arcanist",
                "attack_config": {
                    "cooldown_ms": 950,
                    "bolt_speed": 480.0,
                    "bolt_range": 560.0,
                    "bolt_damage_mult": 0.85,
                    "burn_duration": 3.2,
                    "burn_dps": 4.5,
                    "cast_range": 340.0,
                    "spread_degrees": 5.0,
                },
                "contact_damage": False,
            },
            "trickster": {
                "visual_style": "trickster",
                "sprite_set": "WomanHuman1(Recolor)",
                "speed": 150.0,
                "hp": 75,
                "damage": 10,
                "animation_speed": 7.5,
                "detection_range": 280.0,
                "attack_range": 35.0,
                "ai_profile": "skirmisher",
                "attack_profile": "trickster",
                "attack_config": {
                    "cooldown_ms": 1800,
                    "step_range": 240.0,
                    "step_distance": 55.0,
                    "step_attempts": 6,
                    "step_spread_degrees": 110.0,
                    "strike_range": 75.0,
                    "confuse_duration": 2.8,
                    "dizzy_duration": 2.2,
                    "damage_mult": 0.7,
                },
                "contact_damage": False,
            },
            "bomber": {
                "visual_style": "bomber",
                "sprite_set": "MenHuman1",
                "speed": 105.0,
                "hp": 125,
                "damage": 16,
                "animation_speed": 6.0,
                "detection_range": 320.0,
                "attack_range": 35.0,
                "ai_profile": "skirmisher",
                "ai_config": {
                    "preferred_min": 120.0,
                    "preferred_max": 220.0,
                    "orbit_radius": 180.0,
                },
                "attack_profile": "bomber",
                "attack_config": {
                    "cooldown_ms": 1400,
                    "throw_range": 320.0,
                    "min_range": 90.0,
                    "bomb_speed": 260.0,
                    "bomb_range": 420.0,
                    "blast_radius": 95.0,
                    "fuse_time": 0.9,
                    "damage_mult": 1.1,
                    "knockback_force": 80.0,
                    "spread_degrees": 12.0,
                },
                "contact_damage": False,
            },
            "stalker": {
                "sprite_set": "MenHuman1(Recolor)",
                "speed": 120.0,
                "hp": 110,
                "damage": 15,
                "animation_speed": 6.0,
                "detection_range": 260.0,
                "attack_range": 40.0,
                "ai_config": {
                    "memory_duration": 3.0,
                    "repath_interval": 0.5,
                },
            },
            "skirmisher": {
                "sprite_set": "WomanHuman1(Recolor)",
                "speed": 140.0,
                "hp": 85,
                "damage": 10,
                "animation_speed": 7.0,
                "detection_range": 300.0,
                "attack_range": 35.0,
                "ai_config": {
                    "preferred_min": 80.0,
                    "preferred_max": 170.0,
                    "orbit_radius": 130.0,
                },
            },
            "guardian": {
                "sprite_set": "MenHuman1",
                "speed": 100.0,
                "hp": 140,
                "damage": 18,
                "animation_speed": 5.0,
                "detection_range": 220.0,
                "attack_range": 45.0,
                "patrol_radius": 120.0,
                "ai_config": {
                    "guard_radius": 320.0,
                    "leash_slack": 90.0,
                    "patrol_wait": 0.8,
                },
            },
        }
        self.enemy_profile_names = list(self.enemy_profiles.keys())

        self.ENEMY_SPAWNS = {
            # "maps/test-map-1.tmx": (400, 300), # Якщо закоментувати цей рядок, ворога на старті не буде
            "maps/test-map-2.tmx": {"pos": (600, 450), "profile": "trickster"},
            "maps/test-map-3.tmx": {"pos": (300, 200), "profile": "skirmisher"},
        }

        self.NPC_SPAWNS = {
            "maps/test-map-1.tmx": (400, 400)
        }

        # Maps where enemy spawning (both default and random) is disabled
        self.NO_ENEMY_SPAWN_MAPS = {"maps/tavern.tmx", "maps/test-map-1.tmx"}

        spawn_info = self._get_spawn_info(initial_map_path)
        if initial_map_path in self.NO_ENEMY_SPAWN_MAPS:
            spawn_info = None
        if spawn_info:
            start_x, start_y = spawn_info["pos"]
            default_profile = spawn_info.get("profile")
        else:
            start_x, start_y = -5000, -5000
            default_profile = None

        self.hud = HUD(self.character, app, self.toggle_player_inventory, self.use_skill_slot)

        self.enemy = self._create_enemy(start_x, start_y, profile=default_profile)
        
        self.enemies = [self.enemy]
        self.items = []
        
        # Enemy spawning system
        self.enemy_spawn_timer = 0.0
        self.enemy_spawn_interval = 30.0 # seconds

        if initial_map_path in self.NPC_SPAWNS:
            npc_x, npc_y = self.NPC_SPAWNS[initial_map_path]
        else:
            npc_x, npc_y = -5000, -5000

        self.npc = NPC(x=npc_x, y=npc_y, sprite_set="MenHuman1")
        
        shop_items = [
            create_item("dull_sword"),
            create_item("wooden_bow"),
            create_item("apple"),
            create_item("small_health_potion"),
            create_item("large_health_potion"),
            create_item("large_health_potion"),
            create_item("large_health_potion"),
            create_item("potion_of_confusion"),
            create_item("moldy_bread")
            ]

        self.shop_inv = ShopInventory(self.app, shop_items)

    def reinit_ui(self):
        self.hud = HUD(self.character, self.app, self.toggle_player_inventory, self.use_skill_slot)

        self.MAIN_player_inv.pos_x = cfg.MAIN_INV_pos_x
        self.MAIN_player_inv.pos_y = cfg.MAIN_INV_pos_y
        self.PLAYER_inventory_equipment.pos_x = cfg.MAIN_INV_equipment_pos_x
        self.PLAYER_inventory_equipment.pos_y = cfg.MAIN_INV_equipment_pos_y

        if self.app.INV_manager.current_shop_inv:
            self.MAIN_player_inv.pos_x = cfg.SCREEN_WIDTH // 2 - 500
            self.app.INV_manager.current_shop_inv.pos_x = cfg.SCREEN_WIDTH // 2 + 100
            self.app.INV_manager.current_shop_inv.pos_y = self.MAIN_player_inv.pos_y

    def toggle_player_inventory(self):
        self.app.INV_manager.toggle_inventory(self.MAIN_player_inv, self.PLAYER_inventory_equipment)

    def use_skill_slot(self, slot_index):
        return self.character.use_skill_from_slot(slot_index)

    def _iter_equipment_items(self):
        for col in self.PLAYER_inventory_equipment.items:
            for slot in col:
                if slot:
                    item, _ = slot
                    yield item

    def _get_equipped_weapon(self):
        for item in self._iter_equipment_items():
            if getattr(item, "type", None) == "weapon":
                return item
        return None

    def _sync_weapon_stats(self):
        weapon = self._get_equipped_weapon()
        self.equipped_weapon = weapon

        if weapon:
            self.character.attack_damage = weapon.damage
            self.character.attack_cooldown = getattr(weapon, "cooldown", self.character.base_attack_cooldown)
            if getattr(weapon, "weapon_class", "melee") != "bow":
                self.character.attack_range = getattr(weapon, "range", self.character.base_attack_range)
            else:
                self.character.attack_range = self.character.base_attack_range
        else:
            self.character.attack_damage = self.character.base_attack_damage
            self.character.attack_range = self.character.base_attack_range
            self.character.attack_cooldown = self.character.base_attack_cooldown

    def _get_attack_direction(self):
        return self.character.get_forward_direction()

    def _get_attack_origin(self):
        return self.character.get_center()

    def _get_mouse_aim_direction(self, mouse_pos):
        origin = self._get_attack_origin()
        direction = pygame.Vector2(mouse_pos) - origin
        if direction.length_squared() == 0:
            return self._get_attack_direction()
        return direction.normalize()

    def _clamp_direction_to_cone(self, aim_dir, forward_dir, half_angle_deg):
        if half_angle_deg <= 0:
            return pygame.Vector2(forward_dir)

        if forward_dir.length_squared() == 0:
            forward_dir = pygame.Vector2(1, 0)
        else:
            forward_dir = forward_dir.normalize()

        if aim_dir.length_squared() == 0:
            return pygame.Vector2(forward_dir)

        aim_dir = aim_dir.normalize()
        cross = forward_dir.x * aim_dir.y - forward_dir.y * aim_dir.x
        dot = forward_dir.dot(aim_dir)
        angle = math.degrees(math.atan2(cross, dot))

        if abs(angle) <= half_angle_deg:
            return aim_dir

        return forward_dir.rotate(half_angle_deg if angle > 0 else -half_angle_deg)

    def _spawn_arrow(self, weapon, direction):
        direction = pygame.Vector2(direction)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        else:
            direction = direction.normalize()

        spawn_pos = self._get_attack_origin() + direction * 40
        speed = getattr(weapon, "projectile_speed", 800) or 800
        max_range = getattr(weapon, "range", 500)
        damage = getattr(weapon, "damage", self.character.attack_damage)
        self.projectiles.append(Arrow(spawn_pos, direction, speed, max_range, damage))

    def _update_projectiles(self, dt):
        if not self.projectiles:
            return

        for projectile in self.projectiles:
            projectile.update(dt, self.obstacles, self.enemies)

        self.projectiles = [projectile for projectile in self.projectiles if projectile.alive]

    def _update_enemy_projectiles(self, dt):
        if not self.enemy_projectiles:
            return

        for projectile in self.enemy_projectiles:
            projectile.update(dt, self.obstacles, self.character)

        self.enemy_projectiles = [projectile for projectile in self.enemy_projectiles if projectile.alive]

    def _rebuild_nav_grid(self):
        tmx_data = self.map.current_map.get_tmx_data()
        if not tmx_data:
            self.nav_grid = None
            return
        self.nav_grid = NavGrid.from_tmx(tmx_data, self.obstacles)

    def _format_game_time(self) -> str:
        hours = int(self.game_time_seconds // 3600) % 24
        minutes = int((self.game_time_seconds % 3600) // 60)
        return f"{hours:02d}:{minutes:02d}"

    def is_daytime(self) -> bool:
        return self.DAY_START <= self.game_time_seconds < self.NIGHT_START

    def _update_game_time(self, dt: float):
        self.game_time_seconds = (self.game_time_seconds + dt * self.GAME_SECONDS_PER_REAL_SECOND) % self.GAME_DAY_SECONDS

        if self.DUSK_START <= self.game_time_seconds < self.NIGHT_START:
            t = (self.game_time_seconds - self.DUSK_START) / (self.NIGHT_START - self.DUSK_START)
            cfg.ENVIRONMENT_BRIGHTNESS = 1.0 - t * (1.0 - self.NIGHT_BRIGHTNESS)
        elif self.NIGHT_START <= self.game_time_seconds or self.game_time_seconds < self.DAWN_START:
            cfg.ENVIRONMENT_BRIGHTNESS = self.NIGHT_BRIGHTNESS
        elif self.DAWN_START <= self.game_time_seconds < self.DAY_START:
            t = (self.game_time_seconds - self.DAWN_START) / (self.DAY_START - self.DAWN_START)
            cfg.ENVIRONMENT_BRIGHTNESS = self.NIGHT_BRIGHTNESS + t * (1.0 - self.NIGHT_BRIGHTNESS)
        else:
            cfg.ENVIRONMENT_BRIGHTNESS = 1.0

        self.app.profiler.set_gauge("game_time", self._format_game_time())

    def _get_spawn_info(self, map_path: str) -> dict | None:
        spawn = self.ENEMY_SPAWNS.get(map_path)
        if not spawn:
            return None
        if isinstance(spawn, dict):
            return spawn
        return {"pos": spawn, "profile": "stalker"}

    def _get_camera_offset(self) -> pygame.Vector2:
        viewport_width, viewport_height = self.app.screen.get_size()

        map_width = viewport_width
        map_height = viewport_height
        if self.map.current_map and self.map.current_map.pixel_width and self.map.current_map.pixel_height:
            map_width = self.map.current_map.pixel_width
            map_height = self.map.current_map.pixel_height

        camera_x = int(self.character.get_center().x - viewport_width / 2)
        camera_y = int(self.character.get_center().y - viewport_height / 2)

        max_x = max(0, map_width - viewport_width)
        max_y = max(0, map_height - viewport_height)

        camera_x = max(0, min(camera_x, max_x))
        camera_y = max(0, min(camera_y, max_y))

        return pygame.Vector2(camera_x, camera_y)

    def _make_patrol_points(self, center: pygame.Vector2, radius: float) -> list[tuple[float, float]]:
        return [
            (center.x - radius, center.y - radius),
            (center.x + radius, center.y - radius),
            (center.x + radius, center.y + radius),
            (center.x - radius, center.y + radius),
        ]

    def _create_enemy(self, x: float, y: float, profile: str | None = None) -> Enemy:
        profile_name = profile or random.choice(self.enemy_profile_names)
        if profile_name not in self.enemy_profiles:
            profile_name = "stalker"

        settings = self.enemy_profiles[profile_name]
        ai_profile = settings.get("ai_profile", profile_name)
        attack_profile = settings.get("attack_profile")
        attack_controller = None
        if attack_profile:
            attack_controller = build_attack_controller(attack_profile, settings.get("attack_config"))
        contact_damage = settings.get("contact_damage", True)
        visual_style = settings.get("visual_style")
        animations = None
        if visual_style:
            animations = build_monster_animations(visual_style, (85, 85))
        sprite_set = settings.get("sprite_set", "MenHuman1(Recolor)")
        patrol_points = settings.get("patrol_points")
        if patrol_points is None and profile_name == "guardian":
            radius = float(settings.get("patrol_radius", 120.0))
            patrol_points = self._make_patrol_points(pygame.Vector2(x, y), radius)

        enemy = Enemy(
            x=x,
            y=y,
            sprite_set=sprite_set,
            speed=settings["speed"],
            hp=settings["hp"],
            damage=settings["damage"],
            animation_size=(85, 85),
            animation_speed=settings.get("animation_speed", 6.0),
            detection_range=settings.get("detection_range", 250.0),
            attack_range=settings.get("attack_range", 40.0),
            patrol_points=patrol_points,
            ai_profile=ai_profile,
            ai_config=settings.get("ai_config"),
            animations=animations,
            attack_controller=attack_controller,
            contact_damage=contact_damage,
        )
        enemy.target_entity = self.character
        return enemy

    def _handle_player_attack(self, mouse_pos):
        weapon = self.equipped_weapon or self._get_equipped_weapon()
        if not weapon:
            return

        aim_dir = self._get_mouse_aim_direction(mouse_pos)

        if getattr(weapon, "weapon_class", "melee") == "bow":
            if not self.character.can_attack():
                return
            self.character.start_attack(show_slash=False)
            spread = float(getattr(weapon, "spread_degrees", 4.0))
            if spread:
                aim_dir = aim_dir.rotate(random.uniform(-spread, spread))
            self._spawn_arrow(weapon, aim_dir)
            return

        cone_degrees = float(getattr(weapon, "cone_degrees", 90.0))
        forward_dir = self._get_attack_direction()
        clamped_dir = self._clamp_direction_to_cone(aim_dir, forward_dir, cone_degrees * 0.5)
        self.character.attack(self.enemies, aim_direction=clamped_dir, cone_degrees=cone_degrees)

    def spawn_random_enemy(self):
        if not self.map.current_map or self.map.current_map.pixel_width == 0:
            return

        map_w = self.map.current_map.pixel_width
        map_h = self.map.current_map.pixel_height
        
        # Try 10 times to find a valid position
        for _ in range(10):
            x = random.randint(50, map_w - 50)
            y = random.randint(50, map_h - 50)
            pos = pygame.Vector2(x, y)
            
            # Check distance to player (must be at least 400 pixels away)
            pdiff = pos - self.character.pos
            if pdiff.length_squared() < 400 * 400:
                continue
                
            # Check collision with walls
            # Using approximate size for enemy feet/hitbox
            rect = pygame.Rect(x, y, 40, 20) 
            collides = False
            for wall in self.obstacles:
                if rect.colliderect(wall):
                    collides = True
                    break

            if self.nav_grid and not self.nav_grid.is_walkable(self.nav_grid.world_to_cell(pos)):
                collides = True
            
            if not collides:
                # Spawn enemy
                new_enemy = self._create_enemy(x, y)
                self.enemies.append(new_enemy)
                logger.info(f"Spawned new enemy at ({x}, {y})")
                break

    def update(self, dt):
        switched_map_path = self.map.update(self.character)

        if switched_map_path:
            self.current_map_path = switched_map_path
            logger.info(f"Map switched to {switched_map_path}. Respawning enemy...")
            self.obstacles = self.map.get_obstacles()
            self._rebuild_nav_grid()
            
            # Reset enemies list and spawn default one if needed
            self.enemies = []
            
            spawn_info = self._get_spawn_info(switched_map_path)
            if switched_map_path not in self.NO_ENEMY_SPAWN_MAPS and spawn_info:
                new_x, new_y = spawn_info["pos"]
                profile = spawn_info.get("profile")
                default_enemy = self._create_enemy(new_x, new_y, profile=profile)
                self.enemies.append(default_enemy)

            if switched_map_path in self.NPC_SPAWNS:
                npc_x, npc_y = self.NPC_SPAWNS[switched_map_path]
                self.npc.pos = pygame.Vector2(npc_x, npc_y)
            else:
                self.npc.pos = pygame.Vector2(-5000, -5000)
        
        # Enemy Spawning Logic
        self._update_game_time(dt)

        self.enemy_spawn_timer += dt
        if self.enemy_spawn_timer >= self.enemy_spawn_interval:
            self.enemy_spawn_timer = 0
            # Skip periodic/random spawns on maps where spawning is disabled
            if self.current_map_path not in self.NO_ENEMY_SPAWN_MAPS:
                self.spawn_random_enemy()

        self._sync_weapon_stats()

        self.character.update(dt, self.collision_handler, self.obstacles)

        now_ms = pygame.time.get_ticks()
        attack_context = AttackContext(
            dt=dt,
            player=self.character,
            obstacles=self.obstacles,
            projectiles=self.enemy_projectiles,
            now_ms=now_ms,
        )
        # Update enemies with LOD: skip heavy updates for distant enemies
        LOD_DISTANCE = 800.0
        lod_sq = LOD_DISTANCE * LOD_DISTANCE
        player_pos = self.character.pos
        for enemy in self.enemies:
            ediff = enemy.pos - player_pos
            active = ediff.length_squared() <= lod_sq
            enemy.update(dt, self.collision_handler, self.obstacles, self.nav_grid, attack_context, active=active)

        self._update_projectiles(dt)
        self._update_enemy_projectiles(dt)

        self.collision_handler.check_interactions(
            self.character, self.enemies, self.items
        )

        # Remove dead enemies
        for enemy in self.enemies[:]:
            if enemy.is_dead():
                logger.info("Enemy defeated!")
                
                # Random XP [30, 60]
                xp_gain = random.randint(30, 60)
                self.character.gain_xp(xp_gain)
                
                # Random Money [5, 20]
                money_gain = random.randint(5, 20)
                self.app.money += money_gain
                logger.info(f"Gained {money_gain} money. Total: {self.app.money}")
                
                self.enemies.remove(enemy)

        self.npc.update(self.character.pos)

        self.app.profiler.set_gauge("enemies", len(self.enemies))
        self.app.profiler.set_gauge("projectiles", len(self.projectiles))
        self.app.profiler.set_gauge("enemy_projectiles", len(self.enemy_projectiles))

    def draw_scene(self, screen):
        dt = self.app.clock.get_time() / 1000
        self.app.profiler.start_section("game.update")
        self.update(dt)
        self.app.profiler.end_section("game.update")

        self.app.profiler.start_section("game.draw")
        camera_offset = self._get_camera_offset()
        viewport_rect = pygame.Rect(0, 0, screen.get_width(), screen.get_height())

        def _is_visible(entity) -> bool:
            rect = entity.get_rect()
            rect.x -= int(camera_offset.x)
            rect.y -= int(camera_offset.y)
            return rect.colliderect(viewport_rect)

        self.map.draw(screen, camera_offset)

        self.character.draw(screen, camera_offset)

        for enemy in self.enemies:
            if _is_visible(enemy):
                enemy.draw(screen, camera_offset)

        for projectile in self.projectiles:
            if _is_visible(projectile):
                projectile.draw(screen, camera_offset)

        for projectile in self.enemy_projectiles:
            if _is_visible(projectile):
                projectile.draw(screen, camera_offset)

        self.npc.draw(screen, camera_offset)

        self.map.draw_fringe_overlay(screen, camera_offset, self.character)

        if not self.npc.is_interactable:
            if getattr(self.app.INV_manager, 'current_shop_inv', None) is not None:
                self.app.INV_manager.toggle_trade(self.MAIN_player_inv, self.shop_inv)

        # Dizziness effect (visual)
        if self.character.dizzy:
            alpha = int(100 + 50 * math.sin(pygame.time.get_ticks() * 0.005))
            if self._dizzy_overlay is None or self._dizzy_overlay.get_size() != screen.get_size():
                self._dizzy_overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            self._dizzy_overlay.fill((255, 255, 255, alpha))
            screen.blit(self._dizzy_overlay, (0, 0))

        self.app.profiler.end_section("game.draw")

    def draw_ui(self, screen):
        self.hud.draw(screen)
        if self.app.INV_manager.player_inventory_opened:
            self.app.INV_manager.draw(screen)

    def draw(self, screen):
        self.draw_scene(screen)
        self.draw_ui(screen)

    def handle_event(self, event: pygame.event.Event):
        self.hud.handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.manager.set_state("pause")

            if event.key == pygame.K_1:
                self.use_skill_slot(0)
            if event.key == pygame.K_2:
                self.use_skill_slot(1)
            if event.key == pygame.K_3:
                self.use_skill_slot(2)
            if event.key == pygame.K_4:
                self.use_skill_slot(3)
            if event.key == pygame.K_5:
                self.use_skill_slot(4)
            if event.key == pygame.K_6:
                self.use_skill_slot(5)
            
            if event.key == pygame.K_e:
                # If NPC is interactable -> open/close trade regardless of inventory state
                if self.npc.is_interactable:
                    self.app.INV_manager.toggle_trade(self.MAIN_player_inv, self.shop_inv)
                else:
                    # Otherwise toggle the player's inventory (open/close)
                    self.app.INV_manager.toggle_inventory(self.MAIN_player_inv, self.PLAYER_inventory_equipment)
            
            # Test keys
            if event.key == pygame.K_F1:
                self.character.add_effect(RegenerationEffect(5, 5)) # 5 sec, 5 hp/sec
            if event.key == pygame.K_F2:
                self.character.add_effect(PoisonEffect(5, 5)) # 5 sec, 5 dmg/sec
            if event.key == pygame.K_F3:
                self.character.add_effect(ConfusionEffect(5)) # 5 sec
            if event.key == pygame.K_F4:
                self.character.add_effect(DizzinessEffect(5)) # 5 sec
            if event.key == pygame.K_F5:
                self.character.take_damage(10)
            if event.key == pygame.K_F6:
                self.character.gain_xp(50)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.app.INV_manager.player_inventory_opened:
                # If a shop is open, skill slots should not be considered HUD clicks
                hud_click = self.hud.inv_button.rect.collidepoint(event.pos) or (
                    not getattr(self.app.INV_manager, 'current_shop_inv', None) and any(slot.collidepoint(event.pos) for slot in self.hud.skill_slot_rects)
                )
                if not hud_click:
                    mouse_world_pos = pygame.Vector2(event.pos) + self._get_camera_offset()
                    self._handle_player_attack(mouse_world_pos)

        self.app.INV_manager.PLAYER_inventory_open(event, self.MAIN_player_inv, self.PLAYER_inventory_equipment)

