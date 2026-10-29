"""
test_generator.py
=================
Unit tests for GeminiGenerator using mocks.
"""

from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure paths are configured
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
for p in [str(CURRENT_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from generator import GeminiGenerator


class TestGeminiGenerator(unittest.TestCase):

    def test_unconfigured_key_behavior(self):
        """When API key is missing, returns clear configuration guidance and preserves sources."""
        gen = GeminiGenerator(api_key="")
        self.assertFalse(gen.is_configured())

        dummy_sources = [
            {"id": "q1", "text": "Explain HashMap.", "metadata": {"company_name": "Oracle"}}
        ]
        result = gen.generate_answer("How does HashMap work?", dummy_sources)

        self.assertTrue(result["is_mock_or_unconfigured"])
        self.assertIn("Gemini API Key is not configured", result["answer"])
        self.assertEqual(len(result["sources"]), 1)
        self.assertEqual(result["sources"][0]["text"], "Explain HashMap.")

    def test_successful_generation_mock(self):
        """When API key is configured, formats context and calls client."""
        gen = GeminiGenerator(api_key="fake-key-12345", model_name="gemini-2.5-flash")
        self.assertTrue(gen.is_configured())

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "A HashMap is a hash table based implementation of the Map interface."
        mock_client.models.generate_content.return_value = mock_response
        gen._client = mock_client

        dummy_sources = [
            {
                "id": "q_10",
                "text": "What is the load factor in Java HashMap?",
                "metadata": {"company_name": "Amazon", "role_name": "SDE", "batch": "2027", "category": "technical"},
            }
        ]

        result = gen.generate_answer("Explain HashMap load factor", dummy_sources)

        self.assertFalse(result["is_mock_or_unconfigured"])
        self.assertEqual(result["answer"], mock_response.text)
        self.assertEqual(len(result["sources"]), 1)
        mock_client.models.generate_content.assert_called_once()

    def test_api_exception_handling_and_key_redaction(self):
        """API errors must be handled gracefully without exposing API keys in output."""
        fake_secret = "secret-gemini-key-9999"
        gen = GeminiGenerator(api_key=fake_secret)
        self.assertTrue(gen.is_configured())

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception(f"Quota exceeded for {fake_secret}")
        gen._client = mock_client

        result = gen.generate_answer("Sample query", [])

        self.assertTrue(result["is_mock_or_unconfigured"])
        self.assertIn("Generation Error", result["answer"])
        self.assertNotIn(fake_secret, result["answer"])
        self.assertIn("[REDACTED]", result["answer"])


if __name__ == "__main__":
    unittest.main()
