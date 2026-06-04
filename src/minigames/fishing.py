"""Fishing minigame for the player.

Implements a Stardew Valley-style fishing minigame in which the player
casts a line, waits for a fish to bite, and then keeps a green
bobber on the moving red fish inside a vertical bar to fill a
progress meter.

The module exposes:

* :class:`FishType` -- dataclass describing a kind of fish.
* :class:`Bobber` -- the world-space indicator drawn at the cast
  location.
* :class:`FishInstance` -- a per-cast fish with erratic up/down
  motion on the bar.
* :class:`FishingUI` -- the per-frame drawing layer for the
  catching bar, progress bar, and result messages.
* :class:`FishingController` -- owns the state machine that drives
  the cast, bite, active, and result transitions.

Sphinx ``autodoc`` is used to generate API reference pages; all
public classes and methods are documented below.
"""

import math
import random
import pytmx
import pygame
from dataclasses import dataclass
from typing import Optional, List

try:
    from src.items.items import create_item
except Exception:
    def create_item(_id):
        """Fallback item factory used when ``src.items.items`` is unavailable.

        Args:
            _id (str): Item id to create. Ignored in the fallback.

        Returns:
            None: The fallback never produces an item.
        """
        return None


@dataclass
class FishType:
    """Description of a single kind of fish the player can catch.

    Attributes:
        id (str):
            Stable identifier used by the item/catch system.
        name (str):
            Human-readable name displayed in result messages.
        weight (float):
            Relative spawn weight when selecting a fish on a bite.
        difficulty (float):
            ``0.0`` (very easy) to ``1.0`` (very hard). Controls fish
            speed, direction-change frequency, and catch tolerance.
        speed (float):
            Multiplier applied to the fish's base vertical speed.
        reward_item_id (Optional[str]):
            Item id granted to the player on a successful catch.
            ``None`` means no item is given.
        catch_threshold (int):
            Default progress threshold (out of ``100``) used to
            compute the per-fish ``catch_fill_max`` when the active
            state is entered.
    """

    id: str
    name: str
    weight: float
    difficulty: float
    speed: float
    reward_item_id: Optional[str] = None
    catch_threshold: int = 100


class Bobber:
    """World-space marker drawn at the location the line was cast.

    The bobber renders a small red dot and a faint vertical
    oscillation, simulating a fishing float in the water.

    Attributes:
        pos (pygame.Vector2):
            World-space position of the bobber.
        alive (bool):
            ``True`` while the bobber should be rendered. The
            controller flips this when the cast ends.
        sink_timer (float):
            Seconds since the bobber was created. Used to drive the
            vertical oscillation render offset.
        render_offset (float):
            Latest vertical pixel offset used by the UI for a
            "floating" effect.
    """

    def __init__(self, x: float, y: float):
        """Initialize the bobber at a world position.

        Args:
            x (float): World X coordinate.
            y (float): World Y coordinate.
        """
        self.pos = pygame.Vector2(x, y)
        self.alive = True
        self.sink_timer = 0.0

    def update(self, dt: float):
        """Advance the bobber's animation timer.

        Args:
            dt (float): Elapsed time in seconds since the previous
                call. Must be non-negative.
        """
        self.sink_timer += dt
        self.render_offset = math.sin(self.sink_timer * 4.0) * 2.0


