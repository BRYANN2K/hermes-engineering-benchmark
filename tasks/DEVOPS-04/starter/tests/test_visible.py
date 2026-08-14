import json,tempfile,unittest
from pathlib import Path
from solution import run_migrations
class Visible(unittest.TestCase):
 def test_applies_and_does_not_reapply(self):
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);m=d/"m";m.mkdir();(m/"001-init.json").write_text('{"version":1,"set":{"a":1},"delete":[]}')
   self.assertEqual(run_migrations(d/"state.json",m),[1]);self.assertEqual(run_migrations(d/"state.json",m),[]);self.assertEqual(json.loads((d/"state.json").read_text())["data"],{"a":1})
if __name__=="__main__":unittest.main()
