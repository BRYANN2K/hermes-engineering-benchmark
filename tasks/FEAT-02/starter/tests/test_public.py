import unittest
from rate_limiter import RateLimiter
class Clock:
    def __init__(self):self.t=0.0
    def __call__(self):return self.t
class PublicTests(unittest.TestCase):
    def test_rejection_is_not_recorded(self):
        c=Clock();r=RateLimiter(2,10,c)
        self.assertEqual(r.allow('a'),(True,0.0));c.t=1;self.assertEqual(r.allow('a'),(True,0.0));c.t=2
        self.assertEqual(r.allow('a'),(False,8.0));self.assertEqual(r.snapshot(),{'a':(0.0,1)})
    def test_keys_are_independent(self):
        c=Clock();r=RateLimiter(1,5,c);self.assertTrue(r.allow('a')[0]);self.assertTrue(r.allow('b')[0])
if __name__=='__main__':unittest.main()
