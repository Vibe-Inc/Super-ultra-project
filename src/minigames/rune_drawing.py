import math
import random
import pygame
import src.config as cfg
from src.core.logger import logger

class TraceParticle:
    def __init__(self, pos, color):
        self.x, self.y = pos
        self.vx = random.uniform(-15, 15)
        self.vy = random.uniform(-15, 15)
        self.life = 1.0
        self.max_life = 1.0
        self.color = color
        self.size = random.uniform(3, 8)
        
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

class ArcaneRing:
    def __init__(self, radius, speed, dash_length, color):
        self.radius = radius
        self.speed = speed
        self.dash_length = dash_length
        self.color = color
        self.angle = 0.0

    def update(self, dt):
        self.angle += self.speed * dt

    def draw(self, surface, cx, cy):
        circumference = 2 * math.pi * self.radius
        num_dashes = max(1, int(circumference / self.dash_length))
        angle_step = 2 * math.pi / num_dashes
        
        for i in range(num_dashes):
            if i % 2 == 0:
                start_ang = self.angle + i * angle_step
                end_ang = self.angle + (i + 1) * angle_step
                
                start_pos = (cx + math.cos(start_ang) * self.radius, cy + math.sin(start_ang) * self.radius)
                end_pos = (cx + math.cos(end_ang) * self.radius, cy + math.sin(end_ang) * self.radius)
                pygame.draw.line(surface, self.color, start_pos, end_pos, max(1, int(4 * cfg.ui_scale())))

