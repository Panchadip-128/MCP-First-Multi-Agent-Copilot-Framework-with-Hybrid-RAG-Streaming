"""
API routes for the LLM Copilot Framework.
"""

from fastapi import APIRouter

from app.api.endpoints import chat, projects, tools, memory, health, agents

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
