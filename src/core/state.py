import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import App

class State:
    """
    Represents a base state in a state management system.
    This class should be subclassed to implement specific states for an application.
    Each state can handle events and draw itself to the screen.
    """

    def __init__(self, app: "App"):
        self.app = app

    def handle_event(self, event: pygame.event.Event):
        """Handles input events specific to the state."""
        pass

    def draw(self, screen: pygame.Surface):
        """Renders the state to the provided screen surface."""
        pass

    def update(self, dt: float):
        """Updates the state's logic."""
        pass
