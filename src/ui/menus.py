import pygame
import sys
from typing import TYPE_CHECKING

from src.ui.widgets import Button, Tooltip, Slider
from src.core.state import State
from src.core.save_manager import SaveManager
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

        scale = cfg.ui_scale()
        button_width, button_height = max(1, int(360 * scale)), max(1, int(120 * scale))
        gap = max(4, int(60 * scale))
        tot_width = 2 * button_width + gap
        center_x = cfg.SCREEN_WIDTH // 2

        start_rect = pygame.Rect(center_x - tot_width // 2, int(650 * scale), button_width, button_height)
        exit_rect = pygame.Rect(center_x - tot_width // 2 + button_width + gap, int(650 * scale), button_width, button_height)
        settings_rect = pygame.Rect(center_x - tot_width // 2, int(800 * scale), button_width, button_height)
        credits_rect = pygame.Rect(center_x - tot_width // 2 + button_width + gap, int(800 * scale), button_width, button_height)
        load_rect = pygame.Rect(center_x - button_width // 2, int(520 * scale), button_width, button_height)

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
                load_rect,
                _("LOAD"),
                cfg.button_color_SETTINGS,
                cfg.button_hover_color_SETTINGS,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.open_load_menu
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
        logo_size = max(8, int(280 * cfg.ui_scale()))
        self.beta_logo_img = pygame.transform.scale(self.beta_logo_img, (logo_size, logo_size))
        self.beta_logo_rect = self.beta_logo_img.get_rect()

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

    def layout(self, screen: pygame.Surface):
        sw, sh = self._screen_size(screen)
        scale = cfg.ui_scale()
        button_width, button_height = max(1,int(360 * scale)), max(1,int(120 * scale))
        gap = max(4,int(60 * scale))
        tot_width = 2 * button_width + gap
        center_x = sw // 2

        positions = [
            pygame.Rect(center_x - tot_width // 2, int(sh * 0.60), button_width, button_height),
            pygame.Rect(center_x - button_width // 2, int(sh * 0.48), button_width, button_height),
            pygame.Rect(center_x - tot_width // 2 + button_width + gap, int(sh * 0.60), button_width, button_height),
            pygame.Rect(center_x - tot_width // 2, int(sh * 0.75), button_width, button_height),
            pygame.Rect(center_x - tot_width // 2 + button_width + gap, int(sh * 0.75), button_width, button_height),
        ]

        for button, rect in zip(self.buttons, positions):
            self._apply_button_size(button, rect)

        logo_off = max(20, int(180 * cfg.ui_scale()))
        self.beta_logo_rect = self.beta_logo_img.get_rect(center=(sw - logo_off, sh - logo_off))
        self.tooltips[0].update_target(self.beta_logo_rect, self.tooltips[0].text)

    def draw(self, screen):
        self.layout(screen)
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

    def open_load_menu(self):
        self.app.manager.states["save_load"].mode = "load"
        self.app.manager.states["save_load"].refresh_saves()
        self.app.manager.set_state("save_load")


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

        self.brightness_slider = Slider(
            int(600 * scale), int(550 * scale), max(8,int(40 * scale)), 5,
            (0, 0, 0), (255, 255, 255),
            max(6,int(20 * scale)), max(6,int(20 * scale)), max(20,int(300 * scale)),
            value=cfg.SCREEN_BRIGHTNESS,
            action=lambda v: setattr(cfg, 'SCREEN_BRIGHTNESS', max(0.3, v))
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
                _("RESUME"),
                cfg.button_color_START,
                cfg.button_hover_color_START,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.resume_game
            ),
            Button(
                pygame.Rect(cx, int(800 * scale), button_width, button_height),
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

    def resume_game(self):
        self.app.manager.set_state("gameplay")

    def back_to_main(self):
        self.app.manager.set_state("main")


class SaveLoadMenu(Menu):
    def __init__(self, app: "App"):
        super().__init__(app)
        self.mode = "save" # "save" or "load"
        self.slots = ["save1", "save2", "save3"]
        self.refresh_saves()

    def layout(self, screen: pygame.Surface):
        sw, sh = self._screen_size(screen)
        self.buttons[0].rect = pygame.Rect(80, 70, 240, 100)
        try:
            self.buttons[0]._update_text_surface()
        except Exception:
            pass

        title_width = min(900, sw - 120)
        self._title_rect = pygame.Rect((sw - title_width) // 2, 150, title_width, 100)
        start_y = 320
        slot_width = min(520, sw - 360)
        slot_x = (sw - slot_width) // 2

        button_index = 1
        for i, slot in enumerate(self.slots):
            y = start_y + i * 160
            exists = slot + ".json" in SaveManager.get_save_files()

            if button_index < len(self.buttons):
                self.buttons[button_index].rect = pygame.Rect(slot_x, y, slot_width, 110)
                try:
                    self.buttons[button_index]._update_text_surface()
                except Exception:
                    pass
                button_index += 1

            if exists and button_index < len(self.buttons):
                self.buttons[button_index].rect = pygame.Rect(slot_x + slot_width + 30, y, 180, 110)
                try:
                    self.buttons[button_index]._update_text_surface()
                except Exception:
                    pass
                button_index += 1

    def refresh_saves(self):
        self.buttons = []
        
        # Back button
        back_rect = pygame.Rect(250, 170, 200, 80)
        self.buttons.append(Button(
            back_rect,
            _("BACK"),
            cfg.button_color_SETTINGS_BACK,
            cfg.button_hover_color_SETTINGS_BACK,
            cfg.button_font,
            cfg.text_color,
            cfg.corner_radius,
            on_click=self.go_back
        ))

        # Slot buttons
        start_y = 370
        for i, slot in enumerate(self.slots):
            y = start_y + i * 150
            
            # Check if save exists
            exists = slot + ".json" in SaveManager.get_save_files()
            
            label = f"{_('Slot')} {i+1}"
            if exists:
                label += f" ({_('Used')})"
            else:
                label += f" ({_('Empty')})"

            # Main slot button (Save or Load)
            slot_rect = pygame.Rect(cfg.SCREEN_WIDTH // 2 - 200, y, 400, 100)
            self.buttons.append(Button(
                slot_rect,
                label,
                cfg.button_color_START if exists else (100, 100, 100),
                cfg.button_hover_color_START if exists else (120, 120, 120),
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=lambda s=slot: self.on_slot_click(s)
            ))

            # Delete button (only if exists)
            if exists:
                del_rect = pygame.Rect(cfg.SCREEN_WIDTH // 2 + 250, y, 150, 100)
                self.buttons.append(Button(
                    del_rect,
                    _("DEL"),
                    cfg.button_color_EXIT,
                    cfg.button_hover_color_EXIT,
                    cfg.button_font,
                    cfg.text_color,
                    cfg.corner_radius,
                    on_click=lambda s=slot: self.delete_slot(s)
                ))

    def on_slot_click(self, slot_name):
        if self.mode == "save":
            SaveManager.save_game(self.app, slot_name)
            self.refresh_saves() # Update UI to show "Used"
        elif self.mode == "load":
            if SaveManager.load_game(self.app, slot_name):
                self.app.manager.set_state("gameplay")

    def delete_slot(self, slot_name):
        SaveManager.delete_save(slot_name)
        self.refresh_saves()

    def go_back(self):
        if self.mode == "save":
            self.app.manager.set_state("pause")
        else:
            self.app.manager.set_state("main")

    def draw(self, screen):
        # Draw background (maybe semi-transparent if coming from pause)
        if self.mode == "save":
            overlay = pygame.Surface((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
        else:
            # If loading from main menu, maybe draw background image
            screen.blit(cfg.bg, (0, 0))

        title = _("SAVE GAME") if self.mode == "save" else _("LOAD GAME")
        title_surf = cfg.get_font(80).render(title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(cfg.SCREEN_WIDTH // 2, 200))
        screen.blit(title_surf, title_rect)

        super().draw(screen)
