import pygame
from settings import *
from colors import *
from world.tiles import get_texture, get_tile_category
from assets.character_parts import *
import math # Math 모듈 명시적 임포트

# [시스템: 렌더러]
# 게임 내 캐릭터와 맵, UI 요소를 화면에 그리는 핵심 시스템입니다.
# 최적화를 위해 캐싱(Caching)을 사용하며, 애니메이션 계산을 포함합니다.

class CharacterRenderer:
    _sprite_cache = {}
    
    pygame.font.init()
    NAME_FONT = pygame.font.SysFont("arial", 11, bold=True)
    POPUP_FONT = pygame.font.SysFont("arial", 12, bold=True)

    # [LEGO Design Constants - Slimmed]
    LEGO_HEAD = pygame.Rect(9, 2, 14, 11)
    LEGO_NECK = pygame.Rect(12, 13, 8, 1)
    LEGO_HIPS = pygame.Rect(11, 23, 10, 3)
    LEGO_LEG_L = pygame.Rect(11, 26, 4, 6)
    LEGO_LEG_R = pygame.Rect(17, 26, 4, 6)
    LEGO_ARM_L = pygame.Rect(7, 15, 3, 7)
    LEGO_ARM_R = pygame.Rect(22, 15, 3, 7)
    LEGO_HAND_L = pygame.Rect(7, 22, 3, 4)
    LEGO_HAND_R = pygame.Rect(22, 22, 3, 4)
    
    # Body Shapes (More Distinct)
    # Body Shapes (Procedural 9 Types)
    # Replaced hardcoded TORSOs with dynamic generation based on BODY_TYPES

    _name_surface_cache = {}

    @classmethod
    def clear_cache(cls):
        cls._sprite_cache.clear()
        cls._name_surface_cache.clear()

    @classmethod
    def _get_cache_key(cls, entity, is_highlighted):
        # Hash the entire custom dictionary along with role and facing
        custom_hash = hash(str(entity.custom))
        
        # Also depend on role, sub_role, facing
        facing = getattr(entity, 'facing_dir', (0, 1))
        return (custom_hash, entity.role, entity.sub_role, facing, is_highlighted)


    @staticmethod
    def calculate_animation(entity):
        """
        [애니메이션 계산]
        엔티티의 상태(이동, 숨기, 감정표현 등)와 시간(tick)을 기반으로
        신체 부위별 위치 오프셋(offset)과 회전 각도를 계산합니다.
        """
        # 기본 오프셋 초기화
        offs = {'y_body': 0, 'y_leg_l': 0, 'y_leg_r': 0, 'y_arm_l': 0, 'y_arm_r': 0}
        
        # Safe Attribute Access
        t = getattr(entity, 'anim_tick', 0.0)
        is_moving = getattr(entity, 'is_moving', False)
        is_hiding = getattr(entity, 'is_hiding', False)
        move_state = getattr(entity, 'move_state', 'WALK')
        
        # Style
        cust = getattr(entity, 'custom', {})
        if not isinstance(cust, dict): cust = {}
        s_idx = cust.get('move_style', 5) # Default Normal
        
        # Index Safety
        if s_idx < 0 or s_idx >= len(MOVEMENT_STYLES): s_idx = 5
        style_name = MOVEMENT_STYLES[s_idx]
        
        import math
        
        # --- STATE LOGIC ---
        # --- STATE LOGIC ---
        # --- STATE LOGIC ---
        is_crouching = getattr(entity, 'is_crouching', False)
        
        if is_hiding or is_crouching:
            # HIDING/CROUCHING: Skeletal Compression
            offs['crouch_off'] = 4 
            offs['y_legs_shorten'] = 4 
            
            if style_name == 'Heroic': 
                offs['rot_arm_l'] = -20; offs['rot_arm_r'] = 20
            elif style_name == 'Stealthy': 
                offs['crouch_off'] = 6
                offs['y_legs_shorten'] = 6
            elif style_name == 'Cat': 
                offs['crouch_off'] = 5
                offs['y_legs_shorten'] = 5
            elif style_name == 'Floating': 
                offs['y_body'] = 3
            return offs

        # INTERACTION (Arms Up)
        is_interacting = getattr(entity, 'e_key_pressed', False)
        if is_interacting:
             offs['rot_arm_l'] = -150
             offs['rot_arm_r'] = -150
             return offs

        if not is_moving:
            # IDLE
            if style_name == 'Heroic': 
                offs['y_body'] = math.sin(t*2)*1
                offs['y_arm_l'] = math.sin(t*2)*1; offs['y_arm_r'] = math.sin(t*2+1)*1
            elif style_name == 'Stealthy':
                offs['y_body'] = 2 + math.sin(t*1)*1
            elif style_name == 'Limping':
                offs['y_body'] = math.sin(t*4)*1; offs['y_leg_r'] = -1
            elif style_name == 'Cheerful':
                offs['y_body'] = abs(math.sin(t*5))*2
            elif style_name == 'HipHop':
                offs['y_body'] = math.sin(t*3)*1
            elif style_name == 'Floating':
                offs['y_body'] = -2 + math.sin(t*2)*3
            elif style_name == 'Heavy':
                offs['y_body'] = math.sin(t*1)*0.5
            else: 
                offs['y_body'] = math.sin(t*2)*1
            return offs

        # MOVING
        is_run = (move_state == "RUN")
        speed = 15 if is_run else 8
        if style_name == 'Running': speed = 18; is_run = True
        
        pha = math.sin(t * speed)
        
        if style_name == 'Heroic':
            amp = 5 if is_run else 3
            # Legs: Y lift + X scissor
            offs['y_leg_l'] = pha * amp; offs['y_leg_r'] = -pha * amp
            
            sw_amp = 2 if is_run else 1.5
            sw_amp = 2 if is_run else 1.5
            pha_sw = math.cos(t * speed)
            offs['x_leg_l'] = pha_sw * sw_amp; offs['x_leg_r'] = -pha_sw * sw_amp
            
            # Arms: Rotation (Degrees)
            # Forward swing = positive rot? 
            # If pivot is top: positive rot moves bottom left? standard angle is CCW.
            # let's try: pha_sw * 30
            offs['rot_arm_l'] = pha_sw * 30 if is_run else pha_sw * 20
            offs['rot_arm_r'] = -pha_sw * 30 if is_run else -pha_sw * 20
            
            offs['y_body'] = abs(math.cos(t * speed)) * 2
        elif style_name == 'Stealthy':
            offs['crouch_off'] = 2 # Slightly hunched when moving
            offs['y_legs_shorten'] = 1
            
            offs['y_leg_l'] = pha * 2; offs['y_leg_r'] = -pha * 2
            # Arms Rotation
            offs['rot_arm_l'] = -pha * 15; offs['rot_arm_r'] = pha * 15
            # Sneaky short strides
            pha_sw = math.cos(t * speed)
            offs['x_leg_l'] = pha_sw * 1.5; offs['x_leg_r'] = -pha_sw * 1.5
            offs['x_arm_l'] = pha_sw * 1; offs['x_arm_r'] = -pha_sw * 1
        elif style_name == 'Limping':
            p_limp = math.sin(t * 6)
            if p_limp > 0: offs['y_leg_l'] = p_limp * 3; offs['y_leg_r'] = 0; offs['y_body'] = p_limp * 1
            else: offs['y_leg_l'] = 0; offs['y_leg_r'] = p_limp * 1; offs['y_body'] = -1
            # Dragging leg motion ? Keep simple for now
            pha_sw = math.cos(t * 6)
            offs['x_leg_l'] = pha_sw * 1; offs['x_leg_r'] = -pha_sw * 0.5
        elif style_name == 'Cheerful':
            offs['y_body'] = abs(math.sin(t * 10)) * 3
            # Cheerful: Arms raised? Or swinging wide?
            # Wide Rotation
            pha_sw = math.cos(t * speed)
            offs['rot_arm_l'] = pha_sw * 40; offs['rot_arm_r'] = -pha_sw * 40
            
            offs['y_leg_l'] = pha * 3; offs['y_leg_r'] = -pha * 3
            # Wide swing
            pha_sw = math.cos(t * speed)
            offs['x_leg_l'] = pha_sw * 3; offs['x_leg_r'] = -pha_sw * 3
            offs['x_arm_l'] = pha_sw * 3; offs['x_arm_r'] = -pha_sw * 3
        elif style_name == 'HipHop':
            offs['y_leg_l'] = pha * 3; offs['y_leg_r'] = -pha * 3
            # Loose arms
            offs['rot_arm_l'] = math.sin(t * speed * 0.5) * 30; offs['rot_arm_r'] = math.cos(t * speed * 0.5) * 30
            # Loose walk
            pha_sw = math.cos(t * speed)
            offs['x_leg_l'] = pha_sw * 2.5; offs['x_leg_r'] = -pha_sw * 2.5
        elif style_name == 'Normal':
            offs['y_leg_l'] = pha * 3; offs['y_leg_r'] = -pha * 3
            # Normal Rotation
            offs['rot_arm_l'] = -pha * 20; offs['rot_arm_r'] = pha * 20
            offs['y_body'] = abs(math.sin(t * speed * 2)) * 1
            # Standard
            pha_sw = math.cos(t * speed)
            offs['x_leg_l'] = pha_sw * 2; offs['x_leg_r'] = -pha_sw * 2
            offs['x_arm_l'] = pha_sw * 2; offs['x_arm_r'] = -pha_sw * 2
        elif style_name == 'Moonwalk':
            offs['y_leg_l'] = pha * 2; offs['y_leg_r'] = -pha * 2
            # Glide Slide? Minimal X stepping?
            pha_sw = math.cos(t * speed)
            offs['x_leg_l'] = pha_sw * 1; offs['x_leg_r'] = -pha_sw * 1
        elif style_name == 'Cat':
            offs['crouch_off'] = 2; offs['y_legs_shorten'] = 1
            offs['y_leg_l'] = pha * 2; offs['y_leg_r'] = -pha * 2
            # Paws out (Fixed angle?)
            offs['rot_arm_l'] = 20 + pha*5; offs['rot_arm_r'] = 20 - pha*5
            # Small paws
            pha_sw = math.cos(t * speed)
            offs['x_leg_l'] = pha_sw * 1.5; offs['x_leg_r'] = -pha_sw * 1.5
        elif style_name == 'Dog':
            offs['y_body'] = abs(pha) * 2
            offs['y_leg_l'] = pha * 4; offs['y_leg_r'] = -pha * 4
            # Paws up
            offs['rot_arm_l'] = -45; offs['rot_arm_r'] = -45
            # Energetic
            # Energetic
            pha_sw = math.cos(t * speed)
            offs['x_leg_l'] = pha_sw * 2; offs['x_leg_r'] = -pha_sw * 2
        else: 
            offs['y_leg_l'] = pha * 3; offs['y_leg_r'] = -pha * 3
            # Default X Swing
            pha_sw = math.cos(t * speed)
            offs['x_leg_l'] = pha_sw * 2; offs['x_leg_r'] = -pha_sw * 2
            offs['rot_arm_l'] = pha_sw * 20; offs['rot_arm_r'] = -pha_sw * 20
        
        return offs

        return offs

    @staticmethod
    def draw_part_icon(screen, rect, cat, sub, i):
        """
        [아이콘 그리기] 커스터마이징 UI를 위한 파츠별 아이콘을 그립니다.
        assets 데이터를 기반으로 미리보기 이미지를 생성합니다.
        """
        cx, cy = rect.centerx, rect.centery
        
        # 1. 색상 팔레트 (Color Swatches)
        if 'COLOR' in sub or 'COL' in sub or sub == 'SKIN':
             c_val = None
             if sub == 'SKIN': c_val = CUSTOM_COLORS['SKIN'][i] 
             elif 'EYE' in sub: c_val = CUSTOM_COLORS['EYES'][i]
             elif 'BROWS' in sub: c_val = CUSTOM_COLORS['HAIR'][i]
             elif 'HAIR' in sub or 'BEARD' in sub: c_val = CUSTOM_COLORS['HAIR'][i]
             elif 'SHOE' in sub: c_val = CUSTOM_COLORS['SHOES'][i]
             elif 'GLS' in sub: c_val = CUSTOM_COLORS['GLASSES'][i] 
             elif 'HAT' in sub: c_val = CUSTOM_COLORS['HAT'][i]
             elif 'COAT' in sub or 'TOP' in sub or 'BTM' in sub: c_val = (CUSTOM_COLORS['CLOTHES'][i] if i < len(CUSTOM_COLORS['CLOTHES']) else (100,100,100))
                  
             if c_val is None:
                 pygame.draw.line(screen, (100, 50, 50), rect.topleft, rect.bottomright, 2)
             else:
                 pygame.draw.rect(screen, c_val, rect.inflate(-16, -16), border_radius=3)
             return

        # 2. 파츠 아이콘 (Part Icons)
        # 32x32 캔버스에 그린 후 확대/축소하여 표시
        icon_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        icx, icy = 16, 16 

        # --- BODY: 체형 ---
        if cat == 'BODY' and sub == 'TYPE':
            b_stats = BODY_TYPES[i] if i < len(BODY_TYPES) else BODY_TYPES[0]
            # 어깨, 허리, 힙 크기에 따른 사다리꼴(Trapezoid) 표현
            sx = 16 - b_stats.get('shoulder', 14)//2
            ex = 16 + b_stats.get('shoulder', 14)//2
            wex = 16 - b_stats.get('waist', 12)//2
            hx = 16 - b_stats.get('hip', 13)//2
            
            poly = [(sx, 6), (ex, 6), (16 + b_stats.get('waist', 12)//2, 14), (16 + b_stats.get('hip', 13)//2, 24), (hx, 24), (wex, 14)] 
            pygame.draw.polygon(icon_surf, (200, 180, 150), poly)
            
        # --- FACE: 얼굴 특징 (눈, 입, 눈썹, 수염) ---
        elif cat == 'FACE':
            grid = []
            if sub == 'EYES': grid = EYES[i]['grid'] if i < len(EYES) else []
            elif sub == 'MOUTH': grid = MOUTHS[i]['grid'] if i < len(MOUTHS) else []
            elif sub == 'BROWS': grid = BROWS[i]['grid'] if i < len(BROWS) else []
            elif sub == 'BEARD': grid = BEARDS[i]['grid'] if i < len(BEARDS) else []
            
            if grid:
               sz = 2
               # 중앙 정렬
               start_x = icx - (len(grid[0])*sz)//2
               start_y = icy - (len(grid)*sz)//2
               for r_idx, row_dat in enumerate(grid):
                   for c_idx, val in enumerate(row_dat):
                       if val: pygame.draw.rect(icon_surf, (220,220,220), (start_x+c_idx*sz, start_y+r_idx*sz, sz, sz))
                       
        # --- HAIR: 헤어스타일 ---
        elif cat == 'HAIR' and sub == 'STYLE':
             if i < len(HAIR):
                 h_dat = HAIR[i]
                 anchor_x, anchor_y = 9, 8 # Head 기준점
                 found = False
                 # 앞머리/뒷머리 미리보기
                 for part in ['back', 'front', 'draw']:
                     if h_dat.get(part):
                         found = True
                         for cmd in h_dat[part]:
                             if cmd['type'] == 'rect':
                                 r = cmd['rect']
                                 pygame.draw.rect(icon_surf, (150,150,150), (anchor_x+r[0], anchor_y+r[1], r[2], r[3]))
                 if not found:
                     pygame.draw.circle(icon_surf, (100,100,100), (16,16), 8)

        # --- CLOTHES: 의상 ---
        elif cat == 'CLOTHES':
             if i < len(TOPS) and sub == 'TOP':
                 # 상의: 기본 형태 + 소매
                 dat = TOPS[i]
                 poly = [(9, 8), (23, 8), (22, 17), (10, 17)] 
                 col = (100,100,180)
                 pygame.draw.polygon(icon_surf, col, poly)
                 pygame.draw.rect(icon_surf, col, (6, 9, 3, 4)); pygame.draw.rect(icon_surf, col, (23, 9, 3, 4))
                 
                 # 추가 디테일
                 if len(dat.get('draw', [])) > 1:
                     pygame.draw.rect(icon_surf, (150,150,220), (12, 10, 8, 8))
                     
             elif i < len(BOTTOMS) and sub == 'BOTTOM':
                  dat = BOTTOMS[i]
                  # 하의: 다리 + 힙
                  pygame.draw.rect(icon_surf, (100,100,180), (10, 16, 5, 10))
                  pygame.draw.rect(icon_surf, (100,100,180), (17, 16, 5, 10))
                  pygame.draw.rect(icon_surf, (100,100,180), (10, 14, 12, 3))
                  if 'skirt' in dat.get('draw', [{}])[0].get('type', ''): # 스커트 처리
                      pygame.draw.polygon(icon_surf, (100,100,180), [(10,14), (22,14), (24,24), (8,24)])

             elif i < len(SHOES) and sub == 'SHOES':
                  pygame.draw.rect(icon_surf, (150,100,50), (10, 24, 5, 4)); pygame.draw.rect(icon_surf, (150,100,50), (17, 24, 5, 4))
                  
             elif i < len(COATS) and sub == 'COAT':
                  # 코트: 큰 외투 형태
                  poly = [(7, 6), (25, 6), (24, 26), (8, 26)] 
                  pygame.draw.polygon(icon_surf, (120,120,120), poly)
                  pygame.draw.line(icon_surf, (80,80,80), (16, 6), (16, 26), 2)

        # --- ACC: 액세서리 ---
        elif cat == 'ACC' and sub == 'HAT':
             if i < len(HATS):
                 h_dat = HATS[i]
                 for d in h_dat['draw']:
                     if d['type'] == 'rect':
                         r = d['rect']
                         pygame.draw.rect(icon_surf, (180,80,80), (9+r[0], 2+r[1], r[2], r[3]))
                     elif d['type'] == 'poly':
                         pts = [(p[0]+9, p[1]+2) for p in d['points']]
                         pygame.draw.polygon(icon_surf, (180,80,80), pts)
        
        elif cat == 'ACC' and sub == 'GLASSES':
             if i < len(GLASSES):
                 g_dat = GLASSES[i]
                 for d in g_dat['draw']:
                     if d['type']=='rect': pygame.draw.rect(icon_surf, (50,150,200), (9+d['rect'][0], 4+d['rect'][1], d['rect'][2], d['rect'][3]))
                     if d['type']=='circle': pygame.draw.circle(icon_surf, (50,150,200), (9+d['rect'][0], 4+d['rect'][1]), d['rect'][2])
                     if d['type']=='poly': 
                         pts = [(p[0]+9, p[1]+4) for p in d['points']]
                         pygame.draw.polygon(icon_surf, (50,150,200), pts)
        
        # --- MOVE: 이동 스타일 ---
        elif cat == 'MOVE':
            style_name = MOVEMENT_STYLES[i] if i < len(MOVEMENT_STYLES) else str(i+1)
            col = (200, 200, 200)
            if i == 5: col = (255, 200, 100) # Run highlight
            # 텍스트는 호출자(Customizer)가 처리하거나 여기서 처리
            # Renderer에는 폰트가 있으므로 여기서 처리 가능
            txt = CharacterRenderer.NAME_FONT.render(style_name, True, col)
            scaled_txt = pygame.transform.scale(txt, (int(txt.get_width()*1.5), int(txt.get_height()*1.5)))
            icon_surf.blit(scaled_txt, (16 - scaled_txt.get_width()//2, 16 - scaled_txt.get_height()//2))

        # 최종 스케일링 및 화면 출력
        scaled = pygame.transform.scale(icon_surf, (64, 64))
        r_dest = scaled.get_rect(center=rect.center)
        screen.blit(scaled, r_dest)

    @staticmethod
    def draw_entity(screen, entity, camera_x, camera_y, viewer_role="PLAYER", current_phase="DAY", viewer_device_on=False):
        """
        [엔티티 그리기]
        캐릭터(플레이어/NPC)를 화면에 렌더링합니다.
        커스터마이징, 애니메이션, 역할별 시각 효과를 모두 적용합니다.
        """
        if not entity.alive: return
        
        # Calculate Animation Offsets
        offs = CharacterRenderer.calculate_animation(entity)

        draw_x = entity.rect.x - camera_x
        draw_y = entity.rect.y - camera_y
        screen_w, screen_h = screen.get_width(), screen.get_height()
        if not (-50 < draw_x < screen_w + 50 and -50 < draw_y < screen_h + 50): return

        if entity.role == "SPECTATOR": return

        alpha = 255
        is_highlighted = False
        if viewer_role == "MAFIA" and viewer_device_on:
            is_highlighted = True; alpha = 255 

        if entity.is_hiding and not is_highlighted:
            is_visible = False
            if getattr(entity, 'is_player', False) or entity.name == "Player 1": is_visible, alpha = True, 120
            elif viewer_role == "SPECTATOR": is_visible, alpha = True, 120
            if not is_visible: return

        # [ANIMATION FIX] Disable Caching for Dynamic Animation
        # cache_key = CharacterRenderer._get_cache_key(entity, is_highlighted)
        # if cache_key in CharacterRenderer._sprite_cache:
        #     base_surf = CharacterRenderer._sprite_cache[cache_key]
        # else:
        base_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            
        # --- HELPER: Get Color ---
        def get_col(idx, pal_name):
            if isinstance(idx, int):
                pal = CUSTOM_COLORS.get(pal_name, [(200,200,200)])
                return pal[idx % len(pal)]
            return idx if idx else (200,200,200)

        cust = entity.custom
        # 1. Body Type Logic
        b_idx = cust.get('body_type', 0) # Default 0 (Average)
        if b_idx >= len(BODY_TYPES): b_idx = 0
        b_stats = BODY_TYPES[b_idx]
        
        skin_color = get_col(cust.get('skin', 0), 'SKIN')
        
        # Clothes Colors
        clothes = cust.get('clothes', {})
        if not isinstance(clothes, dict): clothes = {}
        top_color = get_col(clothes.get('top_color', 0), 'CLOTHES')
        btm_color = get_col(clothes.get('bottom_color', 0), 'CLOTHES')
        shoe_color = get_col(clothes.get('shoes_color', 0), 'SHOES')
        coat_color = get_col(clothes.get('coat_color', 0), 'CLOTHES') # Re-use Clothes palette for coats? Or Add COAT palette?
        
        # Prepare Sleeve Info Early
        t_idx = clothes.get('top', 0)
        t_sleeve = 'short'
        if t_idx < len(TOPS):
             sleeve_val = TOPS[t_idx].get('sleeve', 'short')
             if sleeve_val: t_sleeve = sleeve_val
        sl_h = 4 if t_sleeve=='short' else (7 if t_sleeve=='long' else 0)
        
        # Role Override (Uniforms)
        if entity.role == "MAFIA" and current_phase == "NIGHT":
            top_color = btm_color = (30, 30, 35)
        elif entity.role == "DOCTOR": top_color = btm_color = (240, 240, 250)
        elif entity.role == "POLICE": top_color = btm_color = (20, 40, 120)

        if is_highlighted: skin_color = (255, 50, 50); top_color = btm_color = (150, 0, 0)
        
        # [ANIMATION] Crouch Offset (Moved up for Hair Back)
        c_off = offs.get('crouch_off', 0)
        
        # --- 0. SHADOW ---
        pygame.draw.ellipse(base_surf, (0, 0, 0, 80), (4, TILE_SIZE - 6, TILE_SIZE - 8, 4))
        
        # --- 0.5 HAIR USER (BACK) ---
        # Draw Hair Back FIRST so it is behind body/head
        h_idx_back = cust.get('hair', {}).get('id', 0)
        h_col_back = get_col(cust.get('hair', {}).get('color', 0), 'HAIR')
        if h_idx_back < len(HAIR):
            hair_dat = HAIR[h_idx_back]
            if hair_dat.get('back'):
                for cmd in hair_dat['back']:
                    if cmd.get('type') == 'rect':
                        col = h_col_back if cmd.get('col') == 'h' else (0,0,0)
                        r = cmd['rect']
                        # Pos relative to Head Top-Left (9,2)
                        # [ANIMATION] Apply Crouch Offset to Hair Back
                        final_rect = (9 + r[0], 2 + r[1] + c_off, r[2], r[3])
                        pygame.draw.rect(base_surf, col, final_rect, border_radius=2)
        
        # [ANIMATION] Crouch Offset
        # c_off = offs.get('crouch_off', 0) # Moved to top
        
        # --- 1. BODY BASE (Skin) ---
        # Head Y: 2, Neck Y: 13
        head_rect = pygame.Rect(CharacterRenderer.LEGO_HEAD.x, CharacterRenderer.LEGO_HEAD.y + c_off, CharacterRenderer.LEGO_HEAD.width, CharacterRenderer.LEGO_HEAD.height)
        neck_rect = pygame.Rect(CharacterRenderer.LEGO_NECK.x, CharacterRenderer.LEGO_NECK.y + c_off, CharacterRenderer.LEGO_NECK.width, CharacterRenderer.LEGO_NECK.height)
        
        pygame.draw.rect(base_surf, skin_color, head_rect, border_radius=2)
        pygame.draw.rect(base_surf, skin_color, neck_rect)
        
        # Generate Torso Polygon based on Body Stats
        # Center X = 16. Y range = 14 to 23 (Height 9)
        # Shoulder=b_stats['shoulder'], Waist=b_stats['waist'], Hip=b_stats['hip']
        # Coordinates: (16-w/2, y)
        sx = 16 - b_stats.get('shoulder', 14)//2
        ex = 16 + b_stats.get('shoulder', 14)//2
        wx = 16 - b_stats.get('waist', 12)//2
        wex = 16 + b_stats.get('waist', 12)//2
        hx = 16 - b_stats.get('hip', 13)//2
        hex = 16 + b_stats.get('hip', 13)//2
        
        # Apply Crouch to Torso Ys (14, 19, 23)
        y1, y2, y3 = 14 + c_off, 19 + c_off, 23 + c_off
        torso_poly = [(sx, y1), (ex, y1), (wex, y2), (hex, y3), (hx, y3), (wx, y2)]
        pygame.draw.polygon(base_surf, skin_color, torso_poly) # Skin under clothes
        
        # Hips (Skin) - Match Hip width
        hip_rect = pygame.Rect(hx, y3, b_stats.get('hip', 13), 3) # 23-26 approx (Height 3)
        pygame.draw.rect(base_surf, skin_color, hip_rect)
        
        # Legs (Skin) - Simple straight legs from hip width
        leg_w = max(4, b_stats.get('hip', 13)//2 - 1)
        lx = hx
        rx = hx + leg_w + 2 # gap
        
        # Animation Offsets (from calculate_animation)
        l_off = offs['y_leg_l']
        r_off = offs['y_leg_r']
        lx_off = offs.get('x_leg_l', 0)
        rx_off = offs.get('x_leg_r', 0)

        al_off = offs['y_arm_l']
        ar_off = offs['y_arm_r']
        alx_off = offs.get('x_arm_l', 0)
        arx_off = offs.get('x_arm_r', 0)
        
        # Legs: Start Y increases with crouch, Height decreases
        leg_y_start = 26 + c_off + offs.get('y_legs_shorten', 0) # Base Crouch + Specific Shortening
        # Actually calculate_animation sets `y_legs_shorten` which might duplicate c_off logic?
        # Let's trust logic: c_off moves entire body down. Legs connect Hip (y3+3 = 26+c_off) to Ground (32).
        # So Leg Height = 32 - (26 + c_off).
        leg_h = max(1, 6 - c_off)
        
        leg_l_rect = pygame.Rect(lx + lx_off, 26 + c_off + l_off, leg_w, leg_h)
        leg_r_rect = pygame.Rect(rx + rx_off, 26 + c_off + r_off, leg_w, leg_h)
        
        pygame.draw.rect(base_surf, skin_color, leg_l_rect, border_bottom_left_radius=2)
        pygame.draw.rect(base_surf, skin_color, leg_r_rect, border_bottom_right_radius=2)
        
        # [ANIMATION] Rotation Logic for Arms (Replaces Old Arm Drawing)
        # Using Pivot-Center Surface technique
        def draw_rot_arm(p_x, p_y, angle, is_flip):
            # Surface large enough. Pivot is Center (16,16)
            s = pygame.Surface((32, 32), pygame.SRCALPHA)
            
            # Draw Arm relative to Center Pivot
            # Arm is 4x9. We want Top-Center of Arm to be at Pivot (16,16).
            # So Arm Left-Top should be at (16-2, 16).
            dx, dy = 14, 16 
            
            # Skin
            pygame.draw.rect(s, skin_color, (dx, dy, 4, 9), border_radius=2)
            # Hand
            pygame.draw.rect(s, skin_color, (dx, dy+8, 4, 3), border_radius=1)
            
            # Sleeve
            if sl_h > 0:
                 pygame.draw.rect(s, top_color, (dx, dy, 4, sl_h))
            
            # Rotate
            rot_s = pygame.transform.rotate(s, angle)
            
            # Blit Center to Pivot
            # Target Pivot is (p_x, p_y)
            base_surf.blit(rot_s, rot_s.get_rect(center=(p_x, p_y)))

        # NOTE: Old Arm Drawing Removed. Will call draw_rot_arm later.

        # --- CLOTHING RENDERER (Adaptive) ---
        def draw_adaptive_top(surf, pct_rect, color, body_poly):
            # Map rect (x,y,w,h in %) to irregular body shape
            rx, ry, rw, rh = pct_rect
            
            # Helper: Lerp
            def lerp(a, b, t): return a + (b-a)*t
            
            # Y range 0-100% maps to Y 14-23 (approx, shoulder to hip)
            y1_pct = ry / 100.0
            y2_pct = (ry + rh) / 100.0
            
            # Clamp Y to torso range (14 to 23 = 9px height)
            base_y = 14 + c_off
            abs_y1 = base_y + y1_pct * 9
            abs_y2 = base_y + y2_pct * 9
            
            # Find X bounds at Y1 and Y2
            # Interpolate Left X: sx(0) -> hx(4)
            lx1 = lerp(body_poly[0][0], body_poly[4][0], y1_pct)
            lx2 = lerp(body_poly[0][0], body_poly[4][0], y2_pct)
            
            # Interpolate Right X: ex(1) -> hex(3)
            rx1 = lerp(body_poly[1][0], body_poly[3][0], y1_pct)
            rx2 = lerp(body_poly[1][0], body_poly[3][0], y2_pct)
            
            # Map Width within these bounds
            final_lx1 = lerp(lx1, rx1, rx / 100.0)
            final_rx1 = lerp(lx1, rx1, (rx + rw) / 100.0)
            
            final_lx2 = lerp(lx2, rx2, rx / 100.0)
            final_rx2 = lerp(lx2, rx2, (rx + rw) / 100.0)
            
            poly = [(final_lx1, abs_y1), (final_rx1, abs_y1), (final_rx2, abs_y2), (final_lx2, abs_y2)]
            pygame.draw.polygon(surf, color, poly)

        def draw_mapped_rect(surf, ref_rect, pct_rect, color, radius=0):
             x, y, w, h = pct_rect
             rx, ry, rw, rh = ref_rect
             final_x = rx + (x / 100.0) * rw
             final_y = ry + (y / 100.0) * rh
             final_w = (w / 100.0) * rw
             final_h = (h / 100.0) * rh
             pygame.draw.rect(surf, color, (final_x, final_y, final_w, final_h), border_radius=radius)

        # 1. BOTTOMS
        b_idx = clothes.get('bottom', 0)
        if b_idx < len(BOTTOMS):
            b_dat = BOTTOMS[b_idx]
            if b_dat.get('draw'):
                for cmd in b_dat['draw']:
                     col = btm_color if cmd['col']=='p' else (255,255,255)
                     if cmd['type'] == 'legs':
                         l = cmd['len']
                         hh = 100 if l=='long' else (50 if l=='short' else 20)
                         draw_mapped_rect(base_surf, leg_l_rect, (0,0,100,hh), col, 0)
                         draw_mapped_rect(base_surf, leg_r_rect, (0,0,100,hh), col, 0)
                         pygame.draw.rect(base_surf, col, hip_rect) # Hips match
                     elif cmd['type'] == 'skirt':
                         l = cmd['len']
                         h_px = 6 if l=='short' or l=='mini' else 9
                         # Skirt covers hips and goes down
                         pygame.draw.rect(base_surf, col, hip_rect)
                         # Skirt flare
                         flare = 2
                         pygame.draw.polygon(base_surf, col, [(lx-flare, 26), (rx+leg_w+flare, 26), (rx+leg_w+1+flare, 26+h_px), (lx-1-flare, 26+h_px)])
                     elif cmd['type'] == 'rect':
                         # Relative to Hips for generic rects
                         r = cmd['rect']
                         # Map from normalized hip space? Or pixel match?
                         # Assets use pixel coords approx (-2,10,4,10)
                         # Let's anchor to hip center
                         hcx, hcy = hip_rect.centerx, hip_rect.centery
                         pygame.draw.rect(base_surf, col, (hcx + r[0], hcy + r[1] - 5, r[2], r[3])) # Adjust y offset guess

        # 2. SHOES
        s_idx = clothes.get('shoes', 0)
        if s_idx < len(SHOES):
            s_dat = SHOES[s_idx]
            if s_dat.get('draw'):
                for cmd in s_dat['draw']:
                     if cmd['type'] == 'rect':
                         col = shoe_color if cmd['col']=='p' else btm_color
                         # Left Shoe
                         draw_mapped_rect(base_surf, (leg_l_rect.x, 30, leg_l_rect.width, 2), cmd['rect'], col)
                         # Right Shoe
                         draw_mapped_rect(base_surf, (leg_r_rect.x, 30, leg_r_rect.width, 2), cmd['rect'], col)
        
        # 3. TOPS
        t_idx = clothes.get('top', 0)
        if t_idx < len(TOPS):
            t_dat = TOPS[t_idx]
            if t_dat.get('draw'):
                # Bounding Box for Top (Torso Bounding Box)
                ref = pygame.Rect(sx, 14, ex-sx, 9) 
                for cmd in t_dat['draw']:
                     col = top_color if cmd['col']=='p' else (255,255,255)
                     if cmd['type'] == 'rect':
                         draw_adaptive_top(base_surf, cmd['rect'], col, torso_poly)
                         # [ANIMATION] Sleeves moved to draw_rot_arm logic
                     elif cmd['type'] == 'poly':
                         # Poly also needs adaptive mapping? Too complex. Use Center offset.
                         # Map to bounding box of torso approx
                         ref = pygame.Rect(sx, 14, ex-sx, 9)
                         pts = [(ref.x + (p[0]/100)*ref.width, ref.y + (p[1]/100)*ref.height) for p in cmd['points']]
                         pygame.draw.polygon(base_surf, col, pts)

        # [ANIMATION] Draw Arms (Rotated)
        # Calculate Pivots
        # Left Arm Pivot: sx - 2, 14 + c_off
        # wait, ax = sx - 4. Center is sx - 2. Correct.
        # Right Arm Pivot: ex + 2, 14 + c_off
        # arx = ex. Center is ex + 2. Correct.
        
        # Rotation Angles
        rot_l = offs.get('rot_arm_l', 0)
        rot_r = offs.get('rot_arm_r', 0)
        
        # Draw!
        # x_arm_l offsets are actually Rotation angles now? No, we removed x_arm_l.
        # But wait, did we remove x_arm_l in calculate_animation?
        # Yes, we replaced it with rot_arm_l.
        
        # Pivot Y = ay = 14 + c_off.
        pivot_y = 14 + c_off
        
        draw_rot_arm(sx - 2, pivot_y, rot_l, False)
        draw_rot_arm(ex + 2, pivot_y, rot_r, True)

        # 4. COATS (New Layer)
        c_idx = clothes.get('coat', 0)
        if c_idx < len(COATS) and c_idx > 0:
             c_dat = COATS[c_idx]
             if c_dat.get('draw'):
                 for cmd in c_dat['draw']:
                     col = coat_color if cmd.get('col')=='p' else (200,200,200) # s=Secondary
                     if cmd['type'] == 'rect':
                         draw_adaptive_top(base_surf, cmd['rect'], col, torso_poly)
                         # Sleeves for coats? Maybe later.
                         
                         # Fix for long coats (Skirt/Trench) flare?
                         # Adaptive Top extrapolates the Torso Trapezoid.
                         # If Torso is V-shape (wide shoulder, narrow hip), coat gets narrower at bottom?
                         # That might look bad for Trench Coat (which should flare).
                         # But for now it's better than fixed box.
                         
        # --- 2. FACE (32x32 Surface Logic) ---
        face_surf = pygame.Surface((32,32), pygame.SRCALPHA)
        
        # Face Direction Offset
        f_dir = getattr(entity, 'facing_dir', (0, 1))
        
        # Head Center (x=16, y=7 relative to base_surf)
        # User Feedback: Eyes are too low. GLASSES too low.
        # Raised Head Center Y to 5 (was 7)
        # [ANIMATION] Apply Crouch Offset to Face Center
        ox, oy = 16 + f_dir[0]*2, 5 + f_dir[1] + c_off
        
        # Helper to draw grid features
        def draw_grid(grid_def, offset, color):
            if not grid_def: return
            for r, row in enumerate(grid_def):
                for c, val in enumerate(row):
                    if val == 1:
                        face_surf.set_at((offset[0]+c, offset[1]+r), color)
                    elif val == 2: # White/Secondary
                        face_surf.set_at((offset[0]+c, offset[1]+r), (255,255,255))
        
        # Eyes
        e_idx = cust.get('eyes', {}).get('id', 0)
        e_col = get_col(cust.get('eyes', {}).get('color', 0), 'EYES')
        if e_idx < len(EYES):
            draw_grid(EYES[e_idx]['grid'], (ox-5, oy), e_col) # Left
            draw_grid(EYES[e_idx]['grid'], (ox+1, oy), e_col) # Right
        else: 
            face_surf.set_at((ox-2, oy), (0,0,0)); face_surf.set_at((ox+2, oy), (0,0,0))
            
        # Brows
        b_idx = cust.get('eyes', {}).get('brow_id', 0)
        # Brows logic: Color
        b_col_idx = cust.get('eyes', {}).get('brow_color') # Check if new key exists
        if b_col_idx is None: b_col = get_col(cust.get('hair', {}).get('color', 0), 'HAIR') # Fallback to hair
        else: b_col = get_col(b_col_idx, 'HAIR') # Use Hair palette
        
        if b_idx < len(BROWS):
             draw_grid(BROWS[b_idx]['grid'], (ox-5, oy-2), b_col)
             draw_grid(BROWS[b_idx]['grid'], (ox+1, oy-2), b_col)

        # Mouth
        m_idx = cust.get('mouth', {}).get('id', 0)
        if m_idx < len(MOUTHS):
             draw_grid(MOUTHS[m_idx]['grid'], (ox-2, oy+3), (0,0,0))
              
        # Beard
        beard_idx = cust.get('mouth', {}).get('beard', 0)
        beard_col = get_col(cust.get('mouth', {}).get('beard_color', 0), 'HAIR')
        if beard_idx < len(BEARDS):
             draw_grid(BEARDS[beard_idx]['grid'], (ox-2, oy+3), beard_col)

        base_surf.blit(face_surf, (0,0)) 

        # --- 3. HAIR (Front) ---
        h_idx = cust.get('hair', {}).get('id', 0)
        h_col = get_col(cust.get('hair', {}).get('color', 0), 'HAIR')
        if h_idx < len(HAIR):
            dat = HAIR[h_idx]
            
            # Back (Already drawn at step 0.5)
            # Check Front
            if dat.get('front'):
                for cmd in dat['front']:
                    if cmd.get('type') == 'rect':
                        col = h_col if cmd.get('col') == 'h' else (0,0,0)
                        r = cmd['rect']
                        # [ANIMATION] Apply Crouch Offset to Hair Front
                        final_rect = (9 + r[0], 2 + r[1] + c_off, r[2], r[3])
                        pygame.draw.rect(base_surf, col, final_rect, border_radius=2)
            
            # Legacy Support
            if dat.get('draw'):
                for cmd in dat['draw']:
                     if cmd.get('type') == 'rect':
                        col = h_col if cmd.get('col') == 'h' else (0,0,0)
                        r = cmd['rect']
                        # [ANIMATION] Apply Crouch Offset to Hair Front (Fallback)
                        final_rect = (9 + r[0], 2 + r[1] + c_off, r[2], r[3]) 
                        pygame.draw.rect(base_surf, col, final_rect, border_radius=2)

        # --- 4. ACCESSORIES ---
        # Glasses needs to be raised by 2px as well (was +2 originally, now +0 relative to head?)
        # Head starts at y=2. Eyes at oy=5 in face_surf (relative to head=7?).
        # Let's align Glasses with Eyes. Eyes are at y=5 relative to Head Center Offset.
        # Head Top is y=2. Center roughly y=7. 
        # If oy=5 (was 7), we moved up by 2.
        # Glasses offset was +2 (r[1]+2). We should keep +2 or adjust?
        # Original: oy=7. Glasses +2. Distance 5.
        # New: oy=5. Glasses should be 0? 
        # Let's try +0 offset for glasses Y.
        
        # Glasses
        g_idx = cust.get('acc', {}).get('glasses', 0)
        g_col = get_col(cust.get('acc', {}).get('glasses_color', 0), 'GLASSES')
        if g_idx < len(GLASSES) and g_idx > 0:
             dat = GLASSES[g_idx]
             
             # Dynamic Offset matching Face
             g_off_x = f_dir[0]*2
             g_off_y = f_dir[1]
             
             # [ANIMATION] Apply Crouch Offset to Glasses (Logic uses 9+r[0] and r[1] relative to top?)
             # Actually similar to Hair, relative to Y=0 or Y=4?
             # Assuming relative to Top-Left?
             # r[1] + g_off_y is usually very small. Need to add c_off.
             # Also maybe Head Top offset?
             # Existing code: (r[0]+9 + g_off_x, r[1] + g_off_y, ...)
             # If Head is at Y=2 normally. Glasses at Y=4 roughly.
             # So we should just add c_off.
             
             for d in dat['draw']:
                 col = g_col if d.get('col') == 'p' else (0,0,0)
                 if d['type'] == 'rect': 
                     r = d['rect']
                     pygame.draw.rect(base_surf, col, (r[0]+9 + g_off_x, r[1] + g_off_y + c_off, r[2], r[3])) 
                 elif d['type'] == 'circle':
                     r = d['rect']
                     pygame.draw.circle(base_surf, col, (r[0]+9 + g_off_x, r[1] + g_off_y + c_off), r[2])
                 elif d['type'] == 'line': # Eye Patch line?
                     s = d['start']
                     e = d['end']
                     pygame.draw.line(base_surf, col, (s[0]+9+g_off_x, s[1]+g_off_y+c_off), (e[0]+9+g_off_x, e[1]+g_off_y+c_off))
                 elif d['type'] == 'poly': # Aviator
                     pts = [(p[0]+9+g_off_x, p[1]+g_off_y+c_off) for p in d['points']]
                     pygame.draw.polygon(base_surf, col, pts)
        
        # Hat (Always on top)
        hat_idx = cust.get('hat', 0)
        hat_col = get_col(cust.get('hat_color', hat_idx), 'HAT') 
        if hat_idx < len(HATS) and hat_idx > 0:
            dat = HATS[hat_idx]
            for d in dat['draw']:
                col = hat_col if d.get('color') == 'primary' else (200,50,50)
                if d['type'] == 'rect':
                    r = d['rect']
                    # [ANIMATION] Apply Crouch Offset to Hat
                    # Relative to Head Top (Y=2)
                    pygame.draw.rect(base_surf, col, (r[0]+9, r[1]+2 + c_off, r[2], r[3]), border_radius=2)
                elif d['type'] == 'poly':
                    pts = [(p[0]+9, p[1]+2 + c_off) for p in d['points']]
                    pygame.draw.polygon(base_surf, col, pts)

        # CharacterRenderer._sprite_cache[cache_key] = base_surf
            
        final_surf = base_surf
        if alpha < 255: final_surf = base_surf.copy(); final_surf.set_alpha(alpha)
        
        # Apply Global Animation Offset (Bob/Crouch)
        final_y = draw_y + offs.get('y_body', 0)
        screen.blit(final_surf, (draw_x, final_y))
        
        name_color = (230, 230, 230)
        if entity.role == "POLICE" and viewer_role in ["POLICE", "SPECTATOR"]: name_color = (100, 180, 255)
        elif entity.role == "MAFIA" and viewer_role in ["MAFIA", "SPECTATOR"]: name_color = (255, 100, 100)
        
        text_cache_key = (id(entity), entity.name, name_color)
        if text_cache_key in CharacterRenderer._name_surface_cache: name_surf = CharacterRenderer._name_surface_cache[text_cache_key]
        else: name_surf = CharacterRenderer.NAME_FONT.render(entity.name, True, name_color); CharacterRenderer._name_surface_cache[text_cache_key] = name_surf
        screen.blit(name_surf, (draw_x + (TILE_SIZE // 2) - (name_surf.get_width() // 2), final_y - 14))

class MapRenderer:
    CHUNK_SIZE = 16 # Tiles per chunk (16x32 = 512px)

    def __init__(self, map_manager):
        self.map_manager = map_manager
        self._floor_cache = {} # {(cx, cy): Surface}
        self._wall_cache = {}  # {(cx, cy): Surface}
        self.map_width_tiles = map_manager.width
        self.map_height_tiles = map_manager.height

    def invalidate_cache(self):
        self._floor_cache.clear()
        self._wall_cache.clear()

    def _render_floor_chunk(self, cx, cy):
        surf = pygame.Surface((self.CHUNK_SIZE * TILE_SIZE, self.CHUNK_SIZE * TILE_SIZE), pygame.SRCALPHA)
        start_col = cx * self.CHUNK_SIZE
        start_row = cy * self.CHUNK_SIZE
        end_col = min(start_col + self.CHUNK_SIZE, self.map_width_tiles)
        end_row = min(start_row + self.CHUNK_SIZE, self.map_height_tiles)
        floors = self.map_manager.map_data['floor']
        
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                draw_x = (c - start_col) * TILE_SIZE
                draw_y = (r - start_row) * TILE_SIZE
                tile_data = floors[r][c]
                tid = tile_data[0] if isinstance(tile_data, (tuple, list)) else tile_data
                rot = tile_data[1] if isinstance(tile_data, (tuple, list)) else 0
                if tid != 0:
                    img = get_texture(tid, rot)
                    surf.blit(img, (draw_x, draw_y))
        return surf

    def _render_wall_chunk(self, cx, cy):
        surf = pygame.Surface((self.CHUNK_SIZE * TILE_SIZE, self.CHUNK_SIZE * TILE_SIZE), pygame.SRCALPHA)
        start_col = cx * self.CHUNK_SIZE
        start_row = cy * self.CHUNK_SIZE
        end_col = min(start_col + self.CHUNK_SIZE, self.map_width_tiles)
        end_row = min(start_row + self.CHUNK_SIZE, self.map_height_tiles)
        walls = self.map_manager.map_data['wall']
        
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                draw_x = (c - start_col) * TILE_SIZE
                draw_y = (r - start_row) * TILE_SIZE
                tile_data = walls[r][c]
                tid = tile_data[0] if isinstance(tile_data, (tuple, list)) else tile_data
                rot = tile_data[1] if isinstance(tile_data, (tuple, list)) else 0
                if tid != 0:
                    img = get_texture(tid, rot)
                    surf.blit(img, (draw_x, draw_y))
        return surf

    def draw(self, screen, camera, dt, visible_tiles=None, tile_alphas=None):
        if tile_alphas is None: tile_alphas = {}
        
        # 1. Calculate Visible Chunks
        start_chunk_x = int(max(0, camera.x // (self.CHUNK_SIZE * TILE_SIZE)))
        start_chunk_y = int(max(0, camera.y // (self.CHUNK_SIZE * TILE_SIZE)))
        end_chunk_x = int(min((self.map_width_tiles // self.CHUNK_SIZE) + 1, (camera.x + camera.width / camera.zoom_level) // (self.CHUNK_SIZE * TILE_SIZE) + 1))
        end_chunk_y = int(min((self.map_height_tiles // self.CHUNK_SIZE) + 1, (camera.y + camera.height / camera.zoom_level) // (self.CHUNK_SIZE * TILE_SIZE) + 1))

        # 2. Draw Floors (Background)
        for cy in range(start_chunk_y, end_chunk_y + 1):
            for cx in range(start_chunk_x, end_chunk_x + 1):
                chunk_key = (cx, cy)
                if chunk_key not in self._floor_cache:
                    self._floor_cache[chunk_key] = self._render_floor_chunk(cx, cy)
                
                chunk_surf = self._floor_cache[chunk_key]
                dest_x = (cx * self.CHUNK_SIZE * TILE_SIZE) - camera.x
                dest_y = (cy * self.CHUNK_SIZE * TILE_SIZE) - camera.y
                screen.blit(chunk_surf, (dest_x, dest_y))

        # Calculate Tile Range for Dynamic Rendering
        vw, vh = camera.width / camera.zoom_level, camera.height / camera.zoom_level
        start_col = int(max(0, camera.x // TILE_SIZE))
        start_row = int(max(0, camera.y // TILE_SIZE))
        end_col = int(min(self.map_manager.width, (camera.x + vw) // TILE_SIZE + 2))
        end_row = int(min(self.map_manager.height, (camera.y + vh) // TILE_SIZE + 2))
        zones = self.map_manager.zone_map

        # 5. Draw Objects (Non-Door objects first)
        objects = self.map_manager.map_data['object']
        door_list = [] # To render doors after masking
        
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                tile_data = objects[r][c]
                tid = tile_data[0] if isinstance(tile_data, (tuple, list)) else tile_data
                rot = tile_data[1] if isinstance(tile_data, (tuple, list)) else 0
                if tid != 0:
                    if get_tile_category(tid) == 5:
                        # Store door info to draw later
                        door_list.append((c, r, tid, rot))
                    else:
                        # Draw regular object before mask
                        draw_x = c * TILE_SIZE - camera.x
                        draw_y = r * TILE_SIZE - camera.y
                        img = get_texture(tid, rot)
                        screen.blit(img, (draw_x, draw_y))

        # 6. Apply Indoor Masking (Over floors and regular objects)
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                if zones[r][c] in INDOOR_ZONES:
                    draw_alpha = 255
                    if visible_tiles is not None:
                        draw_alpha = tile_alphas.get((c, r), 0)
                    
                    if draw_alpha < 255:
                        draw_x = c * TILE_SIZE - camera.x
                        draw_y = r * TILE_SIZE - camera.y
                        black_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        black_surf.fill((0, 0, 0, 255 - draw_alpha))
                        screen.blit(black_surf, (draw_x, draw_y))
                        
        # 7. Draw Walls (Cached) - Always Top of mask
        for cy in range(start_chunk_y, end_chunk_y + 1):
            for cx in range(start_chunk_x, end_chunk_x + 1):
                chunk_key = (cx, cy)
                if chunk_key not in self._wall_cache:
                    self._wall_cache[chunk_key] = self._render_wall_chunk(cx, cy)
                
                chunk_surf = self._wall_cache[chunk_key]
                dest_x = (cx * self.CHUNK_SIZE * TILE_SIZE) - camera.x
                dest_y = (cy * self.CHUNK_SIZE * TILE_SIZE) - camera.y
                screen.blit(chunk_surf, (dest_x, dest_y))

        # 8. Draw Doors (After mask and walls) - Always Visible
        for dc, dr, dtid, drot in door_list:
            draw_x = dc * TILE_SIZE - camera.x
            draw_y = dr * TILE_SIZE - camera.y
            img = get_texture(dtid, drot)
            screen.blit(img, (draw_x, draw_y))
