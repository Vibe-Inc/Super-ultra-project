import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import App

class State:
    """
    Abstract base class for application states.

    This class should be subclassed to implement specific states (e.g., menus, gameplay) for the application.
    Each state can handle events, draw itself, and update its logic.

    Attributes:
        app (App): Reference to the main application instance.

    Methods:
        __init__(app):
            Initialize the state with a reference to the main app.
        handle_event(event):
            Handle input events specific to the state.
        draw(screen):
            Render the state to the provided screen surface.
        update(dt):
            Update the state's logic.
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
