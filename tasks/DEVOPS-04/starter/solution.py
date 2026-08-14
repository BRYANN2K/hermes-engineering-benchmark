#!/usr/bin/env python3
import json,sys
from pathlib import Path
def run_migrations(db_path,migrations_dir,fail_after=None):
 db=Path(db_path);state=json.loads(db.read_text()) if db.exists() else {"data":{},"applied":[]};new=[]
 for p in sorted(Path(migrations_dir).glob("*.json")):
  m=json.loads(p.read_text());state["data"].update(m["set"]);[state["data"].pop(k,None) for k in m["delete"]];state["applied"].append({"version":m["version"],"sha256":""});new.append(m["version"])
 db.write_text(json.dumps(state));return new
if __name__=="__main__":print(json.dumps(run_migrations(sys.argv[1],sys.argv[2])))
