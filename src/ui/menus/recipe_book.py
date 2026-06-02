import pygame
from src.ui.menus.base import Menu
from src.ui.widgets import Button
import src.config as cfg
from database.GP_database import Gp_database

class RecipeBookMenu(Menu):
    """
    Displays a comprehensive list of all available recipes.

    Inherits from the base Menu class and provides a dedicated interface for
    browsing and viewing crafting recipes with their ingredients and results.

    Attributes:
        app (App):
            The main application reference.
        recipes (list):
            All recipes loaded from the database, containing ingredients and results.
        buttons (list):
            UI button widgets, including the "BACK TO GAME" button.

    Methods:
        __init__(app):
            Initialize the recipe book menu and load recipes from the database.
        close_menu():
            Return to the gameplay state and close the recipe book.
        handle_event(event):
            Process keyboard input and button interactions.
        draw(screen):
            Render the recipe list and UI elements to the screen.
    """

    def __init__(self, app):
        super().__init__(app)
        
        scale = cfg.ui_scale()
        btn_width = max(1, int(250 * scale))
        btn_height = max(1, int(80 * scale))
        
        back_rect = pygame.Rect(
            cfg.SCREEN_WIDTH // 2 - btn_width // 2, 
            cfg.SCREEN_HEIGHT - btn_height - int(50 * scale), 
            btn_width, btn_height
        )
        
        self.buttons = [
            Button(
                back_rect,
                _("BACK TO GAME"),
                cfg.button_color_EXIT,
                cfg.button_hover_color_EXIT,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=self.close_menu
            )
        ]
        
        db = Gp_database()
        self.recipes = db.get_all_recipes()
        db.close()

    def close_menu(self):
        self.app.manager.set_state("gameplay")

    def handle_event(self, event):
        super().handle_event(event)
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close_menu()

    def draw(self, screen):
        screen.fill((45, 35, 25))
        
        font = cfg.button_font
        title = font.render(_("RECIPE BOOK"), True, (240, 230, 200))
        screen.blit(title, (cfg.SCREEN_WIDTH // 2 - title.get_width() // 2, 40))
        
        list_font = cfg.INV_nums_font
        start_y = 150
        for i, recipe in enumerate(self.recipes):
            text = f"{i+1}. Result: {recipe['result_id']} (x{recipe['amount']})"
            lbl = list_font.render(text, True, (255, 255, 255))
            screen.blit(lbl, (100, start_y + i * 40))
            
        for button in self.buttons:
            button.draw(screen)