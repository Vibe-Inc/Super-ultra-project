import pygame
from src.core.logger import logger
from database.effects import create_effect


def _coerce_int(value, default: int = 0) -> int:
    """Best-effort int coercion that tolerates ``None`` and strings.

    Item rows come from SQLite and may store integers as floats (because
    :py:meth:`sqlite3.Row.is_integer` returns ``True`` for whole-number
    floats).  ``max_stack`` / ``durability`` can also arrive as ``None``
    from LEFT JOINs when the row isn't a weapon/tool.  This helper keeps
    the constructor of every item class readable.
    """
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class DurabilityMixin:
    """Shared durability state and behaviour for ``Weapon`` and ``Tool``.

    The mixin centralises every durability concern so the two concrete
    item classes don't have to duplicate it:

    * ``max_durability`` is the pristine value the item started with.
    * ``durability`` is the live, ticking-down value.  It is **clamped
      to ``[0, max_durability]`` on assignment** so callers can't push
      the item into negative or super-repaired states.
    * Items with ``unbreakable = True`` never lose durability and
      always report as fully repaired.
    * ``apply_durability_damage`` returns ``True`` exactly once, on the
      call that drove durability to zero, so the caller can fire
      "your X broke!" feedback precisely.
    * ``repair`` clamps to the max and returns the amount actually
      applied, useful for tooltips ("Repaired 12/30").
    * ``get_effective_damage`` scales weapon damage by remaining
      durability so a worn blade actually feels worn: at 0% it deals
      roughly 50% damage (floor 1); above 25% it deals full damage.
    * ``durability_percent`` is used by the UI for the bar fill.
    """

    #: Damage scaling threshold.  Below this fraction of max durability
    #: the weapon starts to lose damage output.
    DAMAGE_SCALING_THRESHOLD: float = 0.25
    #: Damage multiplier at 0% durability (the floor).  Between the
    #: threshold and 0% the multiplier interpolates linearly.
    DAMAGE_SCALING_FLOOR: float = 0.5

    def _init_durability(self, current: int, maximum, *, unbreakable: bool = False) -> None:
        max_val = _coerce_int(maximum, _coerce_int(current, 0))
        if max_val < 0:
            max_val = 0
        if max_val == 0 and not unbreakable:
            # Avoid silently creating an item that "starts broken":
            # fall back to the live value so the item is at least usable.
            max_val = max(_coerce_int(current, 0), 1)
        self.max_durability: int = max_val
        cur = _coerce_int(current, max_val)
        if cur < 0:
            cur = 0
        if cur > self.max_durability:
            cur = self.max_durability
        self.durability: int = cur
        self.unbreakable: bool = bool(unbreakable)
        self._was_broken: bool = self.durability <= 0 and not self.unbreakable

    @property
    def durability_max(self) -> int:
        """Read-only alias used by UI/serialisation code."""
        return self.max_durability

    def is_broken(self) -> bool:
        """``True`` when the item has no durability left and can no longer
        be used for its primary action (attack, chop, mine, ...).
        """
        if self.unbreakable:
            return False
        return self.durability <= 0

    def durability_percent(self) -> float:
        """Current durability as a ``0.0``..``1.0`` fraction of max.

        Returns ``1.0`` for unbreakable items so UI bars don't render
        them as empty.
        """
        if self.unbreakable or self.max_durability <= 0:
            return 1.0
        return max(0.0, min(1.0, self.durability / self.max_durability))

    def apply_durability_damage(self, amount: int = 1) -> bool:
        """Reduce ``durability`` by ``amount`` and report whether the
        item *just* broke on this call.

        Returns ``True`` exactly once per item lifetime: the call that
        brought ``durability`` from ``>0`` to ``<=0``.  Subsequent calls
        while already broken also return ``True`` until you ``repair``
        above zero, but UI feedback is normally only fired off the
        first transition.

        Unbreakable items never lose durability and always return
        ``False``.
        """
        if self.unbreakable or amount <= 0:
            return False
        if self.durability <= 0:
            # Already broken: still report broken so callers can clean
            # up stale references, but don't double-decrement the bar.
            return True
        self.durability = max(0, self.durability - int(amount))
        if self.durability <= 0:
            self._was_broken = True
            return True
        return False

    def repair(self, amount: int) -> int:
        """Add ``amount`` durability, clamping to ``max_durability``.

        Returns the amount actually applied (useful for tooltips
        showing "Repaired 12/40").  ``repair`` clears the broken flag
        so future damage can fire the "broke!" transition again.
        """
        if amount is None or amount <= 0:
            return 0
        if self.unbreakable:
            return 0
        before = self.durability
        self.durability = min(self.max_durability, self.durability + int(amount))
        if self.durability > 0:
            self._was_broken = False
        return self.durability - before

    def get_effective_damage(self, base_damage: int) -> int:
        """Scale ``base_damage`` by remaining durability.

        Above :py:attr:`DAMAGE_SCALING_THRESHOLD` (25% by default) the
        weapon deals its full base damage.  Between the threshold and
        0% the damage scales linearly from 100% down to
        :py:attr:`DAMAGE_SCALING_FLOOR` (50% by default), and is
        floored at 1 so a worn weapon still chips the enemy.

        Broken items (``durability == 0``) are treated as "bare
        hands" -- they still hit, but for the floor value.
        """
        if self.unbreakable:
            return int(base_damage)
        pct = self.durability_percent()
        if pct >= self.DAMAGE_SCALING_THRESHOLD:
            return int(base_damage)
        if pct <= 0.0:
            scale = self.DAMAGE_SCALING_FLOOR
        else:
            t = pct / self.DAMAGE_SCALING_THRESHOLD
            scale = self.DAMAGE_SCALING_FLOOR + (1.0 - self.DAMAGE_SCALING_FLOOR) * t
        return max(1, int(round(base_damage * scale)))

    def durability_label(self) -> str:
        """Short ``"cur/max"`` label, used by tooltips.

        Unbreakable items return ``"∞"`` so the player can see at a
        glance that the item never wears out.
        """
        if self.unbreakable:
            return "∞"
        return f"{int(self.durability)}/{int(self.max_durability)}"

    def durability_state(self) -> str:
        """Coarse wear tier for UI tinting.

        Returns one of ``"full"`` (>= 75%), ``"good"`` (>= 50%),
        ``"worn"`` (>= 25%), ``"low"`` (> 0%), ``"broken"``.
        Unbreakable items always report ``"full"``.
        """
        if self.unbreakable:
            return "full"
        pct = self.durability_percent()
        if pct <= 0.0:
            return "broken"
        if pct < 0.25:
            return "low"
        if pct < 0.50:
            return "worn"
        if pct < 0.75:
            return "good"
        return "full"

