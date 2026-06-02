import math
import pygame
import src.config as cfg
from src.ui.widgets import Tooltip, Button
from src.inventory.system import Inventory_slider, ShopInventory, MAIN_player_inventory, MAIN_player_hotbar
from src.inventory.inventory_renderer import InventoryRenderer

class Split_popup_model:
    """
    Manages the logic and state of the item split popup interface.

    This class handles the creation, positioning, and interaction for a popup 
    that allows players to split a stack of items using a slider.

    Attributes:
        manager (INVENTORY_manager):
            The inventory manager controlling this popup.
        slot_ref (list):
            A reference to the slot being split containing the item and its count.
        item_obj (Item):
            The item object that is being split.
        total_count (int):
            The total quantity of the item stack available to split.
        width (int):
            The calculated width of the popup window.
        height (int):
            The calculated height of the popup window.
        x (int):
            The x-coordinate position of the popup window.
        y (int):
            The y-coordinate position of the popup window.
        bg_rect (pygame.Rect):
            The background rectangle bounding box for the popup.
        split_amount (int):
            The current amount selected to be split.
        slider (Inventory_slider):
            The slider widget used to select the split amount.
        confirm_btn (Button):
            The button widget used to confirm the split operation.

    Methods:
        __init__(manager, slot_ref, rect_pos):
            Initialize the split popup model and its UI elements.
        update_count(int_val):
            Update the split amount based on the slider value.
        confirm():
            Execute the split operation and update inventory slots.
        handle_event(event):
            Process pygame events for the slider and confirmation button.
    """
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
            text="Confirm", color=cfg.INV_SPLIT_POPUP_BTN_COLOR, hover_color=cfg.INV_SPLIT_POPUP_BTN_HOVER_COLOR,  
            font=cfg.INV_nums_font, font_color=cfg.INV_SPLIT_POPUP_BTN_FONT_COLOR,
            corner_width=max(2,int(cfg.INV_SPLIT_POPUP_BTN_CORNER_WIDTH_SCALE * scale)), on_click=self.confirm       
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

