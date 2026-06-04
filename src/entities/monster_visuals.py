from __future__ import annotations

from functools import lru_cache

import pygame


def build_monster_animations(style: str, size: tuple[int, int]) -> dict[str, list[pygame.Surface]]:
    return _build_monster_animations_cached((style or "").lower(), tuple(size))


@lru_cache(maxsize=16)
def _build_monster_animations_cached(style: str, size: tuple[int, int]) -> dict[str, list[pygame.Surface]]:
    palette = _palette_for(style)
    offsets = [0, 1, 0, -1]

    animations: dict[str, list[pygame.Surface]] = {
        "down": [],
        "up": [],
        "side": [],
    }

    for offset in offsets:
        animations["down"].append(_make_frame(size, palette, style, "down", offset))
        animations["up"].append(_make_frame(size, palette, style, "up", offset))
        animations["side"].append(_make_frame(size, palette, style, "side", offset))

    return animations


def _palette_for(style: str) -> dict[str, tuple[int, int, int] | tuple[int, int, int, int]]:
    palettes = {
        "brute": {
            "body": (130, 75, 48),
            "body_light": (165, 105, 70),
            "body_dark": (85, 42, 25),
            "accent": (170, 50, 50),
            "eye_white": (255, 245, 230),
            "eye_pupil": (200, 40, 40),
            "horn": (100, 60, 35),
            "spike": (145, 90, 60),
            "shadow": (0, 0, 0, 50),
        },
        "venomous": {
            "body": (45, 120, 70),
            "body_light": (65, 175, 95),
            "body_dark": (20, 70, 40),
            "accent": (180, 240, 100),
            "eye_white": (230, 250, 140),
            "eye_pupil": (200, 50, 50),
            "fang": (240, 240, 230),
            "scale": (35, 100, 55),
            "shadow": (0, 0, 0, 50),
        },
        "arcanist": {
            "body": (45, 85, 145),
            "body_light": (110, 155, 215),
            "body_dark": (25, 45, 85),
            "accent": (200, 180, 255),
            "eye_white": (230, 240, 255),
            "eye_pupil": (100, 180, 255),
            "runes": (255, 220, 100),
            "glow": (150, 180, 255, 60),
            "shadow": (0, 0, 0, 50),
        },
        "trickster": {
            "body": (145, 52, 62),
            "body_light": (215, 115, 125),
            "body_dark": (75, 22, 32),
            "accent": (120, 30, 40),
            "eye_white": (245, 230, 210),
            "eye_pupil": (180, 60, 60),
            "ear": (165, 72, 82),
            "grin": (240, 220, 200),
            "mask": (50, 50, 60),
            "shadow": (0, 0, 0, 50),
        },
        "bomber": {
            "body": (145, 98, 42),
            "body_light": (215, 165, 95),
            "body_dark": (85, 52, 20),
            "accent": (220, 70, 50),
            "eye_white": (250, 230, 190),
            "eye_pupil": (100, 100, 100),
            "fuse": (180, 120, 60),
            "spark": (255, 200, 50),
            "metal": (165, 155, 145),
            "stitch": (130, 85, 35),
            "shadow": (0, 0, 0, 50),
        },
        "stalker": {
            "body": (50, 55, 65),
            "body_light": (85, 90, 105),
            "body_dark": (30, 32, 40),
            "accent": (190, 55, 55),
            "eye_white": (220, 220, 230),
            "eye_pupil": (200, 50, 50),
            "cloak": (60, 65, 78),
            "mask": (35, 38, 45),
            "blade": (180, 180, 190),
            "shadow": (0, 0, 0, 50),
        },
        "skirmisher": {
            "body": (70, 125, 115),
            "body_light": (115, 175, 160),
            "body_dark": (40, 78, 68),
            "accent": (205, 185, 100),
            "eye_white": (240, 245, 230),
            "eye_pupil": (90, 140, 130),
            "feather": (185, 145, 90),
            "crest": (205, 165, 95),
            "beak": (220, 190, 120),
            "shadow": (0, 0, 0, 50),
        },
        "guardian": {
            "body": (105, 105, 115),
            "body_light": (145, 145, 160),
            "body_dark": (60, 60, 70),
            "accent": (205, 185, 80),
            "eye_white": (240, 240, 245),
            "eye_pupil": (80, 80, 90),
            "armor": (135, 130, 120),
            "armor_light": (170, 165, 150),
            "shield": (155, 145, 125),
            "crest": (210, 180, 60),
            "shadow": (0, 0, 0, 50),
        },
    }
    return palettes.get(style, palettes["brute"])


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _draw_shadow(surface, cx, width, palette):
    pygame.draw.ellipse(surface, palette["shadow"], (cx - 14, width - 8, 28, 10))