class Item:
    """
    Base class for all game items.

    Attributes:
        id (str): Unique identifier for the item.
        name_key (str): Translation key for the item name.
        type (str): Category of the item.
        max_stack (int): Maximum stack size in the inventory.
        price (int): Monetary value of the item.
        desc_key (str): Translation key for the description.
        image (pygame.Surface): The loaded item sprite.

    Methods:
        __init__(row: dict): Initialize item properties from a dictionary.
        name(): Property returning the translated item name.
        description(): Property returning the translated item description.
        resize(size: int): Return a cached resized surface of the item.
        get_tooltip_text(): Return formatted tooltip text.
        use(target): Abstract method for item usage logic.
    """
    def __init__(self, row: dict):
        self.id = row["id"]
        self.name_key = row["name"]
        self.type = row["type"]
        self.max_stack = row["max_stack"]
        self.price = row["price"]
        self.desc_key = row["description"] if row["description"] is not None else ""
        self.image = pygame.image.load(row["image_path"]).convert_alpha()

        self._cached_image = None
        self._cached_size = 0

    @property
    def name(self):
        return _(self.name_key)

    @property
    def description(self):
        return _(self.desc_key)

    def resize(self, size: int):
        if self._cached_size != size:
            self._cached_image = pygame.transform.scale(self.image, (size, size))
            self._cached_size = size
        return self._cached_image

    def get_tooltip_text(self):
        return f"{self.name}\n{self.description}"

    def use(self, target):
        pass


