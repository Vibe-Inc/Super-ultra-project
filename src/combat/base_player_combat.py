import math
import pygame
import random
from src.entities.projectile import Arrow

class PlayerCombatController:
    """
    Handles player combat mechanics, including weapon stat synchronization,
    aiming calculations, melee attacks, and projectile spawning.

    Attributes:
        game (State):
            Reference to the main game state containing the player and world data.

    Methods:
        __init__(game_state):
            Initialize the player combat controller.
        get_equipped_weapon():
            Retrieve the weapon item currently selected in the player's hotbar.
            Returns:
                Item | None: The equipped weapon, or None if no weapon is selected.
        sync_weapon_stats():
            Update the player character's attack damage, range, and cooldown based on the equipped weapon.
        get_attack_direction():
            Get the current forward-facing direction of the player character.
            Returns:
                pygame.Vector2: The forward direction vector.
        get_attack_origin():
            Get the center coordinates of the player character used as the origin for attacks.
            Returns:
                pygame.Vector2: The attack origin point.
        get_mouse_aim_direction(mouse_pos):
            Calculate the normalized direction vector from the attack origin to the mouse position.
            Args:
                mouse_pos (tuple[int, int]): The current screen coordinates of the mouse.
            Returns:
                pygame.Vector2: The normalized aiming direction.
        clamp_direction_to_cone(aim_dir, forward_dir, half_angle_deg):
            Restrict the attack direction to remain within a specific angle cone relative to the character's forward direction.
            Args:
                aim_dir (pygame.Vector2): The intended aiming direction.
                forward_dir (pygame.Vector2): The current forward direction of the character.
                half_angle_deg (float): Half of the total allowed cone angle in degrees.
            Returns:
                pygame.Vector2: The clamped direction vector.
        spawn_arrow(weapon, direction):
            Instantiate a projectile entity and add it to the game state's active projectiles.
            Args:
                weapon (Item): The ranged weapon used to fire the projectile.
                direction (pygame.Vector2): The normalized direction vector for the projectile.
        handle_player_attack(mouse_pos):
            Execute the combat action (melee swing or ranged shot) directed at the specified coordinates.
            Args:
                mouse_pos (tuple[int, int]): The target coordinates for the attack.
    """
    def __init__(self, game_state):
        """Initialize the player combat controller.

        Args:
            game_state (State): The main game state containing the player and world data.
        """
        self.game = game_state

    def get_equipped_weapon(self):
        """Retrieve the weapon item currently selected in the player's hotbar.

        Returns:
            Item | None: The equipped weapon, or None if no weapon is selected.
        """
        if not getattr(self.game, 'hotbar', None):
            return None
            
        active_index = self.game.hotbar.active_slot_index
        slot = self.game.hotbar.items[active_index][0]
        
        if slot:
            item, count = slot
            if getattr(item, "type", None) == "weapon":
                return item
        return None

    def sync_weapon_stats(self):
        """Update the player character's attack damage, range, and cooldown based on the equipped weapon.

        Handles broken weapons by reverting to bare-handed fallback stats.
        Also exposes the equipped weapon on the character for on-hit enchantments.
        """
        weapon = self.get_equipped_weapon()
        self.game.equipped_weapon = weapon

        char = self.game.character
        # Expose the equipped weapon to the character so on-hit enchantments
        # (Flaming Sword, etc.) can be applied to enemies that get struck.
        char.equipped_weapon = weapon

        if weapon:
            # Broken weapons revert to the bare-handed fallback so the
            # player can't keep swinging a 0-durability sword for full
            # damage.  A broken weapon still occupies the slot visually
            # until the next ``_damage_equipped_weapon`` call removes
            # it (see ``handle_player_attack``).
            if getattr(weapon, "is_broken", lambda: False)():
                char.attack_damage = max(1, char.base_attack_damage // 2)
                char.attack_cooldown = char.base_attack_cooldown
                char.attack_range = char.base_attack_range
            else:
                # ``get_effective_damage`` is provided by ``DurabilityMixin``;
                # fall back to the raw damage attribute for items that
                # somehow lack the mixin.
                base_dmg = weapon.damage
                eff = getattr(weapon, "get_effective_damage", None)
                char.attack_damage = eff(base_dmg) if callable(eff) else base_dmg
                char.attack_cooldown = getattr(weapon, "cooldown", char.base_attack_cooldown)
                if getattr(weapon, "weapon_class", "melee") != "bow":
                    char.attack_range = getattr(weapon, "range", char.base_attack_range)
                else:
                    char.attack_range = char.base_attack_range
        else:
            char.attack_damage = char.base_attack_damage
            char.attack_range = char.base_attack_range
            char.attack_cooldown = char.base_attack_cooldown

    def _damage_equipped_weapon(self, amount: int = 1) -> bool:
        """Wear down the weapon currently in the active hotbar slot.

        Used by the combat code on every successful hit/shot.  When the
        weapon breaks it is removed from the hotbar and the player's
        combat stats are re-synced (so the next click uses fists).  The
        ``True`` return value signals a break, which the caller can use
        to fire UI feedback.
        """
        weapon = self.get_equipped_weapon()
        if weapon is None:
            return False
        apply = getattr(weapon, "apply_durability_damage", None)
        if not callable(apply):
            return False
        broke = bool(apply(amount))
        if not broke:
            # Re-sync so any in-flight damage scaling picks up the
            # updated durability (e.g. the next attack deals 95% damage
            # instead of 100%).
            self.sync_weapon_stats()
            return False
        # Broken -> clear the slot and refresh stats.
        try:
            inv_manager = getattr(self.game.app, "INV_manager", None)
            hotbar = getattr(inv_manager, "hotbar", None) if inv_manager else None
            if hotbar is not None:
                active = getattr(hotbar, "active_slot_index", None)
                if active is not None and 0 <= active < len(hotbar.items):
                    hotbar.items[active][0] = None
        except Exception:
            pass
        self.sync_weapon_stats()
        return True

    def get_attack_direction(self):
        """Get the current forward-facing direction of the player character.

        Returns:
            pygame.Vector2: The forward direction vector.
        """
        return self.game.character.get_forward_direction()

    def get_attack_origin(self):
        """Get the center coordinates of the player character used as the origin for attacks.

        Returns:
            pygame.Vector2: The attack origin point.
        """
        return self.game.character.get_center()

    def get_mouse_aim_direction(self, mouse_pos):
        """Calculate the normalized direction vector from the attack origin to the mouse position.

        Args:
            mouse_pos (tuple[int, int]): The current screen coordinates of the mouse.

        Returns:
            pygame.Vector2: The normalized aiming direction.
        """
        origin = self.get_attack_origin()
        direction = pygame.Vector2(mouse_pos) - origin
        if direction.length_squared() == 0:
            return self.get_attack_direction()
        return direction.normalize()

    def clamp_direction_to_cone(self, aim_dir, forward_dir, half_angle_deg):
        """Restrict the attack direction to remain within a specific angle cone.

        Args:
            aim_dir (pygame.Vector2): The intended aiming direction.
            forward_dir (pygame.Vector2): The current forward direction of the character.
            half_angle_deg (float): Half of the total allowed cone angle in degrees.

        Returns:
            pygame.Vector2: The clamped direction vector.
        """
        if half_angle_deg <= 0:
            return pygame.Vector2(forward_dir)

        if forward_dir.length_squared() == 0:
            forward_dir = pygame.Vector2(1, 0)
        else:
            forward_dir = forward_dir.normalize()

        if aim_dir.length_squared() == 0:
            return pygame.Vector2(forward_dir)

        aim_dir = aim_dir.normalize()
        cross = forward_dir.x * aim_dir.y - forward_dir.y * aim_dir.x
        dot = forward_dir.dot(aim_dir)
        angle = math.degrees(math.atan2(cross, dot))

        if abs(angle) <= half_angle_deg:
            return aim_dir

        return forward_dir.rotate(half_angle_deg if angle > 0 else -half_angle_deg)

    def spawn_arrow(self, weapon, direction):
        """Instantiate a projectile entity and add it to the game state's active projectiles.

        Args:
            weapon (Item): The ranged weapon used to fire the projectile.
            direction (pygame.Vector2): The normalized direction vector for the projectile.
        """
        direction = pygame.Vector2(direction)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        else:
            direction = direction.normalize()

        spawn_pos = self.get_attack_origin() + direction * 40
        speed = getattr(weapon, "projectile_speed", 800) or 800
        max_range = getattr(weapon, "range", 500)
        damage = getattr(weapon, "damage", self.game.character.attack_damage)
        
        self.game.projectiles.append(Arrow(spawn_pos, direction, speed, max_range, damage))

    def handle_player_attack(self, mouse_pos):
        """Execute the combat action (melee swing or ranged shot) directed at the specified coordinates.

        Args:
            mouse_pos (tuple[int, int]): The target coordinates for the attack.
        """
        weapon = self.game.equipped_weapon or self.get_equipped_weapon()
        if not weapon:
            return

        # Broken weapons can't be swung/fired.  We resync stats so a
        # broken weapon the player just placed in the hotbar immediately
        # reverts to bare-handed damage output.
        if getattr(weapon, "is_broken", lambda: False)():
            self.sync_weapon_stats()
            return

        aim_dir = self.get_mouse_aim_direction(mouse_pos)
        if aim_dir.length_squared() == 0:
            return

        char = self.game.character

        forward_dir = self.get_attack_direction()
        if forward_dir.length_squared() > 0:
            forward_dir = forward_dir.normalize()
        else:
            forward_dir = pygame.Vector2(1, 0)

        cross = forward_dir.x * aim_dir.y - forward_dir.y * aim_dir.x
        dot = forward_dir.dot(aim_dir)
        angle = math.degrees(math.atan2(cross, dot))

        allowed_angle = 120.0
        if abs(angle) > allowed_angle:
            return

        if getattr(weapon, "weapon_class", "melee") == "ranged":
            if not char.can_attack():
                return
            char.start_attack(show_slash=False)
            spread = float(getattr(weapon, "spread_degrees", 4.0))
            if spread:
                aim_dir = aim_dir.rotate(random.uniform(-spread, spread))
            self.spawn_arrow(weapon, aim_dir)
            # Ranged weapons take 1 durability per shot.  If the bow
            # breaks we still let the just-fired arrow fly (it's
            # already in flight) but the next click will be blocked
            # by the broken-check above.
            self._damage_equipped_weapon(1)
            return

        if not char.can_attack():
            return

        combat_style = getattr(weapon, "combat_style", "sword")

        if combat_style == "mace":
            char.attack_mace(self.game.enemies, aim_direction=aim_dir)
        elif combat_style == "axe":
            char.attack_axe(self.game.enemies, aim_direction=aim_dir)
        elif combat_style == "spear":
            char.attack_spear(self.game.enemies, aim_direction=aim_dir)
        elif combat_style == "war_hammer":
            char.attack_war_hammer(self.game.enemies, aim_direction=aim_dir)
        else:
            cone_degrees = float(getattr(weapon, "cone_degrees", 90.0))
            char.attack(self.game.enemies, aim_direction=aim_dir, cone_degrees=cone_degrees)

        # Melee weapons take 1 durability per successful swing (a single
        # swing, regardless of how many enemies it hits -- otherwise a
        # war-hammer in a crowd would tear through durability in seconds).
        # The actual hit-test result isn't visible here, so we just charge
        # the swing; if the player whiffs into empty air that's still a
        # use of the weapon.
        self._damage_equipped_weapon(1)