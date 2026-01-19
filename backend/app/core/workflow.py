"""Industry-grade workflow orchestrator with traceability."""
from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List, Optional
from loguru import logger

from app.core.config import settings
from app.core.llm_router import LLMRouter, TaskType
from app.core.mcp_protocol import MCPProtocol, MessageType
from app.core.rag_memory import RAGMemoryEngine


def _extract_json(text: str) -> Dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response")
    return json.loads(match.group(0))


class WorkflowOrchestrator:
    """Run a multi-stage workflow with trace and tool orchestration."""

    def __init__(self, llm: LLMRouter, rag: RAGMemoryEngine, mcp: MCPProtocol):
        self.llm = llm
        self.rag = rag
        self.mcp = mcp

    async def run(
        self,
        goal: str,
        project_id: Optional[str] = None,
        use_memory: bool = True,
        run_tools: bool = True,
    ) -> Dict[str, Any]:
        trace: List[Dict[str, Any]] = []
        sources: List[Dict[str, Any]] = []
        context_block = ""

        if use_memory and project_id:
            t0 = time.time()
            results = await self.rag.search(
                query=goal,
                project_id=project_id,
                top_k=3,
                mode=settings.RAG_SEARCH_MODE,
            )
            sources = results
            if results:
                context_parts = []
                for idx, r in enumerate(results, 1):
                    context_parts.append(
                        f"[Context {idx} from {r['file_path']}:{r['start_line']}-{r['end_line']}\n{r['content']}\n]"
                    )
                context_block = "\n".join(context_parts)
            trace.append({
                "step": "rag_context",
                "status": "ok",
                "duration_ms": int((time.time() - t0) * 1000),
                "output": f"{len(results)} contexts",
            })

        # Planner
        t0 = time.time()
        planner = await self.llm.generate(
            messages=[
                {
                    "role": "system",
                    "content": "You are a planning agent for a FastAPI + MCP backend. Provide a concise step-by-step plan grounded in the existing codebase.",
                },
                {
                    "role": "user",
                    "content": f"Goal: {goal}\n\nContext:\n{context_block}",
                },
            ],
            task_type=TaskType.GENERAL_CHAT,
        )
        trace.append({
            "step": "planner",
            "status": "ok",
            "duration_ms": int((time.time() - t0) * 1000),
        })

        tool_plan = None
        tool_result = None

        if run_tools:
            t0 = time.time()
            tool_specs = self.mcp.get_tool_specs()
            tool_plan_prompt = (
                "Select the best tool for the goal using the provided tool specs. "
                "Return ONLY a JSON object with keys: tool_name, parameters, reason. "
                "If no tool is needed, tool_name is null and parameters is {}."
            )
            tool_plan_resp = await self.llm.generate(
                messages=[
                    {"role": "system", "content": tool_plan_prompt},
                    {
                        "role": "user",
                        "content": json.dumps({
                            "goal": goal,
                            "tools": tool_specs,
                            "context": context_block,
                        }),
                    },
                ],
                task_type=TaskType.GENERAL_CHAT,
            )

            try:
                tool_plan = _extract_json(tool_plan_resp["content"])
            except Exception as e:
                tool_plan = {"tool_name": None, "parameters": {}, "reason": str(e)}

            trace.append({
                "step": "tool_plan",
                "status": "ok",
                "duration_ms": int((time.time() - t0) * 1000),
            })

            if tool_plan.get("tool_name"):
                t1 = time.time()
                msg = self.mcp.create_message(
                    message_type=MessageType.TOOL_CALL,
                    sender="workflow",
                    content={
                        "tool_name": tool_plan["tool_name"],
                        "parameters": tool_plan.get("parameters", {}),
                        "timeout": 30.0,
                    },
                )
                tool_resp = await self.mcp.route_message(msg)
                tool_result = tool_resp.content if tool_resp else {"error": "No response"}
                trace.append({
                    "step": "tool_execute",
                    "status": "ok" if tool_resp else "error",
                    "duration_ms": int((time.time() - t1) * 1000),
                })

        # Coder
        t0 = time.time()
        coder = await self.llm.generate(
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior engineer. Provide a concrete implementation plan and code snippets in this codebase (FastAPI/MCP).",
                },
                {
                    "role": "user",
                    "content": f"Goal: {goal}\n\nPlan:\n{planner['content']}\n\nContext:\n{context_block}\n\nTool Results:\n{tool_result}",
                },
            ],
            task_type=TaskType.CODE_GENERATION,
        )
        trace.append({
            "step": "coder",
            "status": "ok",
            "duration_ms": int((time.time() - t0) * 1000),
        })

        # Reviewer
        t0 = time.time()
        review = await self.llm.generate(
            messages=[
                {
                    "role": "system",
                    "content": "You are a reviewer. Identify risks, edge cases, and improvements tied to actual files where possible.",
                },
                {
                    "role": "user",
                    "content": f"Goal: {goal}\n\nProposal:\n{coder['content']}",
                },
            ],
            task_type=TaskType.DEBUGGING,
        )
        trace.append({
            "step": "reviewer",
            "status": "ok",
            "duration_ms": int((time.time() - t0) * 1000),
        })

        # Tester
        t0 = time.time()
        tests = await self.llm.generate(
            messages=[
                {
                    "role": "system",
                    "content": "You are a test engineer. Propose tests and validation steps with concrete API requests.",
                },
                {
                    "role": "user",
                    "content": f"Goal: {goal}\n\nProposal:\n{coder['content']}",
                },
            ],
            task_type=TaskType.TEST_GENERATION,
        )
        trace.append({
            "step": "tester",
            "status": "ok",
            "duration_ms": int((time.time() - t0) * 1000),
        })

        return {
            "goal": goal,
            "plan": planner["content"],
            "tool_plan": tool_plan,
            "tool_result": tool_result,
            "proposal": coder["content"],
            "review": review["content"],
            "tests": tests["content"],
            "sources": sources,
            "trace": trace,
        }
