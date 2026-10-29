"""
test_index_chroma.py
====================
Unit tests for index_chroma.py using ChromaDB and mocked embeddings.

Verifies:
1. Collection creation and reopening on persistent disk.
2. Ingestion across multiple batches.
3. Idempotent re-ingestion (re-running does NOT create duplicate records).
4. Metadata preservation and retrieval by ID / query.
5. Handling of empty document lists.
6. Error handling (invalid batch sizes, invalid input types).
"""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure ingestion directory is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import chromadb
from index_chroma import (
    DEFAULT_COLLECTION_NAME,
    get_chroma_client,
    get_or_create_collection,
    index_documents,
)


def mock_embed_texts_fn(texts, batch_size=32, show_progress_bar=False):
    """Produces deterministic 384-dimensional vectors for testing without loading model."""
    vectors = []
    for i, t in enumerate(texts):
        # Create deterministic normalized-like 384-dim vector
        val = ((i + 1) % 100) / 100.0
        vec = [val] * 384
        vectors.append(vec)
    return vectors


class TestChromaIndexing(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.persist_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_collection_creation_and_persistence(self):
        """Verify collection creation, closing client, and reopening from disk."""
        client_1 = get_chroma_client(self.persist_path)
        col_1 = get_or_create_collection(client_1, "test_collection")
        self.assertEqual(col_1.count(), 0)

        # Upsert a single record
        col_1.upsert(
            ids=["doc_1"],
            documents=["Sample question"],
            embeddings=[[0.1] * 384],
            metadatas=[{"company_name": "Test Co", "category": "technical"}],
        )
        self.assertEqual(col_1.count(), 1)

        # Close client_1 and reopen with client_2 on the same directory
        del client_1
        client_2 = get_chroma_client(self.persist_path)
        col_2 = get_or_create_collection(client_2, "test_collection")

        self.assertEqual(col_2.count(), 1)
        res = col_2.get(ids=["doc_1"])
        self.assertEqual(res["documents"][0], "Sample question")
        self.assertEqual(res["metadatas"][0]["company_name"], "Test Co")

    @patch("index_chroma.embed_texts", side_effect=mock_embed_texts_fn)
    def test_multi_batch_ingestion_and_metadata_preservation(self, mock_embed):
        """Verify multiple batches are ingested with accurate metadata and IDs."""
        client = get_chroma_client(self.persist_path)
        col = get_or_create_collection(client, "batch_test")

        # Create 5 test documents
        docs = [
            {
                "id": f"q_{i}",
                "text": f"Question number {i}",
                "metadata": {
                    "company_name": "Apple" if i % 2 == 0 else "Microsoft",
                    "role_name": "SWE",
                    "batch": "2027",
                    "category": "technical",
                    "source_record_id": f"rec_{i}",
                    "question_index": i,
                },
            }
            for i in range(5)
        ]

        # Ingest with batch_size=2 (creates 3 batches: 2 + 2 + 1)
        stats = index_documents(docs, col, batch_size=2, show_progress=False)

        self.assertEqual(stats["documents_indexed"], 5)
        self.assertEqual(stats["batches_processed"], 3)
        self.assertEqual(col.count(), 5)

        # Retrieve doc q_2 and verify metadata
        res = col.get(ids=["q_2"])
        self.assertEqual(res["documents"][0], "Question number 2")
        self.assertEqual(res["metadatas"][0]["company_name"], "Apple")
        self.assertEqual(res["metadatas"][0]["question_index"], 2)

    @patch("index_chroma.embed_texts", side_effect=mock_embed_texts_fn)
    def test_idempotent_reingestion_no_duplicates(self, mock_embed):
        """Re-running ingestion on the same dataset must NOT duplicate records."""
        client = get_chroma_client(self.persist_path)
        col = get_or_create_collection(client, "idempotent_test")

        docs = [
            {
                "id": "fixed_id_1",
                "text": "What is virtual memory?",
                "metadata": {"company_name": "Intel", "category": "technical"},
            },
            {
                "id": "fixed_id_2",
                "text": "Explain paging.",
                "metadata": {"company_name": "Intel", "category": "technical"},
            },
        ]

        # First run
        stats_1 = index_documents(docs, col, batch_size=2, show_progress=False)
        self.assertEqual(col.count(), 2)

        # Second run with same IDs
        stats_2 = index_documents(docs, col, batch_size=2, show_progress=False)
        self.assertEqual(col.count(), 2)  # Still 2, not 4!

    def test_empty_documents_list(self):
        """Empty documents list should return 0 indexed without errors."""
        client = get_chroma_client(self.persist_path)
        col = get_or_create_collection(client, "empty_test")
        stats = index_documents([], col, batch_size=32, show_progress=False)

        self.assertEqual(stats["documents_indexed"], 0)
        self.assertEqual(stats["batches_processed"], 0)
        self.assertEqual(stats["collection_total_count"], 0)

    def test_error_handling(self):
        """Invalid types and batch sizes should raise appropriate exceptions."""
        client = get_chroma_client(self.persist_path)
        col = get_or_create_collection(client, "error_test")

        with self.assertRaises(TypeError):
            index_documents("not a list", col)

        with self.assertRaises(ValueError):
            index_documents([], col, batch_size=0)

        with self.assertRaises(ValueError):
            index_documents([], col, batch_size=-10)


if __name__ == "__main__":
    unittest.main()
