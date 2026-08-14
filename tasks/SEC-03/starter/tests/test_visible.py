import json,tempfile,unittest
from pathlib import Path
from solution import run_check
class Visible(unittest.TestCase):
 def test_runs_check_with_environment(self):
  with tempfile.TemporaryDirectory() as td:
   w=Path(td);(w/"checks").mkdir();(w/"checks/probe.py").write_text('import json,os,sys;print(json.dumps({"args":sys.argv[1:],"v":os.environ.get("CHECK_VALUE")}))')
   out=run_check(w,{"script":"checks/probe.py","args":["hello"],"env":{"CHECK_VALUE":"ok"},"timeout_ms":1000});self.assertEqual(out["returncode"],0);self.assertEqual(json.loads(out["stdout"]),{"args":["hello"],"v":"ok"})
if __name__=="__main__":unittest.main()
