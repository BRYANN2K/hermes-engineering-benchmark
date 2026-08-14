import json,unittest
from document_api import DocumentAPI
class PublicTests(unittest.TestCase):
    def test_create_get_update(self):
        api=DocumentAPI();body=b'{"content":"one"}'
        status,h,p=api.request('PUT','/documents/a',{'Content-Type':'application/json','If-None-Match':'*'},body)
        self.assertEqual((status,h['ETag']), (201,'"1"'))
        self.assertEqual(api.request('GET','/documents/a',{},b'')[0],200)
        self.assertEqual(api.request('PUT','/documents/a',{'content-type':'application/json','if-match':'"1"'},b'{"content":"two"}')[0],200)
    def test_invalid_json_does_not_create(self):
        api=DocumentAPI();self.assertEqual(api.request('PUT','/documents/a',{'Content-Type':'application/json','If-None-Match':'*'},b'{')[0],400)
        self.assertEqual(api.request('GET','/documents/a',{},b'')[0],404)
if __name__=='__main__':unittest.main()
