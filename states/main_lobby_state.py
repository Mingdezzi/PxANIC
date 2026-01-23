import pygame
from engine.core.state import State
from managers.resource_manager import ResourceManager
from engine.audio.sound_manager import SoundManager
from ui.widgets.settings_popup import SettingsPopup

class MainLobbyState(State):
    def __init__(self, game):
        super().__init__(game)
        self.res = ResourceManager.get_instance()
        self.sound = SoundManager.get_instance()
        self.buttons = {}
        self.title_font = self.res.get_font('title')
        self.large_font = self.res.get_font('large')
        self.settings_popup = SettingsPopup(game)
        
        self.panel_bg = pygame.Surface((400, 420), pygame.SRCALPHA)
        pygame.draw.rect(self.panel_bg, (20, 20, 25, 220), (0, 0, 400, 420), border_radius=15)
        pygame.draw.rect(self.panel_bg, (80, 80, 100, 255), (0, 0, 400, 420), 2, border_radius=15)

    def draw(self, screen):
        w, h = screen.get_size()
        screen.fill((10, 10, 15))
        self.buttons = {}
        
        # Grid Background
        for x in range(0, w, 40): pygame.draw.line(screen, (20, 20, 30), (x, 0), (x, h))
        for y in range(0, h, 40): pygame.draw.line(screen, (20, 20, 30), (0, y), (w, y))
        
        # User Info (Top Left)
        user_name = self.game.shared_data.get('player_name', "Unknown")
        name_img = self.res.get_font('bold').render(f"WELCOME, {user_name}", True, (100, 200, 255))
        screen.blit(name_img, (20, 20))

        # Title
        title_img = self.title_font.render("PxANIC!", True, (255, 255, 255))
        screen.blit(title_img, (w//2 - title_img.get_width()//2, 80))

        panel_rect = self.panel_bg.get_rect(center=(w//2, h//2 + 50))
        screen.blit(self.panel_bg, panel_rect)

        # Buttons
        start_y = panel_rect.top + 60
        self._draw_btn(screen, "OFFLINE START", w//2, start_y, 'Single')
        self._draw_btn(screen, "SERVER BROWSER", w//2, start_y + 80, 'Multi')
        self._draw_btn(screen, "CUSTOMIZE", w//2, start_y + 160, 'Custom')
        self._draw_btn(screen, "EXIT GAME", w//2, start_y + 240, 'Exit')

        if self.settings_popup.active: self.settings_popup.draw(screen)

    def _draw_btn(self, screen, text, cx, cy, key):
        bw, bh = 300, 50
        rect = pygame.Rect(cx - bw//2, cy - bh//2, bw, bh)
        mx, my = pygame.mouse.get_pos()
        hover = rect.collidepoint(mx, my) and not self.settings_popup.active
        
        col = (60, 60, 80) if hover else (40, 40, 50)
        border = (100, 255, 100) if hover else (80, 80, 100)
        
        pygame.draw.rect(screen, col, rect, border_radius=8)
        pygame.draw.rect(screen, border, rect, 2, border_radius=8)
        
        txt_img = self.large_font.render(text, True, (255, 255, 255))
        screen.blit(txt_img, txt_img.get_rect(center=rect.center))
        self.buttons[key] = rect

    def handle_event(self, event):
        if self.settings_popup.active:
            self.settings_popup.handle_event(event)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if 'Single' in self.buttons and self.buttons['Single'].collidepoint(mx, my):
                self.sound.play_sfx("CLICK")
                from states.lobby_state import LobbyState
                self.game.shared_data['server_ip'] = None
                self.game.state_machine.change(LobbyState(self.game))
            elif 'Multi' in self.buttons and self.buttons['Multi'].collidepoint(mx, my):
                self.sound.play_sfx("CLICK")
                from states.multi_menu_state import MultiMenuState
                self.game.state_machine.change(MultiMenuState(self.game))
            elif 'Custom' in self.buttons and self.buttons['Custom'].collidepoint(mx, my):
                self.sound.play_sfx("CLICK")
                from states.custom_state import CustomizationState
                self.game.state_machine.change(CustomizationState(self.game))
            elif 'Exit' in self.buttons and self.buttons['Exit'].collidepoint(mx, my):
                self.game.running = False
