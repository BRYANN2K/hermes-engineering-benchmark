#!/usr/bin/env python3
import json, sys
from pathlib import PurePath, Path
def select_jobs(config,changed_paths):
 return sorted(j["name"] for j in config["jobs"] if j.get("always") or any(PurePath(p).match(g) for p in changed_paths for g in j["paths"]))
def main(): print(json.dumps(select_jobs(json.loads(Path(sys.argv[1]).read_text()),json.loads(Path(sys.argv[2]).read_text()))))
if __name__=="__main__": main()
