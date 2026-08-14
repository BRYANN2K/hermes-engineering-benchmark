import unittest
from solution import validate_stack
class Visible(unittest.TestCase):
 def test_db_and_admin_violations(self):
  s={"networks":[{"id":"pub","public":True,"ingress":[{"protocol":"tcp","port":22,"cidr":"0.0.0.0/0"}]}],"instances":[{"id":"db1","network":"pub","role":"db","encrypted":False}]}
  self.assertEqual(validate_stack(s),[{"code":"DB_PUBLIC_NETWORK","resource":"db1"},{"code":"DB_UNENCRYPTED","resource":"db1"},{"code":"WORLD_ADMIN_PORT","resource":"pub"}])
 def test_compliant(self):
  s={"networks":[{"id":"pub","public":True,"ingress":[{"protocol":"tcp","port":443,"cidr":"0.0.0.0/0"}]}],"instances":[{"id":"web","network":"pub","role":"web","encrypted":True}]};self.assertEqual(validate_stack(s),[])
if __name__=="__main__":unittest.main()
