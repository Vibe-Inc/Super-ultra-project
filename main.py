import pygame
import sys
import time
from typing import Callable
import pytmx


pygame.init()

class Map:
    """
    Represents a tile-based game map loaded from a Tiled map file.
    Attributes:
        map_file (str): Path to the Tiled map file (.tmx).
        game_map (pytmx.TiledMap): The loaded Tiled map object.
    Methods:
        __init__(map_file: str):
            Initializes the Map instance with the given map file path.
        draw(screen):
            Draws the visible layers of the map onto the provided Pygame screen surface.
            Loads the map file if it hasn't been loaded yet.
    """

    def __init__(self, map_file: str):
        self.map_file = map_file
        self.game_map: pytmx.TiledMap = None

    def draw(self, screen):
        if self.game_map is None:
            self.game_map = pytmx.load_pygame(self.map_file)

        for layer in self.game_map.visible_layers:
            for x, y, gid in layer:
                tile = self.game_map.get_tile_image_by_gid(gid)
                if tile:
                    screen.blit(tile, (x * self.game_map.tilewidth,
                                       y * self.game_map.tileheight))


class State:
    """
    Represents a base state in a state management system.
    This class should be subclassed to implement specific states for an application.
    Each state can handle events and draw itself to the screen.
    Attributes:
        manager: Reference to the state manager controlling state transitions.
    Methods:
        handle_event(event): Handles input events specific to the state.
        draw(screen): Renders the state to the provided screen surface.
    """

    def __init__(self, app: "App"):
        self.app = app

    def handle_event(self, event):
        pass

    def draw(self, screen):
        pass


class StateManager:
    """
    Manages different application states such as main menu, settings, and credits.
    Args:
        app: The main application object, passed to each state.
    Attributes:
        states (dict): Dictionary mapping state names to their corresponding state objects.
        current_state: The currently active state object.
    Methods:
        set_state(name):
            Sets the current state to the state associated with the given name.
        get_state():
            Returns the name of the currently active state, or None if no state is active.
        handle_event(event):
            Delegates event handling to the current state if one is active.
        draw(screen):
            Delegates drawing to the current state if one is active.
    """

    def __init__(self, app: "App"):
        self.states = {
            "main": MainMenu(app),
            "settings": SettingsMenu(app),
            "credits": CreditsMenu(app),
            "gameplay": Game(app),
            "pause": PauseMenu(app)
        }
        self.current_state = None

    def set_state(self, name):
        self.current_state = self.states.get(name)

    def get_state(self):
        for name, state in self.states.items():
            if state == self.current_state:
                return name
        return None

    def handle_event(self, event):
        if self.current_state:
            self.current_state.handle_event(event)

    def draw(self, screen):
        if self.current_state:
            self.current_state.draw(screen)


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
    

    def __init__(self,target_rect  ,text, color ,border_color, font , font_color, delay , padding):
        self.target_rect: pygame.Rect = target_rect
        self.text: str = text
        self.color: tuple[int, int, int] = color
        self.border_color: tuple[int, int, int] = border_color
        self.font: pygame.font.Font = font
        self.font_color: tuple[int, int, int] = font_color
        self.delay: float = delay
        self.padding: int = padding
    
        self.hover_start = None
        self.active: bool = False 
        self.rect = None

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
            self.active = False
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

