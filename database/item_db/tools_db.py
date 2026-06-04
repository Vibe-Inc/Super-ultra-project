def seed_tools(db):
    db.add_tool(
        item_id="fishing_rod",
        name="Fishing Rod",
        image_path="assets/minigames/fishing/fishing_rod-Photoroom.png",
        tool_type="fishing",
        durability=100,
        power=10,
        price=75,
        max_stack=1,
        description="A simple wooden fishing rod. Use it near water to catch fish."
    )
