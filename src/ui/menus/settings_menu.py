import pygame
from typing import TYPE_CHECKING

from src.ui.menus.base import Menu
from src.ui.widgets import Button, Slider
import src.config as cfg

if TYPE_CHECKING:
    from src.app import App


class SettingsMenu(Menu):
    """
    Settings menu interface for the application.

    Inherits from Menu and provides sliders and buttons for adjusting audio, brightness, display mode, language, and returning to the main menu.

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
        scale = cfg.ui_scale()
        button_width, button_height = max(1,int(360 * scale)), max(1,int(120 * scale))
        mode_rect = pygame.Rect(0, 0, button_width, button_height)
        lang_rect = pygame.Rect(0, 0, button_width, button_height)
        back_rect = pygame.Rect(0, 0, button_width, button_height)

        self.buttons = [
            Button(
                mode_rect,
                self._display_mode_label(),
                cfg.button_color_SETTINGS,
                cfg.button_hover_color_SETTINGS,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.toggle_display_mode
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
            ),
            Button(
                back_rect,
                _("BACK"),
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

        def set_brightness(v):
            cfg.USER_SCREEN_BRIGHTNESS = max(0.3, v)
            cfg.update_brightness()

        self.brightness_slider = Slider(
            int(600 * scale), int(550 * scale), max(8,int(40 * scale)), 5,
            (0, 0, 0), (255, 255, 255),
            max(6,int(20 * scale)), max(6,int(20 * scale)), max(20,int(300 * scale)),
            value=cfg.USER_SCREEN_BRIGHTNESS,
            action=set_brightness
        )

        # use a single scaled font for labels
        self.myfont = cfg.get_font(max(10,int(60 * scale)))
        self.brightness_label = self.myfont.render(_('Brightness'), True, (0, 0, 0))
        self.brightness_rect = self.brightness_label.get_rect(center=(int(760 * scale), int(480 * scale)))

        self.audio_slider = Slider(
            int(600 * scale), int(730 * scale), max(8,int(40 * scale)), 5,
            track_colour, knob_colour,
            max(6,int(20 * scale)), max(6,int(20 * scale)), max(20,int(300 * scale)),
            value=initial_volume,
            action=lambda v: pygame.mixer.music.set_volume(v)
        )

        self.text_logo = self.myfont.render(_('Music volume'), True, (0, 0, 0))
        self.text_rect = self.text_logo.get_rect(center=(int(760 * scale), int(650 * scale)))

    def layout(self, screen: pygame.Surface):
        sw, sh = self._screen_size(screen)
        scale = cfg.ui_scale()
        button_width, button_height = max(1,int(360 * scale)), max(1,int(120 * scale))
        center_x = sw // 2
        center_y = sh // 2 + int(80 * scale)

        # keep controls separated: sliders on the left, buttons on the right
        left_column_x = center_x - int(430 * scale)
        right_column_x = center_x + int(70 * scale)

        self.buttons[0].set_text(self._display_mode_label())
        self.buttons[1].set_text(f"{_('LANG')}: {cfg.LANGUAGE.upper()}")
        self.buttons[2].set_text(_("BACK"))

        self.buttons[0].rect = pygame.Rect(right_column_x, center_y - int(170 * scale), button_width, button_height)
        self.buttons[1].rect = pygame.Rect(right_column_x, center_y - int(20 * scale), button_width, button_height)
        self.buttons[2].rect = pygame.Rect(right_column_x, center_y + int(130 * scale), button_width, button_height)
        for button in self.buttons:
            try:
                button._update_text_surface()
            except Exception:
                pass

        # Position sliders so their track centers align with button centers
        self.brightness_slider.x = left_column_x
        self.brightness_slider.y = self.buttons[0].rect.centery - self.brightness_slider.height // 2
        self.audio_slider.x = left_column_x
        self.audio_slider.y = self.buttons[1].rect.centery - self.audio_slider.height // 2

        # Render labels and position them above their respective slider tracks
        self.brightness_label = self.myfont.render(_('Brightness'), True, (0, 0, 0))
        label_x = self.brightness_slider.x + self.brightness_slider.track_length // 2
        label_y = self.brightness_slider.y - 18
        self.brightness_rect = self.brightness_label.get_rect(center=(label_x, label_y))

        self.text_logo = self.myfont.render(_('Music volume'), True, (0, 0, 0))
        text_x = self.audio_slider.x + self.audio_slider.track_length // 2
        text_y = self.audio_slider.y - 18
        self.text_rect = self.text_logo.get_rect(center=(text_x, text_y))

    def back_to_main(self):
        self.app.manager.set_state("main")

    def _display_mode_label(self):
        return f"MODE: {'FULLSCREEN' if self.app.is_fullscreen else 'WINDOW'}"

    def toggle_display_mode(self):
        self.app.toggle_display_mode()
        self.buttons[0].set_text(self._display_mode_label())
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
        self.layout(surface)
        for button in self.buttons:
            button.draw(surface)

        # Draw labels above sliders first, then sliders so labels are visually above
        surface.blit(self.text_logo, self.text_rect)
        surface.blit(self.brightness_label, self.brightness_rect)

        self.audio_slider.draw(surface)
        self.brightness_slider.draw(surface)