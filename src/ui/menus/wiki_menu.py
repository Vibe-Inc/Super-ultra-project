import pygame
from typing import TYPE_CHECKING

from src.ui.menus.base import Menu
from src.ui.widgets import Button
import src.config as cfg

if TYPE_CHECKING:
    from src.app import App


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


class WikiMenu(Menu):
    def __init__(self, app: "App"):
        super().__init__(app)
        self._page = "main"
        self._sub_page = 0
        self._scroll_offset = 0
        self._max_scroll = 0
        self.font = cfg.myfont
        self.body_font = cfg.get_font(28)
        self.title_font = cfg.get_font(52)
        self.section_title_font = cfg.get_font(40)
        self.font_color = (50, 30, 10)
        self.paper_color = (250, 240, 215)
        self.border_color = (160, 100, 50)
        self.accent_color = (120, 60, 20)

        self.padding = 40
        self.text_left_pad = 60

        self.buttons = []

        scale = cfg.ui_scale()
        btn_w = max(1, int(280 * scale))
        btn_h = max(1, int(80 * scale))

        self.back_btn = Button(
            pygame.Rect(0, 0, btn_w, btn_h),
            _("BACK"),
            cfg.button_color_SETTINGS_BACK,
            cfg.button_hover_color_SETTINGS_BACK,
            cfg.button_font,
            cfg.text_color,
            cfg.corner_radius,
            on_click=self._go_back
        )

        self.prev_btn = Button(
            pygame.Rect(0, 0, btn_w, btn_h),
            _("<< PREV"),
            cfg.button_color_SETTINGS,
            cfg.button_hover_color_SETTINGS,
            cfg.button_font,
            cfg.text_color,
            cfg.corner_radius,
            on_click=self._prev_page
        )

        self.next_btn = Button(
            pygame.Rect(0, 0, btn_w, btn_h),
            _("NEXT >>"),
            cfg.button_color_SETTINGS,
            cfg.button_hover_color_SETTINGS,
            cfg.button_font,
            cfg.text_color,
            cfg.corner_radius,
            on_click=self._next_page
        )

        self.section_buttons = []

        self._build_main_page()

    def _build_main_page(self):
        self._page = "main"
        self._sub_page = 0
        self._scroll_offset = 0
        self.section_buttons.clear()

        scale = cfg.ui_scale()
        btn_w = max(1, int(460 * scale))
        btn_h = max(1, int(90 * scale))
        cx = cfg.SCREEN_WIDTH // 2

        entries = [
            (_("Bestiary — Foes of the Realm"), self._open_bestiary),
            (_("Magic — Spells of Power"), self._open_magic),
            (_("Alterations — Curse & Blessing"), self._open_effects),
            (_("Guide — The Adventurer's Handbook"), self._open_guide),
        ]

        start_y = int(320 * scale)
        gap = max(4, int(20 * scale))
        for i, (label, cb) in enumerate(entries):
            btn = Button(
                pygame.Rect(cx - btn_w // 2, start_y + i * (btn_h + gap), btn_w, btn_h),
                label,
                cfg.button_color_START,
                cfg.button_hover_color_START,
                cfg.button_font,
                cfg.text_color,
                cfg.corner_radius,
                on_click=cb,
            )
            self.section_buttons.append(btn)

    def _open_bestiary(self):
        self._page = "bestiary"
        self._sub_page = 0
        self._scroll_offset = 0

    def _open_magic(self):
        self._page = "magic"
        self._sub_page = 0
        self._scroll_offset = 0

    def _open_effects(self):
        self._page = "effects"
        self._sub_page = 0
        self._scroll_offset = 0

    def _open_guide(self):
        self._page = "guide"
        self._sub_page = 0
        self._scroll_offset = 0

    def _go_back(self):
        if self._page != "main":
            self._build_main_page()
        else:
            self.app.manager.set_state("pause")

    def _prev_page(self):
        if self._sub_page > 0:
            self._sub_page -= 1
            self._scroll_offset = 0

    def _next_page(self):
        max_p = self._get_max_subpages()
        if self._sub_page < max_p:
            self._sub_page += 1
            self._scroll_offset = 0

    def _get_max_subpages(self):
        pages = self._get_content()
        return max(0, len(pages) - 1)

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

    def _bestiary_pages(self):
        return [
            {
                "title": _("Bestiary: Foes of the Realm"),
                "body": _(
                    "The world beyond the tavern door is no place for the faint of heart. "
                    "Ancient evils stir in the shadows, twisted by powers long forgotten. "
                    "This chapter recounts the creatures that prowl the land, their habits, "
                    "their hungers, and the tales that surround them. Adventurer, steel yourself "
                    "— for knowledge is the sharpest blade."
                ),
            },
            {
                "title": _("The Brute"),
                "body": _(
                    "They say the first Brute was born from a boulder struck by lightning — "
                    "a creature of fury and stone. These hulking warriors patrol the old roads "
                    "with a single purpose: to crush anything that moves.\n\n"
                    "A Brute does not rush. It stalks. It waits. And when the moment is right, "
                    "it charges with the force of an avalanche, shaking the very ground beneath "
                    "your feet. Its slam can shatter shields and leave even the hardiest adventurer "
                    "gasping for air, slowed and broken.\n\n"
                    "Tale tells of a lone mercenary who dodged a Brute's charge thrice in a single "
                    "night. On the fourth attempt, the ground gave way beneath them both. "
                    "The mercenary's boots were found at the edge of the pit the next morning."
                ),
            },
            {
                "title": _("The Venomous"),
                "body": _(
                    "In the swamplands where even the trees have learned to bite, the Venomous "
                    "make their dens. These lithe, green-skinned stalkers move through the mists "
                    "like whispers, their blades dripping with toxin.\n\n"
                    "A single scratch from their weapons will send poison surging through your "
                    "veins — a creeping decay that grows stronger the longer you ignore it. "
                    "They are patient hunters who harry their prey from the shadows, striking "
                    "and fading before the victim can even cry out.\n\n"
                    "Old Kiril the Alchemist once captured a Venomous for study. He spent three "
                    "weeks trying to brew an antidote. He emerged with a tonic that turned his "
                    "hair green and a newfound respect for staying out of the marshes."
                ),
            },
            {
                "title": _("The Arcanist"),
                "body": _(
                    "Magic is a gift, they say. But some gifts come with a price. The Arcanists "
                    "are former students of the arcane who delved too deep into forbidden "
                    "knowledge, their flesh now crackling with barely contained fire.\n\n"
                    "These robed figures hurl bolts of searing flame from a distance, their aim "
                    "uncanny and their patience endless. The wounds they leave do not stop hurting "
                    "— the fire clings to your skin, burning long after the initial blast.\n\n"
                    "It is whispered that the first Arcanist was once a court mage who tried to "
                    "impress a princess with a firework display. The spell backfired spectacularly. "
                    "The princess survived. His dignity did not."
                ),
            },
            {
                "title": _("The Trickster"),
                "body": _(
                    "Beware the laughter in the dark. The Tricksters are capricious horrors that "
                    "delight in confusion and disarray. Dressed in ragged finery, they blink "
                    "through shadows and appear behind you with a blade already swinging.\n\n"
                    "Their touch clouds the mind — suddenly left is right, forward is back, and "
                    "your own feet refuse to obey. Worse still, the world spins around you in "
                    "a dizzying dance that makes even standing still an act of will.\n\n"
                    "A bard once tried to out-charm a Trickster with a witty rhyme. The Trickster "
                    "responded by swapping all the bard's belongs with a sack of potatoes. "
                    "The bard now travels with a potato on his belt as a warning to others."
                ),
            },
            {
                "title": _("The Bomber"),
                "body": _(
                    "Where there is fire, there is the Bomber. These mad engineers carry satchels "
                    "of volatile concoctions and delight in turning the battlefield into a "
                    "cacophony of explosions.\n\n"
                    "They keep their distance, lobbing timed bombs that arc through the air with "
                    "deceptive grace. When the fuse runs out — the world goes red. The blast "
                    "hurled shrapnel and adventurers alike across the field.\n\n"
                    "Legend speaks of a Bomber who tried to invent a silent explosive. "
                    "He succeeded, but was so disappointed by the lack of 'proper drama' "
                    "that he went back to the old recipe. Some people just want to watch "
                    "the world burn — loudly."
                ),
            },
            {
                "title": _("The Stalker & Skirmisher"),
                "body": _(
                    "Not all threats bear exotic names. The Stalker is the most common — "
                    "and perhaps the most dangerous precisely because of it. A hardened warrior "
                    "with grim determination, it tracks its prey with relentless focus, "
                    "remembering where you vanished and searching until it finds you again.\n\n"
                    "The Skirmisher is its swifter cousin, darting in and out of range like a "
                    "mountain gnat. It prefers to circle its prey, testing defenses before "
                    "committing to the kill.\n\n"
                    "Old soldiers say the best way to tell them apart: a Stalker will "
                    "follow you to the ends of the earth. A Skirmisher will beat you there, "
                    "get bored, and leave before you arrive."
                ),
            },
        ]

    def _magic_pages(self):
        return [
            {
                "title": _("Magic: Spells of Power"),
                "body": _(
                    "Magic flows through all things — in the crackle of a campfire, the "
                    "stillness of a frozen lake, the whisper of wind through leaves. "
                    "Those born with the gift can shape this flow into wonders and terrors "
                    "beyond mortal ken.\n\n"
                    "The following pages detail the incantations, gestures, and pacts that "
                    "grant an adventurer command over the elements, the shadows, and the "
                    "very fabric of time itself. Use them wisely."
                ),
            },
            {
                "title": _("Fireball"),
                "body": _(
                    "The quintessence of destructive magic. The Fireball spell compresses "
                    "a spark of elemental flame into a roaring sphere that streaks toward "
                    "its target before erupting in a glorious conflagration.\n\n"
                    "Damage: 28 base (area). Range: 520. Knockback: moderate. "
                    "The blast radius catches all who stand too close, hurling them back "
                    "and leaving scorched earth where they stood.\n\n"
                    "Those who master the Pyromancer's Fury find their fireballs burning "
                    "hotter (25% more damage) and spreading wider (15% larger radius) — "
                    "a true inferno unleashed."
                ),
            },
            {
                "title": _("Flame Shield"),
                "body": _(
                    "A wreath of protective flames that surrounds the caster, turning "
                    "them into a walking pyre. The Flame Shield scorches any foe foolish "
                    "enough to approach, dealing 8 damage per second to all nearby enemies.\n\n"
                    "Duration: 6 seconds. This spell does not prevent damage — it merely "
                    "ensures that anyone who hurts you will share your pain."
                ),
            },
            {
                "title": _("Frost Nova"),
                "body": _(
                    "A desperate cry to the winter winds. Frost Nova sends a razored ring "
                    "of ice expanding outward from the caster, freezing the very air and "
                    "any enemy caught within its reach.\n\n"
                    "Radius: 150. Freeze Duration: 3 seconds. Enemies trapped in ice can "
                    "neither move nor fight — they stand as frozen statues, helpless against "
                    "whatever follows."
                ),
            },
            {
                "title": _("Ice Armor"),
                "body": _(
                    "A cloak of crystalline frost that forms around the caster's body, "
                    "absorbing incoming blows and chilling those who dare to strike. "
                    "The armor can absorb up to 30 damage before shattering.\n\n"
                    "Duration: 8 seconds. Attackers within 80 pixels are slowed by half. "
                    "The slower they are, the easier to avoid their retaliations."
                ),
            },
            {
                "title": _("Glacial Cascade"),
                "body": _(
                    "A focused beam of frozen fury that tears across the battlefield. "
                    "Glacial Cascade sends a torrent of ice shards racing forward, dealing "
                    "35 damage to everything in its path and leaving a crust of frost "
                    "on the survivors.\n\n"
                    "Freeze Duration: 2 seconds. The cascade travels far and wide, "
                    "freezing enemies who thought themselves safely out of reach."
                ),
            },
            {
                "title": _("Chain Lightning"),
                "body": _(
                    "The storm's wrath, captured and directed. Chain Lightning leaps from "
                    "the caster's fingertips to the nearest foe, then arcs to the next, "
                    "and the next, dancing between up to 5 enemies with vengeful fury.\n\n"
                    "Damage: 22 per strike. Range: 550. Chain Range: 180. "
                    "It may not hit as hard as a fireball, but it will never waste its energy "
                    "— every spark finds a target."
                ),
            },
            {
                "title": _("Thunderstrike"),
                "body": _(
                    "A bolt from the blue — literally. Thunderstrike calls a column of "
                    "lightning down from the heavens upon a chosen location, dealing "
                    "catastrophic damage to all beneath it.\n\n"
                    "Damage: 55. Radius: 100. Range: 600. "
                    "The thunder that follows is as much a warning as a eulogy."
                ),
            },
            {
                "title": _("Entangling Roots"),
                "body": _(
                    "The earth remembers the touch of life. Entangling Roots calls forth "
                    "ancient tendrils from the soil that snake toward the target and erupt "
                    "in a thicket of grasping vines.\n\n"
                    "Root Duration: 4 seconds. Radius: 140. Range: 500. "
                    "Enemies caught cannot move — they can only watch as you line up "
                    "the perfect strike."
                ),
            },
            {
                "title": _("Summon Spirit"),
                "body": _(
                    "A bond with the wilds that transcends death. Summon Spirit calls a "
                    "nature spirit from the green realm to fight at your side — a "
                    "flickering wisp of leaves and light that harries your enemies.\n\n"
                    "Spirit Damage: 15. Duration: 10 seconds. The spirit fights "
                    "autonomously, attacking nearby foes and drawing their attention."
                ),
            },
            {
                "title": _("Shadow Step"),
                "body": _(
                    "The shadows are a doorway for those who know the password. Shadow Step "
                    "allows the caster to dissolve into darkness and reappear a short "
                    "distance away, leaving only a whisper and a fading silhouette.\n\n"
                    "Range: 300. Invulnerability: 0.5 seconds after arrival. "
                    "A perfect escape — or a perfect setup for a strike from behind."
                ),
            },
            {
                "title": _("Dark Pact"),
                "body": _(
                    "The darkest magic demands the highest price. Dark Pact rips the life "
                    "force from the caster's own veins and detonates it in a burst of "
                    "shadow energy that consumes all nearby enemies.\n\n"
                    "Cost: 10% of max HP. Damage: 60 shadow. Radius: 150. "
                    "Only those willing to bleed should wield this spell."
                ),
            },
            {
                "title": _("Arcane Missiles"),
                "body": _(
                    "A volley of pure arcane energy that tracks toward the enemy. "
                    "Arcane Missiles fires a spread of 5 homing projectiles that each "
                    "deal 14 damage, overwhelming foes with sheer volume.\n\n"
                    "The missiles do not require perfect aim — they seek, they find, "
                    "they destroy."
                ),
            },
            {
                "title": _("Mystic Barrier"),
                "body": _(
                    "A shimmering ward of violet energy that envelops the caster. "
                    "Mystic Barrier does not merely block attacks — it turns 30% of "
                    "incoming damage back upon the attacker.\n\n"
                    "Duration: 5 seconds. A perfect tool for those who believe the best "
                    "defense is a defense that fights back."
                ),
            },
            {
                "title": _("Berserker's Rage"),
                "body": _(
                    "To walk the path of the berserker is to walk the razor's edge. "
                    "Berserker's Rage floods the body with raw fury, increasing damage "
                    "dealt by 50% while also increasing damage taken by 20%.\n\n"
                    "Duration: 8 seconds. Cooldown: 20 seconds. "
                    "A gambler's skill — high risk, higher reward."
                ),
            },
            {
                "title": _("Chrono Shift"),
                "body": _(
                    "Time is a river, and those who learn Chrono Shift learn to swim "
                    "against the current. The spell slows the world around you, granting "
                    "a precious few seconds of accelerated perception.\n\n"
                    "Duration: 3 seconds. During this time, all nearby enemies move at "
                    "half speed while you strike with 25% faster attacks. "
                    "Cooldown: 30 seconds."
                ),
            },
            {
                "title": _("Dash"),
                "body": _(
                    "Not all magic comes from ancient tomes. Sometimes it is pure instinct — "
                    "the primal urge to survive. Dash propels the user forward in a burst "
                    "of speed that blurs the line between movement and teleportation.\n\n"
                    "The simplest skill in any adventurer's arsenal, and often the most "
                    "useful. Distance is safety. Speed is life."
                ),
            },
        ]

    def _effects_pages(self):
        return [
            {
                "title": _("Alterations: Curse & Blessing"),
                "body": _(
                    "The body is a battlefield where unseen wars are waged. Beyond the "
                    "flash and thunder of direct magic lies a subtler art — the manipulation "
                    "of life force, mind, and movement.\n\n"
                    "Some of these alterations are gifts that knit wounds and bolster courage. "
                    "Others are poisons that rot from within. An adventurer must know both, "
                    "for the difference between a blessing and a curse is often a matter "
                    "of who wields it."
                ),
            },
            {
                "title": _("Boon: Regeneration"),
                "body": _(
                    "The body's natural healing, accelerated by magic. Regeneration mends "
                    "flesh and bone over time, restoring health with every heartbeat.\n\n"
                    "A steady flow of vitality that can mean the difference between survival "
                    "and a shallow grave. Those with the Regeneration passive find their "
                    "wounds closing even as they fight."
                ),
            },
            {
                "title": _("Bane: Poison"),
                "body": _(
                    "From the fangs of serpents and the blades of the Venomous comes the "
                    "creeping death. Poison seeps into the bloodstream, dealing damage over "
                    "time as the body fights — and loses — against the toxin.\n\n"
                    "A single application may not kill, but it will wear you down, making "
                    "every subsequent hit more dangerous. Antidotes are worth their weight "
                    "in gold in the swamplands."
                ),
            },
            {
                "title": _("Bane: Burn"),
                "body": _(
                    "Fire remembers. The Burn effect lingers long after the initial blast, "
                    "eating away at flesh and armor with equal indifference. Arcanists and "
                    "environmental hazards are common sources.\n\n"
                    "Unlike poison, burn damage is immediate and aggressive — a race against "
                    "time to extinguish the flames before they consume you."
                ),
            },
            {
                "title": _("Bane: Confusion"),
                "body": _(
                    "The Trickster's cruelest gift. Confusion inverts the victim's sense of "
                    "direction — up becomes down, left becomes right, and the desperate "
                    "attempt to flee may carry you straight into the enemy's arms.\n\n"
                    "Duration: ~3 seconds. During this time, trust nothing — not even "
                    "your own instincts. The only cure is to wait it out or find a "
                    "cleansing magic."
                ),
            },
            {
                "title": _("Bane: Dizziness"),
                "body": _(
                    "The world spins. Colors smear. The ground seems to tilt. Dizziness "
                    "is a disorienting affliction that muddles vision and balance, making "
                    "combat a nauseating ordeal.\n\n"
                    "Often paired with Confusion by Tricksters, this effect turns even "
                    "simple movements into a struggle against vertigo."
                ),
            },
            {
                "title": _("Bane: Slow"),
                "body": _(
                    "A creeping weight settles into the limbs. Slow reduces movement speed, "
                    "making the afflicted easy prey for any attacker. The Brute's slam often "
                    "leaves adventurers in this vulnerable state.\n\n"
                    "In combat, speed is life. To be slowed is to be marked for death. "
                    "Prioritize escape or elimination of the source."
                ),
            },
            {
                "title": _("Bane: Freeze & Root"),
                "body": _(
                    "Two faces of the same cursed coin. Freeze locks the body in place, "
                    "usually through magical ice, leaving the victim unable to act. Root "
                    "achieves the same effect through living vines and tendrils.\n\n"
                    "Both are among the most dangerous effects an adventurer can face. "
                    "A frozen or rooted fighter is a dead fighter — unless allies or "
                    "clever positioning can turn the tide."
                ),
            },
        ]

    def _guide_pages(self):
        return [
            {
                "title": _("Guide: The Adventurer's Handbook"),
                "body": _(
                    "Welcome, brave soul, to a world of danger and discovery. This guide "
                    "will teach you everything you need to survive — from the first step "
                    "out of town to the final confrontation with the darkness.\n\n"
                    "Read carefully. The realm does not reward the careless."
                ),
            },
            {
                "title": _("1. Movement & Navigation"),
                "body": _(
                    "Move with WASD keys. Sprint by holding Shift — but watch your stamina, "
                    "shown as the green bar. When it empties, you must wait for it to "
                    "recover before sprinting again.\n\n"
                    "Navigate the world by walking into doors and map edges to transition "
                    "between areas. The terrain varies from open fields to dense forests, "
                    "each with its own inhabitants."
                ),
            },
            {
                "title": _("2. Combat Basics"),
                "body": _(
                    "Left-click to perform a melee attack in the direction of your cursor. "
                    "Each attack has a brief cooldown indicated by a short delay.\n\n"
                    "Your health (red bar) and stamina (green bar) are displayed at the "
                    "top of the screen. When health reaches zero, you will die and respawn "
                    "at your last save point. Death is not the end — but each fall adds "
                    "to your death count."
                ),
            },
            {
                "title": _("3. Skills & Hotbar"),
                "body": _(
                    "Press the number keys (1-6) to use skills assigned to your hotbar "
                    "slots. Skills are learned through the Skill Tree, accessed by "
                    "pressing the skill tree button in your inventory.\n\n"
                    "Each skill has a cooldown (shown as a dimming icon) and some cost "
                    "mana (blue bar). Mana regenerates slowly over time.\n\n"
                    "To assign skills to your hotbar, open the Skillbar Edit mode from "
                    "your inventory and drag skills onto the desired slots."
                ),
            },
            {
                "title": _("4. Inventory & Items"),
                "body": _(
                    "Press TAB or the inventory button to open your inventory. Here you "
                    "can manage equipment, consume potions, and inspect your gear.\n\n"
                    "Items stack in your inventory. Right-click items to see details. "
                    "Drag and drop to rearrange. Equipment slots are at the top of "
                    "the inventory panel.\n\n"
                    "Potion of Healing restores health. Other consumables provide "
                    "temporary buffs or cure ailments. Collect everything — you never "
                    "know what might save your life."
                ),
            },
            {
                "title": _("5. Crafting & Recipes"),
                "body": _(
                    "Combine ingredients in the crafting grid to create new items, "
                    "potions, and equipment. The Recipe Book (accessible from inventory) "
                    "shows known recipes.\n\n"
                    "To craft, place the required ingredients in the 3x3 crafting grid "
                    "in the correct pattern. If the combination is valid, the result "
                    "will appear in the output slot.\n\n"
                    "Experiment with different combinations — some recipes must be "
                    "discovered through trial and error."
                ),
            },
            {
                "title": _("6. Leveling & Experience"),
                "body": _(
                    "Defeating enemies grants experience points (XP). When you accumulate "
                    "enough XP, you level up, increasing your max HP by 20 and granting "
                    "a Skill Tree point.\n\n"
                    "Use Skill Tree points to unlock new abilities and passive bonuses. "
                    "The Skill Tree is divided into branches: Fire, Ice, Lightning, "
                    "Nature, Shadow, and Arcane, plus Keystone passives that grant "
                    "game-changing powers."
                ),
            },
            {
                "title": _("7. Day & Night Cycle"),
                "body": _(
                    "The world follows a day and night cycle. During the day, visibility "
                    "is clear and enemies behave normally. As dusk approaches, shadows "
                    "lengthen and the world dims.\n\n"
                    "At night, the screen darkens significantly and some enemies may "
                    "become more aggressive. Plan your expeditions accordingly — the "
                    "darkness is not your ally."
                ),
            },
            {
                "title": _("8. Enemies & Threat Assessment"),
                "body": _(
                    "Different enemies require different tactics:\n\n"
                    "- Brutes: Slow but deadly. Dodge their charge and punish recovery.\n"
                    "- Venomous: Avoid their blades. Bring antidotes.\n"
                    "- Arcanists: Close the distance. They are vulnerable up close.\n"
                    "- Tricksters: Expect the unexpected. Do not chase — predict.\n"
                    "- Bombers: Stay mobile. Never stand still.\n\n"
                    "Use the Bestiary section of this guide for full details on each foe."
                ),
            },
            {
                "title": _("9. Respeccing & Strategy"),
                "body": _(
                    "Your build matters. Focus on a school of magic or spread your "
                    "points for versatility. Keystones like Elemental Mastery reward "
                    "combining different elements, while Eternal Fortress makes you "
                    "a bulwark of defense.\n\n"
                    "If you wish to change your build, visit the appropriate NPC or "
                    "use the respec option — though such changes may come at a cost.\n\n"
                    "Remember: the best strategy is the one that keeps you alive. "
                    "Adapt. Improvise. Overcome."
                ),
            },
            {
                "title": _("10. Final Words"),
                "body": _(
                    "The road ahead is long and lined with peril. You will fall. You will "
                    "rise. You will face horrors that make your blood run cold — and you "
                    "will learn that the real monster is often the one that dwells within.\n\n"
                    "But you are not alone. Every adventurer who came before has left their "
                    "mark on this world. Their mistakes are your lessons. Their triumphs "
                    "are your inheritance.\n\n"
                    "Now go. The realm awaits, and there is a story to be written. "
                    "Make it a good one."
                ),
            },
        ]

    def layout(self, screen):
        sw, sh = self._screen_size(screen)
        scale = cfg.ui_scale()
        btn_w = max(1, int(280 * scale))
        btn_h = max(1, int(80 * scale))

        if self._page == "main":
            cx = sw // 2
            b_w = max(1, int(460 * scale))
            b_h = max(1, int(90 * scale))
            gap = max(4, int(20 * scale))
            start_y = int(sh * 0.30)
            for i, btn in enumerate(self.section_buttons):
                btn.rect = pygame.Rect(cx - b_w // 2, start_y + i * (b_h + gap), b_w, b_h)
                try:
                    btn._update_text_surface()
                except Exception:
                    pass

            self.back_btn.rect = pygame.Rect(sw - int(440 * scale), sh - int(130 * scale), btn_w, btn_h)
            try:
                self.back_btn._update_text_surface()
            except Exception:
                pass
        else:
            nav_y = sh - int(130 * scale)
            back_y = nav_y - btn_h - max(4, int(10 * scale))

            self.back_btn.rect = pygame.Rect(max(20, int(60 * scale)), back_y, btn_w, btn_h)
            try:
                self.back_btn._update_text_surface()
            except Exception:
                pass

            max_p = self._get_max_subpages()

            self.prev_btn.rect = pygame.Rect(max(20, int(60 * scale)), nav_y, btn_w, btn_h)
            self.next_btn.rect = pygame.Rect(sw - btn_w - max(20, int(60 * scale)), nav_y, btn_w, btn_h)
            try:
                self.prev_btn._update_text_surface()
            except Exception:
                pass
            try:
                self.next_btn._update_text_surface()
            except Exception:
                pass

    def draw(self, screen):
        self.layout(screen)
        sw, sh = self._screen_size(screen)

        if self._page == "main":
            self._draw_main_page(screen, sw, sh)
        else:
            self._draw_content_page(screen, sw, sh)

    def _draw_main_page(self, screen, sw, sh):
        scale = cfg.ui_scale()

        box_pad = max(20, int(40 * scale))
        box = pygame.Rect(box_pad, box_pad, sw - 2 * box_pad, sh - 2 * box_pad)
        pygame.draw.rect(screen, self.paper_color, box, border_radius=30)
        pygame.draw.rect(screen, self.border_color, box, max(3, int(6 * scale)), border_radius=30)

        title_surf = self.title_font.render(_("The Adventurer's Codex"), True, self.accent_color)
        tx = (sw - title_surf.get_width()) // 2
        screen.blit(title_surf, (tx, int(120 * scale)))

        sub_surf = self.body_font.render(_("An in-game compendium of knowledge"), True, self.font_color)
        stx = (sw - sub_surf.get_width()) // 2
        screen.blit(sub_surf, (stx, int(200 * scale)))

        for btn in self.section_buttons:
            btn.draw(screen)

        self.back_btn.draw(screen)

    def _draw_content_page(self, screen, sw, sh):
        scale = cfg.ui_scale()
        pages = self._get_content()
        if not pages:
            return

        page_data = pages[min(self._sub_page, len(pages) - 1)]
        title = page_data.get("title", "")
        body = page_data.get("body", "")

        box_pad = max(8, int(20 * scale))
        box = pygame.Rect(box_pad, box_pad, sw - 2 * box_pad, sh - 2 * box_pad)
        pygame.draw.rect(screen, self.paper_color, box, border_radius=30)
        pygame.draw.rect(screen, self.border_color, box, max(3, int(6 * scale)), border_radius=30)

        inner = box.inflate(-int(60 * scale), -int(100 * scale))

        title_surf = self.section_title_font.render(title, True, self.accent_color)
        tx = inner.x + (inner.width - title_surf.get_width()) // 2
        screen.blit(title_surf, (tx, inner.y))

        body_lines = _wrap_text(body, self.body_font, inner.width)
        line_h = self.body_font.get_height() + max(2, int(4 * scale))
        y_start = inner.y + title_surf.get_height() + max(8, int(16 * scale))
        text_bottom_margin = int(60 * scale)
        available_text_height = inner.height - (title_surf.get_height() + max(8, int(16 * scale))) - text_bottom_margin
        visible_lines = max(0, available_text_height // line_h)

        for i in range(visible_lines):
            idx = i + self._scroll_offset
            if idx >= len(body_lines):
                break
            line = body_lines[idx]
            if line.strip() == "":
                y_start += max(6, int(10 * scale))
                continue
            surf = self.body_font.render(line, True, self.font_color)
            screen.blit(surf, (inner.x, y_start))
            y_start += line_h

        max_p = self._get_max_subpages()
        page_text = _("Page {}/{}").format(self._sub_page + 1, max_p + 1)
        page_surf = self.body_font.render(page_text, True, self.font_color)
        px = (sw - page_surf.get_width()) // 2
        screen.blit(page_surf, (px, sh - int(90 * scale)))

        self.back_btn.draw(screen)
        if max_p > 0:
            if self._sub_page > 0:
                self.prev_btn.draw(screen)
            if self._sub_page < max_p:
                self.next_btn.draw(screen)

    def handle_event(self, event):
        if self._page == "main":
            for btn in self.section_buttons:
                if event.type == pygame.MOUSEBUTTONDOWN and btn.rect.collidepoint(event.pos):
                    btn.on_click()
                    return
            if event.type == pygame.MOUSEBUTTONDOWN and self.back_btn.rect.collidepoint(event.pos):
                self.back_btn.on_click()
                return
        else:
            if event.type == pygame.MOUSEBUTTONDOWN and self.back_btn.rect.collidepoint(event.pos):
                self.back_btn.on_click()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and self.prev_btn.rect.collidepoint(event.pos):
                self.prev_btn.on_click()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and self.next_btn.rect.collidepoint(event.pos):
                self.next_btn.on_click()
                return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self._page != "main":
                    self._build_main_page()
                else:
                    self.app.manager.set_state("pause")
                return
            if event.key == pygame.K_LEFT or event.key == pygame.K_PAGEUP:
                self._prev_page()
                return
            if event.key == pygame.K_RIGHT or event.key == pygame.K_PAGEDOWN:
                self._next_page()
                return
