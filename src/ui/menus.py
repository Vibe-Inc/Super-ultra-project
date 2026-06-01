import math
import random
import pygame
import sys
from typing import TYPE_CHECKING

from src.ui.widgets import Button, Tooltip, Slider
from src.core.state import State
from src.core.save_manager import SaveManager
import src.config as cfg
from src.core.logger import logger

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
    """Main menu screen."""

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
        logger.info("Start game requested from MainMenu")
        self.app.manager.set_state("gameplay")

    def exit_game(self):
        logger.info("Exit requested from MainMenu")
        pygame.quit()
        sys.exit()

    def open_settings(self):
        logger.info("Open Settings from MainMenu")
        self.app.manager.set_state("settings")

    def open_credits(self):
        logger.info("Open Credits from MainMenu")
        self.app.manager.set_state("credits")

    def open_load_menu(self):
        logger.info("Open Load Menu from MainMenu")
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


class SkillbarMenu(Menu):
    """
    Skillbar editor with a single-skill book and a 6-slot active bar.
    """
    def __init__(self, app: "App"):
        super().__init__(app)
        self.bar_slots_count = 6
        self.storage_slots_count = 1
        self.panel_margin = max(18, int(24 * cfg.ui_scale()))
        self.grid_gap = max(6, int(8 * cfg.ui_scale()))
        self.sidebar_width = max(280, int(340 * cfg.ui_scale()))
        self.slot_size = 48

        self.sidebar_rect = pygame.Rect(0, 0, 0, 0)
        self.storage_grid_rect = pygame.Rect(0, 0, 0, 0)
        self.bar_rect = pygame.Rect(0, 0, 0, 0)
        self.storage_slot_rects: list[pygame.Rect] = []
        self.bar_slot_rects: list[pygame.Rect] = []

        self.title_font = cfg.get_font(max(10, int(32 * cfg.ui_scale())))
        self.section_font = cfg.get_font(max(8, int(22 * cfg.ui_scale())))
        self.small_font = cfg.get_font(max(8, int(16 * cfg.ui_scale())))

        exit_width = max(120, int(160 * cfg.ui_scale()))
        exit_height = max(44, int(52 * cfg.ui_scale()))
        self.exit_button = Button(
            pygame.Rect(0, 0, exit_width, exit_height),
            _("EXIT"),
            (110, 70, 70),
            (150, 95, 95),
            cfg.button_font,
            cfg.text_color,
            cfg.corner_radius,
            on_click=self.exit_menu,
        )
        self.buttons = [self.exit_button]

        self.drag_payload = None
        self.drag_offset = (0, 0)

    def _character(self):
        gameplay_state = getattr(getattr(self.app, "manager", None), "states", {}).get("gameplay") if hasattr(self.app, "manager") else None
        return getattr(gameplay_state, "character", None)

    def _skillbook(self):
        character = self._character()
        if character is not None and hasattr(character, "skillbook"):
            if not hasattr(character, "skillbar"):
                character.skillbar = [None for _ in range(self.bar_slots_count)]
            return character.skillbook, character.skillbar

        if not hasattr(self, "_fallback_skillbook"):
            self._fallback_skillbook = [
                {
                    "skill_id": "dash",
                    "name": _("Dash"),
                    "description": _("Quick burst of movement"),
                    "color": (86, 132, 186),
                    "accent": (220, 235, 255),
                }
            ]
            self._fallback_skillbar = [None for _ in range(self.bar_slots_count)]
        return self._fallback_skillbook, self._fallback_skillbar

    def _storage_items(self, skillbook: list[dict], skillbar: list[dict | None]):
        active_skill_ids = {
            skill.get("skill_id")
            for skill in skillbar
            if skill is not None
        }
        return [skill for skill in skillbook if skill.get("skill_id") not in active_skill_ids]

    def _slot_at_position(self, position: tuple[int, int]):
        for index, slot_rect in enumerate(self.bar_slot_rects):
            if slot_rect.collidepoint(position):
                return ("bar", 0, index)

        for index, slot_rect in enumerate(self.storage_slot_rects):
            if slot_rect.collidepoint(position):
                return ("storage", 0, index)

        return None

    def _draw_card(self, surface: pygame.Surface, rect: pygame.Rect, skill: dict | None, *, empty_label: str = "+"):
        if skill is None:
            pygame.draw.rect(surface, (55, 55, 62), rect, border_radius=10)
            pygame.draw.rect(surface, (140, 140, 150), rect, 2, border_radius=10)
            label = self.section_font.render(empty_label, True, (175, 175, 180))
            surface.blit(label, label.get_rect(center=rect.center))
            return

        fill = skill.get("color", (80, 100, 140))
        accent = skill.get("accent", (220, 220, 230))
        pygame.draw.rect(surface, fill, rect, border_radius=10)
        pygame.draw.rect(surface, accent, rect, 2, border_radius=10)
        name = self.small_font.render(skill["name"], True, (255, 255, 255))
        surface.blit(name, name.get_rect(center=(rect.centerx, rect.centery - 5)))
        skill_id = skill.get("skill_id", "")
        if skill_id:
            ident = self.small_font.render(skill_id.replace("_", " ").upper(), True, (235, 235, 235))
            surface.blit(ident, ident.get_rect(center=(rect.centerx, rect.centery + 13)))

    def _sync_state_to_character(self):
        character = self._character()
        if character is None:
            return None, None

        if not hasattr(character, "skillbook"):
            character.skillbook = []
        if not hasattr(character, "skillbar") or len(character.skillbar) != self.bar_slots_count:
            character.skillbar = [None for _ in range(self.bar_slots_count)]
        return character.skillbook, character.skillbar

    def _on_drop(self, source, target):
        skillbook, skillbar = self._sync_state_to_character()
        if skillbook is None:
            skillbook, skillbar = self._skillbook()
        storage_items = self._storage_items(skillbook, skillbar)

        source_area, source_index = source
        target_area, target_index = target

        if source_area == "bar":
            if target_area == "bar":
                if source_index == target_index:
                    return
                skillbar[source_index], skillbar[target_index] = skillbar[target_index], skillbar[source_index]
            elif target_area == "storage":
                skillbar[source_index] = None
            return

        if source_area == "storage":
            if not storage_items or target_area != "bar":
                return
            source_skill = storage_items[source_index]
            if skillbar[target_index] is source_skill:
                return
            skillbar[target_index] = source_skill

    def exit_menu(self):
        # Ensure any open player inventory windows are properly removed
        try:
            # mark as closed
            self.app.INV_manager.player_inventory_opened = False

            # If the gameplay state exists, remove its inventory panels from active list
            gameplay = getattr(getattr(self.app, "manager", None), "states", {}).get("gameplay")
            if gameplay:
                try:
                    self.app.INV_manager.remove_active_inventory(getattr(gameplay, "MAIN_player_inv", None))
                except Exception:
                    pass
                try:
                    self.app.INV_manager.remove_active_inventory(getattr(gameplay, "PLAYER_inventory_equipment", None))
                except Exception:
                    pass
        except Exception:
            pass

        self.app.manager.set_state("gameplay")

    def layout(self, screen: pygame.Surface):
        skillbook, skillbar = self._skillbook()
        storage_items = self._storage_items(skillbook, skillbar)
        self.storage_slots_count = max(1, len(storage_items))

        sw, sh = self._screen_size(screen)
        margin = self.panel_margin
        sidebar_width = min(self.sidebar_width, max(280, sw // 4))
        sidebar_x = sw - sidebar_width - margin
        self.sidebar_rect = pygame.Rect(sidebar_x, margin, sidebar_width, sh - margin * 2)

        left_width = max(320, sidebar_x - margin * 2)

        storage_size = min(
            54,
            max(34, (left_width - self.grid_gap * (self.storage_slots_count + 1)) // self.storage_slots_count),
            max(34, int((sh * 0.28 - self.grid_gap * 2))),
        )
        bar_size = min(72, max(42, storage_size + 4))

        storage_total_w = storage_size * self.storage_slots_count + self.grid_gap * (self.storage_slots_count + 1)
        storage_total_h = storage_size + self.grid_gap * 2
        storage_x = margin + max(0, (left_width - storage_total_w) // 2)
        storage_y = sh - margin - storage_total_h
        self.storage_grid_rect = pygame.Rect(storage_x - self.grid_gap, storage_y - self.grid_gap, storage_total_w, storage_total_h)

        bar_total_w = bar_size * self.bar_slots_count + self.grid_gap * (self.bar_slots_count + 1)
        bar_x = margin + max(0, (left_width - bar_total_w) // 2)
        bar_y = margin + 84
        self.bar_rect = pygame.Rect(bar_x - self.grid_gap, bar_y - self.grid_gap, bar_total_w, bar_size + self.grid_gap * 2)

        self.storage_slot_rects = []
        for index in range(self.storage_slots_count):
            slot_x = storage_x + self.grid_gap + index * (storage_size + self.grid_gap)
            slot_y = storage_y + self.grid_gap
            self.storage_slot_rects.append(pygame.Rect(slot_x, slot_y, storage_size, storage_size))

        self.bar_slot_rects = []
        for index in range(self.bar_slots_count):
            slot_x = bar_x + self.grid_gap + index * (bar_size + self.grid_gap)
            slot_y = bar_y + self.grid_gap
            self.bar_slot_rects.append(pygame.Rect(slot_x, slot_y, bar_size, bar_size))

        exit_width = max(120, int(self.sidebar_rect.width * 0.55))
        exit_height = max(44, int(52 * cfg.ui_scale()))
        self.exit_button.rect = pygame.Rect(
            self.sidebar_rect.centerx - exit_width // 2,
            self.sidebar_rect.bottom - exit_height - margin,
            exit_width,
            exit_height,
        )
        try:
            self.exit_button._update_text_surface()
        except Exception:
            pass

    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)

        skillbook, skillbar = self._sync_state_to_character()
        if skillbook is None:
            skillbook, skillbar = self._skillbook()
        storage_items = self._storage_items(skillbook, skillbar)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            slot = self._slot_at_position(event.pos)
            if slot is None:
                return

            area, column_or_none, row_or_index = slot
            if area == "storage":
                # When there are no unused skills we still render one '+' slot.
                # Guard index access so clicking that placeholder does nothing.
                if row_or_index < 0 or row_or_index >= len(storage_items):
                    return
                self.drag_payload = {"source": ("storage", row_or_index), "skill": storage_items[row_or_index]}
                self.drag_offset = (event.pos[0] - self.storage_slot_rects[row_or_index].x, event.pos[1] - self.storage_slot_rects[row_or_index].y)
                return

            if skillbar[row_or_index] is not None:
                self.drag_payload = {"source": ("bar", row_or_index), "skill": skillbar[row_or_index]}
                self.drag_offset = (event.pos[0] - self.bar_slot_rects[row_or_index].x, event.pos[1] - self.bar_slot_rects[row_or_index].y)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if not self.drag_payload:
                return

            target_slot = self._slot_at_position(event.pos)
            if target_slot is not None and target_slot[0] == "bar":
                self._on_drop(self.drag_payload["source"], ("bar", target_slot[2]))
            elif target_slot is not None and target_slot[0] == "storage":
                self._on_drop(self.drag_payload["source"], ("storage", target_slot[2]))

            self.drag_payload = None
            self.drag_offset = (0, 0)

    def _draw_sidebar(self, surface: pygame.Surface):
        title = self.title_font.render(_("Skillbar"), True, (255, 255, 255))
        surface.blit(title, (self.sidebar_rect.x + 18, self.sidebar_rect.y + 18))

        hint = self.small_font.render(_("Active skills go above. Unused skills stay in the storage row below."), True, (225, 225, 230))
        surface.blit(hint, (self.sidebar_rect.x + 18, self.sidebar_rect.y + 58))

        list_top = self.sidebar_rect.y + 110
        list_rect = pygame.Rect(self.sidebar_rect.x + 14, list_top, self.sidebar_rect.width - 28, self.exit_button.rect.top - list_top - 16)
        pygame.draw.rect(surface, (30, 30, 38), list_rect, border_radius=12)
        pygame.draw.rect(surface, (85, 85, 98), list_rect, 1, border_radius=12)

        label = self.section_font.render(_("Storage"), True, (255, 255, 255))
        surface.blit(label, (list_rect.x + 12, list_rect.y + 10))

        skillbook, skillbar = self._sync_state_to_character()
        if skillbook is None:
            skillbook, skillbar = self._skillbook()
        storage_items = self._storage_items(skillbook, skillbar)

        if not storage_items:
            empty = self.small_font.render(_("No unused skills right now."), True, (205, 205, 215))
            surface.blit(empty, empty.get_rect(center=list_rect.center))
            return

        text_y = list_rect.y + 42
        max_rows = max(1, (list_rect.bottom - text_y - 10) // (self.small_font.get_height() + 8))
        for index, skill in enumerate(storage_items[:max_rows]):
            line = self.small_font.render(f"{index + 1}. {skill['name']}", True, (235, 235, 245))
            surface.blit(line, (list_rect.x + 12, text_y + index * (self.small_font.get_height() + 8)))

    def draw(self, screen: pygame.Surface):
        self.layout(screen)

        screen.fill((16, 16, 20))
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((18, 18, 26, 220))
        screen.blit(overlay, (0, 0))

        skillbook, skillbar = self._sync_state_to_character()
        if skillbook is None:
            skillbook, skillbar = self._skillbook()
        storage_items = self._storage_items(skillbook, skillbar)

        bar_title = self.section_font.render(_("6 active slots"), True, (235, 235, 245))
        screen.blit(bar_title, (self.bar_rect.x, max(12, self.bar_rect.y - bar_title.get_height() - 8)))

        storage_title = self.section_font.render(_("Unused skills"), True, (235, 235, 245))
        screen.blit(storage_title, (self.storage_grid_rect.x, max(12, self.storage_grid_rect.y - storage_title.get_height() - 8)))

        pygame.draw.rect(screen, (24, 24, 30), self.bar_rect, border_radius=18)
        pygame.draw.rect(screen, (82, 82, 96), self.bar_rect, 2, border_radius=18)
        pygame.draw.rect(screen, (24, 24, 30), self.storage_grid_rect, border_radius=18)
        pygame.draw.rect(screen, (82, 82, 96), self.storage_grid_rect, 2, border_radius=18)
        pygame.draw.rect(screen, (28, 28, 34), self.sidebar_rect, border_radius=18)
        pygame.draw.rect(screen, (82, 82, 96), self.sidebar_rect, 2, border_radius=18)

        for index, slot_rect in enumerate(self.bar_slot_rects):
            self._draw_card(screen, slot_rect, skillbar[index], empty_label=str(index + 1))

        for index, slot_rect in enumerate(self.storage_slot_rects):
            skill = storage_items[index] if index < len(storage_items) else None
            self._draw_card(screen, slot_rect, skill, empty_label="+")

        self._draw_sidebar(screen)
        self.exit_button.draw(screen)

        if self.drag_payload:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            skill = self.drag_payload["skill"]
            ghost_size = self.bar_slot_rects[0].width if self.bar_slot_rects else 56
            ghost = pygame.Surface((ghost_size, ghost_size), pygame.SRCALPHA)
            self._draw_card(ghost, ghost.get_rect(), skill, empty_label="+")
            ghost.set_alpha(210)
            screen.blit(ghost, (mouse_x - self.drag_offset[0], mouse_y - self.drag_offset[1]))


class SkillTreeMenu(Menu):
    """
    Placeholder skill tree screen inspired by Path of Exile.
    """
    def __init__(self, app: "App"):
        super().__init__(app)
        scale = cfg.ui_scale()
        self.title_font = cfg.get_font(max(12, int(36 * scale)))
        self.section_font = cfg.get_font(max(10, int(22 * scale)))
        self.small_font = cfg.get_font(max(8, int(16 * scale)))

        exit_width = max(120, int(200 * scale))
        exit_height = max(44, int(52 * scale))
        self.exit_button = Button(
            pygame.Rect(0, 0, exit_width, exit_height),
            _("BACK"),
            (110, 70, 70),
            (150, 95, 95),
            cfg.button_font,
            cfg.text_color,
            cfg.corner_radius,
            on_click=self.exit_menu,
        )
        self.buttons = [self.exit_button]

        self.zoom = 1.0
        self.min_zoom = 0.6
        self.max_zoom = 1.6
        self.pan_offset = pygame.Vector2(0, 0)
        self.dragging_view = False
        self.drag_origin = pygame.Vector2(0, 0)
        self.drag_start_offset = pygame.Vector2(0, 0)

        self.nodes, self.links = self._build_tree()
        self.nodes_by_id = {node["id"]: node for node in self.nodes}
        self.selected_node_id = "core"
        self.hovered_node_id = None
        self.background_points = self._build_background_points()

        self.tree_rect = pygame.Rect(0, 0, 0, 0)
        self.sidebar_rect = pygame.Rect(0, 0, 0, 0)
        self._layout_size = None

    def _character(self):
        gameplay_state = getattr(getattr(self.app, "manager", None), "states", {}).get("gameplay")
        return getattr(gameplay_state, "character", None)

    def _get_unlocked_nodes(self):
        character = self._character()
        unlocked = getattr(character, "skill_tree_unlocked", None) if character else None
        if unlocked is None:
            return {"core"}
        if isinstance(unlocked, list):
            return set(unlocked)
        return set(unlocked)

    def _build_tree(self):
        nodes = []
        links = []
        link_set = set()

        def add_node(node_id, name, effect, pos, size, kind, color, accent):
            nodes.append({
                "id": node_id,
                "name": name,
                "effect": effect,
                "pos": pygame.Vector2(pos),
                "size": size,
                "kind": kind,
                "color": color,
                "accent": accent,
            })

        def add_link(a, b):
            if a == b:
                return
            key = (a, b) if a < b else (b, a)
            if key in link_set:
                return
            link_set.add(key)
            links.append((a, b))

        add_node(
            "core",
            _("Core"),
            _("Placeholder: unlocks nearby nodes."),
            (0, 0),
            22,
            "core",
            (80, 120, 170),
            (220, 235, 250),
        )

        ring1_count = 8
        ring1_radius = 180
        for i in range(ring1_count):
            angle = math.radians(i * (360 / ring1_count))
            pos = (math.cos(angle) * ring1_radius, math.sin(angle) * ring1_radius)
            node_id = f"minor_{i + 1}"
            add_node(
                node_id,
                _("Minor Node"),
                _("Placeholder: small stat bonus."),
                pos,
                10,
                "minor",
                (46, 52, 64),
                (140, 148, 160),
            )
            add_link("core", node_id)

        for i in range(ring1_count):
            add_link(f"minor_{i + 1}", f"minor_{(i + 1) % ring1_count + 1}")

        ring2_count = 6
        ring2_radius = 320
        for i in range(ring2_count):
            angle = math.radians(i * (360 / ring2_count) + 30)
            pos = (math.cos(angle) * ring2_radius, math.sin(angle) * ring2_radius)
            node_id = f"major_{i + 1}"
            add_node(
                node_id,
                _("Notable Node"),
                _("Placeholder: notable bonus."),
                pos,
                16,
                "major",
                (84, 118, 78),
                (210, 232, 210),
            )
            link_target = f"minor_{1 + int(i * ring1_count / ring2_count)}"
            add_link(node_id, link_target)

            cluster_radius = 62
            for j in range(3):
                offset = math.radians(j * 120 + 20)
                cluster_pos = (
                    pos[0] + math.cos(offset) * cluster_radius,
                    pos[1] + math.sin(offset) * cluster_radius,
                )
                cluster_id = f"cluster_{i + 1}_{j + 1}"
                add_node(
                    cluster_id,
                    _("Minor Node"),
                    _("Placeholder: small stat bonus."),
                    cluster_pos,
                    9,
                    "minor",
                    (50, 56, 68),
                    (140, 148, 160),
                )
                add_link(node_id, cluster_id)

        ring3_count = 4
        ring3_radius = 470
        for i in range(ring3_count):
            angle = math.radians(i * (360 / ring3_count) + 45)
            pos = (math.cos(angle) * ring3_radius, math.sin(angle) * ring3_radius)
            node_id = f"keystone_{i + 1}"
            add_node(
                node_id,
                _("Keystone Node"),
                _("Placeholder: large tradeoff."),
                pos,
                22,
                "keystone",
                (140, 74, 74),
                (240, 210, 210),
            )
            add_link(node_id, f"major_{(i % ring2_count) + 1}")

        return nodes, links

    def _build_background_points(self):
        rng = random.Random(23)
        points = []
        for _ in range(220):
            points.append(
                (
                    rng.uniform(-620, 620),
                    rng.uniform(-520, 520),
                    rng.randint(1, 2),
                )
            )
        return points

    def _node_screen_pos(self, node):
        origin = pygame.Vector2(self.tree_rect.center) + self.pan_offset
        return origin + node["pos"] * self.zoom

    def _hit_test_node(self, pos):
        if not self.tree_rect.collidepoint(pos):
            return None
        mx, my = pos
        best_id = None
        best_dist = None
        for node in self.nodes:
            node_pos = self._node_screen_pos(node)
            radius = node["size"] * self.zoom + 4
            dist = (node_pos.x - mx) ** 2 + (node_pos.y - my) ** 2
            if dist <= radius ** 2 and (best_dist is None or dist < best_dist):
                best_dist = dist
                best_id = node["id"]
        return best_id

    def _wrap_text(self, text, font, max_width):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test_line = f"{current} {word}".strip()
            if font.size(test_line)[0] <= max_width or not current:
                current = test_line
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def exit_menu(self):
        try:
            self.app.INV_manager.player_inventory_opened = False
            gameplay = getattr(getattr(self.app, "manager", None), "states", {}).get("gameplay")
            if gameplay:
                try:
                    self.app.INV_manager.remove_active_inventory(getattr(gameplay, "MAIN_player_inv", None))
                except Exception:
                    pass
                try:
                    self.app.INV_manager.remove_active_inventory(getattr(gameplay, "PLAYER_inventory_equipment", None))
                except Exception:
                    pass
        except Exception:
            pass

        self.app.manager.set_state("gameplay")

    def layout(self, screen: pygame.Surface):
        sw, sh = self._screen_size(screen)
        scale = cfg.ui_scale()
        margin = max(12, int(24 * scale))
        sidebar_width = min(max(240, int(360 * scale)), max(240, sw // 3))
        tree_width = max(240, sw - sidebar_width - margin * 3)
        self.sidebar_rect = pygame.Rect(sw - sidebar_width - margin, margin, sidebar_width, sh - margin * 2)
        self.tree_rect = pygame.Rect(margin, margin, tree_width, sh - margin * 2)

        exit_width = max(120, int(self.sidebar_rect.width * 0.6))
        exit_height = max(44, int(52 * scale))
        self.exit_button.rect = pygame.Rect(
            self.sidebar_rect.centerx - exit_width // 2,
            self.sidebar_rect.bottom - exit_height - margin,
            exit_width,
            exit_height,
        )
        try:
            self.exit_button._update_text_surface()
        except Exception:
            pass

        size = (sw, sh)
        if self._layout_size != size:
            self._layout_size = size
            self.pan_offset = pygame.Vector2(0, 0)

    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                node_id = self._hit_test_node(event.pos)
                if node_id:
                    self.selected_node_id = node_id
            if event.button == 3 and self.tree_rect.collidepoint(event.pos):
                self.dragging_view = True
                self.drag_origin = pygame.Vector2(event.pos)
                self.drag_start_offset = pygame.Vector2(self.pan_offset)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                self.dragging_view = False

        elif event.type == pygame.MOUSEMOTION and self.dragging_view:
            delta = pygame.Vector2(event.pos) - self.drag_origin
            self.pan_offset = self.drag_start_offset + delta

        elif event.type == pygame.MOUSEWHEEL:
            if self.tree_rect.collidepoint(pygame.mouse.get_pos()):
                self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom + event.y * 0.08))

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.zoom = 1.0
            self.pan_offset = pygame.Vector2(0, 0)

    def _draw_tree_background(self, surface):
        origin = pygame.Vector2(self.tree_rect.center) + self.pan_offset
        for radius in (180, 320, 470):
            pygame.draw.circle(surface, (32, 32, 42), origin, int(radius * self.zoom), 1)

        for x, y, size in self.background_points:
            pos = origin + pygame.Vector2(x, y) * self.zoom
            if self.tree_rect.collidepoint(pos):
                pygame.draw.circle(surface, (36, 36, 46), (int(pos.x), int(pos.y)), size)

    def _draw_links(self, surface, unlocked):
        for a, b in self.links:
            node_a = self.nodes_by_id.get(a)
            node_b = self.nodes_by_id.get(b)
            if node_a is None or node_b is None:
                continue
            pos_a = self._node_screen_pos(node_a)
            pos_b = self._node_screen_pos(node_b)
            active = a in unlocked and b in unlocked
            color = (120, 140, 160) if active else (68, 68, 78)
            pygame.draw.line(surface, color, pos_a, pos_b, 2)

    def _draw_nodes(self, surface, unlocked):
        for node in self.nodes:
            node_id = node["id"]
            pos = self._node_screen_pos(node)
            radius = max(4, int(node["size"] * self.zoom))
            is_unlocked = node_id in unlocked
            fill = node["color"] if is_unlocked else (46, 46, 54)
            accent = node["accent"] if is_unlocked else (90, 95, 110)
            pygame.draw.circle(surface, fill, (int(pos.x), int(pos.y)), radius)
            pygame.draw.circle(surface, accent, (int(pos.x), int(pos.y)), radius, 2)

            if node_id == self.selected_node_id:
                pygame.draw.circle(surface, (235, 235, 255), (int(pos.x), int(pos.y)), radius + 5, 2)
            elif node_id == self.hovered_node_id:
                pygame.draw.circle(surface, (200, 200, 220), (int(pos.x), int(pos.y)), radius + 3, 1)

            if node["kind"] in ("core", "major", "keystone"):
                label = self.small_font.render(node["name"], True, (220, 220, 230))
                label_rect = label.get_rect(center=(pos.x, pos.y - radius - 12))
                surface.blit(label, label_rect)

    def _draw_sidebar(self, screen, selected_node):
        pygame.draw.rect(screen, (24, 24, 30), self.sidebar_rect, border_radius=18)
        pygame.draw.rect(screen, (82, 82, 96), self.sidebar_rect, 2, border_radius=18)

        title = self.title_font.render(_("Skill Tree"), True, (235, 235, 245))
        screen.blit(title, (self.sidebar_rect.x + 18, self.sidebar_rect.y + 18))

        hint_text = _("Wheel: zoom. Right mouse: pan. Left click: inspect.")
        hint_lines = self._wrap_text(hint_text, self.small_font, self.sidebar_rect.width - 36)
        y = self.sidebar_rect.y + 70
        for line in hint_lines:
            hint = self.small_font.render(line, True, (190, 190, 200))
            screen.blit(hint, (self.sidebar_rect.x + 18, y))
            y += hint.get_height() + 4

        character = self._character()
        points = getattr(character, "skill_tree_points", 0) if character else 0
        points_text = self.section_font.render(f"{_('Points')}: {points}", True, (235, 235, 245))
        screen.blit(points_text, (self.sidebar_rect.x + 18, y + 10))
        y += points_text.get_height() + 18

        if selected_node is None:
            return

        name = self.section_font.render(selected_node["name"], True, (235, 235, 245))
        screen.blit(name, (self.sidebar_rect.x + 18, y))
        y += name.get_height() + 8

        kind_map = {
            "core": _("Core"),
            "minor": _("Minor"),
            "major": _("Notable"),
            "keystone": _("Keystone"),
        }
        kind = kind_map.get(selected_node.get("kind"), _("Unknown"))
        kind_text = self.small_font.render(f"{_('Type')}: {kind}", True, (210, 210, 220))
        screen.blit(kind_text, (self.sidebar_rect.x + 18, y))
        y += kind_text.get_height() + 6

        unlocked = self._get_unlocked_nodes()
        status_label = _("Unlocked") if selected_node["id"] in unlocked else _("Locked")
        status_text = self.small_font.render(f"{_('Status')}: {status_label}", True, (210, 210, 220))
        screen.blit(status_text, (self.sidebar_rect.x + 18, y))
        y += status_text.get_height() + 8

        effect_label = f"{_('Effect')}: {selected_node['effect']}"
        effect_lines = self._wrap_text(effect_label, self.small_font, self.sidebar_rect.width - 36)
        for line in effect_lines:
            line_surf = self.small_font.render(line, True, (210, 210, 220))
            screen.blit(line_surf, (self.sidebar_rect.x + 18, y))
            y += line_surf.get_height() + 4

        note_text = _("Effects are placeholders and do not apply yet.")
        note_lines = self._wrap_text(note_text, self.small_font, self.sidebar_rect.width - 36)
        y += 6
        for line in note_lines:
            line_surf = self.small_font.render(line, True, (180, 180, 190))
            screen.blit(line_surf, (self.sidebar_rect.x + 18, y))
            y += line_surf.get_height() + 4

    def draw(self, screen: pygame.Surface):
        self.layout(screen)

        screen.fill((16, 16, 22))
        pygame.draw.rect(screen, (20, 20, 26), self.tree_rect, border_radius=18)
        pygame.draw.rect(screen, (70, 70, 88), self.tree_rect, 2, border_radius=18)

        old_clip = screen.get_clip()
        screen.set_clip(self.tree_rect)
        self._draw_tree_background(screen)

        unlocked = self._get_unlocked_nodes()
        self._draw_links(screen, unlocked)

        mouse_pos = pygame.mouse.get_pos()
        self.hovered_node_id = self._hit_test_node(mouse_pos)
        self._draw_nodes(screen, unlocked)
        screen.set_clip(old_clip)

        selected_node = self.nodes_by_id.get(self.selected_node_id)
        self._draw_sidebar(screen, selected_node)
        self.exit_button.draw(screen)

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
    """
    Save/load menu that manages save slots and deletion.

    Attributes:
        mode (str):
            Current menu mode, either "save" or "load".
        slots (list[str]):
            List of slot identifiers displayed by the menu.

    Methods:
        __init__(app):
            Initialize the save/load menu.
        layout(screen):
            Position the buttons and menu title for the current screen size.
        refresh_saves():
            Rebuild the button list from the available save files.
        on_slot_click(slot_name):
            Save to or load from a selected slot.
        delete_slot(slot_name):
            Delete a selected save slot.
        go_back():
            Return to the previous menu.
        draw(screen):
            Render the save/load UI.
    """
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
