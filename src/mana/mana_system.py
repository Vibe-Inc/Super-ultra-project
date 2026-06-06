"""
ManaSystem component for managing the player's mana resource.

Handles mana storage, regeneration over time, consumption, and max mana cap management.
Also tracks a "crumble" animation whenever mana is spent: the just-spent section
turns faded and, over CONSUME_ANIM_DURATION seconds, dissolves into dust that
floats away. If more mana is spent while a previous animation is still running,
the new segment extends the existing animation rather than restarting it.
"""

import random

from src.core.logger import logger


# Duration (in seconds) that a single spent-mana segment takes to fully crumble
# into dust. The requirement is 0.8 seconds.
CONSUME_ANIM_DURATION = 0.8


class _ConsumeSegment:
    """A single animated, crumbling segment of the mana bar.

    A segment is defined by a normalized mana range [start_norm, end_norm]
    on the mana bar (0.0 = left edge, 1.0 = right edge). The segment animates
    from its creation time, losing opacity, crumbling visually, and emitting
    dust particles, over CONSUME_ANIM_DURATION seconds.

    Attributes:
        start_norm (float): Normalized left position of the segment on the bar.
        end_norm (float): Normalized right position of the segment on the bar.
        elapsed (float): Time in seconds since the segment was created.
        dust (list): List of dust particle dicts {x_norm, y, vx, vy, lt, max_lt,
            size, color, phase} emitted by this segment.
    """

    __slots__ = ("start_norm", "end_norm", "elapsed", "dust")

    def __init__(self, start_norm: float, end_norm: float):
        self.start_norm = start_norm
        self.end_norm = end_norm
        self.elapsed = 0.0
        # Pre-seed a few dust particles so they are visible immediately.
        self.dust = []
        self._seed_dust(0.0)

    def _seed_dust(self, initial_elapsed: float) -> None:
        """Pre-populate a handful of dust particles across the segment.

        Args:
            initial_elapsed (float): Time at which the seed is being added,
                used to randomize initial offsets so dust doesn't appear in
                lockstep.
        """
        width = max(0.0, self.end_norm - self.start_norm)
        if width <= 0.0:
            return
        particle_count = max(4, int(width * 14))
        for _ in range(particle_count):
            self.dust.append(self._make_dust(initial_elapsed))

    @staticmethod
    def _make_dust(elapsed: float):
        """Create a single dust particle definition.

        Particle coordinates are stored as **offsets relative to the
        segment's own local pixel space**. ``local_x_norm`` is a 0..1
        fraction of the segment width (scaled to pixels by the HUD at
        draw time), and ``y_norm`` is a 0..1 fraction of the bar height
        the segment sits on.  ``y_norm`` drifts downward (larger values)
        over time at ``vy`` px/s, but since we treat larger y_norm as
        "downward", particles with negative vy drift toward y_norm=0
        (the top of the bar) and eventually above it.

        Args:
            elapsed (float): Current segment elapsed time, currently
                unused but kept for forward-compatibility (e.g. randomising
                starting offset so newly merged particles don't all twinkle
                in sync).

        Returns:
            dict: Dust particle parameters.
        """
        lt_value = random.uniform(0.55, 0.95)
        return {
            "local_x_norm": random.uniform(0.0, 1.0),
            "y_norm": random.uniform(0.0, 1.0),
            "vx": random.uniform(-14.0, 14.0),       # normalised drift per second
            "vy": random.uniform(-32.0, -14.0),      # upward (negative) drift
            "lt": lt_value,
            "max_lt": lt_value,                       # remember starting lifetime
            "size": random.uniform(0.6, 1.8),
            "color": random.choice([
                (170, 130, 255),
                (200, 160, 255),
                (140, 100, 230),
                (220, 200, 255),
                (255, 220, 255),
            ]),
            "phase": random.uniform(0.0, 6.28),
        }

    def update(self, dt: float) -> bool:
        """Advance the segment animation by dt seconds.

        Args:
            dt (float): Delta time in seconds.

        Returns:
            bool: True if the segment is still alive (elapsed < duration),
            False if it has finished and should be removed.
        """
        self.elapsed += dt
        # Periodically emit new dust while the segment is still active.
        if self.elapsed < CONSUME_ANIM_DURATION:
            # Emit rate scales with segment width and remaining time.
            width = max(0.0, self.end_norm - self.start_norm)
            emit_chance = min(1.0, dt * 18.0 * max(0.2, width))
            if random.random() < emit_chance:
                self.dust.append(self._make_dust(self.elapsed))
        # Age existing dust.  Coordinates are normalized (0..1 across the
        # segment's width / bar height), so we just keep ``local_x_norm``
        # in [0, 1] and let ``y_norm`` drift upward (subtract) at the
        # velocity, with a tiny gravity bias so dust eventually leaves
        # the visible area.
        alive_dust = []
        for p in self.dust:
            p["local_x_norm"] += p["vx"] * dt * 0.02  # small horizontal drift
            # Clamp horizontal to keep dust above the segment.
            if p["local_x_norm"] < 0.0:
                p["local_x_norm"] = 0.0
            elif p["local_x_norm"] > 1.0:
                p["local_x_norm"] = 1.0
            # Vertical: positive y_norm is downward in our convention,
            # and the particle's vy is *negative* (upward).  Apply a
            # small gravity bias so dust floats up and away quickly.
            p["y_norm"] += p["vy"] * dt * 0.02
            # Limit so dust doesn't overshoot: it can go below 0 (below
            # the bar) or above 1 (above the bar) — the HUD will simply
            # skip rendering particles outside the bar's vertical range.
            p["lt"] -= dt
            if p["lt"] > 0.0:
                alive_dust.append(p)
        self.dust = alive_dust
        return self.elapsed < CONSUME_ANIM_DURATION

    @property
    def progress(self) -> float:
        """0.0 at creation -> 1.0 when fully crumbled.

        Returns:
            float: Animation progress clamped to [0, 1].
        """
        if CONSUME_ANIM_DURATION <= 0.0:
            return 1.0
        return max(0.0, min(1.0, self.elapsed / CONSUME_ANIM_DURATION))


