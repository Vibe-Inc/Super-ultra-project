import math
import copy
import pygame
from typing import TYPE_CHECKING
import src.config as cfg
from src.ui.widgets import Slider, Button
from src.items.items import Consumable, Armor
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
                shift_held = pygame.key.get_mods() & pygame.KMOD_SHIFT

                if shift_held and slot and not manager.selected_item:
                    self._quick_move_slot(x, y, slot, manager)
                    return

                if manager.selected_item:
                    if slot:
                        if slot[0].id == manager.selected_item[0].id:
                            slot[1] += manager.selected_item[1]
                            manager.selected_item = None
                        else:
                            self.items[x][y], manager.selected_item = manager.selected_item, self.items[x][y]
                            manager._held_source = {'inv': self, 'col': x, 'row': y}
                    else:
                        self.items[x][y] = manager.selected_item
                        manager.selected_item = None
                else:
                    if slot:
                        manager.selected_item = slot
                        self.items[x][y] = None
                        manager._held_source = {'inv': self, 'col': x, 'row': y}

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
                elif isinstance(item, Armor):
                    from src.inventory.system import MAIN_player_inventory_equipment
                    equip_inv = None
                    for inv in manager.active_inventories:
                        if isinstance(inv, MAIN_player_inventory_equipment):
                            equip_inv = inv
                            break
                    if equip_inv is None:
                        gs = manager.app.manager.states.get("gameplay")
                        if gs and hasattr(gs, 'PLAYER_inventory_equipment'):
                            equip_inv = gs.PLAYER_inventory_equipment
                    if equip_inv:
                        for ex in range(equip_inv.columns):
                            for ey in range(equip_inv.rows):
                                if equip_inv.get_slot_type(ex, ey) == item.slot_type:
                                    existing = equip_inv.items[ex][ey]
                                    if existing:
                                        equip_inv.items[ex][ey], self.items[x][y] = slot, existing
                                    else:
                                        equip_inv.items[ex][ey] = slot
                                        self.items[x][y] = None
                                    char = getattr(manager.app.manager.states.get("gameplay"), 'character', None)
                                    if char:
                                        equip_inv.sync_character_defense(char)
                                    return

    def _quick_move_slot(self, col, row, slot, manager):
        from src.inventory.system import MAIN_player_hotbar, MAIN_player_inventory, MAIN_player_inventory_equipment

        item, count = slot

        if isinstance(self, MAIN_player_hotbar):
            target_inv = None
            for inv in manager.active_inventories:
                if isinstance(inv, MAIN_player_inventory):
                    target_inv = inv
                    break
            if not target_inv:
                return
            for tx in range(target_inv.columns):
                for ty in range(target_inv.rows):
                    existing = target_inv.items[tx][ty]
                    if existing and existing[0].id == item.id:
                        existing[1] += count
                        self.items[col][row] = None
                        return
            for tx in range(target_inv.columns):
                for ty in range(target_inv.rows):
                    if target_inv.items[tx][ty] is None:
                        target_inv.items[tx][ty] = slot
                        self.items[col][row] = None
                        return

        elif isinstance(self, MAIN_player_inventory_equipment):
            target_inv = None
            for inv in manager.active_inventories:
                if isinstance(inv, MAIN_player_inventory):
                    target_inv = inv
                    break
            if not target_inv:
                return
            for tx in range(target_inv.columns):
                for ty in range(target_inv.rows):
                    existing = target_inv.items[tx][ty]
                    if existing and existing[0].id == item.id:
                        existing[1] += count
                        self.items[col][row] = None
                        return
            for tx in range(target_inv.columns):
                for ty in range(target_inv.rows):
                    if target_inv.items[tx][ty] is None:
                        target_inv.items[tx][ty] = slot
                        self.items[col][row] = None
                        return

        elif isinstance(self, MAIN_player_inventory):
            if isinstance(item, Armor) and hasattr(item, 'slot_type'):
                equip_inv = None
                for inv in manager.active_inventories:
                    if isinstance(inv, MAIN_player_inventory_equipment):
                        equip_inv = inv
                        break
                if equip_inv:
                    for ex in range(equip_inv.columns):
                        for ey in range(equip_inv.rows):
                            if equip_inv.get_slot_type(ex, ey) == item.slot_type:
                                existing = equip_inv.items[ex][ey]
                                if existing:
                                    equip_inv.items[ex][ey], self.items[col][row] = slot, existing
                                else:
                                    equip_inv.items[ex][ey] = slot
                                    self.items[col][row] = None
                                char = getattr(manager.app.manager.states.get("gameplay"), 'character', None)
                                if char:
                                    equip_inv.sync_character_defense(char)
                                return

            target_inv = manager.hotbar
            if not target_inv:
                return
            for tx in range(target_inv.columns):
                for ty in range(target_inv.rows):
                    existing = target_inv.items[tx][ty]
                    if existing and existing[0].id == item.id:
                        existing[1] += count
                        self.items[col][row] = None
                        return
            for tx in range(target_inv.columns):
                for ty in range(target_inv.rows):
                    if target_inv.items[tx][ty] is None:
                        target_inv.items[tx][ty] = slot
                        self.items[col][row] = None
                        return

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
        scale = cfg.ui_scale()
        rows, columns = 4, 4
        items_grid = [[None for _ in range(rows)] for _ in range(columns)]
        for i, item in enumerate(items_list):
            x, y = i % columns, i // columns
            if y < rows: items_grid[x][y] = [item, 1]

        super().__init__(
            columns, rows, items_grid,
            int(cfg.BASE_INV_slot_size * scale), 0, 0,
            int(cfg.BASE_INV_border * scale)
        )
        btn_w, btn_h = max(80, int(140 * scale)), max(28, int(38 * scale))
        self.close_button = Button(
            rect=pygame.Rect(0, 0, btn_w, btn_h),
            text=_("LEAVE SHOP"), color=cfg.INV_SHOP_CLOSE_BTN_COLOR,
            hover_color=cfg.INV_SHOP_CLOSE_BTN_HOVER_COLOR,
            font=cfg.INV_nums_font, font_color=cfg.INV_SHOP_CLOSE_BTN_FONT_COLOR,
            corner_width=max(2, int(8 * scale)), on_click=self._close_shop
        )

    def rescale(self):
        """Recompute slot_size, border, and the close button for the current UI scale."""
        scale = cfg.ui_scale()
        self.slot_size = int(cfg.BASE_INV_slot_size * scale)
        self.border = int(cfg.BASE_INV_border * scale)
        btn_w, btn_h = max(80, int(140 * scale)), max(28, int(38 * scale))
        self.close_button.rect.width = btn_w
        self.close_button.rect.height = btn_h
        self.close_button.corner_width = max(2, int(8 * scale))
        self.close_button.font = cfg.INV_nums_font
        self.close_button._update_text_surface()

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
                shift_held = pygame.key.get_mods() & pygame.KMOD_SHIFT

                if shift_held and slot and not manager.selected_item:
                    from src.inventory.system import MAIN_player_inventory
                    shop_item = slot[0]
                    buy_price = getattr(shop_item, 'price', 0)
                    if self.app.money >= buy_price:
                        pl_inv = None
                        for inv in manager.active_inventories:
                            if isinstance(inv, MAIN_player_inventory):
                                pl_inv = inv
                                break
                        if pl_inv:
                            for tx in range(pl_inv.columns):
                                for ty in range(pl_inv.rows):
                                    existing = pl_inv.items[tx][ty]
                                    if existing and existing[0].id == shop_item.id:
                                        existing[1] += 1
                                        self.app.money -= buy_price
                                        return
                            for tx in range(pl_inv.columns):
                                for ty in range(pl_inv.rows):
                                    if pl_inv.items[tx][ty] is None:
                                        pl_inv.items[tx][ty] = [copy.copy(shop_item), 1]
                                        self.app.money -= buy_price
                                        return
                    return

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
            if game_state: self.app.INV_manager.toggle_trade(game_state.MAIN_player_inv, self, game_state.PLAYER_inventory_equipment)
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
        scale = cfg.ui_scale()
        super().__init__(
            cfg.MAIN_INV_columns, cfg.MAIN_INV_rows, app.MAIN_INV_items,
            int(cfg.BASE_INV_slot_size * scale), cfg.MAIN_INV_pos_x, cfg.MAIN_INV_pos_y,
            int(cfg.BASE_INV_border * scale)
        )
        btn_w = max(20, int(cfg.INV_PLAYER_RIGHT_BTN_WIDTH * scale))
        btn_h = max(8, int(cfg.INV_PLAYER_RIGHT_BTN_HEIGHT * scale))
        
        self.open_skillbar_btn = Button(
            rect=pygame.Rect(0, 0, btn_w, btn_h),
            text=_("SKILLS & MAGIC"), color=cfg.INV_SKILLBAR_BTN_COLOR,
            hover_color=cfg.INV_SKILLBAR_BTN_HOVER_COLOR,
            font=cfg.get_font(max(10, int(22 * scale))), font_color=cfg.INV_SKILLBAR_BTN_FONT_COLOR,
            corner_width=max(2, int(8 * scale)), on_click=None
        )
        self.open_skilltree_btn = Button(
            rect=pygame.Rect(0, 0, btn_w, btn_h),
            text=_("TALENT TREE"), color=cfg.INV_SKILLTREE_BTN_COLOR,
            hover_color=cfg.INV_SKILLTREE_BTN_HOVER_COLOR,
            font=cfg.get_font(max(10, int(22 * scale))), font_color=cfg.INV_SKILLTREE_BTN_FONT_COLOR,
            corner_width=max(2, int(8 * scale)), on_click=None
        )
        # Magical ARCANE QUESTS button (gold & purple theme) — opens the new
        # ArcaneQuestMenu (registered in StateManager as the "arcane_quest" state).
        self.open_arcane_quest_btn = Button(
            rect=pygame.Rect(0, 0, btn_w, btn_h),
            text=_("ARCANE QUESTS"),
            color=cfg.INV_ARCANEQUEST_BTN_COLOR,
            hover_color=cfg.INV_ARCANEQUEST_BTN_HOVER_COLOR,
            font=cfg.get_font(max(10, int(22 * scale))),
            font_color=cfg.INV_ARCANEQUEST_BTN_FONT_COLOR,
            corner_width=max(2, int(8 * scale)),
            on_click=None,
        )
        # Mystical MYSTERIUM MAGNUM button (cards theme) — opens the
        # MysteriumMagnumMenu (registered in StateManager as "mysterium_magnum").
        self.open_mysterium_magnum_btn = Button(
            rect=pygame.Rect(0, 0, btn_w, btn_h),
            text=_("MYSTERIUM MAGNUM"),
            color=cfg.INV_MYSTERIUMMAGNUM_BTN_COLOR,
            hover_color=cfg.INV_MYSTERIUMMAGNUM_BTN_HOVER_COLOR,
            font=cfg.get_font(max(10, int(22 * scale))),
            font_color=cfg.INV_MYSTERIUMMAGNUM_BTN_FONT_COLOR,
            corner_width=max(2, int(8 * scale)),
            on_click=None,
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
                if hasattr(self, 'open_arcane_quest_btn') and self.open_arcane_quest_btn.rect.collidepoint(mouse_pos):
                    if getattr(self.app, 'arcane_quests_unlocked', False):
                        try: self.app.manager.set_state("arcane_quest")
                        except Exception: pass
                    return
                if hasattr(self, 'open_mysterium_magnum_btn') and self.open_mysterium_magnum_btn.rect.collidepoint(mouse_pos):
                    if getattr(self.app, 'mysterium_magnum_unlocked', False):
                        try: self.app.manager.set_state("mysterium_magnum")
                        except Exception: pass
                    return
        return super().inventory_interactions(event, manager)

class MAIN_player_inventory_equipment(Inventory):
    """
    Manages the player's equipment loadout slots.

    A specialized grid intended strictly for equippable armor and accessory items.
    Each slot position is typed (helmet, chestplate, leggings, boots in column 1;
    charm, gloves, ring, belt in column 0). Only Armor items with matching
    slot_type may be placed in each slot.

    Attributes:
        app (App): Reference to the main application instance.

    Methods:
        __init__(app):
            Initialize the equipment inventory grid based on config dimensions.
        get_slot_type(col, row):
            Return the slot type string for the given grid position.
        get_total_defense():
            Sum the defense_value of all equipped Armor items.
        inventory_interactions(event, manager):
            Validate slot type before allowing item placement.
        sync_character_defense(character):
            Recalculate and apply total defense from equipped armor.
    """
    def __init__(self, app: "App"):
        scale = cfg.ui_scale()
        super().__init__(
            cfg.MAIN_INV_equipment_columns, cfg.MAIN_INV_equipment_rows, None,
            int(cfg.BASE_INV_slot_size * scale), cfg.MAIN_INV_equipment_pos_x, cfg.MAIN_INV_equipment_pos_y,
            int(cfg.BASE_INV_border * scale)
        )
        self.app = app

    def get_slot_type(self, col: int, row: int) -> str:
        """Return the slot type for the given grid position."""
        if 0 <= col < len(cfg.EQUIPMENT_SLOT_TYPES) and 0 <= row < len(cfg.EQUIPMENT_SLOT_TYPES[col]):
            return cfg.EQUIPMENT_SLOT_TYPES[col][row]
        return "unknown"

    def get_total_defense(self) -> int:
        """Sum the *effective* defense of all equipped Armor items.

        Each :class:`Armor` instance scales its ``defense_value`` by
        the remaining durability via
        :py:meth:`src.items.items.Armor.get_effective_defense`, so a
        worn-down chestplate contributes proportionally less -- and a
        broken piece contributes the floor value (50% by default)
        rather than zero.  The sum is what gets written to
        ``character.defense`` by :py:meth:`sync_character_defense`.
        """
        total = 0
        for col in range(self.columns):
            for row in range(self.rows):
                slot = self.items[col][row]
                if slot and isinstance(slot[0], Armor):
                    total += slot[0].get_effective_defense()
        return total

    def sync_character_defense(self, character) -> None:
        """Recalculate character.defense from all equipped armor.

        Uses the durability-scaled (effective) defense, not the raw
        ``defense_value``, so worn pieces immediately show up in the
        player's stat without waiting for the next equip change.
        """
        character.defense = self.get_total_defense()

    def damage_equipped_armor(self, amount: int = 1, source: str = "hit") -> list:
        """Reduce the durability of every equipped armor piece by
        ``amount``.

        Called from :py:meth:`src.entities.character.Character.take_damage`
        so each incoming hit chips a point off every worn piece.  A
        broken piece (zero durability) is left alone -- we already
        reported the break to the player; a second hit shouldn't
        re-fire the same floating text.  Unbreakable pieces are
        skipped entirely.

        After damage is applied the function re-syncs ``character.defense``
        via :py:meth:`sync_character_defense` so the in-flight
        :py:meth:`take_damage` reduction picks up the new (lower) defense
        on subsequent hits in the same frame.

        Args:
            amount: How many durability points to subtract per piece.
                Must be a positive integer; non-positive values are a
                no-op.
            source: Short string used only for log messages ("hit",
                "fall", ...).  Doesn't change behaviour.

        Returns:
            A list of ``(col, row, item, broke_now)`` tuples for every
            piece that lost durability on this call, so the caller can
            fire "X just broke!" popups without having to re-walk the
            grid.  An empty list means nothing was equipped (or every
            piece was unbreakable).
        """
        if amount is None or amount <= 0:
            return []
        results: list = []
        for col in range(self.columns):
            for row in range(self.rows):
                slot = self.items[col][row]
                if not slot:
                    continue
                item = slot[0]
                if not isinstance(item, Armor):
                    continue
                if getattr(item, "unbreakable", False):
                    continue
                was_broken = bool(getattr(item, "is_broken", lambda: False)())
                apply = getattr(item, "apply_durability_damage", None)
                if not callable(apply):
                    continue
                apply(int(amount))
                is_broken_now = bool(getattr(item, "is_broken", lambda: False)())
                if not was_broken and is_broken_now:
                    results.append((col, row, item, True))
        return results

    def inventory_interactions(self, event, manager):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()
        x = (mouse_x - self.pos_x) // (self.slot_size + self.border)
        y = (mouse_y - self.pos_y) // (self.slot_size + self.border)

        if not (0 <= x < self.columns and 0 <= y < self.rows):
            return

        slot = self.items[x][y]

        if event.button == 1:
            shift_held = pygame.key.get_mods() & pygame.KMOD_SHIFT

            if shift_held and slot and not manager.selected_item:
                self._quick_move_slot(x, y, slot, manager)
                return

            if manager.selected_item:
                dragged_item = manager.selected_item[0]
                slot_type = self.get_slot_type(x, y)

                # Only allow placing Armor items with matching slot_type
                if isinstance(dragged_item, Armor) and dragged_item.slot_type == slot_type:
                    if slot:
                        if slot[0].id == dragged_item.id:
                            slot[1] += manager.selected_item[1]
                            manager.selected_item = None
                        else:
                            self.items[x][y], manager.selected_item = manager.selected_item, self.items[x][y]
                            manager._held_source = {'inv': self, 'col': x, 'row': y}
                    else:
                        self.items[x][y] = manager.selected_item
                        manager.selected_item = None
                elif slot and slot[0] is dragged_item:
                    self.items[x][y], manager.selected_item = manager.selected_item, self.items[x][y]
                    manager._held_source = {'inv': self, 'col': x, 'row': y}
            else:
                if slot:
                    manager.selected_item = slot
                    self.items[x][y] = None
                    manager._held_source = {'inv': self, 'col': x, 'row': y}

            # Sync character defense after any equipment change
            game_state = manager.app.manager.states.get("gameplay")
            if game_state and hasattr(game_state, 'character'):
                self.sync_character_defense(game_state.character)

        elif event.button == 3 and slot and not manager.selected_item:
            item, count = slot
            if isinstance(item, Consumable):
                game_state = getattr(manager.app.manager.states.get("gameplay"), 'character', None)
                if game_state and item.use(game_state):
                    slot[1] -= 1
                    if slot[1] <= 0:
                        self.items[x][y] = None
            elif isinstance(item, Armor):
                hb = manager.hotbar
                if hb:
                    for hx in range(hb.columns):
                        for hy in range(hb.rows):
                            existing = hb.items[hx][hy]
                            if existing and existing[0].id == item.id:
                                existing[1] += count
                                self.items[x][y] = None
                                char = getattr(manager.app.manager.states.get("gameplay"), 'character', None)
                                if char: self.sync_character_defense(char)
                                return
                    for hx in range(hb.columns):
                        for hy in range(hb.rows):
                            if hb.items[hx][hy] is None:
                                hb.items[hx][hy] = slot
                                self.items[x][y] = None
                                char = getattr(manager.app.manager.states.get("gameplay"), 'character', None)
                                if char: self.sync_character_defense(char)
                                return
                    hb_active = hb.items[hb.active_slot_index][0]
                    hb.items[hb.active_slot_index][0] = slot
                    self.items[x][y] = hb_active
                    char = getattr(manager.app.manager.states.get("gameplay"), 'character', None)
                    if char: self.sync_character_defense(char)

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
        scale = cfg.INV_HOTBAR_SCALE * cfg.ui_scale()
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
        elif slot and isinstance(slot[0], Armor):
            from src.inventory.system import MAIN_player_inventory_equipment
            game_state = self.app.manager.states.get("gameplay")
            if not game_state:
                return
            equip_inv = game_state.PLAYER_inventory_equipment
            if equip_inv:
                item = slot[0]
                for ex in range(equip_inv.columns):
                    for ey in range(equip_inv.rows):
                        if equip_inv.get_slot_type(ex, ey) == item.slot_type:
                            existing = equip_inv.items[ex][ey]
                            if existing:
                                equip_inv.items[ex][ey], self.items[col][0] = slot, existing
                            else:
                                equip_inv.items[ex][ey] = slot
                                self.items[col][0] = None
                            char = getattr(game_state, 'character', None)
                            if char:
                                equip_inv.sync_character_defense(char)
                            return

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
    """
    Manages the 3x3 crafting grid interface.

    Handles recipe matching, ingredient validation, and item crafting mechanics.
    Displays available recipes via a recipe book and processes crafting transactions.

    Attributes:
        app (App):
            The main application reference.
        output_slot (list):
            The crafted item and count displayed in the output slot, or None if empty.
        all_recipes (list):
            All available recipes loaded from the database.
        book_button (Button):
            Button widget to open the recipe book menu.
        pos_x (int):
            The x-coordinate position of the crafting grid on screen.
        pos_y (int):
            The y-coordinate position of the crafting grid on screen.
        output_pos_x (int):
            The x-coordinate position of the output slot.
        output_pos_y (int):
            The y-coordinate position of the output slot.

    Methods:
        __init__(app):
            Initialize the crafting grid, database connection, and recipe book button.
        open_recipe_menu():
            Transition to the recipe book menu state.
        update_positions(base_x, base_y):
            Recalculate grid and output slot positions based on anchor coordinates.
        inventory_interactions(event, manager):
            Handle recipe book button clicks, output slot interactions, and crafting.
        check_recipes():
            Scan the crafting matrix for matching recipes and update the output slot.
        _matrix_match(m1, m2):
            Compare two 3x3 matrices for equality.
    """
    def __init__(self, app):
        scale = cfg.ui_scale()
        super().__init__(3, 3, None,
            int(cfg.BASE_INV_slot_size * scale), 0, 0,
            int(cfg.BASE_INV_border * scale))
        self.app = app
        self.output_slot = None
        
        self.pos_x = 0
        self.pos_y = 0
        self.output_pos_x = 0
        self.output_pos_y = 0
        
        db = Gp_database()
        self.all_recipes = db.get_all_recipes()
        db.close()
        btn_size = int(self.slot_size * 0.85)
        self.book_button = Button(
            rect=pygame.Rect(0, 0, btn_size, btn_size),
            text="",
            color=(40, 25, 10), hover_color=(60, 40, 20),
            font=cfg.INV_nums_font, font_color=(255, 215, 0),
            corner_width=max(2, int(cfg.INV_SLOT_BORDER_RADIUS * 0.75)),
            on_click=self.open_recipe_menu
        )
        

    def open_recipe_menu(self):
        self.app.manager.set_state("recipe_book")

    def rescale(self):
        """Recompute slot_size, border, and the recipe book button for the current UI scale."""
        scale = cfg.ui_scale()
        self.slot_size = int(cfg.BASE_INV_slot_size * scale)
        self.border = int(cfg.BASE_INV_border * scale)
        btn_size = int(self.slot_size * 0.85)
        self.book_button.rect.width = btn_size
        self.book_button.rect.height = btn_size
        self.book_button.corner_width = max(2, int(cfg.INV_SLOT_BORDER_RADIUS * 0.75))
        self.book_button.font = cfg.INV_nums_font
        self.book_button._update_text_surface()

    def update_positions(self, base_x, base_y):
        scale = cfg.ui_scale()
        self.pos_x = base_x
        self.pos_y = base_y
        
        grid_size = (self.slot_size + self.border) * 3
        
        self.output_pos_x = self.pos_x + (grid_size // 2) - (self.slot_size // 2)
        self.output_pos_y = self.pos_y + grid_size + int(15 * scale)
        btn_y = self.output_pos_y + (self.slot_size - self.book_button.rect.height) // 2 - int(2 * scale)
        
        btn_x = self.output_pos_x + self.slot_size + int(12 * scale)
        
        self.book_button.rect.topleft = (btn_x, btn_y)

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
                
                # Guide: Crafting & Recipes — first item crafted
                gs = self.app.manager.states.get("gameplay")
                if gs and not gs._triggered_guide_crafting:
                    gs._triggered_guide_crafting = True
                    self.app.article_tracker.try_open(self.app, "guide", "5. Crafting & Recipes")
                
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
        for c in range(3):
            for r in range(3):
                if m1[c][r] != m2[c][r]:
                    return False
        return True

class CraftingLogic:
    """
    Utility class for crafting validation and ingredient management.

    Provides static methods to validate crafting requirements, consume ingredients,
    and add crafted items to the player inventory.

    Methods:
        can_craft(player_inv, ingredients):
            Check if the player has sufficient items to craft a recipe.
        consume_ingredients(player_inv, ingredients):
            Remove required ingredients from the player inventory.
        add_crafted_item(player_inv, result_item, amount):
            Add the crafted item to available inventory slots or create new slots.
    """
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
        for row in range(player_inv.rows):
            for col in range(player_inv.columns):
                slot = player_inv.items[col][row]
                if slot and slot[0].id == result_item.id:
                    slot[1] += amount
                    return True

        for row in range(player_inv.rows):
            for col in range(player_inv.columns):
                if player_inv.items[col][row] is None:
                    import copy
                    player_inv.items[col][row] = [copy.copy(result_item), amount]
                    return True
        return False
