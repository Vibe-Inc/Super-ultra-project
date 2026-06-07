from __future__ import annotations

import math
from functools import lru_cache

import pygame

from src.entities.monster_visuals import _draw_shadow, _walk_offset


CHRONOS_PALETTE = {
    "robe": (25, 15, 55), "robe_light": (55, 35, 100), "robe_dark": (12, 8, 30),
    "robe_mid": (38, 22, 75), "robe_deep": (18, 10, 40), "robe_highlight": (70, 48, 120),
    "skin": (180, 170, 195), "skin_light": (210, 200, 225), "skin_dark": (100, 90, 120),
    "skin_warm": (195, 180, 210),
    "time_accent": (220, 180, 60), "time_accent_dark": (170, 130, 30),
    "time_accent_bright": (255, 220, 90),
    "time_glow": (255, 210, 80, 70),
    "void": (8, 5, 20), "void_bright": (30, 18, 60),
    "rune": (200, 170, 50), "rune_dark": (140, 115, 25), "rune_bright": (240, 210, 80),
    "eye_white": (240, 230, 200), "eye_pupil": (200, 160, 40),
    "accent": (220, 180, 60), "accent_dark": (160, 125, 25),
    "shadow": (0, 0, 0, 48),
    "chain": (180, 155, 45), "chain_dark": (120, 100, 20),
    "glass": (160, 180, 220, 60), "glass_bright": (200, 220, 255, 80),
    "gear": (140, 120, 80), "gear_dark": (90, 75, 45), "gear_light": (190, 165, 100),
}


def build_boss_animations(style: str, size: tuple[int, int]) -> dict[str, list[pygame.Surface]]:
    return _build_boss_animations_cached((style or "").lower(), tuple(size))


@lru_cache(maxsize=4)
def _build_boss_animations_cached(style: str, size: tuple[int, int]) -> dict[str, list[pygame.Surface]]:
    if style == "chronos":
        palette = CHRONOS_PALETTE
    else:
        palette = CHRONOS_PALETTE
    anims: dict[str, list[pygame.Surface]] = {"down": [], "up": [], "side": []}
    for frame_idx, offset in enumerate([0, 1, 0, -1]):
        for d in ("down", "up", "side"):
            anims[d].append(_make_boss_frame(size, palette, style, d, offset, frame_idx))
    return anims


