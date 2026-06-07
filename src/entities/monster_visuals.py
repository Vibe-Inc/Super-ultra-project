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
            # iron / steel body shell (warm, weathered)
            "iron": (132, 122, 110), "iron_light": (172, 160, 145), "iron_dark": (62, 55, 48),
            "iron_mid": (102, 92, 80),
            # brass plating / rivets / bolts
            "brass": (200, 165, 80), "brass_light": (235, 205, 130), "brass_dark": (140, 110, 45),
            "brass_mid": (170, 135, 65),
            # copper pipes / accents
            "copper": (192, 110, 60), "copper_light": (225, 150, 100), "copper_dark": (130, 65, 30),
            # furnace glow (ember / boiler heat)
            "ember": (255, 175, 60), "ember_dark": (200, 95, 30), "ember_glow": (255, 215, 130),
            "eye_white": (255, 220, 150), "eye_pupil": (200, 95, 30),
            "eye_glow": (255, 175, 60, 110),
            # dark bolts and rivets
            "rivet": (50, 42, 35), "rivet_light": (115, 100, 85),
            # shield plating (iron with brass trim)
            "shield": (108, 98, 88), "shield_light": (148, 135, 120), "shield_dark": (62, 55, 48),
            "shield_trim": (200, 165, 80), "shield_trim_dark": (140, 110, 45),
            # steam / smoke
            "steam": (220, 220, 225, 90), "smoke": (90, 80, 75, 110),
            "shadow": (0, 0, 0, 48),
        },
        "phantom": {
            "skin": (160, 120, 200), "skin_light": (200, 170, 240), "skin_dark": (80, 50, 130),
            "skin_mid": (130, 90, 170),
            "robe": (60, 30, 90), "robe_light": (100, 60, 140), "robe_dark": (30, 15, 50),
            "accent": (200, 140, 255), "accent_dark": (140, 80, 200),
            "eye_white": (220, 200, 255), "eye_pupil": (180, 80, 255),
            "glow": (180, 140, 240, 60), "glow_bright": (220, 180, 255, 100),
            "wisp": (160, 120, 220, 80), "wisp_bright": (200, 170, 255, 120),
            "shadow": (0, 0, 0, 48),
        },
        "titan": {
            "stone": (140, 130, 115), "stone_light": (180, 170, 155), "stone_dark": (80, 72, 60),
            "stone_mid": (110, 100, 88),
            "rune": (100, 200, 160), "rune_dark": (60, 140, 100), "rune_glow": (140, 240, 200, 80),
            "moss": (60, 100, 50), "moss_light": (90, 140, 75),
            "eye_white": (200, 230, 210), "eye_pupil": (80, 200, 140),
            "crack": (50, 45, 38), "shadow": (0, 0, 0, 48),
        },
        "cryomancer": {
            "robe": (40, 80, 140), "robe_light": (80, 140, 200), "robe_dark": (20, 40, 80),
            "robe_mid": (60, 110, 170),
            "skin": (180, 200, 220), "skin_dark": (100, 120, 140),
            "accent": (140, 200, 255), "accent_dark": (80, 150, 220),
            "eye_white": (200, 230, 255), "eye_pupil": (100, 180, 255),
            "crystal": (160, 220, 255), "crystal_light": (200, 240, 255), "crystal_dark": (100, 170, 230),
            "frost": (180, 230, 255, 70), "glow": (140, 200, 255, 55), "shadow": (0, 0, 0, 48),
        },
        "shadowmancer": {
            "robe": (40, 20, 60), "robe_light": (70, 40, 100), "robe_dark": (20, 10, 35),
            "robe_mid": (55, 30, 80),
            "skin": (100, 80, 120), "skin_dark": (60, 40, 80),
            "accent": (180, 60, 220), "accent_dark": (120, 30, 160),
            "eye_white": (200, 180, 240), "eye_pupil": (180, 60, 255),
            "shadow_energy": (100, 40, 160, 70), "shadow_bright": (160, 80, 220, 100),
            "void": (30, 10, 50), "glow": (140, 60, 200, 55), "shadow": (0, 0, 0, 48),
        },
        "revenant": {
            "armor": (60, 55, 70), "armor_light": (90, 85, 100), "armor_dark": (35, 30, 42),
            "armor_mid": (72, 66, 82),
            "bone": (200, 190, 170), "bone_dark": (140, 130, 115),
            "soul": (120, 220, 180), "soul_dark": (60, 160, 120), "soul_glow": (140, 255, 200, 70),
            "eye_white": (200, 240, 220), "eye_pupil": (60, 200, 140),
            "rune": (80, 200, 150), "rune_dark": (40, 140, 90),
            "tattered": (40, 35, 50), "shadow": (0, 0, 0, 48),
        },
        "molten": {
            "rock": (80, 55, 35), "rock_light": (120, 85, 50), "rock_dark": (45, 28, 15),
            "rock_mid": (65, 42, 25),
            "lava": (255, 140, 30), "lava_bright": (255, 200, 80), "lava_dark": (200, 80, 20),
            "lava_glow": (255, 160, 50, 80),
            "ember": (255, 100, 20), "ember_bright": (255, 180, 60),
            "eye_white": (255, 220, 150), "eye_pupil": (255, 100, 20),
            "crack": (255, 120, 30), "crack_bright": (255, 180, 60),
            "glow": (255, 100, 20, 55), "shadow": (0, 0, 0, 48),
        },
        "stormcaller": {
            "robe": (30, 40, 90), "robe_light": (60, 80, 150), "robe_dark": (15, 20, 50),
            "robe_mid": (45, 60, 120),
            "skin": (170, 180, 210), "skin_dark": (100, 110, 140),
            "accent": (100, 180, 255), "accent_dark": (50, 120, 200),
            "eye_white": (200, 230, 255), "eye_pupil": (80, 160, 255),
            "lightning": (140, 200, 255), "lightning_bright": (200, 230, 255),
            "lightning_dark": (80, 140, 220),
            "glow": (100, 180, 255, 60), "spark": (200, 240, 255, 100),
            "shadow": (0, 0, 0, 48),
        },
        "plaguebearer": {
            "robe": (50, 60, 30), "robe_light": (80, 100, 50), "robe_dark": (25, 30, 15),
            "robe_mid": (65, 78, 38),
            "skin": (110, 130, 80), "skin_dark": (70, 85, 50),
            "accent": (140, 200, 60), "accent_dark": (90, 150, 30),
            "eye_white": (200, 230, 180), "eye_pupil": (160, 200, 60),
            "plague": (120, 180, 50), "plague_bright": (160, 220, 80), "plague_dark": (80, 130, 30),
            "plague_glow": (130, 200, 50, 60),
            "pustule": (180, 220, 80), "pustule_dark": (120, 160, 40),
            "glow": (120, 180, 50, 55), "shadow": (0, 0, 0, 48),
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
# GUARDIAN — large industrial robot: iron chassis, exposed gears, steam
# ============================================================
def _draw_guardian(s, w, h, cx, cy, p, dir, bob, frame):
    # -- heavy ground shadow --
    sh_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(sh_surf, p["shadow"], (cx - 20, h - 8 + bob, 40, 12))
    s.blit(sh_surf, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    lo, ro, la, ra = _walk_offset(frame)
    clank = [0, -1, 0, 1][frame]  # weighty body shift

    # -- mechanical legs: heavy iron limbs with brass knee gears and rivets --
    leg_top = int(h * 0.66) + bob + clank // 2
    leg_bottom = h - 8 + bob
    for side, off in [(-1, lo), (1, ro)]:
        lx = cx + side * 11 + off // 2
        # dark outline
        pygame.draw.rect(s, p["iron_dark"], (lx - 5, leg_top, 10, leg_bottom - leg_top), border_radius=2)
        pygame.draw.rect(s, p["iron"], (lx - 4, leg_top + 1, 8, leg_bottom - leg_top - 2), border_radius=2)
        pygame.draw.line(s, p["iron_light"], (lx - 2, leg_top + 2), (lx - 2, leg_bottom - 2), 1)
        pygame.draw.line(s, p["iron_dark"], (lx + 3, leg_top + 2), (lx + 3, leg_bottom - 2), 1)
        # brass knee band with rivets
        ky = (leg_top + leg_bottom) // 2
        pygame.draw.rect(s, p["brass_dark"], (lx - 5, ky - 3, 10, 6))
        pygame.draw.rect(s, p["brass"], (lx - 4, ky - 2, 8, 4))
        pygame.draw.line(s, p["brass_light"], (lx - 3, ky - 1), (lx + 3, ky - 1), 1)
        pygame.draw.circle(s, p["rivet"], (lx - 2, ky), 1)
        pygame.draw.circle(s, p["rivet"], (lx + 2, ky), 1)
        # copper piston rod visible on the side
        pygame.draw.line(s, p["copper_dark"], (lx + side * 4, ky - 3), (lx + side * 4, ky + 3), 1)
        pygame.draw.line(s, p["copper"], (lx + side * 4, ky - 2), (lx + side * 4, ky + 2), 1)
        # foot (brass-banded iron disc)
        fy = leg_bottom
        pygame.draw.ellipse(s, p["iron_dark"], (lx - 7, fy - 2, 14, 6))
        pygame.draw.ellipse(s, p["iron"], (lx - 6, fy - 2, 12, 5))
        pygame.draw.ellipse(s, p["brass"], (lx - 6, fy - 1, 12, 1))
        pygame.draw.line(s, p["iron_light"], (lx - 4, fy - 1), (lx + 1, fy - 1), 1)
        # steam vent on foot
        pygame.draw.circle(s, p["copper_dark"], (lx, fy - 3), 1)

    # -- steam puff from under feet (ambient atmosphere) --
    steam_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for i, (sx, sy_off) in enumerate([(cx - 14, -2), (cx + 12, -1)]):
        sy = h - 12 + bob + sy_off
        sxs = sx + [0, -1, 1, 0][frame]
        sys = sy - [0, 2, 4, 6][frame]
        for k, (dx, dy, r) in enumerate([(0, 0, 3), (-2, -2, 2), (2, -1, 2)]):
            alpha = [70, 50, 30][k]
            pygame.draw.circle(steam_surf, (*p["steam"][:3], alpha),
                               (sxs + dx, sys + dy), r)
    s.blit(steam_surf, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # -- body: large boxy iron torso with rivets and copper piping --
    bw = int(w * 0.70)
    bh = int(h * 0.50)
    bx = cx - bw // 2
    by = int(h * 0.26) + bob + clank
    # back outline
    pygame.draw.rect(s, p["iron_dark"], (bx - 1, by, bw + 2, bh + 1), border_radius=3)
    # main iron shell
    pygame.draw.rect(s, p["iron"], (bx, by + 1, bw, bh - 2), border_radius=2)
    # top highlight
    pygame.draw.rect(s, p["iron_light"], (bx + 3, by + 1, bw - 6, 2))
    # bottom shadow
    pygame.draw.rect(s, p["iron_dark"], (bx + 3, by + bh - 4, bw - 6, 2))
    # left/right edges
    pygame.draw.line(s, p["iron_light"], (bx + 1, by + 3), (bx + 1, by + bh - 4), 1)
    pygame.draw.line(s, p["iron_dark"], (bx + bw - 2, by + 3), (bx + bw - 2, by + bh - 4), 1)
    # brass seam rivets along edges
    for rvy in range(by + 5, by + bh - 4, 5):
        pygame.draw.circle(s, p["rivet"], (bx + 3, rvy), 1)
        pygame.draw.circle(s, p["rivet"], (bx + bw - 4, rvy), 1)
    # horizontal brass band across middle
    band_y = by + bh // 3
    pygame.draw.rect(s, p["brass_dark"], (bx + 2, band_y, bw - 4, 4))
    pygame.draw.rect(s, p["brass"], (bx + 3, band_y, bw - 6, 3))
    pygame.draw.line(s, p["brass_light"], (bx + 3, band_y), (bx + bw - 4, band_y), 1)
    pygame.draw.circle(s, p["rivet"], (bx + 5, band_y + 1), 1)
    pygame.draw.circle(s, p["rivet"], (bx + bw - 6, band_y + 1), 1)
    # copper pipe running vertically on the right side
    pipe_x = bx + bw - 6
    pygame.draw.line(s, p["copper_dark"], (pipe_x, by + 2), (pipe_x, by + bh - 3), 2)
    pygame.draw.line(s, p["copper"], (pipe_x, by + 2), (pipe_x, by + bh - 3), 1)
    pygame.draw.line(s, p["copper_light"], (pipe_x - 1, by + 3), (pipe_x - 1, by + bh - 4), 1)
    # pipe joint valves
    for vj_y in (by + 8, by + bh - 8):
        pygame.draw.rect(s, p["brass_dark"], (pipe_x - 2, vj_y - 1, 5, 3))
        pygame.draw.rect(s, p["brass"], (pipe_x - 1, vj_y, 3, 1))

    # -- exposed gear cavity (chest) with rotating gear --
    gear_cx = cx - 4
    gear_cy = by + int(bh * 0.65)
    gear_r = 7
    # cavity plate (dark recess)
    pygame.draw.circle(s, p["iron_dark"], (gear_cx, gear_cy), gear_r + 2)
    pygame.draw.circle(s, p["iron_mid"], (gear_cx, gear_cy), gear_r + 1)
    # gear teeth (rotating with frame)
    teeth = 8
    gear_angle = frame * (math.pi / (teeth * 2))  # rotates between frames
    for i in range(teeth):
        a = gear_angle + i * (2 * math.pi / teeth)
        tx1 = gear_cx + int((gear_r - 1) * math.cos(a))
        ty1 = gear_cy + int((gear_r - 1) * math.sin(a))
        tx2 = gear_cx + int((gear_r + 1) * math.cos(a))
        ty2 = gear_cy + int((gear_r + 1) * math.sin(a))
        pygame.draw.line(s, p["brass_dark"], (gear_cx, gear_cy), (tx2, ty2), 2)
        pygame.draw.line(s, p["brass"], (gear_cx, gear_cy), (tx1, ty1), 1)
    # gear body
    pygame.draw.circle(s, p["brass"], (gear_cx, gear_cy), gear_r - 1)
    pygame.draw.circle(s, p["brass_dark"], (gear_cx, gear_cy), gear_r - 1, 1)
    pygame.draw.circle(s, p["brass_mid"], (gear_cx, gear_cy), gear_r - 2)
    # gear hub
    pygame.draw.circle(s, p["iron_dark"], (gear_cx, gear_cy), 2)
    pygame.draw.circle(s, p["copper"], (gear_cx, gear_cy), 1)
    # second smaller gear interlocking
    gear2_cx = gear_cx + gear_r + 3
    gear2_cy = gear_cy - 2
    gear2_r = 4
    gear2_angle = -gear_angle * 1.6  # counter-rotation
    for i in range(6):
        a = gear2_angle + i * (2 * math.pi / 6)
        tx1 = gear2_cx + int((gear2_r - 1) * math.cos(a))
        ty1 = gear2_cy + int((gear2_r - 1) * math.sin(a))
        tx2 = gear2_cx + int((gear2_r + 1) * math.cos(a))
        ty2 = gear2_cy + int((gear2_r + 1) * math.sin(a))
        pygame.draw.line(s, p["copper_dark"], (gear2_cx, gear2_cy), (tx2, ty2), 2)
        pygame.draw.line(s, p["copper"], (gear2_cx, gear2_cy), (tx1, ty1), 1)
    pygame.draw.circle(s, p["copper"], (gear2_cx, gear2_cy), gear2_r - 1)
    pygame.draw.circle(s, p["copper_dark"], (gear2_cx, gear2_cy), 1)

    # -- pressure gauge (next to the gear cavity) --
    gauge_cx = cx + 10
    gauge_cy = by + int(bh * 0.65)
    pygame.draw.circle(s, p["brass_dark"], (gauge_cx, gauge_cy), 4)
    pygame.draw.circle(s, p["brass"], (gauge_cx, gauge_cy), 3)
    pygame.draw.circle(s, p["iron_mid"], (gauge_cx, gauge_cy), 2)
    # gauge needle (wiggles)
    needle = [(-2, 1), (-1, -2), (1, -2), (2, 1)][frame]
    pygame.draw.line(s, p["ember_dark"], (gauge_cx, gauge_cy),
                     (gauge_cx + needle[0], gauge_cy + needle[1]), 1)
    pygame.draw.circle(s, p["rivet"], (gauge_cx, gauge_cy), 1)

    # -- shoulder pauldrons with small gear caps --
    for sdx in (bx - 7, bx + bw - 5):
        pygame.draw.rect(s, p["iron_dark"], (sdx, by - 2, 12, 11), border_radius=3)
        pygame.draw.rect(s, p["iron"], (sdx + 1, by - 1, 10, 9), border_radius=2)
        pygame.draw.line(s, p["iron_light"], (sdx + 2, by), (sdx + 2, by + 7), 1)
        pygame.draw.circle(s, p["rivet"], (sdx + 3, by + 1), 1)
        pygame.draw.circle(s, p["rivet"], (sdx + 8, by + 1), 1)
        # brass band on pauldron
        pygame.draw.line(s, p["brass"], (sdx + 2, by + 5), (sdx + 9, by + 5), 1)
        # small gear cap on top
        cap_gx = sdx + 5
        cap_gy = by - 4
        cap_ang = -frame * math.pi / 4
        for i in range(5):
            a = cap_ang + i * (2 * math.pi / 5)
            tx1 = cap_gx + int(2 * math.cos(a))
            ty1 = cap_gy + int(2 * math.sin(a))
            tx2 = cap_gx + int(3 * math.cos(a))
            ty2 = cap_gy + int(3 * math.sin(a))
            pygame.draw.line(s, p["brass_dark"], (cap_gx, cap_gy), (tx2, ty2), 1)
        pygame.draw.circle(s, p["brass"], (cap_gx, cap_gy), 2)
        pygame.draw.circle(s, p["rivet"], (cap_gx, cap_gy), 1)

    # -- mechanical arms (pistons with brass joints and copper rods) --
    shoulder_y = by + 3
    elbow_y = by + int(bh * 0.50)
    hand_y = by + bh + int(h * 0.05)
    for side, swing in [(-1, la), (1, ra)]:
        sx = cx + side * (bw // 2 - 1)
        ex = sx + side * 3 + swing // 3
        wx = sx + side * 5 + swing
        # shoulder brass cap
        pygame.draw.circle(s, p["iron_dark"], (sx, shoulder_y + 2), 3)
        pygame.draw.circle(s, p["brass"], (sx, shoulder_y + 2), 2)
        pygame.draw.circle(s, p["brass_light"], (sx - 1, shoulder_y + 1), 1)
        # upper arm piston (iron)
        pygame.draw.line(s, p["iron_dark"], (sx, shoulder_y + 3), (ex, elbow_y), 4)
        pygame.draw.line(s, p["iron"], (sx, shoulder_y + 3), (ex, elbow_y), 2)
        # copper rod alongside
        rod_off = side * 3
        pygame.draw.line(s, p["copper_dark"], (sx + rod_off, shoulder_y + 3),
                         (ex + rod_off, elbow_y), 1)
        pygame.draw.line(s, p["copper"], (sx + rod_off, shoulder_y + 4),
                         (ex + rod_off, elbow_y - 1), 1)
        # elbow brass joint
        pygame.draw.circle(s, p["iron_dark"], (ex, elbow_y), 3)
        pygame.draw.circle(s, p["brass"], (ex, elbow_y), 2)
        pygame.draw.circle(s, p["brass_light"], (ex - 1, elbow_y - 1), 1)
        # forearm piston
        pygame.draw.line(s, p["iron_dark"], (ex, elbow_y), (wx, hand_y), 4)
        pygame.draw.line(s, p["iron"], (ex, elbow_y), (wx, hand_y), 2)
        pygame.draw.line(s, p["copper_dark"], (ex + rod_off, elbow_y),
                         (wx + rod_off, hand_y), 1)
        pygame.draw.line(s, p["copper"], (ex + rod_off, elbow_y + 1),
                         (wx + rod_off, hand_y - 1), 1)
        # brass-banded claw hand
        pygame.draw.circle(s, p["iron_dark"], (wx, hand_y), 4)
        pygame.draw.circle(s, p["iron"], (wx, hand_y), 3)
        pygame.draw.circle(s, p["brass"], (wx, hand_y), 1)
        pygame.draw.line(s, p["iron_dark"], (wx, hand_y), (wx + side * 2, hand_y + 3), 2)
        pygame.draw.line(s, p["iron_dark"], (wx, hand_y), (wx - side * 1, hand_y + 3), 2)

    # -- neck (segmented iron collar with brass ring) --
    hr = int(w * 0.18)
    hx = cx
    hy = int(h * 0.20) + bob
    head_bob = [0, -1, 0, 1][frame]
    hy += head_bob
    pygame.draw.rect(s, p["iron_dark"], (hx - 5, hy + hr - 3, 10, 6))
    pygame.draw.rect(s, p["iron"], (hx - 4, hy + hr - 2, 8, 4))
    pygame.draw.line(s, p["brass"], (hx - 4, hy + hr - 1), (hx + 4, hy + hr - 1), 1)
    pygame.draw.line(s, p["iron_dark"], (hx - 4, hy + hr + 1), (hx + 4, hy + hr + 1), 1)
    pygame.draw.circle(s, p["rivet"], (hx - 3, hy + hr), 1)
    pygame.draw.circle(s, p["rivet"], (hx + 3, hy + hr), 1)

    # -- head: domed iron boiler with rivets and brass plates --
    # dome
    pygame.draw.ellipse(s, p["iron_dark"], (hx - hr - 1, hy - hr - 2, hr * 2 + 2, hr * 2 + 3))
    pygame.draw.ellipse(s, p["iron"], (hx - hr, hy - hr - 1, hr * 2, hr * 2 + 1))
    # dome highlight
    pygame.draw.arc(s, p["iron_light"], (hx - hr + 1, hy - hr, hr * 2 - 2, hr * 2 - 1), 2.0, 2.7, 2)
    # brass plate at jaw
    pygame.draw.rect(s, p["brass_dark"], (hx - hr + 3, hy + 1, hr * 2 - 6, 6), border_radius=1)
    pygame.draw.rect(s, p["brass"], (hx - hr + 4, hy + 1, hr * 2 - 8, 4), border_radius=1)
    pygame.draw.line(s, p["brass_light"], (hx - hr + 4, hy + 1), (hx + hr - 4, hy + 1), 1)
    # rivets on the dome
    for r_pos in [(hx - hr + 3, hy - 2), (hx - 4, hy - hr + 3),
                  (hx + 4, hy - hr + 3), (hx + hr - 4, hy - 2),
                  (hx - hr + 5, hy + 2), (hx + hr - 5, hy + 2)]:
        pygame.draw.circle(s, p["rivet"], r_pos, 1)
    pygame.draw.circle(s, p["rivet_light"], (hx - 4, hy - hr + 3), 1)
    # side ear / gauge vents
    for side in (-1, 1):
        ex2 = hx + side * (hr - 1)
        pygame.draw.rect(s, p["brass_dark"], (ex2 - 1, hy - 1, 2, 4))
        pygame.draw.line(s, p["brass_light"], (ex2, hy), (ex2, hy + 2), 1)

    # -- furnace eye (warm ember glow, no futuristic crosshair) --
    eye_y = hy + 1
    eye_x = hx + (2 if dir == "side" else 0)
    # glow aura
    eg = pygame.Surface((18, 18), pygame.SRCALPHA)
    pygame.draw.circle(eg, p["eye_glow"], (9, 9), 8)
    s.blit(eg, (eye_x - 9, eye_y - 9), special_flags=pygame.BLEND_ALPHA_SDL2)
    # outer iron bezel
    pygame.draw.circle(s, p["iron_dark"], (eye_x, eye_y), 7)
    pygame.draw.circle(s, p["iron"], (eye_x, eye_y), 6)
    pygame.draw.circle(s, p["brass"], (eye_x, eye_y), 5, 1)
    # furnace interior
    pygame.draw.circle(s, p["ember_dark"], (eye_x, eye_y), 4)
    pygame.draw.circle(s, p["ember"], (eye_x, eye_y), 3)
    # bright ember center
    pygame.draw.circle(s, p["ember_glow"], (eye_x, eye_y), 2)
    pygame.draw.circle(s, (255, 240, 200), (eye_x, eye_y), 1)
    # aperture slats (industrial)
    for slat_off in (-2, 0, 2):
        pygame.draw.line(s, p["iron_dark"], (eye_x - 3, eye_y + slat_off),
                         (eye_x + 3, eye_y + slat_off), 1)

    # -- smokestack on top of dome (with rising steam) --
    stack_x = hx + 2
    stack_y = hy - hr - 1
    # stack base
    pygame.draw.rect(s, p["iron_dark"], (stack_x - 3, stack_y - 5, 6, 5))
    pygame.draw.rect(s, p["iron"], (stack_x - 2, stack_y - 4, 4, 4))
    pygame.draw.line(s, p["iron_light"], (stack_x - 1, stack_y - 3), (stack_x - 1, stack_y - 1), 1)
    pygame.draw.circle(s, p["rivet"], (stack_x - 1, stack_y - 2), 1)
    pygame.draw.circle(s, p["rivet"], (stack_x + 1, stack_y - 2), 1)
    # stack top
    pygame.draw.rect(s, p["iron_dark"], (stack_x - 3, stack_y - 8, 6, 3))
    pygame.draw.rect(s, p["brass_dark"], (stack_x - 3, stack_y - 9, 6, 1))
    # rising steam puffs
    steam_top = pygame.Surface((w, h), pygame.SRCALPHA)
    for k, (dx, dy) in enumerate([(0, -1), (-2, -3), (2, -2), (-1, -5), (1, -4)]):
        rx = stack_x + dx + [0, -1, 1, 0, -1][frame]
        ry = stack_y - 9 + dy - (frame + k) % 3 - 4
        r = [2, 3, 2, 3, 2][k]
        alpha = [110, 80, 60, 40, 25][k]
        pygame.draw.circle(steam_top, (*p["steam"][:3], alpha), (rx, ry), r)
    s.blit(steam_top, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # -- SHIELD (drawn last so it sits in front of the arm) --
    if dir == "side":
        # prominent heater-style iron shield on the right (leading edge)
        sh_cx = cx + bw // 2 - 1
        sh_cy = by + int(bh * 0.5)
        sw_out = int(w * 0.30)
        sh_h = int(h * 0.58)
        sh_pts = [
            (sh_cx, sh_cy - sh_h // 2),
            (sh_cx + sw_out // 2, sh_cy - sh_h // 4),
            (sh_cx + sw_out // 2, sh_cy + sh_h // 4),
            (sh_cx, sh_cy + sh_h // 2),
            (sh_cx - sw_out // 2, sh_cy + sh_h // 4),
            (sh_cx - sw_out // 2, sh_cy - sh_h // 4),
        ]
        pygame.draw.polygon(s, p["shield_dark"], sh_pts)
        sh_inner = [
            (sh_cx, sh_cy - sh_h // 2 + 1),
            (sh_cx + sw_out // 2 - 1, sh_cy - sh_h // 4 + 1),
            (sh_cx + sw_out // 2 - 1, sh_cy + sh_h // 4 - 1),
            (sh_cx, sh_cy + sh_h // 2 - 1),
            (sh_cx - sw_out // 2 + 1, sh_cy + sh_h // 4 - 1),
            (sh_cx - sw_out // 2 + 1, sh_cy - sh_h // 4 + 1),
        ]
        pygame.draw.polygon(s, p["shield"], sh_inner)
        # brass trim border
        for i in range(len(sh_inner) - 1):
            pygame.draw.line(s, p["shield_trim"], sh_inner[i], sh_inner[i + 1], 1)
        pygame.draw.line(s, p["shield_trim"], sh_inner[5], sh_inner[0], 1)
        pygame.draw.line(s, p["shield_trim_dark"], sh_inner[3], sh_inner[4], 1)
        # left edge highlight
        pygame.draw.line(s, p["shield_light"], sh_inner[4], sh_inner[5], 1)
        # brass rivets on shield
        for riv_pos in [
            (sh_inner[0][0] - 1, sh_inner[0][1] + 3),
            (sh_inner[1][0] - 2, sh_inner[1][1] + 1),
            (sh_inner[2][0] - 2, sh_inner[2][1] - 1),
            (sh_inner[3][0] + 1, sh_inner[3][1] - 3),
            (sh_inner[5][0] + 1, sh_inner[5][1] + 1),
        ]:
            pygame.draw.circle(s, p["brass_dark"], riv_pos, 1)
        # central rotating gear emblem
        emb_cx = sh_cx + 1
        emb_cy = sh_cy
        emb_ang = -frame * math.pi / 5
        for i in range(6):
            a = emb_ang + i * (2 * math.pi / 6)
            tx1 = emb_cx + int(3 * math.cos(a))
            ty1 = emb_cy + int(3 * math.sin(a))
            tx2 = emb_cx + int(4 * math.cos(a))
            ty2 = emb_cy + int(4 * math.sin(a))
            pygame.draw.line(s, p["brass_dark"], (emb_cx, emb_cy), (tx2, ty2), 1)
        pygame.draw.circle(s, p["brass"], (emb_cx, emb_cy), 3)
        pygame.draw.circle(s, p["brass_mid"], (emb_cx, emb_cy), 2)
        pygame.draw.circle(s, p["iron_dark"], (emb_cx, emb_cy), 1)
    else:
        # down/up view: compact hex shield held to the side
        sh_cx = cx + bw // 2 + 5
        sh_cy = by + int(bh * 0.5)
        sw_out = int(w * 0.22)
        sh_h = int(h * 0.44)
        sh_pts = [
            (sh_cx, sh_cy - sh_h // 2),
            (sh_cx + sw_out // 2, sh_cy - sh_h // 4),
            (sh_cx + sw_out // 2, sh_cy + sh_h // 4),
            (sh_cx, sh_cy + sh_h // 2),
            (sh_cx - sw_out // 2, sh_cy + sh_h // 4),
            (sh_cx - sw_out // 2, sh_cy - sh_h // 4),
        ]
        pygame.draw.polygon(s, p["shield_dark"], sh_pts)
        sh_inner = [
            (sh_cx, sh_cy - sh_h // 2 + 1),
            (sh_cx + sw_out // 2 - 1, sh_cy - sh_h // 4 + 1),
            (sh_cx + sw_out // 2 - 1, sh_cy + sh_h // 4 - 1),
            (sh_cx, sh_cy + sh_h // 2 - 1),
            (sh_cx - sw_out // 2 + 1, sh_cy + sh_h // 4 - 1),
            (sh_cx - sw_out // 2 + 1, sh_cy - sh_h // 4 + 1),
        ]
        pygame.draw.polygon(s, p["shield"], sh_inner)
        pygame.draw.line(s, p["shield_trim"], sh_inner[3], sh_inner[4], 1)
        pygame.draw.line(s, p["shield_trim"], sh_inner[4], sh_inner[5], 1)
        pygame.draw.line(s, p["shield_light"], sh_inner[4], sh_inner[5], 1)
        # small gear emblem
        emb_ang = frame * math.pi / 6
        for i in range(5):
            a = emb_ang + i * (2 * math.pi / 5)
            tx1 = sh_cx + int(2 * math.cos(a))
            ty1 = sh_cy + int(2 * math.sin(a))
            tx2 = sh_cx + int(3 * math.cos(a))
            ty2 = sh_cy + int(3 * math.sin(a))
            pygame.draw.line(s, p["brass_dark"], (sh_cx, sh_cy), (tx2, ty2), 1)
        pygame.draw.circle(s, p["brass"], (sh_cx, sh_cy), 2)
        pygame.draw.circle(s, p["iron_dark"], (sh_cx, sh_cy), 1)


# ============================================================
# PHANTOM — ghostly wraith with translucent form and trailing wisps
# ============================================================
def _draw_phantom(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    pulse = [0, 2, 0, -2][frame]
    hover = [0, -3, 0, 3][frame]

    # ghostly aura
    ag = pygame.Surface((w, h), pygame.SRCALPHA)
    aura_r = 28 + (frame % 2) * 4
    pygame.draw.circle(ag, p["glow"], (cx, int(h * 0.45) + bob + hover), aura_r)
    pygame.draw.circle(ag, p["glow_bright"], (cx, int(h * 0.45) + bob + hover), aura_r // 2)
    s.blit(ag, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # trailing wisps below
    for wi in range(3):
        wy = int(h * 0.70) + bob + wi * 6
        wx = cx + int(math.sin(frame * 1.5 + wi * 2.1) * (8 + wi * 3))
        wisp_a = max(20, 80 - wi * 20)
        pygame.draw.ellipse(s, (*p["wisp"][:3], wisp_a),
                           (wx - 6, wy, 12, 8))

    # tattered robe body
    bw = int(w * 0.50); bh = int(h * 0.44)
    bx = cx - bw // 2; by = int(h * 0.30) + bob + hover
    # robe tatters
    pygame.draw.polygon(s, p["robe"],
        [(bx + 4, by), (bx + bw - 4, by), (bx + bw + 6, by + bh), (bx - 6, by + bh)])
    pygame.draw.polygon(s, p["robe_dark"],
        [(bx + 8, by + 4), (bx + bw - 8, by + 4), (bx + bw, by + bh - 4), (bx, by + bh - 4)])
    # inner glow seams
    for sy2 in range(by + 10, by + bh - 6, 8):
        glow_c = p["accent"] if sy2 % 16 == 0 else p["accent_dark"]
        pygame.draw.line(s, glow_c, (cx - 4, sy2), (cx + 4, sy2), 1)

    # arms (wispy, ethereal)
    for ax, fl in [(bx - 6, -1), (bx + bw - 2, 1)]:
        arm_sway = [0, 2, 0, -2][frame]
        pygame.draw.polygon(s, p["robe_dark"],
            [(ax + arm_sway, by + 8 + bob), (ax + fl * 14 + arm_sway, by + 20 + bob),
             (ax + fl * 16 + arm_sway, by + 30 + bob), (ax + fl * 4 + arm_sway, by + 22 + bob)])

    # head
    hr = int(w * 0.19); hx, hy = cx, int(h * 0.20) + bob + hover
    pygame.draw.circle(s, p["skin_dark"], (hx, hy + 3), hr)
    pygame.draw.circle(s, p["skin"], (hx, hy), hr)
    pygame.draw.circle(s, p["skin_light"], (hx, hy), hr - 3)

    # hood
    pygame.draw.polygon(s, p["robe"],
        [(hx - hr - 4, hy + 6), (hx - hr + 2, hy - 8), (hx, hy - 14), (hx + hr - 2, hy - 8), (hx + hr + 4, hy + 6)])
    pygame.draw.polygon(s, p["robe_dark"],
        [(hx - hr, hy + 4), (hx - hr + 4, hy - 5), (hx, hy - 10), (hx + hr - 4, hy - 5), (hx + hr, hy + 4)])

    # glowing eyes
    esp = 7 if dir != "side" else 5; so = 2 if dir == "side" else 0
    for ex in (hx - esp + so, hx + esp + so):
        eg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(eg, (180, 120, 255, 50), (ex, hy), 8)
        s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(s, p["eye_white"], (ex, hy), 4)
        pygame.draw.circle(s, p["eye_pupil"], (ex, hy), 2)
        pygame.draw.circle(s, (255, 255, 255, 180), (ex - 1, hy - 1), 1)

    # floating spirit wisps orbiting
    for wi in range(3):
        angle = frame * 1.2 + wi * 2.09
        wr = 16 + wi * 3
        wx = cx + int(math.cos(angle) * wr)
        wy = hy - 4 + int(math.sin(angle * 0.7) * 6)
        ws = max(1, 3 - wi)
        wa = max(30, 100 - wi * 20)
        pygame.draw.circle(s, (*p["accent"][:3], wa), (wx, wy + bob), ws)


# ============================================================
# TITAN — massive stone golem with glowing runes and moss
# ============================================================
def _draw_titan(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    lo, ro, la, ra = _walk_offset(frame)
    clank = [0, -1, 0, 1][frame]

    # heavy legs
    leg_y = int(h * 0.70) + bob
    leg_h = 24
    for lx, off, side in [(cx - 14 + lo, lo, -1), (cx + 4 + ro, ro, 1)]:
        lh = leg_h + abs(off)
        pygame.draw.rect(s, p["stone_dark"], (lx - 2, leg_y, 14, lh), border_radius=3)
        pygame.draw.rect(s, p["stone"], (lx, leg_y + 2, 10, lh - 4), border_radius=2)
        # moss patches
        pygame.draw.ellipse(s, p["moss"], (lx + 1, leg_y + lh - 5, 6, 4))

    # massive torso
    bw = int(w * 0.76); bh = int(h * 0.40)
    bx = cx - bw // 2; by = int(h * 0.28) + bob + clank
    pygame.draw.rect(s, p["stone_dark"], (bx - 1, by, bw + 2, bh + 1), border_radius=4)
    pygame.draw.rect(s, p["stone"], (bx, by + 1, bw, bh - 2), border_radius=3)
    pygame.draw.rect(s, p["stone_light"], (bx + 3, by + 1, bw - 6, 3))
    # stone block lines
    for row in range(3):
        ry = by + 6 + row * (bh // 3)
        pygame.draw.line(s, p["crack"], (bx + 4, ry), (bx + bw - 4, ry), 1)
        for col in range(3):
            rx = bx + 8 + col * ((bw - 16) // 3)
            pygame.draw.line(s, p["crack"], (rx, ry), (rx, ry + bh // 3 - 2), 1)

    # glowing runes on torso
    rune_pulse = [0, 2, 0, -2][frame]
    for ri, (rx, ry) in enumerate([(cx - 12, by + 12), (cx + 12, by + 12),
                                    (cx, by + bh - 10), (cx - 18, by + bh // 2),
                                    (cx + 18, by + bh // 2)]):
        rg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(rg, (*p["rune_glow"][:3], 50 + rune_pulse * 10), (rx, ry), 6)
        s.blit(rg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(s, p["rune"], (rx, ry), 3)
        pygame.draw.circle(s, p["rune_dark"], (rx, ry), 3, 1)
        # rune glow halo
        pygame.draw.circle(s, (*p["rune"][:3], 80), (rx, ry), 5, 1)

    # arms (massive stone fists)
    shoulder_y = by + 4
    for side, swing in [(-1, la), (1, ra)]:
        sx = cx + side * (bw // 2 + 2)
        ex = sx + side * 4 + swing // 2
        wx2 = sx + side * 6 + swing
        # upper arm
        pygame.draw.rect(s, p["stone_dark"], (min(sx, ex), shoulder_y, abs(ex - sx) + 8, 14), border_radius=3)
        pygame.draw.rect(s, p["stone"], (min(sx, ex) + 2, shoulder_y + 2, abs(ex - sx) + 4, 10), border_radius=2)
        # fist
        pygame.draw.circle(s, p["stone_dark"], (wx2, shoulder_y + 18), 7)
        pygame.draw.circle(s, p["stone"], (wx2, shoulder_y + 18), 5)
        # moss on fist
        pygame.draw.ellipse(s, p["moss_light"], (wx2 - 3, shoulder_y + 16, 6, 3))

    # head (blocky stone)
    hr = int(w * 0.20); hx, hy = cx, int(h * 0.18) + bob + clank
    pygame.draw.rect(s, p["stone_dark"], (hx - hr - 1, hy - hr - 1, hr * 2 + 2, hr * 2 + 2), border_radius=4)
    pygame.draw.rect(s, p["stone"], (hx - hr, hy - hr, hr * 2, hr * 2), border_radius=3)
    pygame.draw.rect(s, p["stone_light"], (hx - hr + 3, hy - hr + 2, hr * 2 - 6, 3))

    # glowing eyes
    esp = 7 if dir != "side" else 5; so = 2 if dir == "side" else 0
    for ex2 in (hx - esp + so, hx + esp + so):
        eg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(eg, (*p["rune"][:3], 60), (ex2, hy), 7)
        s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(s, p["eye_white"], (ex2, hy), 4)
        pygame.draw.circle(s, p["eye_pupil"], (ex2, hy), 2)
        pygame.draw.circle(s, (255, 255, 255, 180), (ex2 - 1, hy - 1), 1)

    # moss on shoulders
    for sx2 in (bx - 4, bx + bw - 6):
        pygame.draw.ellipse(s, p["moss"], (sx2, by - 3, 8, 5))
        pygame.draw.ellipse(s, p["moss_light"], (sx2 + 2, by - 2, 4, 3))


# ============================================================
# CRYOMANCER — ice mage with crystal staff and frost aura
# ============================================================
def _draw_cryomancer(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    pulse = [0, 2, 0, -2][frame]
    hover = [0, -2, 0, 2][frame]

    # frost aura
    ag = pygame.Surface((w, h), pygame.SRCALPHA)
    aura_r = 22 + (frame % 2) * 3
    pygame.draw.circle(ag, p["frost"], (cx, int(h * 0.42) + bob + hover), aura_r)
    s.blit(ag, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # frost particles floating
    for fi in range(4):
        angle = frame * 0.9 + fi * 1.57
        dist = 18 + fi * 3 + int(math.sin(frame * 0.6 + fi) * 4)
        fx = cx + int(math.cos(angle) * dist)
        fy = int(h * 0.40) + bob + hover + int(math.sin(angle * 0.7) * dist * 0.5)
        fs = max(1, 3 - fi // 2)
        fa = max(30, 90 - fi * 15)
        pygame.draw.circle(s, (*p["crystal"][:3], fa), (fx, fy), fs)

    # robe
    bw = int(w * 0.50); bh = int(h * 0.44)
    bx = cx - bw // 2; by = int(h * 0.30) + bob + hover
    pygame.draw.polygon(s, p["robe"], [(bx + 6, by), (bx + bw - 6, by), (bx + bw + 6, by + bh), (bx - 6, by + bh)])
    pygame.draw.polygon(s, p["robe_mid"],
        [(bx + 10, by + 4), (bx + bw - 10, by + 4), (bx + bw, by + bh - 4), (bx, by + bh - 4)])
    # crystal trim on robe
    pygame.draw.line(s, p["accent"], (bx - 4, by + bh - 6), (bx + bw + 4, by + bh - 6), 2)
    for sy2 in range(by + 12, by + bh - 8, 10):
        cc = p["crystal_dark"] if sy2 % 20 == 0 else p["crystal"]
        pygame.draw.circle(s, cc, (cx, sy2), 2)

    # arms
    for ax, fl in [(cx - 7, -1), (cx + 7, 1)]:
        wy2 = int(h * 0.58) + bob + hover
        pygame.draw.polygon(s, p["robe_dark"],
            [(ax + pulse // 2, wy2), (ax + fl * 3 + pulse // 2, wy2 + 26), (ax + fl * 5 + pulse // 2, wy2 + 26)])

    # crystal staff (right side)
    if dir == "side":
        staff_x = cx + 14
        staff_top = by - 6
        staff_bot = by + bh + 10
        pygame.draw.line(s, p["crystal_dark"], (staff_x, staff_top), (staff_x - 2, staff_bot), 3)
        pygame.draw.line(s, p["crystal"], (staff_x, staff_top + 1), (staff_x - 2, staff_bot - 1), 1)
        # crystal on top
        crystal_pts = [(staff_x, staff_top - 8), (staff_x - 4, staff_top),
                       (staff_x, staff_top + 4), (staff_x + 4, staff_top)]
        pygame.draw.polygon(s, p["crystal"], crystal_pts)
        pygame.draw.polygon(s, p["crystal_light"], crystal_pts, 1)
        # crystal glow
        cg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(cg, (*p["crystal"][:3], 60), (staff_x, staff_top - 2), 8)
        s.blit(cg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # head
    hr = int(w * 0.17); hx, hy = cx, int(h * 0.18) + bob + hover
    pygame.draw.circle(s, p["skin"], (hx, hy), hr)
    pygame.draw.circle(s, (200, 220, 240), (hx, hy), hr - 2)
    # pointed hat
    pygame.draw.polygon(s, p["robe"], [(hx - 14, hy - 2), (hx + 14, hy - 2), (hx + 10, hy - 24), (hx - 10, hy - 24)])
    pygame.draw.polygon(s, p["robe_dark"],
        [(hx - 10, hy - 4), (hx + 10, hy - 4), (hx + 7, hy - 20), (hx - 7, hy - 20)])
    pygame.draw.ellipse(s, p["robe_dark"], (hx - 16, hy - 4, 32, 8))
    pygame.draw.rect(s, p["accent"], (hx - 12, hy - 5, 24, 3), border_radius=1)
    # crystal on hat
    pygame.draw.polygon(s, p["crystal"], [(hx, hy - 18), (hx - 3, hy - 14), (hx, hy - 12), (hx + 3, hy - 14)])

    # eyes
    esp = 6 if dir != "side" else 5; so = 2 if dir == "side" else 0
    for ex3 in (hx - esp + so, hx + esp + so):
        pygame.draw.circle(s, p["eye_white"], (ex3, hy + 1), 4)
        pygame.draw.circle(s, p["eye_pupil"], (ex3, hy + 1), 2)
    _draw_glint(s, hx, hy + 1, esp, so)


# ============================================================
# SHADOWMANCER — dark hooded mage with shadow energy and void eyes
# ============================================================
def _draw_shadowmancer(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    pulse = [0, 2, 0, -2][frame]
    hover = [0, -2, 0, 2][frame]

    # shadow aura
    ag = pygame.Surface((w, h), pygame.SRCALPHA)
    aura_r = 24 + (frame % 2) * 3
    pygame.draw.circle(ag, p["glow"], (cx, int(h * 0.42) + bob + hover), aura_r)
    s.blit(ag, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # shadow wisps orbiting
    for wi in range(3):
        angle = frame * 1.4 + wi * 2.09
        wr = 16 + wi * 2
        wx = cx + int(math.cos(angle) * wr)
        wy = int(h * 0.40) + bob + hover + int(math.sin(angle * 0.6) * 8)
        ws = max(1, 3 - wi)
        wa = max(30, 90 - wi * 18)
        pygame.draw.circle(s, (*p["accent"][:3], wa), (wx, wy), ws)

    # tattered robe
    bw = int(w * 0.48); bh = int(h * 0.44)
    bx = cx - bw // 2; by = int(h * 0.30) + bob + hover
    pygame.draw.polygon(s, p["robe"],
        [(bx + 4, by), (bx + bw - 4, by), (bx + bw + 8, by + bh), (bx - 8, by + bh)])
    pygame.draw.polygon(s, p["robe_dark"],
        [(bx + 8, by + 4), (bx + bw - 8, by + 4), (bx + bw - 2, by + bh - 4), (bx + 2, by + bh - 4)])
    # shadow energy seams
    for sy2 in range(by + 10, by + bh - 6, 8):
        sc = p["accent"] if sy2 % 16 == 0 else p["accent_dark"]
        pygame.draw.line(s, sc, (cx - 4, sy2), (cx + 4, sy2), 1)

    # arms
    for ax, fl in [(bx - 4, -1), (bx + bw - 2, 1)]:
        arm_sway = [0, 2, 0, -2][frame]
        pygame.draw.polygon(s, p["robe_dark"],
            [(ax + arm_sway, by + 8 + bob), (ax + fl * 14 + arm_sway, by + 20 + bob),
             (ax + fl * 16 + arm_sway, by + 30 + bob), (ax + fl * 4 + arm_sway, by + 22 + bob)])
        # shadow energy in hand
        hand_x = ax + fl * 14 + arm_sway
        hand_y = by + 20 + bob
        eg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(eg, (*p["shadow_energy"][:3], 60), (hand_x, hand_y), 6)
        s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # head
    hr = int(w * 0.18); hx, hy = cx, int(h * 0.20) + bob + hover
    pygame.draw.circle(s, p["skin_dark"], (hx, hy + 3), hr)
    pygame.draw.circle(s, p["skin"], (hx, hy), hr)
    pygame.draw.circle(s, p["skin_dark"], (hx, hy), hr - 2)

    # deep hood
    pygame.draw.polygon(s, p["void"],
        [(hx - hr - 6, hy + 8), (hx - hr, hy - 6), (hx, hy - 16), (hx + hr, hy - 6), (hx + hr + 6, hy + 8)])
    pygame.draw.polygon(s, p["robe_dark"],
        [(hx - hr - 2, hy + 6), (hx - hr + 2, hy - 3), (hx, hy - 12), (hx + hr - 2, hy - 3), (hx + hr + 2, hy + 6)])

    # glowing void eyes
    esp = 7 if dir != "side" else 5; so = 2 if dir == "side" else 0
    for ex4 in (hx - esp + so, hx + esp + so):
        eg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(eg, (*p["accent"][:3], 60), (ex4, hy), 8)
        s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(s, p["eye_white"], (ex4, hy), 4)
        pygame.draw.circle(s, p["eye_pupil"], (ex4, hy), 3)
        pygame.draw.circle(s, (255, 200, 255, 180), (ex4 - 1, hy - 1), 1)
        # shadow flare from eyes
        flare_len = 6 + pulse
        flare_dir = 1 if ex4 > hx else -1
        pygame.draw.line(s, (*p["accent"][:3], 120), (ex4, hy),
                        (ex4 + flare_dir * flare_len, hy - 2), 2)


# ============================================================
# REVENANT — undead warrior with soul-glow runes and tattered armor
# ============================================================
def _draw_revenant(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    lo, ro, la, ra = _walk_offset(frame)
    pulse = [0, 2, 0, -2][frame]

    # spectral soul trail
    for si in range(3):
        sy = int(h * 0.65) + bob + si * 5
        sx = cx + int(math.sin(frame * 1.2 + si * 1.5) * (6 + si * 2))
        sa = max(20, 80 - si * 20)
        pygame.draw.circle(s, (*p["soul"][:3], sa), (sx, sy), 2 + si)

    # heavy legs with bone joints
    leg_y = int(h * 0.72) + bob
    for lx, off, side in [(cx - 12 + lo, lo, -1), (cx + 4 + ro, ro, 1)]:
        lh = 20 + abs(off)
        pygame.draw.rect(s, p["armor_dark"], (lx - 1, leg_y, 13, lh), border_radius=3)
        pygame.draw.rect(s, p["armor"], (lx + 1, leg_y + 2, 9, lh - 4), border_radius=2)
        # bone joint
        pygame.draw.circle(s, p["bone"], (lx + 5, leg_y + lh // 2), 3)
        pygame.draw.circle(s, p["bone_dark"], (lx + 5, leg_y + lh // 2), 3, 1)

    # torso armor with glowing runes
    bw = int(w * 0.55); bh = int(h * 0.38)
    bx = cx - bw // 2; by = int(h * 0.32) + bob
    pygame.draw.rect(s, p["armor_dark"], (bx - 1, by, bw + 2, bh + 1), border_radius=4)
    pygame.draw.rect(s, p["armor"], (bx, by + 1, bw, bh - 2), border_radius=3)
    pygame.draw.rect(s, p["armor_light"], (bx + 3, by + 1, bw - 6, 3))
    # glowing rune lines
    for ry in range(by + 8, by + bh - 4, 8):
        rc = p["rune"] if ry % 16 == 0 else p["rune_dark"]
        glow_a = 120 + pulse * 20
        pygame.draw.line(s, rc, (bx + 6, ry), (bx + bw - 6, ry), 1)
        # rune glow
        rg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(rg, (*p["soul"][:3], 30 + pulse * 10), (cx, ry), 5)
        s.blit(rg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # tattered cape
    cape_y = by + bh - 4
    for ci in range(3):
        cape_x = cx - 8 + ci * 8 + [0, 2, 0, -2][frame]
        cape_len = 14 + ci * 3
        pygame.draw.polygon(s, p["tattered"],
            [(cape_x, cape_y), (cape_x - 3, cape_y + cape_len),
             (cape_x + 3, cape_y + cape_len)])

    # arms with bone fists
    for ax, fl in [(bx - 6, -1), (bx + bw - 2, 1)]:
        arm_sway = [0, 2, 0, -2][frame]
        pygame.draw.polygon(s, p["armor_dark"],
            [(ax + arm_sway, by + 6 + bob), (ax + fl * 12 + arm_sway, by + 18 + bob),
             (ax + fl * 14 + arm_sway, by + 28 + bob), (ax + fl * 4 + arm_sway, by + 20 + bob)])
        # bone fist
        fx = ax + fl * 14 + arm_sway
        fy = by + 28 + bob
        pygame.draw.circle(s, p["bone"], (fx, fy), 4)
        pygame.draw.circle(s, p["bone_dark"], (fx, fy), 4, 1)

    # skull head
    hr = int(w * 0.18); hx, hy = cx, int(h * 0.20) + bob
    pygame.draw.circle(s, p["bone_dark"], (hx, hy + 2), hr)
    pygame.draw.circle(s, p["bone"], (hx, hy), hr)
    # hollow eye sockets with soul glow
    esp = 6 if dir != "side" else 4; so = 2 if dir == "side" else 0
    for ex in (hx - esp + so, hx + esp + so):
        eg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(eg, (*p["soul"][:3], 50), (ex, hy), 7)
        s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(s, p["eye_white"], (ex, hy), 3)
        pygame.draw.circle(s, p["eye_pupil"], (ex, hy), 2)
    # jaw line
    pygame.draw.arc(s, p["bone_dark"], (hx - 6, hy + 2, 12, 8), 0.3, math.pi - 0.3, 1)


# ============================================================
# MOLTEN — fire elemental with lava veins and ember aura
# ============================================================
def _draw_molten(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    pulse = [0, 2, 0, -2][frame]
    lo, ro, la, ra = _walk_offset(frame)

    # ember aura
    ag = pygame.Surface((w, h), pygame.SRCALPHA)
    aura_r = 20 + (frame % 2) * 4
    pygame.draw.circle(ag, p["glow"], (cx, int(h * 0.45) + bob), aura_r)
    s.blit(ag, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # flowing lava drips
    for di in range(4):
        angle = frame * 0.8 + di * 1.57
        drip_d = 12 + int(math.sin(angle) * 6)
        dx = cx + int(math.cos(angle) * drip_d)
        dy = int(h * 0.35) + bob + int(math.sin(angle + 1) * 4)
        pygame.draw.circle(s, p["lava"], (dx, dy), 2)
        pygame.draw.circle(s, p["lava_bright"], (dx, dy), 1)

    # rocky legs
    leg_y = int(h * 0.70) + bob
    for lx, off, side in [(cx - 14 + lo, lo, -1), (cx + 4 + ro, ro, 1)]:
        lh = 20 + abs(off)
        pygame.draw.rect(s, p["rock_dark"], (lx - 1, leg_y, 15, lh), border_radius=3)
        pygame.draw.rect(s, p["rock"], (lx + 1, leg_y + 2, 11, lh - 4), border_radius=2)
        # lava crack
        crack_y = leg_y + 6
        pygame.draw.line(s, p["crack"], (lx + 2, crack_y), (lx + 9, crack_y + 4), 2)

    # massive rocky torso
    bw = int(w * 0.65); bh = int(h * 0.38)
    bx = cx - bw // 2; by = int(h * 0.30) + bob
    pygame.draw.rect(s, p["rock_dark"], (bx - 1, by, bw + 2, bh + 1), border_radius=5)
    pygame.draw.rect(s, p["rock"], (bx, by + 1, bw, bh - 2), border_radius=4)
    pygame.draw.rect(s, p["rock_light"], (bx + 3, by + 1, bw - 6, 3))
    # lava veins across torso
    for vy in range(by + 8, by + bh - 4, 7):
        vx = bx + 6 + int(math.sin(frame * 0.8 + vy * 0.1) * 4)
        vc = p["crack_bright"] if vy % 14 == 0 else p["crack"]
        pygame.draw.line(s, vc, (vx, vy), (vx + bw - 12, vy + 2), 2)
        # glow along cracks
        cg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(cg, (*p["lava"][:3], 40 + pulse * 10), (vx + bw // 4, vy), 5)
        s.blit(cg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # arms — rocky fists with lava glow
    for ax, fl in [(bx - 4, -1), (bx + bw - 2, 1)]:
        arm_sway = [0, 2, 0, -2][frame]
        pygame.draw.polygon(s, p["rock_dark"],
            [(ax + arm_sway, by + 6 + bob), (ax + fl * 14 + arm_sway, by + 18 + bob),
             (ax + fl * 16 + arm_sway, by + 28 + bob), (ax + fl * 4 + arm_sway, by + 20 + bob)])
        # lava fist
        fx = ax + fl * 16 + arm_sway
        fy = by + 28 + bob
        fg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(fg, (*p["lava"][:3], 70), (fx, fy), 8)
        s.blit(fg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(s, p["rock_dark"], (fx, fy), 6)
        pygame.draw.circle(s, p["lava"], (fx, fy), 3)

    # head — angular rock with lava eyes
    hr = int(w * 0.19); hx, hy = cx, int(h * 0.18) + bob
    pygame.draw.rect(s, p["rock_dark"], (hx - hr, hy - hr, hr * 2, hr * 2), border_radius=4)
    pygame.draw.rect(s, p["rock"], (hx - hr + 2, hy - hr + 2, hr * 2 - 4, hr * 2 - 4), border_radius=3)
    # lava crack on forehead
    pygame.draw.line(s, p["crack_bright"], (hx - 4, hy - hr + 3), (hx + 4, hy - 2), 2)
    # glowing lava eyes
    esp = 7 if dir != "side" else 5; so = 2 if dir == "side" else 0
    for ex2 in (hx - esp + so, hx + esp + so):
        eg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(eg, (*p["lava"][:3], 60), (ex2, hy), 7)
        s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(s, p["lava_bright"], (ex2, hy), 4)
        pygame.draw.circle(s, p["eye_white"], (ex2, hy), 2)
    # ember particles rising
    for ei in range(3):
        ea = frame * 1.5 + ei * 2.09
        ed = 10 + ei * 4
        ex3 = hx + int(math.cos(ea) * ed)
        ey = hy - hr - 4 - int(frame * 2 % 8) - ei * 3
        er = max(1, 2 - ei // 2)
        pygame.draw.circle(s, (*p["ember"][:3], max(30, 160 - ei * 40)), (ex3, ey), er)


# ============================================================
# STORMCALLER — lightning mage with crackling aura and energy orbs
# ============================================================
def _draw_stormcaller(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    pulse = [0, 2, 0, -2][frame]
    hover = [0, -3, 0, 3][frame]

    # crackling lightning aura
    ag = pygame.Surface((w, h), pygame.SRCALPHA)
    aura_r = 18 + (frame % 2) * 3
    pygame.draw.circle(ag, p["glow"], (cx, int(h * 0.42) + bob + hover), aura_r)
    s.blit(ag, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # floating sparks
    for si in range(5):
        angle = frame * 1.8 + si * 1.26
        sd = 14 + si * 3
        sx = cx + int(math.cos(angle) * sd)
        sy = int(h * 0.40) + bob + hover + int(math.sin(angle * 0.7) * sd * 0.5)
        ss = max(1, 3 - si // 2)
        sa = max(30, 100 - si * 15)
        pygame.draw.circle(s, (*p["spark"][:3], sa), (sx, sy), ss)

    # robe
    bw = int(w * 0.50); bh = int(h * 0.44)
    bx = cx - bw // 2; by = int(h * 0.30) + bob + hover
    pygame.draw.polygon(s, p["robe"], [(bx + 6, by), (bx + bw - 6, by), (bx + bw + 6, by + bh), (bx - 6, by + bh)])
    pygame.draw.polygon(s, p["robe_mid"],
        [(bx + 10, by + 4), (bx + bw - 10, by + 4), (bx + bw, by + bh - 4), (bx, by + bh - 4)])
    # lightning trim
    pygame.draw.line(s, p["accent"], (bx - 2, by + bh - 4), (bx + bw + 2, by + bh - 4), 2)
    # lightning bolt patterns on robe
    for sy2 in range(by + 10, by + bh - 8, 10):
        bolt_x = bx + 8 + int(math.sin(frame * 0.5 + sy2 * 0.1) * 3)
        pygame.draw.line(s, p["accent"], (bolt_x, sy2), (bolt_x + 4, sy2 + 4), 1)
        pygame.draw.line(s, p["accent"], (bolt_x + 4, sy2 + 4), (bolt_x + 1, sy2 + 8), 1)

    # arms with energy
    for ax, fl in [(cx - 6, -1), (cx + 6, 1)]:
        wy2 = int(h * 0.58) + bob + hover
        pygame.draw.polygon(s, p["robe_dark"],
            [(ax + pulse // 2, wy2), (ax + fl * 3 + pulse // 2, wy2 + 24), (ax + fl * 5 + pulse // 2, wy2 + 24)])
        # lightning spark at hand
        hand_x = ax + fl * 5 + pulse // 2
        hand_y = wy2 + 24
        eg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(eg, (*p["accent"][:3], 60), (hand_x, hand_y), 6)
        s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # head
    hr = int(w * 0.17); hx, hy = cx, int(h * 0.18) + bob + hover
    pygame.draw.circle(s, p["skin"], (hx, hy), hr)
    pygame.draw.circle(s, (190, 200, 230), (hx, hy), hr - 2)
    # pointed hat
    pygame.draw.polygon(s, p["robe"], [(hx - 14, hy - 2), (hx + 14, hy - 2), (hx + 10, hy - 26), (hx - 10, hy - 26)])
    pygame.draw.polygon(s, p["robe_dark"],
        [(hx - 10, hy - 4), (hx + 10, hy - 4), (hx + 7, hy - 22), (hx - 7, hy - 22)])
    pygame.draw.ellipse(s, p["robe_dark"], (hx - 16, hy - 4, 32, 8))
    pygame.draw.rect(s, p["accent"], (hx - 12, hy - 5, 24, 3), border_radius=1)
    # lightning bolt on hat
    pygame.draw.line(s, p["accent"], (hx, hy - 22), (hx - 3, hy - 16), 2)
    pygame.draw.line(s, p["accent"], (hx - 3, hy - 16), (hx + 2, hy - 14), 2)

    # eyes
    esp = 6 if dir != "side" else 5; so = 2 if dir == "side" else 0
    for ex3 in (hx - esp + so, hx + esp + so):
        eg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(eg, (*p["accent"][:3], 40), (ex3, hy + 1), 6)
        s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(s, p["eye_white"], (ex3, hy + 1), 4)
        pygame.draw.circle(s, p["eye_pupil"], (ex3, hy + 1), 2)
    _draw_glint(s, hx, hy + 1, esp, so)


# ============================================================
# PLAGUEBEARER — toxic spreader with pustules and plague cloud aura
# ============================================================
def _draw_plaguebearer(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    pulse = [0, 2, 0, -2][frame]

    # toxic aura
    ag = pygame.Surface((w, h), pygame.SRCALPHA)
    aura_r = 20 + (frame % 2) * 3
    pygame.draw.circle(ag, p["plague_glow"], (cx, int(h * 0.45) + bob), aura_r)
    s.blit(ag, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # toxic drip particles
    for di in range(3):
        drip_x = cx + (di - 1) * 10 + int(math.sin(frame * 0.6 + di) * 4)
        drip_y = int(h * 0.60) + bob + int(math.sin(frame * 0.8 + di * 2) * 3)
        pygame.draw.circle(s, (*p["plague"][:3], 140), (drip_x, drip_y), 2)

    # rotting robe
    bw = int(w * 0.50); bh = int(h * 0.44)
    bx = cx - bw // 2; by = int(h * 0.30) + bob
    pygame.draw.polygon(s, p["robe"], [(bx + 4, by), (bx + bw - 4, by), (bx + bw + 6, by + bh), (bx - 6, by + bh)])
    pygame.draw.polygon(s, p["robe_mid"],
        [(bx + 8, by + 4), (bx + bw - 8, by + 4), (bx + bw, by + bh - 4), (bx, by + bh - 4)])
    # rot holes
    for ri in range(3):
        rx = bx + 10 + ri * 12
        ry = by + 8 + ri * 6
        pygame.draw.ellipse(s, p["robe_dark"], (rx, ry, 6, 4))
    # pustules on robe
    for pi in range(4):
        px = bx + 8 + pi * ((bw - 16) // 3)
        py = by + 6 + (pi % 2) * 10
        pglow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(pglow, (*p["pustule"][:3], 50 + pulse * 10), (px, py), 5)
        s.blit(pglow, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(s, p["pustule"], (px, py), 3)
        pygame.draw.circle(s, p["pustule_dark"], (px, py), 3, 1)

    # arms
    for ax, fl in [(bx - 4, -1), (bx + bw - 2, 1)]:
        arm_sway = [0, 2, 0, -2][frame]
        pygame.draw.polygon(s, p["robe_dark"],
            [(ax + arm_sway, by + 8 + bob), (ax + fl * 14 + arm_sway, by + 20 + bob),
             (ax + fl * 16 + arm_sway, by + 30 + bob), (ax + fl * 4 + arm_sway, by + 22 + bob)])

    # head
    hr = int(w * 0.17); hx, hy = cx, int(h * 0.20) + bob
    pygame.draw.circle(s, p["skin_dark"], (hx, hy + 2), hr)
    pygame.draw.circle(s, p["skin"], (hx, hy), hr)
    pygame.draw.circle(s, p["skin_dark"], (hx, hy), hr - 2)
    # hood
    pygame.draw.polygon(s, p["robe"], [(hx - hr - 4, hy + 6), (hx - hr + 2, hy - 8), (hx, hy - 14), (hx + hr - 2, hy - 8), (hx + hr + 4, hy + 6)])
    pygame.draw.polygon(s, p["robe_dark"],
        [(hx - hr, hy + 4), (hx - hr + 4, hy - 5), (hx, hy - 10), (hx + hr - 4, hy - 5), (hx + hr, hy + 4)])
    # glowing sickly eyes
    esp = 6 if dir != "side" else 4; so = 2 if dir == "side" else 0
    for ex4 in (hx - esp + so, hx + esp + so):
        eg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(eg, (*p["accent"][:3], 50), (ex4, hy), 6)
        s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(s, p["eye_white"], (ex4, hy), 3)
        pygame.draw.circle(s, p["eye_pupil"], (ex4, hy), 2)
    # toxic dripping from mouth
    mouth_y = hy + 4
    for mi in range(2):
        md = 3 + mi * 4 + int(math.sin(frame * 0.5 + mi) * 2)
        pygame.draw.circle(s, (*p["plague"][:3], 120 - mi * 30), (hx + (mi - 0) * 3, mouth_y + md), 2)


DRAW_FUNCS = {
    "brute": _draw_brute, "venomous": _draw_venomous, "arcanist": _draw_arcanist,
    "trickster": _draw_trickster, "bomber": _draw_bomber, "stalker": _draw_stalker,
    "skirmisher": _draw_skirmisher, "guardian": _draw_guardian,
    "phantom": _draw_phantom, "titan": _draw_titan,
    "cryomancer": _draw_cryomancer, "shadowmancer": _draw_shadowmancer,
    "revenant": _draw_revenant, "molten": _draw_molten,
    "stormcaller": _draw_stormcaller, "plaguebearer": _draw_plaguebearer,
}


def _make_frame(size, palette, style, direction, bob_offset, frame_idx):
    w, h = size
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    drawer = DRAW_FUNCS.get(style, _draw_brute)
    drawer(s, w, h, w // 2, h // 2, palette, direction, bob_offset, frame_idx)
    return s

