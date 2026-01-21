import socket
import threading
import json
import queue
from settings import NETWORK_PORT

class NetworkManager:
    def __init__(self, ip="127.0.0.1", port=NETWORK_PORT):
        self.ip = ip
        self.port = port
        self.client = None # 초기화 시점에는 생성 안 함
        self.connected = False
        self.msg_queue = queue.Queue()
        self.my_id = -1 

    def connect(self):
        # 기존 연결이 있다면 해제
        if self.client:
            try: self.client.close()
            except: pass
            
        # 항상 새로운 소켓 생성
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            self.client.connect((self.ip, self.port))
            self.connected = True
            print(f"[NET] Connected to {self.ip}:{self.port}")
            thread = threading.Thread(target=self.receive_loop, daemon=True)
            thread.start()
            return True
        except Exception as e:
            print(f"[NET] Connection Failed: {e}")
            self.connected = False
            return False

    def receive_loop(self):
        while self.connected:
            try:
                header = self.client.recv(4)
                if not header: break
                msg_len = int.from_bytes(header, byteorder='big')
                data = b""
                while len(data) < msg_len:
                    packet = self.client.recv(msg_len - len(data))
                    if not packet: break
                    data += packet
                if not data: break
                try:
                    payload = json.loads(data.decode('utf-8'))
                    # [DEBUG] 패킷 수신 확인
                    if payload.get('type') in ['GAME_START', 'TIME_SYNC']:
                        # 너무 많은 로그 방지를 위해 TIME_SYNC는 간헐적으로만 출력하거나 생략 가능
                        if payload.get('type') == 'GAME_START':
                            print(f"[NET_DEBUG] Packet Received: {payload['type']}")
                            
                    self.msg_queue.put(payload)
                except json.JSONDecodeError as e:
                    print(f"[NET] JSON Error: {e}")
            except Exception as e:
                print(f"[NET] Receive Error: {e}")
                self.connected = False
                break

    def send(self, data):
        if not self.connected: return
        try:
            if self.my_id != -1 and 'id' not in data:
                data['id'] = self.my_id
            serialized = json.dumps(data).encode('utf-8')
            self.client.sendall(len(serialized).to_bytes(4, 'big') + serialized)
        except Exception as e:
            print(f"[NET] Send Error: {e}")

    def get_events(self):
        events = []
        while not self.msg_queue.empty():
            events.append(self.msg_queue.get())
        return events

    # --- Multiplayer Helpers ---
    def send_role_change(self, new_role):
        self.send({"type": "UPDATE_ROLE", "role": new_role})

    def send_add_bot(self, name, group):
        self.send({"type": "ADD_BOT", "name": name, "group": group})

    def send_change_group(self, target_id, new_group):
        self.send({"type": "CHANGE_GROUP", "target_id": target_id, "group": new_group})

    def send_remove_bot(self, target_id):
        self.send({"type": "REMOVE_BOT", "target_id": target_id})

    def send_start_game(self):
        self.send({"type": "START_GAME"})

    def send_move(self, x, y, is_moving, facing_dir):
        self.send({"type": "MOVE", "x": x, "y": y, "is_moving": is_moving, "facing": facing_dir})

    def disconnect(self):
        self.connected = False
        if self.client:
            try: self.client.close()
            except: pass
        self.client = None
