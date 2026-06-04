import pygame
from src.core.logger import logger

class Effect:
    """
    Base class for all item effects.

    Attributes:
        duration (float):
            Total duration of the effect in seconds.
        timer (float):
            Current elapsed time of the effect.
        is_finished (bool):
            Whether the effect has completed its duration.

    Methods:
        update(dt, target):
            Update the effect timer and apply the effect.
        apply(dt, target):
            Apply the effect logic to the target.
        on_end(target):
            Cleanup logic when the effect ends.
    """
    def __init__(self, duration):
        self.duration = duration
        self.timer = 0
        self.is_finished = False
        logger.debug(f"Effect created: {self.__class__.__name__} duration={duration}")

    def update(self, dt, target):
        """
        Update the effect state.

        Args:
            dt (float): Time elapsed since last frame.
            target (Character): The entity affected by this effect.
        """
        self.timer += dt
        if self.timer >= self.duration:
            self.is_finished = True
            self.on_end(target)
        else:
            self.apply(dt, target)

    def apply(self, dt, target):
        """
        Apply the effect's active logic.

        Args:
            dt (float): Time elapsed since last frame.
            target (Character): The entity affected by this effect.
        """
        pass

    def on_end(self, target):
        """
        Perform any cleanup when the effect expires.

        Args:
            target (Character): The entity affected by this effect.
        """
        pass

class RegenerationEffect(Effect):
    """
    Restores HP over time.

    Attributes:
        amount_per_sec (float):
            Amount of HP to restore per second.
        accumulator (float):
            Accumulates fractional HP restoration.
    """
    def __init__(self, duration, amount_per_sec):
        super().__init__(duration)
        self.amount_per_sec = amount_per_sec
        self.accumulator = 0.0

    def apply(self, dt, target):
        """
        Apply regeneration to the target.

        Args:
            dt (float): Time elapsed since last frame.
            target (Character): The entity to heal.
        """
        self.accumulator += self.amount_per_sec * dt
        if self.accumulator >= 1:
            heal = int(self.accumulator)
            target.hp = min(target.max_hp, target.hp + heal)
            self.accumulator -= heal
            logger.debug(f"Regeneration applied {heal} HP to {getattr(target, 'id', type(target))}")

class PoisonEffect(Effect):
    """
    Deals damage over time.

    Attributes:
        damage_per_sec (float):
            Amount of damage to deal per second.
        accumulator (float):
            Accumulates fractional damage.
    """
    def __init__(self, duration, damage_per_sec):
        super().__init__(duration)
        self.damage_per_sec = damage_per_sec
        self.accumulator = 0.0

    def apply(self, dt, target):
        """
        Apply poison damage to the target.

        Args:
            dt (float): Time elapsed since last frame.
            target (Character): The entity to damage.
        """
        self.accumulator += self.damage_per_sec * dt
        if self.accumulator >= 1:
            dmg = int(self.accumulator)
            target.take_damage(dmg, ignore_invulnerability=True)
            self.accumulator -= dmg
            logger.debug(f"Poison dealt {dmg} damage to {getattr(target, 'id', type(target))}")

class BurnEffect(Effect):
    """
    Deals fire damage over time.

    Attributes:
        damage_per_sec (float): Amount of damage to deal per second.
        accumulator (float): Accumulates fractional damage.
    """
    def __init__(self, duration, damage_per_sec):
        super().__init__(duration)
        self.damage_per_sec = damage_per_sec
        self.accumulator = 0.0

    def apply(self, dt, target):
        self.accumulator += self.damage_per_sec * dt
        if self.accumulator >= 1:
            dmg = int(self.accumulator)
            target.take_damage(dmg, ignore_invulnerability=True)
            self.accumulator -= dmg
            logger.debug(f"Burn dealt {dmg} damage to {getattr(target, 'id', type(target))}")

