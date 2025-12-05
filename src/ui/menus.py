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
    Main menu screen of the application.

    Inherits from Menu and provides buttons for starting the game, exiting, opening settings, and viewing credits.

    Attributes:
        buttons (list[Button]):
            List of Button objects for main menu actions.
        beta_logo_img (pygame.Surface):
            Image for the beta logo.
        beta_logo_rect (pygame.Rect):
            Rectangle for positioning the beta logo.
        tooltips (list[Tooltip]):
            List of Tooltip objects for the beta logo.

    Methods:
        start_game():
            Callback for the "START" button. Initiates the game start sequence.
        exit_game():
            Callback for the "EXIT" button. Exits the application.
        open_settings():
            Callback for the "SETTINGS" button. Opens the settings menu.
        open_credits():
            Callback for the "CREDITS" button. Opens the credits menu.
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
                _("START"),
                cfg.button_color_START,
                cfg.button_hover_color_START,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.start_game
            ),
            Button(
                exit_rect,
                _("EXIT"),
                cfg.button_color_EXIT,
                cfg.button_hover_color_EXIT,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.exit_game
            ),
            Button(
                settings_rect,
                _("SETTINGS"),
                cfg.button_color_SETTINGS,
                cfg.button_hover_color_SETTINGS,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.open_settings
            ),
           Button(
                credits_rect,
                _("CREDITS"),
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
                _("Our logo that we need to think of"),
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
    Settings menu interface for the application.

    Inherits from Menu and provides sliders and buttons for adjusting audio, brightness, language, and returning to the main menu.

    Attributes:
        buttons (list[Button]):
            List of Button objects for settings options.
        brightness_slider (Slider):
            Slider for adjusting screen brightness.
        audio_slider (Slider):
            Slider for adjusting music volume.
        myfont (pygame.font.Font):
            Font used for labels.
        brightness_label (pygame.Surface):
            Rendered label for brightness.
        brightness_rect (pygame.Rect):
            Rectangle for positioning the brightness label.
        text_logo (pygame.Surface):
            Rendered label for music volume.
        text_rect (pygame.Rect):
            Rectangle for positioning the music volume label.

    Methods:
        back_to_main():
            Return to the main menu.
        toggle_language():
            Toggle the application language.
        handle_event(event):
            Handle slider and button events.
            Args:
                event (pygame.event.Event): The Pygame event to process.
        update():
            Update the audio slider if needed.
        draw(surface):
            Draw all settings controls and labels.
            Args:
                surface (pygame.Surface): The surface to draw the settings menu on.
    """

    def __init__(self, app: "App"):
        super().__init__(app)
        button_width, button_height = 300, 100
        button_y = 700
        back_rect = pygame.Rect(1000, button_y, button_width, button_height)
        lang_rect = pygame.Rect(1000, 550, button_width, button_height)

        self.buttons = [
            Button(
                back_rect,
                _("BACK"),
                cfg.button_color_SETTINGS_BACK,
                cfg.button_hover_color_SETTINGS_BACK,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.back_to_main
            ),
            Button(
                lang_rect,
                f"{_('LANG')}: {cfg.LANGUAGE.upper()}",
                cfg.button_color_SETTINGS,
                cfg.button_hover_color_SETTINGS,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.toggle_language
            )
        ]

        track_colour = (0, 0, 0)
        knob_colour = (255, 255, 255)
        initial_volume = pygame.mixer.music.get_volume() if pygame.mixer.get_init() else 0.3

        self.brightness_slider = Slider(
            600, 550, 40, 5,
            (0, 0, 0), (255, 255, 255),
            20, 20, 300,
            value=cfg.SCREEN_BRIGHTNESS,
            action=lambda v: setattr(cfg, 'SCREEN_BRIGHTNESS', v)
        )

        self.myfont = cfg.get_font(60)
        self.brightness_label = self.myfont.render(_('Brightness'), True, (0, 0, 0))
        self.brightness_rect = self.brightness_label.get_rect(center=(760, 480))

        self.audio_slider = Slider(
            600, 730, 40, 5,
            track_colour, knob_colour,
            20, 20, 300,
            value=initial_volume,
            action=lambda v: pygame.mixer.music.set_volume(v)
        )

        self.myfont = cfg.get_font(60)
        self.text_logo = self.myfont.render(_('Music volume'), True, (0, 0, 0))
        self.text_rect = self.text_logo.get_rect(center=(760, 650))

    def back_to_main(self):
        self.app.manager.set_state("main")
    
    def toggle_language(self):
        new_lang = 'ua' if cfg.LANGUAGE == 'en' else 'en'
        self.app.update_language(new_lang)
    
    def handle_event(self, event):
        super().handle_event(event)
        self.audio_slider.handle_event(event)
        self.brightness_slider.handle_event(event)

    def update(self):
        if hasattr(self.audio_slider, "update"):
            self.audio_slider.update()

    def draw(self, surface):
        for button in self.buttons:
            button.draw(surface)
        self.audio_slider.draw(surface)
        surface.blit(self.text_logo, self.text_rect)

        self.brightness_slider.draw(surface)
        surface.blit(self.brightness_label, self.brightness_rect)

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
        button_width, button_height = 300, 100
        back_rect = pygame.Rect(1400, 850, button_width, button_height)
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

        button_width, button_height = 300, 100

        self.pause_menu_color = (0, 0, 0, 180)

        self.buttons = [
            Button(
                pygame.Rect((cfg.SCREEN_WIDTH - button_width) // 2, 650, button_width, button_height),
                _("RESUME"),
                cfg.button_color_START,
                cfg.button_hover_color_START,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.resume_game
            ),
            Button(
                pygame.Rect((cfg.SCREEN_WIDTH - button_width) // 2, 800, button_width, button_height),
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
        overlay = pygame.Surface((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(self.pause_menu_color)
        screen.blit(overlay, (0, 0))

        for button in self.buttons:
            button.draw(screen)


    def resume_game(self):
        self.app.manager.set_state("gameplay")

    def back_to_main(self):
        self.app.manager.set_state("main")
