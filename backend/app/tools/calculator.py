"""Simple calculator tool for MCP."""
from typing import Any


class CalculatorTool:
    """Evaluate simple arithmetic expressions safely."""

    async def execute(self, expression: str) -> Any:
        allowed = set("0123456789+-*/(). %")
        if any(ch not in allowed for ch in expression):
            raise ValueError("Expression contains invalid characters")
        # Safe eval in restricted globals/locals
        return eval(expression, {"__builtins__": {}}, {})
