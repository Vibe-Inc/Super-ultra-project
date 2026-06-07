import pygame
import src.config as cfg

class SpawnMenu:
    """
    Simple debug menu for spawning enemies on demand.

    Attributes:
        profiles (list[str]):
            List of enemy profile names to choose from.
        on_spawn (callable):
            Callback invoked with the selected profile name.
        on_close (callable):
            Callback invoked when the menu is closed.
        visible (bool):
            Whether the menu is currently shown.
        selected_index (int):
            Index of the currently highlighted profile.
        font (pygame.font.Font):
            Font used for menu text.
        width (int):
            Width of the menu panel.
        height (int):
            Height of the menu panel.
        rect (pygame.Rect):
            Bounding rectangle of the menu panel.

    Methods:
        __init__(profiles, on_spawn, on_close):
            Initialize the spawn menu.
        toggle():
            Toggle the menu visibility and reset selection.
        handle_event(event):
            Handle keyboard input for navigation and selection.
        draw(screen):
            Render the spawn menu overlay.
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
                while self.profiles[self.selected_index].startswith("---"):
                    self.selected_index = (self.selected_index - 1) % len(self.profiles)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.profiles)
                while self.profiles[self.selected_index].startswith("---"):
                    self.selected_index = (self.selected_index + 1) % len(self.profiles)
            elif event.key == pygame.K_RETURN:
                name = self.profiles[self.selected_index]
                if name.startswith("---"):
                    return
                self.on_spawn(name)
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
            is_label = name.startswith("---")
            if is_label:
                color = (130, 130, 150)
                text = self.font.render(name.strip("-"), True, color)
            else:
                color = (255, 255, 100) if i == self.selected_index else (180, 180, 180)
                text = self.font.render(name.upper(), True, color)
            screen.blit(text, (self.rect.x + 20, self.rect.y + 45 + i * 30))


class EffectsMenu:
    """
    Debug menu to apply any existing Effect to the player for a chosen duration.

    Controls:
      - Up/Down: select effect
      - Left/Right: decrease/increase duration (seconds)
      - Enter: apply effect
      - Esc / F10: close

    Attributes:
        effects (list[str]):
            List of effect class names to choose from.
        on_apply (callable):
            Callback invoked with (effect_name, duration).
        on_close (callable):
            Callback invoked when the menu is closed.
        visible (bool):
            Whether the menu is currently shown.
        selected_index (int):
            Index of the currently highlighted effect.
        duration (int):
            Currently selected duration in seconds.
        font (pygame.font.Font):
            Font used for menu text.
        width (int):
            Width of the menu panel.
        height (int):
            Height of the menu panel.
        rect (pygame.Rect):
            Bounding rectangle of the menu panel.

    Methods:
        __init__(effects, on_apply, on_close):
            Initialize the effects menu.
        toggle():
            Toggle the menu visibility and reset selection/duration.
        handle_event(event):
            Handle keyboard input for navigation, duration adjustment, and application.
        draw(screen):
            Render the effects menu overlay.
    """

    def __init__(self, effects: list[str], on_apply, on_close):
        self.effects = effects
        self.on_apply = on_apply
        self.on_close = on_close
        self.visible = False
        self.selected_index = 0
        self.duration = 5  # default seconds

        # UI elements
        self.font = cfg.get_font(max(12, int(20 * cfg.ui_scale())))
        self.width = 420
        self.height = 80 + len(effects) * 28
        self.rect = pygame.Rect(0, 0, self.width, self.height)

    def toggle(self):
        self.visible = not self.visible
        if self.visible:
            self.selected_index = 0
            self.duration = 5

    def handle_event(self, event):
        if not self.visible:
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.effects)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.effects)
            elif event.key == pygame.K_LEFT:
                self.duration = max(1, self.duration - 1)
            elif event.key == pygame.K_RIGHT:
                self.duration = self.duration + 1
            elif event.key == pygame.K_RETURN:
                self.on_apply(self.effects[self.selected_index], self.duration)
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

        # Title + duration
        title = self.font.render("EFFECTS (DEBUG)", True, (200, 200, 220))
        screen.blit(title, (self.rect.x + 15, self.rect.y + 10))
        dur_text = self.font.render(f"DURATION: {self.duration}s  (←/→)", True, (180, 180, 180))
        screen.blit(dur_text, (self.rect.x + self.width - 180, self.rect.y + 10))

        # Items
        for i, name in enumerate(self.effects):
            color = (255, 255, 100) if i == self.selected_index else (180, 180, 180)
            text = self.font.render(name, True, color)
            screen.blit(text, (self.rect.x + 20, self.rect.y + 45 + i * 28))