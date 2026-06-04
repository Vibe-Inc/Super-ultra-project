import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from database.GP_database import Gp_database

def seed_recipes(db=None):
    if db is None:
        db = Gp_database()
        should_close = True
    else:
        should_close = False

    db.add_shaped_recipe(
        result_item_id="potion_of_confusion",
        result_amount=1,
        grid=[
            ["moldy_bread", "apple", None],
            [None,          None,    None],
            [None,          None,    None]
        ]
    )

    if should_close:
        db.close()

if __name__ == "__main__":
    seed_recipes()