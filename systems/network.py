from engine.network.client import NetworkClient
from settings import NETWORK_PORT

class NetworkManager(NetworkClient):
    def __init__(self, ip="127.0.0.1", port=NETWORK_PORT):
        super().__init__(ip, port)

    # --- Multiplayer Helpers (Game Specific) ---
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

    def send_stats(self, hp, max_hp, ap, max_ap, coins, emotion, action_text, eid=None):
        data = {
            "type": "UPDATE_STATS",
            "hp": hp, "max_hp": max_hp,
            "ap": ap, "max_ap": max_ap,
            "coins": coins,
            "emotion": emotion,
            "action": action_text
        }
        if eid: data['id'] = eid
        self.send(data)

    def send_chat(self, message):
        """임시: 채팅 메시지를 서버로 전송합니다."""
        self.send({"type": "CHAT", "message": message})

    def send_profile(self, name, custom_data):
        self.send({"type": "UPDATE_PROFILE", "name": name, "custom": custom_data})

    def send_death(self, victim_id, reason):
        self.send({"type": "ENTITY_DIED", "victim": victim_id, "reason": reason})
