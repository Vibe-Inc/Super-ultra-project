import pygame
from typing import TYPE_CHECKING

import src.config as cfg
from src.ui.widgets import Tooltip, Slider, Button

if TYPE_CHECKING:
    from src.app import App


class Inventory:
    """
    Represents a grid-based inventory in the game.

    This class manages a 2D grid of item slots, supports item stacking, splitting, and drag-and-drop interactions.

    Attributes:
        columns (int):
            Number of columns in the inventory grid.
        rows (int):
            Number of rows in the inventory grid.
        items (list[list[tuple[Item, int] | None]]):
            2D list representing the slots, where each slot holds either None or a tuple of (item object, count).
        slot_size (int):
            Width and height of a single slot in pixels.
        pos_x (int):
            X-coordinate (top-left) position of the inventory on the screen.
        pos_y (int):
            Y-coordinate (top-left) position of the inventory on the screen.
        border (int):
            Size of the border/spacing between slots.
        slot_color (tuple[int, int, int]):
            RGB color of the inventory slots.
        slot_border_color (tuple[int, int, int]):
            RGB color of the inventory's outer border.
        selected_item (tuple[Item, int] | None):
            The item currently being dragged or held by the mouse from this inventory.

    Methods:
        __init__(columns, rows, items, slot_size, pos_x, pos_y, slot_border, slot_color, slot_border_color):
            Initialize the inventory object.
        draw(screen):
            Render the inventory grid, border, and items onto the screen.
            Args:
                screen (pygame.Surface): The surface to draw the inventory on.
        inventory_interactions(event, manager):
            Handle mouse button events for item picking up, dropping, stacking, swapping, and splitting within the inventory.
            Args:
                event (pygame.event.Event): The Pygame event to process.
                manager (INVENTORY_manager): The inventory manager handling global state.
        get_slot_under_mouse():
            Get the slot and item currently under the mouse cursor.
            Returns:
                tuple[pygame.Rect, Item] | None: The slot rectangle and item, or None if not over a slot.
    """
    def __init__(self, columns, rows, items, slot_size, pos_x, pos_y, slot_border, slot_color, slot_border_color ):
        self.columns:int = columns
        self.rows:int = rows
        if not items:
            self.items:list = [[None for _ in range(self.rows)] for _ in range(self.columns)]
        else:
            self.items:list = items
        self.slot_size:int = slot_size
        self.pos_x:int = pos_x
        self.pos_y:int = pos_y
        self.border:int = slot_border
        self.slot_color:tuple[int, int, int]= slot_color
        self.slot_border_color:tuple[int, int, int]= slot_border_color

        self.selected_item = None

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            self.slot_border_color,
            (self.pos_x, self.pos_y,
             (self.slot_size + self.border) * self.columns + self.border,
             (self.slot_size + self.border) * self.rows + self.border)
        )
      
        for n in range(self.columns):
            for m in range(self.rows):
                rect = (
                    self.pos_x + (self.slot_size + self.border) * n + self.border,
                    self.pos_y + (self.slot_size + self.border) * m + self.border,
                    self.slot_size,
                    self.slot_size
                )
                pygame.draw.rect(screen, self.slot_color, rect)

                if self.items[n][m]:
                    item, count = self.items[n][m]

                    if count <= 0:
                        self.items[n][m] = None
                        continue

                    screen.blit(item.resize(self.slot_size), rect)
                    if count > 1:
                        font_obj = cfg.INV_nums_font
                        obj = font_obj.render(str(count), True, (0, 0, 0))
                        screen.blit(obj, (rect[0] + 50, rect[1] + 50))

    def inventory_interactions(self,event,manager):
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

                elif event.button == 3:
                    if slot and not manager.selected_item and slot[1] > 1:
                        rect = pygame.Rect(
                            self.pos_x + (self.slot_size + self.border) * x + self.border,
                            self.pos_y + (self.slot_size + self.border) * y + self.border,
                            self.slot_size, self.slot_size
                        )
                        manager.active_split_popup = Split_popup(manager, slot, rect)

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
                self.slot_size,
                self.slot_size
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
            x=x, y=y, height=20, track_thickness=4, 
            track_colour=(40, 40, 40), knob_colour=(200, 200, 200),
            knob_width=12, knob_height=18, 
            track_length=width,
            value=0.0, 
            action=self._convert_to_int
        )

    def _convert_to_int(self, float_value):
        if self.max_qty <= 1:
            result = 1
        else:
            result = 1 + int(float_value * (self.max_qty - 1))
        
        if self.external_callback:
            self.external_callback(result)


