import pygame
import random
import math
from core.base_state import BaseState
from settings import *
from systems.camera import Camera
from systems.fov import FOV
from systems.effects import VisualSound, SoundDirectionIndicator
from systems.renderer import CharacterRenderer, MapRenderer
from systems.lighting import LightingManager
from systems.time_system import TimeSystem
from systems.sound_system import SoundSystem
from core.world import GameWorld
from colors import COLORS
from managers.resource_manager import ResourceManager
from ui import UI
from entities.bullet import Bullet
from systems.debug_console import DebugConsole
from entities.npc import Dummy
from ui.widgets.pause_menu import PauseMenu
from ui.widgets.cctv_view import CCTVViewWidget

class PlayState(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.logger = game.logger
        self.resource_manager = ResourceManager.get_instance()
        self.world = GameWorld(game)
        self.time_system = TimeSystem(game)
        self.sound_system = SoundSystem(self.world)
        self.lighting = LightingManager(self)
        self.console = DebugConsole(game, self)
        self.pause_menu = PauseMenu(game) 
        self.cctv_widget = CCTVViewWidget(self)
        self.map_renderer = None
        self.camera = None
        self.fov = None
        self.visible_tiles = set()
        self.tile_alphas = {} 
        self.zoom_level = 1.5
        self.effect_surf = pygame.Surface((self.game.screen_width, self.game.screen_height), pygame.SRCALPHA)
        self.ui = None
        self.is_chatting = False
        self.chat_text = ""
        self.show_vote_ui = False
        self.my_vote_target = None
        self.candidate_rects = []
        self.heartbeat_timer = 0
        self.last_sent_pos = (0, 0)
        self.pov_target = None # [추가] 관전자 POV 추적 대상
        
        # [Work Navigation]
        self.work_target_tid = None
        self.work_check_timer = 0
        self.found_visible_work_target = False
        
        self.time_system.on_phase_change = self.on_phase_change
        self.time_system.on_morning = self.on_morning

    @property
    def player(self): return self.world.player
    @property
    def npcs(self): return self.world.npcs
    @property
    def map_manager(self): return self.world.map_manager
    @property
    def current_phase(self): return self.time_system.current_phase
    @property
    def current_phase_idx(self): return self.time_system.current_phase_idx
    @property
    def phases(self): return self.time_system.phases
    @property
    def state_timer(self): return self.time_system.state_timer
    @property
    def day_count(self): return self.time_system.day_count
    @property
    def weather(self): return self.time_system.weather
    @property
    def weather_particles(self): return self.time_system.weather_particles
    @property
    def is_blackout(self): return self.world.is_blackout
    @property
    def is_mafia_frozen(self): return self.world.is_mafia_frozen

    def enter(self, params=None):
        self.logger.info("PLAY", "Entering PlayState...")
        self.world.load_map("map.json")
        self.map_renderer = MapRenderer(self.world.map_manager)
        self.camera = Camera(self.game.screen_width, self.game.screen_height, self.world.map_manager.width, self.world.map_manager.height)
        self.camera.set_bounds(self.world.map_manager.width * TILE_SIZE, self.world.map_manager.height * TILE_SIZE)
        self.camera.set_zoom(self.zoom_level)
        self.fov = FOV(self.world.map_manager.width, self.world.map_manager.height, self.world.map_manager)
        self.world.init_entities()
        self.time_system.init_timer() 

        # [Network] Send Initial Spawn Position
        if self.player and hasattr(self.game, 'network') and self.game.network.connected:
            self.game.network.send_move(int(self.player.pos_x), int(self.player.pos_y), False, (0, 1))
            self.last_sent_pos = (int(self.player.pos_x), int(self.player.pos_y))

        self.sound_system.sound_manager.play_music("GAME_THEME")

        self.ui = UI(self)
        if self.weather == 'RAIN': self.ui.show_alert("It's Raining...", (100, 100, 255)); self.sound_system.sound_manager.play_sfx("ALERT")
        elif self.weather == 'FOG': self.ui.show_alert("Dense Fog...", (150, 150, 150)); self.sound_system.sound_manager.play_sfx("ALERT")
        elif self.weather == 'SNOW': self.ui.show_alert("It's Snowing...", (200, 200, 255)); self.sound_system.sound_manager.play_sfx("ALERT")

        # [AUTO CONNECT & START] 네트워크 미연결 시 자동 연결 시도
        if not hasattr(self.game, 'network'):
            from systems.network import NetworkManager
            self.game.network = NetworkManager()
            
        if not self.game.network.connected:
            self.logger.info("NET", "Auto-connecting to local server...")
            if self.game.network.connect():
                self.logger.info("NET", "Connected! Initializing Spectator Mode...")
                # 관전자 모드로 자동 설정 및 봇 추가
                # 잠시 대기 후 요청 (서버 처리 시간 고려)
                import time
                time.sleep(0.1)
                
                # [수정] 봇 15마리 대량 추가 요청
                for i in range(1, 16):
                    self.game.network.send_add_bot(f"Bot {i}", "PLAYER")
                    time.sleep(0.01) # 패킷 씹힘 방지 미세 딜레이
                
                self.game.network.send_start_game()
            else:
                self.logger.error("NET", "Failed to connect to server.")

        # [AUTO START] 이미 연결된 경우 바로 시작 요청
        elif self.game.network.connected:
            self.logger.info("NET", "Sending START_GAME request...")
            self.game.network.send_start_game()

    def on_phase_change(self, old_phase, new_phase):
        if old_phase == "AFTERNOON": self.show_vote_ui = False; self._process_voting_results()

    def on_morning(self):
        gx, gy = int(self.player.rect.centerx // TILE_SIZE), int(self.player.rect.centery // TILE_SIZE)
        is_indoors = (0 <= gx < self.world.map_manager.width and 0 <= gy < self.world.map_manager.height and self.world.map_manager.zone_map[gy][gx] in INDOOR_ZONES)
        self.player.morning_process(is_indoors)
        for n in self.npcs: n.morning_process()
        self.world.has_murder_occurred = False
        if self.time_system.daily_news_log: self.ui.show_daily_news(self.time_system.daily_news_log); self.time_system.daily_news_log = []

    def update(self, dt):
        if not self.player: return
        if self.player.is_dead and self.player.role != "SPECTATOR": self.player.change_role("SPECTATOR"); self.ui.show_alert("YOU DIED!", (255, 0, 0))
        if hasattr(self.game, 'network') and self.game.network.connected:
            for e in self.game.network.get_events():
                if e.get('type') == 'MOVE' and e.get('id') in self.world.entities_by_id:
                    ent = self.world.entities_by_id[e['id']]
                    if isinstance(ent, Dummy): ent.sync_state(e['x'], e['y'], 100, 100, 'CITIZEN', e['is_moving'], e['facing'])
                elif e.get('type') == 'TIME_SYNC': 
                    self.time_system.sync_time(e['phase_idx'], e['timer'], e['day'])
                    # [추가] 실시간 역할 동기화 (지속적)
                    roles_data = e.get('roles', {})
                    id_map = {str(k): v for k, v in self.world.entities_by_id.items()}
                    for pid_str, new_role in roles_data.items():
                        if pid_str in id_map:
                            ent = id_map[pid_str]
                            
                            # [수정] 무한 초기화 방지: 현재 역할과 새 역할 정밀 비교
                            current_role_check = ent.role
                            if ent.role == "CITIZEN" and getattr(ent, 'sub_role', None):
                                current_role_check = ent.sub_role
                                
                            if current_role_check != new_role and new_role != "RANDOM":
                                ent.change_role(new_role)
                                self.logger.info("REALTIME_SYNC", f"Entity {ent.name} -> {new_role}")

                elif e.get('type') == 'PLAYER_LIST':
                    # [동기화] 서버의 참가자 리스트와 월드 엔티티 동기화
                    participants = e.get('participants', [])
                    self.game.shared_data['participants'] = participants
                    
                    current_ids = set(self.world.entities_by_id.keys())
                    server_ids = set(str(p['id']) for p in participants)
                    
                    # 1. 없는 엔티티 제거
                    for uid in list(current_ids): # list()로 복사하여 순회 중 삭제 허용
                        if str(uid) not in server_ids and uid != self.player.uid:
                            ent = self.world.entities_by_id[uid]
                            ent.alive = False
                            if ent in self.world.npcs: self.world.npcs.remove(ent)
                            del self.world.entities_by_id[uid]
                            self.logger.info("SYNC", f"Removed entity {uid} (Not in server)")

                    # 2. 새로운 엔티티 추가
                    for p in participants:
                        pid = p['id']
                        if str(pid) not in current_ids and pid != self.game.network.my_id:
                            from entities.npc import Dummy
                            name = p.get('name', f"Entity {pid}")
                            role = p.get('role', 'CITIZEN')
                            sx, sy = self.world.find_safe_spawn()
                            new_npc = Dummy(sx, sy, None, self.world.map_manager.width, self.world.map_manager.height, name=name, role=role, zone_map=self.world.map_manager.zone_map, map_manager=self.world.map_manager)
                            new_npc.uid = pid
                            new_npc.is_master = False 
                            self.world.register_entity(new_npc)
                            self.world.npcs.append(new_npc)
                            self.logger.info("SYNC", f"Added entity {pid} ({name})")

                elif e.get('type') == 'GAME_START':
                    # [핵심 수정] ID 및 이름 기반 이중 매칭 동기화
                    player_data = e.get('players', {})
                    print(f"\n[DEBUG_NET] GAME_START Data: {player_data}\n") 
                    self.logger.info("NET", f"GAME_START: Syncing {len(player_data)} entities.")
                    
                    id_map = {str(k): v for k, v in self.world.entities_by_id.items()}
                    name_map = {v.name: v for v in self.world.entities_by_id.values()}
                    
                    for pid_str, data in player_data.items():
                        target_ent = None
                        if pid_str in id_map: target_ent = id_map[pid_str]
                        elif data.get('name') in name_map: target_ent = name_map[data.get('name')]
                            
                        if target_ent:
                            new_role = data.get('role', 'CITIZEN')
                            target_ent.change_role(new_role)
                            self.logger.info("SYNC_SUCCESS", f"Synced {target_ent.name}: {new_role}")
                        else:
                            self.logger.warning("SYNC_FAIL", f"No entity found for PID {pid_str} / Name {data.get('name')}")

        if self.player.alive:
            curr_pos = (int(self.player.pos_x), int(self.player.pos_y))
            if curr_pos != self.last_sent_pos and hasattr(self.game, 'network') and self.game.network.connected:
                self.game.network.send_move(curr_pos[0], curr_pos[1], self.player.is_moving, self.player.facing_dir); self.last_sent_pos = curr_pos
        if hasattr(self.game, 'network') and self.game.network.connected:
            for n in self.npcs:
                if n.is_master:
                    n_pos = (int(n.pos_x), int(n.pos_y))
                    if not hasattr(n, 'last_sent_pos'): n.last_sent_pos = (0, 0)
                    if n_pos != n.last_sent_pos: self.game.network.send({"type": "MOVE", "id": n.uid, "x": n_pos[0], "y": n_pos[1], "is_moving": n.is_moving, "facing": n.facing_dir}); n.last_sent_pos = n_pos
        # Update Work Target Navigation
        now = pygame.time.get_ticks()
        if now > self.work_check_timer:
            self.work_check_timer = now + 500 # Check every 0.5s
            self.work_target_tid = None
            
            # Check if player needs to work
            is_working_hours = self.current_phase in ["MORNING", "NOON", "AFTERNOON"]
            has_quota = self.player.daily_work_count < DAILY_QUOTA
            
            if self.player.alive and is_working_hours and has_quota:
                job_key = None
                if self.player.role == "DOCTOR":
                    job_key = "DOCTOR"
                elif self.player.role == "CITIZEN":
                    job_key = self.player.sub_role
                
                if job_key and job_key in WORK_SEQ:
                    # Current step target TID
                    step = self.player.work_step % 3
                    self.work_target_tid = WORK_SEQ[job_key][step]

        self.time_system.update(dt); self.world.update(dt, self.current_phase, self.weather, self.day_count); self.lighting.update(dt)
        if self.camera: self.camera.resize(self.game.screen_width, self.game.screen_height)
        if not self.player.is_dead and not (self.ui.show_vending or self.ui.show_inventory or self.ui.show_voting or self.is_chatting):
            if not self.player.is_stunned():
                fx = self.player.update(self.current_phase, self.npcs, self.world.is_blackout, self.weather)
                if fx:
                    for f in fx: self._process_sound_effect(f)
                for p in self.player.popups:
                    if p['text'] == "OPEN_SHOP": self.ui.toggle_vending_machine(); self.player.popups.remove(p); break
            self.player.update_bullets(self.npcs)
        if self.player.role in ["CITIZEN", "DOCTOR", "FARMER", "MINER", "FISHER"] and self.current_phase == "NIGHT":
            nearest = min([math.hypot(n.rect.centerx-self.player.rect.centerx, n.rect.centery-self.player.rect.centery) for n in self.npcs if n.role == "MAFIA" and n.alive] + [float('inf')])
            if nearest < 640:
                self.player.emotions['ANXIETY'] = int((640 - nearest) / 60)
                if pygame.time.get_ticks() - self.heartbeat_timer > max(300, int(nearest * 2)):
                    self.heartbeat_timer = pygame.time.get_ticks(); self.world.effects.append(VisualSound(self.player.rect.centerx, self.player.rect.centery, "THUMP", (100, 0, 0), size_scale=0.5))
            else: self.player.emotions['ANXIETY'] = 0
        if self.current_phase == "NIGHT" and random.random() < 0.005:
            for n in self.npcs:
                if n.role == "MAFIA" and n.alive:
                    gx, gy = int(n.rect.centerx // TILE_SIZE), int(n.rect.centery // TILE_SIZE)
                    if 0 <= gy < self.world.map_manager.height and 0 <= gx < self.world.map_manager.width:
                        zid = self.world.map_manager.zone_map[gy][gx]
                        if zid in ZONES and zid != 1: self.time_system.mafia_last_seen_zone = ZONES[zid]['name']
        for n in self.npcs:
            if not n.is_stunned(): self._handle_npc_action(n.update(self.current_phase, self.player, self.npcs, self.world.is_mafia_frozen, self.world.noise_list, self.day_count, self.world.bloody_footsteps), n, 0)
        
        # [수정] 카메라 및 FOV 업데이트 (POV 시스템 반영)
        if self.player.role == "SPECTATOR":
            if self.pov_target:
                # 1인칭 POV 모드: 타겟 고정 및 타겟의 시야 재현
                self.camera.update(self.pov_target.rect.centerx, self.pov_target.rect.centery)
                rad = self.pov_target.get_vision_radius(self.lighting.current_vision_factor, self.world.is_blackout, self.weather) if hasattr(self.pov_target, 'get_vision_radius') else 10
                direction = getattr(self.pov_target, 'facing_dir', None) if (getattr(self.pov_target, 'flashlight_on', False) and self.current_phase in ['EVENING', 'NIGHT', 'DAWN']) else None
                self.visible_tiles = self.fov.cast_rays(self.pov_target.rect.centerx, self.pov_target.rect.centery, rad, direction, 60)
            else:
                # 전지적 시점: 자유 이동 및 넓은 시야
                self._update_spectator_camera()
                rad = 100 
                self.visible_tiles = self.fov.cast_rays(self.camera.x + self.camera.width//2, self.camera.y + self.camera.height//2, rad, None, 60)
        else:
            self.camera.update(self.player.rect.centerx, self.player.rect.centery)
            rad = self.player.get_vision_radius(self.lighting.current_vision_factor, self.world.is_blackout, self.weather)
            direction = self.player.facing_dir if (self.player.role == "POLICE" and self.player.flashlight_on and self.current_phase in ['EVENING', 'NIGHT', 'DAWN']) else None
            self.visible_tiles = self.fov.cast_rays(self.player.rect.centerx, self.player.rect.centery, rad, direction, 60)
        
        for tile in self.visible_tiles: self.tile_alphas[tile] = min(255, self.tile_alphas.get(tile, 0) + 15)
        for tile in list(self.tile_alphas.keys()):
            if tile not in self.visible_tiles:
                self.tile_alphas[tile] -= 15
                if self.tile_alphas[tile] <= 0: del self.tile_alphas[tile]

    def _update_spectator_camera(self):
        keys = pygame.key.get_pressed()
        cam_dx, cam_dy = 0, 0
        cam_speed = 15

        if keys[pygame.K_a]: cam_dx = -cam_speed
        if keys[pygame.K_d]: cam_dx = cam_speed
        if keys[pygame.K_w]: cam_dy = -cam_speed
        if keys[pygame.K_s]: cam_dy = cam_speed

        if cam_dx != 0 or cam_dy != 0:
            self.ui.spectator_follow_target = None
            self.camera.move(cam_dx, cam_dy)
        elif self.ui.spectator_follow_target:
            t = self.ui.spectator_follow_target
            if t.alive:
                self.camera.update(t.rect.centerx, t.rect.centery)
            else:
                self.ui.spectator_follow_target = None

    def execute_siren(self):
        for n in [x for x in self.npcs if x.role == "MAFIA" and x.alive]:
            n.is_frozen = True; n.frozen_timer = pygame.time.get_ticks() + 5000; self.world.effects.append(VisualSound(n.rect.centerx, n.rect.centery, "SIREN", (0, 0, 255), 2.0))
        self.world.is_mafia_frozen = True; self.world.frozen_timer = pygame.time.get_ticks() + 5000
        self.ui.show_alert("!!! SIREN !!!", (100, 100, 255)); self.sound_system.sound_manager.play_sfx("SIREN")

    def execute_sabotage(self):
        self.world.is_blackout = True; self.world.blackout_timer = pygame.time.get_ticks() + 10000
        self.world.effects.append(VisualSound(self.player.rect.centerx, self.player.rect.centery, "BOOM", (50, 50, 50), 3.0))
        self.ui.show_alert("!!! SABOTAGE !!!", (255, 0, 0)); self.sound_system.sound_manager.play_sfx("EXPLOSION")
        for t in [x for x in self.npcs + [self.player] if x.role in ["CITIZEN", "DOCTOR"] and x.alive]: t.emotions['FEAR'] = 1

    def execute_gunshot(self, shooter, target_pos=None):
        angle = math.atan2(target_pos[1]-shooter.rect.centery, target_pos[0]-shooter.rect.centerx) if target_pos else math.atan2(shooter.facing_dir[1], shooter.facing_dir[0])
        self.player.bullets.append(Bullet(shooter.rect.centerx, shooter.rect.centery, angle, is_enemy=(shooter.role != "PLAYER")))
        self.world.effects.append(VisualSound(shooter.rect.centerx, shooter.rect.centery, "BANG!", (255, 200, 50), 2.0))

    def _handle_npc_action(self, action, n, now):
        if action == "USE_SIREN": self.execute_siren()
        elif action == "USE_SABOTAGE": self.execute_sabotage()
        elif action == "SHOOT_TARGET" and n.chase_target: self.execute_gunshot(n, (n.chase_target.rect.centerx, n.chase_target.rect.centery))
        elif action == "MURDER_OCCURRED": self.world.has_murder_occurred = True
        elif action == "FOOTSTEP": self._process_sound_effect(("FOOTSTEP", n.rect.centerx, n.rect.centery, TILE_SIZE*6, n.role))

    def _process_sound_effect(self, f):
        if len(f) == 5:
            s_type, fx_x, fx_y, rad, source_role = f
        else:
            s_type, fx_x, fx_y, rad = f
            source_role = "UNKNOWN"

        if hasattr(self, 'weather') and self.weather == 'RAIN': rad *= 0.8
        
        # Delegate to SoundSystem
        # Re-pack the tuple with modified radius
        self.sound_system.process_sound_effect((s_type, fx_x, fx_y, rad, source_role), self.player)

    def _handle_v_action(self):
        targets = sorted([(math.hypot(n.rect.centerx-self.player.rect.centerx, n.rect.centery-self.player.rect.centery), n) for n in self.npcs if n.alive], key=lambda x: x[0])
        target = targets[0][1] if targets and targets[0][0] <= 100 else None
        if self.player.role == "DOCTOR":
            res = self.player.do_heal(target)
            if res: self.player.add_popup(res[0] if isinstance(res, tuple) else res, (200, 200, 255))
        else:
            res = self.player.do_attack(target)
            if res: self.player.add_popup(res[0][0], (255, 50, 50)); self._process_sound_effect(res[1])

    def _process_voting_results(self):
        if self.my_vote_target: self.my_vote_target.vote_count += 1; self.my_vote_target = None
        for n in [x for x in self.npcs if x.alive]:
            if random.random() < 0.3: target = random.choice([self.player] + [x for x in self.npcs if x.alive]); target.vote_count += 1
        candidates = sorted([self.player] + self.npcs, key=lambda x: x.vote_count, reverse=True)
        if candidates and candidates[0].vote_count >= 2:
            top = random.choice([c for c in candidates if c.vote_count == candidates[0].vote_count])
            top.is_dead = True; self.player.add_popup("EXECUTION!", (255, 0, 0))

    def draw(self, screen):
        screen.fill(COLORS['BG'])
        if not self.camera: return
        canvas = self.lighting.draw(screen, self.camera)
        canvas.fill(COLORS['BG'])
        if self.map_renderer:
            vis = self.visible_tiles if self.player.role != "SPECTATOR" else None
            self.map_renderer.draw(canvas, self.camera, 0, visible_tiles=vis, tile_alphas=self.tile_alphas)
        
        for n in self.npcs:
            if n.role == "SPECTATOR": continue # 관전자는 맵에 그리지 않음
            if (int(n.rect.centerx//TILE_SIZE), int(n.rect.centery//TILE_SIZE)) in self.visible_tiles or self.player.role == "SPECTATOR":
                n.draw(canvas, self.camera.x, self.camera.y, self.player.role, self.current_phase, self.player.device_on)
        
        if not self.player.is_dead and self.player.role != "SPECTATOR": 
            CharacterRenderer.draw_entity(canvas, self.player, self.camera.x, self.camera.y, self.player.role, self.current_phase, self.player.device_on)
        
        # [추가] 관전자 전용 월드 오버레이 (E-SPORTS 중계용)
        if self.player.role == "SPECTATOR":
            for ent in [self.player] + self.npcs:
                if not ent.alive or ent.role == "SPECTATOR": continue
                
                # 머리 위 위치 계산
                rx = ent.rect.centerx - self.camera.x
                ry = ent.rect.top - self.camera.y - 10
                
                status_text = ""
                status_col = (255, 255, 255)
                
                if ent.is_hiding: status_text = "HIDING"; status_col = (150, 100, 255)
                elif getattr(ent, 'is_working', False): status_text = "WORKING"; status_col = (255, 255, 0)
                elif getattr(ent, 'chase_target', None): status_text = "CHASING"; status_col = (255, 50, 50)
                elif ent.is_stunned(): status_text = "STUNNED"; status_col = (200, 200, 200)
                
                if status_text:
                    s_font = pygame.font.SysFont("arial", 10, bold=True)
                    txt = s_font.render(status_text, True, status_col)
                    canvas.blit(txt, (rx - txt.get_width()//2, ry - 5))

        for fx in self.world.effects: fx.draw(canvas, self.camera.x, self.camera.y)
        for i in self.world.indicators: i.draw(canvas, self.player.rect, self.camera.x, self.camera.y)
        if self.player.role != "SPECTATOR": self.lighting.apply_lighting(self.camera)

        # [Work Target Indicator - Highlight] - DRAWN ON CANVAS
        self.found_visible_work_target = False
        if self.work_target_tid and self.player.alive:
            target_positions = self.world.map_manager.tile_cache.get(self.work_target_tid, [])
            if target_positions:
                visible_targets_for_highlight = []
                for (tx, ty) in target_positions:
                    canvas_tx = tx - self.camera.x
                    canvas_ty = ty - self.camera.y
                    if -TILE_SIZE < canvas_tx < self.camera.width and -TILE_SIZE < canvas_ty < self.camera.height:
                        visible_targets_for_highlight.append((canvas_tx, canvas_ty))
                
                if visible_targets_for_highlight:
                    self.found_visible_work_target = True
                    pulse = (pygame.time.get_ticks() % 1000) / 500.0
                    if pulse > 1.0: pulse = 2.0 - pulse
                    glow_val = int(100 + 155 * pulse)
                    for (stx, sty) in visible_targets_for_highlight:
                        pygame.draw.rect(canvas, (glow_val, glow_val, 0), (stx, sty, TILE_SIZE, TILE_SIZE), 2)

        # --- FINAL SCALING: CANVAS -> SCREEN ---
        screen.blit(pygame.transform.scale(canvas, (self.game.screen_width, self.game.screen_height)), (0, 0))
        
        # [Minigame] Draw on SCREEN space to be always in the center
        if self.player.minigame.active:
            mx = self.game.screen_width // 2
            my = (self.game.screen_height // 2) - (self.player.minigame.height // 2)
            self.player.minigame.draw(screen, mx, my)
        
        # --- DRAW SCREEN-SPACE UI (Weather, Pinpoint, etc.) ---
        if self.weather == 'RAIN':
            for p in self.weather_particles: pygame.draw.line(screen, (150, 150, 255, 150), (p[0], p[1]), (p[0]-2, p[1]+10))
        elif self.weather == 'SNOW':
            for p in self.weather_particles: pygame.draw.circle(screen, (255, 255, 255, 200), (int(p[0]), int(p[1])), 2)

        # [Work Target Indicator - Pinpoint Arrow] - DRAWN ON SCREEN
        if self.work_target_tid and self.player.alive and not self.found_visible_work_target:
            target_positions = self.world.map_manager.tile_cache.get(self.work_target_tid, [])
            if target_positions:
                nearest_pos = None
                min_dist_sq = float('inf')
                # World Coords
                px_world, py_world = self.player.rect.centerx, self.player.rect.centery
                
                for (tx, ty) in target_positions:
                    cx, cy = tx + TILE_SIZE//2, ty + TILE_SIZE//2
                    dist_sq = (px_world - cx)**2 + (py_world - cy)**2
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        nearest_pos = (tx, ty)
                
                if nearest_pos:
                    tx_world, ty_world = nearest_pos
                    sw, sh = self.game.screen_width, self.game.screen_height
                    zoom = self.camera.zoom_level
                    
                    # Player Screen Position
                    px = (self.player.rect.centerx - self.camera.x) * zoom
                    py = (self.player.rect.centery - self.camera.y) * zoom
                    
                    # Target World Center
                    target_cx = tx_world + TILE_SIZE//2
                    target_cy = ty_world + TILE_SIZE//2
                    
                    # Vector from Player to Target (World Space)
                    dx_world = target_cx - self.player.rect.centerx
                    dy_world = target_cy - self.player.rect.centery
                    angle = math.atan2(dy_world, dx_world)
                    
                    # Normalized Direction
                    dist = math.hypot(dx_world, dy_world)
                    if dist == 0: dist = 1
                    dir_x = dx_world / dist
                    dir_y = dy_world / dist
                    
                    # Screen bounds padding
                    pad = 40
                    
                    # Ray-Box Intersection from (px, py) to screen edges
                    t_min = float('inf')
                    
                    # Right Edge (x = sw - pad)
                    if dir_x > 0:
                        t = (sw - pad - px) / dir_x
                        if t > 0: t_min = min(t_min, t)
                    # Left Edge (x = pad)
                    elif dir_x < 0:
                        t = (pad - px) / dir_x
                        if t > 0: t_min = min(t_min, t)
                        
                    # Bottom Edge (y = sh - pad)
                    if dir_y > 0:
                        t = (sh - pad - py) / dir_y
                        if t > 0: t_min = min(t_min, t)
                    # Top Edge (y = pad)
                    elif dir_y < 0:
                        t = (pad - py) / dir_y
                        if t > 0: t_min = min(t_min, t)
                    
                    if t_min != float('inf'):
                        arrow_px = px + dir_x * t_min
                        arrow_py = py + dir_y * t_min
                        
                        # Draw Arrow
                        pygame.draw.circle(screen, (255, 255, 0), (int(arrow_px), int(arrow_py)), 8)
                        end_x = arrow_px + math.cos(angle) * 15
                        end_y = arrow_py + math.sin(angle) * 15
                        pygame.draw.line(screen, (255, 255, 0), (arrow_px, arrow_py), (end_x, end_y), 3)

        if self.ui: self.ui.draw(screen)
        self.console.draw(screen)
        
        if self.cctv_widget.active:
            self.cctv_widget.draw(screen)
        
        if self.pause_menu.active:
            self.pause_menu.draw(screen)

    def handle_event(self, event):
        if self.console.handle_event(event): return
        
        if self.pause_menu.active:
            self.pause_menu.handle_event(event)
            return

        if self.ui.show_vending or self.ui.show_inventory or self.ui.show_voting or self.ui.show_news:
            if event.type == pygame.KEYDOWN:
                res = self.ui.handle_keyboard(event.key, self.npcs)
                if res:
                    if isinstance(res, tuple):
                        if res[0]: self.player.add_popup(res[0]); self._process_sound_effect(res[1])
                    else: self.player.add_popup(res)
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.cctv_widget.active: self.cctv_widget.close(); return
                self.pause_menu.open()
                return

            if not self.player.is_dead:
                if self.cctv_widget.active:
                    if event.key == pygame.K_SPACE: self.cctv_widget.next_cam()
                    elif event.key == pygame.K_q: self.cctv_widget.close()
                    return

                if event.key == pygame.K_z and self.current_phase == "AFTERNOON": self.show_vote_ui = not self.show_vote_ui
                elif event.key == pygame.K_v: self._handle_v_action()
                elif event.key == pygame.K_f: self.player.toggle_flashlight()
                elif event.key == pygame.K_q:
                    # [CCTV Logic]
                    if self.player.role == "POLICE":
                        if self.cctv_widget.active: self.cctv_widget.close()
                        else: self.cctv_widget.open()
                    else:
                        msg = self.player.toggle_device()
                        if msg: self.player.add_popup(msg)
                elif event.key == pygame.K_i: self.ui.toggle_inventory()
                elif event.key == pygame.K_r:
                    msg = self.player.use_active_skill()
                    if msg == "USE_SABOTAGE": self.execute_sabotage()
                    elif msg == "USE_SIREN": self.execute_siren()
                    elif msg: self.player.add_popup(msg)
                else:
                    for k, v in ITEMS.items():
                        if v['key'] == event.key:
                            res = self.player.use_item(k)
                            if isinstance(res, tuple): self.player.add_popup(res[0]); self._process_sound_effect(res[1])
                            elif res: self.player.add_popup(res)
                            break
        if self.player.minigame.active: self.player.minigame.handle_event(event); return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # 1. Minimap Click (All roles if needed, mostly spectator)
                mm_rect = self.ui.minimap_rect
                if mm_rect.collidepoint(event.pos):
                    # Calculate map relative pos
                    rx = (event.pos[0] - mm_rect.x) / mm_rect.width
                    ry = (event.pos[1] - mm_rect.y) / mm_rect.height
                    
                    target_world_x = rx * (self.world.map_manager.width * TILE_SIZE)
                    target_world_y = ry * (self.world.map_manager.height * TILE_SIZE)
                    
                    self.ui.spectator_follow_target = None # Manual move breaks follow
                    self.camera.update(target_world_x, target_world_y)
                    return

                if self.show_vote_ui and self.candidate_rects:
                    for target, rect in self.candidate_rects:
                        if rect.collidepoint(event.pos):
                            self.my_vote_target = target
                            self.player.add_popup(f"Voted for {target.name}", (100, 255, 100))

                if self.player.role == "SPECTATOR":
                    # 1. 사이드바 리스트 클릭 처리
                    for rect, ent in self.ui.entity_rects:
                        if rect.collidepoint(event.pos):
                            if self.pov_target == ent:
                                self.pov_target = None # 해제
                            else:
                                self.pov_target = ent # 1인칭 POV 시작
                            return
                    
                    # 2. Skip Phase 버튼 처리
                    if hasattr(self.ui, 'skip_btn_rect') and self.ui.skip_btn_rect.collidepoint(event.pos):
                        self.time_system.state_timer = 0
                        return
                    
                    # 3. 월드 상의 엔티티 직접 클릭 처리
                    mx, my = event.pos
                    world_mx = mx / self.zoom_level + self.camera.x
                    world_my = my / self.zoom_level + self.camera.y
                    click_rect = pygame.Rect(world_mx - 15, world_my - 15, 30, 30)
                    for ent in [self.player] + self.npcs:
                        if ent.alive and click_rect.colliderect(ent.rect) and ent.role != "SPECTATOR":
                            self.pov_target = ent if self.pov_target != ent else None
                            return
        if event.type == pygame.MOUSEWHEEL and self.player.role == "SPECTATOR":
            if pygame.mouse.get_pos()[0] > self.game.screen_width - 300: self.ui.spectator_scroll_y = max(0, self.ui.spectator_scroll_y - event.y * 20)
            else: self.zoom_level = max(0.2, min(4.0, self.zoom_level + (0.2 if event.y > 0 else -0.2))); self.camera.set_zoom(self.zoom_level)