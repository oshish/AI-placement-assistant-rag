"""
generator.py
============
LLM Answer Generation Layer using the Gemini API.

Provides grounded generation using retrieved placement interview questions as evidence.
Strictly distinguishes between general conceptual explanations and verified dataset evidence.
Safely handles missing keys, timeouts, and API exceptions without exposing secrets.
"""

import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Load local environment variables from .env if present
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent.parent
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")

DEFAULT_GEMINI_MODEL: str = os.getenv("GEMINI_MODEL_NAME", "gemini-3.5-flash")


class GeminiGenerator:
    """
    RAG generation engine powered by Google Gemini.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = model_name or os.getenv("GEMINI_MODEL_NAME", DEFAULT_GEMINI_MODEL)
        self._client = None

        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as err:
                self._client = None

    def is_configured(self) -> bool:
        """Returns True if a valid-looking GEMINI_API_KEY is configured."""
        return bool(self.api_key and len(self.api_key) > 5)

    def _build_system_instruction(self) -> str:
        return (
            "You are 'Your AI Placement Assistant', an expert technical recruitment and placement mentor "
            "for campus recruitment at Thapar Institute of Engineering and Technology (TIET).\n\n"
            "CRITICAL GUIDELINES:\n"
            "1. Grounding: When mentioning interview questions, companies, rounds, or hiring statistics, "
            "rely strictly on the RETRIEVED DATASET EVIDENCE provided below. Do NOT hallucinate questions.\n"
            "2. Distinct Evidence: Clearly distinguish between general educational concepts (which you may "
            "explain using your general knowledge) and actual questions from the placement dataset.\n"
            "3. Source Attribution: When listing or citing questions from the evidence, include the company name, "
            "role, batch, and category.\n"
            "4. Missing Data: If no retrieved evidence matches the user's specific company or concept, "
            "explicitly acknowledge that our current local dataset does not contain questions for it, "
            "then provide general technical guidance.\n"
            "5. Formatting: Use clean Markdown with headers, bullet points, and code blocks where helpful."
        )

    def _format_context(self, retrieved_questions: List[Dict[str, Any]]) -> str:
        if not retrieved_questions:
            return "No matching questions were found in the local placement dataset."

        context_lines = ["RETRIEVED DATASET QUESTIONS:"]
        for idx, item in enumerate(retrieved_questions, 1):
            q_id = item.get("id", "N/A")
            q_text = item.get("text", "").strip()
            meta = item.get("metadata", {})
            company = meta.get("company_name", "Unknown Company")
            role = meta.get("role_name", "Unknown Role")
            batch = meta.get("batch", "Unknown Batch")
            category = meta.get("category", "General")

            context_lines.append(
                f"[{idx}] Question: \"{q_text}\"\n"
                f"    Source ID: {q_id} | Company: {company} | Role: {role} | Batch: {batch} | Category: {category}"
            )
        return "\n\n".join(context_lines)

    def generate_answer(
        self,
        query: str,
        retrieved_questions: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Generates a grounded RAG response.

        Returns:
            Dict containing:
            - 'answer': generated text or guidance message
            - 'sources': list of question objects used as evidence
            - 'is_mock_or_unconfigured': bool
        """
        if not self.is_configured():
            msg = (
                "**Gemini API Key is not configured.**\n\n"
                "To enable AI answer generation, please set `GEMINI_API_KEY` in your environment or in a `.env` file.\n\n"
                f"However, our retrieval system successfully located **{len(retrieved_questions)}** relevant questions "
                "from your local placement dataset. You can inspect the retrieved questions below or in the Question Library!"
            )
            return {
                "answer": msg,
                "sources": retrieved_questions,
                "is_mock_or_unconfigured": True,
            }

        context_str = self._format_context(retrieved_questions)
        prompt = (
            f"{self._build_system_instruction()}\n\n"
            f"--- CONTEXT ---\n{context_str}\n\n"
            f"--- USER QUERY ---\n{query.strip()}\n\n"
            "--- ASSISTANT RESPONSE ---"
        )

        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            answer_text = response.text if hasattr(response, "text") and response.text else "No response generated."
            return {
                "answer": answer_text,
                "sources": retrieved_questions,
                "is_mock_or_unconfigured": False,
            }
        except Exception as err:
            err_msg = str(err).replace(self.api_key, "[REDACTED]") if self.api_key else str(err)
            fallback = (
                f"**Generation Error:** An error occurred while communicating with Gemini API: `{err_msg}`\n\n"
                f"The retrieval system still located **{len(retrieved_questions)}** relevant questions from your dataset:"
            )
            return {
                "answer": fallback,
                "sources": retrieved_questions,
                "is_mock_or_unconfigured": True,
                "error": err_msg,
            }

    def generate_response(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Convenience wrapper matching service naming, returning mode ('rag' or 'fallback').
        """
        res = self.generate_answer(
            query=query,
            retrieved_questions=context_documents,
            conversation_history=conversation_history,
        )
        res["mode"] = "fallback" if res.get("is_mock_or_unconfigured") else "rag"
        return res
