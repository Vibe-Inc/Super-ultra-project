import pygame
from typing import TYPE_CHECKING

from src.ui.menus import MainMenu, SettingsMenu, CreditsMenu, PauseMenu
from src.core.game import Game

if TYPE_CHECKING:
    from src.app import App


class StateManager:
    """
    Manages different application states such as main menu, settings, and credits.
    Args:
        app: The main application object, passed to each state.
    Attributes:
        states (dict): Dictionary mapping state names to their corresponding state objects.
        current_state: The currently active state object.
    Methods:
        set_state(name):
            Sets the current state to the state associated with the given name.
        get_state():
            Returns the name of the currently active state, or None if no state is active.
        handle_event(event):
            Delegates event handling to the current state if one is active.
        draw(screen):
            Delegates drawing to the current state if one is active.
    """

    def __init__(self, app: "App"):
        self.states = {
            "main": MainMenu(app),
            "settings": SettingsMenu(app),
            "credits": CreditsMenu(app),
            "gameplay": Game(app),
            "pause": PauseMenu(app)
        }
        self.current_state = None

    def set_state(self, name):
        self.current_state = self.states.get(name)

    def get_state(self):
        for name, state in self.states.items():
            if state == self.current_state:
                return name
        return None

    def handle_event(self, event):
        if self.current_state:
            self.current_state.handle_event(event)

    def draw(self, screen):
        if self.current_state:
            self.current_state.draw(screen)

    def reinit_states(self):
        current_name = self.get_state()
        
        gameplay_state = self.states["gameplay"]
        if hasattr(gameplay_state, "reinit_ui"):
            gameplay_state.reinit_ui()
        
        self.states = {
            "main": MainMenu(self.states["main"].app),
            "settings": SettingsMenu(self.states["settings"].app),
            "credits": CreditsMenu(self.states["credits"].app),
            "gameplay": gameplay_state,
            "pause": PauseMenu(self.states["pause"].app)
        }
        
        if current_name:
            self.current_state = self.states.get(current_name)
