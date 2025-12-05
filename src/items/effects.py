import pygame

class Effect:
    """
    Base class for all item effects.
    """
    def __init__(self, duration):
        self.duration = duration
        self.timer = 0
        self.is_finished = False

    def update(self, dt, target):
        self.timer += dt
        if self.timer >= self.duration:
            self.is_finished = True
            self.on_end(target)
        else:
            self.apply(dt, target)

    def apply(self, dt, target):
        pass

    def on_end(self, target):
        pass

class RegenerationEffect(Effect):
    """
    Restores HP over time.
    """
    def __init__(self, duration, amount_per_sec):
        super().__init__(duration)
        self.amount_per_sec = amount_per_sec
        self.accumulator = 0.0

    def apply(self, dt, target):
        self.accumulator += self.amount_per_sec * dt
        if self.accumulator >= 1:
            heal = int(self.accumulator)
            target.hp = min(100, target.hp + heal)
            self.accumulator -= heal

class PoisonEffect(Effect):
    """
    Deals damage over time.
    """
    def __init__(self, duration, damage_per_sec):
        super().__init__(duration)
        self.damage_per_sec = damage_per_sec
        self.accumulator = 0.0

    def apply(self, dt, target):
        self.accumulator += self.damage_per_sec * dt
        if self.accumulator >= 1:
            dmg = int(self.accumulator)
            target.take_damage(dmg)
            self.accumulator -= dmg

class ConfusionEffect(Effect):
    """
    Inverts player controls.
    """
    def __init__(self, duration):
        super().__init__(duration)
        self.started = False

    def apply(self, dt, target):
        if not self.started:
            target.confused = True
            self.started = True

    def on_end(self, target):
        target.confused = False

class DizzinessEffect(Effect):
    """
    Causes visual dizziness (blur/shake).
    """
    def __init__(self, duration):
        super().__init__(duration)
        self.started = False

    def apply(self, dt, target):
        if not self.started:
            target.dizzy = True
            self.started = True

    def on_end(self, target):
        target.dizzy = False
