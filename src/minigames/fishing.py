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
    """
    Stardew Valley-style fish: the fish position is driven by a per-instance
    velocity that randomly changes over time, producing an erratic up/down
    motion along the fishing bar.

    `pos.y_norm` is the fish's vertical position on the bar in [0, 1]
    where 0 = top of the bar, 1 = bottom of the bar.
    """

    def __init__(self, fish_type: FishType, start_x: float, start_y: float):
        self.fish_type = fish_type
        self.pos = pygame.Vector2(start_x, start_y)
        self.speed = fish_type.speed
        self.alive = True
        self.time = 0.0
        self.seed = random.random() * 1000.0
        # Vertical position on the bar in [0, 1] (0 = top, 1 = bottom)
        self.y_norm = 0.5
        # Vertical velocity in normalized units per second
        # Difficulty scales the base speed and the chance of sudden bursts.
        # Tuned to be forgiving so the minigame is catchable.
        diff = fish_type.difficulty
        self.velocity = random.uniform(-1.0, 1.0) * (0.3 + diff * 0.4)
        # Time until the fish changes direction / velocity
        self._dir_timer = random.uniform(0.6, 1.6)
        # Difficulty-driven behavior: higher difficulty => more frequent
        # direction changes and larger velocity spikes, but capped so the
        # player can still catch the fish.
        self._change_interval_min = max(0.25, 0.7 - diff * 0.3)
        self._change_interval_max = max(0.6, 1.6 - diff * 0.5)
        # Speed range also scales with difficulty (capped lower for catchability).
        self._max_speed = 0.45 + diff * 0.8

    def update(self, dt: float):
        self.time += dt
        self._dir_timer -= dt
        if self._dir_timer <= 0.0:
            # Pick a new velocity (Stardew-style random walk with bursts)
            burst = 1.0
            if random.random() < 0.25 + self.fish_type.difficulty * 0.25:
                # Sudden burst (fish darts up or down)
                burst = random.uniform(1.3, 2.2)
            direction = random.choice([-1.0, 1.0])
            magnitude = random.uniform(0.25, 1.0) * self._max_speed * burst
            self.velocity = direction * magnitude
            self._dir_timer = random.uniform(
                self._change_interval_min,
                self._change_interval_max,
            )

        # Integrate position
        self.y_norm += self.velocity * dt
        # Bounce softly off the top and bottom (Stardew-style)
        if self.y_norm < 0.02:
            self.y_norm = 0.02
            self.velocity = abs(self.velocity) * 0.6
        elif self.y_norm > 0.98:
            self.y_norm = 0.98
            self.velocity = -abs(self.velocity) * 0.6


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
            # --- Two side-by-side vertical bars (catching + progress) ---
            # Both bars are the same size, stacked next to the player.
            bar_w = 20           # narrower catching bar
            bar_h = 180          # smaller catching bar
            prog_w = 20          # same width as catching bar
            gap = 6              # horizontal gap between the two bars
            player_screen = self.ctrl.game.character.get_center() - camera_offset
            # Anchor to the right of the player; catching bar first, then progress.
            catch_x = int(player_screen.x + 24)
            catch_y = int(player_screen.y - bar_h // 2)
            prog_x = catch_x + bar_w + gap
            prog_y = catch_y


            # ----- Catching bar (fish + bobber) -----
            # Outer frame
            pygame.draw.rect(screen, (15, 15, 20), (catch_x - 3, catch_y - 3, bar_w + 6, bar_h + 6), border_radius=3)
            # Bar background
            pygame.draw.rect(screen, (35, 30, 50), (catch_x, catch_y, bar_w, bar_h), border_radius=2)

            # The moving fish (small, matches the smaller bar)
            fish = self.ctrl.active_fish
            fish_y_norm = getattr(fish, "y_norm", 0.5) if fish else 0.5
            fish_h = 10
            fish_w = bar_w - 4
            fish_y = int(catch_y + fish_y_norm * (bar_h - fish_h))
            fish_rect = pygame.Rect(catch_x + 2, fish_y, fish_w, fish_h)
            pygame.draw.rect(screen, (200, 30, 40), fish_rect, border_radius=2)
            pygame.draw.rect(screen, (120, 20, 25), fish_rect, width=1, border_radius=2)
            # Tiny eye
            eye_x = fish_rect.right - 3
            eye_y = fish_rect.centery
            pygame.draw.circle(screen, (255, 255, 255), (eye_x, eye_y), 1)
            pygame.draw.circle(screen, (0, 0, 0), (eye_x, eye_y), 1)
            # Tail fin
            tail_pts = [
                (fish_rect.left, fish_rect.centery - 2),
                (fish_rect.left - 2, fish_rect.centery),
                (fish_rect.left, fish_rect.centery + 2),
            ]
            pygame.draw.polygon(screen, (180, 25, 35), tail_pts)

            # The bobber (user slider) - half the previous height
            bobber_norm = getattr(self.ctrl, "active_bobber_norm", 0.5)
            bobber_h = 14
            bobber_top_pad = 2
            bobber_bottom_pad = 2
            usable_h = bar_h - bobber_top_pad - bobber_bottom_pad - bobber_h
            bobber_y = int(catch_y + bobber_top_pad + bobber_norm * usable_h)
            bobber_rect = pygame.Rect(catch_x - 1, bobber_y, bar_w + 2, bobber_h)
            overlap = getattr(self.ctrl, "active_overlap", False)
            bobber_color = (110, 240, 110) if overlap else (70, 180, 80)
            pygame.draw.rect(screen, (20, 60, 25), bobber_rect, border_radius=2)
            pygame.draw.rect(screen, bobber_color, bobber_rect.inflate(-2, -2), border_radius=2)



            # ----- Progress bar (vertical, same size as catching bar) -----
            # Outer frame
            pygame.draw.rect(screen, (15, 15, 20), (prog_x - 3, prog_y - 3, prog_w + 6, bar_h + 6), border_radius=3)
            # Progress track background
            pygame.draw.rect(screen, (25, 25, 35), (prog_x, prog_y, prog_w, bar_h), border_radius=2)
            # Fill from bottom to top
            fill_h = int((self.ctrl.catch_fill / max(1.0, self.ctrl.catch_fill_max)) * bar_h)
            if fill_h > 0:
                # Color shifts from yellow -> green as it fills
                t = self.ctrl.catch_fill / max(1.0, self.ctrl.catch_fill_max)
                r = int(220 - 160 * t)
                g = int(180 + 40 * t)
                b = int(60)
                pygame.draw.rect(screen, (r, g, b),
                                 (prog_x, prog_y + bar_h - fill_h, prog_w, fill_h),
                                 border_radius=2)

            # ----- Catch status text -----
            status = "Catch!" if self.ctrl.catch_fill >= self.ctrl.catch_fill_max else "Reel it in!"
            hint = self.hint_font.render(status, True, (240, 240, 240))
            screen.blit(hint, (catch_x + bar_w // 2 - hint.get_width() // 2, catch_y - 22))

            # Input hint below the bars
            hint2 = self.hint_font.render("Hold SPACE / LMB to reel up", True, (200, 200, 200))
            hint2_x = (catch_x + prog_x + prog_w) // 2 - hint2.get_width() // 2
            screen.blit(hint2, (hint2_x, catch_y + bar_h + 8))



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
                    self.active_time_left = 18.0 - self.active_fish.fish_type.difficulty * 6.0
                    self.active_fish_pos_norm = 0.5
                    self.active_bobber_norm = 0.5
                    self.active_overlap = False
                    # Track continuous overlap time (cumulative skill meter)
                    self.active_overlap_time = 0.0
                    self.active_total_time = 0.0
                    self.active_best_streak = 0.0
                    self.active_current_streak = 0.0

        elif self.state == "active":
            # --- Stardew Valley-style fishing minigame ---
            if self.active_fish:
                # The fish updates its own y_norm using an erratic random
                # walk (Stardew-style).
                self.active_fish.update(dt)

            fish_pos_norm = self.active_fish.y_norm

            # ----- Read player input for the bobber -----
            # Mouse Y is the natural control in Stardew, but we also support
            # SPACE / LMB for held-button input. We blend both: the held
            # buttons move the bobber toward the top of the bar (reel up);
            # releasing them lets it sink back down. Mouse Y directly sets
            # the target if it's available.
            mouse_x, mouse_y = pygame.mouse.get_pos()
            # Try to map mouse Y to the bar position. The bar is anchored
            # to the player's screen position with the same constants used
            # in UI drawing (must match FishingUI.draw()).
            bar_h = 180
            bar_w = 20
            player_screen = self.game.character.get_center() - self._get_camera_offset_static()
            catch_x = int(player_screen.x + 24)
            catch_y = int(player_screen.y - bar_h // 2)
            bar_y_top = catch_y
            bar_y_bottom = catch_y + bar_h
            bar_x_left = catch_x
            bar_x_right = catch_x + bar_w
            target_from_mouse = None
            if bar_y_top <= mouse_y <= bar_y_bottom and bar_x_left <= mouse_x <= bar_x_right:
                target_from_mouse = (mouse_y - bar_y_top) / float(bar_h)



            keys = pygame.key.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()
            reeling = keys[pygame.K_SPACE] or mouse_buttons[0]
            # Reel-up is fast, sinking is slow (Stardew style: fish pulls
            # the bobber down on its own but the player can yank it up).
            reel_up_speed = 1.4   # normalized units per second
            sink_speed = 0.35     # much slower so the player can react

            if target_from_mouse is not None and not reeling:
                # Mouse position is the primary control when not reeling.
                # Smoothly track the mouse so the bobber doesn't snap.
                target_norm = max(0.0, min(1.0, target_from_mouse))
                self.catch_zone_offset += (target_norm - self.catch_zone_offset) * min(1.0, 12.0 * dt)
            else:
                if reeling:
                    # Pull the bobber UP (towards the top of the bar).
                    self.catch_zone_offset = max(
                        0.0, self.catch_zone_offset - reel_up_speed * dt
                    )
                else:
                    # Slow sink when not reeling - matches the visual
                    # "fish pulls the bobber down" feel of Stardew.
                    self.catch_zone_offset = min(
                        1.0, self.catch_zone_offset + sink_speed * dt
                    )
            bobber_norm = self.catch_zone_offset

            # ----- Compute overlap between the fish and the bobber -----
            # Tolerance is based on the bobber size (14px on a 180px bar)
            # plus a difficulty-based extra room.
            bobber_size_frac = 14.0 / float(bar_h)  # ~0.078
            difficulty = self.active_fish.fish_type.difficulty
            # Generous base tolerance so a beginner can catch the fish.
            base_tol = 0.32 + (1.0 - difficulty) * 0.15
            tolerance = max(bobber_size_frac, base_tol)
            distance = abs(bobber_norm - fish_pos_norm)
            overlap = distance < tolerance


            # ----- Progress meter: STRICTLY skill-based -----
            # The progress bar fills RAPIDLY when the bobber is on the fish
            # and drains RAPIDLY when it is not, so the player immediately
            # feels the connection between their catching action and the
            # progress bar. Higher difficulty = slightly slower fill and
            # faster drain.
            if overlap:
                proximity = 1.0 - (distance / tolerance) if tolerance > 0 else 0.0
                # Fill rate is STRICTLY tied to catching accuracy.
                # The squaring of proximity makes perfect centering
                # the only fast way to fill the bar.
                # Perfect (1.0) -> 60/s -> ~1.7s to fill
                # 75%      -> 34/s -> ~3s to fill
                # 50%      -> 15/s -> ~6.7s to fill
                # 25%      -> 4/s  -> ~25s to fill
                accel = proximity * proximity
                base_fill = 60.0 * (1.0 - difficulty * 0.15)
                fill_rate = base_fill * accel
                self.catch_fill += fill_rate * dt
            else:
                # Gentle drain when not aligned.
                drain_rate = 25.0 + difficulty * 8.0
                self.catch_fill -= drain_rate * dt
            self.catch_fill = max(0.0, min(self.catch_fill, self.catch_fill_max))




            # Track stats (harmless, useful for future UI)
            self.active_total_time += dt
            if overlap:
                self.active_overlap_time += dt
                self.active_current_streak += dt
                if self.active_current_streak > self.active_best_streak:
                    self.active_best_streak = self.active_current_streak
            else:
                self.active_current_streak = 0.0

            self.active_fish_pos_norm = fish_pos_norm
            self.active_bobber_norm = bobber_norm
            self.active_overlap = overlap

            # Soft fail-safe: if the player can't catch the fish within
            # the time window, the fish escapes.
            self.active_time_left -= dt
            if self.catch_fill >= self.catch_fill_max:
                self._on_catch_success()
            elif self.active_time_left <= 0.0:
                self._on_catch_fail()
        else:
            # Reset overlap flag in non-active states so UI doesn't show stale data
            self.active_overlap = False

    def _get_camera_offset_static(self) -> pygame.Vector2:
        """Helper to fetch the camera offset (used by the active state)."""
        try:
            return self.game._get_camera_offset()
        except Exception:
            return pygame.Vector2(0, 0)

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