"""
ManaSystem component for managing the player's mana resource.

Handles mana storage, regeneration over time, consumption, and max mana cap management.
"""

from src.core.logger import logger


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
        
    Methods:
        update(dt): Update mana regeneration over time.
        consume_mana(amount): Consume mana, returns True if successful.
        restore_mana(amount): Restore mana up to max cap.
        increase_max_mana(amount): Increase the max mana cap.
        set_mana_regen_rate(rate): Set a custom mana regeneration rate.
        reset_mana_regen_rate(): Reset to base regeneration rate.
        get_mana_percent(): Get current mana as a percentage (0.0-1.0).
        is_full(): Check if mana is at maximum.
        is_empty(): Check if mana is at zero.
    """
    
    def __init__(self, max_mana: int = 100, mana_regen_rate: float = 10.0, 
                 mana_regen_delay: float = 0.5):
        """
        Initialize the ManaSystem.
        
        Args:
            max_mana (int): Maximum mana cap. Default is 100.
            mana_regen_rate (float): Mana regenerated per second. Default is 10.0.
            mana_regen_delay (float): Delay before regeneration starts after use. Default is 0.5s.
        """
        self.max_mana = max_mana
        self.current_mana = float(max_mana)
        self.mana_regen_rate = mana_regen_rate
        self.base_mana_regen_rate = mana_regen_rate
        self.mana_regen_delay = mana_regen_delay
        self._regen_timer = 0.0
        self._is_regen_paused = False
        
        logger.debug(f"ManaSystem initialized: max_mana={max_mana}, regen_rate={mana_regen_rate}")
    
    def update(self, dt: float) -> None:
        """
        Update mana regeneration over time.
        
        Args:
            dt (float): Delta time in seconds since last update.
        """
        # If mana is full, no need to regenerate
        if self.current_mana >= self.max_mana:
            self.current_mana = float(self.max_mana)
            self._regen_timer = 0.0
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
    
    def consume_mana(self, amount: float) -> bool:
        """
        Consume mana if enough is available.
        
        Args:
            amount (float): Amount of mana to consume.
            
        Returns:
            bool: True if enough mana was available and consumed, False otherwise.
        """
        if amount <= 0:
            return True
            
        if self.current_mana >= amount:
            self.current_mana -= amount
            self._regen_timer = 0.0
            self._is_regen_paused = True
            logger.debug(f"Consumed {amount:.1f} mana. Mana: {int(self.current_mana)}/{self.max_mana}")
            return True
        
        logger.debug(f"Not enough mana to consume {amount}. Current: {int(self.current_mana)}")
        return False
    
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