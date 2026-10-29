"""
main.py
=======
FastAPI Backend Application for Your AI Placement Assistant RAG System.

Exposes RESTful endpoints for:
1. AI Assistant Chat (Grounded RAG retrieval + Gemini answer generation).
2. Question Library (Full-text keyword search, faceted filters, pagination).
3. Interview Insights & Analytics (Aggregated topic distributions, company rankings, batch stats).
4. System Health and Metadata filters.

Guarantees:
- Zero external network dependencies for Question Library and Analytics (100% offline).
- Graceful fallback when GEMINI_API_KEY is not configured.
- Permissive CORS for seamless local Vite development.
"""

import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure backend directory is in sys.path for relative and package imports
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from analytics.analytics import get_analytics
from llm.generator import GeminiGenerator
from retrieval.retriever import PlacementRetriever

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("placement_backend")

# Initialize FastAPI application
app = FastAPI(
    title="Your AI Placement Assistant API",
    description="RAG-powered backend for college placement interview preparation.",
    version="1.0.0",
)

# Enable CORS for frontend applications (Vite, Next.js, local test servers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton service instances
_retriever: Optional[PlacementRetriever] = None
_generator: Optional[GeminiGenerator] = None


def get_retriever() -> PlacementRetriever:
    global _retriever
    if _retriever is None:
        logger.info("Initializing ChromaDB PlacementRetriever...")
        _retriever = PlacementRetriever()
    return _retriever


def get_generator() -> GeminiGenerator:
    global _generator
    if _generator is None:
        logger.info("Initializing GeminiGenerator...")
        _generator = GeminiGenerator()
    return _generator


# ---------------------------------------------------------------------------
# Request & Response Models (Pydantic v2)
# ---------------------------------------------------------------------------

class ChatFilter(BaseModel):
    company_name: Optional[str] = None
    role_name: Optional[str] = None
    batch: Optional[str] = None
    category: Optional[str] = None


class MessageItem(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text content")


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question or query")
    filters: Optional[ChatFilter] = None
    history: Optional[List[MessageItem]] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20, description="Number of context documents to retrieve")


class SourceDocument(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any]
    similarity_score: float
    retrieval_mode: str


class ChatResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceDocument]
    mode: str
    total_retrieved: int


class QuestionItem(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any]
    similarity_score: float
    retrieval_mode: str


class PaginatedQuestionsResponse(BaseModel):
    items: List[QuestionItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health", tags=["System"])
def health_check() -> Dict[str, Any]:
    """
    Returns system health, ChromaDB collection count, and LLM configuration status.
    """
    retriever = get_retriever()
    generator = get_generator()

    count = 0
    try:
        count = retriever.count()
    except Exception as e:
        logger.warning("Could not obtain collection count: %s", e)

    return {
        "status": "healthy",
        "collection_count": count,
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "gemini_model": generator.model_name,
        "gemini_configured": generator.api_key is not None,
    }


@app.post("/api/chat", response_model=ChatResponse, tags=["AI Assistant"])
def chat(request: ChatRequest) -> ChatResponse:
    """
    RAG chat endpoint:
    1. Retrieves top-k semantically relevant question documents matching metadata filters.
    2. Passes retrieved documents and conversation history to Gemini for grounded answer generation.
    3. Returns generated response with attributed source pills.
    """
    clean_query = request.query.strip()
    if not clean_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty or whitespace only.")

    retriever = get_retriever()
    generator = get_generator()

    # Extract metadata filters if provided
    company_name = request.filters.company_name if request.filters else None
    role_name = request.filters.role_name if request.filters else None
    batch = request.filters.batch if request.filters else None
    category = request.filters.category if request.filters else None

    # Retrieve context documents
    retrieved_docs = retriever.retrieve(
        query=clean_query,
        top_k=request.top_k,
        company_name=company_name,
        role_name=role_name,
        batch=batch,
        category=category,
    )

    # Format history for generator
    history_dicts = [{"role": msg.role, "content": msg.content} for msg in (request.history or [])]

    # Generate grounded response
    result = generator.generate_response(
        query=clean_query,
        context_documents=retrieved_docs,
        conversation_history=history_dicts,
    )

    return ChatResponse(
        query=clean_query,
        answer=result["answer"],
        sources=[SourceDocument(**doc) for doc in result["sources"]],
        mode=result["mode"],
        total_retrieved=len(retrieved_docs),
    )


@app.get("/api/questions", response_model=PaginatedQuestionsResponse, tags=["Question Library"])
def list_questions(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Keyword search filter"),
    company: Optional[str] = Query(None, description="Company name filter"),
    role: Optional[str] = Query(None, description="Role name filter"),
    batch: Optional[str] = Query(None, description="Batch year filter"),
    category: Optional[str] = Query(None, description="Question category filter"),
) -> PaginatedQuestionsResponse:
    """
    Paginated search and filter endpoint for Question Library.
    Guarantees complete coverage across all 9,302 questions with deterministic sorting.
    """
    retriever = get_retriever()
    search_result = retriever.search_comprehensive(
        keyword=search,
        company_name=company,
        role_name=role,
        batch=batch,
        category=category,
        page=page,
        page_size=page_size,
    )

    return PaginatedQuestionsResponse(
        items=[QuestionItem(**item) for item in search_result["items"]],
        total=search_result["total_matches"],
        page=search_result["page"],
        page_size=search_result["page_size"],
        total_pages=search_result["total_pages"],
        has_next=search_result["has_next"],
        has_prev=search_result["has_prev"],
    )


@app.get("/api/questions/{question_id}", tags=["Question Library"])
def get_question(question_id: str) -> Dict[str, Any]:
    """
    Retrieves full details for a single question document by deterministic ID.
    """
    retriever = get_retriever()
    doc = retriever.get_by_id(question_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Question with ID '{question_id}' not found.")
    return doc


@app.get("/api/filters", tags=["Question Library"])
def get_filter_options() -> Dict[str, List[str]]:
    """
    Returns unique values for companies, roles, batches, and categories
    to populate faceted search dropdowns in the frontend.
    """
    analytics_data = get_analytics()
    return analytics_data.get("filter_options", {
        "companies": [],
        "roles": [],
        "batches": [],
        "categories": [],
    })


@app.get("/api/analytics/overview", tags=["Analytics"])
def get_analytics_overview() -> Dict[str, Any]:
    """
    Returns top-level metric counters (total questions, companies, roles, batches).
    """
    analytics_data = get_analytics()
    return analytics_data.get("overview", {})


@app.get("/api/analytics/dashboard", tags=["Analytics"])
def get_analytics_dashboard() -> Dict[str, Any]:
    """
    Returns full analytical payload for the Interview Insights & Analytics page.
    """
    return get_analytics()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