class Weapon(Item, DurabilityMixin):
    """
    Base class for weapon items, providing shared combat statistics.

    Attributes:
        damage (int): Base damage dealt by the weapon.
        durability (int): Current weapon durability points.
        max_durability (int): Original (pristine) durability the weapon
            started with.  Lets the UI render an accurate wear bar
            even as the live ``durability`` ticks down.
        unbreakable (bool): When ``True`` the weapon never loses
            durability (reserved for quest/event weapons).
        cooldown (int): Attack cooldown in milliseconds.
        weapon_class (str): Classification (e.g., melee, ranged).
        on_hit_effects (list): Optional list of effect dicts applied to a
            target each time the weapon lands a hit (e.g. Flaming Sword ->
            BurnEffect).

    Methods:
        __init__(row: dict):
            Initialize weapon properties from a database row.
        _get_base_stats_text():
            Return formatted base stats text (type, damage, durability).
    """
    def __init__(self, row: dict):
        super().__init__(row)
        self.damage = row["damage"]
        self.cooldown = row["cooldown"]
        self.weapon_class = row["weapon_class"]
        # ``max_durability`` is read from the joined row as
        # ``weapon_max_durability`` (it shares its base name with the
        # tool table).  When the column doesn't exist (older DB) the
        # live ``durability`` value doubles as the max so behaviour
        # matches the pre-durability-system code.
        max_dur = row.get("weapon_max_durability", None)
        if max_dur is None:
            max_dur = row.get("max_durability", row["durability"])
        self._init_durability(row["durability"], max_dur)
        # Per-weapon on-hit effects (list of effect dicts).
        # We keep it as a plain attribute even if the column is missing so
        # that existing items (with no on-hit effects) keep working.
        self.on_hit_effects = []
        raw_on_hit = row.get("on_hit_effects")
        if raw_on_hit:
            if isinstance(raw_on_hit, str):
                import ast
                try:
                    self.on_hit_effects = ast.literal_eval(raw_on_hit)
                except (ValueError, SyntaxError, TypeError):
                    self.on_hit_effects = []
            elif isinstance(raw_on_hit, list):
                self.on_hit_effects = list(raw_on_hit)

    def _get_base_stats_text(self):
        weapon_label = f"{_('Weapon')} ({self.weapon_class.capitalize()})"
        if self.unbreakable:
            dur_str = f"{_('Durability')}: ∞"
        else:
            dur_str = f"{_('Durability')}: {int(self.durability)}/{int(self.max_durability)}"
        return (
            f"{_('Type')}: {weapon_label}\n"
            f"{_('Damage')}: {self.damage}\n"
            f"{dur_str}\n"
        )


class MeleeWeapon(Weapon):
    """
    Represents a melee combat weapon.

    Attributes:
        range (int): Effective attack range in pixels.
        combat_style (str): Attack pattern identifier:
            'sword' - standard cone arc,
            'mace'  - circular AoE at impact point,
            'axe'   - full 360° spinning sweep,
            'spear' - long narrow piercing line,
            'dagger' - quick short multi-strike,
            'war_hammer' - heavy slam with small AoE stun.

    Methods:
        __init__(row: dict):
            Initialize melee weapon properties from a database row.
        get_tooltip_text():
            Return formatted tooltip text including range and combat style.
    """
    def __init__(self, row: dict):
        super().__init__(row)
        self.range = row["range"]
        self.combat_style = row.get("combat_style", "sword")

    def get_tooltip_text(self):
        base_stats = self._get_base_stats_text()
        style_label = self.combat_style.replace("_", " ").title()
        stats = (
            f"{base_stats}"
            f"{_('Range')}: {self.range}\n"
            f"{_('Style')}: {style_label}\n"
            f"Price: ${self.price}"
        )
        return f"{self.name}\n{stats}\n{self.description}"


