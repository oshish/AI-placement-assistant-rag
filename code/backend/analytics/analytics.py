"""
analytics.py
============
Analytics and Insights Module for the AI Placement Assistant RAG System.

Performs offline aggregations across the raw placement datasets
(interview_questions.json and interview_experiences.json) to supply
the 'Interview Insights & Analytics' dashboard and filter options.

Guarantees:
- Pure Python standard library (json, collections, pathlib, typing).
- In-memory caching of computed analytics for sub-millisecond API responses.
- Resilient to missing files or empty fields.
"""

from collections import Counter
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Global in-memory cache
_ANALYTICS_CACHE: Optional[Dict[str, Any]] = None


def resolve_data_paths() -> Tuple[Path, Path]:
    """
    Resolves data paths for questions and experiences JSON files.
    """
    current_dir = Path(__file__).resolve().parent
    backend_dir = current_dir.parent
    questions_path = backend_dir / "data" / "raw" / "interview_questions.json"
    experiences_path = backend_dir / "data" / "raw" / "interview_experiences.json"
    return questions_path, experiences_path


class PlacementAnalytics:
    """
    Computes aggregated statistical insights from placement dataset records.
    """

    def __init__(
        self,
        questions_path: Optional[Union[str, Path]] = None,
        experiences_path: Optional[Union[str, Path]] = None,
    ):
        default_q, default_exp = resolve_data_paths()
        self.questions_path = Path(questions_path) if questions_path else default_q
        self.experiences_path = Path(experiences_path) if experiences_path else default_exp
        self._computed: Optional[Dict[str, Any]] = None

    def _load_raw_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Loads raw JSON datasets safely."""
        questions_records: List[Dict[str, Any]] = []
        experiences_records: List[Dict[str, Any]] = []

        if self.questions_path.is_file():
            try:
                with open(self.questions_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        questions_records = data
            except Exception as e:
                logger.warning("Failed to load questions JSON: %s", e)

        if self.experiences_path.is_file():
            try:
                with open(self.experiences_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        experiences_records = data
            except Exception as e:
                logger.warning("Failed to load experiences JSON: %s", e)

        return questions_records, experiences_records

    def compute_all(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Computes all dashboard metrics and returns a structured dictionary.
        Results are cached in the instance.
        """
        if self._computed is not None and not force_refresh:
            return self._computed

        q_records, exp_records = self._load_raw_data()

        companies_set = set()
        roles_set = set()
        batches_set = set()
        categories_counter: Counter = Counter()
        topics_counter: Counter = Counter()
        oa_topics_counter: Counter = Counter()
        company_questions_counter: Counter = Counter()
        company_roles_map: Dict[str, set] = {}
        batch_questions_counter: Counter = Counter()
        role_questions_counter: Counter = Counter()
        total_questions = 0

        for record in q_records:
            comp = str(record.get("company_name", "")).strip()
            role = str(record.get("role_name", "")).strip()
            batch = str(record.get("batch", "")).strip()

            if comp:
                companies_set.add(comp)
                if comp not in company_roles_map:
                    company_roles_map[comp] = set()
                if role:
                    company_roles_map[comp].add(role)

            if role:
                roles_set.add(role)
            if batch:
                batches_set.add(batch)

            for topic in record.get("topics", []) or []:
                if topic and isinstance(topic, str):
                    clean_topic = topic.strip()
                    if clean_topic:
                        topics_counter[clean_topic] += 1

            for oa_topic in record.get("oa_topics", []) or []:
                if oa_topic and isinstance(oa_topic, str):
                    clean_oa = oa_topic.strip()
                    if clean_oa:
                        oa_topics_counter[clean_oa] += 1

            questions = record.get("questions", []) or []
            for q_obj in questions:
                total_questions += 1
                cat = str(q_obj.get("category", "technical") or "technical").strip().lower()
                categories_counter[cat] += 1
                if comp:
                    company_questions_counter[comp] += 1
                if batch:
                    batch_questions_counter[batch] += 1
                if role:
                    role_questions_counter[role] += 1

        # Experiences aggregation
        outcomes_counter: Counter = Counter()
        hiring_modes_counter: Counter = Counter()
        experience_tips: List[Dict[str, str]] = []

        for exp in exp_records:
            outcome = str(exp.get("outcome", "")).strip()
            if outcome:
                outcomes_counter[outcome] += 1
            hm = str(exp.get("hiring_mode", "")).strip()
            if hm:
                hiring_modes_counter[hm] += 1
            advice = str(exp.get("advice", "")).strip()
            if advice:
                experience_tips.append({
                    "company_name": str(exp.get("company_name", "")).strip(),
                    "role_name": str(exp.get("role_name", "")).strip(),
                    "batch": str(exp.get("batch", "")).strip(),
                    "advice": advice[:300] + "..." if len(advice) > 300 else advice,
                    "outcome": outcome,
                })

        # Structured result
        result: Dict[str, Any] = {
            "overview": {
                "total_questions": total_questions,
                "total_companies": len(companies_set),
                "total_roles": len(roles_set),
                "total_batches": len(batches_set),
                "total_experiences": len(exp_records),
                "total_company_role_records": len(q_records),
            },
            "topics": [
                {"topic": name, "count": count}
                for name, count in topics_counter.most_common(30)
            ],
            "oa_topics": [
                {"topic": name, "count": count}
                for name, count in oa_topics_counter.most_common(20)
            ],
            "companies": [
                {
                    "company_name": name,
                    "question_count": count,
                    "role_count": len(company_roles_map.get(name, set())),
                }
                for name, count in company_questions_counter.most_common(30)
            ],
            "categories": [
                {
                    "category": cat,
                    "count": count,
                    "percentage": round((count / total_questions * 100), 1) if total_questions > 0 else 0,
                }
                for cat, count in categories_counter.most_common()
            ],
            "batches": [
                {
                    "batch": batch,
                    "question_count": count,
                }
                for batch, count in sorted(batch_questions_counter.items(), key=lambda x: str(x[0]))
            ],
            "roles": [
                {
                    "role_name": role,
                    "question_count": count,
                }
                for role, count in role_questions_counter.most_common(20)
            ],
            "experiences": {
                "total": len(exp_records),
                "outcomes": dict(outcomes_counter),
                "hiring_modes": dict(hiring_modes_counter),
                "sample_tips": experience_tips[:8],
            },
            "filter_options": {
                "companies": sorted(list(companies_set)),
                "roles": sorted(list(roles_set)),
                "batches": sorted(list(batches_set)),
                "categories": sorted(list(categories_counter.keys())),
            },
        }

        self._computed = result
        return result


def get_analytics(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Returns the globally cached analytics dictionary, computing it if not yet cached.
    """
    global _ANALYTICS_CACHE
    if _ANALYTICS_CACHE is None or force_refresh:
        analytics_engine = PlacementAnalytics()
        _ANALYTICS_CACHE = analytics_engine.compute_all(force_refresh=force_refresh)
    return _ANALYTICS_CACHE


def clear_analytics_cache() -> None:
    """Clears the global analytics cache."""
    global _ANALYTICS_CACHE
    _ANALYTICS_CACHE = None
