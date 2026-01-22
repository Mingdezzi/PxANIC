import pygame

class Entity:
    def __init__(self, x, y, width, height, name="Entity"):
        self.rect = pygame.Rect(x, y, width, height)
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.name = name
        self.width = width
        self.height = height
        
        self.alive = True
        self.is_moving = False
        self.facing_right = True
        self.facing_dir = (0, 1)
        
    def update(self, dt):
        pass

    def set_position(self, x, y):
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)
        
    @property
    def center(self):
        return self.rect.center
        
    @center.setter
    def center(self, value):
        self.rect.center = value
        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)
