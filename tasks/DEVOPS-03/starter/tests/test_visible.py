import unittest
from solution import select_jobs
C={"jobs":[{"name":"lint","paths":["**/*.py"],"needs":[],"always":False},{"name":"unit","paths":["src/**"],"needs":["lint"],"always":False},{"name":"audit","paths":["never/**"],"needs":[],"always":True}]}
class Visible(unittest.TestCase):
 def test_dependencies_are_included(self): self.assertEqual(select_jobs(C,["src/app.py"]),["audit","lint","unit"])
 def test_always_on_empty(self): self.assertEqual(select_jobs(C,[]),["audit"])
if __name__=="__main__": unittest.main()
