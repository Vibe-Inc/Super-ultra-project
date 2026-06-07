import random
import math
import pygame
import pytmx
from enum import Enum
from src.core.logger import logger
import src.config as cfg

# Translatable string helper (fallback to identity if not initialized)
try:
    from src.i18n import _
except ImportError:
    def _(text): return text

class WeatherState(Enum):
    CLEAR = 0
    RAIN = 1
    STORM = 2
    FOG = 3

class WeatherSystem:
    def __init__(self, game_state):
        self.game = game_state
        self.current_weather = WeatherState.CLEAR
        
        # Weather cycle settings
        self.weather_duration = 300.0  # 5 minutes in real-time seconds
        self.weather_timer = self.weather_duration
        
        # Rain particles: 3-layer parallax (0=background, 1=midground, 2=foreground)
        self.rain_particles = []  # dicts: {x, y, speed, len, width, alpha, layer}
        self.max_rain_particles = 120
        
        # Rain splashes (screen-space)
        self.splashes = []  # dicts: {x, y, radius, max_radius, alpha}
        
        # Rain puddles (world-space) - Capped to 8 max for clean visual flow
        self.puddles = []  # dicts: {pos: Vector2, radius, max_radius, alpha, ripples: list}
        self.max_puddles = 8
        self.puddle_spawn_timer = 0.0
        
        # Pre-cache soft fog cloud surfaces for optimization and beauty
        self.fog_surfaces = []
        self._precache_fog_surfaces()
        
        # Fog clouds list
        self.fog_clouds = []  # dicts: {x, y, vx, vy, size_idx, alpha, pulse_speed, pulse_offset}
        self._init_fog_clouds()
        
        # Small fog particles for extra detail
        self.fog_particles = []
        
        # Lightning / Thunder settings
        self.lightning_flash_time = 0.0
        self.lightning_flash_max = 0.0
        self.lightning_flash_intensity = 0.0
        self.flash_sequence = []  # list of dicts for double-strobe effect
        self.lightning_timer = random.uniform(15.0, 30.0)
        self.lightning_strike_pos = None  # World position
        self.lightning_strike_timer = 0.0
        self.lightning_branches = []  # side branches of lightning bolt

    def _precache_fog_surfaces(self):
        """Create a cache of soft radial fog clouds so we don't draw slow vector circles at runtime."""
        self.fog_surfaces = []
        sizes = [450, 600, 800]
        for size in sizes:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            cx, cy = size // 2, size // 2
            # Draw concentric circles with quad-fading transparency
            for r in range(cx, 0, -5):
                frac = r / cx
                # Quad-fade creates a very soft cloud-like edge
                alpha = int((1.0 - frac) * (1.0 - frac) * 35)
                if alpha > 0:
                    pygame.draw.circle(surf, (225, 235, 245, alpha), (cx, cy), r)
            self.fog_surfaces.append(surf)

    def _init_fog_clouds(self):
        self.fog_clouds = []
        # 10 large drifting volumetric clouds
        for _ in range(10):
            self.fog_clouds.append({
                'x': random.uniform(-100, cfg.SCREEN_WIDTH + 100),
                'y': random.uniform(-100, cfg.SCREEN_HEIGHT + 100),
                'vx': random.uniform(8, 18),
                'vy': random.uniform(-4, 4),
                'size_idx': random.choice([0, 1, 2]),
                'alpha_mult': random.uniform(0.7, 1.3),
                'pulse_speed': random.uniform(0.3, 0.8),
                'pulse_offset': random.uniform(0, math.pi * 2)
            })

    def is_indoors(self) -> bool:
        """Returns True if the player is currently inside an indoor area."""
        return getattr(self.game, 'current_map_path', '') == "maps/tavern.tmx"

    def change_weather(self, state: WeatherState):
        if self.current_weather == state:
            return
        logger.info(f"Weather changing from {self.current_weather.name} to {state.name}")
        self.current_weather = state
        self.weather_timer = self.weather_duration
        
        # Clean up some states
        if state != WeatherState.STORM:
            self.lightning_flash_time = 0.0
            self.flash_sequence.clear()
            self.lightning_strike_pos = None
            
        # Evaporate puddles when clearing
        if state == WeatherState.CLEAR or state == WeatherState.FOG:
            for puddle in self.puddles:
                puddle['evaporating'] = True
        else:
            for puddle in self.puddles:
                puddle['evaporating'] = False

        self.apply_weather_gameplay_effects()

    def cycle_weather(self):
        states = list(WeatherState)
        idx = (states.index(self.current_weather) + 1) % len(states)
        self.change_weather(states[idx])

    def apply_weather_gameplay_effects(self):
        """Update movement speeds and enemy detection ranges based on weather."""
        if self.is_indoors():
            speed_mult = 1.0
            detect_mult = 1.0
        else:
            if self.current_weather == WeatherState.RAIN:
                speed_mult = 0.90  # 10% slow
                detect_mult = 0.90  # 10% reduced sight
            elif self.current_weather == WeatherState.STORM:
                speed_mult = 0.85  # 15% slow
                detect_mult = 0.80  # 20% reduced sight
            elif self.current_weather == WeatherState.FOG:
                speed_mult = 1.0
                detect_mult = 0.70  # 30% reduced sight (sneaking advantage!)
            else:
                speed_mult = 1.0
                detect_mult = 1.0

        # Apply to player character
        if hasattr(self.game, 'character') and self.game.character:
            self.game.character.weather_speed_multiplier = speed_mult

        # Apply to all enemies
        if hasattr(self.game, 'enemies') and self.game.enemies:
            for enemy in self.game.enemies:
                enemy.weather_speed_multiplier = speed_mult
                base_range = getattr(enemy, 'base_detection_range', enemy.detection_range)
                enemy.detection_range = base_range * detect_mult

    def update(self, dt: float):
        self.weather_timer -= dt
        if self.weather_timer <= 0:
            roll = random.random()
            if roll < 0.50:
                self.change_weather(WeatherState.CLEAR)
            elif roll < 0.70:
                self.change_weather(WeatherState.RAIN)
            elif roll < 0.85:
                self.change_weather(WeatherState.STORM)
            else:
                self.change_weather(WeatherState.FOG)

        self.apply_weather_gameplay_effects()

        if self.is_indoors():
            self.rain_particles.clear()
            self.splashes.clear()
            self.puddles.clear()
            self.fog_particles.clear()
            return

        self._update_rain(dt)
        self._update_puddles(dt)
        self._update_fog(dt)
        self._update_lightning(dt)

    def _update_rain(self, dt: float):
        is_raining = self.current_weather in (WeatherState.RAIN, WeatherState.STORM)
        self.max_rain_particles = 240 if self.current_weather == WeatherState.STORM else 100
        
        # Spawn rain particles with layered depth
        if is_raining and len(self.rain_particles) < self.max_rain_particles:
            spawn_count = min(20, self.max_rain_particles - len(self.rain_particles))
            for _ in range(spawn_count):
                # Randomly assign depth layer (0=back, 1=mid, 2=front)
                layer = random.choices([0, 1, 2], weights=[0.5, 0.35, 0.15])[0]
                
                if layer == 0:  # Background: small, slow, faded
                    speed = random.uniform(650, 850)
                    length = random.uniform(10, 15)
                    width = 1.0
                    alpha = random.uniform(60, 100)
                elif layer == 1:  # Midground: normal
                    speed = random.uniform(950, 1150)
                    length = random.uniform(18, 28)
                    width = 2.0
                    alpha = random.uniform(110, 150)
                else:  # Foreground: large, thick, fast
                    speed = random.uniform(1300, 1600)
                    length = random.uniform(32, 45)
                    width = 3.2
                    alpha = random.uniform(150, 200)

                self.rain_particles.append({
                    'x': random.uniform(-100, cfg.SCREEN_WIDTH + 100),
                    'y': random.uniform(-50, 0),
                    'speed': speed,
                    'len': length,
                    'width': width,
                    'alpha': alpha,
                    'layer': layer
                })

        # Update rain particles (wind wobbles angle slightly over time)
        time_sec = pygame.time.get_ticks() * 0.001
        base_wind = 220.0 if self.current_weather == WeatherState.STORM else 60.0
        wind_wobble = math.sin(time_sec * 0.8) * 30.0
        wind = base_wind + wind_wobble

        for p in self.rain_particles[:]:
            p['x'] += wind * (p['speed'] / 1000.0) * dt  # parallax wind
            p['y'] += p['speed'] * dt
            if p['y'] > cfg.SCREEN_HEIGHT:
                self.rain_particles.remove(p)
                # Foreground and midground particles make splashes
                if p['layer'] > 0 and random.random() < 0.35:
                    self.splashes.append({
                        'x': p['x'],
                        'y': cfg.SCREEN_HEIGHT - random.uniform(0, 12),
                        'radius': 1.0,
                        'max_radius': random.uniform(5, 10) if p['layer'] == 2 else random.uniform(3, 6),
                        'alpha': p['alpha'] * 0.8
                    })

        # Update splashes
        for s in self.splashes[:]:
            s['radius'] += 18.0 * dt
            s['alpha'] -= 300 * dt
            if s['alpha'] <= 0 or s['radius'] >= s['max_radius']:
                self.splashes.remove(s)

    def _update_puddles(self, dt: float):
        is_raining = self.current_weather in (WeatherState.RAIN, WeatherState.STORM)
        
        # Spawn puddles - limited to max_puddles (8) to be "not so many" and optimized
        if is_raining and len(self.puddles) < self.max_puddles:
            self.puddle_spawn_timer += dt
            if self.puddle_spawn_timer >= 2.0:
                self.puddle_spawn_timer = 0.0
                player = self.game.character
                
                for _ in range(30):
                    px = player.pos.x + random.uniform(-500, 500)
                    py = player.pos.y + random.uniform(-350, 350)
                    
                    map_w = cfg.SCREEN_WIDTH
                    map_h = cfg.SCREEN_HEIGHT
                    if self.game.map.current_map:
                        map_w = self.game.map.current_map.pixel_width
                        map_h = self.game.map.current_map.pixel_height
                    
                    px = max(50, min(px, map_w - 50))
                    py = max(50, min(py, map_h - 50))

                    # Bounding box collision check (30x16)
                    p_radius = 28.0
                    puddle_rect = pygame.Rect(px - p_radius, py - p_radius / 2, p_radius * 2, p_radius)
                    if puddle_rect.collidelist(self.game.obstacles) != -1:
                        continue

                    # Tile Layer check
                    if self.game.map.current_map and self.game.map.current_map.game_map:
                        tmx_data = self.game.map.current_map.game_map
                        tile_x = int(px // tmx_data.tilewidth)
                        tile_y = int(py // tmx_data.tileheight)
                        
                        if not (0 <= tile_x < tmx_data.width and 0 <= tile_y < tmx_data.height):
                            continue
                            
                        is_invalid = False
                        for layer in tmx_data.layers:
                            if isinstance(layer, pytmx.TiledTileLayer):
                                try:
                                    gid = layer.data[tile_y][tile_x]
                                except IndexError:
                                    gid = 0
                                if gid > 0:
                                    if layer.name.strip().lower() == "details fringe layer":
                                        is_invalid = True
                                        break
                                    props = tmx_data.get_tile_properties_by_gid(gid)
                                    if props and props.get("collidable"):
                                        is_invalid = True
                                        break
                        if is_invalid:
                            continue

                    # Spawn puddle!
                    self.puddles.append({
                        'pos': pygame.Vector2(px, py),
                        'radius': 1.0,
                        'max_radius': random.uniform(16, 26),
                        'alpha': 0.0,
                        'max_alpha': random.uniform(70, 110),
                        'ripples': [],
                        'ripple_timer': 0.0,
                        'evaporating': False
                    })
                    break

        # Update puddles
        for p in self.puddles[:]:
            if p.get('evaporating', False):
                p['alpha'] -= 20 * dt
                p['radius'] -= 3 * dt
                if p['alpha'] <= 0 or p['radius'] <= 0:
                    self.puddles.remove(p)
                    continue
            else:
                if p['radius'] < p['max_radius']:
                    p['radius'] += 3.0 * dt
                if p['alpha'] < p['max_alpha']:
                    p['alpha'] += 20 * dt

            # Ripples spawning
            if is_raining:
                p['ripple_timer'] += dt
                if p['ripple_timer'] >= random.uniform(0.5, 0.9):
                    p['ripple_timer'] = 0.0
                    p['ripples'].append({
                        'radius': 1.0,
                        'max_radius': p['radius'] * random.uniform(0.65, 0.95),
                        'alpha': p['alpha']
                    })

            # Update ripples
            for r in p['ripples'][:]:
                r['radius'] += 10 * dt
                r['alpha'] -= 200 * dt
                if r['alpha'] <= 0 or r['radius'] >= r['max_radius']:
                    p['ripples'].remove(r)

    def _update_fog(self, dt: float):
        for cloud in self.fog_clouds:
            cloud['x'] += cloud['vx'] * dt
            cloud['y'] += cloud['vy'] * dt
            
            # Wrap around boundaries
            size = 450 + cloud['size_idx'] * 175
            if cloud['x'] - size > cfg.SCREEN_WIDTH:
                cloud['x'] = -size
            elif cloud['x'] + size < 0:
                cloud['x'] = cfg.SCREEN_WIDTH + size
                
            if cloud['y'] - size > cfg.SCREEN_HEIGHT:
                cloud['y'] = -size
            elif cloud['y'] + size < 0:
                cloud['y'] = cfg.SCREEN_HEIGHT + size

        # Update small fog particles
        if self.current_weather == WeatherState.FOG and len(self.fog_particles) < 180:
            if random.random() < 0.6:
                self.fog_particles.append({
                    'x': random.uniform(-50, cfg.SCREEN_WIDTH + 50),
                    'y': random.uniform(-50, cfg.SCREEN_HEIGHT + 50),
                    'vx': random.uniform(15, 40),
                    'vy': random.uniform(-8, 8),
                    'life': 0.0,
                    'max_life': random.uniform(3.0, 7.0),
                    'size': random.uniform(1.5, 3.5),
                    'max_alpha': random.uniform(60, 180)
                })

        for fp in self.fog_particles[:]:
            fp['x'] += fp['vx'] * dt
            fp['y'] += fp['vy'] * dt
            fp['life'] += dt
            # gentle sine wave drift
            fp['y'] += math.sin(fp['life'] * 2.5) * 12.0 * dt
            if fp['life'] >= fp['max_life']:
                self.fog_particles.remove(fp)

    def _update_lightning(self, dt: float):
        if self.current_weather != WeatherState.STORM:
            return

        # Strike visual update
        if self.lightning_strike_pos:
            self.lightning_strike_timer -= dt
            if self.lightning_strike_timer <= 0:
                self.lightning_strike_pos = None
                self.lightning_branches.clear()

        # Update lightning flash phases
        if self.lightning_flash_time > 0:
            self.lightning_flash_time -= dt
        else:
            if self.flash_sequence:
                flash = self.flash_sequence.pop(0)
                self.lightning_flash_time = flash['dur']
                self.lightning_flash_max = flash['dur']
                self.lightning_flash_intensity = flash['intensity']

        self.lightning_timer -= dt
        if self.lightning_timer <= 0:
            self.lightning_timer = random.uniform(10.0, 18.0)
            
            # Create Realistic Double-Strobe Flash Sequence
            # First bright flash, small gap, second slightly longer/dimmer flash
            self.flash_sequence = [
                {'dur': 0.12, 'intensity': 1.0},
                {'dur': 0.08, 'intensity': 0.0},
                {'dur': 0.25, 'intensity': 0.7}
            ]
            
            # Trigger double screen rumble
            self.game.camera_shake_time = 0.55
            self.game.camera_shake_intensity = random.uniform(10.0, 18.0)
            
            # Calculate strike position
            player = self.game.character
            offset_x = random.uniform(-400, 400)
            offset_y = random.uniform(-300, 300)
            strike_world = player.get_center() + pygame.Vector2(offset_x, offset_y)
            self.lightning_strike_pos = strike_world
            self.lightning_strike_timer = 0.22
            
            # Generate Branching Bolts!
            self.lightning_branches = []
            steps = 7
            start_x = strike_world.x + random.uniform(-100, 100)
            start_y = -50
            
            main_path = [(start_x, start_y)]
            for i in range(1, steps + 1):
                pct = i / steps
                tx = start_x + (strike_world.x - start_x) * pct
                ty = -50 + (strike_world.y - (-50)) * pct
                if i < steps:
                    tx += random.uniform(-35, 35)
                main_path.append((tx, ty))

            # Spawn 2 side branches branching off nodes of the main path
            for b_idx in range(2):
                node_idx = random.randint(2, 4)
                if node_idx < len(main_path):
                    node = main_path[node_idx]
                    branch = [node]
                    curr_x, curr_y = node
                    branch_steps = 3
                    for j in range(1, branch_steps + 1):
                        curr_x += random.uniform(-60, 60) + (100 if b_idx == 0 else -100) * (j / branch_steps)
                        curr_y += random.uniform(30, 80)
                        branch.append((curr_x, curr_y))
                    self.lightning_branches.append(branch)

            self.lightning_branches.append(main_path)  # Main branch is last in array

            # Damage check
            strike_radius = 65.0
            if player.get_center().distance_to(strike_world) < strike_radius:
                player.take_damage(15, ignore_invulnerability=True)
                player.add_floating_text(_("ZAP!"), player.pos.x, player.pos.y - 40, (160, 215, 255), 1.5, 26)
            
            for enemy in list(self.game.enemies):
                if enemy.pos.distance_to(strike_world) < strike_radius:
                    enemy.take_damage(25)
                    if hasattr(enemy, 'stun'):
                        enemy.stun(1.5)

    def draw(self, screen: pygame.Surface):
        if self.is_indoors():
            return

        camera_offset = self.game._get_camera_offset()
        
        # 1. Draw Puddles (world-space)
        for p in self.puddles:
            screen_pos = p['pos'] - camera_offset
            r = int(p['radius'])
            if r <= 0:
                continue
            if -r < screen_pos.x < cfg.SCREEN_WIDTH + r and -r < screen_pos.y < cfg.SCREEN_HEIGHT + r:
                puddle_surf = pygame.Surface((r * 2, r), pygame.SRCALPHA)
                
                # Base puddle color: soft reflective sky color (bright and water-like)
                base_color = (130, 175, 220, int(p['alpha'] * 0.5))
                pygame.draw.ellipse(puddle_surf, base_color, (0, 0, r * 2, r))
                
                # Soft outer rim to blend with ground seamlessly
                rim_color = (160, 200, 235, int(p['alpha'] * 0.25))
                pygame.draw.ellipse(puddle_surf, rim_color, (0, 0, r * 2, r), max(1, r // 10))
                
                # Specular light highlight/glint on top-left of puddle (stunning visual touch!)
                shine_alpha = int(p['alpha'] * 0.6)
                if shine_alpha > 0:
                    shine_r = max(3, r // 3)
                    # Soft gradient glint
                    shine_color = (255, 255, 255, shine_alpha)
                    pygame.draw.ellipse(
                        puddle_surf, 
                        shine_color, 
                        (r - shine_r - r // 2.5, r // 4 - shine_r // 3, shine_r * 2, shine_r)
                    )
                    # Core bright highlight inside the glint
                    core_r = max(1, shine_r // 2)
                    core_color = (255, 255, 255, int(p['alpha'] * 0.95))
                    pygame.draw.ellipse(
                        puddle_surf, 
                        core_color, 
                        (r - shine_r - r // 2.5 + core_r, r // 4 - shine_r // 3 + core_r // 2, core_r * 2, core_r)
                    )
                
                # Draw concentric ripples with smooth anti-aliased look
                for rip in p['ripples']:
                    rip_r = int(rip['radius'])
                    if rip_r > 0:
                        # Ripple ring with expanding fade
                        rip_alpha = int(rip['alpha'] * 0.9)
                        if rip_alpha > 0:
                            rip_color = (160, 200, 240, rip_alpha)
                            thickness = max(1, int((rip['max_radius'] - rip_r) / rip['max_radius'] * 3))
                            pygame.draw.ellipse(puddle_surf, rip_color, (r - rip_r, r // 2 - rip_r // 2, rip_r * 2, rip_r), thickness)
                
                screen.blit(puddle_surf, (screen_pos.x - r, screen_pos.y - r // 2))

        # 2. Draw Branching Lightning Strike Bolts (world-space)
        if self.lightning_strike_pos and self.lightning_branches:
            for idx, path in enumerate(self.lightning_branches):
                is_main = (idx == len(self.lightning_branches) - 1)
                
                # Project path points to screen coordinates
                scr_points = [(pt[0] - camera_offset.x, pt[1] - camera_offset.y) for pt in path]
                
                if len(scr_points) >= 2:
                    if is_main:
                        # Main bolt (thick glow + inner white core)
                        pygame.draw.lines(screen, (75, 155, 255, 140), False, scr_points, 9)
                        pygame.draw.lines(screen, (255, 255, 255, 255), False, scr_points, 3)
                    else:
                        # Side branches (thin faded blue/white discharge)
                        pygame.draw.lines(screen, (100, 175, 255, 90), False, scr_points, 4)
                        pygame.draw.lines(screen, (255, 255, 255, 180), False, scr_points, 1)

            # Draw Ground Impact Blast Ring
            impact_pos = self.lightning_strike_pos - camera_offset
            pygame.draw.circle(screen, (255, 255, 255, 255), (int(impact_pos.x), int(impact_pos.y)), 18)
            pygame.draw.circle(screen, (130, 205, 255, 160), (int(impact_pos.x), int(impact_pos.y)), 40)

        # 3. Draw Parallax Rain (screen-space)
        if self.current_weather in (WeatherState.RAIN, WeatherState.STORM):
            rain_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            
            # Dynamic wind vector matching updates
            time_sec = pygame.time.get_ticks() * 0.001
            base_wind = 220.0 if self.current_weather == WeatherState.STORM else 60.0
            wind = base_wind + math.sin(time_sec * 0.8) * 30.0
            dx_factor = wind / 1000.0

            for p in self.rain_particles:
                # Calculate tilted end point based on wind
                start_x, start_y = p['x'], p['y']
                end_x = start_x + (p['len'] * dx_factor)
                end_y = start_y + p['len']
                
                pygame.draw.line(
                    rain_surf,
                    (130, 180, 242, int(p['alpha'])),
                    (start_x, start_y),
                    (end_x, end_y),
                    int(p['width'])
                )
            
            # Draw splash rings
            for s in self.splashes:
                pygame.draw.ellipse(
                    rain_surf,
                    (160, 205, 255, int(s['alpha'])),
                    (s['x'] - s['radius'], s['y'] - s['radius'] / 2, s['radius'] * 2, s['radius']),
                    2
                )
            screen.blit(rain_surf, (0, 0))

        # 4. Draw Volumetric Fog (Drifting pre-cached surfaces) - OPTIMIZED & BEAUTIFUL
        if self.current_weather == WeatherState.FOG:
            t = pygame.time.get_ticks() * 0.001
            
            # Add a faint full-screen fog tint
            ambient_fog = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            ambient_fog.fill((210, 220, 230, 45))
            screen.blit(ambient_fog, (0, 0))
            
            for cloud in self.fog_clouds:
                surf = self.fog_surfaces[cloud['size_idx']]
                
                # Pulse alpha slightly
                pulse = math.sin(t * cloud['pulse_speed'] + cloud['pulse_offset']) * 0.15
                alpha_pct = max(0.5, min(1.5, cloud['alpha_mult'] * (1.0 + pulse)))
                
                # Fast blit with per-surface alpha
                surf.set_alpha(int(255 * alpha_pct * 0.5))  # Higher alpha for visibility
                screen.blit(surf, (int(cloud['x']), int(cloud['y'])))
                surf.set_alpha(None)

            # Draw small fog particles (floating mist bits)
            if self.fog_particles:
                part_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                for fp in self.fog_particles:
                    life_pct = fp['life'] / fp['max_life']
                    alpha = int(fp['max_alpha'] * (1.0 - (2.0 * life_pct - 1.0)**2))
                    if alpha > 0:
                        pygame.draw.circle(part_surf, (240, 248, 255, alpha), (int(fp['x']), int(fp['y'])), fp['size'])
                screen.blit(part_surf, (0, 0))

        # 5. Draw Storm screen ambient darkening
        if self.current_weather == WeatherState.STORM:
            ambient_dark = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            ambient_dark.fill((6, 3, 20, 110))
            screen.blit(ambient_dark, (0, 0))

        # 6. Draw Lightning Flash (full screen double-strobe)
        if self.lightning_flash_time > 0 and self.lightning_flash_intensity > 0:
            pct = self.lightning_flash_time / self.lightning_flash_max
            flash_alpha = int(pct * 230 * self.lightning_flash_intensity)
            if flash_alpha > 0:
                flash_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, flash_alpha))
                screen.blit(flash_surf, (0, 0))
