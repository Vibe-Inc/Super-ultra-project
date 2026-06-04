import math
import random
import pygame
from database.effects import BurnEffect, FreezeEffect, SlowEffect, RootEffect
from src.core.logger import logger


class Arrow:
    """
    Physical arrow projectile fired by ranged weapons.

    Attributes:
        pos (pygame.Vector2):
            Current projectile position.
        direction (pygame.Vector2):
            Normalized travel direction.
        speed (float):
            Travel speed in pixels per second.
        max_range (float):
            Maximum travel distance before despawning.
        damage (int):
            Damage applied on hit.
        traveled (float):
            Distance traveled so far.
        color (tuple):
            Render color for the projectile.
        alive (bool):
            Whether the projectile should continue updating.

    Methods:
        __init__(pos, direction, speed, max_range, damage, color=(210, 180, 120)):
            Initialize the arrow projectile.
        _size():
            Return the render size based on travel direction.
        get_rect():
            Return the arrow's collision rectangle.
        update(dt, obstacles, enemies):
            Advance the arrow and test for collisions.
        draw(screen, camera_offset=None):
            Render the arrow to the screen.
    """
    def __init__(self, pos, direction, speed, max_range, damage, color=(210, 180, 120)):
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()

        self.speed = speed
        self.max_range = max_range
        self.damage = damage
        self.traveled = 0.0
        self.color = color
        self.alive = True
        self.trail = []
        self.trail_length = 6

    def _size(self):
        if abs(self.direction.x) >= abs(self.direction.y):
            return (20, 6)
        return (6, 20)

    def get_rect(self):
        width, height = self._size()
        rect = pygame.Rect(0, 0, width, height)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, enemies):
        if not self.alive:
            return

        # movement length is speed * dt because direction is normalized
        movement = self.direction * self.speed * dt
        self.pos += movement
        self.traveled += abs(self.speed * dt)
        
        self.trail.append(pygame.Vector2(self.pos))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)

        rect = self.get_rect()
        for wall in obstacles:
            if rect.colliderect(wall):
                logger.debug(f"Arrow collided with wall at {self.pos}")
                self.alive = False
                return

        for enemy in enemies:
            if rect.colliderect(enemy.get_rect()):
                logger.info(f"Arrow hit enemy {getattr(enemy, 'ai_profile', type(enemy))} for {self.damage} damage")
                enemy.take_damage(self.damage)
                self.alive = False
                return

        if self.traveled >= self.max_range:
            logger.debug(f"Arrow exceeded max range at {self.pos}")
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        # Draw trail
        for i, pos in enumerate(self.trail):
            alpha = int(80 * (i / len(self.trail)))
            radius = int(1 + 2 * (i / len(self.trail)))
            t_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(t_surf, (180, 150, 100, alpha), (radius, radius), radius)
            screen.blit(t_surf, (pos.x - radius - camera_offset.x, pos.y - radius - camera_offset.y))

        # Draw shaft
        rect = self.get_rect()
        rect.x -= int(camera_offset.x)
        rect.y -= int(camera_offset.y)
        
        # Glow
        glow_surf = pygame.Surface((rect.width + 8, rect.height + 8), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (255, 200, 100, 40), glow_surf.get_rect(), border_radius=4)
        screen.blit(glow_surf, (rect.x - 4, rect.y - 4))
        
        pygame.draw.rect(screen, (180, 130, 80), rect, border_radius=2)
        pygame.draw.rect(screen, self.color, rect.inflate(-4, -2), border_radius=2)

        # Draw head (triangle)
        if abs(self.direction.x) >= abs(self.direction.y):
            if self.direction.x > 0:
                pts = [(rect.right, rect.centery), (rect.right - 6, rect.top), (rect.right - 6, rect.bottom)]
            else:
                pts = [(rect.left, rect.centery), (rect.left + 6, rect.top), (rect.left + 6, rect.bottom)]
        else:
            if self.direction.y > 0:
                pts = [(rect.centerx, rect.bottom), (rect.left, rect.bottom - 6), (rect.right, rect.bottom - 6)]
            else:
                pts = [(rect.centerx, rect.top), (rect.left, rect.top + 6), (rect.right, rect.top + 6)]
        
        pygame.draw.polygon(screen, (200, 200, 210), pts)
        pygame.draw.polygon(screen, (100, 100, 110), pts, 1)


