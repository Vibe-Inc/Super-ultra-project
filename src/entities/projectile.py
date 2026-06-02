import math
import pygame
from database.effects import BurnEffect
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
        self.trail_length = 8

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
            # Draw trail
            for i, pos in enumerate(self.trail):
                alpha = int(100 * (i / len(self.trail)))
                radius = int(4 + 4 * (i / len(self.trail)))
                t_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(t_surf, (*self.color[:3], alpha), (radius, radius), radius)
                screen.blit(t_surf, (pos.x - radius - camera_offset.x, pos.y - radius - camera_offset.y))

            # Draw main fireball
            rect = self.get_rect()
            rect.x -= int(camera_offset.x)
            rect.y -= int(camera_offset.y)
            
            # Outer glow
            pulse = (math.sin(self.animation_time * 10) + 1.0) * 0.5
            glow_size = int(rect.width * (1.2 + 0.2 * pulse))
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color, 60), (glow_size, glow_size), glow_size)
            screen.blit(glow_surf, (rect.centerx - glow_size, rect.centery - glow_size))
            
            # Core
            pygame.draw.circle(screen, (255, 240, 200), rect.center, rect.width // 2 - 2)
            pygame.draw.circle(screen, self.color, rect.center, rect.width // 2)
            
            # Inner bright spot
            pygame.draw.circle(screen, (255, 255, 255), rect.center, max(2, rect.width // 4), 1)
            return

        # Explosion visuals
        progress = min(1.0, self.explosion_timer / self.explosion_duration)
        radius = int(self.blast_radius * progress)
        if radius <= 0:
            return
            
        # Shockwave ring
        ring_alpha = int(255 * (1 - progress))
        pygame.draw.circle(screen, (255, 200, 100), (int(self.pos.x - camera_offset.x), int(self.pos.y - camera_offset.y)), radius, 3)
        
        # Inner fire
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        inner_alpha = int(180 * (1 - progress))
        pygame.draw.circle(surface, (255, 100, 20, inner_alpha), (radius, radius), radius)
        pygame.draw.circle(surface, (255, 240, 100, int(inner_alpha * 0.6)), (radius, radius), max(1, radius // 2))
        
        screen.blit(surface, (self.pos.x - radius - camera_offset.x, self.pos.y - radius - camera_offset.y))
