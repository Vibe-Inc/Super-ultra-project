import pygame
from src.entities.character import Character
import src.config as cfg

class NPC:
    """
    Represents a Non-Player Character (NPC) that the player can interact with.

    Attributes:
        pos (pygame.Vector2):
            Position of the NPC on the screen.
        image (pygame.Surface):
            Current frame of the NPC to be drawn.
        interaction_range (float):
            Distance within which the player can interact with the NPC.
        is_interactable (bool):
            Whether the player is currently close enough to interact.
        
    Methods:
        update(player_pos):
            Check distance to player and update interaction status.
        draw(screen):
            Draw the NPC and the interaction prompt if applicable.
    """
    def __init__(self, x, y, sprite_set="MenHuman1", dialog_lines=None, is_merchant=False, gender='male'):
        self.pos = pygame.Vector2(x, y)
        self.interaction_range = 100.0
        self.is_interactable = False
        self.dialog_lines = dialog_lines or [
            "Hey there — you look new around here.",
            "I sell useful gear and supplies for the road.",
            "If you're interested, I can open my shop for you."
        ]
        self.is_merchant = is_merchant
        self.gender = gender
        self.was_talked = False

        try:
            self.image = pygame.transform.scale(
                pygame.image.load(f"assets/characters/{sprite_set}/PortraitAndShowcase/PortraitAndShowcase1.png"), 
                (85, 85)
            )
        except FileNotFoundError:
            
            self.image = pygame.transform.scale(
                pygame.image.load(f"assets/characters/{sprite_set}/FrontWalk/FrontWalk1.png"), 
                (85, 85)
            )

        self.rect = self.image.get_rect(topleft=(x, y))
        
        # Interaction prompt (e.g., "E" key)
        self.font = cfg.get_font(max(8,int(20 * cfg.ui_scale())))
        self.prompt_text = self.font.render("E", True, (255, 255, 255))
        self.prompt_bg_color = (0, 0, 0)

    def update(self, player_pos: pygame.Vector2):
        diff = player_pos - self.pos
        self.is_interactable = diff.length_squared() <= (self.interaction_range * self.interaction_range)

    def draw(self, screen: pygame.Surface, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        draw_pos = (int(self.pos.x - camera_offset.x), int(self.pos.y - camera_offset.y))
        screen.blit(self.image, draw_pos)
        
        if self.is_interactable:
            prompt_rect = self.prompt_text.get_rect(center=(self.pos.x - camera_offset.x + 42, self.pos.y - camera_offset.y - 20))
            bg_rect = prompt_rect.inflate(10, 5)
            pygame.draw.rect(screen, self.prompt_bg_color, bg_rect, border_radius=5)
            screen.blit(self.prompt_text, prompt_rect)
