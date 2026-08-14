#!/usr/bin/env python3
import json,sys
from pathlib import Path
def plan_changes(current,desired):
 c={x["id"]:x for x in current["resources"]};d={x["id"]:x for x in desired["resources"]};out=[]
 out += [{"action":"delete","id":x} for x in sorted(c.keys()-d.keys())]
 out += [{"action":"create","id":x} for x in sorted(d.keys()-c.keys())]
 out += [{"action":"update","id":x} for x in sorted(c.keys()&d.keys()) if c[x]["properties"]!=d[x]["properties"]]
 return out
if __name__=="__main__":print(json.dumps(plan_changes(json.loads(Path(sys.argv[1]).read_text()),json.loads(Path(sys.argv[2]).read_text()))))
