"""Evaluation endpoints for retrieval quality."""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.core.config import settings

router = APIRouter()


class EvalQuery(BaseModel):
    query: str
    expected_substring: Optional[str] = None
    project_id: Optional[str] = None
    top_k: int = 5
    mode: Optional[str] = None


class EvalRequest(BaseModel):
    queries: List[EvalQuery]


class EvalResponse(BaseModel):
    total: int
    hits: int
    hit_rate: float
    details: List[Dict[str, Any]]


@router.post("/rag", response_model=EvalResponse)
async def eval_rag(request: Request, payload: EvalRequest) -> EvalResponse:
    rag = request.app.state.rag_memory

    details: List[Dict[str, Any]] = []
    hits = 0

    for q in payload.queries:
        results = await rag.search(
            query=q.query,
            project_id=q.project_id,
            top_k=q.top_k,
            mode=q.mode or settings.RAG_SEARCH_MODE,
        )

        hit = False
        if q.expected_substring:
            for r in results:
                if q.expected_substring in r.get("content", "") or q.expected_substring in r.get("file_path", ""):
                    hit = True
                    break
        else:
            hit = len(results) > 0

        hits += 1 if hit else 0
        details.append({
            "query": q.query,
            "hit": hit,
            "results": results,
        })

    total = len(payload.queries)
    hit_rate = (hits / total) if total else 0.0

    return EvalResponse(total=total, hits=hits, hit_rate=hit_rate, details=details)
