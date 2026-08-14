import unittest
from batch_plan import build_batches
class PublicTests(unittest.TestCase):
    def test_dependencies_use_later_batch(self):
        tasks=[{'id':'a'},{'id':'b','after':['a']},{'id':'c'}]
        self.assertEqual(build_batches(tasks,2),[['a','c'],['b']])
    def test_groups_do_not_share_batch(self):
        tasks=[{'id':'a','group':'db'},{'id':'b','group':'db'},{'id':'c'}]
        self.assertEqual(build_batches(tasks,3),[['a','c'],['b']])
if __name__=='__main__':unittest.main()
