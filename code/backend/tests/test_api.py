"""
test_api.py
===========
Integration tests for FastAPI application endpoints.
"""

from pathlib import Path
import sys
import unittest

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from main import app


class TestFastAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["collection_count"], 9302)
        self.assertIn("gemini_model", data)
        self.assertIn("embedding_model", data)

    def test_get_filters(self):
        response = self.client.get("/api/filters")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("companies", data)
        self.assertIn("roles", data)
        self.assertIn("batches", data)
        self.assertIn("categories", data)
        self.assertEqual(len(data["companies"]), 212)
        self.assertIn("American Express", data["companies"])

    def test_get_analytics_overview(self):
        response = self.client.get("/api/analytics/overview")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_questions"], 9302)
        self.assertEqual(data["total_companies"], 212)

    def test_get_analytics_dashboard(self):
        response = self.client.get("/api/analytics/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("overview", data)
        self.assertIn("topics", data)
        self.assertIn("companies", data)
        self.assertIn("categories", data)
        self.assertIn("batches", data)
        self.assertIn("roles", data)
        self.assertIn("experiences", data)

    def test_list_questions_default_pagination(self):
        response = self.client.get("/api/questions?page=1&page_size=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["items"]), 10)
        self.assertEqual(data["total"], 9302)
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 10)
        self.assertTrue(data["has_next"])
        self.assertFalse(data["has_prev"])

    def test_list_questions_filter_company(self):
        response = self.client.get("/api/questions?company=American+Express&page_size=20")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 321)
        for item in data["items"]:
            self.assertEqual(item["metadata"]["company_name"], "American Express")

    def test_list_questions_filter_keyword(self):
        response = self.client.get("/api/questions?search=HashMap&page_size=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["total"], 0)
        for item in data["items"]:
            self.assertIn("hashmap", item["text"].lower())

    def test_get_question_by_id(self):
        # Fetch first question from list to get a valid ID
        list_resp = self.client.get("/api/questions?page=1&page_size=1")
        self.assertEqual(list_resp.status_code, 200)
        first_item = list_resp.json()["items"][0]
        q_id = first_item["id"]

        response = self.client.get(f"/api/questions/{q_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], q_id)
        self.assertEqual(data["text"], first_item["text"])

    def test_get_question_not_found(self):
        response = self.client.get("/api/questions/non_existent_question_id_99999")
        self.assertEqual(response.status_code, 404)

    def test_chat_endpoint_valid_query(self):
        payload = {
            "query": "What are common Python questions asked at American Express?",
            "filters": {
                "company_name": "American Express"
            },
            "top_k": 3
        }
        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("answer", data)
        self.assertIn("sources", data)
        self.assertIn(data["mode"], ["rag", "fallback"])
        self.assertGreaterEqual(len(data["sources"]), 1)

    def test_chat_endpoint_empty_query(self):
        payload = {"query": "   "}
        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
