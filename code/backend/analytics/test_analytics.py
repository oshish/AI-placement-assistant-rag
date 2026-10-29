"""
test_analytics.py
=================
Unit and integration tests for the analytics module.
"""

import json
from pathlib import Path
import tempfile
import unittest

from analytics import (
    PlacementAnalytics,
    clear_analytics_cache,
    get_analytics,
)


class TestAnalyticsUnit(unittest.TestCase):
    def setUp(self):
        clear_analytics_cache()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.q_file = Path(self.temp_dir.name) / "test_questions.json"
        self.exp_file = Path(self.temp_dir.name) / "test_exp.json"

    def tearDown(self):
        clear_analytics_cache()
        self.temp_dir.cleanup()

    def test_analytics_with_mock_data(self):
        sample_questions = [
            {
                "id": "rec_1",
                "company_name": "Acme Corp",
                "role_name": "SDE-1",
                "batch": "2026",
                "topics": ["Python", "SQL"],
                "oa_topics": ["Arrays"],
                "questions": [
                    {"question": "What is GIL?", "category": "technical"},
                    {"question": "Tell me about a challenge.", "category": "hr"},
                ],
            },
            {
                "id": "rec_2",
                "company_name": "Acme Corp",
                "role_name": "Data Analyst",
                "batch": "2025",
                "topics": ["SQL", "Tableau"],
                "oa_topics": [],
                "questions": [
                    {"question": "Explain indexing in SQL.", "category": "technical"},
                ],
            },
            {
                "id": "rec_3",
                "company_name": "Beta LLC",
                "role_name": "Backend Dev",
                "batch": "2026",
                "topics": ["Go"],
                "oa_topics": ["Graph"],
                "questions": [
                    {"question": "What are goroutines?", "category": "technical"},
                ],
            },
        ]

        sample_experiences = [
            {
                "company_name": "Acme Corp",
                "role_name": "SDE-1",
                "batch": "2026",
                "outcome": "Selected",
                "hiring_mode": "On-Campus",
                "advice": "Focus on LeetCode and DBMS fundamentals.",
            }
        ]

        with open(self.q_file, "w", encoding="utf-8") as f:
            json.dump(sample_questions, f)
        with open(self.exp_file, "w", encoding="utf-8") as f:
            json.dump(sample_experiences, f)

        engine = PlacementAnalytics(
            questions_path=self.q_file,
            experiences_path=self.exp_file,
        )
        data = engine.compute_all()

        self.assertEqual(data["overview"]["total_questions"], 4)
        self.assertEqual(data["overview"]["total_companies"], 2)
        self.assertEqual(data["overview"]["total_roles"], 3)
        self.assertEqual(data["overview"]["total_batches"], 2)
        self.assertEqual(data["overview"]["total_experiences"], 1)

        # Topic counts: SQL was in rec_1 and rec_2 => count 2
        topic_counts = {t["topic"]: t["count"] for t in data["topics"]}
        self.assertEqual(topic_counts["SQL"], 2)
        self.assertEqual(topic_counts["Python"], 1)

        # Company questions count: Acme Corp has 3 questions (2 in rec_1, 1 in rec_2)
        company_counts = {c["company_name"]: c["question_count"] for c in data["companies"]}
        self.assertEqual(company_counts["Acme Corp"], 3)
        self.assertEqual(company_counts["Beta LLC"], 1)

        # Filter options
        filters = data["filter_options"]
        self.assertIn("Acme Corp", filters["companies"])
        self.assertIn("Beta LLC", filters["companies"])
        self.assertIn("2026", filters["batches"])
        self.assertIn("technical", filters["categories"])

    def test_missing_files_handled_gracefully(self):
        engine = PlacementAnalytics(
            questions_path=Path(self.temp_dir.name) / "non_existent.json",
            experiences_path=Path(self.temp_dir.name) / "non_existent_exp.json",
        )
        data = engine.compute_all()
        self.assertEqual(data["overview"]["total_questions"], 0)
        self.assertEqual(data["overview"]["total_companies"], 0)
        self.assertEqual(len(data["topics"]), 0)


class TestAnalyticsLiveSmoke(unittest.TestCase):
    def test_live_dataset_analytics(self):
        data = get_analytics()
        self.assertEqual(data["overview"]["total_questions"], 9302)
        self.assertEqual(data["overview"]["total_companies"], 212)
        self.assertGreater(len(data["topics"]), 10)
        self.assertGreater(len(data["companies"]), 20)
        self.assertGreaterEqual(len(data["batches"]), 2)


if __name__ == "__main__":
    unittest.main()