class ManaSystem:
    """
    Manages the player's mana resource with regeneration over time.

    Attributes:
        current_mana (float): Current mana value.
        max_mana (int): Maximum mana cap.
        mana_regen_rate (float): Mana regenerated per second.
        base_mana_regen_rate (float): Base mana regeneration rate.
        mana_regen_delay (float): Delay in seconds before mana starts regenerating after use.
        _regen_timer (float): Timer tracking time since last mana consumption.
        _consume_segments (list[_ConsumeSegment]): Active crumbling animations.
        _last_visual_mana (float): The highest mana value seen since the last
            consume, used to determine the "edge" of where new spending bites
            into the bar.

    Methods:
        update(dt): Update mana regeneration over time and animation state.
        consume_mana(amount): Consume mana, returns True if successful.
        restore_mana(amount): Restore mana up to max cap.
        increase_max_mana(amount): Increase the max mana cap.
        set_mana_regen_rate(rate): Set a custom mana regeneration rate.
        reset_mana_regen_rate(): Reset to base regeneration rate.
        get_mana_percent(): Get current mana as a percentage (0.0-1.0).
        is_full(): Check if mana is at maximum.
        is_empty(): Check if mana is at zero.
        get_consume_segments(): Return the list of active crumble segments.
    """

    def __init__(self, max_mana: int = 100, mana_regen_rate: float = 2.5,
                 mana_regen_delay: float = 0.5):
        """
        Initialize the ManaSystem.

        Args:
            max_mana (int): Maximum mana cap. Default is 100.
            mana_regen_rate (float): Mana regenerated per second.
                Default is 2.5 (reduced 4x from the previous 10.0).
            mana_regen_delay (float): Delay before regeneration starts after use. Default is 0.5s.
        """
        self.max_mana = max_mana
        self.current_mana = float(max_mana)
        self.mana_regen_rate = mana_regen_rate
        self.base_mana_regen_rate = mana_regen_rate
        self.mana_regen_delay = mana_regen_delay
        self._regen_timer = 0.0
        self._is_regen_paused = False

        # Crumble animation state.
        self._consume_segments: list = []
        # Track the "high-water mark" of mana so that the crumble strip
        # can be visualized at the correct (rightmost) location even when
        # several consumptions happen in a row before the animation ends.
        # _last_visual_mana is the normalized mana level we *last drew*
        # on the bar. New consumptions always bite into the right edge of
        # this value.
        self._last_visual_mana_norm: float = 1.0

        logger.debug(f"ManaSystem initialized: max_mana={max_mana}, regen_rate={mana_regen_rate}")

    def update(self, dt: float) -> None:
        """
        Update mana regeneration over time and animate crumble segments.

        Args:
            dt (float): Delta time in seconds since last update.
        """
        # Advance crumble animations first so any consumed segment aged
        # past its duration is removed before the HUD reads the list.
        alive_segments = []
        for seg in self._consume_segments:
            if seg.update(dt):
                alive_segments.append(seg)
        self._consume_segments = alive_segments

        # If mana is full, no need to regenerate
        if self.current_mana >= self.max_mana:
            self.current_mana = float(self.max_mana)
            self._regen_timer = 0.0
            self._last_visual_mana_norm = 1.0
            return

        # Handle regeneration delay after mana consumption
        if self._is_regen_paused:
            self._regen_timer += dt
            if self._regen_timer >= self.mana_regen_delay:
                self._is_regen_paused = False
                self._regen_timer = 0.0
            return

        # Regenerate mana
        if self.current_mana < self.max_mana:
            self.current_mana += self.mana_regen_rate * dt
            if self.current_mana > self.max_mana:
                self.current_mana = float(self.max_mana)
            # Track where the right edge of the bar is *visually* so future
            # consumptions carve from the new high-water mark.
            self._last_visual_mana_norm = self.current_mana / self.max_mana

    def consume_mana(self, amount: float) -> bool:
        """
        Consume mana if enough is available.

        The consumed section is scheduled for a 0.8s crumble-into-dust
        animation. If a previous animation is still active, the new
        segment extends the existing one rather than replacing it.

        Args:
            amount (float): Amount of mana to consume.

        Returns:
            bool: True if enough mana was available and consumed, False otherwise.
        """
        if amount <= 0:
            return True

        if self.current_mana >= amount:
            # The bar visually fills from the left. When mana is spent, the
            # rightmost (just-lost) portion should crumble. We use the
            # _last_visual_mana_norm (the right edge *before* this consume)
            # as the right end of the spent region, and the new current_mana
            # as the left end.
            before_norm = self._last_visual_mana_norm
            after_norm = max(0.0, (self.current_mana - amount) / self.max_mana)

            if before_norm > after_norm:
                self._add_consume_segment(after_norm, before_norm)

            # Update the high-water mark to the new mana level.
            self._last_visual_mana_norm = after_norm

            self.current_mana -= amount
            self._regen_timer = 0.0
            self._is_regen_paused = True
            logger.debug(f"Consumed {amount:.1f} mana. Mana: {int(self.current_mana)}/{self.max_mana}")
            return True

        logger.debug(f"Not enough mana to consume {amount}. Current: {int(self.current_mana)}")
        return False

    def _add_consume_segment(self, new_start_norm: float, new_end_norm: float) -> None:
        """Register a new crumble segment, extending any active overlapping
        segment on the right (consumed sections are always on the bar's
        right side as mana drains from the right).

        The logic:
        - If an active segment's [start, end] overlaps or is adjacent to
          [new_start, new_end], merge them into a single segment that
          spans the union. The merged segment keeps the older segment's
          elapsed time (so dust state continues smoothly) and is reseeded
          with a few new dust particles in the newly-added region.
        - Otherwise, push a new segment.

        Args:
            new_start_norm (float): Normalized left edge of the spent section.
            new_end_norm (float): Normalized right edge of the spent section.
        """
        # Clamp inputs.
        new_start_norm = max(0.0, min(1.0, new_start_norm))
        new_end_norm = max(0.0, min(1.0, new_end_norm))
        if new_end_norm <= new_start_norm:
            return

        # Try to merge with an existing active segment if they touch/overlap.
        for seg in self._consume_segments:
            # Overlap if seg.end >= new_start AND seg.start <= new_end
            if seg.end_norm + 1e-4 >= new_start_norm and seg.start_norm - 1e-4 <= new_end_norm:
                # Extend on whichever side is new.
                old_start, old_end = seg.start_norm, seg.end_norm
                merged_start = min(old_start, new_start_norm)
                merged_end = max(old_end, new_end_norm)
                seg.start_norm = merged_start
                seg.end_norm = merged_end
                # Seed a few extra dust particles in the newly added region
                # so the freshly-crumbled edge looks alive.
                if merged_start < old_start:
                    self._seed_dust_in_range(seg, merged_start, old_start)
                if merged_end > old_end:
                    self._seed_dust_in_range(seg, old_end, merged_end)
                return

        # No overlap; create a brand-new segment.
        self._consume_segments.append(_ConsumeSegment(new_start_norm, new_end_norm))

    @staticmethod
    def _seed_dust_in_range(segment: _ConsumeSegment, start_norm: float, end_norm: float) -> None:
        """Add a burst of dust particles within a normalized sub-range of
        an existing segment. Used when extending a live segment.

        Args:
            segment (_ConsumeSegment): The segment receiving new particles.
            start_norm (float): Normalized left edge of the new region
                (relative to the whole bar; we convert to segment-local
                coordinates here).
            end_norm (float): Normalized right edge of the new region.
        """
        seg_width = max(0.0, segment.end_norm - segment.start_norm)
        if seg_width <= 0.0:
            return
        # Convert the absolute sub-range [start_norm, end_norm] into a
        # segment-local range [0, 1] so the new particles are placed
        # correctly even when the segment was already partially extended.
        local_start = max(0.0, (start_norm - segment.start_norm) / seg_width)
        local_end = min(1.0, (end_norm - segment.start_norm) / seg_width)
        sub_width = max(0.0, local_end - local_start)
        if sub_width <= 0.0:
            return
        count = max(3, int(sub_width * 14))
        for _ in range(count):
            d = segment._make_dust(segment.elapsed)
            # Position the new particle inside the local sub-range.
            d["local_x_norm"] = random.uniform(local_start, local_end)
            segment.dust.append(d)

    def restore_mana(self, amount: float) -> float:
        """
        Restore mana up to max cap.

        Args:
            amount (float): Amount of mana to restore.

        Returns:
            float: Actual amount of mana restored.
        """
        if amount <= 0:
            return 0.0

        prev_mana = self.current_mana
        self.current_mana = min(float(self.max_mana), self.current_mana + amount)
        restored = self.current_mana - prev_mana

        if restored > 0:
            # Push the high-water mark back up so subsequent consumes
            # carve from the new (higher) level, and so any currently
            # animating segment that is *behind* the new mana level
            # immediately disappears (the bar has refilled past it).
            new_norm = self.current_mana / self.max_mana
            self._last_visual_mana_norm = new_norm
            # Remove segments entirely behind the new fill level.
            self._consume_segments = [
                s for s in self._consume_segments if s.end_norm > new_norm + 1e-4
            ]
            logger.info(f"Restored {int(restored)} mana. Mana: {int(self.current_mana)}/{self.max_mana}")

        return restored

    def increase_max_mana(self, amount: int) -> None:
        """
        Increase the max mana cap and optionally restore some mana.

        Args:
            amount (int): Amount to increase max mana by.
        """
        if amount <= 0:
            return

        self.max_mana += amount
        self.current_mana += amount  # Also increase current mana by same amount
        # A new max means the high-water mark resets and any in-flight
        # segments become invisible (bar is fuller than they extend to).
        self._last_visual_mana_norm = 1.0
        self._consume_segments.clear()
        logger.info(f"Max mana increased by {amount}. New max: {self.max_mana}")

    def set_mana_regen_rate(self, rate: float) -> None:
        """
        Set a custom mana regeneration rate.

        Args:
            rate (float): New mana regeneration rate per second.
        """
        self.mana_regen_rate = rate
        logger.debug(f"Mana regen rate set to {rate}")

    def reset_mana_regen_rate(self) -> None:
        """Reset mana regeneration rate to the base value."""
        self.mana_regen_rate = self.base_mana_regen_rate
        logger.debug(f"Mana regen rate reset to base: {self.base_mana_regen_rate}")

    def get_mana_percent(self) -> float:
        """
        Get current mana as a percentage (0.0 to 1.0).

        Returns:
            float: Current mana percentage.
        """
        if self.max_mana <= 0:
            return 0.0
        return max(0.0, min(1.0, self.current_mana / self.max_mana))

    def is_full(self) -> bool:
        """Check if mana is at maximum."""
        return self.current_mana >= self.max_mana

    def is_empty(self) -> bool:
        """Check if mana is at zero."""
        return self.current_mana <= 0

    def has_enough_mana(self, amount: float) -> bool:
        """
        Check if there's enough mana for an action without consuming it.

        Args:
            amount (float): Amount of mana needed.

        Returns:
            bool: True if there's enough mana.
        """
        return self.current_mana >= amount

    def get_consume_segments(self) -> list:
        """Return the list of currently animating crumble segments.

        Each segment exposes ``start_norm``, ``end_norm`` (0..1), ``elapsed``
        (seconds), ``progress`` (0..1) and a ``dust`` list of particle dicts.
        The HUD uses this list to render the fading, dust-emitting overlay.

        Returns:
            list[_ConsumeSegment]: A list of active crumble animations.
        """
        return self._consume_segments
