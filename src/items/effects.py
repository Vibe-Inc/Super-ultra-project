import pygame

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

Effect_list = {
    "regeneration": RegenerationEffect,
    "poison": PoisonEffect,
    "confusion": ConfusionEffect,
    "dizziness": DizzinessEffect
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
