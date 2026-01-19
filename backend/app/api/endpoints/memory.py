"""Memory/RAG endpoints."""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.core.config import settings

router = APIRouter()


class SearchRequest(BaseModel):
    """Request to search memory."""
    query: str
    project_id: Optional[str] = None
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None
    mode: Optional[str] = None


class SearchResult(BaseModel):
    """Single search result."""
    content: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    score: float


class SearchResponse(BaseModel):
    """Response from memory search."""
    query: str
    results: List[SearchResult]
    total_found: int


@router.post("/search", response_model=SearchResponse)
async def search_memory(
    request: Request,
    search_req: SearchRequest,
) -> SearchResponse:
    """Search the RAG memory for relevant code."""
    rag = request.app.state.rag_memory
    
    results = await rag.search(
        query=search_req.query,
        project_id=search_req.project_id,
        top_k=search_req.top_k,
        filters=search_req.filters,
        mode=search_req.mode or settings.RAG_SEARCH_MODE,
    )
    
    return SearchResponse(
        query=search_req.query,
        results=[
            SearchResult(
                content=r["content"],
                file_path=r["file_path"],
                language=r["language"],
                start_line=r["start_line"],
                end_line=r["end_line"],
                score=r["score"],
            )
            for r in results
        ],
        total_found=len(results),
    )
