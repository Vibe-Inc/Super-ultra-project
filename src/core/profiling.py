from __future__ import annotations

from collections import deque
import time

import pygame

import src.config as cfg


class FrameProfiler:
    """
    Frame timing overlay used to inspect performance during gameplay.

    Attributes:
        sample_size (int):
            Number of FPS samples kept for rolling averages.
        font_size (int):
            Font size used for the overlay text.
        enabled (bool):
            Whether the profiler is currently active.
        _font (pygame.font.Font | None):
            Cached font instance for drawing the overlay.
        _fps_samples (deque):
            Rolling list of recent FPS values.
        _section_start (dict[str, float]):
            Start times for named timing sections.
        _section_times (dict[str, float]):
            Measured duration of named timing sections in milliseconds.
        _section_order (list[str]):
            Rendering order for timing sections.
        _gauges (dict[str, object]):
            Miscellaneous profiler metrics.
        _frame_dt (float):
            Duration of the most recent frame in seconds.
        _last_report (dict | None):
            Cached data rendered by the overlay.

    Methods:
        __init__(sample_size=120, font_size=18):
            Initialize the profiler.
        set_enabled(enabled):
            Enable or disable the overlay.
        reset():
            Clear all collected profiling data.
        _ensure_font():
            Lazily build the overlay font.
        refresh_fonts():
            Rebuild fonts after a UI scale or language change.
        begin_frame(dt):
            Start a new frame and record frame timing.
        start_section(name):
            Mark the start of a named timing section.
        end_section(name):
            Mark the end of a named timing section.
        set_gauge(name, value):
            Store an arbitrary profiler value.
        end_frame():
            Finalize the current frame report.
        draw(screen, position=(12, 12)):
            Render the profiler overlay.
    """
    def __init__(self, sample_size: int = 120, font_size: int = 18):
        self.sample_size = sample_size
        self.font_size = font_size
        self.enabled = False
        self._font = None
        self._fps_samples = deque(maxlen=sample_size)
        self._section_start: dict[str, float] = {}
        self._section_times: dict[str, float] = {}
        self._section_order: list[str] = []
        self._gauges: dict[str, object] = {}
        self._frame_dt = 0.0
        self._last_report = None

    def set_enabled(self, enabled: bool):
        self.enabled = bool(enabled)
        if self.enabled:
            self.reset()
            self._ensure_font()
        else:
            self._last_report = None

    def reset(self):
        self._fps_samples.clear()
        self._section_start.clear()
        self._section_times.clear()
        self._section_order = []
        self._gauges = {}
        self._last_report = None
        self._font = None

    def _ensure_font(self):
        if self._font is None:
            self._font = cfg.get_font(self.font_size)

    def refresh_fonts(self):
        if self.enabled:
            self._font = cfg.get_font(self.font_size)

    def begin_frame(self, dt: float):
        if not self.enabled:
            return
        self._frame_dt = float(dt)
        fps = 1.0 / dt if dt > 0 else 0.0
        self._fps_samples.append(fps)
        self._section_start.clear()
        self._section_times.clear()
        self._section_order = []

    def start_section(self, name: str):
        if not self.enabled:
            return
        if name not in self._section_order:
            self._section_order.append(name)
        self._section_start[name] = time.perf_counter()

    def end_section(self, name: str):
        if not self.enabled:
            return
        start = self._section_start.pop(name, None)
        if start is None:
            return
        self._section_times[name] = (time.perf_counter() - start) * 1000.0

    def set_gauge(self, name: str, value: object):
        if not self.enabled:
            return
        self._gauges[name] = value

    def end_frame(self):
        if not self.enabled:
            return
        now = time.perf_counter()
        for name, start in list(self._section_start.items()):
            self._section_times[name] = (now - start) * 1000.0
        self._section_start.clear()

        fps_avg = sum(self._fps_samples) / len(self._fps_samples) if self._fps_samples else 0.0
        fps_now = self._fps_samples[-1] if self._fps_samples else 0.0
        self._last_report = {
            "fps": fps_now,
            "avg_fps": fps_avg,
            "frame_ms": self._frame_dt * 1000.0,
            "sections": [(name, self._section_times.get(name, 0.0)) for name in self._section_order],
            "gauges": dict(self._gauges),
        }

    def draw(self, screen: pygame.Surface, position: tuple[int, int] = (12, 12)):
        if not self.enabled:
            return
        self._ensure_font()

        report = self._last_report
        if report is None:
            lines = ["Profiler: collecting..."]
        else:
            lines = [
                "Profiler (F3): ON",
                f"FPS: {report['fps']:.1f} (avg {report['avg_fps']:.1f}) | Frame: {report['frame_ms']:.2f} ms",
            ]
            for name, ms in report["sections"]:
                lines.append(f"{name}: {ms:.2f} ms")
            if report["gauges"]:
                for key, value in report["gauges"].items():
                    lines.append(f"{key}: {value}")
            # add mouse cursor position (screen coordinates)
            try:
                mx, my = pygame.mouse.get_pos()
                lines.append(f"Mouse: ({mx}, {my})")
            except Exception:
                pass
            # show actual window size and configured size for debugging
            try:
                w = screen.get_width()
                h = screen.get_height()
                lines.append(f"Window: {w}x{h}")
                lines.append(f"Cfg: {cfg.SCREEN_WIDTH}x{cfg.SCREEN_HEIGHT}")
                if cfg.SCREEN_WIDTH:
                    scale = w / cfg.SCREEN_WIDTH
                    lines.append(f"Scale: {scale:.2f}x")
            except Exception:
                pass

        line_surfs = [self._font.render(line, True, (255, 255, 255)) for line in lines]
        max_width = max((surf.get_width() for surf in line_surfs), default=0)
        line_height = self._font.get_height()

        padding = 6
        total_width = max_width + padding * 2
        total_height = line_height * len(line_surfs) + padding * 2

        panel = pygame.Surface((total_width, total_height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 170))

        x, y = position
        margin = 8
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        x = max(margin, min(x, screen_width - total_width - margin))
        y = max(margin, min(y, screen_height - total_height - margin))
        screen.blit(panel, (x, y))
        for index, surf in enumerate(line_surfs):
            screen.blit(surf, (x + padding, y + padding + index * line_height))