class ArcaneBolt:
    """
    Magical projectile used by arcanist enemies.

    Attributes:
        pos (pygame.Vector2):
            Current projectile position.
        direction (pygame.Vector2):
            Normalized travel direction.
        speed (float):
            Travel speed in pixels per second.
        max_range (float):
            Maximum travel distance before despawning.
        damage (int):
            Damage applied on hit.
        burn_duration (float):
            Duration of the burn effect applied on hit.
        burn_dps (float):
            Damage per second of the burn effect.
        traveled (float):
            Distance traveled so far.
        color (tuple):
            Render color for the projectile.
        alive (bool):
            Whether the projectile should continue updating.

    Methods:
        __init__(pos, direction, speed, max_range, damage, burn_duration, burn_dps, color=(90, 150, 255)):
            Initialize the bolt projectile.
        _size():
            Return the render size based on travel direction.
        get_rect():
            Return the bolt's collision rectangle.
        update(dt, obstacles, player):
            Advance the bolt and test for collisions.
        draw(screen, camera_offset=None):
            Render the bolt to the screen.
    """
    def __init__(
        self,
        pos,
        direction,
        speed,
        max_range,
        damage,
        burn_duration,
        burn_dps,
        color=(90, 150, 255),
    ):
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()

        self.speed = speed
        self.max_range = max_range
        self.damage = damage
        self.burn_duration = burn_duration
        self.burn_dps = burn_dps
        self.traveled = 0.0
        self.color = color
        self.alive = True
        self.trail = []
        self.trail_length = 12
        self.animation_time = 0.0

    def _size(self):
        if abs(self.direction.x) >= abs(self.direction.y):
            return (16, 8)
        return (8, 16)

    def get_rect(self):
        width, height = self._size()
        rect = pygame.Rect(0, 0, width, height)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, player):
        if not self.alive:
            return

        # movement length is speed * dt because direction is normalized
        movement = self.direction * self.speed * dt
        self.pos += movement
        self.traveled += abs(self.speed * dt)
        self.animation_time += dt
        
        self.trail.append(pygame.Vector2(self.pos))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)

        rect = self.get_rect()
        for wall in obstacles:
            if rect.colliderect(wall):
                logger.debug(f"ArcaneBolt collided with wall at {self.pos}")
                self.alive = False
                return

        if player and rect.colliderect(player.get_rect()):
            logger.info(f"ArcaneBolt hit player for {self.damage} damage")
            if self.damage > 0:
                player.take_damage(self.damage)
            if self.burn_dps > 0 and self.burn_duration > 0:
                player.add_effect(BurnEffect(self.burn_duration, self.burn_dps))
            self.alive = False
            return

        if self.traveled >= self.max_range:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        # Draw trail
        for i, pos in enumerate(self.trail):
            alpha = int(150 * (i / len(self.trail)))
            radius = int(2 + 4 * (i / len(self.trail)))
            t_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(t_surf, (*self.color, alpha), (radius, radius), radius)
            screen.blit(t_surf, (pos.x - radius - camera_offset.x, pos.y - radius - camera_offset.y))

        rect = self.get_rect()
        rect.x -= int(camera_offset.x)
        rect.y -= int(camera_offset.y)
        
        # Outer glow
        pulse = (math.sin(self.animation_time * 15) + 1.0) * 0.5
        glow_surf = pygame.Surface((rect.width + 12, rect.height + 12), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (*self.color, int(40 + 20 * pulse)), glow_surf.get_rect())
        screen.blit(glow_surf, (rect.centerx - glow_surf.get_width()//2, rect.centery - glow_surf.get_height()//2))
        
        # Main body
        pygame.draw.ellipse(screen, self.color, rect)
        
        # Core
        core_rect = rect.inflate(-6, -4)
        pygame.draw.ellipse(screen, (200, 220, 255), core_rect)


class Bomb:
    """
    Throwable bomb projectile that explodes after a fuse or impact.

    Attributes:
        pos (pygame.Vector2):
            Current projectile position.
        direction (pygame.Vector2):
            Normalized travel direction.
        speed (float):
            Travel speed in pixels per second.
        max_range (float):
            Maximum travel distance before forcing an explosion.
        damage (int):
            Damage applied by the explosion.
        blast_radius (float):
            Explosion radius in pixels.
        fuse_time (float):
            Time before detonation.
        knockback_force (float):
            Knockback applied to the player by the explosion.
        explosion_duration (float):
            How long the explosion remains active.
        traveled (float):
            Distance traveled so far.
        timer (float):
            Time spent traveling.
        color (tuple):
            Render color for the bomb.
        alive (bool):
            Whether the projectile should continue updating.
        exploding (bool):
            Whether the bomb is currently in its explosion state.
        explosion_timer (float):
            Time spent in the explosion state.
        damage_applied (bool):
            Whether explosion damage has already been applied.

    Methods:
        __init__(pos, direction, speed, max_range, damage, blast_radius, fuse_time, knockback_force=0.0, explosion_duration=0.35, color=(220, 150, 60)):
            Initialize the bomb projectile.
        _size():
            Return the bomb's render size.
        get_rect():
            Return the bomb's collision rectangle.
        _trigger_explosion():
            Switch the bomb into explosion mode.
        _player_center(player):
            Return the player's center position when available.
        update(dt, obstacles, player):
            Advance the bomb, detonate it, and apply explosion damage.
        draw(screen, camera_offset=None):
            Render the bomb or explosion to the screen.
    """
    def __init__(
        self,
        pos,
        direction,
        speed,
        max_range,
        damage,
        blast_radius,
        fuse_time,
        knockback_force=0.0,
        explosion_duration=0.35,
        color=(220, 150, 60),
    ):
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()

        self.speed = speed
        self.max_range = max_range
        self.damage = damage
        self.blast_radius = blast_radius
        self.fuse_time = fuse_time
        self.knockback_force = knockback_force
        self.explosion_duration = explosion_duration
        self.traveled = 0.0
        self.timer = 0.0
        self.color = color
        self.alive = True
        self.exploding = False
        self.explosion_timer = 0.0
        self.damage_applied = False
        self.animation_time = 0.0

    def _size(self):
        return 14, 14

    def get_rect(self):
        width, height = self._size()
        rect = pygame.Rect(0, 0, width, height)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def _trigger_explosion(self):
        if self.exploding:
            return
        self.exploding = True
        self.explosion_timer = 0.0
        self.damage_applied = False

    def _player_center(self, player):
        if player is None:
            return None
        if hasattr(player, "get_rect"):
            rect = player.get_rect()
            return pygame.Vector2(rect.centerx, rect.centery)
        return pygame.Vector2(getattr(player, "pos", (0, 0)))

    def update(self, dt, obstacles, player):
        if not self.alive:
            return
            
        self.animation_time += dt

        if self.exploding:
            self.explosion_timer += dt
            if not self.damage_applied:
                player_center = self._player_center(player)
                if player_center:
                    pdiff = player_center - self.pos
                    if pdiff.length_squared() <= (self.blast_radius * self.blast_radius):
                        if self.damage > 0:
                            player.take_damage(self.damage)
                        if self.knockback_force > 0:
                            direction = player_center - self.pos
                            if direction.length_squared() == 0:
                                direction = pygame.Vector2(1, 0)
                            player.pos += direction.normalize() * self.knockback_force
                self.damage_applied = True
            if self.explosion_timer >= self.explosion_duration:
                self.alive = False
            return

        movement = self.direction * self.speed * dt
        self.pos += movement
        self.traveled += movement.length()
        self.timer += dt

        rect = self.get_rect()
        for wall in obstacles:
            if rect.colliderect(wall):
                logger.debug(f"Bomb impacted wall at {self.pos}, triggering explosion")
                self._trigger_explosion()
                return

        if self.timer >= self.fuse_time or self.traveled >= self.max_range:
            logger.debug(f"Bomb fuse expired or max range reached at {self.pos}, triggering explosion")
            self._trigger_explosion()

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        if not self.exploding:
            rect = self.get_rect()
            rect.x -= int(camera_offset.x)
            rect.y -= int(camera_offset.y)
            
            # Fuse glow
            pulse = (math.sin(self.animation_time * 20) + 1.0) * 0.5
            fuse_size = int(4 + 3 * pulse)
            fuse_surf = pygame.Surface((fuse_size * 2, fuse_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(fuse_surf, (255, 50, 0, 200), (fuse_size, fuse_size), fuse_size)
            screen.blit(fuse_surf, (rect.centerx - fuse_size, rect.top - fuse_size - 2))
            
            # Bomb body
            pygame.draw.circle(screen, self.color, rect.center, rect.width // 2)
            # Metal band
            pygame.draw.rect(screen, (80, 80, 90), rect.inflate(-4, -4), border_radius=4)
            # Highlight
            pygame.draw.circle(screen, (255, 255, 255), (rect.centerx - 2, rect.centery - 2), 2)
            return

        progress = min(1.0, self.explosion_timer / self.explosion_duration)
        radius = int(self.blast_radius * progress)
        if radius <= 0:
            return
            
        # Outer smoke ring
        smoke_alpha = int(100 * (1 - progress))
        pygame.draw.circle(screen, (100, 100, 100, smoke_alpha), (int(self.pos.x - camera_offset.x), int(self.pos.y - camera_offset.y)), radius + 10, 5)
        
        # Main explosion
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        # Outer orange
        pygame.draw.circle(surface, (255, 150, 50, 150), (radius, radius), radius)
        # Inner yellow
        pygame.draw.circle(surface, (255, 220, 100, 200), (radius, radius), max(1, int(radius * 0.6)))
        # Core white
        pygame.draw.circle(surface, (255, 255, 240, 220), (radius, radius), max(1, int(radius * 0.2)))
        
        screen.blit(surface, (self.pos.x - radius - camera_offset.x, self.pos.y - radius - camera_offset.y))


class Fireball:
    """
    Player fireball projectile that explodes on impact or after a short fuse.

    The explosion damages enemies in an area and can optionally knock them back.
    """
    def __init__(
        self,
        pos,
        direction,
        speed,
        max_range,
        damage,
        blast_radius,
        fuse_time,
        knockback_force=0.0,
        explosion_duration=0.35,
        color=(255, 120, 40),
    ):
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()

        self.speed = speed
        self.max_range = max_range
        self.damage = damage
        self.blast_radius = blast_radius
        self.fuse_time = fuse_time
        self.knockback_force = knockback_force
        self.explosion_duration = explosion_duration
        self.traveled = 0.0
        self.timer = 0.0
        self.color = color
        self.alive = True
        self.exploding = False
        self.explosion_timer = 0.0
        self.damage_applied = False
        
        # Visuals
        self.animation_time = 0.0
        self.trail = []
        self.trail_length = 12
        self.ember_particles = []
        self.ember_spawn_timer = 0.0

    def _size(self):
        return 16, 16

    def get_rect(self):
        width, height = self._size()
        rect = pygame.Rect(0, 0, width, height)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def _trigger_explosion(self):
        if self.exploding:
            return
        self.exploding = True
        self.explosion_timer = 0.0
        self.damage_applied = False

    def _entity_center(self, entity):
        if entity is None:
            return None
        if hasattr(entity, "get_rect"):
            rect = entity.get_rect()
            return pygame.Vector2(rect.centerx, rect.centery)
        return pygame.Vector2(getattr(entity, "pos", (0, 0)))

    def update(self, dt, obstacles, enemies):
        if not self.alive:
            return

        self.animation_time += dt

        if self.exploding:
            self.explosion_timer += dt
            if not self.damage_applied:
                for enemy in enemies:
                    enemy_center = self._entity_center(enemy)
                    if enemy_center is None:
                        continue
                    if (enemy_center - self.pos).length_squared() <= self.blast_radius * self.blast_radius:
                        if self.damage > 0:
                            enemy.take_damage(self.damage)
                        if self.knockback_force > 0 and hasattr(enemy, "pos"):
                            direction = enemy_center - self.pos
                            if direction.length_squared() == 0:
                                direction = pygame.Vector2(1, 0)
                            enemy.pos += direction.normalize() * self.knockback_force
                self.damage_applied = True

            if self.explosion_timer >= self.explosion_duration:
                self.alive = False
            return

        movement = self.direction * self.speed * dt
        self.pos += movement
        self.traveled += movement.length()
        self.timer += dt
        
        # Update trail
        self.trail.append(pygame.Vector2(self.pos))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)

        # Spawn ember particles during flight
        self.ember_spawn_timer += dt
        if self.ember_spawn_timer >= 0.02:
            self.ember_spawn_timer = 0.0
            perp = pygame.Vector2(-self.direction.y, self.direction.x)
            for _ in range(2):
                offset = perp * random.uniform(-8, 8) - self.direction * random.uniform(0, 15)
                self.ember_particles.append({
                    "pos": pygame.Vector2(self.pos) + offset,
                    "vel": offset * random.uniform(0.5, 1.5) + pygame.Vector2(random.uniform(-10, 10), random.uniform(-10, 10)),
                    "life": random.uniform(0.15, 0.35),
                    "max_life": random.uniform(0.15, 0.35),
                    "size": random.uniform(1.5, 3.5),
                    "color": random.choice([
                        (255, 200, 80),
                        (255, 150, 40),
                        (255, 100, 20),
                        (255, 220, 100),
                    ]),
                })

        # Update ember particles
        for e in self.ember_particles[:]:
            e["pos"] += e["vel"] * dt
            e["vel"] *= 0.95
            e["life"] -= dt
            if e["life"] <= 0:
                self.ember_particles.remove(e)

        rect = self.get_rect()
        for wall in obstacles:
            if rect.colliderect(wall):
                logger.debug(f"Fireball impacted wall at {self.pos}, triggering explosion")
                self._trigger_explosion()
                return

        if self.timer >= self.fuse_time or self.traveled >= self.max_range:
            logger.debug(f"Fireball fuse expired or max range reached at {self.pos}, triggering explosion")
            self._trigger_explosion()

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        if not self.exploding:
            cx = int(self.pos.x - camera_offset.x)
            cy = int(self.pos.y - camera_offset.y)
            t = self.animation_time

            # ── Draw ember particles ──
            for e in self.ember_particles:
                life_r = e["life"] / e["max_life"] if e["max_life"] > 0 else 0
                if life_r <= 0:
                    continue
                e_alpha = int(200 * life_r)
                e_size = max(1, int(e["size"] * life_r))
                ex = int(e["pos"].x - camera_offset.x)
                ey = int(e["pos"].y - camera_offset.y)
                eg_sz = e_size * 3
                eg = pygame.Surface((eg_sz * 2, eg_sz * 2), pygame.SRCALPHA)
                r, g, b = e["color"]
                pygame.draw.circle(eg, (r, g, b, e_alpha // 3), (eg_sz, eg_sz), eg_sz)
                screen.blit(eg, (ex - eg_sz, ey - eg_sz))
                pygame.draw.circle(screen, e["color"], (ex, ey), e_size)

            # ── Draw trail ──
            for i, pos in enumerate(self.trail):
                ratio = i / len(self.trail) if len(self.trail) > 0 else 0
                alpha = int(80 * ratio)
                radius = int(3 + 5 * ratio)
                t_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                # Gradient from orange to yellow
                trail_color = (
                    int(255 * (0.4 + 0.6 * ratio)),
                    int(120 * ratio),
                    int(20 * ratio),
                )
                pygame.draw.circle(t_surf, (*trail_color, alpha), (radius, radius), radius)
                screen.blit(t_surf, (pos.x - radius - camera_offset.x, pos.y - radius - camera_offset.y))

            # ── Draw main fireball ──
            pulse = (math.sin(t * 12) + 1.0) * 0.5
            fast_pulse = (math.sin(t * 20) + 1.0) * 0.5

            # Outer glow (large, soft)
            glow_size = int(18 + 8 * pulse)
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            outer_glow_a = int(50 + 30 * pulse)
            pygame.draw.circle(glow_surf, (255, 100, 20, outer_glow_a), (glow_size, glow_size), glow_size)
            pygame.draw.circle(glow_surf, (255, 200, 60, int(outer_glow_a * 0.5)), (glow_size, glow_size), int(glow_size * 0.6))
            screen.blit(glow_surf, (cx - glow_size, cy - glow_size))

            # Fireball body — outer ring
            body_r = 8 + 2 * fast_pulse
            pygame.draw.circle(screen, (255, 60, 10), (cx, cy), int(body_r))
            # Mid layer
            mid_r = int(body_r * 0.75)
            pygame.draw.circle(screen, (255, 160, 30), (cx, cy), mid_r)
            # Bright core
            core_r = int(body_r * 0.45)
            core_pulse = 0.8 + 0.2 * math.sin(t * 25)
            pygame.draw.circle(screen, (255, 240, 180), (cx, cy), int(core_r * core_pulse))
            # Hot center
            center_r = int(core_r * 0.5)
            pygame.draw.circle(screen, (255, 255, 255), (cx, cy), max(1, center_r))

            # ── Flame flicker spikes ──
            for i in range(6):
                angle = t * 15 + i * (math.pi * 2 / 6)
                spike_len = 3 + 5 * (0.5 + 0.5 * math.sin(t * 18 + i * 2.5))
                sx = cx + int(math.cos(angle) * body_r)
                sy = cy + int(math.sin(angle) * body_r)
                ex = cx + int(math.cos(angle) * (body_r + spike_len))
                ey = cy + int(math.sin(angle) * (body_r + spike_len))
                spike_alpha = int(150 + 80 * math.sin(t * 22 + i * 3))
                pygame.draw.line(screen, (255, 200 + i * 10, 50, spike_alpha), (sx, sy), (ex, ey),
                                 max(1, int(2 + math.sin(t * 12 + i * 2))))
            return

        # Explosion visuals
        progress = min(1.0, self.explosion_timer / self.explosion_duration)
        radius = int(self.blast_radius * progress)
        if radius <= 0:
            return

        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)

        # ── Outer smoke ring ──
        smoke_radius = radius + 15
        smoke_alpha = int(40 * (1 - progress))
        if smoke_alpha > 0:
            smoke_surf = pygame.Surface((smoke_radius * 2, smoke_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(smoke_surf, (80, 60, 40, smoke_alpha), (smoke_radius, smoke_radius), smoke_radius, 6)
            screen.blit(smoke_surf, (cx - smoke_radius, cy - smoke_radius))

        # ── Shockwave ring (fast expanding) ──
        ring_width = max(1, int(6 * (1 - progress)))
        ring_alpha = int(220 * (1 - progress))
        pygame.draw.circle(screen, (255, 200, 80, ring_alpha), (cx, cy), radius, ring_width)
        # Inner shockwave echo
        if progress < 0.6:
            echo_radius = int(radius * 0.6)
            echo_alpha = int(160 * (1 - progress * 1.5))
            pygame.draw.circle(screen, (255, 240, 160, echo_alpha), (cx, cy), echo_radius, max(1, ring_width - 1))

        # ── Fireball burst layers ──
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

        # Outer flame
        outer_alpha = int(150 * (1 - progress * 0.4))
        pygame.draw.circle(surface, (255, 80, 10, outer_alpha), (radius, radius), radius)

        # Mid flame
        mid_r = max(1, int(radius * 0.7))
        mid_alpha = int(200 * (1 - progress * 0.3))
        pygame.draw.circle(surface, (255, 180, 40, mid_alpha), (radius, radius), mid_r)

        # Inner bright core
        inner_r = max(1, int(radius * 0.35))
        inner_alpha = int(240 * (1 - progress * 0.2))
        pygame.draw.circle(surface, (255, 240, 160, inner_alpha), (radius, radius), inner_r)

        # White hot center
        center_r = max(1, int(radius * 0.15))
        pygame.draw.circle(surface, (255, 255, 255, inner_alpha), (radius, radius), center_r)

        screen.blit(surface, (cx - radius, cy - radius))

        # ── Explosion debris particles ──
        import random as _rnd
        if not hasattr(self, "_debris"):
            self._debris = []
        if progress < 0.4:
            for _ in range(int(6 * (1 - progress * 2.5))):
                angle = _rnd.uniform(0, math.pi * 2)
                dist = _rnd.uniform(radius * 0.3, radius * 0.9)
                d_alpha = int(180 * (1 - progress))
                d_size = _rnd.randint(2, 4)
                d_color = _rnd.choice([(255, 200, 60, d_alpha), (255, 140, 30, d_alpha),
                                       (255, 100, 10, d_alpha)])
                dx = cx + math.cos(angle) * dist
                dy = cy + math.sin(angle) * dist
                d_surf = pygame.Surface((d_size * 2, d_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(d_surf, d_color, (d_size, d_size), d_size)
                screen.blit(d_surf, (int(dx - d_size), int(dy - d_size)))


class FrostNova:
    """
    Instant burst of ice that freezes all enemies within radius.

    Attributes:
        pos (pygame.Vector2): Center position of the nova.
        radius (float): Maximum expansion radius.
        freeze_duration (float): How long enemies stay frozen.
        damage (int): Damage dealt to enemies.
        alive (bool): Whether the effect is still active.
        expansion_time (float): Current expansion time.
        expansion_duration (float): How long the visual expansion lasts.
        current_radius (float): Current visual radius.
    """
    def __init__(self, pos, radius, freeze_duration, damage=0, expansion_duration=0.5):
        self.pos = pygame.Vector2(pos)
        self.radius = radius
        self.freeze_duration = freeze_duration
        self.damage = damage
        self.alive = True
        self.expansion_time = 0.0
        self.expansion_duration = expansion_duration
        self.current_radius = 0.0
        self.damage_applied = False
        self.animation_time = 0.0

    def get_rect(self):
        size = int(self.radius * 2)
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, enemies):
        if not self.alive:
            return

        self.animation_time += dt
        self.expansion_time += dt
        progress = min(1.0, self.expansion_time / self.expansion_duration)
        self.current_radius = self.radius * progress

        if not self.damage_applied and progress >= 0.3:
            for enemy in enemies:
                if enemy.is_dead():
                    continue
                enemy_rect = enemy.get_rect()
                enemy_center = pygame.Vector2(enemy_rect.centerx, enemy_rect.centery)
                if (enemy_center - self.pos).length_squared() <= self.radius * self.radius:
                    if self.damage > 0:
                        enemy.take_damage(self.damage)
                    enemy.add_effect(FreezeEffect(self.freeze_duration))
            self.damage_applied = True

        if self.expansion_time >= self.expansion_duration:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        progress = min(1.0, self.expansion_time / self.expansion_duration)
        radius = int(self.current_radius)

        if radius <= 0:
            return

        # ── Outer frost ring shockwave ──
        ring_alpha = int(200 * (1 - progress))
        pygame.draw.circle(screen, (180, 220, 255, ring_alpha), (cx, cy), radius, max(2, int(3 * (1 - progress) + 1)))

        # ── Main frost nova burst ──
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        outer_alpha = int(120 * (1 - progress * 0.5))
        pygame.draw.circle(surface, (60, 140, 255, outer_alpha), (radius, radius), radius)
        mid_r = max(1, int(radius * 0.65))
        mid_alpha = int(160 * (1 - progress * 0.3))
        pygame.draw.circle(surface, (120, 190, 255, mid_alpha), (radius, radius), mid_r)
        inner_r = max(1, int(radius * 0.3))
        inner_alpha = int(200 * (1 - progress * 0.2))
        pygame.draw.circle(surface, (200, 235, 255, inner_alpha), (radius, radius), inner_r)

        screen.blit(surface, (cx - radius, cy - radius))

        # ── Ice crystal sparkles ──
        import random
        for _ in range(int(6 * (1 - progress) + 2)):
            sp_angle = random.uniform(0, math.pi * 2)
            sp_dist = random.uniform(0, radius)
            sp_x = cx + math.cos(sp_angle) * sp_dist
            sp_y = cy + math.sin(sp_angle) * sp_dist
            sp_size = random.randint(1, 3)
            sp_color = random.choice([(200, 240, 255), (160, 210, 255), (255, 255, 255)])
            pygame.draw.circle(screen, sp_color, (int(sp_x), int(sp_y)), sp_size)

        # ── Inner flash (early burst) ──
        if progress < 0.3:
            flash_alpha = int(180 * (1 - progress / 0.3))
            flash_r = int(radius * 0.5)
            flash_surf = pygame.Surface((flash_r * 2, flash_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (220, 245, 255, flash_alpha), (flash_r, flash_r), flash_r)
            screen.blit(flash_surf, (cx - flash_r, cy - flash_r))


class GlacialCascade:
    """
    A wide ice wave that cascades forward in a spreading fan, damaging and freezing
    all enemies it passes through. The wave grows wider as it travels, with visuals
    of multiple ice shards, frost mist, and a ground frost trail.
    """
    def __init__(self, pos, direction, speed, max_range, damage, freeze_duration,
                 cascade_width=80.0, color=(80, 180, 255)):
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()

        self.speed = speed
        self.max_range = max_range
        self.damage = damage
        self.freeze_duration = freeze_duration
        self.base_width = cascade_width
        self.color = color
        self.alive = True
        self.traveled = 0.0
        self.animation_time = 0.0
        self.hit_cooldowns = {}
        self.frost_particles = []
        self.ground_trail = []

    @property
    def cascade_width(self):
        progress = min(1.0, self.traveled / max(self.max_range, 1))
        return self.base_width * (0.8 + progress * 1.7)

    def _get_wedge_points(self):
        half_w = self.cascade_width * 0.5
        forward = self.direction
        perp = pygame.Vector2(-forward.y, forward.x)
        tip = self.pos + forward * 25
        bl = self.pos - forward * 15 - perp * half_w
        br = self.pos - forward * 15 + perp * half_w
        return tip, bl, br

    def get_rect(self):
        tip, bl, br = self._get_wedge_points()
        xs = [tip.x, bl.x, br.x]
        ys = [tip.y, bl.y, br.y]
        return pygame.Rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    def update(self, dt, obstacles, enemies):
        if not self.alive:
            return

        self.animation_time += dt
        movement = self.direction * self.speed * dt
        self.pos += movement
        self.traveled += movement.length()

        # Ground frost trail
        perp = pygame.Vector2(-self.direction.y, self.direction.x)
        for _ in range(2):
            offset = random.uniform(-self.cascade_width * 0.3, self.cascade_width * 0.3)
            tp = self.pos + perp * offset - self.direction * random.uniform(0, 25)
            self.ground_trail.append((tp, self.animation_time))
        while len(self.ground_trail) > 40:
            self.ground_trail.pop(0)

        # Frost mist particles
        if random.random() < 0.5:
            off = random.uniform(-self.cascade_width * 0.4, self.cascade_width * 0.4)
            pp = self.pos + perp * off + self.direction * random.uniform(-20, 10)
            self.frost_particles.append({
                "pos": pp, "life": random.uniform(0.3, 0.7), "max_life": 0.7,
                "size": random.randint(3, 6),
                "vel": perp * random.uniform(-15, 15) - self.direction * random.uniform(5, 20),
            })
        for p in self.frost_particles[:]:
            p["pos"] += p["vel"] * dt
            p["life"] -= dt
            if p["life"] <= 0:
                self.frost_particles.remove(p)

        # Damage enemies in cascade area
        self._damage_enemies(enemies)

        # Wall collision
        tip = self.pos + self.direction * 25
        for wall in obstacles:
            if wall.collidepoint(tip.x, tip.y):
                self.alive = False
                return

        if self.traveled >= self.max_range:
            self.alive = False

    def _damage_enemies(self, enemies):
        half_w = self.cascade_width * 0.5
        for enemy in enemies:
            if enemy.is_dead():
                continue
            eid = id(enemy)
            ec = pygame.Vector2(enemy.get_rect().center)
            to_enemy = ec - self.pos
            forward_dist = to_enemy.dot(self.direction)
            if forward_dist < -20 or forward_dist > 50:
                continue
            lateral = to_enemy - self.direction * forward_dist
            if lateral.length_squared() > half_w * half_w:
                continue
            # Re-hit cooldown ~0.25s
            last = self.hit_cooldowns.get(eid, -999.0)
            if self.animation_time - last < 0.25:
                continue
            if self.damage > 0:
                enemy.take_damage(self.damage)
            enemy.add_effect(FreezeEffect(self.freeze_duration))
            self.hit_cooldowns[eid] = self.animation_time

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)
        ox, oy = camera_offset.x, camera_offset.y
        t = self.animation_time
        perp = pygame.Vector2(-self.direction.y, self.direction.x)

        # Ground frost trail
        for i, (tp, _) in enumerate(self.ground_trail):
            alpha = int(60 * (i / len(self.ground_trail)))
            r = int(2 + 5 * (i / len(self.ground_trail)))
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color[:3], alpha), (r, r), r)
            screen.blit(surf, (tp.x - r - ox, tp.y - r - oy))

        # Frost mist
        for p in self.frost_particles:
            lr = p["life"] / p["max_life"]
            alpha = int(80 * lr)
            sz = int(p["size"] * (0.5 + 0.5 * lr))
            surf = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (200, 230, 255, alpha), (sz, sz), sz)
            screen.blit(surf, (p["pos"].x - sz - ox, p["pos"].y - sz - oy))

        # Cascade wedge/crescent
        tip, bl, br = self._get_wedge_points()
        tip_s = (tip.x - ox, tip.y - oy)
        bl_s = (bl.x - ox, bl.y - oy)
        br_s = (br.x - ox, br.y - oy)
        pulse = (math.sin(t * 10) + 1.0) * 0.5
        alpha = int(70 + 50 * pulse)

        # Wedge fill and outline
        wedge_pts = [tip_s, bl_s, br_s]
        if len(wedge_pts) >= 3:
            wedge_surf = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
            pygame.draw.polygon(wedge_surf, (*self.color[:3], alpha // 2), wedge_pts)
            pygame.draw.polygon(wedge_surf, (*self.color[:3], alpha), wedge_pts, 2)
            screen.blit(wedge_surf, (0, 0))

        # Multiple ice shards within the cascade
        num_shards = 9
        for i in range(num_shards):
            frac = i / (num_shards - 1) if num_shards > 1 else 0.5
            spread = (frac - 0.5) * self.cascade_width * 0.75
            depth = 15 - frac * 25
            spos = self.pos + perp * spread - self.direction * depth
            ssx, ssy = spos.x - ox, spos.y - oy
            spulse = (math.sin(t * 15 + i * 2.5) + 1.0) * 0.5
            sz = 3 + 4 * (1 - abs(frac - 0.5) * 2)
            pts = [
                (ssx, ssy - sz * (0.4 + 0.3 * spulse)),
                (ssx + sz * 0.35, ssy),
                (ssx, ssy + sz * 0.35),
                (ssx - sz * 0.35, ssy),
            ]
            pygame.draw.polygon(screen, (170, 210, 255), pts)
            pygame.draw.polygon(screen, (210, 235, 255), pts, 1)

        # Central bright core
        cx = (tip_s[0] + bl_s[0] + br_s[0]) // 3
        cy = (tip_s[1] + bl_s[1] + br_s[1]) // 3
        cr = int(5 + 3 * pulse)
        pygame.draw.circle(screen, (220, 245, 255), (cx, cy), cr)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), cr // 2)

        # Sparkles
        for i in range(5):
            angle = t * 2.5 + i * math.pi * 0.4 * 2
            dist = 10 + 6 * math.sin(t * 2 + i * 1.3)
            spx = cx + int(dist * math.cos(angle))
            spy = cy + int(dist * math.sin(angle))
            sps = max(1, int(2 + math.sin(t * 5 + i * 2) * 1))
            pygame.draw.circle(screen, (255, 255, 255), (spx, spy), sps)


class ChainLightning:
    """
    Lightning bolt that flies forward and chains between up to N enemies.

    Attributes:
        pos (pygame.Vector2): Current position.
        direction (pygame.Vector2): Travel direction.
        speed (float): Travel speed.
        max_range (float): Maximum travel distance.
        damage (int): Damage per hit.
        chain_range (float): Max distance to chain to next target.
        max_targets (int): Max number of enemies to chain to.
        alive (bool): Whether the projectile is active.
        traveled (float): Distance traveled.
        hit_enemies (list): Enemies already hit (prevents re-hits).
        chaining (bool): Whether currently chaining between targets.
        chain_targets (list): Remaining targets to chain to.
        animation_time (float): Visual animation timer.
        trail (list): Visual trail points.
    """
    def __init__(self, pos, direction, speed, max_range, damage, chain_range, max_targets=5,
                 color=(255, 220, 50)):
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()

        self.speed = speed
        self.max_range = max_range
        self.damage = damage
        self.chain_range = chain_range
        self.max_targets = max_targets
        self.color = color
        self.alive = True
        self.traveled = 0.0
        self.animation_time = 0.0
        self.trail = []
        self.trail_length = 12

        self.hit_enemies = []
        self.chaining = False
        self.chain_targets = []
        self.chain_timer = 0.0
        self.chain_delay = 0.08
        self.chain_index = 0

        # Visual arc points for rendering chain arcs
        self.arc_points = []

    def _size(self):
        return 12, 12

    def get_rect(self):
        width, height = self._size()
        rect = pygame.Rect(0, 0, width, height)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def _find_chain_target(self, from_pos, enemies):
        """Find nearest alive enemy not yet hit within chain_range."""
        best = None
        best_dist = self.chain_range * self.chain_range
        for enemy in enemies:
            if enemy.is_dead() or enemy in self.hit_enemies:
                continue
            e_center = pygame.Vector2(enemy.get_rect().center)
            d2 = (e_center - from_pos).length_squared()
            if d2 < best_dist:
                best_dist = d2
                best = enemy
        return best

    def update(self, dt, obstacles, enemies):
        if not self.alive:
            return

        self.animation_time += dt

        if self.chaining:
            self.chain_timer += dt
            if self.chain_timer >= self.chain_delay:
                self.chain_timer = 0.0
                self.chain_index += 1
                if self.chain_index >= len(self.chain_targets):
                    self.alive = False
                    return
                enemy = self.chain_targets[self.chain_index]
                e_center = pygame.Vector2(enemy.get_rect().center)
                arc_start = pygame.Vector2(self.pos)
                self.arc_points.append((arc_start, e_center, self.animation_time))
                enemy.take_damage(self.damage)
                logger.info(f"Chain Lightning chained to {enemy.__class__.__name__} for {self.damage} damage!")
                self.pos = e_center
                self.hit_enemies.append(enemy)

                # Find next chain target
                next_enemy = self._find_chain_target(self.pos, enemies)
                if next_enemy and len(self.chain_targets) < self.max_targets:
                    self.chain_targets.append(next_enemy)
            return

        # Flying phase
        movement = self.direction * self.speed * dt
        self.pos += movement
        self.traveled += movement.length()

        self.trail.append(pygame.Vector2(self.pos))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)

        rect = self.get_rect()
        for wall in obstacles:
            if rect.colliderect(wall):
                self.alive = False
                return

        for enemy in enemies:
            if enemy.is_dead():
                continue
            if rect.colliderect(enemy.get_rect()):
                # First hit: start chaining
                if enemy not in self.hit_enemies:
                    enemy.take_damage(self.damage)
                    logger.info(f"Chain Lightning hit {enemy.__class__.__name__} for {self.damage} damage!")
                    self.hit_enemies.append(enemy)
                    e_center = pygame.Vector2(enemy.get_rect().center)
                    self.arc_points.append((pygame.Vector2(self.pos), e_center, self.animation_time))
                    self.pos = e_center

                    # Find chain targets
                    next_enemy = self._find_chain_target(self.pos, enemies)
                    if next_enemy:
                        self.chain_targets = [enemy, next_enemy]
                    else:
                        self.chain_targets = [enemy]
                    self.chaining = True
                    self.chain_index = 0
                    self.chain_timer = 0.0
                return

        if self.traveled >= self.max_range:
            self.alive = False

    def _draw_lightning_arc(self, screen, start, end, time_offset, camera_offset):
        """Draw a zigzag lightning arc between two points with glow."""
        sx = start.x - camera_offset.x
        sy = start.y - camera_offset.y
        ex = end.x - camera_offset.x
        ey = end.y - camera_offset.y

        dx = ex - sx
        dy = ey - sy
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 1:
            return

        segments = max(5, int(dist / 8))
        points = [(sx, sy)]
        for i in range(1, segments):
            t = i / segments
            bx = sx + dx * t
            by = sy + dy * t
            offset = 6 * math.sin(t * math.pi * 4 + time_offset * 20) + \
                     4 * math.sin(t * math.pi * 7 + time_offset * 13)
            perp_x = -dy / dist
            perp_y = dx / dist
            points.append((bx + perp_x * offset, by + perp_y * offset))
        points.append((ex, ey))

        # Glow behind arc
        glow_surf = pygame.Surface((int(abs(dx) + 30), int(abs(dy) + 30)), pygame.SRCALPHA)
        g_ox = min(sx, ex) - 15 - camera_offset.x
        g_oy = min(sy, ey) - 15 - camera_offset.y
        for thickness in (6, 4):
            alpha = 40 if thickness > 4 else 80
            pygame.draw.lines(glow_surf, (255, 220, 50, alpha), False,
                              [(p[0] - g_ox, p[1] - g_oy) for p in points], thickness)
        screen.blit(glow_surf, (g_ox, g_oy))

        # Main arc
        pygame.draw.lines(screen, (255, 255, 200), False, points, 2)
        pygame.draw.lines(screen, self.color, False, points, 1)

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        # Draw chain arcs
        for arc_start, arc_end, t_offset in self.arc_points:
            self._draw_lightning_arc(screen, arc_start, arc_end, t_offset, camera_offset)

        # Draw trail
        for i, pos in enumerate(self.trail):
            alpha = int(120 * (i / len(self.trail)))
            radius = int(2 + 3 * (i / len(self.trail)))
            t_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(t_surf, (*self.color[:3], alpha), (radius, radius), radius)
            screen.blit(t_surf, (pos.x - radius - camera_offset.x, pos.y - radius - camera_offset.y))

        # Draw bolt head
        if not self.chaining:
            rect = self.get_rect()
            rect.x -= int(camera_offset.x)
            rect.y -= int(camera_offset.y)

            pulse = (math.sin(self.animation_time * 15) + 1.0) * 0.5
            # Outer glow
            glow_size = int(rect.width * (1.5 + 0.3 * pulse))
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color, 70), (glow_size, glow_size), glow_size)
            screen.blit(glow_surf, (rect.centerx - glow_size, rect.centery - glow_size))

            # Core bolt
            pygame.draw.circle(screen, (255, 255, 220), rect.center, rect.width // 2)
            pygame.draw.circle(screen, self.color, rect.center, rect.width // 2 - 1)


class Thunderstrike:
    """
    Calls down lightning from above at a target position, dealing damage in a radius.

    Attributes:
        pos (pygame.Vector2): Center position of the strike.
        damage (int): Damage dealt to enemies.
        radius (float): Effect radius.
        alive (bool): Whether the effect is active.
        delay (float): Telegraph delay before strike.
        timer (float): Current time elapsed.
        struck (bool): Whether damage has been applied.
        animation_time (float): Visual animation timer.
    """
    def __init__(self, pos, damage, radius=100.0, delay=0.5):
        self.pos = pygame.Vector2(pos)
        self.damage = damage
        self.radius = radius
        self.alive = True
        self.delay = delay
        self.timer = 0.0
        self.struck = False
        self.animation_time = 0.0
        self.flash_alpha = 0

    def get_rect(self):
        size = int(self.radius * 2)
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, enemies):
        if not self.alive:
            return

        self.animation_time += dt
        self.timer += dt

        if not self.struck and self.timer >= self.delay:
            # Apply damage to all enemies in radius
            for enemy in enemies:
                if enemy.is_dead():
                    continue
                e_center = pygame.Vector2(enemy.get_rect().center)
                if (e_center - self.pos).length_squared() <= self.radius * self.radius:
                    enemy.take_damage(self.damage)
                    logger.info(f"Thunderstrike hit {enemy.__class__.__name__} for {self.damage} damage!")
            self.struck = True
            self.flash_alpha = 255

        if self.struck:
            self.flash_alpha = max(0, self.flash_alpha - 600 * dt)

        if self.timer >= self.delay + 0.6:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)

        if not self.struck:
            # Telegraph: pulsing circle on ground + descending particles
            progress = self.timer / self.delay
            pulse = (math.sin(self.animation_time * 10) + 1.0) * 0.5

            # Ground target circle
            circle_alpha = int(80 + 80 * pulse)
            circle_surf = pygame.Surface((int(self.radius * 2), int(self.radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, (255, 220, 50, circle_alpha),
                               (int(self.radius), int(self.radius)), int(self.radius), 2)
            pygame.draw.circle(circle_surf, (200, 180, 255, int(circle_alpha * 0.5)),
                               (int(self.radius), int(self.radius)), int(self.radius * 0.6), 1)
            screen.blit(circle_surf, (cx - int(self.radius), cy - int(self.radius)))

            # Descending light particles
            import random
            for _ in range(4):
                px = cx + random.uniform(-self.radius * 0.8, self.radius * 0.8)
                py = cy - 200 + progress * 200 + random.uniform(-20, 20)
                p_size = random.randint(2, 4)
                p_alpha = max(0, int(120 * (1 - abs(py - cy) / 200)))
                p_surf = pygame.Surface((p_size * 2, p_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, (255, 255, 200, p_alpha), (p_size, p_size), p_size)
                screen.blit(p_surf, (int(px) - p_size, int(py) - p_size))
        else:
            # Strike visual: bolt from above + expanding electrical field
            bolt_alpha = min(255, self.flash_alpha * 2)

            # Main lightning bolt (from top of screen to center)
            bolt_top_y = cy - 400
            segments = 12
            bolt_points = [(cx, bolt_top_y)]
            for i in range(1, segments):
                t = i / segments
                bx = cx + 15 * math.sin(t * math.pi * 5 + self.animation_time * 30)
                by = bolt_top_y + (cy - bolt_top_y) * t
                bolt_points.append((bx, by))
            bolt_points.append((cx, cy))

            # Bolt glow
            glow_surf = pygame.Surface((200, 450), pygame.SRCALPHA)
            g_ox = cx - 100
            g_oy = cy - 400
            for thickness in (8, 5, 3):
                alpha = int(30 * bolt_alpha / 255) if thickness > 5 else int(80 * bolt_alpha / 255)
                pygame.draw.lines(glow_surf, (255, 220, 50, alpha), False,
                                  [(p[0] - g_ox, p[1] - g_oy) for p in bolt_points], thickness)
            screen.blit(glow_surf, (g_ox, g_oy))

            # Main bolt
            bolt_surf = pygame.Surface((200, 450), pygame.SRCALPHA)
            b_ox = cx - 100
            b_oy = cy - 400
            pygame.draw.lines(bolt_surf, (255, 255, 255, bolt_alpha), False,
                              [(p[0] - b_ox, p[1] - b_oy) for p in bolt_points], 2)
            pygame.draw.lines(bolt_surf, (255, 220, 80, bolt_alpha), False,
                              [(p[0] - b_ox, p[1] - b_oy) for p in bolt_points], 1)
            screen.blit(bolt_surf, (b_ox, b_oy))

            # Expanding electrical field on ground
            field_progress = min(1.0, (self.timer - self.delay) / 0.5)
            field_radius = int(self.radius * (0.3 + 0.7 * field_progress))
            field_surf = pygame.Surface((field_radius * 2, field_radius * 2), pygame.SRCALPHA)

            # Outer ring
            ring_alpha = int(150 * (1 - field_progress))
            pygame.draw.circle(field_surf, (100, 80, 200, ring_alpha),
                               (field_radius, field_radius), field_radius, 2)
            # Inner glow
            inner_alpha = int(80 * (1 - field_progress * 0.5))
            pygame.draw.circle(field_surf, (200, 180, 255, inner_alpha),
                               (field_radius, field_radius), int(field_radius * 0.7))
            # Core flash
            core_alpha = min(200, int(self.flash_alpha * 0.8))
            pygame.draw.circle(field_surf, (255, 255, 255, core_alpha),
                               (field_radius, field_radius), int(field_radius * 0.2))

            screen.blit(field_surf, (cx - field_radius, cy - field_radius))

            # Arc sparks on ground
            import random as rnd
            spark_surf = pygame.Surface((int(self.radius * 2), int(self.radius * 2)), pygame.SRCALPHA)
            s_ox = cx - int(self.radius)
            s_oy = cy - int(self.radius)
            for _ in range(int(8 * (1 - field_progress) + 2)):
                angle = rnd.uniform(0, math.pi * 2)
                dist = rnd.uniform(0, field_radius)
                sx = cx + math.cos(angle) * dist - s_ox
                sy = cy + math.sin(angle) * dist - s_oy
                ex = sx + rnd.uniform(-10, 10)
                ey = sy + rnd.uniform(-10, 10)
                spark_alpha = int(200 * (1 - field_progress))
                pygame.draw.line(spark_surf, (255, 255, 200, spark_alpha), (sx, sy), (ex, ey), 1)
            screen.blit(spark_surf, (s_ox, s_oy))


class EntanglingRoots:
    """
    Missile that flies forward and bursts into roots that immobilize enemies.

    Two phases:
      1. Flying phase — a seed/sprout projectile travels in a direction.
      2. Burst phase — on impact or max range, roots explode outward.
    """
    def __init__(self, pos, direction, speed, max_range, radius, root_duration, damage=0,
                 expansion_duration=0.5):
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()
        self.speed = speed
        self.max_range = max_range
        self.radius = radius
        self.root_duration = root_duration
        self.damage = damage
        self.alive = True
        self.traveled = 0.0
        self.timer = 0.0
        self.expansion_duration = expansion_duration
        self.damage_applied = False
        self.animation_time = 0.0
        self.vine_points = []
        self.bursting = False
        self.trail = []
        self.trail_length = 10
        self.root_particles = []
        self.leaf_particles = []

    def get_rect(self):
        if self.bursting:
            size = int(self.radius * 2)
            rect = pygame.Rect(0, 0, size, size)
            rect.center = (int(self.pos.x), int(self.pos.y))
            return rect
        return pygame.Rect(int(self.pos.x) - 8, int(self.pos.y) - 8, 16, 16)

    def _trigger_burst(self):
        if self.bursting:
            return
        self.bursting = True
        self.timer = 0.0
        self.damage_applied = False
        # Spawn initial root burst leaf particles
        for _ in range(30):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(60, 200)
            self.leaf_particles.append({
                "pos": pygame.Vector2(self.pos),
                "vel": pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                "max_life": (ml := random.uniform(0.3, 0.6)),
                "life": ml,
                "size": random.uniform(2.0, 5.0),
                "color": random.choice([
                    (60, 200, 60), (100, 220, 80),
                    (160, 255, 120), (200, 255, 180),
                    (40, 160, 40),
                ]),
            })

    def update(self, dt, obstacles, enemies):
        if not self.alive:
            return
        self.animation_time += dt

        if self.bursting:
            self.timer += dt
            progress = min(1.0, self.timer / self.expansion_duration)

            if not self.damage_applied and progress >= 0.2:
                for enemy in enemies:
                    if enemy.is_dead():
                        continue
                    enemy_rect = enemy.get_rect()
                    enemy_center = pygame.Vector2(enemy_rect.centerx, enemy_rect.centery)
                    if (enemy_center - self.pos).length_squared() <= self.radius * self.radius:
                        if self.damage > 0:
                            enemy.take_damage(self.damage)
                        enemy.add_effect(RootEffect(self.root_duration))
                self.damage_applied = True

            # Root branch particles
            for _ in range(3):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(0, self.radius * progress)
                self.root_particles.append({
                    "angle": angle,
                    "dist": dist,
                    "max_life": (ml := random.uniform(0.2, 0.4)),
                    "life": ml,
                    "width": random.uniform(2.0, 4.0),
                })
            if len(self.root_particles) > 60:
                self.root_particles = self.root_particles[-60:]

            # Leaf particles drift and fade
            for p in self.leaf_particles[:]:
                p["pos"] += p["vel"] * dt
                p["vel"] *= 0.93
                p["vel"].y += 20 * dt  # slight gravity
                p["life"] -= dt
                if p["life"] <= 0:
                    self.leaf_particles.remove(p)

            if self.timer >= self.expansion_duration:
                self.alive = False
            return

        # Flying phase
        movement = self.direction * self.speed * dt
        self.pos += movement
        self.traveled += movement.length()
        self.trail.append(pygame.Vector2(self.pos))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)

        rect = self.get_rect()
        for wall in obstacles:
            if rect.colliderect(wall):
                self._trigger_burst()
                return

        for enemy in enemies:
            if enemy.is_dead():
                continue
            if rect.colliderect(enemy.get_rect()):
                self._trigger_burst()
                return

        if self.traveled >= self.max_range:
            self._trigger_burst()

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        if not self.bursting:
            cx = int(self.pos.x - camera_offset.x)
            cy = int(self.pos.y - camera_offset.y)
            t = self.animation_time

            # Trail
            for i, pos in enumerate(self.trail):
                alpha = int(100 * (i / len(self.trail)))
                radius = int(2 + 4 * (i / len(self.trail)))
                t_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(t_surf, (40, 160, 40, alpha), (radius, radius), radius)
                screen.blit(t_surf, (pos.x - radius - camera_offset.x, pos.y - radius - camera_offset.y))

            pulse = 0.5 + 0.5 * math.sin(t * 10)

            # Outer glow
            glow_size = 14 + int(4 * pulse)
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (60, 220, 60, int(40 + 20 * pulse)), (glow_size, glow_size), glow_size)
            screen.blit(glow_surf, (cx - glow_size, cy - glow_size))

            # Root tendrils trailing from seed
            for i in range(4):
                ta = t * 4 + i * math.pi / 2
                td = 4 + 5 * pulse
                tx = cx + math.cos(ta) * td
                ty = cy + math.sin(ta) * td
                ex = tx + math.cos(ta + 0.3) * (6 + 4 * pulse)
                ey = ty + math.sin(ta + 0.3) * (6 + 4 * pulse)
                pygame.draw.line(screen, (40, 140, 40, int(150 + 50 * pulse)),
                                 (tx, ty), (ex, ey), max(1, int(2 + pulse)))

            # Seed body
            pygame.draw.circle(screen, (50, 170, 50), (cx, cy), 7)
            pygame.draw.circle(screen, (100, 210, 90), (cx, cy), 5)
            pygame.draw.circle(screen, (180, 255, 160), (cx - 1, cy - 1), 2)

            # Leaf wings
            leaf_w = 4 + 2 * pulse
            for side in (-1, 1):
                lx = cx + side * 6
                ly = cy - 2 + 2 * math.sin(t * 8)
                leaf_surf = pygame.Surface((int(leaf_w * 2), 6), pygame.SRCALPHA)
                pygame.draw.ellipse(leaf_surf, (80, 200, 60, 200), (0, 0, int(leaf_w * 2), 4))
                screen.blit(leaf_surf, (lx - leaf_w, ly - 2))
            return

        # Burst phase
        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        progress = min(1.0, self.timer / self.expansion_duration)
        current_radius = int(self.radius * progress)

        if current_radius <= 0:
            return

        t = self.animation_time

        # Root branches shooting outward
        branch_count = int(10 + 6 * progress)
        for i in range(branch_count):
            ba = t * 0.5 + i * (math.pi * 2 / branch_count) + random.uniform(-0.1, 0.1)
            bd = random.uniform(current_radius * 0.3, current_radius)
            bx = cx + math.cos(ba) * bd
            by = cy + math.sin(ba) * bd
            branch_alpha = int(200 * (1 - progress) * (1 - bd / self.radius))
            branch_width = max(1, int(3 * (1 - progress) * (1 - bd / self.radius * 0.5)))
            # Draw root branch as a jagged line
            pts = [(cx, cy)]
            segs = 3
            for s in range(1, segs + 1):
                frac = s / segs
                jag = random.uniform(-3, 3) * frac
                spx = cx + math.cos(ba + jag * 0.03) * bd * frac
                spy = cy + math.sin(ba + jag * 0.03) * bd * frac
                pts.append((spx, spy))
            for j in range(len(pts) - 1):
                pygame.draw.line(screen, (40, 140, 40, branch_alpha),
                                 pts[j], pts[j + 1], branch_width)

        # Green burst aura
        surface = pygame.Surface((current_radius * 2, current_radius * 2), pygame.SRCALPHA)
        outer_alpha = int(80 * (1 - progress * 0.5))
        pygame.draw.circle(surface, (40, 160, 40, outer_alpha), (current_radius, current_radius), current_radius)
        mid_r = max(1, int(current_radius * 0.6))
        mid_alpha = int(120 * (1 - progress * 0.3))
        pygame.draw.circle(surface, (80, 200, 80, mid_alpha), (current_radius, current_radius), mid_r)
        inner_r = max(1, int(current_radius * 0.3))
        inner_alpha = int(160 * (1 - progress * 0.2))
        pygame.draw.circle(surface, (180, 255, 160, inner_alpha), (current_radius, current_radius), inner_r)
        screen.blit(surface, (cx - current_radius, cy - current_radius))

        # Outer green ring
        ring_alpha = int(180 * (1 - progress))
        pygame.draw.circle(screen, (60, 180, 60, ring_alpha), (cx, cy), current_radius, max(2, int(3 * (1 - progress) + 1)))

        # Leaf particles spiraling outward
        for p in self.leaf_particles:
            life_r = min(1.0, p["life"] / p["max_life"]) if p["max_life"] > 0 else 0
            if life_r <= 0:
                continue
            px = int(p["pos"].x - camera_offset.x)
            py = int(p["pos"].y - camera_offset.y)
            leaf_alpha = int(200 * life_r)
            leaf_size = max(1, int(p["size"] * life_r))
            r, g, b = p["color"]
            # Leaf shape (small rotated ellipse)
            leaf_surf = pygame.Surface((leaf_size * 2, leaf_size), pygame.SRCALPHA)
            pygame.draw.ellipse(leaf_surf, (r, g, b, leaf_alpha),
                                (0, 0, leaf_size * 2, leaf_size))
            screen.blit(leaf_surf, (px - leaf_size, py - leaf_size // 2))

        # Root vine tendrils on the ground
        for rp in self.root_particles:
            vr = min(1.0, rp["life"] / rp["max_life"]) if rp["max_life"] > 0 else 0
            if vr <= 0:
                continue
            angle = rp["angle"]
            dist = rp["dist"]
            vx = cx + math.cos(angle) * dist
            vy = cy + math.sin(angle) * dist
            tendril_len = 6 + 4 * math.sin(angle * 3 + t * 2)
            ex = vx + math.cos(angle + 0.4) * tendril_len
            ey = vy + math.sin(angle + 0.4) * tendril_len
            vine_alpha = int(160 * vr * (1 - dist / self.radius))
            vine_width = max(1, int(rp["width"] * vr))
            pygame.draw.line(screen, (50, 130, 40, vine_alpha), (vx, vy), (ex, ey), vine_width)

        # Inner flash (early burst)
        if progress < 0.3:
            flash_alpha = int(160 * (1 - progress / 0.3))
            flash_r = int(current_radius * 0.5)
            flash_surf = pygame.Surface((flash_r * 2, flash_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (220, 255, 200, flash_alpha), (flash_r, flash_r), flash_r)
            screen.blit(flash_surf, (cx - flash_r, cy - flash_r))


class NatureBolt:
    """
    A nature bolt projectile fired by the Nature Spirit.

    Flies toward a target position with green visuals.
    """
    def __init__(self, pos, direction, speed, max_range, damage, target_pos=None, color=(80, 220, 80)):
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()

        self.speed = speed
        self.max_range = max_range
        self.damage = damage
        self.color = color
        self.alive = True
        self.traveled = 0.0
        self.animation_time = 0.0
        self.trail = []
        self.trail_length = 8
        self.target_pos = pygame.Vector2(target_pos) if target_pos else None
        self.leaf_particles = []

    def _size(self):
        return 12, 12

    def get_rect(self):
        width, height = self._size()
        rect = pygame.Rect(0, 0, width, height)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, enemies):
        if not self.alive:
            return

        self.animation_time += dt
        movement = self.direction * self.speed * dt
        self.pos += movement
        self.traveled += movement.length()

        self.trail.append(pygame.Vector2(self.pos))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)

        # Spawn leaf particles
        if random.random() < 0.4:
            perp = pygame.Vector2(-self.direction.y, self.direction.x)
            offset = perp * random.uniform(-6, 6)
            self.leaf_particles.append({
                "pos": pygame.Vector2(self.pos) + offset,
                "vel": perp * random.uniform(-20, 20) + pygame.Vector2(0, -10),
                "max_life": (ml := random.uniform(0.2, 0.5)),
                "life": ml,
                "size": random.uniform(1.5, 3.0),
                "color": random.choice([
                    (60, 200, 60), (100, 220, 80),
                    (160, 255, 120), (200, 255, 180),
                ]),
            })
        for p in self.leaf_particles[:]:
            p["pos"] += p["vel"] * dt
            p["vel"] *= 0.95
            p["life"] -= dt
            if p["life"] <= 0:
                self.leaf_particles.remove(p)

        rect = self.get_rect()
        for wall in obstacles:
            if rect.colliderect(wall):
                self.alive = False
                return

        if self.traveled >= self.max_range:
            self.alive = False

        if self.target_pos and self.pos.distance_to(self.target_pos) < 15:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        t = self.animation_time

        # Leaf particles
        for p in self.leaf_particles:
            life_r = min(1.0, p["life"] / p["max_life"]) if p["max_life"] > 0 else 0
            if life_r <= 0:
                continue
            px = int(p["pos"].x - camera_offset.x)
            py = int(p["pos"].y - camera_offset.y)
            leaf_alpha = int(150 * life_r)
            leaf_size = max(1, int(p["size"] * life_r))
            r, g, b = p["color"]
            l_surf = pygame.Surface((leaf_size * 2, leaf_size), pygame.SRCALPHA)
            pygame.draw.ellipse(l_surf, (r, g, b, leaf_alpha), (0, 0, leaf_size * 2, leaf_size))
            screen.blit(l_surf, (px - leaf_size, py - leaf_size // 2))

        # Trail
        for i, pos in enumerate(self.trail):
            alpha = int(100 * (i / len(self.trail)))
            radius = int(2 + 4 * (i / len(self.trail)))
            t_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(t_surf, (40, 180, 40, alpha), (radius, radius), radius)
            screen.blit(t_surf, (pos.x - radius - camera_offset.x, pos.y - radius - camera_offset.y))

        pulse = 0.5 + 0.5 * math.sin(t * 12)

        # Glow
        glow_size = int(12 + 4 * pulse)
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (60, 220, 60, int(50 + 20 * pulse)), (glow_size, glow_size), glow_size)
        screen.blit(glow_surf, (cx - glow_size, cy - glow_size))

        # Vine tendril trail behind the bolt
        for i in range(3):
            va = t * 6 + i * math.pi * 2 / 3
            vd = 4 + 2 * pulse
            vx = cx + math.cos(va) * vd
            vy = cy + math.sin(va) * vd
            vex = vx + math.cos(va + 0.3) * (5 + 3 * pulse)
            vey = vy + math.sin(va + 0.3) * (5 + 3 * pulse)
            pygame.draw.line(screen, (40, 160, 40, int(120 + 60 * pulse)),
                             (vx, vy), (vex, vey), max(1, int(2 + pulse)))

        # Body layers
        pygame.draw.circle(screen, (60, 180, 60), (cx, cy), 7)
        pygame.draw.circle(screen, (100, 220, 90), (cx, cy), 5)
        pygame.draw.circle(screen, (180, 255, 160), (cx - 1, cy - 1), 2)


class ArcaneMissile:
    """
    Homing arcane missile that seeks the nearest enemy.
    Crystal shard with orbiting sigils and a spiral trail.
    """
    def __init__(self, pos, direction, speed, max_range, damage, homing_strength=0.15):
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()
        self.speed = speed
        self.max_range = max_range
        self.damage = damage
        self.homing_strength = homing_strength
        self.alive = True
        self.traveled = 0.0
        self.animation_time = 0.0
        self.target = None
        self.trail = []
        self.trail_length = 14
        self.arcane_sparks = []
        self.orbit_angle = random.uniform(0, math.pi * 2)
        self.hit_effect = None

    def _size(self):
        return 14, 14

    def get_rect(self):
        w, h = self._size()
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def _acquire_target(self, enemies):
        closest_dist = float("inf")
        closest = None
        for enemy in enemies:
            if enemy.is_dead():
                continue
            enemy_center = pygame.Vector2(enemy.get_rect().center)
            d = self.pos.distance_squared_to(enemy_center)
            if d < closest_dist:
                closest_dist = d
                closest = enemy
        return closest

    def _spawn_hit_effect(self):
        """Create an arcane rift burst on death."""
        self.hit_effect = {
            "pos": pygame.Vector2(self.pos),
            "life": 0.4,
            "max_life": 0.4,
            "particles": [],
        }
        for _ in range(16):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(60, 200)
            self.hit_effect["particles"].append({
                "pos": pygame.Vector2(self.pos),
                "vel": pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                "max_life": (ml := random.uniform(0.2, 0.4)),
                "life": ml,
                "size": random.uniform(2, 5),
                "color": random.choice([
                    (200, 140, 255), (160, 80, 240),
                    (255, 200, 255), (120, 60, 220),
                ]),
            })

    def update(self, dt, obstacles, enemies):
        if not self.alive:
            if self.hit_effect is not None:
                self.hit_effect["life"] -= dt
                for p in self.hit_effect["particles"][:]:
                    p["pos"] += p["vel"] * dt
                    p["vel"] *= 0.92
                    p["life"] -= dt
                    if p["life"] <= 0:
                        self.hit_effect["particles"].remove(p)
                if self.hit_effect["life"] <= 0:
                    self.hit_effect = None
            return

        self.animation_time += dt
        self.orbit_angle += dt * 4.0

        # Acquire or refresh target
        if self.target is None or self.target.is_dead():
            self.target = self._acquire_target(enemies)

        # Homing toward target
        if self.target is not None and not self.target.is_dead():
            target_center = pygame.Vector2(self.target.get_rect().center)
            target_vec = target_center - self.pos
            if target_vec.length_squared() > 0:
                target_dir = target_vec.normalize()
                self.direction = self.direction.lerp(target_dir, self.homing_strength)
                if self.direction.length_squared() > 0:
                    self.direction = self.direction.normalize()

        movement = self.direction * self.speed * dt
        self.pos += movement
        self.traveled += movement.length()

        self.trail.append(pygame.Vector2(self.pos))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)

        # Spawn arcane sparks
        if random.random() < 0.6:
            perp = pygame.Vector2(-self.direction.y, self.direction.x)
            offset = perp * random.uniform(-10, 10)
            self.arcane_sparks.append({
                "pos": pygame.Vector2(self.pos) + offset,
                "vel": pygame.Vector2(self.direction) * random.uniform(-20, -5) + perp * random.uniform(-15, 15),
                "max_life": (ml := random.uniform(0.2, 0.5)),
                "life": ml,
                "size": random.uniform(1.5, 3.0),
                "color": random.choice([
                    (200, 150, 255), (160, 100, 240),
                    (220, 180, 255), (180, 120, 250),
                ]),
            })
        for s in self.arcane_sparks[:]:
            s["pos"] += s["vel"] * dt
            s["vel"] *= 0.95
            s["life"] -= dt
            if s["life"] <= 0:
                self.arcane_sparks.remove(s)

        rect = self.get_rect()
        for wall in obstacles:
            if rect.colliderect(wall):
                self._spawn_hit_effect()
                self.alive = False
                return

        if self.traveled >= self.max_range:
            self._spawn_hit_effect()
            self.alive = False
            return

        # Hit detection against enemies
        for enemy in enemies:
            if enemy.is_dead():
                continue
            enemy_rect = enemy.get_rect()
            if rect.colliderect(enemy_rect):
                enemy.take_damage(self.damage)
                self._spawn_hit_effect()
                self.alive = False
                return

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        t = self.animation_time

        # ── Draw hit effect ──
        if self.hit_effect is not None:
            progress = 1.0 - self.hit_effect["life"] / self.hit_effect["max_life"]
            # Expanding rift ring
            rift_r = int(10 + 40 * progress)
            rift_alpha = int(200 * (1 - progress))
            rift_surf = pygame.Surface((rift_r * 2, rift_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(rift_surf, (120, 60, 200, rift_alpha), (rift_r, rift_r), rift_r, max(1, int(3 * (1 - progress))))
            pygame.draw.circle(rift_surf, (200, 140, 255, rift_alpha // 2), (rift_r, rift_r), int(rift_r * 0.6), 1)
            screen.blit(rift_surf, (int(self.hit_effect["pos"].x - camera_offset.x - rift_r),
                                    int(self.hit_effect["pos"].y - camera_offset.y - rift_r)))
            # Rift shard burst
            for p in self.hit_effect["particles"]:
                life_r = min(1.0, p["life"] / p["max_life"]) if p["max_life"] > 0 else 0
                if life_r <= 0:
                    continue
                px = int(p["pos"].x - camera_offset.x)
                py = int(p["pos"].y - camera_offset.y)
                p_alpha = int(255 * life_r)
                p_size = max(1, int(p["size"] * life_r))
                r, g, b = p["color"]
                # Draw as small diamond shard
                pts = [
                    (px, py - p_size),
                    (px + p_size * 0.6, py),
                    (px, py + p_size),
                    (px - p_size * 0.6, py),
                ]
                shard_surf = pygame.Surface((p_size * 3, p_size * 3), pygame.SRCALPHA)
                pygame.draw.polygon(shard_surf, (r, g, b, p_alpha), [(p_size * 1.5, p_size * 1.5 - p_size),
                                        (p_size * 1.5 + p_size * 0.6, p_size * 1.5),
                                        (p_size * 1.5, p_size * 1.5 + p_size),
                                        (p_size * 1.5 - p_size * 0.6, p_size * 1.5)])
                screen.blit(shard_surf, (px - p_size * 1.5, py - p_size * 1.5))
                # Glow
                g_sz = p_size * 2
                g_surf = pygame.Surface((g_sz * 2, g_sz * 2), pygame.SRCALPHA)
                pygame.draw.circle(g_surf, (r, g, b, p_alpha // 3), (g_sz, g_sz), g_sz)
                screen.blit(g_surf, (px - g_sz, py - g_sz))
            return

        # ── Draw arcane sparks ──
        for s in self.arcane_sparks:
            life_r = min(1.0, s["life"] / s["max_life"]) if s["max_life"] > 0 else 0
            if life_r <= 0:
                continue
            sx = int(s["pos"].x - camera_offset.x)
            sy = int(s["pos"].y - camera_offset.y)
            s_alpha = int(200 * life_r)
            s_size = max(1, int(s["size"] * life_r))
            r, g, b = s["color"]
            sg_sz = s_size * 3
            sg = pygame.Surface((sg_sz * 2, sg_sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(sg, (r, g, b, s_alpha // 3), (sg_sz, sg_sz), sg_sz)
            screen.blit(sg, (sx - sg_sz, sy - sg_sz))
            pygame.draw.circle(screen, s["color"], (sx, sy), s_size)

        # ── Spiral trail ──
        perp = pygame.Vector2(-self.direction.y, self.direction.x)
        for i, pos in enumerate(self.trail):
            ratio = i / len(self.trail) if len(self.trail) > 0 else 0
            trail_alpha = int(80 * ratio)
            trail_radius = int(1 + 4 * ratio)
            # Spiral offset from center line
            spiral_offset = 6 * math.sin(t * 12 + i * 0.8)
            spiral_dir = perp * spiral_offset
            t_pos = pygame.Vector2(pos) + spiral_dir
            t_surf = pygame.Surface((trail_radius * 2, trail_radius * 2), pygame.SRCALPHA)
            # Color gradient: deep purple to bright pink
            tc = (
                int(120 + 80 * ratio),
                int(60 + 80 * ratio),
                int(200 + 55 * ratio),
            )
            pygame.draw.circle(t_surf, (*tc, trail_alpha), (trail_radius, trail_radius), trail_radius)
            screen.blit(t_surf, (t_pos.x - trail_radius - camera_offset.x,
                                 t_pos.y - trail_radius - camera_offset.y))

        # ── Crystal shard body ──
        pulse = 0.7 + 0.3 * math.sin(t * 12)
        fast_pulse = 0.5 + 0.5 * math.sin(t * 25)

        # Outer glow (hexagonal shape)
        glow_r = 14 + 4 * pulse
        glow_surf = pygame.Surface((int(glow_r * 2) + 8, int(glow_r * 2) + 8), pygame.SRCALPHA)
        g_center = (int(glow_r) + 4, int(glow_r) + 4)
        glow_a = int(40 + 30 * pulse)
        # Hexagonal glow
        glow_pts = []
        for i in range(6):
            a = t * 1.5 + i * (math.pi * 2 / 6)
            gx = g_center[0] + math.cos(a) * glow_r
            gy = g_center[1] + math.sin(a) * glow_r
            glow_pts.append((gx, gy))
        pygame.draw.polygon(glow_surf, (160, 80, 220, glow_a), glow_pts)
        pygame.draw.polygon(glow_surf, (200, 140, 255, glow_a // 2), glow_pts, 2)
        screen.blit(glow_surf, (cx - int(glow_r) - 4, cy - int(glow_r) - 4))

        # Crystal body — rotating diamond
        crystal_r = 6 + 2 * fast_pulse
        rot_angle = t * 3.0
        crystal_pts = []
        for i in range(4):
            a = rot_angle + i * (math.pi * 2 / 4)
            rx = cx + math.cos(a) * crystal_r
            ry = cy + math.sin(a) * crystal_r
            crystal_pts.append((rx, ry))
        # Outer crystal
        pygame.draw.polygon(screen, (140, 60, 210), crystal_pts)
        pygame.draw.polygon(screen, (200, 140, 255), crystal_pts, 2)
        # Inner crystal (smaller, counter-rotating)
        inner_r = crystal_r * 0.6
        inner_pts = []
        for i in range(4):
            a = -rot_angle + i * (math.pi * 2 / 4)
            rx = cx + math.cos(a) * inner_r
            ry = cy + math.sin(a) * inner_r
            inner_pts.append((rx, ry))
        pygame.draw.polygon(screen, (200, 160, 255), inner_pts)
        pygame.draw.polygon(screen, (230, 200, 255), inner_pts, 1)
        # Bright core
        core_r = max(2, int(crystal_r * 0.35))
        pygame.draw.circle(screen, (255, 230, 255), (cx, cy), core_r)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), max(1, core_r // 2))

        # ── Orbiting arcane sigils ──
        sigil_count = 3
        for i in range(sigil_count):
            sigil_angle = self.orbit_angle + i * (math.pi * 2 / sigil_count)
            sigil_dist = 14 + 4 * math.sin(t * 3.0 + i * 2.0)
            sx = cx + math.cos(sigil_angle) * sigil_dist
            sy = cy + math.sin(sigil_angle) * sigil_dist
            sigil_size = max(2, int(3 + 2 * math.sin(t * 5.0 + i * 1.5)))
            sigil_alpha = int(180 + 70 * math.sin(t * 6.0 + i * 2.3))
            # Draw sigil as small 3-point star
            star_pts = []
            for j in range(3):
                a = sigil_angle + j * (math.pi * 2 / 3)
                spx = sx + math.cos(a) * sigil_size
                spy = sy + math.sin(a) * sigil_size
                star_pts.append((spx, spy))
            pygame.draw.polygon(screen, (180, 120, 255, sigil_alpha), star_pts)
            pygame.draw.polygon(screen, (220, 180, 255, sigil_alpha), star_pts, 1)
            # Glow dot at sigil center
            pygame.draw.circle(screen, (255, 220, 255, sigil_alpha), (int(sx), int(sy)), max(1, sigil_size // 2))


class DarkPact:
    """
    Shadow burst that deals damage to all nearby enemies from the caster's position.

    Attributes:
        pos (pygame.Vector2): Center position of the burst.
        damage (int): Damage dealt to each enemy.
        radius (float): Maximum expansion radius.
        alive (bool): Whether the effect is still active.
        expansion_time (float): Current expansion time.
        expansion_duration (float): How long the visual expansion lasts.
        current_radius (float): Current visual radius.
    """
    def __init__(self, pos, damage, radius=150.0, expansion_duration=0.5):
        self.pos = pygame.Vector2(pos)
        self.damage = damage
        self.radius = radius
        self.alive = True
        self.expansion_time = 0.0
        self.expansion_duration = expansion_duration
        self.current_radius = 0.0
        self.damage_applied = False
        self.animation_time = 0.0
        self.smoke_particles = []

    def get_rect(self):
        size = int(self.radius * 2)
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, enemies):
        if not self.alive:
            return

        self.animation_time += dt
        self.expansion_time += dt
        progress = min(1.0, self.expansion_time / self.expansion_duration)
        self.current_radius = self.radius * progress

        if not self.damage_applied and progress >= 0.3:
            for enemy in enemies:
                if enemy.is_dead():
                    continue
                enemy_rect = enemy.get_rect()
                enemy_center = pygame.Vector2(enemy_rect.centerx, enemy_rect.centery)
                if (enemy_center - self.pos).length_squared() <= self.radius * self.radius:
                    enemy.take_damage(self.damage)
            self.damage_applied = True

        # Spawn rising smoke particles
        spawn_count = max(1, int(15 * dt * (1 - progress * 0.5)))
        for _ in range(spawn_count):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(0, self.current_radius)
            self.smoke_particles.append({
                "pos": pygame.Vector2(self.pos) + pygame.Vector2(math.cos(angle), math.sin(angle)) * dist,
                "vel": pygame.Vector2(random.uniform(-8, 8), random.uniform(-30, -10)),
                "max_life": (ml := random.uniform(0.3, 0.7)),
                "life": ml,
                "size": random.uniform(3.0, 7.0),
                "color": random.choice([
                    (60, 20, 100),
                    (100, 50, 160),
                    (140, 80, 200),
                    (40, 10, 80),
                ]),
            })

        for p in self.smoke_particles[:]:
            p["pos"] += p["vel"] * dt
            p["vel"] *= 0.96
            p["life"] -= dt
            if p["life"] <= 0:
                self.smoke_particles.remove(p)

        if self.expansion_time >= self.expansion_duration:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        progress = min(1.0, self.expansion_time / self.expansion_duration)
        radius = int(self.current_radius)

        if radius <= 0:
            return

        t = self.animation_time

        # ── Shadow tendrils reaching outward ──
        tendril_count = int(6 + 4 * (1 - progress))
        for i in range(tendril_count):
            t_angle = t * 2.0 + i * (math.pi * 2 / tendril_count)
            tendril_len = int(radius * (0.6 + 0.4 * math.sin(t * 4.0 + i * 1.5)))
            end_x = cx + math.cos(t_angle) * tendril_len
            end_y = cy + math.sin(t_angle) * tendril_len
            tendril_alpha = int(80 * (1 - progress))
            # Jagged tendril (3 segments)
            pts = [(cx, cy)]
            for seg in range(1, 4):
                frac = seg / 3
                jitter = random.uniform(-4, 4) * frac
                seg_x = cx + math.cos(t_angle + jitter * 0.05) * tendril_len * frac
                seg_y = cy + math.sin(t_angle + jitter * 0.05) * tendril_len * frac
                pts.append((seg_x, seg_y))
            if len(pts) >= 2:
                for j in range(len(pts) - 1):
                    pygame.draw.line(screen, (80, 30, 140, tendril_alpha),
                                     pts[j], pts[j + 1], max(1, int(2 - progress * 1.5)))

        # ── Pulsing shadow rings ──
        ring_count = 3
        for i in range(ring_count):
            ring_r = int(radius * (0.2 + 0.8 * ((i + 1) / ring_count)))
            ring_phase = (t * 3.0 + i * 1.2) % 1.0
            ring_pulse = int(40 + 30 * math.sin(t * 5.0 + i * 2.0))
            pygame.draw.circle(screen, (100, 40, 160, ring_pulse), (cx, cy), ring_r, max(1, int(2 - progress)))

        # ── Outer shadow ring ──
        ring_alpha = int(180 * (1 - progress))
        pygame.draw.circle(screen, (80, 40, 120, ring_alpha), (cx, cy), radius, max(2, int(3 * (1 - progress) + 1)))

        # ── Main dark burst ──
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        outer_alpha = int(100 * (1 - progress * 0.5))
        pygame.draw.circle(surface, (60, 20, 100, outer_alpha), (radius, radius), radius)
        mid_r = max(1, int(radius * 0.6))
        mid_alpha = int(140 * (1 - progress * 0.3))
        pygame.draw.circle(surface, (100, 40, 160, mid_alpha), (radius, radius), mid_r)
        inner_r = max(1, int(radius * 0.3))
        inner_alpha = int(180 * (1 - progress * 0.2))
        pygame.draw.circle(surface, (160, 80, 220, inner_alpha), (radius, radius), inner_r)
        # Void center
        void_r = max(1, int(radius * 0.15))
        pygame.draw.circle(surface, (20, 5, 50, 200), (radius, radius), void_r)

        screen.blit(surface, (cx - radius, cy - radius))

        # ── Rising smoke particles ──
        for p in self.smoke_particles:
            life_r = min(1.0, p["life"] / p["max_life"]) if p["max_life"] > 0 else 0
            if life_r <= 0:
                continue
            px = int(p["pos"].x - camera_offset.x)
            py = int(p["pos"].y - camera_offset.y)
            smoke_alpha = int(120 * life_r)
            smoke_size = max(1, int(p["size"] * (0.5 + 0.5 * life_r)))
            r, g, b = p["color"]
            sg = pygame.Surface((smoke_size * 3, smoke_size * 3), pygame.SRCALPHA)
            pygame.draw.circle(sg, (r, g, b, smoke_alpha), (smoke_size * 1.5, smoke_size * 1.5), smoke_size * 1.5)
            screen.blit(sg, (px - smoke_size * 1.5, py - smoke_size * 1.5))

        # ── Shadow wisps ──
        for _ in range(int(8 * (1 - progress) + 2)):
            w_angle = random.uniform(0, math.pi * 2)
            w_dist = random.uniform(0, radius)
            w_x = cx + math.cos(w_angle) * w_dist
            w_y = cy + math.sin(w_angle) * w_dist
            w_size = random.randint(1, 4)
            w_color = random.choice([(140, 80, 200), (180, 120, 240), (100, 60, 160)])
            pygame.draw.circle(screen, w_color, (int(w_x), int(w_y)), w_size)

        # ── Inner flash (early burst) ──
        if progress < 0.3:
            flash_alpha = int(160 * (1 - progress / 0.3))
            flash_r = int(radius * 0.5)
            flash_surf = pygame.Surface((flash_r * 2, flash_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (200, 140, 255, flash_alpha), (flash_r, flash_r), flash_r)
            screen.blit(flash_surf, (cx - flash_r, cy - flash_r))


class Afterimage:
    """
    Short-lived afterimage left by Void Walker dodge.
    Deals 18 damage once in a small area at the player's previous position.
    """
    def __init__(self, pos, damage=18, radius=70.0, duration=0.7):
        import random
        self.pos = pygame.Vector2(pos)
        self.damage = damage
        self.radius = radius
        self.alive = True
        self.life = 0.0
        self.max_life = duration
        self.damage_applied = False
        self.angle = random.uniform(0, math.pi * 2)
        self.rot_speed = random.uniform(-1.0, 1.0)

    def get_rect(self):
        size = int(self.radius * 3)
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, enemies):
        if not self.alive:
            return
        self.life += dt
        self.angle += self.rot_speed * dt
        if not self.damage_applied and self.life >= 0.05:
            for enemy in enemies:
                if enemy.is_dead():
                    continue
                enemy_rect = enemy.get_rect()
                enemy_center = pygame.Vector2(enemy_rect.centerx, enemy_rect.centery)
                if (enemy_center - self.pos).length_squared() <= self.radius * self.radius:
                    enemy.take_damage(self.damage)
            self.damage_applied = True
        if self.life >= self.max_life:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)
        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        progress = self.life / self.max_life if self.max_life > 0 else 0
        alpha = int(200 * (1 - progress))

        # ── Player silhouette (humanoid shape) ──
        if alpha > 10:
            sil_surf = pygame.Surface((80, 100), pygame.SRCALPHA)
            # Head
            pygame.draw.ellipse(sil_surf, (120, 200, 120, alpha), (22, 5, 36, 36))
            # Body
            pygame.draw.ellipse(sil_surf, (100, 180, 100, alpha), (15, 38, 50, 55))
            # Arms
            pygame.draw.ellipse(sil_surf, (100, 180, 100, alpha // 2), (2, 40, 18, 40))
            pygame.draw.ellipse(sil_surf, (100, 180, 100, alpha // 2), (60, 40, 18, 40))
            # Legs
            pygame.draw.ellipse(sil_surf, (100, 180, 100, alpha // 2), (18, 85, 20, 30))
            pygame.draw.ellipse(sil_surf, (100, 180, 100, alpha // 2), (42, 85, 20, 30))
            screen.blit(sil_surf, (cx - 40, cy - 50))

        # ── Expanding ghostly ring ──
        ring_radius = int(self.radius * (0.5 + 1.0 * progress))
        ring_alpha = int(alpha * 0.6)
        if ring_alpha > 5:
            pygame.draw.circle(screen, (140, 220, 140, ring_alpha), (cx, cy), ring_radius, 3)

        # ── Inner glow ──
        glow_radius = max(1, int(self.radius * 0.5 * (1 - progress)))
        glow_alpha = int(alpha * 0.3)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (160, 240, 160, glow_alpha), (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surf, (cx - glow_radius, cy - glow_radius))

        # ── Rotating nature sigil ──
        if alpha > 30:
            sigil_points = 6
            sigil_r = int(self.radius * 0.35)
            for i in range(sigil_points):
                a = self.angle + i * (math.pi * 2 / sigil_points)
                sx = cx + math.cos(a) * sigil_r
                sy = cy + math.sin(a) * sigil_r
                pygame.draw.circle(screen, (100, 220, 100, alpha), (int(sx), int(sy)), 4)

        # ── Sparkles ──
        import random
        for _ in range(int(8 * (1 - progress))):
            sp_angle = random.uniform(0, math.pi * 2)
            sp_dist = random.uniform(0, self.radius)
            sp_x = cx + math.cos(sp_angle) * sp_dist
            sp_y = cy + math.sin(sp_angle) * sp_dist
            sp_size = random.randint(2, 4)
            sp_alpha = int(alpha * 0.8)
            sp_color = random.choice([(180, 255, 180), (140, 230, 140), (220, 255, 200)])
            pygame.draw.circle(screen, sp_color, (int(sp_x), int(sp_y)), sp_size)


class ElementalBurst:
    """
    Burst of elemental energy triggered by a dual-element combo.
    Deals damage in an area with a colorful elemental visual.
    """
    def __init__(self, pos, damage, radius=180.0, duration=0.8):
        self.pos = pygame.Vector2(pos)
        self.damage = damage
        self.radius = radius
        self.alive = True
        self.life = 0.0
        self.max_life = duration
        self.damage_applied = False

    def get_rect(self):
        size = int(self.radius * 2)
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, enemies):
        if not self.alive:
            return
        self.life += dt
        if not self.damage_applied and self.life >= 0.1:
            for enemy in enemies:
                if enemy.is_dead():
                    continue
                enemy_rect = enemy.get_rect()
                enemy_center = pygame.Vector2(enemy_rect.centerx, enemy_rect.centery)
                if (enemy_center - self.pos).length_squared() <= self.radius * self.radius:
                    enemy.take_damage(self.damage)
            self.damage_applied = True
        if self.life >= self.max_life:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)
        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        t = self.life
        progress = self.life / self.max_life if self.max_life > 0 else 0
        alpha = int(200 * (1 - progress))
        radius = int(self.radius * (0.2 + 0.8 * progress))

        # ── Outer vortex glow ──
        glow_r = radius + 20
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        glow_a = int(40 * (1 - progress))
        for gr in range(glow_r, 0, -4):
            fade = 1 - gr / glow_r
            c = (
                int(200 * fade + 60 * (1 - fade)),
                int(100 * fade + 180 * (1 - fade)),
                int(50 * fade + 200 * (1 - fade)),
                int(glow_a * fade),
            )
            pygame.draw.circle(glow_surf, c, (glow_r, glow_r), gr)
        screen.blit(glow_surf, (cx - glow_r, cy - glow_r))

        # ── Spiral vortex arms ──
        arm_count = 3
        arm_colors = [
            (255, 80, 30),    # fire
            (80, 180, 255),   # ice
            (220, 220, 60),   # lightning
        ]
        for arm in range(arm_count):
            base_angle = t * 2.5 + arm * (math.pi * 2 / arm_count)
            steps = 20
            for i in range(steps):
                frac = i / steps
                a = base_angle + frac * math.pi * 1.5
                dist = radius * frac
                if dist < 4:
                    continue
                px = cx + math.cos(a) * dist
                py = cy + math.sin(a) * dist
                size = max(1, int(4 * (1 - frac) * (1 - progress * 0.3)))
                arm_alpha = int(alpha * (1 - frac) * 0.8)
                blend = (arm / arm_count)
                r = int(arm_colors[arm][0] * (1 - blend * 0.4) + arm_colors[(arm + 1) % arm_count][0] * (blend * 0.4))
                g = int(arm_colors[arm][1] * (1 - blend * 0.4) + arm_colors[(arm + 1) % arm_count][1] * (blend * 0.4))
                b = int(arm_colors[arm][2] * (1 - blend * 0.4) + arm_colors[(arm + 1) % arm_count][2] * (blend * 0.4))
                color = (min(255, r), min(255, g), min(255, b), arm_alpha)
                glow_size = size * 3
                gsurf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(gsurf, (r, g, b, arm_alpha // 3), (glow_size, glow_size), glow_size)
                screen.blit(gsurf, (int(px - glow_size), int(py - glow_size)))
                pygame.draw.circle(screen, color, (int(px), int(py)), size)

        # ── Trailing particles pulled into vortex ──
        import random
        for _ in range(int(15 * (1 - progress))):
            trail_angle = random.uniform(0, math.pi * 2)
            trail_dist = random.uniform(radius * 0.3, radius * 0.95)
            spiral_offset = t * 3.0 + trail_angle * 0.5
            px = cx + math.cos(trail_angle + spiral_offset) * trail_dist
            py = cy + math.sin(trail_angle + spiral_offset) * trail_dist
            trail_size = random.randint(1, 3)
            trail_alpha = int(alpha * 0.5 * (1 - trail_dist / radius))
            trail_color = random.choice([
                (255, 180, 80, trail_alpha), (150, 210, 255, trail_alpha),
                (230, 230, 140, trail_alpha), (255, 220, 180, trail_alpha),
            ])
            pygame.draw.circle(screen, trail_color, (int(px), int(py)), trail_size)

        # ── Bright pulsing core ──
        core_pulse = 0.7 + 0.3 * math.sin(t * 15.0)
        core_r = max(1, int(radius * 0.15 * core_pulse))
        core_surf = pygame.Surface((core_r * 2, core_r * 2), pygame.SRCALPHA)
        core_a = int(alpha * 0.9)
        pygame.draw.circle(core_surf, (255, 230, 180, core_a), (core_r, core_r), core_r)
        inner_r = max(1, int(core_r * 0.5))
        pygame.draw.circle(core_surf, (255, 255, 230, core_a), (core_r, core_r), inner_r)
        screen.blit(core_surf, (cx - core_r, cy - core_r))

        # ── Energy wisps arcing outward ──
        wisp_count = int(6 * (1 - progress))
        for i in range(wisp_count):
            w_angle = t * 4.0 + i * (math.pi * 2 / wisp_count)
            w_dist = radius * (0.3 + 0.7 * math.sin(t * 3.0 + i * 1.5))
            if w_dist < 5:
                continue
            wx = cx + math.cos(w_angle) * w_dist
            wy = cy + math.sin(w_angle) * w_dist
            w_alpha = int(alpha * 0.4 * (1 - w_dist / radius))
            w_color = random.choice([
                (255, 200, 120, w_alpha), (180, 230, 255, w_alpha),
                (240, 240, 180, w_alpha),
            ])
            pygame.draw.line(screen, w_color, (cx, cy), (int(wx), int(wy)), max(1, int(2 * (1 - progress))))
