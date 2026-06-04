def seed_resources(db):
    db.add_generic_item(
        item_id="wood",
        item_type="resource",
        name="Wood",
        image_path="assets/items/resources/wood.png",
        price=2,
        max_stack=64,
        description="A bundle of rough-cut wood. Used for crafting and building."
    )
    db.add_generic_item(
        item_id="stone",
        item_type="resource",
        name="Stone",
        image_path="assets/items/resources/stone.png",
        price=3,
        max_stack=64,
        description="A chunk of quarried stone. Useful for construction."
    )
    db.add_generic_item(
        item_id="iron_ore",
        item_type="resource",
        name="Iron Ore",
        image_path="assets/items/resources/iron_ore.png",
        price=8,
        max_stack=64,
        description="Raw iron ore, straight from the rock. Smelt it into ingots."
    )
