import json,tempfile,threading,unittest,urllib.request
from pathlib import Path
from app import make_server
class T(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.s=make_server(Path(self.t.name)/'p.db');threading.Thread(target=self.s.serve_forever,daemon=True).start();self.base=f'http://127.0.0.1:{self.s.server_port}'
 def tearDown(self):self.s.shutdown();self.s.server_close();self.t.cleanup()
 def req(self,path,body=None):
  q=urllib.request.Request(self.base+path,data=None if body is None else json.dumps(body).encode(),method='GET' if body is None else 'POST',headers={'Content-Type':'application/json','X-Voter-ID':'v1'});r=urllib.request.urlopen(q);return r.status,json.load(r)
 def test_first_vote_and_read(self):
  status,out=self.req('/api/vote',{'choiceId':'alpha'});self.assertEqual(status,201);self.assertEqual(out['totalVotes'],1);self.assertEqual(self.req('/api/poll')[1]['choices'][0]['votes'],1)
 def test_page(self):self.assertIn(b'workshop',urllib.request.urlopen(self.base+'/').read())
