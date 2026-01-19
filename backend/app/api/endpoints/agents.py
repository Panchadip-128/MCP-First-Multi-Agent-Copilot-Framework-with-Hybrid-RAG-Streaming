"""Agent endpoints for planning and orchestration."""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
from typing import List
import json
import re

from app.core.workflow import WorkflowOrchestrator

router = APIRouter()


class ToolPlanRequest(BaseModel):
    goal: str
    context: Optional[str] = None


class ToolPlanResponse(BaseModel):
    plan: Dict[str, Any]
    tool_result: Optional[Dict[str, Any]] = None


class MultiAgentRequest(BaseModel):
    goal: str
    project_id: Optional[str] = None
    use_memory: bool = True


class WorkflowRequest(BaseModel):
    goal: str
    project_id: Optional[str] = None
    use_memory: bool = True
    run_tools: bool = True


class MultiAgentResponse(BaseModel):
    goal: str
    plan: str
    proposal: str
    review: str
    tests: str
    sources: Optional[Any] = None


def _extract_json(text: str) -> Dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response")
    return json.loads(match.group(0))


@router.post("/plan", response_model=ToolPlanResponse)
async def plan_and_execute(request: Request, payload: ToolPlanRequest) -> ToolPlanResponse:
    """
    Plan a tool call and execute it via MCP.
    """
    mcp = request.app.state.mcp_protocol
    llm = request.app.state.llm_router

    tool_specs = mcp.get_tool_specs()

    system_prompt = (
        "You are a tool planning agent. Select the best tool for the goal. "
        "Return ONLY a JSON object with keys: tool_name, parameters, reason. "
        "If no tool is needed, return tool_name as null and parameters as {}."
    )

    user_prompt = {
        "goal": payload.goal,
        "context": payload.context or "",
        "tools": tool_specs,
    }

    # Heuristic: if goal mentions a symbol and no path, do a two-step search + read
    if "MCPProtocol" in payload.goal:
        # Step 1: search
        from app.core.mcp_protocol import MessageType

        search_msg = mcp.create_message(
            message_type=MessageType.TOOL_CALL,
            sender="agent-planner",
            content={
                "tool_name": "code_search",
                "parameters": {
                    "query": "MCPProtocol",
                    "include": ["backend/app/**/*.py"],
                    "max_results": 5,
                },
                "timeout": 30.0,
            },
        )
        search_response = await mcp.route_message(search_msg)
        search_result = search_response.content if search_response else {"error": "No response"}

        # Step 2: read first match
        file_path = None
        if search_result.get("success") and search_result.get("result"):
            results = search_result["result"].get("results", [])
            if results:
                file_path = results[0].get("file")

        if file_path:
            read_msg = mcp.create_message(
                message_type=MessageType.TOOL_CALL,
                sender="agent-planner",
                content={
                    "tool_name": "file_read",
                    "parameters": {
                        "file_path": file_path,
                        "start_line": 1,
                        "end_line": 40,
                    },
                    "timeout": 30.0,
                },
            )
            read_response = await mcp.route_message(read_msg)
            read_result = read_response.content if read_response else {"error": "No response"}

            return ToolPlanResponse(
                plan={
                    "steps": [
                        {"tool": "code_search", "parameters": search_msg.content["parameters"]},
                        {"tool": "file_read", "parameters": read_msg.content["parameters"]},
                    ],
                    "reason": "Search then read the first matching file",
                },
                tool_result={
                    "search": search_result,
                    "read": read_result,
                },
            )

        return ToolPlanResponse(
            plan={
                "steps": [
                    {"tool": "code_search", "parameters": search_msg.content["parameters"]},
                ],
                "reason": "Search results not found",
            },
            tool_result={"search": search_result},
        )

    response = await llm.generate(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_prompt)},
        ],
        task_type="general_chat",
    )

    try:
        plan = _extract_json(response["content"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planner parsing failed: {e}")

    tool_name = plan.get("tool_name")
    if not tool_name:
        return ToolPlanResponse(plan=plan, tool_result=None)

    # Execute tool via MCP
    from app.core.mcp_protocol import MessageType

    message = mcp.create_message(
        message_type=MessageType.TOOL_CALL,
        sender="agent-planner",
        content={
            "tool_name": tool_name,
            "parameters": plan.get("parameters", {}),
            "timeout": 30.0,
        },
    )

    tool_response = await mcp.route_message(message)
    if not tool_response:
        return ToolPlanResponse(plan=plan, tool_result={"error": "No response"})

    return ToolPlanResponse(plan=plan, tool_result=tool_response.content)


@router.post("/run", response_model=MultiAgentResponse)
async def run_multi_agent(request: Request, payload: MultiAgentRequest) -> MultiAgentResponse:
    """Run multi-agent workflow (planner -> coder -> reviewer -> tester)."""
    from app.core.agents import MultiAgentOrchestrator

    orchestrator = MultiAgentOrchestrator(
        llm=request.app.state.llm_router,
        rag=request.app.state.rag_memory,
    )

    result = await orchestrator.run(
        goal=payload.goal,
        project_id=payload.project_id,
        use_memory=payload.use_memory,
    )

    return MultiAgentResponse(**result)


@router.post("/workflow")
async def run_workflow(req: WorkflowRequest, request: Request):
    llm = request.app.state.llm_router
    rag = request.app.state.rag_memory
    mcp = request.app.state.mcp_protocol

    orchestrator = WorkflowOrchestrator(llm=llm, rag=rag, mcp=mcp)
    try:
        result = await orchestrator.run(
            goal=req.goal,
            project_id=req.project_id,
            use_memory=req.use_memory,
            run_tools=req.run_tools,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return result
