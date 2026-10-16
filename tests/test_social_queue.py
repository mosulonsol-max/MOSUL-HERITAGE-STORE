import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from scripts.queue_daily_update import POSTS, choose_slot, queue_update, validate_achievement_update
from scripts.x_text import accepted_post_id, weighted_length


class SocialQueueTests(unittest.TestCase):
    def test_x_credit_exhaustion_is_deferred_without_masking_other_errors(self):
        self.assertIsNone(accepted_post_id(402, {"detail": "credits depleted"}, "credits depleted"))
        with self.assertRaises(RuntimeError):
            accepted_post_id(401, {"detail": "unauthorized"}, "unauthorized")

    def test_posts_fit_x_and_are_ascii(self):
        for text in POSTS.values():
            self.assertTrue(text.isascii())
            self.assertLessEqual(weighted_length(text), 280)

    def test_x_urls_use_weighted_length(self):
        self.assertEqual(weighted_length("a https://example.com/long/path z"), 27)

    def test_only_positive_achievements_are_allowed(self):
        for text in POSTS.values():
            validate_achievement_update(text)
        with self.assertRaises(ValueError):
            validate_achievement_update("Publishing failed because a required secret is missing.")
        with self.assertRaises(ValueError):
            validate_achievement_update("This tissue sample was catalogued.")

    def test_social_copy_does_not_overstate_optional_signing(self):
        self.assertNotIn("signed provenance", POSTS["morning"].casefold())
        self.assertIn("optional Ed25519", POSTS["evening"])

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
