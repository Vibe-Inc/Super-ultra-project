"""
Mage NPC module for the special NPC that gates arcane quests and the Mysterium Magnum.

Provides the MageNPC class that loads its image from a flat file path.
"""

import pygame
from src.entities.npc import NPC
import src.config as cfg


class MageNPC(NPC):
    """
    A special NPC (the Mage) that loads its image from a flat file path
    instead of the standard sprite-set directory structure.

    Uses the custom mage.png asset placed at assets/characters/mage.png.

    Attributes:
        Inherits all attributes from NPC.

    Methods:
        __init__(x, y, dialog_lines, gender):
            Initialize the Mage NPC with custom image loading.
    """

    def __init__(self, x, y, dialog_lines=None, gender='female'):
        """Initialize the Mage NPC bypassing standard NPC image loading.

        Loads the mage.png directly from assets/characters/ and scales it
        to 85px height while preserving aspect ratio.

        Args:
            x (float): World x-coordinate.
            y (float): World y-coordinate.
            dialog_lines (list[str] | None): Optional custom dialog lines.
            gender (str): Gender of the Mage NPC (default 'female').
        """
        # Bypass NPC.__init__ image loading by calling object.__init__ first,
        # then manually setting all the attributes NPC.__init__ would set.
        self.pos = pygame.Vector2(x, y)
        self.interaction_range = 100.0
        self.is_interactable = False
        self.dialog_lines = dialog_lines or [
            "I sense a great power within you.",
        ]
        self.is_merchant = False
        self.gender = gender
        self.was_talked = False

        # Load the mage.png directly — scale to NPC height (85px) while
        # preserving the original aspect ratio (no stretching).
        target_h = 85
        try:
            _raw = pygame.image.load("assets/characters/mage.png")
            scale_factor = target_h / _raw.get_height()
            self.image = pygame.transform.smoothscale(
                _raw,
                (max(1, int(_raw.get_width() * scale_factor)), target_h)
            )
        except FileNotFoundError:
            # Fallback to a default portrait if mage.png is missing
            try:
                _raw = pygame.image.load("assets/characters/WomanHuman1/PortraitAndShowcase/PortraitAndShowcase1.png")
                scale_factor = target_h / _raw.get_height()
                self.image = pygame.transform.smoothscale(
                    _raw,
                    (max(1, int(_raw.get_width() * scale_factor)), target_h)
                )
            except FileNotFoundError:
                self.image = pygame.Surface((85, target_h))
                self.image.fill((180, 80, 220))

        self.rect = self.image.get_rect(topleft=(x, y))

        # Interaction prompt (e.g., "E" key)
        self.font = cfg.get_font(max(8, int(20 * cfg.ui_scale())))
        self.prompt_text = self.font.render("E", True, (255, 255, 255))
        self.prompt_bg_color = (0, 0, 0)