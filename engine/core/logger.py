import logging
import os
import threading
import queue
from datetime import datetime

class GameLogger:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GameLogger()
        return cls._instance

    def __init__(self):
        # [Optimization] Log Queue creation
        self.log_queue = queue.Queue()
        self.running = True
        
        # Logger Setup
        self.logger = logging.getLogger("PixelNight")
        self.logger.setLevel(logging.DEBUG)
        
        if not os.path.exists("logs"):
            os.makedirs("logs")
            
        filename = f"logs/game_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(filename, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # [Optimization] Background thread for file writing
        self.worker_thread = threading.Thread(target=self._process_logs, daemon=True)
        self.worker_thread.start()

    def _process_logs(self):
        """Write queued logs to file in background"""
        while self.running or not self.log_queue.empty():
            try:
                # Wait 0.1s for log
                record = self.log_queue.get(timeout=0.1)
                level, category, message = record
                
                full_msg = f"[{category}] {message}"
                if level == 'INFO': self.logger.info(full_msg)
                elif level == 'ERROR': self.logger.error(full_msg)
                elif level == 'DEBUG': self.logger.debug(full_msg)
                elif level == 'WARNING': self.logger.warning(full_msg)
                
                self.log_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Logging Error: {e}")

    def log(self, level, category, message):
        # [Optimization] Non-blocking put
        self.log_queue.put((level, category, message))

    def info(self, category, message):
        self.log('INFO', category, message)

    def error(self, category, message):
        self.log('ERROR', category, message)
        
    def debug(self, category, message):
        self.log('DEBUG', category, message)

    def shutdown(self):
        self.running = False
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)
