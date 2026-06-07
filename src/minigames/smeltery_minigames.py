"""
Smeltery minigames: small skill challenges that fire when a batch in
the coke oven or blast furnace finishes smelting.

Three new challenges are added on top of the workbench Tempering game:

* **Tending the Fire** -- vertical bellows-hold challenge for the coke
  oven. Player must keep a heat cursor inside a target zone while
  holding SPACE / the mouse button.
* **Iron Forge** -- three-strike horizontal timing challenge for the
  iron-ore -> iron-ingot batch.  Graded Bullseye / Good / Miss.
* **Quench** -- the toughest challenge.  Sweeping cursor that narrows
  as it travels; player must click inside the visible sweet spot
  for the iron-ingot -> steel-ingot batch.

All three are skippable via ESC or a Skip button.  The base batch
output is unaffected; the minigame only grants (or denies) a bonus
yield and an XP multiplier.
"""

import math
import random
import pygame

class ParticleSystem:
    def __init__(self):
        self.particles = []
        
    def spawn(self, x, y, count, color, speed_range, size_range, lifetime_range, gravity=0.0):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(*speed_range)
            life = random.uniform(*lifetime_range)
            size = random.uniform(*size_range)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append({
                "x": x, "y": y, "vx": vx, "vy": vy,
                "color": color, "size": size, "initial_size": size,
                "life": life, "max_life": life, "gravity": gravity
            })
            
    def update(self, dt):
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += p["gravity"] * dt
            p["life"] -= dt
        self.particles = [p for p in self.particles if p["life"] > 0]
        
    def draw(self, surface):
        if not self.particles:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for p in self.particles:
            progress = p["life"] / p["max_life"]
            current_size = max(0.1, p["initial_size"] * progress)
            alpha = int(255 * (progress ** 0.5))
            r, g, b = p["color"]
            pygame.draw.circle(overlay, (r, g, b, alpha), (int(p["x"]), int(p["y"])), int(current_size))
            pygame.draw.circle(overlay, (r, g, b, int(alpha * 0.3)), (int(p["x"]), int(p["y"])), int(current_size * 2.5))
        surface.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

class ScreenShake:
    def __init__(self):
        self.intensity = 0.0
        self.decay = 10.0
        self.offset_x = 0
        self.offset_y = 0
        
    def shake(self, intensity):
        self.intensity = max(self.intensity, intensity)
        
    def update(self, dt):
        if self.intensity > 0:
            self.offset_x = random.uniform(-self.intensity, self.intensity)
            self.offset_y = random.uniform(-self.intensity, self.intensity)
            self.intensity = max(0.0, self.intensity - self.decay * dt)
        else:
            self.offset_x = 0
            self.offset_y = 0

GLOBAL_PARTICLES = ParticleSystem()
GLOBAL_SHAKE = ScreenShake()

# ============================================================================
# Majestic Drawing Helpers
# ============================================================================

