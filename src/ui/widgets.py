import pygame
import time
from typing import Callable

import src.config as cfg
from src.core.logger import logger

class Button:
    """
    Clickable button class.

    Attributes:
        rect (pygame.Rect):
            Rectangle defining the button's position and size.
        text (str):
            Text displayed on the button.
        color (tuple[int, int, int]):
            RGB color of the button in its normal state.
        hover_color (tuple[int, int, int]):
            RGB color of the button when hovered.
        font (pygame.font.Font):
            Font used to render the button's text.
        font_color (tuple[int, int, int]):
            RGB color of the button's text.
        corner_width (int):
            Radius of the button's corners.
        on_click (Callable[[], None]):
            Function to call when the button is clicked.
        text_surf (pygame.Surface):
            Rendered text surface.
        text_rect (pygame.Rect):
            Rectangle for positioning the text surface.

    Methods:
        draw(screen):
            Draw the button on the given screen surface, changing color on hover.
            Args:
                screen (pygame.Surface): The surface to draw the button on.
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
        self._update_text_surface()

    def _update_text_surface(self):
        self.text_surf = self.font.render(self.text, True, self.font_color)

        # Scale text if it's too wide for the button
        if self.text_surf.get_width() > self.rect.width - 20:
            scale_factor = (self.rect.width - 20) / self.text_surf.get_width()
            new_width = int(self.text_surf.get_width() * scale_factor)
            new_height = int(self.text_surf.get_height() * scale_factor)
            self.text_surf = pygame.transform.smoothscale(self.text_surf, (new_width, new_height))

        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def set_text(self, text: str):
        if text == self.text:
            return
        self.text = text
        self._update_text_surface()

    def _adjust_color_brightness(self, color, factor):
        """Adjust color brightness by a factor."""
        return tuple(min(255, max(0, int(c * factor))) for c in color)

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self.rect.collidepoint(mouse_pos)
        base_color = self.hover_color if is_hovered else self.color
        
        # Draw subtle shadow (small offset, less opacity for flat design)
        shadow_offset = 2
        shadow_rect = pygame.Rect(
            self.rect.x + shadow_offset,
            self.rect.y + shadow_offset,
            self.rect.width,
            self.rect.height
        )
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 50))  # Lighter shadow
        # Create rounded shadow
        shadow_mask = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_mask, (255, 255, 255, 255), 
                        (0, 0, shadow_rect.width, shadow_rect.height), 
                        border_radius=self.corner_width)
        shadow_surf.blit(shadow_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(shadow_surf, shadow_rect.topleft)
        
        # Draw flat button background with rounded corners
        pygame.draw.rect(screen, base_color, self.rect, border_radius=self.corner_width)
        
        # Draw subtle border (slightly darker than base color)
        border_color = self._adjust_color_brightness(base_color, 0.7)
        pygame.draw.rect(screen, border_color, self.rect, width=1, border_radius=self.corner_width)
        
        # Draw main text (no shadow to avoid overlapping/duplicated look)
        screen.blit(self.text_surf, self.text_rect)


class Tooltip:
    """
    Delightful tooltip with rounded corners, soft drop shadow, styled text
    hierarchy (gold title · soft-white stats · muted description), a thin
    gold accent bar, and a smooth fade-in / slide-up entrance animation.

    The constructor signature is unchanged so every existing caller keeps working.

    Attributes:
        target_rect (pygame.Rect):
            Hover target that triggers the tooltip.
        text (str):
            Multi-line content (``'\\n'``-separated).  The first line is treated
            as the **title**, the last non-empty line as the **description**, and
            everything in between as **stat lines**.
        color / border_color / font / font_color / delay / padding:
            Kept for API compatibility; the visual palette is defined by the
            class-level colour constants below.
        hover_start (float | None):
            Timestamp when the cursor entered the target.
        active (bool):
            Whether the tooltip is currently visible.
        rect (pygame.Rect | None):
            Bounding rect of the *content* area (excl. shadow padding).
        show_time (float | None):
            Timestamp when the tooltip became active (for animations).
    """

    # ── Colour palette ──────────────────────────────────────────────
    BG_COLOR         = (18, 22, 32, 235)       # Deep dark background
    BORDER_COLOR     = (200, 170, 80, 200)     # Warm gold border
    ACCENT_COLOR     = (230, 185, 60)           # Gold accent bar / title
    TITLE_COLOR      = (255, 215, 80)           # Bright gold title text
    STAT_COLOR       = (210, 218, 235)          # Soft blue-white stat text
    DESC_COLOR       = (140, 152, 170)          # Muted description text
    SEPARATOR_COLOR  = (230, 185, 60, 70)       # Subtle gold separator line
    SHADOW_COLOR     = (0, 0, 0)                # Shadow base colour

    # ── Layout constants ────────────────────────────────────────────
    ANIM_DURATION    = 0.15    # seconds for fade-in
    SLIDE_OFFSET     = 6       # pixels to slide up during entrance
    CORNER_RADIUS    = 10      # rounded corners
    BORDER_WIDTH     = 2       # border thickness
    ACCENT_HEIGHT    = 3       # thin gold bar at the top
    ACCENT_GAP       = 3       # gap below accent bar
    SEPARATOR_GAP    = 4       # gap around the separator line
    SHADOW_LAYERS    = 5       # number of layered rects for soft shadow
    MIN_WIDTH        = 120     # minimum tooltip width

    def __init__(self, target_rect, text, color, border_color, font,
                 font_color, delay, padding):
        self.target_rect: pygame.Rect = target_rect
        self.text: str = text
        # Kept for API compatibility; visual palette uses class constants.
        self.color = color
        self.border_color = border_color
        self.font: pygame.font.Font = font
        self.font_color = font_color
        self.delay: float = delay
        self.padding: int = padding

        self.hover_start = None
        self.active: bool = False
        self.rect = None
        self.show_time = None
        self._cached_surface: pygame.Surface | None = None
        self._cache_key: str = ""
        self._pad: int = 0          # shadow padding (for blit offset)

    # ── Internal helpers ────────────────────────────────────────────

    def _compute_dimensions(self):
        """Return ``(tooltip_w, tooltip_h, line_height, num_lines)``."""
        lines = self.text.split("\n")
        num_lines = len(lines)
        line_height = self.font.get_height()
        max_width = max((self.font.size(ln)[0] for ln in lines), default=0)

        accent_space = self.ACCENT_HEIGHT + self.ACCENT_GAP
        separator_space = self.SEPARATOR_GAP if num_lines > 1 else 0

        tooltip_w = max(max_width + self.padding * 2, self.MIN_WIDTH)
        tooltip_h = (line_height * num_lines
                     + self.padding * 2
                     + accent_space
                     + separator_space)
        return tooltip_w, tooltip_h, line_height, num_lines

    def _build_surface(self):
        """Render the complete tooltip (shadow + chrome + text) onto a
        :class:`pygame.Surface` with per-pixel alpha."""
        tooltip_w, tooltip_h, line_height, num_lines = self._compute_dimensions()

        # Extra canvas room for the shadow
        self._pad = self.SHADOW_LAYERS + 4
        surf_w = tooltip_w + self._pad * 2
        surf_h = tooltip_h + self._pad * 2
        surface = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)

        # ── Soft drop-shadow (layered rounded rects) ────────────────
        for i in range(self.SHADOW_LAYERS, 0, -1):
            alpha = int(45 * (1 - i / (self.SHADOW_LAYERS + 1)))
            expand = i
            s_w = tooltip_w + expand * 2
            s_h = tooltip_h + expand * 2
            s = pygame.Surface((s_w, s_h), pygame.SRCALPHA)
            r = self.CORNER_RADIUS + expand
            pygame.draw.rect(s, (*self.SHADOW_COLOR, alpha),
                             (0, 0, s_w, s_h), border_radius=r)
            surface.blit(s, (self._pad - expand, self._pad - expand))

        # ── Background ──────────────────────────────────────────────
        bg_rect = pygame.Rect(self._pad, self._pad, tooltip_w, tooltip_h)
        pygame.draw.rect(surface, self.BG_COLOR, bg_rect,
                         border_radius=self.CORNER_RADIUS)

        # ── Gold accent bar along the top ───────────────────────────
        bar_w = max(0, tooltip_w - self.CORNER_RADIUS * 2)
        accent_rect = pygame.Rect(
            self._pad + self.CORNER_RADIUS,
            self._pad,
            bar_w,
            self.ACCENT_HEIGHT,
        )
        pygame.draw.rect(surface, self.ACCENT_COLOR, accent_rect,
                         border_radius=1)

        # ── Border ──────────────────────────────────────────────────
        pygame.draw.rect(surface, self.BORDER_COLOR, bg_rect,
                         width=self.BORDER_WIDTH,
                         border_radius=self.CORNER_RADIUS)

        # ── Text rendering with hierarchy ───────────────────────────
        lines = self.text.split("\n")
        text_x = self._pad + self.padding
        text_y = self._pad + self.padding + self.ACCENT_HEIGHT + self.ACCENT_GAP

        for idx, line in enumerate(lines):
            # Pick colour based on line role
            if idx == 0:
                clr = self.TITLE_COLOR          # title
            elif idx == num_lines - 1 and num_lines > 1:
                clr = self.DESC_COLOR           # description
            else:
                clr = self.STAT_COLOR           # stat line

            txt_surf = self.font.render(line, True, clr)
            surface.blit(txt_surf, (text_x, text_y))
            text_y += line_height

            # Thin separator right after the title
            if idx == 0 and num_lines > 1:
                sep_y = text_y + 1
                pygame.draw.rect(
                    surface, self.SEPARATOR_COLOR,
                    (text_x, sep_y, tooltip_w - self.padding * 2, 1),
                )
                text_y += self.SEPARATOR_GAP + 1

        return surface

    # ── Public API (unchanged signatures) ───────────────────────────

    def hover_update(self, mouse_pos):
        now = time.time()

        is_over_target = self.target_rect.collidepoint(mouse_pos)
        is_over_tooltip = (self.active and self.rect
                           and self.rect.collidepoint(mouse_pos))

        if is_over_target or is_over_tooltip:
            if self.hover_start is None:
                self.hover_start = now

            if not self.active and (now - self.hover_start) > self.delay:
                tooltip_w, tooltip_h, _, _ = self._compute_dimensions()

                mouse_x, mouse_y = mouse_pos
                sw, sh = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT

                if mouse_x > sw // 2 and mouse_y > sh // 2:
                    n, m = -tooltip_w - 20, -tooltip_h - 20
                elif mouse_x < sw // 2 and mouse_y > sh // 2:
                    n, m = 20, -tooltip_h - 20
                elif mouse_x > sw // 2 and mouse_y < sh // 2:
                    n, m = -tooltip_w - 20, 20
                else:
                    n, m = 20, 20

                self.rect = pygame.Rect(
                    mouse_pos[0] + n,
                    mouse_pos[1] + m,
                    tooltip_w,
                    tooltip_h,
                )
                self.active = True
                self.show_time = now
                self._cached_surface = None
                logger.debug(
                    "Tooltip shown for target %s",
                    getattr(self.target_rect, "name", str(self.target_rect)),
                )
        else:
            self.hover_start = None
            self.active = False
            self.rect = None
            self.show_time = None
            self._cached_surface = None

    def update_target(self, new_rect, new_text):
        if self.target_rect != new_rect:
            self.target_rect = new_rect
            self.text = new_text
            self.hover_start = None
            self.active = False
            self.rect = None
            self.show_time = None
            self._cached_surface = None

    def draw(self, surface):
        if not self.active or not self.rect:
            return

        # Build (or re-use) the cached tooltip surface
        if self._cached_surface is None or self._cache_key != self.text:
            self._cached_surface = self._build_surface()
            self._cache_key = self.text

        # ── Entrance animation ──────────────────────────────────────
        alpha = 255
        slide_y = 0
        if self.show_time is not None:
            elapsed = time.time() - self.show_time
            if elapsed < self.ANIM_DURATION:
                t = elapsed / self.ANIM_DURATION   # 0 → 1
                # Ease-out cubic for a smooth deceleration
                t = 1.0 - (1.0 - t) ** 3
                alpha = int(255 * t)
                slide_y = int(self.SLIDE_OFFSET * (1.0 - t))

        blit_x = self.rect.x - self._pad
        blit_y = self.rect.y - self._pad + slide_y

        if alpha < 255:
            tmp = self._cached_surface.copy()
            tmp.set_alpha(alpha)
            surface.blit(tmp, (blit_x, blit_y))
        else:
            surface.blit(self._cached_surface, (blit_x, blit_y))

    def draw_multiline_text(self, surface, x, y):
        """Legacy helper – text rendering is now handled inside :meth:`draw`."""


class Dialog:
    """
    Simple modal dialog with text lines and an OK button.
    Supports optional Shop and Play Cards action buttons.
    """
    def __init__(self, app, lines, on_close=None, on_shop=None, show_shop=False,
                 on_play_cards=None, show_play_cards=False):
        self.app = app
        self.lines = lines if isinstance(lines, (list, tuple)) else [str(lines)]
        self.on_close = on_close
        self.on_shop = on_shop
        self.show_shop = bool(show_shop)
        self.on_play_cards = on_play_cards
        self.show_play_cards = bool(show_play_cards)
        sw, sh = self.app.screen.get_size()
        w = min(800, sw - 100)
        h = min(300, sh - 200)
        self.rect = pygame.Rect((sw - w) // 2, (sh - h) // 2, w, h)
        self.font = cfg.get_font(max(8,int(20 * cfg.ui_scale())))
        # Buttons: Close and optional Shop / Play Cards
        btn_w = max(100, int(160 * cfg.ui_scale()))
        btn_h = max(34, int(44 * cfg.ui_scale()))
        gap = int(12 * cfg.ui_scale())

        # Count how many action buttons we need
        action_buttons = []
        if self.show_shop:
            action_buttons.append(('shop', _('SHOP'), (100,110,70), (150,160,110)))
        if self.show_play_cards:
            action_buttons.append(('cards', _('PLAY CARDS'), (70,100,70), (110,150,110)))

        num_buttons = 1 + len(action_buttons)  # +1 for CLOSE
        total_w = btn_w * num_buttons + gap * (num_buttons - 1)
        btn_x = self.rect.x + (self.rect.width - total_w) // 2
        btn_y = self.rect.y + self.rect.height - btn_h - 16

        self.shop_button = None
        self.play_cards_button = None

        for kind, label, color, hover in action_buttons:
            if kind == 'shop':
                self.shop_button = Button(pygame.Rect(btn_x, btn_y, btn_w, btn_h), label, color, hover, self.font, (255,255,255), 6, on_click=self._shop)
            elif kind == 'cards':
                self.play_cards_button = Button(pygame.Rect(btn_x, btn_y, btn_w, btn_h), label, color, hover, self.font, (255,255,255), 6, on_click=self._play_cards_action)
            btn_x += btn_w + gap

        self.ok_button = Button(pygame.Rect(btn_x, btn_y, btn_w, btn_h), _('CLOSE'), (100,100,100), (150,150,150), self.font, (255,255,255), 6, on_click=self._close)

    def _close(self):
        if callable(self.on_close):
            try:
                self.on_close()
            except Exception:
                pass
        # clear current dialog in app
        try:
            self.app.current_dialog = None
        except Exception:
            pass

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.ok_button.rect.collidepoint(event.pos):
                if self.ok_button.on_click:
                    self.ok_button.on_click()
            if self.show_shop and self.shop_button and self.shop_button.rect.collidepoint(event.pos):
                if self.shop_button.on_click:
                    self.shop_button.on_click()
            if self.show_play_cards and self.play_cards_button and self.play_cards_button.rect.collidepoint(event.pos):
                if self.play_cards_button.on_click:
                    self.play_cards_button.on_click()
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                self._close()

    def _shop(self):
        if callable(self.on_shop):
            try:
                self.on_shop()
            except Exception:
                pass
        # close dialog after opening shop
        self._close()

    def _play_cards_action(self):
        if callable(self.on_play_cards):
            try:
                self.on_play_cards()
            except Exception:
                pass
        # close dialog after starting card game
        self._close()

    def draw(self, surface: pygame.Surface):
        # dim background
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0,0,0,120))
        surface.blit(overlay, (0,0))

        # dialog background
        pygame.draw.rect(surface, (40, 40, 40), self.rect, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=8)

        # draw lines
        line_h = self.font.get_height()
        total_h = line_h * len(self.lines)
        start_y = self.rect.y + 20
        for i, line in enumerate(self.lines):
            txt = self.font.render(line, True, (230, 230, 230))
            txt_x = self.rect.x + 20
            txt_y = start_y + i * line_h
            surface.blit(txt, (txt_x, txt_y))

        # draw buttons
        if self.show_shop and self.shop_button:
            try:
                self.shop_button.draw(surface)
            except Exception:
                pass
        if self.show_play_cards and self.play_cards_button:
            try:
                self.play_cards_button.draw(surface)
            except Exception:
                pass
        self.ok_button.draw(surface)

class Slider:
    """
    Horizontal slider UI component for controlling a value (e.g., audio volume).

    Attributes:
        x (int):
            X-coordinate of the slider track's starting position.
        y (int):
            Y-coordinate of the slider track's starting position.
        height (int):
            Thickness of the slider track in pixels.
        track_thickness (int):
            Thickness of the slider track line.
        track_colour (tuple[int, int, int]):
            RGB color of the slider track.
        knob_colour (tuple[int, int, int]):
            RGB color of the draggable knob.
        knob_width (int):
            Width of the slider knob in pixels.
        knob_height (int):
            Height of the slider knob in pixels.
        track_length (int):
            Length of the slider track in pixels.
        value (float):
            Current normalized value of the slider (0.0 to 1.0).
        dragging (bool):
            Whether the slider knob is currently being dragged.
        smooth_speed (float):
            Speed of value smoothing (if implemented).
        action (Callable[[float], None] | None):
            Optional callback function called with the new value when the slider is moved.
        knob_rect (pygame.Rect):
            Rectangle representing the position and size of the slider knob.

    Methods:
        draw(surface):
            Draw the slider track and knob onto the given Pygame surface.
            Args:
                surface (pygame.Surface): The surface to draw the slider on.
        handle_event(event):
            Process Pygame events to handle dragging of the slider knob.
            Args:
                event (pygame.event.Event): The Pygame event to process.
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
            if self.knob_rect.collidepoint(event.pos) or pygame.Rect(self.x, self.y, self.track_length, self.height).collidepoint(event.pos):
                self.dragging = True
                logger.debug("Slider drag started")
                mx, _ = event.pos
                rel_x = max(0, min(mx - self.x, self.track_length))
                self.value = round(rel_x / self.track_length, 2)
                if self.action:
                    self.action(self.value)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mx, _ = event.pos
            rel_x = max(0, min(mx - self.x, self.track_length))
            self.value = round(rel_x / self.track_length, 2)
            logger.debug(f"Slider value changed to {self.value}")
            if self.action:
                self.action(self.value)

class Inventory_slider(Slider):
    """
    Slider specialized for inventory UI, inherits from the generic Slider class.
    """
    def __init__(self, x, y, height, track_thickness, track_colour, knob_colour,
                 knob_width, knob_height, track_length, value=0.3, dragging=False, smooth_speed=0.05, action=None):
        super().__init__(x, y, height, track_thickness, track_colour, knob_colour,
                         knob_width, knob_height, track_length, value, dragging, smooth_speed, action)
