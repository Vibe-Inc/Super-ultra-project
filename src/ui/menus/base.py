import pygame
from typing import TYPE_CHECKING

from src.ui.widgets import Button, Tooltip
import src.config as cfg

if TYPE_CHECKING:
    from src.app import App


class Menu:
    """
    Base class for menu interfaces containing interactive buttons and tooltips.

    Attributes:
        app (App):
            Reference to the main application instance.
        buttons (list[Button]):
            List of Button objects displayed in the menu.
        tooltips (list[Tooltip]):
            List of Tooltip objects for button tooltips.

    Methods:
        draw(screen):
            Draw all buttons and tooltips onto the provided screen surface.
            Args:
                screen (pygame.Surface): The surface to draw the menu on.
        handle_event(event):
            Handle Pygame events, triggering button actions when clicked.
            Args:
                event (pygame.event.Event): The Pygame event to process.
    """
    
    def __init__(self, app: "App"):
        self.app = app
        self.buttons: list[Button] = []
        self.tooltips: list[Tooltip] = []

    def _apply_button_size(self, button: Button, rect: pygame.Rect):
        button.rect = rect
        try:
            button._update_text_surface()
        except Exception:
            pass

    def _screen_size(self, screen: pygame.Surface | None = None) -> tuple[int, int]:
        if screen is not None:
            return screen.get_width(), screen.get_height()
        try:
            return self.app.screen.get_width(), self.app.screen.get_height()
        except Exception:
            return cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT

    def draw(self, screen):
        # keep UI aligned to the actual screen size
        self.layout(screen)
        for button in self.buttons:
            button.draw(screen)
        mouse_pos = pygame.mouse.get_pos()
        for tooltip in self.tooltips:
            tooltip.hover_update(mouse_pos)
            tooltip.draw(screen)

    def layout(self, screen: pygame.Surface):
        # default menus don't need extra layout; subclasses override this
        return

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for button in self.buttons:
                if button.rect.collidepoint(event.pos):
                    button.on_click()