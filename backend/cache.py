"""A small in-process TTL cache.

Not distributed and not persisted across restarts — the goal is only to avoid
re-hitting bioRxiv/arXiv/PubMed on every request within a short window, not to
build a caching layer. A plain dict plus expiry timestamps is enough for that.
"""

import time


class TTLCache:
    def __init__(self, ttl_seconds):
        self.ttl = ttl_seconds
        self._store = {}  # key -> (expires_at, value)

    def get(self, key):
        hit = self._store.get(key)
        if hit is None:
            return None
        expires_at, value = hit
        if time.time() >= expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key, value, ttl=None):
        expires_at = time.time() + (self.ttl if ttl is None else ttl)
        self._store[key] = (expires_at, value)

    def clear(self):
        self._store.clear()

    def __len__(self):
        return len(self._store)

    def __contains__(self, key):
        return self.get(key) is not None