class Inventory:
    """
    Represents a grid-based inventory in the game.
    Attributes:
        columns (int): The number of columns in the inventory grid.
        rows (int): The number of rows in the inventory grid.
        items (list[list[tuple[Item, int] | None]]): A 2D list representing the slots, where each slot holds either None or a tuple of (item object, count).
        slot_size (int): The width and height of a single slot in pixels.
        pos_x (int): The x-coordinate (top-left) position of the inventory on the screen.
        pos_y (int): The y-coordinate (top-left) position of the inventory on the screen.
        border (int): The size of the border/spacing between slots.
        slot_color (tuple[int, int, int]): The RGB color of the inventory slots.
        slot_border_color (tuple[int, int, int]): The RGB color of the inventory's outer border.
        selected_item (tuple[Item, int] | None): The item currently being dragged or held by the mouse from this inventory.

    Methods:
        __init__(self, columns, rows, items, slot_size, pos_x, pos_y, slot_border, slot_color, slot_border_color): Initializes the inventory object.
        draw(self, screen): Renders the inventory grid, border, and items onto the screen.
        inventory_interactions(self, event, manager): Handles mouse button events (clicks) for item picking up, dropping, stacking, swapping, and splitting within the inventory.
    """
    def __init__(self, columns, rows, items, slot_size, pos_x, pos_y, slot_border, slot_color, slot_border_color ):
        self.columns:int = columns
        self.rows:int = rows
        if not items:
            self.items:list = [[None for _ in range(self.rows)] for _ in range(self.columns)]
        else:
            self.items:list = items
        self.slot_size:int = slot_size
        self.pos_x:int = pos_x
        self.pos_y:int = pos_y
        self.border:int = slot_border
        self.slot_color:tuple[int, int, int]= slot_color
        self.slot_border_color:tuple[int, int, int]= slot_border_color

        self.selected_item = None

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            self.slot_border_color,
            (self.pos_x, self.pos_y,
             (self.slot_size + self.border) * self.columns + self.border,
             (self.slot_size + self.border) * self.rows + self.border)
        )
      
        for n in range(self.columns):
            for m in range(self.rows):
                rect = (
                    self.pos_x + (self.slot_size + self.border) * n + self.border,
                    self.pos_y + (self.slot_size + self.border) * m + self.border,
                    self.slot_size,
                    self.slot_size
                )
                pygame.draw.rect(screen, self.slot_color, rect)

                if self.items[n][m]:
                    item, count = self.items[n][m]
                    screen.blit(item.resize(self.slot_size), rect)
                    if count > 1:
                        font_obj = app.INV_nums_font
                        obj = font_obj.render(str(count), True, (0, 0, 0))
                        screen.blit(obj, (rect[0] + 50, rect[1] + 50))

    def inventory_interactions(self,event,manager):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        x = (mouse_x - self.pos_x) // (self.slot_size + self.border)
        y = (mouse_y - self.pos_y) // (self.slot_size + self.border)
        if 0 <= x < self.columns and 0 <= y < self.rows:
                slot = self.items[x][y]
                if event.button == 1:
                    if manager.selected_item:
                        if slot:
                            if slot[0].id == manager.selected_item[0].id:
                                slot[1] += manager.selected_item[1]
                                manager.selected_item = None
                            else:
                                self.items[x][y], manager.selected_item = manager.selected_item, self.items[x][y]
                        else:
                            self.items[x][y] = manager.selected_item
                            manager.selected_item = None
                    else:
                        if slot:
                            manager.selected_item = slot
                            self.items[x][y] = None

                elif event.button == 3 and slot and not manager.selected_item and slot[1] > 1:
                    split_count = (slot[1] + 1) // 2
                    manager.selected_item = [slot[0], split_count]
                    self.items[x][y][1] -= split_count
                    if self.items[x][y][1] <= 0:
                        self.items[x][y] = None
  
