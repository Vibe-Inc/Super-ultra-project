import math
import random
import pygame
from database.effects import BurnEffect, ConfusionEffect, DizzinessEffect, FreezeEffect, PoisonEffect, SlowEffect, RootEffect
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
        trail (list):
            Position history for the visual trail effect.
        trail_length (int):
            Maximum number of trail points stored.

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
        trail (list):
            Position history for the visual trail effect.
        trail_length (int):
            Maximum number of trail points stored.
        animation_time (float):
            Accumulated time for visual animations.
        sparkle_particles (list):
            Sparkle particle effects emitted during flight.
        sigil_angle (float):
            Current rotation angle for the orbiting sigil effect.

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
        self.sparkle_particles = []
        self.sigil_angle = 0.0

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

        self.sigil_angle += dt * 4.0

        self.sparkle_particles.append({
            "pos": pygame.Vector2(self.pos) + pygame.Vector2(random.uniform(-4, 4), random.uniform(-4, 4)),
            "vel": pygame.Vector2(random.uniform(-3, 3), random.uniform(-3, 3)),
            "life": random.uniform(0.2, 0.5),
            "max_life": random.uniform(0.2, 0.5),
            "size": random.uniform(1.0, 2.5),
        })
        for sp in self.sparkle_particles[:]:
            sp["pos"] += sp["vel"] * dt
            sp["vel"] *= 0.95
            sp["life"] -= dt
            if sp["life"] <= 0:
                self.sparkle_particles.remove(sp)

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

        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        t = self.animation_time

        pulse = (math.sin(t * 12) + 1.0) * 0.5
        hue_shift = (math.sin(t * 3.0) + 1.0) * 0.5

        r = int(70 + 60 * hue_shift)
        g = int(140 + 60 * (1 - hue_shift))
        b = int(255 - 60 * hue_shift)
        current_color = (r, g, b)

        core_r_val = int(200 + 40 * (1 - hue_shift))
        core_g_val = int(220 + 30 * (1 - hue_shift))
        core_b_val = 255
        core_color = (core_r_val, core_g_val, core_b_val)

        for i, pos in enumerate(self.trail):
            ratio = i / len(self.trail) if len(self.trail) > 0 else 0
            if ratio <= 0:
                continue
            wobble = math.sin(t * 8 + i * 1.2) * 3
            alpha = int(100 * ratio)
            radius = int(2 + 5 * ratio)
            tx = int(pos.x - camera_offset.x) + int(wobble)
            ty = int(pos.y - camera_offset.y) + int(wobble * 0.5)
            t_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            tr = int(r * (0.3 + 0.7 * ratio))
            tg = int(g * (0.3 + 0.7 * ratio))
            tb = int(b * (0.3 + 0.7 * ratio))
            pygame.draw.circle(t_surf, (tr, tg, tb, alpha), (radius, radius), radius)
            screen.blit(t_surf, (tx - radius, ty - radius))

        for sp in self.sparkle_particles:
            life_r = sp["life"] / sp["max_life"] if sp["max_life"] > 0 else 0
            if life_r <= 0:
                continue
            alpha = int(180 * life_r)
            size = max(1, int(sp["size"] * life_r))
            sx = int(sp["pos"].x - camera_offset.x)
            sy = int(sp["pos"].y - camera_offset.y)
            glow_sz = size * 4
            g_surf = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(g_surf, (*core_color, alpha // 2), (glow_sz, glow_sz), glow_sz)
            screen.blit(g_surf, (sx - glow_sz, sy - glow_sz))
            pygame.draw.circle(screen, core_color, (sx, sy), size)

        glow_size = int(14 + 6 * pulse)
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*current_color, int(30 + 25 * pulse)), (glow_size, glow_size), glow_size)
        screen.blit(glow_surf, (cx - glow_size, cy - glow_size))

        ring_r = int(10 + 4 * pulse)
        ring_a = int(40 + 30 * pulse)
        pygame.draw.circle(screen, (*current_color, ring_a), (cx, cy), ring_r, 2)

        sigil_count = 2
        for i in range(sigil_count):
            angle = self.sigil_angle + i * math.pi
            s_dist = 12 + 3 * math.sin(t * 2 + i * 1.5)
            sx = cx + int(math.cos(angle) * s_dist)
            sy = cy + int(math.sin(angle) * s_dist)
            s_size = 3
            s_alpha = int(120 + 80 * math.sin(t * 5 + i * 2))
            s_surf = pygame.Surface((s_size * 4, s_size * 4), pygame.SRCALPHA)
            sr = (r + 255) // 2
            sg = (g + 255) // 2
            sb = (b + 255) // 2
            points = [
                (s_size * 2, 0),
                (s_size * 2 + s_size, s_size * 2),
                (s_size * 2, s_size * 4),
                (s_size * 2 - s_size, s_size * 2),
            ]
            pygame.draw.polygon(s_surf, (sr, sg, sb, s_alpha), points)
            screen.blit(s_surf, (sx - s_size * 2, sy - s_size * 2))

        body_r = 7
        pygame.draw.circle(screen, current_color, (cx, cy), body_r)
        inner_r = max(1, int(body_r * 0.6))
        pygame.draw.circle(screen, core_color, (cx, cy), inner_r)
        core_r2 = max(1, int(inner_r * 0.5))
        pygame.draw.circle(screen, (240, 245, 255), (cx, cy), core_r2)


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
        animation_time (float):
            Accumulated time for visual animations.
        spark_particles (list):
            Fuse spark particle effects.
        smoke_particles (list):
            Smoke particle effects during explosion.
        shrapnel_particles (list):
            Shrapnel debris particles during explosion.

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
        self.spark_particles = []
        self.smoke_particles = []
        self.shrapnel_particles = []

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
        self.shrapnel_particles = []
        for _ in range(12):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(60, 200)
            self.shrapnel_particles.append({
                "pos": pygame.Vector2(self.pos),
                "vel": pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                "size": random.uniform(2, 5),
                "color": random.choice([(100, 85, 70), (140, 120, 100), (170, 150, 120)]),
                "life": random.uniform(0.3, 0.6),
                "max_life": random.uniform(0.3, 0.6),
            })

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

            for sp in self.shrapnel_particles[:]:
                sp["pos"] += sp["vel"] * dt
                sp["vel"] *= 0.9
                sp["size"] *= 0.98
                sp["life"] -= dt
                if sp["life"] <= 0:
                    self.shrapnel_particles.remove(sp)

            if self.explosion_timer >= self.explosion_duration:
                self.alive = False
            return

        movement = self.direction * self.speed * dt
        self.pos += movement
        self.traveled += movement.length()
        self.timer += dt

        self.spark_particles.append({
            "pos": pygame.Vector2(self.pos) + pygame.Vector2(random.uniform(-3, 3), -random.uniform(3, 7)),
            "vel": pygame.Vector2(random.uniform(-12, 12), -random.uniform(8, 25)),
            "life": random.uniform(0.12, 0.3),
            "max_life": random.uniform(0.12, 0.3),
            "size": random.uniform(1.0, 2.5),
            "color": random.choice([(255, 200, 50), (255, 140, 30), (255, 100, 20)]),
        })
        if random.random() < 0.25:
            self.smoke_particles.append({
                "pos": pygame.Vector2(self.pos) + pygame.Vector2(random.uniform(-2, 2), -2),
                "vel": pygame.Vector2(random.uniform(-4, 4), -random.uniform(5, 12)),
                "life": random.uniform(0.25, 0.5),
                "max_life": random.uniform(0.25, 0.5),
                "size": random.uniform(2.0, 4.0),
            })

        for p in self.spark_particles[:]:
            p["pos"] += p["vel"] * dt
            p["vel"] *= 0.9
            p["life"] -= dt
            if p["life"] <= 0:
                self.spark_particles.remove(p)

        for p in self.smoke_particles[:]:
            p["pos"] += p["vel"] * dt
            p["vel"] *= 0.95
            p["life"] -= dt
            if p["life"] <= 0:
                self.smoke_particles.remove(p)

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

        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        t = self.animation_time

        if not self.exploding:
            body_r = 7

            for p in self.smoke_particles:
                life_r = p["life"] / p["max_life"] if p["max_life"] > 0 else 0
                if life_r <= 0:
                    continue
                alpha = int(60 * life_r)
                size = int(p["size"] * (1.0 + 0.5 * (1 - life_r)))
                sx = int(p["pos"].x - camera_offset.x)
                sy = int(p["pos"].y - camera_offset.y)
                s_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(s_surf, (100, 95, 90, alpha), (size, size), size)
                screen.blit(s_surf, (sx - size, sy - size))

            for p in self.spark_particles:
                life_r = p["life"] / p["max_life"] if p["max_life"] > 0 else 0
                if life_r <= 0:
                    continue
                alpha = int(200 * life_r)
                size = max(1, int(p["size"] * life_r))
                sx = int(p["pos"].x - camera_offset.x)
                sy = int(p["pos"].y - camera_offset.y)
                glow = size * 3
                g_surf = pygame.Surface((glow * 2, glow * 2), pygame.SRCALPHA)
                r, gb, b = p["color"]
                pygame.draw.circle(g_surf, (r, gb, b, alpha // 3), (glow, glow), glow)
                screen.blit(g_surf, (sx - glow, sy - glow))
                pygame.draw.circle(screen, p["color"], (sx, sy), size)

            fuse_y = cy - body_r - 2
            fuse_pulse = (math.sin(t * 25) + 1.0) * 0.5
            glow_size = int(4 + 4 * fuse_pulse)
            fg_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(fg_surf, (255, 120, 20, int(80 + 120 * fuse_pulse)), (glow_size, glow_size), glow_size)
            screen.blit(fg_surf, (cx - glow_size, fuse_y - glow_size))
            pygame.draw.line(screen, (70, 55, 40), (cx, cy - body_r), (cx, fuse_y), 2)

            rot_off = math.cos(t * 4) * body_r * 0.35
            pygame.draw.circle(screen, (55, 38, 22), (cx, cy), body_r)
            pygame.draw.circle(screen, (85, 58, 35), (cx + int(rot_off * 0.5), cy), int(body_r * 0.8))
            hx = cx + int(rot_off)
            pygame.draw.circle(screen, (130, 90, 55), (hx, cy), int(body_r * 0.45))
            pygame.draw.circle(screen, (180, 140, 95), (hx, cy), int(body_r * 0.2))

            band_h = 3
            band_rect = pygame.Rect(cx - body_r, cy - band_h // 2, body_r * 2, band_h)
            pygame.draw.rect(screen, (95, 95, 105), band_rect, border_radius=1)
            pygame.draw.rect(screen, (130, 130, 140), band_rect, 1, border_radius=1)

            for i in range(3):
                rx = cx + int((i - 1) * body_r * 0.55)
                pygame.draw.circle(screen, (70, 70, 80), (rx, cy), 1)
                pygame.draw.circle(screen, (150, 150, 160), (rx - 1, cy - 1), 1)

            flame_y = fuse_y - 2
            flame_r = max(1, int(2 + 1.5 * (0.5 + 0.5 * math.sin(t * 30 + 1))))
            pygame.draw.circle(screen, (255, 220, 80), (cx, flame_y), flame_r)
            pygame.draw.circle(screen, (255, 255, 220), (cx, flame_y), max(1, flame_r - 1))
            return

        progress = min(1.0, self.explosion_timer / self.explosion_duration)
        radius = int(self.blast_radius * progress)
        if radius <= 0:
            return

        smoke_r = radius + 12
        smoke_alpha = int(60 * (1 - progress))
        if smoke_alpha > 0:
            smoke_surf = pygame.Surface((smoke_r * 2, smoke_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(smoke_surf, (90, 85, 80, smoke_alpha), (smoke_r, smoke_r), smoke_r, 5)
            screen.blit(smoke_surf, (cx - smoke_r, cy - smoke_r))

        ring_w = max(1, int(5 * (1 - progress)))
        ring_a = int(200 * (1 - progress))
        pygame.draw.circle(screen, (255, 180, 60, ring_a), (cx, cy), radius, ring_w)

        exp_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(exp_surf, (255, 100, 20, int(160 * (1 - progress * 0.3))), (radius, radius), radius)
        mid_r = max(1, int(radius * 0.65))
        pygame.draw.circle(exp_surf, (255, 190, 50, int(200 * (1 - progress * 0.2))), (radius, radius), mid_r)
        inner_r = max(1, int(radius * 0.35))
        pygame.draw.circle(exp_surf, (255, 240, 140, int(230 * (1 - progress * 0.1))), (radius, radius), inner_r)
        core_r = max(1, int(radius * 0.15))
        pygame.draw.circle(exp_surf, (255, 255, 255, 240), (radius, radius), core_r)
        screen.blit(exp_surf, (cx - radius, cy - radius))

        for sp in self.shrapnel_particles:
            life_r = sp["life"] / sp["max_life"] if sp["max_life"] > 0 else 0
            if life_r <= 0:
                continue
            alpha = int(200 * life_r)
            sx = int(sp["pos"].x - camera_offset.x)
            sy = int(sp["pos"].y - camera_offset.y)
            sz = max(1, int(sp["size"] * life_r))
            sp_surf = pygame.Surface((sz * 2, sz * 2))
            sp_surf.set_colorkey((0, 0, 0))
            points = [(sz, 0), (sz * 2, sz), (sz, sz * 2), (0, sz)]
            pygame.draw.polygon(sp_surf, sp["color"], points)
            sp_surf.set_alpha(alpha)
            screen.blit(sp_surf, (sx - sz, sy - sz))


class Fireball:
    """
    Player fireball projectile that explodes on impact or after a short fuse.

    The explosion damages enemies in an area and can optionally knock them back.

    Attributes:
        pos (pygame.Vector2): Current position in world space.
        direction (pygame.Vector2): Normalized movement direction.
        speed (float): Movement speed in pixels per second.
        max_range (float): Maximum travel distance before self-destruction.
        damage (int): Damage dealt to enemies in the explosion.
        blast_radius (float): Radius of the area-of-effect explosion.
        fuse_time (float): Seconds before the fireball explodes automatically.
        knockback_force (float): Force applied to enemies hit by the explosion.
        explosion_duration (float): Duration of the explosion visual in seconds.
        traveled (float): Distance the fireball has traveled so far.
        timer (float): Elapsed time since creation.
        color (tuple): RGB color of the fireball.
        alive (bool): Whether the projectile is still active.
        exploding (bool): Whether the explosion sequence has started.
        explosion_timer (float): Elapsed time within the explosion phase.
        damage_applied (bool): Whether explosion damage has already been applied.
        animation_time (float): Accumulated time for visual animations.
        trail (list): Position history for the visual trail effect.
        trail_length (int): Maximum number of trail points stored.
        ember_particles (list): Ember particle effects emitted during flight.
        ember_spawn_timer (float): Accumulator controlling ember spawn rate.

    Methods:
        __init__(pos, direction, speed, max_range, damage, blast_radius, fuse_time, knockback_force=0.0, explosion_duration=0.35, color=(255, 120, 40)):
            Initialize the fireball projectile with position, direction, and stats.
        _size():
            Return the visual base dimensions (width, height).
        get_rect():
            Return a collision rectangle centered on the current position.
        _trigger_explosion():
            Begin the explosion sequence.
        _entity_center(entity):
            Return the center position of a given entity.
        update(dt, obstacles, enemies):
            Update movement, trail, ember particles, obstacle collisions, and explosion logic.
        draw(screen, camera_offset=None):
            Render the fireball with trail, ember particles, and explosion effects.
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
        damage_applied (bool): Whether damage and freeze have been applied.
        animation_time (float): Accumulated time for visual animations.
        shards (list): Ice shard particles for the visual effect.
        mist (list): Frost mist particles for the visual effect.

    Methods:
        __init__(pos, radius, freeze_duration, damage=0, expansion_duration=0.5):
            Initialize the frost nova with position, radius, and freeze parameters.
        get_rect():
            Return a rectangle encompassing the full nova radius.
        _spawn_burst_particles():
            Spawn ice shard and mist particles at burst time.
        update(dt, obstacles, enemies):
            Expand the nova, damage and freeze enemies, update particles.
        draw(screen, camera_offset=None):
            Render the frost nova with ice ring, shards, mist, and sparkles.
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
        self.shards = []
        self.mist = []

    def get_rect(self):
        size = int(self.radius * 2)
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def _spawn_burst_particles(self):
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(60, 200)
            self.shards.append({
                "pos": pygame.Vector2(self.pos),
                "vel": pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                "max_life": (ml := random.uniform(0.2, 0.5)),
                "life": ml,
                "size": random.uniform(2.0, 5.0),
                "rotation": random.uniform(0, math.pi * 2),
                "rot_speed": random.uniform(-4, 4),
                "color": random.choice([
                    (200, 240, 255), (160, 210, 255),
                    (220, 250, 255), (180, 220, 255),
                ]),
            })
        for _ in range(12):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(20, 60)
            self.mist.append({
                "pos": pygame.Vector2(self.pos),
                "vel": pygame.Vector2(math.cos(angle), math.sin(angle)) * speed + pygame.Vector2(0, -15),
                "max_life": (ml := random.uniform(0.3, 0.7)),
                "life": ml,
                "size": random.uniform(4.0, 8.0),
            })

    def update(self, dt, obstacles, enemies):
        if not self.alive:
            return

        self.animation_time += dt
        self.expansion_time += dt
        progress = min(1.0, self.expansion_time / self.expansion_duration)
        self.current_radius = self.radius * progress

        if not self.damage_applied and progress >= 0.3:
            self._spawn_burst_particles()
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

        for s in self.shards[:]:
            s["pos"] += s["vel"] * dt
            s["vel"] *= 0.93
            s["rotation"] += s["rot_speed"] * dt
            s["life"] -= dt
            if s["life"] <= 0:
                self.shards.remove(s)

        for m in self.mist[:]:
            m["pos"] += m["vel"] * dt
            m["vel"] *= 0.96
            m["life"] -= dt
            if m["life"] <= 0:
                self.mist.remove(m)

        if self.expansion_time >= self.expansion_duration:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        progress = min(1.0, self.expansion_time / self.expansion_duration)
        radius = int(self.current_radius)
        t = self.animation_time

        if radius <= 0:
            return

        # ── Ground frost pattern ──
        frost_pts = []
        for i in range(12):
            fa = t * 0.3 + i * (math.pi * 2 / 12)
            fd = radius * (0.7 + 0.3 * math.sin(t * 2 + i * 1.5))
            fx = cx + math.cos(fa) * fd
            fy = cy + math.sin(fa) * fd
            frost_pts.append((fx, fy))
        frost_surf = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
        fro = radius + 5
        rel_frost = [(p[0] - cx + fro, p[1] - cy + fro) for p in frost_pts]
        frost_alpha = int(60 * (1 - progress))
        pygame.draw.polygon(frost_surf, (180, 220, 255, frost_alpha), rel_frost)
        pygame.draw.polygon(frost_surf, (200, 235, 255, frost_alpha), rel_frost, 1)
        screen.blit(frost_surf, (cx - fro, cy - fro))

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

        # ── Frost mist ──
        for m in self.mist:
            life_r = min(1.0, m["life"] / m["max_life"]) if m["max_life"] > 0 else 0
            if life_r <= 0:
                continue
            mx = int(m["pos"].x - camera_offset.x)
            my = int(m["pos"].y - camera_offset.y)
            mist_alpha = int(80 * life_r)
            mist_size = max(1, int(m["size"] * (0.5 + 0.5 * life_r)))
            ms = pygame.Surface((mist_size * 2, mist_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(ms, (200, 230, 255, mist_alpha), (mist_size, mist_size), mist_size)
            screen.blit(ms, (mx - mist_size, my - mist_size))

        # ── Ice shards ──
        for s in self.shards:
            life_r = min(1.0, s["life"] / s["max_life"]) if s["max_life"] > 0 else 0
            if life_r <= 0:
                continue
            sx = int(s["pos"].x - camera_offset.x)
            sy = int(s["pos"].y - camera_offset.y)
            shard_alpha = int(220 * life_r)
            shard_size = max(1, int(s["size"] * life_r))
            r, g, b = s["color"]
            rot = s.get("rotation", 0)
            # Diamond shard
            pts = []
            for j in range(4):
                sa = rot + j * (math.pi * 2 / 4)
                sd = shard_size * (1.5 if j % 2 == 0 else 0.7)
                pts.append((sx + math.cos(sa) * sd, sy + math.sin(sa) * sd))
            shard_surf = pygame.Surface((int(shard_size * 3), int(shard_size * 3)), pygame.SRCALPHA)
            soff = shard_size * 1.5
            rel = [(p[0] - sx + soff, p[1] - sy + soff) for p in pts]
            pygame.draw.polygon(shard_surf, (r, g, b, shard_alpha), rel)
            pygame.draw.polygon(shard_surf, (min(255, r + 40), min(255, g + 40), 255, shard_alpha), rel, 1)
            screen.blit(shard_surf, (sx - soff, sy - soff))

        # ── Ice crystal sparkles ──
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

    Attributes:
        pos (pygame.Vector2): Current position in world space.
        direction (pygame.Vector2): Normalized movement direction.
        speed (float): Movement speed in pixels per second.
        max_range (float): Maximum travel distance before destruction.
        damage (int): Damage dealt to enemies on hit.
        freeze_duration (float): How long enemies stay frozen.
        base_width (float): Base width of the cascade fan.
        color (tuple): RGB color of the ice effect.
        alive (bool): Whether the cascade is still active.
        traveled (float): Distance traveled so far.
        animation_time (float): Accumulated time for visual animations.
        hit_cooldowns (dict): Per-enemy ID cooldown timers for repeated hits.
        frost_particles (list): Frost mist particle effects emitted by the wave.
        ground_trail (list): Ground frost trail hexagonal shapes.
        ice_splinters (list): Ice splinter particles flung from the leading edge.

    Methods:
        __init__(pos, direction, speed, max_range, damage, freeze_duration, cascade_width=80.0, color=(80, 180, 255)):
            Initialize the glacial cascade with position, direction, and stats.
        cascade_width (property):
            Current width of the cascade fan based on travel progress.
        _get_wedge_points():
            Return the three corner points (tip, back-left, back-right) of the cascade wedge.
        get_rect():
            Return a bounding rectangle of the cascade wedge.
        update(dt, obstacles, enemies):
            Move the cascade, spawn frost particles, ice splinters, and ground trail, and
            damage/freeze enemies within the wedge area.
        _damage_enemies(enemies):
            Apply damage and freeze effect to enemies within the cascade wedge.
        draw(screen, camera_offset=None):
            Render the cascade with ice shards, frost mist, ground trail, and wedge outline.
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
        self.ice_splinters = []

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
        cw = self.cascade_width
        perp = pygame.Vector2(-self.direction.y, self.direction.x)

        # Ground frost trail - hexagon shapes
        for _ in range(3):
            offset = random.uniform(-cw * 0.35, cw * 0.35)
            tp = self.pos + perp * offset - self.direction * random.uniform(0, 30)
            life = random.uniform(0.3, 0.6)
            self.ground_trail.append({
                "pos": tp, "life": life, "max_life": life,
                "size": random.uniform(3.0, 7.0),
                "rotation": random.uniform(0, math.pi * 2),
            })
        while len(self.ground_trail) > 60:
            self.ground_trail.pop(0)
        for gt in self.ground_trail:
            gt["life"] -= dt
        self.ground_trail = [gt for gt in self.ground_trail if gt["life"] > 0]

        # Frost mist particles
        if random.random() < 0.7:
            off = random.uniform(-cw * 0.45, cw * 0.45)
            pp = self.pos + perp * off + self.direction * random.uniform(-25, 15)
            life = random.uniform(0.4, 0.9)
            self.frost_particles.append({
                "pos": pp, "life": life, "max_life": life,
                "size": random.randint(2, 5),
                "vel": perp * random.uniform(-20, 20) - self.direction * random.uniform(5, 25),
                "rise": random.uniform(-10, -5),
            })
        for p in self.frost_particles[:]:
            p["pos"] += p["vel"] * dt
            p["pos"].y += p["rise"] * dt
            p["life"] -= dt
            if p["life"] <= 0:
                self.frost_particles.remove(p)

        # Ice splinters flung from leading edge
        if random.random() < 0.4:
            spread_frac = random.uniform(-0.8, 0.8)
            off = spread_frac * cw * 0.3
            sp = self.pos + perp * off + self.direction * random.uniform(10, 30)
            life = random.uniform(0.2, 0.5)
            self.ice_splinters.append({
                "pos": sp, "life": life, "max_life": life,
                "vel": (self.direction * random.uniform(50, 150)
                        + perp * random.uniform(-40, 40)),
                "size": random.uniform(1.5, 4.0),
                "rotation": random.uniform(0, math.pi * 2),
                "rot_speed": random.uniform(-4, 4),
            })
        for s in self.ice_splinters[:]:
            s["pos"] += s["vel"] * dt
            s["life"] -= dt
            s["rotation"] += s["rot_speed"] * dt
            if s["life"] <= 0:
                self.ice_splinters.remove(s)

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
        cw = self.cascade_width

        # Ground frost trail - hexagonal crystal shapes
        for gt in self.ground_trail:
            lr = min(1.0, gt["life"] / gt["max_life"]) if gt["max_life"] > 0 else 0
            if lr <= 0:
                continue
            gx = gt["pos"].x - ox
            gy = gt["pos"].y - oy
            sz = gt["size"] * lr
            alpha = int(50 * lr)
            hex_pts = []
            for hv in range(6):
                ha = gt["rotation"] + hv * math.pi / 3
                hex_pts.append((gx + math.cos(ha) * sz, gy + math.sin(ha) * sz))
            if sz > 1:
                hs = pygame.Surface((int(sz * 2.5), int(sz * 2.5)), pygame.SRCALPHA)
                hcx = hcy = int(sz * 1.25)
                hex_local = [(hcx + (px - gx), hcy + (py - gy)) for px, py in hex_pts]
                pygame.draw.polygon(hs, (120, 180, 255, alpha), hex_local, 1)
                screen.blit(hs, (gx - sz * 1.25, gy - sz * 1.25))

        # Frost mist
        for p in self.frost_particles:
            lr = min(1.0, p["life"] / p["max_life"]) if p["max_life"] > 0 else 0
            if lr <= 0:
                continue
            alpha = int(100 * lr)
            sz = int(p["size"] * (0.5 + 0.5 * lr))
            surf = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (180, 220, 255, alpha), (sz, sz), sz)
            screen.blit(surf, (p["pos"].x - sz - ox, p["pos"].y - sz - oy))

        # Ice splinters
        for s in self.ice_splinters:
            lr = min(1.0, s["life"] / s["max_life"]) if s["max_life"] > 0 else 0
            if lr <= 0:
                continue
            sx = s["pos"].x - ox
            sy = s["pos"].y - oy
            sz = s["size"] * (0.3 + 0.7 * lr)
            alpha = int(200 * lr)
            pts = [
                (sx, sy - sz),
                (sx + sz * 0.4, sy - sz * 0.1),
                (sx + sz * 0.1, sy + sz * 0.3),
                (sx - sz * 0.3, sy + sz * 0.2),
            ]
            ca = math.cos(s["rotation"])
            sa = math.sin(s["rotation"])
            cx_ = sx
            cy_ = sy
            rpts = []
            for rpx, rpy in pts:
                dx = rpx - cx_
                dy = rpy - cy_
                rpts.append((cx_ + dx * ca - dy * sa, cy_ + dx * sa + dy * ca))
            pygame.draw.polygon(screen, (180, 220, 255, alpha), rpts)

        # Cascade wedge
        tip, bl, br = self._get_wedge_points()
        tip_s = (tip.x - ox, tip.y - oy)
        bl_s = (bl.x - ox, bl.y - oy)
        br_s = (br.x - ox, br.y - oy)
        pulse = (math.sin(t * 10) + 1.0) * 0.5
        wedge_pts = [tip_s, bl_s, br_s]

        # Layered wedge: outer (dark blue), mid (ice blue), inner (white)
        wedge_surf = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        # Outer layer
        pygame.draw.polygon(wedge_surf, (40, 100, 180, int(35 + 20 * pulse)), wedge_pts)
        # Mid layer (inset)
        mid_pts = [
            (tip_s[0] * 0.5 + bl_s[0] * 0.5, tip_s[1] * 0.5 + bl_s[1] * 0.5),
            (tip_s[0] * 0.5 + br_s[0] * 0.5, tip_s[1] * 0.5 + br_s[1] * 0.5),
        ]
        mid_bl = (bl_s[0] * 0.7 + tip_s[0] * 0.3, bl_s[1] * 0.7 + tip_s[1] * 0.3)
        mid_br = (br_s[0] * 0.7 + tip_s[0] * 0.3, br_s[1] * 0.7 + tip_s[1] * 0.3)
        pygame.draw.polygon(wedge_surf, (120, 200, 255, int(50 + 30 * pulse)),
                            [tip_s, mid_bl, mid_br])
        # Outline
        pygame.draw.polygon(wedge_surf, (180, 230, 255, int(120 + 60 * pulse)), wedge_pts, 2)
        screen.blit(wedge_surf, (0, 0))

        # Jagged ice edge lines along sides
        for side, sign in [(bl_s, 1), (br_s, -1)]:
            for j in range(6):
                jfrac = j / 5.0
                jx = tip_s[0] + (side[0] - tip_s[0]) * jfrac
                jy = tip_s[1] + (side[1] - tip_s[1]) * jfrac
                jitter = 4 + 6 * math.sin(t * 15 + j * 3.0 + sign * 2.0)
                jnx = jx + perp.x * jitter * sign
                jny = jy + perp.y * jitter * sign
                alpha_j = int(100 + 80 * math.sin(t * 12 + j * 1.5))
                pygame.draw.line(screen, (160, 220, 255, alpha_j),
                                 (jx, jy), (jnx, jny), max(1, int(2 + math.sin(t * 8 + j * 2) * 1)))

        # Multiple ice shards within the cascade - diamonds + hexagons mixed
        num_shards = 11
        for i in range(num_shards):
            frac = i / (num_shards - 1) if num_shards > 1 else 0.5
            spread = (frac - 0.5) * cw * 0.8
            depth = 20 - frac * 28
            spos = self.pos + perp * spread - self.direction * depth
            ssx, ssy = spos.x - ox, spos.y - oy
            spulse = (math.sin(t * 12 + i * 2.2) + 1.0) * 0.5
            sz = 3 + 5 * (1 - abs(frac - 0.5) * 2)

            if i % 3 == 0:
                # Hexagonal crystal
                hex_pts = []
                for hv in range(6):
                    ha = t * 2 + i * 1.2 + hv * math.pi / 3
                    hex_pts.append(
                        (ssx + math.cos(ha) * sz, ssy + math.sin(ha) * sz))
                pygame.draw.polygon(screen, (120, 195, 255, 180), hex_pts)
                pygame.draw.polygon(screen, (180, 230, 255, 220), hex_pts, 1)
            else:
                # Diamond shard
                ds = sz * (0.5 + 0.3 * spulse)
                pts = [
                    (ssx, ssy - ds * 1.2),
                    (ssx + ds * 0.6, ssy),
                    (ssx, ssy + ds * 0.8),
                    (ssx - ds * 0.6, ssy),
                ]
                pygame.draw.polygon(screen, (150, 210, 255), pts)
                pygame.draw.polygon(screen, (200, 235, 255), pts, 1)

        # Central bright core with inner glow
        cx = (tip_s[0] + bl_s[0] + br_s[0]) // 3
        cy = (tip_s[1] + bl_s[1] + br_s[1]) // 3
        cr = int(6 + 4 * pulse)
        cg = pygame.Surface((cr * 4, cr * 4), pygame.SRCALPHA)
        cgc = cg.get_width() // 2
        pygame.draw.circle(cg, (200, 240, 255, int(60 + 40 * pulse)),
                           (cgc, cgc), cr * 2)
        pygame.draw.circle(cg, (230, 250, 255, int(120 + 80 * pulse)),
                           (cgc, cgc), cr)
        pygame.draw.circle(cg, (255, 255, 255, int(200 + 55 * pulse)),
                           (cgc, cgc), cr // 2)
        screen.blit(cg, (cx - cgc, cy - cgc))

        # Sparkling ice burst at tip
        for i in range(6):
            angle = t * 3.0 + i * math.pi / 3
            dist = 12 + 8 * math.sin(t * 4 + i * 1.7)
            spx = cx + int(dist * math.cos(angle))
            spy = cy + int(dist * math.sin(angle))
            sps = max(1, int(2.5 + math.sin(t * 6 + i * 2.5) * 1.5))
            bright = int(200 + 55 * math.sin(t * 5 + i * 1.3))
            pygame.draw.circle(screen, (bright, bright, 255), (spx, spy), sps)


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
        color (tuple): RGB color of the lightning.
        alive (bool): Whether the projectile is active.
        traveled (float): Distance traveled.
        animation_time (float): Visual animation timer.
        trail (list): Visual trail points.
        trail_length (int): Maximum number of trail points.
        hit_enemies (list): Enemies already hit (prevents re-hits).
        chaining (bool): Whether currently chaining between targets.
        chain_targets (list): Remaining targets to chain to.
        chain_timer (float): Elapsed time during chain phase.
        chain_delay (float): Delay between chain jumps.
        chain_index (int): Current chain jump index.
        arc_points (list): Lightning arc visual points for the current chain.
        sparks (list): Spark particle effects.
        chain_flash (float): Flash intensity during chain jumps.

    Methods:
        __init__(pos, direction, speed, max_range, damage, chain_range, max_targets=5, color=(255, 220, 50)):
            Initialize the chain lightning projectile.
        _size():
            Return the visual base dimensions (width, height).
        get_rect():
            Return a collision rectangle centered on the current position.
        _find_chain_target(from_pos, enemies):
            Find the nearest unhit enemy within chain range.
        _spawn_spark_burst(pos, count=12):
            Spawn spark particles at the given position.
        update(dt, obstacles, enemies):
            Fly forward, then chain between targets, damaging each enemy.
        _draw_lightning_arc(screen, start, end, time_offset, camera_offset):
            Draw a jagged lightning arc between two positions.
        draw(screen, camera_offset=None):
            Render the lightning bolt with trails, arcs, and sparks.
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

        self.arc_points = []
        self.sparks = []
        self.chain_flash = 0.0

    def _size(self):
        return 12, 12

    def get_rect(self):
        width, height = self._size()
        rect = pygame.Rect(0, 0, width, height)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def _find_chain_target(self, from_pos, enemies):
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

    def _spawn_spark_burst(self, pos, count=12):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(40, 160)
            self.sparks.append({
                "pos": pygame.Vector2(pos),
                "vel": pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                "max_life": (ml := random.uniform(0.15, 0.4)),
                "life": ml,
                "size": random.uniform(1, 3),
                "color": random.choice([
                    (255, 255, 200), (255, 220, 50),
                    (200, 180, 255), (255, 200, 100),
                ]),
            })

    def update(self, dt, obstacles, enemies):
        if not self.alive:
            return

        self.animation_time += dt
        self.chain_flash = max(0, self.chain_flash - 4 * dt)

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
                self._spawn_spark_burst(e_center, 15)
                self.chain_flash = 1.0
                enemy.take_damage(self.damage)
                logger.info(f"Chain Lightning chained to {enemy.__class__.__name__} for {self.damage} damage!")
                self.pos = e_center
                self.hit_enemies.append(enemy)

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

        # Spawn sparks while flying
        if random.random() < 0.5:
            perp = pygame.Vector2(-self.direction.y, self.direction.x)
            offset = perp * random.uniform(-8, 8)
            self.sparks.append({
                "pos": pygame.Vector2(self.pos) + offset,
                "vel": perp * random.uniform(-30, 30) + self.direction * random.uniform(-10, 0),
                "max_life": (ml := random.uniform(0.1, 0.3)),
                "life": ml,
                "size": random.uniform(1, 2.5),
                "color": (255, 255, 200),
            })

        for s in self.sparks[:]:
            s["pos"] += s["vel"] * dt
            s["vel"] *= 0.9
            s["life"] -= dt
            if s["life"] <= 0:
                self.sparks.remove(s)

        rect = self.get_rect()
        for wall in obstacles:
            if rect.colliderect(wall):
                self.alive = False
                return

        for enemy in enemies:
            if enemy.is_dead():
                continue
            if rect.colliderect(enemy.get_rect()):
                if enemy not in self.hit_enemies:
                    enemy.take_damage(self.damage)
                    logger.info(f"Chain Lightning hit {enemy.__class__.__name__} for {self.damage} damage!")
                    self.hit_enemies.append(enemy)
                    e_center = pygame.Vector2(enemy.get_rect().center)
                    self.arc_points.append((pygame.Vector2(self.pos), e_center, self.animation_time))
                    self._spawn_spark_burst(e_center, 15)
                    self.chain_flash = 1.0
                    self.pos = e_center

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

        # Glow
        min_x = min(sx, ex)
        min_y = min(sy, ey)
        max_x = max(sx, ex)
        max_y = max(sy, ey)
        pad = 20
        gw = int(max_x - min_x + pad * 2)
        gh = int(max_y - min_y + pad * 2)
        if gw <= 0 or gh <= 0:
            return
        glow_surf = pygame.Surface((gw, gh), pygame.SRCALPHA)
        rel_pts = [(p[0] - min_x + pad, p[1] - min_y + pad) for p in points]
        for thickness in (8, 5, 3):
            alpha = 25 if thickness > 5 else 60
            pygame.draw.lines(glow_surf, (255, 220, 50, alpha), False, rel_pts, thickness)
        screen.blit(glow_surf, (min_x - pad, min_y - pad))

        # Main arc
        pygame.draw.lines(screen, (255, 255, 200), False, points, 2)
        pygame.draw.lines(screen, self.color, False, points, 1)

        # Branch arc (small offshoot)
        if dist > 60:
            branch_idx = random.randint(1, max(2, segments - 2))
            bp = points[branch_idx]
            b_angle = math.atan2(dy, dx) + random.uniform(-1.0, 1.0)
            b_len = dist * 0.15
            bex = bp[0] + math.cos(b_angle) * b_len
            bey = bp[1] + math.sin(b_angle) * b_len
            branch_pts = [bp, (bex, bey)]
            rel_branch = [(p[0] - min_x + pad, p[1] - min_y + pad) for p in branch_pts]
            pygame.draw.lines(glow_surf, (255, 220, 80, 40), False, rel_branch, 2)
            screen.blit(glow_surf, (min_x - pad, min_y - pad))
            pygame.draw.lines(screen, (255, 255, 200), False, branch_pts, 1)

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        t = self.animation_time

        # Draw chain arcs
        for arc_start, arc_end, t_offset in self.arc_points:
            self._draw_lightning_arc(screen, arc_start, arc_end, t_offset, camera_offset)

        # Draw sparks
        for s in self.sparks:
            life_r = min(1.0, s["life"] / s["max_life"]) if s["max_life"] > 0 else 0
            if life_r <= 0:
                continue
            sx = int(s["pos"].x - camera_offset.x)
            sy = int(s["pos"].y - camera_offset.y)
            alpha = int(200 * life_r)
            size = max(1, int(s["size"] * life_r))
            r, g, b = s["color"]
            sg = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
            pygame.draw.circle(sg, (r, g, b, alpha // 2), (size * 1.5, size * 1.5), size * 1.5)
            screen.blit(sg, (sx - size * 1.5, sy - size * 1.5))
            pygame.draw.circle(screen, (r, g, b, alpha), (sx, sy), size)

        # Draw trail
        for i, pos in enumerate(self.trail):
            alpha = int(100 * (i / len(self.trail)))
            # Jagged electrical trail instead of smooth circles
            trail_r = int(2 + 3 * (i / len(self.trail)))
            jx = random.uniform(-2, 2)
            jy = random.uniform(-2, 2)
            t_surf = pygame.Surface((trail_r * 2 + 4, trail_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(t_surf, (255, 220, 50, alpha), (trail_r + 2, trail_r + 2), trail_r)
            screen.blit(t_surf, (pos.x - trail_r - 2 + jx - camera_offset.x,
                                 pos.y - trail_r - 2 + jy - camera_offset.y))

        # Chain flash overlay
        if self.chain_flash > 0:
            flash_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            flash_a = int(40 * self.chain_flash)
            pygame.draw.circle(flash_surf, (255, 255, 200, flash_a),
                               (int(self.pos.x - camera_offset.x), int(self.pos.y - camera_offset.y)),
                               int(30 * self.chain_flash))
            screen.blit(flash_surf, (0, 0))

        # Draw bolt head
        if not self.chaining:
            cx = int(self.pos.x - camera_offset.x)
            cy = int(self.pos.y - camera_offset.y)
            pulse = 0.5 + 0.5 * math.sin(t * 20)

            # Outer glow
            glow_size = int(14 + 4 * pulse)
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 220, 50, int(50 + 30 * pulse)),
                               (glow_size, glow_size), glow_size)
            screen.blit(glow_surf, (cx - glow_size, cy - glow_size))

            # Directional bolt head (arrow-like shape)
            d = self.direction
            perp = pygame.Vector2(-d.y, d.x)
            size = 6 + 2 * pulse
            tip = (cx + d.x * size * 1.5, cy + d.y * size * 1.5)
            left = (cx + perp.x * size * 0.8 - d.x * size * 0.5,
                    cy + perp.y * size * 0.8 - d.y * size * 0.5)
            right = (cx - perp.x * size * 0.8 - d.x * size * 0.5,
                     cy - perp.y * size * 0.8 - d.y * size * 0.5)
            bolt_pts = [tip, left, right]
            pygame.draw.polygon(screen, (255, 255, 220), bolt_pts)
            pygame.draw.polygon(screen, self.color, bolt_pts, 1)
            # Core dot
            pygame.draw.circle(screen, (255, 255, 255), (cx, cy), max(1, int(size * 0.3)))


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
        flash_alpha (int): Current flash overlay alpha for the strike.
        particles (list): Impact particle effects.

    Methods:
        __init__(pos, damage, radius=100.0, delay=0.5):
            Initialize the thunderstrike at the target position.
        get_rect():
            Return a rectangle covering the strike radius.
        update(dt, obstacles, enemies):
            Wait for delay, then damage enemies and spawn visuals.
        _spawn_impact_particles():
            Spawn spark particles at the strike center.
        _draw_bolt(screen, cx, cy, alpha, camera_offset):
            Draw a branched lightning bolt from above to the strike center.
        draw(screen, camera_offset=None):
            Render the telegraph circle, lightning bolt, impact particles, and flash.
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
        self.particles = []

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
            for enemy in enemies:
                if enemy.is_dead():
                    continue
                e_center = pygame.Vector2(enemy.get_rect().center)
                if (e_center - self.pos).length_squared() <= self.radius * self.radius:
                    enemy.take_damage(self.damage)
                    logger.info(f"Thunderstrike hit {enemy.__class__.__name__} for {self.damage} damage!")
            self.struck = True
            self.flash_alpha = 255
            # Spawn impact particles
            self._spawn_impact_particles()

        if self.struck:
            self.flash_alpha = max(0, self.flash_alpha - 600 * dt)

        for p in self.particles[:]:
            p["pos"] += p["vel"] * dt
            p["vel"] *= 0.92
            p["life"] -= dt
            if p["life"] <= 0:
                self.particles.remove(p)

        if self.timer >= self.delay + 0.8:
            self.alive = False

    def _spawn_impact_particles(self):
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(50, 200)
            self.particles.append({
                "pos": pygame.Vector2(self.pos),
                "vel": pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                "max_life": (ml := random.uniform(0.2, 0.5)),
                "life": ml,
                "size": random.uniform(2, 5),
                "color": random.choice([
                    (255, 255, 200), (255, 220, 50),
                    (200, 180, 255), (255, 200, 100),
                ]),
            })

    def _draw_bolt(self, screen, cx, cy, alpha, camera_offset):
        """Draw a branched lightning bolt from above to center point."""
        bolt_top_y = cy - 400
        segments = 14

        # Main bolt
        bolt_points = [(cx, bolt_top_y)]
        for i in range(1, segments):
            t = i / segments
            bx = cx + 12 * math.sin(t * math.pi * 5 + self.animation_time * 25)
            by = bolt_top_y + (cy - bolt_top_y) * t
            bolt_points.append((bx, by))
        bolt_points.append((cx, cy))

        # Branches
        all_points = [bolt_points]
        for _ in range(3):
            src_idx = random.randint(2, segments - 3)
            sp = bolt_points[src_idx]
            b_angle = math.atan2(cy - bolt_top_y, 0) + random.uniform(-1.5, 1.5)
            b_len = random.uniform(30, 80)
            branch = [(sp[0], sp[1])]
            for j in range(1, 4):
                frac = j / 4
                bx2 = sp[0] + math.cos(b_angle) * b_len * frac
                by2 = sp[1] + math.sin(b_angle) * b_len * frac
                branch.append((bx2 + random.uniform(-3, 3), by2 + random.uniform(-3, 3)))
            all_points.append(branch)

        # Compute bounds
        all_coords = [p for pts in all_points for p in pts]
        min_x = min(p[0] for p in all_coords)
        max_x = max(p[0] for p in all_coords)
        min_y = min(p[1] for p in all_coords)
        max_y = max(p[1] for p in all_coords)
        pad = 25
        gw = int(max_x - min_x + pad * 2)
        gh = int(max_y - min_y + pad * 2)
        if gw <= 0 or gh <= 0:
            return

        glow_surf = pygame.Surface((gw, gh), pygame.SRCALPHA)

        for points in all_points:
            rel = [(p[0] - min_x + pad, p[1] - min_y + pad) for p in points]
            for thickness in (8, 5, 3):
                glow_a = int(20 * alpha / 255) if thickness > 5 else int(50 * alpha / 255)
                pygame.draw.lines(glow_surf, (255, 220, 50, glow_a), False, rel, thickness)

        screen.blit(glow_surf, (min_x - pad, min_y - pad))

        # Main bolt lines
        for idx, points in enumerate(all_points):
            bolt_a = int(alpha * (1.0 if idx == 0 else 0.6))
            pygame.draw.lines(screen, (255, 255, 255, bolt_a), False, points, 2)
            pygame.draw.lines(screen, (255, 220, 80, bolt_a), False, points, 1)

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        t = self.animation_time

        if not self.struck:
            progress = self.timer / self.delay
            pulse = 0.5 + 0.5 * math.sin(t * 10)

            # Ground target circle (outer ring)
            circle_alpha = int(80 + 80 * pulse)
            circle_surf = pygame.Surface((int(self.radius * 2), int(self.radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, (255, 220, 50, circle_alpha),
                               (int(self.radius), int(self.radius)), int(self.radius), 2)
            pygame.draw.circle(circle_surf, (200, 180, 255, int(circle_alpha * 0.5)),
                               (int(self.radius), int(self.radius)), int(self.radius * 0.6), 1)
            screen.blit(circle_surf, (cx - int(self.radius), cy - int(self.radius)))

            # Crackling ground sparks (telegraph)
            for _ in range(3):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(0, self.radius * 0.8)
                ssx = cx + math.cos(angle) * dist
                ssy = cy + math.sin(angle) * dist
                sex = ssx + random.uniform(-15, 15)
                sey = ssy + random.uniform(-15, 15)
                spark_alpha = int(60 + 60 * pulse)
                pygame.draw.line(screen, (255, 255, 200, spark_alpha), (ssx, ssy), (sex, sey), 1)

            # Descending light particles
            for _ in range(5):
                px = cx + random.uniform(-self.radius * 0.8, self.radius * 0.8)
                py = cy - 200 + progress * 200 + random.uniform(-20, 20)
                p_size = random.randint(2, 4)
                p_alpha = max(0, int(120 * (1 - abs(py - cy) / 200)))
                p_surf = pygame.Surface((p_size * 2, p_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, (255, 255, 200, p_alpha), (p_size, p_size), p_size)
                screen.blit(p_surf, (int(px) - p_size, int(py) - p_size))

            # Rising dust/energy from ground
            for _ in range(2):
                rx = cx + random.uniform(-self.radius * 0.6, self.radius * 0.6)
                ry = cy + random.uniform(-5, 5) - progress * 30
                r_size = random.randint(1, 3)
                r_alpha = int(60 * (1 - progress) * (1 - abs(rx - cx) / self.radius))
                r_surf = pygame.Surface((r_size * 2, r_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(r_surf, (200, 180, 255, r_alpha), (r_size, r_size), r_size)
                screen.blit(r_surf, (int(rx) - r_size, int(ry) - r_size))
        else:
            bolt_alpha = min(255, self.flash_alpha * 2)

            # Draw branched lightning bolt
            self._draw_bolt(screen, cx, cy, bolt_alpha, camera_offset)

            # Expanding electrical field on ground
            field_progress = min(1.0, (self.timer - self.delay) / 0.5)
            field_radius = int(self.radius * (0.2 + 0.8 * field_progress))

            # Multiple expanding rings
            for ring_i in range(3):
                ring_r = int(field_radius * (0.3 + 0.7 * ((ring_i + 1) / 3)))
                ring_alpha = int(100 * (1 - field_progress) / (ring_i + 1))
                ring_color = (100, 80, 200) if ring_i > 0 else (255, 220, 50)
                pygame.draw.circle(screen, (*ring_color, ring_alpha), (cx, cy), ring_r,
                                   max(1, int(2 - field_progress)))

            # Main field surface
            field_surf = pygame.Surface((field_radius * 2, field_radius * 2), pygame.SRCALPHA)
            fc = field_radius
            inner_alpha = int(80 * (1 - field_progress * 0.5))
            pygame.draw.circle(field_surf, (200, 180, 255, inner_alpha), (fc, fc), int(field_radius * 0.7))
            core_alpha = min(200, int(self.flash_alpha * 0.8))
            pygame.draw.circle(field_surf, (255, 255, 255, core_alpha), (fc, fc), int(field_radius * 0.15))
            screen.blit(field_surf, (cx - field_radius, cy - field_radius))

            # Arc sparks on ground
            for _ in range(int(10 * (1 - field_progress) + 2)):
                s_angle = random.uniform(0, math.pi * 2)
                s_dist = random.uniform(0, field_radius)
                ssx = cx + math.cos(s_angle) * s_dist
                ssy = cy + math.sin(s_angle) * s_dist
                sex = ssx + random.uniform(-12, 12)
                sey = ssy + random.uniform(-12, 12)
                spark_alpha = int(200 * (1 - field_progress))
                pygame.draw.line(screen, (255, 255, 200, spark_alpha), (ssx, ssy), (sex, sey), 1)

            # Flying debris particles
            for p in self.particles:
                life_r = min(1.0, p["life"] / p["max_life"]) if p["max_life"] > 0 else 0
                if life_r <= 0:
                    continue
                px = int(p["pos"].x - camera_offset.x)
                py = int(p["pos"].y - camera_offset.y)
                p_alpha = int(200 * life_r)
                p_size = max(1, int(p["size"] * life_r))
                r, g, b = p["color"]
                p_surf = pygame.Surface((p_size * 2, p_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, (r, g, b, p_alpha), (p_size, p_size), p_size)
                screen.blit(p_surf, (px - p_size, py - p_size))

            # Screen flash (brief white overlay)
            if self.flash_alpha > 50:
                flash_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                flash_a = int(self.flash_alpha * 0.3)
                flash_surf.fill((255, 255, 255, flash_a))
                screen.blit(flash_surf, (0, 0))


class EntanglingRoots:
    """
    Missile that flies forward and bursts into roots that immobilize enemies.

    Two phases:
      1. Flying phase — a seed/sprout projectile travels in a direction.
      2. Burst phase — on impact or max range, roots explode outward.

    Attributes:
        pos (pygame.Vector2): Current position in world space.
        direction (pygame.Vector2): Normalized movement direction.
        speed (float): Travel speed in pixels per second.
        max_range (float): Maximum travel distance before bursting.
        radius (float): Burst radius for root immobilization.
        root_duration (float): How long enemies stay rooted.
        damage (int): Damage dealt to enemies on burst.
        alive (bool): Whether the projectile is still active.
        traveled (float): Distance traveled so far.
        timer (float): Elapsed time (phase-dependent).
        expansion_duration (float): Duration of the burst expansion animation.
        damage_applied (bool): Whether burst damage has been applied.
        animation_time (float): Accumulated time for visual animations.
        vine_points (list): Root vine visual control points.
        bursting (bool): Whether the burst phase is active.
        trail (list): Position history for the visual trail.
        trail_length (int): Maximum number of trail points stored.
        root_particles (list): Root branch particle data.
        leaf_particles (list): Leaf particle effects burst from the seed.

    Methods:
        __init__(pos, direction, speed, max_range, radius, root_duration, damage=0, expansion_duration=0.5):
            Initialize the entangling roots projectile.
        get_rect():
            Return a bounding rectangle depending on the current phase.
        _trigger_burst():
            Enter the burst phase and spawn initial leaf particles.
        update(dt, obstacles, enemies):
            Fly toward the target, then burst to root and damage enemies.
        draw(screen, camera_offset=None):
            Render the seed, trail, root branches, aura, leaf particles, and vine tendrils.
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

    Attributes:
        pos (pygame.Vector2): Current position in world space.
        direction (pygame.Vector2): Normalized movement direction.
        speed (float): Travel speed in pixels per second.
        max_range (float): Maximum travel distance before despawning.
        damage (int): Damage dealt to enemies on hit.
        color (tuple): RGB color of the nature bolt.
        alive (bool): Whether the projectile is still active.
        traveled (float): Distance traveled so far.
        animation_time (float): Accumulated time for visual animations.
        trail (list): Position history for the visual trail.
        trail_length (int): Maximum number of trail points stored.
        target_pos (pygame.Vector2 or None): Optional target position for homing.
        leaf_particles (list): Leaf particle effects emitted during flight.

    Methods:
        __init__(pos, direction, speed, max_range, damage, target_pos=None, color=(80, 220, 80)):
            Initialize the nature bolt projectile.
        _size():
            Return the visual base dimensions (width, height).
        get_rect():
            Return a collision rectangle centered on the current position.
        update(dt, obstacles, enemies):
            Move the bolt, update leaf particles, check collisions and range.
        draw(screen, camera_offset=None):
            Render the bolt with leaf particles, trail, glow, and vine tendrils.
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

    Attributes:
        pos (pygame.Vector2): Current position in world space.
        direction (pygame.Vector2): Normalized movement direction.
        speed (float): Travel speed in pixels per second.
        max_range (float): Maximum travel distance before despawning.
        damage (int): Damage dealt to enemies on hit.
        homing_strength (float): Turn rate toward the target (0-1).
        alive (bool): Whether the projectile is still active.
        traveled (float): Distance traveled so far.
        animation_time (float): Accumulated time for visual animations.
        target (Enemy or None): Currently tracked enemy.
        trail (list): Position history for the visual trail.
        trail_length (int): Maximum number of trail points stored.
        arcane_sparks (list): Sparkle particle effects.
        orbit_angle (float): Current angle for orbiting sigil visuals.
        hit_effect (pygame.Surface or None): Cached hit visual effect surface.

    Methods:
        __init__(pos, direction, speed, max_range, damage, homing_strength=0.15):
            Initialize the homing arcane missile.
        _size():
            Return the visual base dimensions (width, height).
        get_rect():
            Return a collision rectangle centered on the current position.
        _acquire_target(enemies):
            Find and set the nearest enemy as the homing target.
        _spawn_hit_effect():
            Spawn a bright hit visual at the current position.
        update(dt, obstacles, enemies):
            Home toward the target, move, update sparks, and check collisions.
        draw(screen, camera_offset=None):
            Render the missile with trail, sigils, arcane sparks, and crystals.
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
        damage_applied (bool): Whether damage has already been applied.
        animation_time (float): Accumulated time for visual animations.
        smoke_particles (list): Rising shadow smoke particle effects.

    Methods:
        __init__(pos, damage, radius=150.0, expansion_duration=0.5):
            Initialize the dark pact shadow burst.
        get_rect():
            Return a rectangle covering the burst radius.
        update(dt, obstacles, enemies):
            Expand the burst, damage enemies, and spawn smoke particles.
        draw(screen, camera_offset=None):
            Render the dark burst with smoke rings, particles, and tendrils.
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

    Attributes:
        pos (pygame.Vector2): Center position of the afterimage.
        damage (int): Damage dealt to enemies in range.
        radius (float): Effect radius for damage.
        alive (bool): Whether the effect is still active.
        life (float): Current elapsed lifetime.
        max_life (float): Maximum lifetime before despawn.
        damage_applied (bool): Whether damage has already been applied.
        angle (float): Current rotation angle for visual sigil.
        rot_speed (float): Rotation speed for the sigil.

    Methods:
        __init__(pos, damage=18, radius=70.0, duration=0.7):
            Initialize the afterimage at the given position.
        get_rect():
            Return a rectangle covering the effect area.
        update(dt, obstacles, enemies):
            Apply damage after a short delay and fade out.
        draw(screen, camera_offset=None):
            Render the player silhouette, ghostly ring, glow, sigil, and sparkles.
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

    Attributes:
        pos (pygame.Vector2): Center position of the burst.
        damage (int): Damage dealt to enemies in range.
        radius (float): Maximum expansion radius.
        alive (bool): Whether the effect is still active.
        life (float): Current elapsed lifetime.
        max_life (float): Maximum lifetime before despawn.
        damage_applied (bool): Whether damage has already been applied.

    Methods:
        __init__(pos, damage, radius=180.0, duration=0.8):
            Initialize the elemental burst.
        get_rect():
            Return a rectangle covering the burst radius.
        update(dt, obstacles, enemies):
            Apply damage after a short delay and animate the vortex.
        draw(screen, camera_offset=None):
            Render the vortex glow, spiral arms, particles, core, and energy wisps.
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


class IceShard:
    """
    Ice projectile fired by cryomancer enemies. Applies slow on hit.

    Attributes:
        pos (pygame.Vector2): Current position.
        direction (pygame.Vector2): Normalized travel direction.
        speed (float): Travel speed in pixels per second.
        max_range (float): Maximum travel distance.
        damage (int): Damage on hit.
        slow_duration (float): Duration of the slow effect.
        slow_factor (float): Speed multiplier of the slow.
        traveled (float): Distance traveled so far.
        alive (bool): Whether the projectile is active.
        animation_time (float): Visual animation timer.
        trail (list): Position history for visual trail.
    """
    def __init__(self, pos, direction, speed, max_range, damage, slow_duration, slow_factor):
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()
        self.speed = speed
        self.max_range = max_range
        self.damage = damage
        self.slow_duration = slow_duration
        self.slow_factor = slow_factor
        self.traveled = 0.0
        self.alive = True
        self.animation_time = 0.0
        self.trail = []
        self.trail_length = 10

    def _size(self):
        return 12, 8

    def get_rect(self):
        w, h = self._size()
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, player):
        if not self.alive:
            return
        self.animation_time += dt
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
        if player and rect.colliderect(player.get_rect()):
            if self.damage > 0:
                player.take_damage(self.damage)
            if self.slow_duration > 0:
                player.add_effect(SlowEffect(self.slow_duration, self.slow_factor))
            self.alive = False
            return
        if self.traveled >= self.max_range:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)
        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        t = self.animation_time
        pulse = 0.7 + 0.3 * math.sin(t * 15)
        for i, pos in enumerate(self.trail):
            ratio = i / len(self.trail) if self.trail else 0
            alpha = int(60 * ratio)
            r = int(2 + 3 * ratio)
            ts = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(ts, (150, 210, 255, alpha), (r, r), r)
            screen.blit(ts, (pos.x - r - camera_offset.x, pos.y - r - camera_offset.y))
        glow_sz = int(10 + 4 * pulse)
        gs = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (180, 220, 255, int(40 + 25 * pulse)), (glow_sz, glow_sz), glow_sz)
        screen.blit(gs, (cx - glow_sz, cy - glow_sz))
        d = self.direction
        perp = pygame.Vector2(-d.y, d.x)
        tip = (cx + d.x * 8, cy + d.y * 8)
        left = (cx + perp.x * 4 - d.x * 4, cy + perp.y * 4 - d.y * 4)
        right = (cx - perp.x * 4 - d.x * 4, cy - perp.y * 4 - d.y * 4)
        back = (cx - d.x * 6, cy - d.y * 6)
        pts = [tip, left, back, right]
        pygame.draw.polygon(screen, (200, 235, 255), pts)
        pygame.draw.polygon(screen, (150, 200, 255), pts, 1)
        pygame.draw.circle(screen, (240, 250, 255), (cx, cy), 3)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 1)


class ShadowBolt:
    """
    Shadow projectile fired by shadowmancer enemies. Applies confusion on hit.

    Attributes:
        pos (pygame.Vector2): Current position.
        direction (pygame.Vector2): Normalized travel direction.
        speed (float): Travel speed in pixels per second.
        max_range (float): Maximum travel distance.
        damage (int): Damage on hit.
        confuse_duration (float): Duration of the confusion effect.
        traveled (float): Distance traveled so far.
        alive (bool): Whether the projectile is active.
        animation_time (float): Visual animation timer.
        trail (list): Position history for visual trail.
    """
    def __init__(self, pos, direction, speed, max_range, damage, confuse_duration):
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()
        self.speed = speed
        self.max_range = max_range
        self.damage = damage
        self.confuse_duration = confuse_duration
        self.traveled = 0.0
        self.alive = True
        self.animation_time = 0.0
        self.trail = []
        self.trail_length = 12

    def _size(self):
        return 14, 8

    def get_rect(self):
        w, h = self._size()
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, player):
        if not self.alive:
            return
        self.animation_time += dt
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
        if player and rect.colliderect(player.get_rect()):
            if self.damage > 0:
                player.take_damage(self.damage)
            if self.confuse_duration > 0:
                player.add_effect(ConfusionEffect(self.confuse_duration))
            self.alive = False
            return
        if self.traveled >= self.max_range:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)
        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        t = self.animation_time
        pulse = 0.6 + 0.4 * math.sin(t * 14)
        for i, pos in enumerate(self.trail):
            ratio = i / len(self.trail) if self.trail else 0
            alpha = int(70 * ratio)
            r = int(2 + 3 * ratio)
            ts = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            wobble = math.sin(t * 10 + i * 0.8) * 2
            pygame.draw.circle(ts, (100, 40, 160, alpha), (r + int(wobble), r), r)
            screen.blit(ts, (pos.x - r - camera_offset.x + wobble, pos.y - r - camera_offset.y))
        glow_sz = int(12 + 5 * pulse)
        gs = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (120, 40, 180, int(40 + 30 * pulse)), (glow_sz, glow_sz), glow_sz)
        screen.blit(gs, (cx - glow_sz, cy - glow_sz))
        ring_r = int(7 + 3 * pulse)
        ring_a = int(50 + 30 * pulse)
        pygame.draw.circle(screen, (140, 60, 200, ring_a), (cx, cy), ring_r, 2)
        body_r = 6
        pygame.draw.circle(screen, (80, 30, 140), (cx, cy), body_r)
        pygame.draw.circle(screen, (140, 60, 200), (cx, cy), body_r - 2)
        inner_r = max(1, body_r - 4)
        pygame.draw.circle(screen, (200, 140, 255), (cx, cy), inner_r)
        pygame.draw.circle(screen, (240, 200, 255), (cx, cy), max(1, inner_r // 2))
        for i in range(3):
            sa = t * 5 + i * math.pi * 2 / 3
            sd = 10 + 3 * math.sin(t * 4 + i)
            sx = cx + int(math.cos(sa) * sd)
            sy = cy + int(math.sin(sa) * sd)
            ss = 2
            sa_alpha = int(160 + 60 * math.sin(t * 7 + i * 2))
            pygame.draw.circle(screen, (180, 100, 240, sa_alpha), (sx, sy), ss)


# ============================================================
# CHAIN LIGHTNING BOLT — stormcaller projectile that stuns
# ============================================================
class ChainLightningBolt:
    """Lightning bolt projectile that applies dizziness on hit."""
    def __init__(self, origin, direction, speed, max_range, damage, dizzy_duration):
        self.pos = pygame.Vector2(origin)
        self.direction = pygame.Vector2(direction).normalize()
        self.speed = speed
        self.max_range = max_range
        self.damage = damage
        self.dizzy_duration = dizzy_duration
        self.alive = True
        self.traveled = 0.0
        self.trail = []
        self.animation_time = 0.0
        self._zigzag_offset = 0.0
        self._last_zigzag = 0

    def get_rect(self):
        rect = pygame.Rect(0, 0, 8, 8)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, player):
        if not self.alive:
            return
        self.animation_time += dt
        self.traveled += self.speed * dt
        self.pos += self.direction * self.speed * dt
        self.trail.append(pygame.Vector2(self.pos))
        if len(self.trail) > 12:
            self.trail.pop(0)
        # zigzag lightning wobble
        self._zigzag_offset = math.sin(self.animation_time * 30) * 4
        # hit player
        pr = player.get_rect()
        bolt_rect = pygame.Rect(int(self.pos.x) - 4, int(self.pos.y) - 4, 8, 8)
        if bolt_rect.colliderect(pr):
            if self.damage > 0:
                player.take_damage(self.damage)
            if self.dizzy_duration > 0:
                player.add_effect(DizzinessEffect(self.dizzy_duration))
            self.alive = False
            return
        if self.traveled >= self.max_range:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)
        t = self.animation_time
        # main bolt — jagged line from trail
        if len(self.trail) >= 2:
            for i in range(len(self.trail) - 1):
                p1 = self.trail[i]
                p2 = self.trail[i + 1]
                ratio = i / len(self.trail)
                a = int(255 * ratio)
                # perp wobble for lightning shape
                wobble = math.sin(t * 30 + i * 2.5) * 5
                perp_x = -self.direction.y * wobble
                perp_y = self.direction.x * wobble
                sx1 = int(p1.x - camera_offset.x + perp_x)
                sy1 = int(p1.y - camera_offset.y + perp_y)
                sx2 = int(p2.x - camera_offset.x + perp_x)
                sy2 = int(p2.y - camera_offset.y + perp_y)
                pygame.draw.line(screen, (100, 180, 255, a), (sx1, sy1), (sx2, sy2), 3)
                pygame.draw.line(screen, (220, 240, 255, a), (sx1, sy1), (sx2, sy2), 1)
        # glow at tip
        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        glow_sz = int(10 + 4 * math.sin(t * 20))
        gs = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (100, 200, 255, int(60 + 30 * math.sin(t * 15))),
                           (glow_sz, glow_sz), glow_sz)
        screen.blit(gs, (cx - glow_sz, cy - glow_sz))
        pygame.draw.circle(screen, (180, 220, 255), (cx, cy), 4)
        pygame.draw.circle(screen, (240, 250, 255), (cx, cy), 2)
        # branching sparks
        for i in range(3):
            spark_angle = t * 12 + i * 2.09
            spark_d = 8 + math.sin(t * 10 + i) * 3
            sx = cx + int(math.cos(spark_angle) * spark_d)
            sy = cy + int(math.sin(spark_angle) * spark_d)
            pygame.draw.line(screen, (150, 200, 255, 180), (cx, cy), (sx, sy), 1)


