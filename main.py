import pygame
import sys
import time
from typing import Callable

pygame.init()

class Button:
    """
    A class representing a clickable button in a Pygame application.
    Attributes:
        rect (pygame.Rect): The rectangle defining the button's position and size.
        text (str): The text displayed on the button.
        color (tuple[int, int, int]): The RGB color of the button in its normal state.
        hover_color (tuple[int, int, int]): The RGB color of the button when hovered.
        font (pygame.font.Font): The font used to render the button's text.
        font_color (tuple[int, int, int]): The RGB color of the button's text.
        corner_width (int): The radius of the button's corners.
        on_click (Callable[[], None]): The function to call when the button is clicked.
        text_surf (pygame.Surface): The rendered text surface.
        text_rect (pygame.Rect): The rectangle for positioning the text surface.
    Methods:
        draw(screen):
            Draws the button on the given screen surface, changing color on hover.
    """

    def __init__(self, rect, text, color, hover_color, font, font_color, corner_width, on_click):
        self.rect: pygame.Rect = rect
        self.text: str = text
        self.color: tuple[int, int, int] = color
        self.hover_color: tuple[int, int, int] = hover_color
        self.font: pygame.font.Font = font
        self.font_color: tuple[int, int, int] = font_color
        self.corner_width: int = corner_width
        self.on_click: Callable[[], None] = on_click

        self.text_surf: pygame.Surface = self.font.render(self.text, True, self.font_color)
        self.text_rect: pygame.Rect = self.text_surf.get_rect(center=self.rect.center)

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        curr_color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(screen, curr_color, self.rect, border_radius=self.corner_width)
        screen.blit(self.text_surf, self.text_rect)      

class Tooltip:
    """
    Tooltip class for displaying contextual information when hovering over UI elements.
    
    Attributes:
        target_rect (pygame.Rect): The rectangle area that triggers the tooltip when hovered.
        text (str): The text content displayed in the tooltip. Supports multi-line with '\n'.
        color (tuple[int, int, int]): The background color of the tooltip box.
        border_color (tuple[int, int, int]): The color of the tooltip border.
        font (pygame.font.Font): The font used to render the tooltip text.
        font_color (tuple[int, int, int]): The color of the tooltip text.
        delay (float): Time in seconds to hover before the tooltip appears.
        padding (int): Padding in pixels around the tooltip text inside the box.
        hover_start (float | None): Timestamp when hover started, or None if not hovering.
        active (bool): Whether the tooltip is currently visible.
        rect (pygame.Rect | None): The rectangle representing the tooltip's position and size.

    Methods:
        hover_update(mouse_pos):
            Updates the tooltip's active state and position based on mouse hover and delay.
        draw(surface):
            Draws the tooltip box and its text on the given surface if active.
        draw_multiline_text(surface, x, y):
            Renders multi-line text centered within the tooltip box.
    """
    def draw_multiline_text(self, surface, x, y): 

        lines = self.text.split('\n')
        line_height = self.font.get_height()
        box_width = self.rect.width - 2 * self.padding if self.rect else 0
        for i, line in enumerate(lines):
            txt_surface = self.font.render(line, True, self.font_color)
            line_width = txt_surface.get_width()
            draw_x = x + (box_width - line_width) // 2 if box_width > 0 else x
            draw_y = y + i * line_height 
            surface.blit(txt_surface, (draw_x, draw_y))

    def __init__(self,target_rect  ,text, color ,border_color, font , font_color, delay , padding):
        self.target_rect: pygame.Rect = target_rect
        self.text: str = text
        self.color: tuple[int, int, int] = color
        self.border_color: tuple[int, int, int] = border_color
        self.font: pygame.font.Font = font
        self.font_color: tuple[int, int, int] = font_color
        self.delay: float=delay
        self.padding: int=padding
    
        self.hover_start= None
        self.active: bool = 0 
        self.rect= None
    

    def hover_update(self, mouse_pos):
        now = time.time() 
        if self.target_rect.collidepoint(mouse_pos) or (self.active and self.rect and self.rect.collidepoint(mouse_pos)):
            if self.hover_start is None:
                self.hover_start = now
            hovered = now - self.hover_start
            if not self.active and hovered > self.delay:
                lines = self.text.split('\n')
                num_lines = len(lines)
                line_height = self.font.get_height()
                max_width = max(self.font.size(line)[0] for line in lines) if lines else 0
                total_height = line_height * num_lines

                mouse_x, mouse_y = pygame.mouse.get_pos()
                tooltip_width = max_width
                tooltip_height = line_height * num_lines
                if mouse_x > app.SCREEN_WIDTH //2 and mouse_y > app.SCREEN_HEIGHT //2:
                    n, m = -tooltip_width -20, -tooltip_height -20
                elif mouse_x < app.SCREEN_WIDTH //2 and mouse_y > app.SCREEN_HEIGHT //2:
                    n, m = 20, -tooltip_height -20
                elif mouse_x > app.SCREEN_WIDTH //2 and mouse_y < app.SCREEN_HEIGHT //2:
                    n, m = -tooltip_width -20, 20
                else:n, m = 20, 20

                self.rect = pygame.Rect(
                    mouse_pos[0] + n, 
                    mouse_pos[1] + m,
                    max_width + self.padding * 2,
                    total_height + self.padding * 2 
                )
                self.active = True
        else:
            self.hover_start = None
            self.active = 0
            self.rect = None
    def draw(self, surface):
        if self.active and self.rect:
            pygame.draw.rect(surface, self.color, self.rect)
            pygame.draw.rect(surface, self.border_color, self.rect, 3)
            self.draw_multiline_text(
                surface,
                self.rect.x+self.padding,
                self.rect.y+self.padding
            )



