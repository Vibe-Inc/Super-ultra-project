import math
import random
import time

import pygame
import src.config as cfg
from src.ui.widgets import Button


class WorldScaleMenu:
    DARK_BG = (8, 6, 20)
    PANEL_TOP = (18, 14, 45)
    PANEL_BOT = (8, 6, 22)
    ACCENT_BLUE = (80, 140, 255)
    ACCENT_GOLD = (255, 215, 0)
    ACCENT_GREEN = (100, 220, 140)
    TEXT_MAIN = (220, 220, 240)
    TEXT_DIM = (140, 140, 170)
    TEXT_GOLD = (255, 215, 0)
    CARD_BG = (20, 18, 45)

    def __init__(self, app, world_scale, on_close):
        self.app = app
        self.world_scale = world_scale
        self.on_close = on_close
        self.visible = False
        self._open_time = 0.0

        s = cfg.ui_scale()
        self.font_title = cfg.get_font(max(18, int(44 * s)))
        self.font_section = cfg.get_font(max(14, int(26 * s)))
        self.font_body = cfg.get_font(max(13, int(23 * s)))
        self.font_small = cfg.get_font(max(10, int(19 * s)))
        self.font_level = cfg.get_font(max(20, int(72 * s)))

        self._last_known_level = 0
        self._ever_opened = False
        self._unlock_history = []
        self._latest_unlock_batch = None

        self.panel_w = 680
        self.panel_h = 840

        self.editor_mode = False
        self.editor_input = ""

        self._particles = []
        self._stars = []
        for _ in range(50):
            self._stars.append({
                'x': random.uniform(0, self.panel_w),
                'y': random.uniform(0, self.panel_h),
                'phase': random.uniform(0, math.tau),
                'speed': random.uniform(0.3, 1.5),
                'size': random.uniform(0.5, 1.8),
            })

        self.editor_button = Button(
            pygame.Rect(0, 0, 140, 34),
            "Editor", (60, 60, 100), (90, 90, 150),
            self.font_small, (200, 200, 230), 6, self._toggle_editor,
        )
        self.apply_button = Button(
            pygame.Rect(0, 0, 100, 30),
            "Apply", (40, 80, 40), (60, 140, 60),
            self.font_small, (200, 200, 230), 5, self._apply_editor,
        )

    def _compute_new_unlocks(self, old_level, new_level):
        ability_unlocks = []
        for lvl, name in [
            (5, "Charged Attack"), (10, "Block"), (15, "Parry"),
            (35, "Shockwave"), (45, "Fast Attack"), (55, "Execute"),
        ]:
            if old_level < lvl <= new_level:
                ability_unlocks.append((lvl, name))

        tag_unlocks = []
        for tag_lvl, tag_name, tag_desc in [
            (15, "Aggressive Enemies", "+25% attack speed"),
            (35, "Empowered Enemies", "Extra projectiles, lifesteal"),
            (55, "Elite Enemies", "Unique per-enemy abilities"),
        ]:
            if old_level < tag_lvl <= new_level:
                tag_unlocks.append((tag_lvl, tag_name, tag_desc))
        return ability_unlocks, tag_unlocks

    def toggle(self):
        self.visible = not self.visible
        if self.visible:
            ws = self.world_scale
            if not self._ever_opened:
                self._ever_opened = True
            elif ws.level > self._last_known_level:
                abilities, tags = self._compute_new_unlocks(self._last_known_level, ws.level)
                for lvl, name in abilities:
                    self._unlock_history.append((lvl, name))
                if abilities or tags:
                    self._latest_unlock_batch = (abilities, tags)
            self._last_known_level = ws.level
            self.editor_mode = False
            self.editor_input = ""
            self._open_time = time.time()
            self._particles = []

    def _toggle_editor(self):
        self.editor_mode = not self.editor_mode
        self.editor_input = str(self.world_scale.level)

    def _apply_editor(self):
        try:
            lvl = int(self.editor_input.strip())
            self.world_scale.set_level(lvl)
        except ValueError:
            pass
        self.editor_mode = False
        if self.on_close:
            self.on_close()

    def _add_particles(self, px, py, count=4):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(30, 80)
            self._particles.append({
                'x': px + random.uniform(-8, 8),
                'y': py + random.uniform(-8, 8),
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed - 40,
                'life': random.uniform(0.5, 1.0),
                'max_life': random.uniform(0.5, 1.0),
                'size': random.uniform(1.5, 3.0),
                'color': random.choice([
                    (100, 200, 255), (180, 140, 255),
                    (255, 215, 0), (255, 120, 120),
                ]),
            })

    def _update_particles(self, dt):
        alive = []
        for p in self._particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += 100 * dt
            p['life'] -= dt
            if p['life'] > 0:
                alive.append(p)
        self._particles = alive

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_j, pygame.K_ESCAPE):
                self.visible = False
                if self.on_close:
                    self.on_close()
                return True
            if self.editor_mode:
                if event.key == pygame.K_RETURN:
                    self._apply_editor()
                    return True
                if event.key == pygame.K_BACKSPACE:
                    self.editor_input = self.editor_input[:-1]
                elif event.unicode.isdigit():
                    self.editor_input += event.unicode
                elif event.unicode == '-' and '-' not in self.editor_input:
                    self.editor_input = '-' + self.editor_input
                return True
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if self.editor_mode and self.apply_button.rect and self.apply_button.rect.collidepoint(mx, my):
                self.apply_button.on_click()
                return True
            if not self.editor_mode and self.editor_button.rect and self.editor_button.rect.collidepoint(mx, my):
                self.editor_button.on_click()
                return True
        return True

    def draw(self, screen):
        if not self.visible:
            return
        dt = 1.0 / 60.0
        now = time.time()
        t_ms = pygame.time.get_ticks()
        elapsed = now - self._open_time
        anim = min(1.0, elapsed * 3.0)
        ease = 1.0 - (1.0 - anim) ** 3

        self._update_particles(dt)

        sw, sh = screen.get_size()
        px = sw // 2 - self.panel_w // 2
        py = max(8, sh // 2 - self.panel_h // 2)
        off = int((1.0 - ease) * 50)
        dx, dy = px, py + off

        # ── backdrop ──────────────────────────────────────────
        overlay = pygame.Surface((sw, sh))
        overlay.set_alpha(int(170 * ease))
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        # ── panel ─────────────────────────────────────────────
        panel = pygame.Surface((self.panel_w, self.panel_h))
        for i in range(self.panel_h):
            t = i / self.panel_h
            r = int(self.PANEL_TOP[0] + (self.PANEL_BOT[0] - self.PANEL_TOP[0]) * t)
            g = int(self.PANEL_TOP[1] + (self.PANEL_BOT[1] - self.PANEL_TOP[1]) * t)
            b = int(self.PANEL_TOP[2] + (self.PANEL_BOT[2] - self.PANEL_TOP[2]) * t)
            pygame.draw.line(panel, (r, g, b), (0, i), (self.panel_w, i))
        # soft border
        for i in range(2):
            c = (40 + i * 20, 40 + i * 20, 100 + i * 30)
            pygame.draw.rect(panel, c, (i, i, self.panel_w - i * 2, self.panel_h - i * 2), 1)
        panel.set_alpha(int(240 * ease))
        screen.blit(panel, (dx, dy))

        # ── glow border ──────────────────────────────────────
        for w in range(3):
            a = int(50 + 30 * math.sin(now * 1.5 - w * 0.8))
            col = (60 + w * 30, 50 + w * 20, 140 + w * 40)
            s = pygame.Surface((self.panel_w + w * 4, self.panel_h + w * 4))
            s.set_colorkey((0, 0, 0))
            pygame.draw.rect(s, col, (w, w, self.panel_w + w * 2, self.panel_h + w * 2), 1)
            s.set_alpha(max(0, a))
            screen.blit(s, (dx - w * 2 - 1, dy - w * 2 - 1))

        # ── stars ─────────────────────────────────────────────
        for s in self._stars:
            tw = 0.3 + 0.7 * math.sin(now * s['speed'] + s['phase'])
            a = int(120 * tw * ease)
            sz = max(1, int(s['size'] * tw))
            if a > 3:
                surf = pygame.Surface((sz * 2, sz * 2))
                surf.set_colorkey((0, 0, 0))
                pygame.draw.circle(surf, (180, 200, 255), (sz, sz), sz)
                surf.set_alpha(a)
                screen.blit(surf, (dx + int(s['x']) - sz, dy + int(s['y']) - sz))

        ws = self.world_scale
        cx = dx + self.panel_w // 2

        # ── title ─────────────────────────────────────────────
        title = self.font_title.render("WORLD SCALE", True, self.TEXT_MAIN)
        tr = title.get_rect(centerx=cx, top=dy + 16)
        # title underline glow
        glow_col = (80, 60, 180, int(80 + 40 * math.sin(now * 2)))
        for ox in (-2, 0, 2):
            pygame.draw.line(screen, (60, 40, 150),
                             (cx - 120 + ox, tr.bottom + 6),
                             (cx + 120 + ox, tr.bottom + 6), 2)
        screen.blit(title, tr)

        # ── editor button ─────────────────────────────────────
        eb_x = dx + self.panel_w - 165
        eb_y = dy + 14
        self.editor_button.rect = pygame.Rect(eb_x, eb_y, 140, 34)
        self.editor_button.draw(screen)

        # ── new unlocks ───────────────────────────────────────
        lvl_y = tr.bottom + 30
        if self._latest_unlock_batch:
            abilities, tags = self._latest_unlock_batch
            lvl_y += 4
            hdr = self.font_section.render("NEW UNLOCKS", True, self.ACCENT_GOLD)
            screen.blit(hdr, (dx + 30, lvl_y))
            lvl_y += hdr.get_height() + 6
            for lvl, name in abilities:
                txt = self.font_body.render(f"  + Lv.{lvl}  {name}", True, (255, 255, 200))
                screen.blit(txt, (dx + 30, lvl_y))
                lvl_y += 24
            for _lvl, tname, tdesc in tags:
                txt = self.font_body.render(f"  + {tname}  —  {tdesc}", True, (255, 210, 100))
                screen.blit(txt, (dx + 30, lvl_y))
                lvl_y += 24
            lvl_y += 4
            pygame.draw.line(screen, (70, 60, 40),
                             (dx + 60, lvl_y), (dx + self.panel_w - 60, lvl_y), 1)
            lvl_y += 14

        # ── level + ring ──────────────────────────────────────
        lvl_str = str(ws.level)
        lvl_col = self.ACCENT_GOLD if ws.level >= 55 else self.TEXT_MAIN
        lvl_surf = self.font_level.render(lvl_str, True, lvl_col)
        lvl_glow = self.font_level.render(lvl_str, True, (40, 40, 100))

        ring_center = (dx + 90, lvl_y + lvl_surf.get_height() // 2)
        ring_r = max(lvl_surf.get_width(), lvl_surf.get_height()) // 2 + 14

        needed = ws.xp_for_next()
        if needed > 0:
            prog = ws.progress()
        else:
            prog = 1.0

        # ring bg
        pygame.draw.circle(screen, (25, 22, 60), ring_center, ring_r, 3)
        # ring fill
        if prog > 0.005:
            ang = prog * math.tau
            for rw in range(3):
                rr = ring_r + rw * 2
                col = (80 + rw * 25, 120 + rw * 20, 255 - rw * 20)
                if prog >= 1.0:
                    col = (255, 215 - rw * 20, 0 + rw * 30)
                pygame.draw.arc(screen, col,
                                (ring_center[0] - rr, ring_center[1] - rr, rr * 2, rr * 2),
                                -math.pi * 0.5, -math.pi * 0.5 + ang, max(1, 3 - rw))

        # level number
        for ox, oy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            screen.blit(lvl_glow, (ring_center[0] - lvl_surf.get_width() // 2 + ox,
                                   ring_center[1] - lvl_surf.get_height() // 2 + oy))
        screen.blit(lvl_surf, (ring_center[0] - lvl_surf.get_width() // 2,
                               ring_center[1] - lvl_surf.get_height() // 2))
        # /60 label
        max_lab = self.font_small.render("/ 60", True, self.TEXT_DIM)
        screen.blit(max_lab, (ring_center[0] + lvl_surf.get_width() // 2 + 6,
                              ring_center[1] - max_lab.get_height() // 2 + 4))

        # level text beside
        lvl_label = self.font_section.render("LEVEL", True, self.TEXT_DIM)
        screen.blit(lvl_label, (ring_center[0] + lvl_surf.get_width() // 2 + max_lab.get_width() + 12,
                                ring_center[1] - lvl_label.get_height() // 2 - 4))

        # ── xp bar ────────────────────────────────────────────
        bar_y = ring_center[1] + ring_r + 20
        bar_x = dx + 30
        bar_w = self.panel_w - 60
        bar_h = 26

        if needed > 0:
            xp_text = self.font_small.render(f"XP: {ws.xp} / {needed}", True, (180, 180, 220))
        else:
            xp_text = self.font_small.render("MAX LEVEL — All upgrades active", True, self.ACCENT_GOLD)

        screen.blit(xp_text, (bar_x, bar_y - 16))

        # bar bg
        pygame.draw.rect(screen, (12, 10, 30), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, (25, 22, 50), (bar_x + 1, bar_y + 1, bar_w - 2, bar_h - 2))

        if prog > 0:
            fw = max(2, int((bar_w - 4) * prog))
            for i in range(fw):
                t = i / max(1, fw)
                if prog >= 1.0:
                    r = int(255 - t * 20)
                    g = int(215 - t * 15)
                    b = int(0 + t * 15)
                else:
                    r = int(50 + t * 70)
                    g = int(130 + t * 80)
                    b = int(230 - t * 40)
                pygame.draw.line(screen, (r, g, b),
                                 (bar_x + 2 + i, bar_y + 2),
                                 (bar_x + 2 + i, bar_y + bar_h - 3), 1)
            # shine
            sx = bar_x + 2 + int((t_ms * 0.04) % (bar_w + 60)) - 30
            for i in range(sx, min(sx + 30, bar_x + 2 + fw)):
                a = max(0, 70 - abs(i - sx) * 3)
                if a > 0:
                    s = pygame.Surface((1, bar_h - 3))
                    s.set_alpha(a)
                    s.fill((255, 255, 255))
                    screen.blit(s, (i, bar_y + 2))

        pygame.draw.rect(screen, (50, 50, 90), (bar_x, bar_y, bar_w, bar_h), 1)

        # ── divider helper ────────────────────────────────────
        def div(y):
            pygame.draw.line(screen, (40, 38, 70),
                             (dx + 50, y), (dx + self.panel_w - 50, y))

        def section_hdr(text, y, color=None):
            surf = self.font_section.render(text, True, color or self.TEXT_MAIN)
            screen.blit(surf, (dx + 30, y))
            return y + surf.get_height() + 4

        # ── abilities ─────────────────────────────────────────
        ay = bar_y + bar_h + 12
        div(ay)
        ay += 6
        ay = section_hdr("UNLOCKED ABILITIES", ay, (180, 200, 255))

        if self._unlock_history:
            for lvl, name in self._unlock_history:
                badge = self.font_small.render(f"Lv.{lvl}", True, (140, 200, 255))
                screen.blit(badge, (dx + 32, ay + 1))
                dot_x = dx + 28
                pygame.draw.circle(screen, (100, 180, 255), (dot_x + 4, ay + 7), 3)
                txt = self.font_body.render(name, True, (200, 240, 200))
                screen.blit(txt, (dx + 64, ay))
                ay += 28
        else:
            txt = self.font_small.render("No abilities unlocked yet", True, self.TEXT_DIM)
            screen.blit(txt, (dx + 34, ay))
            ay += 24

        # ── enemy tags ────────────────────────────────────────
        tags = ws.get_milestone_tags()
        if tags:
            ay += 2
            div(ay)
            ay += 6
            ay = section_hdr("ENEMY BONUSES", ay, (255, 220, 140))
            for tag in tags:
                colors = {
                    'aggressive': ((200, 60, 60), "Aggressive"),
                    'empowered': ((200, 100, 200), "Empowered"),
                    'elite': ((255, 180, 50), "Elite"),
                }
                tc, tlabel = colors.get(tag, ((180, 180, 180), tag))
                desc = {
                    'aggressive': '+25% attack speed',
                    'empowered': 'Extra projectiles, lifesteal',
                    'elite': 'Unique per-enemy abilities',
                }.get(tag, tag)
                pygame.draw.circle(screen, tc, (dx + 34, ay + 8), 4)
                name_surf = self.font_body.render(tlabel, True, tc)
                screen.blit(name_surf, (dx + 44, ay + 1))
                desc_surf = self.font_small.render(desc, True, self.TEXT_DIM)
                screen.blit(desc_surf, (dx + 140, ay + 2))
                ay += 28

        # ── player bonuses ────────────────────────────────────
        ay += 2
        div(ay)
        ay += 6
        ay = section_hdr("PLAYER BONUSES", ay, (160, 220, 180))
        t = min(1.0, ws.level / 55.0)
        bonus_items = [
            ("Stamina", f"+{int(t * 60)} Max", t > 0.01),
            ("Cost", f"x{1.0 - t * 0.5:.1f}", t > 0.01),
            ("Fast Stun", f"+{t * 0.3:.1f}s", t > 0.01),
            ("Wave Range", f"x{1.0 + t * 1.5:.1f}", t > 0.01),
            ("Wave Dmg", f"x{1.0 + t * 3.0:.1f}", t > 0.01),
            ("Parry", f"+{int(t * 150)}ms", t > 0.01),
            ("Block", f"{60 + t * 15:.0f}%", t > 0.01),
        ]
        # grid: 2 columns
        col_w = (self.panel_w - 80) // 2
        for idx, (label, val, active) in enumerate(bonus_items):
            col = idx % 2
            row = idx // 2
            bx = dx + 30 + col * (col_w + 10)
            by = ay + row * 24
            color = (180, 220, 180) if active and ws.level > 0 else (90, 90, 100)
            lbl = self.font_small.render(label, True, color)
            v = self.font_small.render(val, True, (200, 200, 220) if active else (100, 100, 110))
            screen.blit(lbl, (bx, by))
            screen.blit(v, (bx + 120, by))
        ay += ((len(bonus_items) + 1) // 2) * 24 + 8

        # ── enemy stats ───────────────────────────────────────
        div(ay)
        ay += 8
        hp = ws.enemy_hp_mult()
        dmg = ws.enemy_damage_mult()
        spd = ws.enemy_speed_mult()
        stats = [
            (f"HP x{hp:.1f}", (200, 80, 80)),
            (f"DMG x{dmg:.1f}", (200, 120, 80)),
            (f"SPD x{spd:.1f}", (200, 160, 80)),
        ]
        stat_w = (self.panel_w - 80) // 3
        for i, (text, color) in enumerate(stats):
            sx = dx + 30 + i * (stat_w + 10)
            surf = self.font_small.render(text, True, color)
            screen.blit(surf, (sx, ay))
        ay += 30
        div(ay)

        # ── editor mode ───────────────────────────────────────
        if self.editor_mode:
            inp_rect = pygame.Rect(eb_x, eb_y + 42, 140, 30)
            pygame.draw.rect(screen, (15, 15, 30), inp_rect)
            pygame.draw.rect(screen, (150, 150, 200), inp_rect, 1)
            inp_surf = self.font_small.render(self.editor_input or "0", True, (200, 200, 230))
            screen.blit(inp_surf, (inp_rect.x + 4, inp_rect.y + 3))
            self.apply_button.rect = pygame.Rect(eb_x + 20, eb_y + 78, 100, 30)
            self.apply_button.draw(screen)

        # ── particles ─────────────────────────────────────────
        for p in self._particles:
            a = int(200 * (p['life'] / p['max_life']))
            if a > 0:
                ps = pygame.Surface((int(p['size'] * 2), int(p['size'] * 2)))
                ps.set_colorkey((0, 0, 0))
                pygame.draw.circle(ps, p['color'], (int(p['size']), int(p['size'])), int(p['size']))
                ps.set_alpha(a)
                screen.blit(ps, (int(p['x'] - p['size']), int(p['y'] - p['size'])))

        if random.random() < 0.25:
            self._add_particles(
                dx + random.randint(0, self.panel_w),
                dy + random.randint(0, self.panel_h), 1,
            )
