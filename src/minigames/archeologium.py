"""
Majestic Archeologium Minigame Module (Minesweeper Variant).

Provides a beautiful, treasure-hunting variation of Minesweeper
with push-your-luck mechanics, glowing runes, and particle effects.
"""

import random
import pygame
import math

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

ENTRY_COST = 20
SAFE_REWARD = 1
ARTIFACT_REWARD = 50
CLEAR_BONUS = 200

NUM_COLS = 10
NUM_ROWS = 10
NUM_CURSES = 15
NUM_ARTIFACTS = 3

# Colors for numbers 1-8
NUMBER_COLORS = {
    1: (100, 200, 255), # Cyan
    2: (100, 255, 100), # Green
    3: (255, 220, 100), # Yellow
    4: (255, 150, 50),  # Orange
    5: (255, 50, 50),   # Red
    6: (200, 50, 255),  # Purple
    7: (255, 50, 150),  # Magenta
    8: (255, 255, 255), # White
}

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
        self.vy = math.sin(angle) * speed - 50 # upward bias
        self.life = 1.0
        self.decay = random.uniform(0.5, 1.5) / life_mult
        self.size = random.uniform(2, 6) * size_mult

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 300 * dt # gravity
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
    PHASE_START = "start"
    PHASE_PLAYING = "playing"
    PHASE_RESULT = "result"

    def __init__(self, app, on_close=None, player_money=100):
        self.app = app
        self.on_close = on_close
        self.player_money = player_money
        self.net_change = 0

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        # Fonts
        self.font_title = cfg.get_font(max(16, int(46 * cfg.ui_scale())))
        self.font_large = cfg.get_font(max(12, int(32 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(24 * cfg.ui_scale())))
        self.font_small = cfg.get_font(max(8, int(18 * cfg.ui_scale())))
        # Special bold font for numbers if possible, else just use large
        self.font_numbers = cfg.get_font(max(14, int(28 * cfg.ui_scale())))

        # Panel rect
        panel_w = int(sw * 0.8)
        panel_h = int(sh * 0.85)
        self.panel_rect = pygame.Rect((sw - panel_w) // 2, (sh - panel_h) // 2, panel_w, panel_h)
        self.bg_surf = self._create_bg_surface(panel_w, panel_h)

        self.phase = self.PHASE_START
        self.tile_size = int(min(panel_w * 0.6 // NUM_COLS, panel_h * 0.6 // NUM_ROWS))
        self.grid_rect = pygame.Rect(
            self.panel_rect.centerx - (NUM_COLS * self.tile_size) // 2,
            self.panel_rect.y + int(panel_h * 0.25),
            NUM_COLS * self.tile_size,
            NUM_ROWS * self.tile_size
        )

        # Game State
        self.grid_mines = []     # bool
        self.grid_artifacts = [] # bool
        self.grid_numbers = []   # int (0-8)
        self.grid_revealed = []  # bool
        self.grid_flagged = []   # bool
        self.first_click = True
        
        self.run_gold = 0
        self.particles = []
        self.last_time = pygame.time.get_ticks()
        
        self.screen_shake = 0.0

        # UI rects
        self._btn_action = None
        self._btn_cash_out = None
        self._btn_close_top = pygame.Rect(self.panel_rect.right - 40, self.panel_rect.y + 10, 30, 30)

        self.result_title = ""
        self.result_color = WHITE

    def _create_bg_surface(self, w, h):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, OBSIDIAN, (0, 0, w, h), border_radius=16)
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

    def _generate_grid(self, safe_x, safe_y):
        self.grid_mines = [[False for _ in range(NUM_ROWS)] for _ in range(NUM_COLS)]
        self.grid_artifacts = [[False for _ in range(NUM_ROWS)] for _ in range(NUM_COLS)]
        self.grid_numbers = [[0 for _ in range(NUM_ROWS)] for _ in range(NUM_COLS)]

        # Place Curses
        placed = 0
        while placed < NUM_CURSES:
            x = random.randint(0, NUM_COLS - 1)
            y = random.randint(0, NUM_ROWS - 1)
            # Prevent mine on first click and immediate surroundings to ensure a safe start
            if not self.grid_mines[x][y] and max(abs(x - safe_x), abs(y - safe_y)) > 1:
                self.grid_mines[x][y] = True
                placed += 1

        # Place Artifacts on safe tiles
        placed = 0
        while placed < NUM_ARTIFACTS:
            x = random.randint(0, NUM_COLS - 1)
            y = random.randint(0, NUM_ROWS - 1)
            if not self.grid_mines[x][y] and not self.grid_artifacts[x][y] and (x != safe_x or y != safe_y):
                self.grid_artifacts[x][y] = True
                placed += 1

        # Calculate numbers
        for x in range(NUM_COLS):
            for y in range(NUM_ROWS):
                if self.grid_mines[x][y]:
                    continue
                count = 0
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < NUM_COLS and 0 <= ny < NUM_ROWS:
                            if self.grid_mines[nx][ny]:
                                count += 1
                self.grid_numbers[x][y] = count

    def _start_game(self):
        if not self._can_afford(ENTRY_COST):
            return
        self.net_change -= ENTRY_COST
        self.run_gold = 0
        self.phase = self.PHASE_PLAYING
        self.first_click = True
        self.grid_revealed = [[False for _ in range(NUM_ROWS)] for _ in range(NUM_COLS)]
        self.grid_flagged = [[False for _ in range(NUM_ROWS)] for _ in range(NUM_COLS)]
        self.screen_shake = 0.0

    def _spawn_explosion(self, cx, cy, color, amount=20, speed_mult=1.0):
        for _ in range(amount):
            self.particles.append(Particle(cx, cy, color, speed_mult))

    def _reveal_tile(self, x, y):
        if self.grid_revealed[x][y] or self.grid_flagged[x][y]:
            return

        cx = self.grid_rect.x + x * self.tile_size + self.tile_size // 2
        cy = self.grid_rect.y + y * self.tile_size + self.tile_size // 2

        if self.first_click:
            self._generate_grid(x, y)
            self.first_click = False

        self.grid_revealed[x][y] = True

        if self.grid_mines[x][y]:
            # Trigger Curse!
            self._spawn_explosion(cx, cy, CURSE_GLOW, 50, 2.0)
            self.screen_shake = 15.0
            loss = self.run_gold // 2
            self.run_gold -= loss
            self.net_change += self.run_gold
            self.result_title = "CURSE TRIGGERED!"
            self.result_color = RED
            # Reveal all mines
            for mx in range(NUM_COLS):
                for my in range(NUM_ROWS):
                    if self.grid_mines[mx][my]:
                        self.grid_revealed[mx][my] = True
            self.phase = self.PHASE_RESULT
            return

        if self.grid_artifacts[x][y]:
            # Artifact found!
            self._spawn_explosion(cx, cy, GOLD_GLOW, 30, 1.5)
            self.run_gold += ARTIFACT_REWARD
        else:
            # Safe tile
            self._spawn_explosion(cx, cy, TILE_COVERED, 5, 0.5)
            self.run_gold += SAFE_REWARD

        # Flood fill if 0
        if self.grid_numbers[x][y] == 0 and not self.grid_artifacts[x][y]:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < NUM_COLS and 0 <= ny < NUM_ROWS:
                        if not self.grid_revealed[nx][ny]:
                            self._reveal_tile(nx, ny)

        self._check_win()

    def _toggle_flag(self, x, y):
        if not self.grid_revealed[x][y]:
            self.grid_flagged[x][y] = not self.grid_flagged[x][y]

    def _check_win(self):
        # Win if all non-mine tiles are revealed
        for x in range(NUM_COLS):
            for y in range(NUM_ROWS):
                if not self.grid_mines[x][y] and not self.grid_revealed[x][y]:
                    return # not won yet
        
        # Won!
        self.run_gold += CLEAR_BONUS
        self.net_change += self.run_gold
        self.result_title = "SITE CLEARED!"
        self.result_color = GOLD_GLOW
        self.screen_shake = 5.0
        # Spawn massive gold explosion
        self._spawn_explosion(self.panel_rect.centerx, self.panel_rect.centery, GOLD_GLOW, 100, 3.0)
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
            if self.phase == self.PHASE_START and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_game()
            elif self.phase == self.PHASE_RESULT and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.phase = self.PHASE_START

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            
            # Close button
            if event.button == 1 and self._btn_close_top.collidepoint(pos):
                if self.phase == self.PHASE_PLAYING and not self.first_click:
                    self._cash_out()
                else:
                    self._close("quit")
                return

            if self.phase == self.PHASE_START and event.button == 1:
                if self._btn_action and self._btn_action.collidepoint(pos):
                    self._start_game()
            
            elif self.phase == self.PHASE_PLAYING:
                if event.button == 1 and self._btn_cash_out and self._btn_cash_out.collidepoint(pos):
                    self._cash_out()
                    return

                if self.grid_rect.collidepoint(pos):
                    tx = (pos[0] - self.grid_rect.x) // self.tile_size
                    ty = (pos[1] - self.grid_rect.y) // self.tile_size
                    if event.button == 1: # Left click (Dig)
                        self._reveal_tile(tx, ty)
                    elif event.button == 3: # Right click (Flag)
                        self._toggle_flag(tx, ty)

            elif self.phase == self.PHASE_RESULT and event.button == 1:
                if self._btn_action and self._btn_action.collidepoint(pos):
                    self.phase = self.PHASE_START

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

    def _update_particles_and_shake(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

        if self.screen_shake > 0:
            self.screen_shake -= dt * 30
            if self.screen_shake < 0:
                self.screen_shake = 0

    def draw(self, surface: pygame.Surface):
        current_time = pygame.time.get_ticks()
        dt = (current_time - self.last_time) / 1000.0
        self.last_time = current_time
        self._update_particles_and_shake(dt)

        # Calculate shake offset
        sx = random.uniform(-self.screen_shake, self.screen_shake)
        sy = random.uniform(-self.screen_shake, self.screen_shake)

        # Dim background
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        # Panel
        surface.blit(self.bg_surf, (self.panel_rect.x + sx, self.panel_rect.y + sy))
        mouse_pos = pygame.mouse.get_pos()
        # Adjust mouse pos for interaction checks on shaken UI isn't strictly necessary since shake is visual and rapid

        # Close Top Right
        pygame.draw.rect(surface, RED, self._btn_close_top.move(sx, sy), border_radius=4)
        x_surf = self.font_medium.render("X", True, WHITE)
        surface.blit(x_surf, x_surf.get_rect(center=self._btn_close_top.move(sx, sy).center))

        # Header
        title = self.font_title.render("Archeologium", True, GOLD_GLOW)
        surface.blit(title, (self.panel_rect.centerx - title.get_width() // 2 + sx, self.panel_rect.y + 20 + sy))

        money_text = self.font_medium.render(f"Total Gold: {self._current_money()}", True, GOLD)
        surface.blit(money_text, (self.panel_rect.x + 30 + sx, self.panel_rect.y + 30 + sy))

        if self.phase == self.PHASE_START:
            self._draw_start(surface, mouse_pos, sx, sy)
        elif self.phase == self.PHASE_PLAYING:
            self._draw_playing(surface, mouse_pos, sx, sy)
        elif self.phase == self.PHASE_RESULT:
            self._draw_playing(surface, (-1000, -1000), sx, sy) # draw grid behind result
            self._draw_result(surface, mouse_pos, sx, sy)

        # Draw particles on top
        for p in self.particles:
            p.draw(surface)

    def _draw_start(self, surface, mouse_pos, sx, sy):
        desc = [
            "Welcome to the majestic dig site.",
            "L-Click to Dig. R-Click to Ward (Flag).",
            "Numbers indicate adjacent ancient curses.",
            f"Earn +{SAFE_REWARD}g per safe tile, +{ARTIFACT_REWARD}g per Artifact.",
            "Hit a Curse? Lose 50% of this run's loot!",
            f"Clear the site for a +{CLEAR_BONUS}g Bonus.",
            "Cash Out anytime to keep your findings safely.",
            "",
            f"Entry Fee: {ENTRY_COST} Gold"
        ]
        
        y = self.panel_rect.centery - 120 + sy
        for line in desc:
            surf = self.font_medium.render(line, True, WHITE)
            surface.blit(surf, (self.panel_rect.centerx - surf.get_width() // 2 + sx, y))
            y += 30

        btn_w, btn_h = 240, 50
        self._btn_action = pygame.Rect(self.panel_rect.centerx - btn_w // 2, self.panel_rect.bottom - 100, btn_w, btn_h)
        can_afford = self._can_afford(ENTRY_COST)
        self._draw_button(surface, self._btn_action.move(sx, sy), "Pay & Descend", self._btn_action.collidepoint(mouse_pos), not can_afford)

    def _draw_playing(self, surface, mouse_pos, sx, sy):
        # Stats UI
        earn_text = self.font_large.render(f"Run Loot: {self.run_gold}g", True, GOLD_GLOW)
        surface.blit(earn_text, (self.panel_rect.x + 40 + sx, self.panel_rect.y + 80 + sy))

        if self.phase == self.PHASE_PLAYING:
            btn_w, btn_h = 160, 40
            self._btn_cash_out = pygame.Rect(self.panel_rect.right - 40 - btn_w, self.panel_rect.y + 80, btn_w, btn_h)
            self._draw_button(surface, self._btn_cash_out.move(sx, sy), "Cash Out", self._btn_cash_out.collidepoint(mouse_pos), disabled=self.first_click, color=GREEN_TEXT)

        # Grid Background border
        g_rect = self.grid_rect.move(sx, sy)
        pygame.draw.rect(surface, MAHOGANY, g_rect.inflate(8, 8), border_radius=4)
        pygame.draw.rect(surface, OBSIDIAN, g_rect)

        # Draw Tiles
        for x in range(NUM_COLS):
            for y in range(NUM_ROWS):
                rect = pygame.Rect(g_rect.x + x * self.tile_size, g_rect.y + y * self.tile_size, self.tile_size, self.tile_size)
                
                if not self.grid_revealed[x][y]:
                    # Covered Tile
                    hover = rect.collidepoint(mouse_pos) and self.phase == self.PHASE_PLAYING
                    color = TILE_COVERED_HOVER if hover else TILE_COVERED
                    pygame.draw.rect(surface, color, rect.inflate(-2, -2), border_radius=2)
                    
                    # Bevel effect for 3D stone look
                    pygame.draw.line(surface, (130, 115, 100), rect.topleft, rect.topright, 2)
                    pygame.draw.line(surface, (130, 115, 100), rect.topleft, rect.bottomleft, 2)
                    pygame.draw.line(surface, (50, 40, 30), rect.bottomleft, rect.bottomright, 2)
                    pygame.draw.line(surface, (50, 40, 30), rect.topright, rect.bottomright, 2)

                    if self.grid_flagged[x][y]:
                        # Runic Ward
                        rune = self.font_numbers.render("W", True, CURSE_GLOW)
                        surface.blit(rune, rune.get_rect(center=rect.center))

                else:
                    # Revealed Tile
                    pygame.draw.rect(surface, TILE_REVEALED, rect.inflate(-2, -2), border_radius=2)

                    if self.grid_mines[x][y]:
                        # Curse
                        pygame.draw.circle(surface, CURSE_GLOW, rect.center, self.tile_size // 3)
                        pygame.draw.circle(surface, BLACK, rect.center, self.tile_size // 4)
                    elif self.grid_artifacts[x][y]:
                        # Artifact
                        pygame.draw.polygon(surface, GOLD_GLOW, [
                            (rect.centerx, rect.top + 5),
                            (rect.right - 5, rect.centery),
                            (rect.centerx, rect.bottom - 5),
                            (rect.left + 5, rect.centery)
                        ])
                    else:
                        # Number
                        num = self.grid_numbers[x][y]
                        if num > 0:
                            c = NUMBER_COLORS.get(num, WHITE)
                            nsurf = self.font_numbers.render(str(num), True, c)
                            surface.blit(nsurf, nsurf.get_rect(center=rect.center))

    def _draw_result(self, surface, mouse_pos, sx, sy):
        # Result Overlay
        overlay = pygame.Surface(self.panel_rect.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (self.panel_rect.x + sx, self.panel_rect.y + sy))

        title = self.font_title.render(self.result_title, True, self.result_color)
        surface.blit(title, (self.panel_rect.centerx - title.get_width() // 2 + sx, self.panel_rect.centery - 60 + sy))

        res = self.font_large.render(f"Secured Loot: {self.run_gold} Gold", True, GOLD_GLOW)
        surface.blit(res, (self.panel_rect.centerx - res.get_width() // 2 + sx, self.panel_rect.centery + 10 + sy))

        btn_w, btn_h = 240, 50
        self._btn_action = pygame.Rect(self.panel_rect.centerx - btn_w // 2, self.panel_rect.bottom - 100, btn_w, btn_h)
        self._draw_button(surface, self._btn_action.move(sx, sy), "Play Again", self._btn_action.collidepoint(mouse_pos))

