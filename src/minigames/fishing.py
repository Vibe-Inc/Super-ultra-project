import math
import random
import pygame
from dataclasses import dataclass
from typing import Optional, List

try:
    from src.items.items import create_item
except Exception:
    def create_item(_id):
        return None


@dataclass
class FishType:
    id: str
    name: str
    weight: float
    difficulty: float
    speed: float
    reward_item_id: Optional[str] = None
    catch_threshold: int = 100


class Bobber:
    def __init__(self, x: float, y: float):
        self.pos = pygame.Vector2(x, y)
        self.alive = True
        self.sink_timer = 0.0

    def update(self, dt: float):
        self.sink_timer += dt
        self.render_offset = math.sin(self.sink_timer * 4.0) * 2.0


class FishInstance:
    def __init__(self, fish_type: FishType, start_x: float, start_y: float):
        self.fish_type = fish_type
        self.pos = pygame.Vector2(start_x, start_y)
        self.speed = fish_type.speed
        self.alive = True
        self.time = 0.0
        self.seed = random.random() * 1000.0

    def update(self, dt: float):
        self.time += dt


class FishingUI:
    def __init__(self, controller):
        self.ctrl = controller
        self.font = pygame.font.SysFont(None, 28)
        self.big_font = pygame.font.SysFont(None, 36)
        self.hint_font = pygame.font.SysFont(None, 20)
        self.show_hit_timer = 0.0
        self.result_message = ""
        self.result_timer = 0.0
        self.result_is_success = False

    def show_hit(self, duration: float = 1.0):
        self.show_hit_timer = duration

    def show_result(self, message: str, success: bool, duration: float = 2.5):
        self.result_message = message
        self.result_is_success = success
        self.result_timer = duration

    def update(self, dt: float):
        if self.show_hit_timer > 0.0:
            self.show_hit_timer = max(0.0, self.show_hit_timer - dt)
        if self.result_timer > 0.0:
            self.result_timer = max(0.0, self.result_timer - dt)

    def draw(self, screen: pygame.Surface, camera_offset: pygame.Vector2):
        if self.ctrl.bobber:
            bob = self.ctrl.bobber
            player_center = self.ctrl.game.character.get_center() - camera_offset
            bob_pos = bob.pos - camera_offset
            try:
                color = (80, 200, 80) if self.ctrl.current_zone_quality > 0.6 else (150, 150, 200)
            except Exception:
                color = (150, 150, 200)
            pygame.draw.line(screen, color, (player_center.x, player_center.y), (bob_pos.x, bob_pos.y), 3)
            r = pygame.Rect(0, 0, 8, 8)
            r.center = (int(bob_pos.x), int(bob_pos.y + getattr(bob, "render_offset", 0)))
            pygame.draw.rect(screen, (220, 50, 50), r)

        if self.show_hit_timer > 0.0:
            txt = self.font.render("Hit!", True, (255, 255, 120))
            screen.blit(txt, (screen.get_width() // 2 - txt.get_width() // 2, screen.get_height() // 2 - 40))

        # Draw result message (caught / escaped)
        if self.result_timer > 0.0 and self.result_message:
            color = (80, 220, 80) if self.result_is_success else (220, 80, 80)
            txt = self.big_font.render(self.result_message, True, color)
            screen.blit(txt, (screen.get_width() // 2 - txt.get_width() // 2, screen.get_height() // 2 - 80))

        if self.ctrl.state == "active":
            # Halved all dimensions (2x smaller)
            w = 14
            h = 100
            # Position the catch bar to the right of the character in screen space
            player_screen = self.ctrl.game.character.get_center() - camera_offset
            bar_x = int(player_screen.x + 20)
            bar_y = int(player_screen.y - h // 2)

            pygame.draw.rect(screen, (30, 30, 30), (bar_x - 4, bar_y - 4, w + 8, h + 8), border_radius=2)
            pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, w, h))

            fill_h = int((self.ctrl.catch_fill / self.ctrl.catch_fill_max) * h)
            pygame.draw.rect(screen, (80, 200, 80), (bar_x, bar_y + h - fill_h, w, fill_h))

            catcher_h = 9
            catcher_norm = getattr(self.ctrl, "active_bobber_norm", 0.5)
            catcher_y = int(bar_y + catcher_norm * h - catcher_h / 2)
            catcher_color = (240, 240, 80) if getattr(self.ctrl, "active_overlap", False) else (200, 200, 80)
            pygame.draw.rect(screen, catcher_color, (bar_x - 2, catcher_y, w + 4, catcher_h), border_radius=2)

            fish_pos_norm = getattr(self.ctrl, "active_fish_pos_norm", 0.5)
            fish_y = int(bar_y + fish_pos_norm * h)
            pygame.draw.line(screen, (220, 80, 80), (bar_x - 4, fish_y), (bar_x + w + 4, fish_y), 2)

            hint = self.hint_font.render("Hold Space / Left Mouse to reel", True, (220, 220, 220))
            screen.blit(hint, (bar_x - hint.get_width() // 2 + w // 2, bar_y + h + 8))


class FishingController:
    def __init__(self, game):
        self.game = game
        self.state = "idle"
        self.bobber: Optional[Bobber] = None
        self.bobber_timer = 0.0
        self.seek_timer = 0.0
        self.seek_interval = 0.5
        self.active_fish: Optional[FishInstance] = None
        self.ui = FishingUI(self)
        self.current_zone_quality = 0.5
        self.catch_fill = 0.0
        self.catch_fill_max = 100.0
        self.catch_zone_offset = 0.5
        self.active_fish_pos_norm = 0.5
        self.active_bobber_norm = 0.5
        self.active_overlap = False

        try:
            from src.minigames.fishing_config import FISH_TYPES
            self.fish_types: List[FishType] = [FishType(**f) for f in FISH_TYPES]
        except Exception:
            self.fish_types = [
                FishType(id="fish_common", name="Common Fish", weight=70, difficulty=0.3, speed=1.0, reward_item_id="fish_raw"),
                FishType(id="fish_rare", name="Rare Fish", weight=30, difficulty=0.7, speed=1.6, reward_item_id="fish_raw"),
            ]

    def _get_fishing_zones(self):
        zones = []
        try:
            tmx = None
            if getattr(self.game, "map", None) and getattr(self.game.map, "current_map", None):
                tmx_map = self.game.map.current_map
                tmx = getattr(tmx_map, "tmxdata", None) or getattr(tmx_map, "get_tmx_data", lambda: None)()
            if not tmx:
                return zones
            objs = getattr(tmx, "objects", None)
            if objs is None:
                try:
                    for layer in getattr(tmx, "layers", []):
                        if getattr(layer, "name", "") == "FishingZones":
                            for obj in getattr(layer, "objects", []):
                                zones.append({
                                    "x": obj.x, "y": obj.y,
                                    "width": obj.width, "height": obj.height,
                                    "quality": float(getattr(obj, "properties", {}).get("quality", 0.5)),
                                })
                except Exception:
                    pass
                return zones
            for obj in objs:
                if getattr(obj, "groupname", "") == "FishingZones" or getattr(obj, "name", "") == "FishingZone":
                    zones.append({
                        "x": obj.x, "y": obj.y,
                        "width": obj.width, "height": obj.height,
                        "quality": float(getattr(obj, "properties", {}).get("quality", 0.5)),
                    })
        except Exception:
            pass
        return zones

    def _player_near_zone(self) -> Optional[dict]:
        try:
            zones = self._get_fishing_zones()
            if not zones:
                return None
            player_center = self.game.character.get_center()
            best = None
            best_dist = float("inf")
            for z in zones:
                zx = z["x"] + z.get("width", 0) / 2
                zy = z["y"] + z.get("height", 0) / 2
                dist = (pygame.Vector2(zx, zy) - player_center).length_squared()
                if dist < best_dist:
                    best_dist = dist
                    best = z
            return best
        except Exception:
            return None

    def _can_fish(self) -> bool:
        try:
            inv_manager = getattr(self.game.app, 'INV_manager', None)
            if not inv_manager:
                return False
            hotbar = getattr(inv_manager, 'hotbar', None)
            if not hotbar:
                return False
            active = getattr(hotbar, 'active_slot_index', None)
            if active is None:
                return False
            if not (0 <= active < len(hotbar.items)):
                return False
            slot = hotbar.items[active][0]
            if not slot:
                return False
            item = slot[0]
            return getattr(item, 'id', '') == 'fishing_rod'
        except Exception:
            return False

    def cast(self, target_world_pos: pygame.Vector2):
        if self.state not in ("ready", "idle"):
            return
        if not self._can_fish():
            return
        player_center = self.game.character.get_center()
        max_range = 320
        dir_vec = pygame.Vector2(target_world_pos) - player_center
        if dir_vec.length() > max_range:
            dir_vec.scale_to_length(max_range)
        bob_pos = player_center + dir_vec
        self.bobber = Bobber(bob_pos.x, bob_pos.y)
        self.state = "casting"
        self.bobber_timer = 0.0
        self.seek_timer = 0.0
        self.ui.show_hit_timer = 0.0

    def _select_fish(self):
        total = sum(ft.weight for ft in self.fish_types)
        r = random.uniform(0, total)
        upto = 0.0
        for ft in self.fish_types:
            if upto + ft.weight >= r:
                return ft
            upto += ft.weight
        return self.fish_types[0]

    def update(self, dt: float):
        self.ui.update(dt)

        if self.bobber:
            self.bobber.update(dt)

        zone = self._player_near_zone()
        if zone:
            self.current_zone_quality = zone.get("quality", 0.5)
            if self.state == "idle":
                if self._can_fish():
                    self.state = "ready"
        else:
            self.current_zone_quality = 0.2
            if self.state == "ready":
                self.state = "idle"

        if self.state == "casting" and self.bobber:
            self.seek_timer += dt
            if self.seek_timer >= self.seek_interval:
                self.seek_timer = 0.0
                base_chance = 0.08 + self.current_zone_quality * 0.25
                if random.random() < base_chance:
                    fish_type = self._select_fish()
                    self.active_fish = FishInstance(fish_type, self.bobber.pos.x, self.bobber.pos.y)
                    self.ui.show_hit(0.9)
                    self.state = "bite"

        elif self.state == "bite":
            if self.ui.show_hit_timer <= 0.0:
                if self.active_fish:
                    self.state = "active"
                    self.catch_fill = 0.0
                    self.catch_fill_max = max(50.0, self.active_fish.fish_type.catch_threshold)
                    self.catch_zone_offset = 0.5
                    self.active_time_left = 12.0 - self.active_fish.fish_type.difficulty * 6.0
                    self.active_fish_pos_norm = 0.5
                    self.active_bobber_norm = 0.5
                    self.active_overlap = False

        elif self.state == "active":
            if self.active_fish:
                self.active_fish.update(dt)

            self.active_fish.time += dt
            fish_speed = self.active_fish.fish_type.speed * 0.35
            fish_pos_norm = (math.sin(self.active_fish.time * fish_speed + self.active_fish.seed) * 0.5 + 0.5)
            fish_pos_norm = max(0.05, min(0.95, fish_pos_norm))

            keys = pygame.key.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()
            reeling = keys[pygame.K_SPACE] or mouse_buttons[0]
            raise_speed = 0.7
            fall_speed = 0.4
            if reeling:
                self.catch_zone_offset = max(0.0, self.catch_zone_offset - raise_speed * dt)
            else:
                self.catch_zone_offset = min(1.0, self.catch_zone_offset + fall_speed * dt)
            bobber_norm = self.catch_zone_offset

            tolerance = 0.18 + (1.0 - self.active_fish.fish_type.difficulty) * 0.15
            overlap = abs(bobber_norm - fish_pos_norm) < tolerance

            if overlap:
                self.catch_fill += 20.0 * dt * (1.0 - self.active_fish.fish_type.difficulty + 0.3)
            else:
                self.catch_fill -= 10.0 * dt * (0.5 + self.active_fish.fish_type.difficulty)
            self.catch_fill = max(0.0, min(self.catch_fill, self.catch_fill_max))

            self.active_fish_pos_norm = fish_pos_norm
            self.active_bobber_norm = bobber_norm
            self.active_overlap = overlap

            self.active_time_left -= dt
            if self.catch_fill >= self.catch_fill_max:
                self._on_catch_success()
            elif self.active_time_left <= 0.0:
                self._on_catch_fail()

    def _on_catch_success(self):
        fish = self.active_fish.fish_type if self.active_fish else None
        if fish:
            msg = f"Caught {fish.name}!"
            if fish.reward_item_id:
                try:
                    item = create_item(fish.reward_item_id)
                    if item:
                        self.game.items.append(item)
                except Exception:
                    pass
            self.ui.show_result(msg, success=True, duration=3.0)
        self.state = "idle"
        self.bobber = None
        self.active_fish = None
        self.ui.show_hit_timer = 0.0

    def _on_catch_fail(self):
        fish = self.active_fish.fish_type if self.active_fish else None
        if fish:
            self.ui.show_result(f"{fish.name} escaped!", success=False, duration=2.0)
        else:
            self.ui.show_result("Fish escaped!", success=False, duration=2.0)
        self.state = "idle"
        self.bobber = None
        self.active_fish = None
        self.ui.show_hit_timer = 0.0

    def draw(self, screen: pygame.Surface, camera_offset: pygame.Vector2):
        try:
            self.ui.draw(screen, camera_offset)
        except Exception:
            pass

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f and self.state in ("ready", "idle"):
                mouse_pos = pygame.mouse.get_pos()
                target_world = pygame.Vector2(mouse_pos) + self.game._get_camera_offset()
                self.cast(target_world)
                return True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3 and self.state in ("ready", "idle"):
                target_world = pygame.Vector2(event.pos) + self.game._get_camera_offset()
                self.cast(target_world)
                return True
        return False