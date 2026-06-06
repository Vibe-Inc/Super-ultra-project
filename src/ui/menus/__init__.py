"""
Menu screens module for all game menu interfaces.

Provides base menu class, main menu, settings, credits, pause, skillbar,
skilltree, recipe book, wiki, collection book, arcane quests, mysterium
magnum, save/load, and smeltery workstation menus.
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
from src.ui.menus.arcane_quest_menu import ArcaneQuestMenu
from src.ui.menus.mysterium_magnum import MysteriumMagnumMenu
from src.ui.menus.intro_animation import IntroAnimation
from src.ui.menus.achievements_menu import AchievementsMenu

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
    "ArcaneQuestMenu",
    "MysteriumMagnumMenu",
    "IntroAnimation",
    "AchievementsMenu",
]