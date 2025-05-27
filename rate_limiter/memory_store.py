import time
from threading import Lock


class InMemoryStore:
    def __init__(self):
        self.data = {}
        self.lock = Lock()

    def get_state(self, key: str):
        with self.lock:
            return self.data.get(key, {"tokens": None, "last_refill": time.time()})

    def set_state(self, key: str, tokens: float, last_refill: float):
        with self.lock:
            self.data[key] = {"tokens": tokens, "last_refill": last_refill}