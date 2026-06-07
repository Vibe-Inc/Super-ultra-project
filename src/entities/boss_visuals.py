from __future__ import annotations

import math
from functools import lru_cache

import pygame

from src.entities.monster_visuals import _draw_shadow, _walk_offset


CHRONOS_PALETTE = {
    "robe": (25, 15, 55), "robe_light": (55, 35, 100), "robe_dark": (12, 8, 30),
    "robe_mid": (38, 22, 75),
    "skin": (180, 170, 195), "skin_light": (210, 200, 225), "skin_dark": (100, 90, 120),
    "time_accent": (220, 180, 60), "time_accent_dark": (170, 130, 30),
    "time_glow": (255, 210, 80, 70),
    "void": (8, 5, 20), "void_bright": (30, 18, 60),
    "rune": (200, 170, 50), "rune_dark": (140, 115, 25),
    "eye_white": (240, 230, 200), "eye_pupil": (200, 160, 40),
    "accent": (220, 180, 60), "accent_dark": (160, 125, 25),
    "shadow": (0, 0, 0, 48),
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


def _draw_chronos(s, w, h, cx, cy, p, dir, bob, frame):
    _draw_shadow(s, cx, h, p, bob)
    pulse = [0, 3, 0, -3][frame]
    hover = [0, -5, 0, 5][frame]
    slow_pulse = 0.5 + 0.5 * math.sin(frame * 0.4)

    rune_r = int(w * 0.40)
    rune_y = int(h * 0.80) + bob
    rune_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(rune_surf, (*p["rune"][:3], 40 + int(pulse * 10)), (cx, rune_y), rune_r, 1)
    pygame.draw.circle(rune_surf, (*p["rune"][:3], 25 + int(pulse * 5)), (cx, rune_y), rune_r + 4, 1)
    pygame.draw.circle(rune_surf, (*p["time_accent"][:3], 50), (cx, rune_y), int(rune_r * 0.6), 1)
    for ri in range(12):
        angle = frame * 0.3 + ri * (math.pi * 2 / 12)
        rmx = cx + int(math.cos(angle) * rune_r)
        rmy = rune_y + int(math.sin(angle) * rune_r * 0.3)
        rs = 3
        pygame.draw.polygon(rune_surf, (*p["rune"][:3], 60 + int(pulse * 20)),
            [(rmx, rmy - rs), (rmx + rs, rmy), (rmx, rmy + rs), (rmx - rs, rmy)])
    for ri in range(12):
        a1 = frame * 0.3 + ri * (math.pi * 2 / 12)
        a2 = frame * 0.3 + (ri + 1) * (math.pi * 2 / 12)
        x1 = cx + int(math.cos(a1) * rune_r)
        y1 = rune_y + int(math.sin(a1) * rune_r * 0.3)
        x2 = cx + int(math.cos(a2) * rune_r)
        y2 = rune_y + int(math.sin(a2) * rune_r * 0.3)
        pygame.draw.line(rune_surf, (*p["rune"][:3], 30), (x1, y1), (x2, y2), 1)
    s.blit(rune_surf, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    ag = pygame.Surface((w, h), pygame.SRCALPHA)
    aura_cy = int(h * 0.42) + bob + hover
    for ring_i in range(3):
        ring_r = int(w * (0.22 + ring_i * 0.06)) + int(slow_pulse * 4 * (ring_i + 1))
        ring_a = int(50 - ring_i * 15 + pulse * 5)
        pygame.draw.circle(ag, (*p["time_glow"][:3], ring_a), (cx, aura_cy), ring_r, 1 if ring_i > 0 else 0)
    pygame.draw.circle(ag, (*p["time_accent"][:3], 30), (cx, aura_cy), int(w * 0.15))
    s.blit(ag, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    for ci in range(3):
        orb_angle = frame * 0.6 + ci * (math.pi * 2 / 3)
        orb_r = int(w * (0.20 + ci * 0.03))
        ocx = cx + int(math.cos(orb_angle) * orb_r)
        ocy = int(h * 0.38) + bob + hover + int(math.sin(orb_angle * 0.7) * 10)
        clock_r = 6 + ci * 2
        oa = max(30, 100 - ci * 20)
        pygame.draw.circle(s, (*p["rune"][:3], oa), (ocx, ocy), clock_r, 1)
        pygame.draw.circle(s, (*p["time_accent"][:3], oa // 2), (ocx, ocy), clock_r + 2, 1)
        ha1 = frame * (0.5 + ci * 0.3)
        ha2 = frame * (1.5 + ci * 0.5)
        pygame.draw.line(s, (*p["time_accent"][:3], oa), (ocx, ocy),
            (ocx + int(math.cos(ha1) * (clock_r - 2)), ocy + int(math.sin(ha1) * (clock_r - 2))), 1)
        pygame.draw.line(s, (*p["rune"][:3], oa), (ocx, ocy),
            (ocx + int(math.cos(ha2) * (clock_r - 3)), ocy + int(math.sin(ha2) * (clock_r - 3))), 1)
        pygame.draw.circle(s, (*p["time_accent"][:3], oa), (ocx, ocy), 1)

    for ri in range(4):
        angle = frame * 0.45 + ri * (math.pi * 2 / 4)
        rr = int(w * (0.24 + ri * 0.02))
        rx = cx + int(math.cos(angle) * rr)
        ry = int(h * 0.35) + bob + hover + int(math.sin(angle * 0.8) * 14)
        ra = max(40, 120 - ri * 20)
        rs = 4
        pygame.draw.polygon(s, (*p["rune"][:3], ra),
            [(rx - rs, ry - rs), (rx + rs, ry - rs), (rx, ry)])
        pygame.draw.polygon(s, (*p["rune"][:3], ra),
            [(rx - rs, ry + rs), (rx + rs, ry + rs), (rx, ry)])
        rg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(rg, (*p["time_glow"][:3], ra // 3), (rx, ry), rs + 4)
        s.blit(rg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    for pi in range(8):
        px = cx + (pi - 4) * int(w * 0.06) + int(math.sin(frame * 0.4 + pi * 0.8) * 4)
        py = int(h * 0.48) + bob + hover + int((frame * 2.5 + pi * 5) % 20)
        pa = max(15, 70 - pi * 8)
        pygame.draw.circle(s, (*p["time_accent"][:3], pa), (px, py), 1)

    lo, ro, la, ra = _walk_offset(frame)
    leg_y = int(h * 0.74) + bob
    for lx, off, side in [(cx - int(w * 0.10) + lo, lo, -1), (cx + int(w * 0.03) + ro, ro, 1)]:
        lh = 22 + abs(off)
        pygame.draw.rect(s, p["robe_dark"], (lx - 2, leg_y, 16, lh), border_radius=4)
        pygame.draw.rect(s, p["robe"], (lx, leg_y + 2, 12, lh - 4), border_radius=3)
        pygame.draw.rect(s, p["robe_light"], (lx + 1, leg_y + 2, 10, 3), border_radius=1)
        pygame.draw.rect(s, p["time_accent_dark"], (lx - 1, leg_y + lh // 2, 14, 4), border_radius=1)
        pygame.draw.rect(s, p["time_accent"], (lx, leg_y + lh // 2 + 1, 12, 2))
        sg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(sg, (*p["time_glow"][:3], 35 + int(pulse * 10)), (lx + 6, leg_y + lh // 2 + 1), 3)
        s.blit(sg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.line(s, p["time_accent"], (lx, leg_y + 1), (lx + 12, leg_y + 1), 1)

    bw = int(w * 0.52); bh = int(h * 0.48)
    bx = cx - bw // 2; by = int(h * 0.28) + bob + hover
    flutter = [0, 2, 0, -2][frame]
    robe_pts = [
        (bx + 6, by), (bx + bw - 6, by),
        (bx + bw + 8 + flutter, by + bh - 4),
        (bx + bw + 4 + flutter, by + bh),
        (bx - 4 - flutter, by + bh),
        (bx - 8 - flutter, by + bh - 4),
    ]
    pygame.draw.polygon(s, p["robe"], robe_pts)
    inner_pts = [
        (bx + 10, by + 4), (bx + bw - 10, by + 4),
        (bx + bw + 2 + flutter, by + bh - 6), (bx - 2 - flutter, by + bh - 6),
    ]
    pygame.draw.polygon(s, p["robe_mid"], inner_pts)
    for fold_x in range(bx + 14, bx + bw - 8, 10):
        fold_alpha = 40 + int(pulse * 10)
        pygame.draw.line(s, (*p["robe_dark"][:3], fold_alpha), (fold_x, by + 6), (fold_x + flutter // 2, by + bh - 8), 1)
    hem_y = by + bh - 3
    pygame.draw.line(s, p["time_accent"], (bx - 6 - flutter, hem_y), (bx + bw + 6 + flutter, hem_y), 2)
    pygame.draw.line(s, p["time_accent_dark"], (bx - 6 - flutter, hem_y + 2), (bx + bw + 6 + flutter, hem_y + 2), 1)
    pygame.draw.line(s, p["time_accent"], (bx + 4, by + 2), (bx + bw - 4, by + 2), 1)
    for si in range(5):
        sx = bx + 10 + si * ((bw - 20) // 4)
        sy = by + 14 + (si % 2) * 16
        sa = 80 + int(pulse * 15)
        hg_rs = 3
        pygame.draw.polygon(s, (*p["rune"][:3], sa),
            [(sx - hg_rs, sy - hg_rs), (sx + hg_rs, sy - hg_rs), (sx, sy)])
        pygame.draw.polygon(s, (*p["rune"][:3], sa),
            [(sx - hg_rs, sy + hg_rs), (sx + hg_rs, sy + hg_rs), (sx, sy)])
        sg2 = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(sg2, (*p["time_glow"][:3], sa // 3), (sx, sy), hg_rs + 3)
        s.blit(sg2, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    for edge_x in [bx + 4, bx + bw - 4]:
        for chain_y in range(by + 8, by + bh - 8, 6):
            ca = 60 + int(pulse * 10)
            pygame.draw.circle(s, (*p["time_accent"][:3], ca), (edge_x, chain_y), 1)

    clock_cx, clock_cy = cx, by + int(bh * 0.45)
    clock_r = int(w * 0.08)
    cg = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(cg, (*p["time_glow"][:3], 50 + int(pulse * 15)), (clock_cx, clock_cy), clock_r + 8)
    s.blit(cg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    pygame.draw.circle(s, p["time_accent_dark"], (clock_cx, clock_cy), clock_r + 2)
    pygame.draw.circle(s, p["time_accent"], (clock_cx, clock_cy), clock_r + 1)
    pygame.draw.circle(s, p["rune"], (clock_cx, clock_cy), clock_r)
    pygame.draw.circle(s, p["rune_dark"], (clock_cx, clock_cy), clock_r - 1)
    for mi in range(12):
        ma = mi * (math.pi * 2 / 12)
        mx1 = clock_cx + int(math.cos(ma) * (clock_r - 3))
        my1 = clock_cy + int(math.sin(ma) * (clock_r - 3))
        mx2 = clock_cx + int(math.cos(ma) * (clock_r - 5))
        my2 = clock_cy + int(math.sin(ma) * (clock_r - 5))
        pygame.draw.line(s, p["time_accent"], (mx1, my1), (mx2, my2), 1)
    h_angle = frame * 0.25
    pygame.draw.line(s, p["time_accent"], (clock_cx, clock_cy),
        (clock_cx + int(math.cos(h_angle) * (clock_r - 5)), clock_cy + int(math.sin(h_angle) * (clock_r - 5))), 2)
    m_angle = frame * 1.2
    pygame.draw.line(s, p["rune"], (clock_cx, clock_cy),
        (clock_cx + int(math.cos(m_angle) * (clock_r - 3)), clock_cy + int(math.sin(m_angle) * (clock_r - 3))), 1)
    s_angle = frame * 3.0
    pygame.draw.line(s, (*p["time_accent"][:3], 150), (clock_cx, clock_cy),
        (clock_cx + int(math.cos(s_angle) * (clock_r - 2)), clock_cy + int(math.sin(s_angle) * (clock_r - 2))), 1)
    pygame.draw.circle(s, p["time_accent"], (clock_cx, clock_cy), 2)

    for side in (-1, 1):
        spx = cx + side * (bw // 2 + 6)
        spy = by - 3
        pygame.draw.polygon(s, p["robe_dark"],
            [(spx - 8, spy + 6), (spx, spy - 6), (spx + 8, spy + 6)])
        pygame.draw.polygon(s, p["robe"],
            [(spx - 6, spy + 5), (spx, spy - 4), (spx + 6, spy + 5)])
        pygame.draw.line(s, p["time_accent"], (spx - 6, spy + 5), (spx, spy - 4), 1)
        pygame.draw.line(s, p["time_accent"], (spx, spy - 4), (spx + 6, spy + 5), 1)
        pg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(pg, (*p["time_glow"][:3], 40), (spx, spy + 1), 4)
        s.blit(pg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(s, p["time_accent"], (spx, spy + 1), 2)

    for ax, fl in [(bx - 5, -1), (bx + bw - 1, 1)]:
        arm_sway = [0, 3, 0, -3][frame]
        sleeve_pts = [
            (ax + arm_sway, by + 10 + bob),
            (ax + fl * 16 + arm_sway, by + 24 + bob),
            (ax + fl * 18 + arm_sway, by + 38 + bob),
            (ax + fl * 6 + arm_sway, by + 28 + bob),
        ]
        pygame.draw.polygon(s, p["robe_dark"], sleeve_pts)
        pygame.draw.line(s, (*p["time_accent"][:3], 100),
            (ax + arm_sway, by + 10 + bob), (ax + fl * 18 + arm_sway, by + 38 + bob), 1)
        hand_x = ax + fl * 18 + arm_sway
        hand_y = by + 38 + bob
        eg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(eg, (*p["time_glow"][:3], 80), (hand_x, hand_y), 10)
        pygame.draw.circle(eg, (*p["time_accent"][:3], 50), (hand_x, hand_y), 14)
        s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(s, p["time_accent"], (hand_x, hand_y), 5)
        pygame.draw.circle(s, p["rune"], (hand_x, hand_y), 3)
        pygame.draw.circle(s, (255, 240, 180), (hand_x, hand_y), 1)
        for si in range(4):
            s_angle = frame * 2.0 + si * (math.pi / 2)
            s_dist = 7 + int(math.sin(frame * 2.5 + si) * 3)
            sx = hand_x + int(math.cos(s_angle) * s_dist)
            sy = hand_y + int(math.sin(s_angle) * s_dist)
            sa2 = max(50, 180 - si * 30)
            pygame.draw.circle(s, (*p["time_accent"][:3], sa2), (sx, sy), 1)

    crown_y = int(h * 0.06) + bob + hover
    for si in range(6):
        shard_angle = frame * 0.4 + si * (math.pi * 2 / 6)
        shard_r = int(w * (0.14 + si * 0.01))
        shard_x = cx + int(math.cos(shard_angle) * shard_r)
        shard_y = crown_y + int(math.sin(shard_angle * 0.6) * 8)
        sa = max(50, 140 - si * 15)
        pygame.draw.polygon(s, (*p["rune"][:3], sa),
            [(shard_x, shard_y - 3), (shard_x + 3, shard_y), (shard_x, shard_y + 3), (shard_x - 3, shard_y)])
        sg3 = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(sg3, (*p["time_glow"][:3], sa // 3), (shard_x, shard_y), 5)
        s.blit(sg3, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    crown_pts = [
        (cx - int(w * 0.10), crown_y + 8),
        (cx - int(w * 0.07), crown_y),
        (cx - int(w * 0.03), crown_y + 5),
        (cx, crown_y - 6),
        (cx + int(w * 0.03), crown_y + 5),
        (cx + int(w * 0.07), crown_y),
        (cx + int(w * 0.10), crown_y + 8),
    ]
    pygame.draw.polygon(s, p["time_accent"], crown_pts)
    pygame.draw.polygon(s, p["rune"], crown_pts, 1)
    gem_g = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(gem_g, (*p["time_glow"][:3], 90), (cx, crown_y + 2), 6)
    s.blit(gem_g, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    pygame.draw.circle(s, p["time_accent"], (cx, crown_y + 2), 3)
    pygame.draw.circle(s, (255, 240, 180), (cx, crown_y + 2), 1)
    for gx in [cx - int(w * 0.06), cx + int(w * 0.06)]:
        pygame.draw.circle(s, p["rune"], (gx, crown_y + 4), 2)

    hr = int(w * 0.16); hx, hy = cx, int(h * 0.16) + bob + hover
    pygame.draw.circle(s, p["skin_dark"], (hx, hy + 3), hr + 1)
    pygame.draw.circle(s, p["skin"], (hx, hy), hr)
    pygame.draw.circle(s, p["skin_light"], (hx, hy), hr - 3)
    for wy_off in [4, 7]:
        wla = 30 + int(pulse * 8)
        pygame.draw.line(s, (*p["skin_dark"][:3], wla), (hx - hr // 2, hy + wy_off), (hx + hr // 2, hy + wy_off), 1)
    for cheek in (-1, 1):
        cheek_x = hx + cheek * (hr // 2 + 2)
        pygame.draw.line(s, (*p["skin_dark"][:3], 25), (cheek_x, hy - 2), (cheek_x + cheek * 4, hy + 6), 1)

    pygame.draw.polygon(s, p["robe"],
        [(hx - hr - 8, hy + 10), (hx - hr + 2, hy - 10), (hx, hy - 22), (hx + hr - 2, hy - 10), (hx + hr + 8, hy + 10)])
    pygame.draw.polygon(s, p["robe_dark"],
        [(hx - hr - 4, hy + 8), (hx - hr + 4, hy - 6), (hx, hy - 18), (hx + hr - 4, hy - 6), (hx + hr + 4, hy + 8)])
    pygame.draw.line(s, p["time_accent"], (hx - hr + 2, hy - 9), (hx, hy - 21), 1)
    pygame.draw.line(s, p["time_accent"], (hx, hy - 21), (hx + hr - 2, hy - 9), 1)
    pygame.draw.line(s, (*p["time_accent"][:3], 100), (hx - hr + 5, hy - 5), (hx, hy - 16), 1)
    pygame.draw.line(s, (*p["time_accent"][:3], 100), (hx, hy - 16), (hx + hr - 5, hy - 5), 1)
    hg = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(hg, (*p["time_glow"][:3], 70), (hx, hy - 12), 4)
    s.blit(hg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    pygame.draw.circle(s, p["time_accent"], (hx, hy - 12), 2)
    for hood_x in [hx - hr + 8, hx + hr - 8]:
        pygame.draw.circle(s, (*p["rune"][:3], 80), (hood_x, hy - 3), 2)

    esp = 8 if dir != "side" else 6; so = 2 if dir == "side" else 0
    for ex in (hx - esp + so, hx + esp + so):
        eg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(eg, (*p["time_glow"][:3], 70), (ex, hy + 1), 10)
        pygame.draw.circle(eg, (*p["time_accent"][:3], 35), (ex, hy + 1), 14)
        pygame.draw.circle(eg, (*p["void"][:3], 20), (ex, hy + 1), 18)
        s.blit(eg, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        pygame.draw.circle(s, p["eye_white"], (ex, hy + 1), 5)
        pygame.draw.circle(s, p["eye_pupil"], (ex, hy + 1), 4)
        pygame.draw.circle(s, (30, 20, 10), (ex, hy + 1), 2)
        flare_len = 6 + pulse
        flare_dir = 1 if ex > hx else -1
        pygame.draw.line(s, (*p["time_accent"][:3], 140), (ex, hy + 1),
                        (ex + flare_dir * flare_len, hy - 2), 2)
        pygame.draw.line(s, (*p["time_accent"][:3], 80), (ex, hy + 1),
                        (ex + flare_dir * (flare_len + 4), hy - 4), 1)
        pygame.draw.circle(s, (255, 255, 255, 200), (ex - 1, hy - 1), 1)

    for wi in range(4):
        wa = frame * 0.5 + wi * (math.pi / 2)
        wr = int(w * 0.20) + int(math.sin(wa * 2) * 4)
        wx = cx + int(math.cos(wa) * wr)
        wy = int(h * 0.16) + bob + hover + int(math.sin(wa * 1.3) * 12)
        w_alpha = max(20, 60 - wi * 12)
        w_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.circle(w_surf, (*p["time_glow"][:3], w_alpha), (wx, wy), 3)
        s.blit(w_surf, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
