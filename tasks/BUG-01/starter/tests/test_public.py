import unittest
from ttl_cache import TTLCache

class Clock:
    def __init__(self): self.now = 10.0
    def __call__(self): return self.now

class PublicTests(unittest.TestCase):
    def test_expired_entries_are_not_counted(self):
        clock = Clock(); cache = TTLCache(2, clock)
        cache.set('old', 1, 1); cache.set('live', 2, 20)
        clock.now = 12
        self.assertEqual(len(cache), 1)
        self.assertEqual(cache.keys(), ['live'])
    def test_reads_drive_lru_eviction(self):
        clock = Clock(); cache = TTLCache(2, clock)
        cache.set('a', 1, 20); cache.set('b', 2, 20)
        self.assertEqual(cache.get('a'), 1)
        cache.set('c', 3, 20)
        self.assertEqual(cache.keys(), ['a', 'c'])

if __name__ == '__main__': unittest.main()
