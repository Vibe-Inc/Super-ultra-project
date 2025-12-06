import pygame
from typing import TYPE_CHECKING
import random

from src.core.logger import logger
from src.core.state import State
from src.entities.character import Character
from src.map.map import LocalMap
from src.inventory.system import MAIN_player_inventory, MAIN_player_inventory_equipment, ShopInventory
from src.items.items import create_item
from src.items.effects import RegenerationEffect, PoisonEffect, ConfusionEffect, DizzinessEffect
from src.entities.enemy import Enemy
from src.entities.npc import NPC
from src.ui.hud import HUD
from src.core.collision_system import CollisionSystem

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

        self.player_inventory_opened = app.INV_manager.player_inventory_opened

        self.MAIN_player_inv = MAIN_player_inventory(app)
        self.PLAYER_inventory_equipment = MAIN_player_inventory_equipment(app)

        self.ENEMY_SPAWNS = {
            # "maps/test-map-1.tmx": (400, 300), # Якщо закоментувати цей рядок, ворога на старті не буде
            "maps/test-map-2.tmx": (600, 450), 
            "maps/test-map-3.tmx": (300, 200)
        }

        self.NPC_SPAWNS = {
            "maps/test-map-1.tmx": (400, 400)
        }

        if initial_map_path in self.ENEMY_SPAWNS:
            start_x, start_y = self.ENEMY_SPAWNS[initial_map_path]
        else:
            start_x, start_y = -5000, -5000

        self.hud = HUD(self.character, app, self.toggle_player_inventory)

        self.enemy = Enemy(
            x=start_x, y=start_y,
            sprite_set="MenHuman1(Recolor)",
            speed=120.0,
            hp=100,
            damage=15,
            animation_size=(85, 85),
            animation_speed=6.0,
            detection_range=250.0,
            attack_range=40.0
        )
        self.enemy.target_entity = self.character
        
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
        self.hud = HUD(self.character, self.app, self.toggle_player_inventory)

    def toggle_player_inventory(self):
        self.app.INV_manager.toggle_inventory(self.MAIN_player_inv, self.PLAYER_inventory_equipment)

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
            if pos.distance_to(self.character.pos) < 400:
                continue
                
            # Check collision with walls
            # Using approximate size for enemy feet/hitbox
            rect = pygame.Rect(x, y, 40, 20) 
            collides = False
            for wall in self.obstacles:
                if rect.colliderect(wall):
                    collides = True
                    break
            
            if not collides:
                # Spawn enemy
                new_enemy = Enemy(
                    x=x, y=y,
                    sprite_set="MenHuman1(Recolor)",
                    speed=120.0,
                    hp=100,
                    damage=15,
                    animation_size=(85, 85),
                    animation_speed=6.0,
                    detection_range=250.0,
                    attack_range=40.0
                )
                new_enemy.target_entity = self.character
                self.enemies.append(new_enemy)
                logger.info(f"Spawned new enemy at ({x}, {y})")
                break

    def update(self, dt):
        switched_map_path = self.map.update(self.character)

        if switched_map_path:
            self.current_map_path = switched_map_path
            logger.info(f"Map switched to {switched_map_path}. Respawning enemy...")
            self.obstacles = self.map.get_obstacles()
            
            # Reset enemies list and spawn default one if needed
            self.enemies = []
            
            if switched_map_path in self.ENEMY_SPAWNS:
                new_x, new_y = self.ENEMY_SPAWNS[switched_map_path]
                default_enemy = Enemy(
                    x=new_x, y=new_y,
                    sprite_set="MenHuman1(Recolor)",
                    speed=120.0,
                    hp=100,
                    damage=15,
                    animation_size=(85, 85),
                    animation_speed=6.0,
                    detection_range=250.0,
                    attack_range=40.0
                )
                default_enemy.target_entity = self.character
                self.enemies.append(default_enemy)

            if switched_map_path in self.NPC_SPAWNS:
                npc_x, npc_y = self.NPC_SPAWNS[switched_map_path]
                self.npc.pos = pygame.Vector2(npc_x, npc_y)
            else:
                self.npc.pos = pygame.Vector2(-5000, -5000)
        
        # Enemy Spawning Logic
        self.enemy_spawn_timer += dt
        if self.enemy_spawn_timer >= self.enemy_spawn_interval:
            self.enemy_spawn_timer = 0
            self.spawn_random_enemy()

        # Update player damage based on equipment
        total_damage = self.character.base_attack_damage
        for col in self.PLAYER_inventory_equipment.items:
            for slot in col:
                if slot:
                    item, count = slot
                    if hasattr(item, 'damage'):
                        total_damage += item.damage
        self.character.attack_damage = total_damage

        self.character.update(dt, self.collision_handler, self.obstacles)

        for enemy in self.enemies:
            enemy.update(dt, self.collision_handler, self.obstacles)

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

    def draw(self, screen):
        dt = self.app.clock.get_time() / 1000
        self.update(dt)

        self.map.draw(screen)

        self.character.draw(screen)

        for enemy in self.enemies:
            enemy.draw(screen)

        self.npc.draw(screen)

        if not self.npc.is_interactable:
            if getattr(self.app.INV_manager, 'current_shop_inv', None) is not None:
                self.app.INV_manager.toggle_trade(self.MAIN_player_inv, self.shop_inv)

        # Dizziness effect (visual)
        if self.character.dizzy:
            # Simulate blur/dizziness with a semi-transparent overlay that changes alpha
            import math
            alpha = int(100 + 50 * math.sin(pygame.time.get_ticks() * 0.005))
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, alpha))
            screen.blit(overlay, (0, 0))

        self.hud.draw(screen)

        if  self.app.INV_manager.player_inventory_opened:
            self.app.INV_manager.draw(screen)

    def handle_event(self, event: pygame.event.Event):
        self.hud.handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.manager.set_state("pause")
            
            # Combat input
            if event.key == pygame.K_SPACE:
                self.character.attack(self.enemies)

            if event.key == pygame.K_e and self.app.INV_manager.player_inventory_opened == False:
                if self.npc.is_interactable:
                    self.app.INV_manager.toggle_trade(self.MAIN_player_inv, self.shop_inv)
            
            # Test keys
            if event.key == pygame.K_1:
                self.character.add_effect(RegenerationEffect(5, 5)) # 5 sec, 5 hp/sec
            if event.key == pygame.K_2:
                self.character.add_effect(PoisonEffect(5, 5)) # 5 sec, 5 dmg/sec
            if event.key == pygame.K_3:
                self.character.add_effect(ConfusionEffect(5)) # 5 sec
            if event.key == pygame.K_4:
                self.character.add_effect(DizzinessEffect(5)) # 5 sec
            if event.key == pygame.K_5:
                self.character.take_damage(10)
            if event.key == pygame.K_6:
                self.character.gain_xp(50)

        self.app.INV_manager.PLAYER_inventory_open(event, self.MAIN_player_inv, self.PLAYER_inventory_equipment)

