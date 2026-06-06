import json
import os
import pygame
from gettext import gettext as _
from src.core.logger import logger

ACHIEVEMENTS_FILE = "saves/achievements.json"

class Achievement:
    def __init__(self, id_str, name, description, icon_name="default_icon", max_progress=0):
        self.id = id_str
        self.name = name
        self.description = description
        self.icon_name = icon_name
        self.max_progress = max_progress
        self.unlocked = False
        self.progress = 0

class AchievementManager:
    """
    Manages the tracking, saving, and loading of global achievements.
    """
    def __init__(self, app):
        self.app = app
        self.achievements = {}
        self._register_default_achievements()
        self.load()

    def _register_default_achievements(self):
        # Base Achievements
        self.register(Achievement("first_step", _("The Journey Begins"), _("Start a new game.")))
        self.register(Achievement("first_blood", _("First Blood"), _("Defeat your first enemy.")))
        self.register(Achievement("wealthy", _("Wealthy"), _("Accumulate 1,000 gold."), max_progress=1000))
        self.register(Achievement("lumberjack", _("Lumberjack"), _("Chop down 10 trees."), max_progress=10))
        self.register(Achievement("master_angler", _("Master Angler"), _("Catch 10 fish."), max_progress=10))

        # Expanded Achievements
        self.register(Achievement("novice_blacksmith", _("Novice Blacksmith"), _("Craft or smelt 5 items."), max_progress=5))
        self.register(Achievement("master_crafter", _("Master Crafter"), _("Craft or smelt 50 items."), max_progress=50))
        self.register(Achievement("exterminator", _("Exterminator"), _("Defeat 50 enemies."), max_progress=50))
        self.register(Achievement("monster_hunter", _("Monster Hunter"), _("Defeat 200 enemies."), max_progress=200))
        self.register(Achievement("high_roller", _("High Roller"), _("Accumulate 10,000 gold."), max_progress=10000))
        self.register(Achievement("tycoon", _("Tycoon"), _("Accumulate 50,000 gold."), max_progress=50000))
        self.register(Achievement("card_shark", _("Card Shark"), _("Win 5 hands in gambling minigames."), max_progress=5))
        self.register(Achievement("casino_regular", _("Casino Regular"), _("Win 25 hands in gambling minigames."), max_progress=25))
        self.register(Achievement("jackpot", _("Jackpot"), _("Win any bet at the Roulette table.")))
        self.register(Achievement("deforestation", _("Deforestation"), _("Chop down 50 trees."), max_progress=50))
        self.register(Achievement("industrial_logger", _("Industrial Logger"), _("Chop down 200 trees."), max_progress=200))
        self.register(Achievement("aquatic_menace", _("Aquatic Menace"), _("Catch 50 fish."), max_progress=50))
        self.register(Achievement("legendary_angler", _("Legendary Angler"), _("Catch 150 fish."), max_progress=150))
        self.register(Achievement("thirsty", _("Thirsty"), _("Drink 10 health or buff potions."), max_progress=10))
        self.register(Achievement("potion_addict", _("Potion Addict"), _("Drink 50 potions."), max_progress=50))
        self.register(Achievement("avid_reader", _("Avid Reader"), _("Read or unlock 5 wiki/guide articles."), max_progress=5))
        self.register(Achievement("scholar", _("Scholar"), _("Read or unlock 20 wiki/guide articles."), max_progress=20))
        self.register(Achievement("lucky_catch", _("Lucky Catch"), _("Catch a Rare or Legendary fish.")))

    def register(self, achievement: Achievement):
        self.achievements[achievement.id] = achievement

    def unlock(self, achievement_id: str):
        """Unlocks an achievement if it hasn't been unlocked yet and saves the state."""
        ach = self.achievements.get(achievement_id)
        if ach and not ach.unlocked:
            ach.unlocked = True
            logger.info(f"Achievement Unlocked: {ach.name}")
            
            # Show a notification if the app has a notification system
            if hasattr(self.app, "manager"):
                state = self.app.manager.get_state()
                if state == "gameplay":
                    gameplay = self.app.manager.states.get("gameplay")
                    if gameplay and hasattr(gameplay, "hud") and hasattr(gameplay.hud, "add_notification"):
                        gameplay.hud.add_notification(f"Achievement Unlocked: {ach.name}", color=(255, 215, 0))
            
            self.save()

    def add_progress(self, achievement_id: str, amount: int, required_amount: int):
        ach = self.achievements.get(achievement_id)
        if ach and not ach.unlocked:
            ach.progress += amount
            if ach.progress >= required_amount:
                self.unlock(achievement_id)
            else:
                self.save()

    def get_all(self):
        return list(self.achievements.values())

    def save(self):
        """Save unlocked achievements to disk."""
        if not os.path.exists("saves"):
            os.makedirs("saves")
            
        data = {
            ach_id: { "unlocked": ach.unlocked, "progress": ach.progress }
            for ach_id, ach in self.achievements.items() 
            if ach.unlocked or ach.progress > 0
        }
        try:
            with open(ACHIEVEMENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save achievements: {e}")

    def load(self):
        """Load unlocked achievements from disk."""
        if os.path.exists(ACHIEVEMENTS_FILE):
            try:
                with open(ACHIEVEMENTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for ach_id, val in data.items():
                        if ach_id in self.achievements:
                            if isinstance(val, bool):
                                self.achievements[ach_id].unlocked = val
                            elif isinstance(val, dict):
                                self.achievements[ach_id].unlocked = val.get("unlocked", False)
                                self.achievements[ach_id].progress = val.get("progress", 0)
            except Exception as e:
                logger.error(f"Failed to load achievements: {e}")
