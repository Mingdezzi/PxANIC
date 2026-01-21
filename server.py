import socket
import threading
import json
import time
from settings import NETWORK_PORT, DEFAULT_PHASE_DURATIONS

class GameServer:
    def __init__(self):
        self.host = "0.0.0.0"
        self.port = NETWORK_PORT
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.clients = {} # {socket: pid}
        self.players = {} # {pid: data}
        self.next_id = 0
        self.game_started = False
        self.running = True
        
        # Time Management
        self.phases = ["DAWN", "MORNING", "NOON", "AFTERNOON", "EVENING", "NIGHT"]
        # [수정] 게임 시작 시 바로 업무를 시작하도록 MORNING(1)부터 시작
        self.current_phase_idx = 1 
        self.day_count = 1
        self.state_timer = DEFAULT_PHASE_DURATIONS[self.phases[self.current_phase_idx]]
        self.last_tick = time.time()
        self.last_sync_time = 0 # [추가] 패킷 폭주 방지용 타이머

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            print(f"[SERVER] Running on {self.host}:{self.port}")

            threading.Thread(target=self.game_loop, daemon=True).start()

            while self.running:
                client_sock, addr = self.server_socket.accept()
                pid = self.next_id
                self.next_id += 1
                
                self.clients[client_sock] = pid
                self.players[pid] = {
                    'id': pid, 'name': f"Player {pid+1}", 'role': 'CITIZEN',
                    'group': 'PLAYER', 'type': 'PLAYER', 'x': -1000, 'y': -1000, 'alive': True
                }

                thread = threading.Thread(target=self.handle_client, args=(client_sock, pid))
                thread.daemon = True
                thread.start()
        except Exception as e:
            print(f"[SERVER] Critical Error: {e}")
        finally:
            self.server_socket.close()

    def game_loop(self):
        while self.running:
            time.sleep(0.1)
            if not self.game_started: continue
            
            now = time.time()
            dt = now - self.last_tick
            self.last_tick = now
            
            self.state_timer -= dt
            if self.state_timer <= 0:
                self._advance_phase()
            
            # [수정] 정확히 1초 간격으로만 전송 (폭주 방지)
            if now - self.last_sync_time >= 1.0:
                self.last_sync_time = now
                packet = {
                    "type": "TIME_SYNC", 
                    "phase_idx": self.current_phase_idx, 
                    "timer": self.state_timer, 
                    "day": self.day_count,
                    "roles": {pid: p['role'] for pid, p in self.players.items()}
                }
                self.broadcast(packet)
                # [DEBUG] 로그 간소화 (10초마다)
                if int(now) % 10 == 0:
                    print(f"[SERVER_DEBUG] Sending Roles: {len(self.players)} players")

    def _advance_phase(self):
        self.current_phase_idx = (self.current_phase_idx + 1) % len(self.phases)
        new_phase = self.phases[self.current_phase_idx]
        if new_phase == "DAWN": self.day_count += 1 # Day increases at DAWN
        self.state_timer = DEFAULT_PHASE_DURATIONS.get(new_phase, 30)
        # [개선] 페이즈 변경 시에도 역할 정보 포함
        self.broadcast({
            "type": "TIME_SYNC", 
            "phase_idx": self.current_phase_idx, 
            "timer": self.state_timer, 
            "day": self.day_count,
            "roles": {pid: p['role'] for pid, p in self.players.items()}
        })

    def handle_client(self, sock, pid):
        self.send_to(sock, {"type": "WELCOME", "my_id": pid})
        self.broadcast_player_list()
        try:
            while self.running:
                header = sock.recv(4)
                if not header: break
                msg_len = int.from_bytes(header, byteorder='big')
                data = b""
                while len(data) < msg_len:
                    packet = sock.recv(msg_len - len(data))
                    if not packet: break
                    data += packet
                if not data: break
                try:
                    payload = json.loads(data.decode('utf-8'))
                    self.process_packet(pid, payload)
                except json.JSONDecodeError as e:
                    print(f"[SERVER] JSON Error from {pid}: {e}")
                except Exception as e:
                    print(f"[SERVER] Packet Error from {pid}: {e}")
        except Exception as e:
            print(f"[SERVER] Client Handler Error: {e}")
        finally:
            self.remove_client(sock, pid)

    def remove_client(self, sock, pid):
        if sock in self.clients: del self.clients[sock]
        if pid in self.players: del self.players[pid]
        try: sock.close()
        except: pass
        self.broadcast_player_list()

    def process_packet(self, pid, data):
        ptype = data.get('type')
        if ptype == 'UPDATE_ROLE':
            target_id = data.get('id', pid) # Use provided ID or sender ID
            if target_id in self.players:
                self.players[target_id]['role'] = data.get('role'); self.broadcast_player_list()
        elif ptype == 'CHANGE_GROUP':
            tid = data.get('target_id')
            if tid in self.players:
                self.players[tid]['group'] = data.get('group'); self.broadcast_player_list()
        elif ptype == 'ADD_BOT':
            bid = self.next_id; self.next_id += 1
            new_role = 'RANDOM'
            
            # [수정] 게임 중 추가된 봇에게 즉시 직업 할당
            if self.game_started:
                import random
                available_roles = ["FARMER", "MINER", "FISHER", "POLICE", "MAFIA", "DOCTOR"]
                new_role = random.choice(available_roles)
                print(f"[SERVER] Late join Bot assigned: {new_role}")

            self.players[bid] = {
                'id': bid, 'name': data.get('name'), 'role': new_role,
                'group': data.get('group'), 'type': 'BOT', 'x': -1000, 'y': -1000, 'alive': True
            }
            self.broadcast_player_list()
            
            # 게임 중이면 역할 정보 업데이트를 위해 TIME_SYNC나 UPDATE_ROLE 유도 필요
            # 다음 TIME_SYNC에서 roles가 전송되므로 자동 해결됨
        elif ptype == 'REMOVE_BOT':
            target_id = data.get('target_id')
            if target_id in self.players and self.players[target_id].get('type') == 'BOT':
                del self.players[target_id]
                self.broadcast_player_list()
        elif ptype == 'START_GAME':
            # [수정] 권한 체크 완화 및 직업 할당 로깅 강화
            if not self.game_started:
                import random
                available_roles = ["FARMER", "MINER", "FISHER", "POLICE", "MAFIA", "DOCTOR"]
                
                print(f"\n--- [SERVER] GAME STARTING: Assigning Roles ---")
                for p in self.players.values():
                    if p['role'] == 'RANDOM' or p['role'] == 'CITIZEN':
                        p['role'] = random.choice(available_roles)
                    print(f" > Assigned: {p['name']} (ID:{p['id']}) -> {p['role']}")
                print(f"-----------------------------------------------\n")
                
                self.game_started = True
                self.last_tick = time.time()
                self.broadcast({"type": "GAME_START", "players": self.players})
        elif ptype == 'MOVE':
            mid = data.get('id', pid) # Can be bot ID sent by host
            if mid in self.players:
                self.players[mid].update({'x': data['x'], 'y': data['y'], 'facing': data.get('facing'), 'is_moving': data.get('is_moving')})
                self.broadcast(data, exclude_pid=pid)

    def broadcast_player_list(self):
        self.broadcast({"type": "PLAYER_LIST", "participants": list(self.players.values())})

    def send_to(self, sock, data):
        try:
            serialized = json.dumps(data).encode('utf-8')
            sock.sendall(len(serialized).to_bytes(4, 'big') + serialized)
        except Exception as e:
            print(f"[SERVER] Send Error: {e}")

    def broadcast(self, data, exclude_pid=None):
        try:
            serialized = json.dumps(data).encode('utf-8')
            packet = len(serialized).to_bytes(4, 'big') + serialized
            for sock, pid in self.clients.items():
                if pid != exclude_pid:
                    try: sock.sendall(packet)
                    except: pass
        except Exception as e:
            print(f"[SERVER] Broadcast Error: {e}")

if __name__ == "__main__":
    GameServer().start()