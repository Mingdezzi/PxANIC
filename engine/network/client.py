import socket
import threading
import json
import queue

class NetworkClient:
    def __init__(self, ip="127.0.0.1", port=5000):
        self.ip = ip
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.msg_queue = queue.Queue()
        self.my_id = -1 

    def connect(self):
        try:
            self.client.connect((self.ip, self.port))
            self.connected = True
            print(f"[NET] Connected to {self.ip}:{self.port}")
            thread = threading.Thread(target=self.receive_loop, daemon=True)
            thread.start()
            return True
        except Exception as e:
            print(f"[NET] Connection Failed: {e}")
            return False

    def recv_safe(self, size):
        data = b""
        while len(data) < size:
            try:
                packet = self.client.recv(size - len(data))
                if not packet:
                    return None
                data += packet
            except socket.error as e:
                print(f"[NET] Socket Error: {e}")
                return None
        return data

    def receive_loop(self):
        while self.connected:
            try:
                # 1. Read Header (4 bytes)
                header = self.recv_safe(4)
                if not header:
                    print("[NET] Disconnected (No Header)")
                    break
                
                msg_len = int.from_bytes(header, byteorder='big')
                
                # 2. Read Payload
                data = self.recv_safe(msg_len)
                if not data:
                    print("[NET] Disconnected (No Body)")
                    break
                
                try:
                    payload = json.loads(data.decode('utf-8'))
                    self.msg_queue.put(payload)
                except json.JSONDecodeError as e:
                    print(f"[NET] JSON Error: {e}")
            except Exception as e:
                print(f"[NET] Receive Loop Error: {e}")
                self.connected = False
                break
        self.connected = False
        print("[NET] Receiver thread ended.")

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

    def disconnect(self):
        self.connected = False
        try:
            self.client.close()
        except:
            pass
