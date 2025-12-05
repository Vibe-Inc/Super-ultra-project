import pygame
from typing import TYPE_CHECKING
import copy

import src.config as cfg
from src.ui.widgets import Tooltip

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



class ShopInventory(Inventory):
    def __init__(self, app, items_data):
        """
        items_data: list of tuples (item_obj, price)
        """
        self.app = app
        self.shop_items_data = items_data
        self.prices = {item.id: price for item, price in items_data}
        
        rows = 4
        columns = 4
        items_grid = [[None for _ in range(rows)] for _ in range(columns)]
        
        for i, (item, price) in enumerate(items_data):
            x = i % columns
            y = i // columns
            if y < rows:
                items_grid[x][y] = [item, 1]
        
        # Position will be set by the manager when opening trade
        super().__init__(
            columns, rows, items_grid, 
            cfg.BASE_INV_slot_size, 
            0, 0, 
            cfg.BASE_INV_border, 
            cfg.BASE_INV_slot_color, 
            cfg.BASE_INV_border_color
        )

    def draw(self, screen):
        # Draw background for shop
        pygame.draw.rect(
            screen,
            cfg.MAIN_INV_BACKGROUND,
            (self.pos_x - 15, self.pos_y - 15,
             (self.slot_size + self.border) * self.columns + self.border + 30,
             (self.slot_size + self.border) * self.rows + self.border + 30),
            0, 16
        )
        
        super().draw(screen)
        
        # Draw prices
        for x in range(self.columns):
            for y in range(self.rows):
                if self.items[x][y]:
                    item = self.items[x][y][0]
                    price = self.prices.get(item.id, 0)
                    
                    font = cfg.INV_nums_font
                    text = font.render(f"${price}", True, (255, 255, 0))
                    rect_x = self.pos_x + (self.slot_size + self.border) * x + self.border
                    rect_y = self.pos_y + (self.slot_size + self.border) * y + self.border
                    
                    screen.blit(text, (rect_x + 5, rect_y + 50))

    def inventory_interactions(self, event, manager):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Check if mouse is within inventory bounds
        total_width = (self.slot_size + self.border) * self.columns
        total_height = (self.slot_size + self.border) * self.rows
        if not (self.pos_x <= mouse_x <= self.pos_x + total_width and 
                self.pos_y <= mouse_y <= self.pos_y + total_height):
            return

        x = (mouse_x - self.pos_x) // (self.slot_size + self.border)
        y = (mouse_y - self.pos_y) // (self.slot_size + self.border)
        
        if 0 <= x < self.columns and 0 <= y < self.rows:
            slot = self.items[x][y]
            
            if event.button == 1: # Left click
                if manager.selected_item:
                    # Selling
                    item, count = manager.selected_item
                    # Sell price logic (e.g. same as buy price or half)
                    # If item is in shop, use its price, else default 10
                    price = self.prices.get(item.id, 10) 
                    
                    self.app.money += price * count
                    manager.selected_item = None
                    # Item is consumed (sold)
                else:
                    # Buying
                    if slot:
                        item, _ = slot
                        price = self.prices.get(item.id, 0)
                        if self.app.money >= price:
                            self.app.money -= price
                            # Create a copy for the player
                            new_item = copy.copy(item)
                            manager.selected_item = [new_item, 1]
                            # Do not remove from shop (infinite stock)


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
        self.app = app
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
            (self.pos_x-15, self.pos_y-335,
             (self.slot_size + self.border) * self.columns + self.border+30,
             (self.slot_size + self.border) * self.rows + self.border +350),
             0, 16, 70 , 70)
            
        # Character preview (relative to pos_x)
        # Offset calculated from original values: (SCREEN_WIDTH//2+100) - MAIN_INV_pos_x
        # Assuming MAIN_INV_pos_x is around 671 and preview_x is 1060, offset is ~389
        preview_offset_x = 389
        preview_x = self.pos_x + preview_offset_x
        
        pygame.draw.rect(
            screen,
            (0, 0, 0),
            (preview_x, self.pos_y-305, 190, 275),
            0, 15, 50, 50, 50, 50
            ) 
        
        # Draw character preview
        game_state = self.app.manager.states.get("gameplay")
        if game_state and hasattr(game_state, "character"):
            # Get the current frame of the character
            char_img = game_state.character.image
            
            # Scale it up to fit the preview box
            scale_factor = 2.5
            new_width = int(char_img.get_width() * scale_factor)
            new_height = int(char_img.get_height() * scale_factor)
            scaled_img = pygame.transform.scale(char_img, (new_width, new_height))
            
            # Center the image in the preview box
            preview_rect = pygame.Rect(preview_x, self.pos_y-305, 190, 275)
            img_rect = scaled_img.get_rect(center=preview_rect.center)
            
            screen.blit(scaled_img, img_rect)

        # Draw money
        money_text = f"{_('Money')}: {self.app.money}"
        text_surf = cfg.tooltip_font_CREDITS.render(money_text, True, (255, 255, 255))
        screen.blit(text_surf, (preview_x, self.pos_y - 20))

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

    def toggle_inventory(self, pl_inv, equip_inv):
        self.player_inventory_opened = not self.player_inventory_opened   
        if self.player_inventory_opened is True:
            self.add_active_inventory(pl_inv)
            self.add_active_inventory(equip_inv)
        else:
            self.remove_active_inventory(pl_inv)
            self.remove_active_inventory(equip_inv)

    def toggle_trade(self, pl_inv, shop_inv):
        # If inventory is already open (normal mode), close it first or switch mode?
        # Let's assume trade mode is separate.
        
        # Check if shop_inv is already active
        if shop_inv in self.active_inventories:
            # Close Trade
            self.remove_active_inventory(shop_inv)
            self.remove_active_inventory(pl_inv)
            
            # Reset Player Inventory Position
            pl_inv.pos_x = cfg.MAIN_INV_pos_x
            self.player_inventory_opened = False
        else:
            # Open Trade
            # Close normal inventory if open
            if self.player_inventory_opened:
                # Just remove equipment, keep player inv but move it
                # self.remove_active_inventory(equip_inv) # Need reference to equip_inv?
                # Assuming toggle_trade is called instead of toggle_inventory
                pass
            
            self.player_inventory_opened = True # Mark as open so other logic knows
            
            # Shift Player Inventory to Left
            pl_inv.pos_x = cfg.SCREEN_WIDTH // 2 - 500 
            
            # Position Shop Inventory to Right
            shop_inv.pos_x = cfg.SCREEN_WIDTH // 2 + 100
            shop_inv.pos_y = pl_inv.pos_y
            
            self.add_active_inventory(pl_inv)
            self.add_active_inventory(shop_inv)
    
    def PLAYER_inventory_open(self,event: pygame.event.Event,pl_inv,equip_inv):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i:
                self.toggle_inventory(pl_inv, equip_inv)
        if self.player_inventory_opened is True and event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_event(event)