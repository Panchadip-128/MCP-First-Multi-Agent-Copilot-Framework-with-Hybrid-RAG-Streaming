"""Plugin manager for MCP tools."""
from __future__ import annotations

import json
import importlib
from pathlib import Path
from typing import Any, Dict, List
from loguru import logger

from app.core.config import settings


class PluginManager:
    """Discover and load MCP tool plugins from manifest files."""

    def __init__(self, mcp_protocol):
        self.mcp = mcp_protocol
        self.plugins: List[Dict[str, Any]] = []

    def load_plugins(self) -> List[Dict[str, Any]]:
        if not settings.PLUGINS_ENABLED:
            logger.info("Plugins disabled")
            return []

        plugins_dir = Path(settings.PLUGINS_DIR)
        if not plugins_dir.exists():
            logger.warning(f"Plugins dir not found: {plugins_dir}")
            return []

        self.plugins = []

        for manifest_path in plugins_dir.glob("**/manifest.json"):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                self._register_plugin(manifest)
                self.plugins.append(manifest)
            except Exception as e:
                logger.error(f"Failed to load plugin {manifest_path}: {e}")

        logger.info(f"Loaded {len(self.plugins)} plugins")
        return self.plugins

    def _register_plugin(self, manifest: Dict[str, Any]) -> None:
        tools = manifest.get("tools", [])
        for tool in tools:
            tool_name = tool.get("name")
            description = tool.get("description", "")
            handler_path = tool.get("handler")
            parameters_schema = tool.get("parameters_schema", {})

            if not tool_name or not handler_path:
                logger.warning("Invalid tool entry in manifest")
                continue

            handler = self._import_handler(handler_path)
            self.mcp.register_tool(
                tool_name=tool_name,
                tool_handler=handler,
                description=description,
                parameters_schema=parameters_schema,
            )

    def _import_handler(self, handler_path: str):
        module_path, _, class_name = handler_path.rpartition(".")
        if not module_path or not class_name:
            raise ValueError(f"Invalid handler path: {handler_path}")

        module = importlib.import_module(module_path)
        handler_cls = getattr(module, class_name)
        return handler_cls()

    def list_plugins(self) -> List[Dict[str, Any]]:
        return self.plugins
