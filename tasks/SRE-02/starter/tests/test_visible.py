import unittest
from solution import burn_alert
def S(t,g,n):return {"timestamp":t,"good":g,"total":n}
class Visible(unittest.TestCase):
 def test_alerts(self):
  x=[S(1,99,100),S(2,99,100),S(3,90,100)]
  out=burn_alert(x,.99,2,3,5,3);self.assertEqual(out["alert_at"],3);self.assertAlmostEqual(out["short_burn"],5.5);self.assertAlmostEqual(out["long_burn"],4)
 def test_no_traffic_no_alert(self):self.assertIsNone(burn_alert([S(1,0,0)],.99,1,2,1,1))
if __name__=="__main__":unittest.main()
