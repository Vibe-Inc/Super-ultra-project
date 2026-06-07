"""
Crafting tier definitions for items produced at the workbench.

When the player crafts a weapon, armor or tool at the smeltery's
workbench tab, the resulting item is rolled for a quality tier.  The
tier determines the item's final stats (``damage``, ``defense_value``,
``max_durability``) and is shown in tooltips as a coloured prefix on
the item name.

Seven tiers are defined, in ascending order of quality:

* ``horrendous`` -- crudely hammered junk, the bottom of the barrel.
* ``poor``       -- barely better than nothing.
* ``common``     -- passable, what you'd expect from an apprentice.
* ``fine``       -- the baseline; matches the database row exactly.
* ``masterwork`` -- noticeably better than the blueprint.
* ``epic``       -- rare and powerful.
* ``legendary``  -- the pinnacle of the smith's craft.

Each tier stores:

* ``name_key``   -- translation key used for the prefix label.
* ``color``      -- RGB tuple used to tint the prefix in tooltips and
                   the quality badge in the inventory / hotbar.
* ``multiplier`` -- applied to the item's pristine stats
                   (``damage``, ``defense_value``,
                   ``max_durability``, ``power`` for tools).
* ``base_weight``-- weight in the base probability distribution, used
                   by :class:`src.systems.smelting_skill.SmeltingSkill`
                   before skill scaling.  Sum doesn't have to be 100;
                   :func:`roll_tier` normalises whatever it is given.

The probability distribution is *skill-dependent*: at low smelting
levels the chance of a high tier is tiny, but every craft grants
smelting XP so the long-tail tier (``legendary``) becomes more
reachable over time.  See :func:`tier_weights_for_level`.
"""

# Ordered list so callers can iterate "from worst to best" deterministically.
TIER_ORDER = [
    "horrendous",
    "poor",
    "common",
    "fine",
    "masterwork",
    "epic",
    "legendary",
]

TIER_DEFINITIONS = {
    "horrendous": {
        "name_key": "tier.horrendous",
        "color":    (130, 80, 70),       # muddy rust
        "multiplier": 0.50,
        "base_weight": 30.0,
    },
    "poor": {
        "name_key": "tier.poor",
        "color":    (160, 160, 160),     # grey
        "multiplier": 0.70,
        "base_weight": 25.0,
    },
    "common": {
        "name_key": "tier.common",
        "color":    (210, 210, 210),     # off-white
        "multiplier": 0.90,
        "base_weight": 20.0,
    },
    "fine": {
        "name_key": "tier.fine",
        "color":    (240, 240, 255),     # bright white
        "multiplier": 1.00,
        "base_weight": 15.0,
    },
    "masterwork": {
        "name_key": "tier.masterwork",
        "color":    (90, 200, 255),      # blue
        "multiplier": 1.20,
        "base_weight": 7.0,
    },
    "epic": {
        "name_key": "tier.epic",
        "color":    (200, 90, 255),      # purple
        "multiplier": 1.50,
        "base_weight": 2.5,
    },
    "legendary": {
        "name_key": "tier.legendary",
        "color":    (255, 180, 60),      # legendary gold
        "multiplier": 2.00,
        "base_weight": 0.5,
    },
}


# Weight boost per skill level, in absolute points, applied to the
# top three tiers (masterwork, epic, legendary).  The corresponding
# negative boost is split across the bottom three tiers so the total
# probability mass stays the same.
_HIGH_TIER_KEYS = ("masterwork", "epic", "legendary")
_LOW_TIER_KEYS = ("horrendous", "poor", "common")


def tier_weights_for_level(smelting_level: int) -> dict:
    """Return a normalised weight dict for each tier at ``smelting_level``.

    The shape of the distribution morphs as the player levels up:
    low tiers get rarer, high tiers get more common.  The function
    clamps ``smelting_level`` to ``[0, MAX_SMELTING_LEVEL]`` so callers
    don't have to.

    The returned dict always contains every key in :data:`TIER_ORDER`,
    even if a tier is temporarily impossible (its weight just becomes
    ``0.0``).
    """
    from src.systems.smelting_skill import MAX_SMELTING_LEVEL  # late import: avoid cycles

    lvl = max(0, min(int(smelting_level), MAX_SMELTING_LEVEL))
    progress = lvl / float(MAX_SMELTING_LEVEL) if MAX_SMELTING_LEVEL > 0 else 0.0

    # The total swing from min to max skill.  Tuned so even at level 0
    # a legendary has a non-zero (but tiny) chance, and at max level
    # the lowest tiers are still possible (just rare).
    boost_total = 12.0  # absolute points transferred to high tiers at max lvl
    per_high = boost_total / float(len(_HIGH_TIER_KEYS))
    per_low  = boost_total / float(len(_LOW_TIER_KEYS))

    weights = {}
    for tier_id, data in TIER_DEFINITIONS.items():
        w = float(data["base_weight"])
        if tier_id in _HIGH_TIER_KEYS:
            w += per_high * progress
        elif tier_id in _LOW_TIER_KEYS:
            w -= per_low * progress
        weights[tier_id] = max(0.0, w)
    return weights


def roll_tier(smelting_level: int, rng=None) -> str:
    """Return a randomly chosen tier id, weighted by smelting skill.

    Uses the standard-library ``random`` module by default; pass a
    custom ``rng`` (anything with ``.random()``) for deterministic
    tests.  Falls back to ``"fine"`` if every weight happens to be
    zero (shouldn't happen in normal use, but guards against a
    misconfigured skill cap).
    """
    import random as _random
    rng = rng or _random

    weights = tier_weights_for_level(smelting_level)
    total = sum(weights.values())
    if total <= 0.0:
        return "fine"

    pick = rng.random() * total
    cursor = 0.0
    for tier_id in TIER_ORDER:
        cursor += weights[tier_id]
        if pick <= cursor:
            return tier_id
    return TIER_ORDER[-1]


def get_tier_data(tier_id: str) -> dict:
    """Return the raw definition dict for ``tier_id`` (or ``fine`` if unknown)."""
    return TIER_DEFINITIONS.get(tier_id, TIER_DEFINITIONS["fine"])


def get_tier_multiplier(tier_id: str) -> float:
    """Stat multiplier (damage / defense / durability) for ``tier_id``."""
    return float(get_tier_data(tier_id).get("multiplier", 1.0))


def get_tier_color(tier_id: str) -> tuple:
    """RGB tint for ``tier_id``, used to colour the prefix and badges."""
    color = get_tier_data(tier_id).get("color", (200, 200, 200))
    try:
        return tuple(int(c) for c in color[:3])
    except Exception:
        return (200, 200, 200)


def get_tier_name(tier_id: str) -> str:
    """Return the localised prefix label for ``tier_id`` (e.g. ``"[Fine]"``)."""
    data = get_tier_data(tier_id)
    try:
        return _("[{label}]").format(label=_(data["name_key"]).capitalize())
    except Exception:
        return f"[{tier_id.capitalize()}]"
