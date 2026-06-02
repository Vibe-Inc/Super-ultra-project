import pygame
import math
from src.ui.menus.base import Menu
from src.ui.widgets import Button
import src.config as cfg
from database.GP_database import Gp_database
from src.items.items import create_item

class RecipeBookMenu(Menu):
    """
    Manages the recipe book UI.

    Displays a comprehensive list of all available crafting recipes in a paginated book format.
    Handles page-flipping animations, item image caching, and user navigation.

    Attributes:
        app (App):
            The main application reference.
        book_magnifier (float):
            Multiplier for scaling the recipe book UI elements.
        recipes (list):
            All available recipes loaded from the database.
        item_images (dict):
            Cached dictionary mapping item IDs to their respective image surfaces.
        recipes_per_spread (int):
            Number of recipes displayed per two-page spread.
        current_spread (int):
            The currently displayed spread index.
        max_spreads (int):
            The total number of available spreads based on recipe count.
        anim_start_time (int):
            Timestamp for the start of the opening animation.
        anim_duration (int):
            Duration of the opening animation in milliseconds.
        is_opening (bool):
            Flag indicating if the opening animation is currently active.
        flip_start_time (int):
            Timestamp for the start of the page-flipping animation.
        flip_duration (int):
            Duration of the page-flipping animation in milliseconds.
        is_flipping (bool):
            Flag indicating if the page-flipping animation is currently active.
        buttons (list):
            UI button widgets for navigation and closing the menu.

    Methods:
        __init__(app):
            Initialize the recipe book, cache item images, and set up animations.
        _render_text(font, text, color):
            Render and scale text based on the book magnifier.
        _setup_buttons():
            Configure and position the navigation buttons.
        prev_page():
            Trigger the logic to turn to the previous page spread.
        next_page():
            Trigger the logic to turn to the next page spread.
        _start_flip_anim():
            Initiate the page-flipping animation variables.
        close_menu():
            Transition back to the gameplay state.
        handle_event(event):
            Process user input, including button clicks and keyboard navigation.
        draw(screen):
            Render the recipe book background, animations, pages, and UI elements.
        _draw_book_background(surf, w, h, scale):
            Render the static visual base of the book including the cover and pages.
        _draw_recipes_for_current_spread(surf, w, h, scale, alpha):
            Render the current spread's recipes onto the book surface.
        _draw_recipe_card(surf, x, y, w, h, recipe, scale):
            Render an individual recipe card containing the crafting grid and result.
    """

    def __init__(self, app):
        super().__init__(app)

        self.book_magnifier = 1.35 

        db = Gp_database()
        self.recipes = db.get_all_recipes()
        db.close()

        self.item_images = {}
        for recipe in self.recipes:
            res_id = recipe['result_id']
            if res_id not in self.item_images:
                try: self.item_images[res_id] = create_item(res_id).image
                except Exception: pass
            
            for col in range(3):
                for row in range(3):
                    ing_id = recipe["matrix"][col][row]
                    if ing_id and ing_id not in self.item_images:
                        try: self.item_images[ing_id] = create_item(ing_id).image
                        except Exception: pass

        self.recipes_per_spread = 4
        self.current_spread = 0
        self.max_spreads = max(1, math.ceil(len(self.recipes) / self.recipes_per_spread))

        self.anim_start_time = pygame.time.get_ticks()
        self.anim_duration = 500  
        self.is_opening = True
        
        self.flip_start_time = 0
        self.flip_duration = 250  
        self.is_flipping = False

        self.buttons = []
        self._setup_buttons()

    def _render_text(self, font, text, color):
        surf = font.render(text, True, color)
        if self.book_magnifier != 1.0:
            w, h = surf.get_size()
            surf = pygame.transform.smoothscale(surf, (int(w * self.book_magnifier), int(h * self.book_magnifier)))
        return surf

    def _setup_buttons(self):
        self.buttons.clear()
        scale = cfg.ui_scale() * self.book_magnifier
        
        cx, cy = cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2
        book_w = int(860 * scale)
        book_h = int(600 * scale)
        
        btn_w, btn_h = int(140 * scale), int(40 * scale)
        
        back_rect = pygame.Rect(cx - btn_w // 2, cy + book_h // 2 - int(50 * scale), btn_w, btn_h)
        self.buttons.append(Button(
            back_rect, _("CLOSE BOOK"), cfg.button_color_EXIT, cfg.button_hover_color_EXIT,
            cfg.button_font, cfg.text_color, cfg.corner_radius, on_click=self.close_menu
        ))

        if self.current_spread > 0:
            prev_rect = pygame.Rect(cx - book_w // 2 + int(40 * scale), cy + book_h // 2 - int(50 * scale), btn_w, btn_h)
            self.buttons.append(Button(
                prev_rect, _("<- PREV"), (100, 80, 60), (130, 100, 80),
                cfg.button_font, cfg.text_color, cfg.corner_radius, on_click=self.prev_page
            ))

        if self.current_spread < self.max_spreads - 1:
            next_rect = pygame.Rect(cx + book_w // 2 - btn_w - int(40 * scale), cy + book_h // 2 - int(50 * scale), btn_w, btn_h)
            self.buttons.append(Button(
                next_rect, _("NEXT ->"), (100, 80, 60), (130, 100, 80),
                cfg.button_font, cfg.text_color, cfg.corner_radius, on_click=self.next_page
            ))

    def prev_page(self):
        if self.current_spread > 0 and not self.is_flipping:
            self.current_spread -= 1
            self._start_flip_anim()

    def next_page(self):
        if self.current_spread < self.max_spreads - 1 and not self.is_flipping:
            self.current_spread += 1
            self._start_flip_anim()

    def _start_flip_anim(self):
        self.is_flipping = True
        self.flip_start_time = pygame.time.get_ticks()
        self._setup_buttons()

    def close_menu(self):
        self.app.manager.set_state("gameplay")

    def handle_event(self, event):
        if self.is_opening or self.is_flipping:
            return

        super().handle_event(event)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close_menu()
            elif event.key == pygame.K_LEFT:
                self.prev_page()
            elif event.key == pygame.K_RIGHT:
                self.next_page()

    def draw(self, screen):
        current_time = pygame.time.get_ticks()
        
        open_progress = 1.0
        if self.is_opening:
            t = (current_time - self.anim_start_time) / self.anim_duration
            if t >= 1.0:
                self.is_opening = False
                open_progress = 1.0
            else:
                open_progress = 1.0 - math.pow(1.0 - t, 3)

        content_alpha = 255
        if self.is_flipping:
            t = (current_time - self.flip_start_time) / self.flip_duration
            if t >= 1.0:
                self.is_flipping = False
            else:
                if t < 0.5:
                    content_alpha = int(255 * (1.0 - t * 2))
                else:
                    content_alpha = int(255 * ((t - 0.5) * 2))

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((10, 10, 10, int(180 * open_progress)))
        screen.blit(overlay, (0, 0))

        scale = cfg.ui_scale() * self.book_magnifier
        cx, cy = cfg.SCREEN_WIDTH // 2, cfg.SCREEN_HEIGHT // 2
        book_w = int(860 * scale)
        book_h = int(600 * scale)

        y_offset = int((1.0 - open_progress) * 150 * scale)
        
        book_surf = pygame.Surface((book_w, book_h), pygame.SRCALPHA)
        
        self._draw_book_background(book_surf, book_w, book_h, scale)
        self._draw_recipes_for_current_spread(book_surf, book_w, book_h, scale, content_alpha)

        book_rect = book_surf.get_rect(center=(cx, cy + y_offset))
        
        if self.is_opening:
            book_surf.set_alpha(int(255 * open_progress))
            
        screen.blit(book_surf, book_rect.topleft)

        if not self.is_opening and not self.is_flipping:
            for button in self.buttons:
                button.draw(screen)

    def _draw_book_background(self, surf, w, h, scale):
        pygame.draw.rect(surf, (70, 35, 15), (0, 0, w, h), border_radius=int(20 * scale))
        pygame.draw.rect(surf, (45, 20, 10), (0, 0, w, h), width=max(2, int(4 * scale)), border_radius=int(20 * scale))

        page_color = (245, 235, 210)
        margin = int(15 * scale)
        left_page = pygame.Rect(margin, margin, w // 2 - margin, h - margin * 2)
        pygame.draw.rect(surf, page_color, left_page, border_top_left_radius=int(10*scale), border_bottom_left_radius=int(10*scale))

        right_page = pygame.Rect(w // 2, margin, w // 2 - margin, h - margin * 2)
        pygame.draw.rect(surf, page_color, right_page, border_top_right_radius=int(10*scale), border_bottom_right_radius=int(10*scale))

        spine_w = int(40 * scale)
        spine_rect = pygame.Rect(w // 2 - spine_w // 2, margin, spine_w, h - margin * 2)
        
        spine_shadow = pygame.Surface((spine_w, h - margin * 2), pygame.SRCALPHA)
        for i in range(spine_w // 2):
            alpha = int(100 * (1.0 - (i / (spine_w // 2))))
            pygame.draw.line(spine_shadow, (0, 0, 0, alpha), (i, 0), (i, h))
            pygame.draw.line(spine_shadow, (0, 0, 0, alpha), (spine_w - i - 1, 0), (spine_w - i - 1, h))
        surf.blit(spine_shadow, spine_rect.topleft)
        
        pygame.draw.line(surf, (150, 130, 100), (w // 2, margin + int(10*scale)), (w // 2, h - margin - int(10*scale)), max(1, int(2*scale)))

    def _draw_recipes_for_current_spread(self, surf, w, h, scale, alpha):
        content_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        
        if self.current_spread == 0:
            title = self._render_text(cfg.button_font, _("RECIPE BOOK"), (90, 50, 30))
            content_surf.blit(title, (w // 4 - title.get_width() // 2, int(30 * scale)))

        left_num = self._render_text(cfg.INV_nums_font, str(self.current_spread * 2 + 1), (150, 130, 100))
        right_num = self._render_text(cfg.INV_nums_font, str(self.current_spread * 2 + 2), (150, 130, 100))
        content_surf.blit(left_num, (int(30 * scale), h - int(35 * scale)))
        content_surf.blit(right_num, (w - int(40 * scale), h - int(35 * scale)))

        start_idx = self.current_spread * self.recipes_per_spread
        end_idx = min(start_idx + self.recipes_per_spread, len(self.recipes))
        
        card_w = int(340 * scale)
        card_h = int(190 * scale)
        start_y = int(90 * scale)
        gap_y = int(20 * scale)

        for i in range(start_idx, end_idx):
            local_idx = i - start_idx
            recipe = self.recipes[i]
            
            is_right_page = local_idx >= 2
            
            if not is_right_page:
                x = (w // 2 - card_w) // 2
            else:
                x = w // 2 + (w // 2 - card_w) // 2
                
            row = local_idx % 2
            y = start_y + row * (card_h + gap_y)

            self._draw_recipe_card(content_surf, x, y, card_w, card_h, recipe, scale)

        content_surf.set_alpha(alpha)
        surf.blit(content_surf, (0, 0))

    def _draw_recipe_card(self, surf, x, y, w, h, recipe, scale):
        card_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surf, (225, 210, 180), card_rect, border_radius=int(8 * scale))
        pygame.draw.rect(surf, (180, 160, 130), card_rect, width=max(1, int(2*scale)), border_radius=int(8 * scale))
        
        formatted_name = recipe['result_id'].replace("_", " ").title()
        title_text = self._render_text(cfg.INV_nums_font, formatted_name, (60, 40, 20))
        surf.blit(title_text, (x + int(15 * scale), y + int(10 * scale)))

        grid_slot_size = int(32 * scale)
        grid_padding = int(4 * scale)
        grid_start_x = x + int(20 * scale)
        grid_start_y = y + int(45 * scale)

        matrix = recipe["matrix"]
        for row in range(3):
            for col in range(3):
                slot_x = grid_start_x + col * (grid_slot_size + grid_padding)
                slot_y = grid_start_y + row * (grid_slot_size + grid_padding)
                slot_rect = pygame.Rect(slot_x, slot_y, grid_slot_size, grid_slot_size)

                pygame.draw.rect(surf, (210, 195, 165), slot_rect)
                pygame.draw.rect(surf, (150, 130, 100), slot_rect, width=1)

                ingredient = matrix[col][row]
                if ingredient:
                    if ingredient in self.item_images:
                        img = self.item_images[ingredient]
                        icon_size = grid_slot_size - int(6 * scale)
                        scaled_img = pygame.transform.scale(img, (icon_size, icon_size))
                        img_rect = scaled_img.get_rect(center=slot_rect.center)
                        surf.blit(scaled_img, img_rect)
                    else:
                        ing_text = self._render_text(cfg.INV_nums_font, ingredient[:3].capitalize(), (80, 60, 40))
                        tx = slot_x + (grid_slot_size - ing_text.get_width()) // 2
                        ty = slot_y + (grid_slot_size - ing_text.get_height()) // 2
                        surf.blit(ing_text, (tx, ty))

        arrow_x = grid_start_x + 3 * (grid_slot_size + grid_padding) + int(15 * scale)
        arrow_y = grid_start_y + grid_slot_size + (grid_padding // 2) - int(5 * scale)
        
        line_w = max(2, int(3 * scale))
        pygame.draw.line(surf, (100, 70, 50), (arrow_x, arrow_y), (arrow_x + int(30 * scale), arrow_y), line_w)
        pygame.draw.line(surf, (100, 70, 50), (arrow_x + int(20 * scale), arrow_y - int(8 * scale)), (arrow_x + int(30 * scale), arrow_y), line_w)
        pygame.draw.line(surf, (100, 70, 50), (arrow_x + int(20 * scale), arrow_y + int(8 * scale)), (arrow_x + int(30 * scale), arrow_y), line_w)

        out_size = int(54 * scale)
        out_x = arrow_x + int(45 * scale)
        out_y = arrow_y - out_size // 2
        out_rect = pygame.Rect(out_x, out_y, out_size, out_size)

        pygame.draw.rect(surf, (200, 185, 150), out_rect, border_radius=int(6*scale))
        pygame.draw.rect(surf, (120, 90, 60), out_rect, width=max(1, int(2*scale)), border_radius=int(6*scale))

        res_id = recipe['result_id']
        if res_id in self.item_images:
            img = self.item_images[res_id]
            res_icon_size = out_size - int(10 * scale)
            scaled_img = pygame.transform.scale(img, (res_icon_size, res_icon_size))
            img_rect = scaled_img.get_rect(center=out_rect.center)
            surf.blit(scaled_img, img_rect)
        else:
            res_short = self._render_text(cfg.INV_nums_font, res_id[:3].capitalize(), (60, 120, 60))
            rx = out_x + (out_size - res_short.get_width()) // 2
            ry = out_y + (out_size - res_short.get_height()) // 2
            surf.blit(res_short, (rx, ry))

        if recipe['amount'] > 1:
            out_amt = self._render_text(cfg.INV_nums_font, f"x{recipe['amount']}", (200, 50, 50))
            surf.blit(out_amt, (out_x + out_size - out_amt.get_width() - 2, out_y + out_size - out_amt.get_height() - 2))