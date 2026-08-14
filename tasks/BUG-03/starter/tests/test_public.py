import unittest
from job_plan import plan_jobs

class PublicTests(unittest.TestCase):
    def test_dependencies_override_priority(self):
        jobs = [{'name':'deploy','needs':['build'],'priority':10}, {'name':'build'}, {'name':'lint','priority':1}]
        self.assertEqual(plan_jobs(jobs), ['lint','build','deploy'])
    def test_unknown_dependency_rejected(self):
        with self.assertRaises(ValueError): plan_jobs([{'name':'a','needs':['missing']}])

if __name__ == '__main__': unittest.main()
