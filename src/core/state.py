"""
State module providing the base class for application states.

This module defines the abstract State class that all game and menu
states inherit from.
"""

import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app import App


class State:
    """
    Abstract base class for application states.

    This class should be subclassed to implement specific states (e.g., menus, gameplay)
    for the application. Each state can handle events, draw itself, and update its logic.

    Attributes:
        app (App): Reference to the main application instance.

    Methods:
        __init__(app):
            Initialize the state with a reference to the main app.
        on_enter():
            Called when this state becomes the active state.
        handle_event(event):
            Handle input events specific to the state.
        draw(screen):
            Render the state to the provided screen surface.
        update(dt):
            Update the state's logic.
    """

    def __init__(self, app: "App"):
        """Initialize the state with a reference to the main application.

        Args:
            app (App): The main application instance.
        """
        self.app = app

    def on_enter(self):
        """Called when this state becomes the active state.

        Override in subclasses to perform setup logic (e.g., playing music,
        resetting UI state) when the state is entered.
        """
        pass

    def handle_event(self, event: pygame.event.Event):
        """Handle input events specific to the state.

        Args:
            event (pygame.event.Event): The pygame event to process.
        """
        pass

    def draw(self, screen: pygame.Surface):
        """Render the state to the provided screen surface.

        Args:
            screen (pygame.Surface): The surface to draw onto.
        """
        pass

    def update(self, dt: float):
        """Update the state's logic.

        Args:
            dt (float): Delta time in seconds since the last frame.
        """
        pass