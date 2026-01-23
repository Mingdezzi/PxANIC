
import sys
import os
import pygame

sys.path.append(os.getcwd())
os.environ['SDL_VIDEODRIVER'] = 'dummy'
pygame.init()
pygame.display.set_mode((1024, 768)) # Standard resolution

# Mock Entity
class MockEntity:
    def __init__(self):
        self.alive = True
        self.rect = pygame.Rect(0,0,32,32)
        self.role = "CITIZEN"
        self.sub_role = None
        self.is_hiding = False
        self.facing_dir = (0, 1)
        self.name = "Test"
        self.custom = {
            'gender': 'MALE',
            'hair': {'id': 2, 'color': 1}, # Bob hair, brown
            'clothes': {'top': 0, 'bottom': 0}
        }

try:
    from systems.renderer import CharacterRenderer
    from ui.widgets.customizer import CustomizerWidget
    
    # 1. Test Renderer Crash Fix (Hair)
    print("Testing Renderer Hair Loop...")
    screen = pygame.display.get_surface()
    entity = MockEntity()
    # This caused a crash before
    CharacterRenderer.draw_entity(screen, entity, 0, 0) 
    print("Renderer draw_entity passed (Hair fix verified)")
    
    # 2. Test New UI Layout
    print("Testing Customizer UI Layout...")
    class MockGame:
        def __init__(self):
            self.player = None
            self.shared_data = {'custom': {}}
            
    widget = CustomizerWidget(MockGame())
    widget.open()
    
    # Draw frame
    widget.draw(screen)
    print("UI Draw passed")
    
    # Simulate a click on a tab (Top Right)
    # Preview width is 300, padding 20 -> Start x=320
    # Tab 0 rect approx (320, 20, 90, 40)
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (330, 30), 'button': 1})
    widget.handle_event(event)
    print("UI Click Event passed")
    
    print("All System Checks Passed")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
