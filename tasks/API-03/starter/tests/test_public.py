import tempfile,unittest
from pathlib import Path
from inventory import *
class PublicTests(unittest.TestCase):
    def test_reserve_replay_and_conflict(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[];s=InventoryStore(Path(d)/'db.sqlite',lambda:calls.append(1) or 10.0);s.add_stock('x',5)
            created,r=s.reserve('x',2,'k');self.assertTrue(created);self.assertEqual(s.stock('x'),3)
            self.assertFalse(s.reserve('x',2,'k')[0]);self.assertEqual(len(calls),1)
            with self.assertRaises(ReservationConflict):s.reserve('x',1,'k')
            s.close()
    def test_insufficient_does_not_record(self):
        with tempfile.TemporaryDirectory() as d:
            s=InventoryStore(Path(d)/'d',lambda:1)
            with self.assertRaises(InsufficientStock):s.reserve('x',1,'k')
            self.assertEqual(s.reservations(),[]);s.close()
if __name__=='__main__':unittest.main()