class ConfusionEffect(Effect):
    """
    Inverts player controls for a duration.

    Attributes:
        started (bool):
            Whether the effect has been initialized on the target.
    """
    def __init__(self, duration):
        super().__init__(duration)
        self.started = False

    def apply(self, dt, target):
        """
        Apply confusion (invert controls) to the target.

        Args:
            dt (float): Time elapsed since last frame.
            target (Character): The entity to confuse.
        """
        if not self.started:
            target.confused = True
            self.started = True

    def on_end(self, target):
        """
        Remove confusion from the target.

        Args:
            target (Character): The entity to restore.
        """
        target.confused = False
        logger.debug(f"ConfusionEffect ended on {getattr(target, 'id', type(target))}")

class DizzinessEffect(Effect):
    """
    Causes visual dizziness (blur/shake) for a duration.

    Attributes:
        started (bool):
            Whether the effect has been initialized on the target.
    """
    def __init__(self, duration):
        super().__init__(duration)
        self.started = False

    def apply(self, dt, target):
        """
        Apply dizziness to the target.

        Args:
            dt (float): Time elapsed since last frame.
            target (Character): The entity to make dizzy.
        """
        if not self.started:
            target.dizzy = True
            self.started = True

    def on_end(self, target):
        """
        Remove dizziness from the target.

        Args:
            target (Character): The entity to restore.
        """
        target.dizzy = False
        logger.debug(f"DizzinessEffect ended on {getattr(target, 'id', type(target))}")

class SlowEffect(Effect):
    """
    Reduces movement speed for a duration.

    Attributes:
        speed_multiplier (float): Multiplier applied to target speed.
        started (bool): Whether the effect has been initialized on the target.
    """
    def __init__(self, duration, speed_multiplier):
        super().__init__(duration)
        self.speed_multiplier = speed_multiplier
        self.started = False

    def apply(self, dt, target):
        if not self.started:
            target.speed_multiplier = min(getattr(target, "speed_multiplier", 1.0), self.speed_multiplier)
            self.started = True

    def on_end(self, target):
        target.speed_multiplier = 1.0
        logger.debug(f"SlowEffect ended on {getattr(target, 'id', type(target))}")

class FreezeEffect(Effect):
    """
    Completely immobilizes the target for a duration.

    Attributes:
        frozen (bool): Whether the freeze has been applied.
    """
    def __init__(self, duration):
        super().__init__(duration)
        self.frozen = False

    def apply(self, dt, target):
        if not self.frozen:
            target.speed_multiplier = 0.0
            self.frozen = True

    def on_end(self, target):
        target.speed_multiplier = 1.0
        self.frozen = False
        logger.debug(f"FreezeEffect ended on {getattr(target, 'id', type(target))}")

class RootEffect(Effect):
    """
    Immobilizes the target with roots for a duration.

    Attributes:
        rooted (bool): Whether the root has been applied.
    """
    def __init__(self, duration):
        super().__init__(duration)
        self.rooted = False

    def apply(self, dt, target):
        if not self.rooted:
            target.speed_multiplier = 0.0
            self.rooted = True

    def on_end(self, target):
        target.speed_multiplier = 1.0
        self.rooted = False
        logger.debug(f"RootEffect ended on {getattr(target, 'id', type(target))}")

# ─── New positive effects ────────────────────────────────────────────────────
class RadiantFortitude(Effect):
    """
    Buff: increases incoming healing and slightly reduces damage taken.
    """
    def __init__(self, duration=30.0, heal_mult=1.2, damage_mult=0.95):
        super().__init__(duration)
        self.heal_mult = heal_mult
        self.damage_mult = damage_mult
        self.started = False

    def apply(self, dt, target):
        if not self.started:
            # store previous values for safe revert
            self._prev_heal = getattr(target, "incoming_healing_mult", 1.0)
            self._prev_damage = getattr(target, "damage_taken_mult", 1.0)
            target.incoming_healing_mult = self._prev_heal * self.heal_mult
            target.damage_taken_mult = self._prev_damage * self.damage_mult
            self.started = True
            logger.debug(f"Applied RadiantFortitude to {getattr(target,'id',type(target))}")

    def on_end(self, target):
        # restore previous values if present
        if hasattr(self, "_prev_heal"):
            target.incoming_healing_mult = getattr(target, "incoming_healing_mult", 1.0) / self.heal_mult
        if hasattr(self, "_prev_damage"):
            target.damage_taken_mult = getattr(target, "damage_taken_mult", 1.0) / self.damage_mult
        logger.debug(f"RadiantFortitude ended on {getattr(target,'id',type(target))}")

