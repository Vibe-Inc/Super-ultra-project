import pygame
import sys

pygame.init()

# Розмір вікна
SCREEN_WIDTH, SCREEN_HEIGHT = 1800, 1200
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("super cooool project ;)")
icon = pygame.image.load("C:\\Users\\Filon\\pr\\EVERY\\smug.png")#Я ХЗ
pygame.display.set_icon(icon)

# Фон і текст
bg = pygame.image.load("C:\\Users\\Filon\\pr\\EVERY\\bg_menu.jpg")#Я ХЗ
myfont = pygame.font.Font("C:\\Users\\Filon\\pr\\EVERY\\font.ttf", 60)#Я ХЗ
text_logo = myfont.render('Super coooooool project', True, (0, 0, 0))
text_rect = text_logo.get_rect(center=(900, 430))

# Кнопки
button_color_START = (83, 112, 44)
button_hover_color_START = (123, 123, 34)
button_color_EXIT = (0, 126, 183)
button_hover_color_EXIT = (67, 152, 174)
text_color = (0, 0, 0)
button_font = pygame.font.Font("C:\\Users\\Filon\\pr\\EVERY\\font.ttf", 60)#Я ХЗ

# Тексти для кнопок
text_surf1 = button_font.render("START", True, text_color)
text_surf2 = button_font.render("EXIT", True, text_color)

button_width, button_height = 300, 100
gap = 50  # відстань між кнопками
button1_x = (SCREEN_WIDTH - (2 * button_width + gap)) // 2
button2_x = button1_x + button_width + gap
button_y = 700
corner_radius = 20

button1_rect = pygame.Rect(button1_x, button_y, button_width, button_height)
button2_rect = pygame.Rect(button2_x, button_y, button_width, button_height)

running = True
while running:
    screen.blit(bg, (0, 0))
    screen.blit(text_logo, text_rect)

    mouse_pos = pygame.mouse.get_pos()

    # Перша кнопка
    color1 = button_hover_color_START if button1_rect.collidepoint(mouse_pos) else button_color_START
    pygame.draw.rect(screen, color1, button1_rect, border_radius=corner_radius)
    text_rect1 = text_surf1.get_rect(center=button1_rect.center)
    screen.blit(text_surf1, text_rect1)

    # Друга кнопка
    color2 = button_hover_color_EXIT if button2_rect.collidepoint(mouse_pos) else button_color_EXIT
    pygame.draw.rect(screen, color2, button2_rect, border_radius=corner_radius)
    text_rect2 = text_surf2.get_rect(center=button2_rect.center)
    screen.blit(text_surf2, text_rect2)

    pygame.display.flip()
    pygame.time.Clock().tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if button1_rect.collidepoint(event.pos):
                print("START")
            elif button2_rect.collidepoint(event.pos):
                pygame.quit()
                sys.exit()
