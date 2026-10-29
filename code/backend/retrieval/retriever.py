"""
retriever.py
============
Retrieval Service Layer for the AI Placement Assistant RAG pipeline.

Provides two complementary retrieval modes over persistent ChromaDB:
1. Semantic Vector Search: Dense embedding similarity for conceptual & exploratory queries.
2. Exact / Keyword & Metadata Filter Search: Comprehensive matching for "all questions" requests
   (e.g., all HashMap questions, all HR questions, all questions for a specific company/role)
   with deterministic pagination and exact counts.
"""

from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure ingestion directory is on sys.path
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
INGESTION_DIR = BACKEND_DIR / "ingestion"
for p in [str(INGESTION_DIR), str(CURRENT_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from embeddings import embed_text
from index_chroma import (
    DEFAULT_COLLECTION_NAME,
    get_chroma_client,
    get_or_create_collection,
    resolve_default_chroma_path,
)


class PlacementRetriever:
    """
    Unified retrieval service for placement interview questions.
    """

    def __init__(
        self,
        persist_dir: Optional[Union[str, Path]] = None,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ):
        self.persist_dir = Path(persist_dir) if persist_dir else resolve_default_chroma_path()
        self.client = get_chroma_client(self.persist_dir)
        self.collection = get_or_create_collection(self.client, collection_name)

    def _build_chroma_where(
        self,
        company_name: Optional[str] = None,
        role_name: Optional[str] = None,
        batch: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Constructs valid ChromaDB metadata filter conditions."""
        conditions: List[Dict[str, Any]] = []

        if company_name and company_name.strip():
            conditions.append({"company_name": company_name.strip()})
        if role_name and role_name.strip():
            conditions.append({"role_name": role_name.strip()})
        if batch and batch.strip():
            conditions.append({"batch": batch.strip()})
        if category and category.strip():
            conditions.append({"category": category.strip().lower()})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def search_semantic(
        self,
        query: str,
        top_k: int = 10,
        company_name: Optional[str] = None,
        role_name: Optional[str] = None,
        batch: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes dense semantic similarity search using Sentence Transformers and ChromaDB.

        Args:
            query: Natural language query string.
            top_k: Number of nearest neighbors to retrieve.
            company_name, role_name, batch, category: Optional metadata filters.

        Returns:
            List of result dicts sorted by similarity score (1 - cosine_distance).
        """
        if not isinstance(query, str) or not query.strip():
            return []

        cleaned_query = query.strip()
        query_vector = embed_text(cleaned_query)
        where_filter = self._build_chroma_where(company_name, role_name, batch, category)

        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [query_vector],
            "n_results": max(1, top_k),
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            query_kwargs["where"] = where_filter

        raw = self.collection.query(**query_kwargs)

        results: List[Dict[str, Any]] = []
        ids = raw.get("ids", [[]])[0]
        docs = raw.get("documents", [[]])[0]
        metas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0]

        for doc_id, text, meta, dist in zip(ids, docs, metas, distances):
            # ChromaDB with cosine space returns cosine distance = 1 - cosine_similarity.
            # Convert to similarity score: similarity = 1 - distance.
            similarity = round(max(0.0, 1.0 - float(dist)), 4) if dist is not None else 0.0
            results.append({
                "id": doc_id,
                "text": text,
                "metadata": meta or {},
                "similarity_score": similarity,
                "retrieval_mode": "semantic",
            })

        return results

    def search_comprehensive(
        self,
        keyword: Optional[str] = None,
        company_name: Optional[str] = None,
        role_name: Optional[str] = None,
        batch: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Executes comprehensive keyword and metadata filtering with pagination.
        Guarantees complete coverage for queries like 'all HashMap questions' or 'all HR questions'.
        """
        where_filter = self._build_chroma_where(company_name, role_name, batch, category)

        # Retrieve candidate records based on metadata filter
        get_kwargs: Dict[str, Any] = {"include": ["documents", "metadatas"]}
        if where_filter:
            get_kwargs["where"] = where_filter

        raw = self.collection.get(**get_kwargs)

        ids = raw.get("ids", [])
        docs = raw.get("documents", [])
        metas = raw.get("metadatas", [])

        # In-memory keyword filtering for case-insensitive matching
        clean_keyword = keyword.strip().lower() if keyword and keyword.strip() else None

        matching_items: List[Dict[str, Any]] = []
        for doc_id, text, meta in zip(ids, docs, metas):
            if clean_keyword:
                text_lower = text.lower()
                # Match keyword as substring in question text
                if clean_keyword not in text_lower:
                    continue

            matching_items.append({
                "id": doc_id,
                "text": text,
                "metadata": meta or {},
                "similarity_score": 1.0,  # Exact match flag
                "retrieval_mode": "exact_keyword" if clean_keyword else "metadata_filtered",
            })

        # Deterministic sorting: by company name, then role, then ID
        matching_items.sort(
            key=lambda x: (
                x["metadata"].get("company_name", "").lower(),
                x["metadata"].get("role_name", "").lower(),
                x["id"],
            )
        )

        total_matches = len(matching_items)
        safe_page = max(1, page)
        safe_page_size = max(1, page_size)

        start_idx = (safe_page - 1) * safe_page_size
        end_idx = start_idx + safe_page_size
        paginated_items = matching_items[start_idx:end_idx]

        total_pages = (total_matches + safe_page_size - 1) // safe_page_size if total_matches > 0 else 1

        return {
            "items": paginated_items,
            "total_matches": total_matches,
            "page": safe_page,
            "page_size": safe_page_size,
            "total_pages": total_pages,
            "has_next": end_idx < total_matches,
            "has_prev": safe_page > 1,
        }

    def get_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Fetches a single question by its deterministic ID."""
        if not question_id or not str(question_id).strip():
            return None

        raw = self.collection.get(ids=[str(question_id).strip()], include=["documents", "metadatas"])
        if not raw or not raw.get("ids"):
            return None

        return {
            "id": raw["ids"][0],
            "text": raw["documents"][0],
            "metadata": raw["metadatas"][0] if raw.get("metadatas") else {},
        }

    def count(self) -> int:
        """Returns total document count in the collection."""
        return self.collection.count()

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        company_name: Optional[str] = None,
        role_name: Optional[str] = None,
        batch: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Convenience alias for search_semantic."""
        return self.search_semantic(
            query=query,
            top_k=top_k,
            company_name=company_name,
            role_name=role_name,
            batch=batch,
            category=category,
        )

    def get_distinct_filter_options(self) -> Dict[str, List[str]]:
        """Returns unique categories, companies, roles, and batches available in vector store."""
        raw = self.collection.get(include=["metadatas"])
        metas = raw.get("metadatas", [])

        companies = set()
        roles = set()
        batches = set()
        categories = set()

        for m in metas:
            if not m:
                continue
            if m.get("company_name"):
                companies.add(m["company_name"])
            if m.get("role_name"):
                roles.add(m["role_name"])
            if m.get("batch"):
                batches.add(m["batch"])
            if m.get("category"):
                categories.add(m["category"])

        return {
            "companies": sorted(list(companies)),
            "roles": sorted(list(roles)),
            "batches": sorted(list(batches)),
            "categories": sorted(list(categories)),
        }
