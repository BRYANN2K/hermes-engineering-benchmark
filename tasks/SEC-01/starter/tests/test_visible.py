import tempfile,unittest
from pathlib import Path
from solution import install_bundle
class Visible(unittest.TestCase):
 def test_install(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)/"root";self.assertEqual(install_bundle(root,[{"path":"etc","type":"dir"},{"path":"etc/app.conf","type":"file","content":"ok"}]),["etc","etc/app.conf"]);self.assertEqual((root/"etc/app.conf").read_text(),"ok")
 def test_traversal_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)/"root"
   with self.assertRaises(ValueError):install_bundle(root,[{"path":"../escape","type":"file","content":"bad"}])
   self.assertFalse((Path(td)/"escape").exists())
if __name__=="__main__":unittest.main()
