import unittest
from solution import reconstruct_outages
def E(t,p,s):return {"timestamp":t,"probe":p,"status":s}
class Visible(unittest.TestCase):
 def test_quorum_outage(self):
  e=[E(1,"a","up"),E(1,"b","up"),E(2,"a","down"),E(2,"b","down"),E(3,"a","up"),E(3,"b","up")]
  self.assertEqual(reconstruct_outages(e,2,10),[{"started_at":2,"ended_at":3}])
 def test_unknown_to_down_does_not_open(self):self.assertEqual(reconstruct_outages([E(1,"a","down"),E(1,"b","down")],2,10),[])
if __name__=="__main__":unittest.main()
