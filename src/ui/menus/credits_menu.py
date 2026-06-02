import pygame
from typing import TYPE_CHECKING

from src.ui.menus.base import Menu
from src.ui.widgets import Button
import src.config as cfg

if TYPE_CHECKING:
    from src.app import App


class CreditsMenu(Menu):
    """
    Credits screen with styled box, multi-line text, and a BACK button.

    Attributes:
        buttons (list[Button]):
            List of Button objects (only BACK).
        credits_text (str):
            The credits text, with lines separated by '\\n'.
        font (pygame.font.Font):
            Font used for the credits text.
        font_color (tuple):
            Color of the credits text.
        padding (int):
            Padding around the text inside the box.
        credits_lines (list[str]):
            List of lines in the credits text.
        box_rect (pygame.Rect):
            Rectangle for the credits box.
        box_color (tuple):
            Background color of the credits box.
        box_border (tuple):
            Border color of the credits box.

    Methods:
        draw(screen):
            Draw the credits box, text, and BACK button.
            Args:
                screen (pygame.Surface): The surface to draw the credits on.
        back_to_main():
            Return to the main menu.
    """

    def __init__(self, app: "App"):
        super().__init__(app)
        scale = cfg.ui_scale()
        button_width, button_height = max(1,int(360 * scale)), max(1,int(120 * scale))
        back_rect = pygame.Rect(0, 0, button_width, button_height)
        self.buttons = [
            Button(back_rect,
                _("BACK"),
                cfg.button_color_SETTINGS_BACK,
                cfg.button_hover_color_SETTINGS_BACK,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.back_to_main
            )
        ]
        self.credits_text = _("""CREDITS:
Vibe inc idea, production and execution
Art not by Vibe inc
Music not by Vibe inc
Main sponsor: Vibe inc
Special thanks to Vibe inc""")
        self.font :pygame.font.Font= cfg.myfont
        self.font_color: tuple = cfg.text_color
        self.padding: int = 30
        self.credits_lines = self.credits_text.split('\n')
        num_credits_lines = len(self.credits_lines)
        line_height = self.font.get_height()
        max_width = max(self.font.size(line)[0] for line in self.credits_lines)if num_credits_lines else 0
        box_width = max_width + 2 * self.padding
        box_height = line_height * num_credits_lines + 2 * self.padding
        self.box_rect = pygame.Rect(
            (cfg.SCREEN_WIDTH - box_width) // 2, int(250 * cfg.ui_scale()), box_width, box_height)
        self.box_color = (245, 222, 179) 
        self.box_border = (139, 49, 19)

    def layout(self, screen: pygame.Surface):
        sw, sh = self._screen_size(screen)
        scale = cfg.ui_scale()
        btn_w, btn_h = max(1,int(360 * scale)), max(1,int(120 * scale))
        self.buttons[0].rect = pygame.Rect(sw - int(420 * scale), sh - int(170 * scale), btn_w, btn_h)
        try:
            self.buttons[0]._update_text_surface()
        except Exception:
            pass
        self.box_rect = pygame.Rect(
            (sw - self.box_rect.width) // 2,
            int(sh * 0.28),
            min(self.box_rect.width, sw - 180),
            self.box_rect.height,
        )

    def draw(self, screen):
        self.layout(screen)
        pygame.draw.rect(screen, self.box_color, self.box_rect, border_radius=15)
        pygame.draw.rect(screen, self.box_border, self.box_rect, 10, border_radius=15)

        y = self.box_rect.y + self.padding
        box_width = self.box_rect.width - 2 * self.padding
        for line in self.credits_lines:
            surf = self.font.render(line, True, self.font_color)
            line_width = surf.get_width()
            x = self.box_rect.x + self.padding + (box_width - line_width) // 2
            screen.blit(surf, (x, y))
            y += self.font.get_height()
        for button in self.buttons:
            button.draw(screen)

    def back_to_main(self):
        self.app.manager.set_state("main")