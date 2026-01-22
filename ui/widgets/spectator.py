import pygame
from settings import *
from colors import *
from systems.renderer import CharacterRenderer

class SpectatorDashboard:
    def __init__(self, game):
        self.game = game
        self.width = 320 # 1280 - 960
        self.height = 720
        self.x = 960
        self.y = 0
        
        # Fonts
        self.font_time = pygame.font.SysFont("arial", 32, bold=True)
        self.font_header = pygame.font.SysFont("arial", 20, bold=True)
        self.font_item = pygame.font.SysFont("arial", 14)
        self.font_small = pygame.font.SysFont("arial", 12)

    def draw(self, screen):
        # [Responsive Layout]
        screen_w, screen_h = screen.get_size()
        self.width = 300 # Fixed Width as requested
        self.height = screen_h
        self.x = screen_w - self.width
        self.y = 0

        # 1. Background Panel
        pygame.draw.rect(screen, (30, 30, 35), (self.x, self.y, self.width, self.height))
        pygame.draw.line(screen, (60, 60, 70), (self.x, 0), (self.x, self.height), 2)
        
        # 2. Clock (Top)
        # self.game is PlayState
        time_sys = self.game.time_system
        if time_sys:
            phase_text = self.font_time.render(f"{time_sys.current_phase}", True, (255, 255, 255))
            screen.blit(phase_text, (self.x + 20, 20))
            
            # self.game is PlayState, self.game.day_count is property
            day_text = self.font_header.render(f"Day {self.game.day_count} - {int(time_sys.state_timer)}s", True, (200, 200, 200))
            screen.blit(day_text, (self.x + 20, 60))

        # 3. Skip Phase Button (Top-Right of Panel)
        self.skip_rect = pygame.Rect(self.x + self.width - 110, 20, 100, 30)
        pygame.draw.rect(screen, (100, 50, 50), self.skip_rect, border_radius=4)
        skip_txt = self.font_small.render("SKIP PHASE", True, (255, 255, 255))
        screen.blit(skip_txt, (self.skip_rect.centerx - skip_txt.get_width()//2, self.skip_rect.centery - skip_txt.get_height()//2))
        
        # [Fix] Update UIManager's skip rect so PlayState can detect clicks
        if hasattr(self.game, 'ui'):
            self.game.ui.skip_btn_rect = self.skip_rect

        # 4. Player List (Middle - Scrollable)
        # Zone: Y=100 to Y=(Height - 320) -> Leaves space for minimap (300px + padding)
        minimap_size = 300
        minimap_y = self.height - minimap_size - 10
        list_height = minimap_y - 100 - 10 # 10px padding
        
        list_rect = pygame.Rect(self.x, 100, self.width, list_height)
        
        # Save current clip
        old_clip = screen.get_clip()
        screen.set_clip(list_rect)
        
        self._draw_player_list(screen, list_rect.top, list_height)
        
        # Restore clip
        screen.set_clip(old_clip)
        
        # Separator Lines
        pygame.draw.line(screen, (60, 60, 70), (self.x, 100), (self.x + self.width, 100), 2)
        pygame.draw.line(screen, (60, 60, 70), (self.x, minimap_y - 10), (self.x + self.width, minimap_y - 10), 2)

        # 5. Minimap is handled by HUD manager (position updated externally)
        # We need to tell HUD where to put regular widgets or just handle logic here?
        # HUD calls minimap.draw().
        # We can update global layout info or just let HUD calculate based on screen size too.
        # Ideally SpectatorDashboard updates a 'layout_state' or similar.
        
        # For now, we update a dynamic property or shared config?
        # Let's update the minimap rect directly if we can access it.
        # self.game.ui.hud.widgets[4] -> Minimap
        # But cleanest way is HUD handles it consistently.

    def _draw_player_list(self, screen, start_y_base, list_height):
        # Access Scroll Y from UIManager
        scroll_y = getattr(self.game.ui, 'spectator_scroll_y', 0)
        
        start_y = start_y_base - scroll_y
        
        # Use World Entities, not Network
        players = []
        if self.game.world and self.game.world.entities_by_id:
             for ent in self.game.world.entities_by_id.values():
                 if ent.role == "SPECTATOR": continue # Skip spectators
                 players.append(ent)
        
        players.sort(key=lambda x: x.name)
        
        # Header
        pygame.draw.rect(screen, (50, 50, 60), (self.x + 10, start_y_base, self.width - 20, 30))
        h_txt = self.font_header.render("PLAYERS", True, (255, 255, 0))
        screen.blit(h_txt, (self.x + 20, start_y_base + 5))
        
        # Content starts after header (approx flow) - actually header shouldn't scroll? 
        # Code above puts header inside list_rect but uses fixed Y (start_y_base). 
        # Wait, if I draw header after clip at fixed Y, it works.
        
        y_offset = float(start_y + 40)
        
        # Draw Entities
        self.game.ui.entity_rects = [] # Update interactable rects for PlayState
        
        for p in players:
            # Skip if not a character (just in case)
            if not hasattr(p, 'role'): continue
            
            # Card Background
            bg_col = (45, 45, 50)
            if not p.alive: bg_col = (60, 30, 30)
            
            # Relative Rect for drawing
            card_rect = pygame.Rect(self.x + 10, y_offset, self.width - 20, 50)
            
            # Only draw if visible
            # list_rect zone: start_y_base to start_y_base + list_height
            if y_offset + 50 > start_y_base and y_offset < start_y_base + list_height:
                pygame.draw.rect(screen, bg_col, card_rect, border_radius=4)
                
                # Name & Role
                name_col = (255, 255, 255)
                if p.role == "MAFIA": name_col = (255, 100, 100)
                elif p.role == "POLICE": name_col = (100, 180, 255)
                elif p.role == "DOCTOR": name_col = (100, 255, 100)
                
                n_txt = self.font_item.render(f"{p.name} ({p.role})", True, name_col)
                screen.blit(n_txt, (self.x + 20, y_offset + 5))
                
                # Stats Bars (HP/AP)
                hp_val = getattr(p, 'hp', 100)
                max_hp = getattr(p, 'max_hp', 100)
                hp_pct = max(0, min(1, hp_val / max_hp)) if max_hp > 0 else 0
                
                pygame.draw.rect(screen, (50, 0, 0), (self.x + 160, y_offset + 8, 50, 6))
                pygame.draw.rect(screen, (255, 50, 50), (self.x + 160, y_offset + 8, 50*hp_pct, 6))
                
                ap_val = getattr(p, 'ap', 100)
                max_ap = getattr(p, 'max_ap', 100)
                ap_pct = max(0, min(1, ap_val / max_ap)) if max_ap > 0 else 0
                
                pygame.draw.rect(screen, (50, 50, 0), (self.x + 220, y_offset + 8, 50, 6))
                pygame.draw.rect(screen, (255, 255, 0), (self.x + 220, y_offset + 8, 50*ap_pct, 6))
                
                # Action / Emotion
                status_txt = getattr(p, 'current_action_text', "Idle")
                if not p.alive: status_txt = "DEAD"
                s_txt = self.font_small.render(status_txt, True, (150, 150, 150))
                screen.blit(s_txt, (self.x + 20, y_offset + 28))
                
                coins = getattr(p, 'coins', 0)
                coin_txt = self.font_small.render(f"{coins} G", True, (255, 215, 0))
                screen.blit(coin_txt, (self.x + 240, y_offset + 28))

            # Store absolute rect for mouse interaction (handled by PlayState/UIManager)
            self.game.ui.entity_rects.append((card_rect, p))

            y_offset += 55
