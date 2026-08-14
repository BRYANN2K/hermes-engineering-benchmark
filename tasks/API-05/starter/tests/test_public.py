import json,unittest
from profile_service import ProfileService
P={'display_name':'A','email':'a@example.com','notifications':True}
class PublicTests(unittest.TestCase):
    def test_seed_get_patch(self):
        s=ProfileService();s.seed('alice',P)
        status,h,b=s.request('GET','/profiles/alice',{},b'');self.assertEqual((status,h['ETag']),(200,'"v1"'))
        status,h,b=s.request('PATCH','/profiles/alice',{'Content-Type':'application/merge-patch+json','If-Match':'"v1"'},b'{"display_name":"Alice"}')
        self.assertEqual((status,h['ETag'],json.loads(b)['version']),(200,'"v2"',2))
    def test_invalid_patch_does_not_mutate(self):
        s=ProfileService();s.seed('alice',P);self.assertEqual(s.request('PATCH','/profiles/alice',{'Content-Type':'application/merge-patch+json','If-Match':'"v1"'},b'{"email":null}')[0],422)
        self.assertEqual(json.loads(s.request('GET','/profiles/alice',{},b'')[2])['version'],1)
if __name__=='__main__':unittest.main()