class Split_popup:
    def __init__(self, manager, slot_ref, rect_pos):
        self.manager = manager
        self.slot_ref = slot_ref
        self.item_obj, self.total_count = slot_ref

        self.width = 180
        self.height = 90
        self.x = rect_pos.right + 5
        self.y = rect_pos.y

        if self.x + self.width > cfg.SCREEN_WIDTH:
            self.x = rect_pos.left - self.width - 5
            
        self.bg_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.split_amount = 1 

        self.slider = Inventory_slider(
            x=self.x + 10,
            y=self.y + 35,
            width=self.width - 20,
            max_qty=self.total_count,
            action_callback=self.update_count 
        )

        self.confirm_btn = Button(
            rect=pygame.Rect(self.x + 40, self.y + 60, 100, 20),
            text="Confirm",
            color=(60, 120, 60),        
            hover_color=(80, 150, 80),  
            font=cfg.INV_nums_font,
            font_color=(255, 255, 255),
            corner_width=5,             
            on_click=self.confirm       
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
        pygame.draw.rect(screen, (45, 45, 50), self.bg_rect)
        pygame.draw.rect(screen, (100, 100, 100), self.bg_rect, 2)

        font = cfg.INV_nums_font
        text = font.render(f"Take: {self.split_amount}", True, (255, 255, 255))
        screen.blit(text, (self.x + 10, self.y + 5))

        self.slider.draw(screen)
        self.confirm_btn.draw(screen)


class MAIN_player_inventory(Inventory):
    """
    Represents the main player inventory grid.

    Inherits from Inventory and customizes drawing to include background and character preview area.

    Methods:
        draw(screen):
            Draw the inventory background, character preview area, and call the base draw method.
            Args:
                screen (pygame.Surface): The surface to draw the inventory on.
    """
    def __init__(self, app:"App"):
        super().__init__(
            cfg.MAIN_INV_columns,
            cfg.MAIN_INV_rows,
            app.MAIN_INV_items,
            cfg.BASE_INV_slot_size,
            cfg.MAIN_INV_pos_x,
            cfg.MAIN_INV_pos_y,
            cfg.BASE_INV_border,
            cfg.BASE_INV_slot_color,
            cfg.BASE_INV_border_color
        )
    def draw(self, screen):
        pygame.draw.rect( 
            screen,
            cfg.MAIN_INV_BACKGROUND,
            (cfg.MAIN_INV_pos_x-15, cfg.MAIN_INV_pos_y-335,
             (cfg.BASE_INV_slot_size + cfg.BASE_INV_border) * cfg.MAIN_INV_columns + cfg.BASE_INV_border+30,
             (cfg.BASE_INV_slot_size + cfg.BASE_INV_border) * cfg.MAIN_INV_rows + cfg.BASE_INV_border +350),
             0, 16, 70 , 70)
            
        pygame.draw.rect(
            screen,
            (0, 0, 0),
            (cfg.SCREEN_WIDTH//2+100, cfg.MAIN_INV_pos_y-305, 190, 275),
            0, 15, 50, 50, 50, 50
            ) #maybe some kind of character preview?

        return super().draw(screen)
    

class MAIN_player_inventory_equipment(Inventory):
    """
    Represents the player's equipment inventory grid (e.g., armor, weapon slots).
    Inherits from Inventory.
    """
    def __init__(self,app :"App"):
        super().__init__(
            cfg.MAIN_INV_equipment_columns,
            cfg.MAIN_INV_equipment_rows,
            None,
            cfg.BASE_INV_slot_size,
            cfg.MAIN_INV_equipment_pos_x,
            cfg.MAIN_INV_equipment_pos_y,
            cfg.BASE_INV_border,
            cfg.BASE_INV_slot_color,
            cfg.BASE_INV_border_color
        )
    pass
    

class INVENTORY_manager:
    """
    Central manager for all in-game inventory operations.

    Tracks which inventories are currently active/visible and manages the state of items being dragged by the player.

    Attributes:
        selected_item (tuple[Item, int] | None):
            The item stack (item object, count) currently held by the mouse cursor, or None if nothing is selected.
        active_inventories (list[Inventory | None]):
            List of Inventory objects (like player bag, equipment, or a chest) that should be drawn and accept interaction.
        player_inventory_opened (bool):
            Flag indicating if the player's main inventory window (and associated equipment) is currently open.
        inventory_tooltip (Tooltip):
            Tooltip object for displaying item information on hover.

    Methods:
        add_active_inventory(inventory):
            Add an Inventory object to the list of active/visible inventories.
            Args:
                inventory (Inventory): The inventory to add.
        remove_active_inventory(inventory):
            Remove an Inventory object from the active list.
            Args:
                inventory (Inventory): The inventory to remove.
        draw(screen):
            Draw all active inventories and the currently selected item (if any) at the mouse position.
            Args:
                screen (pygame.Surface): The surface to draw inventories on.
        handle_event(event):
            Distribute mouse events to all active inventories for interaction processing.
            Args:
                event (pygame.event.Event): The Pygame event to process.
        toggle_inventory(pl_inv, equip_inv):
            Toggle the player's inventory and equipment windows on and off.
            Args:
                pl_inv (Inventory): The main player inventory.
                equip_inv (Inventory): The equipment inventory.
        PLAYER_inventory_open(event, pl_inv, equip_inv):
            Handle opening/closing the player's inventory and equipment with keyboard/mouse events.
            Args:
                event (pygame.event.Event): The Pygame event to process.
                pl_inv (Inventory): The main player inventory.
                equip_inv (Inventory): The equipment inventory.
    """
    def __init__(self):
        self.selected_item:bool = False
        self.active_split_popup = None
        self.active_inventories:list[Inventory|None] = []
        self.player_inventory_opened:bool = False

        self.inventory_tooltip = Tooltip(
            cfg.inventory_tooltip_rect,
            "",
            cfg.inventory_tooltip_bg,
            cfg.inventory_tooltip_border,
            cfg.INV_nums_font,
            cfg.inventory_tooltip_font_color,
            cfg.tooltip_appear,
            cfg.tooltip_padding
        )

    def add_active_inventory (self, inventory):
        if inventory not in self.active_inventories:
            self.active_inventories.append(inventory)

    def remove_active_inventory (self, inventory):
        if inventory in self.active_inventories:
            self.active_inventories.remove(inventory)
    
    def draw(self, screen):
        for inv in self.active_inventories:
            inv.draw(screen)
        if self.selected_item:
            mx, my = pygame.mouse.get_pos()
            item, count = self.selected_item
            screen.blit(item.resize(cfg.BASE_INV_slot_size), (mx - cfg.BASE_INV_slot_size//2, my - cfg.BASE_INV_slot_size//2))
            font = cfg.INV_nums_font
            obj = font.render(str(count), True, (0, 0, 0))
            screen.blit(obj, (mx + cfg.BASE_INV_slot_size//2 - 20 , my + cfg.BASE_INV_slot_size//2 - 20))
        
        if not self.selected_item:
            found_item = False
            for inv in self.active_inventories:
                result = inv.get_slot_under_mouse()
                if result:
                    rect, item = result
                    self.inventory_tooltip.update_target(rect, item.get_tooltip_text())
                    found_item = True
                    break
            if not found_item:
                self.inventory_tooltip.update_target(pygame.Rect(-100,-100,0,0), "")
            self.inventory_tooltip.hover_update(pygame.mouse.get_pos())
            self.inventory_tooltip.draw(screen)
        if self.active_split_popup:
            self.active_split_popup.draw(screen)
    
    def handle_event(self, event):
        if self.active_split_popup:
            self.active_split_popup.handle_event(event)
            return 
        for inv in self.active_inventories:
            inv.inventory_interactions(event, self)

    def toggle_inventory(self, pl_inv, equip_inv):
        self.player_inventory_opened = not self.player_inventory_opened   
        if self.player_inventory_opened is True:
            self.add_active_inventory(pl_inv)
            self.add_active_inventory(equip_inv)
        else:
            self.remove_active_inventory(pl_inv)
            self.remove_active_inventory(equip_inv)
    
    def PLAYER_inventory_open(self,event: pygame.event.Event,pl_inv,equip_inv):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i:
                self.toggle_inventory(pl_inv, equip_inv)

        if self.player_inventory_opened is True:
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                self.handle_event(event)