class FpsCounter:
    """
    Lightweight rolling FPS display for the HUD.

    Attributes:
        sample_size (int):
            Number of FPS values to keep for smoothing.
        font_size (int):
            Font size used for the counter.
        update_interval (float):
            Minimum delay between text refreshes.
        enabled (bool):
            Whether the counter is currently active.
        _font (pygame.font.Font | None):
            Cached font instance.
        _samples (deque):
            Rolling list of recent FPS values.
        _last_update (float):
            Timestamp of the last text refresh.
        _text (str):
            Current text displayed by the counter.
        _text_surf (pygame.Surface | None):
            Cached rendered text surface.
        _max_text_width (int):
            Reserved width to avoid layout jitter.

    Methods:
        __init__(sample_size=60, font_size=18, update_interval=0.25):
            Initialize the FPS counter.
        _ensure_font():
            Lazily build the counter font.
        refresh_fonts():
            Rebuild fonts after a UI scale or language change.
        update(dt):
            Feed a new frame delta and refresh the displayed FPS.
        draw(screen, position=(12, 12), align_right=False):
            Render the FPS counter to the screen.
    """
    def __init__(self, sample_size: int = 60, font_size: int = 18, update_interval: float = 0.25):
        self.sample_size = sample_size
        self.font_size = font_size
        self.update_interval = update_interval
        self.enabled = True
        self._font = None
        self._samples = deque(maxlen=sample_size)
        self._last_update = 0.0
        self._text = "FPS: --"
        self._text_surf = None
        self._max_text_width = 0

    def _ensure_font(self):
        if self._font is None:
            self._font = cfg.get_font(self.font_size)
            self._text_surf = None
            self._max_text_width = self._font.size("FPS: 888.8")[0]

    def refresh_fonts(self):
        self._font = cfg.get_font(self.font_size)
        self._text_surf = None
        self._max_text_width = self._font.size("FPS: 888.8")[0]

    def update(self, dt: float):
        if not self.enabled:
            return
        fps = 1.0 / dt if dt > 0 else 0.0
        self._samples.append(fps)

        now = time.perf_counter()
        if now - self._last_update < self.update_interval:
            return

        avg = sum(self._samples) / len(self._samples) if self._samples else 0.0
        self._text = f"FPS: {avg:.1f}"
        self._text_surf = None
        self._last_update = now

    def draw(
        self,
        screen: pygame.Surface,
        position: tuple[int, int] = (12, 12),
        align_right: bool = False,
    ):
        if not self.enabled:
            return
        self._ensure_font()

        if self._text_surf is None:
            self._text_surf = self._font.render(self._text, True, (255, 255, 255))

        padding = 5
        width = max(self._text_surf.get_width(), self._max_text_width) + padding * 2
        height = self._text_surf.get_height() + padding * 2

        x, y = position
        if align_right:
            x -= width
            if x < 0:
                x = 0

        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 170))
        screen.blit(panel, (x, y))
        screen.blit(self._text_surf, (x + padding, y + padding))
