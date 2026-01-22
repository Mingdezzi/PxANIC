import pygame
from engine.core.state import State
from managers.resource_manager import ResourceManager
from engine.audio.sound_manager import SoundManager

class LoginState(State):
    def __init__(self, game):
        super().__init__(game)
        self.res = ResourceManager.get_instance()
        self.sound = SoundManager.get_instance()
        self.player_name = self.game.shared_data.get('player_name', "Player")
        self.font = self.res.get_font('large')
        self.font = self.res.get_font('large')
        self.active = True
        self.input_rect = pygame.Rect(0, 0, 0, 0) # Placeholder, updated in draw

    def enter(self, params=None):
        self.sound.play_music("TITLE_THEME")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.player_name.strip():
                    self.game.shared_data['player_name'] = self.player_name
                    from states.main_lobby_state import MainLobbyState
                    self.game.state_machine.change(MainLobbyState(self.game))
            elif event.key == pygame.K_BACKSPACE:
                self.player_name = self.player_name[:-1]
            else:
                if len(self.player_name) < 12 and event.unicode.isalnum():
                    self.player_name += event.unicode
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Add a button click for enter? Or just use Keyboard.
                pass

    def draw(self, screen):
        w, h = screen.get_size()
        screen.fill((20, 20, 30))
        
        # Dynamic Scaling
        box_w = min(600, int(w * 0.5))
        box_h = int(h * 0.08) # 8% Height
        self.input_rect = pygame.Rect(w//2 - box_w//2, h//2, box_w, box_h)
        
        # Draw Title
        title_font = self.res.get_font('title')
        title_img = title_font.render("PxANIC!", True, (255, 255, 255))
        # Place title at 20% height
        screen.blit(title_img, (w//2 - title_img.get_width()//2, h * 0.2))
        
        # Draw Instruction
        inst_font = self.res.get_font('large')
        inst_img = inst_font.render("Enter Your Name:", True, (200, 200, 200))
        # Place above input box
        screen.blit(inst_img, (w//2 - inst_img.get_width()//2, self.input_rect.top - inst_img.get_height() - 20))
        
        # Input Box
        pygame.draw.rect(screen, (40, 40, 50), self.input_rect, border_radius=12)
        pygame.draw.rect(screen, (100, 200, 255), self.input_rect, 3, border_radius=12)
        
        inp_font = self.res.get_font('large')
        name_img = inp_font.render(self.player_name + ("|" if (pygame.time.get_ticks()//500)%2 == 0 else ""), True, (255, 255, 255))
        screen.blit(name_img, (self.input_rect.centerx - name_img.get_width()//2, self.input_rect.centery - name_img.get_height()//2))
        
        hint_img = self.res.get_font('default').render("Press ENTER to start", True, (100, 100, 120))
        screen.blit(hint_img, (w//2 - hint_img.get_width()//2, self.input_rect.bottom + 20))
