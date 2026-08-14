import csv,sqlite3,tempfile,unittest
from pathlib import Path
from pipeline import ingest
class T(unittest.TestCase):
 def test_ingest_and_replay(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);p=d/'in.csv';p.write_text('event_id,account_id,occurred_at,amount_cents\ne1,a1,2026-01-02T03:04:05Z,120\ne2,,2026-01-02T03:04:05Z,5\n');r=ingest(p,d/'x.db',d/'bad.csv');self.assertEqual(r,{'read':2,'inserted':1,'duplicates':0,'rejected':1});self.assertEqual(ingest(p,d/'x.db',d/'bad.csv')['duplicates'],1);self.assertEqual(sqlite3.connect(d/'x.db').execute('select sum(amount_cents) from ledger_events').fetchone()[0],120);self.assertEqual(list(csv.reader(open(d/'bad.csv'))),[['line','error'],['3','account_id']])
