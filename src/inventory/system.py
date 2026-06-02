import math
import pygame
from typing import TYPE_CHECKING
import copy

from src.core.logger import logger
import src.config as cfg
from src.ui.widgets import Tooltip, Slider, Button
from src.items.items import Consumable

if TYPE_CHECKING:
    from src.app import App


def draw_panel_with_shadow(screen, rect, bg_color, border_color, border_width=2, border_radius=15, shadow_offset=8):

    shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 120), shadow.get_rect(), border_radius=border_radius)
    screen.blit(shadow, (rect.x + shadow_offset, rect.y + shadow_offset))
    
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, bg_color, panel.get_rect(), border_radius=border_radius)
    pygame.draw.rect(panel, border_color, panel.get_rect(), width=border_width, border_radius=border_radius)
    screen.blit(panel, rect.topleft)


class Inventory:
    def __init__(self, columns, rows, items, slot_size, pos_x, pos_y, slot_border, slot_color, slot_border_color):
        self.columns: int = columns
        self.rows: int = rows
        if not items:
            self.items: list = [[None for _ in range(self.rows)] for _ in range(self.columns)]
        else:
            self.items: list = items
        self.slot_size: int = slot_size
        self.pos_x: int = pos_x
        self.pos_y: int = pos_y
        self.border: int = slot_border
        
        self.slot_bg_color = (22, 26, 32, 255)       
        self.slot_inner_shadow = (10, 12, 16, 255)   
        self.slot_border_color = (55, 65, 80, 255)   
        self.hover_border = (230, 185, 60)           
        self.hover_fill = (230, 185, 60, 25)         
        
        self.selected_item = None

    def draw(self, screen):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        for n in range(self.columns):
            for m in range(self.rows):
                rect = pygame.Rect(
                    self.pos_x + (self.slot_size + self.border) * n + self.border,
                    self.pos_y + (self.slot_size + self.border) * m + self.border,
                    self.slot_size,
                    self.slot_size
                )
                
                pygame.draw.rect(screen, self.slot_bg_color, rect, border_radius=6)
                inner_rect = rect.inflate(-4, -4)
                pygame.draw.rect(screen, self.slot_inner_shadow, inner_rect, border_radius=4)
                
                is_hovered = rect.collidepoint(mouse_x, mouse_y) and not getattr(self, 'is_hidden', False)
                
                if is_hovered:
                    hover_surf = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
                    pygame.draw.rect(hover_surf, self.hover_fill, hover_surf.get_rect(), border_radius=6)
                    screen.blit(hover_surf, rect.topleft)
                    pygame.draw.rect(screen, self.hover_border, rect, width=2, border_radius=6)
                else:
                    pygame.draw.rect(screen, self.slot_border_color, rect, width=2, border_radius=6)
                if self.items[n][m]:
                    item, count = self.items[n][m]

                    if count <= 0:
                        self.items[n][m] = None
                        continue

                    padding = 8
                    item_size = self.slot_size - padding * 2
                    
                    shadow_surf = pygame.Surface((item_size, item_size), pygame.SRCALPHA)
                    pygame.draw.circle(shadow_surf, (0, 0, 0, 120), (item_size//2, item_size//2), item_size//2 - 2)
                    screen.blit(shadow_surf, (rect.x + padding + 2, rect.y + padding + 4))
                    
                    screen.blit(item.resize(item_size), (rect.x + padding, rect.y + padding))
                    
                    if count > 1:
                        font_obj = cfg.INV_nums_font
                        text_str = str(count)
                        
                        shadow1 = font_obj.render(text_str, True, (0, 0, 0))
                        shadow2 = font_obj.render(text_str, True, (0, 0, 0))
                        text_surf = font_obj.render(text_str, True, (245, 245, 250))
                        
                        text_x = rect.right - text_surf.get_width() - 4
                        text_y = rect.bottom - text_surf.get_height() - 2
                        
                        screen.blit(shadow1, (text_x + 2, text_y + 2))
                        screen.blit(shadow2, (text_x + 1, text_y + 1))
                        screen.blit(text_surf, (text_x, text_y))

    def inventory_interactions(self, event, manager):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()
        x = (mouse_x - self.pos_x) // (self.slot_size + self.border)
        y = (mouse_y - self.pos_y) // (self.slot_size + self.border)
        
        if 0 <= x < self.columns and 0 <= y < self.rows:
            slot = self.items[x][y]
            if event.button == 1:
                if manager.selected_item:
                    if slot:
                        if slot[0].id == manager.selected_item[0].id:
                            slot[1] += manager.selected_item[1]
                            manager.selected_item = None
                        else:
                            self.items[x][y], manager.selected_item = manager.selected_item, self.items[x][y]
                    else:
                        self.items[x][y] = manager.selected_item
                        manager.selected_item = None
                else:
                    if slot:
                        manager.selected_item = slot
                        self.items[x][y] = None

            elif event.button == 2:
                if slot and not manager.selected_item and slot[1] > 1:
                    rect = pygame.Rect(
                        self.pos_x + (self.slot_size + self.border) * x + self.border,
                        self.pos_y + (self.slot_size + self.border) * y + self.border,
                        self.slot_size, self.slot_size
                    )
                    manager.active_split_popup = Split_popup(manager, slot, rect)
            elif event.button == 3 and slot and not manager.selected_item:
                item, count = slot
                if isinstance(item, Consumable):
                    game_state = manager.app.manager.states.get("gameplay")
                    if game_state:
                        if item.use(game_state.character):
                            slot[1] -= 1
                            if slot[1] <= 0:
                                self.items[x][y] = None             

    def get_slot_under_mouse(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()

        total_width = (self.slot_size + self.border) * self.columns
        total_height = (self.slot_size + self.border) * self.rows
        if not (self.pos_x <= mouse_x <= self.pos_x + total_width and 
                self.pos_y <= mouse_y <= self.pos_y + total_height):
            return None

        col = (mouse_x - self.pos_x) // (self.slot_size + self.border)
        row = (mouse_y - self.pos_y) // (self.slot_size + self.border)

        if 0 <= col < self.columns and 0 <= row < self.rows:
            slot_data = self.items[col][row]
            rect = pygame.Rect(
                self.pos_x + (self.slot_size + self.border) * col + self.border,
                self.pos_y + (self.slot_size + self.border) * row + self.border,
                self.slot_size, self.slot_size
            )
            if slot_data:
                item, count = slot_data
                return rect, item
        return None


class Inventory_slider(Slider):
    def __init__(self, x, y, width, max_qty, action_callback):
        self.max_qty = max_qty
        self.external_callback = action_callback
        super().__init__(
            x=x, y=y, height=18, track_thickness=6, 
            track_colour=(30, 35, 45), knob_colour=(230, 185, 60),
            knob_width=14, knob_height=18, 
            track_length=width, value=0.0, action=self._convert_to_int
        )

    def _convert_to_int(self, float_value):
        result = 1 if self.max_qty <= 1 else 1 + int(float_value * (self.max_qty - 1))
        if self.external_callback:
            self.external_callback(result)


class Split_popup:
    def __init__(self, manager, slot_ref, rect_pos):
        self.manager = manager
        self.slot_ref = slot_ref
        self.item_obj, self.total_count = slot_ref

        scale = cfg.ui_scale()
        self.width = max(40, int(180 * scale))
        self.height = max(20, int(95 * scale))
        self.x = rect_pos.right + int(10 * scale)
        self.y = rect_pos.y

        if self.x + self.width > cfg.SCREEN_WIDTH:
            self.x = rect_pos.left - self.width - 10
            
        self.bg_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.split_amount = 1 

        self.slider = Inventory_slider(
            x=self.x + int(15 * scale), y=self.y + int(40 * scale),
            width=self.width - int(30 * scale), max_qty=self.total_count,
            action_callback=self.update_count 
        )

        self.confirm_btn = Button(
            rect=pygame.Rect(self.x + int(40 * scale), self.y + int(65 * scale), max(20,int(100 * scale)), max(8,int(22 * scale))),
            text="Confirm", color=(40, 80, 50), hover_color=(60, 110, 70),  
            font=cfg.INV_nums_font, font_color=(230, 240, 230),
            corner_width=max(2,int(6 * scale)), on_click=self.confirm       
        )

    def update_count(self, int_val):
        self.split_amount = int_val

    def confirm(self):
        if self.split_amount < self.total_count:
            self.manager.selected_item = [self.item_obj, self.split_amount]
            self.slot_ref[1] -= self.split_amount
        else:
            self.manager.selected_item = [self.item_obj, self.total_count]
            self.slot_ref[1] = 0 
        self.manager.active_split_popup = None

    def handle_event(self, event):
        self.slider.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.confirm_btn.rect.collidepoint(event.pos):
                self.confirm_btn.on_click()
            elif not self.bg_rect.collidepoint(event.pos):
                self.manager.active_split_popup = None
                
    def draw(self, screen):
        draw_panel_with_shadow(
            screen, self.bg_rect, 
            bg_color=(25, 30, 38, 245), 
            border_color=(70, 80, 95, 255), 
            border_width=2, border_radius=10, shadow_offset=6
        )

        font = cfg.INV_nums_font
        text = font.render(f"Split: {self.split_amount}", True, (240, 240, 245))
        screen.blit(text, (self.x + 15, self.y + 10))

        self.slider.draw(screen)
        self.confirm_btn.draw(screen)


class ShopInventory(Inventory):
    def __init__(self, app, items_list):
        self.app = app
        rows, columns = 4, 4
        items_grid = [[None for _ in range(rows)] for _ in range(columns)]
        
        for i, item in enumerate(items_list):
            x, y = i % columns, i // columns
            if y < rows: items_grid[x][y] = [item, 1]
        
        super().__init__(
            columns, rows, items_grid, 
            cfg.BASE_INV_slot_size, 0, 0, 
            cfg.BASE_INV_border, cfg.BASE_INV_slot_color, cfg.BASE_INV_border_color
        )
        scale = cfg.ui_scale()
        btn_w, btn_h = max(80, int(140 * scale)), max(28, int(38 * scale))
        self.close_button = Button(
            rect=pygame.Rect(0, 0, btn_w, btn_h),
            text=_("LEAVE SHOP"), color=(140, 45, 45), hover_color=(180, 60, 60),
            font=cfg.INV_nums_font, font_color=(255, 240, 240),
            corner_width=max(2, int(8 * scale)), on_click=self._close_shop
        )

    def draw(self, screen):
        bg_rect = pygame.Rect(
            self.pos_x - 20, self.pos_y - 20,
            (self.slot_size + self.border) * self.columns + self.border + 40,
            (self.slot_size + self.border) * self.rows + self.border + 40
        )
        
        draw_panel_with_shadow(
            screen, bg_rect, 
            bg_color=(35, 25, 30, 245), 
            border_color=(100, 70, 80, 255), 
            border_width=3, border_radius=16, shadow_offset=12
        )
        
        title_font = cfg.tooltip_font_CREDITS
        title_surf = title_font.render("MERCHANT", True, (230, 185, 60))
        screen.blit(title_surf, (bg_rect.centerx - title_surf.get_width()//2, bg_rect.y - 10))
        
        super().draw(screen)
        
        for x in range(self.columns):
            for y in range(self.rows):
                if self.items[x][y]:
                    price = getattr(self.items[x][y][0], 'price', 0)
                    font = cfg.INV_nums_font
                    text = font.render(f"{price}G", True, (255, 220, 80))
                    shadow = font.render(f"{price}G", True, (0, 0, 0))
                    
                    rect_x = self.pos_x + (self.slot_size + self.border) * x + self.border
                    rect_y = self.pos_y + (self.slot_size + self.border) * y + self.border
                    
                    price_bg = pygame.Surface((text.get_width() + 6, text.get_height() + 2), pygame.SRCALPHA)
                    pygame.draw.rect(price_bg, (0, 0, 0, 150), price_bg.get_rect(), border_radius=4)
                    
                    bg_pos = (rect_x + self.slot_size//2 - price_bg.get_width()//2, rect_y + self.slot_size - 18)
                    screen.blit(price_bg, bg_pos)
                    screen.blit(shadow, (bg_pos[0] + 4, bg_pos[1] + 2))
                    screen.blit(text, (bg_pos[0] + 3, bg_pos[1] + 1))

        try:
            self.close_button.rect.topleft = (bg_rect.right - self.close_button.rect.width - 16, bg_rect.bottom - self.close_button.rect.height - 16)
            self.close_button._update_text_surface()
            self.close_button.draw(screen)
        except Exception:
            pass

    def inventory_interactions(self, event, manager):
        if event.type != pygame.MOUSEBUTTONDOWN: return
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        if event.button == 1 and getattr(self, 'close_button', None):
            if self.close_button.rect.collidepoint((mouse_x, mouse_y)):
                try: self.close_button.on_click()
                except Exception: pass
                return
        
        total_width = (self.slot_size + self.border) * self.columns
        total_height = (self.slot_size + self.border) * self.rows
        if not (self.pos_x <= mouse_x <= self.pos_x + total_width and self.pos_y <= mouse_y <= self.pos_y + total_height): return

        x, y = (mouse_x - self.pos_x) // (self.slot_size + self.border), (mouse_y - self.pos_y) // (self.slot_size + self.border)
        
        if 0 <= x < self.columns and 0 <= y < self.rows:
            slot = self.items[x][y]
            if event.button == 1: 
                if manager.selected_item:
                    item, count = manager.selected_item
                    self.app.money += int(getattr(item, 'price', 0) * 1) * count                
                    manager.selected_item = None
                else:
                    if slot:
                        shop_item = slot[0]
                        buy_price = getattr(shop_item, 'price', 0)
                        if self.app.money >= buy_price:
                            self.app.money -= buy_price
                            manager.selected_item = [copy.copy(shop_item), 1]

    def _close_shop(self):
        try:
            game_state = self.app.manager.states.get("gameplay")
            if game_state: self.app.INV_manager.toggle_trade(game_state.MAIN_player_inv, self)
            else:
                if self in self.app.INV_manager.active_inventories:
                    self.app.INV_manager.remove_active_inventory(self)
                    if self.app.INV_manager.current_shop_inv is self: self.app.INV_manager.current_shop_inv = None
        except Exception: pass


class MAIN_player_inventory(Inventory):
    def __init__(self, app:"App"):
        self.app = app
        self._portrait_cache = {}
        super().__init__(
            cfg.MAIN_INV_columns, cfg.MAIN_INV_rows, app.MAIN_INV_items,
            cfg.BASE_INV_slot_size, cfg.MAIN_INV_pos_x, cfg.MAIN_INV_pos_y,
            cfg.BASE_INV_border, cfg.BASE_INV_slot_color, cfg.BASE_INV_border_color
        )
        scale = cfg.ui_scale()
        btn_w, btn_h = max(20, int(160 * scale)), max(8, int(36 * scale))
        
        self.open_skillbar_btn = Button(
            rect=pygame.Rect(0, 0, btn_w, btn_h),
            text=_("SKILLS & MAGIC"), color=(45, 60, 80), hover_color=(65, 85, 110),
            font=cfg.tooltip_font_CREDITS, font_color=(230, 240, 255),
            corner_width=max(2, int(8 * scale)), on_click=None
        )
        self.open_skilltree_btn = Button(
            rect=pygame.Rect(0, 0, btn_w, btn_h),
            text=_("TALENT TREE"), color=(55, 45, 75), hover_color=(80, 65, 105),
            font=cfg.tooltip_font_CREDITS, font_color=(240, 230, 255),
            corner_width=max(2, int(8 * scale)), on_click=None
        )

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

    def draw(self, screen):
        bg_rect = pygame.Rect(
            self.pos_x - 24, self.pos_y - 340,
            (self.slot_size + self.border) * self.columns + self.border + 48,
            (self.slot_size + self.border) * self.rows + self.border + 364
        )
        
        draw_panel_with_shadow(
            screen, bg_rect, 
            bg_color=(18, 22, 28, 245), 
            border_color=(70, 80, 95, 255), 
            border_width=3, border_radius=20, shadow_offset=15
        )
            
        preview_offset_x = 389
        preview_x = self.pos_x + preview_offset_x
        
        portrait_bg = pygame.Rect(preview_x, self.pos_y - 310, 190, 275)
        pygame.draw.rect(screen, (10, 12, 16), portrait_bg, border_radius=12)
        
        game_state = self.app.manager.states.get("gameplay")
        if game_state and hasattr(game_state, "character"):
            character = game_state.character
            portrait = self._load_portrait_surface(character) or self._crop_face_from_frame(character.image)
            scaled_img = self._scale_to_fit(portrait, portrait_bg)
            screen.blit(scaled_img, scaled_img.get_rect(center=portrait_bg.center))

        pygame.draw.rect(screen, (100, 90, 60), portrait_bg, width=3, border_radius=12)
        pygame.draw.rect(screen, (230, 185, 60), portrait_bg.inflate(2, 2), width=1, border_radius=12)

        money_panel = pygame.Rect(preview_x, self.pos_y - 25, 190, 36)
        pygame.draw.rect(screen, (25, 30, 35), money_panel, border_radius=8)
        pygame.draw.rect(screen, (55, 65, 75), money_panel, width=2, border_radius=8)
        
        money_text = f"{self.app.money} G"
        text_surf = cfg.tooltip_font_CREDITS.render(money_text, True, (255, 215, 0))
        shadow_surf = cfg.tooltip_font_CREDITS.render(money_text, True, (0, 0, 0))
        
        text_pos_x = money_panel.centerx - text_surf.get_width() // 2
        text_pos_y = money_panel.centery - text_surf.get_height() // 2
        screen.blit(shadow_surf, (text_pos_x + 1, text_pos_y + 1))
        screen.blit(text_surf, (text_pos_x, text_pos_y))

        if not getattr(self.app.INV_manager, 'current_shop_inv', None):
            scale = cfg.ui_scale()
            gap = max(6, int(10 * scale))
            stack_height = self.open_skillbar_btn.rect.height + self.open_skilltree_btn.rect.height + gap
            btn_x = preview_x + (190 - self.open_skillbar_btn.rect.width) // 2
            btn_y = self.pos_y - stack_height - max(8, int(12 * scale)) - 25

            self.open_skillbar_btn.rect.topleft = (btn_x, btn_y)
            self.open_skilltree_btn.rect.topleft = (btn_x, btn_y + self.open_skillbar_btn.rect.height + gap)
            
            try: self.open_skillbar_btn._update_text_surface()
            except Exception: pass
            try: self.open_skilltree_btn._update_text_surface()
            except Exception: pass
            
            self.open_skillbar_btn.draw(screen)
            self.open_skilltree_btn.draw(screen)

        return super().draw(screen)

    def inventory_interactions(self, event, manager):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not getattr(self.app.INV_manager, 'current_shop_inv', None):
                mouse_pos = event.pos
                if hasattr(self, 'open_skilltree_btn') and self.open_skilltree_btn.rect.collidepoint(mouse_pos):
                    try: self.app.manager.set_state("skill_tree")
                    except Exception: pass
                    return
                if hasattr(self, 'open_skillbar_btn') and self.open_skillbar_btn.rect.collidepoint(mouse_pos):
                    try: self.app.manager.set_state("skillbar")
                    except Exception: pass
                    return
        return super().inventory_interactions(event, manager)
    

class MAIN_player_inventory_equipment(Inventory):
    def __init__(self,app :"App"):
        super().__init__(
            cfg.MAIN_INV_equipment_columns, cfg.MAIN_INV_equipment_rows, None,
            cfg.BASE_INV_slot_size, cfg.MAIN_INV_equipment_pos_x, cfg.MAIN_INV_equipment_pos_y,
            cfg.BASE_INV_border, cfg.BASE_INV_slot_color, cfg.BASE_INV_border_color
        )


class MAIN_player_hotbar(Inventory):
    def __init__(self, app: "App"):
        self.app = app
        columns = getattr(cfg, 'HOTBAR_columns', 10)
        rows, scale = 1, 0.8
        slot_size = int(cfg.BASE_INV_slot_size * scale)
        
        if not hasattr(app, 'MAIN_HOTBAR_items'):
            app.MAIN_HOTBAR_items = [[None for _ in range(rows)] for _ in range(columns)]

        super().__init__(
            columns, rows, app.MAIN_HOTBAR_items,
            slot_size, 0, 0, cfg.BASE_INV_border,
            cfg.BASE_INV_slot_color, cfg.BASE_INV_border_color
        )
        self.active_slot_index = 0
        self.update_position()

    def update_position(self):
        total_width = (self.slot_size + self.border) * self.columns + self.border
        self.pos_x = (cfg.SCREEN_WIDTH - total_width) // 2
        self.pos_y = cfg.SCREEN_HEIGHT - self.slot_size - 25

    def get_slot_under_mouse(self):
        self.update_position()
        return super().get_slot_under_mouse()

    def inventory_interactions(self, event, manager):
        self.update_position()
        super().inventory_interactions(event, manager)

    def scroll_active_slot(self, y_direction):
        self.active_slot_index = (self.active_slot_index - y_direction) % self.columns

    def use_active_slot(self):
        self._use_hotbar_item(self.active_slot_index)

    def handle_hotkeys(self, event):
        if event.type != pygame.KEYDOWN: return
        key_map = {
            pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3, pygame.K_5: 4, 
            pygame.K_6: 5, pygame.K_7: 6, pygame.K_8: 7, pygame.K_9: 8, pygame.K_0: 9
        }
        if event.key in key_map and key_map[event.key] < self.columns:
            self.active_slot_index = key_map[event.key]
            self._use_hotbar_item(self.active_slot_index)
                
    def _use_hotbar_item(self, col):
        slot = self.items[col][0]
        if slot and isinstance(slot[0], Consumable):
            game_state = self.app.manager.states.get("gameplay")
            if game_state and slot[0].use(game_state.character):
                slot[1] -= 1
                if slot[1] <= 0: self.items[col][0] = None

    def draw(self, screen):
        self.update_position()
        
        bg_rect = pygame.Rect(
            self.pos_x - 16, self.pos_y - 16,
            (self.slot_size + self.border) * self.columns + self.border + 32,
            (self.slot_size + self.border) * self.rows + self.border + 32
        )
        
        draw_panel_with_shadow(
            screen, bg_rect, 
            bg_color=(20, 24, 30, 230), 
            border_color=(60, 70, 85, 255), 
            border_width=2, border_radius=20, shadow_offset=8
        )
        
        super().draw(screen)

        active_rect_x = self.pos_x + (self.slot_size + self.border) * self.active_slot_index + self.border
        active_rect_y = self.pos_y + self.border
        
        time_ms = pygame.time.get_ticks()
        pulse = (math.sin(time_ms * 0.005) + 1) / 2
        alpha = int(80 + 100 * pulse)
        
        glow = pygame.Surface((self.slot_size + 16, self.slot_size + 16), pygame.SRCALPHA)
        pygame.draw.rect(glow, (230, 185, 60, alpha), glow.get_rect(), border_radius=10)
        screen.blit(glow, (active_rect_x - 8, active_rect_y - 8))
        
        pygame.draw.rect(
            screen, (255, 215, 0), 
            (active_rect_x, active_rect_y, self.slot_size, self.slot_size), 
            width=3, border_radius=6
        )


class INVENTORY_manager:
    def __init__(self, app):
        self.app = app
        self.selected_item = None
        self.active_split_popup = None
        self.active_inventories: list[Inventory|None] = []
        self.player_inventory_opened: bool = False
        self.current_shop_inv: Inventory|None = None
        self.hotbar = None
        
        self.overlay_alpha = 0
        self.target_alpha = 0
        
        self.inventory_tooltip = Tooltip(
            cfg.inventory_tooltip_rect, "", cfg.inventory_tooltip_bg,
            cfg.inventory_tooltip_border, cfg.INV_nums_font,
            cfg.inventory_tooltip_font_color, cfg.tooltip_appear, cfg.tooltip_padding
        )

    def add_active_inventory(self, inventory):
        if inventory not in self.active_inventories: self.active_inventories.append(inventory)

    def remove_active_inventory(self, inventory):
        if inventory in self.active_inventories: self.active_inventories.remove(inventory)
    
    def draw(self, screen):
        self.target_alpha = 160 if self.player_inventory_opened else 0
        if self.overlay_alpha != self.target_alpha:
            self.overlay_alpha += (self.target_alpha - self.overlay_alpha) * 0.15
            if abs(self.target_alpha - self.overlay_alpha) < 2: self.overlay_alpha = self.target_alpha
                
        if self.overlay_alpha > 0:
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((5, 8, 12, int(self.overlay_alpha)))
            screen.blit(overlay, (0, 0))

        for inv in self.active_inventories:
            inv.draw(screen)
            
        if self.selected_item:
            mx, my = pygame.mouse.get_pos()
            item, count = self.selected_item
            
            time_ms = pygame.time.get_ticks()
            scale_offset = math.sin(time_ms * 0.008) * 0.08
            current_size = int(cfg.BASE_INV_slot_size * (1.05 + scale_offset))
            
            # М'яка тінь
            shadow = pygame.Surface((current_size, current_size), pygame.SRCALPHA)
            pygame.draw.circle(shadow, (0, 0, 0, 140), (current_size//2, current_size//2), current_size//2 - 4)
            screen.blit(shadow, (mx - current_size//2 + 12, my - current_size//2 + 18))
            
            screen.blit(item.resize(current_size), item.resize(current_size).get_rect(center=(mx, my)))
            
            if count > 1:
                font = cfg.INV_nums_font
                text_str = str(count)
                shadow_surf = font.render(text_str, True, (0, 0, 0))
                text_surf = font.render(text_str, True, (255, 255, 255))
                screen.blit(shadow_surf, (mx + 12, my + 12))
                screen.blit(text_surf, (mx + 10, my + 10))
        
        if not self.selected_item:
            found_item = False
            for inv in self.active_inventories:
                result = inv.get_slot_under_mouse()
                if result:
                    rect, item = result
                    self.inventory_tooltip.update_target(rect, item.get_tooltip_text())
                    found_item = True
                    break
            if not found_item: self.inventory_tooltip.update_target(pygame.Rect(-100,-100,0,0), "")
            self.inventory_tooltip.hover_update(pygame.mouse.get_pos())
            self.inventory_tooltip.draw(screen)
            
        if self.active_split_popup: self.active_split_popup.draw(screen)
    
    def handle_event(self, event):
        if self.active_split_popup:
            self.active_split_popup.handle_event(event)
            return 
        if self.hotbar: self.hotbar.handle_hotkeys(event)
        for inv in self.active_inventories: inv.inventory_interactions(event, self)

    def toggle_inventory(self, pl_inv, equip_inv):
        self.player_inventory_opened = not self.player_inventory_opened   
        if self.player_inventory_opened:
            self.add_active_inventory(pl_inv)
            self.add_active_inventory(equip_inv)
        else:
            self.remove_active_inventory(pl_inv)
            self.remove_active_inventory(equip_inv)
            if self.current_shop_inv:
                self.remove_active_inventory(self.current_shop_inv)
                self.current_shop_inv = None
                pl_inv.pos_x = cfg.MAIN_INV_pos_x

    def toggle_trade(self, pl_inv, shop_inv):
        if shop_inv in self.active_inventories:
            self.remove_active_inventory(shop_inv)
            self.remove_active_inventory(pl_inv)
            pl_inv.pos_x = cfg.MAIN_INV_pos_x
            self.player_inventory_opened = False
            if self.current_shop_inv is shop_inv: self.current_shop_inv = None
        else:
            self.player_inventory_opened = True 
            pl_inv.pos_x = cfg.SCREEN_WIDTH // 2 - 500 
            shop_inv.pos_x = cfg.SCREEN_WIDTH // 2 + 100
            shop_inv.pos_y = pl_inv.pos_y
            self.add_active_inventory(pl_inv)
            self.add_active_inventory(shop_inv)
            self.current_shop_inv = shop_inv
    
    def PLAYER_inventory_open(self,event: pygame.event.Event,pl_inv,equip_inv):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
            self.toggle_inventory(pl_inv, equip_inv)
        if self.player_inventory_opened and event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            self.handle_event(event)