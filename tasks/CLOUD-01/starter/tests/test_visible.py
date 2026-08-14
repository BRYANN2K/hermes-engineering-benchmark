import unittest
from solution import plan_changes
def R(i,k="service",deps=(),**p):return {"id":i,"kind":k,"depends_on":list(deps),"properties":p}
class Visible(unittest.TestCase):
 def test_create_dependency_order(self):self.assertEqual(plan_changes({"resources":[]},{"resources":[R("app",deps=("net",),runtime="py"),R("net","network",cidr="10.0.0.0/24")]}),[{"action":"create","id":"net"},{"action":"create","id":"app"}])
 def test_mutable_update(self):self.assertEqual(plan_changes({"resources":[R("app",runtime="py",size=1)]},{"resources":[R("app",runtime="py",size=2)]}),[{"action":"update","id":"app"}])
if __name__=="__main__":unittest.main()
