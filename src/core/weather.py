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
        
        # Rain particles (screen-space for performance)
        self.rain_particles = []  # dicts: {x, y, speed, len, width, alpha}
        self.max_rain_particles = 250
        
        # Rain splashes (screen-space)
        self.splashes = []  # dicts: {x, y, radius, max_radius, alpha}
        
        # Rain puddles (world-space)
        self.puddles = []  # dicts: {pos: Vector2, radius, max_radius, alpha, ripples: list}
        self.puddle_spawn_timer = 0.0
        
        # Fog clouds (screen-space)
        self.fog_clouds = []  # dicts: {x, y, radius, vx, vy, alpha, pulse}
        self._init_fog_clouds()
        
        # Lightning / Thunder settings
        self.lightning_flash_time = 0.0
        self.lightning_flash_max = 0.0
        self.lightning_timer = random.uniform(15.0, 30.0)
        self.lightning_strike_pos = None  # World position of strike
        self.lightning_strike_timer = 0.0

    def _init_fog_clouds(self):
        self.fog_clouds = []
        # Increased fog clouds from 8 to 12 for denser fog
        for _ in range(12):
            self.fog_clouds.append({
                'x': random.uniform(0, cfg.SCREEN_WIDTH),
                'y': random.uniform(0, cfg.SCREEN_HEIGHT),
                'radius': random.uniform(280, 480),  # Increased radius for greater visibility
                'vx': random.uniform(12, 30),
                'vy': random.uniform(-6, 6),
                'alpha': random.uniform(40, 75),  # Increased alpha for dense, prominent fog
                'pulse_speed': random.uniform(0.4, 1.2),
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
            self.lightning_strike_pos = None
            
        # Clear puddles if transitioning to CLEAR/FOG (they will evaporate)
        if state == WeatherState.CLEAR or state == WeatherState.FOG:
            for puddle in self.puddles:
                puddle['evaporating'] = True
        else:
            for puddle in self.puddles:
                puddle['evaporating'] = False

        # Apply stat changes immediately
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
                # Keep base detection range
                base_range = getattr(enemy, 'base_detection_range', enemy.detection_range)
                enemy.detection_range = base_range * detect_mult

    def update(self, dt: float):
        # Apply weather cycles
        self.weather_timer -= dt
        if self.weather_timer <= 0:
            # Roll for new weather
            # 50% Clear, 20% Rain, 15% Storm, 15% Fog
            roll = random.random()
            if roll < 0.50:
                self.change_weather(WeatherState.CLEAR)
            elif roll < 0.70:
                self.change_weather(WeatherState.RAIN)
            elif roll < 0.85:
                self.change_weather(WeatherState.STORM)
            else:
                self.change_weather(WeatherState.FOG)

        # Enforce weather effects on entities periodically
        self.apply_weather_gameplay_effects()

        # If indoors, we update timers but skip visual updates/particles
        if self.is_indoors():
            self.rain_particles.clear()
            self.splashes.clear()
            self.puddles.clear()
            return

        # Update visual elements
        self._update_rain(dt)
        self._update_puddles(dt)
        self._update_fog(dt)
        self._update_lightning(dt)

    def _update_rain(self, dt: float):
        is_raining = self.current_weather in (WeatherState.RAIN, WeatherState.STORM)
        # Increased particle count from 150/300 to 250/450 for highly visible rain
        self.max_rain_particles = 450 if self.current_weather == WeatherState.STORM else 250
        
        # Spawn rain particles
        if is_raining and len(self.rain_particles) < self.max_rain_particles:
            spawn_count = min(30, self.max_rain_particles - len(self.rain_particles))
            for _ in range(spawn_count):
                self.rain_particles.append({
                    'x': random.uniform(-100, cfg.SCREEN_WIDTH + 100),
                    'y': random.uniform(-50, 0),
                    'speed': random.uniform(900, 1300),  # Slightly faster falling rain
                    'len': random.uniform(20, 38),       # Longer rain streaks
                    'width': random.uniform(1.8, 3.2),   # Thicker rain streaks for visibility
                    'alpha': random.uniform(140, 220)    # Highly opaque particles
                })

        # Update rain particles
        wind = 250.0 if self.current_weather == WeatherState.STORM else 80.0
        for p in self.rain_particles[:]:
            p['x'] += wind * dt
            p['y'] += p['speed'] * dt
            if p['y'] > cfg.SCREEN_HEIGHT:
                self.rain_particles.remove(p)
                # Spawn splash on bottom of screen occasionally
                if random.random() < 0.5:
                    self.splashes.append({
                        'x': p['x'],
                        'y': cfg.SCREEN_HEIGHT - random.uniform(0, 15),
                        'radius': 1.0,
                        'max_radius': random.uniform(6, 12),  # Larger splashes
                        'alpha': p['alpha']
                    })

        # Update splashes
        for s in self.splashes[:]:
            s['radius'] += 20.0 * dt
            s['alpha'] -= 250 * dt
            if s['alpha'] <= 0 or s['radius'] >= s['max_radius']:
                self.splashes.remove(s)

    def _update_puddles(self, dt: float):
        is_raining = self.current_weather in (WeatherState.RAIN, WeatherState.STORM)
        
        # Spawn puddles in world coordinates near the player, checking collisions
        if is_raining and len(self.puddles) < 25:  # Increased max puddles to 25
            self.puddle_spawn_timer += dt
            if self.puddle_spawn_timer >= 0.8:      # Spawn more frequently
                self.puddle_spawn_timer = 0.0
                player = self.game.character
                
                # Attempt to find a valid coordinate
                for _ in range(25):
                    px = player.pos.x + random.uniform(-650, 650)
                    py = player.pos.y + random.uniform(-450, 450)
                    
                    # Verify map boundaries
                    map_w = cfg.SCREEN_WIDTH
                    map_h = cfg.SCREEN_HEIGHT
                    if self.game.map.current_map:
                        map_w = self.game.map.current_map.pixel_width
                        map_h = self.game.map.current_map.pixel_height
                    
                    px = max(50, min(px, map_w - 50))
                    py = max(50, min(py, map_h - 50))

                    # 1. Point & bounding rect check against all collidable obstacles (Wall layer, collision boxes)
                    puddle_r = 30.0
                    puddle_rect = pygame.Rect(px - puddle_r, py - puddle_r / 2, puddle_r * 2, puddle_r)
                    if puddle_rect.collidelist(self.game.obstacles) != -1:
                        continue

                    # 2. Check current map data for collidable tiles and the Details Fringe Layer
                    if self.game.map.current_map and self.game.map.current_map.game_map:
                        tmx_data = self.game.map.current_map.game_map
                        tile_x = int(px // tmx_data.tilewidth)
                        tile_y = int(py // tmx_data.tileheight)
                        
                        # Clip check
                        if not (0 <= tile_x < tmx_data.width and 0 <= tile_y < tmx_data.height):
                            continue
                            
                        is_invalid_tile = False
                        for layer in tmx_data.layers:
                            if isinstance(layer, pytmx.TiledTileLayer):
                                try:
                                    gid = layer.data[tile_y][tile_x]
                                except IndexError:
                                    gid = 0
                                if gid > 0:
                                    # Reject if tile is on the details fringe layer
                                    if layer.name.strip().lower() == "details fringe layer":
                                        is_invalid_tile = True
                                        break
                                    # Reject if tile property is set as collidable
                                    props = tmx_data.get_tile_properties_by_gid(gid)
                                    if props and props.get("collidable"):
                                        is_invalid_tile = True
                                        break
                        if is_invalid_tile:
                            continue

                    # Spot is valid, spawn puddle!
                    self.puddles.append({
                        'pos': pygame.Vector2(px, py),
                        'radius': 1.0,
                        'max_radius': random.uniform(18, 35),
                        'alpha': 0.0,
                        'max_alpha': random.uniform(90, 140),  # More visible puddles
                        'ripples': [],
                        'ripple_timer': 0.0,
                        'evaporating': False
                    })
                    break

        # Update puddles
        for p in self.puddles[:]:
            # Evaporation vs growth
            if p.get('evaporating', False):
                p['alpha'] -= 20 * dt
                p['radius'] -= 3 * dt
                if p['alpha'] <= 0 or p['radius'] <= 0:
                    self.puddles.remove(p)
                    continue
            else:
                if p['radius'] < p['max_radius']:
                    p['radius'] += 4.0 * dt
                if p['alpha'] < p['max_alpha']:
                    p['alpha'] += 25 * dt

            # Add ripples occasionally if raining
            if is_raining:
                p['ripple_timer'] += dt
                if p['ripple_timer'] >= random.uniform(0.3, 0.7):
                    p['ripple_timer'] = 0.0
                    p['ripples'].append({
                        'radius': 1.0,
                        'max_radius': p['radius'] * random.uniform(0.6, 0.95),
                        'alpha': p['alpha']
                    })

            # Update ripples
            for r in p['ripples'][:]:
                r['radius'] += 15 * dt
                r['alpha'] -= 250 * dt
                if r['alpha'] <= 0 or r['radius'] >= r['max_radius']:
                    p['ripples'].remove(r)

    def _update_fog(self, dt: float):
        for cloud in self.fog_clouds:
            cloud['x'] += cloud['vx'] * dt
            cloud['y'] += cloud['vy'] * dt
            
            # Wrap around boundaries
            if cloud['x'] - cloud['radius'] > cfg.SCREEN_WIDTH:
                cloud['x'] = -cloud['radius']
            elif cloud['x'] + cloud['radius'] < 0:
                cloud['x'] = cfg.SCREEN_WIDTH + cloud['radius']
                
            if cloud['y'] - cloud['radius'] > cfg.SCREEN_HEIGHT:
                cloud['y'] = -cloud['radius']
            elif cloud['y'] + cloud['radius'] < 0:
                cloud['y'] = cfg.SCREEN_HEIGHT + cloud['radius']

    def _update_lightning(self, dt: float):
        if self.current_weather != WeatherState.STORM:
            return

        # Lightning strike animation
        if self.lightning_strike_pos:
            self.lightning_strike_timer -= dt
            if self.lightning_strike_timer <= 0:
                self.lightning_strike_pos = None

        self.lightning_flash_time -= dt
        self.lightning_timer -= dt
        
        if self.lightning_timer <= 0:
            # Trigger lightning flash!
            self.lightning_timer = random.uniform(10.0, 20.0)  # More frequent lightning strikes
            self.lightning_flash_max = random.uniform(0.35, 0.65)  # Longer flash duration
            self.lightning_flash_time = self.lightning_flash_max
            
            # Camera Shake (dramatic screen rumble)
            shake_intensity = random.uniform(12.0, 22.0)  # Stronger screen shake
            self.game.camera_shake_time = 0.6
            self.game.camera_shake_intensity = shake_intensity
            
            # Spawn lightning strike in world coordinates near the screen viewport
            player = self.game.character
            offset_x = random.uniform(-450, 450)
            offset_y = random.uniform(-350, 350)
            strike_world = player.get_center() + pygame.Vector2(offset_x, offset_y)
            self.lightning_strike_pos = strike_world
            self.lightning_strike_timer = 0.22  # Longer strike line persistence

            # Lightning damage to player/enemies nearby
            strike_radius = 60.0
            # Damage player
            if player.get_center().distance_to(strike_world) < strike_radius:
                player.take_damage(15, ignore_invulnerability=True)
                player.add_floating_text(_("ZAP!"), player.pos.x, player.pos.y - 40, (150, 220, 255), 1.5, 26)
            
            # Damage enemies
            for enemy in list(self.game.enemies):
                if enemy.pos.distance_to(strike_world) < strike_radius:
                    enemy.take_damage(25)
                    if hasattr(enemy, 'stun'):
                        enemy.stun(1.5)

    def draw(self, screen: pygame.Surface):
        if self.is_indoors():
            return

        camera_offset = self.game._get_camera_offset()
        
        # 1. Draw Puddles (in world-space)
        for p in self.puddles:
            screen_pos = p['pos'] - camera_offset
            # Clip check
            r = int(p['radius'])
            if r <= 0:
                continue
            if -r < screen_pos.x < cfg.SCREEN_WIDTH + r and -r < screen_pos.y < cfg.SCREEN_HEIGHT + r:
                puddle_surf = pygame.Surface((r * 2, r), pygame.SRCALPHA)
                
                # Darker indigo-grey reflection with environment tint
                env_tint = cfg.ENVIRONMENT_TINT
                base_color = (
                    max(10, min(50, env_tint[0] // 5)),
                    max(20, min(70, env_tint[1] // 4)),
                    max(40, min(95, env_tint[2] // 3)),
                    int(p['alpha'])
                )
                
                pygame.draw.ellipse(puddle_surf, base_color, (0, 0, r * 2, r))
                
                # Draw ripples inside this puddle
                for rip in p['ripples']:
                    rip_r = int(rip['radius'])
                    if rip_r > 0:
                        # Thicker ripple color for visibility
                        rip_color = (150, 190, 235, int(rip['alpha']))
                        pygame.draw.ellipse(puddle_surf, rip_color, (r - rip_r, r // 2 - rip_r // 2, rip_r * 2, rip_r), 2)
                
                screen.blit(puddle_surf, (screen_pos.x - r, screen_pos.y - r // 2))

        # 2. Draw Lightning Strike Line (world-space)
        if self.lightning_strike_pos:
            strike_pos = self.lightning_strike_pos - camera_offset
            # Draw a jagged line from screen top down to strike_pos
            points = []
            steps = 8
            current_x = strike_pos.x + random.uniform(-120, 120)  # Start from top with drift
            current_y = -50
            points.append((current_x, current_y))
            
            for i in range(1, steps):
                target_pct = i / steps
                target_x = current_x + (strike_pos.x - current_x) * target_pct
                target_y = -50 + (strike_pos.y - (-50)) * target_pct
                # Add jagged wobble
                target_x += random.uniform(-40, 40)
                points.append((target_x, target_y))
            points.append((strike_pos.x, strike_pos.y))
            
            # Draw outer glow and inner core lines
            if len(points) >= 2:
                # Thicker visual lines for strikes
                pygame.draw.lines(screen, (80, 160, 255, 140), False, points, 9)
                pygame.draw.lines(screen, (255, 255, 255, 255), False, points, 3)
                # Spawn a bright impact circle
                pygame.draw.circle(screen, (255, 255, 255), (int(strike_pos.x), int(strike_pos.y)), 20)
                pygame.draw.circle(screen, (150, 220, 255, 180), (int(strike_pos.x), int(strike_pos.y)), 45)

        # 3. Draw Rain particles (screen-space)
        if self.current_weather in (WeatherState.RAIN, WeatherState.STORM):
            # Draw particles
            rain_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            wind_dx = 5 if self.current_weather == WeatherState.STORM else 1.8
            for p in self.rain_particles:
                pygame.draw.line(
                    rain_surf,
                    (130, 180, 240, int(p['alpha'])),
                    (p['x'], p['y']),
                    (p['x'] - p['len'] * wind_dx / 10, p['y'] + p['len']),
                    int(p['width'])
                )
            # Draw splashes
            for s in self.splashes:
                pygame.draw.ellipse(
                    rain_surf,
                    (160, 200, 250, int(s['alpha'])),
                    (s['x'] - s['radius'], s['y'] - s['radius'] / 2, s['radius'] * 2, s['radius']),
                    2  # Thicker splash rings
                )
            screen.blit(rain_surf, (0, 0))

        # 4. Draw Fog overlay (screen-space)
        if self.current_weather == WeatherState.FOG:
            fog_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            t = pygame.time.get_ticks() * 0.001
            for cloud in self.fog_clouds:
                # Add pulse to radius and alpha
                pulse = math.sin(t * cloud['pulse_speed'] + cloud['pulse_offset']) * 0.15
                radius = int(cloud['radius'] * (1.0 + pulse))
                alpha = int(cloud['alpha'] * (1.0 + pulse))
                alpha = max(5, min(100, alpha))
                
                # Fog color matches twilight/daytime slightly
                fog_col = (200, 208, 220, alpha)
                pygame.draw.circle(fog_surf, fog_col, (int(cloud['x']), int(cloud['y'])), radius)
            screen.blit(fog_surf, (0, 0))

        # 5. Draw Storm screen ambient darkening
        if self.current_weather == WeatherState.STORM:
            ambient_dark = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            # Storm clouds tint the environment significantly darker indigo for dramatic visibility
            ambient_dark.fill((8, 4, 25, 110))
            screen.blit(ambient_dark, (0, 0))

        # 6. Draw Lightning Flash (full screen alpha overlay)
        if self.lightning_flash_time > 0:
            pct = self.lightning_flash_time / self.lightning_flash_max
            flash_alpha = int(pct * 240)  # Brighter whiteout flash
            flash_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, flash_alpha))
            screen.blit(flash_surf, (0, 0))