class VampiricEdge(Effect):
    """
    Buff: attacks heal the caster for a percentage of damage dealt.
    """
    def __init__(self, duration=20.0, vampiric_pct=0.2):
        super().__init__(duration)
        self.vampiric_pct = vampiric_pct
        self.started = False

    def apply(self, dt, target):
        if not self.started:
            self._prev = getattr(target, "vampiric_pct", 0.0)
            target.vampiric_pct = self.vampiric_pct
            self.started = True
            logger.debug(f"Applied VampiricEdge to {getattr(target,'id',type(target))}")

    def on_end(self, target):
        target.vampiric_pct = max(0.0, getattr(target, "vampiric_pct", 0.0) - self.vampiric_pct)
        logger.debug(f"VampiricEdge ended on {getattr(target,'id',type(target))}")

class KeenInsight(Effect):
    """
    Buff: increases critical chance for duration.
    """
    def __init__(self, duration=20.0, crit_bonus=0.25):
        super().__init__(duration)
        self.crit_bonus = crit_bonus
        self.started = False

    def apply(self, dt, target):
        if not self.started:
            target.crit_chance_bonus = getattr(target, "crit_chance_bonus", 0.0) + self.crit_bonus
            self.started = True
            logger.debug(f"KeenInsight applied to {getattr(target,'id',type(target))}")

    def on_end(self, target):
        target.crit_chance_bonus = max(0.0, getattr(target, "crit_chance_bonus", 0.0) - self.crit_bonus)
        logger.debug(f"KeenInsight ended on {getattr(target,'id',type(target))}")

# =====================================================================
# New effects added to support the new WIP_TEXTURE items.
# =====================================================================

class BleedEffect(Effect):
    """
    Deals physical-style damage over time.

    Attributes:
        damage_per_sec (float): Bleed damage per second.
        accumulator (float): Accumulates fractional damage.
    """
    def __init__(self, duration, damage_per_sec):
        super().__init__(duration)
        self.damage_per_sec = damage_per_sec
        self.accumulator = 0.0

    def apply(self, dt, target):
        self.accumulator += self.damage_per_sec * dt
        if self.accumulator >= 1:
            dmg = int(self.accumulator)
            target.take_damage(dmg, ignore_invulnerability=True)
            self.accumulator -= dmg
            logger.debug(f"Bleed dealt {dmg} damage to {getattr(target, 'id', type(target))}")


class StrengthEffect(Effect):
    """
    Adds a flat damage bonus to attacks for a duration.

    Attributes:
        damage_bonus (int): Flat damage added to every attack.
    """
    def __init__(self, duration, damage_bonus):
        super().__init__(duration)
        self.damage_bonus = int(damage_bonus)
        self.started = False

    def apply(self, dt, target):
        if not self.started:
            target.damage_bonus = getattr(target, "damage_bonus", 0) + self.damage_bonus
            self.started = True
            logger.debug(f"StrengthEffect applied to {getattr(target,'id',type(target))}")

    def on_end(self, target):
        target.damage_bonus = max(0, getattr(target, "damage_bonus", 0) - self.damage_bonus)
        logger.debug(f"StrengthEffect ended on {getattr(target, 'id', type(target))}")

