"""
Configuration module for Super Ultra Project.

This module defines global constants, color schemes, font utilities, and layout settings for the game UI and inventory system.
"""

import pygame
import os

pygame.font.init()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Keep a base design resolution (buttons/fonts authored for 1920x1080).
# Start the window at 1280x720 by default but scale UI from the BASE resolution.
BASE_SCREEN_WIDTH, BASE_SCREEN_HEIGHT = 1920, 1080
DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT = 1280, 720
SCREEN_WIDTH, SCREEN_HEIGHT = DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT
FPS = 0

def _load_background(screen_width, screen_height):
    try:
        bg_path = os.path.join(BASE_DIR, "assets", "ui", "bg_menu.jpg")
        return pygame.transform.scale(pygame.image.load(bg_path), (screen_width, screen_height))
    except (FileNotFoundError, pygame.error):
        return pygame.Surface((screen_width, screen_height))

bg = _load_background(SCREEN_WIDTH, SCREEN_HEIGHT)

USER_SCREEN_BRIGHTNESS = 1.0
ENVIRONMENT_BRIGHTNESS = 1.0
SCREEN_BRIGHTNESS = 1.0
# Environment tinting (used for dawn/dusk/night color overlays)
ENVIRONMENT_TINT = (255, 255, 255)
ENVIRONMENT_DAY_COLOR = (255, 255, 255)
ENVIRONMENT_NIGHT_COLOR = (10, 24, 80)
ENVIRONMENT_DAWN_COLOR = (255, 200, 160)
ENVIRONMENT_DUSK_COLOR = (255, 160, 120)
PROFILER_ENABLED = False
MUSIC_VOLUME = 0.3

LANGUAGE = 'en'
SUPPORTED_LANGUAGES = ['en', 'ua']

def get_font(size):
    """
    Get a Pygame font object for the current language and size.

    Args:
        size (int): Font size in points.

    Returns:
        pygame.font.Font: The font object for rendering text.
    """
    if LANGUAGE == 'ua':
        return pygame.font.SysFont("arial", size)
    try:
        font_path = os.path.join(BASE_DIR, "fonts", "menu_font.ttf")
        return pygame.font.Font(font_path, size)
    except:
        return pygame.font.SysFont("arial", size)

# UI scaling helpers
def ui_scale() -> float:
    """Return the UI scale relative to the BASE_SCREEN resolution.

    Uses the minimum of width and height scale so elements stay proportional.
    """
    try:
        sx = SCREEN_WIDTH / BASE_SCREEN_WIDTH
        sy = SCREEN_HEIGHT / BASE_SCREEN_HEIGHT
        return min(sx, sy)
    except Exception:
        return 1.0


# Default fonts and colors — fonts are updated by `update_scaled_fonts()`.
def update_scaled_fonts():
    global myfont, button_font, inventory_tooltip_font, tooltip_font_CREDITS, INV_nums_font
    scale = ui_scale()
    # Base sizes (authored for 1920x1080)
    myfont = get_font(max(12, int(60 * scale)))
    button_font = get_font(max(10, int(60 * scale)))
    inventory_tooltip_font = get_font(max(14, int(22 * scale)))
    tooltip_font_CREDITS = get_font(max(14, int(22 * scale)))
    INV_nums_font = get_font(max(14, int(20 * scale)))


def update_brightness():
    global SCREEN_BRIGHTNESS
    SCREEN_BRIGHTNESS = max(0.0, min(1.0, USER_SCREEN_BRIGHTNESS))


# initialize scaled fonts
update_scaled_fonts()
update_brightness()

button_color_START = (83, 112, 44)
button_hover_color_START = (123, 123, 34)
button_color_EXIT = (150, 0, 0)
button_hover_color_EXIT = (150, 50, 50)
button_color_SETTINGS = (0, 126, 183)
button_hover_color_SETTINGS = (67, 152, 174)
button_color_SETTINGS_BACK = (83, 112, 44)
button_hover_color_SETTINGS_BACK = (123, 123, 34)        
button_color_CREDITS = (250, 205, 82)
button_hover_color_CREDITS = (255, 220, 97)

text_color = (0, 0, 0)
corner_radius = 20

tooltip_padding = 10
tooltip_appear = 0.5

inventory_tooltip_rect = pygame.Rect(0, 0, 1, 1)
inventory_tooltip_bg = (18, 22, 32)
inventory_tooltip_border = (200, 170, 80)
inventory_tooltip_font_color = (255, 255, 255)

tooltip_bg_CREDITS = (18, 22, 32)
tooltip_border_CREDITS = (200, 170, 80)

