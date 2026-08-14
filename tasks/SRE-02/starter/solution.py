#!/usr/bin/env python3
import json,sys
from pathlib import Path
def burn_alert(samples,slo,short_window,long_window,short_burn,long_burn): return None
if __name__=="__main__":
 x=json.loads(Path(sys.argv[1]).read_text());print(json.dumps(burn_alert(**x)))
