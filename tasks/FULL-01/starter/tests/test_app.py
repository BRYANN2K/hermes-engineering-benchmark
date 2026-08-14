import json,tempfile,threading,unittest,urllib.request
from pathlib import Path
from app import make_server
class T(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.db=str(Path(self.tmp.name)/'x.db');self.s=make_server(self.db);threading.Thread(target=self.s.serve_forever,daemon=True).start();self.url=f'http://127.0.0.1:{self.s.server_port}'
 def tearDown(self):self.s.shutdown();self.s.server_close();self.tmp.cleanup()
 def req(self,path,method='GET',body=None):
  data=None if body is None else json.dumps(body).encode();r=urllib.request.urlopen(urllib.request.Request(self.url+path,data=data,method=method,headers={'Content-Type':'application/json'}));return r.status,json.load(r)
 def test_create_and_list(self):
  status,task=self.req('/api/tasks','POST',{'title':' Ship it '});self.assertEqual(status,201);self.assertEqual(task['title'],'Ship it');status,out=self.req('/api/tasks');self.assertEqual(out['tasks'],[task])
 def test_page(self):self.assertIn(b'Tasks',urllib.request.urlopen(self.url+'/').read())