MAIN_INV_columns = 8
MAIN_INV_rows = 4

MAIN_INV_equipment_columns = 2
MAIN_INV_equipment_rows = 4

# Equipment slot type definitions (col x row -> slot_type)
# Column 0: accessories/wearables
# Column 1: armor pieces
EQUIPMENT_SLOT_TYPES = [
    ["charm", "gloves", "ring", "belt"],
    ["helmet", "chestplate", "leggings", "boots"],
]

# Human-readable labels for equipment slots
EQUIPMENT_SLOT_LABELS = {
    "helmet": "Helmet", "chestplate": "Chestplate",
    "leggings": "Leggings", "boots": "Boots",
    "charm": "Charm", "gloves": "Gloves",
    "ring": "Ring", "belt": "Belt",
}

BASE_INV_slot_size = 70
BASE_INV_border = 3
BASE_INV_slot_color = (216, 223, 203)
BASE_INV_border_color = (33, 41, 48)

MAIN_INV_BACKGROUND=(109, 125, 123)

MAIN_INV_pos_x = 0
MAIN_INV_pos_y = 0
MAIN_INV_equipment_pos_x = 0
MAIN_INV_equipment_pos_y = 0

def recalculate_inventory_positions():
    global MAIN_INV_pos_x, MAIN_INV_pos_y, MAIN_INV_equipment_pos_x, MAIN_INV_equipment_pos_y
    
    scale = ui_scale()
    slot_size = int(BASE_INV_slot_size * scale)
    border = int(BASE_INV_border * scale)
    
    grid_width = (slot_size + border) * MAIN_INV_columns
    grid_height = (slot_size + border) * MAIN_INV_rows
    
    MAIN_INV_pos_x = SCREEN_WIDTH // 2 - grid_width // 2
    
    total_window_height = grid_height + int(350 * scale)
    
    hotbar_height = int(slot_size * 0.8) + int(40 * scale)
    
    available_height = SCREEN_HEIGHT - hotbar_height
    
    window_top = (available_height - total_window_height) // 2
    
    MAIN_INV_pos_y = window_top + int(335 * scale)

    MAIN_INV_equipment_pos_x = MAIN_INV_pos_x + (slot_size + border) * 3 + border
    MAIN_INV_equipment_pos_y = MAIN_INV_pos_y - int(310 * scale)

recalculate_inventory_positions()

# ============== INVENTORY SLOT COLORS AND STYLES ==============
INV_SLOT_BG_COLOR = (22, 26, 32, 255)
INV_SLOT_INNER_SHADOW = (10, 12, 16, 255)
INV_SLOT_BORDER_COLOR = (55, 65, 80, 255)
INV_SLOT_HOVER_BORDER = (230, 185, 60)
INV_SLOT_HOVER_FILL = (230, 185, 60, 25)
INV_SLOT_BORDER_RADIUS = 6
INV_SLOT_INNER_BORDER_RADIUS = 4
INV_SLOT_PADDING = 8
INV_ITEM_SHADOW_COLOR = (0, 0, 0, 120)
INV_ITEM_TEXT_COLOR = (245, 245, 250)

# ============== SHOP INVENTORY COLORS AND STYLING ==============
INV_SHOP_BG_COLOR = (35, 25, 30, 245)
INV_SHOP_BORDER_COLOR = (100, 70, 80, 255)
INV_SHOP_BORDER_WIDTH = 3
INV_SHOP_BORDER_RADIUS = 16
INV_SHOP_SHADOW_OFFSET = 12
INV_SHOP_TITLE_COLOR = (230, 185, 60)
INV_SHOP_PRICE_TEXT_COLOR = (255, 220, 80)
INV_SHOP_PRICE_SHADOW_COLOR = (0, 0, 0)
INV_SHOP_PRICE_BG_COLOR = (0, 0, 0, 150)
INV_SHOP_PRICE_BG_BORDER_RADIUS = 4

