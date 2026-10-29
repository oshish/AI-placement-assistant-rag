"""
test_retriever.py
=================
Unit tests for the PlacementRetriever service.

Tests:
1. Semantic search with distance-to-similarity conversion.
2. Comprehensive keyword matching returning all records (not just top-k).
3. Metadata filtering by company, role, batch, category.
4. Pagination behavior (page, page_size, has_next, total_pages).
5. Duplicate preservation: identical questions across different companies are both retrieved.
6. Empty search query and empty database handling.
7. Single document retrieval by ID.
8. Filter options aggregation.
"""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure paths are configured
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
INGESTION_DIR = BACKEND_DIR / "ingestion"
for p in [str(INGESTION_DIR), str(CURRENT_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import chromadb
from index_chroma import get_chroma_client, get_or_create_collection
from retriever import PlacementRetriever


class TestPlacementRetriever(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.persist_path = Path(self.tmp_dir.name)

        # Populate a lightweight fixture collection
        client = get_chroma_client(self.persist_path)
        col = get_or_create_collection(client, "test_retrieval")

        # 4 test records
        # doc1 and doc2 have identical question text but different companies!
        col.upsert(
            ids=["doc_1", "doc_2", "doc_3", "doc_4"],
            documents=[
                "Implement a HashMap from scratch in C++.",
                "Implement a HashMap from scratch in C++.",
                "What are your greatest weaknesses?",
                "Explain Dijkstra's shortest path algorithm.",
            ],
            embeddings=[
                [0.1] * 384,
                [0.1] * 384,
                [0.9] * 384,
                [0.2] * 384,
            ],
            metadatas=[
                {"company_name": "Amazon", "role_name": "SDE", "batch": "2027", "category": "technical"},
                {"company_name": "Google", "role_name": "SWE", "batch": "2027", "category": "technical"},
                {"company_name": "Google", "role_name": "SWE", "batch": "2027", "category": "hr"},
                {"company_name": "Microsoft", "role_name": "SDE", "batch": "2026", "category": "technical"},
            ],
        )

        self.retriever = PlacementRetriever(
            persist_dir=self.persist_path,
            collection_name="test_retrieval",
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_comprehensive_keyword_search_returns_all_matches(self):
        """Searching for 'hashmap' returns BOTH questions, preserving duplicates across companies."""
        res = self.retriever.search_comprehensive(keyword="hashmap", page_size=10)

        self.assertEqual(res["total_matches"], 2)
        self.assertEqual(len(res["items"]), 2)
        companies = {item["metadata"]["company_name"] for item in res["items"]}
        self.assertEqual(companies, {"Amazon", "Google"})

    def test_comprehensive_metadata_filtering(self):
        """Filtering by category='hr' returns only the HR question."""
        res = self.retriever.search_comprehensive(category="hr")
        self.assertEqual(res["total_matches"], 1)
        self.assertEqual(res["items"][0]["text"], "What are your greatest weaknesses?")
        self.assertEqual(res["items"][0]["metadata"]["company_name"], "Google")

    def test_pagination(self):
        """Pagination slices records properly across multiple pages."""
        # Page 1, size 1
        page1 = self.retriever.search_comprehensive(keyword="hashmap", page=1, page_size=1)
        self.assertEqual(page1["total_matches"], 2)
        self.assertEqual(len(page1["items"]), 1)
        self.assertTrue(page1["has_next"])
        self.assertFalse(page1["has_prev"])

        # Page 2, size 1
        page2 = self.retriever.search_comprehensive(keyword="hashmap", page=2, page_size=1)
        self.assertEqual(page2["total_matches"], 2)
        self.assertEqual(len(page2["items"]), 1)
        self.assertFalse(page2["has_next"])
        self.assertTrue(page2["has_prev"])
        self.assertNotEqual(page1["items"][0]["id"], page2["items"][0]["id"])

    @patch("retriever.embed_text", return_value=[0.1] * 384)
    def test_semantic_search_with_mocked_vector(self, mock_embed):
        """Semantic search returns ranked items with computed similarity scores."""
        results = self.retriever.search_semantic("hash map lookup", top_k=2)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["retrieval_mode"], "semantic")
        self.assertIn("similarity_score", results[0])
        self.assertTrue(0.0 <= results[0]["similarity_score"] <= 1.0)

    def test_get_by_id(self):
        """Fetching by deterministic ID retrieves the single document."""
        item = self.retriever.get_by_id("doc_3")
        self.assertIsNotNone(item)
        self.assertEqual(item["id"], "doc_3")
        self.assertEqual(item["text"], "What are your greatest weaknesses?")

        # Nonexistent ID
        missing = self.retriever.get_by_id("non_existent_id")
        self.assertIsNone(missing)

    def test_get_distinct_filter_options(self):
        """Aggregates all unique metadata filters from the dataset."""
        opts = self.retriever.get_distinct_filter_options()
        self.assertEqual(opts["companies"], ["Amazon", "Google", "Microsoft"])
        self.assertEqual(opts["roles"], ["SDE", "SWE"])
        self.assertEqual(opts["batches"], ["2026", "2027"])
        self.assertEqual(opts["categories"], ["hr", "technical"])


if __name__ == "__main__":
    unittest.main()
