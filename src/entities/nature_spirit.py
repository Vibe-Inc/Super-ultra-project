import math
import random
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

        self.trail = []
        self.trail_length = 10
        self.glow_pulse = 0.0
        self.orbit_angle = random.uniform(0, math.pi * 2)
        self.orbit_particles = []

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
        self.glow_pulse = 0.5 + 0.5 * math.sin(self.animation_time * 3)

        if self.timer >= self.duration:
            self.alive = False
            logger.info("Nature Spirit faded away.")
            return

        self.trail.append(pygame.Vector2(self.pos))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)

        # Orbit around player
        player_center = self.player.get_center()
        to_player = player_center - self.pos
        dist_to_player = to_player.length()

        self.orbit_angle += dt * 1.5

        if dist_to_player > self.follow_distance + 30:
            goal = player_center + pygame.Vector2(
                math.cos(self.orbit_angle), math.sin(self.orbit_angle)
            ) * self.follow_distance
        elif dist_to_player < self.follow_distance - 20:
            goal = player_center
        else:
            goal = player_center + pygame.Vector2(
                math.cos(self.orbit_angle), math.sin(self.orbit_angle)
            ) * self.follow_distance

        move_vec = goal - self.pos
        if move_vec.length_squared() > 0:
            self.pos += move_vec.normalize() * self.speed * dt

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

        if self.target and self.attack_timer >= self.attack_cooldown:
            self.attack_timer = 0.0
            self._attack(self.target, enemies)

        self._update_orbit_particles(dt)

    def _update_orbit_particles(self, dt):
        spawn_count = max(1, int(6 * dt))
        for _ in range(spawn_count):
            angle = random.uniform(0, math.pi * 2)
            self.orbit_particles.append({
                "angle": angle,
                "dist": random.uniform(15, 25),
                "max_life": (ml := random.uniform(0.4, 0.8)),
                "life": ml,
                "size": random.uniform(1.5, 3.0),
                "color": random.choice([
                    (100, 255, 120), (160, 255, 140),
                    (60, 220, 80), (200, 255, 180),
                ]),
            })
        for p in self.orbit_particles[:]:
            p["angle"] += dt * 2.0
            p["life"] -= dt
            if p["life"] <= 0:
                self.orbit_particles.remove(p)

    def _attack(self, target, enemies):
        e_center = pygame.Vector2(target.get_rect().center)
        target.take_damage(self.damage)
        logger.info(f"Nature Spirit attacked {target.__class__.__name__} for {self.damage} damage!")
        self._spawn_attack_visuals(e_center, enemies)

    def _spawn_attack_visuals(self, target_pos, enemies):
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
        t = self.animation_time

        remaining = max(0, self.duration - self.timer)
        fade = min(255, int(255 * (remaining / 2.0))) if remaining < 2.0 else 255

        # Trail
        for i, pos in enumerate(self.trail):
            alpha = int(80 * (i / len(self.trail)) * fade / 255)
            radius = int(2 + 4 * (i / len(self.trail)))
            t_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(t_surf, (60, 220, 60, alpha), (radius, radius), radius)
            screen.blit(t_surf, (pos.x - radius - camera_offset.x, pos.y - radius - camera_offset.y))

        # Orbiting leaf particles
        for p in self.orbit_particles:
            life_r = min(1.0, p["life"] / p["max_life"]) if p["max_life"] > 0 else 0
            if life_r <= 0:
                continue
            px = cx + math.cos(p["angle"]) * p["dist"]
            py = cy + math.sin(p["angle"]) * p["dist"]
            alpha = int(180 * life_r * fade / 255)
            size = max(1, int(p["size"] * life_r))
            r, g, b = p["color"]
            leaf_surf = pygame.Surface((size * 2, size), pygame.SRCALPHA)
            pygame.draw.ellipse(leaf_surf, (r, g, b, alpha), (0, 0, size * 2, size))
            screen.blit(leaf_surf, (int(px) - size, int(py) - size // 2))

        # Outer glow
        glow_size = int(22 + 8 * self.glow_pulse)
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        for r in range(glow_size, 0, -4):
            a = int(35 * (1 - r / glow_size) * fade / 255)
            pygame.draw.circle(glow_surf, (60, 220, 80, a), (glow_size, glow_size), r)
        screen.blit(glow_surf, (cx - glow_size, cy - glow_size))

        # Spirit body — layered wisp
        body_r = 10 + 4 * self.glow_pulse
        body_surf = pygame.Surface((int(body_r * 2) + 4, int(body_r * 2) + 4), pygame.SRCALPHA)
        bc = int(body_r) + 2
        # Outer layer
        pygame.draw.circle(body_surf, (80, 220, 80, int(180 * fade / 255)),
                           (bc, bc), int(body_r))
        # Mid layer with pulse
        mid_r = max(1, int(body_r * 0.7 + 2 * math.sin(t * 5)))
        pygame.draw.circle(body_surf, (160, 255, 160, int(200 * fade / 255)),
                           (bc, bc), mid_r)
        # Core
        core_r = max(1, int(body_r * 0.35))
        pygame.draw.circle(body_surf, (220, 255, 220, int(180 * fade / 255)),
                           (bc, bc), core_r)
        # Bright center
        pygame.draw.circle(body_surf, (255, 255, 255, int(140 * fade / 255)),
                           (bc - 1, bc - 1), max(1, core_r // 2))
        screen.blit(body_surf, (cx - bc, cy - bc))

        # Drifting sparkles
        for _ in range(3):
            sx = cx + random.uniform(-15, 15)
            sy = cy + random.uniform(-15, 15) + math.sin(t * 2 + _) * 6
            sp_size = random.randint(1, 2)
            sp_alpha = int(150 * fade / 255)
            sp_surf = pygame.Surface((sp_size * 2, sp_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(sp_surf, (200, 255, 200, sp_alpha), (sp_size, sp_size), sp_size)
            screen.blit(sp_surf, (int(sx) - sp_size, int(sy) - sp_size))
