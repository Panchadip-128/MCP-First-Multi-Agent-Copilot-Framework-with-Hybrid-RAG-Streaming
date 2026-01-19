"""Tool management endpoints."""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter()


class ToolInfo(BaseModel):
    """Information about a tool."""
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolExecuteRequest(BaseModel):
    """Request to execute a tool."""
    tool_name: str
    parameters: Dict[str, Any]
    timeout: Optional[float] = 30.0


@router.get("/", response_model=List[str])
async def list_tools(request: Request) -> List[str]:
    """List all registered tools."""
    mcp = request.app.state.mcp_protocol
    return mcp.get_tool_list()


@router.get("/specs")
async def list_tool_specs(request: Request) -> List[Dict[str, Any]]:
    """List all registered tools with schemas."""
    mcp = request.app.state.mcp_protocol
    return mcp.get_tool_specs()


@router.post("/execute")
async def execute_tool(
    request: Request,
    tool_request: ToolExecuteRequest,
) -> Dict[str, Any]:
    """
    Execute a tool.
    
    This creates an MCP message and routes it through the protocol.
    """
    mcp = request.app.state.mcp_protocol
    
    # Create tool call message
    from app.core.mcp_protocol import MessageType
    
    message = mcp.create_message(
        message_type=MessageType.TOOL_CALL,
        sender="api",
        content={
            "tool_name": tool_request.tool_name,
            "parameters": tool_request.parameters,
            "timeout": tool_request.timeout,
        },
    )
    
    # Route message
    response = await mcp.route_message(message)
    
    if not response:
        return {"error": "No response from tool"}
    
    return response.content
