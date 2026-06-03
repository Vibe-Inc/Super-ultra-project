def seed_weapons(db):
    # ------------------ Melee weapons ------------------
    db.add_weapon(
        item_id="dull_sword",
        name="Dull Sword",
        image_path="assets/items/weapons/swords/dull_sword.png",
        weapon_class="melee",
        damage=20, durability=50, cone_degrees=120.0, price=50,
        description="A worn-out sword with a dull blade. Thats about it."
    )

    db.add_weapon(
        item_id="iron_sword", name="Iron Sword", image_path="assets/items/weapons/swords/iron_sword.png",
        weapon_class="melee", damage=35, durability=120, range_val=75,
        cone_degrees=110.0, cooldown=450, price=180,
        description="A sturdy iron sword. Reliable and well-balanced."
    )
    db.add_weapon(
        item_id="steel_sword", name="Steel Sword", image_path="assets/items/weapons/swords/steel_sword.png",
        weapon_class="melee", damage=48, durability=180, range_val=80,
        cone_degrees=115.0, cooldown=480, price=320,
        description="A polished steel blade forged by a skilled blacksmith."
    )
    db.add_weapon(
        item_id="battle_axe", name="Battle Axe", image_path="assets/items/weapons/battle_axe.png",
        weapon_class="melee", damage=62, durability=200, range_val=85,
        cone_degrees=130.0, cooldown=850, price=420,
        description="A heavy two-handed axe that cleaves through armor.",
        combat_style="axe"
    )
    db.add_weapon(
        item_id="war_hammer", name="War Hammer", image_path="assets/items/weapons/war_hammer.png",
        weapon_class="melee", damage=75, durability=260, range_val=70,
        cone_degrees=100.0, cooldown=1100, price=550,
        description="An enormous hammer that crushes bones and shields alike.",
        combat_style="war_hammer"
    )
    db.add_weapon(
        item_id="mace", name="Mace", image_path="assets/items/weapons/mace.png",
        weapon_class="melee", damage=40, durability=140, range_val=70,
        cone_degrees=110.0, cooldown=520, price=230,
        description="A spiked mace effective against armored foes.",
        combat_style="mace"
    )
    db.add_weapon(
        item_id="spear", name="Spear", image_path="assets/items/weapons/spear.png",
        weapon_class="melee", damage=28, durability=150, range_val=110,
        cone_degrees=60.0, cooldown=600, price=160,
        description="A long wooden spear with a steel tip. Great reach.",
        combat_style="spear"
    )
    # ------------------ Ranged weapons ------------------
    db.add_weapon(
        item_id="wooden_bow",
        name="Wooden Bow",
        image_path="assets/items/weapons/bows/wooden_bow.png",
        weapon_class="ranged",
        damage=14, durability=40, range_val=520, projectile_speed=900, cooldown=650, spread_degrees=4.0, price=75,
        description="A simple bow made of wood. Lightweight but reliable."
    )
    db.add_weapon(
        item_id="hunting_bow", name="Hunting Bow", image_path="assets/items/weapons/bows/hunting_bow.png",
        weapon_class="ranged", damage=22, durability=80, range_val=600,
        projectile_speed=1000, cooldown=700, spread_degrees=2.5, price=140,
        description="A reinforced bow favored by experienced hunters."
    )
    db.add_weapon(
        item_id="longbow", name="Longbow", image_path="assets/items/weapons/bows/longbow.png",
        weapon_class="ranged", damage=30, durability=100, range_val=780,
        projectile_speed=1100, cooldown=820, spread_degrees=1.8, price=260,
        description="A tall longbow that fires arrows with deadly accuracy."
    )
    db.add_weapon(
        item_id="crossbow", name="Crossbow", image_path="assets/items/weapons/crossbow.png",
        weapon_class="ranged", damage=45, durability=90, range_val=640,
        projectile_speed=1300, cooldown=1100, spread_degrees=1.0, price=380,
        description="A mechanical crossbow that bolts through shields."
    )
    db.add_weapon(
        item_id="throwing_dagger", name="Throwing Dagger", image_path="assets/items/weapons/throwing_dagger.png",
        weapon_class="ranged", damage=10, durability=60, range_val=380,
        projectile_speed=1400, cooldown=320, spread_degrees=6.0, price=90,
        description="Light daggers balanced for throwing. Quick to wield."
    )
