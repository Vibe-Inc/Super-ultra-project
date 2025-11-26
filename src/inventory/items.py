import pygame

class TEST_ITEMS:     #only for testing 
    def __init__(self, color, id):
        self.id = id
        self.color = color
    def resize(self, size):
        surf = pygame.Surface((size, size))
        pygame.draw.rect(surf, self.color, (0, 0, size, size))
        return surf