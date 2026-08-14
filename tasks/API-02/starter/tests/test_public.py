import unittest
from event_page import list_events
R=[{'id':'b','created_at':2,'data':{}},{'id':'a','created_at':2,'data':{'x':1}},{'id':'c','created_at':1,'data':[]}]
class PublicTests(unittest.TestCase):
    def test_order_and_cursor(self):
        s,p=list_events(R,{'limit':'2'},b'key');self.assertEqual((s,[x['id'] for x in p['items']]),(200,['a','b']))
        s,p2=list_events(R,{'cursor':p['next_cursor'],'limit':'2'},b'key');self.assertEqual([x['id'] for x in p2['items']],['c'])
    def test_bad_limit(self):self.assertEqual(list_events(R,{'limit':'01'},b'k'),(400,{'error':'invalid_query'}))
if __name__=='__main__':unittest.main()
