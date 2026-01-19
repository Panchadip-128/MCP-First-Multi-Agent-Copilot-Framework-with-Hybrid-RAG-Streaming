"""Plugin management endpoints."""

from fastapi import APIRouter, Request
from typing import Any, Dict, List

router = APIRouter()


@router.get("/")
async def list_plugins(request: Request) -> List[Dict[str, Any]]:
    """List loaded plugins and their manifests."""
    pm = request.app.state.plugin_manager
    return pm.list_plugins()


@router.post("/reload")
async def reload_plugins(request: Request) -> Dict[str, Any]:
    """Reload plugins from disk."""
    pm = request.app.state.plugin_manager
    plugins = pm.load_plugins()
    return {"reloaded": len(plugins)}
