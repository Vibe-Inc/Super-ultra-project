import math
import pygame
from src.core.logger import logger


class NatureSpirit:
    """
    Summoned nature spirit that follows the player and attacks nearby enemies.

    Attributes:
        pos (pygame.Vector2): Current position.
        player (Character): Reference to the player character.
        damage (int): Damage per attack.
        attack_cooldown (float): Seconds between attacks.
        duration (float): Total lifetime in seconds.
        follow_distance (float): Ideal distance from player.
        attack_range (float): Max distance to target enemies.
        alive (bool): Whether the spirit is active.
        timer (float): Current lifetime.
        attack_timer (float): Cooldown tracker.
        animation_time (float): Visual timer.
        target (Enemy or None): Current attack target.
    """
    def __init__(self, pos, player, damage=15, duration=10.0, attack_range=300.0,
                 follow_distance=60.0, attack_cooldown=1.2):
        self.pos = pygame.Vector2(pos)
        self.player = player
        self.damage = damage
        self.duration = duration
        self.attack_range = attack_range
        self.follow_distance = follow_distance
        self.attack_cooldown = attack_cooldown
        self.alive = True
        self.timer = 0.0
        self.attack_timer = 0.0
        self.animation_time = 0.0
        self.target = None
        self.speed = 180.0

        # Visual
        self.trail = []
        self.trail_length = 8
        self.glow_pulse = 0.0

    def get_rect(self):
        return pygame.Rect(int(self.pos.x) - 12, int(self.pos.y) - 12, 24, 24)

    def get_center(self):
        return pygame.Vector2(self.pos.x, self.pos.y)

    def update(self, dt, enemies):
        if not self.alive:
            return

        self.timer += dt
        self.attack_timer += dt
        self.animation_time += dt
        self.glow_pulse = (math.sin(self.animation_time * 3) + 1.0) * 0.5

        # Check duration
        if self.timer >= self.duration:
            self.alive = False
            logger.info("Nature Spirit faded away.")
            return

        # Trail
        self.trail.append(pygame.Vector2(self.pos))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)

        # Movement toward player if too far
        player_center = self.player.get_center()
        to_player = player_center - self.pos
        dist_to_player = to_player.length()

        if dist_to_player > self.follow_distance + 20:
            if dist_to_player > 0:
                move = to_player.normalize() * self.speed * dt
                self.pos += move
        elif dist_to_player < self.follow_distance - 20:
            if dist_to_player > 0:
                move = -to_player.normalize() * self.speed * dt * 0.5
                self.pos += move

        # Find target
        self.target = None
        best_dist = self.attack_range * self.attack_range
        for enemy in enemies:
            if enemy.is_dead():
                continue
            e_center = pygame.Vector2(enemy.get_rect().center)
            d2 = (e_center - self.pos).length_squared()
            if d2 < best_dist:
                best_dist = d2
                self.target = enemy

        # Attack target
        if self.target and self.attack_timer >= self.attack_cooldown:
            self.attack_timer = 0.0
            self._attack(self.target, enemies)

    def _attack(self, target, enemies):
        """Fire a nature bolt at the target."""
        e_center = pygame.Vector2(target.get_rect().center)
        target.take_damage(self.damage)
        logger.info(f"Nature Spirit attacked {target.__class__.__name__} for {self.damage} damage!")
        self._spawn_attack_visuals(e_center, enemies)

    def _spawn_attack_visuals(self, target_pos, enemies):
        """Spawn a nature bolt projectile that travels to the target."""
        game_state = getattr(self.player, "game_state", None)
        if game_state is not None:
            direction = target_pos - self.pos
            if direction.length_squared() > 0:
                direction = direction.normalize()
            from src.entities.projectile import NatureBolt
            game_state.projectiles.append(
                NatureBolt(self.get_center(), direction, 400.0, 400.0, 0, target_pos)
            )

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)

        # Fade out in last 2 seconds
        remaining = max(0, self.duration - self.timer)
        fade_alpha = min(255, int(255 * (remaining / 2.0))) if remaining < 2.0 else 255

        # Trail
        for i, pos in enumerate(self.trail):
            alpha = int(80 * (i / len(self.trail)) * fade_alpha / 255)
            radius = int(3 + 4 * (i / len(self.trail)))
            t_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(t_surf, (100, 255, 120, alpha), (radius, radius), radius)
            screen.blit(t_surf, (pos.x - radius - camera_offset.x, pos.y - radius - camera_offset.y))

        # Outer glow
        glow_size = int(20 + 6 * self.glow_pulse)
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        for r in range(glow_size, 0, -4):
            a = int(40 * (1 - r / glow_size) * fade_alpha / 255)
            pygame.draw.circle(glow_surf, (80, 255, 100, a), (glow_size, glow_size), r)
        screen.blit(glow_surf, (cx - glow_size, cy - glow_size))

        # Spirit body (wispy orb)
        body_r = 10 + 3 * self.glow_pulse
        body_surf = pygame.Surface((int(body_r * 2), int(body_r * 2)), pygame.SRCALPHA)
        pygame.draw.circle(body_surf, (180, 255, 200, int(200 * fade_alpha / 255)),
                           (int(body_r), int(body_r)), int(body_r))
        pygame.draw.circle(body_surf, (220, 255, 230, int(160 * fade_alpha / 255)),
                           (int(body_r), int(body_r)), max(1, int(body_r * 0.6)))
        pygame.draw.circle(body_surf, (255, 255, 255, int(120 * fade_alpha / 255)),
                           (int(body_r), int(body_r)), max(1, int(body_r * 0.3)))
        screen.blit(body_surf, (cx - int(body_r), cy - int(body_r)))

        # Drifting sparkles
        import random as rnd
        for _ in range(3):
            sx = cx + rnd.uniform(-15, 15)
            sy = cy + rnd.uniform(-15, 15) + math.sin(self.animation_time * 2 + _) * 5
            sp_size = rnd.randint(1, 2)
            sp_surf = pygame.Surface((sp_size * 2, sp_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(sp_surf, (200, 255, 200, int(150 * fade_alpha / 255)),
                               (sp_size, sp_size), sp_size)
            screen.blit(sp_surf, (int(sx) - sp_size, int(sy) - sp_size))
