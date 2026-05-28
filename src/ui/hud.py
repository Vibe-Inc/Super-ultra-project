import pygame
from typing import TYPE_CHECKING
from src.entities.character import Character
from src.ui.widgets import Button
import src.config as cfg

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

    def __init__(self, character: Character, app: "App", toggle_inventory_callback=None):
        self.character = character
        self.app = app
        self.toggle_inventory_callback = toggle_inventory_callback
        self.font = cfg.get_font(40)
        self.stamina_font = pygame.font.Font(None, 24)
        self.stamina_label = self.stamina_font.render(_("STAMINA"), True, (255, 255, 255))

        try:
            self.hp_icon = pygame.image.load("assets/heart.png")
            self.hp_icon = pygame.transform.scale(self.hp_icon, (50, 50))
        except FileNotFoundError:
            self.hp_icon = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(self.hp_icon, (255, 0, 0), (25, 25), 25)

        try:
            self.life_icon = pygame.image.load("assets/skull.png")
            self.life_icon = pygame.transform.scale(self.life_icon, (50, 50))
        except FileNotFoundError:
            self.life_icon = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(self.life_icon, (200, 200, 200), (25, 25), 25)

        button_width = 200
        button_height = 50
        button_x = 200
        button_y = 240
        
        self.inv_button = Button(
            pygame.Rect(button_x, button_y, button_width, button_height),
            _("INVENTORY"),
            (100, 100, 100),
            (150, 150, 150),
            self.font,
            (255, 255, 255),
            10,
            on_click=self.toggle_inventory
        )

        # Skill/ability hotbar on the right (visual only for now)
        self.skill_slot_size = 64
        self.skill_slot_padding = 10
        self.skill_slots_count = 6
        self.skill_panel_margin = 10
        self.skill_panel_width = self.skill_slot_size + self.skill_slot_padding * 2
        # calculate top-left of the panel so slots are centered vertically
        self.skill_total_slots_height = (self.skill_slot_size * self.skill_slots_count) + (self.skill_slot_padding * (self.skill_slots_count + 1))
        self.skill_panel_x = cfg.SCREEN_WIDTH - self.skill_panel_width - self.skill_panel_margin
        self.skill_panel_y = max(10, (cfg.SCREEN_HEIGHT - self.skill_total_slots_height) // 2)

        # create slot rects for future input/hover handling
        self.skill_slot_rects = []
        for i in range(self.skill_slots_count):
            sx = self.skill_panel_x + self.skill_slot_padding
            sy = self.skill_panel_y + self.skill_slot_padding + i * (self.skill_slot_size + self.skill_slot_padding)
            self.skill_slot_rects.append(pygame.Rect(sx, sy, self.skill_slot_size, self.skill_slot_size))

    def toggle_inventory(self):
        if self.toggle_inventory_callback:
            self.toggle_inventory_callback()
        else:
            self.app.INV_manager.player_inventory_opened = not self.app.INV_manager.player_inventory_opened

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.inv_button.rect.collidepoint(event.pos):
                if self.inv_button.on_click:
                    self.inv_button.on_click()
            # future: handle clicks on skill slots
            # for i, r in enumerate(self.skill_slot_rects):
            #     if r.collidepoint(event.pos):
            #         print(f"Skill slot {i} clicked")

    def draw(self, screen: pygame.Surface):
        icon_x, icon_y = 200, 120
        screen.blit(self.hp_icon, (icon_x, icon_y))

        bar_x = icon_x + 60
        bar_y = icon_y + 10
        bar_width = 300
        bar_height = 30

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


        lives_icon_x = icon_x
        lives_icon_y = icon_y + 60

        screen.blit(self.life_icon, (lives_icon_x, lives_icon_y))

        lives_text = self.font.render(f"x {self.character.death_count}", True, (255, 255, 255))
        screen.blit(lives_text, (lives_icon_x + 60, lives_icon_y + 5))
        
        # XP Bar
        xp_bar_width = 300
        xp_bar_height = 15
        xp_bar_x = bar_x + 1150
        xp_bar_y = lives_icon_y - 50
        
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
        screen.blit(level_text, (xp_bar_x - 100, xp_bar_y - 15))

        self.inv_button.draw(screen)

        stamina_bar_width = 600
        stamina_bar_height = 25
        stamina_bar_x = (cfg.SCREEN_WIDTH - stamina_bar_width) // 2
        stamina_bar_y = 920

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

        # Draw vertical skill hotbar (right side)
        panel_rect = pygame.Rect(self.skill_panel_x, self.skill_panel_y, self.skill_panel_width, self.skill_total_slots_height)
        # panel background
        pygame.draw.rect(screen, (30, 30, 30), panel_rect)
        pygame.draw.rect(screen, (200, 200, 200), panel_rect, 2)

        small_font = cfg.get_font(20)
        for idx, slot in enumerate(self.skill_slot_rects, start=1):
            pygame.draw.rect(screen, (60, 60, 60), slot)
            pygame.draw.rect(screen, (180, 180, 180), slot, 2)

            # placeholder: draw a small number showing the hotkey
            num_surf = small_font.render(str(idx if idx <= 9 else idx % 10), True, (220, 220, 220))
            num_rect = num_surf.get_rect(bottomright=(slot.right - 6, slot.bottom - 6))
            screen.blit(num_surf, num_rect)