import pygame
from typing import TYPE_CHECKING

from src.ui.menus.base import Menu
from src.ui.widgets import Button
import src.config as cfg

if TYPE_CHECKING:
    from src.app import App


class PauseMenu(Menu):
    """
    Pause menu for the game, providing options to resume gameplay or return to the main menu.

    Attributes:
        app (App):
            Reference to the main application instance.
        pause_menu_color (tuple):
            RGBA color for the pause menu overlay.
        buttons (list[Button]):
            List of Button objects for menu actions ("RESUME" and "MAIN MENU").

    Methods:
        draw(screen):
            Draw the pause menu overlay and its buttons.
            Args:
                screen (pygame.Surface): The surface to draw the pause menu on.
        resume_game():
            Resume gameplay by setting the application state to "gameplay".
        back_to_main():
            Return to the main menu by setting the application state to "main".
    """

    def __init__(self, app: "App"):
        self.app = app

        scale = cfg.ui_scale()
        button_width, button_height = max(1,int(360 * scale)), max(1,int(120 * scale))

        self.pause_menu_color = (0, 0, 0, 180)

        cx = (cfg.SCREEN_WIDTH - button_width) // 2
        self.buttons = [
            Button(
                pygame.Rect(cx, int(500 * scale), button_width, button_height),
                _("SAVE"),
                cfg.button_color_SETTINGS,
                cfg.button_hover_color_SETTINGS,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.open_save_menu
            ),
            Button(
                pygame.Rect(cx, int(650 * scale), button_width, button_height),
                _("WIKI"),
                cfg.button_color_CREDITS,
                cfg.button_hover_color_CREDITS,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.open_wiki
            ),
            Button(
                pygame.Rect(cx, int(800 * scale), button_width, button_height),
                _("RESUME"),
                cfg.button_color_START,
                cfg.button_hover_color_START,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.resume_game
            ),
            Button(
                pygame.Rect(cx, int(950 * scale), button_width, button_height),
                _("MAIN MENU"),
                cfg.button_color_EXIT,
                cfg.button_hover_color_EXIT,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.back_to_main
            )
        ]

    def draw(self, screen):
        self.layout(screen)
        overlay = pygame.Surface((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(self.pause_menu_color)
        screen.blit(overlay, (0, 0))

        for button in self.buttons:
            button.draw(screen)

    def layout(self, screen: pygame.Surface):
        sw, sh = self._screen_size(screen)
        scale = cfg.ui_scale()
        button_width, button_height = max(1,int(360 * scale)), max(1,int(120 * scale))
        center_x = sw // 2
        positions = [
            (center_x - button_width // 2, int(sh * 0.42)),
            (center_x - button_width // 2, int(sh * 0.56)),
            (center_x - button_width // 2, int(sh * 0.70)),
            (center_x - button_width // 2, int(sh * 0.84)),
        ]
        for button, (x, y) in zip(self.buttons, positions):
            button.rect = pygame.Rect(x, y, button_width, button_height)
            try:
                button._update_text_surface()
            except Exception:
                pass

    def open_save_menu(self):
        self.app.manager.states["save_load"].mode = "save"
        self.app.manager.states["save_load"].refresh_saves()
        self.app.manager.set_state("save_load")

    def open_wiki(self):
        self.app.manager.set_state("wiki")

    def resume_game(self):
        self.app.manager.set_state("gameplay")

    def back_to_main(self):
        self.app.manager.set_state("main")