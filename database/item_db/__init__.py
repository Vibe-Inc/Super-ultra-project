import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from GP_database import Gp_database
from .weapons_db import seed_weapons
from .consumables_db import seed_consumables
from .armor_db import seed_armor
from .tools_db import seed_tools
from .fish_db import seed_fish
from .materials_db import seed_materials


def seed_items():
    print("Starting database population...")
    db = Gp_database()
    seed_weapons(db)
    seed_consumables(db)
    seed_armor(db)
    seed_tools(db)
    seed_fish(db)
    seed_materials(db)
    db.close()
    print("Population complete!")


if __name__ == "__main__":
    seed_items()
