"""
Procedural rendering for majestic peaceful mobs.

Each mob type has its own palette and draw function, following the same
pattern as monster_visuals.py.  All creatures are non-aggressive and
designed to add ambient life and wonder to the world.
"""

from __future__ import annotations

import math
import random as _rnd

import pygame


# ============================================================
# PALETTES
# ============================================================
def _palette_for(style: str) -> dict:
    palettes = {
        "starwhale": {
            # deep celestial body
            "skin": (30, 40, 90), "skin_light": (60, 80, 160), "skin_dark": (15, 20, 50),
            "skin_mid": (45, 60, 130),
            # luminous belly plates
            "belly": (120, 160, 240), "belly_light": (170, 200, 255), "belly_dark": (70, 100, 180),
            # star markings
            "star": (255, 240, 180), "star_bright": (255, 255, 240),
            "star_dim": (200, 190, 140),
            # fins / flukes
            "fin": (40, 60, 140), "fin_light": (80, 110, 200), "fin_dark": (20, 30, 80),
            "fin_accent": (100, 140, 255, 120),
            # eye
            "eye_white": (200, 220, 255), "eye_pupil": (255, 230, 120),
            "eye_glow": (180, 200, 255, 80),
            # trailing stardust
            "dust": (200, 220, 255, 90), "dust_bright": (255, 250, 220, 120),
            "shadow": (0, 0, 0, 40),
        },
        "luminous_deer": {
            # fur base
            "fur": (180, 150, 100), "fur_light": (220, 195, 145), "fur_dark": (120, 95, 60),
            "fur_mid": (200, 175, 125),
            # luminous glow
            "glow": (180, 220, 140, 70), "glow_bright": (220, 255, 180, 100),
            "glow_core": (240, 255, 200),
            # antlers (crystal light)
            "antler": (200, 230, 180), "antler_light": (230, 255, 210),
            "antler_dark": (140, 170, 120), "antler_glow": (200, 255, 160, 100),
            # eyes
            "eye_white": (240, 255, 220), "eye_pupil": (60, 80, 30),
            "eye_ring": (180, 220, 140),
            # hooves
            "hoof": (80, 60, 40), "hoof_light": (120, 95, 65),
            # spots / markings
            "spot": (220, 240, 180, 80),
            "shadow": (0, 0, 0, 40),
        },
        "crystal_serpent": {
            # crystal body segments
            "crystal": (100, 180, 220), "crystal_light": (160, 220, 255),
            "crystal_dark": (50, 110, 160), "crystal_mid": (130, 200, 240),
            # inner glow
            "glow": (180, 230, 255, 80), "glow_bright": (220, 255, 255, 120),
            "glow_core": (240, 255, 255),
            # facets / prism highlights
            "facet": (200, 240, 255, 100), "facet_bright": (255, 255, 255, 140),
            # belly / underside
            "belly": (140, 200, 230), "belly_light": (180, 225, 250),
            # eyes
            "eye_white": (220, 245, 255), "eye_pupil": (40, 120, 180),
            "eye_glow": (150, 220, 255, 90),
            # crystal spines
            "spine": (170, 220, 250), "spine_light": (210, 245, 255),
            "shadow": (0, 0, 0, 40),
        },
        "aurora_moth": {
            # body
            "body": (60, 50, 80), "body_light": (90, 80, 120),
            "body_dark": (35, 28, 50), "body_mid": (75, 65, 100),
            # wing colors (aurora gradient)
            "wing_top": (40, 180, 120), "wing_mid": (80, 140, 220),
            "wing_bot": (180, 60, 200), "wing_edge": (30, 120, 100),
            "wing_shimmer": (120, 220, 180, 100),
            # wing patterns
            "wing_eye": (200, 255, 180), "wing_eye_dark": (80, 160, 100),
            "wing_spot": (255, 200, 140, 80),
            # antennae
            "antenna": (80, 70, 100), "antenna_tip": (180, 255, 200),
            # eye
            "eye_white": (220, 240, 200), "eye_pupil": (30, 20, 40),
            # dust / scales
            "dust": (150, 220, 180, 60), "dust_bright": (200, 255, 220, 80),
            "shadow": (0, 0, 0, 40),
        },
        "grove_titan": {
            # bark / wood body
            "bark": (90, 70, 45), "bark_light": (130, 105, 70),
            "bark_dark": (55, 40, 25), "bark_mid": (110, 88, 58),
            # leaves / canopy
            "leaf": (50, 130, 50), "leaf_light": (80, 175, 70),
            "leaf_dark": (30, 85, 30), "leaf_bright": (100, 200, 80),
            # moss
            "moss": (70, 120, 50), "moss_light": (100, 155, 75),
            # flowers
            "flower": (220, 130, 180), "flower_light": (255, 180, 210),
            "flower_dark": (170, 80, 130),
            # eyes (knot-holes)
            "eye_bg": (30, 25, 15), "eye_glow": (180, 220, 100, 90),
            "eye_pupil": (120, 160, 60),
            # roots / feet
            "root": (70, 50, 30), "root_light": (100, 75, 50),
            "shadow": (0, 0, 0, 40),
        },
        "moon_jelly": {
            # bell / dome
            "bell": (140, 160, 220, 160), "bell_light": (180, 200, 255, 180),
            "bell_dark": (80, 100, 170, 140), "bell_edge": (100, 130, 200, 120),
            # inner glow
            "glow": (180, 200, 255, 60), "glow_bright": (220, 235, 255, 90),
            "glow_core": (240, 245, 255),
            # tentacles
            "tentacle": (120, 150, 220, 100), "tentacle_light": (160, 185, 250, 120),
            "tentacle_bright": (200, 220, 255, 100),
            # bioluminescent spots
            "biolum": (180, 220, 255, 120), "biolum_bright": (220, 245, 255, 160),
            # eye (simple)
            "eye_inner": (200, 220, 255, 180),
            "shadow": (0, 0, 0, 30),
        },
        "prism_fox": {
            # fur
            "fur": (220, 200, 180), "fur_light": (245, 235, 220),
            "fur_dark": (170, 150, 120), "fur_mid": (200, 185, 165),
            # tail tip / ear tips (rainbow refraction)
            "rainbow": (200, 140, 255), "rainbow_alt": (100, 200, 255),
            "rainbow_warm": (255, 180, 120),
            # prism markings
            "prism": (180, 220, 255, 80), "prism_bright": (255, 255, 255, 100),
            # eyes
            "eye_white": (250, 245, 240), "eye_pupil": (140, 80, 40),
            "eye_ring": (200, 160, 255),
            # nose
            "nose": (60, 40, 35),
            # chest / belly
            "chest": (245, 240, 235), "chest_light": (255, 255, 250),
            "shadow": (0, 0, 0, 40),
        },
        "singing_stone": {
            # stone body
            "stone": (150, 140, 130), "stone_light": (190, 182, 172),
            "stone_dark": (100, 92, 85), "stone_mid": (170, 162, 152),
            # moss / lichen
            "moss": (80, 120, 60), "moss_light": (110, 155, 85),
            # crystal embedded in stone
            "crystal": (180, 160, 220), "crystal_light": (220, 200, 255),
            "crystal_glow": (200, 180, 255, 80),
            # rune carvings
            "rune": (200, 180, 130), "rune_glow": (220, 200, 150, 70),
            # eye slits
            "eye_slit": (180, 200, 160), "eye_glow": (200, 230, 140, 90),
            # sound waves (visual)
            "sound": (200, 220, 180, 60), "sound_bright": (230, 250, 200, 80),
            "shadow": (0, 0, 0, 40),
        },
    }
    return palettes.get(style, palettes["starwhale"])


