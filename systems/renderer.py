import pygame
from settings import *
from colors import *
from world.tiles import get_texture, get_tile_category

class CharacterRenderer:
    _sprite_cache = {}
    
    pygame.font.init()
    NAME_FONT = pygame.font.SysFont("arial", 11, bold=True)
    POPUP_FONT = pygame.font.SysFont("arial", 12, bold=True)

    RECT_BODY = pygame.Rect(4, 4, 24, 24)
    RECT_CLOTH = pygame.Rect(4, 14, 24, 14)
    RECT_ARM_L = pygame.Rect(8, 14, 4, 14)
    RECT_ARM_R = pygame.Rect(20, 14, 4, 14)
    RECT_HAT_TOP = pygame.Rect(2, 2, 28, 5)
    RECT_HAT_RIM = pygame.Rect(6, 0, 20, 7)

    _name_surface_cache = {}

    @classmethod
    def clear_cache(cls):
        cls._sprite_cache.clear()
        cls._name_surface_cache.clear()

    @classmethod
    def _get_cache_key(cls, entity, is_highlighted):
        skin_idx = entity.custom.get('skin', 0)
        cloth_idx = entity.custom.get('clothes', 0)
        hat_idx = entity.custom.get('hat', 0)
        facing = getattr(entity, 'facing_dir', (0, 1))
        return (skin_idx, cloth_idx, hat_idx, entity.role, entity.sub_role, facing, is_highlighted)

    @staticmethod
    def draw_entity(screen, entity, camera_x, camera_y, viewer_role="PLAYER", current_phase="DAY", viewer_device_on=False):
        if not entity.alive: return
        draw_x = entity.rect.x - camera_x
        draw_y = entity.rect.y - camera_y
        screen_w, screen_h = screen.get_width(), screen.get_height()
        if not (-50 < draw_x < screen_w + 50 and -50 < draw_y < screen_h + 50): return

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
            skin_idx = entity.custom.get('skin', 0) % len(CUSTOM_COLORS['SKIN'])
            cloth_idx = entity.custom.get('clothes', 0) % len(CUSTOM_COLORS['CLOTHES'])
            body_color = CUSTOM_COLORS['SKIN'][skin_idx]
            clothes_color = CUSTOM_COLORS['CLOTHES'][cloth_idx]
            if is_highlighted: body_color = (255, 50, 50); clothes_color = (150, 0, 0)
            pygame.draw.ellipse(base_surf, (0, 0, 0, 80), (4, TILE_SIZE - 8, TILE_SIZE - 8, 6))
            pygame.draw.rect(base_surf, body_color, CharacterRenderer.RECT_BODY, border_radius=6)
            if entity.role == "MAFIA":
                if current_phase == "NIGHT":
                    pygame.draw.rect(base_surf, (30, 30, 35), CharacterRenderer.RECT_CLOTH, border_bottom_left_radius=6, border_bottom_right_radius=6)
                    pygame.draw.polygon(base_surf, (180, 0, 0), [(16, 14), (13, 22), (19, 22)])
                else:
                    fake_color = clothes_color
                    if entity.sub_role == "POLICE": fake_color = (20, 40, 120)
                    elif entity.sub_role == "DOCTOR": fake_color = (240, 240, 250)
                    pygame.draw.rect(base_surf, fake_color, CharacterRenderer.RECT_CLOTH, border_bottom_left_radius=6, border_bottom_right_radius=6)
            elif entity.role == "DOCTOR":
                pygame.draw.rect(base_surf, (240, 240, 250), CharacterRenderer.RECT_CLOTH, border_bottom_left_radius=6, border_bottom_right_radius=6)
            elif entity.role == "POLICE":
                pygame.draw.rect(base_surf, (20, 40, 120), CharacterRenderer.RECT_CLOTH, border_bottom_left_radius=6, border_bottom_right_radius=6)
            else:
                pygame.draw.rect(base_surf, clothes_color, CharacterRenderer.RECT_CLOTH, border_bottom_left_radius=6, border_bottom_right_radius=6)

            f_dir = getattr(entity, 'facing_dir', (0, 1))
            ox, oy = f_dir[0] * 3, f_dir[1] * 2
            pygame.draw.circle(base_surf, (255, 255, 255), (16 - 5 + ox, 12 + oy), 3)
            pygame.draw.circle(base_surf, (0, 0, 0), (16 - 5 + ox + f_dir[0], 12 + oy + f_dir[1]), 1)
            pygame.draw.circle(base_surf, (255, 255, 255), (16 + 5 + ox, 12 + oy), 3)
            pygame.draw.circle(base_surf, (0, 0, 0), (16 + 5 + ox + f_dir[0], 12 + oy + f_dir[1]), 1)
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
