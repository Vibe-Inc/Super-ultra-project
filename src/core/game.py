import pygame
from typing import TYPE_CHECKING

from src.core.state import State
from src.entities.character import Character
from src.map.map import LocalMap
from src.inventory.system import MAIN_player_inventory, MAIN_player_inventory_equipment
from src.entities.enemy import Enemy
from src.entities.npc import NPC
from src.ui.hud import HUD

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
        self.character = Character()

        initial_map_path = "maps/test-map-1.tmx"
        self.map = LocalMap("Level1", initial_map_path)

        self.player_inventory_opened = app.INV_manager.player_inventory_opened

        self.MAIN_player_inv = MAIN_player_inventory(app)
        self.PLAYER_inventory_equipment = MAIN_player_inventory_equipment(app)

        self.ENEMY_SPAWNS = {
            # "maps/test-map-1.tmx": (400, 300), # Якщо закоментувати цей рядок, ворога на старті не буде
            "maps/test-map-2.tmx": (600, 450), 
            "maps/test-map-3.tmx": (300, 200)
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

        self.npc = NPC(x=400, y=400, sprite_set="MenHuman1")

    def reinit_ui(self):
        self.hud = HUD(self.character, self.app, self.toggle_player_inventory)

    def toggle_player_inventory(self):
        self.app.INV_manager.toggle_inventory(self.MAIN_player_inv, self.PLAYER_inventory_equipment)

    def draw(self, screen):
        switched_map_path = self.map.update(self.character)

        if switched_map_path:
            print(f"Map switched to {switched_map_path}. Respawning enemy...")
            
            if switched_map_path in self.ENEMY_SPAWNS:
                new_x, new_y = self.ENEMY_SPAWNS[switched_map_path]
                self.enemy.pos = pygame.Vector2(new_x, new_y)
                self.enemy.spawn_pos = pygame.Vector2(new_x, new_y)

                self.enemy.target = None
                self.enemy.ai_state = "idle"
            else:
                self.enemy.pos = pygame.Vector2(-5000, -5000)

        self.map.draw(screen)

        dt = self.app.clock.get_time() / 1000
        self.character.update(dt)
        self.character.draw(screen)

        self.enemy.update(dt)
        self.enemy.draw(screen)

        self.npc.update(self.character.pos)
        self.npc.draw(screen)

        self.hud.draw(screen)

        if  self.app.INV_manager.player_inventory_opened:
            self.app.INV_manager.draw(screen)

    def handle_event(self, event: pygame.event.Event):
        self.hud.handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.manager.set_state("pause")

        self.app.INV_manager.PLAYER_inventory_open(event, self.MAIN_player_inv, self.PLAYER_inventory_equipment)

