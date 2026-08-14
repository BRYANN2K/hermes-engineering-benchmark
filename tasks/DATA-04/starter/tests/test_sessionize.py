import json,tempfile,unittest
from pathlib import Path
from sessionize import sessionize
class T(unittest.TestCase):
 def test_orders_and_groups(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);i=d/'in';o=d/'out';events=[{'event_id':'2','user_id':'u','timestamp':'2026-01-01T00:10:00Z','path':'/b'},{'event_id':'1','user_id':'u','timestamp':'2026-01-01T00:00:00Z','path':'/a'},{'event_id':'3','user_id':'u','timestamp':'2026-01-01T01:00:01Z','path':'/c'}];i.write_text('\n'.join(map(json.dumps,events)));self.assertEqual(sessionize(i,o),{'events':3,'sessions':2});rows=[json.loads(x) for x in o.read_text().splitlines()];self.assertEqual(rows[0]['unique_paths'],['/a','/b']);self.assertEqual(rows[0]['duration_seconds'],600)
