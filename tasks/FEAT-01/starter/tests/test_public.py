import unittest
from env_expand import expand_env
class PublicTests(unittest.TestCase):
    def test_plain_default_and_required(self):
        self.assertEqual(expand_env('${A}/${B:-x}', {'A':'one'}), 'one/x')
        with self.assertRaisesRegex(ValueError,'need B'): expand_env('${B:?need B}', {})
    def test_values_are_not_recursively_expanded(self):
        self.assertEqual(expand_env('${A}', {'A':'${B}','B':'two'}), '${B}')
if __name__=='__main__':unittest.main()