class Momentum(Effect):
    """
    Triggered short damage buff (intended to be applied on kill by combat code).
    Grants a percentage damage increase for the duration.
    """
    def __init__(self, duration=6.0, damage_pct=0.10):
        super().__init__(duration)
        self.damage_pct = damage_pct
        self.started = False
        self._added = 0

    def apply(self, dt, target):
        if not self.started:
            base = getattr(target, "base_attack_damage", getattr(target, "attack_damage", 0))
            self._added = int(base * self.damage_pct)
            target.attack_damage = getattr(target, "attack_damage", base) + self._added
            self.started = True
            logger.debug(f"Momentum applied (+{self._added}) to {getattr(target,'id',type(target))}")

    def on_end(self, target):
        # remove added flat damage
        target.attack_damage = max(0, getattr(target, "attack_damage", 0) - self._added)
        logger.debug(f"Momentum ended on {getattr(target,'id',type(target))}")
class BlindEffect(Effect):
    """
    Reduces aim/accuracy for duration.
    """
    def __init__(self, duration=6.0, accuracy_mult=0.5):
        super().__init__(duration)
        self.accuracy_mult = accuracy_mult
        self.started = False

    def apply(self, dt, target):
        if not self.started:
            self._prev = getattr(target, "accuracy_mult", 1.0)
            target.accuracy_mult = self._prev * self.accuracy_mult
            self.started = True
            logger.debug(f"BlindEffect applied to {getattr(target,'id',type(target))}")

    def on_end(self, target):
        target.accuracy_mult = getattr(target, "accuracy_mult", 1.0) / self.accuracy_mult
        logger.debug(f"BlindEffect ended on {getattr(target,'id',type(target))}")


class HasteEffect(Effect):
    """
    Reduces attack cooldown and increases movement speed for a duration.

    Attributes:
        cooldown_multiplier (float): Multiplier applied to attack cooldown (e.g. 0.7 = 30% faster).
        speed_multiplier (float): Multiplier applied to base speed (e.g. 1.3 = 30% faster).
    """
    def __init__(self, duration, cooldown_multiplier=0.7, speed_multiplier=1.3):
        super().__init__(duration)
        self.cooldown_multiplier = float(cooldown_multiplier)
        self.speed_multiplier = float(speed_multiplier)
        self.started = False

    def apply(self, dt, target):
        if not self.started:
            target.cooldown_multiplier = min(getattr(target, "cooldown_multiplier", 1.0), self.cooldown_multiplier)
            target.speed_multiplier = max(getattr(target, "speed_multiplier", 1.0), self.speed_multiplier)
            self.started = True
            logger.debug(f"HasteEffect applied to {getattr(target,'id',type(target))}")

    def on_end(self, target):
        target.cooldown_multiplier = 1.0
        target.speed_multiplier = 1.0
        logger.debug(f"HasteEffect ended on {getattr(target, 'id', type(target))}")

class WeakenEffect(Effect):
    """
    Reduces damage dealt by the target for duration.
    """
    def __init__(self, duration=8.0, damage_mult=0.8):
        super().__init__(duration)
        self.damage_mult = damage_mult
        self.started = False

    def apply(self, dt, target):
        if not self.started:
            self._prev = getattr(target, "damage_dealt_mult", 1.0)
            target.damage_dealt_mult = self._prev * self.damage_mult
            self.started = True
            logger.debug(f"WeakenEffect applied to {getattr(target,'id',type(target))}")

    def on_end(self, target):
        target.damage_dealt_mult = getattr(target, "damage_dealt_mult", 1.0) / self.damage_mult
        logger.debug(f"WeakenEffect ended on {getattr(target,'id',type(target))}")


