"""Sample plugin tool: word count."""
from typing import Any, Dict


class WordCountTool:
    async def execute(self, text: str) -> Dict[str, Any]:
        words = text.strip().split()
        return {"words": len(words), "characters": len(text)}
