import pygame
from colors import COLORS

class ChatBox:
    def __init__(self, x, y, width=300, height=200):
        self.rect = pygame.Rect(x, y, width, height)
        self.messages = [] # List of {"text": str, "color": tuple}
        self.input_text = ""
        self.active = False # Whether the input field is active
        self.font = pygame.font.SysFont("malgungothic", 16) # Supports Korean
        self.input_font = pygame.font.SysFont("malgungothic", 18, bold=True)
        
        # UI Settings
        self.max_messages = 50
        self.bg_color = (0, 0, 0, 100) # Semi-transparent
        self.border_color = (200, 200, 255, 150)
        
        # Scroll offset (not fully implemented but prepared)
        self.scroll_y = 0

    def add_message(self, sender, text, color=(255, 255, 255)):
        full_text = f"[{sender}] {text}"
        self.messages.append({"text": full_text, "color": color})
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def handle_event(self, event, network_manager=None):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if not self.active:
                    self.active = True
                else:
                    if self.input_text.strip():
                        # Send to network if available
                        if network_manager:
                            network_manager.send_chat(self.input_text)
                        else:
                            # Local echo for testing
                            self.add_message("Me", self.input_text)
                        self.input_text = ""
                    self.active = False
                return True # Event consumed
                
            elif self.active:
                if event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.active = False
                else:
                    # Filter non-printable if needed, but unicode is usually fine
                    if len(self.input_text) < 40:
                        self.input_text += event.unicode
                return True # Event consumed
        return False

    def draw(self, screen):
        # 1. Background
        chat_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(chat_surf, self.bg_color, (0, 0, self.rect.width, self.rect.height), border_radius=5)
        
        if self.active:
            pygame.draw.rect(chat_surf, (50, 50, 80, 180), (0, 0, self.rect.width, self.rect.height), border_radius=5)
            pygame.draw.rect(chat_surf, (100, 200, 255), (0, 0, self.rect.width, self.rect.height), 2, border_radius=5)
        else:
            pygame.draw.rect(chat_surf, self.border_color, (0, 0, self.rect.width, self.rect.height), 1, border_radius=5)
        
        screen.blit(chat_surf, self.rect.topleft)

        # 2. Messages (Draw from bottom up)
        line_height = 20
        start_y = self.rect.bottom - (40 if self.active else 10)
        
        for i, msg in enumerate(reversed(self.messages)):
            y = start_y - (i + 1) * line_height
            if y < self.rect.top + 5: break
            
            txt_surf = self.font.render(msg['text'], True, msg['color'])
            screen.blit(txt_surf, (self.rect.x + 10, y))

        # 3. Input Line
        if self.active:
            input_rect = pygame.Rect(self.rect.x + 5, self.rect.bottom - 30, self.rect.width - 10, 25)
            pygame.draw.rect(screen, (20, 20, 30), input_rect, border_radius=3)
            pygame.draw.rect(screen, (0, 255, 0), input_rect, 1, border_radius=3)
            
            prefix = "> "
            txt_surf = self.input_font.render(prefix + self.input_text + "|", True, (255, 255, 255))
            screen.blit(txt_surf, (input_rect.x + 5, input_rect.centery - txt_surf.get_height()//2))
