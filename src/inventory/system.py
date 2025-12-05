import pygame
from typing import TYPE_CHECKING

import src.config as cfg
from src.ui.widgets import Tooltip

if TYPE_CHECKING:
    from src.app import App


class Inventory:
    """
    Represents a grid-based inventory in the game.
    Attributes:
        columns (int): The number of columns in the inventory grid.
        rows (int): The number of rows in the inventory grid.
        items (list[list[tuple[Item, int] | None]]): A 2D list representing the slots, where each slot holds either None or a tuple of (item object, count).
        slot_size (int): The width and height of a single slot in pixels.
        pos_x (int): The x-coordinate (top-left) position of the inventory on the screen.
        pos_y (int): The y-coordinate (top-left) position of the inventory on the screen.
        border (int): The size of the border/spacing between slots.
        slot_color (tuple[int, int, int]): The RGB color of the inventory slots.
        slot_border_color (tuple[int, int, int]): The RGB color of the inventory's outer border.
        selected_item (tuple[Item, int] | None): The item currently being dragged or held by the mouse from this inventory.

    Methods:
        __init__(self, columns, rows, items, slot_size, pos_x, pos_y, slot_border, slot_color, slot_border_color): Initializes the inventory object.
        draw(self, screen): Renders the inventory grid, border, and items onto the screen.
        inventory_interactions(self, event, manager): Handles mouse button events (clicks) for item picking up, dropping, stacking, swapping, and splitting within the inventory.
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
                    screen.blit(item.resize(self.slot_size), rect)
                    if count > 1:
                        font_obj = cfg.INV_nums_font
                        obj = font_obj.render(str(count), True, (0, 0, 0))
                        screen.blit(obj, (rect[0] + 50, rect[1] + 50))

    def inventory_interactions(self,event,manager):
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

                elif event.button == 3 and slot and not manager.selected_item and slot[1] > 1:
                    split_count = (slot[1] + 1) // 2
                    manager.selected_item = [slot[0], split_count]
                    self.items[x][y][1] -= split_count
                    if self.items[x][y][1] <= 0:
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
                self.slot_size,
                self.slot_size
            )

            if slot_data:
                item, count = slot_data
                return rect, item
        
        return None



class MAIN_player_inventory(Inventory):
    
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
    Represents the central manager for all in-game inventory operations. 
    It tracks which inventories are currently active/visible and manages the state 
    of items being dragged by the player.

    Attributes:
        selected_item (tuple[Item, int] | None): The item stack (item object, count) 
            currently held by the mouse cursor, or False/None if nothing is selected. 
            (Note: In the provided code, it's initialized as bool=False but used as a tuple or None).
        active_inventories (list[Inventory | None]): A list of Inventory objects 
            (like player bag, equipment, or a chest) that should be drawn and accept interaction.
        player_inventory_opened (bool): Flag indicating if the player's main inventory 
            window (and associated equipment) is currently open.

    Methods:
        __init__(self): Initializes the manager state.
        add_active_inventory(self, inventory): Adds an Inventory object to the list of active/visible inventories.
        remove_active_inventory(self, inventory): Removes an Inventory object from the active list.
        draw(self, screen): Draws all active inventories and the currently selected item (if any) at the mouse position.
        handle_event(self, event): Distributes mouse events to all active inventories for interaction processing.
        PLAYER_inventory_open(self, event: pygame.event.Event, pl_inv, equip_inv): Toggles the player's inventory 
            and equipment windows on and off, typically upon pressing the 'I' key (pygame.K_i), 
            and triggers interaction handling if a mouse button is clicked while open.
    """
    def __init__(self):
        self.selected_item:bool = False
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
    
    def handle_event(self, event):
        for inv in self.active_inventories:
            inv.inventory_interactions(event, self)
    
    def PLAYER_inventory_open(self,event: pygame.event.Event,pl_inv,equip_inv):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i:
                self.player_inventory_opened = not self.player_inventory_opened   
                if self.player_inventory_opened is True:
                    self.add_active_inventory(pl_inv)
                    self.add_active_inventory(equip_inv)
                else:
                    self.remove_active_inventory(pl_inv)
                    self.remove_active_inventory(equip_inv)
        if self.player_inventory_opened is True and event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_event(event)