import pygame
from ui.widgets.base import UIWidget

class ControlsWidget(UIWidget):
    def draw(self, screen):
        w, h = screen.get_size()
        icon_size = max(60, int(h * 0.12)) # Balanced Size
        gap = 15
        start_x = 20
        start_y = h - (icon_size * 2 + gap) - 30 
        
        def get_pos(col, row):
            return start_x + col * (icon_size + gap), start_y + row * (icon_size + gap)

        self._draw_key_icon(screen, *get_pos(0, 0), "I", "인벤토리", icon_size)
        self._draw_key_icon(screen, *get_pos(1, 0), "Z", "투표", icon_size)
        self._draw_key_icon(screen, *get_pos(2, 0), "E", "상호작용", icon_size)
        
        role = self.game.player.role
        if role in ["CITIZEN", "DOCTOR"]:
            q_label = "동체탐지"
        elif role == "POLICE":
            q_label = "사이렌"
        else:
            q_label = "특수스킬"
        
        self._draw_key_icon(screen, *get_pos(0, 1), "Q", q_label, icon_size)
        self._draw_key_icon(screen, *get_pos(1, 1), "R", "재장전", icon_size)
        self._draw_key_icon(screen, *get_pos(2, 1), "V", "행동", icon_size)

    def _draw_key_icon(self, screen, x, y, key, label, size):
        rect = pygame.Rect(x, y, size, size)
        # 버튼 배경
        pygame.draw.rect(screen, (40, 40, 50), rect, border_radius=12)
        pygame.draw.rect(screen, (100, 100, 120), rect, 3, border_radius=12)
        
        # 1. 키 텍스트 (Top Left or Center?)
        # Let's put Key char in Top-Left, large
        f_main = self.font_main
        k_w, k_h = f_main.size(key)
        
        # If text is too big for icon (e.g. Space), scale it
        if k_w > size - 10:
             # Just use first char if too long? or Font scale?
             # For now assume single char keys mostly
             pass
             
        k_surf = f_main.render(key, True, (255, 255, 255))
        screen.blit(k_surf, (x + size//2 - k_w//2, y + size//2 - k_h//2 - 10))
        
        # 2. Label (Bottom Center)
        f_small = self.font_small
        l_w, l_h = f_small.size(label)
        
        # Scale down if label too wide
        if l_w > size - 4:
            scale = (size - 4) / l_w
            l_surf = pygame.transform.smoothscale(f_small.render(label, True, (200, 200, 200)), (int(l_w*scale), int(l_h*scale)))
            screen.blit(l_surf, (x + size//2 - l_surf.get_width()//2, y + size - l_surf.get_height() - 5))
        else:
            l_surf = f_small.render(label, True, (200, 200, 200))
            screen.blit(l_surf, (x + size//2 - l_w//2, y + size - l_h - 5))
