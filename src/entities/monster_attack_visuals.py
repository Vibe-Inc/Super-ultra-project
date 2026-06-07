from __future__ import annotations

import math
import random
import pygame


def draw_attack_animation(screen: pygame.Surface, enemy, camera_offset: pygame.Vector2):
    """
    Render a close-range attack animation overlay for the given enemy.

    Dispatches to a per-style draw function based on enemy.attack_anim_type
    (or falls back to the visual_style). Progress is the normalized
    elapsed/duration in [0, 1].
    """
    anim = (enemy.attack_anim_type or "").lower()
    if not anim:
        return
    duration = max(0.0001, enemy.attack_anim_duration)
    progress = max(0.0, min(1.0, enemy.attack_anim_elapsed / duration))

    origin = pygame.Vector2(enemy.attack_anim_origin)
    direction = pygame.Vector2(enemy.attack_anim_dir)
    if direction.length_squared() == 0:
        direction = pygame.Vector2(1, 0)
    else:
        direction = direction.normalize()

    sx = int(origin.x - camera_offset.x)
    sy = int(origin.y - camera_offset.y)
    strength = float(enemy.attack_anim_strength)

    # Universal red wind-up indicator – drawn for every enemy (first ~55% of animation)
    _draw_windup_indicator(screen, sx, sy, direction, progress, strength, enemy, anim)

    # Per-enemy strike animation — only plays after wind-up phase finishes,
    # with progress remapped so the strike plays in its own 45% window.
    if progress > 0.55:
        strike_p = (progress - 0.55) / 0.45
        # Scale strike VFX to match the actual damage zone dimensions
        telegraph_range = getattr(enemy, "attack_telegraph_range", 45.0) or 45.0
        range_scale = max(0.5, min(2.0, telegraph_range / 45.0))
        adjusted_strength = strength * range_scale
        handler = _DISPATCH.get(anim, _draw_generic_strike)
        handler(screen, sx, sy, direction, strike_p, adjusted_strength, enemy)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _aa_circle(screen, color, center, radius, width=0):
    if radius < 1:
        return
    size = int(radius * 2 + 4)
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (size // 2, size // 2), int(radius), width)
    screen.blit(surf, (center[0] - size // 2, center[1] - size // 2),
                special_flags=pygame.BLEND_ALPHA_SDL2)


def _aa_arc(screen, color, center, radius, start_rad, end_rad, width):
    size = int(radius * 2 + 8)
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    rect = pygame.Rect(2, 2, size - 4, size - 4)
    pygame.draw.arc(surf, color, rect, start_rad, end_rad, max(1, int(width)))
    screen.blit(surf, (center[0] - size // 2, center[1] - size // 2),
                special_flags=pygame.BLEND_ALPHA_SDL2)


def _aa_ellipse(screen, color, rect_tuple):
    x, y, w, h = rect_tuple
    if w < 1 or h < 1:
        return
    surf = pygame.Surface((int(w) + 2, int(h) + 2), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, color, (1, 1, int(w), int(h)))
    screen.blit(surf, (int(x), int(y)), special_flags=pygame.BLEND_ALPHA_SDL2)


def _aa_polygon(screen, color, points):
    if not points:
        return
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    minx, miny = min(xs), min(ys)
    maxx, maxy = max(xs), max(ys)
    w = max(2, int(maxx - minx) + 4)
    h = max(2, int(maxy - miny) + 4)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    offset_pts = [(p[0] - minx + 2, p[1] - miny + 2) for p in points]
    pygame.draw.polygon(surf, color, offset_pts)
    screen.blit(surf, (int(minx - 2), int(miny - 2)),
                special_flags=pygame.BLEND_ALPHA_SDL2)


def _aa_line(screen, color, p1, p2, width):
    pygame.draw.line(screen, color, p1, p2, max(1, int(width)))


def _slash_arc(screen, cx, cy, base_angle_deg, sweep_deg, radius, progress, color, width=4, layers=3):
    """Draw a curved slash trail expanding through the sweep as progress grows."""
    cur_sweep = sweep_deg * max(0.0, min(1.0, progress))
    if cur_sweep <= 1:
        return
    for layer in range(layers):
        lf = 1.0 - layer * 0.22
        r = max(2, radius * (1.0 - layer * 0.08))
        a = int(color[3] * lf) if len(color) > 3 else int(180 * lf)
        if a <= 0:
            continue
        col = (color[0], color[1], color[2], a)
        start = math.radians(base_angle_deg - cur_sweep * 0.5)
        end = math.radians(base_angle_deg + cur_sweep * 0.5)
        _aa_arc(screen, col, (cx, cy), r, start, end, max(1, int(width * lf)))


def _impact_ring(screen, cx, cy, radius, color, width=3):
    if radius < 1:
        return
    size = int(radius * 2 + 8)
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (size // 2, size // 2), int(radius), max(1, int(width)))
    screen.blit(surf, (cx - size // 2, cy - size // 2), special_flags=pygame.BLEND_ALPHA_SDL2)


def _ground_shockwave(screen, cx, cy, radius, ring_color, fill_color=None, flat=0.45):
    """Flattened ellipse for a ground-style shockwave (perspective)."""
    if radius < 1:
        return
    w = int(radius * 2)
    h = max(2, int(radius * 2 * flat))
    rect = (cx - w // 2, cy - h // 2, w, h)
    if fill_color is not None:
        _aa_ellipse(screen, fill_color, rect)
    surf = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, ring_color, (2, 2, w, h), 2)
    screen.blit(surf, (cx - (w + 4) // 2, cy - (h + 4) // 2),
                special_flags=pygame.BLEND_ALPHA_SDL2)


def _seeded(seed_obj, salt: int = 0) -> random.Random:
    r = random.Random()
    r.seed(id(seed_obj) ^ (salt * 2654435761))
    return r


def _curve(progress: float, peak: float = 0.5) -> float:
    """Bell-shaped curve peaking at `peak`, returning 0..1."""
    if progress <= 0 or progress >= 1:
        return 0.0
    if progress < peak:
        return progress / peak
    return 1.0 - (progress - peak) / (1.0 - peak)


# Attack types whose damage area is a full circle around the enemy (AoE).
# Used by the universal wind-up to draw a circular indicator instead of a cone.
_AOE_ATTACKS = frozenset({
    "cryomancer_nova", "molten_nova", "plaguebearer_nova",
    "stormcaller_field", "arcanist_burst", "titan_stomp",
    "revenant_undying", "shadowmancer_blink",
    "trickster_strike",
})


def _draw_windup_indicator(screen, cx, cy, direction, progress, strength, enemy, anim_type):
    if progress > 0.55:
        return

    p = progress / 0.55
    is_aoe = anim_type.lower() in _AOE_ATTACKS

    telegraph_range = getattr(enemy, "attack_telegraph_range", 60.0) or 60.0
    r = max(2, int(telegraph_range * strength * p))

    # Brighter, more opaque wind-up — stays visible longer
    outer_alpha = int(220 * (1 - p * 0.5))
    inner_alpha = int(160 * (1 - p * 0.4))
    red_outer = (255, 50, 50, outer_alpha)
    red_inner = (255, 100, 100, inner_alpha)

    if is_aoe:
        _aa_circle(screen, red_outer, (cx, cy), r, max(3, int(4 * strength)))
        inner_r = max(2, int(r * 0.6))
        _aa_circle(screen, red_inner, (cx, cy), inner_r, max(2, int(3 * strength)))
    else:
        fwd_angle = math.degrees(math.atan2(direction.y, direction.x))
        telegraph_angle = getattr(enemy, "attack_telegraph_angle", 130.0) or 130.0
        half_angle = telegraph_angle * 0.5
        _aa_arc(screen, red_outer, (cx, cy), r,
                math.radians(fwd_angle - half_angle),
                math.radians(fwd_angle + half_angle),
                max(4, int(5 * strength)))
        inner_r = max(2, int(r * 0.6))
        _aa_arc(screen, red_inner, (cx, cy), inner_r,
                math.radians(fwd_angle - half_angle),
                math.radians(fwd_angle + half_angle),
                max(2, int(3 * strength)))


# ============================================================
# BRUTE — heavy slam: ground shockwave, lava cracks, ember burst
# ============================================================
def _draw_brute_slam(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 11)
    fwd_angle_deg = math.degrees(math.atan2(direction.y, direction.x))
    base_size = 80 * strength

    # Impact point offset — placed in the attack direction so the arc and impact
    # are visually aligned, fixing the previous vertical mirror (impact always
    # below center regardless of direction).
    impact_off_x = int(direction.x * 22 * strength)
    impact_off_y = int(direction.y * 22 * strength)

    # Phase A: wind-up glow & dust cloud puff at impact point (0 .. 0.25)
    if progress < 0.30:
        p = progress / 0.30
        glow_r = int(20 * strength + 10 * p)
        a = int(180 * (1 - p))
        _aa_circle(screen, (255, 90, 30, a), (cx + impact_off_x, cy + impact_off_y + int(6 * strength)), glow_r)
        # rising ember sparks during windup
        for i in range(6):
            ang = rng.uniform(0, math.tau)
            d = 8 + rng.random() * 14 * strength
            ex = cx + impact_off_x + int(math.cos(ang) * d * p)
            ey = cy + impact_off_y + int(8 * strength) - int(p * 18 * strength) + int(math.sin(ang) * 3)
            _aa_circle(screen, (255, 200, 80, int(220 * (1 - p))), (ex, ey), 2 + int((1 - p) * 2))

    # Phase B: impact strike (0.25 .. 0.65)
    if 0.25 <= progress < 0.65:
        p = (progress - 0.25) / 0.40
        # bright impact flash at the directional impact point
        flash_r = int((40 + 90 * p) * strength)
        flash_a = int(230 * (1 - p))
        _aa_circle(screen, (255, 230, 140, flash_a // 2), (cx + impact_off_x, cy + impact_off_y + int(6 * strength)), flash_r)
        _aa_circle(screen, (255, 120, 30, flash_a), (cx + impact_off_x, cy + impact_off_y + int(6 * strength)), flash_r // 2)
        # core flame
        _aa_circle(screen, (255, 255, 220, int(255 * (1 - p))), (cx + impact_off_x, cy + impact_off_y + int(6 * strength)), int(8 * (1 - p) * strength) + 2)

        # forward fist sweep arc at impact point too
        sweep_deg = 150
        _slash_arc(screen, cx + impact_off_x, cy + impact_off_y, fwd_angle_deg, sweep_deg, int(base_size * 0.7),
                   p * 1.2, (255, 140, 40, int(220 * (1 - p))), width=8, layers=3)
        _slash_arc(screen, cx + impact_off_x, cy + impact_off_y, fwd_angle_deg, sweep_deg, int(base_size * 0.7),
                   p * 1.2, (255, 220, 120, int(180 * (1 - p))), width=4, layers=2)

    # Phase C: ground shockwave rings + ember rain (0.30 .. 1.0)
    if progress >= 0.30:
        p = (progress - 0.30) / 0.70
        # Ground-rooted position — the shockwave stays at the enemy's feet
        gx = cx
        gy = cy + int(22 * strength)
        # three expanding ground rings
        for i in range(3):
            ri_p = max(0.0, min(1.0, p - i * 0.18))
            if ri_p <= 0:
                continue
            r = int((30 + 120 * ri_p) * strength)
            a = int(220 * (1 - ri_p))
            _ground_shockwave(screen, gx, gy, r,
                              (255, 110, 30, a), (255, 60, 20, a // 4))
        # inner heat haze ellipse
        haze_r = int((20 + 60 * p) * strength)
        _ground_shockwave(screen, gx, gy, haze_r,
                          (255, 200, 80, int(120 * (1 - p))))

        # lava crack lines radiating out
        crack_p = max(0.0, min(1.0, (progress - 0.32) / 0.45))
        if crack_p > 0:
            for i in range(8):
                ang = i * math.tau / 8 + rng.uniform(-0.18, 0.18)
                rr = int((22 + 90 * crack_p) * strength)
                ex = gx + int(math.cos(ang) * rr)
                ey = gy + int(math.sin(ang) * rr * 0.45)
                _aa_line(screen, (255, 180, 60, int(220 * (1 - crack_p))),
                         (gx, gy), (ex, ey), max(1, int(3 * (1 - crack_p))))
                # inner bright crack core
                _aa_line(screen, (255, 240, 180, int(160 * (1 - crack_p))),
                         (gx, gy), (ex, ey), 1)

        # flying embers from impact point
        for i in range(14):
            tp = (p - i * 0.04) * 1.3
            if tp < 0 or tp > 1:
                continue
            ang = rng.uniform(0, math.tau)
            dist = 12 + tp * 90 * strength
            ex = cx + impact_off_x + int(math.cos(ang) * dist)
            ey = cy + impact_off_y + int(8 * strength) + int(math.sin(ang) * dist * 0.4) - int(tp * 20)
            er = max(1, int(3 * (1 - tp)))
            ec = (255, rng.randint(140, 220), rng.randint(40, 110), int(220 * (1 - tp)))
            _aa_circle(screen, ec, (ex, ey), er)

    # rising heat smoke
    if progress > 0.45:
        sp = (progress - 0.45) / 0.55
        for i in range(4):
            offset = (i - 1.5) * 8
            sy_off = cy - int(sp * 30 * strength) + int(8 * math.sin(sp * 6 + i))
            _aa_circle(screen, (80, 50, 40, int(120 * (1 - sp))),
                       (cx + int(offset), sy_off + int(10 * strength)),
                       int((6 + sp * 8) * strength))


# ============================================================
# VENOMOUS — fang strike: green slash + poison splash + drips
# ============================================================
def _draw_venomous_strike(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 22)
    fwd_angle_deg = math.degrees(math.atan2(direction.y, direction.x))

    target_x = cx + int(direction.x * 32 * strength)
    target_y = cy + int(direction.y * 32 * strength)

    # Phase A: twin fang strike (0 .. 0.4) — covers 100° cone (damage area)
    if progress < 0.45:
        p = progress / 0.45
        # twin curved fang trails spanning 100° cone
        for sign in (-1, 1):
            angle = fwd_angle_deg + sign * 50
            sweep = 55
            _slash_arc(screen, cx, cy, angle, sweep, int(38 * strength),
                       p * 1.25,
                       (180, 240, 110, int(220 * (1 - p))), width=5, layers=3)
            _slash_arc(screen, cx, cy, angle, sweep, int(38 * strength),
                       p * 1.25,
                       (240, 255, 200, int(200 * (1 - p))), width=2, layers=2)
        # fang tips (twin sharp triangles) advancing forward
        perp = pygame.Vector2(-direction.y, direction.x)
        tip_dist = 16 + p * 28 * strength
        for sign in (-1, 1):
            tip = pygame.Vector2(direction) * tip_dist + perp * sign * (6 * strength)
            tx = cx + int(tip.x)
            ty = cy + int(tip.y)
            back1 = pygame.Vector2(direction) * (tip_dist - 14) + perp * sign * (10 * strength)
            back2 = pygame.Vector2(direction) * (tip_dist - 14) + perp * sign * (2 * strength)
            _aa_polygon(screen, (240, 250, 235, int(220 * (1 - p))),
                        [(tx, ty), (cx + int(back1.x), cy + int(back1.y)),
                         (cx + int(back2.x), cy + int(back2.y))])
            _aa_polygon(screen, (210, 60, 70, int(180 * (1 - p))),
                        [(tx, ty),
                         (cx + int(back1.x * 0.7 + back2.x * 0.3),
                          cy + int(back1.y * 0.7 + back2.y * 0.3)),
                         (cx + int(back2.x * 0.6),
                          cy + int(back2.y * 0.6))])

    # Phase B: poison splash burst at impact (0.30 .. 1.0)
    if progress >= 0.30:
        p = (progress - 0.30) / 0.70
        # main green puff cloud (3 layered)
        for layer in range(3):
            lf = 1.0 - layer * 0.2
            r = int((12 + 35 * p) * lf * strength)
            a = int(180 * (1 - p) * lf)
            shade = (90 + layer * 18, 200 - layer * 12, 110 + layer * 8, a)
            _aa_circle(screen, shade, (target_x, target_y), r)
        # bubbles
        for i in range(8):
            bp = (p - i * 0.05) * 1.3
            if bp < 0 or bp > 1:
                continue
            ang = rng.uniform(0, math.tau)
            d = 10 + bp * 26 * strength
            bx = target_x + int(math.cos(ang) * d)
            by = target_y + int(math.sin(ang) * d) - int(bp * 14)
            br = max(1, int(3 * (1 - bp)))
            _aa_circle(screen, (180, 250, 140, int(200 * (1 - bp))), (bx, by), br)
            _aa_circle(screen, (240, 255, 200, int(220 * (1 - bp))), (bx - 1, by - 1), max(1, br - 1))
        # acid drip splatters around impact
        for i in range(6):
            ap = (p - 0.15 - i * 0.08) * 1.5
            if ap < 0 or ap > 1:
                continue
            ang = rng.uniform(math.pi * 0.1, math.pi * 0.9)
            d = 14 + ap * 24 * strength
            sx = target_x + int(math.cos(ang) * d * rng.choice([-1, 1]))
            sy = target_y + int(ap * 22) + int(math.sin(ang) * 4)
            _aa_polygon(screen, (120, 200, 80, int(200 * (1 - ap))),
                        [(sx, sy), (sx - 2, sy - 5), (sx + 2, sy - 5)])
            _aa_circle(screen, (160, 230, 110, int(220 * (1 - ap))), (sx, sy + 2), 2)

    # poison drips dropping straight down at end
    if progress > 0.55:
        dp = (progress - 0.55) / 0.45
        for i in range(5):
            sd = (i - 2) * 8
            yd = target_y + int(dp * 28) + i * 2
            a = int(180 * (1 - dp))
            _aa_circle(screen, (140, 220, 90, a), (target_x + sd, yd), 2)
            _aa_polygon(screen, (140, 220, 90, a),
                        [(target_x + sd, yd - 3),
                         (target_x + sd - 2, yd + 2),
                         (target_x + sd + 2, yd + 2)])


# ============================================================
# TRICKSTER — twin dagger X-slash + smoke puff (from blink)
# ============================================================
def _draw_trickster_strike(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 33)
    fwd_angle_deg = math.degrees(math.atan2(direction.y, direction.x))

    # Phase A: smoke puff (from teleport) (0 .. 0.35)
    if progress < 0.40:
        p = progress / 0.40
        for i in range(6):
            ang = i * math.tau / 6 + p * 0.5
            r = int((10 + p * 22) * strength)
            ox = cx + int(math.cos(ang) * r * 0.6)
            oy = cy + int(math.sin(ang) * r * 0.6)
            cloud_r = max(2, int((8 + (1 - p) * 6) * strength))
            shade = rng.randint(60, 110)
            _aa_circle(screen, (shade, shade - 10, shade + 5, int(200 * (1 - p))),
                       (ox, oy), cloud_r)
        # central dark vortex
        _aa_circle(screen, (35, 30, 45, int(220 * (1 - p))),
                   (cx, cy), int(6 * strength + 4))

    # Phase B: radial burst (360° — damage area is a full circle) + X-slash daggers
    if 0.15 <= progress < 0.80:
        p = (progress - 0.15) / 0.65
        # Expanding radial ring
        ring_r = int((8 + 45 * p) * strength)
        ring_a = int(200 * (1 - p))
        _aa_circle(screen, (220, 80, 100, ring_a), (cx, cy), ring_r, max(2, int(4 * strength)))
        _aa_circle(screen, (255, 180, 200, ring_a // 2), (cx, cy), ring_r - 3, max(1, int(2 * strength)))

        # X-slash daggers (secondary visual)
        for sign in (-1, 1):
            slash_angle = fwd_angle_deg + sign * 45
            sweep = 110
            _slash_arc(screen, cx, cy, slash_angle, sweep, int(42 * strength),
                       p * 1.25,
                       (220, 80, 100, int(220 * (1 - p))), width=6, layers=3)
            _slash_arc(screen, cx, cy, slash_angle, sweep, int(42 * strength),
                       p * 1.25,
                       (255, 200, 220, int(200 * (1 - p))), width=2, layers=2)

        # dagger blade flashes
        perp = pygame.Vector2(-direction.y, direction.x)
        dagger_p = max(0.0, min(1.0, p * 1.2))
        for sign in (-1, 1):
            t = dagger_p
            tip = pygame.Vector2(direction) * (20 + t * 28 * strength) + perp * sign * (16 * strength * (1 - t * 0.5))
            base = pygame.Vector2(direction) * (8 + t * 14 * strength) + perp * sign * (10 * strength)
            tx, ty = cx + int(tip.x), cy + int(tip.y)
            bx, by = cx + int(base.x), cy + int(base.y)
            mid = pygame.Vector2(direction) * (14 + t * 22 * strength) + perp * sign * (13 * strength)
            mx, my = cx + int(mid.x), cy + int(mid.y)
            edge = (mx + (sign * 4), my - 4)
            a = int(220 * (1 - t))
            _aa_polygon(screen, (190, 200, 215, a), [(tx, ty), (bx, by), edge])
            _aa_polygon(screen, (230, 235, 245, a), [(tx, ty), (mx, my), edge])

    # Phase C: red sparkle confetti + ribbon trail (0.4 .. 1.0)
    if progress >= 0.40:
        p = (progress - 0.40) / 0.60
        for i in range(14):
            cp = (p - i * 0.04) * 1.3
            if cp < 0 or cp > 1:
                continue
            ang = rng.uniform(0, math.tau)
            d = 6 + cp * 50 * strength
            cx2 = cx + int(math.cos(ang) * d)
            cy2 = cy + int(math.sin(ang) * d * 0.8) - int(cp * 8)
            sz = max(1, int(3 * (1 - cp)))
            col_choice = rng.choice([(255, 80, 90), (255, 170, 60), (255, 220, 120), (220, 80, 130)])
            col = (col_choice[0], col_choice[1], col_choice[2], int(220 * (1 - cp)))
            # diamond sparkle
            _aa_polygon(screen, col,
                        [(cx2, cy2 - sz), (cx2 + sz, cy2),
                         (cx2, cy2 + sz), (cx2 - sz, cy2)])

        # cross-flash at impact center
        flash_p = _curve(p, 0.2)
        if flash_p > 0:
            fc = (255, 200, 220, int(220 * flash_p))
            fl = int(18 * flash_p * strength)
            _aa_line(screen, fc, (cx - fl, cy), (cx + fl, cy), 3)
            _aa_line(screen, fc, (cx, cy - fl), (cx, cy + fl), 3)
            _aa_line(screen, fc, (cx - fl // 2, cy - fl // 2),
                     (cx + fl // 2, cy + fl // 2), 2)
            _aa_line(screen, fc, (cx + fl // 2, cy - fl // 2),
                     (cx - fl // 2, cy + fl // 2), 2)


# ============================================================
# STALKER — dark crescent slash + crimson shadow trail
# ============================================================
def _draw_stalker_slash(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 44)
    fwd_angle_deg = math.degrees(math.atan2(direction.y, direction.x))
    sweep_deg = 130
    radius = int(50 * strength)

    # main crescent (multi-layer crimson + dark)
    # dark outer
    _slash_arc(screen, cx, cy, fwd_angle_deg, sweep_deg, radius + 6, progress * 1.1,
               (40, 8, 20, int(220 * (1 - progress))), width=11, layers=2)
    # blood-red
    _slash_arc(screen, cx, cy, fwd_angle_deg, sweep_deg, radius, progress * 1.1,
               (180, 30, 50, int(220 * (1 - progress))), width=7, layers=3)
    # bright cutting edge
    _slash_arc(screen, cx, cy, fwd_angle_deg, sweep_deg, radius - 4, progress * 1.1,
               (255, 200, 210, int(220 * (1 - progress))), width=3, layers=2)

    # blade itself (moving along the arc)
    blade_p = max(0.0, min(1.0, progress * 1.1))
    cur_angle = math.radians(fwd_angle_deg - sweep_deg * 0.5 + sweep_deg * blade_p)
    blade_dir = pygame.Vector2(math.cos(cur_angle), math.sin(cur_angle))
    blade_perp = pygame.Vector2(-blade_dir.y, blade_dir.x)
    tip = blade_dir * (radius + 6)
    base = blade_dir * (radius - 12)
    edge = blade_dir * radius + blade_perp * 3
    a = int(220 * (1 - progress))
    _aa_polygon(screen, (180, 190, 200, a),
                [(cx + int(tip.x), cy + int(tip.y)),
                 (cx + int(base.x), cy + int(base.y)),
                 (cx + int(edge.x), cy + int(edge.y))])
    _aa_polygon(screen, (230, 235, 245, a),
                [(cx + int(tip.x), cy + int(tip.y)),
                 (cx + int(edge.x * 0.8), cy + int(edge.y * 0.8)),
                 (cx + int(base.x * 0.7), cy + int(base.y * 0.7))])
    # crimson droplet at blade tip
    _aa_circle(screen, (180, 30, 50, int(220 * (1 - progress))),
               (cx + int(tip.x), cy + int(tip.y)), 3)

    # speed lines behind the arc
    for i in range(7):
        sp = (progress - i * 0.04) * 1.3
        if sp < 0 or sp > 1:
            continue
        ang = math.radians(fwd_angle_deg - sweep_deg * 0.5 + sweep_deg * sp - 8)
        ld = pygame.Vector2(math.cos(ang), math.sin(ang))
        r1 = radius - 14
        r2 = radius + 4
        p1 = (cx + int(ld.x * r1), cy + int(ld.y * r1))
        p2 = (cx + int(ld.x * r2), cy + int(ld.y * r2))
        _aa_line(screen, (210, 80, 100, int(200 * (1 - sp))), p1, p2, max(1, int(2 * (1 - sp))))

    # shadow tendrils trailing the strike
    if progress > 0.3:
        sp = (progress - 0.3) / 0.7
        for i in range(5):
            ang = math.radians(fwd_angle_deg - sweep_deg * 0.5 - i * 14 - sp * 30)
            r = radius + 6 + i * 4
            tx = cx + int(math.cos(ang) * r)
            ty = cy + int(math.sin(ang) * r)
            _aa_circle(screen, (15, 5, 18, int(150 * (1 - sp))), (tx, ty),
                       max(2, int(6 * (1 - sp))))

    # crimson ember splatter at impact start
    if progress < 0.4:
        p = progress / 0.4
        for i in range(8):
            ang = rng.uniform(0, math.tau)
            d = 8 + p * 30 * strength
            ex = cx + int(math.cos(ang) * d)
            ey = cy + int(math.sin(ang) * d)
            _aa_circle(screen, (200, 40, 60, int(220 * (1 - p))), (ex, ey),
                       max(1, int(3 * (1 - p))))


# ============================================================
# SKIRMISHER — three talon claw rakes + feather burst
# ============================================================
def _draw_skirmisher_claw(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 55)
    fwd_angle_deg = math.degrees(math.atan2(direction.y, direction.x))
    perp = pygame.Vector2(-direction.y, direction.x)

    # Three parallel talon slashes, offset perpendicular
    for i, off in enumerate((-12, 0, 12)):
        delay = i * 0.06
        p = (progress - delay) / max(0.0001, 0.6 - delay)
        p = max(0.0, min(1.0, p))
        if p <= 0:
            continue
        ox = perp.x * off * strength * 0.6
        oy = perp.y * off * strength * 0.6
        center_x = cx + int(ox)
        center_y = cy + int(oy)

        sweep_deg = 130
        radius = int(40 * strength)
        a = int(220 * (1 - p))
        # outer dark slash
        _slash_arc(screen, center_x, center_y, fwd_angle_deg + i * 4 - 4, sweep_deg, radius + 4,
                   p * 1.1, (60, 30, 25, a), width=7, layers=2)
        # mid blood-orange
        _slash_arc(screen, center_x, center_y, fwd_angle_deg + i * 4 - 4, sweep_deg, radius,
                   p * 1.1, (220, 70, 60, a), width=5, layers=2)
        # white cutting edge
        _slash_arc(screen, center_x, center_y, fwd_angle_deg + i * 4 - 4, sweep_deg, radius - 3,
                   p * 1.1, (245, 230, 200, a), width=2, layers=2)

        # talon tip line
        blade_p = max(0.0, min(1.0, p * 1.1))
        cur_angle = math.radians(fwd_angle_deg - sweep_deg * 0.5 + sweep_deg * blade_p)
        ld = pygame.Vector2(math.cos(cur_angle), math.sin(cur_angle))
        tip = ld * (radius + 6)
        base = ld * (radius - 6)
        _aa_line(screen, (40, 20, 20, a), (center_x + int(base.x), center_y + int(base.y)),
                 (center_x + int(tip.x), center_y + int(tip.y)), 3)
        _aa_line(screen, (210, 200, 180, a),
                 (center_x + int(base.x), center_y + int(base.y)),
                 (center_x + int(tip.x), center_y + int(tip.y)), 1)
        # crimson scratch droplet
        _aa_circle(screen, (200, 50, 50, a),
                   (center_x + int(tip.x), center_y + int(tip.y)), 2)

    # feather burst (golden crest feathers + dark plume)
    if progress > 0.20:
        p = (progress - 0.20) / 0.80
        for i in range(12):
            fp = (p - i * 0.05) * 1.3
            if fp < 0 or fp > 1:
                continue
            ang = rng.uniform(0, math.tau)
            d = 8 + fp * 45 * strength
            fx = cx + int(math.cos(ang) * d)
            fy = cy + int(math.sin(ang) * d) - int(fp * 10)
            length = max(3, int(8 * (1 - fp)))
            tip_off = pygame.Vector2(math.cos(ang), math.sin(ang)) * length
            choice = rng.random()
            if choice < 0.5:
                col = (220, 175, 78, int(220 * (1 - fp)))   # crest gold
                edge = (255, 235, 120, int(220 * (1 - fp)))
            else:
                col = (38, 88, 78, int(220 * (1 - fp)))     # dark plume
                edge = (118, 178, 162, int(220 * (1 - fp)))
            _aa_polygon(screen, col,
                        [(fx, fy),
                         (fx + int(tip_off.x), fy + int(tip_off.y)),
                         (fx + int(tip_off.x * 0.4 - tip_off.y * 0.3),
                          fy + int(tip_off.y * 0.4 + tip_off.x * 0.3))])
            _aa_line(screen, edge, (fx, fy),
                     (fx + int(tip_off.x), fy + int(tip_off.y)), 1)

    # red warpaint flash overlay
    if progress < 0.30:
        p = progress / 0.30
        a = int(150 * (1 - p))
        _aa_circle(screen, (210, 70, 58, a), (cx, cy), int((18 + p * 18) * strength))


# ============================================================
# GUARDIAN — heavy brass smash: shield bash + steam + sparks
# ============================================================
def _draw_guardian_smash(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 66)
    fwd_angle_deg = math.degrees(math.atan2(direction.y, direction.x))

    # Phase A: steam burst windup (0 .. 0.30)
    if progress < 0.35:
        p = progress / 0.35
        for i in range(5):
            ang = rng.uniform(-math.pi * 0.4, math.pi * 0.4)
            d = 6 + p * 16 * strength
            sx = cx + int(math.cos(ang) * d) - int(direction.x * 14)
            sy = cy - int(p * 18 * strength) - 6 + int(math.sin(ang) * d * 0.4)
            r = max(3, int(7 * (1 - p) + 6 * p) * strength)
            _aa_circle(screen, (220, 220, 225, int(160 * (1 - p))), (sx, sy), int(r * strength))

    # Phase B: brass fist swing arc (0.20 .. 0.65)
    if 0.20 <= progress < 0.75:
        p = (progress - 0.20) / 0.55
        sweep_deg = 130
        radius = int(46 * strength)
        # outer dark shadow
        _slash_arc(screen, cx, cy, fwd_angle_deg, sweep_deg, radius + 6, p * 1.15,
                   (60, 40, 25, int(220 * (1 - p))), width=10, layers=2)
        # brass body
        _slash_arc(screen, cx, cy, fwd_angle_deg, sweep_deg, radius, p * 1.15,
                   (200, 165, 80, int(220 * (1 - p))), width=7, layers=3)
        # bright copper edge
        _slash_arc(screen, cx, cy, fwd_angle_deg, sweep_deg, radius - 4, p * 1.15,
                   (255, 215, 130, int(200 * (1 - p))), width=3, layers=2)

        # the brass fist sphere itself moving along the arc
        blade_p = max(0.0, min(1.0, p * 1.15))
        cur_angle = math.radians(fwd_angle_deg - sweep_deg * 0.5 + sweep_deg * blade_p)
        ld = pygame.Vector2(math.cos(cur_angle), math.sin(cur_angle))
        fist_pos = (cx + int(ld.x * radius), cy + int(ld.y * radius))
        a = int(255 * (1 - p))
        _aa_circle(screen, (60, 42, 22, a), fist_pos, int(11 * strength))
        _aa_circle(screen, (200, 165, 80, a), fist_pos, int(9 * strength))
        _aa_circle(screen, (235, 205, 130, a), fist_pos, int(6 * strength))
        # rivet on fist
        _aa_circle(screen, (60, 42, 22, a), (fist_pos[0] - 2, fist_pos[1] - 2), 2)
        _aa_circle(screen, (255, 235, 180, a), (fist_pos[0] - 3, fist_pos[1] - 3), 1)

    # Phase C: heavy impact + brass spark fireworks + ember rain
    if progress >= 0.40:
        p = (progress - 0.40) / 0.60
        impact_x = cx + int(direction.x * 38 * strength)
        impact_y = cy + int(direction.y * 38 * strength)

        # bright impact flash
        flash_p = _curve(p, 0.15)
        if flash_p > 0:
            _aa_circle(screen, (255, 240, 180, int(220 * flash_p)),
                       (impact_x, impact_y), int(22 * flash_p * strength))
            _aa_circle(screen, (255, 175, 60, int(200 * flash_p)),
                       (impact_x, impact_y), int(14 * flash_p * strength))

        # expanding brass impact ring
        ring_r = int((10 + 50 * p) * strength)
        _impact_ring(screen, impact_x, impact_y, ring_r,
                     (200, 165, 80, int(220 * (1 - p))), width=3)
        _impact_ring(screen, impact_x, impact_y, ring_r - 4,
                     (255, 215, 130, int(180 * (1 - p))), width=2)

        # ground shockwave under impact
        _ground_shockwave(screen, impact_x, impact_y + int(12 * strength),
                          int((20 + 70 * p) * strength),
                          (255, 175, 60, int(200 * (1 - p))),
                          (255, 215, 130, int(60 * (1 - p))))

        # spinning brass spark streaks
        for i in range(14):
            sp = (p - i * 0.035) * 1.35
            if sp < 0 or sp > 1:
                continue
            ang = i * (math.tau / 14) + sp * 1.4
            d = 4 + sp * 60 * strength
            ex1 = impact_x + int(math.cos(ang) * d * 0.4)
            ey1 = impact_y + int(math.sin(ang) * d * 0.4)
            ex2 = impact_x + int(math.cos(ang) * d)
            ey2 = impact_y + int(math.sin(ang) * d * 0.7)
            col = rng.choice([(255, 215, 130), (255, 175, 60), (200, 165, 80)])
            a = int(220 * (1 - sp))
            _aa_line(screen, (*col, a), (ex1, ey1), (ex2, ey2), max(1, int(3 * (1 - sp))))
            # bright tip
            _aa_circle(screen, (255, 240, 200, a), (ex2, ey2), max(1, int(2 * (1 - sp))))

        # falling embers
        for i in range(8):
            ep = (p - i * 0.06) * 1.3
            if ep < 0 or ep > 1:
                continue
            ang = rng.uniform(-math.pi * 0.9, math.pi * 0.1)
            dist = 10 + ep * 45 * strength
            ex = impact_x + int(math.cos(ang) * dist)
            ey = impact_y + int(math.sin(ang) * dist) + int(ep * 20)
            _aa_circle(screen, (255, 175, 60, int(220 * (1 - ep))),
                       (ex, ey), max(1, int(2 * (1 - ep))))


# ============================================================
# ARCANIST — arcane self-melee burst (purple ring, runes)
# ============================================================
def _draw_arcanist_burst(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 77)
    p = progress

    # purple glow ring
    for layer in range(3):
        lf = 1.0 - layer * 0.22
        r = int((20 + 40 * p) * strength * lf)
        a = int(180 * (1 - p) * lf)
        _aa_circle(screen, (160, 110, 230, a), (cx, cy), r, 2)

    # rotating rune sparkles
    for i in range(8):
        ang = i * math.tau / 8 + p * 4.0
        r = int((22 + 25 * p) * strength)
        rx = cx + int(math.cos(ang) * r)
        ry = cy + int(math.sin(ang) * r)
        _aa_circle(screen, (255, 225, 110, int(220 * (1 - p))), (rx, ry), 3)
        _aa_circle(screen, (200, 220, 255, int(160 * (1 - p))), (rx, ry), 5, 1)

    # central energy burst
    if p < 0.5:
        cp = p / 0.5
        _aa_circle(screen, (200, 180, 255, int(220 * (1 - cp))),
                   (cx, cy), int((6 + 18 * cp) * strength))


# ============================================================
# BOMBER — close-range punch fallback (uses generic strike + brass tint)
# ============================================================
def _draw_bomber_strike(screen, cx, cy, direction, progress, strength, enemy):
    fwd_angle_deg = math.degrees(math.atan2(direction.y, direction.x))
    sweep_deg = 100
    _slash_arc(screen, cx, cy, fwd_angle_deg, sweep_deg, int(36 * strength),
               progress * 1.1, (200, 150, 85, int(220 * (1 - progress))), width=5, layers=3)
    _slash_arc(screen, cx, cy, fwd_angle_deg, sweep_deg, int(36 * strength),
               progress * 1.1, (255, 220, 150, int(180 * (1 - progress))), width=2, layers=2)
    if progress > 0.4:
        p = (progress - 0.4) / 0.6
        for i in range(6):
            ang = i * math.tau / 6 + p * 2
            d = int((10 + 30 * p) * strength)
            ex = cx + int(direction.x * 28 + math.cos(ang) * d)
            ey = cy + int(direction.y * 28 + math.sin(ang) * d)
            _aa_circle(screen, (255, 200, 80, int(220 * (1 - p))), (ex, ey), max(1, int(3 * (1 - p))))


# ============================================================
# PHANTOM DRAIN — spectral beam that siphons life
# ============================================================
def _draw_phantom_drain(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 88)

    # spectral beam from caster outward
    beam_len = int(50 * strength * progress)
    target_x = cx + int(direction.x * beam_len)
    target_y = cy + int(direction.y * beam_len)

    # outer dark aura
    for layer in range(3):
        lf = 1.0 - layer * 0.2
        a = int(120 * (1 - progress) * lf)
        r = int((14 + 20 * progress) * lf * strength)
        _aa_circle(screen, (80, 40, 120, a), (cx, cy), r)

    # spectral beam (pulsing wavy line)
    if progress > 0.1:
        bp = (progress - 0.1) / 0.9
        num_pts = 12
        pts = []
        for i in range(num_pts + 1):
            t = i / num_pts
            bx = cx + int(direction.x * t * beam_len)
            by = cy + int(direction.y * t * beam_len)
            # perpendicular wave
            wave = math.sin(t * 8 + progress * 12) * (6 + progress * 8) * strength
            perp_x = -direction.y
            perp_y = direction.x
            bx += int(perp_x * wave)
            by += int(perp_y * wave)
            pts.append((bx, by))
        if len(pts) >= 2:
            # dark beam
            for i in range(len(pts) - 1):
                ba = int(200 * (1 - bp))
                _aa_line(screen, (100, 40, 160, ba), pts[i], pts[i + 1], 4)
                _aa_line(screen, (180, 120, 240, ba), pts[i], pts[i + 1], 2)
                _aa_line(screen, (220, 180, 255, ba // 2), pts[i], pts[i + 1], 1)

        # spectral wisps orbiting the beam
        for wi in range(4):
            angle = progress * 6 + wi * 1.57
            wr = int(10 + progress * 12 * strength)
            wx = cx + int(direction.x * beam_len * 0.5 + math.cos(angle) * wr)
            wy = cy + int(direction.y * beam_len * 0.5 + math.sin(angle) * wr)
            ws = max(1, int(3 * (1 - progress)))
            _aa_circle(screen, (160, 100, 220, int(180 * (1 - progress))), (wx, wy), ws)

    # drain effect at target (pulsing purple ring)
    if progress > 0.3:
        dp = (progress - 0.3) / 0.7
        ring_r = int((8 + 18 * dp) * strength)
        _aa_circle(screen, (180, 100, 255, int(200 * (1 - dp))), (target_x, target_y), ring_r, 2)
        _aa_circle(screen, (140, 60, 200, int(160 * (1 - dp))), (target_x, target_y), ring_r // 2, 1)

    # life essence particles flowing back to caster
    if progress > 0.4:
        lp = (progress - 0.4) / 0.6
        for i in range(6):
            pp = (lp - i * 0.06) * 1.3
            if pp < 0 or pp > 1:
                continue
            dist = (1 - pp) * beam_len
            px = cx + int(direction.x * dist)
            py = cy + int(direction.y * dist)
            _aa_circle(screen, (100, 255, 120, int(200 * (1 - pp))), (px, py), max(1, int(2 * (1 - pp))))


# ============================================================
# TITAN STOMP — ground-shattering AoE slam
# ============================================================
def _draw_titan_stomp(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 99)

    # Phase A: heavy wind-up (0 .. 0.3)
    if progress < 0.35:
        p = progress / 0.35
        # rising dust cloud
        for i in range(4):
            ang = rng.uniform(0, math.tau)
            d = 6 + p * 14
            dx = cx + int(math.cos(ang) * d)
            dy = cy - int(p * 16 * strength) + int(math.sin(ang) * d * 0.4)
            r = max(2, int(6 * (1 - p) * strength))
            _aa_circle(screen, (140, 130, 110, int(180 * (1 - p))), (dx, dy), r)

    # Phase B: impact shockwave (0.25 .. 1.0)
    if progress >= 0.25:
        p = (progress - 0.25) / 0.75

        # expanding ground shockwave rings
        for i in range(3):
            ri_p = max(0.0, min(1.0, p - i * 0.15))
            if ri_p <= 0:
                continue
            r = int((30 + 130 * ri_p) * strength)
            a = int(220 * (1 - ri_p))
            _ground_shockwave(screen, cx, cy + int(20 * strength), r,
                              (140, 130, 110, a), (180, 170, 150, a // 4))
            # inner ring highlight
            if r > 10:
                _ground_shockwave(screen, cx, cy + int(20 * strength), r - 4,
                                  (200, 190, 170, int(a * 0.6)))

        # central impact flash
        flash_p = _curve(p, 0.12)
        if flash_p > 0:
            flash_r = int(25 * flash_p * strength)
            _aa_circle(screen, (220, 210, 180, int(200 * flash_p)), (cx, cy + int(16 * strength)), flash_r)
            _aa_circle(screen, (255, 240, 200, int(220 * flash_p)), (cx, cy + int(16 * strength)), flash_r // 2)

        # radiating crack lines
        crack_p = max(0.0, min(1.0, (progress - 0.28) / 0.5))
        if crack_p > 0:
            for i in range(10):
                ang = i * math.tau / 10 + rng.uniform(-0.12, 0.12)
                rr = int((18 + 100 * crack_p) * strength)
                ex = cx + int(math.cos(ang) * rr)
                ey = cy + int(22 * strength) + int(math.sin(ang) * rr * 0.45)
                _aa_line(screen, (100, 90, 75, int(200 * (1 - crack_p))),
                         (cx, cy + int(22 * strength)), (ex, ey),
                         max(1, int(3 * (1 - crack_p))))
                _aa_line(screen, (180, 170, 150, int(150 * (1 - crack_p))),
                         (cx, cy + int(22 * strength)), (ex, ey), 1)

        # debris chunks flying
        for i in range(12):
            cp = (p - i * 0.03) * 1.4
            if cp < 0 or cp > 1:
                continue
            ang = rng.uniform(0, math.tau)
            dist = 10 + cp * 70 * strength
            dx2 = cx + int(math.cos(ang) * dist)
            dy2 = cy + int(22 * strength) + int(math.sin(ang) * dist * 0.4) - int(cp * 25)
            chunk_r = max(1, int(3 * (1 - cp)))
            col = rng.choice([(140, 130, 110), (110, 100, 88), (180, 170, 150)])
            _aa_circle(screen, (*col, int(220 * (1 - cp))), (dx2, dy2), chunk_r)

        # dust cloud rising
        if progress > 0.4:
            sp = (progress - 0.4) / 0.6
            for i in range(5):
                off = (i - 2) * 10
                sy_off = cy - int(sp * 22 * strength) + int(6 * math.sin(sp * 5 + i))
                _aa_circle(screen, (150, 140, 120, int(100 * (1 - sp))),
                           (cx + off, sy_off + int(12 * strength)),
                           int((5 + sp * 10) * strength))


# ============================================================
# CRYOMANCER NOVA — close-range frost explosion + ice shards
# ============================================================
def _draw_cryomancer_nova(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 110)

    # expanding frost nova rings
    for layer in range(4):
        lf = 1.0 - layer * 0.18
        r = int((15 + 55 * progress) * strength * lf)
        a = int(180 * (1 - progress) * lf)
        _aa_circle(screen, (140, 200, 255, a), (cx, cy), r, max(1, int(3 * lf)))
        if r > 8:
            _aa_circle(screen, (200, 240, 255, a // 2), (cx, cy), r - 4, max(1, int(2 * lf)))

    # inner bright core
    if progress < 0.5:
        cp = progress / 0.5
        core_r = int((4 + 12 * cp) * strength)
        _aa_circle(screen, (220, 245, 255, int(220 * (1 - cp))), (cx, cy), core_r)

    # ice crystal shards flying outward
    if progress > 0.15:
        ip = (progress - 0.15) / 0.85
        for i in range(8):
            angle = i * math.tau / 8 + rng.uniform(-0.15, 0.15)
            dist = (8 + ip * 55 * strength)
            ix = cx + int(math.cos(angle) * dist)
            iy = cy + int(math.sin(angle) * dist)
            shard_len = int(8 * (1 - ip) * strength)
            # crystal diamond shape
            tip = (ix + int(math.cos(angle) * shard_len), iy + int(math.sin(angle) * shard_len))
            back = (ix - int(math.cos(angle) * shard_len // 2), iy - int(math.sin(angle) * shard_len // 2))
            perp = (int(-math.sin(angle) * 3), int(math.cos(angle) * 3))
            a = int(220 * (1 - ip))
            _aa_polygon(screen, (160, 220, 255, a),
                        [(ix, iy), (tip[0] + perp[0], tip[1] + perp[1]), back])
            _aa_polygon(screen, (220, 245, 255, a),
                        [(ix, iy), (tip[0] - perp[0], tip[1] - perp[1]), back])
            # bright tip
            _aa_circle(screen, (255, 255, 255, a), tip, max(1, int(2 * (1 - ip))))

    # frost sparkles
    for i in range(10):
        sp = (progress - i * 0.04) * 1.3
        if sp < 0 or sp > 1:
            continue
        ang = rng.uniform(0, math.tau)
        d = 6 + sp * 50 * strength
        sx = cx + int(math.cos(ang) * d)
        sy = cy + int(math.sin(ang) * d)
        sz = max(1, int(3 * (1 - sp)))
        _aa_polygon(screen, (220, 250, 255, int(200 * (1 - sp))),
                    [(sx, sy - sz), (sx + sz, sy), (sx, sy + sz), (sx - sz, sy)])

    # cold mist at feet
    if progress > 0.3:
        mp = (progress - 0.3) / 0.7
        for i in range(4):
            off = (i - 1.5) * 10
            my = cy + int(18 * strength) - int(mp * 8)
            mr = int((6 + mp * 12) * strength)
            _aa_ellipse(screen, (200, 230, 255, int(100 * (1 - mp))),
                        (cx + off - mr // 2, my - mr // 4, mr, mr // 2))


# ============================================================
# SHADOWMANCER BLINK — teleport + shadow energy burst
# ============================================================
def _draw_shadowmancer_blink(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 120)

    # Phase A: shadow vortex forming (0 .. 0.35)
    if progress < 0.40:
        p = progress / 0.40
        # swirling shadow particles
        for i in range(8):
            angle = p * 4.0 + i * math.tau / 8
            r = int((20 - p * 10) * strength)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * r)
            _aa_circle(screen, (60, 20, 100, int(200 * (1 - p))), (sx, sy),
                       max(2, int(5 * (1 - p) * strength)))
        # central void
        void_r = int((4 + p * 12) * strength)
        _aa_circle(screen, (30, 10, 50, int(220 * (1 - p))), (cx, cy), void_r)

    # Phase B: blink flash (0.25 .. 0.65)
    if 0.25 <= progress < 0.70:
        p = (progress - 0.25) / 0.45
        # purple flash burst
        flash_r = int((25 + 40 * _curve(p, 0.3)) * strength)
        _aa_circle(screen, (160, 80, 220, int(200 * (1 - _curve(p, 0.3)))),
                   (cx, cy), flash_r)
        # shadow energy ring
        ring_r = int((15 + 35 * p) * strength)
        _impact_ring(screen, cx, cy, ring_r,
                     (120, 40, 180, int(220 * (1 - p))), width=3)

        # outward shadow bolts
        for i in range(6):
            angle = i * math.tau / 6 + rng.uniform(-0.12, 0.12)
            dist = 8 + p * 40 * strength
            bx = cx + int(math.cos(angle) * dist)
            by = cy + int(math.sin(angle) * dist)
            _aa_line(screen, (100, 40, 160, int(220 * (1 - p))),
                     (cx, cy), (bx, by), max(1, int(3 * (1 - p))))
            _aa_circle(screen, (180, 100, 240, int(200 * (1 - p))), (bx, by),
                       max(1, int(3 * (1 - p))))

    # Phase C: shadow trail dissipating (0.5 .. 1.0)
    if progress > 0.5:
        sp = (progress - 0.5) / 0.5
        # shadow particles fading away
        for i in range(10):
            fp = (sp - i * 0.05) * 1.3
            if fp < 0 or fp > 1:
                continue
            ang = rng.uniform(0, math.tau)
            d = 10 + fp * 55 * strength
            fx = cx + int(math.cos(ang) * d)
            fy = cy + int(math.sin(ang) * d)
            fs = max(1, int(4 * (1 - fp) * strength))
            _aa_circle(screen, (80, 30, 120, int(180 * (1 - fp))), (fx, fy), fs)
            # bright purple core
            _aa_circle(screen, (180, 100, 240, int(140 * (1 - fp))), (fx, fy), max(1, fs - 1))

    # residual shadow on ground
    if progress > 0.6:
        gp = (progress - 0.6) / 0.4
        _ground_shockwave(screen, cx, cy + int(18 * strength),
                          int((10 + 20 * gp) * strength),
                          (80, 30, 120, int(160 * (1 - gp))),
                          (40, 15, 60, int(80 * (1 - gp))))


# ============================================================
# REVENANT SLASH — cursed soul slash with green lifesteal particles
# ============================================================
def _draw_revenant_slash(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 130)
    fwd_angle_deg = math.degrees(math.atan2(direction.y, direction.x))

    # dark crescent slash
    sweep_deg = 150
    radius = int(44 * strength)
    _slash_arc(screen, cx, cy, fwd_angle_deg, sweep_deg, radius + 4, progress * 1.1,
               (30, 40, 35, int(220 * (1 - progress))), width=8, layers=2)
    _slash_arc(screen, cx, cy, fwd_angle_deg, sweep_deg, radius, progress * 1.1,
               (100, 200, 150, int(220 * (1 - progress))), width=5, layers=3)
    _slash_arc(screen, cx, cy, fwd_angle_deg, sweep_deg, radius - 3, progress * 1.1,
               (180, 255, 200, int(200 * (1 - progress))), width=2, layers=2)

    # green lifesteal particles flowing back to caster
    if progress > 0.3:
        lp = (progress - 0.3) / 0.7
        for i in range(8):
            pp = (lp - i * 0.05) * 1.3
            if pp < 0 or pp > 1:
                continue
            ang = rng.uniform(0, math.tau)
            d = 10 + pp * 40 * strength
            lx = cx + int(math.cos(ang) * d)
            ly = cy + int(math.sin(ang) * d) - int(pp * 10)
            _aa_circle(screen, (80, 255, 140, int(200 * (1 - pp))), (lx, ly), max(1, int(3 * (1 - pp))))

    # dark energy sparks
    for i in range(6):
        sp = (progress - i * 0.04) * 1.3
        if sp < 0 or sp > 1:
            continue
        ang = rng.uniform(0, math.tau)
        d = 8 + sp * 35 * strength
        sx = cx + int(math.cos(ang) * d)
        sy = cy + int(math.sin(ang) * d)
        _aa_circle(screen, (60, 180, 120, int(220 * (1 - sp))), (sx, sy), max(1, int(2 * (1 - sp))))


# ============================================================
# REVENANT UNDYING — soul surge when undying will triggers
# ============================================================
def _draw_revenant_undying(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 131)

    # soul energy burst outward
    for layer in range(4):
        lf = 1.0 - layer * 0.2
        r = int((20 + 50 * progress) * strength * lf)
        a = int(200 * (1 - progress) * lf)
        _aa_circle(screen, (80, 220, 160, a), (cx, cy), r, max(1, int(3 * lf)))

    # bright soul pulse
    flash_p = _curve(progress, 0.2)
    if flash_p > 0:
        _aa_circle(screen, (140, 255, 200, int(220 * flash_p)),
                   (cx, cy), int(20 * flash_p * strength))

    # soul particles spiraling inward (healing)
    for i in range(10):
        angle = progress * 6 + i * 0.63
        r = int((40 - progress * 30) * strength)
        sx = cx + int(math.cos(angle) * r)
        sy = cy + int(math.sin(angle) * r)
        _aa_circle(screen, (100, 255, 180, int(200 * (1 - progress))), (sx, sy), max(1, int(3 * (1 - progress))))

    # rune ring
    rune_r = int((15 + 25 * progress) * strength)
    _impact_ring(screen, cx, cy, rune_r,
                 (80, 200, 150, int(220 * (1 - progress))), width=2)


# ============================================================
# MOLTEN NOVA — fire explosion with lava splatter
# ============================================================
def _draw_molten_nova(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 140)

    # expanding fire rings
    for layer in range(3):
        lf = 1.0 - layer * 0.2
        r = int((15 + 55 * progress) * strength * lf)
        a = int(200 * (1 - progress) * lf)
        _aa_circle(screen, (255, 140, 30, a), (cx, cy), r, max(1, int(3 * lf)))
        if r > 8:
            _aa_circle(screen, (255, 200, 80, a // 2), (cx, cy), r - 4, max(1, int(2 * lf)))

    # inner bright core
    if progress < 0.4:
        cp = progress / 0.4
        core_r = int((5 + 14 * cp) * strength)
        _aa_circle(screen, (255, 230, 140, int(220 * (1 - cp))), (cx, cy), core_r)
        _aa_circle(screen, (255, 255, 220, int(200 * (1 - cp))), (cx, cy), core_r // 2)

    # lava splatter
    if progress > 0.15:
        lp = (progress - 0.15) / 0.85
        for i in range(10):
            sp = (lp - i * 0.04) * 1.3
            if sp < 0 or sp > 1:
                continue
            ang = rng.uniform(0, math.tau)
            d = 8 + sp * 50 * strength
            lx = cx + int(math.cos(ang) * d)
            ly = cy + int(math.sin(ang) * d)
            lr = max(1, int(4 * (1 - sp)))
            col = rng.choice([(255, 140, 30), (255, 100, 20), (255, 180, 60)])
            _aa_circle(screen, (*col, int(220 * (1 - sp))), (lx, ly), lr)

    # embers rising
    for i in range(8):
        ep = (progress - i * 0.04) * 1.2
        if ep < 0 or ep > 1:
            continue
        ang = rng.uniform(-math.pi, 0)
        dist = 10 + ep * 40 * strength
        ex = cx + int(math.cos(ang) * dist)
        ey = cy + int(math.sin(ang) * dist) - int(ep * 20)
        _aa_circle(screen, (255, 180, 60, int(200 * (1 - ep))), (ex, ey), max(1, int(2 * (1 - ep))))


# ============================================================
# MOLTEN SLAM — charge impact with ground裂 crack lines
# ============================================================
def _draw_molten_slam(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 141)
    fwd_angle_deg = math.degrees(math.atan2(direction.y, direction.x))

    # bright impact flash
    flash_p = _curve(progress, 0.15)
    if flash_p > 0:
        _aa_circle(screen, (255, 220, 140, int(220 * flash_p)),
                   (cx, cy), int(22 * flash_p * strength))
        _aa_circle(screen, (255, 140, 30, int(200 * flash_p)),
                   (cx, cy), int(14 * flash_p * strength))

    # forward sweep arc
    sweep_deg = 120
    radius = int(42 * strength)
    _slash_arc(screen, cx, cy, fwd_angle_deg, sweep_deg, radius, progress * 1.15,
               (255, 120, 30, int(220 * (1 - progress))), width=6, layers=3)
    _slash_arc(screen, cx, cy, fwd_angle_deg, sweep_deg, radius - 3, progress * 1.15,
               (255, 200, 80, int(200 * (1 - progress))), width=2, layers=2)

    # expanding fire ring
    ring_r = int((10 + 40 * progress) * strength)
    _impact_ring(screen, cx, cy, ring_r,
                 (255, 140, 30, int(220 * (1 - progress))), width=3)

    # ground crack lines
    crack_p = max(0.0, min(1.0, (progress - 0.2) / 0.6))
    if crack_p > 0:
        for i in range(8):
            ang = i * math.tau / 8 + rng.uniform(-0.12, 0.12)
            rr = int((15 + 60 * crack_p) * strength)
            ex = cx + int(math.cos(ang) * rr)
            ey = cy + int(math.sin(ang) * rr * 0.45)
            _aa_line(screen, (255, 160, 50, int(200 * (1 - crack_p))),
                     (cx, cy), (ex, ey), max(1, int(2 * (1 - crack_p))))

    # lava droplets
    for i in range(6):
        dp = (progress - i * 0.05) * 1.2
        if dp < 0 or dp > 1:
            continue
        ang = rng.uniform(0, math.tau)
        d = 10 + dp * 45 * strength
        dx = cx + int(math.cos(ang) * d)
        dy = cy + int(math.sin(ang) * d)
        _aa_circle(screen, (255, 100, 20, int(220 * (1 - dp))), (dx, dy), max(1, int(3 * (1 - dp))))


# ============================================================
# STORMCALLER FIELD — static electricity burst
# ============================================================
def _draw_stormcaller_field(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 150)

    # expanding static rings
    for layer in range(3):
        lf = 1.0 - layer * 0.2
        r = int((15 + 50 * progress) * strength * lf)
        a = int(180 * (1 - progress) * lf)
        _aa_circle(screen, (100, 180, 255, a), (cx, cy), r, max(1, int(3 * lf)))

    # lightning bolts branching outward
    bolt_p = max(0.0, min(1.0, progress * 1.2))
    for i in range(6):
        angle = i * math.tau / 6 + rng.uniform(-0.15, 0.15)
        length = int((15 + 40 * bolt_p) * strength)
        # jagged lightning line
        pts = [(cx, cy)]
        bx, by = cx, cy
        segments = 4
        for seg in range(segments):
            seg_len = length // segments
            bx += int(math.cos(angle) * seg_len + rng.uniform(-5, 5))
            by += int(math.sin(angle) * seg_len + rng.uniform(-5, 5))
            pts.append((bx, by))
        a = int(220 * (1 - bolt_p))
        for j in range(len(pts) - 1):
            _aa_line(screen, (140, 200, 255, a), pts[j], pts[j + 1], 2)
            _aa_line(screen, (220, 240, 255, a), pts[j], pts[j + 1], 1)
        # bright tip
        _aa_circle(screen, (200, 230, 255, a), pts[-1], max(1, int(3 * (1 - bolt_p))))

    # central flash
    flash_p = _curve(progress, 0.15)
    if flash_p > 0:
        _aa_circle(screen, (200, 230, 255, int(200 * flash_p)),
                   (cx, cy), int(15 * flash_p * strength))

    # electric sparks
    for i in range(8):
        sp = (progress - i * 0.03) * 1.3
        if sp < 0 or sp > 1:
            continue
        ang = rng.uniform(0, math.tau)
        d = 8 + sp * 40 * strength
        sx = cx + int(math.cos(ang) * d)
        sy = cy + int(math.sin(ang) * d)
        _aa_circle(screen, (180, 220, 255, int(220 * (1 - sp))), (sx, sy), max(1, int(2 * (1 - sp))))


# ============================================================
# PLAGUEBEARER NOVA — toxic pestilence explosion
# ============================================================
def _draw_plaguebearer_nova(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 160)

    # expanding toxic rings
    for layer in range(3):
        lf = 1.0 - layer * 0.2
        r = int((15 + 55 * progress) * strength * lf)
        a = int(180 * (1 - progress) * lf)
        _aa_circle(screen, (120, 180, 50, a), (cx, cy), r, max(1, int(3 * lf)))
        if r > 8:
            _aa_circle(screen, (160, 220, 80, a // 2), (cx, cy), r - 4, max(1, int(2 * lf)))

    # inner toxic core
    if progress < 0.4:
        cp = progress / 0.4
        core_r = int((5 + 12 * cp) * strength)
        _aa_circle(screen, (160, 220, 80, int(200 * (1 - cp))), (cx, cy), core_r)

    # poison cloud puffs
    if progress > 0.15:
        cp = (progress - 0.15) / 0.85
        for i in range(8):
            pp = (cp - i * 0.04) * 1.3
            if pp < 0 or pp > 1:
                continue
            ang = rng.uniform(0, math.tau)
            d = 10 + pp * 50 * strength
            px = cx + int(math.cos(ang) * d)
            py = cy + int(math.sin(ang) * d)
            pr = max(2, int(8 * (1 - pp)))
            col = rng.choice([(120, 180, 50), (100, 160, 40), (140, 200, 60)])
            _aa_circle(screen, (*col, int(180 * (1 - pp))), (px, py), pr)

    # toxic drip particles
    for i in range(6):
        dp = (progress - i * 0.05) * 1.2
        if dp < 0 or dp > 1:
            continue
        ang = rng.uniform(0, math.tau)
        d = 8 + dp * 40 * strength
        dx = cx + int(math.cos(ang) * d)
        dy = cy + int(math.sin(ang) * d) + int(dp * 15)
        _aa_circle(screen, (140, 200, 60, int(200 * (1 - dp))), (dx, dy), max(1, int(3 * (1 - dp))))

    # sickly green mist at ground
    if progress > 0.3:
        mp = (progress - 0.3) / 0.7
        for i in range(4):
            off = (i - 1.5) * 10
            my = cy + int(16 * strength) - int(mp * 6)
            mr = int((6 + mp * 14) * strength)
            _aa_ellipse(screen, (120, 180, 50, int(90 * (1 - mp))),
                        (cx + off - mr // 2, my - mr // 4, mr, mr // 2))
# ============================================================
# CASTER BURST — generic energy burst for projectile-based attacks
# ============================================================
def _draw_caster_burst(screen, cx, cy, direction, progress, strength, enemy):
    rng = _seeded(enemy, 170)

    # expanding energy rings
    for layer in range(3):
        lf = 1.0 - layer * 0.2
        r = int((10 + 40 * progress) * strength * lf)
        a = int(200 * (1 - progress) * lf)
        col = rng.choice([
            (120, 180, 255),   # ice / lightning
            (180, 120, 255),   # shadow
            (120, 200, 80),    # poison
            (255, 180, 60),    # generic
        ])
        _aa_circle(screen, (*col, a), (cx, cy), r, max(1, int(2 * lf)))
    # bright inner flash
    if progress < 0.4:
        p = progress / 0.4
        _aa_circle(screen, (255, 255, 255, int(220 * (1 - p))),
                   (cx, cy), int(8 * (1 - p) * strength) + 2)
    # outward spark particles
    if progress > 0.1:
        sp = (progress - 0.1) / 0.9
        for i in range(8):
            pp = (sp - i * 0.04) * 1.3
            if pp < 0 or pp > 1:
                continue
            ang = rng.uniform(0, math.tau)
            d = 6 + pp * 35 * strength
            sx = cx + int(math.cos(ang) * d)
            sy = cy + int(math.sin(ang) * d)
            _aa_circle(screen, (255, 255, 255, int(200 * (1 - pp))),
                       (sx, sy), max(1, int(2 * (1 - pp))))


# ============================================================
def _draw_generic_strike(screen, cx, cy, direction, progress, strength, enemy):
    fwd_angle_deg = math.degrees(math.atan2(direction.y, direction.x))
    sweep_deg = 130
    radius = int(42 * strength)
    _slash_arc(screen, cx, cy, fwd_angle_deg, sweep_deg, radius, progress * 1.1,
               (220, 230, 240, int(220 * (1 - progress))), width=6, layers=3)
    _slash_arc(screen, cx, cy, fwd_angle_deg, sweep_deg, radius - 4, progress * 1.1,
               (255, 255, 255, int(200 * (1 - progress))), width=2, layers=2)
    # impact spark
    if progress < 0.5:
        p = progress / 0.5
        impact_x = cx + int(direction.x * 30 * strength)
        impact_y = cy + int(direction.y * 30 * strength)
        _aa_circle(screen, (255, 255, 220, int(220 * (1 - p))),
                   (impact_x, impact_y), int(8 * (1 - p) * strength) + 2)


_DISPATCH = {
    "brute_slam": _draw_brute_slam,
    "venomous_strike": _draw_venomous_strike,
    "trickster_strike": _draw_trickster_strike,
    "stalker_slash": _draw_stalker_slash,
    "skirmisher_claw": _draw_skirmisher_claw,
    "guardian_smash": _draw_guardian_smash,
    "arcanist_burst": _draw_arcanist_burst,
    "bomber_strike": _draw_bomber_strike,
    "phantom_drain": _draw_phantom_drain,
    "titan_stomp": _draw_titan_stomp,
    "cryomancer_nova": _draw_cryomancer_nova,
    "shadowmancer_blink": _draw_shadowmancer_blink,
    "revenant_slash": _draw_revenant_slash,
    "revenant_undying": _draw_revenant_undying,
    "molten_nova": _draw_molten_nova,
    "molten_slam": _draw_molten_slam,
    "stormcaller_field": _draw_stormcaller_field,
    "plaguebearer_nova": _draw_plaguebearer_nova,
    "caster_burst": _draw_caster_burst,
    "generic_strike": _draw_generic_strike,
}