class FishInstance:

    def __init__(self, fish_type: FishType, start_x: float, start_y: float):
        """Create a fish with erratic vertical motion on the bar.

        Args:
            fish_type (FishType): The kind of fish this instance
                represents. Difficulty and speed parameters are read
                from this object.
            start_x (float): Unused world X coordinate (kept for
                compatibility with the original API).
            start_y (float): Unused world Y coordinate (kept for
                compatibility with the original API).

        Attributes:
            fish_type (FishType): The kind of fish represented.
            pos (pygame.Vector2): Unused world position.
            speed (float): Multiplier from ``fish_type``.
            alive (bool): Always ``True`` while the fish is active.
            time (float): Seconds since the fish was created.
            seed (float): Per-instance random seed for variation.
            y_norm (float): Vertical position on the bar in
                ``[0.02, 0.98]`` (0 = top, 1 = bottom).
            velocity (float): Current vertical velocity in
                normalized units per second.
            _dir_timer (float): Seconds until the next direction
                change.
            _change_interval_min (float): Lower bound for the
                inter-direction-change interval.
            _change_interval_max (float): Upper bound for the
                inter-direction-change interval.
            _max_speed (float): Cap for the fish's burst speed.
        """
        self.fish_type = fish_type
        self.pos = pygame.Vector2(start_x, start_y)
        self.speed = fish_type.speed
        self.alive = True
        self.time = 0.0
        self.seed = random.random() * 1000.0
        self.y_norm = 0.5
        diff = fish_type.difficulty
        self.velocity = random.uniform(-1.0, 1.0) * (0.3 + diff * 0.4)
        self._dir_timer = random.uniform(0.6, 1.6)
        self._change_interval_min = max(0.25, 0.7 - diff * 0.3)
        self._change_interval_max = max(0.6, 1.6 - diff * 0.5)
        self._max_speed = 0.45 + diff * 0.8

    def update(self, dt: float):
        """Step the fish forward by ``dt`` seconds.

        Re-rolls velocity whenever the direction-change timer
        elapses, applies a soft top/bottom bounce, and integrates
        ``y_norm``.

        Args:
            dt (float): Elapsed time in seconds. Must be
                non-negative.
        """
        self.time += dt
        self._dir_timer -= dt
        if self._dir_timer <= 0.0:
            burst = 1.0
            if random.random() < 0.25 + self.fish_type.difficulty * 0.25:
                burst = random.uniform(1.3, 2.2)
            direction = random.choice([-1.0, 1.0])
            magnitude = random.uniform(0.25, 1.0) * self._max_speed * burst
            self.velocity = direction * magnitude
            self._dir_timer = random.uniform(
                self._change_interval_min,
                self._change_interval_max,
            )

        self.y_norm += self.velocity * dt
        if self.y_norm < 0.02:
            self.y_norm = 0.02
            self.velocity = abs(self.velocity) * 0.6
        elif self.y_norm > 0.98:
            self.y_norm = 0.98
            self.velocity = -abs(self.velocity) * 0.6


