import pygame
import sys
from typing import TYPE_CHECKING

from src.ui.widgets import Button, Tooltip, Slider
from src.core.state import State
import src.config as cfg

if TYPE_CHECKING:
    from src.app import App

class Menu(State):
    """
    Represents a menu interface containing interactive buttons.
    Attributes:
        app (App): Reference to the main application instance.
        buttons (list[Button]): List of Button objects displayed in the menu.
        tooltips: list[Tooltip] List of Tooltip objects for button tooltips.
    Methods:
        draw(screen):
            Draws all buttons onto the provided screen surface.
        handle_event(event):
            Handles pygame events, triggering button actions when clicked.
    """
    
    def __init__(self, app: "App"):
        self.app = app
        self.buttons: list[Button] = []
        self.tooltips: list[Tooltip] = []

    def draw(self, screen):
        for button in self.buttons:
            button.draw(screen)
        mouse_pos = pygame.mouse.get_pos()
        for tooltip in self.tooltips:
            tooltip.hover_update(mouse_pos)
            tooltip.draw(screen)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for button in self.buttons:
                if button.rect.collidepoint(event.pos):
                    button.on_click()


class MainMenu(Menu):
    """
    MainMenu class represents the main menu screen of the application, inheriting from the Menu base class.
    Attributes:
        buttons (list): A list of Button objects representing the interactive buttons on the main menu.
    Args:
        app (App): The main application instance, providing configuration and resources for the menu.
    Methods:
        start_game():
            Callback for the "START" button. Initiates the game start sequence.
        exit_game():
            Callback for the "EXIT" button. Exits the application by quitting pygame and terminating the process.
        open_settings():
            Callback for the "SETTINGS" button. Switches the current menu to the settings menu.
    """

    def __init__(self, app: "App"):
        super().__init__(app)

        button_width, button_height = 300, 100
        gap = 50
        tot_width = 2 * button_width + gap
        
        start_rect = pygame.Rect((cfg.SCREEN_WIDTH - tot_width) // 2, 700, button_width, button_height)
        exit_rect = pygame.Rect((cfg.SCREEN_WIDTH - tot_width) // 2 + button_width + gap, 700, button_width, button_height)
        settings_rect = pygame.Rect((cfg.SCREEN_WIDTH - tot_width) // 2, 850, button_width, button_height)
        credits_rect = pygame.Rect((cfg.SCREEN_WIDTH - tot_width) // 2 + button_width + gap, 850, button_width, button_height)

        self.buttons = [
            Button(
                start_rect,
                "START",
                cfg.button_color_START,
                cfg.button_hover_color_START,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.start_game
            ),
            Button(
                exit_rect,
                "EXIT",
                cfg.button_color_EXIT,
                cfg.button_hover_color_EXIT,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.exit_game
            ),
            Button(
                settings_rect,
                "SETTINGS",
                cfg.button_color_SETTINGS,
                cfg.button_hover_color_SETTINGS,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.open_settings
            ),
           Button(
                credits_rect,
                "CREDITS",
                cfg.button_color_CREDITS,
                cfg.button_hover_color_CREDITS,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.open_credits
            )
        ]
        self.beta_logo_img = pygame.image.load("assets/beta_logo.png")
        self.beta_logo_img = pygame.transform.scale(self.beta_logo_img, (200, 200))
        self.beta_logo_rect = self.beta_logo_img.get_rect(center=(1600, 900))

        self.tooltips = [
            Tooltip(
                self.beta_logo_rect,
                "Our logo that we need to think of",
                cfg.tooltip_bg_CREDITS,
                cfg.tooltip_border_CREDITS,
                cfg.tooltip_font_CREDITS,
                cfg.text_color,
                cfg.tooltip_appear,
                cfg.tooltip_padding
            )
        ]

    def draw(self, screen):
        screen.blit(self.beta_logo_img, self.beta_logo_rect, )
        for button in self.buttons:
            button.draw(screen)
        mouse_pos = pygame.mouse.get_pos()
        for tooltip in self.tooltips:
            tooltip.hover_update(mouse_pos)
            tooltip.draw(screen)

    def start_game(self):
        self.app.manager.set_state("gameplay")

    def exit_game(self):
        pygame.quit()
        sys.exit()

    def open_settings(self):
        self.app.manager.set_state("settings")

    def open_credits(self):
        self.app.manager.set_state("credits")


class SettingsMenu(Menu):
    """
    SettingsMenu is a subclass of Menu that provides a settings interface for the application.
    Attributes:
        buttons (list): A list of Button objects representing the settings options (Audio, Fullscreen, Back).
    Methods:
        __init__(app: "App"):
            Initializes the SettingsMenu with buttons for toggling audio, toggling fullscreen mode, and returning to the main menu.
        toggle_audio():
            Toggles the application's audio setting between "on" and "off", and prints the current state.
        toggle_fullscreen():
            Toggles the application's display mode between fullscreen and windowed, and prints the current state.
        back_to_main():
            Switches the current menu back to the main menu.
    """

    def __init__(self, app: "App"):
        super().__init__(app)
        button_width, button_height = 300, 100
        button_y = 700
        back_rect = pygame.Rect(1000, button_y, button_width, button_height)

        self.buttons = [
            Button(
                back_rect,
                "BACK",
                cfg.button_color_SETTINGS_BACK,
                cfg.button_hover_color_SETTINGS_BACK,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.back_to_main
            )
        ]

        track_colour = (0, 0, 0)
        knob_colour = (255, 255, 255)
        initial_volume = pygame.mixer.music.get_volume() if pygame.mixer.get_init() else 0.3

        self.audio_slider = Slider(600, 730, 40, 5,
                                   track_colour, knob_colour,
                                   20, 20,
                                   300, value=initial_volume)

        self.myfont = pygame.font.Font("fonts/menu_font.ttf", 60)
        self.text_logo = cfg.myfont.render('Music volume', True, (0, 0, 0))
        self.text_rect = cfg.text_logo.get_rect(center=(760, 650))

    def back_to_main(self):
        self.app.manager.set_state("main")
    
    def handle_event(self, event):
        super().handle_event(event)
        self.audio_slider.handle_event(event)

    def update(self):
        if hasattr(self.audio_slider, "update"):
            self.audio_slider.update()

    def draw(self, surface):
        for button in self.buttons:
            button.draw(surface)
        self.audio_slider.draw(surface)
        surface.blit(self.text_logo, self.text_rect)


class CreditsMenu(Menu):
    """
    CreditsMenu displays a credits screen with a styled box containing multi-line text and a BACK button.

    Attributes:
        buttons (list[Button]): List of buttons in the menu (only BACK).
        credits_text (str): The credits text, with lines separated by '\n'.
        font (pygame.font.Font): Font used for the credits text.
        font_color (tuple): Color of the credits text.
        padding (int): Padding around the text inside the box.
        credits_lines (list[str]): List of lines in the credits text.
        box_rect (pygame.Rect): Rectangle for the credits box.
        box_color (tuple): Background color of the credits box.
        box_border (tuple): Border color of the credits box.

    Methods:
        draw(screen): Draws the credits box, text, and BACK button.
        back_to_main(): Returns to the main menu.
    """
    def __init__(self, app: "App"):
        super().__init__(app)
        button_width, button_height = 300, 100
        back_rect = pygame.Rect(1400, 850, button_width, button_height)
        self.buttons = [
            Button(back_rect,
                "BACK",
                cfg.button_color_SETTINGS_BACK,
                cfg.button_hover_color_SETTINGS_BACK,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.back_to_main
            )
        ]
        self.credits_text = """CREDITS:\nVibe inc idea, production and execution\nArt not by Vibe inc\nMusic not by Vibe inc\nMain sponsor: Vibe inc\nSpecial thanks to Vibe inc"""
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
            (cfg.SCREEN_WIDTH - box_width) // 2, 300, box_width, box_height)
        self.box_color = (245, 222, 179) 
        self.box_border = (139, 49, 19)

    def draw(self, screen):
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


class PauseMenu(Menu):
    """
    Represents the pause menu in the game, providing options to resume gameplay or return to the main menu.
    Args:
        app (App): The main application instance containing configuration and state management.
    Attributes:
        app (App): Reference to the main application instance.
        pause_menu_color (tuple): RGBA color for the pause menu overlay.
        buttons (list[Button]): List of Button objects for menu actions ("RESUME" and "MAIN MENU").
    Methods:
        draw(screen):
            Draws the pause menu overlay and its buttons on the provided screen surface.
        resume_game():
            Callback to resume gameplay by setting the application state to "gameplay".
        back_to_main():
            Callback to return to the main menu by setting the application state to "main".
    """

    def __init__(self, app: "App"):
        self.app = app

        button_width, button_height = 300, 100

        self.pause_menu_color = (0, 0, 0, 180)

        self.buttons = [
            Button(
                pygame.Rect((cfg.SCREEN_WIDTH - button_width) // 2, 650, button_width, button_height),
                "RESUME",
                cfg.button_color_START,
                cfg.button_hover_color_START,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.resume_game
            ),
            Button(
                pygame.Rect((cfg.SCREEN_WIDTH - button_width) // 2, 800, button_width, button_height),
                "MAIN MENU",
                cfg.button_color_EXIT,
                cfg.button_hover_color_EXIT,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.back_to_main
            )
        ]

    def draw(self, screen):
        overlay = pygame.Surface((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(self.pause_menu_color)
        screen.blit(overlay, (0, 0))

        for button in self.buttons:
            button.draw(screen)


    def resume_game(self):
        self.app.manager.set_state("gameplay")

    def back_to_main(self):
        self.app.manager.set_state("main")
