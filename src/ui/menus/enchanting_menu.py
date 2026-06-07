import math
import random
import pygame
import src.config as cfg
from src.core.logger import logger

class FloatingParticle:
    def __init__(self, rect):
        self.x = random.randint(rect.left, rect.right)
        self.y = random.randint(rect.bottom - 40, rect.bottom)
        self.vy = random.uniform(-30, -15)
        self.vx = random.uniform(-15, 15)
        self.life = random.uniform(2.0, 4.0)
        self.max_life = self.life
        self.size = random.uniform(2, 6)
        self.color = random.choice([(180, 100, 255), (100, 220, 255), (255, 180, 220)])

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

class EnchantingMenu:
    def __init__(self, app):
        self.app = app
        self.font_title = cfg.get_font(int(36 * cfg.ui_scale()))
        self.font = cfg.get_font(int(24 * cfg.ui_scale()))
        self.small_font = cfg.get_font(int(16 * cfg.ui_scale()))
        
        self.screen_w = app.windowed_size[0] if not app.is_fullscreen else cfg.SCREEN_WIDTH
        self.screen_h = app.windowed_size[1] if not app.is_fullscreen else cfg.SCREEN_HEIGHT
        
        self.w = int(760 * cfg.ui_scale())
        self.h = int(580 * cfg.ui_scale())
        self.x = (self.screen_w - self.w) // 2
        self.y = (self.screen_h - self.h) // 2
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        
        self.is_open = False
        self.selected_weapon = None
        self.selected_rune = None
        
        self.particles = []
        self.open_time = 0.0
        
        self.enchant_effect_time = 0.0

    def open(self):
        self.is_open = True
        self.selected_weapon = None
        self.selected_rune = None
        self.particles.clear()
        self.open_time = 0.0
        self.enchant_effect_time = 0.0
        try:
            if getattr(self.app, 'sound_manager', None):
                self.app.sound_manager.play_sound("level_up")
        except Exception:
            pass

    def close(self):
        self.is_open = False
        if "gameplay" in self.app.manager.states:
            self.app.manager.states["gameplay"].enchanting_menu = None

    def _get_weapons(self):
        weapons = []
        try:
            gs = self.app.manager.states["gameplay"]
            for i, item_data in enumerate(gs.MAIN_player_inv.items):
                if item_data is not None:
                    item = item_data[0]
                    if getattr(item, 'item_type', '') == 'weapon' or hasattr(item, 'on_hit_effects'):
                        weapons.append(item)
            for i, item_data in enumerate(gs.PLAYER_inventory_equipment.items):
                if item_data is not None:
                    item = item_data[0]
                    if getattr(item, 'item_type', '') == 'weapon' or hasattr(item, 'on_hit_effects'):
                        weapons.append(item)
        except Exception:
            pass
        return weapons

    def _get_runes(self):
        runes = []
        try:
            gs = self.app.manager.states["gameplay"]
            for i, item_data in enumerate(gs.MAIN_player_inv.items):
                if item_data is not None:
                    item = item_data[0]
                    if item.id in ["fire_rune", "ice_rune"]:
                        runes.append(item)
        except Exception:
            pass
        return runes

    def handle_event(self, event):
        if not self.is_open:
            return
            
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            close_btn = pygame.Rect(self.x + self.w - 50, self.y + 15, 35, 35)
            if close_btn.collidepoint(event.pos):
                self.close()
                return
                
            weapons = self._get_weapons()
            runes = self._get_runes()
            
            # Weapon clicks
            start_y = self.y + 120
            w_w = 320
            w_h = 45
            for i, w in enumerate(weapons):
                r = pygame.Rect(self.x + 30, start_y + i * (w_h + 8), w_w, w_h)
                if r.collidepoint(event.pos):
                    self.selected_weapon = w
                    try:
                        self.app.sound_manager.play_sound("click")
                    except Exception: pass
                    
            # Rune clicks
            r_w = 320
            for i, rune in enumerate(runes):
                r = pygame.Rect(self.x + self.w - r_w - 30, start_y + i * (w_h + 8), r_w, w_h)
                if r.collidepoint(event.pos):
                    self.selected_rune = rune
                    try:
                        self.app.sound_manager.play_sound("click")
                    except Exception: pass
                    
            # Enchant click
            enchant_btn = pygame.Rect(self.x + self.w//2 - 120, self.y + self.h - 80, 240, 55)
            if enchant_btn.collidepoint(event.pos):
                if self.selected_weapon and self.selected_rune:
                    self._do_enchant()

    def _do_enchant(self):
        try:
            self.app.sound_manager.play_sound("buy")
        except Exception: pass
        
        self.enchant_effect_time = 1.0
        self.selected_weapon.socketed_rune = self.selected_rune.id
        
        # Consume rune
        gs = self.app.manager.states["gameplay"]
        consumed = False
        for i, item_data in enumerate(gs.MAIN_player_inv.items):
            if item_data and item_data[0] == self.selected_rune:
                if item_data[1] > 1:
                    gs.MAIN_player_inv.items[i][1] -= 1
                else:
                    gs.MAIN_player_inv.items[i] = None
                consumed = True
                break
                
        if consumed:
            logger.info(f"Socketed {self.selected_weapon.name} with rune.")
            self.selected_rune = None
            
        # Spawn extra particles
        for _ in range(30):
            self.particles.append(FloatingParticle(self.rect))

    def update(self, dt):
        if not self.is_open:
            return
        self.open_time += dt
        if self.enchant_effect_time > 0:
            self.enchant_effect_time -= dt
            
        # Update particles
        if random.random() < 0.3:
            self.particles.append(FloatingParticle(self.rect))
        
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

    def _draw_glowing_rect(self, surface, rect, color, radius=10, glow_amount=15):
        # Draw base
        pygame.draw.rect(surface, color, rect, border_radius=radius)
        # Draw glow
        for i in range(3):
            inflate = (i + 1) * 2
            alpha = max(0, 100 - i * 30)
            glow_surface = pygame.Surface((rect.width + inflate * 2, rect.height + inflate * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*color[:3], alpha), glow_surface.get_rect(), border_radius=radius + inflate, width=2)
            surface.blit(glow_surface, (rect.x - inflate, rect.y - inflate))

    def draw(self, surface):
        if not self.is_open:
            return
            
        # Entrance anim
        ease = min(1.0, self.open_time / 0.3)
        ease = 1.0 - (1.0 - ease)**3
        
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((10, 5, 20, int(200 * ease)))
        surface.blit(overlay, (0, 0))
        
        scale_w = int(self.w * (0.8 + 0.2 * ease))
        scale_h = int(self.h * (0.8 + 0.2 * ease))
        r = pygame.Rect(
            self.x + (self.w - scale_w) // 2,
            self.y + (self.h - scale_h) // 2,
            scale_w, scale_h
        )
        
        # Panel Background
        panel_surf = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (20, 20, 35, 230), panel_surf.get_rect(), border_radius=15)
        # Gradient effect
        for i in range(r.height):
            c = (max(10, 40 - int(i * 0.05)), max(10, 30 - int(i * 0.05)), max(30, 60 - int(i * 0.05)), 100)
            pygame.draw.line(panel_surf, c, (0, i), (r.width, i))
        
        pygame.draw.rect(panel_surf, (150, 100, 255), panel_surf.get_rect(), width=2, border_radius=15)
        surface.blit(panel_surf, r)
        
        # Particles
        for p in self.particles:
            alpha = int(255 * (p.life / p.max_life))
            size = int(p.size * ease)
            c = (*p.color[:3], alpha)
            psurf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(psurf, c, (size, size), size)
            surface.blit(psurf, (p.x, p.y))

        # Header
        title = self.font_title.render("Arcane Enchanting", True, (230, 200, 255))
        shadow = self.font_title.render("Arcane Enchanting", True, (50, 20, 80))
        surface.blit(shadow, (r.centerx - title.get_width()//2 + 2, r.y + 22))
        surface.blit(title, (r.centerx - title.get_width()//2, r.y + 20))
        
        # Divider
        pygame.draw.line(surface, (120, 80, 200, 150), (r.left + 50, r.y + 80), (r.right - 50, r.y + 80), 2)
        
        # Close Button
        close_btn = pygame.Rect(r.right - 50, r.y + 15, 35, 35)
        m_pos = pygame.mouse.get_pos()
        c_color = (255, 100, 100) if close_btn.collidepoint(m_pos) else (200, 50, 50)
        pygame.draw.rect(surface, c_color, close_btn, border_radius=8)
        cx = self.font.render("X", True, (255, 255, 255))
        surface.blit(cx, (close_btn.centerx - cx.get_width()//2, close_btn.centery - cx.get_height()//2))

        weapons = self._get_weapons()
        runes = self._get_runes()
        
        # Titles for lists
        w_t = self.font.render("Weapons", True, (200, 200, 200))
        surface.blit(w_t, (r.left + 40, r.y + 90))
        r_t = self.font.render("Runes", True, (200, 200, 200))
        surface.blit(r_t, (r.right - r_t.get_width() - 40, r.y + 90))

        start_y = r.y + 130
        w_w = 320
        w_h = 45
        
        # Draw Weapons List
        for i, w in enumerate(weapons):
            item_r = pygame.Rect(r.left + 30, start_y + i * (w_h + 8), w_w, w_h)
            is_sel = (w == self.selected_weapon)
            is_hov = item_r.collidepoint(m_pos)
            bg = (80, 70, 120) if is_sel else ((60, 50, 90) if is_hov else (40, 35, 60))
            
            if is_sel:
                self._draw_glowing_rect(surface, item_r, bg, radius=8)
            else:
                pygame.draw.rect(surface, bg, item_r, border_radius=8)
                pygame.draw.rect(surface, (100, 90, 150), item_r, width=1, border_radius=8)
            
            sock = getattr(w, 'socketed_rune', None)
            sock_str = f" [{sock.replace('_', ' ').title()}]" if sock else ""
            c_txt = (255, 215, 0) if sock else (230, 230, 230)
            
            txt = self.small_font.render(w.name + sock_str, True, c_txt)
            surface.blit(txt, (item_r.x + 15, item_r.centery - txt.get_height()//2))
            
        # Draw Runes List
        for i, rune in enumerate(runes):
            item_r = pygame.Rect(r.right - w_w - 30, start_y + i * (w_h + 8), w_w, w_h)
            is_sel = (rune == self.selected_rune)
            is_hov = item_r.collidepoint(m_pos)
            bg = (120, 60, 80) if is_sel else ((90, 50, 70) if is_hov else (60, 35, 50))
            
            if is_sel:
                self._draw_glowing_rect(surface, item_r, bg, radius=8)
            else:
                pygame.draw.rect(surface, bg, item_r, border_radius=8)
                pygame.draw.rect(surface, (150, 80, 100), item_r, width=1, border_radius=8)
                
            txt = self.small_font.render(rune.name, True, (255, 230, 230))
            surface.blit(txt, (item_r.x + 15, item_r.centery - txt.get_height()//2))
            
        # Draw Enchant Button
        enchant_btn = pygame.Rect(r.centerx - 120, r.bottom - 90, 240, 60)
        can_enchant = self.selected_weapon is not None and self.selected_rune is not None
        btn_hov = enchant_btn.collidepoint(m_pos)
        
        pulse = (math.sin(self.open_time * 5) + 1) / 2
        
        if can_enchant:
            base_col = (130, 80, 255) if btn_hov else (100, 50, 200)
            glow_col = (int(base_col[0] + pulse * 40), int(base_col[1] + pulse * 40), int(base_col[2] + pulse * 40))
            self._draw_glowing_rect(surface, enchant_btn, glow_col, radius=12, glow_amount=15)
        else:
            pygame.draw.rect(surface, (50, 50, 60), enchant_btn, border_radius=12)
            pygame.draw.rect(surface, (80, 80, 90), enchant_btn, width=2, border_radius=12)
            
        if self.enchant_effect_time > 0:
            flash_alpha = int(255 * self.enchant_effect_time)
            flash_surf = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
            pygame.draw.rect(flash_surf, (255, 200, 255, flash_alpha), flash_surf.get_rect(), border_radius=15)
            surface.blit(flash_surf, r)

        btn_txt = self.font.render("ENCHANT", True, (255, 255, 255) if can_enchant else (150, 150, 150))
        surface.blit(btn_txt, (enchant_btn.centerx - btn_txt.get_width()//2, enchant_btn.centery - btn_txt.get_height()//2))