def _draw_legs(surface, cx, y, leg_w, leg_h, color, offset=0):
    gap = 10
    lx = cx - gap - leg_w // 2
    rx = cx + gap - leg_w // 2
    ly = y + offset
    pygame.draw.rect(surface, color, (lx, ly, leg_w, leg_h), border_radius=3)
    pygame.draw.rect(surface, color, (rx, ly, leg_w, leg_h), border_radius=3)


def _draw_arm(surface, x, y, w, h, color, flip=1, border_radius=4):
    pygame.draw.rect(surface, color, (x, y, w, h), border_radius=border_radius)


def _draw_eyes(surface, cx, ey, spacing, eye_white, pupil, side_offset=0):
    lx = cx - spacing + side_offset
    rx = cx + spacing + side_offset
    pygame.draw.circle(surface, eye_white, (lx, ey), 4)
    pygame.draw.circle(surface, eye_white, (rx, ey), 4)
    pygame.draw.circle(surface, pupil, (lx, ey), 2)
    pygame.draw.circle(surface, pupil, (rx, ey), 2)


def _draw_slit_eyes(surface, cx, ey, spacing, eye_color, pupil, side_offset=0):
    lx = cx - spacing + side_offset
    rx = cx + spacing + side_offset
    for ex in (lx, rx):
        pts = [(ex, ey - 4), (ex + 3, ey), (ex, ey + 4), (ex - 3, ey)]
        pygame.draw.polygon(surface, eye_color, pts)
    pygame.draw.circle(surface, pupil, (lx, ey), 1)
    pygame.draw.circle(surface, pupil, (rx, ey), 1)


# ---------------------------------------------------------------------------
# Style-specific drawers
# ---------------------------------------------------------------------------

def _draw_brute(surface, width, height, cx, cy, palette, direction, bob):
    _draw_shadow(surface, cx, height, palette)

    # legs
    _draw_legs(surface, cx, int(height * 0.62), 14, 18, palette["body_dark"], bob)

    # body - wide and bulky
    bw, bh = int(width * 0.72), int(height * 0.45)
    bx, by = cx - bw // 2, int(height * 0.30) + bob
    pygame.draw.rect(surface, palette["body"], (bx, by, bw, bh), border_radius=10)
    # lighter belly
    pygame.draw.rect(surface, palette["body_light"], (bx + 6, by + 6, bw - 12, bh - 12), border_radius=8)

    # arms - thick
    arm_w, arm_h = 10, int(height * 0.30)
    arm_y = by + 8
    _draw_arm(surface, bx - 6, arm_y + bob, arm_w, arm_h, palette["body_dark"])
    _draw_arm(surface, bx + bw - 4, arm_y + bob, arm_w, arm_h, palette["body_dark"])

    # shoulder spikes
    sp = [(bx - 4, by - 2), (bx - 6, by + 10), (bx + 6, by + 4)]
    pygame.draw.polygon(surface, palette["spike"], sp)
    sp2 = [(bx + bw + 4, by - 2), (bx + bw + 6, by + 10), (bx + bw - 6, by + 4)]
    pygame.draw.polygon(surface, palette["spike"], sp2)

    # head - large round
    head_r = int(width * 0.20)
    hx, hy = cx, int(height * 0.20) + bob
    pygame.draw.circle(surface, palette["body"], (hx, hy), head_r)

    # horns
    if direction == "side":
        horn = [(hx + head_r - 2, hy - 4), (hx + head_r + 14, hy - 12), (hx + head_r, hy + 6)]
        pygame.draw.polygon(surface, palette["horn"], horn)
    else:
        hp = [
            [(hx - head_r + 2, hy - 4), (hx - head_r - 12, hy - 12), (hx - head_r + 2, hy + 6)],
            [(hx + head_r - 2, hy - 4), (hx + head_r + 12, hy - 12), (hx + head_r - 2, hy + 6)],
        ]
        for pts in hp:
            pygame.draw.polygon(surface, palette["horn"], pts)

    # eyes - angry
    e_spacing = 7 if direction == "side" else 9
    so = 2 if direction == "side" else 0
    _draw_eyes(surface, hx, hy + 1, e_spacing, palette["eye_white"], palette["eye_pupil"], so)
    # angry eyebrows
    brow_y = hy - 5
    for ex in (hx - e_spacing + so, hx + e_spacing + so):
        pygame.draw.line(surface, palette["body_dark"], (ex - 4, brow_y - 1), (ex + 4, brow_y + 2), 2)

    # chest scar/mark
    scar_y = by + int(bh * 0.5)
    pygame.draw.rect(surface, palette["body_dark"], (bx + 8, scar_y, bw - 16, 4), border_radius=2)


