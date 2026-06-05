def seed_fish(db):
    """Seed all fish items into the database.

    Each call uses ``db.add_fish()`` which inserts into both the
    ``items`` and ``fish`` tables automatically.
    """
    db.add_fish(
        item_id="fish_anchovy", name="Anchovy",
        image_path="assets/minigames/fishing/fish/Anchovy.png",
        rarity="common", difficulty=0.15, speed=0.7,
        spawn_weight=80, base_price=5,
        description="A tiny silver fish that schools in shallow waters. Easy to catch, hard to keep on the hook."
    )
    db.add_fish(
        item_id="fish_goldfish", name="Goldfish",
        image_path="assets/minigames/fishing/fish/Goldfish.png",
        rarity="common", difficulty=0.20, speed=0.8,
        spawn_weight=70, base_price=8,
        description="A bright orange fish with shimmering scales. Common near riverbanks."
    )
    db.add_fish(
        item_id="fish_clownfish", name="Clownfish",
        image_path="assets/minigames/fishing/fish/Clownfish.png",
        rarity="common", difficulty=0.30, speed=1.0,
        spawn_weight=60, base_price=12,
        description="A small, striped fish known for darting between rocks and coral."
    )
    db.add_fish(
        item_id="fish_bass", name="Bass",
        image_path="assets/minigames/fishing/fish/Bass.png",
        rarity="common", difficulty=0.35, speed=1.1,
        spawn_weight=50, base_price=15,
        description="A sturdy freshwater fish. A reliable catch for any angler."
    )
    db.add_fish(
        item_id="fish_rainbow_trout", name="Rainbow Trout",
        image_path="assets/minigames/fishing/fish/Rainbow Trout.png",
        rarity="uncommon", difficulty=0.45, speed=1.3,
        spawn_weight=35, base_price=25,
        description="A flash of iridescent color beneath the surface. Fast and slippery."
    )
    db.add_fish(
        item_id="fish_catfish", name="Catfish",
        image_path="assets/minigames/fishing/fish/Catfish.png",
        rarity="uncommon", difficulty=0.50, speed=1.0,
        spawn_weight=30, base_price=30,
        description="A bottom-dwelling fish with long whiskers. Slow but deceptively erratic."
    )
    db.add_fish(
        item_id="fish_angelfish", name="Angelfish",
        image_path="assets/minigames/fishing/fish/Angelfish.png",
        rarity="rare", difficulty=0.60, speed=1.5,
        spawn_weight=20, base_price=50,
        description="An elegant fish with flowing fins. Prized by collectors for its beauty."
    )
    db.add_fish(
        item_id="fish_surgeonfish", name="Surgeonfish",
        image_path="assets/minigames/fishing/fish/Surgeonfish.png",
        rarity="rare", difficulty=0.75, speed=1.7,
        spawn_weight=10, base_price=80,
        description="A sleek ocean fish with a razor-sharp tail spine. Extremely fast."
    )
    db.add_fish(
        item_id="fish_pufferfish", name="Pufferfish",
        image_path="assets/minigames/fishing/fish/Pufferfish.png",
        rarity="legendary", difficulty=0.90, speed=2.0,
        spawn_weight=5, base_price=150,
        description="The rarest catch in these waters. Puffs up when threatened and fights like nothing else."
    )