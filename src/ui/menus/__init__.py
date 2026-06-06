"""
Menus package for the game UI.

This package contains all menu classes used in the game, split into separate modules
for better organization and maintainability.
"""

from src.ui.menus.base import Menu
from src.ui.menus.main_menu import MainMenu
from src.ui.menus.settings_menu import SettingsMenu
from src.ui.menus.skillbar_menu import SkillbarMenu
from src.ui.menus.skilltree_menu import SkillTreeMenu
from src.ui.menus.credits_menu import CreditsMenu
from src.ui.menus.pause_menu import PauseMenu
from src.ui.menus.save_load_menu import SaveLoadMenu
from src.ui.menus.recipe_book import RecipeBookMenu
from src.ui.menus.wiki_menu import WikiMenu
from src.ui.menus.collection_book import CollectionBookMenu

__all__ = [
    "Menu",
    "MainMenu",
    "SettingsMenu",
    "SkillbarMenu",
    "SkillTreeMenu",
    "CreditsMenu",
    "PauseMenu",
    "SaveLoadMenu",
    "RecipeBookMenu",
    "WikiMenu",
    "CollectionBookMenu",
]
