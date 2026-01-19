"""Health check endpoints."""

from fastapi import APIRouter, Request
from typing import Dict, Any

router = APIRouter()


@router.get("/")
async def health_check(request: Request) -> Dict[str, Any]:
    """Basic health check."""
    return {
        "status": "healthy",
        "version": "0.1.0",
    }


@router.get("/detailed")
async def detailed_health_check(request: Request) -> Dict[str, Any]:
    """Detailed health check with service status."""
    services = {}
    
    # Check MCP Protocol
    try:
        mcp = request.app.state.mcp_protocol
        services["mcp_protocol"] = {
            "status": "active",
            "registered_tools": len(mcp.registered_tools),
            "registered_agents": len(mcp.registered_agents),
        }
    except Exception as e:
        services["mcp_protocol"] = {"status": "error", "error": str(e)}
    
    # Check RAG Memory
    try:
        rag = request.app.state.rag_memory
        services["rag_memory"] = {
            "status": "active" if rag.client else "inactive",
        }
    except Exception as e:
        services["rag_memory"] = {"status": "error", "error": str(e)}
    
    # Check LLM Router
    try:
        llm = request.app.state.llm_router
        services["llm_router"] = {
            "status": "active",
            "available_models": len(llm.available_models),
        }
    except Exception as e:
        services["llm_router"] = {"status": "error", "error": str(e)}
    
    return {
        "status": "healthy",
        "version": "0.1.0",
        "services": services,
    }
