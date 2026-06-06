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

def _draw_majestic_background(surface):
    import math, pygame
    w, h = surface.get_size()
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((10, 5, 20, 180)) # Deep violet-black base
    time_ms = pygame.time.get_ticks()
    pulse = math.sin(time_ms * 0.001) * 20
    center_glow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(center_glow, (80, 20, 100, int(40 + pulse)), (w//2, h//2), int(h*0.8))
    pygame.draw.circle(center_glow, (120, 60, 20, int(30 + pulse)), (w//2, h), int(h*0.6))
    overlay.blit(center_glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    
    # Tiny floating embers in the background
    for i in range(40):
        seed = i * 7331
        speed = 10 + (seed % 20)
        x = (seed * 19) % w
        y = h - ((time_ms / 1000.0 * speed + seed * 83) % (h + 50))
        wobble = math.sin(time_ms * 0.0015 + i) * 20
        alpha = int(abs(math.sin(time_ms * 0.002 + i)) * 100) + 20
        pygame.draw.circle(overlay, (255, 120, 50, alpha), (int(x + wobble), int(y)), 1)
        
    surface.blit(overlay, (0, 0))


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


def _draw_panel(surface, panel_rect, title, subtitle, fonts, majestic=True):
    import math
    
    # 1. Soft, realistic multi-layered drop shadow
    for i in range(4):
        offset = (i + 1) * 4
        sh_surf = pygame.Surface((panel_rect.width + offset*2, panel_rect.height + offset*2), pygame.SRCALPHA)
        alpha = 60 - i * 12
        pygame.draw.rect(sh_surf, (0, 0, 0, alpha), sh_surf.get_rect(), border_radius=24)
        surface.blit(sh_surf, (panel_rect.x - offset, panel_rect.y - offset + 6))

    # 2. Base Panel with Rich Vertical Gradient
    panel_surf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
    color_top = (28, 30, 42)
    color_bottom = (14, 15, 22)
    for y in range(panel_rect.height):
        ratio = y / float(panel_rect.height)
        r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        pygame.draw.line(panel_surf, (r, g, b, 245), (0, y), (panel_rect.width, y))
        
    # 3. Majestic Magical & Forge Glows
    if majestic:
        time_ms = pygame.time.get_ticks()
        pulse = (math.sin(time_ms * 0.002) + 1) / 2
        
        # Subtle violet magical inner tint
        pygame.draw.rect(panel_surf, (110, 60, 180, int(20 + 15 * pulse)), panel_surf.get_rect(), border_radius=20)
        
        # Warm forge bottom glow
        glow_bottom = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        for y in range(int(panel_rect.height * 0.4), panel_rect.height):
            alpha = int(((y - panel_rect.height * 0.4) / (panel_rect.height * 0.6)) * (90 + 30 * pulse))
            pygame.draw.line(glow_bottom, (255, 110, 20, alpha), (0, y), (panel_rect.width, y))
        panel_surf.blit(glow_bottom, (0, 0))
        
        # Corner ambient sparks
        for i in range(15):
            seed = i * 4321
            speed = 15 + (seed % 20)
            x = (seed * 37) % panel_rect.width
            y = panel_rect.height - ((time_ms / 1000.0 * speed + seed * 73) % (panel_rect.height * 0.6))
            wobble = math.sin(time_ms * 0.003 + i) * 10
            alpha = int(abs(math.sin(time_ms * 0.004 + i)) * 180)
            pygame.draw.circle(panel_surf, (255, 180, 80, alpha), (int(x + wobble), int(y)), 1)

    # 4. Clip the panel to a smooth rounded rectangle
    mask = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=20)
    panel_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    
    # 5. Draw the panel onto the screen
    surface.blit(panel_surf, panel_rect.topleft)

    # 6. Beautiful Metallic Borders
    pygame.draw.rect(surface, (70, 75, 90), panel_rect, width=2, border_radius=20) # Outer rim
    inner_rect = panel_rect.inflate(-12, -12)
    pygame.draw.rect(surface, (45, 48, 60), inner_rect, width=1, border_radius=16) # Inner dark rim
    
    # Subtle top highlight to simulate bevel
    pygame.draw.line(surface, (120, 125, 140), (panel_rect.x + 25, panel_rect.y + 2), (panel_rect.right - 25, panel_rect.y + 2), 1)

    # 7. Typography and Divider
    font_title, font_sub = fonts
    title_surf = font_title.render(title, True, (255, 215, 100))
    # Render title drop shadow
    shadow_surf = font_title.render(title, True, (0, 0, 0))
    surface.blit(shadow_surf, (panel_rect.centerx - shadow_surf.get_width() // 2 + 2, panel_rect.y + 22))
    surface.blit(title_surf, (panel_rect.centerx - title_surf.get_width() // 2, panel_rect.y + 20))

    # Elegant divider under title
    div_y = panel_rect.y + 20 + title_surf.get_height() + 10
    div_w = int(panel_rect.width * 0.6)
    div_rect = pygame.Rect(panel_rect.centerx - div_w // 2, div_y, div_w, 2)
    pygame.draw.rect(surface, (100, 105, 120), div_rect)
    pygame.draw.circle(surface, (255, 215, 100), (panel_rect.centerx, div_y + 1), 4)

    # Subtitle
    if subtitle:
        sub_surf = font_sub.render(subtitle, True, (180, 185, 200))
        surface.blit(sub_surf, (panel_rect.centerx - sub_surf.get_width() // 2, div_y + 15))


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
        _draw_majestic_background(surface)

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
        _draw_majestic_background(surface)

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
# Minigame chain
# ---------------------------------------------------------------------------

CHAIN_STEP_NAMES = {
    "tending": "Tending the Fire",
    "forge": "Forging",
    "quench": "Quenching",
    "bellows": "Bellows Pump",
    "pattern": "Pattern Hammer",
    "temper": "Tempering",
}

CHAIN_TITLES = {
    ("forge", "quench"): "Steel Forging",
    ("forge", "pattern", "temper"): "Damascus Forging",
    ("bellows", "temper"): "Steel Tempering",
}

# ===========================================================================
# Pattern Hammer (Damascus Patterning)
# ===========================================================================

class PatternMinigame:
    """A majestic rhythm-based pattern forging challenge.
    
    Glowing runes (notes) slide towards a target strike zone. The player
    must press SPACE or click right as the rune enters the target zone
    to hammer the pattern into the metal. The precision of strikes 
    determines the overall score.
    """

    PHASE_INTRO = "intro"
    PHASE_ACTIVE = "active"
    PHASE_RESULT = "result"

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
        panel_h = int(sh * 0.52)
        self.panel_rect = pygame.Rect(
            (sw - panel_w) // 2,
            (sh - panel_h) // 2,
            panel_w, panel_h,
        )

        self.track_rect = pygame.Rect(
            self.panel_rect.x + int(40 * cfg.ui_scale()),
            self.panel_rect.centery - int(10 * cfg.ui_scale()),
            self.panel_rect.width - int(80 * cfg.ui_scale()),
            int(36 * cfg.ui_scale()),
        )
        self.target_x = self.track_rect.right - int(50 * cfg.ui_scale())
        
        self.phase = self.PHASE_INTRO
        self._intro_timer = 1.0
        self._result_timer = 0.0
        self._outcome = ""
        self._outcome_color = TEXT_LIGHT
        self._xp_multiplier = 1.0
        self._bonus_amount = 0
        self._btn_skip = None
        self._btn_strike = None
        
        self.t = 0.0
        self.notes = [1.0, 1.8, 2.4, 2.7, 3.5, 4.0, 4.4, 4.6, 5.0, 5.8]
        self.active_notes = []
        for n in self.notes:
            self.active_notes.append({"time": n, "hit": False, "missed": False, "flash": 0.0})
        
        self.speed = 300.0 * cfg.ui_scale()
        self.max_time = 7.0
        self.results = []
        self._last_zone_flash = ""
        self._flash_timer = 0.0

    def _finalise(self):
        score = 0
        for r in self.results:
            if r == "perfect": score += 2
            elif r == "good": score += 1
            
        max_score = len(self.notes) * 2
        
        if score >= max_score * 0.8:
            self._bonus_amount = 2
            self._xp_multiplier = 2.0
            self._outcome = "MAJESTIC PATTERN!"
            self._outcome_color = TEXT_GOLD
        elif score >= max_score * 0.5:
            self._bonus_amount = 1
            self._xp_multiplier = 1.5
            self._outcome = "Solid pattern."
            self._outcome_color = TEXT_GOOD
        elif score >= max_score * 0.2:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "Acceptable pattern."
            self._outcome_color = TEXT_LIGHT
        else:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "The pattern is deeply flawed..."
            self._outcome_color = TEXT_BAD
            
        self._result_timer = 2.4
        self.phase = self.PHASE_RESULT

    def _close(self):
        if callable(self.on_close):
            try:
                self.on_close(self._outcome, self._bonus_amount, self._xp_multiplier)
            except Exception as exc:
                logger.warning("pattern minigame on_close failed: %s", exc)
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    def _attempt_strike(self):
        if self.phase != self.PHASE_ACTIVE:
            return
            
        closest = None
        min_dist = 9999
        for note in self.active_notes:
            if not note["hit"] and not note["missed"]:
                note_x = self.track_rect.x + (self.t - note["time"]) * self.speed + (self.target_x - self.track_rect.x)
                dist = abs(note_x - self.target_x)
                if dist < min_dist:
                    min_dist = dist
                    closest = note
                    
        if closest and min_dist < int(40 * cfg.ui_scale()):
            if min_dist < int(15 * cfg.ui_scale()):
                self.results.append("perfect")
                self._last_zone_flash = "perfect"
                closest["flash"] = 1.0
            else:
                self.results.append("good")
                self._last_zone_flash = "good"
                closest["flash"] = 0.5
            closest["hit"] = True
            self._flash_timer = 0.5
        else:
            self.results.append("miss")
            self._last_zone_flash = "miss"
            self._flash_timer = 0.5

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._bonus_amount = 0
                self._xp_multiplier = 1.0
                self._outcome = "Skipped"
                self._close()
                return
            if self.phase == self.PHASE_ACTIVE and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._attempt_strike()
                return
            if self.phase == self.PHASE_INTRO and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.phase = self.PHASE_ACTIVE
                return
            if self.phase == self.PHASE_RESULT and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._close()
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
                if self._btn_strike and self._btn_strike.collidepoint(pos):
                    self._attempt_strike()
                    return
                if self.track_rect.inflate(20, 40).collidepoint(pos):
                    self._attempt_strike()
                    return
            if self.phase == self.PHASE_RESULT:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._close()
                    return

    def update(self, dt):
        if self.phase == self.PHASE_INTRO:
            self._intro_timer -= dt
            if self._intro_timer <= 0.0:
                self.phase = self.PHASE_ACTIVE
            return
        if self.phase == self.PHASE_ACTIVE:
            self.t += dt
            self._flash_timer = max(0.0, self._flash_timer - dt)
            
            for note in self.active_notes:
                if not note["hit"] and not note["missed"]:
                    note_x = self.track_rect.x + (self.t - note["time"]) * self.speed + (self.target_x - self.track_rect.x)
                    if note_x > self.target_x + int(40 * cfg.ui_scale()):
                        note["missed"] = True
                        self.results.append("miss")
                        self._last_zone_flash = "miss"
                        self._flash_timer = 0.5
            
            if self.t >= self.max_time:
                self._finalise()
            return
        if self.phase == self.PHASE_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._close()

    def draw(self, surface):
        _draw_majestic_background(surface)

        shake_x = 0
        shake_y = 0
        if self.phase == self.PHASE_ACTIVE and getattr(self, '_flash_timer', 0.0) > 0.0 and getattr(self, '_last_zone_flash', '') == 'miss':
            import random
            intensity = int(self._flash_timer * 15)
            shake_x = random.randint(-intensity, intensity)
            shake_y = random.randint(-intensity, intensity)
            
        pr = self.panel_rect.move(shake_x, shake_y)
        tr = self.track_rect.move(shake_x, shake_y)
        target_x = self.target_x + shake_x

        _draw_panel(
            surface, pr,
            "Pattern Hammer",
            "Strike (SPACE/Click) when glowing runes enter the target zone.",
            (self.font_title, self.font_small),
        )
        mouse_pos = pygame.mouse.get_pos()

        pygame.draw.rect(surface, BAR_BG, tr, border_radius=8)
        pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, tr, width=2, border_radius=8)
        
        target_rect = pygame.Rect(target_x - 15, tr.y - 4, 30, tr.height + 8)
        pygame.draw.rect(surface, BAR_BULLSEYE, target_rect, border_radius=4)
        pygame.draw.rect(surface, BAR_CURSOR_GLOW, target_rect, width=2, border_radius=4)

        if self.phase == self.PHASE_ACTIVE:
            for note in self.active_notes:
                if not note["hit"] and not note["missed"]:
                    note_x = tr.x + (self.t - note["time"]) * self.speed + (target_x - tr.x)
                    if tr.x <= note_x <= tr.right + 20:
                        n_rect = pygame.Rect(int(note_x) - 10, tr.y + 4, 20, tr.height - 8)
                        pygame.draw.rect(surface, (100, 220, 255), n_rect, border_radius=4)
                        pygame.draw.rect(surface, (200, 255, 255), n_rect, width=2, border_radius=4)
                        
                        letter = "R"
                        t = self.font_small.render(letter, True, (255, 255, 255))
                        surface.blit(t, t.get_rect(center=n_rect.center))

        if self.phase == self.PHASE_INTRO:
            hint = self.font_medium.render("Click / SPACE to start the rhythm forge", True, TEXT_LIGHT)
            surface.blit(hint, (pr.centerx - hint.get_width() // 2, pr.y + pr.height - 90))
        elif self.phase == self.PHASE_ACTIVE:
            btn_w = 130
            btn_h = 38
            strike_rect = pygame.Rect(pr.centerx - btn_w - 10, pr.bottom - 60, btn_w, btn_h)
            skip_rect = pygame.Rect(pr.centerx + 10, pr.bottom - 60, btn_w, btn_h)
            self._btn_strike = strike_rect
            self._btn_skip = skip_rect
            _draw_button(surface, self.font_medium, strike_rect, "STRIKE", strike_rect.collidepoint(mouse_pos), TEXT_GOLD)
            _draw_button(surface, self.font_medium, skip_rect, "SKIP", skip_rect.collidepoint(mouse_pos))
            
            if self._flash_timer > 0.0:
                zone = self._last_zone_flash
                flash = {"perfect": "MAJESTIC!", "good": "GOOD", "miss": "MISS"}.get(zone, "")
                color = BAR_BULLSEYE if zone == "perfect" else (BAR_GOOD if zone == "good" else BAR_MISS)
                fs = self.font_medium.render(flash, True, color)
                alpha = int(255 * (self._flash_timer / 0.5))
                fs.set_alpha(alpha)
                surface.blit(fs, (pr.centerx - fs.get_width() // 2, pr.bottom - 110))
                
        elif self.phase == self.PHASE_RESULT:
            out_surf = self.font_large.render(self._outcome, True, self._outcome_color)
            surface.blit(out_surf, (pr.centerx - out_surf.get_width() // 2, pr.y + 130))
            if self._bonus_amount > 0:
                bonus = self.font_medium.render(
                    "+%d pattern quality (smelt XP x%g)" % (self._bonus_amount, self._xp_multiplier),
                    True, TEXT_GOOD,
                )
            else:
                bonus = self.font_medium.render("No bonus -- basic pattern only", True, TEXT_DIM)
            surface.blit(bonus, (pr.centerx - bonus.get_width() // 2, pr.y + 130 + out_surf.get_height() + 6))
            btn_w = 160
            btn_h = 38
            cont = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = cont
            _draw_button(surface, self.font_medium, cont, "Continue", cont.collidepoint(mouse_pos), TEXT_GOLD)



class MinigameChain:
    """Wrapper that plays several minigames in sequence.

    Each step in the chain is a separate minigame.  When one finishes,
    the next starts automatically.  Bonuses and XP multipliers are
    accumulated across all steps; the final :meth:`on_close` callback
    receives the aggregated results.

    The chain shares the same ``update`` / ``draw`` / ``handle_event``
    interface as individual minigames so the smeltery menu treats it
    transparently.
    """

    PHASE_PLAYING = "playing"
    PHASE_RESULT = "result"

    def __init__(self, app, chain_ids, *, on_close=None, smelting_level=1):
        self.app = app
        self.chain_ids = list(chain_ids)
        self.final_on_close = on_close
        self.smelting_level = max(1, int(smelting_level))

        sw, sh = app.screen.get_size()
        self.screen_w = sw
        self.screen_h = sh

        self.font_title = cfg.get_font(max(12, int(40 * cfg.ui_scale())))
        self.font_large = cfg.get_font(max(11, int(30 * cfg.ui_scale())))
        self.font_medium = cfg.get_font(max(10, int(22 * cfg.ui_scale())))
        self.font_small = cfg.get_font(max(8, int(18 * cfg.ui_scale())))

        self.phase = self.PHASE_PLAYING
        self.current_index = 0
        self.current_minigame = None
        self._total_bonus = 0
        self._total_xp_mult = 1.0
        self._step_results = []
        self._closed = False

        chain_key = tuple(chain_ids)
        self.chain_title = CHAIN_TITLES.get(chain_key, "Forging Chain")

        self._step_labels = [
            CHAIN_STEP_NAMES.get(mid, mid.replace("_", " ").title())
            for mid in chain_ids
        ]

        self._start_current()

    def _step_on_close(self, outcome, bonus_amount, xp_multiplier):
        self._step_results.append((outcome, bonus_amount, xp_multiplier))
        self._total_bonus += int(bonus_amount or 0)
        self._total_xp_mult *= float(xp_multiplier or 1.0)
        self.current_index += 1
        self._start_current()

    def _start_current(self):
        if self.current_index >= len(self.chain_ids):
            self._finish_chain()
            return
        mg_id = self.chain_ids[self.current_index]
        cls = None
        if mg_id == "tending": cls = TendingFireMinigame
        elif mg_id == "forge": cls = ForgeMinigame
        elif mg_id == "quench": cls = QuenchMinigame
        elif mg_id == "bellows": cls = BellowsMinigame
        elif mg_id == "temper": cls = TemperMinigame
        elif mg_id == "pattern": cls = PatternMinigame
        
        if cls is None:
            logger.warning("MinigameChain: unknown minigame id %r, skipping", mg_id)
            self.current_index += 1
            self._start_current()
            return
        try:
            self.current_minigame = cls(
                self.app,
                on_close=self._step_on_close,
                smelting_level=self.smelting_level,
            )
        except Exception as exc:
            logger.warning("MinigameChain: failed to create %s: %s", mg_id, exc)
            self.current_index += 1
            self._start_current()

    def _finish_chain(self):
        self.phase = self.PHASE_RESULT
        if self._total_bonus > 0:
            self._outcome = "Chain complete! (+%d bonus)" % self._total_bonus
            self._outcome_color = TEXT_GOLD
        else:
            self._outcome = "Chain complete."
            self._outcome_color = TEXT_LIGHT
        self._result_timer = 2.0

    def _close(self):
        if self._closed:
            return
        self._closed = True
        if callable(self.final_on_close):
            try:
                self.final_on_close(self._outcome, self._total_bonus, self._total_xp_mult)
            except Exception as exc:
                logger.warning("MinigameChain final on_close failed: %s", exc)
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    def _draw_chain_hud(self, surface):
        total = len(self.chain_ids)
        step = min(self.current_index + 1, total)
        label = "Step %d/%d: %s" % (step, total, self._step_labels[self.current_index] if self.current_index < total else "")
        suf = self.font_small.render(label, True, TEXT_GOLD)
        surface.blit(suf, (self.screen_w // 2 - suf.get_width() // 2, int(20 * cfg.ui_scale())))

        bar_w = int(240 * cfg.ui_scale())
        bar_h = int(8 * cfg.ui_scale())
        bar_x = self.screen_w // 2 - bar_w // 2
        bar_y = int(20 * cfg.ui_scale()) + suf.get_height() + int(6 * cfg.ui_scale())
        bar_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(surface, BAR_BG, bar_rect, border_radius=4)
        pygame.draw.rect(surface, ANVIL_BORDER, bar_rect, width=1, border_radius=4)
        fill_w = max(1, int(bar_w * step / total))
        fill = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
        pygame.draw.rect(surface, BAR_BULLSEYE, fill, border_radius=4)

    def update(self, dt):
        if self.current_minigame is not None:
            self.current_minigame.update(dt)
        elif self.phase == self.PHASE_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._close()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.current_minigame = None
            self._total_bonus = 0
            self._total_xp_mult = 1.0
            self._outcome = "Chain skipped"
            self._outcome_color = TEXT_BAD
            self._close()
            return
        if self.current_minigame is not None:
            self.current_minigame.handle_event(event)

    def draw(self, surface):
        if self.current_minigame is not None:
            self.current_minigame.draw(surface)
            self._draw_chain_hud(surface)
        elif self.phase == self.PHASE_RESULT:
            _draw_majestic_background(surface)
            pr = pygame.Rect(
                (self.screen_w - 500) // 2,
                (self.screen_h - 200) // 2,
                500, 200,
            )
            _draw_panel(
                surface, pr,
                self.chain_title,
                self._outcome,
                (self.font_title, self.font_medium),
            )
            if self._total_bonus > 0:
                bonus = self.font_medium.render(
                    "+%d bonus items (smelt XP x%g)" % (self._total_bonus, self._total_xp_mult),
                    True, TEXT_GOOD,
                )
                surface.blit(bonus, (pr.centerx - bonus.get_width() // 2, pr.centery + 10))
            else:
                bonus = self.font_medium.render("No bonus -- base output only", True, TEXT_DIM)
                surface.blit(bonus, (pr.centerx - bonus.get_width() // 2, pr.centery + 10))


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
    if mg_id == "bellows":
        return BellowsMinigame(app, on_close=on_close, smelting_level=smelting_level)
    if mg_id == "temper":
        return TemperMinigame(app, on_close=on_close, smelting_level=smelting_level)
    if mg_id == "pattern":
        return PatternMinigame(app, on_close=on_close, smelting_level=smelting_level)
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
        _draw_majestic_background(surface)

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
            return  # end of file


# ===========================================================================
# Bellows Pump (iron-ore + coal -> iron-ingot blast furnace)
# ===========================================================================

class BellowsMinigame:
    """Rapid-click pressure challenge for iron smelting.

    A vertical pressure gauge with a needle that naturally falls. The
    player must click / press SPACE to pump the bellows and keep the
    pressure inside a gold target zone for a cumulative duration.  If
    the pressure drops below a critical threshold the fire dies and the
    batch yields no bonus.
    """

    PHASE_INTRO = "intro"
    PHASE_ACTIVE = "active"
    PHASE_RESULT = "result"

    PUMP_FORCE = 0.14
    DRAG = 0.10
    HOLD_TARGET = 1.8
    ZONE_CENTER = 0.55
    ZONE_WIDTH = 0.24
    CRITICAL_FLOOR = 0.08
    CRITICAL_TOLERANCE = 0.6

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

        panel_w = int(sw * 0.60)
        panel_h = int(sh * 0.54)
        self.panel_rect = pygame.Rect(
            (sw - panel_w) // 2,
            (sh - panel_h) // 2,
            panel_w, panel_h,
        )
        gauge_w = 28
        gauge_h = int(panel_h * 0.60)
        gauge_x = self.panel_rect.centerx - gauge_w // 2
        gauge_y = self.panel_rect.y + int(panel_h * 0.28)
        self.gauge_rect = pygame.Rect(gauge_x, gauge_y, gauge_w, gauge_h)

        self.phase = self.PHASE_INTRO
        self.pressure = 0.5
        self.hold_time = 0.0
        self._critical_time = 0.0
        self._intro_timer = 1.0
        self._result_timer = 0.0
        self._outcome = ""
        self._outcome_color = TEXT_LIGHT
        self._xp_multiplier = 1.0
        self._bonus_amount = 0
        self._btn_skip = None

    def _finalise(self, perfect, success):
        if perfect:
            self._bonus_amount = 2
            self._xp_multiplier = 2.0
            self._outcome = "BELLOWS MASTERY!"
            self._outcome_color = TEXT_GOLD
        elif success:
            self._bonus_amount = 1
            self._xp_multiplier = 1.5
            self._outcome = "Strong bellows work."
            self._outcome_color = TEXT_GOOD
        else:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "The fire died out..."
            self._outcome_color = TEXT_BAD
        self._result_timer = 2.2
        self.phase = self.PHASE_RESULT

    def _close(self):
        if callable(self.on_close):
            try:
                self.on_close(self._outcome, self._bonus_amount, self._xp_multiplier)
            except Exception as exc:
                logger.warning("bellows minigame on_close failed: %s", exc)
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
                self.pressure = min(1.0, self.pressure + self.PUMP_FORCE)
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
                self.pressure = min(1.0, self.pressure + self.PUMP_FORCE)
                return
            if self.phase == self.PHASE_RESULT:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._close()
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

        self.pressure = max(0.0, self.pressure - self.DRAG * dt)

        zone_low = self.ZONE_CENTER - self.ZONE_WIDTH * 0.5
        zone_high = self.ZONE_CENTER + self.ZONE_WIDTH * 0.5
        in_zone = zone_low <= self.pressure <= zone_high

        if in_zone:
            self.hold_time += dt
            self._critical_time = 0.0
        else:
            self._critical_time += dt

        if self.pressure < self.CRITICAL_FLOOR and self._critical_time > self.CRITICAL_TOLERANCE:
            self._finalise(perfect=False, success=False)
            return

        if self.hold_time >= self.HOLD_TARGET:
            perfect = self._critical_time < 0.1 and self.hold_time < self.HOLD_TARGET * 1.3
            self._finalise(perfect=perfect, success=True)
            return

    def draw(self, surface):
        _draw_majestic_background(surface)

        _draw_panel(
            surface, self.panel_rect,
            "Bellows Pump",
            "Pump the bellows -- keep the pressure in the gold zone.",
            (self.font_title, self.font_small),
        )
        pr = self.panel_rect
        mouse_pos = pygame.mouse.get_pos()

        gr = self.gauge_rect
        gh = gr.height
        pygame.draw.rect(surface, BAR_BG, gr, border_radius=8)

        zone_low = int(gh * (1.0 - (self.ZONE_CENTER + self.ZONE_WIDTH * 0.5)))
        zone_high = int(gh * (1.0 - (self.ZONE_CENTER - self.ZONE_WIDTH * 0.5)))
        zone_rect = pygame.Rect(gr.x, gr.y + zone_low, gr.width, max(4, zone_high - zone_low))
        pygame.draw.rect(surface, BAR_BULLSEYE, zone_rect, border_radius=4)

        pressure_y = gr.bottom - int(self.pressure * gh) - 4
        cursor_h = 10
        cursor_rect = pygame.Rect(gr.x - 6, pressure_y, gr.width + 12, cursor_h)
        pressure_color = (60, 200, 60) if self.pressure > 0.3 else (200, 60, 30)
        pygame.draw.rect(surface, pressure_color, cursor_rect, border_radius=3)
        pygame.draw.rect(surface, BAR_CURSOR, cursor_rect, width=1, border_radius=3)
        pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, gr, width=2, border_radius=8)

        if self.pressure < self.CRITICAL_FLOOR:
            warn = self.font_small.render("FIRE DYING!", True, TEXT_BAD)
            surface.blit(warn, (gr.right + 24, pressure_y - warn.get_height() // 2))

        bar_fill = int(gh * (self.hold_time / self.HOLD_TARGET))
        if bar_fill > 0:
            fill_rect = pygame.Rect(gr.x + 2, gr.bottom - bar_fill - 1, gr.width - 4, bar_fill)
            pygame.draw.rect(surface, (100, 200, 220), fill_rect, border_radius=3)

        if self.phase == self.PHASE_INTRO:
            hint = self.font_medium.render("Click / SPACE to start pumping the bellows", True, TEXT_LIGHT)
            surface.blit(hint, (pr.centerx - hint.get_width() // 2, pr.y + pr.height - 90))
        elif self.phase == self.PHASE_ACTIVE:
            btn_w = 130
            btn_h = 38
            skip_rect = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = skip_rect
            _draw_button(surface, self.font_medium, skip_rect, "SKIP", skip_rect.collidepoint(mouse_pos))
            tip = self.font_medium.render("PUMP!" if self.pressure < self.ZONE_CENTER else "Hold...", True, TEXT_GOOD)
            surface.blit(tip, (pr.centerx - tip.get_width() // 2, pr.bottom - 110))
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







# ===========================================================================
# Temper (iron-ingot + coke -> steel-ingot alternative / high-end)
# ===========================================================================
# Temper (iron-ingot + coke -> steel-ingot alternative / high-end)
# ===========================================================================

class TemperMinigame:
    """Multi-stage colour-match tempering challenge for steel.

    A glowing ingot cycles through colours as it heats and cools.  The
    player must press SPACE / click when the ingot colour matches the
    target colour shown above.  5 stages; the cycle speeds up each
    stage.  Precision across all stages determines the bonus yield and
    XP multiplier.
    """

    PHASE_INTRO = "intro"
    PHASE_STAGE = "stage"
    PHASE_RESULT = "result"

    STAGES = 5
    CYCLE_SPEED_BASE = 0.8
    CYCLE_SPEED_INCREMENT = 0.3
    MATCH_THRESHOLD = 0.10

    COLOUR_CYCLE = [
        (80, 20, 10),
        (160, 40, 20),
        (220, 100, 40),
        (255, 180, 60),
        (255, 220, 130),
        (255, 240, 200),
        (255, 220, 130),
        (255, 180, 60),
        (220, 100, 40),
        (160, 40, 20),
    ]

    TARGET_COLOURS = [
        (220, 100, 40),
        (255, 180, 60),
        (255, 220, 130),
        (255, 240, 200),
        (255, 180, 60),
    ]

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

        panel_w = int(sw * 0.60)
        panel_h = int(sh * 0.52)
        self.panel_rect = pygame.Rect(
            (sw - panel_w) // 2,
            (sh - panel_h) // 2,
            panel_w, panel_h,
        )

        self.ingot_centre = (self.panel_rect.centerx, self.panel_rect.centery + 20)
        self.ingot_radius = int(72 * cfg.ui_scale())

        self.target_swatch_rect = pygame.Rect(
            self.panel_rect.centerx - int(30 * cfg.ui_scale()),
            self.panel_rect.y + int(28 * cfg.ui_scale()),
            int(60 * cfg.ui_scale()),
            int(24 * cfg.ui_scale()),
        )

        self.phase = self.PHASE_INTRO
        self.stage_index = 0
        self.results = []
        self._cycle_t = 0.0
        self._stage_timer = 0.0
        self._input_locked_timer = 0.0
        self._final_stage = False
        self._intro_timer = 1.0
        self._result_timer = 0.0
        self._outcome = ""
        self._outcome_color = TEXT_LIGHT
        self._xp_multiplier = 1.0
        self._bonus_amount = 0
        self._btn_skip = None
        self._last_result = ""

    def _current_cycle_speed(self):
        return self.CYCLE_SPEED_BASE + self.stage_index * self.CYCLE_SPEED_INCREMENT

    def _ingot_colour(self):
        t = self._cycle_t
        idx = int(t) % len(self.COLOUR_CYCLE)
        frac = t - int(t)
        next_idx = (idx + 1) % len(self.COLOUR_CYCLE)
        c1 = self.COLOUR_CYCLE[idx]
        c2 = self.COLOUR_CYCLE[next_idx]
        return (
            int(c1[0] + (c2[0] - c1[0]) * frac),
            int(c1[1] + (c2[1] - c1[1]) * frac),
            int(c1[2] + (c2[2] - c1[2]) * frac),
        )

    def _colour_distance(self, c1, c2):
        return math.sqrt(
            (c1[0] - c2[0]) ** 2 +
            (c1[1] - c2[1]) ** 2 +
            (c1[2] - c2[2]) ** 2
        ) / math.sqrt(3 * 255 ** 2)

    def _attempt_match(self):
        if self.phase != self.PHASE_STAGE:
            return
        if self._input_locked_timer > 0.0:
            return
        ingot_c = self._ingot_colour()
        target_c = self.TARGET_COLOURS[self.stage_index % len(self.TARGET_COLOURS)]
        dist = self._colour_distance(ingot_c, target_c)
        if dist <= 0.08:
            self.results.append("perfect")
            self._last_result = "PERFECT!"
        elif dist <= self.MATCH_THRESHOLD:
            self.results.append("good")
            self._last_result = "Good match"
        else:
            self.results.append("miss")
            self._last_result = "Mismatch"
        self._input_locked_timer = 0.4
        self.stage_index += 1
        if self.stage_index >= self.STAGES:
            self._finalise()
        else:
            self._stage_timer = 1.2
            self._cycle_t = 0.0

    def _finalise(self):
        perfects = sum(1 for r in self.results if r == "perfect")
        goods = sum(1 for r in self.results if r == "good")
        if perfects >= 4:
            self._bonus_amount = 2
            self._xp_multiplier = 2.5
            self._outcome = "MASTER TEMPER!"
            self._outcome_color = TEXT_GOLD
        elif perfects >= 2:
            self._bonus_amount = 1
            self._xp_multiplier = 1.5
            self._outcome = "Well tempered."
            self._outcome_color = TEXT_GOOD
        elif goods + perfects >= 3:
            self._bonus_amount = 0
            self._xp_multiplier = 1.2
            self._outcome = "Adequate temper."
            self._outcome_color = TEXT_LIGHT
        else:
            self._bonus_amount = 0
            self._xp_multiplier = 1.0
            self._outcome = "The steel became brittle..."
            self._outcome_color = TEXT_BAD
        self._result_timer = 2.4
        self.phase = self.PHASE_RESULT

    def _close(self):
        if callable(self.on_close):
            try:
                self.on_close(self._outcome, self._bonus_amount, self._xp_multiplier)
            except Exception as exc:
                logger.warning("temper minigame on_close failed: %s", exc)
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
            if self.phase == self.PHASE_STAGE and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._attempt_match()
                return
            if self.phase == self.PHASE_INTRO and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.phase = self.PHASE_STAGE
                return
            if self.phase == self.PHASE_RESULT and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._close()
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.phase == self.PHASE_INTRO:
                self.phase = self.PHASE_STAGE
                return
            if self.phase == self.PHASE_STAGE:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._bonus_amount = 0
                    self._xp_multiplier = 1.0
                    self._outcome = "Skipped"
                    self._close()
                    return
                if self._input_locked_timer <= 0.0:
                    self._attempt_match()
                return
            if self.phase == self.PHASE_RESULT:
                if self._btn_skip and self._btn_skip.collidepoint(pos):
                    self._close()
                    return

    def update(self, dt):
        if self.phase == self.PHASE_INTRO:
            self._intro_timer -= dt
            if self._intro_timer <= 0.0:
                self.phase = self.PHASE_STAGE
            return
        if self.phase == self.PHASE_RESULT:
            self._result_timer -= dt
            if self._result_timer <= 0.0:
                self._close()
            return
        if self.phase == self.PHASE_STAGE:
            self._input_locked_timer = max(0.0, self._input_locked_timer - dt)
            if self._stage_timer > 0.0:
                self._stage_timer -= dt
                if self._stage_timer <= 0.0:
                    self._cycle_t = 0.0
            else:
                speed = self._current_cycle_speed()
                self._cycle_t += dt * speed
            return

    def draw(self, surface):
        _draw_majestic_background(surface)

        _draw_panel(
            surface, self.panel_rect,
            "Temper the Steel",
            "Click when the ingot colour matches the target.",
            (self.font_title, self.font_small),
        )
        pr = self.panel_rect
        mouse_pos = pygame.mouse.get_pos()

        ingot_c = self._ingot_colour()
        target_c = self.TARGET_COLOURS[self.stage_index % len(self.TARGET_COLOURS)]

        stage_str = "Stage %d / %d" % (self.stage_index + 1, self.STAGES)
        ss = self.font_medium.render(stage_str, True, TEXT_LIGHT)
        surface.blit(ss, (pr.centerx - ss.get_width() // 2, self.target_swatch_rect.bottom + 6))

        pygame.draw.rect(surface, target_c, self.target_swatch_rect, border_radius=4)
        pygame.draw.rect(surface, ANVIL_BORDER_LIGHT, self.target_swatch_rect, width=2, border_radius=4)
        target_label = self.font_small.render("Target", True, TEXT_DIM)
        surface.blit(target_label, (self.target_swatch_rect.centerx - target_label.get_width() // 2,
                                    self.target_swatch_rect.top - target_label.get_height() - 2))

        cx, cy = self.ingot_centre
        r = self.ingot_radius
        glow = pygame.Surface((r * 3, r * 3), pygame.SRCALPHA)
        for ir in range(r, 0, -3):
            alpha = max(0, int(120 * (1.0 - ir / r)))
            pygame.draw.circle(glow, (*ingot_c, alpha), (r * 1.5, r * 1.5), ir)
        surface.blit(glow, (cx - r * 1.5, cy - r * 1.5))

        pygame.draw.circle(surface, ingot_c, (cx, cy), r)
        pygame.draw.circle(surface, ANVIL_BORDER_LIGHT, (cx, cy), r, width=3)

        highlight = (
            min(255, ingot_c[0] + 80),
            min(255, ingot_c[1] + 80),
            min(255, ingot_c[2] + 80),
        )
        pygame.draw.circle(surface, highlight, (cx - r // 3, cy - r // 3), r // 3)

        stage_results_x = pr.left + int(20 * cfg.ui_scale())
        stage_results_y = pr.centery + r + int(30 * cfg.ui_scale())
        for i, res in enumerate(self.results):
            label = {"perfect": "O", "good": "o", "miss": "X"}.get(res, "?")
            color = TEXT_GOLD if res == "perfect" else (TEXT_GOOD if res == "good" else TEXT_BAD)
            surf = self.font_small.render(label, True, color)
            surface.blit(surf, (stage_results_x + i * 24, stage_results_y))

        if self.phase == self.PHASE_INTRO:
            hint = self.font_medium.render("Click / SPACE to begin tempering", True, TEXT_LIGHT)
            surface.blit(hint, (pr.centerx - hint.get_width() // 2, pr.y + pr.height - 90))
        elif self.phase == self.PHASE_STAGE:
            btn_w = 130
            btn_h = 38
            skip_rect = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - 60, btn_w, btn_h)
            self._btn_skip = skip_rect
            _draw_button(surface, self.font_medium, skip_rect, "SKIP", skip_rect.collidepoint(mouse_pos))
            if self._input_locked_timer > 0.0:
                tip_text = self._last_result
            else:
                tip_text = "MATCH COLOUR!"
            tip = self.font_medium.render(tip_text, True, TEXT_GOLD)
            surface.blit(tip, (pr.centerx - tip.get_width() // 2, pr.bottom - 110))
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
