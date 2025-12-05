import pygame
from src.inventory.system import Inventory
import src.config as cfg
import copy

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
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
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
