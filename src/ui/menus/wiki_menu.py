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
    "smeltery": {"accent": (180,70,30),  "border": (120,40,10),  "glow": (255,140,60),     "icon": "\u2699"},
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
    "smeltery": {"subtitle": _("Master's Forge"), "icon": "\u2699", "entries": [
        _("1. The Smeltery Unveiled"), _("2. Workbench & Shaping"),
        _("3. Coke Oven & Fuel"), _("4. Blast Furnace & Alloys"),
        _("5. Anvil & Restoration"), _("6. Smelting Skill & Mastery"),
        _("7. Minigames & Refinement"), _("8. Forgemaster's Secrets")]},
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
        self._skip_to_gameplay = False
        self.begin_btn = Button(pygame.Rect(0, 0, bw, bh), _(">> BEGIN ADVENTURE"),
            (100, 75, 25), (160, 120, 40),
            cfg.button_font, cfg.text_color, cfg.corner_radius, on_click=self._begin_adventure)

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
            (_("Smeltery"), _("Master's Forge"), self._open_smeltery, SECTION_THEMES["smeltery"]),
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

    def _open_smeltery(self):
        self._transition_from = self._page; self._page = "smeltery"; self._sub_page = 0
        self._show_toc = True; self._page_enter_time = pygame.time.get_ticks()
        self._transition_progress = 0.0; self._emit_particles(SECTION_THEMES["smeltery"])

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

    def _begin_adventure(self):
        self._skip_to_gameplay = False
        self.app.manager.set_state("gameplay")

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
              "effects": self._effects_pages, "guide": self._guide_pages,
              "smeltery": self._smeltery_pages}.get(self._page)
        return fn() if fn else []

    def _get_meta(self):
        return SECTIONS_META.get(self._page, {})

    def _bestiary_pages(self):
        return [
            {"title": _("The Brute"), "portrait": "brute", "body": _(
                "They say the first Brute was born from a boulder struck by lightning\u2014a creature "
                "of fury and stone. These hulking warriors patrol the old roads with a single purpose: "
                "to crush anything that moves.\n\n"
                "A Brute does not rush. It stalks. It waits. And when the moment is right, it charges "
                "with the force of an avalanche. Its Slam attack deals heavy damage with knockback and "
                "leaves you slowed, unable to dodge the next blow.\n\n"
                "Abilities: Charge (2.4\u00d7 speed, 220 range), Slam (1.5\u00d7 damage, knockback, "
                "slow 1.5s). Health: 160. Speed: 110.\n\n"
                "Tactics: Dodge sideways when it charges\u2014never backward. After a missed charge, "
                "the Brute is vulnerable. Strike hard and retreat before the Slam lands.")},
            {"title": _("The Venomous"), "portrait": "venomous", "body": _(
                "In the swamplands where even the trees have learned to bite, the Venomous make "
                "their dens. These serpentine hunters rely on venom to weaken their prey before "
                "closing in for the kill.\n\n"
                "A single scratch sends poison surging through your veins\u2014a creeping decay "
                "that grows stronger the longer you ignore it. The poison stacks, and a prolonged "
                "encounter with multiple Venomous foes can overwhelm even the hardiest adventurer.\n\n"
                "Abilities: Poison Strike (4s, 5 DPS per stack). Health: 95. Speed: 130.\n\n"
                "Tactics: Antidotes are non-negotiable. Use ranged attacks to avoid contact poison. "
                "If poisoned, retreat and cure before re-engaging.")},
            {"title": _("The Arcanist"), "portrait": "arcanist", "body": _(
                "Magic is a gift, they say. But some gifts come with a price. The Arcanists are "
                "former students who delved too deep and emerged with minds scorched by forbidden "
                "knowledge.\n\n"
                "These robed figures hurl bolts of searing flame with uncanny aim and endless "
                "patience. They prefer to keep their distance, kiting relentlessly while their "
                "Arcane Bolt burns through your defenses.\n\n"
                "Abilities: Arcane Bolt (480 speed, 560 range, burn 3.2s). Health: 80. "
                "Speed: 115.\n\n"
                "Tactics: Close the distance quickly\u2014Arcanists are fragile once engaged in "
                "melee. Use Shadow Step or Dash to close the gap, then interrupt their casting.")},
            {"title": _("The Trickster"), "portrait": "trickster", "body": _(
                "Beware the laughter in the dark. The Tricksters delight in confusion and disarray, "
                "weaving shadows into cruel pranks that leave their victims lost and helpless.\n\n"
                "Their touch clouds the mind\u2014suddenly left is right, forward is back. They "
                "blink in and out of visibility, making them maddeningly difficult to pin down.\n\n"
                "Abilities: Blink (240 range), Confuse (2.8s), Dizzy (2.2s). Health: 75. "
                "Speed: 150.\n\n"
                "Tactics: Predict their Blink destination and strike preemptively. If Confused, "
                "consciously invert your inputs. Their low health makes them quick to eliminate.")},
            {"title": _("The Bomber"), "portrait": "bomber", "body": _(
                "A hiss of steam, a flicker of arc-light\u2014the Bomber lumbers in on riveted peg "
                "legs. Brass-plated and pressure-sealed, these wandering automatons keep their "
                "distance while lobbing timed bombs that arc through the air with deceptive grace.\n\n"
                "The bombs have a 0.9-second fuse, giving you just enough time to react\u2014if you "
                "are paying attention. The blast radius is punishing, and the knockback can send you "
                "into the path of other enemies.\n\n"
                "Abilities: Timed Bomb (95 blast radius, 80 knockback, 0.9s fuse). Health: 125. "
                "Speed: 105.\n\n"
                "Tactics: Stay mobile. Never stand still\u2014Bombers lead their targets. Close the "
                "distance aggressively; Bombers are vulnerable in close quarters.")},
            {"title": _("The Stalker"), "portrait": "stalker", "body": _(
                "Where shadow pools deep and torchlight fails, the Stalker waits\u2014patient, "
                "silent, and unseen. Cloaked and masked, these grim assassins favor the blade "
                "over brute strength.\n\n"
                "They remember your last position long after you have broken line of sight, "
                "pursuing with relentless precision. When cut off from their target, they are "
                "quick to re-pick a fresh path, making them nearly impossible to shake.\n\n"
                "Abilities: Blade Strike (40 range), Memory Trail (3s pursuit after losing sight), "
                "Repath (0.5s). Health: 110. Speed: 120.\n\n"
                "Tactics: Breaking line of sight is not enough\u2014keep moving for a full 3 "
                "seconds after losing them. Use tight corners and doors to break the Memory Trail.")},
            {"title": _("The Skirmisher"), "portrait": "skirmisher", "body": _(
                "Swift as the raptor it resembles, the Skirmisher darts across the battlefield "
                "with javelin raised and crest fluttering. These winged hunters prefer to keep "
                "their distance\u2014harrying from the fringes, circling, striking, and vanishing "
                "before the counter-blow can land.\n\n"
                "Tribal warpaint marks the kills they have claimed, and their javelins find their "
                "mark with unsettling accuracy. They orbit their prey at a preferred range, always "
                "just out of reach.\n\n"
                "Abilities: Javelin Toss (35 range), Orbit (preferred 80\u2013170, radius 130). "
                "Health: 85. Speed: 140.\n\n"
                "Tactics: Close in to force them into melee, but watch for the Javelin Toss as "
                "you approach. Ranged users should lead their shots\u2014their orbit pattern is "
                "predictable.")},
            {"title": _("The Guardian"), "portrait": "guardian", "body": _(
                "Forged in the fires of a forgotten forge, the Guardian is a hulking iron sentinel "
                "bound to a place of power. Steam hisses from brass-banded joints and copper pistons "
                "pump with every ponderous step.\n\n"
                "It will not stray far from its post\u2014its leash is short and its duty absolute. "
                "But woe to any intruder that crosses the threshold it defends. The Guardian's Heavy "
                "Slam sends adventurers flying, and it pursues with relentless, mechanical patience.\n\n"
                "Abilities: Heavy Slam (45 range, knockback), Guard Post (radius 320, leash 90), "
                "Patrol Wait (0.8s). Health: 140. Speed: 100.\n\n"
                "Tactics: If possible, avoid engaging Guardians on their home turf. If you must "
                "fight, bait the Heavy Slam and strike during the recovery.")},
            {"title": _("The Phantom"), "portrait": "phantom", "body": _(
                "Some wounds never heal. Some souls never leave. The Phantoms are the remnants of mages who tried to cheat death.\n\n"
                "Bound to the world by spectral chains, they drift through walls and memory alike, draining life force with a touch that feels like a winter breeze\u2014cold, brief, and leaving you weaker.\n\n"
                "Abilities: Life Drain (280 speed, heal 35% of damage), Slow (1.5s, 0.65x). Health: 100. Speed: 105.")},
            {"title": _("The Titan"), "portrait": "titan", "body": _(
                "The mountains remember the Titans\u2014ancient stone colossi carved by a forgotten race to guard the old roads.\n\n"
                "Moss and time have worn their features smooth, but the runes etched into their hide still pulse with amber light. When a Titan stomps, the ground itself trembles, and roots erupt to hold you in place.\n\n"
                "Abilities: Stomp (50 range, knockback 45, root 2.5s), Charge (2\u00d7 speed, 320 cooldown). Health: 220. Speed: 75.")},
            {"title": _("The Cryomancer"), "portrait": "cryomancer", "body": _(
                "In the northern ruins where snow falls even in summer, the Cryomancers hold court.\n\n"
                "These ice-weavers were once scholars of a frost school that has long since crumbled. Now they guard their frozen libraries with jagged shards of crystallized mana. Up close, they unleash a biting nova that freezes blood in the veins.\n\n"
                "Abilities: Ice Shard (420 speed, 500 range, slow 2.5s), Frost Nova (80 radius, freeze 2s). Health: 85. Speed: 110.")},
            {"title": _("The Shadowmancer"), "portrait": "shadowmancer", "body": _(
                "The Shadowmancers speak in whispers to things that dwell between the stars. Their bodies are merely vessels for the void they serve.\n\n"
                "They flicker and vanish when threatened, reappearing at a safe distance before loosing bolts of concentrated shadow that infest the mind with confusion. To face one is to question your own senses.\n\n"
                "Abilities: Shadow Bolt (450 speed, 480 range, confuse 3s), Void Escape (260 range teleport). Health: 75. Speed: 125.")},
            {"title": _("The Revenant"), "portrait": "revenant", "body": _(
                "A revenant is what happens when a warrior\u2019s rage outlives their flesh. These undying soldiers remember only the fight.\n\n"
                "Every strike heals them, siphoning life from the wound they just opened. And should you manage to bring one low, its undying will ignites\u2014a surge of pale green soul-fire that restores it to fighting form.\n\n"
                "Abilities: Lifesteal Slash (30% heal, bleed 3s), Undying Will (35% heal, 2.5s immunity, 15s cooldown). Health: 130. Speed: 110.")},
            {"title": _("The Molten"), "portrait": "molten", "body": _(
                "Deep within the earth, where pressure cooks stone into magma, the Molten were born.\n\n"
                "These hulking fire elementals are living forges. Lava pulses through cracks in their rocky hides, and they burn everything they touch. When angered, they release a searing nova or charge with the unstoppable force of a landslide.\n\n"
                "Abilities: Fire Nova (100 radius, burn 3.5s, 6 DPS), Lava Charge (2.5\u00d7 speed, 350 cooldown). Health: 150. Speed: 100.")},
            {"title": _("The Stormcaller"), "portrait": "stormcaller", "body": _(
                "High atop jagged peaks that pierce the clouds, the Stormcallers conduct their eternal symphony of lightning.\n\n"
                "These robed tempests hurl crackling bolts that dance with wild energy. If you close the distance, they release a static field that scrambles the senses, leaving you disoriented and vulnerable.\n\n"
                "Abilities: Chain Lightning (500 speed, 520 range, dizzy 1.8s), Static Field (90 radius, 3s cooldown). Health: 80. Speed: 115.")},
            {"title": _("The Plaguebearer"), "portrait": "plaguebearer", "body": _(
                "The Plaguebearers were once healers\u2014until they tried to cure a disease that had no cure. Now they are its carriers.\n\n"
                "Robes caked with filth and malice, these wretched casters lob clouds of pestilence that poison the air. At close range they erupt in a pestilent nova that saps strength and leaves a creeping sickness in its wake.\n\n"
                "Abilities: Plague Cloud (380 speed, 460 range, poison 4s, 5.5 DPS), Pestilence Nova (100 radius, slow 2s). Health: 110. Speed: 105.")},
        ]

    def _magic_pages(self):
        return [
            {"title": _("Fireball"), "body": _(
                "The quintessence of destructive magic. A roaring sphere of condensed flame that "
                "erupts in glorious conflagration upon impact.\n\n"
                "Summon a fireball that travels toward your target and explodes on contact, "
                "scorching everything in its blast radius. No other spell announces your presence "
                "with such authority.\n\n"
                "Damage: 28 base (area). Range: 520. Knockback: moderate. Pyromancer's Fury: "
                "+25% damage. Use it to break enemy formations or punish clustered foes.")},
            {"title": _("Flame Shield"), "body": _(
                "A wreath of protective flames that scorches any foe foolish enough to approach.\n\n"
                "Wreathe yourself in roaring fire for 6 seconds. Enemies within melee range take "
                "continuous burn damage, making this ideal for brawling against groups or deterring "
                "aggressive pursuers. The flames do not discriminate\u2014stand too close to allies "
                "and they too will feel the heat.\n\n"
                "Damage: 8/sec to nearby enemies. Duration: 6 seconds. Combines well with Ice "
                "Armor for a fire-and-ice defensive shell.")},
            {"title": _("Frost Nova"), "body": _(
                "A razored ring of ice that erupts from your body and expands outward, "
                "flash-freezing everything it touches.\n\n"
                "In an instant, a circle of crystalline frost explodes from the caster, freezing "
                "enemies solid for 3 seconds. Frozen enemies cannot move or act, making them easy "
                "targets for follow-up attacks. The freeze breaks early if the target takes "
                "significant damage, so time your burst carefully.\n\n"
                "Radius: 150. Freeze: 3 seconds. Excellent setup for Fireball\u2014freeze "
                "first, then detonate.")},
            {"title": _("Ice Armor"), "body": _(
                "A cloak of crystalline frost that wraps around you, absorbing incoming blows and "
                "punishing those who strike you.\n\n"
                "For 8 seconds, Ice Armor absorbs up to 30 damage before shattering. While active, "
                "any melee attacker within 80 pixels is slowed by half, giving you precious space "
                "to reposition or counterattack. The absorption applies before your health pool\u2014"
                "every point of damage blocked is a point you do not feel.\n\n"
                "Absorbs up to 30 damage. Duration: 8s. Attackers within 80px slowed by half. "
                "A must-have for melee-range mages.")},
            {"title": _("Glacial Cascade"), "body": _(
                "A torrent of razor-sharp ice shards that races forward in a widening cone, "
                "shredding everything in its path.\n\n"
                "Launch a cascade of glacial fragments that travels in a broad arc, dealing 35 "
                "damage to all enemies caught in its path. The piercing cold freezes targets for "
                "2 seconds\u2014shorter than Frost Nova but applied at range. The cascade travels "
                "far and wide, making it exceptional for corridor fighting and thinning approaching "
                "hordes.\n\n"
                "Damage: 35. Freeze: 2 seconds. Wide arc, long range. Ideal for controlling "
                "chokepoints.")},
            {"title": _("Chain Lightning"), "body": _(
                "A crackling bolt of lightning that leaps from the caster to the nearest foe, "
                "then arcs to the next, and the next.\n\n"
                "Chain Lightning seeks out enemies with unerring accuracy. The initial strike "
                "hits your closest target within 550 range, then arcs up to 180 units to the "
                "next, chaining across up to 5 enemies. Each strike deals 22 damage\u2014less "
                "than a Fireball, but the total damage across a full chain is devastating.\n\n"
                "Damage: 22/strike. Range: 550. Chain radius: 180. Max chains: 5. Excels against "
                "tightly packed groups.")},
            {"title": _("Thunderstrike"), "body": _(
                "A column of pure lightning that crashes down from the heavens, dealing "
                "catastrophic single-target damage.\n\n"
                "Call upon the sky itself to smite a target within 600 range. The strike lands "
                "with a 100-radius blast, dealing 55 damage\u2014the hardest-hitting single-instance "
                "spell in the arcane arsenal. Use it to eliminate high-priority targets before "
                "they close to melee range.\n\n"
                "Damage: 55. Radius: 100. Range: 600. Best reserved for elite enemies and bosses.")},
            {"title": _("Entangling Roots"), "body": _(
                "Ancient tendrils erupt from the soil beneath your target, grasping and holding "
                "them in place.\n\n"
                "Call upon the deep earth to bind your enemies. Roots erupt in a 140-radius area "
                "at a target location up to 500 units away, holding all caught enemies for 4 "
                "seconds. Rooted enemies cannot move but can still attack and use abilities. The "
                "roots are vulnerable to fire\u2014a clever foe can burn their way free.\n\n"
                "Root duration: 4 seconds. Radius: 140. Range: 500. Combines with Fireball or "
                "Glacial Cascade for devastating area combos.")},
            {"title": _("Summon Spirit"), "body": _(
                "A nature spirit fights at your side\u2014a flickering wisp of leaves and ancient "
                "light that harries your enemies.\n\n"
                "Summon a loyal nature spirit from the woodland realm. The spirit lasts 10 seconds, "
                "automatically attacking nearby foes for 15 damage per strike. It cannot be targeted "
                "or killed, making it a reliable source of supplementary damage. The spirit follows "
                "you and prioritizes enemies you are currently fighting.\n\n"
                "Spirit Damage: 15 per strike. Duration: 10 seconds. Invaluable for split focus\u2014"
                "let the spirit harass while you prepare a heavy spell.")},
            {"title": _("Shadow Step"), "body": _(
                "Dissolve into shadow and reform a short distance away, leaving your enemies "
                "grasping at nothing.\n\n"
                "Shadow Step is your ultimate mobility tool. Vanish into darkness at your current "
                "location and reappear up to 300 units away in the direction of your choosing. "
                "For 0.5 seconds after arrival, you are completely invulnerable\u2014long enough "
                "to absorb a killing blow or dodge a telegraphed attack.\n\n"
                "Range: 300. Invulnerability: 0.5s after arrival. Use to escape deadly situations "
                "or reposition for a counterattack.")},
            {"title": _("Dark Pact"), "body": _(
                "A forbidden pact that rips life force from the caster and detonates it in a "
                "burst of shadow energy.\n\n"
                "Sacrifice 10% of your maximum health to unleash a blast of shadow damage\u2014"
                "60 damage to all enemies within a 150-radius area. The health cost is paid "
                "instantly and cannot be mitigated. Dark Pact deals the highest area burst damage "
                "of any spell, but the price is steep. Use it when the risk is worth the reward.\n\n"
                "Cost: 10% max HP. Damage: 60 shadow. Radius: 150. Always carry health potions "
                "when this spell is in your arsenal.")},
            {"title": _("Arcane Missiles"), "body": _(
                "Five homing projectiles of pure arcane energy that seek out your enemies with "
                "unerring accuracy.\n\n"
                "Launch a volley of 5 arcane missiles that each deal 14 damage. The missiles "
                "automatically track the nearest enemy within range, curving through the air to "
                "find their mark. They can strike multiple targets or focus fire on a single foe. "
                "Against a lone enemy, the full volley delivers 70 damage.\n\n"
                "Projectiles: 5. Damage: 14 each (70 total if all hit). Homing: yes. They seek, "
                "they find, they destroy.")},
            {"title": _("Mystic Barrier"), "body": _(
                "A shimmering ward of pure arcane energy that surrounds you, reflecting a portion "
                "of incoming damage back at your attackers.\n\n"
                "For 5 seconds, Mystic Barrier reduces all damage you take and reflects 30% of it "
                "back to the source. The reflected damage scales with the incoming hit\u2014the "
                "harder they strike, the more they feel. This does not prevent the damage to you, "
                "so it is a gamble: you survive the hit, and they feel the sting.\n\n"
                "Duration: 5s. Reflection: 30% of incoming. Use against hard-hitting enemies to "
                "turn their strength against them.")},
            {"title": _("Berserker's Rage"), "body": _(
                "Raw, untamed fury surges through your veins\u2014your attacks hit harder, but "
                "your defenses crack.\n\n"
                "Enter a berserker trance for 8 seconds. All damage you deal is increased by 50%, "
                "but all damage you take is increased by 20%. This is the glass cannon's signature\u2014"
                "devastating power at a perilous cost. Activate it when you know you can end the "
                "fight before the enemy ends you.\n\n"
                "Duration: 8s. Cooldown: 20s. Damage dealt: +50%. Damage taken: +20%. Pair with "
                "defensive abilities to offset the vulnerability.")},
            {"title": _("Chrono Shift"), "body": _(
                "Bend the flow of time itself, slowing the world around you to a crawl while you "
                "move with supernatural swiftness.\n\n"
                "For 3 seconds, Chrono Shift reduces enemy movement speed by half while increasing "
                "your attack speed by 25%. The effect is immediate and disorienting\u2014enemies "
                "appear to wade through molasses while you dance between their attacks. The long "
                "cooldown means you must choose your moment carefully.\n\n"
                "Duration: 3s. Enemies: half speed. Your attack speed: +25%. Cooldown: 30s. The "
                "ultimate tool for outmaneuvering overwhelming odds.")},
            {"title": _("Dash"), "body": _(
                "Propels the user forward in a burst of speed\u2014a short, sharp lunge that "
                "can mean the difference between life and death.\n\n"
                "Dash grants an instant burst of movement in the direction you are facing. It "
                "covers moderate ground in a fraction of a second, passing through enemies and "
                "projectiles without taking damage during the dash. The cooldown is short, "
                "encouraging frequent use.\n\n"
                "Distance is safety. Speed is life. Use Dash to close gaps, evade attacks, or "
                "reposition in the heat of battle.")},
        ]

    def _effects_pages(self):
        return [
            {"title": _("Boon: Regeneration"), "body": _(
                "Accelerated healing that restores health with every heartbeat of the caster.\n\n"
                "Regeneration is a beneficial effect that restores a set amount of health each "
                "second over its duration. It stacks with passive health recovery and other healing "
                "sources. The effect can be applied through potions, spells, food, or environmental "
                "effects such as resting at a campfire.\n\n"
                "Rate: ~5 HP per second. Duration varies by source. A steady flow of vitality that "
                "keeps you in the fight longer.\n\n"
                "Tip: Let regeneration top you off between fights to conserve potions.")},
            {"title": _("Bane: Poison"), "body": _(
                "Creeping death that seeps into the victim's bloodstream, dealing damage over "
                "time until cured or expired.\n\n"
                "Poison is a stacking damage-over-time effect. Each application adds a stack, "
                "and each stack deals independent damage per tick. The damage grows more dangerous "
                "as stacks accumulate\u2014a single Venomous strike may apply one stack, but "
                "repeated hits can stack poison to lethal levels quickly.\n\n"
                "Duration: 4s per stack. Damage: ~5 DPS per stack. Antidotes remove all poison "
                "stacks instantly and are worth their weight in gold. Without antidotes, you must "
                "wait for the poison to run its course.\n\n"
                "Tip: Always carry antidotes before exploring swamp biomes.")},
            {"title": _("Bane: Burn"), "body": _(
                "Fire remembers. The Burn effect lingers long after the initial blast, consuming "
                "its victim in persistent flame.\n\n"
                "Burn is a damage-over-time effect applied by fire-based attacks and environmental "
                "hazards such as lava pools and fire traps. Unlike poison, burn does not stack\u2014"
                "instead, a fresh application refreshes the duration. The damage per tick is higher "
                "than poison, making it more dangerous in short bursts.\n\n"
                "Duration: ~3.2s per application. Damage: higher DPS than poison. Can be "
                "extinguished by rolling or submerging in water.\n\n"
                "Tip: If you catch fire, roll to put it out. Standing still is a death sentence.")},
            {"title": _("Bane: Confusion"), "body": _(
                "Inverts your controls\u2014up becomes down, left becomes right, and your muscle "
                "memory becomes your enemy.\n\n"
                "Confusion is a disorienting status effect that reverses all directional input for "
                "approximately 3 seconds. Every instinct you have developed will betray you. The "
                "effect is applied by Trickster enemies and certain shadow-based traps. There is "
                "no direct cure\u2014you must wait it out.\n\n"
                "Duration: ~3s. Effect: directional inversion. No antidote exists. Trust nothing, "
                "not even your own hands.\n\n"
                "Tip: Invert your own thinking. If you need to go left, press right. It takes "
                "practice, but it can save your life.")},
            {"title": _("Bane: Dizziness"), "body": _(
                "The world spins around you. Colors smear and blur. Combat becomes a nauseating "
                "ordeal.\n\n"
                "Dizziness impairs your visual clarity, making it difficult to judge distances "
                "and track enemy movements. The screen wobbles and your character's movement "
                "becomes slightly sluggish. Often paired with Confusion by Trickster enemies\u2014"
                "together, they create a deadly cocktail of disorientation.\n\n"
                "Duration: ~2.2s. Effect: visual distortion, slight movement impairment. Often "
                "applied alongside Confusion.\n\n"
                "Tip: If both Confusion and Dizziness are active, retreat to a safe area and "
                "wait for both to expire. Fighting through both is a fool's errand.")},
            {"title": _("Bane: Slow"), "body": _(
                "A creeping weight settles into your limbs, slowing your movement to a crawl.\n\n"
                "Slow reduces your movement speed by approximately 50% for its duration. The "
                "effect can be applied by environmental hazards (deep snow, mud, water), enemy "
                "attacks (Ice-based spells, certain creature abilities), or traps. In combat, "
                "being slowed is exceptionally dangerous\u2014you cannot dodge, you cannot kite, "
                "and you cannot retreat.\n\n"
                "Duration: ~1.5s to 4s depending on source. Speed reduction: ~50%. Some sources "
                "also reduce attack speed.\n\n"
                "Tip: Speed is life. To be slowed is to be marked for death. Carry cleansing "
                "items or avoid hazards that apply this effect.")},
            {"title": _("Bane: Freeze & Root"), "body": _(
                "Two faces of the same cursed coin. Both leave you utterly unable to move, and "
                "both are followed by a killing blow.\n\n"
                "Freeze encases the target in solid ice, preventing all movement and actions for "
                "its duration. The ice can be broken early by taking enough damage\u2014make sure "
                "your allies are ready to shatter it. Root binds the target's feet to the earth, "
                "preventing movement but allowing attacks and abilities to be used. Root is applied "
                "by Entangling Roots and similar nature-based abilities.\n\n"
                "Freeze duration: 2\u20133 seconds. Breaks on sufficient damage.\n"
                "Root duration: 4 seconds. Movement only is blocked; attacks and abilities "
                "still work.\n\n"
                "Tip: A frozen or rooted fighter is a dead fighter. Prioritize cleansing or "
                "avoiding these effects above all others.")},
        ]

    def _guide_pages(self):
        return [
            {"title": _("1. Movement & Navigation"), "body": _(
                "The world is vast and unforgiving. Mastery of movement is your first and most essential "
                "skill.\n\n"
                "Use the WASD keys to navigate\u2014W for north, A for west, S for south, D for east. "
                "Hold Shift to sprint, granting you burst speed at the cost of stamina. The yellow "
                "stamina bar above your hotbar depletes with every sprinting step and refills when you "
                "walk or stand still.\n\n"
                "Walk into doorways and map edges to transition between areas. Some transitions are "
                "one-way\u2014once you descend into a dungeon, the only way out is through.\n\n"
                "Tip: Keep your stamina reserve for combat. A tired warrior is a dead warrior.")},
            {"title": _("2. Combat Basics"), "body": _(
                "The world does not wait for you to be ready. Learn the rhythm of battle or be "
                "consumed by it.\n\n"
                "Left-click any nearby enemy to perform a basic attack. Your health bar (red) sits "
                "at the top of the screen\u2014when it empties, you fall. Your stamina bar (yellow) "
                "sits just above the hotbar\u2014it fuels both sprinting and special maneuvers. Let "
                "neither run dry in a fight.\n\n"
                "When your health reaches zero, you respawn at your last activated save point. "
                "Enemies you have slain stay dead, but their patrols will be reinforced. Death is "
                "a setback, not an ending.\n\n"
                "Tip: Kite enemies one at a time when possible. Two foes are twice the trouble; "
                "three is a grave.")},
            {"title": _("3. Skills & Hotbar"), "body": _(
                "Your arsenal of abilities is bound to the hotbar\u2014quick access slots that mean "
                "the difference between victory and defeat.\n\n"
                "Press keys 1 through 6 to activate the skill in the corresponding hotbar slot. "
                "Skills range from offensive spells to defensive wards to mobility tools. Each "
                "skill has its own cooldown, shown as a dimming icon that slowly brightens as it "
                "becomes available again.\n\n"
                "Open the Skill Tree from your inventory screen to spend points earned through "
                "leveling. Branches include Fire, Ice, Lightning, Nature, Shadow, and Arcane\u2014"
                "each with its own philosophy and power.\n\n"
                "Tip: Build synergy. A Frost Nova to freeze, then a Fireball for double impact.")},
            {"title": _("4. Inventory & Items"), "body": _(
                "Your pack is your lifeline\u2014every potion, weapon, and trinket you carry may tip "
                "the scales of fate.\n\n"
                "Press E to open your inventory. Here you can equip weapons and armor, consume "
                "potions by right-clicking, and inspect every item in your possession. Hover your "
                "cursor over any item to see its detailed stats, flavor text, and sell value. Drag "
                "items with the left mouse button to rearrange your pack or move them between your "
                "inventory and other containers.\n\n"
                "Equipment slots include head, chest, legs, feet, main hand, and off-hand. Unequip "
                "items by dragging them back to your pack.\n\n"
                "Tip: Keep at least three health potions on you at all times. The wilderness is not "
                "merciful.")},
            {"title": _("5. Crafting & Recipes"), "body": _(
                "Creation is survival. From the humblest bandage to the mightiest blade, everything "
                "must be forged.\n\n"
                "Open your inventory and you will find a 3\u00d73 crafting grid. Place ingredients "
                "in the correct pattern, and the result appears in the output slot. Drag it into "
                "your pack to claim your creation.\n\n"
                "The Recipe Book, accessible from the crafting interface, records every recipe you "
                "have discovered. Some recipes are learned from scrolls and schematics found in the "
                "world. Others must be discovered through bold experimentation\u2014place unfamiliar "
                "combinations in the grid and see what emerges.\n\n"
                "Tip: The grid is small, but the possibilities are endless. Try every combination "
                "you can imagine.")},
            {"title": _("6. Leveling & Experience"), "body": _(
                "Every battle fought, every enemy vanquished, every challenge overcome\u2014all of it "
                "feeds the fire of your growth.\n\n"
                "Defeat enemies to earn experience points (XP). Your progress is tracked in the XP "
                "bar at the bottom of the screen. When it fills, you gain a level, which grants +20 "
                "maximum health and one Skill Tree point to spend on new abilities or enhance "
                "existing ones.\n\n"
                "The Skill Tree branches into six schools of power:\n"
                "\u2022 Fire \u2014 Raw destructive force and area denial.\n"
                "\u2022 Ice \u2014 Crowd control and defensive fortitude.\n"
                "\u2022 Lightning \u2014 Speed and chain damage.\n"
                "\u2022 Nature \u2014 Summoning and sustained warfare.\n"
                "\u2022 Shadow \u2014 Deception and high-risk, high-reward tactics.\n"
                "\u2022 Arcane \u2014 Utility and raw magical power.\n\n"
                "Tip: You cannot max every branch in a single playthrough. Choose your path wisely.")},
            {"title": _("7. Day & Night Cycle"), "body": _(
                "The sun rises and sets in this world, and with the changing light comes shifting "
                "danger.\n\n"
                "The full day-night cycle spans roughly 24 minutes of real time. During the day, "
                "visibility is high and most enemies follow predictable patrol routes. As dusk "
                "falls, shadows lengthen and the creatures of the dark stir.\n\n"
                "At night, many enemies become more aggressive\u2014their detection range increases, "
                "their damage may rise, and new nocturnal foes emerge from their lairs. The undead, "
                "in particular, grow bolder under the cover of darkness.\n\n"
                "Tip: If you hear howling at night, find shelter or light a torch. Some horrors "
                "only hunt in the dark.")},
            {"title": _("8. Enemies & Threat Assessment"), "body": _(
                "The realm is teeming with threats, each with its own deadly habits. Know your "
                "enemy before it knows you.\n\n"
                "\u2022 Brutes \u2014 Slow but devastating. Their Charge attack covers ground "
                "quickly. Dodge sideways, never backward. Strike after they miss.\n"
                "\u2022 Venomous \u2014 Their poison stacks quickly. Bring antidotes to every "
                "swamp encounter. Ranged attacks are safest.\n"
                "\u2022 Arcanists \u2014 Deadly at range, vulnerable up close. Close the distance "
                "and interrupt their casting.\n"
                "\u2022 Tricksters \u2014 Unpredictable and maddening. Predict their Blink "
                "destination and strike first.\n"
                "\u2022 Bombers \u2014 Timed bombs with a wide blast radius. Stay mobile and "
                "never stand still.\n"
                "\u2022 Stalkers \u2014 They remember your position. Breaking line of sight is "
                "not enough\u2014keep moving for three seconds.\n"
                "\u2022 Skirmishers \u2014 Ranged harriers that orbit at a distance. Close in to "
                "force them into melee.\n"
                "\u2022 Guardians \u2014 Immobile sentinels. Lure them to the edge of their "
                "leash range if you must engage.\n\n"
                "Tip: Knowledge is armor. Study each entry in the Bestiary before venturing into "
                "unknown territory.")},
            {"title": _("9. Respeccing & Strategy"), "body": _(
                "No path is set in stone. The wise warrior evolves with every battle.\n\n"
                "Your Skill Tree points shape your playstyle. A focused build\u2014investing "
                "deeply in a single school\u2014unlocks powerful tier-3 and tier-4 abilities that "
                "a generalist cannot reach. A spread build offers flexibility, letting you adapt "
                "to any situation with a broad toolkit.\n\n"
                "If you find your choices no longer serve you, the respec option allows you to "
                "reclaim all spent Skill Tree points and redistribute them. Visit the appropriate "
                "NPC or use the respec option in the Skill Tree menu.\n\n"
                "Tip: Respeccing is not failure. It is refinement. The best warriors adapt their "
                "build to the challenges ahead.")},
            {"title": _("10. Final Words"), "body": _(
                "The road ahead is long and lined with peril. You will fall. You will rise. "
                "You will fall again\u2014and still, you will rise.\n\n"
                "Remember: every potion crafted, every skill unlocked, every enemy studied is "
                "a thread in the tapestry of your legend. The world remembers what you do. "
                "The Codex Arcanum records your discoveries. The forge awaits your hand.\n\n"
                "Their mistakes are your lessons. Their triumphs are your inheritance.\n\n"
                "Now go. The realm awaits\u2014and it has never been ready for you.")},
        ]

    def _smeltery_pages(self):
        return [
            {"title": _("1. The Smeltery Unveiled"), "body": _(
                "Deep within the earth, where molten stone flows like rivers of fire, the first smeltery "
                "was kindled by dwarven forgemasters of old. Today, you stand at the threshold of that "
                "ancient craft.\n\n"
                "The Smeltery is a workstation of unparalleled power. Approach any smeltery tile and "
                "press E to open its panel. Within, four stations await:\n\n"
                "\u2699 Workbench \u2014 Shape raw materials into tools of war.\n"
                "\u2699 Coke Oven \u2014 Smelt ores with patient flame.\n"
                "\u2699 Blast Furnace \u2014 Forge alloys of legend.\n"
                "\u2699 Anvil \u2014 Restore the fallen to glory.\n\n"
                "Each station serves a purpose. Master them all, and the very metal will bend to your will.")},
            {"title": _("2. Workbench & Shaping"), "body": _(
                "The Workbench is your foundation. Here, in the 3\u00d73 crafting grid, raw ingredients "
                "are arranged in sacred patterns to produce arms, armor, and arcane components.\n\n"
                "Unlike standard crafting, the smeltery workbench accesses recipes that require "
                "smeltery-processed materials \u2014 ingots forged in the coke oven, alloys from the "
                "blast furnace, and metals refined through the heat of experience.\n\n"
                "Drag items between the grid and your inventory. The output slot will reveal the "
                "result when the arrangement matches a known pattern. Experiment freely \u2014 the "
                "forge rewards curiosity.\n\n"
                "Tip: Keep your recipe book close. It highlights which recipes call for "
                "smeltery-crafted components.")},
            {"title": _("3. Coke Oven & Fuel"), "body": _(
                "The Coke Oven is the first pillar of pyromancy. A simple furnace: input on the left, "
                "output on the right, and a hungry flame between them.\n\n"
                "Deposit raw ore into the input slot. The oven consumes it, and after a patient wait, "
                "pure smelted material appears in the output. The progress bar glows with the heat of "
                "your patience.\n\n"
                "The oven's beauty lies in its simplicity. One input, one output, and the quiet "
                "certainty of transformation. Load it with ore, tend to other stations, and return "
                "to collect your bounty.\n\n"
                "A single batch consumes one unit of input and produces one unit of refined material. "
                "The oven will automatically resume the next batch if more input is waiting.")},
            {"title": _("4. Blast Furnace & Alloys"), "body": _(
                "Where the coke oven merely purifies, the Blast Furnace creates something greater "
                "than the sum of its parts.\n\n"
                "Two input slots: ore on top, fuel below. The furnace combines them in a roaring "
                "marriage of elements, producing alloys of superior quality. Steel, darksteel, "
                "and stranger metals await those who discover the right combinations.\n\n"
                "The fuel slot accepts coal or other combustible materials. Each fuel has its own "
                "burning properties. Experiment with different ore-fuel pairs to unlock new recipes.\n\n"
                "High-tier alloys may trigger a Smeltery Minigame upon completion \u2014 a chance to "
                "refine the batch further through quick thinking and steady hands. Success yields "
                "bonus ingots and additional smelting experience.\n\n"
                "The blast furnace also locks its input slots while a job runs. Plan your batches wisely.")},
            {"title": _("5. Anvil & Restoration"), "body": _(
                "The Anvil is a sanctuary for the broken. Here, damaged weapons, armor, and tools "
                "are returned to their former glory.\n\n"
                "Three slots serve this purpose:\n"
                "\u2022 Damaged Item (left) \u2014 Place the battered weapon or armor here.\n"
                "\u2022 Material (center) \u2014 Iron ingots, steel ingots, or other repair materials.\n"
                "\u2022 Repaired Output (right) \u2014 Collect the restored item.\n\n"
                "The anvil consumes the repair material immediately and begins its work. A progress "
                "bar tracks the restoration. The status line below previews the durability recovery.\n\n"
                "Not all items are repairable. Unbreakable artifacts and fully intact gear cannot be "
                "placed on the anvil. Likewise, only certain materials can serve as repair agents.\n\n"
                "A word of caution: removing the damaged item mid-repair cancels the job and the "
                "material is lost. Choose your repairs with care.")},
            {"title": _("6. Smelting Skill & Mastery"), "body": _(
                "Every ingot forged, every alloy refined, every item repaired feeds your Smelting "
                "Skill. This hidden art grows with you, granting greater rewards as your mastery "
                "deepens.\n\n"
                "The skill bar at the bottom of the smeltery panel shows your current level and "
                "experience progress:\n\n"
                "\u2022 Smelting Lv. X \u2014 Your current rank in the forgemaster's craft.\n"
                "\u2022 Progress Bar \u2014 Tracks advancement to the next level.\n"
                "\u2022 XP Counter \u2014 Current / required experience.\n\n"
                "Higher levels unlock:\n"
                "\u2022 Better minigame rewards (bonus ingots per success)\n"
                "\u2022 Higher-tier item crafting chances\n"
                "\u2022 Increased respect among the world's merchants\n\n"
                "The path of the forgemaster is one of patience and persistence. Smelt often. "
                "Smelt well. The metal remembers.")},
            {"title": _("7. Minigames & Refinement"), "body": _(
                "When the Blast Furnace completes a high-tier alloy, the forge itself may challenge "
                "you to prove your worth through a Smeltery Minigame.\n\n"
                "These are brief, interactive trials that test your reflexes and focus:\n\n"
                "\u2022 Tending the Fire \u2014 Stoke the flames at just the right moment. "
                "Too weak and the metal cools. Too strong and it burns.\n"
                "\u2022 Iron Forge \u2014 Strike the glowing ingot while the hammer's rhythm "
                "matches the heartbeat of the forge.\n"
                "\u2022 Arcane Crucible \u2014 Channel magical energy into the molten pool, "
                "stabilizing its arcane resonance.\n"
                "\u2022 Quench & Temper \u2014 Plunge the hot metal into the quenching bath "
                "at the precise temperature for optimal hardening.\n\n"
                "Success yields bonus output \u2014 extra ingots, improved quality, and bonus "
                "smelting XP. Failure grants nothing but experience. Every attempt refines "
                "the forgemaster.")},
            {"title": _("8. Forgemaster's Secrets"), "body": _(
                "The greatest smelters know that the forge is not merely a tool \u2014 it is a "
                "partner. Here are the secrets whispered among master forgemasters:\n\n"
                "\u2726 The Blast Furnace respects efficiency. Fuel lasts longer when the "
                "furnace is kept running. Batch processing is the mark of a master.\n\n"
                "\u2726 Anvil repairs consume material upfront. Always inspect the preview "
                "before committing. A single ingot can restore a legendary blade to full power.\n\n"
                "\u2726 Minigames scale with your Smelting Level. A level 50 forgemaster "
                "extracts far more bonus ingots than a novice. Persevere.\n\n"
                "\u2726 The Workbench grid can combine smeltery outputs into finished gear. "
                "Plan your production chain: mine \u2192 smelt \u2192 alloy \u2192 craft.\n\n"
                "\u2726 Some recipes are not discovered but inherited. Seek ancient texts and "
                "lost schematics in your adventures. The Codex Arcanum remembers all.\n\n"
                "The forge awaits. Make it sing.")},
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
        elif self._show_toc:
            ny = sh - bh - max(16, int(24 * scale))
            mx = max(20, int(30 * scale))
            self.back_btn.rect = pygame.Rect(mx, ny, bw, bh)
            if self._skip_to_gameplay and self._page == "guide":
                pad2 = max(8, int(24 * scale))
                box2 = pygame.Rect(pad2, pad2, sw - 2 * pad2, sh - 2 * pad2)
                inner2 = box2.inflate(-int(60 * scale), -int(100 * scale))
                btn_w2 = max(1, int(340 * scale))
                btn_h2 = max(1, int(62 * scale))
                btn_x2 = inner2.x + (inner2.width - btn_w2) // 2
                btn_y2 = inner2.y + inner2.height - btn_h2 - int(60 * scale)
                self.begin_btn.rect = pygame.Rect(btn_x2, btn_y2, btn_w2, btn_h2)
        else:
            ny = sh - bh - max(40, int(60 * scale))
            mx = max(40, int(60 * scale))
            gap = max(8, int(10 * scale))
            x = mx
            if self._sub_page > 0:
                self.prev_btn.rect = pygame.Rect(x, ny, bw, bh)
                x += bw + gap
            self.back_btn.rect = pygame.Rect(x, ny, bw, bh)
            x += bw + gap
            self.toc_btn.rect = pygame.Rect(x, ny, bw, bh)
            self.next_btn.rect = pygame.Rect(sw - bw - mx, ny, bw, bh)
            if self._skip_to_gameplay and self._page == "guide":
                btn_w = max(1, int(340 * scale))
                btn_h = max(1, int(62 * scale))
                btn_x = (sw - btn_w) // 2
                self.begin_btn.rect = pygame.Rect(btn_x, ny, btn_w, btn_h)
        for b in (self.back_btn, self.prev_btn, self.next_btn, self.toc_btn, self.begin_btn):
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
            locked = self._page != "guide" and not self.app.article_tracker.already_seen(self._page, et)

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

            if locked:
                ns2 = self.font_small.render("?", True, GOLD_DARK)
            else:
                ns2 = self.font_small.render(f"{i+1}.", True, GOLD_BRIGHT)
            screen.blit(ns2, (er.x + 12, er.y + (er.height - ns2.get_height()) // 2))

            tc = GOLD_BRIGHT if hov else self.ink_color
            if locked:
                tc = tuple(c // 2 + 30 for c in self.ink_color)
            es = self.font_toc.render(et, True, tc)
            screen.blit(es, (er.x + 48, er.y + (er.height - es.get_height()) // 2))

            if locked:
                seal_size = max(1, int(entry_h * 0.55))
                sc = seal_size // 2
                ga = int(18 + 14 * math.sin(t * 2))
                gs2 = pygame.Surface((seal_size + 6, seal_size + 6), pygame.SRCALPHA)
                pygame.draw.circle(gs2, (*theme["glow"], ga), (gs2.get_width() // 2, gs2.get_height() // 2), sc)
                ss = pygame.Surface((seal_size, seal_size), pygame.SRCALPHA)
                pygame.draw.circle(ss, theme["accent"], (sc, sc), sc, max(1, int(2 * scale)))
                pygame.draw.circle(ss, theme["accent"], (sc, sc), sc - max(2, int(3 * scale)), 1)
                si = self.font_small.render(theme.get("icon", "?"), True, theme["accent"])
                si.set_alpha(180)
                ss.blit(si, (sc - si.get_width() // 2, sc - si.get_height() // 2))
                gx = er.right - seal_size - 14 - 3
                gy = er.y + (er.height - seal_size) // 2 - 3
                screen.blit(gs2, (gx, gy))
                screen.blit(ss, (er.right - seal_size - 14, er.y + (er.height - seal_size) // 2))
            elif hov:
                ar = self.font_small.render("\u2192", True, GOLD_BRIGHT)
                screen.blit(ar, (er.right - ar.get_width() - 14,
                                 er.y + (er.height - ar.get_height()) // 2 + int(math.sin(t * 4) * 3)))

            self._toc_entry_rects.append((er, i))

        hs = self.font_small.render(_("Select an entry to read"), True, self.ink_light)
        hs.set_alpha(int(140 + 60 * math.sin(t * 0.8)))
        screen.blit(hs, (inner.x + (inner.width - hs.get_width()) // 2,
                         inner.y + inner.height - hs.get_height() - 10))

        if self._skip_to_gameplay and self._page == "guide":
            self.begin_btn.draw(screen)

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

        locked = self._page != "guide" and not self.app.article_tracker.already_seen(self._page, title)
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
        if locked:
            dark_accent = tuple(max(0, c // 4) for c in theme["accent"])
            cx = inner.x + taw2 // 2
            cy = tt2 + int(60 * scale) + int(math.sin(t * 0.8) * 4 * scale)

            seal_radius = max(30, int(55 * scale))
            sc = seal_radius
            ring = pygame.Surface((sc * 2, sc * 2), pygame.SRCALPHA)
            # Outer ring
            pygame.draw.circle(ring, (*dark_accent, 60), (sc, sc), sc, max(1, int(2 * scale)))
            # Inner ring
            pygame.draw.circle(ring, (*dark_accent, 40), (sc, sc), int(sc * 0.7), max(1, int(scale)))
            # Compass rays
            for ang in range(0, 360, 90):
                rad = math.radians(ang + t * 30)
                ex = sc + math.cos(rad) * sc
                ey = sc + math.sin(rad) * sc
                pygame.draw.line(ring, (*dark_accent, 35), (sc, sc), (ex, ey), max(1, int(scale)))
            # Mid-point ticks
            for ang in range(45, 360, 90):
                rad = math.radians(ang - t * 20)
                tx = sc + math.cos(rad) * sc * 0.85
                ty = sc + math.sin(rad) * sc * 0.85
                pygame.draw.circle(ring, (*dark_accent, 50), (int(tx), int(ty)), max(1, int(2 * scale)))

            # Glow
            glow_r = int(sc * 1.4)
            gs = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            ga = int(10 + 8 * math.sin(t * 1.5))
            pygame.draw.circle(gs, (*theme["glow"], ga), (glow_r, glow_r), glow_r)
            screen.blit(gs, (cx - glow_r, cy - glow_r))
            screen.blit(ring, (cx - sc, cy - sc))

            # Section icon in center
            icon_char = theme.get("icon", "?")
            icon_sz = max(1, int(36 * scale))
            icon_fnt = cfg.get_font(icon_sz)
            icon_surf = icon_fnt.render(icon_char, True, theme["accent"])
            icon_surf.set_alpha(int(70 + 40 * math.sin(t * 1.5)))
            screen.blit(icon_surf, (cx - icon_surf.get_width() // 2, cy - icon_surf.get_height() // 2))

            # Orbital wisps — outer ring
            for i in range(4):
                ang = t * 0.8 + i * math.pi * 0.5
                d = sc * 0.85
                wpx = cx + math.cos(ang) * d
                wpy = cy + math.sin(ang) * d
                wa = int(40 + 30 * math.sin(t * 1.2 + i * 1.5))
                ws = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(ws, (*theme["glow"], wa), (3, 3), 3)
                screen.blit(ws, (wpx - 3, wpy - 3))
            # Orbital wisps — inner ring
            for i in range(3):
                ang = t * 1.1 + i * math.pi * 0.667 + 0.5
                d = sc * 0.55
                wpx = cx + math.cos(ang) * d
                wpy = cy + math.sin(ang) * d
                wa = int(25 + 20 * math.sin(t * 1.5 + i * 2.0))
                ws = pygame.Surface((4, 4), pygame.SRCALPHA)
                pygame.draw.circle(ws, (*theme["accent"], wa), (2, 2), 2)
                screen.blit(ws, (wpx - 2, wpy - 2))

            sub = self.font_subtitle.render("Not yet discovered", True,
                                             tuple(c // 2 + 40 for c in self.ink_light))
            sub.set_alpha(int(130 + 50 * math.sin(t * 0.7)))
            sub_x = inner.x + (taw2 - sub.get_width()) // 2
            sub_y = cy + sc + int(30 * scale)
            screen.blit(sub, (sub_x, sub_y))
        else:
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
        if self._skip_to_gameplay and self._page == "guide":
            self.begin_btn.draw(screen)

    # ─── Events ─────────────────────────────────────────────
    def handle_event(self, event):
        if self._page == "main" and hasattr(self, 'section_button_data'):
            self._handle_main_click(event)
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._skip_to_gameplay and self._page == "guide":
                if self.begin_btn.rect.collidepoint(event.pos):
                    self.begin_btn.on_click(); return
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
                        self._toc_hover = idx; break
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