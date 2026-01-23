import pygame
import sys
import gc
import time
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from engine.core.state_machine import StateMachine
from engine.core.logger import GameLogger

class GameEngine:
    def __init__(self):
        pygame.init()
        # [Optimization] GC enabled for stability
        # gc.disable()
        
        self.logger = GameLogger.get_instance()
        self.logger.info("SYSTEM", "Game Engine Initializing...")

        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
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
                self.screen_width, self.screen_height = event.w, event.h
                self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

            self.state_machine.handle_event(event)

    def update(self, dt):
        self.state_machine.update(dt)

    def draw(self):
        self.state_machine.draw(self.screen)
        pygame.display.flip()

    def quit(self):
        self.logger.info("SYSTEM", "Engine Shutting Down")
        pygame.quit()
        sys.exit()
