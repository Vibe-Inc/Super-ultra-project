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
FPS = 60

def _load_background(screen_width, screen_height):
    try:
        bg_path = os.path.join(BASE_DIR, "assets", "bg_menu.jpg")
        return pygame.transform.scale(pygame.image.load(bg_path), (screen_width, screen_height))
    except (FileNotFoundError, pygame.error):
        return pygame.Surface((screen_width, screen_height))

bg = _load_background(SCREEN_WIDTH, SCREEN_HEIGHT)

SCREEN_BRIGHTNESS = 1.0
PROFILER_ENABLED = False

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
    inventory_tooltip_font = get_font(max(8, int(20 * scale)))
    tooltip_font_CREDITS = get_font(max(8, int(20 * scale)))
    INV_nums_font = get_font(max(8, int(15 * scale)))


# initialize scaled fonts
update_scaled_fonts()

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

tooltip_padding=8
tooltip_appear= 0.7

inventory_tooltip_rect = pygame.Rect(0,0,1,1)
inventory_tooltip_bg = (50, 50, 50)
inventory_tooltip_border = (200, 200, 200)
inventory_tooltip_font_color = (255, 255, 255)

tooltip_bg_CREDITS = (156, 179, 200)
tooltip_border_CREDITS = (54, 105, 121)

MAIN_INV_columns = 8
MAIN_INV_rows = 4
          
BASE_INV_slot_size = 70
BASE_INV_border = 3
BASE_INV_slot_color = (216, 223, 203)
BASE_INV_border_color = (33, 41, 48)

MAIN_INV_BACKGROUND=(109, 125, 123)
MAIN_INV_pos_x = SCREEN_WIDTH//2- (BASE_INV_slot_size + BASE_INV_border) * MAIN_INV_rows + BASE_INV_border
MAIN_INV_pos_y = SCREEN_HEIGHT//2

MAIN_INV_equipment_columns = 2
MAIN_INV_equipment_rows = 4
MAIN_INV_equipment_pos_x = MAIN_INV_pos_x + (BASE_INV_slot_size + BASE_INV_border) * 3 + BASE_INV_border
MAIN_INV_equipment_pos_y =MAIN_INV_pos_y-310


def set_screen_size(screen_width, screen_height):
    global SCREEN_WIDTH, SCREEN_HEIGHT, bg
    global MAIN_INV_pos_x, MAIN_INV_pos_y, MAIN_INV_equipment_pos_x, MAIN_INV_equipment_pos_y

    SCREEN_WIDTH = int(screen_width)
    SCREEN_HEIGHT = int(screen_height)
    bg = _load_background(SCREEN_WIDTH, SCREEN_HEIGHT)

    MAIN_INV_pos_x = SCREEN_WIDTH // 2 - (BASE_INV_slot_size + BASE_INV_border) * MAIN_INV_rows + BASE_INV_border
    MAIN_INV_pos_y = SCREEN_HEIGHT // 2
    MAIN_INV_equipment_pos_x = MAIN_INV_pos_x + (BASE_INV_slot_size + BASE_INV_border) * 3 + BASE_INV_border
    MAIN_INV_equipment_pos_y = MAIN_INV_pos_y - 310
    # update scaled fonts when the screen size changes
    try:
        update_scaled_fonts()
    except Exception:
        pass