class INVENTORY_manager:
    """
    Manages the overall inventory system, user interactions, and UI rendering.

    This class handles multiple inventory types, drag-and-drop mechanics, 
    tooltips, item splitting, and rendering of all inventory interfaces.

    Attributes:
        app (App):
            The main application reference.
        selected_item (list):
            The currently held item and its count during drag-and-drop.
        active_split_popup (Split_popup_model):
            The currently active split popup, if any.
        active_inventories (list):
            A list containing all currently opened inventory objects.
        player_inventory_opened (bool):
            Flag indicating whether the player's main inventory is open.
        current_shop_inv (ShopInventory):
            The currently active shop inventory instance.
        hotbar (MAIN_player_hotbar):
            The player's action hotbar instance.
        renderer (InventoryRenderer):
            The rendering engine used to draw the inventories.
        overlay_alpha (float):
            The current alpha transparency for the background overlay.
        target_alpha (float):
            The target alpha transparency for background overlay transitions.
        inventory_tooltip (Tooltip):
            The tooltip widget used to display item information on hover.

    Methods:
        __init__(app):
            Initialize the inventory manager and rendering components.
        add_active_inventory(inventory):
            Add an inventory instance to the active rendering list.
        remove_active_inventory(inventory):
            Remove an inventory instance from the active rendering list.
        draw(screen):
            Render active inventories, overlays, dragged items, and tooltips.
        handle_event(event):
            Process and distribute pygame events to active UI components.
        toggle_inventory(pl_inv, equip_inv):
            Open or close the player's main and equipment inventories.
        toggle_trade(pl_inv, shop_inv):
            Open or close the trading interface with a specified shop.
        PLAYER_inventory_open(event, pl_inv, equip_inv):
            Handle hotkey interactions for toggling the inventory screen.
    """
    def __init__(self, app):
        self.app = app
        self.selected_item = None
        self.active_split_popup = None
        self.active_inventories = []
        self.player_inventory_opened = False

        self.current_shop_inv = None
        self.hotbar = None
        
        from src.inventory.system import CraftingGrid
        self.crafting_system = CraftingGrid(app)
        
        self.renderer = InventoryRenderer()
        
        self.renderer = InventoryRenderer()
        
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
        self.target_alpha = cfg.INV_OVERLAY_ALPHA if self.player_inventory_opened else 0
        if self.overlay_alpha != self.target_alpha:
            self.overlay_alpha += (self.target_alpha - self.overlay_alpha) * cfg.INV_OVERLAY_ALPHA_LERP
            if abs(self.target_alpha - self.overlay_alpha) < 2: self.overlay_alpha = self.target_alpha
                
        if self.overlay_alpha > 0:
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((*cfg.INV_OVERLAY_COLOR, int(self.overlay_alpha)))
            screen.blit(overlay, (0, 0))

        for inv in self.active_inventories:
            if isinstance(inv, ShopInventory):
                self.renderer.draw_shop(screen, inv)
            elif isinstance(inv, MAIN_player_inventory):
                self.renderer.draw_player_inventory(screen, inv)
                
                from src.inventory.system import MAIN_player_inventory_equipment
                equip_inv = None
                for active_inv in self.active_inventories:
                    if isinstance(active_inv, MAIN_player_inventory_equipment):
                        equip_inv = active_inv
                        break
                
                if equip_inv:
                    scale = cfg.ui_scale()
                    craft_width = (self.crafting_system.slot_size + self.crafting_system.border) * 3
                    
                    craft_x = equip_inv.pos_x - craft_width - int(15 * scale)
                    craft_y = equip_inv.pos_y
                    
                    self.crafting_system.update_positions(craft_x, craft_y)
                    self.renderer.draw_crafting_system(screen, self.crafting_system)
                
                self.renderer.draw_crafting_system(screen, self.crafting_system)
            elif isinstance(inv, MAIN_player_hotbar):
                self.renderer.draw_hotbar(screen, inv)
            else:
                self.renderer.draw_base_inventory(screen, inv)
            
        if self.selected_item:
            mx, my = pygame.mouse.get_pos()
            item, count = self.selected_item
            
            time_ms = pygame.time.get_ticks()
            scale_offset = math.sin(time_ms * 0.008) * cfg.INV_SELECTED_ITEM_SCALE_OFFSET
            current_size = int(cfg.BASE_INV_slot_size * (cfg.INV_SELECTED_ITEM_SCALE_BASE + scale_offset))
            
            shadow = pygame.Surface((current_size, current_size), pygame.SRCALPHA)
            pygame.draw.circle(shadow, cfg.INV_SELECTED_ITEM_SHADOW_COLOR, (current_size//2, current_size//2), current_size//2 - 4)
            screen.blit(shadow, (mx - current_size//2, my - current_size//2))
            screen.blit(item.resize(current_size), item.resize(current_size).get_rect(center=(mx, my)))
            
            if count > 1:
                font = cfg.INV_nums_font
                text_str = str(count)
                shadow_surf = font.render(text_str, True, cfg.INV_SELECTED_ITEM_SHADOW_TEXT_COLOR)
                text_surf = font.render(text_str, True, cfg.INV_SELECTED_ITEM_TEXT_COLOR)
                screen.blit(shadow_surf, (mx + cfg.INV_SELECTED_ITEM_TEXT_OFFSET_X, my + cfg.INV_SELECTED_ITEM_TEXT_OFFSET_Y))
                screen.blit(text_surf, (mx + cfg.INV_SELECTED_ITEM_TEXT_OFFSET_X - 2, my + cfg.INV_SELECTED_ITEM_TEXT_OFFSET_Y - 2))
        
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
            
        if self.active_split_popup:
            self.renderer.draw_split_popup(screen, self.active_split_popup)
    
    def handle_event(self, event):
        if self.active_split_popup:
            self.active_split_popup.handle_event(event)
            return 
        
        if self.player_inventory_opened:
            self.crafting_system.inventory_interactions(event, self)

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
    
    def PLAYER_inventory_open(self, event, pl_inv, equip_inv):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
            self.toggle_inventory(pl_inv, equip_inv)
        if self.player_inventory_opened and event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            self.handle_event(event)