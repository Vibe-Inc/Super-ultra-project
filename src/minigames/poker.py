"""
Poker minigame module.

Provides a Video Poker (Jacks or Better) casino game UI that renders over the game screen
with a green tablecloth aesthetic. Uses card images from
assets/minigames/Cards/.
"""

import os
import random
import pygame
from collections import Counter

import src.config as cfg
from src.core.logger import logger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CARDS_DIR = os.path.join("assets", "minigames", "Cards")

SUITS = ["hearts", "diamonds", "clubs", "spades"]
RANKS = ["A", "02", "03", "04", "05", "06", "07", "08", "09", "10", "J", "Q", "K"]

# Card display size (scaled from original assets)
CARD_WIDTH = 90
CARD_HEIGHT = 130

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

# ---------------------------------------------------------------------------
# Card / Deck helpers
# ---------------------------------------------------------------------------

def _rank_value(rank: str) -> int:
    if rank == "A": return 14
    if rank == "K": return 13
    if rank == "Q": return 12
    if rank == "J": return 11
    return int(rank)

def _create_deck() -> list[dict]:
    """Create a standard 52-card deck (no jokers)."""
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append({"suit": suit, "rank": rank})
    random.shuffle(deck)
    return deck

def _evaluate_hand(hand: list[dict]) -> tuple[str, int]:
    """Evaluate a 5-card poker hand and return (hand_name, multiplier)."""
    ranks = [_rank_value(card["rank"]) for card in hand]
    suits = [card["suit"] for card in hand]
    
    ranks.sort(reverse=True)
    
    is_flush = len(set(suits)) == 1
    
    # Check straight
    is_straight = False
    if len(set(ranks)) == 5 and ranks[0] - ranks[-1] == 4:
        is_straight = True
    # Special case for A, 2, 3, 4, 5 straight
    if ranks == [14, 5, 4, 3, 2]:
        is_straight = True
        
    counts = Counter(ranks)
    freqs = list(counts.values())
    freqs.sort(reverse=True)
    
    if is_flush and is_straight:
        if ranks[0] == 14 and ranks[1] == 13: # A, K, Q, J, 10
            return "Royal Flush", 250
        return "Straight Flush", 50
    if freqs == [4, 1]:
        return "Four of a Kind", 25
    if freqs == [3, 2]:
        return "Full House", 9
    if is_flush:
        return "Flush", 6
    if is_straight:
        return "Straight", 4
    if freqs == [3, 1, 1]:
        return "Three of a Kind", 3
    if freqs == [2, 2, 1]:
        return "Two Pair", 2
    if freqs == [2, 1, 1, 1]:
        # Check if pair is Jacks or Better (11 or higher)
        for r, count in counts.items():
            if count == 2 and r >= 11:
                return "Jacks or Better", 1
    
    return "High Card", 0


# ---------------------------------------------------------------------------
# Image cache
# ---------------------------------------------------------------------------

_image_cache: dict[str, pygame.Surface] = {}

def _load_card_image(filename: str) -> pygame.Surface:
    """Load and cache a card image, scaled to CARD_WIDTH x CARD_HEIGHT."""
    if filename in _image_cache:
        return _image_cache[filename]
    path = os.path.join(CARDS_DIR, filename + ".png")
    try:
        img = pygame.transform.scale(pygame.image.load(path), (CARD_WIDTH, CARD_HEIGHT))
    except (FileNotFoundError, pygame.error):
        # Fallback: coloured rectangle
        img = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        img.fill((180, 180, 180))
        pygame.draw.rect(img, (100, 100, 100), img.get_rect(), 2)
    _image_cache[filename] = img
    return img

def _card_face_image(card: dict) -> pygame.Surface:
    """Return the face-up image for a card dict."""
    filename = f"card_{card['suit']}_{card['rank']}"
    return _load_card_image(filename)

def _card_back_image() -> pygame.Surface:
    """Return the card-back image."""
    return _load_card_image("card_back")


# ---------------------------------------------------------------------------
# Poker Game
# ---------------------------------------------------------------------------

