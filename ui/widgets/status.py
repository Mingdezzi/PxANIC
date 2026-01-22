import pygame
from ui.widgets.base import UIWidget
from colors import COLORS

class PlayerStatusWidget(UIWidget):
    def __init__(self, game):
        super().__init__(game)
        self.width = 460 # Base init
        self.height = 140
        self.panel_bg = None

    def draw(self, screen):
        w, h = screen.get_size()
        
        # Dynamic Size (Balanced)
        self.width = max(350, int(w * 0.3))
        self.height = 160
        
        if not self.panel_bg or self.panel_bg.get_width() != self.width or self.panel_bg.get_height() != self.height:
            self.panel_bg = self.create_panel_bg(self.width, self.height)

        p = self.game.player
        x, y = 20, 20
        
        # 배경 그리기
        screen.blit(self.panel_bg, (x, y))

        role_cols = {
            'CITIZEN': (100, 200, 100), 
            'POLICE': (50, 50, 255), 
            'MAFIA': (200, 50, 50), 
            'DOCTOR': (200, 200, 255), 
            'SPECTATOR':(100,100,100)
        }
        c = role_cols.get(p.role, (200, 200, 200))
        
        # Avatar
        avatar_size = int(self.height * 0.7) # 70% of height
        avatar_rect = pygame.Rect(x + 20, y + (self.height - avatar_size)//2, avatar_size, avatar_size)
        pygame.draw.rect(screen, (40, 40, 40), avatar_rect, border_radius=10)
        pygame.draw.rect(screen, c, avatar_rect, 4, border_radius=10)
        
        # Initial
        role_char = p.role[0] 
        f_big = self.font_big # Automatically scaled by ResourceManager
        t_w, t_h = f_big.size(role_char)
        txt = f_big.render(role_char, True, c)
        screen.blit(txt, (avatar_rect.centerx - t_w//2, avatar_rect.centery - t_h//2))
        
        # Role text below avatar? might overlap if avatar is big
        # Put it inside avatar or just tooltip? 
        # Let's put it to the right of avatar, above bars
        
        bar_x = avatar_rect.right + 20
        remaining_w = self.width - (bar_x - x) - 20
        
        # Role Name & Subrole
        role_str = f"{p.role} [{p.sub_role}]" if p.sub_role else p.role
        f_small = self.font_small
        r_surf = f_small.render(role_str, True, (200, 200, 200))
        screen.blit(r_surf, (bar_x, y + 15))
        
        # Money
        f_digit = self.game.resource_manager.get_font('digit')
        coin_str = f"${p.coins}"
        c_surf = f_digit.render(coin_str, True, (255, 215, 0))
        # Right align money
        screen.blit(c_surf, (x + self.width - c_surf.get_width() - 20, y + 10))

        # Bars
        # Vertical space available below text
        bar_start_y = y + 45
        bar_h = int((self.height - 60) / 2)
        
        hp_ratio = max(0, p.hp / p.max_hp)
        self._draw_bar(screen, bar_x, bar_start_y, remaining_w, bar_h, hp_ratio, (220, 60, 60), "HP")
        
        ap_ratio = max(0, p.ap / p.max_ap)
        self._draw_bar(screen, bar_x, bar_start_y + bar_h + 5, remaining_w, bar_h, ap_ratio, (60, 150, 220), "AP")

    def _draw_bar(self, screen, x, y, w, h, ratio, color, label):
        pygame.draw.rect(screen, (40, 40, 40), (x, y, w, h), border_radius=4)
        fill_w = int(w * ratio)
        if fill_w > 0:
            pygame.draw.rect(screen, color, (x, y, fill_w, h), border_radius=4)
        for i in range(x, x+w, 10):
            pygame.draw.line(screen, (0,0,0,50), (i, y), (i+5, y+h), 1)
        l_surf = self.font_small.render(label, True, (200, 200, 200))
        screen.blit(l_surf, (x - 25, y - 2))
