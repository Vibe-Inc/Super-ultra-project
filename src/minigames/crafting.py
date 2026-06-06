"""
Crafting "Tempering" minigame / Majestic Forging Chain.

Replaces the legacy 3-strike minigame with a 5-stage majestic forging chain
that mimics real blacksmithing. The cumulative score determines the tier shift.
"""

import math
import random
import pygame

import src.config as cfg
from src.core.logger import logger
from database.crafting_tiers_db import TIER_ORDER, get_tier_name

from src.minigames.smeltery_minigames import MinigameChain, _draw_panel, BUTTON_HOVER, BUTTON_BG, BUTTON_BORDER, TEXT_LIGHT, TEXT_DIM, TEXT_GOLD, TEXT_GOOD, TEXT_BAD

def _shift_tier(tier_id: str, direction: int) -> str:
    if tier_id not in TIER_ORDER:
        return tier_id
    idx = TIER_ORDER.index(tier_id)
    idx = max(0, min(len(TIER_ORDER) - 1, idx + direction))
    return TIER_ORDER[idx]


class CraftingMinigame(MinigameChain):
    def __init__(self, app, item, on_close=None, smelting_level: int = 1):
        self.item = item
        self.original_tier = str(getattr(item, "tier", "fine") or "fine")
        
        # 5-stage majestic forging chain
        chain_ids = ["tending", "forge", "pattern", "temper", "quench"]
        super().__init__(app, chain_ids, on_close=on_close, smelting_level=smelting_level)
        
        self.chain_title = "Majestic Forging"
        self._final_tier = self.original_tier
        self._outcome_text = ""
        self._outcome_color = TEXT_LIGHT

    def _finish_chain(self):
        from src.items.items import apply_tier_to_item

        self.phase = self.PHASE_RESULT
        
        score = self._total_bonus
        
        if score >= 6:
            new_tier = _shift_tier(self.original_tier, +1)
            self._total_xp_mult = 2.0
            self._outcome_text = "MASTERFUL FORGE WORK!"
            self._outcome_color = TEXT_GOLD
        elif score >= 3:
            new_tier = self.original_tier
            self._total_xp_mult = 1.5
            self._outcome_text = "Solid craftsmanship."
            self._outcome_color = TEXT_GOOD
        elif score >= 1:
            new_tier = self.original_tier
            self._total_xp_mult = 1.0
            self._outcome_text = "Acceptable forging."
            self._outcome_color = TEXT_LIGHT
        else:
            new_tier = _shift_tier(self.original_tier, -1)
            self._total_xp_mult = 1.0
            self._outcome_text = "The item is flawed..."
            self._outcome_color = TEXT_BAD

        self._final_tier = new_tier
        try:
            apply_tier_to_item(self.item, new_tier)
        except Exception as exc:
            logger.warning(f"Failed to apply tier to item in crafting minigame: {exc}")

        self._result_timer = 3.0

    def _close(self):
        if self._closed:
            return
        self._closed = True
        if callable(self.final_on_close):
            try:
                self.final_on_close(self.item, self._total_xp_mult, self._outcome_text)
            except Exception as exc:
                logger.warning(f"crafting minigame on_close callback failed: {exc}")
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    def _draw_button(self, surface, rect, text, hovered=False, text_color=None):
        bg = BUTTON_HOVER if hovered else BUTTON_BG
        pygame.draw.rect(surface, bg, rect, border_radius=8)
        pygame.draw.rect(surface, BUTTON_BORDER, rect, width=2, border_radius=8)
        tc = text_color if text_color else TEXT_LIGHT
        txt_surf = self.font_medium.render(text, True, tc)
        txt_rect = txt_surf.get_rect(center=rect.center)
        surface.blit(txt_surf, txt_rect)

    def draw(self, surface):
        if self.current_minigame is not None:
            self.current_minigame.draw(surface)
            self._draw_chain_hud(surface)
        elif self.phase == self.PHASE_RESULT:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            surface.blit(overlay, (0, 0))
            
            pr = pygame.Rect(
                (self.screen_w - int(600 * cfg.ui_scale())) // 2,
                (self.screen_h - int(400 * cfg.ui_scale())) // 2,
                int(600 * cfg.ui_scale()), int(400 * cfg.ui_scale()),
            )
            
            _draw_panel(
                surface, pr,
                self.chain_title,
                "The forging process is complete.",
                (self.font_title, self.font_small),
                majestic=True
            )
            
            mouse_pos = pygame.mouse.get_pos()
            
            title = self.font_large.render(self._outcome_text, True, self._outcome_color)
            surface.blit(title, (pr.centerx - title.get_width() // 2, pr.y + int(100 * cfg.ui_scale())))

            try:
                from_tier = get_tier_name(self.original_tier)
                to_tier   = get_tier_name(self._final_tier)
            except Exception:
                from_tier = f"[{self.original_tier.capitalize()}]"
                to_tier   = f"[{self._final_tier.capitalize()}]"
                
            tier_text = f"{from_tier}  ->  {to_tier}"
            tier_surf = self.font_medium.render(tier_text, True, TEXT_LIGHT)
            surface.blit(tier_surf, (pr.centerx - tier_surf.get_width() // 2, pr.y + int(100 * cfg.ui_scale()) + title.get_height() + 10))

            try:
                item_name = self.item.name() if hasattr(self.item, "name") else str(self.item)
            except Exception:
                item_name = str(self.item)
            name_surf = self.font_medium.render(item_name, True, TEXT_GOLD)
            surface.blit(name_surf, (pr.centerx - name_surf.get_width() // 2, pr.y + int(100 * cfg.ui_scale()) + title.get_height() + 14 + tier_surf.get_height()))

            score_text = f"Total Quality Score: {self._total_bonus}/8"
            score_surf = self.font_small.render(score_text, True, TEXT_DIM)
            surface.blit(score_surf, (pr.centerx - score_surf.get_width() // 2, pr.bottom - int(120 * cfg.ui_scale())))

            if self._total_xp_mult != 1.0:
                xp_text = f"Smelting XP x{self._total_xp_mult:g}"
                xp_color = TEXT_GOOD if self._total_xp_mult > 1.0 else TEXT_LIGHT
                xp_surf = self.font_small.render(xp_text, True, xp_color)
                surface.blit(xp_surf, (pr.centerx - xp_surf.get_width() // 2, pr.bottom - int(95 * cfg.ui_scale())))

            btn_w = int(180 * cfg.ui_scale())
            btn_h = int(40 * cfg.ui_scale())
            continue_rect = pygame.Rect(
                pr.centerx - btn_w // 2,
                pr.bottom - int(60 * cfg.ui_scale()),
                btn_w, btn_h,
            )
            self._draw_button(surface, continue_rect, "Continue", continue_rect.collidepoint(mouse_pos), TEXT_GOLD)
            
            # Allow clicking anywhere to skip early during result phase, or continuing via button
            if pygame.mouse.get_pressed()[0] and continue_rect.collidepoint(mouse_pos):
                self._close()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.phase != self.PHASE_RESULT:
                self.current_minigame = None
                self._total_bonus = 0
                self._total_xp_mult = 1.0
                self._finish_chain()
            else:
                self._close()
            return
            
        if self.phase == self.PHASE_RESULT:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._close()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                pr = pygame.Rect(
                    (self.screen_w - int(600 * cfg.ui_scale())) // 2,
                    (self.screen_h - int(400 * cfg.ui_scale())) // 2,
                    int(600 * cfg.ui_scale()), int(400 * cfg.ui_scale()),
                )
                btn_w = int(180 * cfg.ui_scale())
                btn_h = int(40 * cfg.ui_scale())
                continue_rect = pygame.Rect(pr.centerx - btn_w // 2, pr.bottom - int(60 * cfg.ui_scale()), btn_w, btn_h)
                if continue_rect.collidepoint(mouse_pos):
                    self._close()
            return

        if self.current_minigame is not None:
            self.current_minigame.handle_event(event)

