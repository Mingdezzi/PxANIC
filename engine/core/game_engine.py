import pygame
import sys
import gc
import time
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from engine.core.state_machine import StateMachine
from engine.core.logger import GameLogger

class GameEngine:
    def __init__(self):
        # [Fix] Windows DPI Awareness (Screen Recording Offset Fix)
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1) # PROCESS_SYSTEM_DPI_AWARE
            except Exception as e:
                print(f"[SYSTEM] DPI Awareness set failed: {e}")

        pygame.init()
        # [Optimization] GC enabled for stability
        # gc.disable()
        
        self.logger = GameLogger.get_instance()
        self.logger.info("SYSTEM", "Game Engine Initializing...")

        # [Fix] Virtual Resolution Configuration
        # Lower virtual resolution = Larger UI & Narrower FOV
        from settings import RENDER_SCALE
        self.render_scale = RENDER_SCALE
        
        # [Fix] 80% Screen Size Initialization
        info_obj = pygame.display.Info()
        self.window_width = int(info_obj.current_w * 0.8)
        self.window_height = int(info_obj.current_h * 0.8)
        
        self.screen_width = int(self.window_width / self.render_scale)
        self.screen_height = int(self.window_height / self.render_scale)
        
        # [Global UI Scale]
        # Base resolution reference: 1280x720
        # If window is 1920x1080 -> Scale ~ 1.5
        pass_w = self.window_width / 1280.0
        pass_h = self.window_height / 720.0
        self.ui_scale = min(pass_w, pass_h)
        
        # Apply to Font Manager
        from managers.resource_manager import ResourceManager
        ResourceManager.get_instance().set_font_scale(self.ui_scale)
        
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        self.virtual_screen = pygame.Surface((self.screen_width, self.screen_height))
        
        pygame.display.set_caption("PxANIC!")

        self.clock = pygame.time.Clock()
        self.running = True

        self.state_machine = StateMachine(self)
        self.shared_data = {}

        # Profiling
        self.last_profile_time = time.time()
        self.frame_count = 0

    def run(self, initial_state=None):
        if initial_state:
            self.state_machine.push(initial_state)

        self.logger.info("SYSTEM", "Engine Loop Started")
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            # Profiling
            start_t = time.perf_counter()
            
            self.process_events()
            self.update(dt)
            self.draw()
            
            end_t = time.perf_counter()
            frame_time = (end_t - start_t) * 1000
    
    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.VIDEORESIZE:
                self.window_width, self.window_height = event.w, event.h
                self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
                # Sync virtual resolution
                self.screen_width = int(self.window_width / self.render_scale)
                self.screen_height = int(self.window_height / self.render_scale)
                self.virtual_screen = pygame.Surface((self.screen_width, self.screen_height))
                
                # Update Scale
                pass_w = self.window_width / 1280.0
                pass_h = self.window_height / 720.0
                self.ui_scale = min(pass_w, pass_h)
                
                from managers.resource_manager import ResourceManager
                ResourceManager.get_instance().set_font_scale(self.ui_scale)

            # [Fix] Scale Mouse Events to Virtual Coordinates
            if hasattr(event, 'pos'):
                event.pos = (int(event.pos[0] / self.render_scale), int(event.pos[1] / self.render_scale))

            self.state_machine.handle_event(event)

    def get_scaled_mouse_pos(self):
        mx, my = pygame.mouse.get_pos()
        return (int(mx / self.render_scale), int(my / self.render_scale))

    def update(self, dt):
        self.state_machine.update(dt)

    def draw(self):
        self.state_machine.draw(self.virtual_screen)
        # Scale virtual screen to full window
        pygame.transform.scale(self.virtual_screen, (self.window_width, self.window_height), self.screen)
        pygame.display.flip()

    def quit(self):
        self.logger.info("SYSTEM", "Engine Shutting Down")
        pygame.quit()
        sys.exit()