# ============================================================
# HELPER DRAWING FUNCTIONS
# ============================================================

def _draw_ellipse_alpha(surface, color, rect):
    """Draw an ellipse with alpha onto the target surface."""
    if len(color) == 4 and color[3] < 255:
        overlay = pygame.Surface(
            (rect[2], rect[3]), pygame.SRCALPHA
        )
        pygame.draw.ellipse(overlay, color, (0, 0, rect[2], rect[3]))
        surface.blit(overlay, (rect[0], rect[1]), special_flags=pygame.BLEND_ALPHA_SDL2)
    else:
        pygame.draw.ellipse(surface, color, rect)


def _draw_circle_alpha(surface, color, center, radius):
    """Draw a circle with alpha onto the target surface."""
    if len(color) == 4 and color[3] < 255:
        size = radius * 2 + 2
        overlay = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(overlay, color, (size // 2, size // 2), radius)
        surface.blit(overlay, (center[0] - size // 2, center[1] - size // 2),
                     special_flags=pygame.BLEND_ALPHA_SDL2)
    else:
        pygame.draw.circle(surface, color, center, radius)


def _shadow(surface, cx, h, p, bob=0):
    """Draw a soft ground shadow."""
    y = h - 10 + bob
    _draw_ellipse_alpha(surface, p["shadow"], (cx - 18, y, 36, 12))


# ============================================================
# STARWHALE — celestial floating whale with stardust trails
# ============================================================
def _draw_starwhale(s, w, h, cx, cy, p, direction, bob, frame):
    """A majestic celestial whale that drifts serenely, trailing stardust."""
    _shadow(s, cx, h, p, bob)

    # Bobbing offset
    by = bob
    swim = [0, 2, 0, -2][frame]
    tail_flex = [-2, 0, 2, 0][frame]

    # -- stardust trail (behind body) --
    for i in range(6):
        angle = frame * 0.4 + i * 1.05
        dx = int(math.cos(angle) * (18 + i * 6))
        dy = int(math.sin(angle * 0.7) * (8 + i * 3))
        alpha = max(20, 80 - i * 12)
        sz = max(1, 3 - i // 2)
        _draw_circle_alpha(s, (*p["dust"][:3], alpha), (cx - 25 + dx, cy + by + dy), sz)
        _draw_circle_alpha(s, (*p["dust_bright"][:3], alpha // 2),
                           (cx - 30 + dx + 3, cy + by + dy - 2), sz - 1 if sz > 1 else 1)

    # -- tail flukes --
    tail_x = cx - 32
    tail_y = cy + 2 + by + tail_flex
    pygame.draw.polygon(s, p["fin_dark"], [
        (tail_x, tail_y),
        (tail_x - 14, tail_y - 14),
        (tail_x - 6, tail_y),
        (tail_x - 14, tail_y + 12),
    ])
    pygame.draw.polygon(s, p["fin"], [
        (tail_x + 1, tail_y),
        (tail_x - 12, tail_y - 12),
        (tail_x - 5, tail_y),
        (tail_x - 12, tail_y + 10),
    ])
    # tail fin accent
    pygame.draw.polygon(s, p["fin_accent"], [
        (tail_x - 3, tail_y - 5),
        (tail_x - 10, tail_y - 10),
        (tail_x - 5, tail_y - 2),
    ])

    # -- main body (elongated ellipse) --
    bw = int(w * 0.58)
    bh = int(h * 0.38)
    bx = cx - bw // 2 + swim
    by2 = cy - bh // 2 + by
    pygame.draw.ellipse(s, p["skin_dark"], (bx - 1, by2 - 1, bw + 2, bh + 2))
    pygame.draw.ellipse(s, p["skin"], (bx, by2, bw, bh))
    pygame.draw.ellipse(s, p["skin_light"], (bx + 4, by2 + 2, bw // 3, bh - 6))

    # -- belly plates --
    belly_w = int(bw * 0.7)
    belly_h = int(bh * 0.45)
    belly_x = cx - belly_w // 2 + swim
    belly_y = by2 + bh - belly_h - 2
    pygame.draw.ellipse(s, p["belly_dark"], (belly_x, belly_y, belly_w, belly_h))
    pygame.draw.ellipse(s, p["belly"], (belly_x + 2, belly_y + 2, belly_w - 4, belly_h - 4))
    pygame.draw.ellipse(s, p["belly_light"], (belly_x + 4, belly_y + 3, belly_w // 2, belly_h - 6))
    # plate lines
    for i in range(3):
        ly = belly_y + 4 + i * (belly_h // 4)
        pygame.draw.line(s, p["belly_dark"], (belly_x + 4, ly), (belly_x + belly_w - 4, ly), 1)

    # -- pectoral fins --
    for side in (-1, 1):
        fin_cx = cx + side * (bw // 2 - 4) + swim
        fin_cy = by2 + int(bh * 0.6)
        fin_pts = [
            (fin_cx, fin_cy),
            (fin_cx + side * 12, fin_cy + 8 + swim),
            (fin_cx + side * 18, fin_cy + 3),
            (fin_cx + side * 10, fin_cy - 2),
        ]
        pygame.draw.polygon(s, p["fin_dark"], fin_pts)
        pygame.draw.polygon(s, p["fin"], [
            (fin_cx + 1, fin_cy + 1),
            (fin_cx + side * 11, fin_cy + 7 + swim),
            (fin_cx + side * 16, fin_cy + 3),
            (fin_cx + side * 9, fin_cy - 1),
        ])

    # -- dorsal ridge --
    for i in range(5):
        rx = bx + 10 + i * (bw - 20) // 4
        ry = by2 - 2
        rh = 3 + (2 if i == 2 else 0)
        pygame.draw.polygon(s, p["fin_dark"], [(rx, ry), (rx - 2, ry - rh), (rx + 2, ry - rh)])
        pygame.draw.polygon(s, p["fin"], [(rx, ry - 1), (rx - 1, ry - rh + 1), (rx + 1, ry - rh + 1)])

    # -- star markings on body --
    for i in range(4):
        sx = bx + 10 + i * (bw - 20) // 3
        sy = by2 + int(bh * 0.3) + ([0, 2, -1, 1][i])
        pulse = 1 if (frame + i) % 3 == 0 else 0
        _draw_circle_alpha(s, (*p["star"][:3], 150 + pulse * 50), (sx, sy + by), 2 + pulse)
        _draw_circle_alpha(s, (*p["star_bright"][:3], 100), (sx, sy + by), 4 + pulse)
        # small star rays
        for angle_off in [0, 1.57, 3.14, 4.71]:
            ex = sx + int(math.cos(angle_off + frame * 0.2) * 4)
            ey = sy + by + int(math.sin(angle_off + frame * 0.2) * 4)
            pygame.draw.line(s, (*p["star"][:3], 80), (sx, sy + by), (ex, ey), 1)

    # -- head / eye --
    head_x = cx + bw // 2 - 6 + swim
    head_y = cy + by - 2
    # eye
    _draw_circle_alpha(s, p["eye_glow"], (head_x + 2, head_y), 8)
    _draw_circle_alpha(s, p["eye_white"], (head_x + 2, head_y), 5)
    _draw_circle_alpha(s, p["eye_pupil"], (head_x + 3, head_y), 3)
    _draw_circle_alpha(s, (255, 255, 255, 150), (head_x + 4, head_y - 1), 1)

    # mouth line
    pygame.draw.arc(s, p["skin_dark"], (head_x - 8, head_y + 2, 16, 8), 0.3, 2.8, 1)

    # -- barnacles / detail --
    for i in range(3):
        bx2 = bx + 8 + i * 12
        by3 = by2 + bh // 2 + 2
        _draw_circle_alpha(s, (*p["belly"][:3], 80), (bx2, by3), 2)

    # -- extra glow aura --
    aura = pygame.Surface((w, h), pygame.SRCALPHA)
    pulse_r = int(w * 0.38) + (frame % 2) * 3
    _draw_circle_alpha(aura, (*p["dust"][:3], 25), (cx + swim, cy + by), pulse_r)
    s.blit(aura, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)


# ============================================================
# LUMINOUS DEER — glowing forest deer with crystal antlers
# ============================================================
def _draw_luminous_deer(s, w, h, cx, cy, p, direction, bob, frame):
    """A serene forest deer whose antlers glow with crystallized light."""
    _shadow(s, cx, h, p, bob)
    walk = [0, 1, 0, -1][frame]
    head_bob = [0, -1, 0, 1][frame]

    # -- ground glow aura --
    aura = pygame.Surface((w, h), pygame.SRCALPHA)
    _draw_ellipse_alpha(aura, p["glow"], (cx - 25, h - 18 + bob, 50, 14))
    s.blit(aura, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # -- legs --
    leg_y = int(h * 0.62)
    for lx, off in [(cx - 10 + walk, walk), (cx + 4 - walk, -walk)]:
        # upper leg
        pygame.draw.rect(s, p["fur_dark"], (lx, leg_y + bob, 7, 16), border_radius=2)
        pygame.draw.rect(s, p["fur"], (lx + 1, leg_y + bob + 1, 5, 14), border_radius=1)
        # lower leg
        pygame.draw.rect(s, p["fur_dark"], (lx + 1, leg_y + 14 + bob, 5, 10), border_radius=1)
        # hoof
        pygame.draw.rect(s, p["hoof"], (lx, leg_y + 22 + bob, 7, 4), border_radius=1)
        pygame.draw.rect(s, p["hoof_light"], (lx + 1, leg_y + 22 + bob, 5, 2), border_radius=1)
        # glow at ankle
        _draw_circle_alpha(s, (*p["glow"][:3], 40), (lx + 3, leg_y + 14 + bob), 4)

    # -- body --
    bw = int(w * 0.44)
    bh = int(h * 0.30)
    bx = cx - bw // 2
    by = int(h * 0.32) + bob
    pygame.draw.ellipse(s, p["fur_dark"], (bx - 1, by - 1, bw + 2, bh + 2))
    pygame.draw.ellipse(s, p["fur"], (bx, by, bw, bh))
    pygame.draw.ellipse(s, p["fur_light"], (bx + 3, by + 3, bw // 3, bh - 6))

    # -- luminous spots --
    for i in range(5):
        sx = bx + 6 + i * (bw - 12) // 4
        sy = by + 4 + ([0, 3, -1, 2, -2][i])
        pulse = 1 if (frame + i) % 2 == 0 else 0
        _draw_circle_alpha(s, (*p["spot"][:3], 60 + pulse * 30), (sx, sy), 3 + pulse)

    # -- neck --
    neck_x = cx + bw // 2 - 6
    neck_y = by - 4
    pygame.draw.polygon(s, p["fur_dark"], [
        (neck_x - 5, neck_y + 8), (neck_x + 5, neck_y + 8),
        (neck_x + 3, neck_y - 6), (neck_x - 3, neck_y - 6),
    ])
    pygame.draw.polygon(s, p["fur"], [
        (neck_x - 4, neck_y + 7), (neck_x + 4, neck_y + 7),
        (neck_x + 2, neck_y - 4), (neck_x - 2, neck_y - 4),
    ])

    # -- head --
    hr = int(w * 0.13)
    hx = neck_x
    hy = neck_y - 8 + head_bob
    pygame.draw.ellipse(s, p["fur_dark"], (hx - hr - 1, hy - hr // 2 - 1, hr * 2 + 2, hr + 2))
    pygame.draw.ellipse(s, p["fur"], (hx - hr, hy - hr // 2, hr * 2, hr))
    pygame.draw.ellipse(s, p["fur_light"], (hx - hr + 2, hy - hr // 2 + 1, hr, hr - 3))

    # -- ears --
    for side in (-1, 1):
        ear_x = hx + side * (hr - 1)
        ear_y = hy - 6
        pygame.draw.polygon(s, p["fur_dark"], [
            (ear_x, ear_y), (ear_x + side * 4, ear_y - 10), (ear_x + side * 7, ear_y - 4)
        ])
        pygame.draw.polygon(s, p["fur"], [
            (ear_x + 1, ear_y - 1), (ear_x + side * 4, ear_y - 8), (ear_x + side * 6, ear_y - 4)
        ])
        # inner ear glow
        _draw_circle_alpha(s, (*p["glow"][:3], 50), (ear_x + side * 3, ear_y - 5), 3)

    # -- crystal antlers (the signature feature) --
    for side in (-1, 1):
        base_x = hx + side * (hr // 2)
        base_y = hy - hr // 2 - 1
        # main branch
        tip_x = base_x + side * 14
        tip_y = base_y - 18
        pygame.draw.line(s, p["antler_dark"], (base_x, base_y), (tip_x, tip_y), 3)
        pygame.draw.line(s, p["antler"], (base_x, base_y), (tip_x, tip_y), 2)
        # side branch
        br_x = base_x + side * 8
        br_y = base_y - 10
        pygame.draw.line(s, p["antler_dark"], (br_x, br_y), (br_x + side * 8, br_y - 8), 2)
        pygame.draw.line(s, p["antler"], (br_x, br_y), (br_x + side * 8, br_y - 8), 1)
        # crystal tips glow
        _draw_circle_alpha(s, (*p["antler_glow"][:3], 80 + (frame % 2) * 30), (tip_x, tip_y), 4)
        _draw_circle_alpha(s, (*p["antler_glow"][:3], 50), (br_x + side * 8, br_y - 8), 3)
        # glow aura around antlers
        _draw_circle_alpha(s, (*p["antler_glow"][:3], 25), (base_x + side * 7, base_y - 8), 10)

    # -- eyes --
    esp = 4
    for ex in (hx - esp, hx + esp):
        _draw_circle_alpha(s, p["eye_ring"], (ex, hy), 5)
        _draw_circle_alpha(s, p["eye_white"], (ex, hy), 3)
        _draw_circle_alpha(s, p["eye_pupil"], (ex, hy), 2)
        _draw_circle_alpha(s, (255, 255, 255, 180), (ex - 1, hy - 1), 1)

    # -- tail --
    tail_x = bx - 2
    tail_y = by + bh // 2
    tail_wag = [0, 3, 0, -3][frame]
    pygame.draw.ellipse(s, p["fur_dark"], (tail_x - 4 + tail_wag, tail_y - 4, 10, 8))
    pygame.draw.ellipse(s, p["fur_light"], (tail_x - 2 + tail_wag, tail_y - 3, 6, 6))
    _draw_circle_alpha(s, (*p["glow"][:3], 40), (tail_x + tail_wag, tail_y), 5)


# ============================================================
# CRYSTAL SERPENT — gentle serpentine creature of living crystal
# ============================================================
def _draw_crystal_serpent(s, w, h, cx, cy, p, direction, bob, frame):
    """A gentle serpentine creature made of living crystal, refracting light."""
    _shadow(s, cx, h, p, bob)
    sway = [0, 3, 0, -3][frame]
    coil = [0, 1, 0, -1][frame]

    # -- body coils (3 segments, overlapping) --
    segments = []
    for i in range(5):
        seg_x = cx + int(math.sin(frame * 0.8 + i * 1.2) * (12 - i * 2))
        seg_y = cy + int(i * (h * 0.12)) + bob
        seg_r = int(w * 0.18) - i * 2
        segments.append((seg_x, seg_y, max(seg_r, 4)))

    # draw back to front
    for i in range(len(segments) - 1, -1, -1):
        sx, sy, sr = segments[i]
        # crystal segment body
        _draw_circle_alpha(s, p["crystal_dark"], (sx + sway // 2, sy), sr + 1)
        _draw_circle_alpha(s, p["crystal"], (sx + sway // 2, sy), sr)
        _draw_circle_alpha(s, p["crystal_light"], (sx + sway // 2 - 1, sy - 1), sr - 2 if sr > 3 else 1)
        # facet highlights
        facet_angle = frame * 0.5 + i * 1.0
        fx = sx + int(math.cos(facet_angle) * (sr - 2))
        fy = sy + int(math.sin(facet_angle) * (sr - 2))
        _draw_circle_alpha(s, p["facet"], (fx + sway // 2, fy), 2)
        if (frame + i) % 3 == 0:
            _draw_circle_alpha(s, p["facet_bright"], (fx + sway // 2, fy), 1)
        # inner glow
        _draw_circle_alpha(s, (*p["glow"][:3], 40), (sx + sway // 2, sy), sr + 4)

    # -- crystal spines along the back --
    for i in range(0, len(segments) - 1):
        sx, sy, sr = segments[i]
        spine_angle = -math.pi / 2 + math.sin(frame * 0.3 + i) * 0.3
        for j in range(2):
            sa = spine_angle + j * 0.4 - 0.2
            sp_x = sx + int(math.cos(sa) * sr)
            sp_y = sy + int(math.sin(sa) * sr)
            sp_tip_x = sp_x + int(math.cos(sa) * 6)
            sp_tip_y = sp_y + int(math.sin(sa) * 6)
            pygame.draw.line(s, p["spine"], (sp_x + sway // 2, sp_y),
                             (sp_tip_x + sway // 2, sp_tip_y), 2)
            _draw_circle_alpha(s, (*p["glow_bright"][:3], 60),
                               (sp_tip_x + sway // 2, sp_tip_y), 2)

    # -- head --
    head_seg = segments[0]
    hx, hy, hr = head_seg[0], head_seg[1], head_seg[2]
    # eye glow
    for side in (-1, 1):
        ex = hx + side * (hr // 2) + sway // 2
        ey = hy - 2
        _draw_circle_alpha(s, p["eye_glow"], (ex, ey), 5)
        _draw_circle_alpha(s, p["eye_white"], (ex, ey), 3)
        _draw_circle_alpha(s, p["eye_pupil"], (ex, ey), 2)
        _draw_circle_alpha(s, (255, 255, 255, 180), (ex, ey - 1), 1)

    # -- trailing sparkle particles --
    for i in range(4):
        angle = frame * 0.6 + i * 1.57
        last_seg = segments[-1]
        px = last_seg[0] + int(math.cos(angle) * 10)
        py = last_seg[1] + int(math.sin(angle) * 8) + i * 3
        alpha = max(20, 80 - i * 15)
        _draw_circle_alpha(s, (*p["glow_bright"][:3], alpha), (px + sway // 2, py), 2)


# ============================================================
# AURORA MOTH — massive moth with wings displaying aurora colors
# ============================================================
def _draw_aurora_moth(s, w, h, cx, cy, p, direction, bob, frame):
    """A massive ethereal moth whose wings shimmer with aurora borealis colors."""
    _shadow(s, cx, h, p, bob)
    wing_flap = [0, 4, 0, -4][frame]
    antenna_sway = [0, 2, 0, -2][frame]

    # -- wing aura glow --
    aura = pygame.Surface((w, h), pygame.SRCALPHA)
    _draw_ellipse_alpha(aura, (*p["wing_shimmer"][:3], 30),
                        (cx - w // 2, cy - h // 2 + bob, w, h))
    s.blit(aura, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # -- wings (4 wings: upper pair larger, lower pair smaller) --
    for side in (-1, 1):
        # Upper wing
        uw_x = cx + side * 4
        uw_y = cy - 2 + bob
        uw_pts = [
            (uw_x, uw_y),
            (uw_x + side * (28 + wing_flap), uw_y - 16),
            (uw_x + side * (34 + wing_flap), uw_y - 4),
            (uw_x + side * (26 + wing_flap), uw_y + 10),
            (uw_x + side * 8, uw_y + 8),
        ]
        # wing gradient layers
        pygame.draw.polygon(s, p["wing_edge"], uw_pts)
        uw_inner = [
            (uw_x + side * 3, uw_y - 1),
            (uw_x + side * (24 + wing_flap), uw_y - 13),
            (uw_x + side * (28 + wing_flap), uw_y - 3),
            (uw_x + side * (22 + wing_flap), uw_y + 7),
            (uw_x + side * 8, uw_y + 6),
        ]
        pygame.draw.polygon(s, p["wing_top"], uw_inner)
        # mid section
        uw_mid = [
            (uw_x + side * 6, uw_y),
            (uw_x + side * (18 + wing_flap), uw_y - 8),
            (uw_x + side * (20 + wing_flap), uw_y),
            (uw_x + side * (14 + wing_flap), uw_y + 5),
            (uw_x + side * 8, uw_y + 3),
        ]
        pygame.draw.polygon(s, p["wing_mid"], uw_mid)
        # wing eye spot
        spot_cx = uw_x + side * (18 + wing_flap)
        spot_cy = uw_y - 4
        _draw_circle_alpha(s, p["wing_eye_dark"], (spot_cx, spot_cy), 5)
        _draw_circle_alpha(s, p["wing_eye"], (spot_cx, spot_cy), 3)
        pulse = 1 if frame % 2 == 0 else 0
        _draw_circle_alpha(s, (*p["wing_shimmer"][:3], 80 + pulse * 40), (spot_cx, spot_cy), 6)

        # wing veins
        for vi in range(3):
            vx_end = uw_x + side * (12 + vi * 8 + wing_flap)
            vy_end = uw_y - 10 + vi * 6
            pygame.draw.line(s, (*p["wing_edge"][:3],), (uw_x + side * 2, uw_y),
                             (vx_end, vy_end), 1)

        # Lower wing (smaller)
        lw_x = cx + side * 3
        lw_y = cy + 6 + bob
        lw_pts = [
            (lw_x, lw_y),
            (lw_x + side * (20 - wing_flap), lw_y + 2),
            (lw_x + side * (22 - wing_flap), lw_y + 14),
            (lw_x + side * (12 - wing_flap), lw_y + 16),
            (lw_x + side * 4, lw_y + 8),
        ]
        pygame.draw.polygon(s, p["wing_edge"], lw_pts)
        lw_inner = [
            (lw_x + side * 2, lw_y + 1),
            (lw_x + side * (17 - wing_flap), lw_y + 3),
            (lw_x + side * (18 - wing_flap), lw_y + 12),
            (lw_x + side * (10 - wing_flap), lw_y + 14),
            (lw_x + side * 5, lw_y + 7),
        ]
        pygame.draw.polygon(s, p["wing_bot"], lw_inner)
        # lower wing spot
        ls_cx = lw_x + side * (12 - wing_flap)
        ls_cy = lw_y + 8
        _draw_circle_alpha(s, p["wing_eye_dark"], (ls_cx, ls_cy), 3)
        _draw_circle_alpha(s, p["wing_eye"], (ls_cx, ls_cy), 2)

    # -- body (fuzzy thorax + abdomen) --
    body_y = cy - 4 + bob
    # thorax
    pygame.draw.ellipse(s, p["body_dark"], (cx - 5, body_y - 1, 10, 12))
    pygame.draw.ellipse(s, p["body"], (cx - 4, body_y, 8, 10))
    pygame.draw.ellipse(s, p["body_light"], (cx - 2, body_y + 1, 4, 6))
    # abdomen (longer, segmented)
    for seg in range(3):
        seg_y = body_y + 10 + seg * 5
        seg_w = 6 - seg
        pygame.draw.ellipse(s, p["body_dark"], (cx - seg_w // 2 - 1, seg_y - 1, seg_w + 2, 6))
        pygame.draw.ellipse(s, p["body_mid"], (cx - seg_w // 2, seg_y, seg_w, 5))

    # -- fuzzy texture on thorax --
    for fi in range(4):
        fx = cx - 3 + fi * 2
        fy = body_y + 2 + (fi % 2)
        _draw_circle_alpha(s, (*p["body_light"][:3], 80), (fx, fy), 1)

    # -- head --
    hy = body_y - 4
    _draw_circle_alpha(s, p["body_dark"], (cx, hy), 5)
    _draw_circle_alpha(s, p["body"], (cx, hy), 4)
    # eyes
    for side in (-1, 1):
        ex = cx + side * 3
        _draw_circle_alpha(s, p["eye_white"], (ex, hy - 1), 2)
        _draw_circle_alpha(s, p["eye_pupil"], (ex, hy - 1), 1)

    # -- antennae (feathery) --
    for side in (-1, 1):
        base_x = cx + side * 2
        base_y = hy - 3
        tip_x = base_x + side * (8 + antenna_sway)
        tip_y = base_y - 12
        pygame.draw.line(s, p["antenna"], (base_x, base_y), (tip_x, tip_y), 1)
        # feathery barbs
        for bi in range(4):
            bx2 = base_x + int((tip_x - base_x) * bi / 4)
            by2 = base_y + int((tip_y - base_y) * bi / 4)
            pygame.draw.line(s, p["antenna"], (bx2, by2),
                             (bx2 + side * 3, by2 - 2), 1)
        # glowing tips
        _draw_circle_alpha(s, (*p["antenna_tip"][:3], 120), (tip_x, tip_y), 2)
        _draw_circle_alpha(s, (*p["antenna_tip"][:3], 50), (tip_x, tip_y), 4)

    # -- trailing dust particles --
    for i in range(5):
        angle = frame * 0.5 + i * 1.26
        dx = int(math.cos(angle) * (10 + i * 4))
        dy = int(math.sin(angle * 0.6) * (6 + i * 3))
        alpha = max(15, 60 - i * 10)
        _draw_circle_alpha(s, (*p["dust"][:3], alpha), (cx + dx, cy + bob + 20 + dy), 2)
        if i % 2 == 0:
            _draw_circle_alpha(s, (*p["dust_bright"][:3], alpha // 2),
                               (cx + dx + 2, cy + bob + 20 + dy - 1), 1)


# ============================================================
# GROVE TITAN — small friendly tree creature that walks slowly
# ============================================================
def _draw_grove_titan(s, w, h, cx, cy, p, direction, bob, frame):
    """A small, gentle tree-like creature that waddles and hums."""
    _shadow(s, cx, h, p, bob)
    walk = [0, 1, 0, -1][frame]
    sway = [0, 2, 0, -2][frame]

    # -- root feet --
    for side in (-1, 1):
        foot_x = cx + side * 8 + walk * side
        foot_y = h - 14 + bob
        # root toes
        for t in range(3):
            tx = foot_x + (t - 1) * 4
            pygame.draw.line(s, p["root"], (foot_x, foot_y + 4), (tx, foot_y + 10), 3)
            pygame.draw.line(s, p["root_light"], (foot_x, foot_y + 5), (tx, foot_y + 9), 1)
        # ankle
        pygame.draw.ellipse(s, p["bark_dark"], (foot_x - 4, foot_y, 8, 6))
        pygame.draw.ellipse(s, p["bark"], (foot_x - 3, foot_y + 1, 6, 4))

    # -- trunk body --
    bw = int(w * 0.40)
    bh = int(h * 0.42)
    bx = cx - bw // 2 + sway
    by = int(h * 0.30) + bob
    # trunk shape (slightly tapered)
    trunk_pts = [
        (bx + 3, by), (bx + bw - 3, by),
        (bx + bw, by + bh), (bx, by + bh),
    ]
    pygame.draw.polygon(s, p["bark_dark"], trunk_pts)
    inner_pts = [
        (bx + 5, by + 2), (bx + bw - 5, by + 2),
        (bx + bw - 2, by + bh - 2), (bx + 2, by + bh - 2),
    ]
    pygame.draw.polygon(s, p["bark"], inner_pts)
    pygame.draw.polygon(s, p["bark_light"], [
        (bx + 7, by + 3), (bx + bw // 2, by + 3),
        (bx + bw // 2 - 2, by + bh - 4), (bx + 5, by + bh - 4),
    ])

    # bark texture lines
    for i in range(4):
        ly = by + 6 + i * (bh // 5)
        pygame.draw.line(s, p["bark_dark"], (bx + 5, ly), (bx + bw - 5, ly + 2), 1)

    # -- moss patches --
    for mx, my in [(bx + 4, by + bh - 8), (bx + bw - 10, by + 10), (bx + bw // 2, by + bh - 4)]:
        _draw_ellipse_alpha(s, p["moss"], (mx + sway, my, 8, 4))
        _draw_ellipse_alpha(s, p["moss_light"], (mx + 1 + sway, my + 1, 5, 2))

    # -- canopy / leaves on top --
    canopy_y = by - 8
    leaf_clusters = [
        (cx + sway, canopy_y, 14),
        (cx - 10 + sway, canopy_y + 4, 10),
        (cx + 10 + sway, canopy_y + 4, 10),
        (cx - 5 + sway, canopy_y - 4, 8),
        (cx + 5 + sway, canopy_y - 4, 8),
    ]
    for lx, ly, lr in leaf_clusters:
        _draw_circle_alpha(s, p["leaf_dark"], (lx, ly), lr)
        _draw_circle_alpha(s, p["leaf"], (lx, ly), lr - 2)
        _draw_circle_alpha(s, p["leaf_light"], (lx - 1, ly - 1), lr - 4 if lr > 5 else 2)

    # -- flowers on canopy --
    flower_positions = [(cx - 8 + sway, canopy_y - 2), (cx + 6 + sway, canopy_y + 2),
                        (cx + sway, canopy_y - 6)]
    for fx, fy in flower_positions:
        pulse = 1 if (frame + fx) % 3 == 0 else 0
        _draw_circle_alpha(s, p["flower_dark"], (fx, fy), 3)
        _draw_circle_alpha(s, p["flower"], (fx, fy), 2 + pulse)
        _draw_circle_alpha(s, p["flower_light"], (fx, fy - 1), 1)

    # -- face (knot-hole eyes) --
    face_x = cx + sway
    face_y = by + int(bh * 0.25)
    # eyes
    for side in (-1, 1):
        ex = face_x + side * 7
        ey = face_y
        _draw_circle_alpha(s, p["eye_bg"], (ex, ey), 4)
        _draw_circle_alpha(s, p["eye_glow"], (ex, ey), 3)
        _draw_circle_alpha(s, p["eye_pupil"], (ex, ey), 2)
        blink = frame % 4 == 0
        if blink:
            pygame.draw.line(s, p["bark"], (ex - 3, ey), (ex + 3, ey), 2)

    # mouth (gentle curve)
    mouth_y = face_y + 7
    pygame.draw.arc(s, p["eye_bg"], (face_x - 5, mouth_y - 2, 10, 6), 3.5, 5.9, 1)

    # -- small arms (stubby branches) --
    for side in (-1, 1):
        arm_x = bx + (0 if side < 0 else bw)
        arm_y = by + int(bh * 0.35) + bob
        hand_x = arm_x + side * (8 + walk)
        hand_y = arm_y + 6
        pygame.draw.line(s, p["bark_dark"], (arm_x, arm_y), (hand_x, hand_y), 4)
        pygame.draw.line(s, p["bark"], (arm_x, arm_y + 1), (hand_x, hand_y), 2)
        # leaf on hand
        _draw_circle_alpha(s, p["leaf"], (hand_x, hand_y), 3)
        _draw_circle_alpha(s, p["leaf_light"], (hand_x, hand_y), 2)

    # -- floating leaf particles --
    for i in range(3):
        angle = frame * 0.3 + i * 2.1
        lx = cx + int(math.cos(angle) * 18)
        ly = cy + int(math.sin(angle) * 12) + bob
        _draw_circle_alpha(s, (*p["leaf_bright"][:3], 60), (lx, ly), 2)


# ============================================================
# MOON JELLYFISH — ethereal floating jellyfish with moonlight glow
# ============================================================
def _draw_moon_jelly(s, w, h, cx, cy, p, direction, bob, frame):
    """An ethereal floating jellyfish that glows with soft moonlight."""
    _shadow(s, cx, h, p, bob)
    pulse = [0, 2, 0, -2][frame]
    tentacle_sway = [0, 3, 0, -3][frame]

    # -- main glow aura --
    aura = pygame.Surface((w, h), pygame.SRCALPHA)
    aura_r = int(w * 0.40) + pulse
    _draw_circle_alpha(aura, (*p["glow"][:3], 35), (cx, cy + bob), aura_r)
    s.blit(aura, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # -- tentacles (drawn first, behind bell) --
    tentacle_base_y = cy + 6 + bob
    for i in range(6):
        tx_base = cx - 15 + i * 6
        sway_off = int(math.sin(frame * 0.8 + i * 0.9) * (4 + tentacle_sway))
        tx_end = tx_base + sway_off
        ty_end = tentacle_base_y + 18 + i * 2
        # wavy tentacle using line segments
        points = []
        segments = 5
        for seg in range(segments + 1):
            t = seg / segments
            px = tx_base + int(sway_off * t)
            py = tentacle_base_y + int((ty_end - tentacle_base_y) * t)
            px += int(math.sin(frame * 1.2 + i + seg * 0.8) * 3 * t)
            points.append((px, py))
        if len(points) >= 2:
            alpha = 80 + (i % 2) * 30
            color = p["tentacle"] if i % 2 == 0 else p["tentacle_light"]
            for j in range(len(points) - 1):
                pygame.draw.line(s, (*color[:3], alpha), points[j], points[j + 1], 2)
            # bright tip
            _draw_circle_alpha(s, (*p["tentacle_bright"][:3], alpha // 2), points[-1], 2)

    # -- bell / dome --
    bell_w = int(w * 0.52)
    bell_h = int(h * 0.34)
    bell_x = cx - bell_w // 2
    bell_y = cy - bell_h // 2 + bob + pulse

    # outer glow
    _draw_ellipse_alpha(s, (*p["bell_edge"][:3], 80),
                        (bell_x - 4, bell_y - 2, bell_w + 8, bell_h + 6))
    # main bell
    _draw_ellipse_alpha(s, p["bell_dark"], (bell_x - 1, bell_y, bell_w + 2, bell_h + 2))
    _draw_ellipse_alpha(s, p["bell"], (bell_x, bell_y + 1, bell_w, bell_h))
    _draw_ellipse_alpha(s, p["bell_light"],
                        (bell_x + 4, bell_y + 2, bell_w // 3, bell_h - 4))

    # inner glow rings
    for ring_i in range(3):
        ring_r = bell_w // 3 - ring_i * 4
        if ring_r > 2:
            _draw_ellipse_alpha(s, (*p["glow_bright"][:3], 40 - ring_i * 10),
                                (cx - ring_r // 2, cy + bob - ring_r // 4 + pulse,
                                 ring_r, ring_r // 2))

    # -- bioluminescent spots on bell --
    spot_positions = [
        (cx - 8, cy - 6 + bob + pulse), (cx + 8, cy - 6 + bob + pulse),
        (cx, cy - 10 + bob + pulse), (cx - 4, cy + bob + pulse),
        (cx + 4, cy + bob + pulse),
    ]
    for sx, sy in spot_positions:
        bright = 1 if (frame + sx) % 3 == 0 else 0
        _draw_circle_alpha(s, p["biolum"], (sx, sy), 3 + bright)
        _draw_circle_alpha(s, p["biolum_bright"], (sx, sy), 2)

    # -- frilly bell margin --
    for i in range(8):
        mx = bell_x + 2 + i * (bell_w - 4) // 7
        my = bell_y + bell_h - 2
        frill = [0, 2, 0, -2][(frame + i) % 4]
        pygame.draw.ellipse(s, (*p["bell_edge"][:3], 70),
                            (mx - 2, my + frill - 1, 5, 4))

    # -- simple eye-like spots --
    for side in (-1, 1):
        ex = cx + side * 6
        ey = cy - 4 + bob + pulse
        _draw_circle_alpha(s, p["eye_inner"], (ex, ey), 3)
        _draw_circle_alpha(s, (*p["glow_bright"][:3], 120), (ex, ey), 2)


# ============================================================
# PRISM FOX — elegant fox that refracts light into rainbows
# ============================================================
def _draw_prism_fox(s, w, h, cx, cy, p, direction, bob, frame):
    """An elegant fox-like creature whose fur refracts light into rainbows."""
    _shadow(s, cx, h, p, bob)
    walk = [0, 1, 0, -1][frame]
    tail_wag = [0, 4, 0, -4][frame]

    # -- tail (large, fluffy) --
    tail_x = cx - 18
    tail_y = cy + 4 + bob
    # tail shape
    tail_pts = [
        (tail_x, tail_y),
        (tail_x - 14 + tail_wag, tail_y - 10),
        (tail_x - 20 + tail_wag, tail_y - 16),
        (tail_x - 16 + tail_wag, tail_y - 20),
        (tail_x - 8, tail_y - 12),
    ]
    pygame.draw.polygon(s, p["fur_dark"], tail_pts)
    tail_inner = [
        (tail_x + 1, tail_y + 1),
        (tail_x - 12 + tail_wag, tail_y - 8),
        (tail_x - 17 + tail_wag, tail_y - 14),
        (tail_x - 14 + tail_wag, tail_y - 17),
        (tail_x - 8, tail_y - 10),
    ]
    pygame.draw.polygon(s, p["fur"], tail_inner)
    # rainbow tip
    tip_x = tail_x - 18 + tail_wag
    tip_y = tail_y - 18
    _draw_circle_alpha(s, p["rainbow"], (tip_x, tip_y), 5)
    _draw_circle_alpha(s, p["rainbow_alt"], (tip_x - 2, tip_y + 2), 3)
    _draw_circle_alpha(s, p["rainbow_warm"], (tip_x + 2, tip_y - 1), 3)
    # prism glow on tail
    _draw_circle_alpha(s, (*p["prism"][:3], 40), (tail_x - 10 + tail_wag, tail_y - 12), 8)

    # -- hind legs --
    for side in (-1, 1):
        lx = cx + side * 6 - 2
        ly = int(h * 0.62) + bob
        pygame.draw.rect(s, p["fur_dark"], (lx, ly, 6, 14), border_radius=2)
        pygame.draw.rect(s, p["fur"], (lx + 1, ly + 1, 4, 12), border_radius=1)
        pygame.draw.rect(s, p["fur_light"], (lx + 1, ly + 1, 2, 8), border_radius=1)
        # paw
        pygame.draw.ellipse(s, p["fur_dark"], (lx - 1, ly + 12, 8, 4))

    # -- body --
    bw = int(w * 0.44)
    bh = int(h * 0.28)
    bx = cx - bw // 2 + 2
    by = int(h * 0.36) + bob
    pygame.draw.ellipse(s, p["fur_dark"], (bx - 1, by - 1, bw + 2, bh + 2))
    pygame.draw.ellipse(s, p["fur"], (bx, by, bw, bh))
    pygame.draw.ellipse(s, p["fur_light"], (bx + 3, by + 3, bw // 3, bh - 6))

    # -- prism markings on fur --
    for i in range(3):
        mx = bx + 8 + i * (bw - 16) // 2
        my = by + bh // 2
        pulse = 1 if (frame + i) % 2 == 0 else 0
        _draw_circle_alpha(s, (*p["prism"][:3], 50 + pulse * 30), (mx, my), 3 + pulse)
        # rainbow refraction lines
        for j, color_key in enumerate(["rainbow", "rainbow_alt", "rainbow_warm"]):
            angle = frame * 0.3 + j * 1.05
            lx2 = mx + int(math.cos(angle) * 5)
            ly2 = my + int(math.sin(angle) * 4)
            _draw_circle_alpha(s, (*p[color_key][:3], 30), (lx2, ly2), 2)

    # -- front legs --
    for side in (-1, 1):
        lx = cx + side * 8 + 2
        ly = int(h * 0.52) + bob
        leg_walk = walk * side
        pygame.draw.rect(s, p["fur_dark"], (lx + leg_walk, ly, 6, 18), border_radius=2)
        pygame.draw.rect(s, p["fur"], (lx + 1 + leg_walk, ly + 1, 4, 16), border_radius=1)
        pygame.draw.rect(s, p["fur_light"], (lx + 1 + leg_walk, ly + 1, 2, 10), border_radius=1)
        pygame.draw.ellipse(s, p["fur_dark"], (lx - 1 + leg_walk, ly + 16, 8, 4))

    # -- chest / belly --
    chest_x = cx
    chest_y = by + bh - 2
    _draw_ellipse_alpha(s, p["chest"], (chest_x - 6, chest_y - 3, 12, 8))
    _draw_ellipse_alpha(s, p["chest_light"], (chest_x - 4, chest_y - 2, 8, 5))

    # -- neck --
    neck_x = cx + 8
    neck_y = by - 2
    pygame.draw.polygon(s, p["fur_dark"], [
        (neck_x - 4, neck_y + 6), (neck_x + 4, neck_y + 6),
        (neck_x + 3, neck_y - 4), (neck_x - 3, neck_y - 4),
    ])
    pygame.draw.polygon(s, p["fur"], [
        (neck_x - 3, neck_y + 5), (neck_x + 3, neck_y + 5),
        (neck_x + 2, neck_y - 2), (neck_x - 2, neck_y - 2),
    ])

    # -- head --
    hr = int(w * 0.14)
    hx = neck_x + 2
    hy = neck_y - 6
    # head shape (slightly pointed)
    pygame.draw.ellipse(s, p["fur_dark"], (hx - hr - 1, hy - hr // 2 - 1, hr * 2 + 2, hr + 2))
    pygame.draw.ellipse(s, p["fur"], (hx - hr, hy - hr // 2, hr * 2, hr))
    pygame.draw.ellipse(s, p["fur_light"], (hx - hr + 2, hy - hr // 2 + 1, hr, hr - 3))

    # -- ears --
    for side in (-1, 1):
        ear_x = hx + side * (hr - 2)
        ear_y = hy - 4
        pygame.draw.polygon(s, p["fur_dark"], [
            (ear_x, ear_y), (ear_x + side * 3, ear_y - 12), (ear_x + side * 7, ear_y - 3)
        ])
        pygame.draw.polygon(s, p["fur"], [
            (ear_x + 1, ear_y - 1), (ear_x + side * 3, ear_y - 10), (ear_x + side * 6, ear_y - 3)
        ])
        # rainbow ear tip
        _draw_circle_alpha(s, p["rainbow"], (ear_x + side * 3, ear_y - 10), 2)

    # -- snout --
    snout_x = hx + hr - 1
    snout_y = hy + 2
    pygame.draw.ellipse(s, p["fur"], (snout_x - 2, snout_y - 2, 8, 6))
    pygame.draw.ellipse(s, p["fur_light"], (snout_x - 1, snout_y - 1, 6, 4))
    # nose
    _draw_circle_alpha(s, p["nose"], (snout_x + 3, snout_y), 2)

    # -- eyes --
    esp = 5
    for side2 in (-1, 1):
        ex = hx + side2 * (esp - 1)
        ey = hy - 1
        _draw_circle_alpha(s, p["eye_ring"], (ex, ey), 4)
        _draw_circle_alpha(s, p["eye_white"], (ex, ey), 3)
        _draw_circle_alpha(s, p["eye_pupil"], (ex, ey), 2)
        _draw_circle_alpha(s, (255, 255, 255, 180), (ex - 1, ey - 1), 1)

    # -- whiskers --
    for side2 in (-1, 1):
        for wi in range(2):
            wx_start = snout_x + 2
            wy_start = snout_y + wi * 2 - 1
            wx_end = wx_start + side2 * 12
            wy_end = wy_start + (wi - 1) * 3
            pygame.draw.line(s, (*p["fur_light"][:3],), (wx_start, wy_start), (wx_end, wy_end), 1)

    # -- prism rainbow arc effect --
    for i in range(5):
        angle = frame * 0.4 + i * 0.6
        rx = cx + int(math.cos(angle) * 22)
        ry = cy + int(math.sin(angle * 0.7) * 14) + bob
        alpha = max(15, 50 - i * 8)
        color = [p["rainbow"], p["rainbow_alt"], p["rainbow_warm"]][i % 3]
        _draw_circle_alpha(s, (*color[:3], alpha), (rx, ry), 2)


# ============================================================
# SINGING STONE — living rock creature with embedded crystals
# ============================================================
def _draw_singing_stone(s, w, h, cx, cy, p, direction, bob, frame):
    """A gentle living rock creature that hums melodically, with glowing runes."""
    _shadow(s, cx, h, p, bob)
    bob = [0, 1, 0, -1][frame]

    # -- body (rounded boulder shape) --
    bw = int(w * 0.50)
    bh = int(h * 0.48)
    bx = cx - bw // 2
    by = int(h * 0.28) + bob

    # main stone body
    pygame.draw.ellipse(s, p["stone_dark"], (bx - 1, by - 1, bw + 2, bh + 2))
    pygame.draw.ellipse(s, p["stone"], (bx, by, bw, bh))
    pygame.draw.ellipse(s, p["stone_light"], (bx + 3, by + 3, bw // 3, bh // 3))

    # stone texture / cracks
    for i in range(3):
        cx1 = bx + 8 + i * (bw - 16) // 2
        cy1 = by + bh // 4 + (i * 5)
        cx2 = cx1 + 6 + i * 2
        cy2 = cy1 + 8
        pygame.draw.line(s, p["stone_dark"], (cx1, cy1), (cx2, cy2), 1)

    # -- moss patches --
    for mx, my in [(bx + 4, by + bh - 8), (bx + bw - 12, by + 6),
                   (bx + bw // 2 - 4, by + bh - 4)]:
        _draw_ellipse_alpha(s, p["moss"], (mx, my, 10, 5))
        _draw_ellipse_alpha(s, p["moss_light"], (mx + 1, my + 1, 6, 3))

    # -- embedded crystal (glowing, on the chest area) --
    crystal_cx = cx
    crystal_cy = by + int(bh * 0.35)
    crystal_pulse = 1 if frame % 2 == 0 else 0
    # crystal glow aura
    _draw_circle_alpha(s, (*p["crystal_glow"][:3], 40 + crystal_pulse * 20),
                       (crystal_cx, crystal_cy), 12)
    # crystal shape (diamond)
    cr_size = 6
    crystal_pts = [
        (crystal_cx, crystal_cy - cr_size),
        (crystal_cx + cr_size - 1, crystal_cy),
        (crystal_cx, crystal_cy + cr_size),
        (crystal_cx - cr_size + 1, crystal_cy),
    ]
    pygame.draw.polygon(s, p["crystal"], crystal_pts)
    crystal_inner = [
        (crystal_cx, crystal_cy - cr_size + 2),
        (crystal_cx + cr_size - 3, crystal_cy),
        (crystal_cx, crystal_cy + cr_size - 2),
        (crystal_cx - cr_size + 3, crystal_cy),
    ]
    pygame.draw.polygon(s, p["crystal_light"], crystal_inner)
    # sparkle on crystal
    _draw_circle_alpha(s, (255, 255, 255, 120 + crystal_pulse * 60),
                       (crystal_cx, crystal_cy - 2), 2)

    # -- rune carvings (glow rhythmically) --
    rune_positions = [
        (bx + 6, by + bh // 3), (bx + bw - 8, by + bh // 3),
        (cx - 10, by + bh - 10), (cx + 10, by + bh - 10),
    ]
    for ri, (rx, ry) in enumerate(rune_positions):
        glow_phase = (frame + ri) % 4
        alpha = 40 + glow_phase * 15
        _draw_circle_alpha(s, (*p["rune_glow"][:3], alpha), (rx, ry), 3)
        pygame.draw.circle(s, p["rune"], (rx, ry), 2)
        # small connecting line to center
        if ri < 2:
            pygame.draw.line(s, (*p["rune_glow"][:3], alpha // 2),
                             (rx, ry), (crystal_cx, crystal_cy), 1)

    # -- face (eye slits in the stone) --
    face_y = by + int(bh * 0.22)
    for side in (-1, 1):
        ex = cx + side * 8
        ey = face_y
        # eye slit
        pygame.draw.ellipse(s, p["eye_slit"], (ex - 3, ey - 2, 6, 4))
        # glow
        _draw_circle_alpha(s, p["eye_glow"], (ex, ey), 3)
        # pupil dot
        pygame.draw.circle(s, p["stone_dark"], (ex, ey), 1)

    # -- "singing" sound wave ripples --
    wave_count = 3
    for i in range(wave_count):
        wave_phase = (frame + i) % 4
        wave_r = 10 + wave_phase * 6
        wave_alpha = max(10, 50 - wave_phase * 12)
        # arc above the stone
        wave_rect = (cx - wave_r, cy - wave_r - 4 + bob, wave_r * 2, wave_r)
        pygame.draw.arc(s, (*p["sound"][:3], wave_alpha), wave_rect, 3.5, 5.9, 1)
        # second arc
        wave_r2 = wave_r + 4
        wave_alpha2 = max(5, wave_alpha - 10)
        wave_rect2 = (cx - wave_r2, cy - wave_r2 - 4 + bob, wave_r2 * 2, wave_r2)
        pygame.draw.arc(s, (*p["sound_bright"][:3], wave_alpha2), wave_rect2, 3.7, 5.7, 1)

    # -- small root feet --
    for side in (-1, 1):
        foot_x = cx + side * 10
        foot_y = by + bh - 2
        pygame.draw.line(s, p["stone_dark"], (foot_x, foot_y), (foot_x + side * 3, foot_y + 6), 3)
        pygame.draw.line(s, p["stone"], (foot_x, foot_y + 1), (foot_x + side * 3, foot_y + 5), 1)


# ============================================================
# RENDERER REGISTRY
# ============================================================
DRAW_FUNCS = {
    "starwhale": _draw_starwhale,
    "luminous_deer": _draw_luminous_deer,
    "crystal_serpent": _draw_crystal_serpent,
    "aurora_moth": _draw_aurora_moth,
    "grove_titan": _draw_grove_titan,
    "moon_jelly": _draw_moon_jelly,
    "prism_fox": _draw_prism_fox,
    "singing_stone": _draw_singing_stone,
}


def build_peaceful_mob_animations(style: str, size: tuple[int, int]) -> dict[str, list[pygame.Surface]]:
    """
    Build a full set of animation frames for a peaceful mob style.
    Returns {"down": [...], "up": [...], "side": [...]} with 4 frames each.
    """
    palette = _palette_for(style)
    anims: dict[str, list[pygame.Surface]] = {"down": [], "up": [], "side": []}
    drawer = DRAW_FUNCS.get(style, _draw_starwhale)
    w, h = size
    for frame_idx, bob_offset in enumerate([0, 1, 0, -1]):
        for direction in ("down", "up", "side"):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            drawer(surf, w, h, w // 2, h // 2, palette, direction, bob_offset, frame_idx)
            anims[direction].append(surf)
    return anims