"""
Smelting / crafting skill tracking.

A single ``SmeltingSkill`` instance lives on the player character
(``character.smelting_skill``) and tracks how experienced the
blacksmith is.  Every successful craft at the workbench (and every
successful repair at the anvil) grants a small amount of XP; as XP
accumulates the player levels up, which in turn tilts the tier weight
distribution in :mod:`database.crafting_tiers_db` toward the rare,
high-tier results.

The instance is a plain attribute bag so it can be JSON-serialised by
:mod:`src.core.save_manager` -- only ``level``, ``xp`` and
``xp_to_next_level`` are persisted, and the rest of the class is
derived from those.

Tunables
--------

``XP_PER_CRAFT`` -- flat XP awarded for finishing a workbench craft.

``XP_PER_REPAIR`` -- smaller XP awarded for repairing an item at the
anvil.  Repairs are much faster and cheaper than full crafts, so the
skill reward is intentionally lower.

``MAX_SMELTING_LEVEL`` -- hard cap on the level.  Once reached, the
XP bar still tracks overflow but no more levels are gained.  The tier
weight distribution tops out at this cap.

``xp_to_next_level`` -- quadratic curve ``50 * level + 10`` so each
level requires slightly more XP than the previous one.  This is
recomputed every level-up, so the stored value is a snapshot of the
target for the *current* level only.
"""

MAX_SMELTING_LEVEL = 50
XP_PER_CRAFT = 10
XP_PER_REPAIR = 3


def _xp_required_for(level: int) -> int:
    """XP required to *finish* a given level and roll into the next one."""
    if level < 1:
        level = 1
    if level >= MAX_SMELTING_LEVEL:
        # At max level the target is "infinity" so the bar never fills.
        # Use a very large finite number so the UI can still render a
        # progress fraction (which is always 0%).
        return 10**9
    # Quadratic-ish: level 1 -> 60 XP, level 2 -> 110 XP, level 50 -> 2510 XP.
    return 50 * level + 10


class SmeltingSkill:
    """Tracks the player's crafting experience and exposes a level.

    Attributes:
        level (int): Current smelting level, clamped to
            ``[1, MAX_SMELTING_LEVEL]``.
        xp (int): XP accumulated *within the current level*.  Resets
            to the overflow amount whenever a level-up fires.
        xp_to_next_level (int): XP required to finish the current
            level and gain the next one.  Set to a huge sentinel at
            :py:attr:`MAX_SMELTING_LEVEL`.
    """

    __slots__ = ("level", "xp", "xp_to_next_level")

    def __init__(self, level: int = 1, xp: int = 0, xp_to_next_level: int | None = None):
        self.level = 1
        self.xp = 0
        self.xp_to_next_level = _xp_required_for(1)
        self.set_level(level, recompute_xp=False)
        # Always set xp last so the cap is enforced against the
        # possibly-updated xp_to_next_level.
        if xp:
            self.set_xp(xp, allow_level_up=False)
        if xp_to_next_level is not None:
            try:
                self.xp_to_next_level = max(1, int(xp_to_next_level))
            except (TypeError, ValueError):
                self.xp_to_next_level = _xp_required_for(self.level)

    # ------------------------------------------------------------------ #
    # Level / XP state                                                   #
    # ------------------------------------------------------------------ #

    def set_level(self, level: int, recompute_xp: bool = True) -> None:
        """Force the level to ``level`` (clamped) and recompute the
        XP target.  Existing XP is preserved unless ``recompute_xp``
        is ``False``, in which case it is reset to zero.
        """
        try:
            lvl = int(level)
        except (TypeError, ValueError):
            lvl = 1
        self.level = max(1, min(MAX_SMELTING_LEVEL, lvl))
        self.xp_to_next_level = _xp_required_for(self.level)
        if recompute_xp:
            self.xp = min(self.xp, self.xp_to_next_level - 1) if self.level < MAX_SMELTING_LEVEL else 0

    def set_xp(self, xp: int, allow_level_up: bool = True) -> None:
        """Set the current-level XP to ``xp`` (clamped non-negative).

        If ``allow_level_up`` is ``True`` (default) any overflow past
        ``xp_to_next_level`` is consumed and may trigger one or more
        level-ups, with the remainder carried over as the new
        current-level XP.  When called with ``allow_level_up=False``
        (typically from the deserialiser) the value is clamped but
        never triggers a level transition.
        """
        try:
            self.xp = max(0, int(xp))
        except (TypeError, ValueError):
            self.xp = 0
        if not allow_level_up:
            return
        # Cascade level-ups as long as we have overflow.  Caps at MAX.
        while self.level < MAX_SMELTING_LEVEL and self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.xp_to_next_level = _xp_required_for(self.level)
        if self.level >= MAX_SMELTING_LEVEL:
            self.xp = 0
            self.xp_to_next_level = _xp_required_for(MAX_SMELTING_LEVEL)

    def add_xp(self, amount: int) -> int:
        """Award ``amount`` XP, cascading into level-ups.

        Returns the number of levels gained by this call (usually 0
        or 1; can be 2+ for huge grants).  Negative or zero inputs
        are a no-op.
        """
        if amount is None:
            return 0
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            return 0
        if amount <= 0:
            return 0
        before = self.level
        if self.level >= MAX_SMELTING_LEVEL:
            # No more levels to gain; swallow the XP.
            return 0
        self.set_xp(self.xp + amount, allow_level_up=True)
        return max(0, self.level - before)

    # ------------------------------------------------------------------ #
    # Convenience                                                        #
    # ------------------------------------------------------------------ #

    def progress(self) -> float:
        """Current XP within this level as a ``0.0``..``1.0`` fraction."""
        if self.level >= MAX_SMELTING_LEVEL:
            return 1.0
        target = max(1, self.xp_to_next_level)
        return max(0.0, min(1.0, self.xp / float(target)))

    def is_max_level(self) -> bool:
        return self.level >= MAX_SMELTING_LEVEL

    def to_dict(self) -> dict:
        """Serialise to a JSON-friendly dict (used by the save manager)."""
        return {
            "level": int(self.level),
            "xp": int(self.xp),
            "xp_to_next_level": int(self.xp_to_next_level),
        }

    @classmethod
    def from_dict(cls, data) -> "SmeltingSkill":
        """Inverse of :meth:`to_dict`; tolerates missing keys."""
        if not isinstance(data, dict):
            return cls()
        return cls(
            level=int(data.get("level", 1) or 1),
            xp=int(data.get("xp", 0) or 0),
            xp_to_next_level=data.get("xp_to_next_level"),
        )

    def __repr__(self) -> str:
        return f"SmeltingSkill(level={self.level}, xp={self.xp}/{self.xp_to_next_level})"