class RangedWeapon(Weapon):
    """
    Represents a ranged combat weapon.

    Attributes:
        range (int): Effective attack range in pixels.
        projectile_speed (int): Speed of the fired projectile.
        cone_degrees (int): Total cone angle in degrees for spread.
        spread_degrees (int): Random spread angle per shot in degrees.

    Methods:
        __init__(row: dict):
            Initialize ranged weapon properties from a database row.
        get_tooltip_text():
            Return formatted tooltip text including range and projectile speed.
    """
    def __init__(self, row: dict):
        super().__init__(row)
        self.range = row["range"]
        self.projectile_speed = row["projectile_speed"]
        self.cone_degrees = row["cone_degrees"]
        self.spread_degrees = row["spread_degrees"]

    def get_tooltip_text(self):
        base_stats = self._get_base_stats_text()
        stats = (
            f"{base_stats}"
            f"{_('Range')}: {self.range}\n"
            f"{_('Proj. Speed')}: {self.projectile_speed}\n"
            f"Price: ${self.price}"
        )
        return f"{self.name}\n{stats}\n{self.description}"


class Consumable(Item):
    """
    Represents an item that can be used to restore health
    or apply temporary effects to the target.

    Attributes:
        heal_amount (int): Points of HP restored or lost.
        effects_list (list): Configuration for applying dynamic effects.

    Methods:
        __init__(row: dict):
            Initialize consumable properties from a database row.
        get_tooltip_text():
            Return formatted tooltip text including heal and effects info.
        use(target):
            Apply the consumable's effects to the target. Returns True if at
            least one effect was applied.
    """
    def __init__(self, row: dict):
        super().__init__(row)
        self.heal_amount = row.get("heal_amount", 0)
        self.effects_list = row.get("effects", [])

    def get_tooltip_text(self):
        stats = f"{_('Type')}: {_('Consumable')}"
        if self.heal_amount > 0:
            stats += f"\n{_('Heal')}: +{self.heal_amount} {_('HP')}"
        elif self.heal_amount < 0:
            stats += f"\n{_('Damage')}: {self.heal_amount} {_('HP')}"
        if self.effects_list:
            stats += f"\n{_('Effects')}:"
            for effect_data in self.effects_list:
                etype = effect_data.get("type", "unknown")
                dur = effect_data.get("duration", 0)
                stats += f"\n - {etype.capitalize()} ({dur}s)"

        stats += f"\nPrice: ${self.price}"
        return f"{self.name}\n{stats}\n{self.description}"

    def use(self, target):
        """
        Apply the consumable's effects to the target.

        Returns True when at least one effect was applied (HP, mana, or
        a status effect), False otherwise.
        """
        used = False
        if self.heal_amount != 0:
            new_hp = min(target.max_hp, max(0, target.hp + self.heal_amount))
            # Special case: very large heal_amount (e.g. Elixir of Life) acts
            # as a full restore, no matter the current missing HP.
            if self.heal_amount >= target.max_hp:
                target.hp = target.max_hp
            else:
                target.hp = new_hp
            used = True

        if self.effects_list:
            used = True
            for effect_data in self.effects_list:
                effect_obj = create_effect(effect_data)
                if effect_obj:
                    target.add_effect(effect_obj)
        return used