# ============== PLAYER INVENTORY COLORS AND POSITIONING ==============
INV_PLAYER_BG_COLOR = (18, 22, 28, 245)
INV_PLAYER_BORDER_COLOR = (70, 80, 95, 255)
INV_PLAYER_BORDER_WIDTH = 3
INV_PLAYER_BORDER_RADIUS = 20
INV_PLAYER_SHADOW_OFFSET = 15
INV_PLAYER_PREVIEW_OFFSET_X = 389
INV_PLAYER_PREVIEW_WIDTH = 190
INV_PLAYER_PREVIEW_HEIGHT = 275
INV_PLAYER_PREVIEW_Y_OFFSET = -310
INV_PLAYER_PORTRAIT_BORDER_RADIUS = 12
INV_PLAYER_PORTRAIT_BORDER_COLOR_1 = (100, 90, 60)
INV_PLAYER_PORTRAIT_BORDER_COLOR_2 = (230, 185, 60)
INV_PLAYER_MONEY_PANEL_BG_COLOR = (25, 30, 35)
INV_PLAYER_MONEY_PANEL_BORDER_COLOR = (55, 65, 75)
INV_PLAYER_MONEY_PANEL_WIDTH = 190
INV_PLAYER_MONEY_PANEL_HEIGHT = 36
INV_PLAYER_MONEY_PANEL_BORDER_RADIUS = 8
INV_PLAYER_MONEY_TEXT_COLOR = (255, 215, 0)
INV_PLAYER_MONEY_PANEL_Y_OFFSET = -25

# ============== PLAYER INVENTORY BUTTON POSITIONING ==============
INV_PLAYER_BTN_GAP_MIN = 6
INV_PLAYER_BTN_GAP_SCALE = 10
INV_PLAYER_BTN_SPACING_MIN = 8
INV_PLAYER_BTN_SPACING_SCALE = 12
INV_PLAYER_BTN_TOP_OFFSET = 25

# Right-side button positioning (majestic style)
INV_PLAYER_RIGHT_BTN_WIDTH = 260
INV_PLAYER_RIGHT_BTN_HEIGHT = 85
INV_PLAYER_RIGHT_BTN_GAP = 28
INV_PLAYER_RIGHT_BTN_MARGIN_X = 12
INV_PLAYER_RIGHT_BTN_EXTRA = 6.0  # multiplier for extra panel width on right

# ============== HOTBAR COLORS AND STYLING ==============
INV_HOTBAR_BG_COLOR = (20, 24, 30, 230)
INV_HOTBAR_BORDER_COLOR = (60, 70, 85, 255)
INV_HOTBAR_BORDER_WIDTH = 2
INV_HOTBAR_BORDER_RADIUS = 20
INV_HOTBAR_SHADOW_OFFSET = 8
INV_HOTBAR_SCALE = 0.85
INV_HOTBAR_ROWS = 1
INV_HOTBAR_COLUMNS = 10
INV_HOTBAR_GLOW_COLOR = (230, 185, 60)
INV_HOTBAR_ACTIVE_SLOT_BORDER_COLOR = (255, 215, 0)
INV_HOTBAR_ACTIVE_SLOT_BORDER_WIDTH = 3
INV_HOTBAR_ACTIVE_SLOT_BORDER_RADIUS = 6
INV_HOTBAR_Y_OFFSET = -25

# ============== SPLIT POPUP COLORS AND STYLING ==============
INV_SPLIT_POPUP_BG_COLOR = (25, 30, 38, 245)
INV_SPLIT_POPUP_BORDER_COLOR = (70, 80, 95, 255)
INV_SPLIT_POPUP_BORDER_WIDTH = 2
INV_SPLIT_POPUP_BORDER_RADIUS = 10
INV_SPLIT_POPUP_SHADOW_OFFSET = 6
INV_SPLIT_POPUP_BTN_COLOR = (40, 80, 50)
INV_SPLIT_POPUP_BTN_HOVER_COLOR = (60, 110, 70)
INV_SPLIT_POPUP_BTN_FONT_COLOR = (230, 240, 230)
INV_SPLIT_POPUP_BTN_CORNER_WIDTH_SCALE = 6
INV_SPLIT_POPUP_TEXT_COLOR = (240, 240, 245)

# ============== SLIDER COLORS ==============
INV_SLIDER_TRACK_COLOR = (30, 35, 45)
INV_SLIDER_KNOB_COLOR = (230, 185, 60)
INV_SLIDER_TRACK_HEIGHT = 18
INV_SLIDER_TRACK_THICKNESS = 6
INV_SLIDER_KNOB_WIDTH = 14
INV_SLIDER_KNOB_HEIGHT = 18

# ============== SHOP BUTTONS ==============
INV_SHOP_CLOSE_BTN_COLOR = (140, 45, 45)
INV_SHOP_CLOSE_BTN_HOVER_COLOR = (180, 60, 60)
INV_SHOP_CLOSE_BTN_FONT_COLOR = (255, 240, 240)

# ============== PLAYER INVENTORY BUTTONS ==============
INV_SKILLBAR_BTN_COLOR = (45, 60, 80)
INV_SKILLBAR_BTN_HOVER_COLOR = (65, 85, 110)
INV_SKILLBAR_BTN_FONT_COLOR = (230, 240, 255)
INV_SKILLTREE_BTN_COLOR = (55, 45, 75)
INV_SKILLTREE_BTN_HOVER_COLOR = (80, 65, 105)
INV_SKILLTREE_BTN_FONT_COLOR = (240, 230, 255)

