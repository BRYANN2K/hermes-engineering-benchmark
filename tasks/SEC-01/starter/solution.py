#!/usr/bin/env python3
import json,sys
from pathlib import Path
def install_bundle(root,entries,fail_after=None):
 root=Path(root);out=[]
 for e in entries:
  p=root/e["path"]
  if e["type"]=="dir":p.mkdir(parents=True,exist_ok=True)
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(e["content"])
  out.append(e["path"])
  if fail_after is not None and len(out)>=fail_after:raise RuntimeError("injected failure")
 return sorted(out)
if __name__=="__main__":print(json.dumps(install_bundle(sys.argv[1],json.loads(Path(sys.argv[2]).read_text()))))
