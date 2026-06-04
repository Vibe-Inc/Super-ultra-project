from __future__ import annotations

import math
from functools import lru_cache

import pygame


def build_monster_animations(style: str, size: tuple[int, int]) -> dict[str, list[pygame.Surface]]:
    return _build_monster_animations_cached((style or "").lower(), tuple(size))


@lru_cache(maxsize=16)
def _build_monster_animations_cached(style: str, size: tuple[int, int]) -> dict[str, list[pygame.Surface]]:
    palette = _palette_for(style)
    anims: dict[str, list[pygame.Surface]] = {"down": [], "up": [], "side": []}
    for frame_idx, offset in enumerate([0, 1, 0, -1]):
        for d in ("down", "up", "side"):
            anims[d].append(_make_frame(size, palette, style, d, offset, frame_idx))
    return anims


def _palette_for(style: str) -> dict:
    palettes = {
        "brute": {
            "skin": (180, 55, 35), "skin_light": (230, 100, 60), "skin_dark": (100, 25, 15),
            "skin_mid": (200, 75, 45), "fur": (40, 18, 10), "fur_light": (70, 32, 18),
            "fur_dark": (20, 8, 4), "accent": (255, 120, 30), "accent_dark": (200, 70, 15),
            "eye_white": (255, 200, 50), "eye_pupil": (255, 80, 20),
            "horn": (60, 55, 70), "horn_light": (100, 90, 115), "horn_dark": (30, 25, 40),
            "horn_glow": (255, 140, 30, 120), "tusk": (245, 235, 220),
            "core_glow": (255, 180, 50), "core_dark": (200, 80, 20),
            "aura": (200, 50, 20, 30), "aura_bright": (255, 100, 30, 60),
            "ember": (255, 200, 80), "shadow": (0, 0, 0, 60),
            "vein": (200, 60, 30), "metal": (80, 75, 85), "metal_dark": (50, 45, 55),
            "spike": (70, 65, 78), "spike_light": (100, 92, 110),
        },
        "venomous": {
            "skin": (42, 125, 72), "skin_light": (65, 180, 98), "skin_dark": (20, 72, 42),
            "skin_mid": (52, 150, 82), "belly": (90, 200, 130),
            "accent": (185, 245, 100), "accent_dark": (120, 200, 60),
            "eye_white": (235, 255, 145), "eye_pupil": (210, 55, 55),
            "fang": (245, 245, 235), "fang_dark": (200, 200, 190),
            "scale": (32, 100, 58), "scale_light": (50, 130, 72), "shadow": (0, 0, 0, 48),
        },
        "arcanist": {
            "robe": (42, 82, 148), "robe_light": (110, 158, 220), "robe_dark": (22, 42, 82),
            "robe_mid": (70, 115, 180), "skin": (180, 160, 200), "skin_dark": (100, 80, 130),
            "accent": (210, 190, 255), "accent_dark": (140, 110, 200),
            "eye_white": (235, 245, 255), "eye_pupil": (100, 185, 255),
            "rune": (255, 225, 110), "rune_dark": (200, 170, 60),
            "glow": (160, 190, 255, 55), "glow_bright": (200, 220, 255, 90), "shadow": (0, 0, 0, 48),
        },
        "trickster": {
            "skin": (150, 55, 65), "skin_light": (220, 120, 130), "skin_dark": (78, 22, 32),
            "skin_mid": (185, 80, 92), "cloth": (55, 35, 55), "cloth_light": (85, 60, 85),
            "cloth_dark": (35, 20, 35), "accent": (230, 120, 40), "accent_dark": (180, 80, 20),
            "eye_white": (250, 235, 215), "eye_pupil": (185, 65, 65),
            "mask": (45, 45, 55), "mask_light": (65, 65, 78), "grin": (245, 228, 210), "shadow": (0, 0, 0, 48),
        },
        "bomber": {
            "skin": (150, 100, 45), "skin_light": (220, 170, 100), "skin_dark": (88, 55, 22),
            "skin_mid": (185, 135, 70), "metal": (170, 160, 150), "metal_light": (200, 190, 180),
            "metal_dark": (130, 120, 110), "accent": (230, 75, 55), "accent_dark": (180, 50, 30),
            "eye_white": (255, 235, 195), "eye_pupil": (100, 95, 90),
            "fuse": (185, 125, 65), "fuse_light": (210, 150, 80),
            "spark": (255, 210, 60), "spark_bright": (255, 240, 180), "stitch": (135, 90, 38), "shadow": (0, 0, 0, 48),
        },
        "stalker": {
            "cloth": (48, 52, 62), "cloth_light": (78, 85, 100), "cloth_dark": (28, 30, 38),
            "cloth_mid": (62, 68, 80), "skin": (55, 50, 60), "skin_dark": (32, 28, 36),
            "accent": (200, 60, 60), "accent_dark": (140, 35, 35),
            "eye_white": (220, 220, 235), "eye_pupil": (200, 50, 50),
            "mask": (32, 35, 42), "mask_light": (45, 48, 56),
            "blade": (185, 190, 200), "blade_dark": (120, 125, 135),
            "metal": (170, 160, 150), "metal_dark": (130, 120, 110), "shadow": (0, 0, 0, 48),
        },
        "skirmisher": {
            "skin": (72, 128, 118), "skin_light": (118, 178, 165), "skin_dark": (40, 78, 68),
            "skin_mid": (92, 150, 138), "accent": (210, 190, 105), "accent_dark": (165, 145, 65),
            "eye_white": (242, 248, 232), "eye_pupil": (92, 142, 132),
            "feather": (190, 150, 92), "feather_light": (215, 175, 120), "feather_dark": (155, 118, 72),
            "crest": (210, 170, 98), "crest_light": (230, 195, 130),
            "beak": (225, 195, 125), "beak_dark": (185, 155, 90), "warpaint": (200, 130, 60), "shadow": (0, 0, 0, 48),
        },
        "guardian": {
            "armor": (138, 133, 122), "armor_light": (175, 170, 155), "armor_dark": (62, 60, 68),
            "armor_mid": (155, 150, 138), "accent": (210, 190, 82), "accent_dark": (165, 145, 55),
            "eye_white": (242, 242, 248), "eye_pupil": (82, 82, 92),
            "shield": (160, 150, 130), "shield_light": (185, 175, 155), "shield_dark": (115, 108, 92),
            "crest": (215, 185, 62), "crest_dark": (175, 145, 40),
            "plume": (195, 65, 55), "plume_light": (225, 95, 85), "plume_dark": (145, 38, 30), "shadow": (0, 0, 0, 48),
        },
    }
    return palettes.get(style, palettes["brute"])


def _walk_offset(frame_idx: int) -> tuple:
    return [(0, 0, 0, 0), (-2, 2, 3, -3), (0, 0, 0, 0), (2, -2, -3, 3)][frame_idx % 4]