class Armor(Item, DurabilityMixin):
    """
    Represents an armor item that can be equipped in a specific equipment slot.

    Armor inherits from :class:`DurabilityMixin` so it shares the same
    wear-bar UX as weapons and tools: each time the wearer takes a hit
    the equipped piece loses a point of ``durability``; the wear bar in
    the inventory/hotbar renders the live value, and a piece that has
    hit zero contributes 0 defense.  Armor that has never been hit stays
    at ``max_durability`` for its entire lifetime.

    Attributes:
        slot_type (str): The equipment slot this armor belongs to
                         ("helmet", "chestplate", "leggings", "boots",
                          "charm", "gloves", "ring", "belt").
        defense_value (int): Pristine flat damage reduction this armor
            provides.  The *effective* contribution to the player's
            ``character.defense`` is scaled by the remaining
            durability via :py:meth:`get_effective_defense` so a worn
            chestplate still feels worn.
        durability (int): Current wear points (set by
            :py:meth:`DurabilityMixin._init_durability`).
        max_durability (int): Pristine wear budget.

    Methods:
        __init__(row: dict):
            Initialize armor properties from a database row.
        get_effective_defense():
            Return the damage-reduction contribution of this piece,
            scaled by remaining durability.
        get_tooltip_text():
            Return formatted tooltip text including armor type,
            defense, and durability.
    """
    # Defense scaling curve mirrors the weapon damage curve so a worn
    # armor piece feels the same as a worn weapon: above 25% durability
    # you get the full defense, between 0% and 25% the contribution
    # interpolates down to the floor (50% by default), and broken
    # pieces (0% durability) contribute the floor value too -- never
    # zero, so a broken chestplate is still slightly better than
    # nothing.
    DEFENSE_SCALING_THRESHOLD: float = 0.25
    DEFENSE_SCALING_FLOOR: float = 0.5

    def __init__(self, row: dict):
        super().__init__(row)
        self.slot_type = row.get("slot_type", "helmet")
        self.defense_value = row.get("defense_value", 0)
        # ``armor_durability`` is the alias used by the DB query's LEFT
        # JOIN on the ``armor`` table.  Fall back to ``max_durability``
        # (flat row variant) and finally to the live value so the item
        # is at least "fully repaired" out of the box.
        current_dur = row.get("armor_durability", row.get("durability", None))
        max_dur = row.get("armor_max_durability", None)
        if max_dur is None:
            max_dur = row.get("max_durability", current_dur)
        self._init_durability(current_dur if current_dur is not None else 100, max_dur)

    def get_effective_defense(self) -> int:
        """Return the damage-reduction contribution of this piece,
        scaled by remaining durability.

        Mirrors :py:meth:`DurabilityMixin.get_effective_damage` for
        weapons: above :py:attr:`DEFENSE_SCALING_THRESHOLD` the piece
        provides its full ``defense_value``; between 0% and the
        threshold it interpolates linearly down to
        :py:attr:`DEFENSE_SCALING_FLOOR` (50% by default).  Broken
        pieces (0% durability) still provide the floor value, floored
        at 1 so a worn-down chestplate never becomes literal dead
        weight that *reduces* the player's defense.

        Unbreakable armor pieces always return the full
        ``defense_value``.
        """
        if self.unbreakable:
            return int(self.defense_value)
        pct = self.durability_percent()
        if pct >= self.DEFENSE_SCALING_THRESHOLD:
            return int(self.defense_value)
        if pct <= 0.0:
            scale = self.DEFENSE_SCALING_FLOOR
        else:
            t = pct / self.DEFENSE_SCALING_THRESHOLD
            scale = self.DEFENSE_SCALING_FLOOR + (1.0 - self.DEFENSE_SCALING_FLOOR) * t
        return max(1, int(round(self.defense_value * scale)))

    def get_tooltip_text(self):
        slot_map = {
            "helmet": _("Helmet"), "chestplate": _("Chestplate"),
            "leggings": _("Leggings"), "boots": _("Boots"),
            "charm": _("Charm"), "gloves": _("Gloves"),
            "ring": _("Ring"), "belt": _("Belt"),
        }
        slot_label = slot_map.get(self.slot_type, self.slot_type.capitalize())
        if self.unbreakable:
            dur_str = f"{_('Durability')}: ∞"
        else:
            dur_str = f"{_('Durability')}: {int(self.durability)}/{int(self.max_durability)}"
        # Show the *effective* defense so the player understands why a
        # worn piece suddenly feels weaker than the displayed +N.
        effective = self.get_effective_defense()
        if effective != self.defense_value:
            defense_str = f"{_('Defense')}: +{self.defense_value} ({effective} effective)"
        else:
            defense_str = f"{_('Defense')}: +{self.defense_value}"
        stats = (
            f"{_('Type')}: {_('Armor')} ({slot_label})\n"
            f"{defense_str}\n"
            f"{dur_str}\n"
            f"Price: ${self.price}"
        )
        return f"{self.name}\n{stats}\n{self.description}"


