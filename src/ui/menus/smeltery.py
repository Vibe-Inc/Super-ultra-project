"""
Smeltery workstation interface.

The smeltery is opened by the player pressing ``E`` while standing next
to a tile carrying the ``Is_smeltery_workstation`` custom property.
While the smeltery is open it acts as an overlay: the game loop keeps
ticking so smelting timers advance in real time, but events and draw
calls are routed through this module.

Three tool stations are exposed via a tab bar at the top of the panel:

* **Workbench** -- the standard 3x3 shaped crafting grid (re-uses
  ``CraftingGrid`` and the player inventory through the inventory
  manager).
* **Coke Oven** -- a single-input furnace. One item slot on the left,
  one output slot on the right, a real-time progress bar and flame
  glow.
* **Blast Furnace** -- a two-input furnace. Material slot on the top
  left, fuel slot below it, a shared output slot on the right, with
  the same kind of progress / glow as the coke oven.

Layout and slot chrome follow the existing inventory style: rounded
panels with drop shadows, the same slot background palette, and the
same item-render path that ``InventoryRenderer.draw_base_inventory``
uses.  Only the in-station visuals (furnace frame, flame, progress
bar) are station-specific.
"""

import math
import pygame

import src.config as cfg
from src.core.logger import logger
from src.inventory.inventory_renderer import draw_panel_with_shadow
from database.smeltery_recipes_db import (
    COKE_OVEN_RECIPES,
    BLAST_FURNACE_RECIPES,
    ANVIL_RECIPES,
    get_coke_recipe_for_input,
    get_blast_recipe_for_inputs,
    get_anvil_recipe_for_material,
    get_recipe_minigame_id,
    MINIGAME_NONE,
)


STATION_WORKBENCH = "workbench"
STATION_COKE_OVEN = "coke_oven"
STATION_BLAST_FURNACE = "blast_furnace"
STATION_ANVIL = "anvil"

STATION_LABELS = {
    STATION_WORKBENCH: "Workbench",
    STATION_COKE_OVEN: "Coke Oven",
    STATION_BLAST_FURNACE: "Blast Furnace",
    STATION_ANVIL: "Anvil",
}

STATION_ORDER = [STATION_WORKBENCH, STATION_COKE_OVEN, STATION_BLAST_FURNACE, STATION_ANVIL]


class _FurnaceSlot:
    """A single furnace slot with item + count, mirroring the Inventory
    slot convention ``[Item, int]`` or ``None``."""

    __slots__ = ("item", "count")

    def __init__(self):
        self.item = None
        self.count = 0

    def is_empty(self):
        return self.item is None or self.count <= 0

    def set(self, item, count):
        self.item = item
        self.count = max(0, int(count))

    def clear(self):
        self.item = None
        self.count = 0

    def as_pair(self):
        if self.is_empty():
            return None
        return [self.item, self.count]

    def can_accept(self, item, count):
        """Return True if ``count`` more of ``item`` would fit here.

        An empty slot can accept anything. A non-empty slot only accepts
        the same ``item.id`` and only up to the item's ``max_stack``.
        """
        if item is None or count <= 0:
            return False
        if self.is_empty():
            return True
        if self.item.id != item.id:
            return False
        max_stack = getattr(self.item, "max_stack", 64) or 64
        return self.count + count <= max_stack


class _FurnaceJob:
    """Tracks an active smelting job for a single furnace."""

    __slots__ = (
        "recipe",
        "elapsed",
        "duration",
        "primary_item_id",
        "primary_amount",
        "fired_flash",
    )

    def __init__(self, recipe):
        self.recipe = recipe
        self.elapsed = 0.0
        self.duration = float(recipe.get("duration", 5.0))
        self.primary_item_id = recipe["primary_output_id"]
        self.primary_amount = int(recipe["primary_output_amount"])
        self.fired_flash = 0.0

    def progress(self):
        if self.duration <= 0.0:
            return 1.0
        return min(1.0, self.elapsed / self.duration)


