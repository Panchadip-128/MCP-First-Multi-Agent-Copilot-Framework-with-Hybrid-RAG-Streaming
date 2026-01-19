"""File read tool for MCP."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from app.core.config import settings


class FileReadTool:
    """Read a file range from the workspace."""

    async def execute(self, file_path: str, start_line: int = 1, end_line: int = 200) -> Dict[str, Any]:
        root = Path(settings.WORKSPACE_ROOT).resolve()
        target = (root / file_path).resolve()

        if not target.exists() or not target.is_file():
            raise ValueError("File not found")

        if root not in target.parents and root != target:
            raise ValueError("Access denied")

        if start_line < 1 or end_line < start_line:
            raise ValueError("Invalid line range")

        lines = target.read_text(encoding="utf-8", errors="ignore").splitlines()
        snippet = lines[start_line - 1:end_line]

        return {
            "file": file_path,
            "start_line": start_line,
            "end_line": end_line,
            "content": "\n".join(snippet),
            "total_lines": len(lines),
        }