def _draw_venomous(surface, width, height, cx, cy, palette, direction, bob):
    _draw_shadow(surface, cx, height, palette)

    # tail instead of legs
    tail_y = int(height * 0.65) + bob
    tail_pts = [
        (cx - 4, tail_y),
        (cx, tail_y + 14),
        (cx + 4, tail_y),
    ]
    pygame.draw.polygon(surface, palette["body_dark"], tail_pts)
    # tail tip
    tip_pts = [(cx - 3, tail_y + 10), (cx, tail_y + 18), (cx + 3, tail_y + 10)]
    pygame.draw.polygon(surface, palette["accent"], tip_pts)

    # body - elongated, serpentine
    bw, bh = int(width * 0.48), int(height * 0.48)
    bx, by = cx - bw // 2, int(height * 0.30) + bob
    pygame.draw.rect(surface, palette["body"], (bx, by, bw, bh), border_radius=6)
    # scale pattern
    for row in range(3):
        sy = by + 8 + row * 10
        for col in range(3):
            sx = bx + 6 + col * (bw - 12) // 2
            pygame.draw.ellipse(surface, palette["scale"], (sx, sy, 8, 6))

    # arms - thin
    arm_w, arm_h = 7, int(height * 0.28)
    arm_y = by + 6
    _draw_arm(surface, bx - 4, arm_y + bob, arm_w, arm_h, palette["body_dark"], border_radius=3)
    _draw_arm(surface, bx + bw - 3, arm_y + bob, arm_w, arm_h, palette["body_dark"], border_radius=3)

    # head - diamond shape
    head_pts = [
        (cx, int(height * 0.10) + bob),
        (cx + 12, int(height * 0.20) + bob),
        (cx, int(height * 0.30) + bob),
        (cx - 12, int(height * 0.20) + bob),
    ]
    pygame.draw.polygon(surface, palette["body"], head_pts)
    # lighter inner diamond
    inner = [(cx, int(height * 0.13) + bob), (cx + 7, int(height * 0.20) + bob),
             (cx, int(height * 0.27) + bob), (cx - 7, int(height * 0.20) + bob)]
    pygame.draw.polygon(surface, palette["body_light"], inner)

    # eyes - slitted
    e_spacing = 6 if direction == "side" else 7
    so = 2 if direction == "side" else 0
    _draw_slit_eyes(surface, cx, int(height * 0.18) + bob, e_spacing, palette["eye_white"], palette["eye_pupil"], so)

    # fangs
    fang_y = int(height * 0.27) + bob
    if direction != "side":
        for fx in (cx - 4, cx + 4):
            pts = [(fx, fang_y), (fx - 1, fang_y + 6), (fx + 1, fang_y + 6)]
            pygame.draw.polygon(surface, palette["fang"], pts)
    else:
        pts = [(cx + 1, fang_y), (cx, fang_y + 6), (cx + 2, fang_y + 6)]
        pygame.draw.polygon(surface, palette["fang"], pts)

    # venom drips
    for dx in (cx - 8, cx + 8):
        drip_pts = [(dx, by + bh), (dx - 1, by + bh + 6), (dx + 1, by + bh + 6)]
        pygame.draw.polygon(surface, palette["accent"], drip_pts)


