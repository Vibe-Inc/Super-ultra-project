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

# Ensure project root is on sys.path so 'src' package is importable when running this script directly
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import App

if __name__ == "__main__":
    app = App()
    app.run()
    