import pygame
import sys

from src.core.state_manager import StateManager
from src.inventory.system import INVENTORY_manager
from src.inventory.items import TEST_ITEMS
import src.config as cfg
import src.i18n as i18n


class App:
    """
    Main application class for the Super Ultra Project game.
    Attributes:
        screen (pygame.Surface): The main display surface.
        icon (pygame.Surface): The window icon image.

        menus (dict): Dictionary of menu states and their corresponding menu objects. # Not used in __init__
        menu_state (str): Current active menu state. # Not used in __init__

        audio (str): Audio state ("on" or "off").
        is_fullscreen (bool): Fullscreen mode state.
        clock (pygame.time.Clock): Clock object for controlling frame rate.

        manager (StateManager): The state management system controlling game/menu flow.

    Methods:
        set_menu(menu_name: str):
            Sets the current menu state using the StateManager.
        music_play():
            Loads and starts the background music, setting the volume based on the 'audio' attribute.
        run():
            Main loop of the application. Handles rendering, event processing, clock ticking, and state management logic.
    """

    def __init__(self):
        self.screen = pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT))
        pygame.display.set_caption("super cooool project ;)")
        self.icon = pygame.image.load("assets/smug.png")
        pygame.display.set_icon(self.icon)

        i18n.install_language(cfg.LANGUAGE)
        self.create_logo()

        self.INV_manager = INVENTORY_manager()
        self.MAIN_INV_items = [[None for _ in range(cfg.MAIN_INV_rows)] for _ in range(cfg.MAIN_INV_columns)]
        colors = [(255, 0, 0), (0, 0, 255), (255, 255, 0)]
        for i in range(min(cfg.MAIN_INV_columns, 3)):
            self.MAIN_INV_items[i][0] = [TEST_ITEMS(colors[i], i), i + 10]

        # Audio / fullscreen / clock
        self.audio = "on"
        self.is_fullscreen = False
        self.clock = pygame.time.Clock()

        # State manager
        self.manager = StateManager(self)

    def create_logo(self):
        self.text_logo = cfg.myfont.render(_('Super coooooool project'), True, (0, 0, 0))
        self.text_rect = self.text_logo.get_rect(center=(cfg.SCREEN_WIDTH//2, cfg.SCREEN_HEIGHT//2 - 150))

    def update_language(self, lang_code):
        if lang_code in cfg.SUPPORTED_LANGUAGES:
            cfg.LANGUAGE = lang_code
            i18n.install_language(lang_code)

            cfg.myfont = cfg.get_font(60)
            cfg.button_font = cfg.get_font(60)
            cfg.tooltip_font_CREDITS = cfg.get_font(20)
            cfg.INV_nums_font = cfg.get_font(15)
            
            self.create_logo()
            self.manager.reinit_states()

    def music_play(self):
        pygame.mixer.music.load('sounds/LIFE (Instrumental).wav')
        pygame.mixer.music.set_volume(0.3 if self.audio == "on" else 0.0)
        pygame.mixer.music.play(-1)

    def run(self):
        self.manager.set_state("main")
        self.music_play()

        running = True
        while running:
            dt = self.clock.tick(cfg.FPS) / 1000  # seconds since last frame

            self.screen.blit(cfg.bg, (0, 0))
            if self.manager.get_state() != "credits":
                self.screen.blit(self.text_logo, self.text_rect)

            self.manager.draw(self.screen)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()
                self.manager.handle_event(event)