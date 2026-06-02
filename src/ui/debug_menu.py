import pygame
import src.config as cfg

class SpawnMenu:
    """
    Simple debug menu for spawning enemies.
    """
    def __init__(self, profiles: list[str], on_spawn, on_close):
        self.profiles = profiles
        self.on_spawn = on_spawn
        self.on_close = on_close
        self.visible = False
        self.selected_index = 0
        
        # UI elements
        self.font = cfg.get_font(max(12, int(24 * cfg.ui_scale())))
        self.width = 300
        self.height = 40 + len(profiles) * 30
        self.rect = pygame.Rect(0, 0, self.width, self.height)

    def toggle(self):
        self.visible = not self.visible
        if self.visible:
            self.selected_index = 0

    def handle_event(self, event):
        if not self.visible:
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.profiles)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.profiles)
            elif event.key == pygame.K_RETURN:
                self.on_spawn(self.profiles[self.selected_index])
                self.visible = False
                self.on_close()
            elif event.key == pygame.K_ESCAPE or event.key == pygame.K_F10:
                self.visible = False
                self.on_close()

    def draw(self, screen):
        if not self.visible:
            return

        # Center on screen
        sw, sh = screen.get_size()
        self.rect.center = (sw // 2, sh // 2)

        # Background
        bg_surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (20, 20, 30, 220), bg_surf.get_rect(), border_radius=8)
        pygame.draw.rect(bg_surf, (100, 100, 120), bg_surf.get_rect(), 2, border_radius=8)
        screen.blit(bg_surf, self.rect.topleft)

        # Title
        title = self.font.render("SPAWN MOB", True, (200, 200, 220))
        screen.blit(title, (self.rect.x + 15, self.rect.y + 10))

        # Items
        for i, name in enumerate(self.profiles):
            color = (255, 255, 100) if i == self.selected_index else (180, 180, 180)
            text = self.font.render(name.upper(), True, color)
            screen.blit(text, (self.rect.x + 20, self.rect.y + 45 + i * 30))