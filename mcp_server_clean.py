#!/usr/bin/env python3
"""Clean MCP server shim used for local verification.

This is a drop-in style shim (different module name) used to validate
that the memory system's `log_tool_call` API persists entries.
"""
from typing import Any, Dict, Optional
import asyncio

from ai_memory_core import PersistentAIMemorySystem


class PersistentAIMemoryMCPServer:
    def __init__(self):
        self.memory_system = PersistentAIMemorySystem()

    async def _log_call(self, tool_name: str, parameters: Dict = None, execution_time_ms: float = None, status: str = "success", result: Any = None, error_message: str = None, client_id: Optional[str] = None):
        try:
            if hasattr(self.memory_system, "log_tool_call"):
                await self.memory_system.log_tool_call(tool_name, parameters or {}, execution_time_ms, status, result, error_message, client_id)
        except Exception:
            pass

    async def _call_method(self, method_name: str, *args, **kwargs):
        method = getattr(self.memory_system, method_name, None)
        if method is None or not asyncio.iscoroutinefunction(method):
            raise AttributeError(f"Method {method_name} not available on memory system")
        return await method(*args, **kwargs)

    async def handle_mcp_request(self, request: Dict[str, Any], client_id: Optional[str] = None) -> Dict[str, Any]:
        tool = request.get("tool")
        params = request.get("parameters") or {}

        try:
            if tool in ("store_memory", "create_memory"):
                content = params.get("content") or params.get("memory_content")
                memory_type = params.get("memory_type")
                importance = params.get("importance_level", 5)
                tags = params.get("tags")
                res = await self._call_method("create_memory", content, memory_type, importance, tags, params.get("source_conversation_id"))
                await self._log_call(tool, params, execution_time_ms=None, status="success", result=res, client_id=client_id)
                return {"status": "success", "result": res}

            if tool == "get_tool_call_history":
                limit = params.get("limit", 50)
                rows = []
                try:
                    if hasattr(self.memory_system, "mcp_db") and hasattr(self.memory_system.mcp_db, "get_tool_call_history"):
                        rows = await self.memory_system.mcp_db.get_tool_call_history(limit=limit)
                except Exception:
                    rows = []
                await self._log_call(tool, params, execution_time_ms=None, status="success", result={"history_count": len(rows)}, client_id=client_id)
                return {"status": "success", "result": {"history": rows}}

            return {"status": "error", "error": f"Unknown tool: {tool}"}

        except Exception as e:
            await self._log_call(tool or "unknown", params, execution_time_ms=None, status="error", error_message=str(e), client_id=client_id)
            return {"status": "error", "error": str(e)}
