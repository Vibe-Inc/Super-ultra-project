import math
import random
import pygame
from gettext import gettext as _
from typing import TYPE_CHECKING

from src.ui.menus.base import Menu
from src.ui.widgets import Button
from src.entities.monster_visuals import build_monster_animations
import src.config as cfg

if TYPE_CHECKING:
    from src.app import App

GOLD = (212, 175, 55)
GOLD_BRIGHT = (255, 215, 0)
GOLD_DARK = (160, 120, 30)
PARCHMENT = (248, 236, 210)
PARCHMENT_DARK = (230, 210, 180)
PARCHMENT_LIGHT = (255, 248, 230)
INK = (45, 30, 15)
INK_LIGHT = (90, 65, 40)

SECTION_THEMES = {
    "main":     {"accent": GOLD,         "border": (180,140,60),  "glow": GOLD_BRIGHT,      "icon": "\u269A"},
    "bestiary": {"accent": (180,80,40),  "border": (120,50,20),  "glow": (220,120,60),     "icon": "\u2694"},
    "magic":    {"accent": (200,120,40), "border": (160,80,20),  "glow": (255,180,60),     "icon": "\u2726"},
    "effects":  {"accent": (120,60,140), "border": (80,30,100),  "glow": (180,100,220),    "icon": "\u2622"},
    "guide":    {"accent": (20,40,100),  "border": (30,20,80),   "glow": (80,120,220),     "icon": "\u270E"},
}

# ─── Caches ─────────────────────────────────────────────────
_cached_bg = {}
_shimmer_cache = {}
_WIKI_PORTRAIT_CACHE = {}


def _eased_out_cubic(t):
    return 1 - (1 - t) ** 3


def _wrap_text(text, font, max_width):
    lines = []
    for para in text.split('\n'):
        current = ''
        for word in para.split(' '):
            test = current + ' ' + word if current else word
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        lines.append('')
    if lines and lines[-1] == '':
        lines.pop()
    return lines


