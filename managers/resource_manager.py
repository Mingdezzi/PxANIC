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

    def set_font_scale(self, scale):
        self.current_scale = scale
        self._load_system_fonts()

    def _load_system_fonts(self):
        scale = getattr(self, 'current_scale', 1.0)
        
        # Base Sizes
        base_def = 18
        base_bold = 20
        base_large = 28
        base_title = 60
        base_small = 14
        
        # Scaled Sizes
        s_def = int(base_def * scale)
        s_bold = int(base_bold * scale)
        s_large = int(base_large * scale)
        s_title = int(base_title * scale)
        s_small = int(base_small * scale)

        font_name = "malgungothic"
        if font_name not in pygame.font.get_fonts():
            font_name = "arial"

        try:
            self.fonts['default'] = pygame.font.SysFont(font_name, s_def)
            self.fonts['bold'] = pygame.font.SysFont(font_name, s_bold, bold=True)
            self.fonts['large'] = pygame.font.SysFont(font_name, s_large)
            self.fonts['title'] = pygame.font.SysFont(font_name, s_title)
            self.fonts['small'] = pygame.font.SysFont(font_name, s_small)
            self.fonts['digit'] = pygame.font.SysFont("impact", s_large) # Added digit font
        except:
            self.logger.warning("RESOURCE", "Failed to load system fonts, using default")
            self.fonts['default'] = pygame.font.Font(None, s_def)
            self.fonts['bold'] = pygame.font.Font(None, s_bold)
            self.fonts['large'] = pygame.font.Font(None, s_large)
            self.fonts['title'] = pygame.font.Font(None, s_title)
            self.fonts['small'] = pygame.font.Font(None, s_small)
            self.fonts['digit'] = pygame.font.Font(None, s_large)

    def get_font(self, name):
        return self.fonts.get(name, self.fonts['default'])

    # [최적화] 이미지 로드 및 캐싱 메서드 추가
    def get_image(self, path, use_alpha=True):
        """이미지를 로드하고 디스플레이 포맷에 맞춰 최적화(convert)하여 반환"""
        if path in self.images:
            return self.images[path]
        
        try:
            if not os.path.exists(path):
                self.logger.error("RESOURCE", f"Image not found: {path}")
                return None
                
            img = pygame.image.load(path)
            # [핵심] 로드 직후 포맷 변환 (블리팅 속도 5~10배 향상)
            if use_alpha:
                img = img.convert_alpha()
            else:
                img = img.convert()
                
            self.images[path] = img
            return img
        except Exception as e:
            self.logger.error("RESOURCE", f"Failed to load image: {path} / {e}")
            return None
            
    def clear_cache(self):
        self.images.clear()
        # 폰트는 유지하거나 필요시 재생성