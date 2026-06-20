import time

class RedisSimulationCache:
    def __init__(self, ttl_seconds=30):
        self._cache = {}
        self.ttl_seconds = ttl_seconds

    def get(self, key):
        """Checks the memory cache cluster for an existing triage verdict."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp <= self.ttl_seconds:
                return value
            del self._cache[key]
        return None

    def set(self, key, value):
        """Caches a secure triage result in memory."""
        self._cache[key] = (value, time.time())