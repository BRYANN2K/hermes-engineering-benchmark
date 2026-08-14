import unittest
from config_merge import merge_config

class PublicTests(unittest.TestCase):
    def test_nested_merge_preserves_siblings(self):
        base = {'db': {'host': 'a', 'port': 1}, 'debug': False}
        self.assertEqual(merge_config(base, {'db': {'port': 2}}), {'db': {'host': 'a', 'port': 2}, 'debug': False})
    def test_delete_marker_removes_nested_key(self):
        self.assertEqual(merge_config({'a': {'x': 1, 'y': 2}}, {'a': {'x': '__DELETE__'}}), {'a': {'y': 2}})

if __name__ == '__main__': unittest.main()
