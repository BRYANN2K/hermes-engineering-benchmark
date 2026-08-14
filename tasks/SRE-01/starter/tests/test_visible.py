import unittest
from solution import detect_incidents
def S(t,v):return {"timestamp":t,"value":v}
class Visible(unittest.TestCase):
 def test_open_and_resolve_hysteresis(self):self.assertEqual(detect_incidents([S(1,11),S(2,12),S(3,13),S(4,8),S(5,7)],10),[{"opened_at":3,"resolved_at":5,"peak":13}])
 def test_short_spike_ignored(self):self.assertEqual(detect_incidents([S(1,11),S(2,12),S(3,9)],10),[])
if __name__=="__main__":unittest.main()
