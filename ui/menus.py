import pygame
from ui.widgets.base import UIWidget
from settings import ITEMS, FPS

class PopupManager(UIWidget):
    def __init__(self, game):
        super().__init__(game)
        self.dim_surface = None
        self.spectator_scroll_y = 0
        self.skip_btn_rect = None
        self.entity_rects = []

    def draw_inventory(self, screen, w, h, sel_idx):
        iw, ih = 500, 400; rect_obj = pygame.Rect(w//2 - iw//2, h//2 - ih//2, iw, ih)
        pygame.draw.rect(screen, (30, 30, 40), rect_obj); pygame.draw.rect(screen, (255, 255, 0), rect_obj, 2)
        screen.blit(self.font_big.render("INVENTORY", True, (255, 255, 0)), (rect_obj.x + 20, rect_obj.y + 20))
        items_list = list(ITEMS.keys())
        grid_cols, slot_size, gap = 5, 60, 15; start_x, start_y = rect_obj.x + 30, rect_obj.y + 70
        for i, key in enumerate(items_list):
            row, col = i // grid_cols, i % grid_cols; x, y = start_x + col * (slot_size + gap), start_y + row * (slot_size + gap); r = pygame.Rect(x, y, slot_size, slot_size)
            count = self.game.player.inventory.get(key, 0); self._draw_item_icon(screen, key, r, sel_idx == i)
            if count > 0:
                cnt_txt = self.font_small.render(str(count), True, (255, 255, 255))
                screen.blit(cnt_txt, cnt_txt.get_rect(bottomright=(r.right-2, r.bottom-2)))
            else:
                s = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA); s.fill((0, 0, 0, 150)); screen.blit(s, r)
        if 0 <= sel_idx < len(items_list):
            key = items_list[sel_idx]; data = ITEMS[key]; info_y = rect_obj.bottom - 100
            pygame.draw.line(screen, (100, 100, 100), (rect_obj.x, info_y), (rect_obj.right, info_y))
            screen.blit(self.font_main.render(data['name'], True, (255, 255, 255)), (rect_obj.x + 30, info_y + 15))
            screen.blit(self.font_small.render(f"Owned: {self.game.player.inventory.get(key,0)}", True, (200, 200, 200)), (rect_obj.x + 30, info_y + 45))
            screen.blit(self.font_small.render(data['desc'], True, (150, 150, 150)), (rect_obj.x + 30, info_y + 70))

    def draw_vending_machine(self, screen, w, h, sel_idx):
        vw, vh = 600, 500; rect_obj = pygame.Rect(w//2 - vw//2, h//2 - vh//2, vw, vh)
        pygame.draw.rect(screen, (20, 20, 30), rect_obj); pygame.draw.rect(screen, (0, 255, 255), rect_obj, 3)
        screen.blit(self.font_big.render("SHOP", True, (0, 255, 255)), (rect_obj.x + 20, rect_obj.y + 20))
        items_list = list(ITEMS.keys())
        grid_cols, slot_size, gap = 5, 60, 15; start_x, start_y = rect_obj.x + 30, rect_obj.y + 70
        for i, key in enumerate(items_list):
            row, col = i // grid_cols, i % grid_cols; x, y = start_x + col * (slot_size + gap), start_y + row * (slot_size + gap)
            self._draw_item_icon(screen, key, pygame.Rect(x, y, slot_size, slot_size), sel_idx == i)
        if 0 <= sel_idx < len(items_list):
            key = items_list[sel_idx]; data = ITEMS[key]; info_y = rect_obj.bottom - 120
            pygame.draw.line(screen, (100, 100, 100), (rect_obj.x, info_y), (rect_obj.right, info_y))
            screen.blit(self.font_main.render(data['name'], True, (255, 255, 255)), (rect_obj.x + 30, info_y + 15))
            screen.blit(self.font_small.render(f"Price: {data['price']}G", True, (255, 215, 0)), (rect_obj.x + 30, info_y + 45))
            screen.blit(self.font_small.render(data['desc'], True, (200, 200, 200)), (rect_obj.x + 30, info_y + 75))

    def _draw_item_icon(self, screen, key, rect, is_sel):
        col = (60, 60, 80) if not is_sel else (100, 100, 150)
        pygame.draw.rect(screen, col, rect, border_radius=5)
        if is_sel: pygame.draw.rect(screen, (255, 255, 0), rect, 2, border_radius=5)
        c = rect.center
        if key == 'TANGERINE': pygame.draw.circle(screen, (255, 165, 0), c, 10)
        elif key == 'CHOCOBAR': pygame.draw.rect(screen, (139, 69, 19), (c[0]-8, c[1]-12, 16, 24))
        elif key == 'MEDKIT': 
            pygame.draw.rect(screen, (255, 255, 255), (c[0]-10, c[1]-8, 20, 16))
            pygame.draw.line(screen, (255, 0, 0), (c[0], c[1]-5), (c[0], c[1]+5), 2); pygame.draw.line(screen, (255, 0, 0), (c[0]-5, c[1]), (c[0]+5, c[1]), 2)
        elif key == 'KEY': pygame.draw.line(screen, (255, 215, 0), (c[0]-5, c[1]+5), (c[0]+5, c[1]-5), 3)
        elif key == 'BATTERY': pygame.draw.rect(screen, (0, 255, 0), (c[0]-6, c[1]-10, 12, 20))
        elif key == 'TASER': pygame.draw.rect(screen, (50, 50, 200), (c[0]-10, c[1]-5, 20, 10))
        else: pygame.draw.circle(screen, (200, 200, 200), c, 5)

    def draw_vote_ui(self, screen, w, h):
        if self.game.current_phase != "VOTE": return
        center_x = w // 2
        msg = self.font_big.render("VOTING SESSION", True, (255, 50, 50))
        screen.blit(msg, (center_x - msg.get_width()//2, 100))
        desc = self.font_main.render("Press 'Z' to Vote", True, (200, 200, 200))
        screen.blit(desc, (center_x - desc.get_width()//2, 140))

    def draw_vote_popup(self, screen, sw, sh, npcs, player, current_target):
        w, h = 400, 500
        cx, cy = sw // 2, sh // 2
        panel_rect = pygame.Rect(cx - w//2, cy - h//2, w, h)
        
        if self.dim_surface is None or self.dim_surface.get_size() != (sw, sh):
             self.dim_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)
             self.dim_surface.fill((0, 0, 0, 150))
        screen.blit(self.dim_surface, (0, 0))
        
        pygame.draw.rect(screen, (40, 40, 45), panel_rect, border_radius=12)
        pygame.draw.rect(screen, (100, 100, 120), panel_rect, 2, border_radius=12)
        title = self.font_big.render("VOTE TARGET", True, (255, 255, 255))
        screen.blit(title, (cx - title.get_width()//2, panel_rect.top + 20))
        candidates = [player] + [n for n in npcs if n.alive]
        candidate_rects = []
        start_y = panel_rect.top + 80
        for c in candidates:
            row_rect = pygame.Rect(panel_rect.left + 20, start_y, w - 40, 40)
            is_selected = (current_target == c)
            col = (50, 50, 150) if is_selected else (60, 60, 70)
            if row_rect.collidepoint(pygame.mouse.get_pos()):
                col = (80, 80, 100)
            pygame.draw.rect(screen, col, row_rect, border_radius=4)
            info = f"{c.name} ({c.role})"
            t = self.font_main.render(info, True, (220, 220, 220))
            screen.blit(t, (row_rect.left + 10, row_rect.centery - t.get_height()//2))
            candidate_rects.append((c, row_rect))
            start_y += 50
        return candidate_rects

    def draw_daily_news(self, screen, w, h, news_text):
        if self.dim_surface is None or self.dim_surface.get_size() != (w, h):
             self.dim_surface = pygame.Surface((w, h), pygame.SRCALPHA)
             self.dim_surface.fill((0, 0, 0, 150))
        screen.blit(self.dim_surface, (0, 0))
        
        center_x, center_y = w // 2, h // 2
        paper_w, paper_h = 500, 600
        paper_rect = pygame.Rect(center_x - paper_w//2, center_y - paper_h//2, paper_w, paper_h)
        pygame.draw.rect(screen, (240, 230, 200), paper_rect)
        pygame.draw.rect(screen, (100, 90, 80), paper_rect, 4)
        title = self.font_big.render("DAILY NEWS", True, (50, 40, 30))
        screen.blit(title, (center_x - title.get_width()//2, paper_rect.top + 30))
        line_y = paper_rect.top + 80
        pygame.draw.line(screen, (50, 40, 30), (paper_rect.left + 20, line_y), (paper_rect.right - 20, line_y), 2)
        y_offset = 110
        for line in news_text:
            t = self.font_main.render(line, True, (20, 20, 20))
            screen.blit(t, (center_x - t.get_width()//2, paper_rect.top + y_offset))
            y_offset += 35
        close_txt = self.font_small.render("Press SPACE to Close", True, (100, 100, 100))
        screen.blit(close_txt, (center_x - close_txt.get_width()//2, paper_rect.bottom - 40))

    def draw_spectator_ui(self, screen, w, h):
        # 1. 상단 제어바 (PHASE SKIP)
        self.skip_btn_rect = pygame.Rect(w - 140, 10, 130, 35)
        pygame.draw.rect(screen, (150, 50, 50), self.skip_btn_rect, border_radius=6)
        pygame.draw.rect(screen, (200, 70, 70), self.skip_btn_rect, 2, border_radius=6)
        txt = self.font_small.render("PHASE SKIP", True, (255, 255, 255))
        screen.blit(txt, (self.skip_btn_rect.centerx - txt.get_width()//2, self.skip_btn_rect.centery - txt.get_height()//2))
        
        # 2. 엔티티 상세 대시보드 (영역 고정)
        top_margin = 110
        bottom_limit = h - 260 
        sidebar_w = 270
        sidebar_h = max(100, bottom_limit - top_margin)
        sidebar_x = w - sidebar_w - 10
        sidebar_y = top_margin
        
        # 영역 배경 (반투명 어둡게)
        bg_panel = pygame.Surface((sidebar_w, sidebar_h), pygame.SRCALPHA)
        bg_panel.fill((20, 20, 25, 180)) 
        screen.blit(bg_panel, (sidebar_x, sidebar_y))
        pygame.draw.rect(screen, (60, 60, 70), (sidebar_x, sidebar_y, sidebar_w, sidebar_h), 1)
        
        # 리스트 렌더링 영역 제한
        old_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(sidebar_x, sidebar_y, sidebar_w, sidebar_h))
        
        self.entity_rects = []
        curr_y = sidebar_y + 10 - self.spectator_scroll_y
        
        all_entities = [self.game.player] + self.game.npcs
        pov_target = getattr(self.game, 'pov_target', None)
        
        for ent in all_entities:
            if not ent.alive or ent.role == "SPECTATOR": continue
            
            card_h = 75 
            r = pygame.Rect(sidebar_x + 5, curr_y, sidebar_w - 10, card_h)
            
            # POV 대상 강조
            is_pov = (pov_target == ent)
            bg_col = (60, 60, 80) if is_pov else (40, 40, 45)
            border_col = (255, 215, 0) if is_pov else (70, 70, 80)
            
            role_col = (100, 255, 100)
            if ent.role == "MAFIA": role_col = (255, 70, 70)
            elif ent.role == "POLICE": role_col = (70, 150, 255)
            elif ent.role == "DOCTOR": role_col = (240, 240, 250)
            
            pygame.draw.rect(screen, bg_col, r, border_radius=6)
            pygame.draw.rect(screen, border_col, r, 2 if is_pov else 1, border_radius=6)
            
            # 이름 및 직업
            name_txt = self.font_main.render(ent.name, True, (255, 255, 255))
            
            # [수정] 직업 표기 로직 강화 (RANDOM 방지)
            display_role = ent.role
            if ent.role == "CITIZEN" and getattr(ent, 'sub_role', None):
                display_role = f"{ent.sub_role}"
            elif ent.role == "RANDOM":
                display_role = "Assigning..." # 아직 서버 패킷 대기 중
                
            role_txt = self.font_small.render(display_role, True, role_col)
            screen.blit(name_txt, (r.left + 10, r.top + 5))
            screen.blit(role_txt, (r.right - role_txt.get_width() - 10, r.top + 8))
            
            # HP/AP 바
            bar_w = r.width - 20
            pygame.draw.rect(screen, (60, 20, 20), (r.left + 10, r.top + 32, bar_w, 5))
            pygame.draw.rect(screen, (255, 50, 50), (r.left + 10, r.top + 32, bar_w * (ent.hp/ent.max_hp), 5))
            pygame.draw.rect(screen, (20, 40, 20), (r.left + 10, r.top + 40, bar_w, 5))
            pygame.draw.rect(screen, (50, 255, 50), (r.left + 10, r.top + 40, bar_w * (ent.ap/ent.max_ap), 5))
            
            # 하단 정보
            coin_txt = self.font_small.render(f"{ent.coins}G", True, (255, 215, 0))
            status_str = "IDLE"
            if ent.is_hiding: status_str = "HIDING"
            elif getattr(ent, 'is_working', False): status_str = "WORKING"
            elif getattr(ent, 'chase_target', None): status_str = "CHASING"
            elif ent.is_moving: status_str = "MOVING"
            status_txt = self.font_small.render(status_str, True, (200, 200, 200))
            
            screen.blit(coin_txt, (r.left + 10, r.top + 52))
            screen.blit(status_txt, (r.right - status_txt.get_width() - 10, r.top + 52))

            self.entity_rects.append((r, ent))
            curr_y += card_h + 8
            
        screen.set_clip(old_clip) 



    def draw(self, screen):
        pass # Placeholder
