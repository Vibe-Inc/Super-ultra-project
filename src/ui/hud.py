import math
import random
import pygame
from typing import TYPE_CHECKING
from src.entities.character import Character
from src.ui.widgets import Button
import src.config as cfg
from src.core.logger import logger
from database.effects import (
    Effect, RegenerationEffect, PoisonEffect, BurnEffect, ConfusionEffect,
    DizzinessEffect, SlowEffect, FreezeEffect, RootEffect, RadiantFortitude,
    VampiricEdge, KeenInsight, BleedEffect, StrengthEffect, Momentum,
    BlindEffect, HasteEffect, WeakenEffect, ShieldEffect, CurseEffect,
    LethargyEffect, Effect_list,
)
from src.mana.mana_system import CONSUME_ANIM_DURATION

# Ensure _ is available for gettext translations
try:
    _  # type: ignore[used-before-def]
except NameError:
    from gettext import gettext as _

if TYPE_CHECKING:
    from src.app import App

class HUD:
    """
    Head-Up Display (HUD) for player status and UI controls.

    This class is responsible for rendering player health, lives, stamina, XP,
    money, skill hotbar, and the inventory button, as well as handling related UI events.

    Attributes:
        character (Character):
            The character object whose state is being displayed.
        app (App):
            The main application object for accessing managers (e.g., INV_manager).
        toggle_inventory_callback (callable | None):
            Optional callback to toggle inventory state.
        use_skill_callback (callable | None):
            Optional callback to use a skill from a slot.
        open_shop_callback (callable | None):
            Optional callback to open the shop.
        font (pygame.font.Font):
            The font used for rendering text.
        stamina_font (pygame.font.Font):
            Font used for stamina label.
        stamina_label (pygame.Surface):
            Rendered "STAMINA" label surface.
        hp_icon (pygame.Surface):
            The icon representing health (a heart).
        life_icon (pygame.Surface):
            The icon representing the number of lives (a skull).
        inv_button (Button):
            The button to open/close the inventory.
        coin_icon (pygame.Surface):
            The coin icon surface used for money display.
        skill_slot_size (int):
            Size of each skill slot in pixels.
        skill_slot_padding (int):
            Padding between skill slots.
        skill_slots_count (int):
            Number of skill hotbar slots.
        skill_panel_margin (int):
            Margin around the skill panel.
        skill_panel_width (int):
            Width of the skill panel.
        skill_total_slots_height (int):
            Total height of all skill slots combined.
        skill_panel_x (int):
            X position of the skill panel.
        skill_panel_y (int):
            Y position of the skill panel.
        animation_time (float):
            Accumulated time for animation effects.
        hp_icon_pos (tuple[int, int]):
            Screen position of the HP icon.
        life_icon_pos (tuple[int, int]):
            Screen position of the life icon.
        hp_bar_rect (pygame.Rect):
            Rectangle for the HP bar.
        xp_bar_rect (pygame.Rect):
            Rectangle for the XP bar.
        stamina_bar_rect (pygame.Rect):
            Rectangle for the stamina bar.
        money_pos (tuple[int, int]):
            Screen position for the money display.
        _layout_size (tuple[int, int] | None):
            Cached screen size for layout recalc.
        skill_slot_rects (list[pygame.Rect]):
            List of rectangles for each skill slot.
        NEON_THEMES (dict):
            Color themes for skill elements.

    Methods:
        __init__(character, app, toggle_inventory_callback=None, use_skill_callback=None, open_shop_callback=None):
            Initialize the HUD with player character, app, and callbacks.
        _recalc_layout(screen_width, screen_height):
            Recalculate HUD positions based on the current screen size.
        _ensure_layout(screen_width, screen_height):
            Ensure layout is recalculated if screen size changed.
        toggle_inventory():
            Toggle the inventory open/closed, using callback if provided.
        handle_event(event):
            Handle mouse events for the inventory button and skill slots.
        _get_skill_theme(skill):
            Get the neon color theme for a skill based on its properties.
        _draw_hud_skill_slot(surface, rect, skill, idx):
            Draw an individual skill slot with glow and cooldown effects.
        _on_shop_clicked():
            Handle shop button click, using callback or fallback.
        draw(screen):
            Draw all HUD elements (health, stamina, XP, money, skill hotbar, inventory button).
    """

    NEON_THEMES = {
        "fire": {"primary": (255, 80, 40), "glow": (255, 120, 60), "accent": (255, 200, 100)},
        "ice": {"primary": (60, 140, 255), "glow": (100, 180, 255), "accent": (180, 220, 255)},
        "lightning": {"primary": (255, 220, 50), "glow": (255, 240, 100), "accent": (255, 255, 180)},
        "nature": {"primary": (80, 200, 100), "glow": (120, 240, 140), "accent": (180, 255, 180)},
        "shadow": {"primary": (160, 80, 220), "glow": (200, 120, 255), "accent": (220, 180, 255)},
        "arcane": {"primary": (220, 80, 180), "glow": (255, 120, 220), "accent": (255, 180, 240)},
        "default": {"primary": (100, 140, 200), "glow": (140, 180, 240), "accent": (200, 220, 255)},
    }

    def __init__(self, character: Character, app: "App", toggle_inventory_callback=None, use_skill_callback=None, open_shop_callback=None):
        self.character = character
        self.app = app
        self.toggle_inventory_callback = toggle_inventory_callback
        self.use_skill_callback = use_skill_callback
        self.open_shop_callback = open_shop_callback
        self.font = cfg.get_font(max(8,int(40 * cfg.ui_scale())))
        self.stamina_font = pygame.font.Font(None, 24)
        self.stamina_label = self.stamina_font.render(_("STAMINA"), True, (255, 255, 255))
        self._toast_font = cfg.get_font(max(8, int(18 * cfg.ui_scale())))
        self._toast_title_font = cfg.get_font(max(8, int(22 * cfg.ui_scale())))
        self._active_toast = None
        self._toast_timer = 0.0

        try:
            self.hp_icon = pygame.image.load("assets/ui/heart.png")
            ico = max(8,int(50 * cfg.ui_scale()))
            self.hp_icon = pygame.transform.scale(self.hp_icon, (ico, ico))
        except FileNotFoundError:
            ico = max(8,int(50 * cfg.ui_scale()))
            self.hp_icon = pygame.Surface((ico, ico), pygame.SRCALPHA)
            pygame.draw.circle(self.hp_icon, (255, 0, 0), (ico//2, ico//2), ico//2)

        try:
            self.life_icon = pygame.image.load("assets/ui/skull.png")
            ico = max(8,int(50 * cfg.ui_scale()))
            self.life_icon = pygame.transform.scale(self.life_icon, (ico, ico))
        except FileNotFoundError:
            ico = max(8,int(50 * cfg.ui_scale()))
            self.life_icon = pygame.Surface((ico, ico), pygame.SRCALPHA)
            pygame.draw.circle(self.life_icon, (200, 200, 200), (ico//2, ico//2), ico//2)

        scale = cfg.ui_scale()
        button_width = max(1,int(200 * scale))
        button_height = max(1,int(50 * scale))
        button_x = int(200 * scale)
        button_y = int(240 * scale)

        self.inv_button = Button(
            pygame.Rect(button_x, button_y, button_width, button_height),
            _("INVENTORY"),
            (100, 100, 100),
            (150, 150, 150),
            self.font,
            (255, 255, 255),
            max(2,int(10 * cfg.ui_scale())),
            on_click=self.toggle_inventory
        )


        # Skill/ability hotbar on the right (visual only for now)
        self.skill_slot_size = 64
        self.skill_slot_padding = 10
        self.skill_slots_count = 6
        self.skill_panel_margin = 10
        self.skill_panel_width = self.skill_slot_size + self.skill_slot_padding * 2
        self.skill_total_slots_height = (self.skill_slot_size * self.skill_slots_count) + (self.skill_slot_padding * (self.skill_slots_count + 1))
        self.skill_panel_x = 0
        self.skill_panel_y = 0
        self.animation_time = 0.0

        self.hp_icon_pos = (0, 0)
        self.life_icon_pos = (0, 0)
        self.hp_bar_rect = pygame.Rect(0, 0, 0, 0)
        self.xp_bar_rect = pygame.Rect(0, 0, 0, 0)
        self.stamina_bar_rect = pygame.Rect(0, 0, 0, 0)
        self.mana_bar_rect = pygame.Rect(0, 0, 0, 0)
        self._layout_size = None

        # slot rects (populated/updated per-frame or on-event)
        self.skill_slot_rects: list[pygame.Rect] = []

    def _recalc_layout(self, screen_width: int, screen_height: int):
        """Recalculate HUD positions based on the current screen size."""
        left_margin = 20
        top_margin = 20
        right_margin = 20
        bottom_margin = 20
        bar_width = max(220, min(320, screen_width // 4))
        bar_height = max(8,int(30 * cfg.ui_scale()))

        self.hp_icon_pos = (left_margin, top_margin)
        self.hp_bar_rect = pygame.Rect(left_margin + 60, top_margin + 10, bar_width, bar_height)
        self.life_icon_pos = (left_margin, top_margin + 60)

        scale = cfg.ui_scale()
        button_width = max(1,int(200 * scale))
        button_height = max(1,int(50 * scale))
        button_x = left_margin
        button_y = top_margin + int(170 * scale)
        self.inv_button.rect = pygame.Rect(button_x, button_y, button_width, button_height)
        try:
            self.inv_button._update_text_surface()
        except Exception:
            pass
        pass

        xp_bar_width = min(320, max(220, screen_width // 4))
        xp_bar_height = 15
        xp_bar_x = screen_width - right_margin - xp_bar_width
        xp_bar_y = top_margin + 10
        self.xp_bar_rect = pygame.Rect(xp_bar_x, xp_bar_y, xp_bar_width, xp_bar_height)

        self.skill_panel_x = screen_width - self.skill_panel_width - right_margin
        self.skill_panel_y = (screen_height - self.skill_total_slots_height) // 2

        # Stamina bar above the hotbar at the bottom of the screen
        hotbar_scale = cfg.INV_HOTBAR_SCALE * cfg.ui_scale()
        hotbar_slot_size = int(cfg.BASE_INV_slot_size * hotbar_scale)
        hotbar_border = cfg.BASE_INV_border
        hotbar_columns = getattr(cfg, 'INV_HOTBAR_COLUMNS', 10)
        hotbar_total_width = (hotbar_slot_size + hotbar_border) * hotbar_columns + hotbar_border
        hotbar_top = screen_height + cfg.INV_HOTBAR_Y_OFFSET - hotbar_slot_size

        stamina_bar_width = hotbar_total_width
        stamina_bar_height = 12
        stamina_bar_x = (screen_width - stamina_bar_width) // 2
        stamina_bar_y = hotbar_top - stamina_bar_height - 10
        self.stamina_bar_rect = pygame.Rect(stamina_bar_x, stamina_bar_y, stamina_bar_width, stamina_bar_height)

        # Mana bar above stamina bar
        mana_bar_width = hotbar_total_width
        mana_bar_height = 14
        mana_bar_x = (screen_width - mana_bar_width) // 2
        mana_bar_y = stamina_bar_y - mana_bar_height - 6
        self.mana_bar_rect = pygame.Rect(mana_bar_x, mana_bar_y, mana_bar_width, mana_bar_height)

        # rebuild rects
        self.skill_slot_rects = []
        for i in range(self.skill_slots_count):
            sx = self.skill_panel_x + self.skill_slot_padding
            sy = self.skill_panel_y + self.skill_slot_padding + i * (self.skill_slot_size + self.skill_slot_padding)
            self.skill_slot_rects.append(pygame.Rect(sx, sy, self.skill_slot_size, self.skill_slot_size))

        # top skillbar removed from layout

    def _ensure_layout(self, screen_width: int, screen_height: int):
        size = (screen_width, screen_height)
        if self._layout_size != size:
            self._layout_size = size
            self._recalc_layout(screen_width, screen_height)

    def toggle_inventory(self):
        if self.toggle_inventory_callback:
            self.toggle_inventory_callback()
        else:
            self.app.INV_manager.player_inventory_opened = not self.app.INV_manager.player_inventory_opened
        logger.info(f"Inventory toggled: open={self.app.INV_manager.player_inventory_opened}")

    def handle_event(self, event: pygame.event.Event):
        try:
            sw, sh = self.app.screen.get_size()
            self._ensure_layout(sw, sh)
        except Exception:
            self._ensure_layout(cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.inv_button.rect.collidepoint(event.pos):
                if self.inv_button.on_click:
                    self.inv_button.on_click()

            # Only handle skill slot clicks when shop is not open
            if not getattr(self.app.INV_manager, 'current_shop_inv', None):
                for index, slot_rect in enumerate(self.skill_slot_rects):
                    if slot_rect.collidepoint(event.pos):
                        if self.use_skill_callback:
                            logger.info(f"Skill slot used: {index}")
                            self.use_skill_callback(index)
                        break

    def _get_skill_theme(self, skill):
        if skill is None:
            return self.NEON_THEMES["default"]
        skill_id = skill.get("skill_id", "").lower()
        name = skill.get("name", "").lower()
        color = skill.get("color", (100, 140, 200))
        
        for theme_name, theme in self.NEON_THEMES.items():
            if theme_name in skill_id or theme_name in name:
                return theme
        
        best_match = "default"
        best_score = 0
        for theme_name, theme in self.NEON_THEMES.items():
            primary = theme["primary"]
            score = sum(abs(a - b) for a, b in zip(color, primary))
            if score < best_score or best_score == 0:
                best_score = score
                best_match = theme_name
        return self.NEON_THEMES.get(best_match, self.NEON_THEMES["default"])

    def _draw_hud_skill_slot(self, surface, rect, skill, idx):
        t = self.animation_time
        theme = self._get_skill_theme(skill)
        
        # Panel background with glow
        pulse = (math.sin(t * 2.5 + idx * 0.5) + 1.0) * 0.5
        if skill:
            bg_color = skill.get("color", theme["primary"])
            border_color = skill.get("accent", theme["accent"])
            glow_color = theme["glow"]
        else:
            bg_color = cfg.INV_SLOT_BG_COLOR
            border_color = cfg.INV_SLOT_BORDER_COLOR
            glow_color = (40, 40, 50)

        # Glow layers for active skills
        if skill:
            for offset in range(3, 0, -1):
                glow_rect = rect.inflate(offset * 2, offset * 2)
                alpha = int(40 + 30 * pulse) // (offset + 1)
                glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                gc = (*glow_color, alpha)
                pygame.draw.rect(glow_surf, gc, glow_surf.get_rect(), border_radius=14 + offset)
                surface.blit(glow_surf, glow_rect.topleft)

        # Slot background
        pygame.draw.rect(surface, bg_color, rect, border_radius=cfg.INV_SLOT_BORDER_RADIUS)
        
        # Inner shadow for depth
        inner_rect = rect.inflate(-4, -4)
        pygame.draw.rect(surface, cfg.INV_SLOT_INNER_SHADOW, inner_rect, border_radius=cfg.INV_SLOT_INNER_BORDER_RADIUS)

        if skill:
            cooldown_percent = self.character.get_skill_cooldown_percent(skill)

            if cooldown_percent > 0.0:
                center = (rect.width // 2, rect.height // 2)
                radius = max(rect.width, rect.height)
                dark_color = cfg.COOLDOWN_RADIAL_COLOR
                start_angle = -math.pi / 2
                dark_sweep = cooldown_percent * 2 * math.pi

                if dark_sweep >= 2 * math.pi - 0.001:
                    overlay_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
                    pygame.draw.rect(overlay_surf, dark_color, overlay_surf.get_rect(), border_radius=cfg.INV_SLOT_BORDER_RADIUS)
                    surface.blit(overlay_surf, rect.topleft)
                elif dark_sweep > 0.01:
                    overlay_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
                    angle_start = start_angle + (1 - cooldown_percent) * 2 * math.pi
                    points = [center]
                    num_steps = max(6, int(dark_sweep / (2 * math.pi) * 60))
                    for i in range(num_steps + 1):
                        angle = angle_start + dark_sweep * i / num_steps
                        points.append((center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)))
                    pygame.draw.polygon(overlay_surf, dark_color, points)
                    surface.blit(overlay_surf, rect.topleft)

        # Border
        final_border = border_color
        if skill:
            final_border = tuple(min(255, int(c * 1.2)) for c in border_color)
        pygame.draw.rect(surface, final_border, rect, 2, border_radius=cfg.INV_SLOT_BORDER_RADIUS)

        if skill:
            if cooldown_percent > 0.0:
                def _cd_color(p):
                    if p > 0.5:
                        t2 = (p - 0.5) * 2
                        return (255, int(200 - 120 * t2), int(50 + 30 * t2))
                    t2 = p * 2
                    return (int(80 + 175 * t2), int(255 - 55 * t2), int(120 - 70 * t2))

                cd_col = _cd_color(cooldown_percent)
                cd_highlight = tuple(min(255, c + 60) for c in cd_col)

                ring_sweep = (1.0 - cooldown_percent) * 2 * math.pi
                if ring_sweep > 0.02:
                    ring_rect = rect.inflate(-4, -4)
                    pygame.draw.arc(surface, (*cd_col, 200), ring_rect, -math.pi / 2, -math.pi / 2 + ring_sweep, cfg.COOLDOWN_RING_WIDTH)

                bar_height = cfg.COOLDOWN_BAR_HEIGHT
                bar_rect = pygame.Rect(rect.left + 2, rect.bottom - bar_height - 2, rect.width - 4, bar_height)
                pygame.draw.rect(surface, cfg.COOLDOWN_BAR_BG_COLOR, bar_rect, border_radius=3)

                fill_width = int((1.0 - cooldown_percent) * bar_rect.width)
                if fill_width > 0:
                    fill_rect = pygame.Rect(bar_rect.left, bar_rect.top, fill_width, bar_rect.height)
                    pygame.draw.rect(surface, (*cd_col, 220), fill_rect, border_radius=3)
                    highlight_rect = pygame.Rect(bar_rect.left, bar_rect.top, fill_width, max(1, bar_rect.height // 2))
                    pygame.draw.rect(surface, (*cd_highlight, 180), highlight_rect, border_radius=3)

                if cooldown_percent < 0.25:
                    ap = (math.sin(t * 4.0) + 1.0) * 0.5
                    anticipation_rect = rect.inflate(4, 4)
                    anticipation_surf = pygame.Surface(anticipation_rect.size, pygame.SRCALPHA)
                    anticipation_color = (*theme["accent"][:3], int(20 + 35 * ap))
                    pygame.draw.rect(anticipation_surf, anticipation_color, anticipation_surf.get_rect(), border_radius=cfg.INV_SLOT_BORDER_RADIUS + 1, width=1)
                    surface.blit(anticipation_surf, anticipation_rect.topleft)

                skill_id = skill.get("skill_id", "")
                if skill_id == "berserkers_rage":
                    cooldown = self.character.berserkers_rage_cooldown + getattr(self.character, "berserkers_rage_cooldown_bonus", 0)
                elif skill_id == "chrono_shift":
                    cooldown = self.character.chrono_shift_cooldown + getattr(self.character, "chrono_shift_cooldown_bonus", 0)
                else:
                    cooldown = getattr(self.character, f"{skill_id}_cooldown", 0)
                cooldown_time = cooldown / 1000.0

                remaining_time = cooldown_time * cooldown_percent
                if remaining_time > 0.0:
                    cooldown_font = cfg.get_font(max(8, int(cfg.COOLDOWN_TEXT_SIZE * cfg.ui_scale())))
                    time_text = f"{remaining_time:.1f}s"
                    time_surf = cooldown_font.render(time_text, True, cfg.COOLDOWN_TEXT_COLOR)

                    text_padding = int(4 * cfg.ui_scale())
                    text_bg_rect = time_surf.get_rect().inflate(text_padding * 2, text_padding)
                    y_offset = int(10 * cfg.ui_scale())
                    text_bg_rect.center = (rect.centerx, rect.centery + y_offset)
                    bg_surf = pygame.Surface(text_bg_rect.size, pygame.SRCALPHA)
                    pygame.draw.rect(bg_surf, cfg.COOLDOWN_TEXT_BG_COLOR, bg_surf.get_rect(), border_radius=cfg.COOLDOWN_TEXT_BORDER_RADIUS)
                    surface.blit(bg_surf, text_bg_rect.topleft)

                    if cooldown_percent < 0.3:
                        time_surf.set_alpha(int(200 + 55 * (math.sin(t * 6.0) + 1.0) * 0.5))

                    time_rect = time_surf.get_rect(center=(rect.centerx, rect.centery + y_offset))
                    surface.blit(time_surf, time_rect)
            else:
                ready_pulse = (math.sin(t * 3.0) + 1.0) * 0.5
                glow_alpha = int(40 + 50 * ready_pulse)
                ready_glow_color = (*theme["accent"][:3], glow_alpha)

                glow_rect = rect.inflate(6, 6)
                glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, ready_glow_color, glow_surf.get_rect(), border_radius=cfg.INV_SLOT_BORDER_RADIUS + 2, width=2)
                surface.blit(glow_surf, glow_rect.topleft)

                ready_alpha = int(60 + 60 * ready_pulse)
                ready_surf = pygame.Surface((rect.width - 4, cfg.COOLDOWN_BAR_HEIGHT), pygame.SRCALPHA)
                ready_color = (*cfg.COOLDOWN_BAR_READY_COLOR[:3], ready_alpha)
                pygame.draw.rect(ready_surf, ready_color, ready_surf.get_rect(), border_radius=3)
                surface.blit(ready_surf, (rect.left + 2, rect.bottom - cfg.COOLDOWN_BAR_HEIGHT - 2))

            small_font = cfg.get_font(max(8, int(16 * cfg.ui_scale())))
            name = small_font.render(skill.get("name", ""), True, cfg.INV_ITEM_TEXT_COLOR)
            surface.blit(name, name.get_rect(center=(rect.centerx, rect.centery - 4)))

            ident = small_font.render(str(idx + 1), True, cfg.INV_ITEM_TEXT_COLOR)
            surface.blit(ident, ident.get_rect(bottomright=(rect.right - 6, rect.bottom - 6)))

    def _on_shop_clicked(self):
        if self.open_shop_callback:
            try:
                self.open_shop_callback()
            except Exception:
                pass
        else:
            # fallback: try to open shop via gameplay state
            try:
                game_state = getattr(self.app.manager, 'states', {}).get('gameplay')
                if game_state and hasattr(game_state, 'open_shop'):
                    game_state.open_shop()
            except Exception:
                pass

    # ─── Effect Bar helpers ───────────────────────────────────────────────
    # Map effect class -> config key used in EFFECT_BAR_* dicts
    _EFFECT_CLASS_TO_KEY = {}

    @classmethod
    def _build_effect_key_map(cls):
        """Build mapping from effect class to lowercase key (called once)."""
        if cls._EFFECT_CLASS_TO_KEY:
            return
        # Use the reverse of Effect_list (name -> class) to build class -> name
        for name, klass in Effect_list.items():
            cls._EFFECT_CLASS_TO_KEY[klass] = name

    def _get_effect_key(self, effect) -> str:
        """Return the config key string for an effect instance."""
        self._build_effect_key_map()
        key = self._EFFECT_CLASS_TO_KEY.get(type(effect))
        if key:
            return key
        # Fallback: lowercase class name without 'Effect' suffix
        cls_name = type(effect).__name__
        if cls_name.endswith("Effect"):
            cls_name = cls_name[:-6]
        return cls_name.lower()

    def _get_effect_remaining(self, effect) -> float:
        """Return remaining seconds for the effect."""
        return max(0.0, effect.duration - effect.timer)

    def _get_effect_total(self, effect) -> float:
        """Return total duration of the effect."""
        return max(0.001, effect.duration)

    def _draw_effect_icon(self, surface, cx, cy, radius, key, tint):
        """Draw a polished, unique icon for each effect type at (cx, cy)."""
        import math as _m
        r = radius
        highlight = tuple(min(255, c + 70) for c in tint)
        shadow = tuple(max(0, c - 60) for c in tint)
        bright = tuple(min(255, c + 120) for c in tint)

        # Helper: draw a smooth outlined polygon
        def _filled(poly, col, outline_col=None, width=1):
            pygame.draw.polygon(surface, col, poly)
            if outline_col:
                pygame.draw.polygon(surface, outline_col, poly, width)

        # Helper: draw a small 4-point star
        def _star4(sx, sy, outer_r, inner_r, col):
            pts = []
            for i in range(8):
                a = i * _m.pi / 4 - _m.pi / 2
                rd = outer_r if i % 2 == 0 else inner_r
                pts.append((sx + int(_m.cos(a) * rd), sy + int(_m.sin(a) * rd)))
            if len(pts) >= 3:
                pygame.draw.polygon(surface, col, pts)

        # Helper: smooth almond / eye shape
        def _eye_shape(ex, cy2, ew, eh, col, outline=None, lw=1):
            pts = []
            for i in range(24):
                a = i * _m.pi * 2 / 24
                factor = 1.0 - abs(_m.cos(a)) * 0.6
                px = ex + int(_m.cos(a) * ew)
                py = cy2 + int(_m.sin(a) * eh * factor)
                pts.append((px, py))
            if len(pts) >= 3:
                _filled(pts, col, outline, lw)
            return pts

        # Small ambient glow behind icon
        glow_r = int(r * 0.55)
        glow_surf = pygame.Surface((glow_r * 4, glow_r * 4), pygame.SRCALPHA)
        for gr in range(glow_r, 0, -3):
            alpha = int(25 * (1 - gr / glow_r))
            if alpha > 0:
                pygame.draw.circle(glow_surf, (*tint, alpha), (glow_r * 2, glow_r * 2), gr)
        surface.blit(glow_surf, (cx - glow_r * 2, cy - glow_r * 2), special_flags=pygame.BLEND_RGBA_ADD)

        lw_main = max(1, int(r * 0.07))
        lw_thin = max(1, int(r * 0.05))
        lw_bold = max(2, int(r * 0.10))

        if key == "regeneration":
            # Polished heart with outline
            hr = max(3, r * 0.38)
            ox = int(hr * 0.38)
            oy = int(r * 0.12)
            pygame.draw.circle(surface, highlight, (cx - ox, cy - oy), int(hr) + 1)
            pygame.draw.circle(surface, highlight, (cx + ox, cy - oy), int(hr) + 1)
            pygame.draw.circle(surface, tint, (cx - ox, cy - oy), int(hr))
            pygame.draw.circle(surface, tint, (cx + ox, cy - oy), int(hr))
            bot_pts = [
                (cx - int(hr * 1.15), cy - oy + int(hr * 0.2)),
                (cx + int(hr * 1.15), cy - oy + int(hr * 0.2)),
                (cx, cy + int(hr * 1.1)),
            ]
            _filled(bot_pts, tint, shadow, lw_thin)
            # Small white highlight
            pygame.draw.circle(surface, bright, (cx - ox - max(1, int(hr * 0.2)), cy - oy - max(1, int(hr * 0.25))), max(1, int(hr * 0.18)))

        elif key == "poison":
            # Rounded skull with jaw and dark eyes
            sk_r = int(r * 0.42)
            pygame.draw.circle(surface, shadow, (cx, cy - int(r * 0.12) + 1), sk_r + 1)
            pygame.draw.circle(surface, tint, (cx, cy - int(r * 0.12)), sk_r)
            # Jaw (rounded rect)
            jaw = pygame.Rect(cx - int(r * 0.28), cy + int(r * 0.15), int(r * 0.56), int(r * 0.22))
            pygame.draw.rect(surface, tint, jaw, border_radius=int(r * 0.06))
            pygame.draw.rect(surface, shadow, jaw, lw_thin, border_radius=int(r * 0.06))
            # Eyes
            er = max(2, int(r * 0.11))
            eye_y = cy - int(r * 0.18)
            pygame.draw.circle(surface, shadow, (cx - int(r * 0.14), eye_y), er + 1)
            pygame.draw.circle(surface, (10, 10, 15), (cx - int(r * 0.14), eye_y), er)
            pygame.draw.circle(surface, shadow, (cx + int(r * 0.14), eye_y), er + 1)
            pygame.draw.circle(surface, (10, 10, 15), (cx + int(r * 0.14), eye_y), er)
            # Nose
            pygame.draw.circle(surface, shadow, (cx, cy - int(r * 0.03)), max(1, int(r * 0.04)))

        elif key == "burn":
            # Smooth flame with glow
            fh = int(r * 0.55)
            # Outer (darker)
            outer_pts = [
                (cx, cy - fh),
                (cx - int(r * 0.15), cy - int(r * 0.25)),
                (cx - int(r * 0.4), cy + int(r * 0.35)),
                (cx - int(r * 0.1), cy + int(r * 0.42)),
                (cx + int(r * 0.1), cy + int(r * 0.42)),
                (cx + int(r * 0.4), cy + int(r * 0.35)),
                (cx + int(r * 0.15), cy - int(r * 0.25)),
            ]
            _filled(outer_pts, tint, shadow, lw_thin)
            # Mid flame
            mid_pts = [
                (cx, cy - int(r * 0.45)),
                (cx - int(r * 0.22), cy + int(r * 0.25)),
                (cx, cy + int(r * 0.35)),
                (cx + int(r * 0.22), cy + int(r * 0.25)),
            ]
            _filled(mid_pts, highlight, None)
            # Bright core
            core_pts = [
                (cx, cy - int(r * 0.2)),
                (cx - int(r * 0.08), cy + int(r * 0.3)),
                (cx + int(r * 0.08), cy + int(r * 0.3)),
            ]
            _filled(core_pts, bright, None)

        elif key == "confusion":
            # Smooth spiral with dot
            spiral_pts = []
            for i in range(40):
                t2 = i / 40.0
                angle = t2 * _m.pi * 3.5
                dist = r * (0.08 + t2 * 0.38)
                px = cx + int(_m.cos(angle) * dist)
                py = cy - int(r * 0.05) + int(_m.sin(angle) * dist)
                spiral_pts.append((px, py))
            if len(spiral_pts) > 1:
                # Glow
                pygame.draw.lines(surface, shadow, False, spiral_pts, lw_bold)
                pygame.draw.lines(surface, tint, False, spiral_pts, lw_main)
            # Dot
            pygame.draw.circle(surface, shadow, (cx, cy + int(r * 0.38)), max(2, int(r * 0.08)) + 1)
            pygame.draw.circle(surface, tint, (cx, cy + int(r * 0.38)), max(2, int(r * 0.08)))

        elif key == "dizziness":
            # 5 orbiting 4-point stars
            for i in range(5):
                ang = i * _m.pi * 2 / 5 - _m.pi / 2
                sx = cx + int(_m.cos(ang) * r * 0.38)
                sy = cy + int(_m.sin(ang) * r * 0.38)
                sr = max(2, int(r * 0.14))
                _star4(sx, sy, sr, sr // 2 + 1, shadow)
                _star4(sx, sy, sr - 1, sr // 2, highlight)

        elif key == "slow":
            # Hourglass with rounded bars
            hw = int(r * 0.42)
            hh = int(r * 0.6)
            bar_w = max(2, int(r * 0.08))
            # Top triangle
            pts_t = [(cx - hw, cy - hh), (cx + hw, cy - hh), (cx, cy - int(r * 0.05))]
            _filled(pts_t, tint, shadow, lw_thin)
            # Bottom triangle
            pts_b = [(cx - hw, cy + hh), (cx + hw, cy + hh), (cx, cy + int(r * 0.05))]
            _filled(pts_b, tint, shadow, lw_thin)
            # Bars
            pygame.draw.line(surface, highlight, (cx - hw, cy - hh), (cx + hw, cy - hh), bar_w)
            pygame.draw.line(surface, highlight, (cx - hw, cy + hh), (cx + hw, cy + hh), bar_w)
            # Sand dots
            for dx in [-int(r * 0.1), 0, int(r * 0.1)]:
                pygame.draw.circle(surface, bright, (cx + dx, cy + int(r * 0.2)), max(1, int(r * 0.03)))

        elif key == "freeze":
            # 6-armed snowflake with branching
            for i in range(6):
                ang = i * _m.pi / 6
                dx = int(_m.cos(ang) * r * 0.55)
                dy = int(_m.sin(ang) * r * 0.55)
                # Main arm (shadow then highlight)
                pygame.draw.line(surface, shadow, (cx - dx, cy - dy), (cx + dx, cy + dy), lw_bold)
                pygame.draw.line(surface, tint, (cx - dx, cy - dy), (cx + dx, cy + dy), lw_main)
                # Branches at 60%
                bx = cx + int(dx * 0.6)
                by = cy + int(dy * 0.6)
                b_len = int(r * 0.2)
                for side in [-1, 1]:
                    ba = ang + side * _m.pi / 5
                    ex = bx + int(_m.cos(ba) * b_len)
                    ey = by + int(_m.sin(ba) * b_len)
                    pygame.draw.line(surface, tint, (bx, by), (ex, ey), lw_thin)
            # Center dot
            pygame.draw.circle(surface, highlight, (cx, cy), max(2, int(r * 0.07)))

        elif key == "root":
            # Organic tree with curved branches
            lw_t = lw_bold
            # Trunk
            pygame.draw.line(surface, shadow, (cx + 1, cy + int(r * 0.52)), (cx + 1, cy - int(r * 0.08)), lw_t)
            pygame.draw.line(surface, tint, (cx, cy + int(r * 0.5)), (cx, cy - int(r * 0.1)), lw_t)
            # Branches (two layers)
            for dy_off, spread, arm_lw in [(-int(r * 0.1), 0.38, lw_main), (-int(r * 0.28), 0.28, lw_thin)]:
                for side in [-1, 1]:
                    bx = cx + side * int(r * spread)
                    by = cy + dy_off - int(r * 0.28)
                    pygame.draw.line(surface, tint, (cx, cy + dy_off), (bx, by), arm_lw)
            # Leaf blobs
            leaf_r = max(2, int(r * 0.1))
            for dx, dy in [(-int(r * 0.35), -int(r * 0.38)), (int(r * 0.35), -int(r * 0.38)), (0, -int(r * 0.42))]:
                pygame.draw.circle(surface, highlight, (cx + dx, cy + dy), leaf_r)
                pygame.draw.circle(surface, tint, (cx + dx, cy + dy), leaf_r - 1)
            # Roots
            for side in [-1, 1]:
                rx = cx + side * int(r * 0.22)
                ry = cy + int(r * 0.6)
                pygame.draw.line(surface, tint, (cx, cy + int(r * 0.4)), (rx, ry), lw_thin)

        elif key == "radiant_fortitude":
            # Glowing sun with rays
            sun_cy = cy - int(r * 0.05)
            sun_r = int(r * 0.3)
            # Outer glow ring
            pygame.draw.circle(surface, shadow, (cx, sun_cy), sun_r + 3)
            pygame.draw.circle(surface, tint, (cx, sun_cy), sun_r)
            pygame.draw.circle(surface, highlight, (cx, sun_cy), max(2, int(sun_r * 0.5)))
            # 8 rays with alternating lengths
            for i in range(8):
                a = i * _m.pi / 4
                inner = sun_r + 3
                outer = sun_r + int(r * (0.22 if i % 2 == 0 else 0.15))
                rx1 = cx + int(_m.cos(a) * inner)
                ry1 = sun_cy + int(_m.sin(a) * inner)
                rx2 = cx + int(_m.cos(a) * outer)
                ry2 = sun_cy + int(_m.sin(a) * outer)
                pygame.draw.line(surface, tint, (rx1, ry1), (rx2, ry2), max(1, int(r * 0.05)))
            # Bright center
            pygame.draw.circle(surface, bright, (cx, sun_cy), max(1, int(sun_r * 0.25)))

        elif key == "vampiric_edge":
            # Two polished fangs with a gum line
            gum_y = cy - int(r * 0.22)
            fw = int(r * 0.14)
            fh = int(r * 0.45)
            for side in [-1, 1]:
                base_x = cx + side * int(r * 0.22)
                # Gum line
                pygame.draw.line(surface, shadow, (base_x - fw, gum_y), (base_x + fw, gum_y), lw_thin)
                # Fang triangle
                fang_pts = [
                    (base_x - fw, gum_y),
                    (base_x + fw, gum_y),
                    (base_x, cy + fh),
                ]
                _filled(fang_pts, highlight, shadow, lw_thin)
                # Bright tip
                pygame.draw.circle(surface, bright, (base_x, cy + fh - max(1, int(r * 0.06))), max(1, int(r * 0.04)))
            # Connecting gum
            pygame.draw.line(surface, tint, (cx - int(r * 0.36), gum_y), (cx + int(r * 0.36), gum_y), lw_thin)

        elif key == "keen_insight":
            # Polished eye with iris and highlight
            _eye_shape(cx, cy, int(r * 0.65), int(r * 0.32), tint, shadow, lw_thin)
            # Iris
            ir_r = max(3, int(r * 0.22))
            pygame.draw.circle(surface, shadow, (cx, cy), ir_r + 1)
            pygame.draw.circle(surface, tint, (cx, cy), ir_r)
            # Pupil
            pr = max(2, int(r * 0.12))
            pygame.draw.circle(surface, (10, 10, 15), (cx, cy), pr)
            # Catchlight
            pygame.draw.circle(surface, (255, 255, 255), (cx - max(1, int(r * 0.08)), cy - max(1, int(r * 0.08))), max(1, int(r * 0.06)))

        elif key == "bleed":
            # Smooth teardrop
            drop_pts = []
            for i in range(28):
                a = i * _m.pi * 2 / 28
                s_val = _m.sin(a)
                if s_val < 0:
                    factor = 1.0 + s_val * 0.6
                else:
                    factor = 1.0
                dx = int(_m.cos(a) * r * 0.32 * factor)
                dy = int(_m.sin(a) * r * 0.42)
                drop_pts.append((cx + dx, cy + dy - int(r * 0.05)))
            if len(drop_pts) >= 3:
                _filled(drop_pts, tint, shadow, lw_thin)
                # Bright highlight on left
                pygame.draw.circle(surface, highlight, (cx - int(r * 0.1), cy - int(r * 0.12)), max(1, int(r * 0.06)))

        elif key == "strength":
            # Bold upward arrow with outline
            shaft_w = lw_bold
            # Shaft
            pygame.draw.line(surface, shadow, (cx + 1, cy + int(r * 0.45)), (cx + 1, cy - int(r * 0.15)), shaft_w + 1)
            pygame.draw.line(surface, tint, (cx, cy + int(r * 0.45)), (cx, cy - int(r * 0.15)), shaft_w)
            # Arrowhead
            head_pts = [
                (cx, cy - int(r * 0.58)),
                (cx - int(r * 0.32), cy - int(r * 0.12)),
                (cx + int(r * 0.32), cy - int(r * 0.12)),
            ]
            _filled(head_pts, tint, shadow, lw_thin)
            # Bright tip
            pygame.draw.circle(surface, highlight, (cx, cy - int(r * 0.48)), max(1, int(r * 0.05)))

        elif key == "momentum":
            # Stylized lightning bolt
            pts = [
                (cx - int(r * 0.02), cy - int(r * 0.52)),
                (cx - int(r * 0.22), cy - int(r * 0.02)),
                (cx - int(r * 0.02), cy - int(r * 0.02)),
                (cx - int(r * 0.12), cy + int(r * 0.52)),
                (cx + int(r * 0.18), cy + int(r * 0.0)),
                (cx - int(r * 0.0), cy + int(r * 0.0)),
            ]
            # Outline then fill
            pygame.draw.polygon(surface, shadow, [(x + 1, y + 1) for x, y in pts])
            _filled(pts, highlight, shadow, lw_thin)
            # Bright center line
            bright_pts = [
                (cx - int(r * 0.02), cy - int(r * 0.35)),
                (cx - int(r * 0.12), cy - int(r * 0.05)),
                (cx + int(r * 0.02), cy + int(r * 0.05)),
                (cx - int(r * 0.06), cy + int(r * 0.35)),
            ]
            if len(bright_pts) > 1:
                pygame.draw.lines(surface, bright, False, bright_pts, lw_thin)

        elif key == "blind":
            # Eye with slash through it
            _eye_shape(cx, cy, int(r * 0.52), int(r * 0.28), tint, shadow, lw_thin)
            # Pupil
            pygame.draw.circle(surface, shadow, (cx, cy), max(2, int(r * 0.1)))
            pygame.draw.circle(surface, (10, 10, 15), (cx, cy), max(1, int(r * 0.07)))
            # Slash
            pygame.draw.line(surface, shadow, (cx - int(r * 0.52), cy + int(r * 0.42)),
                             (cx + int(r * 0.52), cy - int(r * 0.42)), lw_bold)

        elif key == "haste":
            # Wing with feathers + speed lines
            lw_h = lw_main
            # Wing base
            base = (cx + int(r * 0.05), cy + int(r * 0.15))
            feathers = [(-0.42, -0.08), (-0.28, -0.32), (-0.10, -0.48)]
            for i, (dx, dy) in enumerate(feathers):
                ex = cx + int(dx * r * 2)
                ey = cy + int(dy * r * 2)
                # Each feather is a thin filled triangle
                mid_x = (base[0] + ex) // 2
                mid_y = (base[1] + ey) // 2
                side = 1 if i % 2 == 0 else -1
                f_pts = [
                    base,
                    (ex, ey),
                    (mid_x + side * int(r * 0.08), mid_y + side * int(r * 0.08)),
                ]
                pygame.draw.polygon(surface, shadow, f_pts)
                pygame.draw.polygon(surface, tint, f_pts, lw_thin)
            # Speed lines
            for j, dy_off in enumerate([-int(r * 0.22), 0, int(r * 0.22)]):
                sx = cx + int(r * 0.18)
                line_len = int(r * (0.38 - j * 0.05))
                pygame.draw.line(surface, tint, (sx, cy + dy_off), (sx + line_len, cy + dy_off), lw_thin)

        elif key == "weaken":
            # Cracked shield outline
            shield_pts = [
                (cx, cy + int(r * 0.48)),
                (cx - int(r * 0.42), cy - int(r * 0.08)),
                (cx - int(r * 0.3), cy - int(r * 0.45)),
                (cx + int(r * 0.3), cy - int(r * 0.45)),
                (cx + int(r * 0.42), cy - int(r * 0.08)),
            ]
            pygame.draw.polygon(surface, tint, shield_pts, lw_bold)
            # Zigzag crack
            crack_pts = [
                (cx, cy - int(r * 0.35)),
                (cx + int(r * 0.08), cy - int(r * 0.15)),
                (cx - int(r * 0.05), cy + int(r * 0.1)),
                (cx + int(r * 0.05), cy + int(r * 0.25)),
                (cx - int(r * 0.03), cy + int(r * 0.38)),
            ]
            pygame.draw.lines(surface, shadow, False, crack_pts, lw_main)

        elif key == "curse":
            # Demonic skull with horns
            sk_r = int(r * 0.38)
            head_cy = cy + int(r * 0.05)
            pygame.draw.circle(surface, shadow, (cx, head_cy + 1), sk_r + 1)
            pygame.draw.circle(surface, tint, (cx, head_cy), sk_r)
            # Jaw
            jaw = pygame.Rect(cx - int(r * 0.22), cy + int(r * 0.22), int(r * 0.44), int(r * 0.18))
            pygame.draw.rect(surface, tint, jaw, border_radius=int(r * 0.05))
            pygame.draw.rect(surface, shadow, jaw, lw_thin, border_radius=int(r * 0.05))
            # Eyes (glowing)
            er = max(2, int(r * 0.09))
            eye_y2 = cy - int(r * 0.02)
            pygame.draw.circle(surface, bright, (cx - int(r * 0.13), eye_y2), er + 1)
            pygame.draw.circle(surface, (255, 220, 60), (cx - int(r * 0.13), eye_y2), er)
            pygame.draw.circle(surface, bright, (cx + int(r * 0.13), eye_y2), er + 1)
            pygame.draw.circle(surface, (255, 220, 60), (cx + int(r * 0.13), eye_y2), er)
            # Horns (curved via two line segments)
            for side in [-1, 1]:
                hx1 = cx + side * int(r * 0.28)
                hy1 = cy - int(r * 0.25)
                hx2 = cx + side * int(r * 0.4)
                hy2 = cy - int(r * 0.45)
                hx3 = cx + side * int(r * 0.48)
                hy3 = cy - int(r * 0.52)
                pygame.draw.line(surface, tint, (hx1, hy1), (hx2, hy2), lw_bold)
                pygame.draw.line(surface, highlight, (hx2, hy2), (hx3, hy3), lw_main)

        elif key == "lethargy":
            # Weight with handle
            lw_l = lw_bold
            # Handle (arc)
            arc_rect = pygame.Rect(cx - int(r * 0.14), cy - int(r * 0.45), int(r * 0.28), int(r * 0.2))
            pygame.draw.arc(surface, tint, arc_rect, _m.pi, _m.pi * 2, lw_l)
            # Rope
            pygame.draw.line(surface, tint, (cx, cy - int(r * 0.35)), (cx, cy - int(r * 0.05)), lw_main)
            # Weight body (rounded trapezoid)
            w_pts = [
                (cx - int(r * 0.12), cy - int(r * 0.05)),
                (cx + int(r * 0.12), cy - int(r * 0.05)),
                (cx + int(r * 0.32), cy + int(r * 0.32)),
                (cx - int(r * 0.32), cy + int(r * 0.32)),
            ]
            _filled(w_pts, tint, shadow, lw_thin)
            # Highlight on body
            hl_pts = [
                (cx - int(r * 0.08), cy + int(r * 0.02)),
                (cx + int(r * 0.08), cy + int(r * 0.02)),
                (cx + int(r * 0.18), cy + int(r * 0.22)),
                (cx - int(r * 0.18), cy + int(r * 0.22)),
            ]
            pygame.draw.polygon(surface, highlight, hl_pts)

        elif key == "shield":
            # Full filled shield with cross
            shield_pts = [
                (cx, cy + int(r * 0.52)),
                (cx - int(r * 0.42), cy - int(r * 0.08)),
                (cx - int(r * 0.32), cy - int(r * 0.48)),
                (cx, cy - int(r * 0.58)),
                (cx + int(r * 0.32), cy - int(r * 0.48)),
                (cx + int(r * 0.42), cy - int(r * 0.08)),
            ]
            # Shadow outline
            pygame.draw.polygon(surface, shadow, [(x + 1, y + 1) for x, y in shield_pts])
            _filled(shield_pts, tint, shadow, lw_thin)
            # Inner highlight half
            inner_hl = [
                (cx, cy + int(r * 0.35)),
                (cx - int(r * 0.22), cy - int(r * 0.02)),
                (cx, cy - int(r * 0.38)),
            ]
            pygame.draw.polygon(surface, highlight, inner_hl)
            # Center cross
            cr_w = max(1, int(r * 0.06))
            pygame.draw.line(surface, bright, (cx, cy - int(r * 0.25)), (cx, cy + int(r * 0.25)), cr_w)
            pygame.draw.line(surface, bright, (cx - int(r * 0.15), cy - int(r * 0.05)), (cx + int(r * 0.15), cy - int(r * 0.05)), cr_w)

        else:
            # Default: polished diamond
            pts = [
                (cx, cy - int(r * 0.52)),
                (cx + int(r * 0.42), cy),
                (cx, cy + int(r * 0.52)),
                (cx - int(r * 0.42), cy),
            ]
            _filled(pts, tint, shadow, lw_thin)

    def _draw_effect_bar(self, screen: pygame.Surface):
        """Draw the active-effect bar below the HP bar (left side)."""
        effects = getattr(self.character, "effects", [])
        if not effects:
            return

        scale = cfg.ui_scale()
        slot_size = max(12, int(cfg.EFFECT_BAR_SLOT_SIZE * scale))
        padding = max(2, int(cfg.EFFECT_BAR_PADDING * scale))
        gap = max(1, int(cfg.EFFECT_BAR_GAP * scale))
        max_per_row = cfg.EFFECT_BAR_MAX_VISIBLE

        # Position: bottom-left corner, above the hotbar
        try:
            sw, sh = screen.get_size()
        except Exception:
            sw, sh = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT

        hotbar_scale = cfg.INV_HOTBAR_SCALE * cfg.ui_scale()
        hotbar_slot_size = int(cfg.BASE_INV_slot_size * hotbar_scale)
        hotbar_border = cfg.BASE_INV_border
        hotbar_columns = getattr(cfg, 'INV_HOTBAR_COLUMNS', 10)
        hotbar_total_width = (hotbar_slot_size + hotbar_border) * hotbar_columns + hotbar_border
        hotbar_top = sh + cfg.INV_HOTBAR_Y_OFFSET - hotbar_slot_size

        bar_x = 20  # left margin
        bar_y = hotbar_top - gap  # stack upward from above hotbar

        # Font for effect labels and timers (scales with slot size)
        label_size = max(8, int(slot_size * 0.28))
        label_font = cfg.get_font(label_size)

        mouse_pos = pygame.mouse.get_pos()
        hovered_effect = None

        cols = min(len(effects), max_per_row)
        total_w = cols * slot_size + (cols - 1) * padding
        rows = (len(effects) + max_per_row - 1) // max_per_row
        total_h = rows * slot_size + (rows - 1) * gap

        # Draw a subtle background panel behind the effect icons
        panel_rect = pygame.Rect(
            bar_x - padding,
            bar_y - padding,
            total_w + padding * 2,
            total_h + padding * 2,
        )
        panel_bg = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            panel_bg,
            cfg.EFFECT_BAR_BG_COLOR,
            panel_bg.get_rect(),
            border_radius=cfg.EFFECT_BAR_BORDER_RADIUS,
        )
        screen.blit(panel_bg, panel_rect.topleft)
        pygame.draw.rect(
            screen,
            cfg.EFFECT_BAR_BORDER_COLOR[:3],
            panel_rect,
            1,
            border_radius=cfg.EFFECT_BAR_BORDER_RADIUS,
        )

        for idx, effect in enumerate(effects):
            row = idx // max_per_row
            col = idx % max_per_row
            sx = bar_x + col * (slot_size + padding)
            sy = bar_y + row * (slot_size + padding)
            slot_rect = pygame.Rect(sx, sy, slot_size, slot_size)

            key = self._get_effect_key(effect)
            is_buff = key in cfg.EFFECT_BAR_BUFF_TYPES
            is_debuff = key in cfg.EFFECT_BAR_DEBUFF_TYPES

            # Base tint colour
            tint = cfg.EFFECT_BAR_COLORS.get(key, (120, 120, 140))

            # ── Slot background ──────────────────────────────────────
            slot_bg = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
            # Dark semi-transparent background
            pygame.draw.rect(
                slot_bg,
                (10, 12, 18, 200),
                slot_bg.get_rect(),
                border_radius=cfg.EFFECT_BAR_BORDER_RADIUS,
            )
            screen.blit(slot_bg, slot_rect.topleft)

            # Subtle coloured border (buff=green, debuff=red, else grey)
            if is_buff:
                border_col = cfg.EFFECT_BAR_BUFF_COLOR
            elif is_debuff:
                border_col = cfg.EFFECT_BAR_DEBUFF_COLOR
            else:
                border_col = cfg.EFFECT_BAR_BORDER_COLOR[:3]
            pygame.draw.rect(
                screen,
                border_col,
                slot_rect,
                1,
                border_radius=cfg.EFFECT_BAR_BORDER_RADIUS,
            )

            # ── Unique icon for each effect ────────────────────────
            icon_r = max(3, slot_size // 3)
            icon_cx = slot_rect.centerx
            icon_cy = slot_rect.centery - max(2, int(4 * scale))
            self._draw_effect_icon(screen, icon_cx, icon_cy, icon_r, key, tint)

            # ── Timer bar at the bottom of the slot ─────────────────
            remaining = self._get_effect_remaining(effect)
            total = self._get_effect_total(effect)
            pct = max(0.0, min(1.0, remaining / total))

            timer_h = max(2, int(slot_size * 0.15))
            timer_rect = pygame.Rect(
                slot_rect.left + 2,
                slot_rect.bottom - timer_h - 2,
                slot_rect.width - 4,
                timer_h,
            )
            # Background
            pygame.draw.rect(screen, (30, 30, 35), timer_rect, border_radius=1)
            # Fill
            fill_w = int(timer_rect.width * pct)
            if fill_w > 0:
                fill_r = pygame.Rect(timer_rect.left, timer_rect.top, fill_w, timer_rect.height)
                pygame.draw.rect(screen, tint, fill_r, border_radius=1)

            # ── Remaining time text below the timer bar ─────────────
            time_text = f"{remaining:.1f}s"
            time_surf = label_font.render(time_text, True, (200, 200, 210))
            # Only draw if there's room below the timer bar
            time_y = slot_rect.bottom + 1
            if time_y + time_surf.get_height() < screen.get_height():
                screen.blit(
                    time_surf,
                    time_surf.get_rect(centerx=slot_rect.centerx, top=time_y),
                )

            # ── Hover detection for tooltip ─────────────────────────
            if slot_rect.collidepoint(mouse_pos):
                hovered_effect = (effect, key, slot_rect)

        # ── Draw tooltip for hovered effect ──────────────────────────
        if hovered_effect:
            effect, key, slot_rect = hovered_effect
            remaining = self._get_effect_remaining(effect)
            total = self._get_effect_total(effect)
            is_buff = key in cfg.EFFECT_BAR_BUFF_TYPES

            # Build tooltip lines
            display_name = cfg.EFFECT_BAR_LABELS.get(key, key.replace("_", " ").title())
            # Try to get a prettier name from the class
            cls_name = type(effect).__name__
            if cls_name.endswith("Effect"):
                cls_name = cls_name[:-6]
            # Insert spaces before capitals for CamelCase
            pretty_name = ""
            for i, ch in enumerate(cls_name):
                if i > 0 and ch.isupper():
                    pretty_name += " "
                pretty_name += ch

            lines = [
                pretty_name,
                f"Remaining: {remaining:.1f}s / {total:.1f}s",
            ]
            # Add extra info if available
            if hasattr(effect, "damage_per_sec"):
                lines.append(f"Damage: {effect.damage_per_sec:.1f}/s")
            if hasattr(effect, "amount_per_sec"):
                lines.append(f"Heal: {effect.amount_per_sec:.1f}/s")
            if hasattr(effect, "speed_multiplier") and effect.speed_multiplier != 1.0:
                lines.append(f"Speed: ×{effect.speed_multiplier:.2f}")
            if hasattr(effect, "heal_mult"):
                lines.append(f"Heal mult: ×{effect.heal_mult:.2f}")
            if hasattr(effect, "damage_mult"):
                lines.append(f"Damage mult: ×{effect.damage_mult:.2f}")
            if hasattr(effect, "absorb_amount"):
                lines.append(f"Shield: {effect.remaining:.0f}/{effect.absorb_amount:.0f}")
            if hasattr(effect, "crit_bonus"):
                lines.append(f"Crit: +{effect.crit_bonus*100:.0f}%")
            if hasattr(effect, "vampiric_pct"):
                lines.append(f"Lifesteal: {effect.vampiric_pct*100:.0f}%")
            if hasattr(effect, "damage_bonus"):
                lines.append(f"Damage: +{effect.damage_bonus}")
            if hasattr(effect, "damage_pct"):
                lines.append(f"Damage: +{effect.damage_pct*100:.0f}%")

            tip_font = cfg.get_font(max(8, int(12 * scale)))
            line_surfs = [tip_font.render(l, True, (240, 240, 245)) for l in lines]
            max_w = max(s.get_width() for s in line_surfs) if line_surfs else 100
            line_h = tip_font.get_linesize()
            tip_pad = max(3, int(6 * scale))
            tip_w = max_w + tip_pad * 2
            tip_h = len(line_surfs) * line_h + tip_pad * 2

            # Position tooltip to the right of the slot, or left if near edge
            tip_x = slot_rect.right + 6
            tip_y = slot_rect.top
            sw, sh = screen.get_size()
            if tip_x + tip_w > sw:
                tip_x = slot_rect.left - tip_w - 6
            if tip_y + tip_h > sh:
                tip_y = sh - tip_h
            if tip_y < 0:
                tip_y = 0

            tip_rect = pygame.Rect(tip_x, tip_y, tip_w, tip_h)
            tip_bg = pygame.Surface(tip_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(
                tip_bg,
                (15, 18, 25, 230),
                tip_bg.get_rect(),
                border_radius=6,
            )
            screen.blit(tip_bg, tip_rect.topleft)
            border_col = cfg.EFFECT_BAR_BUFF_COLOR if is_buff else cfg.EFFECT_BAR_DEBUFF_COLOR
            pygame.draw.rect(screen, border_col, tip_rect, 1, border_radius=6)

            for i, s in enumerate(line_surfs):
                screen.blit(s, (tip_rect.left + tip_pad, tip_rect.top + tip_pad + i * line_h))
    # ─── Mana Crumble Animation helpers ────────────────────────────────

    def _draw_mana_crumble_segment(
        self,
        screen: pygame.Surface,
        bar_x: int,
        bar_y: int,
        bar_width: int,
        bar_height: int,
        seg,
    ) -> None:
        """Render a single crumbling, dust-emitting segment of the mana bar.

        The segment is described by a normalized [start_norm, end_norm] range
        over the bar.  This function draws:

        1. A faded "ghost" of the lost mana section that smoothly dissolves
           away over ``CONSUME_ANIM_DURATION`` seconds.
        2. A few darker crumble blocks along the right edge of the segment,
           receding as the animation progresses.
        3. Each dust particle defined in ``seg.dust`` (rising and fading).

        Args:
            screen: Target pygame surface.
            bar_x: X position of the mana bar in screen coordinates.
            bar_y: Y position of the mana bar in screen coordinates.
            bar_width: Width of the mana bar in pixels.
            bar_height: Height of the mana bar in pixels.
            seg: A ``_ConsumeSegment`` with ``start_norm``, ``end_norm``,
                ``progress`` (0..1) and a ``dust`` list of particle dicts.
        """
        progress = float(getattr(seg, "progress", 0.0))
        if progress >= 1.0:
            return

        # Convert normalized range to pixel coordinates on the bar.
        seg_x0 = int(bar_x + seg.start_norm * bar_width)
        seg_x1 = int(bar_x + seg.end_norm * bar_width)
        seg_w = max(1, seg_x1 - seg_x0)
        seg_h = bar_height

        # The right edge "eats" inward a little as the animation progresses,
        # so the segment visually shrinks from the right (the part that was
        # just spent is the part that disappears first).
        right_eat = int(seg_w * 0.25 * progress)
        draw_x0 = seg_x0
        draw_x1 = max(seg_x0 + 1, seg_x1 - right_eat)
        draw_w = max(1, draw_x1 - draw_x0)

        # ── 1. Faded ghost of the spent section ──
        ghost_alpha = int(180 * (1.0 - progress))
        if ghost_alpha > 0 and draw_w > 0:
            ghost = pygame.Surface((draw_w, seg_h), pygame.SRCALPHA)
            # Pale lavender fill with a soft vertical gradient
            for y in range(seg_h):
                fade = y / max(1, seg_h - 1)
                r = int(150 + 50 * (1 - fade))
                g = int(110 + 60 * (1 - fade))
                b = int(220 - 20 * fade)
                pygame.draw.line(ghost, (r, g, b, ghost_alpha), (0, y), (draw_w, y))
            # Add a few sparkly highlight stripes that crackle through the
            # segment as it dissolves.
            crackle_t = self.animation_time
            for ci in range(3):
                stripe_x = int((crackle_t * 35 + ci * 37 + seg.start_norm * 17) % draw_w)
                stripe_alpha = int(60 * (1.0 - progress) * (0.4 + 0.6 * math.sin(crackle_t * 6 + ci)))
                if stripe_alpha > 0:
                    pygame.draw.line(ghost, (255, 240, 255, stripe_alpha),
                                     (stripe_x, 0), (stripe_x, seg_h - 1), 1)
            # Top and bottom subtle "disintegrating" borders
            pygame.draw.line(ghost, (220, 200, 255, ghost_alpha // 2), (0, 0), (draw_w, 0), 1)
            pygame.draw.line(ghost, (200, 180, 240, ghost_alpha // 2), (0, seg_h - 1), (draw_w, seg_h - 1), 1)
            screen.blit(ghost, (draw_x0, bar_y))

        # ── 2. Crumble noise blocks along the right (draining) edge ──
        # A row of small chunks that get smaller and sparser over time.
        if draw_w > 2 and seg_h > 3:
            chunk_count = max(2, int(draw_w / 6))
            chunk_layer = pygame.Surface((draw_w, seg_h), pygame.SRCALPHA)
            for ci in range(chunk_count):
                # Each chunk has a stable seed-like offset based on its index
                # and the segment so the same chunk pattern is reproducible.
                seed_t = ci * 0.31 + (seg.start_norm * 5.7)
                wobble = (math.sin(seed_t * 11.1 + self.animation_time * 2.0) * 0.5 + 0.5)
                shrink = progress  # 0..1
                chunk_w = max(1, int(3 * (1.0 - shrink * 0.8) * (0.5 + 0.5 * wobble)))
                chunk_h = max(1, int(seg_h * (0.35 + 0.5 * wobble) * (1.0 - shrink * 0.5)))
                if chunk_w <= 0 or chunk_h <= 0:
                    continue
                # Position chunks in a slightly irregular row near the right
                cx = draw_w - 1 - int((ci + 0.5) * (draw_w / chunk_count))
                if cx < 0 or cx >= draw_w:
                    continue
                cy = (seg_h - chunk_h) // 2 + int(2 * math.sin(seed_t * 7.3 + self.animation_time * 3))
                cy = max(0, min(seg_h - chunk_h, cy))
                chunk_alpha = int(220 * (1.0 - shrink) * (0.5 + 0.5 * wobble))
                if chunk_alpha <= 0:
                    continue
                chunk_color = (180, 150, 240, chunk_alpha)
                pygame.draw.rect(chunk_layer, chunk_color,
                                 (cx - chunk_w // 2, cy, chunk_w, chunk_h))
            screen.blit(chunk_layer, (draw_x0, bar_y))

        # ── 3. Dust particles (drifting upward and out) ──
        for p in seg.dust:
            lt = p.get("lt", 0.0)
            # Each particle stores its starting lifetime; recompute on the
            # fly as 0.55..0.95 (matches _make_dust's spawn range) so we
            # don't have to also persist ``max_lt``.
            max_lt = p.get("max_lt", 0.0)
            if max_lt <= 0.0:
                # Fallback: estimate from spawn range.  This is only used
                # for legacy particles; new ones always set max_lt.
                max_lt = 0.75
            life_ratio = max(0.0, min(1.0, lt / max_lt))
            if life_ratio <= 0.0:
                continue

            # Particle local X is normalized 0..1 across the segment's
            # width.  If a particle has drifted out of the segment via
            # horizontal velocity, skip it (it floats off the bar's edge).
            local_x = p.get("local_x_norm", 0.5)
            local_x = max(0.0, min(1.0, local_x))
            # Y is normalized 0..1 across the *bar height* (not the
            # segment height) and drifts upward.  Skip particles that
            # have flown well above the bar.
            y_norm = p.get("y_norm", 0.5)
            if y_norm < -0.6 or y_norm > 1.4:
                continue
            px = draw_x0 + int(local_x * draw_w)
            y_offset_px = y_norm * seg_h
            py = bar_y + int(y_offset_px)
            # Apply an extra upward drift based on remaining life so
            # dust feels like it lifts off the bar and floats away.
            drift = (1.0 - life_ratio) * 18.0
            py = int(py - drift)

            size = max(0.6, p.get("size", 1.0) * (0.4 + 0.6 * life_ratio))
            r, g, b = p.get("color", (200, 160, 255))
            base_alpha = 220
            alpha = int(base_alpha * life_ratio)
            if alpha <= 0:
                continue

            # Soft glow
            glow_sz = max(1, int(size * 3.5))
            glow_surf = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (r, g, b, alpha // 4),
                               (glow_sz, glow_sz), glow_sz)
            screen.blit(glow_surf, (int(px) - glow_sz, py - glow_sz))
            # Core
            pygame.draw.circle(screen, (r, g, b, alpha), (int(px), py), max(1, int(size)))
            # Bright center for the freshest dust
            if life_ratio > 0.6 and size > 1.0:
                pygame.draw.circle(screen, (255, 240, 255, int(alpha * 0.7)),
                                   (int(px), py), max(1, int(size * 0.55)))

    def _draw_minimap(self, screen: pygame.Surface, game_state):
        if not game_state or not getattr(game_state, 'map', None) or not getattr(game_state.map, 'current_map', None):
            return

        map_w = game_state.map.current_map.pixel_width
        map_h = game_state.map.current_map.pixel_height
        if map_w <= 0 or map_h <= 0:
            return

        sw, sh = screen.get_size()
        mm_w = int(200 * cfg.ui_scale())
        mm_h = int(200 * cfg.ui_scale())
        mm_x = sw - mm_w - 20
        mm_y = self.xp_bar_rect.bottom + 20

        # Background with glassmorphism
        bg_surf = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (20, 20, 30, 200), bg_surf.get_rect(), border_radius=12)
        
        scale_x = mm_w / map_w
        scale_y = mm_h / map_h

        # Draw map background (water/grass)
        pygame.draw.rect(bg_surf, (30, 45, 60, 220), bg_surf.get_rect(), border_radius=12)
        
        # Draw obstacles
        if hasattr(game_state, 'obstacles'):
            for obs in game_state.obstacles:
                ox = int(obs.x * scale_x)
                oy = int(obs.y * scale_y)
                ow = max(1, int(obs.width * scale_x))
                oh = max(1, int(obs.height * scale_y))
                pygame.draw.rect(bg_surf, (50, 60, 80, 200), (ox, oy, ow, oh))

        screen.blit(bg_surf, (mm_x, mm_y))

        # Helper to draw blips
        def draw_blip(world_x, world_y, color, size, pulse=False):
            bx = mm_x + int(world_x * scale_x)
            by = mm_y + int(world_y * scale_y)
            
            if pulse:
                p_size = size + int(math.sin(self.animation_time * 5.0) * 2)
                if p_size > 0:
                    p_alpha = int(100 + 50 * math.sin(self.animation_time * 5.0))
                    p_surf = pygame.Surface((p_size*2, p_size*2), pygame.SRCALPHA)
                    pygame.draw.circle(p_surf, (*color[:3], p_alpha), (p_size, p_size), p_size)
                    screen.blit(p_surf, (bx - p_size, by - p_size))

            pygame.draw.circle(screen, color, (bx, by), size)
            pygame.draw.circle(screen, (255, 255, 255), (bx, by), max(1, size // 2))

        # Transitions
        if hasattr(game_state.map, 'map_transitions') and hasattr(game_state.map, 'current_map_path'):
            transitions = game_state.map.map_transitions.get(game_state.map.current_map_path, {})
            for direction, trans in transitions.items():
                tx, ty = mm_x, mm_y
                tw, th = mm_w, mm_h
                t_color = (100, 200, 255, 150)
                t_rect = None
                thickness = max(2, int(4 * cfg.ui_scale()))
                if direction == "left":
                    t_rect = pygame.Rect(tx, ty, thickness, th)
                elif direction == "right":
                    t_rect = pygame.Rect(tx + tw - thickness, ty, thickness, th)
                elif direction == "up":
                    t_rect = pygame.Rect(tx, ty, tw, thickness)
                elif direction == "down":
                    t_rect = pygame.Rect(tx, ty + th - thickness, tw, thickness)
                
                if t_rect:
                    glow = pygame.Surface((t_rect.width, t_rect.height), pygame.SRCALPHA)
                    pygame.draw.rect(glow, t_color, glow.get_rect(), border_radius=4)
                    screen.blit(glow, t_rect.topleft)

        # Draw enemies
        if hasattr(game_state, 'enemies'):
            for e in game_state.enemies:
                if getattr(e, 'hp', 1) > 0:
                    draw_blip(e.pos.x, e.pos.y, (255, 50, 50), max(2, int(3 * cfg.ui_scale())))

        # Draw NPCs
        npcs = []
        if hasattr(game_state, 'npc'): npcs.append(game_state.npc)
        if hasattr(game_state, 'card_npc'): npcs.append(game_state.card_npc)
        if hasattr(game_state, 'fishing_npc'): npcs.append(game_state.fishing_npc)
        if hasattr(game_state, 'mage_npc'): npcs.append(game_state.mage_npc)
        for n in npcs:
            if n and hasattr(n, 'pos') and n.pos.x >= 0 and n.pos.y >= 0:
                draw_blip(n.pos.x, n.pos.y, (255, 215, 0), max(2, int(4 * cfg.ui_scale())), pulse=True)

        # Draw player
        if hasattr(self, 'character') and hasattr(self.character, 'pos'):
            draw_blip(self.character.pos.x, self.character.pos.y, (50, 255, 50), max(3, int(5 * cfg.ui_scale())), pulse=True)

        # Majestic border
        border_color = (212, 175, 55)
        pygame.draw.rect(screen, border_color, (mm_x - 2, mm_y - 2, mm_w + 4, mm_h + 4), 2, border_radius=14)
        pygame.draw.rect(screen, (255, 230, 100), (mm_x, mm_y, mm_w, mm_h), 1, border_radius=12)

    def draw(self, screen: pygame.Surface):
        # Update animation time using the game clock for smooth animations
        try:
            dt = self.app.clock.get_time() / 1000.0
        except Exception:
            dt = 0.016
        self.animation_time += dt

        try:
            sw, sh = screen.get_size()
            self._ensure_layout(sw, sh)
        except Exception:
            self._ensure_layout(cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)

        icon_x, icon_y = self.hp_icon_pos
        screen.blit(self.hp_icon, (icon_x, icon_y))

        bar_x = self.hp_bar_rect.x
        bar_y = self.hp_bar_rect.y
        bar_width = self.hp_bar_rect.width
        bar_height = self.hp_bar_rect.height

        hp_percent = max(0, self.character.hp / self.character.max_hp)
        current_bar_width = int(bar_width * hp_percent)

        # HP Bar Background (Rounded)
        hp_bg_surf = pygame.Surface((bar_width, bar_height), pygame.SRCALPHA)
        pygame.draw.rect(hp_bg_surf, (40, 40, 50, 200), hp_bg_surf.get_rect(), border_radius=8)
        screen.blit(hp_bg_surf, (bar_x, bar_y))

        # HP Bar Fill (Rounded with gradient and shimmer)
        if current_bar_width > 0:
            fill_radius = min(8, current_bar_width // 2)
            hp_fill_surf = pygame.Surface((current_bar_width, bar_height), pygame.SRCALPHA)
            for x in range(current_bar_width):
                t = x / max(1, current_bar_width)
                r = int(140 + 100 * t)
                g = int(10 + 40 * t)
                b = int(30 + 40 * t)
                pygame.draw.line(hp_fill_surf, (r, g, b, 240), (x, 0), (x, bar_height - 1))
            shimmer_offset = int((self.animation_time * 40) % (current_bar_width + 60)) - 30
            for sx in range(max(0, shimmer_offset), min(current_bar_width, shimmer_offset + 30)):
                shimmer_alpha = int(80 * (1 - abs(sx - shimmer_offset - 15) / 15))
                if shimmer_alpha > 0 and sx < current_bar_width:
                    pygame.draw.line(hp_fill_surf, (255, 200, 200, shimmer_alpha), (sx, 1), (sx, 2))
            clip_surf = pygame.Surface((current_bar_width, bar_height), pygame.SRCALPHA)
            pygame.draw.rect(clip_surf, (255, 255, 255, 255), clip_surf.get_rect(), border_radius=fill_radius)
            hp_fill_surf.blit(clip_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(hp_fill_surf, (bar_x, bar_y))

        # Double Border (dark red outer, bright red inner)
        hp_border_outer = (140, 15, 35)
        hp_border_inner = (255, 60, 80)
        pygame.draw.rect(screen, hp_border_outer, (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2), 2, border_radius=9)
        pygame.draw.rect(screen, hp_border_inner, (bar_x, bar_y, bar_width, bar_height), 1, border_radius=8)

        # Twinkling sparkles
        t = self.animation_time
        hp_star_positions = [
            (0.1, 0.3), (0.3, 0.7), (0.5, 0.2), (0.7, 0.8), (0.9, 0.4),
            (0.15, 0.6), (0.45, 0.5), (0.75, 0.3), (0.85, 0.7)
        ]
        for sx_pct, sy_pct in hp_star_positions:
            sx = bar_x + int(sx_pct * bar_width)
            sy = bar_y + int(sy_pct * bar_height)
            twinkle = (math.sin(t * 4.0 + sx_pct * 10) + 1.0) * 0.5
            if twinkle > 0.6:
                star_alpha = int(200 * (twinkle - 0.6) * 2.5)
                star_size = 1 + int(twinkle * 2)
                star_color = (255, 220, 200, star_alpha)
                pygame.draw.line(screen, star_color[:3], (sx - star_size, sy), (sx + star_size, sy), 1)
                pygame.draw.line(screen, star_color[:3], (sx, sy - star_size), (sx, sy + star_size), 1)

        # Corner glow orbs
        gem_glow = int(100 + 60 * math.sin(t * 3.0))
        for gx, gy in [(bar_x + 4, bar_y + bar_height // 2),
                       (bar_x + bar_width - 4, bar_y + bar_height // 2)]:
            gem_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(gem_surf, (220, 30, 60, gem_glow), (4, 4), 4)
            pygame.draw.circle(gem_surf, (255, 100, 120, gem_glow), (4, 4), 2)
            screen.blit(gem_surf, (gx - 4, gy - 4))

        # Draw HP Text
        hp_text = cfg.INV_nums_font.render(f"{self.character.hp}/{self.character.max_hp}", True, (255, 255, 255))
        screen.blit(hp_text, (bar_x + bar_width // 2 - hp_text.get_width() // 2, bar_y + 5))

        # Draw time indicator
        game_state = self.app.manager.states.get("gameplay")
        time_string = "--:--"
        is_day = True
        if game_state and hasattr(game_state, "_format_game_time"):
            time_string = game_state._format_game_time()
            is_day = game_state.is_daytime()

        # Prettier circular day/night clock
        icon_radius = max(10, int(20 * cfg.ui_scale()))
        icon_center = (bar_x + bar_width + icon_radius + 28, bar_y + bar_height // 2)

        # Background ring with subtle tint
        ring_surf = pygame.Surface((icon_radius*2+8, icon_radius*2+8), pygame.SRCALPHA)
        ring_rect = ring_surf.get_rect(center=icon_center)
        bg_col = tuple(min(255, int(c * 0.9)) for c in cfg.ENVIRONMENT_TINT)
        pygame.draw.circle(ring_surf, (*bg_col, 120), (ring_rect.width//2, ring_rect.height//2), icon_radius+4)
        pygame.draw.circle(ring_surf, (10,10,12,200), (ring_rect.width//2, ring_rect.height//2), icon_radius+2)

        # Draw sun/moon position along the top half of the clock
        try:
            if game_state:
                frac = (game_state.game_time_seconds % game_state.GAME_DAY_SECONDS) / game_state.GAME_DAY_SECONDS
            else:
                frac = 0.25
        except Exception:
            frac = 0.25
        # Convert fraction to angle (0 at midnight -> sun at top moving clockwise)
        angle = frac * 360.0 - 90.0
        rad = math.radians(angle)
        orbit_r = icon_radius - 4
        sun_x = ring_rect.centerx + int(math.cos(rad) * orbit_r)
        sun_y = ring_rect.centery + int(math.sin(rad) * orbit_r)

        # Draw the background ring and the sun/moon
        screen.blit(ring_surf, ring_rect.topleft)

        # Sun or moon body with icon style
        if is_day:
            # --- Sun with rays ---
            sun_color = (255, 210, 60)
            ray_color = (255, 200, 80)
            core_r = max(3, int(icon_radius * 0.38))
            ray_count = 8
            ray_inner = core_r + 2
            ray_outer = icon_radius - 2

            # Animated rotation for the rays
            rot = self.animation_time * 0.4  # slow rotation

            # Glow behind sun
            glow_surf = pygame.Surface((icon_radius * 4, icon_radius * 4), pygame.SRCALPHA)
            grect = glow_surf.get_rect(center=(sun_x, sun_y))
            for r in range(core_r * 3, 0, -4):
                a = int(35 * (1 - r / (core_r * 3)))
                if a > 0:
                    pygame.draw.circle(glow_surf, (255, 220, 110, a), (grect.width // 2, grect.height // 2), r)
            screen.blit(glow_surf, grect.topleft, special_flags=pygame.BLEND_RGBA_ADD)

            # Draw rays as small triangles / lines radiating outward
            for i in range(ray_count):
                a_rad = rot + (math.pi * 2 * i / ray_count)
                rx = sun_x + int(math.cos(a_rad) * ray_inner)
                ry = sun_y + int(math.sin(a_rad) * ray_inner)
                rx2 = sun_x + int(math.cos(a_rad) * ray_outer)
                ry2 = sun_y + int(math.sin(a_rad) * ray_outer)
                ray_w = max(1, int(core_r * 0.35))
                # Perpendicular offset for thickness
                px = int(-math.sin(a_rad) * ray_w)
                py = int(math.cos(a_rad) * ray_w)
                pts = [(rx + px, ry + py), (rx2, ry2), (rx - px, ry - py)]
                pygame.draw.polygon(screen, ray_color, pts)

            # Sun core
            pygame.draw.circle(screen, sun_color, (sun_x, sun_y), core_r)
            # Bright highlight
            highlight_r = max(1, core_r // 2)
            hx = sun_x - max(1, core_r // 4)
            hy = sun_y - max(1, core_r // 4)
            pygame.draw.circle(screen, (255, 245, 170), (hx, hy), highlight_r)
        else:
            # --- Crescent Moon ---
            moon_r = max(4, int(icon_radius * 0.44))
            moon_color = (220, 225, 245)
            shadow_color = (40, 42, 60)

            # Gentle glow behind moon
            glow_surf = pygame.Surface((icon_radius * 4, icon_radius * 4), pygame.SRCALPHA)
            grect = glow_surf.get_rect(center=(sun_x, sun_y))
            for r in range(moon_r * 3, 0, -4):
                a = int(25 * (1 - r / (moon_r * 3)))
                if a > 0:
                    pygame.draw.circle(glow_surf, (180, 190, 255, a), (grect.width // 2, grect.height // 2), r)
            screen.blit(glow_surf, grect.topleft, special_flags=pygame.BLEND_RGBA_ADD)

            # Main moon disc
            pygame.draw.circle(screen, moon_color, (sun_x, sun_y), moon_r)
            # Shadow circle offset to create crescent
            offset_x = int(moon_r * 0.55)
            offset_y = int(-moon_r * 0.25)
            pygame.draw.circle(screen, shadow_color, (sun_x + offset_x, sun_y + offset_y), int(moon_r * 0.80))

            # Tiny stars around the moon
            _rng = random.Random(int(game_state.game_time_seconds // 30) if game_state else 0)
            star_positions = [(_rng.randint(-icon_radius - 4, icon_radius + 4),
                               _rng.randint(-icon_radius - 4, icon_radius + 4)) for _ in range(4)]
            for dx, dy in star_positions:
                sx2, sy2 = sun_x + dx, sun_y + dy
                # Skip stars that overlap the moon body
                dist_sq = (dx * dx + dy * dy)
                if dist_sq < (moon_r + 2) ** 2:
                    continue
                star_size = _rng.choice([1, 1, 1, 2])
                twinkle = (math.sin(self.animation_time * 3.0 + dx * 0.5 + dy * 0.7) + 1.0) * 0.5
                alpha = int(120 + 135 * twinkle)
                star_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
                pygame.draw.circle(star_surf, (255, 255, 230, alpha), (2, 2), star_size)
                screen.blit(star_surf, (sx2 - 2, sy2 - 2))

        # Time text
        time_text = self.font.render(time_string, True, (245, 245, 245))
        screen.blit(time_text, (icon_center[0] + icon_radius + 12, icon_center[1] - time_text.get_height() // 2))

        lives_icon_x, lives_icon_y = self.life_icon_pos

        screen.blit(self.life_icon, (lives_icon_x, lives_icon_y))

        # Death Counter with Shadow
        death_str = f" {self.character.death_count}"
        death_shadow = self.font.render(death_str, True, (0, 0, 0))
        screen.blit(death_shadow, (lives_icon_x + 62, lives_icon_y + 7))
        
        death_text = self.font.render(death_str, True, (220, 50, 50))
        screen.blit(death_text, (lives_icon_x + 60, lives_icon_y + 5))

        # XP Bar
        xp_bar_x = self.xp_bar_rect.x
        xp_bar_y = self.xp_bar_rect.y
        xp_bar_width = self.xp_bar_rect.width
        xp_bar_height = self.xp_bar_rect.height
        
        xp_percent = max(0, self.character.xp / self.character.xp_to_next_level)
        current_xp_width = int(xp_bar_width * xp_percent)
        
        # Draw XP Background
        pygame.draw.rect(screen, (50, 50, 50), (xp_bar_x, xp_bar_y, xp_bar_width, xp_bar_height))
        # Draw XP
        pygame.draw.rect(screen, (0, 200, 0), (xp_bar_x, xp_bar_y, current_xp_width, xp_bar_height))
        # Draw Border
        pygame.draw.rect(screen, (255, 255, 255), (xp_bar_x, xp_bar_y, xp_bar_width, xp_bar_height), 2)
        
        # Level Text
        level_text = self.font.render(f"Lvl {self.character.level}", True, (255, 255, 255))
        level_text_rect = level_text.get_rect(midright=(xp_bar_x - 12, xp_bar_y + xp_bar_height // 2))
        screen.blit(level_text, level_text_rect)

        self.inv_button.draw(screen)
        
        game_state = self.app.manager.states.get("gameplay")
        if game_state:
            self._draw_minimap(screen, game_state)

        stamina_bar_x = self.stamina_bar_rect.x
        stamina_bar_y = self.stamina_bar_rect.y
        stamina_bar_width = self.stamina_bar_rect.width
        stamina_bar_height = self.stamina_bar_rect.height

        stamina_percent = max(0, self.character.stamina / self.character.max_stamina)
        current_stamina_width = int(stamina_bar_width * stamina_percent)

        # Stamina Bar Background (Rounded)
        stam_bg_surf = pygame.Surface((stamina_bar_width, stamina_bar_height), pygame.SRCALPHA)
        pygame.draw.rect(stam_bg_surf, (30, 30, 40, 200), stam_bg_surf.get_rect(), border_radius=6)
        screen.blit(stam_bg_surf, (stamina_bar_x, stamina_bar_y))

        # Stamina Bar Fill (Rounded with gradient and shimmer)
        if current_stamina_width > 0:
            fill_radius = min(6, current_stamina_width // 2)
            stam_fill_surf = pygame.Surface((current_stamina_width, stamina_bar_height), pygame.SRCALPHA)
            for x in range(current_stamina_width):
                t = x / max(1, current_stamina_width)
                r = int(20 + 60 * t)
                g = int(130 + 110 * t)
                b = int(30 + 50 * t)
                pygame.draw.line(stam_fill_surf, (r, g, b, 240), (x, 0), (x, stamina_bar_height - 1))
            shimmer_offset = int((self.animation_time * 40) % (current_stamina_width + 60)) - 30
            for sx in range(max(0, shimmer_offset), min(current_stamina_width, shimmer_offset + 30)):
                shimmer_alpha = int(80 * (1 - abs(sx - shimmer_offset - 15) / 15))
                if shimmer_alpha > 0 and sx < current_stamina_width:
                    pygame.draw.line(stam_fill_surf, (200, 255, 200, shimmer_alpha), (sx, 1), (sx, 2))
            clip_surf = pygame.Surface((current_stamina_width, stamina_bar_height), pygame.SRCALPHA)
            pygame.draw.rect(clip_surf, (255, 255, 255, 255), clip_surf.get_rect(), border_radius=fill_radius)
            stam_fill_surf.blit(clip_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(stam_fill_surf, (stamina_bar_x, stamina_bar_y))

        # Double Border (dark green outer, bright green inner)
        stam_border_outer = (25, 120, 25)
        stam_border_inner = (100, 255, 100)
        pygame.draw.rect(screen, stam_border_outer, (stamina_bar_x - 1, stamina_bar_y - 1, stamina_bar_width + 2, stamina_bar_height + 2), 2, border_radius=7)
        pygame.draw.rect(screen, stam_border_inner, (stamina_bar_x, stamina_bar_y, stamina_bar_width, stamina_bar_height), 1, border_radius=6)

        # Twinkling sparkles
        t = self.animation_time
        stam_star_positions = [
            (0.1, 0.3), (0.3, 0.7), (0.5, 0.2), (0.7, 0.8), (0.9, 0.4),
            (0.15, 0.6), (0.45, 0.5), (0.75, 0.3), (0.85, 0.7)
        ]
        for sx_pct, sy_pct in stam_star_positions:
            sx = stamina_bar_x + int(sx_pct * stamina_bar_width)
            sy = stamina_bar_y + int(sy_pct * stamina_bar_height)
            twinkle = (math.sin(t * 4.0 + sx_pct * 10) + 1.0) * 0.5
            if twinkle > 0.6:
                star_alpha = int(200 * (twinkle - 0.6) * 2.5)
                star_size = 1 + int(twinkle * 2)
                star_color = (200, 255, 200, star_alpha)
                pygame.draw.line(screen, star_color[:3], (sx - star_size, sy), (sx + star_size, sy), 1)
                pygame.draw.line(screen, star_color[:3], (sx, sy - star_size), (sx, sy + star_size), 1)

        # Corner glow orbs
        gem_glow = int(100 + 60 * math.sin(t * 3.0))
        for gx, gy in [(stamina_bar_x + 4, stamina_bar_y + stamina_bar_height // 2),
                       (stamina_bar_x + stamina_bar_width - 4, stamina_bar_y + stamina_bar_height // 2)]:
            gem_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(gem_surf, (50, 200, 50, gem_glow), (4, 4), 4)
            pygame.draw.circle(gem_surf, (120, 255, 120, gem_glow), (4, 4), 2)
            screen.blit(gem_surf, (gx - 4, gy - 4))

        # ═══════════════════════════════════════════════════════════════
        # MANA BAR - Magical Purple-Blue with Gold Trim and Stars
        # ═══════════════════════════════════════════════════════════════
        mana_bar_x = self.mana_bar_rect.x
        mana_bar_y = self.mana_bar_rect.y
        mana_bar_width = self.mana_bar_rect.width
        mana_bar_height = self.mana_bar_rect.height

        mana_percent = max(0, self.character.mana / self.character.max_mana)
        current_mana_width = int(mana_bar_width * mana_percent)

        # Mana Bar Background (Dark purple)
        mana_bg_surf = pygame.Surface((mana_bar_width, mana_bar_height), pygame.SRCALPHA)
        pygame.draw.rect(mana_bg_surf, (15, 8, 35, 220), mana_bg_surf.get_rect(), border_radius=7)
        screen.blit(mana_bg_surf, (mana_bar_x, mana_bar_y))

        # Mana Bar Fill (Gradient purple-blue with shimmer)
        if current_mana_width > 0:
            fill_radius = min(7, current_mana_width // 2)
            mana_fill_surf = pygame.Surface((current_mana_width, mana_bar_height), pygame.SRCALPHA)
            # Base gradient
            for x in range(current_mana_width):
                t = x / max(1, current_mana_width)
                # Purple to blue gradient
                r = int(80 + 60 * (1 - t))
                g = int(40 + 80 * t)
                b = int(180 + 75 * t)
                pygame.draw.line(mana_fill_surf, (r, g, b, 240), (x, 0), (x, mana_bar_height - 1))
            # Shimmer highlight
            shimmer_offset = int((self.animation_time * 40) % (current_mana_width + 60)) - 30
            for sx in range(max(0, shimmer_offset), min(current_mana_width, shimmer_offset + 30)):
                shimmer_alpha = int(80 * (1 - abs(sx - shimmer_offset - 15) / 15))
                if shimmer_alpha > 0 and sx < current_mana_width:
                    pygame.draw.line(mana_fill_surf, (200, 180, 255, shimmer_alpha), (sx, 1), (sx, 2))
            # Clip with rounded corners
            clip_surf = pygame.Surface((current_mana_width, mana_bar_height), pygame.SRCALPHA)
            pygame.draw.rect(clip_surf, (255, 255, 255, 255), clip_surf.get_rect(), border_radius=fill_radius)
            mana_fill_surf.blit(clip_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(mana_fill_surf, (mana_bar_x, mana_bar_y))

        # ─── Magical Crumble Overlay ──────────────────────────────────
        # The just-spent section turns faded and dissolves into dust.
        # The ManaSystem exposes these as normalized [start_norm, end_norm]
        # ranges on the bar.  We render them as:
        #   1) a fading purple/lavender "ghost" fill that loses opacity
        #   2) crumbling noise blocks along the right (draining) edge
        #   3) drifting dust particles that float upward and out
        mana_system = getattr(self.character, "mana_system", None)
        if mana_system is not None and mana_bar_width > 0 and mana_bar_height > 0:
            segments = mana_system.get_consume_segments()
            for seg in segments:
                self._draw_mana_crumble_segment(
                    screen,
                    mana_bar_x,
                    mana_bar_y,
                    mana_bar_width,
                    mana_bar_height,
                    seg,
                )

        # Gold Trim Border (Double layer for richness)
        gold_outer = (212, 175, 55)
        gold_inner = (255, 215, 100)
        pygame.draw.rect(screen, gold_outer, (mana_bar_x - 1, mana_bar_y - 1, mana_bar_width + 2, mana_bar_height + 2), 2, border_radius=8)
        pygame.draw.rect(screen, gold_inner, (mana_bar_x, mana_bar_y, mana_bar_width, mana_bar_height), 1, border_radius=7)

        # Magical Stars and Sparkles
        t = self.animation_time
        star_positions = [
            (0.1, 0.3), (0.3, 0.7), (0.5, 0.2), (0.7, 0.8), (0.9, 0.4),
            (0.15, 0.6), (0.45, 0.5), (0.75, 0.3), (0.85, 0.7)
        ]
        for sx_pct, sy_pct in star_positions:
            sx = mana_bar_x + int(sx_pct * mana_bar_width)
            sy = mana_bar_y + int(sy_pct * mana_bar_height)
            # Twinkle effect
            twinkle = (math.sin(t * 4.0 + sx_pct * 10) + 1.0) * 0.5
            if twinkle > 0.6:
                star_alpha = int(200 * (twinkle - 0.6) * 2.5)
                star_size = 1 + int(twinkle * 2)
                star_color = (255, 255, 200, star_alpha)
                # Draw 4-pointed star
                pygame.draw.line(screen, star_color[:3], (sx - star_size, sy), (sx + star_size, sy), 1)
                pygame.draw.line(screen, star_color[:3], (sx, sy - star_size), (sx, sy + star_size), 1)

        # Corner gem decorations (magical orbs at edges)
        gem_glow = int(100 + 60 * math.sin(t * 3.0))
        for gx, gy in [(mana_bar_x + 4, mana_bar_y + mana_bar_height // 2),
                       (mana_bar_x + mana_bar_width - 4, mana_bar_y + mana_bar_height // 2)]:
            gem_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(gem_surf, (120, 80, 200, gem_glow), (4, 4), 4)
            pygame.draw.circle(gem_surf, (180, 150, 255, gem_glow), (4, 4), 2)
            screen.blit(gem_surf, (gx - 4, gy - 4))

        # Draw vertical skill hotbar (right side) if no shop is open
        if not getattr(self.app.INV_manager, 'current_shop_inv', None):
            panel_rect = pygame.Rect(self.skill_panel_x, self.skill_panel_y, self.skill_panel_width, self.skill_total_slots_height)
            
            # Shadow
            shadow = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 120), shadow.get_rect(), border_radius=cfg.INV_PLAYER_BORDER_RADIUS)
            screen.blit(shadow, (panel_rect.x + 8, panel_rect.y + 8))
            
            # Panel background
            pygame.draw.rect(screen, cfg.INV_PLAYER_BG_COLOR, panel_rect, border_radius=cfg.INV_PLAYER_BORDER_RADIUS)
            pygame.draw.rect(screen, cfg.INV_PLAYER_BORDER_COLOR, panel_rect, cfg.INV_PLAYER_BORDER_WIDTH, border_radius=cfg.INV_PLAYER_BORDER_RADIUS)

            skillbar = getattr(self.character, "skillbar", [])
            for idx, slot in enumerate(self.skill_slot_rects):
                skill = skillbar[idx] if idx < len(skillbar) else None
                self._draw_hud_skill_slot(screen, slot, skill, idx)

        # top skillbar removed

        # ── Active Effects Bar ──────────────────────────────────────
        self._draw_effect_bar(screen)
        # ─── Article Unlock Toast ──────────────────────────────────
        dt = self.app.clock.get_time() / 1000.0 if hasattr(self.app, 'clock') else 0.016
        if self._active_toast is None and self.app.article_notifications:
            notif = self.app.article_notifications.pop(0)
            self._active_toast = notif
            self._toast_timer = 4.0

        if self._active_toast:
            self._toast_timer -= dt
            if self._toast_timer <= 0.0:
                self._active_toast = None
            else:
                section = self._active_toast["section"]
                title = self._active_toast["title"]
                fade = min(255, int(255 * min(1.0, self._toast_timer / 0.5)))
                sw, sh = screen.get_size()
                pw = int(380 * cfg.ui_scale())
                ph = int(90 * cfg.ui_scale())
                px = (sw - pw) // 2
                py = int(20 * cfg.ui_scale())

                bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
                pygame.draw.rect(bg, (20, 15, 25, min(220, fade)), bg.get_rect(), border_radius=10)
                pygame.draw.rect(bg, (212, 175, 55, fade), bg.get_rect(), 2, border_radius=10)
                screen.blit(bg, (px, py))

                icon_surf = self._toast_font.render("\U0001F514", True, (255, 215, 0, fade))
                screen.blit(icon_surf, (px + 10, py + 10))

                tsf = self._toast_title_font.render(title, True, (255, 215, 0))
                tsf.set_alpha(fade)
                screen.blit(tsf, (px + 40, py + 8))

                ssf = self._toast_font.render(f"Section: {section.title()}", True, (180, 160, 130))
                ssf.set_alpha(fade)
                screen.blit(ssf, (px + 40, py + 34))

                hf = self._toast_font.render("Press ESC \u2192 Pause \u2192 Wiki to read", True, (140, 130, 120))
                hf.set_alpha(fade)
                screen.blit(hf, (px + 40, py + 56))