class Lamp(Item):
    """Simple handheld lamp item that can be toggled on/off to provide light."""
    def __init__(self, row: dict | None = None, *, image_path: str = "assets/items/lamp.png"):
        # Create a minimal row-like dict if none provided
        if row is None:
            row = {
                "id": "hand_lamp",
                "name": "Hand Lamp",
                "type": "misc",
                "max_stack": 1,
                "price": 15,
                "description": "A small oil lamp that provides light when turned on.",
                "image_path": image_path,
            }
        super().__init__(row)
        self.lit = False
        self.light_radius = 220  # pixels
        self.intensity = 1.0

    def toggle(self, target=None):
        self.lit = not self.lit
        return self.lit

    def use(self, target):
        # Toggle lamp on the target (player)
        try:
            target.active_lamp = self if getattr(target, 'active_lamp', None) is not self else None
        except Exception:
            pass
        self.lit = not self.lit
        return True


class Lantern(Item):
    """Handheld lantern that illuminates a small radius around the character while held.

    The lantern emits light automatically when it occupies the player's active
    hotbar slot — no toggling needed.  ``Game.get_light_sources`` reads the
    ``emits_light`` flag and the ``light_radius`` / ``intensity`` attributes to
    feed the lighting overlay in the renderer.
    """
    def __init__(self, row: dict | None = None, *, image_path: str = "assets/items/lantern.png"):
        if row is None:
            row = {
                "id": "lantern",
                "name": "Lantern",
                "type": "misc",
                "max_stack": 1,
                "price": 25,
                "description": "A compact lantern that casts a warm glow around you when carried.",
                "image_path": image_path,
            }
        super().__init__(row)
        self.light_radius = 200   # pixels – soft warm glow
        self.intensity = 1.4      # strong intensity for clear illumination
        self.emits_light = True   # flag checked by Game.get_light_sources()

    def get_tooltip_text(self):
        stats = (
            f"{_('Type')}: {_('Misc')}\n"
            f"{_('Light Radius')}: {self.light_radius}px\n"
            f"Price: ${self.price}"
        )
        return f"{self.name}\n{stats}\n{self.description}"


class LightRing(Armor):
    """Enchanted ring that amplifies the lantern's glow when worn.

    Equip this ring in the ring slot to increase both the light radius and
    intensity of any light-emitting item held in the hotbar (Lantern, Lamp).
    """
    def __init__(self, row: dict | None = None, *, image_path: str = "assets/items/accessories/Light_ring.png"):
        if row is None:
            row = {
                "id": "light_ring",
                "name": "Light Ring",
                "type": "armor",
                "max_stack": 1,
                "price": 120,
                "description": "An enchanted ring that emits a soft glow and amplifies any light source you carry.",
                "image_path": image_path,
                "slot_type": "ring",
                "defense_value": 0,
            }
        super().__init__(row)
        self.light_radius = 260   # bigger radius than the lantern (200)
        self.light_intensity = 1.6  # strong illumination
        self.emits_light = True   # same flag the lantern uses
        self.light_radius_bonus = 80   # extra pixels added to lantern radius
        self.light_intensity_bonus = 0.3  # extra intensity added to lantern

    def get_tooltip_text(self):
        stats = (
            f"{_('Type')}: {_('Armor')} ({_('Ring')})\n"
            f"{_('Defense')}: +{self.defense_value}\n"
            f"+{self.light_radius_bonus} {_('Light Radius')}\n"
            f"+{self.light_intensity_bonus} {_('Light Intensity')}\n"
        )
        return f"{self.name}\n{stats}\n{self.description}"