def _make_boss_frame(size, palette, style, direction, bob_offset, frame_idx):
    w, h = size
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    if style == "chronos":
        _draw_chronos(s, w, h, w // 2, h // 2, palette, direction, bob_offset, frame_idx)
    else:
        _draw_chronos(s, w, h, w // 2, h // 2, palette, direction, bob_offset, frame_idx)
    return s


def _smooth_ellipse(surface, color, rect, width=0):
    """Draw a smooth anti-aliased-looking ellipse."""
    pygame.draw.ellipse(surface, color, rect, width)


def _gradient_circle(surface, cx, cy, radius, color_inner, color_outer, steps=6):
    """Draw a smooth gradient circle from inner to outer color."""
    for i in range(steps, 0, -1):
        ratio = i / steps
        r = int(radius * ratio)
        if r < 1:
            continue
        ri, gi, bi = color_inner[:3]
        ro, go, bo = color_outer[:3]
        ri2 = int(ri + (ro - ri) * (1 - ratio))
        gi2 = int(gi + (go - gi) * (1 - ratio))
        bi2 = int(bi + (bo - bi) * (1 - ratio))
        alpha = color_inner[3] if len(color_inner) > 3 else 255
        alpha2 = int(alpha * (0.3 + 0.7 * ratio))
        pygame.draw.circle(surface, (ri2, gi2, bi2, alpha2), (cx, cy), r)


def _bezier_point(p0, p1, p2, t):
    """Quadratic bezier interpolation."""
    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
    return (int(x), int(y))


def _draw_bezier_curve(surface, color, p0, p1, p2, width=1, steps=12):
    """Draw a quadratic bezier curve."""
    points = [_bezier_point(p0, p1, p2, i / steps) for i in range(steps + 1)]
    if len(points) >= 2:
        pygame.draw.lines(surface, color, False, points, width)


def _draw_chronos(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    pulse = [0, 3, 0, -3][frame]
    hover = [0, -5, 0, 5][frame]
    slow_pulse = 0.5 + 0.5 * math.sin(frame * 0.4)
    t = frame * 1.0

    # ─── TEMPORAL DISTORTION FIELD (outermost layer) ───
    td = pygame.Surface((w, h), pygame.SRCALPHA)
    td_cy = int(h * 0.42) + bob + hover
    for ring_i in range(5):
        ring_r = int(w * (0.30 + ring_i * 0.04)) + int(slow_pulse * 3 * (ring_i + 1))
        ring_a = max(5, 30 - ring_i * 6 + int(pulse * 3))
        ring_w = 1 if ring_i % 2 == 0 else 0
        pygame.draw.circle(td, (*p["time_glow"][:3], ring_a), (cx, td_cy), ring_r, ring_w)
    s.blit(td, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # ─── RUNE CIRCLE (ground) ───
    rune_r = int(w * 0.40)
    rune_y = int(h * 0.80) + bob
    rune_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(rune_surf, (*p["rune"][:3], 40 + int(pulse * 10)), (cx, rune_y), rune_r, 1)
    pygame.draw.circle(rune_surf, (*p["rune"][:3], 25 + int(pulse * 5)), (cx, rune_y), rune_r + 4, 1)
    pygame.draw.circle(rune_surf, (*p["time_accent"][:3], 50), (cx, rune_y), int(rune_r * 0.6), 1)
    # inner double ring
    pygame.draw.circle(rune_surf, (*p["rune_dark"][:3], 30), (cx, rune_y), int(rune_r * 0.45), 1)
    for ri in range(16):
        angle = t * 0.3 + ri * (math.pi * 2 / 16)
        rmx = cx + int(math.cos(angle) * rune_r)
        rmy = rune_y + int(math.sin(angle) * rune_r * 0.3)
        rs = 3
        pygame.draw.polygon(rune_surf, (*p["rune"][:3], 60 + int(pulse * 20)),
            [(rmx, rmy - rs), (rmx + rs, rmy), (rmx, rmy + rs), (rmx - rs, rmy)])
    # runic connecting arcs
    for ri in range(16):
        a1 = t * 0.3 + ri * (math.pi * 2 / 16)
        a2 = t * 0.3 + (ri + 1) * (math.pi * 2 / 16)
        x1 = cx + int(math.cos(a1) * rune_r)
        y1 = rune_y + int(math.sin(a1) * rune_r * 0.3)
        x2 = cx + int(math.cos(a2) * rune_r)
        y2 = rune_y + int(math.sin(a2) * rune_r * 0.3)
        mid_a = (a1 + a2) / 2
        ctrl_r = rune_r + 6
        ctrl_x = cx + int(math.cos(mid_a) * ctrl_r)
        ctrl_y = rune_y + int(math.sin(mid_a) * ctrl_r * 0.3)
        _draw_bezier_curve(rune_surf, (*p["rune"][:3], 20), (x1, y1), (ctrl_x, ctrl_y), (x2, y2), 1, 8)
    # runic text symbols (small marks between runes)
    for ri in range(8):
        angle = t * 0.3 + ri * (math.pi * 2 / 8) + math.pi / 16
        sym_r = int(rune_r * 0.75)
        sx = cx + int(math.cos(angle) * sym_r)
        sy = rune_y + int(math.sin(angle) * sym_r * 0.3)
        pygame.draw.line(rune_surf, (*p["time_accent"][:3], 35), (sx - 2, sy), (sx + 2, sy), 1)
        pygame.draw.line(rune_surf, (*p["time_accent"][:3], 35), (sx, sy - 2), (sx, sy + 2), 1)
    s.blit(rune_surf, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # ─── AURA LAYERS ───
    ag = pygame.Surface((w, h), pygame.SRCALPHA)
    aura_cy = int(h * 0.42) + bob + hover
    # outer wispy aura
    for ring_i in range(4):
        ring_r = int(w * (0.22 + ring_i * 0.05)) + int(slow_pulse * 4 * (ring_i + 1))
        ring_a = max(0, int(40 - ring_i * 10 + pulse * 4))
        pygame.draw.circle(ag, (*p["time_glow"][:3], ring_a), (cx, aura_cy), ring_r, 1)
    # inner fill glow
    pygame.draw.circle(ag, (*p["time_accent"][:3], 20), (cx, aura_cy), int(w * 0.15))
    # radial glow rays
    for ray_i in range(8):
        ray_a = t * 0.2 + ray_i * (math.pi / 4)
        ray_len = int(w * 0.18) + int(math.sin(t * 0.5 + ray_i) * 4)
        rx = cx + int(math.cos(ray_a) * ray_len)
        ry = aura_cy + int(math.sin(ray_a) * ray_len)
        pygame.draw.line(ag, (*p["time_glow"][:3], 18), (cx, aura_cy), (rx, ry), 1)
    s.blit(ag, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # ─── ORBITING CLOCK ORBS (3, with gear teeth) ───
    for ci in range(3):
        orb_angle = t * 0.6 + ci * (math.pi * 2 / 3)
        orb_r = int(w * (0.20 + ci * 0.03))
        ocx = cx + int(math.cos(orb_angle) * orb_r)
        ocy = int(h * 0.38) + bob + hover + int(math.sin(orb_angle * 0.7) * 10)
        clock_r = 7 + ci * 2
        oa = max(30, 100 - ci * 20)
        # outer ring with gear teeth
        pygame.draw.circle(s, (*p["rune"][:3], oa), (ocx, ocy), clock_r, 1)
        pygame.draw.circle(s, (*p["time_accent"][:3], oa // 2), (ocx, ocy), clock_r + 2, 1)
        # gear teeth
        for gi in range(8):
            ga = t * (0.8 + ci * 0.2) + gi * (math.pi / 4)
            gx1 = ocx + int(math.cos(ga) * (clock_r + 1))
            gy1 = ocy + int(math.sin(ga) * (clock_r + 1))
            gx2 = ocx + int(math.cos(ga) * (clock_r + 3))
            gy2 = ocy + int(math.sin(ga) * (clock_r + 3))
            pygame.draw.line(s, (*p["gear"][:3], oa), (gx1, gy1), (gx2, gy2), 1)
        # clock hands
        ha1 = t * (0.5 + ci * 0.3)
        ha2 = t * (1.5 + ci * 0.5)
        ha3 = t * 3.0
        pygame.draw.line(s, (*p["time_accent"][:3], oa), (ocx, ocy),
            (ocx + int(math.cos(ha1) * (clock_r - 2)), ocy + int(math.sin(ha1) * (clock_r - 2))), 1)
        pygame.draw.line(s, (*p["rune"][:3], oa), (ocx, ocy),
            (ocx + int(math.cos(ha2) * (clock_r - 3)), ocy + int(math.sin(ha2) * (clock_r - 3))), 1)
        pygame.draw.line(s, (*p["time_accent_bright"][:3], oa // 2), (ocx, ocy),
            (ocx + int(math.cos(ha3) * (clock_r - 1)), ocy + int(math.sin(ha3) * (clock_r - 1))), 1)
        pygame.draw.circle(s, (*p["time_accent"][:3], oa), (ocx, ocy), 1)
        # glass reflection
        glint_a = int(oa * 0.3)
        pygame.draw.circle(s, (*p["glass_bright"][:3], glint_a), (ocx - 2, ocy - 2), 2)

    # ─── FLOATING RUNE DIAMONDS (upper body) ───
    for ri in range(5):
        angle = t * 0.45 + ri * (math.pi * 2 / 5)
        rr = int(w * (0.24 + ri * 0.015))
        rx = cx + int(math.cos(angle) * rr)
        ry = int(h * 0.35) + bob + hover + int(math.sin(angle * 0.8) * 14)
        ra = max(40, 120 - ri * 18)
        rs = 4
        # double diamond shape
        pygame.draw.polygon(s, (*p["rune"][:3], ra),
            [(rx - rs, ry - rs), (rx + rs, ry - rs), (rx, ry)])
        pygame.draw.polygon(s, (*p["rune_bright"][:3], ra),
            [(rx - rs, ry + rs), (rx + rs, ry + rs), (rx, ry)])
        pygame.draw.polygon(s, (*p["rune"][:3], ra // 2), [(rx, ry - rs - 2), (rx + 2, ry), (rx, ry + rs + 2), (rx - 2, ry)])
        # glow
        rg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(rg, (*p["time_glow"][:3], ra // 3), (rx, ry), rs + 5)
        s.blit(rg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # ─── TRAILING TIME PARTICLES ───
    for pi in range(12):
        px = cx + (pi - 6) * int(w * 0.05) + int(math.sin(t * 0.4 + pi * 0.7) * 5)
        py = int(h * 0.48) + bob + hover + int((t * 2.5 + pi * 4) % 24)
        pa = max(10, 65 - pi * 5)
        pr = 1 + (1 if pi % 3 == 0 else 0)
        pygame.draw.circle(s, (*p["time_accent"][:3], pa), (px, py), pr)

    # ─── LEGS (flowing robe with layered fabric) ───
    lo, ro, la, ra = _walk_offset(frame)
    leg_y = int(h * 0.74) + bob
    for lx, off, side in [(cx - int(w * 0.10) + lo, lo, -1), (cx + int(w * 0.03) + ro, ro, 1)]:
        lh = 22 + abs(off)
        # outer robe drape
        pygame.draw.rect(s, p["robe_dark"], (lx - 3, leg_y - 1, 18, lh + 2), border_radius=5)
        # main leg fabric
        pygame.draw.rect(s, p["robe"], (lx, leg_y + 2, 14, lh - 3), border_radius=4)
        # fabric highlight
        pygame.draw.rect(s, p["robe_light"], (lx + 1, leg_y + 3, 5, lh - 6), border_radius=2)
        # fabric fold shadow
        pygame.draw.rect(s, p["robe_deep"], (lx + 8, leg_y + 4, 4, lh - 7), border_radius=2)
        # gold band with filigree
        pygame.draw.rect(s, p["time_accent_dark"], (lx - 1, leg_y + lh // 2, 16, 5), border_radius=2)
        pygame.draw.rect(s, p["time_accent"], (lx, leg_y + lh // 2 + 1, 14, 3))
        # tiny rune marks on band
        for ri2 in range(3):
            rmx = lx + 2 + ri2 * 5
            pygame.draw.line(s, p["rune_dark"], (rmx, leg_y + lh // 2 + 1), (rmx, leg_y + lh // 2 + 3), 1)
        # glow at hem
        sg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(sg, (*p["time_glow"][:3], 35 + int(pulse * 10)), (lx + 7, leg_y + lh // 2 + 1), 4)
        s.blit(sg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        # ankle chain
        pygame.draw.line(s, p["time_accent"], (lx, leg_y + 1), (lx + 14, leg_y + 1), 1)
        for ci2 in range(4):
            cx2 = lx + 1 + ci2 * 4
            pygame.draw.circle(s, p["chain"], (cx2, leg_y + 1), 1)

    # ─── ROBE / TORSO (flowing, layered fabric) ───
    bw = int(w * 0.52); bh = int(h * 0.48)
    bx = cx - bw // 2; by = int(h * 0.28) + bob + hover
    flutter = [0, 2, 0, -2][frame]
    # outer robe shape (wider, more flowing)
    robe_pts = [
        (bx + 4, by), (bx + bw - 4, by),
        (bx + bw + 10 + flutter, by + bh - 6),
        (bx + bw + 6 + flutter, by + bh),
        (bx - 6 - flutter, by + bh),
        (bx - 10 - flutter, by + bh - 6),
    ]
    pygame.draw.polygon(s, p["robe"], robe_pts)
    # inner robe panel
    inner_pts = [
        (bx + 10, by + 4), (bx + bw - 10, by + 4),
        (bx + bw + 3 + flutter, by + bh - 6), (bx - 3 - flutter, by + bh - 6),
    ]
    pygame.draw.polygon(s, p["robe_mid"], inner_pts)
    # highlight panel (center)
    hl_pts = [
        (bx + bw // 2 - 8, by + 6), (bx + bw // 2 + 8, by + 6),
        (bx + bw // 2 + 5 + flutter // 2, by + bh - 10), (bx + bw // 2 - 5 - flutter // 2, by + bh - 10),
    ]
    pygame.draw.polygon(s, p["robe_highlight"], hl_pts)
    # fabric folds (curved lines)
    for fold_i in range(4):
        fold_x = bx + 16 + fold_i * ((bw - 32) // 3)
        fold_a = 40 + int(pulse * 8)
        ctrl_x = fold_x + flutter // 2 + (2 if fold_i % 2 == 0 else -2)
        _draw_bezier_curve(s, (*p["robe_dark"][:3], fold_a),
            (fold_x, by + 8), (ctrl_x, by + bh // 2), (fold_x + flutter, by + bh - 10), 1, 10)
    # gold hem with double line
    hem_y = by + bh - 3
    pygame.draw.line(s, p["time_accent"], (bx - 8 - flutter, hem_y), (bx + bw + 8 + flutter, hem_y), 2)
    pygame.draw.line(s, p["time_accent_dark"], (bx - 8 - flutter, hem_y + 2), (bx + bw + 8 + flutter, hem_y + 2), 1)
    pygame.draw.line(s, p["time_accent_bright"], (bx - 6 - flutter, hem_y - 1), (bx + bw + 6 + flutter, hem_y - 1), 1)
    # gold neck trim
    pygame.draw.line(s, p["time_accent"], (bx + 4, by + 2), (bx + bw - 4, by + 2), 1)
    pygame.draw.line(s, p["time_accent_bright"], (bx + 6, by + 1), (bx + bw - 6, by + 1), 1)
    # rune diamonds on chest (7 in a constellation pattern)
    rune_positions = [
        (bx + bw // 2, by + 14),
        (bx + bw // 2 - 8, by + 22), (bx + bw // 2 + 8, by + 22),
        (bx + bw // 2 - 14, by + 32), (bx + bw // 2, by + 30), (bx + bw // 2 + 14, by + 32),
        (bx + bw // 2, by + 42),
    ]
    for si, (rx, ry) in enumerate(rune_positions):
        sa = 80 + int(pulse * 15)
        hg_rs = 3
        pygame.draw.polygon(s, (*p["rune"][:3], sa),
            [(rx - hg_rs, ry - hg_rs), (rx + hg_rs, ry - hg_rs), (rx, ry)])
        pygame.draw.polygon(s, (*p["rune_bright"][:3], sa),
            [(rx - hg_rs, ry + hg_rs), (rx + hg_rs, ry + hg_rs), (rx, ry)])
        sg2 = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(sg2, (*p["time_glow"][:3], sa // 3), (rx, ry), hg_rs + 4)
        s.blit(sg2, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    # constellation lines connecting runes
    for ci2 in range(len(rune_positions) - 1):
        r1 = rune_positions[ci2]
        r2 = rune_positions[ci2 + 1]
        if ci2 < 3:
            pygame.draw.line(s, (*p["rune"][:3], 25), r1, r2, 1)
    # chain dots along edges
    for edge_x in [bx + 4, bx + bw - 4]:
        for chain_y in range(by + 8, by + bh - 8, 5):
            ca = 60 + int(pulse * 10)
            pygame.draw.circle(s, (*p["time_accent"][:3], ca), (edge_x, chain_y), 1)
            # alternating chain link shape
            if chain_y % 10 < 5:
                pygame.draw.line(s, (*p["chain"][:3], ca // 2), (edge_x - 1, chain_y), (edge_x + 1, chain_y), 1)

    # ─── CLOCK MECHANISM (chest) ───
    clock_cx, clock_cy = cx, by + int(bh * 0.45)
    clock_r = int(w * 0.09)
    cg = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(cg, (*p["time_glow"][:3], 50 + int(pulse * 15)), (clock_cx, clock_cy), clock_r + 10)
    s.blit(cg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    # outer ring
    pygame.draw.circle(s, p["time_accent_dark"], (clock_cx, clock_cy), clock_r + 3)
    pygame.draw.circle(s, p["time_accent"], (clock_cx, clock_cy), clock_r + 2)
    pygame.draw.circle(s, p["time_accent_bright"], (clock_cx, clock_cy), clock_r + 1)
    pygame.draw.circle(s, p["rune"], (clock_cx, clock_cy), clock_r)
    pygame.draw.circle(s, p["rune_dark"], (clock_cx, clock_cy), clock_r - 1)
    # inner ring
    pygame.draw.circle(s, (*p["rune_dark"][:3], 60), (clock_cx, clock_cy), int(clock_r * 0.7), 1)
    # hour marks (12, with minute marks between)
    for mi in range(12):
        ma = mi * (math.pi * 2 / 12)
        mx1 = clock_cx + int(math.cos(ma) * (clock_r - 3))
        my1 = clock_cy + int(math.sin(ma) * (clock_r - 3))
        mx2 = clock_cx + int(math.cos(ma) * (clock_r - 5))
        my2 = clock_cy + int(math.sin(ma) * (clock_r - 5))
        pygame.draw.line(s, p["time_accent"], (mx1, my1), (mx2, my2), 1)
    # minute marks
    for mi in range(60):
        if mi % 5 == 0:
            continue
        ma = mi * (math.pi * 2 / 60)
        mx1 = clock_cx + int(math.cos(ma) * (clock_r - 3))
        my1 = clock_cy + int(math.sin(ma) * (clock_r - 3))
        mx2 = clock_cx + int(math.cos(ma) * (clock_r - 4))
        my2 = clock_cy + int(math.sin(ma) * (clock_r - 4))
        pygame.draw.line(s, (*p["rune_dark"][:3], 50), (mx1, my1), (mx2, my2), 1)
    # roman numeral dots at XII, III, VI, IX
    for ni, na in enumerate([0, math.pi / 2, math.pi, math.pi * 1.5]):
        nx = clock_cx + int(math.cos(na) * (clock_r - 7))
        ny = clock_cy + int(math.sin(na) * (clock_r - 7))
        pygame.draw.circle(s, p["time_accent_bright"], (nx, ny), 1)
    # hour hand (thick, ornate)
    h_angle = t * 0.25
    h_len = clock_r - 5
    h_end_x = clock_cx + int(math.cos(h_angle) * h_len)
    h_end_y = clock_cy + int(math.sin(h_angle) * h_len)
    pygame.draw.line(s, p["time_accent"], (clock_cx, clock_cy), (h_end_x, h_end_y), 2)
    pygame.draw.circle(s, p["time_accent"], (h_end_x, h_end_y), 2)
    # minute hand (thinner)
    m_angle = t * 1.2
    m_len = clock_r - 3
    m_end_x = clock_cx + int(math.cos(m_angle) * m_len)
    m_end_y = clock_cy + int(math.sin(m_angle) * m_len)
    pygame.draw.line(s, p["rune"], (clock_cx, clock_cy), (m_end_x, m_end_y), 1)
    # second hand (thin, fast)
    s_angle = t * 3.0
    s_end_x = clock_cx + int(math.cos(s_angle) * (clock_r - 2))
    s_end_y = clock_cy + int(math.sin(s_angle) * (clock_r - 2))
    pygame.draw.line(s, (*p["time_accent_bright"][:3], 150), (clock_cx, clock_cy), (s_end_x, s_end_y), 1)
    # center cap
    pygame.draw.circle(s, p["time_accent"], (clock_cx, clock_cy), 2)
    pygame.draw.circle(s, p["time_accent_bright"], (clock_cx, clock_cy), 1)

    # ─── SHOULDER PAULDRONS (layered, ornate) ───
    for side in (-1, 1):
        spx = cx + side * (bw // 2 + 8)
        spy = by - 4
        # layered pauldron plates
        for layer_i in range(3):
            layer_off = layer_i * 3
            layer_a = max(40, 140 - layer_i * 30)
            # curved pauldron shape
            p_pts = [
                (spx - 10 + layer_off * side, spy + 8),
                (spx - 4 + layer_off * side, spy - 8 - layer_off),
                (spx + 2, spy - 10 - layer_off),
                (spx + 6 - layer_off * side, spy - 8 - layer_off),
                (spx + 12 - layer_off * side, spy + 8),
            ]
            pygame.draw.polygon(s, (*p["robe_dark"][:3], layer_a), p_pts)
        # gold trim
        trim_pts = [
            (spx - 10, spy + 8), (spx - 4, spy - 8), (spx + 2, spy - 10),
            (spx + 6, spy - 8), (spx + 12, spy + 8),
        ]
        pygame.draw.lines(s, p["time_accent"], True, trim_pts, 1)
        # rune on pauldron
        pygame.draw.polygon(s, p["rune"],
            [(spx - 2, spy - 4), (spx + 2, spy - 4), (spx, spy - 7)])
        pygame.draw.polygon(s, p["rune"],
            [(spx - 2, spy + 2), (spx + 2, spy + 2), (spx, spy - 1)])
        # glow
        pg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(pg, (*p["time_glow"][:3], 45), (spx, spy), 6)
        s.blit(pg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(s, p["time_accent"], (spx, spy + 1), 2)
        # dangling chain links
        for cli in range(3):
            clx = spx + side * (2 + cli * 3)
            cly = spy + 10 + cli * 3
            pygame.draw.line(s, p["chain"], (clx, cly), (clx + 2, cly + 2), 1)
            pygame.draw.line(s, p["chain"], (clx + 2, cly + 2), (clx, cly + 4), 1)

    # ─── ARMS (flowing sleeves with energy hands) ───
    for ax, fl in [(bx - 5, -1), (bx + bw - 1, 1)]:
        arm_sway = [0, 3, 0, -3][frame]
        # upper sleeve
        sleeve_pts = [
            (ax + arm_sway, by + 10 + bob),
            (ax + fl * 14 + arm_sway, by + 22 + bob),
            (ax + fl * 18 + arm_sway, by + 38 + bob),
            (ax + fl * 8 + arm_sway, by + 32 + bob),
        ]
        pygame.draw.polygon(s, p["robe_dark"], sleeve_pts)
        # sleeve highlight
        hl_sleeve = [
            (ax + fl * 2 + arm_sway, by + 12 + bob),
            (ax + fl * 12 + arm_sway, by + 22 + bob),
            (ax + fl * 15 + arm_sway, by + 35 + bob),
            (ax + fl * 6 + arm_sway, by + 30 + bob),
        ]
        pygame.draw.polygon(s, p["robe_mid"], hl_sleeve)
        # gold trim along sleeve
        pygame.draw.line(s, (*p["time_accent"][:3], 100),
            (ax + arm_sway, by + 10 + bob), (ax + fl * 18 + arm_sway, by + 38 + bob), 1)
        # cuff band
        cuff_x = ax + fl * 16 + arm_sway
        cuff_y = by + 34 + bob
        pygame.draw.rect(s, p["time_accent_dark"], (cuff_x - 3, cuff_y, 8, 4), border_radius=1)
        pygame.draw.rect(s, p["time_accent"], (cuff_x - 2, cuff_y + 1, 6, 2))
        # energy hand (glowing orb with fingers)
        hand_x = ax + fl * 18 + arm_sway
        hand_y = by + 38 + bob
        eg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(eg, (*p["time_glow"][:3], 90), (hand_x, hand_y), 12)
        pygame.draw.circle(eg, (*p["time_accent"][:3], 55), (hand_x, hand_y), 16)
        s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(s, p["time_accent"], (hand_x, hand_y), 6)
        pygame.draw.circle(s, p["rune"], (hand_x, hand_y), 4)
        pygame.draw.circle(s, p["time_accent_bright"], (hand_x, hand_y), 2)
        # finger-like energy wisps
        for fi in range(5):
            fa = t * 2.0 + fi * (math.pi * 2 / 5)
            f_dist = 8 + int(math.sin(t * 2.5 + fi) * 3)
            fx = hand_x + int(math.cos(fa) * f_dist)
            fy = hand_y + int(math.sin(fa) * f_dist)
            fa2 = max(40, 160 - fi * 25)
            # wisp with tail
            pygame.draw.circle(s, (*p["time_accent"][:3], fa2), (fx, fy), 2)
            tail_x = fx + int(math.cos(fa + 0.5) * 4)
            tail_y = fy + int(math.sin(fa + 0.5) * 4)
            pygame.draw.line(s, (*p["time_accent"][:3], fa2 // 2), (fx, fy), (tail_x, tail_y), 1)
        # orbiting sparks
        for si in range(5):
            s_angle = t * 2.0 + si * (math.pi * 2 / 5)
            s_dist = 10 + int(math.sin(t * 2.5 + si) * 3)
            sx = hand_x + int(math.cos(s_angle) * s_dist)
            sy = hand_y + int(math.sin(s_angle) * s_dist)
            sa2 = max(50, 180 - si * 25)
            pygame.draw.circle(s, (*p["time_accent_bright"][:3], sa2), (sx, sy), 1)

    # ─── CROWN (majestic, multi-layered) ───
    crown_y = int(h * 0.06) + bob + hover
    # floating clock fragments around crown
    for si in range(8):
        shard_angle = t * 0.4 + si * (math.pi * 2 / 8)
        shard_r = int(w * (0.14 + si * 0.008))
        shard_x = cx + int(math.cos(shard_angle) * shard_r)
        shard_y = crown_y + int(math.sin(shard_angle * 0.6) * 8)
        sa = max(50, 140 - si * 12)
        # each shard is a tiny clock face fragment
        pygame.draw.circle(s, (*p["rune"][:3], sa), (shard_x, shard_y), 3, 1)
        pygame.draw.line(s, (*p["time_accent"][:3], sa), (shard_x, shard_y),
            (shard_x + int(math.cos(shard_angle * 3) * 2), shard_y - 2), 1)
        sg3 = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(sg3, (*p["time_glow"][:3], sa // 3), (shard_x, shard_y), 6)
        s.blit(sg3, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    # crown polygon (7 points, more elaborate)
    crown_pts = [
        (cx - int(w * 0.12), crown_y + 8),
        (cx - int(w * 0.08), crown_y - 2),
        (cx - int(w * 0.04), crown_y + 4),
        (cx - int(w * 0.01), crown_y - 8),
        (cx, crown_y - 10),
        (cx + int(w * 0.01), crown_y - 8),
        (cx + int(w * 0.04), crown_y + 4),
        (cx + int(w * 0.08), crown_y - 2),
        (cx + int(w * 0.12), crown_y + 8),
    ]
    pygame.draw.polygon(s, p["time_accent"], crown_pts)
    pygame.draw.polygon(s, p["time_accent_bright"], crown_pts, 1)
    # crown base band
    pygame.draw.rect(s, p["time_accent_dark"], (cx - int(w * 0.11), crown_y + 6, int(w * 0.22), 4), border_radius=2)
    # central gem (larger, glowing)
    gem_g = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(gem_g, (*p["time_glow"][:3], 100), (cx, crown_y + 2), 8)
    s.blit(gem_g, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    pygame.draw.circle(s, p["time_accent_bright"], (cx, crown_y + 2), 4)
    pygame.draw.circle(s, (255, 250, 220), (cx, crown_y + 2), 2)
    # side gems
    for gx in [cx - int(w * 0.06), cx + int(w * 0.06)]:
        pygame.draw.circle(s, p["rune"], (gx, crown_y + 5), 2)
        pygame.draw.circle(s, p["rune_bright"], (gx, crown_y + 5), 1)

    # ─── HEAD (detailed face with features) ───
    hr = int(w * 0.16); hx, hy = cx, int(h * 0.16) + bob + hover
    # shadow behind head
    pygame.draw.circle(s, p["skin_dark"], (hx, hy + 4), hr + 2)
    # main head shape (slightly oval)
    pygame.draw.ellipse(s, p["skin"], (hx - hr, hy - hr + 2, hr * 2, hr * 2 - 2))
    pygame.draw.ellipse(s, p["skin_light"], (hx - hr + 4, hy - hr + 5, hr * 2 - 8, hr * 2 - 10))
    # cheekbone shadows
    for cheek in (-1, 1):
        cheek_x = hx + cheek * (hr // 2 + 1)
        pygame.draw.line(s, (*p["skin_dark"][:3], 30), (cheek_x, hy - 3), (cheek_x + cheek * 5, hy + 7), 1)
        # subtle cheek highlight
        pygame.draw.circle(s, (*p["skin_light"][:3], 20), (cheek_x - cheek * 2, hy + 2), 3)
    # forehead wrinkles (subtle age lines)
    for wy_off in [3, 5, 7]:
        wla = 25 + int(pulse * 6)
        pygame.draw.line(s, (*p["skin_dark"][:3], wla), (hx - hr // 2, hy - wy_off), (hx + hr // 2, hy - wy_off), 1)
    # brow ridge (more defined)
    for brow in (-1, 1):
        brow_x = hx + brow * (hr // 3)
        pygame.draw.arc(s, p["skin_dark"], (brow_x - 5, hy - 8, 10, 7), 3.14, 0, 2)
    # nose (subtle)
    pygame.draw.line(s, (*p["skin_dark"][:3], 35), (hx, hy - 2), (hx, hy + 4), 1)
    pygame.draw.line(s, (*p["skin_dark"][:3], 25), (hx - 2, hy + 4), (hx + 2, hy + 4), 1)
    # mouth (thin line)
    pygame.draw.line(s, (*p["skin_dark"][:3], 40), (hx - 4, hy + 8), (hx + 4, hy + 8), 1)
    # chin
    pygame.draw.circle(s, (*p["skin_dark"][:3], 15), (hx, hy + hr - 2), 3)

    # ─── HOOD (flowing, layered fabric) ───
    # outer hood shape
    pygame.draw.polygon(s, p["robe"],
        [(hx - hr - 10, hy + 12), (hx - hr + 2, hy - 12), (hx - 2, hy - 26),
         (hx + 2, hy - 26), (hx + hr - 2, hy - 12), (hx + hr + 10, hy + 12)])
    # inner hood
    pygame.draw.polygon(s, p["robe_dark"],
        [(hx - hr - 5, hy + 10), (hx - hr + 4, hy - 8), (hx, hy - 22),
         (hx + hr - 4, hy - 8), (hx + hr + 5, hy + 10)])
    # hood fold details
    _draw_bezier_curve(s, (*p["time_accent"][:3], 80),
        (hx - hr + 3, hy - 10), (hx - hr // 2, hy - 20), (hx, hy - 24), 1, 10)
    _draw_bezier_curve(s, (*p["time_accent"][:3], 80),
        (hx + hr - 3, hy - 10), (hx + hr // 2, hy - 20), (hx, hy - 24), 1, 10)
    # inner trim line
    pygame.draw.line(s, (*p["time_accent"][:3], 90), (hx - hr + 5, hy - 6), (hx, hy - 18), 1)
    pygame.draw.line(s, (*p["time_accent"][:3], 90), (hx, hy - 18), (hx + hr - 5, hy - 6), 1)
    # hood gem at apex
    hg = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(hg, (*p["time_glow"][:3], 80), (hx, hy - 14), 5)
    s.blit(hg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    pygame.draw.circle(s, p["time_accent"], (hx, hy - 14), 2)
    # hood side ornaments
    for hood_x in [hx - hr + 8, hx + hr - 8]:
        pygame.draw.circle(s, (*p["rune"][:3], 80), (hood_x, hy - 3), 2)
        pygame.draw.circle(s, (*p["rune_bright"][:3], 50), (hood_x, hy - 3), 1)

    # ─── EYES (glowing, with temporal flares) ───
    esp = 8 if dir != "side" else 6; so = 2 if dir == "side" else 0
    for ex in (hx - esp + so, hx + esp + so):
        # outer glow layers
        eg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(eg, (*p["time_glow"][:3], 80), (ex, hy + 1), 12)
        pygame.draw.circle(eg, (*p["time_accent"][:3], 40), (ex, hy + 1), 16)
        pygame.draw.circle(eg, (*p["void"][:3], 20), (ex, hy + 1), 20)
        s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        # eye white (slightly oval)
        pygame.draw.ellipse(s, p["eye_white"], (ex - 5, hy - 2, 10, 7))
        # iris
        pygame.draw.circle(s, p["eye_pupil"], (ex, hy + 1), 4)
        # pupil
        pygame.draw.circle(s, (30, 20, 10), (ex, hy + 1), 2)
        # temporal flare (extends outward)
        flare_dir = 1 if ex > hx else -1
        flare_len = 8 + pulse
        pygame.draw.line(s, (*p["time_accent"][:3], 150), (ex, hy + 1),
                        (ex + flare_dir * flare_len, hy - 3), 2)
        pygame.draw.line(s, (*p["time_accent"][:3], 80), (ex, hy + 1),
                        (ex + flare_dir * (flare_len + 5), hy - 5), 1)
        pygame.draw.line(s, (*p["time_accent"][:3], 50), (ex, hy + 1),
                        (ex + flare_dir * (flare_len + 8), hy - 2), 1)
        # highlight
        pygame.draw.circle(s, (255, 255, 255, 200), (ex - 1, hy - 1), 1)

    # ─── WISPY ENERGY TRAIL (around head) ───
    for wi in range(5):
        wa = t * 0.5 + wi * (math.pi * 2 / 5)
        wr = int(w * 0.20) + int(math.sin(wa * 2) * 5)
        wx = cx + int(math.cos(wa) * wr)
        wy = int(h * 0.16) + bob + hover + int(math.sin(wa * 1.3) * 12)
        w_alpha = max(15, 55 - wi * 10)
        w_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(w_surf, (*p["time_glow"][:3], w_alpha), (wx, wy), 4)
        # wisp tail
        tail_a = wa + 0.3
        tail_x = wx + int(math.cos(tail_a) * 6)
        tail_y = wy + int(math.sin(tail_a) * 6)
        pygame.draw.line(w_surf, (*p["time_glow"][:3], w_alpha // 2), (wx, wy), (tail_x, tail_y), 1)
        s.blit(w_surf, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
