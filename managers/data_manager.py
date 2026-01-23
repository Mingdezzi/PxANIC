import json
import os
from systems.logger import GameLogger

class DataManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DataManager()
        return cls._instance

    def __init__(self):
        if DataManager._instance is not None:
            raise Exception("This class is a singleton!")
        
        self.logger = GameLogger.get_instance()
        self.profile = {}
        
        self.load_all()

    def load_all(self):
        self.load_items()
        self.load_tiles()
        self.load_roles()
        self.load_user_profile()

    def load_user_profile(self):
        try:
            if os.path.exists('profile.json'):
                with open('profile.json', 'r', encoding='utf-8') as f:
                    self.profile = json.load(f)
                self.logger.info("DATA", "Loaded user profile.")
            else:
                self.logger.warning("DATA", "No profile found. Creating new.")
                self.profile = {"custom": {}, "name": "Player 1"}
                self.save_user_profile()
        except Exception as e:
            self.logger.error("DATA", f"Failed to load profile: {e}")
            self.profile = {"custom": {}, "name": "Player 1"}

    def save_user_profile(self):
        try:
            with open('profile.json', 'w', encoding='utf-8') as f:
                json.dump(self.profile, f, indent=4)
            self.logger.info("DATA", "Saved user profile.")
        except Exception as e:
            self.logger.error("DATA", f"Failed to save profile: {e}")

    def load_items(self):
        try:
            with open('data/items.json', 'r', encoding='utf-8') as f:
                self.items = json.load(f)
            self.logger.info("DATA", f"Loaded {len(self.items)} items.")
        except Exception as e:
            self.logger.error("DATA", f"Failed to load items: {e}")

    def load_tiles(self):
        try:
            with open('data/tiles.json', 'r', encoding='utf-8') as f:
                raw_tiles = json.load(f)
                # JSON 키는 문자열이므로 int로 변환
                self.tiles = {int(k): v for k, v in raw_tiles.items()}
                
                # 색상값 리스트 -> 튜플 변환 (Pygame 호환)
                for tid, data in self.tiles.items():
                    if 'color' in data:
                        data['color'] = tuple(data['color'])
                        
            self.logger.info("DATA", f"Loaded {len(self.tiles)} tiles.")
        except Exception as e:
            self.logger.error("DATA", f"Failed to load tiles: {e}")

    def load_roles(self):
        try:
            with open('data/roles.json', 'r', encoding='utf-8') as f:
                self.roles = json.load(f)
            self.logger.info("DATA", f"Loaded {len(self.roles)} roles.")
        except Exception as e:
            self.logger.error("DATA", f"Failed to load roles: {e}")

    def get_item(self, key):
        return self.items.get(key)

    def get_tile(self, tid):
        return self.tiles.get(tid)

    def get_role(self, role_name):
        return self.roles.get(role_name)
