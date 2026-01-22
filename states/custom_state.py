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
        self.res = ResourceManager.get_instance()
        self.sound = SoundManager.get_instance()
        self.large_font = self.res.get_font('large')
        self.bold_font = self.res.get_font('bold')
        self.small_font = self.res.get_font('small')
        
        # 1. Load Custom Data
        custom = self.game.shared_data.get('custom', {})
        self.gender_idx = 0 if custom.get('gender') == 'MALE' else 1
        
        # Parts mapping
        self.parts_data = {
            'face': custom.get('face', {}),
            'hair': custom.get('hair', {}),
            'clothes': custom.get('clothes', {}),
            'shoes': custom.get('shoes', {}),
            'glasses': custom.get('glasses', {})
        }

        # Initialize defaults if missing
        for key in self.parts_data:
            if 'type' not in self.parts_data[key]: self.parts_data[key]['type'] = 0
            if 'color' not in self.parts_data[key]: self.parts_data[key]['color'] = 0
            if 'pixels' not in self.parts_data[key]: self.parts_data[key]['pixels'] = {}
            
            raw_pixels = self.parts_data[key]['pixels']
            new_pixels = {}
            for k, v in raw_pixels.items():
                if isinstance(k, str) and ',' in k:
                    try:
                        x, y = map(int, k.split(','))
                        new_pixels[(x, y)] = v
                    except: pass
                else:
                    new_pixels[k] = v
            self.parts_data[key]['pixels'] = new_pixels

        # UI State
        self.selected_cat = 'gender'
        self.edit_mode = 'SELECT' 
        self.brush_color_idx = 0
        self.zoom = 12
        self.grid_pos = (440, 240) 
        
        # [New] Undo & History
        self.undo_stack = [] # List of (part_key, {pixels_snapshot})
        
        self._init_selectors()
        self.palette_previews = {} 

    def _init_selectors(self):
        start_y = 190
        gap = 46
        self.selectors = [
            {'label': "GENDER", 'key': 'gender', 'y': start_y, 'type': 'list', 'options': ['MALE', 'FEMALE']},
            {'label': "SKIN", 'key': 'skin', 'y': start_y + gap, 'type': 'palette', 'palette_key': 'SKIN', 'part': 'face'},
            {'label': "EYE DESIGN", 'key': 'eye_t', 'y': start_y + gap * 2, 'type': 'grid', 'count': 5, 'part': 'face'},
            {'label': "MOUTH", 'key': 'mouth_t', 'y': start_y + gap * 3, 'type': 'grid', 'count': 5, 'part': 'face'},
            {'label': "HAIR STYLE", 'key': 'hair_t', 'y': start_y + gap * 4, 'type': 'grid', 'count': 5, 'part': 'hair'},
            {'label': "HAIR COLOR", 'key': 'hair_c', 'y': start_y + gap * 5, 'type': 'palette', 'palette_key': 'HAIR', 'part': 'hair'},
            {'label': "CLOTH TYPE", 'key': 'cloth_t', 'y': start_y + gap * 6, 'type': 'grid', 'count': 5, 'part': 'clothes'},
            {'label': "CLOTH COLOR", 'key': 'cloth_c', 'y': start_y + gap * 7, 'type': 'palette', 'palette_key': 'CLOTHES', 'part': 'clothes'},
            {'label': "GLASSES", 'key': 'glass_t', 'y': start_y + gap * 8, 'type': 'grid', 'count': 5, 'part': 'glasses'},
            {'label': "SHOES", 'key': 'shoe_t', 'y': start_y + gap * 9, 'type': 'list', 'options': ['NO', 'YES'], 'part': 'shoes'},
        ]

    def _save_local(self):
        final_parts = {}
        for k, v in self.parts_data.items():
            part_copy = v.copy()
            pixels_copy = {}
            for (px, py), col in part_copy.get('pixels', {}).items():
                pixels_copy[f"{px},{py}"] = col
            part_copy['pixels'] = pixels_copy
            final_parts[k] = part_copy

        custom_data = {
            'gender': 'MALE' if self.gender_idx == 0 else 'FEMALE',
            'face': final_parts['face'],
            'hair': final_parts['hair'],
            'clothes': final_parts['clothes'],
            'shoes': final_parts['shoes'],
            'glasses': final_parts['glasses']
        }
        self.game.shared_data['custom'] = custom_data
        try:
            with open("profile.json", "w", encoding='utf-8') as f:
                json.dump({'name': self.game.shared_data.get('player_name', 'Player'), 'custom': custom_data}, f)
        except: pass

    def handle_event(self, event):
        mx, my = self.game.get_scaled_mouse_pos()
        w, h = self.game.screen.get_size()

        if event.type == pygame.MOUSEBUTTONDOWN:
            # 1. Back Button
            if pygame.Rect(w//2 - 100, 650, 200, 50).collidepoint(mx, my) and event.button == 1:
                self.sound.play_sfx("CLICK")
                self._save_local()
                from states.main_lobby_state import MainLobbyState
                self.game.state_machine.change(MainLobbyState(self.game))
                return

            # 2. Mode Toggle Button
            if pygame.Rect(w - 220, 140, 200, 35).collidepoint(mx, my) and event.button == 1:
                self.sound.play_sfx("CLICK")
                self.edit_mode = 'DOT' if self.edit_mode == 'SELECT' else 'SELECT'
                return

            # 3. Category Selection (Always available)
            for s in self.selectors:
                if pygame.Rect(50, s['y'], 300, 40).collidepoint(mx, my) and event.button == 1:
                    if self.selected_cat != s['key']:
                        self.selected_cat = s['key']
                        self.sound.play_sfx("CLICK")
                        self.palette_previews.clear()

            if self.edit_mode == 'SELECT':
                if event.button == 1:
                    self._handle_select_clicks(mx, my)
            else:
                # [Dot Mode]
                # UNDO / RESET Buttons check
                if event.button == 1:
                    if pygame.Rect(420, 185, 80, 25).collidepoint(mx, my): # UNDO
                        self._undo()
                        return
                    if pygame.Rect(510, 185, 80, 25).collidepoint(mx, my): # RESET
                        self._reset_current_part()
                        return

                self._handle_dot_clicks(mx, my, is_continuous=False, button=event.button)

        # Continuous Drawing in DOT mode
        if self.edit_mode == 'DOT':
            l_down = pygame.mouse.get_pressed()[0]
            r_down = pygame.mouse.get_pressed()[2]
            if l_down:
                self._handle_dot_clicks(mx, my, is_continuous=True, button=1)
            elif r_down:
                self._handle_dot_clicks(mx, my, is_continuous=True, button=3)

    def _undo(self):
        if self.undo_stack:
            self.sound.play_sfx("CLICK")
            part, pixels_snap = self.undo_stack.pop()
            self.parts_data[part]['pixels'] = pixels_snap.copy()
            self.palette_previews.clear()

    def _reset_current_part(self):
        sel = next((s for s in self.selectors if s['key'] == self.selected_cat), None)
        if sel and 'part' in sel:
            self.sound.play_sfx("CLICK")
            self._save_undo(sel['part']) # Save state before resetting
            self.parts_data[sel['part']]['pixels'] = {}
            self.palette_previews.clear()

    def _save_undo(self, part):
        # Limit stack size
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)
        self.undo_stack.append((part, self.parts_data[part]['pixels'].copy()))

    def _get_val(self, sel):
        if self.selected_cat == 'gender': return self.gender_idx
        part = sel['part']
        field = 'type'
        if sel['key'] == 'skin': field = 'skin'
        elif sel['key'] == 'eye_t': field = 'eye_type'
        elif sel['key'] == 'mouth_t': field = 'mouth_type'
        elif 'color' in sel['label'].lower() or 'palette' == sel['type']: field = 'color'
        return self.parts_data[part].get(field, 0)

    def _set_val(self, sel, val):
        if self.selected_cat == 'gender': 
            self.gender_idx = val
            return
        part = sel['part']
        field = 'type'
        if sel['key'] == 'skin': field = 'skin'
        elif sel['key'] == 'eye_t': field = 'eye_type'
        elif sel['key'] == 'mouth_t': field = 'mouth_type'
        elif 'color' in sel['label'].lower() or 'palette' == sel['type']: field = 'color'
        self.parts_data[part][field] = val

    def _handle_select_clicks(self, mx, my):
        p_rect = pygame.Rect(400, 200, 450, 420)
        if not p_rect.collidepoint(mx, my): return

        sel = next(s for s in self.selectors if s['key'] == self.selected_cat)
        item_w, item_h = 90, 70
        gap_x, gap_y = 15, 15
        cols = 4

        if sel['type'] == 'palette':
            colors = CUSTOM_COLORS[sel['palette_key']]
            for i in range(len(colors)):
                row, col = i // cols, i % cols
                rect = pygame.Rect(420 + col*(item_w+gap_x), 260 + row*(item_h+gap_y), item_w, item_h)
                if rect.collidepoint(mx, my):
                    self.sound.play_sfx("CLICK")
                    self._set_val(sel, i)
                    self.palette_previews.clear()

        elif sel['type'] == 'grid':
            for i in range(sel['count']):
                row, col = i // cols, i % cols
                rect = pygame.Rect(420 + col*(item_w+gap_x), 260 + row*(item_h+gap_y), item_w, item_h)
                if rect.collidepoint(mx, my):
                    self.sound.play_sfx("CLICK")
                    self._set_val(sel, i)
                    self.palette_previews.clear()

        elif sel['type'] == 'list':
            options = sel.get('options', [])
            for i in range(len(options)):
                row, col = i // cols, i % cols
                rect = pygame.Rect(420 + col*(item_w+gap_x), 260 + row*(item_h+gap_y), item_w, item_h)
                if rect.collidepoint(mx, my):
                    self.sound.play_sfx("CLICK")
                    self._set_val(sel, i)
                    self.palette_previews.clear()

    def _handle_dot_clicks(self, mx, my, is_continuous=False, button=1):
        # 1. Grid Interaction
        grid_rect = pygame.Rect(self.grid_pos[0], self.grid_pos[1], 32 * self.zoom, 32 * self.zoom)
        if grid_rect.collidepoint(mx, my):
            px = (mx - self.grid_pos[0]) // self.zoom
            py = (my - self.grid_pos[1]) // self.zoom
            
            sel = next((s for s in self.selectors if s['key'] == self.selected_cat), None)
            if sel and 'part' in sel:
                part = sel['part']
                
                # Check for change before saving undo
                changed = False
                if button == 1: # Draw
                    if self.parts_data[part]['pixels'].get((px, py)) != self.brush_color_idx:
                        if not is_continuous: self._save_undo(part)
                        self.parts_data[part]['pixels'][(px, py)] = self.brush_color_idx
                        changed = True
                elif button == 3: # Erase (Right Click)
                    if (px, py) in self.parts_data[part]['pixels']:
                        if not is_continuous: self._save_undo(part)
                        del self.parts_data[part]['pixels'][(px, py)]
                        changed = True
                
                if changed and not is_continuous: 
                    self.sound.play_sfx("CLICK")

        # 2. Color Palette for Brush (Bottom area)
        if button == 1:
            pal_y = self.grid_pos[1] + 32 * self.zoom + 20
            colors = CUSTOM_COLORS['CLOTHES'] 
            for i, col in enumerate(colors):
                rect = pygame.Rect(420 + i * 35, pal_y, 30, 30)
                if rect.collidepoint(mx, my) and not is_continuous:
                    self.brush_color_idx = i
                    self.sound.play_sfx("CLICK")

    def _get_mock_entity(self):
        class MockEntity:
            def __init__(self, state):
                self.custom = {
                    'gender': 'MALE' if state.gender_idx == 0 else 'FEMALE',
                    'face': state.parts_data['face'].copy(),
                    'hair': state.parts_data['hair'].copy(),
                    'clothes': state.parts_data['clothes'].copy(),
                    'shoes': state.parts_data['shoes'].copy(),
                    'glasses': state.parts_data['glasses'].copy()
                }
                self.role, self.sub_role, self.alive, self.is_hiding = "PLAYER", "CITIZEN", True, False
                self.is_moving, self.move_state = False, "WALK"
                self.rect, self.name, self.facing_dir = pygame.Rect(0, 0, 32, 32), "PREVIEW", (0, 1)
        return MockEntity(self)

    def draw(self, screen):
        w, h = screen.get_size()
        screen.fill((18, 20, 25))
        
        # 0. Title & Preview Area
        header_h = int(h * 0.2)
        pygame.draw.rect(screen, (30, 32, 40), (0, 0, w, header_h))
        
        # Center Title Vertical in Header
        head_txt = self.large_font.render("CHARACTER STUDIO", True, (255, 255, 255))
        screen.blit(head_txt, (50, header_h//2 - head_txt.get_height()//2))

        # Preview on Top Right
        mock = self._get_mock_entity()
        preview_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        CharacterRenderer.draw_entity(preview_surf, mock, 0, 0)
        
        # Scale Preview based on header height
        p_size = int(header_h * 0.8)
        scaled_preview = pygame.transform.scale(preview_surf, (p_size, p_size))
        screen.blit(scaled_preview, (w - p_size - 40, (header_h - p_size)//2))

        # Mode Toggle Button
        mode_btn_w, mode_btn_h = 240, 40
        mode_rect = pygame.Rect(w - mode_btn_w - 50, header_h + 20, mode_btn_w, mode_btn_h)
        mx, my = self.game.get_scaled_mouse_pos()
        hover = mode_rect.collidepoint(mx, my)
        btn_col = (100, 150, 255) if self.edit_mode == 'DOT' else (150, 100, 255)
        if hover: btn_col = tuple(min(255, c + 30) for c in btn_col)
        pygame.draw.rect(screen, btn_col, mode_rect, border_radius=8)
        mode_txt = self.bold_font.render("DOT EDITOR" if self.edit_mode == 'SELECT' else "BACK TO SELECT", True, (255,255,255))
        screen.blit(mode_txt, mode_txt.get_rect(center=mode_rect.center))

        # 1. Categories (Left side)
        start_y = header_h + 30
        avail_h = h - start_y - 100 # leave space for save button
        sel_gap = max(35, int(avail_h / len(self.selectors)))
        sel_w = max(250, int(w * 0.25))
        
        for i, s in enumerate(self.selectors):
            # Update s['y'] dynamically for click handling
            s_y = start_y + i * sel_gap
            s['y'] = s_y # Store for click handler update
            
            is_active = self.selected_cat == s['key']
            bg_col = (70, 90, 150) if is_active else (35, 37, 45)
            rect = pygame.Rect(50, s_y, sel_w, sel_gap - 5)
            pygame.draw.rect(screen, bg_col, rect, border_radius=8)
            if is_active: pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=8)
            
            # Text Scaling check
            lbl_surf = self.bold_font.render(s['label'], True, (255, 255, 255))
            screen.blit(lbl_surf, (70, s_y + (sel_gap-5)//2 - lbl_surf.get_height()//2))

        # 2. Main Content Area (Right side)
        # Calculate dynamic positions (re-used logic from vars above ideally, but re-calculating for simplicity)
        header_h = int(h * 0.2)
        start_y = header_h + 30
        sel_w = max(250, int(w * 0.25))
        
        panel_x = 50 + sel_w + 30
        panel_y = start_y
        panel_w = max(400, w - panel_x - 50)
        panel_h = h - start_y - 120
        
        p_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(screen, (28, 30, 38), p_rect, border_radius=15)
        
        if self.edit_mode == 'SELECT':
            self._draw_select_mode(screen, p_rect)
        else:
            self._draw_dot_mode(screen, p_rect)

        # 4. Save Button
        btn_h = 60
        btn_back = pygame.Rect(w//2 - 150, h - 80, 300, btn_h)
        hover = btn_back.collidepoint(mx, my)
        pygame.draw.rect(screen, (100, 255, 100) if hover else (50, 180, 50), btn_back, border_radius=12)
        txt_img = self.large_font.render("SAVE & BACK", True, (255, 255, 255))
        screen.blit(txt_img, txt_img.get_rect(center=btn_back.center))

    def _draw_select_mode(self, screen, p_rect):
        sel = next(s for s in self.selectors if s['key'] == self.selected_cat)
        title_img = self.bold_font.render(f"SELECT {sel['label']}", True, (255, 215, 0))
        screen.blit(title_img, (420, 210))

        item_w, item_h = 90, 70
        gap_x, gap_y = 15, 15
        cols = 4

        if sel['type'] == 'palette':
            colors = CUSTOM_COLORS[sel['palette_key']]
            for i, col in enumerate(colors):
                r, c = i // cols, i % cols
                rect = pygame.Rect(420 + c*(item_w+gap_x), 260 + r*(item_h+gap_y), item_w, item_h)
                is_sel = self._get_val(sel) == i
                pygame.draw.rect(screen, col, rect, border_radius=6)
                if is_sel: pygame.draw.rect(screen, (255, 255, 255), rect, 4, border_radius=6)

        elif sel['type'] == 'grid':
            for i in range(sel['count']):
                r, c = i // cols, i % cols
                rect = pygame.Rect(420 + c*(item_w+gap_x), 260 + r*(item_h+gap_y), item_w, item_h)
                is_sel = self._get_val(sel) == i
                pygame.draw.rect(screen, (45, 47, 55), rect, border_radius=6)
                if is_sel: pygame.draw.rect(screen, (100, 200, 255), rect, 3, border_radius=6)
                
                prev_key = (self.selected_cat, i, 'MALE' if self.gender_idx == 0 else 'FEMALE')
                if prev_key not in self.palette_previews:
                    p_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
                    mock = self._get_mock_entity()
                    # Apply the value to the mock entity correctly
                    part = sel['part']
                    field = 'type'
                    if sel['key'] == 'skin': field = 'skin'
                    elif sel['key'] == 'eye_t': field = 'eye_type'
                    elif sel['key'] == 'mouth_t': field = 'mouth_type'
                    mock.custom[part][field] = i
                    
                    CharacterRenderer.draw_entity(p_surf, mock, 0, 0)
                    self.palette_previews[prev_key] = pygame.transform.scale(p_surf, (60, 60))
                screen.blit(self.palette_previews[prev_key], (rect.centerx - 30, rect.centery - 30))

        elif sel['type'] == 'list':
            for i, opt in enumerate(sel['options']):
                r, c = i // cols, i % cols
                rect = pygame.Rect(420 + c*(item_w+gap_x), 260 + r*(item_h+gap_y), item_w, item_h)
                is_sel = self._get_val(sel) == i
                pygame.draw.rect(screen, (60, 62, 75) if is_sel else (45, 47, 55), rect, border_radius=6)
                txt = self.bold_font.render(opt, True, (255, 255, 255))
                screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

    def _draw_dot_mode(self, screen, p_rect):
        sel = next((s for s in self.selectors if s['key'] == self.selected_cat), None)
        part_name = sel['label'] if sel else "PART"
        
        # Tools Header
        title_img = self.bold_font.render(f"DOT: {part_name}", True, (50, 255, 50))
        screen.blit(title_img, (420, 210))
        
        # UNDO / RESET Buttons
        mx, my = self.game.get_scaled_mouse_pos()
        u_rect = pygame.Rect(600, 205, 100, 30)
        r_rect = pygame.Rect(710, 205, 100, 30)
        
        pygame.draw.rect(screen, (60, 80, 100) if u_rect.collidepoint(mx, my) else (40, 50, 60), u_rect, border_radius=4)
        pygame.draw.rect(screen, (150, 50, 50) if r_rect.collidepoint(mx, my) else (100, 40, 40), r_rect, border_radius=4)
        
        ut = self.small_font.render("UNDO", True, (255, 255, 255))
        rt = self.small_font.render("RESET", True, (255, 255, 255))
        screen.blit(ut, ut.get_rect(center=u_rect.center))
        screen.blit(rt, rt.get_rect(center=r_rect.center))

        # 1. Background Character Reference
        ref_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        mock = self._get_mock_entity()
        CharacterRenderer.draw_entity(ref_surf, mock, 0, 0)
        scaled_ref = pygame.transform.scale(ref_surf, (32 * self.zoom, 32 * self.zoom))
        scaled_ref.set_alpha(100) 
        screen.blit(scaled_ref, self.grid_pos)

        # 2. Grid & Pixels
        for x in range(33):
            pygame.draw.line(screen, (60, 60, 70), (self.grid_pos[0] + x * self.zoom, self.grid_pos[1]), 
                             (self.grid_pos[0] + x * self.zoom, self.grid_pos[1] + 32 * self.zoom), 1)
        for y in range(33):
            pygame.draw.line(screen, (60, 60, 70), (self.grid_pos[0], self.grid_pos[1] + y * self.zoom), 
                             (self.grid_pos[0] + 32 * self.zoom, self.grid_pos[1] + y * self.zoom), 1)

        if sel and 'part' in sel:
            pixels = self.parts_data[sel['part']]['pixels']
            for (px, py), col_idx in pixels.items():
                p_col = CUSTOM_COLORS['CLOTHES'][col_idx % len(CUSTOM_COLORS['CLOTHES'])]
                pix_rect = pygame.Rect(self.grid_pos[0] + px * self.zoom, self.grid_pos[1] + py * self.zoom, self.zoom, self.zoom)
                pygame.draw.rect(screen, p_col, pix_rect)

        # 3. Palette for Brush
        pal_y = self.grid_pos[1] + 32 * self.zoom + 20
        colors = CUSTOM_COLORS['CLOTHES']
        for i, col in enumerate(colors):
            rect = pygame.Rect(420 + i * 36, pal_y, 32, 32)
            pygame.draw.rect(screen, col, rect, border_radius=4)
            if self.brush_color_idx == i:
                pygame.draw.rect(screen, (255, 255, 255), rect, 3, border_radius=4)
        
        help_txt = self.small_font.render("L: Draw | R: Erase | Hold and Drag supported", True, (150, 150, 150))
        screen.blit(help_txt, (420, pal_y + 45))
