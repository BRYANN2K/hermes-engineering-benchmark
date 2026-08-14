#!/usr/bin/env python3
import hashlib,hmac,json,sys
from pathlib import Path
def sign(secret,timestamp,nonce,body):return "v1="+hmac.new(secret,f"{timestamp}.{nonce}.".encode()+body,hashlib.sha256).hexdigest()
def verify_request(secret,headers,body,now,store_path,tolerance=300):
 # BUG: accepts valid signatures but has no freshness or replay protection.
 try: expected=sign(secret,headers["X-Webhook-Timestamp"],headers["X-Webhook-Nonce"],body)
 except Exception:return False
 return hmac.compare_digest(expected,headers["X-Webhook-Signature"])
