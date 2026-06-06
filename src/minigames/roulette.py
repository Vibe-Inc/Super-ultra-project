"""
Roulette minigame module.

Provides a Roulette casino game UI that renders over the game screen
with a green tablecloth aesthetic, similar to Blackjack.
"""

import math
import random
import time
import pygame

import src.config as cfg
from src.core.logger import logger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Tablecloth colours
TABLE_GREEN = (34, 100, 45)
TABLE_GREEN_DARK = (26, 78, 35)
TABLE_BORDER = (60, 40, 20)
FELT_PATTERN_COLOR = (38, 108, 50)

# UI colours
GOLD = (212, 175, 55)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
GREEN_TEXT = (80, 200, 80)
BUTTON_BG = (50, 45, 35)
BUTTON_HOVER = (80, 70, 55)
BUTTON_BORDER = (120, 100, 60)

# Betting chip values
BET_CHIPS = [5, 10, 25, 50]

# Standard European Roulette Wheel Numbers (Clockwise from 0)
WHEEL_NUMBERS = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]

# Standard colors
RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}

def get_number_color(num: int) -> tuple:
    if num == 0:
        return (40, 160, 60)
    if num in RED_NUMBERS:
        return (180, 40, 40)
    return (40, 40, 40)

# ---------------------------------------------------------------------------
# Roulette Game
# ---------------------------------------------------------------------------

