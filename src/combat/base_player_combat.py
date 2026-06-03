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
        self.game = game_state

    def get_equipped_weapon(self):
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
        weapon = self.get_equipped_weapon()
        self.game.equipped_weapon = weapon

        char = self.game.character
        # Expose the equipped weapon to the character so on-hit enchantments
        # (Flaming Sword, etc.) can be applied to enemies that get struck.
        char.equipped_weapon = weapon

        if weapon:
            char.attack_damage = weapon.damage
            char.attack_cooldown = getattr(weapon, "cooldown", char.base_attack_cooldown)
            if getattr(weapon, "weapon_class", "melee") != "bow":
                char.attack_range = getattr(weapon, "range", char.base_attack_range)
            else:
                char.attack_range = char.base_attack_range
        else:
            char.attack_damage = char.base_attack_damage
            char.attack_range = char.base_attack_range
            char.attack_cooldown = char.base_attack_cooldown

    def get_attack_direction(self):
        return self.game.character.get_forward_direction()

    def get_attack_origin(self):
        return self.game.character.get_center()

    def get_mouse_aim_direction(self, mouse_pos):
        origin = self.get_attack_origin()
        direction = pygame.Vector2(mouse_pos) - origin
        if direction.length_squared() == 0:
            return self.get_attack_direction()
        return direction.normalize()

    def clamp_direction_to_cone(self, aim_dir, forward_dir, half_angle_deg):
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
        weapon = self.game.equipped_weapon or self.get_equipped_weapon()
        if not weapon:
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
            return

        if not char.can_attack():
            return

        cone_degrees = float(getattr(weapon, "cone_degrees", 90.0))
        char.attack(self.game.enemies, aim_direction=aim_dir, cone_degrees=cone_degrees)