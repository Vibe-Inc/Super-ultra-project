import math
import random
import pygame
import src.config as cfg

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
    """A single twinkling background star.

    Attributes:
        x (float): X position.
        y (float): Y position.
        size (float): Radius of the star.
        base_alpha (int): Base alpha value for the twinkle.
        twinkle_speed (float): Speed of the twinkle oscillation.
        phase (float): Random phase offset for the twinkle wave.
        color (tuple): RGB color of the star.

    Methods:
        draw(surf, t): Draw the star with current twinkle alpha.
    """
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
            pygame.draw.circle(surf, (*self.color, alpha), (px, py), int(sz))


class LightRay:
    """A drifting ray of light across the screen.

    Attributes:
        sw (int): Screen width for boundary calculations.
        sh (int): Screen height for boundary calculations.
        y (float): Current Y position of the ray.
        height (float): Height of the light ray.
        speed (float): Drift speed of the ray.
        phase (float): Random phase offset for sine wave motion.
        amp (float): Amplitude of the sine wave drift.
        alpha (int): Alpha transparency of the ray.
        width_factor (float): Fraction of screen width the ray spans.

    Methods:
        _reset(): Reinitialize the ray with random values.
        draw(surf, t): Draw the light ray at the current position.
    """
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
    """A floating ember particle that rises upward.

    Attributes:
        sw (int): Screen width.
        sh (int): Screen height.
        x (float): Current X position.
        y (float): Current Y position.
        speed (float): Upward movement speed.
        sway_amp (float): Horizontal sway amplitude.
        sway_freq (float): Horizontal sway frequency.
        phase (float): Random phase offset.
        size (float): Radius of the ember.
        alpha (int): Base alpha transparency.
        color (tuple): RGB color tuple.

    Methods:
        _reset(): Reinitialize the ember with random values.
        update(dt, t): Move the ember upward and sway it.
        draw(surf, t): Draw the ember with pulsing alpha.
    """
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
        for ri in range(int(sz), 0, -1):
            ratio = ri / sz
            ca = int(a * (1 - ratio))
            pygame.draw.circle(surf, (*self.color, max(0, min(255, ca))),
                               (int(self.x), int(self.y)), ri)


class FloatingOrb:
    """A large floating orb with a soft glowing halo.

    Attributes:
        sw (int): Screen width.
        sh (int): Screen height.
        x (float): Current X position.
        y (float): Current Y position.
        vx (float): Horizontal velocity.
        vy (float): Vertical velocity.
        radius (int): Radius of the orb.
        hue_shift (float): Color hue shift value.
        phase (float): Random phase offset for pulsing.
        freq (float): Pulse frequency.
        alpha_base (int): Base alpha for the glow.
        color_variant (str): Color scheme name ('gold', 'purple', 'teal', 'crimson').

    Methods:
        _reset(init=False): Reinitialize the orb with random values.
        _get_color(ri, r, a): Compute the color at a given ring.
        update(dt, t): Move the orb and apply drift.
        draw(surf, t): Draw the glowing orb.
    """
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
    """A burst particle emitted during a screen launch transition.

    Attributes:
        x (float): Current X position.
        y (float): Current Y position.
        vx (float): Horizontal velocity.
        vy (float): Vertical velocity.
        color (tuple): RGBA color tuple.
        size (float): Size of the particle.
        lt (float): Remaining lifetime in seconds.
        max_lt (float): Maximum lifetime in seconds.

    Methods:
        update(dt): Update position, gravity, and lifetime.
        draw(surf): Draw the particle if still alive.
    """
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
        pygame.draw.circle(surf, (*self.color[:3], a),
                           (int(self.x), int(self.y)), sz)


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
    """A small sparkle particle emitted from the title text.

    Attributes:
        x (float): Current X position.
        y (float): Current Y position.
        vx (float): Horizontal velocity.
        vy (float): Vertical velocity.
        life (float): Remaining life ratio (0 to 1).
        max_life (float): Maximum lifetime in seconds.
        size (float): Radius of the sparkle.
        color (tuple): RGB color tuple.

    Methods:
        update(dt): Update position, gravity, and lifetime.
        draw(surf): Draw the sparkle if still alive.
    """
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


