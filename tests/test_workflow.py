"""Offline acceptance checks against the included live YouTube dataset."""
import csv
import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from src.filtering import classify
from src.outreach import simulate_send
from src.pipeline import DATA
from src.personalization import openai_personalize


def word_count(value):
    return len(re.findall(r"\b[\w'-]+\b", value))


class WorkflowAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (DATA / "influencers.csv").open(encoding="utf-8", newline="") as handle:
            cls.records = list(csv.DictReader(handle))
        with (DATA / "shortlisted_messages.csv").open(encoding="utf-8", newline="") as handle:
            cls.shortlist = list(csv.DictReader(handle))

    def test_live_dataset_has_50_unique_records_and_explanations(self):
        self.assertGreaterEqual(len(self.records), 50)
        self.assertEqual(len({row["profile_url"] for row in self.records}), len(self.records))
        self.assertTrue(all(row["filter_reason"] for row in self.records))
        self.assertTrue(all(row["contact_email"] for row in self.records))

    def test_shortlist_matches_filter_and_message_lengths(self):
        actual = [row for row in self.records if row["filter_status"] == "Passed"]
        self.assertEqual(len(actual), len(self.shortlist))
        self.assertTrue(all(classify(row)[0] for row in actual))
        for row in self.shortlist:
            self.assertTrue(60 <= word_count(row["email_pitch"]) <= 90)
            self.assertTrue(15 <= word_count(row["instagram_dm"]) <= 30)

    def test_private_email_is_never_guessed(self):
        for row in self.records:
            if row["contact_email"] == "Not Found":
                self.assertEqual(row["contact_email"], "Not Found")
            else:
                self.assertRegex(row["contact_email"], r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def test_tracker_is_duplicate_safe_and_sends_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir=Path(directory)
            shutil.copy(DATA / "influencers.csv", data_dir / "influencers.csv")
            first = simulate_send(data_dir)
            second = simulate_send(data_dir)
        self.assertEqual(first["queued"], 0)
        self.assertEqual(first["skipped"], len(self.shortlist))
        self.assertEqual(second["queued"], 0)
        self.assertEqual(second["duplicates"], len(self.shortlist))
        self.assertTrue(all(not row["Sent Date"] for row in second["tracker"]))
        self.assertTrue(all(row["Status"] == "SKIPPED_NO_PUBLIC_EMAIL" for row in second["tracker"]))

    def test_missing_openai_key_uses_local_mode(self):
        prior=os.environ.pop("OPENAI_API_KEY",None)
        try:
            self.assertIsNone(openai_personalize(self.shortlist[0]))
        finally:
            if prior is not None: os.environ["OPENAI_API_KEY"] = prior

    def test_streamlit_dashboard_and_tracker_pages_render(self):
        app_path=DATA.parent / "app.py"
        app=AppTest.from_file(str(app_path)).run(timeout=30)
        self.assertEqual(len(app.exception),0)
        self.assertEqual([metric.value for metric in app.metric], ["50","5","0","5"])
        app.radio[0].set_value("Outreach Tracker").run(timeout=30)
        self.assertEqual(len(app.exception),0)
        self.assertTrue(app.dataframe)


if __name__ == "__main__": unittest.main()
