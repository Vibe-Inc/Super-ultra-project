import pygame
from typing import TYPE_CHECKING

from src.ui.menus import MainMenu, SettingsMenu, CreditsMenu, PauseMenu, SaveLoadMenu
from src.core.game import Game

if TYPE_CHECKING:
    from src.app import App


class StateManager:
    """
    Manages the application's high-level states (main menu, settings, credits, gameplay, pause).

    This class is responsible for switching between different UI/game states, delegating event handling and drawing, and reinitializing states when needed (e.g., after a language change).

    Attributes:
        states (dict[str, State]): Mapping of state names to their corresponding state objects.
        current_state (State | None): The currently active state object.

    Methods:
        __init__(app):
            Initialize all states and set the current state to None.
        set_state(name):
            Set the current state by name.
        get_state():
            Get the name of the currently active state, or None if no state is active.
        handle_event(event):
            Delegate event handling to the current state.
        draw(screen):
            Delegate drawing to the current state.
        reinit_states():
            Reinitialize all states (except gameplay), preserving the current state and refreshing UI as needed.
    """

    def __init__(self, app: "App"):
        self.states = {
            "main": MainMenu(app),
            "settings": SettingsMenu(app),
            "credits": CreditsMenu(app),
            "gameplay": Game(app),
            "pause": PauseMenu(app),
            "save_load": SaveLoadMenu(app)
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
