"""
test_embeddings_smoke.py
========================
Optional real-model smoke test for the AI Placement Assistant embedding module.

Executes a live end-to-end check using sentence-transformers/all-MiniLM-L6-v2
on a tiny real sample to verify:
1. Successful weight initialization and dynamic dimension reporting (384).
2. Live single-query and batch embedding generation.
3. L2 vector normalization (magnitude == 1.0).
4. Semantic sanity check: semantically related technical questions have higher
   cosine similarity than unrelated HR questions.
"""

import math
import sys
import unittest
from pathlib import Path

# Ensure ingestion directory is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from embeddings import (
    DEFAULT_MODEL_NAME,
    embed_text,
    embed_texts,
    get_embedding_dimension,
)


def cosine_similarity(v1: list, v2: list) -> float:
    """Computes cosine similarity between two 1D vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


class TestEmbeddingsSmoke(unittest.TestCase):

    def test_real_model_smoke(self):
        """Live smoke test executing real all-MiniLM-L6-v2 model."""
        print(f"\n[Smoke Test] Loading real model: {DEFAULT_MODEL_NAME}...")
        dim = get_embedding_dimension()
        self.assertEqual(dim, 384, f"Expected 384 dimensions, got {dim}")
        print(f"[Smoke Test] Model dimension verified: {dim}")

        q_tech_1 = "What is an array in C++ and how does contiguous memory allocation work?"
        q_tech_2 = "Explain dynamic array resizing and memory reallocation."
        q_hr = "Why do you want to join our company as an intern?"

        # Test single query embedding
        vec_tech_1 = embed_text(q_tech_1)
        self.assertEqual(len(vec_tech_1), 384)
        self.assertTrue(all(isinstance(x, float) for x in vec_tech_1))

        # Verify L2 normalization: magnitude should be approximately 1.0
        mag_1 = math.sqrt(sum(x * x for x in vec_tech_1))
        self.assertAlmostEqual(mag_1, 1.0, places=4)

        # Test batch embedding
        batch_results = embed_texts([q_tech_2, q_hr], batch_size=2)
        self.assertEqual(len(batch_results), 2)
        vec_tech_2 = batch_results[0]
        vec_hr = batch_results[1]
        self.assertEqual(len(vec_tech_2), 384)
        self.assertEqual(len(vec_hr), 384)

        # Semantic sanity check
        sim_tech = cosine_similarity(vec_tech_1, vec_tech_2)
        sim_cross = cosine_similarity(vec_tech_1, vec_hr)

        print(f"[Smoke Test] Cosine similarity (Tech Q1 vs Tech Q2): {sim_tech:.4f}")
        print(f"[Smoke Test] Cosine similarity (Tech Q1 vs HR Q)    : {sim_cross:.4f}")

        # Two questions about arrays must be more similar than array vs HR question
        self.assertGreater(
            sim_tech,
            sim_cross,
            "Expected related technical questions to have higher similarity than cross-domain HR question",
        )
        print("[Smoke Test] Real model smoke test completed successfully!")


if __name__ == "__main__":
    unittest.main()
