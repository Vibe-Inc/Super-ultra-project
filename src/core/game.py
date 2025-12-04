import pygame
from typing import TYPE_CHECKING

from src.core.state import State
from src.entities.character import Character
# ЗМІНА 1: Імпортуємо LocalMap
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
        
        # ЗМІНА 2: Використовуємо LocalMap для підтримки переходів
        self.map = LocalMap("Level1", "maps/test-map-1.tmx")

        self.player_inventory_opened = app.INV_manager.player_inventory_opened

        self.MAIN_player_inv = MAIN_player_inventory(app)
        self.PLAYER_inventory_equipment = MAIN_player_inventory_equipment(app)
        self.enemy = Enemy(
            x=400, y=300,
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
        # ЗМІНА 3: Оновлюємо мапу (тут відбувається перевірка переходів)
        self.map.update(self.character)
        
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