def _draw_arcanist(surface, width, height, cx, cy, palette, direction, bob):
    _draw_shadow(surface, cx, height, palette)

    # mystical aura
    aura_r = int(width * 0.45)
    aura_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.circle(aura_surf, palette["glow"], (cx, int(height * 0.40) + bob), aura_r)
    surface.blit(aura_surf, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # legs - floating, just a wisp
    wisp_y = int(height * 0.62) + bob
    for wx in (cx - 6, cx + 6):
        pts = [(wx, wisp_y), (wx - 2, wisp_y + 14), (wx + 2, wisp_y + 14)]
        pygame.draw.polygon(surface, palette["body_dark"], pts)

    # body - robe-like, wider at bottom
    bw, bh = int(width * 0.52), int(height * 0.45)
    bx, by = cx - bw // 2, int(height * 0.28) + bob
    body_pts = [
        (bx + 6, by),
        (bx + bw - 6, by),
        (bx + bw + 4, by + bh),
        (bx - 4, by + bh),
    ]
    pygame.draw.polygon(surface, palette["body"], body_pts)
    # inner lighter area
    inner_pts = [
        (bx + 10, by + 4),
        (bx + bw - 10, by + 4),
        (bx + bw - 2, by + bh - 4),
        (bx + 2, by + bh - 4),
    ]
    pygame.draw.polygon(surface, palette["body_light"], inner_pts)

    # runes on robe
    rune_pos = [
        (cx - 8, by + int(bh * 0.35)),
        (cx + 8, by + int(bh * 0.55)),
        (cx - 6, by + int(bh * 0.75)),
    ]
    for rx, ry in rune_pos:
        pygame.draw.circle(surface, palette["runes"], (rx, ry), 2)
        pygame.draw.circle(surface, palette["runes"], (rx, ry), 4, 1)

    # arms - floating orbs
    orb_off = 12
    orb_y = by + 12
    for ox in (cx - orb_off, cx + orb_off):
        pygame.draw.circle(surface, palette["runes"], (ox, orb_y + bob), 4)
        pygame.draw.circle(surface, palette["body_light"], (ox, orb_y + bob), 3)

    # head - floating with hat
    head_r = int(width * 0.16)
    hx, hy = cx, int(height * 0.17) + bob
    pygame.draw.circle(surface, palette["body_light"], (hx, hy), head_r)

    # hat
    hat_pts = [
        (hx - 12, hy - 4),
        (hx + 12, hy - 4),
        (hx + 8, hy - 18),
        (hx - 8, hy - 18),
    ]
    pygame.draw.polygon(surface, palette["body"], hat_pts)
    # hat brim
    pygame.draw.ellipse(surface, palette["body_dark"], (hx - 14, hy - 6, 28, 8))

    # eyes - glowing
    e_spacing = 5 if direction == "side" else 7
    so = 2 if direction == "side" else 0
    _draw_eyes(surface, hx, hy + 1, e_spacing, palette["eye_white"], palette["eye_pupil"], so)
    # arcane glow around eyes
    for ex in (hx - e_spacing + so, hx + e_spacing + so):
        pygame.draw.circle(surface, palette["glow"], (ex, hy + 1), 6, 1)


def _draw_trickster(surface, width, height, cx, cy, palette, direction, bob):
    _draw_shadow(surface, cx, height, palette)

    # legs - slim, quick
    _draw_legs(surface, cx, int(height * 0.62), 10, 18, palette["body_dark"], bob)

    # body - lean
    bw, bh = int(width * 0.50), int(height * 0.40)
    bx, by = cx - bw // 2, int(height * 0.32) + bob
    pygame.draw.rect(surface, palette["body"], (bx, by, bw, bh), border_radius=6)
    pygame.draw.rect(surface, palette["body_light"], (bx + 4, by + 4, bw - 8, bh - 8), border_radius=5)

    # arms - thin, agile
    arm_w, arm_h = 6, int(height * 0.28)
    arm_y = by + 4
    _draw_arm(surface, bx - 4, arm_y + bob, arm_w, arm_h, palette["body_dark"], border_radius=3)
    _draw_arm(surface, bx + bw - 2, arm_y + bob, arm_w, arm_h, palette["body_dark"], border_radius=3)

    # mask / hood
    hood_y = int(height * 0.15) + bob
    hood_pts = [
        (cx - 14, hood_y + 8),
        (cx - 12, hood_y - 2),
        (cx, hood_y - 6),
        (cx + 12, hood_y - 2),
        (cx + 14, hood_y + 8),
    ]
    pygame.draw.polygon(surface, palette["mask"], hood_pts)

    # head
    head_r = int(width * 0.16)
    hx, hy = cx, int(height * 0.22) + bob
    pygame.draw.circle(surface, palette["body_light"], (hx, hy), head_r)

    # ears - pointed
    for ex in (cx - head_r - 2, cx + head_r + 2):
        ear_pts = [(ex, hy), (ex - 4 * (1 if ex < cx else -1), hy - 8), (ex, hy - 4)]
        pygame.draw.polygon(surface, palette["ear"], ear_pts)

    # eyes - mischievous (one squint)
    e_spacing = 5 if direction == "side" else 7
    so = 2 if direction == "side" else 0
    _draw_eyes(surface, hx, hy, e_spacing, palette["eye_white"], palette["eye_pupil"], so)

    # grin
    grin_y = hy + 7
    grin_w = 10 if direction == "side" else 14
    grin_pts = [
        (hx - grin_w // 2 + so, grin_y),
        (hx - grin_w // 4 + so, grin_y + 4),
        (hx + so, grin_y + 2),
        (hx + grin_w // 4 + so, grin_y + 4),
        (hx + grin_w // 2 + so, grin_y),
    ]
    pygame.draw.lines(surface, palette["grin"], False, grin_pts, 2)

    # rogue mark on cheek
    mark_side = 1 if direction == "side" else -1
    pygame.draw.circle(surface, palette["accent"], (hx + mark_side * 9, hy + 5), 2)


def _draw_bomber(surface, width, height, cx, cy, palette, direction, bob):
    _draw_shadow(surface, cx, height, palette)

    # legs - stubby
    _draw_legs(surface, cx, int(height * 0.65), 12, 14, palette["body_dark"], bob)

    # body - round/barrel
    bw, bh = int(width * 0.60), int(height * 0.42)
    bx, by = cx - bw // 2, int(height * 0.32) + bob
    pygame.draw.rect(surface, palette["body"], (bx, by, bw, bh), border_radius=12)

    # stitch marks across body
    stitch_y = by + 4
    for sx in range(bx + 6, bx + bw - 6, 8):
        pygame.draw.line(surface, palette["stitch"], (sx, stitch_y), (sx + 4, stitch_y + 4), 2)
        pygame.draw.line(surface, palette["stitch"], (sx + 4, stitch_y + 4), (sx + 8, stitch_y), 2)

    # metal belt/band
    belt_y = by + int(bh * 0.65)
    pygame.draw.rect(surface, palette["metal"], (bx - 2, belt_y, bw + 4, 6), border_radius=3)
    # buckle
    pygame.draw.rect(surface, palette["accent"], (cx - 4, belt_y + 1, 8, 4), border_radius=1)

    # arms - mechanical-looking
    arm_w, arm_h = 8, int(height * 0.25)
    arm_y = by + 8
    _draw_arm(surface, bx - 5, arm_y + bob, arm_w, arm_h, palette["metal"], border_radius=3)
    _draw_arm(surface, bx + bw - 3, arm_y + bob, arm_w, arm_h, palette["metal"], border_radius=3)

    # head - round with goggles
    head_r = int(width * 0.18)
    hx, hy = cx, int(height * 0.20) + bob
    pygame.draw.circle(surface, palette["body_light"], (hx, hy), head_r)

    # goggles
    goggle_w = 10 if direction == "side" else 12
    goggle_y = hy - 2
    for gx in (hx - 7 + (2 if direction == "side" else 0), hx + 7 - (2 if direction == "side" else 0)):
        if direction == "side" and gx < hx:
            continue
        pygame.draw.ellipse(surface, palette["metal"], (gx - goggle_w // 2, goggle_y - 4, goggle_w, 8))
        pygame.draw.ellipse(surface, palette["body_dark"], (gx - goggle_w // 2 + 2, goggle_y - 2, goggle_w - 4, 4))

    # eyes behind goggles
    e_spacing = 5 if direction == "side" else 7
    so = 2 if direction == "side" else 0
    _draw_eyes(surface, hx, goggle_y, e_spacing, palette["eye_white"], palette["eye_pupil"], so)

    # fuse on top of head
    fuse_y = hy - head_r - 2
    fuse_pts = [(hx, fuse_y), (hx + 2, fuse_y - 8), (hx - 1, fuse_y - 14)]
    pygame.draw.lines(surface, palette["fuse"], False, fuse_pts, 2)
    # spark at tip
    spark_y = fuse_y - 14
    pygame.draw.circle(surface, palette["spark"], (hx - 1, spark_y), 3)
    pygame.draw.circle(surface, palette["accent"], (hx - 1, spark_y), 2)


def _draw_stalker(surface, width, height, cx, cy, palette, direction, bob):
    _draw_shadow(surface, cx, height, palette)

    # legs - dark, stealthy
    _draw_legs(surface, cx, int(height * 0.62), 12, 18, palette["body_dark"], bob)

    # body - cloaked
    bw, bh = int(width * 0.54), int(height * 0.42)
    bx, by = cx - bw // 2, int(height * 0.30) + bob
    # cloak shape (wider at bottom)
    cloak_pts = [
        (bx + 4, by),
        (bx + bw - 4, by),
        (bx + bw + 6, by + bh),
        (bx - 6, by + bh),
    ]
    pygame.draw.polygon(surface, palette["cloak"], cloak_pts)
    # inner body
    inner_pts = [
        (bx + 8, by + 4),
        (bx + bw - 8, by + 4),
        (bx + bw - 2, by + bh - 4),
        (bx + 2, by + bh - 4),
    ]
    pygame.draw.polygon(surface, palette["body"], inner_pts)

    # arms - hidden in cloak, only hands visible
    hand_y = by + int(bh * 0.65) + bob
    for hx in (bx + 2, bx + bw - 2):
        pygame.draw.circle(surface, palette["body_dark"], (hx, hand_y), 4)

    # blade (side only)
    if direction == "side":
        blade_pts = [
            (bx + bw + 8, by + int(bh * 0.20)),
            (bx + bw + 14, by + int(bh * 0.10)),
            (bx + bw + 16, by + int(bh * 0.40)),
        ]
        pygame.draw.polygon(surface, palette["blade"], blade_pts)
        # blade guard
        pygame.draw.line(surface, palette["blade"], (bx + bw + 7, by + int(bh * 0.18)),
                         (bx + bw + 7, by + int(bh * 0.42)), 2)

    # head - masked
    head_r = int(width * 0.16)
    hx, hy = cx, int(height * 0.20) + bob
    pygame.draw.circle(surface, palette["body_dark"], (hx, hy), head_r)

    # mask covering lower face
    mask_pts = [
        (hx - head_r + 2, hy),
        (hx + head_r - 2, hy),
        (hx + head_r - 4, hy + head_r + 2),
        (hx - head_r + 4, hy + head_r + 2),
    ]
    pygame.draw.polygon(surface, palette["mask"], mask_pts)

    # eyes - narrowed, glowing
    e_spacing = 5 if direction == "side" else 7
    so = 2 if direction == "side" else 0
    _draw_eyes(surface, hx, hy - 1, e_spacing, palette["eye_white"], palette["eye_pupil"], so)
    # shadow over eyes (narrowed look)
    for ex in (hx - e_spacing + so, hx + e_spacing + so):
        pygame.draw.line(surface, palette["body_dark"], (ex - 4, hy - 3), (ex + 4, hy - 3), 2)

    # hood rim
    pygame.draw.arc(surface, palette["cloak"], (hx - 14, hy - head_r - 4, 28, 12), 3.14, 0, 2)


def _draw_skirmisher(surface, width, height, cx, cy, palette, direction, bob):
    _draw_shadow(surface, cx, height, palette)

    # legs - springy
    _draw_legs(surface, cx, int(height * 0.62), 10, 18, palette["body_dark"], bob)

    # body - light, compact
    bw, bh = int(width * 0.48), int(height * 0.40)
    bx, by = cx - bw // 2, int(height * 0.32) + bob
    pygame.draw.rect(surface, palette["body"], (bx, by, bw, bh), border_radius=8)
    pygame.draw.rect(surface, palette["body_light"], (bx + 4, by + 4, bw - 8, bh - 8), border_radius=6)

    # feather pattern on chest
    for fy in range(by + 8, by + bh - 4, 6):
        fx = cx
        fw = bw // 3
        feather_pts = [(fx, fy), (fx - fw // 2, fy + 4), (fx, fy + 2), (fx + fw // 2, fy + 4)]
        pygame.draw.polygon(surface, palette["feather"], feather_pts)

    # arms - thin, quick
    arm_w, arm_h = 6, int(height * 0.26)
    arm_y = by + 6
    _draw_arm(surface, bx - 3, arm_y + bob, arm_w, arm_h, palette["body_dark"], border_radius=3)
    _draw_arm(surface, bx + bw - 3, arm_y + bob, arm_w, arm_h, palette["body_dark"], border_radius=3)

    # head - bird-like
    head_r = int(width * 0.16)
    hx, hy = cx, int(height * 0.22) + bob
    pygame.draw.circle(surface, palette["body_light"], (hx, hy), head_r)

    # crest feathers
    for i, c in enumerate([(hx - 8, hy - head_r - 2), (hx, hy - head_r - 6), (hx + 8, hy - head_r - 2)]):
        cpts = [(c[0], c[1]), (c[0] - 3 + i * 2, c[1] - 6), (c[0] + 2 - i, c[1] - 4)]
        pygame.draw.polygon(surface, palette["crest"], cpts)

    # beak
    if direction == "side":
        beak_pts = [(hx + head_r - 2, hy + 1), (hx + head_r + 8, hy + 4), (hx + head_r - 2, hy + 7)]
        pygame.draw.polygon(surface, palette["beak"], beak_pts)
    else:
        beak_pts = [(hx - 3, hy + 3), (hx, hy + 9), (hx + 3, hy + 3)]
        pygame.draw.polygon(surface, palette["beak"], beak_pts)

    # eyes
    e_spacing = 5 if direction == "side" else 7
    so = 2 if direction == "side" else 0
    _draw_eyes(surface, hx, hy - 1, e_spacing, palette["eye_white"], palette["eye_pupil"], so)

    # warpaint
    paint_y = hy + 5
    if direction == "side":
        pygame.draw.line(surface, palette["accent"], (hx - 2, paint_y), (hx + 6, paint_y), 2)
    else:
        pygame.draw.line(surface, palette["accent"], (hx - 6, paint_y), (hx + 6, paint_y), 2)


def _draw_guardian(surface, width, height, cx, cy, palette, direction, bob):
    _draw_shadow(surface, cx, height, palette)

    # legs - armored
    _draw_legs(surface, cx, int(height * 0.62), 14, 18, palette["armor"], bob)

    # body - heavily armored
    bw, bh = int(width * 0.64), int(height * 0.44)
    bx, by = cx - bw // 2, int(height * 0.30) + bob
    pygame.draw.rect(surface, palette["armor"], (bx, by, bw, bh), border_radius=6)
    # armor plates
    pygame.draw.rect(surface, palette["armor_light"], (bx + 4, by + 4, bw - 8, bh - 8), border_radius=5)
    # chest emblem
    emblem_r = 6
    pygame.draw.circle(surface, palette["crest"], (cx, by + int(bh * 0.50)), emblem_r)
    pygame.draw.circle(surface, palette["accent"], (cx, by + int(bh * 0.50)), emblem_r - 2)

    # shoulder pads
    for sdx in (bx - 6, bx + bw - 4):
        pygame.draw.ellipse(surface, palette["armor"], (sdx, by - 2, 14, 12))
        pygame.draw.ellipse(surface, palette["armor_light"], (sdx + 2, by, 10, 8))

    # arms - armored
    arm_w, arm_h = 8, int(height * 0.26)
    arm_y = by + 6
    _draw_arm(surface, bx - 5, arm_y + bob, arm_w, arm_h, palette["armor"], border_radius=3)
    _draw_arm(surface, bx + bw - 3, arm_y + bob, arm_w, arm_h, palette["armor"], border_radius=3)

    # shield (on left arm, side view)
    if direction == "side":
        shield_pts = [
            (bx - 10, by + 2),
            (bx - 4, by - 4),
            (bx - 4, by + int(bh * 0.7)),
            (bx - 10, by + int(bh * 0.65)),
        ]
        pygame.draw.polygon(surface, palette["shield"], shield_pts)
        pygame.draw.polygon(surface, palette["armor_light"],
                            [(p[0] + 2, p[1] + 2) for p in shield_pts], 1)

    # head - helmeted
    head_r = int(width * 0.17)
    hx, hy = cx, int(height * 0.20) + bob
    pygame.draw.circle(surface, palette["armor"], (hx, hy), head_r)

    # helmet visor
    visor_pts = [
        (hx - head_r + 2, hy - 2),
        (hx + head_r - 2, hy - 2),
        (hx + head_r - 6, hy + 6),
        (hx - head_r + 6, hy + 6),
    ]
    pygame.draw.polygon(surface, palette["armor_light"], visor_pts)

    # eyes through visor
    e_spacing = 5 if direction == "side" else 7
    so = 2 if direction == "side" else 0
    _draw_eyes(surface, hx, hy + 1, e_spacing, palette["eye_white"], palette["eye_pupil"], so)

    # helmet crest/plume
    plume_y = hy - head_r - 4
    plume_pts = [
        (hx - 6, plume_y),
        (hx, plume_y - 10),
        (hx + 6, plume_y),
    ]
    pygame.draw.polygon(surface, palette["crest"], plume_pts)
    pygame.draw.polygon(surface, palette["accent"], [(hx - 3, plume_y - 2), (hx, plume_y - 7), (hx + 3, plume_y - 2)])


# ---------------------------------------------------------------------------
# Frame dispatcher
# ---------------------------------------------------------------------------

def _make_frame(
    size: tuple[int, int],
    palette: dict,
    style: str,
    direction: str,
    bob_offset: int,
) -> pygame.Surface:
    width, height = size
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    cx = width // 2

    draw_functions = {
        "brute": _draw_brute,
        "venomous": _draw_venomous,
        "arcanist": _draw_arcanist,
        "trickster": _draw_trickster,
        "bomber": _draw_bomber,
        "stalker": _draw_stalker,
        "skirmisher": _draw_skirmisher,
        "guardian": _draw_guardian,
    }
    drawer = draw_functions.get(style, _draw_brute)
    cy = height // 2
    drawer(surface, width, height, cx, cy, palette, direction, bob_offset)

    return surface