def _draw_shadow(surface, cx, height, palette, bob=0):
    y = height - 8 + bob
    pygame.draw.ellipse(surface, palette["shadow"], (cx - 15, y, 30, 10))


def _draw_pupils(surface, cx, ey, spacing, pupil_c, side_off=0):
    pygame.draw.circle(surface, pupil_c, (cx - spacing + side_off, ey), 2)
    pygame.draw.circle(surface, pupil_c, (cx + spacing + side_off, ey), 2)


def _draw_glint(surface, cx, ey, spacing, side_off=0):
    gc = (255, 255, 255, 180)
    pygame.draw.circle(surface, gc, (cx - spacing + side_off - 1, ey - 1), 1)
    pygame.draw.circle(surface, gc, (cx + spacing + side_off - 1, ey - 1), 1)


def _draw_arm_pair(surface, bx, bw, by, bob, arm_w, arm_h, palette,
                   la_swing, ra_swing, dark_key, light_key, fist_r=4):
    for ax, swing, is_front in [(bx - 4 - la_swing // 2, la_swing, False),
                                (bx + bw - 5 + ra_swing // 2, ra_swing, True)]:
        c1 = palette[dark_key]
        c2 = palette[light_key]
        pygame.draw.rect(surface, c1, (ax, by + 6 + bob, arm_w, arm_h), border_radius=5)
        pygame.draw.rect(surface, c2, (ax + 1, by + 8 + bob, arm_w - 2, arm_h - 4), border_radius=4)
        fy = by + arm_h + 2 + bob
        pygame.draw.circle(surface, c1, (ax + arm_w // 2, fy), fist_r)


def _draw_leg_pair(surface, cx, leg_y, bob, leg_w, leg_h, palette, ll_off, rl_off, dark_key, light_key):
    leg_h += 8
    for lx, lw, off in [(cx - 15 + ll_off, leg_w, ll_off), (cx + 2 + rl_off, leg_w, rl_off)]:
        pygame.draw.rect(surface, palette[dark_key], (lx, leg_y + bob, lw, leg_h), border_radius=3)
        pygame.draw.rect(surface, palette[light_key],
                         (lx + 1, leg_y + bob + 2, lw - 2, leg_h - 4), border_radius=2)


def _draw_eye_pair(surface, cx, ey, spacing, palette, side_off=0):
    for ex in (cx - spacing + side_off, cx + spacing + side_off):
        pygame.draw.circle(surface, palette["eye_white"], (ex, ey), 4)
    _draw_pupils(surface, cx, ey, spacing, palette["eye_pupil"], side_off)
    _draw_glint(surface, cx, ey, spacing, side_off)


# ============================================================
# BRUTE — fiery demonic hulk with magma core, glowing runes, ember aura
# ============================================================
def _draw_brute(s, w, h, cx, cy, p, dir, bob, frame):
    # -- aura glow beneath --
    ag = pygame.Surface((w, h), pygame.SRCALPHA)
    pulse_r = 18 + (frame % 2) * 3
    pygame.draw.ellipse(ag, p["aura_bright"], (cx - pulse_r, h - 12 + bob, pulse_r * 2, 10))
    pygame.draw.ellipse(ag, p["aura"], (cx - pulse_r - 4, h - 10 + bob, pulse_r * 2 + 8, 8))
    s.blit(ag, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    _draw_shadow(s, cx, h, p, bob)
    lo, ro, la, ra = _walk_offset(frame)

    # --- legs with armour and knee spikes ---
    leg_y = int(h * 0.74)
    leg_h = 22
    for lx, off, side in [(cx - 16 + lo, lo, -1), (cx + 5 + ro, ro, 1)]:
        lh = leg_h + abs(off)
        pygame.draw.ellipse(s, p["fur_dark"], (lx - 2, leg_y + bob, 15, lh))
        pygame.draw.ellipse(s, p["fur_light"], (lx, leg_y + bob + 2, 11, lh - 4))
        pygame.draw.rect(s, p["metal"], (lx - 1, leg_y + bob + lh - 7, 13, 5), border_radius=2)
        pygame.draw.polygon(s, p["spike"], [(lx + 2, leg_y + bob + lh - 9),
                                             (lx + 6, leg_y + bob + lh - 14),
                                             (lx + 10, leg_y + bob + lh - 9)])

    # --- body: massive dual torso ---
    bw1 = int(w * 0.80); bw2 = int(w * 0.64)
    bh1 = int(h * 0.26); bh2 = int(h * 0.18)
    bx1 = cx - bw1 // 2; bx2 = cx - bw2 // 2
    gap = 1
    by1 = int(h * 0.26) + bob
    by2 = by1 + bh1 + gap

    # -- upper torso (V-shape muscular) --
    ut_pts = [(bx1, by1), (bx1 + bw1, by1), (bx1 + bw1 - 4, by1 + bh1), (bx1 + 4, by1 + bh1)]
    pygame.draw.polygon(s, p["fur"], ut_pts)
    ut_inner = [(bx1 + 4, by1 + 3), (bx1 + bw1 - 4, by1 + 3),
                (bx1 + bw1 - 7, by1 + bh1 - 3), (bx1 + 7, by1 + bh1 - 3)]
    pygame.draw.polygon(s, p["fur_light"], ut_inner)
    pec_y1 = by1 + int(bh1 * 0.30)
    pygame.draw.line(s, p["fur_dark"], (cx, by1 + 2), (cx, pec_y1), 2)
    l_pec = [(bx1 + 5, by1 + 2), (cx - 1, by1 + 2), (cx - 3, pec_y1), (bx1 + 9, pec_y1 - 2)]
    r_pec = [(cx + 1, by1 + 2), (bx1 + bw1 - 5, by1 + 2), (bx1 + bw1 - 9, pec_y1 - 2), (cx + 3, pec_y1)]
    pygame.draw.lines(s, p["fur_dark"], True, l_pec, 2)
    pygame.draw.lines(s, p["fur_dark"], True, r_pec, 2)

    # -- lower torso (narrower, tighter abs) --
    lt_pts = [(bx2, by2), (bx2 + bw2, by2), (bx2 + bw2 - 2, by2 + bh2), (bx2 + 2, by2 + bh2)]
    pygame.draw.polygon(s, p["fur_dark"], lt_pts)
    lt_inner = [(bx2 + 3, by2 + 2), (bx2 + bw2 - 3, by2 + 2),
                (bx2 + bw2 - 4, by2 + bh2 - 2), (bx2 + 4, by2 + bh2 - 2)]
    pygame.draw.polygon(s, p["fur"], lt_inner)
    pygame.draw.line(s, p["fur_dark"], (cx, by2 + 2), (cx, by2 + bh2 - 2), 2)
    for ab_row in range(2):
        aby = by2 + 4 + ab_row * 6
        pygame.draw.line(s, p["fur_dark"], (cx - 7, aby), (cx + 7, aby), 2)

    # -- glowing chest core / rune (between torsos, overlapped) --
    core_cx, core_cy = cx, by1 + bh1 - 1
    core_pulse = 4 + (frame % 2) * 3
    cg = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(cg, (*p["core_glow"][:3], 70), (core_cx, core_cy), 14 + core_pulse)
    s.blit(cg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    pygame.draw.ellipse(s, p["core_dark"], (core_cx - 8, core_cy - 4, 16, 8))
    pygame.draw.ellipse(s, p["core_glow"], (core_cx - 6, core_cy - 3, 12, 6))
    pygame.draw.ellipse(s, (255, 255, 220), (core_cx - 3, core_cy - 2, 6, 4))
    for angle in [0, 1.05, 2.1, 3.14, 4.2, 5.25]:
        rx = core_cx + int(13 * math.cos(angle + frame * 0.3))
        ry = core_cy + int(6 * math.sin(angle + frame * 0.3))
        pygame.draw.line(s, p["core_glow"], (core_cx, core_cy), (rx, ry), 1)

    # -- connecting tissue between torsos --
    for rx2 in (cx - 10, cx - 5, cx + 5, cx + 10):
        pygame.draw.line(s, p["vein"], (rx2, by1 + bh1), (rx2, by2), 1)

    # -- body veins on upper torso --
    for vx in (cx - 11, cx + 11):
        for vy in range(by1 + 10, by1 + bh1 - 4, 5):
            pygame.draw.line(s, p["vein"], (vx, vy), (vx + (1 if vx > cx else -1), vy + 2), 1)

    # -- shoulder spikes ---
    for sx, fl in [(bx1 - 5, -1), (bx1 + bw1 + 3, 1)]:
        for i in range(4):
            spx = sx + fl * i * 4
            spy = by1 + 2 + i * 7
            pygame.draw.polygon(s, p["spike"],
                [(spx, spy), (spx + fl * 9, spy - 3), (spx + fl * 2, spy + 5)])

    # -- back spike row (upper torso) --
    for si in range(5):
        sx = bx1 + 5 + si * (bw1 - 10) // 4
        sy = by1 + 1 - si
        pygame.draw.polygon(s, p["spike"], [(sx, sy), (sx - 3, sy - 6 - si), (sx + 3, sy - 5 - si)])

    # -- arms with spiked bracers ---
    for ax, swing, side in [(bx1 - 6 + la // 2, la, -1), (bx1 + bw1 - 5 + ra // 2, ra, 1)]:
        arm_w, arm_h = 12, int(h * 0.38)
        aw = arm_w + abs(swing) // 2
        pygame.draw.rect(s, p["skin_dark"], (ax, by1 + 6 + bob, aw, arm_h), border_radius=4)
        pygame.draw.rect(s, p["skin"], (ax + 1, by1 + 8 + bob, aw - 2, arm_h - 4), border_radius=3)
        br_y = by1 + arm_h - 2 + bob
        pygame.draw.rect(s, p["metal"], (ax - 1, br_y, aw + 2, 8), border_radius=2)
        pygame.draw.rect(s, p["metal_dark"], (ax, br_y + 1, aw, 3), border_radius=1)
        fy = br_y + 8
        pygame.draw.circle(s, p["skin_dark"], (ax + aw // 2, fy), 5)
        pygame.draw.circle(s, p["skin"], (ax + aw // 2, fy - 1), 4)
        pygame.draw.polygon(s, p["spike"],
            [(ax + aw // 2, br_y), (ax + aw // 2 + side * 5, br_y - 5), (ax + aw // 2, br_y + 2)])
        # extra elbow spike
        ey2 = by1 + int(arm_h * 0.5) + bob
        pygame.draw.polygon(s, p["spike"],
            [(ax + (0 if side < 0 else aw), ey2),
             (ax + (0 if side < 0 else aw) + side * 6, ey2 - 4),
             (ax + (0 if side < 0 else aw), ey2 + 2)])

    # --- head ---
    hr = int(w * 0.20); hx, hy = cx, int(h * 0.17) + bob
    head_bob = [0, -1, 0, 1][frame]
    hy += head_bob

    # jaw / lower face
    pygame.draw.circle(s, p["skin_dark"], (hx, hy + 6), int(hr * 0.85))
    pygame.draw.circle(s, p["skin"], (hx, hy), hr)
    pygame.draw.circle(s, p["skin_light"], (hx, hy), hr - 3)
    # brow ridge
    for brx in (hx - 6, hx + 6):
        pygame.draw.arc(s, p["skin_dark"], (brx - 5, hy - 7, 10, 8), 3.14, 0, 2)

    # --- majestic horns ---
    horn_frame_off = [0, -1, 1, -1][frame]
    if dir == "side":
        horn_points = [
            (hx + hr - 2, hy - 5),
            (hx + hr + 18 + horn_frame_off, hy - 22 - horn_frame_off),
            (hx + hr + 12, hy - 8),
            (hx + hr + 22 + horn_frame_off, hy - 10),
        ]
        pygame.draw.polygon(s, p["horn_dark"], horn_points[:3])
        pygame.draw.polygon(s, p["horn_light"], [
            (horn_points[0][0] + 2, horn_points[0][1] + 1),
            (horn_points[1][0] - 2, horn_points[1][1] + 2),
            (horn_points[2][0] - 1, horn_points[2][1] - 1),
        ])
        # glow crack on horn
        pygame.draw.line(s, p["horn_glow"], horn_points[1], horn_points[3], 2)
    else:
        for hf in (-1, 1):
            horn_base = hx + hf * (hr - 2)
            horn_tip = hx + hf * (hr + 22 + horn_frame_off)
            tip_y = hy - 22 - horn_frame_off
            # main horn
            pygame.draw.polygon(s, p["horn_dark"], [
                (horn_base, hy - 4), (horn_tip, tip_y), (horn_base - hf * 4, hy - 6)
            ])
            # lighter inner
            pygame.draw.polygon(s, p["horn_light"], [
                (horn_base + hf * 1, hy - 5), (horn_tip - hf * 2, tip_y + 2),
                (horn_base + hf * 1, hy - 5)
            ])
            # glow rune on horn
            grx = (horn_base + horn_tip) // 2
            gry = (hy - 4 + tip_y) // 2
            pygame.draw.circle(s, p["horn_glow"], (grx, gry), 3)
            pygame.draw.line(s, p["horn_glow"], (horn_base + hf * 2, hy - 6), (grx, gry), 1)
            pygame.draw.line(s, p["horn_glow"], (grx, gry), (horn_tip - hf * 1, tip_y + 2), 1)

    # --- eyes (glowing) ---
    esp = 7 if dir != "side" else 5
    so = 2 if dir == "side" else 0
    glint_frame = frame % 2
    for ex in (hx - esp + so, hx + esp + so):
        # eye glow aura
        eg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(eg, (255, 150, 50, 40), (ex, hy), 7)
        s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        # eye white (fiery)
        pygame.draw.circle(s, p["eye_white"], (ex, hy), 4)
        pupil_c = p["eye_pupil"]
        # pupil
        pygame.draw.circle(s, pupil_c, (ex, hy), 2)
        # glint
        if glint_frame:
            pygame.draw.circle(s, (255, 255, 255, 220), (ex - 1, hy - 1), 1)

    # --- glowing eye trail / brow flames ---
    for brx in (hx - esp + so - 4, hx + esp + so + 4):
        pygame.draw.polygon(s, p["accent"], [
            (brx, hy - 6), (brx + (1 if brx > hx else -1) * 4, hy - 12), (brx, hy - 4)
        ], 1)

    # --- flaming maw ---
    maw_y = hy + 9
    if dir == "side":
        maw_pts = [(hx + so - 4, maw_y), (hx + so + 6, maw_y + 3), (hx + so - 2, maw_y + 7)]
        pygame.draw.polygon(s, p["skin_dark"], maw_pts)
        for ti in range(3):
            tx = hx + so - 2 + ti * 3
            pygame.draw.polygon(s, (255, 255, 240), [(tx, maw_y + 1), (tx - 1, maw_y + 4), (tx + 1, maw_y + 4)])
        # inner fire glow
        pygame.draw.circle(s, (255, 150, 30, 80), (hx + so, maw_y + 3), 4)
        # flame tongue
        flame_pts = [(hx + so - 2, maw_y + 3), (hx + so + frame - 3, maw_y + 12 + (frame % 2)),
                     (hx + so + 1, maw_y + 3)]
        pygame.draw.polygon(s, (255, 200, 50, 120), flame_pts)
    else:
        maw_pts = [(hx - 6, maw_y), (hx + 6, maw_y), (hx + 4, maw_y + 7), (hx - 4, maw_y + 7)]
        pygame.draw.polygon(s, p["skin_dark"], maw_pts)
        for ti in range(4):
            tx = hx - 5 + ti * 3
            pygame.draw.polygon(s, (255, 255, 240), [(tx, maw_y + 1), (tx - 1, maw_y + 4), (tx + 1, maw_y + 4)])
        # inner fire glow
        pygame.draw.ellipse(s, (255, 150, 30, 100), (hx - 3, maw_y + 2, 6, 4))
        # flame tongue
        flame_pts = [(hx - 4, maw_y + 4), (hx + frame - 2, maw_y + 13 + (frame % 2) * 2),
                     (hx + 4, maw_y + 4)]
        pygame.draw.polygon(s, (255, 200, 50, 120), flame_pts)

    # --- ember particles floating around ---
    for ei in range(4):
        angle = (frame * 0.8 + ei * 1.57) % 6.28
        dist = 14 + ei * 3 + int(math.sin(frame * 0.5 + ei) * 4)
        ex = cx + int(math.cos(angle) * dist)
        ey = hy - 8 + int(math.sin(angle * 0.7) * dist * 0.5)
        es = max(1, 3 - ei // 2)
        ea = max(30, 100 - ei * 15)
        pygame.draw.circle(s, (*p["ember"][:3], ea), (ex, ey + bob), es)



# ============================================================
# VENOMOUS — serpentine with scales, cobra hood, fangs
# ============================================================
def _draw_venomous(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    sway = [0, 1, 0, -1][frame]
    ty = int(h * 0.64) + bob
    pygame.draw.polygon(s, p["skin_dark"], [(cx - 5 + sway, ty), (cx + sway, ty + 24), (cx + 5 + sway, ty)])
    pygame.draw.polygon(s, p["accent"], [(cx - 4 + sway, ty + 18), (cx + sway, ty + 30), (cx + 4 + sway, ty + 18)])
    bw = int(w * 0.46); bh = int(h * 0.48)
    bx = cx - bw // 2; by = int(h * 0.30) + bob
    pygame.draw.rect(s, p["skin"], (bx + sway // 2, by, bw, bh), border_radius=8)
    pygame.draw.rect(s, p["skin_mid"], (bx + 4 + sway // 2, by + 4, bw - 8, bh - 8), border_radius=6)
    bw2 = bw // 3
    pygame.draw.rect(s, p["belly"], (cx - bw2 // 2 + sway // 2, by + 4, bw2, bh - 8), border_radius=4)
    for row in range(4):
        for col in range(4):
            sx2 = bx + 4 + sway // 2 + col * (bw - 8) // 3
            sy2 = by + 6 + row * 10
            sc = p["scale"] if (row + col) % 2 == 0 else p["scale_light"]
            pygame.draw.ellipse(s, sc, (sx2, sy2, 7, 5))
    arm_sway = [0, 2, 0, -2][frame]
    for ax, fl in [(bx - 4, -1), (bx + bw - 4, 1)]:
        pygame.draw.rect(s, p["skin_dark"], (ax + arm_sway, by + 8 + bob, 6, int(h * 0.26)), border_radius=3)
        for ci in range(3):
            cx2 = ax + 1 + arm_sway + ci * 2 - 1
            cy2 = by + int(h * 0.26) + 4 + bob + ci
            pygame.draw.line(s, p["fang"], (cx2, cy2), (cx2 - fl + 1, cy2 + 5), 2)
    hy = int(h * 0.12) + bob
    if dir != "side":
        pygame.draw.polygon(s, p["skin"],
            [(cx - 16, hy + 6), (cx - 14, hy - 2), (cx, hy - 8), (cx + 14, hy - 2), (cx + 16, hy + 6)])
        pygame.draw.polygon(s, p["skin_mid"],
            [(cx - 10, hy + 4), (cx - 8, hy), (cx, hy - 3), (cx + 8, hy), (cx + 10, hy + 4)])
        for hx2 in (cx - 8, cx + 8):
            pygame.draw.ellipse(s, p["accent_dark"], (hx2 - 3, hy + 1, 6, 4))
    pygame.draw.polygon(s, p["skin"], [(cx, hy - 2), (cx + 11, hy + 6), (cx, hy + 14), (cx - 11, hy + 6)])
    pygame.draw.polygon(s, p["skin_light"], [(cx, hy), (cx + 7, hy + 6), (cx, hy + 11), (cx - 7, hy + 6)])
    esp = 6 if dir != "side" else 5; so = 2 if dir == "side" else 0
    for ex in (cx - esp + so, cx + esp + so):
        pygame.draw.polygon(s, p["eye_white"], [(ex, hy + 2 - 4), (ex + 3, hy + 2), (ex, hy + 2 + 4), (ex - 3, hy + 2)])
    _draw_pupils(s, cx, hy + 2, esp, p["eye_pupil"], so)
    fy = hy + 11
    if dir == "side":
        pygame.draw.polygon(s, p["fang"], [(cx + 1, fy), (cx - 2, fy + 7), (cx + 4, fy + 1)])
    else:
        for fx in (cx - 4, cx + 4):
            pygame.draw.polygon(s, p["fang"], [(fx, fy), (fx - 2, fy + 7), (fx + 2, fy + 7)])
    dx = cx + sway
    pygame.draw.polygon(s, p["accent"], [(dx - 1, by + bh), (dx - 2, by + bh + 7), (dx + 2, by + bh + 7)])


# ============================================================
# ARCANIST — floating mage with robe, hat, runes, aura
# ============================================================
def _draw_arcanist(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    pulse = [0, 3, 0, -3][frame]
    aura = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(aura, p["glow"], (cx, int(h * 0.38) + bob), int(w * 0.42))
    s.blit(aura, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    for wx, wo in [(cx - 7, -1), (cx + 7, 1)]:
        wy = int(h * 0.60) + bob
        pygame.draw.polygon(s, p["robe_dark"],
            [(wx + wo * pulse // 2, wy), (wx + wo * pulse // 2 - 3, wy + 26), (wx + wo * pulse // 2 + 3, wy + 26)])
    bw = int(w * 0.50); bh = int(h * 0.44)
    bx = cx - bw // 2; by = int(h * 0.28) + bob
    pygame.draw.polygon(s, p["robe"], [(bx + 6, by), (bx + bw - 6, by), (bx + bw + 6, by + bh), (bx - 6, by + bh)])
    pygame.draw.polygon(s, p["robe_mid"],
        [(bx + 10, by + 4), (bx + bw - 10, by + 4), (bx + bw, by + bh - 4), (bx, by + bh - 4)])
    pygame.draw.line(s, p["accent"], (bx - 4, by + bh - 6), (bx + bw + 4, by + bh - 6), 2)
    for sy2 in range(by + 12, by + bh - 8, 10):
        sc = p["rune_dark"] if sy2 % 20 == 0 else p["rune"]
        pygame.draw.circle(s, sc, (cx, sy2), 2)
        pygame.draw.circle(s, sc, (cx - 10, sy2 + 4), 1)
        pygame.draw.circle(s, sc, (cx + 10, sy2 + 4), 1)
    for ri in range(3):
        rx = cx + int(14 * math.cos(frame * 1.57 + ri * 2.1))
        ry = by + 14 + ri * 18 + bob
        pygame.draw.circle(s, p["rune"], (rx, ry), 3)
        pygame.draw.circle(s, p["glow_bright"] if ri == frame % 3 else p["glow"], (rx, ry), 5, 1)
    for ox in (cx - 14, cx + 14):
        pygame.draw.circle(s, p["glow_bright"], (ox, by + 14 + bob + pulse // 2), 8)
        pygame.draw.circle(s, p["rune"], (ox, by + 14 + bob + pulse // 2), 4)
        pygame.draw.circle(s, (255, 255, 255, 180), (ox - 1, by + 14 + bob + pulse // 2 - 1), 2)
    hr = int(w * 0.17); hx, hy = cx, int(h * 0.16) + bob
    pygame.draw.circle(s, p["skin"], (hx, hy), hr)
    pygame.draw.circle(s, (200, 185, 215), (hx, hy), hr - 2)
    pygame.draw.polygon(s, p["robe"], [(hx - 14, hy - 2), (hx + 14, hy - 2), (hx + 10, hy - 22), (hx - 10, hy - 22)])
    pygame.draw.polygon(s, p["robe_dark"],
        [(hx - 10, hy - 4), (hx + 10, hy - 4), (hx + 7, hy - 18), (hx - 7, hy - 18)])
    pygame.draw.ellipse(s, p["robe_dark"], (hx - 16, hy - 4, 32, 8))
    pygame.draw.ellipse(s, p["robe"], (hx - 14, hy - 3, 28, 5))
    pygame.draw.rect(s, p["accent"], (hx - 12, hy - 5, 24, 3), border_radius=1)
    pygame.draw.circle(s, p["rune"], (hx, hy - 14), 2)
    esp = 6 if dir != "side" else 5; so = 2 if dir == "side" else 0
    for ex in (hx - esp + so, hx + esp + so):
        pygame.draw.circle(s, p["eye_white"], (ex, hy + 1), 4)
        pygame.draw.circle(s, p["glow_bright"], (ex, hy + 1), 6, 1)
    _draw_pupils(s, hx, hy + 1, esp, p["eye_pupil"], so)
    _draw_glint(s, hx, hy + 1, esp, so)
    pygame.draw.polygon(s, p["skin_dark"], [(hx - 6, hy + 8), (hx + 6, hy + 8), (hx + 4, hy + 18), (hx - 4, hy + 18)])
    pygame.draw.polygon(s, p["skin"], [(hx - 4, hy + 9), (hx + 4, hy + 9), (hx + 2, hy + 15), (hx - 2, hy + 15)])


# ============================================================
# TRICKSTER — agile jester with hood, grin, daggers
# ============================================================
def _draw_trickster(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    lo, ro, la, ra = _walk_offset(frame)
    _draw_leg_pair(s, cx, int(h * 0.62), bob, 9, 18, p, lo, ro, "cloth_dark", "cloth")
    bw = int(w * 0.48); bh = int(h * 0.38)
    bx = cx - bw // 2; by = int(h * 0.34) + bob
    pygame.draw.rect(s, p["cloth"], (bx, by, bw, bh), border_radius=8)
    pygame.draw.rect(s, p["cloth_light"], (bx + 4, by + 4, bw - 8, bh - 8), border_radius=6)
    dia_c = p["accent_dark"]
    pygame.draw.polygon(s, dia_c, [(cx, by + 6), (cx + 6, by + 12), (cx, by + 18), (cx - 6, by + 12)])
    pygame.draw.polygon(s, p["accent"], [(cx, by + 8), (cx + 3, by + 12), (cx, by + 16), (cx - 3, by + 12)])
    _draw_arm_pair(s, bx, bw, by, bob, 6, int(h * 0.26), p, la, ra, "cloth_dark", "cloth", 4)
    hr = int(w * 0.17); hx, hy = cx, int(h * 0.22) + bob
    pygame.draw.circle(s, p["skin"], (hx, hy), hr)
    pygame.draw.circle(s, p["skin_light"], (hx, hy), hr - 2)
    pygame.draw.polygon(s, p["cloth"],
        [(hx - 15, hy + 6), (hx - 13, hy - 6), (hx, hy - 10), (hx + 13, hy - 6), (hx + 15, hy + 6)])
    pygame.draw.polygon(s, p["cloth_dark"],
        [(hx - 11, hy + 4), (hx - 9, hy - 4), (hx, hy - 7), (hx + 9, hy - 4), (hx + 11, hy + 4)])
    pygame.draw.arc(s, p["cloth_light"], (hx - 12, hy - hr - 2, 24, 10), 3.14, 0, 2)
    pygame.draw.polygon(s, p["mask"],
        [(hx - hr + 2, hy), (hx + hr - 2, hy), (hx + hr - 4, hy + hr + 1), (hx - hr + 4, hy + hr + 1)])
    esp = 6 if dir != "side" else 5; so = 3 if dir == "side" else 0
    pygame.draw.circle(s, p["eye_white"], (hx - esp + so, hy), 5)
    pygame.draw.circle(s, p["eye_white"], (hx + esp + so, hy), 4)
    pygame.draw.circle(s, p["eye_pupil"], (hx - esp + so, hy), 2)
    pygame.draw.circle(s, p["eye_pupil"], (hx + esp + so, hy), 2)
    _draw_glint(s, hx, hy, esp, so)
    pygame.draw.line(s, p["mask"], (hx - esp + so - 4, hy - 6), (hx - esp + so + 4, hy - 8), 2)
    pygame.draw.line(s, p["mask"], (hx + esp + so - 4, hy - 6), (hx + esp + so + 4, hy - 4), 2)
    gy = hy + 8; gw = 12 if dir != "side" else 8
    pts = [(hx - gw // 2 + so, gy), (hx - gw // 4 + so, gy + 5), (hx + so, gy + 3),
           (hx + gw // 4 + so, gy + 5), (hx + gw // 2 + so, gy)]
    pygame.draw.lines(s, p["grin"], False, pts, 2)
    for tx in (hx - 3 + so, hx + 3 + so):
        pygame.draw.line(s, p["grin"], (tx, gy + 1), (tx, gy + 3), 1)
    ms = 1 if dir == "side" else -1
    pygame.draw.circle(s, p["accent"], (hx + ms * 10, hy + 6), 2)


# ============================================================
# BOMBER — barrel-body with goggles, fuse, patches
# ============================================================
def _draw_bomber(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    lo, ro, la, ra = _walk_offset(frame)
    wob = [0, 1, 0, -1][frame]
    _draw_leg_pair(s, cx, int(h * 0.64), bob, 11, 14, p, lo, ro, "metal_dark", "metal")
    bw = int(w * 0.58); bh = int(h * 0.42)
    bx = cx - bw // 2; by = int(h * 0.32) + bob
    pygame.draw.rect(s, p["skin"], (bx + wob // 2, by, bw, bh), border_radius=14)
    pygame.draw.rect(s, p["skin_mid"], (bx + 4 + wob // 2, by + 4, bw - 8, bh - 8), border_radius=12)
    for py2 in range(by + 6, by + bh - 4, 8):
        pygame.draw.line(s, p["skin_dark"], (bx + 6 + wob // 2, py2), (bx + bw - 6 + wob // 2, py2), 1)
    for sx2 in range(bx + 6, bx + bw - 6, 10):
        sy2 = by + 5
        pygame.draw.line(s, p["stitch"], (sx2, sy2), (sx2 + 3, sy2 + 4), 2)
        pygame.draw.line(s, p["stitch"], (sx2 + 3, sy2 + 4), (sx2 + 6, sy2), 2)
    by2 = by + int(bh * 0.62)
    pygame.draw.rect(s, p["metal"], (bx - 2 + wob // 2, by2, bw + 4, 7), border_radius=3)
    pygame.draw.rect(s, p["metal_light"], (bx + wob // 2, by2 + 1, bw, 3), border_radius=2)
    pygame.draw.rect(s, p["accent"], (cx - 5 + wob // 2, by2, 10, 7), border_radius=2)
    pygame.draw.rect(s, p["accent_dark"], (cx - 3 + wob // 2, by2 + 1, 6, 5), border_radius=1)
    for bi, bdx in enumerate([-8, 8]):
        bx3 = cx + bdx + wob // 2
        pygame.draw.circle(s, p["accent_dark"], (bx3, by2 + 7), 4)
        pygame.draw.circle(s, p["accent"], (bx3, by2 + 7), 3)
        pygame.draw.line(s, p["fuse"], (bx3, by2 + 4), (bx3 + 2, by2 + 1), 1)
    _draw_arm_pair(s, bx, bw, by, bob, 8, int(h * 0.24), p, la, ra, "metal_dark", "metal", 4)
    hr = int(w * 0.19); hx, hy = cx, int(h * 0.19) + bob
    pygame.draw.circle(s, p["skin"], (hx, hy), hr)
    pygame.draw.circle(s, p["skin_light"], (hx, hy), hr - 3)
    px2 = hx + 8 if dir != "side" else hx + 4
    py3 = hy + 5
    pygame.draw.rect(s, p["skin_dark"], (px2 - 4, py3 - 3, 8, 6), border_radius=2)
    pygame.draw.line(s, p["stitch"], (px2 - 3, py3 - 2), (px2 + 3, py3 + 2), 1)
    pygame.draw.line(s, p["stitch"], (px2 + 3, py3 - 2), (px2 - 3, py3 + 2), 1)
    gw2 = 11 if dir != "side" else 9; gy2 = hy - 1
    if dir == "side":
        pygame.draw.ellipse(s, p["metal"], (hx - gw2 // 2, gy2 - 5, gw2, 10))
        pygame.draw.ellipse(s, p["metal_dark"], (hx - gw2 // 2 + 2, gy2 - 3, gw2 - 4, 6))
    else:
        for gx in (hx - 7, hx + 7):
            pygame.draw.ellipse(s, p["metal"], (gx - gw2 // 2, gy2 - 5, gw2, 10))
            pygame.draw.ellipse(s, p["metal_dark"], (gx - gw2 // 2 + 2, gy2 - 3, gw2 - 4, 6))
            pygame.draw.ellipse(s, (200, 220, 255, 100), (gx - gw2 // 2 + 1, gy2 - 3, 4, 4))
    esp = 6 if dir != "side" else 5; so = 2 if dir == "side" else 0
    for ex in (hx - esp + so, hx + esp + so):
        pygame.draw.circle(s, p["eye_white"], (ex, gy2 + 1), 3)
    _draw_pupils(s, hx, gy2 + 1, esp, p["eye_pupil"], so)
    my2 = gy2 + 9
    pygame.draw.arc(s, p["skin_dark"], (hx - 7, my2 - 2, 14, 8), 0.2, 2.94, 2)
    for tx in range(hx - 4, hx + 5, 4):
        pygame.draw.line(s, p["eye_white"], (tx, my2 + 1), (tx, my2 + 3), 1)
    fy = hy - hr - 3; fx2 = [0, 1, -1, 1][frame]
    pygame.draw.lines(s, p["fuse"], False, [(hx + fx2, fy), (hx + 3 + fx2, fy - 10), (hx + fx2, fy - 18)], 2)
    sy3 = fy - 18; sr = 4 + (frame % 2)
    pygame.draw.circle(s, p["spark"], (hx + fx2 - 1, sy3), sr)
    pygame.draw.circle(s, p["spark_bright"], (hx + fx2 - 1, sy3), sr - 1)
    for ei in range(2):
        ex = hx + fx2 + ei * 4 - 2; ey = sy3 - ei * 4 + 2
        pygame.draw.circle(s, p["accent"], (ex + frame, ey), 2)


# ============================================================
# STALKER — dark assassin with cloak, mask, blade
# ============================================================
def _draw_stalker(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    glide = [0, 1, 0, -1][frame]
    _draw_leg_pair(s, cx, int(h * 0.62), bob, 10, 18, p, 0, 0, "cloth_dark", "cloth")
    bw = int(w * 0.52); bh = int(h * 0.42)
    bx = cx - bw // 2; by = int(h * 0.30) + bob
    pygame.draw.polygon(s, p["cloth"],
        [(bx + 4, by), (bx + bw - 4, by), (bx + bw + 8 + glide, by + bh), (bx - 8 + glide, by + bh)])
    pygame.draw.polygon(s, p["cloth_dark"],
        [(bx + 8, by + 4), (bx + bw - 8, by + 4), (bx + bw - 2 + glide, by + bh - 4), (bx + 2 + glide, by + bh - 4)])
    tear = [(bx + bw + 4 + glide, by + bh - 4), (bx + bw + 10 + glide, by + bh), (bx + bw + 6 + glide, by + bh - 8)]
    pygame.draw.polygon(s, p["cloth_mid"], tear)
    by2 = by + int(bh * 0.60)
    pygame.draw.rect(s, p["cloth_mid"], (bx - 2 + glide, by2, bw + 4, 4), border_radius=2)
    _draw_arm_pair(s, bx, bw, by, bob, 6, int(h * 0.26), p, 0, 0, "cloth_dark", "cloth", 4)
    if dir == "side":
        blade = [(bx + bw + 10, by + int(bh * 0.18)), (bx + bw + 16, by + int(bh * 0.06)),
                 (bx + bw + 20, by + int(bh * 0.38))]
        pygame.draw.polygon(s, p["blade"], blade)
        hl = [(bx + bw + 11, by + int(bh * 0.18)), (bx + bw + 15, by + int(bh * 0.09)),
              (bx + bw + 18, by + int(bh * 0.32))]
        pygame.draw.polygon(s, p["blade_dark"], hl)
        pygame.draw.rect(s, p["metal"], (bx + bw + 5, by + int(bh * 0.14), 6, 14), border_radius=2)
        pygame.draw.circle(s, p["accent"], (bx + bw + 8, by + int(bh * 0.14)), 2)
        pygame.draw.circle(s, p["metal_dark"], (bx + bw + 5, by + int(bh * 0.38)), 3)
    hr = int(w * 0.17); hx, hy = cx, int(h * 0.19) + bob
    pygame.draw.circle(s, p["skin"], (hx, hy), hr)
    pygame.draw.circle(s, p["skin_dark"], (hx, hy), hr - 2)
    pygame.draw.polygon(s, p["cloth"],
        [(hx - 16, hy + 4), (hx - 14, hy - 8), (hx, hy - 12), (hx + 14, hy - 8), (hx + 16, hy + 4)])
    pygame.draw.polygon(s, p["cloth_dark"],
        [(hx - 12, hy + 2), (hx - 10, hy - 5), (hx, hy - 8), (hx + 10, hy - 5), (hx + 12, hy + 2)])
    pygame.draw.arc(s, p["cloth_mid"], (hx - 13, hy - hr - 2, 26, 10), 3.14, 0, 2)
    pygame.draw.polygon(s, p["mask"],
        [(hx - hr + 2, hy - 2), (hx + hr - 2, hy - 2), (hx + hr - 5, hy + hr + 1), (hx - hr + 5, hy + hr + 1)])
    pygame.draw.polygon(s, p["mask_light"],
        [(hx - hr + 4, hy), (hx + hr - 4, hy), (hx + hr - 6, hy + hr - 2), (hx - hr + 6, hy + hr - 2)])
    esp = 6 if dir != "side" else 5; so = 2 if dir == "side" else 0
    for ex in (hx - esp + so, hx + esp + so):
        pygame.draw.circle(s, p["eye_white"], (ex, hy), 4)
        pygame.draw.circle(s, (255, 100, 100, 100), (ex, hy), 6, 1)
    _draw_pupils(s, hx, hy, esp, p["eye_pupil"], so)
    _draw_glint(s, hx, hy, esp, so)
    for ex in (hx - esp + so, hx + esp + so):
        pygame.draw.line(s, p["mask"], (ex - 4, hy - 3), (ex + 4, hy - 3), 2)


# ============================================================
# SKIRMISHER — bird-like scout with crest, beak, warpaint
# ============================================================
def _draw_skirmisher(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    bc = [0, -1, 0, 1][frame]; bo = [0, 2, 0, -2][frame]
    _draw_leg_pair(s, cx, int(h * 0.62), bob, 9, 18, p, bo // 2, bo // 2, "skin_dark", "skin")
    bw = int(w * 0.46); bh = int(h * 0.38)
    bx = cx - bw // 2; by = int(h * 0.34) + bob
    pygame.draw.rect(s, p["skin"], (bx, by, bw, bh), border_radius=10)
    pygame.draw.rect(s, p["skin_light"], (bx + 4, by + 4, bw - 8, bh - 8), border_radius=8)
    for fy2 in range(by + 8, by + bh - 4, 6):
        pygame.draw.polygon(s, p["feather"], [(cx, fy2), (cx - 6, fy2 + 4), (cx, fy2 + 2), (cx + 6, fy2 + 4)])
        pygame.draw.polygon(s, p["feather_light"], [(cx, fy2 + 1), (cx - 3, fy2 + 3), (cx, fy2 + 1), (cx + 3, fy2 + 3)])
    ws = [0, 2, 0, -2][frame]
    for wx, fl in [(bx - 4, -1), (bx + bw - 2, 1)]:
        pygame.draw.rect(s, p["feather_dark"], (wx + ws, by + 6 + bob, 7, int(h * 0.24)), border_radius=3)
        pygame.draw.rect(s, p["feather"], (wx + 1 + ws, by + 8 + bob, 5, int(h * 0.24) - 4), border_radius=2)
        for fi in range(3):
            fx = wx + ws + fi * 2
            fy2 = by + int(h * 0.24) + 2 + bob
            pygame.draw.line(s, p["feather_light"], (fx, fy2), (fx - fl * 2, fy2 + 5), 2)
    hr = int(w * 0.17); hx, hy = cx, int(h * 0.22) + bob + bc // 2
    pygame.draw.circle(s, p["skin"], (hx, hy), hr)
    pygame.draw.circle(s, p["skin_light"], (hx, hy), hr - 2)
    for i, (cx2, cy2) in enumerate([(hx - 9, hy - hr - 3), (hx, hy - hr - 8), (hx + 9, hy - hr - 3)]):
        cpt = [(cx2, cy2 + bc), (cx2 - 4 + i * 3, cy2 - 8 + bc), (cx2 + 2 - i, cy2 - 5 + bc)]
        pygame.draw.polygon(s, p["crest"], cpt)
        cpt2 = [(cx2, cy2 + 1 + bc), (cx2 - 2 + i * 2, cy2 - 5 + bc), (cx2 + 1 - i, cy2 - 3 + bc)]
        pygame.draw.polygon(s, p["crest_light"], cpt2)
    esp = 6 if dir != "side" else 5; so = 2 if dir == "side" else 0
    for ex in (hx - esp + so, hx + esp + so):
        pygame.draw.circle(s, p["eye_white"], (ex, hy - 1), 4)
        pygame.draw.circle(s, p["accent_dark"], (ex, hy - 1), 4, 1)
    _draw_pupils(s, hx, hy - 1, esp, p["eye_pupil"], so)
    _draw_glint(s, hx, hy - 1, esp, so)
    if dir == "side":
        pygame.draw.polygon(s, p["beak"], [(hx + hr - 2, hy + 1), (hx + hr + 10, hy + 4), (hx + hr - 2, hy + 8)])
        pygame.draw.polygon(s, p["beak_dark"], [(hx + hr, hy + 3), (hx + hr + 6, hy + 4), (hx + hr, hy + 6)])
        pygame.draw.circle(s, p["beak_dark"], (hx + hr + 5, hy + 3), 1)
    else:
        pygame.draw.polygon(s, p["beak"], [(hx - 4, hy + 3), (hx, hy + 11), (hx + 4, hy + 3)])
        pygame.draw.polygon(s, p["beak_dark"], [(hx - 2, hy + 4), (hx, hy + 8), (hx + 2, hy + 4)])
        pygame.draw.circle(s, p["beak_dark"], (hx, hy + 3), 1)
    py4 = hy + 6; pww = 10 if dir == "side" else 14
    pygame.draw.line(s, p["warpaint"], (hx - pww // 2, py4), (hx + pww // 2, py4), 3)
    pygame.draw.line(s, p["accent"], (hx - pww // 2 + 1, py4), (hx + pww // 2 - 1, py4), 1)


# ============================================================
# GUARDIAN — heavy knight with armor, shield, plume
# ============================================================
def _draw_guardian(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    lo, ro, la, ra = _walk_offset(frame)
    clank = [0, 0, -1, 0][frame]
    _draw_leg_pair(s, cx, int(h * 0.62), bob, 12, 18, p, lo, ro, "armor_dark", "armor")
    bw = int(w * 0.62); bh = int(h * 0.44)
    bx = cx - bw // 2; by = int(h * 0.30) + bob + clank
    pygame.draw.rect(s, p["armor_dark"], (bx, by, bw, bh), border_radius=8)
    pygame.draw.rect(s, p["armor"], (bx + 3, by + 3, bw - 6, bh - 6), border_radius=7)
    pygame.draw.rect(s, p["armor_light"], (bx + 6, by + 6, bw - 12, bh - 12), border_radius=6)
    for rvy in (by + 8, by + bh - 8):
        for rvx in (bx + 8, bx + bw - 8):
            pygame.draw.circle(s, p["accent_dark"], (rvx, rvy), 2)
            pygame.draw.circle(s, p["accent"], (rvx, rvy), 1)
    er = 7; ey = by + int(bh * 0.48)
    pygame.draw.circle(s, p["crest_dark"], (cx, ey), er)
    pygame.draw.circle(s, p["crest"], (cx, ey), er - 1)
    pygame.draw.circle(s, p["accent"], (cx, ey), er - 3)
    pygame.draw.line(s, p["crest_dark"], (cx, ey - 4), (cx, ey + 4), 2)
    pygame.draw.line(s, p["crest_dark"], (cx - 4, ey), (cx + 4, ey), 2)
    for sdx in (bx - 7, bx + bw - 3):
        pygame.draw.ellipse(s, p["armor"], (sdx, by - 2, 14, 12))
        pygame.draw.ellipse(s, p["armor_light"], (sdx + 2, by, 10, 8))
    _draw_arm_pair(s, bx, bw, by, bob, 8, int(h * 0.26), p, la, ra, "armor_dark", "armor", 4)
    if dir == "side":
        sh = [(bx - 10, by + 2), (bx - 4, by - 4), (bx - 4, by + int(bh * 0.7)), (bx - 10, by + int(bh * 0.65))]
        pygame.draw.polygon(s, p["shield"], sh)
        pygame.draw.polygon(s, p["armor_light"], [(p2[0] + 2, p2[1] + 2) for p2 in sh], 1)
    hr = int(w * 0.17); hx, hy = cx, int(h * 0.20) + bob
    pygame.draw.circle(s, p["armor"], (hx, hy), hr)
    visor = [(hx - hr + 2, hy - 2), (hx + hr - 2, hy - 2), (hx + hr - 6, hy + 6), (hx - hr + 6, hy + 6)]
    pygame.draw.polygon(s, p["armor_light"], visor)
    esp = 6 if dir != "side" else 5; so = 2 if dir == "side" else 0
    _draw_eye_pair(s, hx, hy + 1, esp, p, so)
    py5 = hy - hr - 4
    pl = [(hx - 6, py5), (hx, py5 - 10), (hx + 6, py5)]
    pygame.draw.polygon(s, p["plume"], pl)
    pygame.draw.polygon(s, p["plume_light"], [(hx - 3, py5 - 2), (hx, py5 - 7), (hx + 3, py5 - 2)])


DRAW_FUNCS = {
    "brute": _draw_brute, "venomous": _draw_venomous, "arcanist": _draw_arcanist,
    "trickster": _draw_trickster, "bomber": _draw_bomber, "stalker": _draw_stalker,
    "skirmisher": _draw_skirmisher, "guardian": _draw_guardian,
}


def _make_frame(size, palette, style, direction, bob_offset, frame_idx):
    w, h = size
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    drawer = DRAW_FUNCS.get(style, _draw_brute)
    drawer(s, w, h, w // 2, h // 2, palette, direction, bob_offset, frame_idx)
    return s

