import pygame
from settings import *
from colors import *
from world.tiles import get_texture, get_tile_category

class CharacterRenderer:
    _sprite_cache = {}
    
    pygame.font.init()
    NAME_FONT = pygame.font.SysFont("arial", 11, bold=True)
    POPUP_FONT = pygame.font.SysFont("arial", 12, bold=True)

    # [Balanced Skeleton] Proportions for Cute Character
    # Head is round and friendly
    RECT_HEAD = pygame.Rect(6, 2, 20, 18)
    RECT_BODY = pygame.Rect(10, 18, 12, 10)
    RECT_ARMS = pygame.Rect(7, 18, 18, 6) # Combined arm span for base
    RECT_LEGS = pygame.Rect(10, 26, 12, 6)

    _name_surface_cache = {}

    @classmethod
    def clear_cache(cls):
        cls._sprite_cache.clear()
        cls._name_surface_cache.clear()

    @classmethod
    def _get_cache_key(cls, entity, is_highlighted):
        # Flatten the modular custom dict for cache key
        c = entity.custom
        # Defensive check: Ensure each part is a dictionary (compatibility with legacy data)
        f = c.get('face', {}) if isinstance(c.get('face'), dict) else {}
        h = c.get('hair', {}) if isinstance(c.get('hair'), dict) else {}
        cl = c.get('clothes', {}) if isinstance(c.get('clothes'), dict) else {}
        s = c.get('shoes', {}) if isinstance(c.get('shoes'), dict) else {}
        g = c.get('glasses', {}) if isinstance(c.get('glasses'), dict) else {}
        
        facing = getattr(entity, 'facing_dir', (0, 1))
        is_crouching = getattr(entity, 'move_state', 'WALK') == 'CROUCH' or getattr(entity, 'is_hiding', False)
        
        # [Animation] Discretize frames for caching
        walk_frame = 0
        if getattr(entity, 'is_moving', False) and not is_crouching: # No walk anim while crouching for simplicity, or we can keep it
            # 4-stage walk cycle (150ms per frame)
            walk_frame = (pygame.time.get_ticks() // 150) % 4
        
        action_frame = 0
        action_start = getattr(entity, 'action_anim_start_time', 0)
        if action_start > 0:
            elapsed = pygame.time.get_ticks() - action_start
            if elapsed < 400: # 400ms total action duration
                action_frame = (elapsed // 100) + 1 # Frames 1 to 4
        
        # Convert pixel dicts to frozen sets for caching
        px_key = (
            frozenset(f.get('pixels', {}).items()),
            frozenset(h.get('pixels', {}).items()),
            frozenset(cl.get('pixels', {}).items()),
            frozenset(s.get('pixels', {}).items()),
            frozenset(g.get('pixels', {}).items())
        )

        return (
            c.get('gender'),
            f.get('skin'), f.get('eye_type'), f.get('mouth_type'),
            h.get('type'), h.get('color'),
            cl.get('type'), cl.get('color'),
            s.get('type'), s.get('color'),
            g.get('type'), g.get('color'),
            px_key,
            entity.role, entity.sub_role, facing, is_highlighted,
            walk_frame, action_frame, is_crouching
        )

    @staticmethod
    def draw_entity(screen, entity, camera_x, camera_y, viewer_role="PLAYER", current_phase="DAY", viewer_device_on=False):
        if not entity.alive: return
        draw_x = entity.rect.x - camera_x
        draw_y = entity.rect.y - camera_y
        screen_w, screen_h = screen.get_width(), screen.get_height()
        if not (-50 < draw_x < screen_w + 50 and -50 < draw_y < screen_h + 50): return

        # [Refactor] Spectator Rendering moved here
        if entity.role == "SPECTATOR":
            return

        alpha = 255
        is_highlighted = False
        if viewer_role == "MAFIA" and viewer_device_on:
            is_highlighted = True; alpha = 255 

        if entity.is_hiding and not is_highlighted:
            is_visible = False
            if getattr(entity, 'is_player', False) or entity.name == "Player 1": is_visible, alpha = True, 120
            elif viewer_role == "SPECTATOR": is_visible, alpha = True, 120
            if not is_visible: return

        cache_key = CharacterRenderer._get_cache_key(entity, is_highlighted)
        if cache_key in CharacterRenderer._sprite_cache:
            base_surf = CharacterRenderer._sprite_cache[cache_key]
        else:
            base_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            
            # 1. Colors & Data Setup
            c_data = entity.custom
            gender = c_data.get('gender', 'MALE')
            f_data = c_data.get('face', {}) if isinstance(c_data.get('face'), dict) else {}
            h_data = c_data.get('hair', {}) if isinstance(c_data.get('hair'), dict) else {}
            cl_data = c_data.get('clothes', {}) if isinstance(c_data.get('clothes'), dict) else {}
            s_data = c_data.get('shoes', {}) if isinstance(c_data.get('shoes'), dict) else {}
            g_data = c_data.get('glasses', {}) if isinstance(c_data.get('glasses'), dict) else {}

            body_color = CUSTOM_COLORS['SKIN'][f_data.get('skin', 0) % len(CUSTOM_COLORS['SKIN'])]
            clothes_color = CUSTOM_COLORS['CLOTHES'][cl_data.get('color', 0) % len(CUSTOM_COLORS['CLOTHES'])]
            hair_color = CUSTOM_COLORS['HAIR'][h_data.get('color', 0) % len(CUSTOM_COLORS['HAIR'])]
            
            if is_highlighted: body_color = (255, 50, 50); clothes_color = (150, 0, 0)
            
            # 2. Shadow (Drawn first)
            pygame.draw.ellipse(base_surf, (0, 0, 0, 80), (4, TILE_SIZE - 4, TILE_SIZE - 8, 4))
            
            # [Animation Offsets]
            is_crouching = getattr(entity, 'move_state', 'WALK') == 'CROUCH' or getattr(entity, 'is_hiding', False)
            c_y = 4 if is_crouching else 0 # Crouch downward offset
            
            walk_frame = 0
            if getattr(entity, 'is_moving', False):
                walk_frame = (pygame.time.get_ticks() // 150) % 4
            
            action_frame = 0
            action_start = getattr(entity, 'action_anim_start_time', 0)
            if action_start > 0:
                elapsed = pygame.time.get_ticks() - action_start
                if elapsed < 400:
                    action_frame = (elapsed // 100) + 1

            y_off_l, y_off_r = 0, 0
            if walk_frame == 1: y_off_l, y_off_r = -2, 1
            elif walk_frame == 3: y_off_l, y_off_r = 1, -2
            
            arm_r_y_off = 0
            if action_frame > 0:
                if action_frame <= 2: arm_r_y_off = -5
                else: arm_r_y_off = -3

            # 3. Feet & Shoes
            shoe_type = s_data.get('type', 0)
            shoe_color = CUSTOM_COLORS['SHOES'][s_data.get('color', 0) % len(CUSTOM_COLORS['SHOES'])]
            if shoe_type > 0:
                pygame.draw.rect(base_surf, shoe_color, (10, 28 + y_off_l, 5, 3), border_radius=1)
                pygame.draw.rect(base_surf, shoe_color, (17, 28 + y_off_r, 5, 3), border_radius=1)

            # 4. Legs
            pygame.draw.rect(base_surf, clothes_color, (10, 26 + y_off_l, 5, 5), border_radius=1)
            pygame.draw.rect(base_surf, clothes_color, (17, 26 + y_off_r, 5, 5), border_radius=1)
            
            # 5. Arms (Connected to shoulders)
            arm_y = 19 + c_y
            ax_l, ax_r = 7, 22
            if gender == 'FEMALE':
                ax_l, ax_r = 8, 21 # Narrower shoulders for female
            
            # Arms move opposite to legs
            pygame.draw.rect(base_surf, body_color, (ax_l, arm_y + y_off_r, 3, 7 - (2 if is_crouching else 0)), border_radius=1)
            pygame.draw.rect(base_surf, body_color, (ax_r, arm_y + y_off_l + arm_r_y_off, 3, 7 - (2 if is_crouching else 0)), border_radius=1)

            # 6. Torso & Clothes (Gender Based Body Shapes)
            torso_y = 18 + c_y
            torso_h = 10 - (2 if is_crouching else 0)
            torso_color = clothes_color
            if entity.role == "MAFIA" and current_phase == "NIGHT":
                torso_color = (40, 40, 45)
            elif entity.role == "DOCTOR":
                torso_color = (255, 255, 255)
            elif entity.role == "POLICE":
                torso_color = (40, 60, 150)
            
            cl_type = cl_data.get('type', 0)
            
            if gender == 'FEMALE':
                # Female body
                if cl_type == 1: # Dress
                    pygame.draw.rect(base_surf, torso_color, (10, torso_y, 12, torso_h + 1), border_radius=5)
                    pygame.draw.polygon(base_surf, torso_color, [(8, 28), (24, 28), (20, 23 + c_y), (12, 23 + c_y)])
                elif cl_type == 3: # Hoodie
                    pygame.draw.rect(base_surf, torso_color, (9, torso_y, 14, torso_h + 1), border_radius=6)
                elif cl_type == 4: # Shirt
                    pygame.draw.rect(base_surf, torso_color, (10, torso_y, 12, torso_h), border_radius=4)
                    pygame.draw.circle(base_surf, (200, 50, 50), (16, torso_y + 3), 2)
                else:
                    pygame.draw.rect(base_surf, torso_color, (10, torso_y, 12, torso_h), border_radius=5)
            else:
                # Male body
                if cl_type == 1: # Overall
                    pygame.draw.rect(base_surf, torso_color, (9, torso_y, 14, torso_h), border_radius=3)
                    pygame.draw.rect(base_surf, torso_color, (9, 24 + c_y, 14, 4 - (2 if is_crouching else 0)))
                elif cl_type == 2: # Suit
                    pygame.draw.rect(base_surf, torso_color, (8, torso_y, 16, torso_h + 1), border_top_left_radius=4, border_top_right_radius=4)
                    pygame.draw.polygon(base_surf, (255, 255, 255), [(13, torso_y), (16, torso_y + 7), (19, torso_y)])
                elif cl_type == 3: # Hoodie
                    pygame.draw.rect(base_surf, torso_color, (8, torso_y, 16, torso_h + 1), border_radius=6)
                elif cl_type == 4: # Uniform
                    pygame.draw.rect(base_surf, torso_color, (9, torso_y, 14, torso_h), border_radius=3)
                    pygame.draw.rect(base_surf, (255, 215, 0), (11, torso_y + 2, 3, 3))
                else: # Basic
                    pygame.draw.rect(base_surf, torso_color, (9, torso_y, 14, torso_h), border_radius=3)
            
            # Role Details (Adjusted for crouch)
            if entity.role == "MAFIA" and current_phase == "NIGHT":
                 pygame.draw.line(base_surf, (150, 0, 0), (14, torso_y + 2), (18, torso_y + 2), 2)
            elif entity.role == "POLICE":
                 pygame.draw.rect(base_surf, (255, 215, 0), (15, torso_y + 2, 3, 3))
 
            # 7. Head (Squashed Down)
            head_rect = pygame.Rect(CharacterRenderer.RECT_HEAD.x, CharacterRenderer.RECT_HEAD.y + c_y, 
                                CharacterRenderer.RECT_HEAD.width, CharacterRenderer.RECT_HEAD.height)
            pygame.draw.rect(base_surf, body_color, head_rect, border_radius=9)

            # 8. Facial Features
            f_dir = getattr(entity, 'facing_dir', (0, 1))
            ox, oy = f_dir[0] * 2, f_dir[1] * 1 + c_y
            
            # 1. Eyes
            eye_y = 10 + oy
            eye_t = f_data.get('eye_type', 0)
            
            if eye_t == 1: # Big Sparkly
                pygame.draw.circle(base_surf, (255, 255, 255), (10.5 + ox, eye_y), 3.5)
                pygame.draw.circle(base_surf, (20, 20, 40), (10.5 + ox + f_dir[0]*0.5, eye_y + f_dir[1]*0.5), 1.8)
                pygame.draw.circle(base_surf, (255, 255, 255), (10 + ox, eye_y - 1), 1)
                pygame.draw.circle(base_surf, (255, 255, 255), (21.5 + ox, eye_y), 3.5)
                pygame.draw.circle(base_surf, (20, 20, 40), (21.5 + ox + f_dir[0]*0.5, eye_y + f_dir[1]*0.5), 1.8)
                pygame.draw.circle(base_surf, (255, 255, 255), (21 + ox, eye_y - 1), 1)
            elif eye_t == 2: # Wink
                pygame.draw.line(base_surf, (40, 40, 50), (9+ox, eye_y), (12+ox, eye_y), 2)
                pygame.draw.circle(base_surf, (255, 255, 255), (21.5+ox, eye_y), 3)
                pygame.draw.circle(base_surf, (20, 20, 40), (21.5+ox, eye_y), 1.5)
            elif eye_t == 3: # Angry (> <)
                pygame.draw.line(base_surf, (40, 40, 50), (9+ox, eye_y-1), (12+ox, eye_y+1), 2)
                pygame.draw.line(base_surf, (40, 40, 50), (12+ox, eye_y-1), (9+ox, eye_y+1), 2)
                pygame.draw.line(base_surf, (40, 40, 50), (20+ox, eye_y-1), (23+ox, eye_y+1), 2)
                pygame.draw.line(base_surf, (40, 40, 50), (23+ox, eye_y-1), (20+ox, eye_y+1), 2)
            elif eye_t == 4: # Sleeping (- -)
                pygame.draw.line(base_surf, (40, 40, 50), (9+ox, eye_y), (12+ox, eye_y), 2)
                pygame.draw.line(base_surf, (40, 40, 50), (20+ox, eye_y), (23+ox, eye_y), 2)
            else: # Normal
                pygame.draw.circle(base_surf, (255, 255, 255), (10.5 + ox, eye_y), 3)
                pygame.draw.circle(base_surf, (20, 20, 40), (10.5 + ox+f_dir[0]*0.5, eye_y+f_dir[1]*0.5), 1.5)
                pygame.draw.circle(base_surf, (255, 255, 255), (21.5 + ox, eye_y), 3)
                pygame.draw.circle(base_surf, (20, 20, 40), (21.5 + ox+f_dir[0]*0.5, eye_y+f_dir[1]*0.5), 1.5)

            # Glasses
            g_type = g_data.get('type', 0)
            if g_type > 0:
                g_col = CUSTOM_COLORS['GLASSES'][g_data.get('color', 0) % len(CUSTOM_COLORS['GLASSES'])]
                if g_type == 1: # Square
                    pygame.draw.rect(base_surf, g_col, (8 + ox, eye_y - 2, 6, 5), 1)
                    pygame.draw.rect(base_surf, g_col, (18 + ox, eye_y - 2, 6, 5), 1)
                    pygame.draw.line(base_surf, g_col, (14 + ox, eye_y), (18 + ox, eye_y), 1)
                elif g_type == 2: # Round
                    pygame.draw.circle(base_surf, g_col, (10.5 + ox, eye_y), 4, 1)
                    pygame.draw.circle(base_surf, g_col, (21.5 + ox, eye_y), 4, 1)
                    pygame.draw.line(base_surf, g_col, (14 + ox, eye_y), (18 + ox, eye_y), 1)
                elif g_type == 3: # Sunglasses
                    pygame.draw.rect(base_surf, (20, 20, 30), (8 + ox, eye_y - 2, 7, 5), border_radius=1)
                    pygame.draw.rect(base_surf, (20, 20, 30), (17 + ox, eye_y - 2, 7, 5), border_radius=1)
                    pygame.draw.line(base_surf, (20, 20, 30), (15 + ox, eye_y), (17 + ox, eye_y), 1)
                elif g_type == 4: # Monocle
                    pygame.draw.circle(base_surf, g_col, (10.5 + ox, eye_y), 4, 1)
                    pygame.draw.line(base_surf, g_col, (14.5 + ox, eye_y), (18 + ox, eye_y - 5), 1)

            # 2. Blush
            blush_col = (255, 210, 215, 100)
            pygame.draw.circle(base_surf, blush_col, (16 - 6 + ox, 14.5 + oy), 2)
            pygame.draw.circle(base_surf, blush_col, (16 + 6 + ox, 14.5 + oy), 2)

            # 3. Mouth
            m_y = 15.5 + oy
            m_t = f_data.get('mouth_type', 0)
            if not entity.alive:
                pygame.draw.line(base_surf, (60, 40, 40), (14.5+ox, m_y), (17.5+ox, m_y), 1)
                pygame.draw.line(base_surf, (60, 40, 40), (16+ox, m_y-1), (16+ox, m_y+1), 1)
            else:
                if m_t == 1: # Smile
                    pygame.draw.arc(base_surf, (100, 40, 40), (14+ox, m_y-2, 4, 4), 3.14, 0, 2)
                elif m_t == 2: # Cat
                    pygame.draw.arc(base_surf, (60, 40, 40), (14+ox, m_y-1, 2, 3), 3.14, 0, 1)
                    pygame.draw.arc(base_surf, (60, 40, 40), (16+ox, m_y-1, 2, 3), 3.14, 0, 1)
                elif m_t == 3: # Surprised (O)
                    pygame.draw.circle(base_surf, (60, 40, 40), (16+ox, m_y), 2, 1)
                elif m_t == 4: # Pouting (/ \)
                    pygame.draw.line(base_surf, (60, 40, 40), (15+ox, m_y+1), (16+ox, m_y-1), 1)
                    pygame.draw.line(base_surf, (60, 40, 40), (16+ox, m_y-1), (17+ox, m_y+1), 1)
                else: # Neutral
                    pygame.draw.line(base_surf, (60, 40, 40), (15+ox, m_y), (17+ox, m_y), 1)

            # 9. Hair (Redesigned to not cover eyes)
            h_type = h_data.get('type', 0)
            if h_type > 0:
                if h_type == 1: # Short
                    pygame.draw.rect(base_surf, hair_color, (6, 1, 20, 5), border_top_left_radius=9, border_top_right_radius=9)
                elif h_type == 2: # Bob Cut (Sides only, clear forehead)
                    pygame.draw.rect(base_surf, hair_color, (6, 1, 20, 5), border_top_left_radius=9, border_top_right_radius=9)
                    pygame.draw.rect(base_surf, hair_color, (6, 6, 4, 7))
                    pygame.draw.rect(base_surf, hair_color, (22, 6, 4, 7))
                elif h_type == 3: # Spiky
                    pygame.draw.rect(base_surf, hair_color, (7, 0, 18, 5), border_top_left_radius=9, border_top_right_radius=9)
                    for i in range(3):
                        pygame.draw.polygon(base_surf, hair_color, [(9+i*6, 1), (12+i*6, -3), (15+i*6, 1)])
                elif h_type == 4: # Long with side tail
                    pygame.draw.rect(base_surf, hair_color, (6, 1, 20, 5), border_top_left_radius=9, border_top_right_radius=9)
                    pygame.draw.rect(base_surf, hair_color, (22, 6, 4, 11), border_radius=2)

            # 10. User Dot Pixels (Overlays)
            all_parts = [f_data, h_data, cl_data, s_data, g_data]
            for part in all_parts:
                pixels = part.get('pixels', {})
                for k, col_idx in pixels.items():
                    # Handle both (x,y) tuples and "x,y" strings from JSON
                    if isinstance(k, str):
                        try: px, py = map(int, k.split(','))
                        except: continue
                    else:
                        px, py = k
                    
                    if 0 <= px < TILE_SIZE and 0 <= py < TILE_SIZE:
                        p_col = CUSTOM_COLORS['CLOTHES'][col_idx % len(CUSTOM_COLORS['CLOTHES'])]
                        base_surf.set_at((px, py), p_col)

            CharacterRenderer._sprite_cache[cache_key] = base_surf

        final_surf = base_surf
        if alpha < 255: final_surf = base_surf.copy(); final_surf.set_alpha(alpha)
        screen.blit(final_surf, (draw_x, draw_y))

        name_color = (230, 230, 230)
        if entity.role == "POLICE" and viewer_role in ["POLICE", "SPECTATOR"]: name_color = (100, 180, 255)
        elif entity.role == "MAFIA" and viewer_role in ["MAFIA", "SPECTATOR"]: name_color = (255, 100, 100)
        text_cache_key = (id(entity), entity.name, name_color)
        if text_cache_key in CharacterRenderer._name_surface_cache: name_surf = CharacterRenderer._name_surface_cache[text_cache_key]
        else: name_surf = CharacterRenderer.NAME_FONT.render(entity.name, True, name_color); CharacterRenderer._name_surface_cache[text_cache_key] = name_surf
        screen.blit(name_surf, (draw_x + (TILE_SIZE // 2) - (name_surf.get_width() // 2), draw_y - 14))

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