class MAIN_player_inventory(Inventory):
    
    def __init__(self, app:"App"):
        super().__init__(
            app.MAIN_INV_columns,
            app.MAIN_INV_rows,
            app.MAIN_INV_items,
            app.BASE_INV_slot_size,
            app.MAIN_INV_pos_x,
            app.MAIN_INV_pos_y,
            app.BASE_INV_border,
            app.BASE_INV_slot_color,
            app.BASE_INV_border_color
        )
    def draw(self, screen):
        pygame.draw.rect( 
            screen,
            app.MAIN_INV_BACKGROUND,
            (app.MAIN_INV_pos_x-15, app.MAIN_INV_pos_y-335,
             (app.BASE_INV_slot_size + app.BASE_INV_border) * app.MAIN_INV_columns + app.BASE_INV_border+30,
             (app.BASE_INV_slot_size + app.BASE_INV_border) * app.MAIN_INV_rows + app.BASE_INV_border +350),
             0, 16, 70 , 70)
            
        pygame.draw.rect(
            screen,
            (0, 0, 0),
            (app.SCREEN_WIDTH//2+100, app.MAIN_INV_pos_y-305, 190, 275),
            0, 15, 50, 50, 50, 50
            ) #maybe some kind of character preview?

        return super().draw(screen)
    
class MAIN_player_inventory_equipment(Inventory):
    def __init__(self,app :"App"):
        super().__init__(
            app.MAIN_INV_equipment_columns,
            app.MAIN_INV_equipment_rows,
            None,
            app.BASE_INV_slot_size,
            app.MAIN_INV_equipment_pos_x,
            app.MAIN_INV_equipment_pos_y,
            app.BASE_INV_border,
            app.BASE_INV_slot_color,
            app.BASE_INV_border_color
        )
    pass
    
class INVENTORY_manager:
    """
    Represents the central manager for all in-game inventory operations. 
    It tracks which inventories are currently active/visible and manages the state 
    of items being dragged by the player.

    Attributes:
        selected_item (tuple[Item, int] | None): The item stack (item object, count) 
            currently held by the mouse cursor, or False/None if nothing is selected. 
            (Note: In the provided code, it's initialized as bool=False but used as a tuple or None).
        active_inventories (list[Inventory | None]): A list of Inventory objects 
            (like player bag, equipment, or a chest) that should be drawn and accept interaction.
        player_inventory_opened (bool): Flag indicating if the player's main inventory 
            window (and associated equipment) is currently open.

    Methods:
        __init__(self): Initializes the manager state.
        add_active_inventory(self, inventory): Adds an Inventory object to the list of active/visible inventories.
        remove_active_inventory(self, inventory): Removes an Inventory object from the active list.
        draw(self, screen): Draws all active inventories and the currently selected item (if any) at the mouse position.
        handle_event(self, event): Distributes mouse events to all active inventories for interaction processing.
        PLAYER_inventory_open(self, event: pygame.event.Event, pl_inv, equip_inv): Toggles the player's inventory 
            and equipment windows on and off, typically upon pressing the 'I' key (pygame.K_i), 
            and triggers interaction handling if a mouse button is clicked while open.
    """
    def __init__(self):
        self.selected_item:bool = False
        self.active_inventories:list[Inventory|None] = []
        self.player_inventory_opened:bool = False


    def add_active_inventory (self, inventory):
        if inventory not in self.active_inventories:
            self.active_inventories.append(inventory)

    def remove_active_inventory (self, inventory):
        if inventory in self.active_inventories:
            self.active_inventories.remove(inventory)
    
    def draw(self, screen):
        for inv in self.active_inventories:
            inv.draw(screen)
        if self.selected_item:
            mx, my = pygame.mouse.get_pos()
            item, count = self.selected_item
            screen.blit(item.resize(app.BASE_INV_slot_size), (mx - app.BASE_INV_slot_size//2, my - app.BASE_INV_slot_size//2))
            font = app.INV_nums_font
            obj = font.render(str(count), True, (0, 0, 0))
            screen.blit(obj, (mx + app.BASE_INV_slot_size//2 - 20 , my + app.BASE_INV_slot_size//2 - 20))
    
    def handle_event(self, event):
        for inv in self.active_inventories:
            inv.inventory_interactions(event, self)
    
    def PLAYER_inventory_open(self,event: pygame.event.Event,pl_inv,equip_inv):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i:
                self.player_inventory_opened = not self.player_inventory_opened   
                if self.player_inventory_opened is True:
                    app.INV_manager.add_active_inventory(pl_inv)
                    app.INV_manager.add_active_inventory(equip_inv)
                else:
                    app.INV_manager.remove_active_inventory(pl_inv)
                    app.INV_manager.remove_active_inventory(equip_inv)
        if self.player_inventory_opened is True and event.type == pygame.MOUSEBUTTONDOWN:
            app.INV_manager.handle_event(event)

   
class TEST_ITEMS:     #only for testing 
    def __init__(self, color, id):
        self.id = id
        self.color = color
    def resize(self, size):
        surf = pygame.Surface((size, size))
        pygame.draw.rect(surf, self.color, (0, 0, size, size))
        return surf
    

class Menu(State):
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
        settings_rect = pygame.Rect((app.SCREEN_WIDTH - tot_width) // 2, 850, button_width, button_height)
        credits_rect = pygame.Rect((app.SCREEN_WIDTH - tot_width) // 2 + button_width + gap, 850, button_width, button_height)

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
                "CREDITS",
                app.button_color_CREDITS,
                app.button_hover_color_CREDITS,
                app.button_font,
                app.text_color,
                app.corner_radius,
                on_click=self.open_credits
            )
        ]
        self.beta_logo_img = pygame.image.load("assets/beta_logo.png")
        self.beta_logo_img = pygame.transform.scale(self.beta_logo_img, (200, 200))
        self.beta_logo_rect = self.beta_logo_img.get_rect(center=(1600, 900))

        self.tooltips = [
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

    def draw(self, screen):
        screen.blit(self.beta_logo_img, self.beta_logo_rect, )
        for button in self.buttons:
            button.draw(screen)
        mouse_pos = pygame.mouse.get_pos()
        for tooltip in self.tooltips:
            tooltip.hover_update(mouse_pos)
            tooltip.draw(screen)

    def start_game(self):
        self.app.manager.set_state("gameplay")

    def exit_game(self):
        pygame.quit()
        sys.exit()

    def open_settings(self):
        self.app.manager.set_state("settings")

    def open_credits(self):
        self.app.manager.set_state("credits")


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
        
        audio_rect = pygame.Rect(600, button_y, button_width, button_height)
        back_rect = pygame.Rect(1000, button_y, button_width, button_height)

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
                back_rect,
                "BACK",
                app.button_color_SETTINGS_BACK,
                app.button_hover_color_SETTINGS_BACK,
                app.button_font,
                app.text_color,
                app.corner_radius,
                on_click=self.back_to_main
            )
        ]

    def toggle_audio(self):
        if self.app.audio == "on":
            self.app.audio = "off"
            pygame.mixer.music.set_volume(0.0)
            print("AUDIO OFF")
        else:
            self.app.audio = "on"
            pygame.mixer.music.set_volume(0.3)
            print("AUDIO ON")

    def back_to_main(self):
        self.app.manager.set_state("main")


class CreditsMenu(Menu):
    """
    CreditsMenu displays a credits screen with a styled box containing multi-line text and a BACK button.

    Attributes:
        buttons (list[Button]): List of buttons in the menu (only BACK).
        credits_text (str): The credits text, with lines separated by '\n'.
        font (pygame.font.Font): Font used for the credits text.
        font_color (tuple): Color of the credits text.
        padding (int): Padding around the text inside the box.
        credits_lines (list[str]): List of lines in the credits text.
        box_rect (pygame.Rect): Rectangle for the credits box.
        box_color (tuple): Background color of the credits box.
        box_border (tuple): Border color of the credits box.

    Methods:
        draw(screen): Draws the credits box, text, and BACK button.
        back_to_main(): Returns to the main menu.
    """
    def __init__(self, app: "App"):
        super().__init__(app)
        button_width, button_height = 300, 100
        back_rect = pygame.Rect(1400, 850, button_width, button_height)
        self.buttons = [
            Button(back_rect,
                "BACK",
                app.button_color_SETTINGS_BACK,
                app.button_hover_color_SETTINGS_BACK,
                app.button_font,
                app.text_color,
                app.corner_radius,
                on_click=self.back_to_main
            )
        ]
        self.credits_text = """CREDITS:\nVibe inc idea, production and execution\nArt not by Vibe inc\nMusic not by Vibe inc\nMain sponsor: Vibe inc\nSpecial thanks to Vibe inc"""
        self.font :pygame.font.Font= app.myfont
        self.font_color: tuple = app.text_color
        self.padding: int = 30
        self.credits_lines = self.credits_text.split('\n')
        num_credits_lines = len(self.credits_lines)
        line_height = self.font.get_height()
        max_width = max(self.font.size(line)[0] for line in self.credits_lines)if num_credits_lines else 0
        box_width = max_width + 2 * self.padding
        box_height = line_height * num_credits_lines + 2 * self.padding
        self.box_rect = pygame.Rect(
            (app.SCREEN_WIDTH - box_width) // 2, 300, box_width, box_height)
        self.box_color = (245, 222, 179) 
        self.box_border = (139, 49, 19)

    def draw(self, screen):
        pygame.draw.rect(screen, self.box_color, self.box_rect, border_radius=15)
        pygame.draw.rect(screen, self.box_border, self.box_rect, 10, border_radius=15)

        y = self.box_rect.y + self.padding
        box_width = self.box_rect.width - 2 * self.padding
        for line in self.credits_lines:
            surf = self.font.render(line, True, self.font_color)
            line_width = surf.get_width()
            x = self.box_rect.x + self.padding + (box_width - line_width) // 2
            screen.blit(surf, (x, y))
            y += self.font.get_height()
        for button in self.buttons:
            button.draw(screen)

    def back_to_main(self):
        self.app.manager.set_state("main")


class PauseMenu(Menu):
    """
    Represents the pause menu in the game, providing options to resume gameplay or return to the main menu.
    Args:
        app (App): The main application instance containing configuration and state management.
    Attributes:
        app (App): Reference to the main application instance.
        pause_menu_color (tuple): RGBA color for the pause menu overlay.
        buttons (list[Button]): List of Button objects for menu actions ("RESUME" and "MAIN MENU").
    Methods:
        draw(screen):
            Draws the pause menu overlay and its buttons on the provided screen surface.
        resume_game():
            Callback to resume gameplay by setting the application state to "gameplay".
        back_to_main():
            Callback to return to the main menu by setting the application state to "main".
    """

    def __init__(self, app: "App"):
        self.app = app

        button_width, button_height = 300, 100

        self.pause_menu_color = (0, 0, 0, 180)

        self.buttons = [
            Button(
                pygame.Rect((app.SCREEN_WIDTH - button_width) // 2, 650, button_width, button_height),
                "RESUME",
                app.button_color_START,
                app.button_hover_color_START,
                app.button_font,
                app.text_color,
                app.corner_radius,
                on_click=self.resume_game
            ),
            Button(
                pygame.Rect((app.SCREEN_WIDTH - button_width) // 2, 800, button_width, button_height),
                "MAIN MENU",
                app.button_color_EXIT,
                app.button_hover_color_EXIT,
                app.button_font,
                app.text_color,
                app.corner_radius,
                on_click=self.back_to_main
            )
        ]

    def draw(self, screen):
        overlay = pygame.Surface((self.app.SCREEN_WIDTH, self.app.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(self.pause_menu_color)
        screen.blit(overlay, (0, 0))

        for button in self.buttons:
            button.draw(screen)


    def resume_game(self):
        self.app.manager.set_state("gameplay")

    def back_to_main(self):
        self.app.manager.set_state("main")


class Game(State):
    """
    Game class represents the main gameplay state of the application.
    Attributes:
        app (App): Reference to the main application instance.
        map (Map): The game map loaded from a Tiled map file.
        character (Character): The player character instance.
    Methods:
        draw(screen):
            Draws the game map onto the provided screen surface.
        handle_event(event):
            Handles pygame events specific to the gameplay state.

    """

    def __init__(self, app: "App"):
        super().__init__(app)
        self.character = Character()
        self.map = Map("maps/test-map-1.tmx")

        app.INV_manager.player_inventory_opened

        self.MAIN_player_inv = MAIN_player_inventory(app)
        self.PLAYER_inventory_equipment = MAIN_player_inventory_equipment(app)

    def draw(self, screen):

        self.map.draw(screen)

        dt = self.app.clock.get_time() / 1000  # seconds since last frame
        self.character.update(dt)
        self.character.draw(screen)

        if  app.INV_manager.player_inventory_opened:
            app.INV_manager.draw(screen)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.manager.set_state("pause")
        app.INV_manager.PLAYER_inventory_open(event,self.MAIN_player_inv,self.PLAYER_inventory_equipment)

class Character:
    """
        class entity needed might do it later

        Represents the player character with animated movement in four directions.
    
        Attributes:
            animations (dict): Dictionary containing lists of Pygame surfaces for each direction ("up", "down", "side").
            direction (str): Current movement direction of the character ("up", "down", "side").
            image (pygame.Surface): Current frame of the character to be drawn.
            pos (pygame.Vector2): Position of the character on the screen.
            speed (float): Movement speed of the character in pixels per second.

            frame_index (int): Current frame index for animation.
            animation_speed (float): Number of frames per second for animation.
            time_accumulator (float): Accumulates time to control animation frame switching.
            flip (bool): Whether to flip the character horizontally (used for left/right movement).
            moving (bool): Whether the character is currently moving.

        Methods:
            update(dt):
                Updates the characters position and animation based on keyboard input.
                Args:
                    dt (float): Time elapsed since the last frame in seconds.
            draw(screen):
                Draws the characters current frame to the given Pygame surface.
                Args:
                    screen (pygame.Surface): The surface to draw the character on.
        """
    def __init__(self):
        self.animations = {
            "down":  [pygame.transform.scale(pygame.image.load(f"assets/characters/WomanHuman1(Recolor)/FrontWalk/FrontWalk{i}.png"), (85, 85)) for i in range(1, 5)],
            "up":    [pygame.transform.scale(pygame.image.load(f"assets/characters/WomanHuman1(Recolor)/BackWalk/BackWalk{i}.png"), (85, 85)) for i in range(1, 5)],
            "side":  [pygame.transform.scale(pygame.image.load(f"assets/characters/WomanHuman1(Recolor)/SideWalk/SideWalk{i}.png"), (85, 85)) for i in range(1, 5)],
        }

        self.direction = "down"
        self.image = self.animations[self.direction][0]
        self.pos = pygame.Vector2(960, 540)  
        self.speed = 200  

        self.frame_index = 0
        self.animation_speed = 10
        self.time_accumulator = 0
        self.flip = False
        self.moving = False

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.moving = False 

        if keys[pygame.K_w]:
            self.pos.y -= self.speed * dt
            self.direction = "up"
            self.moving = True
        elif keys[pygame.K_s]:
            self.pos.y += self.speed * dt
            self.direction = "down"
            self.moving = True
        elif keys[pygame.K_a]:
            self.pos.x -= self.speed * dt
            self.direction = "side"
            self.flip = True
            self.moving = True
        elif keys[pygame.K_d]:
            self.pos.x += self.speed * dt
            self.direction = "side"
            self.flip = False
            self.moving = True

        if self.moving:
            self.time_accumulator += dt
            if self.time_accumulator > 1 / self.animation_speed:
                self.time_accumulator = 0
                self.frame_index = (self.frame_index + 1) % len(self.animations[self.direction])
            self.image = self.animations[self.direction][self.frame_index]
        else:
            self.frame_index = 0
            self.image = self.animations[self.direction][0]

    def draw(self, screen):
        if self.direction == "side":
            screen.blit(pygame.transform.flip(self.image, self.flip, False), self.pos)
        else:
            screen.blit(self.image, self.pos)


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
        button_color_SETTINGS_BACK (tuple): Color for the SETTINGS 'Back' button.
        button_hover_color_SETTINGS_BACK (tuple): Hover color for the SETTINGS 'Back' button.
        button_color_CREDITS (tuple): Color for the CREDITS button.
        button_hover_color_CREDITS (tuple): Hover color for the CREDITS button. 

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

        INV_manager (INVENTORY_manager): The central manager for all inventory operations.

        MAIN_INV_rows (int): Number of rows in the main inventory.
        MAIN_INV_columns (int): Number of columns in the main inventory. 
        MAIN_INV_items (list): 2D list representing items in the main inventory.
        MAIN_INV_slot_size (int): Size of each inventory slot. # Used as BASE_INV_slot_size
        MAIN_INV_border (int): Border size between inventory slots. # Used as BASE_INV_border
        MAIN_INV_slot_color (tuple): Color of inventory slots. # Used as BASE_INV_slot_color
        MAIN_INV_border_color (tuple): Color of inventory slot borders. # Used as BASE_INV_border_color
        MAIN_INV_BACKGROUND (tuple): Background color for the inventory area.
        INV_nums_font (pygame.font.Font): Font for item count numbers in inventory.
        MAIN_INV_pos_x (int): X position of the main inventory on screen.
        MAIN_INV_pos_y (int): Y position of the main inventory on screen.
        
        MAIN_INV_equipment_columns (int): Number of columns in the equipment inventory. 
        MAIN_INV_equipment_rows (int): Number of rows in the equipment inventory. 
        MAIN_INV_equipment_pos_x (int): X position of the equipment inventory.
        MAIN_INV_equipment_pos_y (int): Y position of the equipment inventory.

        BASE_INV_slot_size (int): Standard size of an inventory slot in pixels.
        BASE_INV_border (int): Standard border/spacing size for inventory slots.
        BASE_INV_slot_color (tuple): Standard color for inventory slots (RGB).
        BASE_INV_border_color (tuple): Standard color for inventory borders (RGB).
        
        INV_BUTTONS_font (pygame.font.Font): Font for inventory buttons. 
        MAIN_INV_BUTTON_color (tuple): Color for inventory buttons.
        MAIN_INV_BUTTON_hover_color (tuple): Hover color for inventory buttons.

        menus (dict): Dictionary of menu states and their corresponding menu objects. # Not used in __init__
        menu_state (str): Current active menu state. # Not used in __init__

        audio (str): Audio state ("on" or "off").
        is_fullscreen (bool): Fullscreen mode state.
        clock (pygame.time.Clock): Clock object for controlling frame rate.
        FPS (int): Frames per second.

        manager (StateManager): The state management system controlling game/menu flow.

    Methods:
        set_menu(menu_name: str):
            Sets the current menu state using the StateManager.
        music_play():
            Loads and starts the background music, setting the volume based on the 'audio' attribute.
        run():
            Main loop of the application. Handles rendering, event processing, clock ticking, and state management logic.
    """

    def __init__(self):
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = 1920, 1080
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("super cooool project ;)")
        self.icon = pygame.image.load("assets/smug.png")
        pygame.display.set_icon(self.icon)

        self.bg = pygame.transform.scale(pygame.image.load("assets/bg_menu.jpg"), (self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.myfont = pygame.font.Font("fonts/menu_font.ttf", 60)
        self.text_logo = self.myfont.render('Super coooooool project', True, (0, 0, 0))
        self.text_rect = self.text_logo.get_rect(center=(self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT//2 - 150))

        self.button_color_START = (83, 112, 44)
        self.button_hover_color_START = (123, 123, 34)
        self.button_color_EXIT = (150, 0, 0)
        self.button_hover_color_EXIT = (150, 50, 50)
        self.button_color_SETTINGS = (0, 126, 183)
        self.button_hover_color_SETTINGS = (67, 152, 174)
        self.button_color_SETTINGS_BACK = (83, 112, 44)
        self.button_hover_color_SETTINGS_BACK = (123, 123, 34)        
        self.button_color_CREDITS = (250, 205, 82)
        self.button_hover_color_CREDITS = (255, 220, 97)

        self.text_color = (0, 0, 0)
        self.button_font = pygame.font.Font("fonts/menu_font.ttf", 60)
        self.corner_radius = 20

        self.tooltip_padding=8
        self.tooltip_appear= 0.7

        self.tooltip_bg_CREDITS = (156, 179, 200)
        self.tooltip_border_CREDITS = (54, 105, 121)
        self.tooltip_font_CREDITS = pygame.font.Font("fonts/menu_font.ttf", 20)

        self.INV_manager = INVENTORY_manager()

        self.MAIN_INV_columns = 8
        self.MAIN_INV_rows = 4
        self.MAIN_INV_items = [[None for _ in range(self.MAIN_INV_rows)] for _ in range(self.MAIN_INV_columns)]
        colors = [(255,0,0), (0,0,255), (255,255,0)]
        for i in range(min(self.MAIN_INV_columns, 3)):
            self.MAIN_INV_items[i][0] = [TEST_ITEMS(colors[i], i), i+10]
          
        self.BASE_INV_slot_size = 70
        self.BASE_INV_border = 3
        self.BASE_INV_slot_color = (216, 223, 203)
        self.BASE_INV_border_color = (33, 41, 48)

        self.MAIN_INV_BACKGROUND=(109, 125, 123)

        self.INV_nums_font = pygame.font.Font("fonts/menu_font.ttf", 15)
        self.MAIN_INV_pos_x = self.SCREEN_WIDTH//2- (self.BASE_INV_slot_size + self.BASE_INV_border) * self.MAIN_INV_rows + self.BASE_INV_border
        self.MAIN_INV_pos_y = self.SCREEN_HEIGHT//2

        self.MAIN_INV_equipment_columns = 2
        self.MAIN_INV_equipment_rows = 4
        self.MAIN_INV_equipment_pos_x = self.MAIN_INV_pos_x + (self.BASE_INV_slot_size + self.BASE_INV_border) * 3 + self.BASE_INV_border
        self.MAIN_INV_equipment_pos_y =self.MAIN_INV_pos_y-310

        self.audio = "on"
        self.is_fullscreen = False

        self.clock = pygame.time.Clock()
        self.FPS = 60

        self.manager = StateManager(self)

    def music_play(self):
        pygame.mixer.music.load('sounds/LIFE (Instrumental).wav')
        pygame.mixer.music.set_volume(0.3 if self.audio == "on" else 0.0)
        pygame.mixer.music.play(-1)

    def run(self):
        self.manager.set_state("main")
        self.music_play()

        running = True
        while running:
            dt = self.clock.tick(self.FPS) / 1000  # seconds since last frame

            self.screen.blit(self.bg, (0, 0))
            if self.manager.get_state() != "credits":
                self.screen.blit(self.text_logo, self.text_rect)

            self.manager.draw(self.screen)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()
                self.manager.handle_event(event)


if __name__ == "__main__":
    app = App()
    app.run()