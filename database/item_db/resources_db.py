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
    db.add_generic_item(
        item_id="stick",
        item_type="resource",
        name="Stick",
        image_path="assets/items/resources/stick.png",
        price=1,
        max_stack=64,
        description="A thin wooden stick. A basic crafting component for tools and weapons."
    )
    db.add_generic_item(
        item_id="flint",
        item_type="resource",
        name="Flint",
        image_path="assets/items/resources/flint.png",
        price=4,
        max_stack=64,
        description="A sharp-edged stone. Useful for starting fires and crafting tools."
    )
