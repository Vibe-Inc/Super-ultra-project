import math
import copy
import pygame
from typing import TYPE_CHECKING
import src.config as cfg
from src.ui.widgets import Slider, Button
from src.items.items import Consumable
from database.GP_database import Gp_database
from src.items.items import create_item

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
    """
    Manages the player's equipment loadout slots.

    A specialized grid intended strictly for equippable items such as armor, 
    weapons, and accessories that alter character stats.

    Methods:
        __init__(app):
            Initialize the equipment inventory grid based on config dimensions.
    """
    def __init__(self, app: "App"):
        super().__init__(
            cfg.MAIN_INV_equipment_columns, cfg.MAIN_INV_equipment_rows, None,
            cfg.BASE_INV_slot_size, cfg.MAIN_INV_equipment_pos_x, cfg.MAIN_INV_equipment_pos_y, cfg.BASE_INV_border
        )

class MAIN_player_hotbar(Inventory):
    """
    Handles the player's quick-access action bar.

    Manages a single-row horizontal grid of items bound to keyboard shortcuts (1-0). 
    Supports visual active-slot highlights and fast consumption during gameplay.

    Attributes:
        app (App): 
            The main application reference.
        active_slot_index (int): 
            The current column index of the highlighted hotbar slot.

    Methods:
        __init__(app):
            Initialize the hotbar slots and dimensions.
        update_position():
            Dynamically recalculate position to keep the hotbar centered on the screen.
        get_slot_under_mouse():
            Wrapper to update position before checking mouse hover logic.
        inventory_interactions(event, manager):
            Wrapper to update position before processing clicks.
        scroll_active_slot(y_direction):
            Rotate the active highlighted slot via mouse wheel input.
        use_active_slot():
            Consume or interact with the item in the currently active slot.
        handle_hotkeys(event):
            Parse keyboard input (1 through 0) to swap active slots and use items.
        _use_hotbar_item(col):
            Internal logic for triggering the item's use method in gameplay.
    """
    def __init__(self, app: "App"):
        self.app = app
        columns = getattr(cfg, 'INV_HOTBAR_COLUMNS', 10)
        rows = cfg.INV_HOTBAR_ROWS
        scale = cfg.INV_HOTBAR_SCALE
        slot_size = int(cfg.BASE_INV_slot_size * scale)
        
        if not hasattr(app, 'MAIN_HOTBAR_items'):
            app.MAIN_HOTBAR_items = [[None for _ in range(rows)] for _ in range(columns)]

        super().__init__(columns, rows, app.MAIN_HOTBAR_items, slot_size, 0, 0, cfg.BASE_INV_border)
        self.active_slot_index = 0
        self.update_position()

    def update_position(self):
        total_width = (self.slot_size + self.border) * self.columns + self.border
        self.pos_x = (cfg.SCREEN_WIDTH - total_width) // 2
        self.pos_y = cfg.SCREEN_HEIGHT + cfg.INV_HOTBAR_Y_OFFSET - self.slot_size

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

class Inventory_slider(Slider):
    """
    A specialized slider widget for selecting item split quantities.

    Maps a continuous float output from the base Slider interface into 
    discrete integer amounts based on the maximum stack count of an item.

    Attributes:
        max_qty (int): 
            The maximum available item stack quantity to restrict the slider range.
        external_callback (callable): 
            The function to fire when the user adjusts the slider value.

    Methods:
        __init__(x, y, width, max_qty, action_callback):
            Initialize the slider geometry, colors, and maximum quantity limits.
        _convert_to_int(float_value):
            Translate the slider's native 0.0-1.0 float position into a valid integer split amount.
    """
    def __init__(self, x, y, width, max_qty, action_callback):
        self.max_qty = max_qty
        self.external_callback = action_callback
        super().__init__(
            x=x, y=y, height=cfg.INV_SLIDER_TRACK_HEIGHT, track_thickness=cfg.INV_SLIDER_TRACK_THICKNESS, 
            track_colour=cfg.INV_SLIDER_TRACK_COLOR, knob_colour=cfg.INV_SLIDER_KNOB_COLOR,
            knob_width=cfg.INV_SLIDER_KNOB_WIDTH, knob_height=cfg.INV_SLIDER_KNOB_HEIGHT, 
            track_length=width, value=0.0, action=self._convert_to_int
        )

    def _convert_to_int(self, float_value):
        result = 1 if self.max_qty <= 1 else 1 + int(float_value * (self.max_qty - 1))
        if self.external_callback:
            self.external_callback(result)

