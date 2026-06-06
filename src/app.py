import pygame
import sys

from src.core.logger import logger
from src.core.state_manager import StateManager
from src.core.save_manager import SaveManager
from src.core.profiling import FrameProfiler, FpsCounter
from src.core.article_tracker import ArticleUnlockTracker
from src.inventory.inventory_manager import INVENTORY_manager
from src.items.items import create_item
from database.item_db.weapons_db import seed_weapons
from database.item_db.consumables_db import seed_consumables
from database.item_db.armor_db import seed_armor
from database.item_db.tools_db import seed_tools
from database.item_db.fish_db import seed_fish
from database.crafting_recepies_db import seed_recipes
from database.GP_database import Gp_database
import src.config as cfg
import src.i18n as i18n


class App:
    """
    Main application class for the Super Ultra Project game.

    Initializes the game window, manages global state, handles language and audio,
    and runs the main game loop.

    Attributes:
        screen (pygame.Surface):
            The main display surface.
        icon (pygame.Surface):
            The window icon image.
        windowed_size (tuple[int, int]):
            Size of the windowed-mode display.
        is_fullscreen (bool):
            Fullscreen mode state.
        INV_manager (INVENTORY_manager):
            The inventory manager instance.
        MAIN_INV_items (list[list[tuple[Item, int] | None]]):
            2D list of main inventory items (item object, count) or None.
        money (int):
            Player currency amount.
        current_dialog (Dialog | None):
            Currently active dialog, or None.
        last_talked_npc (NPC | None):
            The last NPC the player interacted with.
        audio (str):
            Audio state ("on" or "off").
        clock (pygame.time.Clock):
            Clock object for controlling frame rate.
        _brightness_overlay (pygame.Surface | None):
            Cached dimming overlay surface.
        profiler (FrameProfiler):
            Frame profiling utility.
        fps_counter (FpsCounter):
            FPS counter display.
        manager (StateManager):
            The state management system controlling game/menu flow.
        text_logo (pygame.Surface):
            Rendered logo text surface.
        text_rect (pygame.Rect):
            Rectangle positioning the logo text.

    Methods:
        __init__():
            Initialize the application, window, inventory, and state manager.
        create_logo():
            Render and position the main logo text.
        update_language(lang_code):
            Change the application language and update fonts/UI.
        set_profiler_enabled(enabled):
            Enable or disable the frame profiler.
        toggle_profiler():
            Toggle the profiler on/off.
        _get_fullscreen_size():
            Get the native desktop resolution.
        _apply_display_mode(fullscreen, update_windowed_size=True):
            Apply fullscreen or windowed display mode.
        toggle_display_mode():
            Toggle between fullscreen and windowed mode.
        sync_display_size(width, height):
            Update window size from a resize event.
        music_play():
            Load and start the background music.
        run():
            Main loop of the application.
    """

    def __init__(self):
        logger.info("Initializing Application...")
        # Create the window at the exact configured resolution.
        # DPI awareness is enabled in `main.py`, so we want 1:1 pixels here.
        self.windowed_size = (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        self.is_fullscreen = False
        self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        pygame.display.set_caption("Codex Arcanum")
        self.icon = pygame.image.load("assets/ui/smug.png")
        pygame.display.set_icon(self.icon)

        i18n.install_language(cfg.LANGUAGE)
        self.create_logo()

        db = Gp_database()
        seed_weapons(db)
        seed_consumables(db)
        seed_armor(db)
        seed_tools(db)
        seed_fish(db)
        seed_recipes(db)
        db.close()

        self.INV_manager = INVENTORY_manager(self)
        self.MAIN_INV_items = [[None for _ in range(cfg.MAIN_INV_rows)] for _ in range(cfg.MAIN_INV_columns)]

        def add_item(col, row, item_id, count=1):
            item = create_item(item_id)
            if item:
                self.MAIN_INV_items[col][row] = [item, count]

        # Row 0 — Melee weapons
        add_item(0, 0, "dull_sword")
        add_item(1, 0, "iron_sword")
        add_item(2, 0, "steel_sword")
        add_item(3, 0, "battle_axe")
        add_item(4, 0, "war_hammer")
        add_item(5, 0, "mace")
        add_item(6, 0, "spear")
        # Row 1 — Ranged weapons + accessories
        add_item(0, 1, "wooden_bow")
        add_item(1, 1, "hunting_bow")
        add_item(2, 1, "longbow")
        add_item(3, 1, "crossbow")
        add_item(4, 1, "throwing_dagger")
        add_item(6, 1, "gay_ring")
        add_item(7, 1, "light_ring")
        add_item(5, 1, "fishing_rod")

        # Row 2 — Potions
        add_item(0, 2, "small_health_potion", 3)
        add_item(1, 2, "medium_health_potion", 2)
        add_item(2, 2, "large_health_potion", 2)
        add_item(3, 2, "greater_health_potion")
        add_item(4, 2, "potion_of_speed")
        add_item(5, 2, "potion_of_strength")
        add_item(6, 2, "potion_of_haste")
        add_item(7, 2, "potion_of_shield")

        # Row 3 — Armor
        add_item(0, 3, "iron_helmet")
        add_item(1, 3, "iron_chestplate")
        add_item(2, 3, "iron_leggings")
        add_item(3, 3, "iron_boots")
        add_item(4, 3, "steel_helmet")
        add_item(5, 3, "steel_chestplate")
        add_item(6, 3, "steel_leggings")
        add_item(7, 3, "steel_boots")
        
        self.money = 100
        self.purple_stars = 0
        self.revealed_tarot_cards: set[int] = set()

        # Unlock flags for mage-NPC gated features
        self.arcane_quests_unlocked = False
        self.mysterium_magnum_unlocked = False

        # Dialog state: current active dialog UI and last NPC the player talked to
        self.current_dialog = None
        self.last_talked_npc = None

        # Persistent collection book state — fish_id -> catch count
        self.caught_fish = {}

        # Audio / fullscreen / clock
        self.audio = "on"
        self.clock = pygame.time.Clock()
        self._brightness_overlay = None
        self.profiler = FrameProfiler()
        self.fps_counter = FpsCounter()
        self.set_profiler_enabled(cfg.PROFILER_ENABLED)

        # State manager
        self.manager = StateManager(self)

        # Article unlock tracker for auto-opening wiki articles
        self.article_tracker = ArticleUnlockTracker()

    def _get_dir_mask(self, radius: int, dir_x: float, dir_y: float) -> "pygame.Surface":
        """Return a cached hemisphere mask that attenuates light behind the character.

        The mask is a ``(2*radius, 2*radius)`` SRCALPHA surface where pixels
        in the *facing* direction are fully white (keep light) and pixels
        behind are dark (suppress light), with a smooth transition on the
        sides.  Results are cached by ``(radius, dir_x, dir_y)`` so the
        mask is only built once per unique combination.
        """
        if not hasattr(self, '_dir_mask_cache'):
            self._dir_mask_cache = {}
        key = (radius, round(dir_x, 4), round(dir_y, 4))
        if key in self._dir_mask_cache:
            return self._dir_mask_cache[key]

        size = radius * 2
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = radius
        # Use a step size that balances quality vs. build time
        step = max(1, radius // 15)
        for y in range(0, size, step):
            for x in range(0, size, step):
                px = x - cx
                py = y - cy
                dist_sq = px * px + py * py
                if dist_sq > radius * radius:
                    continue
                dist = dist_sq ** 0.5
                if dist < 1:
                    dot = 0.0
                else:
                    dot = (px * dir_x + py * dir_y) / dist
                # Map dot [-1, 1] → attenuation [0, 1.0]
                # 0 at the back = no illumination behind the character
                atten = max(0.0, dot * 0.5 + 0.5)
                a = int(atten * 255)
                pygame.draw.rect(mask, (255, 255, 255, a), (x, y, step, step))
        # Smooth the mask with a cheap down-scale / up-scale blur
        small = pygame.transform.smoothscale(mask, (size // 4 or 1, size // 4 or 1))
        mask = pygame.transform.smoothscale(small, (size, size))
        self._dir_mask_cache[key] = mask
        return mask

    def create_logo(self):
        self.text_logo = cfg.myfont.render(_('Codex Arcanum'), True, (255, 215, 0))
        self.text_rect = self.text_logo.get_rect(center=(cfg.SCREEN_WIDTH // 2, int(cfg.SCREEN_HEIGHT * 0.12)))

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
        pygame.mixer.music.set_volume(cfg.MUSIC_VOLUME if self.audio == "on" else 0.0)
        pygame.mixer.music.play(-1)

    def run(self):
        SaveManager.load_settings(self)
        self.manager.set_state("main")
        self.music_play()

        running = True
        while running:
            dt = self.clock.tick(cfg.FPS) / 1000  # seconds since last frame
            self.profiler.begin_frame(dt)
            self.fps_counter.update(dt)

            self.screen.blit(cfg.bg, (0, 0))

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

            if self.manager.get_state() in ("pause", "save_load"):
                self.screen.blit(self.text_logo, self.text_rect)

            self.profiler.start_section("postfx")
            effective_brightness = cfg.USER_SCREEN_BRIGHTNESS
            night_tint = False
            if self.manager.get_state() == "gameplay":
                effective_brightness = cfg.USER_SCREEN_BRIGHTNESS * cfg.ENVIRONMENT_BRIGHTNESS
                night_tint = cfg.ENVIRONMENT_BRIGHTNESS <= 0.55

            # Collect local light sources (lantern, lamp, etc.)
            local_lights = []
            if self.manager.get_state() == "gameplay":
                gameplay_state = self.manager.states.get("gameplay")
                try:
                    local_lights = gameplay_state.get_light_sources() if gameplay_state and hasattr(gameplay_state, 'get_light_sources') else []
                except Exception:
                    pass

            has_lights = bool(local_lights)

            # Skip day-night overlay entirely for interior maps (e.g. tavern)
            _skip_night_overlay = False
            if self.manager.get_state() == "gameplay":
                gs = self.manager.states.get("gameplay")
                if gs and getattr(gs, 'current_map_path', '') == "maps/tavern.tmx":
                    _skip_night_overlay = True

            if effective_brightness < 1 and not _skip_night_overlay:
                overlay_alpha = int((1 - effective_brightness) * 255)
                # Use the environment tint color computed by the game state for dawn/dusk/night
                if night_tint:
                    tint = cfg.ENVIRONMENT_TINT
                else:
                    tint = (0, 0, 0)

                if has_lights:
                    # Per-pixel alpha overlay: light sources make the overlay
                    # transparent so the original scene shows through (soft glow).
                    overlay = pygame.Surface(
                        (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.SRCALPHA
                    )
                    overlay.fill((tint[0], tint[1], tint[2], overlay_alpha))

                    # Determine character facing direction for directional light
                    dir_x, dir_y = 0.0, 1.0  # default: facing down
                    try:
                        char = getattr(gameplay_state, 'character', None)
                        if char:
                            facing = getattr(char, 'direction', 'down')
                            flip = getattr(char, 'flip', False)
                            if facing == 'up':
                                dir_x, dir_y = 0.0, -1.0
                            elif facing == 'side':
                                dir_x = -1.0 if flip else 1.0
                                dir_y = 0.0
                            # 'down' stays (0, 1)
                    except Exception:
                        pass

                    for l in local_lights:
                        lx, ly = l.get('pos', (0, 0))
                        radius = int(l.get('radius', 120))
                        intensity = float(l.get('intensity', 1.0))
                        even = l.get('even', False)
                        if radius <= 0:
                            continue
                        # Build a soft alpha-reduction gradient.
                        # Centre is fully transparent (reveals scene),
                        # edges keep the overlay darkness.
                        grad = pygame.Surface(
                            (radius * 2, radius * 2), pygame.SRCALPHA
                        )
                        steps = max(1, radius)
                        for i in range(steps, 0, -1):
                            frac = i / steps          # 1 at edge, 0 at centre
                            r = int(frac * radius)
                            # Alpha to SUBTRACT from the overlay: high at centre
                            if even:
                                a = int(overlay_alpha * intensity)
                            else:
                                a = int((1.0 - frac) * overlay_alpha * intensity)
                            a = max(0, min(255, a))
                            pygame.draw.circle(
                                grad, (0, 0, 0, a), (radius, radius), r
                            )
                        # Smooth the gradient to remove concentric banding
                        small = pygame.transform.smoothscale(
                            grad, (max(1, radius // 2), max(1, radius // 2))
                        )
                        grad = pygame.transform.smoothscale(
                            small, (radius * 2, radius * 2)
                        )

                        # Apply directional hemisphere mask so the light
                        # only illuminates in front and sides, not behind.
                        if not l.get('full_360'):
                            mask = self._get_dir_mask(radius, dir_x, dir_y)
                            grad.blit(
                                mask, (0, 0),
                                special_flags=pygame.BLEND_RGBA_MULT,
                            )

                        gx = lx - radius
                        gy = ly - radius
                        try:
                            overlay.blit(
                                grad, (gx, gy),
                                special_flags=pygame.BLEND_RGBA_SUB,
                            )
                        except Exception:
                            pass

                        # Colored light overlay (e.g. rainbow GayRing)
                        light_color = l.get('color')
                        if light_color:
                            clr = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                            for i in range(steps, 0, -1):
                                frac = i / steps
                                r = int(frac * radius)
                                ca = int((1.0 - frac) * 80 * intensity)
                                ca = max(0, min(255, ca))
                                pygame.draw.circle(clr, (*light_color, ca), (radius, radius), r)
                            small = pygame.transform.smoothscale(clr, (max(1, radius // 2), max(1, radius // 2)))
                            clr = pygame.transform.smoothscale(small, (radius * 2, radius * 2))
                            if not l.get('full_360'):
                                mask = self._get_dir_mask(radius, dir_x, dir_y)
                                clr.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                            try:
                                overlay.blit(clr, (gx, gy), special_flags=pygame.BLEND_RGBA_ADD)
                            except Exception:
                                pass
                else:
                    # No local lights – simple uniform darkening
                    if self._brightness_overlay is None or self._brightness_overlay.get_size() != (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT):
                        self._brightness_overlay = pygame.Surface((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT))
                    self._brightness_overlay.set_alpha(overlay_alpha)
                    self._brightness_overlay.fill(tint)
                    overlay = self._brightness_overlay

                self.screen.blit(overlay, (0, 0))
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
                    SaveManager.save_settings(self)
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