class ShieldEffect(Effect):
    """
    Absorbs incoming damage up to a configured amount.

    Attributes:
        absorb_amount (float): Total damage this shield can absorb.
        remaining (float): How much absorption is left after starts.
    """
    def __init__(self, duration, absorb_amount):
        super().__init__(duration)
        self.absorb_amount = float(absorb_amount)
        self.remaining = float(absorb_amount)
        self.started = False

    def apply(self, dt, target):
        if not self.started:
            target.shield = getattr(target, "shield", 0.0) + self.remaining
            self.started = True

    def on_end(self, target):
        target.shield = max(0.0, getattr(target, "shield", 0.0) - self.remaining)
        logger.debug(f"ShieldEffect ended on {getattr(target, 'id', type(target))}")

class CurseEffect(Effect):
    """
    Increases damage taken and reduces resistances while active.
    """
    def __init__(self, duration=12.0, damage_taken_mult=1.25, resist_penalty=0.15):
        super().__init__(duration)
        self.damage_taken_mult = damage_taken_mult
        self.resist_penalty = resist_penalty
        self.started = False
        self._prev_resists = {}

    def apply(self, dt, target):
        if not self.started:
            self._prev = getattr(target, "damage_taken_mult", 1.0)
            target.damage_taken_mult = self._prev * self.damage_taken_mult
            # apply resist penalty to every existing resistance key
            prevs = {}
            for k, v in getattr(target, "resistances", {}).items():
                prevs[k] = v
                target.resistances[k] = max(0.0, v - self.resist_penalty)
            self._prev_resists = prevs
            self.started = True
            logger.debug(f"CurseEffect applied to {getattr(target,'id',type(target))}")

    def on_end(self, target):
        target.damage_taken_mult = getattr(target, "damage_taken_mult", 1.0) / self.damage_taken_mult
        for k, v in self._prev_resists.items():
            target.resistances[k] = v
        logger.debug(f"CurseEffect ended on {getattr(target,'id',type(target))}")


class LethargyEffect(Effect):
    """
    Slows the target and increases their attack cooldown (debuff).

    Attributes:
        speed_multiplier (float): Multiplier applied to base speed.
        cooldown_multiplier (float): Multiplier applied to attack cooldown.
    """
    def __init__(self, duration, speed_multiplier=0.7, cooldown_multiplier=1.4):
        super().__init__(duration)
        self.speed_multiplier = float(speed_multiplier)
        self.cooldown_multiplier = float(cooldown_multiplier)
        self.started = False

    def apply(self, dt, target):
        if not self.started:
            target.speed_multiplier = min(getattr(target, "speed_multiplier", 1.0), self.speed_multiplier)
            target.cooldown_multiplier = max(getattr(target, "cooldown_multiplier", 1.0), self.cooldown_multiplier)
            self.started = True

    def on_end(self, target):
        target.speed_multiplier = 1.0
        target.cooldown_multiplier = 1.0
        logger.debug(f"LethargyEffect ended on {getattr(target, 'id', type(target))}")


Effect_list = {
    "regeneration": RegenerationEffect,
    "poison": PoisonEffect,
    "burn": BurnEffect,
    "confusion": ConfusionEffect,
    "dizziness": DizzinessEffect,
    "slow": SlowEffect,
    "freeze": FreezeEffect,
    "root": RootEffect,
    "radiant_fortitude": RadiantFortitude,
    "vampiric_edge": VampiricEdge,
    "keen_insight": KeenInsight,
    "momentum": Momentum,
    "blind": BlindEffect,
    "weaken": WeakenEffect,
    "curse": CurseEffect,
    # New effects below
    "bleed": BleedEffect,
    "strength": StrengthEffect,
    "haste": HasteEffect,
    "shield": ShieldEffect,
    "lethargy": LethargyEffect,
}

def create_effect(effect_data: dict):
    """
    Factory function to create an effect instance from a dictionary.

    Args:
        effect_data (dict): Dictionary containing effect type and parameters.

    Returns:
        Effect | None: The created effect instance, or None if type is invalid.
    """
    data = effect_data.copy()
    effect_type = data.pop("type", None)
    effect_class = Effect_list.get(effect_type)
    if effect_class:
        return effect_class(**data)
    else:
        return None
