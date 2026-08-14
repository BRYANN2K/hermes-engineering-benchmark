class RateLimiter:
    def __init__(self, limit, window, clock):
        self.limit=limit; self.window=window; self.clock=clock
    def allow(self, key):
        raise NotImplementedError
    def reset(self, key): return False
    def snapshot(self): return {}
