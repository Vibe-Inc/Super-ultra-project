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
            # brass / bronze body shell
            "skin": (170, 130, 70), "skin_light": (220, 180, 110), "skin_dark": (90, 62, 28),
            "skin_mid": (195, 150, 85), "skin_warm": (235, 195, 120),
            # steel/iron for joints, rivets, banded tank sections
            "metal": (140, 130, 120), "metal_light": (190, 180, 168), "metal_dark": (90, 82, 74),
            "rivet": (70, 62, 52), "rivet_light": (160, 150, 135),
            # verdigris patina / copper oxidation accents
            "accent": (95, 165, 145), "accent_dark": (55, 110, 95),
            # glowing eye lens and antenna spark
            "eye_white": (255, 230, 150), "eye_pupil": (240, 140, 50),
            "eye_glow": (255, 200, 80, 110),
            "spark": (255, 210, 60), "spark_bright": (255, 240, 180),
            "fuse": (185, 145, 80), "fuse_light": (215, 175, 105),
            "stitch": (110, 75, 32),
            # leather belt + dynamite sticks
            "belt": (78, 55, 32), "belt_light": (115, 85, 50), "belt_dark": (50, 32, 18),
            "dynamite": (215, 55, 40), "dynamite_dark": (140, 28, 22),
            "dynamite_cap": (235, 200, 130), "dynamite_cap_dark": (185, 150, 90),
            "shadow": (0, 0, 0, 48),
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
            # base teal skin/plumage (raptor-like)
            "skin": (62, 122, 112), "skin_light": (118, 178, 162), "skin_dark": (32, 72, 64),
            "skin_mid": (88, 148, 132),
            # body feathers (darker, layered wing/back plumage)
            "feather": (38, 88, 78), "feather_light": (78, 138, 122), "feather_dark": (22, 52, 46),
            # chest/belly plumage (lighter, contrasting)
            "belly": (172, 210, 192), "belly_light": (208, 232, 215),
            # crest (gold-yellow feather fan on head)
            "crest": (220, 175, 78), "crest_light": (245, 210, 125), "crest_dark": (175, 130, 50),
            # beak (yellow with darker hooked tip)
            "beak": (232, 200, 110), "beak_dark": (175, 140, 60), "beak_tip": (90, 60, 30),
            # warpaint (fierce red tribal stripes)
            "warpaint": (210, 70, 58), "warpaint_dark": (140, 32, 28),
            # talons (dark claws)
            "talon": (60, 50, 45), "talon_dark": (30, 25, 22),
            # javelin weapon
            "wood": (138, 96, 58), "wood_dark": (92, 62, 36), "wood_light": (175, 130, 85),
            "metal": (190, 192, 200), "metal_dark": (122, 125, 135), "metal_light": (225, 228, 235),
            # eyes (amber, fierce predator)
            "eye_white": (255, 240, 180), "eye_pupil": (38, 22, 18),
            "eye_glow": (255, 200, 100, 80),
            "shadow": (0, 0, 0, 48),
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
# BOMBER — brass steampunk automaton: domed helmet, antenna spark,
# segmented tank torso, thin pipe limbs with claw hands & peg feet
# ============================================================
def _draw_bomber(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    lo, ro, la, ra = _walk_offset(frame)
    sway = [0, 1, 0, -1][frame]

    # --- thin pipe legs with peg feet ---
    leg_top = int(h * 0.66) + bob
    leg_bottom = h - 10 + bob
    for side, off in [(-1, lo), (1, ro)]:
        lx = cx + side * 9 + off // 2
        # dark outline pipe
        pygame.draw.line(s, p["metal_dark"], (lx, leg_top), (lx, leg_bottom), 4)
        # brass pipe core
        pygame.draw.line(s, p["skin_mid"], (lx, leg_top), (lx, leg_bottom), 2)
        # knee rivet
        ky = (leg_top + leg_bottom) // 2
        pygame.draw.circle(s, p["metal_dark"], (lx, ky), 2)
        pygame.draw.circle(s, p["rivet_light"], (lx - 1, ky - 1), 1)
        # peg foot (small disc with a heel)
        fx = lx
        fy = leg_bottom
        pygame.draw.ellipse(s, p["metal_dark"], (fx - 5, fy - 1, 10, 4))
        pygame.draw.ellipse(s, p["metal"], (fx - 4, fy - 1, 8, 3))
        pygame.draw.ellipse(s, p["metal_light"], (fx - 3, fy - 1, 4, 1))

    # --- segmented tank torso (banded brass canister, longer) ---
    bw = int(w * 0.28)
    bh = int(h * 0.36)
    bx = cx - bw // 2
    by = int(h * 0.34) + bob
    # outer dark
    pygame.draw.rect(s, p["skin_dark"], (bx - 1 + sway // 2, by, bw + 2, bh), border_radius=8)
    # brass shell
    pygame.draw.rect(s, p["skin"], (bx + sway // 2, by, bw, bh), border_radius=7)
    # left highlight
    pygame.draw.rect(s, p["skin_light"], (bx + 2 + sway // 2, by + 2, 3, bh - 4), border_radius=1)
    # right shadow
    pygame.draw.rect(s, p["skin_dark"], (bx + bw - 5 + sway // 2, by + 2, 3, bh - 4), border_radius=1)
    # horizontal bands (tank segments)
    for band_y in (by + 5, by + bh // 2 - 1, by + bh - 6):
        pygame.draw.line(s, p["metal_dark"], (bx - 1 + sway // 2, band_y),
                         (bx + bw + 1 + sway // 2, band_y), 1)
        pygame.draw.line(s, p["metal_light"], (bx - 1 + sway // 2, band_y + 1),
                         (bx + bw + 1 + sway // 2, band_y + 1), 1)
    # rivets on bands
    for band_y in (by + 5, by + bh // 2 - 1, by + bh - 6):
        for rx in (bx + 3, bx + bw // 2, bx + bw - 4):
            pygame.draw.circle(s, p["rivet"], (rx + sway // 2, band_y), 1)
    # small verdigris pressure gauge near top of chest
    gauge_cx, gauge_cy = cx + sway // 2, by + 9
    pygame.draw.circle(s, p["metal_dark"], (gauge_cx, gauge_cy), 5)
    pygame.draw.circle(s, p["metal_light"], (gauge_cx, gauge_cy), 4)
    pygame.draw.circle(s, p["accent_dark"], (gauge_cx, gauge_cy), 3)
    pygame.draw.line(s, p["accent"], (gauge_cx, gauge_cy),
                     (gauge_cx + 2, gauge_cy - 2), 1)

    # --- leather belt strap around the lower torso (behind the sticks) ---
    belt_y = by + int(bh * 0.66) + sway // 2
    # dark leather wrap that extends slightly past the canister
    pygame.draw.rect(s, p["belt_dark"], (bx - 4 + sway // 2, belt_y - 2, bw + 8, 5), border_radius=1)
    pygame.draw.rect(s, p["belt"], (bx - 3 + sway // 2, belt_y - 2, bw + 6, 4), border_radius=1)
    pygame.draw.rect(s, p["belt_light"], (bx - 3 + sway // 2, belt_y - 2, bw + 6, 1))
    # belt stitch line
    pygame.draw.line(s, p["stitch"], (bx - 2 + sway // 2, belt_y + 1),
                     (bx + bw + 2 + sway // 2, belt_y + 1), 1)
    # tiny belt rivets at the ends
    pygame.draw.circle(s, p["rivet"], (bx - 1 + sway // 2, belt_y), 1)
    pygame.draw.circle(s, p["rivet"], (bx + bw + 1 + sway // 2, belt_y), 1)

    # --- thin pipe arms with claw hands ---
    shoulder_y = by + 3
    elbow_y = by + int(bh * 0.50)
    hand_y = by + bh + int(h * 0.05)
    for side, swing in [(-1, la), (1, ra)]:
        sx = cx + side * (bw // 2 + 1) + sway // 2
        ex = sx + side * 3 + swing // 2
        wx = sx + side * 4 + swing
        # shoulder rivet
        pygame.draw.circle(s, p["rivet"], (sx, shoulder_y + 1), 2)
        pygame.draw.circle(s, p["rivet_light"], (sx - 1, shoulder_y), 1)
        # upper arm
        pygame.draw.line(s, p["metal_dark"], (sx, shoulder_y + 2), (ex, elbow_y), 3)
        pygame.draw.line(s, p["skin_mid"], (sx, shoulder_y + 2), (ex, elbow_y), 1)
        # elbow joint
        pygame.draw.circle(s, p["metal_dark"], (ex, elbow_y), 2)
        # forearm
        pygame.draw.line(s, p["metal_dark"], (ex, elbow_y), (wx, hand_y), 3)
        pygame.draw.line(s, p["skin_mid"], (ex, elbow_y), (wx, hand_y), 1)
        # claw hand (small brass ball with two prongs)
        pygame.draw.circle(s, p["metal_dark"], (wx, hand_y), 3)
        pygame.draw.circle(s, p["skin"], (wx, hand_y), 2)
        pygame.draw.line(s, p["metal_dark"], (wx, hand_y), (wx + side * 2, hand_y + 3), 1)
        pygame.draw.line(s, p["metal_dark"], (wx, hand_y), (wx - side * 1, hand_y + 3), 1)

    # --- domed brass helmet (the iconic head) ---
    hr = int(w * 0.19)
    hx = cx
    hy = int(h * 0.26) + bob
    # shadow ring under the dome
    pygame.draw.ellipse(s, p["metal_dark"], (hx - hr - 1, hy + hr - 2, (hr + 1) * 2, 6))
    # dome base (skull)
    pygame.draw.circle(s, p["skin_dark"], (hx, hy), hr + 1)
    pygame.draw.circle(s, p["skin"], (hx, hy), hr)
    # dome highlight (top-left curve)
    pygame.draw.arc(s, p["skin_warm"], (hx - hr + 2, hy - hr + 2, hr * 2, hr * 2), 2.0, 2.7, 2)
    # equator band (rim of the helmet)
    pygame.draw.line(s, p["metal_dark"], (hx - hr, hy + 2), (hx + hr, hy + 2), 2)
    pygame.draw.line(s, p["metal_light"], (hx - hr, hy + 4), (hx + hr, hy + 4), 1)
    # rivets along the rim
    for rx in (hx - hr + 4, hx - 8, hx + 8, hx + hr - 4):
        pygame.draw.circle(s, p["rivet"], (rx, hy + 3), 1)
    # neck collar (segmented ring under head)
    pygame.draw.rect(s, p["metal_dark"], (hx - 7, hy + hr - 1, 14, 4), border_radius=1)
    pygame.draw.rect(s, p["metal"], (hx - 6, hy + hr, 12, 2), border_radius=1)

    # --- two large round goggle eyes (the signature look) ---
    eye_y = hy - 2
    esp = 8 if dir != "side" else 6
    so = 2 if dir == "side" else 0
    for ex in (hx - esp + so, hx + esp + so):
        # outer dark bezel
        pygame.draw.circle(s, p["metal_dark"], (ex, eye_y), 6)
        # brass bezel
        pygame.draw.circle(s, p["skin_mid"], (ex, eye_y), 5)
        # dark inner lens
        pygame.draw.circle(s, p["rivet"], (ex, eye_y), 4)
        # glowing pupil
        pygame.draw.circle(s, p["eye_pupil"], (ex, eye_y), 3)
        # soft glow
        glow = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(glow, p["eye_glow"], (6, 6), 5)
        s.blit(glow, (ex - 6, eye_y - 6), special_flags=pygame.BLEND_ALPHA_SDL2)
        # bright pupil core
        pygame.draw.circle(s, p["eye_white"], (ex, eye_y), 1)
        # top reflection
        pygame.draw.circle(s, (255, 255, 255, 180), (ex - 1, eye_y - 2), 1)
    # goggle strap across forehead
    pygame.draw.line(s, p["metal_dark"], (hx - hr + 2, eye_y - 2),
                     (hx - esp - 4, eye_y - 3), 1)
    pygame.draw.line(s, p["metal_dark"], (hx + hr - 2, eye_y - 2),
                     (hx + esp + 4, eye_y - 3), 1)

    # --- thin grinning mouth slit (bolted plate) ---
    my = eye_y + 8
    pygame.draw.rect(s, p["skin_dark"], (hx - 6, my - 1, 12, 3), border_radius=1)
    pygame.draw.line(s, p["accent_dark"], (hx - 5, my), (hx + 5, my), 1)
    pygame.draw.circle(s, p["rivet"], (hx - 5, my + 1), 1)
    pygame.draw.circle(s, p["rivet"], (hx + 5, my + 1), 1)

    # --- sparking antenna on top of the dome (kept inside bounds) ---
    ant_base_x = hx + 2
    ant_base_y = hy - hr + 2
    sway_ant = [0, 1, -1, 1][frame]
    # antenna rod
    pygame.draw.line(s, p["metal_dark"], (ant_base_x, ant_base_y),
                     (ant_base_x + sway_ant, ant_base_y - 7), 2)
    pygame.draw.line(s, p["skin_mid"], (ant_base_x, ant_base_y),
                     (ant_base_x + sway_ant, ant_base_y - 7), 1)
    # antenna cap
    cap_x = ant_base_x + sway_ant
    cap_y = ant_base_y - 7
    pygame.draw.circle(s, p["metal_dark"], (cap_x, cap_y), 3)
    pygame.draw.circle(s, p["skin_mid"], (cap_x, cap_y), 2)
    # spark burst
    sr = 4 + (frame % 2)
    pygame.draw.circle(s, p["spark"], (cap_x, cap_y - 1), sr)
    pygame.draw.circle(s, p["spark_bright"], (cap_x, cap_y - 1), sr - 1)
    # flying embers
    for ei, (edx, edy) in enumerate([(3, -1), (-3, -2), (2, -4), (-2, -3)]):
        ex = cap_x + edx + [1, -1, 1, -1][frame] * (ei + 1)
        ey = cap_y + edy - (frame + ei) % 3
        pygame.draw.circle(s, p["accent"], (ex, ey), 1)

    # --- dynamite sticks strapped to the belt (drawn last so they sit in front) ---
    stick_w = 3
    stick_h_list = [6, 8, 6]  # short, tall, short — gives a varied silhouette
    gap = 2
    n_sticks = 3
    total_w = n_sticks * stick_w + (n_sticks - 1) * gap
    start_x = cx - total_w // 2 + sway // 2
    # micro sway for each stick so they look hand-stuffed, not perfectly rigid
    micro = [0, 0, 0, 0][frame]
    for i in range(n_sticks):
        sx = start_x + i * (stick_w + gap) + (1 if i == 1 else 0) * micro
        sh = stick_h_list[i]
        # red stick body (outline + fill)
        pygame.draw.rect(s, p["dynamite_dark"], (sx - 1, belt_y - sh, stick_w + 2, sh), border_radius=1)
        pygame.draw.rect(s, p["dynamite"], (sx, belt_y - sh + 1, stick_w, sh - 1), border_radius=1)
        # tan wax cap on top
        pygame.draw.rect(s, p["dynamite_cap_dark"], (sx - 1, belt_y - sh - 1, stick_w + 2, 1))
        pygame.draw.rect(s, p["dynamite_cap"], (sx, belt_y - sh - 2, stick_w, 1))
        # tiny fuse and spark
        fuse_x = sx + stick_w // 2 + (1 if i % 2 == 0 else 0)
        fuse_y = belt_y - sh - 2
        pygame.draw.line(s, p["fuse"], (fuse_x, fuse_y), (fuse_x + 1, fuse_y - 2), 1)
        pygame.draw.circle(s, p["spark"], (fuse_x + 1, fuse_y - 2), 1)
        # tiny belt strap tying the stick down
        pygame.draw.rect(s, p["belt_dark"], (sx - 1, belt_y - 1, stick_w + 2, 1))


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
# SKIRMISHER — raptor-scout with feathered crest, hooked beak, tribal warpaint
# ============================================================
def _draw_skirmisher(s, w, h, cx, cy, p, dir, bob, frame):
    # -- ground shadow --
    _draw_shadow(s, cx, h, p, bob)

    # -- animation offsets --
    bc = [0, -1, 0, 1][frame]            # head counter-bob
    lo, ro, la, ra = _walk_offset(frame)  # leg/arm walk
    ft = [0, 1, 0, -1][frame]             # feather flutter
    crest_sway = [0, -2, 0, 2][frame]     # crest wind sway
    tail_sway = [-1, 1, 2, -1][frame]     # tail movement
    leg_off_y = [0, 2, 0, -2][frame]      # leg step lift

    # ============================================================
    # LAYER 1 — TAIL FEATHERS (behind body, visible from up/side)
    # ============================================================
    if dir != "down":
        tail_cy = int(h * 0.58) + bob
        tail_x_off = 2 if dir == "side" else 0
        for i in range(5):
            spread = (i - 2) * 3 + tail_sway
            f_len = 22 - abs(i - 2) * 2
            fpx = cx + spread + tail_x_off
            fpy = tail_cy + abs(i - 2)
            # dark outline
            pygame.draw.polygon(s, p["feather_dark"], [
                (fpx - 3, fpy + 1), (fpx, fpy - 1),
                (fpx + 1, fpy + f_len), (fpx + 4, fpy + 1)
            ])
            # main feather
            pygame.draw.polygon(s, p["feather"], [
                (fpx - 2, fpy + 1), (fpx, fpy),
                (fpx + 1, fpy + f_len - 1), (fpx + 3, fpy + 1)
            ])
            # shaft highlight
            pygame.draw.line(s, p["feather_light"], (fpx, fpy + 2), (fpx, fpy + f_len - 3), 1)
            # sub-vanes detail
            for vy in range(fpy + 5, fpy + f_len - 2, 3):
                pygame.draw.line(s, p["feather_dark"], (fpx - 1, vy), (fpx + 1, vy + 1), 1)

    # ============================================================
    # LAYER 2 — LEGS / TALONS
    # ============================================================
    leg_top = int(h * 0.62)
    for lx, off in [(cx - 10 + lo, lo), (cx + 2 + ro, ro)]:
        # thigh (feathered)
        pygame.draw.rect(s, p["feather_dark"], (lx - 1, leg_top + bob, 11, 11), border_radius=3)
        pygame.draw.rect(s, p["feather"], (lx, leg_top + bob + 1, 9, 9), border_radius=2)
        pygame.draw.rect(s, p["feather_light"], (lx + 1, leg_top + bob + 2, 4, 6), border_radius=1)
        # thigh feather scallops
        for fy in range(leg_top + 1, leg_top + 10, 3):
            pygame.draw.line(s, p["feather_dark"], (lx, fy + bob), (lx + 9, fy + bob), 1)
        # shin (thin scaled)
        pygame.draw.rect(s, p["skin_dark"], (lx + 3, leg_top + 11 + bob + off // 2, 5, 12), border_radius=1)
        pygame.draw.rect(s, p["skin"], (lx + 4, leg_top + 12 + bob + off // 2, 3, 10), border_radius=1)
        # scale bands
        for sy in range(leg_top + 14, leg_top + 22, 3):
            pygame.draw.line(s, p["skin_dark"],
                             (lx + 3, sy + bob + off // 2),
                             (lx + 8, sy + bob + off // 2), 1)
        # ankle joint
        pygame.draw.circle(s, p["skin_dark"], (lx + 5, leg_top + 23 + bob + off // 2), 3)
        pygame.draw.circle(s, p["skin_mid"], (lx + 5, leg_top + 23 + bob + off // 2), 2)
        # 3-toe taloned foot
        for tdx in (-4, 0, 4):
            talon_y = leg_top + 25 + bob + off // 2
            tx_end = lx + 5 + tdx
            pygame.draw.line(s, p["talon_dark"], (lx + 5, talon_y), (tx_end, talon_y + 5), 2)
            pygame.draw.line(s, p["talon"], (lx + 5, talon_y - 1), (tx_end, talon_y + 4), 1)
            pygame.draw.circle(s, p["talon_dark"], (tx_end, talon_y + 5), 1)
        # back claw (hallux) sticking up behind
        pygame.draw.line(s, p["talon_dark"], (lx + 5, leg_top + 22 + bob + off // 2),
                         (lx + 3, leg_top + 18 + bob + off // 2), 2)

    # ============================================================
    # LAYER 3 — BODY (feathered torso with belly)
    # ============================================================
    bw = int(w * 0.52)
    bh = int(h * 0.36)
    bx = cx - bw // 2
    by = int(h * 0.32) + bob

    # body silhouette (slightly tapered, bird-like posture)
    pygame.draw.polygon(s, p["feather_dark"], [
        (bx + 4, by), (bx + bw - 4, by),
        (bx + bw - 1, by + bh - 4),
        (bx + bw - 7, by + bh),
        (bx + 7, by + bh),
        (bx + 1, by + bh - 4),
    ])
    # main body
    pygame.draw.polygon(s, p["feather"], [
        (bx + 6, by + 1), (bx + bw - 6, by + 1),
        (bx + bw - 3, by + bh - 5),
        (bx + bw - 8, by + bh - 1),
        (bx + 8, by + bh - 1),
        (bx + 3, by + bh - 5),
    ])
    # inner highlight
    pygame.draw.polygon(s, p["feather_light"], [
        (bx + 9, by + 3), (bx + bw - 9, by + 3),
        (bx + bw - 10, by + bh - 5),
        (bx + 10, by + bh - 5),
    ])

    # belly/chest (lighter plumage)
    belly_w = int(bw * 0.50)
    belly_h = int(bh * 0.75)
    belly_x = cx - belly_w // 2
    belly_y = by + 4
    pygame.draw.polygon(s, p["belly"], [
        (belly_x, belly_y), (belly_x + belly_w, belly_y),
        (belly_x + belly_w - 5, belly_y + belly_h),
        (belly_x + 5, belly_y + belly_h),
    ])
    # belly highlight
    pygame.draw.polygon(s, p["belly_light"], [
        (belly_x + 4, belly_y + 3), (belly_x + belly_w - 4, belly_y + 3),
        (belly_x + belly_w - 8, belly_y + belly_h - 5),
        (belly_x + 8, belly_y + belly_h - 5),
    ])
    # belly centerline feathering (V pattern)
    for vy in range(belly_y + 6, belly_y + belly_h - 4, 4):
        pygame.draw.line(s, p["belly_light"], (cx - 4, vy), (cx, vy + 2), 1)
        pygame.draw.line(s, p["belly_light"], (cx + 4, vy), (cx, vy + 2), 1)

    # scalloped feather rows on the body sides (the dark plumage)
    for row in range(3):
        ry = by + 6 + row * 7
        for col in range(3):
            rx = bx + 5 + col * 4
            if rx < belly_x - 1 or rx > belly_x + belly_w:
                pygame.draw.polygon(s, p["feather_dark"], [
                    (rx, ry), (rx - 2, ry + 4), (rx, ry + 5), (rx + 2, ry + 4)
                ])
                pygame.draw.polygon(s, p["feather_light"], [
                    (rx, ry + 1), (rx - 1, ry + 3), (rx, ry + 4), (rx + 1, ry + 3)
                ])

    # ============================================================
    # LAYER 4 — WINGS (folded, with primary flight feathers)
    # ============================================================
    if dir == "side":
        # single wing visible on the far side
        wx = bx + bw - 1
        wy = by + 2
        # main wing shape
        pygame.draw.polygon(s, p["feather_dark"], [
            (wx, wy), (wx + 8, wy + 4), (wx + 10, wy + int(bh * 0.6)),
            (wx + 3, wy + int(bh * 0.55))
        ])
        pygame.draw.polygon(s, p["feather"], [
            (wx + 1, wy + 1), (wx + 7, wy + 5), (wx + 8, wy + int(bh * 0.55)),
            (wx + 4, wy + int(bh * 0.5))
        ])
        # wing covert scallops
        for cov_y in range(wy + 3, wy + int(bh * 0.5), 4):
            pygame.draw.line(s, p["feather_light"], (wx + 3, cov_y), (wx + 7, cov_y + 2), 1)
        # primary flight feathers (4 long, staggered)
        for fi in range(4):
            fpx = wx + 2 + fi * 2
            fpy = wy + int(bh * 0.45)
            pygame.draw.polygon(s, p["feather_dark"], [
                (fpx, fpy), (fpx + 4, fpy + 2),
                (fpx + 5, fpy + 14 + ft), (fpx + 1, fpy + 12 + ft)
            ])
            pygame.draw.polygon(s, p["feather"], [
                (fpx + 1, fpy + 1), (fpx + 4, fpy + 3),
                (fpx + 4, fpy + 12 + ft), (fpx + 2, fpy + 10 + ft)
            ])
            pygame.draw.line(s, p["feather_light"], (fpx + 1, fpy + 2), (fpx + 3, fpy + 10 + ft), 1)
    elif dir == "up":
        # back view - both wings fanning out
        for wx, fl in [(bx - 5, -1), (bx + bw, 1)]:
            pygame.draw.polygon(s, p["feather_dark"], [
                (wx, by + 1), (wx + fl * 10, by + 5), (wx + fl * 8, by + int(bh * 0.7)),
                (wx - fl * 2, by + int(bh * 0.6))
            ])
            pygame.draw.polygon(s, p["feather"], [
                (wx + fl * 1, by + 2), (wx + fl * 8, by + 6), (wx + fl * 6, by + int(bh * 0.65)),
                (wx, by + int(bh * 0.55))
            ])
            # covert detail
            for cov_y in range(by + 6, by + int(bh * 0.55), 4):
                pygame.draw.line(s, p["feather_light"],
                                 (wx + fl * 2, cov_y),
                                 (wx + fl * 6, cov_y + 2), 1)
            # primary feathers
            for fi in range(3):
                fpx = wx + fl * 1
                fpy = by + int(bh * 0.5) + fi * 3
                pygame.draw.polygon(s, p["feather_dark"], [
                    (fpx, fpy), (fpx + fl * 6, fpy + 2),
                    (fpx + fl * 5, fpy + 10), (fpx - fl * 1, fpy + 7)
                ])
                pygame.draw.polygon(s, p["feather"], [
                    (fpx + fl * 1, fpy + 1), (fpx + fl * 5, fpy + 2),
                    (fpx + fl * 4, fpy + 9), (fpx, fpy + 6)
                ])
    else:  # "down" - wings folded against body, primaries peeking
        for wx, fl in [(bx - 1, -1), (bx + bw - 5, 1)]:
            # main wing (smaller, folded tight)
            pygame.draw.polygon(s, p["feather_dark"], [
                (wx, by + 2), (wx + fl * 4, by + 2),
                (wx + fl * 6, by + int(bh * 0.55)), (wx - fl * 1, by + int(bh * 0.5))
            ])
            pygame.draw.polygon(s, p["feather"], [
                (wx + fl * 1, by + 3), (wx + fl * 3, by + 3),
                (wx + fl * 5, by + int(bh * 0.5)), (wx, by + int(bh * 0.45))
            ])
            # covert detail
            for cov_y in range(by + 5, by + int(bh * 0.45), 4):
                pygame.draw.line(s, p["feather_light"],
                                 (wx + fl * 1, cov_y),
                                 (wx + fl * 4, cov_y + 2), 1)
            # primary feathers (3 peeking out)
            for fi in range(3):
                fpx = wx + fl * 1
                fpy = by + int(bh * 0.4) + fi * 3
                pygame.draw.polygon(s, p["feather_dark"], [
                    (fpx, fpy), (fpx + fl * 5, fpy + 1),
                    (fpx + fl * 4, fpy + 9 + ft), (fpx - fl * 1, fpy + 7)
                ])
                pygame.draw.polygon(s, p["feather"], [
                    (fpx + fl * 1, fpy + 1), (fpx + fl * 4, fpy + 2),
                    (fpx + fl * 3, fpy + 8 + ft), (fpx, fpy + 6)
                ])

    # ============================================================
    # LAYER 5 — JAVELIN (skirmisher's signature weapon, side view)
    # ============================================================
    if dir == "side":
        j_top_x, j_top_y = bx + bw + 6, by - 4
        j_bot_x, j_bot_y = bx + bw - 10, by + int(bh * 0.85)
        # shaft outline
        pygame.draw.line(s, p["wood_dark"], (j_top_x, j_top_y), (j_bot_x, j_bot_y), 3)
        # shaft body
        pygame.draw.line(s, p["wood"], (j_top_x, j_top_y - 1), (j_bot_x, j_bot_y - 1), 1)
        # shaft highlight
        pygame.draw.line(s, p["wood_light"], (j_top_x - 1, j_top_y - 1), (j_bot_x - 1, j_bot_y - 1), 1)
        # metal tip
        pygame.draw.polygon(s, p["metal_dark"], [
            (j_top_x, j_top_y), (j_top_x + 7, j_top_y - 7), (j_top_x + 3, j_top_y + 1)
        ])
        pygame.draw.polygon(s, p["metal"], [
            (j_top_x + 1, j_top_y), (j_top_x + 6, j_top_y - 6), (j_top_x + 3, j_top_y)
        ])
        pygame.draw.line(s, p["metal_light"], (j_top_x + 1, j_top_y - 1), (j_top_x + 5, j_top_y - 5), 1)
        # fletching (red feathers at base)
        pygame.draw.polygon(s, p["warpaint_dark"], [
            (j_bot_x - 1, j_bot_y), (j_bot_x - 7, j_bot_y + 4), (j_bot_x, j_bot_y + 2)
        ])
        pygame.draw.polygon(s, p["warpaint"], [
            (j_bot_x - 1, j_bot_y - 1), (j_bot_x - 6, j_bot_y + 3), (j_bot_x, j_bot_y + 1)
        ])

    # ============================================================
    # LAYER 6 — NECK COLLAR (feathered band where head meets body)
    # ============================================================
    neck_y = by - 2
    pygame.draw.ellipse(s, p["feather_dark"], (cx - 13, neck_y - 1, 26, 8))
    pygame.draw.ellipse(s, p["feather"], (cx - 12, neck_y, 24, 6))
    # collar accent beads
    for bx_b in (cx - 7, cx, cx + 7):
        pygame.draw.circle(s, p["warpaint"], (bx_b, neck_y + 3), 2)
        pygame.draw.circle(s, p["warpaint_dark"], (bx_b, neck_y + 3), 2, 1)
        pygame.draw.circle(s, p["warpaint"], (bx_b - 1, neck_y + 2), 1)

    # ============================================================
    # LAYER 7 — HEAD
    # ============================================================
    hr = int(w * 0.18)
    hx = cx
    hy = int(h * 0.20) + bob + bc // 2

    if dir == "up":
        # back of head - feathered nape
        pygame.draw.circle(s, p["feather_dark"], (hx, hy), hr + 1)
        pygame.draw.circle(s, p["feather"], (hx, hy), hr)
        pygame.draw.circle(s, p["feather_light"], (hx, hy), hr - 4)
        # nape feather chevrons
        for fy in range(hy - hr + 5, hy + hr - 6, 5):
            for fx in (hx - 4, hx, hx + 4):
                pygame.draw.line(s, p["feather_dark"], (fx - 2, fy + 2), (fx, fy), 1)
                pygame.draw.line(s, p["feather_dark"], (fx + 2, fy + 2), (fx, fy), 1)
    else:
        # front/side head
        pygame.draw.circle(s, p["skin_dark"], (hx, hy), hr + 1)
        pygame.draw.circle(s, p["skin"], (hx, hy), hr)
        pygame.draw.circle(s, p["skin_light"], (hx, hy), hr - 3)
        # cheek/jaw
        pygame.draw.circle(s, p["skin_mid"], (hx, hy + 4), hr - 5)
        # brow ridge
        brow_y = hy - 4
        if dir == "down":
            for brx in (hx - 8, hx + 8):
                pygame.draw.polygon(s, p["feather_dark"], [
                    (brx - 4, brow_y), (brx + 4, brow_y),
                    (brx + 2, brow_y - 3), (brx - 2, brow_y - 3)
                ])
        else:
            pygame.draw.arc(s, p["feather_dark"], (hx - 5, hy - hr + 2, hr + 4, 6), 3.14, 0, 2)

    # ============================================================
    # LAYER 8 — CREST (tall feather fan)
    # ============================================================
    crest_count = 7 if dir != "side" else 5
    crest_base_x = hx - 1
    crest_base_y = hy - hr + 2 + bc // 2
    for i in range(crest_count):
        spread = (i - (crest_count - 1) / 2) * 3
        f_len = 20 - abs(i - (crest_count - 1) / 2) * 1.4
        fpx = crest_base_x + int(spread) + crest_sway
        fpy = crest_base_y - abs(int(i - (crest_count - 1) / 2))
        # main feather
        pygame.draw.polygon(s, p["crest_dark"], [
            (fpx - 2, fpy + 2), (fpx, fpy - int(f_len)), (fpx + 2, fpy + 2)
        ])
        pygame.draw.polygon(s, p["crest"], [
            (fpx - 1, fpy + 1), (fpx, fpy - int(f_len) + 1), (fpx + 1, fpy + 1)
        ])
        # highlight shaft
        pygame.draw.line(s, p["crest_light"], (fpx, fpy - 2), (fpx, fpy - int(f_len) + 4), 1)
        # sub-vanes
        for vy in range(fpy - int(f_len) + 4, fpy - 2, 2):
            pygame.draw.line(s, p["crest_dark"], (fpx - 1, vy), (fpx, vy + 1), 1)

    # ============================================================
    # LAYER 9 — FACE (eyes, beak, warpaint)
    # ============================================================
    if dir == "side":
        # one eye visible
        ex, ey = hx + 4, hy - 1
        # amber eye glow
        eg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(eg, p["eye_glow"], (ex, ey), 7)
        s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        # eye
        pygame.draw.circle(s, p["eye_white"], (ex, ey), 4)
        pygame.draw.circle(s, p["eye_pupil"], (ex, ey), 2)
        pygame.draw.circle(s, (255, 255, 255, 220), (ex - 1, ey - 1), 1)

        # hooked beak (side profile)
        pygame.draw.polygon(s, p["beak_dark"], [
            (hx + hr - 1, hy - 2), (hx + hr + 12, hy + 1),
            (hx + hr + 4, hy + 4), (hx + hr - 1, hy + 5)
        ])
        pygame.draw.polygon(s, p["beak"], [
            (hx + hr, hy - 1), (hx + hr + 10, hy + 1),
            (hx + hr + 3, hy + 3), (hx + hr, hy + 4)
        ])
        # beak tip (darker hooked point)
        pygame.draw.polygon(s, p["beak_tip"], [
            (hx + hr + 7, hy + 1), (hx + hr + 12, hy + 1), (hx + hr + 5, hy + 3)
        ])
        # beak top highlight
        pygame.draw.line(s, p["crest_light"], (hx + hr + 1, hy), (hx + hr + 8, hy + 1), 1)
        # nostril
        pygame.draw.circle(s, p["beak_tip"], (hx + hr + 3, hy), 1)

        # warpaint - diagonal slash through eye + cheek stripe
        pygame.draw.line(s, p["warpaint_dark"], (ex - 8, ey - 1), (ex + 5, ey - 3), 2)
        pygame.draw.line(s, p["warpaint"], (ex - 7, ey - 1), (ex + 4, ey - 3), 1)
        # cheek stripe (3 marks)
        for cdy in (5, 8, 11):
            pygame.draw.line(s, p["warpaint"], (hx - 4, hy + cdy), (hx - 6, hy + cdy + 1), 2)
        # jaw dot
        pygame.draw.circle(s, p["warpaint"], (hx - 2, hy + 14), 1)

    elif dir == "down":
        esp = 7
        for ex in (hx - esp, hx + esp):
            # amber eye glow
            eg = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.circle(eg, p["eye_glow"], (ex, hy - 1), 8)
            s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
            # eye
            pygame.draw.circle(s, p["eye_white"], (ex, hy - 1), 4)
            pygame.draw.circle(s, p["eye_pupil"], (ex, hy - 1), 2)
            pygame.draw.circle(s, (255, 255, 255, 220), (ex - 1, hy - 2), 1)

        # hooked beak (front view)
        pygame.draw.polygon(s, p["beak_dark"], [
            (hx - 3, hy + 2), (hx + 3, hy + 2),
            (hx + 5, hy + 8), (hx + 1, hy + 13),
            (hx - 1, hy + 13), (hx - 5, hy + 8)
        ])
        pygame.draw.polygon(s, p["beak"], [
            (hx - 2, hy + 3), (hx + 2, hy + 3),
            (hx + 3, hy + 7), (hx, hy + 11),
            (hx, hy + 11), (hx - 3, hy + 7)
        ])
        # central ridge highlight
        pygame.draw.line(s, p["crest_light"], (hx, hy + 4), (hx, hy + 10), 1)
        # hooked tip
        pygame.draw.polygon(s, p["beak_tip"], [
            (hx - 2, hy + 9), (hx + 2, hy + 9), (hx, hy + 13)
        ])
        # nostrils
        pygame.draw.circle(s, p["beak_tip"], (hx - 2, hy + 4), 1)
        pygame.draw.circle(s, p["beak_tip"], (hx + 2, hy + 4), 1)

        # warpaint - twin diagonal slashes through both eyes
        for ex in (hx - esp, hx + esp):
            pygame.draw.line(s, p["warpaint_dark"], (ex - 6, hy - 5), (ex + 6, hy + 1), 2)
            pygame.draw.line(s, p["warpaint"], (ex - 5, hy - 5), (ex + 5, hy + 1), 1)
        # forehead diamond
        pygame.draw.polygon(s, p["warpaint_dark"], [
            (hx, hy - 8), (hx + 4, hy - 4), (hx, hy), (hx - 4, hy - 4)
        ])
        pygame.draw.polygon(s, p["warpaint"], [
            (hx, hy - 7), (hx + 3, hy - 4), (hx, hy - 1), (hx - 3, hy - 4)
        ])
        # cheek stripes (angled down and out)
        pygame.draw.line(s, p["warpaint_dark"], (hx - 9, hy + 5), (hx - 12, hy + 12), 2)
        pygame.draw.line(s, p["warpaint"], (hx - 9, hy + 5), (hx - 11, hy + 11), 1)
        pygame.draw.line(s, p["warpaint_dark"], (hx + 9, hy + 5), (hx + 12, hy + 12), 2)
        pygame.draw.line(s, p["warpaint"], (hx + 9, hy + 5), (hx + 11, hy + 11), 1)
        # jaw dot trio
        pygame.draw.circle(s, p["warpaint"], (hx - 4, hy + 15), 1)
        pygame.draw.circle(s, p["warpaint"], (hx, hy + 16), 1)
        pygame.draw.circle(s, p["warpaint"], (hx + 4, hy + 15), 1)


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