# ============================================================
# PLAGUE CLOUD — plaguebearer projectile that poisons on hit
# ============================================================
class PlagueCloud:
    """Toxic cloud projectile that applies poison and slow on hit."""
    def __init__(self, origin, direction, speed, max_range, damage, poison_duration, poison_dps):
        self.pos = pygame.Vector2(origin)
        self.direction = pygame.Vector2(direction).normalize()
        self.speed = speed
        self.max_range = max_range
        self.damage = damage
        self.poison_duration = poison_duration
        self.poison_dps = poison_dps
        self.alive = True
        self.traveled = 0.0
        self.trail = []
        self.animation_time = 0.0

    def get_rect(self):
        rect = pygame.Rect(0, 0, 20, 20)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, player):
        if not self.alive:
            return
        self.animation_time += dt
        self.traveled += self.speed * dt
        self.pos += self.direction * self.speed * dt
        self.trail.append(pygame.Vector2(self.pos))
        if len(self.trail) > 10:
            self.trail.pop(0)
        pr = player.get_rect()
        cloud_rect = pygame.Rect(int(self.pos.x) - 10, int(self.pos.y) - 10, 20, 20)
        if cloud_rect.colliderect(pr):
            if self.damage > 0:
                player.take_damage(self.damage)
            if self.poison_duration > 0:
                player.add_effect(PoisonEffect(self.poison_duration, self.poison_dps))
            self.alive = False
            return
        if self.traveled >= self.max_range:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)
        t = self.animation_time
        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        # toxic trail
        for i, pos in enumerate(self.trail):
            ratio = i / len(self.trail) if self.trail else 0
            a = int(100 * ratio)
            r = int(2 + 5 * ratio)
            tx = int(pos.x - camera_offset.x)
            ty = int(pos.y - camera_offset.y)
            wobble = math.sin(t * 6 + i * 0.9) * 3
            pygame.draw.circle(screen, (80, 160, 60, a), (tx + int(wobble), ty), r)
        # main cloud body — layered circles
        pulse = 0.7 + 0.3 * math.sin(t * 8)
        for layer in range(3):
            lr = int((8 + layer * 3) * pulse)
            la = int(180 - layer * 40)
            off_x = int(math.sin(t * 5 + layer) * 3)
            off_y = int(math.cos(t * 4 + layer) * 2)
            pygame.draw.circle(screen, (70 + layer * 20, 140 - layer * 10, 50 + layer * 10, la),
                               (cx + off_x, cy + off_y), lr)
        # bright center
        pygame.draw.circle(screen, (120, 200, 80), (cx, cy), 4)
        pygame.draw.circle(screen, (180, 240, 140), (cx, cy), 2)
        # toxic drip particles
        for i in range(3):
            drip_angle = t * 3 + i * 2.09
            drip_d = 12 + math.sin(t * 4 + i) * 3
            dx = cx + int(math.cos(drip_angle) * drip_d)
            dy = cy + int(math.sin(drip_angle) * drip_d) + 4
            pygame.draw.circle(screen, (100, 180, 60, 150), (dx, dy), 2)


