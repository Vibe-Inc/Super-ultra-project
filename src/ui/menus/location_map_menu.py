import math
import pygame
from typing import TYPE_CHECKING
from gettext import gettext as _

from src.ui.menus.base import Menu
from src.map.locations import (
    LOCATION_DEFS, LOCATION_SLOTS, get_location, can_travel,
)
from src.ui.effects import GOLD, GOLD_BRIGHT, GOLD_DARK, ease_out_cubic
import src.config as cfg

if TYPE_CHECKING:
    from src.app import App

LOC_THEMES = {
    "peaceful_forest": {
        "primary": (60, 140, 50),
        "accent": (100, 200, 70),
        "dark": (30, 80, 25),
        "glow": (80, 220, 60),
        "label": _("Peaceful Forest"),
    },
    "temple": {
        "primary": (180, 140, 50),
        "accent": (220, 180, 60),
        "dark": (100, 80, 30),
        "glow": (255, 215, 0),
        "label": _("Temple"),
    },
    "cave": {
        "primary": (80, 60, 100),
        "accent": (130, 100, 160),
        "dark": (40, 30, 55),
        "glow": (160, 130, 200),
        "label": _("Dark Cave"),
    },
}

EMPTY_THEME = {
    "primary": (35, 35, 45),
    "accent": (55, 55, 70),
    "dark": (20, 20, 28),
    "glow": (60, 60, 80),
    "label": "",
}


