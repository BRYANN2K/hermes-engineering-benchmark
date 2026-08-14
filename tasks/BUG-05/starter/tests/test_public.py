import unittest
from datetime import datetime, timezone
from retention import select_deletions

class PublicTests(unittest.TestCase):
    def test_keep_is_applied_per_label(self):
        names=['backup-20260101T000000Z-db.tar.gz','backup-20260102T000000Z-db.tar.gz','backup-20260101T000000Z-media.tar.gz','backup-20260102T000000Z-media.tar.gz']
        now=datetime(2026,2,1,tzinfo=timezone.utc)
        self.assertEqual(select_deletions(names,1,now,7), ['backup-20260101T000000Z-db.tar.gz','backup-20260101T000000Z-media.tar.gz'])
    def test_invalid_names_are_ignored(self):
        now=datetime(2026,2,1,tzinfo=timezone.utc)
        self.assertEqual(select_deletions(['notes.txt','backup-20261340T000000Z-db.tar.gz'],0,now,0), [])

if __name__ == '__main__': unittest.main()
