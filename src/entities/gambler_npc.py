"""
Gambler NPC module for the tavern gambler NPC that hosts card games.

Provides the GamblerNPC class that loads its image from a flat file path.
"""

import pygame
from src.entities.npc import NPC
import src.config as cfg


class GamblerNPC(NPC):
    """
    A special NPC (the Gambler) that loads its image from a flat file path
    instead of the standard sprite-set directory structure.

    Uses the custom casino_man.png asset placed at assets/characters/casino_man.png.

    Attributes:
        Inherits all attributes from NPC.

    Methods:
        __init__(x, y, dialog_lines, gender):
            Initialize the Gambler NPC with custom image loading.
    """

    def __init__(self, x, y, dialog_lines=None, gender='male'):
        """Initialize the Gambler NPC bypassing standard NPC image loading.

        Loads the casino_man.png directly from assets/characters/ and scales it
        to 85px height while preserving aspect ratio.

        Args:
            x (float): World x-coordinate.
            y (float): World y-coordinate.
            dialog_lines (list[str] | None): Optional custom dialog lines.
            gender (str): Gender of the Gambler NPC (default 'male').
        """
        # Bypass NPC.__init__ image loading by calling object.__init__ first,
        # then manually setting all the attributes NPC.__init__ would set.
        self.pos = pygame.Vector2(x, y)
        self.interaction_range = 100.0
        self.is_interactable = False
        self.dialog_lines = dialog_lines or [
            "Care for a round of cards?",
        ]
        self.is_merchant = False
        self.gender = gender
        self.was_talked = False

        # Load the casino_man.png directly — scale to NPC height (85px) while
        # preserving the original aspect ratio (no stretching).
        target_h = 85
        try:
            _raw = pygame.image.load("assets/characters/casino_man.png")
            scale_factor = target_h / _raw.get_height()
            self.image = pygame.transform.smoothscale(
                _raw,
                (max(1, int(_raw.get_width() * scale_factor)), target_h)
            )
        except FileNotFoundError:
            # Fallback to a default portrait if casino_man.png is missing
            try:
                _raw = pygame.image.load("assets/characters/MenHuman1(Recolor)/PortraitAndShowcase/PortraitAndShowcase1.png")
                scale_factor = target_h / _raw.get_height()
                self.image = pygame.transform.smoothscale(
                    _raw,
                    (max(1, int(_raw.get_width() * scale_factor)), target_h)
                )
            except FileNotFoundError:
                self.image = pygame.Surface((85, target_h))
                self.image.fill((100, 150, 100))

        self.rect = self.image.get_rect(topleft=(x, y))

        # Interaction prompt (e.g., "E" key)
        self.font = cfg.get_font(max(8, int(20 * cfg.ui_scale())))
        self.prompt_text = self.font.render("E", True, (255, 255, 255))
        self.prompt_bg_color = (0, 0, 0)
