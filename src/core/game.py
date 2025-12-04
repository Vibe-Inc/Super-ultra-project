import pygame
from typing import TYPE_CHECKING

from src.core.state import State
from src.entities.character import Character
from src.map.map import LocalMap
from src.inventory.system import MAIN_player_inventory, MAIN_player_inventory_equipment
from src.entities.enemy import Enemy
from src.ui.hud import HUD

if TYPE_CHECKING:
    from src.app import App

class Game(State):
    def __init__(self, app: "App"):
        super().__init__(app)
        self.character = Character()
        self.hud = HUD(self.character, app)
        
        # Початкова карта
        initial_map_path = "maps/test-map-1.tmx"
        self.map = LocalMap("Level1", initial_map_path)

        self.player_inventory_opened = app.INV_manager.player_inventory_opened

        self.MAIN_player_inv = MAIN_player_inventory(app)
        self.PLAYER_inventory_equipment = MAIN_player_inventory_equipment(app)
        
        # === КРОК 1: Визначаємо місця спавну ДО створення ворога ===
        self.ENEMY_SPAWNS = {
            # "maps/test-map-1.tmx": (400, 300), # Якщо закоментувати цей рядок, ворога на старті не буде
            "maps/test-map-2.tmx": (600, 450), 
            "maps/test-map-3.tmx": (300, 200)
        }

        # === КРОК 2: Визначаємо стартову позицію ===
        # Перевіряємо, чи є ворог на поточній карті (initial_map_path)
        if initial_map_path in self.ENEMY_SPAWNS:
            start_x, start_y = self.ENEMY_SPAWNS[initial_map_path]
        else:
            # Якщо спавну для цієї карти немає, ховаємо ворога далеко
            start_x, start_y = -5000, -5000

        # Створюємо ворога з правильними координатами
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

    def draw(self, screen):
        # 1. Оновлюємо мапу і перевіряємо, чи був перехід
        switched_map_path = self.map.update(self.character)
        
        # 2. Якщо перехід відбувся, рухаємо ворога
        if switched_map_path:
            print(f"Map switched to {switched_map_path}. Respawning enemy...")
            
            if switched_map_path in self.ENEMY_SPAWNS:
                # Беремо нові координати зі словника
                new_x, new_y = self.ENEMY_SPAWNS[switched_map_path]
                self.enemy.pos = pygame.Vector2(new_x, new_y)
                self.enemy.spawn_pos = pygame.Vector2(new_x, new_y)
                
                # Скидаємо агресію ворога
                self.enemy.target = None
                self.enemy.ai_state = "idle"
            else:
                # Ховаємо ворога далеко, якщо для цієї карти немає спавну
                self.enemy.pos = pygame.Vector2(-5000, -5000)

        # 3. Малюємо все інше
        self.map.draw(screen)

        dt = self.app.clock.get_time() / 1000
        self.character.update(dt)
        self.character.draw(screen)

        self.enemy.update(dt)
        self.enemy.draw(screen)

        self.hud.draw(screen)

        if self.app.INV_manager.player_inventory_opened:
            self.MAIN_player_inv.draw(screen)
            self.PLAYER_inventory_equipment.draw(screen)

    def handle_event(self, event: pygame.event.Event):
        self.hud.handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.manager.set_state("pause")

            self.app.INV_manager.PLAYER_inventory_open(event, self.MAIN_player_inv, self.PLAYER_inventory_equipment)