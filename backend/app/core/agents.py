"""Multi-agent orchestration (coder/tester/reviewer)."""
from __future__ import annotations

from typing import Dict, Any, List, Optional
from loguru import logger

from app.core.llm_router import LLMRouter, TaskType
from app.core.rag_memory import RAGMemoryEngine
from app.core.config import settings


class MultiAgentOrchestrator:
    """Run multi-agent workflow with optional RAG context."""

    def __init__(self, llm: LLMRouter, rag: RAGMemoryEngine):
        self.llm = llm
        self.rag = rag

    async def run(
        self,
        goal: str,
        project_id: Optional[str] = None,
        use_memory: bool = True,
    ) -> Dict[str, Any]:
        sources = []
        context_block = ""

        if use_memory and project_id:
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


        # Planner
        planner_prompt = (
            "You are a planning agent for a FastAPI + MCP backend. "
            "Provide a concise step-by-step plan grounded in the existing codebase. "
            "Reference specific files and endpoints when applicable."
        )
        planner = await self.llm.generate(
            messages=[
                {"role": "system", "content": planner_prompt},
                {"role": "user", "content": f"Goal: {goal}\n\nContext:\n{context_block}"},
            ],
            task_type=TaskType.GENERAL_CHAT,
        )

        # Coder
        coder_prompt = (
            "You are a senior engineer working in this codebase. "
            "Provide concrete implementation steps and code snippets that fit FastAPI and MCP. "
            "Reference actual files (e.g., backend/app/api/endpoints/*.py)."
        )
        coder = await self.llm.generate(
            messages=[
                {"role": "system", "content": coder_prompt},
                {"role": "user", "content": f"Goal: {goal}\n\nPlan:\n{planner['content']}\n\nContext:\n{context_block}"},
            ],
            task_type=TaskType.CODE_GENERATION,
        )

        # Reviewer
        reviewer_prompt = (
            "You are a reviewer. Identify risks, edge cases, and improvements for this FastAPI/MCP codebase. "
            "Suggest specific fixes tied to files where possible."
        )
        review = await self.llm.generate(
            messages=[
                {"role": "system", "content": reviewer_prompt},
                {"role": "user", "content": f"Goal: {goal}\n\nProposal:\n{coder['content']}"},
            ],
            task_type=TaskType.DEBUGGING,
        )

        # Tester
        tester_prompt = (
            "You are a test engineer. Propose tests and validation steps for this codebase, "
            "including concrete API requests and expected outputs."
        )
        tests = await self.llm.generate(
            messages=[
                {"role": "system", "content": tester_prompt},
                {"role": "user", "content": f"Goal: {goal}\n\nProposal:\n{coder['content']}"},
            ],
            task_type=TaskType.TEST_GENERATION,
        )

        return {
            "goal": goal,
            "plan": planner["content"],
            "proposal": coder["content"],
            "review": review["content"],
            "tests": tests["content"],
            "sources": sources,
        }