class Tool(Item, DurabilityMixin):
    """
    Represents a utility tool used to perform a specific in-world action
    (fishing, mining, woodcutting, etc.). Tools are not weapons, not
    consumables, and usually do not stack.

    Attributes:
        tool_type (str): Sub-category of the tool
            (e.g. "fishing", "pickaxe", "axe").
        durability (int): Current durability points (live value).
        max_durability (int): Pristine durability the tool started with;
            used to draw the wear bar in the inventory / hotbar.
        unbreakable (bool): ``True`` for tools that never wear down.
        power (int): Generic effectiveness multiplier (e.g. catch power
            bonus for a fishing rod, mining speed for a pickaxe).
        gather_type (str | None): Resource type this tool can gather.
            ``"wood"`` matches ``choppable`` tiles; ``"stone"`` or
            ``"ore"`` matches ``minable`` tiles. ``None`` means the
            tool does not gather (e.g. a fishing rod).
        gather_yield_min (int): Minimum items produced per gather.
        gather_yield_max (int): Maximum items produced per gather.

    Methods:
        __init__(row: dict):
            Initialize tool properties from a database row.
        get_tooltip_text():
            Return formatted tooltip text including tool type, power,
            and the resource it gathers (if any).
    """
    def __init__(self, row: dict):
        super().__init__(row)
        self.tool_type = row.get("tool_type", "generic") or "generic"
        current_dur = row.get("tool_durability", row.get("durability", 100)) or 100
        # ``tool_max_durability`` is the alias used by the DB query's
        # LEFT JOIN on the ``tools`` table.  Fall back to ``max_durability``
        # for callers that pre-compute a flat row, and finally to the
        # current value so the item is at least "fully repaired".
        max_dur = row.get("tool_max_durability", None)
        if max_dur is None:
            max_dur = row.get("max_durability", current_dur)
        self._init_durability(current_dur, max_dur)
        self.power = row.get("power", 0) or 0
        self.gather_type = row.get("gather_type") or None
        self.gather_yield_min = int(row.get("gather_yield_min") or 1)
        self.gather_yield_max = int(row.get("gather_yield_max") or self.gather_yield_min)

    def get_tooltip_text(self):
        type_label = self.tool_type.replace("_", " ").title()
        if self.unbreakable:
            dur_str = f"{_('Durability')}: ∞"
        else:
            dur_str = f"{_('Durability')}: {int(self.durability)}/{int(self.max_durability)}"
        stats = (
            f"{_('Type')}: {_('Tool')} ({type_label})\n"
            f"{dur_str}\n"
            f"{_('Power')}: +{self.power}\n"
        )
        if self.gather_type:
            gather_label = self.gather_type.replace("_", " ").title()
            if self.gather_yield_min == self.gather_yield_max:
                yield_str = str(self.gather_yield_min)
            else:
                yield_str = f"{self.gather_yield_min}-{self.gather_yield_max}"
            stats += f"{_('Gathers')}: {gather_label} ({yield_str})\n"
        stats += f"Price: ${self.price}"
        return f"{self.name}\n{stats}\n{self.description}"


# ─── Rainbow / Gay Ring ───────────────────────────────────────────────────────