def _draw_majestic_background(surface):
    """Draw a rich atmospheric background with layered embers, heat glow,
    and a subtle vignette for all smeltery minigames."""
    import math, pygame, random
    w, h = surface.get_size()
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    time_ms = pygame.time.get_ticks()

    # 1. Deep gradient: dark purple-black at top -> smouldering amber at bottom
    for y in range(0, h, 2):
        ratio = y / float(h)
        sr = ratio * ratio * (3.0 - 2.0 * ratio)          # smoothstep
        r = int(10 + 58 * sr)
        g = int(2  + 20 * sr)
        b = int(14 + 10 * sr)
        a = int(225 - 25 * sr)
        col = (r, g, b, a)
        pygame.draw.line(overlay, col, (0, y), (w, y))
        if y + 1 < h:
            pygame.draw.line(overlay, col, (0, y + 1), (w, y + 1))

    # 2. Animated radial heat glows from below
    heat = pygame.Surface((w, h), pygame.SRCALPHA)
    p1 = (math.sin(time_ms * 0.0008) + 1) * 0.5
    p2 = (math.sin(time_ms * 0.0013 + 1.5) + 1) * 0.5
    p3 = (math.sin(time_ms * 0.0018 + 3.0) + 1) * 0.5

    pygame.draw.circle(heat, (180, 60, 15, int(40 + 30 * p1)),
                       (int(w * 0.5), int(h * 1.15)), int(h * (0.52 + 0.1 * p1)))
    pygame.draw.circle(heat, (120, 30, 10, int(30 + 22 * p2)),
                       (int(w * 0.18), int(h * 0.92)), int(h * (0.38 + 0.08 * p2)))
    pygame.draw.circle(heat, (75, 12, 110, int(25 + 18 * p3)),
                       (int(w * 0.82), int(h * 0.96)), int(h * (0.42 + 0.1 * p3)))
    pygame.draw.circle(heat, (255, 90, 18, int(18 + 12 * p1)),
                       (int(w * 0.5), int(h * 1.05)), int(h * (0.28 + 0.05 * p1)))
    overlay.blit(heat, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    # 3. Ember layers (three depths for parallax)
    # Far – tiny, slow, dim
    for i in range(45):
        seed = i * 3571
        spd = 7 + (seed % 14)
        ex = (seed * 19) % w
        ey = h - ((time_ms / 1000.0 * spd + seed * 83) % (h + 160))
        wb = math.sin(time_ms * 0.001 + i * 0.7) * 14
        al = int(abs(math.sin(time_ms * 0.0015 + i * 0.5)) * 90) + 25
        pygame.draw.circle(overlay, (255, int(110 + 80 * math.sin(i * 0.3)), 35, al),
                           (int(ex + wb), int(ey)), 1)
    # Mid
    for i in range(35):
        seed = i * 7331
        spd = 16 + (seed % 26)
        ex = (seed * 19) % w
        ey = h - ((time_ms / 1000.0 * spd + seed * 83) % (h + 100))
        wb = math.sin(time_ms * 0.002 + i) * 22
        al = int(abs(math.sin(time_ms * 0.0025 + i)) * 140) + 55
        pygame.draw.circle(overlay, (255, int(140 + 110 * math.sin(i)), 48, al),
                           (int(ex + wb), int(ey)), 2)
        pygame.draw.circle(overlay, (255, 110, 28, al // 4),
                           (int(ex + wb), int(ey)), 5)
    # Near – large, fast, bright
    for i in range(22):
        seed = i * 11213
        spd = 32 + (seed % 42)
        ex = (seed * 19) % w
        ey = h - ((time_ms / 1000.0 * spd + seed * 83) % (h + 80))
        wb = math.sin(time_ms * 0.003 + i * 1.3) * 34
        al = min(255, int(abs(math.sin(time_ms * 0.003 + i)) * 200) + 50)
        pygame.draw.circle(overlay, (255, int(175 + 80 * math.sin(i * 0.7)), 55, al),
                           (int(ex + wb), int(ey)), 3)
        pygame.draw.circle(overlay, (255, 150, 38, al // 3),
                           (int(ex + wb), int(ey)), 9)

    # 4. Soft vignette
    vig = pygame.Surface((w, h), pygame.SRCALPHA)
    edge = max(18, int(min(w, h) * 0.10))
    for i in range(edge):
        a = int(((edge - i) / edge) ** 2 * 50)
        pygame.draw.line(vig, (0, 0, 0, a), (0, i), (w, i))
        pygame.draw.line(vig, (0, 0, 0, a), (0, h - 1 - i), (w, h - 1 - i))
        pygame.draw.line(vig, (0, 0, 0, a), (i, 0), (i, h))
        pygame.draw.line(vig, (0, 0, 0, a), (w - 1 - i, 0), (w - 1 - i, h))
    overlay.blit(vig, (0, 0))

    surface.blit(overlay, (0, 0))


import src.config as cfg
from src.core.logger import logger

# ============================================================================
# Palette
# ============================================================================
ANVIL_BG          = (28, 22, 18)
ANVIL_BORDER      = (90, 60, 30)
ANVIL_BORDER_LIGHT = (140, 100, 50)
ANVIL_GLOW        = (180, 90, 30)

BAR_BG            = (50, 35, 22)
BAR_MISS          = (140, 40, 40)
BAR_GOOD          = (170, 170, 175)
BAR_BULLSEYE      = (255, 200, 60)
BAR_CURSOR        = (245, 245, 245)
BAR_CURSOR_GLOW   = (255, 255, 200)

TEXT_LIGHT        = (235, 225, 200)
TEXT_DIM          = (160, 145, 120)
TEXT_GOLD         = (255, 200, 90)
TEXT_BAD          = (220, 80, 80)
TEXT_GOOD         = (120, 220, 130)

BUTTON_BG         = (60, 40, 25)
BUTTON_HOVER      = (95, 65, 35)
BUTTON_BORDER     = (160, 110, 50)

# Extra majestic palette
ORNAMENT_GOLD     = (200, 160, 75)
GLOW_WARM         = (255, 140, 40)
GLOW_COOL         = (100, 180, 255)
BAR_MISS_GLOW     = (200, 60, 50)
BAR_GOOD_GLOW     = (210, 210, 220)
BAR_BULL_GLOW     = (255, 220, 100)


# ============================================================================
# Button
# ============================================================================

def _draw_button(surface, font, rect, text, hovered=False, text_color=None):
    """Draw a button with shadow, optional hover glow, and gold border."""
    import math
    time_ms = pygame.time.get_ticks()

    # Drop shadow
    sh = pygame.Surface((rect.width + 6, rect.height + 6), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 70), sh.get_rect(), border_radius=10)
    surface.blit(sh, (rect.x - 3, rect.y + 4))

    # Background
    bg = BUTTON_HOVER if hovered else BUTTON_BG
    pygame.draw.rect(surface, bg, rect, border_radius=8)

    if hovered:
        # Animated glow border
        pulse = int(abs(math.sin(time_ms * 0.005)) * 50 + 130)
        glow_surf = pygame.Surface((rect.width + 8, rect.height + 8), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (255, 200, 80, pulse), glow_surf.get_rect(),
                         width=3, border_radius=10)
        surface.blit(glow_surf, (rect.x - 4, rect.y - 4))

    # Gold border
    pygame.draw.rect(surface, BUTTON_BORDER, rect, width=2, border_radius=8)

    # Text
    tc = text_color if text_color else TEXT_LIGHT
    if hovered:
        tg = font.render(text, True, (255, 230, 150))
        tg.set_alpha(70)
        surface.blit(tg, (rect.centerx - tg.get_width() // 2 + 1,
                          rect.centery - tg.get_height() // 2 + 1))
    txt_surf = font.render(text, True, tc)
    surface.blit(txt_surf, txt_surf.get_rect(center=rect.center))


# ============================================================================
# Panel (glassmorphism with ornaments)
# ============================================================================

def _draw_panel(surface, panel_rect, title, subtitle, fonts, majestic=True):
    """Draw a majestic glassmorphism panel with corner ornaments,
    animated shimmer divider, and warm ambient glows."""
    import math

    # 1. Deep progressive drop shadow
    for i in range(7):
        off = (i + 1) * 4
        sh_surf = pygame.Surface(
            (panel_rect.width + off * 2, panel_rect.height + off * 2), pygame.SRCALPHA)
        a = max(0, 55 - i * 8)
        pygame.draw.rect(sh_surf, (0, 0, 0, a), sh_surf.get_rect(), border_radius=28)
        surface.blit(sh_surf, (panel_rect.x - off, panel_rect.y - off + 10))

    # 2. Frosted glass base
    panel_surf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (16, 18, 26, 218), panel_surf.get_rect(), border_radius=24)
    # Subtle top-down light
    for y in range(0, panel_rect.height, 2):
        ratio = y / float(panel_rect.height)
        oa = int(22 * (1 - ratio))
        line = (255, 255, 255, oa)
        pygame.draw.line(panel_surf, line, (0, y), (panel_rect.width, y))
        if y + 1 < panel_rect.height:
            pygame.draw.line(panel_surf, line, (0, y + 1), (panel_rect.width, y + 1))

    # 3. Majestic warm glow
    if majestic:
        time_ms = pygame.time.get_ticks()
        pulse = (math.sin(time_ms * 0.003) + 1) * 0.5

        # Bottom warm gradient
        glow_bot = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        start_y = int(panel_rect.height * 0.25)
        for y in range(start_y, panel_rect.height):
            frac = (y - start_y) / float(panel_rect.height - start_y)
            a = int(frac * (95 + 55 * pulse))
            pygame.draw.line(glow_bot, (255, 95, 22, a), (0, y), (panel_rect.width, y))
        panel_surf.blit(glow_bot, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # Corner accent glows
        cr = int(min(panel_rect.width, panel_rect.height) * 0.35)
        cga = int(28 + 16 * pulse)
        corner_sf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        pygame.draw.circle(corner_sf, (200, 75, 18, cga), (0, panel_rect.height), cr)
        pygame.draw.circle(corner_sf, (200, 75, 18, cga), (panel_rect.width, panel_rect.height), cr)
        panel_surf.blit(corner_sf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # Floating sparks
        for i in range(18):
            seed = i * 4321
            spd = 11 + (seed % 20)
            sx = (seed * 37) % panel_rect.width
            sy = panel_rect.height - (
                (time_ms / 1000.0 * spd + seed * 73) % (panel_rect.height * 0.52))
            swb = math.sin(time_ms * 0.003 + i) * 8
            sa = int(abs(math.sin(time_ms * 0.004 + i)) * 155)
            pygame.draw.circle(panel_surf, (255, 165, 65, sa),
                               (int(sx + swb), int(sy)), 1)

    surface.blit(panel_surf, panel_rect.topleft)

    # 4. Metallic double border
    pygame.draw.rect(surface, (140, 100, 60), panel_rect, width=2, border_radius=24)
    inner = panel_rect.inflate(-16, -16)
    pygame.draw.rect(surface, (42, 36, 30), inner, width=1, border_radius=18)

    # 5. Animated top highlight shimmer
    if majestic:
        time_ms = pygame.time.get_ticks()
        shim_frac = (math.sin(time_ms * 0.002) + 1) * 0.5
        shim_x = int(panel_rect.x + panel_rect.width * 0.2 +
                     shim_frac * panel_rect.width * 0.6)
        shim_w = int(panel_rect.width * 0.14)
        shim_sf = pygame.Surface((shim_w, 3), pygame.SRCALPHA)
        for px in range(shim_w):
            pxr = 1.0 - abs(px / max(1, shim_w) * 2 - 1)
            a = int(pxr * 190)
            pygame.draw.line(shim_sf, (255, 218, 155, a), (px, 0), (px, 1))
            pygame.draw.line(shim_sf, (255, 218, 155, max(0, a - 50)), (px, 1), (px, 2))
        surface.blit(shim_sf, (shim_x - shim_w // 2, panel_rect.y + 2))

    # 6. Corner ornaments (gold L-brackets)
    orn_sz = 14
    orn_c = ORNAMENT_GOLD
    orn_w = 2
    px, py = panel_rect.x, panel_rect.y
    rx, ry = panel_rect.right, panel_rect.bottom
    # Top-left
    pygame.draw.line(surface, orn_c, (px + 6, py + 6), (px + 6, py + 6 + orn_sz), orn_w)
    pygame.draw.line(surface, orn_c, (px + 6, py + 6), (px + 6 + orn_sz, py + 6), orn_w)
    # Top-right
    pygame.draw.line(surface, orn_c, (rx - 6, py + 6), (rx - 6, py + 6 + orn_sz), orn_w)
    pygame.draw.line(surface, orn_c, (rx - 6, py + 6), (rx - 6 - orn_sz, py + 6), orn_w)
    # Bottom-left
    pygame.draw.line(surface, orn_c, (px + 6, ry - 6), (px + 6, ry - 6 - orn_sz), orn_w)
    pygame.draw.line(surface, orn_c, (px + 6, ry - 6), (px + 6 + orn_sz, ry - 6), orn_w)
    # Bottom-right
    pygame.draw.line(surface, orn_c, (rx - 6, ry - 6), (rx - 6, ry - 6 - orn_sz), orn_w)
    pygame.draw.line(surface, orn_c, (rx - 6, ry - 6), (rx - 6 - orn_sz, ry - 6), orn_w)

    # 7. Typography & divider
    font_title, font_sub = fonts

    # Title shadow + glow + main
    ts = font_title.render(title, True, (0, 0, 0))
    surface.blit(ts, (panel_rect.centerx - ts.get_width() // 2 + 2, panel_rect.y + 26))
    tg = font_title.render(title, True, (255, 180, 60))
    tg.set_alpha(55)
    surface.blit(tg, (panel_rect.centerx - tg.get_width() // 2 - 1, panel_rect.y + 23))
    tt = font_title.render(title, True, (255, 225, 140))
    surface.blit(tt, (panel_rect.centerx - tt.get_width() // 2, panel_rect.y + 24))

    # Animated glowing divider with diamond
    div_y = panel_rect.y + 24 + tt.get_height() + 12
    div_w = int(panel_rect.width * 0.62)
    div_x = panel_rect.centerx - div_w // 2

    if majestic:
        time_ms = pygame.time.get_ticks()
        div_sf = pygame.Surface((div_w, 3), pygame.SRCALPHA)
        pygame.draw.line(div_sf, (130, 95, 55, 200), (0, 1), (div_w, 1))
        shimmer_pos = int((math.sin(time_ms * 0.003) + 1) * 0.5 * div_w)
        for dx in range(-22, 23):
            px = shimmer_pos + dx
            if 0 <= px < div_w:
                intensity = 1.0 - abs(dx) / 22
                a = int(intensity * 145)
                pygame.draw.line(div_sf, (255, 218, 135, a), (px, 0), (px, 2))
        surface.blit(div_sf, (div_x, div_y))
    else:
        pygame.draw.line(surface, (130, 95, 55), (div_x, div_y + 1),
                         (div_x + div_w, div_y + 1), 1)

    # Diamond ornament
    dcx = panel_rect.centerx
    dcy = div_y + 1
    ds = 6
    diamond = [(dcx, dcy - ds), (dcx + ds, dcy), (dcx, dcy + ds), (dcx - ds, dcy)]
    pygame.draw.polygon(surface, (255, 225, 140), diamond)
    pygame.draw.polygon(surface, (255, 255, 200), diamond, 1)
    pygame.draw.circle(surface, (255, 255, 255), (dcx, dcy), 2)

    # Subtitle
    if subtitle:
        ss = font_sub.render(subtitle, True, (0, 0, 0))
        surface.blit(ss, (panel_rect.centerx - ss.get_width() // 2 + 1, div_y + 19))
        st = font_sub.render(subtitle, True, (195, 185, 170))
        surface.blit(st, (panel_rect.centerx - st.get_width() // 2, div_y + 18))


# ============================================================================
# Reusable visual building blocks
# ============================================================================

def _draw_zone_bar(surface, rect, zones, cursor_x=None, cursor_active=False, time_ms=0):
    """Draw a majestic horizontal bar with gradient-filled zones,
    glowing boundaries, and an animated shimmer.

    *zones* is a list of ``(start_frac, end_frac, base_color, glow_color)``
    tuples (0.0-1.0 fractions of bar width).
    """
    bw, bh = rect.width, rect.height

    # Base
    pygame.draw.rect(surface, BAR_BG, rect, border_radius=8)

    # Zone fills with gradient
    for start_f, end_f, base_c, glow_c in zones:
        zx = int(rect.x + bw * start_f)
        zw = max(2, int(bw * (end_f - start_f)))
        zone_rect = pygame.Rect(zx, rect.y, zw, bh)

        # Gradient fill (top lighter, bottom darker)
        grad = pygame.Surface(zone_rect.size, pygame.SRCALPHA)
        for yy in range(bh):
            ratio = yy / max(1, bh)
            r = min(255, int(base_c[0] * (0.7 + 0.3 * (1 - ratio))))
            g = min(255, int(base_c[1] * (0.7 + 0.3 * (1 - ratio))))
            b = min(255, int(base_c[2] * (0.7 + 0.3 * (1 - ratio))))
            pygame.draw.line(grad, (r, g, b, 255), (0, yy), (zw, yy))
        surface.blit(grad, zone_rect.topleft)

        # Glow at zone boundaries (vertical glow lines)
        glow_line = pygame.Surface((2, bh), pygame.SRCALPHA)
        for yy in range(bh):
            a = int(100 + 40 * math.sin(yy * 0.1 + time_ms * 0.003))
            pygame.draw.line(glow_line, (*glow_c, min(255, a)), (0, yy), (1, yy))
        surface.blit(glow_line, (zx, rect.y))
        if zw > 4:
            surface.blit(glow_line, (zx + zw - 2, rect.y))

    # Animated shimmer sweep
    if time_ms:
        shim_x = int((math.sin(time_ms * 0.0018) + 1) * 0.5 * bw)
        shim_sf = pygame.Surface((max(2, int(bw * 0.06)), bh - 4), pygame.SRCALPHA)
        for px in range(shim_sf.get_width()):
            pxr = 1.0 - abs(px / max(1, shim_sf.get_width()) * 2 - 1)
            a = int(pxr * 55)
            pygame.draw.line(shim_sf, (255, 255, 230, a), (px, 0), (px, shim_sf.get_height()))
        surface.blit(shim_sf, (rect.x + shim_x - shim_sf.get_width() // 2, rect.y + 2))

    # Border
    pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, rect, width=2, border_radius=8)

    # Cursor
    if cursor_x is not None:
        cx = int(cursor_x)
        ch = bh + 14
        ct = rect.y - 7
        c_rect = pygame.Rect(cx - 3, ct, 6, ch)
        # Glow behind cursor
        glow_pulse = int(abs(math.sin(time_ms * 0.006)) * 40 + 80) if time_ms else 120
        c_glow = pygame.Surface((14, ch + 4), pygame.SRCALPHA)
        pygame.draw.rect(c_glow, (*BAR_CURSOR_GLOW, glow_pulse), c_glow.get_rect(), border_radius=4)
        surface.blit(c_glow, (cx - 7, ct - 2))
        # Cursor line
        c_color = BAR_BULLSEYE if cursor_active else BAR_CURSOR
        pygame.draw.rect(surface, c_color, c_rect, border_radius=2)
        # Top diamond
        pygame.draw.polygon(surface, BAR_CURSOR_GLOW,
                            [(cx, ct - 6), (cx + 4, ct - 2), (cx, ct + 2), (cx - 4, ct - 2)])


def _draw_zone_gauge(surface, rect, value, zone_center, zone_width,
                     fill=0.0, fill_target=1.0, warning=False, time_ms=0):
    """Draw a majestic vertical gauge with gradient fill, target zone,
    and animated effects."""
    gw, gh = rect.width, rect.height

    # Base
    pygame.draw.rect(surface, BAR_BG, rect, border_radius=8)

    # Gradient fill background (cool blue -> warm based on value)
    grad = pygame.Surface((gw, gh), pygame.SRCALPHA)
    for yy in range(gh):
        ratio = yy / max(1, gh)
        # Cool at bottom, warm at top
        r = int(30 + 60 * ratio)
        g = int(40 + 30 * (1 - ratio))
        b = int(80 - 30 * ratio)
        pygame.draw.line(grad, (r, g, b, 80), (0, yy), (gw, yy))
    surface.blit(grad, rect.topleft)

    # Target zone
    zone_low = zone_center - zone_width * 0.5
    zone_high = zone_center + zone_width * 0.5
    zy1 = int(rect.bottom - zone_high * gh)
    zy2 = int(rect.bottom - zone_low * gh)
    zone_h = max(4, zy2 - zy1)

    # Zone glow
    zone_glow = pygame.Surface((gw + 8, zone_h + 8), pygame.SRCALPHA)
    pulse = int(abs(math.sin(time_ms * 0.004)) * 35 + 65) if time_ms else 80
    pygame.draw.rect(zone_glow, (*BAR_BULL_GLOW, pulse), zone_glow.get_rect(), border_radius=6)
    surface.blit(zone_glow, (rect.x - 4, zy1 - 4))

    # Zone fill
    zone_rect = pygame.Rect(rect.x, zy1, gw, zone_h)
    pygame.draw.rect(surface, BAR_BULLSEYE, zone_rect, border_radius=4)

    # Perfect center line
    perfect_y = int(rect.bottom - zone_center * gh)
    pygame.draw.line(surface, (255, 240, 180),
                     (rect.x + 2, perfect_y), (rect.right - 2, perfect_y), 1)

    # Progress fill
    if fill > 0:
        fill_h = max(1, int(gh * min(1.0, fill / max(0.01, fill_target))))
        fill_rect = pygame.Rect(rect.x + 2, rect.bottom - fill_h - 1, gw - 4, fill_h)
        # Gradient fill
        fg = pygame.Surface(fill_rect.size, pygame.SRCALPHA)
        for yy in range(fill_rect.height):
            ratio = yy / max(1, fill_rect.height)
            r = int(80 + 60 * (1 - ratio))
            g = int(200 + 30 * (1 - ratio))
            b = int(220 - 40 * (1 - ratio))
            pygame.draw.line(fg, (r, g, b, 220), (0, yy), (fill_rect.width, yy))
        surface.blit(fg, fill_rect.topleft)

    # Border
    pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, rect, width=2, border_radius=8)

    # Pressure cursor
    cy = rect.bottom - int(value * gh) - 4
    cursor_h = 10
    c_rect = pygame.Rect(rect.x - 6, cy, gw + 12, cursor_h)
    # Glow
    if time_ms:
        gp = int(abs(math.sin(time_ms * 0.006)) * 30 + 60)
    else:
        gp = 80
    c_glow = pygame.Surface((gw + 18, cursor_h + 6), pygame.SRCALPHA)
    cursor_color = (60, 200, 60) if value > 0.25 else (200, 50, 30)
    pygame.draw.rect(c_glow, (*cursor_color, gp), c_glow.get_rect(), border_radius=5)
    surface.blit(c_glow, (rect.x - 9, cy - 3))
    # Cursor body
    pygame.draw.rect(surface, cursor_color, c_rect, border_radius=3)
    pygame.draw.rect(surface, BAR_CURSOR, c_rect, width=1, border_radius=3)

    # Warning pulse
    if warning and time_ms:
        wp = int(abs(math.sin(time_ms * 0.008)) * 180)
        warn_sf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(warn_sf, (220, 50, 30, wp), warn_sf.get_rect(), width=3, border_radius=8)
        surface.blit(warn_sf, rect.topleft)


def _draw_result_overlay(surface, panel_rect, outcome, outcome_color,
                         bonus_text, bonus_color, font_large, font_medium,
                         time_ms=0, bonus_icons=0):
    """Draw a dramatic result display with glow, ornaments, and text."""
    pr = panel_rect

    # Outcome text with glow
    out_glow = font_large.render(outcome, True, outcome_color)
    out_glow.set_alpha(70)
    surface.blit(out_glow, (pr.centerx - out_glow.get_width() // 2 + 2, pr.y + 118))
    out_surf = font_large.render(outcome, True, outcome_color)
    surface.blit(out_surf, (pr.centerx - out_surf.get_width() // 2, pr.y + 116))

    # Decorative lines flanking the outcome
    line_w = max(10, (pr.width - out_surf.get_width()) // 2 - 40)
    line_y = pr.y + 116 + out_surf.get_height() // 2
    # Left line
    lx1 = pr.centerx - out_surf.get_width() // 2 - 14
    lx0 = lx1 - line_w
    pygame.draw.line(surface, (140, 100, 60), (lx0, line_y), (lx1, line_y), 1)
    # Right line
    rx1 = pr.centerx + out_surf.get_width() // 2 + 14
    rx0 = rx1 + line_w
    pygame.draw.line(surface, (140, 100, 60), (rx1, line_y), (rx0, line_y), 1)
    # Small diamonds at line ends
    for dx in [lx0, rx0]:
        ds = 3
        pygame.draw.polygon(surface, ORNAMENT_GOLD,
                            [(dx, line_y - ds), (dx + ds, line_y),
                             (dx, line_y + ds), (dx - ds, line_y)])

    # Bonus text
    if bonus_text:
        bt = font_medium.render(bonus_text, True, bonus_color)
        surface.blit(bt, (pr.centerx - bt.get_width() // 2, pr.y + 130 + out_surf.get_height() + 8))

    # Bonus icons (small glowing circles)
    if bonus_icons > 0:
        icon_y = pr.y + 130 + out_surf.get_height() + 8
        if bonus_text:
            icon_y += font_medium.size(bonus_text)[1] + 6
        icon_start_x = pr.centerx - bonus_icons * 12
        for i in range(bonus_icons):
            ix = icon_start_x + i * 24
            # Glow
            igr = pygame.Surface((14, 14), pygame.SRCALPHA)
            pygame.draw.circle(igr, (255, 200, 80, 80), (7, 7), 7)
            surface.blit(igr, (ix - 1, icon_y - 1))
            pygame.draw.circle(surface, BAR_BULLSEYE, (ix + 5, icon_y + 5), 5)
            pygame.draw.circle(surface, (255, 240, 180), (ix + 5, icon_y + 5), 5, 1)


def _draw_strike_pips(surface, center_x, y, results, num_strikes, font_small):
    """Draw ornate strike-result indicators (diamond pips)."""
    pip_size = 14
    gap = 12
    total_w = num_strikes * pip_size * 2 + (num_strikes - 1) * gap
    start_x = center_x - total_w // 2

    for i in range(num_strikes):
        cx = start_x + i * (pip_size * 2 + gap) + pip_size
        cy = y + pip_size

        if i < len(results):
            zone = results[i]
            if zone in ("bullseye", "perfect"):
                fill_c = BAR_BULLSEYE
                glow_c = BAR_BULL_GLOW
                letter = "B" if zone == "bullseye" else "P"
            elif zone == "good":
                fill_c = BAR_GOOD
                glow_c = BAR_GOOD_GLOW
                letter = "G"
            else:
                fill_c = BAR_MISS
                glow_c = BAR_MISS_GLOW
                letter = "X"

            # Glow behind
            pg = pygame.Surface((pip_size * 2 + 4, pip_size * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(pg, (*glow_c, 60), (pip_size + 2, pip_size + 2), pip_size + 2)
            surface.blit(pg, (cx - pip_size - 2, cy - pip_size - 2))

            # Diamond shape
            points = [(cx, cy - pip_size), (cx + pip_size, cy),
                      (cx, cy + pip_size), (cx - pip_size, cy)]
            pygame.draw.polygon(surface, fill_c, points)
            pygame.draw.polygon(surface, (255, 255, 240), points, 1)

            # Letter
            t = font_small.render(letter, True, (255, 255, 255))
            surface.blit(t, t.get_rect(center=(cx, cy)))
        else:
            # Empty pip (outline diamond)
            points = [(cx, cy - pip_size), (cx + pip_size, cy),
                      (cx, cy + pip_size), (cx - pip_size, cy)]
            pygame.draw.polygon(surface, ANVIL_BG, points)
            pygame.draw.polygon(surface, ANVIL_BORDER, points, 2)


def _draw_orb_ingot(surface, cx, cy, radius, color, time_ms=0):
    """Draw a majestic glowing orb/ingot with multi-layer glow,
    specular highlight, and animated ring."""
    # Outer ambient glow
    glow_r = int(radius * 2.2)
    glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
    for ir in range(glow_r, 0, -4):
        frac = ir / glow_r
        a = int((1.0 - frac) * 50)
        pygame.draw.circle(glow, (*color, a), (glow_r, glow_r), ir)
    surface.blit(glow, (cx - glow_r, cy - glow_r))

    # Pulsing ring
    if time_ms:
        ring_r = int(radius * 1.3 + 5 * math.sin(time_ms * 0.004))
        ring_a = int(abs(math.sin(time_ms * 0.003)) * 80 + 40)
        ring_sf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(ring_sf, (*color, ring_a), (ring_r + 2, ring_r + 2), ring_r, 2)
        surface.blit(ring_sf, (cx - ring_r - 2, cy - ring_r - 2))

    # Main body
    pygame.draw.circle(surface, color, (cx, cy), radius)

    # Gradient overlay for depth
    depth = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for ir in range(radius, 0, -2):
        frac = ir / radius
        a = int((1.0 - frac) * 100)
        pygame.draw.circle(depth, (0, 0, 0, a), (radius, radius), ir)
    surface.blit(depth, (cx - radius, cy - radius))

    # Re-draw the main circle on top (so the gradient only darkens edges)
    pygame.draw.circle(surface, color, (cx, cy), radius)

    # Border
    pygame.draw.circle(surface, ANVIL_BORDER_LIGHT, (cx, cy), radius, 3)

    # Specular highlight (top-left)
    hx = cx - radius // 3
    hy = cy - radius // 3
    highlight = (min(255, color[0] + 90), min(255, color[1] + 90), min(255, color[2] + 90))
    pygame.draw.circle(surface, highlight, (hx, hy), radius // 3)

    # Bright specular dot
    pygame.draw.circle(surface, (255, 255, 255), (hx - 2, hy - 2), radius // 7)


# ============================================================================
# Minigame chain labels
# ============================================================================

CHAIN_STEP_NAMES = {
    "tending": "Tending the Fire",
    "forge": "Forging",
    "quench": "Quenching",
    "bellows": "Bellows Pump",
    "pattern": "Pattern Hammer",
    "temper": "Tempering",
}

CHAIN_TITLES = {
    ("forge", "quench"): "Steel Forging",
    ("forge", "pattern", "temper"): "Damascus Forging",
    ("bellows", "temper"): "Steel Tempering",
}


# ===========================================================================
# Tending the Fire
# ===========================================================================

class TendingFireMinigame:
    PHASE_INTRO = "intro"
    PHASE_ACTIVE = "active"
    PHASE_RESULT = "result"

    BAR_WIDTH = 26
    CURSOR_FREQ = 1.6
    GOOD_ZONE = 0.18
    PERFECT_ZONE = 0.08
    HOLD_TARGET = 1.0
    OUT_OF_ZONE_TOLERANCE = 0.45

    def __init__(self, app, *, recipe_name="Coke Oven",
                 hold_target=None, on_close=None, smelting_level=1):
        self.app = app
        self.on_close = on_close
        self.recipe_name = recipe_name
        self.smelting_level = max(1, int(smelting_level))
        if hold_target is not None:
            self.HOLD_TARGET = float(hold_target)

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        self.font_title  = cfg.get_font(max(12, int(40 * cfg.ui_scale())))
        self.font_large  = cfg.get_font(max(11, int(30 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(22 * cfg.ui_scale())))
        self.font_small  = cfg.get_font(max(8,  int(18 * cfg.ui_scale())))

        panel_w = int(sw * 0.62)
        panel_h = int(sh * 0.58)
        self.panel_rect = pygame.Rect(
            (sw - panel_w) // 2,
            (sh - panel_h) // 2,
            panel_w, panel_h,
        )
        bar_h = int(panel_h * 0.62)
        bar_x = self.panel_rect.centerx - self.BAR_WIDTH // 2
        bar_y = self.panel_rect.y + int(panel_h * 0.30)
        self.bar_rect = pygame.Rect(bar_x, bar_y, self.BAR_WIDTH, bar_h)

        self.phase = self.PHASE_INTRO
        self.heat = 0.5
        self.hold_charge = 0.0
        self.out_of_zone_time = 0.0
        self._intro_timer = 1.0
        self._result_timer = 0.0
        self._outcome = ""
        self._outcome_color = TEXT_LIGHT
        self._xp_multiplier = 1.0
        self._bonus_amount = 0
        self._holding = False
        self._btn_skip = None

    def _finalise(self, success, perfect):
        if perfect:
            self._bonus_amount = 1
            self._xp_multiplier = 2.0
            self._outcome = "PERFECT TEMPER!"
            self._outcome_color = TEXT_GOLD
        elif success:
            self._bonus_amount = 1
            self._xp_multiplier = 1.5
            self._outcome = "Clean burn."
            self._outcome_color = TEXT_GOOD
        else:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "The fire died down..."
            self._outcome_color = TEXT_BAD
        self._result_timer = 2.2
        self.phase = self.PHASE_RESULT

    def _close(self):
        if callable(self.on_close):
            try:
                self.on_close(self._outcome, self._bonus_amount, self._xp_multiplier)
            except Exception as exc:
                logger.warning("smeltery minigame on_close failed: %s", exc)
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._bonus_amount = 0
                self._xp_multiplier = 1.0
                self._outcome = "Skipped"
                self._close()
                return
            if self.phase == self.PHASE_ACTIVE and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._holding = True
                return
        if event.type == pygame.KEYUP:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._holding = False
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.phase == self.PHASE_INTRO:
                self.phase = self.PHASE_ACTIVE
                return
            if self.phase == self.PHASE_ACTIVE:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._bonus_amount = 0
                    self._xp_multiplier = 1.0
                    self._outcome = "Skipped"
                    self._close()
                    return
                self._holding = True
                return
            if self.phase == self.PHASE_RESULT:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._close()
                    return
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._holding = False
            return

    def update(self, dt):
        GLOBAL_PARTICLES.update(dt)
        GLOBAL_SHAKE.update(dt)
        if self.phase == self.PHASE_INTRO:
            self._intro_timer -= dt
            if self._intro_timer <= 0.0:
                self.phase = self.PHASE_ACTIVE
            return
        if self.phase == self.PHASE_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._close()
            return
        if self.phase != self.PHASE_ACTIVE:
            return

        phase = pygame.time.get_ticks() * 0.001 * self.CURSOR_FREQ
        target_heat = 0.5 + 0.45 * math.sin(phase * math.tau)

        if self._holding:
            self.heat += (0.5 - self.heat) * min(1.0, 4.0 * dt)
        else:
            self.heat += (target_heat - self.heat) * min(1.0, 2.5 * dt)

        in_perfect = abs(self.heat - 0.5) < (self.PERFECT_ZONE * 0.5)
        in_good    = abs(self.heat - 0.5) < (self.GOOD_ZONE * 0.5)

        if in_good:
            self.out_of_zone_time = 0.0
            if self._holding:
                charge = dt * (2.5 if in_perfect else 1.4)
                self.hold_charge = min(self.HOLD_TARGET, self.hold_charge + charge)
                if in_perfect and self.hold_charge >= self.HOLD_TARGET:
                    GLOBAL_PARTICLES.spawn(self.bar_rect.centerx, self.bar_rect.centery,
                                           100, (255, 180, 50), (200, 600), (4, 10),
                                           (0.5, 1.5), gravity=-100)
                    GLOBAL_SHAKE.shake(25)
                    self._finalise(success=True, perfect=True)
                    return
            else:
                self.hold_charge = max(0.0, self.hold_charge - dt * 0.3)
        else:
            self.out_of_zone_time += dt
            self.hold_charge = max(0.0, self.hold_charge - dt * 1.5)
            if self.out_of_zone_time > self.OUT_OF_ZONE_TOLERANCE and self._holding:
                self._finalise(success=False, perfect=False)
                return

    def draw(self, surface):
        _draw_majestic_background(surface)

        _draw_panel(
            surface, self.panel_rect,
            "Tending the Fire",
            "Hold the bellows to keep the heat in the gold zone.",
            (self.font_title, self.font_small),
        )
        pr = self.panel_rect
        mouse_pos = pygame.mouse.get_pos()
        time_ms = pygame.time.get_ticks()

        br = self.bar_rect
        bw, bh = br.width, br.height

        # Vertical gauge background
        pygame.draw.rect(surface, BAR_BG, br, border_radius=8)

        # Gradient fill behind gauge (subtle cool-warm)
        gauge_grad = pygame.Surface((bw, bh), pygame.SRCALPHA)
        for yy in range(bh):
            ratio = yy / max(1, bh)
            a = int(40 + 20 * (1 - ratio))
            pygame.draw.line(gauge_grad, (80, 50, 30, a), (0, yy), (bw, yy))
        surface.blit(gauge_grad, br.topleft)

        # Good zone with glow
        good_h = int(bh * self.GOOD_ZONE)
        good = pygame.Rect(br.x, br.centery - good_h // 2, bw, good_h)
        # Glow around good zone
        gz_glow = pygame.Surface((bw + 10, good_h + 10), pygame.SRCALPHA)
        gp = int(abs(math.sin(time_ms * 0.004)) * 30 + 55)
        pygame.draw.rect(gz_glow, (*BAR_BULL_GLOW, gp), gz_glow.get_rect(), border_radius=8)
        surface.blit(gz_glow, (br.x - 5, good.y - 5))
        pygame.draw.rect(surface, BAR_BULLSEYE, good, border_radius=4)

        # Perfect zone (bright center)
        perfect_h = max(6, int(bh * self.PERFECT_ZONE))
        perfect = pygame.Rect(br.x, br.centery - perfect_h // 2, bw, perfect_h)
        # Glow on perfect zone
        pz_glow = pygame.Surface((bw + 6, perfect_h + 6), pygame.SRCALPHA)
        pygame.draw.rect(pz_glow, (255, 240, 140, 70), pz_glow.get_rect(), border_radius=6)
        surface.blit(pz_glow, (br.x - 3, perfect.y - 3))
        pygame.draw.rect(surface, (255, 235, 130), perfect, border_radius=3)

        # Border
        pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, br, width=2, border_radius=8)

        # Heat cursor (animated)
        cursor_y = br.bottom - int(self.heat * bh) - 4
        cursor_h = 10
        cursor_rect = pygame.Rect(br.x - 4, cursor_y, bw + 8, cursor_h)
        # Cursor glow
        cg = pygame.Surface((bw + 16, cursor_h + 8), pygame.SRCALPHA)
        c_pulse = int(abs(math.sin(time_ms * 0.006)) * 30 + 50)
        cursor_color = (200, 60, 30) if not self._holding else (255, 200, 60)
        pygame.draw.rect(cg, (*cursor_color, c_pulse), cg.get_rect(), border_radius=6)
        surface.blit(cg, (br.x - 8, cursor_y - 4))
        pygame.draw.rect(surface, cursor_color, cursor_rect, border_radius=2)
        pygame.draw.rect(surface, BAR_CURSOR, cursor_rect, width=1, border_radius=2)

        # Charge meter on the side (enhanced)
        meter_w = 14
        meter_h = bh
        meter_x = br.right + 16
        meter_rect = pygame.Rect(meter_x, br.y, meter_w, meter_h)
        # Meter shadow
        ms = pygame.Surface((meter_w + 4, meter_h + 4), pygame.SRCALPHA)
        pygame.draw.rect(ms, (0, 0, 0, 40), ms.get_rect(), border_radius=6)
        surface.blit(ms, (meter_x - 2, br.y - 2))
        pygame.draw.rect(surface, BAR_BG, meter_rect, border_radius=5)
        pygame.draw.rect(surface, ANVIL_BORDER, meter_rect, width=1, border_radius=5)
        fill_h = int(meter_h * (self.hold_charge / self.HOLD_TARGET))
        if fill_h > 0:
            fill = pygame.Rect(meter_x + 1, meter_rect.bottom - fill_h, meter_w - 2, fill_h)
            # Gradient fill
            fg = pygame.Surface(fill.size, pygame.SRCALPHA)
            for yy in range(fill.height):
                ratio = yy / max(1, fill.height)
                r = int(80 + 60 * (1 - ratio))
                g = int(200 + 30 * (1 - ratio))
                b = int(130 + 20 * (1 - ratio))
                pygame.draw.line(fg, (r, g, b, 230), (0, yy), (fill.width, yy))
            surface.blit(fg, fill.topleft)
            # Glow at top of fill
            fill_glow = pygame.Surface((meter_w + 4, 6), pygame.SRCALPHA)
            pygame.draw.rect(fill_glow, (150, 255, 160, 80), fill_glow.get_rect(), border_radius=3)
            surface.blit(fill_glow, (meter_x - 2, fill.y - 3))

        # Phase-specific UI
        if self.phase == self.PHASE_INTRO:
            hint = self.font_medium.render(
                "Click to start -- hold SPACE / mouse to charge the bellows",
                True, TEXT_LIGHT)
            surface.blit(hint, (pr.centerx - hint.get_width() // 2, pr.y + pr.height - 90))
        elif self.phase == self.PHASE_ACTIVE:
            btn_w = 130
            btn_h = 38
            skip_rect = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = skip_rect
            _draw_button(surface, self.font_medium, skip_rect, "SKIP",
                         skip_rect.collidepoint(mouse_pos))
            label = "HOLD BELLOWS" if self._holding else "Release to rest"
            color = TEXT_GOOD if self._holding else TEXT_DIM
            tip = self.font_medium.render(label, True, color)
            surface.blit(tip, (pr.centerx - tip.get_width() // 2, pr.bottom - 110))
        elif self.phase == self.PHASE_RESULT:
            bonus_text = ("+1 bonus output (smelt XP x%g)" % self._xp_multiplier
                          if self._bonus_amount > 0 else "No bonus -- base output only")
            bonus_color = TEXT_GOOD if self._bonus_amount > 0 else TEXT_DIM
            _draw_result_overlay(surface, pr, self._outcome, self._outcome_color,
                                 bonus_text, bonus_color,
                                 self.font_large, self.font_medium, time_ms,
                                 bonus_icons=self._bonus_amount)
            btn_w = 160
            btn_h = 38
            cont = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = cont
            _draw_button(surface, self.font_medium, cont, "Continue",
                         cont.collidepoint(mouse_pos), TEXT_GOLD)


# ===========================================================================
# Iron Forge (iron-ore -> iron-ingot blast furnace)
# ===========================================================================

def _zone_at(x, bar_x, bar_w):
    """Classify cursor ``x`` into bullseye / good / miss relative to a bar."""
    if bar_w <= 0:
        return "miss"
    rel = (x - bar_x) / float(bar_w)
    rel = max(0.0, min(1.0, rel))
    dist = abs(rel - 0.5) * 2.0
    if dist <= 0.20:
        return "bullseye"
    if dist <= 0.48:
        return "good"
    return "miss"


class ForgeMinigame:
    """Three-strike horizontal timing challenge."""

    PHASE_INTRO = "intro"
    PHASE_STRIKE = "strike"
    PHASE_RESULT = "result"

    NUM_STRIKES = 3
    SWEEP_SPEED = 720.0

    def __init__(self, app, *, on_close=None, smelting_level=1):
        self.app = app
        self.on_close = on_close
        self.smelting_level = max(1, int(smelting_level))

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        self.font_title  = cfg.get_font(max(12, int(40 * cfg.ui_scale())))
        self.font_large  = cfg.get_font(max(11, int(30 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(22 * cfg.ui_scale())))
        self.font_small  = cfg.get_font(max(8,  int(18 * cfg.ui_scale())))

        panel_w = int(sw * 0.78)
        panel_h = int(sh * 0.50)
        self.panel_rect = pygame.Rect(
            (sw - panel_w) // 2,
            (sh - panel_h) // 2,
            panel_w, panel_h,
        )
        bar_w = int(panel_w * 0.78)
        bar_h = max(28, int(36 * cfg.ui_scale()))
        self.bar_rect = pygame.Rect(
            self.panel_rect.centerx - bar_w // 2,
            self.panel_rect.y + int(panel_h * 0.55),
            bar_w, bar_h,
        )

        self.phase = self.PHASE_INTRO
        self.strike_index = 0
        self.results = []
        self.cursor_x = float(self.bar_rect.x)
        self.cursor_dir = 1
        self._intro_timer = 1.0
        self._result_timer = 0.0
        self._outcome = ""
        self._outcome_color = TEXT_LIGHT
        self._xp_multiplier = 1.0
        self._bonus_amount = 0
        self._btn_strike = None
        self._btn_skip = None
        self._last_zone_flash = ""

    def _finalise(self):
        score = 0
        for zone in self.results:
            if zone == "bullseye":
                score += 2
            elif zone == "good":
                score += 1
        if score >= 5:
            self._bonus_amount = 2
            self._xp_multiplier = 2.0
            self._outcome = "MASTERFUL FORGE WORK!"
            self._outcome_color = TEXT_GOLD
        elif score >= 3:
            self._bonus_amount = 1
            self._xp_multiplier = 1.5
            self._outcome = "Solid hammering."
            self._outcome_color = TEXT_GOOD
        elif score >= 1:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "Acceptable shaping."
            self._outcome_color = TEXT_LIGHT
        else:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "The ingot cracked under the hammer..."
            self._outcome_color = TEXT_BAD
        self._result_timer = 2.4
        self.phase = self.PHASE_RESULT

    def _close(self):
        if callable(self.on_close):
            try:
                self.on_close(self._outcome, self._bonus_amount, self._xp_multiplier)
            except Exception as exc:
                logger.warning("smeltery minigame on_close failed: %s", exc)
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    def _record_strike(self):
        if self.phase != self.PHASE_STRIKE:
            return
        zone = _zone_at(self.cursor_x, self.bar_rect.x, self.bar_rect.width)
        if zone == "bullseye":
            GLOBAL_PARTICLES.spawn(self.cursor_x, self.bar_rect.centery, 50,
                                   (255, 180, 50), (100, 400), (3, 6),
                                   (0.3, 0.8), gravity=300)
            GLOBAL_SHAKE.shake(15)
        elif zone == "good":
            GLOBAL_PARTICLES.spawn(self.cursor_x, self.bar_rect.centery, 20,
                                   (200, 150, 50), (50, 200), (2, 4),
                                   (0.2, 0.5), gravity=250)
            GLOBAL_SHAKE.shake(5)
        else:
            GLOBAL_SHAKE.shake(3)
        self.results.append(zone)
        self._last_zone_flash = zone
        self.strike_index += 1
        if self.strike_index >= self.NUM_STRIKES:
            self._finalise()
        else:
            self.cursor_x = float(self.bar_rect.x + self.bar_rect.width // 2)
            self.cursor_dir = 1

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._bonus_amount = 0
                self._xp_multiplier = 1.0
                self._outcome = "Skipped"
                self._close()
                return
            if self.phase == self.PHASE_STRIKE and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._record_strike()
                return
            if self.phase == self.PHASE_INTRO and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.phase = self.PHASE_STRIKE
                return
            if self.phase == self.PHASE_RESULT and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._close()
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.phase == self.PHASE_INTRO:
                self.phase = self.PHASE_STRIKE
                return
            if self.phase == self.PHASE_STRIKE:
                if self._btn_strike and self._btn_strike.collidepoint(pos):
                    self._record_strike()
                    return
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._bonus_amount = 0
                    self._xp_multiplier = 1.0
                    self._outcome = "Skipped"
                    self._close()
                    return
                if self.bar_rect.collidepoint(pos):
                    self.cursor_x = float(pos[0])
                    self._record_strike()
                    return
            if self.phase == self.PHASE_RESULT:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._close()
                    return

    def update(self, dt):
        GLOBAL_PARTICLES.update(dt)
        GLOBAL_SHAKE.update(dt)
        if self.phase == self.PHASE_INTRO:
            self._intro_timer -= dt
            if self._intro_timer <= 0.0:
                self.phase = self.PHASE_STRIKE
            return
        if self.phase == self.PHASE_STRIKE:
            bar = self.bar_rect
            self.cursor_x += self.cursor_dir * self.SWEEP_SPEED * dt
            if self.cursor_x >= bar.right:
                self.cursor_x = float(bar.right)
                self.cursor_dir = -1
            elif self.cursor_x <= bar.x:
                self.cursor_x = float(bar.x)
                self.cursor_dir = 1
            return
        if self.phase == self.PHASE_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._close()

    def draw(self, surface):
        _draw_majestic_background(surface)
        time_ms = pygame.time.get_ticks()

        _draw_panel(
            surface, self.panel_rect,
            "Iron Forge",
            "Hammer when the cursor is in the gold zone -- three hits in a row.",
            (self.font_title, self.font_small),
        )
        pr = self.panel_rect
        mouse_pos = pygame.mouse.get_pos()

        # Strike indicators (ornate diamonds)
        _draw_strike_pips(surface, pr.centerx, pr.y + 78,
                          self.results, self.NUM_STRIKES, self.font_small)

        # Majestic zone bar
        bw = self.bar_rect.width
        miss_w = 0.22
        good_w = 0.28
        bull_w = 0.22
        zones = [
            (0.0, miss_w, BAR_MISS, BAR_MISS_GLOW),
            (miss_w, miss_w + good_w, BAR_GOOD, BAR_GOOD_GLOW),
            (miss_w + good_w, 1.0 - miss_w - good_w, BAR_BULLSEYE, BAR_BULL_GLOW),
            (1.0 - miss_w - good_w, 1.0 - good_w, BAR_GOOD, BAR_GOOD_GLOW),
            (1.0 - good_w, 1.0, BAR_MISS, BAR_MISS_GLOW),
        ]
        _draw_zone_bar(surface, self.bar_rect, zones,
                       cursor_x=self.cursor_x, time_ms=time_ms)

        # Phase-specific UI
        if self.phase == self.PHASE_INTRO:
            hint = self.font_medium.render(
                "Click / SPACE to start the forge hammer", True, TEXT_LIGHT)
            surface.blit(hint, (pr.centerx - hint.get_width() // 2, pr.y + pr.height - 90))
        elif self.phase == self.PHASE_STRIKE:
            btn_w = 130
            btn_h = 38
            strike_rect = pygame.Rect(pr.centerx - btn_w - 10, pr.bottom - 60, btn_w, btn_h)
            skip_rect = pygame.Rect(pr.centerx + 10, pr.bottom - 60, btn_w, btn_h)
            self._btn_strike = strike_rect
            self._btn_skip = skip_rect
            _draw_button(surface, self.font_medium, strike_rect, "STRIKE",
                         strike_rect.collidepoint(mouse_pos), TEXT_GOLD)
            _draw_button(surface, self.font_medium, skip_rect, "SKIP",
                         skip_rect.collidepoint(mouse_pos))
            if self._last_zone_flash:
                zone = self._last_zone_flash
                flash = {"bullseye": "PERFECT!", "good": "GOOD", "miss": "MISS"}.get(zone, "")
                color = BAR_BULLSEYE if zone == "bullseye" else (
                    BAR_GOOD if zone == "good" else BAR_MISS)
                fs = self.font_medium.render(flash, True, color)
                surface.blit(fs, (pr.centerx - fs.get_width() // 2, pr.bottom - 110))
        elif self.phase == self.PHASE_RESULT:
            bonus_text = ("+%d bonus ingot (smelt XP x%g)" % (self._bonus_amount, self._xp_multiplier)
                          if self._bonus_amount > 0 else "No bonus -- base output only")
            bonus_color = TEXT_GOOD if self._bonus_amount > 0 else TEXT_DIM
            _draw_result_overlay(surface, pr, self._outcome, self._outcome_color,
                                 bonus_text, bonus_color,
                                 self.font_large, self.font_medium, time_ms,
                                 bonus_icons=self._bonus_amount)
            btn_w = 160
            btn_h = 38
            cont = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = cont
            _draw_button(surface, self.font_medium, cont, "Continue",
                         cont.collidepoint(mouse_pos), TEXT_GOLD)


# ===========================================================================
# Quench (iron-ingot -> steel-ingot blast furnace)
# ===========================================================================

class QuenchMinigame:
    """Single-click timing challenge for the steel batch."""

    PHASE_INTRO = "intro"
    PHASE_SWEEP = "sweep"
    PHASE_RESULT = "result"

    SWEEP_DURATION = 1.6
    INITIAL_SWEET_SPOT = 0.55
    FINAL_SWEET_SPOT   = 0.18
    TOLERANCE_PX = 4

    def __init__(self, app, *, on_close=None, smelting_level=1):
        self.app = app
        self.on_close = on_close
        self.smelting_level = max(1, int(smelting_level))

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        self.font_title  = cfg.get_font(max(12, int(40 * cfg.ui_scale())))
        self.font_large  = cfg.get_font(max(11, int(30 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(22 * cfg.ui_scale())))
        self.font_small  = cfg.get_font(max(8,  int(18 * cfg.ui_scale())))

        panel_w = int(sw * 0.72)
        panel_h = int(sh * 0.46)
        self.panel_rect = pygame.Rect(
            (sw - panel_w) // 2,
            (sh - panel_h) // 2,
            panel_w, panel_h,
        )
        bar_w = int(panel_w * 0.86)
        bar_h = max(40, int(50 * cfg.ui_scale()))
        self.bar_rect = pygame.Rect(
            self.panel_rect.centerx - bar_w // 2,
            self.panel_rect.y + int(panel_h * 0.50),
            bar_w, bar_h,
        )

        self.phase = self.PHASE_INTRO
        self.t = 0.0
        self._intro_timer = 1.0
        self._result_timer = 0.0
        self._outcome = ""
        self._outcome_color = TEXT_LIGHT
        self._xp_multiplier = 1.0
        self._bonus_amount = 0
        self._btn_skip = None

    def _sweep_position(self):
        return self.t * self.bar_rect.width

    def _sweet_spot_rect(self):
        bw = self.bar_rect.width
        frac = self.INITIAL_SWEET_SPOT + (self.FINAL_SWEET_SPOT - self.INITIAL_SWEET_SPOT) * self.t
        w = bw * frac
        x = bw * 0.5 - w * 0.5
        return x, w

    def _attempt_click(self, x=None):
        if self.phase != self.PHASE_SWEEP:
            return
        cursor_x = self._sweep_position()
        spot_x, spot_w = self._sweet_spot_rect()
        dist = abs(cursor_x - (spot_x + spot_w * 0.5))
        if dist <= spot_w * 0.5 + self.TOLERANCE_PX:
            precision = 1.0 - min(1.0, dist / max(1, spot_w))
            if precision >= 0.85:
                GLOBAL_PARTICLES.spawn(self.bar_rect.x + self._sweep_position(),
                                       self.bar_rect.centery, 80, (100, 200, 255),
                                       (150, 500), (3, 8), (0.5, 1.2), gravity=150)
                GLOBAL_SHAKE.shake(20)
                self._bonus_amount = 1
                self._xp_multiplier = 2.0
                self._outcome = "PERFECT SEAL!"
                self._outcome_color = TEXT_GOLD
            elif precision >= 0.55:
                GLOBAL_PARTICLES.spawn(self.bar_rect.x + self._sweep_position(),
                                       self.bar_rect.centery, 30, (150, 220, 255),
                                       (50, 200), (2, 5), (0.4, 0.8), gravity=100)
                GLOBAL_SHAKE.shake(8)
                self._bonus_amount = 1
                self._xp_multiplier = 1.5
                self._outcome = "Good quench."
                self._outcome_color = TEXT_GOOD
            else:
                self._bonus_amount = 0
                self._xp_multiplier = 1.2
                self._outcome = "Marginal seal."
                self._outcome_color = TEXT_LIGHT
        else:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "The steel cracked..."
            self._outcome_color = TEXT_BAD
        self._result_timer = 2.2
        self.phase = self.PHASE_RESULT

    def _close(self):
        if callable(self.on_close):
            try:
                self.on_close(self._outcome, self._bonus_amount, self._xp_multiplier)
            except Exception as exc:
                logger.warning("smeltery minigame on_close failed: %s", exc)
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._bonus_amount = 0
                self._xp_multiplier = 1.0
                self._outcome = "Skipped"
                self._close()
                return
            if self.phase == self.PHASE_INTRO and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.phase = self.PHASE_SWEEP
                return
            if self.phase == self.PHASE_SWEEP and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._attempt_click()
                return
            if self.phase == self.PHASE_RESULT and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._close()
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.phase == self.PHASE_INTRO:
                self.phase = self.PHASE_SWEEP
                return
            if self.phase == self.PHASE_SWEEP:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._bonus_amount = 0
                    self._xp_multiplier = 1.0
                    self._outcome = "Skipped"
                    self._close()
                    return
                self._attempt_click()
                return
            if self.phase == self.PHASE_RESULT:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._close()
                    return

    def update(self, dt):
        GLOBAL_PARTICLES.update(dt)
        GLOBAL_SHAKE.update(dt)
        if self.phase == self.PHASE_INTRO:
            self._intro_timer -= dt
            if self._intro_timer <= 0.0:
                self.phase = self.PHASE_SWEEP
            return
        if self.phase == self.PHASE_SWEEP:
            self.t += dt / self.SWEEP_DURATION
            if self.t >= 1.0:
                self.t = 1.0
                self._bonus_amount = 0
                self._xp_multiplier = 1.0
                self._outcome = "Too slow -- the ingot cracked..."
                self._outcome_color = TEXT_BAD
                self._result_timer = 2.2
                self.phase = self.PHASE_RESULT
            return
        if self.phase == self.PHASE_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._close()

    def draw(self, surface):
        _draw_majestic_background(surface)
        time_ms = pygame.time.get_ticks()

        _draw_panel(
            surface, self.panel_rect,
            "Quench",
            "Click at the moment the cursor crosses the gold band.",
            (self.font_title, self.font_small),
        )
        pr = self.panel_rect
        mouse_pos = pygame.mouse.get_pos()

        br = self.bar_rect
        bw, bh = br.width, br.height

        # Draw base bar
        pygame.draw.rect(surface, BAR_BG, br, border_radius=8)

        # Sweet spot with animated glow
        spot_x, spot_w = self._sweet_spot_rect()
        spot = pygame.Rect(br.x + int(spot_x), br.y + 4, int(spot_w), bh - 8)
        # Glow around sweet spot
        sg = pygame.Surface((spot.width + 12, spot.height + 12), pygame.SRCALPHA)
        sp = int(abs(math.sin(time_ms * 0.005)) * 35 + 60)
        pygame.draw.rect(sg, (*BAR_BULL_GLOW, sp), sg.get_rect(), border_radius=10)
        surface.blit(sg, (spot.x - 6, spot.y - 6))
        # Sweet spot gradient fill
        ssf = pygame.Surface(spot.size, pygame.SRCALPHA)
        for yy in range(spot.height):
            ratio = yy / max(1, spot.height)
            r = min(255, int(255 * (0.8 + 0.2 * (1 - ratio))))
            g = min(255, int(200 * (0.8 + 0.2 * (1 - ratio))))
            b = min(255, int(60 * (0.8 + 0.2 * (1 - ratio))))
            pygame.draw.line(ssf, (r, g, b, 255), (0, yy), (spot.width, yy))
        surface.blit(ssf, spot.topleft)
        pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, br, width=2, border_radius=8)

        # Sweeping cursor with trail
        if self.phase == self.PHASE_SWEEP:
            cursor_x = br.x + int(self._sweep_position())
            # Afterglow trail
            trail_len = int(bw * 0.08)
            for i in range(trail_len):
                tx = cursor_x - trail_len + i
                if tx >= br.x:
                    ta = int((i / trail_len) * 120)
                    trail_pt = pygame.Surface((2, bh), pygame.SRCALPHA)
                    pygame.draw.line(trail_pt, (180, 220, 255, ta), (0, 0), (0, bh))
                    surface.blit(trail_pt, (tx, br.y))

            cursor_h = bh + 14
            cursor_top = br.y - 7
            # Cursor glow
            cg = pygame.Surface((16, cursor_h + 6), pygame.SRCALPHA)
            cp = int(abs(math.sin(time_ms * 0.007)) * 40 + 80)
            pygame.draw.rect(cg, (*BAR_CURSOR_GLOW, cp), cg.get_rect(), border_radius=5)
            surface.blit(cg, (cursor_x - 8, cursor_top - 3))
            cursor_rect = pygame.Rect(cursor_x - 3, cursor_top, 6, cursor_h)
            pygame.draw.rect(surface, BAR_CURSOR, cursor_rect, border_radius=2)
            # Top diamond
            pygame.draw.polygon(surface, BAR_CURSOR_GLOW,
                                [(cursor_x, cursor_top - 8), (cursor_x + 5, cursor_top - 3),
                                 (cursor_x, cursor_top + 2), (cursor_x - 5, cursor_top - 3)])

            # Pulsing CLICK prompt
            tip_alpha = int(abs(math.sin(time_ms * 0.008)) * 80 + 175)
            tip = self.font_medium.render("CLICK!", True, TEXT_GOLD)
            tip.set_alpha(tip_alpha)
            surface.blit(tip, (pr.centerx - tip.get_width() // 2, br.bottom + 10))

        if self.phase == self.PHASE_INTRO:
            hint = self.font_medium.render("Click / SPACE to begin the quench",
                                            True, TEXT_LIGHT)
            surface.blit(hint, (pr.centerx - hint.get_width() // 2, pr.y + pr.height - 90))
        elif self.phase == self.PHASE_SWEEP:
            btn_w = 130
            btn_h = 38
            skip_rect = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = skip_rect
            _draw_button(surface, self.font_medium, skip_rect, "SKIP",
                         skip_rect.collidepoint(mouse_pos))
        elif self.phase == self.PHASE_RESULT:
            bonus_text = ("+1 bonus steel ingot (smelt XP x%g)" % self._xp_multiplier
                          if self._bonus_amount > 0 else "No bonus -- base output only")
            bonus_color = TEXT_GOOD if self._bonus_amount > 0 else TEXT_DIM
            _draw_result_overlay(surface, pr, self._outcome, self._outcome_color,
                                 bonus_text, bonus_color,
                                 self.font_large, self.font_medium, time_ms,
                                 bonus_icons=self._bonus_amount)
            btn_w = 160
            btn_h = 38
            cont = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = cont
            _draw_button(surface, self.font_medium, cont, "Continue",
                         cont.collidepoint(mouse_pos), TEXT_GOLD)


# ===========================================================================
# Pattern Hammer (Damascus Patterning)
# ===========================================================================

class PatternMinigame:
    """A majestic rhythm-based pattern forging challenge."""

    PHASE_INTRO = "intro"
    PHASE_ACTIVE = "active"
    PHASE_RESULT = "result"

    def __init__(self, app, *, on_close=None, smelting_level=1):
        self.app = app
        self.on_close = on_close
        self.smelting_level = max(1, int(smelting_level))

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        self.font_title  = cfg.get_font(max(12, int(40 * cfg.ui_scale())))
        self.font_large  = cfg.get_font(max(11, int(30 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(22 * cfg.ui_scale())))
        self.font_small  = cfg.get_font(max(8,  int(18 * cfg.ui_scale())))

        panel_w = int(sw * 0.72)
        panel_h = int(sh * 0.52)
        self.panel_rect = pygame.Rect(
            (sw - panel_w) // 2,
            (sh - panel_h) // 2,
            panel_w, panel_h,
        )

        self.track_rect = pygame.Rect(
            self.panel_rect.x + int(40 * cfg.ui_scale()),
            self.panel_rect.centery - int(10 * cfg.ui_scale()),
            self.panel_rect.width - int(80 * cfg.ui_scale()),
            int(36 * cfg.ui_scale()),
        )
        self.target_x = self.track_rect.right - int(50 * cfg.ui_scale())
        
        self.phase = self.PHASE_INTRO
        self._intro_timer = 1.0
        self._result_timer = 0.0
        self._outcome = ""
        self._outcome_color = TEXT_LIGHT
        self._xp_multiplier = 1.0
        self._bonus_amount = 0
        self._btn_skip = None
        self._btn_strike = None
        
        self.t = 0.0
        self.notes = [1.0, 1.8, 2.4, 2.7, 3.5, 4.0, 4.4, 4.6, 5.0, 5.8]
        self.active_notes = []
        for n in self.notes:
            self.active_notes.append({"time": n, "hit": False, "missed": False, "flash": 0.0})
        
        self.speed = 300.0 * cfg.ui_scale()
        self.max_time = 7.0
        self.results = []
        self._last_zone_flash = ""
        self._flash_timer = 0.0

    def _finalise(self):
        score = 0
        for r in self.results:
            if r == "perfect": score += 2
            elif r == "good": score += 1
            
        max_score = len(self.notes) * 2
        
        if score >= max_score * 0.8:
            self._bonus_amount = 2
            self._xp_multiplier = 2.0
            self._outcome = "MAJESTIC PATTERN!"
            self._outcome_color = TEXT_GOLD
        elif score >= max_score * 0.5:
            self._bonus_amount = 1
            self._xp_multiplier = 1.5
            self._outcome = "Solid pattern."
            self._outcome_color = TEXT_GOOD
        elif score >= max_score * 0.2:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "Acceptable pattern."
            self._outcome_color = TEXT_LIGHT
        else:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "The pattern is deeply flawed..."
            self._outcome_color = TEXT_BAD
            
        self._result_timer = 2.4
        self.phase = self.PHASE_RESULT

    def _close(self):
        if callable(self.on_close):
            try:
                self.on_close(self._outcome, self._bonus_amount, self._xp_multiplier)
            except Exception as exc:
                logger.warning("pattern minigame on_close failed: %s", exc)
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    def _attempt_strike(self):
        if self.phase != self.PHASE_ACTIVE:
            return
            
        closest = None
        min_dist = 9999
        for note in self.active_notes:
            if not note["hit"] and not note["missed"]:
                note_x = self.track_rect.x + (self.t - note["time"]) * self.speed + (self.target_x - self.track_rect.x)
                dist = abs(note_x - self.target_x)
                if dist < min_dist:
                    min_dist = dist
                    closest = note
                    
        if closest and min_dist < int(40 * cfg.ui_scale()):
            if min_dist < int(15 * cfg.ui_scale()):
                GLOBAL_PARTICLES.spawn(self.target_x, self.track_rect.centery, 60,
                                       (255, 200, 50), (100, 500), (3, 8),
                                       (0.4, 0.8), gravity=200)
                GLOBAL_SHAKE.shake(20)
                self.results.append("perfect")
                self._last_zone_flash = "perfect"
                closest["flash"] = 1.0
            else:
                GLOBAL_PARTICLES.spawn(self.target_x, self.track_rect.centery, 20,
                                       (255, 150, 50), (50, 200), (2, 5),
                                       (0.3, 0.6), gravity=150)
                GLOBAL_SHAKE.shake(8)
                self.results.append("good")
                self._last_zone_flash = "good"
                closest["flash"] = 0.5
            closest["hit"] = True
            self._flash_timer = 0.5
        else:
            self.results.append("miss")
            self._last_zone_flash = "miss"
            self._flash_timer = 0.5

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._bonus_amount = 0
                self._xp_multiplier = 1.0
                self._outcome = "Skipped"
                self._close()
                return
            if self.phase == self.PHASE_ACTIVE and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._attempt_strike()
                return
            if self.phase == self.PHASE_INTRO and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.phase = self.PHASE_ACTIVE
                return
            if self.phase == self.PHASE_RESULT and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._close()
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.phase == self.PHASE_INTRO:
                self.phase = self.PHASE_ACTIVE
                return
            if self.phase == self.PHASE_ACTIVE:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._bonus_amount = 0
                    self._xp_multiplier = 1.0
                    self._outcome = "Skipped"
                    self._close()
                    return
                if self._btn_strike and self._btn_strike.collidepoint(pos):
                    self._attempt_strike()
                    return
                if self.track_rect.inflate(20, 40).collidepoint(pos):
                    self._attempt_strike()
                    return
            if self.phase == self.PHASE_RESULT:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._close()
                    return

    def update(self, dt):
        GLOBAL_PARTICLES.update(dt)
        GLOBAL_SHAKE.update(dt)
        if self.phase == self.PHASE_INTRO:
            self._intro_timer -= dt
            if self._intro_timer <= 0.0:
                self.phase = self.PHASE_ACTIVE
            return
        if self.phase == self.PHASE_ACTIVE:
            self.t += dt
            self._flash_timer = max(0.0, self._flash_timer - dt)
            
            for note in self.active_notes:
                if not note["hit"] and not note["missed"]:
                    note_x = self.track_rect.x + (self.t - note["time"]) * self.speed + (self.target_x - self.track_rect.x)
                    if note_x > self.target_x + int(40 * cfg.ui_scale()):
                        note["missed"] = True
                        self.results.append("miss")
                        self._last_zone_flash = "miss"
                        self._flash_timer = 0.5
            
            if self.t >= self.max_time:
                self._finalise()
            return
        if self.phase == self.PHASE_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._close()

    def draw(self, surface):
        _draw_majestic_background(surface)
        time_ms = pygame.time.get_ticks()

        shake_x = 0
        shake_y = 0
        if (self.phase == self.PHASE_ACTIVE and self._flash_timer > 0.0
                and self._last_zone_flash == 'miss'):
            intensity = int(self._flash_timer * 15)
            shake_x = random.randint(-intensity, intensity)
            shake_y = random.randint(-intensity, intensity)
            
        pr = self.panel_rect.move(shake_x, shake_y)
        tr = self.track_rect.move(shake_x, shake_y)
        target_x = self.target_x + shake_x

        _draw_panel(
            surface, pr,
            "Pattern Hammer",
            "Strike (SPACE/Click) when glowing runes enter the target zone.",
            (self.font_title, self.font_small),
        )
        mouse_pos = pygame.mouse.get_pos()

        # Track base
        pygame.draw.rect(surface, BAR_BG, tr, border_radius=8)
        pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, tr, width=2, border_radius=8)
        
        # Target zone with animated glow
        target_w = 30
        target_rect = pygame.Rect(target_x - target_w // 2, tr.y - 4, target_w, tr.height + 8)
        tg = pygame.Surface((target_w + 10, tr.height + 16), pygame.SRCALPHA)
        tp = int(abs(math.sin(time_ms * 0.005)) * 40 + 65)
        pygame.draw.rect(tg, (*BAR_BULL_GLOW, tp), tg.get_rect(), border_radius=8)
        surface.blit(tg, (target_rect.x - 5, target_rect.y - 4))
        pygame.draw.rect(surface, BAR_BULLSEYE, target_rect, border_radius=4)
        pygame.draw.rect(surface, BAR_CURSOR_GLOW, target_rect, width=2, border_radius=4)

        # Active runes
        if self.phase == self.PHASE_ACTIVE:
            for note in self.active_notes:
                if not note["hit"] and not note["missed"]:
                    note_x = tr.x + (self.t - note["time"]) * self.speed + (target_x - tr.x)
                    if tr.x <= note_x <= tr.right + 20:
                        n_rect = pygame.Rect(int(note_x) - 10, tr.y + 4, 20, tr.height - 8)
                        # Rune glow
                        rg = pygame.Surface((28, tr.height), pygame.SRCALPHA)
                        pygame.draw.rect(rg, (100, 220, 255, 50), rg.get_rect(), border_radius=6)
                        surface.blit(rg, (n_rect.x - 4, n_rect.y - 2))
                        # Rune body
                        pygame.draw.rect(surface, (100, 220, 255), n_rect, border_radius=4)
                        pygame.draw.rect(surface, (200, 255, 255), n_rect, width=2, border_radius=4)
                        letter = "R"
                        t = self.font_small.render(letter, True, (255, 255, 255))
                        surface.blit(t, t.get_rect(center=n_rect.center))
                elif note["flash"] > 0:
                    # Flash effect on hit notes
                    note_x = tr.x + (self.t - note["time"]) * self.speed + (target_x - tr.x)
                    if tr.x <= note_x <= tr.right + 20:
                        flash_alpha = int(note["flash"] * 200)
                        flash_c = (255, 220, 80) if note["flash"] >= 1.0 else (255, 180, 60)
                        fs = pygame.Surface((24, tr.height - 4), pygame.SRCALPHA)
                        pygame.draw.rect(fs, (*flash_c, flash_alpha), fs.get_rect(), border_radius=4)
                        surface.blit(fs, (int(note_x) - 12, tr.y + 2))

        if self.phase == self.PHASE_INTRO:
            hint = self.font_medium.render("Click / SPACE to start the rhythm forge",
                                            True, TEXT_LIGHT)
            surface.blit(hint, (pr.centerx - hint.get_width() // 2, pr.y + pr.height - 90))
        elif self.phase == self.PHASE_ACTIVE:
            btn_w = 130
            btn_h = 38
            strike_rect = pygame.Rect(pr.centerx - btn_w - 10, pr.bottom - 60, btn_w, btn_h)
            skip_rect = pygame.Rect(pr.centerx + 10, pr.bottom - 60, btn_w, btn_h)
            self._btn_strike = strike_rect
            self._btn_skip = skip_rect
            _draw_button(surface, self.font_medium, strike_rect, "STRIKE",
                         strike_rect.collidepoint(mouse_pos), TEXT_GOLD)
            _draw_button(surface, self.font_medium, skip_rect, "SKIP",
                         skip_rect.collidepoint(mouse_pos))
            
            if self._flash_timer > 0.0:
                zone = self._last_zone_flash
                flash = {"perfect": "MAJESTIC!", "good": "GOOD", "miss": "MISS"}.get(zone, "")
                color = BAR_BULLSEYE if zone == "perfect" else (
                    BAR_GOOD if zone == "good" else BAR_MISS)
                fs = self.font_medium.render(flash, True, color)
                alpha = int(255 * (self._flash_timer / 0.5))
                fs.set_alpha(alpha)
                surface.blit(fs, (pr.centerx - fs.get_width() // 2, pr.bottom - 110))
                
        elif self.phase == self.PHASE_RESULT:
            bonus_text = ("+%d pattern quality (smelt XP x%g)" % (self._bonus_amount, self._xp_multiplier)
                          if self._bonus_amount > 0 else "No bonus -- basic pattern only")
            bonus_color = TEXT_GOOD if self._bonus_amount > 0 else TEXT_DIM
            _draw_result_overlay(surface, pr, self._outcome, self._outcome_color,
                                 bonus_text, bonus_color,
                                 self.font_large, self.font_medium, time_ms,
                                 bonus_icons=self._bonus_amount)
            btn_w = 160
            btn_h = 38
            cont = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = cont
            _draw_button(surface, self.font_medium, cont, "Continue",
                         cont.collidepoint(mouse_pos), TEXT_GOLD)


# ===========================================================================
# Minigame Chain
# ===========================================================================

class MinigameChain:
    """Wrapper that plays several minigames in sequence."""

    PHASE_PLAYING = "playing"
    PHASE_RESULT = "result"

    def __init__(self, app, chain_ids, *, on_close=None, smelting_level=1):
        self.app = app
        self.chain_ids = list(chain_ids)
        self.final_on_close = on_close
        self.smelting_level = max(1, int(smelting_level))

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        self.font_title = cfg.get_font(max(12, int(40 * cfg.ui_scale())))
        self.font_large = cfg.get_font(max(11, int(30 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(22 * cfg.ui_scale())))
        self.font_small = cfg.get_font(max(8, int(18 * cfg.ui_scale())))

        self.phase = self.PHASE_PLAYING
        self.current_index = 0
        self.current_minigame = None
        self._total_bonus = 0
        self._total_xp_mult = 1.0
        self._step_results = []
        self._closed = False

        chain_key = tuple(chain_ids)
        self.chain_title = CHAIN_TITLES.get(chain_key, "Forging Chain")

        self._step_labels = [
            CHAIN_STEP_NAMES.get(mid, mid.replace("_", " ").title())
            for mid in chain_ids
        ]

        self._start_current()

    def _step_on_close(self, outcome, bonus_amount, xp_multiplier):
        self._step_results.append((outcome, bonus_amount, xp_multiplier))
        self._total_bonus += int(bonus_amount or 0)
        self._total_xp_mult *= float(xp_multiplier or 1.0)
        self.current_index += 1
        self._start_current()

    def _start_current(self):
        if self.current_index >= len(self.chain_ids):
            self._finish_chain()
            return
        mg_id = self.chain_ids[self.current_index]
        cls = None
        if mg_id == "tending": cls = TendingFireMinigame
        elif mg_id == "forge": cls = ForgeMinigame
        elif mg_id == "quench": cls = QuenchMinigame
        elif mg_id == "bellows": cls = BellowsMinigame
        elif mg_id == "temper": cls = TemperMinigame
        elif mg_id == "pattern": cls = PatternMinigame
        
        if cls is None:
            logger.warning("MinigameChain: unknown minigame id %r, skipping", mg_id)
            self.current_index += 1
            self._start_current()
            return
        try:
            self.current_minigame = cls(
                self.app,
                on_close=self._step_on_close,
                smelting_level=self.smelting_level,
            )
        except Exception as exc:
            logger.warning("MinigameChain: failed to create %s: %s", mg_id, exc)
            self.current_index += 1
            self._start_current()

    def _finish_chain(self):
        self.phase = self.PHASE_RESULT
        if self._total_bonus > 0:
            self._outcome = "Chain complete! (+%d bonus)" % self._total_bonus
            self._outcome_color = TEXT_GOLD
        else:
            self._outcome = "Chain complete."
            self._outcome_color = TEXT_LIGHT
        self._result_timer = 2.0

    def _close(self):
        if self._closed:
            return
        self._closed = True
        if callable(self.final_on_close):
            try:
                self.final_on_close(self._outcome, self._total_bonus, self._total_xp_mult)
            except Exception as exc:
                logger.warning("MinigameChain final on_close failed: %s", exc)
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    def _draw_chain_hud(self, surface):
        import math
        time_ms = pygame.time.get_ticks()
        total = len(self.chain_ids)
        step = min(self.current_index + 1, total)

        # Step label
        label = "Step %d/%d: %s" % (step, total,
                                     self._step_labels[self.current_index]
                                     if self.current_index < total else "")
        suf = self.font_small.render(label, True, TEXT_GOLD)
        surface.blit(suf, (self.screen_w // 2 - suf.get_width() // 2,
                           int(20 * cfg.ui_scale())))

        # Progress bar with glow
        bar_w = int(260 * cfg.ui_scale())
        bar_h = int(10 * cfg.ui_scale())
        bar_x = self.screen_w // 2 - bar_w // 2
        bar_y = int(20 * cfg.ui_scale()) + suf.get_height() + int(6 * cfg.ui_scale())
        bar_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)

        # Shadow
        sh = pygame.Surface((bar_w + 4, bar_h + 4), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 60), sh.get_rect(), border_radius=6)
        surface.blit(sh, (bar_x - 2, bar_y + 2))

        pygame.draw.rect(surface, BAR_BG, bar_rect, border_radius=5)
        pygame.draw.rect(surface, ANVIL_BORDER, bar_rect, width=1, border_radius=5)
        fill_w = max(1, int(bar_w * step / total))
        fill = pygame.Rect(bar_x, bar_y, fill_w, bar_h)

        # Gradient fill
        fg = pygame.Surface(fill.size, pygame.SRCALPHA)
        for yy in range(bar_h):
            ratio = yy / max(1, bar_h)
            r = min(255, int(255 * (0.85 + 0.15 * (1 - ratio))))
            g = min(255, int(200 * (0.85 + 0.15 * (1 - ratio))))
            b = min(255, int(60 * (0.85 + 0.15 * (1 - ratio))))
            pygame.draw.line(fg, (r, g, b, 255), (0, yy), (fill_w, yy))
        surface.blit(fg, fill.topleft)

        # Glow at fill edge
        glow_x = bar_x + fill_w - 2
        glow_sf = pygame.Surface((8, bar_h + 6), pygame.SRCALPHA)
        gp = int(abs(math.sin(time_ms * 0.004)) * 40 + 60)
        pygame.draw.rect(glow_sf, (*BAR_BULL_GLOW, gp), glow_sf.get_rect(), border_radius=4)
        surface.blit(glow_sf, (glow_x - 4, bar_y - 3))

        # Diamond at fill end
        dx = bar_x + fill_w
        dy = bar_y + bar_h // 2
        ds = 4
        pygame.draw.polygon(surface, (255, 240, 160),
                            [(dx, dy - ds), (dx + ds, dy), (dx, dy + ds), (dx - ds, dy)])

    def update(self, dt):
        GLOBAL_PARTICLES.update(dt)
        GLOBAL_SHAKE.update(dt)
        if self.current_minigame is not None:
            self.current_minigame.update(dt)
        elif self.phase == self.PHASE_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._close()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.current_minigame = None
            self._total_bonus = 0
            self._total_xp_mult = 1.0
            self._outcome = "Chain skipped"
            self._outcome_color = TEXT_BAD
            self._close()
            return
        if self.current_minigame is not None:
            self.current_minigame.handle_event(event)

    def draw(self, surface):
        if self.current_minigame is not None:
            self.current_minigame.draw(surface)
            self._draw_chain_hud(surface)
        elif self.phase == self.PHASE_RESULT:
            _draw_majestic_background(surface)
            time_ms = pygame.time.get_ticks()
            pr = pygame.Rect(
                (self.screen_w - 520) // 2,
                (self.screen_h - 220) // 2,
                520, 220,
            )
            _draw_panel(
                surface, pr,
                self.chain_title,
                self._outcome,
                (self.font_title, self.font_medium),
            )
            bonus_text = ("+%d bonus items (smelt XP x%g)" % (self._total_bonus, self._total_xp_mult)
                          if self._total_bonus > 0 else "No bonus -- base output only")
            bonus_color = TEXT_GOOD if self._total_bonus > 0 else TEXT_DIM
            _draw_result_overlay(surface, pr, self._outcome, self._outcome_color,
                                 bonus_text, bonus_color,
                                 self.font_large, self.font_medium, time_ms,
                                 bonus_icons=self._total_bonus)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def make_smeltery_minigame(app, recipe, *, on_close=None, smelting_level=1):
    """Return a fresh smeltery-minigame instance for ``recipe`` or
    ``None`` if the recipe doesn't trigger one.

    ``recipe`` is a dict in the form documented in
    :mod:`database.smeltery_recipes_db`. The minigame id is taken
    from the ``minigame`` key (see :data:`MINIGAME_REGISTRY`).
    """
    if not recipe:
        return None
    mg_id = recipe.get("minigame", "none") or "none"
    if mg_id == "tending":
        return TendingFireMinigame(app, on_close=on_close, smelting_level=smelting_level)
    if mg_id == "forge":
        return ForgeMinigame(app, on_close=on_close, smelting_level=smelting_level)
    if mg_id == "quench":
        return QuenchMinigame(app, on_close=on_close, smelting_level=smelting_level)
    if mg_id == "bellows":
        return BellowsMinigame(app, on_close=on_close, smelting_level=smelting_level)
    if mg_id == "temper":
        return TemperMinigame(app, on_close=on_close, smelting_level=smelting_level)
    if mg_id == "pattern":
        return PatternMinigame(app, on_close=on_close, smelting_level=smelting_level)
    return None


# ===========================================================================
# Bellows Pump (iron-ore + coal -> iron-ingot blast furnace)
# ===========================================================================

class BellowsMinigame:
    """Rapid-click pressure challenge for iron smelting."""

    PHASE_INTRO = "intro"
    PHASE_ACTIVE = "active"
    PHASE_RESULT = "result"

    PUMP_FORCE = 0.14
    DRAG = 0.10
    HOLD_TARGET = 1.8
    ZONE_CENTER = 0.55
    ZONE_WIDTH = 0.24
    CRITICAL_FLOOR = 0.08
    CRITICAL_TOLERANCE = 0.6

    def __init__(self, app, *, on_close=None, smelting_level=1):
        self.app = app
        self.on_close = on_close
        self.smelting_level = max(1, int(smelting_level))

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        self.font_title  = cfg.get_font(max(12, int(40 * cfg.ui_scale())))
        self.font_large  = cfg.get_font(max(11, int(30 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(22 * cfg.ui_scale())))
        self.font_small  = cfg.get_font(max(8,  int(18 * cfg.ui_scale())))

        panel_w = int(sw * 0.60)
        panel_h = int(sh * 0.54)
        self.panel_rect = pygame.Rect(
            (sw - panel_w) // 2,
            (sh - panel_h) // 2,
            panel_w, panel_h,
        )
        gauge_w = 28
        gauge_h = int(panel_h * 0.60)
        gauge_x = self.panel_rect.centerx - gauge_w // 2
        gauge_y = self.panel_rect.y + int(panel_h * 0.28)
        self.gauge_rect = pygame.Rect(gauge_x, gauge_y, gauge_w, gauge_h)

        self.phase = self.PHASE_INTRO
        self.pressure = 0.5
        self.hold_time = 0.0
        self._critical_time = 0.0
        self._intro_timer = 1.0
        self._result_timer = 0.0
        self._outcome = ""
        self._outcome_color = TEXT_LIGHT
        self._xp_multiplier = 1.0
        self._bonus_amount = 0
        self._btn_skip = None

    def _finalise(self, perfect, success):
        if perfect:
            self._bonus_amount = 2
            self._xp_multiplier = 2.0
            self._outcome = "BELLOWS MASTERY!"
            self._outcome_color = TEXT_GOLD
        elif success:
            self._bonus_amount = 1
            self._xp_multiplier = 1.5
            self._outcome = "Strong bellows work."
            self._outcome_color = TEXT_GOOD
        else:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "The fire died out..."
            self._outcome_color = TEXT_BAD
        self._result_timer = 2.2
        self.phase = self.PHASE_RESULT

    def _close(self):
        if callable(self.on_close):
            try:
                self.on_close(self._outcome, self._bonus_amount, self._xp_multiplier)
            except Exception as exc:
                logger.warning("bellows minigame on_close failed: %s", exc)
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._bonus_amount = 0
                self._xp_multiplier = 1.0
                self._outcome = "Skipped"
                self._close()
                return
            if self.phase == self.PHASE_ACTIVE and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.pressure = min(1.0, self.pressure + self.PUMP_FORCE)
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.phase == self.PHASE_INTRO:
                self.phase = self.PHASE_ACTIVE
                return
            if self.phase == self.PHASE_ACTIVE:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._bonus_amount = 0
                    self._xp_multiplier = 1.0
                    self._outcome = "Skipped"
                    self._close()
                    return
                self.pressure = min(1.0, self.pressure + self.PUMP_FORCE)
                return
            if self.phase == self.PHASE_RESULT:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._close()
                    return

    def update(self, dt):
        GLOBAL_PARTICLES.update(dt)
        GLOBAL_SHAKE.update(dt)
        if self.phase == self.PHASE_INTRO:
            self._intro_timer -= dt
            if self._intro_timer <= 0.0:
                self.phase = self.PHASE_ACTIVE
            return
        if self.phase == self.PHASE_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._close()
            return
        if self.phase != self.PHASE_ACTIVE:
            return

        self.pressure = max(0.0, self.pressure - self.DRAG * dt)

        zone_low = self.ZONE_CENTER - self.ZONE_WIDTH * 0.5
        zone_high = self.ZONE_CENTER + self.ZONE_WIDTH * 0.5
        in_zone = zone_low <= self.pressure <= zone_high

        if in_zone:
            self.hold_time += dt
            self._critical_time = 0.0
        else:
            self._critical_time += dt

        if self.pressure < self.CRITICAL_FLOOR and self._critical_time > self.CRITICAL_TOLERANCE:
            self._finalise(perfect=False, success=False)
            return

        if self.hold_time >= self.HOLD_TARGET:
            perfect = self._critical_time < 0.1 and self.hold_time < self.HOLD_TARGET * 1.3
            self._finalise(perfect=perfect, success=True)
            return

    def draw(self, surface):
        _draw_majestic_background(surface)
        time_ms = pygame.time.get_ticks()

        _draw_panel(
            surface, self.panel_rect,
            "Bellows Pump",
            "Pump the bellows -- keep the pressure in the gold zone.",
            (self.font_title, self.font_small),
        )
        pr = self.panel_rect
        mouse_pos = pygame.mouse.get_pos()

        # Enhanced vertical gauge
        _draw_zone_gauge(surface, self.gauge_rect, self.pressure,
                         self.ZONE_CENTER, self.ZONE_WIDTH,
                         fill=self.hold_time, fill_target=self.HOLD_TARGET,
                         warning=(self.pressure < self.CRITICAL_FLOOR),
                         time_ms=time_ms)

        gr = self.gauge_rect

        # Fire dying warning
        if self.pressure < self.CRITICAL_FLOOR:
            warn_alpha = int(abs(math.sin(time_ms * 0.008)) * 200)
            warn = self.font_small.render("FIRE DYING!", True, TEXT_BAD)
            warn.set_alpha(warn_alpha)
            surface.blit(warn, (gr.right + 24, gr.centery - warn.get_height() // 2))

        # Phase-specific UI
        if self.phase == self.PHASE_INTRO:
            hint = self.font_medium.render(
                "Click / SPACE to start pumping the bellows", True, TEXT_LIGHT)
            surface.blit(hint, (pr.centerx - hint.get_width() // 2, pr.y + pr.height - 90))
        elif self.phase == self.PHASE_ACTIVE:
            btn_w = 130
            btn_h = 38
            skip_rect = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = skip_rect
            _draw_button(surface, self.font_medium, skip_rect, "SKIP",
                         skip_rect.collidepoint(mouse_pos))
            tip_text = "PUMP!" if self.pressure < self.ZONE_CENTER else "Hold..."
            tip = self.font_medium.render(tip_text, True, TEXT_GOOD)
            surface.blit(tip, (pr.centerx - tip.get_width() // 2, pr.bottom - 110))
        elif self.phase == self.PHASE_RESULT:
            bonus_text = ("+%d bonus ingot (smelt XP x%g)" % (self._bonus_amount, self._xp_multiplier)
                          if self._bonus_amount > 0 else "No bonus -- base output only")
            bonus_color = TEXT_GOOD if self._bonus_amount > 0 else TEXT_DIM
            _draw_result_overlay(surface, pr, self._outcome, self._outcome_color,
                                 bonus_text, bonus_color,
                                 self.font_large, self.font_medium, time_ms,
                                 bonus_icons=self._bonus_amount)
            btn_w = 160
            btn_h = 38
            cont = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = cont
            _draw_button(surface, self.font_medium, cont, "Continue",
                         cont.collidepoint(mouse_pos), TEXT_GOLD)


# ===========================================================================
# Temper (iron-ingot + coke -> steel-ingot alternative / high-end)
# ===========================================================================

class TemperMinigame:
    """Multi-stage colour-match tempering challenge for steel."""

    PHASE_INTRO = "intro"
    PHASE_STAGE = "stage"
    PHASE_RESULT = "result"

    STAGES = 5
    CYCLE_SPEED_BASE = 0.8
    CYCLE_SPEED_INCREMENT = 0.3
    MATCH_THRESHOLD = 0.10

    COLOUR_CYCLE = [
        (80, 20, 10),
        (160, 40, 20),
        (220, 100, 40),
        (255, 180, 60),
        (255, 220, 130),
        (255, 240, 200),
        (255, 220, 130),
        (255, 180, 60),
        (220, 100, 40),
        (160, 40, 20),
    ]

    TARGET_COLOURS = [
        (220, 100, 40),
        (255, 180, 60),
        (255, 220, 130),
        (255, 240, 200),
        (255, 180, 60),
    ]

    def __init__(self, app, *, on_close=None, smelting_level=1):
        self.app = app
        self.on_close = on_close
        self.smelting_level = max(1, int(smelting_level))

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        self.font_title  = cfg.get_font(max(12, int(40 * cfg.ui_scale())))
        self.font_large  = cfg.get_font(max(11, int(30 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(22 * cfg.ui_scale())))
        self.font_small  = cfg.get_font(max(8,  int(18 * cfg.ui_scale())))

        panel_w = int(sw * 0.60)
        panel_h = int(sh * 0.52)
        self.panel_rect = pygame.Rect(
            (sw - panel_w) // 2,
            (sh - panel_h) // 2,
            panel_w, panel_h,
        )

        self.ingot_centre = (self.panel_rect.centerx, self.panel_rect.centery + 20)
        self.ingot_radius = int(72 * cfg.ui_scale())

        self.target_swatch_rect = pygame.Rect(
            self.panel_rect.centerx - int(30 * cfg.ui_scale()),
            self.panel_rect.y + int(28 * cfg.ui_scale()),
            int(60 * cfg.ui_scale()),
            int(24 * cfg.ui_scale()),
        )

        self.phase = self.PHASE_INTRO
        self.stage_index = 0
        self.results = []
        self._cycle_t = 0.0
        self._stage_timer = 0.0
        self._input_locked_timer = 0.0
        self._final_stage = False
        self._intro_timer = 1.0
        self._result_timer = 0.0
        self._outcome = ""
        self._outcome_color = TEXT_LIGHT
        self._xp_multiplier = 1.0
        self._bonus_amount = 0
        self._btn_skip = None
        self._last_result = ""

    def _current_cycle_speed(self):
        return self.CYCLE_SPEED_BASE + self.stage_index * self.CYCLE_SPEED_INCREMENT

    def _ingot_colour(self):
        t = self._cycle_t
        idx = int(t) % len(self.COLOUR_CYCLE)
        frac = t - int(t)
        next_idx = (idx + 1) % len(self.COLOUR_CYCLE)
        c1 = self.COLOUR_CYCLE[idx]
        c2 = self.COLOUR_CYCLE[next_idx]
        return (
            int(c1[0] + (c2[0] - c1[0]) * frac),
            int(c1[1] + (c2[1] - c1[1]) * frac),
            int(c1[2] + (c2[2] - c1[2]) * frac),
        )

    def _colour_distance(self, c1, c2):
        return math.sqrt(
            (c1[0] - c2[0]) ** 2 +
            (c1[1] - c2[1]) ** 2 +
            (c1[2] - c2[2]) ** 2
        ) / math.sqrt(3 * 255 ** 2)

    def _attempt_match(self):
        if self.phase != self.PHASE_STAGE:
            return
        if self._input_locked_timer > 0.0:
            return
        ingot_c = self._ingot_colour()
        target_c = self.TARGET_COLOURS[self.stage_index % len(self.TARGET_COLOURS)]
        dist = self._colour_distance(ingot_c, target_c)
        if dist <= 0.08:
            self.results.append("perfect")
            self._last_result = "PERFECT!"
        elif dist <= self.MATCH_THRESHOLD:
            self.results.append("good")
            self._last_result = "Good match"
        else:
            self.results.append("miss")
            self._last_result = "Mismatch"
        self._input_locked_timer = 0.4
        self.stage_index += 1
        if self.stage_index >= self.STAGES:
            self._finalise()
        else:
            self._stage_timer = 1.2
            self._cycle_t = 0.0

    def _finalise(self):
        perfects = sum(1 for r in self.results if r == "perfect")
        goods = sum(1 for r in self.results if r == "good")
        if perfects >= 4:
            self._bonus_amount = 2
            self._xp_multiplier = 2.5
            self._outcome = "MASTER TEMPER!"
            self._outcome_color = TEXT_GOLD
        elif perfects >= 2:
            self._bonus_amount = 1
            self._xp_multiplier = 1.5
            self._outcome = "Well tempered."
            self._outcome_color = TEXT_GOOD
        elif goods + perfects >= 3:
            self._bonus_amount = 0
            self._xp_multiplier = 1.2
            self._outcome = "Adequate temper."
            self._outcome_color = TEXT_LIGHT
        else:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "The steel became brittle..."
            self._outcome_color = TEXT_BAD
        self._result_timer = 2.4
        self.phase = self.PHASE_RESULT

    def _close(self):
        if callable(self.on_close):
            try:
                self.on_close(self._outcome, self._bonus_amount, self._xp_multiplier)
            except Exception as exc:
                logger.warning("temper minigame on_close failed: %s", exc)
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._bonus_amount = 0
                self._xp_multiplier = 1.0
                self._outcome = "Skipped"
                self._close()
                return
            if self.phase == self.PHASE_STAGE and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._attempt_match()
                return
            if self.phase == self.PHASE_INTRO and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.phase = self.PHASE_STAGE
                return
            if self.phase == self.PHASE_RESULT and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._close()
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.phase == self.PHASE_INTRO:
                self.phase = self.PHASE_STAGE
                return
            if self.phase == self.PHASE_STAGE:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._bonus_amount = 0
                    self._xp_multiplier = 1.0
                    self._outcome = "Skipped"
                    self._close()
                    return
                if self._input_locked_timer <= 0.0:
                    self._attempt_match()
                return
            if self.phase == self.PHASE_RESULT:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._close()
                    return

    def update(self, dt):
        GLOBAL_PARTICLES.update(dt)
        GLOBAL_SHAKE.update(dt)
        if self.phase == self.PHASE_INTRO:
            self._intro_timer -= dt
            if self._intro_timer <= 0.0:
                self.phase = self.PHASE_STAGE
            return
        if self.phase == self.PHASE_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._close()
            return
        if self.phase == self.PHASE_STAGE:
            self._input_locked_timer = max(0.0, self._input_locked_timer - dt)
            if self._stage_timer > 0.0:
                self._stage_timer -= dt
                if self._stage_timer <= 0.0:
                    self._cycle_t = 0.0
            else:
                speed = self._current_cycle_speed()
                self._cycle_t += dt * speed
            return

    def draw(self, surface):
        _draw_majestic_background(surface)
        time_ms = pygame.time.get_ticks()

        _draw_panel(
            surface, self.panel_rect,
            "Temper the Steel",
            "Click when the ingot colour matches the target.",
            (self.font_title, self.font_small),
        )
        pr = self.panel_rect
        mouse_pos = pygame.mouse.get_pos()

        ingot_c = self._ingot_colour()
        target_c = self.TARGET_COLOURS[self.stage_index % len(self.TARGET_COLOURS)]

        # Stage label
        stage_str = "Stage %d / %d" % (self.stage_index + 1, self.STAGES)
        ss = self.font_medium.render(stage_str, True, TEXT_LIGHT)
        surface.blit(ss, (pr.centerx - ss.get_width() // 2,
                          self.target_swatch_rect.bottom + 6))

        # Target swatch with glow
        sw = self.target_swatch_rect
        sw_glow = pygame.Surface((sw.width + 10, sw.height + 10), pygame.SRCALPHA)
        sp = int(abs(math.sin(time_ms * 0.004)) * 30 + 50)
        pygame.draw.rect(sw_glow, (*target_c, sp), sw_glow.get_rect(), border_radius=8)
        surface.blit(sw_glow, (sw.x - 5, sw.y - 5))
        pygame.draw.rect(surface, target_c, sw, border_radius=4)
        pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, sw, width=2, border_radius=4)
        target_label = self.font_small.render("Target", True, TEXT_DIM)
        surface.blit(target_label, (sw.centerx - target_label.get_width() // 2,
                                    sw.top - target_label.get_height() - 2))

        # Majestic glowing ingot
        cx, cy = self.ingot_centre
        r = self.ingot_radius
        _draw_orb_ingot(surface, cx, cy, r, ingot_c, time_ms)

        # Stage results as ornate diamonds
        stage_results_x = pr.left + int(20 * cfg.ui_scale())
        stage_results_y = pr.centery + r + int(30 * cfg.ui_scale())
        for i, res in enumerate(self.results):
            ix = stage_results_x + i * 28
            iy = stage_results_y + 8
            ps = 7
            if res == "perfect":
                color = TEXT_GOLD
                points = [(ix, iy - ps), (ix + ps, iy), (ix, iy + ps), (ix - ps, iy)]
                pygame.draw.polygon(surface, BAR_BULLSEYE, points)
                pygame.draw.polygon(surface, (255, 240, 180), points, 1)
            elif res == "good":
                color = TEXT_GOOD
                points = [(ix, iy - ps), (ix + ps, iy), (ix, iy + ps), (ix - ps, iy)]
                pygame.draw.polygon(surface, BAR_GOOD, points)
                pygame.draw.polygon(surface, (255, 255, 255), points, 1)
            else:
                color = TEXT_BAD
                points = [(ix, iy - ps), (ix + ps, iy), (ix, iy + ps), (ix - ps, iy)]
                pygame.draw.polygon(surface, BAR_MISS, points)
                pygame.draw.polygon(surface, (255, 100, 100), points, 1)
            label = {"perfect": "P", "good": "G", "miss": "X"}.get(res, "?")
            t = self.font_small.render(label, True, (255, 255, 255))
            surface.blit(t, t.get_rect(center=(ix, iy)))

        # Phase-specific UI
        if self.phase == self.PHASE_INTRO:
            hint = self.font_medium.render("Click / SPACE to begin tempering",
                                            True, TEXT_LIGHT)
            surface.blit(hint, (pr.centerx - hint.get_width() // 2, pr.y + pr.height - 90))
        elif self.phase == self.PHASE_STAGE:
            btn_w = 130
            btn_h = 38
            skip_rect = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = skip_rect
            _draw_button(surface, self.font_medium, skip_rect, "SKIP",
                         skip_rect.collidepoint(mouse_pos))
            if self._input_locked_timer > 0.0:
                tip_text = self._last_result
                tip_color = (TEXT_GOLD if "PERFECT" in self._last_result
                             else TEXT_GOOD if "Good" in self._last_result else TEXT_BAD)
            else:
                tip_text = "MATCH COLOUR!"
                tip_color = TEXT_GOLD
            tip = self.font_medium.render(tip_text, True, tip_color)
            surface.blit(tip, (pr.centerx - tip.get_width() // 2, pr.bottom - 110))
        elif self.phase == self.PHASE_RESULT:
            bonus_text = ("+%d bonus ingot (smelt XP x%g)" % (self._bonus_amount, self._xp_multiplier)
                          if self._bonus_amount > 0 else "No bonus -- base output only")
            bonus_color = TEXT_GOOD if self._bonus_amount > 0 else TEXT_DIM
            _draw_result_overlay(surface, pr, self._outcome, self._outcome_color,
                                 bonus_text, bonus_color,
                                 self.font_large, self.font_medium, time_ms,
                                 bonus_icons=self._bonus_amount)
            btn_w = 160
            btn_h = 38
            cont = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = cont
            _draw_button(surface, self.font_medium, cont, "Continue",
                         cont.collidepoint(mouse_pos), TEXT_GOLD)