import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from GP_database import Gp_database

def seed_recipes():
    print("Starting recipe population...")
    db = Gp_database()

    db.add_shaped_recipe(
        result_item_id="potion_of_confusion",
        result_amount=1,
        grid=[
            ["moldy_bread", "apple", None],
            [None,          None,    None],
            [None,          None,    None]
        ]
    )

    db.close()
    print("Recipe population complete!")

if __name__ == "__main__":
    seed_recipes()