class PokerGame:
    """
    Modal Video Poker game overlay with betting.
    """

    # Game phases
    PHASE_BETTING = "betting"
    PHASE_HOLD = "hold"
    PHASE_RESULT = "result"

    def __init__(self, app, on_close=None, player_money: int = 100):
        self.app = app
        self.on_close = on_close
        self.player_money = player_money
        self.bet_amount = 10
        self.net_change = 0

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        # Fonts
        self.font_large = cfg.get_font(max(12, int(36 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(26 * cfg.ui_scale())))
        self.font_small = cfg.get_font(max(8, int(20 * cfg.ui_scale())))

        # Table rect
        table_w = int(sw * 0.82)
        table_h = int(sh * 0.82)
        self.table_rect = pygame.Rect(
            (sw - table_w) // 2,
            (sh - table_h) // 2,
            table_w,
            table_h,
        )

        self._tablecloth_surf = self._build_tablecloth(table_w, table_h)

        # Game state
        self.deck: list[dict] = []
        self.player_hand: list[dict] = []
        self.held_cards: list[bool] = [False] * 5
        self.phase = self.PHASE_BETTING
        self.result_text = ""
        self.result_color = WHITE
        self.show_rules = False

        # Button rects
        self._btn_action: pygame.Rect | None = None
        self._btn_close: pygame.Rect | None = None
        self._btn_rules: pygame.Rect | None = None
        self._chip_rects: list[tuple[pygame.Rect, int]] = []
        self._card_rects: list[pygame.Rect] = []

    def _build_tablecloth(self, w: int, h: int) -> pygame.Surface:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill(TABLE_GREEN)
        pattern_spacing = 28
        for x in range(0, w, pattern_spacing):
            for y in range(0, h, pattern_spacing):
                cx, cy = x + pattern_spacing // 2, y + pattern_spacing // 2
                r = 3
                pygame.draw.polygon(
                    surf, FELT_PATTERN_COLOR,
                    [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)],
                )
        border_rect = pygame.Rect(0, 0, w, h)
        pygame.draw.rect(surf, TABLE_BORDER, border_rect, width=6, border_radius=24)
        inner = border_rect.inflate(-12, -12)
        pygame.draw.rect(surf, GOLD, inner, width=2, border_radius=18)
        return surf

    def _current_money(self) -> int:
        return self.player_money + self.net_change

    def _can_afford(self, amount: int) -> bool:
        return self._current_money() >= amount

    def _add_bet(self, amount: int):
        if self._can_afford(self.bet_amount + amount):
            self.bet_amount += amount

    def _clear_bet(self):
        self.bet_amount = 5

    def _deal(self):
        if self.bet_amount < 1:
            self.bet_amount = 1
        if not self._can_afford(self.bet_amount):
            self.bet_amount = max(1, self._current_money())
            
        self.net_change -= self.bet_amount
        self.deck = _create_deck()
        self.player_hand = [self.deck.pop() for _ in range(5)]
        self.held_cards = [False] * 5
        self.phase = self.PHASE_HOLD
        self.result_text = ""

    def _draw_cards(self):
        # Replace unheld cards
        for i in range(5):
            if not self.held_cards[i]:
                self.player_hand[i] = self.deck.pop()
                
        # Evaluate hand
        hand_name, mult = _evaluate_hand(self.player_hand)
        winnings = self.bet_amount * mult
        self.net_change += winnings
        
        if winnings > 0 and hasattr(self.app, "achievement_manager"):
            self.app.achievement_manager.add_progress("card_shark", 1, 5)
            self.app.achievement_manager.add_progress("casino_regular", 1, 25)
        
        self.phase = self.PHASE_RESULT
        if winnings > 0:
            self.result_text = f"{hand_name}! You won +{winnings} gold!"
            self.result_color = GOLD
        else:
            self.result_text = "No win."
            self.result_color = RED

    def _go_to_betting(self):
        if self._current_money() <= 0:
            self._close("quit")
            return
        self.bet_amount = min(10, self._current_money())
        self.phase = self.PHASE_BETTING
        self.player_hand = []
        self.result_text = ""

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
                    self._deal()
                elif event.key == pygame.K_c:
                    self._clear_bet()
            elif self.phase == self.PHASE_HOLD:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._draw_cards()
                # 1-5 to toggle hold
                for i in range(5):
                    if event.key == getattr(pygame, f"K_{i+1}"):
                        self.held_cards[i] = not self.held_cards[i]
            elif self.phase == self.PHASE_RESULT:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._go_to_betting()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self._btn_rules and self._btn_rules.collidepoint(pos):
                self.show_rules = True
                return

            if self.phase == self.PHASE_BETTING:
                for rect, value in self._chip_rects:
                    if rect.collidepoint(pos):
                        self._add_bet(value)
                        break
                if self._btn_action and self._btn_action.collidepoint(pos):
                    self._deal()
            elif self.phase == self.PHASE_HOLD:
                for i, rect in enumerate(self._card_rects):
                    if rect.collidepoint(pos):
                        self.held_cards[i] = not self.held_cards[i]
                if self._btn_action and self._btn_action.collidepoint(pos):
                    self._draw_cards()
            elif self.phase == self.PHASE_RESULT:
                if self._btn_action and self._btn_action.collidepoint(pos):
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

    def _draw_chip(self, surface, rect, value, hovered=False):
        chip_colors = {5: (200, 50, 50), 10: (50, 50, 200), 25: (50, 180, 50), 50: (180, 50, 180)}
        color = chip_colors.get(value, (150, 150, 150))
        if hovered:
            color = tuple(min(255, c + 40) for c in color)
        cx, cy = rect.centerx, rect.centery
        r = rect.width // 2
        pygame.draw.circle(surface, color, (cx, cy), r)
        pygame.draw.circle(surface, WHITE, (cx, cy), r, width=2)
        pygame.draw.circle(surface, WHITE, (cx, cy), r - 4, width=1)
        txt = self.font_small.render(str(value), True, WHITE)
        txt_rect = txt.get_rect(center=(cx, cy))
        surface.blit(txt, txt_rect)
        
    def _draw_rules(self, surface: pygame.Surface, tr: pygame.Rect):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        mw, mh = int(tr.width * 0.7), int(tr.height * 0.7)
        m_rect = pygame.Rect(tr.centerx - mw // 2, tr.centery - mh // 2, mw, mh)
        pygame.draw.rect(surface, BUTTON_BG, m_rect, border_radius=12)
        pygame.draw.rect(surface, BUTTON_BORDER, m_rect, width=3, border_radius=12)

        title = self.font_large.render("Video Poker Rules", True, GOLD)
        surface.blit(title, (m_rect.centerx - title.get_width() // 2, m_rect.y + 20))

        rules = [
            "Goal: Make the best 5-card poker hand.",
            "",
            "How to play:",
            "  - Place your bet and click 'Deal'.",
            "  - You are dealt 5 cards.",
            "  - Click on cards to 'Hold' them.",
            "  - Click 'Draw' to replace unheld cards.",
            "  - Get paid based on your final hand.",
            "",
            "Payouts:",
            "  - Royal Flush: 250x",
            "  - Straight Flush: 50x",
            "  - Four of a Kind: 25x",
            "  - Full House: 9x",
            "  - Flush: 6x",
            "  - Straight: 4x",
            "  - Three of a Kind: 3x",
            "  - Two Pair: 2x",
            "  - Jacks or Better: 1x"
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
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        surface.blit(self._tablecloth_surf, self.table_rect.topleft)

        tr = self.table_rect
        mouse_pos = pygame.mouse.get_pos()

        title = self.font_large.render("Video Poker", True, GOLD)
        surface.blit(title, (tr.centerx - title.get_width() // 2, tr.y + 16))

        # Rules button
        btn_w = max(90, int(120 * cfg.ui_scale()))
        btn_h = max(30, int(40 * cfg.ui_scale()))
        self._btn_rules = pygame.Rect(tr.x + 20, tr.y + 20, btn_w, btn_h)
        self._draw_button(surface, self._btn_rules, "Rules (R)", self._btn_rules.collidepoint(mouse_pos), GOLD)

        # Money display
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
        
        _money_area_bottom = nc_y + nc_text.get_height() + line_spacing

        if self.phase == self.PHASE_BETTING:
            bet_title = self.font_large.render("Place Your Bet", True, WHITE)
            surface.blit(bet_title, (tr.centerx - bet_title.get_width() // 2, tr.y + 80))

            bet_display = self.font_large.render(f"Bet: {self.bet_amount} gold", True, GOLD)
            surface.blit(bet_display, (tr.centerx - bet_display.get_width() // 2, tr.y + 140))

            chip_size = max(50, int(64 * cfg.ui_scale()))
            gap = 20
            total_chips_w = len(BET_CHIPS) * chip_size + (len(BET_CHIPS) - 1) * gap
            chip_start_x = tr.centerx - total_chips_w // 2
            chip_y = tr.y + 200

            self._chip_rects = []
            for i, value in enumerate(BET_CHIPS):
                cx = chip_start_x + i * (chip_size + gap)
                rect = pygame.Rect(cx, chip_y, chip_size, chip_size)
                self._chip_rects.append((rect, value))
                self._draw_chip(surface, rect, value, rect.collidepoint(mouse_pos))

            label_y = chip_y + chip_size + 8
            for i, value in enumerate(BET_CHIPS):
                cx = chip_start_x + i * (chip_size + gap)
                label = self.font_small.render(f"+{value}", True, WHITE)
                surface.blit(label, (cx + chip_size // 2 - label.get_width() // 2, label_y))

            btn_w = max(140, int(200 * cfg.ui_scale()))
            btn_h = max(40, int(52 * cfg.ui_scale()))
            deal_x = tr.centerx - btn_w // 2
            deal_y = tr.y + 320

            can_deal = self._can_afford(self.bet_amount) and self.bet_amount > 0
            self._btn_action = pygame.Rect(deal_x, deal_y, btn_w, btn_h)
            deal_color = GOLD if can_deal else (120, 120, 120)
            self._draw_button(surface, self._btn_action, "Deal (Enter)",
                              self._btn_action.collidepoint(mouse_pos) and can_deal,
                              text_color=deal_color)

            hint = self.font_small.render("ESC to leave", True, (180, 180, 180))
            surface.blit(hint, (tr.right - hint.get_width() - 20, tr.bottom - hint.get_height() - 8))
            
        else:
            # Drawing cards
            bet_text = self.font_small.render(f"Bet: {self.bet_amount} gold", True, GOLD)
            surface.blit(bet_text, (tr.right - bet_text.get_width() - right_margin, _money_area_bottom))
            
            card_gap = 10
            total_w = 5 * CARD_WIDTH + 4 * card_gap
            start_x = tr.centerx - total_w // 2
            start_y = tr.centery - CARD_HEIGHT // 2

            self._card_rects = []
            for i, card in enumerate(self.player_hand):
                cx = start_x + i * (CARD_WIDTH + card_gap)
                rect = pygame.Rect(cx, start_y, CARD_WIDTH, CARD_HEIGHT)
                self._card_rects.append(rect)
                img = _card_face_image(card)
                surface.blit(img, (cx, start_y))
                
                # Draw hold label
                if self.held_cards[i]:
                    hold_txt = self.font_medium.render("HELD", True, RED)
                    surface.blit(hold_txt, (cx + CARD_WIDTH//2 - hold_txt.get_width()//2, start_y + CARD_HEIGHT + 10))

            btn_w = max(140, int(200 * cfg.ui_scale()))
            btn_h = max(40, int(52 * cfg.ui_scale()))
            btn_y = tr.bottom - btn_h - 40

            if self.phase == self.PHASE_HOLD:
                self._btn_action = pygame.Rect(tr.centerx - btn_w // 2, btn_y, btn_w, btn_h)
                self._draw_button(surface, self._btn_action, "Draw (Enter)", self._btn_action.collidepoint(mouse_pos))
                
                inst = self.font_small.render("Click cards to hold/unhold them", True, WHITE)
                surface.blit(inst, (tr.centerx - inst.get_width() // 2, btn_y - 40))
                
            elif self.phase == self.PHASE_RESULT:
                gap = 20
                total_btn_w = btn_w * 2 + gap
                bx = tr.centerx - total_btn_w // 2
                
                can_continue = self._current_money() > 0
                play_label = "Play Again" if can_continue else "Broke!"
                self._btn_action = pygame.Rect(bx, btn_y, btn_w, btn_h)
                self._btn_close = pygame.Rect(bx + btn_w + gap, btn_y, btn_w, btn_h)
                
                self._draw_button(surface, self._btn_action, play_label,
                                  self._btn_action.collidepoint(mouse_pos) and can_continue,
                                  text_color=WHITE if can_continue else (120, 120, 120))
                self._draw_button(surface, self._btn_close, "Cash Out", self._btn_close.collidepoint(mouse_pos))
                
                # Result text
                res_surf = self.font_large.render(self.result_text, True, self.result_color)
                ry = start_y - res_surf.get_height() - 30
                surface.blit(res_surf, (tr.centerx - res_surf.get_width() // 2, ry))

            hint = self.font_small.render("ESC to cash out", True, (180, 180, 180))
            surface.blit(hint, (tr.right - hint.get_width() - 20, tr.bottom - hint.get_height() - 8))

        if self.show_rules:
            self._draw_rules(surface, tr)
