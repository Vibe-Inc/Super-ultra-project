def seed_tools(db):
    db.add_tool(
        item_id="fishing_rod",
        name="Fishing Rod",
        image_path="assets/minigames/fishing/FishingRod.png",
        tool_type="fishing",
        durability=100,
        power=10,
        price=75,
        max_stack=1,
        description="A simple wooden fishing rod. Use it near water to catch fish."
    )

    db.add_tool(
        item_id="wooden_pickaxe",
        name="Wooden Pickaxe",
        image_path="assets/items/tools/wooden_pickaxe.png",
        tool_type="pickaxe",
        durability=30,
        power=1,
        price=15,
        max_stack=1,
        description="A flimsy pickaxe carved from wood. Better than fists when mining stone.",
        gather_type="stone",
        gather_yield_min=1,
        gather_yield_max=1,
    )

    db.add_tool(
        item_id="wooden_axe",
        name="Wooden Axe",
        image_path="assets/items/tools/wooden_axe.png",
        tool_type="axe",
        durability=30,
        power=1,
        price=15,
        max_stack=1,
        description="A rough wooden axe. Useful for chopping down trees.",
        gather_type="wood",
        gather_yield_min=1,
        gather_yield_max=2,
    )

    db.add_tool(
        item_id="stone_axe",
        name="Stone Axe",
        image_path="assets/items/tools/stone_axe.png",
        tool_type="axe",
        durability=50,
        power=2,
        price=40,
        max_stack=1,
        description="A crude axe fitted with a chipped stone head. Useful for chopping wood.",
        gather_type="wood",
        gather_yield_min=1,
        gather_yield_max=2,
    )

    db.add_tool(
        item_id="iron_axe",
        name="Iron Axe",
        image_path="assets/items/tools/axe.png",
        tool_type="axe",
        durability=120,
        power=4,
        price=180,
        max_stack=1,
        description="A sturdy axe with a forged iron head. Chops wood much faster than a stone axe.",
        gather_type="wood",
        gather_yield_min=2,
        gather_yield_max=4,
    )

    db.add_tool(
        item_id="stone_pickaxe",
        name="Stone Pickaxe",
        image_path="assets/items/tools/stone_pickaxe.png",
        tool_type="pickaxe",
        durability=50,
        power=2,
        price=40,
        max_stack=1,
        description="A rough pickaxe tipped with stone. Slow but gets the job done.",
        gather_type="stone",
        gather_yield_min=1,
        gather_yield_max=2,
    )

    db.add_tool(
        item_id="iron_pickaxe",
        name="Iron Pickaxe",
        image_path="assets/items/tools/pickaxe.png",
        tool_type="pickaxe",
        durability=120,
        power=4,
        price=180,
        max_stack=1,
        description="A solid iron pickaxe. Mines stone and ore efficiently.",
        gather_type="stone",
        gather_yield_min=2,
        gather_yield_max=4,
    )

    db.add_tool(
        item_id="stone_hammer",
        name="Stone Hammer",
        image_path="assets/items/tools/hammer.png",
        tool_type="hammer",
        durability=60,
        power=2,
        price=55,
        max_stack=1,
        description="A crude hammer with a chipped stone head. Useful for breaking rocks and ore veins.",
        gather_type="ore",
        gather_yield_min=1,
        gather_yield_max=2,
    )

    db.add_tool(
        item_id="iron_hammer",
        name="Iron Hammer",
        image_path="assets/items/tools/hammer.png",
        tool_type="hammer",
        durability=140,
        power=5,
        price=210,
        max_stack=1,
        description="A heavy iron hammer that crushes rock and cracks open ore veins with ease.",
        gather_type="ore",
        gather_yield_min=2,
        gather_yield_max=4,
    )
