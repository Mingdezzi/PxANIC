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
        self.input_rect = pygame.Rect(440, 340, 400, 50)
        self.active = True

    def enter(self, params=None):
        self.sound.play_music("TITLE_THEME")
        
        # [Fix] Sync from DataManager
        from managers.data_manager import DataManager
        dm = DataManager.get_instance()
        if dm.profile:
            self.player_name = dm.profile.get('name', self.player_name)
            self.game.shared_data['custom'] = dm.profile.get('custom', {})
            self.game.shared_data['player_name'] = self.player_name

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
        
        # Draw Title
        title_font = self.res.get_font('title')
        title_img = title_font.render("PxANIC!", True, (255, 255, 255))
        screen.blit(title_img, (w//2 - title_img.get_width()//2, 150))
        
        # Draw Instruction
        inst_img = self.font.render("Enter Your Name:", True, (200, 200, 200))
        screen.blit(inst_img, (w//2 - inst_img.get_width()//2, 300))
        
        # Input Box
        pygame.draw.rect(screen, (40, 40, 50), self.input_rect, border_radius=8)
        pygame.draw.rect(screen, (100, 200, 255), self.input_rect, 2, border_radius=8)
        
        name_img = self.font.render(self.player_name + ("|" if (pygame.time.get_ticks()//500)%2 == 0 else ""), True, (255, 255, 255))
        screen.blit(name_img, (self.input_rect.x + 15, self.input_rect.centery - name_img.get_height()//2))
        
        hint_img = self.res.get_font('default').render("Press ENTER to start", True, (100, 100, 120))
        screen.blit(hint_img, (w//2 - hint_img.get_width()//2, 420))
