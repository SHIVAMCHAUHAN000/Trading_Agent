"""
Model Context Protocol (MCP) Tool Registry and Abstraction Layer.
Standardizes tool schemas, execution, auditing, and health checks.
"""

from __future__ import annotations

import inspect
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON schema of parameters
    handler: Callable[..., Any]
    is_active: bool = True
    total_calls: int = 0
    failed_calls: int = 0
    last_called_at: Optional[datetime] = None
    last_latency_ms: float = 0.0


class MCPToolRegistry:
    """Registry managing all MCP tools available to the AI Quant Brain."""

    def __init__(self) -> None:
        self._tools: Dict[str, MCPTool] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Any],
    ) -> None:
        """Register a new MCP tool."""
        self._tools[name] = MCPTool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
        )
        logger.info("Registered MCP tool: %s", name)

    def get_tool(self, name: str) -> Optional[MCPTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[MCPTool]:
        return list(self._tools.values())

    def get_openai_tools_schema(self) -> List[Dict[str, Any]]:
        """Returns tool declarations formatted for OpenAI/Gemini/Anthropic function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
            if tool.is_active
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Invokes a registered tool with latency tracking, auditing, and error handling."""
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Tool '{name}' is not registered in the MCP registry."}

        start_time = time.time()
        tool.total_calls += 1
        tool.last_called_at = datetime.now(timezone.utc)

        try:
            if inspect.iscoroutinefunction(tool.handler):
                result = await tool.handler(**arguments)
            else:
                result = tool.handler(**arguments)

            tool.last_latency_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "tool": name,
                "status": "success",
                "latency_ms": tool.last_latency_ms,
                "data": result,
            }
        except Exception as e:
            tool.failed_calls += 1
            tool.last_latency_ms = round((time.time() - start_time) * 1000, 2)
            logger.error("Error executing MCP tool '%s': %s", name, e, exc_info=True)
            return {
                "tool": name,
                "status": "error",
                "latency_ms": tool.last_latency_ms,
                "error": str(e),
            }

    def get_status(self) -> List[Dict[str, Any]]:
        """Returns health and status of all registered tools."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "is_active": t.is_active,
                "total_calls": t.total_calls,
                "failed_calls": t.failed_calls,
                "last_called_at": t.last_called_at.isoformat() if t.last_called_at else None,
                "last_latency_ms": t.last_latency_ms,
            }
            for t in self._tools.values()
        ]


# Global singleton tool registry
mcp_registry = MCPToolRegistry()
