import pygame
from ui.widgets.base import UIWidget
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE
from colors import CUSTOM_COLORS as COLORS 
from systems.renderer import CharacterRenderer
from assets.character_parts import *

# Define some custom colors just for this UI
# [상수 정의: UI 레이아웃]
# UI 배치를 위한 크기 및 간격 상수 (Magic Number 제거)
LAYOUT_PREVIEW_W = 300    # 좌측 미리보기 패널 너비
LAYOUT_TAB_H = 40         # 대분류 탭 높이
LAYOUT_TAB_W = 90         # 대분류 탭 너비
LAYOUT_SUB_H = 35         # 소분류 탭 높이
LAYOUT_SUB_W = 110        # 소분류 탭 너비
LAYOUT_CELL_SIZE = 80     # 아이템 그리드 셀 크기
LAYOUT_GAP = 15           # 그리드 간격
LAYOUT_MARGIN = 20        # 패널 간 여백

C_BG = (20, 20, 25)
C_PANEL = (30, 30, 35)
C_BTN = (50, 50, 60)
C_BTN_HOVER = (70, 70, 80)
C_BTN_SELECTED = (80, 100, 80)
C_TEXT = (200, 200, 200)

class MockEntity:
    def __init__(self, c): 
        self.custom = c
        self.alive = True
        self.rect = pygame.Rect(0,0,32,32)
        self.role = "CITIZEN"
        self.sub_role = None
        self.is_hiding = False
        self.facing_dir = (0, 1)
        self.name = ""

