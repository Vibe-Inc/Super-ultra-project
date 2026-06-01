"""
Blackjack minigame module.

Provides a blackjack card game UI that renders over the game screen
with a green tablecloth aesthetic. Uses card images from
assets/minigames/Cards/.
"""

import os
import random
import pygame

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
BUTTON_BG = (50, 45, 35)
BUTTON_HOVER = (80, 70, 55)
BUTTON_BORDER = (120, 100, 60)


# ---------------------------------------------------------------------------
# Card / Deck helpers
# ---------------------------------------------------------------------------

def _card_value(rank: str) -> list[int]:
    """Return possible blackjack values for a rank."""
    if rank == "A":
        return [1, 11]
    if rank in ("J", "Q", "K"):
        return [10]
    return [int(rank)]


def _hand_value(cards: list[dict]) -> int:
    """Compute the best blackjack hand value (handles aces)."""
    total = 0
    aces = 0
    for card in cards:
        vals = _card_value(card["rank"])
        if len(vals) == 2:
            aces += 1
            total += 11  # start by counting ace as 11
        else:
            total += vals[0]
    # Convert aces from 11 to 1 if busting
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total


def _create_deck() -> list[dict]:
    """Create a standard 52-card deck (no jokers)."""
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append({"suit": suit, "rank": rank})
    random.shuffle(deck)
    return deck


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
# Blackjack Game
# ---------------------------------------------------------------------------