class RuneDrawingMinigame:
    def __init__(self, app, rune_type="fire_rune", on_close=None):
        self.app = app
        self.rune_type = rune_type
        self.on_close = on_close
        
        self.fee = 50
        if self.app.money >= self.fee:
            self.app.money -= self.fee
        else:
            self.on_close(False)
            return

        self.screen_w = app.windowed_size[0] if not app.is_fullscreen else cfg.SCREEN_WIDTH
        self.screen_h = app.windowed_size[1] if not app.is_fullscreen else cfg.SCREEN_HEIGHT
        
        self.font_title = cfg.get_font(int(45 * cfg.ui_scale()))
        self.font = cfg.get_font(int(30 * cfg.ui_scale()))
        self.font_small = cfg.get_font(int(20 * cfg.ui_scale()))
        
        self.cx, self.cy = self.screen_w // 2, self.screen_h // 2
        sz = int(160 * cfg.ui_scale()) # slightly larger base size
        
        if rune_type == "fire_rune":
            # Pentagram star
            self.nodes = [
                pygame.Vector2(self.cx, self.cy - sz),
                pygame.Vector2(self.cx + sz*0.58, self.cy + sz*0.8),
                pygame.Vector2(self.cx - sz*0.95, self.cy - sz*0.3),
                pygame.Vector2(self.cx + sz*0.95, self.cy - sz*0.3),
                pygame.Vector2(self.cx - sz*0.58, self.cy + sz*0.8),
                pygame.Vector2(self.cx, self.cy - sz)
            ]
            self.color = (255, 120, 50)
            self.bg_color = (60, 20, 10)
        elif rune_type == "ice_rune":
            # Snowflake zigzag
            self.nodes = [
                pygame.Vector2(self.cx, self.cy - sz),
                pygame.Vector2(self.cx + sz*0.8, self.cy + sz*0.6),
                pygame.Vector2(self.cx + sz*0.8, self.cy - sz*0.6),
                pygame.Vector2(self.cx - sz*0.8, self.cy + sz*0.6),
                pygame.Vector2(self.cx - sz*0.8, self.cy - sz*0.6),
                pygame.Vector2(self.cx, self.cy - sz)
            ]
            self.color = (100, 220, 255)
            self.bg_color = (10, 30, 60)
        elif rune_type == "lightning_rune":
            # Jagged lightning bolt
            self.nodes = [
                pygame.Vector2(self.cx + sz*0.4, self.cy - sz),
                pygame.Vector2(self.cx - sz*0.2, self.cy - sz*0.1),
                pygame.Vector2(self.cx + sz*0.3, self.cy + sz*0.2),
                pygame.Vector2(self.cx - sz*0.5, self.cy + sz),
                pygame.Vector2(self.cx + sz*0.1, self.cy + sz*0.5),
                pygame.Vector2(self.cx - sz*0.1, self.cy)
            ]
            self.color = (255, 255, 100)
            self.bg_color = (40, 40, 10)
        elif rune_type == "void_rune":
            # Hourglass inside a square
            self.nodes = [
                pygame.Vector2(self.cx - sz, self.cy - sz),
                pygame.Vector2(self.cx + sz, self.cy - sz),
                pygame.Vector2(self.cx - sz, self.cy + sz),
                pygame.Vector2(self.cx + sz, self.cy + sz),
                pygame.Vector2(self.cx - sz, self.cy - sz),
                pygame.Vector2(self.cx, self.cy),
                pygame.Vector2(self.cx + sz, self.cy + sz)
            ]
            self.color = (200, 80, 255)
            self.bg_color = (30, 10, 40)
        else:
            self.nodes = [pygame.Vector2(self.cx, self.cy - sz), pygame.Vector2(self.cx, self.cy + sz)]
            self.color = (255, 255, 255)
            self.bg_color = (0, 0, 0)
            
        self.current_node_idx = 0
        self.traced_points = []
        self.particles = []
        
        self.time_limit = 8.0
        self.time_started = pygame.time.get_ticks()
        
        self.is_won = False
        self.is_lost = False
        self.finished = False
        self.is_drawing = False
        
        self.intro_time = 0.0
        
        # Rings for background
        self.rings = [
            ArcaneRing(sz * 1.5, 1.0, 30, (*self.color, 150)),
            ArcaneRing(sz * 1.7, -0.8, 40, (*self.color, 100)),
            ArcaneRing(sz * 1.9, 0.5, 60, (*self.color, 80))
        ]

    def handle_event(self, event):
        if self.finished:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                self.close()
            return
            
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.is_lost = True
            self.finished = True
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.is_drawing = True
            # Spawn some initial particles to show drawing started
            m_pos = pygame.mouse.get_pos()
            for _ in range(5):
                self.particles.append(TraceParticle(m_pos, self.color))
                
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_drawing = False
            # When lifted, reset if not finished
            if self.current_node_idx > 0 and self.current_node_idx < len(self.nodes):
                self.current_node_idx = 0
                self.traced_points.clear()
                try:
                    self.app.sound_manager.play_sound("error")
                except Exception: pass

    def update(self, dt):
        self.intro_time += dt
        
        for r in self.rings:
            r.update(dt)
            
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        
        if self.finished:
            # Spawn victory particles if won
            if self.is_won and random.random() < 0.3:
                for _ in range(8):
                    self.particles.append(TraceParticle((self.cx, self.cy), self.color))
            return
            
        elapsed = (pygame.time.get_ticks() - self.time_started) / 1000.0
        if elapsed > self.time_limit:
            self.is_lost = True
            self.finished = True
            try:
                self.app.sound_manager.play_sound("error")
            except Exception: pass
            return

        m_pos = pygame.mouse.get_pos()
        m_vec = pygame.Vector2(m_pos)
        
        if self.is_drawing:
            if not self.traced_points:
                self.traced_points.append(m_pos)
            else:
                last_pos = pygame.Vector2(self.traced_points[-1])
                if last_pos.distance_to(m_vec) > 5:
                    self.traced_points.append(m_pos)
                    # Spawn trace particles
                    for _ in range(2):
                        self.particles.append(TraceParticle(m_pos, self.color))
            
            if self.current_node_idx < len(self.nodes):
                target = self.nodes[self.current_node_idx]
                dist = target.distance_to(m_vec)
                threshold = int(55 * cfg.ui_scale())
                
                if dist <= threshold:
                    self.current_node_idx += 1
                    self._play_node_sound()
                    # Spawn burst
                    for _ in range(25):
                        self.particles.append(TraceParticle((target.x, target.y), (255, 255, 255)))
                        
                    if self.current_node_idx >= len(self.nodes):
                        self.is_won = True
                        self.finished = True
                        self.is_drawing = False
                        try:
                            self.app.sound_manager.play_sound("level_up")
                        except Exception: pass
                        
                        # Give the player the rune!
                        from src.items.items import create_item
                        rune = create_item(self.rune_type)
                        if rune:
                            gs = self.app.manager.states.get("gameplay")
                            if gs:
                                from src.inventory.system import CraftingLogic
                                if not CraftingLogic.add_crafted_item(gs.MAIN_player_inv, rune, 1):
                                    if hasattr(gs, 'hotbar') and gs.hotbar:
                                        CraftingLogic.add_crafted_item(gs.hotbar, rune, 1)

    def _play_node_sound(self):
        try:
            self.app.sound_manager.play_sound("click")
        except Exception: pass

    def draw(self, surface):
        ease = min(1.0, self.intro_time / 0.5)
        ease = 1.0 - (1.0 - ease)**3
        
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        # Background gradient based on rune type
        for i in range(0, self.screen_h, max(1, int(4*cfg.ui_scale()))):
            alpha = int(240 * ease)
            bg_r = int((self.bg_color[0] * i / self.screen_h))
            bg_g = int((self.bg_color[1] * i / self.screen_h))
            bg_b = int((self.bg_color[2] * i / self.screen_h))
            pygame.draw.line(overlay, (bg_r, bg_g, bg_b, alpha), (0, i), (self.screen_w, i), int(4*cfg.ui_scale()))
            
        surface.blit(overlay, (0, 0))
        
        # Draw Rings
        for r in self.rings:
            r.draw(surface, self.cx, self.cy)
            
        # Draw Particles
        for p in self.particles:
            alpha = int(255 * (p.life / p.max_life))
            size = max(1, int(p.size * ease))
            c = (*p.color[:3], alpha)
            psurf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(psurf, c, (size, size), size)
            surface.blit(psurf, (p.x - size, p.y - size))

        if self.finished:
            text = "RUNE CRAFTED!" if self.is_won else "CRAFTING FAILED!"
            col = (100, 255, 100) if self.is_won else (255, 100, 100)
            
            # Glow text
            txt_glow = self.font_title.render(text, True, col)
            glow_surf = pygame.Surface(txt_glow.get_size(), pygame.SRCALPHA)
            glow_surf.blit(txt_glow, (0,0))
            glow_surf.set_alpha(150)
            surface.blit(glow_surf, (self.cx - txt_glow.get_width()//2 - 2, self.cy - 70 - 2))
            surface.blit(glow_surf, (self.cx - txt_glow.get_width()//2 + 2, self.cy - 70 + 2))
            
            txt_surf = self.font_title.render(text, True, (255, 255, 255))
            surface.blit(txt_surf, (self.cx - txt_surf.get_width()//2, self.cy - 70))
            
            sub = self.font_small.render("Press any key to continue", True, (200, 200, 200))
            surface.blit(sub, (self.cx - sub.get_width()//2, self.cy + 20))
            return

        elapsed = (pygame.time.get_ticks() - self.time_started) / 1000.0
        rem = max(0, self.time_limit - elapsed)
        
        # Shake timer if low
        timer_x, timer_y = 30, 30
        t_col = (255, 255, 255)
        if rem < 3.0:
            timer_x += random.randint(-3, 3)
            timer_y += random.randint(-3, 3)
            t_col = (255, 80, 80)
            
        time_text = self.font.render(f"Arcane Energy: {rem:.1f}s", True, t_col)
        time_shadow = self.font.render(f"Arcane Energy: {rem:.1f}s", True, (0, 0, 0))
        surface.blit(time_shadow, (timer_x + 2, timer_y + 2))
        surface.blit(time_text, (timer_x, timer_y))

        # Draw connecting line background guide
        if len(self.nodes) > 1:
            pygame.draw.lines(surface, (*self.color, 50), False, [(n.x, n.y) for n in self.nodes], int(25 * cfg.ui_scale()))
            pygame.draw.lines(surface, (*self.color, 120), False, [(n.x, n.y) for n in self.nodes], int(10 * cfg.ui_scale()))
            
        # Draw Nodes
        pulse = (math.sin(self.intro_time * 10) + 1) / 2
        
        for i, n in enumerate(self.nodes):
            radius = int(22 * cfg.ui_scale())
            if i < self.current_node_idx:
                c = self.color
            elif i == self.current_node_idx:
                c = (255, 255, 255)
                radius += int(pulse * 10) # Pulse current node strongly
            else:
                c = (80, 80, 80)
                
            # Outer glow
            glow = pygame.Surface((radius*3, radius*3), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*c[:3], 60), (radius*1.5, radius*1.5), radius*1.5)
            surface.blit(glow, (int(n.x - radius*1.5), int(n.y - radius*1.5)))
            
            pygame.draw.circle(surface, c, (int(n.x), int(n.y)), radius)
            pygame.draw.circle(surface, (255, 255, 255), (int(n.x), int(n.y)), int(radius * 0.4))
            
        # Draw Traced Line
        if len(self.traced_points) > 1:
            pygame.draw.lines(surface, self.color, False, self.traced_points, int(10 * cfg.ui_scale()))
            # Draw glow on line
            pygame.draw.lines(surface, (255, 255, 255), False, self.traced_points, int(4 * cfg.ui_scale()))
            
        hint = self.font_small.render(f"Hold Left Click and trace the constellation! Cost: {self.fee} Gold.", True, (220, 220, 220))
        hint_s = self.font_small.render(f"Hold Left Click and trace the constellation! Cost: {self.fee} Gold.", True, (0, 0, 0))
        hx = self.cx - hint.get_width()//2
        hy = self.screen_h - 60
        surface.blit(hint_s, (hx + 1, hy + 1))
        surface.blit(hint, (hx, hy))

    def close(self):
        if self.on_close:
            self.on_close(self.is_won)
