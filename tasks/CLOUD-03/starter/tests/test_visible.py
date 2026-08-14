import unittest
from solution import reconcile
class Visible(unittest.TestCase):
 def test_newest_object_replicates(self):
  regions={"a":[{"key":"x","version":1,"content":"old"}],"b":[{"key":"x","version":2,"content":"new"}]}
  self.assertEqual(reconcile(regions,[]),[{"action":"put","region":"a","key":"x","version":2,"content":"new"}])
 def test_equal_tombstone_deletes(self):
  self.assertEqual(reconcile({"a":[{"key":"x","version":2,"content":"v"}],"b":[]},[{"key":"x","version":2}]),[{"action":"delete","region":"a","key":"x","version":2}])
if __name__=="__main__":unittest.main()
