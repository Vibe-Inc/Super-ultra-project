import math
import copy
import pygame
from typing import TYPE_CHECKING
import src.config as cfg
from src.ui.widgets import Slider, Button
from src.items.items import Consumable

if TYPE_CHECKING:
    from src.app import App

class Inventory:
    """
    Base logic class for grid-based inventory systems.

    Manages item storage, grid positioning, and core mouse interactions 
    such as drag-and-drop mechanics, item splitting, and consuming items directly 
    from the slots.

    Attributes:
        columns (int): 
            The number of columns in the inventory grid.
        rows (int): 
            The number of rows in the inventory grid.
        items (list): 
            A 2D list representing the grid of items.
        slot_size (int): 
            The pixel size (width and height) of a single inventory slot.
        pos_x (int): 
            The x-coordinate position of the inventory on the screen.
        pos_y (int): 
            The y-coordinate position of the inventory on the screen.
        border (int): 
            The thickness of the border spacing between slots.
        is_hidden (bool): 
            Flag indicating whether the inventory interactions are currently disabled/hidden.

    Methods:
        __init__(columns, rows, items, slot_size, pos_x, pos_y, slot_border):
            Initialize the base inventory grid and parameters.
        inventory_interactions(event, manager):
            Process mouse clicks for dragging, dropping, splitting, or consuming items.
        get_slot_under_mouse():
            Detect and return the slot data and bounding rectangle currently hovered by the mouse.
    """
    def __init__(self, columns, rows, items, slot_size, pos_x, pos_y, slot_border):
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
        self.is_hidden = False

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
                from src.inventory.inventory_manager import Split_popup_model
                if slot and not manager.selected_item and slot[1] > 1:
                    rect = pygame.Rect(
                        self.pos_x + (self.slot_size + self.border) * x + self.border,
                        self.pos_y + (self.slot_size + self.border) * y + self.border,
                        self.slot_size, self.slot_size
                    )
                    manager.active_split_popup = Split_popup_model(manager, slot, rect)
                    
            elif event.button == 3 and slot and not manager.selected_item:
                item, count = slot
                if isinstance(item, Consumable):
                    game_state = getattr(manager.app.manager.states.get("gameplay"), 'character', None)
                    if game_state and item.use(game_state):
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

class ShopInventory(Inventory):
    """
    Represents a merchant's inventory interface.

    Extends the base Inventory to support buying and selling mechanics, 
    automatic money deductions, and a dedicated UI button for closing the shop.

    Attributes:
        app (App): 
            The main application reference for accessing global states like money.
        close_button (Button): 
            The UI button responsible for closing the shop interface.

    Methods:
        __init__(app, items_list):
            Initialize the shop grid and populate it with merchant items.
        inventory_interactions(event, manager):
            Process trading mechanics (buying items, selling dragged items).
        _close_shop():
            Close the merchant interface and remove it from active rendering.
    """
    def __init__(self, app, items_list):
        self.app = app
        rows, columns = 4, 4
        items_grid = [[None for _ in range(rows)] for _ in range(columns)]
        for i, item in enumerate(items_list):
            x, y = i % columns, i // columns
            if y < rows: items_grid[x][y] = [item, 1]
            
        super().__init__(
            columns, rows, items_grid, 
            cfg.BASE_INV_slot_size, 0, 0, cfg.BASE_INV_border
        )
        scale = cfg.ui_scale()
        btn_w, btn_h = max(80, int(140 * scale)), max(28, int(38 * scale))
        self.close_button = Button(
            rect=pygame.Rect(0, 0, btn_w, btn_h),
            text=_("LEAVE SHOP"), color=cfg.INV_SHOP_CLOSE_BTN_COLOR, 
            hover_color=cfg.INV_SHOP_CLOSE_BTN_HOVER_COLOR,
            font=cfg.INV_nums_font, font_color=cfg.INV_SHOP_CLOSE_BTN_FONT_COLOR,
            corner_width=max(2, int(8 * scale)), on_click=self._close_shop
        )

    def inventory_interactions(self, event, manager):
        if event.type != pygame.MOUSEBUTTONDOWN: return
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        if event.button == 1 and self.close_button:
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
    """
    Manages the primary player inventory screen.

    Inherits from the base Inventory and embeds additional UI elements like 
    navigation buttons to switch to the skill or talent tree menus.

    Attributes:
        app (App): 
            The main application reference.
        open_skillbar_btn (Button): 
            Button widget to navigate to the magic/skills interface.
        open_skilltree_btn (Button): 
            Button widget to navigate to the talent tree interface.

    Methods:
        __init__(app):
            Initialize the main player inventory and standard buttons.
        inventory_interactions(event, manager):
            Handle clicks for buttons and fall back to base inventory item logic.
    """
    def __init__(self, app:"App"):
        self.app = app
        super().__init__(
            cfg.MAIN_INV_columns, cfg.MAIN_INV_rows, app.MAIN_INV_items,
            cfg.BASE_INV_slot_size, cfg.MAIN_INV_pos_x, cfg.MAIN_INV_pos_y, cfg.BASE_INV_border
        )
        scale = cfg.ui_scale()
        btn_w, btn_h = max(20, int(160 * scale)), max(8, int(36 * scale))
        
        self.open_skillbar_btn = Button(
            rect=pygame.Rect(0, 0, btn_w, btn_h),
            text=_("SKILLS & MAGIC"), color=cfg.INV_SKILLBAR_BTN_COLOR, 
            hover_color=cfg.INV_SKILLBAR_BTN_HOVER_COLOR,
            font=cfg.tooltip_font_CREDITS, font_color=cfg.INV_SKILLBAR_BTN_FONT_COLOR,
            corner_width=max(2, int(8 * scale)), on_click=None
        )
        self.open_skilltree_btn = Button(
            rect=pygame.Rect(0, 0, btn_w, btn_h),
            text=_("TALENT TREE"), color=cfg.INV_SKILLTREE_BTN_COLOR, 
            hover_color=cfg.INV_SKILLTREE_BTN_HOVER_COLOR,
            font=cfg.tooltip_font_CREDITS, font_color=cfg.INV_SKILLTREE_BTN_FONT_COLOR,
            corner_width=max(2, int(8 * scale)), on_click=None
        )