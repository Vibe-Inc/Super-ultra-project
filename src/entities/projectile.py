import pygame


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

        movement = self.direction * self.speed * dt
        self.pos += movement
        self.traveled += movement.length()

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

    def draw(self, screen):
        rect = self.get_rect()
        pygame.draw.rect(screen, self.color, rect)

        if abs(self.direction.x) >= abs(self.direction.y):
            tip = (rect.left if self.direction.x < 0 else rect.right, rect.centery)
        else:
            tip = (rect.centerx, rect.top if self.direction.y < 0 else rect.bottom)

        pygame.draw.circle(screen, (90, 60, 30), tip, 2)
