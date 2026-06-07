"""
Majestic Archeologium Minigame Module (Ultimate Ascension).

Provides a beautiful, treasure-hunting variation of Minesweeper
with push-your-luck mechanics, AI generated backgrounds, a Rules tab,
Hardened Stone, massive assembled artifacts, and a mid-game shop (The Reliquary).
"""

import random
import pygame
import math
import os

import src.config as cfg
from src.core.logger import logger

# ---------------------------------------------------------------------------
# Constants & Colors
# ---------------------------------------------------------------------------

GOLD = (230, 190, 80)
GOLD_GLOW = (255, 230, 150)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 40, 40)
CURSE_GLOW = (150, 0, 200)
GREEN_TEXT = (80, 220, 80)
OBSIDIAN = (20, 20, 25)
MAHOGANY = (50, 25, 15)

TILE_COVERED = (90, 75, 60)
TILE_COVERED_HOVER = (110, 95, 80)
TILE_REVEALED = (40, 35, 30)

TILE_HARDENED = (60, 45, 35)
TILE_HARDENED_HOVER = (75, 60, 45)

BASE_SAFE_REWARD = 2
HARDENED_MULTIPLIER = 3
BASE_ARTIFACT_REWARD = 250
BASE_CLEAR_BONUS = 200

COST_AEGIS = 60
COST_ORACLE = 40

NUMBER_COLORS = {
    1: (100, 200, 255),
    2: (100, 255, 100),
    3: (255, 220, 100),
    4: (255, 150, 50),
    5: (255, 50, 50),
    6: (200, 50, 255),
    7: (255, 50, 150),
    8: (255, 255, 255),
}

DIFFICULTIES = {
    "Easy": {"cols": 8, "rows": 8, "curses": 8, "artifacts": 1, "cost": 10, "mult": 1.0},
    "Normal": {"cols": 12, "rows": 12, "curses": 20, "artifacts": 2, "cost": 30, "mult": 1.5},
    "Hard": {"cols": 16, "rows": 16, "curses": 45, "artifacts": 3, "cost": 80, "mult": 2.5},
}

COMPLICATIONS = [
    {"id": "volatile", "name": "Volatile Curses", "desc": "Curse penalty is 100% of loot instead of 50%.", "mult": 0.5},
    {"id": "time", "name": "Time Crunch", "desc": "You have exactly 60 seconds to clear or cash out.", "mult": 0.5},
    {"id": "blind", "name": "Blind Faith", "desc": "Wards (Flags) are completely disabled.", "mult": 0.8},
    {"id": "fog", "name": "Fog of War", "desc": "Numbers are obscured unless your mouse is nearby.", "mult": 1.0},
]

# ---------------------------------------------------------------------------
# Particle System
# ---------------------------------------------------------------------------

class Particle:
    def __init__(self, x, y, color, speed_mult=1.0, life_mult=1.0, size_mult=1.0):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(50, 150) * speed_mult
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 50
        self.life = 1.0
        self.decay = random.uniform(0.5, 1.5) / life_mult
        self.size = random.uniform(2, 6) * size_mult

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 300 * dt
        self.life -= self.decay * dt

    def draw(self, surface):
        if self.life > 0:
            alpha = int(255 * self.life)
            color = (*self.color[:3], alpha)
            surf = pygame.Surface((int(self.size), int(self.size)), pygame.SRCALPHA)
            surf.fill(color)
            surface.blit(surf, (int(self.x), int(self.y)))


# ---------------------------------------------------------------------------
# Minigame Class
# ---------------------------------------------------------------------------

