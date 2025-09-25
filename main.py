import pygame
import sys

pygame.init()

menu_state = "main"
audio = "on"

# Розмір вікна
SCREEN_WIDTH, SCREEN_HEIGHT = 1800, 1200
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("super cooool project ;)")
icon = pygame.image.load("images/smug.png")
pygame.display.set_icon(icon)

# Фон і текст
bg = pygame.transform.scale(pygame.image.load("images/bg_menu.jpg"), (SCREEN_WIDTH, SCREEN_HEIGHT))
myfont = pygame.font.Font("fonts/menu_font.ttf", 60)
text_logo = myfont.render('Super coooooool project', True, (0, 0, 0))
text_rect = text_logo.get_rect(center=(900, 430))

# Кнопки
button_color_START = (83, 112, 44)
button_hover_color_START = (123, 123, 34)
button_color_EXIT = (150, 0, 0)
button_hover_color_EXIT = (150, 50, 50)
button_color_SETTINGS = (0, 126, 183)
button_hover_color_SETTINGS = (67, 152, 174)
text_color = (0, 0, 0)
button_font = pygame.font.Font("fonts/menu_font.ttf", 60)

# Тексти для кнопок
text_surf1 = button_font.render("START", True, text_color)
text_surf2 = button_font.render("EXIT", True, text_color)
text_surf3 = button_font.render("SETTINGS", True, text_color)
text_surf4 = button_font.render("AUDIO", True, text_color)
text_surf5 = button_font.render("FULLSC", True, text_color)
text_surf6 = button_font.render("BACK", True, text_color)
text_surf7 = button_font.render("SOME SHIT", True, text_color) #place holder for later use

button_width, button_height = 300, 100
gap = 50  # відстань між кнопками
button1_x = (SCREEN_WIDTH - (2 * button_width + gap)) // 2
button2_x = button1_x + button_width + gap
button_y = 700
button2_y = 900
corner_radius = 20

#main menu
button1_rect = pygame.Rect(button1_x, button_y, button_width, button_height) #start
button2_rect = pygame.Rect(button2_x, button_y, button_width, button_height) #exit
button3_rect = pygame.Rect(button1_x, button2_y, button_width, button_height) #settings
#settings menu
button4_rect = pygame.Rect(100, button_y, button_width, button_height) #audio
button5_rect = pygame.Rect(500, button_y, button_width, button_height) #fullscreen or windowed
button6_rect = pygame.Rect(900, button_y, button_width, button_height) # back to the menu


running = True
while running:
    screen.blit(bg, (0, 0))
    screen.blit(text_logo, text_rect)

    mouse_pos = pygame.mouse.get_pos()

    # start
    if menu_state == "main":
        color1 = button_hover_color_START if button1_rect.collidepoint(mouse_pos) else button_color_START
        pygame.draw.rect(screen, color1, button1_rect, border_radius=corner_radius)
        text_rect1 = text_surf1.get_rect(center=button1_rect.center)
        screen.blit(text_surf1, text_rect1)

    # exit
    
    if menu_state == "main":
        color2 = button_hover_color_EXIT if button2_rect.collidepoint(mouse_pos) else button_color_EXIT
        pygame.draw.rect(screen, color2, button2_rect, border_radius=corner_radius)
        text_rect2 = text_surf2.get_rect(center=button2_rect.center)
        screen.blit(text_surf2, text_rect2)

    # settings
    
    if menu_state == "main":
        color3 = button_hover_color_SETTINGS if button3_rect.collidepoint(mouse_pos) else button_color_SETTINGS
        pygame.draw.rect(screen, color3, button3_rect, border_radius=corner_radius)
        text_rect3 = text_surf3.get_rect(center=button3_rect.center)
        screen.blit(text_surf3, text_rect3)
    
    #audio
    
    if menu_state == "settings":
        color4 = button_hover_color_SETTINGS if button4_rect.collidepoint(mouse_pos) else button_color_SETTINGS
        pygame.draw.rect(screen, color4, button4_rect, border_radius=corner_radius)
        text_rect4 = text_surf4.get_rect(center=button4_rect.center)
        screen.blit(text_surf4, text_rect4)
    
    #fullsc

    if menu_state == "settings":
        color5 = button_hover_color_SETTINGS if button5_rect.collidepoint(mouse_pos) else button_color_SETTINGS
        pygame.draw.rect(screen, color5, button5_rect, border_radius=corner_radius)
        text_rect5 = text_surf5.get_rect(center=button5_rect.center)
        screen.blit(text_surf5, text_rect5)

    #back

    if menu_state == "settings":
        color6 = button_hover_color_START if button6_rect.collidepoint(mouse_pos) else button_color_START
        pygame.draw.rect(screen, color6, button6_rect, border_radius=corner_radius)
        text_rect6 = text_surf6.get_rect(center=button6_rect.center)
        screen.blit(text_surf6, text_rect6)

    pygame.display.flip()
    pygame.time.Clock().tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if menu_state == "main":
                if button1_rect.collidepoint(event.pos):
                    print("START")
                elif button2_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
                elif button3_rect.collidepoint(event.pos):
                    menu_state = "settings"
            elif menu_state == "settings":
                if button4_rect.collidepoint(event.pos):
                    if audio == "on":
                        audio = "off"
                        print("audio is off")
                    if audio == "off":
                        audio = "on"
                        print("audio is on")
                elif button5_rect.collidepoint(event.pos):
                    print("fullscreen")
                elif button6_rect.collidepoint(event.pos):
                    menu_state = "main"

                