class Menu:
    """
    Represents a menu interface containing interactive buttons.
    Attributes:
        app (App): Reference to the main application instance.
        buttons (list[Button]): List of Button objects displayed in the menu.
        tooltips: list[Tooltip] List of Tooltip objects for button tooltips.
    Methods:
        draw(screen):
            Draws all buttons onto the provided screen surface.
        handle_event(event):
            Handles pygame events, triggering button actions when clicked.
    """
    
    def __init__(self, app: "App"):
        self.app = app
        self.buttons: list[Button] = []
        self.tooltips: list[Tooltip] = [] 

    def draw(self, screen):

        screen.blit(self.beta_logo_img, self.beta_logo_rect)

        for button in self.buttons:
            button.draw(screen)

        mouse_pos = pygame.mouse.get_pos()
        for tooltip in self.tooltips:
            tooltip.hover_update(mouse_pos)
            tooltip.draw(screen)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for button in self.buttons:
                if button.rect.collidepoint(event.pos):
                    button.on_click()

class MainMenu(Menu):
    """
    MainMenu class represents the main menu screen of the application, inheriting from the Menu base class.
    Attributes:
        buttons (list): A list of Button objects representing the interactive buttons on the main menu.
    Args:
        app (App): The main application instance, providing configuration and resources for the menu.
    Methods:
        start_game():
            Callback for the "START" button. Initiates the game start sequence.
        exit_game():
            Callback for the "EXIT" button. Exits the application by quitting pygame and terminating the process.
        open_settings():
            Callback for the "SETTINGS" button. Switches the current menu to the settings menu.
    """

    def __init__(self, app: "App"):
        super().__init__(app)

        button_width, button_height = 300, 100
        gap = 50
        tot_width = 2 * button_width + gap
        
        start_rect = pygame.Rect((app.SCREEN_WIDTH - tot_width) // 2, 700, button_width, button_height)
        exit_rect = pygame.Rect((app.SCREEN_WIDTH - tot_width) // 2 + button_width + gap, 700, button_width, button_height)
        settings_rect = pygame.Rect((app.SCREEN_WIDTH - tot_width) // 2, 900, button_width, button_height)
        credits_rect = pygame.Rect((app.SCREEN_WIDTH - tot_width) // 2 + button_width + gap, 900, button_width, button_height)

        self.buttons = [
            Button(
                start_rect,
                "START",
                app.button_color_START,
                app.button_hover_color_START,
                app.button_font,
                app.text_color,
                app.corner_radius,
                on_click=self.start_game
            ),
            Button(
                exit_rect,
                "EXIT",
                app.button_color_EXIT,
                app.button_hover_color_EXIT,
                app.button_font,
                app.text_color,
                app.corner_radius,
                on_click=self.exit_game
            ),
            Button(
                settings_rect,
                "SETTINGS",
                app.button_color_SETTINGS,
                app.button_hover_color_SETTINGS,
                app.button_font,
                app.text_color,
                app.corner_radius,
                on_click=self.open_settings
            ),
           Button(
                credits_rect,
                "Credits",
                app.tooltip_color_CREDITS,
                app.tooltip_hover_color_CREDITS,
                app.button_font,
                app.text_color,
                app.corner_radius,
                on_click=self.credits
            )
        ]
        self.beta_logo_img = pygame.image.load("images/beta_logo.png")
        self.beta_logo_img = pygame.transform.scale(self.beta_logo_img, (200, 200))
        self.beta_logo_rect = self.beta_logo_img.get_rect(center=(1500, 950))

        self.tooltips = [
            Tooltip(
                credits_rect,
                "Dedicated professionals of Vibe.Inc \n After tiresly thinking about the project\nCreated Shashki",
                app.tooltip_bg_CREDITS,
                app.tooltip_border_CREDITS,
                app.tooltip_font_CREDITS,
                app.text_color,
                app.tooltip_appear,
                app.tooltip_padding
            ),
            Tooltip(
                self.beta_logo_rect,
                "Our logo that we need to think of",
                app.tooltip_bg_CREDITS,
                app.tooltip_border_CREDITS,
                app.tooltip_font_CREDITS,
                app.text_color,
                app.tooltip_appear,
                app.tooltip_padding
            )
        ]


    def start_game(self):
        print("START")

    def exit_game(self):
        pygame.quit()
        sys.exit()

    def open_settings(self):
        self.app.current_menu = self.app.set_menu("settings")

    def credits(self):
        print("Credits")

class SettingsMenu(Menu):
    """
    SettingsMenu is a subclass of Menu that provides a settings interface for the application.
    Attributes:
        buttons (list): A list of Button objects representing the settings options (Audio, Fullscreen, Back).
    Methods:
        __init__(app: "App"):
            Initializes the SettingsMenu with buttons for toggling audio, toggling fullscreen mode, and returning to the main menu.
        toggle_audio():
            Toggles the application's audio setting between "on" and "off", and prints the current state.
        toggle_fullscreen():
            Toggles the application's display mode between fullscreen and windowed, and prints the current state.
        back_to_main():
            Switches the current menu back to the main menu.
    """

    def __init__(self, app: "App"):
        super().__init__(app)
        
        button_width, button_height = 300, 100
        button_y = 700

        audio_rect = pygame.Rect(100, button_y, button_width, button_height)
        fullscreen_rect = pygame.Rect(500, button_y, button_width, button_height)
        back_rect = pygame.Rect(900, button_y, button_width, button_height)

        self.buttons = [
            Button(
                audio_rect,
                "AUDIO",
                app.button_color_SETTINGS,
                app.button_hover_color_SETTINGS,
                app.button_font,
                app.text_color,
                app.corner_radius,
                on_click=self.toggle_audio
            ),
            Button(
                fullscreen_rect,
                "FULLSC",
                app.button_color_SETTINGS,
                app.button_hover_color_SETTINGS,
                app.button_font,
                app.text_color,
                app.corner_radius,
                on_click=self.toggle_fullscreen
            ),
            Button(
                back_rect,
                "BACK",
                app.button_color_SETTINGS,
                app.button_hover_color_SETTINGS,
                app.button_font,
                app.text_color,
                app.corner_radius,
                on_click=self.back_to_main
            )
        ]

    def toggle_audio(self):
        if self.app.audio == "on":
            self.app.audio = "off"
            print("AUDIO OFF")
        else:
            self.app.audio = "on"
            print("AUDIO ON")

    def toggle_fullscreen(self):
        if self.app.is_fullscreen:
            pygame.display.set_mode((self.app.SCREEN_WIDTH, self.app.SCREEN_HEIGHT))
            self.app.is_fullscreen = False
            print("WINDOWED")
        else:
            pygame.display.set_mode((self.app.SCREEN_WIDTH, self.app.SCREEN_HEIGHT), pygame.FULLSCREEN)
            self.app.is_fullscreen = True
            print("FULLSCREEN")

    def back_to_main(self):
        self.app.current_menu = self.app.set_menu("main")

class App:
    """
    Main application class for the Super Ultra Project game.
    Attributes:
        SCREEN_WIDTH (int): Width of the game window.
        SCREEN_HEIGHT (int): Height of the game window.

        screen (pygame.Surface): The main display surface.
        icon (pygame.Surface): The window icon image.
        bg (pygame.Surface): The background image for the menu.
        myfont (pygame.font.Font): Font used for the logo text.
        text_logo (pygame.Surface): Rendered logo text surface.
        text_rect (pygame.Rect): Rectangle for positioning the logo text.

        button_color_START (tuple): Color for the START button.
        button_hover_color_START (tuple): Hover color for the START button.
        button_color_EXIT (tuple): Color for the EXIT button.
        button_hover_color_EXIT (tuple): Hover color for the EXIT button.
        button_color_SETTINGS (tuple): Color for the SETTINGS button.
        button_hover_color_SETTINGS (tuple): Hover color for the SETTINGS button.

        text_color (tuple): Color for button text.
        button_font (pygame.font.Font): Font used for button text.
        corner_radius (int): Corner radius for rounded buttons.

        tooltip_padding (int): Padding around tooltip.
        tooltip_appear (float): Delay before tooltip appears.
        tooltip_color_CREDITS (tuple): Tooltip color for credits button.
        tooltip_hover_color_CREDITS (tuple): Tooltip hover color for credits button.
        tooltip_bg_CREDITS (tuple): Tooltip background color for credits.
        tooltip_border_CREDITS (tuple): Tooltip border color for credits.
        tooltip_font_CREDITS (pygame.font.Font): Tooltip font for credits.

        menus (dict): Dictionary of menu states and their corresponding menu objects.
        menu_state (str): Current active menu state.

        audio (str): Audio state ("on" or "off").
        is_fullscreen (bool): Fullscreen mode state.
        clock (pygame.time.Clock): Clock object for controlling frame rate.
        FPS (int): Frames per second.
    Methods:
        set_menu(menu_name: str):
            Sets the current menu state.
        run():
            Main loop of the application. Handles rendering, events, and menu logic.
    """

    def __init__(self):
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = 1800, 1200
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("super cooool project ;)")
        self.icon = pygame.image.load("images/smug.png")
        pygame.display.set_icon(self.icon)

        self.bg = pygame.transform.scale(pygame.image.load("images/bg_menu.jpg"), (self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.myfont = pygame.font.Font("fonts/menu_font.ttf", 60)
        self.text_logo = self.myfont.render('Super coooooool project', True, (0, 0, 0))
        self.text_rect = self.text_logo.get_rect(center=(900, 430))

        self.button_color_START = (83, 112, 44)
        self.button_hover_color_START = (123, 123, 34)
        self.button_color_EXIT = (150, 0, 0)
        self.button_hover_color_EXIT = (150, 50, 50)
        self.button_color_SETTINGS = (0, 126, 183)
        self.button_hover_color_SETTINGS = (67, 152, 174)
        self.text_color = (0, 0, 0)
        self.button_font = pygame.font.Font("fonts/menu_font.ttf", 60)
        self.corner_radius = 20

        self.tooltip_padding=8
        self.tooltip_appear= 0.7
        self.tooltip_color_CREDITS = (0, 0, 255)
        self.tooltip_hover_color_CREDITS = (123, 123, 200)
        self.tooltip_bg_CREDITS = (255, 0, 0)
        self.tooltip_border_CREDITS = (255, 255, 255)
        self.tooltip_font_CREDITS = pygame.font.Font("fonts/menu_font.ttf", 20)
        self.menus = {
            "main": MainMenu(self),
            "settings": SettingsMenu(self)
        }

        self.menu_state = "main"
        self.audio = "on"
        self.is_fullscreen = False

        self.clock = pygame.time.Clock()
        self.FPS = 60

    def set_menu(self, menu_name: str):
        self.menu_state = menu_name

    def run(self):
        running = True
        while running:
            self.screen.blit(self.bg, (0, 0))
            self.screen.blit(self.text_logo, self.text_rect)

            self.menus[self.menu_state].draw(self.screen)

            pygame.display.flip()
            self.clock.tick(self.FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()
                self.menus[self.menu_state].handle_event(event)

if __name__ == "__main__":
    app = App()
    app.run()