class MenuClock:
    """An animated analogue clock rendered on the menu screen.

    Attributes:
        _face (pygame.Surface | None): Cached clock face surface.
        _key (tuple): Cache key based on screen dimensions.
        _numerals (list[str]): Roman numeral labels (XII, I, II, ...).
        _num_cache (dict): Cache for rendered numeral surfaces.

    Methods:
        _get_num_surf(text, font): Return a cached numeral surface.
        _build_face(sw, sh, scale): Pre-render the static clock face.
        draw(screen, t, sw, sh, scale): Draw the clock with animated hands.
    """
    def __init__(self):
        self._face = None
        self._key = (0, 0)
        self._numerals = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
        self._num_cache = {}

    def _get_num_surf(self, text, font):
        if text not in self._num_cache:
            self._num_cache[text] = font.render(text, True, GOLD_BRIGHT)
        return self._num_cache[text]

    def _build_face(self, sw, sh, scale):
        self._key = (sw, sh)
        self._face = pygame.Surface((sw, sh), pygame.SRCALPHA)
        cx, cy = sw // 2, int(sh * 0.35)
        base_r = min(sw, sh) // 4
        if base_r < 30:
            base_r = 30

        ring = pygame.Surface((base_r * 2, base_r * 2), pygame.SRCALPHA)
        for r, a, w in [(base_r, 30, 3), (base_r - 4, 20, 1), (base_r - 8, 15, 1)]:
            if r >= 4:
                pygame.draw.circle(ring, (*GOLD, a), (base_r, base_r), r, w)
        self._face.blit(ring, (cx - base_r, cy - base_r))

        for i in range(12):
            angle = math.radians(i * 30 - 90)
            inner_r = base_r - max(8, int(15 * scale))
            outer_r = base_r - max(3, int(5 * scale))
            ix = cx + int(math.cos(angle) * inner_r)
            iy = cy + int(math.sin(angle) * inner_r)
            ox = cx + int(math.cos(angle) * outer_r)
            oy = cy + int(math.sin(angle) * outer_r)
            pygame.draw.line(self._face, (*GOLD_BRIGHT, 40), (ix, iy), (ox, oy), 2)

        for i in range(60):
            if i % 5 == 0:
                continue
            angle = math.radians(i * 6 - 90)
            inner_r = base_r - max(6, int(10 * scale))
            outer_r = base_r - max(2, int(4 * scale))
            ix = cx + int(math.cos(angle) * inner_r)
            iy = cy + int(math.sin(angle) * inner_r)
            ox = cx + int(math.cos(angle) * outer_r)
            oy = cy + int(math.sin(angle) * outer_r)
            pygame.draw.line(self._face, (*GOLD, 20), (ix, iy), (ox, oy), 1)

        num_size = max(8, int(20 * scale))
        num_font = cfg.get_font(num_size)
        for i, numeral in enumerate(self._numerals):
            angle = math.radians(i * 30 - 90)
            r = base_r - max(18, int(30 * scale))
            ns = self._get_num_surf(numeral, num_font)
            nx = cx + int(math.cos(angle) * r) - ns.get_width() // 2
            ny = cy + int(math.sin(angle) * r) - ns.get_height() // 2
            self._face.blit(ns, (nx, ny))

        cd_r = max(3, int(6 * scale))
        cs = pygame.Surface((cd_r * 2, cd_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(cs, (*GOLD_BRIGHT, 60), (cd_r, cd_r), cd_r)
        self._face.blit(cs, (cx - cd_r, cy - cd_r))

    def draw(self, screen, t, sw, sh, scale):
        if self._key != (sw, sh) or self._face is None:
            self._build_face(sw, sh, scale)

        screen.blit(self._face, (0, 0))

        cx, cy = sw // 2, int(sh * 0.35)
        base_r = min(sw, sh) // 4
        if base_r < 30:
            base_r = 30

        total_ms = pygame.time.get_ticks()
        total_sec = total_ms / 1000.0
        second = total_sec % 60
        minute = (total_sec / 60) % 60
        hour = (total_sec / 3600) % 12

        sec_angle = math.radians(second * 6 - 90)
        sec_len = base_r - max(10, int(20 * scale))
        sec_x = cx + int(math.cos(sec_angle) * sec_len)
        sec_y = cy + int(math.sin(sec_angle) * sec_len)
        pygame.draw.line(screen, (*GOLD_BRIGHT, 50), (cx, cy), (sec_x, sec_y), 1)

        min_angle = math.radians(minute * 6 + second * 0.1 - 90)
        min_len = base_r - max(20, int(40 * scale))
        min_x = cx + int(math.cos(min_angle) * min_len)
        min_y = cy + int(math.sin(min_angle) * min_len)
        pygame.draw.line(screen, (*GOLD, 70), (cx, cy), (min_x, min_y), 3)

        hour_angle = math.radians(hour * 30 + minute * 0.5 - 90)
        hour_len = base_r - max(35, int(70 * scale))
        hour_x = cx + int(math.cos(hour_angle) * hour_len)
        hour_y = cy + int(math.sin(hour_angle) * hour_len)
        pygame.draw.line(screen, (*GOLD_BRIGHT, 80), (cx, cy), (hour_x, hour_y), 4)

        cap_r = max(2, int(4 * scale))
        s = pygame.Surface((cap_r * 2, cap_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*GOLD_BRIGHT, 80), (cap_r, cap_r), cap_r)
        screen.blit(s, (cx - cap_r, cy - cap_r))
