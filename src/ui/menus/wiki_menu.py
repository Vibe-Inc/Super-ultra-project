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
DEEP_RED = (140, 30, 20)
ROYAL_BLUE = (20, 40, 100)
FOREST_GREEN = (25, 70, 35)
PURPLE_SHADOW = (50, 20, 60)

SECTION_THEMES = {
    "main":     {"accent": GOLD,        "border": (180,140,60),  "glow": GOLD_BRIGHT,      "icon": "\u269A"},
    "bestiary": {"accent": (180,80,40), "border": (120,50,20),  "glow": (220,120,60),     "icon": "\u2694"},
    "magic":    {"accent": (200,120,40),"border": (160,80,20),  "glow": (255,180,60),     "icon": "\u2726"},
    "effects":  {"accent": (120,60,140),"border": (80,30,100),  "glow": (180,100,220),    "icon": "\u2622"},
    "guide":    {"accent": ROYAL_BLUE,  "border": (30,20,80),   "glow": (80,120,220),     "icon": "\u270E"},
}


class WikiParticle:
    def __init__(self, x, y, vx, vy, lifetime, color, size, glow=False, star=False):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.size = size
        self.glow = glow
        self.star = star

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        self.vy += 60 * dt

    def draw(self, surf, offset=(0, 0)):
        if self.lifetime <= 0:
            return
        alpha = max(0, min(255, int(255 * (self.lifetime / self.max_lifetime))))
        px = int(self.x + offset[0])
        py = int(self.y + offset[1])
        sz = max(1, int(self.size * (0.6 + 0.4 * (self.lifetime / self.max_lifetime))))
        c = (self.color[0], self.color[1], self.color[2], alpha)

        if self.star:
            s = pygame.Surface((sz * 6, sz * 6), pygame.SRCALPHA)
            cx2 = sz * 3
            cy2 = sz * 3
            pts = []
            for i in range(10):
                a2 = math.radians(i * 36 - 90)
                r2 = sz * 3 if i % 2 == 0 else sz * 1.2
                pts.append((cx2 + r2 * math.cos(a2), cy2 + r2 * math.sin(a2)))
            pygame.draw.polygon(s, c, pts)
            surf.blit(s, (px - cx2, py - cy2))
            return

        if self.glow:
            for r in range(4, 0, -1):
                ga = alpha // (r * 3)
                gc = (self.color[0], self.color[1], self.color[2], ga)
                gs = pygame.Surface((sz * r * 5, sz * r * 5), pygame.SRCALPHA)
                pygame.draw.circle(gs, gc, (sz * r * 2.5, sz * r * 2.5), sz * r)
                surf.blit(gs, (px - sz * r * 2.5, py - sz * r * 2.5))
        s2 = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(s2, c, (sz, sz), sz)
        surf.blit(s2, (px - sz, py - sz))


def _wrap_text(text, font, max_width):
    lines = []
    paragraphs = text.split('\n')
    for para in paragraphs:
        words = para.split(' ')
        current = ''
        for word in words:
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


def _draw_parchment_bg(surf, rect, scale):
    r = pygame.Rect(rect)
    shadow = r.inflate(10, 10)
    ss = pygame.Surface(shadow.size, pygame.SRCALPHA)
    for i in range(6, 0, -1):
        a = 15 // i
        pygame.draw.rect(ss, (0, 0, 0, a), ss.get_rect().inflate(-i * 2, -i * 2), border_radius=26)
    surf.blit(ss, shadow.topleft)
    inner = r.inflate(-4, -4)
    pygame.draw.rect(surf, PARCHMENT_DARK, r, border_radius=26)
    pygame.draw.rect(surf, PARCHMENT_LIGHT, inner, border_radius=22)


def _draw_ornate_border(surf, rect, theme, scale):
    accent = theme["accent"]
    border = theme["border"]

    _draw_parchment_bg(surf, rect, scale)

    r = pygame.Rect(rect)
    pygame.draw.rect(surf, border, r, max(2, int(4 * scale)), border_radius=26)
    inner2 = r.inflate(-4, -4)
    pygame.draw.rect(surf, accent, inner2, max(1, int(2 * scale)), border_radius=22)

    ofs = max(6, int(16 * scale))
    corner_size = max(4, int(14 * scale))
    for cx_pos, cy_pos, dx, dy in [
        (r.x + ofs, r.y + ofs, 1, 1),
        (r.right - ofs, r.y + ofs, -1, 1),
        (r.x + ofs, r.bottom - ofs, 1, -1),
        (r.right - ofs, r.bottom - ofs, -1, -1),
    ]:
        pts = []
        for i in range(16):
            a = math.radians(i * 22.5)
            rad = corner_size * (0.5 + 0.5 * math.sin(i * 2.0 + 0.8))
            px = cx_pos + dx * rad * math.cos(a)
            py = cy_pos + dy * rad * math.sin(a)
            pts.append((px, py))
        if len(pts) > 2:
            pygame.draw.polygon(surf, accent, pts, max(1, int(2 * scale)))
            pygame.draw.polygon(surf, GOLD_BRIGHT, pts, max(1, int(1 * scale)))

    for y in range(r.y + int(40 * scale), r.bottom - int(40 * scale), int(50 * scale)):
        w = max(1, int(2 * scale))
        lx = r.x + int(10 * scale)
        rx = r.right - int(10 * scale)
        pygame.draw.line(surf, border, (lx, y), (lx + int(16 * scale), y), w)
        pygame.draw.line(surf, border, (rx - int(16 * scale), y), (rx, y), w)


