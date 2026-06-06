import json
import os
import pygame
from gettext import gettext as _
from src.core.logger import logger

ACHIEVEMENTS_FILE = "saves/achievements.json"

class Achievement:
    def __init__(self, id_str, name, description, icon_name="default_icon"):
        self.id = id_str
        self.name = name
        self.description = description
        self.icon_name = icon_name
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
        # Register standard achievements
        self.register(Achievement("first_step", _("The Journey Begins"), _("Start a new game.")))
        self.register(Achievement("first_blood", _("First Blood"), _("Defeat your first enemy.")))
        self.register(Achievement("wealthy", _("Wealthy"), _("Accumulate 1,000 gold.")))
        self.register(Achievement("lumberjack", _("Lumberjack"), _("Chop down 10 trees.")))
        self.register(Achievement("master_angler", _("Master Angler"), _("Catch 10 fish.")))

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
