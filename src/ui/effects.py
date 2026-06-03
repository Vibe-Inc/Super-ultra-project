import math
import random
import pygame

GOLD = (212, 175, 55)
GOLD_BRIGHT = (255, 215, 0)
GOLD_DARK = (160, 120, 30)


def ease_out_back(t):
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def ease_out_elastic(t):
    if t == 0 or t == 1:
        return t
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1


def ease_in_quart(t):
    return t * t * t * t


class Star:
    def __init__(self, sw, sh):
        self.x = random.uniform(0, sw)
        self.y = random.uniform(0, sh)
        self.size = random.uniform(0.5, 2.8)
        self.base_alpha = random.randint(20, 200)
        self.twinkle_speed = random.uniform(0.4, 3.0)
        self.phase = random.uniform(0, 6.28)
        self.color = random.choice([
            (255, 255, 255),
            (255, 240, 200),
            (200, 220, 255),
            (255, 200, 180),
        ])

    def draw(self, surf, t):
        alpha = int(self.base_alpha * (0.5 + 0.5 * math.sin(t * self.twinkle_speed + self.phase)))
        alpha = max(0, min(255, alpha))
        if alpha < 5:
            return
        px = int(self.x)
        py = int(self.y)
        sz = max(1, self.size)
        if sz <= 1.5:
            surf.set_at((px, py), (*self.color, alpha))
        else:
            s = pygame.Surface((int(sz * 2), int(sz * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (int(sz), int(sz)), int(sz))
            surf.blit(s, (px - int(sz), py - int(sz)))


class LightRay:
    def __init__(self, sw, sh):
        self.sw = sw
        self.sh = sh
        self._reset()

    def _reset(self):
        self.y = random.uniform(0, self.sh)
        self.height = random.uniform(20, 80)
        self.speed = random.uniform(0.15, 0.4)
        self.phase = random.uniform(0, 6.28)
        self.amp = random.uniform(20, 60)
        self.alpha = random.randint(3, 12)
        self.width_factor = random.uniform(0.3, 0.8)

    def draw(self, surf, t):
        cy = self.y + math.sin(t * self.speed + self.phase) * self.amp
        h = self.height
        s = pygame.Surface((int(self.sw * self.width_factor), int(h)), pygame.SRCALPHA)
        for i in range(int(h)):
            ratio = 1.0 - abs(i - h / 2) / (h / 2)
            a = int(self.alpha * max(0, ratio) ** 2)
            if a < 1:
                continue
            c = (255, 230, 180, min(255, a))
            pygame.draw.line(s, c, (0, i), (s.get_width(), i))
        sx = int(self.sw * (1 - self.width_factor) * 0.5)
        surf.blit(s, (sx, int(cy - h / 2)))


class AmbientEmber:
    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        self._reset()

    def _reset(self):
        self.x = random.uniform(0, self.sw)
        self.y = random.uniform(self.sh, self.sh + 50)
        self.speed = random.uniform(15, 50)
        self.sway_amp = random.uniform(10, 40)
        self.sway_freq = random.uniform(0.5, 2.0)
        self.phase = random.uniform(0, 6.28)
        self.size = random.uniform(1.0, 3.5)
        self.alpha = random.randint(30, 120)
        self.color = random.choice([
            (255, 200, 80),
            (255, 180, 60),
            (255, 220, 100),
            (255, 160, 40),
            (200, 150, 255),
        ])

    def update(self, dt, t):
        self.y -= self.speed * dt
        self.x += math.sin(t * self.sway_freq + self.phase) * self.sway_amp * dt
        if self.y < -20 or self.x < -50 or self.x > self.sw + 50:
            self._reset()

    def draw(self, surf, t):
        a = int(self.alpha * (0.6 + 0.4 * math.sin(t * 1.5 + self.phase)))
        a = max(0, min(255, a))
        sz = self.size
        s = pygame.Surface((int(sz * 2 + 2), int(sz * 2 + 2)), pygame.SRCALPHA)
        for ri in range(int(sz), 0, -1):
            ratio = ri / sz
            ca = int(a * (1 - ratio))
            pygame.draw.circle(s, (*self.color, max(0, min(255, ca))),
                               (int(sz + 1), int(sz + 1)), ri)
        surf.blit(s, (int(self.x - sz), int(self.y - sz)))


class FloatingOrb:
    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        self._reset(True)

    def _reset(self, init=False):
        self.x = random.uniform(0, self.sw)
        self.y = random.uniform(0, self.sh) if init else random.uniform(self.sh, self.sh + 100)
        self.vx = random.uniform(-15, 15)
        self.vy = random.uniform(-40, -10)
        self.radius = random.randint(30, 90)
        self.hue_shift = random.uniform(-30, 30)
        self.phase = random.uniform(0, 6.28)
        self.freq = random.uniform(0.3, 1.0)
        self.alpha_base = random.randint(6, 22)
        self.color_variant = random.choice(['gold', 'purple', 'teal', 'crimson'])

    def _get_color(self, ri, r, a):
        if self.color_variant == 'gold':
            return (max(0, min(255, 210 + int(self.hue_shift))),
                    max(0, min(255, 175 + int(self.hue_shift * 0.5))),
                    max(0, min(255, 55 + int(self.hue_shift * 0.3))), a)
        elif self.color_variant == 'purple':
            return (max(0, min(255, 180 + int(self.hue_shift))),
                    max(0, min(255, 120 + int(self.hue_shift * 0.3))),
                    max(0, min(255, 220 + int(self.hue_shift))), a)
        elif self.color_variant == 'teal':
            return (max(0, min(255, 80 + int(self.hue_shift * 0.3))),
                    max(0, min(255, 200 + int(self.hue_shift))),
                    max(0, min(255, 200 + int(self.hue_shift))), a)
        else:
            return (max(0, min(255, 200 + int(self.hue_shift))),
                    max(0, min(255, 80 + int(self.hue_shift * 0.3))),
                    max(0, min(255, 80 + int(self.hue_shift * 0.3))), a)

    def update(self, dt, t):
        self.x += self.vx * dt + math.sin(t * 0.3 + self.phase) * 10 * dt
        self.y += self.vy * dt
        if self.y < -self.radius * 2 or self.x < -self.radius * 2 or self.x > self.sw + self.radius * 2:
            self._reset()

    def draw(self, surf, t):
        a = int(self.alpha_base * (0.5 + 0.5 * math.sin(t * self.freq + self.phase)))
        a = max(0, min(40, a))
        px = int(self.x)
        py = int(self.y)
        r = self.radius
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for ri in range(r, 0, -2):
            ratio = ri / r
            ca = int(a * (1 - ratio) ** 1.5)
            c = self._get_color(ri, r, ca)
            pygame.draw.circle(s, c, (r, r), ri)
        surf.blit(s, (px - r, py - r))


class LaunchBurst:
    def __init__(self, x, y, vx, vy, color, size, lt):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.size = size
        self.lt = self.max_lt = lt

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 40 * dt
        self.lt -= dt

    def draw(self, surf):
        if self.lt <= 0:
            return
        a = int(255 * (self.lt / self.max_lt))
        sz = max(1, int(self.size * (self.lt / self.max_lt)))
        c = (*self.color[:3], a)
        s = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, c, (sz, sz), sz)
        surf.blit(s, (int(self.x) - sz, int(self.y) - sz))


def render_shimmer_text(font, text, base_color, t, intensity=0.15):
    tb = int(t * 6)
    ck = (id(font), text, base_color, tb)
    if not hasattr(render_shimmer_text, '_cache'):
        render_shimmer_text._cache = {}
    if ck in render_shimmer_text._cache:
        return render_shimmer_text._cache[ck]
    result = font.render(text, True, base_color)
    if intensity <= 0:
        return result
    w, h = result.get_size()
    shimmer_w = max(1, int(w * 0.2))
    band = pygame.Surface((shimmer_w, h), pygame.SRCALPHA)
    for sx in range(shimmer_w):
        ratio = 1.0 - abs(sx - shimmer_w // 2) / (shimmer_w // 2 + 1)
        a = int(60 * ratio * intensity / 0.15)
        pygame.draw.line(band, (*GOLD_BRIGHT, max(0, min(140, a))), (sx, 0), (sx, h))
    band_x = int((t * 180) % (w + shimmer_w)) - shimmer_w
    result.blit(band, (band_x, 0), special_flags=pygame.BLEND_RGBA_ADD)
    if len(render_shimmer_text._cache) > 30:
        render_shimmer_text._cache.clear()
    render_shimmer_text._cache[ck] = result
    return result


class TitleSparkle:
    def __init__(self, x, y):
        self.x = x + random.uniform(-4, 4)
        self.y = y + random.uniform(-4, 4)
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-20, -5)
        self.life = 1.0
        self.max_life = random.uniform(0.4, 1.0)
        self.size = random.uniform(1, 3)
        angle = random.uniform(0, 6.28)
        self.color = (
            max(0, min(255, 255)),
            max(0, min(255, int(200 + 55 * math.sin(angle)))),
            max(0, min(255, int(140 + 80 * math.cos(angle)))),
        )

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 15 * dt
        self.life -= dt / self.max_life

    def draw(self, surf):
        if self.life <= 0:
            return
        a = int(255 * self.life)
        sz = max(0.5, self.size * self.life)
        s = pygame.Surface((int(sz * 2 + 2), int(sz * 2 + 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, max(0, min(255, a))), (int(sz + 1), int(sz + 1)), int(sz))
        surf.blit(s, (int(self.x - sz), int(self.y - sz)))
