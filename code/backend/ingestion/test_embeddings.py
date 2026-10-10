"""
test_embeddings.py
==================
Unit tests for embeddings.py using Python's standard unittest and unittest.mock.

Tests all scenarios with mocked SentenceTransformer:
1. Single-text embedding generation and return type.
2. Multiple-text embedding generation and return type.
3. Batch processing parameter validation and forwarding.
4. Empty inputs (empty string, whitespace string, empty list).
5. Invalid input types (integers, None, nested lists).
6. Output vector shape and numeric values.
7. Model reuse and caching (constructor called once per model name).
8. Error handling (zero/negative batch size, invalid model name).
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

# Ensure ingestion directory is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from embeddings import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_MODEL_NAME,
    clear_model_cache,
    embed_text,
    embed_texts,
    get_embedding_dimension,
    get_embedding_model,
)


class TestEmbeddingsModule(unittest.TestCase):

    def setUp(self):
        """Clear model cache before each test to ensure test isolation."""
        clear_model_cache()

    def tearDown(self):
        """Clean up model cache after each test."""
        clear_model_cache()

    @patch("embeddings.SentenceTransformer")
    def test_model_caching_and_reuse(self, mock_transformer_cls):
        """Verify that the model is loaded only once and reused on subsequent calls."""
        mock_instance = MagicMock()
        mock_transformer_cls.return_value = mock_instance

        # First call should instantiate SentenceTransformer
        model_1 = get_embedding_model(DEFAULT_MODEL_NAME)
        self.assertEqual(mock_transformer_cls.call_count, 1)

        # Second call should return cached instance without re-instantiating
        model_2 = get_embedding_model(DEFAULT_MODEL_NAME)
        self.assertEqual(mock_transformer_cls.call_count, 1)
        self.assertIs(model_1, model_2)

        # After clearing cache, next call should instantiate again
        clear_model_cache()
        model_3 = get_embedding_model(DEFAULT_MODEL_NAME)
        self.assertEqual(mock_transformer_cls.call_count, 2)

    @patch("embeddings.SentenceTransformer")
    def test_get_embedding_dimension(self, mock_transformer_cls):
        """Verify dimension extraction from the model interface."""
        mock_instance = MagicMock()
        mock_instance.get_embedding_dimension.return_value = 384
        mock_transformer_cls.return_value = mock_instance

        dim = get_embedding_dimension(DEFAULT_MODEL_NAME)
        self.assertEqual(dim, 384)
        mock_instance.get_embedding_dimension.assert_called_once()

    @patch("embeddings.SentenceTransformer")
    def test_embed_text_single(self, mock_transformer_cls):
        """Verify single text embedding produces 1D list of floats with correct values."""
        mock_instance = MagicMock()
        dummy_vector = np.array([[0.1, 0.2, 0.3, 0.4]], dtype=np.float32)
        mock_instance.encode.return_value = dummy_vector
        mock_transformer_cls.return_value = mock_instance

        result = embed_text("What is a binary search tree?")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 4)
        self.assertAlmostEqual(result[0], 0.1, places=5)
        self.assertAlmostEqual(result[3], 0.4, places=5)
        self.assertTrue(all(isinstance(x, float) for x in result))

        # Check call arguments to mock
        mock_instance.encode.assert_called_once_with(
            ["What is a binary search tree?"],
            batch_size=1,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    @patch("embeddings.SentenceTransformer")
    def test_embed_texts_multiple(self, mock_transformer_cls):
        """Verify multiple text embedding produces 2D list of floats."""
        mock_instance = MagicMock()
        dummy_vectors = np.array(
            [
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6],
                [0.7, 0.8, 0.9],
            ],
            dtype=np.float32,
        )
        mock_instance.encode.return_value = dummy_vectors
        mock_transformer_cls.return_value = mock_instance

        queries = ["Question 1", "Question 2", "Question 3"]
        results = embed_texts(queries, batch_size=16)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 3)
        self.assertEqual(len(results[0]), 3)
        self.assertAlmostEqual(results[0][0], 0.1, places=5)
        self.assertAlmostEqual(results[2][2], 0.9, places=5)

        mock_instance.encode.assert_called_once_with(
            queries,
            batch_size=16,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    def test_embed_texts_empty_list(self):
        """Empty input list should return [] immediately without invoking model."""
        with patch("embeddings.SentenceTransformer") as mock_transformer_cls:
            result = embed_texts([])
            self.assertEqual(result, [])
            mock_transformer_cls.assert_not_called()

    def test_embed_text_empty_and_whitespace(self):
        """Empty string or whitespace-only string should raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            embed_text("")
        self.assertIn("cannot be empty", str(ctx.exception).lower())

        with self.assertRaises(ValueError) as ctx:
            embed_text("   \n\t  ")
        self.assertIn("cannot be empty", str(ctx.exception).lower())

    def test_embed_text_invalid_type(self):
        """Non-string inputs should raise TypeError."""
        for invalid_val in [None, 12345, ["hello"], {"q": "text"}]:
            with self.assertRaises(TypeError):
                embed_text(invalid_val)

    def test_embed_texts_invalid_inputs(self):
        """Non-list input or lists with invalid elements should raise appropriate errors."""
        with self.assertRaises(TypeError):
            embed_texts("not a list")

        with self.assertRaises(TypeError):
            embed_texts(["valid text", 12345])

        with self.assertRaises(ValueError):
            embed_texts(["valid text", "   "])

    def test_batch_size_validation(self):
        """Non-positive or non-integer batch sizes should raise ValueError."""
        with self.assertRaises(ValueError):
            embed_texts(["Sample text"], batch_size=0)

        with self.assertRaises(ValueError):
            embed_texts(["Sample text"], batch_size=-5)

        with self.assertRaises(ValueError):
            embed_texts(["Sample text"], batch_size="32")  # type: ignore

    def test_invalid_model_name(self):
        """Empty or non-string model name should raise ValueError."""
        with self.assertRaises(ValueError):
            get_embedding_model("")

        with self.assertRaises(ValueError):
            get_embedding_model("   ")

        with self.assertRaises(ValueError):
            get_embedding_model(None)  # type: ignore


if __name__ == "__main__":
    unittest.main()
