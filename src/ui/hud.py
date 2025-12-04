import pygame
from typing import TYPE_CHECKING
from src.entities.character import Character

if TYPE_CHECKING:
    from src.app import App


class HUD:
    def __init__(self, character: Character, app: "App"):
        self.character = character
        self.app = app
        try:
            self.font = pygame.font.Font("fonts/menu_font.ttf", 40)
        except FileNotFoundError:
            self.font = pygame.font.SysFont("Arial", 40)

        try:
            self.hp_icon = pygame.image.load("assets/heart.png")
            self.hp_icon = pygame.transform.scale(self.hp_icon, (50, 50))
        except FileNotFoundError:
            self.hp_icon = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(self.hp_icon, (255, 0, 0), (25, 25), 25)

        try:
            self.life_icon = pygame.image.load("assets/skull.png")
            self.life_icon = pygame.transform.scale(self.life_icon, (50, 50))
        except FileNotFoundError:
            self.life_icon = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(self.life_icon, (200, 200, 200), (25, 25), 25)

    def handle_event(self, event: pygame.event.Event):
        pass

    def draw(self, screen: pygame.Surface):
        icon_x, icon_y = 200, 120
        screen.blit(self.hp_icon, (icon_x, icon_y))

        bar_x = icon_x + 60
        bar_y = icon_y + 10
        bar_width = 300
        bar_height = 30

        hp_percent = max(0, self.character.hp / 100.0)
        current_bar_width = int(bar_width * hp_percent)

        # Draw Background
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        # Draw HP
        pygame.draw.rect(screen, (220, 20, 60), (bar_x, bar_y, current_bar_width, bar_height))
        # Draw Border
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 3)

        lives_icon_x = icon_x
        lives_icon_y = icon_y + 60

        screen.blit(self.life_icon, (lives_icon_x, lives_icon_y))

        lives_text = self.font.render(f"x {self.character.death_count}", True, (255, 255, 255))
        screen.blit(lives_text, (lives_icon_x + 60, lives_icon_y + 5))
