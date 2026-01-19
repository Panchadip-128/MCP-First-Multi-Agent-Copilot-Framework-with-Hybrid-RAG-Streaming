"""Code search tool for MCP."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from app.core.config import settings


class CodeSearchTool:
    """Search for a regex pattern across files in the workspace."""

    async def execute(
        self,
        query: str,
        include: List[str] | None = None,
        exclude: List[str] | None = None,
        max_results: int = 50,
    ) -> Dict[str, Any]:
        root = Path(settings.WORKSPACE_ROOT).resolve()
        if not root.exists():
            raise ValueError(f"Workspace root not found: {root}")

        include = include or ["**/*.*"]
        exclude = exclude or ["**/node_modules/**", "**/.git/**", "**/__pycache__/**", "**/.venv/**"]

        regex = re.compile(query, re.IGNORECASE)

        results: List[Dict[str, Any]] = []
        for pattern in include:
            for path in root.glob(pattern):
                if not path.is_file():
                    continue

                rel = str(path.relative_to(root)).replace("\\", "/")
                if any(Path(rel).match(ex) for ex in exclude):
                    continue

                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                for i, line in enumerate(text.splitlines(), start=1):
                    if regex.search(line):
                        results.append({
                            "file": rel,
                            "line": i,
                            "text": line.strip(),
                        })
                        if len(results) >= max_results:
                            return {"results": results, "total": len(results)}

        return {"results": results, "total": len(results)}
