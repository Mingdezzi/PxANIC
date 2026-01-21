import pygame
import os
from systems.logger import GameLogger

class ResourceManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ResourceManager()
        return cls._instance

    def __init__(self):
        if ResourceManager._instance is not None:
            raise Exception("This class is a singleton!")
        ResourceManager._instance = self

        self.logger = GameLogger.get_instance()
        self.fonts = {}
        self.sounds = {}
        self.images = {} # [추가] 이미지 캐시

        self._load_system_fonts()

    def _load_system_fonts(self):
        font_name = "malgungothic"
        if font_name not in pygame.font.get_fonts():
            font_name = "arial"

        try:
            self.fonts['default'] = pygame.font.SysFont(font_name, 18)
            self.fonts['bold'] = pygame.font.SysFont(font_name, 20, bold=True)
            self.fonts['large'] = pygame.font.SysFont(font_name, 28)
            self.fonts['title'] = pygame.font.SysFont(font_name, 60)
            self.fonts['small'] = pygame.font.SysFont(font_name, 12)
        except:
            self.logger.warning("RESOURCE", "Failed to load system fonts, using default")
            self.fonts['default'] = pygame.font.Font(None, 24)
            self.fonts['bold'] = pygame.font.Font(None, 26)
            self.fonts['large'] = pygame.font.Font(None, 36)
            self.fonts['title'] = pygame.font.Font(None, 70)
            self.fonts['small'] = pygame.font.Font(None, 16)

    def get_font(self, name):
        return self.fonts.get(name, self.fonts['default'])