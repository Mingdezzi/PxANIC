import pygame
import json
import os
from engine.core.state import State
from managers.resource_manager import ResourceManager
from engine.audio.sound_manager import SoundManager
from colors import CUSTOM_COLORS
from systems.renderer import CharacterRenderer

class CustomizationState(State):
    def __init__(self, game):
        super().__init__(game)
        from ui.widgets.customizer import CustomizerWidget
        self.customizer = CustomizerWidget(game)
        self.customizer.open()
        
    def handle_event(self, event):
        self.customizer.handle_event(event)

    def update(self, dt):
        # If widget is closed, return to Lobby
        if not self.customizer.active:
            from states.main_lobby_state import MainLobbyState
            self.game.state_machine.change(MainLobbyState(self.game))

    def draw(self, screen):
        screen.fill((20, 20, 25))
        self.customizer.draw(screen)
