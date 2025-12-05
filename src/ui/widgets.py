import pygame
import time
from typing import Callable

import src.config as cfg

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
        
        # Scale text if it's too wide for the button
        if self.text_surf.get_width() > self.rect.width - 20:
            scale_factor = (self.rect.width - 20) / self.text_surf.get_width()
            new_width = int(self.text_surf.get_width() * scale_factor)
            new_height = int(self.text_surf.get_height() * scale_factor)
            self.text_surf = pygame.transform.smoothscale(self.text_surf, (new_width, new_height))
            
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
                if mouse_x > cfg.SCREEN_WIDTH //2 and mouse_y > cfg.SCREEN_HEIGHT //2:
                    n, m = -tooltip_width -20, -tooltip_height -20
                elif mouse_x < cfg.SCREEN_WIDTH //2 and mouse_y > cfg.SCREEN_HEIGHT //2:
                    n, m = 20, -tooltip_height -20
                elif mouse_x > cfg.SCREEN_WIDTH //2 and mouse_y < cfg.SCREEN_HEIGHT //2:
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
    
    def update_target(self, new_rect, new_text):
        if self.target_rect != new_rect:
            self.target_rect = new_rect
            self.text = new_text
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

class Slider:
    """
    Represents a horizontal slider UI component for controlling a value, such as audio volume, in a Pygame application.

    Attributes:
        x (int): The x-coordinate of the slider track's starting position.
        y (int): The y-coordinate of the slider track's starting position.
        height (int): The thickness of the slider track in pixels.
        width (int): The width of the slider track's line.
        track_colour (tuple[int, int, int]): RGB color of the slider track.
        knob_colour (tuple[int, int, int]): RGB color of the draggable knob.
        knob_width (int): Width of the slider knob in pixels.
        knob_height (int): Height of the slider knob in pixels.
        track_length (int): Length of the slider track in pixels.
        value (float): Current normalized value of the slider (between `min_value` and `max_value`).
        dragging (bool): Indicates whether the slider knob is currently being dragged.
        current_volume (float): Current value applied to the controlled parameter (e.g., audio volume).
        knob_rect (pygame.Rect): Rectangle representing the position and size of the slider knob.

    Methods:
        draw(surface):
            Draws the slider track and knob onto the given Pygame surface.

        handle_event(event):
            Processes Pygame events to handle dragging of the slider knob. Sets volume in appropriate level.
    """
    def __init__(self, x, y, height, track_thickness, track_colour, knob_colour,
                 knob_width, knob_height, track_length, value=0.3, dragging=False, smooth_speed=0.05, action=None):
        self.x = x
        self.y = y
        self.height = height
        self.track_thickness = track_thickness
        self.track_colour = track_colour
        self.knob_colour = knob_colour
        self.knob_width = knob_width
        self.knob_height = knob_height
        self.track_length = track_length
        self.value = value
        self.dragging = dragging
        self.smooth_speed = smooth_speed
        self.action = action

        knob_x = self.x + int(self.value * self.track_length) - self.knob_width // 2
        knob_y = self.y + self.height // 2 - self.knob_height // 2
        self.knob_rect = pygame.Rect(knob_x, knob_y, self.knob_width, self.knob_height)

        # We don't set current_volume here anymore as this is a generic slider
        
    def draw(self, surface):
        track_start = (self.x, self.y + self.height // 2)
        track_end = (self.x + self.track_length, self.y + self.height // 2)
        pygame.draw.line(surface, self.track_colour, track_start, track_end, width=self.track_thickness)

        filled_end = (self.x + int(self.value * self.track_length), self.y + self.height // 2)
        pygame.draw.line(surface, (200, 200, 200), track_start, filled_end, width=self.track_thickness)

        knob_x = self.x + int(self.value * self.track_length) - self.knob_width // 2
        knob_y = self.y + self.height // 2 - self.knob_height // 2
        self.knob_rect = pygame.Rect(knob_x, knob_y, self.knob_width, self.knob_height)
        pygame.draw.rect(surface, self.knob_colour, self.knob_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.knob_rect.collidepoint(event.pos):
                self.dragging = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mx, _ = event.pos
            rel_x = max(0, min(mx - self.x, self.track_length))
            self.value = round(rel_x / self.track_length, 2)
            if self.action:
                self.action(self.value)

