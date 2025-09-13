#!/usr/bin/env python3
"""Minimal MCP shim used by tests.

Provides a small `PersistentAIMemoryMCPServer` implementation that maps a
few tool names to `PersistentAIMemorySystem` methods and logs calls via
`memory_system.log_tool_call` so unit tests can observe persisted
tool-call records.
"""
from typing import Any, Dict, Optional
import asyncio

from ai_memory_core import PersistentAIMemorySystem


class PersistentAIMemoryMCPServer:
    """Tiny MCP shim used by the test-suite."""

    def __init__(self):
        # Disable file monitoring in the test shim to avoid background
        # observers keeping DB files locked on Windows during short-lived
        # test runs.
        self.memory_system = PersistentAIMemorySystem(enable_file_monitoring=False)

    async def _log_call(self, tool_name: str, parameters: Optional[Dict] = None,
                        execution_time_ms: Optional[float] = None, status: str = "success",
                        result: Any = None, error_message: Optional[str] = None,
                        client_id: Optional[str] = None):
        try:
            if hasattr(self.memory_system, "log_tool_call"):
                await self.memory_system.log_tool_call(
                    tool_name,
                    parameters or {},
                    execution_time_ms,
                    status,
                    result,
                    error_message,
                    client_id,
                )
        except Exception:
            # best-effort logging in tests
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
                res = await self._call_method(
                    "create_memory",
                    content,
                    memory_type,
                    importance,
                    tags,
                    params.get("source_conversation_id"),
                )
                await self._log_call(tool, params, execution_time_ms=None, status="success", result=res, client_id=client_id)
                return {"status": "success", "result": res}

            if tool == "search_memories":
                query = params.get("query")
                limit = params.get("limit", 10)
                res = await self._call_method("search_memories", query, limit)
                await self._log_call(tool, params, execution_time_ms=None, status="success", result=res, client_id=client_id)
                return {"status": "success", "result": res}

            if tool == "get_system_health":
                res = await self._call_method("get_system_health")
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

            if tool == "store_conversation":
                content = params.get("user_message") or params.get("content")
                assistant = params.get("assistant_response")
                session_id = params.get("session_id")
                msg1 = await self._call_method("store_conversation", content, "user", session_id, None, params.get("metadata"))
                if assistant:
                    await self._call_method("store_conversation", assistant, "assistant", session_id, None, params.get("metadata"))
                await self._log_call(tool, params, execution_time_ms=None, status="success", result={"conversation_id": msg1.get('conversation_id') if isinstance(msg1, dict) else None}, client_id=client_id)
                return {"status": "success", "result": {"conversation_id": msg1.get('conversation_id') if isinstance(msg1, dict) else None}}

            # default: unknown tool
            return {"status": "error", "error": f"Unknown tool: {tool}"}

        except Exception as e:
            await self._log_call(tool or "unknown", params, execution_time_ms=None, status="error", error_message=str(e), client_id=client_id)
            return {"status": "error", "error": str(e)}


# Backwards-compatible alias expected by some tests
AIMemoryMCPServer = PersistentAIMemoryMCPServer
