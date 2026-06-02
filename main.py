import pygame
import platform

if platform.system() == "Windows":
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            import ctypes

            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

pygame.init()

from src.app import App

if __name__ == "__main__":
    app = App()
    app.run()
    