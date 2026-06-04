import math
import pygame
import src.config as cfg
from src.inventory.system import ShopInventory, MAIN_player_inventory, MAIN_player_hotbar, MAIN_player_inventory_equipment, CraftingGrid

def draw_panel_with_shadow(screen, rect, bg_color, border_color, border_width=2, border_radius=15, shadow_offset=8):
    """
    Draws a modern UI panel with a drop shadow effect.

    This helper function creates a rounded rectangular surface for the panel
    background and a slightly offset darker surface underneath to simulate a shadow.

    Args:
        screen (pygame.Surface): The main surface to draw the panel on.
        rect (pygame.Rect): The bounding rectangle for the panel.
        bg_color (tuple): The background color of the panel.
        border_color (tuple): The border color of the panel.
        border_width (int, optional): The thickness of the border. Defaults to 2.
        border_radius (int, optional): The rounding radius of the panel corners. Defaults to 15.
        shadow_offset (int, optional): The pixel offset for the drop shadow. Defaults to 8.
    """
    shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 120), shadow.get_rect(), border_radius=border_radius)
    screen.blit(shadow, (rect.x + shadow_offset, rect.y + shadow_offset))
    
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, bg_color, panel.get_rect(), border_radius=border_radius)
    pygame.draw.rect(panel, border_color, panel.get_rect(), width=border_width, border_radius=border_radius)
    screen.blit(panel, rect.topleft)

