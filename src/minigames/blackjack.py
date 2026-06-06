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
GREEN_TEXT = (80, 200, 80)
BUTTON_BG = (50, 45, 35)
BUTTON_HOVER = (80, 70, 55)
BUTTON_BORDER = (120, 100, 60)

# Betting chip values
BET_CHIPS = [5, 10, 25, 50]


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
    Modal blackjack game overlay with betting.

    Attributes:
        PHASE_BETTING (str): Betting phase identifier.
        PHASE_PLAYER_TURN (str): Player turn phase identifier.
        PHASE_DEALER_TURN (str): Dealer turn phase identifier.
        PHASE_RESULT (str): Result phase identifier.
        app: Reference to the main application instance.
        on_close (callable | None): Callback invoked when the game closes.
        player_money (int): Starting money.
        bet_amount (int): Current bet amount.
        net_change (int): Cumulative money change across rounds.
        screen_w (int): Screen width.
        screen_h (int): Screen height.
        font_large: Large font for titles.
        font_medium: Medium font for labels.
        font_small: Small font for details.
        table_rect (pygame.Rect): Rect defining the table area.
        _tablecloth_surf (pygame.Surface): Pre-rendered tablecloth surface.
        deck (list[dict]): The current deck of cards.
        player_hand (list[dict]): The player's current hand.
        dealer_hand (list[dict]): The dealer's current hand.
        phase (str): Current game phase.
        result_text (str): Text displayed in the result phase.
        result_color (tuple): Color of the result text.
        _round_outcome (str): Outcome of the current round.
        _btn_hit (pygame.Rect | None): Hit button rect.
        _btn_stand (pygame.Rect | None): Stand button rect.
        _btn_play (pygame.Rect | None): Play again button rect.
        _btn_close (pygame.Rect | None): Close button rect.
        _btn_deal (pygame.Rect | None): Deal button rect.
        _chip_rects (list): List of (rect, value) for betting chips.

    Methods:
        __init__(app, on_close=None, player_money=100):
            Initialize the blackjack game.
        _build_tablecloth(w, h):
            Build a green felt tablecloth surface with subtle pattern.
        _current_money():
            Return the player's current money.
        _can_afford(amount):
            Check if the player can afford the given bet.
        _add_bet(amount):
            Add to the current bet.
        _clear_bet():
            Reset bet to minimum.
        _deal():
            Start a round with the current bet.
        _start_round():
            Shuffle and deal initial cards.
        _player_hit():
            Player draws a card.
        _player_stand():
            Player stands; dealer plays.
        _resolve_dealer():
            Dealer draws until 17, then determine winner.
        _go_to_betting():
            Return to betting phase for a new round.
        _close(outcome):
            Invoke the on_close callback.
        handle_event(event):
            Process a pygame event.
        _draw_button(surface, rect, text, hovered=False, text_color=None):
            Draw a styled button.
        _draw_chip(surface, rect, value, hovered=False):
            Draw a betting chip.
        _draw_hand(surface, cards, x_start, y, face_up=True, hide_second=False):
            Draw a hand of cards with overlap.
        draw(surface):
            Draw the full blackjack overlay.
        _draw_betting_phase(surface, tr, mouse_pos):
            Draw the betting phase UI.
    """

    # Game phases
    PHASE_BETTING = "betting"
    PHASE_PLAYER_TURN = "player_turn"
    PHASE_DEALER_TURN = "dealer_turn"
    PHASE_RESULT = "result"

    def __init__(self, app, on_close=None, player_money: int = 100):
        self.app = app
        self.on_close = on_close
        self.player_money = player_money
        self.bet_amount = 10  # default bet
        self.net_change = 0   # cumulative money change across rounds

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
        self._round_outcome = ""  # "win", "lose", "push" for current round

        # Button rects (computed in draw, stored for event handling)
        self._btn_hit: pygame.Rect | None = None
        self._btn_stand: pygame.Rect | None = None
        self._btn_play: pygame.Rect | None = None
        self._btn_close: pygame.Rect | None = None
        self._btn_deal: pygame.Rect | None = None
        self._btn_rules: pygame.Rect | None = None
        self._chip_rects: list[tuple[pygame.Rect, int]] = []  # (rect, chip_value)

        self.show_rules = False

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

    def _current_money(self) -> int:
        """Return the player's current money (initial + net change)."""
        return self.player_money + self.net_change

    def _can_afford(self, amount: int) -> bool:
        """Check if the player can afford the given bet."""
        return self._current_money() >= amount

    def _add_bet(self, amount: int):
        """Add to the current bet if the player can afford it."""
        if self._can_afford(self.bet_amount + amount):
            self.bet_amount += amount

    def _clear_bet(self):
        """Reset bet to minimum (5)."""
        self.bet_amount = 5

    def _deal(self):
        """Start a round with the current bet."""
        if self.bet_amount < 1:
            self.bet_amount = 1
        if not self._can_afford(self.bet_amount):
            self.bet_amount = max(1, self._current_money())
        self._start_round()

    def _start_round(self):
        """Shuffle and deal initial cards."""
        self.deck = _create_deck()
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]
        self.phase = self.PHASE_PLAYER_TURN
        self.result_text = ""
        self._round_outcome = ""

        # Check for natural blackjack
        pv = _hand_value(self.player_hand)
        dv = _hand_value(self.dealer_hand)
        if pv == 21 and dv == 21:
            self._round_outcome = "push"
            self.phase = self.PHASE_RESULT
            self.result_text = "Both Blackjack — Push!"
            self.result_color = GOLD
        elif pv == 21:
            # Blackjack pays 3:2
            winnings = int(self.bet_amount * 1.5)
            self.net_change += winnings
            self._round_outcome = "win"
            self.phase = self.PHASE_RESULT
            self.result_text = f"Blackjack! +{winnings} gold!"
            self.result_color = GOLD
        elif dv == 21:
            self.net_change -= self.bet_amount
            self._round_outcome = "lose"
            self.phase = self.PHASE_RESULT
            self.result_text = f"Dealer Blackjack! -{self.bet_amount} gold!"
            self.result_color = RED

    def _player_hit(self):
        """Player draws a card."""
        if self.phase != self.PHASE_PLAYER_TURN:
            return
        self.player_hand.append(self.deck.pop())
        pv = _hand_value(self.player_hand)
        if pv > 21:
            self.net_change -= self.bet_amount
            self._round_outcome = "lose"
            self.phase = self.PHASE_RESULT
            self.result_text = f"Bust! -{self.bet_amount} gold!"
            self.result_color = RED
        elif pv == 21:
            self._player_stand()

    def _player_stand(self):
        """Player stands; dealer reveals and plays."""
        if self.phase != self.PHASE_PLAYER_TURN:
            return
        self.phase = self.PHASE_DEALER_TURN
        self._resolve_dealer()

    def _resolve_dealer(self):
        """Dealer draws until 17 or higher, then determine winner."""
        dv = _hand_value(self.dealer_hand)
        while dv < 17:
            self.dealer_hand.append(self.deck.pop())
            dv = _hand_value(self.dealer_hand)

        pv = _hand_value(self.player_hand)
        if dv > 21:
            self.net_change += self.bet_amount
            self._round_outcome = "win"
            self.result_text = f"Dealer busts! +{self.bet_amount} gold!"
            self.result_color = GREEN_TEXT
        elif pv > dv:
            self.net_change += self.bet_amount
            self._round_outcome = "win"
            self.result_text = f"You win! +{self.bet_amount} gold!"
            self.result_color = GREEN_TEXT
        elif dv > pv:
            self.net_change -= self.bet_amount
            self._round_outcome = "lose"
            self.result_text = f"Dealer wins! -{self.bet_amount} gold!"
            self.result_color = RED
        else:
            self._round_outcome = "push"
            self.result_text = "Push — tie!"
            self.result_color = WHITE

        self.phase = self.PHASE_RESULT

    def _go_to_betting(self):
        """Return to betting phase for a new round if player has money."""
        if self._current_money() <= 0:
            # Player is broke, force close
            self._close("quit")
            return
        self.bet_amount = min(10, self._current_money())
        self.phase = self.PHASE_BETTING
        self.player_hand = []
        self.dealer_hand = []
        self.result_text = ""

    def _close(self, outcome: str):
        """Invoke the on_close callback and clear the dialog reference."""
        if callable(self.on_close):
            try:
                self.on_close(outcome, self.net_change)
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
        if self.show_rules:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.show_rules = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Close rules if clicking outside the modal or clicking a close button (handled in draw or just any click closes)
                self.show_rules = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._close("quit")
                return
            if self.phase == self.PHASE_BETTING:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self._deal()
                elif event.key == pygame.K_c:
                    self._clear_bet()
            elif self.phase == self.PHASE_PLAYER_TURN:
                if event.key == pygame.K_h:
                    self._player_hit()
                elif event.key == pygame.K_s:
                    self._player_stand()
            elif self.phase == self.PHASE_RESULT:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._go_to_betting()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self._btn_rules and self._btn_rules.collidepoint(pos):
                self.show_rules = True
                return
                
            if self.phase == self.PHASE_BETTING:
                # Check chip clicks
                for rect, value in self._chip_rects:
                    if rect.collidepoint(pos):
                        self._add_bet(value)
                        break
                # Check deal button
                if self._btn_deal and self._btn_deal.collidepoint(pos):
                    self._deal()
            elif self.phase == self.PHASE_PLAYER_TURN:
                if self._btn_hit and self._btn_hit.collidepoint(pos):
                    self._player_hit()
                elif self._btn_stand and self._btn_stand.collidepoint(pos):
                    self._player_stand()
            elif self.phase == self.PHASE_RESULT:
                if self._btn_play and self._btn_play.collidepoint(pos):
                    self._go_to_betting()
                elif self._btn_close and self._btn_close.collidepoint(pos):
                    self._close("quit")

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_button(self, surface, rect, text, hovered=False, text_color=None):
        """Draw a styled button on the table."""
        bg = BUTTON_HOVER if hovered else BUTTON_BG
        pygame.draw.rect(surface, bg, rect, border_radius=8)
        pygame.draw.rect(surface, BUTTON_BORDER, rect, width=2, border_radius=8)
        tc = text_color if text_color else WHITE
        txt_surf = self.font_small.render(text, True, tc)
        txt_rect = txt_surf.get_rect(center=rect.center)
        surface.blit(txt_surf, txt_rect)

    def _draw_chip(self, surface, rect, value, hovered=False):
        """Draw a betting chip."""
        # Chip colours by value
        chip_colors = {5: (200, 50, 50), 10: (50, 50, 200), 25: (50, 180, 50), 50: (180, 50, 180)}
        color = chip_colors.get(value, (150, 150, 150))
        if hovered:
            color = tuple(min(255, c + 40) for c in color)

        # Draw chip as a circle
        cx, cy = rect.centerx, rect.centery
        r = rect.width // 2
        pygame.draw.circle(surface, color, (cx, cy), r)
        pygame.draw.circle(surface, WHITE, (cx, cy), r, width=2)
        pygame.draw.circle(surface, WHITE, (cx, cy), r - 4, width=1)

        # Value text
        txt = self.font_small.render(str(value), True, WHITE)
        txt_rect = txt.get_rect(center=(cx, cy))
        surface.blit(txt, txt_rect)

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

    def _draw_rules(self, surface: pygame.Surface, tr: pygame.Rect):
        """Draw the rules modal."""
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Modal rect
        mw, mh = int(tr.width * 0.7), int(tr.height * 0.7)
        m_rect = pygame.Rect(tr.centerx - mw // 2, tr.centery - mh // 2, mw, mh)
        pygame.draw.rect(surface, BUTTON_BG, m_rect, border_radius=12)
        pygame.draw.rect(surface, BUTTON_BORDER, m_rect, width=3, border_radius=12)

        # Title
        title = self.font_large.render("Blackjack Rules", True, GOLD)
        surface.blit(title, (m_rect.centerx - title.get_width() // 2, m_rect.y + 20))

        # Rules text
        rules = [
            "Goal: Beat the dealer's hand without going over 21.",
            "Card Values:",
            "  - Face cards (J, Q, K) are worth 10.",
            "  - Aces are worth 1 or 11, whichever makes a better hand.",
            "  - All other cards are their face value.",
            "",
            "Actions:",
            "  - Hit: Draw another card.",
            "  - Stand: Stop drawing cards and let the dealer play.",
            "",
            "Dealer Rules:",
            "  - The dealer must hit until their cards total 17 or higher.",
            "  - If you and the dealer tie, it is a 'Push' (bets are returned).",
            "  - A 'Blackjack' (an Ace and a 10-value card) pays 3:2."
        ]

        ty = m_rect.y + 80
        for line in rules:
            if line:
                txt = self.font_small.render(line, True, WHITE)
                surface.blit(txt, (m_rect.x + 40, ty))
            ty += 24

        hint = self.font_small.render("Click anywhere to close", True, (150, 150, 150))
        surface.blit(hint, (m_rect.centerx - hint.get_width() // 2, m_rect.bottom - 40))

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
        mouse_pos = pygame.mouse.get_pos()

        # Title
        title = self.font_large.render("Blackjack", True, GOLD)
        surface.blit(title, (tr.centerx - title.get_width() // 2, tr.y + 16))

        # Rules button
        btn_w = max(90, int(120 * cfg.ui_scale()))
        btn_h = max(30, int(40 * cfg.ui_scale()))
        self._btn_rules = pygame.Rect(tr.x + 20, tr.y + 20, btn_w, btn_h)
        self._draw_button(surface, self._btn_rules, "Rules (R)", self._btn_rules.collidepoint(mouse_pos), GOLD)

        # ---- Money display (top-right) ----
        # Use dynamic spacing based on actual font heights to avoid overlap on larger displays
        right_margin = 20
        top_margin = 16
        line_spacing = 6

        current_money = self._current_money()
        money_text = self.font_medium.render(f"Gold: {current_money}", True, GOLD)
        money_y = tr.y + top_margin
        surface.blit(money_text, (tr.right - money_text.get_width() - right_margin, money_y))

        # Net change indicator (positioned below money with dynamic spacing)
        if self.net_change > 0:
            nc_text = self.font_small.render(f"(+{self.net_change})", True, GREEN_TEXT)
        elif self.net_change < 0:
            nc_text = self.font_small.render(f"({self.net_change})", True, RED)
        else:
            nc_text = self.font_small.render("(+/- 0)", True, WHITE)
        nc_y = money_y + money_text.get_height() + line_spacing
        surface.blit(nc_text, (tr.right - nc_text.get_width() - right_margin, nc_y))

        # Store the bottom of the money area for other elements to reference
        self._money_area_bottom = nc_y + nc_text.get_height() + line_spacing

        # ---- Betting phase ----
        if self.phase == self.PHASE_BETTING:
            self._draw_betting_phase(surface, tr, mouse_pos)
            # Hint
            hint = self.font_small.render("ESC to leave", True, (180, 180, 180))
            surface.blit(hint, (tr.right - hint.get_width() - 20, tr.bottom - hint.get_height() - 8))
            return

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

            can_continue = self._current_money() > 0
            play_label = "Play Again" if can_continue else "Broke!"
            self._btn_play = pygame.Rect(bx, btn_y, btn_w, btn_h)
            self._btn_close = pygame.Rect(bx + btn_w + gap, btn_y, btn_w, btn_h)

            self._draw_button(surface, self._btn_play, play_label,
                              self._btn_play.collidepoint(mouse_pos) and can_continue,
                              text_color=WHITE if can_continue else (120, 120, 120))
            self._draw_button(surface, self._btn_close, "Cash Out", self._btn_close.collidepoint(mouse_pos))

            # Result text
            result_surf = self.font_large.render(self.result_text, True, self.result_color)
            ry = tr.centery - result_surf.get_height() // 2
            surface.blit(result_surf, (tr.centerx - result_surf.get_width() // 2, ry))

        # ---- Bet info (during play) ----
        # Position bet info below the money area to avoid overlap
        bet_text = self.font_small.render(f"Bet: {self.bet_amount} gold", True, GOLD)
        bet_y = getattr(self, '_money_area_bottom', tr.y + 80)
        surface.blit(bet_text, (tr.right - bet_text.get_width() - right_margin, bet_y))

        # ---- Hint ----
        hint = self.font_small.render("ESC to cash out", True, (180, 180, 180))
        surface.blit(hint, (tr.right - hint.get_width() - 20, tr.bottom - hint.get_height() - 8))

        if self.show_rules:
            self._draw_rules(surface, tr)

    def _draw_betting_phase(self, surface, tr, mouse_pos):
        """Draw the betting phase UI."""
        # Title for betting
        bet_title = self.font_large.render("Place Your Bet", True, WHITE)
        surface.blit(bet_title, (tr.centerx - bet_title.get_width() // 2, tr.y + 80))

        # Current bet display
        bet_display = self.font_large.render(f"Bet: {self.bet_amount} gold", True, GOLD)
        surface.blit(bet_display, (tr.centerx - bet_display.get_width() // 2, tr.y + 140))

        # Chips
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

        # Chip labels
        label_y = chip_y + chip_size + 8
        for i, value in enumerate(BET_CHIPS):
            cx = chip_start_x + i * (chip_size + gap)
            label = self.font_small.render(f"+{value}", True, WHITE)
            surface.blit(label, (cx + chip_size // 2 - label.get_width() // 2, label_y))

        # Deal button
        btn_w = max(140, int(200 * cfg.ui_scale()))
        btn_h = max(40, int(52 * cfg.ui_scale()))
        deal_x = tr.centerx - btn_w // 2
        deal_y = tr.y + 320

        can_deal = self._can_afford(self.bet_amount) and self.bet_amount > 0
        self._btn_deal = pygame.Rect(deal_x, deal_y, btn_w, btn_h)
        deal_color = GOLD if can_deal else (120, 120, 120)
        self._draw_button(surface, self._btn_deal, "Deal (Enter)",
                          self._btn_deal.collidepoint(mouse_pos) and can_deal,
                          text_color=deal_color)

        # Instructions
        inst_y = deal_y + btn_h + 20
        inst1 = self.font_small.render("Click chips to increase bet  |  C to clear  |  Enter to deal", True, (180, 180, 180))
        surface.blit(inst1, (tr.centerx - inst1.get_width() // 2, inst_y))

        # Show player's total money
        money_info = self.font_medium.render(f"Your gold: {self._current_money()}", True, GOLD)
        surface.blit(money_info, (tr.centerx - money_info.get_width() // 2, inst_y + 40))