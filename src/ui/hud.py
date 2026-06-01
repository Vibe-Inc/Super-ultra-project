import math
import pygame
from typing import TYPE_CHECKING
from src.entities.character import Character
from src.ui.widgets import Button
import src.config as cfg
from src.core.logger import logger

if TYPE_CHECKING:
    from src.app import App

class HUD:

    """
    Head-Up Display (HUD) for player status and UI controls.

    This class is responsible for rendering player health, lives, and the inventory button, as well as handling related UI events.

    Attributes:
        character (Character):
            The character object whose state is being displayed.
        app (App):
            The main application object for accessing managers (e.g., INV_manager).
        font (pygame.font.Font):
            The font used for rendering text.
        hp_icon (pygame.Surface):
            The icon representing health (a heart).
        life_icon (pygame.Surface):
            The icon representing the number of lives (a skull).
        inv_button (Button):
            The button to open/close the inventory.
        toggle_inventory_callback (callable | None):
            Optional callback to toggle inventory state.

    Methods:
        __init__(character, app, toggle_inventory_callback=None):
            Initialize the HUD with player character, app, and optional inventory toggle callback.
        toggle_inventory():
            Toggle the inventory open/closed, using callback if provided.
        handle_event(event):
            Handle mouse events for the inventory button.
            Args:
                event (pygame.event.Event): The Pygame event to process.
        draw(screen):
            Draw the HUD elements (health bar, lives, inventory button) on the screen.
            Args:
                screen (pygame.Surface): The surface to draw the HUD on.
    """

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

        self.hp_icon_pos = (0, 0)
        self.life_icon_pos = (0, 0)
        self.hp_bar_rect = pygame.Rect(0, 0, 0, 0)
        self.xp_bar_rect = pygame.Rect(0, 0, 0, 0)
        self.stamina_bar_rect = pygame.Rect(0, 0, 0, 0)
        self.money_pos = (0, 0)
        self._layout_size = None

        # Create coin icon (gold circle)
        coin_size = max(8, int(28 * cfg.ui_scale()))
        self.coin_icon = pygame.Surface((coin_size, coin_size), pygame.SRCALPHA)
        pygame.draw.circle(self.coin_icon, (212, 175, 55), (coin_size // 2, coin_size // 2), coin_size // 2)
        pygame.draw.circle(self.coin_icon, (255, 215, 0), (coin_size // 2, coin_size // 2), coin_size // 2 - 2)
        # Add a "G" letter in the center for "Gold"
        coin_font = cfg.get_font(max(8, int(14 * cfg.ui_scale())))
        g_surf = coin_font.render("G", True, (139, 119, 42))
        g_rect = g_surf.get_rect(center=(coin_size // 2, coin_size // 2))
        self.coin_icon.blit(g_surf, g_rect)

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

        stamina_bar_width = min(600, max(280, screen_width // 2))
        stamina_bar_height = 25
        stamina_bar_x = (screen_width - stamina_bar_width) // 2
        stamina_bar_y = (screen_height - stamina_bar_height - bottom_margin)-80
        self.stamina_bar_rect = pygame.Rect(stamina_bar_x, stamina_bar_y, stamina_bar_width, stamina_bar_height)

        self.skill_panel_x = screen_width - self.skill_panel_width - right_margin
        self.skill_panel_y = (screen_height - self.skill_total_slots_height) // 2

        # Money display position (below lives icon, left side)
        self.money_pos = (left_margin, top_margin + 110)

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

        # Draw Background
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        # Draw HP
        pygame.draw.rect(screen, (220, 20, 60), (bar_x, bar_y, current_bar_width, bar_height))
        # Draw Border
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 3)
        
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

        lives_text = self.font.render(f"x {self.character.death_count}", True, (255, 255, 255))
        screen.blit(lives_text, (lives_icon_x + 60, lives_icon_y + 5))

        # ---- Money display with coin icon ----
        money_x, money_y = self.money_pos
        screen.blit(self.coin_icon, (money_x, money_y))
        money_font = cfg.get_font(max(8, int(24 * cfg.ui_scale())))
        money_text = money_font.render(f"{self.app.money}", True, (255, 215, 0))
        coin_size = self.coin_icon.get_width()
        screen.blit(money_text, (money_x + coin_size + 8, money_y + (coin_size - money_text.get_height()) // 2))

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

        if self.character.stamina <= 0:
            stamina_color = (150, 0, 0)  # Dark red when depleted
        elif self.character.is_sprinting:
            stamina_color = (255, 200, 0)  # Orange while sprinting
        else:
            stamina_color = (0, 200, 255)  # Cyan when full/regenerating

        pygame.draw.rect(screen, (40, 40, 40), (stamina_bar_x, stamina_bar_y, stamina_bar_width, stamina_bar_height))
        pygame.draw.rect(screen, stamina_color, (stamina_bar_x, stamina_bar_y, current_stamina_width, stamina_bar_height))
        pygame.draw.rect(screen, (200, 200, 200), (stamina_bar_x, stamina_bar_y, stamina_bar_width, stamina_bar_height), 3)

        label_rect = self.stamina_label.get_rect(center=(stamina_bar_x + stamina_bar_width // 2, stamina_bar_y - 15))
        screen.blit(self.stamina_label, label_rect)

        # Draw vertical skill hotbar (right side) if no shop is open
        if not getattr(self.app.INV_manager, 'current_shop_inv', None):
            panel_rect = pygame.Rect(self.skill_panel_x, self.skill_panel_y, self.skill_panel_width, self.skill_total_slots_height)
            # panel background
            pygame.draw.rect(screen, (30, 30, 30), panel_rect)
            pygame.draw.rect(screen, (200, 200, 200), panel_rect, 2)

            small_font = cfg.get_font(max(8,int(20 * cfg.ui_scale())))
            skillbar = getattr(self.character, "skillbar", [])
            for idx, slot in enumerate(self.skill_slot_rects, start=1):
                skill = skillbar[idx - 1] if idx - 1 < len(skillbar) else None
                fill = skill.get("color", (60, 60, 60)) if skill else (60, 60, 60)
                border = skill.get("accent", (180, 180, 180)) if skill else (180, 180, 180)
                pygame.draw.rect(screen, fill, slot)
                pygame.draw.rect(screen, border, slot, 2)

                if skill:
                    label = small_font.render(skill.get("name", ""), True, (255, 255, 255))
                    label_rect = label.get_rect(center=(slot.centerx, slot.centery - 4))
                    screen.blit(label, label_rect)

                # placeholder: draw a small number showing the hotkey
                num_surf = small_font.render(str(idx if idx <= 9 else idx % 10), True, (220, 220, 220))
                num_rect = num_surf.get_rect(bottomright=(slot.right - 6, slot.bottom - 6))
                screen.blit(num_surf, num_rect)

        # top skillbar removed
