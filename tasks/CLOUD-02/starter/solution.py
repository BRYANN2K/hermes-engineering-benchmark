#!/usr/bin/env python3
import json,sys
from pathlib import Path
def validate_stack(stack): return []
if __name__=="__main__":print(json.dumps(validate_stack(json.loads(Path(sys.argv[1]).read_text()))))
