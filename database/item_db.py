import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from GP_database import Gp_database

# Path to the global "Work In Progress" texture. New placeholder items
# that don't have bespoke art yet reference this file so they still
# render in-game until proper sprites are created.
WIP_TEXTURE = "assets/WIP_TEXTURE.jpg"

def seed_items():
    """
    Execute the database population process.

    This function connects to the Gp_database, calls insertion methods for various item
    categories, and closes the connection once complete. It handles weapons with
    combat statistics, food with minor healing or damage effects, and potions
    with complex dynamic effects.
    """
    print("Starting database population...")
    db = Gp_database()

    # ============================================================
    # Original items (have unique art assets).
    # ============================================================
    db.add_weapon(
        item_id="dull_sword",
        name="Dull Sword",
        image_path="assets/items/weapons/swords/dull_sword.png",
        weapon_class="melee",
        damage=20, durability=50, cone_degrees=120.0, price=50,
        description="A worn-out sword with a dull blade. Thats about it."
    )

    db.add_weapon(
        item_id="wooden_bow",
        name="Wooden Bow",
        image_path="assets/items/weapons/bows/wooden_bow.png",
        weapon_class="ranged",
        damage=14, durability=40, range_val=520, projectile_speed=900, cooldown=650, spread_degrees=4.0, price=75,
        description="A simple bow made of wood. Lightweight but reliable."
    )

    db.add_consumable(
        item_id="apple",
        item_type="food",
        name="Apple",
        image_path="assets/items/consumables/food/apple.png",
        heal_amount=10,
        max_stack=64,
        price=5,
        description="An apple.",
        effects=[{"type": "regeneration", "duration": 5, "amount_per_sec": 2}]
    )

    db.add_consumable(
        item_id="moldy_bread",
        item_type="food",
        name="Moldy Bread",
        image_path="assets/items/consumables/food/moldy_bread.png",
        heal_amount=-5,
        max_stack=64,
        price=2,
        description="A piece of bread that has gone bad.",
        effects=[{"type": "poison", "duration": 5, "damage_per_sec": 2}]
    )

    db.add_consumable(
        item_id="small_health_potion",
        item_type="potion",
        name="Small Health Potion",
        image_path="assets/items/consumables/potion/small_health_potion.png",
        heal_amount=30,
        max_stack=1,
        price=30,
        description="A small potion that restores health.",
        effects=[{"type": "regeneration", "duration": 3, "amount_per_sec": 10}]
    )

    db.add_consumable(
        item_id="large_health_potion",
        item_type="potion",
        name="Large Health Potion",
        image_path="assets/items/consumables/potion/large_health_potion.png",
        heal_amount=70,
        max_stack=1,
        price=60,
        description="A large potion that restores a significant amount of health.",
        effects=[{"type": "regeneration", "duration": 5, "amount_per_sec": 14}]
    )

    db.add_consumable(
        item_id="potion_of_confusion",
        item_type="potion",
        name="Potion of Confusion",
        image_path="assets/items/consumables/potion/potion_of_confusion.png",
        heal_amount=0,
        max_stack=1,
        price=25,
        description="A mix oh herbs and spices that causes confusion.",
        effects=[
            {"type": "confusion", "duration": 30},
            {"type": "dizziness", "duration": 30}
        ]
    )

    # ============================================================
    # New placeholder items below use the WIP_TEXTURE until proper
    # art assets are created. They cover a variety of categories so
    # the world can be populated with a richer set of content.
    # ============================================================

    # ------------------ Melee weapons ------------------
    db.add_weapon(
        item_id="iron_sword", name="Iron Sword", image_path=WIP_TEXTURE,
        weapon_class="melee", damage=35, durability=120, range_val=75,
        cone_degrees=110.0, cooldown=450, price=180,
        description="A sturdy iron sword. Reliable and well-balanced."
    )
    db.add_weapon(
        item_id="steel_sword", name="Steel Sword", image_path=WIP_TEXTURE,
        weapon_class="melee", damage=48, durability=180, range_val=80,
        cone_degrees=115.0, cooldown=480, price=320,
        description="A polished steel blade forged by a skilled blacksmith."
    )
    db.add_weapon(
        item_id="rusty_dagger", name="Rusty Dagger", image_path=WIP_TEXTURE,
        weapon_class="melee", damage=12, durability=20, range_val=40,
        cone_degrees=80.0, cooldown=220, price=15,
        description="A small, rusted dagger. Quick, but fragile."
    )
    db.add_weapon(
        item_id="battle_axe", name="Battle Axe", image_path=WIP_TEXTURE,
        weapon_class="melee", damage=62, durability=200, range_val=85,
        cone_degrees=130.0, cooldown=850, price=420,
        description="A heavy two-handed axe that cleaves through armor."
    )
    db.add_weapon(
        item_id="war_hammer", name="War Hammer", image_path=WIP_TEXTURE,
        weapon_class="melee", damage=75, durability=260, range_val=70,
        cone_degrees=100.0, cooldown=1100, price=550,
        description="An enormous hammer that crushes bones and shields alike."
    )
    db.add_weapon(
        item_id="mace", name="Mace", image_path=WIP_TEXTURE,
        weapon_class="melee", damage=40, durability=140, range_val=70,
        cone_degrees=110.0, cooldown=520, price=230,
        description="A spiked mace effective against armored foes."
    )
    db.add_weapon(
        item_id="spear", name="Spear", image_path=WIP_TEXTURE,
        weapon_class="melee", damage=28, durability=150, range_val=110,
        cone_degrees=60.0, cooldown=600, price=160,
        description="A long wooden spear with a steel tip. Great reach."
    )
    db.add_weapon(
        item_id="flaming_sword", name="Flaming Sword", image_path=WIP_TEXTURE,
        weapon_class="melee", damage=55, durability=160, range_val=80,
        cone_degrees=120.0, cooldown=500, price=600,
        description="A magical blade wreathed in eternal flame."
    )

    # ------------------ Ranged weapons ------------------
    db.add_weapon(
        item_id="hunting_bow", name="Hunting Bow", image_path=WIP_TEXTURE,
        weapon_class="ranged", damage=22, durability=80, range_val=600,
        projectile_speed=1000, cooldown=700, spread_degrees=2.5, price=140,
        description="A reinforced bow favored by experienced hunters."
    )
    db.add_weapon(
        item_id="longbow", name="Longbow", image_path=WIP_TEXTURE,
        weapon_class="ranged", damage=30, durability=100, range_val=780,
        projectile_speed=1100, cooldown=820, spread_degrees=1.8, price=260,
        description="A tall longbow that fires arrows with deadly accuracy."
    )
    db.add_weapon(
        item_id="crossbow", name="Crossbow", image_path=WIP_TEXTURE,
        weapon_class="ranged", damage=45, durability=90, range_val=640,
        projectile_speed=1300, cooldown=1100, spread_degrees=1.0, price=380,
        description="A mechanical crossbow that bolts through shields."
    )
    db.add_weapon(
        item_id="throwing_dagger", name="Throwing Dagger", image_path=WIP_TEXTURE,
        weapon_class="ranged", damage=10, durability=60, range_val=380,
        projectile_speed=1400, cooldown=320, spread_degrees=6.0, price=90,
        description="Light daggers balanced for throwing. Quick to wield."
    )

    # ------------------ Food / consumables ------------------
    db.add_consumable(
        item_id="bread", item_type="food", name="Bread", image_path=WIP_TEXTURE,
        heal_amount=15, max_stack=32, price=8,
        description="A loaf of fresh bread. Restores a bit of health.",
        effects=[{"type": "regeneration", "duration": 4, "amount_per_sec": 3}]
    )
    db.add_consumable(
        item_id="cheese", item_type="food", name="Cheese", image_path=WIP_TEXTURE,
        heal_amount=20, max_stack=16, price=12,
        description="Aged cheese, rich in flavor and calories.",
        effects=[{"type": "regeneration", "duration": 5, "amount_per_sec": 4}]
    )
    db.add_consumable(
        item_id="cooked_meat", item_type="food", name="Cooked Meat", image_path=WIP_TEXTURE,
        heal_amount=35, max_stack=16, price=22,
        description="A juicy piece of cooked meat. Very satisfying.",
        effects=[{"type": "regeneration", "duration": 6, "amount_per_sec": 6}]
    )
    db.add_consumable(
        item_id="fish", item_type="food", name="Fish", image_path=WIP_TEXTURE,
        heal_amount=22, max_stack=16, price=14,
        description="A freshly caught fish. Tasty when cooked.",
        effects=[{"type": "regeneration", "duration": 5, "amount_per_sec": 4}]
    )
    db.add_consumable(
        item_id="berry", item_type="food", name="Berry", image_path=WIP_TEXTURE,
        heal_amount=5, max_stack=64, price=3,
        description="A small handful of sweet forest berries.",
        effects=[{"type": "regeneration", "duration": 3, "amount_per_sec": 2}]
    )
    db.add_consumable(
        item_id="mushroom", item_type="food", name="Mushroom", image_path=WIP_TEXTURE,
        heal_amount=8, max_stack=32, price=6,
        description="An edible mushroom found in damp forests.",
        effects=[{"type": "regeneration", "duration": 4, "amount_per_sec": 2}]
    )
    db.add_consumable(
        item_id="spicy_pepper", item_type="food", name="Spicy Pepper", image_path=WIP_TEXTURE,
        heal_amount=-3, max_stack=32, price=5,
        description="An extremely spicy pepper. Burns on the way down.",
        effects=[{"type": "burn", "duration": 6, "damage_per_sec": 3}]
    )
    db.add_consumable(
        item_id="rotten_fish", item_type="food", name="Rotten Fish", image_path=WIP_TEXTURE,
        heal_amount=-8, max_stack=16, price=1,
        description="A foul-smelling fish. Eating it is a terrible idea.",
        effects=[{"type": "poison", "duration": 8, "damage_per_sec": 3}]
    )
    db.add_consumable(
        item_id="honey", item_type="food", name="Honey", image_path=WIP_TEXTURE,
        heal_amount=12, max_stack=16, price=10,
        description="Sweet golden honey harvested from wild bees.",
        effects=[{"type": "regeneration", "duration": 5, "amount_per_sec": 3}]
    )

    # ------------------ Potions ------------------
    db.add_consumable(
        item_id="medium_health_potion", item_type="potion", name="Medium Health Potion",
        image_path=WIP_TEXTURE, heal_amount=50, max_stack=1, price=45,
        description="A medium-sized potion that restores a fair amount of health.",
        effects=[{"type": "regeneration", "duration": 4, "amount_per_sec": 12}]
    )
    db.add_consumable(
        item_id="greater_health_potion", item_type="potion", name="Greater Health Potion",
        image_path=WIP_TEXTURE, heal_amount=120, max_stack=1, price=120,
        description="A potent potion brewed by master alchemists.",
        effects=[{"type": "regeneration", "duration": 6, "amount_per_sec": 20}]
    )
    db.add_consumable(
        item_id="ultimate_health_potion", item_type="potion", name="Ultimate Health Potion",
        image_path=WIP_TEXTURE, heal_amount=250, max_stack=1, price=300,
        description="An incredibly powerful potion that almost fully restores health.",
        effects=[{"type": "regeneration", "duration": 8, "amount_per_sec": 30}]
    )
    db.add_consumable(
        item_id="potion_of_speed", item_type="potion", name="Potion of Speed",
        image_path=WIP_TEXTURE, heal_amount=0, max_stack=1, price=80,
        description="A swift potion that makes the drinker much faster for a short time.",
        effects=[{"type": "regeneration", "duration": 2, "amount_per_sec": 1}]
    )
    db.add_consumable(
        item_id="potion_of_slow", item_type="potion", name="Potion of Slowness",
        image_path=WIP_TEXTURE, heal_amount=0, max_stack=1, price=60,
        description="A viscous brew that slows down whoever drinks it.",
        effects=[{"type": "slow", "duration": 20, "speed_multiplier": 0.5}]
    )
    db.add_consumable(
        item_id="potion_of_poison", item_type="potion", name="Potion of Poison",
        image_path=WIP_TEXTURE, heal_amount=-10, max_stack=1, price=40,
        description="A toxic green liquid. Drinking it poisons you.",
        effects=[{"type": "poison", "duration": 12, "damage_per_sec": 4}]
    )
    db.add_consumable(
        item_id="potion_of_burning", item_type="potion", name="Potion of Burning",
        image_path=WIP_TEXTURE, heal_amount=-15, max_stack=1, price=55,
        description="A boiling flask of liquid flame. Sets the drinker on fire.",
        effects=[{"type": "burn", "duration": 10, "damage_per_sec": 5}]
    )
    db.add_consumable(
        item_id="potion_of_dizziness", item_type="potion", name="Potion of Dizziness",
        image_path=WIP_TEXTURE, heal_amount=0, max_stack=1, price=30,
        description="A swirling draught that makes the world spin.",
        effects=[{"type": "dizziness", "duration": 25}]
    )
    db.add_consumable(
        item_id="mana_potion", item_type="potion", name="Mana Potion",
        image_path=WIP_TEXTURE, heal_amount=0, max_stack=1, price=70,
        description="A glowing blue potion that restores magical energy.",
        effects=[{"type": "regeneration", "duration": 5, "amount_per_sec": 8}]
    )
    db.add_consumable(
        item_id="elixir_of_life", item_type="potion", name="Elixir of Life",
        image_path=WIP_TEXTURE, heal_amount=999, max_stack=1, price=2000,
        description="A legendary elixir said to fully restore the drinker.",
        effects=[{"type": "regeneration", "duration": 15, "amount_per_sec": 60}]
    )

    db.close()
    print("Population complete!")

if __name__ == "__main__":
    seed_items()
