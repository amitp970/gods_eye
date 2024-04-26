import threading

class ThreadSafeSet:
    def __init__(self):
        self.set = set()
        self.lock = threading.Lock()
    
    def add(self, item):
        with self.lock:
            self.set.add(item)
    
    def remove(self, item):
        with self.lock:
            self.set.remove(item)
    
    def contains(self, item):
        return item in self.set
    
    def get_all(self):
        return self.set.copy()
    
    def is_empty(self):
        return not self.set
    
    def __contains__(self, item):
        return self.contains(item)
