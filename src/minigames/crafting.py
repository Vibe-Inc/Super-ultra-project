"""
Crafting "Tempering" minigame.

Triggered when the player takes a freshly-crafted tool, armor or weapon
from the workbench output slot.  The minigame is a short, three-strike
timing challenge that biases the item's rolled crafting tier up or down
based on performance.

Mechanics
---------

A horizontal anvil bar contains three zones:

* **Bullseye** (gold)   -- small sweet spot in the centre.
* **Good**    (silver) -- ring around the bullseye.
* **Miss**    (red)    -- the two outer ends of the bar.

A hammer cursor sweeps back and forth across the bar; the player clicks
(or presses SPACE) to strike the anvil and lock in the position.  Three
strikes are performed in a row.  After the third strike the combined
score is converted into a tier shift that is applied to the crafted
item.

Score -> shift
~~~~~~~~~~~~~~

The strike positions are scored individually and then summed:

* Bullseye = 2 points
* Good     = 1 point
* Miss     = 0 points

Maximum score is 6 (three bullseyes).  The total is mapped to a tier
shift relative to the rolled tier:

* score >= 5  : shift up by 1 tier
* score 3..4  : keep the rolled tier (no shift), +50% bonus XP
* score 1..2  : keep the rolled tier, normal XP
* score  0   : shift down by 1 tier

Tier shifts are clamped to ``["horrendous", "legendary"]``.  The shift
direction is shown to the player at the end of the minigame along with
the final item tier and a celebratory or commiserating message.

The minigame is skippable: a "Skip" button and ESC key both close it
without changing the rolled tier.  This keeps the feature purely
optional -- a player who dislikes the minigame can never be forced to
play it.

Integration
-----------

The minigame is launched from
:meth:`src.inventory.system.CraftingGrid.inventory_interactions` when the
player clicks the workbench output slot.  It receives the freshly
crafted item and a callback that, on close, places the (possibly
re-tiered) item into the player's cursor and consumes the grid
ingredients.  The instance is owned by
:meth:`src.core.game.Game.crafting_minigame`, mirroring the
``blackjack_game`` pattern.
"""

import math
import random
import pygame

import src.config as cfg
from src.core.logger import logger
from database.crafting_tiers_db import TIER_ORDER, get_tier_name

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Anvil / forge palette
ANVIL_BG          = (28, 22, 18)
ANVIL_BG_DARK     = (20, 15, 12)
ANVIL_BORDER      = (90, 60, 30)
ANVIL_BORDER_LIGHT= (140, 100, 50)
ANVIL_GLOW        = (180, 90, 30)

BAR_BG            = (50, 35, 22)
BAR_MISS          = (140, 40, 40)
BAR_GOOD          = (170, 170, 175)
BAR_BULLSEYE      = (255, 200, 60)
BAR_CURSOR        = (245, 245, 245)
BAR_CURSOR_GLOW   = (255, 255, 200)

TEXT_LIGHT        = (235, 225, 200)
TEXT_DIM          = (160, 145, 120)
TEXT_GOLD         = (255, 200, 90)
TEXT_BAD          = (220, 80, 80)
TEXT_GOOD         = (120, 220, 130)

BUTTON_BG         = (60, 40, 25)
BUTTON_HOVER      = (95, 65, 35)
BUTTON_BORDER     = (160, 110, 50)

NUM_STRIKES       = 3

# Sweep speed in pixels per second (cursor bounces between the two ends).
# Tuned up from 620 to 820 so the existing Tempering / "Tending the
# Fire" challenge is meaningfully tougher for iron-tier crafts.
SWEEP_SPEED       = 820.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _shift_tier(tier_id: str, direction: int) -> str:
    """Return the tier ``direction`` steps away from ``tier_id``.

    ``direction`` is ``+1`` (better) or ``-1`` (worse).  The result is
    clamped to the bounds of :data:`TIER_ORDER` so a legendary cannot
    be shifted above legendary and a horrendous cannot be shifted
    below horrendous.
    """
    if tier_id not in TIER_ORDER:
        return tier_id
    idx = TIER_ORDER.index(tier_id)
    idx = max(0, min(len(TIER_ORDER) - 1, idx + direction))
    return TIER_ORDER[idx]


