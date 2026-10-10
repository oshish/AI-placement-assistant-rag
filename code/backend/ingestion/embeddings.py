"""
embeddings.py
=============
Embedding generation module for the AI Placement Assistant RAG pipeline.

Responsibilities:
1. Load and cache the Sentence Transformers embedding model (`all-MiniLM-L6-v2`).
2. Provide clean, validated functions to embed single queries and batches of documents.
3. Enforce deterministic output dimensions (384 for all-MiniLM-L6-v2).
4. Return standardized Python primitive structures (`list[float]`, `list[list[float]]`)
   directly compatible with ChromaDB in the next stage.
5. Strictly validate empty and invalid inputs to prevent corrupt vector indices.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

# Default model configuration
DEFAULT_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_BATCH_SIZE: int = 32

# In-memory model cache to avoid re-instantiating heavy models per request
_MODEL_CACHE: Dict[str, SentenceTransformer] = {}


def get_embedding_model(model_name: str = DEFAULT_MODEL_NAME) -> SentenceTransformer:
    """
    Retrieves or loads a SentenceTransformer model instance from memory cache.

    Args:
        model_name: Hugging Face model identifier or local path.

    Returns:
        Cached SentenceTransformer instance.

    Raises:
        ValueError: If model_name is empty or invalid.
    """
    if not isinstance(model_name, str) or not model_name.strip():
        raise ValueError("Model name must be a non-empty string.")

    cleaned_name = model_name.strip()
    if cleaned_name not in _MODEL_CACHE:
        # Load once per process lifecycle
        _MODEL_CACHE[cleaned_name] = SentenceTransformer(cleaned_name)

    return _MODEL_CACHE[cleaned_name]


def clear_model_cache() -> None:
    """
    Clears the in-memory model cache. Useful for testing and resource cleanup.
    """
    _MODEL_CACHE.clear()


def get_embedding_dimension(model_name: str = DEFAULT_MODEL_NAME) -> int:
    """
    Dynamically retrieves the embedding dimension produced by the model.

    Args:
        model_name: Embedding model identifier.

    Returns:
        Integer vector dimension (e.g. 384 for all-MiniLM-L6-v2).
    """
    model = get_embedding_model(model_name)
    if hasattr(model, "get_embedding_dimension"):
        dimension = model.get_embedding_dimension()
    elif hasattr(model, "get_sentence_embedding_dimension"):
        dimension = model.get_sentence_embedding_dimension()
    else:
        dimension = None

    if dimension is None:
        # Fallback inspection if dimension method is not defined
        sample_vec = model.encode("dimension check sample")
        return int(sample_vec.shape[-1])
    return int(dimension)


def embed_text(
    text: str,
    model_name: str = DEFAULT_MODEL_NAME,
) -> List[float]:
    """
    Generates an embedding vector for a single string (document text or search query).

    Args:
        text: Input string to embed.
        model_name: Model identifier to use.

    Returns:
        1D list of floating point numbers representing the semantic embedding.

    Raises:
        TypeError: If text is not a string.
        ValueError: If text is empty or contains only whitespace.
    """
    if not isinstance(text, str):
        raise TypeError(f"Input text must be a string, got {type(text).__name__}.")

    cleaned_text = text.strip()
    if not cleaned_text:
        raise ValueError("Input text cannot be empty or whitespace-only.")

    # Re-use embed_texts to guarantee identical preprocessing and normalization
    results = embed_texts([cleaned_text], batch_size=1, model_name=model_name)
    return results[0]


def embed_texts(
    texts: List[str],
    batch_size: int = DEFAULT_BATCH_SIZE,
    model_name: str = DEFAULT_MODEL_NAME,
    show_progress_bar: bool = False,
) -> List[List[float]]:
    """
    Generates embedding vectors for a collection of strings using batch processing.

    Args:
        texts: List of strings to embed.
        batch_size: Positive integer determining how many texts to encode simultaneously.
        model_name: Embedding model identifier.
        show_progress_bar: Whether to display sentence-transformers progress bar.

    Returns:
        2D list where each element is a list of floats matching the model dimension.
        Returns [] if input texts is empty.

    Raises:
        TypeError: If texts is not a list or if any item is not a string.
        ValueError: If batch_size <= 0 or if any item is empty/whitespace-only.
    """
    if not isinstance(texts, list):
        raise TypeError(f"Texts parameter must be a list, got {type(texts).__name__}.")

    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError(f"Batch size must be a positive integer, got {batch_size}.")

    if len(texts) == 0:
        return []

    # Strict validation of each element prior to model execution
    cleaned_texts: List[str] = []
    for idx, item in enumerate(texts):
        if not isinstance(item, str):
            raise TypeError(
                f"Element at index {idx} must be a string, got {type(item).__name__}."
            )
        cleaned = item.strip()
        if not cleaned:
            raise ValueError(
                f"Element at index {idx} cannot be empty or whitespace-only."
            )
        cleaned_texts.append(cleaned)

    model = get_embedding_model(model_name)

    # Encode with L2 normalization enabled:
    # Normalized embeddings allow inner product (dot product) to equal cosine similarity,
    # which is significantly faster and standard for vector DB retrieval.
    raw_embeddings = model.encode(
        cleaned_texts,
        batch_size=batch_size,
        show_progress_bar=show_progress_bar,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    # Convert to pure Python list of floats for standard ChromaDB ingestion
    if isinstance(raw_embeddings, np.ndarray):
        return raw_embeddings.tolist()

    return [list(map(float, vec)) for vec in raw_embeddings]


if __name__ == "__main__":
    print(f"Loading default embedding model: {DEFAULT_MODEL_NAME}...")
    dim = get_embedding_dimension()
    print(f"Model dimension verified: {dim} dimensions.")
    sample = "What is the time complexity of QuickSort in the average case?"
    vec = embed_text(sample)
    print(f"Sample embedded successfully: '{sample}'")
    print(f"Vector length: {len(vec)} | First 5 values: {[round(x, 4) for x in vec[:5]]}")
