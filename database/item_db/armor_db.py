def seed_armor(db):
    # Durability values scale roughly with the defense tier:
    #   * light cloth / leather accessories wear out fastest,
    #   * iron-grade sits in the middle,
    #   * steel / silver tier pieces are the most durable.
    # The numbers are intentionally generous so normal play doesn't shred
    # armor in a single encounter, but a chest hit on steel still has
    # enough hits to feel meaningful (a few dozen rough fights).
    db.add_armor(
        item_id="iron_helmet", name="Iron Helmet", image_path="assets/items/armor/iron_helmet.png",
        slot_type="helmet", defense_value=5, price=120,
        description="A sturdy iron helmet that protects the head.",
        durability=240,
    )
    db.add_armor(
        item_id="iron_chestplate", name="Iron Chestplate", image_path="assets/items/armor/iron_chestplate.png",
        slot_type="chestplate", defense_value=12, price=280,
        description="Heavy iron chestplate offering solid protection.",
        durability=400,
    )
    db.add_armor(
        item_id="iron_leggings", name="Iron Leggings", image_path="assets/items/armor/iron_leggings.png",
        slot_type="leggings", defense_value=8, price=200,
        description="Iron leg guards that balance mobility and defense.",
        durability=320,
    )
    db.add_armor(
        item_id="iron_boots", name="Iron Boots", image_path="assets/items/armor/iron_boots.png",
        slot_type="boots", defense_value=4, price=90,
        description="Reinforced boots to protect your feet.",
        durability=200,
    )
    db.add_armor(
        item_id="steel_helmet", name="Steel Helmet", image_path="assets/items/armor/steel_helmet.png",
        slot_type="helmet", defense_value=8, price=240,
        description="A polished steel helmet with a visor.",
        durability=360,
    )
    db.add_armor(
        item_id="steel_chestplate", name="Steel Chestplate", image_path="assets/items/armor/steel_chestplate.png",
        slot_type="chestplate", defense_value=18, price=480,
        description="Masterfully crafted steel chestplate.",
        durability=600,
    )
    db.add_armor(
        item_id="steel_leggings", name="Steel Leggings", image_path="assets/items/armor/steel_leggings.png",
        slot_type="leggings", defense_value=12, price=340,
        description="Steel leg guards forged by a skilled blacksmith.",
        durability=480,
    )
    db.add_armor(
        item_id="steel_boots", name="Steel Boots", image_path="assets/items/armor/steel_boots.png",
        slot_type="boots", defense_value=6, price=160,
        description="Sturdy steel boots with reinforced soles.",
        durability=300,
    )
    db.add_armor(
        item_id="defense_charm", name="Defense Charm", image_path="assets/items/accessories/defense_charm.png",
        slot_type="charm", defense_value=3, price=150,
        description="A small charm imbued with protective magic.",
        durability=160,
    )
    db.add_armor(
        item_id="leather_gloves", name="Leather Gloves", image_path="assets/items/armor/leather_gloves.png",
        slot_type="gloves", defense_value=2, price=60,
        description="Simple leather gloves offering minimal protection.",
        durability=120,
    )
    db.add_armor(
        item_id="iron_ring", name="Iron Ring", image_path="assets/items/accessories/iron_ring.png",
        slot_type="ring", defense_value=1, price=80,
        description="A plain iron ring with a faint protective aura.",
        durability=140,
    )
    db.add_armor(
        item_id="leather_belt", name="Leather Belt", image_path="assets/items/armor/leather_belt.png",
        slot_type="belt", defense_value=2, price=50,
        description="A sturdy leather belt with a small steel buckle.",
        durability=120,
    )
    db.add_armor(
        item_id="steel_ring", name="Steel Ring", image_path="assets/items/accessories/steel_ring.png",
        slot_type="ring", defense_value=3, price=180,
        description="A finely crafted steel ring etched with runes.",
        durability=220,
    )
    db.add_armor(
        item_id="iron_gloves", name="Iron Gloves", image_path="assets/items/armor/iron_gloves.png",
        slot_type="gloves", defense_value=5, price=140,
        description="Iron gloves offering good hand protection.",
        durability=220,
    )
    db.add_armor(
        item_id="silver_charm", name="Silver Charm", image_path="assets/items/accessories/silver_charm.png",
        slot_type="charm", defense_value=6, price=300,
        description="A gleaming silver charm radiating pure protective energy.",
        durability=260,
    )

