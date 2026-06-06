"""
Smeltery minigames: small skill challenges that fire when a batch in
the coke oven or blast furnace finishes smelting.

Three new challenges are added on top of the workbench Tempering game:

* **Tending the Fire** -- vertical bellows-hold challenge for the coke
  oven. Player must keep a heat cursor inside a target zone while
  holding SPACE / the mouse button.
* **Iron Forge** -- three-strike horizontal timing challenge for the
  iron-ore -> iron-ingot batch. Graded Bullseye / Good / Miss.
* **Quench** -- the toughest challenge. Sweeping cursor that narrows
  as it travels; player must click inside the visible sweet spot
  for the iron-ingot -> steel-ingot batch.

All three are skippable via ESC or a Skip button. The base batch
output is unaffected; the minigame only grants (or denies) a bonus
yield and an XP multiplier.
"""

import math
import random
import pygame

import src.config as cfg
from src.core.logger import logger

# Palette
ANVIL_BG          = (28, 22, 18)
ANVIL_BORDER      = (90, 60, 30)
ANVIL_BORDER_LIGHT = (140, 100, 50)
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


def _draw_button(surface, font, rect, text, hovered=False, text_color=None):
    bg = BUTTON_HOVER if hovered else BUTTON_BG
    pygame.draw.rect(surface, bg, rect, border_radius=8)
    pygame.draw.rect(surface, BUTTON_BORDER, rect, width=2, border_radius=8)
    tc = text_color if text_color else TEXT_LIGHT
    txt_surf = font.render(text, True, tc)
    txt_rect = txt_surf.get_rect(center=rect.center)
    surface.blit(txt_surf, txt_rect)


def _draw_panel(surface, panel_rect, title, subtitle, fonts):
    shadow = panel_rect.move(6, 8)
    sh_surf = pygame.Surface(shadow.size, pygame.SRCALPHA)
    pygame.draw.rect(sh_surf, (0, 0, 0, 110), sh_surf.get_rect(), border_radius=18)
    surface.blit(sh_surf, shadow.topleft)
    pygame.draw.rect(surface, ANVIL_BG, panel_rect, border_radius=18)
    pygame.draw.rect(surface, ANVIL_BORDER, panel_rect, width=3, border_radius=18)
    inner = panel_rect.inflate(-10, -10)
    pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, inner, width=1, border_radius=14)
    for i in range(40):
        alpha = max(0, 80 - i * 2)
        band = pygame.Surface((panel_rect.width - 20, 1), pygame.SRCALPHA)
        band.fill((ANVIL_GLOW[0], ANVIL_GLOW[1], ANVIL_GLOW[2], alpha))
        surface.blit(band, (panel_rect.x + 10, panel_rect.y + 10 + i))

    font_title, font_sub = fonts
    title_surf = font_title.render(title, True, TEXT_GOLD)
    surface.blit(title_surf, (panel_rect.centerx - title_surf.get_width() // 2,
                              panel_rect.y + 18))
    sub_surf = font_sub.render(subtitle, True, TEXT_DIM)
    surface.blit(sub_surf, (panel_rect.centerx - sub_surf.get_width() // 2,
                            panel_rect.y + 18 + title_surf.get_height() + 4))


# ===========================================================================
# Tending the Fire (coke oven)
# ===========================================================================

