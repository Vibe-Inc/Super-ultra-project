import pygame
from typing import TYPE_CHECKING

from src.ui.menus.base import Menu
from src.ui.widgets import Button
from src.core.save_manager import SaveManager
import src.config as cfg

if TYPE_CHECKING:
    from src.app import App


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