class FishingUI:
    """Renderer for the fishing minigame.

    Draws the in-world bobber, the "Hit!" and result messages, and
    the two vertical bars (catching bar + progress bar) used during
    the active phase of the minigame.

    Attributes:
        ctrl (FishingController):
            The owning controller. Used to query state, fish, and
            progress values.
        font (pygame.font.Font):
            Font used for the "Hit!" message.
        big_font (pygame.font.Font):
            Font used for catch/escape result messages.
        hint_font (pygame.font.Font):
            Font used for status text and input hints.
        show_hit_timer (float):
            Seconds remaining for the "Hit!" overlay.
        result_message (str):
            Current result message ("Caught ..." or "X escaped!").
        result_timer (float):
            Seconds remaining for the result overlay.
        result_is_success (bool):
            ``True`` if the current result is a successful catch.
    """

    def __init__(self, controller):
        """Initialize the UI bound to a controller.

        Args:
            controller (FishingController): The owning controller.
        """
        self.ctrl = controller
        self.font = pygame.font.SysFont(None, 28)
        self.big_font = pygame.font.SysFont(None, 36)
        self.hint_font = pygame.font.SysFont(None, 20)
        self.show_hit_timer = 0.0
        self.result_message = ""
        self.result_timer = 0.0
        self.result_is_success = False

    def show_hit(self, duration: float = 1.0):
        """Trigger the "Hit!" overlay for ``duration`` seconds.

        Args:
            duration (float): How long the overlay should stay
                visible, in seconds. Defaults to ``1.0``.
        """
        self.show_hit_timer = duration

    def show_result(self, message: str, success: bool, duration: float = 2.5):
        """Show a result message ("Caught ..." or "X escaped!").

        Args:
            message (str): The text to display.
            success (bool): ``True`` colors the message green
                (catch), ``False`` colors it red (escape).
            duration (float): How long the message should remain
                visible, in seconds.
        """
        self.result_message = message
        self.result_is_success = success
        self.result_timer = duration

    def update(self, dt: float):
        """Decay the overlay timers.

        Args:
            dt (float): Elapsed time in seconds.
        """
        if self.show_hit_timer > 0.0:
            self.show_hit_timer = max(0.0, self.show_hit_timer - dt)
        if self.result_timer > 0.0:
            self.result_timer = max(0.0, self.result_timer - dt)

    def draw(self, screen: pygame.Surface, camera_offset: pygame.Vector2):
        """Draw the full fishing UI for one frame.

        Renders the world-space bobber (when not in active state),
        the "Hit!" and result overlays, and the two vertical bars
        (catching bar with fish/bobber and progress bar).

        Args:
            screen (pygame.Surface): Target surface to draw onto.
            camera_offset (pygame.Vector2): Current camera offset in
                world space; everything is drawn in screen space.
        """
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

        if self.result_timer > 0.0 and self.result_message:
            color = (80, 220, 80) if self.result_is_success else (220, 80, 80)
            txt = self.big_font.render(self.result_message, True, color)
            screen.blit(txt, (screen.get_width() // 2 - txt.get_width() // 2, screen.get_height() // 2 - 80))

        if self.ctrl.state == "active":
            bar_w = 20
            bar_h = 180
            prog_w = 20
            gap = 6
            player_screen = self.ctrl.game.character.get_center() - camera_offset
            catch_x = int(player_screen.x + 24)
            catch_y = int(player_screen.y - bar_h // 2)
            prog_x = catch_x + bar_w + gap
            prog_y = catch_y

            pygame.draw.rect(screen, (15, 15, 20), (catch_x - 3, catch_y - 3, bar_w + 6, bar_h + 6), border_radius=3)
            pygame.draw.rect(screen, (35, 30, 50), (catch_x, catch_y, bar_w, bar_h), border_radius=2)

            fish = self.ctrl.active_fish
            fish_y_norm = getattr(fish, "y_norm", 0.5) if fish else 0.5
            fish_h = 10
            fish_w = bar_w - 4
            fish_y = int(catch_y + fish_y_norm * (bar_h - fish_h))
            fish_rect = pygame.Rect(catch_x + 2, fish_y, fish_w, fish_h)
            pygame.draw.rect(screen, (200, 30, 40), fish_rect, border_radius=2)
            pygame.draw.rect(screen, (120, 20, 25), fish_rect, width=1, border_radius=2)
            eye_x = fish_rect.right - 3
            eye_y = fish_rect.centery
            pygame.draw.circle(screen, (255, 255, 255), (eye_x, eye_y), 1)
            pygame.draw.circle(screen, (0, 0, 0), (eye_x, eye_y), 1)
            tail_pts = [
                (fish_rect.left, fish_rect.centery - 2),
                (fish_rect.left - 2, fish_rect.centery),
                (fish_rect.left, fish_rect.centery + 2),
            ]
            pygame.draw.polygon(screen, (180, 25, 35), tail_pts)

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

            pygame.draw.rect(screen, (15, 15, 20), (prog_x - 3, prog_y - 3, prog_w + 6, bar_h + 6), border_radius=3)
            pygame.draw.rect(screen, (25, 25, 35), (prog_x, prog_y, prog_w, bar_h), border_radius=2)
            fill_h = int((self.ctrl.catch_fill / max(1.0, self.ctrl.catch_fill_max)) * bar_h)
            if fill_h > 0:
                t = self.ctrl.catch_fill / max(1.0, self.ctrl.catch_fill_max)
                r = int(220 - 160 * t)
                g = int(180 + 40 * t)
                b = int(60)
                pygame.draw.rect(screen, (r, g, b),
                                 (prog_x, prog_y + bar_h - fill_h, prog_w, fill_h),
                                 border_radius=2)

            status = "Catch!" if self.ctrl.catch_fill >= self.ctrl.catch_fill_max else "Reel it in!"
            hint = self.hint_font.render(status, True, (240, 240, 240))
            screen.blit(hint, (catch_x + bar_w // 2 - hint.get_width() // 2, catch_y - 22))

            hint2 = self.hint_font.render("Hold SPACE / LMB to reel up", True, (200, 200, 200))
            hint2_x = (catch_x + prog_x + prog_w) // 2 - hint2.get_width() // 2
            screen.blit(hint2, (hint2_x, catch_y + bar_h + 8))



class FishingController:
    """State machine that drives the fishing minigame.

    States:

    * ``idle`` -- player is not in a fishing zone, or has no rod.
    * ``ready`` -- player is in a fishing zone and has a rod
      equipped; can cast.
    * ``casting`` -- line is in the water, waiting for a bite.
    * ``bite`` -- a fish is biting, the "Hit!" overlay is shown.
    * ``active`` -- the minigame is live, the player must keep the
      bobber on the fish.

    The controller exposes :py:meth:`update` for the per-frame tick,
    :py:meth:`draw` for the world/UI render hook, and
    :py:meth:`handle_event` for pygame event dispatch.

    Attributes:
        game: The owning :class:`src.core.game.Game` instance.
        state (str): Current state name (see the state list above).
        bobber (Optional[Bobber]): World-space bobber when cast.
        bobber_timer (float): Unused; reserved for future use.
        seek_timer (float): Seconds accumulated in the
            ``casting`` state between bite rolls.
        seek_interval (float): Seconds between bite-chance rolls.
        active_fish (Optional[FishInstance]): The active fish in
            the ``active`` state, otherwise ``None``.
        ui (FishingUI): UI renderer for this controller.
        current_zone_quality (float): Cached quality of the
            nearest fishing zone (``0.0`` - ``1.0``).
        catch_fill (float): Current progress-meter value.
        catch_fill_max (float): Progress required to win the
            active state.
        catch_zone_offset (float): Normalized bobber position
            (``0.0`` = top, ``1.0`` = bottom).
        active_fish_pos_norm (float): Last reported fish y_norm.
        active_bobber_norm (float): Last reported bobber y_norm.
        active_overlap (bool): Whether the bobber currently
            overlaps the fish.
        fish_types (List[FishType]): Available fish archetypes.
    """

    def __init__(self, game):
        """Initialize the controller for the given game.

        Loads fish archetypes from ``src.minigames.fishing_config``
        if available, otherwise falls back to a small built-in list.

        Args:
            game: The owning :class:`src.core.game.Game` instance.
        """
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

    def _is_fishable_tile(self, world_pos: pygame.Vector2) -> bool:
        """Check whether the tile at ``world_pos`` has the
        ``fishable`` custom property.

        Returns:
            bool: ``True`` if the tile at the given world position
            has ``fishable`` set to ``True``.
        """
        try:
            if not getattr(self.game, "map", None) or not getattr(self.game.map, "current_map", None):
                return False
            tmx_map = self.game.map.current_map
            tmx = getattr(tmx_map, "tmxdata", None) or getattr(tmx_map, "get_tmx_data", lambda: None)()
            if not tmx:
                return False
            tile_x = int(world_pos.x // tmx.tilewidth)
            tile_y = int(world_pos.y // tmx.tileheight)
            for layer in tmx.layers:
                if not isinstance(layer, pytmx.TiledTileLayer):
                    continue
                try:
                    gid = layer.data[tile_y][tile_x]
                except (IndexError, TypeError):
                    continue
                if not gid:
                    continue
                tile_properties = tmx.get_tile_properties_by_gid(gid)
                if tile_properties and tile_properties.get("fishable"):
                    return True
        except Exception:
            pass
        return False

    def _can_fish(self) -> bool:
        """Check whether the player can currently cast.

        The check requires a valid inventory manager, a hotbar with
        an active slot, and a fishing rod in that slot.

        Returns:
            bool: ``True`` if the player can cast, ``False`` otherwise.
        """
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
        """Cast the line to ``target_world_pos``.

        The cast position is clamped to ``max_range`` from the
        player. Transitions ``idle``/``ready`` -> ``casting``.

        Args:
            target_world_pos (pygame.Vector2): Desired cast
                location in world space.
        """
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
        if not self._is_fishable_tile(bob_pos):
            return
        self.bobber = Bobber(bob_pos.x, bob_pos.y)
        self.state = "casting"
        self.bobber_timer = 0.0
        self.seek_timer = 0.0
        self.ui.show_hit_timer = 0.0

    def _select_fish(self):
        """Choose a fish archetype weighted by ``fish.weight``.

        Returns:
            FishType: The selected fish archetype (never ``None``;
            falls back to the first entry if rounding leaves no
            candidate).
        """
        total = sum(ft.weight for ft in self.fish_types)
        r = random.uniform(0, total)
        upto = 0.0
        for ft in self.fish_types:
            if upto + ft.weight >= r:
                return ft
            upto += ft.weight
        return self.fish_types[0]

    def update(self, dt: float):
        """Per-frame state update.

        Drives the cast/bite/active state machine, polls input
        (mouse position, keyboard, mouse buttons) and updates the
        progress meter. The state machine transitions are:

        * ``idle``/``ready`` -- based on whether the fishing rod is equipped.
        * ``casting`` -- rolls for a bite every
          ``self.seek_interval`` seconds.
        * ``bite`` -- transitions to ``active`` once the
          "Hit!" overlay expires.
        * ``active`` -- updates the fish, reads input, computes
          overlap, fills/drains the progress bar, and ends the
          minigame on success or timeout.

        Args:
            dt (float): Elapsed time in seconds.
        """
        self.ui.update(dt)

        if self.bobber:
            self.bobber.update(dt)

        if self._can_fish():
            if self.state == "idle":
                self.state = "ready"
        else:
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
                    self.active_overlap_time = 0.0
                    self.active_total_time = 0.0
                    self.active_best_streak = 0.0
                    self.active_current_streak = 0.0

        elif self.state == "active":
            if self.active_fish:
                self.active_fish.update(dt)

            fish_pos_norm = self.active_fish.y_norm

            mouse_x, mouse_y = pygame.mouse.get_pos()
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
            reel_up_speed = 1.4
            sink_speed = 0.35

            if target_from_mouse is not None and not reeling:
                target_norm = max(0.0, min(1.0, target_from_mouse))
                self.catch_zone_offset += (target_norm - self.catch_zone_offset) * min(1.0, 12.0 * dt)
            else:
                if reeling:
                    self.catch_zone_offset = max(
                        0.0, self.catch_zone_offset - reel_up_speed * dt
                    )
                else:
                    self.catch_zone_offset = min(
                        1.0, self.catch_zone_offset + sink_speed * dt
                    )
            bobber_norm = self.catch_zone_offset

            bobber_size_frac = 14.0 / float(bar_h)
            difficulty = self.active_fish.fish_type.difficulty
            base_tol = 0.32 + (1.0 - difficulty) * 0.15
            tolerance = max(bobber_size_frac, base_tol)
            distance = abs(bobber_norm - fish_pos_norm)
            overlap = distance < tolerance

            if overlap:
                proximity = 1.0 - (distance / tolerance) if tolerance > 0 else 0.0
                accel = proximity * proximity
                base_fill = 60.0 * (1.0 - difficulty * 0.15)
                fill_rate = base_fill * accel
                self.catch_fill += fill_rate * dt
            else:
                drain_rate = 25.0 + difficulty * 8.0
                self.catch_fill -= drain_rate * dt
            self.catch_fill = max(0.0, min(self.catch_fill, self.catch_fill_max))

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

            self.active_time_left -= dt
            if self.catch_fill >= self.catch_fill_max:
                self._on_catch_success()
            elif self.active_time_left <= 0.0:
                self._on_catch_fail()
        else:
            self.active_overlap = False

    def _get_camera_offset_static(self) -> pygame.Vector2:
        """Return the current camera offset (with safe fallback).

        Returns:
            pygame.Vector2: The camera offset, or ``(0, 0)`` if it
            cannot be resolved.
        """
        try:
            return self.game._get_camera_offset()
        except Exception:
            return pygame.Vector2(0, 0)

    def _on_catch_success(self):
        """Handle a successful catch.

        Adds the fish's reward item to the world item list and
        shows a green "Caught ..." result message, then returns
        the controller to the ``idle`` state.
        """
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
        """Handle a failed catch (timeout).

        Shows a red "X escaped!" result message and returns the
        controller to the ``idle`` state.
        """
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
        """Draw the fishing UI to ``screen``.

        Any error during drawing is swallowed so that the host
        state's render loop is not interrupted.

        Args:
            screen (pygame.Surface): Target surface.
            camera_offset (pygame.Vector2): Current camera offset.
        """
        try:
            self.ui.draw(screen, camera_offset)
        except Exception:
            pass

    def handle_event(self, event: pygame.event.Event):
        """Dispatch a pygame event to the fishing state machine.

        Recognises the ``F`` key (cast) and right mouse button
        (cast) when in ``idle`` or ``ready`` state.

        Args:
            event (pygame.event.Event): The event to process.

        Returns:
            bool: ``True`` if the event was consumed, ``False``
            otherwise.
        """
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