class TendingFireMinigame:
    PHASE_INTRO = "intro"
    PHASE_ACTIVE = "active"
    PHASE_RESULT = "result"

    BAR_WIDTH = 26
    CURSOR_FREQ = 1.6
    GOOD_ZONE = 0.18
    PERFECT_ZONE = 0.08
    HOLD_TARGET = 1.0
    OUT_OF_ZONE_TOLERANCE = 0.45

    def __init__(self, app, *, recipe_name="Coke Oven",
                 hold_target=None, on_close=None, smelting_level=1):
        self.app = app
        self.on_close = on_close
        self.recipe_name = recipe_name
        self.smelting_level = max(1, int(smelting_level))
        if hold_target is not None:
            self.HOLD_TARGET = float(hold_target)

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        self.font_title  = cfg.get_font(max(12, int(40 * cfg.ui_scale())))
        self.font_large  = cfg.get_font(max(11, int(30 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(22 * cfg.ui_scale())))
        self.font_small  = cfg.get_font(max(8,  int(18 * cfg.ui_scale())))

        panel_w = int(sw * 0.62)
        panel_h = int(sh * 0.58)
        self.panel_rect = pygame.Rect(
            (sw - panel_w) // 2,
            (sh - panel_h) // 2,
            panel_w, panel_h,
        )
        bar_h = int(panel_h * 0.62)
        bar_x = self.panel_rect.centerx - self.BAR_WIDTH // 2
        bar_y = self.panel_rect.y + int(panel_h * 0.30)
        self.bar_rect = pygame.Rect(bar_x, bar_y, self.BAR_WIDTH, bar_h)

        self.phase = self.PHASE_INTRO
        self.heat = 0.5
        self.hold_charge = 0.0
        self.out_of_zone_time = 0.0
        self._intro_timer = 1.0
        self._result_timer = 0.0
        self._outcome = ""
        self._outcome_color = TEXT_LIGHT
        self._xp_multiplier = 1.0
        self._bonus_amount = 0
        self._holding = False
        self._btn_skip = None

    def _finalise(self, success, perfect):
        if perfect:
            self._bonus_amount = 1
            self._xp_multiplier = 2.0
            self._outcome = "PERFECT TEMPER!"
            self._outcome_color = TEXT_GOLD
        elif success:
            self._bonus_amount = 1
            self._xp_multiplier = 1.5
            self._outcome = "Clean burn."
            self._outcome_color = TEXT_GOOD
        else:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "The fire died down..."
            self._outcome_color = TEXT_BAD
        self._result_timer = 2.2
        self.phase = self.PHASE_RESULT

    def _close(self):
        if callable(self.on_close):
            try:
                self.on_close(self._outcome, self._bonus_amount, self._xp_multiplier)
            except Exception as exc:
                logger.warning("smeltery minigame on_close failed: %s", exc)
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._bonus_amount = 0
                self._xp_multiplier = 1.0
                self._outcome = "Skipped"
                self._close()
                return
            if self.phase == self.PHASE_ACTIVE and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._holding = True
                return
        if event.type == pygame.KEYUP:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._holding = False
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.phase == self.PHASE_INTRO:
                self.phase = self.PHASE_ACTIVE
                return
            if self.phase == self.PHASE_ACTIVE:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._bonus_amount = 0
                    self._xp_multiplier = 1.0
                    self._outcome = "Skipped"
                    self._close()
                    return
                self._holding = True
                return
            if self.phase == self.PHASE_RESULT:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._close()
                    return
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._holding = False
            return

    def update(self, dt):
        if self.phase == self.PHASE_INTRO:
            self._intro_timer -= dt
            if self._intro_timer <= 0.0:
                self.phase = self.PHASE_ACTIVE
            return
        if self.phase == self.PHASE_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._close()
            return
        if self.phase != self.PHASE_ACTIVE:
            return

        phase = pygame.time.get_ticks() * 0.001 * self.CURSOR_FREQ
        target_heat = 0.5 + 0.45 * math.sin(phase * math.tau)

        if self._holding:
            self.heat += (0.5 - self.heat) * min(1.0, 4.0 * dt)
        else:
            self.heat += (target_heat - self.heat) * min(1.0, 2.5 * dt)

        in_perfect = abs(self.heat - 0.5) < (self.PERFECT_ZONE * 0.5)
        in_good    = abs(self.heat - 0.5) < (self.GOOD_ZONE * 0.5)

        if in_good:
            self.out_of_zone_time = 0.0
            if self._holding:
                charge = dt * (2.5 if in_perfect else 1.4)
                self.hold_charge = min(self.HOLD_TARGET, self.hold_charge + charge)
                if in_perfect and self.hold_charge >= self.HOLD_TARGET:
                    self._finalise(success=True, perfect=True)
                    return
            else:
                self.hold_charge = max(0.0, self.hold_charge - dt * 0.3)
        else:
            self.out_of_zone_time += dt
            self.hold_charge = max(0.0, self.hold_charge - dt * 1.5)
            if self.out_of_zone_time > self.OUT_OF_ZONE_TOLERANCE and self._holding:
                self._finalise(success=False, perfect=False)
                return

    def draw(self, surface):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        _draw_panel(
            surface, self.panel_rect,
            "Tending the Fire",
            "Hold the bellows to keep the heat in the gold zone.",
            (self.font_title, self.font_small),
        )
        pr = self.panel_rect
        mouse_pos = pygame.mouse.get_pos()

        br = self.bar_rect
        pygame.draw.rect(surface, BAR_BG, br, border_radius=8)
        bw, bh = br.width, br.height
        good_h = int(bh * self.GOOD_ZONE)
        good = pygame.Rect(br.x, br.centery - good_h // 2, bw, good_h)
        pygame.draw.rect(surface, BAR_BULLSEYE, good, border_radius=4)
        perfect_h = max(6, int(bh * self.PERFECT_ZONE))
        perfect = pygame.Rect(br.x, br.centery - perfect_h // 2, bw, perfect_h)
        pygame.draw.rect(surface, (255, 235, 130), perfect, border_radius=3)
        pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, br, width=2, border_radius=8)

        # Cursor (heat level)
        cursor_y = br.bottom - int(self.heat * bh) - 4
        cursor_h = 8
        cursor_rect = pygame.Rect(br.x - 4, cursor_y, bw + 8, cursor_h)
        cursor_color = (200, 60, 30) if not self._holding else (255, 200, 60)
        pygame.draw.rect(surface, cursor_color, cursor_rect, border_radius=2)
        pygame.draw.rect(surface, BAR_CURSOR, cursor_rect, width=1, border_radius=2)

        # Charge meter on the side
        meter_w = 12
        meter_h = bh
        meter_x = br.right + 14
        meter_rect = pygame.Rect(meter_x, br.y, meter_w, meter_h)
        pygame.draw.rect(surface, BAR_BG, meter_rect, border_radius=4)
        pygame.draw.rect(surface, ANVIL_BORDER, meter_rect, width=1, border_radius=4)
        fill_h = int(meter_h * (self.hold_charge / self.HOLD_TARGET))
        if fill_h > 0:
            fill = pygame.Rect(meter_x + 1, meter_rect.bottom - fill_h, meter_w - 2, fill_h)
            pygame.draw.rect(surface, (120, 220, 130), fill, border_radius=3)

        # Buttons
        if self.phase == self.PHASE_INTRO:
            hint = self.font_medium.render("Click to start -- hold SPACE / mouse to charge the bellows",
                                            True, TEXT_LIGHT)
            surface.blit(hint, (pr.centerx - hint.get_width() // 2, pr.y + pr.height - 90))
        elif self.phase == self.PHASE_ACTIVE:
            btn_w = 130
            btn_h = 38
            skip_rect = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = skip_rect
            _draw_button(surface, self.font_medium, skip_rect, "SKIP", skip_rect.collidepoint(mouse_pos))
            label = "HOLD BELLOWS" if self._holding else "Release to rest"
            color = TEXT_GOOD if self._holding else TEXT_DIM
            tip = self.font_medium.render(label, True, color)
            surface.blit(tip, (pr.centerx - tip.get_width() // 2, pr.bottom - 110))
        elif self.phase == self.PHASE_RESULT:
            out_surf = self.font_large.render(self._outcome, True, self._outcome_color)
            surface.blit(out_surf, (pr.centerx - out_surf.get_width() // 2, pr.y + 130))
            if self._bonus_amount > 0:
                bonus = self.font_medium.render(
                    "+1 bonus output (smelt XP x%g)" % self._xp_multiplier,
                    True, TEXT_GOOD,
                )
            else:
                bonus = self.font_medium.render(
                    "No bonus -- base output only",
                    True, TEXT_DIM,
                )
            surface.blit(bonus, (pr.centerx - bonus.get_width() // 2, pr.y + 130 + out_surf.get_height() + 6))
            btn_w = 160
            btn_h = 38
            cont = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = cont
            _draw_button(surface, self.font_medium, cont, "Continue", cont.collidepoint(mouse_pos), TEXT_GOLD)


# ===========================================================================
# Quench (iron-ingot -> steel-ingot blast furnace)
# ===========================================================================

class QuenchMinigame:
    """Single-click timing challenge for the steel batch.

    A horizontal bar sweeps from left to right; the gold "sweet spot"
    shrinks as the bar advances, and a moving cursor crosses it. The
    player must click (or press SPACE) while the cursor is inside the
    sweet spot to seal the steel. The earlier the click, the bigger
    the bonus; clicking too late or missing the spot cracks the
    ingot and yields no bonus.
    """

    PHASE_INTRO = "intro"
    PHASE_SWEEP = "sweep"
    PHASE_RESULT = "result"

    SWEEP_DURATION = 1.6  # seconds for the bar to travel from left to right
    INITIAL_SWEET_SPOT = 0.55  # 55% of the bar width at t=0
    FINAL_SWEET_SPOT   = 0.18  # shrinks to 18% by t=1
    TOLERANCE_PX = 4  # how forgiving the click detection is

    def __init__(self, app, *, on_close=None, smelting_level=1):
        self.app = app
        self.on_close = on_close
        self.smelting_level = max(1, int(smelting_level))

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        self.font_title  = cfg.get_font(max(12, int(40 * cfg.ui_scale())))
        self.font_large  = cfg.get_font(max(11, int(30 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(22 * cfg.ui_scale())))
        self.font_small  = cfg.get_font(max(8,  int(18 * cfg.ui_scale())))

        panel_w = int(sw * 0.72)
        panel_h = int(sh * 0.46)
        self.panel_rect = pygame.Rect(
            (sw - panel_w) // 2,
            (sh - panel_h) // 2,
            panel_w, panel_h,
        )
        bar_w = int(panel_w * 0.86)
        bar_h = max(40, int(50 * cfg.ui_scale()))
        self.bar_rect = pygame.Rect(
            self.panel_rect.centerx - bar_w // 2,
            self.panel_rect.y + int(panel_h * 0.50),
            bar_w, bar_h,
        )

        self.phase = self.PHASE_INTRO
        self.t = 0.0
        self._intro_timer = 1.0
        self._result_timer = 0.0
        self._outcome = ""
        self._outcome_color = TEXT_LIGHT
        self._xp_multiplier = 1.0
        self._bonus_amount = 0
        self._btn_skip = None

    def _sweep_position(self):
        """Return cursor x in pixels inside the bar (0..bar_w)."""
        return self.t * self.bar_rect.width

    def _sweet_spot_rect(self):
        """Return the (x, width) of the current sweet spot inside the bar."""
        bw = self.bar_rect.width
        # Interpolate sweet spot width from INITIAL to FINAL.
        frac = self.INITIAL_SWEET_SPOT + (self.FINAL_SWEET_SPOT - self.INITIAL_SWEET_SPOT) * self.t
        w = bw * frac
        # Sweet spot is centred on the bar.
        x = bw * 0.5 - w * 0.5
        return x, w

    def _attempt_click(self, x=None):
        if self.phase != self.PHASE_SWEEP:
            return
        cursor_x = self._sweep_position()
        spot_x, spot_w = self._sweet_spot_rect()
        dist = abs(cursor_x - (spot_x + spot_w * 0.5))
        # Tighter hits (early clicks) get a better bonus.
        if dist <= spot_w * 0.5 + self.TOLERANCE_PX:
            # Success: bonus scales with how early / centred the click was.
            precision = 1.0 - min(1.0, dist / max(1, spot_w))
            if precision >= 0.85:
                self._bonus_amount = 1
                self._xp_multiplier = 2.0
                self._outcome = "PERFECT SEAL!"
                self._outcome_color = TEXT_GOLD
            elif precision >= 0.55:
                self._bonus_amount = 1
                self._xp_multiplier = 1.5
                self._outcome = "Good quench."
                self._outcome_color = TEXT_GOOD
            else:
                self._bonus_amount = 0
                self._xp_multiplier = 1.2
                self._outcome = "Marginal seal."
                self._outcome_color = TEXT_LIGHT
        else:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "The steel cracked..."
            self._outcome_color = TEXT_BAD
        self._result_timer = 2.2
        self.phase = self.PHASE_RESULT

    def _close(self):
        if callable(self.on_close):
            try:
                self.on_close(self._outcome, self._bonus_amount, self._xp_multiplier)
            except Exception as exc:
                logger.warning("smeltery minigame on_close failed: %s", exc)
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._bonus_amount = 0
                self._xp_multiplier = 1.0
                self._outcome = "Skipped"
                self._close()
                return
            if self.phase == self.PHASE_INTRO and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.phase = self.PHASE_SWEEP
                return
            if self.phase == self.PHASE_SWEEP and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._attempt_click()
                return
            if self.phase == self.PHASE_RESULT and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._close()
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.phase == self.PHASE_INTRO:
                self.phase = self.PHASE_SWEEP
                return
            if self.phase == self.PHASE_SWEEP:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._bonus_amount = 0
                    self._xp_multiplier = 1.0
                    self._outcome = "Skipped"
                    self._close()
                    return
                self._attempt_click()
                return
            if self.phase == self.PHASE_RESULT:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._close()
                    return

    def update(self, dt):
        if self.phase == self.PHASE_INTRO:
            self._intro_timer -= dt
            if self._intro_timer <= 0.0:
                self.phase = self.PHASE_SWEEP
            return
        if self.phase == self.PHASE_SWEEP:
            self.t += dt / self.SWEEP_DURATION
            if self.t >= 1.0:
                # Bar finished without a click -- miss.
                self.t = 1.0
                self._bonus_amount = 0
                self._xp_multiplier = 1.0
                self._outcome = "Too slow -- the ingot cracked..."
                self._outcome_color = TEXT_BAD
                self._result_timer = 2.2
                self.phase = self.PHASE_RESULT
            return
        if self.phase == self.PHASE_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._close()

    def draw(self, surface):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        _draw_panel(
            surface, self.panel_rect,
            "Quench",
            "Click at the moment the cursor crosses the gold band.",
            (self.font_title, self.font_small),
        )
        pr = self.panel_rect
        mouse_pos = pygame.mouse.get_pos()

        br = self.bar_rect
        bw, bh = br.width, br.height
        pygame.draw.rect(surface, BAR_BG, br, border_radius=8)
        pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, br, width=2, border_radius=8)

        # Sweet spot
        spot_x, spot_w = self._sweet_spot_rect()
        spot = pygame.Rect(br.x + int(spot_x), br.y + 4, int(spot_w), bh - 8)
        pygame.draw.rect(surface, BAR_BULLSEYE, spot, border_radius=6)

        if self.phase == self.PHASE_SWEEP:
            cursor_x = br.x + int(self._sweep_position())
            cursor_h = bh + 12
            cursor_top = br.y - 6
            cursor_rect = pygame.Rect(cursor_x - 3, cursor_top, 6, cursor_h)
            pygame.draw.rect(surface, BAR_CURSOR, cursor_rect, border_radius=2)
            pygame.draw.line(surface, BAR_CURSOR_GLOW,
                             (cursor_x, cursor_top - 4),
                             (cursor_x, cursor_top + 4), 3)
            # Progress hint
            tip = self.font_medium.render("CLICK!", True, TEXT_GOLD)
            surface.blit(tip, (pr.centerx - tip.get_width() // 2, br.bottom + 8))

        if self.phase == self.PHASE_INTRO:
            hint = self.font_medium.render("Click / SPACE to begin the quench", True, TEXT_LIGHT)
            surface.blit(hint, (pr.centerx - hint.get_width() // 2, pr.y + pr.height - 90))
        elif self.phase == self.PHASE_SWEEP:
            btn_w = 130
            btn_h = 38
            skip_rect = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = skip_rect
            _draw_button(surface, self.font_medium, skip_rect, "SKIP", skip_rect.collidepoint(mouse_pos))
        elif self.phase == self.PHASE_RESULT:
            out_surf = self.font_large.render(self._outcome, True, self._outcome_color)
            surface.blit(out_surf, (pr.centerx - out_surf.get_width() // 2, pr.y + 130))
            if self._bonus_amount > 0:
                bonus = self.font_medium.render(
                    "+1 bonus steel ingot (smelt XP x%g)" % self._xp_multiplier,
                    True, TEXT_GOOD,
                )
            else:
                bonus = self.font_medium.render("No bonus -- base output only", True, TEXT_DIM)
            surface.blit(bonus, (pr.centerx - bonus.get_width() // 2, pr.y + 130 + out_surf.get_height() + 6))
            btn_w = 160
            btn_h = 38
            cont = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = cont
            _draw_button(surface, self.font_medium, cont, "Continue", cont.collidepoint(mouse_pos), TEXT_GOLD)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def make_smeltery_minigame(app, recipe, *, on_close=None, smelting_level=1):
    """Return a fresh smeltery-minigame instance for ``recipe`` or
    ``None`` if the recipe doesn't trigger one.

    ``recipe`` is a dict in the form documented in
    :mod:`database.smeltery_recipes_db`. The minigame id is taken
    from the ``minigame`` key (see :data:`MINIGAME_REGISTRY`).
    """
    if not recipe:
        return None
    mg_id = recipe.get("minigame", "none") or "none"
    if mg_id == "tending":
        return TendingFireMinigame(app, on_close=on_close, smelting_level=smelting_level)
    if mg_id == "forge":
        return ForgeMinigame(app, on_close=on_close, smelting_level=smelting_level)
    if mg_id == "quench":
        return QuenchMinigame(app, on_close=on_close, smelting_level=smelting_level)
    return None


# ===========================================================================
# Iron Forge (iron-ore -> iron-ingot blast furnace)
# ===========================================================================

def _zone_at(x, bar_x, bar_w):
    """Classify cursor ``x`` into bullseye / good / miss relative to a bar."""
    if bar_w <= 0:
        return "miss"
    rel = (x - bar_x) / float(bar_w)
    rel = max(0.0, min(1.0, rel))
    dist = abs(rel - 0.5) * 2.0
    if dist <= 0.20:
        return "bullseye"
    if dist <= 0.48:
        return "good"
    return "miss"


class ForgeMinigame:
    """Three-strike horizontal timing challenge.

    A hammer cursor sweeps across a horizontal forge bar. The player
    must click (or press SPACE) to "strike" the bar when the cursor
    is in the gold zone. Three strikes in a row are graded
    Bullseye / Good / Miss; the sum determines the bonus yield and
    the XP multiplier.

    Used by the iron-ore -> iron-ingot blast-furnace batch.
    """

    PHASE_INTRO = "intro"
    PHASE_STRIKE = "strike"
    PHASE_RESULT = "result"

    NUM_STRIKES = 3
    SWEEP_SPEED = 720.0  # pixels per second; faster than the workbench

    def __init__(self, app, *, on_close=None, smelting_level=1):
        self.app = app
        self.on_close = on_close
        self.smelting_level = max(1, int(smelting_level))

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        self.font_title  = cfg.get_font(max(12, int(40 * cfg.ui_scale())))
        self.font_large  = cfg.get_font(max(11, int(30 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(22 * cfg.ui_scale())))
        self.font_small  = cfg.get_font(max(8,  int(18 * cfg.ui_scale())))

        panel_w = int(sw * 0.78)
        panel_h = int(sh * 0.50)
        self.panel_rect = pygame.Rect(
            (sw - panel_w) // 2,
            (sh - panel_h) // 2,
            panel_w, panel_h,
        )
        bar_w = int(panel_w * 0.78)
        bar_h = max(28, int(36 * cfg.ui_scale()))
        self.bar_rect = pygame.Rect(
            self.panel_rect.centerx - bar_w // 2,
            self.panel_rect.y + int(panel_h * 0.55),
            bar_w, bar_h,
        )

        self.phase = self.PHASE_INTRO
        self.strike_index = 0
        self.results = []
        self.cursor_x = float(self.bar_rect.x)
        self.cursor_dir = 1
        self._intro_timer = 1.0
        self._result_timer = 0.0
        self._outcome = ""
        self._outcome_color = TEXT_LIGHT
        self._xp_multiplier = 1.0
        self._bonus_amount = 0
        self._btn_strike = None
        self._btn_skip = None
        self._last_zone_flash = ""

    def _finalise(self):
        score = 0
        for zone in self.results:
            if zone == "bullseye":
                score += 2
            elif zone == "good":
                score += 1
        if score >= 5:
            self._bonus_amount = 2
            self._xp_multiplier = 2.0
            self._outcome = "MASTERFUL FORGE WORK!"
            self._outcome_color = TEXT_GOLD
        elif score >= 3:
            self._bonus_amount = 1
            self._xp_multiplier = 1.5
            self._outcome = "Solid hammering."
            self._outcome_color = TEXT_GOOD
        elif score >= 1:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "Acceptable shaping."
            self._outcome_color = TEXT_LIGHT
        else:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "The ingot cracked under the hammer..."
            self._outcome_color = TEXT_BAD
        self._result_timer = 2.4
        self.phase = self.PHASE_RESULT

    def _close(self):
        if callable(self.on_close):
            try:
                self.on_close(self._outcome, self._bonus_amount, self._xp_multiplier)
            except Exception as exc:
                logger.warning("smeltery minigame on_close failed: %s", exc)
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    def _record_strike(self):
        if self.phase != self.PHASE_STRIKE:
            return
        zone = _zone_at(self.cursor_x, self.bar_rect.x, self.bar_rect.width)
        self.results.append(zone)
        self._last_zone_flash = zone
        self.strike_index += 1
        if self.strike_index >= self.NUM_STRIKES:
            self._finalise()
        else:
            self.cursor_x = float(self.bar_rect.x + self.bar_rect.width // 2)
            self.cursor_dir = 1

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._bonus_amount = 0
                self._xp_multiplier = 1.0
                self._outcome = "Skipped"
                self._close()
                return
            if self.phase == self.PHASE_STRIKE and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._record_strike()
                return
            if self.phase == self.PHASE_INTRO and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.phase = self.PHASE_STRIKE
                return
            if self.phase == self.PHASE_RESULT and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._close()
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.phase == self.PHASE_INTRO:
                self.phase = self.PHASE_STRIKE
                return
            if self.phase == self.PHASE_STRIKE:
                if self._btn_strike and self._btn_strike.collidepoint(pos):
                    self._record_strike()
                    return
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._bonus_amount = 0
                    self._xp_multiplier = 1.0
                    self._outcome = "Skipped"
                    self._close()
                    return
                if self.bar_rect.collidepoint(pos):
                    self.cursor_x = float(pos[0])
                    self._record_strike()
                    return
            if self.phase == self.PHASE_RESULT:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._close()
                    return

    def update(self, dt):
        if self.phase == self.PHASE_INTRO:
            self._intro_timer -= dt
            if self._intro_timer <= 0.0:
                self.phase = self.PHASE_STRIKE
            return
        if self.phase == self.PHASE_STRIKE:
            bar = self.bar_rect
            self.cursor_x += self.cursor_dir * self.SWEEP_SPEED * dt
            if self.cursor_x >= bar.right:
                self.cursor_x = float(bar.right)
                self.cursor_dir = -1
            elif self.cursor_x <= bar.x:
                self.cursor_x = float(bar.x)
                self.cursor_dir = 1
            return
        if self.phase == self.PHASE_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._close()

    def draw(self, surface):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        _draw_panel(
            surface, self.panel_rect,
            "Iron Forge",
            "Hammer when the cursor is in the gold zone -- three hits in a row.",
            (self.font_title, self.font_small),
        )
        pr = self.panel_rect
        mouse_pos = pygame.mouse.get_pos()

        # Strike indicator (anvil icons)
        icon_size = 24
        gap = 10
        total_w = self.NUM_STRIKES * icon_size + (self.NUM_STRIKES - 1) * gap
        x = pr.centerx - total_w // 2
        y = pr.y + 90
        for i in range(self.NUM_STRIKES):
            rect = pygame.Rect(x + i * (icon_size + gap), y, icon_size, icon_size)
            if i < len(self.results):
                pygame.draw.rect(surface, BAR_BULLSEYE, rect, border_radius=6)
                pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, rect, width=2, border_radius=6)
                letter = {"bullseye": "B", "good": "G", "miss": "X"}.get(self.results[i], "?")
                t = self.font_small.render(letter, True, TEXT_LIGHT)
                surface.blit(t, t.get_rect(center=rect.center))
            else:
                pygame.draw.rect(surface, ANVIL_BG, rect, border_radius=6)
                pygame.draw.rect(surface, ANVIL_BORDER, rect, width=2, border_radius=6)

        # Bar
        br = self.bar_rect
        bw, bh = br.width, br.height
        cx = br.centerx
        pygame.draw.rect(surface, BAR_BG, br, border_radius=8)
        miss_w = int(bw * 0.22)
        pygame.draw.rect(surface, BAR_MISS, pygame.Rect(br.x, br.y, miss_w, bh), border_radius=8)
        pygame.draw.rect(surface, BAR_MISS, pygame.Rect(br.right - miss_w, br.y, miss_w, bh), border_radius=8)
        good_w = int(bw * 0.28)
        pygame.draw.rect(surface, BAR_GOOD, pygame.Rect(br.x + miss_w, br.y, good_w, bh), border_radius=6)
        pygame.draw.rect(surface, BAR_GOOD, pygame.Rect(br.right - miss_w - good_w, br.y, good_w, bh), border_radius=6)
        bull_w = int(bw * 0.22)
        pygame.draw.rect(surface, BAR_BULLSEYE, pygame.Rect(cx - bull_w // 2, br.y, bull_w, bh), border_radius=4)
        pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, br, width=2, border_radius=8)

        if self.phase in (self.PHASE_STRIKE, self.PHASE_INTRO):
            cx_pos = int(self.cursor_x)
            cursor_top = br.y - 12
            cursor_rect = pygame.Rect(cx_pos - 3, cursor_top, 6, bh + 18)
            pygame.draw.rect(surface, BAR_CURSOR, cursor_rect, border_radius=2)
            pygame.draw.line(surface, BAR_CURSOR_GLOW,
                             (cx_pos, cursor_top - 4),
                             (cx_pos, cursor_top + 4), 3)

        if self.phase == self.PHASE_INTRO:
            hint = self.font_medium.render("Click / SPACE to start the forge hammer", True, TEXT_LIGHT)
            surface.blit(hint, (pr.centerx - hint.get_width() // 2, pr.y + pr.height - 90))
        elif self.phase == self.PHASE_STRIKE:
            btn_w = 130
            btn_h = 38
            strike_rect = pygame.Rect(pr.centerx - btn_w - 10, pr.bottom - 60, btn_w, btn_h)
            skip_rect = pygame.Rect(pr.centerx + 10, pr.bottom - 60, btn_w, btn_h)
            self._btn_strike = strike_rect
            self._btn_skip = skip_rect
            _draw_button(surface, self.font_medium, strike_rect, "STRIKE", strike_rect.collidepoint(mouse_pos), TEXT_GOLD)
            _draw_button(surface, self.font_medium, skip_rect, "SKIP", skip_rect.collidepoint(mouse_pos))
            if self._last_zone_flash:
                zone = self._last_zone_flash
                flash = {"bullseye": "PERFECT!", "good": "GOOD", "miss": "MISS"}.get(zone, "")
                color = BAR_BULLSEYE if zone == "bullseye" else (BAR_GOOD if zone == "good" else BAR_MISS)
                fs = self.font_medium.render(flash, True, color)
                surface.blit(fs, (pr.centerx - fs.get_width() // 2, pr.bottom - 110))
        elif self.phase == self.PHASE_RESULT:
            out_surf = self.font_large.render(self._outcome, True, self._outcome_color)
            surface.blit(out_surf, (pr.centerx - out_surf.get_width() // 2, pr.y + 130))
            if self._bonus_amount > 0:
                bonus = self.font_medium.render(
                    "+%d bonus ingot (smelt XP x%g)" % (self._bonus_amount, self._xp_multiplier),
                    True, TEXT_GOOD,
                )
            else:
                bonus = self.font_medium.render("No bonus -- base output only", True, TEXT_DIM)
            surface.blit(bonus, (pr.centerx - bonus.get_width() // 2, pr.y + 130 + out_surf.get_height() + 6))
            btn_w = 160
            btn_h = 38
            cont = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = cont
            _draw_button(surface, self.font_medium, cont, "Continue", cont.collidepoint(mouse_pos), TEXT_GOLD)