# ─── Cached Background ──────────────────────────────────────
def _draw_deep_bg(surf, sw, sh, t, theme):
    accent = theme.get("accent", GOLD)
    ak = (accent[0] // 8, accent[1] // 8, accent[2] // 8)
    ck = (sw, sh, ak)
    cached = _cached_bg.get(ck)
    if cached is None:
        cached = pygame.Surface((sw, sh), pygame.SRCALPHA)
        cached.fill((8, 6, 12, 248))
        cx, cy = sw // 2, sh // 2
        max_r = int(math.sqrt(cx * cx + cy * cy))
        step = max(40, int(40 * cfg.ui_scale()))
        for rs in range(max_r, 0, -step):
            ratio = rs / max_r
            a = max(0, min(40, int(35 * (1 - ratio * ratio))))
            gc = (ak[0], ak[1], ak[2], a)
            gs = pygame.Surface((rs * 2, rs * 2), pygame.SRCALPHA)
            pygame.draw.circle(gs, gc, (rs, rs), rs)
            cached.blit(gs, (cx - rs, cy - rs))
        _cached_bg[ck] = cached
    surf.blit(cached, (0, 0))
    # 2 animated light streaks
    cx, cy = sw // 2, sh // 2
    sz = max(80, int(100 * cfg.ui_scale()))
    for i in range(2):
        phase = t * 0.3 + i * 3.14159
        sx = int(cx + math.cos(phase) * sw * 0.25)
        sy = int(cy + math.sin(phase * 0.7) * sh * 0.25)
        a = max(0, min(30, int(8 + 5 * math.sin(t * 0.5 + i))))
        ss = pygame.Surface((sz, sz), pygame.SRCALPHA)
        pygame.draw.circle(ss, (ak[0] * 2, ak[1] * 2, ak[2] * 2, a), (sz // 2, sz // 2), sz // 2)
        surf.blit(ss, (sx - sz // 2, sy - sz // 2))


# ─── Simple gold divider (no surface per diamond) ───────────
def _draw_gold_divider(surf, x, y, width, scale, t=0.0):
    mid = y
    thin = max(1, int(1.5 * scale))
    thick = max(2, int(3 * scale))
    pygame.draw.line(surf, GOLD_DARK, (x, mid), (x + width, mid), thick)
    pygame.draw.line(surf, GOLD_BRIGHT, (x, mid - thin), (x + width, mid - thin), thin)
    for j, cx in enumerate((x + width // 4, x + width // 2, x + 3 * width // 4)):
        phase = t * 2.0 + j * 1.2
        ds = max(3, int(6 * scale * (0.8 + 0.2 * math.sin(phase))))
        pts = [(cx, mid - ds), (cx + ds, mid), (cx, mid + ds), (cx - ds, mid)]
        pygame.draw.polygon(surf, GOLD_BRIGHT, pts)


# ─── Corner scroll ──────────────────────────────────────────
def _draw_corner_scroll(surf, rect, scale, t=0.0):
    ofs = max(8, int(22 * scale))
    for cx, cy, dx, dy in [
        (rect.x + ofs, rect.y + ofs, 1, 1),
        (rect.right - ofs, rect.y + ofs, -1, 1),
        (rect.x + ofs, rect.bottom - ofs, 1, -1),
        (rect.right - ofs, rect.bottom - ofs, -1, -1),
    ]:
        pts = []
        for i in range(12):
            tt = i / 11
            angle = tt * math.pi * 0.5
            anim = 1.0 + 0.05 * math.sin(t * 1.5 + cx * 0.01)
            rx = max(4, int(32 * scale * anim)) * (1 - 0.3 * tt)
            ry = max(3, int(20 * scale * anim)) * (1 - 0.4 * tt)
            pts.append((cx + dx * rx * math.cos(angle), cy + dy * ry * math.sin(angle)))
        if len(pts) > 2:
            pygame.draw.lines(surf, GOLD, False, pts, max(1, int(2 * scale)))


# ─── Parchment + ornate border ──────────────────────────────
def _draw_ornate_border(surf, rect, theme, scale):
    r = pygame.Rect(rect)
    # Shadow
    shadow = r.inflate(12, 12)
    ss = pygame.Surface(shadow.size, pygame.SRCALPHA)
    ss.fill((0, 0, 0, 25))
    pygame.draw.rect(ss, (0, 0, 0, 0), ss.get_rect(), 0, border_radius=30)
    surf.blit(ss, shadow.topleft)
    # Parchment fill
    inner = r.inflate(-4, -4)
    pygame.draw.rect(surf, PARCHMENT_DARK, r, border_radius=28)
    pygame.draw.rect(surf, PARCHMENT_LIGHT, inner, border_radius=24)
    # Borders
    accent = theme["accent"]
    border = theme["border"]
    pygame.draw.rect(surf, border, r, max(2, int(4 * scale)), border_radius=28)
    pygame.draw.rect(surf, accent, r.inflate(-4, -4), max(1, int(2 * scale)), border_radius=24)
    # Corners — simple dots instead of complex shapes
    ofs = max(8, int(18 * scale))
    cr = max(3, int(5 * scale))
    for cx, cy in [(r.x + ofs, r.y + ofs), (r.right - ofs, r.y + ofs),
                   (r.x + ofs, r.bottom - ofs), (r.right - ofs, r.bottom - ofs)]:
        pygame.draw.circle(surf, accent, (int(cx), int(cy)), cr)
        pygame.draw.circle(surf, GOLD_BRIGHT, (int(cx), int(cy)), max(1, cr - 2))
    # Side ticks
    for y in range(r.y + int(40 * scale), r.bottom - int(40 * scale), int(60 * scale)):
        w = max(1, int(2 * scale))
        pygame.draw.line(surf, border, (r.x + int(10 * scale), y), (r.x + int(18 * scale), y), w)
        pygame.draw.line(surf, border, (r.right - int(18 * scale), y), (r.right - int(10 * scale), y), w)


# ─── Plain text (no shimmer) ────────────────────────────────
def _render_shimmer_text(font, text, base_color, t, intensity=0.15):
    return font.render(text, True, base_color)


# ─── Ambient Particle (simplified — single circle) ──────────
class AmbientParticle:
    """
    Simple floating ambient particle used for background atmosphere.

    Attributes:
        sw (int):
            Screen width boundary.
        sh (int):
            Screen height boundary.
        x (float):
            Current x position.
        y (float):
            Current y position.
        vx (float):
            Horizontal velocity.
        vy (float):
            Vertical velocity.
        sz (int):
            Particle radius in pixels.
        brightness (int):
            Brightness value for the particle color.
        alpha (int):
            Alpha transparency value.
        phase (float):
            Phase offset for oscillation.
        freq (float):
            Frequency of horizontal oscillation.
        _surf (pygame.Surface | None):
            Cached surface (may be None).

    Methods:
        __init__(sw, sh):
            Initialize the particle with random properties.
        _reset(init=False):
            Reset particle position and properties.
        update(dt, t):
            Update particle position and check bounds.
        draw(surf, t):
            Draw the particle with oscillating alpha.
    """

    def __init__(self, sw, sh):
        self.sw, self.sh = sw, sh
        self._reset(True)

    def _reset(self, init=False):
        self.x = random.uniform(0, self.sw)
        self.y = random.uniform(0, self.sh) if init else random.uniform(self.sh, self.sh + 60)
        self.vx = random.uniform(-10, 10)
        self.vy = random.uniform(-20, -6)
        self.sz = random.randint(1, 3)
        self.brightness = random.randint(80, 180)
        self.alpha = random.randint(40, 100)
        self.phase = random.uniform(0, 6.28)
        self.freq = random.uniform(0.6, 2.0)
        self._surf = None  # cached surface

    def update(self, dt, t):
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y < -10 or self.x < -10 or self.x > self.sw + 10:
            self._reset()

    def draw(self, surf, t):
        a = int(self.alpha * (0.5 + 0.5 * math.sin(t * 1.2 + self.phase)))
        a = max(0, min(255, a))
        px = int(self.x + math.sin(t * self.freq + self.phase) * 3)
        py = int(self.y)
        sz = self.sz
        # Draw directly with minimal surface
        s = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (self.brightness, int(self.brightness * 0.9), int(self.brightness * 0.6), a), (sz, sz), sz)
        surf.blit(s, (px - sz, py - sz))


# ─── Burst Particle ─────────────────────────────────────────
class WikiParticle:
    """
    Burst particle for wiki menu visual effects, supporting glow and star shapes.

    Attributes:
        x (float):
            Current x position.
        y (float):
            Current y position.
        vx (float):
            Horizontal velocity.
        vy (float):
            Vertical velocity (gravity applied each frame).
        lt (float):
            Remaining lifetime in seconds.
        max_lt (float):
            Maximum lifetime for alpha scaling.
        color (tuple):
            RGB(A) color of the particle.
        size (int):
            Base size of the particle.
        glow (bool):
            Whether this particle has a glow effect.
        star (bool):
            Whether this particle is drawn as a star shape.

    Methods:
        __init__(x, y, vx, vy, lt, color, size, glow=False, star=False):
            Initialize the burst particle.
        update(dt):
            Update position and lifetime.
        draw(surf):
            Draw the particle with fading alpha.
    """

    def __init__(self, x, y, vx, vy, lt, color, size, glow=False, star=False):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.lt = self.max_lt = lt
        self.color, self.size = color, size
        self.glow, self.star = glow, star

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lt -= dt
        self.vy += 60 * dt

    def draw(self, surf):
        if self.lt <= 0:
            return
        a = max(0, min(255, int(255 * self.lt / self.max_lt)))
        px, py = int(self.x), int(self.y)
        sz = max(1, int(self.size * (0.6 + 0.4 * self.lt / self.max_lt)))
        c = (*self.color[:3], a)
        if self.star:
            s = pygame.Surface((sz * 4, sz * 4), pygame.SRCALPHA)
            h = sz * 2
            pts = []
            for i in range(8):
                r2 = sz * 2 if i % 2 == 0 else sz
                ang = math.radians(i * 45 - 90)
                pts.append((h + r2 * math.cos(ang), h + r2 * math.sin(ang)))
            pygame.draw.polygon(s, c, pts)
            surf.blit(s, (px - h, py - h))
            return
        # Simple circle
        s = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, c, (sz, sz), sz)
        surf.blit(s, (px - sz, py - sz))


# ─── Portrait ───────────────────────────────────────────────
def _get_monster_portrait(visual_style, size=140):
    key = (visual_style, size)
    if key in _WIKI_PORTRAIT_CACHE:
        return _WIKI_PORTRAIT_CACHE[key]
    anims = build_monster_animations(visual_style, (size, size))
    frame = anims["down"][0].copy()
    total = size + 24
    s = pygame.Surface((total, total), pygame.SRCALPHA)
    for r in range(8, 0, -1):
        a = 20 // r
        pygame.draw.circle(s, (GOLD[0], GOLD[1], GOLD[2], a), (total // 2, total // 2), size // 2 + r, 2)
    s.blit(frame, ((total - size) // 2, (total - size) // 2))
    _WIKI_PORTRAIT_CACHE[key] = s
    return s


def _draw_portrait_frame(surf, x, y, size, theme, scale, pulse):
    fsz = size + 12
    fs = pygame.Surface((fsz, fsz), pygame.SRCALPHA)
    c = theme["accent"]
    pygame.draw.rect(fs, GOLD, fs.get_rect(), max(2, int(3 * scale)), border_radius=12)
    pygame.draw.rect(fs, GOLD_BRIGHT, fs.get_rect().inflate(-4, -4), max(1, int(1 * scale)), border_radius=10)
    for cx, cy in [(4, 4), (fsz - 4, 4), (4, fsz - 4), (fsz - 4, fsz - 4)]:
        pygame.draw.circle(fs, GOLD_BRIGHT, (cx, cy), max(2, int(3 * scale)))
    surf.blit(fs, (x - 6, y - 6))


SECTIONS_META = {
    "bestiary": {"subtitle": _("Foes of the Realm"), "icon": "\u2694", "entries": [
        _("The Brute"), _("The Venomous"), _("The Arcanist"), _("The Trickster"), _("The Bomber"),
        _("The Stalker"), _("The Skirmisher"), _("The Guardian")]},
    "magic": {"subtitle": _("Spells of Power"), "icon": "\u2726", "entries": [
        _("Fireball"), _("Flame Shield"), _("Frost Nova"), _("Ice Armor"),
        _("Glacial Cascade"), _("Chain Lightning"), _("Thunderstrike"),
        _("Entangling Roots"), _("Summon Spirit"), _("Shadow Step"),
        _("Dark Pact"), _("Arcane Missiles"), _("Mystic Barrier"),
        _("Berserker's Rage"), _("Chrono Shift"), _("Dash")]},
    "effects": {"subtitle": _("Curse & Blessing"), "icon": "\u2622", "entries": [
        _("Boon: Regeneration"), _("Bane: Poison"), _("Bane: Burn"),
        _("Bane: Confusion"), _("Bane: Dizziness"), _("Bane: Slow"),
        _("Bane: Freeze & Root")]},
    "guide": {"subtitle": _("Adventurer's Handbook"), "icon": "\u270E", "entries": [
        _("1. Movement & Navigation"), _("2. Combat Basics"),
        _("3. Skills & Hotbar"), _("4. Inventory & Items"),
        _("5. Crafting & Recipes"), _("6. Leveling & Experience"),
        _("7. Day & Night Cycle"), _("8. Enemies & Threat Assessment"),
        _("9. Respeccing & Strategy"), _("10. Final Words")]},
}


class WikiMenu(Menu):
    """
    In-game wiki / compendium (Codex Arcanum) with bestiary, magic, effects, and guide sections.

    Features ornate parchment-styled backgrounds, section cards, table of contents,
    content pages with monster portraits, and transition animations.

    Attributes:
        app (App):
            The main application instance.
        _page (str):
            Current page identifier ('main', 'bestiary', 'magic', 'effects', 'guide').
        _sub_page (int):
            Current sub-page index within a section.
        _show_toc (bool):
            Whether the table of contents is currently displayed.
        font_ornate (pygame.font.Font):
            Large ornate font for icons.
        font_large (pygame.font.Font):
            Large font for the main title.
        font_title (pygame.font.Font):
            Title font for section headers.
        font_subtitle (pygame.font.Font):
            Subtitle font for section cards.
        font_body (pygame.font.Font):
            Body text font for content pages.
        font_small (pygame.font.Font):
            Small font for captions and page numbers.
        font_toc (pygame.font.Font):
            Font for table of contents entries.
        ink_color (tuple):
            Primary ink color for text.
        ink_light (tuple):
            Lighter ink color for subtler text.
        particles (list[WikiParticle]):
            Active burst particles.
        ambient_particles (list[AmbientParticle]):
            Active ambient background particles.
        _anim_time (float):
            Accumulated animation time.
        _page_enter_time (int):
            Timestamp of the last page entry (ms).
        _transition_progress (float):
            Normalized page transition progress (0.0 to 1.0).
        _transition_from (str):
            Page being transitioned from.
        _hover_glow (dict):
            Hover glow progress per section card index.
        buttons (list[Button]):
            List of control buttons.
        back_btn (Button):
            Back button.
        prev_btn (Button):
            Previous page button.
        next_btn (Button):
            Next page button.
        toc_btn (Button):
            Table of contents toggle button.
        section_buttons (list):
            Main page section card buttons.
        section_button_data (list[tuple]):
            Data for main page section cards.
        _toc_hover (int):
            Index of the hovered TOC entry.
        _toc_entry_rects (list[tuple[pygame.Rect, int]]):
            List of (rect, page_index) for TOC hit detection.

    Methods:
        __init__(app):
            Initialize the wiki menu.
        on_enter():
            Reset animations and spawn ambient particles on entry.
        _build_main_page():
            Build the main page with section cards.
        _open_bestiary():
            Open the bestiary section.
        _open_magic():
            Open the magic section.
        _open_effects():
            Open the effects section.
        _open_guide():
            Open the guide section.
        _emit_particles(theme):
            Spawn burst particles with the given theme colors.
        _go_back():
            Navigate back through sub-pages or to the main page.
        _toggle_toc():
            Toggle the table of contents display.
        _prev_page():
            Go to the previous sub-page.
        _next_page():
            Go to the next sub-page.
        _get_max_subpages():
            Get the maximum sub-page index for the current section.
        _theme():
            Get the current section's color theme.
        _get_content():
            Get the content pages for the current section.
        _get_meta():
            Get the metadata for the current section.
        _bestiary_pages():
            Build bestiary content pages.
        _magic_pages():
            Build magic content pages.
        _effects_pages():
            Build effects content pages.
        _guide_pages():
            Build guide content pages.
        layout(screen):
            Position buttons based on screen size and current page.
        update(dt):
            Update animations and particles.
        draw(screen):
            Render the wiki menu.
        _draw_main(screen, sw, sh, scale):
            Draw the main page with section cards.
        _draw_toc(screen, sw, sh, scale):
            Draw the table of contents.
        _draw_content(screen, sw, sh, scale):
            Draw a content page with title, body, and optional portrait.
        handle_event(event):
            Handle input events.
        _handle_main_click(event):
            Handle clicks on the main page section cards.
        _handle_toc_click(event):
            Handle clicks on table of contents entries.
    """

    def __init__(self, app: "App"):
        super().__init__(app)
        self._page = "main"
        self._sub_page = 0
        self._show_toc = False
        self.font_ornate = cfg.get_font(64)
        self.font_large = cfg.get_font(52)
        self.font_title = cfg.get_font(38)
        self.font_subtitle = cfg.get_font(30)
        self.font_body = cfg.get_font(24)
        self.font_small = cfg.get_font(18)
        self.font_toc = cfg.get_font(26)
        self.ink_color = INK
        self.ink_light = INK_LIGHT
        self.particles = []
        self.ambient_particles = []
        self._anim_time = 0.0
        self._page_enter_time = 0
        self._transition_progress = 1.0
        self._transition_from = "main"
        self._hover_glow = {}
        scale = cfg.ui_scale()
        bw = max(1, int(220 * scale))
        bh = max(1, int(62 * scale))
        self.buttons = []
        self.back_btn = Button(pygame.Rect(0, 0, bw, bh), _("BACK"),
            cfg.button_color_SETTINGS_BACK, cfg.button_hover_color_SETTINGS_BACK,
            cfg.button_font, cfg.text_color, cfg.corner_radius, on_click=self._go_back)
        self.prev_btn = Button(pygame.Rect(0, 0, bw, bh), _("<< PREV"),
            cfg.button_color_SETTINGS, cfg.button_hover_color_SETTINGS,
            cfg.button_font, cfg.text_color, cfg.corner_radius, on_click=self._prev_page)
        self.next_btn = Button(pygame.Rect(0, 0, bw, bh), _("NEXT >>"),
            cfg.button_color_SETTINGS, cfg.button_hover_color_SETTINGS,
            cfg.button_font, cfg.text_color, cfg.corner_radius, on_click=self._next_page)
        self.toc_btn = Button(pygame.Rect(0, 0, bw, bh), _("CONTENTS"),
            (100, 80, 60), (140, 120, 90),
            cfg.button_font, cfg.text_color, cfg.corner_radius, on_click=self._toggle_toc)
        self.section_buttons = []
        self._build_main_page()
        self._toc_hover = -1

    def on_enter(self):
        self._anim_time = 0.0
        self._page_enter_time = pygame.time.get_ticks()
        self._transition_progress = 0.0
        sw, sh = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT
        if not self.ambient_particles:
            for _ in range(20):
                self.ambient_particles.append(AmbientParticle(sw, sh))

    def _build_main_page(self):
        self._transition_from = self._page
        self._page = "main"
        self._sub_page = 0
        self._show_toc = False
        self._transition_progress = 0.0
        self._page_enter_time = pygame.time.get_ticks()
        self.section_buttons.clear()
        self.section_button_data = [
            (_("Bestiary"), _("Foes of the Realm"), self._open_bestiary, SECTION_THEMES["bestiary"]),
            (_("Magic"), _("Spells of Power"), self._open_magic, SECTION_THEMES["magic"]),
            (_("Alterations"), _("Curse & Blessing"), self._open_effects, SECTION_THEMES["effects"]),
            (_("Guide"), _("Adventurer's Handbook"), self._open_guide, SECTION_THEMES["guide"]),
        ]

    def _open_bestiary(self):
        self._transition_from = self._page; self._page = "bestiary"; self._sub_page = 0
        self._show_toc = True; self._page_enter_time = pygame.time.get_ticks()
        self._transition_progress = 0.0; self._emit_particles(SECTION_THEMES["bestiary"])

    def _open_magic(self):
        self._transition_from = self._page; self._page = "magic"; self._sub_page = 0
        self._show_toc = True; self._page_enter_time = pygame.time.get_ticks()
        self._transition_progress = 0.0; self._emit_particles(SECTION_THEMES["magic"])

    def _open_effects(self):
        self._transition_from = self._page; self._page = "effects"; self._sub_page = 0
        self._show_toc = True; self._page_enter_time = pygame.time.get_ticks()
        self._transition_progress = 0.0; self._emit_particles(SECTION_THEMES["effects"])

    def _open_guide(self):
        self._transition_from = self._page; self._page = "guide"; self._sub_page = 0
        self._show_toc = True; self._page_enter_time = pygame.time.get_ticks()
        self._transition_progress = 0.0; self._emit_particles(SECTION_THEMES["guide"])

    def _emit_particles(self, theme):
        sw, sh = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT
        for _ in range(40):
            self.particles.append(WikiParticle(
                random.randint(0, sw), random.randint(0, sh),
                random.uniform(-120, 120), random.uniform(-280, -40),
                random.uniform(0.6, 1.8), theme["accent"], random.randint(2, 5),
                glow=random.random() < 0.3, star=random.random() < 0.15))

    def _go_back(self):
        if self._show_toc and self._sub_page > 0:
            self._show_toc = False; self._sub_page = 0
            self._transition_progress = 0.0; return
        if self._page != "main":
            self._build_main_page()
        else:
            self.app.manager.set_state("pause")

    def _toggle_toc(self):
        self._show_toc = not self._show_toc
        if self._show_toc: self._sub_page = 0
        self._page_enter_time = pygame.time.get_ticks(); self._transition_progress = 0.0

    def _prev_page(self):
        if self._sub_page > 0:
            self._sub_page -= 1; self._show_toc = False
            self._page_enter_time = pygame.time.get_ticks(); self._transition_progress = 0.0

    def _next_page(self):
        mp = self._get_max_subpages()
        if self._sub_page < mp:
            self._sub_page += 1; self._show_toc = False
            self._page_enter_time = pygame.time.get_ticks(); self._transition_progress = 0.0

    def _get_max_subpages(self):
        return max(0, len(self._get_content()) - 1)

    def _theme(self):
        return SECTION_THEMES.get(self._page, SECTION_THEMES["main"])

    def _get_content(self):
        fn = {"bestiary": self._bestiary_pages, "magic": self._magic_pages,
              "effects": self._effects_pages, "guide": self._guide_pages}.get(self._page)
        return fn() if fn else []

    def _get_meta(self):
        return SECTIONS_META.get(self._page, {})

    def _bestiary_pages(self):
        return [
            {"title": _("The Brute"), "portrait": "brute", "body": _(
                "They say the first Brute was born from a boulder struck by lightning\u2014a creature of fury and stone. "
                "These hulking warriors patrol the old roads with a single purpose: to crush anything that moves.\n\n"
                "A Brute does not rush. It stalks. It waits. And when the moment is right, it charges with the force of an avalanche.\n\n"
                "Abilities: Charge (2.4\u00d7 speed, 220 range), Slam (1.5\u00d7 damage, knockback, slow 1.5s). Health: 160. Speed: 110.")},
            {"title": _("The Venomous"), "portrait": "venomous", "body": _(
                "In the swamplands where even the trees have learned to bite, the Venomous make their dens.\n\n"
                "A single scratch sends poison surging through your veins\u2014a creeping decay that grows stronger the longer you ignore it.\n\n"
                "Abilities: Poison Strike (4s, 5 DPS). Health: 95. Speed: 130.")},
            {"title": _("The Arcanist"), "portrait": "arcanist", "body": _(
                "Magic is a gift, they say. But some gifts come with a price. The Arcanists are former students who delved too deep.\n\n"
                "These robed figures hurl bolts of searing flame, their aim uncanny and their patience endless.\n\n"
                "Abilities: Arcane Bolt (480 speed, 560 range, burn 3.2s). Health: 80. Speed: 115.")},
            {"title": _("The Trickster"), "portrait": "trickster", "body": _(
                "Beware the laughter in the dark. The Tricksters delight in confusion and disarray.\n\n"
                "Their touch clouds the mind\u2014suddenly left is right, forward is back.\n\n"
                "Abilities: Blink (240 range), Confuse (2.8s), Dizzy (2.2s). Health: 75. Speed: 150.")},
            {"title": _("The Bomber"), "portrait": "bomber", "body": _(
                "A hiss of steam, a flicker of arc-light\u2014the Bomber lumbers in on riveted peg legs.\n\n"
                "Brass-plated and pressure-sealed, these wandering automatons keep their distance while lobbing timed bombs that arc through the air with deceptive grace.\n\n"
                "Abilities: Timed Bomb (95 blast radius, 80 knockback, 0.9s fuse). Health: 125. Speed: 105.")},
            {"title": _("The Stalker"), "portrait": "stalker", "body": _(
                "Where shadow pools deep and torchlight fails, the Stalker waits\u2014patient, silent, and unseen.\n\n"
                "Cloaked and masked, these grim assassins favor the blade over brute strength. They remember your last position long after you've broken line of sight, and they are quick to re-pick a fresh path when cut off.\n\n"
                "Abilities: Blade Strike (40 range), Memory Trail (3s pursuit after losing sight), Repath (0.5s). Health: 110. Speed: 120.")},
            {"title": _("The Skirmisher"), "portrait": "skirmisher", "body": _(
                "Swift as the raptor it resembles, the Skirmisher darts across the battlefield with javelin raised and crest fluttering.\n\n"
                "These winged hunters prefer to keep their distance\u2014harrying from the fringes, circling, striking, and vanishing before the counter-blow can land. Tribal warpaint marks the kills they've claimed.\n\n"
                "Abilities: Javelin Toss (35 range), Orbit (preferred 80\u2013170, radius 130). Health: 85. Speed: 140.")},
            {"title": _("The Guardian"), "portrait": "guardian", "body": _(
                "Forged in the fires of a forgotten forge, the Guardian is a hulking iron sentinel bound to a place of power.\n\n"
                "Steam hisses from brass-banded joints and copper pistons pump with every ponderous step. It will not stray far from its post\u2014but woe to any intruder that crosses the threshold it defends.\n\n"
                "Abilities: Heavy Slam (45 range, knockback), Guard Post (radius 320, leash 90), Patrol Wait (0.8s). Health: 140. Speed: 100.")},
        ]

    def _magic_pages(self):
        return [
            {"title": _("Fireball"), "body": _(
                "The quintessence of destructive magic. A roaring sphere that erupts in glorious conflagration.\n\n"
                "Damage: 28 base (area). Range: 520. Knockback: moderate. Pyromancer's Fury: +25% damage.")},
            {"title": _("Flame Shield"), "body": _(
                "A wreath of protective flames that scorches any foe foolish enough to approach.\n\n"
                "Damage: 8/sec to nearby enemies. Duration: 6 seconds.")},
            {"title": _("Frost Nova"), "body": _(
                "A razored ring of ice expanding outward, freezing any enemy caught within.\n\n"
                "Radius: 150. Freeze: 3 seconds.")},
            {"title": _("Ice Armor"), "body": _(
                "A cloak of crystalline frost that absorbs incoming blows.\n\n"
                "Absorbs up to 30 damage. Duration: 8s. Attackers within 80px slowed by half.")},
            {"title": _("Glacial Cascade"), "body": _(
                "A torrent of ice shards racing forward, dealing 35 damage.\n\n"
                "Freeze: 2 seconds. Travels far and wide.")},
            {"title": _("Chain Lightning"), "body": _(
                "Leaps from the caster to the nearest foe, then arcs to the next.\n\n"
                "Damage: 22/strike. Range: 550. Chain: 180. Up to 5 enemies.")},
            {"title": _("Thunderstrike"), "body": _(
                "A column of lightning from the heavens, dealing catastrophic damage.\n\n"
                "Damage: 55. Radius: 100. Range: 600.")},
            {"title": _("Entangling Roots"), "body": _(
                "Ancient tendrils erupt from the soil, grasping the target.\n\n"
                "Root: 4 seconds. Radius: 140. Range: 500.")},
            {"title": _("Summon Spirit"), "body": _(
                "A nature spirit fights at your side\u2014a flickering wisp of leaves and light.\n\n"
                "Spirit Damage: 15. Duration: 10 seconds.")},
            {"title": _("Shadow Step"), "body": _(
                "Dissolve into darkness and reappear a short distance away.\n\n"
                "Range: 300. Invulnerability: 0.5s after arrival.")},
            {"title": _("Dark Pact"), "body": _(
                "Rips life force from the caster and detonates it in shadow energy.\n\n"
                "Cost: 10% max HP. Damage: 60 shadow. Radius: 150.")},
            {"title": _("Arcane Missiles"), "body": _(
                "5 homing projectiles that each deal 14 damage.\n\n"
                "They seek, they find, they destroy.")},
            {"title": _("Mystic Barrier"), "body": _(
                "A shimmering ward that turns 30% of incoming damage back.\n\n"
                "Duration: 5s.")},
            {"title": _("Berserker's Rage"), "body": _(
                "Raw fury: +50% damage dealt, +20% damage taken.\n\n"
                "Duration: 8s. Cooldown: 20s.")},
            {"title": _("Chrono Shift"), "body": _(
                "Slows the world around you.\n\n"
                "Duration: 3s. Enemies at half speed, you strike 25% faster. Cooldown: 30s.")},
            {"title": _("Dash"), "body": _(
                "Propels the user forward in a burst of speed.\n\n"
                "Distance is safety. Speed is life.")},
        ]

    def _effects_pages(self):
        return [
            {"title": _("Boon: Regeneration"), "body": _(
                "Accelerated healing\u2014restoring health with every heartbeat.\n\n"
                "A steady flow of vitality.")},
            {"title": _("Bane: Poison"), "body": _(
                "Creeping death that seeps into the bloodstream.\n\n"
                "Deals damage over time. Antidotes are worth their weight in gold.")},
            {"title": _("Bane: Burn"), "body": _(
                "Fire remembers. The Burn effect lingers long after the initial blast.\n\n"
                "Immediate and aggressive damage.")},
            {"title": _("Bane: Confusion"), "body": _(
                "Inverts direction\u2014up becomes down, left becomes right.\n\n"
                "Duration: ~3s. Trust nothing.")},
            {"title": _("Bane: Dizziness"), "body": _(
                "The world spins. Colors smear. Combat becomes a nauseating ordeal.\n\n"
                "Often paired with Confusion.")},
            {"title": _("Bane: Slow"), "body": _(
                "A creeping weight settles into the limbs.\n\n"
                "Speed is life. To be slowed is to be marked for death.")},
            {"title": _("Bane: Freeze & Root"), "body": _(
                "Two faces of the same cursed coin. Both leave you unable to act.\n\n"
                "A frozen or rooted fighter is a dead fighter.")},
        ]

    def _guide_pages(self):
        return [
            {"title": _("1. Movement & Navigation"), "body": _(
                "Move with WASD. Sprint with Shift\u2014watch your stamina bar.\n\n"
                "Walk into doors and map edges to transition between areas.")},
            {"title": _("2. Combat Basics"), "body": _(
                "Left-click to attack. Health (red) at top and stamina (blue) above hotbar.\n\n"
                "When health reaches zero, you respawn at your last save point.")},
            {"title": _("3. Skills & Hotbar"), "body": _(
                "Press 1-6 for skills. Open Skill Tree from inventory.\n\n"
                "Each skill has a cooldown.")},
            {"title": _("4. Inventory & Items"), "body": _(
                "Press E. Manage equipment, consume potions, inspect gear.\n\n"
                "Point cursor for details. Drag to rearrange.")},
            {"title": _("5. Crafting & Recipes"), "body": _(
                "Combine ingredients in the 3\u00d73 crafting grid.\n\n"
                "The Recipe Book shows known recipes. Experiment to discover more.")},
            {"title": _("6. Leveling & Experience"), "body": _(
                "Defeat enemies for XP. Level up = +20 max HP + Skill Tree point.\n\n"
                "Branches: Fire, Ice, Lightning, Nature, Shadow, Arcane.")},
            {"title": _("7. Day & Night Cycle"), "body": _(
                "The world follows day and night. Some enemies are more aggressive at night.\n\n"
                "Plan your expeditions accordingly.")},
            {"title": _("8. Enemies & Threat Assessment"), "body": _(
                "Brutes: dodge charge. Venomous: bring antidotes. Arcanists: close distance.\n\n"
                "Tricksters: predict. Bombers: stay mobile.")},
            {"title": _("9. Respeccing & Strategy"), "body": _(
                "Your build matters. Focus or spread for versatility.\n\n"
                "Adapt. Improvise. Overcome.")},
            {"title": _("10. Final Words"), "body": _(
                "The road ahead is long and lined with peril. You will fall. You will rise.\n\n"
                "Their mistakes are your lessons. Their triumphs are your inheritance.\n\n"
                "Now go. The realm awaits.")},
        ]

    # ─── Layout ─────────────────────────────────────────────
    def layout(self, screen):
        sw, sh = self._screen_size(screen)
        scale = cfg.ui_scale()
        bw = max(1, int(220 * scale))
        bh = max(1, int(62 * scale))
        if self._page == "main":
            self.back_btn.rect = pygame.Rect(sw - bw - max(20, int(40 * scale)),
                                             sh - bh - max(20, int(28 * scale)), bw, bh)
        else:
            ny = sh - bh - max(16, int(24 * scale))
            by2 = ny - bh - max(4, int(8 * scale))
            mx = max(20, int(30 * scale))
            self.back_btn.rect = pygame.Rect(mx, by2, bw, bh)
            self.toc_btn.rect = pygame.Rect(mx + bw + max(8, int(10 * scale)), by2, bw, bh)
            self.prev_btn.rect = pygame.Rect(mx, ny, bw, bh)
            self.next_btn.rect = pygame.Rect(sw - bw - mx, ny, bw, bh)
        for b in (self.back_btn, self.prev_btn, self.next_btn, self.toc_btn):
            try: b._update_text_surface()
            except: pass

    def update(self, dt):
        self._anim_time += dt
        if self._transition_progress < 1.0:
            self._transition_progress = min(1.0, self._transition_progress + dt * 3.0)
        self.particles = [p for p in self.particles if p.lt > 0]
        for p in self.particles: p.update(dt)
        for ap in self.ambient_particles: ap.update(dt, self._anim_time)

    def draw(self, screen):
        self.layout(screen)
        sw, sh = self._screen_size(screen)
        scale = cfg.ui_scale()
        self.update(1 / 60)

        # Ambient particles on separate surface
        amb = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for ap in self.ambient_particles: ap.draw(amb, self._anim_time)
        screen.blit(amb, (0, 0))

        if self._page == "main":
            self._draw_main(screen, sw, sh, scale)
        elif self._show_toc:
            self._draw_toc(screen, sw, sh, scale)
        else:
            self._draw_content(screen, sw, sh, scale)

        for p in self.particles: p.draw(screen)

        if self._transition_progress < 1.0:
            a = max(0, min(255, int(255 * (1.0 - _eased_out_cubic(self._transition_progress)))))
            ov = pygame.Surface((sw, sh), pygame.SRCALPHA); ov.fill((0, 0, 0, a))
            screen.blit(ov, (0, 0))

    # ─── Main Page ──────────────────────────────────────────
    def _draw_main(self, screen, sw, sh, scale):
        t = self._anim_time
        theme = SECTION_THEMES["main"]
        _draw_deep_bg(screen, sw, sh, t, theme)

        pad = max(20, int(45 * scale))
        box = pygame.Rect(pad, pad, sw - 2 * pad, sh - 2 * pad)
        _draw_ornate_border(screen, box, theme, scale)
        _draw_corner_scroll(screen, box, scale, t)
        inner = box.inflate(-int(60 * scale), -int(60 * scale))

        # Floating icon
        ip = 0.8 + 0.2 * math.sin(t * 1.2)
        ifl = math.sin(t * 0.8) * 4 * scale
        is2 = self.font_ornate.render("\u2726", True, GOLD_BRIGHT)
        is2 = pygame.transform.scale(is2, (int(is2.get_width() * ip), int(is2.get_height() * ip)))
        gs = pygame.Surface((is2.get_width() + 30, is2.get_height() + 30), pygame.SRCALPHA)
        ga = int(40 + 30 * math.sin(t * 1.8))
        pygame.draw.circle(gs, (*GOLD, max(0, min(80, ga))), (gs.get_width() // 2, gs.get_height() // 2), gs.get_width() // 2)
        ix = inner.x + (inner.width - gs.get_width()) // 2
        iy = inner.y + int(5 * scale) + int(ifl)
        screen.blit(gs, (ix, iy - 15))
        screen.blit(is2, (ix + 15, iy))

        # Title
        ty = inner.y + int(60 * scale) + int(ifl)
        ts = _render_shimmer_text(self.font_large, _("The Adventurer's Codex"), INK, t, 0.08)
        tx = inner.x + (inner.width - ts.get_width()) // 2
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            g = self.font_large.render(_("The Adventurer's Codex"), True, INK_LIGHT)
            g.set_alpha(25)
            screen.blit(g, (tx + ox, ty + oy))
        screen.blit(ts, (tx, ty))

        # Divider
        dy = ty + ts.get_height() + int(14 * scale)
        _draw_gold_divider(screen, inner.x + int(40 * scale), dy, inner.width - int(80 * scale), scale, t)

        # Subtitle
        sy = dy + int(28 * scale)
        ss = self.font_subtitle.render(_("An in-game compendium of knowledge"), True, self.ink_light)
        ss.set_alpha(int(180 + 75 * math.sin(t * 0.9)))
        screen.blit(ss, (inner.x + (inner.width - ss.get_width()) // 2, sy))

        # Section cards
        bsy = sy + ss.get_height() + int(35 * scale)
        bh = max(1, int(92 * scale))
        bw = max(1, int(420 * scale))
        gap = max(6, int(18 * scale))
        cx = sw // 2
        mp = pygame.mouse.get_pos()

        for i, (label, sublabel, cb, th) in enumerate(self.section_button_data):
            by = bsy + i * (bh + gap)
            bx = cx - bw // 2
            br = pygame.Rect(bx, by, bw, bh)
            hov = br.collidepoint(mp)
            ht = self._hover_glow.get(i, 0.0)
            ht = min(1.0, ht + 0.08) if hov else max(0.0, ht - 0.05)
            self._hover_glow[i] = ht
            e = _eased_out_cubic(ht)

            # Card background
            c = th["accent"]
            bs2 = pygame.Surface(br.size, pygame.SRCALPHA)
            gi = int(30 * e)
            bs2.fill((min(255, c[0] // 5 + 25 + gi), min(255, c[1] // 5 + 18 + gi),
                       min(255, c[2] // 5 + 25 + gi), int(180 + 70 * e)))
            pygame.draw.rect(bs2, c, bs2.get_rect(), max(1, int((2 + e) * scale)), border_radius=int(16 * scale))
            pygame.draw.rect(bs2, GOLD_DARK, bs2.get_rect().inflate(-5, -5), max(1, int(scale)), border_radius=int(12 * scale))

            # Glow on hover
            if ht > 0.01:
                gs2 = pygame.Surface((br.w + int(16 * e), br.h + int(16 * e)), pygame.SRCALPHA)
                pygame.draw.rect(gs2, (*th["glow"], max(0, min(70, int(60 * e)))),
                                 gs2.get_rect(), border_radius=int(20 * scale))
                screen.blit(gs2, (br.x - int(8 * e), br.y - int(8 * e)))

            screen.blit(bs2, br.topleft)

            # Icon
            iyo = math.sin(t * 1.5 + i * 0.8) * 3 * scale * (0.3 + 0.7 * e)
            ic = self.font_subtitle.render(th.get("icon", ""), True, GOLD_BRIGHT)
            screen.blit(ic, (bx + int(18 * scale), int(by + 10 * scale + iyo)))

            # Label
            lc = GOLD_BRIGHT if ht > 0.05 else GOLD
            screen.blit(self.font_subtitle.render(label, True, lc), (bx + int(58 * scale), by + int(10 * scale)))
            sbl = self.font_small.render(sublabel, True,
                tuple(min(255, int(c * (0.6 + 0.4 * e))) for c in self.ink_light))
            screen.blit(sbl, (bx + int(58 * scale), by + int(52 * scale)))

            # Arrow
            if ht > 0.1:
                ar = self.font_subtitle.render("\u2192", True, GOLD_BRIGHT)
                ar.set_alpha(int(255 * e))
                screen.blit(ar, (br.right - int(40 * scale) - int(8 * e), by + (br.height - ar.get_height()) // 2))

        # Footer
        vs = self.font_small.render(_("Codex Arcanum \u2014 First Edition"), True, self.ink_light)
        vs.set_alpha(int(140 + 50 * math.sin(t * 0.7)))
        screen.blit(vs, ((sw - vs.get_width()) // 2, sh - int(42 * scale)))
        self.back_btn.draw(screen)

    # ─── TOC Page ───────────────────────────────────────────
    def _draw_toc(self, screen, sw, sh, scale):
        theme = self._theme()
        meta = self._get_meta()
        entries = meta.get("entries", [])
        t = self._anim_time

        _draw_deep_bg(screen, sw, sh, t, theme)
        pad = max(8, int(24 * scale))
        box = pygame.Rect(pad, pad, sw - 2 * pad, sh - 2 * pad)
        _draw_ornate_border(screen, box, theme, scale)
        _draw_corner_scroll(screen, box, scale, t)
        inner = box.inflate(-int(60 * scale), -int(100 * scale))

        icon = theme.get("icon", "")
        title_full = f"{icon}  {meta.get('subtitle', '')}"
        ts = _render_shimmer_text(self.font_title, title_full, INK, t, 0.1)
        tx = inner.x + (inner.width - ts.get_width()) // 2
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            g = self.font_title.render(title_full, True, INK_LIGHT)
            g.set_alpha(30)
            screen.blit(g, (tx + ox, inner.y + oy))
        screen.blit(ts, (tx, inner.y))

        _draw_gold_divider(screen, inner.x + int(30 * scale),
                           inner.y + ts.get_height() + int(8 * scale),
                           inner.width - int(60 * scale), scale, t)

        toc_top = inner.y + ts.get_height() + int(28 * scale)
        entry_h = max(1, int(48 * scale))
        gap = max(3, int(8 * scale))
        mv = (inner.height - ts.get_height() - int(28 * scale)) // (entry_h + gap)
        self._toc_entry_rects = []

        for i, et in enumerate(entries[:mv]):
            ed = i * 0.06
            et2 = max(0, min(1.0, (t - ed) * 4.0)) if self._transition_progress < 1.0 else 1.0
            sl = int((1.0 - _eased_out_cubic(et2)) * 40 * scale)
            ey = toc_top + i * (entry_h + gap) + sl
            er = pygame.Rect(inner.x + int(10 * scale), ey, inner.width - int(20 * scale), entry_h)
            hov = i == self._toc_hover
            locked = not self.app.article_tracker.already_seen(self._page, et)

            ns = pygame.Surface(er.size, pygame.SRCALPHA)
            bc = theme["accent"]
            if locked:
                ns.fill((bc[0] // 8 + 10, bc[1] // 8 + 8, bc[2] // 8 + 10, 80) if hov else
                        (bc[0] // 10 + 5, bc[1] // 10 + 4, bc[2] // 10 + 5, 40))
            else:
                ns.fill((bc[0] // 3 + 50, bc[1] // 3 + 40, bc[2] // 3 + 50, 140) if hov else
                        (bc[0] // 6 + 20, bc[1] // 6 + 15, bc[2] // 6 + 20, 60))

            if hov and not locked:
                gs2 = pygame.Surface((er.w + 12, er.h + 12), pygame.SRCALPHA)
                pygame.draw.rect(gs2, (*theme["glow"], max(0, min(60, int(50 + 20 * math.sin(t * 3))))),
                                 gs2.get_rect(), border_radius=12)
                screen.blit(gs2, (er.x - 6, er.y - 6))

            pygame.draw.rect(ns, GOLD if hov and not locked else GOLD_DARK, ns.get_rect(), 1, border_radius=10)
            screen.blit(ns, er.topleft)

            ns2 = self.font_small.render(f"{i+1}.", True, GOLD_BRIGHT if not locked else GOLD_DARK)
            screen.blit(ns2, (er.x + 12, er.y + (er.height - ns2.get_height()) // 2))

            tc = GOLD_BRIGHT if hov else self.ink_color
            if locked:
                tc = tuple(c // 2 + 30 for c in self.ink_color)
            es = self.font_toc.render(et, True, tc)
            screen.blit(es, (er.x + 48, er.y + (er.height - es.get_height()) // 2))

            if locked:
                lock_surf = self.font_small.render("\U0001F512", True, (100, 80, 60))
                screen.blit(lock_surf, (er.right - lock_surf.get_width() - 14,
                                        er.y + (er.height - lock_surf.get_height()) // 2))
            elif hov:
                ar = self.font_small.render("\u2192", True, GOLD_BRIGHT)
                screen.blit(ar, (er.right - ar.get_width() - 14,
                                 er.y + (er.height - ar.get_height()) // 2 + int(math.sin(t * 4) * 3)))

            self._toc_entry_rects.append((er, i + 1))

        hs = self.font_small.render(_("Select an entry to read"), True, self.ink_light)
        hs.set_alpha(int(140 + 60 * math.sin(t * 0.8)))
        screen.blit(hs, (inner.x + (inner.width - hs.get_width()) // 2,
                         inner.y + inner.height - hs.get_height() - 10))
        self.back_btn.draw(screen)

    # ─── Content Page ───────────────────────────────────────
    def _draw_content(self, screen, sw, sh, scale):
        theme = self._theme()
        pages = self._get_content()
        if not pages:
            return
        pd = pages[min(self._sub_page, len(pages) - 1)]
        title = pd.get("title", "")
        body = pd.get("body", "")
        ps = pd.get("portrait", None)
        t = self._anim_time

        locked = not self.app.article_tracker.already_seen(self._page, title)
        if locked:
            body = "???\n\nThis knowledge has not yet been unlocked.\nBrave the wilds and earn this entry."
            ps = None

        _draw_deep_bg(screen, sw, sh, t, theme)
        pad = max(8, int(20 * scale))
        box = pygame.Rect(pad, pad, sw - 2 * pad, sh - 2 * pad)
        _draw_ornate_border(screen, box, theme, scale)
        _draw_corner_scroll(screen, box, scale, t)
        inner = box.inflate(-int(50 * scale), -int(80 * scale))

        # Portrait — positioned in lower-right area
        pimg = None; px = py = ps2 = 0
        if ps:
            ps2 = max(1, int(140 * scale))
            pimg = _get_monster_portrait(ps, ps2)
            px = inner.right - ps2 - int(20 * scale)
            py = inner.y + int(inner.height * 0.65)

        # Title
        taw = inner.width - (ps2 + int(24 * scale) if pimg else 0)
        tt = max(0, min(1.0, t * 5.0))
        tsl = int((1.0 - _eased_out_cubic(tt)) * 30 * scale)
        title_color = tuple(c // 2 + 40 for c in INK) if locked else INK
        ts = _render_shimmer_text(self.font_title, title, title_color, t, 0.1)
        tx = inner.x + (taw - ts.get_width()) // 2

        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            g = self.font_title.render(title, True, INK_LIGHT)
            g.set_alpha(30)
            screen.blit(g, (tx + ox, inner.y + tsl + oy))
        screen.blit(ts, (tx, inner.y + tsl))

        # Divider
        dy = inner.y + ts.get_height() + int(8 * scale) + tsl
        dw = taw + (ps2 + int(24 * scale) if pimg else 0)
        _draw_gold_divider(screen, inner.x + int(10 * scale), dy, dw - int(20 * scale), scale, t)

        # Body text
        tt2 = dy + int(18 * scale)
        taw2 = inner.width - (ps2 + int(24 * scale) if pimg else 0)
        tah = inner.y + inner.height - tt2
        bf = self.font_body
        lh = bf.get_height() + max(2, int(3 * scale))
        bl = _wrap_text(body, bf, taw2)
        vl = max(0, (tah - int(40 * scale)) // lh)

        for i in range(vl):
            if i >= len(bl): break
            line = bl[i]
            if not line.strip(): continue
            ld = i * 0.02
            lt2 = max(0, min(1.0, (t - 0.1 - ld) * 4.0))
            la = int(255 * _eased_out_cubic(lt2))

            if i == 0 and line.strip():
                fc = line[0]; rest = line[1:]
                cs = int(bf.get_height() * 1.8)
                try: cf = cfg.get_font(cs)
                except: cf = bf
                cap = cf.render(fc, True, theme["accent"])
                cap.set_alpha(la)
                screen.blit(cap, (inner.x + int(10 * scale), tt2))
                if rest:
                    rs = bf.render(rest, True, self.ink_color)
                    rs.set_alpha(la)
                    screen.blit(rs, (inner.x + int(10 * scale) + cap.get_width() + 2,
                                     tt2 + int((cs - bf.get_height()) * 0.6)))
            else:
                sf = bf.render(line, True, self.ink_color)
                sf.set_alpha(la)
                screen.blit(sf, (inner.x + int(10 * scale), tt2 + i * lh))

        # Portrait
        if pimg:
            pulse = 0.7 + 0.3 * math.sin(t * 2)
            _draw_portrait_frame(screen, px, py, ps2, theme, scale, pulse)
            fy = int(math.sin(t * 0.9) * 3 * scale)
            screen.blit(pimg, (px + 6, py + 6 + fy))
            ns = self.font_small.render(title, True, theme["accent"])
            nx = px + (ps2 + 12 - ns.get_width()) // 2
            for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                g = self.font_small.render(title, True, theme["glow"])
                g.set_alpha(max(0, min(45, int(50 + 20 * math.sin(t * 1.6)))))
                screen.blit(g, (nx + ox, py + ps2 + int(14 * scale) + fy + oy))
            screen.blit(ns, (nx, py + ps2 + int(14 * scale) + fy))

        # Page number
        mp = self._get_max_subpages()
        if mp > 0:
            pt = f"\u276E  {_('Page {}/{}').format(self._sub_page + 1, mp + 1)}  \u276F"
            ps3 = self.font_small.render(pt, True, GOLD_DARK)
            ppx = (sw - ps3.get_width()) // 2
            pbg = pygame.Surface((ps3.get_width() + 20, ps3.get_height() + 8), pygame.SRCALPHA)
            pygame.draw.rect(pbg, (*PARCHMENT_DARK, 120), pbg.get_rect(), border_radius=10)
            pygame.draw.rect(pbg, (*GOLD_DARK, 100), pbg.get_rect(), 1, border_radius=10)
            screen.blit(pbg, (ppx - 10, sh - int(50 * scale)))
            screen.blit(ps3, (ppx, sh - int(48 * scale)))

        self.back_btn.draw(screen)
        self.toc_btn.draw(screen)
        if mp > 0:
            if self._sub_page > 0: self.prev_btn.draw(screen)
            if self._sub_page < mp: self.next_btn.draw(screen)

    # ─── Events ─────────────────────────────────────────────
    def handle_event(self, event):
        if self._page == "main" and hasattr(self, 'section_button_data'):
            self._handle_main_click(event)
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_btn.rect.collidepoint(event.pos):
                self.back_btn.on_click(); return
            if self._page != "main":
                if self.toc_btn.rect.collidepoint(event.pos):
                    self.toc_btn.on_click(); return
                if self._show_toc:
                    self._handle_toc_click(event); return
                if self.prev_btn.rect.collidepoint(event.pos):
                    self.prev_btn.on_click(); return
                if self.next_btn.rect.collidepoint(event.pos):
                    self.next_btn.on_click(); return
        if event.type == pygame.MOUSEMOTION and self._show_toc:
            self._toc_hover = -1
            if hasattr(self, '_toc_entry_rects'):
                for er, idx in self._toc_entry_rects:
                    if er.collidepoint(event.pos):
                        self._toc_hover = idx - 1; break
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self._show_toc and self._sub_page > 0:
                    self._show_toc = False
                elif self._page != "main":
                    self._build_main_page()
                else:
                    self.app.manager.set_state("pause")
                return
            if event.key in (pygame.K_LEFT, pygame.K_PAGEUP):
                self._prev_page(); return
            if event.key in (pygame.K_RIGHT, pygame.K_PAGEDOWN):
                self._next_page(); return
            if event.key in (pygame.K_t, pygame.K_TAB):
                self._toggle_toc(); return

    def _handle_main_click(self, event):
        scale = cfg.ui_scale()
        sw, sh = self._screen_size()
        bh = max(1, int(92 * scale))
        bw = max(1, int(420 * scale))
        gap = max(6, int(18 * scale))
        cx = sw // 2
        pad = max(20, int(45 * scale))
        box = pygame.Rect(pad, pad, sw - 2 * pad, sh - 2 * pad)
        inner = box.inflate(-int(60 * scale), -int(60 * scale))
        ifl = math.sin(self._anim_time * 0.8) * 4 * scale
        ty = inner.y + int(60 * scale) + ifl
        ts = self.font_large.render(_("The Adventurer's Codex"), True, GOLD_BRIGHT)
        dy = ty + ts.get_height() + int(14 * scale)
        sy = dy + int(28 * scale)
        ss = self.font_subtitle.render(_("An in-game compendium of knowledge"), True, self.ink_light)
        bsy = sy + ss.get_height() + int(35 * scale)
        for i, (label, sublabel, cb, th) in enumerate(self.section_button_data):
            by = bsy + i * (bh + gap)
            bx = cx - bw // 2
            br = pygame.Rect(bx, by, bw, bh)
            if event.type == pygame.MOUSEBUTTONDOWN and br.collidepoint(event.pos):
                cb(); return
        if event.type == pygame.MOUSEBUTTONDOWN and self.back_btn.rect.collidepoint(event.pos):
            self.back_btn.on_click()

    def _handle_toc_click(self, event):
        if not hasattr(self, '_toc_entry_rects'): return
        for er, pi in self._toc_entry_rects:
            if er.collidepoint(event.pos):
                self._sub_page = pi; self._show_toc = False
                self._page_enter_time = pygame.time.get_ticks()
                self._transition_progress = 0.0; return