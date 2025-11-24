from collections import defaultdict
from threading import Lock

class EventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.lock = Lock()

    def subscribe(self, event_type, callback):
        with self.lock:
            self.subscribers[event_type].append(callback)

    def publish(self, event_type, data):
        with self.lock:
            for callback in self.subscribers[event_type]:
                try:
                    callback(data)
                except Exception:
                    # Safe-guard subscriber exceptions
                    pass

# Singleton instance
event_bus = EventBus()