def _zone_at(x: float, bar_x: int, bar_w: int) -> str:
    """Classify cursor ``x`` into ``"bullseye"``, ``"good"`` or ``"miss"``.

    The bar is divided as follows (symmetric around the centre):

    * Centre 22 %  -> bullseye
    * Next 28 %    -> good
    * Outer 22 %   -> miss
    """
    if bar_w <= 0:
        return "miss"
    rel = (x - bar_x) / float(bar_w)
    rel = max(0.0, min(1.0, rel))
    dist = abs(rel - 0.5) * 2.0  # 0 at centre, 1 at the edges
    if dist <= 0.22:
        return "bullseye"
    if dist <= 0.50:
        return "good"
    return "miss"


def _zone_color(zone: str) -> tuple:
    return {
        "bullseye": BAR_BULLSEYE,
        "good":     BAR_GOOD,
        "miss":     BAR_MISS,
    }.get(zone, BAR_MISS)


# ---------------------------------------------------------------------------
# Crafting Minigame
# ---------------------------------------------------------------------------

class CraftingMinigame:
    """Modal "Tempering" timing minigame overlay.

    Attributes:
        PHASE_INTRO   (str): Brief intro phase before the first strike.
        PHASE_STRIKE  (str): Cursor is sweeping; awaiting a click.
        PHASE_RESULT  (str): All three strikes done; showing outcome.
        app: Reference to the main application instance.
        on_close (callable | None): Callback invoked when the minigame
            closes.  Receives ``(final_item, xp_multiplier)`` where
            ``xp_multiplier`` is ``1.0`` for a normal craft, ``1.5`` for
            a "Good" outcome, ``1.0`` for a "Miss", and ``2.0`` for an
            upgrade.  ``final_item`` has its tier attribute re-applied
            according to the minigame score.
        item: The crafted item instance that will be re-tiered.
        original_tier (str): The tier that was rolled by the crafting
            grid before the minigame ran.  Preserved so we can show
            the "before -> after" tier change to the player.
        smelting_level (int): Player's smelting level at craft time
            (kept for telemetry / future tuning).
        screen_w (int): Screen width.
        screen_h (int): Screen height.
        font_*: Pre-rendered pygame fonts.
        phase (str): Current phase constant.
        strike_index (int): Index of the current strike ``[0, NUM_STRIKES)``.
        results (list[str]): Zone result of each completed strike.
        cursor_x (float): Current x position of the hammer cursor in
            screen space.
        cursor_dir (int): ``+1`` or ``-1``; sweep direction.
        _intro_timer (float): Seconds remaining in the intro phase.
        _result_timer (float): Seconds remaining in the result phase
            before the auto-close fires.
        _btn_strike (pygame.Rect | None): Strike button rect.
        _btn_skip (pygame.Rect | None): Skip button rect.
        _bar_rect (pygame.Rect | None): The anvil bar rect.

    Methods:
        __init__(app, item, on_close=None, smelting_level=1):
            Initialise the minigame with a freshly crafted item.
        handle_event(event):
            Process a pygame event.
        update(dt):
            Advance the cursor and phase timers.
        draw(surface):
            Draw the full overlay.
        _close(outcome, xp_multiplier=1.0):
            Finalise the tier and invoke the close callback.
        _record_strike():
            Lock in the current cursor position and advance the round.
        _finalise():
            Score the strikes, apply the tier shift, and start the
            result phase.
    """

    PHASE_INTRO  = "intro"
    PHASE_STRIKE = "strike"
    PHASE_RESULT = "result"

    def __init__(self, app, item, on_close=None, smelting_level: int = 1):
        self.app = app
        self.on_close = on_close
        self.item = item
        self.original_tier = str(getattr(item, "tier", "fine") or "fine")
        self.smelting_level = max(1, int(smelting_level))

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        # Fonts
        self.font_title  = cfg.get_font(max(12, int(40 * cfg.ui_scale())))
        self.font_large  = cfg.get_font(max(11, int(30 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(22 * cfg.ui_scale())))
        self.font_small  = cfg.get_font(max(8,  int(18 * cfg.ui_scale())))

        # Panel / bar geometry
        panel_w = int(sw * 0.78)
        panel_h = int(sh * 0.62)
        self.panel_rect = pygame.Rect(
            (sw - panel_w) // 2,
            (sh - panel_h) // 2,
            panel_w,
            panel_h,
        )
        bar_w = int(panel_w * 0.78)
        bar_h = max(28, int(36 * cfg.ui_scale()))
        self.bar_rect = pygame.Rect(
            self.panel_rect.centerx - bar_w // 2,
            self.panel_rect.y + int(panel_h * 0.55),
            bar_w,
            bar_h,
        )

        # State
        self.phase = self.PHASE_INTRO
        self.strike_index = 0
        self.results: list[str] = []
        self.cursor_x = float(self.bar_rect.x)
        self.cursor_dir = 1
        self._intro_timer = 1.4
        self._result_timer = 0.0
        self._final_tier: str = self.original_tier
        self._xp_multiplier: float = 1.0
        self._outcome_text: str = ""
        self._outcome_color: tuple = TEXT_LIGHT

        # Button rects (recomputed every draw)
        self._btn_strike: pygame.Rect | None = None
        self._btn_skip:   pygame.Rect | None = None

        # Hammer-blow animation: stored in milliseconds, ticked by update().
        self._last_zone_flash: str = ""

    # ------------------------------------------------------------------
    # Tier scoring
    # ------------------------------------------------------------------

    def _finalise(self):
        """Score the strikes, shift the tier, and start the result phase.

        The score-to-shift mapping is documented in the module
        docstring.  Tier changes are applied to ``self.item`` via
        :func:`src.items.items.apply_tier_to_item` so the rest of the
        game sees a single, consistent tier attribute.
        """
        from src.items.items import apply_tier_to_item

        score = 0
        for zone in self.results:
            if zone == "bullseye":
                score += 2
            elif zone == "good":
                score += 1

        if score >= 5:
            new_tier = _shift_tier(self.original_tier, +1)
            self._xp_multiplier = 2.0
            self._outcome_text = "MASTERFUL FORGE WORK!"
            self._outcome_color = TEXT_GOLD
        elif score >= 3:
            new_tier = self.original_tier
            self._xp_multiplier = 1.5
            self._outcome_text = "Solid craftsmanship."
            self._outcome_color = TEXT_GOOD
        elif score >= 1:
            new_tier = self.original_tier
            self._xp_multiplier = 1.0
            self._outcome_text = "Acceptable tempering."
            self._outcome_color = TEXT_LIGHT
        else:
            new_tier = _shift_tier(self.original_tier, -1)
            self._xp_multiplier = 1.0
            self._outcome_text = "The blade cracked under your hammer..."
            self._outcome_color = TEXT_BAD

        # Apply the tier to the live item instance.
        self._final_tier = new_tier
        try:
            apply_tier_to_item(self.item, new_tier)
        except Exception as exc:
            logger.warning(f"Failed to apply tier to item in crafting minigame: {exc}")

        # Result auto-closes after a short pause so the player can read it.
        self._result_timer = 2.4
        self.phase = self.PHASE_RESULT

    # ------------------------------------------------------------------
    # Phase transitions
    # ------------------------------------------------------------------

    def _record_strike(self):
        """Lock in the current cursor position and advance the round.

        After the final strike the minigame moves to the result phase
        via :meth:`_finalise`.
        """
        if self.phase != self.PHASE_STRIKE:
            return
        zone = _zone_at(self.cursor_x, self.bar_rect.x, self.bar_rect.width)
        self.results.append(zone)
        self._last_zone_flash = zone
        self.strike_index += 1
        if self.strike_index >= NUM_STRIKES:
            self._finalise()
        else:
            # Reset cursor to the centre so the next sweep starts clean.
            self.cursor_x = float(self.bar_rect.x + self.bar_rect.width // 2)
            self.cursor_dir = 1

    def _close(self, outcome: str, xp_multiplier: float = 1.0):
        """Invoke the close callback and clear the active reference.

        ``outcome`` is a string label for telemetry.  ``xp_multiplier``
        defaults to ``1.0`` when the player skips the minigame.
        """
        if callable(self.on_close):
            try:
                self.on_close(self.item, xp_multiplier, outcome)
            except Exception as exc:
                logger.warning(f"crafting minigame on_close callback failed: {exc}")
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event):
        """Process a pygame event for the minigame UI."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Skip without changing the tier.
                self._close("skipped", 1.0)
                return
            if self.phase == self.PHASE_STRIKE and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._record_strike()
                return
            if self.phase == self.PHASE_RESULT and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                self._close(self._outcome_text, self._xp_multiplier)
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.phase == self.PHASE_STRIKE:
                if self._btn_strike and self._btn_strike.collidepoint(pos):
                    self._record_strike()
                    return
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._close("skipped", 1.0)
                    return
                # Clicking anywhere on the bar itself also counts as a strike.
                if self.bar_rect.collidepoint(pos):
                    self.cursor_x = float(pos[0])
                    self._record_strike()
                    return
            elif self.phase == self.PHASE_RESULT:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._close(self._outcome_text, self._xp_multiplier)
                    return

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float):
        """Advance the cursor and phase timers by ``dt`` seconds."""
        if self.phase == self.PHASE_INTRO:
            self._intro_timer -= dt
            if self._intro_timer <= 0.0:
                self.phase = self.PHASE_STRIKE
        elif self.phase == self.PHASE_STRIKE:
            bar = self.bar_rect
            # Move the cursor; bounce off the bar ends.
            self.cursor_x += self.cursor_dir * SWEEP_SPEED * dt
            if self.cursor_x >= bar.right:
                self.cursor_x = float(bar.right)
                self.cursor_dir = -1
            elif self.cursor_x <= bar.x:
                self.cursor_x = float(bar.x)
                self.cursor_dir = 1
        elif self.phase == self.PHASE_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._close(self._outcome_text, self._xp_multiplier)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_button(self, surface, rect, text, hovered=False, text_color=None):
        """Draw a styled button (matching the blackjack aesthetic)."""
        bg = BUTTON_HOVER if hovered else BUTTON_BG
        pygame.draw.rect(surface, bg, rect, border_radius=8)
        pygame.draw.rect(surface, BUTTON_BORDER, rect, width=2, border_radius=8)
        tc = text_color if text_color else TEXT_LIGHT
        txt_surf = self.font_medium.render(text, True, tc)
        txt_rect = txt_surf.get_rect(center=rect.center)
        surface.blit(txt_surf, txt_rect)

    def _draw_panel(self, surface):
        """Draw the dark forge-themed background panel."""
        pr = self.panel_rect
        # Drop shadow
        shadow = pr.move(6, 8)
        sh_surf = pygame.Surface(shadow.size, pygame.SRCALPHA)
        pygame.draw.rect(sh_surf, (0, 0, 0, 110), sh_surf.get_rect(), border_radius=18)
        surface.blit(sh_surf, shadow.topleft)
        # Panel
        pygame.draw.rect(surface, ANVIL_BG, pr, border_radius=18)
        pygame.draw.rect(surface, ANVIL_BORDER, pr, width=3, border_radius=18)
        # Inner highlight
        inner = pr.inflate(-10, -10)
        pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, inner, width=1, border_radius=14)
        # Subtle anvil-glow gradient at the top
        for i in range(40):
            alpha = max(0, 80 - i * 2)
            band = pygame.Surface((pr.width - 20, 1), pygame.SRCALPHA)
            band.fill((ANVIL_GLOW[0], ANVIL_GLOW[1], ANVIL_GLOW[2], alpha))
            surface.blit(band, (pr.x + 10, pr.y + 10 + i))

    def _draw_title(self, surface, pr):
        title = self.font_title.render("Tempering", True, TEXT_GOLD)
        surface.blit(title, (pr.centerx - title.get_width() // 2, pr.y + 18))
        sub = self.font_small.render(
            "Strike the anvil at the right moment to hone your craft.",
            True, TEXT_DIM,
        )
        surface.blit(sub, (pr.centerx - sub.get_width() // 2, pr.y + 18 + title.get_height() + 4))

    def _draw_strike_indicator(self, surface, pr):
        """Draw N anvil icons, one filled per completed strike."""
        icon_size = 26
        gap = 10
        total_w = NUM_STRIKES * icon_size + (NUM_STRIKES - 1) * gap
        x = pr.centerx - total_w // 2
        y = pr.y + 90
        for i in range(NUM_STRIKES):
            rect = pygame.Rect(x + i * (icon_size + gap), y, icon_size, icon_size)
            if i < len(self.results):
                # Filled anvil (strike complete)
                pygame.draw.rect(surface, BAR_BULLSEYE, rect, border_radius=6)
                pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, rect, width=2, border_radius=6)
                # Result letter
                letter = {"bullseye": "B", "good": "G", "miss": "X"}.get(self.results[i], "?")
                txt = self.font_small.render(letter, True, TEXT_LIGHT)
                surface.blit(txt, txt.get_rect(center=rect.center))
            else:
                # Empty slot
                pygame.draw.rect(surface, ANVIL_BG_DARK, rect, border_radius=6)
                pygame.draw.rect(surface, ANVIL_BORDER, rect, width=2, border_radius=6)

    def _draw_bar(self, surface):
        """Draw the anvil bar with its three coloured zones and the cursor."""
        br = self.bar_rect
        # Bar background
        pygame.draw.rect(surface, BAR_BG, br, border_radius=8)
        # The three zones are drawn as nested rounded rects so the
        # boundaries are clearly visible.  The bar is symmetric around
        # the centre.
        bw, bh = br.width, br.height
        cx = br.centerx
        # Miss (outer 22 % on each side)
        miss_w = int(bw * 0.22)
        miss_left  = pygame.Rect(br.x,                br.y, miss_w, bh)
        miss_right = pygame.Rect(br.right - miss_w,   br.y, miss_w, bh)
        pygame.draw.rect(surface, BAR_MISS, miss_left,  border_radius=8)
        pygame.draw.rect(surface, BAR_MISS, miss_right, border_radius=8)
        # Good (next 28 % on each side)
        good_w = int(bw * 0.28)
        good_left  = pygame.Rect(br.x + miss_w,                  br.y, good_w, bh)
        good_right = pygame.Rect(br.right - miss_w - good_w,    br.y, good_w, bh)
        pygame.draw.rect(surface, BAR_GOOD, good_left,  border_radius=6)
        pygame.draw.rect(surface, BAR_GOOD, good_right, border_radius=6)
        # Bullseye (centre 22 %)
        bull_w = int(bw * 0.22)
        bull = pygame.Rect(cx - bull_w // 2, br.y, bull_w, bh)
        pygame.draw.rect(surface, BAR_BULLSEYE, bull, border_radius=4)
        # Bar outline
        pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, br, width=2, border_radius=8)

        # Cursor (a vertical hammer head)
        if self.phase in (self.PHASE_STRIKE, self.PHASE_INTRO):
            cx_pos = int(self.cursor_x)
            cursor_h = br.height + 18
            cursor_top = br.y - 12
            cursor_rect = pygame.Rect(cx_pos - 3, cursor_top, 6, cursor_h)
            pygame.draw.rect(surface, BAR_CURSOR, cursor_rect, border_radius=2)
            # Glow line on top
            pygame.draw.line(
                surface, BAR_CURSOR_GLOW,
                (cx_pos, cursor_top - 4),
                (cx_pos, cursor_top + 4),
                3,
            )

    def _draw_result(self, surface, pr):
        """Draw the post-strike summary, tier shift, and item name."""
        # Big outcome text
        title = self.font_large.render(self._outcome_text, True, self._outcome_color)
        surface.blit(title, (pr.centerx - title.get_width() // 2, pr.y + 130))

        # Tier before -> after
        try:
            from_tier = get_tier_name(self.original_tier)
            to_tier   = get_tier_name(self._final_tier)
        except Exception:
            from_tier = f"[{self.original_tier.capitalize()}]"
            to_tier   = f"[{self._final_tier.capitalize()}]"
        tier_text = f"{from_tier}  ->  {to_tier}"
        tier_surf = self.font_medium.render(tier_text, True, TEXT_LIGHT)
        surface.blit(tier_surf, (pr.centerx - tier_surf.get_width() // 2, pr.y + 130 + title.get_height() + 4))

        # Item name (with the new tier prefix baked in)
        try:
            item_name = self.item.name() if hasattr(self.item, "name") else str(self.item)
        except Exception:
            item_name = str(self.item)
        name_surf = self.font_medium.render(item_name, True, TEXT_GOLD)
        surface.blit(name_surf, (pr.centerx - name_surf.get_width() // 2, pr.y + 130 + title.get_height() + 4 + tier_surf.get_height() + 6))

        # Score breakdown
        strikes_text = "  ".join(
            {"bullseye": "PERFECT", "good": "GOOD", "miss": "MISS"}.get(r, "?")
            for r in self.results
        )
        score_text = f"Strikes: {strikes_text}"
        score_surf = self.font_small.render(score_text, True, TEXT_DIM)
        surface.blit(score_surf, (pr.centerx - score_surf.get_width() // 2, pr.bottom - 110))

        # XP multiplier hint
        if self._xp_multiplier != 1.0:
            xp_text = f"Smelting XP x{self._xp_multiplier:g}"
            xp_color = TEXT_GOOD if self._xp_multiplier > 1.0 else TEXT_LIGHT
            xp_surf = self.font_small.render(xp_text, True, xp_color)
            surface.blit(xp_surf, (pr.centerx - xp_surf.get_width() // 2, pr.bottom - 88))

    # ------------------------------------------------------------------
    # Main draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface):
        """Draw the full minigame overlay."""
        # Dim background
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        pr = self.panel_rect
        self._draw_panel(surface)
        self._draw_title(surface, pr)
        self._draw_strike_indicator(surface, pr)
        self._draw_bar(surface)

        # Phase-specific content
        mouse_pos = pygame.mouse.get_pos()
        if self.phase == self.PHASE_INTRO:
            hint = self.font_medium.render("Strike when the cursor is in the gold zone!", True, TEXT_LIGHT)
            surface.blit(hint, (pr.centerx - hint.get_width() // 2, pr.y + pr.height - 90))
        elif self.phase == self.PHASE_STRIKE:
            # Strike / Skip buttons under the bar
            btn_w = 140
            btn_h = 38
            strike_rect = pygame.Rect(
                pr.centerx - btn_w - 10,
                pr.bottom - 70,
                btn_w, btn_h,
            )
            skip_rect = pygame.Rect(
                pr.centerx + 10,
                pr.bottom - 70,
                btn_w, btn_h,
            )
            self._btn_strike = strike_rect
            self._btn_skip = skip_rect
            self._draw_button(surface, strike_rect, "STRIKE", strike_rect.collidepoint(mouse_pos), TEXT_GOLD)
            self._draw_button(surface, skip_rect,   "SKIP",   skip_rect.collidepoint(mouse_pos))
            # Last-result flash text
            if self._last_zone_flash:
                zone = self._last_zone_flash
                flash = {"bullseye": "PERFECT!", "good": "GOOD", "miss": "MISS"}.get(zone, "")
                flash_surf = self.font_medium.render(flash, True, _zone_color(zone))
                surface.blit(flash_surf, (pr.centerx - flash_surf.get_width() // 2, pr.bottom - 130))
        elif self.phase == self.PHASE_RESULT:
            self._draw_result(surface, pr)
            # Continue button
            btn_w = 180
            btn_h = 40
            continue_rect = pygame.Rect(
                pr.centerx - btn_w // 2,
                pr.bottom - 60,
                btn_w, btn_h,
            )
            self._btn_skip = continue_rect
            self._draw_button(surface, continue_rect, "Continue", continue_rect.collidepoint(mouse_pos), TEXT_GOLD)

        # Hint footer
        if self.phase != self.PHASE_RESULT:
            footer = self.font_small.render("SPACE / click to strike  -  ESC to skip", True, TEXT_DIM)
            surface.blit(footer, (pr.centerx - footer.get_width() // 2, pr.bottom - 24))
