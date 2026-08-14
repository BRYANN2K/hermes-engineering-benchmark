import tempfile,unittest
from pathlib import Path
from solution import sign,verify_request
class Visible(unittest.TestCase):
 def test_accept_then_reject_replay(self):
  with tempfile.TemporaryDirectory() as td:
   secret=b"key";ts="100";nonce="abcdefghijklmnop";body=b"{}";h={"X-Webhook-Timestamp":ts,"X-Webhook-Nonce":nonce,"X-Webhook-Signature":sign(secret,ts,nonce,body)};p=Path(td)/"seen.json"
   self.assertTrue(verify_request(secret,h,body,100,p));self.assertFalse(verify_request(secret,h,body,100,p))
 def test_bad_signature_no_store(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"seen.json";h={"X-Webhook-Timestamp":"100","X-Webhook-Nonce":"abcdefghijklmnop","X-Webhook-Signature":"v1="+"0"*64};self.assertFalse(verify_request(b"key",h,b"{}",100,p));self.assertFalse(p.exists())
if __name__=="__main__":unittest.main()
