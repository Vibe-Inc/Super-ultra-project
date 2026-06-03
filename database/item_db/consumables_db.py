WIP_TEXTURE = "assets/WIP_TEXTURE.jpg"


def seed_consumables(db):
    # ------------------ Food / consumables ------------------
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
    # art assets are created.
    # ============================================================

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
        description="A swift potion that makes the drinker much faster and attack quicker.",
        effects=[
            {"type": "haste", "duration": 15, "cooldown_multiplier": 0.7, "speed_multiplier": 1.3}
        ]
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
        item_id="elixir_of_life", item_type="potion", name="Elixir of Life",
        image_path=WIP_TEXTURE, heal_amount=999, max_stack=1, price=2000,
        description="A legendary elixir that fully restores the drinker.",
        effects=[{"type": "regeneration", "duration": 15, "amount_per_sec": 60}]
    )

    # ------------------ New buff / utility consumables ------------------
    db.add_consumable(
        item_id="potion_of_strength", item_type="potion", name="Potion of Strength",
        image_path=WIP_TEXTURE, heal_amount=0, max_stack=1, price=110,
        description="Increases melee damage for a short time.",
        effects=[{"type": "strength", "duration": 30, "damage_bonus": 12}]
    )
    db.add_consumable(
        item_id="potion_of_haste", item_type="potion", name="Potion of Haste",
        image_path=WIP_TEXTURE, heal_amount=0, max_stack=1, price=130,
        description="Massively boosts attack and movement speed.",
        effects=[
            {"type": "haste", "duration": 20, "cooldown_multiplier": 0.5, "speed_multiplier": 1.5}
        ]
    )
    db.add_consumable(
        item_id="potion_of_shield", item_type="potion", name="Potion of Shield",
        image_path=WIP_TEXTURE, heal_amount=0, max_stack=1, price=100,
        description="Creates a magical shield that absorbs incoming damage.",
        effects=[{"type": "shield", "duration": 30, "absorb_amount": 80}]
    )
    db.add_consumable(
        item_id="potion_of_lethargy", item_type="potion", name="Potion of Lethargy",
        image_path=WIP_TEXTURE, heal_amount=0, max_stack=1, price=70,
        description="A calming draught that saps strength and slows attacks.",
        effects=[
            {"type": "lethargy", "duration": 20, "speed_multiplier": 0.7, "cooldown_multiplier": 1.4}
        ]
    )
