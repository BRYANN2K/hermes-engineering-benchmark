#!/usr/bin/env python3
import json,sys
from pathlib import Path
def reconcile(regions,tombstones):
 # BUG: copies the first observed object and ignores versions/deletes.
 first={}
 for records in regions.values():
  for x in records:first.setdefault(x["key"],x)
 return [{"action":"put","region":r,"key":k,"version":x["version"],"content":x["content"]} for k,x in first.items() for r,records in regions.items() if not any(y==x for y in records)]
if __name__=="__main__":print(json.dumps(reconcile(json.loads(Path(sys.argv[1]).read_text()),json.loads(Path(sys.argv[2]).read_text()))))