class LocationMapMenu(Menu):
    def __init__(self, app: "App"):
        super().__init__(app)
        scale = cfg.ui_scale()
        self._anim_time = 0.0
        self._surf_cache = {}

        self._title_font = cfg.get_font(max(16, int(48 * scale)))
        self._name_font = cfg.get_font(max(12, int(30 * scale)))
        self._hint_font = cfg.get_font(max(9, int(16 * scale)))
        self._fog_font = cfg.get_font(max(14, int(36 * scale)))
        self._icon_font = cfg.get_font(max(16, int(40 * scale)))

        self._card_w = max(1, int(360 * scale))
        self._card_h = max(1, int(76 * scale))
        self._card_gap = max(1, int(16 * scale))
        self._title_bar_h = max(1, int(60 * scale))

    def on_enter(self):
        self._anim_time = 0.0
        game = self.app.manager.states["gameplay"]
        self._current_loc = game.map.current_location_id

        discovered = getattr(game, "discovered_locations", set())
        game.discovered_locations = discovered
        discovered.add("peaceful_forest")

    def _get_surf(self, name, sw, sh):
        key = (name, sw, sh)
        if key in self._surf_cache:
            surf = self._surf_cache[key]
            surf.fill((0, 0, 0, 0))
            return surf
        surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._surf_cache[key] = surf
        return surf

    def _build_cards(self, sw, sh):
        count = len(LOCATION_SLOTS)
        total_h = count * self._card_h + (count - 1) * self._card_gap
        start_y = (sh - total_h) // 2 + self._title_bar_h // 2

        self._cards = []
        for i, slot_id in enumerate(LOCATION_SLOTS):
            cy = start_y + i * (self._card_h + self._card_gap)
            cx = sw // 2
            rect = pygame.Rect(cx - self._card_w // 2, cy, self._card_w, self._card_h)
            self._cards.append({
                "id": slot_id,
                "rect": rect,
                "center": (cx, cy + self._card_h // 2),
            })

    def travel_to_location(self, loc_id):
        game = self.app.manager.states["gameplay"]
        game.discovered_locations.add(loc_id)

        exits = getattr(game.map, "location_exits", {})
        stored = exits.get(loc_id)

        if stored:
            entry_map = stored["map_path"]
            spawn_pos = stored["pos"]
            game.map.current_location_id = loc_id
            game.map.switch_map(entry_map)
        else:
            entry_map = game.map.switch_to_location(loc_id)
            if not entry_map:
                self.app.manager.set_state("gameplay")
                return
            spawn_pos = None

        game.current_map_path = entry_map
        game.obstacles = game.map.get_obstacles()
        game._rebuild_nav_grid()
        game.enemies = []
        spawn_info = game._get_spawn_info(entry_map)
        if entry_map not in game.NO_ENEMY_SPAWN_MAPS and spawn_info:
            new_x, new_y = spawn_info["pos"]
            profile = spawn_info.get("profile")
            game.enemies = [game._create_enemy(new_x, new_y, profile=profile)]
        game._place_npcs_for_map(entry_map)

        if spawn_pos:
            game.character.pos.x = spawn_pos[0]
            game.character.pos.y = spawn_pos[1]
        else:
            loc_def = get_location(loc_id)
            if loc_def and loc_def["entry_tile"]:
                tx, ty = loc_def["entry_tile"]
                tmx_data = game.map.current_map.get_tmx_data()
                if tmx_data:
                    tw = tmx_data.tilewidth
                    th = tmx_data.tileheight
                    game.character.pos.x = tx * tw
                    game.character.pos.y = ty * th
            else:
                tmx_data = game.map.current_map.get_tmx_data()
                if tmx_data:
                    mw = tmx_data.width * tmx_data.tilewidth
                    mh = tmx_data.height * tmx_data.tileheight
                    spawn_type = loc_def.get("entry_spawn_type") if loc_def else None
                    if spawn_type == "bottom_center":
                        game.character.pos.x = mw // 2
                        game.character.pos.y = mh - game.character.image.get_height() - int(100 * cfg.ui_scale())
                    else:
                        game.character.pos.x = mw // 2
                        game.character.pos.y = mh // 2
        self.app.manager.set_state("gameplay")

    def _draw_background(self, screen, sw, sh, t):
        overlay = self._get_surf("overlay", sw, sh)
        alpha = int(200 * min(1.0, t / 0.3))
        overlay.fill((0, 0, 0, min(200, alpha)))
        screen.blit(overlay, (0, 0))

        title_surf = self._get_surf("title_bar", sw, sh)
        title_alpha = int(255 * ease_out_cubic(min(1.0, t / 0.4)))
        if title_alpha < 5:
            return
        bar_h = self._title_bar_h
        pygame.draw.rect(title_surf, (*GOLD_DARK, min(180, title_alpha)),
                        (0, 0, sw, bar_h))
        pygame.draw.rect(title_surf, (*GOLD, min(120, title_alpha)),
                        (0, bar_h - 1, sw, max(1, int(2 * cfg.ui_scale()))))
        screen.blit(title_surf, (0, 0))

        t_text = self._title_font.render(_("Travel Map"), True, GOLD_BRIGHT)
        t_text.set_alpha(title_alpha)
        screen.blit(t_text, (sw // 2 - t_text.get_width() // 2,
                             bar_h // 2 - t_text.get_height() // 2))

    def _draw_connections(self, screen, t):
        game = self.app.manager.states["gameplay"]
        discovered = getattr(game, "discovered_locations", set())
        conn_alpha = int(180 * min(1.0, (t - 0.2) / 0.4))
        if conn_alpha < 5:
            return

        pairs = set()
        for card in self._cards:
            cid = card["id"]
            if cid is None:
                continue
            loc = get_location(cid)
            if not loc:
                continue
            for conn_id in loc["connections"]:
                peer = next((c for c in self._cards if c["id"] == conn_id), None)
                if peer is None:
                    continue
                pair = tuple(sorted([cid, conn_id]))
                if pair in pairs:
                    continue
                pairs.add(pair)

                show = (
                    cid == self._current_loc or conn_id == self._current_loc
                    or can_travel(self._current_loc, cid)
                    or can_travel(self._current_loc, conn_id)
                )

                x1 = card["rect"].centerx
                y1 = card["rect"].bottom
                x2 = peer["rect"].centerx
                y2 = peer["rect"].top
                my = (y1 + y2) / 2

                lw = max(1, int(3 * cfg.ui_scale()))
                if show:
                    pulse = int(120 + 80 * math.sin(t * 2.5))
                    c = (*GOLD_BRIGHT, min(200, pulse))
                    lw = max(1, int(4 * cfg.ui_scale()))
                else:
                    c = (60, 65, 75, min(80, conn_alpha))
                    lw = max(1, int(2 * cfg.ui_scale()))

                pygame.draw.line(screen, c, (int(x1), int(y1)), (int(x2), int(y2)), lw)

                if show:
                    glow_r = max(2, int(4 * cfg.ui_scale() * (0.7 + 0.3 * math.sin(t * 3))))
                    glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_s, (*GOLD_BRIGHT, min(150, pulse)),
                                    (glow_r, glow_r), glow_r)
                    screen.blit(glow_s, (int(my - glow_r), int(my - glow_r)))

    def _draw_deco(self, surf, w, h, theme, alpha):
        r = max(3, int(8 * cfg.ui_scale()))
        pygame.draw.rect(surf, (*theme["dark"], min(220, alpha)), (0, 0, w, h), border_radius=r)
        pygame.draw.rect(surf, (*theme["accent"], min(80, alpha)),
                        (0, 0, w, h), max(1, int(2 * cfg.ui_scale())), border_radius=r)

        bar_w = max(1, int(6 * cfg.ui_scale()))
        bar_r = max(1, int(3 * cfg.ui_scale()))
        pygame.draw.rect(surf, (*theme["glow"], min(140, alpha)),
                        (0, 0, bar_w, h), border_radius=bar_r)

    def _draw_card(self, screen, card, t):
        slot_id = card["id"]
        rect = card["rect"]
        game = self.app.manager.states["gameplay"]
        discovered = getattr(game, "discovered_locations", set())

        card_t = max(0, min(1.0, (t - 0.15) / 0.5))
        card_alpha = int(255 * ease_out_cubic(card_t))
        if card_alpha < 5:
            return

        is_current = slot_id == self._current_loc
        is_discovered = slot_id is not None and slot_id in discovered
        is_connected = slot_id is not None and can_travel(self._current_loc, slot_id)

        if slot_id is None:
            theme = EMPTY_THEME
            surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            self._draw_deco(surf, rect.w, rect.h, theme, card_alpha // 2)
            screen.blit(surf, rect.topleft)
            return

        theme = LOC_THEMES.get(slot_id, EMPTY_THEME)

        if is_current:
            glow_surf = pygame.Surface((rect.w + 12, rect.h + 12), pygame.SRCALPHA)
            g_a = int(60 + 40 * math.sin(t * 3))
            pygame.draw.rect(glow_surf, (*theme["glow"], min(100, g_a)),
                           glow_surf.get_rect(), border_radius=max(3, int(10 * cfg.ui_scale())))
            screen.blit(glow_surf, (rect.x - 6, rect.y - 6))

        surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)

        if not is_discovered:
            self._draw_deco(surf, rect.w, rect.h, EMPTY_THEME, card_alpha)
            screen.blit(surf, rect.topleft)

            fog_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            fog_a = int(160 + 60 * math.sin(t * 2 + hash(slot_id) % 10))
            fog_surf.fill((15, 18, 30, min(200, fog_a)))
            pygame.draw.rect(fog_surf, (30, 35, 50, min(60, card_alpha)),
                           fog_surf.get_rect(), max(1, int(2 * cfg.ui_scale())),
                           border_radius=max(3, int(8 * cfg.ui_scale())))
            screen.blit(fog_surf, rect.topleft)

            q_s = self._fog_font.render("???", True, (120, 120, 140))
            q_s.set_alpha(card_alpha)
            screen.blit(q_s, (rect.x + int(16 * cfg.ui_scale()),
                              rect.centery - q_s.get_height() // 2))
            return

        self._draw_deco(surf, rect.w, rect.h, theme, card_alpha)

        if is_connected:
            pygame.draw.rect(surf, (*theme["glow"], min(40, card_alpha)),
                           (0, 0, rect.w, rect.h), max(1, int(3 * cfg.ui_scale())),
                           border_radius=max(3, int(8 * cfg.ui_scale())))

        screen.blit(surf, rect.topleft)

        icon_x = rect.x + int(20 * cfg.ui_scale())
        icon_y = rect.y + int(10 * cfg.ui_scale())
        icon_s = self._icon_font.render(theme.get("icon", theme["label"][0]), True, (255, 255, 255))
        icon_s.set_alpha(card_alpha)
        screen.blit(icon_s, (icon_x, icon_y))

        name_x = icon_x + self._icon_font.get_height() + int(12 * cfg.ui_scale())
        name_y = rect.y + int(12 * cfg.ui_scale())
        name_s = self._name_font.render(theme["label"], True, (240, 240, 250))
        name_s.set_alpha(card_alpha)
        screen.blit(name_s, (name_x, name_y))

        desc_y = name_y + self._name_font.get_height() + int(2 * cfg.ui_scale())
        if is_current:
            desc = _("You are here")
            dc = (180, 230, 255)
        elif is_connected:
            desc = _("Click to travel")
            dc = theme["glow"]
        elif is_discovered and slot_id != self._current_loc:
            desc = _("Blocked")
            dc = (140, 140, 150)
        else:
            desc = ""
            dc = (0, 0, 0)

        if desc:
            d_s = self._hint_font.render(desc, True, dc)
            d_s.set_alpha(max(0, card_alpha - 40))
            screen.blit(d_s, (name_x, desc_y))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.manager.set_state("gameplay")
                return
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                for card in self._cards:
                    sid = card["id"]
                    if sid is None or sid == self._current_loc:
                        continue
                    if can_travel(self._current_loc, sid):
                        game = self.app.manager.states["gameplay"]
                        if sid in getattr(game, "discovered_locations", set()):
                            self.travel_to_location(sid)
                            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            for card in self._cards:
                sid = card["id"]
                if sid is None:
                    continue
                if card["rect"].collidepoint(event.pos):
                    if sid == self._current_loc:
                        return
                    if can_travel(self._current_loc, sid):
                        game = self.app.manager.states["gameplay"]
                        if sid in getattr(game, "discovered_locations", set()):
                            self.travel_to_location(sid)
                            return
                    break

    def draw(self, screen):
        self._anim_time += 1 / 60
        t = self._anim_time
        sw, sh = self._screen_size(screen)

        self._build_cards(sw, sh)
        self._draw_background(screen, sw, sh, t)
        self._draw_connections(screen, t)
        for card in self._cards:
            self._draw_card(screen, card, t)

        esc = self._hint_font.render(_("ESC to go back"), True, (160, 160, 170))
        esc.set_alpha(int(120 + 80 * math.sin(t * 2)))
        screen.blit(esc, (int(16 * cfg.ui_scale()),
                          int(sh - 32 * cfg.ui_scale())))
