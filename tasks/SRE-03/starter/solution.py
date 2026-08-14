#!/usr/bin/env python3
import json,sys
from pathlib import Path
def reconstruct_outages(events,quorum,stale_after):
 out=[];open_=None
 for e in events:
  if e["status"]=="down" and open_ is None:open_={"started_at":e["timestamp"],"ended_at":None}
  elif e["status"]=="up" and open_ is not None:open_["ended_at"]=e["timestamp"];out.append(open_);open_=None
 if open_:out.append(open_)
 return out
if __name__=="__main__":print(json.dumps(reconstruct_outages(json.loads(Path(sys.argv[1]).read_text()),int(sys.argv[2]),int(sys.argv[3]))))
