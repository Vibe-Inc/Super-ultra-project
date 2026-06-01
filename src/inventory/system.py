import pygame
from typing import TYPE_CHECKING
import copy

from src.core.logger import logger
import src.config as cfg
from src.ui.widgets import Tooltip, Slider, Button
from src.items.items import Consumable

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
                                logger.debug(f"Merged stacks of {slot[0].id} new_count={slot[1]}")
                                manager.selected_item = None
                            else:
                                self.items[x][y], manager.selected_item = manager.selected_item, self.items[x][y]
                                logger.debug(f"Swapped items into slot ({x},{y})")
                        else:
                            self.items[x][y] = manager.selected_item
                            logger.debug(f"Placed item {getattr(manager.selected_item[0], 'id', None)} into slot ({x},{y})")
                            manager.selected_item = None
                    else:
                        if slot:
                            manager.selected_item = slot
                            self.items[x][y] = None
                            logger.debug(f"Picked up item {getattr(slot[0], 'id', None)} from slot ({x},{y})")

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
                                logger.info(f"Used consumable {item.id} on character")
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
                self.slot_size,
                self.slot_size
            )

            if slot_data:
                item, count = slot_data
                return rect, item
        
        return None

class Inventory_slider(Slider):
    """
    Slider widget that selects an inventory split amount.

    Attributes:
        max_qty (int):
            Maximum quantity represented by the slider.
        external_callback (callable | None):
            Callback invoked with the selected integer amount.

    Methods:
        __init__(x, y, width, max_qty, action_callback):
            Initialize the slider for item splitting.
        _convert_to_int(float_value):
            Convert the slider value to a quantity and forward it to the callback.
    """
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
    """
    Popup used to split a stack of items into two parts.

    Attributes:
        manager (INVENTORY_manager):
            Inventory manager that owns the popup.
        slot_ref (list):
            Reference to the original inventory slot being split.
        item_obj (Item):
            Item instance stored in the slot.
        total_count (int):
            Total stack size at the time the popup was opened.
        width (int):
            Popup width in pixels.
        height (int):
            Popup height in pixels.
        x (int):
            Popup x-position.
        y (int):
            Popup y-position.
        bg_rect (pygame.Rect):
            Background rectangle for the popup.
        split_amount (int):
            Currently selected split amount.
        slider (Inventory_slider):
            Slider used to choose the split amount.
        confirm_btn (Button):
            Button that confirms the split.

    Methods:
        __init__(manager, slot_ref, rect_pos):
            Initialize the split popup.
        update_count(int_val):
            Update the selected split amount.
        confirm():
            Apply the split and close the popup.
        handle_event(event):
            Forward input events to the popup controls.
        draw(screen):
            Render the popup and its controls.
    """
    def __init__(self, manager, slot_ref, rect_pos):
        self.manager = manager
        self.slot_ref = slot_ref
        self.item_obj, self.total_count = slot_ref

        scale = cfg.ui_scale()
        self.width = max(40,int(180 * scale))
        self.height = max(20,int(90 * scale))
        self.x = rect_pos.right + int(5 * scale)
        self.y = rect_pos.y

        if self.x + self.width > cfg.SCREEN_WIDTH:
            self.x = rect_pos.left - self.width - 5
            
        self.bg_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.split_amount = 1 


        self.slider = Inventory_slider(
            x=self.x + int(10 * scale),
            y=self.y + int(35 * scale),
            width=self.width - int(20 * scale),
            max_qty=self.total_count,
            action_callback=self.update_count 
        )

        self.confirm_btn = Button(
            rect=pygame.Rect(self.x + int(40 * scale), self.y + int(60 * scale), max(20,int(100 * scale)), max(8,int(20 * scale))),
            text="Confirm",
            color=(60, 120, 60),        
            hover_color=(80, 150, 80),  
            font=cfg.INV_nums_font,
            font_color=(255, 255, 255),
            corner_width=max(2,int(5 * scale)),             
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


class ShopInventory(Inventory):
    """
    Inventory view that presents shop items for buying and selling.

    Attributes:
        app (App):
            Reference to the main application.

    Methods:
        __init__(app, items_list):
            Build a shop inventory from a flat list of items.
        draw(screen):
            Render the shop background, items, and item prices.
        inventory_interactions(event, manager):
            Handle buying and selling interactions.
    """
    def __init__(self, app, items_list):
        self.app = app
        
        rows = 4
        columns = 4
        items_grid = [[None for _ in range(rows)] for _ in range(columns)]
        
        for i, item in enumerate(items_list):
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
        # Close shop button
        scale = cfg.ui_scale()
        btn_w = max(80, int(140 * scale))
        btn_h = max(28, int(38 * scale))
        self.close_button = Button(
            rect=pygame.Rect(0, 0, btn_w, btn_h),
            text=_("CLOSE SHOP"),
            color=(120, 60, 60),
            hover_color=(160, 90, 90),
            font=cfg.INV_nums_font,
            font_color=(255, 255, 255),
            corner_width=max(2, int(6 * scale)),
            on_click=self._close_shop
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
                    price = getattr(item, 'price', 0)
                    
                    font = cfg.INV_nums_font
                    text = font.render(f"${price}", True, (255, 255, 0))
                    rect_x = self.pos_x + (self.slot_size + self.border) * x + self.border
                    rect_y = self.pos_y + (self.slot_size + self.border) * y + self.border
                    
                    screen.blit(text, (rect_x + 5, rect_y + 50))

        # Draw close shop button at bottom-right of shop window
        try:
            bg_x = self.pos_x - 15
            bg_y = self.pos_y - 15
            bg_w = (self.slot_size + self.border) * self.columns + self.border + 30
            bg_h = (self.slot_size + self.border) * self.rows + self.border + 30
            # position button inside bg rect at bottom-right
            self.close_button.rect.topleft = (bg_x + bg_w - self.close_button.rect.width - 12, bg_y + bg_h - self.close_button.rect.height - 12)
            self.close_button._update_text_surface()
            self.close_button.draw(screen)
        except Exception:
            pass

    def inventory_interactions(self, event, manager):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()
        # Check close button first
        if event.button == 1 and getattr(self, 'close_button', None):
            if self.close_button.rect.collidepoint((mouse_x, mouse_y)):
                try:
                    self.close_button.on_click()
                except Exception:
                    pass
                return
        
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
                    base_price = getattr(item, 'price', 0)
                    # Sell price logic (e.g. same as buy price or half)
                    # If item is in shop, use its price, else default 10
                    sell_price = int(base_price* 1)
                    
                    self.app.money += sell_price * count                
                    manager.selected_item = None
                    # Item is consumed (sold)
                else:
                    # Buying
                    if slot:
                        shop_item, _ = slot
                        buy_price = getattr(shop_item, 'price', 0)
                        if self.app.money >= buy_price:
                            self.app.money -= buy_price
                            # Create a copy for the player
                            new_item = copy.copy(shop_item)
                            manager.selected_item = [new_item, 1]
                            # Do not remove from shop (infinite stock)
                        else:
                            logger.info(f"Not enough money to buy {shop_item.id}. Cost: ${buy_price}, Balance: ${self.app.money}")


    def _close_shop(self):
        # Attempt to close the currently open shop via inventory manager
        try:
            game_state = self.app.manager.states.get("gameplay")
            if game_state:
                pl_inv = game_state.MAIN_player_inv
                self.app.INV_manager.toggle_trade(pl_inv, self)
            else:
                # fallback: try to remove ourselves
                if self in self.app.INV_manager.active_inventories:
                    self.app.INV_manager.remove_active_inventory(self)
                    if self.app.INV_manager.current_shop_inv is self:
                        self.app.INV_manager.current_shop_inv = None
        except Exception:
            pass


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
        self._portrait_cache = {}
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
        # button to open skillbar/skills menu (rect is positioned in draw)
        scale = cfg.ui_scale()
        btn_w = max(20, int(160 * scale))
        btn_h = max(8, int(36 * scale))
        self.open_skillbar_btn = Button(
            rect=pygame.Rect(0, 0, btn_w, btn_h),
            text=_("SKILLBAR"),
            color=(100, 100, 140),
            hover_color=(140, 140, 180),
            font=cfg.tooltip_font_CREDITS,
            font_color=(255, 255, 255),
            corner_width=max(2, int(8 * scale)),
            on_click=None
        )

    def _load_portrait_surface(self, character):
        sprite_set = getattr(character, "sprite_set", None)
        if not sprite_set:
            return None

        cached = self._portrait_cache.get(sprite_set)
        if cached:
            return cached

        portrait_path = f"assets/characters/{sprite_set}/PortraitAndShowcase/Portrait.png"
        try:
            portrait = pygame.image.load(portrait_path).convert_alpha()
        except FileNotFoundError:
            return None

        self._portrait_cache[sprite_set] = portrait
        return portrait

    def _crop_face_from_frame(self, frame):
        face_height = max(1, int(frame.get_height() * 0.4))
        face_rect = pygame.Rect(0, 0, frame.get_width(), face_height)
        return frame.subsurface(face_rect).copy()

    def _scale_to_fit(self, surface, target_rect):
        if surface.get_width() == 0 or surface.get_height() == 0:
            return surface

        scale = min(
            target_rect.width / surface.get_width(),
            target_rect.height / surface.get_height(),
        )
        new_size = (
            max(1, int(surface.get_width() * scale)),
            max(1, int(surface.get_height() * scale)),
        )
        return pygame.transform.smoothscale(surface, new_size)
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
            preview_rect = pygame.Rect(preview_x, self.pos_y - 305, 190, 275)
            character = game_state.character

            portrait = self._load_portrait_surface(character)
            if portrait is None:
                portrait = self._crop_face_from_frame(character.image)

            scaled_img = self._scale_to_fit(portrait, preview_rect)
            img_rect = scaled_img.get_rect(center=preview_rect.center)
            screen.blit(scaled_img, img_rect)

        # Draw money
        money_text = f"{_('Money')}: {self.app.money}"
        text_surf = cfg.tooltip_font_CREDITS.render(money_text, True, (255, 255, 255))
        screen.blit(text_surf, (preview_x, self.pos_y - 20))

        # position the skillbar open button near the preview area and draw it
        # Draw the skillbar open button only when no shop is active
        if not getattr(self.app.INV_manager, 'current_shop_inv', None):
            btn_x = preview_x
            btn_y = self.pos_y - 60
            self.open_skillbar_btn.rect = pygame.Rect(btn_x, btn_y, self.open_skillbar_btn.rect.width, self.open_skillbar_btn.rect.height)
            try:
                self.open_skillbar_btn._update_text_surface()
            except Exception:
                pass
            self.open_skillbar_btn.draw(screen)

        return super().draw(screen)

    def inventory_interactions(self, event, manager):
        # Handle SKILLBAR button click (only when shop not open)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if hasattr(self, 'open_skillbar_btn') and self.open_skillbar_btn.rect.collidepoint(pygame.mouse.get_pos()):
                if not getattr(self.app.INV_manager, 'current_shop_inv', None):
                    try:
                        self.app.manager.set_state("skillbar")
                    except Exception:
                        pass
                    return

        return super().inventory_interactions(event, manager)
    

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

class MAIN_player_hotbar(Inventory):
    """
    Represents the player's hotbar for quick access to consumable items or skills.

    This class extends the base Inventory to provide a permanently visible, bottom-aligned grid.
    It supports mouse wheel scrolling, hotkey activation (1-9, 0), and active slot highlighting.

    Attributes:
        app (App):
            Reference to the main application instance.
        active_slot_index (int):
            The index of the currently highlighted and active slot (from 0 to columns - 1).

    Methods:
        __init__(app):
            Initialize the hotbar object, calculating its layout and dimensions.
        scroll_active_slot(y_direction):
            Update the active slot index based on mouse wheel movement.
            Args:
                y_direction (int): The scroll direction (-1 or 1).
        use_active_slot():
            Consume or activate the item in the currently highlighted slot.
        handle_hotkeys(event):
            Process keyboard events to map number keys to specific slots.
            Args:
                event (pygame.event.Event): The Pygame event to process.
        _use_hotbar_item(col):
            Execute the logic for using a consumable item from a specific slot.
            Args:
                col (int): The column index of the slot to use.
        draw(screen):
            Render the hotbar background, slots, keybind numbers, and the active slot highlight.
            Args:
                screen (pygame.Surface): The surface to draw the hotbar on.
    """
    def __init__(self, app: "App"):
        self.app = app
        
        columns = getattr(cfg, 'HOTBAR_columns', 10)
        rows = 1
        
        scale = 0.8
        slot_size = int(cfg.BASE_INV_slot_size * scale)
        border = cfg.BASE_INV_border
        total_width = (slot_size + border) * columns + border
        
        pos_x = ((cfg.SCREEN_WIDTH - total_width) // 2)
        pos_y = cfg.SCREEN_HEIGHT - slot_size - 17
        
        if not hasattr(app, 'MAIN_HOTBAR_items'):
            app.MAIN_HOTBAR_items = [[None for _ in range(rows)] for _ in range(columns)]

        super().__init__(
            columns,
            rows,
            app.MAIN_HOTBAR_items,
            slot_size,
            pos_x,
            pos_y,
            border,
            cfg.BASE_INV_slot_color,
            cfg.BASE_INV_border_color
        )
        
        self.active_slot_index = 0

    def scroll_active_slot(self, y_direction):
        self.active_slot_index -= y_direction
        self.active_slot_index %= self.columns

    def use_active_slot(self):
        self._use_hotbar_item(self.active_slot_index)

    def handle_hotkeys(self, event):
        if event.type != pygame.KEYDOWN:
            return
            
        key_map = {
            pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
            pygame.K_4: 3, pygame.K_5: 4, pygame.K_6: 5,
            pygame.K_7: 6, pygame.K_8: 7, pygame.K_9: 8,
            pygame.K_0: 9
        }
        
        if event.key in key_map:
            col = key_map[event.key]
            if col < self.columns:
                self.active_slot_index = col
                self._use_hotbar_item(col)
                
    def _use_hotbar_item(self, col):
        slot = self.items[col][0]
        if slot:
            item, count = slot
            if isinstance(item, Consumable):
                game_state = self.app.manager.states.get("gameplay")
                if game_state:
                    if item.use(game_state.character):
                        slot[1] -= 1
                        logger.info(f"Used consumable {item.id} from hotbar")
                        if slot[1] <= 0:
                            self.items[col][0] = None

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            cfg.MAIN_INV_BACKGROUND,
            (self.pos_x - 10, self.pos_y - 25,
             (self.slot_size + self.border) * self.columns + self.border + 20,
             (self.slot_size + self.border) * self.rows + self.border + 35),
            0, 10
        )
        
        super().draw(screen)

        for i in range(self.columns):
            key_text = str((i + 1) % 10)
            text_surf = cfg.INV_nums_font.render(key_text, True, (200, 200, 200))
            rect_x = self.pos_x + (self.slot_size + self.border) * i + self.border
            screen.blit(text_surf, (rect_x + 5, self.pos_y - 18))

        active_rect_x = self.pos_x + (self.slot_size + self.border) * self.active_slot_index + self.border
        active_rect_y = self.pos_y + self.border
        
        pygame.draw.rect(
            screen, 
            (255, 215, 0), 
            (active_rect_x, active_rect_y, self.slot_size, self.slot_size), 
            3,
            border_radius=2
        )

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
    def __init__(self, app):
        self.app = app
        self.selected_item = None
        self.active_split_popup = None
        self.active_inventories: list[Inventory|None] = []
        self.player_inventory_opened: bool = False
        self.current_shop_inv: Inventory|None = None
        
        self.hotbar = None
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

        if self.hotbar:
            self.hotbar.handle_hotkeys(event)

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
            if self.current_shop_inv:
                self.remove_active_inventory(self.current_shop_inv)
                self.current_shop_inv = None
                pl_inv.pos_x = cfg.MAIN_INV_pos_x

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
            if self.current_shop_inv is shop_inv:
                self.current_shop_inv = None
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
            self.current_shop_inv = shop_inv
    
    def PLAYER_inventory_open(self,event: pygame.event.Event,pl_inv,equip_inv):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i:
                self.toggle_inventory(pl_inv, equip_inv)

        if self.player_inventory_opened is True:
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                self.handle_event(event)