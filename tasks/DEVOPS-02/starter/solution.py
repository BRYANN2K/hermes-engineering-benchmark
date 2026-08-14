#!/usr/bin/env python3
import json, sys
from pathlib import Path

def publish_release(root,version,files,fail_after=None):
 root=Path(root); dest=root/"releases"/version; dest.mkdir(parents=True,exist_ok=True)
 for i,(name,content) in enumerate(files.items(),1):
  p=dest/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content)
  if fail_after is not None and i>=fail_after: raise RuntimeError("injected failure")
 (root/"current").write_text(version+"\n")
 return dest

def main():
 files=json.loads(Path(sys.argv[3]).read_text()); print(publish_release(sys.argv[1],sys.argv[2],files))
if __name__=="__main__": main()
