from src.core.logger import logger

SECTION_ARTICLE_MAP = {
    "bestiary": {
        "the brute": 0, "the venomous": 1, "the arcanist": 2,
        "the trickster": 3, "the bomber": 4, "the stalker": 5,
        "the skirmisher": 6, "the guardian": 7,
    },
    "magic": {
        "fireball": 0, "flame shield": 1, "frost nova": 2,
        "ice armor": 3, "glacial cascade": 4, "chain lightning": 5,
        "thunderstrike": 6, "entangling roots": 7, "summon spirit": 8,
        "shadow step": 9, "dark pact": 10, "arcane missiles": 11,
        "mystic barrier": 12, "berserker's rage": 13, "chrono shift": 14,
        "dash": 15,
    },
    "effects": {
        "boon: regeneration": 0, "bane: poison": 1, "bane: burn": 2,
        "bane: confusion": 3, "bane: dizziness": 4, "bane: slow": 5,
        "bane: freeze & root": 6,
    },
    "guide": {
        "1. movement & navigation": 0, "2. combat basics": 1,
        "3. skills & hotbar": 2, "4. inventory & items": 3,
        "5. crafting & recipes": 4, "6. leveling & experience": 5,
        "7. day & night cycle": 6, "8. enemies & threat assessment": 7,
        "9. respeccing & strategy": 8, "10. final words": 9,
    },
}


class ArticleUnlockTracker:
    def __init__(self):
        self.seen_articles: set[tuple[str, str]] = set()

    def article_exists(self, section: str, title: str) -> bool:
        mapping = SECTION_ARTICLE_MAP.get(section)
        if mapping is None:
            return False
        return title.strip().lower() in mapping

    def already_seen(self, section: str, title: str) -> bool:
        return (section, title.strip().lower()) in self.seen_articles

    def try_open(self, app, section: str, title: str) -> bool:
        title_lower = title.strip().lower()
        mapping = SECTION_ARTICLE_MAP.get(section)
        if mapping is None or title_lower not in mapping:
            logger.debug(f"ArticleUnlockTracker: no article '{title}' in section '{section}'")
            return False
        if (section, title_lower) in self.seen_articles:
            return False
        idx = mapping[title_lower]
        self.seen_articles.add((section, title_lower))
        wiki = app.manager.states.get("wiki")
        if wiki is None:
            logger.warning("ArticleUnlockTracker: wiki state not found")
            return False
        wiki._page = section
        wiki._sub_page = idx
        wiki._show_toc = False
        wiki._transition_progress = 0.0
        wiki._page_enter_time = __import__("pygame").time.get_ticks()
        wiki._emit_particles(wiki._theme())
        app.manager.set_state("wiki")
        logger.info(f"ArticleUnlockTracker: opened '{title}' in section '{section}'")
        return True

    def mark_seen(self, section: str, title: str):
        title_lower = title.strip().lower()
        mapping = SECTION_ARTICLE_MAP.get(section)
        if mapping is not None and title_lower in mapping:
            self.seen_articles.add((section, title_lower))

    def serialize(self) -> list:
        return [list(pair) for pair in sorted(self.seen_articles)]

    def deserialize(self, data: list):
        self.seen_articles = {tuple(pair) for pair in data}
