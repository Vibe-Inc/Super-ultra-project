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
        "ember_phoenix": {
            # feathers (fire)
            "feather": (220, 120, 40), "feather_light": (255, 180, 80),
            "feather_dark": (160, 60, 20), "feather_mid": (240, 150, 60),
            # flame accents
            "flame": (255, 200, 50), "flame_bright": (255, 240, 150),
            "flame_core": (255, 255, 220),
            # wing tips
            "wing_tip": (200, 80, 30), "wing_glow": (255, 160, 60, 80),
            # eyes
            "eye_white": (255, 240, 200), "eye_pupil": (120, 40, 10),
            "eye_glow": (255, 200, 100, 80),
            # crest
            "crest": (255, 160, 50), "crest_bright": (255, 220, 120),
            # ember particles
            "ember": (255, 180, 60, 100), "ember_bright": (255, 230, 120, 120),
            "shadow": (0, 0, 0, 40),
        },
        "coral_golem": {
            # coral body
            "coral": (210, 120, 130), "coral_light": (240, 160, 170),
            "coral_dark": (160, 80, 90), "coral_mid": (225, 140, 150),
            # secondary coral branches
            "branch": (230, 150, 100), "branch_light": (250, 185, 140),
            # ocean energy
            "energy": (80, 160, 200, 80), "energy_bright": (120, 200, 240, 100),
            # barnacles / detail
            "barnacle": (190, 170, 150), "barnacle_light": (220, 205, 185),
            # eyes
            "eye_bg": (50, 40, 55), "eye_glow": (80, 180, 220, 90),
            "eye_pupil": (60, 140, 180),
            # water droplets
            "water": (120, 180, 220, 80), "water_bright": (170, 210, 240, 100),
            "shadow": (0, 0, 0, 40),
        },
        "void_butterfly": {
            # body
            "body": (40, 30, 60), "body_light": (70, 60, 95),
            "body_dark": (25, 20, 40),
            # wing colors (cosmic)
            "wing": (30, 20, 70), "wing_light": (60, 50, 110),
            "wing_dark": (15, 10, 40),
            # cosmos pattern on wings
            "cosmos": (80, 60, 160), "cosmos_bright": (140, 120, 220),
            "cosmos_star": (220, 210, 255, 120),
            # nebula accents
            "nebula": (100, 50, 140, 80), "nebula_bright": (160, 100, 200, 100),
            # antennae
            "antenna": (60, 50, 80), "antenna_tip": (160, 140, 220),
            # eyes
            "eye_white": (180, 170, 220), "eye_pupil": (30, 20, 50),
            "shadow": (0, 0, 0, 40),
        },
        # ---- NEW MAJESTIC ANIMAL PALETTES ----
        "moss_rabbit": {
            "fur": (160, 185, 140), "fur_light": (200, 220, 180),
            "fur_dark": (110, 135, 90), "fur_mid": (180, 205, 160),
            "belly": (220, 230, 200),
            "ear": (130, 100, 90), "ear_inner": (200, 160, 150),
            "eye_white": (230, 230, 210), "eye_pupil": (50, 40, 30),
            "nose": (180, 120, 110),
            "moss": (80, 140, 60), "moss_light": (110, 175, 85),
            "flower": (240, 180, 200), "flower_light": (255, 210, 230),
            "flower_dark": (200, 130, 160),
            "shadow": (0, 0, 0, 40),
        },
        "crystal_fox": {
            "fur": (160, 180, 210), "fur_light": (200, 220, 245),
            "fur_dark": (105, 125, 155), "fur_mid": (180, 200, 230),
            "belly": (220, 235, 255),
            "crystal": (120, 170, 220), "crystal_light": (180, 210, 255, 80),
            "crystal_glow": (160, 200, 255, 60),
            "ear": (140, 160, 190), "ear_inner": (200, 180, 200),
            "eye_white": (220, 230, 250), "eye_pupil": (60, 80, 110),
            "nose": (40, 45, 60),
            "tail_tip": (180, 200, 240, 80),
            "shadow": (0, 0, 0, 40),
        },
        "fairy_cat": {
            "fur": (140, 120, 170), "fur_light": (180, 160, 210),
            "fur_dark": (95, 75, 125), "fur_mid": (160, 140, 190),
            "belly": (200, 185, 220),
            "wing": (180, 150, 220, 80), "wing_bright": (220, 190, 255, 100),
            "wing_inner": (160, 120, 200, 60),
            "ear": (120, 100, 150), "ear_inner": (210, 180, 200),
            "eye_white": (220, 220, 250), "eye_pupil": (40, 30, 60),
            "nose": (180, 140, 160),
            "collar": (200, 180, 100), "bell": (255, 220, 80), "bell_glow": (255, 230, 120, 80),
            "pad": (160, 140, 180),
            "tail_tip": (180, 160, 210),
            "shadow": (0, 0, 0, 40),
        },

    }
    return palettes.get(style, palettes["grove_titan"])


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


def _shadow(surface, cx, h, p, bob=0, foot_y=None):
    """Draw a soft ground shadow. ``foot_y`` overrides the automatic bottom-edge offset."""
    y = (foot_y + bob) if foot_y is not None else (h - 10 + bob)
    _draw_ellipse_alpha(surface, p["shadow"], (cx - 18, y, 36, 12))


