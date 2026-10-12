import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from scripts.queue_daily_update import POSTS, choose_slot, queue_update


class SocialQueueTests(unittest.TestCase):
    def test_posts_fit_x_and_are_ascii(self):
        for text in POSTS.values():
            self.assertTrue(text.isascii())
            self.assertLessEqual(len(text), 280)

    def test_three_baghdad_slots(self):
        self.assertEqual(choose_slot(dt.datetime(2026, 1, 1, 5, tzinfo=dt.timezone.utc)), "morning")
        self.assertEqual(choose_slot(dt.datetime(2026, 1, 1, 10, tzinfo=dt.timezone.utc)), "afternoon")
        self.assertEqual(choose_slot(dt.datetime(2026, 1, 1, 17, tzinfo=dt.timezone.utc)), "evening")

    def test_idempotent_queue(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "updates.json"
            path.write_text('{"updates": []}\n')
            now = dt.datetime(2026, 10, 12, 6, tzinfo=dt.timezone.utc)
            self.assertTrue(queue_update(path, "morning", now))
            self.assertFalse(queue_update(path, "morning", now))
            self.assertEqual(len(json.loads(path.read_text())["updates"]), 1)


if __name__ == "__main__":
    unittest.main()
