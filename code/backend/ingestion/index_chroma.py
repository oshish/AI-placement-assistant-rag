"""
index_chroma.py
===============
ChromaDB Vector Database Ingestion and Indexing Layer.

Connects the document preparation stage and embedding module to a persistent
local ChromaDB collection (`placement_questions`).

Key Properties:
1. Persistent Local Storage: Stored at `code/backend/data/chroma_db`.
2. Idempotent Indexing: Uses `collection.upsert()` so re-runs never create duplicate vectors.
3. Batch Processing: Computes embeddings and upserts in configurable chunks (default: 64).
4. Memory-Efficient: Does not hold all embedding matrices in RAM at once.
5. Reusable: Database operations are decoupled from HTTP routes and CLI.
"""

import argparse
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Union

import chromadb

# Ensure ingestion directory is importable
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from embeddings import embed_texts, get_embedding_dimension
from prepare_documents import load_question_records, prepare_question_documents

logger = logging.getLogger("index_chroma")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DEFAULT_COLLECTION_NAME: str = "placement_questions"
DEFAULT_BATCH_SIZE: int = 64


def resolve_default_chroma_path() -> Path:
    """Resolves default persistent ChromaDB storage directory."""
    backend_dir = CURRENT_DIR.parent
    return backend_dir / "data" / "chroma_db"


def get_chroma_client(persist_dir: Optional[Union[str, Path]] = None) -> chromadb.PersistentClient:
    """
    Creates or reopens a persistent ChromaDB client on local disk.

    Args:
        persist_dir: Directory path for ChromaDB storage.

    Returns:
        chromadb.PersistentClient instance.
    """
    target_path = Path(persist_dir) if persist_dir is not None else resolve_default_chroma_path()
    target_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(target_path))


def get_or_create_collection(
    client: chromadb.PersistentClient,
    collection_name: str = DEFAULT_COLLECTION_NAME,
):
    """
    Retrieves an existing collection or creates a new one configured for cosine similarity.

    Args:
        client: Active PersistentClient.
        collection_name: Name of collection.

    Returns:
        ChromaDB Collection object.
    """
    # Configure HNSW space for cosine distance so vector similarity matches normalized embeddings
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def index_documents(
    documents: List[Dict[str, Any]],
    collection: Any,
    batch_size: int = DEFAULT_BATCH_SIZE,
    show_progress: bool = True,
) -> Dict[str, Any]:
    """
    Generates embeddings and upserts documents into ChromaDB in batches.

    Args:
        documents: List of prepared document dicts ({id, text, metadata}).
        collection: Target ChromaDB collection.
        batch_size: Number of documents to embed and upsert per batch.
        show_progress: Whether to log batch-by-batch progress.

    Returns:
        Summary dict containing processed counts and collection status.
    """
    if not isinstance(documents, list):
        raise TypeError("Documents must be provided as a list.")

    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer.")

    total_docs = len(documents)
    if total_docs == 0:
        return {
            "documents_indexed": 0,
            "batches_processed": 0,
            "collection_total_count": collection.count(),
        }

    total_batches = (total_docs + batch_size - 1) // batch_size
    processed_count = 0

    if show_progress:
        logger.info(
            f"Beginning ChromaDB indexing: {total_docs} documents across {total_batches} batches (batch_size={batch_size})"
        )

    for b_idx in range(total_batches):
        start_idx = b_idx * batch_size
        end_idx = min(start_idx + batch_size, total_docs)
        batch = documents[start_idx:end_idx]

        ids = [doc["id"] for doc in batch]
        texts = [doc["text"] for doc in batch]
        metadatas = [doc["metadata"] for doc in batch]

        # Generate embeddings for current batch using sentence-transformers
        vectors = embed_texts(texts, batch_size=batch_size, show_progress_bar=False)

        # Idempotent upsert: inserts new records or updates existing IDs in place
        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=vectors,
            metadatas=metadatas,
        )

        processed_count += len(batch)
        if show_progress and (b_idx + 1) % 10 == 0 or (b_idx + 1) == total_batches:
            logger.info(
                f"Batch {b_idx + 1}/{total_batches} complete ({processed_count}/{total_docs} documents upserted)"
            )

    return {
        "documents_indexed": processed_count,
        "batches_processed": total_batches,
        "collection_total_count": collection.count(),
    }


def ingest_placement_questions(
    data_path: Optional[Union[str, Path]] = None,
    persist_dir: Optional[Union[str, Path]] = None,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    batch_size: int = DEFAULT_BATCH_SIZE,
    show_progress: bool = True,
) -> Dict[str, Any]:
    """
    High-level pipeline: Loads JSON records -> Prepares documents -> Upserts into ChromaDB.
    """
    records = load_question_records(data_path)
    documents, skipped = prepare_question_documents(records)

    client = get_chroma_client(persist_dir)
    collection = get_or_create_collection(client, collection_name)

    stats = index_documents(
        documents=documents,
        collection=collection,
        batch_size=batch_size,
        show_progress=show_progress,
    )

    return {
        **stats,
        "records_loaded": len(records),
        "skipped_items": len(skipped),
        "collection_name": collection_name,
        "storage_path": str(persist_dir or resolve_default_chroma_path()),
    }


def print_indexing_summary(summary: Dict[str, Any]) -> None:
    """Prints a clear terminal summary of ChromaDB indexing."""
    print("\n" + "=" * 65)
    print("AI Placement Assistant RAG — ChromaDB Indexing Complete")
    print("=" * 65)
    print(f"  • Raw Records Loaded          : {summary.get('records_loaded', 'N/A')}")
    print(f"  • Documents Upserted          : {summary.get('documents_indexed', 'N/A')}")
    print(f"  • Skipped / Malformed Items   : {summary.get('skipped_items', 0)}")
    print(f"  • Total Batches Executed      : {summary.get('batches_processed', 'N/A')}")
    print(f"  • Target Collection Name      : {summary.get('collection_name', DEFAULT_COLLECTION_NAME)}")
    print(f"  • Final Collection Total Count: {summary.get('collection_total_count', 'N/A')}")
    print(f"  • Persistent DB Location      : {summary.get('storage_path', 'N/A')}")
    print("=" * 65 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Index placement questions into persistent ChromaDB.")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Batch size for embedding and upsert")
    parser.add_argument("--stats-only", action="store_true", help="Print current collection count without re-indexing")
    args = parser.parse_args()

    client = get_chroma_client()
    collection = get_or_create_collection(client)

    if args.stats_only:
        print(f"Collection '{collection.name}' currently contains {collection.count()} documents.")
        return 0

    try:
        summary = ingest_placement_questions(batch_size=args.batch_size, show_progress=True)
        print_indexing_summary(summary)
        return 0
    except Exception as exc:
        logger.error(f"ChromaDB indexing failed: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
