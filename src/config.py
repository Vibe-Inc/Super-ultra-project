"""
Configuration module for Super Ultra Project.

This module defines global constants, color schemes, font utilities, and layout settings for the game UI and inventory system.
"""

import pygame
import os

pygame.font.init()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
FPS = 60

try:
    bg_path = os.path.join(BASE_DIR, "assets", "bg_menu.jpg")
    bg = pygame.transform.scale(pygame.image.load(bg_path), (SCREEN_WIDTH, SCREEN_HEIGHT))
except (FileNotFoundError, pygame.error):
    bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

SCREEN_BRIGHTNESS = 1.0

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

myfont = get_font(60)

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
button_font = get_font(60)
corner_radius = 20

tooltip_padding=8
tooltip_appear= 0.7

inventory_tooltip_rect = pygame.Rect(0,0,1,1)
inventory_tooltip_bg = (50, 50, 50)
inventory_tooltip_border = (200, 200, 200)
inventory_tooltip_font = get_font(20)
inventory_tooltip_font_color = (255, 255, 255)

tooltip_bg_CREDITS = (156, 179, 200)
tooltip_border_CREDITS = (54, 105, 121)
tooltip_font_CREDITS = get_font(20)

MAIN_INV_columns = 8
MAIN_INV_rows = 4
          
BASE_INV_slot_size = 70
BASE_INV_border = 3
BASE_INV_slot_color = (216, 223, 203)
BASE_INV_border_color = (33, 41, 48)

MAIN_INV_BACKGROUND=(109, 125, 123)

INV_nums_font = get_font(15)
MAIN_INV_pos_x = SCREEN_WIDTH//2- (BASE_INV_slot_size + BASE_INV_border) * MAIN_INV_rows + BASE_INV_border
MAIN_INV_pos_y = SCREEN_HEIGHT//2

MAIN_INV_equipment_columns = 2
MAIN_INV_equipment_rows = 4
MAIN_INV_equipment_pos_x = MAIN_INV_pos_x + (BASE_INV_slot_size + BASE_INV_border) * 3 + BASE_INV_border
MAIN_INV_equipment_pos_y =MAIN_INV_pos_y-310
