import math
import random
import pygame
from typing import TYPE_CHECKING

from src.ui.menus.base import Menu
from src.ui.widgets import Button
import src.config as cfg
from src.core.logger import logger

if TYPE_CHECKING:
    from src.app import App


class SkillbarMenu(Menu):
    """
    Skillbar editor with a single-skill book and a 6-slot active bar.
    Redesigned with stunning animations: glowing neon borders, particle effects,
    smooth hover animations, gradient cards, and pulsing active slots.
    """
    
    # Neon color themes for skill elements
    NEON_THEMES = {
        "fire": {"primary": (255, 80, 40), "glow": (255, 120, 60), "accent": (255, 200, 100)},
        "ice": {"primary": (60, 140, 255), "glow": (100, 180, 255), "accent": (180, 220, 255)},
        "lightning": {"primary": (255, 220, 50), "glow": (255, 240, 100), "accent": (255, 255, 180)},
        "nature": {"primary": (80, 200, 100), "glow": (120, 240, 140), "accent": (180, 255, 180)},
        "shadow": {"primary": (160, 80, 220), "glow": (200, 120, 255), "accent": (220, 180, 255)},
        "arcane": {"primary": (220, 80, 180), "glow": (255, 120, 220), "accent": (255, 180, 240)},
        "default": {"primary": (100, 140, 200), "glow": (140, 180, 240), "accent": (200, 220, 255)},
    }
    
    def __init__(self, app: "App"):
        super().__init__(app)
        self.bar_slots_count = 6
        self.storage_slots_count = 1
        self.panel_margin = max(18, int(24 * cfg.ui_scale()))
        self.grid_gap = max(6, int(8 * cfg.ui_scale()))
        self.sidebar_width = max(280, int(340 * cfg.ui_scale()))
        self.slot_size = 48

        self.sidebar_rect = pygame.Rect(0, 0, 0, 0)
        self.storage_grid_rect = pygame.Rect(0, 0, 0, 0)
        self.bar_rect = pygame.Rect(0, 0, 0, 0)
        self.storage_slot_rects: list[pygame.Rect] = []
        self.bar_slot_rects: list[pygame.Rect] = []

        self.title_font = cfg.get_font(max(16, int(34 * cfg.ui_scale())))
        self.section_font = cfg.get_font(max(16, int(26 * cfg.ui_scale())))
        self.small_font = cfg.get_font(max(14, int(20 * cfg.ui_scale())))

        exit_width = max(120, int(160 * cfg.ui_scale()))
        exit_height = max(44, int(52 * cfg.ui_scale()))
        self.exit_button = Button(
            pygame.Rect(0, 0, exit_width, exit_height),
            _("EXIT"),
            (110, 70, 70),
            (150, 95, 95),
            cfg.button_font,
            cfg.text_color,
            cfg.corner_radius,
            on_click=self.exit_menu,
        )
        self.buttons = [self.exit_button]

        self.drag_payload = None
        self.drag_offset = (0, 0)
        
        # Animation state
        self.animation_time = 0.0
        self.particles: list[dict] = []
        self._init_particles()
        
        # Hover animation state per slot
        self.bar_hover_anim: list[float] = [0.0] * self.bar_slots_count
        self.storage_hover_anim: list[float] = [0.0] * self.storage_slots_count
        
        # Entrance animation
        self.entrance_progress = 0.0
        self.entrance_active = True
        self.slot_entrance_delays: list[float] = []
        
        # Drag trail particles
        self.drag_trail: list[dict] = []
        
        # Glow pulse for active bar
        self.bar_glow_phase = 0.0
        
        # Drop zone highlight
        self.drop_highlight_alpha = 0.0
        self.drop_highlight_target = 0.0
        
        # Hovered skill for sidebar description
        self.hovered_skill = None
        
        # Cached gradient surfaces
        self._gradient_cache = {}
    
    def _init_particles(self):
        """Initialize floating particles for ambient background effect."""
        self.particles = []
        for _ in range(45):
            self.particles.append({
                "x": random.uniform(0, 1),
                "y": random.uniform(0, 1),
                "size": random.uniform(1.5, 4),
                "speed_x": random.uniform(-0.02, 0.02),
                "speed_y": random.uniform(-0.015, -0.005),
                "alpha": random.uniform(0.2, 0.6),
                "pulse_speed": random.uniform(0.8, 2.5),
                "color": random.choice([
                    (80, 120, 200), (120, 80, 180), (180, 120, 80), 
                    (80, 180, 140), (140, 100, 200), (100, 160, 180)
                ]),
            })
    
    def _update_animations(self, dt):
        """Update all animation states."""
        self.animation_time += dt
        self.bar_glow_phase += dt * 2.0
        
        # Update entrance animation
        if self.entrance_active:
            self.entrance_progress += dt * 1.5
            if self.entrance_progress >= 1.0:
                self.entrance_progress = 1.0
                self.entrance_active = False
        
        # Update particles
        for p in self.particles:
            p["x"] += p["speed_x"] * dt
            p["y"] += p["speed_y"] * dt
            # Wrap around
            if p["y"] < -0.05:
                p["y"] = 1.05
                p["x"] = random.uniform(0, 1)
            if p["x"] < -0.05:
                p["x"] = 1.05
            elif p["x"] > 1.05:
                p["x"] = -0.05
        
        # Update hover animations
        mouse_pos = pygame.mouse.get_pos()
        for i, rect in enumerate(self.bar_slot_rects):
            is_hovered = rect.collidepoint(mouse_pos)
            target = 1.0 if is_hovered else 0.0
            self.bar_hover_anim[i] += (target - self.bar_hover_anim[i]) * min(1.0, dt * 8.0)
        
        for i, rect in enumerate(self.storage_slot_rects):
            is_hovered = rect.collidepoint(mouse_pos)
            target = 1.0 if is_hovered else 0.0
            self.storage_hover_anim[i] += (target - self.storage_hover_anim[i]) * min(1.0, dt * 8.0)
        
        # Update drop highlight
        self.drop_highlight_alpha += (self.drop_highlight_target - self.drop_highlight_alpha) * min(1.0, dt * 6.0)
        
        # Track hovered skill for sidebar description
        self.hovered_skill = None
        skillbook, skillbar = self._sync_state_to_character()
        if skillbook is None:
            skillbook, skillbar = self._skillbook()
        storage_items = self._storage_items(skillbook, skillbar) if skillbook else []
        for i, rect in enumerate(self.bar_slot_rects):
            if rect.collidepoint(mouse_pos):
                if i < len(skillbar) and skillbar[i] is not None:
                    self.hovered_skill = skillbar[i]
                break
        if self.hovered_skill is None:
            for i, rect in enumerate(self.storage_slot_rects):
                if rect.collidepoint(mouse_pos):
                    if i < len(storage_items) and storage_items[i] is not None:
                        self.hovered_skill = storage_items[i]
                    break
        
        # Update drag trail
        if self.drag_payload:
            mx, my = pygame.mouse.get_pos()
            # Add trail particle
            if random.random() < 0.6:
                self.drag_trail.append({
                    "x": mx + random.uniform(-8, 8),
                    "y": my + random.uniform(-8, 8),
                    "size": random.uniform(3, 7),
                    "life": 0.5,
                    "max_life": 0.5,
                    "color": self.drag_payload["skill"].get("color", (100, 140, 200)),
                })
        
        # Update trail particles
        to_remove = []
        for trail in self.drag_trail:
            trail["life"] -= dt
            if trail["life"] <= 0:
                to_remove.append(trail)
        for t in to_remove:
            if t in self.drag_trail:
                self.drag_trail.remove(t)

    def _get_skill_theme(self, skill):
        """Get the neon theme for a skill based on its properties."""
        if skill is None:
            return self.NEON_THEMES["default"]
        
        skill_id = skill.get("skill_id", "").lower()
        name = skill.get("name", "").lower()
        color = skill.get("color", (100, 140, 200))
        
        # Try to match by skill_id or name
        for theme_name, theme in self.NEON_THEMES.items():
            if theme_name in skill_id or theme_name in name:
                return theme
        
        # Match by color similarity
        best_match = "default"
        best_score = 0
        for theme_name, theme in self.NEON_THEMES.items():
            primary = theme["primary"]
            # Simple color distance
            score = sum(abs(a - b) for a, b in zip(color, primary))
            if score < best_score or best_score == 0:
                best_score = score
                best_match = theme_name
        
        return self.NEON_THEMES.get(best_match, self.NEON_THEMES["default"])

    def _draw_glowing_rect(self, surface, rect, color, glow_color, glow_intensity=1.0, border_radius=12):
        """Draw a rectangle with animated neon glow effect."""
        t = self.animation_time
        
        # Pulsing glow
        pulse = (math.sin(t * 2.5) + 1.0) * 0.5
        glow_alpha = int(40 + 30 * pulse * glow_intensity)
        
        # Draw outer glow layers
        for offset in range(4, 0, -1):
            glow_rect = rect.inflate(offset * 2, offset * 2)
            alpha = glow_alpha // (offset + 1)
            glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            gc = (*glow_color, alpha)
            pygame.draw.rect(glow_surf, gc, glow_surf.get_rect(), border_radius=border_radius + offset)
            surface.blit(glow_surf, glow_rect.topleft)
        
        # Draw main rectangle
        pygame.draw.rect(surface, color, rect, border_radius=border_radius)
        
        # Draw bright border
        border_alpha = int(180 + 75 * pulse * glow_intensity)
        border_color = tuple(min(255, int(c * 1.3)) for c in glow_color)
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=border_radius)

    def _draw_animated_card(self, surface, rect, skill, hover_anim, empty_label, slot_index=0):
        """Draw a skill card with hover animation and glow effects."""
        t = self.animation_time
        
        # Calculate scale from hover animation
        scale = 1.0 + hover_anim * 0.08
        scaled_rect = rect.inflate(
            int(rect.width * (scale - 1.0)),
            int(rect.height * (scale - 1.0))
        )
        
        if skill is None:
            # Empty slot with subtle animation
            pulse = (math.sin(t * 1.5 + slot_index * 0.5) + 1.0) * 0.5
            base_color = (45 + int(10 * pulse), 45 + int(10 * pulse), 52 + int(10 * pulse))
            border_color = (100 + int(40 * pulse), 100 + int(40 * pulse), 110 + int(40 * pulse))
            
            pygame.draw.rect(surface, base_color, scaled_rect, border_radius=12)
            pygame.draw.rect(surface, border_color, scaled_rect, 2, border_radius=12)
            
            # Animated empty label
            label_alpha = int(140 + 60 * pulse)
            label = self.section_font.render(empty_label, True, (label_alpha, label_alpha, label_alpha + 10))
            surface.blit(label, label.get_rect(center=scaled_rect.center))
            return
        
        # Skill card with theme
        theme = self._get_skill_theme(skill)
        fill = skill.get("color", theme["primary"])
        accent = skill.get("accent", theme["accent"])
        glow = theme["glow"]
        
        # Hover glow effect
        if hover_anim > 0.01:
            glow_intensity = hover_anim
            for offset in range(3, 0, -1):
                glow_rect = scaled_rect.inflate(offset * 2, offset * 2)
                alpha = int(50 * glow_intensity) // offset
                glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                gc = (*glow, alpha)
                pygame.draw.rect(glow_surf, gc, glow_surf.get_rect(), border_radius=14 + offset)
                surface.blit(glow_surf, glow_rect.topleft)
        
        # Gradient fill (top lighter, bottom darker)
        grad_surf = pygame.Surface(scaled_rect.size, pygame.SRCALPHA)
        top_color = tuple(min(255, c + 30) for c in fill)
        bottom_color = tuple(max(0, c - 20) for c in fill)
        for y in range(scaled_rect.height):
            ratio = y / max(1, scaled_rect.height)
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            pygame.draw.line(grad_surf, (r, g, b), (0, y), (scaled_rect.width, y))
        
        # Create rounded mask
        mask_surf = pygame.Surface(scaled_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask_surf, (255, 255, 255, 255), mask_surf.get_rect(), border_radius=12)
        grad_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        # Draw text directly on gradient surface (no shadow/duplication)
        name = self.small_font.render(skill["name"], True, (255, 255, 255))
        name_pos = name.get_rect(center=(scaled_rect.width // 2, scaled_rect.height // 2 - 5))
        grad_surf.blit(name, name_pos)
        
        # Skill ID label
        skill_id = skill.get("skill_id", "")
        if skill_id:
            ident = self.small_font.render(skill_id.replace("_", " ").upper(), True, (200, 200, 210))
            ident_pos = ident.get_rect(center=(scaled_rect.width // 2, scaled_rect.height // 2 + 13))
            grad_surf.blit(ident, ident_pos)
        
        # Apply shimmer effect to gradient surface
        shimmer_pos = (t * 100 + slot_index * 50) % (scaled_rect.width + 100) - 50
        for x in range(max(0, int(shimmer_pos) - 15), min(scaled_rect.width, int(shimmer_pos) + 15)):
            if 0 <= x < scaled_rect.width:
                dist = abs(x - shimmer_pos)
                alpha = max(0, min(100, int(50 * (1 - dist / 15))))
                for y in range(scaled_rect.height):
                    pixel = grad_surf.get_at((x, y))
                    if pixel[3] > 0:  # Only modify visible pixels
                        new_r = min(255, pixel[0] + alpha)
                        new_g = min(255, pixel[1] + alpha)
                        new_b = min(255, pixel[2] + alpha)
                        grad_surf.set_at((x, y), (new_r, new_g, new_b, pixel[3]))
        
        surface.blit(grad_surf, scaled_rect.topleft)
        
        # Border with pulse
        pulse = (math.sin(t * 3.0 + slot_index) + 1.0) * 0.5
        border_brightness = 0.7 + 0.3 * pulse + 0.3 * hover_anim
        border_color = tuple(min(255, int(c * border_brightness)) for c in accent)
        pygame.draw.rect(surface, border_color, scaled_rect, 2, border_radius=12)

    def _draw_particle_background(self, surface, rect):
        """Draw animated particle background within a rect."""
        t = self.animation_time
        
        for p in self.particles:
            px = int(rect.x + p["x"] * rect.width)
            py = int(rect.y + p["y"] * rect.height)
            
            if not rect.collidepoint((px, py)):
                continue
            
            pulse = (math.sin(t * p["pulse_speed"]) + 1.0) * 0.5
            alpha = p["alpha"] * (0.5 + 0.5 * pulse)
            size = p["size"] * (0.8 + 0.4 * pulse)
            
            r, g, b = p["color"]
            color = (int(r * alpha), int(g * alpha), int(b * alpha))
            
            pygame.draw.circle(surface, color, (px, py), max(1, int(size)))

    def _draw_drag_trail(self, surface):
        """Draw particle trail behind dragged skill."""
        for trail in self.drag_trail:
            alpha = int(200 * (trail["life"] / trail["max_life"]))
            size = trail["size"] * (trail["life"] / trail["max_life"])
            color = trail["color"]
            
            # Glow
            glow_surf = pygame.Surface((int(size * 4), int(size * 4)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*color, alpha // 3), (int(size * 2), int(size * 2)), int(size * 2))
            surface.blit(glow_surf, (int(trail["x"] - size * 2), int(trail["y"] - size * 2)))
            
            # Core
            pygame.draw.circle(surface, color, (int(trail["x"]), int(trail["y"])), max(1, int(size)))

    def _character(self):
        gameplay_state = getattr(getattr(self.app, "manager", None), "states", {}).get("gameplay") if hasattr(self.app, "manager") else None
        return getattr(gameplay_state, "character", None)

    def _skillbook(self):
        character = self._character()
        if character is not None and hasattr(character, "skillbook"):
            if not hasattr(character, "skillbar"):
                character.skillbar = [None for _ in range(self.bar_slots_count)]
            return character.skillbook, character.skillbar

        if not hasattr(self, "_fallback_skillbook"):
            self._fallback_skillbook = [
                {
                    "skill_id": "dash",
                    "name": _("Dash"),
                    "description": _("Quick burst of movement"),
                    "color": (86, 132, 186),
                    "accent": (220, 235, 255),
                }
            ]
            self._fallback_skillbar = [None for _ in range(self.bar_slots_count)]
        return self._fallback_skillbook, self._fallback_skillbar

    def _storage_items(self, skillbook: list[dict], skillbar: list[dict | None]):
        active_skill_ids = {
            skill.get("skill_id")
            for skill in skillbar
            if skill is not None
        }
        return [skill for skill in skillbook if skill.get("skill_id") not in active_skill_ids]

    def _slot_at_position(self, position: tuple[int, int]):
        for index, slot_rect in enumerate(self.bar_slot_rects):
            if slot_rect.collidepoint(position):
                return ("bar", 0, index)

        for index, slot_rect in enumerate(self.storage_slot_rects):
            if slot_rect.collidepoint(position):
                return ("storage", 0, index)

        return None

    def _draw_card(self, surface: pygame.Surface, rect: pygame.Rect, skill: dict | None, *, empty_label: str = "+"):
        if skill is None:
            pygame.draw.rect(surface, (55, 55, 62), rect, border_radius=10)
            pygame.draw.rect(surface, (140, 140, 150), rect, 2, border_radius=10)
            label = self.section_font.render(empty_label, True, (175, 175, 180))
            surface.blit(label, label.get_rect(center=rect.center))
            return

        fill = skill.get("color", (80, 100, 140))
        accent = skill.get("accent", (220, 220, 230))
        pygame.draw.rect(surface, fill, rect, border_radius=10)
        pygame.draw.rect(surface, accent, rect, 2, border_radius=10)
        name = self.small_font.render(skill["name"], True, (255, 255, 255))
        surface.blit(name, name.get_rect(center=(rect.centerx, rect.centery - 5)))
        skill_id = skill.get("skill_id", "")
        if skill_id:
            ident = self.small_font.render(skill_id.replace("_", " ").upper(), True, (235, 235, 235))
            surface.blit(ident, ident.get_rect(center=(rect.centerx, rect.centery + 13)))

    def _sync_state_to_character(self):
        character = self._character()
        if character is None:
            return None, None

        if not hasattr(character, "skillbook"):
            character.skillbook = []
        if not hasattr(character, "skillbar") or len(character.skillbar) != self.bar_slots_count:
            character.skillbar = [None for _ in range(self.bar_slots_count)]
        return character.skillbook, character.skillbar

    def _on_drop(self, source, target):
        skillbook, skillbar = self._sync_state_to_character()
        if skillbook is None:
            skillbook, skillbar = self._skillbook()
        storage_items = self._storage_items(skillbook, skillbar)

        source_area, source_index = source
        target_area, target_index = target

        if source_area == "bar":
            if target_area == "bar":
                if source_index == target_index:
                    return
                skillbar[source_index], skillbar[target_index] = skillbar[target_index], skillbar[source_index]
            elif target_area == "storage":
                skillbar[source_index] = None
            return

        if source_area == "storage":
            if not storage_items or target_area != "bar":
                return
            source_skill = storage_items[source_index]
            if skillbar[target_index] is source_skill:
                return
            skillbar[target_index] = source_skill

    def exit_menu(self):
        # Ensure any open player inventory windows are properly removed
        try:
            self.app.INV_manager._return_held_item()
            # mark as closed
            self.app.INV_manager.player_inventory_opened = False

            # If the gameplay state exists, remove its inventory panels from active list
            gameplay = getattr(getattr(self.app, "manager", None), "states", {}).get("gameplay")
            if gameplay:
                try:
                    self.app.INV_manager.remove_active_inventory(getattr(gameplay, "MAIN_player_inv", None))
                except Exception:
                    pass
                try:
                    self.app.INV_manager.remove_active_inventory(getattr(gameplay, "PLAYER_inventory_equipment", None))
                except Exception:
                    pass
        except Exception:
            pass

        self.app.manager.set_state("gameplay")

    def layout(self, screen: pygame.Surface):
        skillbook, skillbar = self._skillbook()
        storage_items = self._storage_items(skillbook, skillbar)
        self.storage_slots_count = max(1, len(storage_items))

        sw, sh = self._screen_size(screen)
        margin = self.panel_margin
        sidebar_width = min(self.sidebar_width, max(280, sw // 4))
        sidebar_x = sw - sidebar_width - margin
        self.sidebar_rect = pygame.Rect(sidebar_x, margin, sidebar_width, sh - margin * 2)

        left_width = max(320, sidebar_x - margin * 2)

        storage_size = min(
            54,
            max(34, (left_width - self.grid_gap * (self.storage_slots_count + 1)) // self.storage_slots_count),
            max(34, int((sh * 0.28 - self.grid_gap * 2))),
        )
        bar_size = min(72, max(42, storage_size + 4))

        storage_total_w = storage_size * self.storage_slots_count + self.grid_gap * (self.storage_slots_count + 1)
        storage_total_h = storage_size + self.grid_gap * 2
        storage_x = margin + max(0, (left_width - storage_total_w) // 2)
        storage_y = sh - margin - storage_total_h
        self.storage_grid_rect = pygame.Rect(storage_x - self.grid_gap, storage_y - self.grid_gap, storage_total_w, storage_total_h)

        bar_total_w = bar_size * self.bar_slots_count + self.grid_gap * (self.bar_slots_count + 1)
        bar_x = margin + max(0, (left_width - bar_total_w) // 2)
        bar_y = margin + 84
        self.bar_rect = pygame.Rect(bar_x - self.grid_gap, bar_y - self.grid_gap, bar_total_w, bar_size + self.grid_gap * 2)

        self.storage_slot_rects = []
        for index in range(self.storage_slots_count):
            slot_x = storage_x + self.grid_gap + index * (storage_size + self.grid_gap)
            slot_y = storage_y + self.grid_gap
            self.storage_slot_rects.append(pygame.Rect(slot_x, slot_y, storage_size, storage_size))
        
        # Resize hover animation list to match the new storage slots count
        while len(self.storage_hover_anim) < self.storage_slots_count:
            self.storage_hover_anim.append(0.0)
        while len(self.storage_hover_anim) > self.storage_slots_count:
            self.storage_hover_anim.pop()

        self.bar_slot_rects = []
        for index in range(self.bar_slots_count):
            slot_x = bar_x + self.grid_gap + index * (bar_size + self.grid_gap)
            slot_y = bar_y + self.grid_gap
            self.bar_slot_rects.append(pygame.Rect(slot_x, slot_y, bar_size, bar_size))

        exit_width = max(120, int(self.sidebar_rect.width * 0.55))
        exit_height = max(44, int(52 * cfg.ui_scale()))
        self.exit_button.rect = pygame.Rect(
            self.sidebar_rect.centerx - exit_width // 2,
            self.sidebar_rect.bottom - exit_height - margin,
            exit_width,
            exit_height,
        )
        try:
            self.exit_button._update_text_surface()
        except Exception:
            pass

    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)

        skillbook, skillbar = self._sync_state_to_character()
        if skillbook is None:
            skillbook, skillbar = self._skillbook()
        storage_items = self._storage_items(skillbook, skillbar)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            slot = self._slot_at_position(event.pos)
            if slot is None:
                return

            area, column_or_none, row_or_index = slot
            if area == "storage":
                # When there are no unused skills we still render one '+' slot.
                # Guard index access so clicking that placeholder does nothing.
                if row_or_index < 0 or row_or_index >= len(storage_items):
                    return
                self.drag_payload = {"source": ("storage", row_or_index), "skill": storage_items[row_or_index]}
                self.drag_offset = (event.pos[0] - self.storage_slot_rects[row_or_index].x, event.pos[1] - self.storage_slot_rects[row_or_index].y)
                return

            if skillbar[row_or_index] is not None:
                self.drag_payload = {"source": ("bar", row_or_index), "skill": skillbar[row_or_index]}
                self.drag_offset = (event.pos[0] - self.bar_slot_rects[row_or_index].x, event.pos[1] - self.bar_slot_rects[row_or_index].y)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if not self.drag_payload:
                return

            target_slot = self._slot_at_position(event.pos)
            source_area = self.drag_payload["source"][0]
            
            if target_slot is not None and target_slot[0] == "bar":
                self._on_drop(self.drag_payload["source"], ("bar", target_slot[2]))
            elif target_slot is not None and target_slot[0] == "storage":
                self._on_drop(self.drag_payload["source"], ("storage", target_slot[2]))
            elif source_area == "bar" and not self.bar_rect.collidepoint(event.pos):
                # Dropped outside the bar area - remove skill from bar
                source_index = self.drag_payload["source"][1]
                skillbar = self._skillbook()[1]
                if 0 <= source_index < len(skillbar):
                    removed_skill = skillbar[source_index]
                    skillbar[source_index] = None
                    logger.info(f"Removed skill '{removed_skill.get('name', 'unknown')}' from bar slot {source_index} by dragging outside")

            self.drag_payload = None
            self.drag_offset = (0, 0)

    def _draw_gradient_rect(self, surface, rect, color_top, color_bottom, border_radius=0):
        """Draw a vertical gradient rectangle. Cached."""
        cache_key = (rect.width, rect.height, color_top, color_bottom, border_radius)
        if cache_key in self._gradient_cache:
            temp = self._gradient_cache[cache_key]
        else:
            height = rect.height
            temp = pygame.Surface((rect.width, height), pygame.SRCALPHA)
            for y in range(height):
                t = y / max(1, height - 1)
                r = int(color_top[0] + (color_bottom[0] - color_top[0]) * t)
                g = int(color_top[1] + (color_bottom[1] - color_top[1]) * t)
                b = int(color_top[2] + (color_bottom[2] - color_top[2]) * t)
                pygame.draw.line(temp, (r, g, b), (0, y), (rect.width, y))
            if border_radius > 0:
                mask = pygame.Surface((rect.width, height), pygame.SRCALPHA)
                mask.fill((0, 0, 0, 0))
                pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, rect.width, height), border_radius=border_radius)
                temp.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            self._gradient_cache[cache_key] = temp
        surface.blit(temp, rect)

    def _draw_sidebar(self, surface: pygame.Surface):
        t = self.animation_time
        r = self.sidebar_rect
        
        # ── Glassmorphism gradient background ──
        self._draw_gradient_rect(surface, r, (22, 18, 32), (12, 10, 22), border_radius=18)
        pygame.draw.rect(surface, (68, 60, 88), r, 2, border_radius=18)
        inner_border = r.inflate(-4, -4)
        pygame.draw.rect(surface, (46, 40, 62), inner_border, 1, border_radius=16)

        # ── Corner ornaments ──
        orn_len = 20
        orn_color = (150, 120, 190)
        for cx, cy, hdx, hdy in [(r.x, r.y, 1, 1), (r.right, r.y, -1, 1),
                                  (r.x, r.bottom, 1, -1), (r.right, r.bottom, -1, -1)]:
            pygame.draw.line(surface, orn_color, (cx, cy), (cx + hdx * orn_len, cy), 2)
            pygame.draw.line(surface, orn_color, (cx, cy), (cx, cy + hdy * orn_len), 2)

        # ── Title with glow ──
        title_text = _("✦ Skillbar ✦")
        glow_a = int((math.sin(t * 1.5) + 1.0) * 60 + 60)
        for i in range(4):
            glow_surf = self.title_font.render(title_text, True, (100, 80, 170))
            glow_surf.set_alpha(glow_a // (i + 1))
            surface.blit(glow_surf, (r.x + 18 + i, r.y + 18 + i))
        title = self.title_font.render(title_text, True, (240, 230, 250))
        surface.blit(title, (r.x + 18, r.y + 18))

        # ── Decorative divider ──
        div_y = r.y + 18 + title.get_height() + 12
        for i in range(r.width - 36):
            x = r.x + 18 + i
            alpha = int((1.0 - abs(i / max(1, r.width - 36) - 0.5) * 2) * 120)
            pygame.draw.line(surface, (110, 90, 170, alpha), (x, div_y), (x, div_y + 1))

        # ── Hint ──
        hint_text = _("Drag skills between the bar and storage")
        hint = self.small_font.render(hint_text, True, (150, 145, 175))
        surface.blit(hint, (r.x + 18, div_y + 10))
        py = div_y + 10 + hint.get_height() + 16

        # ── Second divider ──
        for i in range(r.width - 36):
            x = r.x + 18 + i
            alpha = int((1.0 - abs(i / max(1, r.width - 36) - 0.5) * 2) * 80)
            pygame.draw.line(surface, (80, 65, 100, alpha), (x, py), (x, py + 1))
        py += 8

        # ── Hovered skill detail panel ──
        if self.hovered_skill is not None:
            skill = self.hovered_skill
            theme = self._get_skill_theme(skill)
            
            # Skill name with theme accent
            name_color = theme["glow"]
            name = self.section_font.render(skill["name"], True, name_color)
            surface.blit(name, (r.x + 18, py))
            py += name.get_height() + 6

            # Skill ID badge
            skill_id = skill.get("skill_id", "")
            if skill_id:
                badge = self.small_font.render(skill_id.replace("_", " ").upper(), True, (30, 28, 40))
                bw = badge.get_width() + 14
                bh = badge.get_height() + 6
                badge_rect = pygame.Rect(r.x + 18, py, bw, bh)
                pygame.draw.rect(surface, (*theme["primary"], 50), badge_rect, border_radius=5)
                pygame.draw.rect(surface, theme["primary"], badge_rect, 1, border_radius=5)
                surface.blit(badge, (badge_rect.x + 7, badge_rect.y + 3))
                py += bh + 10

            # Description in styled panel
            desc = skill.get("description", "")
            if desc:
                desc_bg = pygame.Rect(r.x + 14, py, r.width - 28, 0)
                desc_font = self.small_font
                max_w = desc_bg.width - 12
                words = desc.split()
                desc_lines = []
                current = ""
                for word in words:
                    test = f"{current} {word}".strip()
                    if desc_font.size(test)[0] <= max_w or not current:
                        current = test
                    else:
                        desc_lines.append(current)
                        current = word
                if current:
                    desc_lines.append(current)
                total_h = len(desc_lines) * (desc_font.get_height() + 4) + 12
                desc_bg.h = total_h
                pygame.draw.rect(surface, (24, 20, 36), desc_bg, border_radius=8)
                pygame.draw.rect(surface, (50, 44, 68), desc_bg, 1, border_radius=8)
                dp = desc_bg.y + 6
                for line in desc_lines:
                    line_surf = desc_font.render(line, True, (200, 200, 220))
                    surface.blit(line_surf, (desc_bg.x + 6, dp))
                    dp += desc_font.get_height() + 4
                py += total_h + 8

            # Skill stats
            stats = []
            if "cooldown" in skill:
                stats.append((_("Cooldown"), f"{skill['cooldown']}s"))
            if "mana_cost" in skill:
                stats.append((_("Mana Cost"), str(skill["mana_cost"])))
            if "damage" in skill:
                stats.append((_("Damage"), str(skill["damage"])))
            if "range" in skill:
                stats.append((_("Range"), f"{skill['range']}"))
            if "duration" in skill:
                stats.append((_("Duration"), f"{skill['duration']}s"))

            if stats:
                stat_y = py
                for label, value in stats:
                    stat_bg = pygame.Rect(r.x + 14, stat_y, r.width - 28, 26)
                    pygame.draw.rect(surface, (22, 20, 34), stat_bg, border_radius=6)
                    lbl = self.small_font.render(label, True, (160, 160, 185))
                    val = self.small_font.render(value, True, theme["accent"])
                    surface.blit(lbl, (stat_bg.x + 6, stat_bg.y + 4))
                    surface.blit(val, (stat_bg.right - val.get_width() - 6, stat_bg.y + 4))
                    stat_y += 30

            py = max(py, stat_y if stats else py)

        else:
            # Empty state — show storage list
            skillbook, skillbar = self._sync_state_to_character()
            if skillbook is None:
                skillbook, skillbar = self._skillbook()
            storage_items = self._storage_items(skillbook, skillbar) if skillbook else []

            storage_label = self.section_font.render(_("Storage"), True, (220, 215, 235))
            surface.blit(storage_label, (r.x + 18, py))
            py += storage_label.get_height() + 10

            if not storage_items:
                empty = self.small_font.render(_("No unused skills"), True, (130, 130, 155))
                surface.blit(empty, (r.x + 18, py))
            else:
                for idx, sk in enumerate(storage_items):
                    # Limit to visible space
                    if py > self.exit_button.rect.top - 60:
                        break
                    theme = self._get_skill_theme(sk)
                    dot_color = theme["primary"]
                    pygame.draw.circle(surface, dot_color, (r.x + 22, py + 9), 4)
                    name = self.small_font.render(sk["name"], True, (220, 220, 235))
                    surface.blit(name, (r.x + 32, py + 1))
                    py += name.get_height() + 8

    def draw(self, screen: pygame.Surface):
        self.layout(screen)
        
        # Calculate delta time for animations
        dt = 0.016
        try:
            dt = self.app.clock.get_time() / 1000.0 if hasattr(self.app, 'clock') else 0.016
        except Exception:
            pass
        
        # Update all animations
        self._update_animations(dt)

        # Dark background
        screen.fill((12, 10, 20))
        
        # Draw floating particles in background
        self._draw_particle_background(screen, screen.get_rect())

        skillbook, skillbar = self._sync_state_to_character()
        if skillbook is None:
            skillbook, skillbar = self._skillbook()
        storage_items = self._storage_items(skillbook, skillbar)

        # Calculate entrance animation offset
        entrance_offset = 0.0
        if self.entrance_active:
            # Ease out cubic
            t = self.entrance_progress
            entrance_offset = (1.0 - t) * 50.0
        
        # Draw section titles with glow
        t = self.animation_time
        title_pulse = (math.sin(t * 2.0) + 1.0) * 0.5
        
        bar_title = self.section_font.render(_("6 active slots"), True, (235, 235, 245))
        title_y = max(12, int(self.bar_rect.y - bar_title.get_height() - 8 - entrance_offset))
        # Title glow
        glow_surf = pygame.Surface((bar_title.get_width() + 20, bar_title.get_height() + 10), pygame.SRCALPHA)
        glow_alpha = int(30 + 20 * title_pulse)
        glow_surf.fill((100, 140, 220, glow_alpha))
        screen.blit(glow_surf, (self.bar_rect.x - 10, title_y - 5))
        screen.blit(bar_title, (self.bar_rect.x, title_y))

        storage_title = self.section_font.render(_("Unused skills"), True, (235, 235, 245))
        storage_title_y = max(12, int(self.storage_grid_rect.y - storage_title.get_height() - 8 + entrance_offset))
        glow_surf2 = pygame.Surface((storage_title.get_width() + 20, storage_title.get_height() + 10), pygame.SRCALPHA)
        glow_surf2.fill((100, 140, 220, glow_alpha))
        screen.blit(glow_surf2, (self.storage_grid_rect.x - 10, storage_title_y - 5))
        screen.blit(storage_title, (self.storage_grid_rect.x, storage_title_y))

        # Draw bar container with animated neon border
        bar_color = (22, 22, 30)
        bar_glow = (80, 120, 200)
        self._draw_glowing_rect(screen, self.bar_rect, bar_color, bar_glow, 0.6 + 0.4 * title_pulse, 18)
        
        # Draw storage container with animated neon border
        storage_glow = (100, 80, 180)
        self._draw_glowing_rect(screen, self.storage_grid_rect, bar_color, storage_glow, 0.5 + 0.3 * title_pulse, 18)
        
        # Sidebar is drawn by _draw_sidebar (handles gradient, border, ornaments)

        # Draw bar slots with entrance animation
        for index, slot_rect in enumerate(self.bar_slot_rects):
            # Staggered entrance
            if self.entrance_active:
                delay = index * 0.08
                slot_progress = max(0, min(1, (self.entrance_progress - delay) * 2))
                # Ease out back
                t_slot = slot_progress
                c1 = 1.70158
                c3 = c1 + 1
                eased = 1 + c3 * pow(t_slot - 1, 3) + c1 * pow(t_slot - 1, 2)
                scale = max(0.01, eased)
                
                # Apply scale animation
                center = slot_rect.center
                w = int(slot_rect.width * scale)
                h = int(slot_rect.height * scale)
                animated_rect = pygame.Rect(center[0] - w // 2, center[1] - h // 2, w, h)
            else:
                animated_rect = slot_rect
            
            skill = skillbar[index] if index < len(skillbar) else None
            hover = self.bar_hover_anim[index] if index < len(self.bar_hover_anim) else 0.0
            self._draw_animated_card(screen, animated_rect, skill, hover, str(index + 1), index)

        # Draw storage slots with entrance animation
        for index, slot_rect in enumerate(self.storage_slot_rects):
            # Staggered entrance (reverse order)
            if self.entrance_active:
                delay = (len(self.storage_slot_rects) - index - 1) * 0.06
                slot_progress = max(0, min(1, (self.entrance_progress - 0.3 - delay) * 2))
                t_slot = slot_progress
                c1 = 1.70158
                c3 = c1 + 1
                eased = 1 + c3 * pow(t_slot - 1, 3) + c1 * pow(t_slot - 1, 2)
                scale = max(0.01, eased)
                
                center = slot_rect.center
                w = int(slot_rect.width * scale)
                h = int(slot_rect.height * scale)
                animated_rect = pygame.Rect(center[0] - w // 2, center[1] - h // 2, w, h)
            else:
                animated_rect = slot_rect
            
            skill = storage_items[index] if index < len(storage_items) else None
            hover = self.storage_hover_anim[index] if index < len(self.storage_hover_anim) else 0.0
            self._draw_animated_card(screen, animated_rect, skill, hover, "+", index)

        # Draw drag trail particles
        self._draw_drag_trail(screen)

        # Draw sidebar content
        self._draw_sidebar(screen)
        self.exit_button.draw(screen)

        # Draw dragged skill with enhanced ghost effect
        if self.drag_payload:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            skill = self.drag_payload["skill"]
            ghost_size = self.bar_slot_rects[0].width if self.bar_slot_rects else 56
            
            # Create ghost surface
            ghost = pygame.Surface((ghost_size, ghost_size), pygame.SRCALPHA)
            
            # Draw animated card on ghost
            theme = self._get_skill_theme(skill)
            fill = skill.get("color", theme["primary"])
            
            # Gradient fill
            for y in range(ghost_size):
                ratio = y / ghost_size
                r = int(fill[0] * (1.3 - 0.3 * ratio))
                g = int(fill[1] * (1.3 - 0.3 * ratio))
                b = int(fill[2] * (1.3 - 0.3 * ratio))
                pygame.draw.line(ghost, (min(255, r), min(255, g), min(255, b)), (0, y), (ghost_size, y))
            
            # Rounded mask
            mask = pygame.Surface((ghost_size, ghost_size), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=12)
            ghost.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            
            # Border
            pygame.draw.rect(ghost, theme["accent"], ghost.get_rect(), 2, border_radius=12)
            
            # Skill name
            name = self.small_font.render(skill.get("name", ""), True, (255, 255, 255))
            ghost.blit(name, name.get_rect(center=(ghost_size // 2, ghost_size // 2 - 5)))
            
            # Check if dragging outside bar area (for removal indicator)
            source_area = self.drag_payload["source"][0]
            is_outside_bar = source_area == "bar" and not self.bar_rect.collidepoint((mouse_x, mouse_y))
            
            if is_outside_bar:
                # Red overlay for removal
                red_overlay = pygame.Surface((ghost_size, ghost_size), pygame.SRCALPHA)
                red_overlay.fill((200, 50, 50, 120))
                ghost.blit(red_overlay, (0, 0))
                # Animated red X
                x_margin = ghost_size // 4
                pulse = (math.sin(t * 5) + 1.0) * 0.5
                x_color = (255, int(60 + 40 * pulse), int(60 + 40 * pulse))
                pygame.draw.line(ghost, x_color, (x_margin, x_margin), (ghost_size - x_margin, ghost_size - x_margin), 4)
                pygame.draw.line(ghost, x_color, (ghost_size - x_margin, x_margin), (x_margin, ghost_size - x_margin), 4)
            
            # Outer glow for ghost
            glow_size = ghost_size + 16
            glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            glow_color = theme["glow"]
            pygame.draw.rect(glow_surf, (*glow_color, 60), glow_surf.get_rect(), border_radius=16)
            inner_cut = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.rect(inner_cut, (0, 0, 0, 255), inner_cut.get_rect().inflate(-16, -16), border_radius=12)
            glow_surf.blit(inner_cut, (8, 8), special_flags=pygame.BLEND_RGBA_MIN)
            
            ghost.set_alpha(230)
            screen.blit(glow_surf, (mouse_x - self.drag_offset[0] - 8, mouse_y - self.drag_offset[1] - 8))
            screen.blit(ghost, (mouse_x - self.drag_offset[0], mouse_y - self.drag_offset[1]))
        
        # Update drop highlight target based on drag state
        if self.drag_payload:
            target_slot = self._slot_at_position(pygame.mouse.get_pos())
            if target_slot and target_slot[0] == "bar":
                self.drop_highlight_target = 1.0
            else:
                self.drop_highlight_target = 0.0
        else:
            self.drop_highlight_target = 0.0
        
        # Draw drop zone highlight
        if self.drop_highlight_alpha > 0.01:
            highlight_surf = pygame.Surface(self.bar_rect.size, pygame.SRCALPHA)
            alpha = int(80 * self.drop_highlight_alpha)
            pulse = (math.sin(t * 4) + 1.0) * 0.5
            extra_alpha = int(30 * pulse * self.drop_highlight_alpha)
            highlight_surf.fill((100, 200, 100, alpha + extra_alpha))
            screen.blit(highlight_surf, self.bar_rect.topleft)