class CraftingGrid(Inventory):
    def __init__(self, app):
        super().__init__(3, 3, None, cfg.BASE_INV_slot_size, 0, 0, cfg.BASE_INV_border)
        self.app = app
        self.output_slot = None
        
        self.pos_x = 0
        self.pos_y = 0
        self.output_pos_x = 0
        self.output_pos_y = 0
        
        db = Gp_database()
        self.all_recipes = db.get_all_recipes()
        db.close()
        
        scale = cfg.ui_scale()
        self.book_button = Button(
            rect=pygame.Rect(0, 0, max(80, int(100 * scale)), max(24, int(28 * scale))),
            text="RECIPES", color=(40, 40, 40), hover_color=(70, 70, 70),
            font=cfg.INV_nums_font, font_color=(255, 255, 255),
            corner_width=2, 
            on_click=self.open_recipe_menu
        )
    def open_recipe_menu(self):
        self.app.manager.set_state("recipe_book")

    def update_positions(self, base_x, base_y):
        """Динамічно оновлює координати крафту відносно головного інвентарю екіпірування"""
        scale = cfg.ui_scale()
        self.pos_x = base_x
        self.pos_y = base_y
        
        grid_size = (self.slot_size + self.border) * 3
        
        self.output_pos_x = self.pos_x + (grid_size // 2) - (self.slot_size // 2)
        self.output_pos_y = self.pos_y + grid_size + int(45 * scale)
        
        self.book_button.rect.topleft = (self.pos_x - int(40 * scale), self.pos_y)

    def inventory_interactions(self, event, manager):
        if event.type != pygame.MOUSEBUTTONDOWN: return
        mouse_x, mouse_y = pygame.mouse.get_pos()

        if self.book_button.rect.collidepoint((mouse_x, mouse_y)) and event.button == 1:
            self.book_button.on_click()
            return

        output_rect = pygame.Rect(self.output_pos_x, self.output_pos_y, self.slot_size, self.slot_size)
        if output_rect.collidepoint(mouse_x, mouse_y) and event.button == 1:
            if self.output_slot and not manager.selected_item:
                manager.selected_item = self.output_slot
                self.output_slot = None
                
                for col in range(3):
                    for row in range(3):
                        if self.items[col][row]:
                            self.items[col][row][1] -= 1
                            if self.items[col][row][1] <= 0:
                                self.items[col][row] = None
                self.check_recipes()
            return

        super().inventory_interactions(event, manager)
        self.check_recipes()

    def check_recipes(self):
        current_matrix = [[None for _ in range(3)] for _ in range(3)]
        for col in range(3):
            for row in range(3):
                if self.items[col][row]:
                    current_matrix[col][row] = self.items[col][row][0].id

        matched_recipe = None
        for recipe in self.all_recipes:
            if self._matrix_match(current_matrix, recipe["matrix"]):
                matched_recipe = recipe
                break

        if matched_recipe:
            new_item = create_item(matched_recipe["result_id"])
            self.output_slot = [new_item, matched_recipe["amount"]]
        else:
            self.output_slot = None

    def _matrix_match(self, m1, m2):
        """Порівнює дві матриці 3х3"""
        for c in range(3):
            for r in range(3):
                if m1[c][r] != m2[c][r]:
                    return False
        return True

class CraftingLogic:
    @staticmethod
    def can_craft(player_inv: MAIN_player_inventory, ingredients: dict) -> bool:
        available = {}
        for col in range(player_inv.columns):
            for row in range(player_inv.rows):
                slot = player_inv.items[col][row]
                if slot:
                    item_id = slot[0].id
                    count = slot[1]
                    available[item_id] = available.get(item_id, 0) + count

        for req_id, req_amount in ingredients.items():
            if available.get(req_id, 0) < req_amount:
                return False
        return True

    @staticmethod
    def consume_ingredients(player_inv: MAIN_player_inventory, ingredients: dict):
        for req_id, req_amount in ingredients.items():
            amount_to_remove = req_amount
            for col in range(player_inv.columns):
                for row in range(player_inv.rows):
                    if amount_to_remove <= 0:
                        break
                    
                    slot = player_inv.items[col][row]
                    if slot and slot[0].id == req_id:
                        if slot[1] >= amount_to_remove:
                            slot[1] -= amount_to_remove
                            amount_to_remove = 0
                            if slot[1] == 0:
                                player_inv.items[col][row] = None
                        else:
                            amount_to_remove -= slot[1]
                            player_inv.items[col][row] = None

    @staticmethod
    def add_crafted_item(player_inv: MAIN_player_inventory, result_item, amount: int) -> bool:
        for col in range(player_inv.columns):
            for row in range(player_inv.rows):
                slot = player_inv.items[col][row]
                if slot and slot[0].id == result_item.id:
                    slot[1] += amount
                    return True
                    
        for col in range(player_inv.columns):
            for row in range(player_inv.rows):
                if player_inv.items[col][row] is None:
                    import copy
                    player_inv.items[col][row] = [copy.copy(result_item), amount]
                    return True
        return False