class InventoryRenderer:
    """
    Handles all visual rendering operations for the inventory systems.

    This class draws the base inventory slots, shop interfaces, player main 
    inventory, hotbar, and popups using consistent styling, shading, and layouts.

    Attributes:
        slot_bg_color (tuple):
            The background color for standard inventory slots.
        slot_inner_shadow (tuple):
            The inner shadow color used to create depth for slots.
        slot_border_color (tuple):
            The standard border color for unselected slots.
        hover_border (tuple):
            The border color when a slot is hovered by the mouse.
        hover_fill (tuple):
            The background color when a slot is hovered by the mouse.
        _portrait_cache (dict):
            A cache for loaded character portrait images to optimize rendering.

    Methods:
        __init__():
            Initialize the renderer with colors from the configuration.
        draw_base_inventory(screen, inv):
            Render the standard grid of inventory slots and contained items.
        draw_shop(screen, inv):
            Render the merchant interface, including item prices and backgrounds.
        draw_player_inventory(screen, inv):
            Render the player's main inventory, including portrait, money, and skill buttons.
        draw_hotbar(screen, inv):
            Render the quick-access hotbar and highlight the currently active slot.
        draw_split_popup(screen, popup):
            Render the item splitting popup interface and slider.
        _load_portrait_surface(character):
            Load and cache the character's portrait image from disk.
        _crop_face_from_frame(frame):
            Extract a smaller face segment from a full character sprite frame.
        _scale_to_fit(surface, target_rect):
            Proportionally scale a surface to fit within a target rectangle.
    """
    def __init__(self):
        self.slot_bg_color = cfg.INV_SLOT_BG_COLOR
        self.slot_inner_shadow = cfg.INV_SLOT_INNER_SHADOW
        self.slot_border_color = cfg.INV_SLOT_BORDER_COLOR
        self.hover_border = cfg.INV_SLOT_HOVER_BORDER
        self.hover_fill = cfg.INV_SLOT_HOVER_FILL
        self._portrait_cache = {}

    def draw_base_inventory(self, screen, inv):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        for n in range(inv.columns):
            for m in range(inv.rows):
                rect = pygame.Rect(
                    inv.pos_x + (inv.slot_size + inv.border) * n + inv.border,
                    inv.pos_y + (inv.slot_size + inv.border) * m + inv.border,
                    inv.slot_size, inv.slot_size
                )
                
                pygame.draw.rect(screen, self.slot_bg_color, rect, border_radius=cfg.INV_SLOT_BORDER_RADIUS)
                inner_rect = rect.inflate(-4, -4)
                pygame.draw.rect(screen, self.slot_inner_shadow, inner_rect, border_radius=cfg.INV_SLOT_INNER_BORDER_RADIUS)
                
                is_hovered = rect.collidepoint(mouse_x, mouse_y) and not inv.is_hidden
                if is_hovered:
                    hover_surf = pygame.Surface((inv.slot_size, inv.slot_size), pygame.SRCALPHA)
                    pygame.draw.rect(hover_surf, self.hover_fill, hover_surf.get_rect(), border_radius=cfg.INV_SLOT_BORDER_RADIUS)
                    screen.blit(hover_surf, rect.topleft)
                    pygame.draw.rect(screen, self.hover_border, rect, width=2, border_radius=cfg.INV_SLOT_BORDER_RADIUS)
                else:
                    pygame.draw.rect(screen, self.slot_border_color, rect, width=2, border_radius=cfg.INV_SLOT_BORDER_RADIUS)

                if inv.items[n][m]:
                    item, count = inv.items[n][m]
                    if count <= 0 or item is None:
                        inv.items[n][m] = None
                        continue

                    padding = cfg.INV_SLOT_PADDING
                    item_size = inv.slot_size - padding * 2
                    
                    shadow_surf = pygame.Surface((item_size, item_size), pygame.SRCALPHA)
                    pygame.draw.circle(shadow_surf, cfg.INV_ITEM_SHADOW_COLOR, (item_size//2, item_size//2), item_size//2 - 2)
                    screen.blit(shadow_surf, (rect.x + padding + 2, rect.y + padding + 4))
                    
                    screen.blit(item.resize(item_size), (rect.x + padding, rect.y + padding))
                    
                    if count > 1:
                        font_obj = cfg.INV_nums_font
                        text_str = str(count)
                        shadow1 = font_obj.render(text_str, True, (0, 0, 0))
                        shadow2 = font_obj.render(text_str, True, (0, 0, 0))
                        text_surf = font_obj.render(text_str, True, cfg.INV_ITEM_TEXT_COLOR)
                        
                        text_x = rect.right - text_surf.get_width() - 4
                        text_y = rect.bottom - text_surf.get_height() - 2
                        screen.blit(shadow1, (text_x + 2, text_y + 2))
                        screen.blit(shadow2, (text_x + 1, text_y + 1))
                        screen.blit(text_surf, (text_x, text_y))

    def draw_equipment(self, screen, inv: MAIN_player_inventory_equipment):
        # Draw slot backgrounds with labels
        label_font = cfg.INV_nums_font
        for n in range(inv.columns):
            for m in range(inv.rows):
                slot_type = inv.get_slot_type(n, m)
                label = cfg.EQUIPMENT_SLOT_LABELS.get(slot_type, slot_type.capitalize())

                rect = pygame.Rect(
                    inv.pos_x + (inv.slot_size + inv.border) * n + inv.border,
                    inv.pos_y + (inv.slot_size + inv.border) * m + inv.border,
                    inv.slot_size, inv.slot_size
                )

                # Draw slot background
                pygame.draw.rect(screen, self.slot_bg_color, rect, border_radius=cfg.INV_SLOT_BORDER_RADIUS)
                inner_rect = rect.inflate(-4, -4)
                pygame.draw.rect(screen, self.slot_inner_shadow, inner_rect, border_radius=cfg.INV_SLOT_INNER_BORDER_RADIUS)

                mouse_x, mouse_y = pygame.mouse.get_pos()
                is_hovered = rect.collidepoint(mouse_x, mouse_y) and not inv.is_hidden
                if is_hovered:
                    hover_surf = pygame.Surface((inv.slot_size, inv.slot_size), pygame.SRCALPHA)
                    pygame.draw.rect(hover_surf, self.hover_fill, hover_surf.get_rect(), border_radius=cfg.INV_SLOT_BORDER_RADIUS)
                    screen.blit(hover_surf, rect.topleft)
                    pygame.draw.rect(screen, self.hover_border, rect, width=2, border_radius=cfg.INV_SLOT_BORDER_RADIUS)
                else:
                    pygame.draw.rect(screen, self.slot_border_color, rect, width=2, border_radius=cfg.INV_SLOT_BORDER_RADIUS)

                # Draw label only on empty slots
                if not inv.items[n][m]:
                    text_surf = label_font.render(label, True, (80, 85, 95))
                    text_x = rect.centerx - text_surf.get_width() // 2
                    text_y = rect.centery - text_surf.get_height() // 2
                    screen.blit(text_surf, (text_x, text_y))

                # Draw item if present
                if inv.items[n][m]:
                    item, count = inv.items[n][m]
                    if count <= 0:
                        inv.items[n][m] = None
                        continue
                    padding = cfg.INV_SLOT_PADDING
                    item_size = inv.slot_size - padding * 2
                    shadow_surf = pygame.Surface((item_size, item_size), pygame.SRCALPHA)
                    pygame.draw.circle(shadow_surf, cfg.INV_ITEM_SHADOW_COLOR, (item_size//2, item_size//2), item_size//2 - 2)
                    screen.blit(shadow_surf, (rect.x + padding + 2, rect.y + padding + 4))
                    screen.blit(item.resize(item_size), (rect.x + padding, rect.y + padding))
                    if count > 1:
                        font_obj = cfg.INV_nums_font
                        text_str = str(count)
                        shadow1 = font_obj.render(text_str, True, (0, 0, 0))
                        shadow2 = font_obj.render(text_str, True, (0, 0, 0))
                        text_surf = font_obj.render(text_str, True, cfg.INV_ITEM_TEXT_COLOR)
                        text_x = rect.right - text_surf.get_width() - 4
                        text_y = rect.bottom - text_surf.get_height() - 2
                        screen.blit(shadow1, (text_x + 2, text_y + 2))
                        screen.blit(shadow2, (text_x + 1, text_y + 1))
                        screen.blit(text_surf, (text_x, text_y))

    def draw_shop(self, screen, inv: ShopInventory):
        sc = cfg.ui_scale()
        bg_rect = pygame.Rect(
            inv.pos_x - int(20 * sc), inv.pos_y - int(20 * sc),
            (inv.slot_size + inv.border) * inv.columns + inv.border + int(40 * sc),
            (inv.slot_size + inv.border) * inv.rows + inv.border + int(40 * sc)
        )
        
        draw_panel_with_shadow(
            screen, bg_rect, bg_color=cfg.INV_SHOP_BG_COLOR, 
            border_color=cfg.INV_SHOP_BORDER_COLOR, border_width=cfg.INV_SHOP_BORDER_WIDTH, 
            border_radius=cfg.INV_SHOP_BORDER_RADIUS, shadow_offset=cfg.INV_SHOP_SHADOW_OFFSET
        )
        
        title_font = cfg.tooltip_font_CREDITS
        title_surf = title_font.render("MERCHANT", True, cfg.INV_SHOP_TITLE_COLOR)
        screen.blit(title_surf, (bg_rect.centerx - title_surf.get_width()//2, bg_rect.y - int(10 * sc)))
        
        self.draw_base_inventory(screen, inv)
        
        for x in range(inv.columns):
            for y in range(inv.rows):
                if inv.items[x][y]:
                    price = getattr(inv.items[x][y][0], 'price', 0)
                    font = cfg.INV_nums_font
                    text = font.render(f"{price}G", True, cfg.INV_SHOP_PRICE_TEXT_COLOR)
                    shadow = font.render(f"{price}G", True, cfg.INV_SHOP_PRICE_SHADOW_COLOR)
                    
                    rect_x = inv.pos_x + (inv.slot_size + inv.border) * x + inv.border
                    rect_y = inv.pos_y + (inv.slot_size + inv.border) * y + inv.border
                    
                    price_bg = pygame.Surface((text.get_width() + 6, text.get_height() + 2), pygame.SRCALPHA)
                    pygame.draw.rect(price_bg, cfg.INV_SHOP_PRICE_BG_COLOR, price_bg.get_rect(), border_radius=cfg.INV_SHOP_PRICE_BG_BORDER_RADIUS)
                    
                    bg_pos = (rect_x + inv.slot_size//2 - price_bg.get_width()//2, rect_y + inv.slot_size - 18)
                    screen.blit(price_bg, bg_pos)
                    screen.blit(shadow, (bg_pos[0] + 4, bg_pos[1] + 2))
                    screen.blit(text, (bg_pos[0] + 3, bg_pos[1] + 1))

        if getattr(inv, 'close_button', None):
            inv.close_button.rect.topleft = (bg_rect.right - inv.close_button.rect.width - int(16 * sc), bg_rect.bottom - inv.close_button.rect.height - int(16 * sc))
            try: inv.close_button._update_text_surface()
            except Exception: pass
            inv.close_button.draw(screen)

    def draw_player_inventory(self, screen, inv: MAIN_player_inventory):
        sc = cfg.ui_scale()
        btn_extra = int(inv.slot_size * cfg.INV_PLAYER_RIGHT_BTN_EXTRA)
        bg_rect = pygame.Rect(
            inv.pos_x - int(24 * sc), inv.pos_y - int(340 * sc),
            (inv.slot_size + inv.border) * inv.columns + inv.border + int(48 * sc) + btn_extra,
            (inv.slot_size + inv.border) * inv.rows + inv.border + int(364 * sc)
        )
        
        draw_panel_with_shadow(
            screen, bg_rect, bg_color=cfg.INV_PLAYER_BG_COLOR, 
            border_color=cfg.INV_PLAYER_BORDER_COLOR, border_width=cfg.INV_PLAYER_BORDER_WIDTH, 
            border_radius=cfg.INV_PLAYER_BORDER_RADIUS, shadow_offset=cfg.INV_PLAYER_SHADOW_OFFSET
        )
            
        preview_offset_x = int(cfg.INV_PLAYER_PREVIEW_OFFSET_X * sc)
        preview_x = inv.pos_x + preview_offset_x
        
        portrait_bg = pygame.Rect(preview_x, inv.pos_y + int(cfg.INV_PLAYER_PREVIEW_Y_OFFSET * sc), 
                                  int(cfg.INV_PLAYER_PREVIEW_WIDTH * sc), int(cfg.INV_PLAYER_PREVIEW_HEIGHT * sc))
        pygame.draw.rect(screen, cfg.INV_SLOT_INNER_SHADOW, portrait_bg, border_radius=cfg.INV_PLAYER_PORTRAIT_BORDER_RADIUS)
        
        game_state = inv.app.manager.states.get("gameplay")
        if game_state and hasattr(game_state, "character"):
            character = game_state.character
            portrait = self._load_portrait_surface(character) or self._crop_face_from_frame(character.image)
            scaled_img = self._scale_to_fit(portrait, portrait_bg)
            screen.blit(scaled_img, scaled_img.get_rect(center=portrait_bg.center))

        pygame.draw.rect(screen, cfg.INV_PLAYER_PORTRAIT_BORDER_COLOR_1, portrait_bg, 
                        width=3, border_radius=cfg.INV_PLAYER_PORTRAIT_BORDER_RADIUS)
        pygame.draw.rect(screen, cfg.INV_PLAYER_PORTRAIT_BORDER_COLOR_2, portrait_bg.inflate(2, 2), 
                        width=1, border_radius=cfg.INV_PLAYER_PORTRAIT_BORDER_RADIUS)

        money_panel = pygame.Rect(preview_x, inv.pos_y + int(cfg.INV_PLAYER_MONEY_PANEL_Y_OFFSET * sc), 
                                 int(cfg.INV_PLAYER_MONEY_PANEL_WIDTH * sc), int(cfg.INV_PLAYER_MONEY_PANEL_HEIGHT * sc))
        pygame.draw.rect(screen, cfg.INV_PLAYER_MONEY_PANEL_BG_COLOR, money_panel, 
                        border_radius=cfg.INV_PLAYER_MONEY_PANEL_BORDER_RADIUS)
        pygame.draw.rect(screen, cfg.INV_PLAYER_MONEY_PANEL_BORDER_COLOR, money_panel, 
                        width=2, border_radius=cfg.INV_PLAYER_MONEY_PANEL_BORDER_RADIUS)
        
        money_text = f"{inv.app.money} G"
        text_surf = cfg.tooltip_font_CREDITS.render(money_text, True, cfg.INV_PLAYER_MONEY_TEXT_COLOR)
        shadow_surf = cfg.tooltip_font_CREDITS.render(money_text, True, (0, 0, 0))
        
        text_pos_x = money_panel.centerx - text_surf.get_width() // 2
        text_pos_y = money_panel.centery - text_surf.get_height() // 2
        screen.blit(shadow_surf, (text_pos_x + 1, text_pos_y + 1))
        screen.blit(text_surf, (text_pos_x, text_pos_y))

        # ─── Right-side majestic skillbar & talent tree & arcane quest buttons ───
        if not getattr(inv.app.INV_manager, 'current_shop_inv', None):
            gap = int(cfg.INV_PLAYER_RIGHT_BTN_GAP * sc)

            btn_x = portrait_bg.right + int(cfg.INV_PLAYER_RIGHT_BTN_MARGIN_X * sc) + int(120 * sc)
            # Include the new ARCANE QUESTS button in the stack
            has_arcane = hasattr(inv, 'open_arcane_quest_btn')
            stack_count = 3 if has_arcane else 2
            stack_height = (
                inv.open_skillbar_btn.rect.height
                + inv.open_skilltree_btn.rect.height
                + (inv.open_arcane_quest_btn.rect.height if has_arcane else 0)
                + gap * (stack_count - 1)
            )
            btn_y = portrait_bg.centery - stack_height // 2 + int(100 * sc)

            inv.open_skillbar_btn.rect.topleft = (btn_x, btn_y)
            inv.open_skilltree_btn.rect.topleft = (
                btn_x, btn_y + inv.open_skillbar_btn.rect.height + gap
            )
            if has_arcane:
                inv.open_arcane_quest_btn.rect.topleft = (
                    btn_x,
                    btn_y + inv.open_skillbar_btn.rect.height + gap
                          + inv.open_skilltree_btn.rect.height + gap,
                )

            try: inv.open_skillbar_btn._update_text_surface()
            except Exception: pass
            try: inv.open_skilltree_btn._update_text_surface()
            except Exception: pass
            if has_arcane:
                try: inv.open_arcane_quest_btn._update_text_surface()
                except Exception: pass

            self._draw_majestic_skill_button(screen, inv.open_skillbar_btn, is_skillbar=True, pulse_offset=0.0)
            self._draw_majestic_skill_button(screen, inv.open_skilltree_btn, is_skillbar=False, pulse_offset=2.0)
            if has_arcane:
                self._draw_majestic_arcane_quest_button(screen, inv.open_arcane_quest_btn, pulse_offset=4.0)

        self.draw_base_inventory(screen, inv)

    def _draw_majestic_skill_button(self, screen, button, is_skillbar=True, pulse_offset=0.0):
        rect = button.rect
        t = pygame.time.get_ticks() / 1000.0
        pulse = (math.sin(t * 0.004 + pulse_offset) + 1) / 2
        scale = cfg.ui_scale()
        is_hovered = rect.collidepoint(pygame.mouse.get_pos())

        gold = (212, 175, 55)
        gold_light = (240, 210, 100)
        gold_dark = (150, 120, 50)

        if is_skillbar:
            theme_primary = (60, 100, 200)
            theme_glow = (100, 150, 255)
            theme_bg = (25, 30, 45)
        else:
            theme_primary = (160, 60, 200)
            theme_glow = (190, 120, 255)
            theme_bg = (35, 22, 45)

        hover_boost = 0.3 if is_hovered else 0.0

        # ── Radiant aura ──
        aura_size = int(rect.width * 2.2)
        aura_surf = pygame.Surface((aura_size, aura_size), pygame.SRCALPHA)
        aura_alpha = int(35 + pulse * 30 + hover_boost * 40)
        for r in range(aura_size // 2, 0, -1):
            a = int(aura_alpha * (1.0 - r / (aura_size // 2)))
            if a > 0:
                c = tuple(min(255, int(c * 1.0)) for c in theme_glow)
                pygame.draw.circle(aura_surf, (*c, a), (aura_size // 2, aura_size // 2), r)
        screen.blit(aura_surf, (rect.centerx - aura_size // 2, rect.centery - aura_size // 2))

        # ── Outer ornate triple-gold frame ──
        pad = int(6 * scale)
        frame_rect = pygame.Rect(rect.x - pad, rect.y - pad, rect.width + pad * 2, rect.height + pad * 2)
        for fi in range(3):
            frect = pygame.Rect(frame_rect.x - fi, frame_rect.y - fi,
                                frame_rect.width + fi * 2, frame_rect.height + fi * 2)
            fc = [gold_light, gold, gold_dark][fi]
            bw = max(1, int(2.5 * scale - fi * 0.4 + hover_boost))
            pygame.draw.rect(screen, fc, frect, width=bw,
                             border_radius=int(10 * scale - fi * 2))

        # ── Corner gems ──
        gem_size = max(1, int(4 * scale + pulse * 1.5 + hover_boost * 2))
        gem_colors = [(220, 40, 40), (40, 70, 220), (40, 200, 40), (220, 180, 40)]
        for gi, (gx, gy) in enumerate([
            (frame_rect.x, frame_rect.y), (frame_rect.right, frame_rect.y),
            (frame_rect.x, frame_rect.bottom), (frame_rect.right, frame_rect.bottom)
        ]):
            gc = gem_colors[gi]
            lighter = tuple(min(255, c + 80) for c in gc)
            darker = tuple(max(0, c - 40) for c in gc)
            pts_top = [(gx, gy - gem_size), (gx - gem_size, gy), (gx + gem_size, gy)]
            pts_bot = [(gx - gem_size, gy), (gx + gem_size, gy), (gx, gy + gem_size)]
            pygame.draw.polygon(screen, lighter, pts_top)
            pygame.draw.polygon(screen, darker, pts_bot)

            # Gem sparkle
            spark_sz = max(1, gem_size // 2)
            spark_surf = pygame.Surface((spark_sz * 4, spark_sz * 4), pygame.SRCALPHA)
            spark_alpha = int(180 * pulse)
            pygame.draw.circle(spark_surf, (255, 255, 255, spark_alpha), (spark_sz * 2, spark_sz * 2), spark_sz)
            screen.blit(spark_surf, (gx - spark_sz * 2, gy - spark_sz * 2))

        # ── Button background ──
        if is_hovered:
            bg = tuple(min(255, c + 15) for c in theme_bg)
        else:
            bg = theme_bg
        pygame.draw.rect(screen, bg, rect, border_radius=int(8 * scale))

        # Inner glowing border
        inner_border = rect.inflate(-int(3 * scale), -int(3 * scale))
        ib_pulse = (math.sin(t * 0.005 + pulse_offset + 1) + 1) * 0.3 + 0.4
        ib_color = tuple(min(255, int(c * ib_pulse)) for c in theme_primary)
        pygame.draw.rect(screen, ib_color, inner_border, width=max(1, int(2 * scale)),
                         border_radius=int(6 * scale))

        # ── Icon ──
        icon_cx = rect.left + int(rect.width * 0.2)
        icon_cy = rect.centery

        if is_skillbar:
            # Spellbook icon
            bw = int(rect.width * 0.22)
            bh = int(rect.height * 0.7)
            shadow_rect = pygame.Rect(icon_cx - bw // 2 + int(1.5 * scale),
                                      icon_cy - bh // 2 + int(1.5 * scale), bw, bh)
            shadow_s = pygame.Surface((bw, bh), pygame.SRCALPHA)
            pygame.draw.rect(shadow_s, (0, 0, 0, 80), shadow_s.get_rect(), border_radius=int(3 * scale))
            screen.blit(shadow_s, shadow_rect)

            cover = pygame.Rect(icon_cx - bw // 2, icon_cy - bh // 2, bw, bh)
            pygame.draw.rect(screen, (70, 18, 10), cover, border_radius=int(3 * scale))
            pygame.draw.rect(screen, gold, cover, width=max(1, int(1.5 * scale)),
                             border_radius=int(3 * scale))

            spine_w = max(2, int(bw * 0.2))
            spine = pygame.Rect(icon_cx - spine_w // 2, cover.y, spine_w, bh)
            pygame.draw.rect(screen, gold_dark, spine, border_radius=int(1 * scale))

            page_color = (250, 240, 215)
            pm = max(1, int(bw * 0.1))
            left_p = pygame.Rect(cover.x + pm, cover.y + int(bh * 0.12),
                                 spine.x - cover.x - pm, int(bh * 0.76))
            right_p = pygame.Rect(spine.right, cover.y + int(bh * 0.12),
                                  cover.right - spine.right - pm, int(bh * 0.76))
            pygame.draw.rect(screen, page_color, left_p)
            pygame.draw.rect(screen, page_color, right_p)

            accent_y = cover.y + int(bh * 0.35)
            pygame.draw.line(screen, gold, (cover.x + int(bw * 0.15), accent_y),
                             (cover.right - int(bw * 0.15), accent_y), max(1, int(1 * scale)))
        else:
            # Crown/Tree icon
            tw = int(rect.width * 0.28)
            th = int(rect.height * 0.65)

            # Crown base
            crown_rect = pygame.Rect(icon_cx - tw // 2, icon_cy - th // 2, tw, th)
            crown_color = (200, 160, 50)
            crown_dark = (140, 110, 40)

            # Crown points (3 peaks)
            pts = [
                (crown_rect.left, crown_rect.bottom),
                (crown_rect.left + tw // 4, crown_rect.top + th // 4),
                (icon_cx, crown_rect.top),
                (crown_rect.right - tw // 4, crown_rect.top + th // 4),
                (crown_rect.right, crown_rect.bottom),
            ]
            pygame.draw.polygon(screen, crown_dark, pts)
            pygame.draw.polygon(screen, crown_color, [(p[0], p[1] - 1) for p in pts], width=0)

            # Crown band
            band_y = crown_rect.bottom - int(th * 0.22)
            pygame.draw.line(screen, gold, (crown_rect.left + 2, band_y),
                             (crown_rect.right - 2, band_y), max(1, int(2 * scale)))

            # Crown jewels
            jcolors = [(220, 40, 40), (40, 200, 40), (40, 70, 220)]
            jewel_positions = [icon_cx, icon_cx - tw // 4, icon_cx + tw // 4]
            for ji, jx in enumerate(jewel_positions):
                jc = jcolors[ji % len(jcolors)]
                pygame.draw.circle(screen, jc, (jx, crown_rect.top + int(th * 0.12)),
                                   max(1, int(2.5 * scale)))

        # ── Text in gold ──
        text_x = rect.left + int(rect.width * 0.4)
        text_w = rect.width - (text_x - rect.x) - 8
        text_surf = button.font.render(button.text, True, gold_light)
        if text_surf.get_width() > text_w:
            text_surf = pygame.transform.smoothscale(text_surf,
                (int(text_w), int(text_surf.get_height() * text_w / text_surf.get_width())))
        shadow_surf = button.font.render(button.text, True, (0, 0, 0))
        if shadow_surf.get_width() > text_w:
            shadow_surf = pygame.transform.smoothscale(shadow_surf,
                (int(text_w), int(shadow_surf.get_height() * text_w / shadow_surf.get_width())))

        txt_rect = text_surf.get_rect(midleft=(text_x, rect.centery))
        shd_rect = shadow_surf.get_rect(midleft=(text_x + 1, rect.centery + 1))

        # Text glow
        glow_txt = pygame.Surface((text_surf.get_width() + 20, text_surf.get_height() + 20), pygame.SRCALPHA)
        glow_alpha = int(40 + 30 * pulse)
        glow_txt.fill((*theme_glow, glow_alpha))
        # Soften the glow edges
        glow_center = pygame.Rect(6, 6, text_surf.get_width() + 8, text_surf.get_height() + 8)
        pygame.draw.rect(glow_txt, (*theme_glow, 0), glow_center)
        screen.blit(glow_txt, (txt_rect.x - 10, txt_rect.y - 10))

        screen.blit(shadow_surf, shd_rect)
        screen.blit(text_surf, txt_rect)

        # ── Sparkle dots around button ──
        for si in range(3):
            angle = si * 2.094 + t * 0.5 + pulse_offset
            dist = rect.width * 0.7
            sx = rect.centerx + int(math.cos(angle) * dist)
            sy = rect.centery + int(math.sin(angle) * dist)
            dot_s = max(1, int(1.5 * scale + pulse * 0.8))
            da = int(150 + 105 * pulse)
            dot_surf = pygame.Surface((dot_s * 4, dot_s * 4), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, (*gold_light, da), (dot_s * 2, dot_s * 2), dot_s)
            screen.blit(dot_surf, (sx - dot_s * 2, sy - dot_s * 2))

        # ── Hover border glow ──
        if is_hovered:
            hw = max(1, int(3 * scale))
            hover_pulse = (math.sin(t * 0.008 + pulse_offset) + 1) * 0.3 + 0.4
            hc = tuple(min(255, int(c * hover_pulse)) for c in gold_light)
            pygame.draw.rect(screen, hc, rect, width=hw, border_radius=int(8 * scale))

    def _draw_majestic_arcane_quest_button(self, screen, button, pulse_offset=4.0):
        """Render the ARCANE QUESTS button with a magical gold/purple aura.

        Visually echoes the Arcane Quest menu's title bar: gold & purple
        accents on a near-black base, with a soft pulsing aura.
        """
        rect = button.rect
        t = pygame.time.get_ticks() / 1000.0
        pulse = (math.sin(t * 0.004 + pulse_offset) + 1) / 2
        scale = cfg.ui_scale()
        is_hovered = rect.collidepoint(pygame.mouse.get_pos())

        gold = (212, 175, 55)
        gold_light = (240, 210, 100)
        gold_dark = (150, 120, 50)
        purple_bright = (200, 130, 255)
        purple = (140, 80, 220)
        theme_glow = purple_bright
        theme_bg = (28, 14, 50)
        hover_boost = 0.3 if is_hovered else 0.0

        # ── Magical aura (gold + purple blend) ──
        aura_size = int(rect.width * 2.2)
        aura_surf = pygame.Surface((aura_size, aura_size), pygame.SRCALPHA)
        aura_alpha = int(40 + pulse * 35 + hover_boost * 40)
        for r in range(aura_size // 2, 0, -1):
            a = int(aura_alpha * (1.0 - r / (aura_size // 2)))
            if a > 0:
                t_r = r / (aura_size // 2)
                c = (
                    int(gold_light[0] * (1 - t_r) + purple_bright[0] * t_r),
                    int(gold_light[1] * (1 - t_r) + purple_bright[1] * t_r),
                    int(gold_light[2] * (1 - t_r) + purple_bright[2] * t_r),
                )
                pygame.draw.circle(aura_surf, (*c, a), (aura_size // 2, aura_size // 2), r)
        screen.blit(aura_surf, (rect.centerx - aura_size // 2, rect.centery - aura_size // 2))

        # ── Outer ornate triple-frame (gold, gold-dark, purple) ──
        pad = int(6 * scale)
        frame_rect = pygame.Rect(rect.x - pad, rect.y - pad, rect.width + pad * 2, rect.height + pad * 2)
        for fi in range(3):
            frect = pygame.Rect(frame_rect.x - fi, frame_rect.y - fi,
                                frame_rect.width + fi * 2, frame_rect.height + fi * 2)
            fc = [gold_light, gold, purple][fi]
            bw = max(1, int(2.5 * scale - fi * 0.4 + hover_boost))
            pygame.draw.rect(screen, fc, frect, width=bw,
                             border_radius=int(10 * scale - fi * 2))

        # ── Corner gems (gold, purple, gold, purple) ──
        gem_size = max(1, int(4 * scale + pulse * 1.5 + hover_boost * 2))
        gem_colors = [gold, purple_bright, gold, purple_bright]
        for gi, (gx, gy) in enumerate([
            (frame_rect.x, frame_rect.y), (frame_rect.right, frame_rect.y),
            (frame_rect.x, frame_rect.bottom), (frame_rect.right, frame_rect.bottom)
        ]):
            gc = gem_colors[gi]
            lighter = tuple(min(255, c + 60) for c in gc)
            darker = tuple(max(0, c - 40) for c in gc)
            pts_top = [(gx, gy - gem_size), (gx - gem_size, gy), (gx + gem_size, gy)]
            pts_bot = [(gx - gem_size, gy), (gx + gem_size, gy), (gx, gy + gem_size)]
            pygame.draw.polygon(screen, lighter, pts_top)
            pygame.draw.polygon(screen, darker, pts_bot)
            spark_sz = max(1, gem_size // 2)
            spark_surf = pygame.Surface((spark_sz * 4, spark_sz * 4), pygame.SRCALPHA)
            spark_alpha = int(180 * pulse)
            pygame.draw.circle(spark_surf, (255, 255, 255, spark_alpha), (spark_sz * 2, spark_sz * 2), spark_sz)
            screen.blit(spark_surf, (gx - spark_sz * 2, gy - spark_sz * 2))

        # ── Button background (dark purple-black) ──
        if is_hovered:
            bg = tuple(min(255, c + 18) for c in theme_bg)
        else:
            bg = theme_bg
        pygame.draw.rect(screen, bg, rect, border_radius=int(8 * scale))

        # Inner glowing purple border
        inner_border = rect.inflate(-int(3 * scale), -int(3 * scale))
        ib_pulse = (math.sin(t * 0.005 + pulse_offset + 1) + 1) * 0.3 + 0.4
        ib_color = tuple(min(255, int(c * ib_pulse)) for c in purple)
        pygame.draw.rect(screen, ib_color, inner_border, width=max(1, int(2 * scale)),
                         border_radius=int(6 * scale))

        # ── Icon: a magical scroll with a star above ──
        icon_cx = rect.left + int(rect.width * 0.2)
        icon_cy = rect.centery

        # Scroll body
        sw = int(rect.width * 0.22)
        sh = int(rect.height * 0.55)
        scroll_rect = pygame.Rect(icon_cx - sw // 2, icon_cy - sh // 2, sw, sh)
        pygame.draw.rect(screen, gold_dark, scroll_rect, border_radius=int(2 * scale))
        pygame.draw.rect(screen, gold, scroll_rect, width=max(1, int(1 * scale)),
                         border_radius=int(2 * scale))
        # Parchment inside
        page_rect = scroll_rect.inflate(-int(3 * scale), -int(3 * scale))
        pygame.draw.rect(screen, (245, 230, 200), page_rect, border_radius=int(1 * scale))
        # A purple star above the scroll
        star_cy = scroll_rect.top - max(2, int(3 * scale))
        sp = [(icon_cx, star_cy - int(5 * scale)),
              (icon_cx + int(3 * scale), star_cy - int(1 * scale)),
              (icon_cx + int(5 * scale), star_cy),
              (icon_cx + int(3 * scale), star_cy + int(1 * scale)),
              (icon_cx, star_cy + int(5 * scale)),
              (icon_cx - int(3 * scale), star_cy + int(1 * scale)),
              (icon_cx - int(5 * scale), star_cy),
              (icon_cx - int(3 * scale), star_cy - int(1 * scale))]
        pygame.draw.polygon(screen, purple_bright, sp)
        glow = pygame.Surface((int(20 * scale), int(20 * scale)), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*purple_bright, int(120 * pulse)),
                           (int(10 * scale), int(10 * scale)), int(8 * scale))
        screen.blit(glow, (icon_cx - int(10 * scale), star_cy - int(10 * scale)))

        # ── Text in gold with purple glow ──
        text_x = rect.left + int(rect.width * 0.4)
        text_w = rect.width - (text_x - rect.x) - 8
        text_surf = button.font.render(button.text, True, gold_light)
        if text_surf.get_width() > text_w:
            text_surf = pygame.transform.smoothscale(text_surf,
                (int(text_w), int(text_surf.get_height() * text_w / text_surf.get_width())))
        shadow_surf = button.font.render(button.text, True, (0, 0, 0))
        if shadow_surf.get_width() > text_w:
            shadow_surf = pygame.transform.smoothscale(shadow_surf,
                (int(text_w), int(shadow_surf.get_height() * text_w / shadow_surf.get_width())))

        txt_rect = text_surf.get_rect(midleft=(text_x, rect.centery))
        shd_rect = shadow_surf.get_rect(midleft=(text_x + 1, rect.centery + 1))

        glow_txt = pygame.Surface((text_surf.get_width() + 20, text_surf.get_height() + 20), pygame.SRCALPHA)
        glow_alpha = int(50 + 30 * pulse)
        glow_txt.fill((*theme_glow, glow_alpha))
        glow_center = pygame.Rect(6, 6, text_surf.get_width() + 8, text_surf.get_height() + 8)
        pygame.draw.rect(glow_txt, (*theme_glow, 0), glow_center)
        screen.blit(glow_txt, (txt_rect.x - 10, txt_rect.y - 10))

        screen.blit(shadow_surf, shd_rect)
        screen.blit(text_surf, txt_rect)

        # Sparkle dots around the button
        for si in range(4):
            angle = si * 1.57 + t * 0.5 + pulse_offset
            dist = rect.width * 0.68
            sx = rect.centerx + int(math.cos(angle) * dist)
            sy = rect.centery + int(math.sin(angle) * dist)
            dot_s = max(1, int(1.5 * scale + pulse * 0.8))
            da = int(150 + 105 * pulse)
            col = gold_light if si % 2 == 0 else purple_bright
            dot_surf = pygame.Surface((dot_s * 4, dot_s * 4), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, (*col, da), (dot_s * 2, dot_s * 2), dot_s)
            screen.blit(dot_surf, (sx - dot_s * 2, sy - dot_s * 2))

        # Hover border glow
        if is_hovered:
            hw = max(1, int(3 * scale))
            hover_pulse = (math.sin(t * 0.008 + pulse_offset) + 1) * 0.3 + 0.4
            hc = tuple(min(255, int(c * hover_pulse)) for c in gold_light)
            pygame.draw.rect(screen, hc, rect, width=hw, border_radius=int(8 * scale))

    def draw_hotbar(self, screen, inv: MAIN_player_hotbar):
        inv.update_position()
        sc = cfg.ui_scale()
        bg_rect = pygame.Rect(
            inv.pos_x - int(16 * sc), inv.pos_y - int(16 * sc),
            (inv.slot_size + inv.border) * inv.columns + inv.border + int(32 * sc),
            (inv.slot_size + inv.border) * inv.rows + inv.border + int(32 * sc)
        )
        
        draw_panel_with_shadow(
            screen, bg_rect, bg_color=cfg.INV_HOTBAR_BG_COLOR, 
            border_color=cfg.INV_HOTBAR_BORDER_COLOR, border_width=cfg.INV_HOTBAR_BORDER_WIDTH, 
            border_radius=cfg.INV_HOTBAR_BORDER_RADIUS, shadow_offset=cfg.INV_HOTBAR_SHADOW_OFFSET
        )
        
        self.draw_base_inventory(screen, inv)

        active_rect_x = inv.pos_x + (inv.slot_size + inv.border) * inv.active_slot_index + inv.border
        active_rect_y = inv.pos_y + inv.border
        
        time_ms = pygame.time.get_ticks()
        pulse = (math.sin(time_ms * 0.005) + 1) / 2
        alpha = int(80 + 100 * pulse)
        
        glow = pygame.Surface((inv.slot_size + 16, inv.slot_size + 16), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*cfg.INV_HOTBAR_GLOW_COLOR[:3], alpha), glow.get_rect(), border_radius=10)
        screen.blit(glow, (active_rect_x - 8, active_rect_y - 8))
        
        pygame.draw.rect(
            screen, cfg.INV_HOTBAR_ACTIVE_SLOT_BORDER_COLOR, 
            (active_rect_x, active_rect_y, inv.slot_size, inv.slot_size), 
            width=cfg.INV_HOTBAR_ACTIVE_SLOT_BORDER_WIDTH, border_radius=cfg.INV_HOTBAR_ACTIVE_SLOT_BORDER_RADIUS
        )

    def draw_split_popup(self, screen, popup):
        draw_panel_with_shadow(
            screen, popup.bg_rect, 
            bg_color=cfg.INV_SPLIT_POPUP_BG_COLOR, border_color=cfg.INV_SPLIT_POPUP_BORDER_COLOR, 
            border_width=cfg.INV_SPLIT_POPUP_BORDER_WIDTH, border_radius=cfg.INV_SPLIT_POPUP_BORDER_RADIUS, 
            shadow_offset=cfg.INV_SPLIT_POPUP_SHADOW_OFFSET
        )
        font = cfg.INV_nums_font
        text = font.render(f"Split: {popup.split_amount}", True, cfg.INV_SPLIT_POPUP_TEXT_COLOR)
        screen.blit(text, (popup.x + 15, popup.y + 10))

        popup.slider.draw(screen)
        popup.confirm_btn.draw(screen)

    def _load_portrait_surface(self, character):
        sprite_set = getattr(character, "sprite_set", None)
        if not sprite_set: return None
        cached = self._portrait_cache.get(sprite_set)
        if cached: return cached
        try: portrait = pygame.image.load(f"assets/characters/{sprite_set}/PortraitAndShowcase/Portrait.png").convert_alpha()
        except FileNotFoundError: return None
        self._portrait_cache[sprite_set] = portrait
        return portrait

    def _crop_face_from_frame(self, frame):
        face_rect = pygame.Rect(0, 0, frame.get_width(), max(1, int(frame.get_height() * 0.4)))
        return frame.subsurface(face_rect).copy()

    def _scale_to_fit(self, surface, target_rect):
        if surface.get_width() == 0 or surface.get_height() == 0: return surface
        scale = min(target_rect.width / surface.get_width(), target_rect.height / surface.get_height())
        return pygame.transform.smoothscale(surface, (max(1, int(surface.get_width() * scale)), max(1, int(surface.get_height() * scale))))
    
    def _draw_ornate_rec_button(self, screen, button):
        scale = cfg.ui_scale()
        rect = button.rect
        cx, cy = rect.center
        pulse = (math.sin(pygame.time.get_ticks() * 0.004) + 1) / 2

        # Radiant golden aura
        glow_size = int(rect.width * 2.2)
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_alpha = int(50 + pulse * 40)
        for r in range(glow_size // 2, 0, -1):
            a = int(glow_alpha * (1.0 - r / (glow_size // 2)))
            if a > 0:
                pygame.draw.circle(glow_surf, (212, 175, 55, a), (glow_size // 2, glow_size // 2), r)
        screen.blit(glow_surf, (cx - glow_size // 2, cy - glow_size // 2))

        # Outer ornate frame - triple gold
        pad = int(5 * scale)
        frame_rect = pygame.Rect(rect.x - pad, rect.y - pad, rect.width + pad * 2, rect.height + pad * 2)
        gold = (212, 175, 55)
        gold_light = (240, 210, 100)
        gold_dark = (150, 120, 50)
        for fi in range(3):
            frect = pygame.Rect(frame_rect.x - fi, frame_rect.y - fi,
                                frame_rect.width + fi * 2, frame_rect.height + fi * 2)
            fc = [gold_light, gold, gold_dark][fi]
            pygame.draw.rect(screen, fc, frect, width=max(1, int(2 * scale - fi * 0.5)),
                             border_radius=int(7 * scale - fi * 2))

        # Corner gems
        gem_size = max(1, int(3 * scale + pulse))
        gem_colors = [(220, 40, 40), (40, 70, 220), (40, 200, 40), (220, 180, 40)]
        for gi, (gx, gy) in enumerate([(frame_rect.x, frame_rect.y), (frame_rect.right, frame_rect.y),
                                        (frame_rect.x, frame_rect.bottom), (frame_rect.right, frame_rect.bottom)]):
            gc = gem_colors[gi]
            lighter = tuple(min(255, c + 70) for c in gc)
            darker = tuple(max(0, c - 40) for c in gc)
            pts_top = [(gx, gy - gem_size), (gx - gem_size, gy), (gx + gem_size, gy)]
            pts_bot = [(gx - gem_size, gy), (gx + gem_size, gy), (gx, gy + gem_size)]
            pygame.draw.polygon(screen, lighter, pts_top)
            pygame.draw.polygon(screen, darker, pts_bot)

        # Button background - dark leather
        pygame.draw.rect(screen, (50, 30, 15), rect, border_radius=int(6 * scale))

        # Draw majestic book icon inside button
        book_cx = cx
        book_cy = cy
        bw = int(rect.width * 0.55)
        bh = int(rect.height * 0.6)

        # Book shadow
        shadow_rect = pygame.Rect(book_cx - bw // 2 + int(2 * scale), book_cy - bh // 2 + int(2 * scale), bw, bh)
        pygame.draw.rect(screen, (0, 0, 0, 80), shadow_rect, border_radius=int(3 * scale))

        # Book cover
        cover_rect = pygame.Rect(book_cx - bw // 2, book_cy - bh // 2, bw, bh)
        pygame.draw.rect(screen, (80, 20, 10), cover_rect, border_radius=int(3 * scale))
        pygame.draw.rect(screen, gold, cover_rect, width=max(1, int(1.5 * scale)), border_radius=int(3 * scale))

        # Book spine
        spine_w = max(2, int(bw * 0.18))
        spine_rect = pygame.Rect(book_cx - spine_w // 2, cover_rect.y, spine_w, bh)
        pygame.draw.rect(screen, gold_dark, spine_rect, border_radius=int(1 * scale))

        # Pages (visible on sides)
        page_color = (250, 240, 215)
        page_margin = max(1, int(bw * 0.08))
        left_page = pygame.Rect(cover_rect.x + page_margin, cover_rect.y + int(bh * 0.1),
                                spine_rect.x - cover_rect.x - page_margin, int(bh * 0.8))
        right_page = pygame.Rect(spine_rect.right, cover_rect.y + int(bh * 0.1),
                                 cover_rect.right - spine_rect.right - page_margin, int(bh * 0.8))
        pygame.draw.rect(screen, page_color, left_page)
        pygame.draw.rect(screen, page_color, right_page)

        # Gold accent line on cover
        accent_y = cover_rect.y + int(bh * 0.35)
        pygame.draw.line(screen, gold, (cover_rect.x + int(bw * 0.15), accent_y),
                         (cover_rect.right - int(bw * 0.15), accent_y), max(1, int(1 * scale)))

        # Small gem on cover
        gem_cx = book_cx
        gem_cy = cover_rect.y + int(bh * 0.55)
        gem_s = max(1, int(2.5 * scale))
        gcol = (220, 40, 40)
        gl = tuple(min(255, c + 70) for c in gcol)
        gd = tuple(max(0, c - 40) for c in gcol)
        pygame.draw.polygon(screen, gl, [(gem_cx, gem_cy - gem_s), (gem_cx - gem_s, gem_cy), (gem_cx + gem_s, gem_cy)])
        pygame.draw.polygon(screen, gd, [(gem_cx - gem_s, gem_cy), (gem_cx + gem_s, gem_cy), (gem_cx, gem_cy + gem_s)])

        # Golden sparkle dots around the button
        for i in range(4):
            angle = i * math.pi / 2 + pulse * 0.5
            dist = rect.width * 0.65
            sx = cx + int(math.cos(angle) * dist)
            sy = cy + int(math.sin(angle) * dist)
            dot_s = max(1, int(1.5 * scale + pulse * 0.5))
            pygame.draw.circle(screen, gold_light, (sx, sy), dot_s)

    def draw_crafting_system(self, screen, crafting):
        self.draw_base_inventory(screen, crafting)

        self._draw_ornate_rec_button(screen, crafting.book_button)

        scale = cfg.ui_scale()
        
        grid_size = (crafting.slot_size + crafting.border) * 3
        arrow_center_x = crafting.pos_x + (grid_size // 2)
        
        arrow_start_y = crafting.pos_y + grid_size + int(2 * scale)
        
        shaft_w = int(10 * scale)
        shaft_h = int(4 * scale)
        head_w = int(24 * scale)
        head_h = int(8 * scale)
        
        gold_color = (212, 175, 55)
        pygame.draw.polygon(screen, gold_color, [
            (arrow_center_x - shaft_w//2, arrow_start_y),                   
            (arrow_center_x + shaft_w//2, arrow_start_y),                   
            (arrow_center_x + shaft_w//2, arrow_start_y + shaft_h),         
            (arrow_center_x + head_w//2, arrow_start_y + shaft_h),          
            (arrow_center_x, arrow_start_y + shaft_h + head_h),             
            (arrow_center_x - head_w//2, arrow_start_y + shaft_h),          
            (arrow_center_x - shaft_w//2, arrow_start_y + shaft_h)          
        ])
        pygame.draw.polygon(screen, (160, 130, 60), [
            (arrow_center_x - shaft_w//2, arrow_start_y),
            (arrow_center_x + shaft_w//2, arrow_start_y),
            (arrow_center_x + shaft_w//2, arrow_start_y + shaft_h),
            (arrow_center_x - shaft_w//2, arrow_start_y + shaft_h)
        ], 1)

        out_rect = pygame.Rect(crafting.output_pos_x, crafting.output_pos_y, crafting.slot_size, crafting.slot_size)
        pygame.draw.rect(screen, self.slot_bg_color, out_rect, border_radius=cfg.INV_SLOT_BORDER_RADIUS)
        pygame.draw.rect(screen, self.slot_inner_shadow, out_rect.inflate(-4, -4), border_radius=cfg.INV_SLOT_INNER_BORDER_RADIUS)
        pygame.draw.rect(screen, (0, 255, 100) if crafting.output_slot else self.slot_border_color, out_rect, width=2, border_radius=cfg.INV_SLOT_BORDER_RADIUS)

        if crafting.output_slot:
            item, count = crafting.output_slot
            padding = cfg.INV_SLOT_PADDING
            item_size = crafting.slot_size - padding * 2
            screen.blit(item.resize(item_size), (out_rect.x + padding, out_rect.y + padding))
            
            if count > 1:
                font_obj = cfg.INV_nums_font
                text_surf = font_obj.render(str(count), True, cfg.INV_ITEM_TEXT_COLOR)
                screen.blit(text_surf, (out_rect.right - text_surf.get_width() - 4, out_rect.bottom - text_surf.get_height() - 2))