# ============================================================
# GROVE TITAN — small friendly tree creature that walks slowly
# ============================================================
def _draw_grove_titan(s, w, h, cx, cy, p, direction, bob, frame):
    """A small, gentle tree-like creature that waddles and hums."""
    _shadow(s, cx, h, p, bob, foot_y=h - 14)
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
# SINGING STONE — living rock creature with embedded crystals
# ============================================================
def _draw_singing_stone(s, w, h, cx, cy, p, direction, bob, frame):
    """A gentle living rock creature that hums melodically, with glowing runes."""
    _shadow(s, cx, h, p, bob, foot_y=int(h * 0.28) + int(h * 0.48) - 2)
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
# EMBER PHOENIX — radiant bird of gentle flame
# ============================================================
def _draw_ember_phoenix(s, w, h, cx, cy, p, direction, bob, frame):
    """A radiant bird of gentle flame that radiates warmth and healing light."""
    _shadow(s, cx, h, p, bob, foot_y=int(h * 0.60))
    wing_flap = [0, 5, 0, -5][frame]
    head_bob = [0, -1, 0, 1][frame]

    # -- flame aura --
    aura = pygame.Surface((w, h), pygame.SRCALPHA)
    pulse_r = int(w * 0.35) + (frame % 2) * 3
    _draw_circle_alpha(aura, (*p["wing_glow"][:3], 20), (cx, cy + bob), pulse_r)
    s.blit(aura, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # -- tail feathers (long, flowing flames) --
    tail_base_x = cx - 10
    tail_base_y = cy + 6 + bob
    for i in range(5):
        angle = math.pi + 0.3 * (i - 2) + math.sin(frame * 0.4 + i) * 0.2
        length = 18 + i * 3
        tx = tail_base_x + int(math.cos(angle) * length)
        ty = tail_base_y + int(math.sin(angle) * length)
        colors = [p["feather_dark"], p["feather"], p["feather_light"], p["flame"], p["flame_bright"]]
        pygame.draw.line(s, colors[i], (tail_base_x, tail_base_y), (tx, ty), 3 - i // 2)
        _draw_circle_alpha(s, (*p["flame_bright"][:3], 60), (tx, ty), 2)

    # -- wings (spread, flame-like) --
    for side in (-1, 1):
        wing_x = cx + side * 4
        wing_y = cy - 2 + bob
        # outer wing
        wing_pts = [
            (wing_x, wing_y),
            (wing_x + side * (22 + wing_flap), wing_y - 14),
            (wing_x + side * (28 + wing_flap), wing_y - 6),
            (wing_x + side * (24 + wing_flap), wing_y + 6),
            (wing_x + side * 6, wing_y + 6),
        ]
        pygame.draw.polygon(s, p["wing_tip"], wing_pts)
        # inner wing
        wing_inner = [
            (wing_x + side * 2, wing_y),
            (wing_x + side * (18 + wing_flap), wing_y - 10),
            (wing_x + side * (22 + wing_flap), wing_y - 4),
            (wing_x + side * (18 + wing_flap), wing_y + 4),
            (wing_x + side * 6, wing_y + 4),
        ]
        pygame.draw.polygon(s, p["feather_dark"], wing_inner)
        # flame layer
        wing_flame = [
            (wing_x + side * 4, wing_y + 1),
            (wing_x + side * (14 + wing_flap), wing_y - 6),
            (wing_x + side * (16 + wing_flap), wing_y),
            (wing_x + side * (12 + wing_flap), wing_y + 3),
            (wing_x + side * 6, wing_y + 2),
        ]
        pygame.draw.polygon(s, p["feather"], wing_flame)
        # flame tip highlights
        _draw_circle_alpha(s, (*p["flame"][:3], 80),
                           (wing_x + side * (20 + wing_flap), wing_y - 8), 4)
        _draw_circle_alpha(s, (*p["flame_bright"][:3], 60),
                           (wing_x + side * (18 + wing_flap), wing_y - 6), 3)

    # -- body --
    bw = int(w * 0.30)
    bh = int(h * 0.28)
    bx = cx - bw // 2
    by = int(h * 0.32) + bob
    pygame.draw.ellipse(s, p["feather_dark"], (bx - 1, by - 1, bw + 2, bh + 2))
    pygame.draw.ellipse(s, p["feather"], (bx, by, bw, bh))
    pygame.draw.ellipse(s, p["feather_light"], (bx + 2, by + 2, bw // 3, bh - 4))

    # -- neck --
    neck_x = cx + 4
    neck_y = by - 4
    pygame.draw.polygon(s, p["feather_dark"], [
        (neck_x - 3, neck_y + 6), (neck_x + 3, neck_y + 6),
        (neck_x + 2, neck_y - 6), (neck_x - 2, neck_y - 6),
    ])
    pygame.draw.polygon(s, p["feather"], [
        (neck_x - 2, neck_y + 5), (neck_x + 2, neck_y + 5),
        (neck_x + 1, neck_y - 4), (neck_x - 1, neck_y - 4),
    ])

    # -- head --
    hx = neck_x + 1
    hy = neck_y - 8 + head_bob
    hr = 7
    pygame.draw.ellipse(s, p["feather_dark"], (hx - hr, hy - hr // 2, hr * 2, hr))
    pygame.draw.ellipse(s, p["feather"], (hx - hr + 1, hy - hr // 2 + 1, hr * 2 - 2, hr - 2))
    pygame.draw.ellipse(s, p["feather_light"], (hx - hr + 2, hy - hr // 2 + 1, hr, hr - 3))

    # -- crest (flame crown) --
    for i in range(3):
        crest_x = hx + (i - 1) * 3
        crest_y = hy - hr // 2
        crest_h = 8 + (1 if i == 1 else 0)
        flame_wave = [0, 1, 0, -1][(frame + i) % 4]
        pygame.draw.line(s, p["crest"], (crest_x, crest_y),
                         (crest_x + flame_wave, crest_y - crest_h), 2)
        _draw_circle_alpha(s, (*p["flame_bright"][:3], 80),
                           (crest_x + flame_wave, crest_y - crest_h), 2)

    # -- eyes --
    for side in (-1, 1):
        ex = hx + side * 3
        ey = hy - 1
        _draw_circle_alpha(s, p["eye_glow"], (ex, ey), 4)
        _draw_circle_alpha(s, p["eye_white"], (ex, ey), 2)
        _draw_circle_alpha(s, p["eye_pupil"], (ex, ey), 1)

    # -- beak --
    beak_x = hx + hr - 1
    beak_y = hy + 2
    pygame.draw.polygon(s, p["flame"], [
        (beak_x, beak_y - 2), (beak_x + 6, beak_y), (beak_x, beak_y + 2),
    ])

    # -- ember particles --
    for i in range(5):
        angle = frame * 0.5 + i * 1.26
        ex = cx + int(math.cos(angle) * (12 + i * 3))
        ey = cy + int(math.sin(angle) * 10) + bob + 8
        alpha = max(15, 70 - i * 12)
        _draw_circle_alpha(s, (*p["ember"][:3], alpha), (ex, ey), 2)
        if i % 2 == 0:
            _draw_circle_alpha(s, (*p["ember_bright"][:3], alpha // 2), (ex + 1, ey - 1), 1)


# ============================================================
# CORAL GOLEM — living coral formation with ocean energy
# ============================================================
def _draw_coral_golem(s, w, h, cx, cy, p, direction, bob, frame):
    """A living coral formation that pulses with deep ocean energy."""
    _shadow(s, cx, h, p, bob, foot_y=int(h * 0.28) + int(h * 0.42))
    pulse = [0, 1, 0, -1][frame]

    # -- ocean energy glow --
    aura = pygame.Surface((w, h), pygame.SRCALPHA)
    _draw_circle_alpha(aura, (*p["energy"][:3], 20), (cx, cy + bob), int(w * 0.35))
    s.blit(aura, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # -- base / feet (root-like coral) --
    for side in (-1, 1):
        foot_x = cx + side * 8
        foot_y = cy + 18 + bob
        for t in range(3):
            tx = foot_x + (t - 1) * 4
            pygame.draw.line(s, p["coral_dark"], (foot_x, foot_y), (tx, foot_y + 6), 3)
            pygame.draw.line(s, p["coral"], (foot_x, foot_y + 1), (tx, foot_y + 5), 1)

    # -- main body (rounded, bumpy coral) --
    bw = int(w * 0.44)
    bh = int(h * 0.42)
    bx = cx - bw // 2
    by = int(h * 0.28) + bob + pulse

    pygame.draw.ellipse(s, p["coral_dark"], (bx - 1, by - 1, bw + 2, bh + 2))
    pygame.draw.ellipse(s, p["coral"], (bx, by, bw, bh))
    pygame.draw.ellipse(s, p["coral_light"], (bx + 3, by + 3, bw // 3, bh // 3))

    # -- coral bumps / texture --
    bump_positions = [
        (bx + 6, by + 6, 4), (bx + bw - 10, by + 8, 3),
        (bx + bw // 2, by + 4, 5), (bx + 4, by + bh // 2, 3),
        (bx + bw - 6, by + bh // 2, 4),
    ]
    for mx, my, mr in bump_positions:
        _draw_circle_alpha(s, p["coral_dark"], (mx, my + pulse), mr)
        _draw_circle_alpha(s, p["coral"], (mx, my + pulse), mr - 1)

    # -- coral branches growing from body --
    branch_configs = [
        (-1, -12, 10), (1, -14, 12), (-1, -6, 8), (1, -8, 9),
    ]
    for side, y_off, length in branch_configs:
        bx_start = cx + side * (bw // 4)
        by_start = by + y_off
        bx_end = bx_start + side * 6
        by_end = by_start - length
        pygame.draw.line(s, p["coral_dark"], (bx_start, by_start), (bx_end, by_end), 3)
        pygame.draw.line(s, p["branch"], (bx_start, by_start + 1), (bx_end, by_end), 2)
        # branch tip (glowing)
        tip_pulse = 1 if (frame + bx_start) % 3 == 0 else 0
        _draw_circle_alpha(s, p["branch_light"], (bx_end, by_end), 3 + tip_pulse)

    # -- barnacles / detail --
    for bx2, by2 in [(bx + 8, by + bh // 2), (bx + bw - 10, by + bh // 3)]:
        _draw_circle_alpha(s, p["barnacle"], (bx2, by2 + pulse), 3)
        _draw_circle_alpha(s, p["barnacle_light"], (bx2, by2 + pulse), 2)

    # -- face (simple glowing eyes) --
    face_y = by + int(bh * 0.30)
    for side in (-1, 1):
        ex = cx + side * 7
        ey = face_y
        _draw_circle_alpha(s, p["eye_bg"], (ex, ey), 4)
        _draw_circle_alpha(s, p["eye_glow"], (ex, ey), 3)
        _draw_circle_alpha(s, p["eye_pupil"], (ex, ey), 2)

    # -- ocean energy pulses --
    for i in range(3):
        wave_phase = (frame + i) % 4
        wave_r = 12 + wave_phase * 5
        wave_alpha = max(10, 40 - wave_phase * 10)
        _draw_circle_alpha(s, (*p["energy_bright"][:3], wave_alpha), (cx, cy + bob), wave_r)

    # -- water droplet particles --
    for i in range(3):
        angle = frame * 0.4 + i * 2.1
        dx = cx + int(math.cos(angle) * 16)
        dy = cy + int(math.sin(angle) * 10) + bob
        _draw_circle_alpha(s, (*p["water"][:3], 50), (dx, dy), 2)
        _draw_circle_alpha(s, (*p["water_bright"][:3], 30), (dx, dy), 1)


# ============================================================
# VOID BUTTERFLY — butterfly with cosmic wings
# ============================================================
def _draw_void_butterfly(s, w, h, cx, cy, p, direction, bob, frame):
    """A massive butterfly whose wings reveal glimpses of the distant cosmos."""
    _shadow(s, cx, h, p, bob, foot_y=int(h * 0.55))
    wing_flap = [0, 5, 0, -5][frame]
    antenna_sway = [0, 2, 0, -2][frame]

    # -- cosmic aura --
    aura = pygame.Surface((w, h), pygame.SRCALPHA)
    _draw_circle_alpha(aura, (*p["nebula"][:3], 20), (cx, cy + bob), int(w * 0.4))
    s.blit(aura, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # -- wings (4: 2 large upper, 2 smaller lower) --
    for side in (-1, 1):
        # Upper wing (large, cosmic)
        uw_x = cx + side * 3
        uw_y = cy - 2 + bob
        uw_pts = [
            (uw_x, uw_y),
            (uw_x + side * (28 + wing_flap), uw_y - 16),
            (uw_x + side * (34 + wing_flap), uw_y - 4),
            (uw_x + side * (26 + wing_flap), uw_y + 10),
            (uw_x + side * 6, uw_y + 8),
        ]
        # outer wing (dark void)
        pygame.draw.polygon(s, p["wing_dark"], uw_pts)
        # inner wing (deep cosmos)
        uw_inner = [
            (uw_x + side * 3, uw_y - 1),
            (uw_x + side * (24 + wing_flap), uw_y - 13),
            (uw_x + side * (28 + wing_flap), uw_y - 3),
            (uw_x + side * (22 + wing_flap), uw_y + 7),
            (uw_x + side * 6, uw_y + 6),
        ]
        pygame.draw.polygon(s, p["wing"], uw_inner)
        # cosmos layer
        uw_cosmos = [
            (uw_x + side * 6, uw_y),
            (uw_x + side * (18 + wing_flap), uw_y - 8),
            (uw_x + side * (20 + wing_flap), uw_y),
            (uw_x + side * (14 + wing_flap), uw_y + 4),
            (uw_x + side * 6, uw_y + 3),
        ]
        pygame.draw.polygon(s, p["wing_light"], uw_cosmos)

        # star speckles on upper wing
        for i in range(5):
            st_x = uw_x + side * (6 + i * 5 + wing_flap * 0.5)
            st_y = uw_y - 8 + i * 3
            bright = 1 if (frame + i + int(uw_x)) % 3 == 0 else 0
            _draw_circle_alpha(s, (*p["cosmos_star"][:3], 60 + bright * 40),
                               (int(st_x), int(st_y)), 1 + bright)

        # nebula accent
        neb_x = uw_x + side * (16 + wing_flap)
        neb_y = uw_y - 4
        _draw_circle_alpha(s, (*p["nebula_bright"][:3], 50), (int(neb_x), int(neb_y)), 6)
        _draw_circle_alpha(s, (*p["cosmos"][:3], 70), (int(neb_x), int(neb_y)), 4)

        # Lower wing (smaller)
        lw_x = cx + side * 2
        lw_y = cy + 6 + bob
        lw_pts = [
            (lw_x, lw_y),
            (lw_x + side * (18 - wing_flap), lw_y + 2),
            (lw_x + side * (20 - wing_flap), lw_y + 14),
            (lw_x + side * (10 - wing_flap), lw_y + 16),
            (lw_x + side * 3, lw_y + 8),
        ]
        pygame.draw.polygon(s, p["wing_dark"], lw_pts)
        lw_inner = [
            (lw_x + side * 2, lw_y + 1),
            (lw_x + side * (15 - wing_flap), lw_y + 3),
            (lw_x + side * (16 - wing_flap), lw_y + 12),
            (lw_x + side * (8 - wing_flap), lw_y + 14),
            (lw_x + side * 3, lw_y + 7),
        ]
        pygame.draw.polygon(s, p["wing"], lw_inner)
        # small star on lower wing
        _draw_circle_alpha(s, (*p["cosmos_star"][:3], 70),
                           (lw_x + side * (10 - wing_flap), lw_y + 8), 2)

    # -- body (fuzzy, dark) --
    body_y = cy - 2 + bob
    # thorax
    pygame.draw.ellipse(s, p["body_dark"], (cx - 4, body_y - 1, 8, 10))
    pygame.draw.ellipse(s, p["body"], (cx - 3, body_y, 6, 8))
    pygame.draw.ellipse(s, p["body_light"], (cx - 2, body_y + 1, 4, 5))
    # abdomen
    for seg in range(3):
        seg_y = body_y + 8 + seg * 4
        seg_w = 5 - seg
        pygame.draw.ellipse(s, p["body_dark"], (cx - seg_w // 2 - 1, seg_y - 1, seg_w + 2, 5))
        pygame.draw.ellipse(s, p["body"], (cx - seg_w // 2, seg_y, seg_w, 4))

    # -- head --
    hy = body_y - 4
    _draw_circle_alpha(s, p["body_dark"], (cx, hy), 4)
    _draw_circle_alpha(s, p["body"], (cx, hy), 3)
    # eyes
    for side in (-1, 1):
        ex = cx + side * 2
        _draw_circle_alpha(s, p["eye_white"], (ex, hy - 1), 2)
        _draw_circle_alpha(s, p["eye_pupil"], (ex, hy - 1), 1)

    # -- antennae (long, curled) --
    for side in (-1, 1):
        base_x = cx + side * 2
        base_y = hy - 3
        mid_x = base_x + side * (6 + antenna_sway)
        mid_y = base_y - 8
        tip_x = mid_x + side * 3
        tip_y = mid_y - 4
        # draw as two segments
        pygame.draw.line(s, p["antenna"], (base_x, base_y), (mid_x, mid_y), 1)
        pygame.draw.line(s, p["antenna"], (mid_x, mid_y), (tip_x, tip_y), 1)
        # glowing tip
        _draw_circle_alpha(s, (*p["antenna_tip"][:3], 120), (tip_x, tip_y), 2)
        _draw_circle_alpha(s, (*p["antenna_tip"][:3], 50), (tip_x, tip_y), 4)

    # -- trailing cosmic dust --
    for i in range(4):
        angle = frame * 0.4 + i * 1.57
        dx = int(math.cos(angle) * (10 + i * 4))
        dy = int(math.sin(angle * 0.6) * (6 + i * 3))
        alpha = max(15, 50 - i * 10)
        _draw_circle_alpha(s, (*p["cosmos"][:3], alpha), (cx + dx, cy + bob + 18 + dy), 2)


# ============================================================
# MOSS RABBIT — fluffy rabbit with moss and flowers
# ============================================================
def _draw_moss_rabbit(s, w, h, cx, cy, p, direction, bob, frame):
    """A fluffy rabbit with moss and tiny flowers growing on its back."""
    _shadow(s, cx, h, p, bob, foot_y=int(h * 0.62) + 12)
    hop = [0, -2, 0, -1][frame]
    ear_wag = [0, 2, 0, -2][frame]

    # -- legs (hopping) --
    for side in (-1, 1):
        lx = cx + side * 5
        ly = int(h * 0.62) + bob + hop
        pygame.draw.ellipse(s, p["fur_dark"], (lx, ly, 8, 12))
        pygame.draw.ellipse(s, p["fur"], (lx + 1, ly + 1, 6, 10))
        pygame.draw.ellipse(s, p["fur_light"], (lx + 1, ly + 8, 6, 4))

    # -- body (round, fluffy) --
    bw = int(w * 0.38)
    bh = int(h * 0.30)
    bx = cx - bw // 2
    by = int(h * 0.34) + bob + hop
    pygame.draw.ellipse(s, p["fur_dark"], (bx - 1, by - 1, bw + 2, bh + 2))
    pygame.draw.ellipse(s, p["fur"], (bx, by, bw, bh))
    pygame.draw.ellipse(s, p["fur_light"], (bx + 3, by + 3, bw // 3, bh - 6))

    # -- belly --
    _draw_ellipse_alpha(s, p["belly"], (cx - 6, by + bh - 6, 12, 8))

    # -- moss on back --
    for mx, my in [(bx + 4, by + 4), (bx + bw - 6, by + 6), (cx, by + 2)]:
        _draw_ellipse_alpha(s, p["moss"], (mx, my, 8, 4))
        _draw_ellipse_alpha(s, p["moss_light"], (mx + 1, my + 1, 5, 2))
        # tiny flower on moss
        _draw_circle_alpha(s, p["flower"], (mx + 3, my - 1), 2)
        _draw_circle_alpha(s, p["flower_light"], (mx + 3, my - 2), 1)

    # -- head --
    hr = int(w * 0.14)
    hx = cx + bw // 2 - 4
    hy = by - 2 + [0, -1, 0, 1][frame]
    pygame.draw.ellipse(s, p["fur_dark"], (hx - hr, hy - hr // 2, hr * 2, hr))
    pygame.draw.ellipse(s, p["fur"], (hx - hr + 1, hy - hr // 2 + 1, hr * 2 - 2, hr - 2))

    # -- ears (long, floppy) --
    for side in (-1, 1):
        ear_x = hx + side * 4
        ear_y = hy - 4
        ear_len = 14 + side * ear_wag
        pygame.draw.ellipse(s, p["fur_dark"], (ear_x - 3, ear_y - ear_len, 6, ear_len))
        pygame.draw.ellipse(s, p["fur"], (ear_x - 2, ear_y - ear_len + 1, 4, ear_len - 2))
        pygame.draw.ellipse(s, p["ear_inner"], (ear_x - 1, ear_y - ear_len + 4, 2, ear_len - 6))

    # -- eyes --
    for side in (-1, 1):
        ex = hx + side * 3
        ey = hy - 1
        pygame.draw.circle(s, p["eye_white"], (ex, ey), 3)
        pygame.draw.circle(s, p["eye_pupil"], (ex, ey), 2)
        pygame.draw.circle(s, (255, 255, 255, 180), (ex + 1, ey - 1), 1)

    # -- nose --
    pygame.draw.circle(s, p["nose"], (hx + hr - 2, hy + 1), 2)

    # -- tail (fluffy cottonball) --
    tail_x = bx - 4
    tail_y = by + bh // 2
    _draw_circle_alpha(s, p["belly"], (tail_x, tail_y), 5)
    _draw_circle_alpha(s, p["fur_light"], (tail_x, tail_y), 4)


# ============================================================
# CRYSTAL FOX — sleek fox with shimmering crystal fur
# ============================================================
def _draw_crystal_fox(s, w, h, cx, cy, p, direction, bob, frame):
    """A sleek fox whose fur shimmers like cut gemstones in the sunlight."""
    _shadow(s, cx, h, p, bob, foot_y=int(h * 0.56) + 14)
    walk = [0, 1, 0, -1][frame]
    tail_sway = [0, 3, 0, -3][frame]

    # -- tail (bushy, crystal-tipped) --
    tail_x = cx - 16
    tail_y = cy + 2 + bob
    tail_pts = []
    for i in range(5):
        tx = tail_x - i * 4 + tail_sway * (i * 0.2)
        ty = tail_y + i * 2 + int(math.sin(frame * 0.4 + i) * 2)
        tail_pts.append((tx, ty))
    for i in range(len(tail_pts) - 1):
        pygame.draw.line(s, p["fur_dark"], tail_pts[i], tail_pts[i + 1], max(1, 4 - i))
        pygame.draw.line(s, p["fur"], tail_pts[i], tail_pts[i + 1], max(1, 3 - i))
    # crystal tip
    tip = tail_pts[-1]
    _draw_circle_alpha(s, (*p["tail_tip"][:3], 80), tip, 4)

    # -- hind legs --
    for side in (-1, 1):
        lx = cx + side * 5 - 2
        ly = int(h * 0.56) + bob
        pygame.draw.rect(s, p["fur_dark"], (lx + walk * side, ly, 6, 14), border_radius=2)
        pygame.draw.rect(s, p["fur"], (lx + 1 + walk * side, ly + 1, 4, 12), border_radius=1)

    # -- body --
    bw = int(w * 0.40)
    bh = int(h * 0.28)
    bx = cx - bw // 2
    by = int(h * 0.32) + bob
    pygame.draw.ellipse(s, p["fur_dark"], (bx - 1, by - 1, bw + 2, bh + 2))
    pygame.draw.ellipse(s, p["fur"], (bx, by, bw, bh))
    pygame.draw.ellipse(s, p["fur_light"], (bx + 3, by + 2, bw // 3, bh - 6))

    # -- crystal shimmer on fur --
    for i in range(4):
        sx = bx + 4 + i * (bw - 8) // 3
        sy = by + 3 + (i % 3) * 3
        pulse = 1 if (frame + i) % 2 == 0 else 0
        _draw_circle_alpha(s, (*p["crystal_glow"][:3], 40 + pulse * 30), (sx, sy), 2 + pulse)

    # -- belly --
    _draw_ellipse_alpha(s, p["belly"], (cx - 5, by + bh - 4, 10, 6))

    # -- front legs --
    for side in (-1, 1):
        lx = cx + side * 7 + 2
        ly = int(h * 0.50) + bob
        leg_walk = walk * side
        pygame.draw.rect(s, p["fur_dark"], (lx + leg_walk, ly, 6, 16), border_radius=2)
        pygame.draw.rect(s, p["fur"], (lx + 1 + leg_walk, ly + 1, 4, 14), border_radius=1)
        pygame.draw.rect(s, p["fur_light"], (lx + 1 + leg_walk, ly + 1, 2, 8), border_radius=1)

    # -- neck --
    neck_x = cx + 6
    neck_y = by - 4
    pygame.draw.polygon(s, p["fur_dark"], [
        (neck_x - 4, neck_y + 6), (neck_x + 4, neck_y + 6),
        (neck_x + 3, neck_y - 4), (neck_x - 3, neck_y - 4),
    ])
    pygame.draw.polygon(s, p["fur"], [
        (neck_x - 3, neck_y + 5), (neck_x + 3, neck_y + 5),
        (neck_x + 2, neck_y - 2), (neck_x - 2, neck_y - 2),
    ])

    # -- head (pointed, fox-like) --
    hr = int(w * 0.13)
    hx = neck_x + 2
    hy = neck_y - 6 + [0, -1, 0, 1][frame]
    pygame.draw.ellipse(s, p["fur_dark"], (hx - hr - 1, hy - hr // 2 - 1, hr * 2 + 2, hr + 2))
    pygame.draw.ellipse(s, p["fur"], (hx - hr, hy - hr // 2, hr * 2, hr))
    pygame.draw.ellipse(s, p["fur_light"], (hx - hr + 2, hy - hr // 2 + 1, hr, hr - 3))

    # -- ears (triangular, pointed) --
    for side in (-1, 1):
        ear_x = hx + side * (hr - 2)
        ear_y = hy - 3
        pygame.draw.polygon(s, p["fur_dark"], [
            (ear_x, ear_y), (ear_x + side * 2, ear_y - 10), (ear_x + side * 6, ear_y - 2)
        ])
        pygame.draw.polygon(s, p["fur"], [
            (ear_x + 1, ear_y - 1), (ear_x + side * 2, ear_y - 8), (ear_x + side * 5, ear_y - 2)
        ])

    # -- snout --
    snout_x = hx + hr - 1
    snout_y = hy + 2
    pygame.draw.ellipse(s, p["fur"], (snout_x - 2, snout_y - 2, 8, 6))
    pygame.draw.ellipse(s, p["fur_light"], (snout_x - 1, snout_y - 1, 6, 4))
    pygame.draw.circle(s, p["nose"], (snout_x + 2, snout_y + 1), 1)

    # -- eyes --
    esp = 4
    for side2 in (-1, 1):
        ex = hx + side2 * esp
        ey = hy - 1
        _draw_circle_alpha(s, p["eye_white"], (ex, ey), 3)
        _draw_circle_alpha(s, p["eye_pupil"], (ex, ey), 2)
        pygame.draw.circle(s, (255, 255, 255, 180), (ex + 1, ey - 1), 1)

    # -- crystal sparkle trail --
    for i in range(3):
        angle = frame * 0.4 + i * 2.1
        sx = cx + int(math.cos(angle) * 18)
        sy = cy + int(math.sin(angle) * 10) + bob
        _draw_circle_alpha(s, (*p["crystal_light"][:3], 40), (sx, sy), 2)




# ============================================================
# FAIRY CAT — graceful feline with iridescent wings
# ============================================================
def _draw_fairy_cat(s, w, h, cx, cy, p, direction, bob, frame):
    """A graceful feline with iridescent wings and eyes like tiny moons."""
    _shadow(s, cx, h, p, bob, foot_y=int(h * 0.56) + 14)
    walk = [0, 1, 0, -1][frame]
    tail_wag = [0, 4, 0, -4][frame]
    wing_flap = [0, 3, 0, -3][frame]

    # -- wings (fairy/insect-like) --
    for side in (-1, 1):
        wing_x = cx + side * 2
        wing_y = cy - 4 + bob
        # upper wing
        uw_pts = [
            (wing_x, wing_y),
            (wing_x + side * (18 + wing_flap), wing_y - 10),
            (wing_x + side * (22 + wing_flap), wing_y),
            (wing_x + side * (16 + wing_flap), wing_y + 6),
            (wing_x + side * 4, wing_y + 4),
        ]
        pygame.draw.polygon(s, (*p["wing"][:3], 60), uw_pts)
        uw_inner = [
            (wing_x + side * 3, wing_y),
            (wing_x + side * (14 + wing_flap), wing_y - 6),
            (wing_x + side * (16 + wing_flap), wing_y),
            (wing_x + side * (12 + wing_flap), wing_y + 4),
            (wing_x + side * 4, wing_y + 3),
        ]
        pygame.draw.polygon(s, (*p["wing_bright"][:3], 40), uw_inner)
        # lower wing
        lw_pts = [
            (wing_x, wing_y + 4),
            (wing_x + side * (12 - wing_flap), wing_y + 6),
            (wing_x + side * (14 - wing_flap), wing_y + 12),
            (wing_x + side * (8 - wing_flap), wing_y + 14),
            (wing_x + side * 3, wing_y + 8),
        ]
        pygame.draw.polygon(s, (*p["wing_inner"][:3], 50), lw_pts)

    # -- tail (long, graceful) --
    tail_x = cx - 14
    tail_y = cy + 4 + bob
    tail_pts = []
    for i in range(5):
        tx = tail_x - i * 5 + tail_wag * (i * 0.2)
        ty = tail_y + i * 2 + int(math.sin(frame * 0.5 + i * 0.8) * 2)
        tail_pts.append((tx, ty))
    for i in range(len(tail_pts) - 1):
        pygame.draw.line(s, p["fur_dark"], tail_pts[i], tail_pts[i + 1], max(1, 3 - i))
        pygame.draw.line(s, p["fur"], tail_pts[i], tail_pts[i + 1], max(1, 2 - i))
    tip = tail_pts[-1]
    _draw_circle_alpha(s, (*p["tail_tip"][:3], 80), tip, 3)

    # -- hind legs --
    for side in (-1, 1):
        lx = cx + side * 6 - 2
        ly = int(h * 0.56) + bob
        pygame.draw.rect(s, p["fur_dark"], (lx + walk * side, ly, 6, 14), border_radius=2)
        pygame.draw.rect(s, p["fur"], (lx + 1 + walk * side, ly + 1, 4, 12), border_radius=1)
        pygame.draw.ellipse(s, p["pad"], (lx + walk * side, ly + 12, 6, 4))

    # -- body --
    bw = int(w * 0.40)
    bh = int(h * 0.28)
    bx = cx - bw // 2
    by = int(h * 0.32) + bob
    pygame.draw.ellipse(s, p["fur_dark"], (bx - 1, by - 1, bw + 2, bh + 2))
    pygame.draw.ellipse(s, p["fur"], (bx, by, bw, bh))
    pygame.draw.ellipse(s, p["fur_light"], (bx + 3, by + 2, bw // 3, bh - 6))

    # -- belly --
    _draw_ellipse_alpha(s, p["belly"], (cx - 5, by + bh - 4, 10, 6))

    # -- front legs --
    for side in (-1, 1):
        lx = cx + side * 8 + 2
        ly = int(h * 0.50) + bob
        leg_walk = walk * side
        pygame.draw.rect(s, p["fur_dark"], (lx + leg_walk, ly, 6, 16), border_radius=2)
        pygame.draw.rect(s, p["fur"], (lx + 1 + leg_walk, ly + 1, 4, 14), border_radius=1)
        pygame.draw.rect(s, p["fur_light"], (lx + 1 + leg_walk, ly + 1, 2, 8), border_radius=1)
        pygame.draw.ellipse(s, p["pad"], (lx + leg_walk, ly + 14, 6, 4))

    # -- neck --
    neck_x = cx + bw // 2 - 4
    neck_y = by - 4
    pygame.draw.polygon(s, p["fur_dark"], [
        (neck_x - 4, neck_y + 6), (neck_x + 4, neck_y + 6),
        (neck_x + 2, neck_y - 4), (neck_x - 2, neck_y - 4),
    ])
    pygame.draw.polygon(s, p["fur"], [
        (neck_x - 3, neck_y + 5), (neck_x + 3, neck_y + 5),
        (neck_x + 1, neck_y - 2), (neck_x - 1, neck_y - 2),
    ])

    # -- head (round, cat-like) --
    hr = int(w * 0.14)
    hx = neck_x + 1
    hy = neck_y - 6 + [0, -1, 0, 1][frame]
    pygame.draw.ellipse(s, p["fur_dark"], (hx - hr - 1, hy - hr // 2 - 1, hr * 2 + 2, hr + 2))
    pygame.draw.ellipse(s, p["fur"], (hx - hr, hy - hr // 2, hr * 2, hr))
    pygame.draw.ellipse(s, p["fur_light"], (hx - hr + 2, hy - hr // 2 + 1, hr, hr - 3))

    # -- ears (cat-like, pointed) --
    for side in (-1, 1):
        ear_x = hx + side * (hr - 2)
        ear_y = hy - 4
        pygame.draw.polygon(s, p["fur_dark"], [
            (ear_x, ear_y), (ear_x + side * 2, ear_y - 10), (ear_x + side * 6, ear_y - 2)
        ])
        pygame.draw.polygon(s, p["fur"], [
            (ear_x + 1, ear_y - 1), (ear_x + side * 2, ear_y - 8), (ear_x + side * 5, ear_y - 2)
        ])
        pygame.draw.polygon(s, p["ear_inner"], [
            (ear_x + 1, ear_y - 1), (ear_x + side * 2, ear_y - 7), (ear_x + side * 4, ear_y - 2)
        ])

    # -- eyes (large, round) --
    esp = 4
    for side2 in (-1, 1):
        ex = hx + side2 * esp
        ey = hy - 1
        _draw_circle_alpha(s, p["eye_white"], (ex, ey), 4)
        _draw_circle_alpha(s, p["eye_pupil"], (ex, ey), 3)
        pygame.draw.circle(s, (255, 255, 255, 200), (ex + 1, ey - 1), 1)

    # -- nose --
    pygame.draw.circle(s, p["nose"], (hx + hr - 2, hy + 1), 1)

    # -- collar with bell --
    collar_y = hy + hr // 2 + 2
    pygame.draw.line(s, p["collar"], (hx - 4, collar_y), (hx + 4, collar_y), 2)
    bell_y = collar_y + 2
    _draw_circle_alpha(s, p["bell"], (hx, bell_y), 2)
    _draw_circle_alpha(s, p["bell_glow"], (hx, bell_y), 3)


# ============================================================
# RENDERER REGISTRY
# ============================================================
DRAW_FUNCS = {
    "grove_titan": _draw_grove_titan,
    "singing_stone": _draw_singing_stone,
    "ember_phoenix": _draw_ember_phoenix,
    "coral_golem": _draw_coral_golem,
    "void_butterfly": _draw_void_butterfly,
    "moss_rabbit": _draw_moss_rabbit,
    "crystal_fox": _draw_crystal_fox,
    "fairy_cat": _draw_fairy_cat,

}


def build_peaceful_mob_animations(style: str, size: tuple[int, int]) -> dict[str, list[pygame.Surface]]:
    """
    Build a full set of animation frames for a peaceful mob style.
    Returns {"down": [...], "up": [...], "side": [...]} with 4 frames each.
    """
    palette = _palette_for(style)
    anims: dict[str, list[pygame.Surface]] = {"down": [], "up": [], "side": []}
    drawer = DRAW_FUNCS.get(style, _draw_grove_titan)
    w, h = size
    for frame_idx, bob_offset in enumerate([0, 1, 0, -1]):
        for direction in ("down", "up", "side"):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            drawer(surf, w, h, w // 2, h // 2, palette, direction, bob_offset, frame_idx)
            anims[direction].append(surf)
    return anims