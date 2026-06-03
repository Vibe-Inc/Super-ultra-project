WIP_TEXTURE = "assets/WIP_TEXTURE.jpg"


def seed_armor(db):
    db.add_armor(
        item_id="iron_helmet", name="Iron Helmet", image_path=WIP_TEXTURE,
        slot_type="helmet", defense_value=5, price=120,
        description="A sturdy iron helmet that protects the head."
    )
    db.add_armor(
        item_id="iron_chestplate", name="Iron Chestplate", image_path=WIP_TEXTURE,
        slot_type="chestplate", defense_value=12, price=280,
        description="Heavy iron chestplate offering solid protection."
    )
    db.add_armor(
        item_id="iron_leggings", name="Iron Leggings", image_path=WIP_TEXTURE,
        slot_type="leggings", defense_value=8, price=200,
        description="Iron leg guards that balance mobility and defense."
    )
    db.add_armor(
        item_id="iron_boots", name="Iron Boots", image_path=WIP_TEXTURE,
        slot_type="boots", defense_value=4, price=90,
        description="Reinforced boots to protect your feet."
    )
    db.add_armor(
        item_id="steel_helmet", name="Steel Helmet", image_path=WIP_TEXTURE,
        slot_type="helmet", defense_value=8, price=240,
        description="A polished steel helmet with a visor."
    )
    db.add_armor(
        item_id="steel_chestplate", name="Steel Chestplate", image_path=WIP_TEXTURE,
        slot_type="chestplate", defense_value=18, price=480,
        description="Masterfully crafted steel chestplate."
    )
    db.add_armor(
        item_id="steel_leggings", name="Steel Leggings", image_path=WIP_TEXTURE,
        slot_type="leggings", defense_value=12, price=340,
        description="Steel leg guards forged by a skilled blacksmith."
    )
    db.add_armor(
        item_id="steel_boots", name="Steel Boots", image_path=WIP_TEXTURE,
        slot_type="boots", defense_value=6, price=160,
        description="Sturdy steel boots with reinforced soles."
    )
    db.add_armor(
        item_id="defense_charm", name="Defense Charm", image_path=WIP_TEXTURE,
        slot_type="charm", defense_value=3, price=150,
        description="A small charm imbued with protective magic."
    )
    db.add_armor(
        item_id="leather_gloves", name="Leather Gloves", image_path=WIP_TEXTURE,
        slot_type="gloves", defense_value=2, price=60,
        description="Simple leather gloves offering minimal protection."
    )
    db.add_armor(
        item_id="iron_ring", name="Iron Ring", image_path=WIP_TEXTURE,
        slot_type="ring", defense_value=1, price=80,
        description="A plain iron ring with a faint protective aura."
    )
    db.add_armor(
        item_id="leather_belt", name="Leather Belt", image_path=WIP_TEXTURE,
        slot_type="belt", defense_value=2, price=50,
        description="A sturdy leather belt with a small steel buckle."
    )
    db.add_armor(
        item_id="steel_ring", name="Steel Ring", image_path=WIP_TEXTURE,
        slot_type="ring", defense_value=3, price=180,
        description="A finely crafted steel ring etched with runes."
    )
    db.add_armor(
        item_id="chain_gloves", name="Chain Gloves", image_path=WIP_TEXTURE,
        slot_type="gloves", defense_value=5, price=140,
        description="Chainmail gloves offering good hand protection."
    )
    db.add_armor(
        item_id="silver_charm", name="Silver Charm", image_path=WIP_TEXTURE,
        slot_type="charm", defense_value=6, price=300,
        description="A gleaming silver charm radiating pure protective energy."
    )
    db.add_armor(
        item_id="studded_belt", name="Studded Belt", image_path=WIP_TEXTURE,
        slot_type="belt", defense_value=4, price=110,
        description="A thick belt reinforced with metal studs."
    )
