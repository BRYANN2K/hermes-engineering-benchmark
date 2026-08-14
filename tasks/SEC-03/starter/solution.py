#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
def run_check(workspace,spec):
 # BUG: shell interpolation, inherited environment, no path validation.
 cmd=" ".join([sys.executable,str(Path(workspace)/spec["script"]),*spec["args"]])
 p=subprocess.run(cmd,shell=True,cwd=workspace,text=True,capture_output=True,timeout=spec["timeout_ms"]/1000)
 return {"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr,"timed_out":False}
if __name__=="__main__":print(json.dumps(run_check(sys.argv[1],json.loads(Path(sys.argv[2]).read_text()))))
