"""
Archeologist NPC module.

Provides the ArcheologistNPC class that loads its image from a flat file path.
"""

import pygame
from src.entities.npc import NPC
import src.config as cfg


class ArcheologistNPC(NPC):
    """
    A special NPC (the Archeologist) that loads its image from a flat file path
    instead of the standard sprite-set directory structure.

    Uses the custom archeologist.png asset placed at assets/characters/archeologist.png.
    """

    def __init__(self, x, y, dialog_lines=None, gender='male'):
        """Initialize the Archeologist NPC bypassing standard NPC image loading."""
        self.pos = pygame.Vector2(x, y)
        self.interaction_range = 100.0
        self.is_interactable = False
        self.dialog_lines = dialog_lines or [
            "Ah, a fellow seeker of knowledge!",
            "This temple holds many secrets... and artifacts.",
            "Care to try your hand at the Archeologium? Who knows what you'll find!"
        ]
        self.is_merchant = False
        self.gender = gender
        self.was_talked = False

        # Load the archeologist.png directly — scale to NPC height (85px) while
        # preserving the original aspect ratio (no stretching).
        target_h = 85
        try:
            _raw = pygame.image.load("assets/characters/archeologist.png")
            scale_factor = target_h / _raw.get_height()
            self.image = pygame.transform.smoothscale(
                _raw,
                (max(1, int(_raw.get_width() * scale_factor)), target_h)
            )
        except FileNotFoundError:
            # Fallback
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

        # Interaction prompt
        self.font = cfg.get_font(max(8, int(20 * cfg.ui_scale())))
        self.prompt_text = self.font.render("E", True, (255, 255, 255))
        self.prompt_bg_color = (0, 0, 0)
