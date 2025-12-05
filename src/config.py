import pygame

SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
FPS = 60
bg = pygame.transform.scale(pygame.image.load("assets/bg_menu.jpg"), (SCREEN_WIDTH, SCREEN_HEIGHT))

LANGUAGE = 'en'
SUPPORTED_LANGUAGES = ['en', 'uk']

def get_font(size):
    if LANGUAGE == 'uk':
        return pygame.font.SysFont("arial", size)
    try:
        return pygame.font.Font("fonts/menu_font.ttf", size)
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
