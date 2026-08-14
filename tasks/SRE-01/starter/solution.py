#!/usr/bin/env python3
import json,sys
from pathlib import Path
def detect_incidents(samples,threshold):
 # BUG: opens on first breach and resolves on first healthy sample.
 out=[];active=None
 for s in samples:
  if s["value"] is not None and s["value"]>threshold and active is None:active={"opened_at":s["timestamp"],"resolved_at":None,"peak":s["value"]}
  elif active is not None and s["value"] is not None:
   active["peak"]=max(active["peak"],s["value"])
   if s["value"]<=threshold:active["resolved_at"]=s["timestamp"];out.append(active);active=None
 if active:out.append(active)
 return out
if __name__=="__main__":print(json.dumps(detect_incidents(json.loads(Path(sys.argv[1]).read_text()),float(sys.argv[2]))))