class SmelteryMenu:
    """
    Overlay menu opened by a smeltery workstation tile.

    The instance is owned by :class:`src.core.game.Game` and stays
    alive across open / close cycles so that smelting jobs can keep
    ticking even when the player walks away from the workstation.

    Attributes:
        app (App): Main application reference.
        is_open (bool): True while the overlay is being shown.
        active_station (str): One of ``STATION_*``.
        coke_input / coke_output (_FurnaceSlot): Coke oven slots.
        coke_job (_FurnaceJob | None): Active coke-oven smelting job.
        blast_item / blast_fuel / blast_output (_FurnaceSlot): Blast
            furnace slots.
        blast_job (_FurnaceJob | None): Active blast-furnace smelting
            job.
        tab_buttons (list[Button]): Station selector buttons.
        close_button (Button): The "X" button that closes the overlay.
    """

    PANEL_MARGIN = 24

    def __init__(self, app):
        from src.ui.widgets import Button
        from src.inventory.system import CraftingGrid

        self.app = app
        self.is_open = False
        self.active_station = STATION_WORKBENCH

        self.coke_input = _FurnaceSlot()
        self.coke_output = _FurnaceSlot()
        self.coke_job = None

        self.blast_item = _FurnaceSlot()
        self.blast_fuel = _FurnaceSlot()
        self.blast_output = _FurnaceSlot()
        self.blast_job = None

        # Anvil: damaged item on the left, repair material in the
        # middle, repaired output on the right.  A separate job
        # (with its own progress bar) ticks in real time.
        self.anvil_item = _FurnaceSlot()
        self.anvil_material = _FurnaceSlot()
        self.anvil_output = _FurnaceSlot()
        self.anvil_job = None
        # The anvil keeps a snapshot of the item being repaired so
        # the progress bar can show the live durability fraction.
        # ``anvil_pending_item`` is set when a job starts and cleared
        # when the output is collected.
        self.anvil_pending_item = None

        # Active smeltery minigame (Tending the Fire / Iron Forge /
        # Quench). The instance drives its own update / draw / event
        # loop; the smeltery is just a host. ``None`` when no minigame
        # is running. While ``active_minigame`` is set, the smeltery
        # blocks input on the rest of its UI and routes events
        # exclusively to the minigame.
        self.active_minigame = None
        # Snapshot of the recipe the active minigame was launched
        # for. Used to apply the bonus output and award XP on close.
        self._active_minigame_recipe = None
        # The output slot the bonus should be added to (coke vs.
        # blast). Same key as the ``_FurnaceJob`` primary_item_id.
        self._active_minigame_output_slot = None
        # The amount of XP the batch itself will award once the
        # minigame closes. Cached at launch time so we can apply the
        # multiplier even if the recipe is mutated mid-minigame.
        self._active_minigame_base_xp = 0
        # The :class:`src.systems.smelting_skill.SmeltingSkill` instance
        # that should receive the XP. We resolve the player character
        # once at launch so a save / load during the minigame doesn't
        # lose the reference.
        self._active_minigame_skill = None

        # A dedicated 3x3 CraftingGrid for the workbench tab. Separate
        # from the player inventory's CraftingGrid so the worktable has
        # its own persistent grid state.
        try:
            self.crafting_grid = CraftingGrid(app)
            # Resize to fit inside the workbench body.
            scale = cfg.ui_scale()
            self.crafting_grid.slot_size = int(56 * scale)
            self.crafting_grid.border = int(3 * scale)
            self.crafting_grid.rescale()
        except Exception as exc:
            logger.warning(f"Smeltery: failed to create workbench CraftingGrid: {exc}")
            self.crafting_grid = None

        self._close_button = None
        self._tab_buttons = []
        self._layout_size = None
        self._panel_rect = None
        self._tab_bar_rect = None
        self._workbench_rect = None
        self._coke_rect = None
        self._blast_rect = None
        self._anvil_rect = None
        self._anvil_item_rect = None
        self._anvil_material_rect = None
        self._anvil_output_rect = None
        self._anvil_progress_rect = None
        self._anvil_status_rect = None
        # Skill bar at the bottom of the smeltery panel.
        self._skill_bar_rect = None
        self._skill_label_pos = None

        self._buttons_built = False
        self._ButtonCls = Button

    # ------------------------------------------------------------------ #
    # Layout                                                              #
    # ------------------------------------------------------------------ #

    def _screen_size(self):
        try:
            return self.app.screen.get_width(), self.app.screen.get_height()
        except Exception:
            return cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT

    def _ensure_layout(self):
        """Build the buttons and (re)compute rects on size or inventory
        position change.

        The smeltery panel is anchored to the left side of the player
        inventory and spans the full vertical length of the inventory's
        visual background (the tall panel that holds the portrait,
        grid, and equipment).  This mirrors the shop layout, where the
        merchant panel sits on the right of the inventory.
        """
        sw, sh = self._screen_size()
        pl_inv = self._player_inventory()
        inv_pos = (pl_inv.pos_x, pl_inv.pos_y) if pl_inv is not None else None
        cache_key = (sw, sh, inv_pos)
        if self._buttons_built and self._layout_size == cache_key:
            return

        self._layout_size = cache_key
        scale = cfg.ui_scale()
        Button = self._ButtonCls

        # Outer panel that contains the tab bar + the active station.
        # The smeltery docks to the left edge of the screen and extends
        # rightward until it slightly touches the left edge of the
        # inventory's visual background, spanning the full vertical
        # length of that background.  The inventory stays in its default
        # centered position.
        # Sized to comfortably hold 4 tab labels (the longest being
        # "Blast Furnace") with a bit of margin.
        panel_w = int(560 * scale)
        if pl_inv is not None:
            slot_size = pl_inv.slot_size
            border = pl_inv.border
            inv_grid_h = (slot_size + border) * pl_inv.rows + border
            inv_bg_top = pl_inv.pos_y - int(340 * scale)
            inv_bg_h = inv_grid_h + int(364 * scale)
            inv_bg_left = pl_inv.pos_x - int(24 * scale)

            panel_h = inv_bg_h
            panel_y = inv_bg_top
            panel_x = inv_bg_left - panel_w
            if panel_x < int(20 * scale):
                panel_x = int(20 * scale)
        else:
            panel_h = int(360 * scale)
            panel_x = int(20 * scale)
            panel_y = int(60 * scale)
        self._panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        # Tab bar at the top of the panel.
        tab_h = int(50 * scale)
        self._tab_bar_rect = pygame.Rect(panel_x, panel_y, panel_w, tab_h)

        # Station body rect.
        body_y = panel_y + tab_h
        body_h = panel_h - tab_h
        self._body_rect = pygame.Rect(panel_x, body_y, panel_w, body_h)

        # Close button at the top-right of the tab bar.
        close_size = int(34 * scale)
        self._close_button = Button(
            pygame.Rect(panel_x + panel_w - close_size - int(8 * scale),
                        panel_y + (tab_h - close_size) // 2,
                        close_size, close_size),
            "X",
            cfg.INV_SHOP_CLOSE_BTN_COLOR,
            cfg.INV_SHOP_CLOSE_BTN_HOVER_COLOR,
            cfg.INV_nums_font,
            cfg.INV_SHOP_CLOSE_BTN_FONT_COLOR,
            max(2, int(6 * scale)),
            on_click=self.close,
        )

        # Three tab buttons evenly distributed across the tab bar.
        self._tab_buttons = []
        tab_count = len(STATION_ORDER)
        tab_pad = int(10 * scale)
        tab_btn_h = tab_h - tab_pad * 2
        tab_total_w = panel_w - int(80 * scale) - tab_pad * (tab_count - 1)
        tab_btn_w = tab_total_w // tab_count
        for i, station in enumerate(STATION_ORDER):
            tx = panel_x + tab_pad + i * (tab_btn_w + tab_pad)
            ty = panel_y + tab_pad
            self._tab_buttons.append(Button(
                pygame.Rect(tx, ty, tab_btn_w, tab_btn_h),
                _(STATION_LABELS[station]),
                (50, 50, 65),
                (90, 90, 115),
                cfg.INV_nums_font,
                (235, 235, 245),
                max(2, int(6 * scale)),
                on_click=lambda s=station: self._set_station(s),
            ))

        # Layout the station bodies.
        self._layout_station_bodies(scale, panel_x, body_y, panel_w, body_h)

        self._buttons_built = True

    def _layout_station_bodies(self, scale, panel_x, body_y, panel_w, body_h):
        """Compute rects for the three station layouts."""
        slot_size = int(56 * scale)
        slot_pad = int(6 * scale)

        # Skill bar at the bottom of the body, shared by every tab.
        # Reserves a strip of height for the smelting level + XP bar
        # so each station body knows how much vertical room it
        # actually has for its own widgets.
        skill_bar_h = int(46 * scale)
        self._skill_bar_rect = pygame.Rect(
            panel_x + int(10 * scale),
            body_y + body_h - skill_bar_h - int(4 * scale),
            panel_w - int(20 * scale),
            skill_bar_h,
        )
        station_body_h = max(0, body_h - skill_bar_h - int(8 * scale))

        # Coke oven: input left, output right, with a progress bar between.
        coke_w = int(420 * scale)
        coke_h = int(140 * scale)
        coke_x = panel_x + (panel_w - coke_w) // 2
        coke_y = body_y + (station_body_h - coke_h) // 2
        self._coke_rect = pygame.Rect(coke_x, coke_y, coke_w, coke_h)

        ci_w = slot_size
        ci_h = slot_size
        ci_x = coke_x + int(24 * scale)
        ci_y = coke_y + (coke_h - ci_h) // 2
        self._coke_input_rect = pygame.Rect(ci_x, ci_y, ci_w, ci_h)

        co_x = coke_x + coke_w - ci_w - int(24 * scale)
        co_y = ci_y
        self._coke_output_rect = pygame.Rect(co_x, co_y, ci_w, ci_h)

        # Progress bar (vertical, fits between slots).
        pb_w = int(18 * scale)
        pb_h = int(86 * scale)
        pb_x = ci_x + ci_w + (co_x - (ci_x + ci_w) - pb_w) // 2
        pb_y = ci_y + (ci_h - pb_h) // 2
        self._coke_progress_rect = pygame.Rect(pb_x, pb_y, pb_w, pb_h)

        # Labels.
        self._coke_input_label_pos = (ci_x + ci_w // 2,
                                       ci_y + ci_h + int(14 * scale))
        self._coke_output_label_pos = (co_x + ci_w // 2,
                                        co_y + ci_h + int(14 * scale))

        # Blast furnace: item + fuel stacked on the left, output on the right.
        blast_w = int(480 * scale)
        blast_h = int(190 * scale)
        blast_x = panel_x + (panel_w - blast_w) // 2
        blast_y = body_y + (station_body_h - blast_h) // 2
        self._blast_rect = pygame.Rect(blast_x, blast_y, blast_w, blast_h)

        # Two input slots stacked vertically on the left.
        bi_w = slot_size
        bi_h = slot_size
        bi_x = blast_x + int(24 * scale)
        bi_y_top = blast_y + int(28 * scale)
        self._blast_item_rect = pygame.Rect(bi_x, bi_y_top, bi_w, bi_h)
        self._blast_fuel_rect = pygame.Rect(bi_x,
                                              bi_y_top + bi_h + slot_pad,
                                              bi_w, bi_h)

        # Output slot on the right.
        bo_x = blast_x + blast_w - bi_w - int(24 * scale)
        bo_y = blast_y + (blast_h - bi_h) // 2
        self._blast_output_rect = pygame.Rect(bo_x, bo_y, bi_w, bi_h)

        # Progress bar (vertical, between inputs and output).
        pb2_w = int(18 * scale)
        pb2_h = int(120 * scale)
        pb2_x = bi_x + bi_w + (bo_x - (bi_x + bi_w) - pb2_w) // 2
        pb2_y = blast_y + (blast_h - pb2_h) // 2
        self._blast_progress_rect = pygame.Rect(pb2_x, pb2_y, pb2_w, pb2_h)

        # Labels.
        self._blast_item_label_pos = (bi_x + bi_w // 2,
                                       bi_y_top - int(14 * scale))
        self._blast_fuel_label_pos = (self._blast_fuel_rect.centerx,
                                       self._blast_fuel_rect.bottom + int(14 * scale))
        self._blast_output_label_pos = (bo_x + bi_w // 2,
                                         bo_y + bi_h + int(14 * scale))

        # Anvil: damaged item on the left, repair material in the middle,
        # repaired output on the right.  A horizontal progress bar sits
        # between the material and the output.
        anvil_w = int(460 * scale)
        anvil_h = int(190 * scale)
        anvil_x = panel_x + (panel_w - anvil_w) // 2
        anvil_y = body_y + (station_body_h - anvil_h) // 2
        self._anvil_rect = pygame.Rect(anvil_x, anvil_y, anvil_w, anvil_h)

        ai_w = slot_size
        ai_h = slot_size
        ai_pad_x = int(28 * scale)
        self._anvil_item_rect = pygame.Rect(
            anvil_x + ai_pad_x,
            anvil_y + (anvil_h - ai_h) // 2,
            ai_w, ai_h,
        )
        self._anvil_material_rect = pygame.Rect(
            anvil_x + (anvil_w - ai_w) // 2,
            anvil_y + (anvil_h - ai_h) // 2,
            ai_w, ai_h,
        )
        self._anvil_output_rect = pygame.Rect(
            anvil_x + anvil_w - ai_w - ai_pad_x,
            anvil_y + (anvil_h - ai_h) // 2,
            ai_w, ai_h,
        )

        # Horizontal progress bar between the material and the output.
        apb_w = int(110 * scale)
        apb_h = int(16 * scale)
        apb_x = self._anvil_material_rect.right + (
            self._anvil_output_rect.left - self._anvil_material_rect.right - apb_w
        ) // 2
        apb_y = self._anvil_material_rect.centery - apb_h // 2
        self._anvil_progress_rect = pygame.Rect(apb_x, apb_y, apb_w, apb_h)

        # Status text rect (used to show repair percentage).
        ast_h = int(20 * scale)
        self._anvil_status_rect = pygame.Rect(
            anvil_x + int(8 * scale),
            anvil_y + anvil_h - ast_h - int(4 * scale),
            anvil_w - int(16 * scale),
            ast_h,
        )

        # Anvil labels.
        self._anvil_item_label_pos = (self._anvil_item_rect.centerx,
                                      self._anvil_item_rect.top - int(14 * scale))
        self._anvil_material_label_pos = (self._anvil_material_rect.centerx,
                                           self._anvil_material_rect.top - int(14 * scale))
        self._anvil_output_label_pos = (self._anvil_output_rect.centerx,
                                        self._anvil_output_rect.top - int(14 * scale))

        # Workbench body rect.
        self._workbench_rect = pygame.Rect(
            panel_x + int(8 * scale),
            body_y + int(8 * scale),
            panel_w - int(16 * scale),
            station_body_h - int(16 * scale),
        )

        # Position the 3x3 CraftingGrid inside the workbench body.
        # Total height the grid needs = grid_size + spacing + output_size
        if self.crafting_grid is not None:
            grid_w = (self.crafting_grid.slot_size + self.crafting_grid.border) * 3
            grid_h = grid_w + int(15 * scale) + self.crafting_grid.slot_size
            base_x = self._workbench_rect.left + (
                self._workbench_rect.width - grid_w
            ) // 2
            base_y = self._workbench_rect.top + (
                self._workbench_rect.height - grid_h
            ) // 2
            self.crafting_grid.update_positions(base_x, base_y)

    # ------------------------------------------------------------------ #
    # State transitions                                                   #
    # ------------------------------------------------------------------ #

    def open(self):
        self.is_open = True
        # Open (and horizontally shift) the player inventory first so the
        # smeltery panel can anchor to its new position.
        self._sync_inv_manager_inventory_open(True)
        self._ensure_layout()

    def close(self):
        self.is_open = False
        # Closing restores the player inventory to its default position.
        self._sync_inv_manager_inventory_open(False)

    def _sync_inv_manager_inventory_open(self, want_open):
        """Open or close the player inventory so items can be moved
        between the player and the smeltery slots."""
        try:
            inv_manager = getattr(self.app, "INV_manager", None)
            if inv_manager is None:
                return
            gs = getattr(self.app.manager, "states", {}).get("gameplay") if getattr(self.app, "manager", None) else None
            if gs is None:
                return
            pl_inv = getattr(gs, "MAIN_player_inv", None)
            equip_inv = getattr(gs, "PLAYER_inventory_equipment", None)
            if pl_inv is None or equip_inv is None:
                return
            currently_open = bool(getattr(inv_manager, "player_inventory_opened", False))
            if want_open and not currently_open:
                inv_manager.toggle_inventory(pl_inv, equip_inv)
            elif not want_open and currently_open:
                inv_manager.toggle_inventory(pl_inv, equip_inv)
            # Apply smeltery-specific horizontal shift so the smeltery
            # panel has room on the left (mirror of the shop's left-shift).
        except Exception as exc:
            logger.debug(f"Smeltery: failed to sync inv manager: {exc}")

    def _set_station(self, station):
        if station in STATION_LABELS:
            self.active_station = station

    # ------------------------------------------------------------------ #
    # Update / smelting ticks                                            #
    # ------------------------------------------------------------------ #

    def update(self, dt):
        """Tick smelting jobs. Called from :class:`Game.update` so the
        timers keep advancing even while the smeltery overlay is closed.
        """
        if self.coke_job is not None:
            self._tick_coke_oven(dt)
        if self.blast_job is not None:
            self._tick_blast_furnace(dt)
        if self.anvil_job is not None:
            self._tick_anvil(dt)

    def _tick_coke_oven(self, dt):
        job = self.coke_job
        if job is None:
            return

        # If the output slot is full of a different item, pause the job.
        # Same-type outputs are allowed to stack up to max_stack.
        if not self.coke_output.is_empty():
            if self.coke_output.item.id != job.primary_item_id:
                return
            max_stack = getattr(self.coke_output.item, "max_stack", 64) or 64
            if self.coke_output.count + job.primary_amount > max_stack:
                return

        job.elapsed += dt
        job.fired_flash = max(0.0, job.fired_flash - dt)
        if job.elapsed >= job.duration:
            self._finish_coke_oven_job()

    def _finish_coke_oven_job(self):
        job = self.coke_job
        if job is None:
            return

        # Re-check: maybe the output became full of a different item
        # between the last tick and now.
        if not self.coke_output.is_empty():
            if self.coke_output.item.id != job.primary_item_id:
                return
            max_stack = getattr(self.coke_output.item, "max_stack", 64) or 64
            if self.coke_output.count + job.primary_amount > max_stack:
                return

        primary_item = self._make_item(job.primary_item_id)
        if primary_item is None:
            logger.warning(f"Smeltery: cannot create primary output {job.primary_item_id!r}")
            self.coke_job = None
            return

        # Stack onto existing output if compatible, else place fresh.
        if self.coke_output.is_empty():
            self.coke_output.set(primary_item, job.primary_amount)
        else:
            max_stack = getattr(self.coke_output.item, "max_stack", 64) or 64
            new_count = min(
                self.coke_output.count + job.primary_amount, max_stack
            )
            self.coke_output.set(self.coke_output.item, new_count)

        self.coke_job = None
        job.fired_flash = 0.6

        # Auto-resume: kick off the next batch if more input is waiting
        # and the output slot can still accept the result.
        self._try_start_coke_job()

    def _tick_blast_furnace(self, dt):
        job = self.blast_job
        if job is None:
            return

        # If the output slot is full of a different item, pause the job.
        # Same-type outputs are allowed to stack up to max_stack.
        if not self.blast_output.is_empty():
            if self.blast_output.item.id != job.primary_item_id:
                return
            max_stack = getattr(self.blast_output.item, "max_stack", 64) or 64
            if self.blast_output.count + job.primary_amount > max_stack:
                return

        job.elapsed += dt
        job.fired_flash = max(0.0, job.fired_flash - dt)
        if job.elapsed >= job.duration:
            self._finish_blast_job()

    def _finish_blast_job(self):
        job = self.blast_job
        if job is None:
            return

        # Re-check: maybe the output became full of a different item
        # between the last tick and now.
        if not self.blast_output.is_empty():
            if self.blast_output.item.id != job.primary_item_id:
                return
            max_stack = getattr(self.blast_output.item, "max_stack", 64) or 64
            if self.blast_output.count + job.primary_amount > max_stack:
                return

        primary_item = self._make_item(job.primary_item_id)
        if primary_item is None:
            logger.warning(f"Smeltery: cannot create primary output {job.primary_item_id!r}")
            self.blast_job = None
            return

        # Stack onto existing output if compatible, else place fresh.
        if self.blast_output.is_empty():
            self.blast_output.set(primary_item, job.primary_amount)
        else:
            max_stack = getattr(self.blast_output.item, "max_stack", 64) or 64
            new_count = min(
                self.blast_output.count + job.primary_amount, max_stack
            )
            self.blast_output.set(self.blast_output.item, new_count)

        self.blast_job = None
        job.fired_flash = 0.6

        # Auto-resume: kick off the next batch if more input/fuel is
        # waiting and the output slot can still accept the result.
        self._try_start_blast_job()

    def _make_item(self, item_id):
        try:
            from src.items.items import create_item
            return create_item(item_id)
        except Exception as exc:
            logger.warning(f"Smeltery: create_item({item_id!r}) failed: {exc}")
            return None

    # ------------------------------------------------------------------ #
    # Smeltery minigame plumbing                                          #
    # ------------------------------------------------------------------ #

    def _get_player_smelting_skill(self):
        """Return the player's :class:`SmeltingSkill` instance or
        ``None`` if it can't be resolved.
        """
        try:
            gs = getattr(self.app.manager, "states", {}).get("gameplay")
            char = getattr(gs, "character", None)
            return getattr(char, "smelting_skill", None)
        except Exception:
            return None

    def _launch_minigame_for(self, recipe, output_slot):
        """Spawn the appropriate smeltery minigame for ``recipe``.

        ``output_slot`` is one of the :class:`_FurnaceSlot` instances
        (coke_output / blast_output) the bonus should be applied to.
        The minigame's :py:meth:`on_close` callback re-enters the
        smeltery via :py:meth:`_finalise_minigame` to apply the
        bonus output and award XP.

        Recipes whose ``minigame`` field is missing or set to
        :data:`MINIGAME_NONE` are silently ignored (no minigame
        launched) so the existing flow continues to work.
        """
        if not recipe:
            return False
        mg_id = get_recipe_minigame_id(recipe)
        if mg_id == MINIGAME_NONE:
            return False
        if self.active_minigame is not None:
            # Don't stack minigames; only one at a time. Drop the
            # bonus in that case (caller will still have the base
            # output already in the slot).
            logger.debug("Smeltery: minigame already running, skipping launch")
            return False

        try:
            from src.minigames.smeltery_minigames import make_smeltery_minigame
        except Exception as exc:
            logger.warning("Smeltery: could not import smeltery minigames: %s", exc)
            return False

        skill = self._get_player_smelting_skill()
        smelting_level = int(getattr(skill, "level", 1) or 1) if skill is not None else 1

        def on_close(outcome, bonus_amount, xp_multiplier):
            self._finalise_minigame(outcome, bonus_amount, xp_multiplier)

        try:
            mg = make_smeltery_minigame(
                self.app,
                recipe,
                on_close=on_close,
                smelting_level=smelting_level,
            )
        except Exception as exc:
            logger.warning("Smeltery: failed to construct minigame: %s", exc)
            return False
        if mg is None:
            return False

        self.active_minigame = mg
        self._active_minigame_recipe = recipe
        self._active_minigame_output_slot = output_slot
        # Cache the base XP so a future recipe mutation doesn't change
        # the awarded amount.
        try:
            from src.systems.smelting_skill import XP_PER_CRAFT
            self._active_minigame_base_xp = int(XP_PER_CRAFT)
        except Exception:
            self._active_minigame_base_xp = 0
        self._active_minigame_skill = skill
        # Auto-open the smeltery panel if the player has walked away
        # so they don't miss the bonus prompt.
        if not self.is_open:
            self.open()
        return True

    def _finalise_minigame(self, outcome, bonus_amount, xp_multiplier):
        """Apply the bonus output and award XP after a minigame closes.

        ``bonus_amount`` units of the recipe's primary output are added
        to :py:attr:`_active_minigame_output_slot` (same slot the base
        batch was placed in).  ``xp_multiplier`` scales the
        :data:`XP_PER_CRAFT` grant.  A bonus of 0 and a multiplier of
        1.0 is the "skipped" path -- the player still gets the base
        batch output already in the slot, but no extra ingots / XP.
        """
        try:
            recipe = self._active_minigame_recipe
            output_slot = self._active_minigame_output_slot
            skill = self._active_minigame_skill
            base_xp = int(self._active_minigame_base_xp or 0)

            # Apply the bonus output to the slot. We must be careful
            # not to exceed the stack cap.
            if recipe and output_slot is not None and bonus_amount and bonus_amount > 0:
                try:
                    primary_id = recipe["primary_output_id"]
                except Exception:
                    primary_id = None
                if primary_id:
                    # If the slot is empty, the bonus becomes the
                    # *only* output of this batch.  The base output
                    # would already be in the slot by this point, so
                    # the more common case is "stack onto the existing
                    # base output".
                    if output_slot.is_empty():
                        # Shouldn't happen -- the base batch output
                        # was already placed -- but handle it anyway.
                        bonus_item = self._make_item(primary_id)
                        if bonus_item is not None:
                            output_slot.set(bonus_item, int(bonus_amount))
                    else:
                        max_stack = getattr(output_slot.item, "max_stack", 64) or 64
                        new_count = min(
                            output_slot.count + int(bonus_amount),
                            max_stack,
                        )
                        output_slot.set(output_slot.item, new_count)

            # Award the (possibly multiplied) XP.
            if skill is not None and base_xp > 0:
                try:
                    award = int(round(base_xp * float(xp_multiplier)))
                    if award > 0:
                        skill.add_xp(award)
                except Exception:
                    pass
        except Exception as exc:
            logger.warning("Smeltery: minigame finalise failed: %s", exc)
        finally:
            # Clear the active minigame state so the next batch can
            # launch its own.
            self.active_minigame = None
            self._active_minigame_recipe = None
            self._active_minigame_output_slot = None
            self._active_minigame_base_xp = 0
            self._active_minigame_skill = None

    # ------------------------------------------------------------------ #
    # Anvil repair flow                                                   #
    # ------------------------------------------------------------------ #

    def _is_repairable(self, item) -> bool:
        """Return True if ``item`` can be placed on the anvil."""
        if item is None:
            return False
        if getattr(item, "unbreakable", False):
            return False
        from src.items.items import Weapon, Armor, Tool
        return isinstance(item, (Weapon, Armor, Tool))

    def _anvil_target_durability(self, item, repair_fraction: float) -> int:
        """Compute the durability value the item will have after the
        repair completes.

        We restore ``repair_fraction`` of ``max_durability`` but never
        overshoot the cap, and we always leave the item with at least
        one point of durability so a "repaired" item is at least usable.
        """
        if item is None:
            return 0
        try:
            cur = int(getattr(item, "durability", 0) or 0)
            mx = int(getattr(item, "max_durability", 0) or 0)
        except Exception:
            return 0
        if mx <= 0:
            return cur
        restore = int(round(mx * float(repair_fraction)))
        new_cur = min(mx, cur + restore)
        if new_cur <= 0 and mx > 0:
            new_cur = 1
        return new_cur

    def _tick_anvil(self, dt):
        """Advance the anvil repair job. Pauses if the output slot
        is occupied by a different item (so the player can still walk
        away with the previous repair in hand)."""
        job = self.anvil_job
        if job is None:
            return
        # If the output slot has a *different* item in it, the job is
        # blocked.  An empty output slot or a same-id slot resumes.
        if not self.anvil_output.is_empty():
            if self.anvil_output.item.id != job.target_item_id:
                return
            max_stack = getattr(self.anvil_output.item, "max_stack", 64) or 64
            if self.anvil_output.count + 1 > max_stack:
                return
        job.elapsed += dt
        job.fired_flash = max(0.0, job.fired_flash - dt)
        if job.elapsed >= job.duration:
            self._finish_anvil_job()

    def _finish_anvil_job(self):
        """Apply the pending durability restore to the target item
        and place the repaired item in the anvil output slot.

        The item reference is :py:attr:`anvil_pending_item` (snapshotted
        at job start) so durability changes are visible in the input
        slot as the job runs.  We use :py:meth:`DurabilityMixin.repair`
        to honour the wear/damage scaling logic.
        """
        job = self.anvil_job
        if job is None:
            return
        if not self.anvil_output.is_empty():
            if self.anvil_output.item.id != job.target_item_id:
                return
            max_stack = getattr(self.anvil_output.item, "max_stack", 64) or 64
            if self.anvil_output.count + 1 > max_stack:
                return

        target = self.anvil_pending_item
        if target is None or getattr(target, "unbreakable", False):
            self.anvil_job = None
            return

        # Apply the durability restore.
        try:
            target.repair(job.repair_amount)
        except Exception:
            pass

        # Place a fresh copy of the target into the output slot.  The
        # input slot already has the *same* Python object, so we move
        # it to the output and clear the input.  This avoids
        # double-ownership where the input slot still shows the
        # (now-repaired) item.
        self.anvil_item.clear()
        self.anvil_pending_item = None
        if self.anvil_output.is_empty():
            self.anvil_output.set(target, 1)
        else:
            max_stack = getattr(self.anvil_output.item, "max_stack", 64) or 64
            new_count = min(self.anvil_output.count + 1, max_stack)
            self.anvil_output.set(self.anvil_output.item, new_count)

        # Award smelting XP for the repair.
        try:
            from src.systems.smelting_skill import XP_PER_REPAIR
            char = None
            gs = getattr(self.app.manager, "states", {}).get("gameplay") if getattr(self.app, "manager", None) else None
            if gs is not None:
                char = getattr(gs, "character", None)
            skill = getattr(char, "smelting_skill", None) if char is not None else None
            if skill is not None:
                skill.add_xp(XP_PER_REPAIR)
        except Exception:
            pass

        self.anvil_job = None
        job.fired_flash = 0.6

    def _try_start_anvil_job(self):
        """Begin a new anvil repair if both slots are filled with
        valid items and the output slot is free (or holds the same
        repaired item)."""
        if self.anvil_job is not None:
            return
        if self.anvil_item.is_empty() or self.anvil_material.is_empty():
            return
        item = self.anvil_item.item
        material = self.anvil_material.item
        if not self._is_repairable(item):
            return
        # The item must actually need repair (or be at least partially
        # damaged).  Fully repaired items waste material; we politely
        # refuse so the player gets visual feedback.
        try:
            cur = int(getattr(item, "durability", 0) or 0)
            mx = int(getattr(item, "max_durability", 0) or 0)
        except Exception:
            return
        if mx <= 0 or cur >= mx:
            return
        recipe = get_anvil_recipe_for_material(material.id)
        if recipe is None:
            return
        # Make sure the output slot can accept the repaired item.
        if not self.anvil_output.is_empty():
            if self.anvil_output.item.id != item.id:
                return
            max_stack = getattr(self.anvil_output.item, "max_stack", 64) or 64
            if self.anvil_output.count + 1 > max_stack:
                return
        # Consume one material now.
        new_count = self.anvil_material.count - int(recipe["material_amount"])
        if new_count <= 0:
            self.anvil_material.clear()
        else:
            self.anvil_material.set(material, new_count)
        # Snapshot the item and compute the restore amount.
        self.anvil_pending_item = item
        repair_amount = self._anvil_target_durability(item, recipe["repair_fraction"]) - cur
        if repair_amount < 1:
            repair_amount = 1
        self.anvil_job = _FurnaceJob({
            "duration": float(recipe.get("duration", 4.0)),
            "heat_color": recipe.get("heat_color", (255, 150, 60)),
            "primary_output_id": item.id,
            "primary_output_amount": 1,
        })
        # The stock _FurnaceJob is shared with the furnaces; expose
        # the repair-specific data on the instance so the renderer and
        # the finish handler can read it without growing the schema.
        self.anvil_job.target_item_id = item.id
        self.anvil_job.repair_amount = int(repair_amount)
        self.anvil_job.heat_color = recipe.get("heat_color", (255, 150, 60))

    # ------------------------------------------------------------------ #
    # Slot interaction                                                    #
    # ------------------------------------------------------------------ #

    def _coke_input_rect(self):
        return getattr(self, "_coke_input_rect_real", None) or self._coke_input_rect

    def handle_event(self, event):
        """Process a pygame event while the smeltery overlay is open.

        Returns ``True`` when the event was consumed (so callers can
        stop propagating it), otherwise ``False``.
        """
        if not self.is_open:
            return False

        self._ensure_layout()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Close button.
            if self._close_button and self._close_button.rect.collidepoint((mx, my)):
                self._close_button.on_click()
                return True

            # Tab buttons.
            for btn in self._tab_buttons:
                if btn.rect.collidepoint((mx, my)):
                    btn.on_click()
                    return True

            # Station-specific slot clicks.
            if self.active_station == STATION_WORKBENCH:
                if self.crafting_grid is not None and self._workbench_rect.collidepoint((mx, my)):
                    inv = self._inv_manager()
                    if inv is not None:
                        self.crafting_grid.inventory_interactions(event, inv)
                    return True
            elif self.active_station == STATION_COKE_OVEN:
                if self._coke_input_rect.collidepoint((mx, my)):
                    self._handle_furnace_slot_click(self.coke_input, allow_extract=True)
                    return True
                if self._coke_output_rect.collidepoint((mx, my)):
                    self._handle_output_slot_click(self.coke_output)
                    return True
            elif self.active_station == STATION_BLAST_FURNACE:
                if self._blast_item_rect.collidepoint((mx, my)):
                    self._handle_furnace_slot_click(self.blast_item, allow_extract=True)
                    return True
                if self._blast_fuel_rect.collidepoint((mx, my)):
                    self._handle_furnace_slot_click(self.blast_fuel, allow_extract=True)
                    return True
                if self._blast_output_rect.collidepoint((mx, my)):
                    self._handle_output_slot_click(self.blast_output)
                    return True
            elif self.active_station == STATION_ANVIL:
                if self._anvil_item_rect.collidepoint((mx, my)):
                    self._handle_anvil_item_click()
                    return True
                if self._anvil_material_rect.collidepoint((mx, my)):
                    self._handle_anvil_material_click()
                    return True
                if self._anvil_output_rect.collidepoint((mx, my)):
                    self._handle_output_slot_click(self.anvil_output)
                    return True

        return False

    def _inv_manager(self):
        return getattr(self.app, "INV_manager", None)

    def _player_inventory(self):
        try:
            return self.app.manager.states["gameplay"].MAIN_player_inv
        except Exception:
            return None

    def _handle_furnace_slot_click(self, slot, allow_extract=True):
        """Click handler for furnace input slots.

        - LMB with no held item and a non-empty slot: pick up (only if
          ``allow_extract`` is true -- input slots in the blast furnace
          are locked once a job has started).
        - LMB with a held item and an empty slot: place.
        - LMB with a held item and a non-empty slot of the same id:
          merge stacks.
        - LMB with a held item and a non-empty slot of a different id:
          swap.
        """
        inv = self._inv_manager()
        if inv is None:
            return
        held = inv.selected_item

        if held is None:
            if not allow_extract:
                return
            if slot.is_empty():
                return
            inv.selected_item = slot.as_pair()
            slot.clear()
        else:
            held_item, held_count = held
            held_id = held_item.id

            if slot.is_empty():
                slot.set(held_item, held_count)
                inv.selected_item = None
            else:
                existing_item, existing_count = slot.as_pair()
                if existing_item.id == held_id:
                    slot.set(existing_item, existing_count + held_count)
                    inv.selected_item = None
                else:
                    # Swap.
                    inv.selected_item = slot.as_pair()
                    slot.set(held_item, held_count)

        # After any change to a furnace slot, see if a new job can begin.
        self._try_start_coke_job()
        self._try_start_blast_job()
        self._try_start_anvil_job()

    def _handle_output_slot_click(self, slot):
        """Output slots can only be extracted from.

        After clearing the output, attempt to start a new smelting job so
        the furnace auto-resumes when more input is available.
        """
        inv = self._inv_manager()
        if inv is None or slot.is_empty():
            return
        inv.selected_item = slot.as_pair()
        slot.clear()
        # Auto-resume: if there is still input waiting, kick off the next batch.
        self._try_start_coke_job()
        self._try_start_blast_job()
        self._try_start_anvil_job()

    def _handle_anvil_item_click(self):
        """Click handler for the anvil's damaged-item slot.

        The item slot is unlocked so the player can pull the item back
        out at any time (unlike the blast furnace inputs that lock once
        a job starts).  When pulled mid-job, the in-flight repair is
        cancelled and the snapshot is restored into the slot.
        """
        inv = self._inv_manager()
        if inv is None:
            return
        held = inv.selected_item

        if held is None:
            if self.anvil_item.is_empty():
                return
            inv.selected_item = self.anvil_item.as_pair()
            self.anvil_item.clear()
            # If we just yanked the item that was being repaired, kill
            # the in-flight job (and refund the material? -- no, the
            # material was already consumed, that's the player's loss).
            if self.anvil_job is not None and self.anvil_pending_item is inv.selected_item[0]:
                self.anvil_job = None
                self.anvil_pending_item = None
        else:
            held_item, held_count = held
            # Only allow weapons/armor/tools to be placed on the anvil.
            if not self._is_repairable(held_item):
                return
            if self.anvil_item.is_empty():
                # Place a single copy (these items never stack) and
                # keep the remainder in the cursor if it was a stack.
                self.anvil_item.set(held_item, 1)
                if held_count > 1:
                    inv.selected_item = [held_item, held_count - 1]
                else:
                    inv.selected_item = None
            else:
                # Slot is occupied -- swap with the held item.
                existing = self.anvil_item.as_pair()
                if held_count > 1:
                    # Don't drop a partial stack on a single-instance slot.
                    return
                self.anvil_item.set(held_item, 1)
                inv.selected_item = existing
        self._try_start_anvil_job()

    def _handle_anvil_material_click(self):
        """Click handler for the anvil's repair material slot.

        The slot accepts *any* valid repair material (iron_ingot,
        steel_ingot).  Like the furnace input slots, it supports
        pick-up, place, merge, and swap.  Extraction is blocked while
        a job is running (the material has already been consumed).
        """
        inv = self._inv_manager()
        if inv is None:
            return
        held = inv.selected_item
        allow_extract = self.anvil_job is None

        if held is None:
            if not allow_extract:
                return
            if self.anvil_material.is_empty():
                return
            inv.selected_item = self.anvil_material.as_pair()
            self.anvil_material.clear()
        else:
            held_item, held_count = held
            # Only repair materials are valid here.
            if get_anvil_recipe_for_material(held_item.id) is None:
                return
            if self.anvil_material.is_empty():
                self.anvil_material.set(held_item, held_count)
                inv.selected_item = None
            else:
                existing_item, existing_count = self.anvil_material.as_pair()
                if existing_item.id == held_item.id:
                    new_count = existing_count + held_count
                    inv.selected_item = None
                    self.anvil_material.set(existing_item, new_count)
                else:
                    # Swap.
                    inv.selected_item = self.anvil_material.as_pair()
                    self.anvil_material.set(held_item, held_count)
        self._try_start_anvil_job()

    def _try_start_coke_job(self):
        if self.coke_job is not None:
            return
        if self.coke_input.is_empty():
            return
        item, _count = self.coke_input.as_pair()
        recipe = get_coke_recipe_for_input(item.id)
        if recipe is None:
            return
        # Make sure the output slot can accept one more batch. We need
        # to know the produced item's max_stack, but the item doesn't
        # exist yet -- estimate from the recipe's primary_output_id by
        # looking up a similar existing item.
        amount = int(recipe["primary_output_amount"])
        # Peek the primary item to know its max_stack.
        primary_peek = self._make_item(recipe["primary_output_id"])
        if primary_peek is None:
            return
        if not self.coke_output.can_accept(primary_peek, amount):
            return
        # Consume one batch worth of input on start, mirroring the
        # blast furnace behaviour. This way each input unit smelts once
        # and the stack count decreases as smelting progresses.
        self.coke_input.set(item, _count - int(recipe["input_amount"]))
        if self.coke_input.count <= 0:
            self.coke_input.clear()
        self.coke_job = _FurnaceJob(recipe)

    def _try_start_blast_job(self):
        if self.blast_job is not None:
            return
        if self.blast_item.is_empty() or self.blast_fuel.is_empty():
            return
        item, _item_count = self.blast_item.as_pair()
        fuel, _fuel_count = self.blast_fuel.as_pair()
        recipe = get_blast_recipe_for_inputs(item.id, fuel.id)
        if recipe is None:
            return
        # Make sure the output slot can accept one more batch.
        amount = int(recipe["primary_output_amount"])
        primary_peek = self._make_item(recipe["primary_output_id"])
        if primary_peek is None:
            return
        if not self.blast_output.can_accept(primary_peek, amount):
            return
        # Consume one batch worth of inputs immediately.
        self.blast_item.set(item, _item_count - int(recipe["input_item_amount"]))
        if self.blast_item.count <= 0:
            self.blast_item.clear()
        self.blast_fuel.set(fuel, _fuel_count - int(recipe["input_fuel_amount"]))
        if self.blast_fuel.count <= 0:
            self.blast_fuel.clear()
        self.blast_job = _FurnaceJob(recipe)

    # ------------------------------------------------------------------ #
    # Drawing                                                             #
    # ------------------------------------------------------------------ #

    def draw(self, screen):
        if not self.is_open:
            return

        self._ensure_layout()

        # Outer panel with rounded corners + shadow.
        draw_panel_with_shadow(
            screen,
            self._panel_rect,
            bg_color=(28, 32, 42, 245),
            border_color=(70, 80, 95, 255),
            border_width=2,
            border_radius=14,
            shadow_offset=10,
        )

        # Tab bar background.
        pygame.draw.rect(
            screen,
            (40, 44, 56, 255),
            self._tab_bar_rect,
            border_radius=12,
        )
        # Re-stroke the bottom edge flat (the rounding above gives a pill).
        pygame.draw.line(
            screen,
            (70, 80, 95, 255),
            (self._tab_bar_rect.left + 12, self._tab_bar_rect.bottom),
            (self._tab_bar_rect.right - 12, self._tab_bar_rect.bottom),
            2,
        )

        # Title (left-aligned inside the tab bar).
        title_font = cfg.tooltip_font_CREDITS
        title_surf = title_font.render(_("SMELTERY"), True, (230, 185, 60))
        title_x = self._tab_bar_rect.left + int(18 * cfg.ui_scale())
        title_y = self._tab_bar_rect.centery - title_surf.get_height() // 2
        screen.blit(title_surf, (title_x, title_y))

        # Tab buttons.
        for i, btn in enumerate(self._tab_buttons):
            station = STATION_ORDER[i]
            if station == self.active_station:
                # Highlight the active tab.
                hl_rect = btn.rect.inflate(0, int(4 * cfg.ui_scale()))
                pygame.draw.rect(screen, (90, 75, 45), hl_rect, border_radius=6)
                pygame.draw.rect(screen, (212, 175, 55), hl_rect, width=2, border_radius=6)
            btn.draw(screen)

        # Close button.
        if self._close_button:
            self._close_button.draw(screen)

        # Station body.
        if self.active_station == STATION_WORKBENCH:
            self._draw_workbench_body(screen)
        elif self.active_station == STATION_COKE_OVEN:
            self._draw_coke_oven_body(screen)
        elif self.active_station == STATION_BLAST_FURNACE:
            self._draw_blast_furnace_body(screen)
        elif self.active_station == STATION_ANVIL:
            self._draw_anvil_body(screen)

        # Skill bar (shared by every tab).
        self._draw_skill_bar(screen)

    def _draw_workbench_body(self, screen):
        if self.crafting_grid is None:
            # Fall back to a hint when the grid failed to construct.
            font = cfg.tooltip_font_CREDITS
            line1 = font.render(_("Use the 3x3 crafting grid below to shape items."),
                                 True, (220, 220, 230))
            line2 = font.render(_("Drag items between the grid and your inventory to craft."),
                                 True, (170, 170, 185))
            cx = self._workbench_rect.centerx
            cy = self._workbench_rect.centery
            screen.blit(line1, (cx - line1.get_width() // 2, cy - line1.get_height()))
            screen.blit(line2, (cx - line2.get_width() // 2, cy + int(6 * cfg.ui_scale())))
            return

        # Draw the 3x3 grid + output slot + book button on the workbench.
        from src.inventory.inventory_renderer import InventoryRenderer
        renderer = InventoryRenderer()
        renderer.draw_crafting_system(screen, self.crafting_grid)

    def _draw_coke_oven_body(self, screen):
        # Furnace frame.
        frame = self._coke_rect
        pygame.draw.rect(screen, (40, 25, 20, 255), frame, border_radius=10)
        pygame.draw.rect(screen, (90, 60, 45, 255), frame, width=3, border_radius=10)
        # Inner heat area.
        inner = frame.inflate(-int(16 * cfg.ui_scale()), -int(16 * cfg.ui_scale()))
        pygame.draw.rect(screen, (60, 30, 20, 255), inner, border_radius=6)
        self._draw_flame_glow(screen, inner, self.coke_job, 0)

        # Slots.
        self._draw_furnace_slot(screen, self._coke_input_rect, self.coke_input)
        self._draw_furnace_slot(screen, self._coke_output_rect, self.coke_output)

        # Progress bar.
        self._draw_progress_bar(screen, self._coke_progress_rect, self.coke_job)

        # Labels.
        self._draw_slot_label(screen, _("Input"), self._coke_input_label_pos)
        self._draw_slot_label(screen, _("Output"), self._coke_output_label_pos)

    def _draw_blast_furnace_body(self, screen):
        # Furnace frame.
        frame = self._blast_rect
        pygame.draw.rect(screen, (32, 22, 22, 255), frame, border_radius=10)
        pygame.draw.rect(screen, (90, 60, 55, 255), frame, width=3, border_radius=10)
        inner = frame.inflate(-int(16 * cfg.ui_scale()), -int(16 * cfg.ui_scale()))
        pygame.draw.rect(screen, (55, 30, 25, 255), inner, border_radius=6)
        self._draw_flame_glow(screen, inner, self.blast_job, 1)

        # Slots.
        self._draw_furnace_slot(screen, self._blast_item_rect, self.blast_item)
        self._draw_furnace_slot(screen, self._blast_fuel_rect, self.blast_fuel)
        self._draw_furnace_slot(screen, self._blast_output_rect, self.blast_output)

        # Progress bar.
        self._draw_progress_bar(screen, self._blast_progress_rect, self.blast_job)

        # Labels.
        self._draw_slot_label(screen, _("Ore"), self._blast_item_label_pos)
        self._draw_slot_label(screen, _("Fuel"), self._blast_fuel_label_pos)
        self._draw_slot_label(screen, _("Output"), self._blast_output_label_pos)

    def _draw_furnace_slot(self, screen, rect, slot):
        """Draw a single furnace slot with the same look as the
        inventory renderer."""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hovered = rect.collidepoint((mouse_x, mouse_y))

        pygame.draw.rect(screen, cfg.INV_SLOT_BG_COLOR, rect,
                         border_radius=cfg.INV_SLOT_BORDER_RADIUS)
        inner_rect = rect.inflate(-4, -4)
        pygame.draw.rect(screen, cfg.INV_SLOT_INNER_SHADOW, inner_rect,
                         border_radius=cfg.INV_SLOT_INNER_BORDER_RADIUS)
        if hovered:
            hover_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(hover_surf, cfg.INV_SLOT_HOVER_FILL,
                             hover_surf.get_rect(),
                             border_radius=cfg.INV_SLOT_BORDER_RADIUS)
            screen.blit(hover_surf, rect.topleft)
            pygame.draw.rect(screen, cfg.INV_SLOT_HOVER_BORDER, rect, width=2,
                             border_radius=cfg.INV_SLOT_BORDER_RADIUS)
        else:
            pygame.draw.rect(screen, cfg.INV_SLOT_BORDER_COLOR, rect, width=2,
                             border_radius=cfg.INV_SLOT_BORDER_RADIUS)

        if not slot.is_empty():
            item, count = slot.as_pair()
            padding = cfg.INV_SLOT_PADDING
            item_size = rect.width - padding * 2
            shadow = pygame.Surface((item_size, item_size), pygame.SRCALPHA)
            pygame.draw.circle(shadow, cfg.INV_ITEM_SHADOW_COLOR,
                               (item_size // 2, item_size // 2),
                               item_size // 2 - 2)
            screen.blit(shadow, (rect.x + padding + 2, rect.y + padding + 4))
            screen.blit(item.resize(item_size), (rect.x + padding, rect.y + padding))
            if count > 1:
                font_obj = cfg.INV_nums_font
                text_str = str(count)
                sh1 = font_obj.render(text_str, True, (0, 0, 0))
                sh2 = font_obj.render(text_str, True, (0, 0, 0))
                tx = font_obj.render(text_str, True, cfg.INV_ITEM_TEXT_COLOR)
                tx_pos = (rect.right - tx.get_width() - 4,
                          rect.bottom - tx.get_height() - 2)
                screen.blit(sh1, (tx_pos[0] + 2, tx_pos[1] + 2))
                screen.blit(sh2, (tx_pos[0] + 1, tx_pos[1] + 1))
                screen.blit(tx, tx_pos)

    def _draw_progress_bar(self, screen, rect, job):
        """Vertical progress bar used by both furnaces."""
        # Background.
        pygame.draw.rect(screen, (15, 10, 10, 255), rect, border_radius=4)
        pygame.draw.rect(screen, (60, 30, 25, 255), rect, width=2, border_radius=4)

        if job is None:
            return

        # Filled portion (bottom-up).
        progress = job.progress()
        if progress > 0:
            fill_h = max(1, int(rect.height * progress))
            fill_rect = pygame.Rect(rect.x, rect.bottom - fill_h, rect.width, fill_h)
            heat = job.recipe.get("heat_color", (220, 80, 30))
            # Gradient from dark red at bottom to bright at top.
            for y in range(fill_rect.height):
                t = y / max(1, fill_rect.height)
                r = int(heat[0] * (0.6 + 0.4 * t))
                g = int(heat[1] * (0.4 + 0.6 * t))
                b = int(heat[2] * (0.3 + 0.5 * t))
                pygame.draw.line(screen, (r, g, b),
                                 (fill_rect.x, fill_rect.y + y),
                                 (fill_rect.right, fill_rect.y + y))

        # Flame icon on top of the bar.
        cx, cy = rect.centerx, rect.y + 8
        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) / 2
        base = 4
        flame_h = int(base + 2 * pulse)
        flame_w = max(3, int(rect.width * 0.6))
        pts = [
            (cx, cy - flame_h),
            (cx + flame_w // 2, cy),
            (cx, cy + flame_h // 2),
            (cx - flame_w // 2, cy),
        ]
        pygame.draw.polygon(screen, (255, 200, 60), pts)
        pygame.draw.polygon(screen, (255, 120, 30), [
            (cx, cy - flame_h + 2),
            (cx + flame_w // 4, cy),
            (cx - flame_w // 4, cy),
        ])

    def _draw_flame_glow(self, screen, rect, job, color_index):
        """Subtle warm glow inside the furnace body when a job is running."""
        if job is None:
            return
        progress = job.progress()
        heat = job.recipe.get("heat_color", (220, 80, 30))
        intensity = int(40 + 60 * progress + 30 * job.fired_flash)
        glow = pygame.Surface(rect.size, pygame.SRCALPHA)
        center = (rect.width // 2, rect.height - int(12 * cfg.ui_scale()))
        max_r = max(rect.width, rect.height) // 2
        for r in range(max_r, 0, -2):
            a = int(intensity * (1.0 - r / max_r) * 0.6)
            if a <= 0:
                continue
            pygame.draw.circle(glow, (*heat, max(0, min(80, a))),
                               center, r)
        screen.blit(glow, rect.topleft)

    def _draw_slot_label(self, screen, text, center_pos):
        font = cfg.INV_nums_font
        surf = font.render(text, True, (200, 200, 215))
        screen.blit(surf, (center_pos[0] - surf.get_width() // 2,
                            center_pos[1] - surf.get_height() // 2))

    # ------------------------------------------------------------------ #
    # Anvil body + skill bar                                              #
    # ------------------------------------------------------------------ #

    def _draw_anvil_body(self, screen):
        """Render the anvil tab: three slots, a horizontal progress
        bar, and a status line that previews the repair amount."""
        scale = cfg.ui_scale()

        # Anvil frame (dark iron-grey with brass trim).
        frame = self._anvil_rect
        pygame.draw.rect(screen, (32, 28, 28, 255), frame, border_radius=10)
        pygame.draw.rect(screen, (130, 105, 60, 255), frame, width=3, border_radius=10)
        inner = frame.inflate(-int(16 * scale), -int(16 * scale))
        pygame.draw.rect(screen, (50, 45, 40, 255), inner, border_radius=6)

        # A pair of decorative anvil legs at the bottom of the inner panel.
        leg_h = int(8 * scale)
        leg_w = int(28 * scale)
        leg_y = inner.bottom - leg_h
        for cx in (inner.left + int(28 * scale), inner.right - int(28 * scale) - leg_w):
            pygame.draw.rect(screen, (110, 90, 55, 255),
                             pygame.Rect(cx, leg_y, leg_w, leg_h),
                             border_radius=2)

        # A central anvil top block (just for the chrome).
        top_w = int(120 * scale)
        top_h = int(12 * scale)
        top_x = inner.centerx - top_w // 2
        top_y = inner.top + int(8 * scale)
        pygame.draw.rect(screen, (140, 115, 70, 255),
                         pygame.Rect(top_x, top_y, top_w, top_h),
                         border_radius=3)

        # Slots.
        self._draw_furnace_slot(screen, self._anvil_item_rect, self.anvil_item)
        self._draw_furnace_slot(screen, self._anvil_material_rect, self.anvil_material)
        self._draw_furnace_slot(screen, self._anvil_output_rect, self.anvil_output)

        # Progress bar (horizontal, between the material and the output).
        self._draw_anvil_progress_bar(screen, self._anvil_progress_rect, self.anvil_job)

        # Status line at the bottom of the frame.
        self._draw_anvil_status(screen, self._anvil_status_rect)

        # Slot labels.
        self._draw_slot_label(screen, _("Damaged"), self._anvil_item_label_pos)
        self._draw_slot_label(screen, _("Material"), self._anvil_material_label_pos)
        self._draw_slot_label(screen, _("Repaired"), self._anvil_output_label_pos)

    def _draw_anvil_progress_bar(self, screen, rect, job):
        """Horizontal progress bar used by the anvil."""
        pygame.draw.rect(screen, (15, 10, 10, 255), rect, border_radius=4)
        pygame.draw.rect(screen, (90, 65, 30, 255), rect, width=2, border_radius=4)
        if job is None:
            return
        progress = job.progress()
        if progress > 0:
            fill_w = max(1, int(rect.width * progress))
            fill_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
            heat = job.recipe.get("heat_color", (255, 150, 60)) if hasattr(job, "recipe") and job.recipe else (255, 150, 60)
            for x in range(fill_rect.width):
                t = x / max(1, fill_rect.width)
                r = int(heat[0] * (0.6 + 0.4 * t))
                g = int(heat[1] * (0.4 + 0.6 * t))
                b = int(heat[2] * (0.3 + 0.5 * t))
                pygame.draw.line(screen, (r, g, b),
                                 (fill_rect.x + x, fill_rect.y),
                                 (fill_rect.x + x, fill_rect.bottom))
        # Hammer icon at the end of the bar (just a stylised "T").
        cx = rect.right - 8
        cy = rect.centery
        pygame.draw.line(screen, (220, 180, 90), (cx, cy - 5), (cx, cy + 5), 2)
        pygame.draw.line(screen, (220, 180, 90), (cx - 4, cy - 5), (cx + 4, cy - 5), 2)

    def _draw_anvil_status(self, screen, rect):
        """Status line that previews the repair amount / job state."""
        font = cfg.INV_nums_font
        text = ""
        color = (200, 200, 215)
        if self.anvil_job is not None:
            text = _("Repairing... {pct:.0f}%").format(
                pct=self.anvil_job.progress() * 100.0
            )
            color = (255, 200, 90)
        elif not self.anvil_item.is_empty() and not self.anvil_material.is_empty():
            item = self.anvil_item.item
            material = self.anvil_material.item
            recipe = get_anvil_recipe_for_material(material.id)
            if recipe is None or not self._is_repairable(item):
                text = _("Invalid combination")
                color = (200, 110, 110)
            else:
                try:
                    cur = int(getattr(item, "durability", 0) or 0)
                    mx = int(getattr(item, "max_durability", 0) or 0)
                except Exception:
                    cur, mx = 0, 0
                if mx > 0 and cur >= mx:
                    text = _("Already fully repaired")
                    color = (140, 220, 140)
                else:
                    fraction = float(recipe.get("repair_fraction", 0.0)) * 100.0
                    text = _("Will restore {pct:.0f}% durability").format(pct=fraction)
                    color = (220, 220, 240)
        elif not self.anvil_item.is_empty() and self._is_repairable(self.anvil_item.item):
            text = _("Add a repair material (iron / steel ingot)")
            color = (170, 170, 185)
        else:
            text = _("Place a damaged item to begin")
            color = (170, 170, 185)
        surf = font.render(text, True, color)
        # Centre the text inside the status rect.
        tx = rect.centerx - surf.get_width() // 2
        ty = rect.centery - surf.get_height() // 2
        screen.blit(surf, (tx, ty))

    def _draw_skill_bar(self, screen):
        """Render the smelting-skill HUD at the bottom of the panel.

        Visible on every tab.  Shows the level number, an XP progress
        bar, and a faint "tier chance" hint.  Layout:

        [Smelting Lv. N]  [================......]  X / Y XP  (Tiers)
        """
        if self._skill_bar_rect is None:
            return
        scale = cfg.ui_scale()
        rect = self._skill_bar_rect
        # Background.
        pygame.draw.rect(screen, (22, 26, 32, 255), rect, border_radius=6)
        pygame.draw.rect(screen, (60, 70, 85, 255), rect, width=1, border_radius=6)

        font = cfg.INV_nums_font
        title_font = cfg.tooltip_font_CREDITS

        # Read the skill from the player character; fall back to a
        # level-1 placeholder so the bar is always rendered.
        skill = None
        try:
            gs = self.app.manager.states.get("gameplay")
            char = getattr(gs, "character", None)
            skill = getattr(char, "smelting_skill", None)
        except Exception:
            skill = None
        if skill is None:
            from src.systems.smelting_skill import SmeltingSkill
            skill = SmeltingSkill()

        # Left: "Smelting Lv. N" label.
        try:
            from src.systems.smelting_skill import MAX_SMELTING_LEVEL
        except Exception:
            MAX_SMELTING_LEVEL = 50
        level_label = _("Smelting Lv. {lvl}").format(lvl=int(skill.level))
        if skill.is_max_level():
            level_label = _("Smelting Lv. {lvl} (MAX)").format(lvl=int(skill.level))
        lvl_surf = title_font.render(level_label, True, (255, 215, 90))
        lvl_x = rect.left + int(10 * scale)
        lvl_y = rect.centery - lvl_surf.get_height() // 2
        screen.blit(lvl_surf, (lvl_x, lvl_y))

        # Right: "Xp / ToNext" text.
        if skill.is_max_level():
            xp_text = _("MAX")
            xp_color = (255, 215, 90)
        else:
            xp_text = _("{cur} / {target} XP").format(
                cur=int(skill.xp), target=int(skill.xp_to_next_level)
            )
            xp_color = (200, 200, 215)
        xp_surf = font.render(xp_text, True, xp_color)
        xp_x = rect.right - xp_surf.get_width() - int(10 * scale)
        xp_y = rect.centery - xp_surf.get_height() // 2
        screen.blit(xp_surf, (xp_x, xp_y))

        # Centre: XP bar.
        bar_pad_x = int(8 * scale)
        bar_x = lvl_x + lvl_surf.get_width() + bar_pad_x
        bar_right = xp_x - bar_pad_x
        bar_w = max(20, bar_right - bar_x)
        bar_h = max(8, int(10 * scale))
        bar_y = rect.centery - bar_h // 2
        bar_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(screen, (12, 14, 18, 255), bar_rect, border_radius=3)
        pygame.draw.rect(screen, (50, 55, 65, 255), bar_rect, width=1, border_radius=3)
        if bar_w > 4:
            progress = skill.progress()
            if progress > 0:
                fill_w = max(1, int((bar_w - 2) * progress))
                fill_rect = pygame.Rect(bar_x + 1, bar_y + 1, fill_w, bar_h - 2)
                # Gradient from orange to gold.
                for x in range(fill_rect.width):
                    t = x / max(1, fill_rect.width)
                    r = int(220 + (255 - 220) * t)
                    g = int(120 + (200 - 120) * t)
                    b = int(40 + (60 - 40) * t)
                    pygame.draw.line(screen, (r, g, b),
                                     (fill_rect.x + x, fill_rect.y),
                                     (fill_rect.x + x, fill_rect.bottom))
