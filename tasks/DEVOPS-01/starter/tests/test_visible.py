import unittest
from solution import build_plan
class PlannerTests(unittest.TestCase):
 def test_dependency_order_and_ready_tie_break(self):
  manifest={"services":[{"name":"api","depends_on":["z-db"]},{"name":"worker","depends_on":["z-db"]},{"name":"z-db","depends_on":[]}]}
  self.assertEqual(build_plan(manifest),["z-db","api","worker"])
 def test_empty_manifest(self): self.assertEqual(build_plan({"services":[]}),[])
if __name__=="__main__": unittest.main()
