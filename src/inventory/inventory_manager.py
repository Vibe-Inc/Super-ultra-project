import math
import pygame
import src.config as cfg
from src.ui.widgets import Tooltip, Button
from src.inventory.system import Inventory_slider, ShopInventory, MAIN_player_inventory, MAIN_player_inventory_equipment, MAIN_player_hotbar
from src.inventory.inventory_renderer import InventoryRenderer


class Split_popup_model:
    """
    Manages the logic and state of the item split popup interface.

    Provides a slider-driven popup that lets the player split a stack of
    items, leaving a chosen amount in the original slot and putting the
    remainder into the inventory manager's held-item slot.

    Attributes:
        manager (INVENTORY_manager):
            The inventory manager that owns this popup.
        slot_ref (list):
            Reference to the slot being split (item, total_count).
        item_obj (Item):
            Item stored in the slot being split.
        total_count (int):
            Total stack size available to split.
        width (int):
            Calculated pixel width of the popup window.
        height (int):
            Calculated pixel height of the popup window.
        x (int):
            Pixel x-coordinate of the popup window.
        y (int):
            Pixel y-coordinate of the popup window.
        bg_rect (pygame.Rect):
            Background rectangle bounding the popup.
        split_amount (int):
            Currently selected split amount.
        slider (Inventory_slider):
            Slider widget used to choose the split amount.
        confirm_btn (Button):
            Button widget used to confirm the split.

    Methods:
        __init__(manager, slot_ref, rect_pos):
            Build the popup, its slider, and its confirm button.
        update_count(int_val):
            Update :pyattr:`split_amount` from the slider callback.
        confirm():
            Apply the split to the slot and the inventory manager.
        handle_event(event):
            Route pygame events to the slider and confirm button.
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
            rect=pygame.Rect(self.x + int(40 * scale), self.y + int(65 * scale), max(20, int(100 * scale)), max(8, int(22 * scale))),
            text="Confirm", color=cfg.INV_SPLIT_POPUP_BTN_COLOR, hover_color=cfg.INV_SPLIT_POPUP_BTN_HOVER_COLOR,
            font=cfg.INV_nums_font, font_color=cfg.INV_SPLIT_POPUP_BTN_FONT_COLOR,
            corner_width=max(2, int(cfg.INV_SPLIT_POPUP_BTN_CORNER_WIDTH_SCALE * scale)), on_click=self.confirm
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

    Coordinates the active inventories (main, equipment, hotbar, shop,
    crafting), the held/dragged item, tooltips, split popups, the
    overlay backdrop, and the Q-drop shortcuts.

    Attributes:
        app (App):
            The main application reference.
        selected_item (list):
            Currently held (dragged) item and its count, or None.
        active_split_popup (Split_popup_model):
            The currently open split popup, if any.
        active_inventories (list):
            All currently opened inventory instances.
        player_inventory_opened (bool):
            Whether the player's main inventory is currently shown.
        current_shop_inv (ShopInventory):
            The currently open shop inventory, if any.
        hotbar (MAIN_player_hotbar):
            The player's action hotbar instance.
        crafting_system (CraftingGrid):
            The 3x3 crafting grid bound to the player's inventory.
        renderer (InventoryRenderer):
            Renderer used to draw all inventory UI.
        overlay_alpha (float):
            Current alpha of the background dimming overlay.
        target_alpha (float):
            Target alpha for the background overlay fade.
        inventory_tooltip (Tooltip):
            Tooltip widget used to show item info on hover.

    Methods:
        __init__(app):
            Initialize the manager, renderer, crafting grid, and tooltip.
        add_active_inventory(inventory):
            Register an inventory for rendering and event routing.
        remove_active_inventory(inventory):
            Unregister an inventory from the manager.
        draw(screen):
            Render the overlay, inventories, dragged item, tooltip, popups.
        handle_event(event):
            Distribute events to crafting, hotbar, and active inventories.
        _compute_drop_position(game_state, drop_distance=None):
            Compute the world position a Q-dropped item should land at.
        drop_item_data(item_data, drop_distance=None):
            Drop a given [item, count] pair on the ground near the player.
        drop_selected_item(drop_distance=None):
            Drop the currently held (selected) item on the ground.
        toggle_inventory(pl_inv, equip_inv):
            Open or close the player's main and equipment inventories.
        toggle_trade(pl_inv, shop_inv, equip_inv=None):
            Open or close the trading interface with a shop.
        get_item_under_mouse():
            Return the (inventory, col, row, slot) under the cursor, or None.
        take_item_from_under_mouse():
            Pop and return the [item, count] pair from the hovered slot.
        take_active_hotbar_item():
            Pop and return the [item, count] pair from the active hotbar slot.
        PLAYER_inventory_open(event, pl_inv, equip_inv):
            Handle the I hotkey for toggling the inventory screen.
    """

    def __init__(self, app):
        self.app = app
        self.selected_item = None
        self._held_source = None
        self.active_split_popup = None
        self.active_inventories = []
        self.player_inventory_opened = False

        self.current_shop_inv = None
        self.hotbar = None

        from src.inventory.system import CraftingGrid
        self.crafting_system = CraftingGrid(app)

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

                equip_inv = None
                for active_inv in self.active_inventories:
                    if isinstance(active_inv, MAIN_player_inventory_equipment):
                        equip_inv = active_inv
                        break

                scale = cfg.ui_scale()
                craft_width = (self.crafting_system.slot_size + self.crafting_system.border) * 3

                if equip_inv:
                    craft_x = equip_inv.pos_x - craft_width - int(8 * scale)
                    craft_y = equip_inv.pos_y
                else:
                    craft_x = inv.pos_x
                    craft_y = inv.pos_y

                self.crafting_system.update_positions(craft_x, craft_y)
                self.renderer.draw_crafting_system(screen, self.crafting_system)
            elif isinstance(inv, MAIN_player_inventory_equipment):
                self.renderer.draw_equipment(screen, inv)
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
            pygame.draw.circle(shadow, cfg.INV_SELECTED_ITEM_SHADOW_COLOR, (current_size // 2, current_size // 2), current_size // 2 - 4)
            screen.blit(shadow, (mx - current_size // 2, my - current_size // 2))
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
            if not found_item: self.inventory_tooltip.update_target(pygame.Rect(-100, -100, 0, 0), "")
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

    def _compute_drop_position(self, game_state, drop_distance=None):
        if drop_distance is None:
            drop_distance = 120
        from src.entities.dropped_item import DroppedItem
        player = game_state.character
        try:
            player_center = player.get_center()
        except Exception:
            player_center = pygame.Vector2(player.pos.x, player.pos.y)

        forward = None
        try:
            if getattr(player, 'velocity', None) is not None and player.velocity.length_squared() > 0:
                forward = player.velocity.normalize()
        except Exception:
            forward = None
        if forward is None:
            try:
                forward = player.get_forward_direction()
                if forward.length_squared() == 0:
                    forward = None
            except Exception:
                forward = None
        if forward is None:
            try:
                camera_offset = game_state._get_camera_offset()
                mouse_world_pos = pygame.Vector2(pygame.mouse.get_pos()) + camera_offset
                direction = mouse_world_pos - player_center
                if direction.length_squared() > 0:
                    forward = direction.normalize()
            except Exception:
                forward = None
        if forward is None:
            forward = pygame.Vector2(1, 0)

        drop_pos = pygame.Vector2(
            player_center.x + forward.x * drop_distance,
            player_center.y + forward.y * drop_distance - 8,
        )
        return drop_pos

    def drop_item_data(self, item_data, drop_distance=None):
        if not item_data:
            return False
        game_state = self.app.manager.states.get("gameplay")
        if not game_state:
            return False
        from src.entities.dropped_item import DroppedItem
        drop_pos = self._compute_drop_position(game_state, drop_distance)
        item_obj, count = item_data
        dropped_item = DroppedItem(drop_pos.x, drop_pos.y, item_obj, count)
        game_state.items.append(dropped_item)
        return True

    def drop_selected_item(self, drop_distance=None):
        if not self.selected_item:
            return False
        item_data = self.selected_item
        self.selected_item = None
        return self.drop_item_data(item_data, drop_distance)

    def toggle_inventory(self, pl_inv, equip_inv):
        self.player_inventory_opened = not self.player_inventory_opened
        if self.player_inventory_opened:
            pl_inv.pos_x = cfg.MAIN_INV_pos_x
            pl_inv.pos_y = cfg.MAIN_INV_pos_y
            equip_inv.pos_x = cfg.MAIN_INV_equipment_pos_x
            equip_inv.pos_y = cfg.MAIN_INV_equipment_pos_y
            self.add_active_inventory(pl_inv)
            self.add_active_inventory(equip_inv)
        else:
            self._return_held_item()
            self.remove_active_inventory(pl_inv)
            self.remove_active_inventory(equip_inv)
            if self.current_shop_inv:
                self.remove_active_inventory(self.current_shop_inv)
                self.current_shop_inv = None
                pl_inv.pos_x = cfg.MAIN_INV_pos_x
                equip_inv.pos_x = cfg.MAIN_INV_equipment_pos_x

    def _return_held_item(self):
        if self.selected_item and self._held_source:
            src = self._held_source
            inv = src.get('inv')
            col, row = src.get('col'), src.get('row')
            if inv and hasattr(inv, 'items') and 0 <= col < inv.columns and 0 <= row < inv.rows:
                if inv.items[col][row] is None:
                    inv.items[col][row] = self.selected_item
                    self.selected_item = None
        self._held_source = None

    def toggle_trade(self, pl_inv, shop_inv, equip_inv=None):
        if shop_inv in self.active_inventories:
            self._return_held_item()
            self.remove_active_inventory(shop_inv)
            self.remove_active_inventory(pl_inv)
            if equip_inv:
                self.remove_active_inventory(equip_inv)
            pl_inv.pos_x = cfg.MAIN_INV_pos_x
            if equip_inv:
                equip_inv.pos_x = cfg.MAIN_INV_equipment_pos_x
            self.player_inventory_opened = False
            if self.current_shop_inv is shop_inv: self.current_shop_inv = None
        else:
            self.player_inventory_opened = True
            sc = cfg.ui_scale()
            new_pl_inv_x = cfg.SCREEN_WIDTH // 2 - int(500 * sc)
            pl_inv.pos_x = new_pl_inv_x
            if equip_inv:
                equip_offset = cfg.MAIN_INV_equipment_pos_x - cfg.MAIN_INV_pos_x
                equip_inv.pos_x = new_pl_inv_x + equip_offset
            shop_inv.pos_x = cfg.SCREEN_WIDTH // 2 + int(100 * sc)
            shop_inv.pos_y = pl_inv.pos_y
            self.add_active_inventory(pl_inv)
            if equip_inv:
                self.add_active_inventory(equip_inv)
            self.add_active_inventory(shop_inv)
            self.current_shop_inv = shop_inv

    def get_item_under_mouse(self):
        if not self.active_inventories:
            return None
        for inv in self.active_inventories:
            if not hasattr(inv, 'columns') or not hasattr(inv, 'rows'):
                continue
            if hasattr(inv, 'update_position'):
                try:
                    inv.update_position()
                except Exception:
                    pass
            mouse_x, mouse_y = pygame.mouse.get_pos()
            total_width = (inv.slot_size + inv.border) * inv.columns
            total_height = (inv.slot_size + inv.border) * inv.rows
            if not (inv.pos_x <= mouse_x <= inv.pos_x + total_width
                    and inv.pos_y <= mouse_y <= inv.pos_y + total_height):
                continue
            x = (mouse_x - inv.pos_x) // (inv.slot_size + inv.border)
            y = (mouse_y - inv.pos_y) // (inv.slot_size + inv.border)
            if 0 <= x < inv.columns and 0 <= y < inv.rows:
                slot = inv.items[x][y]
                if slot:
                    return inv, x, y, slot
        return None

    def take_item_from_under_mouse(self):
        result = self.get_item_under_mouse()
        if not result:
            return None
        inv, x, y, slot = result
        inv.items[x][y] = None
        return slot

    def take_active_hotbar_item(self):
        hotbar = getattr(self, 'hotbar', None)
        if not hotbar or not hasattr(hotbar, 'active_slot_index'):
            return None
        col = hotbar.active_slot_index
        if not (0 <= col < hotbar.columns):
            return None
        slot = hotbar.items[col][0]
        if not slot:
            return None
        hotbar.items[col][0] = None
        return slot

    def PLAYER_inventory_open(self, event, pl_inv, equip_inv):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
            self.toggle_inventory(pl_inv, equip_inv)
        if self.player_inventory_opened and event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            self.handle_event(event)
       