# ============== ARCANE QUESTS BUTTON (right-side, below Talent Tree) ==============
# Gold & purple magical theme on a near-black base.
INV_ARCANEQUEST_BTN_COLOR        = (38, 22, 60)
INV_ARCANEQUEST_BTN_HOVER_COLOR  = (62, 38, 100)
INV_ARCANEQUEST_BTN_FONT_COLOR   = (255, 220, 140)

# ============== MYSTERIUM MAGNUM BUTTON (right-side, below Arcane Quests) ==============
# Magical cards theme: deep teal base with gold/cyan accents.
INV_MYSTERIUMMAGNUM_BTN_COLOR        = (15, 40, 55)
INV_MYSTERIUMMAGNUM_BTN_HOVER_COLOR  = (25, 65, 85)
INV_MYSTERIUMMAGNUM_BTN_FONT_COLOR   = (180, 230, 255)

# ============== INVENTORY OVERLAY AND SELECTED ITEM ==============
INV_OVERLAY_ALPHA = 160
INV_OVERLAY_COLOR = (5, 8, 12)
INV_OVERLAY_ALPHA_LERP = 0.15
INV_SELECTED_ITEM_SHADOW_COLOR = (0, 0, 0, 140)
INV_SELECTED_ITEM_SCALE_OFFSET = 0.08
INV_SELECTED_ITEM_SCALE_BASE = 1.05
INV_SELECTED_ITEM_SHADOW_TEXT_COLOR = (0, 0, 0)
INV_SELECTED_ITEM_TEXT_COLOR = (255, 255, 255)
INV_SELECTED_ITEM_SHADOW_OFFSET_X = 12
INV_SELECTED_ITEM_SHADOW_OFFSET_Y = 18
INV_SELECTED_ITEM_TEXT_OFFSET_X = 12
INV_SELECTED_ITEM_TEXT_OFFSET_Y = 10

# ============== SKILL COOLDOWN INDICATORS ==============
COOLDOWN_BAR_HEIGHT = 5
COOLDOWN_BAR_BG_COLOR = (20, 20, 25, 200)
COOLDOWN_BAR_FILL_COLOR = (255, 80, 80, 220)
COOLDOWN_BAR_FILL_HIGHLIGHT = (255, 160, 160, 180)
COOLDOWN_BAR_READY_COLOR = (80, 255, 120, 180)
COOLDOWN_OVERLAY_COLOR = (0, 0, 0, 140)
COOLDOWN_OVERLAY_TINT_STRENGTH = 0.3
COOLDOWN_TEXT_COLOR = (255, 255, 255)
COOLDOWN_TEXT_SIZE = 14
COOLDOWN_TEXT_BG_COLOR = (0, 0, 0, 160)
COOLDOWN_TEXT_BORDER_RADIUS = 6

# ============== DURABILITY BAR (TOOLS / WEAPONS) ==============
# Slim wear bar overlaid on item slots (inventory, hotbar, equipment).
# The fill colour is picked from DURABILITY_BAR_COLORS based on the
# item's :py:meth:`DurabilityMixin.durability_state` so the player can
# read wear at a glance.
DURABILITY_BAR_HEIGHT = 4
DURABILITY_BAR_BG_COLOR = (15, 15, 20, 220)
DURABILITY_BAR_BORDER_RADIUS = 2
DURABILITY_BAR_INSET = 3
# Tier colours keyed by ``durability_state()``:
#   full  -> bright green, plenty of life left
#   good  -> lime, slightly worn
#   worn  -> amber, getting risky
#   low   -> orange, almost gone
#   broken -> red (paired with a desaturated item render)
DURABILITY_BAR_COLORS = {
    "full":   (80, 220, 110, 230),
    "good":   (170, 220, 80, 230),
    "worn":   (240, 200, 60, 230),
    "low":    (240, 140, 60, 230),
    "broken": (220, 70, 70, 230),
}

def set_screen_size(screen_width, screen_height):
    global SCREEN_WIDTH, SCREEN_HEIGHT, bg
    SCREEN_WIDTH = int(screen_width)
    SCREEN_HEIGHT = int(screen_height)
    bg = _load_background(SCREEN_WIDTH, SCREEN_HEIGHT)

    recalculate_inventory_positions()
    
    try:
        update_scaled_fonts()
    except Exception:
        pass