def _draw_gold_divider(surf, x, y, width, scale):
    mid = y
    thin = max(1, int(1.5 * scale))
    thick = max(2, int(3 * scale))
    pygame.draw.line(surf, GOLD_DARK, (x, mid), (x + width, mid), thick)
    pygame.draw.line(surf, GOLD_BRIGHT, (x, mid - thin), (x + width, mid - thin), thin)
    pygame.draw.line(surf, (180, 140, 60), (x, mid + thick), (x + width, mid + thick), thin)
    for cx in (x + width // 4, x + width // 2, x + 3 * width // 4):
        ds = pygame.Surface((int(10 * scale), int(10 * scale)), pygame.SRCALPHA)
        h = int(5 * scale)
        pts = [(h, 0), (int(10 * scale), h), (h, int(10 * scale)), (0, h)]
        pygame.draw.polygon(ds, GOLD_BRIGHT, pts)
        pygame.draw.polygon(ds, GOLD, [(p[0] + 1, p[1] + 1) for p in pts], 1)
        surf.blit(ds, (cx - h, mid - h))


def _draw_corner_scroll(surf, rect, scale):
    ofs = max(8, int(20 * scale))
    for cx, cy, dx, dy in [
        (rect.x + ofs, rect.y + ofs, 1, 1),
        (rect.right - ofs, rect.y + ofs, -1, 1),
        (rect.x + ofs, rect.bottom - ofs, 1, -1),
        (rect.right - ofs, rect.bottom - ofs, -1, -1),
    ]:
        pts = []
        for i in range(12):
            t = i / 11
            angle = t * math.pi * 0.5
            rx = max(4, int(28 * scale)) * (1 - 0.3 * t)
            ry = max(3, int(18 * scale)) * (1 - 0.4 * t)
            px = cx + dx * rx * math.cos(angle)
            py = cy + dy * ry * math.sin(angle)
            pts.append((px, py))
        if len(pts) > 2:
            pygame.draw.lines(surf, GOLD, False, pts, max(1, int(2 * scale)))
            pygame.draw.lines(surf, GOLD_BRIGHT, False,
                              [(p[0] + dx * 1, p[1] + dy * 1) for p in pts],
                              max(1, int(1 * scale)))


_WIKI_PORTRAIT_CACHE = {}


def _get_monster_portrait(visual_style, size=140):
    key = (visual_style, size)
    if key in _WIKI_PORTRAIT_CACHE:
        return _WIKI_PORTRAIT_CACHE[key]
    anims = build_monster_animations(visual_style, (size, size))
    frame = anims["down"][0].copy()
    total = size + 24
    surf = pygame.Surface((total, total), pygame.SRCALPHA)
    for r in range(12, 0, -1):
        a = 18 // r
        c = (GOLD[0], GOLD[1], GOLD[2], a)
        pygame.draw.circle(surf, c, (total // 2, total // 2), size // 2 + r, 2)
    surf.blit(frame, ((total - size) // 2, (total - size) // 2))
    _WIKI_PORTRAIT_CACHE[key] = surf
    return surf


def _draw_portrait_frame(surf, x, y, size, theme, scale, pulse):
    frame_sz = size + 8
    fs = pygame.Surface((frame_sz, frame_sz), pygame.SRCALPHA)
    c = theme["accent"]
    for r in range(6, 0, -1):
        a = int(30 * pulse // r)
        pygame.draw.rect(fs, (*c, a), fs.get_rect().inflate(-r * 2, -r * 2),
                         max(1, int(2 * scale)), border_radius=10)
    pygame.draw.rect(fs, GOLD, fs.get_rect(), max(2, int(3 * scale)), border_radius=10)
    pygame.draw.rect(fs, GOLD_BRIGHT, fs.get_rect().inflate(-3, -3),
                     max(1, int(1 * scale)), border_radius=8)
    for cx, cy in [(4, 4), (frame_sz - 4, 4), (4, frame_sz - 4), (frame_sz - 4, frame_sz - 4)]:
        pygame.draw.circle(fs, GOLD_BRIGHT, (cx, cy), max(2, int(3 * scale)))
    surf.blit(fs, (x - 4, y - 4))


SECTIONS_META = {
    "bestiary": {"subtitle": _("Foes of the Realm"), "icon": "\u2694", "entries": [
        _("The Brute"), _("The Venomous"), _("The Arcanist"),
        _("The Trickster"), _("The Bomber"),
    ]},
    "magic": {"subtitle": _("Spells of Power"), "icon": "\u2726", "entries": [
        _("Fireball"), _("Flame Shield"), _("Frost Nova"), _("Ice Armor"),
        _("Glacial Cascade"), _("Chain Lightning"), _("Thunderstrike"),
        _("Entangling Roots"), _("Summon Spirit"), _("Shadow Step"),
        _("Dark Pact"), _("Arcane Missiles"), _("Mystic Barrier"),
        _("Berserker's Rage"), _("Chrono Shift"), _("Dash"),
    ]},
    "effects": {"subtitle": _("Curse & Blessing"), "icon": "\u2622", "entries": [
        _("Boon: Regeneration"), _("Bane: Poison"), _("Bane: Burn"),
        _("Bane: Confusion"), _("Bane: Dizziness"), _("Bane: Slow"),
        _("Bane: Freeze & Root"),
    ]},
    "guide": {"subtitle": _("Adventurer's Handbook"), "icon": "\u270E", "entries": [
        _("1. Movement & Navigation"), _("2. Combat Basics"),
        _("3. Skills & Hotbar"), _("4. Inventory & Items"),
        _("5. Crafting & Recipes"), _("6. Leveling & Experience"),
        _("7. Day & Night Cycle"), _("8. Enemies & Threat Assessment"),
        _("9. Respeccing & Strategy"), _("10. Final Words"),
    ]},
}


class WikiMenu(Menu):
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
        self._anim_time = 0.0
        self._page_enter_time = 0

        scale = cfg.ui_scale()
        btn_w = max(1, int(240 * scale))
        btn_h = max(1, int(66 * scale))

        self.buttons = []

        self.back_btn = Button(
            pygame.Rect(0, 0, btn_w, btn_h),
            _("BACK"),
            cfg.button_color_SETTINGS_BACK,
            cfg.button_hover_color_SETTINGS_BACK,
            cfg.button_font, cfg.text_color, cfg.corner_radius,
            on_click=self._go_back
        )

        self.prev_btn = Button(
            pygame.Rect(0, 0, btn_w, btn_h),
            _("<< PREV"),
            cfg.button_color_SETTINGS,
            cfg.button_hover_color_SETTINGS,
            cfg.button_font, cfg.text_color, cfg.corner_radius,
            on_click=self._prev_page
        )

        self.next_btn = Button(
            pygame.Rect(0, 0, btn_w, btn_h),
            _("NEXT >>"),
            cfg.button_color_SETTINGS,
            cfg.button_hover_color_SETTINGS,
            cfg.button_font, cfg.text_color, cfg.corner_radius,
            on_click=self._next_page
        )

        self.toc_btn = Button(
            pygame.Rect(0, 0, btn_w, btn_h),
            _("CONTENTS"),
            (100, 80, 60), (140, 120, 90),
            cfg.button_font, cfg.text_color, cfg.corner_radius,
            on_click=self._toggle_toc
        )

        self.section_buttons = []
        self._build_main_page()
        self._toc_hover = -1

    def on_enter(self):
        self._anim_time = 0.0
        self._page_enter_time = pygame.time.get_ticks()

    def _build_main_page(self):
        self._page = "main"
        self._sub_page = 0
        self._show_toc = False
        self.section_buttons.clear()
        themes = [
            (_("Bestiary"), _("Foes of the Realm"), self._open_bestiary, SECTION_THEMES["bestiary"]),
            (_("Magic"), _("Spells of Power"), self._open_magic, SECTION_THEMES["magic"]),
            (_("Alterations"), _("Curse & Blessing"), self._open_effects, SECTION_THEMES["effects"]),
            (_("Guide"), _("Adventurer's Handbook"), self._open_guide, SECTION_THEMES["guide"]),
        ]
        self.section_button_data = themes

    def _open_bestiary(self):
        self._page = "bestiary"
        self._sub_page = 0
        self._show_toc = True
        self._page_enter_time = pygame.time.get_ticks()
        self._emit_page_particles(SECTION_THEMES["bestiary"])

    def _open_magic(self):
        self._page = "magic"
        self._sub_page = 0
        self._show_toc = True
        self._page_enter_time = pygame.time.get_ticks()
        self._emit_page_particles(SECTION_THEMES["magic"])

    def _open_effects(self):
        self._page = "effects"
        self._sub_page = 0
        self._show_toc = True
        self._page_enter_time = pygame.time.get_ticks()
        self._emit_page_particles(SECTION_THEMES["effects"])

    def _open_guide(self):
        self._page = "guide"
        self._sub_page = 0
        self._show_toc = True
        self._page_enter_time = pygame.time.get_ticks()
        self._emit_page_particles(SECTION_THEMES["guide"])

    def _emit_page_particles(self, theme):
        sw, sh = cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT
        for _ in range(50):
            x = random.randint(0, sw)
            y = random.randint(0, sh)
            vx = random.uniform(-100, 100)
            vy = random.uniform(-250, -30)
            lt = random.uniform(0.5, 2.0)
            sz = random.randint(2, 6)
            self.particles.append(WikiParticle(
                x, y, vx, vy, lt, theme["accent"], sz,
                glow=random.random() < 0.3, star=random.random() < 0.15
            ))

    def _go_back(self):
        if self._show_toc and self._sub_page > 0:
            self._show_toc = False
            self._sub_page = 0
            return
        if self._page != "main":
            self._build_main_page()
            self._page_enter_time = pygame.time.get_ticks()
        else:
            self.app.manager.set_state("pause")

    def _toggle_toc(self):
        self._show_toc = not self._show_toc
        if self._show_toc:
            self._sub_page = 0
        self._page_enter_time = pygame.time.get_ticks()

    def _prev_page(self):
        if self._sub_page > 0:
            self._sub_page -= 1
            self._show_toc = False
            self._page_enter_time = pygame.time.get_ticks()

    def _next_page(self):
        max_p = self._get_max_subpages()
        if self._sub_page < max_p:
            self._sub_page += 1
            self._show_toc = False
            self._page_enter_time = pygame.time.get_ticks()

    def _get_max_subpages(self):
        pages = self._get_content()
        return max(0, len(pages) - 1)

    def _theme(self):
        return SECTION_THEMES.get(self._page, SECTION_THEMES["main"])

    def _get_content(self):
        if self._page == "bestiary":
            return self._bestiary_pages()
        if self._page == "magic":
            return self._magic_pages()
        if self._page == "effects":
            return self._effects_pages()
        if self._page == "guide":
            return self._guide_pages()
        return []

    def _get_meta(self):
        return SECTIONS_META.get(self._page, {})

    def _bestiary_pages(self):
        return [
            {"title": _("The Brute"),     "portrait": "brute",     "body": _(
                "They say the first Brute was born from a boulder struck by lightning"
                "\u2014a creature of fury and stone. These hulking warriors patrol the old "
                "roads with a single purpose: to crush anything that moves.\n\n"
                "A Brute does not rush. It stalks. It waits. And when the moment is right, "
                "it charges with the force of an avalanche, shaking the very ground beneath "
                "your feet. Its slam can shatter shields and leave even the hardiest "
                "adventurer gasping, slowed and broken.\n\n"
                "Abilities: Charge (2.4\u00d7 speed, 220 range), Slam (1.5\u00d7 damage, "
                "knockback, slow 1.5s). Health: 160. Speed: 110.")},
            {"title": _("The Venomous"),  "portrait": "venomous",  "body": _(
                "In the swamplands where even the trees have learned to bite, the Venomous "
                "make their dens. These lithe, green-skinned stalkers move through the mists "
                "like whispers, their blades dripping with toxin.\n\n"
                "A single scratch from their weapons will send poison surging through your "
                "veins\u2014a creeping decay that grows stronger the longer you ignore it. "
                "They are patient hunters who harry their prey from the shadows, striking "
                "and fading before the victim can even cry out.\n\n"
                "Abilities: Poison Strike (4s, 5 DPS). Health: 95. Speed: 130. "
                "Resistant to their own toxins.")},
            {"title": _("The Arcanist"),  "portrait": "arcanist",  "body": _(
                "Magic is a gift, they say. But some gifts come with a price. The Arcanists "
                "are former students of the arcane who delved too deep into forbidden "
                "knowledge, their flesh now crackling with barely contained fire.\n\n"
                "These robed figures hurl bolts of searing flame from a distance, their aim "
                "uncanny and their patience endless. The wounds they leave do not stop "
                "hurting\u2014the fire clings to your skin, burning long after the blast.\n\n"
                "Abilities: Arcane Bolt (480 speed, 560 range, burn 3.2s at 4.5 DPS). "
                "Health: 80. Speed: 115. Vulnerable up close.")},
            {"title": _("The Trickster"), "portrait": "trickster", "body": _(
                "Beware the laughter in the dark. The Tricksters are capricious horrors "
                "that delight in confusion and disarray. Dressed in ragged finery, they "
                "blink through shadows and appear behind you with a blade already swinging.\n\n"
                "Their touch clouds the mind\u2014suddenly left is right, forward is back, "
                "and your own feet refuse to obey. Worse still, the world spins around you "
                "in a dizzying dance that makes even standing still an act of will.\n\n"
                "Abilities: Blink (240 range), Confuse (2.8s), Dizzy (2.2s). "
                "Health: 75. Speed: 150. Fragile but elusive.")},
            {"title": _("The Bomber"),    "portrait": "bomber",    "body": _(
                "Where there is fire, there is the Bomber. These mad engineers carry "
                "satchels of volatile concoctions and delight in turning the battlefield "
                "into a cacophony of explosions.\n\n"
                "They keep their distance, lobbing timed bombs that arc through the air "
                "with deceptive grace. When the fuse runs out\u2014the world goes red. "
                "The blast hurls shrapnel and adventurers alike across the field.\n\n"
                "Abilities: Timed Bomb (95 blast radius, 80 knockback, 0.9s fuse). "
                "Health: 125. Speed: 105. Keep moving.")},
        ]

    def _magic_pages(self):
        return [
            {"title": _("Fireball"),          "body": _(
                "The quintessence of destructive magic. The Fireball spell compresses "
                "a spark of elemental flame into a roaring sphere that streaks toward "
                "its target before erupting in a glorious conflagration.\n\n"
                "Damage: 28 base (area). Range: 520. Knockback: moderate. "
                "The blast radius catches all who stand too close, hurling them back "
                "and leaving scorched earth where they stood.\n\n"
                "Pyromancer's Fury upgrade: 25% more damage, 15% larger radius.")},
            {"title": _("Flame Shield"),      "body": _(
                "A wreath of protective flames that surrounds the caster, turning "
                "them into a walking pyre. The Flame Shield scorches any foe foolish "
                "enough to approach.\n\n"
                "Damage: 8/sec to nearby enemies. Duration: 6 seconds. "
                "It does not prevent damage\u2014it merely ensures that anyone "
                "who hurts you will share your pain.")},
            {"title": _("Frost Nova"),         "body": _(
                "A desperate cry to the winter winds. Frost Nova sends a razored ring "
                "of ice expanding outward from the caster, freezing the very air and "
                "any enemy caught within its reach.\n\n"
                "Radius: 150. Freeze: 3 seconds. Enemies trapped in ice can "
                "neither move nor fight\u2014they stand as frozen statues, helpless "
                "against whatever follows.")},
            {"title": _("Ice Armor"),          "body": _(
                "A cloak of crystalline frost that forms around the caster's body, "
                "absorbing incoming blows and chilling those who dare to strike. "
                "The armor can absorb up to 30 damage before shattering.\n\n"
                "Duration: 8s. Attackers within 80px slowed by half. "
                "The slower they are, the easier to avoid retaliation.")},
            {"title": _("Glacial Cascade"),    "body": _(
                "A focused beam of frozen fury that tears across the battlefield. "
                "Glacial Cascade sends a torrent of ice shards racing forward, dealing "
                "35 damage to everything in its path.\n\n"
                "Freeze: 2 seconds. The cascade travels far and wide, "
                "freezing enemies who thought themselves safely out of reach.")},
            {"title": _("Chain Lightning"),    "body": _(
                "The storm's wrath, captured and directed. Chain Lightning leaps from "
                "the caster's fingertips to the nearest foe, then arcs to the next, "
                "dancing between up to 5 enemies with vengeful fury.\n\n"
                "Damage: 22/strike. Range: 550. Chain: 180. "
                "It may not hit as hard as a fireball, but every spark finds a target.")},
            {"title": _("Thunderstrike"),      "body": _(
                "A bolt from the blue\u2014literally. Thunderstrike calls a column of "
                "lightning down from the heavens upon a chosen location, dealing "
                "catastrophic damage to all beneath it.\n\n"
                "Damage: 55. Radius: 100. Range: 600. "
                "The thunder that follows is as much a warning as a eulogy.")},
            {"title": _("Entangling Roots"),   "body": _(
                "The earth remembers the touch of life. Entangling Roots calls forth "
                "ancient tendrils from the soil that snake toward the target and erupt "
                "in a thicket of grasping vines.\n\n"
                "Root: 4 seconds. Radius: 140. Range: 500. "
                "Enemies caught cannot move\u2014they can only watch as you line up "
                "the perfect strike.")},
            {"title": _("Summon Spirit"),      "body": _(
                "A bond with the wilds that transcends death. Summon Spirit calls a "
                "nature spirit from the green realm to fight at your side\u2014a "
                "flickering wisp of leaves and light that harries your enemies.\n\n"
                "Spirit Damage: 15. Duration: 10 seconds. The spirit fights "
                "autonomously, attacking nearby foes and drawing their attention.")},
            {"title": _("Shadow Step"),        "body": _(
                "The shadows are a doorway for those who know the password. Shadow Step "
                "allows the caster to dissolve into darkness and reappear a short "
                "distance away, leaving only a whisper and a fading silhouette.\n\n"
                "Range: 300. Invulnerability: 0.5s after arrival. "
                "A perfect escape\u2014or a perfect setup for a strike from behind.")},
            {"title": _("Dark Pact"),          "body": _(
                "The darkest magic demands the highest price. Dark Pact rips the life "
                "force from the caster's own veins and detonates it in a burst of "
                "shadow energy that consumes all nearby enemies.\n\n"
                "Cost: 10% max HP. Damage: 60 shadow. Radius: 150. "
                "Only those willing to bleed should wield this spell.")},
            {"title": _("Arcane Missiles"),    "body": _(
                "A volley of pure arcane energy that tracks toward the enemy. "
                "Arcane Missiles fires a spread of 5 homing projectiles that each "
                "deal 14 damage, overwhelming foes with sheer volume.\n\n"
                "The missiles do not require perfect aim\u2014they seek, they find, "
                "they destroy.")},
            {"title": _("Mystic Barrier"),     "body": _(
                "A shimmering ward of violet energy that envelops the caster. "
                "Mystic Barrier does not merely block attacks\u2014it turns 30% of "
                "incoming damage back upon the attacker.\n\n"
                "Duration: 5s. The best defense is one that fights back.")},
            {"title": _("Berserker's Rage"),   "body": _(
                "To walk the path of the berserker is to walk the razor's edge. "
                "Berserker's Rage floods the body with raw fury, increasing damage "
                "dealt by 50% while also increasing damage taken by 20%.\n\n"
                "Duration: 8s. Cooldown: 20s. High risk, higher reward.")},
            {"title": _("Chrono Shift"),       "body": _(
                "Time is a river, and those who learn Chrono Shift swim against "
                "the current. The spell slows the world around you, granting "
                "a precious few seconds of accelerated perception.\n\n"
                "Duration: 3s. Nearby enemies at half speed, you strike 25% faster. "
                "Cooldown: 30s.")},
            {"title": _("Dash"),               "body": _(
                "Not all magic comes from ancient tomes. Sometimes it is pure instinct"
                "\u2014the primal urge to survive. Dash propels the user forward in a "
                "burst of speed that blurs the line between movement and teleportation.\n\n"
                "The simplest skill in any adventurer's arsenal, and often the most "
                "useful. Distance is safety. Speed is life.")},
        ]

    def _effects_pages(self):
        return [
            {"title": _("Boon: Regeneration"), "body": _(
                "The body's natural healing, accelerated by magic. Regeneration mends "
                "flesh and bone over time, restoring health with every heartbeat.\n\n"
                "A steady flow of vitality that can mean the difference between survival "
                "and a shallow grave. Those with the Regeneration passive find their "
                "wounds closing even as they fight.")},
            {"title": _("Bane: Poison"),       "body": _(
                "From the fangs of serpents and the blades of the Venomous comes the "
                "creeping death. Poison seeps into the bloodstream, dealing damage over "
                "time as the body fights\u2014and loses\u2014against the toxin.\n\n"
                "A single application may not kill, but it will wear you down, making "
                "every subsequent hit more dangerous. Antidotes are worth their weight "
                "in gold in the swamplands.")},
            {"title": _("Bane: Burn"),         "body": _(
                "Fire remembers. The Burn effect lingers long after the initial blast, "
                "eating away at flesh and armor with equal indifference. Arcanists and "
                "environmental hazards are common sources.\n\n"
                "Unlike poison, burn damage is immediate and aggressive\u2014a race "
                "against time to extinguish the flames before they consume you.")},
            {"title": _("Bane: Confusion"),    "body": _(
                "The Trickster's cruelest gift. Confusion inverts the victim's sense of "
                "direction\u2014up becomes down, left becomes right, and the desperate "
                "attempt to flee may carry you straight into the enemy's arms.\n\n"
                "Duration: ~3s. Trust nothing\u2014not even your own instincts. "
                "The only cure is to wait it out or find a cleansing magic.")},
            {"title": _("Bane: Dizziness"),    "body": _(
                "The world spins. Colors smear. The ground seems to tilt. Dizziness "
                "is a disorienting affliction that muddles vision and balance, making "
                "combat a nauseating ordeal.\n\n"
                "Often paired with Confusion by Tricksters, this effect turns even "
                "simple movements into a struggle against vertigo.")},
            {"title": _("Bane: Slow"),         "body": _(
                "A creeping weight settles into the limbs. Slow reduces movement speed, "
                "making the afflicted easy prey for any attacker. The Brute's slam often "
                "leaves adventurers in this vulnerable state.\n\n"
                "In combat, speed is life. To be slowed is to be marked for death. "
                "Prioritize escape or elimination of the source.")},
            {"title": _("Bane: Freeze & Root"), "body": _(
                "Two faces of the same cursed coin. Freeze locks the body in place, "
                "usually through magical ice, leaving the victim unable to act. Root "
                "achieves the same effect through living vines and tendrils.\n\n"
                "Both are among the most dangerous effects an adventurer can face. "
                "A frozen or rooted fighter is a dead fighter\u2014unless allies or "
                "clever positioning can turn the tide.")},
        ]

    def _guide_pages(self):
        return [
            {"title": _("1. Movement & Navigation"), "body": _(
                "Move with WASD keys. Sprint by holding Shift\u2014but watch your "
                "stamina, shown as the green bar. When it empties, you must wait for "
                "it to recover before sprinting again.\n\n"
                "Navigate the world by walking into doors and map edges to transition "
                "between areas. The terrain varies from open fields to dense forests, "
                "each with its own inhabitants.")},
            {"title": _("2. Combat Basics"), "body": _(
                "Left-click to perform a melee attack in the direction of your cursor. "
                "Each attack has a brief cooldown indicated by a short delay.\n\n"
                "Your health (red bar) and stamina (green bar) are displayed at the "
                "top of the screen. When health reaches zero, you will die and respawn "
                "at your last save point. Death is not the end\u2014but each fall adds "
                "to your death count.")},
            {"title": _("3. Skills & Hotbar"), "body": _(
                "Press the number keys (1-6) to use skills assigned to your hotbar "
                "slots. Skills are learned through the Skill Tree, accessed by "
                "pressing the skill tree button in your inventory.\n\n"
                "Each skill has a cooldown (shown as a dimming icon) and some cost "
                "mana (blue bar). Mana regenerates slowly over time.\n\n"
                "To assign skills to your hotbar, open the Skillbar Edit mode from "
                "your inventory and drag skills onto the desired slots.")},
            {"title": _("4. Inventory & Items"), "body": _(
                "Press TAB or the inventory button to open your inventory. Here you "
                "can manage equipment, consume potions, and inspect your gear.\n\n"
                "Items stack in your inventory. Right-click items to see details. "
                "Drag and drop to rearrange. Equipment slots are at the top of "
                "the inventory panel.\n\n"
                "Potion of Healing restores health. Collect everything\u2014you never "
                "know what might save your life.")},
            {"title": _("5. Crafting & Recipes"), "body": _(
                "Combine ingredients in the crafting grid to create new items, "
                "potions, and equipment. The Recipe Book (accessible from inventory) "
                "shows known recipes.\n\n"
                "To craft, place the required ingredients in the 3\u00d73 crafting grid "
                "in the correct pattern. If the combination is valid, the result "
                "will appear in the output slot.\n\n"
                "Experiment\u2014some recipes must be discovered through trial and error.")},
            {"title": _("6. Leveling & Experience"), "body": _(
                "Defeating enemies grants experience points (XP). When you accumulate "
                "enough XP, you level up, increasing your max HP by 20 and granting "
                "a Skill Tree point.\n\n"
                "Use Skill Tree points to unlock new abilities and passive bonuses. "
                "The Skill Tree is divided into branches: Fire, Ice, Lightning, "
                "Nature, Shadow, and Arcane, plus Keystone passives that grant "
                "game-changing powers.")},
            {"title": _("7. Day & Night Cycle"), "body": _(
                "The world follows a day and night cycle. During the day, visibility "
                "is clear and enemies behave normally. As dusk approaches, shadows "
                "lengthen and the world dims.\n\n"
                "At night, the screen darkens significantly and some enemies may "
                "become more aggressive. Plan your expeditions accordingly\u2014the "
                "darkness is not your ally.")},
            {"title": _("8. Enemies & Threat Assessment"), "body": _(
                "Different enemies require different tactics:\n\n"
                "\u2022 Brutes: Slow but deadly. Dodge their charge and punish recovery.\n"
                "\u2022 Venomous: Avoid their blades. Bring antidotes.\n"
                "\u2022 Arcanists: Close the distance. Vulnerable up close.\n"
                "\u2022 Tricksters: Expect the unexpected. Do not chase\u2014predict.\n"
                "\u2022 Bombers: Stay mobile. Never stand still.\n\n"
                "Use the Bestiary section for full details on each foe.")},
            {"title": _("9. Respeccing & Strategy"), "body": _(
                "Your build matters. Focus on a school of magic or spread your "
                "points for versatility. Keystones like Elemental Mastery reward "
                "combining different elements, while Eternal Fortress makes you "
                "a bulwark of defense.\n\n"
                "If you wish to change your build, visit the appropriate NPC or "
                "use the respec option\u2014though such changes may come at a cost.\n\n"
                "Adapt. Improvise. Overcome.")},
            {"title": _("10. Final Words"), "body": _(
                "The road ahead is long and lined with peril. You will fall. You will "
                "rise. You will face horrors that make your blood run cold\u2014and you "
                "will learn that the real monster is often the one that dwells within.\n\n"
                "But you are not alone. Every adventurer who came before has left their "
                "mark on this world. Their mistakes are your lessons. Their triumphs "
                "are your inheritance.\n\n"
                "Now go. The realm awaits, and there is a story to be written. "
                "Make it a good one.")},
        ]

    def layout(self, screen):
        sw, sh = self._screen_size(screen)
        scale = cfg.ui_scale()
        btn_w = max(1, int(220 * scale))
        btn_h = max(1, int(62 * scale))

        if self._page == "main":
            self.back_btn.rect = pygame.Rect(sw - btn_w - max(20, int(40 * scale)),
                                             sh - btn_h - max(20, int(28 * scale)),
                                             btn_w, btn_h)
        else:
            nav_y = sh - btn_h - max(16, int(24 * scale))
            back_y = nav_y - btn_h - max(4, int(8 * scale))

            self.back_btn.rect = pygame.Rect(max(20, int(30 * scale)), back_y, btn_w, btn_h)
            self.toc_btn.rect = pygame.Rect(max(20, int(30 * scale)) + btn_w + max(8, int(10 * scale)),
                                            back_y, btn_w, btn_h)
            self.prev_btn.rect = pygame.Rect(max(20, int(30 * scale)), nav_y, btn_w, btn_h)
            self.next_btn.rect = pygame.Rect(sw - btn_w - max(20, int(30 * scale)), nav_y, btn_w, btn_h)

        for b in (self.back_btn, self.prev_btn, self.next_btn, self.toc_btn):
            try:
                b._update_text_surface()
            except Exception:
                pass

    def update(self, dt):
        self._anim_time += dt
        self.particles = [p for p in self.particles if p.lifetime > 0]
        for p in self.particles:
            p.update(dt)

    def draw(self, screen):
        self.layout(screen)
        sw, sh = self._screen_size(screen)
        scale = cfg.ui_scale()
        self.update(1 / 60)

        if self._page == "main":
            self._draw_main_page(screen, sw, sh, scale)
        else:
            if self._show_toc:
                self._draw_toc_page(screen, sw, sh, scale)
            else:
                self._draw_content_page(screen, sw, sh, scale)

        for p in self.particles:
            p.draw(screen)

    def _draw_decorated_title(self, screen, rect, theme, scale):
        icon = theme.get("icon", "\u2726")
        pulse = 0.85 + 0.15 * math.sin(self._anim_time * 1.8)
        icolor = tuple(min(255, int(c * pulse)) for c in theme["accent"])
        icon_s = self.font_large.render(icon, True, icolor)
        screen.blit(icon_s, (rect.x + int(20 * scale), rect.y))

    def _draw_main_page(self, screen, sw, sh, scale):
        theme = SECTION_THEMES["main"]
        bg_s = pygame.Surface((sw, sh), pygame.SRCALPHA)
        bg_s.fill((12, 8, 6, 245))
        screen.blit(bg_s, (0, 0))

        box_pad = max(20, int(45 * scale))
        box = pygame.Rect(box_pad, box_pad, sw - 2 * box_pad, sh - 2 * box_pad)
        _draw_ornate_border(screen, box, theme, scale)
        _draw_corner_scroll(screen, box, scale)

        inner = box.inflate(-int(60 * scale), -int(60 * scale))

        icon_s = self.font_ornate.render("\u2726", True, GOLD_BRIGHT)
        icon_pulse = 0.8 + 0.2 * math.sin(self._anim_time * 1.2)
        is2 = pygame.transform.scale(icon_s,
            (int(icon_s.get_width() * icon_pulse), int(icon_s.get_height() * icon_pulse)))
        screen.blit(is2, (inner.x + (inner.width - is2.get_width()) // 2,
                          inner.y + int(5 * scale)))

        title_y = inner.y + int(55 * scale)
        title_s = self.font_large.render(_("The Adventurer's Codex"), True, GOLD_BRIGHT)
        glow = int(80 + 40 * math.sin(self._anim_time * 1.5))
        for ox, oy in [(1,1),(-1,1),(1,-1),(-1,-1),(0,2),(2,0),(0,-2),(-2,0)]:
            gs = self.font_large.render(_("The Adventurer's Codex"), True, (glow, glow//2, 0))
            screen.blit(gs, (inner.x + (inner.width - title_s.get_width()) // 2 + ox,
                             title_y + oy))
        screen.blit(title_s, (inner.x + (inner.width - title_s.get_width()) // 2, title_y))

        deco_y = title_y + title_s.get_height() + int(14 * scale)
        _draw_gold_divider(screen, inner.x + int(40 * scale), deco_y,
                           inner.width - int(80 * scale), scale)

        sub_y = deco_y + int(28 * scale)
        sub_s = self.font_subtitle.render(
            _("An in-game compendium of knowledge"), True, self.ink_light)
        screen.blit(sub_s, (inner.x + (inner.width - sub_s.get_width()) // 2, sub_y))

        btn_start_y = sub_y + sub_s.get_height() + int(35 * scale)
        b_h = max(1, int(92 * scale))
        b_w = max(1, int(400 * scale))
        gap = max(4, int(16 * scale))
        cx = sw // 2

        for i, (label, sublabel, cb, t) in enumerate(self.section_button_data):
            by = btn_start_y + i * (b_h + gap)
            bx = cx - b_w // 2
            br = pygame.Rect(bx, by, b_w, b_h)

            bs = pygame.Surface(br.size, pygame.SRCALPHA)
            c = t["accent"]
            bg_c = (c[0] // 5 + 25, c[1] // 5 + 18, c[2] // 5 + 25, 210)
            bs.fill(bg_c)
            pygame.draw.rect(bs, c, bs.get_rect(), max(1, int(2 * scale)), border_radius=16)
            pygame.draw.rect(bs, GOLD_DARK, bs.get_rect().inflate(-5, -5),
                             max(1, int(1 * scale)), border_radius=12)

            screen.blit(bs, br.topleft)

            icon_s2 = self.font_subtitle.render(t.get("icon", ""), True, GOLD_BRIGHT)
            screen.blit(icon_s2, (bx + int(16 * scale), by + int(10 * scale)))

            lbl = self.font_subtitle.render(label, True, GOLD_BRIGHT)
            sbl = self.font_small.render(sublabel, True, self.ink_light)
            lx = bx + int(56 * scale)
            screen.blit(lbl, (lx, by + int(10 * scale)))
            screen.blit(sbl, (lx, by + int(52 * scale)))

        ver_y = sh - int(42 * scale)
        ver_s = self.font_small.render(
            _("Codex Arcanum \u2014 First Edition"), True, self.ink_light)
        screen.blit(ver_s, ((sw - ver_s.get_width()) // 2, ver_y))

        self.back_btn.draw(screen)

    def _draw_toc_page(self, screen, sw, sh, scale):
        theme = self._theme()
        meta = self._get_meta()
        entries = meta.get("entries", [])

        bg_s = pygame.Surface((sw, sh), pygame.SRCALPHA)
        bg_s.fill((12, 8, 6, 245))
        screen.blit(bg_s, (0, 0))

        box_pad = max(8, int(24 * scale))
        box = pygame.Rect(box_pad, box_pad, sw - 2 * box_pad, sh - 2 * box_pad)
        _draw_ornate_border(screen, box, theme, scale)
        _draw_corner_scroll(screen, box, scale)

        inner = box.inflate(-int(60 * scale), -int(100 * scale))

        icon = theme.get("icon", "")
        title_full = f"{icon}  {meta.get('subtitle', '')}"
        title_s = self.font_title.render(title_full, True, theme["accent"])
        tx = inner.x + (inner.width - title_s.get_width()) // 2
        screen.blit(title_s, (tx, inner.y))

        _draw_gold_divider(screen, inner.x + int(30 * scale),
                           inner.y + title_s.get_height() + int(8 * scale),
                           inner.width - int(60 * scale), scale)

        toc_top = inner.y + title_s.get_height() + int(28 * scale)
        entry_h = max(1, int(44 * scale))
        gap = max(2, int(6 * scale))
        max_visible = (inner.height - (title_s.get_height() + int(28 * scale))) // (entry_h + gap)

        visible_entries = entries[:max_visible]
        body_font = self.font_toc
        self._toc_entry_rects = []

        for i, entry_title in enumerate(visible_entries):
            ey = toc_top + i * (entry_h + gap)
            er = pygame.Rect(inner.x + int(10 * scale), ey, inner.width - int(20 * scale), entry_h)

            ns = pygame.Surface(er.size, pygame.SRCALPHA)
            bg_c = theme["accent"]
            hover = i == self._toc_hover
            if hover:
                ns.fill((bg_c[0] // 4 + 40, bg_c[1] // 4 + 30, bg_c[2] // 4 + 40, 120))
            else:
                ns.fill((bg_c[0] // 6 + 20, bg_c[1] // 6 + 15, bg_c[2] // 6 + 20, 60))
            pygame.draw.rect(ns, GOLD_DARK if not hover else GOLD,
                             ns.get_rect(), max(1, int(1 * scale)), border_radius=8)
            screen.blit(ns, er.topleft)

            num_s = self.font_small.render(f"{i+1}.", True, GOLD_BRIGHT)
            screen.blit(num_s, (er.x + int(10 * scale),
                                er.y + (er.height - num_s.get_height()) // 2))

            ent_s = body_font.render(entry_title, True,
                                     GOLD_BRIGHT if hover else self.ink_color)
            screen.blit(ent_s, (er.x + int(44 * scale),
                                er.y + (er.height - ent_s.get_height()) // 2))

            if hover:
                arrow_s = self.font_small.render("\u2192", True, GOLD_BRIGHT)
                screen.blit(arrow_s, (er.right - arrow_s.get_width() - int(10 * scale),
                                      er.y + (er.height - arrow_s.get_height()) // 2))

            self._toc_entry_rects.append((er, i + 1))

        header_s = self.font_small.render(
            _("Select an entry to read"), True, self.ink_light)
        screen.blit(header_s, (inner.x + (inner.width - header_s.get_width()) // 2,
                               inner.y + inner.height - header_s.get_height() - int(10 * scale)))

        self.back_btn.draw(screen)

    def _draw_content_page(self, screen, sw, sh, scale):
        theme = self._theme()
        pages = self._get_content()
        if not pages:
            return

        page_data = pages[min(self._sub_page, len(pages) - 1)]
        title = page_data.get("title", "")
        body = page_data.get("body", "")
        portrait_style = page_data.get("portrait", None)

        bg_s = pygame.Surface((sw, sh), pygame.SRCALPHA)
        bg_s.fill((12, 8, 6, 245))
        screen.blit(bg_s, (0, 0))

        box_pad = max(8, int(20 * scale))
        box = pygame.Rect(box_pad, box_pad, sw - 2 * box_pad, sh - 2 * box_pad)
        _draw_ornate_border(screen, box, theme, scale)
        _draw_corner_scroll(screen, box, scale)

        inner = box.inflate(-int(50 * scale), -int(80 * scale))

        # ── portrait (right side, bigger) ──
        portrait_size = 0
        portrait_img = None
        portrait_x = 0
        portrait_y = 0
        if portrait_style is not None:
            portrait_size = max(1, int(140 * scale))
            portrait_img = _get_monster_portrait(portrait_style, portrait_size)
            portrait_x = inner.right - portrait_size - int(10 * scale)
            portrait_y = inner.y + int(10 * scale)

        # ── title ──
        title_area_w = inner.width
        if portrait_img is not None:
            title_area_w -= portrait_size + int(24 * scale)

        title_surf = self.font_title.render(title, True, theme["accent"])
        tx = inner.x + (title_area_w - title_surf.get_width()) // 2
        screen.blit(title_surf, (tx, inner.y))

        deco_y = inner.y + title_surf.get_height() + int(6 * scale)
        deco_w = title_area_w if portrait_img is None else title_area_w + portrait_size + int(24 * scale)
        _draw_gold_divider(screen, inner.x + int(10 * scale), deco_y,
                           deco_w - int(20 * scale), scale)

        # ── body text ──
        text_top = deco_y + int(18 * scale)
        text_area_w = inner.width
        if portrait_img is not None:
            text_area_w -= portrait_size + int(24 * scale)
        text_area_h = inner.y + inner.height - text_top

        body_font = self.font_body
        line_h = body_font.get_height() + max(2, int(3 * scale))

        body_lines = _wrap_text(body, body_font, text_area_w)
        available_h = text_area_h - int(40 * scale)
        visible_lines = max(0, available_h // line_h)

        for i in range(visible_lines):
            idx = i
            if idx >= len(body_lines):
                break
            line = body_lines[idx]
            if line.strip() == "":
                continue
            surf = body_font.render(line, True, self.ink_color)
            screen.blit(surf, (inner.x + int(10 * scale), text_top + i * line_h))

        # ── portrait overlay ──
        if portrait_img is not None:
            pulse = 0.7 + 0.3 * math.sin(self._anim_time * 2)
            _draw_portrait_frame(screen, portrait_x, portrait_y, portrait_size, theme, scale, pulse)
            screen.blit(portrait_img, (portrait_x + 4, portrait_y + 4))

            # name label under portrait
            name_s = self.font_small.render(title, True, theme["accent"])
            nx = portrait_x + (portrait_size + 8 - name_s.get_width()) // 2
            screen.blit(name_s, (nx, portrait_y + portrait_size + int(12 * scale)))

        # ── page number ──
        max_p = self._get_max_subpages()
        if max_p > 0:
            page_text = _("Page {}/{}").format(self._sub_page + 1, max_p + 1)
            page_surf = self.font_small.render(page_text, True, self.ink_light)
            px = (sw - page_surf.get_width()) // 2
            screen.blit(page_surf, (px, sh - int(48 * scale)))

        self.back_btn.draw(screen)
        self.toc_btn.draw(screen)
        if max_p > 0:
            if self._sub_page > 0:
                self.prev_btn.draw(screen)
            if self._sub_page < max_p:
                self.next_btn.draw(screen)

    def handle_event(self, event):
        if self._page == "main" and hasattr(self, 'section_button_data'):
            self._handle_main_click(event)
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_btn.rect.collidepoint(event.pos):
                self.back_btn.on_click()
                return
            if self._page != "main":
                if self.toc_btn.rect.collidepoint(event.pos):
                    self.toc_btn.on_click()
                    return
                if self._show_toc:
                    self._handle_toc_click(event)
                    return
                if self.prev_btn.rect.collidepoint(event.pos):
                    self.prev_btn.on_click()
                    return
                if self.next_btn.rect.collidepoint(event.pos):
                    self.next_btn.on_click()
                    return

        if event.type == pygame.MOUSEMOTION and self._show_toc:
            self._toc_hover = -1
            if hasattr(self, '_toc_entry_rects'):
                for er, idx in self._toc_entry_rects:
                    if er.collidepoint(event.pos):
                        self._toc_hover = idx - 1
                        break

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self._show_toc and self._sub_page > 0:
                    self._show_toc = False
                elif self._page != "main":
                    self._build_main_page()
                    self._page_enter_time = pygame.time.get_ticks()
                else:
                    self.app.manager.set_state("pause")
                return
            if event.key == pygame.K_LEFT or event.key == pygame.K_PAGEUP:
                self._prev_page()
                return
            if event.key == pygame.K_RIGHT or event.key == pygame.K_PAGEDOWN:
                self._next_page()
                return
            if event.key == pygame.K_t or event.key == pygame.K_TAB:
                self._toggle_toc()
                return

    def _handle_main_click(self, event):
        scale = cfg.ui_scale()
        sw, sh = self._screen_size()
        b_h = max(1, int(92 * scale))
        b_w = max(1, int(400 * scale))
        gap = max(4, int(16 * scale))
        cx = sw // 2

        box_pad = max(20, int(45 * scale))
        box = pygame.Rect(box_pad, box_pad, sw - 2 * box_pad, sh - 2 * box_pad)
        inner = box.inflate(-int(60 * scale), -int(60 * scale))

        icon_s = self.font_ornate.render("\u2726", True, GOLD_BRIGHT)
        title_y = inner.y + int(55 * scale)
        title_s = self.font_large.render(_("The Adventurer's Codex"), True, GOLD_BRIGHT)
        deco_y = title_y + title_s.get_height() + int(14 * scale)
        sub_y = deco_y + int(28 * scale)
        sub_s = self.font_subtitle.render(_("An in-game compendium of knowledge"), True, self.ink_light)
        btn_start_y = sub_y + sub_s.get_height() + int(35 * scale)

        for i, (label, sublabel, cb, t) in enumerate(self.section_button_data):
            by = btn_start_y + i * (b_h + gap)
            bx = cx - b_w // 2
            br = pygame.Rect(bx, by, b_w, b_h)
            if event.type == pygame.MOUSEBUTTONDOWN and br.collidepoint(event.pos):
                cb()
                return
        if event.type == pygame.MOUSEBUTTONDOWN and self.back_btn.rect.collidepoint(event.pos):
            self.back_btn.on_click()

    def _handle_toc_click(self, event):
        if not hasattr(self, '_toc_entry_rects'):
            return
        for er, page_idx in self._toc_entry_rects:
            if er.collidepoint(event.pos):
                self._sub_page = page_idx
                self._show_toc = False
                self._page_enter_time = pygame.time.get_ticks()
                return