class TimeBolt:
    """Temporal bolt fired by Chronos — applies slow and damages the player."""
    def __init__(self, pos, direction, speed, max_range, damage, slow_duration=2.0, slow_factor=0.5):
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()
        self.speed = speed
        self.max_range = max_range
        self.damage = damage
        self.slow_duration = slow_duration
        self.slow_factor = slow_factor
        self.traveled = 0.0
        self.alive = True
        self.trail = []
        self.animation_time = 0.0

    def get_rect(self):
        rect = pygame.Rect(0, 0, 16, 16)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, player):
        if not self.alive:
            return
        self.animation_time += dt
        self.traveled += self.speed * dt
        self.pos += self.direction * self.speed * dt
        self.trail.append(pygame.Vector2(self.pos))
        if len(self.trail) > 8:
            self.trail.pop(0)
        pr = player.get_rect()
        bolt_rect = pygame.Rect(int(self.pos.x) - 8, int(self.pos.y) - 8, 16, 16)
        if bolt_rect.colliderect(pr):
            if self.damage > 0:
                player.take_damage(self.damage)
            player.add_effect(SlowEffect(self.slow_duration, self.slow_factor))
            self.alive = False
            return
        if self.traveled >= self.max_range:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)
        t = self.animation_time
        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        # golden temporal trail
        for i, pos in enumerate(self.trail):
            ratio = i / len(self.trail) if self.trail else 0
            a = int(120 * ratio)
            r = int(2 + 4 * ratio)
            tx = int(pos.x - camera_offset.x)
            ty = int(pos.y - camera_offset.y)
            wobble = math.sin(t * 6 + i * 0.9) * 2
            pygame.draw.circle(screen, (220, 180, 60, a), (tx + int(wobble), ty), r)
        # main bolt body — glowing golden orb
        pulse = 0.7 + 0.3 * math.sin(t * 10)
        for layer in range(3):
            lr = int((6 + layer * 2) * pulse)
            la = int(200 - layer * 40)
            pygame.draw.circle(screen, (220, 180, 60, la), (cx, cy), lr)
        # bright core
        pygame.draw.circle(screen, (255, 220, 100), (cx, cy), 3)
        pygame.draw.circle(screen, (255, 255, 200), (cx, cy), 1)
        # clock-hand decorative lines
        for hi in range(2):
            ha = t * 4 + hi * math.pi
            hx2 = cx + int(math.cos(ha) * 6)
            hy2 = cy + int(math.sin(ha) * 6)
            pygame.draw.line(screen, (200, 170, 50, 100), (cx, cy), (hx2, hy2), 1)


