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
        """Update the player character's attack damage, range, and cooldown based on the equipped weapon
        and world scale multipliers.  Without a weapon the player cannot attack.
        """
        weapon = self.get_equipped_weapon()
        self.game.equipped_weapon = weapon

        char = self.game.character
        char.equipped_weapon = weapon

        ws = getattr(self.game, 'world_scale', None)

        if weapon:
            char._combat_style = getattr(weapon, "combat_style", "sword")
            if getattr(weapon, "is_broken", lambda: False)():
                char.attack_damage = 0
                char.attack_cooldown = char.base_attack_cooldown
                char.attack_range = 0
            else:
                base_dmg = weapon.damage
                eff = getattr(weapon, "get_effective_damage", None)
                weapon_damage = eff(base_dmg) if callable(eff) else base_dmg
                if ws:
                    char.attack_damage = int(char.base_attack_damage * ws.player_damage_mult() + weapon_damage)
                else:
                    char.attack_damage = weapon_damage

                char.attack_cooldown = getattr(weapon, "cooldown", char.base_attack_cooldown)

                wc = getattr(weapon, "weapon_class", "melee")
                weapon_range = getattr(weapon, "range", char.base_attack_range)
                if ws:
                    range_mult = ws.player_ranged_range_mult() if wc == "bow" else ws.player_melee_range_mult()
                    char.attack_range = max(1, int(weapon_range * range_mult))
                else:
                    char.attack_range = weapon_range
        else:
            char.attack_damage = 0
            char.attack_range = 0
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
        """Instantiate a projectile entity and add it to the game state's active projectiles."""
        direction = pygame.Vector2(direction)
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        else:
            direction = direction.normalize()

        spawn_pos = self.get_attack_origin() + direction * 40
        speed = getattr(weapon, "projectile_speed", 800) or 800
        max_range = getattr(weapon, "range", 500)
        damage = getattr(weapon, "damage", self.game.character.attack_damage)

        ws = getattr(self.game, 'world_scale', None)
        execute_chance = 0.10 if (ws and ws.has_ability('execute')) else 0.0
        self.game.projectiles.append(Arrow(spawn_pos, direction, speed, max_range, damage, execute_chance=execute_chance))

    def _aim_dir_valid(self, aim_dir, char):
        forward_dir = self.get_attack_direction()
        if forward_dir.length_squared() > 0:
            forward_dir = forward_dir.normalize()
        else:
            forward_dir = pygame.Vector2(1, 0)
        cross = forward_dir.x * aim_dir.y - forward_dir.y * aim_dir.x
        dot = forward_dir.dot(aim_dir)
        angle = math.degrees(math.atan2(cross, dot))
        allowed_angle = 120.0
        return abs(angle) <= allowed_angle

    def _execute_melee_attack(self, char, aim_dir):
        weapon = self.game.equipped_weapon or self.get_equipped_weapon()
        combat_style = getattr(weapon, "combat_style", "sword") if weapon else "sword"
        if combat_style == "mace":
            char.attack_mace(self.game.enemies, aim_direction=aim_dir)
        elif combat_style == "axe":
            char.attack_axe(self.game.enemies, aim_direction=aim_dir)
        elif combat_style == "spear":
            char.attack_spear(self.game.enemies, aim_direction=aim_dir)
        elif combat_style == "war_hammer":
            char.attack_war_hammer(self.game.enemies, aim_direction=aim_dir)
        else:
            cone_degrees = float(getattr(weapon, "cone_degrees", 90.0)) if weapon else 90.0
            char.attack(self.game.enemies, aim_direction=aim_dir, cone_degrees=cone_degrees)
        self._damage_equipped_weapon(1)

    def handle_player_attack(self, mouse_pos):
        """Execute the combat action (melee swing or ranged shot) directed at the specified coordinates.

        Args:
            mouse_pos (tuple[int, int]): The target coordinates for the attack.
        """
        weapon = self.game.equipped_weapon or self.get_equipped_weapon()
        if not weapon:
            return

        if getattr(weapon, "is_broken", lambda: False)():
            self.sync_weapon_stats()
            return

        aim_dir = self.get_mouse_aim_direction(mouse_pos)
        if aim_dir.length_squared() == 0:
            return

        char = self.game.character

        if not self._aim_dir_valid(aim_dir, char):
            return

        if getattr(weapon, "weapon_class", "melee") == "ranged":
            if not char.can_attack():
                return
            char.start_attack(show_slash=False)
            spread = float(getattr(weapon, "spread_degrees", 4.0))
            if spread:
                aim_dir = aim_dir.rotate(random.uniform(-spread, spread))
            self.spawn_arrow(weapon, aim_dir)
            self._damage_equipped_weapon(1)
            return

        if not char.can_attack():
            return

        # Normal attack — use charge system: quick release = normal, held = charged
        char.start_charge(mouse_pos=mouse_pos)

    def handle_player_attack_release(self, mouse_pos):
        """Called when LMB is released. Releases the charge (normal or charged attack)."""
        char = self.game.character
        if not char.is_charging:
            return

        weapon = self.game.equipped_weapon or self.get_equipped_weapon()
        if not weapon:
            char.cancel_charge()
            return

        aim_dir = self.get_mouse_aim_direction(mouse_pos)
        if aim_dir.length_squared() == 0:
            char.cancel_charge()
            return

        if not self._aim_dir_valid(aim_dir, char):
            char.cancel_charge()
            return

        char.release_charge(self.game.enemies, aim_direction=aim_dir, game_state=self.game)
        self._damage_equipped_weapon(1)

    def handle_fast_attack(self, mouse_pos):
        """Execute a fast attack (different key). Requires world scale level 45."""
        ws = getattr(self.game, 'world_scale', None)
        if ws and not ws.has_ability('fast_attack'):
            return

        weapon = self.game.equipped_weapon or self.get_equipped_weapon()
        if not weapon:
            return

        if getattr(weapon, "is_broken", lambda: False)():
            self.sync_weapon_stats()
            return

        if getattr(weapon, "weapon_class", "melee") != "melee":
            return

        aim_dir = self.get_mouse_aim_direction(mouse_pos)
        if aim_dir.length_squared() == 0:
            return

        char = self.game.character
        if not self._aim_dir_valid(aim_dir, char):
            return
        if not char.can_attack():
            return

        char.attack_fast(self.game.enemies, aim_direction=aim_dir)
        self._damage_equipped_weapon(1)

    def handle_throw_weapon(self, mouse_pos):
        """Throw the weapon from the active hotbar slot toward the cursor."""
        aim_dir = self.get_mouse_aim_direction(mouse_pos)
        if aim_dir.length_squared() == 0:
            return

        char = self.game.character
        char.throw_weapon(self.game.enemies, aim_direction=aim_dir, game_state=self.game)