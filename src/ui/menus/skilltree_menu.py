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


class SkillTreeMenu(Menu):
    """
    Enhanced skill tree screen inspired by Path of Exile with visual wow effects.
    Features: animated glowing nodes, particle background, gradient links, 
    pulsing selection, branch color themes, and expanded node count.
    """
    
    # Branch color themes for different areas of the tree
    BRANCH_THEMES = {
        "fire": {"primary": (180, 60, 30), "secondary": (255, 120, 50), "accent": (255, 200, 100), "glow": (255, 80, 20)},
        "ice": {"primary": (40, 100, 180), "secondary": (80, 160, 255), "accent": (180, 220, 255), "glow": (60, 140, 255)},
        "lightning": {"primary": (160, 140, 40), "secondary": (255, 230, 80), "accent": (255, 255, 180), "glow": (255, 220, 50)},
        "nature": {"primary": (50, 140, 60), "secondary": (100, 200, 100), "accent": (180, 255, 180), "glow": (80, 220, 80)},
        "shadow": {"primary": (100, 50, 140), "secondary": (160, 100, 220), "accent": (220, 180, 255), "glow": (140, 80, 200)},
        "arcane": {"primary": (140, 60, 120), "secondary": (220, 100, 200), "accent": (255, 180, 240), "glow": (200, 80, 180)},
    }
    
    def __init__(self, app: "App"):
        super().__init__(app)
        scale = cfg.ui_scale()
        self.title_font = cfg.get_font(max(16, int(36 * scale)))
        self.section_font = cfg.get_font(max(16, int(26 * scale)))
        self.small_font = cfg.get_font(max(14, int(20 * scale)))

        exit_width = max(120, int(200 * scale))
        exit_height = max(44, int(52 * scale))
        self.exit_button = Button(
            pygame.Rect(0, 0, exit_width, exit_height),
            _("BACK"),
            (110, 70, 70),
            (150, 95, 95),
            cfg.button_font,
            cfg.text_color,
            cfg.corner_radius,
            on_click=self.exit_menu,
        )
        # Unlock button placed above the exit button in the sidebar
        self.unlock_button = Button(
            pygame.Rect(0, 0, exit_width, exit_height),
            "",
            (70, 110, 70),
            (95, 150, 95),
            cfg.button_font,
            cfg.text_color,
            cfg.corner_radius,
            on_click=self._unlock_selected,
        )
        self.buttons = [self.exit_button, self.unlock_button]

        self.zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 1.8
        self.pan_offset = pygame.Vector2(0, 0)
        self.dragging_view = False
        self.drag_origin = pygame.Vector2(0, 0)
        self.drag_start_offset = pygame.Vector2(0, 0)

        # Animation state
        self.animation_time = 0
        self.particles = []
        self._init_particles()
        
        # Unlock animation effects
        self.unlock_effects = []  # list of active unlock animations
        self.screen_flash_alpha = 0  # for screen flash effect
        self.screen_flash_timer = 0
        
        # Entrance animation (tree assembling on open) — multi-phase cinematic
        self.entrance_active = False
        self.entrance_progress = 0.0      # 0.0 = start, 1.0 = fully assembled
        self.entrance_sparks = []          # converging spark particles
        self.entrance_glow = 0
        self._entrance_triggered = False   # prevent re-triggering
        self._entrance_animation_played = False  # only play animation once
        
        # Phase system: 0=void, 1=starfield, 2=convergence, 3=core_ignition, 4=branch_growth, 5=settled
        self.entrance_phase = 0
        self.entrance_phase_time = 0.0     # time spent in current phase
        self.entrance_total_time = 0.0     # total elapsed time
        
        # Core ignition effect
        self.core_ignition_flash = 0.0
        self.core_ignition_rings = []      # expanding energy rings from core
        self.core_ignition_particles = []  # particles bursting from core
        
        # Branch growth: track which nodes/links have been "reached" by the growing energy
        self.entrance_revealed_nodes = set()   # node IDs that have lit up
        self.entrance_revealed_links = set()   # (a,b) link tuples that have lit up
        self.entrance_growth_frontier = []     # list of (node_id, arrival_time) for BFS growth
        self.entrance_link_travels = []        # visual energy traveling along links
        
        # Background star fade-in
        self.entrance_star_alpha = 0.0
        
        # Swirling convergence vortex particles
        self.entrance_vortex = []
        
        self.nodes, self.links = self._build_tree()
        self.nodes_by_id = {node["id"]: node for node in self.nodes}
        self.selected_node_id = None
        self.hovered_node_id = None
        self.background_points = self._build_background_points()

        self.tree_rect = pygame.Rect(0, 0, 0, 0)
        self.sidebar_rect = pygame.Rect(0, 0, 0, 0)
        self._layout_size = None
        
        self.rotation_angle = 0.0
        self.target_zoom = 1.0
        self.target_pan_offset = pygame.Vector2(0, 0)
        
    def on_enter(self):
        """Called when this state becomes active. Resets and triggers the entrance animation (only first time)."""
        self._entrance_triggered = False
        self.selected_node_id = None
        self.rotation_angle = 0.0
        self.target_zoom = 1.0
        self.target_pan_offset = pygame.Vector2(0, 0)
        self.zoom = 1.0
        self.pan_offset = pygame.Vector2(0, 0)
        # Only play the entrance animation the first time the skill tree is opened
        if not self._entrance_animation_played:
            self.trigger_entrance_animation()
        else:
            # Skip animation - set everything to fully revealed state
            self.entrance_active = False
            self.entrance_phase = 6
            self.entrance_progress = 1.0
            self.entrance_star_alpha = 1.0
            # Reveal all nodes immediately
            self.entrance_revealed_nodes = {node["id"] for node in self.nodes}

    def _init_particles(self):
        """Initialize floating particles for ambient background effect."""
        self.particles = []
        for _ in range(60):
            self.particles.append({
                "x": random.uniform(-700, 700),
                "y": random.uniform(-600, 600),
                "size": random.uniform(1, 3),
                "speed_x": random.uniform(-0.2, 0.2),
                "speed_y": random.uniform(-0.3, -0.05),
                "alpha": random.uniform(0.3, 0.8),
                "pulse_speed": random.uniform(0.5, 2.0),
                "color": random.choice([(100, 140, 200), (140, 100, 180), (180, 140, 100), (100, 180, 140)]),
            })

    def trigger_entrance_animation(self):
        """Start the multi-phase cinematic entrance animation when the skill tree opens."""
        if self._entrance_triggered:
            return
        self._entrance_triggered = True
        self.entrance_active = True
        self.entrance_progress = 0.0
        self.entrance_phase = 0
        self.entrance_phase_time = 0.0
        self.entrance_total_time = 0.0
        
        # Reset all entrance state
        self.entrance_revealed_nodes = set()
        self.entrance_revealed_links = set()
        self.entrance_growth_frontier = []
        self.entrance_link_travels = []
        self.entrance_star_alpha = 0.0
        self.core_ignition_flash = 0.0
        self.core_ignition_rings = []
        self.core_ignition_particles = []
        self.entrance_vortex = []
        self.entrance_sparks = []
        self.entrance_glow = 1.0
        
        rng = random.Random(42)
        
        # Pre-generate vortex particles that will spiral into the center
        self.entrance_vortex = []
        for _ in range(120):
            angle = rng.uniform(0, math.pi * 2)
            dist = rng.uniform(300, 700)
            speed = rng.uniform(0.6, 1.8)
            orbit_speed = rng.uniform(1.5, 4.0) * rng.choice([-1, 1])
            size = rng.uniform(1.5, 5.0)
            brightness = rng.uniform(0.5, 1.0)
            # Color from a random branch
            branch = rng.choice(list(self.BRANCH_THEMES.keys()))
            theme = self.BRANCH_THEMES[branch]
            color = rng.choice([theme["glow"], theme["primary"], theme["secondary"], theme["accent"]])
            self.entrance_vortex.append({
                "angle": angle,
                "dist": dist,
                "initial_dist": dist,
                "speed": speed,           # radial inward speed
                "orbit_speed": orbit_speed,  # angular speed (radians/sec)
                "size": size,
                "brightness": brightness,
                "color": color,
                "alpha": 0.0,
                "trail": [],
            })
        
        # Pre-generate the sparks that converge from edges (kept for extra flair)
        for node in self.nodes:
            count = 2 + (node["size"] // 6)
            for _ in range(count):
                side = rng.randint(0, 3)
                if side == 0:
                    sx = rng.uniform(-750, 750)
                    sy = rng.uniform(-700, -600)
                elif side == 1:
                    sx = rng.uniform(-750, 750)
                    sy = rng.uniform(600, 700)
                elif side == 2:
                    sx = rng.uniform(-800, -700)
                    sy = rng.uniform(-650, 650)
                else:
                    sx = rng.uniform(700, 800)
                    sy = rng.uniform(-650, 650)
                
                target_pos = node["pos"]
                branch = node.get("branch", "arcane")
                theme = self.BRANCH_THEMES.get(branch, self.BRANCH_THEMES["arcane"])
                color = rng.choice([theme["glow"], theme["primary"], theme["secondary"], theme["accent"], (255, 255, 255)])
                travel_time = rng.uniform(0.5, 1.8)
                
                self.entrance_sparks.append({
                    "x": sx,
                    "y": sy,
                    "start_x": sx,
                    "start_y": sy,
                    "target_x": target_pos.x,
                    "target_y": target_pos.y,
                    "progress": 0.0,
                    "speed": 1.0 / travel_time,
                    "size": rng.uniform(1.0, 3.5),
                    "color": color,
                    "alpha": 1.0,
                    "arrived": False,
                    "delay": rng.uniform(0.0, 0.5),
                    "node_id": node["id"],
                })
        rng.shuffle(self.entrance_sparks)

    def _update_entrance(self, dt):
        """Update the multi-phase cinematic entrance animation."""
        if not self.entrance_active:
            return
        
        self.entrance_phase_time += dt
        self.entrance_total_time += dt
        
        # ─── Phase transitions ───
        if self.entrance_phase == 0:
            # Phase 0: Void — brief darkness (0.4s)
            if self.entrance_phase_time >= 0.4:
                self.entrance_phase = 1
                self.entrance_phase_time = 0.0
        
        elif self.entrance_phase == 1:
            # Phase 1: Starfield — background stars fade in (0.8s)
            self.entrance_star_alpha = min(1.0, self.entrance_phase_time / 0.8)
            if self.entrance_phase_time >= 0.8:
                self.entrance_phase = 2
                self.entrance_phase_time = 0.0
        
        elif self.entrance_phase == 2:
            # Phase 2: Convergence — vortex particles spiral inward (1.8s)
            # Also start moving sparks toward their targets
            progress = min(1.0, self.entrance_phase_time / 1.8)
            self.entrance_progress = progress * 0.3  # map to 0..0.3 range
            
            # Update vortex particles: spiral inward
            for vp in self.entrance_vortex:
                # Fade in
                vp["alpha"] = min(vp["brightness"], vp["alpha"] + dt * 2.0)
                # Spiral inward
                vp["dist"] = max(0, vp["dist"] - vp["speed"] * 180 * dt)
                vp["angle"] += vp["orbit_speed"] * dt
                # Update position
                vp["x"] = math.cos(vp["angle"]) * vp["dist"]
                vp["y"] = math.sin(vp["angle"]) * vp["dist"]
                # Store trail point
                vp["trail"].append((vp["x"], vp["y"], vp["alpha"]))
                if len(vp["trail"]) > 12:
                    vp["trail"].pop(0)
            
            # Also update sparks (they start moving during convergence)
            self._update_entrance_sparks(dt)
            
            if self.entrance_phase_time >= 1.8:
                self.entrance_phase = 3
                self.entrance_phase_time = 0.0
                # Trigger core ignition!
                self.core_ignition_flash = 1.0
                # Spawn expanding energy rings from core
                for i in range(5):
                    self.core_ignition_rings.append({
                        "radius": 0,
                        "max_radius": 200 + i * 80,
                        "speed": 250 + i * 40,
                        "alpha": 0.9 - i * 0.1,
                        "width": 4 - i * 0.5,
                        "delay": i * 0.12,
                        "started": False,
                    })
                # Spawn burst particles from core
                for _ in range(60):
                    angle = random.uniform(0, math.pi * 2)
                    speed = random.uniform(80, 300)
                    life = random.uniform(0.5, 1.5)
                    branch = random.choice(list(self.BRANCH_THEMES.keys()))
                    theme = self.BRANCH_THEMES[branch]
                    color = random.choice([theme["glow"], theme["accent"], (255, 255, 255)])
                    self.core_ignition_particles.append({
                        "x": 0, "y": 0,
                        "vx": math.cos(angle) * speed,
                        "vy": math.sin(angle) * speed,
                        "size": random.uniform(2, 6),
                        "life": life,
                        "max_life": life,
                        "color": color,
                        "alpha": 1.0,
                    })
                # Start BFS growth from core
                self.entrance_revealed_nodes.add("core")
                # Add all nodes linked to core to the frontier
                for a, b in self.links:
                    if a == "core":
                        self.entrance_growth_frontier.append((b, 0.0))
                    elif b == "core":
                        self.entrance_growth_frontier.append((a, 0.0))
        
        elif self.entrance_phase == 3:
            # Phase 3: Core ignition flash + rings expanding (1.2s)
            self.core_ignition_flash = max(0, self.core_ignition_flash - dt * 2.5)
            
            # Update ignition rings
            for ring in self.core_ignition_rings:
                if ring["delay"] > 0:
                    ring["delay"] -= dt
                    continue
                ring["started"] = True
                ring["radius"] += ring["speed"] * dt
                ring["alpha"] = max(0, ring["alpha"] - dt * 0.8)
                ring["width"] = max(0.5, ring["width"] - dt * 1.5)
            
            # Update ignition particles
            for p in self.core_ignition_particles:
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["vx"] *= 0.97
                p["vy"] *= 0.97
                p["life"] -= dt
                p["alpha"] = max(0, p["life"] / p["max_life"])
            
            # Continue updating vortex (they're settling now)
            for vp in self.entrance_vortex:
                vp["dist"] = max(0, vp["dist"] - vp["speed"] * 60 * dt)
                vp["angle"] += vp["orbit_speed"] * 0.5 * dt
                vp["x"] = math.cos(vp["angle"]) * vp["dist"]
                vp["y"] = math.sin(vp["angle"]) * vp["dist"]
                vp["alpha"] = max(0, vp["alpha"] - dt * 0.5)
                vp["trail"].append((vp["x"], vp["y"], vp["alpha"]))
                if len(vp["trail"]) > 8:
                    vp["trail"].pop(0)
            
            # Continue sparks
            self._update_entrance_sparks(dt)
            
            self.entrance_progress = 0.3 + min(0.15, self.entrance_phase_time / 1.2 * 0.15)
            
            if self.entrance_phase_time >= 1.2:
                self.entrance_phase = 4
                self.entrance_phase_time = 0.0
        
        elif self.entrance_phase == 4:
            # Phase 4: Branch growth — energy spreads from core outward through links
            # BFS-style reveal with timed delays
            growth_speed = 220  # nodes per second conceptually
            max_phase_duration = 8.0  # fallback timeout
            
            # Process frontier: reveal nodes and spawn link travels
            new_frontier = []
            for node_id, arrival_time in self.entrance_growth_frontier:
                if node_id in self.entrance_revealed_nodes:
                    continue
                if self.entrance_phase_time >= arrival_time:
                    self.entrance_revealed_nodes.add(node_id)
                    # Find links from this node to unrevealed neighbors
                    for a, b in self.links:
                        neighbor = None
                        if a == node_id and b not in self.entrance_revealed_nodes:
                            neighbor = b
                        elif b == node_id and a not in self.entrance_revealed_nodes:
                            neighbor = a
                        if neighbor is not None:
                            # Calculate distance for travel time
                            node_a = self.nodes_by_id.get(a)
                            node_b = self.nodes_by_id.get(b)
                            if node_a and node_b:
                                dist = math.sqrt((node_a["pos"].x - node_b["pos"].x)**2 + 
                                                (node_a["pos"].y - node_b["pos"].y)**2)
                                travel_time = dist / growth_speed
                                link_key = (min(a, b), max(a, b))
                                if link_key not in self.entrance_revealed_links:
                                    self.entrance_revealed_links.add(link_key)
                                    self.entrance_link_travels.append({
                                        "from_id": node_id,
                                        "to_id": neighbor,
                                        "progress": 0.0,
                                        "speed": 1.0 / max(0.15, travel_time),
                                        "alpha": 1.0,
                                    })
                                # Only add if not already in new_frontier
                                if not any(nid == neighbor for nid, _ in new_frontier):
                                    new_frontier.append((neighbor, self.entrance_phase_time + travel_time))
                else:
                    # Node hasn't reached arrival time yet — keep it in the frontier!
                    if not any(nid == node_id for nid, _ in new_frontier):
                        new_frontier.append((node_id, arrival_time))
            
            self.entrance_growth_frontier = new_frontier
            
            # Update link travel visuals
            for travel in self.entrance_link_travels:
                travel["progress"] = min(1.0, travel["progress"] + dt * travel["speed"])
                if travel["progress"] >= 1.0:
                    travel["alpha"] = max(0, travel["alpha"] - dt * 3.0)
            
            # Clean up finished travels
            self.entrance_link_travels = [t for t in self.entrance_link_travels if t["alpha"] > 0.01]
            
            # Update remaining sparks
            self._update_entrance_sparks(dt)
            
            # Progress: 0.45 to 0.9
            self.entrance_progress = 0.45 + min(0.45, self.entrance_phase_time / max_phase_duration * 0.45)
            
            # Check if all nodes are revealed and travels done, OR timeout reached
            all_revealed = len(self.entrance_revealed_nodes) >= len(self.nodes)
            all_travels_done = len(self.entrance_link_travels) == 0
            timeout_reached = self.entrance_phase_time >= max_phase_duration
            if (all_revealed and all_travels_done) or timeout_reached:
                self.entrance_phase = 5
                self.entrance_phase_time = 0.0
        
        elif self.entrance_phase == 5:
            # Phase 5: Settlement — everything is revealed, gentle fade to normal
            self.entrance_progress = min(1.0, self.entrance_progress + dt * 2.0)
            
            # Fade out remaining vortex
            for vp in self.entrance_vortex:
                vp["alpha"] = max(0, vp["alpha"] - dt * 2.0)
            
            # Clean up ignition effects
            self.core_ignition_particles = [p for p in self.core_ignition_particles if p["life"] > 0]
            
            # Clear any remaining link travels to prevent lights staying on
            self.entrance_link_travels = []
            
            if self.entrance_progress >= 1.0:
                self.entrance_active = False
                self.entrance_phase = 6  # done
                self._entrance_animation_played = True  # don't play animation again
                # Final celebratory flash
                self.screen_flash_alpha = 0.15
                self.screen_flash_timer = 0.25
    
    def _update_entrance_sparks(self, dt):
        """Update the converging spark particles during entrance."""
        for spark in self.entrance_sparks:
            if spark["arrived"]:
                continue
            if spark["delay"] > 0:
                spark["delay"] -= dt
                continue
            
            spark["progress"] += dt * spark["speed"]
            if spark["progress"] >= 1.0:
                spark["progress"] = 1.0
                spark["x"] = spark["target_x"]
                spark["y"] = spark["target_y"]
                spark["arrived"] = True
            else:
                t = spark["progress"]
                ease = t * t * (3 - 2 * t)
                spark["x"] = spark["start_x"] + (spark["target_x"] - spark["start_x"]) * ease
                spark["y"] = spark["start_y"] + (spark["target_y"] - spark["start_y"]) * ease
                if ease < 0.5:
                    spark["alpha"] = 0.6 + 0.4 * (ease / 0.5)
                else:
                    spark["alpha"] = 0.6 + 0.4 * ((1.0 - ease) / 0.5)

    def _draw_entrance_sparks(self, surface):
        """Draw all entrance animation effects: vortex, sparks, core ignition, branch growth."""
        if self.entrance_phase == 0:
            # Phase 0: void — draw nothing extra
            return
        
        origin = pygame.Vector2(self.tree_rect.center) + self.pan_offset
        
        # ─── Phase 1+: Background star fade-in overlay ───
        # (Stars are drawn in _draw_tree_background, controlled by entrance_star_alpha)
        
        # ─── Phase 2+: Swirling vortex particles ───
        if self.entrance_phase >= 2 and self.entrance_vortex:
            for vp in self.entrance_vortex:
                if vp["alpha"] <= 0.01:
                    continue
                sx = origin.x + vp.get("x", 0) * self.zoom
                sy = origin.y + vp.get("y", 0) * self.zoom
                
                if not self.tree_rect.collidepoint((int(sx), int(sy))):
                    continue
                
                alpha = vp["alpha"]
                color = vp["color"]
                size = max(1, vp["size"] * self.zoom)
                
                # Draw trail — apply alpha to color so trails fade out properly
                if alpha > 0.02:
                    trail = vp.get("trail", [])
                    if len(trail) >= 2:
                        for i in range(len(trail) - 1):
                            tx, ty, ta = trail[i]
                            tx2, ty2, ta2 = trail[i + 1]
                            trail_sx = origin.x + tx * self.zoom
                            trail_sy = origin.y + ty * self.zoom
                            trail_sx2 = origin.x + tx2 * self.zoom
                            trail_sy2 = origin.y + ty2 * self.zoom
                            trail_brightness = ta * alpha * (i / max(1, len(trail) - 1))
                            if trail_brightness > 0.03:
                                trail_color = tuple(max(0, min(255, int(c * trail_brightness))) for c in color)
                                pygame.draw.line(surface, trail_color,
                                               (int(trail_sx), int(trail_sy)),
                                               (int(trail_sx2), int(trail_sy2)),
                                               max(1, int(size * 0.6)))
                
                # Draw glow
                glow_r = max(2, int(size * 3))
                glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                glow_a = int(60 * alpha)
                pygame.draw.circle(glow_surf, (color[0], color[1], color[2], glow_a), (glow_r, glow_r), glow_r)
                surface.blit(glow_surf, (int(sx) - glow_r, int(sy) - glow_r))
                
                # Draw core
                core_a = int(255 * alpha)
                core_color = tuple(min(255, c + 40) for c in color)
                pygame.draw.circle(surface, core_color, (int(sx), int(sy)), max(1, int(size)))
        
        # ─── Phase 2+: Converging sparks ───
        for spark in self.entrance_sparks:
            if spark["arrived"] and self.entrance_phase >= 4:
                continue
            
            screen_x = origin.x + spark["x"] * self.zoom
            screen_y = origin.y + spark["y"] * self.zoom
            
            if not self.tree_rect.collidepoint((int(screen_x), int(screen_y))):
                continue
            
            phase_factor = min(1.0, max(0.0, (self.entrance_total_time - 0.8) / 0.5))
            alpha = int(255 * spark["alpha"] * phase_factor)
            if alpha <= 5:
                continue
            
            color = spark["color"]
            size = max(0.5, spark["size"] * self.zoom * (0.8 + 0.4 * (1.0 - spark["progress"])))
            
            # Glow
            glow_r = max(1, int(size * 2.5))
            for g in range(2):
                gc = tuple(int(c * (0.25 - g * 0.08)) for c in color)
                pygame.draw.circle(surface, gc, (int(screen_x), int(screen_y)), glow_r - g * 2)
            
            # Core
            core_color = tuple(min(255, int(c + 50)) for c in color)
            pygame.draw.circle(surface, core_color, (int(screen_x), int(screen_y)), max(1, int(size)))
            
            # Trail
            if spark["progress"] > 0.05 and not spark["arrived"]:
                t = spark["progress"]
                ease = t * t * (3 - 2 * t)
                trail_factor = max(0.05, ease - 0.04)
                trail_ease = trail_factor * trail_factor * (3 - 2 * trail_factor)
                trail_x = origin.x + (spark["start_x"] + (spark["target_x"] - spark["start_x"]) * trail_ease) * self.zoom
                trail_y = origin.y + (spark["start_y"] + (spark["target_y"] - spark["start_y"]) * trail_ease) * self.zoom
                pygame.draw.line(surface, color,
                                 (int(trail_x), int(trail_y)), (int(screen_x), int(screen_y)),
                                 max(1, int(size * 0.4)))
        
        # ─── Phase 3: Core ignition flash ───
        if self.core_ignition_flash > 0.01:
            core_node = self.nodes_by_id.get("core")
            if core_node:
                cx = origin.x + core_node["pos"].x * self.zoom
                cy = origin.y + core_node["pos"].y * self.zoom
                
                # Bright flash
                flash_r = int(120 * self.core_ignition_flash * self.zoom)
                flash_surf = pygame.Surface((flash_r * 2, flash_r * 2), pygame.SRCALPHA)
                flash_a = int(200 * self.core_ignition_flash)
                pygame.draw.circle(flash_surf, (200, 220, 255, flash_a), (flash_r, flash_r), flash_r)
                inner_r = int(flash_r * 0.4)
                pygame.draw.circle(flash_surf, (255, 255, 255, min(255, flash_a + 50)), (flash_r, flash_r), inner_r)
                surface.blit(flash_surf, (int(cx) - flash_r, int(cy) - flash_r))
        
        # ─── Phase 3: Core ignition expanding rings ───
        for ring in self.core_ignition_rings:
            if not ring["started"] or ring["alpha"] <= 0.01:
                continue
            core_node = self.nodes_by_id.get("core")
            if core_node:
                cx = origin.x + core_node["pos"].x * self.zoom
                cy = origin.y + core_node["pos"].y * self.zoom
                r = int(ring["radius"] * self.zoom)
                if r > 0:
                    a = int(255 * ring["alpha"])
                    color = (140, 180, 255)
                    pygame.draw.circle(surface, color, (int(cx), int(cy)), r, max(1, int(ring["width"] * self.zoom)))
                    # Inner glow ring
                    if r > 4:
                        ga = a // 3
                        pygame.draw.circle(surface, (200, 220, 255), (int(cx), int(cy)), r - 2, max(1, int(ring["width"] * self.zoom * 0.5)))
        
        # ─── Phase 3: Core ignition burst particles ───
        for p in self.core_ignition_particles:
            if p["life"] <= 0:
                continue
            px = origin.x + p["x"] * self.zoom
            py = origin.y + p["y"] * self.zoom
            if not self.tree_rect.collidepoint((int(px), int(py))):
                continue
            a = int(255 * p["alpha"])
            if a <= 5:
                continue
            color = p["color"]
            sz = max(1, int(p["size"] * p["alpha"] * self.zoom))
            # Glow
            glow_r = sz * 3
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (color[0], color[1], color[2], a // 3), (glow_r, glow_r), glow_r)
            surface.blit(glow_surf, (int(px) - glow_r, int(py) - glow_r))
            # Core
            bright = tuple(min(255, c + 60) for c in color)
            pygame.draw.circle(surface, bright, (int(px), int(py)), sz)
        
        # ─── Phase 4: Branch growth — link travel visuals ───
        for travel in self.entrance_link_travels:
            from_node = self.nodes_by_id.get(travel["from_id"])
            to_node = self.nodes_by_id.get(travel["to_id"])
            if from_node is None or to_node is None:
                continue
            
            from_pos = self._node_screen_pos(from_node)
            to_pos = self._node_screen_pos(to_node)
            
            progress = travel["progress"]
            # Position along the link
            cx = from_pos.x + (to_pos.x - from_pos.x) * progress
            cy = from_pos.y + (to_pos.y - from_pos.y) * progress
            
            alpha = travel["alpha"]
            if alpha <= 0.01:
                continue
            
            # Determine color from branch
            branch = from_node.get("branch") or to_node.get("branch") or "arcane"
            theme = self.BRANCH_THEMES.get(branch, self.BRANCH_THEMES["arcane"])
            color = theme["glow"]
            
            # Draw glowing traveling orb
            orb_size = max(3, int(8 * self.zoom))
            
            # Trail line (already revealed portion) — apply alpha to color so it fades out
            if alpha > 0.05:
                trail_end_x = from_pos.x + (to_pos.x - from_pos.x) * max(0, progress - 0.15)
                trail_end_y = from_pos.y + (to_pos.y - from_pos.y) * max(0, progress - 0.15)
                trail_color = tuple(max(0, min(255, int(c * alpha))) for c in color)
                pygame.draw.line(surface, trail_color,
                               (int(trail_end_x), int(trail_end_y)), (int(cx), int(cy)),
                               max(2, int(3 * self.zoom)))
            
            # Bright orb at the front
            glow_r = orb_size * 3
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            glow_a = int(100 * alpha)
            pygame.draw.circle(glow_surf, (color[0], color[1], color[2], glow_a), (glow_r, glow_r), glow_r)
            surface.blit(glow_surf, (int(cx) - glow_r, int(cy) - glow_r))
            
            if alpha > 0.1:
                pygame.draw.circle(surface, (255, 255, 255), (int(cx), int(cy)), max(2, orb_size // 2))
            
            # Sparkle particles around the orb — apply alpha to color so they fade out
            if alpha > 0.1:
                for _ in range(3):
                    sx = cx + random.uniform(-orb_size, orb_size)
                    sy = cy + random.uniform(-orb_size, orb_size)
                    spark_brightness = alpha * random.uniform(0.3, 1.0)
                    spark_color = tuple(max(0, min(255, int(c * spark_brightness))) for c in color)
                    spark_sz = max(1, int(2 * self.zoom))
                    pygame.draw.circle(surface, spark_color, (int(sx), int(sy)), spark_sz)

    def _character(self):
        gameplay_state = getattr(getattr(self.app, "manager", None), "states", {}).get("gameplay")
        return getattr(gameplay_state, "character", None)

    def _get_unlocked_nodes(self):
        character = self._character()
        unlocked = getattr(character, "skill_tree_unlocked", None) if character else None
        if unlocked is None:
            return {"core"}
        if isinstance(unlocked, list):
            return set(unlocked)
        return set(unlocked)

    def _build_tree(self):
        nodes = []
        links = []
        link_set = set()

        # Branch theme assignments for each sector (6 branches around the circle)
        branch_names = ["fire", "ice", "lightning", "nature", "shadow", "arcane"]
        
        # Node name/effect data for themed notable nodes
        notable_data = {
            "fire": [
                (_("Fireball Mastery"), _("Unlocks the Fireball skill — launch an explosive fireball dealing 28 damage with area effect and knockback.")),
                (_("Flame Shield"), _("Surrounds you with flames, dealing 8 damage/sec to nearby enemies.")),
                (_("Pyromancer's Fury"), _("Fire skills deal 25% more damage and have 15% larger area.")),
            ],
            "ice": [
                (_("Frost Nova"), _("Unlocks Frost Nova — freeze all enemies within radius for 3 seconds.")),
                (_("Ice Armor"), _("Grants a shield of ice absorbing 30 damage and slowing attackers.")),
                (_("Glacial Cascade"), _("Ice shards cascade outward dealing 35 damage and freezing enemies.")),
            ],
            "lightning": [
                (_("Chain Lightning"), _("Unlocks Chain Lightning — bolt jumps between up to 5 enemies.")),
                (_("Static Field"), _("Passive: 12% chance to shock attackers, dealing 20 damage.")),
                (_("Thunderstrike"), _("Call down lightning for 55 damage in a column from above.")),
            ],
            "nature": [
                (_("Entangling Roots"), _("Unlocks root trap that immobilizes enemies for 4 seconds.")),
                (_("Regeneration"), _("Passive: regenerate 3 HP per second at all times.")),
                (_("Summon Spirit"), _("Summon a nature spirit that attacks for 15 damage.")),
            ],
            "shadow": [
                (_("Shadow Step"), _("Unlocks teleport through shadows, becoming invulnerable briefly.")),
                (_("Poison Blade"), _("Attacks apply poison dealing 6 damage/sec for 5 seconds.")),
                (_("Dark Pact"), _("Sacrifice 10% HP to deal 60 shadow damage to all nearby enemies.")),
            ],
            "arcane": [
                (_("Arcane Missiles"), _("Unlocks homing arcane missiles dealing 22 damage each.")),
                (_("Mana Flow"), _("Passive: skill cooldowns reduced by 20%.")),
                (_("Mystic Barrier"), _("Creates a barrier that reflects 30% of incoming damage.")),
            ],
        }

        keystone_data = [
            (_("Berserker's Rage"), _("Massive damage boost (+50%) but take 20% more damage. The fury consumes you.")),
            (_("Eternal Fortress"), _("+80% defense and +40 max HP, but movement speed reduced by 15%.")),
            (_("Soul Harvest"), _("Each kill restores 5 HP and grants +2% damage for 8 seconds (stacks).")),
            (_("Void Walker"), _("Teleport on dodge. +30% dodge chance. Leave afterimage dealing 18 damage.")),
            (_("Elemental Mastery"), _("All elemental damage +35%. Unlock dual-element combo attacks.")),
            (_("Chrono Shift"), _("Slow time for 3 seconds. +25% attack speed. Cooldown: 30 seconds.")),
        ]

        def add_node(node_id, name, effect, pos, size, kind, color, accent, branch=None):
            nodes.append({
                "id": node_id,
                "name": name,
                "effect": effect,
                "pos": pygame.Vector2(pos),
                "size": size,
                "kind": kind,
                "color": color,
                "accent": accent,
                "branch": branch,
            })

        def add_link(a, b):
            if a == b:
                return
            key = (a, b) if a < b else (b, a)
            if key in link_set:
                return
            link_set.add(key)
            links.append((a, b))

        def get_branch_color(branch, role):
            """Get color from branch theme. role: 'primary', 'secondary', 'accent', 'glow'"""
            theme = self.BRANCH_THEMES.get(branch, self.BRANCH_THEMES["arcane"])
            return theme.get(role, (100, 100, 120))

        # ─── CORE NODE ───
        add_node(
            "core",
            _("Core"),
            _("The heart of your power. Unlocks paths to all branches of mastery."),
            (0, 0),
            26,
            "core",
            (100, 140, 200),
            (220, 235, 255),
        )

        # ─── RING 1: Inner circle — 12 minor nodes ───
        ring1_count = 12
        ring1_radius = 130
        for i in range(ring1_count):
            angle = math.radians(i * (360 / ring1_count) - 90)
            pos = (math.cos(angle) * ring1_radius, math.sin(angle) * ring1_radius)
            branch = branch_names[i % len(branch_names)]
            bc = get_branch_color(branch, "primary")
            ba = get_branch_color(branch, "accent")
            node_id = f"inner_{i + 1}"
            stat_names = [
                _("Vitality I"), _("Strength I"), _("Agility I"), _("Wisdom I"),
                _("Endurance I"), _("Focus I"), _("Reflexes I"), _("Fortitude I"),
                _("Precision I"), _("Resilience I"), _("Power I"), _("Speed I"),
            ]
            stat_effects = [
                _("+5 Max HP"), _("+3 Melee Damage"), _("+2% Move Speed"), _("+4 Max Stamina"),
                _("+2 Armor"), _("+3% Crit Chance"), _("+2% Attack Speed"), _("+3 Dodge Chance"),
                _("+2 Accuracy"), _("+2% Damage Reduction"), _("+3 Spell Damage"), _("+2% Move Speed"),
            ]
            add_node(
                node_id,
                stat_names[i],
                stat_effects[i],
                pos,
                9,
                "minor",
                tuple(max(20, c - 20) for c in bc),
                ba,
                branch,
            )
            add_link("core", node_id)

        # Connect ring 1 nodes to neighbors
        for i in range(ring1_count):
            add_link(f"inner_{i + 1}", f"inner_{(i + 1) % ring1_count + 1}")

        # ─── BRIDGE NODES: Between ring 1 and ring 2 — 6 nodes ───
        bridge_radius = 210
        for i in range(6):
            angle = math.radians(i * 60 - 60)
            pos = (math.cos(angle) * bridge_radius, math.sin(angle) * bridge_radius)
            branch = branch_names[i]
            bc = get_branch_color(branch, "primary")
            ba = get_branch_color(branch, "accent")
            node_id = f"bridge_{i + 1}"
            add_node(
                node_id,
                _("Path Node"),
                _("Opens the way to greater power in this branch."),
                pos,
                8,
                "minor",
                tuple(max(20, c - 10) for c in bc),
                ba,
                branch,
            )
            # Link to two nearest inner nodes
            idx1 = (i * 2) % ring1_count + 1
            idx2 = (i * 2 + 1) % ring1_count + 1
            add_link(node_id, f"inner_{idx1}")
            add_link(node_id, f"inner_{idx2}")

        # ─── RING 2: Notable nodes — 6 major nodes with 4 cluster nodes each ───
        ring2_count = 6
        ring2_radius = 310
        for i in range(ring2_count):
            angle = math.radians(i * (360 / ring2_count) - 60)
            pos = (math.cos(angle) * ring2_radius, math.sin(angle) * ring2_radius)
            branch = branch_names[i]
            bc = get_branch_color(branch, "primary")
            bs = get_branch_color(branch, "secondary")
            ba = get_branch_color(branch, "accent")
            node_id = f"major_{i + 1}"

            # Use the first notable entry for the main node
            ndata = notable_data[branch][0]
            add_node(
                node_id,
                ndata[0],
                ndata[1],
                pos,
                18,
                "major",
                bc,
                ba,
                branch,
            )
            add_link(node_id, f"bridge_{i + 1}")

            # 4 cluster nodes around each major node
            cluster_radius = 55
            for j in range(4):
                offset = math.radians(j * 90 + 45)
                cluster_pos = (
                    pos[0] + math.cos(offset) * cluster_radius,
                    pos[1] + math.sin(offset) * cluster_radius,
                )
                cluster_id = f"cluster_{i + 1}_{j + 1}"
                # Use remaining notable data for cluster nodes 1 and 2
                if j < 2:
                    cdata = notable_data[branch][j + 1]
                    cname, ceffect = cdata[0], cdata[1]
                    ckind = "major"
                    csize = 13
                    ccolor = bs
                else:
                    cname = _("Minor Node")
                    ceffect = _("Small stat bonus in the {branch} branch.").format(branch=branch.capitalize())
                    ckind = "minor"
                    csize = 8
                    ccolor = tuple(max(20, c - 15) for c in bc)
                add_node(
                    cluster_id,
                    cname,
                    ceffect,
                    cluster_pos,
                    csize,
                    ckind,
                    ccolor,
                    ba,
                    branch,
                )
                add_link(node_id, cluster_id)

            # Link adjacent cluster nodes for visual density
            for j in range(4):
                add_link(f"cluster_{i + 1}_{j + 1}", f"cluster_{i + 1}_{(j + 1) % 4 + 1}")

        # ─── CONNECTOR NODES: Between ring 2 majors — 6 nodes ───
        for i in range(ring2_count):
            angle_a = math.radians(i * (360 / ring2_count) - 60)
            angle_b = math.radians(((i + 1) % ring2_count) * (360 / ring2_count) - 60)
            mid_angle = (angle_a + angle_b) / 2
            conn_radius = 330
            pos = (math.cos(mid_angle) * conn_radius, math.sin(mid_angle) * conn_radius)
            node_id = f"conn_{i + 1}"
            # Blend colors of adjacent branches
            b1 = branch_names[i]
            b2 = branch_names[(i + 1) % len(branch_names)]
            c1 = get_branch_color(b1, "secondary")
            c2 = get_branch_color(b2, "secondary")
            blended = tuple((a + b) // 2 for a, b in zip(c1, c2))
            add_node(
                node_id,
                _("Crossroads"),
                _("A junction between two paths of power."),
                pos,
                10,
                "minor",
                blended,
                (200, 200, 220),
                b1,
            )
            add_link(node_id, f"major_{i + 1}")
            add_link(node_id, f"major_{(i + 1) % ring2_count + 1}")

        # ─── RING 3: Keystone nodes — 6 with 3 cluster nodes each ───
        ring3_count = 6
        ring3_radius = 460
        for i in range(ring3_count):
            angle = math.radians(i * (360 / ring3_count) - 30)
            pos = (math.cos(angle) * ring3_radius, math.sin(angle) * ring3_radius)
            branch = branch_names[i]
            bc = get_branch_color(branch, "primary")
            ba = get_branch_color(branch, "accent")
            glow = get_branch_color(branch, "glow")
            node_id = f"keystone_{i + 1}"
            kd = keystone_data[i]
            add_node(
                node_id,
                kd[0],
                kd[1],
                pos,
                24,
                "keystone",
                glow,
                ba,
                branch,
            )
            add_link(node_id, f"major_{i + 1}")

            # 3 satellite nodes around each keystone
            sat_radius = 60
            for j in range(3):
                offset = math.radians(j * 120 + 30)
                sat_pos = (
                    pos[0] + math.cos(offset) * sat_radius,
                    pos[1] + math.sin(offset) * sat_radius,
                )
                sat_id = f"keystone_sat_{i + 1}_{j + 1}"
                add_node(
                    sat_id,
                    _("Keystone Shard"),
                    _("A fragment of keystone power: +2% to all stats in this branch."),
                    sat_pos,
                    8,
                    "minor",
                    tuple(max(20, c - 30) for c in bc),
                    ba,
                    branch,
                )
                add_link(node_id, sat_id)

            # Link adjacent keystone satellites
            for j in range(3):
                add_link(f"keystone_sat_{i + 1}_{j + 1}", f"keystone_sat_{i + 1}_{(j + 1) % 3 + 1}")

        # ─── RING 4: Outer ring — 18 minor nodes ───
        ring4_count = 18
        ring4_radius = 580
        for i in range(ring4_count):
            angle = math.radians(i * (360 / ring4_count) - 90)
            pos = (math.cos(angle) * ring4_radius, math.sin(angle) * ring4_radius)
            branch = branch_names[i % len(branch_names)]
            bc = get_branch_color(branch, "primary")
            ba = get_branch_color(branch, "accent")
            node_id = f"outer_{i + 1}"
            outer_names = [
                _("Iron Will"), _("Swift Feet"), _("Sharp Mind"), _("Tough Skin"),
                _("Quick Hands"), _("Eagle Eye"), _("Stone Heart"), _("Flame Touch"),
                _("Frost Bite"), _("Thunder Palm"), _("Vine Grip"), _("Shadow Veil"),
                _("Arcane Touch"), _("Steel Spine"), _("Wind Step"), _("Ember Soul"),
                _("Ice Blood"), _("Storm Core"),
            ]
            outer_effects = [
                _("+5% knockback resistance"), _("+3% movement speed"), _("+4% mana regen"),
                _("+4 armor"), _("+3% attack speed"), _("+5% accuracy"),
                _("+8 max HP"), _("+3 fire damage on hit"), _("+2% freeze chance"),
                _("+3% shock chance"), _("+2% root chance on hit"), _("+3% dodge chance"),
                _("+4 spell power"), _("+3% damage reduction"), _("+2% evasion"),
                _("+5 fire resistance"), _("+5 cold resistance"), _("+5 lightning resistance"),
            ]
            add_node(
                node_id,
                outer_names[i],
                outer_effects[i],
                pos,
                8,
                "minor",
                tuple(max(20, c - 25) for c in bc),
                ba,
                branch,
            )
            # Link to nearest keystone or keystone satellite
            ks_idx = (i % ring3_count) + 1
            sat_idx = (i % 3) + 1
            add_link(node_id, f"keystone_sat_{ks_idx}_{sat_idx}")

        # Connect outer ring neighbors
        for i in range(ring4_count):
            add_link(f"outer_{i + 1}", f"outer_{(i + 1) % ring4_count + 1}")

        # ─── EXTRA: Inter-ring connections for visual density ───
        # Connect some bridge nodes to adjacent major clusters
        for i in range(6):
            next_bridge = (i + 1) % 6 + 1
            add_link(f"bridge_{i + 1}", f"cluster_{next_bridge}_1")

        return nodes, links

    def _build_background_points(self):
        """Build twinkling star background with more stars and varied sizes."""
        rng = random.Random(23)
        points = []
        for _ in range(400):
            points.append(
                (
                    rng.uniform(-750, 750),
                    rng.uniform(-650, 650),
                    rng.randint(1, 3),
                    rng.uniform(0.3, 1.0),  # twinkle phase offset
                    rng.uniform(0.5, 2.0),  # twinkle speed
                )
            )
        return points

    def _node_screen_pos(self, node):
        origin = pygame.Vector2(self.tree_rect.center) + self.pan_offset
        # Apply rotation around the core node (0, 0)
        angle = self.rotation_angle
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        rx = node["pos"].x * cos_a - node["pos"].y * sin_a
        ry = node["pos"].x * sin_a + node["pos"].y * cos_a
        return origin + pygame.Vector2(rx, ry) * self.zoom

    def _hit_test_node(self, pos):
        if not self.tree_rect.collidepoint(pos):
            return None
        mx, my = pos
        best_id = None
        best_dist = None
        for node in self.nodes:
            node_pos = self._node_screen_pos(node)
            radius = node["size"] * self.zoom + 4
            dist = (node_pos.x - mx) ** 2 + (node_pos.y - my) ** 2
            if dist <= radius ** 2 and (best_dist is None or dist < best_dist):
                best_dist = dist
                best_id = node["id"]
        return best_id

    def _wrap_text(self, text, font, max_width):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test_line = f"{current} {word}".strip()
            if font.size(test_line)[0] <= max_width or not current:
                current = test_line
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def exit_menu(self):
        try:
            self.app.INV_manager.player_inventory_opened = False
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

    def _get_adjacent_nodes(self, node_id):
        """Get all node IDs that are directly connected to the given node."""
        adjacent = set()
        for a, b in self.links:
            if a == node_id:
                adjacent.add(b)
            elif b == node_id:
                adjacent.add(a)
        return adjacent

    def _can_unlock_node(self, node_id, unlocked):
        """Check if a node can be unlocked (must be adjacent to an unlocked node)."""
        if node_id in unlocked:
            return False
        # Core node is always unlocked by default
        if node_id == "core":
            return False
        # Check if any adjacent node is unlocked
        adjacent = self._get_adjacent_nodes(node_id)
        return bool(adjacent & unlocked)

    def _unlock_selected(self):
        selected = self.nodes_by_id.get(self.selected_node_id)
        if selected is None:
            return

        character = self._character()
        if character is None:
            return

        unlocked = self._get_unlocked_nodes()
        node_id = selected["id"]
        if node_id in unlocked:
            return

        # Check sequential unlock requirement - must be connected to an unlocked node
        if not self._can_unlock_node(node_id, unlocked):
            from src.ui.widgets import Dialog
            self.app.current_dialog = Dialog(self.app, [_('You must unlock an adjacent node first.')])
            return

        kind = selected.get("kind")
        cost_map = {"minor": 1, "major": 2, "keystone": 3, "core": 0}
        cost = cost_map.get(kind, 1)

        points = getattr(character, "skill_tree_points", 0)
        if points < cost:
            # show dialog: not enough points
            from src.ui.widgets import Dialog
            self.app.current_dialog = Dialog(self.app, [_('Not enough points to unlock this node.')])
            return

        # Deduct points and mark unlocked
        try:
            character.skill_tree_points = points - cost
        except Exception:
            try:
                setattr(character, "skill_tree_points", points - cost)
            except Exception:
                pass

        # ensure unlocked is mutable set on character
        cur = getattr(character, "skill_tree_unlocked", None)
        if cur is None:
            character.skill_tree_unlocked = {"core"}
            cur = character.skill_tree_unlocked
        if isinstance(cur, list):
            cur = set(cur)
        cur.add(node_id)
        character.skill_tree_unlocked = cur
        logger.info(f"Unlocked node {node_id}; cost {cost} points. Remaining: {getattr(character, 'skill_tree_points', 0)}")

        # If the Fireball Mastery node was unlocked, teach the fireball skill
        if node_id == "major_1" and hasattr(character, "learn_fireball"):
            character.learn_fireball()

        # Flame Shield: cluster_1_1
        if node_id == "cluster_1_1" and hasattr(character, "learn_flame_shield"):
            character.learn_flame_shield()

        # Pyromancer's Fury (passive): cluster_1_2
        if node_id == "cluster_1_2" and hasattr(character, "learn_pyromancers_fury"):
            character.learn_pyromancers_fury()

        # Ice: major_2 = Frost Nova, cluster_2_1 = Ice Armor, cluster_2_2 = Glacial Cascade
        if node_id == "major_2" and hasattr(character, "learn_frost_nova"):
            character.learn_frost_nova()

        if node_id == "cluster_2_1" and hasattr(character, "learn_ice_armor"):
            character.learn_ice_armor()

        if node_id == "cluster_2_2" and hasattr(character, "learn_glacial_cascade"):
            character.learn_glacial_cascade()

        # Lightning: major_3 = Chain Lightning, cluster_3_1 = Static Field, cluster_3_2 = Thunderstrike
        if node_id == "major_3" and hasattr(character, "learn_chain_lightning"):
            character.learn_chain_lightning()

        if node_id == "cluster_3_1" and hasattr(character, "learn_static_field"):
            character.learn_static_field()

        if node_id == "cluster_3_2" and hasattr(character, "learn_thunderstrike"):
            character.learn_thunderstrike()

        # Nature: major_4 = Entangling Roots, cluster_4_1 = Regeneration, cluster_4_2 = Summon Spirit
        if node_id == "major_4" and hasattr(character, "learn_entangling_roots"):
            character.learn_entangling_roots()

        if node_id == "cluster_4_1" and hasattr(character, "learn_regeneration"):
            character.learn_regeneration()

        if node_id == "cluster_4_2" and hasattr(character, "learn_summon_spirit"):
            character.learn_summon_spirit()

        # Shadow: major_5 = Shadow Step, cluster_5_1 = Poison Blade, cluster_5_2 = Dark Pact
        if node_id == "major_5" and hasattr(character, "learn_shadow_step"):
            character.learn_shadow_step()

        if node_id == "cluster_5_1" and hasattr(character, "learn_poison_blade"):
            character.learn_poison_blade()

        if node_id == "cluster_5_2" and hasattr(character, "learn_dark_pact"):
            character.learn_dark_pact()

        # Arcane: major_6 = Arcane Missiles, cluster_6_1 = Mana Flow, cluster_6_2 = Mystic Barrier
        if node_id == "major_6" and hasattr(character, "learn_arcane_missiles"):
            character.learn_arcane_missiles()

        if node_id == "cluster_6_1" and hasattr(character, "learn_mana_flow"):
            character.learn_mana_flow()

        if node_id == "cluster_6_2" and hasattr(character, "learn_mystic_barrier"):
            character.learn_mystic_barrier()

        # Keystones: keystone_1 = Berserker's Rage, keystone_2 = Eternal Fortress, keystone_3 = Soul Harvest, keystone_4 = Void Walker, keystone_5 = Elemental Mastery, keystone_6 = Chrono Shift
        if node_id == "keystone_1" and hasattr(character, "learn_berserkers_rage"):
            character.learn_berserkers_rage()

        if node_id == "keystone_2" and hasattr(character, "learn_eternal_fortress"):
            character.learn_eternal_fortress()

        if node_id == "keystone_3" and hasattr(character, "learn_soul_harvest"):
            character.learn_soul_harvest()

        if node_id == "keystone_4" and hasattr(character, "learn_void_walker"):
            character.learn_void_walker()

        if node_id == "keystone_5" and hasattr(character, "learn_elemental_mastery"):
            character.learn_elemental_mastery()

        if node_id == "keystone_6" and hasattr(character, "learn_chrono_shift"):
            character.learn_chrono_shift()

        # Trigger unlock animation
        self._spawn_unlock_effect(node_id)

    def layout(self, screen: pygame.Surface):
        sw, sh = self._screen_size(screen)
        scale = cfg.ui_scale()
        margin = max(12, int(24 * scale))
        sidebar_width = min(max(240, int(360 * scale)), max(240, sw // 3))
        tree_width = max(240, sw - sidebar_width - margin * 3)
        self.sidebar_rect = pygame.Rect(sw - sidebar_width - margin, margin, sidebar_width, sh - margin * 2)
        self.tree_rect = pygame.Rect(margin, margin, tree_width, sh - margin * 2)

        exit_width = max(120, int(self.sidebar_rect.width * 0.6))
        exit_height = max(44, int(52 * scale))
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

        # position unlock button above exit button
        try:
            unlock_y = self.exit_button.rect.y - exit_height - int(8 * scale)
            self.unlock_button.rect = pygame.Rect(
                self.sidebar_rect.centerx - exit_width // 2,
                unlock_y,
                exit_width,
                exit_height,
            )
            self.unlock_button._update_text_surface()
        except Exception:
            pass

        size = (sw, sh)
        if self._layout_size != size:
            self._layout_size = size
            self.selected_node_id = None
            self.rotation_angle = 0.0
            self.target_zoom = 1.0
            self.target_pan_offset = pygame.Vector2(0, 0)
            self.zoom = 1.0
            self.pan_offset = pygame.Vector2(0, 0)

    def handle_event(self, event: pygame.event.Event):
        # Route events to dialog first if one is active
        if getattr(self.app, 'current_dialog', None):
            try:
                self.app.current_dialog.handle_event(event)
                return
            except Exception:
                pass

        super().handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.tree_rect.collidepoint(event.pos):
                    node_id = self._hit_test_node(event.pos)
                    if node_id:
                        self.selected_node_id = node_id
                        self.target_zoom = 1.4
                        node = self.nodes_by_id[node_id]
                        angle = self.rotation_angle
                        cos_a = math.cos(angle)
                        sin_a = math.sin(angle)
                        rx = node["pos"].x * cos_a - node["pos"].y * sin_a
                        ry = node["pos"].x * sin_a + node["pos"].y * cos_a
                        self.target_pan_offset = pygame.Vector2(-rx * self.target_zoom, -ry * self.target_zoom)
                    else:
                        # Deselect by clicking on an area that isn't a node
                        self.selected_node_id = None
                        self.target_zoom = 1.0
                        self.target_pan_offset = pygame.Vector2(0, 0)
            elif event.button == 3:
                if self.selected_node_id is not None:
                    # Deselect on right-click if a node is currently selected
                    self.selected_node_id = None
                    self.target_zoom = 1.0
                    self.target_pan_offset = pygame.Vector2(0, 0)
                elif self.tree_rect.collidepoint(event.pos):
                    self.dragging_view = True
                    self.drag_origin = pygame.Vector2(event.pos)
                    self.drag_start_offset = pygame.Vector2(self.pan_offset)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                self.dragging_view = False

        elif event.type == pygame.MOUSEMOTION and self.dragging_view:
            if self.selected_node_id is None:
                delta = pygame.Vector2(event.pos) - self.drag_origin
                self.pan_offset = self.drag_start_offset + delta
                self.target_pan_offset = pygame.Vector2(self.pan_offset)

        elif event.type == pygame.MOUSEWHEEL:
            if self.tree_rect.collidepoint(pygame.mouse.get_pos()):
                # Only allow manual zooming when no node is selected to maintain centering
                if self.selected_node_id is None:
                    self.target_zoom = max(self.min_zoom, min(self.max_zoom, self.target_zoom + event.y * 0.08))

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.zoom = 1.0
            self.pan_offset = pygame.Vector2(0, 0)

    def _spawn_unlock_effect(self, node_id):
        """Spawn a dramatic unlock animation at the given node position.
        
        Different node kinds get different animation intensities:
        - minor: Basic particle burst and shockwave
        - major: Larger burst, spiral particles, double shockwave
        - keystone: Massive burst, rotating light beams, pulsing rings, star pattern
        - core: Ultimate explosion with rainbow particles, multiple rings, screen-filling effects
        """
        node = self.nodes_by_id.get(node_id)
        if node is None:
            return
        
        branch = node.get("branch", "arcane")
        theme = self.BRANCH_THEMES.get(branch, self.BRANCH_THEMES["arcane"])
        glow_color = theme["glow"]
        primary_color = theme["primary"]
        secondary_color = theme["secondary"]
        accent_color = theme["accent"]
        
        # Get screen position of the node
        screen_pos = self._node_screen_pos(node)
        node_size = max(4, int(node["size"] * self.zoom))
        kind = node.get("kind", "minor")
        
        # Scale effects based on node kind
        if kind == "core":
            burst_count = 200
            shockwave_count = 5
            particle_speed_mult = 2.0
            shockwave_max_radius = 400
            screen_flash_intensity = 0.6
            text_size_mult = 2.0
        elif kind == "keystone":
            burst_count = 150
            shockwave_count = 3
            particle_speed_mult = 1.6
            shockwave_max_radius = 300
            screen_flash_intensity = 0.5
            text_size_mult = 1.6
        elif kind == "major":
            burst_count = 100
            shockwave_count = 2
            particle_speed_mult = 1.3
            shockwave_max_radius = 220
            screen_flash_intensity = 0.4
            text_size_mult = 1.3
        else:  # minor
            burst_count = 60
            shockwave_count = 1
            particle_speed_mult = 1.0
            shockwave_max_radius = 150
            screen_flash_intensity = 0.25
            text_size_mult = 1.0
        
        # ─── 1. Particle burst (scaled by node kind) ───
        burst_particles = []
        for _ in range(burst_count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(60, 250) * self.zoom * particle_speed_mult
            lifetime = random.uniform(0.5, 1.5)
            # Choose a color from the branch palette
            color_choice = random.choice([glow_color, primary_color, secondary_color, accent_color, (255, 255, 255)])
            burst_particles.append({
                "type": "burst",
                "x": screen_pos.x,
                "y": screen_pos.y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "size": random.uniform(2, 8) * self.zoom,
                "life": lifetime,
                "max_life": lifetime,
                "color": color_choice,
                "alpha": 1.0,
            })
        
        # ─── 2. Multiple shockwave rings (scaled by node kind) ───
        shockwaves = []
        for i in range(shockwave_count):
            delay = i * 0.15  # Stagger the shockwaves
            shockwaves.append({
                "type": "shockwave",
                "x": screen_pos.x,
                "y": screen_pos.y,
                "radius": node_size,
                "max_radius": node_size + shockwave_max_radius * self.zoom,
                "speed": (300 + i * 50) * self.zoom,
                "life": 0.8 + i * 0.1,
                "max_life": 0.8 + i * 0.1,
                "color": glow_color if i % 2 == 0 else accent_color,
                "alpha": 0.9 - i * 0.1,
                "width": 4 - i * 0.5,
                "delay": delay,
            })
        
        # ─── 3. Cascading light on connected links ───
        link_lights = []
        adjacent = self._get_adjacent_nodes(node_id)
        unlocked = self._get_unlocked_nodes()
        for adj_id in adjacent:
            if adj_id in unlocked:
                adj_node = self.nodes_by_id.get(adj_id)
                if adj_node:
                    adj_pos = self._node_screen_pos(adj_node)
                    # Traveling light from unlocked adjacent to new node
                    link_lights.append({
                        "type": "link_light",
                        "x1": adj_pos.x,
                        "y1": adj_pos.y,
                        "x2": screen_pos.x,
                        "y2": screen_pos.y,
                        "progress": 0.0,
                        "speed": random.uniform(0.8, 1.5),
                        "color": secondary_color,
                        "size": max(3, int(6 * self.zoom)),
                        "alpha": 1.0,
                    })
        
        # ─── 4. Floating text effect (scaled by node kind) ───
        float_text = {
            "type": "float_text",
            "x": screen_pos.x,
            "y": screen_pos.y - node_size - 20,
            "text": "✦ UNLOCKED ✦" if kind == "minor" else "★ UNLOCKED ★" if kind == "major" else "✧ UNLOCKED ✧" if kind == "keystone" else "⚜ UNLOCKED ⚜",
            "color": accent_color,
            "life": 2.0,
            "max_life": 2.0,
            "speed_y": -50 * self.zoom,
            "size": max(16, int(22 * self.zoom * text_size_mult)),
        }
        
        # Add all effects to the queue
        self.unlock_effects.extend(burst_particles)
        self.unlock_effects.extend(shockwaves)
        self.unlock_effects.extend(link_lights)
        self.unlock_effects.append(float_text)
        
        # ─── 5. Additional effects for major+ nodes ───
        if kind in ("major", "keystone", "core"):
            # Spiral particles that orbit outward
            spiral_count = 20 if kind == "major" else 40 if kind == "keystone" else 60
            for i in range(spiral_count):
                angle = (i / spiral_count) * math.pi * 2
                speed = random.uniform(80, 180) * self.zoom * particle_speed_mult
                lifetime = random.uniform(0.8, 1.8)
                # Alternate colors for spiral effect
                color = glow_color if i % 2 == 0 else accent_color
                self.unlock_effects.append({
                    "type": "spiral_particle",
                    "x": screen_pos.x,
                    "y": screen_pos.y,
                    "angle": angle,
                    "radius": 0,
                    "speed": speed,
                    "angular_speed": random.uniform(2, 5) * (1 if i % 2 == 0 else -1),
                    "life": lifetime,
                    "max_life": lifetime,
                    "color": color,
                    "size": random.uniform(3, 7) * self.zoom,
                    "alpha": 1.0,
                })
        
        if kind in ("keystone", "core"):
            # Rotating light beams (only for keystone and core)
            beam_count = 6 if kind == "keystone" else 12
            for i in range(beam_count):
                angle = (i / beam_count) * math.pi * 2
                self.unlock_effects.append({
                    "type": "light_beam",
                    "x": screen_pos.x,
                    "y": screen_pos.y,
                    "angle": angle,
                    "length": node_size * 3,
                    "max_length": (150 if kind == "keystone" else 250) * self.zoom,
                    "speed": 200 * self.zoom,
                    "life": 1.0,
                    "max_life": 1.0,
                    "color": glow_color,
                    "width": 3 * self.zoom,
                    "alpha": 0.8,
                })
            
            # Pulsing concentric rings
            ring_count = 3 if kind == "keystone" else 5
            for i in range(ring_count):
                self.unlock_effects.append({
                    "type": "pulse_ring",
                    "x": screen_pos.x,
                    "y": screen_pos.y,
                    "radius": node_size + i * 20 * self.zoom,
                    "max_radius": node_size + (100 + i * 30) * self.zoom,
                    "pulse_speed": 100 * self.zoom,
                    "life": 1.5,
                    "max_life": 1.5,
                    "color": accent_color if i % 2 == 0 else glow_color,
                    "width": 2 * self.zoom,
                    "alpha": 0.6,
                    "phase": i * 0.3,
                })
        
        if kind == "core":
            # Star burst pattern - particles in a star shape
            star_points = 8
            for i in range(star_points):
                angle = (i / star_points) * math.pi * 2
                for j in range(15):
                    speed = (100 + j * 20) * self.zoom
                    lifetime = random.uniform(0.6, 1.4)
                    # Rainbow colors for core unlock
                    hue = (i * 45 + j * 10) % 360
                    color = self._hsv_to_rgb(hue, 0.8, 1.0)
                    self.unlock_effects.append({
                        "type": "burst",
                        "x": screen_pos.x,
                        "y": screen_pos.y,
                        "vx": math.cos(angle) * speed,
                        "vy": math.sin(angle) * speed,
                        "size": random.uniform(4, 10) * self.zoom,
                        "life": lifetime,
                        "max_life": lifetime,
                        "color": color,
                        "alpha": 1.0,
                    })
        
        # ─── 6. Trigger screen flash (scaled by node kind) ───
        self.screen_flash_alpha = screen_flash_intensity
        self.screen_flash_timer = 0.5 if kind in ("keystone", "core") else 0.4
    
    def _hsv_to_rgb(self, h, s, v):
        """Convert HSV color to RGB tuple."""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))
    
    def _update_particles(self, dt):
        """Update floating particle positions for ambient effect."""
        for p in self.particles:
            p["x"] += p["speed_x"] * dt * 60
            p["y"] += p["speed_y"] * dt * 60
            # Wrap particles that drift too far
            if p["y"] < -650:
                p["y"] = 650
                p["x"] = random.uniform(-700, 700)
            if p["x"] < -750:
                p["x"] = 750
            elif p["x"] > 750:
                p["x"] = -750
        
        # Update unlock effects
        self._update_unlock_effects(dt)
        
        # Update entrance animation
        self._update_entrance(dt)
    
    def _update_unlock_effects(self, dt):
        """Update all active unlock animation effects."""
        to_remove = []
        
        # Update screen flash
        if self.screen_flash_timer > 0:
            self.screen_flash_timer -= dt
            self.screen_flash_alpha *= 0.92  # exponential fade
            if self.screen_flash_timer <= 0:
                self.screen_flash_alpha = 0
                self.screen_flash_timer = 0
        
        for effect in self.unlock_effects:
            effect_type = effect.get("type")
            
            if effect_type == "burst":
                # Move particle
                effect["x"] += effect["vx"] * dt
                effect["y"] += effect["vy"] * dt
                # Apply drag
                effect["vx"] *= 0.97
                effect["vy"] *= 0.97
                # Add gravity for sparkle effect
                effect["vy"] += 20 * dt * self.zoom
                # Decrease life
                effect["life"] -= dt
                effect["alpha"] = effect["life"] / effect["max_life"]
                if effect["life"] <= 0:
                    to_remove.append(effect)
            
            elif effect_type == "shockwave":
                # Expand ring
                effect["radius"] += effect["speed"] * dt
                effect["life"] -= dt
                progress = 1.0 - (effect["life"] / effect["max_life"])
                effect["alpha"] = 0.9 * (1.0 - progress)
                effect["width"] = max(1, int(3 * (1.0 - progress * 0.7)))
                if effect["life"] <= 0:
                    to_remove.append(effect)
            
            elif effect_type == "link_light":
                # Traveling light along the link
                effect["progress"] += dt * effect["speed"]
                effect["alpha"] = 1.0 - effect["progress"]
                if effect["progress"] >= 1.0:
                    to_remove.append(effect)
            
            elif effect_type == "float_text":
                # Float upward
                effect["y"] += effect["speed_y"] * dt
                effect["life"] -= dt
                progress = 1.0 - (effect["life"] / effect["max_life"])
                effect["alpha"] = 1.0 - progress  # fade out
                # Scale up slightly
                effect["size"] += 2 * dt
                if effect["life"] <= 0:
                    to_remove.append(effect)
            
            elif effect_type == "spiral_particle":
                # Spiral outward from center
                effect["radius"] += effect["speed"] * dt
                effect["angle"] += effect["angular_speed"] * dt
                effect["life"] -= dt
                progress = 1.0 - (effect["life"] / effect["max_life"])
                effect["alpha"] = 1.0 - progress
                # Update position based on spiral
                effect["x"] = effect.get("start_x", effect["x"]) + math.cos(effect["angle"]) * effect["radius"]
                effect["y"] = effect.get("start_y", effect["y"]) + math.sin(effect["angle"]) * effect["radius"]
                if effect["life"] <= 0:
                    to_remove.append(effect)
            
            elif effect_type == "light_beam":
                # Extend beam outward
                effect["length"] = min(effect["max_length"], effect["length"] + effect["speed"] * dt)
                effect["life"] -= dt
                progress = 1.0 - (effect["life"] / effect["max_life"])
                effect["alpha"] = 0.8 * (1.0 - progress)
                if effect["life"] <= 0:
                    to_remove.append(effect)
            
            elif effect_type == "pulse_ring":
                # Expand ring with pulse
                effect["radius"] = min(effect["max_radius"], effect["radius"] + effect["pulse_speed"] * dt)
                effect["life"] -= dt
                progress = 1.0 - (effect["life"] / effect["max_life"])
                effect["alpha"] = 0.6 * (1.0 - progress)
                if effect["life"] <= 0:
                    to_remove.append(effect)
        
        # Remove expired effects
        for effect in to_remove:
            if effect in self.unlock_effects:
                self.unlock_effects.remove(effect)
    
    def _draw_unlock_effects(self, surface):
        """Draw all active unlock animation effects."""
        for effect in self.unlock_effects:
            effect_type = effect.get("type")
            
            if effect_type == "burst":
                alpha = int(255 * effect["alpha"])
                if alpha <= 0:
                    continue
                color = effect["color"]
                r, g, b = color[:3]
                # Fade to white as it fades
                fade = alpha / 255
                dr = int(r * fade + 255 * (1 - fade))
                dg = int(g * fade + 255 * (1 - fade))
                db = int(b * fade + 255 * (1 - fade))
                clr = (dr, dg, db, alpha)
                size = max(1, effect["size"] * effect["alpha"])
                pos = (int(effect["x"]), int(effect["y"]))
                if self.tree_rect.collidepoint(pos):
                    pygame.draw.circle(surface, clr[:3], pos, int(size))
            
            elif effect_type == "shockwave":
                alpha = int(255 * effect["alpha"])
                if alpha <= 0:
                    continue
                color = effect["color"]
                r, g, b = color[:3]
                clr = (r, g, b)
                pos = (int(effect["x"]), int(effect["y"]))
                radius = int(effect["radius"])
                # Draw multiple rings for a glow effect
                for w in range(effect["width"], 0, -1):
                    ring_alpha = alpha // (effect["width"] - w + 1) if w > 0 else alpha
                    offset = w * 3
                    adj_alpha = max(0, ring_alpha - offset * 10)
                    if adj_alpha > 0:
                        t_clr = tuple(max(0, min(255, (c + adj_alpha) if i == 0 else c)) for i, c in enumerate(color))
                        pygame.draw.circle(surface, color, pos, radius + offset, max(1, w))
            
            elif effect_type == "link_light":
                alpha = int(255 * effect["alpha"])
                if alpha <= 0:
                    continue
                progress = effect["progress"]
                x = effect["x1"] + (effect["x2"] - effect["x1"]) * progress
                y = effect["y1"] + (effect["y2"] - effect["y1"]) * progress
                color = effect["color"]
                size = int(effect["size"] * (0.5 + 0.5 * math.sin(progress * math.pi)))
                # Draw glow ball
                glow_size = size * 3
                for i in range(3):
                    glow_alpha = alpha // (2 ** i + 1)
                    glow_r = max(1, glow_size - i * 4)
                    gc = tuple(max(0, min(255, c)) for c in color)
                    pygame.draw.circle(surface, gc, (int(x), int(y)), glow_r)
                pygame.draw.circle(surface, (255, 255, 255), (int(x), int(y)), size)
            
            elif effect_type == "float_text":
                alpha = int(255 * effect["alpha"])
                if alpha <= 0:
                    continue
                font = cfg.get_font(max(12, int(effect["size"])))
                text_surf = font.render(effect["text"], True, effect["color"])
                text_surf.set_alpha(alpha)
                pos = (int(effect["x"] - text_surf.get_width() // 2), int(effect["y"]))
                # Draw shadow for readability
                shadow = font.render(effect["text"], True, (0, 0, 0))
                shadow.set_alpha(alpha // 2)
                surface.blit(shadow, (pos[0] + 2, pos[1] + 2))
                surface.blit(text_surf, pos)
            
            elif effect_type == "spiral_particle":
                alpha = int(255 * effect["alpha"])
                if alpha <= 0:
                    continue
                color = effect["color"]
                size = max(1, int(effect["size"] * effect["alpha"]))
                pos = (int(effect["x"]), int(effect["y"]))
                # Draw glow
                glow_r = size * 3
                glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                glow_a = alpha // 3
                pygame.draw.circle(glow_surf, (*color, glow_a), (glow_r, glow_r), glow_r)
                surface.blit(glow_surf, (pos[0] - glow_r, pos[1] - glow_r))
                # Draw core
                bright = tuple(min(255, c + 60) for c in color)
                pygame.draw.circle(surface, bright, pos, size)
            
            elif effect_type == "light_beam":
                alpha = int(255 * effect["alpha"])
                if alpha <= 0:
                    continue
                color = effect["color"]
                # Draw beam as a line from center outward
                end_x = effect["x"] + math.cos(effect["angle"]) * effect["length"]
                end_y = effect["y"] + math.sin(effect["angle"]) * effect["length"]
                # Draw glow layer
                glow_color = tuple(max(0, min(255, c)) for c in color)
                pygame.draw.line(surface, glow_color, (int(effect["x"]), int(effect["y"])), (int(end_x), int(end_y)), max(1, int(effect["width"] * 2)))
                # Draw bright core
                bright = tuple(min(255, c + 80) for c in color)
                pygame.draw.line(surface, bright, (int(effect["x"]), int(effect["y"])), (int(end_x), int(end_y)), max(1, int(effect["width"])))
            
            elif effect_type == "pulse_ring":
                alpha = int(255 * effect["alpha"])
                if alpha <= 0:
                    continue
                color = effect["color"]
                radius = int(effect["radius"])
                if radius > 0:
                    # Draw multiple rings for glow effect
                    for w in range(3):
                        ring_alpha = alpha // (w + 1)
                        ring_color = tuple(max(0, min(255, c)) for c in color)
                        pygame.draw.circle(surface, ring_color, (int(effect["x"]), int(effect["y"])), radius + w * 2, max(1, int(effect["width"])))
        
        # Draw screen flash (light overlay)
        if self.screen_flash_alpha > 0.01:
            flash = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            alpha_val = int(255 * self.screen_flash_alpha)
            flash.fill((255, 255, 255, alpha_val))
            surface.blit(flash, (0, 0))

    def _draw_tree_background(self, surface):
        """Draw enhanced background with concentric rings, twinkling stars, and particles."""
        origin = pygame.Vector2(self.tree_rect.center) + self.pan_offset
        t = self.animation_time
        
        # During entrance, star visibility is controlled by entrance_star_alpha
        star_alpha_mult = self.entrance_star_alpha if self.entrance_active else 1.0

        # Draw subtle radial gradient background using concentric circles
        for r in range(700, 0, -8):
            brightness = max(12, 22 - r // 50)
            # During entrance, dim the background until stars fade in
            if self.entrance_active and self.entrance_phase < 2:
                brightness = int(brightness * star_alpha_mult)
            pygame.draw.circle(surface, (brightness, brightness, brightness + 4), origin, int(r * self.zoom), 0)

        # Draw concentric guide rings with subtle pulse
        ring_radii = [130, 210, 310, 330, 460, 580]
        for idx, radius in enumerate(ring_radii):
            pulse = math.sin(t * 0.5 + idx * 0.8) * 0.15 + 0.85
            c = int(28 * pulse)
            if self.entrance_active and self.entrance_phase < 2:
                c = int(c * star_alpha_mult)
            pygame.draw.circle(surface, (c, c, c + 8), origin, int(radius * self.zoom), 1)

        # Draw twinkling stars (fade in during entrance phase 1+)
        for star_data in self.background_points:
            x, y, size, phase, speed = star_data
            pos = origin + pygame.Vector2(x, y) * self.zoom
            if self.tree_rect.collidepoint(pos):
                twinkle = (math.sin(t * speed + phase) + 1.0) * 0.5
                brightness = int((25 + 35 * twinkle) * star_alpha_mult)
                star_color = (brightness, brightness, brightness + 12)
                pygame.draw.circle(surface, star_color, (int(pos.x), int(pos.y)), size)

        # Draw floating particles (fade in during entrance)
        for p in self.particles:
            pos = origin + pygame.Vector2(p["x"], p["y"]) * self.zoom
            if self.tree_rect.collidepoint(pos):
                pulse = (math.sin(t * p["pulse_speed"]) + 1.0) * 0.5
                alpha = p["alpha"] * (0.4 + 0.6 * pulse) * star_alpha_mult
                r, g, b = p["color"]
                pcolor = (int(r * alpha), int(g * alpha), int(b * alpha))
                sz = max(1, int(p["size"] * self.zoom * (0.8 + 0.4 * pulse)))
                pygame.draw.circle(surface, pcolor, (int(pos.x), int(pos.y)), sz)

    def _draw_links(self, surface, unlocked, revealed_filter=None):
        """Draw links with glow effect for active (unlocked) connections.
        
        Args:
            revealed_filter: If provided, only draw links where both nodes are in this set.
        """
        t = self.animation_time
        for a, b in self.links:
            node_a = self.nodes_by_id.get(a)
            node_b = self.nodes_by_id.get(b)
            if node_a is None or node_b is None:
                continue
            # During entrance animation, only draw links where both nodes have been revealed
            if revealed_filter is not None:
                if a not in revealed_filter or b not in revealed_filter:
                    continue
            pos_a = self._node_screen_pos(node_a)
            pos_b = self._node_screen_pos(node_b)
            active = a in unlocked and b in unlocked

            if active:
                # Determine branch color for the link
                branch = node_a.get("branch") or node_b.get("branch")
                if branch and branch in self.BRANCH_THEMES:
                    theme = self.BRANCH_THEMES[branch]
                    glow_color = theme["glow"]
                    base_color = theme["secondary"]
                else:
                    glow_color = (140, 180, 220)
                    base_color = (120, 160, 200)

                # Animated pulse for active links
                pulse = (math.sin(t * 2.0) + 1.0) * 0.5
                glow_alpha = 0.3 + 0.2 * pulse

                # Draw glow (wider, semi-transparent line underneath)
                glow_r = int(glow_color[0] * glow_alpha)
                glow_g = int(glow_color[1] * glow_alpha)
                glow_b = int(glow_color[2] * glow_alpha)
                pygame.draw.line(surface, (glow_r, glow_g, glow_b), pos_a, pos_b, max(3, int(5 * self.zoom)))

                # Draw main line
                pygame.draw.line(surface, base_color, pos_a, pos_b, max(1, int(2 * self.zoom)))
            else:
                # Inactive links — dim
                pygame.draw.line(surface, (48, 48, 58), pos_a, pos_b, max(1, int(1.5 * self.zoom)))

    def _draw_nodes(self, surface, unlocked, revealed_filter=None):
        """Draw nodes with glow halos, pulsing effects, and inner highlights.
        
        Args:
            revealed_filter: If provided, only draw nodes that are in this set.
        """
        t = self.animation_time
        for node in self.nodes:
            node_id = node["id"]
            # During entrance animation, only draw nodes that have been revealed
            if revealed_filter is not None and node_id not in revealed_filter:
                continue
            pos = self._node_screen_pos(node)
            radius = max(4, int(node["size"] * self.zoom))
            is_unlocked = node_id in unlocked
            is_selected = node_id == self.selected_node_id
            is_hovered = node_id == self.hovered_node_id
            kind = node["kind"]
            branch = node.get("branch")

            # Determine colors
            if is_unlocked:
                fill = node["color"]
                accent = node["accent"]
            else:
                fill = (38, 38, 46)
                accent = (70, 75, 90)

            # ── Glow halo for unlocked nodes ──
            if is_unlocked and branch and branch in self.BRANCH_THEMES:
                glow_color = self.BRANCH_THEMES[branch]["glow"]
                pulse = (math.sin(t * 1.5 + hash(node_id) * 0.1) + 1.0) * 0.5
                glow_radius = radius + int((6 + 4 * pulse) * self.zoom)
                glow_alpha = 0.15 + 0.1 * pulse

                # Draw multiple glow rings for soft effect
                for ring in range(3):
                    r_off = ring * int(3 * self.zoom)
                    alpha_factor = glow_alpha * (1.0 - ring * 0.3)
                    gc = tuple(max(0, min(255, int(c * alpha_factor))) for c in glow_color)
                    pygame.draw.circle(surface, gc, (int(pos.x), int(pos.y)), glow_radius + r_off, 1)

            # ── Core node special effect: rotating ring ──
            if kind == "core" and is_unlocked:
                core_pulse = (math.sin(t * 1.2) + 1.0) * 0.5
                core_glow_r = radius + int((10 + 6 * core_pulse) * self.zoom)
                for ring in range(4):
                    r_off = ring * int(3 * self.zoom)
                    alpha = 0.2 * (1.0 - ring * 0.2) * (0.7 + 0.3 * core_pulse)
                    gc = (int(100 * alpha), int(160 * alpha), int(255 * alpha))
                    pygame.draw.circle(surface, gc, (int(pos.x), int(pos.y)), core_glow_r + r_off, 1)

                # Draw rotating decorative arcs around core
                for i in range(6):
                    arc_angle = t * 0.8 + i * math.pi / 3
                    arc_x = pos.x + math.cos(arc_angle) * (radius + 8) * self.zoom
                    arc_y = pos.y + math.sin(arc_angle) * (radius + 8) * self.zoom
                    dot_r = max(2, int(2 * self.zoom))
                    pygame.draw.circle(surface, (180, 210, 255), (int(arc_x), int(arc_y)), dot_r)

            # ── Keystone special effect: diamond shape indicator ──
            if kind == "keystone" and is_unlocked:
                ks_pulse = (math.sin(t * 1.8 + hash(node_id) * 0.2) + 1.0) * 0.5
                ks_glow_r = radius + int((8 + 5 * ks_pulse) * self.zoom)
                glow_color = node.get("color", (200, 100, 100))
                for ring in range(3):
                    r_off = ring * int(3 * self.zoom)
                    alpha = 0.25 * (1.0 - ring * 0.25) * (0.6 + 0.4 * ks_pulse)
                    gc = tuple(max(0, min(255, int(c * alpha))) for c in glow_color)
                    pygame.draw.circle(surface, gc, (int(pos.x), int(pos.y)), ks_glow_r + r_off, 1)

            # ── Draw main node circle ──
            pygame.draw.circle(surface, fill, (int(pos.x), int(pos.y)), radius)

            # ── Inner highlight (lighter center for 3D effect) ──
            if is_unlocked and radius > 5:
                inner_r = max(2, radius // 2)
                highlight = tuple(min(255, c + 40) for c in fill)
                pygame.draw.circle(surface, highlight, (int(pos.x - radius * 0.15), int(pos.y - radius * 0.15)), inner_r)

            # ── Border ──
            border_width = 2 if kind in ("core", "keystone", "major") else 1
            pygame.draw.circle(surface, accent, (int(pos.x), int(pos.y)), radius, border_width)

            # ── Selection ring (animated pulse) ──
            if is_selected:
                sel_pulse = (math.sin(t * 3.0) + 1.0) * 0.5
                sel_r = radius + int((5 + 3 * sel_pulse) * self.zoom)
                sel_color = (
                    int(200 + 55 * sel_pulse),
                    int(200 + 55 * sel_pulse),
                    255,
                )
                pygame.draw.circle(surface, sel_color, (int(pos.x), int(pos.y)), sel_r, 2)
                # Second outer ring
                sel_r2 = sel_r + int(3 * self.zoom)
                sel_alpha = 0.4 + 0.3 * sel_pulse
                sel_color2 = (int(180 * sel_alpha), int(180 * sel_alpha), int(255 * sel_alpha))
                pygame.draw.circle(surface, sel_color2, (int(pos.x), int(pos.y)), sel_r2, 1)
            elif is_hovered:
                hover_r = radius + int(4 * self.zoom)
                pygame.draw.circle(surface, (180, 180, 210), (int(pos.x), int(pos.y)), hover_r, 1)

            # ── Unlockable indicator: dotted ring for nodes that can be unlocked ──
            if not is_unlocked and node_id != "core":
                adjacent_unlocked = bool(self._get_adjacent_nodes(node_id) & unlocked)
                if adjacent_unlocked:
                    can_pulse = (math.sin(t * 2.5) + 1.0) * 0.5
                    can_r = radius + int(4 * self.zoom)
                    can_color = (
                        int(80 + 60 * can_pulse),
                        int(120 + 60 * can_pulse),
                        int(80 + 60 * can_pulse),
                    )
                    pygame.draw.circle(surface, can_color, (int(pos.x), int(pos.y)), can_r, 1)

            # ── Labels for important nodes ──
            if kind in ("core", "major", "keystone"):
                label_color = (235, 235, 245) if is_unlocked else (160, 160, 175)
                label = self.small_font.render(node["name"], True, label_color)
                label_rect = label.get_rect(center=(pos.x, pos.y - radius - int(14 * self.zoom)))
                # Draw label background for readability
                bg_pad = 3
                bg_rect = label_rect.inflate(bg_pad * 2, bg_pad)
                bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
                bg_surface.fill((16, 16, 22, 160))
                surface.blit(bg_surface, bg_rect)
                surface.blit(label, label_rect)

    def _draw_sidebar(self, screen, selected_node):
        pygame.draw.rect(screen, (24, 24, 30), self.sidebar_rect, border_radius=18)
        pygame.draw.rect(screen, (82, 82, 96), self.sidebar_rect, 2, border_radius=18)

        title = self.title_font.render(_("Skill Tree"), True, (235, 235, 245))
        screen.blit(title, (self.sidebar_rect.x + 18, self.sidebar_rect.y + 18))

        hint_text = _("Wheel: zoom. Right mouse: pan. Left click: inspect.")
        hint_lines = self._wrap_text(hint_text, self.small_font, self.sidebar_rect.width - 36)
        y = self.sidebar_rect.y + 70
        for line in hint_lines:
            hint = self.small_font.render(line, True, (190, 190, 200))
            screen.blit(hint, (self.sidebar_rect.x + 18, y))
            y += hint.get_height() + 4

        character = self._character()
        points = getattr(character, "skill_tree_points", 0) if character else 0
        points_text = self.section_font.render(f"{_('Points')}: {points}", True, (235, 235, 245))
        screen.blit(points_text, (self.sidebar_rect.x + 18, y + 10))
        y += points_text.get_height() + 18

        if selected_node is None:
            return

        name = self.section_font.render(selected_node["name"], True, (235, 235, 245))
        screen.blit(name, (self.sidebar_rect.x + 18, y))
        y += name.get_height() + 8

        kind_map = {
            "core": _("Core"),
            "minor": _("Minor"),
            "major": _("Notable"),
            "keystone": _("Keystone"),
        }
        kind = kind_map.get(selected_node.get("kind"), _("Unknown"))
        kind_text = self.small_font.render(f"{_('Type')}: {kind}", True, (210, 210, 220))
        screen.blit(kind_text, (self.sidebar_rect.x + 18, y))
        y += kind_text.get_height() + 6

        unlocked = self._get_unlocked_nodes()
        status_label = _("Unlocked") if selected_node["id"] in unlocked else _("Locked")
        status_text = self.small_font.render(f"{_('Status')}: {status_label}", True, (210, 210, 220))
        screen.blit(status_text, (self.sidebar_rect.x + 18, y))
        y += status_text.get_height() + 8

        effect_label = f"{_('Effect')}: {selected_node['effect']}"
        effect_lines = self._wrap_text(effect_label, self.small_font, self.sidebar_rect.width - 36)
        for line in effect_lines:
            line_surf = self.small_font.render(line, True, (210, 210, 220))
            screen.blit(line_surf, (self.sidebar_rect.x + 18, y))
            y += line_surf.get_height() + 4

        note_text = _("Effects are placeholders and do not apply yet.")
        note_lines = self._wrap_text(note_text, self.small_font, self.sidebar_rect.width - 36)
        y += 6
        for line in note_lines:
            line_surf = self.small_font.render(line, True, (180, 180, 190))
            screen.blit(line_surf, (self.sidebar_rect.x + 18, y))
            y += line_surf.get_height() + 4

        # Update unlock button state and text
        if selected_node is None:
            self.unlock_button.set_text("")
        else:
            kind = selected_node.get("kind")
            # cost mapping: minor(normal)=1, major(notable)=2, keystone(best)=3
            cost_map = {"minor": 1, "major": 2, "keystone": 3, "core": 0}
            cost = cost_map.get(kind, 1)
            if selected_node["id"] in unlocked or cost == 0:
                self.unlock_button.set_text(_("Unlocked"))
            else:
                self.unlock_button.set_text(f"{_('Unlock')} ({cost})")

    def draw(self, screen: pygame.Surface):
        self.layout(screen)

        # Update animation time using pygame clock
        dt = 0.016  # Default ~60fps delta
        try:
            dt = self.app.clock.get_time() / 1000.0 if hasattr(self.app, 'clock') else 0.016
        except Exception:
            pass
        
        # Update rotation only if no node is selected and entrance animation is not active
        if self.selected_node_id is None and not self.entrance_active:
            self.rotation_angle += dt * 0.15  # Slow rotation (~8.6 degrees per second)
        
        # Smoothly interpolate zoom and pan towards targets
        lerp_speed = 6.0 * dt
        self.zoom += (self.target_zoom - self.zoom) * lerp_speed
        self.pan_offset.x += (self.target_pan_offset.x - self.pan_offset.x) * lerp_speed
        self.pan_offset.y += (self.target_pan_offset.y - self.pan_offset.y) * lerp_speed
        
        self.animation_time += dt
        self._update_particles(dt)

        # Dark background fill
        screen.fill((10, 10, 16))
        
        # During entrance phase 0 (void), draw almost nothing — just a dark screen
        # The tree area border fades in during phase 1
        entrance_border_alpha = 1.0
        if self.entrance_active and self.entrance_phase <= 1:
            if self.entrance_phase == 0:
                entrance_border_alpha = 0.0
            elif self.entrance_phase == 1:
                entrance_border_alpha = min(1.0, self.entrance_phase_time / 0.8)
        
        # Draw tree area background with subtle gradient border
        border_color = (18, 18, 24)
        if entrance_border_alpha < 1.0:
            border_color = tuple(int(c * entrance_border_alpha) for c in border_color)
        pygame.draw.rect(screen, border_color, self.tree_rect, border_radius=18)
        
        # Decorative double border (fades in)
        if entrance_border_alpha > 0.1:
            outer_border = tuple(int(c * entrance_border_alpha) for c in (55, 55, 72))
            pygame.draw.rect(screen, outer_border, self.tree_rect, 2, border_radius=18)
            inner_border = tuple(int(c * entrance_border_alpha) for c in (35, 35, 48))
            inner_rect = self.tree_rect.inflate(-4, -4)
            pygame.draw.rect(screen, inner_border, inner_rect, 1, border_radius=16)

        old_clip = screen.get_clip()
        screen.set_clip(self.tree_rect)
        
        # Draw background — during entrance, star alpha is controlled by the animation
        self._draw_tree_background(screen)

        # During entrance, only draw links/nodes that have been revealed
        unlocked = self._get_unlocked_nodes()
        
        # Determine if we should hide normal tree rendering during early entrance phases
        hide_tree = self.entrance_active and self.entrance_phase < 3
        
        # During entrance animation (phase 3+), use entrance_revealed_nodes to filter
        # which nodes/links are drawn, making the tree appear gradually during BFS
        use_entrance_filter = self.entrance_active and self.entrance_phase >= 3 and self.entrance_phase < 6
        
        if not hide_tree:
            # Determine the revealed filter for entrance animation
            revealed_filter = self.entrance_revealed_nodes if use_entrance_filter else None
            
            # Normal link and node drawing (after core ignition, nodes are revealed by entrance)
            self._draw_links(screen, unlocked, revealed_filter=revealed_filter)

            mouse_pos = pygame.mouse.get_pos()
            self.hovered_node_id = self._hit_test_node(mouse_pos)
            self._draw_nodes(screen, unlocked, revealed_filter=revealed_filter)
        else:
            # During early entrance, still allow hover detection but don't draw normal nodes
            mouse_pos = pygame.mouse.get_pos()
            self.hovered_node_id = None  # No hover during entrance
        
        # Draw entrance animation effects (vortex, sparks, core ignition, branch growth)
        self._draw_entrance_sparks(screen)
        
        # Draw unlock animation effects on top of everything
        self._draw_unlock_effects(screen)
        
        screen.set_clip(old_clip)

        # Draw node count info in bottom-left of tree area (fade in after entrance)
        if not self.entrance_active or self.entrance_phase >= 5:
            total_nodes = len(self.nodes)
            unlocked_count = len(unlocked)
            info_text = self.small_font.render(
                f"{unlocked_count}/{total_nodes} nodes", True, (100, 100, 120)
            )
            screen.blit(info_text, (self.tree_rect.x + 12, self.tree_rect.bottom - info_text.get_height() - 8))

        selected_node = self.nodes_by_id.get(self.selected_node_id)
        self._draw_sidebar(screen, selected_node)
        # draw sidebar buttons
        try:
            self.unlock_button.draw(screen)
        except Exception:
            pass
        self.exit_button.draw(screen)

        # Draw dialog on top if one is active
        if getattr(self.app, 'current_dialog', None):
            try:
                self.app.current_dialog.draw(screen)
            except Exception:
                pass