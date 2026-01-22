import pygame
from ui.widgets.base import UIWidget
from settings import TILE_SIZE
from world.tiles import TILE_DATA

# 기본 색상 (TILE_DATA에 없는 경우 대비)
DEFAULT_COLORS = {'floor': (40, 40, 40), 'wall': (100, 100, 100), 'object': (200, 200, 100)}

class MinimapWidget(UIWidget):
    def __init__(self, game):
        super().__init__(game)
        self.minimap_surface = None
        self.cached_minimap = None
        self.radar_timer = 0
        self.radar_blips = []
        self.rect = pygame.Rect(0, 0, 0, 0) # [Added] To detect clicks

    def _generate_surface(self):
        w, h = self.game.map_manager.width, self.game.map_manager.height
        surf = pygame.Surface((w, h))
        surf.fill((20, 20, 25))
        pixels = pygame.PixelArray(surf)
        
        floors = self.game.map_manager.map_data['floor']
        walls = self.game.map_manager.map_data['wall']
        objects = self.game.map_manager.map_data['object']

        for y in range(h):
            for x in range(w):
                # 우선순위: Object > Wall > Floor
                color = None
                
                # 1. Object
                o_val = objects[y][x]
                o_tid = o_val[0] if isinstance(o_val, (tuple, list)) else o_val
                if o_tid != 0 and o_tid in TILE_DATA:
                    color = TILE_DATA[o_tid].get('color')
                
                # 2. Wall (If no object or object has no color)
                if color is None:
                    w_val = walls[y][x]
                    w_tid = w_val[0] if isinstance(w_val, (tuple, list)) else w_val
                    if w_tid != 0 and w_tid in TILE_DATA:
                        color = TILE_DATA[w_tid].get('color')
                
                # 3. Floor (If no wall/object)
                if color is None:
                    f_val = floors[y][x]
                    f_tid = f_val[0] if isinstance(f_val, (tuple, list)) else f_val
                    if f_tid != 0 and f_tid in TILE_DATA:
                        color = TILE_DATA[f_tid].get('color')
                
                # Apply Color
                if color:
                    pixels[x, y] = color
                else:
                    # Fallback for empty/unknown
                    pass 

        pixels.close()
        return surf

    def draw(self, screen):
        # Normal HUD Minimap (Bottom Right)
        w, h = screen.get_size()
        mm_size = max(220, int(min(w, h) * 0.25)) # 25% of smaller dim
        mm_w, mm_h = mm_size, mm_size
        
        x = w - mm_w - 20
        y = h - mm_h - 20 
        
        # Check if we are in Spectator Mode (Externally set rect in HUD overrides this?)
        # Actually HUD calls draw() on the widget after checking role.
        # But if the HUD simply calls draw(), this default logic puts it in bottom right.
        # HUD modifies self.rect before calling draw? No, it sets rect and then calls draw.
        # Wait, the draw method here recalculates x, y. This overrides HUD's placement!
        
        # [Fix] Use self.rect if it was set externally by HUD for Spectator Mode?
        # Or split into draw_normal and draw_spectator.
        
        # Let's trust self.rect if it matches Spectator Panel Logic
        if self.rect.width == 300 and self.rect.height == 300:
             # This is Spectator Mode call
             self._draw_full_map(screen)
             return

        # Default HUD usage
        mm_rect = pygame.Rect(x, y, mm_w, mm_h)
        self.rect = mm_rect 
        self._draw_minimap_logic(screen, mm_rect)

    def _draw_full_map(self, screen):
        # Spectator Mode: Full Map Scaled to self.rect (300x300)
        # Assuming self.rect is already set by HUD to (970, 420, 300, 300)
        
        # Background
        pygame.draw.rect(screen, (20, 20, 25), self.rect)
        pygame.draw.rect(screen, (100, 100, 120), self.rect, 2)
        
        if not self.minimap_surface:
             self.minimap_surface = self._generate_surface()
        
        # Scale to fit fully
        scaled_map = pygame.transform.scale(self.minimap_surface, (self.rect.width - 4, self.rect.height - 4))
        screen.blit(scaled_map, (self.rect.x + 2, self.rect.y + 2))
        
        # Draw Entities on Full Map
        self._draw_radar(screen, self.rect, self.game.map_manager.width * TILE_SIZE, self.game.map_manager.height * TILE_SIZE, self.rect.width, self.rect.height, full_map=True)

    def _draw_minimap_logic(self, screen, mm_rect):
        s = pygame.Surface((mm_rect.width, mm_rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        screen.blit(s, mm_rect.topleft)
        pygame.draw.rect(screen, (100, 100, 120), mm_rect, 2)
        
        if not self.minimap_surface:
            self.minimap_surface = self._generate_surface()
            self.cached_minimap = pygame.transform.scale(self.minimap_surface, (mm_rect.width - 4, mm_rect.height - 4))
            
        screen.blit(self.cached_minimap, (mm_rect.x + 2, mm_rect.y + 2))
        
        map_w_px = self.game.map_manager.width * TILE_SIZE
        map_h_px = self.game.map_manager.height * TILE_SIZE
        
        # Player Dot (Self)
        if map_w_px > 0:
            dot_x = mm_rect.x + 2 + (self.game.player.rect.centerx / map_w_px) * (mm_rect.width - 4)
            dot_y = mm_rect.y + 2 + (self.game.player.rect.centery / map_h_px) * (mm_rect.height - 4)
            pygame.draw.circle(screen, (0, 255, 0), (int(dot_x), int(dot_y)), 3)

        self._draw_radar(screen, mm_rect, map_w_px, map_h_px, mm_rect.width, mm_rect.height)

    def _draw_radar(self, screen, mm_rect, map_w, map_h, mm_w, mm_h, full_map=False):
        is_blackout = getattr(self.game, 'is_blackout', False)
        player = self.game.player
        
        # [Spectator] Show ALL entities
        if full_map or player.role == "SPECTATOR":
            for n in self.game.npcs + ([player] if player.role != "SPECTATOR" else []):
                if not n.alive or n.role == "SPECTATOR": continue
                
                col = (0, 255, 0) # Citizen
                if n.role == "MAFIA": col = (255, 0, 0)
                elif n.role == "POLICE": col = (0, 100, 255)
                elif n.role == "DOCTOR": col = (100, 255, 100)
                
                nx = mm_rect.x + 2 + (n.rect.centerx / map_w) * (mm_w - 4)
                ny = mm_rect.y + 2 + (n.rect.centery / map_h) * (mm_h - 4)
                pygame.draw.circle(screen, col, (int(nx), int(ny)), 4)
            return

        # 1. Police CCTV Passive
        if player.role == "POLICE":
            cctv_tid = 7310011
            cctv_locs = self.game.map_manager.tile_cache.get(cctv_tid, [])
            
            for cx, cy in cctv_locs:
                # Convert to Minimap Coords
                mx = mm_rect.x + 2 + ((cx + TILE_SIZE//2) / map_w) * (mm_w - 4)
                my = mm_rect.y + 2 + ((cy + TILE_SIZE//2) / map_h) * (mm_h - 4)
                
                # Check motion near CCTV
                motion_detected = False
                # Check NPCs
                for n in self.game.npcs:
                    if n.alive and getattr(n, 'is_moving', False):
                        dist_sq = (n.rect.centerx - (cx+16))**2 + (n.rect.centery - (cy+16))**2
                        if dist_sq < (5 * TILE_SIZE)**2: # 5 tile radius
                            motion_detected = True
                            break
                
                # Draw CCTV Dot
                col = (150, 0, 255) # Purple
                if motion_detected:
                    # Blink if motion detected
                    if (pygame.time.get_ticks() // 200) % 2 == 0:
                        pygame.draw.circle(screen, (255, 100, 255), (int(mx), int(my)), 4)
                        pygame.draw.circle(screen, col, (int(mx), int(my)), 6, 1)
                else:
                    # Static dot
                    pygame.draw.rect(screen, col, (int(mx)-2, int(my)-2, 4, 4))
 
        # 2. Mafia Blackout Radar
        elif player.role == "MAFIA" and is_blackout:
            now = pygame.time.get_ticks()
            if now > self.radar_timer:
                self.radar_timer = now + 2000
                self.radar_blips = []
                for n in self.game.npcs:
                    if not n.alive: continue
                    color = (0, 255, 0)
                    if n.role == "POLICE": color = (0, 100, 255)
                    elif n.role == "MAFIA": color = (255, 0, 0)
                    nx = mm_rect.x + 2 + (n.rect.centerx / map_w) * (mm_w - 4)
                    ny = mm_rect.y + 2 + (n.rect.centery / map_h) * (mm_h - 4)
                    self.radar_blips.append(((int(nx), int(ny)), color))
            for pos, col in self.radar_blips: pygame.draw.circle(screen, col, pos, 4)
        
        # 3. Citizen/Doctor Proximity Sensor (Device ON)
        elif player.device_on and player.role in ["CITIZEN", "DOCTOR"]:
             for n in self.game.npcs:
                if not n.alive: continue
                import math
                if math.sqrt((player.rect.centerx - n.rect.centerx)**2 + (player.rect.centery - n.rect.centery)**2) < 400 and getattr(n, 'is_moving', False):
                     nx = mm_rect.x + 2 + (n.rect.centerx / map_w) * (mm_w - 4)
                     ny = mm_rect.y + 2 + (n.rect.centery / map_h) * (mm_h - 4)
                     pygame.draw.circle(screen, (0, 255, 0), (int(nx), int(ny)), 3)