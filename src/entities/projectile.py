import math
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
    Ice shard projectile that cascades forward, dealing damage and freezing on impact.

    Attributes:
        pos (pygame.Vector2): Current position.
        direction (pygame.Vector2): Travel direction.
        speed (float): Travel speed.
        max_range (float): Maximum travel distance.
        damage (int): Damage on hit.
        freeze_duration (float): Freeze duration on hit.
        cascade_width (float): Width of the cascade area.
        alive (bool): Whether the projectile is active.
        traveled (float): Distance traveled.
        animation_time (float): Visual animation timer.
        trail (list): Visual trail points.
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
        self.cascade_width = cascade_width
        self.color = color
        self.alive = True
        self.traveled = 0.0
        self.animation_time = 0.0
        self.trail = []
        self.trail_length = 10
        self.damage_applied = False

    def _size(self):
        return 14, 14

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

        rect = self.get_rect()
        for wall in obstacles:
            if rect.colliderect(wall):
                self._apply_cascade(enemies)
                self.alive = False
                return

        for enemy in enemies:
            if enemy.is_dead():
                continue
            if rect.colliderect(enemy.get_rect()):
                self._apply_cascade(enemies)
                self.alive = False
                return

        if self.traveled >= self.max_range:
            self._apply_cascade(enemies)
            self.alive = False

    def _apply_cascade(self, enemies):
        """Apply damage and freeze to enemies within the cascade area."""
        if self.damage_applied:
            return
        self.damage_applied = True

        half_width = self.cascade_width * 0.5
        for enemy in enemies:
            if enemy.is_dead():
                continue
            enemy_rect = enemy.get_rect()
            enemy_center = pygame.Vector2(enemy_rect.centerx, enemy_rect.centery)

            to_enemy = enemy_center - self.pos
            forward_dist = to_enemy.dot(self.direction)
            if forward_dist < -half_width or forward_dist > half_width:
                continue
            lateral = to_enemy - self.direction * forward_dist
            if lateral.length_squared() > self.cascade_width * self.cascade_width * 0.25:
                continue

            if self.damage > 0:
                enemy.take_damage(self.damage)
            enemy.add_effect(FreezeEffect(self.freeze_duration))

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        # ── Ice trail ──
        for i, pos in enumerate(self.trail):
            alpha = int(120 * (i / len(self.trail)))
            radius = int(3 + 3 * (i / len(self.trail)))
            t_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(t_surf, (*self.color[:3], alpha), (radius, radius), radius)
            screen.blit(t_surf, (pos.x - radius - camera_offset.x, pos.y - radius - camera_offset.y))

        # ── Main ice shard ──
        rect = self.get_rect()
        rect.x -= int(camera_offset.x)
        rect.y -= int(camera_offset.y)

        pulse = (math.sin(self.animation_time * 12) + 1.0) * 0.5
        t = self.animation_time

        # Outer glow
        glow_size = int(rect.width * (1.5 + 0.3 * pulse))
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_color = (self.color[0], self.color[1], self.color[2], 50)
        pygame.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
        screen.blit(glow_surf, (rect.centerx - glow_size, rect.centery - glow_size))

        # Ice shard body (diamond)
        pts = [
            (rect.centerx, rect.top + 2),
            (rect.right - 2, rect.centery),
            (rect.centerx, rect.bottom - 2),
            (rect.left + 2, rect.centery),
        ]
        pygame.draw.polygon(screen, (160, 210, 255), pts)
        pygame.draw.polygon(screen, (200, 235, 255), pts, 2)

        # Inner bright core
        core_size = max(2, rect.width // 3)
        core_color = (220, 245, 255, int(180 + 75 * pulse))
        pygame.draw.circle(screen, core_color[:3], rect.center, core_size)

        # Sparkle effect
        sp_x = rect.centerx + int(4 * math.sin(t * 15))
        sp_y = rect.centery + int(4 * math.cos(t * 12))
        pygame.draw.circle(screen, (255, 255, 255), (sp_x, sp_y), max(1, core_size // 2))


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
        self.trail_length = 8

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

            if self.timer >= self.expansion_duration:
                self.alive = False

            # Vine points
            import random as _rnd
            for _ in range(2):
                angle = _rnd.uniform(0, math.pi * 2)
                dist = _rnd.uniform(0, self.radius * progress)
                self.vine_points.append((angle, dist, self.animation_time))
            if len(self.vine_points) > 40:
                self.vine_points = self.vine_points[-40:]
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
            # Draw flying seed/sprout
            cx = int(self.pos.x - camera_offset.x)
            cy = int(self.pos.y - camera_offset.y)

            # Trail
            for i, pos in enumerate(self.trail):
                alpha = int(100 * (i / len(self.trail)))
                radius = int(2 + 3 * (i / len(self.trail)))
                t_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(t_surf, (60, 200, 60, alpha), (radius, radius), radius)
                screen.blit(t_surf, (pos.x - radius - camera_offset.x, pos.y - radius - camera_offset.y))

            pulse = (math.sin(self.animation_time * 10) + 1.0) * 0.5

            # Glow
            glow_size = 12 + int(4 * pulse)
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (80, 255, 80, 50), (glow_size, glow_size), glow_size)
            screen.blit(glow_surf, (cx - glow_size, cy - glow_size))

            # Seed body — small green orb with leaf-like shape
            pygame.draw.circle(screen, (60, 180, 60), (cx, cy), 7)
            pygame.draw.circle(screen, (120, 220, 100), (cx, cy), 5)
            pygame.draw.circle(screen, (200, 255, 180), (cx - 1, cy - 1), 2)

            # Tiny leaf wings
            leaf_w = 4 + 2 * pulse
            for side in (-1, 1):
                lx = cx + side * 6
                ly = cy - 2 + 2 * math.sin(self.animation_time * 8)
                pygame.draw.ellipse(screen, (80, 200, 60),
                                    (lx - leaf_w, ly - 2, leaf_w * 2, 4))
            return

        # Burst phase
        cx = int(self.pos.x - camera_offset.x)
        cy = int(self.pos.y - camera_offset.y)
        progress = min(1.0, self.timer / self.expansion_duration)
        current_radius = int(self.radius * progress)

        if current_radius <= 0:
            return

        import random as rnd

        # Outer green ring shockwave
        ring_alpha = int(180 * (1 - progress))
        pygame.draw.circle(screen, (60, 180, 60, ring_alpha), (cx, cy), current_radius, max(2, int(3 * (1 - progress) + 1)))

        # Main nature burst
        burst_surf = pygame.Surface((current_radius * 2, current_radius * 2), pygame.SRCALPHA)
        outer_alpha = int(100 * (1 - progress * 0.5))
        pygame.draw.circle(burst_surf, (40, 160, 40, outer_alpha), (current_radius, current_radius), current_radius)
        mid_r = max(1, int(current_radius * 0.65))
        mid_alpha = int(140 * (1 - progress * 0.3))
        pygame.draw.circle(burst_surf, (80, 200, 80, mid_alpha), (current_radius, current_radius), mid_r)
        inner_r = max(1, int(current_radius * 0.3))
        inner_alpha = int(180 * (1 - progress * 0.2))
        pygame.draw.circle(burst_surf, (180, 255, 160, inner_alpha), (current_radius, current_radius), inner_r)
        screen.blit(burst_surf, (cx - current_radius, cy - current_radius))

        # Rising leaf particles
        for _ in range(int(5 * (1 - progress) + 2)):
            lx = cx + rnd.uniform(-current_radius, current_radius)
            ly = cy - current_radius + progress * current_radius * 2 + rnd.uniform(-10, 10)
            l_size = rnd.randint(2, 4)
            l_color = rnd.choice([(60, 200, 60), (100, 220, 80), (160, 255, 120), (200, 255, 180)])
            leaf_surf = pygame.Surface((l_size * 2, l_size * 2), pygame.SRCALPHA)
            alpha = int(200 * (1 - progress))
            pygame.draw.circle(leaf_surf, (*l_color, alpha), (l_size, l_size), l_size)
            screen.blit(leaf_surf, (int(lx) - l_size, int(ly) - l_size))

        # Vine tendrils on the ground
        for angle, dist, t in self.vine_points:
            vx = cx + math.cos(angle + t * 0.5) * dist
            vy = cy + math.sin(angle + t * 0.5) * dist
            tendril_len = 8 + 4 * math.sin(angle * 3 + t * 2)
            ex = vx + math.cos(angle + 0.5) * tendril_len
            ey = vy + math.sin(angle + 0.5) * tendril_len
            vine_alpha = int(160 * (1 - dist / self.radius))
            pygame.draw.line(screen, (60, 140, 40, vine_alpha), (vx, vy), (ex, ey), 2)

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
        self.trail_length = 6
        self.target_pos = pygame.Vector2(target_pos) if target_pos else None

    def _size(self):
        return 10, 10

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

        rect = self.get_rect()
        for wall in obstacles:
            if rect.colliderect(wall):
                self.alive = False
                return

        if self.traveled >= self.max_range:
            self.alive = False

        # Hit if close to target position (visual-only projectile)
        if self.target_pos and self.pos.distance_to(self.target_pos) < 15:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        # Trail
        for i, pos in enumerate(self.trail):
            alpha = int(100 * (i / len(self.trail)))
            radius = int(2 + 3 * (i / len(self.trail)))
            t_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(t_surf, (*self.color[:3], alpha), (radius, radius), radius)
            screen.blit(t_surf, (pos.x - radius - camera_offset.x, pos.y - radius - camera_offset.y))

        rect = self.get_rect()
        rect.x -= int(camera_offset.x)
        rect.y -= int(camera_offset.y)

        pulse = (math.sin(self.animation_time * 12) + 1.0) * 0.5

        # Glow
        glow_size = int(rect.width * (1.5 + 0.3 * pulse))
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 60), (glow_size, glow_size), glow_size)
        screen.blit(glow_surf, (rect.centerx - glow_size, rect.centery - glow_size))

        # Body
        pygame.draw.circle(screen, (180, 255, 160), rect.center, rect.width // 2)
        pygame.draw.circle(screen, self.color, rect.center, rect.width // 2 - 1)
        # Core
        pygame.draw.circle(screen, (220, 255, 220), rect.center, max(2, rect.width // 4))


class ArcaneMissile:
    """
    Homing arcane missile that seeks the nearest enemy.

    Attributes:
        pos (pygame.Vector2): Current position.
        direction (pygame.Vector2): Initial direction.
        speed (float): Travel speed in pixels per second.
        max_range (float): Maximum travel distance.
        damage (int): Damage on hit.
        alive (bool): Whether the missile is active.
        traveled (float): Distance traveled so far.
        target (Enemy | None): Current homing target.
        homing_strength (float): How aggressively it tracks (0-1).
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
        self.trail_length = 8

    def _size(self):
        return 12, 12

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

    def update(self, dt, obstacles, enemies):
        if not self.alive:
            return

        self.animation_time += dt

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

        rect = self.get_rect()
        for wall in obstacles:
            if rect.colliderect(wall):
                self.alive = False
                return

        if self.traveled >= self.max_range:
            self.alive = False
            return

        # Hit detection against enemies
        for enemy in enemies:
            if enemy.is_dead():
                continue
            enemy_rect = enemy.get_rect()
            if rect.colliderect(enemy_rect):
                enemy.take_damage(self.damage)
                self.alive = False
                return

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        # Trail
        for i, pos in enumerate(self.trail):
            alpha = int(120 * (i / len(self.trail)))
            radius = int(2 + 3 * (i / len(self.trail)))
            t_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(t_surf, (180, 100, 220, alpha), (radius, radius), radius)
            screen.blit(t_surf, (pos.x - radius - camera_offset.x, pos.y - radius - camera_offset.y))

        rect = self.get_rect()
        rect.x -= int(camera_offset.x)
        rect.y -= int(camera_offset.y)

        pulse = (math.sin(self.animation_time * 15) + 1.0) * 0.5

        # Outer glow
        glow_size = int(rect.width * (2.0 + 0.4 * pulse))
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (200, 120, 255, 50), (glow_size, glow_size), glow_size)
        screen.blit(glow_surf, (rect.centerx - glow_size, rect.centery - glow_size))

        # Missile body - outer
        pygame.draw.circle(screen, (160, 80, 200), rect.center, rect.width // 2)
        # Missile body - inner
        pygame.draw.circle(screen, (200, 140, 240), rect.center, rect.width // 2 - 1)
        # Core
        core_r = max(2, rect.width // 4)
        core_pulse = 0.7 + 0.3 * pulse
        pygame.draw.circle(screen, (255, 220, 255), rect.center, int(core_r * core_pulse))
        # Inner spark
        pygame.draw.circle(screen, (255, 255, 255), rect.center, max(1, core_r // 2))


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

        screen.blit(surface, (cx - radius, cy - radius))

        # ── Shadow wisps ──
        import random
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
    def __init__(self, pos, damage, radius=120.0, duration=0.6):
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
