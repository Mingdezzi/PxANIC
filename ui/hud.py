import pygame
from ui.widgets.status import PlayerStatusWidget
from ui.widgets.spectator import SpectatorDashboard
from ui.widgets.environment import EnvironmentWidget
from ui.widgets.controls import ControlsWidget
from ui.widgets.bars import ActionBarsWidget
from ui.widgets.minimap import MinimapWidget
from ui.widgets.panels import EmotionPanelWidget
from ui.widgets.tools import SpecialToolsWidget

class HUD:
    def __init__(self, game):
        self.game = game
        self.widgets = [
            PlayerStatusWidget(game),
            EnvironmentWidget(game),
            ControlsWidget(game),
            ActionBarsWidget(game),
            MinimapWidget(game),
            EmotionPanelWidget(game),
            SpecialToolsWidget(game),
            SpectatorDashboard(game)
        ]

    def draw(self, screen):
        role = self.game.player.role if self.game.player else "CITIZEN"
        
        if role == "SPECTATOR":
            # Draw only Spectator Dashboard + Minimap
            # Index 7 is SpectatorDashboard (added last)
            self.widgets[7].draw(screen)
            
            # Move Minimap to bottom of panel and draw
            # [Responsive] Position relative to screen width
            w, h = screen.get_size()
            minimap = self.widgets[4]
            # minimap.rect.topleft = (960 + 10, 420) # Old Hardcoded
            
            panel_w = 300
            mm_size = 300
            mm_x = w - panel_w
            mm_y = h - mm_size
            
            original_rect = minimap.rect.copy()
            minimap.rect.topleft = (mm_x, mm_y) 
            minimap.rect.width = mm_size
            minimap.rect.height = mm_size
            minimap.draw(screen)
            minimap.rect = original_rect # Restore for next frame logic impact?
        else:
            # Draw all normal widgets EXCEPT SpectatorDashboard
            for i, widget in enumerate(self.widgets):
                if i != 7: # Skip SpectatorDashboard
                    widget.draw(screen)

    def get_minimap_rect(self):
        # MinimapWidget is the 5th widget (index 4)
        return self.widgets[4].rect
