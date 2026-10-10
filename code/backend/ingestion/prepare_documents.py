"""
prepare_documents.py
====================
Document Preparation Stage for the AI Placement Assistant RAG Pipeline.

Transforms raw structured JSON records (interview_questions.json) into atomic,
searchable documents suitable for vector embedding and ChromaDB indexing.

Design Principles:
1. One Searchable Document per Individual Question (Atomic Retrieval Unit).
2. Pure Text Content: Preserves exact verbatim question without artificial prompt wrapping.
3. ChromaDB-Compatible Flat Metadata: All metadata fields are primitive types (str, int).
4. Deterministic, Stable Document IDs: Predictable IDs across re-runs.
5. Zero External Dependencies: Pure Python standard library.
"""

from collections import Counter
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple, Union


def resolve_default_data_path() -> Path:
    """
    Resolves the default path to interview_questions.json relative to this file.
    Works dynamically across environments without hardcoding absolute user paths.
    """
    current_dir = Path(__file__).resolve().parent
    # Expected structure: code/backend/ingestion/prepare_documents.py
    # Data is at:         code/backend/data/raw/interview_questions.json
    backend_dir = current_dir.parent
    data_path = backend_dir / "data" / "raw" / "interview_questions.json"
    return data_path


def load_question_records(file_path: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
    """
    Loads and validates the raw interview questions JSON file.

    Args:
        file_path: Optional custom path. If None, resolves using resolve_default_data_path().

    Returns:
        List of raw company-role records.

    Raises:
        FileNotFoundError: If the target file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        ValueError: If the top-level structure is not a list.
    """
    resolved_path = Path(file_path) if file_path is not None else resolve_default_data_path()

    if not resolved_path.is_file():
        raise FileNotFoundError(
            f"Question dataset not found at expected path: {resolved_path}"
        )

    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as err:
        raise json.JSONDecodeError(
            f"Failed to parse JSON file at {resolved_path}: {err.msg}",
            err.doc,
            err.pos,
        )

    if not isinstance(data, list):
        raise ValueError(
            f"Unexpected top-level data structure in {resolved_path}: "
            f"expected list, got {type(data).__name__}"
        )

    return data


def generate_question_id(record_id: Optional[str], question_index: int) -> str:
    """
    Generates a deterministic, stable document ID for a question document.

    Format: {source_record_id}_q{question_index}
    Example: '1BNkNhRzll6NYdokUXCk_q0'

    Rationale:
    - Stable across repeated ingestion runs as long as source record ID and question
      ordering within the record remain consistent.
    - Human-readable and traceable back to the source record.

    Limitations:
    - If questions within a record are inserted, removed, or reordered in the source JSON,
      subsequent indices will shift.
    """
    safe_rec_id = str(record_id or "").strip() or "unknown_rec"
    return f"{safe_rec_id}_q{question_index}"


def prepare_question_documents(
    records: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Converts company-role records into individual searchable question documents.

    Args:
        records: List of raw company-role dictionaries loaded from interview_questions.json.

    Returns:
        tuple: (documents, skipped_issues)
            - documents: List of prepared document dicts ready for ChromaDB.
            - skipped_issues: List of diagnostics describing any skipped or malformed items.
    """
    documents: List[Dict[str, Any]] = []
    skipped_issues: List[Dict[str, Any]] = []

    for r_idx, record in enumerate(records):
        if not isinstance(record, dict):
            skipped_issues.append({
                "record_index": r_idx,
                "reason": f"Record is not a dictionary (type={type(record).__name__})",
            })
            continue

        record_id = str(record.get("id") or f"rec_{r_idx}").strip()
        company_name = str(record.get("company_name") or "").strip()
        company_id = str(record.get("company_id") or "").strip()
        role_name = str(record.get("role_name") or "").strip()
        role_id = str(record.get("role_id") or "").strip()
        batch = str(record.get("batch") or "").strip()

        # Primary source: structured 'questions' array with category tags
        raw_questions = record.get("questions")

        # Fallback: if 'questions' array is absent, gather from categorized arrays
        if not isinstance(raw_questions, list):
            fallback_items = []
            for q in record.get("technical_questions") or []:
                fallback_items.append({"question": q, "category": "technical"})
            for q in record.get("hr_questions") or []:
                fallback_items.append({"question": q, "category": "hr"})
            for q in record.get("additional_questions") or []:
                fallback_items.append({"question": q, "category": "additional_practice"})
            raw_questions = fallback_items

        for q_idx, q_item in enumerate(raw_questions):
            if not isinstance(q_item, dict):
                skipped_issues.append({
                    "record_id": record_id,
                    "question_index": q_idx,
                    "reason": f"Question item is not a dictionary (type={type(q_item).__name__})",
                })
                continue

            raw_text = q_item.get("question")
            if not isinstance(raw_text, str) or not raw_text.strip():
                skipped_issues.append({
                    "record_id": record_id,
                    "question_index": q_idx,
                    "reason": "Empty or non-string question text",
                })
                continue

            cleaned_text = raw_text.strip()
            raw_category = str(q_item.get("category") or "").strip()
            category = raw_category if raw_category else "unspecified"

            doc_id = generate_question_id(record_id, q_idx)

            # Metadata is kept strictly ChromaDB-compatible:
            # Primitive scalar types only (str, int). No nested dicts or lists.
            metadata = {
                "company_name": company_name,
                "company_id": company_id,
                "role_name": role_name,
                "role_id": role_id,
                "batch": batch,
                "category": category,
                "source_record_id": record_id,
                "question_index": q_idx,
            }

            documents.append({
                "id": doc_id,
                "text": cleaned_text,
                "metadata": metadata,
            })

    return documents, skipped_issues


def summarize_prepared_documents(
    records: List[Dict[str, Any]],
    documents: List[Dict[str, Any]],
    skipped_issues: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Computes a concise diagnostic summary of the prepared documents.
    """
    categories = Counter(doc["metadata"]["category"] for doc in documents)
    companies = {doc["metadata"]["company_name"] for doc in documents if doc["metadata"]["company_name"]}
    roles = {doc["metadata"]["role_name"] for doc in documents if doc["metadata"]["role_name"]}
    batches = {doc["metadata"]["batch"] for doc in documents if doc["metadata"]["batch"]}

    return {
        "records_loaded": len(records),
        "valid_documents": len(documents),
        "skipped_or_malformed": len(skipped_issues),
        "distinct_companies": len(companies),
        "distinct_roles": len(roles),
        "batches": sorted(list(batches)),
        "categories": dict(categories),
    }


def print_preparation_summary(summary: Dict[str, Any], sample_doc: Optional[Dict[str, Any]] = None) -> None:
    """
    Prints a clean, concise terminal report of the document preparation stage.
    """
    print("=" * 65)
    print("AI Placement Assistant RAG — Document Preparation Summary")
    print("=" * 65)
    print(f"  • Source Records Loaded        : {summary['records_loaded']}")
    print(f"  • Valid Question Documents     : {summary['valid_documents']}")
    print(f"  • Skipped / Malformed Items    : {summary['skipped_or_malformed']}")
    print(f"  • Distinct Companies           : {summary['distinct_companies']}")
    print(f"  • Distinct Roles               : {summary['distinct_roles']}")
    print(f"  • Batches Represented          : {', '.join(summary['batches']) if summary['batches'] else 'None'}")
    print("\n  Question Categories:")
    for cat, count in sorted(summary["categories"].items(), key=lambda x: x[1], reverse=True):
        print(f"    - {cat:<22}: {count:,}")
    print("=" * 65)

    if sample_doc:
        print("\nRepresentative Prepared Document (JSON Preview):")
        print("-" * 65)
        print(json.dumps(sample_doc, indent=2, ensure_ascii=False))
        print("-" * 65)


def main() -> int:
    """CLI execution entrypoint."""
    try:
        records = load_question_records()
        documents, skipped = prepare_question_documents(records)
        summary = summarize_prepared_documents(records, documents, skipped)
        sample = documents[0] if documents else None
        print_preparation_summary(summary, sample)
        return 0
    except Exception as exc:
        print(f"Error during document preparation: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
