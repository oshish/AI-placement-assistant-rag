"""
test_prepare_documents.py
=========================
Unit tests for prepare_documents.py using Python's standard unittest framework.

Tests all required scenarios:
1. Normal company-role record with multiple questions.
2. Multiple companies containing identical question wording (no accidental deduplication).
3. Missing optional metadata (graceful default handling).
4. Empty questions (skipped and reported).
5. Malformed question entries (non-dict or malformed items).
6. Stable, deterministic document IDs across repeated runs.
7. Invalid JSON, missing file, and unexpected top-level data structures.
8. Preservation of company, role, batch, and category metadata for every question.
"""

import json
import tempfile
import sys
import unittest
from pathlib import Path

# Ensure ingestion directory is on sys.path regardless of execution CWD
sys.path.insert(0, str(Path(__file__).resolve().parent))

from prepare_documents import (
    generate_question_id,
    load_question_records,
    prepare_question_documents,
    resolve_default_data_path,
    summarize_prepared_documents,
)


class TestPrepareDocuments(unittest.TestCase):

    def test_normal_record_with_multiple_questions(self):
        """Test 1: Standard company-role record with multiple questions."""
        records = [
            {
                "id": "rec_001",
                "company_name": "Google",
                "company_id": "google",
                "role_name": "Software Engineer",
                "role_id": "swe",
                "batch": "2027",
                "questions": [
                    {"question": "Explain LRU Cache.", "category": "technical"},
                    {"question": "Tell me about a time you failed.", "category": "hr"},
                ],
            }
        ]

        docs, skipped = prepare_question_documents(records)
        self.assertEqual(len(docs), 2)
        self.assertEqual(len(skipped), 0)

        # First question
        self.assertEqual(docs[0]["id"], "rec_001_q0")
        self.assertEqual(docs[0]["text"], "Explain LRU Cache.")
        self.assertEqual(docs[0]["metadata"]["category"], "technical")
        self.assertEqual(docs[0]["metadata"]["company_name"], "Google")
        self.assertEqual(docs[0]["metadata"]["question_index"], 0)

        # Second question
        self.assertEqual(docs[1]["id"], "rec_001_q1")
        self.assertEqual(docs[1]["text"], "Tell me about a time you failed.")
        self.assertEqual(docs[1]["metadata"]["category"], "hr")
        self.assertEqual(docs[1]["metadata"]["company_name"], "Google")
        self.assertEqual(docs[1]["metadata"]["question_index"], 1)

    def test_multiple_companies_with_identical_questions(self):
        """Test 2: Identical question text appearing across different companies is preserved."""
        common_q = "Explain the difference between a process and a thread."
        records = [
            {
                "id": "rec_amazon",
                "company_name": "Amazon",
                "role_name": "SDE",
                "batch": "2026",
                "questions": [{"question": common_q, "category": "technical"}],
            },
            {
                "id": "rec_microsoft",
                "company_name": "Microsoft",
                "role_name": "Software Engineer",
                "batch": "2027",
                "questions": [{"question": common_q, "category": "technical"}],
            },
        ]

        docs, skipped = prepare_question_documents(records)
        self.assertEqual(len(docs), 2)
        self.assertEqual(len(skipped), 0)

        # Both documents must be retained with distinct IDs and correct metadata
        self.assertNotEqual(docs[0]["id"], docs[1]["id"])
        self.assertEqual(docs[0]["text"], common_q)
        self.assertEqual(docs[1]["text"], common_q)
        self.assertEqual(docs[0]["metadata"]["company_name"], "Amazon")
        self.assertEqual(docs[1]["metadata"]["company_name"], "Microsoft")

    def test_missing_optional_metadata(self):
        """Test 3: Missing optional metadata fields do not crash and receive safe defaults."""
        records = [
            {
                # id, company_id, role_id, batch missing
                "company_name": "Startup Inc",
                "role_name": "Backend Intern",
                "questions": [{"question": "What is REST?", "category": "technical"}],
            }
        ]

        docs, skipped = prepare_question_documents(records)
        self.assertEqual(len(docs), 1)
        self.assertEqual(len(skipped), 0)

        meta = docs[0]["metadata"]
        self.assertEqual(meta["company_name"], "Startup Inc")
        self.assertEqual(meta["role_name"], "Backend Intern")
        self.assertEqual(meta["company_id"], "")
        self.assertEqual(meta["role_id"], "")
        self.assertEqual(meta["batch"], "")
        self.assertTrue(docs[0]["id"].startswith("rec_0_q0"))

    def test_empty_questions(self):
        """Test 4: Empty and whitespace-only questions are skipped and reported."""
        records = [
            {
                "id": "rec_empty",
                "company_name": "Tech Corp",
                "questions": [
                    {"question": "", "category": "technical"},
                    {"question": "   \n\t  ", "category": "hr"},
                    {"question": "Valid Question Here", "category": "technical"},
                ],
            }
        ]

        docs, skipped = prepare_question_documents(records)
        self.assertEqual(len(docs), 1)
        self.assertEqual(len(skipped), 2)
        self.assertEqual(docs[0]["text"], "Valid Question Here")
        self.assertTrue(any("Empty or non-string" in s["reason"] for s in skipped))

    def test_malformed_question_entries(self):
        """Test 5: Malformed question entries (non-dict or non-string) are handled safely."""
        records = [
            {
                "id": "rec_malformed",
                "company_name": "Tech Corp",
                "questions": [
                    "This is a string instead of a dict",
                    12345,
                    {"question": None, "category": "technical"},
                    {"question": "Valid Question", "category": "technical"},
                ],
            },
            "This entire record is a string instead of a dict",
        ]

        docs, skipped = prepare_question_documents(records)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["text"], "Valid Question")
        # 3 malformed questions + 1 non-dict record = 4 skipped items
        self.assertEqual(len(skipped), 4)

    def test_stable_ids_across_repeated_runs(self):
        """Test 6: Document IDs are deterministic across multiple runs."""
        records = [
            {
                "id": "abc_123",
                "company_name": "Adobe",
                "questions": [
                    {"question": "Question A", "category": "technical"},
                    {"question": "Question B", "category": "hr"},
                ],
            }
        ]

        docs_run1, _ = prepare_question_documents(records)
        docs_run2, _ = prepare_question_documents(records)

        self.assertEqual([d["id"] for d in docs_run1], [d["id"] for d in docs_run2])
        self.assertEqual(docs_run1[0]["id"], generate_question_id("abc_123", 0))
        self.assertEqual(docs_run1[1]["id"], generate_question_id("abc_123", 1))

    def test_invalid_json_and_unexpected_structure(self):
        """Test 7: File errors, invalid JSON, and unexpected top-level structures raise clear exceptions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Subcase A: Missing file
            non_existent = Path(tmpdir) / "missing.json"
            with self.assertRaises(FileNotFoundError):
                load_question_records(non_existent)

            # Subcase B: Invalid JSON syntax
            corrupted = Path(tmpdir) / "corrupted.json"
            corrupted.write_text("{ unclosed json: ", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                load_question_records(corrupted)

            # Subcase C: Unexpected top-level object (dict instead of list)
            invalid_root = Path(tmpdir) / "invalid_root.json"
            invalid_root.write_text('{"records": []}', encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                load_question_records(invalid_root)
            self.assertIn("expected list", str(ctx.exception))

    def test_preservation_of_metadata_and_wording(self):
        """Test 8: Exact wording and metadata are preserved without alteration."""
        verbatim_question = (
            "Given an unsorted integer array nums, return the smallest missing positive integer."
        )
        records = [
            {
                "id": "meta_test",
                "company_name": "Atlassian",
                "company_id": "atlassian",
                "role_name": "Site Reliability Engineer",
                "role_id": "sre",
                "batch": "2028",
                "questions": [
                    {"question": verbatim_question, "category": "technical"}
                ],
            }
        ]

        docs, skipped = prepare_question_documents(records)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["text"], verbatim_question)

        meta = docs[0]["metadata"]
        self.assertEqual(meta["company_name"], "Atlassian")
        self.assertEqual(meta["company_id"], "atlassian")
        self.assertEqual(meta["role_name"], "Site Reliability Engineer")
        self.assertEqual(meta["role_id"], "sre")
        self.assertEqual(meta["batch"], "2028")
        self.assertEqual(meta["category"], "technical")
        self.assertEqual(meta["source_record_id"], "meta_test")
        self.assertEqual(meta["question_index"], 0)

        # ChromaDB compatibility: ensure all metadata values are primitive scalars
        for key, val in meta.items():
            self.assertIsInstance(
                val,
                (str, int, float, bool),
                f"Metadata key '{key}' has non-primitive type: {type(val)}",
            )

    def test_fallback_when_questions_array_is_absent(self):
        """Bonus Test: Backward compatibility when record only has separate category arrays."""
        records = [
            {
                "id": "rec_fallback",
                "company_name": "Cisco",
                "technical_questions": ["What is TCP 3-way handshake?"],
                "hr_questions": ["Why Cisco?"],
                "additional_questions": ["Explain OSPF routing."],
            }
        ]

        docs, skipped = prepare_question_documents(records)
        self.assertEqual(len(docs), 3)
        self.assertEqual(len(skipped), 0)
        self.assertEqual(docs[0]["metadata"]["category"], "technical")
        self.assertEqual(docs[1]["metadata"]["category"], "hr")
        self.assertEqual(docs[2]["metadata"]["category"], "additional_practice")


if __name__ == "__main__":
    unittest.main()