class ChronoBurst:
    """AoE temporal explosion — expands outward dealing damage and applying slow."""
    def __init__(self, pos, damage, radius=100.0, slow_duration=1.5, slow_factor=0.6):
        self.pos = pygame.Vector2(pos)
        self.damage = damage
        self.radius = radius
        self.slow_duration = slow_duration
        self.slow_factor = slow_factor
        self.alive = True
        self.animation_time = 0.0
        self.duration = 0.6
        self.hit_player = False

    def get_rect(self):
        r = int(self.radius * (self.animation_time / self.duration) if self.duration > 0 else 0)
        rect = pygame.Rect(0, 0, r * 2, r * 2)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, player):
        if not self.alive:
            return
        self.animation_time += dt
        progress = min(1.0, self.animation_time / self.duration)
        current_radius = self.radius * progress
        if not self.hit_player and player is not None:
            pr = player.get_rect()
            dist = pygame.Vector2(player.pos) - self.pos
            if dist.length_squared() <= current_radius * current_radius:
                if self.damage > 0:
                    player.take_damage(self.damage)
                player.add_effect(SlowEffect(self.slow_duration, self.slow_factor))
                self.hit_player = True
        if self.animation_time >= self.duration:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)
        t = self.animation_time
        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        progress = min(1.0, t / self.duration)
        current_r = int(self.radius * progress)
        alpha = int(180 * (1.0 - progress))
        # expanding ring
        pygame.draw.circle(screen, (220, 180, 60, alpha), (cx, cy), current_r, 2)
        pygame.draw.circle(screen, (255, 210, 80, alpha // 2), (cx, cy), max(0, current_r - 5), 1)
        # inner fill (fading)
        fill_alpha = int(60 * (1.0 - progress))
        pygame.draw.circle(screen, (200, 170, 50, fill_alpha), (cx, cy), current_r)
        # center flash
        if progress < 0.3:
            flash_alpha = int(200 * (1.0 - progress / 0.3))
            pygame.draw.circle(screen, (255, 230, 120, flash_alpha), (cx, cy), int(12 * (1.0 - progress)))
        # floating rune particles
        for ri in range(4):
            angle = t * 3 + ri * 1.57
            rr = int(current_r * 0.7)
            rx = cx + int(math.cos(angle) * rr)
            ry = cy + int(math.sin(angle) * rr)
            ra = max(0, int(120 * (1.0 - progress)))
            pygame.draw.circle(screen, (200, 170, 50, ra), (rx, ry), 2)


class TemporalSiphon:
    """Majestic spiraling bolt that drains life force — heals Chronos on hit."""
    def __init__(self, pos, direction, speed, max_range, damage, heal_amount=15,
                 slow_duration=1.0, slow_factor=0.7):
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()
        self.speed = speed
        self.max_range = max_range
        self.damage = damage
        self.heal_amount = heal_amount
        self.slow_duration = slow_duration
        self.slow_factor = slow_factor
        self.traveled = 0.0
        self.alive = True
        self.trail = []
        self.animation_time = 0.0
        self.spiral_particles = []

    def get_rect(self):
        rect = pygame.Rect(0, 0, 20, 20)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, player):
        if not self.alive:
            return
        self.animation_time += dt
        self.traveled += self.speed * dt
        self.pos += self.direction * self.speed * dt
        self.trail.append(pygame.Vector2(self.pos))
        if len(self.trail) > 14:
            self.trail.pop(0)
        # spawn spiral particles
        if int(self.animation_time * 30) % 2 == 0:
            angle = self.animation_time * 8
            dist = 8 + len(self.spiral_particles) * 0.5
            self.spiral_particles.append({
                "angle": angle, "dist": dist, "life": 1.0,
                "offset": pygame.Vector2(math.cos(angle) * dist, math.sin(angle) * dist),
            })
        for sp in self.spiral_particles:
            sp["life"] -= dt * 3.0
            sp["dist"] += dt * 20
            sp["offset"] = pygame.Vector2(
                math.cos(sp["angle"] + self.animation_time * 4) * sp["dist"],
                math.sin(sp["angle"] + self.animation_time * 4) * sp["dist"],
            )
        self.spiral_particles = [sp for sp in self.spiral_particles if sp["life"] > 0]
        pr = player.get_rect()
        bolt_rect = pygame.Rect(int(self.pos.x) - 10, int(self.pos.y) - 10, 20, 20)
        if bolt_rect.colliderect(pr):
            if self.damage > 0:
                player.take_damage(self.damage)
            player.add_effect(SlowEffect(self.slow_duration, self.slow_factor))
            self.alive = False
            return
        if self.traveled >= self.max_range:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)
        t = self.animation_time
        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        # spiral trail particles
        for sp in self.spiral_particles:
            alpha = int(180 * sp["life"])
            px = int(self.pos.x + sp["offset"].x - camera_offset.x)
            py = int(self.pos.y + sp["offset"].y - camera_offset.y)
            r = int(2 + 2 * sp["life"])
            pygame.draw.circle(screen, (180, 120, 255, alpha), (px, py), r)
        # main trail (violet-gold spiral)
        for i, pos in enumerate(self.trail):
            ratio = i / len(self.trail) if self.trail else 0
            a = int(150 * ratio)
            r = int(2 + 5 * ratio)
            tx = int(pos.x - camera_offset.x)
            ty = int(pos.y - camera_offset.y)
            wobble = math.sin(t * 8 + i * 1.2) * 3
            wobble2 = math.cos(t * 6 + i * 0.9) * 2
            color_r = int(200 + 55 * ratio)
            color_g = int(140 + 60 * ratio)
            color_b = int(255 - 80 * ratio)
            pygame.draw.circle(screen, (color_r, color_g, color_b, a), (tx + int(wobble), ty + int(wobble2)), r)
        # outer glow
        pulse = 0.7 + 0.3 * math.sin(t * 12)
        glow_r = int(14 * pulse)
        glow_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (180, 120, 255, 35), (20, 20), glow_r + 6)
        pygame.draw.circle(glow_surf, (200, 150, 255, 50), (20, 20), glow_r)
        screen.blit(glow_surf, (cx - 20, cy - 20), special_flags=pygame.BLEND_ALPHA_SDL2)
        # main orb body
        for layer in range(3):
            lr = int((7 + layer * 2) * pulse)
            la = int(220 - layer * 40)
            pygame.draw.circle(screen, (180, 130, 255, la), (cx, cy), lr)
        # gold ring inside
        pygame.draw.circle(screen, (220, 180, 60, 120), (cx, cy), int(5 * pulse), 1)
        # bright core
        pygame.draw.circle(screen, (240, 220, 255), (cx, cy), 3)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 1)
        # clock-hand siphon lines (draining inward)
        for hi in range(3):
            ha = -t * 5 + hi * (math.pi * 2 / 3)
            hx2 = cx + int(math.cos(ha) * 10)
            hy2 = cy + int(math.sin(ha) * 10)
            pygame.draw.line(screen, (200, 150, 255, 80), (hx2, hy2), (cx, cy), 1)


