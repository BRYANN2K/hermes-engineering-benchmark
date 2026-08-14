import json,tempfile,threading,unittest,urllib.request
from pathlib import Path
from app import make_server
class T(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.s=make_server(Path(self.t.name)/'x');threading.Thread(target=self.s.serve_forever,daemon=True).start();self.b=f'http://127.0.0.1:{self.s.server_port}'
 def tearDown(self):self.s.shutdown();self.s.server_close();self.t.cleanup()
 def req(self,path,method='GET',body=None):q=urllib.request.Request(self.b+path,data=None if body is None else json.dumps(body).encode(),method=method,headers={'Content-Type':'application/json'});r=urllib.request.urlopen(q);return r.status,json.load(r)
 def test_create_and_list(self):
  body={'requestId':'r1','email':'a@b','subject':' Help ','priority':'normal'};st,t=self.req('/api/tickets','POST',body);self.assertEqual(st,201);self.assertEqual(t['subject'],'Help');self.assertEqual(self.req('/api/tickets?status=open')[1]['tickets'],[t])
 def test_page(self):self.assertIn(b'Contact support',urllib.request.urlopen(self.b+'/').read())
