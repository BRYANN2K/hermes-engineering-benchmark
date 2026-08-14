import hashlib,hmac,json,unittest
from webhook import WebhookReceiver
def signed(secret,ts,body):return {'X-Webhook-Timestamp':str(ts),'X-Webhook-Signature':'v1='+hmac.new(secret,str(ts).encode()+b'.'+body,hashlib.sha256).hexdigest()}
class PublicTests(unittest.TestCase):
    def test_accept_and_replay(self):
        body=b'{"id":"e1","type":"push","data":{}}';r=WebhookReceiver(b'k',5,lambda:100)
        self.assertEqual(r.handle(signed(b'k',100,body),body),(202,{'accepted':'e1'}));self.assertEqual(r.handle(signed(b'k',100,body),body)[0],409)
    def test_bad_signature(self):
        r=WebhookReceiver(b'k',5,lambda:100);self.assertEqual(r.handle({'X-Webhook-Timestamp':'100','X-Webhook-Signature':'v1='+'0'*64},b'{}')[0],401)
if __name__=='__main__':unittest.main()
