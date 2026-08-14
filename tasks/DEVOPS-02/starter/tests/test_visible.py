import tempfile, unittest
from pathlib import Path
from solution import publish_release
class Visible(unittest.TestCase):
 def test_publish(self):
  with tempfile.TemporaryDirectory() as td:
   p=publish_release(td,"v1",{"app.txt":"hello","conf/x":"ok"})
   self.assertEqual((p/"app.txt").read_text(),"hello"); self.assertEqual((Path(td)/"current").read_text(),"v1\n")
 def test_reject_parent_path(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(ValueError): publish_release(td,"v1",{"../escape":"x"})
if __name__=="__main__": unittest.main()
