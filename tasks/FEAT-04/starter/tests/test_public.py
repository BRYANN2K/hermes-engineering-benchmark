import unittest
from retry import run_with_retry
class PublicTests(unittest.TestCase):
    def test_retries_in_policy_order(self):
        calls=[];sleeps=[]
        def op():
            calls.append(1)
            if len(calls)<3:raise ValueError('no')
            return 'yes'
        self.assertEqual(run_with_retry(op,[0.1,0.2],sleeps.append,(ValueError,)),'yes')
        self.assertEqual(sleeps,[0.1,0.2])
    def test_nonretryable_propagates_without_sleep(self):
        sleeps=[]
        with self.assertRaises(KeyError):run_with_retry(lambda:(_ for _ in ()).throw(KeyError('x')),[1],sleeps.append,(ValueError,))
        self.assertEqual(sleeps,[])
if __name__=='__main__':unittest.main()
