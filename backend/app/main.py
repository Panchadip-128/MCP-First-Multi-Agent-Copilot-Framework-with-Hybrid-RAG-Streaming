"""
Main FastAPI application entry point for the LLM Copilot Framework.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings
from app.api.routes import api_router
from app.core.mcp_protocol import MCPProtocol
from app.core.rag_memory import RAGMemoryEngine
from app.core.llm_router import LLMRouter
from app.core.plugin_manager import PluginManager
from app.tools import CalculatorTool, CodeSearchTool, FileReadTool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and cleanup on shutdown."""
    logger.info("🚀 Starting LLM Copilot Framework...")
    
    # Initialize core services
    app.state.mcp_protocol = MCPProtocol()
    app.state.rag_memory = RAGMemoryEngine()
    app.state.llm_router = LLMRouter()

    # Register tools
    app.state.mcp_protocol.register_tool(
        tool_name="calculator",
        tool_handler=CalculatorTool(),
        description="Evaluate arithmetic expressions safely",
        parameters_schema={
            "type": "object",
            "properties": {
                "expression": {"type": "string"},
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
    )

    app.state.mcp_protocol.register_tool(
        tool_name="code_search",
        tool_handler=CodeSearchTool(),
        description="Search for a regex pattern across workspace files",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "include": {"type": "array", "items": {"type": "string"}},
                "exclude": {"type": "array", "items": {"type": "string"}},
                "max_results": {"type": "integer"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    )

    app.state.mcp_protocol.register_tool(
        tool_name="file_read",
        tool_handler=FileReadTool(),
        description="Read a file range from the workspace",
        parameters_schema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "start_line": {"type": "integer"},
                "end_line": {"type": "integer"},
            },
            "required": ["file_path"],
            "additionalProperties": False,
        },
    )

    # Load plugins
    app.state.plugin_manager = PluginManager(app.state.mcp_protocol)
    app.state.plugin_manager.load_plugins()
    
    # Initialize connections
    await app.state.rag_memory.initialize()
    await app.state.llm_router.initialize()
    
    logger.info("✅ All services initialized successfully")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down services...")
    await app.state.rag_memory.close()
    await app.state.llm_router.close()
    logger.info("✅ Cleanup complete")


# Create FastAPI application
app = FastAPI(
    title="LLM Copilot Framework",
    description="Open-source modular framework for AI-powered developer copilots",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "LLM Copilot Framework",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "api": "/api/v1",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "mcp_protocol": "active",
            "rag_memory": "active",
            "llm_router": "active",
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
