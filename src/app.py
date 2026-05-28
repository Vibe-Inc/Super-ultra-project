import pygame
import sys

from src.core.logger import logger
from src.core.state_manager import StateManager
from src.core.profiling import FrameProfiler, FpsCounter
from src.inventory.system import INVENTORY_manager
from src.items.items import create_item
import src.config as cfg
import src.i18n as i18n


class App:
    """
    Main application class for the Super Ultra Project game.

    This class initializes the game window, manages global state, handles language and audio, and runs the main game loop.

    Attributes:
        screen (pygame.Surface):
            The main display surface.
        icon (pygame.Surface):
            The window icon image.
        INV_manager (INVENTORY_manager):
            The inventory manager instance.
        MAIN_INV_items (list[list[tuple[Item, int] | None]]):
            2D list of main inventory items (item object, count) or None.
        audio (str):
            Audio state ("on" or "off").
        is_fullscreen (bool):
            Fullscreen mode state.
        clock (pygame.time.Clock):
            Clock object for controlling frame rate.
        manager (StateManager):
            The state management system controlling game/menu flow.

    Methods:
        __init__():
            Initialize the application, window, inventory, and state manager.
        create_logo():
            Render and position the main logo text.
        update_language(lang_code):
            Change the application language and update fonts/UI.
            Args:
                lang_code (str): Language code to switch to (e.g., 'en', 'ua').
        music_play():
            Load and start the background music, setting the volume based on the audio attribute.
        run():
            Main loop of the application. Handles rendering, event processing, clock ticking, and state management logic.
    """

    def __init__(self):
        logger.info("Initializing Application...")
        # Create the window at the exact configured resolution.
        # DPI awareness is enabled in `main.py`, so we want 1:1 pixels here.
        self.screen = pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT))
        pygame.display.set_caption("super cooool project ;)")
        self.icon = pygame.image.load("assets/smug.png")
        pygame.display.set_icon(self.icon)

        i18n.install_language(cfg.LANGUAGE)
        self.create_logo()

        self.INV_manager = INVENTORY_manager(self)
        self.MAIN_INV_items = [[None for _ in range(cfg.MAIN_INV_rows)] for _ in range(cfg.MAIN_INV_columns)]
        self.MAIN_INV_items[0][0] = [create_item("dull_sword"), 1]
        self.MAIN_INV_items[1][0] = [create_item("apple"), 5]
        
        self.money = 100

        SCREEN_BRIGHTNESS = 1.0

        # Audio / fullscreen / clock
        self.audio = "on"
        self.is_fullscreen = False
        self.clock = pygame.time.Clock()
        self._brightness_overlay = None
        self.profiler = FrameProfiler()
        self.fps_counter = FpsCounter()
        self.set_profiler_enabled(cfg.PROFILER_ENABLED)

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
            self.profiler.refresh_fonts()
            self.fps_counter.refresh_fonts()

    def set_profiler_enabled(self, enabled: bool):
        cfg.PROFILER_ENABLED = bool(enabled)
        self.profiler.set_enabled(cfg.PROFILER_ENABLED)

    def toggle_profiler(self):
        self.set_profiler_enabled(not cfg.PROFILER_ENABLED)

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
            self.profiler.begin_frame(dt)
            self.fps_counter.update(dt)

            self.screen.blit(cfg.bg, (0, 0))
            if self.manager.get_state() != "credits":
                self.screen.blit(self.text_logo, self.text_rect)

            self.profiler.start_section("state.draw")
            self.manager.draw(self.screen)
            self.profiler.end_section("state.draw")

            self.profiler.start_section("postfx")
            if cfg.SCREEN_BRIGHTNESS < 1:
                if self._brightness_overlay is None or self._brightness_overlay.get_size() != (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT):
                    self._brightness_overlay = pygame.Surface((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT))
                self._brightness_overlay.set_alpha(int((1 - cfg.SCREEN_BRIGHTNESS) * 255))
                self._brightness_overlay.fill((0, 0, 0))
                self.screen.blit(self._brightness_overlay, (0, 0))
            self.profiler.end_section("postfx")

            if self.profiler.enabled:
                self.profiler.draw(self.screen, position=(190, 100))

            screen_width = self.screen.get_width()
            self.fps_counter.draw(self.screen, position=(screen_width - 12, 12), align_right=True)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                    self.toggle_profiler()
                self.manager.handle_event(event)

            self.profiler.end_frame()