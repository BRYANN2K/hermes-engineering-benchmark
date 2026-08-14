import sqlite3,tempfile,unittest
from pathlib import Path
from inventory import apply_batch
class T(unittest.TestCase):
 def test_apply_and_replay(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);db=d/'x';c=sqlite3.connect(db);c.execute('create table inventory(sku TEXT PRIMARY KEY,quantity INTEGER NOT NULL CHECK(quantity>=0))');c.execute('insert into inventory values("a",5)');c.commit();c.close();p=d/'b';p.write_text('batch_id,movement_id,sku,delta\nb1,m1,a,-2\nb1,m2,b,3\n');self.assertEqual(apply_batch(db,p),{'batch_id':'b1','applied':2,'replayed':False,'balances':{'a':3,'b':3}});self.assertTrue(apply_batch(db,p)['replayed'])