class ArcheologiumMinigame:
    PHASE_SETUP = "setup"
    PHASE_RULES = "rules"
    PHASE_PLAYING = "playing"
    PHASE_RESULT = "result"

    TOOL_NORMAL = "normal"
    TOOL_ORACLE = "oracle"

    def __init__(self, app, on_close=None, player_money=100):
        self.app = app
        self.on_close = on_close
        self.player_money = player_money
        self.net_change = 0

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        self.font_title = cfg.get_font(max(16, int(46 * cfg.ui_scale())))
        self.font_large = cfg.get_font(max(12, int(32 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(24 * cfg.ui_scale())))
        self.font_small = cfg.get_font(max(8, int(18 * cfg.ui_scale())))
        self.font_numbers = cfg.get_font(max(14, int(28 * cfg.ui_scale())))

        # Panel rect
        panel_w = int(sw * 0.9)
        panel_h = int(sh * 0.95)
        self.panel_rect = pygame.Rect((sw - panel_w) // 2, (sh - panel_h) // 2, panel_w, panel_h)
        self.bg_surf = self._create_bg_surface(panel_w, panel_h)

        self.phase = self.PHASE_SETUP
        
        # Setup Selection
        self.sel_diff = "Normal"
        self.sel_comps = {"volatile": False, "time": False, "blind": False, "fog": False}

        # Game State
        self.num_cols = 10
        self.num_rows = 10
        self.num_curses = 15
        self.num_artifacts = 2
        self.tile_size = 32
        self.grid_rect = pygame.Rect(0, 0, 0, 0)
        
        self.grid_health = []    # 0=Revealed, 1=Dirt, 2=Hardened
        self.grid_mines = []     
        self.grid_numbers = []   
        self.grid_flagged = []
        
        # Artifact tracking
        self.artifacts = [] # List of dicts {id, cells: [], claimed: bool}
        self.grid_artifact_id = []

        self.first_click = True
        self.run_gold = 0
        self.particles = []
        self.last_time = pygame.time.get_ticks()
        self.screen_shake = 0.0

        # Reliquary state
        self.has_aegis = False
        self.active_tool = self.TOOL_NORMAL
        self.time_left = 0.0

        # UI
        self._btn_action = None
        self._btn_rules = None
        self._btn_setup = None
        self._btn_cash_out = None
        self._btn_aegis = None
        self._btn_oracle = None
        self._btn_close_top = pygame.Rect(self.panel_rect.right - 40, self.panel_rect.y + 10, 30, 30)
        self._rects_diff = {}
        self._rects_comp = {}

        self.result_title = ""
        self.result_color = WHITE

    def _create_bg_surface(self, w, h):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        # Try to load the generated majestic background
        bg_path = os.path.join(cfg.BASE_DIR, "assets", "ui", "archeologium_bg.png")
        if os.path.exists(bg_path):
            try:
                img = pygame.image.load(bg_path).convert_alpha()
                # Tile it
                iw, ih = img.get_size()
                for tx in range(0, w, iw):
                    for ty in range(0, h, ih):
                        surf.blit(img, (tx, ty))
                # Add dark overlay so text is readable
                darken = pygame.Surface((w, h), pygame.SRCALPHA)
                darken.fill((0, 0, 0, 150))
                surf.blit(darken, (0, 0))
            except Exception as e:
                pygame.draw.rect(surf, OBSIDIAN, (0, 0, w, h))
        else:
            pygame.draw.rect(surf, OBSIDIAN, (0, 0, w, h))

        # Borders
        pygame.draw.rect(surf, OBSIDIAN, (0, 0, w, h), width=0, border_radius=16)
        inner_rect = pygame.Rect(8, 8, w - 16, h - 16)
        pygame.draw.rect(surf, MAHOGANY, inner_rect, width=6, border_radius=12)
        pygame.draw.rect(surf, GOLD, (0, 0, w, h), width=4, border_radius=16)

        for cx in (16, w - 16):
            for cy in (16, h - 16):
                pygame.draw.circle(surf, GOLD_GLOW, (cx, cy), 8)
                pygame.draw.circle(surf, WHITE, (cx, cy), 3)
        return surf

    def _current_money(self) -> int:
        return self.player_money + self.net_change

    def _can_afford(self, amount: int) -> bool:
        return self._current_money() >= amount

    def _get_current_mult(self):
        m = DIFFICULTIES[self.sel_diff]["mult"]
        for c in COMPLICATIONS:
            if self.sel_comps[c["id"]]:
                m += c["mult"]
        return m

    def _start_game(self):
        cost = DIFFICULTIES[self.sel_diff]["cost"]
        if not self._can_afford(cost):
            return
            
        self.net_change -= cost
        self.run_gold = 0
        self.phase = self.PHASE_PLAYING
        self.first_click = True
        self.screen_shake = 0.0
        self.has_aegis = False
        self.active_tool = self.TOOL_NORMAL

        c = DIFFICULTIES[self.sel_diff]
        self.num_cols = c["cols"]
        self.num_rows = c["rows"]
        self.num_curses = c["curses"]
        self.num_artifacts = c["artifacts"]
        
        pw, ph = self.panel_rect.width, self.panel_rect.height
        # Leave room on the right for the Reliquary Shop
        self.tile_size = int(min(pw * 0.6 // self.num_cols, ph * 0.7 // self.num_rows))
        self.grid_rect = pygame.Rect(
            self.panel_rect.x + 50,
            self.panel_rect.y + int(ph * 0.2),
            self.num_cols * self.tile_size,
            self.num_rows * self.tile_size
        )

        self.grid_health = [[1 for _ in range(self.num_rows)] for _ in range(self.num_cols)]
        self.grid_flagged = [[False for _ in range(self.num_rows)] for _ in range(self.num_cols)]

        if self.sel_comps["time"]:
            self.time_left = 60.0

    def _generate_grid(self, safe_x, safe_y):
        self.grid_mines = [[False for _ in range(self.num_rows)] for _ in range(self.num_cols)]
        self.grid_artifact_id = [[-1 for _ in range(self.num_rows)] for _ in range(self.num_cols)]
        self.grid_numbers = [[0 for _ in range(self.num_rows)] for _ in range(self.num_cols)]
        self.artifacts = []

        # 1. Place 2x2 Artifacts
        placed = 0
        while placed < self.num_artifacts:
            x = random.randint(0, self.num_cols - 2)
            y = random.randint(0, self.num_rows - 2)
            # Ensure it doesn't overlap the first click safe zone
            safe_dist = max(abs(x - safe_x), abs(y - safe_y), abs(x+1 - safe_x), abs(y+1 - safe_y))
            if safe_dist > 1:
                # Check empty
                empty = True
                for dx in range(2):
                    for dy in range(2):
                        if self.grid_artifact_id[x+dx][y+dy] != -1:
                            empty = False
                if empty:
                    cells = [(x+dx, y+dy) for dx in range(2) for dy in range(2)]
                    for cx, cy in cells:
                        self.grid_artifact_id[cx][cy] = placed
                    self.artifacts.append({"id": placed, "cells": cells, "claimed": False})
                    placed += 1

        # 2. Place Curses
        placed = 0
        while placed < self.num_curses:
            x = random.randint(0, self.num_cols - 1)
            y = random.randint(0, self.num_rows - 1)
            if not self.grid_mines[x][y] and self.grid_artifact_id[x][y] == -1 and max(abs(x - safe_x), abs(y - safe_y)) > 1:
                self.grid_mines[x][y] = True
                placed += 1

        # 3. Calculate numbers
        for x in range(self.num_cols):
            for y in range(self.num_rows):
                if self.grid_mines[x][y]:
                    continue
                count = 0
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.num_cols and 0 <= ny < self.num_rows:
                            if self.grid_mines[nx][ny]:
                                count += 1
                self.grid_numbers[x][y] = count

        # 4. Hardened Stone (15% chance for safe non-artifact tiles)
        for x in range(self.num_cols):
            for y in range(self.num_rows):
                if self.grid_artifact_id[x][y] == -1 and not self.grid_mines[x][y]:
                    if random.random() < 0.15:
                        self.grid_health[x][y] = 2

    def _spawn_explosion(self, cx, cy, color, amount=20, speed_mult=1.0):
        for _ in range(amount):
            self.particles.append(Particle(cx, cy, color, speed_mult))

    def _reveal_tile(self, x, y, force_oracle=False):
        if self.grid_health[x][y] == 0 or self.grid_flagged[x][y]:
            return

        cx = self.grid_rect.x + x * self.tile_size + self.tile_size // 2
        cy = self.grid_rect.y + y * self.tile_size + self.tile_size // 2

        if self.first_click:
            self._generate_grid(x, y)
            self.first_click = False

        if force_oracle:
            self.grid_health[x][y] = 0
        else:
            self.grid_health[x][y] -= 1
            if self.grid_health[x][y] > 0:
                # Still hardened, just spawned dust
                self._spawn_explosion(cx, cy, TILE_COVERED, 8, 0.5)
                return

        # Tile is now fully revealed
        if self.grid_mines[x][y]:
            if force_oracle:
                # Oracle protects and flags
                self.grid_flagged[x][y] = True
                self.grid_health[x][y] = 1 # Cover it back up
                return

            if self.has_aegis:
                # Shield breaks, mine destroyed safely!
                self.has_aegis = False
                self.grid_mines[x][y] = False
                self.grid_numbers[x][y] = -1 # Disarmed
                self._spawn_explosion(cx, cy, (50, 150, 255), 40, 2.0)
                self.screen_shake = 5.0
                return

            # Curse Triggered
            self._spawn_explosion(cx, cy, CURSE_GLOW, 80, 2.5)
            self.screen_shake = 25.0
            penalty = self.run_gold if self.sel_comps["volatile"] else self.run_gold // 2
            self.run_gold -= penalty
            self.net_change += self.run_gold
            self.result_title = "CURSE TRIGGERED!"
            self.result_color = RED
            for mx in range(self.num_cols):
                for my in range(self.num_rows):
                    if self.grid_mines[mx][my]:
                        self.grid_health[mx][my] = 0
            self.phase = self.PHASE_RESULT
            return

        mult = self._get_current_mult()
        aid = self.grid_artifact_id[x][y]

        if aid != -1:
            self._spawn_explosion(cx, cy, GOLD_GLOW, 15, 1.0)
            art = self.artifacts[aid]
            if not art["claimed"]:
                all_revealed = True
                for cx_a, cy_a in art["cells"]:
                    if self.grid_health[cx_a][cy_a] > 0:
                        all_revealed = False
                        break
                if all_revealed:
                    art["claimed"] = True
                    self.run_gold += int(BASE_ARTIFACT_REWARD * mult)
                    self.screen_shake = 5.0
                    for cx_a, cy_a in art["cells"]:
                        px = self.grid_rect.x + cx_a * self.tile_size + self.tile_size // 2
                        py = self.grid_rect.y + cy_a * self.tile_size + self.tile_size // 2
                        self._spawn_explosion(px, py, GOLD_GLOW, 50, 2.5)
        else:
            self._spawn_explosion(cx, cy, TILE_COVERED, 5, 0.5)
            # Hardened gave 3x gold
            reward = BASE_SAFE_REWARD * HARDENED_MULTIPLIER if self.grid_health[x][y] == 2 else BASE_SAFE_REWARD
            self.run_gold += int(reward * mult)

        if self.grid_numbers[x][y] == 0 and aid == -1:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.num_cols and 0 <= ny < self.num_rows:
                        if self.grid_health[nx][ny] > 0:
                            self._reveal_tile(nx, ny, force_oracle)

        self._check_win()

    def _toggle_flag(self, x, y):
        if self.sel_comps["blind"]:
            return 
        if self.grid_health[x][y] > 0:
            self.grid_flagged[x][y] = not self.grid_flagged[x][y]

    def _use_oracle(self, center_x, center_y):
        self.active_tool = self.TOOL_NORMAL
        if self.first_click:
            self._generate_grid(center_x, center_y)
            self.first_click = False

        self.screen_shake = 8.0
        # Safe reveal 3x3
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = center_x + dx, center_y + dy
                if 0 <= nx < self.num_cols and 0 <= ny < self.num_rows:
                    if self.grid_mines[nx][ny]:
                        self.grid_flagged[nx][ny] = True
                    elif self.grid_health[nx][ny] > 0:
                        self._reveal_tile(nx, ny, force_oracle=True)

    def _check_win(self):
        for x in range(self.num_cols):
            for y in range(self.num_rows):
                if not self.grid_mines[x][y] and self.grid_health[x][y] > 0:
                    return
        
        mult = self._get_current_mult()
        self.run_gold += int(BASE_CLEAR_BONUS * mult)
        self.net_change += self.run_gold
        self.result_title = "SITE CLEARED!"
        self.result_color = GOLD_GLOW
        self.screen_shake = 5.0
        self._spawn_explosion(self.panel_rect.centerx, self.panel_rect.centery, GOLD_GLOW, 150, 3.5)
        self.phase = self.PHASE_RESULT

    def _cash_out(self):
        if self.phase != self.PHASE_PLAYING or self.first_click:
            return
        self.net_change += self.run_gold
        self.result_title = "CASHED OUT"
        self.result_color = GREEN_TEXT
        self.phase = self.PHASE_RESULT

    def _close(self, outcome: str):
        if callable(self.on_close):
            try:
                self.on_close(outcome, self.net_change)
            except Exception:
                pass
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.phase == self.PHASE_PLAYING and not self.first_click:
                    self._cash_out()
                else:
                    self._close("quit")
                return

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            
            if event.button == 1 and self._btn_close_top.collidepoint(pos):
                if self.phase == self.PHASE_PLAYING and not self.first_click:
                    self._cash_out()
                else:
                    self._close("quit")
                return

            if self.phase == self.PHASE_SETUP and event.button == 1:
                if self._btn_rules and self._btn_rules.collidepoint(pos):
                    self.phase = self.PHASE_RULES
                    return

                for diff_name, rect in self._rects_diff.items():
                    if rect.collidepoint(pos):
                        self.sel_diff = diff_name
                for comp_id, rect in self._rects_comp.items():
                    if rect.collidepoint(pos):
                        self.sel_comps[comp_id] = not self.sel_comps[comp_id]
                        
                if self._btn_action and self._btn_action.collidepoint(pos):
                    self._start_game()
            
            elif self.phase == self.PHASE_RULES and event.button == 1:
                if self._btn_setup and self._btn_setup.collidepoint(pos):
                    self.phase = self.PHASE_SETUP

            elif self.phase == self.PHASE_PLAYING:
                if event.button == 1:
                    if self._btn_cash_out and self._btn_cash_out.collidepoint(pos):
                        self._cash_out()
                        return
                    if self._btn_aegis and self._btn_aegis.collidepoint(pos) and self.run_gold >= COST_AEGIS and not self.has_aegis:
                        self.run_gold -= COST_AEGIS
                        self.has_aegis = True
                    if self._btn_oracle and self._btn_oracle.collidepoint(pos) and self.run_gold >= COST_ORACLE:
                        if self.active_tool == self.TOOL_ORACLE:
                            self.active_tool = self.TOOL_NORMAL
                        else:
                            self.active_tool = self.TOOL_ORACLE

                if self.grid_rect.collidepoint(pos):
                    tx = (pos[0] - self.grid_rect.x) // self.tile_size
                    ty = (pos[1] - self.grid_rect.y) // self.tile_size
                    if event.button == 1:
                        if self.active_tool == self.TOOL_ORACLE:
                            self.run_gold -= COST_ORACLE
                            self._use_oracle(tx, ty)
                        else:
                            self._reveal_tile(tx, ty)
                    elif event.button == 3:
                        self._toggle_flag(tx, ty)

            elif self.phase == self.PHASE_RESULT and event.button == 1:
                if self._btn_action and self._btn_action.collidepoint(pos):
                    self.phase = self.PHASE_SETUP

    def _draw_button(self, surface, rect, text, hovered=False, disabled=False, color=GOLD):
        if disabled:
            bg, border, tc = (40, 40, 40), (80, 80, 80), (150, 150, 150)
        else:
            bg = (100, 80, 40) if hovered else (60, 45, 20)
            border = GOLD_GLOW if hovered else color
            tc = WHITE

        pygame.draw.rect(surface, bg, rect, border_radius=8)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=8)
        txt_surf = self.font_medium.render(text, True, tc)
        surface.blit(txt_surf, txt_surf.get_rect(center=rect.center))

    def _update_logic(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

        if self.screen_shake > 0:
            self.screen_shake -= dt * 40
            if self.screen_shake < 0:
                self.screen_shake = 0

        if self.phase == self.PHASE_PLAYING and self.sel_comps["time"] and not self.first_click:
            self.time_left -= dt
            if self.time_left <= 0:
                self.time_left = 0
                self.screen_shake = 15.0
                penalty = self.run_gold if self.sel_comps["volatile"] else self.run_gold // 2
                self.run_gold -= penalty
                self.net_change += self.run_gold
                self.result_title = "TIME OUT! CAVE IN!"
                self.result_color = RED
                for mx in range(self.num_cols):
                    for my in range(self.num_rows):
                        if self.grid_mines[mx][my]:
                            self.grid_health[mx][my] = 0
                self.phase = self.PHASE_RESULT

    def draw(self, surface: pygame.Surface):
        current_time = pygame.time.get_ticks()
        dt = (current_time - self.last_time) / 1000.0
        self.last_time = current_time
        self._update_logic(dt)

        sx = random.uniform(-self.screen_shake, self.screen_shake)
        sy = random.uniform(-self.screen_shake, self.screen_shake)

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        surface.blit(self.bg_surf, (self.panel_rect.x + sx, self.panel_rect.y + sy))
        mouse_pos = pygame.mouse.get_pos()

        pygame.draw.rect(surface, RED, self._btn_close_top.move(sx, sy), border_radius=4)
        x_surf = self.font_medium.render("X", True, WHITE)
        surface.blit(x_surf, x_surf.get_rect(center=self._btn_close_top.move(sx, sy).center))

        title = self.font_title.render("Archeologium", True, GOLD_GLOW)
        surface.blit(title, (self.panel_rect.centerx - title.get_width() // 2 + sx, self.panel_rect.y + 20 + sy))

        money_text = self.font_medium.render(f"Bank: {self._current_money()}g", True, GOLD)
        surface.blit(money_text, (self.panel_rect.x + 30 + sx, self.panel_rect.y + 30 + sy))

        if self.phase == self.PHASE_SETUP:
            self._draw_setup(surface, mouse_pos, sx, sy)
        elif self.phase == self.PHASE_RULES:
            self._draw_rules(surface, mouse_pos, sx, sy)
        elif self.phase == self.PHASE_PLAYING:
            self._draw_playing(surface, mouse_pos, sx, sy)
        elif self.phase == self.PHASE_RESULT:
            self._draw_playing(surface, (-1000, -1000), sx, sy) 
            self._draw_result(surface, mouse_pos, sx, sy)

        for p in self.particles:
            p.draw(surface)

    def _draw_setup(self, surface, mouse_pos, sx, sy):
        py = self.panel_rect.y + 100 + sy
        px = self.panel_rect.x + 40 + sx

        # Tabs
        self._btn_rules = pygame.Rect(self.panel_rect.right - 180 + sx, self.panel_rect.y + 90 + sy, 140, 40)
        self._draw_button(surface, self._btn_rules, "Read Rules", self._btn_rules.collidepoint(mouse_pos), color=(100, 200, 255))

        d_title = self.font_large.render("Select Difficulty", True, GOLD_GLOW)
        surface.blit(d_title, (px, py))
        py += 40

        self._rects_diff.clear()
        for diff in ["Easy", "Normal", "Hard"]:
            cfg_d = DIFFICULTIES[diff]
            rect = pygame.Rect(px, py, 300, 40)
            self._rects_diff[diff] = rect
            
            color = GOLD if self.sel_diff == diff else (150, 150, 150)
            pygame.draw.circle(surface, color, (px + 15, py + 20), 10, width=0 if self.sel_diff == diff else 2)
            
            dtx = self.font_medium.render(f"{diff} (Fee: {cfg_d['cost']}g, x{cfg_d['mult']})", True, color)
            surface.blit(dtx, (px + 40, py + 8))
            py += 50

        py += 20
        c_title = self.font_large.render("Complications (Optional)", True, RED)
        surface.blit(c_title, (px, py))
        py += 40

        self._rects_comp.clear()
        for comp in COMPLICATIONS:
            cid = comp["id"]
            rect = pygame.Rect(px, py, 600, 40)
            self._rects_comp[cid] = rect
            
            selected = self.sel_comps[cid]
            color = GOLD_GLOW if selected else (150, 150, 150)
            
            pygame.draw.rect(surface, color, (px, py + 10, 20, 20), width=0 if selected else 2, border_radius=4)
            if selected:
                pygame.draw.line(surface, OBSIDIAN, (px+4, py+20), (px+8, py+26), 3)
                pygame.draw.line(surface, OBSIDIAN, (px+8, py+26), (px+16, py+14), 3)

            ctx = self.font_medium.render(f"{comp['name']} (+{comp['mult']}x)", True, color)
            surface.blit(ctx, (px + 35, py + 8))
            
            desc = self.font_small.render(comp["desc"], True, (180, 180, 180))
            surface.blit(desc, (px + 35, py + 35))
            py += 60

        tot_mult = self._get_current_mult()
        tot_cost = DIFFICULTIES[self.sel_diff]["cost"]

        res_px = self.panel_rect.right - 350 + sx
        res_py = self.panel_rect.y + 150 + sy
        pygame.draw.rect(surface, MAHOGANY, (res_px, res_py, 300, 200), border_radius=12)
        pygame.draw.rect(surface, GOLD, (res_px, res_py, 300, 200), width=3, border_radius=12)

        st1 = self.font_large.render("Total Multiplier", True, WHITE)
        surface.blit(st1, (res_px + 150 - st1.get_width()//2, res_py + 30))
        st2 = self.font_title.render(f"x{tot_mult:.1f}", True, GOLD_GLOW)
        surface.blit(st2, (res_px + 150 - st2.get_width()//2, res_py + 70))
        st3 = self.font_medium.render(f"Entry Fee: {tot_cost}g", True, RED)
        surface.blit(st3, (res_px + 150 - st3.get_width()//2, res_py + 130))

        btn_w, btn_h = 240, 60
        self._btn_action = pygame.Rect(self.panel_rect.centerx - btn_w // 2, self.panel_rect.bottom - 100 + sy, btn_w, btn_h)
        can_afford = self._can_afford(tot_cost)
        self._draw_button(surface, self._btn_action, "Pay & Descend", self._btn_action.collidepoint(mouse_pos), not can_afford)

    def _draw_rules(self, surface, mouse_pos, sx, sy):
        py = self.panel_rect.y + 100 + sy
        px = self.panel_rect.x + 60 + sx

        self._btn_setup = pygame.Rect(self.panel_rect.right - 180 + sx, self.panel_rect.y + 90 + sy, 140, 40)
        self._draw_button(surface, self._btn_setup, "Back to Setup", self._btn_setup.collidepoint(mouse_pos))

        rules = [
            ("The Goal:", "Uncover all safe dirt tiles to earn Gold and a massive Clear Bonus.", GOLD_GLOW),
            ("Numbers:", "Show how many Curses (Mines) are in the 8 adjacent tiles.", (100, 200, 255)),
            ("Curses:", "Clicking a Curse explodes the site. You lose half your loot and the game ends.", RED),
            ("Wards:", "Right-click to place a Ward to flag suspected curses safely.", (200, 100, 255)),
            ("Hardened Stone:", "Darker, cracked dirt. Takes 2 clicks to break, but yields 3x Gold!", (150, 130, 100)),
            ("Pharaoh's Relic:", "Find and uncover all 4 tiles of a 2x2 Golden Artifact for a huge payout.", GOLD),
            ("The Reliquary:", "Spend your run's gold during the game to buy powerful tactical abilities:", WHITE),
            (" - Aegis:", "Costs 60g. Shields you from a single curse explosion.", (100, 255, 100)),
            (" - Oracle:", "Costs 40g. Safely reveals a random 3x3 area around your click.", (100, 200, 255)),
            ("Cash Out:", "You can click 'Cash Out' at any time to walk away with your current loot.", GREEN_TEXT)
        ]

        for title, desc, color in rules:
            t_surf = self.font_medium.render(title, True, color)
            surface.blit(t_surf, (px, py))
            d_surf = self.font_small.render(desc, True, (200, 200, 200))
            surface.blit(d_surf, (px + t_surf.get_width() + 10, py + 5))
            py += 45

    def _draw_playing(self, surface, mouse_pos, sx, sy):
        earn_text = self.font_large.render(f"Run Loot: {self.run_gold}g", True, GOLD_GLOW)
        surface.blit(earn_text, (self.panel_rect.x + 40 + sx, self.panel_rect.y + 80 + sy))

        if self.sel_comps["time"]:
            col = RED if self.time_left < 10 else WHITE
            time_str = f"{self.time_left:.1f}s"
            t_text = self.font_title.render(time_str, True, col)
            surface.blit(t_text, (self.panel_rect.centerx - t_text.get_width()//2 + sx, self.panel_rect.y + 70 + sy))

        if self.phase == self.PHASE_PLAYING:
            btn_w, btn_h = 140, 40
            self._btn_cash_out = pygame.Rect(self.panel_rect.right - 40 - btn_w, self.panel_rect.y + 80, btn_w, btn_h)
            self._draw_button(surface, self._btn_cash_out.move(sx, sy), "Cash Out", self._btn_cash_out.collidepoint(mouse_pos), disabled=self.first_click, color=GREEN_TEXT)

            # Reliquary Shop
            shop_x = self.grid_rect.right + 20
            shop_y = self.grid_rect.y + 20
            s_title = self.font_large.render("Reliquary", True, (200, 150, 255))
            surface.blit(s_title, (shop_x + sx, shop_y + sy))
            
            # Aegis
            self._btn_aegis = pygame.Rect(shop_x, shop_y + 50, 160, 50)
            a_disabled = self.run_gold < COST_AEGIS or self.has_aegis or self.first_click
            a_col = (100, 255, 100) if self.has_aegis else GOLD_GLOW
            a_txt = "Aegis Active" if self.has_aegis else f"Aegis ({COST_AEGIS}g)"
            self._draw_button(surface, self._btn_aegis.move(sx, sy), a_txt, self._btn_aegis.collidepoint(mouse_pos), disabled=a_disabled, color=a_col)
            
            # Oracle
            self._btn_oracle = pygame.Rect(shop_x, shop_y + 120, 160, 50)
            o_disabled = self.run_gold < COST_ORACLE or self.first_click
            o_col = (100, 200, 255) if self.active_tool == self.TOOL_ORACLE else GOLD_GLOW
            o_txt = "Select Oracle..." if self.active_tool == self.TOOL_ORACLE else f"Oracle ({COST_ORACLE}g)"
            self._draw_button(surface, self._btn_oracle.move(sx, sy), o_txt, self._btn_oracle.collidepoint(mouse_pos), disabled=o_disabled, color=o_col)


        g_rect = self.grid_rect.move(sx, sy)
        pygame.draw.rect(surface, MAHOGANY, g_rect.inflate(12, 12), border_radius=6)
        pygame.draw.rect(surface, OBSIDIAN, g_rect)

        use_fog = self.sel_comps["fog"] and self.phase == self.PHASE_PLAYING
        mx, my = mouse_pos
        mtx = (mx - g_rect.x) // self.tile_size
        mty = (my - g_rect.y) // self.tile_size

        pulse = (math.sin(pygame.time.get_ticks() / 300.0) + 1) / 2 # 0.0 to 1.0

        for x in range(self.num_cols):
            for y in range(self.num_rows):
                rect = pygame.Rect(g_rect.x + x * self.tile_size, g_rect.y + y * self.tile_size, self.tile_size, self.tile_size)
                
                in_light = True
                if use_fog:
                    dist = max(abs(x - mtx), abs(y - mty))
                    if dist > 1:
                        in_light = False

                if self.grid_health[x][y] > 0:
                    hover = rect.collidepoint(mouse_pos) and self.phase == self.PHASE_PLAYING
                    if self.grid_health[x][y] == 2:
                        color = TILE_HARDENED_HOVER if hover else TILE_HARDENED
                    else:
                        color = TILE_COVERED_HOVER if hover else TILE_COVERED

                    pygame.draw.rect(surface, color, rect.inflate(-2, -2), border_radius=2)
                    
                    if self.grid_health[x][y] == 1:
                        pygame.draw.line(surface, (130, 115, 100), rect.topleft, rect.topright, 2)
                        pygame.draw.line(surface, (130, 115, 100), rect.topleft, rect.bottomleft, 2)
                        pygame.draw.line(surface, (50, 40, 30), rect.bottomleft, rect.bottomright, 2)
                        pygame.draw.line(surface, (50, 40, 30), rect.topright, rect.bottomright, 2)
                    else:
                        # Hardened stone details
                        pygame.draw.line(surface, (80, 65, 55), rect.topleft, rect.topright, 2)
                        pygame.draw.line(surface, (30, 20, 15), rect.bottomleft, rect.bottomright, 2)
                        # Cracks
                        pygame.draw.line(surface, (20, 15, 10), rect.center, (rect.centerx+10, rect.bottom-5), 2)
                        pygame.draw.line(surface, (20, 15, 10), rect.center, (rect.left+5, rect.centery-5), 2)

                    if self.grid_flagged[x][y] and in_light:
                        glow_r = int(CURSE_GLOW[0] * (0.6 + 0.4 * pulse))
                        glow_b = int(CURSE_GLOW[2] * (0.6 + 0.4 * pulse))
                        rune = self.font_numbers.render("W", True, (glow_r, 0, glow_b))
                        surface.blit(rune, rune.get_rect(center=rect.center))

                else:
                    pygame.draw.rect(surface, TILE_REVEALED, rect.inflate(-2, -2), border_radius=2)

                    if self.grid_mines[x][y]:
                        if self.grid_numbers[x][y] == -1:
                            # Disarmed mine
                            pygame.draw.circle(surface, (80, 80, 80), rect.center, self.tile_size // 3)
                        else:
                            pygame.draw.circle(surface, CURSE_GLOW, rect.center, self.tile_size // 3)
                            pygame.draw.circle(surface, BLACK, rect.center, self.tile_size // 4)
                    else:
                        aid = self.grid_artifact_id[x][y]
                        if aid != -1:
                            art = self.artifacts[aid]
                            if in_light:
                                col = GOLD_GLOW if art["claimed"] else GOLD
                                pygame.draw.rect(surface, col, rect.inflate(-6, -6), border_radius=4)
                                if art["claimed"]:
                                    pygame.draw.rect(surface, WHITE, rect.inflate(-6, -6), width=2, border_radius=4)
                        else:
                            num = self.grid_numbers[x][y]
                            if num > 0 and in_light:
                                c = NUMBER_COLORS.get(num, WHITE)
                                # Animated glow for high numbers
                                if num >= 3:
                                    c = (int(c[0]*(0.8+0.2*pulse)), int(c[1]*(0.8+0.2*pulse)), int(c[2]*(0.8+0.2*pulse)))
                                nsurf = self.font_numbers.render(str(num), True, c)
                                surface.blit(nsurf, nsurf.get_rect(center=rect.center))

                if not in_light:
                    fog_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
                    fog_surf.fill((0, 0, 0, 180))
                    surface.blit(fog_surf, rect)

    def _draw_result(self, surface, mouse_pos, sx, sy):
        overlay = pygame.Surface(self.panel_rect.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        surface.blit(overlay, (self.panel_rect.x + sx, self.panel_rect.y + sy))

        title = self.font_title.render(self.result_title, True, self.result_color)
        surface.blit(title, (self.panel_rect.centerx - title.get_width() // 2 + sx, self.panel_rect.centery - 60 + sy))

        res = self.font_large.render(f"Secured Loot: {self.run_gold} Gold", True, GOLD_GLOW)
        surface.blit(res, (self.panel_rect.centerx - res.get_width() // 2 + sx, self.panel_rect.centery + 10 + sy))

        btn_w, btn_h = 240, 50
        self._btn_action = pygame.Rect(self.panel_rect.centerx - btn_w // 2, self.panel_rect.bottom - 100, btn_w, btn_h)
        self._draw_button(surface, self._btn_action.move(sx, sy), "Continue", self._btn_action.collidepoint(mouse_pos))