class EternalChains:
    """Slow-moving chain projectile that roots the player on hit."""
    def __init__(self, pos, direction, speed, max_range, damage,
                 root_duration=1.5, slow_duration=2.0, slow_factor=0.4):
        self.pos = pygame.Vector2(pos)
        self.direction = pygame.Vector2(direction)
        if self.direction.length_squared() == 0:
            self.direction = pygame.Vector2(1, 0)
        else:
            self.direction = self.direction.normalize()
        self.speed = speed
        self.max_range = max_range
        self.damage = damage
        self.root_duration = root_duration
        self.slow_duration = slow_duration
        self.slow_factor = slow_factor
        self.traveled = 0.0
        self.alive = True
        self.chain_links = []
        self.animation_time = 0.0
        self._build_chain_links()

    def _build_chain_links(self):
        for i in range(6):
            self.chain_links.append({
                "offset": pygame.Vector2(-i * 6, 0),
                "angle": 0.0,
                "swing": 0.0,
            })

    def get_rect(self):
        rect = pygame.Rect(0, 0, 24, 24)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, player):
        if not self.alive:
            return
        self.animation_time += dt
        self.traveled += self.speed * dt
        self.pos += self.direction * self.speed * dt
        # animate chain links with physics-like swing
        for i, link in enumerate(self.chain_links):
            link["angle"] = self.animation_time * (3 + i * 0.5)
            link["swing"] = math.sin(self.animation_time * 4 + i * 0.8) * (2 + i * 0.5)
            link["offset"] = pygame.Vector2(
                -i * 6 * self.direction.x + link["swing"] * self.direction.y,
                -i * 6 * self.direction.y - link["swing"] * self.direction.x,
            )
        pr = player.get_rect()
        bolt_rect = pygame.Rect(int(self.pos.x) - 12, int(self.pos.y) - 12, 24, 24)
        if bolt_rect.colliderect(pr):
            if self.damage > 0:
                player.take_damage(self.damage)
            player.add_effect(RootEffect(self.root_duration))
            player.add_effect(SlowEffect(self.slow_duration, self.slow_factor))
            self.alive = False
            return
        if self.traveled >= self.max_range:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)
        t = self.animation_time
        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        # chain link trail
        for i in range(len(self.chain_links) - 1, -1, -1):
            link = self.chain_links[i]
            lx = int(self.pos.x + link["offset"].x - camera_offset.x)
            ly = int(self.pos.y + link["offset"].y - camera_offset.y)
            alpha = max(40, 200 - i * 30)
            # chain link (oval)
            link_w = 5
            link_h = 3
            # rotation effect via polygon
            cos_a = math.cos(link["angle"])
            sin_a = math.sin(link["angle"])
            pts = []
            for ai in range(8):
                a = ai * (math.pi * 2 / 8)
                px = int(lx + (link_w * math.cos(a) * cos_a - link_h * math.sin(a) * sin_a))
                py = int(ly + (link_w * math.cos(a) * sin_a + link_h * math.sin(a) * cos_a))
                pts.append((px, py))
            if len(pts) >= 3:
                pygame.draw.polygon(screen, (180, 155, 45, alpha), pts, 2)
                pygame.draw.polygon(screen, (220, 190, 60, alpha // 2), pts)
        # leading chain head (ornate)
        head_pulse = 0.7 + 0.3 * math.sin(t * 10)
        # outer glow
        glow_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (220, 180, 60, 30), (18, 18), int(14 * head_pulse))
        screen.blit(glow_surf, (cx - 18, cy - 18), special_flags=pygame.BLEND_ALPHA_SDL2)
        # head orb
        for layer in range(3):
            lr = int((6 + layer * 2) * head_pulse)
            la = int(200 - layer * 40)
            pygame.draw.circle(screen, (180, 155, 45, la), (cx, cy), lr)
        # golden rune core
        pygame.draw.circle(screen, (220, 180, 60), (cx, cy), 4)
        pygame.draw.circle(screen, (255, 220, 90), (cx, cy), 2)
        # binding rune symbols
        for ri in range(4):
            ra = t * 3 + ri * (math.pi / 2)
            rx = cx + int(math.cos(ra) * 8)
            ry = cy + int(math.sin(ra) * 8)
            pygame.draw.line(screen, (200, 170, 50, 100), (rx, ry), (cx, cy), 1)
            pygame.draw.circle(screen, (220, 180, 60, 80), (rx, ry), 1)


class ParadoxMirror:
    """Floating temporal mirror that creates a paradox zone — slows and damages enemies within (player AoE denial)."""
    def __init__(self, pos, damage, radius=90.0, duration=3.0,
                 slow_duration=2.0, slow_factor=0.5):
        self.pos = pygame.Vector2(pos)
        self.damage = damage
        self.radius = radius
        self.duration = duration
        self.slow_duration = slow_duration
        self.slow_factor = slow_factor
        self.alive = True
        self.animation_time = 0.0
        self.hit_cooldowns = {}
        self.mirror_angle = 0.0

    def get_rect(self):
        r = int(self.radius)
        rect = pygame.Rect(0, 0, r * 2, r * 2)
        rect.center = (int(self.pos.x), int(self.pos.y))
        return rect

    def update(self, dt, obstacles, player):
        if not self.alive:
            return
        self.animation_time += dt
        self.mirror_angle += dt * 2.0
        if self.animation_time >= self.duration:
            self.alive = False
            return
        if player is None:
            return
        # damage player periodically if inside radius
        dist = pygame.Vector2(player.pos) - self.pos
        if dist.length_squared() <= self.radius * self.radius:
            now_key = id(player)
            last_hit = self.hit_cooldowns.get(now_key, -1.0)
            if self.animation_time - last_hit >= 0.8:
                if self.damage > 0:
                    player.take_damage(self.damage)
                player.add_effect(SlowEffect(self.slow_duration, self.slow_factor))
                self.hit_cooldowns[now_key] = self.animation_time

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)
        t = self.animation_time
        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        progress = min(1.0, t / self.duration)
        fade = 1.0 - progress
        # paradox zone ground effect
        zone_alpha = int(50 * fade)
        zone_r = int(self.radius * (0.8 + 0.2 * math.sin(t * 3)))
        # swirling ground runes
        for ri in range(8):
            ra = t * 1.5 + ri * (math.pi * 2 / 8)
            rr = int(zone_r * 0.8)
            rx = cx + int(math.cos(ra) * rr)
            ry = cy + int(math.sin(ra) * rr * 0.4)
            a = max(10, int(80 * fade))
            pygame.draw.circle(screen, (160, 120, 255, a), (rx, ry), 2)
            # connecting line to center
            pygame.draw.line(screen, (160, 120, 255, a // 3), (rx, ry), (cx, cy), 1)
        # zone boundary ring
        ring_alpha = int(120 * fade)
        pygame.draw.circle(screen, (140, 100, 230, ring_alpha), (cx, cy), zone_r, 1)
        pygame.draw.circle(screen, (180, 140, 255, ring_alpha // 2), (cx, cy), zone_r + 3, 1)
        # inner swirl
        for si in range(3):
            sa = t * 2.5 + si * (math.pi * 2 / 3)
            sr = int(zone_r * 0.5)
            sx = cx + int(math.cos(sa) * sr)
            sy = cy + int(math.sin(sa) * sr * 0.4)
            pygame.draw.circle(screen, (180, 140, 255, int(60 * fade)), (sx, sy), 3)
        # mirror orb at center (floating, rotating)
        mirror_glow = 0.7 + 0.3 * math.sin(t * 6)
        # outer glow
        mg = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(mg, (180, 140, 255, int(40 * fade)), (20, 20), int(16 * mirror_glow))
        screen.blit(mg, (cx - 20, cy - 20), special_flags=pygame.BLEND_ALPHA_SDL2)
        # mirror body (diamond shape rotating)
        mirror_size = int(8 * mirror_glow)
        m_pts = []
        for mi in range(4):
            ma = self.mirror_angle + mi * (math.pi / 2)
            mpx = cx + int(math.cos(ma) * mirror_size)
            mpy = cy + int(math.sin(ma) * mirror_size)
            m_pts.append((mpx, mpy))
        if len(m_pts) >= 3:
            pygame.draw.polygon(screen, (160, 120, 240), m_pts)
            pygame.draw.polygon(screen, (200, 170, 255), m_pts, 1)
        # bright center
        pygame.draw.circle(screen, (220, 200, 255, int(180 * fade)), (cx, cy), 3)
        pygame.draw.circle(screen, (255, 255, 255, int(150 * fade)), (cx, cy), 1)
        # paradox symbols orbiting the mirror
        for pi in range(4):
            pa = t * 3 + pi * (math.pi / 2)
            pr = 12 + int(math.sin(t * 4 + pi) * 3)
            px = cx + int(math.cos(pa) * pr)
            py = cy + int(math.sin(pa) * pr)
            pa_alpha = max(20, int(100 * fade))
            pygame.draw.circle(screen, (200, 170, 255, pa_alpha), (px, py), 2)
            pygame.draw.line(screen, (180, 150, 240, pa_alpha // 2), (px, py), (cx, cy), 1)