class BlackjackGame:
    """
    Modal blackjack game overlay.

    Usage::

        game = BlackjackGame(app, on_close=callback)
        # In the game loop:
        game.handle_event(event)
        game.draw(screen)

    The *on_close* callback receives a single string argument:
    ``"win"``, ``"lose"``, ``"push"``, or ``"quit"``.
    """

    # Game phases
    PHASE_BETTING = "betting"
    PHASE_PLAYER_TURN = "player_turn"
    PHASE_DEALER_TURN = "dealer_turn"
    PHASE_RESULT = "result"

    def __init__(self, app, on_close=None, bet_amount: int = 10):
        self.app = app
        self.on_close = on_close
        self.bet_amount = bet_amount

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        # Fonts
        self.font_large = cfg.get_font(max(12, int(36 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(26 * cfg.ui_scale())))
        self.font_small = cfg.get_font(max(8, int(20 * cfg.ui_scale())))

        # Table rect (centred, ~80 % of screen)
        table_w = int(sw * 0.82)
        table_h = int(sh * 0.82)
        self.table_rect = pygame.Rect(
            (sw - table_w) // 2,
            (sh - table_h) // 2,
            table_w,
            table_h,
        )

        # Pre-render tablecloth pattern surface
        self._tablecloth_surf = self._build_tablecloth(table_w, table_h)

        # Game state
        self.deck: list[dict] = []
        self.player_hand: list[dict] = []
        self.dealer_hand: list[dict] = []
        self.phase = self.PHASE_BETTING
        self.result_text = ""
        self.result_color = WHITE
        self._dealer_reveal_timer = 0.0
        self._dealer_reveal_interval = 0.5  # seconds between dealer cards

        # Button rects (computed in draw, stored for event handling)
        self._btn_hit: pygame.Rect | None = None
        self._btn_stand: pygame.Rect | None = None
        self._btn_play: pygame.Rect | None = None
        self._btn_close: pygame.Rect | None = None

        # Start the first round automatically
        self._start_round()

    # ------------------------------------------------------------------
    # Tablecloth rendering
    # ------------------------------------------------------------------

    def _build_tablecloth(self, w: int, h: int) -> pygame.Surface:
        """Build a green felt tablecloth surface with subtle pattern."""
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Base green
        surf.fill(TABLE_GREEN)

        # Diamond / cross-hatch felt pattern
        pattern_spacing = 28
        for x in range(0, w, pattern_spacing):
            for y in range(0, h, pattern_spacing):
                # Small diamond shape
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

    # ------------------------------------------------------------------
    # Game logic
    # ------------------------------------------------------------------

    def _start_round(self):
        """Shuffle and deal initial cards."""
        self.deck = _create_deck()
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]
        self.phase = self.PHASE_PLAYER_TURN
        self.result_text = ""

        # Check for natural blackjack
        pv = _hand_value(self.player_hand)
        dv = _hand_value(self.dealer_hand)
        if pv == 21 and dv == 21:
            self.phase = self.PHASE_RESULT
            self.result_text = "Both Blackjack — Push!"
            self.result_color = GOLD
        elif pv == 21:
            self.phase = self.PHASE_RESULT
            self.result_text = "Blackjack! You win!"
            self.result_color = GOLD
        elif dv == 21:
            self.phase = self.PHASE_RESULT
            self.result_text = "Dealer Blackjack! You lose!"
            self.result_color = RED

    def _player_hit(self):
        """Player draws a card."""
        if self.phase != self.PHASE_PLAYER_TURN:
            return
        self.player_hand.append(self.deck.pop())
        pv = _hand_value(self.player_hand)
        if pv > 21:
            self.phase = self.PHASE_RESULT
            self.result_text = "Bust! You lose!"
            self.result_color = RED
        elif pv == 21:
            self._player_stand()

    def _player_stand(self):
        """Player stands; dealer reveals and plays."""
        if self.phase != self.PHASE_PLAYER_TURN:
            return
        self.phase = self.PHASE_DEALER_TURN
        self._dealer_reveal_timer = 0.0
        self._resolve_dealer()

    def _resolve_dealer(self):
        """Dealer draws until 17 or higher, then determine winner."""
        dv = _hand_value(self.dealer_hand)
        while dv < 17:
            self.dealer_hand.append(self.deck.pop())
            dv = _hand_value(self.dealer_hand)

        pv = _hand_value(self.player_hand)
        if dv > 21:
            self.result_text = "Dealer busts! You win!"
            self.result_color = GOLD
        elif pv > dv:
            self.result_text = "You win!"
            self.result_color = GOLD
        elif dv > pv:
            self.result_text = "Dealer wins!"
            self.result_color = RED
        else:
            self.result_text = "Push — tie!"
            self.result_color = WHITE

        self.phase = self.PHASE_RESULT

    def _close(self, outcome: str):
        """Invoke the on_close callback and clear the dialog reference."""
        if callable(self.on_close):
            try:
                self.on_close(outcome)
            except Exception:
                pass
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event):
        """Process a pygame event for the blackjack UI."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._close("quit")
                return
            if self.phase == self.PHASE_PLAYER_TURN:
                if event.key == pygame.K_h:
                    self._player_hit()
                elif event.key == pygame.K_s:
                    self._player_stand()
            elif self.phase == self.PHASE_RESULT:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._start_round()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.phase == self.PHASE_PLAYER_TURN:
                if self._btn_hit and self._btn_hit.collidepoint(pos):
                    self._player_hit()
                elif self._btn_stand and self._btn_stand.collidepoint(pos):
                    self._player_stand()
            elif self.phase == self.PHASE_RESULT:
                if self._btn_play and self._btn_play.collidepoint(pos):
                    self._start_round()
                elif self._btn_close and self._btn_close.collidepoint(pos):
                    self._close("quit")

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_button(self, surface, rect, text, hovered=False):
        """Draw a styled button on the table."""
        bg = BUTTON_HOVER if hovered else BUTTON_BG
        pygame.draw.rect(surface, bg, rect, border_radius=8)
        pygame.draw.rect(surface, BUTTON_BORDER, rect, width=2, border_radius=8)
        txt_surf = self.font_small.render(text, True, WHITE)
        txt_rect = txt_surf.get_rect(center=rect.center)
        surface.blit(txt_surf, txt_rect)

    def _draw_hand(self, surface, cards, x_start, y, face_up=True, hide_second=False):
        """Draw a hand of cards with slight overlap."""
        overlap = int(CARD_WIDTH * 0.45)
        for i, card in enumerate(cards):
            cx = x_start + i * overlap
            if hide_second and i == 1:
                img = _card_back_image()
            elif face_up:
                img = _card_face_image(card)
            else:
                img = _card_back_image()
            surface.blit(img, (cx, y))

    # ------------------------------------------------------------------
    # Main draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface):
        """Draw the full blackjack overlay."""
        # Dim background
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Tablecloth
        surface.blit(self._tablecloth_surf, self.table_rect.topleft)

        tr = self.table_rect  # shorthand

        # Title
        title = self.font_large.render("Blackjack", True, GOLD)
        surface.blit(title, (tr.centerx - title.get_width() // 2, tr.y + 16))

        # ---- Dealer area ----
        dealer_label = self.font_medium.render("Dealer", True, WHITE)
        surface.blit(dealer_label, (tr.x + 30, tr.y + 60))

        if self.phase == self.PHASE_DEALER_TURN or self.phase == self.PHASE_RESULT:
            dv = _hand_value(self.dealer_hand)
            dv_text = self.font_small.render(f"({dv})", True, WHITE)
            surface.blit(dv_text, (tr.x + 30 + dealer_label.get_width() + 10, tr.y + 68))
            self._draw_hand(surface, self.dealer_hand, tr.x + 30, tr.y + 95, face_up=True)
        else:
            # Show first card, hide second
            dv_first = _hand_value([self.dealer_hand[0]]) if self.dealer_hand else 0
            dv_text = self.font_small.render(f"({dv_first} + ?)", True, WHITE)
            surface.blit(dv_text, (tr.x + 30 + dealer_label.get_width() + 10, tr.y + 68))
            self._draw_hand(surface, self.dealer_hand, tr.x + 30, tr.y + 95, hide_second=True)

        # ---- Player area ----
        player_y = tr.y + tr.height - CARD_HEIGHT - 120
        player_label = self.font_medium.render("Player", True, WHITE)
        surface.blit(player_label, (tr.x + 30, player_y - 35))

        pv = _hand_value(self.player_hand)
        pv_text = self.font_small.render(f"({pv})", True, WHITE)
        surface.blit(pv_text, (tr.x + 30 + player_label.get_width() + 10, player_y - 28))

        self._draw_hand(surface, self.player_hand, tr.x + 30, player_y, face_up=True)

        # ---- Buttons ----
        mouse_pos = pygame.mouse.get_pos()
        btn_w = max(110, int(150 * cfg.ui_scale()))
        btn_h = max(36, int(46 * cfg.ui_scale()))
        btn_y = tr.y + tr.height - btn_h - 24

        if self.phase == self.PHASE_PLAYER_TURN:
            gap = 16
            total_w = btn_w * 2 + gap
            bx = tr.centerx - total_w // 2

            self._btn_hit = pygame.Rect(bx, btn_y, btn_w, btn_h)
            self._btn_stand = pygame.Rect(bx + btn_w + gap, btn_y, btn_w, btn_h)

            self._draw_button(surface, self._btn_hit, "Hit (H)", self._btn_hit.collidepoint(mouse_pos))
            self._draw_button(surface, self._btn_stand, "Stand (S)", self._btn_stand.collidepoint(mouse_pos))

        elif self.phase == self.PHASE_RESULT:
            gap = 16
            total_w = btn_w * 2 + gap
            bx = tr.centerx - total_w // 2

            self._btn_play = pygame.Rect(bx, btn_y, btn_w, btn_h)
            self._btn_close = pygame.Rect(bx + btn_w + gap, btn_y, btn_w, btn_h)

            self._draw_button(surface, self._btn_play, "Play Again", self._btn_play.collidepoint(mouse_pos))
            self._draw_button(surface, self._btn_close, "Leave Table", self._btn_close.collidepoint(mouse_pos))

            # Result text
            result_surf = self.font_large.render(self.result_text, True, self.result_color)
            ry = tr.centery - result_surf.get_height() // 2
            surface.blit(result_surf, (tr.centerx - result_surf.get_width() // 2, ry))

        # ---- Bet info ----
        bet_text = self.font_small.render(f"Bet: {self.bet_amount} gold", True, GOLD)
        surface.blit(bet_text, (tr.right - bet_text.get_width() - 20, tr.y + 20))

        # ---- Hint ----
        hint = self.font_small.render("ESC to leave", True, (180, 180, 180))
        surface.blit(hint, (tr.right - hint.get_width() - 20, tr.bottom - hint.get_height() - 8))