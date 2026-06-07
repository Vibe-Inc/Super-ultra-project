"""
State manager module for application state transitions.

Provides the StateManager class that orchestrates switching between
different game states (menus, gameplay, pause, etc.).
"""

import pygame
from typing import TYPE_CHECKING

from src.core.logger import logger
from src.ui.menus import MainMenu, SettingsMenu, CreditsMenu, PauseMenu, SaveLoadMenu, SkillbarMenu, SkillTreeMenu, RecipeBookMenu, WikiMenu, CollectionBookMenu, ArcaneQuestMenu, MysteriumMagnumMenu, LocationMapMenu, IntroAnimation, TempleIntroAnimation, EndingAnimation, AchievementsMenu
from src.core.game import Game

if TYPE_CHECKING:
    from src.app import App


class StateManager:
    """
    Manages the application's high-level states (main menu, settings, credits, gameplay, pause).

    This class is responsible for switching between different UI/game states, delegating event
    handling and drawing, and reinitializing states when needed (e.g., after a language change).

    Attributes:
        states (dict[str, State]):
            Mapping of state names to their corresponding state objects.
        current_state (State | None):
            The currently active state object.

    Methods:
        __init__(app):
            Initialize all states and set the current state to None.
        set_state(name):
            Set the current state by name.
        get_state():
            Get the name of the currently active state.
        handle_event(event):
            Delegate event handling to the current state.
        draw(screen):
            Delegate drawing to the current state.
        reinit_states():
            Reinitialize all states (except gameplay), preserving the current state.
    """

    def __init__(self, app: "App"):
        """Initialize all states and set the current state to None.

        Creates all game and menu state instances and stores them in a
        dictionary keyed by state name.

        Args:
            app (App): The main application instance.
        """
        logger.info("Initializing StateManager and States...")
        self.states = {
            "main": MainMenu(app),
            "settings": SettingsMenu(app),
            "credits": CreditsMenu(app),
            "gameplay": Game(app),
            "skillbar": SkillbarMenu(app),
            "skill_tree": SkillTreeMenu(app),
            "pause": PauseMenu(app),
            "save_load": SaveLoadMenu(app),
            "recipe_book": RecipeBookMenu(app),
            "wiki": WikiMenu(app),
            "collection_book": CollectionBookMenu(app),
            "arcane_quest": ArcaneQuestMenu(app),
            "mysterium_magnum": MysteriumMagnumMenu(app),
            "location_map": LocationMapMenu(app),
            "intro_animation": IntroAnimation(app),
            "temple_intro_animation": TempleIntroAnimation(app),
            "ending_animation": EndingAnimation(app),
            "achievements": AchievementsMenu(app),
        }
        self.current_state = None

    def set_state(self, name):
        """Set the current state by name.

        Args:
            name (str): The name of the state to switch to (e.g. ``"main"``, ``"gameplay"``).
                        If the name is not in the states dict, an error is logged.
        """
        if name in self.states:
            logger.info(f"Switching state to: {name}")
            self.current_state = self.states.get(name)
            if self.current_state and hasattr(self.current_state, 'on_enter'):
                try:
                    self.current_state.on_enter()
                except Exception:
                    pass
        else:
            logger.error(f"Attempted to switch to invalid state: {name}")

    def get_state(self):
        """Get the name of the currently active state.

        Returns:
            str | None: The name of the currently active state, or None if
            no state is active.
        """
        for name, state in self.states.items():
            if state == self.current_state:
                return name
        return None

    def handle_event(self, event):
        """Delegate event handling to the current state.

        Args:
            event (pygame.event.Event): The pygame event to forward.
        """
        if self.current_state:
            self.current_state.handle_event(event)

    def draw(self, screen):
        """Delegate drawing to the current state.

        Args:
            screen (pygame.Surface): The surface to draw onto.
        """
        if self.current_state:
            self.current_state.draw(screen)

    def reinit_states(self):
        """Reinitialize all states (except gameplay), preserving the current state.

        Called after a language change or font rescaling so that UI elements
        are rebuilt. The Game state is preserved and only its ``reinit_ui``
        method is called. Quest data is also preserved across the recreation
        of the ArcaneQuest menu.
        """
        current_name = self.get_state()
        logger.info("Reinitializing UI states...")
        
        gameplay_state = self.states["gameplay"]
        if hasattr(gameplay_state, "reinit_ui"):
            gameplay_state.reinit_ui()
        
        # Preserve quest data before recreating the quest menu
        old_quest = self.states.get("arcane_quest")
        quest_data = None
        if old_quest and hasattr(old_quest, "get_quest_data"):
            quest_data = old_quest.get_quest_data()
        
        self.states = {
            "main": MainMenu(self.states["main"].app),
            "settings": SettingsMenu(self.states["settings"].app),
            "credits": CreditsMenu(self.states["credits"].app),
            "gameplay": gameplay_state,
            "skillbar": SkillbarMenu(self.states["main"].app),
            "skill_tree": SkillTreeMenu(self.states["main"].app),
            "pause": PauseMenu(self.states["pause"].app),
            "save_load": SaveLoadMenu(self.states["main"].app),
            "recipe_book": RecipeBookMenu(self.states["main"].app),
            "wiki": WikiMenu(self.states["main"].app),
            "collection_book": CollectionBookMenu(self.states["main"].app),
            "arcane_quest": ArcaneQuestMenu(self.states["main"].app),
            "mysterium_magnum": MysteriumMagnumMenu(self.states["main"].app),
            "location_map": LocationMapMenu(self.states["main"].app),
            "intro_animation": self.states["intro_animation"],
            "temple_intro_animation": self.states["temple_intro_animation"],
            "ending_animation": self.states["ending_animation"],
            "achievements": AchievementsMenu(self.states["main"].app),
        }
        
        # Restore quest data into the new quest menu
        if quest_data:
            new_quest = self.states.get("arcane_quest")
            if new_quest and hasattr(new_quest, "set_quest_data"):
                new_quest.set_quest_data(quest_data)
        
        if current_name:
            self.current_state = self.states.get(current_name)
        logger.info("Reinitialization of UI states complete.")