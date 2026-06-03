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
        bg_rect = pygame.Rect(
            inv.pos_x - 20, inv.pos_y - 20,
            (inv.slot_size + inv.border) * inv.columns + inv.border + 40,
            (inv.slot_size + inv.border) * inv.rows + inv.border + 40
        )
        
        draw_panel_with_shadow(
            screen, bg_rect, bg_color=cfg.INV_SHOP_BG_COLOR, 
            border_color=cfg.INV_SHOP_BORDER_COLOR, border_width=cfg.INV_SHOP_BORDER_WIDTH, 
            border_radius=cfg.INV_SHOP_BORDER_RADIUS, shadow_offset=cfg.INV_SHOP_SHADOW_OFFSET
        )
        
        title_font = cfg.tooltip_font_CREDITS
        title_surf = title_font.render("MERCHANT", True, cfg.INV_SHOP_TITLE_COLOR)
        screen.blit(title_surf, (bg_rect.centerx - title_surf.get_width()//2, bg_rect.y - 10))
        
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
            inv.close_button.rect.topleft = (bg_rect.right - inv.close_button.rect.width - 16, bg_rect.bottom - inv.close_button.rect.height - 16)
            try: inv.close_button._update_text_surface()
            except Exception: pass
            inv.close_button.draw(screen)

    def draw_player_inventory(self, screen, inv: MAIN_player_inventory):
        bg_rect = pygame.Rect(
            inv.pos_x - 24, inv.pos_y - 340,
            (inv.slot_size + inv.border) * inv.columns + inv.border + 48,
            (inv.slot_size + inv.border) * inv.rows + inv.border + 364
        )
        
        draw_panel_with_shadow(
            screen, bg_rect, bg_color=cfg.INV_PLAYER_BG_COLOR, 
            border_color=cfg.INV_PLAYER_BORDER_COLOR, border_width=cfg.INV_PLAYER_BORDER_WIDTH, 
            border_radius=cfg.INV_PLAYER_BORDER_RADIUS, shadow_offset=cfg.INV_PLAYER_SHADOW_OFFSET
        )
            
        preview_offset_x = cfg.INV_PLAYER_PREVIEW_OFFSET_X
        preview_x = inv.pos_x + preview_offset_x
        
        portrait_bg = pygame.Rect(preview_x, inv.pos_y + cfg.INV_PLAYER_PREVIEW_Y_OFFSET, 
                                  cfg.INV_PLAYER_PREVIEW_WIDTH, cfg.INV_PLAYER_PREVIEW_HEIGHT)
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

        money_panel = pygame.Rect(preview_x, inv.pos_y + cfg.INV_PLAYER_MONEY_PANEL_Y_OFFSET, 
                                 cfg.INV_PLAYER_MONEY_PANEL_WIDTH, cfg.INV_PLAYER_MONEY_PANEL_HEIGHT)
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

        if not getattr(inv.app.INV_manager, 'current_shop_inv', None):
            scale = cfg.ui_scale()
            gap = max(cfg.INV_PLAYER_BTN_GAP_MIN, int(cfg.INV_PLAYER_BTN_GAP_SCALE * scale))
            stack_height = inv.open_skillbar_btn.rect.height + inv.open_skilltree_btn.rect.height + gap
            btn_x = preview_x + (cfg.INV_PLAYER_PREVIEW_WIDTH - inv.open_skillbar_btn.rect.width) // 2
            btn_y = inv.pos_y - stack_height - max(cfg.INV_PLAYER_BTN_SPACING_MIN, int(cfg.INV_PLAYER_BTN_SPACING_SCALE * scale)) - cfg.INV_PLAYER_BTN_TOP_OFFSET

            inv.open_skillbar_btn.rect.topleft = (btn_x, btn_y)
            inv.open_skilltree_btn.rect.topleft = (btn_x, btn_y + inv.open_skillbar_btn.rect.height + gap)
            
            try: inv.open_skillbar_btn._update_text_surface()
            except Exception: pass
            try: inv.open_skilltree_btn._update_text_surface()
            except Exception: pass
            
            inv.open_skillbar_btn.draw(screen)
            inv.open_skilltree_btn.draw(screen)

        self.draw_base_inventory(screen, inv)

    def draw_hotbar(self, screen, inv: MAIN_player_hotbar):
        inv.update_position()
        bg_rect = pygame.Rect(
            inv.pos_x - 16, inv.pos_y - 16,
            (inv.slot_size + inv.border) * inv.columns + inv.border + 32,
            (inv.slot_size + inv.border) * inv.rows + inv.border + 32
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
    
    def draw_crafting_system(self, screen, crafting):
        self.draw_base_inventory(screen, crafting)
        
        crafting.book_button.draw(screen)
        
        scale = cfg.ui_scale()
        
        grid_size = (crafting.slot_size + crafting.border) * 3
        arrow_center_x = crafting.pos_x + (grid_size // 2)
        
        arrow_start_y = crafting.pos_y + grid_size + int(2 * scale)
        
        shaft_w = int(10 * scale)
        shaft_h = int(4 * scale)
        head_w = int(24 * scale)
        head_h = int(8 * scale)
        
        pygame.draw.polygon(screen, (200, 200, 200), [
            (arrow_center_x - shaft_w//2, arrow_start_y),                   
            (arrow_center_x + shaft_w//2, arrow_start_y),                   
            (arrow_center_x + shaft_w//2, arrow_start_y + shaft_h),         
            (arrow_center_x + head_w//2, arrow_start_y + shaft_h),          
            (arrow_center_x, arrow_start_y + shaft_h + head_h),             
            (arrow_center_x - head_w//2, arrow_start_y + shaft_h),          
            (arrow_center_x - shaft_w//2, arrow_start_y + shaft_h)          
        ])

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
