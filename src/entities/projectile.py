import pygame

from src.items.effects import BurnEffect


class Arrow:
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

    def _size(self):
        if abs(self.direction.x) >= abs(self.direction.y):
            return (18, 6)
        return (6, 18)

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

        rect = self.get_rect()
        for wall in obstacles:
            if rect.colliderect(wall):
                self.alive = False
                return

        for enemy in enemies:
            if rect.colliderect(enemy.get_rect()):
                enemy.take_damage(self.damage)
                self.alive = False
                return

        if self.traveled >= self.max_range:
            self.alive = False

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        rect = self.get_rect()
        rect.x -= int(camera_offset.x)
        rect.y -= int(camera_offset.y)
        pygame.draw.rect(screen, self.color, rect)

        if abs(self.direction.x) >= abs(self.direction.y):
            tip = (rect.left if self.direction.x < 0 else rect.right, rect.centery)
        else:
            tip = (rect.centerx, rect.top if self.direction.y < 0 else rect.bottom)

        pygame.draw.circle(screen, (90, 60, 30), tip, 2)


class ArcaneBolt:
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

    def _size(self):
        if abs(self.direction.x) >= abs(self.direction.y):
            return (14, 8)
        return (8, 14)

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

        rect = self.get_rect()
        for wall in obstacles:
            if rect.colliderect(wall):
                self.alive = False
                return

        if player and rect.colliderect(player.get_rect()):
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

        rect = self.get_rect()
        rect.x -= int(camera_offset.x)
        rect.y -= int(camera_offset.y)
        pygame.draw.ellipse(screen, self.color, rect)

        tail_offset = self.direction * -6
        tail_pos = (int(self.pos.x + tail_offset.x - camera_offset.x), int(self.pos.y + tail_offset.y - camera_offset.y))
        pygame.draw.circle(screen, (40, 90, 180), tail_pos, 3)


class Bomb:
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

    def _size(self):
        return 12, 12

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
                self._trigger_explosion()
                return

        if self.timer >= self.fuse_time or self.traveled >= self.max_range:
            self._trigger_explosion()

    def draw(self, screen, camera_offset=None):
        if camera_offset is None:
            camera_offset = pygame.Vector2(0, 0)

        if not self.exploding:
            rect = self.get_rect()
            rect.x -= int(camera_offset.x)
            rect.y -= int(camera_offset.y)
            pygame.draw.circle(screen, self.color, rect.center, rect.width // 2)
            pygame.draw.circle(screen, (60, 40, 20), rect.center, 3)
            return

        progress = min(1.0, self.explosion_timer / self.explosion_duration)
        radius = int(self.blast_radius * progress)
        if radius <= 0:
            return
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surface, (255, 180, 90, 140), (radius, radius), radius)
        screen.blit(surface, (self.pos.x - radius - camera_offset.x, self.pos.y - radius - camera_offset.y))
