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
    Redesigned with stunning animations: glowing neon borders, particle effects,
    smooth hover animations, gradient cards, and pulsing active slots.
    """
    
    # Neon color themes for skill elements
    NEON_THEMES = {
        "fire": {"primary": (255, 80, 40), "glow": (255, 120, 60), "accent": (255, 200, 100)},
        "ice": {"primary": (60, 140, 255), "glow": (100, 180, 255), "accent": (180, 220, 255)},
        "lightning": {"primary": (255, 220, 50), "glow": (255, 240, 100), "accent": (255, 255, 180)},
        "nature": {"primary": (80, 200, 100), "glow": (120, 240, 140), "accent": (180, 255, 180)},
        "shadow": {"primary": (160, 80, 220), "glow": (200, 120, 255), "accent": (220, 180, 255)},
        "arcane": {"primary": (220, 80, 180), "glow": (255, 120, 220), "accent": (255, 180, 240)},
        "default": {"primary": (100, 140, 200), "glow": (140, 180, 240), "accent": (200, 220, 255)},
    }
    
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
        
        # Animation state
        self.animation_time = 0.0
        self.particles: list[dict] = []
        self._init_particles()
        
        # Hover animation state per slot
        self.bar_hover_anim: list[float] = [0.0] * self.bar_slots_count
        self.storage_hover_anim: list[float] = [0.0] * self.storage_slots_count
        
        # Entrance animation
        self.entrance_progress = 0.0
        self.entrance_active = True
        self.slot_entrance_delays: list[float] = []
        
        # Drag trail particles
        self.drag_trail: list[dict] = []
        
        # Glow pulse for active bar
        self.bar_glow_phase = 0.0
        
        # Drop zone highlight
        self.drop_highlight_alpha = 0.0
        self.drop_highlight_target = 0.0
    
    def _init_particles(self):
        """Initialize floating particles for ambient background effect."""
        self.particles = []
        for _ in range(45):
            self.particles.append({
                "x": random.uniform(0, 1),
                "y": random.uniform(0, 1),
                "size": random.uniform(1.5, 4),
                "speed_x": random.uniform(-0.02, 0.02),
                "speed_y": random.uniform(-0.015, -0.005),
                "alpha": random.uniform(0.2, 0.6),
                "pulse_speed": random.uniform(0.8, 2.5),
                "color": random.choice([
                    (80, 120, 200), (120, 80, 180), (180, 120, 80), 
                    (80, 180, 140), (140, 100, 200), (100, 160, 180)
                ]),
            })
    
    def _update_animations(self, dt):
        """Update all animation states."""
        self.animation_time += dt
        self.bar_glow_phase += dt * 2.0
        
        # Update entrance animation
        if self.entrance_active:
            self.entrance_progress += dt * 1.5
            if self.entrance_progress >= 1.0:
                self.entrance_progress = 1.0
                self.entrance_active = False
        
        # Update particles
        for p in self.particles:
            p["x"] += p["speed_x"] * dt
            p["y"] += p["speed_y"] * dt
            # Wrap around
            if p["y"] < -0.05:
                p["y"] = 1.05
                p["x"] = random.uniform(0, 1)
            if p["x"] < -0.05:
                p["x"] = 1.05
            elif p["x"] > 1.05:
                p["x"] = -0.05
        
        # Update hover animations
        mouse_pos = pygame.mouse.get_pos()
        for i, rect in enumerate(self.bar_slot_rects):
            is_hovered = rect.collidepoint(mouse_pos)
            target = 1.0 if is_hovered else 0.0
            self.bar_hover_anim[i] += (target - self.bar_hover_anim[i]) * min(1.0, dt * 8.0)
        
        for i, rect in enumerate(self.storage_slot_rects):
            is_hovered = rect.collidepoint(mouse_pos)
            target = 1.0 if is_hovered else 0.0
            self.storage_hover_anim[i] += (target - self.storage_hover_anim[i]) * min(1.0, dt * 8.0)
        
        # Update drop highlight
        self.drop_highlight_alpha += (self.drop_highlight_target - self.drop_highlight_alpha) * min(1.0, dt * 6.0)
        
        # Update drag trail
        if self.drag_payload:
            mx, my = pygame.mouse.get_pos()
            # Add trail particle
            if random.random() < 0.6:
                self.drag_trail.append({
                    "x": mx + random.uniform(-8, 8),
                    "y": my + random.uniform(-8, 8),
                    "size": random.uniform(3, 7),
                    "life": 0.5,
                    "max_life": 0.5,
                    "color": self.drag_payload["skill"].get("color", (100, 140, 200)),
                })
        
        # Update trail particles
        to_remove = []
        for trail in self.drag_trail:
            trail["life"] -= dt
            if trail["life"] <= 0:
                to_remove.append(trail)
        for t in to_remove:
            if t in self.drag_trail:
                self.drag_trail.remove(t)

    def _get_skill_theme(self, skill):
        """Get the neon theme for a skill based on its properties."""
        if skill is None:
            return self.NEON_THEMES["default"]
        
        skill_id = skill.get("skill_id", "").lower()
        name = skill.get("name", "").lower()
        color = skill.get("color", (100, 140, 200))
        
        # Try to match by skill_id or name
        for theme_name, theme in self.NEON_THEMES.items():
            if theme_name in skill_id or theme_name in name:
                return theme
        
        # Match by color similarity
        best_match = "default"
        best_score = 0
        for theme_name, theme in self.NEON_THEMES.items():
            primary = theme["primary"]
            # Simple color distance
            score = sum(abs(a - b) for a, b in zip(color, primary))
            if score < best_score or best_score == 0:
                best_score = score
                best_match = theme_name
        
        return self.NEON_THEMES.get(best_match, self.NEON_THEMES["default"])

    def _draw_glowing_rect(self, surface, rect, color, glow_color, glow_intensity=1.0, border_radius=12):
        """Draw a rectangle with animated neon glow effect."""
        t = self.animation_time
        
        # Pulsing glow
        pulse = (math.sin(t * 2.5) + 1.0) * 0.5
        glow_alpha = int(40 + 30 * pulse * glow_intensity)
        
        # Draw outer glow layers
        for offset in range(4, 0, -1):
            glow_rect = rect.inflate(offset * 2, offset * 2)
            alpha = glow_alpha // (offset + 1)
            glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            gc = (*glow_color, alpha)
            pygame.draw.rect(glow_surf, gc, glow_surf.get_rect(), border_radius=border_radius + offset)
            surface.blit(glow_surf, glow_rect.topleft)
        
        # Draw main rectangle
        pygame.draw.rect(surface, color, rect, border_radius=border_radius)
        
        # Draw bright border
        border_alpha = int(180 + 75 * pulse * glow_intensity)
        border_color = tuple(min(255, int(c * 1.3)) for c in glow_color)
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=border_radius)

    def _draw_animated_card(self, surface, rect, skill, hover_anim, empty_label, slot_index=0):
        """Draw a skill card with hover animation and glow effects."""
        t = self.animation_time
        
        # Calculate scale from hover animation
        scale = 1.0 + hover_anim * 0.08
        scaled_rect = rect.inflate(
            int(rect.width * (scale - 1.0)),
            int(rect.height * (scale - 1.0))
        )
        
        if skill is None:
            # Empty slot with subtle animation
            pulse = (math.sin(t * 1.5 + slot_index * 0.5) + 1.0) * 0.5
            base_color = (45 + int(10 * pulse), 45 + int(10 * pulse), 52 + int(10 * pulse))
            border_color = (100 + int(40 * pulse), 100 + int(40 * pulse), 110 + int(40 * pulse))
            
            pygame.draw.rect(surface, base_color, scaled_rect, border_radius=12)
            pygame.draw.rect(surface, border_color, scaled_rect, 2, border_radius=12)
            
            # Animated empty label
            label_alpha = int(140 + 60 * pulse)
            label = self.section_font.render(empty_label, True, (label_alpha, label_alpha, label_alpha + 10))
            surface.blit(label, label.get_rect(center=scaled_rect.center))
            return
        
        # Skill card with theme
        theme = self._get_skill_theme(skill)
        fill = skill.get("color", theme["primary"])
        accent = skill.get("accent", theme["accent"])
        glow = theme["glow"]
        
        # Hover glow effect
        if hover_anim > 0.01:
            glow_intensity = hover_anim
            for offset in range(3, 0, -1):
                glow_rect = scaled_rect.inflate(offset * 2, offset * 2)
                alpha = int(50 * glow_intensity) // offset
                glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                gc = (*glow, alpha)
                pygame.draw.rect(glow_surf, gc, glow_surf.get_rect(), border_radius=14 + offset)
                surface.blit(glow_surf, glow_rect.topleft)
        
        # Gradient fill (top lighter, bottom darker)
        grad_surf = pygame.Surface(scaled_rect.size, pygame.SRCALPHA)
        top_color = tuple(min(255, c + 30) for c in fill)
        bottom_color = tuple(max(0, c - 20) for c in fill)
        for y in range(scaled_rect.height):
            ratio = y / max(1, scaled_rect.height)
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            pygame.draw.line(grad_surf, (r, g, b), (0, y), (scaled_rect.width, y))
        
        # Create rounded mask
        mask_surf = pygame.Surface(scaled_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask_surf, (255, 255, 255, 255), mask_surf.get_rect(), border_radius=12)
        grad_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        # Draw text directly on gradient surface (no shadow/duplication)
        name = self.small_font.render(skill["name"], True, (255, 255, 255))
        name_pos = name.get_rect(center=(scaled_rect.width // 2, scaled_rect.height // 2 - 5))
        grad_surf.blit(name, name_pos)
        
        # Skill ID label
        skill_id = skill.get("skill_id", "")
        if skill_id:
            ident = self.small_font.render(skill_id.replace("_", " ").upper(), True, (200, 200, 210))
            ident_pos = ident.get_rect(center=(scaled_rect.width // 2, scaled_rect.height // 2 + 13))
            grad_surf.blit(ident, ident_pos)
        
        # Apply shimmer effect to gradient surface
        shimmer_pos = (t * 100 + slot_index * 50) % (scaled_rect.width + 100) - 50
        for x in range(max(0, int(shimmer_pos) - 15), min(scaled_rect.width, int(shimmer_pos) + 15)):
            if 0 <= x < scaled_rect.width:
                dist = abs(x - shimmer_pos)
                alpha = max(0, min(100, int(50 * (1 - dist / 15))))
                for y in range(scaled_rect.height):
                    pixel = grad_surf.get_at((x, y))
                    if pixel[3] > 0:  # Only modify visible pixels
                        new_r = min(255, pixel[0] + alpha)
                        new_g = min(255, pixel[1] + alpha)
                        new_b = min(255, pixel[2] + alpha)
                        grad_surf.set_at((x, y), (new_r, new_g, new_b, pixel[3]))
        
        surface.blit(grad_surf, scaled_rect.topleft)
        
        # Border with pulse
        pulse = (math.sin(t * 3.0 + slot_index) + 1.0) * 0.5
        border_brightness = 0.7 + 0.3 * pulse + 0.3 * hover_anim
        border_color = tuple(min(255, int(c * border_brightness)) for c in accent)
        pygame.draw.rect(surface, border_color, scaled_rect, 2, border_radius=12)

    def _draw_particle_background(self, surface, rect):
        """Draw animated particle background within a rect."""
        t = self.animation_time
        
        for p in self.particles:
            px = int(rect.x + p["x"] * rect.width)
            py = int(rect.y + p["y"] * rect.height)
            
            if not rect.collidepoint((px, py)):
                continue
            
            pulse = (math.sin(t * p["pulse_speed"]) + 1.0) * 0.5
            alpha = p["alpha"] * (0.5 + 0.5 * pulse)
            size = p["size"] * (0.8 + 0.4 * pulse)
            
            r, g, b = p["color"]
            color = (int(r * alpha), int(g * alpha), int(b * alpha))
            
            pygame.draw.circle(surface, color, (px, py), max(1, int(size)))

    def _draw_drag_trail(self, surface):
        """Draw particle trail behind dragged skill."""
        for trail in self.drag_trail:
            alpha = int(200 * (trail["life"] / trail["max_life"]))
            size = trail["size"] * (trail["life"] / trail["max_life"])
            color = trail["color"]
            
            # Glow
            glow_surf = pygame.Surface((int(size * 4), int(size * 4)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*color, alpha // 3), (int(size * 2), int(size * 2)), int(size * 2))
            surface.blit(glow_surf, (int(trail["x"] - size * 2), int(trail["y"] - size * 2)))
            
            # Core
            pygame.draw.circle(surface, color, (int(trail["x"]), int(trail["y"])), max(1, int(size)))

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
            source_area = self.drag_payload["source"][0]
            
            if target_slot is not None and target_slot[0] == "bar":
                self._on_drop(self.drag_payload["source"], ("bar", target_slot[2]))
            elif target_slot is not None and target_slot[0] == "storage":
                self._on_drop(self.drag_payload["source"], ("storage", target_slot[2]))
            elif source_area == "bar" and not self.bar_rect.collidepoint(event.pos):
                # Dropped outside the bar area - remove skill from bar
                source_index = self.drag_payload["source"][1]
                skillbar = self._skillbook()[1]
                if 0 <= source_index < len(skillbar):
                    removed_skill = skillbar[source_index]
                    skillbar[source_index] = None
                    logger.info(f"Removed skill '{removed_skill.get('name', 'unknown')}' from bar slot {source_index} by dragging outside")

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
        
        # Calculate delta time for animations
        dt = 0.016
        try:
            dt = self.app.clock.get_time() / 1000.0 if hasattr(self.app, 'clock') else 0.016
        except Exception:
            pass
        
        # Update all animations
        self._update_animations(dt)

        # Dark gradient background
        screen.fill((12, 12, 18))
        
        # Draw subtle background gradient
        bg_overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        for y in range(0, screen.get_height(), 4):
            ratio = y / screen.get_height()
            r = int(12 + 8 * ratio)
            g = int(12 + 6 * ratio)
            b = int(18 + 12 * ratio)
            pygame.draw.line(bg_overlay, (r, g, b, 240), (0, y), (screen.get_width(), y))
        screen.blit(bg_overlay, (0, 0))
        
        # Draw floating particles in background
        self._draw_particle_background(screen, screen.get_rect())

        skillbook, skillbar = self._sync_state_to_character()
        if skillbook is None:
            skillbook, skillbar = self._skillbook()
        storage_items = self._storage_items(skillbook, skillbar)

        # Calculate entrance animation offset
        entrance_offset = 0.0
        if self.entrance_active:
            # Ease out cubic
            t = self.entrance_progress
            entrance_offset = (1.0 - t) * 50.0
        
        # Draw section titles with glow
        t = self.animation_time
        title_pulse = (math.sin(t * 2.0) + 1.0) * 0.5
        
        bar_title = self.section_font.render(_("6 active slots"), True, (235, 235, 245))
        title_y = max(12, int(self.bar_rect.y - bar_title.get_height() - 8 - entrance_offset))
        # Title glow
        glow_surf = pygame.Surface((bar_title.get_width() + 20, bar_title.get_height() + 10), pygame.SRCALPHA)
        glow_alpha = int(30 + 20 * title_pulse)
        glow_surf.fill((100, 140, 220, glow_alpha))
        screen.blit(glow_surf, (self.bar_rect.x - 10, title_y - 5))
        screen.blit(bar_title, (self.bar_rect.x, title_y))

        storage_title = self.section_font.render(_("Unused skills"), True, (235, 235, 245))
        storage_title_y = max(12, int(self.storage_grid_rect.y - storage_title.get_height() - 8 + entrance_offset))
        glow_surf2 = pygame.Surface((storage_title.get_width() + 20, storage_title.get_height() + 10), pygame.SRCALPHA)
        glow_surf2.fill((100, 140, 220, glow_alpha))
        screen.blit(glow_surf2, (self.storage_grid_rect.x - 10, storage_title_y - 5))
        screen.blit(storage_title, (self.storage_grid_rect.x, storage_title_y))

        # Draw bar container with animated neon border
        bar_color = (22, 22, 30)
        bar_glow = (80, 120, 200)
        self._draw_glowing_rect(screen, self.bar_rect, bar_color, bar_glow, 0.6 + 0.4 * title_pulse, 18)
        
        # Draw storage container with animated neon border
        storage_glow = (100, 80, 180)
        self._draw_glowing_rect(screen, self.storage_grid_rect, bar_color, storage_glow, 0.5 + 0.3 * title_pulse, 18)
        
        # Draw sidebar with gradient
        sidebar_grad = pygame.Surface(self.sidebar_rect.size, pygame.SRCALPHA)
        for y in range(self.sidebar_rect.height):
            ratio = y / max(1, self.sidebar_rect.height)
            r = int(26 + 8 * ratio)
            g = int(26 + 6 * ratio)
            b = int(34 + 10 * ratio)
            pygame.draw.line(sidebar_grad, (r, g, b, 245), (0, y), (self.sidebar_rect.width, y))
        screen.blit(sidebar_grad, self.sidebar_rect.topleft)
        
        # Sidebar neon border
        sidebar_glow = (90, 70, 160)
        pygame.draw.rect(screen, sidebar_glow, self.sidebar_rect, 2, border_radius=18)
        # Inner glow line
        inner_rect = self.sidebar_rect.inflate(-4, -4)
        sidebar_glow2 = tuple(max(0, c - 40) for c in sidebar_glow)
        pygame.draw.rect(screen, sidebar_glow2, inner_rect, 1, border_radius=16)

        # Draw bar slots with entrance animation
        for index, slot_rect in enumerate(self.bar_slot_rects):
            # Staggered entrance
            if self.entrance_active:
                delay = index * 0.08
                slot_progress = max(0, min(1, (self.entrance_progress - delay) * 2))
                # Ease out back
                t_slot = slot_progress
                c1 = 1.70158
                c3 = c1 + 1
                eased = 1 + c3 * pow(t_slot - 1, 3) + c1 * pow(t_slot - 1, 2)
                scale = max(0.01, eased)
                
                # Apply scale animation
                center = slot_rect.center
                w = int(slot_rect.width * scale)
                h = int(slot_rect.height * scale)
                animated_rect = pygame.Rect(center[0] - w // 2, center[1] - h // 2, w, h)
            else:
                animated_rect = slot_rect
            
            skill = skillbar[index] if index < len(skillbar) else None
            hover = self.bar_hover_anim[index] if index < len(self.bar_hover_anim) else 0.0
            self._draw_animated_card(screen, animated_rect, skill, hover, str(index + 1), index)

        # Draw storage slots with entrance animation
        for index, slot_rect in enumerate(self.storage_slot_rects):
            # Staggered entrance (reverse order)
            if self.entrance_active:
                delay = (len(self.storage_slot_rects) - index - 1) * 0.06
                slot_progress = max(0, min(1, (self.entrance_progress - 0.3 - delay) * 2))
                t_slot = slot_progress
                c1 = 1.70158
                c3 = c1 + 1
                eased = 1 + c3 * pow(t_slot - 1, 3) + c1 * pow(t_slot - 1, 2)
                scale = max(0.01, eased)
                
                center = slot_rect.center
                w = int(slot_rect.width * scale)
                h = int(slot_rect.height * scale)
                animated_rect = pygame.Rect(center[0] - w // 2, center[1] - h // 2, w, h)
            else:
                animated_rect = slot_rect
            
            skill = storage_items[index] if index < len(storage_items) else None
            hover = self.storage_hover_anim[index] if index < len(self.storage_hover_anim) else 0.0
            self._draw_animated_card(screen, animated_rect, skill, hover, "+", index)

        # Draw drag trail particles
        self._draw_drag_trail(screen)

        # Draw sidebar content
        self._draw_sidebar(screen)
        self.exit_button.draw(screen)

        # Draw dragged skill with enhanced ghost effect
        if self.drag_payload:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            skill = self.drag_payload["skill"]
            ghost_size = self.bar_slot_rects[0].width if self.bar_slot_rects else 56
            
            # Create ghost surface
            ghost = pygame.Surface((ghost_size, ghost_size), pygame.SRCALPHA)
            
            # Draw animated card on ghost
            theme = self._get_skill_theme(skill)
            fill = skill.get("color", theme["primary"])
            
            # Gradient fill
            for y in range(ghost_size):
                ratio = y / ghost_size
                r = int(fill[0] * (1.3 - 0.3 * ratio))
                g = int(fill[1] * (1.3 - 0.3 * ratio))
                b = int(fill[2] * (1.3 - 0.3 * ratio))
                pygame.draw.line(ghost, (min(255, r), min(255, g), min(255, b)), (0, y), (ghost_size, y))
            
            # Rounded mask
            mask = pygame.Surface((ghost_size, ghost_size), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=12)
            ghost.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            
            # Border
            pygame.draw.rect(ghost, theme["accent"], ghost.get_rect(), 2, border_radius=12)
            
            # Skill name
            name = self.small_font.render(skill.get("name", ""), True, (255, 255, 255))
            ghost.blit(name, name.get_rect(center=(ghost_size // 2, ghost_size // 2 - 5)))
            
            # Check if dragging outside bar area (for removal indicator)
            source_area = self.drag_payload["source"][0]
            is_outside_bar = source_area == "bar" and not self.bar_rect.collidepoint((mouse_x, mouse_y))
            
            if is_outside_bar:
                # Red overlay for removal
                red_overlay = pygame.Surface((ghost_size, ghost_size), pygame.SRCALPHA)
                red_overlay.fill((200, 50, 50, 120))
                ghost.blit(red_overlay, (0, 0))
                # Animated red X
                x_margin = ghost_size // 4
                pulse = (math.sin(t * 5) + 1.0) * 0.5
                x_color = (255, int(60 + 40 * pulse), int(60 + 40 * pulse))
                pygame.draw.line(ghost, x_color, (x_margin, x_margin), (ghost_size - x_margin, ghost_size - x_margin), 4)
                pygame.draw.line(ghost, x_color, (ghost_size - x_margin, x_margin), (x_margin, ghost_size - x_margin), 4)
            
            # Outer glow for ghost
            glow_size = ghost_size + 16
            glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            glow_color = theme["glow"]
            pygame.draw.rect(glow_surf, (*glow_color, 60), glow_surf.get_rect(), border_radius=16)
            inner_cut = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.rect(inner_cut, (0, 0, 0, 255), inner_cut.get_rect().inflate(-16, -16), border_radius=12)
            glow_surf.blit(inner_cut, (8, 8), special_flags=pygame.BLEND_RGBA_MIN)
            
            ghost.set_alpha(230)
            screen.blit(glow_surf, (mouse_x - self.drag_offset[0] - 8, mouse_y - self.drag_offset[1] - 8))
            screen.blit(ghost, (mouse_x - self.drag_offset[0], mouse_y - self.drag_offset[1]))
        
        # Update drop highlight target based on drag state
        if self.drag_payload:
            target_slot = self._slot_at_position(pygame.mouse.get_pos())
            if target_slot and target_slot[0] == "bar":
                self.drop_highlight_target = 1.0
            else:
                self.drop_highlight_target = 0.0
        else:
            self.drop_highlight_target = 0.0
        
        # Draw drop zone highlight
        if self.drop_highlight_alpha > 0.01:
            highlight_surf = pygame.Surface(self.bar_rect.size, pygame.SRCALPHA)
            alpha = int(80 * self.drop_highlight_alpha)
            pulse = (math.sin(t * 4) + 1.0) * 0.5
            extra_alpha = int(30 * pulse * self.drop_highlight_alpha)
            highlight_surf.fill((100, 200, 100, alpha + extra_alpha))
            screen.blit(highlight_surf, self.bar_rect.topleft)


class SkillTreeMenu(Menu):
    """
    Enhanced skill tree screen inspired by Path of Exile with visual wow effects.
    Features: animated glowing nodes, particle background, gradient links, 
    pulsing selection, branch color themes, and expanded node count.
    """
    
    # Branch color themes for different areas of the tree
    BRANCH_THEMES = {
        "fire": {"primary": (180, 60, 30), "secondary": (255, 120, 50), "accent": (255, 200, 100), "glow": (255, 80, 20)},
        "ice": {"primary": (40, 100, 180), "secondary": (80, 160, 255), "accent": (180, 220, 255), "glow": (60, 140, 255)},
        "lightning": {"primary": (160, 140, 40), "secondary": (255, 230, 80), "accent": (255, 255, 180), "glow": (255, 220, 50)},
        "nature": {"primary": (50, 140, 60), "secondary": (100, 200, 100), "accent": (180, 255, 180), "glow": (80, 220, 80)},
        "shadow": {"primary": (100, 50, 140), "secondary": (160, 100, 220), "accent": (220, 180, 255), "glow": (140, 80, 200)},
        "arcane": {"primary": (140, 60, 120), "secondary": (220, 100, 200), "accent": (255, 180, 240), "glow": (200, 80, 180)},
    }
    
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
        # Unlock button placed above the exit button in the sidebar
        self.unlock_button = Button(
            pygame.Rect(0, 0, exit_width, exit_height),
            "",
            (70, 110, 70),
            (95, 150, 95),
            cfg.button_font,
            cfg.text_color,
            cfg.corner_radius,
            on_click=self._unlock_selected,
        )
        self.buttons = [self.exit_button, self.unlock_button]

        self.zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 1.8
        self.pan_offset = pygame.Vector2(0, 0)
        self.dragging_view = False
        self.drag_origin = pygame.Vector2(0, 0)
        self.drag_start_offset = pygame.Vector2(0, 0)

        # Animation state
        self.animation_time = 0
        self.particles = []
        self._init_particles()
        
        # Unlock animation effects
        self.unlock_effects = []  # list of active unlock animations
        self.screen_flash_alpha = 0  # for screen flash effect
        self.screen_flash_timer = 0
        
        # Entrance animation (tree assembling on open) — multi-phase cinematic
        self.entrance_active = False
        self.entrance_progress = 0.0      # 0.0 = start, 1.0 = fully assembled
        self.entrance_sparks = []          # converging spark particles
        self.entrance_glow = 0
        self._entrance_triggered = False   # prevent re-triggering
        self._entrance_animation_played = False  # only play animation once
        
        # Phase system: 0=void, 1=starfield, 2=convergence, 3=core_ignition, 4=branch_growth, 5=settled
        self.entrance_phase = 0
        self.entrance_phase_time = 0.0     # time spent in current phase
        self.entrance_total_time = 0.0     # total elapsed time
        
        # Core ignition effect
        self.core_ignition_flash = 0.0
        self.core_ignition_rings = []      # expanding energy rings from core
        self.core_ignition_particles = []  # particles bursting from core
        
        # Branch growth: track which nodes/links have been "reached" by the growing energy
        self.entrance_revealed_nodes = set()   # node IDs that have lit up
        self.entrance_revealed_links = set()   # (a,b) link tuples that have lit up
        self.entrance_growth_frontier = []     # list of (node_id, arrival_time) for BFS growth
        self.entrance_link_travels = []        # visual energy traveling along links
        
        # Background star fade-in
        self.entrance_star_alpha = 0.0
        
        # Swirling convergence vortex particles
        self.entrance_vortex = []
        
        self.nodes, self.links = self._build_tree()
        self.nodes_by_id = {node["id"]: node for node in self.nodes}
        self.selected_node_id = "core"
        self.hovered_node_id = None
        self.background_points = self._build_background_points()

        self.tree_rect = pygame.Rect(0, 0, 0, 0)
        self.sidebar_rect = pygame.Rect(0, 0, 0, 0)
        self._layout_size = None
        
    def on_enter(self):
        """Called when this state becomes active. Resets and triggers the entrance animation (only first time)."""
        self._entrance_triggered = False
        # Only play the entrance animation the first time the skill tree is opened
        if not self._entrance_animation_played:
            self.trigger_entrance_animation()
        else:
            # Skip animation - set everything to fully revealed state
            self.entrance_active = False
            self.entrance_phase = 6
            self.entrance_progress = 1.0
            self.entrance_star_alpha = 1.0
            # Reveal all nodes immediately
            self.entrance_revealed_nodes = {node["id"] for node in self.nodes}

    def _init_particles(self):
        """Initialize floating particles for ambient background effect."""
        self.particles = []
        for _ in range(60):
            self.particles.append({
                "x": random.uniform(-700, 700),
                "y": random.uniform(-600, 600),
                "size": random.uniform(1, 3),
                "speed_x": random.uniform(-0.2, 0.2),
                "speed_y": random.uniform(-0.3, -0.05),
                "alpha": random.uniform(0.3, 0.8),
                "pulse_speed": random.uniform(0.5, 2.0),
                "color": random.choice([(100, 140, 200), (140, 100, 180), (180, 140, 100), (100, 180, 140)]),
            })

    def trigger_entrance_animation(self):
        """Start the multi-phase cinematic entrance animation when the skill tree opens."""
        if self._entrance_triggered:
            return
        self._entrance_triggered = True
        self.entrance_active = True
        self.entrance_progress = 0.0
        self.entrance_phase = 0
        self.entrance_phase_time = 0.0
        self.entrance_total_time = 0.0
        
        # Reset all entrance state
        self.entrance_revealed_nodes = set()
        self.entrance_revealed_links = set()
        self.entrance_growth_frontier = []
        self.entrance_link_travels = []
        self.entrance_star_alpha = 0.0
        self.core_ignition_flash = 0.0
        self.core_ignition_rings = []
        self.core_ignition_particles = []
        self.entrance_vortex = []
        self.entrance_sparks = []
        self.entrance_glow = 1.0
        
        rng = random.Random(42)
        
        # Pre-generate vortex particles that will spiral into the center
        self.entrance_vortex = []
        for _ in range(120):
            angle = rng.uniform(0, math.pi * 2)
            dist = rng.uniform(300, 700)
            speed = rng.uniform(0.6, 1.8)
            orbit_speed = rng.uniform(1.5, 4.0) * rng.choice([-1, 1])
            size = rng.uniform(1.5, 5.0)
            brightness = rng.uniform(0.5, 1.0)
            # Color from a random branch
            branch = rng.choice(list(self.BRANCH_THEMES.keys()))
            theme = self.BRANCH_THEMES[branch]
            color = rng.choice([theme["glow"], theme["primary"], theme["secondary"], theme["accent"]])
            self.entrance_vortex.append({
                "angle": angle,
                "dist": dist,
                "initial_dist": dist,
                "speed": speed,           # radial inward speed
                "orbit_speed": orbit_speed,  # angular speed (radians/sec)
                "size": size,
                "brightness": brightness,
                "color": color,
                "alpha": 0.0,
                "trail": [],
            })
        
        # Pre-generate the sparks that converge from edges (kept for extra flair)
        for node in self.nodes:
            count = 2 + (node["size"] // 6)
            for _ in range(count):
                side = rng.randint(0, 3)
                if side == 0:
                    sx = rng.uniform(-750, 750)
                    sy = rng.uniform(-700, -600)
                elif side == 1:
                    sx = rng.uniform(-750, 750)
                    sy = rng.uniform(600, 700)
                elif side == 2:
                    sx = rng.uniform(-800, -700)
                    sy = rng.uniform(-650, 650)
                else:
                    sx = rng.uniform(700, 800)
                    sy = rng.uniform(-650, 650)
                
                target_pos = node["pos"]
                branch = node.get("branch", "arcane")
                theme = self.BRANCH_THEMES.get(branch, self.BRANCH_THEMES["arcane"])
                color = rng.choice([theme["glow"], theme["primary"], theme["secondary"], theme["accent"], (255, 255, 255)])
                travel_time = rng.uniform(0.5, 1.8)
                
                self.entrance_sparks.append({
                    "x": sx,
                    "y": sy,
                    "start_x": sx,
                    "start_y": sy,
                    "target_x": target_pos.x,
                    "target_y": target_pos.y,
                    "progress": 0.0,
                    "speed": 1.0 / travel_time,
                    "size": rng.uniform(1.0, 3.5),
                    "color": color,
                    "alpha": 1.0,
                    "arrived": False,
                    "delay": rng.uniform(0.0, 0.5),
                    "node_id": node["id"],
                })
        rng.shuffle(self.entrance_sparks)

    def _update_entrance(self, dt):
        """Update the multi-phase cinematic entrance animation."""
        if not self.entrance_active:
            return
        
        self.entrance_phase_time += dt
        self.entrance_total_time += dt
        
        # ─── Phase transitions ───
        if self.entrance_phase == 0:
            # Phase 0: Void — brief darkness (0.4s)
            if self.entrance_phase_time >= 0.4:
                self.entrance_phase = 1
                self.entrance_phase_time = 0.0
        
        elif self.entrance_phase == 1:
            # Phase 1: Starfield — background stars fade in (0.8s)
            self.entrance_star_alpha = min(1.0, self.entrance_phase_time / 0.8)
            if self.entrance_phase_time >= 0.8:
                self.entrance_phase = 2
                self.entrance_phase_time = 0.0
        
        elif self.entrance_phase == 2:
            # Phase 2: Convergence — vortex particles spiral inward (1.8s)
            # Also start moving sparks toward their targets
            progress = min(1.0, self.entrance_phase_time / 1.8)
            self.entrance_progress = progress * 0.3  # map to 0..0.3 range
            
            # Update vortex particles: spiral inward
            for vp in self.entrance_vortex:
                # Fade in
                vp["alpha"] = min(vp["brightness"], vp["alpha"] + dt * 2.0)
                # Spiral inward
                vp["dist"] = max(0, vp["dist"] - vp["speed"] * 180 * dt)
                vp["angle"] += vp["orbit_speed"] * dt
                # Update position
                vp["x"] = math.cos(vp["angle"]) * vp["dist"]
                vp["y"] = math.sin(vp["angle"]) * vp["dist"]
                # Store trail point
                vp["trail"].append((vp["x"], vp["y"], vp["alpha"]))
                if len(vp["trail"]) > 12:
                    vp["trail"].pop(0)
            
            # Also update sparks (they start moving during convergence)
            self._update_entrance_sparks(dt)
            
            if self.entrance_phase_time >= 1.8:
                self.entrance_phase = 3
                self.entrance_phase_time = 0.0
                # Trigger core ignition!
                self.core_ignition_flash = 1.0
                # Spawn expanding energy rings from core
                for i in range(5):
                    self.core_ignition_rings.append({
                        "radius": 0,
                        "max_radius": 200 + i * 80,
                        "speed": 250 + i * 40,
                        "alpha": 0.9 - i * 0.1,
                        "width": 4 - i * 0.5,
                        "delay": i * 0.12,
                        "started": False,
                    })
                # Spawn burst particles from core
                for _ in range(60):
                    angle = random.uniform(0, math.pi * 2)
                    speed = random.uniform(80, 300)
                    life = random.uniform(0.5, 1.5)
                    branch = random.choice(list(self.BRANCH_THEMES.keys()))
                    theme = self.BRANCH_THEMES[branch]
                    color = random.choice([theme["glow"], theme["accent"], (255, 255, 255)])
                    self.core_ignition_particles.append({
                        "x": 0, "y": 0,
                        "vx": math.cos(angle) * speed,
                        "vy": math.sin(angle) * speed,
                        "size": random.uniform(2, 6),
                        "life": life,
                        "max_life": life,
                        "color": color,
                        "alpha": 1.0,
                    })
                # Start BFS growth from core
                self.entrance_revealed_nodes.add("core")
                # Add all nodes linked to core to the frontier
                for a, b in self.links:
                    if a == "core":
                        self.entrance_growth_frontier.append((b, 0.0))
                    elif b == "core":
                        self.entrance_growth_frontier.append((a, 0.0))
        
        elif self.entrance_phase == 3:
            # Phase 3: Core ignition flash + rings expanding (1.2s)
            self.core_ignition_flash = max(0, self.core_ignition_flash - dt * 2.5)
            
            # Update ignition rings
            for ring in self.core_ignition_rings:
                if ring["delay"] > 0:
                    ring["delay"] -= dt
                    continue
                ring["started"] = True
                ring["radius"] += ring["speed"] * dt
                ring["alpha"] = max(0, ring["alpha"] - dt * 0.8)
                ring["width"] = max(0.5, ring["width"] - dt * 1.5)
            
            # Update ignition particles
            for p in self.core_ignition_particles:
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["vx"] *= 0.97
                p["vy"] *= 0.97
                p["life"] -= dt
                p["alpha"] = max(0, p["life"] / p["max_life"])
            
            # Continue updating vortex (they're settling now)
            for vp in self.entrance_vortex:
                vp["dist"] = max(0, vp["dist"] - vp["speed"] * 60 * dt)
                vp["angle"] += vp["orbit_speed"] * 0.5 * dt
                vp["x"] = math.cos(vp["angle"]) * vp["dist"]
                vp["y"] = math.sin(vp["angle"]) * vp["dist"]
                vp["alpha"] = max(0, vp["alpha"] - dt * 0.5)
                vp["trail"].append((vp["x"], vp["y"], vp["alpha"]))
                if len(vp["trail"]) > 8:
                    vp["trail"].pop(0)
            
            # Continue sparks
            self._update_entrance_sparks(dt)
            
            self.entrance_progress = 0.3 + min(0.15, self.entrance_phase_time / 1.2 * 0.15)
            
            if self.entrance_phase_time >= 1.2:
                self.entrance_phase = 4
                self.entrance_phase_time = 0.0
        
        elif self.entrance_phase == 4:
            # Phase 4: Branch growth — energy spreads from core outward through links
            # BFS-style reveal with timed delays
            growth_speed = 220  # nodes per second conceptually
            max_phase_duration = 8.0  # fallback timeout
            
            # Process frontier: reveal nodes and spawn link travels
            new_frontier = []
            for node_id, arrival_time in self.entrance_growth_frontier:
                if node_id in self.entrance_revealed_nodes:
                    continue
                if self.entrance_phase_time >= arrival_time:
                    self.entrance_revealed_nodes.add(node_id)
                    # Find links from this node to unrevealed neighbors
                    for a, b in self.links:
                        neighbor = None
                        if a == node_id and b not in self.entrance_revealed_nodes:
                            neighbor = b
                        elif b == node_id and a not in self.entrance_revealed_nodes:
                            neighbor = a
                        if neighbor is not None:
                            # Calculate distance for travel time
                            node_a = self.nodes_by_id.get(a)
                            node_b = self.nodes_by_id.get(b)
                            if node_a and node_b:
                                dist = math.sqrt((node_a["pos"].x - node_b["pos"].x)**2 + 
                                                (node_a["pos"].y - node_b["pos"].y)**2)
                                travel_time = dist / growth_speed
                                link_key = (min(a, b), max(a, b))
                                if link_key not in self.entrance_revealed_links:
                                    self.entrance_revealed_links.add(link_key)
                                    self.entrance_link_travels.append({
                                        "from_id": node_id,
                                        "to_id": neighbor,
                                        "progress": 0.0,
                                        "speed": 1.0 / max(0.15, travel_time),
                                        "alpha": 1.0,
                                    })
                                # Only add if not already in new_frontier
                                if not any(nid == neighbor for nid, _ in new_frontier):
                                    new_frontier.append((neighbor, self.entrance_phase_time + travel_time))
                else:
                    # Node hasn't reached arrival time yet — keep it in the frontier!
                    if not any(nid == node_id for nid, _ in new_frontier):
                        new_frontier.append((node_id, arrival_time))
            
            self.entrance_growth_frontier = new_frontier
            
            # Update link travel visuals
            for travel in self.entrance_link_travels:
                travel["progress"] = min(1.0, travel["progress"] + dt * travel["speed"])
                if travel["progress"] >= 1.0:
                    travel["alpha"] = max(0, travel["alpha"] - dt * 3.0)
            
            # Clean up finished travels
            self.entrance_link_travels = [t for t in self.entrance_link_travels if t["alpha"] > 0.01]
            
            # Update remaining sparks
            self._update_entrance_sparks(dt)
            
            # Progress: 0.45 to 0.9
            self.entrance_progress = 0.45 + min(0.45, self.entrance_phase_time / max_phase_duration * 0.45)
            
            # Check if all nodes are revealed and travels done, OR timeout reached
            all_revealed = len(self.entrance_revealed_nodes) >= len(self.nodes)
            all_travels_done = len(self.entrance_link_travels) == 0
            timeout_reached = self.entrance_phase_time >= max_phase_duration
            if (all_revealed and all_travels_done) or timeout_reached:
                self.entrance_phase = 5
                self.entrance_phase_time = 0.0
        
        elif self.entrance_phase == 5:
            # Phase 5: Settlement — everything is revealed, gentle fade to normal
            self.entrance_progress = min(1.0, self.entrance_progress + dt * 2.0)
            
            # Fade out remaining vortex
            for vp in self.entrance_vortex:
                vp["alpha"] = max(0, vp["alpha"] - dt * 2.0)
            
            # Clean up ignition effects
            self.core_ignition_particles = [p for p in self.core_ignition_particles if p["life"] > 0]
            
            # Clear any remaining link travels to prevent lights staying on
            self.entrance_link_travels = []
            
            if self.entrance_progress >= 1.0:
                self.entrance_active = False
                self.entrance_phase = 6  # done
                self._entrance_animation_played = True  # don't play animation again
                # Final celebratory flash
                self.screen_flash_alpha = 0.15
                self.screen_flash_timer = 0.25
    
    def _update_entrance_sparks(self, dt):
        """Update the converging spark particles during entrance."""
        for spark in self.entrance_sparks:
            if spark["arrived"]:
                continue
            if spark["delay"] > 0:
                spark["delay"] -= dt
                continue
            
            spark["progress"] += dt * spark["speed"]
            if spark["progress"] >= 1.0:
                spark["progress"] = 1.0
                spark["x"] = spark["target_x"]
                spark["y"] = spark["target_y"]
                spark["arrived"] = True
            else:
                t = spark["progress"]
                ease = t * t * (3 - 2 * t)
                spark["x"] = spark["start_x"] + (spark["target_x"] - spark["start_x"]) * ease
                spark["y"] = spark["start_y"] + (spark["target_y"] - spark["start_y"]) * ease
                if ease < 0.5:
                    spark["alpha"] = 0.6 + 0.4 * (ease / 0.5)
                else:
                    spark["alpha"] = 0.6 + 0.4 * ((1.0 - ease) / 0.5)

    def _draw_entrance_sparks(self, surface):
        """Draw all entrance animation effects: vortex, sparks, core ignition, branch growth."""
        if self.entrance_phase == 0:
            # Phase 0: void — draw nothing extra
            return
        
        origin = pygame.Vector2(self.tree_rect.center) + self.pan_offset
        
        # ─── Phase 1+: Background star fade-in overlay ───
        # (Stars are drawn in _draw_tree_background, controlled by entrance_star_alpha)
        
        # ─── Phase 2+: Swirling vortex particles ───
        if self.entrance_phase >= 2 and self.entrance_vortex:
            for vp in self.entrance_vortex:
                if vp["alpha"] <= 0.01:
                    continue
                sx = origin.x + vp.get("x", 0) * self.zoom
                sy = origin.y + vp.get("y", 0) * self.zoom
                
                if not self.tree_rect.collidepoint((int(sx), int(sy))):
                    continue
                
                alpha = vp["alpha"]
                color = vp["color"]
                size = max(1, vp["size"] * self.zoom)
                
                # Draw trail — apply alpha to color so trails fade out properly
                if alpha > 0.02:
                    trail = vp.get("trail", [])
                    if len(trail) >= 2:
                        for i in range(len(trail) - 1):
                            tx, ty, ta = trail[i]
                            tx2, ty2, ta2 = trail[i + 1]
                            trail_sx = origin.x + tx * self.zoom
                            trail_sy = origin.y + ty * self.zoom
                            trail_sx2 = origin.x + tx2 * self.zoom
                            trail_sy2 = origin.y + ty2 * self.zoom
                            trail_brightness = ta * alpha * (i / max(1, len(trail) - 1))
                            if trail_brightness > 0.03:
                                trail_color = tuple(max(0, min(255, int(c * trail_brightness))) for c in color)
                                pygame.draw.line(surface, trail_color,
                                               (int(trail_sx), int(trail_sy)),
                                               (int(trail_sx2), int(trail_sy2)),
                                               max(1, int(size * 0.6)))
                
                # Draw glow
                glow_r = max(2, int(size * 3))
                glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                glow_a = int(60 * alpha)
                pygame.draw.circle(glow_surf, (color[0], color[1], color[2], glow_a), (glow_r, glow_r), glow_r)
                surface.blit(glow_surf, (int(sx) - glow_r, int(sy) - glow_r))
                
                # Draw core
                core_a = int(255 * alpha)
                core_color = tuple(min(255, c + 40) for c in color)
                pygame.draw.circle(surface, core_color, (int(sx), int(sy)), max(1, int(size)))
        
        # ─── Phase 2+: Converging sparks ───
        for spark in self.entrance_sparks:
            if spark["arrived"] and self.entrance_phase >= 4:
                continue
            
            screen_x = origin.x + spark["x"] * self.zoom
            screen_y = origin.y + spark["y"] * self.zoom
            
            if not self.tree_rect.collidepoint((int(screen_x), int(screen_y))):
                continue
            
            phase_factor = min(1.0, max(0.0, (self.entrance_total_time - 0.8) / 0.5))
            alpha = int(255 * spark["alpha"] * phase_factor)
            if alpha <= 5:
                continue
            
            color = spark["color"]
            size = max(0.5, spark["size"] * self.zoom * (0.8 + 0.4 * (1.0 - spark["progress"])))
            
            # Glow
            glow_r = max(1, int(size * 2.5))
            for g in range(2):
                gc = tuple(int(c * (0.25 - g * 0.08)) for c in color)
                pygame.draw.circle(surface, gc, (int(screen_x), int(screen_y)), glow_r - g * 2)
            
            # Core
            core_color = tuple(min(255, int(c + 50)) for c in color)
            pygame.draw.circle(surface, core_color, (int(screen_x), int(screen_y)), max(1, int(size)))
            
            # Trail
            if spark["progress"] > 0.05 and not spark["arrived"]:
                t = spark["progress"]
                ease = t * t * (3 - 2 * t)
                trail_factor = max(0.05, ease - 0.04)
                trail_ease = trail_factor * trail_factor * (3 - 2 * trail_factor)
                trail_x = origin.x + (spark["start_x"] + (spark["target_x"] - spark["start_x"]) * trail_ease) * self.zoom
                trail_y = origin.y + (spark["start_y"] + (spark["target_y"] - spark["start_y"]) * trail_ease) * self.zoom
                pygame.draw.line(surface, color,
                                 (int(trail_x), int(trail_y)), (int(screen_x), int(screen_y)),
                                 max(1, int(size * 0.4)))
        
        # ─── Phase 3: Core ignition flash ───
        if self.core_ignition_flash > 0.01:
            core_node = self.nodes_by_id.get("core")
            if core_node:
                cx = origin.x + core_node["pos"].x * self.zoom
                cy = origin.y + core_node["pos"].y * self.zoom
                
                # Bright flash
                flash_r = int(120 * self.core_ignition_flash * self.zoom)
                flash_surf = pygame.Surface((flash_r * 2, flash_r * 2), pygame.SRCALPHA)
                flash_a = int(200 * self.core_ignition_flash)
                pygame.draw.circle(flash_surf, (200, 220, 255, flash_a), (flash_r, flash_r), flash_r)
                inner_r = int(flash_r * 0.4)
                pygame.draw.circle(flash_surf, (255, 255, 255, min(255, flash_a + 50)), (flash_r, flash_r), inner_r)
                surface.blit(flash_surf, (int(cx) - flash_r, int(cy) - flash_r))
        
        # ─── Phase 3: Core ignition expanding rings ───
        for ring in self.core_ignition_rings:
            if not ring["started"] or ring["alpha"] <= 0.01:
                continue
            core_node = self.nodes_by_id.get("core")
            if core_node:
                cx = origin.x + core_node["pos"].x * self.zoom
                cy = origin.y + core_node["pos"].y * self.zoom
                r = int(ring["radius"] * self.zoom)
                if r > 0:
                    a = int(255 * ring["alpha"])
                    color = (140, 180, 255)
                    pygame.draw.circle(surface, color, (int(cx), int(cy)), r, max(1, int(ring["width"] * self.zoom)))
                    # Inner glow ring
                    if r > 4:
                        ga = a // 3
                        pygame.draw.circle(surface, (200, 220, 255), (int(cx), int(cy)), r - 2, max(1, int(ring["width"] * self.zoom * 0.5)))
        
        # ─── Phase 3: Core ignition burst particles ───
        for p in self.core_ignition_particles:
            if p["life"] <= 0:
                continue
            px = origin.x + p["x"] * self.zoom
            py = origin.y + p["y"] * self.zoom
            if not self.tree_rect.collidepoint((int(px), int(py))):
                continue
            a = int(255 * p["alpha"])
            if a <= 5:
                continue
            color = p["color"]
            sz = max(1, int(p["size"] * p["alpha"] * self.zoom))
            # Glow
            glow_r = sz * 3
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (color[0], color[1], color[2], a // 3), (glow_r, glow_r), glow_r)
            surface.blit(glow_surf, (int(px) - glow_r, int(py) - glow_r))
            # Core
            bright = tuple(min(255, c + 60) for c in color)
            pygame.draw.circle(surface, bright, (int(px), int(py)), sz)
        
        # ─── Phase 4: Branch growth — link travel visuals ───
        for travel in self.entrance_link_travels:
            from_node = self.nodes_by_id.get(travel["from_id"])
            to_node = self.nodes_by_id.get(travel["to_id"])
            if from_node is None or to_node is None:
                continue
            
            from_pos = self._node_screen_pos(from_node)
            to_pos = self._node_screen_pos(to_node)
            
            progress = travel["progress"]
            # Position along the link
            cx = from_pos.x + (to_pos.x - from_pos.x) * progress
            cy = from_pos.y + (to_pos.y - from_pos.y) * progress
            
            alpha = travel["alpha"]
            if alpha <= 0.01:
                continue
            
            # Determine color from branch
            branch = from_node.get("branch") or to_node.get("branch") or "arcane"
            theme = self.BRANCH_THEMES.get(branch, self.BRANCH_THEMES["arcane"])
            color = theme["glow"]
            
            # Draw glowing traveling orb
            orb_size = max(3, int(8 * self.zoom))
            
            # Trail line (already revealed portion) — apply alpha to color so it fades out
            if alpha > 0.05:
                trail_end_x = from_pos.x + (to_pos.x - from_pos.x) * max(0, progress - 0.15)
                trail_end_y = from_pos.y + (to_pos.y - from_pos.y) * max(0, progress - 0.15)
                trail_color = tuple(max(0, min(255, int(c * alpha))) for c in color)
                pygame.draw.line(surface, trail_color,
                               (int(trail_end_x), int(trail_end_y)), (int(cx), int(cy)),
                               max(2, int(3 * self.zoom)))
            
            # Bright orb at the front
            glow_r = orb_size * 3
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            glow_a = int(100 * alpha)
            pygame.draw.circle(glow_surf, (color[0], color[1], color[2], glow_a), (glow_r, glow_r), glow_r)
            surface.blit(glow_surf, (int(cx) - glow_r, int(cy) - glow_r))
            
            if alpha > 0.1:
                pygame.draw.circle(surface, (255, 255, 255), (int(cx), int(cy)), max(2, orb_size // 2))
            
            # Sparkle particles around the orb — apply alpha to color so they fade out
            if alpha > 0.1:
                for _ in range(3):
                    sx = cx + random.uniform(-orb_size, orb_size)
                    sy = cy + random.uniform(-orb_size, orb_size)
                    spark_brightness = alpha * random.uniform(0.3, 1.0)
                    spark_color = tuple(max(0, min(255, int(c * spark_brightness))) for c in color)
                    spark_sz = max(1, int(2 * self.zoom))
                    pygame.draw.circle(surface, spark_color, (int(sx), int(sy)), spark_sz)

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

        # Branch theme assignments for each sector (6 branches around the circle)
        branch_names = ["fire", "ice", "lightning", "nature", "shadow", "arcane"]
        
        # Node name/effect data for themed notable nodes
        notable_data = {
            "fire": [
                (_("Fireball Mastery"), _("Unlocks the Fireball skill — launch an explosive fireball dealing 28 damage with area effect and knockback.")),
                (_("Flame Shield"), _("Surrounds you with flames, dealing 8 damage/sec to nearby enemies.")),
                (_("Pyromancer's Fury"), _("Fire skills deal 25% more damage and have 15% larger area.")),
            ],
            "ice": [
                (_("Frost Nova"), _("Unlocks Frost Nova — freeze all enemies within radius for 3 seconds.")),
                (_("Ice Armor"), _("Grants a shield of ice absorbing 30 damage and slowing attackers.")),
                (_("Glacial Cascade"), _("Ice shards cascade outward dealing 35 damage and freezing enemies.")),
            ],
            "lightning": [
                (_("Chain Lightning"), _("Unlocks Chain Lightning — bolt jumps between up to 5 enemies.")),
                (_("Static Field"), _("Passive: 12% chance to shock attackers, dealing 20 damage.")),
                (_("Thunderstrike"), _("Call down lightning for 55 damage in a column from above.")),
            ],
            "nature": [
                (_("Entangling Roots"), _("Unlocks root trap that immobilizes enemies for 4 seconds.")),
                (_("Regeneration"), _("Passive: regenerate 3 HP per second at all times.")),
                (_("Summon Spirit"), _("Summon a nature spirit that attacks for 15 damage.")),
            ],
            "shadow": [
                (_("Shadow Step"), _("Unlocks teleport through shadows, becoming invulnerable briefly.")),
                (_("Poison Blade"), _("Attacks apply poison dealing 6 damage/sec for 5 seconds.")),
                (_("Dark Pact"), _("Sacrifice 10% HP to deal 60 shadow damage to all nearby enemies.")),
            ],
            "arcane": [
                (_("Arcane Missiles"), _("Unlocks homing arcane missiles dealing 22 damage each.")),
                (_("Mana Flow"), _("Passive: skill cooldowns reduced by 20%.")),
                (_("Mystic Barrier"), _("Creates a barrier that reflects 30% of incoming damage.")),
            ],
        }

        keystone_data = [
            (_("Berserker's Rage"), _("Massive damage boost (+50%) but take 20% more damage. The fury consumes you.")),
            (_("Eternal Fortress"), _("+80% defense and +40 max HP, but movement speed reduced by 15%.")),
            (_("Soul Harvest"), _("Each kill restores 5 HP and grants +2% damage for 8 seconds (stacks).")),
            (_("Void Walker"), _("Teleport on dodge. +30% dodge chance. Leave afterimage dealing 18 damage.")),
            (_("Elemental Mastery"), _("All elemental damage +35%. Unlock dual-element combo attacks.")),
            (_("Chrono Shift"), _("Slow time for 3 seconds. +25% attack speed. Cooldown: 30 seconds.")),
        ]

        def add_node(node_id, name, effect, pos, size, kind, color, accent, branch=None):
            nodes.append({
                "id": node_id,
                "name": name,
                "effect": effect,
                "pos": pygame.Vector2(pos),
                "size": size,
                "kind": kind,
                "color": color,
                "accent": accent,
                "branch": branch,
            })

        def add_link(a, b):
            if a == b:
                return
            key = (a, b) if a < b else (b, a)
            if key in link_set:
                return
            link_set.add(key)
            links.append((a, b))

        def get_branch_color(branch, role):
            """Get color from branch theme. role: 'primary', 'secondary', 'accent', 'glow'"""
            theme = self.BRANCH_THEMES.get(branch, self.BRANCH_THEMES["arcane"])
            return theme.get(role, (100, 100, 120))

        # ─── CORE NODE ───
        add_node(
            "core",
            _("Core"),
            _("The heart of your power. Unlocks paths to all branches of mastery."),
            (0, 0),
            26,
            "core",
            (100, 140, 200),
            (220, 235, 255),
        )

        # ─── RING 1: Inner circle — 12 minor nodes ───
        ring1_count = 12
        ring1_radius = 130
        for i in range(ring1_count):
            angle = math.radians(i * (360 / ring1_count) - 90)
            pos = (math.cos(angle) * ring1_radius, math.sin(angle) * ring1_radius)
            branch = branch_names[i % len(branch_names)]
            bc = get_branch_color(branch, "primary")
            ba = get_branch_color(branch, "accent")
            node_id = f"inner_{i + 1}"
            stat_names = [
                _("Vitality I"), _("Strength I"), _("Agility I"), _("Wisdom I"),
                _("Endurance I"), _("Focus I"), _("Reflexes I"), _("Fortitude I"),
                _("Precision I"), _("Resilience I"), _("Power I"), _("Speed I"),
            ]
            stat_effects = [
                _("+5 Max HP"), _("+3 Melee Damage"), _("+2% Dodge Chance"), _("+4 Max Mana"),
                _("+2 Armor"), _("+3% Crit Chance"), _("+2% Attack Speed"), _("+3 Block Chance"),
                _("+2 Accuracy"), _("+2% Damage Reduction"), _("+3 Spell Damage"), _("+2% Move Speed"),
            ]
            add_node(
                node_id,
                stat_names[i],
                stat_effects[i],
                pos,
                9,
                "minor",
                tuple(max(20, c - 20) for c in bc),
                ba,
                branch,
            )
            add_link("core", node_id)

        # Connect ring 1 nodes to neighbors
        for i in range(ring1_count):
            add_link(f"inner_{i + 1}", f"inner_{(i + 1) % ring1_count + 1}")

        # ─── BRIDGE NODES: Between ring 1 and ring 2 — 6 nodes ───
        bridge_radius = 210
        for i in range(6):
            angle = math.radians(i * 60 - 60)
            pos = (math.cos(angle) * bridge_radius, math.sin(angle) * bridge_radius)
            branch = branch_names[i]
            bc = get_branch_color(branch, "primary")
            ba = get_branch_color(branch, "accent")
            node_id = f"bridge_{i + 1}"
            add_node(
                node_id,
                _("Path Node"),
                _("Opens the way to greater power in this branch."),
                pos,
                8,
                "minor",
                tuple(max(20, c - 10) for c in bc),
                ba,
                branch,
            )
            # Link to two nearest inner nodes
            idx1 = (i * 2) % ring1_count + 1
            idx2 = (i * 2 + 1) % ring1_count + 1
            add_link(node_id, f"inner_{idx1}")
            add_link(node_id, f"inner_{idx2}")

        # ─── RING 2: Notable nodes — 6 major nodes with 4 cluster nodes each ───
        ring2_count = 6
        ring2_radius = 310
        for i in range(ring2_count):
            angle = math.radians(i * (360 / ring2_count) - 60)
            pos = (math.cos(angle) * ring2_radius, math.sin(angle) * ring2_radius)
            branch = branch_names[i]
            bc = get_branch_color(branch, "primary")
            bs = get_branch_color(branch, "secondary")
            ba = get_branch_color(branch, "accent")
            node_id = f"major_{i + 1}"

            # Use the first notable entry for the main node
            ndata = notable_data[branch][0]
            add_node(
                node_id,
                ndata[0],
                ndata[1],
                pos,
                18,
                "major",
                bc,
                ba,
                branch,
            )
            add_link(node_id, f"bridge_{i + 1}")

            # 4 cluster nodes around each major node
            cluster_radius = 55
            for j in range(4):
                offset = math.radians(j * 90 + 45)
                cluster_pos = (
                    pos[0] + math.cos(offset) * cluster_radius,
                    pos[1] + math.sin(offset) * cluster_radius,
                )
                cluster_id = f"cluster_{i + 1}_{j + 1}"
                # Use remaining notable data for cluster nodes 1 and 2
                if j < 2:
                    cdata = notable_data[branch][j + 1]
                    cname, ceffect = cdata[0], cdata[1]
                    ckind = "major"
                    csize = 13
                    ccolor = bs
                else:
                    cname = _("Minor Node")
                    ceffect = _("Small stat bonus in the {branch} branch.").format(branch=branch.capitalize())
                    ckind = "minor"
                    csize = 8
                    ccolor = tuple(max(20, c - 15) for c in bc)
                add_node(
                    cluster_id,
                    cname,
                    ceffect,
                    cluster_pos,
                    csize,
                    ckind,
                    ccolor,
                    ba,
                    branch,
                )
                add_link(node_id, cluster_id)

            # Link adjacent cluster nodes for visual density
            for j in range(4):
                add_link(f"cluster_{i + 1}_{j + 1}", f"cluster_{i + 1}_{(j + 1) % 4 + 1}")

        # ─── CONNECTOR NODES: Between ring 2 majors — 6 nodes ───
        for i in range(ring2_count):
            angle_a = math.radians(i * (360 / ring2_count) - 60)
            angle_b = math.radians(((i + 1) % ring2_count) * (360 / ring2_count) - 60)
            mid_angle = (angle_a + angle_b) / 2
            conn_radius = 330
            pos = (math.cos(mid_angle) * conn_radius, math.sin(mid_angle) * conn_radius)
            node_id = f"conn_{i + 1}"
            # Blend colors of adjacent branches
            b1 = branch_names[i]
            b2 = branch_names[(i + 1) % len(branch_names)]
            c1 = get_branch_color(b1, "secondary")
            c2 = get_branch_color(b2, "secondary")
            blended = tuple((a + b) // 2 for a, b in zip(c1, c2))
            add_node(
                node_id,
                _("Crossroads"),
                _("A junction between two paths of power."),
                pos,
                10,
                "minor",
                blended,
                (200, 200, 220),
                b1,
            )
            add_link(node_id, f"major_{i + 1}")
            add_link(node_id, f"major_{(i + 1) % ring2_count + 1}")

        # ─── RING 3: Keystone nodes — 6 with 3 cluster nodes each ───
        ring3_count = 6
        ring3_radius = 460
        for i in range(ring3_count):
            angle = math.radians(i * (360 / ring3_count) - 30)
            pos = (math.cos(angle) * ring3_radius, math.sin(angle) * ring3_radius)
            branch = branch_names[i]
            bc = get_branch_color(branch, "primary")
            ba = get_branch_color(branch, "accent")
            glow = get_branch_color(branch, "glow")
            node_id = f"keystone_{i + 1}"
            kd = keystone_data[i]
            add_node(
                node_id,
                kd[0],
                kd[1],
                pos,
                24,
                "keystone",
                glow,
                ba,
                branch,
            )
            add_link(node_id, f"major_{i + 1}")

            # 3 satellite nodes around each keystone
            sat_radius = 60
            for j in range(3):
                offset = math.radians(j * 120 + 30)
                sat_pos = (
                    pos[0] + math.cos(offset) * sat_radius,
                    pos[1] + math.sin(offset) * sat_radius,
                )
                sat_id = f"keystone_sat_{i + 1}_{j + 1}"
                add_node(
                    sat_id,
                    _("Keystone Shard"),
                    _("A fragment of keystone power: +2% to all stats in this branch."),
                    sat_pos,
                    8,
                    "minor",
                    tuple(max(20, c - 30) for c in bc),
                    ba,
                    branch,
                )
                add_link(node_id, sat_id)

            # Link adjacent keystone satellites
            for j in range(3):
                add_link(f"keystone_sat_{i + 1}_{j + 1}", f"keystone_sat_{i + 1}_{(j + 1) % 3 + 1}")

        # ─── RING 4: Outer ring — 18 minor nodes ───
        ring4_count = 18
        ring4_radius = 580
        for i in range(ring4_count):
            angle = math.radians(i * (360 / ring4_count) - 90)
            pos = (math.cos(angle) * ring4_radius, math.sin(angle) * ring4_radius)
            branch = branch_names[i % len(branch_names)]
            bc = get_branch_color(branch, "primary")
            ba = get_branch_color(branch, "accent")
            node_id = f"outer_{i + 1}"
            outer_names = [
                _("Iron Will"), _("Swift Feet"), _("Sharp Mind"), _("Tough Skin"),
                _("Quick Hands"), _("Eagle Eye"), _("Stone Heart"), _("Flame Touch"),
                _("Frost Bite"), _("Thunder Palm"), _("Vine Grip"), _("Shadow Veil"),
                _("Arcane Touch"), _("Steel Spine"), _("Wind Step"), _("Ember Soul"),
                _("Ice Blood"), _("Storm Core"),
            ]
            outer_effects = [
                _("+5% knockback resistance"), _("+3% movement speed"), _("+4% mana regen"),
                _("+4 armor"), _("+3% attack speed"), _("+5% accuracy"),
                _("+8 max HP"), _("+3 fire damage on hit"), _("+2% freeze chance"),
                _("+3% shock chance"), _("+2% root chance on hit"), _("+3% dodge chance"),
                _("+4 spell power"), _("+3% damage reduction"), _("+2% evasion"),
                _("+5 fire resistance"), _("+5 cold resistance"), _("+5 lightning resistance"),
            ]
            add_node(
                node_id,
                outer_names[i],
                outer_effects[i],
                pos,
                8,
                "minor",
                tuple(max(20, c - 25) for c in bc),
                ba,
                branch,
            )
            # Link to nearest keystone or keystone satellite
            ks_idx = (i % ring3_count) + 1
            sat_idx = (i % 3) + 1
            add_link(node_id, f"keystone_sat_{ks_idx}_{sat_idx}")

        # Connect outer ring neighbors
        for i in range(ring4_count):
            add_link(f"outer_{i + 1}", f"outer_{(i + 1) % ring4_count + 1}")

        # ─── EXTRA: Inter-ring connections for visual density ───
        # Connect some bridge nodes to adjacent major clusters
        for i in range(6):
            next_bridge = (i + 1) % 6 + 1
            add_link(f"bridge_{i + 1}", f"cluster_{next_bridge}_1")

        return nodes, links

    def _build_background_points(self):
        """Build twinkling star background with more stars and varied sizes."""
        rng = random.Random(23)
        points = []
        for _ in range(400):
            points.append(
                (
                    rng.uniform(-750, 750),
                    rng.uniform(-650, 650),
                    rng.randint(1, 3),
                    rng.uniform(0.3, 1.0),  # twinkle phase offset
                    rng.uniform(0.5, 2.0),  # twinkle speed
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

    def _get_adjacent_nodes(self, node_id):
        """Get all node IDs that are directly connected to the given node."""
        adjacent = set()
        for a, b in self.links:
            if a == node_id:
                adjacent.add(b)
            elif b == node_id:
                adjacent.add(a)
        return adjacent

    def _can_unlock_node(self, node_id, unlocked):
        """Check if a node can be unlocked (must be adjacent to an unlocked node)."""
        if node_id in unlocked:
            return False
        # Core node is always unlocked by default
        if node_id == "core":
            return False
        # Check if any adjacent node is unlocked
        adjacent = self._get_adjacent_nodes(node_id)
        return bool(adjacent & unlocked)

    def _unlock_selected(self):
        selected = self.nodes_by_id.get(self.selected_node_id)
        if selected is None:
            return

        character = self._character()
        if character is None:
            return

        unlocked = self._get_unlocked_nodes()
        node_id = selected["id"]
        if node_id in unlocked:
            return

        # Check sequential unlock requirement - must be connected to an unlocked node
        if not self._can_unlock_node(node_id, unlocked):
            from src.ui.widgets import Dialog
            self.app.current_dialog = Dialog(self.app, [_('You must unlock an adjacent node first.')])
            return

        kind = selected.get("kind")
        cost_map = {"minor": 1, "major": 2, "keystone": 3, "core": 0}
        cost = cost_map.get(kind, 1)

        points = getattr(character, "skill_tree_points", 0)
        if points < cost:
            # show dialog: not enough points
            from src.ui.widgets import Dialog
            self.app.current_dialog = Dialog(self.app, [_('Not enough points to unlock this node.')])
            return

        # Deduct points and mark unlocked
        try:
            character.skill_tree_points = points - cost
        except Exception:
            try:
                setattr(character, "skill_tree_points", points - cost)
            except Exception:
                pass

        # ensure unlocked is mutable set on character
        cur = getattr(character, "skill_tree_unlocked", None)
        if cur is None:
            character.skill_tree_unlocked = {"core"}
            cur = character.skill_tree_unlocked
        if isinstance(cur, list):
            cur = set(cur)
        cur.add(node_id)
        character.skill_tree_unlocked = cur
        logger.info(f"Unlocked node {node_id}; cost {cost} points. Remaining: {getattr(character, 'skill_tree_points', 0)}")

        # If the Fireball Mastery node was unlocked, teach the fireball skill
        if node_id == "major_1" and hasattr(character, "learn_fireball"):
            character.learn_fireball()
        
        # Trigger unlock animation
        self._spawn_unlock_effect(node_id)

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

        # position unlock button above exit button
        try:
            unlock_y = self.exit_button.rect.y - exit_height - int(8 * scale)
            self.unlock_button.rect = pygame.Rect(
                self.sidebar_rect.centerx - exit_width // 2,
                unlock_y,
                exit_width,
                exit_height,
            )
            self.unlock_button._update_text_surface()
        except Exception:
            pass

        size = (sw, sh)
        if self._layout_size != size:
            self._layout_size = size
            self.pan_offset = pygame.Vector2(0, 0)

    def handle_event(self, event: pygame.event.Event):
        # Route events to dialog first if one is active
        if getattr(self.app, 'current_dialog', None):
            try:
                self.app.current_dialog.handle_event(event)
                return
            except Exception:
                pass

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

    def _spawn_unlock_effect(self, node_id):
        """Spawn a dramatic unlock animation at the given node position."""
        node = self.nodes_by_id.get(node_id)
        if node is None:
            return
        
        branch = node.get("branch", "arcane")
        theme = self.BRANCH_THEMES.get(branch, self.BRANCH_THEMES["arcane"])
        glow_color = theme["glow"]
        primary_color = theme["primary"]
        secondary_color = theme["secondary"]
        accent_color = theme["accent"]
        
        # Get screen position of the node
        screen_pos = self._node_screen_pos(node)
        node_size = max(4, int(node["size"] * self.zoom))
        
        # ─── 1. Particle burst (50+ particles flying outward) ───
        burst_particles = []
        for _ in range(80):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(60, 250) * self.zoom
            lifetime = random.uniform(0.4, 1.2)
            # Choose a color from the branch palette
            color_choice = random.choice([glow_color, primary_color, secondary_color, accent_color, (255, 255, 255)])
            burst_particles.append({
                "type": "burst",
                "x": screen_pos.x,
                "y": screen_pos.y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "size": random.uniform(2, 6) * self.zoom,
                "life": lifetime,
                "max_life": lifetime,
                "color": color_choice,
                "alpha": 1.0,
            })
        
        # ─── 2. Shockwave ring data ───
        shockwave = {
            "type": "shockwave",
            "x": screen_pos.x,
            "y": screen_pos.y,
            "radius": node_size,
            "max_radius": node_size + 150 * self.zoom,
            "speed": 300 * self.zoom,
            "life": 0.6,
            "max_life": 0.6,
            "color": glow_color,
            "alpha": 0.9,
            "width": 3,
        }
        
        # ─── 3. Cascading light on connected links ───
        link_lights = []
        adjacent = self._get_adjacent_nodes(node_id)
        unlocked = self._get_unlocked_nodes()
        for adj_id in adjacent:
            if adj_id in unlocked:
                adj_node = self.nodes_by_id.get(adj_id)
                if adj_node:
                    adj_pos = self._node_screen_pos(adj_node)
                    # Traveling light from unlocked adjacent to new node
                    link_lights.append({
                        "type": "link_light",
                        "x1": adj_pos.x,
                        "y1": adj_pos.y,
                        "x2": screen_pos.x,
                        "y2": screen_pos.y,
                        "progress": 0.0,
                        "speed": random.uniform(0.8, 1.5),
                        "color": secondary_color,
                        "size": max(3, int(6 * self.zoom)),
                        "alpha": 1.0,
                    })
        
        # ─── 4. Floating text effect ───
        float_text = {
            "type": "float_text",
            "x": screen_pos.x,
            "y": screen_pos.y - node_size - 20,
            "text": "✦ UNLOCKED ✦",
            "color": accent_color,
            "life": 1.5,
            "max_life": 1.5,
            "speed_y": -40 * self.zoom,
            "size": max(16, int(22 * self.zoom)),
        }
        
        # Add all effects to the queue
        self.unlock_effects.extend(burst_particles)
        self.unlock_effects.append(shockwave)
        self.unlock_effects.extend(link_lights)
        self.unlock_effects.append(float_text)
        
        # ─── 5. Trigger screen flash ───
        self.screen_flash_alpha = 0.35
        self.screen_flash_timer = 0.4
    
    def _update_particles(self, dt):
        """Update floating particle positions for ambient effect."""
        for p in self.particles:
            p["x"] += p["speed_x"] * dt * 60
            p["y"] += p["speed_y"] * dt * 60
            # Wrap particles that drift too far
            if p["y"] < -650:
                p["y"] = 650
                p["x"] = random.uniform(-700, 700)
            if p["x"] < -750:
                p["x"] = 750
            elif p["x"] > 750:
                p["x"] = -750
        
        # Update unlock effects
        self._update_unlock_effects(dt)
        
        # Update entrance animation
        self._update_entrance(dt)
    
    def _update_unlock_effects(self, dt):
        """Update all active unlock animation effects."""
        to_remove = []
        
        # Update screen flash
        if self.screen_flash_timer > 0:
            self.screen_flash_timer -= dt
            self.screen_flash_alpha *= 0.92  # exponential fade
            if self.screen_flash_timer <= 0:
                self.screen_flash_alpha = 0
                self.screen_flash_timer = 0
        
        for effect in self.unlock_effects:
            effect_type = effect.get("type")
            
            if effect_type == "burst":
                # Move particle
                effect["x"] += effect["vx"] * dt
                effect["y"] += effect["vy"] * dt
                # Apply drag
                effect["vx"] *= 0.97
                effect["vy"] *= 0.97
                # Add gravity for sparkle effect
                effect["vy"] += 20 * dt * self.zoom
                # Decrease life
                effect["life"] -= dt
                effect["alpha"] = effect["life"] / effect["max_life"]
                if effect["life"] <= 0:
                    to_remove.append(effect)
            
            elif effect_type == "shockwave":
                # Expand ring
                effect["radius"] += effect["speed"] * dt
                effect["life"] -= dt
                progress = 1.0 - (effect["life"] / effect["max_life"])
                effect["alpha"] = 0.9 * (1.0 - progress)
                effect["width"] = max(1, int(3 * (1.0 - progress * 0.7)))
                if effect["life"] <= 0:
                    to_remove.append(effect)
            
            elif effect_type == "link_light":
                # Traveling light along the link
                effect["progress"] += dt * effect["speed"]
                effect["alpha"] = 1.0 - effect["progress"]
                if effect["progress"] >= 1.0:
                    to_remove.append(effect)
            
            elif effect_type == "float_text":
                # Float upward
                effect["y"] += effect["speed_y"] * dt
                effect["life"] -= dt
                progress = 1.0 - (effect["life"] / effect["max_life"])
                effect["alpha"] = 1.0 - progress  # fade out
                # Scale up slightly
                effect["size"] += 2 * dt
                if effect["life"] <= 0:
                    to_remove.append(effect)
        
        # Remove expired effects
        for effect in to_remove:
            if effect in self.unlock_effects:
                self.unlock_effects.remove(effect)
    
    def _draw_unlock_effects(self, surface):
        """Draw all active unlock animation effects."""
        for effect in self.unlock_effects:
            effect_type = effect.get("type")
            
            if effect_type == "burst":
                alpha = int(255 * effect["alpha"])
                if alpha <= 0:
                    continue
                color = effect["color"]
                r, g, b = color[:3]
                # Fade to white as it fades
                fade = alpha / 255
                dr = int(r * fade + 255 * (1 - fade))
                dg = int(g * fade + 255 * (1 - fade))
                db = int(b * fade + 255 * (1 - fade))
                clr = (dr, dg, db, alpha)
                size = max(1, effect["size"] * effect["alpha"])
                pos = (int(effect["x"]), int(effect["y"]))
                if self.tree_rect.collidepoint(pos):
                    pygame.draw.circle(surface, clr[:3], pos, int(size))
            
            elif effect_type == "shockwave":
                alpha = int(255 * effect["alpha"])
                if alpha <= 0:
                    continue
                color = effect["color"]
                r, g, b = color[:3]
                clr = (r, g, b)
                pos = (int(effect["x"]), int(effect["y"]))
                radius = int(effect["radius"])
                # Draw multiple rings for a glow effect
                for w in range(effect["width"], 0, -1):
                    ring_alpha = alpha // (effect["width"] - w + 1) if w > 0 else alpha
                    offset = w * 3
                    adj_alpha = max(0, ring_alpha - offset * 10)
                    if adj_alpha > 0:
                        t_clr = tuple(max(0, min(255, (c + adj_alpha) if i == 0 else c)) for i, c in enumerate(color))
                        pygame.draw.circle(surface, color, pos, radius + offset, max(1, w))
            
            elif effect_type == "link_light":
                alpha = int(255 * effect["alpha"])
                if alpha <= 0:
                    continue
                progress = effect["progress"]
                x = effect["x1"] + (effect["x2"] - effect["x1"]) * progress
                y = effect["y1"] + (effect["y2"] - effect["y1"]) * progress
                color = effect["color"]
                size = int(effect["size"] * (0.5 + 0.5 * math.sin(progress * math.pi)))
                # Draw glow ball
                glow_size = size * 3
                for i in range(3):
                    glow_alpha = alpha // (2 ** i + 1)
                    glow_r = max(1, glow_size - i * 4)
                    gc = tuple(max(0, min(255, c)) for c in color)
                    pygame.draw.circle(surface, gc, (int(x), int(y)), glow_r)
                pygame.draw.circle(surface, (255, 255, 255), (int(x), int(y)), size)
            
            elif effect_type == "float_text":
                alpha = int(255 * effect["alpha"])
                if alpha <= 0:
                    continue
                font = cfg.get_font(max(12, int(effect["size"])))
                text_surf = font.render(effect["text"], True, effect["color"])
                text_surf.set_alpha(alpha)
                pos = (int(effect["x"] - text_surf.get_width() // 2), int(effect["y"]))
                # Draw shadow for readability
                shadow = font.render(effect["text"], True, (0, 0, 0))
                shadow.set_alpha(alpha // 2)
                surface.blit(shadow, (pos[0] + 2, pos[1] + 2))
                surface.blit(text_surf, pos)
        
        # Draw screen flash (light overlay)
        if self.screen_flash_alpha > 0.01:
            flash = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            alpha_val = int(255 * self.screen_flash_alpha)
            flash.fill((255, 255, 255, alpha_val))
            surface.blit(flash, (0, 0))

    def _draw_tree_background(self, surface):
        """Draw enhanced background with concentric rings, twinkling stars, and particles."""
        origin = pygame.Vector2(self.tree_rect.center) + self.pan_offset
        t = self.animation_time
        
        # During entrance, star visibility is controlled by entrance_star_alpha
        star_alpha_mult = self.entrance_star_alpha if self.entrance_active else 1.0

        # Draw subtle radial gradient background using concentric circles
        for r in range(700, 0, -8):
            brightness = max(12, 22 - r // 50)
            # During entrance, dim the background until stars fade in
            if self.entrance_active and self.entrance_phase < 2:
                brightness = int(brightness * star_alpha_mult)
            pygame.draw.circle(surface, (brightness, brightness, brightness + 4), origin, int(r * self.zoom), 0)

        # Draw concentric guide rings with subtle pulse
        ring_radii = [130, 210, 310, 330, 460, 580]
        for idx, radius in enumerate(ring_radii):
            pulse = math.sin(t * 0.5 + idx * 0.8) * 0.15 + 0.85
            c = int(28 * pulse)
            if self.entrance_active and self.entrance_phase < 2:
                c = int(c * star_alpha_mult)
            pygame.draw.circle(surface, (c, c, c + 8), origin, int(radius * self.zoom), 1)

        # Draw twinkling stars (fade in during entrance phase 1+)
        for star_data in self.background_points:
            x, y, size, phase, speed = star_data
            pos = origin + pygame.Vector2(x, y) * self.zoom
            if self.tree_rect.collidepoint(pos):
                twinkle = (math.sin(t * speed + phase) + 1.0) * 0.5
                brightness = int((25 + 35 * twinkle) * star_alpha_mult)
                star_color = (brightness, brightness, brightness + 12)
                pygame.draw.circle(surface, star_color, (int(pos.x), int(pos.y)), size)

        # Draw floating particles (fade in during entrance)
        for p in self.particles:
            pos = origin + pygame.Vector2(p["x"], p["y"]) * self.zoom
            if self.tree_rect.collidepoint(pos):
                pulse = (math.sin(t * p["pulse_speed"]) + 1.0) * 0.5
                alpha = p["alpha"] * (0.4 + 0.6 * pulse) * star_alpha_mult
                r, g, b = p["color"]
                pcolor = (int(r * alpha), int(g * alpha), int(b * alpha))
                sz = max(1, int(p["size"] * self.zoom * (0.8 + 0.4 * pulse)))
                pygame.draw.circle(surface, pcolor, (int(pos.x), int(pos.y)), sz)

    def _draw_links(self, surface, unlocked, revealed_filter=None):
        """Draw links with glow effect for active (unlocked) connections.
        
        Args:
            revealed_filter: If provided, only draw links where both nodes are in this set.
        """
        t = self.animation_time
        for a, b in self.links:
            node_a = self.nodes_by_id.get(a)
            node_b = self.nodes_by_id.get(b)
            if node_a is None or node_b is None:
                continue
            # During entrance animation, only draw links where both nodes have been revealed
            if revealed_filter is not None:
                if a not in revealed_filter or b not in revealed_filter:
                    continue
            pos_a = self._node_screen_pos(node_a)
            pos_b = self._node_screen_pos(node_b)
            active = a in unlocked and b in unlocked

            if active:
                # Determine branch color for the link
                branch = node_a.get("branch") or node_b.get("branch")
                if branch and branch in self.BRANCH_THEMES:
                    theme = self.BRANCH_THEMES[branch]
                    glow_color = theme["glow"]
                    base_color = theme["secondary"]
                else:
                    glow_color = (140, 180, 220)
                    base_color = (120, 160, 200)

                # Animated pulse for active links
                pulse = (math.sin(t * 2.0) + 1.0) * 0.5
                glow_alpha = 0.3 + 0.2 * pulse

                # Draw glow (wider, semi-transparent line underneath)
                glow_r = int(glow_color[0] * glow_alpha)
                glow_g = int(glow_color[1] * glow_alpha)
                glow_b = int(glow_color[2] * glow_alpha)
                pygame.draw.line(surface, (glow_r, glow_g, glow_b), pos_a, pos_b, max(3, int(5 * self.zoom)))

                # Draw main line
                pygame.draw.line(surface, base_color, pos_a, pos_b, max(1, int(2 * self.zoom)))
            else:
                # Inactive links — dim
                pygame.draw.line(surface, (48, 48, 58), pos_a, pos_b, max(1, int(1.5 * self.zoom)))

    def _draw_nodes(self, surface, unlocked, revealed_filter=None):
        """Draw nodes with glow halos, pulsing effects, and inner highlights.
        
        Args:
            revealed_filter: If provided, only draw nodes that are in this set.
        """
        t = self.animation_time
        for node in self.nodes:
            node_id = node["id"]
            # During entrance animation, only draw nodes that have been revealed
            if revealed_filter is not None and node_id not in revealed_filter:
                continue
            pos = self._node_screen_pos(node)
            radius = max(4, int(node["size"] * self.zoom))
            is_unlocked = node_id in unlocked
            is_selected = node_id == self.selected_node_id
            is_hovered = node_id == self.hovered_node_id
            kind = node["kind"]
            branch = node.get("branch")

            # Determine colors
            if is_unlocked:
                fill = node["color"]
                accent = node["accent"]
            else:
                fill = (38, 38, 46)
                accent = (70, 75, 90)

            # ── Glow halo for unlocked nodes ──
            if is_unlocked and branch and branch in self.BRANCH_THEMES:
                glow_color = self.BRANCH_THEMES[branch]["glow"]
                pulse = (math.sin(t * 1.5 + hash(node_id) * 0.1) + 1.0) * 0.5
                glow_radius = radius + int((6 + 4 * pulse) * self.zoom)
                glow_alpha = 0.15 + 0.1 * pulse

                # Draw multiple glow rings for soft effect
                for ring in range(3):
                    r_off = ring * int(3 * self.zoom)
                    alpha_factor = glow_alpha * (1.0 - ring * 0.3)
                    gc = tuple(max(0, min(255, int(c * alpha_factor))) for c in glow_color)
                    pygame.draw.circle(surface, gc, (int(pos.x), int(pos.y)), glow_radius + r_off, 1)

            # ── Core node special effect: rotating ring ──
            if kind == "core" and is_unlocked:
                core_pulse = (math.sin(t * 1.2) + 1.0) * 0.5
                core_glow_r = radius + int((10 + 6 * core_pulse) * self.zoom)
                for ring in range(4):
                    r_off = ring * int(3 * self.zoom)
                    alpha = 0.2 * (1.0 - ring * 0.2) * (0.7 + 0.3 * core_pulse)
                    gc = (int(100 * alpha), int(160 * alpha), int(255 * alpha))
                    pygame.draw.circle(surface, gc, (int(pos.x), int(pos.y)), core_glow_r + r_off, 1)

                # Draw rotating decorative arcs around core
                for i in range(6):
                    arc_angle = t * 0.8 + i * math.pi / 3
                    arc_x = pos.x + math.cos(arc_angle) * (radius + 8) * self.zoom
                    arc_y = pos.y + math.sin(arc_angle) * (radius + 8) * self.zoom
                    dot_r = max(2, int(2 * self.zoom))
                    pygame.draw.circle(surface, (180, 210, 255), (int(arc_x), int(arc_y)), dot_r)

            # ── Keystone special effect: diamond shape indicator ──
            if kind == "keystone" and is_unlocked:
                ks_pulse = (math.sin(t * 1.8 + hash(node_id) * 0.2) + 1.0) * 0.5
                ks_glow_r = radius + int((8 + 5 * ks_pulse) * self.zoom)
                glow_color = node.get("color", (200, 100, 100))
                for ring in range(3):
                    r_off = ring * int(3 * self.zoom)
                    alpha = 0.25 * (1.0 - ring * 0.25) * (0.6 + 0.4 * ks_pulse)
                    gc = tuple(max(0, min(255, int(c * alpha))) for c in glow_color)
                    pygame.draw.circle(surface, gc, (int(pos.x), int(pos.y)), ks_glow_r + r_off, 1)

            # ── Draw main node circle ──
            pygame.draw.circle(surface, fill, (int(pos.x), int(pos.y)), radius)

            # ── Inner highlight (lighter center for 3D effect) ──
            if is_unlocked and radius > 5:
                inner_r = max(2, radius // 2)
                highlight = tuple(min(255, c + 40) for c in fill)
                pygame.draw.circle(surface, highlight, (int(pos.x - radius * 0.15), int(pos.y - radius * 0.15)), inner_r)

            # ── Border ──
            border_width = 2 if kind in ("core", "keystone", "major") else 1
            pygame.draw.circle(surface, accent, (int(pos.x), int(pos.y)), radius, border_width)

            # ── Selection ring (animated pulse) ──
            if is_selected:
                sel_pulse = (math.sin(t * 3.0) + 1.0) * 0.5
                sel_r = radius + int((5 + 3 * sel_pulse) * self.zoom)
                sel_color = (
                    int(200 + 55 * sel_pulse),
                    int(200 + 55 * sel_pulse),
                    255,
                )
                pygame.draw.circle(surface, sel_color, (int(pos.x), int(pos.y)), sel_r, 2)
                # Second outer ring
                sel_r2 = sel_r + int(3 * self.zoom)
                sel_alpha = 0.4 + 0.3 * sel_pulse
                sel_color2 = (int(180 * sel_alpha), int(180 * sel_alpha), int(255 * sel_alpha))
                pygame.draw.circle(surface, sel_color2, (int(pos.x), int(pos.y)), sel_r2, 1)
            elif is_hovered:
                hover_r = radius + int(4 * self.zoom)
                pygame.draw.circle(surface, (180, 180, 210), (int(pos.x), int(pos.y)), hover_r, 1)

            # ── Unlockable indicator: dotted ring for nodes that can be unlocked ──
            if not is_unlocked and node_id != "core":
                adjacent_unlocked = bool(self._get_adjacent_nodes(node_id) & unlocked)
                if adjacent_unlocked:
                    can_pulse = (math.sin(t * 2.5) + 1.0) * 0.5
                    can_r = radius + int(4 * self.zoom)
                    can_color = (
                        int(80 + 60 * can_pulse),
                        int(120 + 60 * can_pulse),
                        int(80 + 60 * can_pulse),
                    )
                    pygame.draw.circle(surface, can_color, (int(pos.x), int(pos.y)), can_r, 1)

            # ── Labels for important nodes ──
            if kind in ("core", "major", "keystone"):
                label_color = (235, 235, 245) if is_unlocked else (160, 160, 175)
                label = self.small_font.render(node["name"], True, label_color)
                label_rect = label.get_rect(center=(pos.x, pos.y - radius - int(14 * self.zoom)))
                # Draw label background for readability
                bg_pad = 3
                bg_rect = label_rect.inflate(bg_pad * 2, bg_pad)
                bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
                bg_surface.fill((16, 16, 22, 160))
                surface.blit(bg_surface, bg_rect)
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

        # Update unlock button state and text
        if selected_node is None:
            self.unlock_button.set_text("")
        else:
            kind = selected_node.get("kind")
            # cost mapping: minor(normal)=1, major(notable)=2, keystone(best)=3
            cost_map = {"minor": 1, "major": 2, "keystone": 3, "core": 0}
            cost = cost_map.get(kind, 1)
            if selected_node["id"] in unlocked or cost == 0:
                self.unlock_button.set_text(_("Unlocked"))
            else:
                self.unlock_button.set_text(f"{_('Unlock')} ({cost})")

    def draw(self, screen: pygame.Surface):
        self.layout(screen)

        # Update animation time using pygame clock
        dt = 0.016  # Default ~60fps delta
        try:
            dt = self.app.clock.get_time() / 1000.0 if hasattr(self.app, 'clock') else 0.016
        except Exception:
            pass
        self.animation_time += dt
        self._update_particles(dt)

        # Dark background fill
        screen.fill((10, 10, 16))
        
        # During entrance phase 0 (void), draw almost nothing — just a dark screen
        # The tree area border fades in during phase 1
        entrance_border_alpha = 1.0
        if self.entrance_active and self.entrance_phase <= 1:
            if self.entrance_phase == 0:
                entrance_border_alpha = 0.0
            elif self.entrance_phase == 1:
                entrance_border_alpha = min(1.0, self.entrance_phase_time / 0.8)
        
        # Draw tree area background with subtle gradient border
        border_color = (18, 18, 24)
        if entrance_border_alpha < 1.0:
            border_color = tuple(int(c * entrance_border_alpha) for c in border_color)
        pygame.draw.rect(screen, border_color, self.tree_rect, border_radius=18)
        
        # Decorative double border (fades in)
        if entrance_border_alpha > 0.1:
            outer_border = tuple(int(c * entrance_border_alpha) for c in (55, 55, 72))
            pygame.draw.rect(screen, outer_border, self.tree_rect, 2, border_radius=18)
            inner_border = tuple(int(c * entrance_border_alpha) for c in (35, 35, 48))
            inner_rect = self.tree_rect.inflate(-4, -4)
            pygame.draw.rect(screen, inner_border, inner_rect, 1, border_radius=16)

        old_clip = screen.get_clip()
        screen.set_clip(self.tree_rect)
        
        # Draw background — during entrance, star alpha is controlled by the animation
        self._draw_tree_background(screen)

        # During entrance, only draw links/nodes that have been revealed
        unlocked = self._get_unlocked_nodes()
        
        # Determine if we should hide normal tree rendering during early entrance phases
        hide_tree = self.entrance_active and self.entrance_phase < 3
        
        # During entrance animation (phase 3+), use entrance_revealed_nodes to filter
        # which nodes/links are drawn, making the tree appear gradually during BFS
        use_entrance_filter = self.entrance_active and self.entrance_phase >= 3 and self.entrance_phase < 6
        
        if not hide_tree:
            # Determine the revealed filter for entrance animation
            revealed_filter = self.entrance_revealed_nodes if use_entrance_filter else None
            
            # Normal link and node drawing (after core ignition, nodes are revealed by entrance)
            self._draw_links(screen, unlocked, revealed_filter=revealed_filter)

            mouse_pos = pygame.mouse.get_pos()
            self.hovered_node_id = self._hit_test_node(mouse_pos)
            self._draw_nodes(screen, unlocked, revealed_filter=revealed_filter)
        else:
            # During early entrance, still allow hover detection but don't draw normal nodes
            mouse_pos = pygame.mouse.get_pos()
            self.hovered_node_id = None  # No hover during entrance
        
        # Draw entrance animation effects (vortex, sparks, core ignition, branch growth)
        self._draw_entrance_sparks(screen)
        
        # Draw unlock animation effects on top of everything
        self._draw_unlock_effects(screen)
        
        screen.set_clip(old_clip)

        # Draw node count info in bottom-left of tree area (fade in after entrance)
        if not self.entrance_active or self.entrance_phase >= 5:
            total_nodes = len(self.nodes)
            unlocked_count = len(unlocked)
            info_text = self.small_font.render(
                f"{unlocked_count}/{total_nodes} nodes", True, (100, 100, 120)
            )
            screen.blit(info_text, (self.tree_rect.x + 12, self.tree_rect.bottom - info_text.get_height() - 8))

        selected_node = self.nodes_by_id.get(self.selected_node_id)
        self._draw_sidebar(screen, selected_node)
        # draw sidebar buttons
        try:
            self.unlock_button.draw(screen)
        except Exception:
            pass
        self.exit_button.draw(screen)

        # Draw dialog on top if one is active
        if getattr(self.app, 'current_dialog', None):
            try:
                self.app.current_dialog.draw(screen)
            except Exception:
                pass

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
