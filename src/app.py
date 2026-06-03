import pygame
import sys

from src.core.logger import logger
from src.core.state_manager import StateManager
from src.core.profiling import FrameProfiler, FpsCounter
from src.inventory.inventory_manager import INVENTORY_manager
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
        self.windowed_size = (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        self.is_fullscreen = False
        self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        pygame.display.set_caption("super cooool project ;)")
        self.icon = pygame.image.load("assets/smug.png")
        pygame.display.set_icon(self.icon)

        i18n.install_language(cfg.LANGUAGE)
        self.create_logo()

        self.INV_manager = INVENTORY_manager(self)
        self.MAIN_INV_items = [[None for _ in range(cfg.MAIN_INV_rows)] for _ in range(cfg.MAIN_INV_columns)]
        self.MAIN_INV_items[0][0] = [create_item("dull_sword"), 1]
        self.MAIN_INV_items[1][0] = [create_item("apple"), 5]
        self.MAIN_INV_items[2][0] = [create_item("wooden_bow"), 1] #test purposes nshit
        self.MAIN_INV_items[3][0] = [create_item("throwing_dagger"), 1] #test purposes nshit
        # Test armor items
        self.MAIN_INV_items[0][1] = [create_item("iron_helmet"), 1]
        self.MAIN_INV_items[1][1] = [create_item("iron_chestplate"), 1]
        self.MAIN_INV_items[2][1] = [create_item("iron_leggings"), 1]
        self.MAIN_INV_items[3][1] = [create_item("iron_boots"), 1]
        
        self.money = 100

        # Dialog state: current active dialog UI and last NPC the player talked to
        self.current_dialog = None
        self.last_talked_npc = None

        # Audio / fullscreen / clock
        self.audio = "on"
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

            # Recompute scaled fonts for the new language and current screen size
            try:
                cfg.update_scaled_fonts()
            except Exception:
                pass
            
            self.create_logo()
            self.manager.reinit_states()
            self.profiler.refresh_fonts()
            self.fps_counter.refresh_fonts()

    def set_profiler_enabled(self, enabled: bool):
        cfg.PROFILER_ENABLED = bool(enabled)
        self.profiler.set_enabled(cfg.PROFILER_ENABLED)

    def toggle_profiler(self):
        self.set_profiler_enabled(not cfg.PROFILER_ENABLED)

    def _get_fullscreen_size(self):
        try:
            desktop_sizes = pygame.display.get_desktop_sizes()
            if desktop_sizes:
                return desktop_sizes[0]
        except Exception:
            pass

        info = pygame.display.Info()
        return info.current_w or cfg.SCREEN_WIDTH, info.current_h or cfg.SCREEN_HEIGHT

    def _apply_display_mode(self, fullscreen: bool, update_windowed_size: bool = True):
        if update_windowed_size and not self.is_fullscreen:
            self.windowed_size = self.screen.get_size()

        target_size = self._get_fullscreen_size() if fullscreen else self.windowed_size
        flags = pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE

        cfg.set_screen_size(*target_size)
        self.screen = pygame.display.set_mode(target_size, flags)
        pygame.display.set_icon(self.icon)

        self.is_fullscreen = fullscreen
        self.create_logo()
        self._brightness_overlay = None

        gameplay_state = getattr(self.manager, "states", {}).get("gameplay") if hasattr(self, "manager") else None
        if gameplay_state and hasattr(gameplay_state, "reinit_ui"):
            gameplay_state.reinit_ui()

    def toggle_display_mode(self):
        self._apply_display_mode(not self.is_fullscreen)

    def sync_display_size(self, width: int, height: int):
        if self.is_fullscreen:
            return

        self.windowed_size = (int(width), int(height))
        cfg.set_screen_size(*self.windowed_size)
        self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        pygame.display.set_icon(self.icon)
        self.create_logo()
        self._brightness_overlay = None

        gameplay_state = getattr(self.manager, "states", {}).get("gameplay") if hasattr(self, "manager") else None
        if gameplay_state and hasattr(gameplay_state, "reinit_ui"):
            gameplay_state.reinit_ui()

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
            if self.manager.get_state() == "gameplay":
                gameplay_state = self.manager.states.get("gameplay")
                if gameplay_state and hasattr(gameplay_state, "draw_scene"):
                    scene_surface = pygame.Surface(self.screen.get_size())
                    gameplay_state.draw_scene(scene_surface)
                    self.screen.blit(scene_surface, (0, 0))
                else:
                    self.manager.draw(self.screen)
            else:
                self.manager.draw(self.screen)
            self.profiler.end_section("state.draw")

            self.profiler.start_section("postfx")
            effective_brightness = cfg.USER_SCREEN_BRIGHTNESS
            night_tint = False
            if self.manager.get_state() == "gameplay":
                effective_brightness = cfg.USER_SCREEN_BRIGHTNESS * cfg.ENVIRONMENT_BRIGHTNESS
                night_tint = cfg.ENVIRONMENT_BRIGHTNESS <= 0.55

            if effective_brightness < 1:
                if self._brightness_overlay is None or self._brightness_overlay.get_size() != (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT):
                    self._brightness_overlay = pygame.Surface((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT))
                self._brightness_overlay.set_alpha(int((1 - effective_brightness) * 255))
                if night_tint:
                    self._brightness_overlay.fill((10, 24, 80))
                else:
                    self._brightness_overlay.fill((0, 0, 0))
                self.screen.blit(self._brightness_overlay, (0, 0))
            self.profiler.end_section("postfx")

            if self.manager.get_state() == "gameplay":
                gameplay_state = self.manager.states.get("gameplay")
                if gameplay_state and hasattr(gameplay_state, "draw_ui"):
                    gameplay_state.draw_ui(self.screen)

            if self.profiler.enabled:
                self.profiler.draw(self.screen, position=(190, 100))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.VIDEORESIZE:
                    self.sync_display_size(event.w, event.h)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                    self.toggle_profiler()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_display_mode()
                self.manager.handle_event(event)

            self.profiler.end_frame()