class GayRing(Armor):
    """A fabulous rainbow ring that creates a gloving rainbow aura around the wearer.

    When equipped in the ring slot, it generates a vibrant rainbow aura with
    orbiting rainbow-colored particles, pulsing rainbow rings, and sparkle effects
    that follow the player character.
    """
    # Predefined rainbow color palette for consistent cycling
    RAINBOW_COLORS = [
        (255, 50, 50),    # Red
        (255, 160, 20),   # Orange
        (255, 255, 50),   # Yellow
        (50, 255, 50),    # Green
        (50, 200, 255),   # Cyan/Blue
        (200, 50, 255),   # Purple
        (255, 50, 200),   # Pink
    ]

    def __init__(self, row: dict | None = None, *, image_path: str = "assets/items/accessories/Gay_ring.png"):
        if row is None:
            row = {
                "id": "gay_ring",
                "name": "Gay Ring",
                "type": "armor",
                "max_stack": 1,
                "price": 67,
                "description": "A fabulous rainbow ring! Creates a gloving rainbow aura around you when equipped.",
                "image_path": image_path,
                "slot_type": "ring",
                "defense_value": 1,
            }
        super().__init__(row)
        self.emits_light = True
        self.light_radius = 130
        self.light_intensity = 1.6

    def get_tooltip_text(self):
        rainbow_charm = "🌈✨🌈✨🌈"
        stats = (
            f"{_('Type')}: {_('Armor')} ({_('Ring')})\n"
            f"{_('Defense')}: +{self.defense_value}\n"
            f"{rainbow_charm}\n"
            f"{_('Gloving Rainbow Aura')}\n"
        )
        return f"{self.name}\n{stats}\n{self.description}"


class Fish(Item):
    """
    Represents a fish caught via the fishing minigame.

    Attributes:
        rarity (str): Rarity tier (common, uncommon, rare, legendary).
        difficulty (float): 0.0 to 1.0, how hard the fish is to catch.
        speed (float): Speed multiplier for the fish's movement on the bar.
        spawn_weight (int): Relative spawn weight when selecting a fish.
        base_price (int): Gold value when sold.
    """
    def __init__(self, row: dict):
        super().__init__(row)
        self.rarity = row.get("rarity", "common") or "common"
        self.difficulty = row.get("difficulty", 0.3) or 0.3
        self.speed = row.get("fish_speed", row.get("speed", 1.0)) or 1.0
        self.spawn_weight = row.get("spawn_weight", 50) or 50
        self.base_price = row.get("fish_base_price", row.get("base_price", 10)) or 10

    def get_tooltip_text(self):
        rarity_label = self.rarity.capitalize()
        stats = (
            f"{_('Type')}: {_('Fish')} ({rarity_label})\n"
            f"Price: ${self.price}"
        )
        return f"{self.name}\n{stats}\n{self.description}"


def create_item(item_id: str):
    """
    Factory function to instantiate the appropriate item class.

    Args:
        item_id (str): The identifier to look up in the database.

    Returns:
        Item | None: An instance of a specific item class or None.
    """
    # Built-in quick items (do not require DB presence)
    if item_id in ("hand_lamp", "lamp"):
        try:
            return Lamp(None)
        except Exception:
            pass

    if item_id == "lantern":
        try:
            return Lantern(None)
        except Exception:
            pass

    if item_id == "light_ring":
        try:
            return LightRing(None)
        except Exception:
            pass

    if item_id == "gay_ring":
        try:
            return GayRing(None)
        except Exception:
            pass

    from database.GP_database import Gp_database

    db = Gp_database()
    row = db.get_item(item_id)
    db.close()

    if not row:
        logger.error(f"Предмет '{item_id}' не знайдено в базі даних!")
        return None

    item_type = row.get("type")

    if item_type == "weapon":
        w_class = row.get("weapon_class")
        if w_class == "ranged":
            return RangedWeapon(row)
        else:
            return MeleeWeapon(row)
    elif item_type in ("food", "potion"):
        return Consumable(row)
    elif item_type == "armor":
        return Armor(row)
    elif item_type == "tool":
        return Tool(row)
    elif item_type == "resource":
        return Item(row)
    elif item_type == "fish":
        return Fish(row)
    else:
        logger.warning(f"Unknown item type '{item_type}' for '{item_id}'. Defaulting to generic Item.")
        return Item(row)