class CustomizerWidget(UIWidget):
    """
    [커스터마이징 위젯]
    플레이어 캐릭터의 외형(몸, 얼굴, 옷, 액세서리)을 꾸미는 UI입니다.
    좌측에는 실시간 미리보기(Preview)를, 우측에는 탭 방식의 선택화면을 제공합니다.
    """
    def __init__(self, game):
        super().__init__(game)
        self.active = False
        self.categories = ['BODY', 'FACE', 'HAIR', 'CLOTHES', 'ACC', 'MOVE']
        self.current_tab_idx = 0
        self.sub_tab_idx = 0 
        
        # Sub-categories
        self.sub_cats = {
            'BODY': ['TYPE', 'SKIN'],
            'FACE': ['EYES', 'EYE COLOR', 'BROWS', 'BROWS COL', 'MOUTH', 'BEARD', 'BEARD COL'], 
            'HAIR': ['STYLE', 'COLOR'],
            'CLOTHES': ['TOP', 'TOP COLOR', 'BOTTOM', 'BTM COLOR', 'SHOES', 'SHOE COLOR', 'COAT', 'COAT COL'],
            'ACC': ['HAT', 'HAT COLOR', 'GLASSES', 'GLS COLOR'],
            'MOVE': ['STYLE']
        }
        
        self.preview_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 50, 200, 300)
        self.color_palette_grid = [] 
        self.part_grid = [] 
        
        self.temp_custom = {} 
        self.animation_timer = 0
        
        # Dot Editor State
        self.editor_active = False
        self.editor_target = None 
        self.editor_grid = [[(0,0,0,0) for _ in range(16)] for _ in range(16)]
        self.editor_color = (0, 0, 0)
        
        self.font = pygame.font.SysFont("arial", 16)
        self.font_big = pygame.font.SysFont("arial", 24, bold=True)
        
        self.preview_surface = None
        
        self.target_entity = None # Fix Attribute Error

    def open(self):
        self.active = True
        if hasattr(self.game, 'player') and self.game.player:
            self.source_data = self.game.player.custom
            self.target_entity = self.game.player # Set Target Entity
        else:
             if 'custom' not in self.game.shared_data: self.game.shared_data['custom'] = {}
             self.source_data = self.game.shared_data['custom']
             
        import copy
        self.temp_custom = copy.deepcopy(self.source_data)
        
        # Ensure minimal structure
        if 'clothes' not in self.temp_custom: self.temp_custom['clothes'] = {}
        if 'eyes' not in self.temp_custom: self.temp_custom['eyes'] = {}
        if 'mouth' not in self.temp_custom: self.temp_custom['mouth'] = {}
        if 'hair' not in self.temp_custom: self.temp_custom['hair'] = {}
        if 'acc' not in self.temp_custom: self.temp_custom['acc'] = {}
            
        self._update_preview()

    def close(self):
        self.active = False
        if hasattr(self.game, 'player') and self.game.player:
            self.game.player.custom = self.temp_custom
        else:
            self.game.shared_data['custom'] = self.temp_custom
            
            # [Fix] Use DataManager for centralized saving
            from managers.data_manager import DataManager
            dm = DataManager.get_instance()
            dm.profile['custom'] = self.temp_custom
            dm.profile['name'] = self.game.shared_data.get('player_name', 'Player') # Sync name too
            dm.save_user_profile()
            print(f"[Customizer] Profile saved via DataManager.")
        
    def handle_event(self, event):
        """
        [이벤트 처리]
        마우스 클릭 이벤트를 처리하여 탭 전환, 아이템 선택, 저장 등을 수행합니다.
        """
        if not self.active: return False
        
        if self.editor_active:
            return self._handle_editor_event(event)
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
                
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            # --- 레이아웃 계산 (상수 사용) ---
            # 1. 메인 콘텐츠 영역 (우측)
            content_x = LAYOUT_PREVIEW_W + LAYOUT_MARGIN
            content_w = SCREEN_WIDTH - content_x - LAYOUT_MARGIN
            
            # 2. 메인 탭 (Main Tabs) - 상단
            tab_start_y = 20
            for i, cat in enumerate(self.categories):
                rect = pygame.Rect(content_x + i*(LAYOUT_TAB_W+5), tab_start_y, LAYOUT_TAB_W, LAYOUT_TAB_H)
                if rect.collidepoint(mx, my):
                    self.current_tab_idx = i
                    self.sub_tab_idx = 0
                    return True
                    
            # 3. 서브 탭 (Sub Tabs) - 메인 탭 하단
            current_cat = self.categories[self.current_tab_idx]
            subs = self.sub_cats[current_cat]
            sub_start_y = tab_start_y + LAYOUT_TAB_H + 10
            
            # 멀티 라인 처리 (필요 시)
            for i, sub in enumerate(subs):
                col_idx = i % 4 
                row_idx = i // 4
                rect = pygame.Rect(content_x + col_idx*(LAYOUT_SUB_W+5), sub_start_y + row_idx*(LAYOUT_SUB_H+5), LAYOUT_SUB_W, LAYOUT_SUB_H)
                if rect.collidepoint(mx, my):
                    self.sub_tab_idx = i
                    return True
            
            # 4. 아이템 그리드 (Item Grid)
            grid_start_y = sub_start_y + (LAYOUT_SUB_H+5)*2 + 20
            
            cat = self.categories[self.current_tab_idx]
            sub = subs[self.sub_tab_idx]
            
            # 3x3 그리드 클릭 체크
            for i in range(9):
                col = i % 3
                row = i // 3
                rect = pygame.Rect(content_x + col*(LAYOUT_CELL_SIZE+LAYOUT_GAP), grid_start_y + row*(LAYOUT_CELL_SIZE+LAYOUT_GAP), LAYOUT_CELL_SIZE, LAYOUT_CELL_SIZE)
                if rect.collidepoint(mx, my):
                    self._apply_part(cat, sub, i)
                    return True
            
            # Dot Editor 버튼 (그리드 우측)
            edit_btn = pygame.Rect(content_x + 3*(LAYOUT_CELL_SIZE+LAYOUT_GAP) + 20, grid_start_y, 100, 40)
            if edit_btn.collidepoint(mx, my):
                self.editor_active = True
                self.editor_target = f"{cat}_{sub}"
                return True

            # 저장 버튼 (우측 하단)
            save_rect = pygame.Rect(SCREEN_WIDTH - 150, SCREEN_HEIGHT - 60, 120, 50)
            if save_rect.collidepoint(mx, my):
                # 플레이어 및 데이터 매니저에 적용
                if self.target_entity:
                    self.target_entity.custom = self.temp_custom.copy()
                    
                from managers.data_manager import DataManager
                dm = DataManager.get_instance()
                dm.profile['custom'] = self.temp_custom.copy()
                dm.save_user_profile()
                
                self.close()
                return True
                
        return True

    def _apply_part(self, cat, sub, idx):
        if cat == 'BODY':
            if sub == 'TYPE': self.temp_custom['body_type'] = idx
            elif sub == 'SKIN': self.temp_custom['skin'] = idx
        elif cat == 'FACE':
            if 'eyes' not in self.temp_custom: self.temp_custom['eyes'] = {}
            if 'mouth' not in self.temp_custom: self.temp_custom['mouth'] = {}
            
            if sub == 'EYES': self.temp_custom['eyes']['id'] = idx
            elif sub == 'EYE COLOR': self.temp_custom['eyes']['color'] = idx
            elif sub == 'BROWS': self.temp_custom['eyes']['brow_id'] = idx
            elif sub == 'BROWS COL': self.temp_custom['eyes']['brow_color'] = idx
            elif sub == 'MOUTH': self.temp_custom['mouth']['id'] = idx
            elif sub == 'BEARD': self.temp_custom['mouth']['beard'] = idx
            elif sub == 'BEARD COL': self.temp_custom['mouth']['beard_color'] = idx
            
        elif cat == 'HAIR':
            if 'hair' not in self.temp_custom: self.temp_custom['hair'] = {}
            if sub == 'STYLE': self.temp_custom['hair']['id'] = idx
            elif sub == 'COLOR': self.temp_custom['hair']['color'] = idx
            
        elif cat == 'CLOTHES':
            if 'clothes' not in self.temp_custom: self.temp_custom['clothes'] = {}
            if sub == 'TOP': self.temp_custom['clothes']['top'] = idx
            elif sub == 'TOP COLOR': self.temp_custom['clothes']['top_color'] = idx
            elif sub == 'BOTTOM': self.temp_custom['clothes']['bottom'] = idx
            elif sub == 'BTM COLOR': self.temp_custom['clothes']['bottom_color'] = idx
            elif sub == 'SHOES': self.temp_custom['clothes']['shoes'] = idx
            elif sub == 'SHOE COLOR': self.temp_custom['clothes']['shoes_color'] = idx
            elif sub == 'COAT': self.temp_custom['clothes']['coat'] = idx
            elif sub == 'COAT COL': self.temp_custom['clothes']['coat_color'] = idx
            
        elif cat == 'ACC':
            if 'acc' not in self.temp_custom: self.temp_custom['acc'] = {}
            if sub == 'HAT': self.temp_custom['hat'] = idx
            elif sub == 'HAT COLOR': self.temp_custom['hat_color'] = idx
            elif sub == 'GLASSES': self.temp_custom['acc']['glasses'] = idx
            elif sub == 'GLS COLOR': self.temp_custom['acc']['glasses_color'] = idx
            
        elif cat == 'MOVE':
             self.temp_custom['move_style'] = idx
             
        self._update_preview()

    def update(self, dt):
        if not self.active: return
        self.animation_timer += dt
        # Re-render preview every few frames or every frame for smooth animation
        # Optimization: Only if needed?
        # Let's do every frame for smooth bobbing
        self._update_preview()

    def _update_preview(self):
        """
        [미리보기 갱신]
        캐릭터 렌더러를 사용하여 미리보기용 더미 캐릭터를 그립니다.
        걷기/달리기/숨기 등의 애니메이션 사이클을 시뮬레이션합니다.
        """
        # 미리보기 서피스 캐싱
        dummy_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        mock = MockEntity(self.temp_custom)
        mock.anim_tick = self.animation_timer
        
        # 시뮬레이션 사이클 (6초 루프): 걷기 -> 달리기 -> 숨기 -> 대기
        cycle_t = self.animation_timer % 6.0
        
        if cycle_t < 2.0:
            mock.is_moving = True; mock.move_state = "WALK"; mock.is_hiding = False
        elif cycle_t < 4.0:
            mock.is_moving = True; mock.move_state = "RUN"; mock.is_hiding = False
        elif cycle_t < 5.0:
            mock.is_moving = False; mock.move_state = "WALK"; mock.is_hiding = True # 숨기 동작
        else:
            mock.is_moving = False; mock.move_state = "WALK"; mock.is_hiding = False # 대기
            
        # 렌더러 호출 (Native Renderer Animation)
        CharacterRenderer.draw_entity(dummy_surf, mock, 0, 0) 
        self.preview_surface = pygame.transform.scale(dummy_surf, (200, 200))

    def draw(self, screen):
        """
        [화면 그리기]
        UI 전체 요소(배경, 미리보기, 탭, 아이템 그리드)를 렌더링합니다.
        """
        if not self.active: return
        
        # 애니메이션 타이머 업데이트
        self.animation_timer = pygame.time.get_ticks() / 1000.0
        self._update_preview()
        
        # 배경 딤 처리 (Dimming)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(C_BG)
        screen.blit(overlay, (0, 0))
        
        if self.editor_active:
            self._draw_editor(screen)
            return

        # 레이아웃 상수 사용
        content_x = LAYOUT_PREVIEW_W + LAYOUT_MARGIN
        
        # --- [좌측 패널: 미리보기] ---
        pygame.draw.rect(screen, (15, 15, 20), (0, 0, LAYOUT_PREVIEW_W, SCREEN_HEIGHT))
        pygame.draw.line(screen, (40, 40, 50), (LAYOUT_PREVIEW_W, 0), (LAYOUT_PREVIEW_W, SCREEN_HEIGHT), 2)
        
        # 캐릭터 미리보기 그리기
        center_x = LAYOUT_PREVIEW_W // 2
        center_y = SCREEN_HEIGHT // 2
        pygame.draw.circle(screen, (25, 25, 30), (center_x, center_y), 120)
        
        if self.preview_surface:
             big_preview = pygame.transform.scale(self.preview_surface, (256, 256))
             screen.blit(big_preview, (center_x - 128, center_y - 128))
             
        lbl = self.font_big.render("PREVIEW", True, (100, 100, 100))
        screen.blit(lbl, (center_x - lbl.get_width()//2, 50))


        # --- [우측 패널: 컨트롤] ---
        
        # 1. 메인 탭 (Main Tabs)
        tab_start_y = 20
        for i, cat in enumerate(self.categories):
            is_sel = (i == self.current_tab_idx)
            col = C_BTN_SELECTED if is_sel else C_BTN
            rect = pygame.Rect(content_x + i*(LAYOUT_TAB_W+5), tab_start_y, LAYOUT_TAB_W, LAYOUT_TAB_H)
            
            mx, my = pygame.mouse.get_pos()
            if rect.collidepoint(mx, my) and not is_sel: col = C_BTN_HOVER
            
            pygame.draw.rect(screen, col, rect, border_radius=5)
            if is_sel: pygame.draw.rect(screen, (200, 200, 200), rect, 2, border_radius=5)
            
            txt = self.font.render(cat, True, C_TEXT if is_sel else (150,150,150))
            screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

        # 2. 서브 탭 (Sub Tabs)
        current_cat = self.categories[self.current_tab_idx]
        subs = self.sub_cats[current_cat]
        sub_start_y = tab_start_y + LAYOUT_TAB_H + 10
        
        for i, sub in enumerate(subs):
            is_sel = (i == self.sub_tab_idx)
            col = (60, 60, 70) if is_sel else (30, 30, 35)
            
            col_idx = i % 4
            row_idx = i // 4
            rect = pygame.Rect(content_x + col_idx*(LAYOUT_SUB_W+5), sub_start_y + row_idx*(LAYOUT_SUB_H+5), LAYOUT_SUB_W, LAYOUT_SUB_H)

            pygame.draw.rect(screen, col, rect, border_radius=15)
            if is_sel: pygame.draw.rect(screen, (100, 180, 100), rect, 2, border_radius=15)
            
            txt = self.font.render(sub, True, (220, 220, 220) if is_sel else (120, 120, 120))
            screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

        # 3. 아이템 그리드 (Selection Grid)
        grid_start_y = sub_start_y + (LAYOUT_SUB_H+5)*2 + 20
        
        current_sub = subs[self.sub_tab_idx]
        
        # 그리드 배경
        grid_width = 3 * (LAYOUT_CELL_SIZE + LAYOUT_GAP)
        grid_bg_rect = pygame.Rect(content_x - 10, grid_start_y - 10, grid_width + 10, grid_width + 10)
        pygame.draw.rect(screen, (25, 25, 30), grid_bg_rect, border_radius=10)
        
        category_lbl = self.font.render(f"Select {current_sub}", True, (150, 150, 160))
        screen.blit(category_lbl, (content_x, grid_start_y - 30))

        for i in range(9):
            col_idx = i % 3
            row_idx = i // 3
            rect = pygame.Rect(content_x + col_idx*(LAYOUT_CELL_SIZE+LAYOUT_GAP), grid_start_y + row_idx*(LAYOUT_CELL_SIZE+LAYOUT_GAP), LAYOUT_CELL_SIZE, LAYOUT_CELL_SIZE)
            
            # Hover 효과
            mx, my = pygame.mouse.get_pos()
            is_hover = rect.collidepoint(mx, my)
            
            bg_col = (50, 50, 60) if is_hover else (40, 40, 45)
            pygame.draw.rect(screen, bg_col, rect, border_radius=8)
            
            # [리팩토링] CharacterRenderer의 공용 메서드 사용
            CharacterRenderer.draw_part_icon(screen, rect, current_cat, current_sub, i)

        # Dot Editor 버튼
        edit_btn = pygame.Rect(content_x + 3*(LAYOUT_CELL_SIZE+LAYOUT_GAP) + 20, grid_start_y, 140, 40)
        pygame.draw.rect(screen, (70, 70, 90), edit_btn, border_radius=5)
        txt = self.font.render("Dot Editor", True, (200,200,200))
        screen.blit(txt, (edit_btn.centerx - txt.get_width()//2, edit_btn.centery - txt.get_height()//2))

        # 저장 및 종료 버튼
        save_rect = pygame.Rect(SCREEN_WIDTH - 170, SCREEN_HEIGHT - 70, 140, 50)
        pygame.draw.rect(screen, C_BTN_SELECTED, save_rect, border_radius=8)
        # 그림자 효과
        pygame.draw.rect(screen, (40, 60, 40), save_rect.move(0, 4), border_radius=8)
        pygame.draw.rect(screen, C_BTN_SELECTED, save_rect, border_radius=8) 
        
        txt = self.font_big.render("SAVE & EXIT", True, (220, 220, 220))
        screen.blit(txt, (save_rect.centerx - txt.get_width()//2, save_rect.centery - txt.get_height()//2))

    # [제거됨] _draw_icon_content는 시스템 중복을 줄이기 위해 CharacterRenderer.draw_part_icon으로 대체되었습니다.

    def _handle_editor_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            close_rect = pygame.Rect(SCREEN_WIDTH - 100, 20, 80, 40)
            if close_rect.collidepoint(mx, my):
                self.editor_active = False
                return True
        return True

    def _draw_editor(self, screen):
        # ... (Same as before)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((10, 10, 15))
        overlay.set_alpha(200)
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(100, 50, SCREEN_WIDTH-200, SCREEN_HEIGHT-100)
        pygame.draw.rect(screen, (30, 30, 40), panel, border_radius=10)
        msg = self.font_big.render(f"Dot Editor: {self.editor_target} (Coming Soon)", True, C_TEXT)
        screen.blit(msg, (panel.centerx - msg.get_width()//2, panel.centery))
        close_rect = pygame.Rect(SCREEN_WIDTH - 100, 20, 80, 40)
        pygame.draw.rect(screen, C_BTN, close_rect)
        txt = self.font.render("Close", True, C_TEXT)
        screen.blit(txt, (close_rect.centerx-txt.get_width()//2, close_rect.centery-txt.get_height()//2))
