import math
import pygame
from typing import TYPE_CHECKING
from src.entities.character import Character
from src.ui.widgets import Button
import src.config as cfg
from src.core.logger import logger

# Ensure _ is available for gettext translations
try:
    _  # type: ignore[used-before-def]
except NameError:
    from gettext import gettext as _

if TYPE_CHECKING:
    from src.app import App

class HUD:
    """
    Head-Up Display (HUD) for player status and UI controls.

    This class is responsible for rendering player health, lives, stamina, XP,
    money, skill hotbar, and the inventory button, as well as handling related UI events.

    Attributes:
        character (Character):
            The character object whose state is being displayed.
        app (App):
            The main application object for accessing managers (e.g., INV_manager).
        toggle_inventory_callback (callable | None):
            Optional callback to toggle inventory state.
        use_skill_callback (callable | None):
            Optional callback to use a skill from a slot.
        open_shop_callback (callable | None):
            Optional callback to open the shop.
        font (pygame.font.Font):
            The font used for rendering text.
        stamina_font (pygame.font.Font):
            Font used for stamina label.
        stamina_label (pygame.Surface):
            Rendered "STAMINA" label surface.
        hp_icon (pygame.Surface):
            The icon representing health (a heart).
        life_icon (pygame.Surface):
            The icon representing the number of lives (a skull).
        inv_button (Button):
            The button to open/close the inventory.
        coin_icon (pygame.Surface):
            The coin icon surface used for money display.
        skill_slot_size (int):
            Size of each skill slot in pixels.
        skill_slot_padding (int):
            Padding between skill slots.
        skill_slots_count (int):
            Number of skill hotbar slots.
        skill_panel_margin (int):
            Margin around the skill panel.
        skill_panel_width (int):
            Width of the skill panel.
        skill_total_slots_height (int):
            Total height of all skill slots combined.
        skill_panel_x (int):
            X position of the skill panel.
        skill_panel_y (int):
            Y position of the skill panel.
        animation_time (float):
            Accumulated time for animation effects.
        hp_icon_pos (tuple[int, int]):
            Screen position of the HP icon.
        life_icon_pos (tuple[int, int]):
            Screen position of the life icon.
        hp_bar_rect (pygame.Rect):
            Rectangle for the HP bar.
        xp_bar_rect (pygame.Rect):
            Rectangle for the XP bar.
        stamina_bar_rect (pygame.Rect):
            Rectangle for the stamina bar.
        money_pos (tuple[int, int]):
            Screen position for the money display.
        _layout_size (tuple[int, int] | None):
            Cached screen size for layout recalc.
        skill_slot_rects (list[pygame.Rect]):
            List of rectangles for each skill slot.
        NEON_THEMES (dict):
            Color themes for skill elements.

    Methods:
        __init__(character, app, toggle_inventory_callback=None, use_skill_callback=None, open_shop_callback=None):
            Initialize the HUD with player character, app, and callbacks.
        _recalc_layout(screen_width, screen_height):
            Recalculate HUD positions based on the current screen size.
        _ensure_layout(screen_width, screen_height):
            Ensure layout is recalculated if screen size changed.
        toggle_inventory():
            Toggle the inventory open/closed, using callback if provided.
        handle_event(event):
            Handle mouse events for the inventory button and skill slots.
        _get_skill_theme(skill):
            Get the neon color theme for a skill based on its properties.
        _draw_hud_skill_slot(surface, rect, skill, idx):
            Draw an individual skill slot with glow and cooldown effects.
        _on_shop_clicked():
            Handle shop button click, using callback or fallback.
        draw(screen):
            Draw all HUD elements (health, stamina, XP, money, skill hotbar, inventory button).
    """

    NEON_THEMES = {
        "fire": {"primary": (255, 80, 40), "glow": (255, 120, 60), "accent": (255, 200, 100)},
        "ice": {"primary": (60, 140, 255), "glow": (100, 180, 255), "accent": (180, 220, 255)},
        "lightning": {"primary": (255, 220, 50), "glow": (255, 240, 100), "accent": (255, 255, 180)},
        "nature": {"primary": (80, 200, 100), "glow": (120, 240, 140), "accent": (180, 255, 180)},
        "shadow": {"primary": (160, 80, 220), "glow": (200, 120, 255), "accent": (220, 180, 255)},
        "arcane": {"primary": (220, 80, 180), "glow": (255, 120, 220), "accent": (255, 180, 240)},
        "default": {"primary": (100, 140, 200), "glow": (140, 180, 240), "accent": (200, 220, 255)},
    }

    def __init__(self, character: Character, app: "App", toggle_inventory_callback=None, use_skill_callback=None, open_shop_callback=None):
        self.character = character
        self.app = app
        self.toggle_inventory_callback = toggle_inventory_callback
        self.use_skill_callback = use_skill_callback
        self.open_shop_callback = open_shop_callback
        self.font = cfg.get_font(max(8,int(40 * cfg.ui_scale())))
        self.stamina_font = pygame.font.Font(None, 24)
        self.stamina_label = self.stamina_font.render(_("STAMINA"), True, (255, 255, 255))

        try:
            self.hp_icon = pygame.image.load("assets/heart.png")
            ico = max(8,int(50 * cfg.ui_scale()))
            self.hp_icon = pygame.transform.scale(self.hp_icon, (ico, ico))
        except FileNotFoundError:
            ico = max(8,int(50 * cfg.ui_scale()))
            self.hp_icon = pygame.Surface((ico, ico), pygame.SRCALPHA)
            pygame.draw.circle(self.hp_icon, (255, 0, 0), (ico//2, ico//2), ico//2)

        try:
            self.life_icon = pygame.image.load("assets/skull.png")
            ico = max(8,int(50 * cfg.ui_scale()))
            self.life_icon = pygame.transform.scale(self.life_icon, (ico, ico))
        except FileNotFoundError:
            ico = max(8,int(50 * cfg.ui_scale()))
            self.life_icon = pygame.Surface((ico, ico), pygame.SRCALPHA)
            pygame.draw.circle(self.life_icon, (200, 200, 200), (ico//2, ico//2), ico//2)

        scale = cfg.ui_scale()
        button_width = max(1,int(200 * scale))
        button_height = max(1,int(50 * scale))
        button_x = int(200 * scale)
        button_y = int(240 * scale)

        self.inv_button = Button(
            pygame.Rect(button_x, button_y, button_width, button_height),
            _("INVENTORY"),
            (100, 100, 100),
            (150, 150, 150),
            self.font,
            (255, 255, 255),
            max(2,int(10 * cfg.ui_scale())),
            on_click=self.toggle_inventory
        )


        # Skill/ability hotbar on the right (visual only for now)
        self.skill_slot_size = 64
        self.skill_slot_padding = 10
        self.skill_slots_count = 6
        self.skill_panel_margin = 10
        self.skill_panel_width = self.skill_slot_size + self.skill_slot_padding * 2
        self.skill_total_slots_height = (self.skill_slot_size * self.skill_slots_count) + (self.skill_slot_padding * (self.skill_slots_count + 1))
        self.skill_panel_x = 0
        self.skill_panel_y = 0
        self.animation_time = 0.0

        self.hp_icon_pos = (0, 0)
        self.life_icon_pos = (0, 0)
        self.hp_bar_rect = pygame.Rect(0, 0, 0, 0)
        self.xp_bar_rect = pygame.Rect(0, 0, 0, 0)
        self.stamina_bar_rect = pygame.Rect(0, 0, 0, 0)
        self.mana_bar_rect = pygame.Rect(0, 0, 0, 0)
        self._layout_size = None

        # slot rects (populated/updated per-frame or on-event)
        self.skill_slot_rects: list[pygame.Rect] = []

    def _recalc_layout(self, screen_width: int, screen_height: int):
        """Recalculate HUD positions based on the current screen size."""
        left_margin = 20
        top_margin = 20
        right_margin = 20
        bottom_margin = 20
        bar_width = max(220, min(320, screen_width // 4))
        bar_height = max(8,int(30 * cfg.ui_scale()))

        self.hp_icon_pos = (left_margin, top_margin)
        self.hp_bar_rect = pygame.Rect(left_margin + 60, top_margin + 10, bar_width, bar_height)
        self.life_icon_pos = (left_margin, top_margin + 60)

        scale = cfg.ui_scale()
        button_width = max(1,int(200 * scale))
        button_height = max(1,int(50 * scale))
        button_x = left_margin
        button_y = top_margin + int(170 * scale)
        self.inv_button.rect = pygame.Rect(button_x, button_y, button_width, button_height)
        try:
            self.inv_button._update_text_surface()
        except Exception:
            pass
        pass

        xp_bar_width = min(320, max(220, screen_width // 4))
        xp_bar_height = 15
        xp_bar_x = screen_width - right_margin - xp_bar_width
        xp_bar_y = top_margin + 10
        self.xp_bar_rect = pygame.Rect(xp_bar_x, xp_bar_y, xp_bar_width, xp_bar_height)

        self.skill_panel_x = screen_width - self.skill_panel_width - right_margin
        self.skill_panel_y = (screen_height - self.skill_total_slots_height) // 2

        # Stamina bar above the hotbar at the bottom of the screen
        hotbar_scale = cfg.INV_HOTBAR_SCALE * cfg.ui_scale()
        hotbar_slot_size = int(cfg.BASE_INV_slot_size * hotbar_scale)
        hotbar_border = cfg.BASE_INV_border
        hotbar_columns = getattr(cfg, 'INV_HOTBAR_COLUMNS', 10)
        hotbar_total_width = (hotbar_slot_size + hotbar_border) * hotbar_columns + hotbar_border
        hotbar_top = screen_height + cfg.INV_HOTBAR_Y_OFFSET - hotbar_slot_size

        stamina_bar_width = hotbar_total_width
        stamina_bar_height = 12
        stamina_bar_x = (screen_width - stamina_bar_width) // 2
        stamina_bar_y = hotbar_top - stamina_bar_height - 10
        self.stamina_bar_rect = pygame.Rect(stamina_bar_x, stamina_bar_y, stamina_bar_width, stamina_bar_height)

        # Mana bar above stamina bar
        mana_bar_width = hotbar_total_width
        mana_bar_height = 14
        mana_bar_x = (screen_width - mana_bar_width) // 2
        mana_bar_y = stamina_bar_y - mana_bar_height - 6
        self.mana_bar_rect = pygame.Rect(mana_bar_x, mana_bar_y, mana_bar_width, mana_bar_height)

        # rebuild rects
        self.skill_slot_rects = []
        for i in range(self.skill_slots_count):
            sx = self.skill_panel_x + self.skill_slot_padding
            sy = self.skill_panel_y + self.skill_slot_padding + i * (self.skill_slot_size + self.skill_slot_padding)
            self.skill_slot_rects.append(pygame.Rect(sx, sy, self.skill_slot_size, self.skill_slot_size))

        # top skillbar removed from layout

    def _ensure_layout(self, screen_width: int, screen_height: int):
        size = (screen_width, screen_height)
        if self._layout_size != size:
            self._layout_size = size
            self._recalc_layout(screen_width, screen_height)

    def toggle_inventory(self):
        if self.toggle_inventory_callback:
            self.toggle_inventory_callback()
        else:
            self.app.INV_manager.player_inventory_opened = not self.app.INV_manager.player_inventory_opened
        logger.info(f"Inventory toggled: open={self.app.INV_manager.player_inventory_opened}")

    def handle_event(self, event: pygame.event.Event):
        try:
            sw, sh = self.app.screen.get_size()
            self._ensure_layout(sw, sh)
        except Exception:
            self._ensure_layout(cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.inv_button.rect.collidepoint(event.pos):
                if self.inv_button.on_click:
                    self.inv_button.on_click()

            # Only handle skill slot clicks when shop is not open
            if not getattr(self.app.INV_manager, 'current_shop_inv', None):
                for index, slot_rect in enumerate(self.skill_slot_rects):
                    if slot_rect.collidepoint(event.pos):
                        if self.use_skill_callback:
                            logger.info(f"Skill slot used: {index}")
                            self.use_skill_callback(index)
                        break

    def _get_skill_theme(self, skill):
        if skill is None:
            return self.NEON_THEMES["default"]
        skill_id = skill.get("skill_id", "").lower()
        name = skill.get("name", "").lower()
        color = skill.get("color", (100, 140, 200))
        
        for theme_name, theme in self.NEON_THEMES.items():
            if theme_name in skill_id or theme_name in name:
                return theme
        
        best_match = "default"
        best_score = 0
        for theme_name, theme in self.NEON_THEMES.items():
            primary = theme["primary"]
            score = sum(abs(a - b) for a, b in zip(color, primary))
            if score < best_score or best_score == 0:
                best_score = score
                best_match = theme_name
        return self.NEON_THEMES.get(best_match, self.NEON_THEMES["default"])

    def _draw_hud_skill_slot(self, surface, rect, skill, idx):
        t = self.animation_time
        theme = self._get_skill_theme(skill)
        
        # Panel background with glow
        pulse = (math.sin(t * 2.5 + idx * 0.5) + 1.0) * 0.5
        if skill:
            bg_color = skill.get("color", theme["primary"])
            border_color = skill.get("accent", theme["accent"])
            glow_color = theme["glow"]
        else:
            bg_color = cfg.INV_SLOT_BG_COLOR
            border_color = cfg.INV_SLOT_BORDER_COLOR
            glow_color = (40, 40, 50)

        # Glow layers for active skills
        if skill:
            for offset in range(3, 0, -1):
                glow_rect = rect.inflate(offset * 2, offset * 2)
                alpha = int(40 + 30 * pulse) // (offset + 1)
                glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                gc = (*glow_color, alpha)
                pygame.draw.rect(glow_surf, gc, glow_surf.get_rect(), border_radius=14 + offset)
                surface.blit(glow_surf, glow_rect.topleft)

        # Slot background
        pygame.draw.rect(surface, bg_color, rect, border_radius=cfg.INV_SLOT_BORDER_RADIUS)
        
        # Inner shadow for depth
        inner_rect = rect.inflate(-4, -4)
        pygame.draw.rect(surface, cfg.INV_SLOT_INNER_SHADOW, inner_rect, border_radius=cfg.INV_SLOT_INNER_BORDER_RADIUS)

        # Border
        final_border = border_color
        if skill:
            final_border = tuple(min(255, int(c * 1.2)) for c in border_color)
        pygame.draw.rect(surface, final_border, rect, 2, border_radius=cfg.INV_SLOT_BORDER_RADIUS)

        if skill:
            # Get cooldown percentage (0.0 = ready, 1.0 = just used)
            cooldown_percent = self.character.get_skill_cooldown_percent(skill)
            
            # Draw cooldown overlay if skill is on cooldown
            if cooldown_percent > 0.0:
                # Semi-transparent dark overlay
                overlay_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(overlay_surf, cfg.COOLDOWN_OVERLAY_COLOR, overlay_surf.get_rect(), border_radius=cfg.INV_SLOT_BORDER_RADIUS)
                surface.blit(overlay_surf, rect.topleft)
                
                # Progress bar at bottom of slot
                bar_height = cfg.COOLDOWN_BAR_HEIGHT
                bar_rect = pygame.Rect(rect.left + 2, rect.bottom - bar_height - 2, rect.width - 4, bar_height)
                
                # Background of progress bar
                pygame.draw.rect(surface, cfg.COOLDOWN_BAR_BG_COLOR, bar_rect, border_radius=2)
                
                # Fill showing remaining cooldown (fills from left as cooldown recovers)
                fill_width = int((1.0 - cooldown_percent) * bar_rect.width)
                if fill_width > 0:
                    fill_rect = pygame.Rect(bar_rect.left, bar_rect.top, fill_width, bar_rect.height)
                    pygame.draw.rect(surface, cfg.COOLDOWN_BAR_FILL_COLOR, fill_rect, border_radius=2)
                
                # Display cooldown time remaining
                skill_id = skill.get("skill_id", "")
                if skill_id == "berserkers_rage":
                    cooldown = self.character.berserkers_rage_cooldown + getattr(self.character, "berserkers_rage_cooldown_bonus", 0)
                elif skill_id == "chrono_shift":
                    cooldown = self.character.chrono_shift_cooldown + getattr(self.character, "chrono_shift_cooldown_bonus", 0)
                else:
                    cooldown = getattr(self.character, f"{skill_id}_cooldown", 0)
                cooldown_time = cooldown / 1000.0
                
                remaining_time = cooldown_time * cooldown_percent
                if remaining_time > 0.0:
                    cooldown_font = cfg.get_font(max(8, int(cfg.COOLDOWN_TEXT_SIZE * cfg.ui_scale())))
                    time_text = f"{remaining_time:.1f}s"
                    time_surf = cooldown_font.render(time_text, True, cfg.COOLDOWN_TEXT_COLOR)
                    # Lower the remaining time text slightly for better visual alignment
                    y_offset = int(10 * cfg.ui_scale())
                    time_rect = time_surf.get_rect(center=(rect.centerx, rect.centery + y_offset))
                    surface.blit(time_surf, time_rect)
            else:
                # Skill is ready - show subtle ready indicator
                ready_pulse = (math.sin(t * 3.0) + 1.0) * 0.5
                ready_alpha = int(60 + 40 * ready_pulse)
                ready_surf = pygame.Surface((rect.width - 4, cfg.COOLDOWN_BAR_HEIGHT), pygame.SRCALPHA)
                ready_color = (*cfg.COOLDOWN_BAR_READY_COLOR[:3], ready_alpha)
                pygame.draw.rect(ready_surf, ready_color, ready_surf.get_rect(), border_radius=2)
                surface.blit(ready_surf, (rect.left + 2, rect.bottom - cfg.COOLDOWN_BAR_HEIGHT - 2))
            
            small_font = cfg.get_font(max(8, int(16 * cfg.ui_scale())))
            name = small_font.render(skill.get("name", ""), True, cfg.INV_ITEM_TEXT_COLOR)
            surface.blit(name, name.get_rect(center=(rect.centerx, rect.centery - 4)))
            
            ident = small_font.render(str(idx + 1), True, cfg.INV_ITEM_TEXT_COLOR)
            surface.blit(ident, ident.get_rect(bottomright=(rect.right - 6, rect.bottom - 6)))

    def _on_shop_clicked(self):
        if self.open_shop_callback:
            try:
                self.open_shop_callback()
            except Exception:
                pass
        else:
            # fallback: try to open shop via gameplay state
            try:
                game_state = getattr(self.app.manager, 'states', {}).get('gameplay')
                if game_state and hasattr(game_state, 'open_shop'):
                    game_state.open_shop()
            except Exception:
                pass

    def draw(self, screen: pygame.Surface):
        # Update animation time using the game clock for smooth animations
        try:
            dt = self.app.clock.get_time() / 1000.0
        except Exception:
            dt = 0.016
        self.animation_time += dt

        try:
            sw, sh = screen.get_size()
            self._ensure_layout(sw, sh)
        except Exception:
            self._ensure_layout(cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)

        icon_x, icon_y = self.hp_icon_pos
        screen.blit(self.hp_icon, (icon_x, icon_y))

        bar_x = self.hp_bar_rect.x
        bar_y = self.hp_bar_rect.y
        bar_width = self.hp_bar_rect.width
        bar_height = self.hp_bar_rect.height

        hp_percent = max(0, self.character.hp / self.character.max_hp)
        current_bar_width = int(bar_width * hp_percent)

        # HP Bar Background (Rounded)
        hp_bg_surf = pygame.Surface((bar_width, bar_height), pygame.SRCALPHA)
        pygame.draw.rect(hp_bg_surf, (40, 40, 50, 200), hp_bg_surf.get_rect(), border_radius=8)
        screen.blit(hp_bg_surf, (bar_x, bar_y))

        # HP Bar Fill (Rounded)
        if current_bar_width > 0:
            # Clamp radius to avoid distortion on small widths
            fill_radius = min(8, current_bar_width // 2)
            hp_fill_surf = pygame.Surface((current_bar_width, bar_height), pygame.SRCALPHA)
            pygame.draw.rect(hp_fill_surf, (220, 30, 60), hp_fill_surf.get_rect(), border_radius=fill_radius)
            screen.blit(hp_fill_surf, (bar_x, bar_y))

        # HP Bar Border (Rounded)
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=8)
        
        # Draw HP Text
        hp_text = cfg.INV_nums_font.render(f"{self.character.hp}/{self.character.max_hp}", True, (255, 255, 255))
        screen.blit(hp_text, (bar_x + bar_width // 2 - hp_text.get_width() // 2, bar_y + 5))

        # Draw time indicator
        game_state = self.app.manager.states.get("gameplay")
        time_string = "--:--"
        is_day = True
        if game_state and hasattr(game_state, "_format_game_time"):
            time_string = game_state._format_game_time()
            is_day = game_state.is_daytime()

        icon_radius = max(6, int(14 * cfg.ui_scale()))
        icon_center = (bar_x + bar_width + icon_radius + 20, bar_y + bar_height // 2)
        if is_day:
            pygame.draw.circle(screen, (255, 220, 110), icon_center, icon_radius)
            for angle in (0, 90, 180, 270):
                radians = math.radians(angle)
                dx = int(math.cos(radians) * (icon_radius + 6))
                dy = int(math.sin(radians) * (icon_radius + 6))
                pygame.draw.line(screen, (255, 220, 110), icon_center, (icon_center[0] + dx, icon_center[1] + dy), 2)
        else:
            pygame.draw.circle(screen, (225, 225, 230), icon_center, icon_radius)
            moon_offset = (int(icon_radius * 0.4), -int(icon_radius * 0.2))
            pygame.draw.circle(screen, (30, 30, 50), (icon_center[0] + moon_offset[0], icon_center[1] + moon_offset[1]), int(icon_radius * 0.8))

        time_text = self.font.render(time_string, True, (255, 255, 255))
        screen.blit(time_text, (icon_center[0] + icon_radius + 8, icon_center[1] - time_text.get_height() // 2))

        lives_icon_x, lives_icon_y = self.life_icon_pos

        screen.blit(self.life_icon, (lives_icon_x, lives_icon_y))

        # Death Counter with Shadow
        death_str = f" {self.character.death_count}"
        death_shadow = self.font.render(death_str, True, (0, 0, 0))
        screen.blit(death_shadow, (lives_icon_x + 62, lives_icon_y + 7))
        
        death_text = self.font.render(death_str, True, (220, 50, 50))
        screen.blit(death_text, (lives_icon_x + 60, lives_icon_y + 5))

        # XP Bar
        xp_bar_x = self.xp_bar_rect.x
        xp_bar_y = self.xp_bar_rect.y
        xp_bar_width = self.xp_bar_rect.width
        xp_bar_height = self.xp_bar_rect.height
        
        xp_percent = max(0, self.character.xp / self.character.xp_to_next_level)
        current_xp_width = int(xp_bar_width * xp_percent)
        
        # Draw XP Background
        pygame.draw.rect(screen, (50, 50, 50), (xp_bar_x, xp_bar_y, xp_bar_width, xp_bar_height))
        # Draw XP
        pygame.draw.rect(screen, (0, 200, 0), (xp_bar_x, xp_bar_y, current_xp_width, xp_bar_height))
        # Draw Border
        pygame.draw.rect(screen, (255, 255, 255), (xp_bar_x, xp_bar_y, xp_bar_width, xp_bar_height), 2)
        
        # Level Text
        level_text = self.font.render(f"Lvl {self.character.level}", True, (255, 255, 255))
        level_text_rect = level_text.get_rect(midright=(xp_bar_x - 12, xp_bar_y + xp_bar_height // 2))
        screen.blit(level_text, level_text_rect)

        self.inv_button.draw(screen)
        pass

        stamina_bar_x = self.stamina_bar_rect.x
        stamina_bar_y = self.stamina_bar_rect.y
        stamina_bar_width = self.stamina_bar_rect.width
        stamina_bar_height = self.stamina_bar_rect.height

        stamina_percent = max(0, self.character.stamina / self.character.max_stamina)
        current_stamina_width = int(stamina_bar_width * stamina_percent)

        stamina_color = (50, 200, 50)  # Always green

        # Stamina Bar Background (Rounded)
        stam_bg_surf = pygame.Surface((stamina_bar_width, stamina_bar_height), pygame.SRCALPHA)
        pygame.draw.rect(stam_bg_surf, (30, 30, 40, 200), stam_bg_surf.get_rect(), border_radius=6)
        screen.blit(stam_bg_surf, (stamina_bar_x, stamina_bar_y))

        # Stamina Bar Fill (Rounded)
        if current_stamina_width > 0:
            fill_radius = min(6, current_stamina_width // 2)
            stam_fill_surf = pygame.Surface((current_stamina_width, stamina_bar_height), pygame.SRCALPHA)
            pygame.draw.rect(stam_fill_surf, stamina_color, stam_fill_surf.get_rect(), border_radius=fill_radius)
            screen.blit(stam_fill_surf, (stamina_bar_x, stamina_bar_y))

        # Stamina Bar Border (Rounded)
        pygame.draw.rect(screen, (200, 200, 200), (stamina_bar_x, stamina_bar_y, stamina_bar_width, stamina_bar_height), 1, border_radius=6)

        # ═══════════════════════════════════════════════════════════════
        # MANA BAR - Magical Purple-Blue with Gold Trim and Stars
        # ═══════════════════════════════════════════════════════════════
        mana_bar_x = self.mana_bar_rect.x
        mana_bar_y = self.mana_bar_rect.y
        mana_bar_width = self.mana_bar_rect.width
        mana_bar_height = self.mana_bar_rect.height

        mana_percent = max(0, self.character.mana / self.character.max_mana)
        current_mana_width = int(mana_bar_width * mana_percent)

        # Mana Bar Background (Dark purple)
        mana_bg_surf = pygame.Surface((mana_bar_width, mana_bar_height), pygame.SRCALPHA)
        pygame.draw.rect(mana_bg_surf, (15, 8, 35, 220), mana_bg_surf.get_rect(), border_radius=7)
        screen.blit(mana_bg_surf, (mana_bar_x, mana_bar_y))

        # Mana Bar Fill (Gradient purple-blue with shimmer)
        if current_mana_width > 0:
            fill_radius = min(7, current_mana_width // 2)
            mana_fill_surf = pygame.Surface((current_mana_width, mana_bar_height), pygame.SRCALPHA)
            # Base gradient
            for x in range(current_mana_width):
                t = x / max(1, current_mana_width)
                # Purple to blue gradient
                r = int(80 + 60 * (1 - t))
                g = int(40 + 80 * t)
                b = int(180 + 75 * t)
                pygame.draw.line(mana_fill_surf, (r, g, b, 240), (x, 0), (x, mana_bar_height - 1))
            # Shimmer highlight
            shimmer_offset = int((self.animation_time * 40) % (current_mana_width + 60)) - 30
            for sx in range(max(0, shimmer_offset), min(current_mana_width, shimmer_offset + 30)):
                shimmer_alpha = int(80 * (1 - abs(sx - shimmer_offset - 15) / 15))
                if shimmer_alpha > 0 and sx < current_mana_width:
                    pygame.draw.line(mana_fill_surf, (200, 180, 255, shimmer_alpha), (sx, 1), (sx, 2))
            # Clip with rounded corners
            clip_surf = pygame.Surface((current_mana_width, mana_bar_height), pygame.SRCALPHA)
            pygame.draw.rect(clip_surf, (255, 255, 255, 255), clip_surf.get_rect(), border_radius=fill_radius)
            mana_fill_surf.blit(clip_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(mana_fill_surf, (mana_bar_x, mana_bar_y))

        # Gold Trim Border (Double layer for richness)
        gold_outer = (212, 175, 55)
        gold_inner = (255, 215, 100)
        pygame.draw.rect(screen, gold_outer, (mana_bar_x - 1, mana_bar_y - 1, mana_bar_width + 2, mana_bar_height + 2), 2, border_radius=8)
        pygame.draw.rect(screen, gold_inner, (mana_bar_x, mana_bar_y, mana_bar_width, mana_bar_height), 1, border_radius=7)

        # Magical Stars and Sparkles
        t = self.animation_time
        star_positions = [
            (0.1, 0.3), (0.3, 0.7), (0.5, 0.2), (0.7, 0.8), (0.9, 0.4),
            (0.15, 0.6), (0.45, 0.5), (0.75, 0.3), (0.85, 0.7)
        ]
        for sx_pct, sy_pct in star_positions:
            sx = mana_bar_x + int(sx_pct * mana_bar_width)
            sy = mana_bar_y + int(sy_pct * mana_bar_height)
            # Twinkle effect
            twinkle = (math.sin(t * 4.0 + sx_pct * 10) + 1.0) * 0.5
            if twinkle > 0.6:
                star_alpha = int(200 * (twinkle - 0.6) * 2.5)
                star_size = 1 + int(twinkle * 2)
                star_color = (255, 255, 200, star_alpha)
                # Draw 4-pointed star
                pygame.draw.line(screen, star_color[:3], (sx - star_size, sy), (sx + star_size, sy), 1)
                pygame.draw.line(screen, star_color[:3], (sx, sy - star_size), (sx, sy + star_size), 1)

        # Corner gem decorations (magical orbs at edges)
        gem_glow = int(100 + 60 * math.sin(t * 3.0))
        for gx, gy in [(mana_bar_x + 4, mana_bar_y + mana_bar_height // 2),
                       (mana_bar_x + mana_bar_width - 4, mana_bar_y + mana_bar_height // 2)]:
            gem_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(gem_surf, (120, 80, 200, gem_glow), (4, 4), 4)
            pygame.draw.circle(gem_surf, (180, 150, 255, gem_glow), (4, 4), 2)
            screen.blit(gem_surf, (gx - 4, gy - 4))

        # Draw vertical skill hotbar (right side) if no shop is open
        if not getattr(self.app.INV_manager, 'current_shop_inv', None):
            panel_rect = pygame.Rect(self.skill_panel_x, self.skill_panel_y, self.skill_panel_width, self.skill_total_slots_height)
            
            # Shadow
            shadow = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 120), shadow.get_rect(), border_radius=cfg.INV_PLAYER_BORDER_RADIUS)
            screen.blit(shadow, (panel_rect.x + 8, panel_rect.y + 8))
            
            # Panel background
            pygame.draw.rect(screen, cfg.INV_PLAYER_BG_COLOR, panel_rect, border_radius=cfg.INV_PLAYER_BORDER_RADIUS)
            pygame.draw.rect(screen, cfg.INV_PLAYER_BORDER_COLOR, panel_rect, cfg.INV_PLAYER_BORDER_WIDTH, border_radius=cfg.INV_PLAYER_BORDER_RADIUS)

            skillbar = getattr(self.character, "skillbar", [])
            for idx, slot in enumerate(self.skill_slot_rects):
                skill = skillbar[idx] if idx < len(skillbar) else None
                self._draw_hud_skill_slot(screen, slot, skill, idx)

        # top skillbar removed