class RouletteGame:
    """
    Modal Roulette game overlay with betting board and spinning wheel animation.
    """

    # Game phases
    PHASE_BETTING = "betting"
    PHASE_SPINNING = "spinning"
    PHASE_RESULT = "result"

    def __init__(self, app, on_close=None, player_money: int = 100):
        self.app = app
        self.on_close = on_close
        self.player_money = player_money
        self.net_change = 0
        
        self.selected_chip = 10

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        # Fonts
        self.font_large = cfg.get_font(max(12, int(36 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(26 * cfg.ui_scale())))
        self.font_small = cfg.get_font(max(8, int(20 * cfg.ui_scale())))
        self.font_tiny = cfg.get_font(max(6, int(14 * cfg.ui_scale())))
        self.font_wheel = cfg.get_font(max(7, int(17 * cfg.ui_scale())))

        # Table rect (centred, ~80 % of screen)
        table_w = int(sw * 0.82)
        table_h = int(sh * 0.82)
        self.table_rect = pygame.Rect(
            (sw - table_w) // 2,
            (sh - table_h) // 2,
            table_w,
            table_h,
        )

        # Pre-render tablecloth
        self._tablecloth_surf = self._build_tablecloth(table_w, table_h)

        # Game state
        self.phase = self.PHASE_BETTING
        self.bets = {} # key: zone_id, value: bet_amount
        self.result_text = ""
        self.result_color = WHITE
        self.winning_number = None

        # Spin animation state
        self.spin_start_time = 0
        self.spin_duration = 3.0 # seconds
        self.wheel_angle = 0.0
        self.ball_angle = 0.0
        self.start_ball_angle = 0.0
        self.target_ball_angle = 0.0

        # UI elements caching
        self._chip_rects = []
        self._bet_zones = [] # list of dicts: {'id': str, 'rect': pygame.Rect, 'label': str, 'color': tuple}
        self._btn_spin = None
        self._btn_clear = None
        self._btn_close = None
        self._btn_play = None
        self._btn_rules = None
        
        self.show_rules = False

        self._init_bet_zones()

    def _build_tablecloth(self, w: int, h: int) -> pygame.Surface:
        """Build a green felt tablecloth surface with subtle pattern."""
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill(TABLE_GREEN)

        # Diamond / cross-hatch felt pattern
        pattern_spacing = 28
        for x in range(0, w, pattern_spacing):
            for y in range(0, h, pattern_spacing):
                cx, cy = x + pattern_spacing // 2, y + pattern_spacing // 2
                r = 3
                pygame.draw.polygon(
                    surf,
                    FELT_PATTERN_COLOR,
                    [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)],
                )

        # Rounded border
        border_rect = pygame.Rect(0, 0, w, h)
        pygame.draw.rect(surf, TABLE_BORDER, border_rect, width=6, border_radius=24)
        # Inner gold trim
        inner = border_rect.inflate(-12, -12)
        pygame.draw.rect(surf, GOLD, inner, width=2, border_radius=18)

        return surf

    def _init_bet_zones(self):
        self._bet_zones = []
        
        box_w = max(36, int(42 * cfg.ui_scale()))
        box_h = max(36, int(42 * cfg.ui_scale()))
        
        # Grid layout position relative to table center
        grid_width = 12 * box_w
        grid_height = 3 * box_h
        
        # Center the grid vertically, place it on the right half
        grid_x = self.table_rect.x + self.table_rect.width - grid_width - box_w - 60
        grid_y = self.table_rect.y + 160

        # Number 0
        r_0 = pygame.Rect(grid_x - box_w, grid_y, box_w, grid_height)
        self._bet_zones.append({'id': 'num_0', 'rect': r_0, 'label': '0', 'color': get_number_color(0)})

        # Numbers 1-36
        for c in range(12):
            for r in range(3):
                num = (c * 3) + (3 - r)
                rect = pygame.Rect(grid_x + c * box_w, grid_y + r * box_h, box_w, box_h)
                self._bet_zones.append({'id': f'num_{num}', 'rect': rect, 'label': str(num), 'color': get_number_color(num)})

        # Dozens
        dozen_w = box_w * 4
        d_y = grid_y + grid_height
        self._bet_zones.append({'id': 'dozen_1', 'rect': pygame.Rect(grid_x, d_y, dozen_w, box_h), 'label': '1st 12', 'color': TABLE_GREEN_DARK})
        self._bet_zones.append({'id': 'dozen_2', 'rect': pygame.Rect(grid_x + dozen_w, d_y, dozen_w, box_h), 'label': '2nd 12', 'color': TABLE_GREEN_DARK})
        self._bet_zones.append({'id': 'dozen_3', 'rect': pygame.Rect(grid_x + dozen_w * 2, d_y, dozen_w, box_h), 'label': '3rd 12', 'color': TABLE_GREEN_DARK})

        # Outside bets
        out_w = box_w * 2
        o_y = d_y + box_h
        self._bet_zones.append({'id': 'low', 'rect': pygame.Rect(grid_x, o_y, out_w, box_h), 'label': '1-18', 'color': TABLE_GREEN_DARK})
        self._bet_zones.append({'id': 'even', 'rect': pygame.Rect(grid_x + out_w, o_y, out_w, box_h), 'label': 'EVEN', 'color': TABLE_GREEN_DARK})
        self._bet_zones.append({'id': 'red', 'rect': pygame.Rect(grid_x + out_w * 2, o_y, out_w, box_h), 'label': 'RED', 'color': (180, 40, 40)})
        self._bet_zones.append({'id': 'black', 'rect': pygame.Rect(grid_x + out_w * 3, o_y, out_w, box_h), 'label': 'BLACK', 'color': (40, 40, 40)})
        self._bet_zones.append({'id': 'odd', 'rect': pygame.Rect(grid_x + out_w * 4, o_y, out_w, box_h), 'label': 'ODD', 'color': TABLE_GREEN_DARK})
        self._bet_zones.append({'id': 'high', 'rect': pygame.Rect(grid_x + out_w * 5, o_y, out_w, box_h), 'label': '19-36', 'color': TABLE_GREEN_DARK})

    def _current_money(self) -> int:
        """Return player's gold including net change, minus bets currently placed."""
        placed = sum(self.bets.values())
        return self.player_money + self.net_change - placed

    def _can_afford(self, amount: int) -> bool:
        return self._current_money() >= amount

    def _clear_bets(self):
        if self.phase == self.PHASE_BETTING:
            self.bets.clear()

    def _place_bet(self, zone_id: str, amount: int):
        if self.phase != self.PHASE_BETTING:
            return
        if self._can_afford(amount):
            self.bets[zone_id] = self.bets.get(zone_id, 0) + amount

    def _remove_bet(self, zone_id: str, amount: int):
        if self.phase != self.PHASE_BETTING:
            return
        if zone_id in self.bets:
            self.bets[zone_id] -= amount
            if self.bets[zone_id] <= 0:
                del self.bets[zone_id]

    def _spin(self):
        total_bet = sum(self.bets.values())
        if total_bet <= 0:
            return
            
        self.phase = self.PHASE_SPINNING
        self.spin_start_time = time.time()
        
        # Determine winning number randomly
        self.winning_number = random.randint(0, 36)
        
        # Calculate target ball angle based on winning number's sector
        idx = WHEEL_NUMBERS.index(self.winning_number)
        sector_angle = (360.0 / 37.0)
        # Add random offset within the sector
        offset = random.uniform(0.1, 0.9) * sector_angle
        
        self.start_ball_angle = 0.0
        # The ball spins many times around before stopping
        rotations = 5
        final_wheel_angle = -90.0
        self.target_ball_angle = 360.0 * rotations + (idx * sector_angle + offset) + final_wheel_angle

    def _evaluate_bets(self):
        winnings = 0
        loss = 0
        win_num = self.winning_number
        
        for zone_id, amount in self.bets.items():
            won = False
            payout_mult = 0
            
            if zone_id.startswith('num_'):
                num = int(zone_id.split('_')[1])
                if num == win_num:
                    won = True
                    payout_mult = 35
            elif win_num != 0:
                if zone_id == 'red' and win_num in RED_NUMBERS:
                    won = True; payout_mult = 1
                elif zone_id == 'black' and win_num in BLACK_NUMBERS:
                    won = True; payout_mult = 1
                elif zone_id == 'even' and win_num % 2 == 0:
                    won = True; payout_mult = 1
                elif zone_id == 'odd' and win_num % 2 != 0:
                    won = True; payout_mult = 1
                elif zone_id == 'low' and 1 <= win_num <= 18:
                    won = True; payout_mult = 1
                elif zone_id == 'high' and 19 <= win_num <= 36:
                    won = True; payout_mult = 1
                elif zone_id == 'dozen_1' and 1 <= win_num <= 12:
                    won = True; payout_mult = 2
                elif zone_id == 'dozen_2' and 13 <= win_num <= 24:
                    won = True; payout_mult = 2
                elif zone_id == 'dozen_3' and 25 <= win_num <= 36:
                    won = True; payout_mult = 2
            
            if won:
                winnings += amount + (amount * payout_mult)
            else:
                loss += amount

        total_bet = sum(self.bets.values())
        round_net = winnings - total_bet
        self.net_change += round_net
        
        if round_net > 0 and hasattr(self.app, "achievement_manager"):
            self.app.achievement_manager.unlock("jackpot")
            self.app.achievement_manager.add_progress("casino_regular", 1, 25)
            
        self.phase = self.PHASE_RESULT
        if round_net > 0:
            self.result_text = f"You won +{round_net} gold!"
            self.result_color = GREEN_TEXT
        elif round_net < 0:
            self.result_text = f"You lost {abs(round_net)} gold."
            self.result_color = RED
        else:
            self.result_text = "Tie / Push."
            self.result_color = WHITE

    def _go_to_betting(self):
        if self._current_money() + sum(self.bets.values()) <= 0:
            self._close("quit")
            return
        
        # Verify valid bets, remove if unaffordable
        current = self._current_money() + sum(self.bets.values())
        total = sum(self.bets.values())
        if total > current:
            self.bets.clear()
            
        self.phase = self.PHASE_BETTING
        self.result_text = ""
        self.winning_number = None

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
        if self.show_rules:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.show_rules = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.show_rules = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._close("quit")
                return
            if self.phase == self.PHASE_BETTING:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._spin()
                elif event.key == pygame.K_c:
                    self._clear_bets()
            elif self.phase == self.PHASE_RESULT:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._go_to_betting()

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            
            if event.button == 1 and self._btn_rules and self._btn_rules.collidepoint(pos):
                self.show_rules = True
                return

            if self.phase == self.PHASE_BETTING:
                # Left click
                if event.button == 1:
                    for rect, value in self._chip_rects:
                        if rect.collidepoint(pos):
                            self.selected_chip = value
                            return
                    
                    for zone in self._bet_zones:
                        if zone['rect'].collidepoint(pos):
                            self._place_bet(zone['id'], self.selected_chip)
                            return
                            
                    if self._btn_spin and self._btn_spin.collidepoint(pos):
                        self._spin()
                    elif self._btn_clear and self._btn_clear.collidepoint(pos):
                        self._clear_bets()
                # Right click
                elif event.button == 3:
                    for zone in self._bet_zones:
                        if zone['rect'].collidepoint(pos):
                            self._remove_bet(zone['id'], self.selected_chip)
                            return
                            
            elif self.phase == self.PHASE_RESULT:
                if event.button == 1:
                    if self._btn_play and self._btn_play.collidepoint(pos):
                        self._go_to_betting()
                    elif self._btn_close and self._btn_close.collidepoint(pos):
                        self._close("quit")

    def _draw_button(self, surface, rect, text, hovered=False, text_color=None):
        bg = BUTTON_HOVER if hovered else BUTTON_BG
        pygame.draw.rect(surface, bg, rect, border_radius=8)
        pygame.draw.rect(surface, BUTTON_BORDER, rect, width=2, border_radius=8)
        tc = text_color if text_color else WHITE
        txt_surf = self.font_small.render(text, True, tc)
        txt_rect = txt_surf.get_rect(center=rect.center)
        surface.blit(txt_surf, txt_rect)

    def _draw_chip(self, surface, rect, value, hovered=False, selected=False):
        chip_colors = {5: (200, 50, 50), 10: (50, 50, 200), 25: (50, 180, 50), 50: (180, 50, 180)}
        color = chip_colors.get(value, (150, 150, 150))
        if hovered:
            color = tuple(min(255, c + 40) for c in color)

        cx, cy = rect.centerx, rect.centery
        r = rect.width // 2
        
        if selected:
            pygame.draw.circle(surface, GOLD, (cx, cy), r + 4)
            pygame.draw.circle(surface, BLACK, (cx, cy), r + 2)

        pygame.draw.circle(surface, color, (cx, cy), r)
        pygame.draw.circle(surface, WHITE, (cx, cy), r, width=2)
        pygame.draw.circle(surface, WHITE, (cx, cy), r - 4, width=1)

        txt = self.font_tiny.render(str(value), True, WHITE)
        txt_rect = txt.get_rect(center=(cx, cy))
        surface.blit(txt, txt_rect)

    def _draw_wheel(self, surface, cx, cy, radius, ball_angle=None, wheel_angle=0.0):
        # Draw outer wood ring
        pygame.draw.circle(surface, (80, 50, 30), (cx, cy), radius + 10)
        pygame.draw.circle(surface, (60, 40, 20), (cx, cy), radius + 10, width=4)
        
        # Background for the spinning track
        pygame.draw.circle(surface, (20, 20, 20), (cx, cy), radius)

        # Draw the sectors
        sector_angle = 360.0 / 37.0
        r_inner = radius * 0.5
        r_outer = radius * 0.82
        
        for i, num in enumerate(WHEEL_NUMBERS):
            start_angle = math.radians(i * sector_angle + wheel_angle)
            end_angle = math.radians((i + 1) * sector_angle + wheel_angle)
            color = get_number_color(num)
            
            # Draw segment as a polygon
            pts = [
                (cx + r_inner * math.cos(start_angle), cy + r_inner * math.sin(start_angle)),
                (cx + r_outer * math.cos(start_angle), cy + r_outer * math.sin(start_angle)),
                (cx + r_outer * math.cos(end_angle), cy + r_outer * math.sin(end_angle)),
                (cx + r_inner * math.cos(end_angle), cy + r_inner * math.sin(end_angle)),
            ]
            pygame.draw.polygon(surface, color, pts)
            pygame.draw.polygon(surface, (20, 20, 20), pts, width=1)
            
            # Draw text
            mid_angle = math.radians((i + 0.5) * sector_angle + wheel_angle)
            text_r = radius * 0.67
            txt_surf = self.font_wheel.render(str(num), True, WHITE)
            # Optional: Rotate text? Not required for readability if small enough.
            txt_rect = txt_surf.get_rect(center=(cx + text_r * math.cos(mid_angle), cy + text_r * math.sin(mid_angle)))
            surface.blit(txt_surf, txt_rect)
            
        # Draw inner decoration
        pygame.draw.circle(surface, (180, 150, 50), (cx, cy), int(r_inner))
        pygame.draw.circle(surface, (100, 80, 30), (cx, cy), int(r_inner), width=3)
        pygame.draw.circle(surface, (40, 40, 40), (cx, cy), int(r_inner * 0.4))
        
        # Draw the spinning ball
        if ball_angle is not None:
            ball_r = radius * 0.9
            ball_x = cx + ball_r * math.cos(math.radians(ball_angle))
            ball_y = cy + ball_r * math.sin(math.radians(ball_angle))
            pygame.draw.circle(surface, WHITE, (int(ball_x), int(ball_y)), max(6, int(8 * cfg.ui_scale())))
            pygame.draw.circle(surface, (200, 200, 200), (int(ball_x), int(ball_y)), max(6, int(8 * cfg.ui_scale())), width=1)

    def _draw_rules(self, surface: pygame.Surface, tr: pygame.Rect):
        """Draw the rules modal."""
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        mw, mh = int(tr.width * 0.7), int(tr.height * 0.7)
        m_rect = pygame.Rect(tr.centerx - mw // 2, tr.centery - mh // 2, mw, mh)
        pygame.draw.rect(surface, BUTTON_BG, m_rect, border_radius=12)
        pygame.draw.rect(surface, BUTTON_BORDER, m_rect, width=3, border_radius=12)

        title = self.font_large.render("Roulette Rules", True, GOLD)
        surface.blit(title, (m_rect.centerx - title.get_width() // 2, m_rect.y + 20))

        rules = [
            "Goal: Predict where the ball will land on the roulette wheel.",
            "",
            "Betting Options:",
            "  - Straight Up (Single Number): Pays 35 to 1.",
            "  - Dozens (1-12, 13-24, 25-36): Pays 2 to 1.",
            "  - Even-Money Bets (Red/Black, Even/Odd, 1-18/19-36): Pays 1 to 1.",
            "",
            "How to play:",
            "  - Select a chip value from the bottom.",
            "  - Left-click on the betting board to place your chips.",
            "  - Right-click to remove chips.",
            "  - Press 'Spin' when you're ready to play.",
            "  - Number 0 is green and generally results in a loss for outside bets."
        ]

        ty = m_rect.y + 80
        for line in rules:
            if line:
                txt = self.font_small.render(line, True, WHITE)
                surface.blit(txt, (m_rect.x + 40, ty))
            ty += 24

        hint = self.font_small.render("Click anywhere to close", True, (150, 150, 150))
        surface.blit(hint, (m_rect.centerx - hint.get_width() // 2, m_rect.bottom - 40))

    def draw(self, surface: pygame.Surface):
        # Dim background
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Tablecloth
        surface.blit(self._tablecloth_surf, self.table_rect.topleft)

        tr = self.table_rect
        mouse_pos = pygame.mouse.get_pos()

        # Title
        title = self.font_large.render("Roulette Casino", True, GOLD)
        surface.blit(title, (tr.centerx - title.get_width() // 2, tr.y + 16))

        # Rules button
        btn_w = max(90, int(120 * cfg.ui_scale()))
        btn_h = max(30, int(40 * cfg.ui_scale()))
        self._btn_rules = pygame.Rect(tr.x + 20, tr.y + 20, btn_w, btn_h)
        self._draw_button(surface, self._btn_rules, "Rules (R)", self._btn_rules.collidepoint(mouse_pos), GOLD)

        # ---- Money display ----
        right_margin = 20
        top_margin = 16
        line_spacing = 6

        money_text = self.font_medium.render(f"Gold: {self._current_money()}", True, GOLD)
        money_y = tr.y + top_margin
        surface.blit(money_text, (tr.right - money_text.get_width() - right_margin, money_y))

        if self.net_change > 0:
            nc_text = self.font_small.render(f"(+{self.net_change})", True, GREEN_TEXT)
        elif self.net_change < 0:
            nc_text = self.font_small.render(f"({self.net_change})", True, RED)
        else:
            nc_text = self.font_small.render("(+/- 0)", True, WHITE)
        nc_y = money_y + money_text.get_height() + line_spacing
        surface.blit(nc_text, (tr.right - nc_text.get_width() - right_margin, nc_y))

        # Display total bet
        total_bet = sum(self.bets.values())
        bet_text = self.font_small.render(f"Total Bet: {total_bet} gold", True, GOLD)
        bet_y = nc_y + nc_text.get_height() + line_spacing
        surface.blit(bet_text, (tr.right - bet_text.get_width() - right_margin, bet_y))

        # ---- Draw Roulette Wheel ----
        wheel_cx = tr.x + max(200, int(240 * cfg.ui_scale()))
        wheel_cy = tr.centery
        wheel_r = max(160, int(200 * cfg.ui_scale()))
        
        # Update spin animation
        if self.phase == self.PHASE_SPINNING:
            elapsed = time.time() - self.spin_start_time
            if elapsed >= self.spin_duration:
                self.ball_angle = self.target_ball_angle
                self.wheel_angle = -90.0
                if not hasattr(self, '_evaluated'):
                    self._evaluated = True
                    self._evaluate_bets()
            else:
                # Ease out cubic interpolation
                t = elapsed / self.spin_duration
                ease = 1.0 - (1.0 - t) ** 3
                self.ball_angle = self.start_ball_angle + (self.target_ball_angle - self.start_ball_angle) * ease
                # Slight wheel rotation backwards
                self.wheel_angle = ease * -90.0
        elif self.phase == self.PHASE_BETTING:
            self.wheel_angle = 0.0
            if hasattr(self, '_evaluated'):
                delattr(self, '_evaluated')

        if self.phase == self.PHASE_RESULT and self.winning_number is not None:
            # Highlight winning number in the center of the wheel
            res_str = f"Win: {self.winning_number}"
            res_surf = self.font_medium.render(res_str, True, WHITE)
            
            # draw wheel static
            self._draw_wheel(surface, wheel_cx, wheel_cy, wheel_r, self.ball_angle, self.wheel_angle)
            
            bg_rect = res_surf.get_rect(center=(wheel_cx, wheel_cy - wheel_r - 25))
            pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect.inflate(20, 10), border_radius=6)
            surface.blit(res_surf, bg_rect)
        else:
            ball_a = self.ball_angle if self.phase == self.PHASE_SPINNING else None
            self._draw_wheel(surface, wheel_cx, wheel_cy, wheel_r, ball_a, self.wheel_angle)

        # ---- Draw Betting Board ----
        for zone in self._bet_zones:
            rect = zone['rect']
            hover = rect.collidepoint(mouse_pos) and self.phase == self.PHASE_BETTING
            
            color = tuple(min(255, c + 30) for c in zone['color']) if hover else zone['color']
            
            # Highlight if winning zone
            if self.phase == self.PHASE_RESULT and self.winning_number is not None:
                win_num = self.winning_number
                z_id = zone['id']
                is_win_zone = False
                if z_id.startswith('num_') and int(z_id.split('_')[1]) == win_num: is_win_zone = True
                elif win_num != 0:
                    if z_id == 'red' and win_num in RED_NUMBERS: is_win_zone = True
                    elif z_id == 'black' and win_num in BLACK_NUMBERS: is_win_zone = True
                    elif z_id == 'even' and win_num % 2 == 0: is_win_zone = True
                    elif z_id == 'odd' and win_num % 2 != 0: is_win_zone = True
                    elif z_id == 'low' and 1 <= win_num <= 18: is_win_zone = True
                    elif z_id == 'high' and 19 <= win_num <= 36: is_win_zone = True
                    elif z_id == 'dozen_1' and 1 <= win_num <= 12: is_win_zone = True
                    elif z_id == 'dozen_2' and 13 <= win_num <= 24: is_win_zone = True
                    elif z_id == 'dozen_3' and 25 <= win_num <= 36: is_win_zone = True
                
                if is_win_zone:
                    color = tuple(min(255, c + 80) for c in zone['color'])
                    pygame.draw.rect(surface, GOLD, rect, width=0) # background glow
                    
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, WHITE, rect, width=1)
            
            txt = self.font_tiny.render(zone['label'], True, WHITE)
            txt_rect = txt.get_rect(center=rect.center)
            surface.blit(txt, txt_rect)
            
            # Draw placed bets
            amt = self.bets.get(zone['id'], 0)
            if amt > 0:
                chip_r = max(10, int(14 * cfg.ui_scale()))
                chip_rect = pygame.Rect(0, 0, chip_r * 2, chip_r * 2)
                chip_rect.center = rect.center
                self._draw_chip(surface, chip_rect, amt, False, False)

        # ---- Bottom UI Area ----
        if self.phase == self.PHASE_BETTING:
            # Chips selection
            chip_size = max(40, int(50 * cfg.ui_scale()))
            gap = 16
            chips_w = len(BET_CHIPS) * chip_size + (len(BET_CHIPS) - 1) * gap
            cx_start = tr.centerx - chips_w // 2
            cy = tr.bottom - chip_size - 40
            
            self._chip_rects = []
            for i, val in enumerate(BET_CHIPS):
                rect = pygame.Rect(cx_start + i * (chip_size + gap), cy, chip_size, chip_size)
                self._chip_rects.append((rect, val))
                hover = rect.collidepoint(mouse_pos)
                selected = (self.selected_chip == val)
                self._draw_chip(surface, rect, val, hover, selected)
                
            # Spin & Clear Buttons
            btn_w = max(100, int(130 * cfg.ui_scale()))
            btn_h = max(36, int(46 * cfg.ui_scale()))
            
            self._btn_spin = pygame.Rect(tr.right - btn_w * 2 - 40, cy + (chip_size - btn_h) // 2, btn_w, btn_h)
            self._btn_clear = pygame.Rect(tr.right - btn_w - 20, cy + (chip_size - btn_h) // 2, btn_w, btn_h)
            
            can_spin = total_bet > 0
            self._draw_button(surface, self._btn_spin, "Spin", self._btn_spin.collidepoint(mouse_pos) and can_spin, GOLD if can_spin else (120, 120, 120))
            self._draw_button(surface, self._btn_clear, "Clear", self._btn_clear.collidepoint(mouse_pos), WHITE)
            
            hint = self.font_tiny.render("L-Click: Place | R-Click: Remove | ESC: Cash out", True, (180, 180, 180))
            surface.blit(hint, (tr.x + 20, tr.bottom - hint.get_height() - 10))

        elif self.phase == self.PHASE_RESULT:
            btn_w = max(110, int(150 * cfg.ui_scale()))
            btn_h = max(36, int(46 * cfg.ui_scale()))
            btn_y = tr.bottom - btn_h - 40
            
            gap = 20
            total_w = btn_w * 2 + gap
            bx = tr.centerx - total_w // 2

            can_continue = self._current_money() + sum(self.bets.values()) > 0
            play_label = "Spin Again" if can_continue else "Broke!"
            self._btn_play = pygame.Rect(bx, btn_y, btn_w, btn_h)
            self._btn_close = pygame.Rect(bx + btn_w + gap, btn_y, btn_w, btn_h)

            self._draw_button(surface, self._btn_play, play_label,
                              self._btn_play.collidepoint(mouse_pos) and can_continue,
                              text_color=WHITE if can_continue else (120, 120, 120))
            self._draw_button(surface, self._btn_close, "Cash Out", self._btn_close.collidepoint(mouse_pos))

            res_surf = self.font_large.render(self.result_text, True, self.result_color)
            ry = btn_y - res_surf.get_height() - 20
            surface.blit(res_surf, (tr.centerx - res_surf.get_width() // 2, ry))

        if self.show_rules:
            self._draw_rules(surface, tr)
