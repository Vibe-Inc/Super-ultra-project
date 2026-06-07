import pygame
import src.config as cfg
from src.core.logger import logger
from src.ui.widgets import Button

class RuneSelectionMenu:
    def __init__(self, app, on_select):
        self.app = app
        self.on_select = on_select
        self.is_open = False
        
        self.font_title = cfg.get_font(int(45 * cfg.ui_scale()))
        
        self.screen_w = app.windowed_size[0] if not app.is_fullscreen else cfg.SCREEN_WIDTH
        self.screen_h = app.windowed_size[1] if not app.is_fullscreen else cfg.SCREEN_HEIGHT
        
        self.cx, self.cy = self.screen_w // 2, self.screen_h // 2
        
        self.runes = ["fire_rune", "ice_rune", "lightning_rune", "void_rune"]
        self.rune_names = ["Fire Rune", "Ice Rune", "Lightning Rune", "Void Rune"]
        self.rune_colors = [
            (220, 50, 50),
            (50, 150, 220),
            (220, 220, 50),
            (100, 30, 150)
        ]
        
        self.buttons = []
        btn_w = int(240 * cfg.ui_scale())
        btn_h = int(60 * cfg.ui_scale())
        spacing = int(20 * cfg.ui_scale())
        
        total_h = len(self.runes) * btn_h + (len(self.runes) - 1) * spacing
        start_y = self.cy - total_h // 2 + int(40 * cfg.ui_scale())
        
        for i, rune in enumerate(self.runes):
            btn_rect = pygame.Rect(self.cx - btn_w // 2, start_y + i * (btn_h + spacing), btn_w, btn_h)
            can_afford = self.app.money >= 50
            
            btn_text = f"{self.rune_names[i]} (50g)"
            btn_color = (40, 20, 30) if can_afford else (30, 30, 30)
            hover_color = self.rune_colors[i] if can_afford else (40, 40, 40)
            text_color = (255, 255, 255) if can_afford else (100, 100, 100)
            
            def make_on_click(r, afford):
                if afford:
                    return lambda: self._select_rune(r)
                return lambda: None
                
            btn = Button(
                rect=btn_rect,
                text=btn_text,
                color=btn_color,
                hover_color=hover_color,
                font=cfg.get_font(int(24 * cfg.ui_scale())),
                font_color=text_color,
                corner_width=8,
                on_click=make_on_click(rune, can_afford)
            )
            self.buttons.append(btn)
            
    def open(self):
        self.is_open = True
        
    def close(self):
        self.is_open = False
        
    def _select_rune(self, rune_type):
        self.close()
        if self.on_select:
            self.on_select(rune_type)

    def handle_event(self, event):
        if not self.is_open:
            return False
            
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn.rect.collidepoint(event.pos):
                    if btn.on_click:
                        btn.on_click()
                    return True
                
        return True

    def update(self, dt):
        pass

    def draw(self, surface):
        if not self.is_open:
            return
            
        # Draw overlay
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Draw title
        title_txt = self.font_title.render("Select Rune to Craft", True, (255, 215, 0))
        title_rect = title_txt.get_rect(center=(self.cx, self.cy - int(200 * cfg.ui_scale())))
        surface.blit(title_txt, title_rect)
        
        # Draw buttons
        for btn in self.buttons:
            btn.draw(surface)
